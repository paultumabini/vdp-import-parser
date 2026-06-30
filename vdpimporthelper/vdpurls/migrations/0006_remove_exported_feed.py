# exported_feed duplicated vdpurl_source_file; merge then drop.
from django.db import migrations, models


def copy_exported_feed_to_source_file(apps, schema_editor):
    VdpImportSetup = apps.get_model('vdpurls', 'VdpImportSetup')
    for setup in VdpImportSetup.objects.exclude(exported_feed__isnull=True).exclude(
        exported_feed=''
    ):
        if not setup.vdpurl_source_file:
            setup.vdpurl_source_file = setup.exported_feed
            setup.save(update_fields=['vdpurl_source_file'])


class Migration(migrations.Migration):

    dependencies = [
        ('vdpurls', '0005_vdpimportsetup_vdp_url_count'),
    ]

    operations = [
        migrations.RunPython(
            copy_exported_feed_to_source_file,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='vdpimportsetup',
            name='exported_feed',
        ),
        migrations.AlterField(
            model_name='vdpimportsetup',
            name='vdpurl_source_file',
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
                verbose_name='Exported feed',
            ),
        ),
    ]
