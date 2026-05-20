from datetime import date, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.management import call_command
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from ..models import AnalyticsSession, AnalyticsEvent, DailyBlockSummary, BlockManifestEntry, ManifestSyncState


class BuildReportsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "concept_analytics.view_dashboard"

    def _sync_manifest(self):
        from ..conf import get_setting
        from ..manifest_sync import _import_entries
        import json, urllib.request

        site_url = get_setting("SITE_URL")
        if not site_url:
            raise ValueError(
                "CONCEPT_ANALYTICS['SITE_URL'] is not set. "
                "Use 'http://localhost:3000' locally or the live site URL in production."
            )

        url = site_url.rstrip("/") + "/manifest.json"
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = json.loads(resp.read())
        report_name = raw.get("report_name", "") if isinstance(raw, dict) else ""
        entries = raw.get("blocks", raw) if isinstance(raw, dict) else raw
        count = _import_entries(entries)
        from ..manifest_sync import _save_version
        _save_version(raw.get("version", ""), report_name)
        label = f" ({report_name})" if report_name else ""
        return f"Report structure synced from {url}{label} — {count} blocks."

    def post(self, request):
        action = request.POST.get("action", "")
        try:
            if action == "import_manifest":
                msg = self._sync_manifest()
                messages.success(request, msg)
            elif action == "refresh_summaries":
                call_command("refresh_concept_analytics_summaries", days=30)
                messages.success(request, "Summaries rebuilt for the last 30 days.")
            elif action == "build_all":
                msg = self._sync_manifest()
                call_command("refresh_concept_analytics_summaries", days=30)
                messages.success(request, f"{msg} Summaries rebuilt for the last 30 days.")
            else:
                messages.error(request, "Unknown build action.")
        except Exception as exc:
            messages.error(request, f"Build failed: {exc}")
        return redirect(
            f"/analytics/dashboard/?metric={request.GET.get('metric', 'unique_sessions')}"
            f"&filter={request.GET.get('filter', 'all')}"
        )


class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "concept_analytics/dashboard/heatmap.html"
    permission_required = "concept_analytics.view_dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        metric = self.request.GET.get("metric", "unique_sessions")
        if metric not in ("unique_sessions", "total_visible_seconds", "interaction_count"):
            metric = "unique_sessions"

        sort_by = self.request.GET.get("sort", "document")
        if sort_by not in ("document", "value"):
            sort_by = "document"

        # Query last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        selected_report = self.request.GET.get("report", "")

        aggregated = {}
        max_val = 0

        if selected_report:
            # Aggregate directly from events for the selected report version
            events = AnalyticsEvent.objects.filter(
                session__report_name=selected_report,
                received_at__date__range=(start_date, end_date),
                session__is_suspicious=False,
            ).exclude(block_id="")

            if metric == "unique_sessions":
                rows = events.values("block_id").annotate(val=Count("session", distinct=True))
            elif metric == "total_visible_seconds":
                rows = events.values("block_id").annotate(val=Sum("seconds_visible"))
            else:  # interaction_count
                interaction_types = [
                    "section_opened", "accordion_opened", "tab_selected",
                    "case_study_opened", "video_played", "audio_played", "interactive_started",
                ]
                rows = events.filter(event_type__in=interaction_types).values("block_id").annotate(val=Count("id"))

            for row in rows:
                val = row["val"] or 0
                aggregated[row["block_id"]] = val
                if val > max_val:
                    max_val = val
        else:
            summaries = DailyBlockSummary.objects.filter(date__range=(start_date, end_date))
            for s in summaries:
                bid = s.block_id
                if bid not in aggregated:
                    aggregated[bid] = 0
                val = getattr(s, metric) or 0
                aggregated[bid] += val
                if aggregated[bid] > max_val:
                    max_val = aggregated[bid]

        manifest = BlockManifestEntry.objects.filter(is_active=True).order_by("page_path", "display_order")

        pages = {}
        for entry in manifest:
            if entry.page_path not in pages:
                pages[entry.page_path] = {
                    "title": entry.page_title or entry.page_path,
                    "blocks": [],
                    "total": 0,
                }
            val = aggregated.get(entry.block_id, 0)
            intensity = int((val / max_val) * 100) if max_val > 0 else 0
            pages[entry.page_path]["blocks"].append({
                "block_id": entry.block_id,
                "label": entry.label or entry.block_id,
                "value": val,
                "intensity_pct": intensity,
            })
            pages[entry.page_path]["total"] += val

        if sort_by == "value":
            pages = dict(sorted(pages.items(), key=lambda kv: kv[1]["total"], reverse=True))
            for page in pages.values():
                page["blocks"].sort(key=lambda b: b["value"], reverse=True)

        current_filter = self.request.GET.get("filter", "all")

        report_names = list(
            AnalyticsSession.objects.exclude(report_name="")
            .values_list("report_name", flat=True)
            .distinct()
            .order_by("report_name")
        )
        try:
            current_report_name = ManifestSyncState.objects.get(pk=1).report_name
        except ManifestSyncState.DoesNotExist:
            current_report_name = ""

        # Daily visitors panel — last 28 days
        days_back = 28
        chart_start = end_date - timedelta(days=days_back - 1)
        raw_counts = {
            row["day"]: row["count"]
            for row in (
                AnalyticsSession.objects
                .filter(created_at__date__gte=chart_start)
                .annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(count=Count("id"))
            )
        }
        day_range = [chart_start + timedelta(days=i) for i in range(days_back)]
        daily_visitors = [{"date": d, "count": raw_counts.get(d, 0)} for d in day_range]
        max_daily = max((d["count"] for d in daily_visitors), default=1) or 1
        for d in daily_visitors:
            d["pct"] = int(d["count"] / max_daily * 100)
        total_visitors = sum(d["count"] for d in daily_visitors)

        context["pages"] = pages
        context["current_metric"] = metric
        context["current_filter"] = current_filter
        context["current_sort"] = sort_by
        context["max_val"] = max_val
        context["daily_visitors"] = daily_visitors
        context["total_visitors"] = total_visitors
        context["visitor_chart_start"] = chart_start
        context["visitor_chart_end"] = end_date
        context["report_names"] = report_names
        context["current_report_name"] = current_report_name
        context["selected_report"] = selected_report
        return context
