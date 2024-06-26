# Generated by Django 4.1.5 on 2024-06-21 16:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Dealer",
            fields=[
                (
                    "account",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "ACTIVE"),
                            ("INACTIVE", "INACTIVE"),
                            ("DELETED", "DELETED"),
                        ],
                        max_length=10,
                    ),
                ),
                ("dealer_id", models.IntegerField(primary_key=True, serialize=False)),
                ("dealer_name", models.CharField(max_length=200, null=True)),
                ("site_url", models.CharField(max_length=200, null=True)),
                (
                    "account_manager",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                ("fb_feed", models.IntegerField(blank=True, null=True)),
                ("url_new_percent", models.IntegerField(blank=True, null=True)),
                ("url_used_percent", models.IntegerField(blank=True, null=True)),
                ("new_vehicle", models.IntegerField(blank=True, null=True)),
                ("used_vehicle", models.IntegerField(blank=True, null=True)),
                ("date_created", models.DateTimeField(auto_now_add=True, null=True)),
                ("date_modified", models.DateTimeField(auto_now=True, null=True)),
                (
                    "author",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="author",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Project",
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
                ("name", models.CharField(max_length=200, null=True)),
                ("date_created", models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Webprovider",
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
                ("name", models.CharField(blank=True, max_length=200, null=True)),
                ("file_name", models.CharField(blank=True, max_length=200, null=True)),
                ("date_created", models.DateTimeField(auto_now_add=True, null=True)),
                ("date_modified", models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="VdpUrl",
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
                (
                    "dealer_vdpurl_feed_id",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("vin", models.CharField(blank=True, max_length=200, null=True)),
                (
                    "vehicle_url",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                ("date_created", models.DateTimeField(auto_now_add=True, null=True)),
                (
                    "dealer",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vdpurl",
                        to="vdpurls.dealer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="VdpImportSetup",
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
                (
                    "vdpurl_status",
                    models.CharField(
                        choices=[
                            ("approval_requested", "approval_requested"),
                            ("approval_received", "approval_received"),
                            ("export_file_requested", "export_file_requested"),
                            ("export_file_processing", "export_file_processing"),
                            ("export_file_ready", "export_file_ready"),
                            ("setup_in_progress", "setup_in_progress"),
                            ("setup_completed", "setup_completed"),
                            ("pending", "pending"),
                        ],
                        default="pending",
                        max_length=50,
                    ),
                ),
                (
                    "vdpurl_feed_id",
                    models.CharField(
                        blank=True, max_length=50, null=True, verbose_name="Feed ID"
                    ),
                ),
                (
                    "vdpurl_source_file",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        null=True,
                        verbose_name="FTP Src File",
                    ),
                ),
                (
                    "vdpurl_main_feed_src",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        null=True,
                        verbose_name="Main Feed Src",
                    ),
                ),
                (
                    "vdpurl_data_provider",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("WebProvider", "WebProvider"),
                            ("ExtremeScrape", "ExtremeScrape"),
                            ("Paul", "Paul"),
                            ("Liam", "Liam"),
                            ("None", "None"),
                        ],
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "vdpurl_date_setup",
                    models.DateTimeField(auto_now_add=True, null=True),
                ),
                (
                    "vdpurl_date_modified",
                    models.DateTimeField(auto_now=True, null=True),
                ),
                ("note", models.TextField(blank=True, null=True)),
                (
                    "setup",
                    models.CharField(
                        choices=[
                            ("down", "Down"),
                            ("up", "Up"),
                            ("moved", "Moved"),
                            ("dead", "Dead"),
                        ],
                        default="down",
                        max_length=50,
                    ),
                ),
                (
                    "dealer",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vdpsetup",
                        to="vdpurls.dealer",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="dealer",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="vdpurls.project",
            ),
        ),
        migrations.AddField(
            model_name="dealer",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_by",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="dealer",
            name="web_provider",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="web_provider",
                to="vdpurls.webprovider",
            ),
        ),
    ]
