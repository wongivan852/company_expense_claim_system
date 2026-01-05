"""
SSO Integration for Expense Claim System
Connects with the Integrated Business Platform authentication system
"""

import requests
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.sessions.models import Session
from django.utils import timezone

# Get the custom User model
User = get_user_model()

# SSO User mapping for cross-application compatibility
def map_sso_user_data(sso_user_data):
    """Map SSO user data to local user model fields."""
    return {
        'username': sso_user_data.get('email', ''),
        'email': sso_user_data.get('email', ''),
        'first_name': sso_user_data.get('first_name', ''),
        'last_name': sso_user_data.get('last_name', ''),
        'employee_id': sso_user_data.get('employee_id', ''),
        'department': sso_user_data.get('department', ''),
        'is_active': sso_user_data.get('is_active', True),
        'is_staff': sso_user_data.get('is_staff', False),
    }

logger = logging.getLogger(__name__)

# SSO Configuration
SSO_BASE_URL = getattr(settings, 'SSO_BASE_URL', 'http://localhost:8080')
SSO_SECRET_KEY = getattr(settings, 'SSO_SECRET_KEY', 'default-secret-key')
APP_NAME = 'expense_system'


class SSOAuthenticationBackend(BaseBackend):
    """
    Authentication backend that validates SSO tokens with the central platform
    """

    def authenticate(self, request, sso_token=None, **kwargs):
        if not sso_token:
            return None

        try:
            # Validate token with central platform
            response = requests.get(
                f"{SSO_BASE_URL}/auth/api/sso/validate/",
                params={'token': sso_token, 'app_name': APP_NAME},
                timeout=5
            )

            if response.status_code == 200:
                # Get user info from central platform
                user_response = requests.get(
                    f"{SSO_BASE_URL}/auth/api/sso/user-info/",
                    params={'token': sso_token},
                    timeout=5
                )

                if user_response.status_code == 200:
                    user_data = user_response.json()
                    return self._get_or_create_user(user_data, sso_token)

        except requests.RequestException as e:
            logger.error(f"SSO authentication failed: {e}")

        return None

    def _get_or_create_user(self, user_data, sso_token):
        """
        Get or create local user based on SSO data
        """
        try:
            email = user_data.get('email')
            employee_id = user_data.get('employee_id')

            if not email:
                return None

            # Try to find existing user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Try to find by username (email)
                try:
                    user = User.objects.get(username=email)
                except User.DoesNotExist:
                    # Create new user - use create instead of create_user for compatibility
                    mapped_data = map_sso_user_data(user_data)
                    mapped_data['username'] = email
                    user = User.objects.create(**mapped_data)
                    logger.info(f"Created new user from SSO: {email}")

            # Update user data
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.email = email
            user.save()

            # Store SSO token for session management
            user.sso_token = sso_token
            return user

        except Exception as e:
            logger.error(f"Error creating/updating user from SSO: {e}")
            return None


class SSOMiddleware:
    """
    Middleware to handle SSO authentication flow
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process SSO token if present
        sso_token = request.GET.get('sso_token')

        if sso_token and not request.user.is_authenticated:
            backend = SSOAuthenticationBackend()
            user = backend.authenticate(request, sso_token=sso_token)

            if user:
                # Log the user in
                login(request, user, backend='sso_integration.SSOAuthenticationBackend')

                # Explicitly save the session to ensure it persists
                request.session.save()
                logger.info(f"User {user.email} logged in via SSO, session saved")

                # Create session record in central platform
                self._create_central_session(request, sso_token)

                # Redirect to remove token from URL
                redirect_url = request.path
                if request.GET:
                    # Remove sso_token from query params
                    params = request.GET.copy()
                    if 'sso_token' in params:
                        del params['sso_token']
                    if params:
                        redirect_url += '?' + params.urlencode()

                return HttpResponseRedirect(redirect_url)

        response = self.get_response(request)
        return response

    def _create_central_session(self, request, sso_token):
        """
        Create session record in central platform
        """
        try:
            session_data = {
                'token': sso_token,
                'app_name': APP_NAME,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
            }

            requests.post(
                f"{SSO_BASE_URL}/auth/api/sso/create-session/",
                json=session_data,
                timeout=5
            )
        except requests.RequestException as e:
            logger.warning(f"Failed to create central session: {e}")

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def sso_logout(request):
    """
    Handle SSO logout - notify central platform
    """
    if request.user.is_authenticated and hasattr(request.user, 'sso_token'):
        try:
            requests.post(
                f"{SSO_BASE_URL}/auth/api/sso/logout/",
                json={'token': request.user.sso_token},
                timeout=5
            )
        except requests.RequestException as e:
            logger.warning(f"Failed to notify central platform of logout: {e}")


def get_sso_login_url(return_url=None):
    """
    Generate SSO login URL for redirecting to central platform
    """
    login_url = f"{SSO_BASE_URL}/auth/login/"
    if return_url:
        login_url += f"?next={return_url}"
    return login_url