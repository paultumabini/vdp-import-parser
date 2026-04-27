from ftplib import FTP
import logging
from io import BytesIO
import socket

from vdpurls.ftpfeedparser.src.creds import FtpCredential

logger = logging.getLogger(__name__)


class FtpConnect(FtpCredential):
    def __init__(self, config_items):
        super().__init__()
        self._config_items = config_items
        # Track provider-level outcomes for end-of-run operational summary.
        self._stats = {
            'attempted': len(config_items),
            'connected': 0,
            'network_skipped': 0,
            'failed': 0,
            'connected_providers': [],
            'network_skipped_providers': [],
            'failed_providers': [],
        }

    @property
    def config_items(self):
        return self._config_items

    @config_items.setter
    def config_items(self, config_items):
        self._config_items = config_items

    @property
    def stats(self):
        return self._stats

    def connect_ftp(self):
        """Connect to source FTP servers and yield `(buffer, config)` tuples."""
        for item in self.config_items:
            ftp = FTP()
            try:
                provider_name = item.get('provider_name', 'unknown')
                file_name = item.get('file')
                self.provide_cred(
                    item.get('ftp_host'),
                    item.get('ftp_port'),
                    item.get('ftp_user'),
                    item.get('ftp_pass'),
                )
                # Keep a bounded timeout so one bad endpoint does not stall the whole run.
                timeout_seconds = int(item.get('ftp_timeout') or 20)
                ftp.connect(self.ftp_host, self.ftp_port, timeout=timeout_seconds)
                ftp.login(self.ftp_user, self.ftp_pass)
                logger.info(
                    '%s -> %s logged in...',
                    ftp.getwelcome(),
                    provider_name.upper(),
                )
                self._stats['connected'] += 1
                self._stats['connected_providers'].append(provider_name)

                payload = BytesIO()
                ftp.retrbinary(f"RETR /{file_name}", payload.write)
                payload.seek(0)
                yield payload, item
            except (ConnectionRefusedError, TimeoutError, socket.timeout, OSError) as exc:
                # Network-level issues are expected for some providers and should not abort the run.
                self._stats['network_skipped'] += 1
                self._stats['network_skipped_providers'].append(provider_name)
                logger.error(
                    'Skipping provider=%s file=%s due to network error: %s',
                    provider_name,
                    file_name,
                    exc,
                )
            except Exception:
                # Keep traceback for truly unexpected parser/FTP protocol errors.
                self._stats['failed'] += 1
                self._stats['failed_providers'].append(provider_name)
                logger.exception(
                    'Unexpected FTP source read failure for provider=%s file=%s',
                    provider_name,
                    file_name,
                )
            finally:
                try:
                    ftp.quit()
                except Exception:
                    pass
