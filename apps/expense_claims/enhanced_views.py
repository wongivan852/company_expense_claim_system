"""
Enhanced claim creation view that properly handles expense items with exchange rates.
"""
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from .models import ExpenseClaim, ExpenseItem, Company, ExpenseCategory, Currency
from apps.documents.models import ExpenseDocument
from .forms import ExpenseClaimForm
import logging

logger = logging.getLogger(__name__)


@login_required
def enhanced_claim_create_view(request):
    """Enhanced claim creation with proper expense item handling."""
    
    if request.method == 'POST':
        return _handle_claim_creation(request)
    else:
        return _show_claim_form(request)


def _show_claim_form(request):
    """Show the claim creation form."""
    form = ExpenseClaimForm(user=request.user)
    
    context = {
        'form': form,
        'companies': Company.objects.filter(is_active=True),
        'expense_categories': ExpenseCategory.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
    }
    return render(request, 'claims/claim_form.html', context)


def _handle_claim_creation(request):
    """Handle the POST request for claim creation."""
    
    try:
        with transaction.atomic():
            # Create the main claim
            claim = _create_main_claim(request)
            
            # Process expense items
            expense_items = _process_expense_items(request, claim)
            
            if not expense_items:
                messages.error(request, 'At least one expense item is required.')
                return _show_claim_form(request)
            
            # Update claim totals
            _update_claim_totals(claim)
            
            logger.info(f"Created claim {claim.claim_number} with {len(expense_items)} items")
            messages.success(request, f'Expense claim {claim.claim_number} created successfully with {len(expense_items)} items.')
            
            return redirect('expense_claims:claim_detail', pk=claim.pk)
            
    except Exception as e:
        logger.error(f"Error creating claim: {str(e)}")
        messages.error(request, f'Error creating claim: {str(e)}')
        return _show_claim_form(request)


def _create_main_claim(request):
    """Create the main expense claim."""

    # Handle monthly period calculation
    period_from = request.POST.get('period_from')
    period_to = request.POST.get('period_to')

    if period_from and not period_to:
        # Calculate full month period
        from datetime import datetime, timedelta
        import calendar

        start_date = datetime.strptime(period_from, '%Y-%m-%d').date()
        # Set to first day of month
        first_day = start_date.replace(day=1)
        # Calculate last day of month
        last_day = start_date.replace(day=calendar.monthrange(start_date.year, start_date.month)[1])

        # Create a mutable POST data copy
        post_data = request.POST.copy()
        post_data['period_from'] = first_day.strftime('%Y-%m-%d')
        post_data['period_to'] = last_day.strftime('%Y-%m-%d')
        request.POST = post_data

    form = ExpenseClaimForm(request.POST, user=request.user)

    if form.is_valid():
        claim = form.save(commit=False)
        claim.claimant = request.user

        # Handle claim_for field - if not set, the claimant is the expense owner
        # claim_for is handled by the form if provided
        claim.save()
        return claim
    else:
        raise Exception(f"Invalid main claim form: {form.errors}")


def _process_expense_items(request, claim):
    """Process and create expense items."""

    expense_items = []
    item_counter = 0

    # Process expense items from form data
    while True:
        # Check if this item exists in form data
        category_key = f'expense_items[{item_counter}][category]'

        if category_key not in request.POST:
            break

        item_data = _extract_item_data(request, item_counter)

        if item_data['category'] and item_data['amount'] and item_data['expense_date']:
            expense_item = _create_expense_item(request, claim, item_data, item_counter)
            expense_items.append(expense_item)

        item_counter += 1

    return expense_items


def _extract_item_data(request, item_index):
    """Extract data for a single expense item."""
    
    return {
        'category': request.POST.get(f'expense_items[{item_index}][category]', '').strip(),
        'currency': request.POST.get(f'expense_items[{item_index}][currency]', '').strip(),
        'amount': request.POST.get(f'expense_items[{item_index}][amount]', '').strip(),
        'exchange_rate': request.POST.get(f'expense_items[{item_index}][exchange_rate]', '1.0000').strip(),
        'expense_date': request.POST.get(f'expense_items[{item_index}][expense_date]', '').strip(),
        'description': request.POST.get(f'expense_items[{item_index}][description]', '').strip(),
    }


def _create_expense_item(request, claim, item_data, item_index):
    """Create a single expense item with receipt upload handling."""

    try:
        category = ExpenseCategory.objects.get(id=int(item_data['category']))
        currency = Currency.objects.get(code=item_data['currency'])

        original_amount = Decimal(item_data['amount'])
        exchange_rate = Decimal(item_data['exchange_rate'])
        amount_hkd = original_amount * exchange_rate

        # Check if receipt file is uploaded
        receipt_file = request.FILES.get(f'expense_items[{item_index}][receipt]')
        has_receipt = receipt_file is not None

        expense_item = ExpenseItem.objects.create(
            expense_claim=claim,
            item_number=item_index + 1,
            expense_date=item_data['expense_date'],
            description=item_data['description'] or f"{category.name} expense",
            category=category,
            original_amount=original_amount,
            currency=currency,
            exchange_rate=exchange_rate,
            amount_hkd=amount_hkd,
            has_receipt=has_receipt,
        )

        # Handle receipt upload
        if receipt_file:
            ExpenseDocument.objects.create(
                expense_item=expense_item,
                document_type='receipt',
                file=receipt_file,
                uploaded_by=request.user
            )
            logger.info(f"Uploaded receipt for expense item {item_index + 1}")

        logger.info(f"Created expense item: {category.name} - {original_amount} {currency.code} = {amount_hkd} HKD")
        return expense_item

    except Exception as e:
        logger.error(f"Error creating expense item {item_index + 1}: {str(e)}")
        raise Exception(f"Error creating expense item {item_index + 1}: {str(e)}")


def _update_claim_totals(claim):
    """Update claim total amounts."""
    
    total_hkd = sum(item.amount_hkd for item in claim.expense_items.all())
    
    # If the claim model has total fields, update them
    if hasattr(claim, 'total_amount_hkd'):
        claim.total_amount_hkd = total_hkd
        claim.save(update_fields=['total_amount_hkd'])
