# OVERVIEW.md – Multisensory Hub Concept Analytics

## 1. Project summary

We want to build a lightweight, privacy-conscious analytics system for the Multisensory Hub:

https://storyfutures.github.io/multisensoryReport/

The goal is not to build a general-purpose Google Analytics replacement. The goal is to create a research-oriented instrument that helps us understand which topics, concepts, sections, and interactive elements in the Hub attract attention and engagement from visitors.

The system should measure aggregate engagement with the report while avoiding unnecessary personal tracking.

The reusable Django app/package name for v1 is:

```text
concept_analytics
```

Rationale: `concept_analytics` reflects the intended package focus: aggregate engagement with tagged concepts, topics, and content blocks. The internal measurement remains active viewport exposure.

Development/deployment intent:

- develop the app first inside a minimal Django host project;
- keep `concept_analytics` installable as a reusable Django app;
- later install the finished app into the more established Django project at `costartools.uk`;
- avoid hard-coding assumptions from either the temporary development host or the final CoSTAR Tools host.

---

## 2. Core research question

Which topics and concepts in the Multisensory Hub are most popular, engaging, or useful to visitors from the UK creative industries and related communities?

Secondary questions may include:

- Which topics are visited most often?
- Which topics receive the most active dwell time?
- Which concepts are actually brought into view by visitors?
- Which sections are skimmed versus engaged with?
- Which concepts commonly appear in the same sessions?
- Which concepts lead to downstream actions such as downloads, external link clicks, or further navigation?
- Which search terms indicate unmet interest?
- Which parts of the report are underused or hard to discover?
- How do people move through the report from page to page and concept to concept?
- Which content changes appear to alter engagement patterns?

---

## 3. What we mean by “read”

The system should avoid claiming that we know what people literally read or understood.

Instead, we will measure behavioural proxies such as:

- page views;
- topic views;
- section views;
- tagged concept exposure;
- active viewport dwell time;
- scroll depth;
- interaction with accordions, tabs, media, visualisations, downloads, and external links;
- internal search terms, if available;
- navigation pathways through the report.

Preferred terminology:

> active viewport exposure to tagged concepts

or:

> opportunity to read

rather than:

> people read this concept

Avoid claiming that a visitor understood, liked, valued, learned, or paid attention to content unless a separate measure supports that claim.

---

## 4. Scope

### 4.1 In scope

- A React/Docusaurus tracking layer embedded in the Hub.
- An author-facing `TrackedBlock` MDX/React component.
- A Django backend endpoint for receiving analytics events.
- A PostgreSQL database schema for storing short-retention raw/near-raw events and longer-retention aggregate summaries.
- Topic/concept tagging using Docusaurus/MDX components and build-time manifests.
- Active dwell-time measurement using visibility, viewport detection, heartbeat timing, and idle detection.
- Event batching to avoid excessive network requests.
- Ordered session/pathway data for page-level and block/concept-level transitions.
- A private HTMX dashboard and/or Django admin summaries.
- CSV/JSON export for research analysis.
- A later static public aggregate heat map served from GitHub Pages.

### 4.2 Out of scope for v1

- Replacing Matomo, Plausible, GA4, or PostHog as a full analytics platform.
- Individual-level user profiling.
- Session replay.
- Raw mouse-path tracking.
- Keystroke content tracking.
- Cross-site tracking.
- Advertising attribution.
- Fingerprinting.
- Named-user analytics.
- Returning-visitor tracking across days/weeks.
- A polished public dashboard before the instrumentation has been validated.

---

## 5. Design principles

1. **Research-first**  
   The system should answer specific research and dissemination questions, not collect data simply because it is available.

2. **Privacy-conscious by design**  
   Avoid storing names, emails, raw IP addresses, full browser fingerprints, or unnecessary free text.

3. **Aggregate reporting by default**  
   Analyses should primarily report topic-level, concept-level, block-level, and page-level patterns.

4. **Minimal visitor burden**  
   Use clear notice and opt-out rather than intrusive pop-ups, given RHUL/StoryFutures approval for this setup.

5. **Transparent**  
   The Hub should include a clear analytics notice explaining what is collected and why.

6. **Portable**  
   The tracker should be usable on a static Docusaurus site hosted on GitHub Pages.

7. **Simple enough to maintain**  
   Prefer a small, understandable codebase over a complex analytics platform.

8. **Open-sourceable later**  
   Build clean boundaries so the Django app can potentially be packaged later, but do not over-generalise v1.

9. **Version-aware**  
   Engagement metrics must be connected to the content version that generated them, not just to URLs.

10. **Safe by failure**  
   If analytics fail, the Hub should continue working normally.

---

## 6. Proposed architecture

```text
Docusaurus / GitHub Pages site
        ↓
React/Docusaurus analytics tracker
        ↓
Django analytics API provided by installable `concept_analytics` app
        ↓
Temporary minimal Django host project during development
        ↓
Later installed into established CoSTAR Tools host project (`costartools.uk`)
        ↓
PostgreSQL database
        ↓
Private HTMX dashboard / Django admin / exports
        ↓
Public-safe aggregate summary endpoint
        ↓
Scheduled GitHub Actions workflow in StoryFutures/multisensoryReport
        ↓
Static JSON files committed into the Docusaurus repository
        ↓
Docusaurus rebuilds and GitHub Pages serves a static delayed public heat map
```

The key architectural split is:

- **Django** collects raw/near-raw events, stores them temporarily, aggregates them, powers the private dashboard, and exposes a public-safe summary endpoint.
- **GitHub Actions** pulls already-suppressed aggregate summaries from Django, commits static JSON into the Docusaurus repository, and lets the existing GitHub Pages build publish the static public/visitor-facing heat map.
- **GitHub Pages** never needs to query Django from a visitor's browser for the public heat map.

### 6.1 Repository integration

The Multisensory Hub repository is the **existing** `MultisensoryHub` repo (locally at `MultisensoryHub/`, published at `https://github.com/StoryFutures/multisensoryReport`). It already has:

- a GitHub Actions CI pipeline at `.github/workflows/deploy.yml` that runs `docx_to_mdx.py`, `pages_to_mdx.py`, npm build, and deploys to GitHub Pages on every push to `master`;
- a Docusaurus 3 site at `docusaurus-site/`;
- existing React components at `docusaurus-site/src/components/`;
- an existing theme override directory at `docusaurus-site/src/theme/`.

The analytics system integrates into this existing structure — it does not create a new repository.

Current decision:

- Use **GitHub Actions pull**, not Django push.
- The repository workflow should fetch public-safe aggregate JSON from a custom Django endpoint.
- The workflow should commit those JSON files into `docusaurus-site/static/analytics/` (following the existing `docusaurus-site/static/media/` pattern).
- The normal Docusaurus/GitHub Pages build then serves the static heat map from `/analytics/`.

Preferred nightly flow:

```text
1. Django receives events from the frontend tracker.
2. Django aggregates raw events into public-safe summaries.
3. A scheduled GitHub Actions workflow runs nightly.
4. The workflow calls a custom Django summary endpoint.
5. Django returns only delayed, suppressed, public-safe aggregate JSON.
6. The workflow writes files such as:
   - docusaurus-site/static/analytics/block-heatmap.latest.json
   - docusaurus-site/static/analytics/topic-summary.latest.json
   - docusaurus-site/static/analytics/dashboard-build-info.json
7. The workflow commits those files to the repository.
8. The existing Docusaurus build publishes the static public heat map.
```

