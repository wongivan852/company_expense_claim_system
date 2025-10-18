"""
Management command to import leave balances from staff CSV file.
Usage: python manage.py import_leave_balances --file /path/to/staff_list.csv
"""
import csv
import os
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.leave_management.models import LeaveType, LeaveBalance

User = get_user_model()


class Command(BaseCommand):
    help = 'Import leave balances from staff CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=os.path.expanduser('~/Downloads/staff_list.csv'),
            help='Path to staff CSV file (default: ~/Downloads/staff_list.csv)'
        )
        parser.add_argument(
            '--year',
            type=int,
            default=2025,
            help='Year for leave balances (default: 2025)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        year = options['year']

        # Check if file exists
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')

        self.stdout.write(self.style.SUCCESS(f'Importing leave balances from: {file_path}'))

        # Get or create leave types
        annual_leave, _ = LeaveType.objects.get_or_create(
            name='Annual Leave',
            defaults={
                'description': 'Regular annual leave entitlement',
                'max_days_per_year': 14,
                'requires_approval': True,
                'is_active': True,
            }
        )

        sick_leave, _ = LeaveType.objects.get_or_create(
            name='Sick Leave',
            defaults={
                'description': 'Sick leave for medical reasons',
                'max_days_per_year': 10,
                'requires_approval': False,
                'is_active': True,
            }
        )

        # Statistics
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        username = row.get('username', '').strip().replace('\n', '')
                        if not username:
                            stats['skipped'] += 1
                            continue

                        # Get user
                        try:
                            user = User.objects.get(username=username)
                        except User.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f'Row {row_num}: User not found: {username}')
                            )
                            stats['skipped'] += 1
                            continue

                        # Get leave balance values
                        annual_balance = row.get('annual_leave_balance', '14').strip().replace('\n', '')
                        sick_balance = row.get('sick_leave_balance', '10').strip().replace('\n', '')

                        try:
                            annual_balance = Decimal(annual_balance) if annual_balance else Decimal('14')
                            sick_balance = Decimal(sick_balance) if sick_balance else Decimal('10')
                        except:
                            annual_balance = Decimal('14')
                            sick_balance = Decimal('10')

                        # Create or update Annual Leave balance
                        annual_obj, created = LeaveBalance.objects.update_or_create(
                            user=user,
                            leave_type=annual_leave,
                            year=year,
                            defaults={
                                'opening_balance': Decimal('0'),
                                'carried_forward': Decimal('0'),
                                'current_year_entitlement': annual_balance,
                                'taken': Decimal('0'),
                            }
                        )

                        # Create or update Sick Leave balance
                        sick_obj, sick_created = LeaveBalance.objects.update_or_create(
                            user=user,
                            leave_type=sick_leave,
                            year=year,
                            defaults={
                                'opening_balance': Decimal('0'),
                                'carried_forward': Decimal('0'),
                                'current_year_entitlement': sick_balance,
                                'taken': Decimal('0'),
                            }
                        )

                        if created or sick_created:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Row {row_num}: Created balances for {user.get_full_name()} '
                                    f'(Annual: {annual_balance}, Sick: {sick_balance})'
                                )
                            )
                            stats['created'] += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Row {row_num}: Updated balances for {user.get_full_name()}'
                                )
                            )
                            stats['updated'] += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Row {row_num}: Error processing {row.get("username", "unknown")}: {str(e)}'
                            )
                        )
                        stats['errors'] += 1

        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')

        # Print summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('IMPORT SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS(f'Balances created:  {stats["created"]}'))
        self.stdout.write(self.style.SUCCESS(f'Balances updated:  {stats["updated"]}'))
        self.stdout.write(self.style.WARNING(f'Skipped:           {stats["skipped"]}'))
        self.stdout.write(self.style.ERROR(f'Errors:            {stats["errors"]}'))
        self.stdout.write(self.style.SUCCESS('='*60))
