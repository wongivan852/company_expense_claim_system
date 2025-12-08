"""
Stripe Management Models

Models for managing Stripe accounts and transactions in the integrated business platform.
"""
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class StripeAccount(models.Model):
    """Stripe account configuration and management"""
    name = models.CharField(max_length=100, help_text="Account display name")
    api_key = models.CharField(max_length=200, help_text="Stripe API key")
    account_id = models.CharField(max_length=100, unique=True, help_text="Stripe account ID")
    is_active = models.BooleanField(default=True, help_text="Whether this account is active")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Link to user who manages this account
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_stripe_accounts',
        help_text="User who manages this Stripe account"
    )

    class Meta:
        db_table = 'stripe_accounts'
        ordering = ['-created_at']
        verbose_name = 'Stripe Account'
        verbose_name_plural = 'Stripe Accounts'

    def __str__(self):
        return f'{self.name} ({self.account_id})'

    def __repr__(self):
        return f'<StripeAccount {self.name}>'


class Transaction(models.Model):
    """Stripe transaction record"""

    STATUS_CHOICES = [
        ('succeeded', 'Succeeded'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('canceled', 'Canceled'),
    ]

    TYPE_CHOICES = [
        ('charge', 'Charge'),
        ('refund', 'Refund'),
        ('payout', 'Payout'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
    ]

    stripe_id = models.CharField(max_length=100, unique=True, db_index=True, help_text="Stripe transaction ID")
    account = models.ForeignKey(
        StripeAccount,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="Associated Stripe account"
    )

    # Transaction details
    amount = models.IntegerField(help_text="Amount in cents")
    fee = models.IntegerField(default=0, help_text="Processing fee in cents")
    currency = models.CharField(max_length=3, default='usd', help_text="Currency code (usd, eur, etc.)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, help_text="Transaction type")

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, help_text="Record creation time")
    updated_at = models.DateTimeField(auto_now=True)
    stripe_created = models.DateTimeField(help_text="Transaction time from Stripe")

    # Customer and metadata
    customer_email = models.EmailField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    stripe_metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata from Stripe")

    class Meta:
        db_table = 'stripe_transactions'
        ordering = ['-stripe_created']
        verbose_name = 'Stripe Transaction'
        verbose_name_plural = 'Stripe Transactions'
        indexes = [
            models.Index(fields=['-stripe_created']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f'{self.stripe_id}: {self.amount_formatted} {self.currency.upper()}'

    def __repr__(self):
        return f'<Transaction {self.stripe_id}: {self.amount/100} {self.currency}>'

    @property
    def amount_formatted(self):
        """Return amount in dollars/euros etc (divided by 100)"""
        return self.amount / 100

    @property
    def fee_formatted(self):
        """Return fee in dollars/euros etc (divided by 100)"""
        return (self.fee or 0) / 100

    @property
    def net_amount_formatted(self):
        """Return net amount after fees in dollars/euros etc"""
        return self.amount_formatted - self.fee_formatted

    @property
    def net_amount(self):
        """Return net amount in cents"""
        return self.amount - (self.fee or 0)


class MonthlyStatement(models.Model):
    """Monthly reconciliation statement for Stripe accounts"""

    account = models.ForeignKey(
        StripeAccount,
        on_delete=models.CASCADE,
        related_name='statements',
        help_text="Associated Stripe account"
    )

    # Statement period
    year = models.IntegerField(help_text="Statement year")
    month = models.IntegerField(help_text="Statement month (1-12)")

    # Balances
    opening_balance = models.IntegerField(default=0, help_text="Opening balance in cents")
    closing_balance = models.IntegerField(default=0, help_text="Closing balance in cents")
    total_charges = models.IntegerField(default=0, help_text="Total charges in cents")
    total_refunds = models.IntegerField(default=0, help_text="Total refunds in cents")
    total_fees = models.IntegerField(default=0, help_text="Total fees in cents")
    total_payouts = models.IntegerField(default=0, help_text="Total payouts in cents")

    # Status
    is_reconciled = models.BooleanField(default=False, help_text="Whether statement is reconciled")
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciled_statements'
    )

    # Metadata
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stripe_monthly_statements'
        ordering = ['-year', '-month']
        unique_together = [['account', 'year', 'month']]
        verbose_name = 'Monthly Statement'
        verbose_name_plural = 'Monthly Statements'
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['is_reconciled']),
        ]

    def __str__(self):
        return f'{self.account.name} - {self.year}-{self.month:02d}'

    @property
    def opening_balance_formatted(self):
        return self.opening_balance / 100

    @property
    def closing_balance_formatted(self):
        return self.closing_balance / 100

    @property
    def total_charges_formatted(self):
        return self.total_charges / 100

    @property
    def total_refunds_formatted(self):
        return self.total_refunds / 100

    @property
    def total_fees_formatted(self):
        return self.total_fees / 100

    @property
    def total_payouts_formatted(self):
        return self.total_payouts / 100
