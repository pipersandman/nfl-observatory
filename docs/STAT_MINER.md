# Stat Miner: Guide and Roadmap

**What it is:** an automated search for the most unusual, record-setting and
surprising officiating stats each week, filtered so that what's left is very
unlikely to be luck, with the plays behind every number.

**Related docs:** [V2 Build Plan](V2_BUILD_PLAN.md) (data lake, trust standards, build routine) ·
[Growth Cadence Plan](GROWTH_CADENCE_PLAN.md) (Fact of the Day, report cards) ·
[Data Sources](DATA_SOURCES.md).

| Phase | What | Status |
|---|---|---|
| 1 | Candidates + rarity (records, top-5s vs every comparable since 2015) | **Live** |
| 2 | Surprise scoring + luck filter (count models, shrinkage, false-discovery control) | **Live** |
| 2.5 | Quick wins on the current pipeline (novelty log, "first since", streaks, qualifier penalty) | Next, current site |
| 3 | Pattern finding (changepoints, unusual games, crew × team matchups) | V2.0 (needs the data lake) |
| 4 | Publishing loop (Claude drafts with number checks, review queue, Fact of the Day) | V2.0–V2.1 |
| 5 | Ask the Observatory integration and a public Records page | V2.2–V2.4 |

---

## Contents

