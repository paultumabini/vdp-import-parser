import datetime
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List

import django

logger = logging.getLogger(__name__)

start = time.perf_counter()
logger.info('Start: %s', datetime.datetime.now())

sys.path.append(os.path.join(Path(__file__).parents[3], 'vdpimporthelper'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'vdpimporthelper.settings'
django.setup()

from vdpurls.ftpfeedparser.src.configs import get_config
from vdpurls.ftpfeedparser.src.feedhandler import FeedHandler
from vdpurls.ftpfeedparser.src.ftpconnect import FtpConnect
from vdpurls.ftpfeedparser.src.pipelines import ImportSourcePipeline
from vdpurls.models import VdpImportSetup, VdpUrl


def main() -> None:
    """Fetch feeds, normalize payloads, upload and persist VDP URLs."""
    with ThreadPoolExecutor() as executor:
        # Each run starts with a clean VDP URL snapshot.
        VdpUrl.objects.all().delete()
        config_items = get_config()
        connector = FtpConnect(config_items)

        for raw_file, feed in connector.connect_ftp():
            future = executor.submit(
                getattr(FeedHandler, feed['method']),
                raw=raw_file,
                feed_ids=feed['feed_ids'],
                fields=feed['target_fields'],
                type=feed['type'],
                model=VdpImportSetup,
            )
            res_data: List[Dict[str, Any]] = future.result()

            pipeline = ImportSourcePipeline
            attrib = pipeline.evaluate_src(res_data)
            pipeline.process_item(feed['provider_name'], **vars(attrib))
            pipeline.save_to_csv(feed['provider_name'], **vars(attrib))
            raw_file.close()

        stats = connector.stats
        logger.info(
            'FTP run summary: attempted=%s connected=%s skipped_network=%s failed=%s',
            stats['attempted'],
            stats['connected'],
            stats['network_skipped'],
            stats['failed'],
        )
        logger.info(
            'FTP providers connected=%s skipped_network=%s failed=%s',
            sorted(set(stats['connected_providers'])),
            sorted(set(stats['network_skipped_providers'])),
            sorted(set(stats['failed_providers'])),
        )


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    main()

finish = time.perf_counter()
logger.info('End: %s', datetime.datetime.now())
logger.info('Finished in %s second(s)', round(finish - start, 2))
