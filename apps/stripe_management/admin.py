"""
Stripe Management Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import StripeAccount, Transaction, MonthlyStatement


@admin.register(StripeAccount)
class StripeAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_id', 'manager', 'is_active', 'transaction_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'account_id', 'manager__username', 'manager__email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Account Information', {
            'fields': ('name', 'account_id', 'api_key', 'is_active')
        }),
        ('Management', {
            'fields': ('manager',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def transaction_count(self, obj):
        count = obj.transactions.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    transaction_count.short_description = 'Transactions'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['stripe_id', 'account', 'type', 'status', 'amount_display', 'fee_display',
                    'net_display', 'currency', 'customer_email', 'stripe_created']
    list_filter = ['status', 'type', 'currency', 'stripe_created', 'account']
    search_fields = ['stripe_id', 'customer_email', 'description', 'account__name']
    readonly_fields = ['created_at', 'updated_at', 'amount_display', 'fee_display', 'net_display']
    date_hierarchy = 'stripe_created'

    fieldsets = (
        ('Transaction Details', {
            'fields': ('stripe_id', 'account', 'type', 'status')
        }),
        ('Financial Information', {
            'fields': ('amount', 'amount_display', 'fee', 'fee_display', 'net_display', 'currency')
        }),
        ('Customer Information', {
            'fields': ('customer_email', 'description')
        }),
        ('Metadata', {
            'fields': ('stripe_metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('stripe_created', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def amount_display(self, obj):
        return format_html('<span style="color: green; font-weight: bold;">${:.2f}</span>', obj.amount_formatted)
    amount_display.short_description = 'Amount'

    def fee_display(self, obj):
        return format_html('<span style="color: red;">${:.2f}</span>', obj.fee_formatted)
    fee_display.short_description = 'Fee'

    def net_display(self, obj):
        return format_html('<span style="color: blue; font-weight: bold;">${:.2f}</span>', obj.net_amount_formatted)
    net_display.short_description = 'Net Amount'


@admin.register(MonthlyStatement)
class MonthlyStatementAdmin(admin.ModelAdmin):
    list_display = ['account', 'period', 'opening_balance_display', 'closing_balance_display',
                    'total_charges_display', 'is_reconciled', 'reconciled_by']
    list_filter = ['is_reconciled', 'year', 'account']
    search_fields = ['account__name', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'opening_balance_display', 'closing_balance_display',
                      'total_charges_display', 'total_refunds_display', 'total_fees_display', 'total_payouts_display']

    fieldsets = (
        ('Statement Period', {
            'fields': ('account', 'year', 'month')
        }),
        ('Balances', {
            'fields': ('opening_balance', 'opening_balance_display', 'closing_balance', 'closing_balance_display')
        }),
        ('Totals', {
            'fields': ('total_charges', 'total_charges_display', 'total_refunds', 'total_refunds_display',
                      'total_fees', 'total_fees_display', 'total_payouts', 'total_payouts_display')
        }),
        ('Reconciliation', {
            'fields': ('is_reconciled', 'reconciled_at', 'reconciled_by', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def period(self, obj):
        return f'{obj.year}-{obj.month:02d}'
    period.short_description = 'Period'

    def opening_balance_display(self, obj):
        return format_html('${:.2f}', obj.opening_balance_formatted)
    opening_balance_display.short_description = 'Opening Balance'

    def closing_balance_display(self, obj):
        return format_html('${:.2f}', obj.closing_balance_formatted)
    closing_balance_display.short_description = 'Closing Balance'

    def total_charges_display(self, obj):
        return format_html('<span style="color: green;">${:.2f}</span>', obj.total_charges_formatted)
    total_charges_display.short_description = 'Total Charges'

    def total_refunds_display(self, obj):
        return format_html('<span style="color: red;">${:.2f}</span>', obj.total_refunds_formatted)
    total_refunds_display.short_description = 'Total Refunds'

    def total_fees_display(self, obj):
        return format_html('<span style="color: orange;">${:.2f}</span>', obj.total_fees_formatted)
    total_fees_display.short_description = 'Total Fees'

    def total_payouts_display(self, obj):
        return format_html('<span style="color: blue;">${:.2f}</span>', obj.total_payouts_formatted)
    total_payouts_display.short_description = 'Total Payouts'
