"""
Authentication views placeholder
"""
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

class CustomLogoutView(LogoutView):
    next_page = '/'

@login_required
def dashboard(request):
    return redirect('leave_management:dashboard')

def register(request):
    return redirect('accounts:login')
