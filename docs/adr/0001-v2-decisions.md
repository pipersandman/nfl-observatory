# ADR-0001: V2 decisions as of W1

- **Status:** Decided (as a record of the decisions log on this date)
- **Date:** 2026-10-26
- **Plan reference:** `docs/V2_BUILD_PLAN.md` section 33 (decisions log)
- **Issue / PR:** #74

## Context

The V2 build plan keeps a decisions log (section 33). From W1 on, each decision
is also recorded as an ADR in `docs/adr/`. This ADR is the starting record: it
copies the log as it stood when the ADR folder was created, so later ADRs have
a fixed point to supersede.

## Decision

The decisions and their status on 2026-10-26 are:

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

Decided in W1 itself (#74), not yet in section 33:

| Decision | Status | Date |
|---|---|---|
| Ruff starts with basic rules only (`F`, `E9`); the formatter and wider style rules wait for their own issue, to keep diffs reviewable | Decided | 2026-10-26 |

## Consequences

- Section 33 stays the live log. When a Proposed or Open decision is settled,
  write a new ADR for it (from `0000-template.md`) and update its row in
  section 33. This ADR is not edited after merge.
- Suggested follow-up for Ty: add the Ruff-scope row above to section 33.
