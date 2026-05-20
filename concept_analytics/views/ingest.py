import json
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError

from ..models import AnalyticsSession, AnalyticsEvent
from ..validators import validate_ingest_payload
from ..bot_detection import score_session
from ..conf import get_setting

logger = logging.getLogger(__name__)

_RATE_LIMIT = 60  # requests per IP per minute

# Events that carry no analytical value — accepted but not persisted.
_SKIP_EVENT_TYPES = frozenset({
    "page_visible_heartbeat",
    "page_hidden",
    "session_resume",
    "page_unload",
    "concept_exit_view",  # superseded by delta-based heartbeats
})


def _get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "")


def _detect_device_class(user_agent: str) -> str:
    ua = user_agent.lower()
    if any(x in ua for x in ("ipad", "tablet", "kindle")):
        return "tablet"
    if any(x in ua for x in ("mobile", "android", "iphone", "ipod", "blackberry", "windows phone")):
        return "mobile"
    return "desktop"


@method_decorator(csrf_exempt, name="dispatch")
class IngestView(View):
    def post(self, request, *args, **kwargs):
        # 1. IP-based rate limiting (60 req/min)
        ip = _get_client_ip(request)
        rl_key = f"analytics_rl_{ip}"
        count = cache.get(rl_key, 0)
        if count >= _RATE_LIMIT:
            return JsonResponse({"error": "Too many requests"}, status=429)
        cache.set(rl_key, count + 1, timeout=60)

        # 2. Check Content-Type
        if request.content_type not in ("application/json", "text/plain"):
             return JsonResponse({"error": "Unsupported Media Type"}, status=415)

        # 3. Check payload size
        max_bytes = get_setting("MAX_PAYLOAD_BYTES")
        if len(request.body) > max_bytes:
            return JsonResponse({"error": "Payload too large"}, status=413)

        # 4. Check Origin header
        origin = request.headers.get("Origin")
        allowed_origins = get_setting("ALLOWED_ORIGINS")
        if allowed_origins and origin not in allowed_origins:
            logger.warning(f"Rejected ingest from origin: {origin}")
            return JsonResponse({"error": "Forbidden"}, status=403)

        # 5. Parse JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # 6. Validate payload
        try:
            data = validate_ingest_payload(data)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)

        # 7. Manifest version check — trigger background sync on mismatch
        manifest_version = data.get("manifest_version", "")
        if manifest_version:
            from ..manifest_sync import get_known_version, trigger_manifest_sync
            if manifest_version != get_known_version():
                site_url = get_setting("SITE_URL")
                if site_url:
                    trigger_manifest_sync(site_url, manifest_version)

        # 8. Score session
        user_agent = request.headers.get("User-Agent", "")
        events_data = data["events"]
        human_likelihood = score_session(user_agent, events_data)
        device_class = _detect_device_class(user_agent)

        # 8. get_or_create AnalyticsSession
        session_id = data["session_id"]
        report_name = data.get("report_name", "")
        session, created = AnalyticsSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                "landing_path": data["page_path"],
                "referrer_domain": data.get("referrer_domain", ""),
                "device_class": device_class,
                "human_likelihood": human_likelihood,
                "is_suspicious": human_likelihood == "bot_likely",
                "report_name": report_name,
            }
        )
        if not created:
            session.human_likelihood = human_likelihood
            session.device_class = device_class
            if human_likelihood == "bot_likely":
                session.is_suspicious = True
            if report_name and not session.report_name:
                session.report_name = report_name
            session.save()

        # 9. Create AnalyticsEvent records (skip duplicates)
        accepted_count = 0
        for event_data in events_data:
            if event_data["event_type"] in _SKIP_EVENT_TYPES:
                continue
            seq = event_data["event_sequence"]
            if AnalyticsEvent.objects.filter(session=session, event_sequence=seq).exists():
                continue

            AnalyticsEvent.objects.create(
                session=session,
                event_sequence=seq,
                page_path=data["page_path"],
                page_title=event_data.get("page_title", ""),
                event_type=event_data["event_type"],
                block_id=event_data.get("block_id", ""),
                block_version_id=event_data.get("block_version_id", ""),
                content_hash=event_data.get("content_hash", ""),
                topic=event_data.get("topic", ""),
                concept=event_data.get("concept", ""),
                content_type=event_data.get("content_type", ""),
                previous_page_path=event_data.get("previous_page_path", ""),
                previous_block_id=event_data.get("previous_block_id", ""),
                seconds_since_previous_event=event_data.get("seconds_since_previous_event"),
                seconds_visible=event_data.get("seconds_visible"),
                intersection_ratio=event_data.get("intersection_ratio"),
                scroll_depth=event_data.get("scroll_depth"),
                target_path=event_data.get("target_path", ""),
                target_domain=event_data.get("target_domain", ""),
                metadata=event_data.get("metadata", {}),
            )
            accepted_count += 1

        # 10. Return HTTP 202
        return JsonResponse({"status": "ok", "accepted": accepted_count}, status=202)
