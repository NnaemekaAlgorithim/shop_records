from rest_framework.permissions import BasePermission

class IsStaffOrSuperUser(BasePermission):
    """
    Custom permission to allow only staff users or superusers to access the endpoint.
    """
    message = "You must be a staff member or superuser to access this endpoint."

    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser
