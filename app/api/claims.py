"""Enhanced expense claims API endpoints with full business logic."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models.expense import ExpenseClaim, ExpenseItem, ClaimStatus
from app.schemas.expense import (
    ExpenseClaim as ExpenseClaimSchema,
    ExpenseClaimCreate,
    ExpenseClaimUpdate,
    ExpenseClaimSummary,
    ExpenseItem as ExpenseItemSchema,
    ExpenseItemCreate,
    ExpenseItemUpdate
)
from app.services.expense_service import ExpenseClaimService
from app.services.currency_service import CurrencyService
from app.services.ocr_service import OCRService
from app.core.security import get_current_user
from app.models.expense import User

router = APIRouter()
security = HTTPBearer()


@router.get("/", response_model=Dict)
async def get_claims(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    company_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense claims with filtering and pagination."""
    
    expense_service = ExpenseClaimService(db)
    
    # Get claims for the current user
    claims, total = expense_service.get_claims_for_user(
        user_id=current_user.id,
        status=status,
        company_id=company_id,
        limit=limit,
        offset=skip
    )
    
    return {
        "claims": [ExpenseClaimSummary.model_validate(claim) for claim in claims],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/for-approval", response_model=Dict)
async def get_claims_for_approval(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get claims pending approval (for managers/finance)."""
    
    if not (current_user.is_manager or current_user.is_finance):
        raise HTTPException(status_code=403, detail="Access denied")
    
    expense_service = ExpenseClaimService(db)
    
    claims, total = expense_service.get_claims_for_approval(
        approver_id=current_user.id,
        status=status,
        limit=limit,
        offset=skip
    )
    
    return {
        "claims": [ExpenseClaimSummary.model_validate(claim) for claim in claims],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=ExpenseClaimSchema)
async def create_claim(
    claim_data: ExpenseClaimCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new expense claim."""
    
    expense_service = ExpenseClaimService(db)
    
    try:
        claim = expense_service.create_claim(
            claimant_id=current_user.id,
            company_id=claim_data.company_id,
            event_name=claim_data.event_name,
            period_from=claim_data.period_from,
            period_to=claim_data.period_to
        )
        
        # Add expense items if provided
        for item_data in claim_data.expense_items:
            expense_service.add_expense_item(
                claim_id=claim.id,
                expense_data=item_data.model_dump()
            )
        
        # Refresh to get updated totals
        db.refresh(claim)
        
        return ExpenseClaimSchema.model_validate(claim)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create claim")


@router.get("/{claim_id}", response_model=ExpenseClaimSchema)
async def get_claim(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific claim by ID."""
    
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Check access permissions
    can_access = (
        claim.claimant_id == current_user.id or  # Owner
        current_user.is_manager or               # Manager
        current_user.is_finance or               # Finance
        (current_user.is_manager and claim.claimant.manager_id == current_user.id)  # Direct manager
    )
    
    if not can_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ExpenseClaimSchema.model_validate(claim)


@router.put("/{claim_id}", response_model=ExpenseClaimSchema)
async def update_claim(
    claim_id: int,
    claim_update: ExpenseClaimUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update specific claim (only draft claims)."""
    
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Only owner can update their own draft claims
    if claim.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if claim.status != ClaimStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft claims can be updated")
    
    # Update fields
    update_data = claim_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)
    
    db.commit()
    db.refresh(claim)
    
    return ExpenseClaimSchema.model_validate(claim)


@router.delete("/{claim_id}")
async def delete_claim(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete specific claim (only draft claims)."""
    
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Only owner can delete their own draft claims
    if claim.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if claim.status != ClaimStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft claims can be deleted")
    
    db.delete(claim)
    db.commit()
    
    return {"message": "Claim deleted successfully"}


@router.post("/{claim_id}/items", response_model=ExpenseItemSchema)
async def add_expense_item(
    claim_id: int,
    item_data: ExpenseItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add expense item to claim."""
    
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if claim.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if claim.status != ClaimStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Cannot modify submitted claims")
    
    expense_service = ExpenseClaimService(db)
    
    try:
        item = expense_service.add_expense_item(
            claim_id=claim_id,
            expense_data=item_data.model_dump()
        )
        
        return ExpenseItemSchema.model_validate(item)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{claim_id}/items/{item_id}", response_model=ExpenseItemSchema)
async def update_expense_item(
    claim_id: int,
    item_id: int,
    item_update: ExpenseItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update expense item."""
    
    item = db.query(ExpenseItem).filter(
        ExpenseItem.id == item_id,
        ExpenseItem.expense_claim_id == claim_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Expense item not found")
    
    if item.expense_claim.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if item.expense_claim.status != ClaimStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Cannot modify submitted claims")
    
    # Update fields
    update_data = item_update.model_dump(exclude_unset=True)
    
    # Handle currency conversion if amount or currency changed
    if 'original_amount' in update_data or 'currency_id' in update_data:
        currency_service = CurrencyService(db)
        original_amount = update_data.get('original_amount', item.original_amount)
        currency_id = update_data.get('currency_id', item.currency_id)
        
        # Get currency code
        from app.models.expense import Currency
        currency = db.query(Currency).filter(Currency.id == currency_id).first()
        if currency:
            conversion = currency_service.convert_amount(original_amount, currency.code)
            update_data['exchange_rate'] = conversion['exchange_rate']
            update_data['amount_hkd'] = conversion['converted_amount']
    
    for field, value in update_data.items():
        setattr(item, field, value)
    
    # Update claim totals
    expense_service = ExpenseClaimService(db)
    expense_service._update_claim_totals(claim_id)
    
    db.commit()
    db.refresh(item)
    
    return ExpenseItemSchema.model_validate(item)


@router.delete("/{claim_id}/items/{item_id}")
async def delete_expense_item(
    claim_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete expense item."""
    
    item = db.query(ExpenseItem).filter(
        ExpenseItem.id == item_id,
        ExpenseItem.expense_claim_id == claim_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Expense item not found")
    
    if item.expense_claim.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if item.expense_claim.status != ClaimStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Cannot modify submitted claims")
    
    db.delete(item)
    
    # Update claim totals
    expense_service = ExpenseClaimService(db)
    expense_service._update_claim_totals(claim_id)
    
    db.commit()
    
    return {"message": "Expense item deleted successfully"}


@router.post("/{claim_id}/submit")
async def submit_claim(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit claim for approval."""
    
    expense_service = ExpenseClaimService(db)
    
    try:
        claim = expense_service.submit_claim(claim_id, current_user.id)
        return {"message": "Claim submitted successfully", "claim_number": claim.claim_number}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/check")
async def check_claim(
    claim_id: int,
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check/review claim (first level approval)."""
    
    if not (current_user.is_manager or current_user.is_finance):
        raise HTTPException(status_code=403, detail="Access denied")
    
    expense_service = ExpenseClaimService(db)
    
    try:
        claim = expense_service.check_claim(claim_id, current_user.id, notes)
        return {"message": "Claim checked successfully", "claim_number": claim.claim_number}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/approve")
async def approve_claim(
    claim_id: int,
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve claim (final approval)."""
    
    if not (current_user.is_manager or current_user.is_finance):
        raise HTTPException(status_code=403, detail="Access denied")
    
    expense_service = ExpenseClaimService(db)
    
    try:
        claim = expense_service.approve_claim(claim_id, current_user.id, notes)
        return {"message": "Claim approved successfully", "claim_number": claim.claim_number}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/reject")
async def reject_claim(
    claim_id: int,
    reason: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject claim."""
    
    if not (current_user.is_manager or current_user.is_finance):
        raise HTTPException(status_code=403, detail="Access denied")
    
    expense_service = ExpenseClaimService(db)
    
    try:
        claim = expense_service.reject_claim(claim_id, current_user.id, reason)
        return {"message": "Claim rejected", "claim_number": claim.claim_number}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/items/{item_id}/upload-receipt")
async def upload_receipt(
    claim_id: int,
    item_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload receipt image for expense item."""
    
    # Verify access
    item = db.query(ExpenseItem).filter(
        ExpenseItem.id == item_id,
        ExpenseItem.expense_claim_id == claim_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Expense item not found")
    
    if item.expense_claim.claimant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    # Save file
    import os
    import uuid
    from app.core.config import settings
    
    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, "receipts")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create attachment record
    from app.models.expense import ExpenseAttachment
    import hashlib
    
    file_hash = hashlib.sha256(content).hexdigest()
    
    attachment = ExpenseAttachment(
        expense_item_id=item_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        file_hash=file_hash,
        uploaded_by_id=current_user.id,
        processing_status="pending"
    )
    
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
    # Process OCR asynchronously
    ocr_service = OCRService(db)
    
    try:
        # Create thumbnail
        ocr_service.create_thumbnail(attachment.id)
        
        # Compress image
        ocr_service.compress_image(attachment.id)
        
        # Process OCR
        ocr_result = ocr_service.process_receipt_image(attachment.id)
        
        return {
            "message": "Receipt uploaded successfully",
            "attachment_id": attachment.id,
            "ocr_result": ocr_result
        }
        
    except Exception as e:
        # OCR failed, but file upload succeeded
        return {
            "message": "Receipt uploaded successfully, OCR processing failed",
            "attachment_id": attachment.id,
            "error": str(e)
        }


@router.get("/reports/summary")
async def get_expense_summary(
    company_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get expense summary report by category."""
    
    if not (current_user.is_manager or current_user.is_finance):
        raise HTTPException(status_code=403, detail="Access denied")
    
    expense_service = ExpenseClaimService(db)
    
    summary = expense_service.get_expense_summary_by_category(
        company_id=company_id,
        date_from=date_from,
        date_to=date_to,
        status=status
    )
    
    return {"summary": summary}


@router.get("/currency/convert")
async def convert_currency(
    amount: Decimal = Query(...),
    from_currency: str = Query(...),
    to_currency: str = Query("HKD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Convert currency amount."""
    
    currency_service = CurrencyService(db)
    
    try:
        result = currency_service.convert_amount(amount, from_currency, to_currency)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/currency/rates")
async def get_exchange_rates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current exchange rates."""
    
    currency_service = CurrencyService(db)
    currencies = currency_service.get_supported_currencies()
    
    return {"currencies": currencies}


@router.post("/currency/update-rates")
async def update_exchange_rates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update exchange rates from external sources (admin only)."""
    
    if not current_user.is_finance:
        raise HTTPException(status_code=403, detail="Access denied")
    
    currency_service = CurrencyService(db)
    
    try:
        import asyncio
        result = await currency_service.update_all_rates()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))