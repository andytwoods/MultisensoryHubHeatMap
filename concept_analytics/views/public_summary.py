import json
from datetime import date, timedelta
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from ..models import DailyBlockSummary, DailyTopicSummary
from ..conf import get_setting

class PublicSummaryView(View):
    def get(self, request, *args, **kwargs):
        # 2. Check Authorization
        auth_header = request.headers.get("Authorization")
        expected_token = get_setting("SUMMARY_TOKEN")
        if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != expected_token:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        # 3. Query last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        block_summaries = DailyBlockSummary.objects.filter(date__range=(start_date, end_date))
        topic_summaries = DailyTopicSummary.objects.filter(date__range=(start_date, end_date))

        # 4. Apply suppression and aggregate
        # We need to aggregate across the 30 days for each block_id
        aggregated_blocks = {}
        for s in block_summaries:
            bid = s.block_id
            if bid not in aggregated_blocks:
                aggregated_blocks[bid] = {
                    "block_id": bid,
                    "topic": s.topic,
                    "concept": s.concept,
                    "unique_sessions": 0,
                    "total_visible_seconds": 0.0,
                    "interaction_count": 0
                }
            aggregated_blocks[bid]["unique_sessions"] += s.unique_sessions
            aggregated_blocks[bid]["total_visible_seconds"] += s.total_visible_seconds
            aggregated_blocks[bid]["interaction_count"] += s.interaction_count

        # Apply suppression: unique_sessions < 10
        min_sessions = 10
        blocks_list = [
            b for b in aggregated_blocks.values()
            if b["unique_sessions"] >= min_sessions
        ]

        aggregated_topics = {}
        for s in topic_summaries:
            t = s.topic
            if t not in aggregated_topics:
                aggregated_topics[t] = {
                    "topic": t,
                    "unique_sessions": 0,
                    "total_visible_seconds": 0.0,
                    "interaction_count": 0
                }
            aggregated_topics[t]["unique_sessions"] += s.unique_sessions
            aggregated_topics[t]["total_visible_seconds"] += s.total_visible_seconds
            aggregated_topics[t]["interaction_count"] += s.interaction_count

        topics_list = list(aggregated_topics.values())

        # 5. Return JSON
        response_data = {
            "generated_at": timezone.now().isoformat(),
            "date_range": {
                "from": start_date.isoformat(),
                "to": end_date.isoformat()
            },
            "contains_raw_events": False,
            "suppression": {"min_sessions": min_sessions},
            "blocks": blocks_list,
            "topics": topics_list
        }

        return JsonResponse(response_data)
