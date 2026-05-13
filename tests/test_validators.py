import pytest
from django.core.exceptions import ValidationError
from concept_analytics.validators import validate_ingest_payload

MINIMAL_VALID = {
    "session_id": "abc-123-def",
    "page_path": "/docs/scent",
    "events": [{"event_type": "page_view", "event_sequence": 1}],
}

def test_valid_payload():
    result = validate_ingest_payload(MINIMAL_VALID)
    assert result["session_id"] == "abc-123-def"

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
