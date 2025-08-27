#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Add the project directory to the Python path
sys.path.insert(0, '/Users/wongivan/ai_tools/business_tools/company_expense_claim_system')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_system.settings')
django.setup()

from claims.models import Company, ExpenseCategory, Currency, ExchangeRate
from django.utils import timezone

print("🚀 Creating sample data for testing...")

# Create sample companies
companies_data = [
    {'name': 'CG Global Entertainment Ltd', 'code': 'CGGE', 'address': 'Hong Kong'},
    {'name': 'Kappa Investment Ltd', 'code': 'KI', 'address': 'Hong Kong'},
    {'name': 'Kappa Technology Ltd', 'code': 'KT', 'address': 'Hong Kong'},
]

for company_data in companies_data:
    company, created = Company.objects.get_or_create(
        code=company_data['code'],
        defaults=company_data
    )
    if created:
        print(f"✅ Created company: {company.name}")
    else:
        print(f"ℹ️  Company exists: {company.name}")

# Create sample expense categories
categories_data = [
    {'name': 'Transportation', 'name_chinese': '交通費', 'requires_receipt': True},
    {'name': 'Meals & Entertainment', 'name_chinese': '餐費及招待', 'requires_receipt': True},
    {'name': 'Accommodation', 'name_chinese': '住宿費', 'requires_receipt': True},
    {'name': 'Office Supplies', 'name_chinese': '辦公用品', 'requires_receipt': True},
    {'name': 'Communication', 'name_chinese': '通訊費', 'requires_receipt': True},
    {'name': 'Professional Services', 'name_chinese': '專業服務', 'requires_receipt': True},
    {'name': 'Training & Development', 'name_chinese': '培訓發展', 'requires_receipt': True},
    {'name': 'Miscellaneous', 'name_chinese': '雜項', 'requires_receipt': False},
]

for category_data in categories_data:
    category, created = ExpenseCategory.objects.get_or_create(
        name=category_data['name'],
        defaults=category_data
    )
    if created:
        print(f"✅ Created category: {category.name}")
    else:
        print(f"ℹ️  Category exists: {category.name}")

# Create sample currencies
currencies_data = [
    {'code': 'HKD', 'name': 'Hong Kong Dollar', 'symbol': '$', 'is_base_currency': True},
    {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
    {'code': 'RMB', 'name': 'Chinese Renminbi', 'symbol': '¥'},
    {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥'},
    {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
]

for currency_data in currencies_data:
    currency, created = Currency.objects.get_or_create(
        code=currency_data['code'],
        defaults=currency_data
    )
    if created:
        print(f"✅ Created currency: {currency.code} - {currency.name}")
    else:
        print(f"ℹ️  Currency exists: {currency.code} - {currency.name}")

# Create sample exchange rates
exchange_rates_data = [
    {'currency_code': 'USD', 'rate_to_base': Decimal('7.8'), 'source': 'HKMA'},
    {'currency_code': 'RMB', 'rate_to_base': Decimal('1.1'), 'source': 'Bank of China'},
    {'currency_code': 'JPY', 'rate_to_base': Decimal('0.052'), 'source': 'Reuters'},
    {'currency_code': 'EUR', 'rate_to_base': Decimal('8.5'), 'source': 'ECB'},
]

for rate_data in exchange_rates_data:
    try:
        currency = Currency.objects.get(code=rate_data['currency_code'])
        rate, created = ExchangeRate.objects.get_or_create(
            currency=currency,
            effective_date=timezone.now().date(),
            defaults={
                'rate_to_base': rate_data['rate_to_base'],
                'source': rate_data['source']
            }
        )
        if created:
            print(f"✅ Created exchange rate: {rate.currency.code} = {rate.rate_to_base} HKD")
        else:
            print(f"ℹ️  Exchange rate exists: {rate.currency.code} = {rate.rate_to_base} HKD")
    except Currency.DoesNotExist:
        print(f"❌ Currency {rate_data['currency_code']} not found")

print("\n🎉 Sample data creation completed!")
print("\nYou can now test the system with:")
print("- 3 Companies (CGGE, KI, KT)")
print("- 8 Expense Categories")
print("- 5 Currencies with exchange rates")
print("\nCache will be warmed up automatically on next request.")