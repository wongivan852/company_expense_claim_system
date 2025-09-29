"""URL patterns for accounts app."""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # SSO Authentication URLs
    path('login/', views.sso_login_view, name='login'),
    path('logout/', views.sso_logout_view, name='logout'),
    path('sso/login/', views.sso_login_view, name='sso_login'),
    path('sso/logout/', views.sso_logout_view, name='sso_logout'),

    # Profile management
    path('profile/', views.profile_view, name='profile'),
    path('', views.profile_view, name='index'),
]