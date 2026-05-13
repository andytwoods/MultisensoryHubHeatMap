# Multisensory Hub Concept Analytics

A lightweight, privacy-conscious analytics system for tracking user engagement and "dwell time" on concept-based documentation sites. 

This project consists of a **Django backend** for data ingestion and processing, and a **React frontend** tracking library designed for Docusaurus.

## Project Structure

- `concept_analytics/`: The Django app (pip-installable).
- `frontend/`: The React tracking components and hooks.
- `scripts/`: Tooling for manifest generation and validation.
- `tests/`: Comprehensive Python test suite.

---

## Backend Installation & Setup

### 1. Requirements
- Python 3.12+
- Django 4.2+
- `django-cors-headers`

### 2. Installation
Install the package using [uv](https://github.com/astral-sh/uv) (recommended):
```bash
uv sync
```
Or via pip in editable mode:
```bash
pip install -e .
```

### 3. Django Configuration
Add the following to your `settings.py`:

```python
INSTALLED_APPS = [
    ...,
    "corsheaders",
    "concept_analytics",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware", # Must be above CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    ...,
]

# Analytics Settings
CONCEPT_ANALYTICS = {
    "ALLOWED_ORIGINS": ["https://your-docusaurus-site.com"],
    "MAX_EVENTS_PER_BATCH": 50,
    "MAX_PAYLOAD_BYTES": 65536,
    "SUMMARY_TOKEN": "your-secure-secret-token",
}
```

### 4. Database Migrations
Run the migrations to create the analytics tables:
```bash
python manage.py migrate concept_analytics
```

---

## Local Development (Backend)

### Running Tests
We use `pytest` for the backend test suite. Ensure `pytest-django` is installed.

```bash
# Set PYTHONPATH to the app directory if running from the root
$env:PYTHONPATH="."; pytest
```

### Management Commands
Rebuild the summary tables from raw event data:
```bash
python manage.py refresh_concept_analytics_summaries --days 7
```

Import a block manifest from your frontend:
```bash
python manage.py import_manifest path/to/manifest.json --purge
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
