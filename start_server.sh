#!/bin/bash

# Activate virtual environment (using venv which has Django and all dependencies)
source venv/bin/activate

echo "🚀 Starting Django Expense Claim Management System..."
echo "📍 Location: /Users/wongivan/company_apps/company_expense_claim_system"
echo "🌐 URL: http://localhost:8002/"
echo "🔐 Admin: http://localhost:8002/admin/"
echo ""
echo "✅ Virtual environment activated (venv with Python 3.8.12)"
echo "✅ Django project ready with all dependencies"
echo ""
echo "Starting server..."
echo ""

# Start Django development server
python manage.py runserver 0.0.0.0:8002
