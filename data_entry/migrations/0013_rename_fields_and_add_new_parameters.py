# Generated manually to handle field renames and new parameter additions

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_entry', '0012_plant_boiler_lsi_enabled_plant_boiler_lsi_max_and_more'),
    ]

    operations = [
        # Rename boiler_chlorides to boiler_sodium_chloride
        migrations.RenameField(
            model_name='plant',
            old_name='boiler_chlorides_max',
            new_name='boiler_sodium_chloride_max',
        ),
        migrations.RenameField(
            model_name='plant',
            old_name='boiler_chlorides_enabled',
            new_name='boiler_sodium_chloride_enabled',
        ),
        # Rename boiler_sulfite to boiler_sulphite
        migrations.RenameField(
            model_name='plant',
            old_name='boiler_sulfite_min',
            new_name='boiler_sulphite_min',
        ),
        migrations.RenameField(
            model_name='plant',
            old_name='boiler_sulfite_max',
            new_name='boiler_sulphite_max',
        ),
        migrations.RenameField(
            model_name='plant',
            old_name='boiler_sulfite_enabled',
            new_name='boiler_sulphite_enabled',
        ),
        # Add cooling_phosphate fields
        migrations.AddField(
            model_name='plant',
            name='cooling_phosphate_max',
            field=models.DecimalField(decimal_places=2, default=10.0, max_digits=6),
        ),
        migrations.AddField(
            model_name='plant',
            name='cooling_phosphate_enabled',
            field=models.BooleanField(default=False, help_text='Enable phosphate monitoring for this plant'),
        ),
        # Add boiler_do fields
        migrations.AddField(
            model_name='plant',
            name='boiler_do_min',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=6),
        ),
        migrations.AddField(
            model_name='plant',
            name='boiler_do_max',
            field=models.DecimalField(decimal_places=3, default=0.05, max_digits=6),
        ),
        migrations.AddField(
            model_name='plant',
            name='boiler_do_enabled',
            field=models.BooleanField(default=False, help_text='Enable dissolved oxygen monitoring for this plant'),
        ),
        # Add boiler_phosphate fields
        migrations.AddField(
            model_name='plant',
            name='boiler_phosphate_min',
            field=models.DecimalField(decimal_places=2, default=2.0, max_digits=6),
        ),
        migrations.AddField(
            model_name='plant',
            name='boiler_phosphate_max',
            field=models.DecimalField(decimal_places=2, default=10.0, max_digits=6),
        ),
        migrations.AddField(
            model_name='plant',
            name='boiler_phosphate_enabled',
            field=models.BooleanField(default=False, help_text='Enable phosphate monitoring for this plant'),
        ),
    ]
