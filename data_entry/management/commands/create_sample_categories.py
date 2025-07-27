from django.core.management.base import BaseCommand
from data_entry.models import DataCategory

class Command(BaseCommand):
    help = 'Create sample data categories'

    def handle(self, *args, **options):
        categories_data = [
            {
                'name': 'pH Level',
                'description': 'Acidity or alkalinity of water',
                'unit': 'pH',
                'min_value': 0,
                'max_value': 14,
                'is_active': True
            },
            {
                'name': 'Temperature',
                'description': 'Water temperature measurement',
                'unit': '°C',
                'min_value': 0,
                'max_value': 100,
                'is_active': True
            },
            {
                'name': 'Total Dissolved Solids',
                'description': 'Total dissolved solids in water',
                'unit': 'ppm',
                'min_value': 0,
                'max_value': 1000,
                'is_active': True
            },
            {
                'name': 'Hardness',
                'description': 'Water hardness as CaCO₃',
                'unit': 'ppm',
                'min_value': 0,
                'max_value': 500,
                'is_active': True
            },
            {
                'name': 'Alkalinity',
                'description': 'Total alkalinity as CaCO₃',
                'unit': 'ppm',
                'min_value': 0,
                'max_value': 300,
                'is_active': True
            },
            {
                'name': 'Chloride',
                'description': 'Chloride concentration',
                'unit': 'ppm',
                'min_value': 0,
                'max_value': 200,
                'is_active': True
            },
            {
                'name': 'Conductivity',
                'description': 'Electrical conductivity',
                'unit': 'μS/cm',
                'min_value': 0,
                'max_value': 2000,
                'is_active': True
            },
            {
                'name': 'Turbidity',
                'description': 'Water clarity measurement',
                'unit': 'NTU',
                'min_value': 0,
                'max_value': 10,
                'is_active': True
            }
        ]

        created_count = 0
        for category_data in categories_data:
            category, created = DataCategory.objects.get_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new categories')
        ) 