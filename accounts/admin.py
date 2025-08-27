from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced admin interface for managing Krystal Group users."""
    
    # Fields to display in the user list
    list_display = [
        'employee_id', 'username', 'first_name', 'last_name', 
        'email', 'department', 'role', 'location', 'is_active', 'is_staff'
    ]
    
    # Fields to filter by
    list_filter = [
        'role', 'location', 'department', 'is_active', 'is_staff', 'is_superuser'
    ]
    
    # Fields to search
    search_fields = ['username', 'first_name', 'last_name', 'email', 'employee_id', 'department']
    
    # Ordering
    ordering = ['employee_id']
    
    # Custom fieldsets for the user edit form
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        (_('Employee Information'), {
            'fields': ('employee_id', 'department', 'position', 'manager', 'role', 'location')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Preferences'), {
            'fields': ('preferred_language',),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        (_('Employee Information'), {
            'classes': ('wide',),
            'fields': ('employee_id', 'first_name', 'last_name', 'department', 'position', 'role', 'location'),
        }),
        (_('Permissions'), {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff'),
        }),
    )
    
    # Make employee_id readonly in edit form
    readonly_fields = ['date_joined', 'last_login']
    
    # Custom actions
    actions = ['make_active', 'make_inactive', 'reset_passwords']
    
    def make_active(self, request, queryset):
        """Mark selected users as active."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} users marked as active.')
    make_active.short_description = 'Mark selected users as active'
    
    def make_inactive(self, request, queryset):
        """Mark selected users as inactive."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} users marked as inactive.')
    make_inactive.short_description = 'Mark selected users as inactive'
    
    def reset_passwords(self, request, queryset):
        """Reset passwords for selected users to 'temp123'."""
        count = 0
        for user in queryset:
            user.set_password('temp123')
            user.save()
            count += 1
        self.message_user(request, f'Passwords reset for {count} users to "temp123".')
    reset_passwords.short_description = 'Reset passwords to "temp123"'
