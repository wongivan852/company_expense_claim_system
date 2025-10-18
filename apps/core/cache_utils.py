"""
Caching utilities for performance optimization.

This module provides multi-level caching strategies for the expense claim system,
including Redis-backed caching for frequently accessed data.
"""

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class ExpenseSystemCache:
    """Centralized caching management for the expense system."""
    
    # Cache timeout constants (in seconds)
    USER_PERMISSIONS = 3600      # 1 hour
    CATEGORY_LIST = 86400        # 24 hours  
    CURRENCY_RATES = 1800        # 30 minutes
    DASHBOARD_DATA = 300         # 5 minutes
    COMPANY_LIST = 43200         # 12 hours
    EXCHANGE_RATES = 3600        # 1 hour
    
    # Cache key prefixes
    PREFIX_USER_PERMS = 'user_permissions'
    PREFIX_CATEGORIES = 'expense_categories'
    PREFIX_CURRENCIES = 'currencies'
    PREFIX_COMPANIES = 'companies'
    PREFIX_EXCHANGE_RATES = 'exchange_rates'
    PREFIX_DASHBOARD = 'user_dashboard'
    PREFIX_CLAIM_DETAILS = 'claim_details'
    
    @classmethod
    def get_cache_key(cls, prefix, *args):
        """Generate standardized cache key."""
        key_parts = [prefix] + [str(arg) for arg in args]
        return '_'.join(key_parts)
    
    @classmethod
    def get_user_permissions(cls, user_id):
        """Cache user permissions and capabilities."""
        cache_key = cls.get_cache_key(cls.PREFIX_USER_PERMS, user_id)
        permissions = cache.get(cache_key)
        
        if permissions is None:
            try:
                from accounts.models import User
                user = User.objects.select_related('profile').get(id=user_id)
                
                permissions = {
                    'can_approve': user.has_perm('expense_claims.can_approve_claims'),
                    'can_view_all': user.has_perm('expense_claims.can_view_all_claims'),
                    'is_manager': getattr(user, 'is_manager', False),
                    'role': getattr(user, 'role', 'employee'),
                    'department': getattr(user, 'department', ''),
                }
                
                cache.set(cache_key, permissions, cls.USER_PERMISSIONS)
                logger.info(f"Cached permissions for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error caching user permissions for {user_id}: {e}")
                permissions = {}
        
        return permissions
    
    @classmethod
    def get_active_categories(cls):
        """Cache active expense categories."""
        cache_key = cls.get_cache_key(cls.PREFIX_CATEGORIES, 'active')
        categories = cache.get(cache_key)
        
        if categories is None:
            try:
                from apps.expense_claims.models import ExpenseCategory
                categories = list(
                    ExpenseCategory.objects.filter(is_active=True)
                    .values('id', 'name', 'name_chinese', 'requires_receipt')
                    .order_by('name')
                )
                
                cache.set(cache_key, categories, cls.CATEGORY_LIST)
                logger.info(f"Cached {len(categories)} expense categories")
                
            except Exception as e:
                logger.error(f"Error caching categories: {e}")
                categories = []
        
        return categories
    
    @classmethod
    def get_active_currencies(cls):
        """Cache active currencies."""
        cache_key = cls.get_cache_key(cls.PREFIX_CURRENCIES, 'active')
        currencies = cache.get(cache_key)
        
        if currencies is None:
            try:
                from apps.expense_claims.models import Currency
                currencies = list(
                    Currency.objects.filter(is_active=True)
                    .values('id', 'code', 'name', 'symbol', 'is_base_currency')
                    .order_by('name')
                )
                
                cache.set(cache_key, currencies, cls.CATEGORY_LIST)
                logger.info(f"Cached {len(currencies)} currencies")
                
            except Exception as e:
                logger.error(f"Error caching currencies: {e}")
                currencies = []
        
        return currencies
    
    @classmethod
    def get_active_companies(cls):
        """Cache active companies."""
        cache_key = cls.get_cache_key(cls.PREFIX_COMPANIES, 'active')
        companies = cache.get(cache_key)
        
        if companies is None:
            try:
                from apps.expense_claims.models import Company
                companies = list(
                    Company.objects.filter(is_active=True)
                    .values('id', 'name', 'code')
                    .order_by('name')
                )
                
                cache.set(cache_key, companies, cls.COMPANY_LIST)
                logger.info(f"Cached {len(companies)} companies")
                
            except Exception as e:
                logger.error(f"Error caching companies: {e}")
                companies = []
        
        return companies
    
    @classmethod
    def get_exchange_rates(cls, date=None):
        """Cache exchange rates for a specific date."""
        if not date:
            date = timezone.now().date()
        
        cache_key = cls.get_cache_key(cls.PREFIX_EXCHANGE_RATES, date.isoformat())
        rates = cache.get(cache_key)
        
        if rates is None:
            try:
                from apps.expense_claims.models import Currency, ExchangeRate
                rates = {}
                
                for currency in Currency.objects.filter(is_active=True):
                    latest_rate = currency.exchange_rates.filter(
                        effective_date__lte=date
                    ).order_by('-effective_date').first()
                    
                    if latest_rate:
                        rates[currency.code] = {
                            'rate': float(latest_rate.rate_to_base),
                            'effective_date': latest_rate.effective_date.isoformat(),
                            'source': latest_rate.source
                        }
                
                cache.set(cache_key, rates, cls.EXCHANGE_RATES)
                logger.info(f"Cached exchange rates for {date}")
                
            except Exception as e:
                logger.error(f"Error caching exchange rates for {date}: {e}")
                rates = {}
        
        return rates
    
    @classmethod
    def get_dashboard_data(cls, user_id, role='employee'):
        """Cache dashboard data for a user."""
        cache_key = cls.get_cache_key(cls.PREFIX_DASHBOARD, user_id, role)
        dashboard_data = cache.get(cache_key)
        
        if dashboard_data is None:
            try:
                from apps.expense_claims.models import ExpenseClaim
                from django.db.models import Count, Sum
                
                if role in ['manager', 'admin']:
                    # Manager/Admin dashboard data
                    pending_claims = ExpenseClaim.objects.filter(
                        status__in=['submitted', 'under_review']
                    ).count()
                    
                    monthly_stats = ExpenseClaim.objects.filter(
                        created_at__month=timezone.now().month,
                        status='approved'
                    ).aggregate(
                        total_amount=Sum('total_amount_hkd'),
                        claim_count=Count('id')
                    )
                else:
                    # Employee dashboard data
                    user_claims = ExpenseClaim.objects.filter(claimant_id=user_id)
                    pending_claims = user_claims.filter(
                        status__in=['draft', 'submitted', 'under_review']
                    ).count()
                    
                    monthly_stats = user_claims.filter(
                        created_at__month=timezone.now().month
                    ).aggregate(
                        total_amount=Sum('total_amount_hkd'),
                        claim_count=Count('id')
                    )
                
                dashboard_data = {
                    'pending_claims': pending_claims,
                    'monthly_total': monthly_stats.get('total_amount') or 0,
                    'monthly_count': monthly_stats.get('claim_count') or 0,
                    'last_updated': timezone.now().isoformat()
                }
                
                cache.set(cache_key, dashboard_data, cls.DASHBOARD_DATA)
                logger.info(f"Cached dashboard data for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error caching dashboard data for user {user_id}: {e}")
                dashboard_data = {}
        
        return dashboard_data
    
    @classmethod
    def invalidate_user_cache(cls, user_id):
        """Invalidate all cache entries for a user."""
        cache_keys = [
            cls.get_cache_key(cls.PREFIX_USER_PERMS, user_id),
            cls.get_cache_key(cls.PREFIX_DASHBOARD, user_id, 'employee'),
            cls.get_cache_key(cls.PREFIX_DASHBOARD, user_id, 'manager'),
            cls.get_cache_key(cls.PREFIX_DASHBOARD, user_id, 'admin'),
        ]
        
        cache.delete_many(cache_keys)
        logger.info(f"Invalidated cache for user {user_id}")
    
    @classmethod
    def invalidate_claim_related_cache(cls):
        """Invalidate cache when claims are modified."""
        # This could be expanded to be more specific
        cache_patterns = [
            f"{cls.PREFIX_DASHBOARD}_*",
            f"{cls.PREFIX_CATEGORIES}_*",
        ]
        
        # Note: Django cache doesn't support pattern deletion by default
        # For production, consider using Redis directly for pattern deletion
        logger.info("Claim-related cache invalidation triggered")
    
    @classmethod
    def warm_cache(cls):
        """Pre-warm frequently accessed cache entries."""
        try:
            # Warm up static data
            cls.get_active_categories()
            cls.get_active_currencies() 
            cls.get_active_companies()
            cls.get_exchange_rates()
            
            logger.info("Cache warming completed successfully")
            
        except Exception as e:
            logger.error(f"Error during cache warming: {e}")


def cache_result(timeout=3600, key_prefix=''):
    """
    Decorator for caching function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}_{func.__name__}"
            if args:
                cache_key += "_" + "_".join(str(arg) for arg in args)
            if kwargs:
                cache_key += "_" + "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
            
            # Try to get from cache
            result = cache.get(cache_key)
            
            if result is None:
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
                logger.debug(f"Cached result for {func.__name__}")
            else:
                logger.debug(f"Cache hit for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


def clear_user_cache_on_update(user_id):
    """Clear user-specific cache when user data is updated."""
    ExpenseSystemCache.invalidate_user_cache(user_id)


def get_or_set_cache(cache_key, callable_func, timeout=3600):
    """
    Get from cache or set if not exists.
    
    Args:
        cache_key: The cache key
        callable_func: Function to call if cache miss
        timeout: Cache timeout in seconds
    """
    result = cache.get(cache_key)
    
    if result is None:
        result = callable_func()
        cache.set(cache_key, result, timeout)
    
    return result