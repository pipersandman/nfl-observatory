# Analytics

What the site measures, and the rules every event follows. Decisions D18
(Cloudflare Web Analytics for page views) and D21 (PostHog: cookieless, events
only, no session replay). Built in #165 and #179.

## Tools

| Tool | What | Where it's set up |
|---|---|---|
| Cloudflare Web Analytics | Page views and visits (the number of record, D18). Cookieless. History copied weekly to private R2 (#164, `analytics-export.yml`) | Beacon in the shared snippet, `scripts/site_analytics.py` |
| PostHog (US cloud) | The named events below, plus a page view per page load | Script in the shared snippet; settings in `frontend/js/track.js` |

The shared snippet is on every page: `build_static.py` puts it in every pre-built
page, and `scripts/sync_nav.py` writes it into `frontend/index.html` and
`frontend/gameday/index.html` (`check.py` "Menus match" fails if they drift).

**Coverage note:** until #179 (this change), the Cloudflare beacon was only on the
home page. The Cloudflare history in R2 (`internal/analytics/cloudflare-web/`)
covers the home page only up to the deploy of #165/#179.

## Rules

1. **Every event goes through `track(name, props)`** (`frontend/js/track.js`), so the
   tool can be swapped later. Never call `posthog` directly.
2. **No personal data.** No names, emails, typed text or IP addresses kept by us.
   Properties are ids the site already shows (crew slug, team code, game id), labels
   and numbers.
3. **Cookieless:** `persistence: 'memory'`. Nothing in cookies, local storage or
   session storage. Returning visitors aren't recognized.
4. **Events only:** `autocapture: false`, `disable_session_recording: true`, heatmaps,
   rage and dead clicks, performance, error capture, surveys and feature flags off.
   PostHog project settings (Ty): discard client IP data on; session replay,
   autocapture and heatmaps off.
5. **Do Not Track:** PostHog sends nothing when it's on (`respect_dnt: true`).
6. **Names:** `object_action`, lower case. A new event is added to the table below in
   the same pull request; a test fails on any `track('…')` name not listed here.
7. **Localhost:** nothing is sent; `track()` logs `[track] <name> <props>` to the
   console instead.
8. **PostHog version:** pinned (`POSTHOG_VERSION` in `scripts/site_analytics.py`) with
   an integrity hash, using the `array.no-external.js` build, which never loads
   other scripts. A version is at least two weeks old when chosen.

## Events

| Event | Properties | Fires when | Where |
|---|---|---|---|
| `section_view` | `section` (`season`, `previews`, `referees`, `teams`, `trends`) | A home section is half visible, or fills half the screen; once per page view | `track.js` |
| `menu_click` | `label` (menu item), `from` (page path) | A site menu item is clicked | `track.js` |
| `see_all_click` | `section` | A "See all →" link is clicked | `track.js` |
| `outbound_click` | `destination` (`x`, `reddit`, `other`) | A link to another site is clicked | `track.js` |
| `referee_modal_open` | `crew` (slug) | A crew chief profile opens | `app.js` `openRefereeModal` |
| `team_open` | `team` (code) | A team profile opens | `app.js` `openTeamModal` |
| `preview_view` | `season`, `week`, `game_id` | A game preview opens | `app.js` `openPreviewModal` |
| `explainer_open` | `metric` (explainer key) | A "?" or "How … works" explainer opens | `app.js` `openExplainer` |
| `chart_interact` | `chart` (`seasonPenaltiesChart`, `seasonYardsChart`, `crew-style-map`, `week-of-season`, `quarter-penalties`) | A chart click opens a crew chief, or a chart's toggle or menu is used | `app.js` |
| `table_sort` | `table` (`gameday`), `column` (`flags`, `yards`) | A sort button is clicked | `gameday.js` |
| `gameday_view` | `seconds` | `/gameday/` is hidden or closed: the seconds it was visible since last shown (a visit's events add up to its time on the page) | `gameday.js` |

Opening a profile from a link (`/#crew=…`, `/#team=…`, `/#game=…`) also fires its
`_open` / `_view` event.

## Privacy text (not published yet)

Approved by Ty on 2026-10-31. It's kept off the site for now (Ty's decision, 2026-10-31). When it's added, it goes in `/guide/` as `<h2 id="privacy">Privacy</h2>`, with a **Privacy** footer link to `/guide/#privacy`.

> We count visits with Cloudflare Web Analytics and record a few anonymous events with PostHog (US): which sections, crew chiefs, teams and game previews are opened, and which charts and menus are used. Neither tool sets cookies or stores anything in your browser, and we don't record sessions, keystrokes or anything you type. We don't collect names or email addresses, and PostHog is set to discard IP addresses. Your browser's Do Not Track setting is respected.

**Open question before publishing: Do Not Track.** PostHog honors it (`respect_dnt: true`). The Cloudflare Web Analytics beacon isn't known to, so it still counts those page views. Before publishing, either:
- (a) change the last sentence to "PostHog respects your browser's Do Not Track setting."; or
- (b) skip the Cloudflare beacon when Do Not Track is on (this lowers the page-view count of record a little).
