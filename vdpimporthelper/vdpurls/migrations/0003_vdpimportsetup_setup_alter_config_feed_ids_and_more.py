# Generated by Django 4.1.5 on 2023-10-20 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vdpurls", "0002_config_alter_vdpimportsetup_vdpurl_date_setup"),
    ]

    operations = [
        migrations.AddField(
            model_name="vdpimportsetup",
            name="setup",
            field=models.CharField(
                choices=[("pending", "Pending"), ("error", "Error"), ("good", "Good")],
                default="pending",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="feed_ids",
            field=models.CharField(
                max_length=200,
                null=True,
                verbose_name="Feed Ids (comma-separted list values)",
            ),
        ),
        migrations.AlterField(
            model_name="config",
            name="target_fields",
            field=models.CharField(
                max_length=200,
                null=True,
                verbose_name="Target Fields (comma-separted list values)",
            ),
        ),
    ]
