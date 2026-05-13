# PLAN.md – concept_analytics build plan

This document is the authoritative build plan for the `concept_analytics` Django app and associated React frontend. Read `OVERVIEW.md` in full before starting. All design decisions, field names, event names, and terminology are defined there. This plan specifies **what to build, in what order, and how to verify it**.

---

## Rules for the agent

1. **Read OVERVIEW.md before every phase.** It is the authoritative source. If PLAN.md and OVERVIEW.md conflict, OVERVIEW.md wins — flag the conflict before proceeding.
2. **Do not start a phase until all tests for the previous phase pass.**
3. **Do not add features, fields, or behaviour beyond what is specified.** If something seems missing, stop and ask.
4. **Do not modify OVERVIEW.md or PLAN.md** unless explicitly instructed.
5. **Never store raw IP addresses** in any database table. Use them transiently only.
6. **Never use `CORS_ALLOW_ALL_ORIGINS = True`.**
7. **Never skip writing tests.** Every phase has required tests. Write them first if that helps.
8. Mark each checklist item `[x]` only when the code is written **and** the relevant tests pass.

---

## Repository layout

There are **two repositories** involved. Understand the split before writing any code.

### This repo: MultisensoryHubHeatMap (the submodule)

Contains the reusable Django app and canonical copies of the React components. The Django app is pip-installable from here.

```
MultisensoryHubHeatMap/
  concept_analytics/              ← Django app (pip-installable)
    __init__.py
    apps.py
    admin.py
    models.py
    urls.py
    validators.py
    bot_detection.py
    views/
      __init__.py
      ingest.py
      dashboard.py
      public_summary.py
    serializers.py
    middleware.py
    management/
      __init__.py
      commands/
        __init__.py
        refresh_concept_analytics_summaries.py
    migrations/
      __init__.py
    templates/
      concept_analytics/
        dashboard/
          base.html
          heatmap.html
          topic_summary.html
    static/
      concept_analytics/
        dashboard.css
  frontend/                       ← canonical React source (deployed into MultisensoryHub)
    src/
      AnalyticsProvider.jsx
      TrackedBlock.jsx
      hooks/
        useRouteAnalytics.js
        useUserActivity.js
        useConceptTracker.js
      tracker.js
      constants.js
      ErrorBoundary.jsx
    package.json                  ← for running Jest tests only
    jest.config.js
  scripts/
    validate_public_summary.py    ← used by GitHub Actions in MultisensoryHub
    validate_manifest.py
    generate_manifest.py
  tests/
    conftest.py
    settings_test.py
    test_models.py
    test_ingest.py
    test_validators.py
    test_bot_detection.py
    test_public_summary.py
    test_management_commands.py
  pyproject.toml
  README.md
  OVERVIEW.md
  PLAN.md
```

### Parent repo: MultisensoryHub (the Docusaurus site)

The existing site repo at `https://github.com/StoryFutures/multisensoryReport`. This is where the tracker runs, where the analytics config lives, and where public summary JSON is committed. The `MultisensoryHubHeatMap` submodule lives at `MultisensoryHub/multisensoryHubHeatMap/`.

Files that the analytics system adds or modifies in MultisensoryHub:

```
MultisensoryHub/
  analytics/                                     ← NEW: human-edited analytics config
    tracked-blocks.yml                           ← source of truth for TrackedBlock injection
    concepts.yml
    manifest.schema.json
    analytics-notice.md
  docusaurus-site/
    static/
      analytics/                                 ← NEW: generated public summary JSON
        public-summary.latest.json
        block-heatmap.latest.json
    src/
      analytics/                                 ← NEW: copied from MultisensoryHubHeatMap/frontend/src/
        AnalyticsProvider.jsx
        tracker.js
        constants.js
        ErrorBoundary.jsx
        hooks/
          useRouteAnalytics.js
          useUserActivity.js
          useConceptTracker.js
      components/
        TrackedBlock.jsx                         ← NEW: copied from frontend/src/
      theme/
        Root.js                                  ← NEW or MODIFIED: wraps site in AnalyticsProvider
  .github/
    workflows/
      deploy.yml                                 ← EXISTING: do not modify
      update-analytics.yml                       ← NEW: nightly summary pull
  docx_to_mdx.py                                 ← MODIFIED: adds TrackedBlock injection step
  multisensoryHubHeatMap/                        ← git submodule (this repo)
```

---

## Development host project

Build and test the app inside a **minimal Django host project** (separate directory, not in this repo):

```
dev_host/
  manage.py
  dev_host/
    settings.py     ← installs concept_analytics via pip install -e /path/to/MultisensoryHubHeatMap
    urls.py
    wsgi.py
```

Minimal `INSTALLED_APPS` for the dev host:
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "concept_analytics",
]
```

The app must be installable with:
```bash
pip install -e /path/to/MultisensoryHubHeatMap
```

Do not hard-code any settings from the dev host or from `costartools.uk` into the app itself. All configuration must go through Django settings.

---

## Testing setup

All tests live in `tests/` within this repo. Use `pytest` + `pytest-django`.

`tests/settings_test.py`:
```python
SECRET_KEY = "test-secret-key-not-for-production"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "concept_analytics",
]
CONCEPT_ANALYTICS = {
    "ALLOWED_ORIGINS": ["https://storyfutures.github.io"],
    "MAX_EVENTS_PER_BATCH": 50,
    "MAX_PAYLOAD_BYTES": 65536,
    "IDLE_THRESHOLD_SECONDS": 60,
    "SUMMARY_TOKEN": "test-token",
}
```

`pytest.ini` or `pyproject.toml` `[tool.pytest.ini_options]`:
```ini
DJANGO_SETTINGS_MODULE = tests.settings_test
```

Run all tests:
```bash
pytest tests/
```

---

## Phase 0 — Package scaffolding

**Goal:** A pip-installable, importable Django app with no models yet.

### Tasks

- [x] Create `concept_analytics/__init__.py` (empty)
- [x] Create `concept_analytics/apps.py`:
  ```python
  from django.apps import AppConfig

  class ConceptAnalyticsConfig(AppConfig):
      name = "concept_analytics"
      default_auto_field = "django.db.models.BigAutoField"
  ```
- [x] Create `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["setuptools>=68"]
  build-backend = "setuptools.backends.legacy:build"

  [project]
  name = "concept-analytics"
  version = "0.1.0"
  requires-python = ">=3.11"
  dependencies = [
      "Django>=4.2",
      "django-cors-headers>=4.0",
  ]

  [tool.pytest.ini_options]
  DJANGO_SETTINGS_MODULE = "tests.settings_test"
  ```
- [x] Create `tests/__init__.py`, `tests/settings_test.py`, `tests/conftest.py` (empty for now)
- [x] Create `concept_analytics/migrations/__init__.py`

### Tests

`tests/test_import.py`:
```python
def test_app_importable():
    import concept_analytics
    assert concept_analytics is not None

def test_app_config():
    from concept_analytics.apps import ConceptAnalyticsConfig
    assert ConceptAnalyticsConfig.name == "concept_analytics"
```

### Done when
- `pytest tests/test_import.py` passes
- `pip install -e .` succeeds without errors

---

## Phase 1 — Models and migrations

**Goal:** All database models defined, migrated, and registered in Django admin.

### Settings contract

The app reads configuration from `settings.CONCEPT_ANALYTICS` (a dict). Provide a helper:

`concept_analytics/conf.py`:
```python
from django.conf import settings

DEFAULTS = {
    "ALLOWED_ORIGINS": [],
    "MAX_EVENTS_PER_BATCH": 50,
    "MAX_PAYLOAD_BYTES": 65536,
    "IDLE_THRESHOLD_SECONDS": 60,
    "SUMMARY_TOKEN": "",
}

def get_setting(key):
    user = getattr(settings, "CONCEPT_ANALYTICS", {})
    return user.get(key, DEFAULTS[key])
