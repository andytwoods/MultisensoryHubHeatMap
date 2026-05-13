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
