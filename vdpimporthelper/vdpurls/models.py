from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Project(models.Model):
    name = models.CharField(max_length=200, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name or ''


class Webprovider(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    file_name = models.CharField(max_length=200, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return (
            self.name or ''
        )  # Solution for error msg: Error in admin: __str__ returned non-string (type NoneType). In this case, a webprovider_name is blank and must be removed or set to empty string!! Reference: https://stackoverflow.com/questions/42229923/error-in-admin-str-returned-non-string-type-nonetype

    class Meta:
        ordering = ('name',)


class Dealer(models.Model):
    ACCOUNT_STATUS = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('DELETED', 'DELETED'),
    )

    account = models.CharField(max_length=10, choices=ACCOUNT_STATUS)
    dealer_id = models.IntegerField(primary_key=True)
    dealer_name = models.CharField(max_length=200, null=True)
    site_url = models.CharField(max_length=200, null=True)
    web_provider = models.ForeignKey(Webprovider, on_delete=models.SET_NULL, related_name='web_provider', null=True, blank=True)
    account_manager = models.CharField(max_length=200, null=True, blank=True)
    fb_feed = models.IntegerField(null=True, blank=True)
    url_new_percent = models.IntegerField(null=True, blank=True)
    url_used_percent = models.IntegerField(null=True, blank=True)
    new_vehicle = models.IntegerField(null=True, blank=True)
    used_vehicle = models.IntegerField(null=True, blank=True)

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name='projects', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='author', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='updated_by', null=True, blank=True)

    def __str__(self):
        return str(self.dealer_name) or ''  # Solution for error msg: Error in admin: __str__ returned non-string (type NoneType)


class VdpImportSetup(models.Model):
    VDP_STATUS = (
        ('approval_requested', 'approval_requested'),
        ('approval_received', 'approval_received'),
        ('export_file_requested', 'export_file_requested'),
        ('export_file_processing', 'export_file_processing'),
        ('export_file_ready', 'export_file_ready'),
        ('setup_in_progress', 'setup_in_progress'),
        ('setup_completed', 'setup_completed'),
        ('pending', 'pending'),
    )

    DATA_PROVIDER = (
        ('WebProvider', 'WebProvider'),
        ('ExtremeScrape', 'ExtremeScrape'),
        ('Paul', 'Paul'),
        ('Liam', 'Liam'),
        ('None', 'None'),
    )

    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='vdpsetup', null=True)
    vdpurl_status = models.CharField(max_length=50, choices=VDP_STATUS, default='pending')
    vdpurl_feed_id = models.CharField(max_length=50, verbose_name='Feed ID', null=True, blank=True)
    vdpurl_source_file = models.CharField(max_length=200, verbose_name='FTP Src File', null=True, blank=True)
    vdpurl_main_feed_src = models.CharField(max_length=200, verbose_name='Main Feed Src', null=True, blank=True)
    vdpurl_data_provider = models.CharField(max_length=50, choices=DATA_PROVIDER, null=True, blank=True)
    vdpurl_date_setup = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    vdpurl_date_modified = models.DateTimeField(auto_now=True, null=True)
    note = models.TextField(null=True, blank=True)
    setup = models.CharField(
        max_length=50,
        choices=(
            ('down', 'Down'),
            ('up', 'Up'),
            ('moved', 'Moved'),
            ('dead', 'Dead'),
        ),
        default='down',
    )

    def __str__(self):
        return str(self.dealer) or ''  # Solution for error msg: Error in admin: __str__ returned non-string (type NoneType)


class VdpUrl(models.Model):
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name='vdpurl', null=True)
    dealer_vdpurl_feed_id = models.CharField(max_length=100, null=True, blank=True)
    vin = models.CharField(max_length=200, null=True, blank=True)
    vehicle_url = models.CharField(max_length=200, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return str(self.dealer)

    def save(self, *args, **kwargs):
        # Auto-change  VdpImportSetup.setup
        try:
            self.date_created
            objects = VdpImportSetup.objects.filter(dealer__dealer_id=self.dealer.dealer_id)
            for object in objects:
                object.setup = 'up'
                object.save()
        except:
            pass  # self.dealer.dealer_id does not exist here!

        super(VdpUrl, self).save(*args, **kwargs)


class Config(models.Model):
    provider = models.CharField(max_length=200, null=True)
    file = models.CharField(max_length=200, null=True)
    type = models.CharField(max_length=200, null=True)
    method = models.CharField(max_length=200, null=True)
    feed_ids = models.CharField(
        max_length=200,
        null=True,
        verbose_name='Feed Ids (comma-separted list values)',
    )
    target_fields = models.CharField(
        max_length=200,
        null=True,
        verbose_name='Target Fields (comma-separted list values)',
    )
