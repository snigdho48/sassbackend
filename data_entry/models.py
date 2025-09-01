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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Plant-specific parameter ranges for cooling water
    cooling_ph_min = models.DecimalField(max_digits=4, decimal_places=2, default=6.5)
    cooling_ph_max = models.DecimalField(max_digits=4, decimal_places=2, default=7.8)
    cooling_tds_min = models.DecimalField(max_digits=6, decimal_places=2, default=500)
    cooling_tds_max = models.DecimalField(max_digits=6, decimal_places=2, default=800)
    cooling_hardness_max = models.DecimalField(max_digits=6, decimal_places=2, default=300)
    cooling_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, default=300)
    cooling_chloride_max = models.DecimalField(max_digits=6, decimal_places=2, default=250)
    cooling_cycle_min = models.DecimalField(max_digits=4, decimal_places=1, default=5.0)
    cooling_cycle_max = models.DecimalField(max_digits=4, decimal_places=1, default=8.0)
    cooling_iron_max = models.DecimalField(max_digits=4, decimal_places=1, default=3.0)
    
    # Plant-specific parameter ranges for boiler water
    boiler_ph_min = models.DecimalField(max_digits=4, decimal_places=2, default=10.5)
    boiler_ph_max = models.DecimalField(max_digits=4, decimal_places=2, default=11.5)
    boiler_tds_min = models.DecimalField(max_digits=6, decimal_places=2, default=2500)
    boiler_tds_max = models.DecimalField(max_digits=6, decimal_places=2, default=3500)
    boiler_hardness_max = models.DecimalField(max_digits=4, decimal_places=1, default=2.0)
    boiler_alkalinity_min = models.DecimalField(max_digits=6, decimal_places=2, default=600)
    boiler_alkalinity_max = models.DecimalField(max_digits=6, decimal_places=2, default=1400)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_cooling_parameters(self):
        """Get cooling water parameters for this plant."""
        return {
            'ph': {'min': self.cooling_ph_min, 'max': self.cooling_ph_max},
            'tds': {'min': self.cooling_tds_min, 'max': self.cooling_tds_max},
            'hardness': {'max': self.cooling_hardness_max},
            'alkalinity': {'max': self.cooling_alkalinity_max},
            'chloride': {'max': self.cooling_chloride_max},
            'cycle': {'min': self.cooling_cycle_min, 'max': self.cooling_cycle_max},
            'iron': {'max': self.cooling_iron_max}
        }
    
    def get_boiler_parameters(self):
        """Get boiler water parameters for this plant."""
        return {
            'ph': {'min': self.boiler_ph_min, 'max': self.boiler_ph_max},
            'tds': {'min': self.boiler_tds_min, 'max': self.boiler_tds_max},
            'hardness': {'max': self.boiler_hardness_max},
            'alkalinity': {'min': self.boiler_alkalinity_min, 'max': self.boiler_alkalinity_max}
        }


class WaterAnalysis(models.Model):
    """Water analysis data for stability calculations."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_analyses')
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='water_analyses', null=True, blank=True)
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
    
    # Boiler Water Specific Parameters
    m_alkalinity = models.DecimalField(max_digits=6, decimal_places=2, help_text="M-Alkalinity as CaCO₃ (ppm)", null=True, blank=True)
    
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
            # Convert Decimal fields to float for calculations
            ph = float(self.ph)
            tds = float(self.tds)
            total_alkalinity = float(self.total_alkalinity) if self.total_alkalinity else 0
            hardness = float(self.hardness)
            chloride = float(self.chloride) if self.chloride else 0
            temperature = float(self.temperature) if self.temperature else 25
            sulphate = float(self.sulphate) if self.sulphate else 0
            
            # Langelier Saturation Index (LSI)
            # LSI = pH - pHs
            # pHs = (9.3 + A + B) - (C + D)
            # Where A, B, C, D are temperature and TDS dependent factors
            
            # Simplified LSI calculation
            temp_factor = 0.1 * (temperature - 25)
            tds_factor = 0.01 * (tds - 150)
            phs = 9.3 + temp_factor + tds_factor
            self.lsi = ph - phs
            
            # Ryznar Stability Index (RSI)
            # RSI = 2 * pHs - pH
            self.rsi = 2 * phs - ph
            
            # Puckorius Scaling Index (PSI)
            # PSI = 2 * pHs - pH
            self.psi = 2 * phs - ph
            
            # Langelier Ratio (LR)
            # LR = (Cl + SO4) / (HCO3)
            if total_alkalinity > 0:
                self.lr = (chloride + sulphate) / total_alkalinity
            else:
                self.lr = 0
            
            # Determine status
            self.lsi_status = self._get_lsi_status()
            self.rsi_status = self._get_rsi_status()
            self.psi_status = self._get_psi_status()
            self.lr_status = self._get_lr_status()
            self.overall_status = self._get_cooling_overall_status()
            
            # Calculate stability score (0-100)
            self.stability_score = self._calculate_cooling_stability_score()
            
        except Exception as e:
            print(f"Error calculating cooling indices: {e}")
    
    def _calculate_boiler_stability_score(self):
        """Calculate stability score for boiler water."""
        try:
            ph = float(self.ph)
            tds = float(self.tds)
            hardness = float(self.hardness)
            m_alkalinity = float(self.m_alkalinity) if self.m_alkalinity else 0
            
            # Start with 100 points
            score = 100
            
            # pH deduction (ideal range 10.5-11.5)
            if ph < 10.5 or ph > 11.5:
                deviation = abs(ph - 11.0)  # deviation from ideal center
                points_to_deduct = (deviation / 0.1) * 5
                score -= points_to_deduct
            
            # TDS deduction (ideal range 2500-3500)
            if tds < 2500 or tds > 3500:
                if tds > 4000:
                    score -= 20
                else:
                    score -= 10
            
            # Hardness deduction (ideal ≤ 2)
            if hardness > 2:
                if hardness > 5:
                    score -= 20
                else:
                    score -= 10
            
            # M-Alkalinity deduction (ideal range 250-600)
            if m_alkalinity < 250 or m_alkalinity > 600:
                deviation = abs(m_alkalinity - 425)  # deviation from ideal center
                points_to_deduct = (deviation / 50) * 2
                score -= points_to_deduct
            
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
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-trend_date']
        unique_together = ['user', 'parameter', 'trend_date']
    
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




