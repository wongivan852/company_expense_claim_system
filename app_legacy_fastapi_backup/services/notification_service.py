"""Notification service for expense claim workflow."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.expense import ExpenseClaim, User
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications during expense claim workflow."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def notify_claim_submitted(self, claim: ExpenseClaim):
        """Notify managers when a claim is submitted."""
        
        # Get claim details
        claimant = claim.claimant
        company = claim.company
        
        # Get managers to notify
        managers = self._get_managers_for_approval(claim)
        
        subject = f"Expense Claim Submitted - {claim.claim_number}"
        
        for manager in managers:
            message = self._create_submission_message(claim, manager)
            self._send_email(manager.email, subject, message)
            
        logger.info(f"Sent submission notifications for claim {claim.claim_number}")
    
    def notify_claim_checked(self, claim: ExpenseClaim):
        """Notify finance team when a claim is checked."""
        
        # Get finance team members
        finance_users = (
            self.db.query(User)
            .filter(User.is_finance == True, User.is_active == True)
            .all()
        )
        
        subject = f"Expense Claim Ready for Approval - {claim.claim_number}"
        
        for finance_user in finance_users:
            message = self._create_checked_message(claim, finance_user)
            self._send_email(finance_user.email, subject, message)
            
        logger.info(f"Sent checked notifications for claim {claim.claim_number}")
    
    def notify_claim_approved(self, claim: ExpenseClaim):
        """Notify claimant and finance when a claim is approved."""
        
        subject = f"Expense Claim Approved - {claim.claim_number}"
        
        # Notify claimant
        claimant_message = self._create_approval_message(claim, claim.claimant)
        self._send_email(claim.claimant.email, subject, claimant_message)
        
        # Notify finance team for payment processing
        finance_users = (
            self.db.query(User)
            .filter(User.is_finance == True, User.is_active == True)
            .all()
        )
        
        finance_subject = f"Expense Claim Approved for Payment - {claim.claim_number}"
        for finance_user in finance_users:
            finance_message = self._create_payment_message(claim, finance_user)
            self._send_email(finance_user.email, finance_subject, finance_message)
            
        logger.info(f"Sent approval notifications for claim {claim.claim_number}")
    
    def notify_claim_rejected(self, claim: ExpenseClaim, reason: str):
        """Notify claimant when a claim is rejected."""
        
        subject = f"Expense Claim Rejected - {claim.claim_number}"
        message = self._create_rejection_message(claim, reason)
        
        self._send_email(claim.claimant.email, subject, message)
        
        logger.info(f"Sent rejection notification for claim {claim.claim_number}")
    
    def _get_managers_for_approval(self, claim: ExpenseClaim) -> List[User]:
        """Get list of managers who should approve this claim."""
        
        managers = []
        
        # Add claimant's direct manager
        if claim.claimant.manager:
            managers.append(claim.claimant.manager)
        
        # Add company managers if no direct manager
        if not managers:
            company_managers = (
                self.db.query(User)
                .filter(
                    User.company_id == claim.company_id,
                    User.is_manager == True,
                    User.is_active == True
                )
                .all()
            )
            managers.extend(company_managers)
        
        # Always include finance team for high-value claims
        if claim.total_amount_hkd > 10000:  # HKD 10,000 threshold
            finance_users = (
                self.db.query(User)
                .filter(User.is_finance == True, User.is_active == True)
                .all()
            )
            managers.extend(finance_users)
        
        return managers
    
    def _create_submission_message(self, claim: ExpenseClaim, recipient: User) -> str:
        """Create email message for claim submission."""
        
        language = recipient.language_preference or "en"
        
        if language.startswith("zh"):
            return self._create_submission_message_chinese(claim, recipient)
        else:
            return self._create_submission_message_english(claim, recipient)
    
    def _create_submission_message_english(self, claim: ExpenseClaim, recipient: User) -> str:
        """Create English submission notification message."""
        
        message = f"""
Dear {recipient.full_name},

A new expense claim has been submitted for your review:

