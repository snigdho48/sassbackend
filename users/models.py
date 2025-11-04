from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Custom user model with role-based access control."""
    
    class UserRole(models.TextChoices):
        SUPER_ADMIN = 'super_admin', _('Super Administrator')
        ADMIN = 'admin', _('Administrator')
        GENERAL_USER = 'general_user', _('General User')
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.GENERAL_USER,
    )
    company = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    # Every user must refer to an admin (except Super Admin)
    assigned_admin = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_users',
        limit_choices_to={'role__in': [UserRole.ADMIN, UserRole.SUPER_ADMIN]},
        help_text='Admin user this user is assigned to'
    )
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email
    
    @property
    def is_super_admin(self):
        """Super Admin: Can create Admin Users, General Users, Plants."""
        return self.role == self.UserRole.SUPER_ADMIN or self.is_superuser
    
    @property
    def is_admin(self):
        """Admin User: Cannot create Plants, Can add General Users, Cannot change Target Range."""
        return self.role == self.UserRole.ADMIN or self.role == self.UserRole.SUPER_ADMIN
    
    @property
    def is_general_user(self):
        """General User: Can only input Cooling & Boiler data for assigned plant(s)."""
        return self.role == self.UserRole.GENERAL_USER

    @property
    def can_create_plants(self):
        """Only Super Admin can create plants."""
        # Check role directly, not is_super_admin (which includes Django is_superuser)
        return self.role == self.UserRole.SUPER_ADMIN
    
    @property
    def can_create_admin_users(self):
        """Only Super Admin can create Admin Users."""
        # Check role directly, not is_super_admin (which includes Django is_superuser)
        return self.role == self.UserRole.SUPER_ADMIN
    
    @property
    def can_create_general_users(self):
        """Super Admin and Admin can create General Users."""
        return self.role == self.UserRole.SUPER_ADMIN or self.role == self.UserRole.ADMIN
    
    @property
    def can_change_target_range(self):
        """Only Super Admin can change target ranges (plant parameters)."""
        # Check role directly, not is_super_admin (which includes Django is_superuser)
        return self.role == self.UserRole.SUPER_ADMIN
    
    @property
    def can_edit_data(self):
        """General Users can only edit data for their assigned plants."""
        if self.is_general_user:
            # This will be checked at the view level for assigned plants
            return False
        return self.role == self.UserRole.SUPER_ADMIN

    @property
    def can_view_reports(self):
        return True

    @property
    def can_manage_users(self):
        """Super Admin and Admin can manage users."""
        return self.is_super_admin or (self.role == self.UserRole.ADMIN)

    @property
    def can_access_admin_panel(self):
        return self.is_super_admin or self.role == self.UserRole.ADMIN

    @property
    def can_generate_reports(self):
        return self.role in [self.UserRole.ADMIN, self.UserRole.SUPER_ADMIN, self.UserRole.MANAGER, self.UserRole.CLIENT]

    @property
    def can_export_data(self):
        return self.role in [self.UserRole.ADMIN, self.UserRole.SUPER_ADMIN, self.UserRole.MANAGER, self.UserRole.CLIENT]

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0] 