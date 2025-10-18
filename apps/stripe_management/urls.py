"""
Stripe Management URL Configuration
"""
from django.urls import path
from . import views

app_name = 'stripe_management'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/', views.account_list, name='account_list'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('statements/', views.statement_list, name='statement_list'),
    path('statements/generate/', views.generate_statement, name='statement_generate'),
]
