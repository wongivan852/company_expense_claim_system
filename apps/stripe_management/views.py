"""
Stripe Management Views
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from datetime import datetime
from .models import StripeAccount, Transaction, MonthlyStatement


@login_required
def dashboard(request):
    """Stripe management dashboard"""
    accounts = StripeAccount.objects.filter(is_active=True)
    
    # Get summary statistics
    total_transactions = Transaction.objects.count()
    total_revenue = Transaction.objects.filter(
        type='charge',
        status='succeeded'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    recent_transactions = Transaction.objects.select_related('account').order_by('-stripe_created')[:10]
    
    context = {
        'accounts': accounts,
        'total_transactions': total_transactions,
        'total_revenue': total_revenue / 100,  # Convert to dollars
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'stripe_management/dashboard.html', context)


@login_required
def account_list(request):
    """List all Stripe accounts"""
    accounts = StripeAccount.objects.annotate(
        transaction_count=Count('transactions')
    ).order_by('-created_at')
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'stripe_management/account_list.html', context)


@login_required
def transaction_list(request):
    """List transactions with filtering"""
    transactions = Transaction.objects.select_related('account').order_by('-stripe_created')
    
    # Apply filters
    account_id = request.GET.get('account')
    status = request.GET.get('status')
    transaction_type = request.GET.get('type')
    
    if account_id:
        transactions = transactions.filter(account_id=account_id)
    if status:
        transactions = transactions.filter(status=status)
    if transaction_type:
        transactions = transactions.filter(type=transaction_type)
    
    context = {
        'transactions': transactions[:100],  # Limit for performance
        'accounts': StripeAccount.objects.filter(is_active=True),
        'selected_account': account_id,
        'selected_status': status,
        'selected_type': transaction_type,
    }
    
    return render(request, 'stripe_management/transaction_list.html', context)


@login_required
def statement_list(request):
    """List monthly statements"""
    statements = MonthlyStatement.objects.select_related('account', 'reconciled_by').order_by('-year', '-month')
    
    # Apply filters
    account_id = request.GET.get('account')
    year = request.GET.get('year')
    reconciled = request.GET.get('reconciled')
    
    if account_id:
        statements = statements.filter(account_id=account_id)
    if year:
        statements = statements.filter(year=year)
    if reconciled is not None:
        statements = statements.filter(is_reconciled=reconciled == 'true')
    
    context = {
        'statements': statements,
        'accounts': StripeAccount.objects.filter(is_active=True),
        'years': range(datetime.now().year, 2020, -1),
        'selected_account': account_id,
        'selected_year': year,
        'selected_reconciled': reconciled,
    }
    
    return render(request, 'stripe_management/statement_list.html', context)


@login_required
def generate_statement(request):
    """Generate monthly statement"""
    from django.db.models import Sum
    from datetime import date
    from calendar import monthrange
    import sys
    import os

    # Get parameters
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    account_id = request.GET.get('account')

    # Get account
    account = None
    if account_id:
        account = get_object_or_404(StripeAccount, id=account_id)

    # Try to use CompleteCsvService for CSV-based data
    csv_statement = None
    try:
        # Add stripe-dashboard to path
        stripe_dashboard_path = '/Users/wongivan/ai_tools/business_tools/stripe-dashboard'
        if stripe_dashboard_path not in sys.path:
            sys.path.insert(0, stripe_dashboard_path)

        from app.services.complete_csv_service import CompleteCsvService

        # Map account names to company codes
        company_code_map = {
            'CGGE Media': 'cgge',
            'Krystal Institute': 'krystal_institute',
            'Krystal Technology': 'krystal_technology'
        }

        if account and account.name in company_code_map:
            # Specify the correct CSV directory
            csv_dir = os.path.join(stripe_dashboard_path, 'complete_csv')
            service = CompleteCsvService(csv_directory=csv_dir)
            company_code = company_code_map[account.name]
            # Generate monthly statement (will use transaction dates by default)
            csv_statement = service.generate_monthly_statement(year, month, company_code)
    except Exception as e:
        # Fall back to database if CSV service fails
        print(f"CSV service error: {e}")
        csv_statement = None
    
    # Calculate date range
    start_date = datetime(year, month, 1).date()
    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    # Get transactions for the month
    # Use CSV transactions if available, otherwise fall back to database
    if csv_statement:
        transactions = []  # CSV statement already has transactions processed
    else:
        transactions = Transaction.objects.filter(
            stripe_created__gte=start_date,
            stripe_created__lte=end_date
        ).order_by('stripe_created')

        if account:
            transactions = transactions.filter(account=account)
    
    # Prepare month names (needed for descriptions)
    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    # Get or calculate opening balance
    opening_balance = 0

    # Use CSV statement data if available
    if csv_statement:
        # Convert from HKD to cents for consistency with database
        opening_balance = int(csv_statement.get('opening_balance', 0) * 100)
    else:
        try:
            previous_month = month - 1 if month > 1 else 12
            previous_year = year if month > 1 else year - 1

            prev_statement = MonthlyStatement.objects.filter(
                year=previous_year,
                month=previous_month
            )
            if account:
                prev_statement = prev_statement.filter(account=account)

            prev_statement = prev_statement.first()
            if prev_statement:
                opening_balance = prev_statement.closing_balance
        except:
            pass

    # Calculate totals and build statement lines (matching August format)
    total_charges = 0
    total_refunds = 0
    total_fees = 0
    total_payouts = 0
    running_balance = opening_balance

    # Reconciliation counters
    charge_count = 0
    refund_count = 0
    payout_reversal_count = 0
    payout_reversal_amount = 0

    statement_lines = []
    customer_transactions = []

    # Add opening balance line
    statement_lines.append({
        'date': datetime(year, month, 1),
        'nature': 'Opening Balance',
        'party': 'Brought Forward',
        'debit': 0,
        'credit': 0,
        'balance': opening_balance / 100,
        'acknowledged': 'Yes',
        'description': f'Opening balance for {month_names[month-1]} {year}',
        'is_opening': True,
    })

    # Use CSV transactions if available
    if csv_statement and csv_statement.get('transactions'):
        # Process CSV transactions
        for csv_tx in csv_statement['transactions']:
            debit = float(csv_tx.get('debit', 0))
            credit = float(csv_tx.get('credit', 0))

            # Update running balance (debits increase, credits decrease)
            running_balance += int((debit - credit) * 100)

            # Track totals
            if debit > 0 and csv_tx.get('nature', '').startswith('Gross'):
                total_charges += int(debit * 100)
                charge_count += 1

                # Track customer transaction for succeeded charges
                customer_transactions.append({
                    'date': csv_tx.get('date'),
                    'email': csv_tx.get('party', ''),
                    'amount': debit,
                    'stripe_id': csv_tx.get('stripe_id', ''),
                    'description': csv_tx.get('description', ''),
                })

            if credit > 0 and 'Fee' in csv_tx.get('nature', ''):
                total_fees += int(credit * 100)

            # Track refunds
            if 'Refund' in csv_tx.get('nature', ''):
                total_refunds += int(debit * 100)
                refund_count += 1

            # Track payout reversals (failed payouts)
            if 'Payout Failure' in csv_tx.get('nature', '') or 'Payout Reversal' in csv_tx.get('nature', ''):
                payout_reversal_amount += int(debit * 100)
                payout_reversal_count += 1

            # Track payouts
            if 'Payout' in csv_tx.get('nature', '') and credit > 0:
                total_payouts += int(credit * 100)

            statement_lines.append({
                'date': csv_tx.get('date'),
                'nature': csv_tx.get('nature', ''),
                'party': csv_tx.get('party', ''),
                'debit': debit,
                'credit': credit,
                'balance': running_balance / 100,
                'acknowledged': 'No',
                'description': csv_tx.get('description', ''),
            })
    else:
        # Use database transactions
        for txn in transactions:
            # Process each transaction with separate line for fees
            if txn.type == 'charge' and txn.status == 'succeeded':
                # Gross Payment line
                total_charges += txn.amount
                running_balance += txn.amount
                statement_lines.append({
                    'date': txn.stripe_created,
                    'nature': 'Gross Payment',
                    'party': txn.customer_email or 'Unknown',
                    'debit': txn.amount / 100,
                    'credit': 0,
                    'balance': running_balance / 100,
                    'acknowledged': 'No',
                    'description': txn.customer_email or '',
                })

                # Track customer transaction
                customer_transactions.append({
                    'date': txn.stripe_created,
                    'email': txn.customer_email,
                    'amount': txn.amount / 100,
                })

            elif txn.type == 'refund':
                total_refunds += txn.amount
                running_balance -= txn.amount
                statement_lines.append({
                    'date': txn.stripe_created,
                    'nature': 'Refund',
                    'party': 'Stripe',
                    'debit': 0,
                    'credit': txn.amount / 100,
                    'balance': running_balance / 100,
                    'acknowledged': 'No',
                    'description': f'Refund for {txn.stripe_id}',
                })

            elif txn.type == 'payout':
                total_payouts += txn.amount
                running_balance -= txn.amount
                statement_lines.append({
                    'date': txn.stripe_created,
                    'nature': 'Payout',
                    'party': 'Stripe',
                    'debit': 0,
                    'credit': txn.amount / 100,
                    'balance': running_balance / 100,
                    'acknowledged': 'No',
                    'description': 'BOC(HK)',
                })

            # Processing fee (if any) - separate line
            if txn.fee and txn.fee > 0:
                total_fees += txn.fee
                running_balance -= txn.fee
                statement_lines.append({
                    'date': txn.stripe_created,
                    'nature': 'Processing Fee',
                    'party': 'Stripe',
                    'debit': 0,
                    'credit': txn.fee / 100,
                    'balance': running_balance / 100,
                    'acknowledged': 'No',
                    'description': 'Stripe processing fee',
                })

    # Use CSV closing balance if available, otherwise use calculated running balance
    if csv_statement and 'closing_balance' in csv_statement:
        closing_balance = int(csv_statement.get('closing_balance', 0) * 100)
    else:
        closing_balance = running_balance

    # Add closing balance line
    statement_lines.append({
        'date': datetime(year, month, last_day),
        'nature': 'Closing Balance',
        'party': 'Carry Forward',
        'debit': 0,
        'credit': 0,
        'balance': closing_balance / 100,
        'acknowledged': 'Yes',
        'description': f'Closing balance for {month_names[month-1]} {year}',
        'is_closing': True,
    })

    # Calculate total credits (fees + refunds + payouts)
    total_credits = (total_fees + total_refunds + total_payouts) / 100

    # Calculate reconciliation values
    account_activity_before_fees = total_charges / 100
    net_balance_change = (total_charges - total_fees - total_refunds) / 100

    # Calculate what closing SHOULD be based on simple math
    calculated_closing = (opening_balance + total_charges - total_fees - total_refunds - total_payouts) / 100

    # Actual closing might differ due to payout reconciliation adjustments
    balance_change_expected = (closing_balance - opening_balance) / 100

    context = {
        'year': year,
        'month': month,
        'month_name': month_names[month - 1],
        'account': account,
        'accounts': StripeAccount.objects.filter(is_active=True),
        'statement_lines': statement_lines,
        'customer_transactions': customer_transactions,
        'opening_balance': opening_balance / 100,
        'closing_balance': closing_balance / 100,
        'total_charges': total_charges / 100,
        'total_refunds': total_refunds / 100,
        'total_fees': total_fees / 100,
        'total_payouts': total_payouts / 100,
        'total_credits': total_credits,  # Pre-calculated for correct decimal places
        'transaction_count': len(statement_lines) - 2,  # Exclude opening and closing balance rows
        'years': range(2021, datetime.now().year + 1),
        'months': range(1, 13),
        'month_names': month_names,
        # Reconciliation data
        'charge_count': charge_count,
        'refund_count': refund_count,
        'payout_reversal_count': payout_reversal_count,
        'payout_reversal_amount': payout_reversal_amount / 100,
        'account_activity_before_fees': account_activity_before_fees,
        'net_balance_change': net_balance_change,
        'balance_change_expected': balance_change_expected,
        'calculated_closing': calculated_closing,
    }

    return render(request, 'stripe_management/statement_generate.html', context)