**Part 1: Using it now**
1. [Where to find it](#1-where-to-find-it)
2. [How to read an entry](#2-how-to-read-an-entry)
3. [Weekly routine: from report to post](#3-weekly-routine-from-report-to-post)
4. [Running it yourself](#4-running-it-yourself)
5. [What it checks today](#5-what-it-checks-today)
6. [Known limits](#6-known-limits)

**Part 2: Roadmap**

7. [Phase 2.5: quick wins (current site)](#7-phase-25-quick-wins-current-site)
8. [Phase 3: pattern finding (V2.0)](#8-phase-3-pattern-finding-v20)
9. [Phase 4: publishing loop](#9-phase-4-publishing-loop)
10. [Phase 5: Ask the Observatory and Records page](#10-phase-5-ask-the-observatory-and-records-page)
11. [Dependencies](#11-dependencies)

---

# Part 1: Using it now

## 1. Where to find it

- **On GitHub:** `reports/miner/` in the repo, one file per week: `2026-week-06.md` (readable) and `2026-week-06.json` (the same data, for tools).
- **When it updates:** every pipeline run (the scheduled runs, plus any manual run). The report always covers the **latest completed week** (every game played and in the play-by-play), so it appears early Tuesday morning after Monday Night Football.
- **Not on the site.** It's an internal research list; you choose what gets published.

## 2. How to read an entry

Example:

> 1. **Record: Scott Novak, 21.3 flags per game through Week 6** (normal: 13.5): 1st of 204 crew-seasons through Week 6 since 2015.
>    <sub>crew season · surprise p=1.0e-06 · q=0.00</sub>

| Part | Meaning |
|---|---|
| **Record / 2nd highest / Top N** | Where it ranks among everything comparable |
| **Value** (21.3 flags per game) | The stat itself, recomputed from the play-by-play |
| **Normal** (13.5) | What's typical for this kind of thing: the league average, or the entity's own average (a crew's or team's normal is pulled toward the league when it has few games) |
| **1st of 204 crew-seasons through Week 6 since 2015** | Exactly what it was compared with. Season-to-date stats are always compared *through the same week* of past seasons |
| **Level** (crew season) | league week · game · team game · crew game · crew season · team season · player game · player season · flag |
| **surprise p** | How unlikely a number this extreme is if nothing unusual were going on. 1.0e-06 = one in a million; 0.05 = one in 20 |
| **q** | The same, corrected for the thousands of things the miner checks at once. Entries are kept when q ≤ 0.10 (or for an outright record). Lower is stronger |
| **Bullets under an entry** | The plays behind it: quarter, clock, team, penalty, player, yards, points cost |

**Ranking:** entries are ordered by a score combining surprise, rank (records and top 3 get a boost) and level (league-wide and crew stats get a small boost). Only one entry per game or entity is shown.

## 3. Weekly routine: from report to post

About 20 minutes on Tuesday.

1. **Open** `reports/miner/<season>-week-NN.md` on GitHub.
2. **Pick 4–6 entries** with different levels (one league, one game, one crew, one team, one player is a good mix). Prefer low q and records.
3. **Check each one before posting:**
   1. **Context:** read the evidence bullets. Was there overtime, a blowout, an injury, weather? Say so if it matters.
   2. **Window:** the miner compares against **2015 onward**. If you want "since 2020," ask me or check the site's charts; rankings differ (Week 6's 132 penalty yards per game is 11th since 2015 but 1st since 2020).
   3. **Wording:** patterns, not motives. "Novak's crew is calling more flags than any crew through six weeks since 2015," never "biased" or "targeting."
   4. **Names:** player names come as nflverse writes them (`E.Pregnon`); confirm the full name and team before posting.
4. **Write the post** using the site's pages as links (crew page, team page, What Flags Cost) rather than the home page.
5. **Tell me** which entries you used. Until the novelty log (Phase 2.5) exists, that keeps repeats out of next week's suggestions.

## 4. Running it yourself

The miner runs inside the normal pipeline:

```powershell
cd C:\Users\tfost\nfl-observatory
.\venv\Scripts\Activate
python scripts\update_data.py --full
```

The report lands in `reports\miner\`. Settings at the top of `scripts/stat_miner.py`:

| Setting | Default | Effect |
|---|---|---|
| `FDR_Q` | 0.10 | Luck-filter strictness. Lower = fewer, stronger entries |
| `TOP_N` | 30 | Entries in the report |
| `TOP_TYPES` | 12 | Penalty types checked individually |

## 5. What it checks today

| Level | Metrics | Compared with |
|---|---|---|
| **League week** | Flags, penalty yards and first downs by penalty (per game), expected points given away, touchdowns wiped out, each of the 12 most common penalty types | Every regular-season week since 2015 |
| **Game** | Flags, yards, points, win-chance swing, first downs, fourth-quarter flags, one-sidedness, touchdowns wiped out | Every game since 2015 (only the top ~1% are considered) |
| **Team game** | Flags, yards, points, first downs given | Every team-game since 2015; surprise vs the team's own normal |
| **Crew game** | Flags vs the crew chief's own average | The crew's games since 2015 |
| **Crew season** | Flags per game through this week | Every crew-season through the same week since 2015 |
| **Team season** | Flags, yards, points per game, touchdowns wiped out (and fewest flags) | Every team-season through the same week since 2015 |
| **Player** | 3+ flags in a game; season-to-date flags overall and for holding, DPI, false start, roughing the passer, unnecessary roughness, defensive holding | Player-games / player-seasons since 2015 |
| **Single flag** | Costliest by expected points and by win chances | Every flag since 2015 |

## 6. Known limits

1. **Pre-screening:** each level only considers its top 1–5% before scoring, so the "candidates" count is the standouts, not everything examined.
2. **Latest week only:** it reports on the most recent completed week (and season-to-date through it), not past weeks on demand.
3. **No memory of what was posted** (Phase 2.5 adds this).
4. **No "first since" or streaks yet** ("first 20-flag game since 2017," "fifth straight game with 10+"): Phase 2.5.
5. **Simple surprise model:** Poisson counts; for some measures (yards, points) surprise falls back to rank. Phase 3 adds better models.
6. **Crew = crew chief:** like the rest of the site, stats are by crew chief, not the official who threw the flag.
7. **Player names** are nflverse's abbreviations; two players can share one.

---

# Part 2: Roadmap

## 7. Phase 2.5: quick wins (current site)

**Depends on:** nothing (current pipeline). About one session.

1. **Novelty log**
   1. `reports/miner/published.json`: entries you've posted (key, date, where).
   2. A simple way to mark them: you tell me, or a `published:` list you edit on GitHub.
   3. The miner lowers the score of anything already published, or anything that only restates it, for 6 weeks.
   4. **Done when:** a posted entry doesn't reappear next week unless it got more extreme.
2. **"First since" and droughts**
   1. For every top candidate, find the most recent time something as extreme happened ("first 24-flag game for this crew since 2019").
   2. **Done when:** entries include "first since <date>" where it's at least 2 seasons back.
3. **Streaks**
   1. Consecutive games above a threshold for teams, crews and players (10+ flags, a flag in every quarter, a holding call in N straight games).
   2. Compared with the longest streaks since 2015.
4. **Qualifier penalty**
   1. Each extra condition in a stat ("in the 4th quarter," "on the road," "in October") lowers its score unless the stat is striking without it.
   2. Prevents cherry-picked "most X in situation Y after Z" items.
5. **Since-2020 view**
   1. Every entry also shows its rank since 2020, so you can pick the more relevant window.
6. **Draft headlines**
   1. One plain-English headline per entry, written from the verified numbers by a template (no AI yet).

## 8. Phase 3: pattern finding (V2.0)

**Depends on:** V2.0 data lake (DuckDB + dbt marts, R2 raw history) and Data Sources P0 additions (all seven officials, snap counts, weather, closing lines).

1. **Changepoint detection**
   1. CUSUM / Bayesian changepoints on every crew's and team's flags per game, penalty-type mix and yards per flag.
   2. Output: "Novak's crew changed in Week 1 2026: from 11.7 to 21+ per game; probability of a real change 0.99."
   3. **Done when:** backtested on 2015–25 with known rule-emphasis seasons detected (e.g. 2023 illegal-formation, 2026 pre-snap rise).
2. **Unusual games (game fingerprints)**
   1. Each game becomes a vector: penalty-type mix, timing by quarter, offense/defense split, home/road split, yards per flag, pre-snap share.
   2. Isolation forest flags games that are unusual *in combination* (normal totals but all in the 4th quarter; 80% on one team; no pre-snap calls).
   3. Nearest-neighbor "this game looked most like…" for each flagged game.
3. **Crew × team matchups**
   1. Hierarchical model (crew effect + team effect + interaction), shrunk hard toward zero, as in the Data & Modeling Roadmap §5.7.
   2. Report only interactions that survive false-discovery control.
4. **Per-snap and per-player rates** (with snap counts): "most holding calls per 100 snaps," removing playing-time bias.
5. **Official-level patterns** (all seven officials, 2015+): which crew members travel with a crew's tendencies when crews change.
6. **Sequences:** flag clustering and "retaliation" (does a personal foul raise the next drive's flag rate?) with self-exciting (Hawkes) models.
7. **Counterfactuals:** "if both teams had been flagged equally," "if this flag hadn't been thrown" (win-chance swing per game), feeding the report card.
8. **Better surprise models:** negative binomial counts, empirical-Bayes for every level, permutation tests for interactions.
9. **Runs as a Dagster asset** with its own checks; results in a `marts.stat_candidates` table.

## 9. Phase 4: publishing loop

**Depends on:** Phase 2.5 (novelty log) and Phase 3 (for richer items); Growth Cadence step 5.9 (Fact of the Day page) for the public outlet.

1. **Claude drafts** a post-ready sentence and a short explainer per entry, given only the verified numbers.
2. **Number checker:** every number in the draft must match the entry's data; anything else rejects the draft.
3. **Review queue** in the internal admin console (V2 Build Plan, Part A): approve, edit, or reject; approved entries go to the novelty log.
4. **Outlets:** Fact of the Day (`/live/`), Monday/Tuesday report card, Friday X pack, Reddit drafts.
5. **Done when:** a week's top 10 can be reviewed and scheduled in under 15 minutes, with zero number mismatches.

## 10. Phase 5: Ask the Observatory and Records page

**Depends on:** V2.2 (API, explorer) and V2.4 (Ask the Observatory).

1. **Ask the Observatory tool:** "what's unusual about the Chiefs this year?" runs the miner scoped to that entity and returns ranked, evidence-backed answers.
2. **Public Records page:** all-time and season records by level (most flags in a game, longest streaks, costliest flags), updated weekly, with each record's plays. Strong search and AI-citation target.
3. **On-demand weeks:** run the miner for any past week (for recaps and anniversaries).

## 11. Dependencies

```
Live: Phase 1 + 2 ──► Phase 2.5 quick wins (current pipeline)
                           │
V2.0 data lake + Data Sources P0 ──► Phase 3 pattern finding ──┐
                           │                                    ▼
Growth 5.9 Fact of the Day ─────────────────────────► Phase 4 publishing loop
                                                                │
V2.2 API/explorer + V2.4 Ask the Observatory ─────────► Phase 5 Records page + Ask integration
```
