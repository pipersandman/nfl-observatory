# Current state (V1), as of 2026-10-26

What exists before V2 starts. Written in W1 (#74) from the code at commit
`1f4a1a1`. Numbers later stages must match are in
[`baseline-2026-10-27.json`](baseline-2026-10-27.json).

**Ty: read this and correct anything wrong.**

## In one paragraph

A Python pipeline (`scripts/update_data.py`) downloads nflverse data with
`nflreadpy`, computes everything and writes static JSON to `frontend/data/`.
GitHub Actions runs it on a schedule, commits the JSON to `main`, pre-renders
static HTML pages, and uploads `frontend/` to HostGator by FTPS. The site is
plain HTML, CSS and JavaScript that reads those JSON files in the browser. A
separate Cloudflare Worker serves live penalties for `/gameday/` from ESPN.

## Data sources

| Source | What | How |
|---|---|---|
| nflverse play-by-play | Every play 2015 to now; flags are rows with `penalty == 1` | `nfl.load_pbp(season)` per season |
| nflverse schedules | Games, scores, spreads, weather, `referee` column | `nfl.load_schedules` |
| nflverse officials | Seven officials per game (lags in season: in 2026 it only had Week 1) | `nfl.load_officials` |
| Football Zebras | Crew chief assignments before kickoff (usually posted Tuesday ~9am PT) | `scripts/fetch_assignments.py` (RSS + one article per run). Exit 2 (#82) when the fetch or parse fails, the post has 0 games, or the week's first game kicks off with no post; "not posted yet" within 2 days of kickoff and partial parses are warnings (exit 0). Problems also show as `::warning::` on the Actions run page |
| Manual overrides | Corrections to assignments | `data/assignments_overrides.csv` |
| ESPN site API (unofficial) | Live box scores and play text during games | Gameday Worker only |

Crew chief for a played game comes from, in order: the officials feed, then
the schedule's `referee` column, then the saved Football Zebras assignment.
Names are normalized with `NAME_FIXES` in `update_data.py` (for example
"Ronald Torbert" becomes "Ron Torbert"). For 2026 regular-season games through
Week 7: 16 from the officials feed, 49 from the schedule, 42 from assignments.

## Pipeline scripts

`update_data.py` loads the data once, then calls each module with it. Current
season only by default; `--full` rebuilds 2015 to now (CI always uses
`--full`).

**Seasons** (#80): play-by-play and officials load 2015 up to nflverse's current
season (`nfl.get_current_season()`, which turns over the Thursday after Labor
Day; nflverse refuses later seasons). Schedules load up to the calendar year, so
next season's games appear as soon as nflverse publishes them (Week 1 previews
before opening night). The `seasonsRange` label follows the current season.

**One season rule** (#84): `scripts/seasons.py` (standard library only) holds the
same rule for code that runs without nflreadpy. `nflverse_current_season()`
matches `nfl.get_current_season()`; `schedule_seasons()` is the current season
plus the calendar year when later. Users:
- **Workflow gate** watches `play_by_play_<current season>.parquet`.
- **`fetch_assignments.py`** picks the next upcoming regular-season games across
  `schedule_seasons()` (January: Week 18 of the season in progress; August: next
  season's Week 1 once its schedule is out). Playoff games are never fetched.
  `--season` overrides; `--week` alone uses the season the default would pick.
- **`social/generate.py`** defaults `--season` to the current season.
`update_data.py` keeps calling `nfl.get_current_season()` directly.

**Failures** (#80):
- **Data loading** (schedules, officials, any season of play-by-play, including a
  required season with no rows) stops the run with exit 1 before anything is
  written.
- **Modules** each run even if an earlier one failed; `scorecard` and `history`
  are skipped if `previews` fails. Failures and skips are printed in an
  end-of-run summary (also on the Actions run page) and give exit 3.
- **Warnings** (exit 0): an unreadable published assignment file, and next
  season's schedule not published yet.
- **`frontend/data/run_status.json`**, written last and committed with the data:
  `runAt`, `ok`, per module `status` (`ok`, `failed`, `skipped`), short `error`
  or `reason`, `outputs`, and `lastSuccess` (carried forward from the previous
  file), plus `warnings`. For V2.0a step 9 (freshness).
- **`save_json()`** writes a temp file and renames it into place, so a failed
  write leaves the old file. Multi-file modules can still leave a mix of old and
  new files if they fail partway (#81).
- **Testing:** `NFLOBS_FAIL=<name>[,<name>]` forces a named step to fail
  (modules, `wp_tables`, `load_pbp`, `load_schedules`, `load_officials`,
  `save_json:<file>`). It is ignored, with a warning, when `GITHUB_ACTIONS` is
  set.

| Script | Writes (under `frontend/data/`) | What |
|---|---|---|
| `update_data.py` | `stats.json`, `trends.json`, `insights.json`, `season_comparison.json`, `referees.json`, `referee/<slug>.json`, `wp_tables.json` | Core: league totals, trends by season/quarter/type, home vs away, crew chief summaries and profiles, win-probability tables for the Worker |
| `scoreboard.py` | `scoreboard.json` | League running totals by timeframe, week-by-week log |
| `type_trends.py` | `type_trends.json` | Per-game rate of each penalty type by season, this season vs three comparisons |
| `flag_impact.py` | `flag_impact.json` | "What Flags Cost": expected points and drive effect of each accepted flag |
| `stat_miner.py` | `reports/miner/` (tracked) | Weekly ranked list of unusual stats with a false-discovery filter |
| `crew_styles.py` | `crew_styles.json` | Each active crew's calling fingerprint, season-adjusted and shrunk toward league |
| `team_pages.py` | `teams/index.json`, `teams/<ABBR>.json` | Team profiles: this season vs last vs all prior, ranks, types, players, crews |
| `previews.py` | `previews/<season>-week-NN.json`, `previews/latest.json` | Projected flags per game (model estimate; negative binomial ranges) |
| `scorecard.py` | `scorecard/live/`, `scorecard/backtest/`, `scorecard/public.json` | Freezes projections at kickoff, backtests, grades them |
| `history.py` | `history/index.json`, `history/games/`, `history/snapshots/` | Permanent week-by-week ledger with a corrections log |
| `fetch_assignments.py` | `assignments/<season>-week-NN.json` | Football Zebras crew assignments (run before `update_data.py`) |
| `build_static.py` | `frontend/crew/`, `team/`, `assignments/`, `trends/`, `guide/`, `dataset/`, `sitemap.xml`, `llms.txt`, `data/exports/*.csv` | Pre-rendered HTML for search engines and AI crawlers; deploy-time only, gitignored |
| `weeks.py`, `jsonsafe.py` | — | Helpers: completed-week logic; NaN-safe JSON writing |
| `scorecard_report.py` | `reports/scorecard-YYYY-MM-DD.md` (local, untracked) | Internal projection-error report |
| `social/generate.py`, `captions.py`, `colors.py` | `social/output/` (untracked), `social/snapshots/` (tracked) | Weekly social post images and captions; run by hand |
| `make_baseline.py` (W1) | `docs/architecture/baseline-*.json` | Snapshot of published numbers |
| `check.py` (W1) | — | All checks CI runs |

## Site

| Path | What |
|---|---|
| `frontend/index.html`, `js/app.js` (~3,900 lines), `css/styles.css` | The main single-page app; reads `data/*.json` with `fetch` |
| `frontend/js/livestrip.js` | Live strip on the home page |
| `frontend/gameday/index.html`, `js/gameday.js`, `css/gameday.css` | Live Gameday page; reads the Worker |
| `frontend/css/static.css` | Styles for the pre-rendered static pages |
| `frontend/.htaccess` | HostGator (Apache): HTTPS, one canonical address, security headers, caching |
| `frontend/robots.txt`, `site.webmanifest`, icons, `og-image.png` | Site metadata |

## Gameday Worker (`worker/gameday/`)

Cloudflare Worker `nflobs-gameday` serving `GET /live`: ESPN scoreboard and
game summaries, parsed into flags per team (`parse.js`), cached about 15
seconds, combined with the site's `data/previews/latest.json` and
`data/wp_tables.json`. Deployed by pasting `worker.bundle.js` (made by
`node bundle.mjs`) into the Cloudflare dashboard, or with Wrangler. Not deployed
by GitHub Actions. Free plan: 100,000 requests a day.

## Workflows

| Workflow | Runs | Does |
|---|---|---|
| `update-data.yml` | Tuesday 06:00 UTC weekly; Tuesday and Wednesday for assignments; hourly during game windows; every push to `main` (except data-only changes); manual | Game-day runs skip unless nflverse play-by-play for the current season (#84) changed (checks `source_stamp.json`); they also skip while that season's file isn't published yet (opening week), while weekly, manual and push runs go ahead and stop red at data loading if it's still missing. If the nflverse check itself fails, every run continues. Then: install, fetch assignments (allowed to fail: `continue-on-error`, so its exit 2 shows on the step without skipping anything), `update_data.py --full` (exit 3, module failures, still publishes; exit 1 stops the run), commit `frontend/data/` and `reports/miner/` to `main` as `github-actions[bot]`, build static pages, cache-bust CSS/JS URLs, FTPS deploy to HostGator, then "Fail if any module failed" turns the run red if `run_status.json` says `ok: false` |
| `checks.yml` (W1) | Every pull request; manual | `python scripts/check.py`. Job name `checks` |
| Dependabot | Weekly | Pip updates in `scripts/`, GitHub Actions updates |

Actions are pinned to commit SHAs. The data bot pushes directly to `main`
with the workflow's `GITHUB_TOKEN`, which can't be a ruleset bypass actor. So
the W1 ruleset only restricts deletions and blocks force pushes (plan section
28 step 5). Requiring pull requests and the `checks` job needs a GitHub App
for the bot to push as; tracked in #78.

## Secrets (names only)

| Name | Where | Used by |
|---|---|---|
| `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_SERVER_DIR` | GitHub Actions secrets | Deploy step |
| `GITHUB_TOKEN` | Provided by Actions | nflverse release check, data commit |
| `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT` | Not yet created | V2.0 step 1 |
| `ODDS_API_KEY`, `SENTRY_DSN`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `ANTHROPIC_API_KEY` | Not yet created | Later stages (see `.env.example`) |

## Dependencies

- Runtime (`scripts/requirements.txt`, bounded to major versions): `nflreadpy`,
  `pandas`, `numpy`, `pyarrow`, `requests`, `beautifulsoup4`.
- Checks (`scripts/requirements-dev.txt`, exact): `ruff`, `pre-commit`.
- Python 3.11 (laptop and Actions). Node LTS for the Worker scripts and checks.
- Social images need Playwright with Chromium, installed by hand (see
  `social/README.md`); not in either requirements file.

## Deploy flow

1. Code merges to `main`, or a scheduled run starts.
2. `update-data.yml` rebuilds the data and commits it to `main`.
3. The same run pre-renders static pages and cache-busts asset URLs (in the
   runner only, never committed).
4. FTPS upload of `frontend/` to HostGator. No staging site.
5. The Worker is deployed separately, by hand.

## Definitions worth knowing (checked in W1)

- **Flag** = a play nflverse marks `penalty == 1`, counted once per play. In
  2026 regular season, 27 such plays also carry a second, declined flag; it is
  not counted again.
- **League flags per game by season** (`trends.json`) includes playoff games;
  its game count is games with at least one flag. In every season since 2015
  that equals all played games, so the rate is unaffected.
- **Current-season numbers** (`season_comparison.json`, team pages, crew
  pages) are regular season only.

## Recompute check (W1)

The baseline was recomputed directly from nflverse play-by-play and schedules
with separate code (not the pipeline's):

| Numbers | Result |
|---|---|
| League flags, games and flags per game, each season 2015–2026 | All 12 seasons match exactly |
| 2026 regular-season league total (1,570 flags, 107 games, 14.67 per game) | Match |
| 2026 team flags, games, per-game rate and rank (32 teams) | All 32 match |
| 2026 crew chief flags and games (17 active) | All 17 match once the officials-feed name fix is applied (Ron Torbert's Week 1 game is listed as "Ronald Torbert") |

## Known gaps

1. **~~Module failures don't fail the run.~~** Fixed in #80: a failed module
   turns the run red and is recorded in `run_status.json`; data-loading failures
   stop the run before anything is written. Remaining part: multi-file modules
   can leave a mix of old and new files (#81).
2. **No tests of the numbers.** Before W1 there were no automated checks at all;
   `check.py` now covers lint, syntax and JSON validity, not correctness.
3. **Two definitions of "season"** sit side by side: league trends include
   playoffs, current-season pages don't.
4. **Plays with an offsetting-penalty description** are counted as flags (0–6
   plays a season). Worth checking against the "accepted penalties" wording in
   V2.0a.
5. **Wording:** the Referee Variance insight in `update_data.py` says "most
   lenient and strictest crews", against rule 5 in `CLAUDE.md` (#76).
6. **Worker deploys by hand** and has no checks beyond syntax; the ESPN API is
   unofficial.
7. **No staging site**: every merge to `main` deploys to production.
8. **Windows: redirected output crashes on emoji.** Running
   `update_data.py > log.txt` on Windows fails with `UnicodeEncodeError` at the
   first 🏈. Workaround: set `PYTHONUTF8=1` first. Linux (Actions) is fine.
9. **Two unused calculations kept for their own issues** (marked
   `# noqa: F841  (flagged in #74)`): `d_ly` in `social/captions.py` (#75)
   and `spread` in `update_data.py` (#76).
10. **Formatter not adopted yet**: Ruff format would change about 9,500 lines
    in 18 files; deferred to its own issue.
11. **Dependabot bumps** `ruff` in `requirements-dev.txt` but not the matching
    `rev` in `.pre-commit-config.yaml`; update both together.
12. **`main` doesn't require pull requests or passing checks.** The ruleset
    only restricts deletions and blocks force pushes, because the data bot's
    `GITHUB_TOKEN` can't bypass stricter rules. A merge with a red `checks` job
    is possible until #78 is done.
