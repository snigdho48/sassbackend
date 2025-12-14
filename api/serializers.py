from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from users.models import CustomUser
from data_entry.models import DataCategory, TechnicalData, AnalyticalScore, WaterAnalysis, WaterTrend, WaterRecommendation, Plant, WaterSystem
from reports.models import ReportTemplate, GeneratedReport
from dashboard.models import DashboardWidget, UserPreference

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_super_admin = serializers.ReadOnlyField()
    is_admin = serializers.ReadOnlyField()
    is_general_user = serializers.ReadOnlyField()
    can_create_plants = serializers.ReadOnlyField()
    can_create_admin_users = serializers.ReadOnlyField()
    can_create_general_users = serializers.ReadOnlyField()
    can_change_target_range = serializers.ReadOnlyField()
    assigned_admin = serializers.PrimaryKeyRelatedField(read_only=True)
    assigned_admin_email = serializers.CharField(source='assigned_admin.email', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'role', 'role_display',
            'company', 'phone', 'date_joined', 'last_login', 'assigned_admin', 'assigned_admin_email',
            'is_active', 'is_super_admin', 'is_admin', 'is_general_user',
            'can_create_plants', 'can_create_admin_users', 'can_create_general_users',
            'can_change_target_range'
        )
        read_only_fields = ('id', 'date_joined', 'last_login', 'role_display', 'assigned_admin_email')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    role = serializers.CharField(default='general_user', required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)
    assigned_admin = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role__in=[CustomUser.UserRole.ADMIN, CustomUser.UserRole.SUPER_ADMIN]),
        required=False,
        allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password2', 'company', 'phone', 'role', 'assigned_admin')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        # Ensure new users (admin and general users) are ALWAYS created as active by default
        # This overrides any attempt to set is_active=False
        validated_data['is_active'] = True
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
            # Super Admin can always login even if inactive
            if not user.is_active and not user.is_super_admin:
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
            'id', 'analysis_name', 'analysis_date', 'plant', 'water_system', 'analysis_type', 'ph', 'tds', 'total_alkalinity', 
            'hardness', 'chloride', 'temperature', 'basin_temperature', 'sulphate', 'cycle', 'iron', 'phosphate',
            'm_alkalinity', 'p_alkalinity', 'oh_alkalinity', 'sulphite', 'sodium_chloride', 'do', 'boiler_phosphate',
            'lsi', 'rsi', 'psi', 'lr', 'stability_score',
            'lsi_status', 'rsi_status', 'psi_status', 'lr_status', 'overall_status', 
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'stability_score', 'created_at', 'updated_at'
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


class PlantListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for plant list - only basic info for dropdown"""
    class Meta:
        model = Plant
        fields = ['id', 'name']

class PlantDetailSerializer(serializers.ModelSerializer):
    """Full serializer for plant details - includes all parameters"""
    owner = UserSerializer(read_only=True)  # Legacy field for backward compatibility
    owner_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=CustomUser.objects.filter(role__in=[CustomUser.UserRole.ADMIN]),
        required=False,
        allow_null=True,
        source='owner'
    )
    owners = UserSerializer(many=True, read_only=True)
    owner_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True,
        source='owners'
    )
    
    class Meta:
        model = Plant
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        """Make all fields optional except name"""
        super().__init__(*args, **kwargs)
        # Make all fields optional except name
        for field_name, field in self.fields.items():
            if field_name != 'name' and field_name not in ['owner', 'owners', 'owner_id', 'owner_ids', 'created_at', 'updated_at']:
                field.required = False
                field.allow_null = True
    
    def validate(self, attrs):
        """Validate plant data - parameters are now managed via water systems, so no parameter validation needed"""
        # Ensure boolean fields have proper default values
        boolean_fields = [
            'is_active',
            'cooling_chloride_enabled',
            'cooling_cycle_enabled', 
            'cooling_iron_enabled',
            'cooling_phosphate_enabled',
            'cooling_lsi_enabled',
            'cooling_rsi_enabled',
            'boiler_p_alkalinity_enabled',
            'boiler_oh_alkalinity_enabled',
            'boiler_sulphite_enabled',
            'boiler_sodium_chloride_enabled',
            'boiler_do_enabled',
            'boiler_phosphate_enabled',
            'boiler_iron_enabled'
            # Note: boiler_lsi_enabled and boiler_rsi_enabled removed per requirements
        ]
        
        for field in boolean_fields:
            if field in attrs and attrs[field] is None:
                attrs[field] = False
                
        return attrs


class WaterSystemSerializer(serializers.ModelSerializer):
    """Serializer for water systems (cooling/boiler water systems under plants)."""
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    assigned_users = UserSerializer(many=True, read_only=True)
    assigned_user_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True,
        source='assigned_users'
    )
    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)
    
    class Meta:
        model = WaterSystem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        """Make all parameter fields optional except name, plant, and system_type"""
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['name', 'plant', 'system_type', 'is_active', 'assigned_users', 'assigned_user_ids', 'plant_name', 'system_type_display', 'created_at', 'updated_at']:
                field.required = False
                field.allow_null = True


class WaterRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterRecommendation
        fields = [
            'id', 'recommendation_type', 'title', 'description', 'priority', 
            'is_implemented', 'created_at'
        ]
        read_only_fields = ['id', 'created_at'] 