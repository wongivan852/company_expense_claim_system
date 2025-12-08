"""Models for reporting and analytics."""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json


class ReportTemplate(models.Model):
    """Templates for generating various types of reports."""
    
    REPORT_TYPES = [
        ('individual_summary', _('Individual Expense Summary')),
        ('department_summary', _('Department Expense Summary')),
        ('monthly_analytics', _('Monthly Expense Analytics')),
        ('quarterly_analytics', _('Quarterly Expense Analytics')),
        ('currency_breakdown', _('Currency Breakdown Report')),
        ('category_analysis', _('Category Analysis Report')),
        ('approval_summary', _('Approval Summary Report')),
        ('audit_trail', _('Audit Trail Report')),
    ]
    
    name = models.CharField(
        _("Template Name"),
        max_length=100
    )
    
    report_type = models.CharField(
        _("Report Type"),
        max_length=30,
        choices=REPORT_TYPES
    )
    
    description = models.TextField(
        _("Description"),
        blank=True
    )
    
    # Template configuration
    template_file = models.CharField(
        _("Template File"),
        max_length=200,
        help_text=_("Path to template file")
    )
    
    parameters = models.JSONField(
        _("Default Parameters"),
        default=dict,
        blank=True,
        help_text=_("Default parameters for this report template")
    )
    
    # Access control
    is_public = models.BooleanField(
        _("Public"),
        default=False,
        help_text=_("Available to all users")
    )
    
    allowed_roles = models.JSONField(
        _("Allowed Roles"),
        default=list,
        blank=True,
        help_text=_("User roles that can access this report")
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Created By")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Report Template")
        verbose_name_plural = _("Report Templates")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
    
    def can_access(self, user):
        """Check if user can access this report template."""
        if self.is_public:
            return True
        if user.is_admin():
            return True
        return user.role in self.allowed_roles


class SavedReport(models.Model):
    """Saved report configurations and results."""
    
    name = models.CharField(
        _("Report Name"),
        max_length=100
    )
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='saved_reports',
        verbose_name=_("Report Template")
    )
    
    # Report parameters
    parameters = models.JSONField(
        _("Report Parameters"),
        default=dict,
        help_text=_("Parameters used to generate this report")
    )
    
    # Date filters
    date_from = models.DateField(
        _("Date From"),
        null=True,
        blank=True
    )
    
    date_to = models.DateField(
        _("Date To"),
        null=True,
        blank=True
    )
    
    # Filters
    department_filter = models.CharField(
        _("Department Filter"),
        max_length=100,
        blank=True
    )
    
    category_filter = models.CharField(
        _("Category Filter"),
        max_length=100,
        blank=True
    )
    
    status_filter = models.CharField(
        _("Status Filter"),
        max_length=20,
        blank=True
    )
    
    # Results cache
    cached_results = models.JSONField(
        _("Cached Results"),
        default=dict,
        blank=True,
        help_text=_("Cached report results for performance")
    )
    
    cache_expires_at = models.DateTimeField(
        _("Cache Expires At"),
        null=True,
        blank=True
    )
    
    # Ownership and sharing
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_reports',
        verbose_name=_("Created By")
    )
    
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_reports',
        verbose_name=_("Shared With")
    )
    
    is_public = models.BooleanField(
        _("Public Report"),
        default=False,
        help_text=_("Visible to all users with report access")
    )
    
    # Scheduling
    is_scheduled = models.BooleanField(
        _("Scheduled"),
        default=False,
        help_text=_("Generate this report automatically")
    )
    
    schedule_frequency = models.CharField(
        _("Schedule Frequency"),
        max_length=20,
        choices=[
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
            ('monthly', _('Monthly')),
            ('quarterly', _('Quarterly')),
        ],
        blank=True
    )
    
    last_generated = models.DateTimeField(
        _("Last Generated"),
        null=True,
        blank=True
    )
    
    next_generation = models.DateTimeField(
        _("Next Generation"),
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Saved Report")
        verbose_name_plural = _("Saved Reports")
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} - {self.template.name}"
    
    def can_access(self, user):
        """Check if user can access this saved report."""
        if self.created_by == user:
            return True
        if self.is_public and self.template.can_access(user):
            return True
        return user in self.shared_with.all() or user.is_admin()
    
    @property
    def is_cache_valid(self):
        """Check if cached results are still valid."""
        if not self.cache_expires_at:
            return False
        from django.utils import timezone
        return timezone.now() < self.cache_expires_at


