"""
Management command to set up default expense categories.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.expense_claims.models import ExpenseCategory


class Command(BaseCommand):
    help = 'Set up default expense categories for Krystal Group'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Setting up default expense categories...')

        # Default categories based on PDF form structure
        categories_data = [
            {
                'code': 'keynote_speech',
                'name': 'Keynote Speech',
                'name_chinese': '主題演講',
                'description': 'Expenses related to keynote speeches and presentations',
                'requires_receipt': True,
                'is_travel_related': False,
                'requires_participants': True,
                'sort_order': 1
            },
            {
                'code': 'sponsor_guest',
                'name': 'Sponsor Guest',
                'name_chinese': '贊助嘉賓',
                'description': 'Sponsor and guest related expenses',
                'requires_receipt': True,
                'is_travel_related': False,
                'requires_participants': True,
                'sort_order': 2
            },
            {
                'code': 'course_operations',
                'name': 'Course Operations',
                'name_chinese': '課程運營推廣',
                'description': 'Course operations and promotion expenses',
                'requires_receipt': True,
                'is_travel_related': False,
                'requires_participants': False,
                'sort_order': 3
            },
            {
                'code': 'exhibition_procurement',
                'name': 'Exhibition Procurement',
                'name_chinese': '展覽采購',
                'description': 'Exhibition and procurement related expenses',
                'requires_receipt': True,
                'is_travel_related': False,
                'requires_participants': False,
                'sort_order': 4
            },
            {
                'code': 'business_negotiation',
                'name': 'Business Negotiation',
                'name_chinese': '業務商談',
                'description': 'Business meeting and negotiation expenses',
                'requires_receipt': True,
                'is_travel_related': True,
                'requires_participants': True,
                'sort_order': 5
            },
            {
                'code': 'instructor_misc',
                'name': 'Instructor Miscellaneous',
                'name_chinese': '講師雜項',
                'description': 'Instructor related miscellaneous expenses',
                'requires_receipt': True,
                'is_travel_related': False,
                'requires_participants': False,
                'sort_order': 6
            },
            {
                'code': 'procurement_misc',
                'name': 'Procurement Miscellaneous',
                'name_chinese': '采購雜項',
                'description': 'Procurement miscellaneous expenses',
                'requires_receipt': True,
                'is_travel_related': False,
                'requires_participants': False,
                'sort_order': 7
            },
            {
                'code': 'transportation',
                'name': 'Transportation',
                'name_chinese': '交通',
                'description': 'Transportation and travel expenses',
                'requires_receipt': True,
                'is_travel_related': True,
                'requires_participants': False,
                'sort_order': 8
            },
            {
                'code': 'other_misc',
                'name': 'Other Miscellaneous',
                'name_chinese': '其他雜項',
                'description': 'Other miscellaneous expenses',
                'requires_receipt': True,
                'is_travel_related': False,
                'requires_participants': False,
                'sort_order': 9
            }
        ]

        created_count = 0
        for category_data in categories_data:
            category, created = ExpenseCategory.objects.get_or_create(
                code=category_data['code'],
                defaults=category_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name} ({category.name_chinese})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully set up {created_count} expense categories')
        )

        # Display all categories
        self.stdout.write('\n=== Current Expense Categories ===')
        categories = ExpenseCategory.objects.all().order_by('sort_order')
        for category in categories:
            travel_icon = '✈️' if category.is_travel_related else '🏢'
            receipt_icon = '📋' if category.requires_receipt else '📝'
            participants_icon = '👥' if category.requires_participants else '👤'
            
            self.stdout.write(
                f'{travel_icon}{receipt_icon}{participants_icon} {category.code}: {category.name} ({category.name_chinese})'
            )
