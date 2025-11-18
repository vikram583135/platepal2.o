"""
Utility functions for admin panel
"""
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError


def validate_query_param(param_value, param_name, param_type=str, required=False, choices=None, min_value=None, max_value=None):
    """
    Validate query parameter
    
    Args:
        param_value: The value to validate
        param_name: Name of the parameter (for error messages)
        param_type: Expected type (str, int, float, bool)
        required: Whether parameter is required
        choices: List of valid choices (for str/enum types)
        min_value: Minimum value (for numeric types)
        max_value: Maximum value (for numeric types)
    
    Returns:
        Validated value
    
    Raises:
        ValidationError: If validation fails
    """
    if param_value is None:
        if required:
            raise ValidationError(f"{param_name} is required")
        return None
    
    # Type conversion
    try:
        if param_type == bool:
            if isinstance(param_value, str):
                param_value = param_value.lower() in ('true', '1', 'yes', 'on')
            else:
                param_value = bool(param_value)
        elif param_type == int:
            param_value = int(param_value)
        elif param_type == float:
            param_value = float(param_value)
        elif param_type == str:
            param_value = str(param_value).strip()
            if not param_value and required:
                raise ValidationError(f"{param_name} cannot be empty")
    except (ValueError, TypeError) as e:
        raise ValidationError(f"{param_name} must be of type {param_type.__name__}: {str(e)}")
    
    # Choices validation
    if choices and param_value not in choices:
        raise ValidationError(f"{param_name} must be one of: {', '.join(map(str, choices))}")
    
    # Range validation
    if param_type in (int, float):
        if min_value is not None and param_value < min_value:
            raise ValidationError(f"{param_name} must be >= {min_value}")
        if max_value is not None and param_value > max_value:
            raise ValidationError(f"{param_name} must be <= {max_value}")
    
    return param_value


def validate_query_params(request, validations):
    """
    Validate multiple query parameters
    
    Args:
        request: DRF request object
        validations: Dict of {param_name: {param_type, required, choices, min_value, max_value}}
    
    Returns:
        Dict of validated parameters
    
    Raises:
        Response with 400 status if validation fails
    """
    validated = {}
    errors = {}
    
    for param_name, validation_config in validations.items():
        param_value = request.query_params.get(param_name)
        try:
            validated_value = validate_query_param(
                param_value,
                param_name,
                param_type=validation_config.get('type', str),
                required=validation_config.get('required', False),
                choices=validation_config.get('choices'),
                min_value=validation_config.get('min_value'),
                max_value=validation_config.get('max_value'),
            )
            if validated_value is not None:
                validated[param_name] = validated_value
        except ValidationError as e:
            errors[param_name] = str(e)
    
    if errors:
        return Response(
            {'errors': errors, 'message': 'Invalid query parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return validated

