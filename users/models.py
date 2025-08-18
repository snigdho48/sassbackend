from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Custom user model with role-based access control."""
    
    class UserRole(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        CLIENT = 'client', _('Client')
        MANAGER = 'manager', _('Manager')
        OPERATOR = 'operator', _('Operator')
        VIEWER = 'viewer', _('Viewer')
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CLIENT,
    )
    company = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
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
    def is_admin(self):
        return self.role == self.UserRole.ADMIN

    @property
    def is_client(self):
        return self.role == self.UserRole.CLIENT

    @property
    def is_manager(self):
        return self.role in [self.UserRole.ADMIN, self.UserRole.MANAGER]

    @property
    def can_edit_data(self):
        return self.role in [self.UserRole.ADMIN, self.UserRole.MANAGER, self.UserRole.OPERATOR, self.UserRole.CLIENT]

    @property
    def can_view_reports(self):
        return True

    @property
    def can_manage_users(self):
        return self.role in [self.UserRole.ADMIN, self.UserRole.MANAGER]

    @property
    def can_access_admin_panel(self):
        return self.role == self.UserRole.ADMIN

    @property
    def can_generate_reports(self):
        return self.role in [self.UserRole.ADMIN, self.UserRole.MANAGER, self.UserRole.CLIENT]

    @property
    def can_export_data(self):
        return self.role in [self.UserRole.ADMIN, self.UserRole.MANAGER, self.UserRole.CLIENT]

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0] 