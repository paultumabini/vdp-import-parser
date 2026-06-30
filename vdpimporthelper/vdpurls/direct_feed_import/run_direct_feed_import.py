"""CLI entry point for the direct feed import pipeline.

Refactor notes:
- Django is initialized only when run as a script (not at import time).
- Import orchestration lives in runner.run_feed_import(); this file only
  configures logging and prints timing/summary output.
"""
import datetime
import logging
import os
import sys
import time
from pathlib import Path


def setup_django() -> None:
    # Deferred setup keeps imports safe for tooling/tests that do not need ORM.
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vdpimporthelper.settings')

    import django

    django.setup()


def main() -> None:
    from vdpurls.direct_feed_import.src.configs import get_config
    from vdpurls.direct_feed_import.src.runner import log_run_summary, run_feed_import

    start = time.perf_counter()
    logger = logging.getLogger(__name__)
    logger.info('Start: %s', datetime.datetime.now())

    stats = run_feed_import(get_config())
    log_run_summary(stats)

    elapsed = round(time.perf_counter() - start, 2)
    logger.info('End: %s', datetime.datetime.now())
    logger.info('Finished in %s second(s)', elapsed)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    setup_django()
    main()
