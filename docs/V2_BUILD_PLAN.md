# V2 Build Plan: Architecture, Analytical Trust, Experience and Quant Research

**What this covers:** what V2 is (the platform, tools and sequence a
professional team would use), how every number earns trust (statistical
validity, metric definitions, data quality), how the site is organized for fans,
journalists and analysts, the quantitative research track, and how it gets
built: one step at a time, by you with Claude Code on the ROG Strix laptop,
through GitHub pull requests.

**Start here:** Part E, section 27 (Session W0, set up the laptop), then
Session W1. After that, two things run side by side: **V2.0a trust fixes** on
the current site and **V2.0 step 1, R2 raw capture** (time-sensitive).

**What changed (Oct 2026):**
- The AI agent delivery system (old Part C, stage V2.-1) is removed. No parallel
  agents, no independent-reviewer model, no orchestrators, no home-lab machines.
- New Part B (analytical trust) and Part C (experience and information design)
  come from the site audit. Its color and typography recommendations are not
  adopted; the current Penalty Flag theme stays (section 12).
- New stages V2.0a (trust fixes on the current site) and V2.1b (fair
  comparisons). V2.1 now carries the new navigation and page structure.

**Related docs:**
[Data & Modeling Roadmap](DATA_AND_MODELING_ROADMAP.md) (data platform and
models) · [Growth Cadence Plan](GROWTH_CADENCE_PLAN.md) (weekly publishing and
indexing; Phase 1 now, Phase 2 overlaps with this plan) ·
[Data Sources](DATA_SOURCES.md) · [Stat Miner](STAT_MINER.md) (unusual-stat
discovery: live Phases 1–2, roadmap Phases 2.5–5).

**How to use this doc:** each step lists what it depends on, its micro-steps
and how to confirm it's done. Any step can be drilled into further before
building. Each step becomes one GitHub issue and one pull request (section 29).
Decisions are recorded in section 33.

---

## Contents

