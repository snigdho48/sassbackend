from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ReportTemplate(models.Model):
    """Templates for generating different types of reports."""
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Report'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    template_file = models.CharField(max_length=200, help_text="Path to the template file")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class GeneratedReport(models.Model):
    """Generated reports stored for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=500, blank=True)
    parameters = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_downloaded = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.generated_at})"


class ReportSchedule(models.Model):
    """Scheduled report generation."""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_schedules')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    next_generation = models.DateTimeField(null=True, blank=True)
    email_recipients = models.TextField(blank=True, help_text="Comma-separated email addresses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user', 'name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.frequency})"


class ReportParameter(models.Model):
    """Parameters for report generation."""
    PARAMETER_TYPES = [
        ('date_range', 'Date Range'),
        ('category', 'Data Category'),
        ('user', 'User'),
        ('custom', 'Custom'),
    ]
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=100)
    parameter_type = models.CharField(max_length=20, choices=PARAMETER_TYPES)
    default_value = models.CharField(max_length=200, blank=True)
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['template', 'order', 'name']
        unique_together = ['template', 'name']
    
    def __str__(self):
        return f"{self.template.name} - {self.name}"