### 6.2 Securing the GitHub-to-Django summary endpoint

Recommended v1 security model:

- Django exposes a route such as:

```text
GET /analytics/api/public-summary/latest/
```

- The endpoint requires an `Authorization: Bearer ...` token stored as a GitHub Actions secret.
- The endpoint returns only public-safe aggregate data.
- The endpoint must not return session IDs, individual ordered paths, raw timestamps, raw referrers, or unsuppressed small cells.
- The endpoint should be rate-limited.
- The endpoint should log access attempts for operational security.
- Optional GitHub Actions IP allowlisting can be added as defence-in-depth, but it should not be the main authentication mechanism.

Rationale:

- GitHub-hosted runner IP ranges are broad, shared, and can change.
- IP allowlisting alone proves only that a request came from GitHub infrastructure, not that it came from the intended repository workflow.
- A bearer token is adequate for v1 because the endpoint is deliberately low-privilege and aggregate-only.
- GitHub OIDC or signed request validation can be a v2 hardening task if institutional security requires it.

### 6.3 Suggested GitHub Actions workflow

Add this as `.github/workflows/update-analytics.yml` in the MultisensoryHub repository, **alongside** the existing `.github/workflows/deploy.yml`. It is a separate scheduled workflow — do not merge it into `deploy.yml`.

```yaml
name: Update public analytics summaries

on:
  schedule:
    - cron: "17 2 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update-analytics:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Fetch public-safe analytics summaries
        run: |
          mkdir -p docusaurus-site/static/analytics
          curl -sSf \
            -H "Authorization: Bearer ${{ secrets.ANALYTICS_SUMMARY_TOKEN }}" \
            "${{ vars.ANALYTICS_SUMMARY_URL }}" \
            -o docusaurus-site/static/analytics/public-summary.latest.json

      - name: Smoke test summary
        run: |
          python multisensoryHubHeatMap/scripts/validate_public_summary.py \
            docusaurus-site/static/analytics/public-summary.latest.json

      - name: Commit updated analytics summaries
        run: |
          git config --local user.name "github-actions"
          git config --local user.email "github-actions@github.com"
          git add docusaurus-site/static/analytics/public-summary.latest.json
          git diff --cached --quiet || git commit -m "Update public analytics summaries"
          git push
```

Configuration notes:

- The Django summary URL should not be left as a literal placeholder. Store it as a GitHub Actions variable such as `ANALYTICS_SUMMARY_URL`.
- Store the bearer token as a GitHub Actions secret such as `ANALYTICS_SUMMARY_TOKEN`.
- Prefer `git config --local` in the job so the identity applies only to this checkout.

Branch-protection note:

- If the default branch is protected, direct pushes from `GITHUB_TOKEN` may fail.
- Options include:
  - allow the specific workflow to push to the protected branch if repository policy permits;
  - have the workflow open a pull request instead of pushing directly;
  - use a GitHub App token or fine-scoped PAT if institutional/repo policy allows;
  - write summaries to a dedicated unprotected data branch and have the build read from that branch.
- For v1, prefer the simplest route that complies with repository branch-protection rules. If branch protection is active, the pull-request workflow is the safer default.

Scheduling notes:

- Use an off-peak, non-round cron time such as `02:17 UTC` rather than exactly on the hour.
- Include `workflow_dispatch` so the team can manually refresh public summaries when testing.

### 6.4 Static public summaries in the repository

The GitHub repository can contain:

- analytics metadata;
- tracked-block manifests;
- concept vocabulary;
- public-safe aggregate summary JSON;
- generated static heat-map data;
- dashboard build metadata.

The GitHub repository must not contain:

- raw behavioural event rows;
- session IDs;
- individual ordered session paths;
- unsuppressed small-count data;
- raw referrer URLs;
- raw timestamps that could reconstruct individual visits.

Suggested repo structure (within the MultisensoryHub repository):

```text
analytics/                              ← human-editable config (repo root)
  concepts.yml
  tracked-blocks.yml                    ← source of truth for TrackedBlock injection
  manifest.schema.json
  analytics-notice.md
  CHANGELOG.md

docusaurus-site/static/analytics/       ← generated; follows existing static/media/ pattern
  public-summary.latest.json
  block-heatmap.latest.json
  topic-summary.latest.json
  dashboard-build-info.json
```

Avoid committing a new dated JSON file every night. Overwrite stable `*.latest.json` files by default to reduce repository bloat. Keep dated snapshots only for releases, audits, or major content updates.


### 6.5 Reusable Django app and host-project separation

The Django implementation should be structured as an installable reusable app, not as code tied permanently to the temporary development project.

Current decision:

```text
Reusable app/package: concept_analytics
Temporary development host: minimal Django project
Final likely host: established CoSTAR Tools project at costartools.uk
```

Design implications:

- `concept_analytics` should contain models, views, URLs, forms, templates, management commands, static assets, tests, and documentation needed for the analytics app.
- Host-project settings should configure site-specific values such as allowed origins, ingest endpoint paths, dashboard permissions, retention settings, summary-token authentication, and public-summary export behaviour.
- The app should not assume a specific project name, domain, database name, URL prefix, template base, or authentication setup.
- The app should provide a small `urls.py` that the host project can include under a configurable path such as:

```python
path("analytics/", include("concept_analytics.urls"))
```

- The app should define default settings with clear override points, for example:

```python
CONCEPT_ANALYTICS_ALLOWED_ORIGINS = ["https://storyfutures.github.io"]
CONCEPT_ANALYTICS_PUBLIC_SUMMARY_TOKEN = None
CONCEPT_ANALYTICS_RAW_EVENT_RETENTION_DAYS = 180
CONCEPT_ANALYTICS_DEBUG_TRAIL_RETENTION_DAYS = 90
CONCEPT_ANALYTICS_PUBLIC_SUPPRESSION_MIN_SESSIONS = 10
CONCEPT_ANALYTICS_PRIVATE_SUPPRESSION_MIN_SESSIONS = 5
```

- The temporary minimal project should exist only to develop, test, and demonstrate the app.
- The final installation into `costartools.uk` should require only ordinary Django installation steps: install package, add to `INSTALLED_APPS`, include URLs, run migrations, configure settings, collect static files, and schedule management commands.

Recommended repository layout during development:

```text
concept-analytics/
  pyproject.toml
  README.md
  concept_analytics/
    __init__.py
    apps.py
    models.py
    urls.py
    views.py
    admin.py
    forms.py
    templates/concept_analytics/
    static/concept_analytics/
    management/commands/
    migrations/
    tests/
  example_project/
    manage.py
    example_project/
      settings.py
      urls.py
```

Packaging recommendation:

- use `pyproject.toml`;
- keep dependencies minimal;
- support installation from Git initially, then package properly if open-sourcing;
- include an `example_project` for local development and documentation;
- make migrations part of the reusable app;
- include tests that run against SQLite for simple checks and PostgreSQL for integration/performance checks where needed.

Host-project integration risks:

- authentication and permissions may differ between the minimal development app and `costartools.uk`;
- dashboard templates may need to extend a host-specific base template;
- scheduled jobs may be run differently in the final host;
- CORS, proxy headers, and rate limiting may be configured at the host/project or Nginx layer rather than inside the app;
- database scale/performance should be checked again after installation in the established project.

