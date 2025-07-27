from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class APIToken(models.Model):
    """API tokens for external integrations."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    name = models.CharField(max_length=100)
    token = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"

class APIUsage(models.Model):
    """Track API usage for analytics."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_usage')
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    response_time = models.FloatField(help_text="Response time in milliseconds")
    status_code = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.method} {self.endpoint} ({self.status_code})"
