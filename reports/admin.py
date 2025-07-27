from django.contrib import admin
from .models import ReportTemplate, GeneratedReport, ReportSchedule, ReportParameter


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'is_active', 'created_at')
    list_filter = ('report_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'template', 'title', 'generated_at', 'is_downloaded')
    list_filter = ('template', 'generated_at', 'is_downloaded', 'user')
    search_fields = ('user__email', 'title', 'template__name')
    date_hierarchy = 'generated_at'
    ordering = ('-generated_at',)


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'template', 'name', 'frequency', 'is_active', 'last_generated', 'next_generation')
    list_filter = ('frequency', 'is_active', 'template', 'created_at')
    search_fields = ('user__email', 'name', 'template__name')
    ordering = ('user', 'name')


@admin.register(ReportParameter)
class ReportParameterAdmin(admin.ModelAdmin):
    list_display = ('template', 'name', 'parameter_type', 'is_required', 'order')
    list_filter = ('parameter_type', 'is_required', 'template')
    search_fields = ('name', 'template__name')
    ordering = ('template', 'order', 'name')
