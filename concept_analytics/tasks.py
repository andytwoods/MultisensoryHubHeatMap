"""
Huey periodic tasks for concept_analytics.

Scheduled nightly via django_huey / RedisHuey (configured in the host project).
These tasks call the same logic as the management commands so they can also be
run manually: python manage.py refresh_concept_analytics_summaries --days 2
"""
import logging
from datetime import date, timedelta

from huey import crontab
from django_huey import db_periodic_task

logger = logging.getLogger(__name__)


@db_periodic_task(crontab(hour="3", minute="0"))
def nightly_refresh_summaries() -> None:
    """Rebuild DailyBlockSummary, DailyTopicSummary, and DailyTransitionSummary
    for the last 2 days. The one-day overlap guards against events that arrive
    just after midnight being missed by a run on the previous day.
    """
    from django.core.management import call_command

    today = date.today()
    target_dates = [today - timedelta(days=i) for i in range(1, 3)]
    for d in target_dates:
        logger.info("concept_analytics: refreshing summaries for %s", d)
        try:
            call_command("refresh_concept_analytics_summaries", date=str(d))
        except Exception:
            logger.exception(
                "concept_analytics: failed to refresh summaries for %s", d
            )


@db_periodic_task(crontab(hour="3", minute="15"))
def nightly_purge_old_events() -> None:
    """Delete raw events beyond the configured retention window."""
    logger.info("concept_analytics: purging old events")
    try:
        from django.core.management import call_command
        call_command("purge_old_events")
    except Exception:
        logger.exception("concept_analytics: failed to purge old events")
