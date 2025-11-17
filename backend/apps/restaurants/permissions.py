"""
Restaurant permissions
"""
from rest_framework import permissions


class IsRestaurantOwner(permissions.BasePermission):
    """Permission for restaurant owners"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'RESTAURANT' or request.user.role == 'ADMIN'
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.owner == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'menu'):
            return obj.menu.restaurant.owner == request.user
        if hasattr(obj, 'category'):
            return obj.category.menu.restaurant.owner == request.user
        if hasattr(obj, 'menu_item'):
            return obj.menu_item.category.menu.restaurant.owner == request.user
        
        return False

