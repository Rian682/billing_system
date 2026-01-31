from rest_framework import permissions

#Things only manager can view
class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'
    
#Things both staff and manager can access
class IsStaffOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['staff', 'manager']

#Things both can view but only manager can modify
class ManagerCanEditDeleteOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
    
        return request.user.is_authenticated and request.user.role == 'manager'