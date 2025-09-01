from django.core.management.base import BaseCommand
from data_entry.models import Plant


class Command(BaseCommand):
    help = 'Create sample plants for testing'

    def handle(self, *args, **options):
        # Sample Plant 1: Power Plant A
        plant1, created = Plant.objects.get_or_create(
            name="Power Plant A",
                    defaults={
            'is_active': True,
                # Cooling water parameters
                'cooling_ph_min': 6.8,
                'cooling_ph_max': 8.2,
                'cooling_tds_min': 600,
                'cooling_tds_max': 900,
                'cooling_hardness_max': 250,
                'cooling_alkalinity_max': 280,
                'cooling_chloride_max': 200,
                'cooling_cycle_min': 6.0,
                'cooling_cycle_max': 9.0,
                'cooling_iron_max': 2.5,
                # Boiler water parameters
                'boiler_ph_min': 10.8,
                'boiler_ph_max': 11.8,
                'boiler_tds_min': 2800,
                'boiler_tds_max': 3800,
                'boiler_hardness_max': 1.5,
                'boiler_alkalinity_min': 700,
                'boiler_alkalinity_max': 1500,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created plant: {plant1.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Plant already exists: {plant1.name}')
            )

        # Sample Plant 2: Chemical Plant B
        plant2, created = Plant.objects.get_or_create(
            name="Chemical Plant B",
                    defaults={
            'is_active': True,
                # Cooling water parameters
                'cooling_ph_min': 7.0,
                'cooling_ph_max': 8.5,
                'cooling_tds_min': 400,
                'cooling_tds_max': 700,
                'cooling_hardness_max': 180,
                'cooling_alkalinity_max': 220,
                'cooling_chloride_max': 150,
                'cooling_cycle_min': 4.5,
                'cooling_cycle_max': 7.5,
                'cooling_iron_max': 2.0,
                # Boiler water parameters
                'boiler_ph_min': 11.0,
                'boiler_ph_max': 12.0,
                'boiler_tds_min': 3000,
                'boiler_tds_max': 4000,
                'boiler_hardness_max': 1.0,
                'boiler_alkalinity_min': 800,
                'boiler_alkalinity_max': 1600,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created plant: {plant2.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Plant already exists: {plant2.name}')
            )

        # Sample Plant 3: Refinery C
        plant3, created = Plant.objects.get_or_create(
            name="Refinery C",
                    defaults={
            'is_active': True,
                # Cooling water parameters
                'cooling_ph_min': 6.5,
                'cooling_ph_max': 7.8,
                'cooling_tds_min': 500,
                'cooling_tds_max': 800,
                'cooling_hardness_max': 300,
                'cooling_alkalinity_max': 300,
                'cooling_chloride_max': 250,
                'cooling_cycle_min': 5.0,
                'cooling_cycle_max': 8.0,
                'cooling_iron_max': 3.0,
                # Boiler water parameters
                'boiler_ph_min': 10.5,
                'boiler_ph_max': 11.5,
                'boiler_tds_min': 2500,
                'boiler_tds_max': 3500,
                'boiler_hardness_max': 2.0,
                'boiler_alkalinity_min': 600,
                'boiler_alkalinity_max': 1400,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created plant: {plant3.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Plant already exists: {plant3.name}')
            )

        self.stdout.write(
            self.style.SUCCESS('Sample plants creation completed!')
        )