Recommended mitigation:

- define a clear host-integration checklist before installing into `costartools.uk`;
- keep all CoSTAR Tools-specific configuration outside the reusable app;
- add a small smoke-test management command, for example:

```text
python manage.py concept_analytics_check
```

to verify settings, migrations, summary endpoint configuration, retention jobs, and dashboard access after installation.


---

## 7. Current project decisions

### 7.1 Primary purpose

- The project is for **academic research and creative-industry insight**.
- The engagement data itself is not primarily intended for publication.
- The **method** may be publishable/openly shared.
- The analytics outputs should help industry partners understand interest patterns.
- The analytics outputs should also help the team refine the Hub itself.

Implication:

- The system should be robust enough to be methodologically defensible, but it does not need the full burden of a formal participant-level research study unless later positioned that way.
- Dashboard language should remain careful: use `exposure`, `engagement`, and `attention proxy`, not claims of comprehension or preference.

### 7.2 Deployment

- The tracker only needs to support this Multisensory Hub initially.
- The Django code should nevertheless be built as an **installable reusable app** from the start.
- Development should happen in a minimal Django host project.
- The finished app should later be installed into the more established CoSTAR Tools project at `costartools.uk`.
- The Django app may later be open sourced.
- Build for this specific use case first, but keep host-project boundaries clean enough for packaging and reuse.

### 7.3 Privacy and consent

Current decisions and recommended defaults:

- RHUL/StoryFutures allows **notice + opt-out** for this analytics setup.
- Explicit opt-in consent is not required for v1, provided the tracker remains within the agreed scope.
- UK GDPR legal basis: legitimate interest, with a Legitimate Interest Assessment confirmed before launch.
- No need to track returning visitors across days/weeks.
- Use a **cookie-free `sessionStorage` anonymous session ID**.
- Generate a random session ID per browser tab/session.
- Do not attempt to identify returning visitors.
- Do not store raw IP addresses.
- IP addresses should be discarded immediately after request handling.
- Store referrer **domain only** by default, not full referrer URL.
- Store coarse device class and viewport size, but avoid detailed fingerprinting.
- Use IP only transiently for rate limiting/security at the web server or middleware level if needed, without persisting it in analytics tables.

This decision should be revisited if the system later adds:

- cookies for repeat-visitor tracking;
- richer free-text capture;
- individual-level journeys in ordinary dashboards;
- session replay;
- cross-site tracking;
- named-user linkage;
- raw mouse-path or keystroke capture;
- fingerprinting or persistent device identification.

### 7.4 Opt-out mechanism

Opt-out preference is persisted via `localStorage`:

```text
concept_analytics_optout
```

This persists across sessions in the same browser without requiring a cookie.

The tracker must check this key on initialisation. If present and set to `"1"`, no events should be sent and no session ID should be created.

The analytics notice must include a visible opt-out mechanism, such as a link or button that sets the key and confirms the opt-out to the visitor.

### 7.5 Notice placement

The analytics notice must be clearly visible to visitors, for example in the site footer or on a dedicated privacy/analytics page linked from the footer. The notice must be in place before the tracker is activated in production.

Suggested analytics notice:

> We collect anonymous, aggregate engagement data to understand which topics and sections of this report are useful to visitors. We do not collect names, emails, raw IP addresses, or use third-party advertising analytics. You can opt out of analytics at any time.

### 7.6 `sessionStorage` trade-off

Using `sessionStorage` for session IDs means:

- each new browser tab creates a new session;
- sessions are lost when the tab closes;
- a visitor who returns tomorrow appears as a new session;
- session counts will overestimate unique individuals.

This is intentional. It avoids returning-visitor tracking and cookie-consent complexity. Reports should refer to sessions, not users.

### 7.7 Do Not Track and Global Privacy Control

Recommended v1 behaviour:

- Honour Global Privacy Control where straightforward.
- Consider honouring Do Not Track, though browser support and interpretation are inconsistent.
- In either case, the local visitor opt-out must always be available and respected.

---

## 8. Frontend tracking approach

The frontend tracker should detect and send the following classes of events.

### 8.1 Page/session events

- `session_start`
- `page_view`
- `page_visible_heartbeat`
- `page_hidden`
- `page_unload`
- `session_resume`

`session_resume` definition:

- fire when a previously hidden page becomes visible again; and/or
- fire when a previously idle session becomes active again after visitor activity resumes.

Implementation note: distinguish the reason in metadata, for example:

```json
{"resume_reason": "visibility"}
```

or:

```json
{"resume_reason": "idle_recovery"}
```

Do not treat `session_resume` as a new session. It is a continuation of the existing `sessionStorage` session.

### 8.2 Topic and concept exposure events

Concepts and sections can be marked up via reusable MDX/React components:

```mdx
<TrackedBlock
  blockId="scent-case-study-royal-opera-house"
  topic="sensory-modalities"
  concept="scent"
  contentType="case-study"
  label="Scent case study"
>
  ...
</TrackedBlock>
```

The tracker should use `IntersectionObserver` to determine whether tagged elements are in view.

A concept should count as exposed only when:

- the element is in the viewport above the visibility threshold;
- the browser tab is visible/active;
- the exposure lasts longer than the minimum duration;
- the visitor has not been idle for longer than the idle threshold;
- the event has not already been over-counted within the same heartbeat window.

Candidate exposure events:

- `concept_enter_view`
- `concept_visible_heartbeat`
- `concept_exit_view`

### 8.3 Interaction events

Track meaningful interactions, for example:

- `section_opened`
- `accordion_opened`
- `tab_selected`
- `case_study_opened`
- `video_played`
- `audio_played`
- `interactive_started`
- `download_clicked`
- `external_link_clicked`
- `internal_link_clicked`
- `search_submitted`

### 8.4 Navigation/pathway events

Track transitions at both levels:

- page-to-page transitions;
- block/concept-to-block/concept transitions.

The dashboard should generally default to page/topic-level pathways, because block-level pathways may be noisy, while still keeping block-level pathway data available for deeper analysis.

---

## 9. Docusaurus/React implementation architecture

Target assumption: the Hub is using Docusaurus v3. The suggested `src/theme/Root.js` integration point assumes the Docusaurus v3 theme/swizzle structure. If the project is on a different Docusaurus version, confirm the equivalent root-wrapper integration point before implementation.

Because Docusaurus behaves as a React single-page application, the tracker must not rely only on traditional page-load events such as `window.onload`.

Problem:

- `window.onload` fires once when the app first loads.
- Client-side navigation between Docusaurus routes does not necessarily refresh the browser.
- A vanilla tracker could miss later `page_view` events, keep old page state alive, or leave stale `IntersectionObserver` registrations attached to blocks from the previous route.

Required v1 approach:

- Use Docusaurus/React routing state to detect page changes.
- Use a `useEffect` hook tied to the current `location.pathname`.
- On each route change:
  - flush queued events for the previous page;
  - emit a new `page_view` event;
  - reset active page state;
  - reset page-level scroll-depth tracking;
  - preserve the anonymous `sessionStorage` session ID.

Scope note:

