from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.db.models import DateTimeField, OuterRef, Subquery
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .forms import FtpConfigForm
from .models import Dealer, FtpConfig, Project, VdpImportSetup, VdpUrl, Webprovider


class UserAdmin(DjangoUserAdmin):
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
    list_filter = ('account_status', 'web_provider')

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
        'account_status',
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

    @admin.display(description='Status', ordering='account_status')
    def accnt_status(self, obj):
        # Keep color mapping centralized for predictable admin UX.
        if obj.account_status == 'ACTIVE':
            color = '#28a745'
        elif obj.account_status == 'INACTIVE':
            color = '#fea95e'
        else:
            color = '#ff0000'
        return format_html(
            '<strong><p style="color:{}">{}</p></strong>',
            color,
            obj.account_status,
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
    # ``exported_feed`` is pipeline-written only; admin shows a styled read-only chip.
    readonly_fields = ('display_exported_feed',)
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
    actions = ['sync_vdp_url_counts']
    list_display_links = ('accnt_status', 'did')

    list_display = (
        'accnt_status',
        'did',
        'dealer_site',
        'dealer_web_provider',
        'vdpurl_status',
        'vdpurl_feed_id',
        'display_exported_feed',
        'display_vdp_url_count',
        'vdpurl_main_feed_src',
        'date_setup_fmt',  # search by : YYYY-MM-DD
        'last_run',
        'setup_status',
    )
    search_fields = [
        'dealer__account_status',
        'dealer__dealer_id',  # search parent's attribute via ForeignKey: __prefix
        'dealer__dealer_name',
        'vdpurl_status',
        'dealer__dealer_id',
        'vdpurl_feed_id',
        'exported_feed',
        'dealer__vdpurl__date_created',
        'setup',
    ]

    @admin.action(description='Sync VDP URL counts from latest import run')
    def sync_vdp_url_counts(self, request, queryset):
        synced = VdpImportSetup.sync_all_vdp_url_counts()
        self.message_user(request, f'Synced VDP URL counts for {synced} setup(s).')

    def _ordering_includes_vdp_url_count(self, request) -> bool:
        # Admin ``o`` is dot-separated, 1-based ``list_display`` indices (e.g. ``8.9``).
        order_param = request.GET.get('o', '')
        if not order_param:
            return False
        for part in order_param.split('.'):
            try:
                column = abs(int(part))
                if self.list_display[column - 1] == 'display_vdp_url_count':
                    return True
            except (ValueError, IndexError):
                continue
        return False

    def changelist_view(self, request, extra_context=None):
        # Sort uses ``vdp_url_count`` in the DB; refresh before sort so order matches display.
        self._vdp_url_count_sorted = self._ordering_includes_vdp_url_count(request)
        if self._vdp_url_count_sorted:
            VdpImportSetup.sync_all_vdp_url_counts()
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        # Latest VdpUrl timestamp per dealer via subquery — avoids joining every
        # vehicle row (slow on large tables, especially for pagination count()).
        last_run_date = Subquery(
            VdpUrl.objects.filter(dealer_id=OuterRef('dealer_id'))
            .order_by('-date_created')
            .values('date_created')[:1],
            output_field=DateTimeField(),
        )
        return (
            super()
            .get_queryset(request)
            .select_related('dealer', 'dealer__web_provider')
            .annotate(last_run_date=last_run_date)
        )

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        # Reverse FK in search_fields can still multiply rows; keep one row per setup.
        return queryset, True

    # function to color the account status text
    @admin.display(description='Status', ordering='dealer__account_status')
    def accnt_status(self, obj):
        if not obj.dealer:
            return ''
        if obj.dealer.account_status == 'ACTIVE':
            color = '#28a745'
        elif obj.dealer.account_status == 'INACTIVE':
            color = '#fea95e'
        else:
            color = '#ff0000'
        return format_html(
            '<strong><p style="color:{}">{}</p></strong>',
            color,
            obj.dealer.account_status,
        )

    @admin.display(ordering='dealer__dealer_id')
    def did(self, obj):
        return obj.dealer.pk if obj.dealer else None

    # dealers and show site urls links
    @admin.display(description='Site', ordering='dealer__site_url')
    def dealer_site(self, obj):
        if not obj.dealer or not obj.dealer.site_url:
            return ''
        return format_html(
            "<a href='{}' target='_blank'>{}</a>",
            obj.dealer.site_url,
            obj.dealer,
        )

    @admin.display(ordering='dealer__web_provider', description='Provider')
    def dealer_web_provider(self, obj):
        return obj.dealer.web_provider if obj.dealer else None

    # Sort on stored ``vdp_url_count``; counts are bulk-synced in changelist_view when sorting.
    @admin.display(description='VDP URL count', ordering='vdp_url_count')
    def display_vdp_url_count(self, obj):
        if obj.vdp_url_count is not None:
            return obj.vdp_url_count
        if getattr(self, '_vdp_url_count_sorted', False):
            return 0
        if not obj.dealer_id:
            return 0
        return VdpUrl.recent_count_for_dealer(obj.dealer_id)

    # Read-only view of ``VdpImportSetup.exported_feed`` (set by ImportSourcePipeline).
    @admin.display(description='Exported feed', ordering='exported_feed')
    def display_exported_feed(self, obj):
        if obj.exported_feed:
            return format_html(
                '<span class="exported-feed-pill exported-feed-pill--set" '
                'title="Last FTP export">{}</span>',
                obj.exported_feed,
            )
        return mark_safe(
            '<span class="exported-feed-pill exported-feed-pill--empty" '
            'title="No feed exported yet">None</span>'
        )

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

    @admin.display(ordering='last_run_date', description='Last Run')
    def last_run(self, obj):
        if not obj.last_run_date:
            return ''
        return obj.last_run_date.strftime('%Y-%m-%d')

    # sort dealer's dropdown
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'dealer':
            kwargs["queryset"] = Dealer.objects.order_by('dealer_name')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # additional style at `admin-extra.css`
    @admin.display(ordering='setup', description='setup')
    def setup_status(self, obj):
        if obj.setup == 'moved':
            return format_html('<span class="status moved">{}</span>', obj.setup)
        if obj.setup == 'down':
            return format_html('<span class="status down">{}</span>', obj.setup)
        if obj.setup == 'dead':
            return format_html('<span class="status dead">{}</span>', obj.setup)
        return format_html('<span class="status up">{}</span>', obj.setup)


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

    form = FtpConfigForm
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

    @admin.display(ordering='provider')
    def provider_name(self, obj):
        return obj.provider.name if obj.provider else ''

    def save_model(self, request, obj, form, change):  # `change`(not created)
        """This part pulls the id(s) from `VdpImportSetup` through a queried `web_provider`."""

        if not obj.feed_ids and obj.provider:
            provider_setups = VdpImportSetup.objects.filter(
                dealer__web_provider__name__iexact=str(obj.provider),
                dealer__account_status__iexact='active',
            ).values_list('vdpurl_feed_id', flat=True)
            # Deduplicate and keep ordering stable for easier admin diffing.
            feed_ids = sorted({feed_id for feed_id in provider_setups if feed_id})
            obj.feed_ids = ','.join(feed_ids)
        # Always defer persistence to admin's save flow.
        super(VdpUrlConfigView, self).save_model(request, obj, form, change)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Project)
admin.site.register(Dealer, DealerAdminView)
admin.site.register(Webprovider, WebProviderAdminView)
admin.site.register(VdpImportSetup, VdpImportSetupAdminView)
admin.site.register(VdpUrl, VdpUrlAdminView)
admin.site.register(FtpConfig, VdpUrlConfigView)


# change django admin header
admin.site.site_header = 'VDP Direct Feed Import'
admin.site.site_title = 'VDP Direct Feed Import'
admin.site.index_title = 'Direct Feed Admin'
