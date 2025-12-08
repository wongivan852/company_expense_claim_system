"""
Performance monitoring utilities for the expense claim system.

This module provides real-time performance monitoring, metrics collection,
and system health checks.
"""

import time
import psutil
import logging
from functools import wraps
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Real-time performance monitoring system."""
    
    def __init__(self):
        self.metrics = {
            'response_times': deque(maxlen=1000),
            'database_queries': deque(maxlen=1000),
            'cache_operations': deque(maxlen=1000),
            'error_counts': defaultdict(int),
            'request_counts': defaultdict(int),
        }
        self.lock = threading.Lock()
    
    def log_response_time(self, view_name, duration, status_code):
        """Log response time for a view."""
        with self.lock:
            self.metrics['response_times'].append({
                'view': view_name,
                'duration': duration,
                'status': status_code,
                'timestamp': timezone.now().timestamp()
            })
            
            if status_code >= 400:
                self.metrics['error_counts'][f"{status_code}"] += 1
            
            self.metrics['request_counts'][view_name] += 1
    
    def log_database_query(self, query_time, query_count):
        """Log database query performance."""
        with self.lock:
            self.metrics['database_queries'].append({
                'query_time': query_time,
                'query_count': query_count,
                'timestamp': timezone.now().timestamp()
            })
    
    def log_cache_operation(self, operation, hit, duration):
        """Log cache operation."""
        with self.lock:
            self.metrics['cache_operations'].append({
                'operation': operation,
                'hit': hit,
                'duration': duration,
                'timestamp': timezone.now().timestamp()
            })
    
    def get_metrics_summary(self, last_minutes=5):
        """Get performance metrics summary for the last N minutes."""
        cutoff_time = timezone.now().timestamp() - (last_minutes * 60)
        
        with self.lock:
            # Response time metrics
            recent_responses = [
                r for r in self.metrics['response_times'] 
                if r['timestamp'] > cutoff_time
            ]
            
            # Database query metrics
            recent_queries = [
                q for q in self.metrics['database_queries']
                if q['timestamp'] > cutoff_time
            ]
            
            # Cache metrics
            recent_cache = [
                c for c in self.metrics['cache_operations']
                if c['timestamp'] > cutoff_time
            ]
        
        # Calculate statistics
        response_times = [r['duration'] for r in recent_responses]
        query_times = [q['query_time'] for q in recent_queries]
        cache_hits = [c for c in recent_cache if c['hit']]
        
        return {
            'period_minutes': last_minutes,
            'response_times': {
                'count': len(response_times),
                'avg': sum(response_times) / len(response_times) if response_times else 0,
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0,
                'p95': self._percentile(response_times, 95) if response_times else 0,
            },
            'database': {
                'query_count': sum(q['query_count'] for q in recent_queries),
                'avg_query_time': sum(query_times) / len(query_times) if query_times else 0,
            },
            'cache': {
                'operations': len(recent_cache),
                'hit_rate': len(cache_hits) / len(recent_cache) * 100 if recent_cache else 0,
            },
            'errors': dict(self.metrics['error_counts']),
            'requests_by_view': dict(self.metrics['request_counts']),
        }
    
    def _percentile(self, data, percentile):
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            if upper_index >= len(sorted_data):
                return sorted_data[-1]
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(view_name=None):
    """Decorator to monitor view performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            initial_query_count = len(connection.queries)
            
            try:
                response = func(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
            except Exception as e:
                status_code = 500
                logger.error(f"Error in {func.__name__}: {e}")
                raise
            finally:
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # Convert to milliseconds
                query_count = len(connection.queries) - initial_query_count
                
                view_name_actual = view_name or func.__name__
                performance_monitor.log_response_time(view_name_actual, duration, status_code)
                performance_monitor.log_database_query(duration, query_count)
                
                # Log slow operations
                if duration > 1000:  # Slower than 1 second
                    logger.warning(f"Slow operation: {view_name_actual} took {duration:.2f}ms with {query_count} queries")
            
            return response
        
        return wrapper
    return decorator


def monitor_cache_operation(operation_name):
    """Decorator to monitor cache operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                hit = result is not None
            except Exception:
                hit = False
                raise
            finally:
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                performance_monitor.log_cache_operation(operation_name, hit, duration)
            
            return result
        
        return wrapper
    return decorator


class SystemHealthChecker:
    """System health monitoring."""
    
    @staticmethod
    def check_database_health():
        """Check database connection and performance."""
        try:
            start_time = time.time()
            
            # Simple query to test connection
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            query_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': query_time,
                'connection_queries': len(connection.queries)
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': None
            }
    
    @staticmethod
    def check_cache_health():
        """Check Redis cache connection."""
        try:
            start_time = time.time()
            
            # Test cache operation
            test_key = 'health_check_test'
            cache.set(test_key, 'test_value', 60)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            cache_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy' if retrieved_value == 'test_value' else 'unhealthy',
                'response_time_ms': cache_time,
                'test_successful': retrieved_value == 'test_value'
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': None
            }
    
    @staticmethod
    def get_system_resources():
        """Get current system resource usage."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk_usage = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                },
                'disk': {
                    'total': disk_usage.total,
                    'used': disk_usage.used,
                    'free': disk_usage.free,
                    'percent': disk_usage.percent,
                }
            }
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                'error': str(e)
            }
    
    @classmethod
    def get_full_health_report(cls):
        """Get comprehensive system health report."""
        return {
            'timestamp': timezone.now().isoformat(),
            'database': cls.check_database_health(),
            'cache': cls.check_cache_health(),
            'system': cls.get_system_resources(),
            'performance': performance_monitor.get_metrics_summary(5),
        }