- **v1 React work**: `AnalyticsProvider`, route-aware `page_view`, opt-out handling, batching, downloads, outbound/internal link clicks, and safe failure.
- **v2 React work**: central `IntersectionObserver`, `TrackedBlock` exposure timing, idle-aware concept dwell time, and block/concept-to-block/concept transitions.
- The architecture should be designed so v2 can be added cleanly, but v1 should not be blocked on full dwell-time tracking.

Suggested Docusaurus integration points:

```text
src/theme/Root.js
  → wraps the site in <AnalyticsProvider>

src/components/TrackedBlock.jsx
  → author-facing MDX wrapper

src/hooks/useConceptTracker.js
  → registers tracked blocks with the central observer

src/hooks/useUserActivity.js
  → tracks idle/active state

src/hooks/useRouteAnalytics.js
  → handles route changes and cleanup
```

Recommended React structure:

```text
AnalyticsProvider
  - owns the event queue
  - owns the heartbeat timer
  - owns the central IntersectionObserver
  - owns session ID creation
  - owns opt-out/development-mode checks
  - exposes registerBlock/unregisterBlock through context

TrackedBlock
  - accepts blockId, topic, concept, contentType, label as props
  - renders children normally
  - attaches a ref
  - registers/unregisters itself with AnalyticsProvider
```

Performance guidance:

- Use one central `IntersectionObserver` instance where possible rather than one observer per block.
- Store mutable queue/visibility state in `useRef` where appropriate to avoid excessive React re-renders.
- Batch events during the 15-second heartbeat and on page hide/unload.
- Do not send a network request for every `concept_enter_view` event.
- Use `navigator.sendBeacon` for final flushes when available.

Heartbeat safety:

- The 15-second heartbeat interval must be cleared on unmount.
- The heartbeat must be paused or ignored when `document.visibilityState === "hidden"`.
- When the document becomes hidden, flush queued events and stop counting active exposure.
- When the document becomes visible again, send a `page_visible` or `session_resume` event and restart active counting.
- Avoid ghost events from previous routes by ensuring route-change cleanup runs before registering new blocks.

Idle hook:

- Implement `useUserActivity` as a small global hook inside the provider.
- Listen for coarse activity events: `scroll`, `click`, `keydown`, `pointermove`, `touchstart`.
- Do not record actual key content, pointer co-ordinates, or mouse trails.
- Maintain only an `isIdle` flag and `lastActivityAt` timestamp.
- Pause concept-level dwell counting once the idle threshold is reached.

Opt-out and development safeguards:

- The tracker should not run if the visitor has opted out.
- The tracker should not send data in local development unless explicitly enabled.
- The tracker should support a simple environment/config flag such as `analyticsEnabled`.
- A visitor opt-out should be respected before session ID creation where possible.

Error containment:

- Wrap analytics components in an Error Boundary.
- Analytics failures must not crash the Multisensory Hub report.
- If the tracker fails, the site should continue to function normally.

Stable ID enforcement:

- In development mode, `TrackedBlock` should warn if `blockId` is missing.
- The provider or build-time manifest validator should warn or fail if duplicate `blockId`s are detected on a page/build.
- Build-time validation is preferred for duplicate detection because some blocks may not render at the same time in the SPA.

Recommended v1 simplification:

- Build the React tracking layer first around `TrackedBlock`, `AnalyticsProvider`, route-change handling, and batched heartbeats.
- Avoid automatic keyword tagging until the block-level tracker and manifest validation are stable.

---

## 10. Topic/concept tagging

Current decision:

- Expect around **30–40 concepts/topics**.
- Use **designated meaningful blocks** rather than every keyword occurrence.
- Support both manual tagging and some later automatic tagging from a concept vocabulary.
- Distinguish between content types such as sections, case studies, figures, videos, tools, glossary terms, downloads, and interactive components.
- Tracked blocks may be both:
  - larger sections under headings;
  - smaller cards, case studies, figures, media elements, and interactive components.

Recommended default:

- v1 should use **manual block tagging** only.
- v2 can add build-time helper tools to suggest tags from a controlled vocabulary.
- Inline keyword tagging should be avoided unless the term is a deliberate glossary-style anchor or callout.
- Every tracked block must have a stable `block_id`.
- `block_id` values should be human-readable and stable across deployments.

---

## 11. Site versions, content hashes, and tracked-block manifests

The site is hosted from GitHub Pages and built through GitHub Actions. Its source history is already captured in Git. The analytics system should explicitly connect engagement metrics to the content version being measured.

Key principle:

```text
block_id identifies the intended conceptual/content unit.
content_hash identifies the exact text/content version that was measured.
position_hash identifies the block's structural location in the report.
```

If a block remains conceptually the same but its text changes, it can keep the same `block_id` but should receive a new `content_hash` and `block_version_id`.

### 11.1 Content hash definition

`content_hash` should be generated from a canonicalised representation of the tracked block's content.

Recommended v1 rule:

```text
content_hash = SHA-256(canonical_text_content)
```

Where `canonical_text_content` means:

- extract the textual content inside the `TrackedBlock`;
- remove HTML/MDX tags;
- decode entities;
- normalise whitespace to single spaces;
- trim leading/trailing whitespace;
- normalise Unicode consistently;
- lowercase only if the team decides that case-only edits should not create a new version.

Recommended default: **do not lowercase**. Case changes are rare and preserving case makes the hash more literal.

Do **not** hash:

- rendered pixel position;
- compiled React output;
- generated class names;
- volatile build artefacts;
- analytics metrics.

Rationale:

- MDX source can change without changing visible text.
- Rendered HTML may include generated or layout-specific artefacts.
- Compiled React output is too unstable.
- Canonical text is easier to reason about and sufficient for v1.

For blocks where non-text content is central, add optional hash inputs:

```text
canonical_text_content
+ image src/alt text
+ video/audio src/title
+ download href/label
+ manually supplied version note
```

### 11.2 Position hash definition

`position_hash` should identify the block's structural location, not its rendered pixel position.

Recommended v1 rule:

```text
position_hash = SHA-256(page_path + heading_path + display_order + parent_block_id)
```

Where:

- `page_path` is the Docusaurus route/path;
- `heading_path` is the ordered heading hierarchy above the block;
- `display_order` is the block's order among tracked blocks on the page;
- `parent_block_id` is optional, used for nested tracked blocks.

Do **not** use pixel offsets or viewport co-ordinates for `position_hash`.

Purpose:

- detect when a block has moved within the document;
- separate content changes from layout/position changes;
- support before/after comparisons when a page is reorganised.

### 11.3 Block version ID

Recommended v1 rule:

```text
block_version_id = block_id + ":" + short_content_hash
```

Example:

```text
scent-case-study-royal-opera-house:sha256-abcd1234
```

The full hash should be stored in the manifest; the shortened form is acceptable for readable IDs.

### 11.4 Tracked-block manifest

The Docusaurus build should generate or validate a tracked-block manifest.

Manifest fields may include:

- `block_id`
- `block_version_id`
- `content_hash`
- `position_hash`
- `page_path`
- `page_title`
- `heading_path`
- `display_order`
- `topic`
- `concept`
- `content_type`
- `label`
- `parent_block_id`
- `first_seen_commit`
- `last_seen_commit`
- `replaces_block_ids`
- `replaced_by_block_ids`
- `is_active`

The manifest should live in the GitHub repository and be version-controlled.

