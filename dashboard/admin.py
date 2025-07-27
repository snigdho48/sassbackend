from django.contrib import admin
from .models import DashboardWidget, UserPreference, DashboardLayout


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'widget_type', 'title', 'position', 'is_active', 'created_at')
    list_filter = ('widget_type', 'is_active', 'created_at', 'user')
    search_fields = ('user__email', 'title')
    ordering = ('user', 'position', 'created_at')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'language', 'timezone', 'notifications_enabled', 'email_notifications')
    list_filter = ('theme', 'language', 'notifications_enabled', 'email_notifications')
    search_fields = ('user__email',)
    ordering = ('user',)


@admin.register(DashboardLayout)
class DashboardLayoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__email',)
    ordering = ('user',)
