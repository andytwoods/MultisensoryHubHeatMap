import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import AnalyticsSession, AnalyticsEvent
from ..validators import validate_ingest_payload
from ..bot_detection import score_session
from ..conf import get_setting

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name="dispatch")
class IngestView(View):
    def post(self, request, *args, **kwargs):
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

        # 7. Score session
        user_agent = request.headers.get("User-Agent", "")
        events_data = data["events"]
        human_likelihood = score_session(user_agent, events_data)

        # 8. get_or_create AnalyticsSession
        session_id = data["session_id"]
        session, created = AnalyticsSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                "landing_path": data["page_path"],
                "referrer_domain": data.get("referrer_domain", ""),
                "human_likelihood": human_likelihood,
                "is_suspicious": human_likelihood == "bot_likely"
            }
        )
        if not created:
            session.human_likelihood = human_likelihood
            if human_likelihood == "bot_likely":
                session.is_suspicious = True
            session.save()

        # 9. Create AnalyticsEvent
        accepted_count = 0
        for event_data in events_data:
            seq = event_data["event_sequence"]
            # Skip duplicate (session, event_sequence) pairs silently
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
