import os

# Tunable worker counts for the two-stage import pipeline (see runner.py).
# Override at runtime via env vars when tuning for network vs CPU/DB limits.
DOWNLOAD_WORKERS = int(os.environ.get('VDP_FTP_DOWNLOAD_WORKERS', '10'))
PROCESS_WORKERS = int(os.environ.get('VDP_FTP_PROCESS_WORKERS', '8'))

# Destination FTP (provider_id=42) upload concurrency limit.
UPLOAD_CONCURRENCY = int(os.environ.get('VDP_FTP_UPLOAD_CONCURRENCY', '3'))

DEFAULT_FTP_TIMEOUT = 20
