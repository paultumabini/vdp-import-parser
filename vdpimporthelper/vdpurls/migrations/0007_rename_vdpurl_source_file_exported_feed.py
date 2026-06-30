from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vdpurls', '0006_remove_exported_feed'),
    ]

    operations = [
        migrations.RenameField(
            model_name='vdpimportsetup',
            old_name='vdpurl_source_file',
            new_name='exported_feed',
        ),
    ]
