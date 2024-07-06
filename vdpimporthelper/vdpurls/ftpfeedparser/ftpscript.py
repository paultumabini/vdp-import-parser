import datetime
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List

import django

# time start
start = time.perf_counter()
print(f'Start: {datetime.datetime.now()}')

# append path for the module & django settings
sys.path.append(os.path.join(Path(__file__).parents[3], 'vdpimporthelper'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'vdpimporthelper.settings'
django.setup()

from vdpurls.ftpfeedparser.src.configs import get_config
from vdpurls.ftpfeedparser.src.feedhandler import FeedHandler
from vdpurls.ftpfeedparser.src.ftpconnect import FtpConnect
from vdpurls.ftpfeedparser.src.pipelines import ImportSourcePipeline
from vdpurls.models import VdpImportSetup, VdpUrl


def main() -> None:
    """
    Processes in order:
    - get ftp credentials
    - connect to ftp server
    - read and parse feed
    - filter and clean data
    - create vdp_urls import source.
    """
    with ThreadPoolExecutor() as executor:
        # Clear previous data and save new entries.
        VdpUrl.objects.all().delete()
        # Get items from config list of dict.
        config_items = get_config()

        for rf, feed in FtpConnect(config_items).connect_ftp():
            future = executor.submit(
                getattr(
                    FeedHandler,
                    feed['method'],
                ),
                raw=rf,
                feed_ids=feed['feed_ids'],
                fields=feed['target_fields'],
                type=feed['type'],
                model=VdpImportSetup,
            )
            res_data: List[Dict[str, Any]] = future.result()

            pipeline = ImportSourcePipeline
            attrib = pipeline.evaluate_src(res_data)
            pipeline.process_item(
                feed['provider_name'],
                **vars(attrib),
            )
            pipeline.save_to_csv(feed['provider_name'], **vars(attrib))

            rf.close()


if __name__ == '__main__':
    main()

# time end
finish = time.perf_counter()
print(f'End: {datetime.datetime.now()}')
print(f'Finished in {round(finish - start,2)} second(s)')
