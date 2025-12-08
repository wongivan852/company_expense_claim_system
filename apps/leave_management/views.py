"""
Leave Management Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from .models import LeaveType, LeaveBalance, LeaveApplication, SpecialLeaveBalance, SpecialWorkClaim, SpecialLeaveApplication
from datetime import datetime


class SimpleBalance:
    """Simple class to hold balance data"""
    def __init__(self, earned=0.0, used=0.0):
        self.earned = earned
        self.used = used
        self.balance = earned - used


@login_required
def leave_dashboard(request):
    """Leave management dashboard showing user's leave balances and recent applications"""

    # Get user's leave balances for current year
    current_year = datetime.now().year

    # Get all leave balances as a dictionary keyed by leave type name
    leave_balance_objs = LeaveBalance.objects.filter(
        user=request.user,
        year=current_year
    ).select_related('leave_type')

    leave_balances = {}
    annual_leave_details = None

    for balance in leave_balance_objs:
        leave_balances[balance.leave_type.name] = {
            'opening_balance': balance.opening_balance,
            'carried_forward': balance.carried_forward,
            'current_year_entitlement': balance.current_year_entitlement,
            'taken': balance.taken,
            'balance': balance.balance
        }

        # Set annual leave details
        if balance.leave_type.name == 'Annual Leave':
            annual_leave_details = {
                'carried_forward': balance.carried_forward,
                'current_year_entitlement': balance.current_year_entitlement,
                'taken_this_year': balance.taken,
                'current_balance': balance.balance
            }

    # Get special leave balance if exists
    try:
        special_leave_balance = SpecialLeaveBalance.objects.get(user=request.user, year=current_year)
    except SpecialLeaveBalance.DoesNotExist:
        special_leave_balance = SimpleBalance()

    # Get recent leave applications
    applications = LeaveApplication.objects.filter(
        user=request.user
    ).select_related('leave_type', 'approved_by').order_by('-created_at')[:10]

    # Calculate years of service
    years_of_service = (datetime.now().year - request.user.date_joined.year) if request.user.date_joined else 0

    # Get pending applications
    pending_applications = LeaveApplication.objects.filter(
        user=request.user,
        status='pending'
    ).count()

    # Total applications this year
    total_applications_this_year = LeaveApplication.objects.filter(
        user=request.user,
        created_at__year=current_year
    ).count()

    # For managers/admins - get pending special work claims and applications
    pending_special_claims = 0
    pending_special_applications = 0
    if request.user.role in ['manager', 'admin']:
        pending_special_claims = SpecialWorkClaim.objects.filter(status='pending').count()
        pending_special_applications = SpecialLeaveApplication.objects.filter(status='pending').count()

    stats = {
        'years_of_service': years_of_service,
        'total_applications_this_year': total_applications_this_year,
        'pending_applications': pending_applications,
        'pending_special_claims': pending_special_claims,
        'pending_special_applications': pending_special_applications,
        'total_pending_special': pending_special_claims + pending_special_applications,
    }

    context = {
        'employee': request.user,  # Template expects 'employee' variable
        'leave_balances': leave_balances,
        'annual_leave_details': annual_leave_details,
        'special_leave_balance': special_leave_balance,
        'applications': applications,
        'stats': stats,
        'current_year': current_year,
    }

    return render(request, 'leave/dashboard.html', context)


@login_required
def leave_apply(request):
    """Apply for leave"""
    from .forms import LeaveApplicationForm

    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()

            messages.success(request, 'Leave application submitted successfully!')
            return redirect('leave_management:apply_leave_confirm', application_id=application.id)
    else:
        form = LeaveApplicationForm(user=request.user)

    # Get user's leave balances for display
    current_year = datetime.now().year
    leave_balances = LeaveBalance.objects.filter(
        user=request.user,
        year=current_year
    ).select_related('leave_type')

    return render(request, 'leave/apply_leave.html', {
        'form': form,
        'employee': request.user,
        'is_revision': False,
        'leave_balances': leave_balances,
    })


@login_required
def my_leaves(request):
    """View all my leave applications with filtering and pagination"""
    from django.core.paginator import Paginator

    # Base queryset
    applications = LeaveApplication.objects.filter(
        user=request.user
    ).select_related('leave_type', 'approved_by').order_by('-created_at')

    # Get filter parameters
    status_filter = request.GET.get('status', '')
    leave_type_filter = request.GET.get('leave_type', '')

    # Apply filters
    if status_filter:
        applications = applications.filter(status=status_filter)

    if leave_type_filter:
        applications = applications.filter(leave_type__name=leave_type_filter)

    # Pagination
    paginator = Paginator(applications, 20)  # 20 applications per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get leave types for filter dropdown
    leave_types = LeaveType.objects.filter(is_active=True)

    # Status choices for filter
    status_choices = LeaveApplication.STATUS_CHOICES

    context = {
        'applications': page_obj.object_list,
        'page_obj': page_obj,
        'is_manager_view': False,
        'status_filter': status_filter,
        'leave_type_filter': leave_type_filter,
        'status_choices': status_choices,
        'leave_types': leave_types,
    }

    return render(request, 'leave/leave_applications.html', context)


