"""
Custom middleware for accounts app
"""
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
import hashlib
import json

class AuditLogMiddleware(MiddlewareMixin):
    """Log user actions for audit trail"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Log important actions (in production, use proper logging)
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                # Store audit log (simplified - in production, use database)
                pass
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware to prevent abuse"""
    
    def process_request(self, request):
        # Skip rate limiting for admin users
        if request.user.is_authenticated and request.user.role == 'ADMIN':
            return None
        
        # Get client identifier
        if request.user.is_authenticated:
            identifier = f"user_{request.user.id}"
        else:
            ip = self.get_client_ip(request)
            identifier = f"ip_{ip}"
        
        # Rate limit key
        key = f"ratelimit_{identifier}"
        
        # Get current count
        count = cache.get(key, 0)
        
        # Check limit (100 requests per minute for authenticated, 30 for anonymous)
        limit = 100 if request.user.is_authenticated else 30
        
        if count >= limit:
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.'
            }, status=429)
        
        # Increment counter
        cache.set(key, count + 1, 60)  # 60 seconds
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BotDetectionMiddleware(MiddlewareMixin):
    """Detect and block bot traffic"""
    
    def process_request(self, request):
        # Skip for admin
        if request.user.is_authenticated and request.user.role == 'ADMIN':
            return None
        
        # Check user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Known bot user agents
        bot_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'scrapy', 'go-http-client'
        ]
        
        # Check if user agent matches bot patterns
        is_bot = any(pattern in user_agent for pattern in bot_patterns)
        
        # Check for missing common headers
        has_accept = 'HTTP_ACCEPT' in request.META
        has_accept_language = 'HTTP_ACCEPT_LANGUAGE' in request.META
        
        # If looks like bot and missing headers, block
        if is_bot and not (has_accept and has_accept_language):
            # Allow for API endpoints (they might be legitimate)
            if request.path.startswith('/api/'):
                # Check for API key or authentication
                if not request.user.is_authenticated and 'Authorization' not in request.META:
                    return JsonResponse({
                        'error': 'Unauthorized access'
                    }, status=401)
            else:
                return JsonResponse({
                    'error': 'Access denied'
                }, status=403)
        
        return None
