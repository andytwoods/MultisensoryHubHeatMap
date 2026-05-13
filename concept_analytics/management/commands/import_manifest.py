import json
from django.core.management.base import BaseCommand
from ...models import BlockManifestEntry

class Command(BaseCommand):
    help = "Imports a JSON manifest into BlockManifestEntry table"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="Path to manifest.json")
        parser.add_argument("--purge", action="store_true", help="Mark existing entries as inactive if not in manifest")

    def handle(self, *args, **options):
        file_path = options["file"]
        with open(file_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        active_ids = set()
        for entry in manifest:
            bid = entry["block_id"]
            active_ids.add(bid)
            
            BlockManifestEntry.objects.update_or_create(
                block_id=bid,
                defaults={
                    "topic": entry.get("topic", ""),
                    "concept": entry.get("concept", ""),
                    "content_type": entry.get("content_type", ""),
                    "label": entry.get("label", ""),
                    "page_path": entry.get("page_path", ""),
                    "display_order": entry.get("display_order", 0),
                    "content_hash": entry.get("content_hash", ""),
                    "position_hash": entry.get("position_hash", ""),
                    "is_active": True
                }
            )
            self.stdout.write(f"Imported {bid}")

        if options["purge"]:
            BlockManifestEntry.objects.exclude(block_id__in=active_ids).update(is_active=False)
            self.stdout.write("Purged inactive entries")
