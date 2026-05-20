from django.conf import settings

DEFAULTS = {
    "ALLOWED_ORIGINS": [],
    "MAX_EVENTS_PER_BATCH": 50,
    "MAX_PAYLOAD_BYTES": 65536,
    "IDLE_THRESHOLD_SECONDS": 60,
    "SUMMARY_TOKEN": "",
    "SITE_URL": "",  # local: "http://localhost:3000", production: "https://storyfutures.github.io/multisensoryReport"
}

def get_setting(key):
    user = getattr(settings, "CONCEPT_ANALYTICS", {})
    return user.get(key, DEFAULTS[key])
