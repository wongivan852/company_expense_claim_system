"""
Print views for expense claims.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import ExpenseClaim, ExpenseItem
from decimal import Decimal


@login_required
def print_claim_view(request, pk):
    """Print a single expense claim."""
    claim = get_object_or_404(
        ExpenseClaim.objects.prefetch_related(
            'expense_items__category',
            'expense_items__currency',
            'expense_items__documents'
        ),
        pk=pk
    )
    
    # Check permissions
    if claim.claimant != request.user and not request.user.has_perm('claims.can_view_all_claims'):
        messages.error(request, 'You do not have permission to print this claim.')
        return redirect('claims:claim_detail', pk=pk)
    
    # Prepare data structure that matches template expectations
    expense_items = claim.expense_items.all().order_by('item_number')
    
    # Find unique categories used in this claim  
    used_categories = []
    for item in expense_items:
        if item.category:
            # Create category info dict with actual database data
            category_info = {
                'code': item.category.code,
                'zh_label': item.category.name,  # Use actual category name
                'en_label': item.category.name,  # Use actual category name for English too
            }
            # Add if not already present
            if not any(cat['code'] == category_info['code'] for cat in used_categories):
                used_categories.append(category_info)
    
    # Present categories are the ones actually used
    present_categories = used_categories
    
    # Calculate category totals for present categories only
    category_totals = {}
    for cat in present_categories:
        category_totals[cat['code']] = Decimal('0.00')
    
    for item in expense_items:
        if item.category and item.amount_hkd and item.category.code in category_totals:
            category_totals[item.category.code] += item.amount_hkd
    
    claim_data = {
        'claim': claim,
        'expense_items': expense_items,
        'category_totals': category_totals,
        'present_categories': present_categories,
        'total_hkd': claim.total_amount_hkd or Decimal('0.00'),
    }
    
    context = {
        'claims_data': [claim_data],  # Template expects a list
        'is_print': True,
    }
    return render(request, 'claims/print_claims.html', context)


@login_required  
def print_combined_claims_view(request):
    """Print multiple selected claims combined."""
    claim_ids = request.GET.getlist('claims')
    if not claim_ids:
        messages.error(request, 'No claims selected for printing.')
        return redirect('claims:claim_list')
    
    claims = ExpenseClaim.objects.filter(id__in=claim_ids).prefetch_related(
        'expense_items__category',
        'expense_items__currency', 
        'expense_items__documents'
    ).order_by('claim_number')
    
    # Check permissions for all claims
    allowed_claims = []
    for claim in claims:
        if claim.claimant == request.user or request.user.has_perm('claims.can_view_all_claims'):
            allowed_claims.append(claim)
    
    if not allowed_claims:
        messages.error(request, 'You do not have permission to print these claims.')
        return redirect('claims:claim_list')
    
    # Find unique categories used across all claims
    used_categories = []
    for claim in allowed_claims:
        for item in claim.expense_items.all():
            if item.category:
                # Create category info dict with actual database data
                category_info = {
                    'code': item.category.code,
                    'zh_label': item.category.name,  # Use actual category name
                    'en_label': item.category.name,  # Use actual category name for English too
                }
                # Add if not already present
                if not any(cat['code'] == category_info['code'] for cat in used_categories):
                    used_categories.append(category_info)
    
    # Present categories are the ones actually used
    present_categories = used_categories
    
    # Collect all expense items with proper numbering and claim references
    all_items = []
    item_counter = 1
    total_hkd = Decimal('0.00')
    
    # Category totals for present categories only
    category_totals = {}
    for cat in present_categories:
        category_totals[cat['code']] = Decimal('0.00')
    
    claim_numbers = []
    for claim in allowed_claims:
        if claim.total_amount_hkd:
            total_hkd += claim.total_amount_hkd
        claim_numbers.append(claim.claim_number)
        
        for item in claim.expense_items.all().order_by('item_number'):
            # Add claim context to item
            item.combined_item_number = item_counter
            item.claim_reference = claim.claim_number
            all_items.append(item)
            item_counter += 1
            
            # Update category totals for present categories only
            if item.category and item.amount_hkd and item.category.code in category_totals:
                category_totals[item.category.code] += item.amount_hkd
    
    combined_data = {
        'claims': allowed_claims,
        'expense_items': all_items,
        'total_hkd': total_hkd,
        'total_items': len(all_items),
        'claim_numbers': ', '.join(claim_numbers),
        'claims_count': len(allowed_claims),
        'category_totals': category_totals,
        'present_categories': present_categories,
        
        # Additional info for template
        'company_info': allowed_claims[0].company.name if allowed_claims else '',
        'event_name': f"Combined Expense Claims ({len(allowed_claims)} claims)",
        'claimant_name': allowed_claims[0].claimant.get_full_name() if allowed_claims else '',
        'period_from': min(claim.period_from for claim in allowed_claims) if allowed_claims else None,
        'period_to': max(claim.period_to for claim in allowed_claims) if allowed_claims else None,
    }
    
    context = {
        'combined_data': combined_data,
        'is_print': True,
    }
    return render(request, 'claims/print_combined_claims.html', context)


@login_required
def select_claims_for_print_view(request):
    """Show form to select claims for combined printing."""
    if request.method == 'POST':
        selected_claims = request.POST.getlist('selected_claims')
        if selected_claims:
            # Redirect to print combined view with selected claims
            claim_ids = '&'.join([f'claims={cid}' for cid in selected_claims])
            return redirect(f'/claims/print/combined/?{claim_ids}')
        else:
            messages.error(request, 'Please select at least one claim to print.')
    
    # Get user's claims
    if request.user.has_perm('claims.can_view_all_claims'):
        claims = ExpenseClaim.objects.all().order_by('-created_at')
    else:
        claims = ExpenseClaim.objects.filter(claimant=request.user).order_by('-created_at')
    
    context = {
        'claims': claims,
        'page_title': 'Select Claims for Printing',
    }
    return render(request, 'claims/select_claims_print.html', context)
