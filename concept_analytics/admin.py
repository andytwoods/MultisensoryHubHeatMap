from django.contrib import admin
from .models import (
    AnalyticsSession, AnalyticsEvent, BlockManifestEntry,
    DailyBlockSummary, DailyTopicSummary, DailyTransitionSummary
)

@admin.register(AnalyticsSession)
class AnalyticsSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "human_likelihood", "is_suspicious", "created_at", "last_seen_at")
    list_filter = ("human_likelihood", "is_suspicious", "device_class")
    search_fields = ("session_id",)
    readonly_fields = [f.name for f in AnalyticsSession._meta.get_fields()]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("session", "event_type", "block_id", "topic", "received_at")
    list_filter = ("event_type", "topic")
    search_fields = ("block_id", "page_path")
    readonly_fields = [f.name for f in AnalyticsEvent._meta.get_fields() if not f.is_relation or f.one_to_many]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(BlockManifestEntry)
class BlockManifestEntryAdmin(admin.ModelAdmin):
    list_display = ("block_id", "topic", "concept", "is_active", "updated_at")
    list_filter = ("topic", "is_active")
    search_fields = ("block_id", "page_path")

@admin.register(DailyBlockSummary)
class DailyBlockSummaryAdmin(admin.ModelAdmin):
    list_display = ("date", "block_id", "unique_sessions", "total_visible_seconds")
    readonly_fields = [f.name for f in DailyBlockSummary._meta.get_fields()]

@admin.register(DailyTopicSummary)
class DailyTopicSummaryAdmin(admin.ModelAdmin):
    list_display = ("date", "topic", "unique_sessions", "total_visible_seconds")
    readonly_fields = [f.name for f in DailyTopicSummary._meta.get_fields()]

@admin.register(DailyTransitionSummary)
class DailyTransitionSummaryAdmin(admin.ModelAdmin):
    list_display = ("date", "from_page_path", "to_page_path", "transition_count")
    readonly_fields = [f.name for f in DailyTransitionSummary._meta.get_fields()]
