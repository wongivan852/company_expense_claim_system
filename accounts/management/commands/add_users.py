"""
Management command to add users to the Krystal Group expense system.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Add users to the Krystal Group expense system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Add users interactively',
        )
        parser.add_argument(
            '--batch',
            action='store_true',
            help='Add sample users in batch',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Krystal Group User Management')
        )

        if options['interactive']:
            self.add_user_interactive()
        elif options['batch']:
            self.add_sample_users()
        else:
            self.stdout.write(
                self.style.ERROR('Please specify either --interactive or --batch')
            )
            self.stdout.write('Usage examples:')
            self.stdout.write('  python manage.py add_users --interactive')
            self.stdout.write('  python manage.py add_users --batch')

    def add_user_interactive(self):
        """Add a single user interactively."""
        self.stdout.write('\n--- Add New User ---')
        
        try:
            # Basic information
            username = input('Username: ').strip()
            if not username:
                self.stdout.write(self.style.ERROR('Username is required'))
                return

            email = input('Email: ').strip()
            if not email:
                self.stdout.write(self.style.ERROR('Email is required'))
                return

            password = input('Password (leave blank for default "temp123"): ').strip()
            if not password:
                password = 'temp123'

            # Employee information
            employee_id = input('Employee ID (e.g., KI001): ').strip()
            if not employee_id:
                self.stdout.write(self.style.ERROR('Employee ID is required'))
                return

            first_name = input('First Name: ').strip()
            last_name = input('Last Name: ').strip()
            department = input('Department (optional): ').strip()
            position = input('Position (optional): ').strip()

            # Role selection
            self.stdout.write('\nRole options:')
            self.stdout.write('1. staff (default)')
            self.stdout.write('2. manager')
            self.stdout.write('3. admin')
            role_choice = input('Select role (1-3): ').strip()
            role_map = {'1': 'staff', '2': 'manager', '3': 'admin'}
            role = role_map.get(role_choice, 'staff')

            # Location selection
            self.stdout.write('\nLocation options:')
            self.stdout.write('1. hk (Hong Kong, default)')
            self.stdout.write('2. cn (China)')
            self.stdout.write('3. other')
            location_choice = input('Select location (1-3): ').strip()
            location_map = {'1': 'hk', '2': 'cn', '3': 'other'}
            location = location_map.get(location_choice, 'hk')

            phone = input('Phone (optional): ').strip()

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                department=department,
                position=position,
                role=role,
                location=location,
                phone=phone,
                is_staff=(role in ['manager', 'admin']),
                is_superuser=(role == 'admin')
            )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created user: {user.username} ({user.get_full_name()})')
            )
            self.stdout.write(f'Employee ID: {user.employee_id}')
            self.stdout.write(f'Role: {user.role}')
            self.stdout.write(f'Location: {user.location}')

        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f'Validation error: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {e}'))

    def add_sample_users(self):
        """Add sample users for testing."""
        sample_users = [
            {
                'username': 'mary.wong',
                'email': 'mary.wong@krystalgroup.com',
                'password': 'temp123',
                'employee_id': 'KI001',
                'first_name': 'Mary',
                'last_name': 'Wong',
                'department': 'Education',
                'position': 'Course Coordinator',
                'role': 'staff',
                'location': 'hk',
                'phone': '+852-9876-5432'
            },
            {
                'username': 'david.chen',
                'email': 'david.chen@krystalgroup.com',
                'password': 'temp123',
                'employee_id': 'KT001',
                'first_name': 'David',
                'last_name': 'Chen',
                'department': 'Technology',
                'position': 'Senior Developer',
                'role': 'staff',
                'location': 'hk',
                'phone': '+852-9876-5433'
            },
            {
                'username': 'sarah.lim',
                'email': 'sarah.lim@krystalgroup.com',
                'password': 'temp123',
                'employee_id': 'CGGE001',
                'first_name': 'Sarah',
                'last_name': 'Lim',
                'department': 'Entertainment',
                'position': 'Event Manager',
                'role': 'manager',
                'location': 'hk',
                'phone': '+852-9876-5434'
            },
            {
                'username': 'zhang.wei',
                'email': 'zhang.wei@krystalgroup.com',
                'password': 'temp123',
                'employee_id': 'SPSZ001',
                'first_name': 'Wei',
                'last_name': 'Zhang',
                'department': 'Technology',
                'position': 'Technical Director',
                'role': 'manager',
                'location': 'cn',
                'phone': '+86-138-0000-1234'
            },
            {
                'username': 'lisa.finance',
                'email': 'lisa.huang@krystalgroup.com',
                'password': 'temp123',
                'employee_id': 'KI002',
                'first_name': 'Lisa',
                'last_name': 'Huang',
                'department': 'Finance',
                'position': 'Finance Manager',
                'role': 'manager',
                'location': 'hk',
                'phone': '+852-9876-5435'
            }
        ]

        created_count = 0
        for user_data in sample_users:
            try:
                # Check if user already exists
                if User.objects.filter(username=user_data['username']).exists():
                    self.stdout.write(
                        self.style.WARNING(f'User {user_data["username"]} already exists, skipping')
                    )
                    continue

                if User.objects.filter(employee_id=user_data['employee_id']).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Employee ID {user_data["employee_id"]} already exists, skipping')
                    )
                    continue

                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    employee_id=user_data['employee_id'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    department=user_data['department'],
                    position=user_data['position'],
                    role=user_data['role'],
                    location=user_data['location'],
                    phone=user_data['phone'],
                    is_staff=(user_data['role'] in ['manager', 'admin']),
                    is_superuser=(user_data['role'] == 'admin')
                )
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {user.username} ({user.get_full_name()})')
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating user {user_data["username"]}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} users')
        )

        # Display all users
        self.display_all_users()

    def display_all_users(self):
        """Display all users in the system."""
        self.stdout.write('\n--- Current Users ---')
        users = User.objects.all().order_by('employee_id')
        
        for user in users:
            role_display = f"{user.role}"
            if user.is_superuser:
                role_display += " (superuser)"
            elif user.is_staff:
                role_display += " (staff access)"
                
            self.stdout.write(
                f'{user.employee_id}: {user.username} - {user.get_full_name()} '
                f'({user.department}) - {role_display} - {user.get_location_display()}'
            )
