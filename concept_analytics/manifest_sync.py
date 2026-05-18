import json
import logging
import threading
import urllib.request

from .models import BlockManifestEntry, ManifestSyncState

logger = logging.getLogger(__name__)

_CACHE_KEY = "concept_analytics_manifest_version"
_CACHE_TTL = 300  # seconds — fast read path in front of the DB

_lock = threading.Lock()
_sync_in_progress = False


def get_known_version() -> str:
    """Return the manifest version last successfully imported, checking cache then DB."""
    from django.core.cache import cache
    cached = cache.get(_CACHE_KEY)
    if cached is not None:
        return cached
    try:
        version = ManifestSyncState.objects.only("version").get(pk=1).version
    except ManifestSyncState.DoesNotExist:
        version = ""
    cache.set(_CACHE_KEY, version, timeout=_CACHE_TTL)
    return version


def _save_version(version: str) -> None:
    from django.core.cache import cache
    ManifestSyncState.objects.update_or_create(pk=1, defaults={"version": version})
    cache.set(_CACHE_KEY, version, timeout=_CACHE_TTL)


def _import_entries(entries: list) -> int:
    count = 0
    for entry in entries:
        bid = entry.get("block_id")
        if not bid:
            continue
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
                "is_active": True,
            },
        )
        count += 1
    return count


def _do_sync(site_url: str, version: str) -> None:
    global _sync_in_progress
    url = site_url.rstrip("/") + "/manifest.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = json.loads(resp.read())
        entries = raw.get("blocks", raw) if isinstance(raw, dict) else raw
        count = _import_entries(entries)
        _save_version(version)
        logger.info("[manifest_sync] Imported %d blocks, version=%s from %s", count, version, url)
    except Exception:
        logger.exception("[manifest_sync] Failed to fetch/import manifest from %s", url)
    finally:
        with _lock:
            _sync_in_progress = False


def trigger_manifest_sync(site_url: str, version: str) -> None:
    """Start a background thread to fetch and import the manifest. No-ops if one is already running."""
    global _sync_in_progress
    with _lock:
        if _sync_in_progress:
            return
        _sync_in_progress = True
    threading.Thread(target=_do_sync, args=(site_url, version), daemon=True).start()
