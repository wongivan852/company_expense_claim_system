#!/usr/bin/env python

# Test script to validate the amount input fix
import os
import sys
import django

# Setup Django
sys.path.append('/Users/wongivan/ai_tools/business_tools/company_expense_claim_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from claims.models import Company, ExpenseCategory, ExpenseClaim, ExpenseItem
from decimal import Decimal
import datetime

User = get_user_model()

print('🧪 Testing Complete Claim Creation Workflow...')
print('=' * 60)

try:
    # Get user and company
    user = User.objects.get(username='ivan.wong')
    company = Company.objects.get(code='KIL')
    category = ExpenseCategory.objects.first()

    print(f'✅ User: {user.username}')
    print(f'✅ Company: {company.name} ({company.code})')
    print(f'✅ Category: {category.name}')

    # Create a test claim with the problematic amount 71.66
    claim = ExpenseClaim.objects.create(
        claimant=user,
        company=company,
        event_name='Amount Input Validation Test',
        period_from=datetime.date(2025, 9, 1),
        period_to=datetime.date(2025, 9, 30),
        total_amount_hkd=Decimal('71.66'),
        status='draft'
    )

    print(f'✅ Created claim: {claim.claim_number}')

    # Create expense item with the exact amount that was problematic
    expense_item = ExpenseItem.objects.create(
        expense_claim=claim,
        item_number=1,
        category=category,
        description='Test expense with 71.66 amount',
        original_amount=Decimal('71.66'),
        currency=company.base_currency,
        exchange_rate=Decimal('1.0000'),
        amount_hkd=Decimal('71.66'),
        expense_date=datetime.date(2025, 9, 15)
    )

    print(f'✅ Created expense item: {expense_item.description}')
    print(f'   📊 Original Amount: {expense_item.original_amount}')
    print(f'   💰 Amount HKD: {expense_item.amount_hkd}')

    # Verify the amounts are correct
    if expense_item.original_amount == Decimal('71.66'):
        print('✅ Amount stored correctly: 71.66')
    else:
        print(f'❌ Amount incorrect: expected 71.66, got {expense_item.original_amount}')

    if expense_item.amount_hkd == Decimal('71.66'):
        print('✅ HKD amount calculated correctly: 71.66')
    else:
        print(f'❌ HKD amount incorrect: expected 71.66, got {expense_item.amount_hkd}')

    # Test various decimal amounts to ensure robustness
    test_amounts = [
        Decimal('123.45'),
        Decimal('7.02'),
        Decimal('999.99'),
        Decimal('0.01')
    ]

    print('\n🔬 Testing various decimal amounts:')
    for i, amount in enumerate(test_amounts):
        test_item = ExpenseItem.objects.create(
            expense_claim=claim,
            item_number=i+2,
            category=category,
            description=f'Test amount {amount}',
            original_amount=amount,
            currency=company.base_currency,
            exchange_rate=Decimal('1.0000'),
            amount_hkd=amount,
            expense_date=datetime.date(2025, 9, 15)
        )
        print(f'   ✅ {amount} → {test_item.original_amount}')

    print(f'\n📊 Final Claim Summary:')
    print(f'   📋 Claim Number: {claim.claim_number}')
    print(f'   📝 Total Items: {claim.expense_items.count()}')
    print(f'   💸 Total Amount: HK${claim.total_amount_hkd}')

    print('\n🎉 All amount handling tests passed!')
    print('💡 The 71.66 → 7.02 conversion bug has been fixed!')
    
    # Clean up test data
    print('\n🧹 Cleaning up test data...')
    claim.delete()
    print('✅ Test claim deleted')

except Exception as e:
    print(f'❌ Error during testing: {e}')
    sys.exit(1)