from django.db.models import F

from vdpurls.models import FtpConfig


IGNORED_PROVIDERS = {
    'autoverify',
    # 'ffuncars',
    # 'edealer',
    # 'dealerdotcom',
    # 'dealersiteplus',
    # 'sm360',
    # 'd2c',
    # 'foxdealer',
}


def get_config():
    """Build normalized FTP parser configurations from DB records."""
    ftp_config_fields = [field.name for field in FtpConfig._meta.get_fields()]
    ftp_config_fields.append('provider_name')

    ftp_configs = FtpConfig.objects.annotate(provider_name=F('provider__name')).values(
        *ftp_config_fields
    )

    ftp_config_data = []
    for obj in ftp_configs:
        normalized = {k: v.strip() if isinstance(v, str) else v for k, v in obj.items()}
        # Split CSV-style DB fields into normalized list values for parser handlers.
        normalized['feed_ids'] = [v.strip() for v in (obj.get('feed_ids') or '').split(',') if v.strip()]
        normalized['target_fields'] = [
            v.strip() for v in (obj.get('target_fields') or '').split(',') if v.strip()
        ]
        ftp_config_data.append(normalized)

    # Skip destination-only providers used for upload/testing.
    return [
        entry
        for entry in ftp_config_data
        if entry.get('provider_name') not in IGNORED_PROVIDERS
    ]
