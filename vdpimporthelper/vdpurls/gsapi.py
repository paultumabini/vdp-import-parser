"""Import dealer and VDP setup data from Google Sheets."""

import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import django
import numpy as np
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Support running this script directly from the command line.
sys.path.append(os.path.join(Path(__file__).parents[2], 'vdpimporthelper'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'vdpimporthelper.settings'
django.setup()

from django.contrib.auth.models import User
from vdpurls.models import Dealer, Project, VdpImportSetup, Webprovider

logger = logging.getLogger(__name__)


SERVICE_ACCOUNT_FILE = './utils/keys_gs.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1UZ5V28_nCZaNLq9CITviqOzM0_5xpvjn3iSkvATC9LI'


def access_gs_api():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID, range='dealers_list!A2:T'
        ).execute()
        values = result.get('values', [])

        if not values:
            logger.info('No data found from Google Sheets')
            return

        render_dealer_data(values)
        to_vdp_import_setup(values)
    except HttpError as err:
        logger.exception('Google Sheets API request failed: %s', err)


def render_dealer_data(values):
    uniq_dealer_ids = set(
        Dealer.objects.values_list('dealer_id', flat=True).distinct().order_by('dealer_id')
    )

    df = pd.DataFrame(values)
    df = df.iloc[:, np.r_[0:11]]
    processed_dataset = df.replace([''], [None]).values.tolist()

    keys = [f.get_attname() for f in Dealer._meta.fields][0:-5]
    dictlist = []

    for row in [dic.items() for dic in [dict(zip(keys, value)) for value in processed_dataset]]:
        obj = {}
        for key, value in row:
            if key == 'web_provider_id':
                normalized = re.sub('[^A-Za-z0-9]+', '', value).lower() if value else value
                provider, _ = Webprovider.objects.get_or_create(name=normalized, file_name='')
                value = provider.id
            obj[key] = value
        dictlist.append(obj)

    filtered_list = [obj for obj in dictlist if int(obj['dealer_id']) not in uniq_dealer_ids]

    for obj in filtered_list:
        Dealer.objects.create(
            **obj,
            project=Project.objects.first(),
            author=User.objects.first(),
        )

    logger.info('Created %s new dealers from Google Sheets', len(filtered_list))


def to_vdp_import_setup(values):
    df = pd.DataFrame(values)
    df = df.iloc[:, np.r_[1:2, 11:19]]
    processed_dataset = df.replace([''], [None]).values.tolist()

    if not processed_dataset:
        logger.info('No VDP setup rows found from Google Sheets')
        return

    keys = [f.get_attname() for f in VdpImportSetup._meta.fields][1:]
    list_of_dic = [dict(zip(keys, value)) for value in processed_dataset]

    for data in [dic.items() for dic in list_of_dic]:
        obj = {}
        for key, value in data:
            if key == 'vdpurl_date_setup' and value:
                # Convert sheet local datetime into UTC-aware datetime.
                value = datetime.strptime(value, '%Y-%m-%d %I:%M:%S %p').astimezone(
                    timezone.utc
                )

            if key == 'vdpurl_data_provider':
                value = re.sub('[^A-Za-z0-9]+', '', value).lower() if value else value

            if value in ['', None]:
                value = None
            obj[key] = value

        VdpImportSetup.objects.get_or_create(
            dealer_id=obj.get('dealer_id'),
            defaults={
                'vdpurl_status': obj.get('vdpurl_status'),
                'vdpurl_feed_id': obj.get('vdpurl_feed_id'),
                'vdpurl_source_file': obj.get('vdpurl_source_file'),
                'vdpurl_main_feed_src': obj.get('vdpurl_main_feed_src'),
                'vdpurl_data_provider': obj.get('vdpurl_data_provider'),
                'vdpurl_date_setup': obj.get('vdpurl_date_setup'),
                'note': obj.get('note'),
            },
        )


def main():
    access_gs_api()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    main()
