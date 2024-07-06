from django.db.models import F
from vdpurls.models import FtpConfig


def get_config():
    """
    for cvs files:
    - `target_fields` set as the actual column/ header names of the files
    -  for single feed `dealer_id` or `id` is optional, put and empty string("")if not available
    - `target_fields` and `feed_ids` are both comma-separated value, regardless if it's empty or not.
    """
    # Get all field names from FtpConfig model.
    ftp_config_fields = [field.name for field in FtpConfig._meta.get_fields()]

    # Append the annotated provider_name field.
    ftp_config_fields.append('provider_name')

    # Query the FtpConfig model, annotate with provider_name, and include all fields.
    ftp_configs = FtpConfig.objects.annotate(provider_name=F('provider__name')).values(
        *ftp_config_fields
    )

    ftp_config_data = [
        {
            **{k: v.strip() if isinstance(v, str) else v for k, v in obj.items()},
            'feed_ids': [v.strip() for v in (obj['feed_ids'] or '').split(',')],
            'target_fields': [
                v.strip() for v in (obj['target_fields'] or '').split(',')
            ],
        }
        for obj in ftp_configs
    ]
    # Filter out  'autoverify' that is used for destination ftp address.
    filtered_data = [
        entry for entry in ftp_config_data if entry['provider_name'] != 'autoverify'
    ]

    return filtered_data

    """Returned data be like: `-> List[Dict[str,Any]]"""
    """
    [
        {
            'provider_name': 'edealer',
            'file': 'edealer.xml',
            'type': 'batch',
            'method': 'parse_xml_edealer',
            'feed_ids': [6733337,6731437,6732141,...],
            'target_fields': ['dealer_id', 'dealer_name', 'vin', 'details_url'],
        },
        {
            'provider_name': 'ddc',
            'file': 'dealerdotcom.csv',
            'type': 'batch',
            'method': 'parse_csv',
            'feed_ids': ['ccifoundationnorthvancouverchrysler','kenorahonda',...],
            'target_fields': [
                'dealer_id',
                'dealership',
                'vin',
                'details_url',
            ],  # actual fieldnames
        },
        {
            'provider_name': 'dealersiteplus',
            'file': '16604_AIM_VSA.csv',
            'type': 'single',
            'method': 'parse_csv_insert_dname',
            'feed_ids': ['16604'],
            'target_fields': ['dealer_id', 'dealer_name', 'vin', 'misc_1'],
        },
        ...
    ]
    """
