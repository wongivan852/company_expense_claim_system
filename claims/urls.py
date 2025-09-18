"""
URL patterns for expense claims app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, simple_views, enhanced_views, print_views

# API router  
router = DefaultRouter()
# router.register(r'claims', views.ExpenseClaimViewSet, basename='expenseclaim')

app_name = 'claims'

urlpatterns = [
    # Main views (with auth)
    path('', views.OptimizedExpenseClaimListView.as_view(), name='claim_list'),
    path('create/', enhanced_views.enhanced_claim_create_view, name='claim_create'),
    path('<int:pk>/', views.OptimizedExpenseClaimDetailView.as_view(), name='claim_detail'),
    path('<int:pk>/edit/', views.claim_edit_view, name='claim_edit'),
    path('<int:pk>/delete/', views.claim_delete_view, name='claim_delete'),
    
    # Print functionality
    path('print/select/', print_views.select_claims_for_print_view, name='select_claims_print'),
    path('print/combined/', print_views.print_combined_claims_view, name='print_combined_claims'),
    path('<int:pk>/print/', print_views.print_claim_view, name='print_claim'),
    
    # Print with receipts functionality
    path('print/combined-receipts/', print_views.print_combined_claims_with_receipts_view, name='print_combined_claims_receipts'),
    path('<int:pk>/print-receipts/', print_views.print_claim_with_receipts_view, name='print_claim_receipts'),
    
    # Approval workflows
    path('pending/', views.pending_approvals_view, name='pending_approvals'),
    path('<int:pk>/approve/', views.approve_claim_view, name='approve_claim'),
    path('<int:pk>/reject/', views.reject_claim_view, name='reject_claim'),
    
    # Test views (no auth required) 
    path('test/', simple_views.test_dashboard, name='test_dashboard'),
    path('api-test/', simple_views.api_test, name='api_test'),
    path('health/', simple_views.health_simple, name='health_simple'),
    
    # API endpoints
    path('api/', include(router.urls)),
]