Claim Details:
- Claim Number: {claim.claim_number}
- Claimant: {claim.claimant.full_name}
- Company: {claim.company.name}
- Event/Project: {claim.event_name or 'N/A'}
- Period: {claim.period_from.strftime('%Y-%m-%d')} to {claim.period_to.strftime('%Y-%m-%d')}
- Total Amount: HKD {claim.total_amount_hkd:,.2f}

Please log in to the expense system to review and approve this claim.

System URL: {settings.FRONTEND_URL}/claims/{claim.id}

Best regards,
Expense Management System
"""
        return message
    
    def _create_submission_message_chinese(self, claim: ExpenseClaim, recipient: User) -> str:
        """Create Chinese submission notification message."""
        
        recipient_name = recipient.full_name_chinese or recipient.full_name
        claimant_name = claim.claimant.full_name_chinese or claim.claimant.full_name
        company_name = claim.company.name_chinese or claim.company.name
        event_name = claim.event_name_chinese or claim.event_name or '無'
        
        message = f"""
親愛的 {recipient_name}，

有新的費用申請單需要您審核：

申請詳情：
- 申請單號：{claim.claim_number}
- 申請人：{claimant_name}
- 公司：{company_name}
- 活動/項目：{event_name}
- 期間：{claim.period_from.strftime('%Y-%m-%d')} 至 {claim.period_to.strftime('%Y-%m-%d')}
- 總金額：港幣 {claim.total_amount_hkd:,.2f}

請登入費用管理系統審核此申請。

系統網址：{settings.FRONTEND_URL}/claims/{claim.id}

此致
敬禮

費用管理系統
"""
        return message
    
    def _create_checked_message(self, claim: ExpenseClaim, recipient: User) -> str:
        """Create message for checked claim notification."""
        
        language = recipient.language_preference or "en"
        
        if language.startswith("zh"):
            recipient_name = recipient.full_name_chinese or recipient.full_name
            message = f"""
親愛的 {recipient_name}，

費用申請單 {claim.claim_number} 已完成初步審核，請進行最終批准。

申請詳情：
- 申請人：{claim.claimant.full_name_chinese or claim.claimant.full_name}
- 總金額：港幣 {claim.total_amount_hkd:,.2f}
- 審核人：{claim.checked_by.full_name_chinese or claim.checked_by.full_name}

請登入系統進行最終批准。

系統網址：{settings.FRONTEND_URL}/claims/{claim.id}

此致
敬禮

費用管理系統
"""
        else:
            message = f"""
Dear {recipient.full_name},

Expense claim {claim.claim_number} has been checked and is ready for final approval.

Details:
- Claimant: {claim.claimant.full_name}
- Total Amount: HKD {claim.total_amount_hkd:,.2f}
- Checked by: {claim.checked_by.full_name}

Please log in to provide final approval.

System URL: {settings.FRONTEND_URL}/claims/{claim.id}

Best regards,
Expense Management System
"""
        
        return message
    
    def _create_approval_message(self, claim: ExpenseClaim, recipient: User) -> str:
        """Create message for approval notification."""
        
        language = recipient.language_preference or "en"
        
        if language.startswith("zh"):
            recipient_name = recipient.full_name_chinese or recipient.full_name
            message = f"""
親愛的 {recipient_name}，

您的費用申請單 {claim.claim_number} 已獲批准。

申請詳情：
- 總金額：港幣 {claim.total_amount_hkd:,.2f}
- 批准人：{claim.approved_by.full_name_chinese or claim.approved_by.full_name}
- 批准時間：{claim.approved_at.strftime('%Y-%m-%d %H:%M')}

您的費用將安排付款處理。

此致
敬禮

費用管理系統
"""
        else:
            message = f"""
Dear {recipient.full_name},

Your expense claim {claim.claim_number} has been approved.

Details:
- Total Amount: HKD {claim.total_amount_hkd:,.2f}
- Approved by: {claim.approved_by.full_name}
- Approval Date: {claim.approved_at.strftime('%Y-%m-%d %H:%M')}

Your expenses will be processed for payment.

Best regards,
Expense Management System
"""
        
        return message
    
    def _create_payment_message(self, claim: ExpenseClaim, recipient: User) -> str:
        """Create message for payment processing notification."""
        
        message = f"""
Dear Finance Team,

