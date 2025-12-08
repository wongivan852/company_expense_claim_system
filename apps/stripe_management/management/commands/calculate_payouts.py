"""
Management command to calculate and add payout transactions
Based on the pattern from August 2025 statement where payouts happen regularly
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.stripe_management.models import StripeAccount, Transaction
from decimal import Decimal


class Command(BaseCommand):
    help = 'Calculate and add payout transactions for a month based on rolling payout schedule'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, required=True, help='Year')
        parser.add_argument('--month', type=int, required=True, help='Month (1-12)')
        parser.add_argument('--account', type=str, required=True, help='Account name')
        parser.add_argument('--payout-threshold', type=float, default=90.0,
                          help='Minimum balance to trigger payout (default: HK$90)')
        parser.add_argument('--payout-cutoff-day', type=int, default=None,
                          help='Only process payouts for charges before this day of month (e.g., 20 means charges up to day 20)')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be done without actually creating payouts')

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        account_name = options['account']
        threshold_cents = int(options['payout_threshold'] * 100)
        payout_cutoff_day = options.get('payout_cutoff_day')
        dry_run = options['dry_run']

        # Get account
        try:
            account = StripeAccount.objects.get(name=account_name)
        except StripeAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Account "{account_name}" not found'))
            return

        # Get date range
        from calendar import monthrange
        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)

        # Set payout cutoff date if specified
        payout_cutoff_date = None
        if payout_cutoff_day:
            payout_cutoff_date = timezone.make_aware(datetime(year, month, payout_cutoff_day, 23, 59, 59))

        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS(
            f'Calculating Payouts for {account.name} - {start_date.strftime("%B %Y")}'
        ))
        self.stdout.write(f'{"="*80}\n')

        if payout_cutoff_date:
            self.stdout.write(f'Payout cutoff: Only charges before {payout_cutoff_date.strftime("%Y-%m-%d")} will generate payouts\n')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No payouts will be created\n'))

        # Get all charge transactions for the month (ordered by date)
        charges = Transaction.objects.filter(
            account=account,
            stripe_created__gte=timezone.make_aware(start_date),
            stripe_created__lte=timezone.make_aware(end_date),
            type='charge',
            status='succeeded'
        ).order_by('stripe_created')

        if not charges.exists():
            self.stdout.write(self.style.WARNING('No charge transactions found'))
            return

        self.stdout.write(f'Found {charges.count()} charge transactions\n')

        # Simulate rolling balance and calculate payouts
        running_balance = 0
        payouts_to_create = []
        payout_number = 1

        for charge in charges:
            charge_date = charge.stripe_created

            # Add charge amount
            running_balance += charge.amount
            self.stdout.write(
                f'{charge_date.strftime("%Y-%m-%d %H:%M")} Charge: '
                f'+HK${charge.amount/100:.2f} = HK${running_balance/100:.2f}'
            )

            # Deduct fee
            if charge.fee:
                running_balance -= charge.fee
                self.stdout.write(
                    f'{charge_date.strftime("%Y-%m-%d %H:%M")} Fee:    '
                    f'-HK${charge.fee/100:.2f} = HK${running_balance/100:.2f}'
                )

            # Check if payout threshold reached
            if running_balance >= threshold_cents:
                # Schedule payout for next day (Stripe typically pays out T+1 or T+2)
                payout_date = charge_date + timedelta(days=1)
                payout_amount = running_balance

                # Only create payout if:
                # 1. No cutoff date specified, OR
                # 2. Charge date is before the cutoff date
                should_create_payout = (payout_cutoff_date is None) or (charge_date <= payout_cutoff_date)

                if should_create_payout:
                    self.stdout.write(self.style.SUCCESS(
                        f'{payout_date.strftime("%Y-%m-%d %H:%M")} PAYOUT: '
                        f'-HK${payout_amount/100:.2f} = HK$0.00'
                    ))

                    payouts_to_create.append({
                        'date': payout_date,
                        'amount': payout_amount,
                        'number': payout_number
                    })

                    running_balance = 0
                    payout_number += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f'{payout_date.strftime("%Y-%m-%d %H:%M")} PAYOUT SKIPPED (after cutoff): '
                        f'Would be -HK${payout_amount/100:.2f}'
                    ))

            self.stdout.write('')

        # Show summary
        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(f'SUMMARY:')
        self.stdout.write(f'{"="*80}')
        self.stdout.write(f'Total charges: {charges.count()}')
        self.stdout.write(f'Payouts to create: {len(payouts_to_create)}')
        self.stdout.write(f'Remaining balance: HK${running_balance/100:.2f}')

        total_payout_amount = sum(p['amount'] for p in payouts_to_create)
        self.stdout.write(f'Total payout amount: HK${total_payout_amount/100:.2f}\n')

        # Create payouts
        if not dry_run and payouts_to_create:
            self.stdout.write(self.style.WARNING('\nCreating payout transactions...'))

            created_count = 0
            for payout in payouts_to_create:
                # Generate payout ID
                payout_id = f"po_sim_{year}{month:02d}_{account.account_id}_{payout['number']:03d}"

                # Check if already exists
                if Transaction.objects.filter(stripe_id=payout_id).exists():
                    self.stdout.write(f'  Skipping {payout_id} (already exists)')
                    continue

                # Create payout transaction
                payout_datetime = payout['date']
                if timezone.is_naive(payout_datetime):
                    payout_datetime = timezone.make_aware(payout_datetime)

                Transaction.objects.create(
                    stripe_id=payout_id,
                    account=account,
                    amount=payout['amount'],
                    fee=0,
                    currency='hkd',
                    status='succeeded',
                    type='payout',
                    stripe_created=payout_datetime,
                    description='BOC(HK)',
                )
                created_count += 1
                self.stdout.write(f'  Created {payout_id}: HK${payout["amount"]/100:.2f}')

            self.stdout.write(self.style.SUCCESS(f'\n✓ Created {created_count} payout transactions'))
        elif dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No payouts created'))
            self.stdout.write('Run without --dry-run to create these payouts')

        self.stdout.write(f'\n{"="*80}')
        self.stdout.write('Done!')
        self.stdout.write(f'{"="*80}\n')
