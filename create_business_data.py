#!/usr/bin/env python
"""
Create comprehensive business data matching the PDF requirements.
This includes the 4 specific companies and enhanced expense categories.
"""
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

print("🏢 Creating Enhanced Business Data for Expense Claim System")
print("=" * 60)

# Create the 4 specific business companies
companies_data = [
    {
        'name': 'Krystal Institute Limited',
        'name_chinese': '晶曜學院有限公司',
        'name_simplified': '晶曜学院有限公司',
        'code': 'KIL',
        'company_type': 'institute',
        'address': 'Hong Kong',
        'address_chinese': '香港',
        'country_code': 'HK',
        'requires_manager_approval': True,
        'approval_threshold': Decimal('5000.00'),
    },
    {
        'name': 'Krystal Technology Limited',
        'name_chinese': '晶曜科技有限公司',
        'name_simplified': '晶曜科技有限公司',
        'code': 'KTL',
        'company_type': 'technology',
        'address': 'Hong Kong',
        'address_chinese': '香港',
        'country_code': 'HK',
        'requires_manager_approval': True,
        'approval_threshold': Decimal('10000.00'),
    },
    {
        'name': 'CG Global Entertainment Limited',
        'name_chinese': 'CG環球娛樂有限公司',
        'name_simplified': 'CG环球娱乐有限公司',
        'code': 'CGEL',
        'company_type': 'entertainment',
        'address': 'Hong Kong',
        'address_chinese': '香港',
        'country_code': 'HK',
        'requires_manager_approval': True,
        'approval_threshold': Decimal('8000.00'),
    },
    {
        'name': 'Shuzpu Global (Shenzhen) Technology Co., Ltd',
        'name_chinese': '數譜環球(深圳)科技有限公司',
        'name_simplified': '数谱环球(深圳)科技有限公司',
        'code': 'SPGZ',
        'company_type': 'technology',
        'address': 'Shenzhen, China',
        'address_chinese': '中國深圳',
        'country_code': 'CN',
        'requires_manager_approval': True,
        'approval_threshold': Decimal('30000.00'),  # Higher threshold for CN operations
    }
]

print("📋 Creating Companies...")
for company_data in companies_data:
    company, created = Company.objects.get_or_create(
        code=company_data['code'],
        defaults=company_data
    )
    if created:
        print(f"✅ Created: {company.name} ({company.name_chinese})")
    else:
        # Update existing company with new fields
        for field, value in company_data.items():
            setattr(company, field, value)
        company.save()
        print(f"📝 Updated: {company.name} ({company.name_chinese})")

# Create enhanced expense categories matching PDF structure
categories_data = [
    {
        'code': 'keynote_speech',
        'name': 'Keynote Speech',
        'name_chinese': '主題演講',
        'name_simplified': '主题演讲',
        'description': 'Expenses related to keynote speeches and presentations',
        'requires_receipt': True,
        'is_travel_related': False,
        'requires_participants': True,
        'sort_order': 1,
    },
    {
        'code': 'sponsor_guest',
        'name': 'Sponsor/Guest Entertainment',
        'name_chinese': '贊助嘉賓',
        'name_simplified': '赞助嘉宾',
        'description': 'Entertainment expenses for sponsors and guests',
        'requires_receipt': True,
        'is_travel_related': False,
        'requires_participants': True,
        'sort_order': 2,
    },
    {
        'code': 'course_operations',
        'name': 'Course Operations & Marketing',
        'name_chinese': '課程運營推廣',
        'name_simplified': '课程运营推广',
        'description': 'Course operations, marketing and promotional activities',
        'requires_receipt': True,
        'is_travel_related': False,
        'requires_participants': False,
        'sort_order': 3,
    },
    {
        'code': 'exhibition_procurement',
        'name': 'Exhibition Procurement',
        'name_chinese': '展覽采購',
        'name_simplified': '展览采购',
        'description': 'Procurement for exhibitions and displays',
        'requires_receipt': True,
        'is_travel_related': False,
        'requires_participants': False,
        'sort_order': 4,
    },
    {
        'code': 'other_misc',
        'name': 'Other Miscellaneous',
        'name_chinese': '其他雜項',
        'name_simplified': '其他杂项',
        'description': 'Other miscellaneous business expenses',
        'requires_receipt': False,
        'is_travel_related': False,
        'requires_participants': False,
        'sort_order': 5,
    },
    {
        'code': 'business_negotiation',
        'name': 'Business Negotiations',
        'name_chinese': '業務商談',
        'name_simplified': '业务商谈',
        'description': 'Expenses for business meetings and negotiations',
        'requires_receipt': True,
        'is_travel_related': False,
        'requires_participants': True,
        'sort_order': 6,
    },
    {
        'code': 'instructor_misc',
        'name': 'Instructor Miscellaneous',
        'name_chinese': '講師雜項',
        'name_simplified': '讲师杂项',
        'description': 'Miscellaneous expenses for instructors',
        'requires_receipt': True,
        'is_travel_related': False,
        'requires_participants': False,
        'sort_order': 7,
    },
    {
        'code': 'procurement_misc',
        'name': 'Procurement Miscellaneous',
        'name_chinese': '采購雜項',
        'name_simplified': '采购杂项',
        'description': 'General procurement expenses',
        'requires_receipt': True,
        'is_travel_related': False,
        'requires_participants': False,
        'sort_order': 8,
    },
    {
        'code': 'transportation',
        'name': 'Transportation',
        'name_chinese': '交通',
        'name_simplified': '交通',
        'description': 'Transportation expenses including taxis, MTR, cross-border travel',
        'requires_receipt': False,  # Many transport receipts not available
        'is_travel_related': True,
        'requires_participants': True,  # Often multiple people
        'sort_order': 9,
    }
]

