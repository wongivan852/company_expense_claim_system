#!/usr/bin/env python

"""
Initialize basic data for CG Global Entertainment Expense System
"""

import os
import django
import sys

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_system.settings')
django.setup()

from claims.models import Company, ExpenseCategory, Currency, ExchangeRate
from accounts.models import User
from django.contrib.auth.models import Group, Permission
from decimal import Decimal
from django.utils import timezone

def create_companies():
    """Create the 4 main business entities."""
    companies = [
        {
            'name': 'CG Global Entertainment Ltd.',
            'name_chinese': '展盛環球娛樂有限公司',
            'name_simplified': '展盛环球娱乐有限公司',
            'code': 'CGEL',
            'company_type': 'entertainment',
            'address': 'Suite 1601, 16/F, Tower B, Hunghom Commercial Centre, 37-39 Ma Tau Wai Road, Hunghom, Kowloon, Hong Kong',
            'address_chinese': '香港九龍紅磡馬頭圍道37-39號紅磡商業中心B座16樓1601室',
            'registration_number': 'BR123456789',
            'is_active': True,
        },
        {
            'name': 'Key Intelligence Limited',
            'name_chinese': '鑰智有限公司',
            'name_simplified': '钥智有限公司',
            'code': 'KIL',
            'company_type': 'technology',
            'address': 'Suite 1602, 16/F, Tower B, Hunghom Commercial Centre, 37-39 Ma Tau Wai Road, Hunghom, Kowloon, Hong Kong',
            'registration_number': 'BR987654321',
            'is_active': True,
        },
        {
            'name': 'IAICC Institute',
            'name_chinese': 'IAICC學院',
            'name_simplified': 'IAICC学院',
            'code': 'IAICC',
            'company_type': 'institute',
            'address': 'Education Center, Hong Kong',
            'is_active': True,
        },
        {
            'name': 'CG Holdings',
            'name_chinese': '展盛控股',
            'name_simplified': '展盛控股',
            'code': 'CGH',
            'company_type': 'holding',
            'address': 'Corporate Center, Hong Kong',
            'is_active': True,
        }
    ]
    
    for company_data in companies:
        company, created = Company.objects.get_or_create(
            code=company_data['code'],
            defaults=company_data
        )
        if created:
            print(f"Created company: {company.name}")
        else:
            print(f"Company already exists: {company.name}")

def create_currencies():
    """Create supported currencies."""
    currencies = [
        {'code': 'HKD', 'name': 'Hong Kong Dollar', 'symbol': 'HK$', 'is_base_currency': True, 'is_active': True},
        {'code': 'RMB', 'name': 'Chinese Yuan Renminbi', 'symbol': '¥', 'is_base_currency': False, 'is_active': True},
        {'code': 'USD', 'name': 'United States Dollar', 'symbol': '$', 'is_base_currency': False, 'is_active': True},
        {'code': 'TWD', 'name': 'Taiwan Dollar', 'symbol': 'NT$', 'is_base_currency': False, 'is_active': True},
    ]
    
    for currency_data in currencies:
        currency, created = Currency.objects.get_or_create(
            code=currency_data['code'],
            defaults=currency_data
        )
        if created:
            print(f"Created currency: {currency.name}")

def create_categories():
    """Create expense categories matching the PDF form."""
    categories = [
        {
            'code': 'keynote_speech',
            'name': 'Keynote Speech',
            'name_chinese': '主題演講',
            'name_simplified': '主题演讲',
            'description': 'Expenses related to keynote speaking engagements',
            'requires_receipt': True,
            'is_active': True
        },
        {
            'code': 'sponsor_guest',
            'name': 'Sponsor Guest',
            'name_chinese': '贊助嘉賓',
            'name_simplified': '赞助嘉宾',
            'description': 'Expenses for sponsor guests and related activities',
            'requires_receipt': True,
            'is_active': True
        },
        {
            'code': 'course_operations',
            'name': 'Course Operations',
            'name_chinese': '課程運營推廣',
            'name_simplified': '课程运营推广',
            'description': 'Course operations and promotion expenses',
            'requires_receipt': True,
            'is_active': True
        },
        {
            'code': 'exhibition_procurement',
            'name': 'Exhibition Procurement',
            'name_chinese': '展覽采購',
            'name_simplified': '展览采购',
            'description': 'Exhibition and procurement related expenses',
            'requires_receipt': True,
            'is_active': True
        },
        {
            'code': 'business_negotiation',
            'name': 'Business Negotiation',
            'name_chinese': '業務商談',
            'name_simplified': '业务商谈',
            'description': 'Business meetings and negotiation expenses',
            'requires_receipt': True,
            'is_active': True
        },
        {
            'code': 'transportation',
            'name': 'Transportation',
            'name_chinese': '交通',
            'name_simplified': '交通',
            'description': 'Travel and transportation expenses',
            'requires_receipt': False,
            'is_active': True
        },
        {
            'code': 'other_misc',
            'name': 'Other Miscellaneous',
            'name_chinese': '其他雜項',
            'name_simplified': '其他杂项',
            'description': 'Other miscellaneous business expenses',
            'requires_receipt': True,
            'is_active': True
        },
    ]
    
    for category_data in categories:
        category, created = ExpenseCategory.objects.get_or_create(
            code=category_data['code'],
            defaults=category_data
        )
        if created:
            print(f"Created category: {category.name}")

