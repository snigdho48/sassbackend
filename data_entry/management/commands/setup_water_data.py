from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from data_entry.models import WaterAnalysis, WaterTrend, WaterRecommendation

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup sample water analysis data including trends and recommendations'

    def handle(self, *args, **options):
        self.stdout.write('Setting up water analysis data...')
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            email='www.atik48@gmail.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password('1234')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create sample water analyses
        sample_analyses = [
            {
                'analysis_name': 'Daily Water Analysis - Morning',
                'ph': 7.2,
                'tds': 150,
                'total_alkalinity': 120,
                'hardness': 180,
                'chloride': 25,
                'temperature': 25,
                'notes': 'Morning sample analysis'
            },
            {
                'analysis_name': 'Daily Water Analysis - Afternoon',
                'ph': 7.5,
                'tds': 160,
                'total_alkalinity': 125,
                'hardness': 185,
                'chloride': 28,
                'temperature': 28,
                'notes': 'Afternoon sample analysis'
            },
            {
                'analysis_name': 'Weekly Comprehensive Analysis',
                'ph': 7.8,
                'tds': 175,
                'total_alkalinity': 130,
                'hardness': 190,
                'chloride': 30,
                'temperature': 26,
                'notes': 'Weekly comprehensive water quality assessment'
            },
            {
                'analysis_name': 'Monthly Quality Check',
                'ph': 7.1,
                'tds': 145,
                'total_alkalinity': 118,
                'hardness': 175,
                'chloride': 22,
                'temperature': 24,
                'notes': 'Monthly quality control analysis'
            }
        ]
        
        created_analyses = []
        for analysis_data in sample_analyses:
            analysis = WaterAnalysis.objects.create(
                user=admin_user,
                **analysis_data
            )
            analysis.calculate_indices()
            analysis.save()
            created_analyses.append(analysis)
            self.stdout.write(f'Created analysis: {analysis.analysis_name}')
        
        # Create sample trends for the last 30 days
        parameters = ['ph', 'lsi', 'rsi', 'ls']
        base_values = {
            'ph': 7.2,
            'lsi': -0.1,
            'rsi': 6.8,
            'ls': 0.2
        }
        
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            for param in parameters:
                # Add some variation to make trends realistic
                variation = random.uniform(-0.3, 0.3)
                if param == 'ph':
                    value = base_values[param] + variation
                elif param == 'lsi':
                    value = base_values[param] + variation
                elif param == 'rsi':
                    value = base_values[param] + variation
                else:  # ls
                    value = base_values[param] + variation
                
                WaterTrend.objects.create(
                    user=admin_user,
                    parameter=param,
                    value=value,
                    trend_date=date
                )
        
        self.stdout.write(f'Created {30 * len(parameters)} trend data points')
        
        # Create sample recommendations
        sample_recommendations = [
            {
                'recommendation_type': 'treatment',
                'title': 'pH Adjustment Recommended',
                'description': 'Current pH levels are slightly high. Consider adding pH reducer to maintain optimal levels between 7.0-7.4.',
                'priority': 'high'
            },
            {
                'recommendation_type': 'monitoring',
                'title': 'Increase Monitoring Frequency',
                'description': 'LSI values show slight variation. Increase monitoring frequency to daily checks for the next week.',
                'priority': 'medium'
            },
            {
                'recommendation_type': 'maintenance',
                'title': 'System Maintenance Due',
                'description': 'RSI values indicate scaling potential. Schedule system maintenance within the next 2 weeks.',
                'priority': 'medium'
            },
            {
                'recommendation_type': 'treatment',
                'title': 'Chloride Levels Acceptable',
                'description': 'Chloride levels are within acceptable range. No immediate action required.',
                'priority': 'low'
            },
            {
                'recommendation_type': 'optimization',
                'title': 'Temperature Optimization',
                'description': 'Consider adjusting temperature settings to maintain optimal LSI values.',
                'priority': 'medium'
            }
        ]
        
        for rec_data in sample_recommendations:
            # Associate with the first analysis
            if created_analyses:
                recommendation = WaterRecommendation.objects.create(
                    analysis=created_analyses[0],
                    **rec_data
                )
                self.stdout.write(f'Created recommendation: {recommendation.title}')
        
        self.stdout.write(self.style.SUCCESS('Successfully set up water analysis data!'))
        self.stdout.write(f'Created {len(created_analyses)} analyses')
        self.stdout.write(f'Created {len(sample_recommendations)} recommendations')
        self.stdout.write(f'Created {30 * len(parameters)} trend data points') 