from django.contrib import admin
from .models import Company, ExpenseCategory, Currency, ExchangeRate, ExpenseClaim, ClaimComment, ClaimStatusHistory


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for managing companies."""
    list_display = ['name', 'code', 'company_type', 'base_currency', 'is_active']
    list_filter = ['company_type', 'is_active', 'base_currency']
    search_fields = ['name', 'code', 'name_chinese']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Admin interface for managing expense categories."""
    list_display = ['name', 'code', 'name_chinese', 'requires_receipt', 'is_travel_related', 'is_active', 'sort_order']
    list_filter = ['is_active', 'requires_receipt', 'is_travel_related', 'requires_participants']
    search_fields = ['name', 'code', 'name_chinese', 'name_simplified']
    ordering = ['sort_order', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'name_chinese', 'name_simplified', 'description')
        }),
        ('Settings', {
            'fields': ('is_active', 'requires_receipt', 'is_travel_related', 'requires_participants', 'sort_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Admin interface for managing currencies."""
    list_display = ['code', 'name', 'symbol', 'is_base_currency', 'is_active']
    list_filter = ['is_base_currency', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['name']


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """Admin interface for managing exchange rates."""
    list_display = ['currency', 'rate_to_base', 'effective_date']
    list_filter = ['currency', 'effective_date']
    ordering = ['-effective_date', 'currency']


@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(admin.ModelAdmin):
    """Admin interface for managing expense claims."""
    list_display = ['claim_number', 'claimant', 'company', 'total_amount_hkd', 'status', 'submitted_at']
    list_filter = ['status', 'company', 'submitted_at']
    search_fields = ['claim_number', 'claimant__username', 'claimant__email', 'event_name']
    readonly_fields = ['claim_number', 'created_at', 'updated_at']
    date_hierarchy = 'submitted_at'
    ordering = ['-created_at']


@admin.register(ClaimComment)
class ClaimCommentAdmin(admin.ModelAdmin):
    """Admin interface for managing claim comments."""
    list_display = ['expense_claim', 'author', 'created_at', 'comment_preview']
    list_filter = ['created_at', 'author', 'is_internal']
    search_fields = ['expense_claim__claim_number', 'author__username', 'comment']
    ordering = ['-created_at']
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment Preview'


@admin.register(ClaimStatusHistory)
class ClaimStatusHistoryAdmin(admin.ModelAdmin):
    """Admin interface for managing claim status history."""
    list_display = ['expense_claim', 'old_status', 'new_status', 'changed_by', 'created_at', 'notes_preview']
    list_filter = ['old_status', 'new_status', 'created_at']
    search_fields = ['expense_claim__claim_number', 'changed_by__username']
    ordering = ['-created_at']
    
    def notes_preview(self, obj):
        if obj.notes:
            return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
        return '-'
    notes_preview.short_description = 'Notes Preview'
