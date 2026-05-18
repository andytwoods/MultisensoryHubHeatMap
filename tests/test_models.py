import pytest
from django.utils import timezone
from concept_analytics.models import AnalyticsSession, AnalyticsEvent, BlockManifestEntry, ManifestSyncState

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


@pytest.mark.django_db
def test_manifest_sync_state_create():
    state = ManifestSyncState.objects.create(pk=1, version="abc123def456")
    assert state.version == "abc123def456"
    assert state.synced_at is not None


@pytest.mark.django_db
def test_manifest_sync_state_singleton_update():
    ManifestSyncState.objects.create(pk=1, version="aaaaaaaaaaaa")
    ManifestSyncState.objects.filter(pk=1).update(version="bbbbbbbbbbbb")
    assert ManifestSyncState.objects.get(pk=1).version == "bbbbbbbbbbbb"
    assert ManifestSyncState.objects.count() == 1
