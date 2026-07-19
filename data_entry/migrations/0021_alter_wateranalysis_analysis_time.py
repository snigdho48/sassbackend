import data_entry.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_entry', '0020_wateranalysis_analysis_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wateranalysis',
            name='analysis_time',
            field=models.TimeField(default=data_entry.models.current_local_time),
        ),
    ]
