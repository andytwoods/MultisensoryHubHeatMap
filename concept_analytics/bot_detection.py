import re

def score_session(user_agent, events):
    if not user_agent:
        return "bot_likely"

    # 2. bot patterns
    bot_patterns = [
        "bot", "crawler", "spider", "scraper", "curl", "wget", 
        "python-requests", "java/", "go-http", "headless"
    ]
    ua_lower = user_agent.lower()
    for pattern in bot_patterns:
        if pattern in ua_lower:
            return "bot_likely"

    # 3. too many events
    if len(events) > 30:
        return "bot_likely"

    if not events:
        return "unknown"

    # 4. identical sequences
    sequences = [e.get("event_sequence") for e in events]
    if len(sequences) > 1 and len(set(sequences)) == 1:
        return "bot_likely"

    # 5. mechanical repetition
    types = [e.get("event_type") for e in events]
    if len(types) > 5 and len(set(types)) == 1:
        return "bot_likely"

    # Human likely conditions
    has_interaction = any(e.get("event_type") not in ("page_view", "session_start") for e in events)
    distinct_sequences = len(set(sequences)) >= 2
    
    if has_interaction and distinct_sequences:
        return "human_likely"

    return "unknown"
