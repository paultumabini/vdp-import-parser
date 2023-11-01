# Generated by Django 4.1.5 on 2023-08-20 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vdpurls", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Config",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("provider", models.CharField(max_length=200, null=True)),
                ("file", models.CharField(max_length=200, null=True)),
                ("type", models.CharField(max_length=200, null=True)),
                ("method", models.CharField(max_length=200, null=True)),
                ("feed_ids", models.CharField(max_length=200, null=True)),
                ("target_fields", models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name="vdpimportsetup",
            name="vdpurl_date_setup",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]