### 11.5 How `TrackedBlock` gets into MDX

**Critical constraint**: `docx_to_mdx.py` is the canonical pipeline and regenerates all MDX from scratch on every run. Any `TrackedBlock` wrappers manually inserted into `.mdx` files will be silently wiped the next time the pipeline runs. Manual post-editing of generated MDX is not a viable strategy.

`TrackedBlock` wrappers must be injected **by `docx_to_mdx.py`** during MDX generation, guided by `analytics/tracked-blocks.yml`.

#### `analytics/tracked-blocks.yml` format

A human-edited YAML file listing the blocks to track. Each entry maps a stable `block_id` to a heading string that identifies where in the Word document the block begins:

```yaml
blocks:
  - block_id: scent-intro
    heading: "Scent and Olfactory Design"
    topic: scent
    concept: olfactory-design
    content_type: section
    label: "Introduction to Scent"

  - block_id: scent-case-study-royal-opera-house
    heading: "Royal Opera House Case Study"
    topic: scent
    concept: olfactory-design
    content_type: case-study
    label: "Royal Opera House case study"
```

The `heading` value must match the heading text in the Word document exactly (post-Pandoc normalisation). `docx_to_mdx.py` uses it to locate the correct MDX section.

#### Required changes to `docx_to_mdx.py`

Add a post-processing step after MDX generation that:

1. Reads `analytics/tracked-blocks.yml` (skip silently if file does not exist, so the pipeline remains usable without analytics configured).
2. For each block entry, locates the matching heading in the generated MDX by normalised heading text.
3. Wraps the content between that heading and the next same-or-higher-level heading in a `<TrackedBlock>` JSX component:
   ```mdx
   <TrackedBlock blockId="scent-intro" topic="scent" concept="olfactory-design" contentType="section" label="Introduction to Scent">

   ## Scent and Olfactory Design

   ...content...

   </TrackedBlock>
   ```
4. Adds the `TrackedBlock` import to the MDX file's import block if not already present:
   ```mdx
   import TrackedBlock from '@site/src/components/TrackedBlock';
   ```
5. Warns (does not error) if a `tracked-blocks.yml` heading cannot be matched in any generated MDX file — this means the Word document heading changed and the YAML needs updating.
6. Errors and exits non-zero if two blocks in `tracked-blocks.yml` have the same `block_id`.

#### v1 workflow

```text
author edits analytics/tracked-blocks.yml
        ↓
python docx_to_mdx.py runs (pipeline as before)
        ↓
post-processing step injects <TrackedBlock> wrappers from tracked-blocks.yml
        ↓
manifest validator checks block IDs and required metadata
        ↓
Docusaurus build proceeds
```

#### What does NOT change in `docx_to_mdx.py`

- Do not alter the Pandoc conversion step.
- Do not alter heading splitting, slug generation, link rewriting, or any other existing pipeline stage.
- The `TrackedBlock` injection is a final post-processing step only — it reads the already-generated MDX and rewrites it in place.
- The `AI_CONTEXT.md` rule ("changes must be implemented by modifying `docx_to_mdx.py`") applies here: the injection logic lives in `docx_to_mdx.py`, not in a separate script.

### 11.6 Content-change handling

The dashboard should support:

- current content version only;
- all historical versions of this block;
- before/after a content change;
- before/after a Git commit;
- before/after a named site release.

This matters because engagement may change because:

- visitors became more interested in a topic;
- the content moved higher up the page;
- the wording changed;
- a block was split or merged;
- the layout changed;
- the instrumentation changed.

### 11.7 Manual block lifecycle relationships

The manifest should optionally support:

```text
old block A was split into new blocks B and C
old blocks A and B were merged into new block C
old block A was replaced by block B
```

These relationships should be manually reviewed rather than inferred automatically.

---

## 12. Dwell-time definition

Dwell time should be measured as **active visible time**, not simply time between page load and navigation away.

A heartbeat approach should be used:

- Every N seconds, check which tagged concepts/sections are visible.
- Only count time when `document.visibilityState === "visible"`.
- Apply idle detection to reduce inflated readings from unattended open tabs.
- Send batched heartbeat events to the backend.

Recommended default rules:

- Count time only when `document.visibilityState === "visible"`.
- Count concept exposure when at least **50% of the block is visible**.
- Minimum exposure before counting: **3 seconds**.
- Heartbeat interval: **15 seconds**.
- Batch visible concept exposure into heartbeat events.
- Store `intersection_ratio`, `visible_seconds`, and `scroll_depth`.

### 12.1 Idle-tab protection

Tab visibility alone is insufficient because a visible browser window can be unattended.

Recommended rule:

- Track recent user activity signals: scroll, click, keydown, pointermove, touchstart.
- Define the session as idle if there has been no activity for **60 seconds**.
- Stop counting concept-level active exposure after 60 seconds without scroll/click/key/touch/pointer activity.
- Resume counting when activity resumes.
- Cap or flag unusually long exposures to avoid inflated dwell from open tabs.

Suggested caps/flags:

```text
flag concept exposures > 10 minutes in one session
flag page sessions > 30 minutes with low activity
```

Rationale:

- Pointer movement alone is imperfect because people may read without moving the mouse.
- A combined rule is more defensible: visible tab + viewport exposure + recent activity, with caps/flags.

---

## 13. Event payload and transport

### 13.1 Example batched payload

```json
{
  "session_id": "anonymous-random-session-id",
  "page_path": "/multisensoryReport/docs/scent",
  "page_title": "Scent",
  "referrer_domain": "example.org",
  "viewport": {
    "width": 1440,
    "height": 900
  },
  "events": [
    {
      "event_sequence": 14,
      "event_type": "concept_visible_heartbeat",
      "block_id": "scent-case-study-royal-opera-house",
      "block_version_id": "scent-case-study-royal-opera-house:sha256-abcd",
      "content_hash": "sha256-abcd",
      "concept": "scent",
      "topic": "sensory-modalities",
      "content_type": "case-study",
      "seconds_visible": 15,
      "intersection_ratio": 0.74,
      "scroll_depth": 0.68,
      "previous_page_path": "/multisensoryReport/docs/introduction",
      "previous_block_id": "intro-overview"
    },
    {
      "event_sequence": 15,
      "event_type": "download_clicked",
      "block_id": "scent-resource-download",
      "concept": "case-study",
      "topic": "industry-applications",
      "target_path": "/multisensoryReport/downloads/scent-case-study.pdf"
    }
  ]
}
```

### 13.2 URL minimisation

Use:

- `referrer_domain`, not full referrer URL;
- `target_path` for internal links/downloads;
- `target_domain` for external links;
- no full external target URLs by default.

Full URLs should be stored only if there is a specific research/operational reason and the privacy notice is updated accordingly.

### 13.3 CORS and cross-origin transport

The tracker runs on `https://storyfutures.github.io` and posts to a Django backend on a different origin. Every ingest request is cross-origin.

Required backend configuration:

- Install and configure `django-cors-headers`.
- Set:

```python
CORS_ALLOWED_ORIGINS = ["https://storyfutures.github.io"]
```

- Do not use `CORS_ALLOW_ALL_ORIGINS = True`.
- The ingest endpoint must be CSRF-exempt because it receives cross-origin POSTs with no Django session.

### 13.4 `fetch()` and `sendBeacon()` split

