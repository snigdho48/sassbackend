import django.utils.timezone
from django.db import migrations, models


def backfill_analysis_times(apps, schema_editor):
    WaterAnalysis = apps.get_model('data_entry', 'WaterAnalysis')
    for analysis in WaterAnalysis.objects.filter(analysis_time__isnull=True).iterator():
        created_at = analysis.created_at
        if django.utils.timezone.is_aware(created_at):
            created_at = django.utils.timezone.localtime(created_at)
        analysis.analysis_time = created_at.time().replace(tzinfo=None)
        analysis.save(update_fields=['analysis_time'])


class Migration(migrations.Migration):

    dependencies = [
        ('data_entry', '0019_add_cooling_temperature_and_total_alkalinity_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='wateranalysis',
            name='analysis_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_analysis_times, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='wateranalysis',
            name='analysis_time',
            field=models.TimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterModelOptions(
            name='wateranalysis',
            options={
                'ordering': ['-analysis_date', '-analysis_time', '-created_at'],
                'verbose_name_plural': 'Water Analyses',
            },
        ),
    ]