# Django views for monitoring
@user_passes_test(lambda u: u.is_staff)
def health_check(request):
    """Health check endpoint for monitoring systems."""
    health_report = SystemHealthChecker.get_full_health_report()
    
    # Determine overall status
    overall_status = 'healthy'
    if health_report['database']['status'] == 'unhealthy':
        overall_status = 'unhealthy'
    elif health_report['cache']['status'] == 'unhealthy':
        overall_status = 'degraded'
    
    health_report['overall_status'] = overall_status
    
    status_code = 200 if overall_status == 'healthy' else 503
    return JsonResponse(health_report, status=status_code)


@user_passes_test(lambda u: u.is_staff)
def performance_metrics(request):
    """Get performance metrics."""
    minutes = int(request.GET.get('minutes', 5))
    metrics = performance_monitor.get_metrics_summary(minutes)
    
    return JsonResponse(metrics)


@user_passes_test(lambda u: u.is_staff)  
def system_info(request):
    """Get detailed system information."""
    import platform
    import django
    
    info = {
        'timestamp': timezone.now().isoformat(),
        'system': {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'django_version': django.get_version(),
        },
        'database': {
            'engine': settings.DATABASES['default']['ENGINE'],
            'name': settings.DATABASES['default']['NAME'],
        },
        'cache': {
            'backend': settings.CACHES['default']['BACKEND'],
            'location': settings.CACHES['default'].get('LOCATION', 'N/A'),
        },
        'settings': {
            'debug': settings.DEBUG,
            'allowed_hosts': settings.ALLOWED_HOSTS,
            'time_zone': settings.TIME_ZONE,
        }
    }
    
    return JsonResponse(info)


class DatabaseQueryAnalyzer:
    """Analyze database queries for optimization opportunities."""
    
    @staticmethod
    def get_slow_queries(min_duration_ms=100):
        """Get queries that took longer than specified duration."""
        # This would typically integrate with Django Debug Toolbar
        # or a custom query logger
        pass
    
    @staticmethod
    def get_duplicate_queries():
        """Find duplicate queries that could be optimized with caching."""
        pass
    
    @staticmethod
    def analyze_n_plus_one():
        """Detect N+1 query problems."""
        pass


# Middleware for automatic performance monitoring
class PerformanceMonitoringMiddleware:
    """Middleware to automatically monitor all requests."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        initial_query_count = len(connection.queries)
        
        response = self.get_response(request)
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        query_count = len(connection.queries) - initial_query_count
        
        view_name = request.resolver_match.view_name if request.resolver_match else 'unknown'
        
        performance_monitor.log_response_time(view_name, duration, response.status_code)
        performance_monitor.log_database_query(duration, query_count)
        
        # Add performance headers in debug mode
        if settings.DEBUG:
            response['X-Response-Time'] = f"{duration:.2f}ms"
            response['X-Query-Count'] = str(query_count)
        
        return response


# Alert system for performance issues
class PerformanceAlerter:
    """Alert system for performance issues."""
    
    THRESHOLDS = {
        'slow_response_time': 2000,  # 2 seconds
        'high_query_count': 20,      # 20+ queries per request
        'high_error_rate': 5,        # 5% error rate
        'high_memory_usage': 85,     # 85% memory usage
        'high_cpu_usage': 80,        # 80% CPU usage
    }
    
    @classmethod
    def check_alerts(cls):
        """Check for performance issues and generate alerts."""
        alerts = []
        
        # Get recent metrics
        metrics = performance_monitor.get_metrics_summary(5)
        health = SystemHealthChecker.get_full_health_report()
        
        # Check response time
        if metrics['response_times']['avg'] > cls.THRESHOLDS['slow_response_time']:
            alerts.append({
                'type': 'slow_response_time',
                'message': f"Average response time is {metrics['response_times']['avg']:.2f}ms",
                'severity': 'warning'
            })
        
        # Check query count
        if metrics['database']['query_count'] > cls.THRESHOLDS['high_query_count']:
            alerts.append({
                'type': 'high_query_count',
                'message': f"High database query count: {metrics['database']['query_count']}",
                'severity': 'warning'
            })
        
        # Check system resources
        if 'system' in health and 'memory' in health['system']:
            memory_percent = health['system']['memory']['percent']
            if memory_percent > cls.THRESHOLDS['high_memory_usage']:
                alerts.append({
                    'type': 'high_memory_usage',
                    'message': f"High memory usage: {memory_percent}%",
                    'severity': 'critical'
                })
        
        return alerts