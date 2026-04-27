"""Sync dealer account status from AIM API into local Dealer records."""

import logging
import os
import sys
from pathlib import Path

import django
import requests
from django.db.models import CharField
from django.db.models.functions import Cast

# Ensure standalone script execution can resolve Django settings.
sys.path.append(os.path.join(Path(__file__).parents[2], 'vdpimporthelper'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'vdpimporthelper.settings'
django.setup()

from vdpurls.models import Dealer

logger = logging.getLogger(__name__)


class AimApiData:
    _login_url = 'https://aim-admin.com/ncso_api/auth'
    _status_url = 'https://aim-admin.com/aim_system_api/get_data_for_dealers_page/'

    def __init__(self, email, password):
        self._email = email
        self._password = password

    @classmethod
    def from_get_credentials(cls, email, password):
        return cls(email, password)

    @classmethod
    def access_aim_api(cls, email, password):
        form_data = {
            'email': email,
            'password': password,
            'last_logged_version': 'aim_admin',
            'extra_info': {'login_type': 0, 'os': 'Windows', 'device': 'chrome 107.0.0.0'},
        }

        login_res = requests.post(cls._login_url, json=form_data, timeout=30)
        login_res.raise_for_status()
        session_id = login_res.json()[1].get('session_id')

        res = requests.get(f'{cls._status_url}{session_id}', timeout=30)
        res.raise_for_status()
        return res.json()[1].get('data', [])

    @classmethod
    def render_api_data(cls, aimdata):
        # AIM payload uses string ids; cast local dealer_id for robust matching.
        for dealer in aimdata:
            try:
                status = Dealer.objects.annotate(id_str=Cast('dealer_id', output_field=CharField())).get(
                    id_str=dealer.get('id')
                )
                status.account_status = dealer.get('account')
                status.save(update_fields=['account_status'])
            except Exception as exc:
                logger.exception(
                    'Unable to update dealer account status for AIM dealer id=%s',
                    dealer.get('id'),
                )

        logger.info('VDP URLS dealer account status successfully updated')


def main():
    email = os.environ.get('AVAIM_EMAIL')
    password = os.environ.get('AVAIM_PASS')
    credential = AimApiData.from_get_credentials(email, password)
    res_data = AimApiData.access_aim_api(credential._email, credential._password)
    AimApiData.render_api_data(res_data)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    main()