@login_required
def leave_detail(request, application_id):
    """View leave application details"""
    application = get_object_or_404(LeaveApplication, pk=application_id, user=request.user)

    context = {
        'application': application,
        'is_manager_view': False,
    }

    return render(request, 'leave/leave_application_detail.html', context)


@login_required
def leave_cancel(request, application_id):
    """Withdraw a leave application"""
    application = get_object_or_404(LeaveApplication, pk=application_id, user=request.user)

    # Only allow withdrawal if status is pending
    if application.status != 'pending':
        messages.error(request, 'Only pending applications can be withdrawn.')
        return redirect('leave_management:leave_application_detail', application_id=application_id)

    if request.method == 'POST':
        # Update status to withdrawn
        application.status = 'withdrawn'
        application.save()

        messages.success(request, 'Leave application has been withdrawn successfully.')
        return redirect('leave_management:leave_applications')

    # Show confirmation page
    return render(request, 'leave/withdraw_confirmation.html', {
        'application': application
    })


@login_required
def leave_balance(request):
    """View leave balance details"""
    current_year = datetime.now().year
    balances = LeaveBalance.objects.filter(
        user=request.user,
        year=current_year
    ).select_related('leave_type')

    balance_html = '<ul>'
    for balance in balances:
        balance_html += f"""
            <li>
                <strong>{balance.leave_type.name}</strong><br>
                Opening: {balance.opening_balance} days<br>
                Entitlement: {balance.current_year_entitlement} days<br>
                Taken: {balance.taken} days<br>
                <strong>Balance: {balance.balance} days</strong>
            </li>
        """
    balance_html += '</ul>'

    return HttpResponse(f"""
        <h1>Leave Balance ({current_year})</h1>
        {balance_html}
        <p><a href="/leave/dashboard/">Back to Dashboard</a></p>
    """)


@login_required
def leave_approval_list(request):
    """Manager view for approving leave"""
    if request.user.role not in ['manager', 'admin']:
        return HttpResponse("<h1>Access Denied</h1><p>You need manager or admin role to access this page.</p>")

    # Get pending applications from team members
    pending = LeaveApplication.objects.filter(
        status='pending'
    ).select_related('user', 'leave_type').order_by('-created_at')

    return HttpResponse(f"""
        <h1>Leave Approvals</h1>
        <p>Pending approvals: {pending.count()}</p>
        <ul>
        {''.join([f'<li>{app.user.get_full_name()} - {app.leave_type.name} - {app.date_from.date()} to {app.date_to.date()}</li>' for app in pending[:10]])}
        </ul>
        <p><a href="/leave/dashboard/">Back to Dashboard</a></p>
    """)


@login_required
def leave_approve(request, application_id):
    return redirect('leave_management:dashboard')


@login_required
def leave_reject(request, application_id):
    return redirect('leave_management:dashboard')


@login_required
def leave_calendar(request):
    return HttpResponse("""
        <h1>Leave Calendar</h1>
        <p>Calendar view coming soon!</p>
        <p><a href="/leave/dashboard/">Back to Dashboard</a></p>
    """)


@login_required
def special_work_list(request):
    return HttpResponse("""
        <h1>Special Work Claims</h1>
        <p>View and manage special work claims here.</p>
        <p><a href="/leave/dashboard/">Back to Dashboard</a></p>
    """)


@login_required
def special_work_claim(request):
    return HttpResponse("""
        <h1>Submit Special Work Claim</h1>
        <p>Special work claim form coming soon!</p>
        <p><a href="/leave/dashboard/">Back to Dashboard</a></p>
    """)


@login_required
def special_work_detail(request, pk):
    return redirect('leave_management:dashboard')


@login_required
def special_leave_list(request):
    return HttpResponse("""
        <h1>Special Leave Applications</h1>
        <p>View special leave applications here.</p>
        <p><a href="/leave/dashboard/">Back to Dashboard</a></p>
    """)


@login_required
def special_leave_apply(request):
    return HttpResponse("""
        <h1>Apply for Special Leave</h1>
        <p>Special leave application form coming soon!</p>
        <p><a href="/leave/dashboard/">Back to Dashboard</a></p>
    """)


