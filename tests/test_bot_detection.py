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