Expense claim {claim.claim_number} has been approved and requires payment processing.

Payment Details:
- Claimant: {claim.claimant.full_name} ({claim.claimant.employee_id})
- Total Amount: HKD {claim.total_amount_hkd:,.2f}
- Approved by: {claim.approved_by.full_name}
- Approval Date: {claim.approved_at.strftime('%Y-%m-%d %H:%M')}

Category Breakdown:
- Keynote Speech: HKD {claim.keynote_total_hkd:,.2f}
- Sponsor/Guest: HKD {claim.sponsor_total_hkd:,.2f}
- Course Operations: HKD {claim.course_ops_total_hkd:,.2f}
- Exhibition: HKD {claim.exhibition_total_hkd:,.2f}
- Transportation: HKD {claim.transport_total_hkd:,.2f}
- Miscellaneous: HKD {claim.misc_total_hkd:,.2f}
- Business: HKD {claim.business_total_hkd:,.2f}
- Instructor: HKD {claim.instructor_total_hkd:,.2f}
- Procurement: HKD {claim.procurement_total_hkd:,.2f}

Please process payment for this approved claim.

System URL: {settings.FRONTEND_URL}/claims/{claim.id}

Best regards,
Expense Management System
"""
        return message
    
    def _create_rejection_message(self, claim: ExpenseClaim, reason: str) -> str:
        """Create message for rejection notification."""
        
        language = claim.claimant.language_preference or "en"
        
        if language.startswith("zh"):
            recipient_name = claim.claimant.full_name_chinese or claim.claimant.full_name
            message = f"""
親愛的 {recipient_name}，

很抱歉，您的費用申請單 {claim.claim_number} 已被拒絕。

拒絕原因：{reason}

如有疑問，請聯繫您的主管或財務部門。

此致
敬禮

費用管理系統
"""
        else:
            message = f"""
Dear {claim.claimant.full_name},

Unfortunately, your expense claim {claim.claim_number} has been rejected.

Rejection Reason: {reason}

If you have any questions, please contact your manager or the finance department.

Best regards,
Expense Management System
"""
        
        return message
    
    def _send_email(self, to_email: str, subject: str, message: str):
        """Send email notification."""
        
        if not settings.EMAIL_ENABLED:
            logger.info(f"Email sending disabled. Would send to {to_email}: {subject}")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            
            if settings.SMTP_TLS:
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
    
    def send_weekly_summary(self, user_id: int):
        """Send weekly summary of pending claims."""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not (user.is_manager or user.is_finance):
            return
        
        # Get pending claims for this user
        from app.services.expense_service import ExpenseClaimService
        expense_service = ExpenseClaimService(self.db)
        
        pending_claims, total = expense_service.get_claims_for_approval(user_id)
        
        if not pending_claims:
            return
        
        subject = f"Weekly Expense Claims Summary - {total} claims pending"
        
        language = user.language_preference or "en"
        
        if language.startswith("zh"):
            recipient_name = user.full_name_chinese or user.full_name
            message = f"""
親愛的 {recipient_name}，

您有 {total} 個費用申請單等待處理：

"""
            for claim in pending_claims[:10]:  # Show first 10
                claimant_name = claim.claimant.full_name_chinese or claim.claimant.full_name
                message += f"- {claim.claim_number}: {claimant_name} - 港幣 {claim.total_amount_hkd:,.2f}\n"
            
            if total > 10:
                message += f"\n... 還有 {total - 10} 個申請單\n"
            
            message += f"""
請登入系統處理這些申請：{settings.FRONTEND_URL}/approvals

此致
敬禮

費用管理系統
"""
        else:
            message = f"""
Dear {user.full_name},

You have {total} expense claims pending approval:

"""
            for claim in pending_claims[:10]:  # Show first 10
                message += f"- {claim.claim_number}: {claim.claimant.full_name} - HKD {claim.total_amount_hkd:,.2f}\n"
            
            if total > 10:
                message += f"\n... and {total - 10} more claims\n"
            
            message += f"""
Please log in to review these claims: {settings.FRONTEND_URL}/approvals

Best regards,
Expense Management System
"""
        
        self._send_email(user.email, subject, message)