"""
Health check views for load balancer and monitoring
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import time


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for Railway/load balancer.
    Returns 200 if the service is healthy, 503 if unhealthy.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check cache connection
    try:
        cache.set('health_check', 'ok', 10)
        cache_result = cache.get('health_check')
        if cache_result == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'error: cache read mismatch'
            # Don't mark unhealthy for cache issues in development
    except Exception as e:
        health_status['checks']['cache'] = f'error: {str(e)}'
        # Cache issues in development shouldn't fail health check
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check endpoint for Kubernetes/Railway.
    Checks if the application is ready to accept traffic.
    """
    return JsonResponse({
        'status': 'ready',
        'timestamp': time.time()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check endpoint for Kubernetes/Railway.
    Simple check to verify the application is running.
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': time.time()
    })
