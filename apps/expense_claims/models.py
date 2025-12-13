"""Models for expense claims management."""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from djmoney import models as money_models
from decimal import Decimal
import uuid


class Company(models.Model):
    """Enhanced company model for the 4 business entities."""
    
    # Business entities from requirements
    COMPANY_TYPES = [
        ('holding', _('Holding Company')),
        ('institute', _('Institute/Education')),
        ('technology', _('Technology Company')),
        ('entertainment', _('Entertainment Company')),
    ]
    
    name = models.CharField(
        _("Company Name"),
        max_length=200,
        help_text=_("Official company name")
    )
    
    name_chinese = models.CharField(
        _("Chinese Name"),
        max_length=200,
        blank=True,
        help_text=_("Company name in Chinese")
    )
    
    name_simplified = models.CharField(
        _("Simplified Chinese"),
        max_length=200,
        blank=True,
        help_text=_("Company name in Simplified Chinese")
    )
    
    code = models.CharField(
        _("Company Code"),
        max_length=20,
        unique=True,
        help_text=_("Short company identifier (e.g., CGEL, KIL)")
    )
    
    company_type = models.CharField(
        _("Company Type"),
        max_length=20,
        choices=COMPANY_TYPES,
        default='holding'
    )
    
    address = models.TextField(
        _("Address"),
        blank=True,
        help_text=_("Company address")
    )
    
    address_chinese = models.TextField(
        _("Chinese Address"),
        blank=True,
        help_text=_("Company address in Chinese")
    )
    
    # Business details
    registration_number = models.CharField(
        _("Registration Number"),
        max_length=50,
        blank=True,
        help_text=_("Business registration number")
    )
    
    tax_id = models.CharField(
        _("Tax ID"),
        max_length=50,
        blank=True,
        help_text=_("Tax identification number")
    )
    
    base_currency = models.ForeignKey(
        'Currency',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text=_("Primary currency for this company")
    )
    
    # Regional settings
    timezone = models.CharField(
        _("Timezone"),
        max_length=50,
        default='Asia/Hong_Kong',
        help_text=_("Company timezone")
    )
    
    country_code = models.CharField(
        _("Country Code"),
        max_length=2,
        default='HK',
        help_text=_("ISO country code")
    )
    
    # Business configuration
    requires_manager_approval = models.BooleanField(
        _("Requires Manager Approval"),
        default=True,
        help_text=_("Whether expenses need manager approval")
    )
    
    approval_threshold = models.DecimalField(
        _("Approval Threshold"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Amount above which additional approval is needed")
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'company_type']),
        ]
    
    def __str__(self):
        if self.name_chinese:
            return f"{self.name} ({self.name_chinese})"
        return self.name
    
    def get_display_name(self, language='en'):
        """Get company name in specified language."""
        if language == 'zh-hans':
            return self.name_simplified or self.name_chinese or self.name
        elif language == 'zh-hant':
            return self.name_chinese or self.name
        return self.name


class ExpenseCategory(models.Model):
    """Enhanced categories matching PDF form structure."""
    
    # Business category codes from PDF form
    CATEGORY_CODES = [
        ('keynote_speech', '主題演講'),
        ('sponsor_guest', '贊助嘉賓'),
        ('course_operations', '課程運營推廣'),
        ('exhibition_procurement', '展覽采購'),
        ('other_misc', '其他雜項'),
        ('business_negotiation', '業務商談'),
        ('instructor_misc', '講師雜項'),
        ('procurement_misc', '采購雜項'),
        ('transportation', '交通'),
    ]
    
    code = models.CharField(
        _("Category Code"),
        max_length=50,
        unique=True,
        help_text=_("Internal code for category")
    )
    
    name = models.CharField(
        _("Category Name"),
        max_length=100
    )
    
    name_chinese = models.CharField(
        _("Chinese Name"),
        max_length=100,
        help_text=_("Category name in Chinese")
    )
    
    name_simplified = models.CharField(
        _("Simplified Chinese"),
        max_length=100,
        blank=True,
        help_text=_("Category name in Simplified Chinese")
    )
    
    description = models.TextField(
        _("Description"),
        blank=True
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    requires_receipt = models.BooleanField(
        _("Requires Receipt"),
        default=True,
        help_text=_("Whether this category requires receipt attachment")
    )
    
    # Business logic fields
    is_travel_related = models.BooleanField(
        _("Travel Related"),
        default=False,
        help_text=_("Whether this is a travel-related expense")
    )
    
    requires_participants = models.BooleanField(
        _("Requires Participants"),
        default=False,
        help_text=_("Whether participant details are required")
    )
    
    sort_order = models.PositiveIntegerField(
        _("Sort Order"),
        default=0,
        help_text=_("Order for display in forms")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Expense Category")
        verbose_name_plural = _("Expense Categories")
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'sort_order']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.name_chinese})"
    
    def get_display_name(self, language='en'):
        """Get category name in specified language."""
        if language == 'zh-hans':
            return self.name_simplified or self.name_chinese
        elif language == 'zh-hant':
            return self.name_chinese
        return self.name