@login_required
def leave_form_print_view(request, application_id):
    """Print single leave application form"""
    from django.utils import timezone as tz
    from datetime import timedelta

    application = get_object_or_404(LeaveApplication, pk=application_id, user=request.user)

    # Convert to local time
    date_from_local = tz.localtime(application.date_from)
    date_to_local = tz.localtime(application.date_to)

    # Calculate return to work date
    date_back = date_to_local.date()
    if date_to_local.time().hour >= 14:  # PM end
        date_back = date_back + timedelta(days=1)
        # Skip weekends
        while date_back.weekday() >= 5:
            date_back = date_back + timedelta(days=1)

    context = {
        'application': application,
        'date_from_local': date_from_local,
        'date_to_local': date_to_local,
        'date_back_to_work': date_back,
        'is_pdf': False
    }

    return render(request, 'leave/leave_form_print.html', context)


@login_required
def leave_form_pdf_view(request, application_id):
    """Generate PDF for leave application"""
    from django.utils import timezone as tz
    from datetime import timedelta

    application = get_object_or_404(LeaveApplication, pk=application_id, user=request.user)

    # Convert to local time
    date_from_local = tz.localtime(application.date_from)
    date_to_local = tz.localtime(application.date_to)

    # Calculate return to work date
    date_back = date_to_local.date()
    if date_to_local.time().hour >= 14:  # PM end
        date_back = date_back + timedelta(days=1)
        # Skip weekends
        while date_back.weekday() >= 5:
            date_back = date_back + timedelta(days=1)

    from django.template.loader import get_template
    template = get_template('leave/leave_form_print.html')
    context = {
        'application': application,
        'date_from_local': date_from_local,
        'date_to_local': date_to_local,
        'date_back_to_work': date_back,
        'is_pdf': True
    }
    html = template.render(context)

    try:
        # Try to generate PDF using weasyprint if available
        import weasyprint
        pdf_file = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        filename = f'leave_application_{application.user.get_full_name().replace(" ", "_")}_{application_id}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
    except ImportError:
        # If weasyprint is not available, redirect to print view
        messages.warning(request, 'PDF generation is not available. Please use the print function instead.')
        return redirect('leave_management:leave_form_print', application_id=application_id)


@login_required
def combined_print_view(request):
    """Print multiple leave applications on one page (A5 format, 2 per A4 page)"""
    from django.utils import timezone as tz
    from datetime import timedelta

    # Get the IDs from query parameter
    ids = request.GET.get('ids', '')
    if not ids:
        messages.error(request, 'No applications selected for printing.')
        return redirect('leave_management:leave_applications')

    # Parse IDs
    application_ids = [int(id.strip()) for id in ids.split(',') if id.strip().isdigit()]

    # Get applications (limit to 2 for combined printing)
    applications = LeaveApplication.objects.filter(
        id__in=application_ids[:2],
        user=request.user
    ).select_related('leave_type', 'user')

    # Calculate return dates for each
    apps_with_dates = []
    for app in applications:
        # Convert to local time
        date_from_local = tz.localtime(app.date_from)
        date_to_local = tz.localtime(app.date_to)

        date_back = date_to_local.date()
        if date_to_local.time().hour >= 14:  # PM end
            date_back = date_back + timedelta(days=1)
            # Skip weekends
            while date_back.weekday() >= 5:
                date_back = date_back + timedelta(days=1)
        apps_with_dates.append({
            'application': app,
            'date_from_local': date_from_local,
            'date_to_local': date_to_local,
            'date_back_to_work': date_back
        })

    # Extract just the applications and dates for template
    applications = [item['application'] for item in apps_with_dates]
    dates_back_to_work = [item['date_back_to_work'] for item in apps_with_dates]
    dates_from_local = [item['date_from_local'] for item in apps_with_dates]
    dates_to_local = [item['date_to_local'] for item in apps_with_dates]

    context = {
        'applications': applications,
        'dates_back_to_work': dates_back_to_work,
        'dates_from_local': dates_from_local,
        'dates_to_local': dates_to_local,
        'apps_with_dates': apps_with_dates,  # Full data
        'is_pdf': False
    }

    return render(request, 'leave/combined_print.html', context)


