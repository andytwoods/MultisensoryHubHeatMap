from django.urls import path
from .views.ingest import IngestView

from .views.public_summary import PublicSummaryView

from .views.dashboard import DashboardView

urlpatterns = [
    path("ingest/", IngestView.as_view(), name="concept_analytics_ingest"),
    path("summary/latest/", PublicSummaryView.as_view(), name="concept_analytics_summary"),
    path("dashboard/", DashboardView.as_view(), name="concept_analytics_dashboard"),
]
