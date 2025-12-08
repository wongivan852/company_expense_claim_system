"""
Management command to generate monthly statements for Stripe accounts
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from apps.stripe_management.models import StripeAccount, Transaction, MonthlyStatement
import csv


class Command(BaseCommand):
    help = 'Generate monthly statement for a Stripe account'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, required=True, help='Year for the statement')
        parser.add_argument('--month', type=int, required=True, help='Month for the statement (1-12)')
        parser.add_argument('--account', type=str, help='Account name or ID')
        parser.add_argument('--opening-balance', type=float, default=0, help='Opening balance in HKD')

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        account_name = options.get('account')
        opening_balance_cents = int(options.get('opening_balance', 0) * 100)

        # Get account
        if account_name:
            try:
                account = StripeAccount.objects.get(name=account_name)
            except StripeAccount.DoesNotExist:
                try:
                    account = StripeAccount.objects.get(account_id=account_name)
                except StripeAccount.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Account "{account_name}" not found'))
                    return
        else:
            self.stdout.write(self.style.ERROR('Please specify --account'))
            return

        # Get date range
        from calendar import monthrange
        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)

        self.stdout.write(f'\n{"="*80}')
        self.stdout.write(self.style.SUCCESS(f'Generating Monthly Statement for {account.name}'))
        self.stdout.write(self.style.SUCCESS(f'Period: {start_date.strftime("%B %Y")}'))
        self.stdout.write(f'{"="*80}\n')

        # Get transactions for the month
        transactions = Transaction.objects.filter(
            account=account,
            stripe_created__gte=timezone.make_aware(start_date),
            stripe_created__lte=timezone.make_aware(end_date)
        ).order_by('stripe_created')

        txn_count = transactions.count()
        self.stdout.write(f'Found {txn_count} transaction(s)\n')

        # If no transactions, we still generate a statement with opening = closing balance
        if txn_count == 0:
            self.stdout.write(self.style.WARNING(f'No transactions for this period - generating statement with carried forward balance\n'))

        # Calculate statement
        running_balance = opening_balance_cents
        total_gross_payments = 0
        total_fees = 0
        total_payouts = 0
        total_refunds = 0

        transaction_lines = []
        customer_transactions = []

        for txn in transactions:
            line = {
                'date': txn.stripe_created,
                'nature': '',
                'party': '',
                'debit': 0,
                'credit': 0,
                'balance': 0,
                'description': '',
                'transaction': txn
            }

            # Determine transaction nature and calculate balance
            if txn.type == 'charge' and txn.status == 'succeeded':
                # Gross Payment (adds to balance)
                line['nature'] = 'Gross Payment'
                line['party'] = txn.customer_email or 'Unknown'
                line['debit'] = txn.amount
                running_balance += txn.amount
                total_gross_payments += txn.amount

                # Track customer transaction
                customer_transactions.append({
                    'date': txn.stripe_created,
                    'customer_name': '',  # Would need to parse from metadata
                    'email': txn.customer_email,
                    'amount': txn.amount,
                })

            elif txn.type == 'refund':
                line['nature'] = 'Refund'
                line['party'] = 'Stripe'
                line['credit'] = txn.amount
                running_balance -= txn.amount
                total_refunds += txn.amount

            elif txn.type == 'payout':
                line['nature'] = 'Payout'
                line['party'] = 'Stripe'
                line['credit'] = txn.amount
                running_balance -= txn.amount
                total_payouts += txn.amount
                line['description'] = 'BOC(HK)'

            line['balance'] = running_balance
            transaction_lines.append(line)

            # Processing fee (separate line after payment)
            if txn.fee and txn.fee > 0:
                fee_line = {
                    'date': txn.stripe_created,
                    'nature': 'Processing Fee',
                    'party': 'Stripe',
                    'debit': 0,
                    'credit': txn.fee,
                    'balance': 0,
                    'description': 'Stripe processing fee',
                    'transaction': txn
                }
                running_balance -= txn.fee
                total_fees += txn.fee
                fee_line['balance'] = running_balance
                transaction_lines.append(fee_line)

        closing_balance = running_balance

        # Print statement
        self.stdout.write(self.style.SUCCESS(f'\nStatement Summary for {start_date.strftime("%B %Y")}'))
        self.stdout.write(f'Company: {account.account_id}')
        self.stdout.write(f'Opening Balance: HK${opening_balance_cents/100:.2f}')
        self.stdout.write(f'Closing Balance: HK${closing_balance/100:.2f}')
        self.stdout.write(f'Total Transactions: {len(transaction_lines)}\n')

        # Print transaction table
        self.stdout.write(f'{"Date":<12} {"Nature":<20} {"Party":<25} {"Debit":>12} {"Credit":>12} {"Balance":>12} {"Description":<30}')
        self.stdout.write('-' * 135)

        # Opening balance line
        self.stdout.write(
            f'{start_date.strftime("%Y-%m-%d"):<12} '
            f'{"Opening Balance":<20} '
            f'{"Brought Forward":<25} '
            f'{"":>12} '
            f'{"":>12} '
            f'{f"HK${opening_balance_cents/100:.2f}":>12} '
            f'{"Opening balance for " + start_date.strftime("%B %Y"):<30}'
        )

        for line in transaction_lines:
            date_str = line['date'].strftime('%Y-%m-%d')
            debit_str = f"HK${line['debit']/100:.2f}" if line['debit'] > 0 else ''
            credit_str = f"HK${line['credit']/100:.2f}" if line['credit'] > 0 else ''
            balance_str = f"HK${line['balance']/100:.2f}"

            self.stdout.write(
                f'{date_str:<12} '
                f'{line["nature"]:<20} '
                f'{line["party"][:25]:<25} '
                f'{debit_str:>12} '
                f'{credit_str:>12} '
                f'{balance_str:>12} '
                f'{line["description"][:30]:<30}'
            )

        # Subtotal
        self.stdout.write('-' * 135)
        debit_total_str = f"HK${total_gross_payments/100:.2f}"
        credit_total_str = f"HK${(total_fees + total_payouts + total_refunds)/100:.2f}"
        self.stdout.write(
            f'{"SUBTOTAL":<58} '
            f'{debit_total_str:>12} '
            f'{credit_total_str:>12}'
        )

        # Closing balance line
        closing_bal_str = f"HK${closing_balance/100:.2f}"
        closing_desc = f"Closing balance for {start_date.strftime('%B %Y')}"
        self.stdout.write(
            f'{end_date.strftime("%Y-%m-%d"):<12} '
            f'{"Closing Balance":<20} '
            f'{"Carry Forward":<25} '
            f'{"":>12} '
            f'{"":>12} '
            f'{closing_bal_str:>12} '
            f'{closing_desc:<30}'
        )

        # Customer transaction summary
        if customer_transactions:
            self.stdout.write(f'\n\n{self.style.SUCCESS("Customer Transaction Summary")}')
            self.stdout.write(f'Total Customer Transactions: {len(customer_transactions)}\n')
            self.stdout.write(f'{"Date":<12} {"Email":<40} {"Amount":>15}')
            self.stdout.write('-' * 70)

            total_customer_payments = 0
            for ct in customer_transactions:
                amount_str = f"HK${ct['amount']/100:.2f}"
                self.stdout.write(
                    f'{ct["date"].strftime("%Y-%m-%d"):<12} '
                    f'{ct["email"][:40]:<40} '
                    f'{amount_str:>15}'
                )
                total_customer_payments += ct['amount']

            self.stdout.write('-' * 70)
            total_pay_str = f"HK${total_customer_payments/100:.2f}"
            self.stdout.write(f'{"Total Customer Payments:":<52} {total_pay_str:>15}')

        # Save to database
        statement, created = MonthlyStatement.objects.update_or_create(
            account=account,
            year=year,
            month=month,
            defaults={
                'opening_balance': opening_balance_cents,
                'closing_balance': closing_balance,
                'total_charges': total_gross_payments,
                'total_refunds': total_refunds,
                'total_fees': total_fees,
                'total_payouts': total_payouts,
            }
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(f'\n{self.style.SUCCESS(f"{action} monthly statement in database")}')
        self.stdout.write(f'\nUse this closing balance as opening balance for next month:')
        self.stdout.write(self.style.SUCCESS(f'  --opening-balance {closing_balance/100:.2f}'))
