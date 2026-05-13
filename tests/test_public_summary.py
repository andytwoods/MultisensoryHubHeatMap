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
    assert resp.status_code == 200
    text = resp.content.decode()
    assert "session_id" not in text

@pytest.mark.django_db
def test_summary_post_not_allowed(client):
    resp = client.post("/concept-analytics/summary/latest/", HTTP_AUTHORIZATION=AUTH)
    assert resp.status_code == 405
