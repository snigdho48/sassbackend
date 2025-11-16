# Generated manually to make all plant parameters optional

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_entry', '0016_plant_owners_alter_plant_owner'),
    ]

    operations = [
        # Cooling water parameters
        migrations.AlterField(
            model_name='plant',
            name='cooling_ph_min',
            field=models.DecimalField(decimal_places=2, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_ph_max',
            field=models.DecimalField(decimal_places=2, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_tds_min',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_tds_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_hardness_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_alkalinity_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_chloride_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_cycle_min',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_cycle_max',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_iron_max',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_phosphate_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_lsi_min',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_lsi_max',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_rsi_min',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='cooling_rsi_max',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
        # Boiler water parameters
        migrations.AlterField(
            model_name='plant',
            name='boiler_ph_min',
            field=models.DecimalField(decimal_places=2, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_ph_max',
            field=models.DecimalField(decimal_places=2, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_tds_min',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_tds_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_hardness_max',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_alkalinity_min',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_alkalinity_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_p_alkalinity_min',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_p_alkalinity_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_oh_alkalinity_min',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_oh_alkalinity_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_sulphite_min',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_sulphite_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_sodium_chloride_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_do_min',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_do_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_phosphate_min',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_phosphate_max',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plant',
            name='boiler_iron_max',
            field=models.DecimalField(decimal_places=1, max_digits=4, null=True, blank=True),
        ),
    ]