Recommended transport strategy:

- Use `fetch()` with `Content-Type: application/json` for regular heartbeat batches.
- Use `navigator.sendBeacon()` for page hide/unload final flushes.
- When using `sendBeacon()`, send a string or Blob with `Content-Type: text/plain` to avoid CORS/preflight complications.
- The Django view must accept and parse both `application/json` and `text/plain` JSON bodies.

Rationale:

- `sendBeacon()` is useful for final flushes but has content-type constraints.
- Regular heartbeat traffic is easier to validate and debug using normal JSON `fetch()`.
- The backend must be deliberately designed to accept both transport modes.

### 13.5 Backend-down behaviour

If the analytics backend is down:

- the Hub must continue working normally;
- event sends may fail silently in v1;
- the tracker should not show errors to visitors;
- no complex offline persistence is required in v1;
- v2 may add a small retry queue if useful.

---

## 14. Backend responsibilities

The Django backend should:

- accept event batches from the static site;
- validate payloads;
- reject malformed or excessive events;
- apply rate limits;
- avoid storing raw IP addresses;
- optionally use transient IP-level handling for rate limiting/security without storing IP in analytics tables;
- persist events to PostgreSQL;
- preserve event sequence information for pathway analysis;
- compute provisional `human_likelihood` at ingest;
- expose private admin/HTMX dashboard views;
- expose a read-only public-safe summary endpoint for GitHub Actions;
- support export for statistical analysis.

### 14.1 Public browser ingest endpoint security

The browser ingest endpoint is public. It cannot rely on a client-side secret because any browser-visible token can be copied.

Protection strategy for v1:

- **Origin locking**: reject requests whose `Origin` header does not match `https://storyfutures.github.io`.
- **Referrer check**: optionally check `Referer` as a secondary signal.
- **Rate limiting**: apply per-IP rate limits at Nginx or Django middleware level without storing IP in analytics tables.
- **Payload size limit**: reject payloads above a defined maximum, e.g. 64 KB.
- **Event count limit**: reject batches containing more than a defined maximum number of events, e.g. 50 per batch.
- **Schema validation**: reject unknown, malformed, or internally inconsistent payloads.
- **Deduplication**: use session ID + event sequence + timestamp window to avoid duplicate processing.
- **Suspicion scoring**: flag rather than trust suspicious sessions.

Note: `Origin`/`Referer` headers can be spoofed by a determined attacker, but combined with rate limiting, strict schema validation, and bot/suspicion scoring this is a proportionate v1 defence for a low-value analytics target.

### 14.2 Public-safe summary endpoint security

The GitHub Actions summary endpoint is different from the browser ingest endpoint.

Recommended v1 model:

- bearer-token protected;
- read-only;
- aggregate-only;
- suppression already applied before response;
- rate-limited;
- access logged;
- no raw events;
- no session IDs;
- no individual paths;
- no unsuppressed small cells.

### 14.3 Metadata JSONField discipline

If `metadata` is used, it must not become an unstructured dumping ground.

Rules:

- Document allowed keys per event type.
- Validate event-type-specific metadata.
- Avoid storing free text unless explicitly required.
- Avoid storing raw URLs, raw search strings containing personal information, or high-cardinality device data.
- Keep metadata small.

---

## 15. Candidate Django models

### 15.1 Multi-site note

Do not include a `site` field in v1 models. The system supports only the Multisensory Hub initially. Add multi-tenancy later if genuinely needed.

### 15.2 AnalyticsSession

Fields may include:

- `session_id`
- `created_at`
- `last_seen_at`
- `landing_path`
- `referrer_domain`
- `device_class`
- `browser_family` if needed
- `is_suspicious`
- `human_likelihood`: `human_likely`, `bot_likely`, `unknown`

### 15.3 AnalyticsEvent

Fields may include:

- `created_at`
- `received_at`
- `timestamp_client`
- `session_id`
- `event_sequence`
- `page_path`
- `page_title`
- `event_type`
- `block_id`
- `block_version_id`
- `content_hash`
- `topic`
- `concept`
- `content_type`
- `previous_page_path`
- `previous_block_id`
- `seconds_since_previous_event`
- `seconds_visible`
- `intersection_ratio`
- `scroll_depth`
- `target_path`
- `target_domain`
- `metadata`

Indexes should support:

- `session_id`, `event_sequence`
- `page_path`
- `block_id`
- `block_version_id`
- `content_hash`
- `topic`
- `concept`
- `event_type`
- `created_at`

`section_id` is deliberately omitted from v1. Larger sections should be represented as tracked blocks with `content_type="section"`. This avoids maintaining two overlapping identifiers (`section_id` and `block_id`) for the same analytic unit.

### 15.4 TrackedBlock as manifest/build artefact

Avoid relying primarily on a hand-maintained Django `TrackedBlock` table for page structure. It will drift as the Docusaurus site evolves.

Preferred v1 model:

- Docusaurus/MDX source contains `TrackedBlock` components.
- Build-time manifest records structural metadata.
- Django ingests or references the manifest.
- Runtime events include `block_id`, `block_version_id`, and `content_hash`.
- The dashboard uses the manifest for layout/order and the events/aggregates for metrics.

Django may store a copy of the manifest for querying, but Git remains the source of truth for the report structure.

### 15.5 Aggregate summary tables

Use scheduled aggregate tables for v1 rather than PostgreSQL materialised views.

Reason:

- Django does not manage PostgreSQL materialised views natively.
- PostgreSQL materialised views do not auto-refresh.
- Scheduled aggregate tables are easier to manage in Django migrations and management commands.

Suggested tables:

- `DailyBlockSummary`
- `DailyTopicSummary`
- `DailyConceptSummary`
- `DailyTransitionSummary`

`DailyTransitionSummary` computation rule:

- group events by `session_id`;
- order events within each session by `event_sequence`, falling back to `timestamp_client` and then `received_at` only if needed;
- construct consecutive event pairs where both events are meaningful navigation/exposure states;
- produce page-to-page transitions from consecutive changes in `page_path`;
- produce block-to-block transitions from consecutive changes in `block_id`;
- ignore repeated heartbeat events for the same block unless they mark a meaningful continuation summary;
- aggregate by date, source page/block/topic/concept, destination page/block/topic/concept, and `human_likelihood`;
- suppress low-count edges before any public or partner-facing export.

Recommended simplification for v1:

- compute page-to-page transitions first;
- add block/concept-to-block/concept transition summaries once the `TrackedBlock` exposure pipeline is stable.

Aggregation can be refreshed via:

```text
python manage.py refresh_concept_analytics_summaries
```

Scheduled using:

- system cron;
- Celery Beat;
- Django-Q;
- a hosting-platform scheduled job.

Materialised views may be considered later if aggregate table performance becomes a bottleneck.

---

## 16. Retention and versioning

### 16.1 Retention distinction

Do not treat all analytics data the same.

Recommended retention model:

- raw/near-raw event rows: short-to-medium retention;
- individual ordered event trails: shortest retention and restricted access;
- aggregate summaries: long-term retention;
- tracked-block manifests: indefinite retention;
- Git commit/version mappings: indefinite retention;
- public-safe summary JSON in GitHub: overwrite latest by default, with selected snapshots only when useful.

### 16.2 Recommended v1 retention

Suggested defaults:

