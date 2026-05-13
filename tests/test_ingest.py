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
