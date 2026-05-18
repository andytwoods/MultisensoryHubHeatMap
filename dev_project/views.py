from django.http import HttpResponse

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>concept_analytics – dev</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 60px auto; padding: 0 20px; color: #222; }
  h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
  p.sub { color: #666; margin-top: 0; }
  table { border-collapse: collapse; width: 100%; margin: 1.5rem 0; }
  th { text-align: left; font-size: 0.8rem; text-transform: uppercase; color: #888; padding: 0 8px 4px; }
  td { padding: 8px; border-top: 1px solid #eee; vertical-align: top; }
  td:first-child { white-space: nowrap; }
  a { color: #0066cc; }
  code { background: #f3f3f3; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }
  .badge { display: inline-block; font-size: 0.7rem; padding: 1px 6px; border-radius: 10px;
           background: #e8f0fe; color: #1a56d6; margin-left: 6px; vertical-align: middle; }
</style>
</head>
<body>
<h1>concept_analytics <span class="badge">dev</span></h1>
<p class="sub">Minimal Django host project for local development. Not for production.</p>

<table>
  <tr><th>URL</th><th>Description</th></tr>
  <tr>
    <td><a href="/admin/">/admin/</a></td>
    <td>Django admin — browse sessions, events, and manifest entries</td>
  </tr>
  <tr>
    <td><a href="/analytics/dashboard/">/analytics/dashboard/</a></td>
    <td>HTMX heat-map dashboard</td>
  </tr>
  <tr>
    <td><code>POST /analytics/ingest/</code></td>
    <td>Event ingest endpoint — accepts batched JSON payloads from the frontend tracker</td>
  </tr>
  <tr>
    <td><a href="/analytics/summary/latest/">/analytics/summary/latest/</a></td>
    <td>Public-safe aggregate summary — requires <code>Authorization: Bearer dev-token</code></td>
  </tr>
</table>

<h2 style="font-size:1rem;">Quick reference</h2>
<p>Apply migrations and create a superuser on first run:</p>
<pre style="background:#f3f3f3;padding:12px;border-radius:4px;font-size:0.88rem;overflow-x:auto">python manage.py migrate
python manage.py createsuperuser</pre>
<p>Rebuild aggregate summary tables from raw events:</p>
<pre style="background:#f3f3f3;padding:12px;border-radius:4px;font-size:0.88rem;overflow-x:auto">python manage.py refresh_concept_analytics_summaries --days 7</pre>
<p>See <a href="https://github.com/StoryFutures/multisensoryReport">multisensoryReport</a> for the Docusaurus frontend and full project context.</p>
</body>
</html>"""


def index(request):
    return HttpResponse(_HTML)
