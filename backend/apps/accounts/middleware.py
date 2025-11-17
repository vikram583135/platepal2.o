"""
Custom middleware for accounts app
"""
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.encoding import force_bytes
import hashlib
import json
import pickle
import base64

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
                if not request.user.is_authenticated and 'HTTP_AUTHORIZATION' not in request.META:
                    return JsonResponse({
                        'error': 'Unauthorized access'
                    }, status=401)
            else:
                return JsonResponse({
                    'error': 'Access denied'
                }, status=403)
        
        return None


class IdempotencyMiddleware(MiddlewareMixin):
    """
    Middleware to ensure idempotency for POST/PUT/PATCH requests.
    Uses Idempotency-Key header to cache responses and return them for duplicate requests.
    """
    
    IDEMPOTENCY_HEADER = 'Idempotency-Key'
    CACHE_PREFIX = 'idempotency:'
    CACHE_TTL = 24 * 60 * 60  # 24 hours
    
    def process_request(self, request):
        """Check for idempotency key and return cached response if exists"""
        # Only apply to state-changing methods
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return None
        
        # Skip for certain paths (health checks, admin, etc.)
        if request.path.startswith('/admin/') or request.path.startswith('/api/docs/'):
            return None
        
        # Get idempotency key from header
        idempotency_key = request.META.get(f'HTTP_{self.IDEMPOTENCY_HEADER.replace("-", "_").upper()}')
        
        if not idempotency_key:
            return None
        
        # Generate cache key (include user and method to prevent cross-user cache hits)
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        cache_key = f"{self.CACHE_PREFIX}{request.method}:{request.path}:{user_id}:{idempotency_key}"
        
        # Check if we have a cached response
        cached_response = cache.get(cache_key)
        
        if cached_response is not None:
            # Deserialize and return cached response
            try:
                response_data = pickle.loads(base64.b64decode(cached_response))
                
                # Create response object
                response = HttpResponse(
                    content=response_data['content'],
                    status=response_data['status'],
                    content_type=response_data.get('content_type', 'application/json')
                )
                
                # Set headers
                for header, value in response_data.get('headers', {}).items():
                    response[header] = value
                
                # Add idempotency indicator
                response['X-Idempotent-Replayed'] = 'true'
                
                return response
            except Exception as e:
                # If deserialization fails, continue with normal request
                pass
        
        # Store the idempotency key in request for later use
        request._idempotency_key = idempotency_key
        request._idempotency_cache_key = cache_key
        
        return None
    
    def process_response(self, request, response):
        """Cache successful responses for idempotency"""
        # Only cache if idempotency key was present and request was state-changing
        if not hasattr(request, '_idempotency_cache_key'):
            return response
        
        # Only cache successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            try:
                # Serialize response for caching
                response_data = {
                    'content': response.content,
                    'status': response.status_code,
                    'content_type': response.get('Content-Type', 'application/json'),
                    'headers': dict(response.items())
                }
                
                # Cache the serialized response
                cached_value = base64.b64encode(pickle.dumps(response_data)).decode('utf-8')
                cache.set(request._idempotency_cache_key, cached_value, self.CACHE_TTL)
                
                # Add idempotency indicator
                response['X-Idempotent-Key'] = request._idempotency_key
            except Exception as e:
                # If caching fails, log but don't break the request
                pass
        
        return response