def create_exchange_rates():
    """Create initial exchange rates."""
    from datetime import datetime
    
    rates = [
        {'currency_code': 'RMB', 'rate_to_base': 1.14, 'source': 'xe.com'},
        {'currency_code': 'USD', 'rate_to_base': 0.13, 'source': 'xe.com'},
        {'currency_code': 'TWD', 'rate_to_base': 4.0, 'source': 'xe.com'},
    ]
    
    for rate_data in rates:
        currency_code = rate_data['currency_code']
        try:
            currency = Currency.objects.get(code=currency_code)
            exchange_rate, created = ExchangeRate.objects.get_or_create(
                currency=currency,
                effective_date=datetime.now(),
                defaults={
                    'rate_to_base': rate_data['rate_to_base'],
                    'source': rate_data['source']
                }
            )
            if created:
                print(f"Created exchange rate: {currency_code} = {rate_data['rate_to_base']} HKD")
        except Currency.DoesNotExist:
            print(f"Currency {currency_code} not found, skipping exchange rate creation")

def create_groups_and_permissions():
    """Create user groups and permissions."""
    # Create groups
    employee_group, _ = Group.objects.get_or_create(name='Employees')
    manager_group, _ = Group.objects.get_or_create(name='Managers')
    admin_group, _ = Group.objects.get_or_create(name='Administrators')
    
    print("Created user groups")
    
    # Add permissions
    from django.contrib.contenttypes.models import ContentType
    from claims.models import ExpenseClaim
    
    # Get content type
    expense_claim_ct = ContentType.objects.get_for_model(ExpenseClaim)
    
    # Create custom permissions
    permissions_data = [
        ('can_view_all_claims', 'Can view all expense claims'),
        ('can_approve_claims', 'Can approve expense claims'),
        ('can_reject_claims', 'Can reject expense claims'),
        ('can_edit_all_claims', 'Can edit all expense claims'),
        ('can_delete_all_claims', 'Can delete all expense claims'),
    ]
    
    for codename, name in permissions_data:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=expense_claim_ct,
        )
        if created:
            print(f"Created permission: {name}")
    
    # Assign permissions to groups
    view_all_perm = Permission.objects.get(codename='can_view_all_claims')
    approve_perm = Permission.objects.get(codename='can_approve_claims')
    reject_perm = Permission.objects.get(codename='can_reject_claims')
    edit_all_perm = Permission.objects.get(codename='can_edit_all_claims')
    delete_all_perm = Permission.objects.get(codename='can_delete_all_claims')
    
    # Managers can view all, approve, and reject
    manager_group.permissions.add(view_all_perm, approve_perm, reject_perm)
    
    # Admins get all permissions
    admin_group.permissions.add(view_all_perm, approve_perm, reject_perm, edit_all_perm, delete_all_perm)
    
    print("Assigned permissions to groups")

def create_sample_users():
    """Create sample users."""
    users_data = [
        {
            'username': 'john.manager',
            'email': 'john.manager@cgel.com',
            'first_name': 'John',
            'last_name': 'Manager',
            'employee_id': 'CGEL001',
            'department': 'Finance',
            'position': 'Finance Manager',
            'role': 'manager',
            'location': 'hk',
            'is_staff': True,
            'groups': ['Managers'],
        },
        {
            'username': 'alice.employee',
            'email': 'alice.employee@cgel.com',
            'first_name': 'Alice',
            'last_name': 'Wong',
            'employee_id': 'CGEL002',
            'department': 'Marketing',
            'position': 'Marketing Specialist',
            'role': 'staff',
            'location': 'hk',
            'groups': ['Employees'],
        },
        {
            'username': 'bob.admin',
            'email': 'bob.admin@cgel.com',
            'first_name': 'Bob',
            'last_name': 'Chen',
            'employee_id': 'CGEL003',
            'department': 'IT',
            'position': 'IT Administrator',
            'role': 'admin',
            'location': 'hk',
            'is_staff': True,
            'is_superuser': True,
            'groups': ['Admins', 'Managers'],
        }
    ]
    
    for user_data in users_data:
        groups = user_data.pop('groups', [])
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )
        
        if created:
            user.set_password('password123')  # Set default password
            user.save()
            print(f"Created user: {user.username}")
            
            # Add to groups
            for group_name in groups:
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    print(f"Group {group_name} not found for user {user.username}")
            
            print(f"Created user: {user.username}")
        else:
            print(f"User already exists: {user.username}")

def main():
    """Main initialization function."""
    print("Initializing CG Global Entertainment Expense System...")
    
    try:
        create_companies()
        create_currencies()
        create_categories()
        create_exchange_rates()
        create_groups_and_permissions()
        create_sample_users()
        
        print("\n✅ Initialization completed successfully!")
        print("\nLogin credentials:")
        print("- Admin: admin / admin")
        print("- Manager: john.manager / password123")
        print("- Employee: alice.employee / password123")
        print("- Super Admin: bob.admin / password123")
        print("\nYou can now start the server with: python manage.py runserver")
    
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
