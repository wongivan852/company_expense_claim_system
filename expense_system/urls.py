"""
URL configuration for expense_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from django.utils import timezone
from utils.monitoring import health_check, performance_metrics, system_info

def home_view(request):
    """Enhanced home view with dashboard data."""
    context = {
        'current_year': 2025,
    }
    
    if request.user.is_authenticated:
        # Add user statistics if logged in
        try:
            from claims.models import ExpenseClaim
            user_claims = ExpenseClaim.objects.filter(employee=request.user)
            
            context.update({
                'user_stats': {
                    'total_claims': user_claims.count(),
                    'approved_claims': user_claims.filter(status='approved').count(),
                    'pending_claims': user_claims.filter(status='submitted').count(),
                    'total_amount': sum(float(claim.total_amount or 0) for claim in user_claims),
                },
                'recent_claims': user_claims.select_related('company').order_by('-created_at')[:5],
                'notifications': []  # Add notifications logic later
            })
        except Exception as e:
            # If there's an error with claims, just show basic context
            context.update({
                'user_stats': {
                    'total_claims': 0,
                    'approved_claims': 0,
                    'pending_claims': 0,
                    'total_amount': 0,
                },
                'recent_claims': [],
                'notifications': []
            })
    
    return render(request, 'home_simple.html', context)

def dashboard_view(request):
    """Dashboard view that displays the main dashboard."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    # Get user statistics and recent data
    try:
        from claims.models import ExpenseClaim
        
        user_claims = ExpenseClaim.objects.filter(claimant=request.user)
        recent_claims = user_claims.order_by('-created_at')[:5]
        
        user_stats = {
            'total_claims': user_claims.count(),
            'approved_claims': user_claims.filter(status='approved').count(),
            'pending_claims': user_claims.filter(status='pending').count(),
            'total_amount': 0  # Simplified for now
        }
        
        context = {
            'user_stats': user_stats,
            'recent_claims': recent_claims,
            'notifications': []  # Can add notification system later
        }
    except ImportError:
        # Fallback if models aren't available
        context = {
            'user_stats': {
                'total_claims': 0,
                'approved_claims': 0,
                'pending_claims': 0,
                'total_amount': 0
            },
            'recent_claims': [],
            'notifications': []
        }
    
    return render(request, 'dashboard.html', context)

def test_view(request):
    """Simple test view."""
    return render(request, 'test.html')

urlpatterns = [
    path("", home_view, name="home"),
    path("test/", test_view, name="test"),  # Test view
    path("dashboard/", dashboard_view, name="dashboard"),  # Dashboard redirect
    path("admin/", admin.site.urls),
    path("claims/", include("claims.urls")),
    path("documents/", include("documents.urls")),
    path("accounts/", include("accounts.urls")),
    path("reports/", include("reports.urls")),
    
    # Monitoring endpoints
    path("monitoring/health/", health_check, name="health_check"),
    path("monitoring/performance/", performance_metrics, name="performance_metrics"),  
    path("monitoring/system/", system_info, name="system_info"),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
