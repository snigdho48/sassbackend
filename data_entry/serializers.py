from rest_framework import serializers
from .models import DataCategory, TechnicalData, AnalyticalScore, WaterAnalysis, WaterTrend, WaterRecommendation


class DataCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCategory
        fields = '__all__'


class TechnicalDataSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_unit = serializers.CharField(source='category.unit', read_only=True)
    
    class Meta:
        model = TechnicalData
        fields = ['id', 'category', 'category_name', 'category_unit', 'value', 'notes', 'entry_date', 'created_at']
        read_only_fields = ['id', 'created_at']


class AnalyticalScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticalScore
        fields = '__all__'


class WaterAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterAnalysis
        fields = [
            'id', 'analysis_name', 'analysis_date', 'ph', 'tds', 'total_alkalinity', 
            'hardness', 'chloride', 'temperature', 'lsi', 'rsi', 'ls', 'stability_score',
            'lsi_status', 'rsi_status', 'ls_status', 'overall_status', 'notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'lsi', 'rsi', 'ls', 'stability_score', 'lsi_status', 'rsi_status', 
            'ls_status', 'overall_status', 'created_at', 'updated_at'
        ]


class WaterTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterTrend
        fields = ['id', 'parameter', 'value', 'trend_date', 'created_at']
        read_only_fields = ['id', 'created_at']


class WaterRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterRecommendation
        fields = [
            'id', 'recommendation_type', 'title', 'description', 'priority', 
            'is_implemented', 'created_at'
        ]
        read_only_fields = ['id', 'created_at'] 