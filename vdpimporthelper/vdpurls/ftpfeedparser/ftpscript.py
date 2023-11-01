import datetime
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import django

# time start
start = time.perf_counter()
print(f'Start: {datetime.datetime.now()}')

# append path for the module & django settings
sys.path.append(os.path.join(Path(__file__).parents[3], 'vdpimporthelper'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'vdpimporthelper.settings'
django.setup()

from vdpurls.ftpfeedparser.src.configs import config, get_feed_ids
from vdpurls.ftpfeedparser.src.feedhandler import FeedHandler
from vdpurls.ftpfeedparser.src.ftpconnect import FtpConnect
from vdpurls.ftpfeedparser.src.pipelines import ImportSourcePipeline
from vdpurls.models import VdpImportSetup as VIS
from vdpurls.models import VdpUrl


def main():
    """
    Processes in order
    - get ftp credentials
    - connect to ftp server
    - read and parse feed
    - filter and clean data
    - create vdp_urls import source
    """
    with ThreadPoolExecutor() as executor:
        # clear previous data and save new entries
        VdpUrl.objects.all().delete()

        for ftp, rf, feed in FtpConnect(config(mdl=VIS, ids=get_feed_ids)).connect_ftp():
            future = executor.submit(
                getattr(
                    FeedHandler,
                    feed['method'],
                ),
                raw=rf,
                feed_ids=feed['feed_ids'],
                fields=feed['target_fields'],
                type=feed['type'],
                model=VIS,
            )
            res = future.result()

            fd = ImportSourcePipeline
            attrib = fd.evaluate_src(ftp, res)
            fd.process_item(
                VdpUrl,
                VIS,
                feed['provider'],
                **vars(attrib),
            )
            fd.save_to_csv(feed['provider'], **vars(attrib))

            rf.close()


if __name__ == '__main__':
    main()

# time end
finish = time.perf_counter()
print(f'End: {datetime.datetime.now()}')
print(f'Finished in {round(finish - start,2)} second(s)')
