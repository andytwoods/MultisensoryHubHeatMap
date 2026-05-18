import json
import pytest
from unittest.mock import patch, MagicMock
from django.core.cache import cache

from concept_analytics.models import BlockManifestEntry, ManifestSyncState
from concept_analytics.manifest_sync import (
    get_known_version,
    _save_version,
    _do_sync,
    trigger_manifest_sync,
    _CACHE_KEY,
)


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_get_known_version_no_record_returns_empty():
    assert get_known_version() == ""


@pytest.mark.django_db
def test_get_known_version_reads_db():
    ManifestSyncState.objects.create(pk=1, version="abc123def456")
    assert get_known_version() == "abc123def456"


@pytest.mark.django_db
def test_get_known_version_cache_hit_skips_db():
    cache.set(_CACHE_KEY, "cached-version", timeout=300)
    # No DB record — result must come from cache, not DB
    assert get_known_version() == "cached-version"


@pytest.mark.django_db
def test_get_known_version_warms_cache_from_db():
    ManifestSyncState.objects.create(pk=1, version="db-version-xxx")
    get_known_version()
    assert cache.get(_CACHE_KEY) == "db-version-xxx"


@pytest.mark.django_db
def test_save_version_creates_db_record():
    _save_version("newversion1234")
    assert ManifestSyncState.objects.get(pk=1).version == "newversion1234"


@pytest.mark.django_db
def test_save_version_updates_existing_record():
    ManifestSyncState.objects.create(pk=1, version="old")
    _save_version("new")
    assert ManifestSyncState.objects.get(pk=1).version == "new"
    assert ManifestSyncState.objects.count() == 1


@pytest.mark.django_db
def test_save_version_warms_cache():
    _save_version("v999")
    assert cache.get(_CACHE_KEY) == "v999"


@pytest.mark.django_db
def test_do_sync_imports_entries_and_saves_version():
    manifest = {
        "version": "sync-ver-0001",
        "blocks": [
            {"block_id": "b1", "topic": "sound", "page_path": "/docs/sound",
             "concept": "", "content_type": "section", "label": "", "display_order": 0,
             "content_hash": "aabbccdd", "position_hash": "11223344"},
        ],
    }
    fake_resp = MagicMock()
    fake_resp.read.return_value = json.dumps(manifest).encode()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)

    with patch("concept_analytics.manifest_sync.urllib.request.urlopen", return_value=fake_resp):
        _do_sync("https://example.com", "sync-ver-0001")

    assert BlockManifestEntry.objects.filter(block_id="b1").exists()
    assert ManifestSyncState.objects.get(pk=1).version == "sync-ver-0001"


@pytest.mark.django_db
def test_do_sync_handles_legacy_list_format():
    entries = [
        {"block_id": "b2", "topic": "light", "page_path": "/docs/light",
         "concept": "", "content_type": "section", "label": "", "display_order": 0,
         "content_hash": "aabbccdd", "position_hash": "11223344"},
    ]
    fake_resp = MagicMock()
    fake_resp.read.return_value = json.dumps(entries).encode()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)

    with patch("concept_analytics.manifest_sync.urllib.request.urlopen", return_value=fake_resp):
        _do_sync("https://example.com", "ver-legacy")

    assert BlockManifestEntry.objects.filter(block_id="b2").exists()


@pytest.mark.django_db
def test_do_sync_network_failure_does_not_raise():
    with patch("concept_analytics.manifest_sync.urllib.request.urlopen", side_effect=OSError("timeout")):
        _do_sync("https://example.com", "ver-fail")  # must not raise
    assert not ManifestSyncState.objects.filter(pk=1).exists()


@pytest.mark.django_db
def test_trigger_manifest_sync_fires_thread():
    with patch("concept_analytics.manifest_sync._do_sync") as mock_sync:
        with patch("concept_analytics.manifest_sync.threading.Thread") as mock_thread:
            instance = MagicMock()
            mock_thread.return_value = instance
            trigger_manifest_sync("https://example.com", "v123")
            mock_thread.assert_called_once()
            instance.start.assert_called_once()


@pytest.mark.django_db
def test_trigger_manifest_sync_noop_when_in_progress():
    import concept_analytics.manifest_sync as ms
    ms._sync_in_progress = True
    try:
        with patch("concept_analytics.manifest_sync.threading.Thread") as mock_thread:
            trigger_manifest_sync("https://example.com", "v123")
            mock_thread.assert_not_called()
    finally:
        ms._sync_in_progress = False
