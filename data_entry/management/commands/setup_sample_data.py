from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from data_entry.models import DataCategory, TechnicalData, AnalyticalScore
from reports.models import ReportTemplate, GeneratedReport
from dashboard.models import DashboardWidget, UserPreference
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up sample data for the SaaS platform'

    def handle(self, *args, **options):
        self.stdout.write('Setting up sample data...')

        # Create sample users
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'company': 'SaaS Platform',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user')

        client_user, created = User.objects.get_or_create(
            email='client@example.com',
            defaults={
                'username': 'client',
                'first_name': 'John',
                'last_name': 'Client',
                'role': 'client',
                'company': 'Client Corp',
            }
        )
        if created:
            client_user.set_password('client123')
            client_user.save()
            self.stdout.write('Created client user')

        # Create data categories
        categories = [
            {'name': 'Temperature', 'description': 'Temperature measurements', 'unit': '°C'},
            {'name': 'Pressure', 'description': 'Pressure readings', 'unit': 'PSI'},
            {'name': 'Flow Rate', 'description': 'Flow rate measurements', 'unit': 'L/min'},
            {'name': 'Quality', 'description': 'Quality control data', 'unit': '%'},
            {'name': 'Vibration', 'description': 'Vibration analysis', 'unit': 'mm/s'},
        ]

        for cat_data in categories:
            category, created = DataCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create sample technical data
        categories = DataCategory.objects.all()
        users = [admin_user, client_user]

        # Generate unique dates for each entry
        used_dates = set()
        entries_created = 0
        max_attempts = 100

        for i in range(50):
            attempts = 0
            while attempts < max_attempts:
                user = random.choice(users)
                category = random.choice(categories)
                entry_date = timezone.now().date() - timedelta(days=random.randint(0, 30))
                
                # Create a unique key for this combination
                date_key = (user.id, category.id, entry_date)
                
                if date_key not in used_dates:
                    used_dates.add(date_key)
                    
                    # Generate realistic data based on category
                    if category.name == 'Temperature':
                        value = random.uniform(20, 80)
                    elif category.name == 'Pressure':
                        value = random.uniform(10, 50)
                    elif category.name == 'Flow Rate':
                        value = random.uniform(5, 25)
                    elif category.name == 'Quality':
                        value = random.uniform(85, 99)
                    else:  # Vibration
                        value = random.uniform(0.1, 2.0)

                    # Create data entry
                    data_entry, created = TechnicalData.objects.get_or_create(
                        user=user,
                        category=category,
                        entry_date=entry_date,
                        defaults={
                            'value': value,
                            'notes': f'Sample data entry {i+1}',
                        }
                    )

                    if created:
                        entries_created += 1
                        
                        # Create analytical score
                        analytical_score = random.uniform(70, 95)
                        AnalyticalScore.objects.get_or_create(
                            user=user,
                            score_type=f'{category.name}_score',
                            calculation_date=entry_date,
                            defaults={
                                'value': analytical_score,
                                'data_points_used': 1
                            }
                        )
                    break
                attempts += 1

        self.stdout.write(f'Created {entries_created} sample technical data entries')

        # Create report templates
        templates = [
            {'name': 'Daily Report', 'description': 'Daily operational report', 'report_type': 'daily'},
            {'name': 'Weekly Summary', 'description': 'Weekly summary report', 'report_type': 'weekly'},
            {'name': 'Monthly Analysis', 'description': 'Monthly analysis report', 'report_type': 'monthly'},
        ]

        for template_data in templates:
            template, created = ReportTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                self.stdout.write(f'Created report template: {template.name}')

        # Create sample generated reports
        templates = ReportTemplate.objects.all()
        for i in range(10):
            template = random.choice(templates)
            user = random.choice(users)
            
            GeneratedReport.objects.get_or_create(
                title=f'{template.name} - {timezone.now().strftime("%Y-%m-%d")}',
                defaults={
                    'user': user,
                    'template': template,
                    'file_path': f'/media/reports/{template.name.lower().replace(" ", "_")}_{i+1}.pdf',
                    'parameters': {'date_range': '30', 'include_charts': True},
                }
            )

        self.stdout.write('Created sample reports')

        # Create dashboard widgets
        widgets = [
            {'title': 'Recent Entries', 'widget_type': 'chart', 'position': 1},
            {'title': 'Analytics Chart', 'widget_type': 'chart', 'position': 2},
            {'title': 'Quick Stats', 'widget_type': 'metric', 'position': 3},
        ]

        for widget_data in widgets:
            widget, created = DashboardWidget.objects.get_or_create(
                title=widget_data['title'],
                user=admin_user,
                defaults=widget_data
            )
            if created:
                self.stdout.write(f'Created dashboard widget: {widget.title}')

        # Create user preferences
        for user in users:
            UserPreference.objects.get_or_create(
                user=user,
                defaults={
                    'theme': 'light',
                    'language': 'en',
                    'timezone': 'UTC',
                    'notifications_enabled': True,
                    'email_notifications': True,
                }
            )

        self.stdout.write('Created user preferences')

        self.stdout.write(
            self.style.SUCCESS('Sample data setup completed successfully!')
        )
        self.stdout.write('\nSample users:')
        self.stdout.write('Admin: admin@example.com / admin123')
        self.stdout.write('Client: client@example.com / client123') 