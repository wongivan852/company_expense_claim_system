"""
Management command to setup initial leave types.
Usage: python manage.py setup_leave_types
"""
from django.core.management.base import BaseCommand
from apps.leave_management.models import LeaveType


class Command(BaseCommand):
    help = 'Setup initial leave types for the system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up leave types...'))

        leave_types = [
            {
                'name': 'Annual Leave',
                'description': 'Regular annual leave entitlement',
                'max_days_per_year': 14,
                'requires_approval': True,
                'is_active': True,
            },
            {
                'name': 'Sick Leave',
                'description': 'Sick leave for medical reasons',
                'max_days_per_year': 10,
                'requires_approval': False,
                'is_active': True,
            },
            {
                'name': 'Special Leave',
                'description': 'Special leave earned from working on rest days/holidays',
                'max_days_per_year': 0,  # No limit, earned through special work
                'requires_approval': True,
                'is_active': True,
            },
            {
                'name': 'Maternity Leave',
                'description': 'Maternity leave',
                'max_days_per_year': 90,
                'requires_approval': True,
                'is_active': True,
            },
            {
                'name': 'Paternity Leave',
                'description': 'Paternity leave',
                'max_days_per_year': 5,
                'requires_approval': True,
                'is_active': True,
            },
            {
                'name': 'Compassionate Leave',
                'description': 'Leave for family bereavement',
                'max_days_per_year': 5,
                'requires_approval': True,
                'is_active': True,
            },
            {
                'name': 'Unpaid Leave',
                'description': 'Unpaid leave',
                'max_days_per_year': 0,
                'requires_approval': True,
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for leave_data in leave_types:
            leave_type, created = LeaveType.objects.update_or_create(
                name=leave_data['name'],
                defaults=leave_data
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {leave_type.name}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'  ~ Updated: {leave_type.name}'))
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Updated: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Total: {LeaveType.objects.count()}'))
