import re
from django.core.exceptions import ValidationError

ALLOWED_EVENT_TYPES = {
    "session_start", "page_view", "page_visible_heartbeat", "page_hidden",
    "page_unload", "session_resume", "concept_enter_view", "concept_visible_heartbeat",
    "concept_exit_view", "section_opened", "accordion_opened", "tab_selected",
    "case_study_opened", "video_played", "audio_played", "interactive_started",
    "download_clicked", "external_link_clicked", "internal_link_clicked", "search_submitted"
}

def validate_ingest_payload(data):
    if not isinstance(data, dict):
        raise ValidationError("Payload must be a dictionary")

    # 1. session_id
    session_id = data.get("session_id")
    if not session_id or not isinstance(session_id, str):
        raise ValidationError("session_id must be a string")
    if not (8 <= len(session_id) <= 64):
        raise ValidationError("session_id must be 8-64 characters")
    if not re.match(r"^[a-zA-Z0-9\-_]+$", session_id):
        raise ValidationError("session_id contains invalid characters")

    # 2. page_path
    page_path = data.get("page_path")
    if not page_path or not isinstance(page_path, str):
        raise ValidationError("page_path must be a string")
    if not page_path.startswith("/"):
        raise ValidationError("page_path must start with /")
    if len(page_path) > 500:
        raise ValidationError("page_path is too long")

    # 3 & 4. events
    events = data.get("events")
    if not isinstance(events, list) or not events:
        raise ValidationError("events must be a non-empty list")
    
    from .conf import get_setting
    max_events = get_setting("MAX_EVENTS_PER_BATCH")
    if len(events) > max_events:
        raise ValidationError(f"Too many events in batch (max {max_events})")

    # Validate each event
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValidationError(f"Event at index {i} must be a dictionary")

        # 5. event_type and event_sequence
        event_type = event.get("event_type")
        if not event_type or not isinstance(event_type, str):
            raise ValidationError(f"Event at index {i} missing event_type")
        if len(event_type) > 50:
            raise ValidationError(f"Event type at index {i} too long")
        
        if event_type not in ALLOWED_EVENT_TYPES:
            raise ValidationError(f"Unknown event type at index {i}: {event_type}")

        event_sequence = event.get("event_sequence")
        if event_sequence is None or not isinstance(event_sequence, int) or event_sequence < 0:
            raise ValidationError(f"Event at index {i} missing or invalid event_sequence")

        # 7. intersection_ratio
        ratio = event.get("intersection_ratio")
        if ratio is not None:
            try:
                ratio = float(ratio)
                if not (0.0 <= ratio <= 1.0):
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid intersection_ratio at index {i}")

        # 8. scroll_depth
        depth = event.get("scroll_depth")
        if depth is not None:
            try:
                depth = float(depth)
                if not (0.0 <= depth <= 1.0):
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid scroll_depth at index {i}")

        # 9. seconds_visible
        secs = event.get("seconds_visible")
        if secs is not None:
            try:
                secs = float(secs)
                if not (0 <= secs < 3600):
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid seconds_visible at index {i}")

        # 10. block_id
        block_id = event.get("block_id")
        if block_id is not None:
            if not isinstance(block_id, str) or len(block_id) > 200:
                raise ValidationError(f"Invalid block_id at index {i}")
            if not re.match(r"^[a-zA-Z0-9\-_]*$", block_id):
                raise ValidationError(f"block_id at index {i} contains invalid characters")

        # 12. target_path
        target_path = event.get("target_path")
        if target_path is not None:
            if not isinstance(target_path, str) or not target_path.startswith("/") or len(target_path) > 500:
                raise ValidationError(f"Invalid target_path at index {i}")

        # 13. target_domain
        target_domain = event.get("target_domain")
        if target_domain is not None:
            if not isinstance(target_domain, str) or len(target_domain) > 253:
                raise ValidationError(f"Invalid target_domain at index {i}")
            if "/" in target_domain or "://" in target_domain:
                 raise ValidationError(f"target_domain at index {i} must not contain protocol or path")

    # 11. referrer_domain
    referrer_domain = data.get("referrer_domain")
    if referrer_domain is not None:
        if not isinstance(referrer_domain, str) or len(referrer_domain) > 253:
            raise ValidationError("Invalid referrer_domain")
        if "/" in referrer_domain or "://" in referrer_domain:
            raise ValidationError("referrer_domain must not contain protocol or path")

    return data
