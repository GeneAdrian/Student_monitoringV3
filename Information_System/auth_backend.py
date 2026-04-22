# Information_System/auth_backend.py
from django.contrib.auth.backends import BaseBackend
from .admin_models import Admin

class AdminAuthBackend(BaseBackend):
    """
    Custom authentication backend for Admin model only.
    This allows admins to login using the Admin model instead of Django's User model.
    """
    
    def authenticate(self, request, username=None, password=None):
        """
        Authenticate an admin using username and password.
        Returns the Admin object if credentials are valid, None otherwise.
        """
        try:
            # Try to find the admin by username
            admin = Admin.objects.get(username=username)
            
            # Check if admin is active and password is correct
            if admin.is_active and admin.check_password(password):
                return admin
            else:
                return None
                
        except Admin.DoesNotExist:
            # Try to find by email if username not found
            try:
                admin = Admin.objects.get(email=username)
                if admin.is_active and admin.check_password(password):
                    return admin
                else:
                    return None
            except Admin.DoesNotExist:
                return None
    
    def get_user(self, user_id):
        """
        Get an Admin object by ID.
        Used by Django to retrieve the user from the session.
        """
        try:
            return Admin.objects.get(pk=user_id)
        except Admin.DoesNotExist:
            return None
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Simplified permission check.
        For now, return True for active admins.
        You can expand this later for more granular permissions.
        """
        if not user_obj or not user_obj.is_active:
            return False
        
        # Super admins have all permissions
        if user_obj.is_superuser:
            return True
        
        # Add custom permission logic here if needed
        return True
    
    def has_module_perms(self, user_obj, app_label):
        """
        Check if user has permissions for a specific app.
        """
        if not user_obj or not user_obj.is_active:
            return False
        
        # Super admins have all module permissions
        if user_obj.is_superuser:
            return True
        
        # Add custom module permission logic here if needed
        return True