- Raw event rows: 6 months.
- Raw/debug individual session trails: 30–90 days.
- Aggregate summaries: indefinite or until no longer useful.
- Public-safe GitHub summary files: overwrite `latest`; keep selected snapshots for releases.
- Manifests/version mappings: indefinite.

Rationale:

- Raw event trails are more sensitive than aggregate summaries.
- Aggregate summaries and manifests are what support long-term research/insight.
- Content changes are already captured in Git, so analytics should preserve mappings to commits and content hashes.

---

## 17. Heat-map dashboard

A major desired output is a **document heat map**: the whole report laid out visually, with small representations of pages/sections and engagement intensity overlaid.

This should help the team and industry partners see which parts of the Hub attract active viewport exposure, interaction, and follow-on engagement.

### 17.1 Literature grounding

The idea is related to prior work on:

- long-document/webpage heat maps, especially **WebpageMap**, which visualised navigation/reading behaviour within large HTML pages such as technical documentation;
- **Viewport-DOM based heat maps**, where interaction and viewport data are mapped back to DOM elements rather than raw screen co-ordinates;
- **viewport time** work, where attention is modelled at the level of sub-document HTML elements rather than whole pages;
- adjacent work on word attention heat maps and selection heat maps, although this project will focus on meaningful content blocks rather than every word.

### 17.2 Key design decision

The heat map should be **DOM/block anchored**, not pixel/screenshot anchored.

Raw x/y co-ordinates should not be the primary data model because they break across devices, responsive layouts, font-size changes, browser widths, dynamic content, and Docusaurus route changes.

### 17.3 v1 heat map

```text
Mini-page card view
+ each report page represented as a compact vertical card
+ tracked blocks shown inside the card in document order
+ block rectangles shaded by selected metric
```

The v1 heat map should feel like the whole document is splayed out in miniature, but it should be generated from the document structure and tracked block metadata rather than screenshots.

### 17.4 v2 heat map

```text
Mini page thumbnails
+ overlaid block-level engagement rectangles
+ still keyed by DOM block IDs, not raw visitor co-ordinates
```

### 17.5 Candidate heat-map modes

- unique sessions reached;
- total active viewport exposure;
- median active exposure per reached session;
- percentage of page visitors who reached the block;
- interaction density;
- downloads or external clicks after exposure;
- search-driven visits;
- bot-filtered versus all-traffic view.

Current decision:

- The dashboard should collect and support multiple heat metrics rather than committing to one.
- The heat map should include toggles/switches between metrics.

Recommended default view:

- Start with `unique sessions reached`, because it is less likely than total dwell to be dominated by a few long sessions.
- Provide `active viewport exposure` as the second major toggle.

Important:

- The heat map should be based on aggregate exposure data, not session replay.
- Labels should say `active viewport exposure`, `sections reached`, `concept exposure`, or `interaction density`.
- Avoid labels such as `what people read`, `what people liked`, or `what people understood`.

---

## 18. Dashboard and analysis

Current decision:

- A dashboard is desired from the start.
- HTMX is preferred.
- The first dashboard should be **private/internal and delayed** rather than public from the start.
- A public-facing aggregate dashboard inside the site remains an appealing later option.
- First priority chart: heat map.

Recommended default:

- Build a **private/internal HTMX dashboard first**.
- Use permissions to control access.
- Consider a specific permission such as:

```text
can_view_concept_analytics_dashboard
```

- Later create a **public aggregate dashboard** if the data and framing are appropriate.
- Public dashboards should use delayed, aggregated, suppressed, and carefully labelled metrics.

Initial dashboard components:

1. Mini-page-card report heat map by tracked block.
2. Heat-map metric toggles.
3. Top concepts by active viewport exposure.
4. Top pages/sections by unique sessions.
5. High-traffic but low-engagement sections.
6. Low-traffic but high-engagement sections.
7. Downloads and external links following concept exposure.
8. Bot/suspicious traffic summary.
9. Concept co-exposure view.
10. Navigation/pathway view through the document.
11. Before/after content change comparison.
12. Before/after Git commit comparison.

### 18.1 Public dashboard suppression

Recommended defaults:

- Suppress block/topic/pathway cells with fewer than **10 unique sessions** in public or partner-facing summaries.
- Suppress block/topic/pathway cells with fewer than **5 unique sessions** in private/internal aggregate dashboards unless explicitly viewed by an administrator for debugging.
- Apply suppression to pathway/Sankey nodes and edges.
- For small datasets, report broader topic-level summaries rather than fine-grained block-level summaries.

Public-safe endpoint rule:

```text
The Django public summary endpoint should only return data that would already be acceptable to commit into the public GitHub repository.
```

### 18.2 GitHub Actions smoke tests

Before committing a downloaded analytics summary, the GitHub Actions workflow should check that:

- the Django endpoint returned HTTP 200;
- the response is valid JSON;
- the JSON includes expected fields such as `generated_at`, `date_range`, `suppression`, and `contains_raw_events`;
- `contains_raw_events` is `false`;
- a minimum expected heat-map structure is present;
- the file is not suspiciously small or empty;
- the summary date range is not unexpectedly stale;
- suppression metadata is present.

If validation fails:

- do not commit a replacement file;
- keep the previous valid static summary;
- fail the workflow visibly;
- optionally notify maintainers.

---

## 19. Navigation, pathways, and concept co-exposure

Current decision:

- Concept co-exposure is desirable.
- The tracker should record transitions at **both levels**:
  - page-to-page transitions;
  - block/concept-to-block/concept transitions.
- It would be useful to see how people move through the document:
  - where they came from within the report;
  - which page, block, topic, or concept they visited next;
  - whether particular concepts act as gateways to other topics.

Key analysis questions:

- Which concepts are commonly encountered in the same sessions?
- Which topic pairs are commonly co-exposed?
- Which blocks/pages tend to be entry points?
- Which blocks/pages tend to be exit points?
- Where do people go after viewing a given topic or concept?
- Which pathways lead to downloads or external clicks?
- Are there common paths through the Hub that differ from the intended document structure?

Potential visualisations:

1. Page-to-page pathway view.
2. Block/concept-to-block/concept pathway view.
3. Concept co-exposure matrix.
4. Topic co-exposure network.
5. Sankey/alluvial flow between pages or topics.
6. “After viewing this block/concept, people next went to…” table.
7. Entry and exit block/page summary.
8. Pathways leading to downloads or external links.
9. Simplified topic-level Sankey to avoid noisy block-level paths.

Dashboard caution:

- Block/concept-level pathways may be noisy, especially in long documents with many tracked blocks.
- The dashboard should default to page/topic-level pathways, with block-level views available for deeper analysis.
- Aggregate block-level transitions into topic-level flows where useful.

Privacy note:

- Pathway analysis should remain aggregate.
- Avoid exposing individual session trails in ordinary dashboards.
- For debugging, individual event trails may be useful but should be access-limited and short-retention only.

---

## 20. Bot and human-likelihood handling

Need to know whether it is likely a human looking at the document, without using invasive fingerprinting or CAPTCHA for ordinary visitors.

Recommended classification:

```text
human_likely
bot_likely
unknown
```

Recommended signals:

