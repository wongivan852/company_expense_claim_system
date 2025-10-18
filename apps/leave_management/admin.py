"""
Admin configuration for Leave Management app.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib import messages
from .models import (
    LeaveType, LeaveApplication, LeaveBalance,
    SpecialWorkClaim, SpecialLeaveApplication, SpecialLeaveBalance
)

User = get_user_model()


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_days_per_year', 'requires_approval', 'is_active']
    list_filter = ['requires_approval', 'is_active']
    search_fields = ['name', 'description']


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'leave_type', 'date_from', 'date_to', 'days_applied', 'status', 'created_at']
    list_filter = ['status', 'leave_type', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'reason']
    date_hierarchy = 'created_at'
    readonly_fields = ['days_applied', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'leave_type', 'approved_by')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'leave_type', 'year', 'opening_balance', 'carried_forward', 'current_year_entitlement', 'taken', 'balance']
    list_filter = ['leave_type', 'year']
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    readonly_fields = ['balance']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'leave_type')


@admin.register(SpecialWorkClaim)
class SpecialWorkClaimAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_name', 'work_date', 'session', 'status', 'credits_earned', 'priority', 'created_at']
    list_filter = ['status', 'session', 'priority', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'event_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['credits_earned', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'approved_by')


@admin.register(SpecialLeaveApplication)
class SpecialLeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_from', 'date_to', 'days_applied', 'credits_used', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'reason']
    date_hierarchy = 'created_at'
    readonly_fields = ['days_applied', 'credits_used', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'approved_by')


@admin.register(SpecialLeaveBalance)
class SpecialLeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'earned', 'used', 'balance', 'year']
    list_filter = ['year']
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    readonly_fields = ['balance']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
