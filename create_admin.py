#!/usr/bin/env python
"""Script to create Django superuser for expense claim system."""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/wongivan/company_expense_claim_system')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_system.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@cgentertainment.com',
        password='admin123',  # Default password
        first_name='System',
        last_name='Administrator',
        employee_id='ADMIN001',
        department='IT',
        role='admin',
        location='hong_kong'
    )
    print("✅ Superuser created successfully!")
    print("Username: admin")
    print("Password: admin123")
    print("Email: admin@cgentertainment.com")
else:
    admin_user = User.objects.get(username='admin')
    print("✅ Admin user already exists!")
    print("Username: admin")
    print("Email:", admin_user.email)

print("\n🌐 Access admin at: http://localhost:8000/admin/")