```

### Models

`concept_analytics/models.py` — implement exactly these models:

**`AnalyticsSession`**
| Field | Type | Notes |
|---|---|---|
| `session_id` | `CharField(max_length=64, unique=True, db_index=True)` | client-generated UUID |
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `last_seen_at` | `DateTimeField(auto_now=True)` | |
| `landing_path` | `CharField(max_length=500, blank=True)` | |
| `referrer_domain` | `CharField(max_length=253, blank=True)` | |
| `device_class` | `CharField(max_length=20, blank=True)` | `desktop`, `mobile`, `tablet`, `unknown` |
| `browser_family` | `CharField(max_length=50, blank=True)` | |
| `is_suspicious` | `BooleanField(default=False)` | |
| `human_likelihood` | `CharField(max_length=12, default="unknown")` | choices: `human_likely`, `bot_likely`, `unknown` |

**`AnalyticsEvent`**
| Field | Type | Notes |
|---|---|---|
| `id` | auto BigAutoField | |
| `session` | `ForeignKey(AnalyticsSession, on_delete=PROTECT, related_name="events")` | |
| `received_at` | `DateTimeField(auto_now_add=True)` | |
| `timestamp_client` | `DateTimeField(null=True, blank=True)` | |
| `event_sequence` | `PositiveIntegerField()` | client-assigned sequence within session |
| `page_path` | `CharField(max_length=500)` | |
| `page_title` | `CharField(max_length=500, blank=True)` | |
| `event_type` | `CharField(max_length=50, db_index=True)` | |
| `block_id` | `CharField(max_length=200, blank=True, db_index=True)` | |
| `block_version_id` | `CharField(max_length=300, blank=True, db_index=True)` | |
| `content_hash` | `CharField(max_length=80, blank=True, db_index=True)` | |
| `topic` | `CharField(max_length=100, blank=True, db_index=True)` | |
| `concept` | `CharField(max_length=100, blank=True, db_index=True)` | |
| `content_type` | `CharField(max_length=50, blank=True)` | |
| `previous_page_path` | `CharField(max_length=500, blank=True)` | |
| `previous_block_id` | `CharField(max_length=200, blank=True)` | |
| `seconds_since_previous_event` | `FloatField(null=True, blank=True)` | |
| `seconds_visible` | `FloatField(null=True, blank=True)` | |
| `intersection_ratio` | `FloatField(null=True, blank=True)` | 0.0–1.0 |
| `scroll_depth` | `FloatField(null=True, blank=True)` | 0.0–1.0 |
| `target_path` | `CharField(max_length=500, blank=True)` | internal links/downloads only |
| `target_domain` | `CharField(max_length=253, blank=True)` | external links: domain only |
| `metadata` | `JSONField(default=dict, blank=True)` | documented keys only |

Add `class Meta` with `indexes` on `(session, event_sequence)` and `created_at` (use `received_at` as the time index name: `received_at`).

**`BlockManifestEntry`**
| Field | Type | Notes |
|---|---|---|
| `block_id` | `CharField(max_length=200, unique=True, db_index=True)` | |
| `block_version_id` | `CharField(max_length=300, blank=True)` | |
| `content_hash` | `CharField(max_length=80, blank=True)` | |
| `position_hash` | `CharField(max_length=80, blank=True)` | |
| `page_path` | `CharField(max_length=500)` | |
| `page_title` | `CharField(max_length=500, blank=True)` | |
| `heading_path` | `CharField(max_length=1000, blank=True)` | pipe-separated heading hierarchy |
| `display_order` | `PositiveIntegerField(default=0)` | |
| `topic` | `CharField(max_length=100, blank=True)` | |
| `concept` | `CharField(max_length=100, blank=True)` | |
| `content_type` | `CharField(max_length=50, blank=True)` | |
| `label` | `CharField(max_length=500, blank=True)` | |
| `parent_block_id` | `CharField(max_length=200, blank=True)` | |
| `is_active` | `BooleanField(default=True)` | |
| `first_seen_at` | `DateTimeField(auto_now_add=True)` | |
| `updated_at` | `DateTimeField(auto_now=True)` | |

**`DailyBlockSummary`**
| Field | Type |
|---|---|
| `date` | `DateField(db_index=True)` |
| `block_id` | `CharField(max_length=200, db_index=True)` |
| `block_version_id` | `CharField(max_length=300, blank=True)` |
| `topic` | `CharField(max_length=100, blank=True)` |
| `concept` | `CharField(max_length=100, blank=True)` |
| `unique_sessions` | `PositiveIntegerField(default=0)` |
| `event_count` | `PositiveIntegerField(default=0)` |
| `total_visible_seconds` | `FloatField(default=0.0)` |
| `median_visible_seconds` | `FloatField(null=True)` |
| `interaction_count` | `PositiveIntegerField(default=0)` |
| `downloads_after_exposure` | `PositiveIntegerField(default=0)` |
| `external_clicks_after_exposure` | `PositiveIntegerField(default=0)` |

Add `unique_together = [("date", "block_id", "block_version_id")]`.

**`DailyTopicSummary`**
| Field | Type |
|---|---|
| `date` | `DateField(db_index=True)` |
| `topic` | `CharField(max_length=100, db_index=True)` |
| `unique_sessions` | `PositiveIntegerField(default=0)` |
| `total_visible_seconds` | `FloatField(default=0.0)` |
| `interaction_count` | `PositiveIntegerField(default=0)` |

Add `unique_together = [("date", "topic")]`.

**`DailyTransitionSummary`**
| Field | Type |
|---|---|
| `date` | `DateField(db_index=True)` |
| `from_page_path` | `CharField(max_length=500)` |
| `to_page_path` | `CharField(max_length=500)` |
| `from_block_id` | `CharField(max_length=200, blank=True)` |
| `to_block_id` | `CharField(max_length=200, blank=True)` |
| `from_topic` | `CharField(max_length=100, blank=True)` |
| `to_topic` | `CharField(max_length=100, blank=True)` |
| `transition_count` | `PositiveIntegerField(default=0)` |
| `unique_sessions` | `PositiveIntegerField(default=0)` |

### Admin

`concept_analytics/admin.py` — register all five models with:
- `AnalyticsSession`: list_display = `session_id`, `human_likelihood`, `is_suspicious`, `created_at`, `last_seen_at`; list_filter = `human_likelihood`, `is_suspicious`, `device_class`; search_fields = `session_id`; readonly_fields for all fields
- `AnalyticsEvent`: list_display = `session`, `event_type`, `block_id`, `topic`, `received_at`; list_filter = `event_type`, `topic`; search_fields = `block_id`, `page_path`; readonly_fields for all fields. **No inline editing of any event.**
- `BlockManifestEntry`: list_display = `block_id`, `topic`, `concept`, `is_active`, `updated_at`; list_filter = `topic`, `is_active`
- Summary tables: register read-only with list_display showing date and key metrics

### Tests

`tests/test_models.py`:
```python
import pytest
from django.utils import timezone
from concept_analytics.models import AnalyticsSession, AnalyticsEvent, BlockManifestEntry

@pytest.mark.django_db
def test_session_create():
    s = AnalyticsSession.objects.create(session_id="test-uuid-1234")
    assert s.human_likelihood == "unknown"
    assert s.is_suspicious is False

@pytest.mark.django_db
def test_event_requires_session():
    s = AnalyticsSession.objects.create(session_id="test-uuid-5678")
    e = AnalyticsEvent.objects.create(
        session=s,
        event_sequence=1,
        page_path="/test",
        event_type="page_view",
    )
    assert e.received_at is not None

@pytest.mark.django_db
def test_block_manifest_entry():
    b = BlockManifestEntry.objects.create(
        block_id="scent-intro",
        page_path="/docs/scent",
        topic="scent",
    )
    assert b.is_active is True

@pytest.mark.django_db
def test_event_metadata_defaults_to_empty_dict():
    s = AnalyticsSession.objects.create(session_id="meta-test")
    e = AnalyticsEvent.objects.create(session=s, event_sequence=1, page_path="/", event_type="page_view")
    assert e.metadata == {}

