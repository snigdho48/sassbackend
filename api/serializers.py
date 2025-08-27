from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from users.models import CustomUser
from data_entry.models import DataCategory, TechnicalData, AnalyticalScore, WaterAnalysis, WaterTrend, WaterRecommendation
from reports.models import ReportTemplate, GeneratedReport
from dashboard.models import DashboardWidget, UserPreference

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'company', 'phone', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password2', 'company', 'phone', 'role')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # IMPORTANT: Django's default auth backends expect the keyword 'username'
            # even when the user model's USERNAME_FIELD is 'email'. So we pass the
            # email value using the 'username' kwarg to ensure compatibility.
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password,
            )
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
        else:
            raise serializers.ValidationError('Must include "email" and "password".')

        attrs['user'] = user
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

class DataCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataCategory
        fields = '__all__'

class TechnicalDataSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = TechnicalData
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def to_representation(self, instance):
        try:
            # Check if instance is a dictionary or has the expected attributes
            if isinstance(instance, dict):
                # Handle case where instance is already a dictionary
                return {
                    'id': instance.get('id', 'Unknown'),
                    'value': str(instance.get('value', '')),
                    'notes': instance.get('notes', ''),
                    'entry_date': instance.get('entry_date'),
                    'created_at': instance.get('created_at'),
                    'updated_at': instance.get('updated_at'),
                    'category_name': instance.get('category_name', 'Unknown'),
                    'user_name': instance.get('user_name', 'Unknown')
                }
            elif hasattr(instance, 'id'):
                # Normal model instance
                return super().to_representation(instance)
            else:
                # Fallback for unexpected data types
                return {
                    'id': 'Unknown',
                    'value': 'Unknown',
                    'notes': 'Unknown',
                    'entry_date': None,
                    'created_at': None,
                    'updated_at': None,
                    'category_name': 'Unknown',
                    'user_name': 'Unknown'
                }
        except Exception as e:
            # If there's an error with foreign key relationships, return basic data
            try:
                return {
                    'id': getattr(instance, 'id', 'Unknown'),
                    'value': str(getattr(instance, 'value', '')),
                    'notes': getattr(instance, 'notes', ''),
                    'entry_date': getattr(instance, 'entry_date', None),
                    'created_at': getattr(instance, 'created_at', None),
                    'updated_at': getattr(instance, 'updated_at', None),
                    'category_name': 'Unknown',
                    'user_name': 'Unknown'
                }
            except:
                # Ultimate fallback
                return {
                    'id': 'Unknown',
                    'value': 'Unknown',
                    'notes': 'Unknown',
                    'entry_date': None,
                    'created_at': None,
                    'updated_at': None,
                    'category_name': 'Unknown',
                    'user_name': 'Unknown'
                }

class AnalyticalScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticalScore
        fields = '__all__'

class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = '__all__'

class GeneratedReportSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = GeneratedReport
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = '__all__'

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = '__all__'

class DashboardDataSerializer(serializers.Serializer):
    total_entries = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    total_reports = serializers.IntegerField()
    recent_entries = TechnicalDataSerializer(many=True)
    analytics_data = serializers.DictField()
    chart_data = serializers.DictField()

class AnalyticsSerializer(serializers.Serializer):
    date_range = serializers.CharField()
    total_entries = serializers.IntegerField()
    average_score = serializers.FloatField()
    category_breakdown = serializers.DictField()
    trend_data = serializers.ListField()

class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uidb64 = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


# Water Analysis Serializers
class WaterAnalysisSerializer(serializers.ModelSerializer):
    analysis_date = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False)
    
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
    
    def create(self, validated_data):
        # Set default analysis_date if not provided
        if 'analysis_date' not in validated_data:
            from django.utils import timezone
            validated_data['analysis_date'] = timezone.now().date()
        return super().create(validated_data)


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