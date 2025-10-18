"""
Management command to import staff from CSV file.
Usage: python manage.py import_staff --file /path/to/staff_list.csv
"""
import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Import staff from CSV file (staff_list.csv)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=os.path.expanduser('~/Downloads/staff_list.csv'),
            help='Path to staff CSV file (default: ~/Downloads/staff_list.csv)'
        )
        parser.add_argument(
            '--default-password',
            type=str,
            default='Krystal2025!',
            help='Default password for new users (default: Krystal2025!)'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing users instead of skipping them'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        default_password = options['default_password']
        update_existing = options['update_existing']

        # Check if file exists
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')

        self.stdout.write(self.style.SUCCESS(f'Reading staff data from: {file_path}'))

        # Statistics
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # Read CSV with proper handling of newlines in fields
                reader = csv.DictReader(csvfile)

                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                        try:
                            # Clean the data - remove any newlines and extra whitespace
                            username = row.get('username', '').strip().replace('\n', '')
                            email = row.get('email', '').strip().replace('\n', '')
                            first_name = row.get('first_name', '').strip().replace('\n', '')
                            last_name = row.get('last_name', '').strip().replace('\n', '')
                            region = row.get('region', 'HK').strip().replace('\n', '')
                            is_staff = row.get('is_staff', 'TRUE').strip().upper() == 'TRUE'

                            # Parse date_joined
                            date_joined_str = row.get('date_joined', '').strip().replace('\n', '')
                            try:
                                date_joined = datetime.strptime(date_joined_str, '%Y-%m-%d')
                            except ValueError:
                                date_joined = timezone.now()

                            # Skip if username is empty
                            if not username:
                                self.stdout.write(
                                    self.style.WARNING(f'Row {row_num}: Skipping empty username')
                                )
                                stats['skipped'] += 1
                                continue

                            # Check if user exists
                            user_exists = User.objects.filter(username=username).exists()

                            if user_exists:
                                if update_existing:
                                    # Update existing user
                                    user = User.objects.get(username=username)
                                    user.email = email
                                    user.first_name = first_name
                                    user.last_name = last_name
                                    user.is_staff = is_staff
                                    user.location = 'hk' if region.upper() == 'HK' else 'cn' if region.upper() == 'CN' else 'other'

                                    # Generate employee_id if not set
                                    if not user.employee_id:
                                        user.employee_id = f'EMP{user.id:04d}'

                                    user.save()

                                    self.stdout.write(
                                        self.style.SUCCESS(f'Row {row_num}: Updated user: {username}')
                                    )
                                    stats['updated'] += 1
                                else:
                                    self.stdout.write(
                                        self.style.WARNING(f'Row {row_num}: User {username} already exists, skipping')
                                    )
                                    stats['skipped'] += 1
                            else:
                                # Create new user
                                # Generate a temporary employee_id
                                temp_employee_id = f'TEMP_{username}'

                                user = User.objects.create_user(
                                    username=username,
                                    email=email,
                                    password=default_password,
                                    first_name=first_name,
                                    last_name=last_name,
                                    employee_id=temp_employee_id,
                                    is_staff=is_staff,
                                    is_active=True,
                                    location='hk' if region.upper() == 'HK' else 'cn' if region.upper() == 'CN' else 'other',
                                    role='staff',  # Default role
                                )

                                # Update employee_id with actual ID
                                user.employee_id = f'EMP{user.id:04d}'
                                user.save()

                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Row {row_num}: Created user: {username} '
                                        f'(Employee ID: {user.employee_id})'
                                    )
                                )
                                stats['created'] += 1

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
        self.stdout.write(self.style.SUCCESS(f'Users created:  {stats["created"]}'))
        self.stdout.write(self.style.SUCCESS(f'Users updated:  {stats["updated"]}'))
        self.stdout.write(self.style.WARNING(f'Users skipped:  {stats["skipped"]}'))
        self.stdout.write(self.style.ERROR(f'Errors:         {stats["errors"]}'))
        self.stdout.write(self.style.SUCCESS('='*60))

        if stats['created'] > 0 or stats['updated'] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDefault password for new users: {default_password}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'IMPORTANT: Users should change their password on first login!'
                )
            )
