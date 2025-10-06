from django.core.management.base import BaseCommand
from data_entry.models import Plant


class Command(BaseCommand):
    help = 'Fix NULL values in plant optional fields by setting default values'

    def handle(self, *args, **options):
        # Get all plants that might have NULL values in optional fields
        plants = Plant.objects.all()
        
        updated_count = 0
        
        for plant in plants:
            needs_update = False
            
            # Fix cooling water optional fields
            if plant.cooling_chloride_enabled is None:
                plant.cooling_chloride_enabled = False
                needs_update = True
                
            if plant.cooling_cycle_enabled is None:
                plant.cooling_cycle_enabled = False
                needs_update = True
                
            if plant.cooling_iron_enabled is None:
                plant.cooling_iron_enabled = False
                needs_update = True
            
            # Fix boiler water optional fields
            if plant.boiler_p_alkalinity_enabled is None:
                plant.boiler_p_alkalinity_enabled = False
                needs_update = True
                
            if plant.boiler_oh_alkalinity_enabled is None:
                plant.boiler_oh_alkalinity_enabled = False
                needs_update = True
                
            if plant.boiler_sulfite_enabled is None:
                plant.boiler_sulfite_enabled = False
                needs_update = True
                
            if plant.boiler_chlorides_enabled is None:
                plant.boiler_chlorides_enabled = False
                needs_update = True
                
            if plant.boiler_iron_enabled is None:
                plant.boiler_iron_enabled = False
                needs_update = True
            
            # Save if any updates were made
            if needs_update:
                plant.save()
                updated_count += 1
                self.stdout.write(f'Updated plant: {plant.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} plants')
        )