**Part A: Architecture**
1. [Principles](#1-principles)
2. [Target architecture](#2-target-architecture)
3. [Stack by layer](#3-stack-by-layer)
4. [Migration sequence](#4-migration-sequence)

**Part B: Analytical trust and statistical validity**
5. [Three kinds of metric](#5-three-kinds-of-metric)
6. [The metric dictionary](#6-the-metric-dictionary)
7. [Sample size and uncertainty](#7-sample-size-and-uncertainty)
8. [Observed rates vs adjusted crew estimates](#8-observed-rates-vs-adjusted-crew-estimates)
9. [Comparable periods](#9-comparable-periods)
10. [What Flags Cost: observed vs modeled](#10-what-flags-cost-observed-vs-modeled)
11. [Data quality, provenance and corrections](#11-data-quality-provenance-and-corrections)

**Part C: Experience and information design**
12. [Design scope: the current theme stays](#12-design-scope-the-current-theme-stays)
13. [Five questions, three layers](#13-five-questions-three-layers)
14. [Navigation and page map](#14-navigation-and-page-map)
15. [Home page structure](#15-home-page-structure)
16. [Chart standard](#16-chart-standard)
17. [Ethical design standard](#17-ethical-design-standard)
18. [Accessibility and mobile](#18-accessibility-and-mobile)
19. [Three audiences](#19-three-audiences)
20. [Measuring whether it works](#20-measuring-whether-it-works)

**Part D: Quant research track**
21. [Ground rules](#21-ground-rules)
22. [Hypotheses: where edges might exist](#22-hypotheses-where-edges-might-exist)
23. [Core calculations](#23-core-calculations)
24. [Methods](#24-methods)
25. [Research phases (Q0–Q5)](#25-research-phases-q0q5)

**Part E: How it gets built (solo, Claude Code)**
26. [Working model](#26-working-model)
27. [Session W0: set up the laptop](#27-session-w0-set-up-the-laptop)
28. [Session W1: repository conventions](#28-session-w1-repository-conventions)
29. [The routine for every step](#29-the-routine-for-every-step)
30. [Accounts, created when needed](#30-accounts-created-when-needed)
31. [Stage gates](#31-stage-gates)
32. [Security and cost controls](#32-security-and-cost-controls)

**Shared**
33. [Decisions log](#33-decisions-log)
34. [Dependency map](#34-dependency-map)
35. [Costs](#35-costs)

---

# Part A: Architecture

## 1. Principles

1. **Keep what works, replace custom glue.** The Python pipeline, static-first
   pages, the history ledger and the "every number is checked" rule stay.
   Hand-built pieces (static page builder, JSON-file storage, ad-hoc checks)
   are replaced by established open-source tools.
2. **Replace gradually, never rewrite at once.** Each new piece runs alongside
   the old one until proven (the "strangler" approach). The weekly publishing
   cadence never breaks.
3. **One definition of every metric.** "Flags per game," "same-weeks
   comparison," "points given away" are defined once (the metric dictionary,
   then the semantic layer) and used by the site, the API and the AI alike.
4. **Trust before polish.** Fix comparability, denominators and wording before
   redesigning pages. A good-looking chart that misleads is worse than a plain
   one that doesn't.
5. **Transparency is a product feature.** Every number shows what it counts, over
   which games, against which baseline, and how sure we are. Methodology sits
   beside the finding, not only behind a help icon.
6. **Observed is not modeled is not causal.** The site labels which of the three
   each number is and never words a result more strongly than the analysis
   supports.
7. **Static and fast by default.** Pages are HTML first; interactivity is added
   only where it helps. This is also what search engines and AI assistants read.
8. **Open source and low cost.** Prefer permissive licenses (MIT, Apache 2.0)
   and free tiers; hosted services over self-hosting while there's no home lab.
9. **Every change is reviewable.** Code, data definitions, dashboards and
   architecture decisions live in git and go through pull requests.

## 2. Target architecture

```
                 ┌──────────────────────── SOURCES ────────────────────────┐
                 │ nflverse (play-by-play, schedules, officials, snaps,    │
                 │ injuries) · Football Zebras (assignments) · weather ·   │
                 │ betting lines (open/close/movement, props)              │
                 └───────────────────────────┬─────────────────────────────┘
                                             ▼
   ORCHESTRATION   Dagster  (schedules, retries, lineage, data-quality checks)
                                             ▼
   STORAGE         Cloudflare R2: raw snapshots (Parquet, append-only)
                                             ▼
   WAREHOUSE       DuckDB  +  dbt Core  (canonical penalty-event table, tests)
                                             ▼
   SEMANTIC LAYER  dbt metrics = the metric dictionary (one definition of every number)
          ┌──────────────────────┬──────────────────────┬──────────────────────┐
          ▼                      ▼                      ▼                      ▼
   MODELS & RESEARCH      PUBLIC SITE            PUBLIC API             ASK THE OBSERVATORY
   Bambi/PyMC, LightGBM,  Astro (static pages    FastAPI or Datasette   Claude + tool use over
   MLflow tracking,       + interactive islands, (read-only JSON, CSV,  semantic-layer views only,
   ledger + scorecard     DuckDB-WASM explorer,  definitions included)  read-only, row limits,
                          Pagefind search,                              accuracy test set
                          Data & Methods pages)
          │                      │                      │                      │
          └────────── Cloudflare Pages · Workers · Cron Triggers · R2 ─────────┘
                       Supabase (accounts, saved searches, feature requests)
                       Sentry · hosted uptime monitor · Cloudflare Web Analytics
```

## 3. Stack by layer

| Layer | Choice | Alternative | Why |
|---|---|---|---|
| Orchestration | **Dagster** (open source; runs on the laptop with `dagster dev` while building; production on a small DigitalOcean droplet or Dagster+ serverless, D3) | Prefect | Our pipeline is a set of data assets (play-by-play, crews, projections, ledger); Dagster models assets directly, with lineage and built-in data-quality checks, and integrates with dbt |
| Raw storage | **Cloudflare R2**, Parquet, append-only | AWS S3 | Already planned in the roadmap; no egress fees; same vendor as hosting |
| Warehouse | **DuckDB** | MotherDuck (hosted DuckDB) when live queries need it | Fast, free, file-based; no database server |
| Transformations + metrics | **dbt Core** with dbt-duckdb | SQLMesh | Tested, version-controlled definitions; the metric dictionary lives here from V2.0 |
| Data quality | dbt tests + Dagster asset checks + **Pandera** (Python frames) | Great Expectations, Soda | Every run validates before anything publishes (section 11) |
| Modeling | **Bambi/PyMC** (hierarchical), **LightGBM**, scikit-learn | brms (R) | Calibrated count models with honest uncertainty + interaction-finding models |
| Experiment tracking | **MLflow** (local files while building) | Weights & Biases | Every model version, its features and its scorecard results recorded; registry for champion/challenger |
| Public site | **Astro** (MIT; maintained by Cloudflare since Jan 2026) | Observable Framework; SvelteKit | Static HTML by default with interactive islands; real URL for every page; first-class on Cloudflare. Replaces `build_static.py` and `#` links |
| UI components | Current design tokens from `styles.css` + headless components (Radix or Ark UI; Bits UI if Svelte islands) + **Storybook** | — | Accessible behavior without someone else's look. Cloudscape rejected for the public site (AWS look, React-only, Highcharts license for charts) |
| Charts | **Observable Plot** (most charts, incl. dot plots with intervals), **Vega-Lite** (AI-generated charts), Chart.js during migration | Apache ECharts | Plot for concise publication-quality charts; Vega-Lite specs are plain JSON the AI can produce and we can validate before drawing |
| In-browser data explorer | **DuckDB-WASM** + Parquet | — | Filter and slice all data instantly, no server |
| Site search | **Pagefind** | — | Full-text static search, zero server cost |
| Public API | **FastAPI** (reuses Python code) or **Datasette** (instant read-only API + SQL explorer) | — | Journalists and developers; backlinks |
| Accounts + user data | **Supabase** (open-source Postgres + auth) | Clerk + Neon | Saved searches and visualizations, feature requests |
| Ask the Observatory | **Claude with tool use** over semantic-layer views | — | Vanna (open-source text-to-SQL) is archived; building on our own definitions is safer and more accurate |
| Internal analytics | **Evidence** (SQL + Markdown → static reports) | Quarto | Fast internal reports (weekly scorecard, research write-ups, data-quality report) |
| Internal admin console | Plain Astro pages (Cloudscape allowed for private tools) | — | Pipeline runs, data-quality status, narrative review queue, indexing status |
| Hosting | **Cloudflare Pages + Workers + Cron Triggers**; DigitalOcean droplet or Dagster+ for Dagster | AWS (S3, Lambda, ECS) later, as a learning path | Global CDN, instant deploys, Crawler Hints (automatic IndexNow) once DNS moves to Cloudflare |
| Monitoring | **Sentry** (errors), a **hosted uptime monitor** (UptimeRobot or Better Stack free tier, D17), **Cloudflare Web Analytics** (already in use, D18) | Self-hosted Uptime Kuma or Umami if a home lab is added later | No servers of our own to keep running |
| Engineering hygiene | GitHub Actions, Playwright, Lighthouse CI, axe accessibility checks, Ruff, pre-commit, architecture decision records in `docs/adr/` | — | Keeps the codebase healthy as it grows |

## 4. Migration sequence

**Rule for every stage:** the old path keeps running until the new one has
matched its output for two consecutive weeks.

**Order:** W0 → W1 → (V2.0a and V2.0 step 1 in parallel) → rest of V2.0 →
V2.0b → V2.1 → V2.1b → V2.2 → V2.3 → V2.4. The quant track (Part D) starts once
V2.0 step 1 is capturing data. See the dependency map, section 34.

### V2.0a Trust fixes on the current site

**Why first:** these change wording, labels and calculations on pages that
already exist, need no new tools, and make every later stage build on correct
numbers. Details are in Part B; the standard each page must meet is section 17.

**Depends on:** W1.

1. **Metric inventory and conflict audit**
   1. Claude Code: list every number the site publishes (each JSON field in
      `frontend/data/`, each tile, chart, table and CSV in `/dataset/`) with its
      name, numerator, denominator, games included, period, and whether it
      counts accepted, declined, offsetting or nullified penalties.
   2. Claude Code: flag conflicts: the same name calculated two ways, different
      season scopes or week cutoffs on different pages, playoffs or overtime
      included in one place and not another, current-season figures that mix
      partial and complete weeks.
   3. Output: `docs/METRICS.md` (metric dictionary v0, format in section 6) and
      `docs/audits/metric-conflicts-YYYY-MM-DD.md`.
   4. You: read the conflict list and decide each one (pick the definition).
   5. **Done when:** every published number has a dictionary entry and every
      conflict has a decision.
2. **Fix the conflicts**
   1. One shared definition of season scope and completed weeks (in
      `scripts/weeks.py`), used by every script.
   2. Each conflicting metric recalculated to its chosen definition.
   3. **Done when:** a check script recomputes each metric from play-level data
      and matches the JSON for every 2026 week.
3. **Show the sample behind every rate**
   1. Games (or plays) next to every per-game rate: crew tables, team tables,
      trends.
   2. League-average benchmark for the same period next to every crew and team
      rate.
   3. A "small sample" label when below the threshold (D13).
   4. **Done when:** no rate appears on the site without its games count.
4. **Absolute and relative changes together**
   1. Every percentage change shows the absolute change and the baseline
      ("+0.10 flags per game, +40%, vs Weeks 1–7 of 2025").
   2. **Done when:** a search of the built pages finds no bare percentage change.
5. **Rename and reword rankings**
   1. "Observed flags per game" on crew and team rankings; the sort field named
      on every ranked list (still sorted most flags first).
   2. Replace wording that implies a cause ("strictest crew") with descriptive
      wording ("most flags per game in their games").
   3. **Done when:** the wording checklist in section 17 passes on every page.
6. **Chart subtitles carry the key caveat**
   1. Every chart gets a subtitle with population, period and inclusion rules;
      the single most important caveat moves from the ? panel into the subtitle.
      The ? panel keeps formulas and edge cases.
   2. **Done when:** every chart has a subtitle (checked in Playwright).
7. **What Flags Cost: label observed vs modeled**
   1. Each figure tagged "Observed" (yards, erased touchdowns) or "Model
      estimate" (expected points, win chance), with the one-sentence
      counterfactual explanation from section 10.
   2. Methodology states whether costs are direct only or include downstream
      effects.
   3. **Done when:** no modeled number appears without its label and sentence.
8. **Rounding rules** (section 6) applied everywhere; no false precision.
9. **Freshness and exports**
   1. "Data through Week N, updated <date/time PT>" on every page.
   2. Every CSV in `/dataset/` gets a matching `<file>.meta.json` (or a README
      section) stating definition, period, filters and data version.
   3. **Done when:** every page and download shows its data version.
10. **Methodology page**
    1. Expand `/guide/#methodology`: the metric dictionary in plain English,
       limitations (crew = whole crew, not one official; observed ≠ strictness;
       accepted-penalty rules), and a data-quality summary.
    2. **Done when:** every metric's ? panel links to its dictionary entry.
11. **Baseline usability test** on the current site (section 20) so V2.1 can be
    compared against it.

### V2.0 Data platform (time-sensitive; step 1 starts right after W1)

**Depends on:** W1; you creating the Cloudflare R2 bucket and an API token.

1. **R2 bucket and raw capture**
   1. You: Cloudflare dashboard → **R2** → **Create bucket** → name `nflobs-raw` → **Create**.
   2. You: **R2** → **Manage API tokens** → **Create API token** → permission **Object Read & Write**, bucket `nflobs-raw` → copy the Access Key ID, Secret and endpoint into Bitwarden.
   3. You: GitHub repo → **Settings → Secrets and variables → Actions** → add `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`.
   4. Claude Code: every pipeline run writes raw pulls (play-by-play, schedules, officials, assignments, weather, betting lines once available) to `raw/<source>/<date>/` as Parquet, never overwritten.
   5. **Done when:** a week of runs is in R2 and a script can rebuild any past week's site data from raw files alone.
2. **DuckDB + dbt**
   1. dbt project in `warehouse/` with sources (raw), staging (cleaned), marts (games, penalties, crews, teams, projections, ledger).
   2. A **canonical penalty-event table** (one row per penalty: game, play, team, crew, type, accepted/declined/offsetting/nullified, yards, play outcome, game state), with separate games, teams, officials, rule-definition and model-output tables (section 11).
   3. The metric dictionary moves into dbt YAML: every metric with its numerator, denominator, population, window, inclusion rules, benchmark, formula, rounding and limitations. `docs/METRICS.md` and the public methodology page are generated from it.
   4. **Done when:** dbt's output matches the current JSON numbers exactly for every 2026 week (diff report = zero differences).
3. **Data-quality checks** (full list in section 11) as dbt tests and Dagster asset checks; a failed check blocks publishing.
4. **Dagster**
   1. One asset per source and per mart; schedules match the Growth Cadence Plan (Tue polling, Thu previews, Mon/Tue recaps, daily).
   2. Build and test on the laptop (`dagster dev`); then deploy to the DigitalOcean droplet or Dagster+ (D3). GitHub Actions remains the deploy step.
   3. **Done when:** Dagster has produced the site's data for two weeks with zero manual fixes, and GitHub Actions only builds and deploys.
5. **Corrections log:** when a source revises a past record, the change is recorded (what, when, old and new value) and shown on the Data & Methods page, so a source correction is never mistaken for a real change in NFL behavior.

### V2.0b Stat miner Phase 3 (pattern finding)

**Depends on:** V2.0 steps 1–4 and Data Sources P0. Full plan: [Stat Miner](STAT_MINER.md), section 8.

1. Move `scripts/stat_miner.py` into a Dagster asset reading the dbt marts; output `marts.stat_candidates`.
2. Add changepoint detection, game-fingerprint anomalies, crew × team matchups, per-snap and official-level patterns.
3. **Done when:** the weekly report includes pattern items, backtested on 2015–25, and every item still carries its plays as evidence.

### V2.1 Astro site with the new structure

**Depends on:** V2.0 step 2 (marts as the data source), V2.0a (correct numbers
and wording to carry over).

1. Astro project in `site/`; current design tokens and components ported from `styles.css` (section 12); Storybook catalog including the chart standard (section 16) as a reusable chart frame (headline, subtitle, chart, benchmark, sample, method link, data table, export).
2. The six-section navigation and page map (section 14); the home page structure (section 15); the three layers (section 13) on every topic.
3. Global filters (season, weeks, season type) shared across a page; any section-specific exception is labeled; changing a filter updates title, baseline, sample size and export together.
4. Build order: static pages (crew, team, assignments, trends, guide, dataset) → Growth Cadence pages (previews, report cards, team-week, live facts) → Game impact section → home page with interactive islands.
5. Clean URLs (`/crew/scott-novak/`) for everything; old `#crew=` links redirect on load; existing `.htaccess` redirects carried over.
6. Accessibility and mobile (section 18): axe checks in CI, keyboard pass, text equivalents and data tables for every chart.
7. Move hosting to Cloudflare Pages; DNS to Cloudflare; turn on Crawler Hints.
8. Usability round 1 on the new site, same tasks as the baseline (section 20).
9. **Done when:** every current page has an Astro equivalent, Lighthouse scores ≥ 90, axe shows no serious or critical issues, usability tasks succeed at least as often as on the baseline, and Search Console shows no new errors two weeks after cutover.

### V2.1b Fair comparisons

**Depends on:** V2.1; Q0 item 3 (snap counts and participation); the
hierarchical count model from the Data & Modeling Roadmap (section 5.2).

1. **Opportunity-adjusted rates** where a defensible denominator exists (section 5), each with its denominator shown.
2. **Uncertainty intervals** on crew and team rates from the model (section 7); none shown where the data can't support one.
3. **Adjusted crew estimates** beside observed rates (section 8): observed, adjusted, uncertainty, and the model caveat.
4. **Leaderboards as dot plots** with intervals and a league-average line, still sorted most flags first.
5. **What Flags Cost evidence cards** with uncertainty where available (section 10).
6. Usability round 2 focused on whether users read intervals and "adjusted" correctly.
7. **Done when:** every crew and team comparison shows observed, adjusted (where modeled) and uncertainty, and the model's coverage is checked on held-out 2025 games (90% intervals contain about 90% of outcomes).

### V2.2 Explorer, API, search

**Depends on:** V2.1.

1. DuckDB-WASM explorer page over Parquet exports (filter by crew, team, season, week, penalty type); exports include the active filters, definitions and data version.
2. Public read-only API (FastAPI on Workers-compatible hosting, or Datasette) with rate limits; every response names its metric definitions and data version; documented on `/dataset/`.
3. Pagefind search across all pages.
4. **Done when:** API and explorer return the same numbers as the pages for 20 spot-checks.

### V2.3 Accounts and saved work

**Depends on:** V2.2.

1. Supabase project: auth (email link + Google), tables for saved searches, saved visualizations, feature/data requests (with voting).
2. "Save this view" on charts and the explorer; a "Request a feature or data" form feeding a public roadmap page.
3. **Done when:** a user can save, reopen and share a view, and requests appear in the admin console.

### V2.4 Ask the Observatory

**Depends on:** V2.0 (semantic layer), V2.3 (saving answers).

1. Claude with tool use: a `query_metrics` tool limited to semantic-layer views, read-only, row limits, query timeout.
2. Charts returned as Vega-Lite specs, validated before rendering, using the chart standard (section 16).
3. Answers follow the ethical design standard (section 17): sample sizes, absolute and relative changes, observed vs modeled labels, no causal wording.
4. Accuracy test set of 200 questions with known answers; launch only at ≥ 95% exact-match on numbers.
5. Every answer cites the views it used; saved answers become shareable, indexable pages.
6. **Done when:** the test set passes and the first 100 real questions are reviewed with no wrong numbers.

---
# Part B: Analytical trust and statistical validity

**Purpose:** make every number defensible before it's redesigned. Built in
V2.0a (on the current site), moved into dbt in V2.0, extended with models in
V2.1b.

## 5. Three kinds of metric

| Kind | Example | What it tells us | When |
|---|---|---|---|
| Raw count | 85 accepted penalties | Total observed events | Now |
| Exposure-adjusted rate | 8.5 flags per game | Events relative to games played | Now (stays the headline measure) |
| Opportunity-adjusted rate | Flags per 100 relevant plays | Events relative to chances for the event to occur | V2.1b |

**Planned opportunity-adjusted rates** (denominator must match the event):

| Metric | Denominator | Data needed |
|---|---|---|
| Offensive holding per 100 offensive plays | Offensive scrimmage plays | Play-by-play (have) |
| Defensive pass interference per 100 opponent pass attempts | Opponent pass attempts incl. plays nullified by penalty | Play-by-play (have) |
| False starts per 100 offensive snaps | Offensive snaps | Snap counts (Q0 item 3) |
| Crew flags per 100 plays | All scrimmage plays in the crew's games | Play-by-play (have) |

**Rules:**
1. Every rate shows its denominator.
2. Plays that don't fit cleanly (penalties on no-plays, special teams, kneels,
   spikes) have a documented rule for whether they count as an opportunity.
3. Per-game rates stay as the plain-language headline; opportunity rates sit
   beside them, not instead of them.

## 6. The metric dictionary

**Where it lives:** `docs/METRICS.md` in V2.0a; dbt YAML from V2.0 (the
markdown and the public methodology page are generated from it).

Every published metric has:

| Field | What it records |
|---|---|
| Metric name | One name, used everywhere |
| Kind | Raw count / exposure rate / opportunity rate / model estimate |
| Numerator | Which events count |
| Denominator | Games, plays, snaps, attempts |
| Population | Teams, crews, regular season, playoffs |
| Time window | Exact weeks and season boundaries; partial-week rule |
| Inclusion rules | Accepted, declined, offsetting, nullified |
| Benchmark | League average for the same window, prior season, or other |
| Calculation | Formula, weighting, missing-data treatment |
| Rounding | Display precision |
| Provenance | Source dataset, update time, transformation version |
| Limitations | Known biases and what the number does not mean |

**Default rounding:** per-game rates to one decimal; percentages to whole
numbers (one decimal only below 10%); model estimates to the precision their
interval supports; counts as integers.

## 7. Sample size and uncertainty

1. **Always shown:** games (or plays), the observed rate, the league benchmark
   for the same window.
2. **Small-sample label** below a threshold (D13; for example, fewer than 8
   games for a crew in a season, or any team before Week 4).
3. **Intervals (V2.1b):** 90% or 95% intervals from the hierarchical model
   (D14). Check overdispersion first: negative binomial if the variance exceeds
   the mean, which flag counts usually do. Partial pooling pulls crews with few
   games toward the overall distribution.
4. **No manufactured precision:** if the data can't support an interval, show
   the sample and the label instead of a number that looks precise.

## 8. Observed rates vs adjusted crew estimates

A crew's flag rate reflects the teams, game situations and weather it drew, not
only how strictly it calls games. Crews are assigned roughly independently of
matchups (Part D, calculation 3), which helps, but over one season the draw can
still be lopsided.

**Model (V2.1b):** flag count per game ~ negative binomial, with
log(expected flags) = log(exposure) + season effect + team effects (both teams,
offense and defense) + crew effect + game conditions (score state, weather,
venue where reliable). The crew effect is an adjusted association, not proof of
cause.

**Every crew comparison shows four things:**
1. **Observed rate:** what happened in their games.
2. **Adjusted estimate:** the crew's rate after accounting for the listed factors.
3. **Uncertainty:** the interval around the adjusted estimate.
4. **Caveat:** what the model doesn't account for.

## 9. Comparable periods

1. Season comparisons default to the **same weeks** of each season (already the
   site's "same-weeks comparison"; applied everywhere).
2. Games completed in each period are shown.
3. Preseason, regular season, playoffs and overtime inclusion is stated.
4. The baseline sits beside the statistic.
5. Partial weeks are labeled; a partial season is never presented as a full one.
6. Where a rule change affects a penalty type, the change is annotated on the
   chart so it isn't read as a behavior trend.

## 10. What Flags Cost: observed vs modeled

| Measure | Kind | How it's labeled |
|---|---|---|
| Penalty yards | Observed | "Observed" |
| Touchdowns or gains erased | Observed (the play was nullified) | "Observed" |
| Expected-points change | Model estimate | "Model estimate" + counterfactual sentence |
| Win-chance change | Model estimate | "Model estimate" + counterfactual sentence |
| Drives ending without points after a flag | Observed outcome; does not by itself show the flag caused it | "Observed; not a cause" |

**Evidence card** for each event (V2.1, with uncertainty in V2.1b): the event,
the rule, the game context (score, quarter, time, down and distance), the
estimated impact, and the counterfactual assumption. Example sentence:

> **Model estimate: 3.2 expected points.** Compares modeled expected points
> under the ruling with the modeled result had the play stood. Not a directly
> observed number of points lost.

The methodology states whether costs are direct only or include downstream
effects, and the calculation is reproducible from play-level data
(`scripts/flag_impact.py`, later a dbt model). Rankings of "costliest flags"
name their ranking basis and never imply referee error.

## 11. Data quality, provenance and corrections

**Checks on every run** (a failure blocks publishing):
1. Game counts and completed-week boundaries match the schedule.
2. No duplicate plays or penalty events.
3. Team and crew identifiers map consistently across seasons (name fixes
   included).
4. Penalty counts and yards reconcile to the source.
5. Totals, percentages and rankings agree with their underlying rows.
6. Unusually large week-over-week changes are flagged for review (possible
   source or pipeline issue).
7. Every played game has a crew.

**Provenance:** each output records its source, pull time and transformation
version.

**Corrections vs real change:** source revisions go in the corrections log
(V2.0 step 5); a figure that changed because the data was corrected says so.

**Public Data & Methods page:** the dictionary, the checks above with the latest
result, when each dataset was last refreshed, and the corrections log.

**Canonical dataset:** one row per penalty event, linked to games, teams,
officials, rules and model outputs, so any ranking can be rebuilt from its
rows.

---

# Part C: Experience and information design

**Purpose:** a fan gets an answer quickly, a journalist can verify it, an analyst
can reproduce or challenge it. Built mainly in V2.1 (wording and labels already
in V2.0a).

## 12. Design scope: the current theme stays

The audit's color and typography recommendations are **not adopted**. The
Penalty Flag theme and its rules stay as they are:

1. Neutral graphite UI with a single flag-yellow accent.
2. Red = more penalties and green = fewer, kept unambiguous, always with a text
   label or shape as well (never color alone).
3. Team colors (exact official colors, never altered) only on game-preview split
   bars and the quarter-by-quarter chart.
4. No emoji icons except the football (🏈) and the quarter-by-quarter clock (⏱️).
5. Any chart of penalties per game is sorted most penalties first.

What *is* taken from the audit: structure, hierarchy, chart anatomy, wording,
progressive disclosure and accessibility, all built with the existing tokens.

## 13. Five questions, three layers

**Every page serves one of five questions:**
1. What is happening this season? (Are flags up, down or flat?)
2. Where is it happening? (Which teams, penalty types, situations, crews?)
3. Is the difference meaningful? (Bigger than random variation? Comparable groups?)
4. What might it mean? (Field position, scoring, win chance)
5. Can I verify it? (Data, definitions, filters, calculations)

**Every topic has three layers, sharing one set of metric definitions:**
1. **Understand:** the finding, a few key numbers, a plain-English line.
2. **Investigate:** profiles, filters, trends, events, comparisons.
3. **Verify:** raw data, definitions, model documentation, uncertainty,
   provenance, downloads.

A user can start at a headline, drill into a team or crew, open an individual
event and reproduce the statistic.

## 14. Navigation and page map

| Section | Purpose | Current pages that move here |
|---|---|---|
| **Overview** | Latest findings, league snapshot, this week | Home, `/gameday/`, game previews |
| **Teams** | Team rankings, profiles, comparisons | `/team/` |
| **Officials** | Crew profiles, observed and adjusted rates, assignments | `/crew/`, `/assignments/` (placement: D19) |
| **Trends** | Penalty types, quarters, weeks, seasons | `/trends/` |
| **Game impact** | Expected points, win chance, event-level analysis | What Flags Cost |
| **Data & Methods** | Downloads, definitions, models, limitations, data quality | `/dataset/`, `/guide/` |

Existing URLs keep working (redirects). Full history stays reachable from each
section and the explorer (V2.2).

## 15. Home page structure

In this order:
1. **The league at a glance:** flags per game, penalty yards per game, season
   and scope ("2026 regular season, Weeks 1–7"), data-through line.
2. **Start with a question:** four entry cards: Compare teams, Explore
   officials, Track league trends, Understand impact.
3. **Key finding of the week:** one evidence-backed finding with its comparison,
   sample size and a link to the analysis (fed by the stat miner and Growth
   Cadence content).
4. **What changed:** absolute change, comparable baseline, and whether the data
   supports a conclusion.
5. **This week:** games, crew chiefs, projections (already on the home page).
6. **Explore the data:** searchable, sortable table with export and links to
   team, crew and penalty profiles.

## 16. Chart standard

Every chart has, in order:
1. **Headline** stating the question or finding ("Which crews have the most
   observed flags per game this season?"), not just a metric name.
2. **Subtitle** with population, period and inclusion rules, plus the key caveat.
3. **Chart** of the type that fits the task (table below).
4. **Benchmark:** labeled league average or prior period.
5. **Annotation** of important shifts, without implying cause.
6. **Sample size:** games, plays or events used.
7. **Method link:** the ? panel and the dictionary entry.
8. **Data table:** the values behind the chart (also the accessible text version).
9. **Export:** CSV and PNG, carrying the active filters and data version.

| Question | Chart |
|---|---|
| Rankings (teams, crews) | Horizontal bars or dot plots, most flags first, league-average line, sample column; intervals in V2.1b |
| Trends over time | Line chart with comparable baseline; partial periods visibly different (dashed or labeled) |
| Season-over-season change | Diverging dot plot (dumbbell) on a common zero line, absolute change labeled |
| Situational patterns (quarter × type) | Heatmap with denominators; low-volume cells marked |

## 17. Ethical design standard

**Five rules** (every PR touching a page is checked against them):
1. No ranking without a clearly named ranking metric.
2. No percentage change without the baseline and the absolute change.
3. No model estimate presented as a directly observed fact.
4. No critical methodology hidden only behind a tooltip.
5. No title that claims more than the analysis supports.

**Risks to check for, and the fix:**

| Risk | How it misleads | Fix |
|---|---|---|
| Sensational rankings | Most flags reads as "strictest crew" | "Observed" label, sample size, adjusted estimate (V2.1b) |
| Selective time windows | A favorable period makes a team look clean or dirty | Same-weeks default; switching periods is visible |
| Percentage framing | Large % on a tiny change | Absolute and relative together |
| Red/green as judgment | A team or crew reads as good or bad | Red/green means only more/fewer flags; text labels; neutral wording |
| Causal headlines | Association read as proof | Descriptive wording unless the analysis supports a cause |
| Hidden methodology | Users can't tell what a metric means | Short definition beside the metric; dictionary link |
| False precision | Decimals imply certainty | Rounding rules; uncertainty shown |
| Unlabeled sort order | One ordering shapes perception | Sort field named; alternate sorts offered where useful |
| Inconsistent filters | Numbers from different periods compared | Global filters; exceptions labeled |

**Wording checklist** (used in V2.0a step 5 and every later PR): no "strict",
"lenient", "biased", "rigged" or "cost them the game" unless a documented
analysis supports it; "observed" before any raw rate in a ranking; "model
estimate" before any modeled number.

## 18. Accessibility and mobile

1. **Target:** WCAG 2.2 AA. Text contrast checked against the current theme
   tokens (adjust only shades, not the palette, if a token fails).
2. Color is never the only signal (labels, shapes, patterns).
3. Every control is keyboard-operable with a visible focus state.
4. Every chart has a text equivalent and a data table.
5. **Mobile reading order:** finding and period → key numbers → main chart →
   one-line interpretation → expandable detail → full table and export.
6. Tables keep their key columns on phones (name, rate, games) and collapse the
   rest into an expandable row.
7. **Checks:** axe in CI (V2.1), a manual keyboard pass and a phone pass per
   release.

## 19. Three audiences

| Audience | Wants | Gets |
|---|---|---|
| Casual fan | A quick answer: who gets flagged most, are flags up? | Short summary, three or four numbers, plain language, simple selectors, depth optional |
| Journalist or analyst | A defensible, citable finding | Sortable tables, source notes, downloads, baselines and samples, links to games and events, association vs cause stated |
| Researcher or data scientist | To reproduce or challenge a result | Event-level data where licensing allows, formulas, model assumptions, version history, data dictionary, model outputs and uncertainty separate from raw data |

## 20. Measuring whether it works

**Success measures** (define targets after the baseline test):

| Area | Measure |
|---|---|
| Findability | Time to answer common questions |
| Comprehension | % of users who interpret a chart correctly |
| Navigation | Task completion for team, official and trend lookups |
| Data trust | % who can state a metric's definition and period |
| Data quality | Failed checks and unresolved discrepancies per week |
| Performance | Page load time, chart interaction delay |
| Accessibility | WCAG 2.2 AA audit results, keyboard task completion |
| Research use | Successful exports and reproducible queries |

More time on site is not the goal; a correct answer faster is.

**Usability testing:**
1. **Who:** 5–6 people per round (two casual fans, two who write or post about
   football, one or two data-minded). Friends, Reddit or X followers are fine.
2. **Tasks** (same every round):
   1. Which team has the most flags per game this season, and over how many games?
   2. Is this week's crew chief above or below league average, and how sure is that?
   3. Have flags gone up compared with the same weeks last season? By how much?
   4. What does "points given away" mean, and is it observed or estimated?
   5. Download the crew data and say what period it covers.
3. **Method:** screen share or in person; they think aloud; you note time,
   success and wrong interpretations in `docs/usability/round-N.md`.
4. **Rounds:** baseline on the current site (end of V2.0a), round 1 after V2.1,
   round 2 after V2.1b.

---

# Part D: Quant research track

**Purpose:** find out, rigorously, whether officiating data adds information
that betting markets don't already price, and build the most valuable
calculations regardless (they improve the site's projections either way).

**Positioning:** the public site stays analytics ("what this crew means for the
game"), never picks or betting advice. That avoids gambling-promotion and
advertising rules, which vary by state, and protects credibility. Research runs
privately. If any of it is ever published, it includes responsible-gambling
resources.

## 21. Ground rules

1. **Closing line value is the scoreboard.** An edge means our numbers point the
   way the line later moves. Win/loss records over a season are mostly luck.
2. **The bar:** at standard −110 odds, 52.4% is break-even. Report expected value
   after the vig, not hit rate.
3. **Search enough and you'll find false patterns.** Every hypothesis is
   pre-registered (section 25, Q2), tested out of sample, and false-discovery
   adjusted.
4. **No peeking at the future.** Only information available before kickoff
   (the existing `as_of` backtest design is mandatory).
5. **Calibration over accuracy.** Probabilities must mean what they say (log loss,
   Brier score, reliability plots).
6. **Size bets mathematically.** Fractional Kelly; account for correlated bets
   (a total and a team total on the same game are largely one bet).
7. **Expect decay.** Public edges shrink as markets learn; re-test every season.

## 22. Hypotheses: where edges might exist

Ranked by plausibility. Each becomes a pre-registered test in Q2.

| # | Market | Hypothesis | Test |
|---|---|---|---|
| H1 | **Penalty props** (total penalties, penalty yards, team penalties, first-half penalties) | Niche, low-volume markets priced with simpler models than ours | Our projected distribution vs posted line → expected value per prop |
| H2 | **Assignment timing** | Totals lines adjust slowly after crew assignments publish (Tue/Wed) | Line movement from assignment publication to kickoff vs the crew's flag tendency |
| H3 | **Live betting** | Early-game flag pace predicts the rest of the game beyond what live lines assume | Bayesian in-game update of the crew's rate vs live totals |
| H4 | **First-half and team totals** | Less efficient than full-game totals; flags concentrate in Q2 | Crew/team flag effects on first-half scoring vs first-half lines |
| H5 | **Full-game totals** | The net effect of flags on points (more first downs vs clock stops and stalled drives) is mispriced | Regress (actual total − closing total) on projected flags and crew rate, out of sample |
| H6 | **Spreads / home edge** | Least likely; home-bias effects are tiny and heavily studied | Sanity check only |

## 23. Core calculations

1. **Flags → points translation.** Expected points, plays and game time per
   additional expected flag, combining flag cost (expected points per flag) with
   pace (plays per game, clock stoppages). The bridge from our data to totals.
2. **Residual vs market.** Model the gap between the result and the closing line,
   with the line itself as an input. Anything the market already prices shows up
   (correctly) as nothing.
3. **Causal crew effects (natural experiment).** Crews are assigned independently
   of matchups, so crew assignment is close to random: randomization tests and
   matching estimate the causal effect of a crew on penalties, points and home
   results.
4. **Full outcome distributions.** Monte Carlo simulation of each game's flags and
   their point effects → full distributions for props and alternate lines.
5. **Shift detection.** Changepoint detection on every crew and team (Novak 2026)
   to catch real changes early.
6. **Market-efficiency audit.** How much referee information closing lines already
   contain. A "fully priced" result is a finding in itself and redirects research.

## 24. Methods

| Method | Use |
|---|---|
| Hierarchical Bayesian count models (Poisson / negative binomial; crew, team, opponent effects varying over time) | Core flag projections with honest uncertainty, sharing strength across small samples |
| Gradient boosting (LightGBM) on market residuals | Interactions the market misses (weather × crew × team style) |
| Causal inference (randomization inference, matching on assignment) | Separates crew effects from matchup and schedule effects |
| Changepoint detection (CUSUM, Bayesian changepoints) | Early warning on crew and team shifts |
| Self-exciting models (Hawkes processes) | Flag clustering ("chippy games") → live signals |
| Conformal prediction | Guaranteed-coverage ranges for props |
| Calibration (isotonic / Platt) + SHAP explanations | Trustworthy probabilities; why the model leans a way |
| Ensembling (Bayesian + boosting + market-informed) | Usually beats any single model |
| Monte Carlo game simulation | Distributions for props and alternate lines |
| LLMs (Claude) | Not prediction. Extracting structured features from text (officiating emphasis memos, crew roster changes, injury news, weather alerts) and writing narratives from verified facts |

## 25. Research phases (Q0–Q5)

### Q0 Data additions

**Full catalog:** [Data Sources and Data Lake Design](DATA_SOURCES.md) lists every source with coverage, access, license, join keys and priority (P0–P3), plus the lake's zones and id crosswalks.

**Depends on:** V2.0 step 1 (raw capture to R2). Priority order:

1. **Betting lines:** opening, closing, timestamps of movement, and prop lines where available (e.g. The Odds API).
   1. You: create an account at the odds provider, pick the plan that covers NFL game lines + props + historical data, add the key as a GitHub secret `ODDS_API_KEY`.
   2. Me: capture lines every pipeline run (more often Tue–Sun) to `raw/odds/`; backfill available history.
   3. **Done when:** every 2026 game has open/close totals and spreads with movement timestamps.
2. **Full officiating crews** (all seven officials) from nflverse officials data.
3. **Snap counts and participation** (nflverse) → per-snap rates (also needed for V2.1b opportunity-adjusted rates).
4. **Injury reports** (nflverse) → backup offensive linemen and cornerbacks as features.
5. **Rule emphasis memos / points of emphasis** per season (text → features via Claude).
6. **Travel and time zones** (computed from the schedule).

### Q1 Foundations

**Depends on:** Q0 items 1–2.

1. Flags → points translation (calculation 1).
2. Market-efficiency audit (calculation 6).
3. Causal crew effects (calculation 3).
4. **Done when:** a written internal report (Evidence) with each result, its uncertainty and what it implies.

### Q2 Pre-registration

**Depends on:** Q1.

1. For each hypothesis H1–H6 still plausible after Q1, write a one-page pre-registration in `research/prereg/`: market, signal, decision rule, odds source, sample, success criteria (CLV > 0 and positive EV after vig at a false-discovery-adjusted level).
2. Commit before running the test (the commit date is the proof).

### Q3 Walk-forward backtests

**Depends on:** Q2.

1. 2020–2025 walk-forward, pre-game information only; 2026 fully held out.
2. Score: closing line value, EV after vig, calibration, false-discovery-adjusted significance.
3. **Done when:** each pre-registered hypothesis is marked pass / fail with its report.

### Q4 Paper trading

**Depends on:** at least one Q3 pass.

1. 4–8 weeks of logged recommendations in the history ledger (separate private file), recorded before kickoff with the line at the time.
2. **Done when:** CLV stays positive over the paper period.

### Q5 Monitoring

**Depends on:** Q4.

1. Weekly CLV and calibration tracking; alert on decay.
2. Re-run the market-efficiency audit every season.
---

# Part E: How it gets built (solo, Claude Code)

## 26. Working model

1. **Who:** you, with Claude Code running in PowerShell on the ROG Strix laptop.
   This Claude project is for planning, drill-downs and second opinions on a
   plan or a diff.
2. **One step at a time.** One plan step = one GitHub issue = one branch = one
   pull request. Nothing starts until the previous step is merged, unless the
   dependency map (section 34) says the two are independent (V2.0a and V2.0
   step 1).
3. **Plan before code.** Every Claude Code session starts by reading the plan
   section and the issue, then proposing a plan; nothing is edited until you
   approve it.
4. **Checks decide, not confidence.** A step is done when its "Done when" check
   passes, CI is green and you've read the diff.
5. **No home lab, no extra agents.** Everything runs on the laptop, GitHub
   Actions or hosted services. Dagster runs on the laptop while building and in
   the cloud in production.
6. **Slow is fine.** A session is 1–2 hours. Stop at a clean point: committed,
   pushed, or explicitly parked with a note in the issue.

## 27. Session W0: set up the laptop

**Depends on:** nothing. All commands in PowerShell unless noted.

1. **Install the tools** (skip any already installed; check with the version
   commands in step 2):
   1. `winget install --id Git.Git -e` (Claude Code on Windows also needs Git for Windows)
   2. `winget install --id GitHub.cli -e`
   3. `winget install --id Python.Python.3.11 -e` (matches the GitHub Actions workflow)
   4. `winget install --id OpenJS.NodeJS.LTS -e` (needed for Astro in V2.1)
   5. Close and reopen PowerShell so the new commands are found.
2. **Check versions:** `git --version`, `gh --version`, `py -3.11 --version`,
   `node --version` (20 or higher). Each should print a version.
3. **Sign in to GitHub:** `gh auth login` → GitHub.com → HTTPS → Login with a
   web browser. Check: `gh auth status` shows your account.
4. **Set your git identity** (once): `git config --global user.name "Ty Foster"`
   and `git config --global user.email "<your GitHub email>"`.
5. **Get the repo onto the laptop:**
   1. If `C:\Users\tfost\nfl-observatory` exists on this laptop:
      `cd C:\Users\tfost\nfl-observatory`, then `git remote -v` (should show
      `github.com/pipersandman/nfl-observatory`), `git status` (should be clean;
      if not, commit or stash first), `git switch main`, `git pull`.
   2. If not: `cd C:\Users\tfost`, then
      `gh repo clone pipersandman/nfl-observatory`, then `cd nfl-observatory`.
6. **Python environment:**
   1. `py -3.11 -m venv venv` (only if `venv` doesn't exist or uses another version)
   2. `.\venv\Scripts\Activate` (prompt shows `(venv)`)
   3. `pip install -r scripts\requirements.txt`
   4. Check: `python scripts\update_data.py` runs to "DATA UPDATE COMPLETE"
      (don't commit the data it writes; `git restore frontend\data` afterwards).
   5. Check: `python -m http.server 8000 --directory frontend`, open
      http://localhost:8000, the site loads; `Ctrl+C` to stop.
7. **Install Claude Code:** follow the current Windows instructions at
   docs.claude.com (Claude Code → Setup), sign in with your Claude account, then
   in the repo folder run `claude` and confirm it starts. Type `/exit` to quit.
8. **Credentials:** a Bitwarden folder "NFL Observatory" for every account and
   token in section 30. Secrets never go in the repo or into a Claude Code
   prompt.
9. **Done when:** all checks in steps 2, 3, 6 and 7 pass.

## 28. Session W1: repository conventions

**Depends on:** W0. Run through the routine in section 29 (issue → branch →
Claude Code → PR).

1. **Claude Code: `CLAUDE.md`** at the repo root, covering:
   1. What the project is; where the plan lives (`docs/V2_BUILD_PLAN.md`).
   2. Commands on Windows: activate venv, run the pipeline, run the local
      server, run the checks (step 3).
   3. Rules: never commit secrets or `.env`; never hand-edit `frontend/data/`
      (it's generated); penalties-per-game charts sorted most first; theme rules
      (section 12); the ethical design standard (section 17); every new number
      gets a dictionary entry; plan first, edit after approval.
2. **Claude Code: current-state inventory**
   1. `docs/architecture/current-state.md`: pipeline scripts and what each
      produces, site files, workflows, secrets *by name only*, dependencies,
      deploy flow, known gaps.
   2. `docs/architecture/baseline-YYYY-MM-DD.json`: league flags per game per
      season, every crew's 2026 rate, team ranks, scorecard summary (the numbers
      later stages must match).
   3. You: read both and correct anything wrong.
3. **Claude Code: checks**
   1. Ruff (lint/format) and pre-commit.
   2. `scripts/check.py`: one cross-platform command that runs everything CI
      runs (`python scripts\check.py` locally, same on Linux in Actions).
   3. A CI job in `.github/workflows/checks.yml` running it on every pull request.
4. **Claude Code: templates**
   1. `.github/ISSUE_TEMPLATE/step.md`: the task card (section 29, step 1).
   2. `.github/pull_request_template.md`: what changed, how it was checked
      (commands and results), numbers before/after where data is touched,
      section 17 checklist ticked for page changes, open questions.
   3. `docs/adr/` with a template and ADR-0001 recording the decisions in
      section 33.
5. **You: protect `main` (basic).** GitHub → repo **Settings → Rules →
   Rulesets → New branch ruleset** → target `main` → tick **Restrict
   deletions** and **Block force pushes** only → **Create**. Leave "Require a
   pull request" and "Require status checks" off: the data bot pushes to
   `main` with the workflow's `GITHUB_TOKEN`, which can't be a ruleset bypass
   actor, so those rules would block its commits. Full protection (pull
   request and the `checks` job required) needs a GitHub App for the bot to
   push as, added as the bypass actor; tracked as its own issue.
6. **Done when:** the ruleset is active on `main` with those two rules, and the
   next automated "Update NFL data" commit still lands on `main`.

## 29. The routine for every step

1. **Issue.** GitHub → **Issues → New issue → Step** template, filled in:
   - **Goal** and **why** (link to the plan section)
   - **Depends on** (issues that must be merged first)
   - **Files** expected to change
   - **Done when** (commands and expected results, numbers where data is involved)
   - **Stop and ask if** (ambiguity, a check that fails for an unclear reason,
     needing a secret or a new account, more than two sessions of work)
2. **Branch.** In PowerShell, in the repo:
   `git switch main` → `git pull` → `git switch -c step/<issue#>-<short-name>`
   (e.g. `step/12-metric-inventory`).
3. **Start Claude Code:** `.\venv\Scripts\Activate`, then `claude`. First prompt:
   > Read CLAUDE.md, docs/V2_BUILD_PLAN.md section <N>, and issue #<n> (`gh issue view <n>`).
   > Propose a step-by-step plan with the files you'll change and how you'll
   > check it. Don't edit anything until I approve.
4. **Approve or adjust the plan.** Ask for smaller steps if any part is unclear.
5. **Build.** Let Claude Code work; approve each command it asks to run (keep the
   default permission mode; never use the skip-permissions option). If it asks
   for a secret, stop: add it to GitHub secrets or `.env` yourself.
6. **Check locally:** `python scripts\check.py`; for page changes, run the
   local server and look at the changed pages on desktop and a narrow window.
7. **Commit and open the PR:** ask Claude Code to commit with a clear message,
   then `git push -u origin HEAD` and `gh pr create --fill`. Fill the PR
   template.
8. **Review:** wait for CI to pass; read the diff on GitHub (**Files changed**).
   Optional: paste the diff summary into this project for a second look.
9. **Merge:** **Merge pull request → Confirm merge → Delete branch**. Then locally:
   `git switch main` → `git pull`.
10. **Close out:** close the issue; mark the step done in this plan (or in a
    GitHub Project board); record any decision in section 33.

## 30. Accounts, created when needed

Create each one only when its step arrives. Store every login and token in
Bitwarden; put tokens the pipeline needs in GitHub Actions secrets (and `.env`
locally, never committed).

| Account / token | When | Notes |
|---|---|---|
| GitHub | Have | Ruleset in W1 |
| Claude (Claude Code) | Have | Sign in during W0 |
| Cloudflare: R2 bucket + API token | V2.0 step 1 | Existing account; secrets `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT` |
| Odds data provider (e.g. The Odds API) | Q0 item 1 | Secret `ODDS_API_KEY`; plan choice is D5 |
| DigitalOcean (or Dagster+) | V2.0 step 4 deploy | D3; set a billing alert |
| Sentry | V2.1 | Free tier; public DSN only in the site |
| Uptime monitor (UptimeRobot or Better Stack) | V2.1 cutover | Free tier; alerts to the project email |
| Cloudflare Pages + DNS move from HostGator | V2.1 cutover | Keep HostGator live until two clean weeks |
| Supabase | V2.3 | Free tier at launch |
| Anthropic API console | V2.4 | Separate from your Claude plan; set a monthly spend limit |

## 31. Stage gates

| Stage | Must pass before the next stage |
|---|---|
| W0–W1 | Laptop checks pass; `main` ruleset active (restrict deletions, block force pushes); data bot still commits. Pull request and `checks` protection follow with a GitHub App (own issue) |
| V2.0a | Every published number in the dictionary; conflicts resolved; recompute check matches JSON; section 17 checklist passes on every page; baseline usability test done |
| V2.0 | Zero-difference reconciliation with current JSON; data-quality checks blocking; two parallel weeks |
| V2.0b | Backtest on 2015–25 detects known shifts; false-discovery control on every item; evidence plays attached |
| V2.1 | Page parity; Lighthouse ≥ 90; axe clean of serious issues; usability round 1 ≥ baseline; post-cutover indexing checks |
| V2.1b | Interval coverage checked on held-out games; observed/adjusted/uncertainty on every comparison; usability round 2 |
| V2.2 | 20 cross-surface numeric checks; read-only API rate limits tested |
| V2.3 | User isolation, access-control and sharing tests |
| V2.4 | 200-question test ≥ 95% exact numeric match; first 100 real questions reviewed, no wrong numbers |
| Q0–Q5 | Pre-registration; no lookahead; held-out tests; uncertainty and calibration checks |

## 32. Security and cost controls

1. Secrets live only in Bitwarden, GitHub Actions secrets and a local `.env`
   listed in `.gitignore`. Never pasted into Claude Code, issues or PRs.
2. Tokens are scoped to what they need (R2 token to one bucket; API keys
   read-only where possible) and rotated if exposed.
3. Production deploys run only from GitHub Actions after a merge to `main`.
4. Claude Code runs in its default permission mode; you approve commands.
5. Spend limits in every paid console (DigitalOcean billing alert, odds
   provider plan, Anthropic API monthly cap).
6. No public ports or self-hosted services; nothing runs on home-lab machines.

---

# Shared

## 33. Decisions log

Record each decision here (and as an ADR in `docs/adr/` from W1).

| # | Decision | Status | Date |
|---|---|---|---|
| D1 | Public site framework: Astro (vs Observable Framework, SvelteKit) | Proposed | — |
| D2 | Orchestrator: Dagster (vs Prefect) | Proposed | — |
| D3 | Orchestrator hosting: DigitalOcean droplet vs Dagster+ serverless | Open (V2.0 step 4) | — |
| D4 | Public API: FastAPI vs Datasette | Open | — |
| D5 | Odds data provider and plan | Open | — |
| D6 | Research results public or private | Private by default | — |
| D7 | Cloudscape: internal tools only, not the public site | Decided | Oct 2026 |
| D8 | Text-to-SQL: Claude tool use over semantic layer (not Vanna, archived) | Decided | Oct 2026 |
| D9 | Build method: solo, Claude Code on the ROG Strix laptop, one step per issue/branch/PR | Decided | Oct 2026 |
| D10 | No home-lab infrastructure for V2 for now; hosted services only | Decided | Oct 2026 |
| D11 | AI agent delivery system (old V2.-1: parallel agents, Codex reviewer, Herdr, orchestrators) removed | Decided | Oct 2026 |
| D12 | Trust fixes (V2.0a) ship on the current site before the redesign | Proposed | — |
| D13 | Small-sample threshold for the label (games per crew-season, team weeks) | Open (V2.0a step 3) | — |
| D14 | Public uncertainty display: interval level (90% vs 95%) and model source | Open (V2.1b) | — |
| D15 | R2 raw capture starts right after W1, in parallel with V2.0a | Proposed | — |
| D16 | Visual design: keep the Penalty Flag theme; audit's palette and typography not adopted | Decided | Oct 2026 |
| D17 | Uptime monitoring: hosted free tier instead of self-hosted Uptime Kuma | Proposed | — |
| D18 | Analytics: keep Cloudflare Web Analytics (Plausible optional later) | Proposed | — |
| D19 | Where assignments and Gameday live in the six-section navigation | Open (V2.1) | — |

## 34. Dependency map

```
W0 Laptop ──► W1 Conventions ──┬──► V2.0a Trust fixes (current site) ──────────────┐
                               │                                                    ▼
                               └──► V2.0 Data platform ──► V2.0b Stat miner    V2.1 Astro site + new structure
                                    (step 1 R2 capture         patterns              │
                                     starts immediately)                             ▼
                                         │                                     V2.1b Fair comparisons ◄── Q0 item 3 (snaps)
                                         │                                           │                  + hierarchical model
                                         │                                           ▼
                                         │                       V2.2 Explorer/API/search ──► V2.3 Accounts ──► V2.4 Ask the Observatory
                                         │
                                         └──► Q0 Data additions (odds, full crews, snaps, injuries) ──► Q1 Foundations ──► Q2 Prereg ──► Q3 Backtests ──► Q4 Paper ──► Q5 Monitor
                                                                     │
                                                                     └──► improves site projections (model v2) regardless of betting results
Growth Cadence Phase 1 runs throughout; its Phase 2 items land in V2.1.
```

## 35. Costs

| Item | Monthly |
|---|---|
| Cloudflare (Pages, Workers, R2 at our size; Web Analytics free) | $0–5 |
| DigitalOcean droplet for Dagster (or Dagster+) | ~$6–12 |
| Odds data provider | depends on plan (historical + props tiers cost more; D5) |
| Sentry, uptime monitor (free tiers) | $0 |
| Supabase (free tier at launch) | $0 |
| Claude API for Ask the Observatory | usage-based; capped |
| Claude Code | covered by your Claude plan |
| **Total excluding odds data** | **~$6–20** |
