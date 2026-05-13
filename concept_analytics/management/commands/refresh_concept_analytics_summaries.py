from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Q, Avg
from ...models import (
    AnalyticsSession, AnalyticsEvent, 
    DailyBlockSummary, DailyTopicSummary, DailyTransitionSummary
)

class Command(BaseCommand):
    help = "Rebuilds daily summary tables from raw AnalyticsEvent data"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Refresh a specific date (YYYY-MM-DD)")
        parser.add_argument("--days", type=int, default=1, help="Refresh the last N days")

    def handle(self, *args, **options):
        if options["date"]:
            target_dates = [date.fromisoformat(options["date"])]
        else:
            days = options["days"]
            today = date.today()
            target_dates = [today - timedelta(days=i) for i in range(1, days + 1)]

        for d in target_dates:
            self.stdout.write(f"Refreshing summaries for {d}...")
            self.refresh_daily_summaries(d)

    def refresh_daily_summaries(self, d):
        # 1. DailyBlockSummary
        events_on_day = AnalyticsEvent.objects.filter(received_at__date=d)
        
        # Aggregate by (block_id, block_version_id)
        block_groups = events_on_day.values("block_id", "block_version_id", "topic", "concept").annotate(
            unique_sessions=Count("session", distinct=True),
            event_count=Count("id"),
            total_visible_seconds=Sum("seconds_visible")
        ).filter(~Q(block_id=""))

        for group in block_groups:
            # Median visible seconds
            visible_secs = events_on_day.filter(
                block_id=group["block_id"], 
                block_version_id=group["block_version_id"],
                seconds_visible__isnull=False
            ).values_list("seconds_visible", flat=True).order_by("seconds_visible")
            
            median_val = None
            if visible_secs:
                count = len(visible_secs)
                if count % 2 == 1:
                    median_val = visible_secs[count // 2]
                else:
                    median_val = (visible_secs[count // 2 - 1] + visible_secs[count // 2]) / 2

            # Interaction count
            interaction_types = [
                "section_opened", "accordion_opened", "tab_selected", 
                "case_study_opened", "video_played", "audio_played", "interactive_started"
            ]
            interactions = events_on_day.filter(
                block_id=group["block_id"],
                block_version_id=group["block_version_id"],
                event_type__in=interaction_types
            ).count()

            # Downloads/External clicks after exposure
            # Find sessions that had exposure to this block on this day
            exposed_sessions = events_on_day.filter(
                block_id=group["block_id"],
                block_version_id=group["block_version_id"],
                event_type="concept_visible_heartbeat"
            ).values_list("session_id", flat=True).distinct()

            downloads = events_on_day.filter(
                session_id__in=exposed_sessions,
                event_type="download_clicked",
                block_id=group["block_id"] # The plan says "also had a heartbeat for this block_id"
            ).count()

            external_clicks = events_on_day.filter(
                session_id__in=exposed_sessions,
                event_type="external_link_clicked",
                block_id=group["block_id"]
            ).count()

            DailyBlockSummary.objects.update_or_create(
                date=d,
                block_id=group["block_id"],
                block_version_id=group["block_version_id"],
                defaults={
                    "topic": group["topic"],
                    "concept": group["concept"],
                    "unique_sessions": group["unique_sessions"],
                    "event_count": group["event_count"],
                    "total_visible_seconds": group["total_visible_seconds"] or 0.0,
                    "median_visible_seconds": median_val,
                    "interaction_count": interactions,
                    "downloads_after_exposure": downloads,
                    "external_clicks_after_exposure": external_clicks
                }
            )

        # 2. DailyTopicSummary
        topic_groups = events_on_day.values("topic").annotate(
            unique_sessions=Count("session", distinct=True),
            total_visible_seconds=Sum("seconds_visible")
        ).filter(~Q(topic=""))

        for group in topic_groups:
             interaction_types = [
                "section_opened", "accordion_opened", "tab_selected", 
                "case_study_opened", "video_played", "audio_played", "interactive_started"
            ]
             interactions = events_on_day.filter(
                topic=group["topic"],
                event_type__in=interaction_types
            ).count()

             DailyTopicSummary.objects.update_or_create(
                date=d,
                topic=group["topic"],
                defaults={
                    "unique_sessions": group["unique_sessions"],
                    "total_visible_seconds": group["total_visible_seconds"] or 0.0,
                    "interaction_count": interactions
                }
            )

        # 3. DailyTransitionSummary
        # This is more complex as it requires session sequencing
        sessions_on_day = events_on_day.values_list("session_id", flat=True).distinct()
        
        transitions = {} # (from_p, to_p, from_b, to_b, from_t, to_t) -> {count: N, sessions: set()}

        for sid in sessions_on_day:
            session_events = AnalyticsEvent.objects.filter(session_id=sid, received_at__date=d).order_by("event_sequence")
            
            prev_page = None
            prev_block = None
            prev_topic = None

            for e in session_events:
                # Page transitions
                if prev_page and e.page_path != prev_page:
                    key = (prev_page, e.page_path, "", "", "", "")
                    if key not in transitions:
                        transitions[key] = {"count": 0, "sessions": set()}
                    transitions[key]["count"] += 1
                    transitions[key]["sessions"].add(sid)
                
                # Block transitions
                if prev_block and e.block_id and e.block_id != prev_block:
                    key = ("", "", prev_block, e.block_id, prev_topic, e.topic)
                    if key not in transitions:
                        transitions[key] = {"count": 0, "sessions": set()}
                    transitions[key]["count"] += 1
                    transitions[key]["sessions"].add(sid)

                prev_page = e.page_path
                if e.block_id:
                    prev_block = e.block_id
                    prev_topic = e.topic

        for key, data in transitions.items():
            from_p, to_p, from_b, to_b, from_t, to_t = key
            DailyTransitionSummary.objects.update_or_create(
                date=d,
                from_page_path=from_p,
                to_page_path=to_p,
                from_block_id=from_b,
                to_block_id=to_b,
                from_topic=from_t,
                to_topic=to_t,
                defaults={
                    "transition_count": data["count"],
                    "unique_sessions": len(data["sessions"])
                }
            )
