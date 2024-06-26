from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django_admin_listfilter_dropdown.filters import (
    ChoiceDropdownFilter,
    DropdownFilter,
    RelatedDropdownFilter,
)

from .models import Dealer, FtpConfig, Project, VdpImportSetup, VdpUrl, Webprovider


class UserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
    )


class DealerAdminView(admin.ModelAdmin):
    # list_filter = (
    #     # for ordinary fields
    #     ('account', DropdownFilter),
    #     # # for choice fields
    #     # ('a_choicefield', ChoiceDropdownFilter),
    #     # for related fields
    #     ('web_provider', RelatedDropdownFilter),
    # )
    list_per_page = 10
    list_max_show_all = 500
    list_filter = ('account', 'web_provider')

    list_display = (
        'accnt_status',
        'dealer_id',
        'dealer_name',
        'site_url',
        'web_provider',
        'account_manager',
        'date_created_fmt',
        'date_modified_fmt',
    )
    search_fields = [
        'account',
        'dealer_id',
        'dealer_name',
        'site_url',
        'web_provider__name',
        'account_manager',
    ]

    list_select_related = ['web_provider']

    list_display_links = (
        'dealer_id',
        'dealer_name',
    )

    @admin.display(description='Status', ordering='dealer__account')
    def accnt_status(self, obj):
        if obj.account == 'ACTIVE':
            color = '#28a745'
        elif obj.account == 'INACTIVE':
            color = '#fea95e'
        else:
            color = '#ff0000'
        return format_html(
            f'<strong> <p style="color:{color}">{obj.account}</p> </strong>'
        )

    # format date
    @admin.display(ordering='date_created', description='Date_Created')
    def date_created_fmt(self, obj):
        return obj.date_created.strftime("%Y-%m-%d") if obj.date_created else ''

    @admin.display(ordering='date_modified', description='Date_Modified')
    def date_modified_fmt(self, obj):
        return obj.date_modified.strftime("%Y-%m-%d") if obj.date_modified else ''

    def save_model(self, request, obj, form, change):
        # If the entry is being modified, set the modified_by field
        if change:
            obj.updated_by = request.user

        # If the entry is being added, set the author field
        else:
            obj.author = request.user

        # Save the object with the user information
        super().save_model(request, obj, form, change)


class WebProviderAdminView(admin.ModelAdmin):
    list_display = ('name', 'file_name')
    search_fields = ['name', 'file_name']


class VdpImportSetupAdminView(admin.ModelAdmin):
    # list_filter = (
    #     # for ordinary fields
    #     ('vdpurl_status', DropdownFilter),
    #     # # for choice fields
    #     # ('vdpurl_status', ChoiceDropdownFilter),
    #     # for related fields
    #     # ('dealer', RelatedDropdownFilter),
    # )

    list_per_page = 10
    list_max_show_all = 500
    list_filter = ['dealer__web_provider', 'vdpurl_status', 'setup']
    list_display_links = ('accnt_status', 'did')

    list_display = (
        'accnt_status',
        'did',
        'dealer_site',
        'dealer_web_provider',
        'vdpurl_status',
        'vdpurl_feed_id',
        'vdpurl_source_file',  # automatically updated value in pipelines
        'vdpurl_main_feed_src',
        'date_setup_fmt',  # search by : YYYY-MM-DD
        'last_run',
        'setup_status',
    )
    search_fields = [
        'dealer__account',
        'dealer__dealer_id',  # search parent's attribute via ForeignKey: __prefix
        'dealer__dealer_name',
        'vdpurl_status',
        'dealer__dealer_id',
        'vdpurl_feed_id',
        'vdpurl_source_file',
        'dealer__vdpurl__date_created',
        'setup',
    ]

    # function to color the account status text
    @admin.display(description='Status', ordering='dealer__account')
    def accnt_status(self, obj):
        if obj.dealer.account == 'ACTIVE':
            color = '#28a745'
        elif obj.dealer.account == 'INACTIVE':
            color = '#fea95e'
        else:
            color = '#ff0000'
        return format_html(
            f'<strong> <p style="color:{color}">{obj.dealer.account}</p> </strong>'
        )

    accnt_status.allow_tags = True

    @admin.display(ordering='dealer__dealer_id')
    def did(self, obj):
        return obj.dealer.pk

    # dealers and show site urls links
    @admin.display(description='Site', ordering='site_url')
    def dealer_site(self, obj):
        return format_html(
            f"<a href='{obj.dealer.site_url}' target='_blank'>{obj.dealer}</a>"
        )

    @admin.display(ordering='dealer__web_provider', description='Provider')
    def dealer_web_provider(self, obj):
        return obj.dealer.web_provider

    # format date
    @admin.display(ordering='vdpurl_date_setup', description='Date_Setup')
    def date_setup_fmt(self, obj):
        return (
            obj.vdpurl_date_setup.strftime("%Y-%m-%d") if obj.vdpurl_date_setup else ''
        )

    # Not being displayed atm ##
    @admin.display(ordering='vdpurl_date_modified', description='Date_Modified')
    def date_modified_fmt(self, obj):
        return (
            obj.vdpurl_date_modified.strftime("%Y-%m-%d")
            if obj.vdpurl_date_modified
            else ''
        )

    @admin.display(ordering='dealer__vdpurl__date_created', description='Last Run')
    def last_run(self, obj):
        try:
            return (
                VdpUrl.objects.filter(dealer__dealer_id=obj.dealer.dealer_id)
                .first()
                .date_created.strftime("%Y-%m-%d")
            )

        except Exception as e:
            return format_html(
                f'<strong> <p style="color:#ff0000">Error {e}!</p> </strong>'
            )

    # sort dealer's dropdown
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'dealer':
            kwargs["queryset"] = Dealer.objects.order_by('dealer_name')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # additional style at `admin-extra.css`
    @admin.display(ordering='setup', description='setup')
    def setup_status(self, obj):
        if obj.setup == 'moved':
            return format_html(f'<span class="status moved">{obj.setup}</span>')
        if obj.setup == 'down':
            return format_html(f'<span class="status down">{obj.setup}</span>')
        if obj.setup == 'dead':
            return format_html(f'<span class="status dead">{obj.setup}</span>')
        return format_html(f'<span class="status up">{obj.setup}</span>')


