"""
URL patterns for documents app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API router
router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet, basename='document')

app_name = 'documents'

urlpatterns = [
    # Web views
    path('upload/', views.OptimizedDocumentUploadView.as_view(), name='upload'),
    path('download/<int:document_id>/', views.document_download, name='download'),
    path('status/<int:document_id>/', views.processing_status, name='processing_status'),
    path('stats/', views.document_statistics, name='statistics'),
    
    # API endpoints
    path('api/', include(router.urls)),
]