- Exclude obvious bots using user-agent checks.
- Rate-limit impossible event volumes.
- Flag sessions with no scroll/click/pointer/key/touch activity.
- Flag sessions with extremely fast full-page traversal.
- Flag sessions with very regular mechanical timing.
- Flag implausible viewport/event combinations.

Do not try to prove that a visitor is human. Instead, report analyses with and without suspicious sessions.

`human_likelihood` should be computed provisionally at ingest time using the signals available in the request and payload. It can be recomputed retrospectively via a management command as detection rules improve.

Default public view:

```text
human_likely only, delayed, suppressed, aggregate
```

Recommended dashboard filters:

```text
human_likely only
human_likely + unknown
all traffic
```

---

## 21. Event sending strategy

Current decision:

- The tracker should be loaded globally.
- Event sending should be batched, not one request per interaction.
- Offline/failed-event retries are not required for v1.

Recommended default:

- Load the tracker globally.
- Use `fetch()` for regular heartbeat batches.
- Use `sendBeacon()` for final flushes where possible.
- Send events in near-real-time batches every 15 seconds rather than literally every event instantly.
- On page unload/visibility hidden, flush any queued events.
- Keep a very small in-memory queue.
- Do not implement complex offline persistence in v1.
- Optionally use `localStorage` for a short retry queue in v2.

---

## 22. Literature-informed design notes

This project is closely related to prior work on implicit feedback, viewport time, viewability, and digital attention measurement.

Key takeaways from the literature:

- Dwell time is useful but ambiguous. Longer time can indicate interest, difficulty, confusion, distraction, or an idle tab.
- Page-level dwell time is too coarse for a rich interactive report.
- Viewport time is a better fit: measure how long specific page components are visible on screen.
- Sub-document attention can be modelled at the level of HTML elements such as paragraphs, images, figures, cards, and sections.
- Visibility should be weighted by how much of the element is visible and, optionally, by how much screen real estate it occupies.
- A heartbeat interval of around 15 seconds has precedent in large-scale web reading analytics.
- The system should distinguish between opportunity-to-see and stronger claims about attention, reading, comprehension, or usefulness.
- Reports should use relative/within-session measures as well as raw seconds, because people read and skim at different speeds.
- Concept-level exposure should be combined with interaction signals such as downloads, media plays, section opens, and internal search terms.

Terminology to use:

- `viewport exposure`
- `active visible time`
- `concept exposure`
- `opportunity to read`
- `engagement proxy`

Terminology to avoid unless separately validated:

- `read`
- `understood`
- `liked`
- `learned`
- `paid attention`

Recommended default measurement rules:

- use `IntersectionObserver` for tagged blocks/components;
- count only when the tab is visible;
- sample or heartbeat every 10–15 seconds;
- use 50% visible for at least 3 seconds as an initial concept exposure threshold;
- store cumulative visible seconds per concept, section, and page;
- store maximum scroll depth per page/session;
- store relative exposure share per session, not just raw seconds;
- treat large blocks differently from small inline keywords;
- cap or flag very long idle sessions;
- report medians and distributions, not only means.

---

## 23. V1 pilot readiness and critical implementation safeguards

The proposed v1 architecture is ready for a pilot if the following are implemented before any public/partner-facing reporting:

- `concept_analytics` app scaffolded as the single Django app;
- CORS and cross-origin transport strategy implemented;
- CSRF-exempt ingest endpoint with strict validation;
- public browser ingest endpoint protected by origin checks, rate limiting, payload limits, and schema validation;
- GitHub Actions summary endpoint protected by bearer token;
- public-safe aggregate-only JSON;
- suppression logic;
- stable tracked-block manifest;
- content hashes and block version IDs;
- smoke-tested GitHub Actions pull;
- overwrite-only `latest` summary files;
- private HTMX dashboard for instrumentation checking;
- static delayed heat map for any visitor-facing reporting.

OIDC should be considered a v2 hardening task unless institutional security review requires it before launch.

---

## 24. Version plan

### v0 – design and taxonomy

- create reusable Django app skeleton for `concept_analytics`;
- create minimal development host project;
- define topic taxonomy;
- define concept vocabulary;
- decide tagging approach;
- decide event schema;
- confirm RHUL/StoryFutures notice + opt-out wording;
- define stable `block_id`s;
- define tracked-block manifest schema;
- define content hashing approach;
- define CORS/transport strategy;
- define endpoint validation and rate-limiting rules;
- decide internal dashboard permissions.

### v1 – basic event collection

- installable Django `concept_analytics` app;
- minimal development host project;
- CORS-enabled ingest endpoint;
- event model;
- session model;
- tracked block manifest import/reference;
- React `AnalyticsProvider`;
- React `TrackedBlock`;
- route-aware page views;
- downloads and external links;
- ordered event sequences;
- page-to-page transitions;
- Django admin/private diagnostic display.

### v2 – active dwell-time tracking

- central `IntersectionObserver`;
- visibility-aware heartbeat;
- idle detection;
- batched event sending;
- block/concept-to-block/concept transitions;
- basic concept exposure summaries;
- content-hash-aware aggregation.

### v3 – private HTMX dashboard and exports

- mini-page-card heat map;
- metric toggles;
- topic ranking dashboard;
- concept ranking dashboard;
- bot-filtered views;
- CSV/JSON exports;
- daily/weekly aggregate summaries;
- before/after content-change comparisons.

### v4 – research/insight layer

- co-exposure analysis;
- topic/concept pathway analysis;
- longitudinal changes in interest;
- referrer/topic interaction;
- device differences;
- link between concept exposure and downstream actions;
- possible public aggregate dashboard.

Note: v4 requires a meaningful data volume to be analytically useful. Do not overbuild v4 before v1–v3 have generated enough reliable data.

---

## 25. Initial assumption set

Until changed, assume:

- non-Google products only;
- one installable reusable Django app: `concept_analytics`;
- develop first in a minimal Django host project;
- later install into the established CoSTAR Tools project at `costartools.uk`;
- Django + PostgreSQL backend;
- existing Hetzner-hosted infrastructure;
- Docusaurus static frontend on GitHub Pages;
- React/Docusaurus tracking architecture, not a generic page-load script;
- no named-user tracking;
- no returning visitor tracking;
- no raw IP storage;
- cookie-free `sessionStorage` session ID;
- notice + opt-out approved by RHUL/StoryFutures for this setup;
- localStorage opt-out key checked before session creation;
- referrer domain only;
- target path/domain only, not full external URLs;
- no session replay;
- no raw mouse tracking;
- aggregate concept/topic analytics only;
- manual tagging of meaningful sections/components rather than every keyword occurrence;
- both large sections and smaller components can be tracked;
- stable `block_id`s are required;
- content hashes are required for changed text/content;
- GitHub repository can hold manifests and public-safe aggregate summaries;
- GitHub repository must not hold raw behavioural event data;
- GitHub Actions pulls public-safe summaries from Django;
- Django does not push to GitHub in v1;
- heartbeat-based active dwell tracking;
- 50% visibility for 3 seconds as initial exposure rule;
- 15-second heartbeat;
- idle detection after 60 seconds without activity;
- both page-level and block/concept-level transitions;
- mini-page-card heat map as v1 dashboard centrepiece;
- private delayed HTMX dashboard first;
- public aggregate dashboard only later if appropriate;
- raw event retention around 6 months;
- aggregate summaries and manifests retained longer;
- open-source/package later, not from day one.
