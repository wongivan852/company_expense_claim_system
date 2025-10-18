"""
URL configuration for Integrated Business Platform.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from django.utils import timezone
from apps.core.monitoring import health_check, performance_metrics, system_info

def home_view(request):
    """Enhanced platform home view showing all available apps."""
    context = {
        'current_year': 2025,
    }

    if request.user.is_authenticated:
        # Platform apps configuration
        context['platform_apps'] = [
            {
                'name': 'Expense Claims',
                'description': 'Submit and manage expense claims with receipt uploads',
                'icon': 'fa-file-invoice-dollar',
                'url': 'expense_claims:claim_list',
                'color': 'primary',
                'available': True,
            },
            {
                'name': 'Documents',
                'description': 'Upload and manage business documents',
                'icon': 'fa-folder-open',
                'url': 'documents:upload',
                'color': 'info',
                'available': True,
            },
            # Leave Management moved to separate app (company-leave-system on port 8002)
            # {
            #     'name': 'Leave Management',
            #     'description': 'Apply for leave and manage your annual leave balance',
            #     'icon': 'fa-calendar-check',
            #     'url': 'http://localhost:8002',
            #     'color': 'success',
            #     'available': True,
            # },
            {
                'name': 'Reports',
                'description': 'View analytics and generate reports',
                'icon': 'fa-chart-line',
                'url': 'reports:index',
                'color': 'info',
                'available': True,
            },
            # Stripe Dashboard moved to separate app (stripe-dashboard on port 8081)
            # {
            #     'name': 'Stripe Management',
            #     'description': 'Manage Stripe accounts, transactions, and reconciliation',
            #     'icon': 'fa-stripe-s',
            #     'url': 'http://localhost:8081',
            #     'color': 'primary',
            #     'available': True,
            # },
            {
                'name': 'My Profile',
                'description': 'Manage your account settings and preferences',
                'icon': 'fa-user-cog',
                'url': 'accounts:profile',
                'color': 'warning',
                'available': True,
            },
        ]

        # Add user statistics if logged in
        try:
            from apps.expense_claims.models import ExpenseClaim
            user_claims = ExpenseClaim.objects.filter(claimant=request.user)

            context.update({
                'user_stats': {
                    'total_claims': user_claims.count(),
                    'approved_claims': user_claims.filter(status='approved').count(),
                    'pending_claims': user_claims.filter(status='pending').count(),
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

    return render(request, 'platform_home.html', context)

def dashboard_view(request):
    """Enhanced dashboard view with all platform statistics."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    from datetime import datetime
    from django.db.models import Sum, Q, Count

    context = {}
    current_year = datetime.now().year

    # Get expense claims statistics
    try:
        from apps.expense_claims.models import ExpenseClaim
        user_claims = ExpenseClaim.objects.filter(claimant=request.user)

        context['expense_stats'] = {
            'total_claims': user_claims.count(),
            'approved_claims': user_claims.filter(status='approved').count(),
            'pending_claims': user_claims.filter(status='pending').count(),
            'rejected_claims': user_claims.filter(status='rejected').count(),
            'total_amount': sum(float(claim.total_amount or 0) for claim in user_claims),
            'this_month_amount': sum(float(claim.total_amount or 0) for claim in user_claims.filter(
                created_at__year=datetime.now().year,
                created_at__month=datetime.now().month
            )),
        }
        context['recent_claims'] = user_claims.select_related('company').order_by('-created_at')[:5]
    except Exception as e:
        context['expense_stats'] = {
            'total_claims': 0, 'approved_claims': 0, 'pending_claims': 0,
            'rejected_claims': 0, 'total_amount': 0, 'this_month_amount': 0
        }
        context['recent_claims'] = []

    # Get leave management statistics
    try:
        from apps.leave_management.models import LeaveApplication, LeaveBalance
        user_leave_apps = LeaveApplication.objects.filter(user=request.user)

        context['leave_stats'] = {
            'total_applications': user_leave_apps.count(),
            'pending_applications': user_leave_apps.filter(status='pending').count(),
            'approved_applications': user_leave_apps.filter(status='approved').count(),
            'rejected_applications': user_leave_apps.filter(status='rejected').count(),
        }

        # Get leave balance
        try:
            annual_leave_balance = LeaveBalance.objects.filter(
                user=request.user,
                year=current_year,
                leave_type__name='Annual Leave'
            ).first()

            if annual_leave_balance:
                context['leave_stats']['annual_balance'] = annual_leave_balance.balance
                context['leave_stats']['annual_taken'] = annual_leave_balance.taken
                context['leave_stats']['annual_entitlement'] = annual_leave_balance.current_year_entitlement
            else:
                context['leave_stats']['annual_balance'] = 0
                context['leave_stats']['annual_taken'] = 0
                context['leave_stats']['annual_entitlement'] = 0
        except:
            context['leave_stats']['annual_balance'] = 0
            context['leave_stats']['annual_taken'] = 0
            context['leave_stats']['annual_entitlement'] = 0

        context['recent_leave_apps'] = user_leave_apps.select_related('leave_type').order_by('-created_at')[:5]
    except Exception as e:
        context['leave_stats'] = {
            'total_applications': 0, 'pending_applications': 0,
            'approved_applications': 0, 'rejected_applications': 0,
            'annual_balance': 0, 'annual_taken': 0, 'annual_entitlement': 0
        }
        context['recent_leave_apps'] = []

    # Check if this is first login (user has no activity)
    context['is_first_login'] = (
        context['expense_stats']['total_claims'] == 0 and
        context['leave_stats']['total_applications'] == 0
    )

    # Platform quick actions
    context['quick_actions'] = [
        {
            'title': 'New Expense Claim',
            'description': 'Submit a new expense claim with receipts',
            'icon': 'fa-receipt',
            'url': 'expense_claims:claim_create',
            'color': 'primary',
            'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        },
        {
            'title': 'Apply for Leave',
            'description': 'Submit a leave application',
            'icon': 'fa-calendar-plus',
            'url': 'leave_management:apply_leave',
            'color': 'success',
            'gradient': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
        },
        {
            'title': 'Upload Documents',
            'description': 'Upload and manage documents',
            'icon': 'fa-cloud-upload-alt',
            'url': 'documents:upload',
            'color': 'info',
            'gradient': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        },
        {
            'title': 'View Reports',
            'description': 'Access analytics and reports',
            'icon': 'fa-chart-pie',
            'url': 'reports:index',
            'color': 'warning',
            'gradient': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        },
    ]

    context['notifications'] = []

    return render(request, 'dashboard.html', context)

def test_view(request):
    """Simple test view."""
    return render(request, 'test.html')

urlpatterns = [
    path("", home_view, name="home"),
    path("test/", test_view, name="test"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("admin/", admin.site.urls),

    # Business Apps
    path("expense-claims/", include("apps.expense_claims.urls")),
    path("documents/", include("apps.documents.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("reports/", include("apps.reports.urls")),
    # NOTE: Leave and Stripe are now separate apps accessed via main platform
    # path("leave/", include("apps.leave_management.urls")),  # Removed - use company-leave-system
    # path("stripe/", include("apps.stripe_management.urls")),  # Removed - use stripe-dashboard

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
