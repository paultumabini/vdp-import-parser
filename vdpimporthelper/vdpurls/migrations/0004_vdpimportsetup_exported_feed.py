# Stores the last successful FTP export filename per VdpImportSetup (see ImportSourcePipeline).
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vdpurls', '0003_alter_ftpconfig_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vdpimportsetup',
            name='exported_feed',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
