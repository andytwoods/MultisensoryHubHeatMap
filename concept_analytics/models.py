from django.db import models

class AnalyticsSession(models.Model):
    session_id = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    landing_path = models.CharField(max_length=500, blank=True)
    referrer_domain = models.CharField(max_length=253, blank=True)
    device_class = models.CharField(max_length=20, blank=True)
    browser_family = models.CharField(max_length=50, blank=True)
    is_suspicious = models.BooleanField(default=False)
    human_likelihood = models.CharField(max_length=12, default="unknown")

    def __str__(self):
        return self.session_id

class AnalyticsEvent(models.Model):
    session = models.ForeignKey(AnalyticsSession, on_delete=models.PROTECT, related_name="events")
    received_at = models.DateTimeField(auto_now_add=True)
    timestamp_client = models.DateTimeField(null=True, blank=True)
    event_sequence = models.PositiveIntegerField()
    page_path = models.CharField(max_length=500)
    page_title = models.CharField(max_length=500, blank=True)
    event_type = models.CharField(max_length=50, db_index=True)
    block_id = models.CharField(max_length=200, blank=True, db_index=True)
    block_version_id = models.CharField(max_length=300, blank=True, db_index=True)
    content_hash = models.CharField(max_length=80, blank=True, db_index=True)
    topic = models.CharField(max_length=100, blank=True, db_index=True)
    concept = models.CharField(max_length=100, blank=True, db_index=True)
    content_type = models.CharField(max_length=50, blank=True)
    previous_page_path = models.CharField(max_length=500, blank=True)
    previous_block_id = models.CharField(max_length=200, blank=True)
    seconds_since_previous_event = models.FloatField(null=True, blank=True)
    seconds_visible = models.FloatField(null=True, blank=True)
    intersection_ratio = models.FloatField(null=True, blank=True)
    scroll_depth = models.FloatField(null=True, blank=True)
    target_path = models.CharField(max_length=500, blank=True)
    target_domain = models.CharField(max_length=253, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["session", "event_sequence"]),
            models.Index(fields=["received_at"]),
        ]
        permissions = [("view_dashboard", "Can view concept analytics dashboard")]

class BlockManifestEntry(models.Model):
    block_id = models.CharField(max_length=200, unique=True, db_index=True)
    block_version_id = models.CharField(max_length=300, blank=True)
    content_hash = models.CharField(max_length=80, blank=True)
    position_hash = models.CharField(max_length=80, blank=True)
    page_path = models.CharField(max_length=500)
    page_title = models.CharField(max_length=500, blank=True)
    heading_path = models.CharField(max_length=1000, blank=True) # pipe-separated heading hierarchy
    display_order = models.PositiveIntegerField(default=0)
    topic = models.CharField(max_length=100, blank=True)
    concept = models.CharField(max_length=100, blank=True)
    content_type = models.CharField(max_length=50, blank=True)
    label = models.CharField(max_length=500, blank=True)
    parent_block_id = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.block_id

class DailyBlockSummary(models.Model):
    date = models.DateField(db_index=True)
    block_id = models.CharField(max_length=200, db_index=True)
    block_version_id = models.CharField(max_length=300, blank=True)
    topic = models.CharField(max_length=100, blank=True)
    concept = models.CharField(max_length=100, blank=True)
    unique_sessions = models.PositiveIntegerField(default=0)
    event_count = models.PositiveIntegerField(default=0)
    total_visible_seconds = models.FloatField(default=0.0)
    median_visible_seconds = models.FloatField(null=True)
    interaction_count = models.PositiveIntegerField(default=0)
    downloads_after_exposure = models.PositiveIntegerField(default=0)
    external_clicks_after_exposure = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("date", "block_id", "block_version_id")]

class DailyTopicSummary(models.Model):
    date = models.DateField(db_index=True)
    topic = models.CharField(max_length=100, db_index=True)
    unique_sessions = models.PositiveIntegerField(default=0)
    total_visible_seconds = models.FloatField(default=0.0)
    interaction_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("date", "topic")]

class DailyTransitionSummary(models.Model):
    date = models.DateField(db_index=True)
    from_page_path = models.CharField(max_length=500)
    to_page_path = models.CharField(max_length=500)
    from_block_id = models.CharField(max_length=200, blank=True)
    to_block_id = models.CharField(max_length=200, blank=True)
    from_topic = models.CharField(max_length=100, blank=True)
    to_topic = models.CharField(max_length=100, blank=True)
    transition_count = models.PositiveIntegerField(default=0)
    unique_sessions = models.PositiveIntegerField(default=0)