@pytest.mark.django_db
def test_intersection_ratio_null():
    s = AnalyticsSession.objects.create(session_id="ratio-test")
    e = AnalyticsEvent.objects.create(session=s, event_sequence=1, page_path="/", event_type="page_view")
    assert e.intersection_ratio is None
```

### Done when
- `pytest tests/test_models.py` passes
- `python manage.py migrate` succeeds in the dev host
- All five models appear in Django admin with correct list_display

---

## Phase 2 — Payload validation

**Goal:** A standalone validator module that parses and validates ingest payloads before any database writes.

### Implementation

`concept_analytics/validators.py` — implement `validate_ingest_payload(data: dict) -> dict`:

Rules (raise `ValidationError` with a descriptive message on failure):
1. `session_id` must be present, a string, 8–64 characters, alphanumeric/hyphens/underscores only
2. `page_path` must be present, a string, starts with `/`, max 500 chars
3. `events` must be a non-empty list
4. Number of events must not exceed `get_setting("MAX_EVENTS_PER_BATCH")`
5. Each event must have `event_type` (string, max 50 chars) and `event_sequence` (non-negative integer)
6. `event_type` must be in the allowed set (see OVERVIEW.md §8): `session_start`, `page_view`, `page_visible_heartbeat`, `page_hidden`, `page_unload`, `session_resume`, `concept_enter_view`, `concept_visible_heartbeat`, `concept_exit_view`, `section_opened`, `accordion_opened`, `tab_selected`, `case_study_opened`, `video_played`, `audio_played`, `interactive_started`, `download_clicked`, `external_link_clicked`, `internal_link_clicked`, `search_submitted`
7. `intersection_ratio` if present must be 0.0–1.0
8. `scroll_depth` if present must be 0.0–1.0
9. `seconds_visible` if present must be >= 0 and < 3600
10. `block_id` if present: string, max 200 chars, alphanumeric/hyphens/underscores only
11. `referrer_domain` if present: max 253 chars, no protocol prefix, no path
12. `target_path` if present: must start with `/`, max 500 chars
13. `target_domain` if present: max 253 chars, no protocol or path
14. Unknown top-level payload keys are allowed (ignore, do not error)
15. Unknown event keys are allowed (ignore, do not error)

Return the validated and cleaned data dict (do not mutate the original).

### Tests

`tests/test_validators.py`:
```python
import pytest
from django.core.exceptions import ValidationError
from concept_analytics.validators import validate_ingest_payload

MINIMAL_VALID = {
    "session_id": "abc-123",
    "page_path": "/docs/scent",
    "events": [{"event_type": "page_view", "event_sequence": 1}],
}

def test_valid_payload():
    result = validate_ingest_payload(MINIMAL_VALID)
    assert result["session_id"] == "abc-123"

def test_missing_session_id():
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "session_id": None})

def test_invalid_session_id_chars():
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "session_id": "bad id with spaces"})

def test_session_id_too_short():
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "session_id": "ab"})

def test_missing_page_path():
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "page_path": None})

def test_page_path_no_slash():
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "page_path": "docs/scent"})

def test_empty_events():
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "events": []})

def test_too_many_events():
    events = [{"event_type": "page_view", "event_sequence": i} for i in range(51)]
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "events": events})

def test_unknown_event_type():
    bad = {**MINIMAL_VALID, "events": [{"event_type": "invented_event", "event_sequence": 1}]}
    with pytest.raises(ValidationError):
        validate_ingest_payload(bad)

def test_intersection_ratio_out_of_range():
    event = {"event_type": "concept_visible_heartbeat", "event_sequence": 1, "intersection_ratio": 1.5}
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "events": [event]})

def test_unknown_top_level_keys_are_ignored():
    payload = {**MINIMAL_VALID, "unknown_future_field": "ignored"}
    result = validate_ingest_payload(payload)
    assert result is not None

def test_target_domain_no_path():
    event = {"event_type": "external_link_clicked", "event_sequence": 1, "target_domain": "example.org/path/bad"}
    with pytest.raises(ValidationError):
        validate_ingest_payload({**MINIMAL_VALID, "events": [event]})

def test_referrer_domain_no_protocol():
    payload = {**MINIMAL_VALID, "referrer_domain": "https://example.org"}
    with pytest.raises(ValidationError):
        validate_ingest_payload(payload)
```

### Done when
- `pytest tests/test_validators.py` passes (all 12 tests)

---

## Phase 3 — Bot detection

**Goal:** A bot scoring function that classifies a session as `human_likely`, `bot_likely`, or `unknown` from request and payload signals.

### Implementation

`concept_analytics/bot_detection.py` — implement `score_session(user_agent: str, events: list[dict]) -> str`:

Rules (return `"bot_likely"` if any of these trigger):
1. `user_agent` is empty
2. `user_agent` matches any of these patterns (case-insensitive): `bot`, `crawler`, `spider`, `scraper`, `curl`, `wget`, `python-requests`, `java/`, `go-http`, `headless`
3. Number of events > 30 (impossible for human in one batch at 15s heartbeat)
4. All event `event_sequence` values are identical (mechanical)
5. All events have the same `event_type` and count > 5 (mechanical repetition)

Return `"unknown"` if none of the above trigger.

Return `"human_likely"` only when:
- user_agent is non-empty and not bot-pattern-matched; AND
- at least one event is a non-`page_view`, non-`session_start` event type (implies real interaction); AND
- events contain at least 2 distinct `event_sequence` values

Otherwise return `"unknown"`.

### Tests

`tests/test_bot_detection.py`:
```python
from concept_analytics.bot_detection import score_session

def test_empty_user_agent_is_bot():
    assert score_session("", [{"event_type": "page_view", "event_sequence": 1}]) == "bot_likely"

def test_googlebot_is_bot():
    assert score_session("Googlebot/2.1", [{"event_type": "page_view", "event_sequence": 1}]) == "bot_likely"

def test_curl_is_bot():
    assert score_session("curl/7.88", [{"event_type": "page_view", "event_sequence": 1}]) == "bot_likely"

def test_too_many_events_is_bot():
    events = [{"event_type": "page_view", "event_sequence": i} for i in range(31)]
    assert score_session("Mozilla/5.0 Safari", events) == "bot_likely"

def test_real_browser_with_interaction_is_human():
    events = [
        {"event_type": "page_view", "event_sequence": 1},
        {"event_type": "download_clicked", "event_sequence": 2},
    ]
    assert score_session("Mozilla/5.0 (Windows NT 10.0) Safari/537.36", events) == "human_likely"

def test_only_page_view_is_unknown():
    events = [{"event_type": "page_view", "event_sequence": 1}]
    assert score_session("Mozilla/5.0 Safari", events) == "unknown"

def test_identical_sequences_is_bot():
    events = [{"event_type": "page_view", "event_sequence": 1} for _ in range(5)]
    assert score_session("Mozilla/5.0 Safari", events) == "bot_likely"
```

### Done when
- `pytest tests/test_bot_detection.py` passes (all 7 tests)

---

## Phase 4 — Ingest endpoint

**Goal:** A working POST endpoint that accepts, validates, and persists event batches from the Docusaurus tracker.

### URL

```
POST /concept-analytics/ingest/
```

### Implementation

`concept_analytics/views/ingest.py` — implement `IngestView` as a Django `View`:

Behaviour (in order):
1. Check `request.method == "POST"`, return 405 otherwise
2. Check `Content-Type` is `application/json` or `text/plain`; return 415 otherwise
3. Check payload size ≤ `get_setting("MAX_PAYLOAD_BYTES")`; return 413 if exceeded
4. Check `Origin` header is in `get_setting("ALLOWED_ORIGINS")`; return 403 if not (log a warning)
5. Parse JSON body; return 400 on parse failure
6. Call `validate_ingest_payload(data)`; return 400 with error message on `ValidationError`
7. Call `score_session(user_agent, events)` to get `human_likelihood`
8. `get_or_create` `AnalyticsSession` by `session_id`; update `last_seen_at`, `human_likelihood`, `is_suspicious` (set `True` if `bot_likely`)
9. For each event in the validated payload: create `AnalyticsEvent` linked to the session. Skip duplicate `(session, event_sequence)` pairs silently.
10. Return `{"status": "ok", "accepted": N}` with HTTP 202

Decorator: `@method_decorator(csrf_exempt, name="dispatch")`

`concept_analytics/urls.py`:
```python
from django.urls import path
from .views.ingest import IngestView
from .views.public_summary import PublicSummaryView
from .views.dashboard import DashboardView

