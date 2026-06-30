from django.apps import AppConfig


class VdpurlsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vdpurls'
    verbose_name = 'VDP Direct Feed'

    def ready(self):
        # Patch jazzmin paginator for Django 6 (see vdpimporthelper/jazzmin_compat.py).
        from jazzmin.templatetags.jazzmin import register

        from vdpimporthelper.jazzmin_compat import jazzmin_paginator_number

        register.simple_tag(name='jazzmin_paginator_number')(jazzmin_paginator_number)