class ExpenseAnalytics(models.Model):
    """Aggregated expense analytics data."""
    
    PERIOD_TYPES = [
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('yearly', _('Yearly')),
    ]
    
    period_type = models.CharField(
        _("Period Type"),
        max_length=10,
        choices=PERIOD_TYPES
    )
    
    period_start = models.DateField(
        _("Period Start"),
        help_text=_("Start date of the period")
    )
    
    period_end = models.DateField(
        _("Period End"),
        help_text=_("End date of the period")
    )
    
    # Aggregated metrics
    total_claims = models.PositiveIntegerField(
        _("Total Claims"),
        default=0
    )
    
    total_amount_hkd = models.DecimalField(
        _("Total Amount (HKD)"),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    approved_claims = models.PositiveIntegerField(
        _("Approved Claims"),
        default=0
    )
    
    approved_amount_hkd = models.DecimalField(
        _("Approved Amount (HKD)"),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    rejected_claims = models.PositiveIntegerField(
        _("Rejected Claims"),
        default=0
    )
    
    pending_claims = models.PositiveIntegerField(
        _("Pending Claims"),
        default=0
    )
    
    average_claim_amount = models.DecimalField(
        _("Average Claim Amount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Breakdown by category
    category_breakdown = models.JSONField(
        _("Category Breakdown"),
        default=dict,
        help_text=_("Amount breakdown by expense category")
    )
    
    # Breakdown by currency
    currency_breakdown = models.JSONField(
        _("Currency Breakdown"),
        default=dict,
        help_text=_("Amount breakdown by currency")
    )
    
    # Breakdown by department
    department_breakdown = models.JSONField(
        _("Department Breakdown"),
        default=dict,
        help_text=_("Amount breakdown by department")
    )
    
    # Processing times
    average_approval_time_hours = models.DecimalField(
        _("Average Approval Time (Hours)"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    calculated_at = models.DateTimeField(
        _("Calculated At"),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _("Expense Analytics")
        verbose_name_plural = _("Expense Analytics")
        ordering = ['-period_start']
        unique_together = ['period_type', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.get_period_type_display()} Analytics: {self.period_start} - {self.period_end}"


class DashboardWidget(models.Model):
    """User-customizable dashboard widgets."""
    
    WIDGET_TYPES = [
        ('expense_summary', _('Expense Summary')),
        ('recent_claims', _('Recent Claims')),
        ('pending_approvals', _('Pending Approvals')),
        ('category_chart', _('Category Chart')),
        ('monthly_trend', _('Monthly Trend')),
        ('currency_breakdown', _('Currency Breakdown')),
        ('approval_stats', _('Approval Statistics')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_widgets',
        verbose_name=_("User")
    )
    
    widget_type = models.CharField(
        _("Widget Type"),
        max_length=20,
        choices=WIDGET_TYPES
    )
    
    title = models.CharField(
        _("Widget Title"),
        max_length=100,
        blank=True
    )
    
    configuration = models.JSONField(
        _("Widget Configuration"),
        default=dict,
        help_text=_("Widget-specific configuration options")
    )
    
    position_row = models.PositiveIntegerField(
        _("Row Position"),
        default=1
    )
    
    position_col = models.PositiveIntegerField(
        _("Column Position"),
        default=1
    )
    
    width = models.PositiveIntegerField(
        _("Width"),
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_("Width in grid columns (1-12)")
    )
    
    height = models.PositiveIntegerField(
        _("Height"),
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_("Height in grid rows")
    )
    
    is_visible = models.BooleanField(
        _("Visible"),
        default=True
    )
    
    refresh_interval = models.PositiveIntegerField(
        _("Refresh Interval (seconds)"),
        default=300,
        help_text=_("How often to refresh widget data")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Dashboard Widget")
        verbose_name_plural = _("Dashboard Widgets")
        ordering = ['user', 'position_row', 'position_col']
        unique_together = ['user', 'position_row', 'position_col']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_widget_type_display()}"


class ReportSchedule(models.Model):
    """Scheduled report generation."""
    
    name = models.CharField(
        _("Schedule Name"),
        max_length=100
    )
    
    report_template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_("Report Template")
    )
    
    # Schedule configuration
    FREQUENCY_CHOICES = [
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
    ]
    
    frequency = models.CharField(
        _("Frequency"),
        max_length=10,
        choices=FREQUENCY_CHOICES
    )
    
    # Time settings
    run_time = models.TimeField(
        _("Run Time"),
        help_text=_("Time of day to generate the report")
    )
    
    # Recipients
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='scheduled_reports',
        verbose_name=_("Recipients")
    )
    
    email_subject = models.CharField(
        _("Email Subject"),
        max_length=200,
        blank=True
    )
    
    email_body = models.TextField(
        _("Email Body"),
        blank=True,
        help_text=_("Email body template")
    )
    
    # Parameters
    parameters = models.JSONField(
        _("Report Parameters"),
        default=dict,
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(
        _("Active"),
        default=True
    )
    
    last_run = models.DateTimeField(
        _("Last Run"),
        null=True,
        blank=True
    )
    
    next_run = models.DateTimeField(
        _("Next Run"),
        null=True,
        blank=True
    )
    
    run_count = models.PositiveIntegerField(
        _("Run Count"),
        default=0
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Created By")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Report Schedule")
        verbose_name_plural = _("Report Schedules")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"
    
    def calculate_next_run(self):
        """Calculate the next run time based on frequency."""
        from django.utils import timezone
        from datetime import timedelta, datetime
        
        now = timezone.now()
        
        if self.frequency == 'daily':
            next_run = now.replace(hour=self.run_time.hour, minute=self.run_time.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif self.frequency == 'weekly':
            # Run every Monday at specified time
            days_ahead = 0 - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=self.run_time.hour, minute=self.run_time.minute, second=0, microsecond=0)
        elif self.frequency == 'monthly':
            # Run on first day of next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_run = now.replace(month=now.month + 1, day=1)
            next_run = next_run.replace(hour=self.run_time.hour, minute=self.run_time.minute, second=0, microsecond=0)
        elif self.frequency == 'quarterly':
            # Run on first day of next quarter
            current_quarter = (now.month - 1) // 3 + 1
            if current_quarter == 4:
                next_quarter_month = 1
                next_year = now.year + 1
            else:
                next_quarter_month = current_quarter * 3 + 1
                next_year = now.year
            next_run = now.replace(year=next_year, month=next_quarter_month, day=1)
            next_run = next_run.replace(hour=self.run_time.hour, minute=self.run_time.minute, second=0, microsecond=0)
        
        self.next_run = next_run
        self.save(update_fields=['next_run'])
