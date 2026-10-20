# V2 Build Plan: Architecture, Quant Research and AI Delivery

**What this covers:** what V2 is (the platform, tools and sequence a
professional team would use), the quantitative research track (what we
measure, which models we use, and how any betting-related edge is tested), and
how it gets built (an AI engineering delivery system with isolated agents,
independent review and human approval).

**Start here:** Part C, section 12 (V2.-1 setup, Session 0) is the first thing
to build. V2.0's R2 raw capture can start alongside it.

**Related docs:**
[Data & Modeling Roadmap](DATA_AND_MODELING_ROADMAP.md) (data platform and
models) · [Growth Cadence Plan](GROWTH_CADENCE_PLAN.md) (weekly publishing and
indexing; Phase 1 now, Phase 2 overlaps with this plan).

**How to use this doc:** each step lists what it depends on, its micro-steps
and how to confirm it's done. Any step can be drilled into further before
building. Decisions are recorded in section 16.

---

## Contents

**Part A: Architecture**
1. [Principles](#1-principles)
2. [Target architecture](#2-target-architecture)
3. [Stack by layer](#3-stack-by-layer)
4. [Migration sequence (V2.0–V2.4)](#4-migration-sequence-v20v24)

**Part B: Quant research track**
5. [Ground rules](#5-ground-rules)
6. [Hypotheses: where edges might exist](#6-hypotheses-where-edges-might-exist)
7. [Core calculations](#7-core-calculations)
8. [Methods](#8-methods)
9. [Research phases (Q0–Q5)](#9-research-phases-q0q5)

**Part C: AI engineering delivery system (V2.-1)**
10. [Roles and boundaries](#10-roles-and-boundaries)
11. [Tools and runtime](#11-tools-and-runtime)
12. [V2.-1 setup sequence](#12-v2-1-setup-sequence)
13. [Agent task protocol](#13-agent-task-protocol)
14. [Phase ownership and gates](#14-phase-ownership-and-gates)
15. [Hosting, security and cost controls](#15-hosting-security-and-cost-controls)

**Shared**
16. [Decisions log](#16-decisions-log)
17. [Dependency map](#17-dependency-map)
18. [Costs](#18-costs)

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
   comparison," "points given away" are defined once (the semantic layer) and
   used by the site, the API and the AI alike.
4. **Static and fast by default.** Pages are HTML first; interactivity is added
   only where it helps. This is also what search engines and AI assistants read.
5. **Open source and low cost.** Prefer permissive licenses (MIT, Apache 2.0)
   and free tiers; avoid tools that need commercial licenses for a public
   website.
6. **Every change is reviewable.** Code, data definitions, dashboards and
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
   WAREHOUSE       DuckDB  +  dbt Core  (clean tables, tests, metric definitions)
                                             ▼
   SEMANTIC LAYER  dbt models / metrics: the single definition of every number
          ┌──────────────────────┬──────────────────────┬──────────────────────┐
          ▼                      ▼                      ▼                      ▼
   MODELS & RESEARCH      PUBLIC SITE            PUBLIC API             ASK THE OBSERVATORY
   Bambi/PyMC, LightGBM,  Astro (static pages    FastAPI or Datasette   Claude + tool use over
   MLflow tracking,       + interactive islands, (read-only JSON, CSV)  semantic-layer views only,
   ledger + scorecard     DuckDB-WASM explorer,                         read-only, row limits,
                          Pagefind search)                              accuracy test set
          │                      │                      │                      │
          └────────── Cloudflare Pages · Workers · Cron Triggers · R2 ─────────┘
                       Supabase (accounts, saved searches, feature requests)
                       Sentry · Uptime Kuma · Plausible/Umami
```

## 3. Stack by layer

| Layer | Choice | Alternative | Why |
|---|---|---|---|
| Orchestration | **Dagster** (open source; on a small DigitalOcean server, or Dagster+ serverless) | Prefect | Our pipeline is a set of data assets (play-by-play, crews, projections, ledger); Dagster models assets directly, with lineage and built-in data-quality checks, and integrates with dbt |
| Raw storage | **Cloudflare R2**, Parquet, append-only | AWS S3 | Already planned in the roadmap; no egress fees; same vendor as hosting |
| Warehouse | **DuckDB** | MotherDuck (hosted DuckDB) when live queries need it | Fast, free, file-based; no database server |
| Transformations + metrics | **dbt Core** with dbt-duckdb | SQLMesh | Tested, version-controlled definitions; the single source of truth |
| Data quality | dbt tests + Dagster asset checks + **Pandera** (Python frames) | Great Expectations, Soda | Every run validates before anything publishes |
| Modeling | **Bambi/PyMC** (hierarchical), **LightGBM**, scikit-learn | brms (R) | Calibrated count models + interaction-finding models |
| Experiment tracking | **MLflow** | Weights & Biases | Every model version, its features and its scorecard results recorded; registry for champion/challenger |
| Public site | **Astro** (MIT; maintained by Cloudflare since Jan 2026) | Observable Framework; SvelteKit | Static HTML by default with interactive islands; real URL for every page; first-class on Cloudflare. Replaces `build_static.py` and `#` links |
| UI components | Our design tokens + headless components (Radix or Ark UI; Bits UI if Svelte islands) + **Storybook** | — | Accessible behavior without someone else's look. Cloudscape rejected for the public site (AWS look, React-only, Highcharts license for charts) |
| Charts | **Observable Plot** (most charts), **Vega-Lite** (AI-generated charts), Chart.js during migration | Apache ECharts | Plot for concise publication-quality charts; Vega-Lite specs are plain JSON the AI can produce and we can validate before drawing |
| In-browser data explorer | **DuckDB-WASM** + Parquet | — | Filter and slice all data instantly, no server |
| Site search | **Pagefind** | — | Full-text static search, zero server cost |
| Public API | **FastAPI** (reuses Python code) or **Datasette** (instant read-only API + SQL explorer) | — | Journalists and developers; backlinks |
| Accounts + user data | **Supabase** (open-source Postgres + auth) | Clerk + Neon | Saved searches and visualizations, feature requests |
| Ask the Observatory | **Claude with tool use** over semantic-layer views | — | Vanna (open-source text-to-SQL) is archived; building on our own definitions is safer and more accurate |
| Internal analytics | **Evidence** (SQL + Markdown → static reports) | Quarto | Fast internal reports (weekly scorecard, research write-ups); brand doesn't matter internally |
| Internal admin console | Cloudscape *or* plain Astro pages | — | Pipeline runs, data-quality status, narrative review queue, indexing status. Cloudscape's look is fine for private tools |
| Hosting | **Cloudflare Pages + Workers + Cron Triggers**; one DigitalOcean droplet for Dagster | AWS (S3, Lambda, ECS) later, as a learning path | Global CDN, instant deploys, Crawler Hints (automatic IndexNow) once DNS moves to Cloudflare |
| Monitoring | **Sentry** (errors), **Uptime Kuma** (uptime), **Plausible** or **Umami** (analytics) | PostHog | Lightweight, privacy-friendly |
| Engineering hygiene | GitHub Actions, Playwright, Lighthouse CI, Ruff, pre-commit, architecture decision records in `docs/adr/` | — | Keeps the codebase healthy as it grows |

## 4. Migration sequence (V2.0–V2.4)

**Rule for every stage:** the old path keeps running until the new one has
matched its output for two consecutive weeks.

### V2.0 Data platform (time-sensitive; start first)

**Depends on:** you creating the Cloudflare R2 bucket and an API token.

1. **R2 bucket and raw capture**
   1. You: Cloudflare dashboard → **R2** → **Create bucket** → name `nflobs-raw` → **Create**.
   2. You: **R2** → **Manage API tokens** → **Create API token** → permission **Object Read & Write**, bucket `nflobs-raw` → copy the Access Key ID, Secret and endpoint.
   3. You: GitHub repo → **Settings → Secrets and variables → Actions** → add `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`.
   4. Me: every pipeline run writes raw pulls (play-by-play, schedules, officials, assignments, weather, betting lines) to `raw/<source>/<date>/` as Parquet, never overwritten.
   5. **Done when:** a week of runs is in R2 and a script can rebuild any past week's site data from raw files alone.
2. **DuckDB + dbt**
   1. dbt project in `warehouse/` with sources (raw), staging (cleaned), marts (games, penalties, crews, teams, projections, ledger).
   2. Metric definitions (flags per game, same-weeks comparison, points given away) as dbt models with tests.
   3. **Done when:** dbt's output matches the current JSON numbers exactly for every 2026 week (diff report = zero differences).
3. **Dagster**
   1. One asset per source and per mart; schedules match the Growth Cadence Plan (Tue polling, Thu previews, Mon/Tue recaps, daily).
   2. Asset checks: row counts, no duplicate plays, every played game has a crew, totals reconcile.
   3. Runs on a DigitalOcean droplet (or Dagster+); GitHub Actions remains the deploy step.
   4. **Done when:** Dagster has produced the site's data for two weeks with zero manual fixes, and GitHub Actions only builds and deploys.

### V2.1 Astro site

**Depends on:** V2.0 step 2 (marts as the data source).

1. Astro project in `site/`; design tokens and components ported from `styles.css`; Storybook catalog.
2. Build order: static pages (crew, team, assignments, trends, guide, dataset) → Growth Cadence pages (previews, report cards, team-week, live facts) → home page with interactive islands.
3. Clean URLs (`/crew/scott-novak/`) for everything; old `#crew=` links redirect on load.
4. Move hosting to Cloudflare Pages; DNS to Cloudflare; turn on Crawler Hints.
5. **Done when:** every current page has an Astro equivalent, Lighthouse scores ≥ 90, and Search Console shows no new errors two weeks after cutover.

### V2.2 Explorer, API, search

**Depends on:** V2.1.

1. DuckDB-WASM explorer page over Parquet exports (filter by crew, team, season, week, penalty type).
2. Public read-only API (FastAPI on Workers-compatible hosting, or Datasette) with rate limits; documented on `/dataset/`.
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
2. Charts returned as Vega-Lite specs, validated before rendering.
3. Accuracy test set of 200 questions with known answers; launch only at ≥ 95% exact-match on numbers.
4. Every answer cites the views it used; saved answers become shareable, indexable pages.
5. **Done when:** the test set passes and the first 100 real questions are reviewed with no wrong numbers.

---

# Part B: Quant research track

**Purpose:** find out, rigorously, whether officiating data adds information
that betting markets don't already price, and build the most valuable
calculations regardless (they improve the site's projections either way).

**Positioning:** the public site stays analytics ("what this crew means for the
game"), never picks or betting advice. That avoids gambling-promotion and
advertising rules, which vary by state, and protects credibility. Research runs
privately. If any of it is ever published, it includes responsible-gambling
resources.

## 5. Ground rules

1. **Closing line value is the scoreboard.** An edge means our numbers point the
   way the line later moves. Win/loss records over a season are mostly luck.
2. **The bar:** at standard −110 odds, 52.4% is break-even. Report expected value
   after the vig, not hit rate.
3. **Search enough and you'll find false patterns.** Every hypothesis is
   pre-registered (section 9, Q2), tested out of sample, and false-discovery
   adjusted.
4. **No peeking at the future.** Only information available before kickoff
   (the existing `as_of` backtest design is mandatory).
5. **Calibration over accuracy.** Probabilities must mean what they say (log loss,
   Brier score, reliability plots).
6. **Size bets mathematically.** Fractional Kelly; account for correlated bets
   (a total and a team total on the same game are largely one bet).
7. **Expect decay.** Public edges shrink as markets learn; re-test every season.

## 6. Hypotheses: where edges might exist

Ranked by plausibility. Each becomes a pre-registered test in Q2.

| # | Market | Hypothesis | Test |
|---|---|---|---|
| H1 | **Penalty props** (total penalties, penalty yards, team penalties, first-half penalties) | Niche, low-volume markets priced with simpler models than ours | Our projected distribution vs posted line → expected value per prop |
| H2 | **Assignment timing** | Totals lines adjust slowly after crew assignments publish (Tue/Wed) | Line movement from assignment publication to kickoff vs the crew's flag tendency |
| H3 | **Live betting** | Early-game flag pace predicts the rest of the game beyond what live lines assume | Bayesian in-game update of the crew's rate vs live totals |
| H4 | **First-half and team totals** | Less efficient than full-game totals; flags concentrate in Q2 | Crew/team flag effects on first-half scoring vs first-half lines |
| H5 | **Full-game totals** | The net effect of flags on points (more first downs vs clock stops and stalled drives) is mispriced | Regress (actual total − closing total) on projected flags and crew rate, out of sample |
| H6 | **Spreads / home edge** | Least likely; home-bias effects are tiny and heavily studied | Sanity check only |

## 7. Core calculations

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

## 8. Methods

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

## 9. Research phases (Q0–Q5)

### Q0 Data additions

**Depends on:** V2.0 step 1 (raw capture to R2). Priority order:

1. **Betting lines:** opening, closing, timestamps of movement, and prop lines where available (e.g. The Odds API).
   1. You: create an account at the odds provider, pick the plan that covers NFL game lines + props + historical data, add the key as a GitHub secret `ODDS_API_KEY`.
   2. Me: capture lines every pipeline run (more often Tue–Sun) to `raw/odds/`; backfill available history.
   3. **Done when:** every 2026 game has open/close totals and spreads with movement timestamps.
2. **Full officiating crews** (all seven officials) from nflverse officials data.
3. **Snap counts and participation** (nflverse) → per-snap rates.
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

# Part C: AI engineering delivery system (V2.-1)

**What this is:** how V2 gets built. A small team of AI coding agents does the
implementation, each in isolation, with independent review and human approval
for anything that ships. This governs the *building* of V2; it does not replace
Dagster (production data orchestration) or the public-site architecture.

**Stage name:** V2.-1, because it comes before V2.0.

## 10. Roles and boundaries

| Role | Who | Does | Never does |
|---|---|---|---|
| **Product owner** | You | Sets priorities; approves architecture decisions, credentials, spending and production releases | — |
| **Lead architect** | Claude (in this project or Claude Code) | Reads the repo, breaks work into scoped tasks, defines interfaces and acceptance criteria, drafts decision records | Merges or deploys |
| **Builders** | Claude Code sessions | Implement one scoped task each, in their own Git worktree and branch; data-platform, site and API tasks run in parallel only when their interfaces are stable | Touch files outside the task's allowed paths |
| **Independent reviewer** | Codex (a different model family from the builder) | Reviews each change; runs regression and security tests; challenges data and statistical assumptions | Approves its own or another agent's work for production. *A second model reviewing is a check, not proof of correctness; tests and numbers decide* |
| **Quant research agent** | Claude Code session scoped to `research/` | Implements experiments, records uncertainty | Runs tests that weren't pre-registered (Part B, Q2), uses held-out data |
| **Documentation agent** | Claude Code session scoped to `docs/` | Updates READMEs, decision records, runbooks and changelogs from merged code | Documents unmerged or unverified results |
| **Release coordinator** | Claude (summary) + you (decision) | Summarizes CI, parity checks, staging, rollback plan and approval status | Deploys without your approval |

## 11. Tools and runtime

| Need | Baseline (start here) | Candidates to pilot | Notes |
|---|---|---|---|
| Task tracking | **GitHub Issues + Projects** | Built into ComposioHQ agent-orchestrator / Stoneforge | Every task is an issue using the task contract (section 13) |
| Isolation | **Git worktrees** (one per task) + a dedicated agent machine | Containers per agent (Docker) | No two agents ever share a writable working directory |
| Agent sessions | Claude Code and Codex CLIs in separate terminals | **Herdr**: persistent, agent-aware terminal workspaces; shows which agent is working, blocked or done; survives disconnects; SSH remote; CLI/socket API. Rust, **AGPL-3.0** (fine for internal use). macOS/Linux, so on Windows run it under **WSL2** or on the ThinkCentre | Adopt only after a pilot (decision D11) |
| Coordination | You + the lead architect assigning issues | **ComposioHQ agent-orchestrator** (spawns agents in isolated worktrees, routes CI failures and review comments back to the agent), **Stoneforge** (Apache 2.0; dispatch, worktree isolation, merge automation), **Overstory** | The draft named "orchestratr"; no project by that name could be found. Use one of these or stay on the baseline (D11) |
| CI | **GitHub Actions** (existing) | — | Required checks on every PR (section 13, step 5) |
| Production data | **Dagster** (Part A) | — | Unaffected by any of the above |

**Permissions (non-negotiable):**
1. Agents get **read-only** production data access and **least-privilege** development tokens (fine-grained GitHub token scoped to this repo, no admin).
2. **No autonomous changes** to DNS, billing, secrets, GitHub settings, or production datasets.
3. The agent machine never holds production deploy credentials (HostGator FTP, Cloudflare account tokens); deploys run only from GitHub Actions after you merge.
4. Agents never see secrets in plain text; secrets live in GitHub Actions secrets and a local `.env` excluded from git.

## 12. V2.-1 setup sequence

Each session is about 1–2 hours. **You** steps are clicks and approvals; **Agent** steps are run by Claude Code with you watching.

### Session 0: Agent machine and accounts

**Depends on:** nothing.

1. **You: pick the machine.** The ThinkCentre (Linux) is the cleaner choice; your Windows PC works with WSL2. Keep the Raspberry Pi for other services.
2. **You: if using Windows,** open PowerShell as administrator → `wsl --install` → restart → finish the Ubuntu setup (username and password).
3. **You: install the basics** on the agent machine (in the Ubuntu/Linux terminal):
   1. `sudo apt update && sudo apt install -y git gh python3-venv python3-pip`
   2. Node.js 20+ (needed by both CLIs): `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs`
4. **You: sign in to GitHub:** `gh auth login` → GitHub.com → HTTPS → login with a web browser.
5. **You: install Claude Code** and sign in (follow the current instructions at docs.claude.com for Claude Code), then run `claude` once to confirm it starts.
6. **You: install Codex CLI** and sign in (follow OpenAI's current Codex CLI instructions), then run `codex` once to confirm.
7. **You: clone the repo into a dedicated folder:** `mkdir -p ~/agents && cd ~/agents && git clone https://github.com/pipersandman/nfl-observatory.git main`
8. **Done when:** `claude`, `codex`, `gh auth status` and `git -C ~/agents/main status` all work.

### Session 1: Current-state inventory

**Depends on:** Session 0.

1. **Agent (lead architect):** inventory the repo: pipeline scripts and what each produces, site files, tests, workflows, secrets *by name only*, dependencies, deploy flow.
2. **Agent:** record baseline numbers to compare against later (league flags per game per season, every crew's 2026 rate, team ranks, scorecard summary) in `docs/architecture/baseline-YYYY-MM-DD.json`.
3. **Agent:** write `docs/architecture/current-state.md` (diagram + file map + data flow + known gaps).
4. **You:** read it and correct anything wrong.
5. **Done when:** the inventory is merged through a PR.

### Session 2: Repository conventions

**Depends on:** Session 1.

1. **Agent:** add `AGENTS.md` (instructions any coding agent reads: setup, test commands, allowed paths per role, "never" list from section 13) and `CLAUDE.md` (Claude Code specifics; points to `AGENTS.md`).
2. **Agent:** add `docs/adr/` with a template and ADR-0001 recording decisions D1–D15.
3. **Agent:** add `.github/ISSUE_TEMPLATE/agent-task.md` (the task contract, section 13) and `.github/pull_request_template.md` (test evidence, diff summary, assumptions, open questions).
4. **Agent:** add Ruff + pre-commit and a `make test` (or `scripts/test.sh`) that runs everything CI runs.
5. **You:** GitHub → repo **Settings → Branches → Add branch ruleset** for `main`: require a pull request, require status checks (the CI job), block force pushes. (The data bot's daily commit needs an exception: add GitHub Actions as a bypass actor.)
6. **Done when:** conventions are merged and a test PR can't merge without passing CI.

### Session 3: Isolated environments and budgets

**Depends on:** Session 2.

1. **Agent:** script `scripts/agent-worktree.sh <issue-number>` that creates `~/agents/wt-<issue>` on branch `agent/<issue>-<slug>` from latest `main`.
2. **You:** create a **fine-grained GitHub token** (github.com → Settings → Developer settings → Fine-grained tokens): repository `nfl-observatory` only; Contents read/write, Pull requests read/write, Issues read/write; nothing else; 90-day expiry. Store it in the agent machine's credential store, never in the repo.
3. **You:** set spending limits: in the Anthropic and OpenAI consoles (or plans), a monthly cap; note the per-task budget in `AGENTS.md` (e.g. stop and ask if a task exceeds 2 hours or the set cost).
4. **Agent:** logging: every agent session writes a summary to the PR (what it ran, test results, time spent).
5. **Done when:** two worktrees can run at once without touching each other, and the token can't access other repos or settings.

### Session 4: Pilot one small task end to end

**Depends on:** Session 3.

1. **You + lead architect:** pick a noncritical task (suggestion: add unit tests for `scripts/weeks.py` and fix anything they reveal).
2. **Agent (builder):** implement in its own worktree; open a PR using the template.
3. **Agent (reviewer, Codex):** review the PR: logic, tests, edge cases; comment on the PR.
4. **Builder:** address comments; CI passes.
5. **You:** review and merge.
6. **Done when:** one full issue → isolated build → independent review → green CI → your merge cycle completes, with no credentials exposed.

### Session 5 (optional): Pilot Herdr and/or an orchestrator

**Depends on:** Session 4.

1. **Agent:** install Herdr on the agent machine (Linux/WSL2); run builder and reviewer in two panes on a second small task.
2. **Agent:** optionally trial one coordinator (ComposioHQ agent-orchestrator or Stoneforge) on a third small task.
3. **You + lead architect:** compare against the baseline: did it save time, did it stay within permissions, is it maintained? Record the decision (D11).
4. **Done when:** D11 is decided (adopt / keep baseline).

### Session 6: Authorize V2.0

**Depends on:** Session 4 (Session 5 optional).

1. **Lead architect:** confirm reproducible setup instructions, reliable logs, and a written recovery procedure (how to roll back a bad merge; how to restore data from the history ledger and R2).
2. **You:** approve starting V2.0.

**V2.-1 exit criteria:** one complete issue → isolated build → independent review → green CI → human-approved merge; no exposed credentials; setup reproducible from the docs.

**Exception (time-sensitive):** V2.0 step 1, **R2 raw capture**, may start before V2.-1 finishes. It's append-only, doesn't touch the site, and every week without it is history we can't recover (decision D15).

## 13. Agent task protocol

**Task contract** (every issue has all of these):
- **Goal** and **why**
- **Inputs:** files, data and docs to read
- **Allowed paths:** where the agent may write
- **Depends on:** issues that must merge first
- **Outputs:** files or changes expected
- **Acceptance tests:** commands and expected results (including numeric parity where data is involved)
- **Escalate when:** conditions where the agent stops and asks (ambiguity, a failing check it can't explain, needing a secret, exceeding the budget)

**Flow:**
1. Lead architect creates the issue with the contract.
2. Only dependency-ready issues are assigned; the builder gets its own worktree and minimum permissions.
3. Builder commits, then opens a PR with test evidence, diff summary, assumptions and open questions.
4. Independent reviewer checks logic, data sources, security, numerical outputs and reproducibility.
5. CI runs Ruff, unit and integration tests, dbt tests, Playwright, Lighthouse where relevant, and dependency scans.
6. You review release-sensitive changes and approve the merge; failures go back to the builder.
7. The documentation agent updates docs and the decisions log after merge.

**Never allowed:** an agent approving its own work; silent edits to production data; publishing unverified numbers; unreviewed infrastructure changes; unrestricted shell or network access while running untrusted code.

## 14. Phase ownership and gates

| Phase | Builder focus | Independent gate (must pass before the next phase) |
|---|---|---|
| V2.-1 | Conventions, worktrees, pilot | One full reviewed, CI-green, human-merged cycle |
| V2.0 | R2 snapshots; DuckDB/dbt marts; Dagster assets | Zero-difference metric reconciliation; two parallel weeks |
| V2.1 | Astro pages, design system, redirects | Page parity; Lighthouse ≥ 90; post-cutover indexing checks |
| V2.2 | Explorer, API, Pagefind | 20 cross-surface numeric checks; read-only API security review |
| V2.3 | Supabase auth and saved work | User isolation, access-control and sharing tests |
| V2.4 | Claude metric tools, Vega-Lite rendering | 200-question test ≥ 95% exact numeric match; first 100 real questions reviewed, no wrong numbers |
| Q0–Q5 | Data sourcing, experiments, reproducible reports | Pre-registration; no lookahead; held-out tests; uncertainty and calibration checks |

## 15. Hosting, security and cost controls

1. **Agent machine:** your development PC (via WSL2) or one dedicated ThinkCentre. Keep the Raspberry Pi for other services. Use hosted model APIs; don't run local model inference on the small machines.
2. **Network:** keep any agent dashboards (Herdr, orchestrators) off public ports; reach them over SSH or a private network (Tailscale or similar). Encrypt the disk; back up the agent machine's config (not secrets) to the repo or a private backup.
3. **Isolation from production:** production Cloudflare, DigitalOcean and HostGator accounts are never logged in on the agent machine.
4. **Cost tracking,** separately:
   - (a) agent model usage (Claude, Codex)
   - (b) agent tooling infrastructure (if any)
   - (c) CI and development hosting
   - (d) production services and odds data
5. **Budgets:** monthly caps in each provider console, a per-task budget in `AGENTS.md`, and a rule that any loop running past its budget stops and escalates.

---

# Shared

## 16. Decisions log

Record each decision here (and as an ADR in `docs/adr/` once V2 starts).

| # | Decision | Status | Date |
|---|---|---|---|
| D1 | Public site framework: Astro (vs Observable Framework, SvelteKit) | Proposed | — |
| D2 | Orchestrator: Dagster (vs Prefect) | Proposed | — |
| D3 | Orchestrator hosting: DigitalOcean droplet vs Dagster+ serverless | Open | — |
| D4 | Public API: FastAPI vs Datasette | Open | — |
| D5 | Odds data provider and plan | Open | — |
| D6 | Research results public or private | Private by default | — |
| D7 | Cloudscape: internal tools only, not the public site | Decided | Oct 2026 |
| D8 | Text-to-SQL: Claude tool use over semantic layer (not Vanna, archived) | Decided | Oct 2026 |
| D9 | AI engineering control plane, separate from Dagster | Proposed | — |
| D10 | Claude Code as primary builder; Codex as independent reviewer | Proposed | — |
| D11 | Herdr and/or an orchestrator (agent-orchestrator, Stoneforge, Overstory): pilot before adopting; baseline is GitHub Issues + worktrees | Open (Session 5) | — |
| D12 | GitHub PRs, isolated worktrees, required CI, human approval for merges and production | Proposed | — |
| D13 | Lead architect model: Claude by default; confirm the exact "Astra" product/model before assigning it a role | Open | — |
| D14 | Agent machine (ThinkCentre vs Windows + WSL2) and agent spending budgets | Open (Session 0, 3) | — |
| D15 | R2 raw capture may start before V2.-1 completes (append-only, time-sensitive) | Proposed | — |

## 17. Dependency map

```
V2.-1 Agent delivery system (Sessions 0–6) ──► authorizes V2.0 onward
   (exception: V2.0 step 1, R2 raw capture, may start now)

V2.0 Data platform ──► V2.1 Astro site ──► V2.2 Explorer/API/search ──► V2.3 Accounts ──► V2.4 Ask the Observatory
   │  (R2 raw capture)                                                                         ▲
   │                                                                                           │
   └──► Q0 Data additions (odds, full crews, snaps, injuries) ──► Q1 Foundations ──► Q2 Prereg ──► Q3 Backtests ──► Q4 Paper ──► Q5 Monitor
                                             │
                                             └──► improves site projections (model v2) regardless of betting results
Growth Cadence Phase 1 runs throughout; its Phase 2 items land in V2.1.
```

## 18. Costs

| Item | Monthly |
|---|---|
| Cloudflare (Pages, Workers, R2 at our size) | $0–5 |
| DigitalOcean droplet for Dagster | ~$6–12 |
| Odds data provider | depends on plan (historical + props tiers cost more; decision D5) |
| Plausible (or self-hosted Umami: $0) | $0–9 |
| Supabase (free tier at launch) | $0 |
| Claude API for Ask the Observatory | usage-based; cap with rate limits |
| **Total excluding odds data and AI agents** | **~$10–30** |
| AI engineering agents (Claude Code, Codex) | plan- or usage-based; set monthly caps (D14) |
| Agent tooling (Herdr is free; orchestrators mostly free/open source) | $0 for the baseline |
