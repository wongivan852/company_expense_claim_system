"""
Management command to import Stripe transactions from CSV files
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.stripe_management.models import StripeAccount, Transaction
import csv
import os
from datetime import datetime
from decimal import Decimal


class Command(BaseCommand):
    help = 'Import Stripe transactions from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file to import'
        )
        parser.add_argument(
            '--account',
            type=str,
            help='Stripe account ID to associate transactions with'
        )
        parser.add_argument(
            '--create-account',
            type=str,
            help='Create account with this name if it doesn\'t exist'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        account_id = options.get('account')
        account_name = options.get('create_account')

        # Check if file exists
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return

        # Get or create account
        if account_name:
            account, created = StripeAccount.objects.get_or_create(
                account_id=account_name.lower().replace(' ', '_'),
                defaults={
                    'name': account_name,
                    'api_key': 'imported',
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created account: {account.name}'))
        elif account_id:
            try:
                account = StripeAccount.objects.get(account_id=account_id)
            except StripeAccount.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Account not found: {account_id}'))
                return
        else:
            self.stdout.write(self.style.ERROR('Please specify --account or --create-account'))
            return

        # Import CSV
        imported_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(f'Importing from: {csv_file}')
        self.stdout.write(f'Target account: {account.name}')

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Skip empty rows
                    if not row.get('id'):
                        skipped_count += 1
                        continue

                    stripe_id = row['id']
                    
                    # Check if transaction already exists
                    if Transaction.objects.filter(stripe_id=stripe_id).exists():
                        skipped_count += 1
                        continue

                    # Parse amount (convert to cents)
                    amount_str = row.get('Converted Amount', row.get('Amount', '0'))
                    amount = int(float(amount_str or 0) * 100)

                    # Parse fee
                    fee_str = row.get('Fee', '0')
                    fee = int(float(fee_str or 0) * 100)

                    # Parse currency
                    currency = row.get('Converted Currency', row.get('Currency', 'hkd')).lower()

                    # Parse date
                    date_str = row.get('Created date (UTC)', '')
                    if date_str:
                        try:
                            stripe_created = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                            stripe_created = timezone.make_aware(stripe_created, timezone.utc)
                        except ValueError:
                            stripe_created = timezone.now()
                    else:
                        stripe_created = timezone.now()

                    # Determine status
                    status_raw = row.get('Status', '').lower()
                    if status_raw == 'paid':
                        status = 'succeeded'
                    elif status_raw == 'canceled':
                        status = 'canceled'
                    else:
                        status = status_raw or 'pending'

                    # Determine type
                    if row.get('Amount Refunded') and float(row['Amount Refunded'] or 0) > 0:
                        txn_type = 'refund'
                    else:
                        txn_type = 'charge'

                    # Create transaction
                    Transaction.objects.create(
                        stripe_id=stripe_id,
                        account=account,
                        amount=amount,
                        fee=fee,
                        currency=currency,
                        status=status,
                        type=txn_type,
                        stripe_created=stripe_created,
                        customer_email=row.get('Customer Email', ''),
                        description=row.get('Description', ''),
                        stripe_metadata={
                            'customer_id': row.get('Customer ID', ''),
                            'card_id': row.get('Card ID', ''),
                            'invoice_id': row.get('Invoice ID', ''),
                            'subs_type': row.get('subs_type (metadata)', ''),
                            'site': row.get('site (metadata)', ''),
                        }
                    )

                    imported_count += 1

                    if imported_count % 100 == 0:
                        self.stdout.write(f'Imported {imported_count} transactions...')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.WARNING(f'Error importing row: {str(e)}'))
                    continue

        self.stdout.write(self.style.SUCCESS(f'\nImport complete!'))
        self.stdout.write(f'Imported: {imported_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write(f'Errors: {error_count}')
