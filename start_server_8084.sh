#!/bin/bash

# Change to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

echo "🚀 Starting Django Expense Claim Management System..."
echo "�� Location: $(pwd)"
echo "🌐 URL: http://localhost:8084/"
echo "🔐 Admin: http://localhost:8084/admin/"
echo ""
echo "✅ Virtual environment activated"
echo "✅ Django project ready with all dependencies"
echo ""
echo "Starting server on port 8084..."
echo ""

# Start Django development server
python manage.py runserver 0.0.0.0:8084
