"""FTP feed import orchestration.

Refactor notes (parallel/concurrent run):
- Two thread pools: one for FTP downloads, one for parse/upload/DB work.
- Each completed download is submitted to the process pool immediately, so
  processing overlaps with remaining downloads instead of waiting for all
  downloads to finish first.
- Per-feed failures are captured in ProcessResult and logged without stopping
  the rest of the run.
"""
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
import logging
from io import BytesIO
from typing import Any, Dict, List, NamedTuple, Optional, cast

from vdpurls.direct_feed_import.src.constants import DOWNLOAD_WORKERS, PROCESS_WORKERS
from vdpurls.direct_feed_import.src.feedhandler import FeedHandler
from vdpurls.direct_feed_import.src.ftpconnect import FtpRunStats, fetch_feed, log_fetch_failure
from vdpurls.direct_feed_import.src.pipelines import ImportSourcePipeline
from vdpurls.models import VdpImportSetup, VdpUrl

logger = logging.getLogger(__name__)


class ProcessResult(NamedTuple):
    provider_name: str
    error: Optional[BaseException]


def process_feed(raw_file: BytesIO, feed: Dict[str, Any]) -> ProcessResult:
    """Parse, upload, persist, and save a local copy for one downloaded feed."""
    provider_name: str = feed.get('provider_name', 'unknown')
    try:
        # method comes from DB config; validate before getattr so pyright
        # knows the attribute name is a str (not None/Any).
        parser_name = feed.get('method')
        if not isinstance(parser_name, str) or not parser_name:
            raise ValueError(
                f'Missing or invalid parser method for provider={provider_name!r}'
            )
        parser = getattr(FeedHandler, parser_name, None)
        if not callable(parser):
            raise ValueError(f'Unknown parser method: {parser_name!r}')

        # getattr() returns object; cast after callable() check above.
        parsed_data = cast(
            List[List[Any]],
            parser(
                raw=raw_file,
                feed_ids=feed['feed_ids'],
                fields=feed['target_fields'],
                type=feed['type'],
                model=VdpImportSetup,
            ),
        )
        ImportSourcePipeline(parsed_data).run(provider_name)
        return ProcessResult(provider_name, None)
    except Exception as exc:
        logger.exception('Failed processing feed for provider=%s', provider_name)
        return ProcessResult(provider_name, exc)
    finally:
        raw_file.close()


def run_feed_import(
    config_items: List[Dict[str, Any]],
    *,
    download_workers: int = DOWNLOAD_WORKERS,
    process_workers: int = PROCESS_WORKERS,
    reset_vdp_urls: bool = True,
) -> Dict[str, Any]:
    """Run the full FTP import with overlapping download and processing stages.

    Downloads and processing each use their own thread pool. As soon as a feed
    finishes downloading it is submitted for processing, so parsing/upload/DB
    work overlaps with remaining FTP downloads.
    """
    if reset_vdp_urls:
        VdpUrl.objects.all().delete()

    stats = FtpRunStats(len(config_items))
    process_futures: List[Future[ProcessResult]] = []
    process_errors: List[ProcessResult] = []

    with ThreadPoolExecutor(max_workers=process_workers) as process_pool:
        # Download pool lives inside the process-pool context so processing can
        # start while later feeds are still downloading.
        with ThreadPoolExecutor(max_workers=download_workers) as download_pool:
            download_futures = [
                download_pool.submit(fetch_feed, item) for item in config_items
            ]

            for future in as_completed(download_futures):
                result = future.result()
                stats.record(result)

                if result.status != 'ok':
                    log_fetch_failure(result)
                    continue

                assert result.payload is not None
                # Hand off to process pool as soon as this download completes.
                process_futures.append(
                    process_pool.submit(process_feed, result.payload, result.item)
                )

        # All downloads finished; drain any processing still in flight.
        for future in as_completed(process_futures):
            process_result = future.result()
            if process_result.error:
                process_errors.append(process_result)
                logger.warning(
                    'Provider %s errored during processing: %s',
                    process_result.provider_name,
                    process_result.error,
                )

    summary = stats.as_dict()
    summary['process_errors'] = len(process_errors)
    return summary


def log_run_summary(stats: Dict[str, Any]) -> None:
    logger.info(
        'FTP run summary: attempted=%s connected=%s skipped_network=%s failed=%s process_errors=%s',
        stats['attempted'],
        stats['connected'],
        stats['network_skipped'],
        stats['failed'],
        stats.get('process_errors', 0),
    )
    logger.info(
        'FTP providers connected=%s skipped_network=%s failed=%s',
        sorted(set(stats['connected_providers'])),
        sorted(set(stats['network_skipped_providers'])),
        sorted(set(stats['failed_providers'])),
    )
