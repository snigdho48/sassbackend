from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import math

User = get_user_model()


class DataCategory(models.Model):
    """Categories for different types of technical data."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, blank=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Data Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TechnicalData(models.Model):
    """Main model for storing technical data entries."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_entries')
    category = models.ForeignKey(DataCategory, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    entry_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-entry_date', '-created_at']
        unique_together = ['user', 'category', 'entry_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.category.name}: {self.value} ({self.entry_date})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.category.min_value and self.value < self.category.min_value:
            raise ValidationError(f"Value must be at least {self.category.min_value}")
        if self.category.max_value and self.value > self.category.max_value:
            raise ValidationError(f"Value must be at most {self.category.max_value}")


class Plant(models.Model):
    """Plant model to store plant-specific parameters and ranges for water analysis."""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    # Multiple users can be assigned to a single plant
    owners = models.ManyToManyField(User, blank=True, related_name='owned_plants', help_text='Users assigned to this plant')
    # Keep owner field for backward compatibility during migration
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_plants_legacy')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Plant-specific parameter ranges for cooling water (all optional)
    cooling_ph_min = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cooling_ph_max = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cooling_tds_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_tds_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_hardness_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_chloride_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_chloride_enabled = models.BooleanField(default=False, help_text="Enable chloride monitoring for this plant")
    cooling_cycle_min = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_cycle_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_cycle_enabled = models.BooleanField(default=False, help_text="Enable cycle of concentration monitoring for this plant")
    cooling_iron_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_iron_enabled = models.BooleanField(default=False, help_text="Enable iron monitoring for this plant")
    cooling_phosphate_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_phosphate_enabled = models.BooleanField(default=False, help_text="Enable phosphate monitoring for this plant")
    
    # Plant-specific parameter ranges for boiler water (all optional)
    boiler_ph_min = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    boiler_ph_max = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    boiler_tds_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_tds_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_hardness_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    boiler_alkalinity_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Boiler water optional parameters
    boiler_p_alkalinity_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_p_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_p_alkalinity_enabled = models.BooleanField(default=False, help_text="Enable P-alkalinity monitoring for this plant")
    boiler_oh_alkalinity_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_oh_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_oh_alkalinity_enabled = models.BooleanField(default=False, help_text="Enable OH-alkalinity monitoring for this plant")
    boiler_sulphite_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_sulphite_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_sulphite_enabled = models.BooleanField(default=False, help_text="Enable sulphite monitoring for this plant")
    boiler_sodium_chloride_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_sodium_chloride_enabled = models.BooleanField(default=False, help_text="Enable sodium chloride monitoring for this plant")
    boiler_do_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_do_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_do_enabled = models.BooleanField(default=False, help_text="Enable dissolved oxygen monitoring for this plant")
    boiler_phosphate_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_phosphate_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_phosphate_enabled = models.BooleanField(default=False, help_text="Enable phosphate monitoring for this plant")
    boiler_iron_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    boiler_iron_enabled = models.BooleanField(default=False, help_text="Enable iron monitoring for this plant")
    
    # LSI and RSI parameters (for cooling water only - removed from boiler per requirements)
    cooling_lsi_min = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_lsi_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_lsi_enabled = models.BooleanField(default=False, help_text="Enable LSI monitoring for cooling water")
    cooling_rsi_min = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_rsi_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_rsi_enabled = models.BooleanField(default=False, help_text="Enable RSI monitoring for cooling water")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_cooling_parameters(self):
        """Get cooling water parameters for this plant."""
        params = {}
        
        # Include only when configured
        if self.cooling_ph_min is not None or self.cooling_ph_max is not None:
            params['ph'] = {'min': self.cooling_ph_min, 'max': self.cooling_ph_max}
        if self.cooling_tds_min is not None or self.cooling_tds_max is not None:
            params['tds'] = {'min': self.cooling_tds_min, 'max': self.cooling_tds_max}
        if self.cooling_hardness_max is not None:
            params['hardness'] = {'max': self.cooling_hardness_max}
        if self.cooling_alkalinity_max is not None:
            params['alkalinity'] = {'max': self.cooling_alkalinity_max}
        
        # Only include optional parameters if enabled
        if self.cooling_chloride_enabled:
            params['chloride'] = {'max': self.cooling_chloride_max}
        if self.cooling_cycle_enabled:
            params['cycle'] = {'min': self.cooling_cycle_min, 'max': self.cooling_cycle_max}
        if self.cooling_iron_enabled:
            params['iron'] = {'max': self.cooling_iron_max}
        if self.cooling_phosphate_enabled:
            params['phosphate'] = {'max': self.cooling_phosphate_max}
        if self.cooling_lsi_enabled:
            params['lsi'] = {'min': self.cooling_lsi_min, 'max': self.cooling_lsi_max}
        if self.cooling_rsi_enabled:
            params['rsi'] = {'min': self.cooling_rsi_min, 'max': self.cooling_rsi_max}
            
        return params
    
    def get_boiler_parameters(self):
        """Get boiler water parameters for this plant."""
        params = {}
        
        # Include only when configured
        if self.boiler_ph_min is not None or self.boiler_ph_max is not None:
            params['ph'] = {'min': self.boiler_ph_min, 'max': self.boiler_ph_max}
        if self.boiler_tds_min is not None or self.boiler_tds_max is not None:
            params['tds'] = {'min': self.boiler_tds_min, 'max': self.boiler_tds_max}
        if self.boiler_hardness_max is not None:
            params['hardness'] = {'max': self.boiler_hardness_max}
        if self.boiler_alkalinity_min is not None or self.boiler_alkalinity_max is not None:
            params['alkalinity'] = {'min': self.boiler_alkalinity_min, 'max': self.boiler_alkalinity_max}
        
        # Only include optional parameters if enabled
        if self.boiler_p_alkalinity_enabled:
            params['p_alkalinity'] = {'min': self.boiler_p_alkalinity_min, 'max': self.boiler_p_alkalinity_max}
        if self.boiler_oh_alkalinity_enabled:
            params['oh_alkalinity'] = {'min': self.boiler_oh_alkalinity_min, 'max': self.boiler_oh_alkalinity_max}
        if self.boiler_sulphite_enabled:
            params['sulphite'] = {'min': self.boiler_sulphite_min, 'max': self.boiler_sulphite_max}
        if self.boiler_sodium_chloride_enabled:
            params['sodium_chloride'] = {'max': self.boiler_sodium_chloride_max}
        if self.boiler_do_enabled:
            params['do'] = {'min': self.boiler_do_min, 'max': self.boiler_do_max}
        if self.boiler_phosphate_enabled:
            params['phosphate'] = {'min': self.boiler_phosphate_min, 'max': self.boiler_phosphate_max}
        if self.boiler_iron_enabled:
            params['iron'] = {'max': self.boiler_iron_max}
        # Note: LSI and RSI are removed from boiler water analysis per feedback
            
        return params


class WaterSystem(models.Model):
    """Water system model for cooling or boiler water systems under a plant."""
    SYSTEM_TYPES = [
        ('cooling', 'Cooling Water'),
        ('boiler', 'Boiler Water'),
    ]
    
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='water_systems')
    name = models.CharField(max_length=100, help_text="Name of the water system (e.g., 'Cooling Tower 1', 'Boiler System A')")
    system_type = models.CharField(max_length=20, choices=SYSTEM_TYPES)
    is_active = models.BooleanField(default=True)
    # Users who can access this water system for analysis
    assigned_users = models.ManyToManyField(User, blank=True, related_name='assigned_water_systems', help_text='Users assigned to this water system')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Cooling water parameters (all optional)
    cooling_ph_min = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cooling_ph_max = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cooling_tds_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_tds_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_hardness_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_chloride_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_chloride_enabled = models.BooleanField(default=False, help_text="Enable chloride monitoring")
    cooling_cycle_min = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_cycle_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_cycle_enabled = models.BooleanField(default=False, help_text="Enable cycle of concentration monitoring")
    cooling_iron_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_iron_enabled = models.BooleanField(default=False, help_text="Enable iron monitoring")
    cooling_phosphate_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cooling_phosphate_enabled = models.BooleanField(default=False, help_text="Enable phosphate monitoring")
    cooling_lsi_min = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_lsi_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_lsi_enabled = models.BooleanField(default=False, help_text="Enable LSI monitoring")
    cooling_rsi_min = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_rsi_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cooling_rsi_enabled = models.BooleanField(default=False, help_text="Enable RSI monitoring")
    
    # Boiler water parameters (all optional)
    boiler_ph_min = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    boiler_ph_max = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    boiler_tds_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_tds_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_hardness_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    boiler_alkalinity_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_p_alkalinity_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_p_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_p_alkalinity_enabled = models.BooleanField(default=False, help_text="Enable P-alkalinity monitoring")
    boiler_oh_alkalinity_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_oh_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_oh_alkalinity_enabled = models.BooleanField(default=False, help_text="Enable OH-alkalinity monitoring")
    boiler_sulphite_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_sulphite_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_sulphite_enabled = models.BooleanField(default=False, help_text="Enable sulphite monitoring")
    boiler_sodium_chloride_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_sodium_chloride_enabled = models.BooleanField(default=False, help_text="Enable sodium chloride monitoring")
    boiler_do_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_do_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_do_enabled = models.BooleanField(default=False, help_text="Enable dissolved oxygen monitoring")
    boiler_phosphate_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_phosphate_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    boiler_phosphate_enabled = models.BooleanField(default=False, help_text="Enable phosphate monitoring")
    boiler_iron_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    boiler_iron_enabled = models.BooleanField(default=False, help_text="Enable iron monitoring")
    
    class Meta:
        ordering = ['plant', 'system_type', 'name']
        unique_together = ['plant', 'name', 'system_type']  # Same name can exist for different types
    
    def __str__(self):
        return f"{self.plant.name} - {self.get_system_type_display()} - {self.name}"
    
    def get_parameters(self):
        """Get parameters based on system type."""
        if self.system_type == 'cooling':
            return self.get_cooling_parameters()
        else:
            return self.get_boiler_parameters()
    
    def get_cooling_parameters(self):
        """Get cooling water parameters for this system."""
        params = {}
        
        if self.cooling_ph_min is not None or self.cooling_ph_max is not None:
            params['ph'] = {'min': self.cooling_ph_min, 'max': self.cooling_ph_max}
        if self.cooling_tds_min is not None or self.cooling_tds_max is not None:
            params['tds'] = {'min': self.cooling_tds_min, 'max': self.cooling_tds_max}
        if self.cooling_hardness_max is not None:
            params['hardness'] = {'max': self.cooling_hardness_max}
        if self.cooling_alkalinity_max is not None:
            params['alkalinity'] = {'max': self.cooling_alkalinity_max}
        
        if self.cooling_chloride_enabled:
            params['chloride'] = {'max': self.cooling_chloride_max}
        if self.cooling_cycle_enabled:
            params['cycle'] = {'min': self.cooling_cycle_min, 'max': self.cooling_cycle_max}
        if self.cooling_iron_enabled:
            params['iron'] = {'max': self.cooling_iron_max}
        if self.cooling_phosphate_enabled:
            params['phosphate'] = {'max': self.cooling_phosphate_max}
        if self.cooling_lsi_enabled:
            params['lsi'] = {'min': self.cooling_lsi_min, 'max': self.cooling_lsi_max}
        if self.cooling_rsi_enabled:
            params['rsi'] = {'min': self.cooling_rsi_min, 'max': self.cooling_rsi_max}
            
        return params
    
    def get_boiler_parameters(self):
        """Get boiler water parameters for this system."""
        params = {}
        
        if self.boiler_ph_min is not None or self.boiler_ph_max is not None:
            params['ph'] = {'min': self.boiler_ph_min, 'max': self.boiler_ph_max}
        if self.boiler_tds_min is not None or self.boiler_tds_max is not None:
            params['tds'] = {'min': self.boiler_tds_min, 'max': self.boiler_tds_max}
        if self.boiler_hardness_max is not None:
            params['hardness'] = {'max': self.boiler_hardness_max}
        if self.boiler_alkalinity_min is not None or self.boiler_alkalinity_max is not None:
            params['alkalinity'] = {'min': self.boiler_alkalinity_min, 'max': self.boiler_alkalinity_max}
        
        if self.boiler_p_alkalinity_enabled:
            params['p_alkalinity'] = {'min': self.boiler_p_alkalinity_min, 'max': self.boiler_p_alkalinity_max}
        if self.boiler_oh_alkalinity_enabled:
            params['oh_alkalinity'] = {'min': self.boiler_oh_alkalinity_min, 'max': self.boiler_oh_alkalinity_max}
        if self.boiler_sulphite_enabled:
            params['sulphite'] = {'min': self.boiler_sulphite_min, 'max': self.boiler_sulphite_max}
        if self.boiler_sodium_chloride_enabled:
            params['sodium_chloride'] = {'max': self.boiler_sodium_chloride_max}
        if self.boiler_do_enabled:
            params['do'] = {'min': self.boiler_do_min, 'max': self.boiler_do_max}
        if self.boiler_phosphate_enabled:
            params['phosphate'] = {'min': self.boiler_phosphate_min, 'max': self.boiler_phosphate_max}
        if self.boiler_iron_enabled:
            params['iron'] = {'max': self.boiler_iron_max}
            
        return params


class WaterAnalysis(models.Model):
    """Water analysis data for stability calculations."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_analyses')
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='water_analyses', null=True, blank=True)
    water_system = models.ForeignKey('WaterSystem', on_delete=models.CASCADE, related_name='water_analyses', null=True, blank=True, help_text='The specific water system (cooling/boiler) for this analysis')
    analysis_date = models.DateField(default=timezone.now)
    analysis_name = models.CharField(max_length=100, default="Water Analysis")
    analysis_type = models.CharField(max_length=20, choices=[('cooling', 'Cooling Water'), ('boiler', 'Boiler Water')], default='cooling')
    
    # Water Parameters - Common
    ph = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(14)])
    tds = models.DecimalField(max_digits=6, decimal_places=2, help_text="Total Dissolved Solids (ppm)")
    hardness = models.DecimalField(max_digits=6, decimal_places=2, help_text="Hardness as CaCO₃ (ppm)")
    
    # Cooling Water Specific Parameters
    total_alkalinity = models.DecimalField(max_digits=6, decimal_places=2, help_text="Total Alkalinity as CaCO₃ (ppm)", null=True, blank=True)
    chloride = models.DecimalField(max_digits=6, decimal_places=2, help_text="Chloride as NaCl (ppm)", null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text="Hot Side Temperature (°C)", null=True, blank=True)
    basin_temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text="Basin Temperature (°C)", null=True, blank=True)
    sulphate = models.DecimalField(max_digits=6, decimal_places=2, help_text="Sulphate (ppm)", null=True, blank=True)
    cycle = models.DecimalField(max_digits=4, decimal_places=1, help_text="Cycle of Concentration", null=True, blank=True)
    iron = models.DecimalField(max_digits=6, decimal_places=2, help_text="Iron (ppm)", null=True, blank=True)
    phosphate = models.DecimalField(max_digits=6, decimal_places=2, help_text="Phosphate (ppm)", null=True, blank=True)  # For cooling water
    
    # Boiler Water Specific Parameters
    m_alkalinity = models.DecimalField(max_digits=6, decimal_places=2, help_text="M-Alkalinity as CaCO₃ (ppm)", null=True, blank=True)
    p_alkalinity = models.DecimalField(max_digits=6, decimal_places=2, help_text="P-Alkalinity as CaCO₃ (ppm)", null=True, blank=True)
    oh_alkalinity = models.DecimalField(max_digits=6, decimal_places=2, help_text="OH-Alkalinity as CaCO₃ (ppm)", null=True, blank=True)
    sulphite = models.DecimalField(max_digits=6, decimal_places=2, help_text="Sulphite (ppm)", null=True, blank=True)  # Changed from sulfite
    sodium_chloride = models.DecimalField(max_digits=6, decimal_places=2, help_text="Sodium Chloride (ppm)", null=True, blank=True)  # Changed from chlorides
    do = models.DecimalField(max_digits=6, decimal_places=3, help_text="Dissolved Oxygen (ppm)", null=True, blank=True)  # New field
    boiler_phosphate = models.DecimalField(max_digits=6, decimal_places=2, help_text="Phosphate (ppm)", null=True, blank=True)  # For boiler water
    
    # Calculated Indices
    lsi = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    rsi = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    psi = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    lr = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    stability_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Status fields
    lsi_status = models.CharField(max_length=100, blank=True)
    rsi_status = models.CharField(max_length=100, blank=True)
    psi_status = models.CharField(max_length=100, blank=True)
    lr_status = models.CharField(max_length=100, blank=True)
    overall_status = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-analysis_date', '-created_at']
        verbose_name_plural = "Water Analyses"
    
    def __str__(self):
        return f"{self.user.email} - {self.analysis_name} ({self.analysis_date})"
    
    def save(self, *args, **kwargs):
        """Override save to create WaterTrend records for historical tracking."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Create trend records for new analyses
        if is_new:
            try:
                self._create_trend_records()
            except Exception as e:
                print(f"Error creating trend records: {e}")
                # Don't fail the save if trend creation fails
    
    def _create_trend_records(self):
        """Create WaterTrend records for this analysis."""
        from django.utils import timezone
        from django.apps import apps
        
        # Get WaterTrend model using apps registry to avoid circular import
        WaterTrend = apps.get_model('data_entry', 'WaterTrend')
        
        # Parameters to track for trends
        trend_parameters = {
            'ph': self.ph,
            'lsi': self.lsi,
            'rsi': self.rsi,
        }
        
        # Add LR only if chloride monitoring is enabled for the plant
        plant_obj = getattr(self, 'plant', None)
        if plant_obj and plant_obj.cooling_chloride_enabled and self.lr is not None:
            trend_parameters['lr'] = self.lr
        
        # Create trend records
        for parameter, value in trend_parameters.items():
            if value is not None:
                WaterTrend.objects.create(
                    user=self.user,
                    parameter=parameter,
                    trend_date=self.analysis_date,
                    value=value,
                    analysis_id=self.id  # Add analysis reference
                )
    
    def calculate_indices(self):
        """Calculate water stability indices based on analysis type."""
        try:
            if self.analysis_type == 'boiler':
                # For boiler water, only calculate stability score
                self.stability_score = self._calculate_boiler_stability_score()
                self.overall_status = self._get_boiler_overall_status()
            else:
                # For cooling water, calculate all indices
                self._calculate_cooling_indices()
            
            self.save()
            return True
        except Exception as e:
            print(f"Error calculating indices: {e}")
            return False
    
    def _calculate_cooling_indices(self):
        """Calculate LSI, RSI, PSI, and LR indices for cooling water."""
        try:
            # Convert Decimal fields to float for calculations with safe conversion
            ph = float(self.ph) if self.ph is not None else None
            tds = float(self.tds) if self.tds is not None else None
            total_alkalinity = float(self.total_alkalinity) if self.total_alkalinity is not None else None
            hardness = float(self.hardness) if self.hardness is not None else None
            # Handle chloride - check water_system first, then plant
            # Prefer water_system setting, fallback to plant setting
            use_chloride = False
            if self.water_system and self.water_system.system_type == 'cooling':
                use_chloride = self.water_system.cooling_chloride_enabled
            elif hasattr(self, 'plant') and self.plant:
                use_chloride = self.plant.cooling_chloride_enabled
            
            if use_chloride:
                chloride = float(self.chloride) if self.chloride is not None else None
            else:
                chloride = None  # Skip chloride if not enabled
            temperature = float(self.temperature) if self.temperature is not None else None
            sulphate = float(self.sulphate) if self.sulphate is not None else None
            
            # If key inputs are missing, skip log-based indices to avoid math domain errors
            can_compute_lsi = ph is not None and tds is not None and hardness is not None and total_alkalinity is not None and (temperature is not None)

            # Langelier Saturation Index (LSI) (only when we have all needed inputs)
            # LSI = pH - pHs
            # pHs = 9.3 + A + B - C - D
            # Where:
            # A = (Log10(TDS)-1)/10
            # B = -13.12 x Log10(Hot Side Temp (°C)+273) + 34.55
            # C = Log10(Hardness CaCO3) - 0.4
            # D = Log10(Alkaline CaCO3)
            
            if can_compute_lsi and tds > 0 and hardness > 0 and total_alkalinity > 0 and (temperature is not None and temperature > 0):
                import math
                # Calculate A, B, C, D factors
                A = (math.log10(tds) - 1) / 10
                B = -13.12 * math.log10(temperature + 273) + 34.55
                C = math.log10(hardness) - 0.4
                D = math.log10(total_alkalinity)
                
                phs = 9.3 + A + B - C - D
                self.lsi = ph - phs
                
                # Ryznar Stability Index (RSI)
                # RSI = 2 * pHs - pH
                self.rsi = 2 * phs - ph
                
                # Puckorius Scaling Index (PSI)
                # PSI = 2 * pHs - pHe
                # Where pHe = 1.465 + Log10(Alkaline CaCO3) + 4.54
                pHe = 1.465 + math.log10(total_alkalinity) + 4.54
                self.psi = 2 * phs - pHe
            else:
                self.lsi = None
                self.rsi = None
                self.psi = None
            
            # Langelier Ratio (LR)
            # LR = (Cl + SO4) / (HCO3)
            # Only calculate if chloride is enabled (check water_system first, then plant)
            if total_alkalinity is not None and total_alkalinity > 0:
                # Check if chloride should be used
                use_chloride = False
                if self.water_system and self.water_system.system_type == 'cooling':
                    use_chloride = self.water_system.cooling_chloride_enabled
                elif hasattr(self, 'plant') and self.plant:
                    use_chloride = self.plant.cooling_chloride_enabled
                
                if use_chloride:
                    # Require chloride value to compute with chloride; if not present, skip
                    if chloride is not None and sulphate is not None:
                        self.lr = (chloride + sulphate) / total_alkalinity
                    elif chloride is not None:
                        self.lr = chloride / total_alkalinity
                    elif sulphate is not None:
                        self.lr = sulphate / total_alkalinity
                    else:
                        self.lr = None
                else:
                    # Skip chloride in calculation if not enabled
                    if sulphate is not None:
                        self.lr = sulphate / total_alkalinity
                    else:
                        self.lr = None
            else:
                self.lr = None
            
            # Determine status
            self.lsi_status = self._get_lsi_status() if self.lsi is not None else ""
            self.rsi_status = self._get_rsi_status() if self.rsi is not None else ""
            self.psi_status = self._get_psi_status() if self.psi is not None else ""
            self.lr_status = self._get_lr_status() if self.lr is not None else ""
            self.overall_status = self._get_cooling_overall_status()
            
            # Calculate stability score (0-100)
            self.stability_score = self._calculate_cooling_stability_score()
            
        except Exception as e:
            print(f"Error calculating cooling indices: {e}")
    
    def _calculate_boiler_stability_score(self):
        """Calculate stability score for boiler water."""
        try:
            ph = float(self.ph) if self.ph is not None else None
            tds = float(self.tds) if self.tds is not None else None
            hardness = float(self.hardness) if self.hardness is not None else None
            m_alkalinity = float(self.m_alkalinity) if self.m_alkalinity is not None else None

            # Helper to check and penalize outside ranges with plant-configurable targets
            def penalize_range(val, rng_min, rng_max, step, base_penalty):
                if val is None:
                    return 0
                if rng_min is None and rng_max is None:
                    return 0
                # Clamp missing side with the other bound to compute deviation
                if rng_min is not None and val < rng_min:
                    deviation_units = (rng_min - val) / step
                    return deviation_units * base_penalty
                if rng_max is not None and val > rng_max:
                    deviation_units = (val - rng_max) / step
                    return deviation_units * base_penalty
                return 0
            
            # Start with 100 points
            score = 100
            
            # Use water_system parameters first, then plant-specific configured ranges, otherwise use sensible defaults
            # Prefer water_system parameters if available
            if self.water_system and self.water_system.system_type == 'boiler':
                boiler_params = self.water_system.get_boiler_parameters()
                ph_min = boiler_params.get('ph', {}).get('min') if boiler_params.get('ph') else None
                ph_max = boiler_params.get('ph', {}).get('max') if boiler_params.get('ph') else None
                tds_min = boiler_params.get('tds', {}).get('min') if boiler_params.get('tds') else None
                tds_max = boiler_params.get('tds', {}).get('max') if boiler_params.get('tds') else None
                hardness_max = boiler_params.get('hardness', {}).get('max') if boiler_params.get('hardness') else None
                alk_min = boiler_params.get('alkalinity', {}).get('min') if boiler_params.get('alkalinity') else None
                alk_max = boiler_params.get('alkalinity', {}).get('max') if boiler_params.get('alkalinity') else None
            else:
                # Fallback to plant parameters
                plant_obj = getattr(self, 'plant', None)
                if plant_obj:
                    ph_min = plant_obj.boiler_ph_min
                    ph_max = plant_obj.boiler_ph_max
                    tds_min = plant_obj.boiler_tds_min
                    tds_max = plant_obj.boiler_tds_max
                    hardness_max = plant_obj.boiler_hardness_max
                    alk_min = plant_obj.boiler_alkalinity_min
                    alk_max = plant_obj.boiler_alkalinity_max
                else:
                    ph_min = ph_max = tds_min = tds_max = hardness_max = alk_min = alk_max = None

            # Defaults if plant ranges not configured
            ph_min = float(ph_min) if ph_min is not None else 10.5
            ph_max = float(ph_max) if ph_max is not None else 11.5
            tds_min = float(tds_min) if tds_min is not None else 2500
            tds_max = float(tds_max) if tds_max is not None else 3500
            hardness_max = float(hardness_max) if hardness_max is not None else 2.0
            alk_min = float(alk_min) if alk_min is not None else 250
            alk_max = float(alk_max) if alk_max is not None else 600

            # pH deduction (use 0.1 step, 5 points per step)
            score -= penalize_range(ph, ph_min, ph_max, step=0.1, base_penalty=5)

            # TDS deduction: outside range small penalty; heavy if far
            if tds is not None:
                if tds < tds_min or tds > tds_max:
                    score -= 10
                    if tds is not None and (tds > (tds_max + 500) or tds < max(0, tds_min - 500)):
                        score -= 10

            # Hardness deduction: penalty only when exceeding max
            if hardness is not None and hardness_max is not None and hardness > hardness_max:
                score -= 10 if hardness <= hardness_max + 3 else 20

            # M-Alkalinity deduction (use 50 ppm step, 2 points per step)
            score -= penalize_range(m_alkalinity, alk_min, alk_max, step=50, base_penalty=2)
            
            return max(0, min(100, score))
        except Exception as e:
            print(f"Error calculating boiler stability score: {e}")
            return 0
    
    def _get_lsi_status(self):
        """Get LSI status based on value."""
        if self.lsi > 0.5:
            return "Scaling Likely"
        elif self.lsi < -0.5:
            return "Corrosion Likely"
        else:
            return "Stable"
    
    def _get_rsi_status(self):
        """Get RSI status based on value."""
        if self.rsi < 6.0:
            return "Scaling Likely"
        elif self.rsi > 7.0:
            return "Corrosion Likely"
        else:
            return "Stable"
    
    def _get_psi_status(self):
        """Get PSI status based on value."""
        if self.psi < 4.5:
            return "Water has a tendency to scale"
        elif 4.5 <= self.psi <= 6.5:
            return "Water is in optimal range with no corrosion or scaling"
        else:
            return "Water has a tendency to corrode"
    
    def _get_lr_status(self):
        """Get LR status based on value."""
        if self.lr < 0.8:
            return "Chlorides and sulfate probably will not interfere with natural film formation"
        elif 0.8 <= self.lr <= 1.2:
            return "Chlorides and sulfates may interfere with natural film formation. Higher than desired corrosion rates might be anticipated."
        else:
            return "The tendency towards high corrosion rates of a local type should be expected as the index increases"
    
    def _get_cooling_overall_status(self):
        """Get overall water stability status for cooling water."""
        lsi_score = 1 if self.lsi_status == "Stable" else 0
        rsi_score = 1 if self.rsi_status == "Stable" else 0
        psi_score = 1 if self.psi_status == "Water is in optimal range with no corrosion or scaling" else 0
        lr_score = 1 if self.lr_status == "Chlorides and sulfate probably will not interfere with natural film formation" else 0
        
        total_score = lsi_score + rsi_score + psi_score + lr_score
        if total_score >= 3:
            return "Stable"
        elif total_score >= 2:
            return "Moderate"
        else:
            return "Unstable"
    
    def _get_boiler_overall_status(self):
        """Get overall water stability status for boiler water."""
        if self.stability_score >= 70:
            return "Stable"
        elif self.stability_score >= 50:
            return "Moderate"
        else:
            return "Unstable"
    
    def _calculate_cooling_stability_score(self):
        """Calculate overall stability score (0-100) for cooling water."""
        base_score = 50
        
        # LSI contribution
        if self.lsi_status == "Stable":
            base_score += 20
        elif self.lsi_status == "Scaling Likely":
            base_score -= 10
        elif self.lsi_status == "Corrosion Likely":
            base_score -= 20
        
        # RSI contribution
        if self.rsi_status == "Stable":
            base_score += 20
        elif self.rsi_status == "Scaling Likely":
            base_score -= 10
        elif self.rsi_status == "Corrosion Likely":
            base_score -= 20
        
        # PSI contribution
        if self.psi_status == "Water is in optimal range with no corrosion or scaling":
            base_score += 12
        elif self.psi_status == "Water has a tendency to scale":
            base_score -= 6
        elif self.psi_status == "Water has a tendency to corrode":
            base_score -= 12
        
        # LR contribution
        if self.lr_status == "Chlorides and sulfate probably will not interfere with natural film formation":
            base_score += 10
        elif self.lr_status == "Chlorides and sulfates may interfere with natural film formation. Higher than desired corrosion rates might be anticipated.":
            base_score += 5
        elif self.lr_status == "The tendency towards high corrosion rates of a local type should be expected as the index increases":
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    def _generate_recommendations(self):
        """Generate recommendations based on analysis results."""
        # Clear existing recommendations
        self.recommendations.all().delete()
        
        recommendations = []
        
        # LSI-based recommendations
        if self.lsi_status == "Scaling Likely":
            recommendations.append({
                'type': 'scaling',
                'title': 'Review chemical dosing to reduce scaling tendency',
                'description': 'High LSI indicates potential for scale formation. Consider adjusting chemical treatment.',
                'priority': 'high'
            })
            recommendations.append({
                'type': 'treatment',
                'title': 'Increase blowdown rate',
                'description': 'Higher blowdown rate can help reduce scaling potential.',
                'priority': 'medium'
            })
        
        elif self.lsi_status == "Corrosion Likely":
            recommendations.append({
                'type': 'corrosion',
                'title': 'Implement corrosion inhibitor treatment',
                'description': 'Low LSI indicates potential for corrosion. Add corrosion inhibitors.',
                'priority': 'high'
            })
        
        # RSI-based recommendations
        if self.rsi_status == "Scaling Likely":
            recommendations.append({
                'type': 'scaling',
                'title': 'Optimize water treatment program',
                'description': 'Low RSI indicates scaling tendency. Review treatment chemicals.',
                'priority': 'medium'
            })
        
        elif self.rsi_status == "Corrosion Likely":
            recommendations.append({
                'type': 'corrosion',
                'title': 'Monitor system for corrosion',
                'description': 'High RSI indicates corrosion potential. Increase monitoring frequency.',
                'priority': 'medium'
            })
        
        # PSI-based recommendations
        if self.psi_status == "Water has a tendency to scale":
            recommendations.append({
                'type': 'scaling',
                'title': 'Address scaling tendency',
                'description': 'High PSI indicates scaling potential. Review treatment program.',
                'priority': 'medium'
            })
        elif self.psi_status == "Water has a tendency to corrode":
            recommendations.append({
                'type': 'corrosion',
                'title': 'Address corrosion tendency',
                'description': 'High PSI indicates corrosion potential. Add corrosion inhibitors.',
                'priority': 'medium'
            })
        
        # LR-based recommendations
        if self.lr_status == "The tendency towards high corrosion rates of a local type should be expected as the index increases":
            recommendations.append({
                'type': 'corrosion',
                'title': 'Address chloride and sulfate corrosion',
                'description': 'High Langelier Ratio indicates chloride/sulfate corrosion potential.',
                'priority': 'high'
            })
        
        # General recommendations
        if self.overall_status == "Unstable":
            recommendations.append({
                'type': 'monitoring',
                'title': 'Increase monitoring frequency',
                'description': 'Overall unstable conditions require more frequent monitoring.',
                'priority': 'high'
            })
        
        # Create recommendation objects
        for rec in recommendations:
            WaterRecommendation.objects.create(
                analysis=self,
                recommendation_type=rec['type'],
                title=rec['title'],
                description=rec['description'],
                priority=rec['priority']
            )


class WaterTrend(models.Model):
    """Historical water analysis trends."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_trends')
    parameter = models.CharField(max_length=50)  # ph, lsi, rsi, etc.
    value = models.DecimalField(max_digits=6, decimal_places=2)
    trend_date = models.DateField(default=timezone.now)
    analysis_id = models.IntegerField(null=True, blank=True, help_text="Reference to WaterAnalysis ID")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-trend_date', '-created_at']
        unique_together = ['user', 'parameter', 'analysis_id']  # Allow multiple per date
    
    def __str__(self):
        return f"{self.user.email} - {self.parameter}: {self.value} ({self.trend_date})"


class WaterRecommendation(models.Model):
    """Recommendations based on water analysis results."""
    RECOMMENDATION_TYPES = [
        ('scaling', 'Scaling Prevention'),
        ('corrosion', 'Corrosion Prevention'),
        ('treatment', 'Water Treatment'),
        ('monitoring', 'Monitoring'),
        ('maintenance', 'Maintenance'),
    ]
    
    analysis = models.ForeignKey(WaterAnalysis, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=[
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], default='medium')
    is_implemented = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.analysis.analysis_name} - {self.title}"


class AnalyticalScore(models.Model):
    """Calculated analytical scores based on technical data."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytical_scores')
    score_type = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=5, decimal_places=2)
    calculation_date = models.DateField(default=timezone.now)
    data_points_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-calculation_date', '-created_at']
        unique_together = ['user', 'score_type', 'calculation_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.score_type}: {self.value} ({self.calculation_date})"


class DataCalculation(models.Model):
    """Model to store calculation logic and formulas."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    formula = models.TextField(help_text="Python expression for calculation")
    categories_required = models.ManyToManyField(DataCategory, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def calculate_score(self, user, date=None):
        """Calculate score based on the formula and user's data."""
        if date is None:
            date = timezone.now().date()
        
        # Get required data for this calculation
        data_entries = TechnicalData.objects.filter(
            user=user,
            category__in=self.categories_required.all(),
            entry_date=date
        )
        
        if not data_entries.exists():
            return None
        
        # Create a context for the formula
        context = {}
        for entry in data_entries:
            context[entry.category.name.lower().replace(' ', '_')] = float(entry.value)
        
        try:
            # Safely evaluate the formula
            result = eval(self.formula, {"__builtins__": {}}, context)
            return round(result, 2)
        except Exception as e:
            print(f"Error calculating {self.name}: {e}")
            return None


# Predefined calculations
def create_default_calculations():
    """Create default calculation formulas."""
    calculations = [
        {
            'name': 'Efficiency Score',
            'description': 'Overall efficiency based on multiple parameters',
            'formula': 'min(100, (temperature * 0.3 + pressure * 0.4 + flow_rate * 0.3))',
        },
        {
            'name': 'Performance Index',
            'description': 'Performance indicator based on operational data',
            'formula': 'max(0, (output / input) * 100) if input > 0 else 0',
        },
        {
            'name': 'Quality Score',
            'description': 'Quality assessment based on defect rates',
            'formula': 'max(0, 100 - (defects / total_units * 100))',
        },
    ]
    
    for calc_data in calculations:
        DataCalculation.objects.get_or_create(
            name=calc_data['name'],
            defaults=calc_data
        )




