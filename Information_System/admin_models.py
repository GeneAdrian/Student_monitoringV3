# Information_System/admin_models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class Admin(models.Model):
    """Separate Admin model for authentication - NO student login capability"""
    
    # Authentication fields
    username = models.CharField(max_length=150, unique=True)
    # >>>>>>>>>>> WALA NA! EMAIL IS GONE! <<<<<<<<<<<
    password_hash = models.CharField(max_length=128)  # Store hashed password
    auth_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Personal info
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_picture = models.ImageField(upload_to='admin_profiles/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Admin specific
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Administrator'),
        ('faculty', 'Faculty'),
        ('program_chair', 'Program Chair'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='admin')
    department = models.CharField(max_length=100, blank=True)
    approved_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'admin_users'  # Separate table from auth_user
    
    def __str__(self):
        return f"{self.username} - {self.role}"
    
    def set_password(self, raw_password):
        """Hash and set password"""
        self.password_hash = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check password against hash"""
        return check_password(raw_password, self.password_hash)
    
    @property
    def is_authenticated(self):
        """Django compatibility property"""
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_full_name(self):
        """Return full name or username if not set"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username
    
    def get_role_display(self):
        """Get human-readable role name"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)


class AdminAuthorization(models.Model):
    """Model to store and validate admin authorization codes"""
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)
    created_by = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='created_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_codes')
    used_at = models.DateTimeField(null=True, blank=True)
    
    def is_valid(self):
        """Check if authorization code is still valid"""
        return not self.is_used and self.expires_at > timezone.now()
    
    def __str__(self):
        status = 'Valid' if self.is_valid() else 'Invalid'
        return f"{self.code} - {status}"
    
    class Meta:
        db_table = 'admin_authorizations'
        verbose_name_plural = "Admin Authorizations"


class AdminLoginHistory(models.Model):
    """Track admin login history for security"""
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_successful = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.admin.username} logged in at {self.login_time}"
    
    class Meta:
        db_table = 'admin_login_history'
        ordering = ['-login_time']
        verbose_name_plural = "Admin Login Histories"