print("\n📂 Creating Enhanced Expense Categories...")
for category_data in categories_data:
    category, created = ExpenseCategory.objects.get_or_create(
        code=category_data['code'],
        defaults=category_data
    )
    if created:
        print(f"✅ Created: {category.name} ({category.name_chinese})")
    else:
        # Update existing categories with new fields
        for field, value in category_data.items():
            setattr(category, field, value)
        category.save()
        print(f"📝 Updated: {category.name} ({category.name_chinese})")

# Create enhanced currencies with proper business exchange rates
currencies_data = [
    {
        'code': 'HKD',
        'name': 'Hong Kong Dollar',
        'symbol': 'HK$',
        'is_base_currency': True,
        'is_active': True
    },
    {
        'code': 'USD',
        'name': 'US Dollar',
        'symbol': 'US$',
        'is_base_currency': False,
        'is_active': True
    },
    {
        'code': 'RMB',
        'name': 'Chinese Renminbi',
        'symbol': '¥',
        'is_base_currency': False,
        'is_active': True
    },
    {
        'code': 'CNY',
        'name': 'Chinese Yuan',
        'symbol': 'CN¥',
        'is_base_currency': False,
        'is_active': True
    },
    {
        'code': 'JPY',
        'name': 'Japanese Yen',
        'symbol': '¥',
        'is_base_currency': False,
        'is_active': True
    },
    {
        'code': 'EUR',
        'name': 'Euro',
        'symbol': '€',
        'is_base_currency': False,
        'is_active': True
    }
]

print("\n💰 Creating Enhanced Currencies...")
for currency_data in currencies_data:
    currency, created = Currency.objects.get_or_create(
        code=currency_data['code'],
        defaults=currency_data
    )
    if created:
        print(f"✅ Created: {currency.code} - {currency.name}")
    else:
        print(f"ℹ️  Currency exists: {currency.code} - {currency.name}")

# Create business-accurate exchange rates (from PDF: 1 CNY = 1.08 HKD)
exchange_rates_data = [
    {'currency_code': 'USD', 'rate_to_base': Decimal('7.8'), 'source': 'HKMA'},
    {'currency_code': 'RMB', 'rate_to_base': Decimal('1.08'), 'source': 'Bank of China'},  # From PDF
    {'currency_code': 'CNY', 'rate_to_base': Decimal('1.08'), 'source': 'Bank of China'},  # From PDF
    {'currency_code': 'JPY', 'rate_to_base': Decimal('0.052'), 'source': 'Reuters'},
    {'currency_code': 'EUR', 'rate_to_base': Decimal('8.5'), 'source': 'ECB'},
]

print("\n📈 Creating Business Exchange Rates...")
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
            print(f"✅ Created: 1 {rate.currency.code} = {rate.rate_to_base} HKD")
        else:
            # Update existing rate
            rate.rate_to_base = rate_data['rate_to_base']
            rate.source = rate_data['source']
            rate.save()
            print(f"📝 Updated: 1 {rate.currency.code} = {rate.rate_to_base} HKD")
    except Currency.DoesNotExist:
        print(f"❌ Currency {rate_data['currency_code']} not found")

# Set base currency for companies
print("\n🏦 Setting Base Currencies for Companies...")
try:
    hkd_currency = Currency.objects.get(code='HKD')
    rmb_currency = Currency.objects.get(code='RMB')
    
    # HK companies use HKD
    for code in ['KIL', 'KTL', 'CGEL']:
        try:
            company = Company.objects.get(code=code)
            company.base_currency = hkd_currency
            company.save()
            print(f"✅ Set {company.code} base currency to HKD")
        except Company.DoesNotExist:
            print(f"❌ Company {code} not found")
    
    # CN company uses RMB
    try:
        company = Company.objects.get(code='SPGZ')
        company.base_currency = rmb_currency
        company.save()
        print(f"✅ Set {company.code} base currency to RMB")
    except Company.DoesNotExist:
        print(f"❌ Company SPGZ not found")

except Currency.DoesNotExist:
    print("❌ Base currencies not found")

print("\n" + "=" * 60)
print("🎉 Enhanced Business Data Creation Completed!")
print(f"""
📊 Summary:
✅ 4 Business Companies (KIL, KTL, CGEL, SPGZ)
✅ 9 Enhanced Expense Categories (matching PDF)
✅ 6 Multi-currency Support
✅ Business Exchange Rates (1 CNY = 1.08 HKD)
✅ Multi-language Support (EN/繁/简)

🌐 Companies Created:
• Krystal Institute Limited (晶曜學院有限公司)
• Krystal Technology Limited (晶曜科技有限公司) 
• CG Global Entertainment Limited (CG環球娛樂有限公司)
• 数谱环球(深圳)科技有限公司 (Shenzhen Operations)

📂 Categories (PDF Form Structure):
• 主題演講 (Keynote Speech)
• 贊助嘉賓 (Sponsor/Guest)
• 課程運營推廣 (Course Operations)
• 展覽采購 (Exhibition Procurement)
• 其他雜項 (Other Miscellaneous)
• 業務商談 (Business Negotiations)
• 講師雜項 (Instructor Miscellaneous)
• 采購雜項 (Procurement Miscellaneous)
• 交通 (Transportation)

💰 Exchange Rate (from PDF):
• 1 CNY/RMB = 1.08 HKD (Business Accurate)

🚀 Ready for IAICC Event Expense Claims!
""")