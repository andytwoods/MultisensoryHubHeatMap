from django.apps import AppConfig

class ConceptAnalyticsConfig(AppConfig):
    name = "concept_analytics"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        try:
            import concept_analytics.tasks  # noqa: F401 — registers periodic tasks with Huey
        except ImportError:
            pass  # django_huey not installed in this environment (e.g. tests)
