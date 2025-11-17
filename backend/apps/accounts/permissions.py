"""
Custom permissions
"""
from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to allow owners or admins"""
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.role == 'ADMIN':
            return True
        
        # Check if user owns the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsRestaurantOwner(permissions.BasePermission):
    """Permission for restaurant owners"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'RESTAURANT'
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.owner == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class IsDeliveryRider(permissions.BasePermission):
    """Permission for delivery riders"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'DELIVERY'


class IsCustomer(permissions.BasePermission):
    """Permission for customers"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'CUSTOMER'

