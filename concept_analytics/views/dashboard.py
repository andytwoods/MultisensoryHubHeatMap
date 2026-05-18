from datetime import date, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from ..models import DailyBlockSummary, BlockManifestEntry


class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "concept_analytics/dashboard/heatmap.html"
    permission_required = "concept_analytics.view_dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        metric = self.request.GET.get("metric", "unique_sessions")
        if metric not in ("unique_sessions", "total_visible_seconds", "interaction_count"):
            metric = "unique_sessions"

        # Query last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        # Bot filtering is applied when summaries are built by
        # refresh_concept_analytics_summaries (which skips is_suspicious sessions).
        summaries = DailyBlockSummary.objects.filter(date__range=(start_date, end_date))

        # Aggregate by block_id
        aggregated = {}
        max_val = 0
        for s in summaries:
            bid = s.block_id
            if bid not in aggregated:
                aggregated[bid] = 0
            val = getattr(s, metric) or 0
            aggregated[bid] += val
            if aggregated[bid] > max_val:
                max_val = aggregated[bid]

        # Get all manifest entries to structure the dashboard
        manifest = BlockManifestEntry.objects.filter(is_active=True).order_by("page_path", "display_order")

        pages = {}
        for entry in manifest:
            if entry.page_path not in pages:
                pages[entry.page_path] = {
                    "title": entry.page_title or entry.page_path,
                    "blocks": []
                }

            val = aggregated.get(entry.block_id, 0)
            intensity = (val / max_val) if max_val > 0 else 0

            pages[entry.page_path]["blocks"].append({
                "block_id": entry.block_id,
                "label": entry.label or entry.block_id,
                "value": val,
                "intensity_pct": int(intensity * 100),
            })

        context["pages"] = pages
        context["current_metric"] = metric
        context["max_val"] = max_val
        return context
