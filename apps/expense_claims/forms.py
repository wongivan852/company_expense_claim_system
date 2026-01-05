"""
Optimized forms for expense claims with performance enhancements.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ExpenseClaim, ExpenseItem, Company, ExpenseCategory, Currency
from apps.core.cache_utils import ExpenseSystemCache

User = get_user_model()


class ExpenseClaimForm(forms.ModelForm):
    """Optimized expense claim form with cached dropdowns."""

    class Meta:
        model = ExpenseClaim
        fields = ['company', 'event_name', 'period_from', 'period_to', 'claim_for']
        widgets = {
            'period_from': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'period_to': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'company': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'event_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'e.g., IAICC event'}
            ),
            'claim_for': forms.Select(
                attrs={'class': 'form-select'}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Make event_name required
        self.fields['event_name'].required = True

        # Use cached company data
        companies = ExpenseSystemCache.get_active_companies()
        self.fields['company'].choices = [('', '--- Select Company ---')] + [
            (company['id'], company['name']) for company in companies
        ]

        # Populate claim_for field with active users
        # The current user is the applicant/claimant; claim_for allows specifying
        # a different person for whom the claim is being submitted
        self.fields['claim_for'].required = False
        self.fields['claim_for'].label = 'Claim For (Optional)'
        self.fields['claim_for'].help_text = 'Select if submitting on behalf of another user'

        # Get active users for the claim_for dropdown
        active_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['claim_for'].choices = [('', '--- Same as Applicant ---')] + [
            (user.id, f"{user.get_full_name()} ({user.employee_id})") for user in active_users
        ]
    
    def clean_event_name(self):
        """Validate that event_name is not empty."""
        event_name = self.cleaned_data.get('event_name')
        if not event_name or not event_name.strip():
            raise ValidationError('Event/Purpose name is required. Please provide a description for your expense claim.')
        return event_name.strip()
    
    def clean_period_from(self):
        """Allow future dates for expense periods - no restrictions."""
        period_from = self.cleaned_data.get('period_from')
        return period_from
    
    def clean_period_to(self):
        """Allow future dates for expense periods - no restrictions."""
        period_to = self.cleaned_data.get('period_to')
        return period_to
    
    def clean(self):
        """Validate that period_to is not before period_from."""
        cleaned_data = super().clean()
        period_from = cleaned_data.get('period_from')
        period_to = cleaned_data.get('period_to')
        
        if period_from and period_to:
            if period_to < period_from:
                raise ValidationError({
                    'period_to': 'End date cannot be before start date.'
                })
        
        return cleaned_data


class ExpenseItemForm(forms.ModelForm):
    """Optimized expense item form."""
    
    class Meta:
        model = ExpenseItem
        fields = [
            'expense_date', 'description', 'description_chinese',
            'category', 'original_amount', 'currency', 'exchange_rate',
            'has_receipt', 'receipt_notes', 'location', 'participants', 'notes'
        ]
        widgets = {
            'expense_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'description_chinese': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'category': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'original_amount': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}
            ),
            'currency': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'exchange_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001', 'min': '0.0001'}
            ),
            'has_receipt': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'receipt_notes': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'location': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'participants': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Use cached data for dropdowns
        categories = ExpenseSystemCache.get_active_categories()
        currencies = ExpenseSystemCache.get_active_currencies()
        
        self.fields['category'].choices = [('', '--- Select Category ---')] + [
            (cat['id'], cat['name']) for cat in categories
        ]
        
        self.fields['currency'].choices = [('', '--- Select Currency ---')] + [
            (curr['id'], f"{curr['code']} - {curr['name']}") for curr in currencies
        ]
    
    def clean_expense_date(self):
        """Allow future dates for individual expense items."""
        expense_date = self.cleaned_data.get('expense_date')
        
        if expense_date:
            # Allow dates up to 1 year in the future for planning purposes
            max_future_date = timezone.now().date() + timedelta(days=365)
            
            if expense_date > max_future_date:
                raise ValidationError(
                    f"Expense date cannot be more than 1 year in the future. "
                    f"Maximum allowed date: {max_future_date.strftime('%Y-%m-%d')}"
                )
        
        return expense_date