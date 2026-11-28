---
name: observatory-rules
description: Standing rules for every change in the NFL Officiating Observatory repo (process, git, numbers, wording, design, data, deploys), each with the issue, PR or #86 comment it came from. Load before planning, building or reviewing a step.
user-invocable: false
---

# Observatory standing rules

Each rule has an ID (cite it in plans and reviews as `R<n>`) and its source.
IDs never change once given; rules confirmed later (R67, R68, R69, R71, R72) sit
in their topic's section, so IDs aren't always in order.
"#86 (date)" means a comment on the pinned issue #86 "V2 progress log" on that
date (UTC). CLAUDE.md and `docs/V2_BUILD_PLAN.md` still apply in full; where a
rule here only points at them, they are the authority.

Rules in the last section, **Unconfirmed**, are not yet confirmed by Ty: the
planner and builder follow them where they fit, and the reviewer reports a
breach of one under "Questions for Ty" but never as a required change.

## A. Process and scope

- **R1** One plan step = one issue = one branch = one PR. Read the issue and its plan section (`docs/V2_BUILD_PLAN.md` or, from #146 on, `docs/BUILD_PLAN_ADDENDUM.md`) before proposing anything. *CLAUDE.md; plan §26.*
- **R2** Plan first: no file changes until Ty approves the plan. *CLAUDE.md "How we work" 1; plan §26.3; #86 (2026-10-31).*
- **R3** Stay inside the issue. Anything found outside it is noted and becomes its own issue; stop rather than fix it. *CLAUDE.md; #102, #104, #168.*
- **R4** Stop and ask when the plan is ambiguous, a check fails for an unclear reason, a secret, account or setting change is needed, or the work grows past the issue. See the `escalation` skill. *CLAUDE.md; step template.*
- **R5** Every agreed follow-up or "later" item becomes its own `step` issue, drafted and shown to Ty before it is created. Handoff notes point at issue numbers. *#86 (2026-10-31, 2026-11-18).*
- **R6** Every wrong number found gets a D-number (continuing from D14 in `docs/audits/metric-conflicts-2026-10-28.md`) and a drafted issue, all shown to Ty together at the end. Stop mid-session only if the live site badly misleads visitors right now. *#86 (2026-10-29).*
- **R7** Text-only data errors (wording, no number change) are batched in one issue; errors that change a number get their own issue. #112 is closed, so ask Ty before opening the next batch issue. *#112; #86 (2026-10-29).*
- **R8** Data-error fixes change only what the issue names ("the numbers only" or "the text only"); titles, definitions and populations stay put. *#107, #110, #112, #114.*
- **R9** Ask before changing `CLAUDE.md`, the plan's routine or `.claude/settings.json`. *#134; CLAUDE.md.*
- **R10** Interim work must not turn into the V2.1 build (Astro, six-section navigation, full on-demand loading). Stop if it starts to. *#148, #153, #166.*
- **R67** A scope change agreed with Ty mid-issue is recorded as an issue comment headed "Scope note", with the options and the choice. *#102, #166; confirmed by Ty 2026-11-26.*
- **R72** During a `/run-step` run, each of Ty's decisions (plan approval and wording, option choices, scope changes, answers to the reviewer) is posted straight away, without asking, as a comment headed "Decisions from Ty (<date>)" on the issue, or on the PR once one exists, from a scratchpad file with `--body-file`, before the next delegation. Only Ty's decisions; other comments still need his OK. *#215; confirmed by Ty 2026-11-27.*
- **R11** Report PR, issue and run status from live GitHub (`gh pr view`, `gh issue view`, `gh run view`), never from earlier notes. *Ty's instruction (2026-10-27; confirmed 2026-11-26).*

## B. Git, branches and PRs

- **R12** Branch: `git switch main`, `git pull`, `git switch -c step/<issue#>-<short-name>`. Never commit to `main`, never force-push. *CLAUDE.md; plan §29; #86 (2026-10-31); every step issue since #146.*
- **R13** Run `git push`, `gh pr create`, `gh pr merge`, `gh pr edit` and `gh issue edit` each as a standalone call: no `cd … &&`, no heredoc or other command in the same call. Write PR and issue bodies to a file first. Plain `git push`; never `git -C` or `git -c`. *CLAUDE.md rule 8; PR #100, PR #113; #86 (2026-10-28, 2026-10-29).*
- **R14** Ty merges. Ask Ty before every push, PR description edit and "ready for review". *#86 (2026-10-29).*
- **R15** End of a step: run `venv/Scripts/python scripts/check.py`, then commit, then push, then open the PR, each as its own call. *#191, #193, #206.*
- **R16** The PR fills `.github/pull_request_template.md` and its body contains `Closes #<n>`. *Template; PR #94 (#93 didn't close because the link was added late).*
- **R17** Commit messages: a short summary line, then what changed and why. *CLAUDE.md.*
- **R18** Never commit generated output: after local pipeline or build runs, `git restore frontend/data reports/miner` and the summary fill. Change the script, never the generated file. *CLAUDE.md; #80, #82, #148, #158, #166.*
- **R19** Edit `.github/workflows/` files only with the Edit tool. *CLAUDE.md rule 7; #98.*
- **R20** Don't use `git worktree` or `git archive`. Build the "before" site from `git show main:<file>` copies in the scratchpad; propose any other method before trying it. *#86 (2026-10-30, 2026-10-31).*
- **R21** Dependabot: the PR is the step (no separate issue or branch unless something must change). One update per step; Python package upgrades get a before/after data diff; don't merge until the release is 14 days old. *#86 (2026-10-27, 2026-10-28, 2026-11-26); #92; PR #97.*
- **R22** Packages are locked to exact versions with uv `--universal`, Python floor 3.11.9; raise the floor only in its own step. Actions are pinned to a full SHA with a plain version comment (`# v7.0.1`). *#92, #93; #86 (2026-10-28).*
- **R68** Multi-session steps: one branch, a checkpoint commit after each session, a draft PR after the first session; every push still asks Ty. *#104; confirmed by Ty 2026-11-26.*

## C. Checks and evidence

- **R23** `scripts/check.py` passes and CI is green before a step is called done. Report the actual output. *CLAUDE.md; plan §26.4.*
- **R24** Tests need no network and no secrets. Each new test must fail when the code it covers is deliberately broken; show one break per test file. *#89, #166.*
- **R25** Every changed number is recomputed with separate scratchpad code from play-level data, and the PR states the match count (for example "28 of 28 match"). *CLAUDE.md data rule 1; #105, #107, #114, #148.*
- **R26** "No number moves" (or "only these fields move") is shown with `rebuild_from_raw.py` / `compare()` before and after (`--at … --all`), with a control run showing "no differences", and every changed path listed in the PR. *#105, #107, #110, #112, #116–#118, #134; #86 (2026-10-29).*
- **R27** Page changes: Ty checks the "before" site on port 8001 (main) against "after" on port 8000 (the branch); UI changes get before and after screenshots at desktop and narrow widths, with a fresh browser profile each run. *#114, #116–#118, #158, #166, #168, #169; #86 (2026-10-29).*
- **R28** After merge: check the merge run (green, `All modules OK`), walk the data commit field by field, run the live checks, and post the results to the PR as a comment. If anything changed outside the expected fields, especially in `scorecard/` or `history/`, stop. *PRs #103, #108, #109, #111, #151, #152, #183–#185, #198; #86 (2026-10-29).*
- **R29** Windows local testing: for `build_static.py`, swap `%-d` for `%#d` in memory only (never edit the file); restore `frontend/index.html` and `frontend/gameday/index.html` before `check.py`; use `PYTHONUTF8=1` for `rebuild_from_raw.py`. Applies until #91 is fixed. *#86 (2026-10-29, 2026-10-31).*

## D. Numbers and metrics

- **R30** Every new or changed metric has an entry in `docs/METRICS.md` (plan §6 fields). Retired metrics are marked "retired (date)", not deleted. Data-fix PRs name the M-entries they update. *CLAUDE.md; #104, #117, #118, #158, #206.*
- **R31** Every rate shows its sample (games or plays). Every percentage change shows the absolute change and the baseline. *CLAUDE.md; plan §17.*
- **R32** One small-sample threshold everywhere: 8 games, for any per-game rate shown (plan decision D13). *#86 (2026-10-29); #127.*
- **R33** Never hard-code years, windows or values in labels or text: compute them from the data or say it without a number. Allow-listed constants (such as the 2015 start) are the only exception. `check.py` enforces part of this. *#110, #112, #116–#118, #158; #86 (2026-10-29).*
- **R34** Share differences are in percentage points ("pts"); `%` only for relative change. Worked examples in explainers are generic, not a current crew chief's figures. *#107, #110.*
- **R35** Model estimates are labeled "model estimate" and never shown as observed facts; raw rates in rankings are labeled "observed". *CLAUDE.md; plan §17.*
- **R36** Rounding follows plan §6: per-game rates to one decimal; percentages whole (one decimal below 10%); counts as integers. *Plan §6; #172.*
- **R37** Team codes map to today's abbreviations in one shared place (STL, SD, OAK; ARZ→ARI); `game_id` keeps its original form. *#105, #206.*
- **R38** "Updated" means: file times are when the content last changed; the page line is the last run time. *#86 (2026-10-31); #163, #173.*
- **R69** Home vs road is shown as "% more on road teams" with the league figure beside it, and every metric conflict C1–C27 follows the option Ty chose (regular season everywhere, career = seasons before this one, raw rates by default with adjusted rates labeled). *`docs/audits/metric-conflicts-2026-10-28.md`; #86 (2026-10-29); #117, #120; confirmed by Ty 2026-11-26.*

## E. Wording

- **R39** Wording describes, it doesn't accuse: no "strict", "lenient", "biased", "rigged" or "cost them the game" unless a documented analysis supports it. Titles never claim more than the analysis supports. *CLAUDE.md; plan §17.*
- **R40** Every ranking names its ranking metric; the key caveat is visible, not only behind a ? panel. *Plan §17; PR template.*
- **R41** Headings: the H1 is the search phrase, computed, never hard-coded; page titles follow the H1; menu labels stay short; buttons use the menu name ("See all <menu name> →"). No doubled labels, no filler copy, chart titles in sentence case. *#158, #191.*
- **R42** New or changed visitor-facing copy needs Ty's approval. Wording not on an approved list, or a rename that would change meaning, means stop and ask. *#158, #165, #191.*
- **R71** Never say "updated weekly"; say "Updated automatically during and after every game day." *#86 (2026-10-29, D11); confirmed by Ty 2026-11-26.*

## F. Design and pages

- **R43** Neutral graphite UI with one flag-yellow accent; no new palette or colors. *CLAUDE.md; plan §12; #166, #169.*
- **R44** Red = more penalties, green = fewer, always with a text label or shape too. *CLAUDE.md; plan §12.*
- **R45** Team colors (exact official colors) only on game-preview split bars and the quarter-by-quarter chart. *CLAUDE.md; plan §12.*
- **R46** No emoji icons except 🏈 and ⏱️. *CLAUDE.md; plan §12; PR #22.*
- **R47** Any chart of penalties per game is sorted most penalties first. *CLAUDE.md; plan §12.*
- **R48** Every full page is a superset of its home section: fully interactive, ordered by visitor intent, no "on the home page" buttons (`check.py` "Full pages"). *Ty's rule, #166, #168, #169; #86 (2026-10-31).*
- **R49** Menus change only in `scripts/site_nav.py`, followed by `scripts/sync_nav.py`; never by hand (`check.py` "Menus match"). *#153, #191.*
- **R50** URLs and anchors stay stable through renames so shared links keep working. *#153, #158, #191.*
- **R51** `?v=` cache-bust stamps are added at deploy, never typed by hand. *#147.*
- **R52** Security headers come only from `frontend/.htaccess`; if a live header differs, stop (Ty checks the host). *#146.*

## G. Data, privacy and analytics

- **R53** Never read, print or write `.env` or any secret. Ty creates every token, key and account; give him exact clicks. Secret names go in `.env.example`. Public keys (PostHog `phc_`) may be committed as config. *CLAUDE.md; plan §32; #164, #165.*
- **R54** While the repo is public, private files go to R2 (`nflobs-raw/internal/`), never to a committed folder. *#86 (2026-10-31, plan decision D27).*
- **R55** While the repo is public, issues, PRs, commits and #86 comments never describe the referee grade's design. Refer to it only as "private, kept outside the repo (D27)"; grade decisions appear by title only. Scan every posted text for this before posting. *#86 (2026-10-31); Ty's instruction after the 2026-10-30 handoff draft.*
- **R56** The raw store in R2 is append-only: conditional writes, never overwritten or rewritten. *#88, #164, #193.*
- **R57** ESPN data: the raw copy stays private in R2; only our own derived data is published; ESPN's play text is never published. *#193.*
- **R58** Pipeline failures are loud: a data-loading failure exits 1 and writes nothing; a module failure exits 3 and is recorded in `run_status.json` (no tracebacks or paths: it is public); writes are atomic. *#80, #81, #82.*
- **R59** Forced-failure hooks (`NFLOBS_FAIL`) are ignored under GitHub Actions; fake dates appear only in throwaway test scripts, never in code. *#80, #81, #84.*
- **R60** Analytics: every event goes through the one `track()` helper; PostHog US, cookieless, events only (no session replay, autocapture or heatmaps); never rename event names or properties (only labels change). New or changed events are listed in `docs/ANALYTICS.md`. No privacy text on the site until #181 is decided. *#165, #191; #86 (2026-10-31).*
- **R61** Model-internal fields don't go in public JSON; full copies go to R2 `internal/`. *#86 (2026-10-31, plan decision D24); #150.*

## H. Docs

- **R62** Update `docs/architecture/current-state.md` when code, workflows, the deploy or the data layout change; `docs/DATA_SOURCES.md` when a source or storage changes. *Practice in nearly every issue since #80; #164, #193.*

## I. Session handoff

- **R63** End every working session with one comment on #86, drafted and shown to Ty before posting. Heading `## Handoff <date> (<part of day>): <summary>`; sections **Done**, **Open right now**, **Next steps** (full steps, exact clicks and commands, an **Expected:** line each, never "see the earlier handoff"), **Things to check next session** (exact `gh` commands, **Expected:** each), **Open decisions or questions**. Every fact from live GitHub; every open item has an issue number. Every open item from the previous handoff is carried forward unless it is closed (checked on live GitHub); a closed one is listed once under **Done**. *#86 body and comments (2026-10-27 on); latest format 2026-11-27; carry-forward #215.*

## J. Merges and deploys

- **R64** Never merge a PR that starts a data run while a game is in progress; give Ty safe merge windows. *#86 (2026-11-26, 2026-11-27); #206; confirmed by Ty 2026-11-26.*
- **R65** If a deploy returns a 500, open a revert PR right away (`git revert` the merge, on a branch); Ty merges it. Never try fixes on `main`. *#146, #147; confirmed by Ty 2026-11-26.*

## Unconfirmed

Not yet confirmed by Ty. The reviewer reports on these under "Questions for
Ty" and never lists them as required changes.

- **R66 (unconfirmed)** Generated files are deterministic (sorted keys, no per-file timestamps nothing reads) so unchanged files stay byte-identical. *#102; #163 open.* Stated for team pages; #163 may make it general.
- **R70 (unconfirmed)** Crew changes go through `data/assignments_overrides.csv` on a branch with a PR, before kickoff. *#86 (2026-10-31); PR #141.* The manual weekly check ended with #145; unclear if the override route is still the rule.
