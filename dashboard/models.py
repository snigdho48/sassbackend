from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardWidget(models.Model):
    """User dashboard widgets and their configurations."""
    WIDGET_TYPES = [
        ('chart', 'Chart'),
        ('metric', 'Metric'),
        ('table', 'Table'),
        ('gauge', 'Gauge'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets')
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=100)
    configuration = models.JSONField(default=dict)
    position = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position', 'created_at']
        unique_together = ['user', 'title']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class UserPreference(models.Model):
    """User preferences for dashboard and application settings."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
    ])
    language = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
    ])
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='Y-m-d')
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.email}"


class DashboardLayout(models.Model):
    """Dashboard layout configurations."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_layout')
    layout_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Layout for {self.user.email}"
