"""
Leave Management Models for Integrated Business Platform
Uses the platform's User model from apps.accounts
"""
from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class LeaveType(models.Model):
    """Types of leave available (Annual, Sick, Special, etc.)"""
    name = models.CharField(_("Leave Type"), max_length=50)
    description = models.TextField(_("Description"), blank=True)
    max_days_per_year = models.PositiveIntegerField(_("Max Days Per Year"), default=0)
    requires_approval = models.BooleanField(_("Requires Approval"), default=True)
    is_active = models.BooleanField(_("Is Active"), default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Leave Type")
        verbose_name_plural = _("Leave Types")
        ordering = ['name']


class LeaveApplication(models.Model):
    """Leave application submitted by employees"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('cancelled', _('Cancelled')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    date_from = models.DateTimeField(_("Start Date/Time"))
    date_to = models.DateTimeField(_("End Date/Time"))
    reason = models.TextField(_("Reason"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)

    def calculate_days(self):
        """Calculate the number of leave days based on session logic"""
        if not self.date_from or not self.date_to:
            return 0

        # Convert to local time if timezone-aware
        from django.utils import timezone as tz

        date_from_local = self.date_from
        date_to_local = self.date_to

        # If timezone-aware, convert to local timezone
        if tz.is_aware(self.date_from):
            date_from_local = tz.localtime(self.date_from)
        if tz.is_aware(self.date_to):
            date_to_local = tz.localtime(self.date_to)

        # Get the session info from time components
        start_time = date_from_local.time()
        end_time = date_to_local.time()

        # Determine if it's AM (9:00) or PM (14:00) sessions
        is_start_am = start_time.hour == 9
        is_start_pm = start_time.hour == 14
        is_end_am = end_time.hour == 13  # End of AM session
        is_end_pm = end_time.hour == 18  # End of PM session

        # If same day
        if date_from_local.date() == date_to_local.date():
            if is_start_am and is_end_pm:
                return 1.0  # Full day (AM + PM)
            else:
                return 0.5  # Half day (AM only or PM only)

        # Multiple days - count business days and adjust for partial days
        total_days = 0
        current_date = date_from_local.date()
        end_date = date_to_local.date()

        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday=0, Friday=4
                if current_date == date_from_local.date():
                    # First day - depends on start session
                    total_days += 0.5 if is_start_pm else 1.0
                elif current_date == date_to_local.date():
                    # Last day - depends on end session
                    total_days += 0.5 if is_end_am else 1.0
                else:
                    # Full middle days
                    total_days += 1.0
            current_date += timedelta(days=1)

        return total_days

    @property
    def days_applied(self):
        return self.calculate_days()

    @property
    def back_to_office_date(self):
        """Calculate when employee should return to office"""
        if not self.date_from:
            return None

        # If leave starts in AM (9:00), return same day
        if self.date_from.time().hour == 9:
            return self.date_from.date()

        # If leave is PM only, return next working day
        next_day = self.date_to.date() + timedelta(days=1)
        # Skip weekends
        while next_day.weekday() >= 5:  # Saturday=5, Sunday=6
            next_day += timedelta(days=1)
        return next_day

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.leave_type} ({self.get_status_display()})"

    def can_cancel(self):
        """Check if the leave application can be cancelled."""
        return (self.status == 'pending' and
                self.date_from > timezone.now())

    class Meta:
        verbose_name = _("Leave Application")
        verbose_name_plural = _("Leave Applications")
        ordering = ['-created_at']


class LeaveBalance(models.Model):
    """Leave balance for each user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(_("Year"), default=2025)
    opening_balance = models.DecimalField(_("Opening Balance"), max_digits=5, decimal_places=2, default=0.00)
    carried_forward = models.DecimalField(_("Carried Forward"), max_digits=5, decimal_places=2, default=0.00)
    current_year_entitlement = models.DecimalField(_("Current Year Entitlement"), max_digits=5, decimal_places=2, default=0.00)
    taken = models.DecimalField(_("Taken"), max_digits=5, decimal_places=2, default=0.00)

    @property
    def balance(self):
        return float(self.opening_balance + self.carried_forward + self.current_year_entitlement - self.taken)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.leave_type} ({self.year}): {self.balance}"

    class Meta:
        verbose_name = _("Leave Balance")
        verbose_name_plural = _("Leave Balances")
        unique_together = ['user', 'leave_type', 'year']
        ordering = ['user__last_name', 'leave_type__name']


