# CLAUDE.md

Instructions for Claude Code working in this repository. Read this first in
every session.

## What this is

NFL Officiating Observatory (nflobservatory.com): crew chief and team penalty
data, game previews and projections, trends, a live gameday page, and the
"What Flags Cost" analysis. Data comes from nflverse (via `nflreadpy`) and
Football Zebras (crew assignments). History covers 2015 to the present.

**The plan:** `docs/V2_BUILD_PLAN.md`. Every task is one step from that plan,
tracked as one GitHub issue, built on one branch, merged through one pull
request. Read the plan section named in the issue before proposing anything.

## How we work

1. **Plan first.** Read this file, the plan section and the issue
   (`gh issue view <n>`). Propose a numbered plan listing the files you'll
   change and how you'll check the result. Do not edit files until Ty approves.
2. **Small steps.** Stay inside the issue's scope. If something outside it needs
   changing, say so and stop; it becomes its own issue.
3. **Stop and ask** when: the plan is ambiguous, a check fails for a reason you
   can't explain, you need a secret or a new account, or the work is growing
   past the issue.
4. **Check before you call it done.** Run the checks (below) and the issue's
   "Done when" commands, and report the actual output.
5. **Explain like a checklist.** Ty follows instructions literally: give exact
   commands, exact clicks, and what he should see when it worked.
6. When Ty asks to review something before you act, stop and wait for his OK,
   even if the next step seems obvious.

## Machine and shell

- Windows laptop (ROG Strix). Ty uses PowerShell; your shell may be Git Bash.
  Use forward slashes in paths you run, and call Python through the venv
  directly so activation doesn't matter: `venv/Scripts/python`.
- Python 3.11 (matches GitHub Actions). Node LTS is installed (needed from V2.1).
- CI and the data workflow run on Ubuntu. Line endings are LF (`.gitattributes`).

## Commands

| Task | Command |
|---|---|
| Install dependencies (exact versions from the lock file) | `venv/Scripts/python -m pip install -r scripts/requirements.txt` |
| Regenerate the lock file (after editing `scripts/requirements.in`; run from `scripts/`) | `../venv/Scripts/python -m uv pip compile requirements.in --universal --python-version 3.11.9 --output-file requirements.txt` |
| Update current season | `venv/Scripts/python scripts/update_data.py` |
| Full rebuild (2015 to now) | `venv/Scripts/python scripts/update_data.py --full` |
| Crew assignments | `venv/Scripts/python scripts/fetch_assignments.py` |
| Build static pages (crew, team, trends, guide, dataset, sitemap) | `venv/Scripts/python scripts/build_static.py` |
| Local site | `venv/Scripts/python -m http.server 8000 --directory frontend` → http://localhost:8000 |
| Gameday worker local test | `node worker/gameday/test-local.mjs [espnEventId]` |
| All checks (added in Session W1) | `venv/Scripts/python scripts/check.py` |

After running the pipeline locally for testing, discard the generated data
unless the task is about data: `git restore frontend/data reports/miner`.

## Repository map

| Path | What it is |
|---|---|
| `scripts/update_data.py` | Main pipeline; writes everything in `frontend/data/` |
| `scripts/*.py` | Pipeline modules: weeks, previews, scorecard, history ledger, flag impact, crew styles, team pages, type trends, stat miner, scoreboard |
| `scripts/build_static.py` | Pre-renders static pages at deploy time (output is gitignored) |
| `frontend/` | The site: `index.html`, `css/`, `js/` (app, gameday, livestrip), `gameday/` |
| `frontend/data/` | **Generated.** Never hand-edit; change the script that writes it |
| `worker/gameday/` | Cloudflare Worker serving live penalties for `/gameday/` |
| `social/`, `scripts/social/` | Social post image generation |
| `reports/miner/` | Weekly stat miner reports (tracked); rest of `reports/` is local only |
| `docs/` | Plans: V2 build plan, data and modeling roadmap, growth cadence, data sources, stat miner |
| `.github/workflows/update-data.yml` | Scheduled data runs, commits data to `main`, builds static pages, deploys by FTP to HostGator. Also runs on every merge to `main` |

## Rules

**Data and numbers**
1. Every number is checked: recompute from play-level data and compare before
   publishing a new or changed metric.
2. Every new or changed metric gets an entry in the metric dictionary
   (`docs/METRICS.md` from V2.0a; format in plan section 6).
3. Every rate shows its sample (games or plays). Every percentage change shows
   the absolute change and the baseline.
4. Label model estimates as estimates; never present them as observed facts.
5. Wording describes, it doesn't accuse: no "strict", "lenient", "biased",
   "rigged" or "cost them the game" unless a documented analysis supports it.
   Full standard: plan section 17.

**Design (current theme stays; plan section 12)**
1. Neutral graphite UI with a single flag-yellow accent. No new palette.
2. Red = more penalties, green = fewer, always with a text label or shape too.
3. Team colors (exact official colors, never altered) only on game-preview
   split bars and the quarter-by-quarter chart.
4. No emoji icons except the football (🏈) and the quarter-by-quarter clock (⏱️).
5. Any chart of penalties per game is sorted most penalties first.

**Git and safety**
1. Work on the issue's branch. Never commit to `main` directly, never force-push.
2. Never read, print or write `.env` or any secret. Secret names are in
   `.env.example`; values live in GitHub Actions secrets and Ty's `.env`.
3. Never change GitHub settings, secrets, DNS, hosting or billing. Tell Ty the
   clicks instead.
4. Don't commit generated folders listed in `.gitignore`.
5. Commit messages: a short summary line, then what changed and why.
6. Pull from `main` before starting: the data bot commits to it several times
   a week (more on game days).