class VdpUrlAdminView(admin.ModelAdmin):

    list_display = [
        'dealer_id_or_dealer_name',
        'dealer_vdpurl_feed_id',
        'vin',
        'show_vehicle_url',
        'date_created_fmt',
    ]
    search_fields = [
        'dealer__dealer_name',  # search parent's attribute via ForeignKey
        'dealer__dealer_id',
        'dealer_vdpurl_feed_id',
        'vin',
        'vehicle_url',
        'date_created',
    ]

    # ordering also fixed sorting not working
    @admin.display(ordering='dealer__dealer_name')
    def dealer_id_or_dealer_name(self, obj):
        return f'{obj.dealer_id} - {obj.dealer}'

    # show vdp urls links
    @admin.display(description='VDP URLS')
    def show_vehicle_url(self, obj):
        return format_html(
            "<a href='{url}' target='_blank'>{url}</a>", url=obj.vehicle_url
        )

    @admin.display(ordering='date_created', description='Date_Created')
    def date_created_fmt(self, obj):
        return obj.date_created.strftime("%Y-%m-%d") if obj.date_created else ''


class VdpUrlConfigView(admin.ModelAdmin):
    list_display = [
        'provider_name',
        'file',
        'type',
        'method',
        'target_fields',
        'feed_ids',
    ]

    search_fields = [
        'provider',
        'file',
        'type',
        'method',
        'target_fields',
        'feed_ids',
    ]

    @admin.display(ordering='provider__name')
    def provider_name(self, obj):
        return f'{obj.provider.name}'

    def save_model(self, request, obj, form, change):
        # if the object is being changed (not created)
        # if change:

        if not obj.feed_ids:
            provider = VdpImportSetup.objects.filter(
                dealer__web_provider__name__iexact=str(obj.provider),
                dealer__account__iexact='active',
            ).all()
            feed_ids = list(
                set([id.vdpurl_feed_id for id in provider if bool(id.vdpurl_feed_id)])
            )
            obj.feed_ids = ','.join(feed_ids)
            obj.save()
        super(VdpUrlConfigView, self).save_model(request, obj, form, change)


# Re-register UserAdmin to customize use display info at admin ui
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Project)
admin.site.register(Dealer, DealerAdminView)
admin.site.register(Webprovider, WebProviderAdminView)
admin.site.register(VdpImportSetup, VdpImportSetupAdminView)
admin.site.register(VdpUrl, VdpUrlAdminView)
admin.site.register(FtpConfig, VdpUrlConfigView)


# change django admin header
admin.site.site_header = 'VDP Import'
admin.site.site_title = 'VDP Import'
admin.site.index_title = 'Admin Console'
