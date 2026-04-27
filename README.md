# VDP Import Helper

Django-based tooling for importing vehicle detail page (VDP) URLs from multiple provider FTP feeds, normalizing records, and exporting results for downstream use.

## What This Project Does

- Manages dealer and VDP setup records in Django admin.
- Pulls source files from provider FTP endpoints.
- Parses CSV/XML feed formats into a normalized schema.
- Uploads generated provider output files to a destination FTP.
- Stores VDP URL rows in the database.
- Emits operational logs with per-run provider summaries.

## Tech Stack

- Python 3.11
- Django 4.1
- PostgreSQL
- Pandas / xmltodict

## Project Layout

- `vdpimporthelper/` - Django project root (`manage.py`, settings, templates, apps)
- `vdpimporthelper/vdpurls/` - main app (models, admin, FTP pipeline, scripts)
- `vdpimporthelper/vdpurls/ftpfeedparser/` - feed ingestion pipeline
- `output_csv/` - generated local CSV output from pipeline runs

## Quick Start

1. Clone and enter repo
   - `git clone <repo-url>`
   - `cd vdp`
2. Create/activate virtualenv
   - `python3 -m venv venv`
   - `source venv/bin/activate`
3. Install dependencies
   - `pip install -r requirements.txt`
4. Create env file from template
   - `cp .env.example .env`
5. Run migrations
   - `cd vdpimporthelper`
   - `python manage.py migrate`
6. Start server
   - `python manage.py runserver`

## Environment Variables

Use `.env.example` as reference.

### Django

- `DJANGO_DEBUG`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_SECURE_HSTS_PRELOAD`

### Database

- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

### External APIs

- `AVAIM_EMAIL`
- `AVAIM_PASS`

## Running Common Tasks

From `vdpimporthelper/`:

- Django checks: `../venv/bin/python manage.py check`
- Tests: `../venv/bin/python manage.py test vdpurls -v 1`
- Create superuser: `python manage.py createsuperuser`

## FTP Import Pipeline

Run from `vdpimporthelper/`:

- `../venv/bin/python vdpurls/ftpfeedparser/ftpscript.py`

What happens:

1. Reads active provider config from `FtpConfig`.
2. Connects to each source FTP (with timeout and skip-on-network-failure behavior).
3. Parses feed using configured parser method.
4. Uploads generated `VDP_URLS_<dealer>.csv` files to destination FTP.
5. Saves rows to `VdpUrl`.
6. Logs end-of-run summary:
   - attempted
   - connected
   - skipped (network)
   - failed
   - provider lists per outcome

## Other Utility Scripts

From `vdpimporthelper/`:

- AIM account status sync:
  - `../venv/bin/python vdpurls/aimapi.py`
- Google Sheets import sync:
  - `../venv/bin/python vdpurls/gsapi.py`

## Notes

- Keep secrets out of source control (`.env` is gitignored).
- `keys_gs.json` is excluded from git; place it locally when using `gsapi.py`.
- In production, set `DJANGO_DEBUG=false` and use a strong `DJANGO_SECRET_KEY`.
