import csv
import io
import logging
import threading
from pathlib import Path
from ftplib import FTP
from typing import Any, Dict, List, Optional

from django.conf import settings

from vdpurls.direct_feed_import.src.constants import UPLOAD_CONCURRENCY
from vdpurls.models import FtpConfig, VdpImportSetup, VdpUrl

logger = logging.getLogger(__name__)

# Shared destination FTP (provider_id=42) caps concurrent uploads across
# all providers being processed in parallel.
_UPLOAD_SEMAPHORE = threading.Semaphore(UPLOAD_CONCURRENCY)

# Each record is [labels_dict, data_rows].
ImportRecord = List[Any]


class ImportSourcePipeline:
    """Upload parsed feed rows to destination FTP, DB, and optional local CSV.

    Refactor notes:
    - Replaced evaluate_src()/process_item(**vars(...)) with a single instance
      API: ImportSourcePipeline(data).run(provider_name).
    - Local CSV output uses settings.BASE_DIR instead of a hardcoded path.
    """
    def __init__(self, import_data: List[ImportRecord]) -> None:
        self.import_data = import_data

    def run(self, provider_name: str, *, save_local_csv: bool = True) -> None:
        self.process(provider_name)
        if save_local_csv:
            self.save_local_csv(provider_name)

    def process(self, provider_name: str) -> None:
        logs: List[Dict[str, Any]] = []

        for labels, data in self.import_data:
            if not data:
                continue

            feed_id = labels.get('feed_id')
            dealer_name = labels.get('dealer_name')
            aim_id = labels.get('aim_id')

            try:
                self._upload_to_ftp(dealer_name, data)
                self._save_to_database(feed_id, aim_id, data)
                self._update_vdp_import_setup(feed_id, dealer_name, aim_id)
                logs.append(
                    {
                        'FEEDID': feed_id,
                        'FILE': f'VDP_URLS_{dealer_name}.csv',
                        'AIMID': aim_id,
                    }
                )
            except Exception:
                logger.exception(
                    'Pipeline processing failed for provider=%s feed_id=%s',
                    provider_name,
                    feed_id,
                )

        logger.info(
            '%s processed %s dealer feed(s): %s',
            provider_name.upper(),
            len(logs),
            logs,
        )

    def save_local_csv(self, provider_name: str) -> None:
        output_dir = settings.BASE_DIR.parent / 'output_csv'
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files: List[str] = []
        for index, (labels, data) in enumerate(self.import_data, start=1):
            if not data:
                continue

            dealer_name = labels.get('dealer_name')
            output_file = output_dir / f'VDP_URLS_{provider_name}_{dealer_name}.csv'

            with output_file.open('w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

            saved_files.append(f'{index}. {output_file.name}')

        if saved_files:
            logger.info(
                '[%s] saved %s local CSV file(s): %s',
                provider_name.upper(),
                len(saved_files),
                saved_files,
            )

    @staticmethod
    def _upload_to_ftp(dealer_name: str, data: List[Dict[str, Any]]) -> None:
        csvfile = io.StringIO()
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        file_name = f'VDP_URLS_{dealer_name}.csv'
        ftp_dest_cred = FtpConfig.objects.filter(provider_id=42).values().first()
        if not ftp_dest_cred:
            raise ValueError('Destination FTP config (provider_id=42) not found')

        with _UPLOAD_SEMAPHORE:
            with FTP(ftp_dest_cred['ftp_host']) as ftp:
                ftp.login(ftp_dest_cred['ftp_user'], ftp_dest_cred['ftp_pass'])
                ftp.storbinary(
                    f'STOR {file_name}', io.BytesIO(csvfile.getvalue().encode())
                )

    @staticmethod
    def _save_to_database(
        feed_id: str, aim_id: Optional[int], data: List[Dict[str, Any]]
    ) -> None:
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
    def _update_vdp_import_setup(
        feed_id: str, dealer_name: str, dealer_id: Optional[int]
    ) -> None:
        file_name = f'VDP_URLS_{dealer_name}.csv'
        if dealer_id:
            VdpImportSetup.sync_vdp_url_count(dealer_id)
        for obj in VdpImportSetup.objects.filter(vdpurl_feed_id=feed_id):
            obj.exported_feed = file_name
            obj.save(update_fields=['exported_feed'])
