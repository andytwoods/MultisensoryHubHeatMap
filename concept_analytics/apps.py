from django.apps import AppConfig

class ConceptAnalyticsConfig(AppConfig):
    name = "concept_analytics"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        try:
            import concept_analytics.tasks  # noqa: F401 — registers periodic tasks with Huey
        except Exception:
            pass  # django_huey not installed or not configured (e.g. tests)
