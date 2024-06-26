import csv
import io
import os
from ftplib import FTP
from typing import Any, Dict, List

from vdpurls.models import FtpConfig, VdpImportSetup, VdpUrl


class ImportSourcePipeline:
    def __init__(self, import_data: List[Dict[str, Any]]) -> None:
        self._import_data = import_data

    @classmethod
    def evaluate_src(cls, import_data: List[Dict[str, Any]]) -> 'ImportSourcePipeline':
        return cls(import_data)

    @staticmethod
    def process_item(provider_name: str, **kwargs: Dict[str, Any]) -> None:
        # Initialize logs and counters
        logs: List[Dict[str, Any]] = []

        for labels, data in kwargs.get('_import_data', []):
            feed_id = labels.get('feed_id')
            dealer_name = labels.get('dealer_name')
            aim_id = labels.get('aim_id')

            # Upload CSV to FTP
            try:
                ImportSourcePipeline._upload_to_ftp(dealer_name, data)
            except Exception as e:
                print(f"FTP Error: {str(e)}")
                continue

            # Save to database
            try:
                ImportSourcePipeline._save_to_database(feed_id, aim_id, data)
            except Exception as e:
                print(f"Database Error: {str(e)}")
                continue

            # Update VdpImportSetup
            try:
                ImportSourcePipeline._update_vdp_import_setup(feed_id, dealer_name)
            except Exception as e:
                print(f"Database Update Error: {str(e)}")

            # Logging
            ImportSourcePipeline._log_process(logs, feed_id, dealer_name, aim_id)

        print('File upload success!')
        print(
            f'{provider_name.upper()} ({len(kwargs.get("_import_data", []))}): {logs}'
        )

    # Connect to FTP server and upload CSV file
    @staticmethod
    def _upload_to_ftp(dealer_name: str, data: List[dict]) -> None:
        fieldnames = data[0].keys()
        csvfile = io.StringIO()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        file = f'VDP_URLS_{dealer_name}.csv'

        # sending to `ftp.aim.autoverify.com`
        ftp_dest_cred = [
            entry for entry in FtpConfig.objects.values() if entry['provider_id'] == 42
        ][0]

        with FTP(ftp_dest_cred['ftp_host']) as ftp:
            ftp.login(ftp_dest_cred['ftp_user'], ftp_dest_cred['ftp_pass'])
            ftp.storbinary(f'STOR {file}', io.BytesIO(csvfile.getvalue().encode()))

    # Save to database (assuming VdpUrl model exists)
    @staticmethod
    def _save_to_database(feed_id: str, aim_id: str, data: List[dict]) -> None:
        for obj in data:
            VdpUrl.objects.create(
                dealer_id=aim_id,
                dealer_vdpurl_feed_id=feed_id,
                vin=obj.get('VIN'),
                vehicle_url=obj.get('VDP URLS'),
            )

    # Update VdpImportSetup > FTP Src File with source file if not already set
    @staticmethod
    def _update_vdp_import_setup(feed_id: str, dealer_name: str) -> None:
        vdp_src_file = VdpImportSetup.objects.filter(vdpurl_feed_id=feed_id)
        for obj in vdp_src_file:
            if not obj.vdpurl_source_file:
                obj.vdpurl_source_file = f'VDP_URLS_{dealer_name}.csv'
                obj.save()

    @staticmethod
    def _log_process(
        logs: List[Dict[str, Any]], feed_id: str, dealer_name: str, aim_id: str
    ) -> None:

        logs.append(
            {'FEEDID': feed_id, 'FILE': f'VDP_URLS_{dealer_name}.csv', 'AIMID': aim_id}
        )

    # Save csv file
    @staticmethod
    def save_to_csv(provider_name: str, **kwargs: Dict[str, Any]) -> None:
        dir = '/home/pt/Dev/Projects/django/aim/vdp/output_csv/'
        if not os.path.exists(dir):
            os.mkdir(dir)

        logs = []
        total_dealers = 0

        for labels, data in kwargs.get('_import_data', []):
            dealer_name = labels.get('dealer_name')
            fieldnames = data[0].keys()

            with open(
                f'{dir}VDP_URLS_{provider_name}_{dealer_name}.csv',
                'w',
                newline='',
                encoding='utf-8',
            ) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            total_dealers += 1
            logs.append(f'{total_dealers}. VDP_URLS_{dealer_name}.csv')

        print(f'[{provider_name.upper()}] ({total_dealers}):', logs)
        print('Local csv files saved')
