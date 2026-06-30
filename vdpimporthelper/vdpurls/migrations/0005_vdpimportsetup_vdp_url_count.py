# VdpUrl count from the last successful import run (see ImportSourcePipeline).
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('vdpurls', '0004_vdpimportsetup_exported_feed'),
    ]

    operations = [
        migrations.AddField(
            model_name='vdpimportsetup',
            name='vdp_url_count',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
