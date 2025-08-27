#!/usr/bin/env python3
"""
Import expense categories for the expense claim system.
This script adds comprehensive expense categories based on common business needs.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/wongivan/ai_tools/business_tools/company_expense_claim_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_system.settings')
django.setup()

from claims.models import ExpenseCategory


def import_expense_categories():
    """Import comprehensive expense categories."""
    
    categories = [
        # Travel & Transportation
        {
            'code': 'transportation',
            'name': 'Transportation',
            'name_chinese': '交通',
            'name_simplified': '交通',
            'description': 'All forms of transportation including flights, trains, buses, taxis, etc.',
            'is_travel_related': True,
            'requires_receipt': True,
            'sort_order': 10
        },
        {
            'code': 'accommodation',
            'name': 'Accommodation',
            'name_chinese': '住宿',
            'name_simplified': '住宿',
            'description': 'Hotel, lodging, and accommodation expenses',
            'is_travel_related': True,
            'requires_receipt': True,
            'sort_order': 20
        },
        {
            'code': 'meals_travel',
            'name': 'Travel Meals',
            'name_chinese': '差旅餐費',
            'name_simplified': '差旅餐费',
            'description': 'Meals during business travel',
            'is_travel_related': True,
            'requires_receipt': True,
            'sort_order': 30
        },
        
        # Business Operations
        {
            'code': 'keynote_speech',
            'name': 'Keynote Speech',
            'name_chinese': '主題演講',
            'name_simplified': '主题演讲',
            'description': 'Expenses related to keynote speeches and presentations',
            'requires_participants': True,
            'requires_receipt': True,
            'sort_order': 40
        },
        {
            'code': 'sponsor_guest',
            'name': 'Sponsor Guest',
            'name_chinese': '贊助嘉賓',
            'name_simplified': '赞助嘉宾',
            'description': 'Expenses for sponsored guests and VIP entertainment',
            'requires_participants': True,
            'requires_receipt': True,
            'sort_order': 50
        },
        {
            'code': 'course_operations',
            'name': 'Course Operations',
            'name_chinese': '課程運營推廣',
            'name_simplified': '课程运营推广',
            'description': 'Course operation and promotion activities',
            'requires_receipt': True,
            'sort_order': 60
        },
        {
            'code': 'exhibition_procurement',
            'name': 'Exhibition & Procurement',
            'name_chinese': '展覽采購',
            'name_simplified': '展览采购',
            'description': 'Exhibition participation and procurement expenses',
            'requires_receipt': True,
            'sort_order': 70
        },
        {
            'code': 'business_negotiation',
            'name': 'Business Negotiation',
            'name_chinese': '業務商談',
            'name_simplified': '业务商谈',
            'description': 'Business meetings, negotiations, and client entertainment',
            'requires_participants': True,
            'requires_receipt': True,
            'sort_order': 80
        },
        
        # Professional Services
        {
            'code': 'instructor_misc',
            'name': 'Instructor Expenses',
            'name_chinese': '講師雜項',
            'name_simplified': '讲师杂项',
            'description': 'Miscellaneous instructor-related expenses',
            'requires_receipt': True,
            'sort_order': 90
        },
        {
            'code': 'procurement_misc',
            'name': 'Procurement Miscellaneous',
            'name_chinese': '采購雜項',
            'name_simplified': '采购杂项',
            'description': 'Miscellaneous procurement and supply expenses',
            'requires_receipt': True,
            'sort_order': 100
        },
        
        # Office & Equipment
        {
            'code': 'office_supplies',
            'name': 'Office Supplies',
            'name_chinese': '辦公用品',
            'name_simplified': '办公用品',
            'description': 'Stationery, office equipment, and supplies',
            'requires_receipt': True,
            'sort_order': 110
        },
        {
            'code': 'software_licenses',
            'name': 'Software & Licenses',
            'name_chinese': '軟件許可證',
            'name_simplified': '软件许可证',
            'description': 'Software subscriptions, licenses, and digital tools',
            'requires_receipt': True,
            'sort_order': 120
        },
        
        # Entertainment & Marketing
        {
            'code': 'client_entertainment',
            'name': 'Client Entertainment',
            'name_chinese': '客戶招待',
            'name_simplified': '客户招待',
            'description': 'Client entertainment and business meals',
            'requires_participants': True,
            'requires_receipt': True,
            'sort_order': 130
        },
        {
            'code': 'marketing_promotion',
            'name': 'Marketing & Promotion',
            'name_chinese': '市場推廣',
            'name_simplified': '市场推广',
            'description': 'Marketing activities, advertising, and promotional expenses',
            'requires_receipt': True,
            'sort_order': 140
        },
        
        # Communication & Utilities
        {
            'code': 'telecommunications',
            'name': 'Telecommunications',
            'name_chinese': '電訊通訊',
            'name_simplified': '电讯通讯',
            'description': 'Phone bills, internet, and communication expenses',
            'requires_receipt': True,
            'sort_order': 150
        },
        
        # Training & Development
        {
            'code': 'training_development',
            'name': 'Training & Development',
            'name_chinese': '培訓發展',
            'name_simplified': '培训发展',
            'description': 'Staff training, courses, and professional development',
            'requires_receipt': True,
            'sort_order': 160
        },
        
        # Miscellaneous
        {
            'code': 'other_misc',
            'name': 'Other Miscellaneous',
            'name_chinese': '其他雜項',
            'name_simplified': '其他杂项',
            'description': 'Other business-related expenses not covered by specific categories',
            'requires_receipt': True,
            'sort_order': 999
        }
    ]
    
    imported_count = 0
    updated_count = 0
    
    for category_data in categories:
        category, created = ExpenseCategory.objects.update_or_create(
            code=category_data['code'],
            defaults=category_data
        )
        
        if created:
            imported_count += 1
            print(f"✅ Created: {category.name} ({category.name_chinese})")
        else:
            updated_count += 1
            print(f"🔄 Updated: {category.name} ({category.name_chinese})")
    
    print(f"\n📊 Import Summary:")
    print(f"   New categories created: {imported_count}")
    print(f"   Existing categories updated: {updated_count}")
    print(f"   Total categories processed: {len(categories)}")
    
    return imported_count, updated_count


if __name__ == "__main__":
    print("🚀 Starting expense category import...")
    print("=" * 50)
    
    try:
        imported, updated = import_expense_categories()
        print("=" * 50)
        print("✅ Expense category import completed successfully!")
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ Error during import: {e}")
        sys.exit(1)
