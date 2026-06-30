"""Stateless FTP download helpers.

Refactor notes:
- Replaced FtpConnect + shared FtpCredential state (and its thread lock) with
  fetch_feed(), which reads credentials from the config dict per call.
- FtpRunStats uses a lock because download and process threads both record
  outcomes via as_completed() callbacks.
"""
import logging
import socket
import threading
from ftplib import FTP, error_perm
from io import BytesIO
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from vdpurls.direct_feed_import.src.constants import DEFAULT_FTP_TIMEOUT

logger = logging.getLogger(__name__)


class FetchResult(NamedTuple):
    status: str  # 'ok' | 'network' | 'auth' | 'failed'
    payload: Optional[BytesIO]
    item: Dict[str, Any]
    provider_name: str
    file_name: Optional[str]
    error: Optional[BaseException]


class FtpRunStats:
    """Thread-safe counters for one import run."""

    def __init__(self, attempted: int) -> None:
        self._lock = threading.Lock()
        self.attempted = attempted
        self.connected = 0
        self.network_skipped = 0
        self.failed = 0
        self.connected_providers: List[str] = []
        self.network_skipped_providers: List[str] = []
        self.failed_providers: List[str] = []

    def record(self, result: FetchResult) -> None:
        with self._lock:
            if result.status == 'ok':
                self.connected += 1
                self.connected_providers.append(result.provider_name)
            elif result.status == 'network':
                self.network_skipped += 1
                self.network_skipped_providers.append(result.provider_name)
            elif result.status == 'auth':
                self.failed += 1
                self.failed_providers.append(result.provider_name)
            else:
                self.failed += 1
                self.failed_providers.append(result.provider_name)

    def as_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'attempted': self.attempted,
                'connected': self.connected,
                'network_skipped': self.network_skipped,
                'failed': self.failed,
                'connected_providers': list(self.connected_providers),
                'network_skipped_providers': list(self.network_skipped_providers),
                'failed_providers': list(self.failed_providers),
            }


def _require_credentials(item: Dict[str, Any], provider_name: str) -> Tuple[str, int, str, str]:
    host = item.get('ftp_host')
    port = item.get('ftp_port')
    user = item.get('ftp_user')
    password = item.get('ftp_pass')
    if not host or not port or not user or not password:
        raise ValueError(
            f'Missing required FTP credential field(s) in config for provider={provider_name}'
        )
    return str(host), int(port), str(user), str(password)


def fetch_feed(item: Dict[str, Any]) -> FetchResult:
    """Download one source feed. Stateless and safe to run in parallel."""
    provider_name: str = item.get('provider_name', 'unknown')
    file_name: Optional[str] = item.get('file')
    ftp = FTP()

    try:
        host, port, user, password = _require_credentials(item, provider_name)
        timeout_seconds = int(item.get('ftp_timeout') or DEFAULT_FTP_TIMEOUT)

        ftp.connect(host, port, timeout=timeout_seconds)
        ftp.login(user, password)
        logger.info('%s -> %s logged in...', ftp.getwelcome(), provider_name.upper())

        payload = BytesIO()
        ftp.retrbinary(f'RETR /{file_name}', payload.write)
        payload.seek(0)
        return FetchResult('ok', payload, item, provider_name, file_name, None)

    except error_perm as exc:
        # 530 Login incorrect / permission denied = bad credentials or access,
        # not a transient network fault.
        return FetchResult('auth', None, item, provider_name, file_name, exc)
    except (ConnectionRefusedError, TimeoutError, socket.timeout, OSError) as exc:
        return FetchResult('network', None, item, provider_name, file_name, exc)
    except Exception as exc:
        return FetchResult('failed', None, item, provider_name, file_name, exc)
    finally:
        try:
            ftp.quit()
        except Exception:
            pass


def log_fetch_failure(result: FetchResult) -> None:
    if result.status == 'network':
        logger.error(
            'Skipping provider=%s file=%s due to network error: %s',
            result.provider_name,
            result.file_name,
            result.error,
        )
    elif result.status == 'auth':
        logger.error(
            'Skipping provider=%s file=%s due to FTP login/auth failure: %s '
            '(check FtpConfig ftp_user/ftp_pass for this provider)',
            result.provider_name,
            result.file_name,
            result.error,
        )
    elif result.status == 'failed':
        logger.exception(
            'Unexpected FTP source read failure for provider=%s file=%s',
            result.provider_name,
            result.file_name,
            exc_info=result.error,
        )
