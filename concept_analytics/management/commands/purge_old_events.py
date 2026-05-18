from datetime import date, timedelta
from django.core.management.base import BaseCommand
from ...models import AnalyticsEvent


class Command(BaseCommand):
    help = "Delete raw AnalyticsEvent records older than N days (default: 180)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=180,
            help="Retain events newer than this many days (default: 180)",
        )

    def handle(self, *args, **options):
        cutoff = date.today() - timedelta(days=options["days"])
        deleted, _ = AnalyticsEvent.objects.filter(received_at__date__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted} event(s) received before {cutoff}")
        )
