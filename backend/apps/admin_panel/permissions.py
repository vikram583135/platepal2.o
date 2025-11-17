"""
Custom permissions for admin app
"""
from rest_framework import permissions
from .models import AdminUser, RolePermission, Permission


class IsAdminUser(permissions.BasePermission):
    """Check if user is an admin"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'ADMIN' or request.user.is_staff


class HasAdminPermission(permissions.BasePermission):
    """Check if user has specific permission"""
    
    def __init__(self, permission_codename=None, resource_type=None, action=None):
        self.permission_codename = permission_codename
        self.resource_type = resource_type
        self.action = action
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is admin
        try:
            admin_user = AdminUser.objects.get(user=request.user, is_active=True)
        except AdminUser.DoesNotExist:
            return False
        
        # Get user's role
        if not admin_user.role:
            return False
        
        # Build permission lookup
        if self.permission_codename:
            perm_filter = {'permission__codename': self.permission_codename}
        elif self.resource_type and self.action:
            perm_filter = {
                'permission__resource_type': self.resource_type,
                'permission__action': self.action
            }
        else:
            return False
        
        # Check role permissions
        has_perm = RolePermission.objects.filter(
            role=admin_user.role,
            **perm_filter
        ).exists()
        
        return has_perm


class HasResourcePermission(permissions.BasePermission):
    """Check resource-level permission"""
    
    def __init__(self, permission_codename, resource_id_field='pk'):
        self.permission_codename = permission_codename
        self.resource_id_field = resource_id_field
    
    def has_permission(self, request, view):
        return HasAdminPermission(permission_codename=self.permission_codename).has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        try:
            admin_user = AdminUser.objects.get(user=request.user, is_active=True)
        except AdminUser.DoesNotExist:
            return False
        
        if not admin_user.role:
            return False
        
        # Get resource ID
        resource_id = str(getattr(obj, self.resource_id_field, ''))
        
        # Check resource-level permission
        has_perm = RolePermission.objects.filter(
            role=admin_user.role,
            permission__codename=self.permission_codename,
            resource_id=resource_id
        ).exists()
        
        # If no resource-level permission, check general permission
        if not has_perm:
            has_perm = RolePermission.objects.filter(
                role=admin_user.role,
                permission__codename=self.permission_codename,
                resource_id=''
            ).exists()
        
        return has_perm


def require_permission(permission_codename):
    """Decorator to require specific permission"""
    def decorator(func):
        func.permission_codename = permission_codename
        return func
    return decorator

