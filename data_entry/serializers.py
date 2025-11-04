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


class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'

class WaterAnalysisSerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    
    class Meta:
        model = WaterAnalysis
        fields = [
            'id', 'plant', 'plant_name', 'analysis_name', 'analysis_type', 'analysis_date', 'ph', 'tds', 'hardness',
            'total_alkalinity', 'chloride', 'temperature', 'basin_temperature', 'sulphate', 'cycle', 'iron', 'phosphate',
            'm_alkalinity', 'p_alkalinity', 'oh_alkalinity', 'sulphite', 'sodium_chloride', 'do', 'boiler_phosphate',
            'lsi', 'rsi', 'psi', 'lr', 'stability_score',
            'lsi_status', 'rsi_status', 'psi_status', 'lr_status', 'overall_status', 'notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'lsi', 'rsi', 'psi', 'lr', 'stability_score', 'lsi_status', 'rsi_status', 
            'psi_status', 'lr_status', 'overall_status', 'created_at', 'updated_at'
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