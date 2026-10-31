# NFL Observatory: Combined Build Plan Addendum

Oct 30, 2026 · Ty

## How to use this plan

This addendum adds five workstreams to the V2 build (`docs/V2_BUILD_PLAN.md`). It does not replace the V2 sequence: the V2.0a issues (#119 to #131) stay next, and these workstreams slot around them as described in the last section. Its decisions are numbered D21 onward and logged in section 33 of the V2 plan.

**Conventions every item follows**

- Every change goes through the tracked process: `git switch main`, `git pull`, a branch, a PR that says `Closes #N`, Ty merges.
- Each workstream becomes GitHub issues labeled `step` plus its own label. Each issue lists every step for Claude Code and ends with checks Ty can run himself.
- One small-sample rule everywhere (plan decision D13, conflict C17): show the number with its sample, plus a visible "small sample" label below 8 games. The threshold and label are set in #127 (V2.0a step 3).
- No hard-coded years, windows or values in any label text.
- Charts of penalties per game are always sorted most penalties first.
- Red means more penalties and green means fewer. Nothing else on the site may reuse red or green for a different meaning.
- Proprietary rule: methods, model parameters and backtest detail stay private. Only outputs and plain-language definitions are public.
- New metrics get an entry in `docs/METRICS.md` before they ship. The entry format (plan section 6) gains two fields: **Version** (the metric's version, bumped on any change to its definition or calculation) and **Owner** (who answers for it). That change is its own issue.

**The five workstreams**

| # | Workstream | What it delivers | Size |
| --- | --- | --- | --- |
| 1 | Site performance and data exposure | Faster pages, caching, no model internals in public files | Small, ready now |
| 2 | Analytics and measurement | Event tracking, campaign attribution, search data history | Small to medium |
| 3 | Sources and reconciliation | A source registry, canonical official IDs, weekly number checks | Medium |
| 4 | ESPN live layer | Richer gameday capture, raw archive, live-vs-official checks | Medium |
| 5 | Referee grade | A measured, validated grade of crew behavior | Large |

## Workstream 1: Site performance and data exposure

Five issues are drafted as files (`1-compression.md` to `5-model-internals.md`, for `create_issues.ps1`, label `site-perf`). **They are not on GitHub yet:** on 30 Oct 2026 the repository had no `site-perf` label and no issues using it. A HAR capture on 30 Oct 2026 found each home page load sends about 93 requests and 4.2 MB before compression, with JSON served uncompressed and the model's parameters in public files.

| Issue | Change | Evidence from the capture | Done when |
| --- | --- | --- | --- |
| Site perf 1 | Gzip JSON, CSS, JS, HTML, SVG in `frontend/.htaccess` | MIA.json: 49.7 KB sent as 50.4 KB | curl shows `content-encoding: gzip`; security headers still present |
| Site perf 2 | Cache rules: 1 year for versioned CSS/JS, 5 minutes for data, none for HTML; parallel startup fetches | Every file `no-cache`, about 45 revalidation round trips per visit | CSS/JS come from disk cache on repeat visits |
| Site perf 3 | **Minimal now:** referee cards read from `referees.json` instead of preloading all 28 profiles. **Full version in V2.1:** load all data on demand (the Astro rebuild changes how pages load data) | 43 JSON files (1.74 MB) per load, all 28 referee profiles preloaded | Now: no `referee/<slug>.json` requests before a card is opened. V2.1: 10 or fewer JSON requests before scrolling |
| Site perf 4 | Self-host team logos at 2x display size | 32 ESPN PNGs, about 1.7 MB, hotlinked | No requests to a.espncdn.com, logos under 200 KB |
| Site perf 5 | Remove model internals from public JSON; keep full copies outside the deploy | Preview files publish season weights, dispersion and per-type factors; scorecard files publish the same factors | Every field Ty marks "remove" in the table below is absent from every public file |

**Order.** 1, then 2 (both edit `.htaccess`), then 3 (minimal). Issues 4 and 5 run any time; 5 waits for decision D27.

**Stop points built into the issues.** Issue 1 stops if security headers live in cPanel rather than the repo. Issue 2 stops if the `?v=` stamp is typed by hand. Issue 5 stops if the repo is still public, then waits for Ty to decide each field below.

### Site perf 5: what it would remove (for Ty to decide, field by field)

Ty's decision of 2026-10-29 on P5 to P7 (`docs/audits/metric-conflicts-2026-10-28.md`, "Published but not displayed") keeps `scorecard/live/`, `scorecard/backtest/` and `history/snapshots/` in the deploy as the evidence behind the scorecard. Site perf 5 as first written ("scorecard publishes backtests") would undo that, so each file and field is listed here.

- **Model internal:** a parameter or intermediate value of the projection model that no page shows.
- **Published evidence:** a published projection or record that the scorecard is graded against, or that can't be made again later.
- **Shown on the page:** read by `app.js` today; removing it changes the page.

Checked on 30 Oct 2026 against `frontend/js/app.js`, `gameday.js`, `livestrip.js`, `scripts/build_static.py` and the gameday worker.

**`previews/<season>-week-NN.json`** (the upcoming game previews; P4 kept the past weeks' files)

| Field | Shown on the page? | Marked | Ty's decision |
| --- | --- | --- | --- |
| `model.seasonWeights` (weight per season, e.g. 1.0 / 0.6 / 0.3) | No (the footnote says only "weighted toward <season>") | Model internal | |
| `model.dispersion` (negative binomial dispersion) | No | Model internal | |
| `model.version` | No | Model internal | |
| `model.regularSeasonOnly` | No | Model internal | |
| `games[].byType[].factors` (`homeCommit`, `awayCommit`, `homeDraw`, `awayDraw`, `crew`) | No | Model internal | |
| `games[].teams.home/away.gamesInModel` | No | Model internal | |
| `model.seasons` | Yes (footnote) | Shown on the page | Keep |
| `model.leagueAveragePerGame` | Yes; `scorecard.py` also reads it as a fallback (P4) | Shown on the page | Keep |
| `contextReference` | Yes (game context) | Shown on the page | Keep |
| `games[].projection.drivers` | Yes (drivers chart) | Shown on the page | Keep |
| `games[].crew.gamesInModel` | Yes (tilts footnote) | Shown on the page | Keep |
| `games[].projection.*` (total, ranges, yards, `probOver`, `overThreshold`, `byQuarter`, `vsLeaguePct`) and `byType[]` (`total`, `leagueTotal`, `yardsEach`) | Yes | Shown on the page | Keep |

**`scorecard/live/<season>-week-NN.json`** (projections frozen at kickoff; P5: keep and deploy)

| Field | Shown on the page? | Marked | Ty's decision |
| --- | --- | --- | --- |
| `byTypeFactors` (the same five factors per type) | No | Model internal | |
| `modelVersion`, `crewKnown`, `frozenAt`, `source` | No | Published evidence (what was projected, by which version, and when) | |
| `total`, `home_proj`, `away_proj`, `range`, `homeRange`, `awayRange`, `yards`, `byType`, `byTypeTeams`, `byQuarter`, `probOver`, `overThreshold`, `leagueAverage`, `drivers`, `context`, `crew` | No page reads this file; the same values were shown in the preview before kickoff | Published evidence | |

**`scorecard/backtest/<season>-week-NN.json`** (projections rebuilt afterward; P6: keep and deploy)

| Field | Shown on the page? | Marked | Ty's decision |
| --- | --- | --- | --- |
| `byTypeFactors` | No | Model internal | |
| Every other field (same fields as `scorecard/live/`) | No page reads this file | Published evidence (rebuilt, labeled "backtest") | |

**Other files**

| File or field | Shown on the page? | Marked | Ty's decision |
| --- | --- | --- | --- |
| `wp_tables.json` (win-probability lookup table) | No page; the gameday worker fetches it from the public URL | Model internal (removing it means the worker needs another source first) | |
| `history/snapshots/` (the league after each week; P7) | No | Published evidence (can't be rebuilt "as it stood that week") | |
| `history/games/` and `history/index.json` (the ledger: each game's prediction, outcome and grade) | Yes (ledger) | Shown on the page | Keep |
| `scorecard/public.json` (scorecard summary) | Yes (scorecard) | Shown on the page | Keep |

**Why it matters for the grade.** Workstream 5 will produce the most valuable numbers on the site. Issue 5 sets the rule that keeps model parameters private before the grade exists.

## Workstream 2: Analytics and measurement

Today the site only knows page views (Cloudflare Web Analytics) and Google search clicks (Search Console). This workstream adds what visitors do on the page, where they came from, and a history of search data, without cookies or a consent banner.

**Phase A: Choose the tool (decision D21)**

1. Recommended: PostHog in cookieless mode (`persistence: 'memory'`). It covers events, funnels, paths, heatmaps and session replay now, and V2 product analytics later (searches run, visualizations saved, feature requests). Cost of cookieless: returning visitors are not recognized.
2. Alternative: Umami (free if self-hosted) or Plausible (paid). Cleaner, events and campaigns only, no replay.
3. Rejected: GA4. It needs cookies and a consent banner, which conflicts with the trust-first design.

Choosing PostHog would replace plan decision D18 (keep Cloudflare Web Analytics, Plausible optional later); Cloudflare Web Analytics can stay alongside it for page views.

**Phase B: Install and instrument**

1. Add the tool's script to every HTML page (home, `crew/*`, `team/*`, `assignments/`, `dataset/`, `guide/`, `gameday/`), and add its host to the content security policy (`script-src` and `connect-src`).
2. Add one `track(name, props)` helper in `app.js`. Every event goes through it, so the tool can be swapped later.
3. Fire these events, names in `object_action` form:

| Event | Properties | What it answers |
| --- | --- | --- |
| `referee_modal_open` | crew slug | Who people look up, and whether it spikes when assignments post |
| `explainer_open` | metric name | Which metrics confuse people (input to V2.0a labels) |
| `preview_view` | season, week, game id | Interest in previews by matchup |
| `gameday_view` | seconds on page | Live tracker use during games |
| `chart_interact` | chart id | Which charts get used |
| `table_sort` | table id, column | What people sort by |
| `outbound_click` | destination (X, Reddit, other) | Traffic leaving to social |
| `team_open` | team code | Team page interest |
| `search_submitted` (V2) | query text | Demand for plain-English search |
| `viz_saved`, `feature_requested` (V2) | id, text | Product use and requests |

4. The team view opens as `#team=MIA` on the home page, which page-view tools do not count as a page. Link to the real `/team/<code>/` and `/crew/<slug>/` pages wherever possible, and fire `team_open` when the in-page view opens.
5. Update the privacy page: what is collected, that it is cookieless, and the tool used.

**Phase C: Campaign tagging**

1. Every link posted to X or Reddit carries `utm_source`, `utm_medium=social`, `utm_campaign` (e.g. `wk9-preview`) and `utm_content` (e.g. `r-eagles`).
2. Keep a short UTM convention note in `docs/` so every post uses the same names.

**Phase D: Search and live data**

1. Add a weekly GitHub Actions step that pulls Search Console query and page data through its API and stores it (the UI keeps only 16 months).
2. Register the site in Bing Webmaster Tools (covers Bing and DuckDuckGo).
3. Add Workers Analytics Engine logging to `nflobs-gameday`: one data point per request, so live usage curves during games are visible.
4. Add Sentry's free tier to catch JavaScript errors (a failed data load on a phone is invisible to every other tool).

**Phase E: Own the data**

1. Weekly export of events from the analytics tool's API to private storage (R2 now, the V2 database later).
2. Join to the football calendar: lookups per crew chief before kickoff, traffic by matchup, traffic after assignments post. This is a demand signal and a proof-of-audience number for media and bettors.

**Done when:** events appear in the tool within a day of deploy; a UTM-tagged test link shows its campaign; the first weekly Search Console file exists in storage; the gameday worker shows request counts for a game window.

## Workstream 3: Sources and reconciliation

Nearly every referee-stats site repackages the same few primary sources, so the Observatory ingests the primaries and uses the repackagers only as benchmarks. For 2020 onward, NFLPenalties is built on the same nflfastR data as the Observatory (its footer says so, and its yardline column is nflfastR's `yardline_100`), so differences between the two are definitions, not data.

**Source registry** (lives in `docs/SOURCES.md`, one row per source, reviewed each season)

| Source | Data | Role | Access | Use status |
| --- | --- | --- | --- | --- |
| nflverse (nflfastR, via nflreadpy) | Play-by-play, officials (all 7 per game), schedules with spread and total lines | Primary, official record | Public files | In use; check license terms and attribution |
| Football Zebras | Assignments days before games, crew rosters with tenure | Primary for assignments | Public pages (check for a `wp-json` feed) | In use for assignments |
| ESPN game summary feed | Live flags, full crew, win/cover/over probability, attendance, wall clock | Live layer | Undocumented feed | In use by gameday worker; not licensed for commercial use |
| NFL Football Operations | Rule changes, officiating roster, game books | Primary for rules and crews | Public pages and PDFs | Planned |
| Pro Football Reference | Referee seasons from 1999, home win % | Benchmark | Public pages; automated access restricted | Manual spot checks only |
| NFLPenalties | Accepted, declined, offsetting, player and position views | Benchmark | Server-rendered HTML, no feed | Manual spot checks only |
| Betting sites (Sharp, Action, SportsBettingDime, Covers, RotoWire) | Referee ATS and over/under trends | Benchmark | Public pages | Replicate from nflverse lines, never copy |

**Phase A: Canonical IDs for officials**

1. Create `config/officials.csv`: one row per official with a stable id, display name, and every alias seen (nflverse, ESPN, Football Zebras, NFLPenalties). Example: Ron Torbert with alias Ronald Torbert.
2. Replace `NAME_FIXES` in the pipeline with a lookup against this file.
3. The pipeline fails loudly when it meets a name with no match, rather than creating a new official.

**Phase B: Definitions**

1. Write one definitions file (`docs/DEFINITIONS.md`) for every count the site shows. Core terms: accepted (enforced), declined, offsetting, dismissed (declined plus offsetting, NFLPenalties' term), total flags (all three), no-play.
2. Every metric in `docs/METRICS.md` names which of these it counts.

**Phase C: Weekly reconciliation job**

1. After each week, compare per game: accepted, declined, offsetting, yards, per team. Sources: nflfastR (record) versus the ESPN capture from Workstream 4.
2. Write differences to a private report in `internal/reconciliation/`. Any game off by more than one flag gets a line explaining why (late data correction, definition, parse miss).
3. Monthly manual spot check of three crews against NFLPenalties and Pro Football Reference, logged in the same folder.

**Phase D: Replicate betting trends from our own data**

1. nflverse schedules already include `spread_line`, `total_line` and final scores. Compute each crew chief's against-the-spread and over/under records from these.
2. Small samples follow the D13/C17 rule: the record is shown with its games and a "small sample" label below 8 games. Records only, never leans or picks.

**Phase E: Public "how our numbers compare" page**

One page explaining why the Observatory, Pro Football Reference and NFLPenalties can show different numbers for the same crew (accepted versus total flags, history depth, name spellings). No competitor publishes this; it builds trust and earns citations.

**Phase F: Remaining source captures (HAR files Ty records)**

- [ ] ESPN game page for a game not yet played (are officials listed before kickoff?)
- [ ] ESPN game page for a past game with declined or offsetting flags (does the feed carry them?)
- [ ] NFL.com game center and an official game book PDF
- [ ] Football Zebras assignments post (is there a `wp-json` feed?)
- [ ] Action Network game page and SportsBettingDime referee tracker (whose odds feed?)

Capture logged out, in Chrome with Preserve log on and the Fetch/XHR filter, then export the HAR.

## Workstream 4: ESPN live layer

The gameday worker (`nflobs-gameday`) already reads ESPN's game summary feed, but keeps only a slice of it, and only in Cloudflare's cache while visitors are loading `/gameday/`. ESPN becomes the live layer during games; nflverse stays the record afterward; Workstream 3 reconciles them weekly.

**What the feed holds** (from the Panthers at Packers capture, game 401873023, 680 KB, the single feed behind every tab of ESPN's game page)

- All seven officials by position (that game: Scott Novak, Mike Morton, Brian Sakowski, Mark Stewart, John Jenkins, Don Willard, Tony Josselyn).
- A `penalty` object on each flagged play: type, yards, status, team. Totals matched the box score exactly (Carolina 5 for 41, Green Bay 6 for 45).
- Per play: home win probability, home cover probability, over probability, and a real-time `wallclock`.
- Attendance, venue, grass or turf, injuries, drives, DraftKings spread, total and moneylines.

**Parsing rules (traps found in the capture)**

1. Detect penalties by the `penalty` object, never by play type. An intentional grounding sat on a play typed "Fumble Recovery (Own)" and an unnecessary roughness on a "Rush".
2. The penalized player is tagged (`participants[].type = "penalized"`) only on standalone penalty plays. On live-ball fouls, parse the text `PENALTY on <TEAM>-<Player>`.
3. Unknown yet: whether declined and offsetting flags get a `penalty` object. Answered by the Workstream 3 capture of a game that had them; until then, the worker records the play text so they can be found later.

**Where the game record lives (decided here)**

The stored game record goes to R2 bucket `nflobs-raw`, beside the raw feed, one file per game:

| What | Key in `nflobs-raw` |
| --- | --- |
| Raw summary feed, exactly as received | `espn/summary/<season>/<week>/<game_id>.json` |
| Game record (the parsed fields in Phase A) | `espn/game/<season>/<week>/<game_id>.json` |

Both are written once, when the game is final, with a conditional write that never overwrites an existing file (the same rule as the raw capture, plan decision D20). A re-parse writes a new record version beside the old one rather than replacing it. Not Workers KV and not the edge cache: the record has to outlive the cache and be readable by the weekly reconciliation job in GitHub Actions.

**Phase A: Capture more per game**

1. The game record holds: officials (with canonical ids from Workstream 3), every penalty object with status and parsed player, per-play win/cover/over probability on penalty plays and the play before, wall clock per play, attendance, surface, and the betting line with its provider.
2. Keep the public `/live` response as it is now; the new fields go to storage, not to visitors (the Workstream 1 rule).

**Phase B: Raw archive**

1. **Cron Trigger for finished games.** Add a schedule to the worker (`[triggers] crons` in `worker/gameday/wrangler.toml`) that runs during game windows, finds games that reached `post` and have no archived file yet, and archives them. Archiving must not depend on someone having `/gameday/` open when a game ends. The schedule covers every day with games, Saturdays included late in the season.
2. **R2 bucket binding, `nflobs-raw` only.** The worker reaches R2 through a bucket binding in `wrangler.toml` (`[[r2_buckets]]` with `bucket_name = "nflobs-raw"`), not an API token, so it can read and write that one bucket and no other (the account also holds `drsplus-tiles`). No R2 credentials are stored in the worker.
3. This builds a private history of data nflverse does not carry: cover and over probability per play, real-time stamps, attendance.

**Phase C: Pre-game officials**

If the Workstream 3 capture shows ESPN lists officials before kickoff, add a check that compares ESPN's pre-game crew with Football Zebras' assignment and flags any mismatch to Ty.

**Phase D: Weekly live-versus-record check**

Feeds the Workstream 3 reconciliation job: for each game, ESPN flag counts and yards versus nflfastR. A difference of more than one flag is logged with a reason.

**Licensing guardrail.** The feed is undocumented and not licensed for commercial use. Use it for the live tracker and private research; do not republish ESPN's probabilities as Observatory numbers. Before any paid product, budget for a licensed feed (for example Sportradar) to replace it.

**Done when:** a finished game produces both files in `nflobs-raw` without anyone visiting `/gameday/`, the game record has all seven officials and every flag, the worker's only R2 access is the `nflobs-raw` binding, and the weekly check lists zero unexplained differences.

## Workstream 5: Referee grade

Referee grade: a measured, validated grade of crew behavior. Its design is kept private and will be added when the repository is private.

## Decisions and sequencing

Seven decisions gate this work, numbered as plan decisions D21 to D27 (section 33 of the V2 plan). D21, D24 and D27 are needed in the next two weeks. Decisions about the referee grade are listed by title only; their options are in the private plan.

| ID | Decision | Recommendation | Needed before |
| --- | --- | --- | --- |
| D21 | Analytics tool | PostHog in cookieless mode (would replace D18) | Workstream 2, Phase B |
| D22 | Referee grade: penalty classes | In the private plan | Grade foundations |
| D23 | Referee grade: name | In the private plan | Grade publishing |
| D24 | Model fields in public files | Ty decides each field in the Site perf 5 table; P5 to P7 evidence stays deployed unless he decides otherwise | Site perf 5 |
| D25 | Referee grade: which flags count | In the private plan | Grade foundations |
| D26 | Referee grade: when to publish | In the private plan | Grade publishing |
| D27 | Repository visibility | Private before Site perf 5 and any grade code is pushed | Site perf 5, grade foundations |

### Sequence

**Done:** #116 (shared windows and computed labels, PR #132), #117 (regular season everywhere, PR #136), #118 (same weeks everywhere, PR #139).

Read each lane top to bottom; the lanes run side by side.

| Lane | Order |
| --- | --- |
| V2.0a queue | #119 to #126 (V2.0a step 2), #127 (small-sample threshold and label, D13), #128 and #129 (wording), #130 (What Flags Cost), #131 (methodology) |
| Workstream 1 | Create the site-perf issues; Site perf 1, then 2, then 3 (minimal now, full version in V2.1); 4 any time; 5 after D24 and D27 |
| Workstream 2 | D21, then Phases B to E |
| Workstream 3 | Phase A (official ids) first; then B to F |
| Workstream 4 | Phase A and B (game record, Cron Trigger, R2 binding), then C and D |
| Workstream 5 | After D27; design in the private plan |

Two links cross lanes: the official ID file from Workstream 3 feeds the grade's foundations, and the richer ESPN capture feeds the weekly reconciliation. The grade publishes only after Site perf 5 keeps its parameters private.

### Turning this plan into issues

1. This file is committed as `docs/BUILD_PLAN_ADDENDUM.md` on branch `docs/build-plan-addendum`, with a PR.
2. Create labels once: `site-perf`, `analytics`, `sources`, `espn-live` (with `gh label create <name> --repo pipersandman/nfl-observatory --force`). The grade's label waits for D27.
3. In Claude Code, for one workstream phase at a time: have it read `docs/BUILD_PLAN_ADDENDUM.md`, draft that phase's issues in the same format as the site perf issue files (why, goal, depends on, every step, checks Ty can run), and show them before creating them.
4. Record each phase's start and finish in the pinned progress log, issue #86.
5. Order: the site perf issues and the three urgent decisions (D21, D24, D27) first, then continue #119 to #131 with Workstreams 2, 3 and 4 alongside, then the grade's foundations.