class Currency(models.Model):
    """Supported currencies for multi-currency expense claims."""
    
    code = models.CharField(
        _("Currency Code"),
        max_length=3,
        unique=True,
        help_text=_("ISO 4217 currency code (e.g., HKD, RMB)")
    )
    
    name = models.CharField(
        _("Currency Name"),
        max_length=50
    )
    
    symbol = models.CharField(
        _("Symbol"),
        max_length=5,
        blank=True
    )
    
    is_base_currency = models.BooleanField(
        _("Base Currency"),
        default=False,
        help_text=_("Primary currency for reporting (HKD)")
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one base currency
        if self.is_base_currency:
            Currency.objects.filter(is_base_currency=True).update(is_base_currency=False)
        super().save(*args, **kwargs)


class ExchangeRate(models.Model):
    """Exchange rates for currency conversion."""
    
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='exchange_rates'
    )
    
    rate_to_base = models.DecimalField(
        _("Rate to Base Currency"),
        max_digits=10,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text=_("Exchange rate to base currency (HKD)")
    )
    
    effective_date = models.DateTimeField(
        _("Effective Date"),
        help_text=_("When this rate becomes effective")
    )
    
    source = models.CharField(
        _("Source"),
        max_length=50,
        blank=True,
        help_text=_("Source of exchange rate (e.g., xe.com)")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Exchange Rate")
        verbose_name_plural = _("Exchange Rates")
        ordering = ['-effective_date']
        unique_together = ['currency', 'effective_date']
    
    def __str__(self):
        return f"{self.currency.code} = {self.rate_to_base} HKD ({self.effective_date.date()})"


class ExpenseClaim(models.Model):
    """Main expense claim model."""
    
    # Claim states based on requirements
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('paid', _('Paid')),
    ]
    
    # Generate unique claim number
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=20,
        unique=True,
        editable=False
    )
    
    # Basic Information
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='expense_claims',
        verbose_name=_("Claimant")
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        verbose_name=_("Company")
    )
    
    event_name = models.CharField(
        _("Event/Project Name"),
        max_length=200,
        blank=True,
        help_text=_("e.g., IAICC event")
    )
    
    period_from = models.DateField(
        _("Period From"),
        help_text=_("Start date of expense period")
    )
    
    period_to = models.DateField(
        _("Period To"),
        help_text=_("End date of expense period")
    )
    
    # Status and Workflow
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Approval workflow
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_claims',
        verbose_name=_("Checked By")
    )
    
    checked_at = models.DateTimeField(
        _("Checked At"),
        null=True,
        blank=True
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_claims',
        verbose_name=_("Approved By")
    )
    
    approved_at = models.DateTimeField(
        _("Approved At"),
        null=True,
        blank=True
    )
    
    # Rejection details
    rejection_reason = models.TextField(
        _("Rejection Reason"),
        blank=True
    )
    
    # Totals (calculated from line items)
    total_amount_original = models.DecimalField(
        _("Total Amount (Original)"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )
    
    total_amount_hkd = models.DecimalField(
        _("Total Amount (HKD)"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(
        _("Submitted At"),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("Expense Claim")
        verbose_name_plural = _("Expense Claims")
        ordering = ['-created_at']
        permissions = [
            ('can_approve_claims', 'Can approve expense claims'),
            ('can_view_all_claims', 'Can view all expense claims'),
        ]
    
    def __str__(self):
        return f"{self.claim_number} - {self.claimant.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            self.claim_number = self.generate_claim_number()
        super().save(*args, **kwargs)
    
    def generate_claim_number(self):
        """Generate unique claim number."""
        import datetime
        today = datetime.date.today()
        prefix = f"CGGE{today.strftime('%Y%m')}"
        
        # Get the last claim number for this month
        last_claim = ExpenseClaim.objects.filter(
            claim_number__startswith=prefix
        ).order_by('-claim_number').first()
        
        if last_claim:
            last_number = int(last_claim.claim_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def can_edit(self, user):
        """Check if user can edit this claim."""
        return (
            self.status == 'draft' and 
            self.claimant == user
        ) or user.is_admin()
    
    def can_approve(self, user):
        """Check if user can approve this claim."""
        return (
            self.status in ['submitted', 'under_review'] and
            user.can_approve_claims() and
            user != self.claimant
        )
    
    def can_delete(self, user):
        """Check if user can delete this claim."""
        # Only allow deletion of draft claims by the owner or admin users
        return (
            self.status == 'draft' and 
            (self.claimant == user or user.is_staff)
        )
    
    def update_totals(self):
        """Update total amounts from line items."""
        items = self.expense_items.all()
        self.total_amount_original = sum(item.original_amount for item in items)
        self.total_amount_hkd = sum(item.amount_hkd for item in items)
        self.save(update_fields=['total_amount_original', 'total_amount_hkd'])


class ExpenseItem(models.Model):
    """Individual expense line items."""
    
    expense_claim = models.ForeignKey(
        ExpenseClaim,
        on_delete=models.CASCADE,
        related_name='expense_items'
    )
    
    item_number = models.PositiveIntegerField(
        _("Item Number"),
        help_text=_("Sequential number within the claim")
    )
    
    expense_date = models.DateField(
        _("Expense Date"),
        help_text=_("Date when the expense was incurred")
    )
    
    description = models.TextField(
        _("Description"),
        help_text=_("Detailed description of the expense")
    )
    
    description_chinese = models.TextField(
        _("Chinese Description"),
        blank=True,
        help_text=_("Description in Chinese")
    )
    
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        verbose_name=_("Category")
    )
    
    # Amount and Currency (negative values allowed for refunds)
    original_amount = models.DecimalField(
        _("Original Amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Enter positive amount for expenses, negative for refunds")
    )
    
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name=_("Currency")
    )
    
    exchange_rate = models.DecimalField(
        _("Exchange Rate"),
        max_digits=10,
        decimal_places=6,
        help_text=_("Rate used for conversion to HKD")
    )
    
    amount_hkd = models.DecimalField(
        _("Amount (HKD)"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Amount converted to HKD")
    )
    
    # Receipt information
    has_receipt = models.BooleanField(
        _("Has Receipt"),
        default=True,
        help_text=_("Whether receipt is available")
    )
    
    receipt_notes = models.CharField(
        _("Receipt Notes"),
        max_length=200,
        blank=True,
        help_text=_("e.g., 'Paper receipt', 'without receipt'")
    )
    
    # Additional details
    location = models.CharField(
        _("Location"),
        max_length=200,
        blank=True,
        help_text=_("Location where expense was incurred")
    )
    
    participants = models.CharField(
        _("Participants"),
        max_length=200,
        blank=True,
        help_text=_("People involved (e.g., 'Total 2 persons included Jeff and Ivan')")
    )
    
    notes = models.TextField(
        _("Additional Notes"),
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Expense Item")
        verbose_name_plural = _("Expense Items")
        ordering = ['expense_claim', 'item_number']
        unique_together = ['expense_claim', 'item_number']
    
    def __str__(self):
        return f"{self.expense_claim.claim_number} - Item {self.item_number}"
    
    def save(self, *args, **kwargs):
        # Calculate HKD amount if not provided
        if not self.amount_hkd:
            self.amount_hkd = self.original_amount * self.exchange_rate
        
        # Auto-assign item number if not provided
        if not self.item_number:
            last_item = ExpenseItem.objects.filter(
                expense_claim=self.expense_claim
            ).order_by('-item_number').first()
            
            self.item_number = (last_item.item_number + 1) if last_item else 1
        
        super().save(*args, **kwargs)
        
        # Update claim totals
        self.expense_claim.update_totals()


class ClaimComment(models.Model):
    """Comments and feedback on expense claims."""
    
    expense_claim = models.ForeignKey(
        ExpenseClaim,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Author")
    )
    
    comment = models.TextField(
        _("Comment"),
        help_text=_("Feedback or notes about the claim")
    )
    
    is_internal = models.BooleanField(
        _("Internal Comment"),
        default=False,
        help_text=_("Only visible to managers and admins")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Claim Comment")
        verbose_name_plural = _("Claim Comments")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.expense_claim.claim_number} by {self.author.get_full_name()}"


class ClaimStatusHistory(models.Model):
    """Track status changes for audit trail."""
    
    expense_claim = models.ForeignKey(
        ExpenseClaim,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Changed By")
    )
    
    old_status = models.CharField(
        _("Old Status"),
        max_length=20,
        choices=ExpenseClaim.STATUS_CHOICES
    )
    
    new_status = models.CharField(
        _("New Status"),
        max_length=20,
        choices=ExpenseClaim.STATUS_CHOICES
    )
    
    notes = models.TextField(
        _("Notes"),
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Status History")
        verbose_name_plural = _("Status Histories")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.expense_claim.claim_number}: {self.old_status} → {self.new_status}"
