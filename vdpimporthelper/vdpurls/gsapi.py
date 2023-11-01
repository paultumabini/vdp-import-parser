"""
    References:
    `updated google sheets with data`
    https://developers.google.com/sheets/api/quickstart/python
    https://developers.google.com/identity/protocols/oauth2/service-account#python
    https://developers.google.com/sheets/api/reference/rest
"""


import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import django
import numpy as np
import pandas as pd
import requests
from django.db import IntegrityError

# from django.utils import timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# append path to the project dir
sys.path.append(os.path.join(Path(__file__).parents[2], 'vdpimporthelper'))
# append path for the module dir
# sys.path.append(os.path.join(Path(__file__).parents[1], 'vdpurls'))
# Path(__file__).resolve().parent

os.environ['DJANGO_SETTINGS_MODULE'] = 'vdpimporthelper.settings'
django.setup()


from django.contrib.auth.models import User
from vdpurls.models import Dealer, Project, VdpImportSetup, Webprovider


def AccessGsApi():
    SERVICE_ACCOUNT_FILE = './utils/keys_gs.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SPREADSHEET_ID = '1UZ5V28_nCZaNLq9CITviqOzM0_5xpvjn3iSkvATC9LI'

    creds = None
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()

        # Read sheet values
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='dealers_list!A2:T').execute()
        values = result.get('values', [])

        # Dealer.objects.all().delete()

        # convert values into dataframe
        df = pd.DataFrame(values)

        df = df.iloc[:, np.r_[0:11]]  # col1-col11

        # replace all non trailing blank values created by Google Sheets API w/ null values
        df_replace = df.replace([''], [None])

        # convert back to list to insert into Redshift
        processed_dataset = df_replace.values.tolist()

        if not processed_dataset:
            print('No data found -', processed_dataset)
            return

        keys = [f.get_attname() for f in Dealer._meta.fields][0:-5]

        list_of_dic = [dict(zip(keys, value)) for value in processed_dataset]
        # print(list_of_dic)

        render_dealer_data(list_of_dic)

    except HttpError as err:
        print(err)


def render_dealer_data(data):
    uniq_dealer_ids = Dealer.objects.values_list('dealer_id', flat=True).distinct().order_by('dealer_id')

    dictlist = []

    for data in [dic.items() for dic in data]:
        obj = {}

        for key, value in data:
            if key == 'web_provider_id':
                value = re.sub('[^A-Za-z0-9]+', '', value).lower() if value else value

                # get or create additional web providers
                Webprovider.objects.get_or_create(name=value, file_name='')
                # the web provider name thru webprovider_id
                value = Webprovider.objects.filter(name=value).first().id

            obj[key] = value
        dictlist.append(obj)

    # filter out dealer_id does not exists in database
    filtered_list = [obj for obj in dictlist if int(obj['dealer_id']) not in list(uniq_dealer_ids)]

    # save to database;
    for obj in filtered_list:
        dealers = Dealer(
            **obj,
            project=Project.objects.first(),  # instance if foreignkey
            author=User.objects.first(),
        )
        dealers.save()

    print(filtered_list)


def to_vdp_import_setup(values):
    # VdpImportSetup.objects.all().delete()

    # convert values into dataframe
    df = pd.DataFrame(values)
    df = df.iloc[:, np.r_[1:2, 11:19]]  # col2, col12-col19
    df_replace = df.replace([''], [None])
    processed_dataset = df_replace.values.tolist()

    if not processed_dataset:
        print('No data found -', processed_dataset)
        return

    keys2 = [f.get_attname() for f in VdpImportSetup._meta.fields][1::]
    list_of_dic = [dict(zip(keys2, value)) for value in processed_dataset]

    for data in [dic.items() for dic in list_of_dic]:
        obj = {}

        for key, value in data:
            # date_setup field
            if key == 'vdpurl_date_setup' or key == 'vdpurl_date_updated':
                if value:
                    value = datetime.strptime(value, "%Y-%m-%d %I:%M:%S %p").astimezone(timezone.utc)  # avoid RuntimeWarning: DateTimeField
            if key == 'vdpurl_data_provider' or key == 'web_provider_id':
                value = re.sub('[^A-Za-z0-9]+', '', value).lower() if value else value

                if key == 'web_provider_id':
                    # get or create additional web providers
                    Webprovider.objects.get_or_create(name=value, file_name='')
                    # the web provider name thru webprovider_id
                    value = Webprovider.objects.filter(name=value).first().id

            # If value is blank or '', e.g. fb_feed field, new_vehicle field, etc.
            if not value:
                value = None
            obj[key] = value

            # preserve if does exist otherwise create
        vdp, created = VdpImportSetup.objects.get_or_create(
            dealer_id=obj.get('dealer_id'),
            vdpurl_status=obj.get('vdpurl_status'),
            vdpurl_feed_id=obj.get('vdpurl_feed_id'),
            vdpurl_source_file=obj.get('vdpurl_source_file'),
            vdpurl_main_feed_src=obj.get('vdpurl_main_feed_src'),
            vdpurl_data_provider=obj.get('vdpurl_data_provider'),
            vdpurl_date_setup=obj.get('vdpurl_date_setup'),
            vdpurl_date_updated=obj.get('vdpurl_date_updated'),
            note=obj.get('note'),
        )
    print(vdp, created)


AccessGsApi()
