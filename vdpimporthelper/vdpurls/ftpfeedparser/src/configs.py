def config(**kwargs):
    edealer, ddc = kwargs['ids'](kwargs['mdl'])

    """ for cvs files:
    - `target_fields` set as the actual column/ header names of the files 
    -  for single feed `dealer_id` or `id` is optional, put and empty string("")if not available
    """

    return [
        {
            'provider': 'edealer',
            'file': 'edealer_edealer.xml',
            'type': 'batch',
            'method': 'parse_xml_edealer',
            'feed_ids': edealer,
            'target_fields': ['dealer_id', 'dealer_name', 'vin', 'details_url'],
        },
        {
            'provider': 'ddc',
            'file': 'dealerdotcom.csv',
            'type': 'batch',
            'method': 'parse_csv',
            'feed_ids': ddc,
            'target_fields': ['dealer_id', 'dealership', 'vin', 'details_url'],  # actual fieldnames
        },
        {
            'provider': 'ffuncars',
            'file': 'VDP_EXPORT_FFUNCARS.csv',
            'type': 'single',
            'method': 'parse_csv',
            'feed_ids': ['FFUNCars'],
            'target_fields': ['', 'Dealer Name', 'VIN', 'VDP URLS'],
        },
        {
            'provider': 'sm360',
            'file': 'saint_john_toyota.csv_en.csv',
            'type': 'single',
            'method': 'parse_csv',
            'feed_ids': ['2119'],
            'target_fields': ['d_id', 'dealer_name', 'vin', 'external_url'],
        },
        {
            'provider': 'sm360',
            'file': 'lexus_saint_john.csv_en.csv',
            'type': 'single',
            'method': 'parse_csv',
            'feed_ids': ['2118'],
            'target_fields': ['d_id', 'dealer_name', 'vin', 'external_url'],
        },
        {
            'provider': 'dealersiteplus',
            'file': '16604_AIM_VSA.csv',
            'type': 'single',
            'method': 'parse_csv_insert_dname',
            'feed_ids': ['16604'],
            'target_fields': ['dealer_id', 'dealer_name', 'vin', 'misc_1'],
        },
        # {
        #     'provider': 'tadvantage',
        #     'file': 'trader_full_used.csv',
        #     'type': 'single',
        #     'method': 'parse_csv',
        #     'feed_ids': ['20230331180620721'],
        #     'target_fields': ['CompanyID', 'CompanyName', 'Vin', 'Status'],
        # },
    ]


def get_feed_ids(model):
    def strip_space(ids):
        return [id.strip() for id in ids]

    """ To refer to correct field via foreign keys, dont forget to use double underscores """
    # Edealer
    edealer = model.objects.filter(dealer__web_provider__name__iexact='edealer', dealer__account__iexact='active').all()
    edealer_ids = list(set([id.vdpurl_feed_id for id in edealer if bool(id.vdpurl_feed_id)]))

    # DCC
    ddc = model.objects.filter(dealer__web_provider__name__iexact='dealersmart', dealer__account__iexact='active').all()
    ddc_ids = list(set([id.vdpurl_feed_id for id in ddc if bool(id.vdpurl_feed_id)]))

    return [
        strip_space(edealer_ids),
        strip_space(ddc_ids),
    ]
