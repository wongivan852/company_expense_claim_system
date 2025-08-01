"""User models for the expense claim system."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Supports multi-location operations for CG Global Entertainment Ltd.
    """
    
    # Additional user fields based on requirements
    employee_id = models.CharField(
        _("Employee ID"),
        max_length=20,
        unique=True,
        help_text=_("Unique employee identifier")
    )
    
    department = models.CharField(
        _("Department"),
        max_length=100,
        blank=True,
        help_text=_("Employee's department")
    )
    
    position = models.CharField(
        _("Position"),
        max_length=100,
        blank=True,
        help_text=_("Employee's job position")
    )
    
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_employees',
        verbose_name=_("Manager"),
        help_text=_("Direct manager for approval workflow")
    )
    
    # Role-based access control
    ROLE_CHOICES = [
        ('staff', _('Staff')),
        ('manager', _('Manager')),
        ('admin', _('Admin')),
    ]
    
    role = models.CharField(
        _("Role"),
        max_length=10,
        choices=ROLE_CHOICES,
        default='staff',
        help_text=_("User role for permissions")
    )
    
    # Geographic considerations
    LOCATION_CHOICES = [
        ('hk', _('Hong Kong')),
        ('cn', _('China')),
        ('other', _('Other')),
    ]
    
    location = models.CharField(
        _("Location"),
        max_length=10,
        choices=LOCATION_CHOICES,
        default='hk',
        help_text=_("Primary work location")
    )
    
    # Contact information
    phone = models.CharField(
        _("Phone Number"),
        max_length=20,
        blank=True
    )
    
    # Preferences
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('zh-hans', _('Simplified Chinese')),
    ]
    
    preferred_language = models.CharField(
        _("Preferred Language"),
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en'
    )
    
    # Additional fields
    date_joined = models.DateTimeField(_("Date Joined"), auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(
        _("Last Login IP"),
        null=True,
        blank=True
    )
    
    # Security fields
    two_factor_enabled = models.BooleanField(
        _("Two Factor Authentication"),
        default=False,
        help_text=_("Enable two-factor authentication")
    )
    
    failed_login_attempts = models.PositiveIntegerField(
        _("Failed Login Attempts"),
        default=0
    )
    
    account_locked_until = models.DateTimeField(
        _("Account Locked Until"),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id})"
    
    def get_full_name(self):
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_manager(self):
        """Check if user is a manager."""
        return self.role in ['manager', 'admin']
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin'
    
    def can_approve_claims(self):
        """Check if user can approve expense claims."""
        return self.is_manager()
    
    def get_managed_employees(self):
        """Get all employees managed by this user."""
        return self.managed_employees.filter(is_active=True)


class UserProfile(models.Model):
    """
    Extended user profile for additional information.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    avatar = models.ImageField(
        _("Avatar"),
        upload_to='avatars/',
        null=True,
        blank=True
    )
    
    bio = models.TextField(
        _("Bio"),
        max_length=500,
        blank=True
    )
    
    birthday = models.DateField(
        _("Birthday"),
        null=True,
        blank=True
    )
    
    emergency_contact_name = models.CharField(
        _("Emergency Contact Name"),
        max_length=100,
        blank=True
    )
    
    emergency_contact_phone = models.CharField(
        _("Emergency Contact Phone"),
        max_length=20,
        blank=True
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(
        _("Email Notifications"),
        default=True,
        help_text=_("Receive email notifications for claim updates")
    )
    
    sms_notifications = models.BooleanField(
        _("SMS Notifications"),
        default=False,
        help_text=_("Receive SMS notifications for urgent updates")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"


class LoginHistory(models.Model):
    """
    Track user login history for security purposes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    
    ip_address = models.GenericIPAddressField(_("IP Address"))
    user_agent = models.TextField(_("User Agent"), blank=True)
    login_time = models.DateTimeField(_("Login Time"), auto_now_add=True)
    success = models.BooleanField(_("Success"), default=True)
    
    class Meta:
        verbose_name = _("Login History")
        verbose_name_plural = _("Login Histories")
        ordering = ['-login_time']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.user.username} - {status} - {self.login_time}"
