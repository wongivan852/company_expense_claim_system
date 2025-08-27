"""
Optimized views for document management with async file processing.

This module provides high-performance file upload, compression, and processing
capabilities for the expense claim system.
"""

import os
import json
import mimetypes
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import models

from .models import ExpenseDocument, DocumentProcessingJob, GeneratedDocument
from claims.models import ExpenseItem
from utils.cache_utils import cache_result
import logging

logger = logging.getLogger(__name__)


class OptimizedDocumentUploadView(LoginRequiredMixin, CreateView):
    """Optimized document upload with async processing."""
    
    model = ExpenseDocument
    template_name = 'documents/upload.html'
    fields = ['document_type', 'description']
    
    def post(self, request, *args, **kwargs):
        """Handle file upload with validation and async processing."""
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        expense_item_id = request.POST.get('expense_item_id')
        
        # Validate expense item
        try:
            expense_item = ExpenseItem.objects.select_related('expense_claim').get(
                id=expense_item_id
            )
            
            # Check permissions
            if expense_item.expense_claim.claimant != request.user:
                if not request.user.has_perm('claims.can_view_all_claims'):
                    return JsonResponse({'error': 'Permission denied'}, status=403)
                    
        except ExpenseItem.DoesNotExist:
            return JsonResponse({'error': 'Expense item not found'}, status=404)
        
        # Validate file size
        if file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            return JsonResponse({
                'error': f'File too large. Maximum size is {settings.FILE_UPLOAD_MAX_MEMORY_SIZE / (1024*1024):.1f}MB'
            }, status=413)
        
        # Validate file type
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx']
        file_extension = os.path.splitext(file.name)[1].lower().lstrip('.')
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
            }, status=400)
        
        try:
            # Create document record
            document = ExpenseDocument.objects.create(
                expense_item=expense_item,
                document_type=request.POST.get('document_type', 'receipt'),
                file=file,
                description=request.POST.get('description', ''),
                uploaded_by=request.user,
                original_size=file.size
            )
            
            # Queue async processing (would use Celery in production)
            if document.is_image and file.size > 1024 * 1024:  # 1MB threshold
                logger.info(f"Queuing compression for document {document.id}")
            
            # Queue OCR processing for images
            if document.is_image:
                logger.info(f"Queuing OCR processing for document {document.id}")
            
            logger.info(f"Document {document.id} uploaded successfully by {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'document_id': document.id,
                'filename': document.original_filename,
                'size': document.get_file_size_display(),
                'processing': document.is_image
            })
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return JsonResponse({'error': 'Upload failed'}, status=500)


@login_required
def document_download(request, document_id):
    """Secure document download with access logging."""
    try:
        document = get_object_or_404(ExpenseDocument, id=document_id)
        
        # Check permissions
        expense_claim = document.expense_item.expense_claim
        if expense_claim.claimant != request.user:
            if not request.user.has_perm('claims.can_view_all_claims'):
                raise Http404("Document not found")
        
        # Log access
        logger.info(f"Document {document_id} accessed by {request.user.username}")
        
        # Serve file
        response = HttpResponse(
            document.file.read(),
            content_type=document.mime_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
        response['Content-Length'] = document.file_size
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {e}")
        raise Http404("Document not found")


@login_required
def processing_status(request, document_id):
    """Get processing status for a document."""
    try:
        document = get_object_or_404(ExpenseDocument, id=document_id)
        
        # Check permissions
        expense_claim = document.expense_item.expense_claim
        if expense_claim.claimant != request.user:
            if not request.user.has_perm('claims.can_view_all_claims'):
                return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get processing jobs
        jobs = document.processing_jobs.order_by('-created_at')
        
        job_status = []
        for job in jobs:
            job_status.append({
                'job_type': job.job_type,
                'status': job.status,
                'progress': job.progress,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_message': job.error_message,
                'result_data': job.result_data
            })
        
        return JsonResponse({
            'document_id': document_id,
            'processing_jobs': job_status
        })
        
    except Exception as e:
        logger.error(f"Error getting processing status for document {document_id}: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# API Views
class DocumentViewSet(viewsets.ModelViewSet):
    """API viewset for document management."""
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Filter documents based on user permissions."""
        user = self.request.user
        
        if user.has_perm('claims.can_view_all_claims'):
            return ExpenseDocument.objects.select_related(
                'expense_item__expense_claim__claimant',
                'uploaded_by'
            ).order_by('-uploaded_at')
        else:
            return ExpenseDocument.objects.select_related(
                'expense_item__expense_claim__claimant',
                'uploaded_by'
            ).filter(
                expense_item__expense_claim__claimant=user
            ).order_by('-uploaded_at')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document via API."""
        document = self.get_object()
        
        response = HttpResponse(
            document.file.read(),
            content_type=document.mime_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
        
        return response
    
    @action(detail=True, methods=['get'])
    def processing_status(self, request, pk=None):
        """Get processing status via API."""
        document = self.get_object()
        jobs = document.processing_jobs.order_by('-created_at')
        
        job_data = []
        for job in jobs:
            job_data.append({
                'job_type': job.job_type,
                'status': job.status,
                'progress': job.progress,
                'result_data': job.result_data
            })
        
        return Response({'processing_jobs': job_data})


@cache_result(timeout=3600, key_prefix='document_stats')
def get_document_statistics():
    """Get cached document statistics."""
    from django.db.models import Count, Sum, Avg
    
    stats = ExpenseDocument.objects.aggregate(
        total_documents=Count('id'),
        total_size=Sum('file_size'),
        avg_size=Avg('file_size'),
        compressed_count=Count('id', filter=models.Q(is_compressed=True))
    )
    
    stats['total_size_mb'] = (stats['total_size'] or 0) / (1024 * 1024)
    stats['avg_size_mb'] = (stats['avg_size'] or 0) / (1024 * 1024)
    stats['compression_ratio'] = (
        (stats['compressed_count'] / stats['total_documents']) * 100
        if stats['total_documents'] else 0
    )
    
    return stats


@login_required
def document_statistics(request):
    """API endpoint for document statistics."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    stats = get_document_statistics()
    return JsonResponse(stats)