urlpatterns = [
    path("ingest/", IngestView.as_view(), name="concept_analytics_ingest"),
    path("summary/latest/", PublicSummaryView.as_view(), name="concept_analytics_summary"),
    path("dashboard/", DashboardView.as_view(), name="concept_analytics_dashboard"),
]
```

Document in `README.md` that the host project should add:
```python
path("concept-analytics/", include("concept_analytics.urls")),
```

### Tests

`tests/test_ingest.py`:
```python
import json
import pytest
from django.test import Client
from concept_analytics.models import AnalyticsSession, AnalyticsEvent

VALID_PAYLOAD = {
    "session_id": "test-session-01",
    "page_path": "/docs/scent",
    "events": [
        {"event_type": "page_view", "event_sequence": 1},
        {"event_type": "download_clicked", "event_sequence": 2},
    ],
}

ORIGIN = "https://storyfutures.github.io"

@pytest.fixture
def client():
    return Client()

@pytest.mark.django_db
def test_ingest_creates_session(client):
    resp = client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(VALID_PAYLOAD),
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
    )
    assert resp.status_code == 202
    assert AnalyticsSession.objects.filter(session_id="test-session-01").exists()

@pytest.mark.django_db
def test_ingest_creates_events(client):
    client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(VALID_PAYLOAD),
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
    )
    assert AnalyticsEvent.objects.filter(session__session_id="test-session-01").count() == 2

@pytest.mark.django_db
def test_ingest_wrong_origin_returns_403(client):
    resp = client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(VALID_PAYLOAD),
        content_type="application/json",
        HTTP_ORIGIN="https://evil.example.com",
    )
    assert resp.status_code == 403

@pytest.mark.django_db
def test_ingest_bad_json_returns_400(client):
    resp = client.post(
        "/concept-analytics/ingest/",
        data="not json",
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
    )
    assert resp.status_code == 400

@pytest.mark.django_db
def test_ingest_invalid_payload_returns_400(client):
    bad = {**VALID_PAYLOAD, "session_id": None}
    resp = client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(bad),
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
    )
    assert resp.status_code == 400

@pytest.mark.django_db
def test_ingest_text_plain_content_type_accepted(client):
    resp = client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(VALID_PAYLOAD),
        content_type="text/plain",
        HTTP_ORIGIN=ORIGIN,
    )
    assert resp.status_code == 202

@pytest.mark.django_db
def test_ingest_duplicate_event_sequence_skipped(client):
    client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(VALID_PAYLOAD),
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
    )
    client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(VALID_PAYLOAD),
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
    )
    assert AnalyticsEvent.objects.filter(session__session_id="test-session-01").count() == 2

@pytest.mark.django_db
def test_bot_session_marked_suspicious(client):
    payload = {
        "session_id": "bot-session-01",
        "page_path": "/docs/scent",
        "events": [{"event_type": "page_view", "event_sequence": 1}],
    }
    client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
        HTTP_USER_AGENT="Googlebot/2.1",
    )
    session = AnalyticsSession.objects.get(session_id="bot-session-01")
    assert session.is_suspicious is True
    assert session.human_likelihood == "bot_likely"

@pytest.mark.django_db
def test_no_ip_stored(client):
    client.post(
        "/concept-analytics/ingest/",
        data=json.dumps(VALID_PAYLOAD),
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
    )
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM concept_analytics_analyticssession")
        columns = [d[0] for d in cursor.description]
    assert "ip_address" not in columns
    assert "ip" not in columns
