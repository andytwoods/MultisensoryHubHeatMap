# Multisensory Hub Concept Analytics

A lightweight, privacy-conscious analytics system for tracking user engagement and "dwell time" on concept-based documentation sites. 

This project consists of a **Django backend** for data ingestion and processing, and a **React frontend** tracking library designed for Docusaurus.

## Project Structure

- `concept_analytics/`: The Django app (pip-installable).
- `frontend/`: The React tracking components and hooks.
- `scripts/`: Tooling for manifest generation and validation.
- `tests/`: Comprehensive Python test suite.

---

## Running the dev server

`dev_project/` is a minimal Django host project for local development.
It uses a file-based SQLite database (`dev.sqlite3`) so data persists between runs.

### 1. Install dependencies

This submodule lives inside the `MultisensoryHub` workspace. Run `uv sync` once from the **parent repo root** to create the shared virtual environment:

```bash
cd ..   # MultisensoryHub root
uv sync
```

Working on this submodule in isolation (outside the parent workspace)? Use:

```bash
uv venv && uv pip install -e ".[dev]"
```

### 2. First-time setup

Run from inside `multisensoryHubHeatMap/`:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Or from the parent `MultisensoryHub/` directory:

```bash
uv run python multisensoryHubHeatMap/manage.py migrate
uv run python multisensoryHubHeatMap/manage.py createsuperuser
```

### 3. Start the server

From `multisensoryHubHeatMap/`:

```bash
python manage.py runserver
```

From the parent `MultisensoryHub/`:

```bash
uv run python multisensoryHubHeatMap/manage.py runserver
```

### Available URLs

| URL | Description |
|-----|-------------|
| http://localhost:8000/admin/ | Django admin — browse sessions, events, manifest entries |
| http://localhost:8000/analytics/ingest/ | Event ingest endpoint (POST) |
| http://localhost:8000/analytics/summary/latest/ | Public-safe aggregate summary (GET, requires `Authorization: Bearer dev-token`) |
| http://localhost:8000/analytics/dashboard/ | HTMX heat-map dashboard |

### Running tests

From `multisensoryHubHeatMap/`:

```bash
pytest
```

From the parent `MultisensoryHub/`:

```bash
uv run pytest multisensoryHubHeatMap/
```

### Management commands

Rebuild summary tables from raw event data (bot sessions are automatically excluded):

```bash
python manage.py refresh_concept_analytics_summaries --days 7
```

Delete raw events older than 180 days (run periodically, e.g. weekly cron):

```bash
python manage.py purge_old_events --days 180
```

---

## Installing into a host project

### Requirements
- Python 3.12+
- Django 4.2+
- `django-cors-headers`

### Installation

```bash
pip install -e .
```

### Django configuration

Add to `settings.py`:

```python
INSTALLED_APPS = [
    ...,
    "corsheaders",
    "concept_analytics",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must be above CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    ...,
]

CONCEPT_ANALYTICS = {
    "ALLOWED_ORIGINS": ["https://your-docusaurus-site.com"],
    "MAX_EVENTS_PER_BATCH": 50,
    "MAX_PAYLOAD_BYTES": 65536,
    "SUMMARY_TOKEN": "your-secure-secret-token",
}
```

Add to `urls.py`:

```python
path("analytics/", include("concept_analytics.urls")),
```

### Migrations

```bash
python manage.py migrate
```

---

## Frontend Installation & Setup

The frontend tracker is located in the `frontend/` directory. For a Docusaurus project:

1. Copy the contents of `frontend/src/` to your Docusaurus `src/analytics/` folder.
2. Wrap your site in the `AnalyticsProvider` (typically in `src/theme/Root.js`).
3. Use the `docx_to_mdx.py` pipeline to automatically inject `<TrackedBlock>` components.

### Local Development (Frontend)
Navigate to the frontend directory:
```bash
cd frontend
npm install
npm test
```

---

## Security & Privacy
- **No PII:** The system does not store IP addresses or personal identifiers.
- **Bot Filtering:** Includes built-in scoring to filter out crawlers and mechanical traffic.
- **Suppression:** Public summary endpoints suppress data for blocks with fewer than 10 unique sessions.
- **Opt-out:** Respects a `concept_analytics_optout` key in `localStorage`.
