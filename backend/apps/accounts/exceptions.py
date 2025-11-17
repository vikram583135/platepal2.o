"""
Custom exception handlers
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import traceback


def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses"""
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standard DRF exception - format it
        custom_response_data = {
            'error': str(exc),
            'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
        }
        response.data = custom_response_data
    else:
        # Non-DRF exception (like TypeError, AttributeError, etc.)
        # Return JSON error instead of HTML
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        
        error_message = str(exc)
        # Try to extract more useful error info
        error_type = type(exc).__name__
        
        custom_response_data = {
            'error': f'{error_type}: {error_message}',
            'details': {
                'type': error_type,
                'message': error_message
            }
        }
        response = Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response

