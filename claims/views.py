"""
Optimized views for expense claims management.

This module provides high-performance views with proper caching,
query optimization, and efficient data handling.
"""

import re
from decimal import Decimal, InvalidOperation as DecimalInvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.utils.decorators import method_decorator
from django.db.models import Prefetch, Count, Sum, Q
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ExpenseClaim, ExpenseItem, Company, ExpenseCategory, Currency, ClaimComment, ClaimStatusHistory
from documents.models import ExpenseDocument
try:
    from .forms import ExpenseClaimForm, ExpenseItemForm
except ImportError:
    # Handle missing forms gracefully
    ExpenseClaimForm = None
    ExpenseItemForm = None
from utils.cache_utils import ExpenseSystemCache, cache_result
import logging

logger = logging.getLogger(__name__)


class OptimizedExpenseClaimListView(LoginRequiredMixin, ListView):
    """Optimized list view for expense claims with caching and query optimization."""
    
    model = ExpenseClaim
    template_name = 'claims/claim_list.html'
    context_object_name = 'claims'
    paginate_by = 20
    
    def get_queryset(self):
        """Optimized queryset with select_related and prefetch_related."""
        queryset = ExpenseClaim.objects.select_related(
            'claimant',
            'company', 
            'approved_by'
        ).prefetch_related(
            Prefetch(
                'expense_items',
                queryset=ExpenseItem.objects.select_related('category', 'currency')
            )
        )
        
        # Filter based on user permissions
        user = self.request.user
        if not user.has_perm('claims.can_view_all_claims'):
            queryset = queryset.filter(claimant=user)
        
        # Apply filters
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        company_filter = self.request.GET.get('company')
        if company_filter:
            queryset = queryset.filter(company_id=company_filter)
        
        # Optimize ordering
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add optimized context data."""
        context = super().get_context_data(**kwargs)
        
        # Use cached data for dropdowns
        context['companies'] = ExpenseSystemCache.get_active_companies()
        context['status_choices'] = ExpenseClaim.STATUS_CHOICES
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'company': self.request.GET.get('company', ''),
        }
        
        # Add delete permissions for each claim
        if 'claims' in context:
            for claim in context['claims']:
                claim._can_delete_for_user = claim.can_delete(self.request.user)
        
        return context


class OptimizedExpenseClaimDetailView(LoginRequiredMixin, DetailView):
    """Optimized detail view for expense claims."""
    
    model = ExpenseClaim
    template_name = 'claims/claim_detail.html'
    context_object_name = 'claim'
    
    def get_queryset(self):
        """Optimized queryset for detail view."""
        return ExpenseClaim.objects.select_related(
            'claimant',
            'company',
            'checked_by',
            'approved_by'
        ).prefetch_related(
            Prefetch(
                'expense_items',
                queryset=ExpenseItem.objects.select_related(
                    'category', 'currency'
                ).prefetch_related('documents').order_by('item_number')
            ),
            Prefetch(
                'comments',
                queryset=ClaimComment.objects.select_related('author')
                .order_by('-created_at')
            ),
            Prefetch(
                'status_history',
                queryset=ClaimStatusHistory.objects.select_related('changed_by')
                .order_by('-created_at')
            )
        )
    
    def get_object(self, queryset=None):
        """Get object with permission check."""
        obj = super().get_object(queryset)
        
        # Check permissions
        user = self.request.user
        if not user.has_perm('claims.can_view_all_claims') and obj.claimant != user:
            raise PermissionDenied("You don't have permission to view this claim.")
        
        return obj
    
    def get_context_data(self, **kwargs):
        """Add delete permission to context."""
        context = super().get_context_data(**kwargs)
        context['can_delete_claim'] = self.object.can_delete(self.request.user)
        return context


class OptimizedExpenseClaimCreateView(LoginRequiredMixin, CreateView):
    """Optimized create view for expense claims."""
    
    model = ExpenseClaim
    form_class = ExpenseClaimForm
    template_name = 'claims/claim_form.html'
    
    def get_form_kwargs(self):
        """Pass user to form for optimization."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Set claimant and handle form submission."""
        form.instance.claimant = self.request.user
        
        # Clear relevant cache
        ExpenseSystemCache.invalidate_user_cache(self.request.user.id)
        
        messages.success(self.request, 'Expense claim created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add cached context data."""
        context = super().get_context_data(**kwargs)
        context['companies'] = ExpenseSystemCache.get_active_companies()
        context['categories'] = ExpenseSystemCache.get_active_categories()
        context['currencies'] = ExpenseSystemCache.get_active_currencies()
        return context


@method_decorator(cache_page(60 * 5), name='dispatch')  # 5-minute cache
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class DashboardView(LoginRequiredMixin, ListView):
    """Optimized dashboard view with caching."""
    
    template_name = 'claims/dashboard.html'
    context_object_name = 'recent_claims'
    paginate_by = 10
    
    def get_queryset(self):
        """Get recent claims for dashboard."""
        user = self.request.user
        
        queryset = ExpenseClaim.objects.select_related(
            'claimant', 'company'
        ).prefetch_related('expense_items')
        
        if not user.has_perm('claims.can_view_all_claims'):
            queryset = queryset.filter(claimant=user)
        
        return queryset.order_by('-created_at')[:10]
    
    def get_context_data(self, **kwargs):
        """Add optimized dashboard statistics."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get cached dashboard data
        role = 'admin' if user.is_staff else ('manager' if user.has_perm('claims.can_approve_claims') else 'employee')
        dashboard_data = ExpenseSystemCache.get_dashboard_data(user.id, role)
        
        context.update(dashboard_data)
        context['user_permissions'] = ExpenseSystemCache.get_user_permissions(user.id)
        
        return context


# API Views for AJAX and mobile app support

class ExpenseClaimViewSet(viewsets.ModelViewSet):
    """Optimized API viewset for expense claims."""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimized queryset with proper joins."""
        queryset = ExpenseClaim.objects.select_related(
            'claimant', 'company', 'approved_by'
        ).prefetch_related(
            'expense_items__category',
            'expense_items__currency'
        )
        
        # Filter based on permissions
        user = self.request.user
        if not user.has_perm('claims.can_view_all_claims'):
            queryset = queryset.filter(claimant=user)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics via API."""
        user = request.user
        role = 'admin' if user.is_staff else ('manager' if user.has_perm('claims.can_approve_claims') else 'employee')
        
        stats = ExpenseSystemCache.get_dashboard_data(user.id, role)
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def form_data(self, request):
        """Get form dropdown data via API."""
        return Response({
            'companies': ExpenseSystemCache.get_active_companies(),
            'categories': ExpenseSystemCache.get_active_categories(),
            'currencies': ExpenseSystemCache.get_active_currencies(),
            'exchange_rates': ExpenseSystemCache.get_exchange_rates(),
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a claim with optimized processing."""
        claim = self.get_object()
        
        if not claim.can_approve(request.user):
            return Response(
                {'error': 'You do not have permission to approve this claim.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        claim.status = 'approved'
        claim.approved_by = request.user
        claim.approved_at = timezone.now()
        claim.save(update_fields=['status', 'approved_by', 'approved_at'])
        
        # Clear relevant cache
        ExpenseSystemCache.invalidate_user_cache(claim.claimant.id)
        ExpenseSystemCache.invalidate_user_cache(request.user.id)
        
        logger.info(f"Claim {claim.claim_number} approved by {request.user.username}")
        
        return Response({'status': 'approved'})


@login_required
def ajax_exchange_rate(request):
    """AJAX endpoint for getting exchange rates."""
    currency_code = request.GET.get('currency')
    date_str = request.GET.get('date')
    
    if not currency_code:
        return JsonResponse({'error': 'Currency code required'}, status=400)
    
    try:
        if date_str:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        rates = ExpenseSystemCache.get_exchange_rates(date)
        
        if currency_code in rates:
            return JsonResponse({
                'rate': rates[currency_code]['rate'],
                'effective_date': rates[currency_code]['effective_date'],
                'source': rates[currency_code].get('source', '')
            })
        else:
            return JsonResponse({'error': 'Exchange rate not found'}, status=404)
    
    except Exception as e:
        logger.error(f"Error getting exchange rate: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@cache_result(timeout=300, key_prefix='user_claims_summary')
def get_user_claims_summary(user_id, period='month'):
    """Cached function for user claims summary."""
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    
    now = timezone.now()
    
    if period == 'month':
        start_date = now.replace(day=1)
    elif period == 'quarter':
        quarter_start = (now.month - 1) // 3 * 3 + 1
        start_date = now.replace(month=quarter_start, day=1)
    else:  # year
        start_date = now.replace(month=1, day=1)
    
    claims = ExpenseClaim.objects.filter(
        claimant_id=user_id,
        created_at__gte=start_date
    ).aggregate(
        total_amount=Sum('total_amount_hkd'),
        claim_count=Count('id'),
        approved_amount=Sum(
            'total_amount_hkd',
            filter=Q(status='approved')
        ),
        approved_count=Count('id', filter=Q(status='approved'))
    )
    
    return {
        'period': period,
        'total_amount': claims['total_amount'] or 0,
        'claim_count': claims['claim_count'] or 0,
        'approved_amount': claims['approved_amount'] or 0,
        'approved_count': claims['approved_count'] or 0,
        'start_date': start_date.isoformat(),
    }


@login_required
def user_claims_summary(request):
    """API endpoint for user claims summary."""
    period = request.GET.get('period', 'month')
    summary = get_user_claims_summary(request.user.id, period)
    return JsonResponse(summary)


# Performance monitoring view
@login_required
def performance_metrics(request):
    """View for monitoring application performance."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    from django.db import connection
    from django.core.cache import cache
    from django.conf import settings
    
    metrics = {
        'database_queries': len(connection.queries),
        'cache_status': 'enabled' if hasattr(settings, 'CACHES') else 'disabled',
        'active_sessions': 'N/A',  # Would need session store access
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(metrics)


# Additional view functions for URL routing

@login_required
def claim_create_view(request):
    """Function-based view for creating claims with expense items."""
    from .models import Company, ExpenseCategory, Currency
    from documents.models import ExpenseDocument
    from decimal import Decimal
    import re
    
    if request.method == 'POST':
        form = ExpenseClaimForm(request.POST, user=request.user)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.claimant = request.user
            claim.save()
            
            # Process expense items
            expense_items_created = 0
            for key in request.POST:
                # Look for expense_items[N][field] pattern
                match = re.match(r'expense_items\[(\d+)\]\[(\w+)\]', key)
                if match:
                    index, field = match.groups()
                    index = int(index)
                    
                    # Get all data for this item index
                    if field == 'category':  # Process each item only once
                        try:
                            category_id = request.POST.get(f'expense_items[{index}][category]')
                            currency_code = request.POST.get(f'expense_items[{index}][currency]')
                            exchange_rate = request.POST.get(f'expense_items[{index}][exchange_rate]')
                            amount_str = request.POST.get(f'expense_items[{index}][amount]', '').replace(',', '')
                            expense_date = request.POST.get(f'expense_items[{index}][expense_date]')
                            description = request.POST.get(f'expense_items[{index}][description]', '')
                            
                            if category_id and currency_code and amount_str and expense_date:
                                original_amount = Decimal(amount_str)
                                exchange_rate_val = Decimal(exchange_rate or '1.0')
                                
                                # Create expense item
                                expense_item = ExpenseItem.objects.create(
                                    expense_claim=claim,
                                    item_number=expense_items_created + 1,
                                    category_id=category_id,
                                    currency=Currency.objects.get(code=currency_code),
                                    exchange_rate=exchange_rate_val,
                                    original_amount=original_amount,
                                    amount_hkd=original_amount * exchange_rate_val,
                                    expense_date=expense_date,
                                    description=description
                                )
                                
                                # Handle receipt upload
                                receipt_file = request.FILES.get(f'expense_items[{index}][receipt]')
                                if receipt_file:
                                    ExpenseDocument.objects.create(
                                        expense_item=expense_item,
                                        document_type='receipt',
                                        file=receipt_file,
                                        uploaded_by=request.user
                                    )
                                
                                expense_items_created += 1
                                
                        except (ValueError, Currency.DoesNotExist, ExpenseCategory.DoesNotExist):
                            continue
            
            if expense_items_created > 0:
                messages.success(request, f'Expense claim created successfully with {expense_items_created} items.')
            else:
                messages.success(request, 'Expense claim created successfully.')
            return redirect('claims:claim_detail', pk=claim.pk)
    else:
        form = ExpenseClaimForm(user=request.user)
    
    context = {
        'form': form,
        'companies': Company.objects.filter(is_active=True),
        'expense_categories': ExpenseCategory.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
    }
    return render(request, 'claims/claim_form.html', context)


@login_required  
def claim_edit_view(request, pk):
    """Function-based view for editing claims."""
    claim = get_object_or_404(
        ExpenseClaim.objects.prefetch_related(
            'expense_items__category',
            'expense_items__currency',
            'expense_items__documents'
        ),
        pk=pk
    )
    
    # Check permissions
    if claim.claimant != request.user and not request.user.has_perm('claims.can_edit_all_claims'):
        messages.error(request, 'You do not have permission to edit this claim.')
        return redirect('claims:claim_detail', pk=pk)
    
    if request.method == 'POST':
        form = ExpenseClaimForm(request.POST, instance=claim, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                claim = form.save()
                
                # Track existing expense items to handle deletions
                existing_item_ids = set(claim.expense_items.values_list('id', flat=True))
                processed_item_ids = set()
                expense_items_processed = 0
                
                # Parse expense items from form data
                expense_item_pattern = re.compile(r'expense_items\[(\d+)\]\[([^]]+)\]')
                expense_items_data = {}
                
                for key, value in request.POST.items():
                    match = expense_item_pattern.match(key)
                    if match:
                        index, field = match.groups()
                        if index not in expense_items_data:
                            expense_items_data[index] = {}
                        expense_items_data[index][field] = value
                
                # Process each expense item
                for index, item_data in expense_items_data.items():
                    if not item_data.get('description') or not item_data.get('amount'):
                        continue
                        
                    try:
                        # Get or create expense item
                        expense_item_id = item_data.get('id')
                        if expense_item_id:
                            try:
                                expense_item = claim.expense_items.get(id=int(expense_item_id))
                                processed_item_ids.add(int(expense_item_id))
                            except (ValueError, ExpenseItem.DoesNotExist):
                                expense_item = ExpenseItem(expense_claim=claim)
                        else:
                            expense_item = ExpenseItem(expense_claim=claim)
                        
                        # Update expense item fields
                        expense_item.description = item_data.get('description', '')
                        
                        # Handle amount
                        amount_str = item_data.get('amount', '0').replace(',', '')
                        expense_item.original_amount = Decimal(amount_str) if amount_str else Decimal('0')
                        
                        # Handle expense date
                        expense_date_str = item_data.get('expense_date')
                        if expense_date_str:
                            from datetime import datetime
                            try:
                                expense_item.expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
                            except ValueError:
                                expense_item.expense_date = claim.period_from
                        else:
                            expense_item.expense_date = claim.period_from
                        
                        # Handle currency and exchange rate
                        currency_code = item_data.get('currency', 'HKD')
                        exchange_rate_str = item_data.get('exchange_rate', '1.0')
                        
                        try:
                            expense_item.currency = Currency.objects.get(code=currency_code)
                            expense_item.exchange_rate = Decimal(exchange_rate_str)
                            expense_item.amount_hkd = expense_item.original_amount * expense_item.exchange_rate
                        except (Currency.DoesNotExist, ValueError, DecimalInvalidOperation):
                            # Default to HKD
                            hkd_currency = Currency.objects.filter(code='HKD').first()
                            if hkd_currency:
                                expense_item.currency = hkd_currency
                                expense_item.exchange_rate = Decimal('1.0')
                                expense_item.amount_hkd = expense_item.original_amount
                        
                        # Set required fields for new items
                        if not expense_item.pk:
                            # For new items, find next available item number to avoid conflicts
                            existing_numbers = set(claim.expense_items.exclude(pk=expense_item.pk).values_list('item_number', flat=True))
                            # Also check numbers that might be assigned to items we're processing in this request
                            for processed_id in processed_item_ids:
                                try:
                                    existing_item = ExpenseItem.objects.get(pk=processed_id)
                                    existing_numbers.add(existing_item.item_number)
                                except ExpenseItem.DoesNotExist:
                                    pass
                            
                            next_number = 1
                            while next_number in existing_numbers:
                                next_number += 1
                            expense_item.item_number = next_number
                        
                        # Handle category
                        category_id = item_data.get('category')
                        if category_id:
                            try:
                                expense_item.category = ExpenseCategory.objects.get(id=int(category_id))
                            except (ValueError, ExpenseCategory.DoesNotExist):
                                # Set to first available category if none selected
                                first_category = ExpenseCategory.objects.filter(is_active=True).first()
                                if first_category:
                                    expense_item.category = first_category
                        else:
                            # Ensure we have a category (required field)
                            if not expense_item.category_id:
                                first_category = ExpenseCategory.objects.filter(is_active=True).first()
                                if first_category:
                                    expense_item.category = first_category
                        
                        expense_item.save()
                        expense_items_processed += 1
                        
                        # Handle receipt upload
                        receipt_file = request.FILES.get(f'expense_items[{index}][receipt]')
                        if receipt_file:
                            # Delete existing receipt for this item
                            expense_item.documents.filter(document_type='receipt').delete()
                            # Create new receipt document
                            ExpenseDocument.objects.create(
                                expense_item=expense_item,
                                document_type='receipt',
                                file=receipt_file,
                                uploaded_by=request.user
                            )
                        
                    except (ValueError, DecimalInvalidOperation) as e:
                        messages.warning(request, f'Error processing expense item {index}: {str(e)}')
                        continue
                
                # Delete removed expense items
                items_to_delete = existing_item_ids - processed_item_ids
                if items_to_delete:
                    deleted_count = claim.expense_items.filter(id__in=items_to_delete).count()
                    claim.expense_items.filter(id__in=items_to_delete).delete()
                    if deleted_count > 0:
                        messages.info(request, f'Removed {deleted_count} expense items.')
                
                if expense_items_processed > 0:
                    messages.success(request, f'Expense claim updated successfully with {expense_items_processed} items.')
                else:
                    messages.success(request, 'Expense claim updated successfully.')
                
                return redirect('claims:claim_detail', pk=pk)
    else:
        form = ExpenseClaimForm(instance=claim, user=request.user)
    
    context = {
        'form': form,
        'claim': claim,
        'companies': Company.objects.filter(is_active=True),
        'expense_categories': ExpenseCategory.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
    }
    return render(request, 'claims/claim_form.html', context)


@login_required
def claim_delete_view(request, pk):
    """Function-based view for deleting claims - only allows deletion of draft claims."""
    claim = get_object_or_404(ExpenseClaim, pk=pk)
    
    # Check if user can delete this claim (business rules)
    if not claim.can_delete(request.user):
        if claim.status != 'draft':
            messages.error(request, f'Cannot delete claim {claim.claim_number}. Only draft claims can be deleted.')
        else:
            messages.error(request, 'You do not have permission to delete this claim.')
        return redirect('claims:claim_detail', pk=pk)
    
    if request.method == 'POST':
        claim_number = claim.claim_number
        claim.delete()
        messages.success(request, f'Draft claim {claim_number} has been deleted successfully.')
        return redirect('claims:claim_list')
    
    # For GET request, show confirmation page
    context = {
        'claim': claim,
        'page_title': f'Delete Claim {claim.claim_number}',
    }
    return render(request, 'claims/claim_confirm_delete.html', context)


@login_required
def pending_approvals_view(request):
    """View for pending approvals."""
    if not request.user.has_perm('claims.can_approve_claims'):
        messages.error(request, 'You do not have permission to view pending approvals.')
        return redirect('claims:claim_list')
    
    claims = ExpenseClaim.objects.filter(
        status='pending'
    ).select_related(
        'claimant', 'company'
    ).prefetch_related(
        'expense_items'
    ).order_by('-created_at')
    
    context = {
        'claims': claims,
        'page_title': 'Pending Approvals',
    }
    return render(request, 'claims/pending_approvals.html', context)


@login_required
def approve_claim_view(request, pk):
    """Approve a claim."""
    claim = get_object_or_404(ExpenseClaim, pk=pk)
    
    if not request.user.has_perm('claims.can_approve_claims'):
        messages.error(request, 'You do not have permission to approve claims.')
        return redirect('claims:claim_detail', pk=pk)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        
        claim.status = 'approved'
        claim.approved_by = request.user
        claim.approved_at = timezone.now()
        claim.save()
        
        if comment:
            ClaimComment.objects.create(
                claim=claim,
                author=request.user,
                comment=comment,
                comment_type='approval'
            )
        
        messages.success(request, f'Claim {claim.claim_number} approved successfully.')
        return redirect('claims:claim_detail', pk=pk)
    
    return render(request, 'claims/approve_claim.html', {'claim': claim})


@login_required
def reject_claim_view(request, pk):
    """Reject a claim."""
    claim = get_object_or_404(ExpenseClaim, pk=pk)
    
    if not request.user.has_perm('claims.can_approve_claims'):
        messages.error(request, 'You do not have permission to reject claims.')
        return redirect('claims:claim_detail', pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, 'Rejection reason is required.')
            return render(request, 'claims/reject_claim.html', {'claim': claim})
        
        claim.status = 'rejected'
        claim.approved_by = request.user
        claim.approved_at = timezone.now()
        claim.save()
        
        ClaimComment.objects.create(
            claim=claim,
            author=request.user,
            comment=reason,
            comment_type='rejection'
        )
        
        messages.success(request, f'Claim {claim.claim_number} rejected.')
        return redirect('claims:claim_detail', pk=pk)
    
    return render(request, 'claims/reject_claim.html', {'claim': claim})