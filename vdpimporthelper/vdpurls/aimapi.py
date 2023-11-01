"""
    References:
    `updated google sheets with data`
    https://developers.google.com/sheets/api/quickstart/python
    https://developers.google.com/identity/protocols/oauth2/service-account#python
    https://developers.google.com/sheets/api/reference/rest
"""


import os
import sys
from pathlib import Path

import django
import requests

# append path to the project dir
sys.path.append(os.path.join(Path(__file__).parents[2], 'vdpimporthelper'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'vdpimporthelper.settings'
django.setup()


from django.db.models import CharField
from django.db.models.functions import Cast
from vdpurls.models import Dealer


class AimApiData:
    _login_url = 'https://aim-admin.com/ncso_api/auth'
    _status_url = 'https://aim-admin.com/aim_system_api/get_data_for_dealers_page/'

    def __init__(self, email, password):
        self._email = email
        self._password = password

    @property
    def email(self):
        return self._email

    @email.setter
    def serv_acct_file(self, file):
        if not self._email:
            self._email = file

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        if not self._password:
            self._password = password

    @classmethod
    def from_get_credentials(cls, email, password):
        return cls(email, password)

    @classmethod
    def access_aim_api(cls, **kwargs):

        form_data = {
            "email": kwargs['_email'],
            "password": kwargs['_password'],
            "last_logged_version": "aim_admin",
            "extra_info": {"login_type": 0, "os": "Windows", "device": "chrome 107.0.0.0"},
        }

        login_res = requests.post(cls._login_url, json=form_data)
        # required session_id
        session_id = login_res.json()[1].get('session_id')

        # get avaim data response
        res_data = requests.get(f'{cls._status_url}{session_id}').json()[1].get('data')

        return res_data

    @classmethod
    def render_api_data(cls, aimdata):
        # update account status in webscrape
        for dealer in aimdata:
            try:
                status = Dealer.objects.annotate(id_str=Cast('dealer_id', output_field=CharField())).get(id_str=dealer.get('id'))
                status.account = dealer.get('account')
                status.save()
            except:
                pass

        print(
            'VDP URLS:',
            [[d.account, d.dealer_id, d.dealer_name] for d in Dealer.objects.all().order_by('account')],
        )
        print('VDP URLS Dealer Account Status successfully updated!')


aim = AimApiData
email = os.environ.get('AVAIM_EMAIL')
password = os.environ.get('AVAIM_PASS')
credential = aim.from_get_credentials(email, password)
res_data = aim.access_aim_api(**vars(credential))
aim.render_api_data(res_data)
