# Metric conflicts audit (2026-10-28)

Places where the site calculates or labels the same idea in different ways.
Found while building the metric dictionary ([`../METRICS.md`](../METRICS.md))
in V2.0a step 1 (#104).

**For each conflict, Ty picks one definition.** V2.0a step 2 then changes the
code to match (#76 keeps the Referee Variance card fix). This file only
records the conflicts and the decisions; it changes nothing on the site.

**Status:** session 1 of 7 (home page). C1's trends evidence is completed in
session 4. Data errors D1–D4 are listed at the end.

## Summary

| ID | Conflict | Found in | Recommended | Ty's decision |
|---|---|---|---|---|
| C1 | Two meanings of "season" (playoffs in or out) | Known gap 3 | A: regular season only, everywhere | |
| C2 | Offsetting-penalty plays counted as flags | Known gap 4 | A: accepted penalties only | |
| C3 | Referee Variance card (#76) | #76 | A: rebuild as a labeled spread | |
| C4 | Current season includes partial-week games; the same-weeks comparison doesn't | Session 1 | A: compare through the same last week | |
| C5 | "Penalties" counts plays with an accepted penalty | Session 1 | B: keep "penalties", define it | |
| C6 | Wording and framing (section 17) on the home page | Session 1 | A: descriptive wording, listed per item | |
| C7 | The home summary line compares with all of last season | Session 1 | A: same weeks, as the section below | |
| C8 | "All seasons" vs "Since 2015": two windows, similar names | Session 1 | A: prior seasons only, one name | |

**Data errors (own issues):** wrong numbers on the live site, not definition
choices. Each gets its own issue; the dictionary entries note them.

| ID | Error | Where | Issue |
|---|---|---|---|
| D1 | Relocated teams: two team abbreviations joined (STL/SD/OAK vs LA/LAC/LV) | `team_pages.py`, `scoreboard.py`, `stat_miner.py` | (being drafted) |
| D2 | "Home Field Bias" card misstates its number | `update_data.py` `generate_insights()` | to decide |
| D3 | "Most Common Call" card uses the wrong denominator | `update_data.py` `generate_insights()` | to decide |
| D4 | Scoreboard crew leader uses incomplete crew assignments | `scoreboard.py` | to decide |

## How to read a conflict

```markdown
## C<n>. <Short name>

**What differs:** one or two sentences.

**Evidence:** file:line references, and an example value from the data at `9add749`.

**Options:**
- **A.** … Effect on published numbers: …
- **B.** … Effect: …

**Recommendation:** A, because …

**Ty's decision:** (blank until decided)
```

---

## C1. Two meanings of "season"

**What differs:** some numbers labeled by season include playoff games; others
are regular season only.

**Evidence (session 1; trends side completed in session 4):**
- **Regular season only:** `season_comparison.json` (the "This Season vs Last"
  section, M1), which states `regularSeasonOnly: true`.
  `scripts/update_data.py` `calculate_season_comparison()` filters
  `season_type == 'REG'`, because playoff games are worked by all-star crews.
- **Playoffs included:**
  - `calculate_league_trends()` (`trends.json` → `bySeason`, `byQuarter`,
    `byType`, `homeVsAway`) has no `season_type` filter
  - `calculate_referee_stats()` (crew chief career numbers, Referee Variance
    M3) has no filter either
- **On the home page:** the "Penalty Surge Since 2022" card compares 2022
  (regular season and playoffs) with 2026 (regular season so far): "from 11.1
  to 14.7", +32%. The comparison mixes a full season including playoffs with a
  partial regular season. The percentage is also computed from the two values
  already rounded to 1 decimal.
- **The same comparison on other bases** (spot check, play-by-play, 2026 =
  14.67 per game: 1,570 penalties in 107 games, regular season through
  Week 7):

  | 2022 basis | 2022 per game | Change to 2026 | Absolute change |
  |---|---|---|---|
  | **Card today:** regular season + playoffs, games with at least one penalty (3,153 in 284 games), rounded before dividing | 11.1 | +32% | +3.6 |
  | **Regular season, full season** (3,031 in 271 games) | 11.18 | +31.2% | +3.49 |
  | **Same basis as 2026: regular season, Weeks 1–7** (1,303 in 108 games) | 12.06 | **+21.6%** | +2.61 |

  On a like-for-like basis (same weeks, regular season only, section 9),
  the change is about two-thirds of what the card shows.

**Options:**
- **A. Regular season only, everywhere.** Playoffs shown separately where
  they're useful (a labeled playoff line or table). Effect: every
  `trends.json` season value and every crew chief career number changes
  slightly (playoffs add 11 to 13 games a season to about 270); the 2022
  baseline on the surge card changes.
- **B. Playoffs included everywhere.** Effect: crew chief comparisons mix in
  all-star crews; "This Season vs Last" changes after each postseason.
- **C. Keep both, labeled.** Each number says "regular season" or "regular
  season and playoffs". Effect: no numbers change, but the same label still
  means two things across pages.

**Recommendation:** A. It matches the section most visitors read first, keeps
crew chief comparisons to crews' own games, and lets every "per season" number
be compared with every other. Partial seasons are labeled as partial
(plan section 9, point 5).

**Ty's decision:**

---

## C2. Offsetting-penalty plays counted as flags

**What differs:** `docs/architecture/current-state.md` known gap 4 says plays
with an offsetting-penalty description are counted as flags (0–6 plays a
season), while the site's wording elsewhere refers to accepted penalties.

**Evidence (spot check, regular season, play-by-play):**
- **2015–2025:** 11 plays with `penalty == 1` mention "offsetting": 6 in 2017,
  2 in 2023, 1 each in 2020, 2021 and 2025, none in the other seasons. This
  matches known gap 4 (0–6 a season).
- **2026 through Week 7:** 0 such plays. 20 offsetting plays have
  `penalty == 0` and aren't counted.
- These plays are counted wherever "penalties" are counted (M1 and every
  count built from `penalty == 1`). The effect is at most 6 plays in a season
  of about 3,400.
- Separate from this: `update_data.py` keeps touchdowns wiped out by
  offsetting penalties as `offsetting_tds` (for What Flags Cost, session 6).

**Options:**
- **A. Accepted penalties only.** Offsetting plays are never counted as
  flags; the dictionary says so. Effect: up to 6 plays a season fewer in the
  seasons where they're counted today.
- **B. Count every thrown flag,** including offsetting and declined. Effect:
  every penalty count and rate rises (in 2026 so far: +20 offsetting and +156
  declined-only plays on 1,570, about +11%). It also needs a different source
  field, since `penalty == 1` doesn't mark these plays.

**Recommendation:** A. It matches nflverse's `penalty` field and the site's
"accepted penalties" wording. B is
a different metric ("flags thrown"); if it's wanted, it can be added later as
its own entry.

**Ty's decision:**

---

## C3. Referee Variance card (#76)

**What differs:** the card's population, wording and display don't match the
rest of the home page or the section 17 standard. The fix itself stays in #76;
this records the definition to use.

**Evidence:** `scripts/update_data.py` `generate_insights()` (`ref_variance`)
and `calculate_referee_stats()`; dictionary entry M3.
- **Population:** crew chief career rates include playoffs (C1), with no
  minimum games and no games count shown.
- **Unused number:** `spread = max_avg − min_avg` is computed and never shown
  (`# noqa: F841`), while the explanation says "The spread tells you…".
- **Wording:** "the most lenient and strictest crews" (section 17 checklist).
  The "Crew Chief Spread" card (`crew_spread`) uses the same phrase and shows
  the same range.
- **Styling:** green "positive" below 15% reads as a judgment.
- **Example:** 9%, "Crew chiefs range from 11.0 to 16.5 penalties/game" (Bill
  Vinovich, 190 games, to Alex Moore, 22 games).

**Options:**
- **A. Rebuild as a labeled spread:**
  - regular season only (with C1)
  - crew chiefs above a minimum number of games (D13 threshold)
  - show the range in penalties per game with each end's games count, e.g.
    "11.0 to 16.5 penalties per game (190 and 22 games)"
  - descriptive wording, neutral styling
  - the coefficient of variation kept only if its meaning is explained in one
    sentence
  - merged with "Crew Chief Spread", which shows the same range

  Effect: the value and description change; one card instead of two.
- **B. Keep the coefficient of variation as the value** and fix only the
  wording, the unused `spread` and the games counts. Effect: two cards still
  show the same range.
- **C. Remove the card.** Effect: the spread appears only on the crew chief
  pages.

**Recommendation:** A. The range in penalties per game is the number visitors
can use ("who's calling my game"). The coefficient of variation is hard to
read without an explanation, and two cards showing one range is redundant.

**Ty's decision:**

---

## C5. "Penalties" counts plays with an accepted penalty

**What differs:** the site calls the count "penalties" (and "flags" in the
scoreboard and the guide), but what's counted is **plays** with at least one
accepted penalty. Two accepted penalties on one play count once.

**Evidence:**
- Every count comes from nflverse play-by-play rows with `penalty == 1`,
  which has one row per play (`scripts/update_data.py` `load_all_data()`:
  `data['penalties'] = pbp[pbp['penalty'] == 1]`).
- The guide's glossary (`scripts/build_static.py`) says: "Accepted penalty: A
  flag the offended team accepted; the only kind counted here" and "Flags per
  game: Accepted penalties on both teams in a game, averaged".
- **How often it matters** (spot check, regular season; accepted penalties
  per play read from each "penalty on" clause of the play description,
  declined and offsetting clauses left out):

  | Season | Penalty plays | Plays with 2+ accepted | Share | Count if each penalty counted | Difference |
  |---|---|---|---|---|---|
  | 2015 | 3,537 | 12 | 0.34% | 3,550 | +0.37% |
  | 2016 | 3,435 | 15 | 0.44% | 3,450 | +0.44% |
  | 2017 | 3,416 | 7 | 0.20% | 3,423 | +0.20% |
  | 2018 | 3,441 | 7 | 0.20% | 3,448 | +0.20% |
  | 2019 | 3,448 | 5 | 0.15% | 3,453 | +0.15% |
  | 2020 | 2,873 | 7 | 0.24% | 2,880 | +0.24% |
  | 2021 | 3,213 | 12 | 0.37% | 3,225 | +0.37% |
  | 2022 | 3,031 | 5 | 0.16% | 3,036 | +0.16% |
  | 2023 | 3,104 | 8 | 0.26% | 3,112 | +0.26% |
  | 2024 | 3,499 | 16 | 0.46% | 3,515 | +0.46% |
  | 2025 | 3,461 | 12 | 0.35% | 3,473 | +0.35% |
  | 2026 (Wk 1–7) | 1,570 | 5 | 0.32% | 1,575 | +0.32% |
  | **All** | **38,028** | **111** | **0.29%** | **38,140** | **+0.29%** |

  In 2026 so far, counting each accepted penalty would change 14.67 per game
  to 14.72. On the site's 1-decimal display that's 14.7 either way. Reading
  penalties from the description is approximate: the count of plays is exact,
  but the number of accepted penalties per play depends on the text.

**Options:**
- **A. Rename what's shown** to match what's counted: "penalized plays",
  "plays with a flag" or similar, on every tile, column and chart. Effect: no
  numbers change; many labels change; the wording is less familiar to
  visitors.
- **B. Keep "penalties"** and define it once: in the dictionary's Terms, on
  the methodology page (V2.0a step 10) and in the glossary: "a play with at
  least one accepted penalty, counted once; two on one play (about 0.3% of
  penalty plays) count once". Effect: no numbers or labels change.
- **C. Count each accepted penalty** (from the description, or another
  source). Effect: counts rise by 0.15–0.46% a season; most displayed rates
  don't change at 1 decimal; it needs a parser and a check.

**Recommendation:** B. The difference is under 0.5% in every season and
doesn't change the displayed rates, while renaming every label makes the site
harder to read. One sentence in the definition makes it accurate.

**Ty's decision:**

---

## C4. Partial-week games in the current season, not in the comparison

**What differs:** the current-season numbers in "This Season vs Last" include
every game played so far, including games from a week that hasn't finished.
The same-weeks comparison stops at the last completed week.

**Evidence:** `scripts/update_data.py` `calculate_season_comparison()`:
- `league.current` = every regular-season game of the current season
- `sameWeeks` = previous season, `week <= through_week`
- Crew chiefs are handled: one who already worked a partial-week game is
  compared through that week (`crew_week`). The league isn't.
- The subtitle says so ("through Week N (plus k games from Week N+1)"), but
  the league tiles compare the two windows as if they matched.
- At `9add749` there's no partial week, so no effect. On a Friday after a
  Thursday game, 2026 would have one more game than 2025's window.

**Options:**
- **A. Compare through the same last week:** the league comparison includes
  the previous season's games up to the partial week (as crew chiefs already
  do), or the current numbers leave the partial week out. Effect: league
  tiles change only while a week is in progress.
- **B. Leave it as it is, labeled:** the subtitle already names the partial
  games. Effect: none.

**Recommendation:** A, matching the crew chief rule, so both sides of every
comparison cover the same weeks (section 9).

**Ty's decision:**

---

## C6. Wording and framing (section 17) on the home page

**What differs:** labels that claim a cause or a judgment, or a number the
data doesn't support (section 17: rule 5 and the wording checklist; rule 5 in
`CLAUDE.md`).

**Evidence (session 1):**

| Where | Text today | Problem |
|---|---|---|
| Insight card (M21) | Title "Home Field Bias"; "This likely reflects crowd influence on officials" | "Bias" and "crowd influence" claim a cause |
| Insight card (M22) | '"Let Them Play" Effect'; "refs are reluctant to 'decide' games with late flags" | Claims a cause; the value (+24%, more flags in Q4) runs against the title |
| Insight card (M20) | "Penalty Surge Since 2022"; "jumped" | Stronger than the like-for-like change supports (+21.6%, C1) |
| Insight cards (M3, M23) | "the most lenient and strictest crews" | Checklist words (also C3) |
| Scoreboard (M18) | "Cleanest team" | Reads as a judgment of behavior |
| Section subtitle | "headline discoveries from five seasons of penalty data" | The data covers 12 seasons (2015–2026) |

**Options:**
- **A. Descriptive wording, item by item** (proposed text, for V2.0a step 5):
  - "Home and road penalties"
  - "Fourth quarter vs first quarter"
  - "Penalties per game since 2022" (with the same-weeks basis)
  - "Lowest and highest crew chief rates"
  - "Fewest flags per game"
  - "headline numbers from penalty data since 2015"
- **B. Keep the titles, soften the explanations only.** Effect: the titles
  still claim causes.

**Recommendation:** A. Titles are what people quote; the explanations alone
can't carry the caveat.

**Ty's decision:**

---

## C7. The home summary line compares with all of last season

**What differs:** the summary line at the top of the home page compares the
current season with **all** of last season, while "This Season vs Last" below
it defaults to the same weeks.

**Evidence:** `scripts/build_static.py` `home_summary()` uses the scoreboard's
`season` and `lastSeason` frames: "2026 games average 14.7 accepted penalties
through Week 7 (vs 12.7 in 2025)". The section below shows 14.7 vs **14.2**
(2025 Weeks 1–7). In 2025, Weeks 1–7 had more flags per game (14.21) than the
season as a whole (12.72), so the summary makes the rise look larger.

**Options:**
- **A. Same weeks:** "(vs 14.2 in Weeks 1–7 of 2025)". Effect: the summary
  line's comparison value changes.
- **B. Keep all of last season, labeled:** "(vs 12.7 over all of 2025)".
  Effect: the label changes only.

**Recommendation:** A (section 9: same weeks by default).

**Ty's decision:**

---

## C8. "All seasons" and "Since 2015": two windows, similar names

**What differs:** the comparison toggle's "All seasons" means 2015 to last
season (the current season left out). The scoreboard's "Since 2015" means
every season including the current one.

**Evidence:**
- `calculate_season_comparison()`: `all` = `prior_seasons` (2015–2025): 12.59
  per game, 2,895 games.
- `scripts/scoreboard.py`: `all` = `season >= 2015` (2015–2026): 12.7 per
  game, 3,002 games.
- Both use the key `all` in their JSON.

**Options:**
- **A. Prior seasons only, one name:** both mean 2015 to last season, labeled
  "2015–25". Effect: the scoreboard's "Since 2015" frame changes slightly
  (107 fewer games).
- **B. Keep both, with distinct labels:** "2015–25 (before this season)" and
  "2015–26 (including this season)". Effect: labels only.

**Recommendation:** A. A frame for comparing against is clearer when it never
contains the season being compared.

**Ty's decision:**

---

# Data errors (own issues)

## D1. Relocated teams: two team abbreviations joined

**What's wrong:** nflverse play-by-play uses **today's** team abbreviations
for every season (`LA`, `LAC`, `LV`, even in 2015). Schedules and game ids use
the abbreviations **of the time** (`STL` until 2015, `SD` until 2016, `OAK`
until 2019). Scripts that count a team's games from the schedule and its
flags from play-by-play mismatch for those seasons.

**Evidence (data at `9add749`):**
- **Scoreboard, "Since 2015":**
  - "Most flagged team: **LV, 12.0** flags per game" (Oakland-era flags over
    Las Vegas games only)
  - "Cleanest team: **STL, 0.0**" (games, no flags)
- **Team pages:**
  - LA's history starts in 2016, LAC's in 2017 and LV's in 2020.
  - Opponent rows show STL, SD and OAK separately, with 0 flags drawn (e.g.
    KC vs OAK: 10 games, 0.0).
  - Every team's flags drawn and rank for 2015–2019 are affected.
  - LV's "prior seasons" quarter rates add up to 12.2 per game against LV's
    actual prior rate of 6.07: the Oakland-era flags are divided by Las Vegas
    games.
- Full list of affected places: the issue for D1.

## D2. "Home Field Bias" card misstates its number

**What's wrong:** "Away teams are penalized 2.8% more than home teams". 2.8 is
the gap between the road share of penalties (51.4%) and the home share
(48.6%), in percentage points. Road teams were penalized **5.8%** more
(20,218 vs 19,117). `generate_insights()` (`home_bias`); entry M21.

## D3. "Most Common Call" card uses the wrong denominator

**What's wrong:** "7,671 total calls (26% of all penalties)". The share is of
the 10 most common types only (29,726); of all 39,335 penalties it's
**19.5%**. `generate_insights()` (`top_penalty`); entry M16.

## D4. Scoreboard crew leader uses incomplete crew assignments

**What's wrong:** the scoreboard's "Flag-heaviest crew" takes the crew chief
from the schedule's `referee` column only. That column is empty for 42 of the
107 games played (Weeks 5–7 not yet filled in), so crew rates use part of each
crew's games. Everything else uses the officials feed with two fallbacks.
- **Example:** "Scott Novak, 22.0 flags per game" is his first 4 games.
- `season_comparison.json` has him at 20.1 over all 7, and the summary line
  above shows that figure for the same crew.
- `scripts/scoreboard.py` `build_scoreboard()` (`referee` from the schedule)
  vs `update_data.py` `load_all_data()`.