class SpecialWorkClaim(models.Model):
    """Claims for special work to earn additional leave credits"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    SESSION_CHOICES = [
        ('AM', _('AM (9:00am - 1:00pm)')),
        ('PM', _('PM (2:00pm - 6:00pm)')),
        ('FULL', _('Full Day (9:00am - 6:00pm)')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='special_work_claims')
    work_date = models.DateField(_("Work Date"))
    work_end_date = models.DateField(
        _("Work End Date"),
        null=True,
        blank=True,
        help_text=_("Leave blank for single day")
    )
    session = models.CharField(_("Session"), max_length=10, choices=SESSION_CHOICES)
    event_name = models.CharField(_("Event Name"), max_length=200)
    description = models.TextField(_("Description"))
    priority = models.CharField(_("Priority"), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    credits_earned = models.FloatField(_("Credits Earned"), default=0.0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_special_work'
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)
    manager_comment = models.TextField(_("Manager Comment"), blank=True)

    def get_work_days_count(self):
        """Calculate the number of work days"""
        if not self.work_end_date or self.work_end_date == self.work_date:
            return 1
        return (self.work_end_date - self.work_date).days + 1

    def calculate_credits(self):
        """Calculate credits based on session and work days"""
        days = self.get_work_days_count()
        if self.session == 'FULL':
            return float(days)
        else:  # AM or PM
            return float(days * 0.5)

    def save(self, *args, **kwargs):
        # Auto-calculate credits
        self.credits_earned = self.calculate_credits()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event_name} ({self.work_date})"

    class Meta:
        verbose_name = _("Special Work Claim")
        verbose_name_plural = _("Special Work Claims")
        ordering = ['-created_at']


class SpecialLeaveApplication(models.Model):
    """Leave application using special leave credits"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('cancelled', _('Cancelled')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='special_leave_applications')
    date_from = models.DateTimeField(_("Start Date/Time"))
    date_to = models.DateTimeField(_("End Date/Time"))
    reason = models.TextField(_("Reason"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    credits_used = models.FloatField(_("Credits Used"), default=0.0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_special_leaves'
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)

    def calculate_days(self):
        """Calculate the number of leave days (same as regular leave)"""
        if not self.date_from or not self.date_to:
            return 0

        start_time = self.date_from.time()
        end_time = self.date_to.time()

        is_start_am = start_time.hour == 9
        is_start_pm = start_time.hour == 14
        is_end_am = end_time.hour == 13
        is_end_pm = end_time.hour == 18

        if self.date_from.date() == self.date_to.date():
            if is_start_am and is_end_pm:
                return 1.0
            else:
                return 0.5

        total_days = 0
        current_date = self.date_from.date()
        end_date = self.date_to.date()

        while current_date <= end_date:
            if current_date.weekday() < 5:
                if current_date == self.date_from.date():
                    total_days += 0.5 if is_start_pm else 1.0
                elif current_date == self.date_to.date():
                    total_days += 0.5 if is_end_am else 1.0
                else:
                    total_days += 1.0
            current_date += timedelta(days=1)

        return total_days

    @property
    def days_applied(self):
        return self.calculate_days()

    def save(self, *args, **kwargs):
        # Auto-calculate credits used
        self.credits_used = self.calculate_days()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} - Special Leave ({self.get_status_display()})"

    class Meta:
        verbose_name = _("Special Leave Application")
        verbose_name_plural = _("Special Leave Applications")
        ordering = ['-created_at']


class SpecialLeaveBalance(models.Model):
    """Special leave balance tracking"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='special_leave_balance')
    earned = models.FloatField(_("Earned"), default=0.0, help_text=_("Credits earned from special work claims"))
    used = models.FloatField(_("Used"), default=0.0, help_text=_("Credits used for special leave"))
    year = models.IntegerField(_("Year"), default=2025)

    @property
    def balance(self):
        return self.earned - self.used

    def __str__(self):
        return f"{self.user.get_full_name()} - Special Leave Balance: {self.balance}"

    class Meta:
        verbose_name = _("Special Leave Balance")
        verbose_name_plural = _("Special Leave Balances")
        ordering = ['user__last_name']
        unique_together = ['user', 'year']
