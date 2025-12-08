"""Models for document and file management."""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator, MaxValueValidator
import os
import uuid


def expense_document_path(instance, filename):
    """Generate upload path for expense documents."""
    # Create path like: documents/2024/08/claim_CGGE202408001/item_1/filename
    claim = instance.expense_item.expense_claim
    return f"documents/{claim.created_at.year}/{claim.created_at.month:02d}/{claim.claim_number}/item_{instance.expense_item.item_number}/{filename}"


class ExpenseDocument(models.Model):
    """Documents attached to expense items (receipts, invoices, etc.)."""
    
    # Document types
    TYPE_CHOICES = [
        ('receipt', _('Receipt')),
        ('invoice', _('Invoice')),
        ('proof', _('Proof of Payment')),
        ('other', _('Other')),
    ]
    
    expense_item = models.ForeignKey(
        'expense_claims.ExpenseItem',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_("Expense Item")
    )
    
    document_type = models.CharField(
        _("Document Type"),
        max_length=20,
        choices=TYPE_CHOICES,
        default='receipt'
    )
    
    file = models.FileField(
        _("File"),
        upload_to=expense_document_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx']
            )
        ],
        help_text=_("Supported formats: PDF, JPG, PNG, GIF, DOC, DOCX (Max 10MB)")
    )
    
    original_filename = models.CharField(
        _("Original Filename"),
        max_length=255,
        editable=False
    )
    
    file_size = models.PositiveIntegerField(
        _("File Size"),
        editable=False,
        help_text=_("File size in bytes")
    )
    
    mime_type = models.CharField(
        _("MIME Type"),
        max_length=100,
        blank=True,
        editable=False
    )
    
    description = models.CharField(
        _("Description"),
        max_length=200,
        blank=True,
        help_text=_("Brief description of the document")
    )
    
    # OCR extracted data (future enhancement)
    ocr_text = models.TextField(
        _("OCR Text"),
        blank=True,
        editable=False,
        help_text=_("Text extracted from image using OCR")
    )
    
    ocr_amount = models.DecimalField(
        _("OCR Amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text=_("Amount extracted from receipt using OCR")
    )
    
    ocr_date = models.DateField(
        _("OCR Date"),
        null=True,
        blank=True,
        editable=False,
        help_text=_("Date extracted from receipt using OCR")
    )
    
    # Upload metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Uploaded By")
    )
    
    uploaded_at = models.DateTimeField(
        _("Uploaded At"),
        auto_now_add=True
    )
    
    # Image compression metadata
    is_compressed = models.BooleanField(
        _("Is Compressed"),
        default=False,
        help_text=_("Whether the image has been compressed")
    )
    
    original_size = models.PositiveIntegerField(
        _("Original Size"),
        null=True,
        blank=True,
        help_text=_("Original file size before compression")
    )
    
    class Meta:
        verbose_name = _("Expense Document")
        verbose_name_plural = _("Expense Documents")
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.expense_item} - {self.get_document_type_display()}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
            
            # Detect MIME type
            import mimetypes
            self.mime_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete the file when the model is deleted
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
    
    @property
    def file_extension(self):
        """Get file extension."""
        return os.path.splitext(self.original_filename)[1].lower()
    
    @property
    def is_image(self):
        """Check if file is an image."""
        return self.file_extension in ['.jpg', '.jpeg', '.png', '.gif']
    
    @property
    def is_pdf(self):
        """Check if file is a PDF."""
        return self.file_extension == '.pdf'
    
    def get_file_size_display(self):
        """Get human-readable file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class DocumentTemplate(models.Model):
    """Templates for generating documents (reports, forms, etc.)."""
    
    TEMPLATE_TYPES = [
        ('claim_form', _('Expense Claim Form')),
        ('report', _('Expense Report')),
        ('summary', _('Summary Report')),
    ]
    
    name = models.CharField(
        _("Template Name"),
        max_length=100
    )
    
    template_type = models.CharField(
        _("Template Type"),
        max_length=20,
        choices=TEMPLATE_TYPES
    )
    
    file = models.FileField(
        _("Template File"),
        upload_to='templates/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['html', 'pdf', 'docx']
            )
        ]
    )
    
    description = models.TextField(
        _("Description"),
        blank=True
    )
    
    is_active = models.BooleanField(
        _("Active"),
        default=True
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Created By")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Document Template")
        verbose_name_plural = _("Document Templates")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class GeneratedDocument(models.Model):
    """Track generated documents (reports, exports, etc.)."""
    
    DOCUMENT_TYPES = [
        ('pdf_report', _('PDF Report')),
        ('excel_export', _('Excel Export')),
        ('csv_export', _('CSV Export')),
        ('claim_form', _('Claim Form')),
    ]
    
    document_type = models.CharField(
        _("Document Type"),
        max_length=20,
        choices=DOCUMENT_TYPES
    )
    
    title = models.CharField(
        _("Document Title"),
        max_length=200
    )
    
    file = models.FileField(
        _("Generated File"),
        upload_to='generated/%Y/%m/'
    )
    
    # Related objects (optional)
    expense_claim = models.ForeignKey(
        'expense_claims.ExpenseClaim',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='generated_documents',
        verbose_name=_("Related Claim")
    )
    
    # Generation parameters
    parameters = models.JSONField(
        _("Generation Parameters"),
        default=dict,
        blank=True,
        help_text=_("Parameters used to generate this document")
    )
    
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Generated By")
    )
    
    generated_at = models.DateTimeField(
        _("Generated At"),
        auto_now_add=True
    )
    
    # Access tracking
    download_count = models.PositiveIntegerField(
        _("Download Count"),
        default=0
    )
    
    last_accessed = models.DateTimeField(
        _("Last Accessed"),
        null=True,
        blank=True
    )
    
    # Auto-deletion
    expires_at = models.DateTimeField(
        _("Expires At"),
        null=True,
        blank=True,
        help_text=_("When this document will be automatically deleted")
    )
    
    class Meta:
        verbose_name = _("Generated Document")
        verbose_name_plural = _("Generated Documents")
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"
    
    def record_access(self):
        """Record that this document was accessed."""
        from django.utils import timezone
        self.download_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['download_count', 'last_accessed'])
    
    @property
    def is_expired(self):
        """Check if document has expired."""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at


class DocumentProcessingJob(models.Model):
    """Track document processing jobs (OCR, compression, etc.)."""
    
    JOB_TYPES = [
        ('ocr', _('OCR Processing')),
        ('compression', _('Image Compression')),
        ('thumbnail', _('Thumbnail Generation')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]
    
    document = models.ForeignKey(
        ExpenseDocument,
        on_delete=models.CASCADE,
        related_name='processing_jobs'
    )
    
    job_type = models.CharField(
        _("Job Type"),
        max_length=20,
        choices=JOB_TYPES
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    progress = models.PositiveIntegerField(
        _("Progress"),
        default=0,
        validators=[MaxValueValidator(100)],
        help_text=_("Progress percentage (0-100)")
    )
    
    result_data = models.JSONField(
        _("Result Data"),
        default=dict,
        blank=True,
        help_text=_("Results from processing job")
    )
    
    error_message = models.TextField(
        _("Error Message"),
        blank=True
    )
    
    started_at = models.DateTimeField(
        _("Started At"),
        null=True,
        blank=True
    )
    
    completed_at = models.DateTimeField(
        _("Completed At"),
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Document Processing Job")
        verbose_name_plural = _("Document Processing Jobs")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.document}"
