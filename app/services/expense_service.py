"""Core expense claim business logic service."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.expense import (
    ExpenseClaim, ExpenseItem, ExpenseCategory, User, Company,
    ClaimStatus, ExpenseCategories, AuditLog
)
from app.services.currency_service import CurrencyService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ExpenseClaimService:
    """Service for managing expense claims and business workflows."""
    
    def __init__(self, db: Session):
        self.db = db
        self.currency_service = CurrencyService(db)
        self.notification_service = NotificationService(db)
    
    def create_claim(
        self, 
        claimant_id: int, 
        company_id: int,
        event_name: str,
        period_from: datetime,
        period_to: datetime,
        **kwargs
    ) -> ExpenseClaim:
        """Create a new expense claim."""
        
        # Generate claim number
        claim_number = self._generate_claim_number(company_id)
        
        claim = ExpenseClaim(
            claim_number=claim_number,
            claimant_id=claimant_id,
            company_id=company_id,
            event_name=event_name,
            event_name_chinese=kwargs.get('event_name_chinese'),
            project_name=kwargs.get('project_name'),
            period_from=period_from,
            period_to=period_to,
            status=ClaimStatus.DRAFT
        )
        
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        
        # Log the creation
        self._log_audit_event(claim.id, "CREATE", None, claim.__dict__, claimant_id)
        
        logger.info(f"Created expense claim {claim_number} for user {claimant_id}")
        return claim
    
    def add_expense_item(
        self,
        claim_id: int,
        expense_data: Dict
    ) -> ExpenseItem:
        """Add an expense item to a claim."""
        
        claim = self.db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
        if not claim:
            raise ValueError("Expense claim not found")
        
        if claim.status not in [ClaimStatus.DRAFT]:
            raise ValueError("Cannot modify submitted claims")
        
        # Calculate item number
        item_count = self.db.query(ExpenseItem).filter(
            ExpenseItem.expense_claim_id == claim_id
        ).count()
        item_number = item_count + 1
        
        # Convert currency if needed
        conversion = self.currency_service.convert_amount(
            expense_data['original_amount'],
            expense_data['currency_code']
        )
        
        expense_item = ExpenseItem(
            expense_claim_id=claim_id,
            item_number=item_number,
            expense_date=expense_data['expense_date'],
            description=expense_data['description'],
            description_chinese=expense_data.get('description_chinese'),
            category_id=expense_data['category_id'],
            original_amount=expense_data['original_amount'],
            currency_id=expense_data['currency_id'],
            exchange_rate=conversion['exchange_rate'],
            amount_hkd=conversion['converted_amount'],
            has_receipt=expense_data.get('has_receipt', True),
            receipt_notes=expense_data.get('receipt_notes'),
            location=expense_data.get('location'),
            location_chinese=expense_data.get('location_chinese'),
            participants=expense_data.get('participants'),
            business_purpose=expense_data.get('business_purpose'),
            vendor_name=expense_data.get('vendor_name'),
            tax_amount=expense_data.get('tax_amount', Decimal('0')),
            tax_rate=expense_data.get('tax_rate', Decimal('0'))
        )
        
        self.db.add(expense_item)
        
        # Update claim totals
        self._update_claim_totals(claim_id)
        
        self.db.commit()
        self.db.refresh(expense_item)
        
        logger.info(f"Added expense item to claim {claim.claim_number}")
        return expense_item
    
    def submit_claim(self, claim_id: int, user_id: int) -> ExpenseClaim:
        """Submit a claim for approval."""
        
        claim = self.db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
        if not claim:
            raise ValueError("Expense claim not found")
        
        if claim.claimant_id != user_id:
            raise ValueError("Only the claimant can submit their own claim")
        
        if claim.status != ClaimStatus.DRAFT:
            raise ValueError("Only draft claims can be submitted")
        
        # Validate claim has items
        item_count = self.db.query(ExpenseItem).filter(
            ExpenseItem.expense_claim_id == claim_id
        ).count()
        
        if item_count == 0:
            raise ValueError("Cannot submit empty claim")
        
        # Update status and timestamp
        old_values = claim.__dict__.copy()
        claim.status = ClaimStatus.SUBMITTED
        claim.submitted_at = datetime.utcnow()
        
        self.db.commit()
        
        # Log audit event
        self._log_audit_event(claim_id, "SUBMIT", old_values, claim.__dict__, user_id)
        
        # Send notification to manager
        self.notification_service.notify_claim_submitted(claim)
        
        logger.info(f"Submitted expense claim {claim.claim_number}")
        return claim
    
    def check_claim(
        self, 
        claim_id: int, 
        checker_id: int, 
        notes: Optional[str] = None
    ) -> ExpenseClaim:
        """Mark a claim as checked (first level approval)."""
        
        claim = self.db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
        if not claim:
            raise ValueError("Expense claim not found")
        
        if claim.status != ClaimStatus.SUBMITTED:
            raise ValueError("Only submitted claims can be checked")
        
        # Verify checker has permission
        checker = self.db.query(User).filter(User.id == checker_id).first()
        if not checker or not (checker.is_manager or checker.is_finance):
            raise ValueError("User does not have permission to check claims")
        
        old_values = claim.__dict__.copy()
        claim.status = ClaimStatus.CHECKED
        claim.checked_by_id = checker_id
        claim.checked_at = datetime.utcnow()
        claim.check_notes = notes
        
        self.db.commit()
        
        # Log audit event
        self._log_audit_event(claim_id, "CHECK", old_values, claim.__dict__, checker_id)
        
        # Notify for final approval
        self.notification_service.notify_claim_checked(claim)
        
        logger.info(f"Checked expense claim {claim.claim_number} by user {checker_id}")
        return claim
    
    def approve_claim(
        self, 
        claim_id: int, 
        approver_id: int, 
        notes: Optional[str] = None
    ) -> ExpenseClaim:
        """Approve a claim (final approval)."""
        
        claim = self.db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
        if not claim:
            raise ValueError("Expense claim not found")
        
        if claim.status != ClaimStatus.CHECKED:
            raise ValueError("Only checked claims can be approved")
        
        # Verify approver has permission
        approver = self.db.query(User).filter(User.id == approver_id).first()
        if not approver or not (approver.is_manager or approver.is_finance):
            raise ValueError("User does not have permission to approve claims")
        
        old_values = claim.__dict__.copy()
        claim.status = ClaimStatus.APPROVED
        claim.approved_by_id = approver_id
        claim.approved_at = datetime.utcnow()
        claim.approval_notes = notes
        
        self.db.commit()
        
        # Log audit event
        self._log_audit_event(claim_id, "APPROVE", old_values, claim.__dict__, approver_id)
        
        # Notify claimant and finance
        self.notification_service.notify_claim_approved(claim)
        
        logger.info(f"Approved expense claim {claim.claim_number} by user {approver_id}")
        return claim
    
    def reject_claim(
        self, 
        claim_id: int, 
        rejector_id: int, 
        reason: str
    ) -> ExpenseClaim:
        """Reject a claim."""
        
        claim = self.db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
        if not claim:
            raise ValueError("Expense claim not found")
        
        if claim.status not in [ClaimStatus.SUBMITTED, ClaimStatus.CHECKED]:
            raise ValueError("Only submitted or checked claims can be rejected")
        
        # Verify rejector has permission
        rejector = self.db.query(User).filter(User.id == rejector_id).first()
        if not rejector or not (rejector.is_manager or rejector.is_finance):
            raise ValueError("User does not have permission to reject claims")
        
        old_values = claim.__dict__.copy()
        claim.status = ClaimStatus.REJECTED
        
        # Set appropriate rejection fields based on current status
        if claim.status == ClaimStatus.SUBMITTED:
            claim.checked_by_id = rejector_id
            claim.checked_at = datetime.utcnow()
            claim.check_notes = f"REJECTED: {reason}"
        else:
            claim.approved_by_id = rejector_id
            claim.approved_at = datetime.utcnow()
            claim.approval_notes = f"REJECTED: {reason}"
        
        self.db.commit()
        
        # Log audit event
        self._log_audit_event(claim_id, "REJECT", old_values, claim.__dict__, rejector_id)
        
        # Notify claimant
        self.notification_service.notify_claim_rejected(claim, reason)
        
        logger.info(f"Rejected expense claim {claim.claim_number} by user {rejector_id}")
        return claim
    
    def get_claims_for_user(
        self, 
        user_id: int, 
        status: Optional[str] = None,
        company_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ExpenseClaim], int]:
        """Get expense claims for a user with pagination."""
        
        query = self.db.query(ExpenseClaim).filter(ExpenseClaim.claimant_id == user_id)
        
        if status:
            query = query.filter(ExpenseClaim.status == status)
        
        if company_id:
            query = query.filter(ExpenseClaim.company_id == company_id)
        
        total = query.count()
        
        claims = (
            query.order_by(desc(ExpenseClaim.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        return claims, total
    
    def get_claims_for_approval(
        self, 
        approver_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ExpenseClaim], int]:
        """Get claims that need approval by a manager/finance user."""
        
        approver = self.db.query(User).filter(User.id == approver_id).first()
        if not approver or not (approver.is_manager or approver.is_finance):
            return [], 0
        
        # Get claims that need approval
        status_filter = [ClaimStatus.SUBMITTED, ClaimStatus.CHECKED]
        if status:
            status_filter = [status]
        
        query = self.db.query(ExpenseClaim).filter(
            ExpenseClaim.status.in_(status_filter)
        )
        
        # If manager, filter by their team
        if approver.is_manager and not approver.is_finance:
            managed_user_ids = [u.id for u in approver.managed_users]
            managed_user_ids.append(approver_id)  # Include self
            query = query.filter(ExpenseClaim.claimant_id.in_(managed_user_ids))
        
        total = query.count()
        
        claims = (
            query.order_by(ExpenseClaim.submitted_at)
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        return claims, total
    
    def get_expense_summary_by_category(
        self,
        company_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """Get expense summary grouped by category."""
        
        query = (
            self.db.query(
                ExpenseCategory.name,
                ExpenseCategory.name_chinese_traditional,
                func.sum(ExpenseItem.amount_hkd).label('total_amount'),
                func.count(ExpenseItem.id).label('item_count')
            )
            .join(ExpenseItem, ExpenseCategory.id == ExpenseItem.category_id)
            .join(ExpenseClaim, ExpenseItem.expense_claim_id == ExpenseClaim.id)
        )
        
        if company_id:
            query = query.filter(ExpenseClaim.company_id == company_id)
        
        if date_from:
            query = query.filter(ExpenseClaim.period_from >= date_from)
        
        if date_to:
            query = query.filter(ExpenseClaim.period_to <= date_to)
        
        if status:
            query = query.filter(ExpenseClaim.status == status)
        
        results = query.group_by(
            ExpenseCategory.id,
            ExpenseCategory.name,
            ExpenseCategory.name_chinese_traditional
        ).all()
        
        return [
            {
                "category_name": result.name,
                "category_name_chinese": result.name_chinese_traditional,
                "total_amount": float(result.total_amount or 0),
                "item_count": result.item_count
            }
            for result in results
        ]
    
    def _generate_claim_number(self, company_id: int) -> str:
        """Generate a unique claim number."""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        company_code = company.code if company else "UNK"
        
        # Get current year and month
        now = datetime.utcnow()
        year_month = now.strftime("%Y%m")
        
        # Get next sequence number for this company and month
        prefix = f"{company_code}-{year_month}-"
        
        latest_claim = (
            self.db.query(ExpenseClaim)
            .filter(
                ExpenseClaim.company_id == company_id,
                ExpenseClaim.claim_number.like(f"{prefix}%")
            )
            .order_by(desc(ExpenseClaim.created_at))
            .first()
        )
        
        if latest_claim and latest_claim.claim_number:
            try:
                last_seq = int(latest_claim.claim_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"
    
    def _update_claim_totals(self, claim_id: int):
        """Update claim totals when items are added/modified."""
        
        # Calculate total amounts
        totals = (
            self.db.query(
                func.sum(ExpenseItem.original_amount).label('total_original'),
                func.sum(ExpenseItem.amount_hkd).label('total_hkd')
            )
            .filter(ExpenseItem.expense_claim_id == claim_id)
            .first()
        )
        
        # Calculate category-wise totals
        category_totals = (
            self.db.query(
                ExpenseCategory.code,
                func.sum(ExpenseItem.amount_hkd).label('category_total')
            )
            .join(ExpenseItem, ExpenseCategory.id == ExpenseItem.category_id)
            .filter(ExpenseItem.expense_claim_id == claim_id)
            .group_by(ExpenseCategory.code)
            .all()
        )
        
        # Update claim
        claim = self.db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
        if claim:
            claim.total_amount_original = totals.total_original or Decimal('0')
            claim.total_amount_hkd = totals.total_hkd or Decimal('0')
            
            # Reset category totals
            claim.keynote_total_hkd = Decimal('0')
            claim.sponsor_total_hkd = Decimal('0')
            claim.course_ops_total_hkd = Decimal('0')
            claim.exhibition_total_hkd = Decimal('0')
            claim.misc_total_hkd = Decimal('0')
            claim.business_total_hkd = Decimal('0')
            claim.instructor_total_hkd = Decimal('0')
            claim.procurement_total_hkd = Decimal('0')
            claim.transport_total_hkd = Decimal('0')
            
            # Set category totals
            for category_code, total in category_totals:
                if category_code == ExpenseCategories.KEYNOTE_SPEECH:
                    claim.keynote_total_hkd = total
                elif category_code == ExpenseCategories.SPONSOR_GUEST:
                    claim.sponsor_total_hkd = total
                elif category_code == ExpenseCategories.COURSE_OPERATIONS_MARKETING:
                    claim.course_ops_total_hkd = total
                elif category_code == ExpenseCategories.EXHIBITION_PROCUREMENT:
                    claim.exhibition_total_hkd = total
                elif category_code == ExpenseCategories.OTHER_MISCELLANEOUS:
                    claim.misc_total_hkd = total
                elif category_code == ExpenseCategories.BUSINESS_NEGOTIATIONS:
                    claim.business_total_hkd = total
                elif category_code == ExpenseCategories.INSTRUCTOR_MISCELLANEOUS:
                    claim.instructor_total_hkd = total
                elif category_code == ExpenseCategories.PROCUREMENT_MISCELLANEOUS:
                    claim.procurement_total_hkd = total
                elif category_code == ExpenseCategories.TRANSPORTATION:
                    claim.transport_total_hkd = total
    
    def _log_audit_event(
        self, 
        record_id: int, 
        action: str, 
        old_values: Optional[Dict], 
        new_values: Dict, 
        user_id: int
    ):
        """Log audit event."""
        import json
        
        audit_log = AuditLog(
            table_name="expense_claims",
            record_id=record_id,
            action=action,
            old_values=json.dumps(old_values, default=str) if old_values else None,
            new_values=json.dumps(new_values, default=str),
            user_id=user_id
        )
        
        self.db.add(audit_log)