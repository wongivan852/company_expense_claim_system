"""
Management command to set up Krystal Group companies.
"""

from django.core.management.base import BaseCommand
from apps.expense_claims.models import Company, Currency
from django.db import transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Set up Krystal Group companies'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Krystal Group companies...')
        
        with transaction.atomic():
            # Get or create HKD currency (most likely base currency)
            hkd, _ = Currency.objects.get_or_create(
                code='HKD',
                defaults={
                    'name': 'Hong Kong Dollar',
                    'symbol': 'HK$',
                    'is_active': True
                }
            )
            
            # Get or create CNY currency for the Chinese company
            cny, _ = Currency.objects.get_or_create(
                code='CNY',
                defaults={
                    'name': 'Chinese Yuan',
                    'symbol': '¥',
                    'is_active': True
                }
            )
            
            # Clear existing companies
            Company.objects.all().delete()
            
            # Create the four Krystal Group companies
            # Company data with your specified names only
        companies_data = [
            {
                'code': 'KI',
                'name': 'Krystal Institute Limited',
                'name_chinese': '',
                'base_currency': Currency.objects.get(code='HKD'),
                'approval_threshold': Decimal('10000.00'),
                'company_type': 'institute'
            },
            {
                'code': 'KT',
                'name': 'Krystal Technology Limited',
                'name_chinese': '',
                'base_currency': Currency.objects.get(code='HKD'),
                'approval_threshold': Decimal('15000.00'),
                'company_type': 'technology'
            },
            {
                'code': 'CGGE',
                'name': 'CG Global Entertainment Limited',
                'name_chinese': '',
                'base_currency': Currency.objects.get(code='HKD'),
                'approval_threshold': Decimal('20000.00'),
                'company_type': 'entertainment'
            },
            {
                'code': '数谱(深圳)',
                'name': '数谱环球(深圳)科技有限公司',
                'name_chinese': '',
                'base_currency': Currency.objects.get(code='CNY'),
                'approval_threshold': Decimal('50000.00'),
                'company_type': 'technology'
            }
        ]
        
        # Create companies
        created_count = 0
        for company_data in companies_data:
            company, created = Company.objects.get_or_create(
                code=company_data['code'],
                defaults=company_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created company: {company.name}')
                )
            else:
                # Update existing company
                for key, value in company_data.items():
                    setattr(company, key, value)
                company.save()
                self.stdout.write(
                    self.style.WARNING(f'Updated company: {company.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up {len(companies_data)} Krystal Group companies'
            )
        )
        
        # Display current companies
        current_companies = Company.objects.all()
        self.stdout.write('\nCurrent companies:')
        for company in current_companies:
            chinese_display = f' ({company.name_chinese})' if company.name_chinese else ''
            self.stdout.write(f'  - {company.code}: {company.name}{chinese_display}')