```

### CORS configuration

`concept_analytics/apps.py` — add a note comment that the host project must add `corsheaders` to `INSTALLED_APPS` and `MIDDLEWARE` (before `CommonMiddleware`). Document this in `README.md`.

### Done when
- `pytest tests/test_ingest.py` passes (all 9 tests)
- No IP address field exists in any model (verified by last test)

---

## Phase 5 — Public summary endpoint

**Goal:** A read-only, bearer-token-protected endpoint that returns suppressed aggregate JSON for use by GitHub Actions.

### URL

```
GET /concept-analytics/summary/latest/
```

### Implementation

`concept_analytics/views/public_summary.py` — implement `PublicSummaryView`:

1. Accept only `GET`; return 405 otherwise
2. Check `Authorization: Bearer <token>` header against `get_setting("SUMMARY_TOKEN")`; return 401 if missing or wrong
3. Query `DailyBlockSummary` and `DailyTopicSummary` for the last 30 days
4. Apply suppression: exclude any `block_id` with `unique_sessions < 10` across the period
5. Return JSON with this exact top-level structure:
```json
{
  "generated_at": "<ISO 8601 UTC>",
  "date_range": {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"},
  "contains_raw_events": false,
  "suppression": {"min_sessions": 10},
  "blocks": [...],
  "topics": [...]
}
```
6. Each block entry: `block_id`, `topic`, `concept`, `unique_sessions`, `total_visible_seconds`, `interaction_count`
7. Each topic entry: `topic`, `unique_sessions`, `total_visible_seconds`, `interaction_count`
8. No session IDs, no individual paths, no raw timestamps in response

### Tests

`tests/test_public_summary.py`:
```python
import json
import pytest
from django.test import Client
from concept_analytics.models import DailyBlockSummary, DailyTopicSummary
from datetime import date

@pytest.fixture
def client():
    return Client()

TOKEN = "test-token"
AUTH = f"Bearer {TOKEN}"

@pytest.mark.django_db
def test_summary_requires_auth(client):
    resp = client.get("/concept-analytics/summary/latest/")
    assert resp.status_code == 401

@pytest.mark.django_db
def test_summary_wrong_token(client):
    resp = client.get("/concept-analytics/summary/latest/", HTTP_AUTHORIZATION="Bearer wrong")
    assert resp.status_code == 401

@pytest.mark.django_db
def test_summary_returns_correct_structure(client):
    DailyBlockSummary.objects.create(
        date=date.today(), block_id="scent-intro", topic="scent",
        unique_sessions=15, total_visible_seconds=300.0, interaction_count=5,
    )
    resp = client.get("/concept-analytics/summary/latest/", HTTP_AUTHORIZATION=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["contains_raw_events"] is False
    assert "generated_at" in data
    assert "date_range" in data
    assert "suppression" in data
    assert "blocks" in data
    assert "topics" in data

@pytest.mark.django_db
def test_summary_suppresses_low_session_blocks(client):
    DailyBlockSummary.objects.create(
        date=date.today(), block_id="rare-block", topic="scent",
        unique_sessions=3, total_visible_seconds=10.0, interaction_count=0,
    )
    resp = client.get("/concept-analytics/summary/latest/", HTTP_AUTHORIZATION=AUTH)
    data = resp.json()
    block_ids = [b["block_id"] for b in data["blocks"]]
    assert "rare-block" not in block_ids

@pytest.mark.django_db
def test_summary_no_session_ids_in_response(client):
    resp = client.get("/concept-analytics/summary/latest/", HTTP_AUTHORIZATION=AUTH)
    assert resp.status_code in (200, 200)
    text = resp.content.decode()
    assert "session_id" not in text

@pytest.mark.django_db
def test_summary_post_not_allowed(client):
    resp = client.post("/concept-analytics/summary/latest/", HTTP_AUTHORIZATION=AUTH)
    assert resp.status_code == 405
```

### Done when
- `pytest tests/test_public_summary.py` passes (all 6 tests)

---

## Phase 6 — Management command: refresh summaries

**Goal:** A management command that rebuilds all daily summary tables from raw `AnalyticsEvent` data.

### Implementation

`concept_analytics/management/commands/refresh_concept_analytics_summaries.py`

Command: `python manage.py refresh_concept_analytics_summaries`

Options:
- `--date YYYY-MM-DD`: refresh a specific date (default: yesterday)
- `--days N`: refresh the last N days (default: 1)

Logic for `DailyBlockSummary`:
- For each `(date, block_id, block_version_id)` combination in `AnalyticsEvent` filtered by `received_at__date`:
  - `unique_sessions`: count distinct `session_id` values
  - `event_count`: count of all events for the block on that date
  - `total_visible_seconds`: sum of `seconds_visible` (non-null)
  - `median_visible_seconds`: compute in Python after querying (sort + midpoint)
  - `interaction_count`: count events where `event_type` in `section_opened`, `accordion_opened`, `tab_selected`, `case_study_opened`, `video_played`, `audio_played`, `interactive_started`
  - `downloads_after_exposure`: count `download_clicked` events in sessions that also had a `concept_visible_heartbeat` for this `block_id`
  - `external_clicks_after_exposure`: same pattern for `external_link_clicked`
- Use `update_or_create` on `(date, block_id, block_version_id)`

Logic for `DailyTopicSummary`:
- Aggregate `AnalyticsEvent` by `(date, topic)` similarly

Logic for `DailyTransitionSummary`:
- For each session on that date, order events by `event_sequence`
- For each consecutive pair of events where `page_path` changes: record a `(from_page_path, to_page_path)` transition
- For consecutive events where `block_id` is non-empty and changes: record `(from_block_id, to_block_id)` transition
- Aggregate counts and unique sessions across all sessions

### Tests

`tests/test_management_commands.py`:
```python
import pytest
from datetime import date, timedelta
from django.core.management import call_command
from concept_analytics.models import (
    AnalyticsSession, AnalyticsEvent,
    DailyBlockSummary, DailyTopicSummary, DailyTransitionSummary,
)

def make_session(session_id):
    return AnalyticsSession.objects.create(session_id=session_id)

def make_event(session, seq, event_type, page_path="/docs/scent", block_id="scent-intro",
               topic="scent", seconds_visible=None):
    return AnalyticsEvent.objects.create(
        session=session, event_sequence=seq, event_type=event_type,
        page_path=page_path, block_id=block_id, topic=topic,
        seconds_visible=seconds_visible,
    )

@pytest.mark.django_db
def test_refresh_creates_block_summary():
    today = date.today()
    s = make_session("cmd-test-01")
    make_event(s, 1, "concept_visible_heartbeat", seconds_visible=15.0)
    make_event(s, 2, "download_clicked")
    call_command("refresh_concept_analytics_summaries", date=today.isoformat())
    summary = DailyBlockSummary.objects.get(date=today, block_id="scent-intro")
    assert summary.unique_sessions >= 1
    assert summary.total_visible_seconds >= 15.0

@pytest.mark.django_db
def test_refresh_creates_topic_summary():
    today = date.today()
    s = make_session("cmd-test-02")
    make_event(s, 1, "page_view", topic="scent")
    call_command("refresh_concept_analytics_summaries", date=today.isoformat())
    assert DailyTopicSummary.objects.filter(date=today, topic="scent").exists()

@pytest.mark.django_db
def test_refresh_creates_transition_summary():
    today = date.today()
    s = make_session("cmd-test-03")
    make_event(s, 1, "page_view", page_path="/docs/intro", block_id="")
    make_event(s, 2, "page_view", page_path="/docs/scent", block_id="")
    call_command("refresh_concept_analytics_summaries", date=today.isoformat())
    assert DailyTransitionSummary.objects.filter(
        date=today, from_page_path="/docs/intro", to_page_path="/docs/scent"
    ).exists()

@pytest.mark.django_db
def test_refresh_idempotent():
    today = date.today()
    s = make_session("cmd-test-04")
    make_event(s, 1, "concept_visible_heartbeat", seconds_visible=10.0)
    call_command("refresh_concept_analytics_summaries", date=today.isoformat())
    call_command("refresh_concept_analytics_summaries", date=today.isoformat())
    assert DailyBlockSummary.objects.filter(date=today, block_id="scent-intro").count() == 1
```

### Done when
- `pytest tests/test_management_commands.py` passes (all 4 tests)
- `python manage.py refresh_concept_analytics_summaries` runs without errors in the dev host

---

## Phase 7 — Private HTMX dashboard

**Goal:** A password-protected internal dashboard with a basic heat map view.

### Implementation

`concept_analytics/views/dashboard.py` — implement `DashboardView`:

1. Require login: redirect to Django login if not authenticated
2. Require permission `concept_analytics.view_analyticsevent` OR staff status; return 403 otherwise
3. Accept optional `?metric=unique_sessions` (default) or `?metric=total_visible_seconds` or `?metric=interaction_count`
4. Accept optional `?filter=human_likely` (default), `human_and_unknown`, `all`
5. Query `DailyBlockSummary` for last 30 days aggregated by `block_id`
6. Join to `BlockManifestEntry` for ordering (`display_order`, `page_path`)
7. Pass data to template `concept_analytics/dashboard/heatmap.html`

Template requirements:
- Display page title: "Concept Analytics Dashboard"
- List each page as a card; list each tracked block within the card as a coloured bar
- Bar colour intensity = normalised metric value (use inline CSS `opacity` or a utility class)
- Metric toggle links (three `<a>` tags that reload with `?metric=...`)
- Filter toggle links (three `<a>` tags that reload with `?filter=...`)
- Bot traffic warning if `?filter=all` is selected
- No JavaScript required for basic operation (HTMX enhancements are optional, v3+ task)

`concept_analytics/admin.py` — add the custom permission:
```python
class Meta:
    permissions = [("view_dashboard", "Can view concept analytics dashboard")]
```
Add this to `AnalyticsEvent.Meta`.

### Tests

```python
# tests/test_dashboard.py
import pytest
from django.test import Client
from django.contrib.auth.models import User

@pytest.fixture
def staff_client(db):
    user = User.objects.create_user("staff", password="pass", is_staff=True)
    client = Client()
    client.force_login(user)
    return client

@pytest.fixture
def anon_client():
    return Client()

@pytest.mark.django_db
def test_dashboard_requires_login(anon_client):
    resp = anon_client.get("/concept-analytics/dashboard/")
    assert resp.status_code == 302  # redirect to login

@pytest.mark.django_db
def test_dashboard_accessible_to_staff(staff_client):
    resp = staff_client.get("/concept-analytics/dashboard/")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_dashboard_contains_title(staff_client):
    resp = staff_client.get("/concept-analytics/dashboard/")
    assert b"Concept Analytics" in resp.content

@pytest.mark.django_db
def test_dashboard_metric_toggle(staff_client):
    resp = staff_client.get("/concept-analytics/dashboard/?metric=total_visible_seconds")
    assert resp.status_code == 200
```

### Done when
- `pytest tests/test_dashboard.py` passes (all 4 tests)
- Dashboard renders in browser on dev host with no JavaScript errors in console

---

## Phase 8 — React tracker v1 (frontend)

**Goal:** An `AnalyticsProvider` and `TrackedBlock` that track page views, downloads, and link clicks, with opt-out and Error Boundary. All files go in `frontend/src/`.

### File: `frontend/src/constants.js`

```js
export const OPTOUT_KEY = "concept_analytics_optout";
export const SESSION_KEY = "concept_analytics_session_id";
export const HEARTBEAT_MS = 15000;
export const ALLOWED_EVENT_TYPES = [
  "session_start", "page_view", "page_visible_heartbeat",
  "page_hidden", "page_unload", "session_resume",
  "concept_enter_view", "concept_visible_heartbeat", "concept_exit_view",
  "section_opened", "accordion_opened", "tab_selected",
  "case_study_opened", "video_played", "audio_played",
  "interactive_started", "download_clicked",
  "external_link_clicked", "internal_link_clicked", "search_submitted",
];
```

### File: `frontend/src/tracker.js`

Exports:
- `isOptedOut()` → reads `localStorage.getItem(OPTOUT_KEY) === "1"`
- `optOut()` → sets `localStorage.setItem(OPTOUT_KEY, "1")`
- `optIn()` → removes key
- `getOrCreateSessionId()` → reads `sessionStorage`, creates UUID v4 if absent, returns string
- `sendBatch(endpoint, payload)` → `fetch(endpoint, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)})`; fails silently (catch and log to console only, never throw)
- `flushBeacon(endpoint, payload)` → `navigator.sendBeacon(endpoint, JSON.stringify(payload))` with graceful fallback to `sendBatch`

### File: `frontend/src/AnalyticsProvider.jsx`

Props: `endpoint` (string, required), `children`, `disabled` (bool, default false)

Behaviour:
1. On mount: check `isOptedOut()` and `disabled`; if either true, render children only and do nothing else
2. Get or create session ID from `sessionStorage`
3. Emit `session_start` event (sequence 0)
4. Listen for `visibilitychange`: emit `page_hidden` or `session_resume`
5. On route change (via `useEffect` on `location.pathname`): flush previous page events, emit `page_view`
6. Intercept `download_clicked`: listen for clicks on `<a>` elements where `href` matches `/\.(pdf|docx|xlsx|pptx|zip)$/i`; emit event with `target_path`
7. Intercept `external_link_clicked`: `<a>` elements where `href` starts with `http` and domain ≠ `storyfutures.github.io`; emit event with `target_domain` (domain only)
8. Batch events in a ref queue; flush every `HEARTBEAT_MS`
9. On unmount: flush remaining events with `flushBeacon`
10. Expose context value `{ trackEvent, optOut, optIn, isOptedOut }` via `AnalyticsContext`

Do NOT implement IntersectionObserver in v1. That is v2.

### File: `frontend/src/TrackedBlock.jsx`

Props: `blockId` (required), `topic`, `concept`, `contentType`, `label`, `children`

Behaviour (v1 only):
- In development: warn to console if `blockId` is missing
- Render `<div data-block-id={blockId} data-topic={topic} data-concept={concept} data-content-type={contentType}>` wrapping `children`
- Do not register with IntersectionObserver yet (v2)

### File: `frontend/src/ErrorBoundary.jsx`

Standard React class-based Error Boundary. On error: render `null` (hide analytics silently, never a visible error message). Log error to `console.error`.

### File: `frontend/src/hooks/useRouteAnalytics.js`

A hook that detects Docusaurus route changes via `useLocation()` from `@docusaurus/router` and calls `trackEvent("page_view", { page_path: pathname })` on change.

### Installation into Docusaurus site (MultisensoryHub)

Perform these steps in the **MultisensoryHub** repo, not in this submodule.

**Step 1 — Copy React source files:**
```bash
# From MultisensoryHub root
cp -r multisensoryHubHeatMap/frontend/src/* docusaurus-site/src/analytics/
cp multisensoryHubHeatMap/frontend/src/TrackedBlock.jsx docusaurus-site/src/components/TrackedBlock.jsx
```

**Step 2 — Create `docusaurus-site/src/theme/Root.js`:**
```jsx
import React from 'react';
import ErrorBoundary from '../analytics/ErrorBoundary';
import AnalyticsProvider from '../analytics/AnalyticsProvider';

export default function Root({ children }) {
  return (
    <ErrorBoundary>
      <AnalyticsProvider endpoint={process.env.REACT_APP_ANALYTICS_ENDPOINT || ''}>
        {children}
      </AnalyticsProvider>
    </ErrorBoundary>
  );
}
```

**Step 3 — Set the ingest endpoint** in `docusaurus-site/docusaurus.config.ts` or via an environment variable. Do not hard-code the production URL in committed source.

**Step 4 — `TrackedBlock` is injected automatically** by `docx_to_mdx.py` (Phase 9a). Do not add it manually to MDX files.

### Tests

Use Jest + React Testing Library. `frontend/package.json` must include:
```json
{
  "devDependencies": {
    "@testing-library/react": "^14",
    "@testing-library/jest-dom": "^6",
    "jest": "^29",
    "jest-environment-jsdom": "^29"
  }
}
```

`frontend/src/__tests__/tracker.test.js`:
```js
import { isOptedOut, optOut, optIn, getOrCreateSessionId } from "../tracker";

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

test("not opted out by default", () => {
  expect(isOptedOut()).toBe(false);
});

test("optOut sets key", () => {
  optOut();
  expect(isOptedOut()).toBe(true);
});

test("optIn clears key", () => {
  optOut();
  optIn();
  expect(isOptedOut()).toBe(false);
});

test("getOrCreateSessionId returns stable ID within session", () => {
  const id1 = getOrCreateSessionId();
  const id2 = getOrCreateSessionId();
  expect(id1).toBe(id2);
  expect(id1.length).toBeGreaterThan(8);
});

test("getOrCreateSessionId creates new ID in new session", () => {
  const id1 = getOrCreateSessionId();
  sessionStorage.clear();
  const id2 = getOrCreateSessionId();
  expect(id1).not.toBe(id2);
});
```

`frontend/src/__tests__/TrackedBlock.test.jsx`:
```jsx
import React from "react";
import { render, screen } from "@testing-library/react";
import TrackedBlock from "../TrackedBlock";

test("renders children", () => {
  render(<TrackedBlock blockId="test-block" topic="scent">Hello</TrackedBlock>);
  expect(screen.getByText("Hello")).toBeInTheDocument();
});

test("sets data-block-id attribute", () => {
  const { container } = render(<TrackedBlock blockId="scent-intro" topic="scent">Content</TrackedBlock>);
  expect(container.firstChild.getAttribute("data-block-id")).toBe("scent-intro");
});

test("warns in dev if blockId missing", () => {
  const warn = jest.spyOn(console, "warn").mockImplementation(() => {});
  render(<TrackedBlock topic="scent">Content</TrackedBlock>);
  expect(warn).toHaveBeenCalled();
  warn.mockRestore();
});
```

Run frontend tests:
```bash
cd frontend && npm test
```

### Done when
- `cd frontend && npm test` passes (all 8 tests)
- `AnalyticsProvider` renders children without crashing when wrapped in `ErrorBoundary`
- `TrackedBlock` renders correct data attributes

---

## Phase 9 — Manifest tooling [DONE]

**Goal:** A schema, a validator script, and content/position hash generation used at Docusaurus build time.

### File: `analytics/manifest.schema.json`

JSON Schema for a tracked-block manifest file. Required fields per block:
- `block_id` (string, pattern: `^[a-z0-9][a-z0-9\-]{1,198}[a-z0-9]$`)
- `page_path` (string, starts with `/`)
- `topic` (string)
- `concept` (string)
- `content_type` (string, enum: `section`, `case-study`, `figure`, `video`, `audio`, `tool`, `glossary`, `download`, `interactive`)
- `label` (string)
- `display_order` (integer, >= 0)

Optional fields: `parent_block_id`, `heading_path`, `replaces_block_ids`, `replaced_by_block_ids`

### File: `scripts/generate_manifest.py`

CLI: `python scripts/generate_manifest.py <tracked-blocks.yml> [--output manifest.json]`

Behaviour:
1. Read YAML file containing a list of block definitions
2. For each block, compute:
   - `content_hash`: `sha256(canonical_text)` where `canonical_text` = whitespace-normalised, tag-stripped, Unicode-normalised text from `label` + optional `text` field
   - `position_hash`: `sha256(page_path + "|" + heading_path + "|" + str(display_order) + "|" + parent_block_id)`
   - `block_version_id`: `f"{block_id}:{content_hash[:8]}"`
3. Validate each block against `manifest.schema.json`
4. Check for duplicate `block_id` values; exit non-zero if found
5. Write output JSON

### File: `scripts/validate_manifest.py`

CLI: `python scripts/validate_manifest.py <manifest.json>`

Checks:
- Valid JSON
- All required fields present
- No duplicate `block_id` values
- All `block_id` values match the regex `^[a-z0-9][a-z0-9\-]{1,198}[a-z0-9]$`

Exit 0 on success, exit 1 on failure with clear error messages.

### File: `scripts/validate_public_summary.py`

CLI: `python scripts/validate_public_summary.py <summary.json>`

Checks (as per OVERVIEW.md §18.2):
1. Valid JSON
2. Field `contains_raw_events` is `false`
3. Fields `generated_at`, `date_range`, `suppression` are present
4. `blocks` is a list
5. `topics` is a list
6. File size > 10 bytes
7. No field named `session_id` anywhere in the document (recursive check)

Exit 0 on success, exit 1 on failure.

### Tests

```python
# tests/test_manifest_tools.py
import json, subprocess, sys, tempfile, os
from pathlib import Path

VALID_BLOCK = {
    "block_id": "scent-intro",
    "page_path": "/docs/scent",
    "topic": "scent",
    "concept": "olfactory-design",
    "content_type": "section",
    "label": "Introduction to Scent",
    "display_order": 0,
}

def run_script(script, *args):
    return subprocess.run(
        [sys.executable, f"scripts/{script}"] + list(args),
        capture_output=True, text=True
    )

def test_validate_manifest_passes_valid():
    manifest = {"blocks": [VALID_BLOCK]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(manifest, f)
        name = f.name
    result = run_script("validate_manifest.py", name)
    os.unlink(name)
    assert result.returncode == 0

def test_validate_manifest_fails_duplicate_ids():
    manifest = {"blocks": [VALID_BLOCK, VALID_BLOCK]}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(manifest, f)
        name = f.name
    result = run_script("validate_manifest.py", name)
    os.unlink(name)
    assert result.returncode == 1

def test_validate_public_summary_passes_valid():
    summary = {
        "generated_at": "2025-01-01T00:00:00Z",
        "date_range": {"from": "2024-12-01", "to": "2024-12-31"},
        "contains_raw_events": False,
        "suppression": {"min_sessions": 10},
        "blocks": [],
        "topics": [],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(summary, f)
        name = f.name
    result = run_script("validate_public_summary.py", name)
    os.unlink(name)
    assert result.returncode == 0

def test_validate_public_summary_fails_if_contains_raw_events():
    summary = {
        "generated_at": "2025-01-01T00:00:00Z",
        "date_range": {"from": "2024-12-01", "to": "2024-12-31"},
        "contains_raw_events": True,
        "suppression": {"min_sessions": 10},
        "blocks": [], "topics": [],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(summary, f)
        name = f.name
    result = run_script("validate_public_summary.py", name)
    os.unlink(name)
    assert result.returncode == 1

def test_validate_public_summary_fails_if_session_id_present():
    summary = {
        "generated_at": "2025-01-01T00:00:00Z",
        "date_range": {"from": "2024-12-01", "to": "2024-12-31"},
        "contains_raw_events": False,
        "suppression": {"min_sessions": 10},
        "blocks": [{"session_id": "leaked"}],
        "topics": [],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(summary, f)
        name = f.name
    result = run_script("validate_public_summary.py", name)
    os.unlink(name)
    assert result.returncode == 1
```

### Done when
- `pytest tests/test_manifest_tools.py` passes (all 5 tests)

---

## Phase 9a — `docx_to_mdx.py` TrackedBlock injection

**Goal:** Modify `docx_to_mdx.py` (in the MultisensoryHub repo) to read `analytics/tracked-blocks.yml` and inject `<TrackedBlock>` wrappers into generated MDX during pipeline execution. This replaces any manual MDX editing — the pipeline is the only source of TrackedBlock markup.

This phase is implemented in the **MultisensoryHub** repo, not this submodule. Read `AI_CONTEXT.md` in MultisensoryHub before starting — it specifies that all pipeline changes go into `docx_to_mdx.py`.

### `analytics/tracked-blocks.yml` schema

Create this file in MultisensoryHub. Example:

```yaml
blocks:
  - block_id: scent-intro
    heading: "Scent and Olfactory Design"
    topic: scent
    concept: olfactory-design
    content_type: section
    label: "Introduction to Scent"
```

`heading` must match the heading text exactly as it appears in the generated markdown (post-Pandoc, post-normalisation). Use the pipeline's existing `slugify` logic to verify the match.

### Changes to `docx_to_mdx.py`

Add a function `inject_tracked_blocks(mdx_files: list[Path], config_path: Path) -> None` called as the final step after all MDX files have been written.

The function must:

1. If `config_path` does not exist, log a debug message and return immediately — never error.
2. Load and parse `tracked-blocks.yml`. Error and exit non-zero if YAML is malformed.
3. Validate: no duplicate `block_id` values. Error and exit non-zero if found.
4. For each block entry, scan all generated MDX files for the heading text (normalised, case-insensitive match against the heading line without `#` prefix).
5. On match: wrap the content from that heading to the next heading of equal or lesser depth in `<TrackedBlock ...>...</TrackedBlock>`.
6. Add the import line `import TrackedBlock from '@site/src/components/TrackedBlock';` to the MDX file's import block if not already present.
7. Warn (do not error) if a block's `heading` is not found in any MDX file — print which `block_id` could not be matched.
8. Write the modified MDX back in place.

### Tests

Add to `tests/` in MultisensoryHub (not the submodule — these test the pipeline script):

```python
# tests/test_tracked_block_injection.py
import textwrap
from pathlib import Path
import pytest
import tempfile, yaml

# Import the function under test — adjust import to match actual module structure
from docx_to_mdx import inject_tracked_blocks

SAMPLE_MDX = textwrap.dedent("""
    import Something from '@site/src/components/Something';

    ## Scent and Olfactory Design

    This is the scent section content.

    ## Next Section

    Other content.
""").strip()

SAMPLE_CONFIG = {
    "blocks": [{
        "block_id": "scent-intro",
        "heading": "Scent and Olfactory Design",
        "topic": "scent",
        "concept": "olfactory-design",
        "content_type": "section",
        "label": "Introduction to Scent",
    }]
}

@pytest.fixture
def tmp_mdx(tmp_path):
    f = tmp_path / "scent.mdx"
    f.write_text(SAMPLE_MDX)
    return f

@pytest.fixture
def tmp_config(tmp_path):
    c = tmp_path / "tracked-blocks.yml"
    c.write_text(yaml.dump(SAMPLE_CONFIG))
    return c

def test_inject_adds_tracked_block_wrapper(tmp_mdx, tmp_config):
    inject_tracked_blocks([tmp_mdx], tmp_config)
    content = tmp_mdx.read_text()
    assert 'blockId="scent-intro"' in content
    assert "<TrackedBlock" in content
    assert "</TrackedBlock>" in content

def test_inject_adds_import(tmp_mdx, tmp_config):
    inject_tracked_blocks([tmp_mdx], tmp_config)
    content = tmp_mdx.read_text()
    assert "import TrackedBlock from '@site/src/components/TrackedBlock'" in content

def test_inject_does_not_duplicate_import(tmp_mdx, tmp_config):
    inject_tracked_blocks([tmp_mdx], tmp_config)
    inject_tracked_blocks([tmp_mdx], tmp_config)
    content = tmp_mdx.read_text()
    assert content.count("import TrackedBlock") == 1

def test_inject_missing_config_is_noop(tmp_mdx, tmp_path):
    original = tmp_mdx.read_text()
    inject_tracked_blocks([tmp_mdx], tmp_path / "nonexistent.yml")
    assert tmp_mdx.read_text() == original

def test_inject_warns_on_unmatched_heading(tmp_mdx, tmp_path, capsys):
    config = tmp_path / "tracked-blocks.yml"
    config.write_text(yaml.dump({"blocks": [{
        "block_id": "missing-block",
        "heading": "This Heading Does Not Exist",
        "topic": "scent", "concept": "x", "content_type": "section", "label": "x",
    }]}))
    inject_tracked_blocks([tmp_mdx], config)
    captured = capsys.readouterr()
    assert "missing-block" in captured.out or "missing-block" in captured.err

def test_inject_errors_on_duplicate_block_ids(tmp_mdx, tmp_path):
    config = tmp_path / "tracked-blocks.yml"
    config.write_text(yaml.dump({"blocks": [
        {"block_id": "dup", "heading": "A", "topic": "x", "concept": "x", "content_type": "section", "label": "x"},
        {"block_id": "dup", "heading": "B", "topic": "x", "concept": "x", "content_type": "section", "label": "x"},
    ]}))
    with pytest.raises(SystemExit):
        inject_tracked_blocks([tmp_mdx], config)
```

### Done when
- All 6 tests in `test_tracked_block_injection.py` pass
- Running `python docx_to_mdx.py` with a populated `analytics/tracked-blocks.yml` produces MDX files containing `<TrackedBlock>` wrappers at the correct headings
- Running `python docx_to_mdx.py` with no `analytics/tracked-blocks.yml` completes normally with no error
- Generated MDX compiles in Docusaurus (`npm run build` succeeds)

---

## Phase 10 — GitHub Actions workflow

**Goal:** Add the nightly analytics summary workflow to the MultisensoryHub repository.

Create `.github/workflows/update-analytics.yml` in the **MultisensoryHub** repo (alongside the existing `deploy.yml`). Do not modify `deploy.yml`.

Content: implement exactly the workflow described in OVERVIEW.md §6.3, with:
- `cron: "17 2 * * *"`
- `workflow_dispatch`
- `actions/checkout@v4`
- `curl` fetch with `Authorization: Bearer ${{ secrets.ANALYTICS_SUMMARY_TOKEN }}`
- URL from `vars.ANALYTICS_SUMMARY_URL`
- Output to `docusaurus-site/static/analytics/public-summary.latest.json`
- Smoke test: `python multisensoryHubHeatMap/scripts/validate_public_summary.py docusaurus-site/static/analytics/public-summary.latest.json`
- `git config --local`
- `git add docusaurus-site/static/analytics/public-summary.latest.json`
- `git diff --cached --quiet || git commit`
- `git push`
- Branch-protection comment (as per OVERVIEW.md §6.3)

No tests for this phase — verify by reading the YAML and confirming it matches OVERVIEW.md §6.3 exactly.

### Done when
- YAML is valid: `python -c "import yaml; yaml.safe_load(open('.github/workflows/update-analytics.yml'))"`
- All fields from OVERVIEW.md §6.3 are present
- Workflow does not modify `deploy.yml` or any existing workflow file

---

## Phase 11 — v2 dwell-time tracking (React)

**Goal:** Add `IntersectionObserver`-based concept exposure tracking, idle detection, and heartbeat to `AnalyticsProvider`.

Only start this phase after all Phase 8 tests pass and v1 is deployed and collecting real data.

### Changes to `AnalyticsProvider.jsx`

Add:
1. A single central `IntersectionObserver` observing all registered blocks
2. `registerBlock(blockId, ref, meta)` / `unregisterBlock(blockId)` exposed via context
3. On `IntersectionObserver` callback: mark block as entering/exiting viewport; store `entry_time` when ratio ≥ 0.5
4. Heartbeat (every 15s): for each currently visible block where entry time > 3s ago and session is not idle, emit `concept_visible_heartbeat` with `seconds_visible` and `intersection_ratio`
5. On block exit: emit `concept_exit_view`
6. Idle detection via `useUserActivity` hook: pause heartbeat after 60s inactivity
7. On route change: disconnect all observers, clear visible-block state, re-register after new page mounts
8. Flag exposures > 600 seconds (10 min) with `metadata.flagged_long_exposure: true`

### Changes to `TrackedBlock.jsx`

- Attach `ref` to wrapper div
- Call `registerBlock` on mount, `unregisterBlock` on unmount

### File: `frontend/src/hooks/useUserActivity.js`

- Listen for `scroll`, `click`, `keydown`, `pointermove`, `touchstart` on `document`
- Maintain `isIdle` (boolean) and `lastActivityAt` (timestamp)
- Idle after 60 000 ms without any event
- Expose `{ isIdle, lastActivityAt }`
- Do not record coordinates or key values

### File: `frontend/src/hooks/useConceptTracker.js`

- Wrapper that calls `registerBlock` from context; returns nothing

### Tests (add to `frontend/src/__tests__/`)

`useUserActivity.test.js`:
```js
import { renderHook, act } from "@testing-library/react";
import useUserActivity from "../hooks/useUserActivity";

jest.useFakeTimers();

test("not idle on mount", () => {
  const { result } = renderHook(() => useUserActivity());
  expect(result.current.isIdle).toBe(false);
});

test("becomes idle after 60s", () => {
  const { result } = renderHook(() => useUserActivity());
  act(() => { jest.advanceTimersByTime(61000); });
  expect(result.current.isIdle).toBe(true);
});

test("resets idle on activity", () => {
  const { result } = renderHook(() => useUserActivity());
  act(() => { jest.advanceTimersByTime(61000); });
  expect(result.current.isIdle).toBe(true);
  act(() => { document.dispatchEvent(new Event("scroll")); });
  expect(result.current.isIdle).toBe(false);
});
```

### Done when
- All Phase 8 tests still pass
- `useUserActivity` tests pass
- Manual test: open Docusaurus dev server, watch console — `concept_visible_heartbeat` events appear for visible `TrackedBlock` elements; events stop after 60s inactivity

---

## Phase 12 — Production handoff checklist

Before deploying to `costartools.uk`, verify all of the following:

- [ ] `pip install concept-analytics` installs cleanly (build and publish to private PyPI or install via git)
- [ ] `CONCEPT_ANALYTICS["ALLOWED_ORIGINS"]` set to production Docusaurus origin
- [ ] `CONCEPT_ANALYTICS["SUMMARY_TOKEN"]` is a strong random token stored in environment variable, not in code
- [ ] `CORS_ALLOWED_ORIGINS` set in host Django settings (do not use `CORS_ALLOW_ALL_ORIGINS`)
- [ ] Nginx rate limiting configured per IP on `/concept-analytics/ingest/`
- [ ] Analytics notice is live in Docusaurus site footer before tracker goes live
- [ ] Opt-out link in footer sets `localStorage` key correctly (manual test)
- [ ] `python manage.py refresh_concept_analytics_summaries --days 1` added to cron
- [ ] Private dashboard login tested with a real staff user
- [ ] Public summary endpoint returns `contains_raw_events: false`
- [ ] GitHub Actions workflow runs and commits `docusaurus-site/static/analytics/public-summary.latest.json` without error
- [ ] Smoke test `validate_public_summary.py` passes on committed file
- [ ] `docx_to_mdx.py` injects `<TrackedBlock>` wrappers correctly after a full pipeline run
- [ ] `npm run build` succeeds in `docusaurus-site/` with TrackedBlock-injected MDX
- [ ] No IP addresses stored in any analytics table (run `test_no_ip_stored` test against production DB schema)
- [ ] LIA confirmed with RHUL data governance
- [ ] All Phase 0–11 tests pass against production database schema (run with `pytest --reuse-db`)

---

## Summary of test commands

```bash
# Django app tests (run from repo root)
pytest tests/

# Individual phases
pytest tests/test_models.py
pytest tests/test_validators.py
pytest tests/test_bot_detection.py
pytest tests/test_ingest.py
pytest tests/test_public_summary.py
pytest tests/test_management_commands.py
pytest tests/test_dashboard.py
pytest tests/test_manifest_tools.py

# Frontend tests
cd frontend && npm test

# Manifest validation
python scripts/validate_manifest.py analytics/tracked-blocks.json
python scripts/validate_public_summary.py static/analytics/public-summary.latest.json
```
