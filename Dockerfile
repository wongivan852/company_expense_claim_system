# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=expense_system.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libmagic1 \
        tesseract-ocr \
        tesseract-ocr-eng \
        libgl1-mesa-dev \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        wget \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements_django.txt /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements_django.txt

# Create necessary directories
RUN mkdir -p /app/media /app/staticfiles /app/logs /app/uploads

# Copy project files
COPY . /app/

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Create SQLite database directory with proper permissions
RUN mkdir -p /app/data

# Expose port 8084
EXPOSE 8084

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8084/admin/login/ || exit 1

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8084"]
