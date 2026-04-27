import csv
import io
import logging
from pathlib import Path
from ftplib import FTP
from typing import Any, Dict, List

from vdpurls.models import FtpConfig, VdpImportSetup, VdpUrl

logger = logging.getLogger(__name__)


class ImportSourcePipeline:
    def __init__(self, import_data: List[Dict[str, Any]]) -> None:
        self._import_data = import_data

    @classmethod
    def evaluate_src(cls, import_data: List[Dict[str, Any]]) -> 'ImportSourcePipeline':
        return cls(import_data)

    @staticmethod
    def process_item(provider_name: str, **kwargs: Dict[str, Any]) -> None:
        logs: List[Dict[str, Any]] = []

        for labels, data in kwargs.get('_import_data', []):
            if not data:
                continue

            feed_id = labels.get('feed_id')
            dealer_name = labels.get('dealer_name')
            aim_id = labels.get('aim_id')

            try:
                ImportSourcePipeline._upload_to_ftp(dealer_name, data)
                ImportSourcePipeline._save_to_database(feed_id, aim_id, data)
                ImportSourcePipeline._update_vdp_import_setup(feed_id, dealer_name)
                ImportSourcePipeline._log_process(logs, feed_id, dealer_name, aim_id)
            except Exception as exc:
                logger.exception(
                    'Pipeline processing failed for provider=%s feed_id=%s',
                    provider_name,
                    feed_id,
                )
                continue

        logger.info('File upload success!')
        logger.info(
            '%s (%s): %s',
            provider_name.upper(),
            len(kwargs.get('_import_data', [])),
            logs,
        )

    @staticmethod
    def _upload_to_ftp(dealer_name: str, data: List[dict]) -> None:
        fieldnames = data[0].keys()
        csvfile = io.StringIO()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        file_name = f'VDP_URLS_{dealer_name}.csv'

        # Provider id 42 is reserved for the destination uploader account.
        ftp_dest_cred = FtpConfig.objects.filter(provider_id=42).values().first()
        if not ftp_dest_cred:
            raise ValueError('Destination FTP config (provider_id=42) not found')

        with FTP(ftp_dest_cred['ftp_host']) as ftp:
            ftp.login(ftp_dest_cred['ftp_user'], ftp_dest_cred['ftp_pass'])
            ftp.storbinary(f'STOR {file_name}', io.BytesIO(csvfile.getvalue().encode()))

    @staticmethod
    def _save_to_database(feed_id: str, aim_id: str, data: List[dict]) -> None:
        if not aim_id:
            return
        for obj in data:
            VdpUrl.objects.create(
                dealer_id=aim_id,
                dealer_vdpurl_feed_id=feed_id,
                vin=obj.get('VIN'),
                vehicle_url=obj.get('VDP URLS'),
            )

    @staticmethod
    def _update_vdp_import_setup(feed_id: str, dealer_name: str) -> None:
        for obj in VdpImportSetup.objects.filter(vdpurl_feed_id=feed_id):
            if not obj.vdpurl_source_file:
                obj.vdpurl_source_file = f'VDP_URLS_{dealer_name}.csv'
                obj.save(update_fields=['vdpurl_source_file'])

    @staticmethod
    def _log_process(
        logs: List[Dict[str, Any]], feed_id: str, dealer_name: str, aim_id: str
    ) -> None:
        logs.append({'FEEDID': feed_id, 'FILE': f'VDP_URLS_{dealer_name}.csv', 'AIMID': aim_id})

    @staticmethod
    def save_to_csv(provider_name: str, **kwargs: Dict[str, Any]) -> None:
        output_dir = Path('/home/pt/Dev/Projects/django/aim/vdp/output_csv')
        output_dir.mkdir(parents=True, exist_ok=True)

        logs = []
        total_dealers = 0

        for labels, data in kwargs.get('_import_data', []):
            if not data:
                continue
            dealer_name = labels.get('dealer_name')
            fieldnames = data[0].keys()
            output_file = output_dir / f'VDP_URLS_{provider_name}_{dealer_name}.csv'

            with output_file.open('w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            total_dealers += 1
            logs.append(f'{total_dealers}. VDP_URLS_{dealer_name}.csv')

        logger.info('[%s] (%s): %s', provider_name.upper(), total_dealers, logs)
        logger.info('Local csv files saved')