@login_required
def combined_print_pdf_view(request):
    """Generate combined PDF"""
    from django.utils import timezone as tz
    from datetime import timedelta

    # Similar to combined_print_view but generates PDF
    ids = request.GET.get('ids', '')
    if not ids:
        messages.error(request, 'No applications selected for PDF generation.')
        return redirect('leave_management:leave_applications')

    application_ids = [int(id.strip()) for id in ids.split(',') if id.strip().isdigit()]
    applications = LeaveApplication.objects.filter(
        id__in=application_ids[:2],
        user=request.user
    ).select_related('leave_type', 'user')

    apps_with_dates = []
    for app in applications:
        # Convert to local time
        date_from_local = tz.localtime(app.date_from)
        date_to_local = tz.localtime(app.date_to)

        date_back = date_to_local.date()
        if date_to_local.time().hour >= 14:
            date_back = date_back + timedelta(days=1)
            while date_back.weekday() >= 5:
                date_back = date_back + timedelta(days=1)
        apps_with_dates.append({
            'application': app,
            'date_from_local': date_from_local,
            'date_to_local': date_to_local,
            'date_back_to_work': date_back
        })

    # Extract just the applications and dates for template
    applications = [item['application'] for item in apps_with_dates]
    dates_back_to_work = [item['date_back_to_work'] for item in apps_with_dates]
    dates_from_local = [item['date_from_local'] for item in apps_with_dates]
    dates_to_local = [item['date_to_local'] for item in apps_with_dates]

    from django.template.loader import get_template
    template = get_template('leave/combined_print.html')
    context = {
        'applications': applications,
        'dates_back_to_work': dates_back_to_work,
        'dates_from_local': dates_from_local,
        'dates_to_local': dates_to_local,
        'apps_with_dates': apps_with_dates,  # Full data
        'is_pdf': True
    }
    html = template.render(context)

    try:
        import weasyprint
        pdf_file = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="combined_leave_applications.pdf"'

        return response
    except ImportError:
        messages.warning(request, 'PDF generation is not available. Please use the print function instead.')
        return redirect('leave_management:combined_print') + f'?ids={ids}'


@login_required
def revise_leave_application_view(request, application_id):
    """Revise a pending leave application"""
    from .forms import LeaveApplicationForm

    application = get_object_or_404(LeaveApplication, pk=application_id, user=request.user)

    # Only allow revision if status is pending
    if application.status != 'pending':
        messages.error(request, 'Only pending applications can be revised.')
        return redirect('leave_management:leave_application_detail', application_id=application_id)

    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST, user=request.user, instance=application)
        if form.is_valid():
            revised_application = form.save(commit=False)
            revised_application.user = request.user
            revised_application.save()

            messages.success(request, 'Leave application has been revised successfully!')
            return redirect('leave_management:apply_leave_confirm', application_id=revised_application.id)
    else:
        form = LeaveApplicationForm(user=request.user, instance=application)

    # Get user's leave balances for display
    current_year = datetime.now().year
    leave_balances = LeaveBalance.objects.filter(
        user=request.user,
        year=current_year
    ).select_related('leave_type')

    return render(request, 'leave/apply_leave.html', {
        'form': form,
        'employee': request.user,
        'is_revision': True,
        'application': application,
        'leave_balances': leave_balances,
    })


@login_required
def apply_leave_confirm(request, application_id):
    """Confirm leave application"""
    application = get_object_or_404(LeaveApplication, pk=application_id, user=request.user)

    if request.method == 'POST':
        if 'confirm' in request.POST:
            messages.success(request, 'Leave application confirmed!')
            return redirect('leave_management:leave_applications')
        elif 'edit' in request.POST:
            return redirect('leave_management:apply_leave')

    # Prepare context data for template
    context = {
        'employee': request.user,
        'leave_type': application.leave_type,
        'application_data': {
            'days_applied': application.days_applied,
            'reason': application.reason,
        },
        'start_date_display': application.date_from.strftime('%A, %B %d, %Y'),
        'start_time_display': 'AM (9:00am - 1:00pm)' if application.date_from.hour == 9 else 'PM (2:00pm - 6:00pm)',
        'end_date_display': application.date_to.strftime('%A, %B %d, %Y'),
        'end_time_display': 'AM (9:00am - 1:00pm)' if application.date_to.hour == 13 else 'PM (2:00pm - 6:00pm)',
        'is_revision': False
    }

    return render(request, 'leave/apply_leave_confirm.html', context)


# Legacy view aliases for URL routing
apply_leave = leave_apply
leave_applications = my_leaves
leave_application_detail = leave_detail
revise_leave_application = revise_leave_application_view
withdraw_leave_application = leave_cancel
holiday_management = leave_calendar
holiday_import = leave_calendar
holiday_add = leave_calendar
employee_import = leave_dashboard
import_history = leave_dashboard
view_import_content = leave_dashboard
download_balances = leave_balance
special_leave_apply_confirm = special_leave_apply
special_leave_management = special_leave_list
holiday_edit = leave_calendar
holiday_delete = leave_calendar
leave_form_print = leave_form_print_view
leave_form_pdf = leave_form_pdf_view
combined_print = combined_print_view
combined_print_pdf = combined_print_pdf_view
manager_dashboard = leave_approval_list
approve_leave_application = leave_approve
approve_special_work_claim = leave_approve
approve_special_leave_application = leave_approve
