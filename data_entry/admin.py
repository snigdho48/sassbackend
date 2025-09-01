from django.contrib import admin
from .models import DataCategory, TechnicalData, AnalyticalScore, DataCalculation, WaterAnalysis, WaterTrend, WaterRecommendation


@admin.register(DataCategory)
class DataCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'min_value', 'max_value', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(TechnicalData)
class TechnicalDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'value', 'entry_date', 'created_at')
    list_filter = ('category', 'entry_date', 'created_at', 'user')
    search_fields = ('user__email', 'category__name', 'notes')
    date_hierarchy = 'entry_date'
    ordering = ('-entry_date', '-created_at')


@admin.register(AnalyticalScore)
class AnalyticalScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score_type', 'value', 'calculation_date', 'data_points_used')
    list_filter = ('score_type', 'calculation_date', 'user')
    search_fields = ('user__email', 'score_type')
    date_hierarchy = 'calculation_date'
    ordering = ('-calculation_date', '-created_at')


@admin.register(DataCalculation)
class DataCalculationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('categories_required',)
    ordering = ('name',)


@admin.register(WaterAnalysis)
class WaterAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'analysis_name', 'analysis_type', 'analysis_date', 'ph', 'lsi', 'rsi', 'psi', 'lr', 'stability_score', 'overall_status')
    list_filter = ('analysis_type', 'overall_status', 'analysis_date', 'user', 'lsi_status', 'rsi_status', 'psi_status', 'lr_status')
    search_fields = ('user__email', 'analysis_name', 'notes')
    date_hierarchy = 'analysis_date'
    ordering = ('-analysis_date', '-created_at')
    readonly_fields = ('lsi', 'rsi', 'psi', 'lr', 'stability_score', 'lsi_status', 'rsi_status', 'psi_status', 'lr_status', 'overall_status')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'analysis_name', 'analysis_type', 'analysis_date', 'notes')
        }),
        ('Water Parameters - Common', {
            'fields': ('ph', 'tds', 'hardness')
        }),
        ('Cooling Water Parameters', {
            'fields': ('total_alkalinity', 'chloride', 'temperature', 'basin_temperature', 'sulphate'),
            'classes': ('collapse',)
        }),
        ('Boiler Water Parameters', {
            'fields': ('m_alkalinity',),
            'classes': ('collapse',)
        }),
        ('Calculated Results', {
            'fields': ('lsi', 'rsi', 'psi', 'lr', 'stability_score', 'lsi_status', 'rsi_status', 'psi_status', 'lr_status', 'overall_status'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WaterTrend)
class WaterTrendAdmin(admin.ModelAdmin):
    list_display = ('user', 'parameter', 'value', 'trend_date')
    list_filter = ('parameter', 'trend_date', 'user')
    search_fields = ('user__email', 'parameter')
    date_hierarchy = 'trend_date'
    ordering = ('-trend_date', '-created_at')


@admin.register(WaterRecommendation)
class WaterRecommendationAdmin(admin.ModelAdmin):
    list_display = ('analysis', 'recommendation_type', 'title', 'priority', 'is_implemented')
    list_filter = ('recommendation_type', 'priority', 'is_implemented', 'created_at')
    search_fields = ('title', 'description', 'analysis__analysis_name')
    ordering = ('-priority', '-created_at')
