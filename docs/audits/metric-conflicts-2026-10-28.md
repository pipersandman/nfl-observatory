# Metric conflicts audit (2026-10-28)

Places where the site calculates or labels the same idea in different ways.
Found while building the metric dictionary ([`../METRICS.md`](../METRICS.md))
in V2.0a step 1 (#104).

**Ty's decisions are recorded (2026-10-29, session 11).** One rule for all of them: **no hard-coded years, windows or values in labels or text.** Every label that has a year or a value is computed from the data (for example C8's "2015–25").

**For each conflict, Ty picks one definition.** V2.0a step 2 then changes the
code to match (#76 keeps the Referee Variance card fix). This file only
records the conflicts and the decisions; it changes nothing on the site.

**Status:** session 11 of 11: Ty's decisions recorded (2026-10-29). The gameday worker test (session 10, Part 5) is still open.
Fields published but not displayed are listed after the conflicts. Data
errors are listed at the end; D1–D7, D9 and D10 are fixed, D8 is #112
(open), D11 and D12 are on #112 too (text-only fixes; later text-only errors go there).

## Summary

| ID | Conflict | Found in | Recommended | Ty's decision |
|---|---|---|---|---|
| C1 | Two meanings of "season" (playoffs in or out) | Known gap 3 | A: regular season only, everywhere | A: regular season only, everywhere (2026-10-29) |
| C2 | Offsetting-penalty plays counted as flags | Known gap 4 | A: accepted penalties only | A: accepted penalties only (2026-10-29) |
| C3 | Referee Variance card (#76) | #76 | A: rebuild as a labeled spread | A: rebuild as a labeled spread (2026-10-29) |
| C4 | Current season includes partial-week games; the same-weeks comparison doesn't | Session 1 | A: compare through the same last week | A: compare through the same last week (2026-10-29) |
| C5 | "Penalties" counts plays with an accepted penalty | Session 1 | B: keep "penalties", define it | B: keep "penalties", define it (2026-10-29) |
| C6 | Wording and framing (section 17) on the home page | Session 1 | A: descriptive wording, listed per item | A: descriptive wording (2026-10-29) |
| C7 | The home summary line compares with all of last season | Session 1 | A: same weeks, as the section below | A: same weeks (2026-10-29) |
| C8 | "All seasons" vs "Since 2015": two windows, similar names | Session 1 | A: prior seasons only, one name | A: prior seasons only, one name (2026-10-29) |
| C9 | Scorecard grades each game's last projection before kickoff (updates until then) | After PR #108 | A: keep it, say so plainly, show `frozenAt` | A: keep it, say so, show the save time (2026-10-29) |
| C10 | "League average" means three things on crew chief pages | Session 2 | A: the league's own rate, same games and window | A: the league's own rate, same games and window (2026-10-29) |
| C11 | "Career" means three different windows | Session 2 | A: 2015 to last season, regular season | A: 2015 to last season, regular season (2026-10-29) |
| C12 | Three measures of home vs road for one idea | Session 2 | B: home share with the league share beside it | **A, adjusted**: % more on road teams, league figure beside it (2026-10-29) |
| C13 | Wording and framing (section 17) on crew chief pages | Session 2 | A: descriptive wording, listed per item | A: descriptive wording (2026-10-29) |
| C14 | Season-adjusted and raw career rates under one label | Session 3 | A: raw by default; adjusted labeled each time | A: raw by default; adjusted labeled (2026-10-29) |
| C15 | Model estimates on crew style pages not labeled as estimates | Session 3 | A: label each estimate, observed count beside it | A: label each estimate (2026-10-29) |
| C16 | "Flags per game": a game total and one team's total under one label | Session 4 | A: separate names (and CSV column) | A: separate names (and CSV column) (2026-10-29) |
| C17 | Small samples handled four ways | Session 4 | A: one threshold (plan decision D13), one visible label | A: one threshold, one label (approach now) (2026-10-29) |
| C18 | Wording and framing (section 17) on team pages | Session 4 | A: descriptive wording, listed per item | A: descriptive wording (2026-10-29) |
| C19 | Trend text: fixed answers and stated causes | Session 5 | A: answers from the data; causes as possibilities | A: answers from the data (2026-10-29) |
| C20 | Averages of averages in the week-of-season text | Session 5 | A: games-weighted, with both rates | A: games-weighted, both rates (2026-10-29) |
| C21 | "League" in previews is the model's level, not the observed rate | Session 6 | A: name it the model's level; observed rate beside it | A: name it the model's level (2026-10-29) |
| C22 | Model estimates in previews: labels and attribution | Session 6 | A: label each as a model estimate | A: label as model estimates (2026-10-29) |
| C23 | "In the likely range": target ≈ 80% vs the range's design | Session 7 | A: state the model's expected share | A: state the expected share (2026-10-29) |
| C24 | Live and backtest projections mixed in one week summary | Session 7 | A: split mixed weeks | A: split mixed weeks (2026-10-29) |
| C25 | What Flags Cost: model estimates, precision and "erased" | Session 8 | A: label every modeled number; 1 decimal | A: label every modeled number (2026-10-29) |
| C26 | Live counts and win chances come from ESPN, final ones from nflverse | Session 8 | A: say so on the live strip too | A: say so on the live strip too (2026-10-29) |
| C27 | Two tie rules for ranks | Session 10 (cross-page pass) | A: ties share the higher rank, shown "T-22" | A: ties share the higher rank, "T-22" (2026-10-29) |

**Data errors (own issues):** wrong numbers on the live site, not definition
choices. (D-numbers here are data errors. The plan's decisions in
`docs/adr/0001-v2-decisions.md` are a separate list, D1–D19; this file calls
those "plan decision D<n>".) Each gets its own issue; the dictionary entries note them.

| ID | Error | Where | Issue |
|---|---|---|---|
| D1 | Relocated teams: two team abbreviations joined (STL/SD/OAK vs LA/LAC/LV) | `team_pages.py`, `scoreboard.py`, `stat_miner.py` | #105: **fixed** (PR #108, merged 2026-10-29) |
| D2 | "Home Field Bias" card misstates its number | `update_data.py` `generate_insights()` | #107: **fixed** (PR #109, merged 2026-10-29) |
| D3 | "Most Common Call" card uses the wrong denominator | `update_data.py` `generate_insights()` | #107: **fixed** (PR #109, merged 2026-10-29) |
| D4 | Scoreboard crew leader uses incomplete crew assignments | `scoreboard.py` | #107: **fixed** (PR #109, merged 2026-10-29) |
| D5 | Crew chief Home Bias explained as "how much more" | `app.js` `EXPLAINERS['home-bias']`, table legend | #110: **fixed** (PR #111, merged 2026-10-29) |
| D6 | Crew chief table labels don't match what it shows | `app.js` `EXPLAINERS['games']`, `index.html` | #110: **fixed** (PR #111, merged 2026-10-29) |
| D7 | Fixed league-average text out of date | `app.js` `EXPLAINERS['avg-per-game']`, `build_static.py` `/crew/` note | #110: **fixed** (PR #111, merged 2026-10-29) |
| D8 | Style Map explainer: "about 95 games each" | `app.js` `EXPLAINERS['crew-style-map']` | #112 (open; text-only fixes) |
| D9 | Touchdowns lost to offsetting penalties counted twice | `app.js` `renderFlagCost()`, `teamFlagCostHtml()` | #114: **fixed** (PR #115, merged 2026-10-29) |
| D10 | What Flags Cost: "≈ Wins given away" and "Own turnovers erased" columns swapped | `app.js` `renderFlagCost()` | #114: **fixed** (PR #115, merged 2026-10-29) |
| D11 | "How is this data collected?" says "updated weekly … on Tuesdays" | `app.js` `EXPLAINERS['data-methodology']` | #112 (open; text-only fixes, comment) |
| D12 | Cost method text leaves out "touchdown value" | `app.js` `renderFlagCost()`, `build_static.py` `guide_page()`, `flag_impact.py` `definitions` | #112 (open; text-only fixes, comment) |

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

**Evidence (sessions 1, 2 and 5):**
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
- **Crew chief pages (session 2, data at `5091e57`):** the same card, pop-up
  and static page mix both populations.
  - **Playoffs included:** `referees.json` and `referee/<slug>.json` career
    figures (M25 games, M26 rate, M27 range, M28 Home Bias, M29
    Consistency), `seasonStats` (the static page's "Season by season"),
    `penaltyTypes` (the card's "Most common"), `quarterDistribution` and
    `recentGames`.
  - **Regular season only:** the card's rate rows and the pop-up's "2026 vs
    history" block (`season_comparison.json`), `regularSeasonStats` (the
    pop-up's season chart, labeled "(regular season)"), and the per-game
    type and quarter comparisons.
  - **Example, Bill Vinovich:** the card header says "190 games" (177
    regular season + 13 playoff) above rate rows built from regular-season
    games. His 2015 season is **12.1 per game in 16 games** on the static
    page and **12.0 in 15** in the pop-up chart.
  - The pop-up labels one block "Career (all games incl. playoffs,
    2015–2026)"; the static page's season table doesn't say.
- **League trends (session 5, data at `53e0bd1`):** two by-season files with
  different rules.
  - **Regular season only:** `type_trends.json` (`scripts/type_trends.py`):
    every chart and table in The Big Picture, the static `/trends/` page, the
    guide and the three trend CSVs (M64–M70). The season explainer says
    "playoffs excluded".
  - **Playoffs included:** `trends.json`, which no chart reads; four home
    page cards are built from it (M16, M20, M21, M22).
  - **Example, 2025:** the season chart shows **12.72** per game (3,461
    penalties in 272 regular-season games); `trends.json` has **12.5** (3,559
    in 285 games, 13 of them playoffs, rounded to 1 decimal).
  - **Most common type:** the "Most Common Call" card says "Holding", 20%
    (7,671 of 39,335, playoffs in); the share chart's "Since 2015" says
    offensive holding 19.7% (7,481 of 38,028, regular season).

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

**Ty's decision (2026-10-29):** A. Regular season only, everywhere; playoffs shown separately where they're useful. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

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
  offsetting penalties as `offsetting_tds` (What Flags Cost, M94).

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

**Ty's decision (2026-10-29):** A. Accepted penalties only. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

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
  - crew chiefs above a minimum number of games (plan decision D13 threshold)
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

**Ty's decision (2026-10-29):** A. Rebuild the card as a labeled spread (range in penalties per game, each end's games count, crew chiefs above the plan decision D13 threshold, regular season); the fix stays in #76. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

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
- **Team pages (session 4, data at `53e0bd1`):** teams follow the crew chief
  rule. `scripts/team_pages.py` compares each team through the later of the
  league's last completed week and the team's latest game (`team_week`,
  M48). The index's button label uses the league's week, so on a day with a
  partial week a team card can read "2025 Wk 1–8" under a "2025 thru Wk 7"
  button. At `53e0bd1` every team's week is 7.
- **League trends (session 5):** "Which calls are rising?" works like the
  league tiles: the current rate includes partial-week games, the same-weeks
  comparison stops at the league's last completed week
  (`scripts/type_trends.py`, M69). The season chart is the exception: its
  "Weeks 1–N" bars leave the partial week out of the current season too
  (M64), so its two sides match.

**Options:**
- **A. Compare through the same last week:** the league comparison includes
  the previous season's games up to the partial week (as crew chiefs already
  do), or the current numbers leave the partial week out. Effect: league
  tiles change only while a week is in progress.
- **B. Leave it as it is, labeled:** the subtitle already names the partial
  games. Effect: none.

**Recommendation:** A, matching the crew chief rule, so both sides of every
comparison cover the same weeks (section 9).

**Ty's decision (2026-10-29):** A. Compare through the same last week. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

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

- **Gameday and the live strip (session 8):** live counts come from ESPN's
  box score, which counts **penalties**: two accepted flags on one play count
  twice (`worker/gameday/parse.js` `boxPenalties()`, M98). The same game is
  counted as plays on every other page once nflverse has it (C26).

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

**Ty's decision (2026-10-29):** B. Keep "penalties" and define it once: a play with at least one accepted penalty, counted once. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

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

**Ty's decision (2026-10-29):** A. Descriptive wording, item by item. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

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
- **Session 5:** the static `/trends/` summary ("14.7 accepted penalties
  through Week 7, vs 12.7 across all of 2025", labeled) and the guide's "Are
  NFL penalties up in 2026?" ("vs 12.7 in 2025", not labeled) use the same
  comparison (`build_static.py` `trends_page()`, `guide_page()`). The table
  just below the static summary uses the same weeks.
- **Session 6:** the preview pop-up's "Team discipline" badge compares
  each team's rate with all of last season (`previews.py` `discipline()`,
  M77); the team pop-up defaults to the same weeks (M48).

**Options:**
- **A. Same weeks:** "(vs 14.2 in Weeks 1–7 of 2025)". Effect: the summary
  line's comparison value changes.
- **B. Keep all of last season, labeled:** "(vs 12.7 over all of 2025)".
  Effect: the label changes only.

**Recommendation:** A (section 9: same weeks by default).

**Ty's decision (2026-10-29):** A. Same weeks, as the section below. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

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
- **League trends (session 5):** both windows in one section.
  `type_trends.json` → `scopeLabels.all` "Since 2015" (quarter and share
  charts, 2015–2026, 3,002 games) and `comparisons[allPrior]` "All seasons
  (2015–25)" ("Which calls are rising?", 2,895 games). The static
  `/trends/` page's quarter line says "Since 2015" (2015–2026); the guide's
  "Since 2015, Weeks 1–4 average …" uses 2015–25.

**Options:**
- **A. Prior seasons only, one name:** both mean 2015 to last season, labeled
  "2015–25". Effect: the scoreboard's "Since 2015" frame changes slightly
  (107 fewer games).
- **B. Keep both, with distinct labels:** "2015–25 (before this season)" and
  "2015–26 (including this season)". Effect: labels only.

**Recommendation:** A. A frame for comparing against is clearer when it never
contains the season being compared.

**Ty's decision (2026-10-29):** A. Prior seasons only, one name; the label (for example "2015–25") is computed from the data. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C9. Scorecard: which projection is graded

**What differs:** the scorecard grades each game's **last projection before
kickoff**. A game's projection isn't fixed when it's first saved: every data
run before kickoff replaces it, and after kickoff it never changes. Nothing on
the site says when a graded projection was made, so a visitor can't tell
whether it was the Tuesday number or one from minutes before kickoff.

**Evidence:**
- `scripts/scorecard.py`: the module notes say "every pipeline run saves the
  projection of every game that hasn't kicked off yet. 'Last update before
  kickoff wins'; once a game starts its projection is locked forever."
  `freeze()` skips a game once `now >= kickoff` (kickoff = `gameday` +
  `gametime`, US Eastern) and otherwise rewrites its record with a new
  `frozenAt`.
- The scorecard's own label: "Projections published on the site before
  kickoff" (`scorecard.py`, `live`).
- **Spot check** (read-only, every commit on `main` that touched
  `frontend/data/scorecard/live/`, up to `db4f788`): 98 commits, 56 games
  (Weeks 4–8 of 2026).
  - Changes after kickoff: **0**. Games whose `frozenAt` is after kickoff: **0**.
  - Before kickoff: 1,577 changes of `frozenAt` alone, and 257 that also
    changed projected numbers.
  - 29 of the 42 games played had their projected numbers change after the
    first save.
  - Last projection change before kickoff: median **42 hours**; closest **8
    minutes** (WAS @ SF, Week 6, at 8:07 pm ET for an 8:15 pm kickoff).
  - Measured by commit time; each file was written a few seconds before its
    commit.
  - **Corrected in session 7:** this check counted a change to *any* field
    of the record as a projection change. WAS @ SF's 8:07 pm change was to
    its `context` only (betting lines and similar); its projected numbers
    last changed at 11:33 am that day. The recount below separates the
    definitions.
- **Recount (session 7, up to `53e0bd1`, the same 98 commits plus 2):** 100
  commits, 56 live games, 42 played.

  | What counts as a change (played games) | Changes | Games changed after first save | Last change before kickoff: median | Closest |
  |---|---|---|---|---|
  | **Graded and shown:** total, home, away, range | 93 | 28 of 42 | **118 hours** | **45 min** (LA @ LV, Week 7) |
  | Any projection field (adds types, quarters, chance, yards, drivers, team ranges, league level) | 147 | 29 of 42 | 42 hours | 25 min (DEN @ ARI, Week 7) |
  | Any field except `frozenAt` (adds context, crew, model version) | 187 | 29 of 42 | 42 hours | 7 min (WAS @ SF, Week 6) |

  - Changes after kickoff: still **0**; `frozenAt` after kickoff: **0**.
  - **"Exactly as they appeared on the site":** every final live record
    equals the last preview committed before that game's kickoff (total,
    home, away, range): **56 of 56**.
  - **A frozen record keeps the model inputs of its last save:** BUF @ LV
    (Week 6) was saved on 2026-10-17 with dispersion 1.47, giving 8–19; the
    week's final preview file has 1.48, which gives 8–20. The graded 8–19 is
    what the site showed (working as built).
  - **Two graded projections come from social posts** (`live-post`, ATL @ NO
    and TB @ DAL), both saved before kickoff; the site calls them
    "published" like the rest (M81).
  - **`frozenAt` is shown nowhere:** not on the scorecard, its tables or the
    history ledger (`history/<week>` → `prediction.frozenAt` is stored, not
    displayed).

**Options:**
- **A. Keep "last projection before kickoff", and say so:** state it plainly
  on the scorecard and the methodology page, and show each graded
  projection's `frozenAt`. Effect: no numbers change; one line of text and a
  time per game. Note: `frozenAt` is the time of the **last save**, not of the
  last change (every run re-saves, hence the 1,577 changes of `frozenAt`
  alone), so it reads correctly as "projection as of", not as "last changed".
- **B. Grade a fixed snapshot,** for example Thursday noon ET (or the
  previous one for a Thursday game). Effect: graded projections and the
  scorecard's accuracy figures change; later projection updates aren't
  graded; the pipeline keeps a second record per game.

**Recommendation:** A. The last projection before kickoff uses the most
information (final crew assignment, latest data), and it's what a visitor saw
just before the game. The fix needed is transparency, not a different rule.

**Ty's decision (2026-10-29):** A. Keep "last projection before kickoff", say so plainly, and show each graded projection's save time (`frozenAt`, "projection as of"). Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C10. "League average" means three things on crew chief pages

**What differs:** a crew chief is compared with "the league average", but the
average isn't the same number in each place, and two of them sit in one
pop-up panel.

**Evidence (data at `5091e57`):**
- **The league's own rate, same window, regular season:**
  `season_comparison.json` → `league.current.perGame` (14.67 in 2026) and
  `league.baselines.all.perGame` (12.59, 2015–25, games-weighted). Used by
  the pop-up's "2026 so far" line (`app.js` `openRefereeModal()`), the static
  `/crew/<slug>/` summary and tiles (`build_static.py` `crew_pages()`), and
  the "Crew Chief Flag Rates" chart's marker (`renderPenaltiesByRefChart()`).
- **The mean of crew chiefs' career averages:** `generate_referee_profiles()`
  `league_avg = ref_stats['avg_per_game'].mean()` = **12.80**. Unweighted (a
  22-game crew chief counts as much as a 190-game one), playoffs included,
  each crew chief's average rounded to 1 decimal first, current season
  included. Used by the pop-up's "Career:" line (`tendencies.description`).
- **Fixed text:** the "Average Penalties Per Game" explainer: "League average
  is typically around 11-12 penalties per game" (D7).
- **Example, Bill Vinovich, one pop-up:** "In 2026 … 13.7 … vs a league
  average of 14.7" and, two lines below, "Career: Let-them-play style …
  1.8 fewer penalties per game" (11.0 vs 12.80). Against the league's
  2015–25 regular-season rate the same comparison is 11.02 vs 12.59 (−1.57).

**Options:**
- **A. The league's own rate for the same games and window, everywhere:**
  games-weighted, regular season (C1), the same seasons as the crew chief
  figure. The career line compares 2015–25 with 2015–25. Effect: every career
  comparison changes slightly; the mean of crews disappears.
- **B. Keep both, labeled:** "average of crew chiefs" vs "league average".
  Effect: no numbers change; two benchmarks remain.

**Recommendation:** A. A benchmark should cover the same games as the number
it's compared with (section 7), and one panel shouldn't show two league
averages.

**Ty's decision (2026-10-29):** A. The league's own rate for the same games and window, everywhere. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C11. "Career" means three different windows

**What differs:** "career" is used for three different sets of a crew
chief's games.

**Evidence (data at `5091e57`):**
- **Pop-up "Career (all games incl. playoffs, 2015–2026)"** and the
  Complete Crew Chief Stats table ("Crew Chief Statistics (All Seasons)"):
  `referees.json`, every game from 2015 including playoffs and the current
  season (M25–M29).
- **Static `/crew/` and `crew_chiefs_<season>.csv`:**
  `career_games_2015_25`, `career_flags_per_game_2015_25` and the "2015–25
  flags / game" column: `season_comparison.json` → `baselines.all`, regular
  season, seasons before this one. The CSV and the pop-up's legend call
  this "career" and "2015–25 avg".
- **`crew_styles.json`:** "Career = seasons before the current one"
  (regular season, 2015–25), as the static page's "Career (2015–25)" style
  (session 3).
- **Example:** Vinovich's "career" is 11.0 per game over 190 games in the
  pop-up and the table, and 11.02 over 171 games in the CSV. Moore: 16.5
  over 22 vs 16.12 over 16.
- Related: C8 ("All seasons" vs "Since 2015").

**Options:**
- **A. One meaning:** "career" = 2015 to last season, regular season (the
  `all` baseline; C1 and C8 option A), labeled "2015–25". The current season
  is always shown separately. Effect: the table, the pop-up's career block
  and M3/M23 change slightly.
- **B. Keep three, labeled:** each says its window and whether playoffs are
  in. Effect: labels only.

**Recommendation:** A, which follows from C1 and C8 option A.

**Ty's decision (2026-10-29):** A. "Career" = 2015 to last season, regular season, with the window computed from the data; the current season shown separately. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C12. Three measures of home vs road for one idea

**What differs:** the site describes "home vs road" with three different
measures, two of them under the name "bias".

**Evidence (data at `5091e57`):**
- **Percentage-point gap:** crew chief "Home Bias" (`referees.json` →
  `home_bias_pct`): road share minus home share, all games, playoffs in.
  Vinovich +2.5, Moore +8.2 (M28).
- **Relative difference:** the home page's "Home Field Bias" card since #107
  (`trends.json` → `homeVsAway.awayMorePct`): road ÷ home − 1, +5.8% for the
  league (M21). On that measure Vinovich is +5.2% and Moore +18.0%.
- **Home share:** the scoreboard's "Home or road" (`scoreboard.json` →
  `frames[].homeShare`: 49% since 2015, 50% in 2026, M15) and the style
  profile's `homeShare` with the league share as benchmark (`crew_styles.json`:
  Vinovich 48.9% over 171 games, league 48.6%), used in the static page's
  FAQ ("Does <name> call more penalties on the home team?").

**Options:**
- **A. Relative difference everywhere** ("road teams drew X% more flags"),
  with both counts. Effect: crew chief values roughly double (Moore 8.2 →
  18.0).
- **B. Home share everywhere, with the league share beside it**
  ("48.9% of flags on the home team; league 48.6%"), with counts. Effect:
  every crew chief value and the league card change form; "bias" leaves the
  labels.
- **C. Keep each, label each** with its unit (points, percent, share).
  Effect: labels only; three measures remain.

**Recommendation:** B. A share with the league share beside it reads
directly, compares crews fairly, already appears on the scoreboard and the
static pages, and doesn't need the word "bias" (C13). The home card's wording
is #76 and C6.

**Ty's decision (2026-10-29):** **A, adjusted** (not the recommended B): "% more on road teams", with the league figure beside it, everywhere, matching the home card fixed in #107. "Bias" leaves the labels. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C13. Wording and framing (section 17) on crew chief pages

**What differs:** labels and explanations on crew chief pages describe a
style, motive or use the numbers don't support (section 17: rule 5 and the
wording checklist). Same type of issue as C6, for session 2's pages.

**Evidence (`frontend/js/app.js` and `scripts/update_data.py`):**
- **Rates described as styles:** "Flag-heavy crew — expect more penalties
  than average", "Let-them-play style — fewer flags than average", "Tends to
  let minor infractions go", "League-average officiating style"
  (`generate_referee_profiles()` `tendencies.description`); "one of the more
  flag-heavy crews this season", "letting them play more than most this
  season" (`openRefereeModal()`); "Crew chiefs with higher averages run
  'flag-heavy' crews, while lower averages indicate a 'let them play' style"
  (explainer `avg-per-game`).
- **Causes and uses claimed:** "This likely reflects crowd influence on
  officials", "Research shows home bias is strongest in Q1 and fades" (no
  source; explainer `home-bias`); "This is the same method used by Vegas
  oddsmakers", "work with consistent crew members all season" (explainer
  `crew-chief`; the static pages say "crews change around the chief each
  year"); "more predictable for game planning and betting analysis",
  "Wildcard crew" (explainer `consistency`).
- **"Bias" as a label:** "Home Bias" column, card footer and pop-up stat
  (M28).
- **Colors:** Home Bias is red above 5 pts and green below 0. Red is the
  site's color for more penalties; here it marks road teams flagged more
  (the legend was fixed in #110, D5; the colors are unchanged).
- **Consistency called "Style"** in the pop-up (M29).
- **Crew styles (session 3, `scripts/crew_styles.py`, `app.js`):**
  - Quadrant names "Game-changers" and "Let them play" (`QUADS`, M44)
    describe an effect on games and a calling attitude; two averages above
    or below the league's show neither. The same names label the Style Map,
    the pop-up, the static pages, `/assignments/`, the CSV's `career_style`
    and game previews.
  - Quadrant colors: "Game-changers" red and "Let them play" green, but
    "Stop-and-start" (also more flags) yellow and "Few but costly" blue: red
    and green don't consistently mean more and fewer penalties.
  - Traits attribute rates to the crew chief: "Calls more roughing the
    passer", "Busier 4th quarters", "Cheaper flags" (`TRAIT_TEXT`, M42).

**Options:**
- **A. Descriptive wording, listed per item:** state the number and its
  comparison ("13.7 per game, 7% below the league's 14.7 in 2026, 6 games"),
  drop style and motive words, remove unsourced claims, keep red/green for
  more/fewer penalties only. Effect: no numbers change; many sentences
  change.
- **B. Keep the style words, with a caveat** under each ("describes the rate
  only"). Effect: the words stay.

**Recommendation:** A, as for C6. Wording changes go in V2.0a's wording step
with C6.

**Ty's decision (2026-10-29):** A. Descriptive wording, listed per item; red/green only for more/fewer penalties. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C14. Season-adjusted and raw career rates under one label

**What differs:** a crew chief's 2015–25 rates appear twice, once raw and
once season-adjusted, under the same labels ("flags per game", "yards per
flag"), sometimes in the same panel.

**Evidence (data at `53e0bd1`):**
- **Raw:** `season_comparison.json` → `crewChiefs[].baselines.all` (M1):
  the card's and pop-up's "2015–25" row, the static `/crew/` and
  `/crew/<slug>/` "2015–25 flags / game", the CSV's
  `career_flags_per_game_2015_25`.
- **Season-adjusted:** `crew_styles.json` → `crews[]` (M37, M38, M40): the
  pop-up's "Crew style" career tiles, the Style Map's career view, traits,
  the quadrant (M44).
- **Example, Alex Moore (16 games), one pop-up:** "2015–25" row **16.1**
  flags per game; "Crew style" tile **16.0** "Flags / game". Yards per flag:
  7.89 raw, **8.28** adjusted. Vinovich (171 games): 11.02 both ways.
- The pop-up's career footnote and the Style Map's subtitle say
  "season-adjusted"; the tiles, traits and static pages' style section
  don't (the type table's heading does).

**Options:**
- **A. Raw by default; adjusted only where it's labeled each time** (tile
  label "Flags / game, season-adjusted", with the raw value beside it).
  Effect: labels change; the quadrant and traits keep using adjusted values,
  labeled.
- **B. Adjusted everywhere for career figures**, raw only in a footnote.
  Effect: the card rows, static tiles and CSV change slightly.
- **C. Raw everywhere**; drop the adjustment. Effect: career styles and
  quadrants shift for crew chiefs whose seasons had unusual league levels
  (Moore's yards per flag 8.28 → 7.89).

**Recommendation:** A. The adjustment is useful for comparing crews across
eras, but a visitor reading one number twice should see why it differs.

**Ty's decision (2026-10-29):** A. Raw by default; season-adjusted only where labeled each time. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C15. Model estimates on crew style pages not labeled as estimates

**What differs:** rule 4 ("label model estimates as estimates; never present
them as observed facts"). Two crew style figures are estimates but read as
observed counts and rates.

**Evidence (data at `53e0bd1`):**
- **Shrunk penalty-type rates** (M41): each type's rate is pulled toward the
  league by 20 games' worth of the league rate (`crew_styles.py`
  `SHRINK = 20`). They appear as "How often they call each type vs the
  league" (pop-up), traits ("Calls more roughing the passer: 79% above the
  league rate"), the static type table ("Per game", "vs league rate") and
  the static FAQ ("What penalties does <name> call most? Per game, 2015–25:
  …").
  - **Example, Moore, roughing the passer:** shown **+79%** (0.73 per
    game). Observed: 15 in 16 games, **0.94** per game, +129% vs the
    league's 0.41.
  - The pop-up's footnote says rates are "pulled toward the league average
    so a few calls can't dominate", but no value is called an estimate, and
    the static pages don't say it.
- **Points per flag** (M39): built from nflverse's expected-points model
  for plays wiped out by the foul, and a fixed points-per-yard rate
  otherwise. Shown as "Points / flag" and "Cheaper flags: 0.80 points each
  (league 0.89)" with no explanation.

**Options:**
- **A. Label each as an estimate, with the observed count beside it:**
  "Roughing the passer: 15 in 16 games (0.94 per game); estimated 0.73 after
  adjusting for the small sample". Points per flag labeled "estimated cost
  in expected points" with a link to the method. Effect: no numbers change;
  labels and a count are added.
- **B. Show observed rates; use the shrunk values only to choose traits.**
  Effect: displayed type rates and "vs league" percentages change; traits
  quote observed values.

**Recommendation:** A. Shrinkage is the right tool for small samples (section
7), so keep it, and say what it is.

**Ty's decision (2026-10-29):** A. Label each estimate, with the observed count beside it. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C16. "Flags per game": a game total and one team's total under one label

**What differs:** "penalties per game" and "flags per game" mean both teams'
penalties in a game (league, crew chiefs) and one team's penalties (team
pages, scoreboard team leaders). The second is about half the first, and
each has its own "league average".

**Evidence (data at `53e0bd1`):**
- **Game total (M1):** home tile "Penalties per game" **14.7**; scoreboard
  "Flags per game" 14.7; crew chiefs "Pen / Game", "flags / game";
  `flags_by_season.csv` → `flags_per_game`.
- **One team (M46, M18):** team cards "penalties/game", pop-up "Pen/g",
  static `/team/<ABBR>/` tile "Flags / game", scoreboard "Most flagged team …
  9.3 flags per game"; `teams_<season>.csv` → `flags_per_game`.
- **Two league averages:** team cards "vs league avg **7.3**" and static
  team pages "league 7.3" (`teams/index.json` → `leaguePerGame`, per team per
  game, M47) beside the home page's league 14.7. Only the static `/team/`
  page says "per team per game".
- **Same column name, two meanings, one download page:** `flags_per_game` is
  14.7-scale in `flags_by_season.csv` and 7.3-scale in `teams_2026.csv`.

**Options:**
- **A. Separate names:** "per game" stays the game total (both teams); team
  rates become "flags on <team> per game" with "league average per team"
  beside them; the team CSV column becomes `team_flags_per_game`. Effect: no
  numbers change; labels and one CSV column name change.
- **B. Keep the labels, add a definition** under each team number ("one
  team's penalties; a game averages 14.7 for both teams"). Effect: no
  numbers or names change.

**Recommendation:** A. A label should mean one thing site-wide (section 6),
and a CSV column name is read without the page around it.

**Ty's decision (2026-10-29):** A. Separate names: "per game" stays the game total; team rates are "flags on <team> per game" with "league average per team"; the team CSV column becomes `team_flags_per_game`. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C17. Small samples handled four ways

**What differs:** rates from a few games are shown with four different rules:
a minimum to appear, a dimmed badge, a footnote, or nothing. The plan's
small-sample threshold (plan decision D13, V2.0a step 3) is still open.

**Evidence (data at `53e0bd1`):**
- **Minimum to appear:** team crew chief rows need 2 games
  (`team_pages.py` `MIN_CREW_GAMES`); the scoreboard's crew leader needs 3
  (M19).
- **Dimmed badge, no words:** under 4 games (`MIN_GAMES_FOR_PCT`): 175 of the
  847 team crew chief rows have 2 or 3 games. The static `/team/<ABBR>/`
  table lists the top 8 by rate, so it leads with small samples: LV's first
  row is Terry McAulay, 14.3 flags per game in 3 games (M60).
- **Footnote only:** "By opponent": "Few meetings = small samples"; 56 of 992
  rows rest on 2 meetings, none marked (M61). Pop-up: "Only <n> games this
  season — early numbers swing a lot" appears below 4 games only.
- **Nothing:** current-season ranks from 6 or 7 games ("#2 of 32", ties
  unmarked, M54); home and road rates from 3 or 4 games each (M52); the
  current season's bar on the season chart (M63).
- **Previews (session 6):** the context chips' averages show no window or
  sample: "Thursday night (avg 13.4 flags vs 13.1 Sunday)" is 47 Thursday
  games vs 535 Sunday games, 2024–26 (M79).

**Options:**
- **A. One threshold (plan decision D13), one visible label everywhere:** below it, the
  number shows a "small sample" label and its games count; lists that rank by
  rate leave out or mark rows below it. Effect: no numbers change; labels and
  some list orders change.
- **B. Keep each rule; add a games count wherever a rate is shown.**
  Effect: no numbers change; more columns.

**Recommendation:** A, decided with plan decision D13 in V2.0a step 3 (plan section 7:
games always shown, a small-sample label below the threshold).

**Ty's decision (2026-10-29):** A, the approach now: one threshold and one visible label everywhere. The threshold itself is set with plan decision D13 (V2.0a step 3). Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C18. Wording and framing (section 17) on team pages

**What differs:** labels on team pages judge or imply a cause the numbers
don't show. Same type of issue as C6 and C13.

**Evidence (`frontend/index.html`, `frontend/js/app.js`, `scripts/build_static.py`):**
- **"Team Discipline"** (section title, `index.html`): penalties per game
  reflect opponents, crews and play style as well as discipline.
- **"Watchlist (<season>)"** for the players flagged most (M59).
- **"Drawn":** "Drawn/g", "What they draw from opponents", "drew more than
  committed per game" (M49, M50, M56): describes opponents' flags as the
  team's doing.
- **"Came out ahead"** with green for a positive net in "By opponent" (M61):
  a flag count framed as a result.
- **Rankings without "observed":** "Most-penalized rank", "most and least
  penalized teams" (static `/team/` title), "#22 most in the NFL" (M54); the
  wording checklist asks for "observed" before a raw rate in a ranking.
- **Previews (session 6):** the pop-up repeats "🏈 Team discipline",
  "Watchlist" and "Drawn from opponents" (M77).
- **Red badge on "Drawn/g":** red marks more penalties on opponents. It
  follows the color rule (red = more flags), but reads as bad for the team.

**Options:**
- **A. Descriptive wording, listed per item:** "Team penalties", "Players
  flagged most", "Opponent flags", "Opponents flagged more per game",
  "Observed rank (most flags per game)"; net shown without green/"ahead".
  Effect: no numbers change; labels change.
- **B. Keep the sports terms ("drawn" is common usage), add definitions.**
  Effect: no wording changes except "Watchlist" and "came out ahead".

**Recommendation:** A, with C6 and C13 in V2.0a's wording step.

**Ty's decision (2026-10-29):** A. Descriptive wording, listed per item. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C19. Trend text: fixed answers and stated causes

**What differs:** some trend sentences are written in code rather than taken
from the data, or give a cause the data doesn't test (section 17: rule 5 and
"causal headlines"). Same type of issue as C6, C13 and C18.

**Evidence (`scripts/build_static.py`, `frontend/js/app.js`, `frontend/index.html`):**
- **Fixed answers:** the guide's "Are NFL penalties up in 2026?" always starts
  "Yes." and "Do refs call more penalties early in the season?" always starts
  "Usually." (`guide_page()`). Both hold at `53e0bd1` (14.7 vs 12.7; Weeks 1–4
  above Weeks 15–18 in all 11 seasons), but neither is checked: a season with
  fewer flags would still read "Yes."
- **Causes stated:** "partly because the two-minute drill packs in extra
  plays" (quarter chart subtitle, its explainer, static `/trends/`); "partly
  because of resting starters and games with nothing at stake" (guide; the
  week explainer says "play a part"). Neither is measured.
- **Previews (session 6):** the spread chip adds "(expected close — late
  flags tend to drop)" for spreads of 3 or less (`openPreviewModal()`), not
  measured anywhere on the site. The guide's "the chance of 15 or more
  flags" is fixed text; the page's threshold is the model's league level
  rounded, plus one (15 at `53e0bd1`, M72).
- **Section subtitle:** "How officiating patterns have evolved across
  seasons" (`index.html`), while the week explainer says "The data can't
  separate player discipline from officiating or game context."

- **What Flags Cost (session 8):** the guide's "The most costly flags are
  pass interference and personal fouls that hand the offense a first down on
  third down" (`guide_page()`, fixed text) fits the **average** flag (2026:
  defensive pass interference 1.64 points per flag, roughing the passer 1.09,
  third- or fourth-down first downs 1.62, all flags 0.89), but not the
  costliest single flags the page lists: 9 of 2026's 10 are offensive flags
  that erased a touchdown (4.16 points on average). Same issue: a fixed
  sentence about the data, not checked against it.

**Options:**
- **A. Answers from the data; causes as possibilities:** the guide's first
  word is computed ("Up" / "Down" / "About the same", with both rates and the
  window); causes are worded "possible reasons include …" or removed; the
  subtitle describes the data ("How penalty rates have changed across
  seasons"). Effect: no numbers change; sentences change.
- **B. Keep the text; add a check** that fails the build if "Yes." stops
  being true. Effect: no wording changes.

**Recommendation:** A, with C6, C13 and C18 in V2.0a's wording step.

**Ty's decision (2026-10-29):** A. Answers computed from the data; causes worded as possibilities or removed. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C20. Averages of averages in the week-of-season text

**What differs:** the weekly chart's averages are games-weighted, but the
sentences built from them average the weekly values as if every week had the
same games, and Week 18 has 5 seasons where Weeks 1–17 have 11. The fade is
also shown as a percentage without its two rates.

**Evidence (data at `53e0bd1`; `app.js` `renderWeekChart()`,
`build_static.py` `trends_page()`, `guide_page()`):**
- "Weeks 15–18 average about **19%** fewer than Weeks 1–4" (chart takeaway,
  static page): plain mean of four weekly averages, 11.02 vs 13.55.
- Games-weighted (Week 18: 80 games; Weeks 15–17: about 176 each): Weeks
  15–18 average **11.31**, **16.5%** fewer.
- "11% above the usual 13.3 for those weeks": the usual is a plain mean of
  the seven weekly averages (13.27); this season's 14.67 is games-weighted.
- The chart and static page give the 19% without the rates; the guide gives
  the rates (13.5, 11.0) without the percentage.

**Options:**
- **A. Games-weighted, with both rates:** "Weeks 15–18 average 11.3 flags per
  game, 2.2 fewer than Weeks 1–4 (13.6), 16% fewer (2015–25)". Effect: the
  fade changes from 19% to about 16%; the "usual" changes slightly.
- **B. Keep plain means, say so:** "average of the weekly averages". Effect:
  no numbers change.

**Recommendation:** A (section 9 comparable periods; rule 2: a percentage
with its baseline and absolute change).

**Ty's decision (2026-10-29):** A. Games-weighted, with both rates shown. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C21. "League" in previews is the model's level, not the observed rate

**What differs:** the previews compare each projection with "league" and
"league avg game", but that number is the model's own league level (this
season mixed with 2024–25, weighted), not the league's observed rate shown
everywhere else.

**Evidence (data at `53e0bd1`):**
- Cards "vs league **14.3**", pop-up "league avg game: 14.3", per-type badges
  "Total vs league" (`previews/<week>` → `model.leagueAveragePerGame`,
  `byType[].leagueTotal`; M73).
- Observed 2026 league rate: **14.67** per game (home tiles, scoreboard,
  season chart; M1, M64). Rebuilt model level: 14.25.
- The explainer says each projection "starts from the league's current
  penalty rate": it's the current season mixed with the 2024–26 weighted
  level using a prior of 100 team-games (214 team-games played, so about
  two-thirds current).
- The chance tile's threshold ("15+") comes from the same level.
- `scripts/scorecard.py` uses the same level as the "guess the league
  average" baseline for its skill figure (session 7, M85): the live guesses
  were 13.7–14.5, while the observed 2026 rate before each week was
  14.4–15.0. Skill is **+3.3%** against the model's level and **+5.2%**
  against the observed rate (3.48 vs 3.60 and 3.67 flags of average miss, 44
  games). The guide calls it "guessing the league average".

**Options:**
- **A. Name it for what it is:** "model's league level 14.3" (or "average
  matchup"), with the observed rate beside it once in the pop-up ("league so
  far: 14.7 in 107 games"). Effect: no numbers change; labels change.
- **B. Compare with the observed league rate:** badges and the chance
  threshold use M1's rate. Effect: every "vs league" badge and the threshold
  change (14.67 rounds to 15, so "16+").

**Recommendation:** A. The projection is built on the model's level, so that
is the fair benchmark; the label must say it isn't the observed rate
(section 17, rule 3).

**Ty's decision (2026-10-29):** A. Name it the model's league level, with the observed rate beside it. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C22. Model estimates in previews: labels and attribution

**What differs:** the projections are labeled "projected" and "likely", but
some labels present the model's split of its own estimate as an effect, and
the range's coverage is named only in the explainer.

**Evidence (`frontend/js/app.js` `openPreviewModal()`, `previewCard()`):**
- **Attribution as cause:** "Crew effect on this game +0.8, flags vs an
  average crew"; "What's driving the projection" (M76). The split is
  order-dependent (crew first, then home, then away), so the same projection
  could credit the crew differently.
- **Coverage unnamed:** "10–23 likely" and "likely 4–14" don't say 80% (the
  explainer does); the range covers game-to-game variation only, not
  uncertainty in the factors (M72).
- **Labeled well:** "projected flags" on the cards, pop-up, home page source
  and `/assignments/`, and the static page's note "our model's expected
  accepted penalties". Same type of issue as C15 (crew styles).

**Options:**
- **A. Label each as a model estimate:** "Model estimate: crew adds about
  +0.8 flags" with "one way to split the projection" in the footnote; "80%
  likely range". Effect: no numbers change; labels change.
- **B. Remove the drivers and crew-effect tiles;** keep the projection and
  range. Effect: two blocks disappear.

**Recommendation:** A, with C15.

**Ty's decision (2026-10-29):** A. Label each as a model estimate. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C23. "In the likely range": target ≈ 80% vs the range's design

**What differs:** the scorecard says the share of games inside the likely
range has a "target ≈ 80%", and the preview explainer says the range "covers
80% of likely outcomes". The range is built so that the model expects **more**
than 80% of games inside it.

**Evidence (`scripts/previews.py` `_poisson_nb_quantiles()`,
`scripts/scorecard.py` `_grade_games()`, data at `53e0bd1`):**
- The range is the 10th to the 90th percentile of the projection's negative
  binomial, in whole flags, and a game counts as inside when low ≤ actual ≤
  high (both ends). So the chance of landing inside is at least 90% − 10%,
  and with whole flags always a little more.
- **The model's own expected share**, using each week's dispersion: **83.5%**
  for the 56 live projections. Over every mean from 8 to 20 flags and
  dispersion from 1.1 to 3.0, the lowest is 80.5%: by design it can't be 80%.
- **What that does to the readings:** live 88.6% (44 games) is about 5 points
  above what the model expects (not 9 above the target); the 2025 backtest's
  80.1% (272 games) is about 3 points *below*, shown as on target.
- The hit rates themselves are computed correctly (M83: recomputed, a match).

**Options:**
- **A. State the expected share:** replace "target ≈ 80%" with the model's
  expected share for the same games ("model expects 84%; actual 89%"), and
  the explainer's "covers 80%" with "the model expects about 4 in 5 games, a
  little more, inside it". Effect: no numbers change; one label and one
  sentence change, plus one stored number per summary.
- **B. Make the range an exact 80% interval:** choose the bounds so the
  expected share is as close to 80% as whole flags allow (for example 10th
  to 90th percentile with one end exclusive, or a narrower pair). Effect:
  every range changes (narrower), every hit rate changes, and graded live
  projections can't be rebuilt, so live and backtest history would mix two
  definitions.

**Recommendation:** A. It keeps every published range as it was, and it
makes the comparison fair: a hit rate is judged against what the model
claimed for those games.

**Ty's decision (2026-10-29):** A. State the model's expected share beside the actual hit rate. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C24. Live and backtest projections mixed in one week summary

**What differs:** the scorecard keeps live and backtest projections apart
everywhere, but the history ledger's week summary averages whatever each game
has, and it says so only when the whole week is backtest.

**Evidence (`scripts/history.py` `_summary()`, `app.js`
`renderHistoryWeek()`, data at `53e0bd1`):**
- **2026 Week 4:** 16 games graded, **1 published** (ATL @ NO, a social post)
  and **15 backtest**; the week shows "4.4 avg miss · 75% in range" with no
  note (the "predates live tracking" footnote needs every game to be
  backtest). Each row has a "published" tag or not.
- The scorecard's live block counts only that one Week 4 game (3.0 miss, in
  range); its backtest block counts the other 15.
- Every other week is a single source at `53e0bd1` (2025 and 2026 Weeks 1–3
  all backtest; Weeks 5–7 all published).

**Options:**
- **A. Split mixed weeks:** the summary shows published and reconstructed
  figures on separate lines (or published only, with the count of
  reconstructed games). Effect: one week's summary changes; future
  first-weeks-of-tracking too.
- **B. Keep one summary, labeled:** "16 games: 1 published, 15
  reconstructed". Effect: a label only.

**Recommendation:** A, matching the scorecard: published and reconstructed
projections answer different questions (rule 3: estimates rebuilt afterward
aren't what visitors saw).

**Ty's decision (2026-10-29):** A. Split mixed weeks: published and reconstructed figures on separate lines. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C25. What Flags Cost: model estimates, precision and "erased"

**What differs:** points and win chances are model estimates (nflverse's
expected-points and win-probability models), and the block's notes say so
(`flag_impact.json` → `notes`: "Points and win chances are estimates"), but
the page shows them like observed counts, to two decimals, beside counts of
plays.

**Evidence (`frontend/js/app.js` `renderFlagCost()`, `teamFlagCostHtml()`,
`scripts/build_static.py`, data at `64e6587`):**
- **No "estimate" label** on "Points given away / game", "Season total",
  "≈ Wins given away" ("≈" only), the costliest flags' "pts" and "% win
  chance", the static `/team/` column and tiles, the `/trends/` and guide
  sentences. The `notes` sentence isn't displayed anywhere.
- **Two decimals** for a summed estimate with no interval ("9.53", "league
  6.51"), against section 6's rule (model estimates to the precision their
  interval supports).
- **Ranked "most costly first"** with no note that the rank reflects play
  volume and game situations as well as discipline (M90).
- **Wording:** "Points given away", "Drives stalled" (the footnote: "not
  proof the flag caused it"), field name `drivesKilled`; the costliest flag
  in the live strip: "−28%" with no "estimate".
- Same type of issue as C15 (crew styles) and C22 (previews).

**Options:**
- **A. Label every modeled number** ("Model estimate: expected points given
  away"), round per-game points to 1 decimal, show the `notes` sentence under
  the table, and keep "≈". Effect: no numbers change; labels and rounding
  change.
- **B. Move the modeled columns into their own block** ("Estimated cost"),
  separate from the counts (key first downs, touchdowns and turnovers
  erased). Effect: the table splits in two.

**Recommendation:** A, with C15 and C22 (section 17, rule 3).

**Ty's decision (2026-10-29):** A. Label every modeled number, per-game points to 1 decimal, and show the notes sentence. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C26. Live counts and win chances come from ESPN, final ones from nflverse

**What differs:** during games, `/gameday/` and the live strip count flags
and value them with ESPN's data; after each game, every other page uses
nflverse's. The same game can show two flag counts and two costs.

**Evidence (`worker/gameday/`, `frontend/js/gameday.js`, `livestrip.js`):**
- **Counts:** ESPN's box score counts penalties (two flags on one play count
  twice); nflverse-based pages count plays (C5). Between game weeks the live
  strip switches to the history ledger's nflverse counts (M87, M98).
- **Win chances:** ESPN's live win probability vs nflverse's model on What
  Flags Cost (M91, M99); the gameday note says "final expected-points and
  win-chance numbers appear on the site after each game".
- **Said on `/gameday/`** (its note), **not on the live strip**.
- **Not measured at `64e6587`:** no Week 8 game had finished, so the worker's
  counts weren't compared with nflverse's for a game.

**Options:**
- **A. Say so on the live strip too, and mark live numbers as live**
  ("live, ESPN · final numbers after the game"). Effect: labels only.
- **B. Count live flags as plays** (one per play with an accepted flag), to
  match the rest of the site. Effect: live counts change; the box score is
  used only as a check.

**Recommendation:** A now; B with C5's decision (if C5 keeps "plays", live
counts should follow).

**Ty's decision (2026-10-29):** A. Say so on the live strip too, and mark live numbers as live. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## C27. Two tie rules for ranks

**What differs:** the site ranks teams in two places with different rules
for ties, and both ranks sit in the same team pop-up.

**Evidence (data at `64e6587`):**
- **"Most-penalized rank"** (`team_pages.py`, M54): `rank(method='min')`,
  tied teams share the higher rank. KC and CIN, both 6.83 per game: **#22**
  each (the next is #24).
- **"#<n> of 32 most costly"** (`flag_impact.py` `_team_block()`, M90):
  sorted by the rounded points per game, then numbered 1, 2, 3…, so a tie is
  broken by the order the teams were listed (alphabetical). CHI and KC, both
  5.73: CHI **#21**, KC **#22**. 2025: ATL #21 and LAC #22 (5.21), BAL #24
  and PIT #25 (4.87).
- KC's pop-up shows both: "Most-penalized rank #22" (a shared rank) and "#22
  of 32 most costly" (an unshared one, behind a team with the same value).
- Neither rank says it's tied.

**Options:**
- **A. One rule: ties share the higher rank, shown as "T-22"**, for every
  rank on the site (ranked on the unrounded value). Effect: some What Flags
  Cost ranks change (KC #21 tied with CHI); tied ranks get a "T".
- **B. Keep both, labeled:** "ranked by points per game; ties in table order".
  Effect: a label only.

**Recommendation:** A (section 17, rule 1: a ranking names its metric, and a
tie shouldn't look like a difference).

**Ty's decision (2026-10-29):** A. One rule: ties share the higher rank, shown "T-22", ranked on the unrounded value. Plus the rule for every decision: no hard-coded years, windows or values in labels or text (see the top of this file).

---

## Cross-page pass

Session 10. Every idea used in more than one session, with the entries that
use it and the conflicts that cover it. **New in this pass: C27.** Everything
else is already covered; where several conflicts cover one idea, they should
be decided together (session 11).

| Idea | Entries | Covered by | Notes |
|---|---|---|---|
| "Flags per game" / "penalties per game" | M1, M18, M46, M47, M64, M65, M98 | C5, C16, C26 | A game total, one team's total, and live counts (penalties, not plays) under one label |
| "League average" | M35, M47, M73, M85, M90 | C10, C16, C21 | Five benchmarks: league rate (14.67), mean of crews (12.80), per team (7.34), the model's level (14.3), points per team-game (6.51). Decide C10, C16 and C21 together, so each name means one thing |
| "Season" and playoffs | M1, M16, M20–M22, M25–M31, M64 | C1 | `trends.json` and crew chief career figures include playoffs; every other page is regular season |
| "All seasons", "Since 2015", "career" | M1, M37, M48, M67–M70 | C8, C11, C14 | "Since 2015" includes the current season; "All seasons (2015–25)" and "career" don't, except where C11 lists |
| Home vs road | M15, M21, M28, M40, M52 | C12 | Four measures: share of flags, % more on road teams, the pts gap, per-game rates |
| Same weeks and partial weeks | M1, M48, M64, M69, M97 | C4, C7 | The league and type trends compare a partial week with a completed one; crew chiefs and teams follow their own week; summary lines use all of last season |
| Most common type | M16, M32, M55, M68, M77 | C1 | Card "Holding" (playoffs in) vs "Offensive Holding" everywhere else; the name shortening is recorded on M16 (wording step) |
| Rank and ties | M19, M54, M77, M90 | **C27**, C17, C18, C25 | Two tie rules (new); no "observed" (C18); small samples (C17); estimates ranked (C25) |
| Small samples | M2, M19, M52, M54, M60, M61, M63, M79 | C17 | One threshold is plan decision D13 (V2.0a step 3) |
| Model estimates vs observed | M37–M44, M71–M76, M81–M86, M89–M91, M99 | C14, C15, C21, C22, C23, C25 | Decide together: one labeling rule for every estimate |
| Red/green and arrows | M2, M28, M44, M49, M61, M82 | C13, C18 | Red = more penalties holds everywhere except Home Bias colors and quadrant colors (C13); "came out ahead" in green (C18) |
| Rounding | most entries | — | Recorded per entry, not a conflict (issue scope); V2.0a step 8 applies the section 6 defaults |
| Live vs final, frozen vs rebuilt | M71, M81, M87, M98, M99 | C9, C24, C26 | Live ESPN numbers, frozen projections, and rebuilt (backtest) ones, each labeled differently |
| "Drawn" | M49, M50, M56, M77 | C18 | — |
| Wording (section 17) | home page, crew chiefs, teams, trends, What Flags Cost | C6, C13, C18, C19, C25 | One wording step (V2.0a) for all five |
| Fixed text about the data | M24, M35, M37, M72, M89 | C19, D7, D8, D11, D12 | Sentences that state a number or fact in code rather than from the data |

**Links, both ways:** every C and D item is linked from at least one entry;
every entry's links resolve; an entry that mentions a C or D number lists it
under "Conflicts" (M24 now lists D11, M26 lists C13).

---

## Published but not displayed

Fields written to `frontend/data/` that no page, chart or static page reads.
They are deployed on every run. The dictionary entries mark them "not displayed" (M100 lists every field).

| ID | Field | Who uses it | Removing it would |
|---|---|---|---|
| P1 | `trends.json` → `byQuarterAndType` (shares by quarter for 6 types) | Nothing | Change nothing on the site. The quarter chart's type menu reads `type_trends.json` → `quarters.<scope>.types` (M67). |
| P2 | `trends.json` → `byQuarter` (counts by quarter, playoffs in) | The pipeline uses the same values in memory for the "Let Them Play" card (M22) before writing the file; no page reads the file's copy | Change nothing on the site, if the card keeps its calculation. The quarter chart reads `type_trends.json` → `quarters` (M67). |
| P3 | `trends.json` → `bySeason`, `homeVsAway`, `byType` | The pipeline (cards M20, M21, M16); the page reads them only in a fallback when `insights.json` is empty; `scripts/make_baseline.py` reads `bySeason` (local snapshot) | Remove the fallback cards' data and the baseline snapshot's source; decide with C1 (which season definition the cards use). |
| P4 | `previews/<season>-week-NN.json` for past weeks (Weeks 4–7 at `53e0bd1`) | No page (the page reads only the weeks listed in `previews/latest.json`). `scripts/scorecard.py` reads `model.leagueAveragePerGame` from them as a fallback baseline (session 7) | Change nothing on the site; the scorecard would need its baseline from elsewhere. Decide with session 7's scorecard files. |
| P5 | `scorecard/live/` (frozen projections, one file per week) | `scorecard.py` (grading) and `history.py` (the ledger's predictions); no page | Remove the record the scorecard is graded from. **Keep:** once a game kicks off its live record can't be made again. Only the deploy is optional (it could stay in the repository and not be uploaded). |
| P6 | `scorecard/backtest/` (rebuilt projections) | `scorecard.py`, `history.py` (earlier weeks); no page | They can be rebuilt (76 of 76 reproduced), so not deploying them loses nothing; keep them in the repository as the cache. |
| P7 | `history/snapshots/` (the league after each week) | Nothing reads them yet | Lose a record that can't be rebuilt later ("as it stood that week"). **Keep**; the deploy is optional. |
| P8 | `run_status.json` (each run's modules, warnings and raw capture) | The data workflow's "Fail if any module failed" step; no page | Lose the workflow's check. **Keep**; only deploying is optional. |
| P9 | `source_stamp.json` (play-by-play version and check time) | The pipeline (deciding whether nflverse changed); no page | Lose the change check. **Keep**; only deploying is optional. |

**Ty's decisions (2026-10-29):**
- **P1:** remove.
- **P2:** remove the file copy; keep the in-memory calculation (the "Let Them Play" card).
- **P3:** follows C1 (regular season).
- **P4:** keep.
- **P5, P6, P7:** keep, and keep deploying them: they're the evidence behind the scorecard, for the plan's "Verify" layer; Data & Methods will link to them later.
- **P8, P9:** keep.


Not in `frontend/data`, but also published and never shown: the gameday
feed's `games[].preview.low` and `.high` are always empty (the worker reads
`projection.low` / `.high`, which don't exist; the range is
`projection.range`; M98).

Other "not displayed" fields from sessions 1–9 (samples such as
`comparisons[].games`, timestamps, team yards and opponent counts) are listed
in the dictionary; every field of P5–P9's files is listed in M100. Most are samples the site should start showing (section
7), not removal candidates; session 10's cross-page pass adds any that are
neither.

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
- Full list of affected places: #105.

**Fixed:** #105, PR #108 (merged 2026-10-29). Schedules are mapped to today's
abbreviations as they're loaded (`scripts/teams.py`). At `5091e57`: "Since
2015" most flagged team **LV 6.9**, cleanest **CIN 5.7**; LA, LAC and LV
history starts in 2015; no `STL`, `SD` or `OAK` values remain in
`frontend/data/`.

## D2. "Home Field Bias" card misstates its number

**What's wrong:** "Away teams are penalized 2.8% more than home teams". 2.8 is
the gap between the road share of penalties (51.4%) and the home share
(48.6%), in percentage points. Road teams were penalized **5.8%** more
(20,218 vs 19,117). `generate_insights()` (`home_bias`); entry M21.

**Fixed:** #107, PR #109 (merged 2026-10-29). The card uses the new
`trends.json` → `homeVsAway.awayMorePct`: **+5.8%**, "Away teams are
penalized 5.8% more than home teams". `bias_pct` (2.8) and the card's styling
are unchanged.

## D3. "Most Common Call" card uses the wrong denominator

**What's wrong:** "7,671 total calls (26% of all penalties)". The share is of
the 10 most common types only (29,726); of all 39,335 penalties it's
**19.5%**. `generate_insights()` (`top_penalty`); entry M16.

**Fixed:** #107, PR #109 (merged 2026-10-29). The share is of all penalties:
"7,671 total calls (**20%** of all penalties)".

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

**Fixed:** #107, PR #109 (merged 2026-10-29). The scoreboard uses the merged
crew chief assignment (`data['officials']`, as `season_comparison.json`), and
shows the games: "Scott Novak, **20.1** flags per game · 7 games". Every 2026
game played has a crew chief (107 of 107). The week picker's leaders changed
the same way.

## D5. Crew chief Home Bias explained as "how much more"

**What's wrong:** the "What is Home Bias?" explainer (`frontend/js/app.js`
`EXPLAINERS['home-bias']`) says the number "measures how much more (or less)
the away team gets penalized compared to the home team, shown as a
percentage". The number is the road share minus the home share, in
percentage points (`calculate_referee_stats()` `home_bias_pct`), the same
mistake as D2. Entry M28.
- **Example (data at `5091e57`):** Alex Moore "+8.2%": road teams drew
  **18.0% more** flags in his games (197 vs 167). Bill Vinovich "+2.5%":
  5.2% more (1,072 vs 1,019).
- **Same table:** the legend "Above average" / "Below average" describes the
  column's colors, which are fixed cut-offs (red above 5, green below 0), not
  an average.
- Shown on the Meet The Officials cards, the Complete Crew Chief Stats table
  and the crew pop-up. The profile's `explanations.homeBiasPct` repeats the
  wording but isn't displayed.
- The choice of measure is C12; this error is only that the explanation
  doesn't match the number shown.

**Fixed:** #110, PR #111 (merged 2026-10-29). The explainer says the number
is "the road teams' share of the crew's penalties minus the home teams'
share, in percentage points (pts)", with a generic example; values show
**"pts"** on the cards, the table, the pop-up and the pre-filled table; the
legend reads "Home Bias above 5 pts" / "Home Bias below 0";
`explanations.homeBiasPct` has the same wording. At `53e0bd1`: Moore
**+8.2 pts**, Vinovich **+2.5 pts** (values unchanged).

## D6. Crew chief table labels don't match what it shows

**What's wrong:** two labels on the Complete Crew Chief Stats table
(`frontend/index.html`, `app.js` `EXPLAINERS['games']`) describe a different
set of numbers from the one shown.
- **"Games" explainer:** "Total number of regular-season games this crew
  chief has led in the data (2015 onward)". The column is `referees.json` →
  `games`, which includes playoffs: Bill Vinovich **190** (177 regular season
  + 13 playoff). Entry M25.
- **Section subtitle:** "All active head referees ranked by experience". The
  table lists all **28** crew chiefs since 2015, including the 11 not active
  in 2026 (17 active).

**Fixed:** #110, PR #111 (merged 2026-10-29). The explainer reads "Total
number of games this crew chief has led in the data (2015 onward), including
playoff games"; the subtitle reads "Every crew chief since 2015, most games
first".

## D7. Fixed league-average text out of date

**What's wrong:** the "Average Penalties Per Game" explainer (`app.js`
`EXPLAINERS['avg-per-game']`) says "League average is typically around
**11-12** penalties per game". In the data (regular season, play-by-play):
**12.59** for 2015–25 combined; seasons range from 11.18 (2022) to 13.82
(2015); **14.67** in 2026 so far. Only 2020–2023 fall in 11–12. Entries M26,
M35.
- Similar fixed text on the static `/crew/` page ("about 13.5 per game in
  2015–19, 11–13 since") is right for 2015–25 (13.50; 11.18 to 12.86 a
  season) but not for 2026 (14.67).

**Fixed:** #110, PR #111 (merged 2026-10-29). **No hard-coded number:** the
explainer reads "The league average for the same seasons is shown on the Crew
Chief Flag Rates chart and in each crew chief's profile". The `/crew/` note
takes its numbers from `season_comparison.json`, with windows: at `53e0bd1`,
"league average **12.6** per game in 2015–25, **14.7** in 2026 through Week 7".

## D8. Style Map explainer: "about 95 games each"

**What's wrong:** the "Crew Chief Style Map" explainer (`frontend/js/app.js`
`EXPLAINERS['crew-style-map']`) says "Career view uses each crew's regular
seasons before this one (**about 95 games each**)". At `53e0bd1` the 17
active crew chiefs have **128** career games on average (median 125, range
16 to 172; `crew_styles.json` → `crews[].games`). Entries M37, M38.
- The explainer's other claim, "under a yard per flag between crews", holds:
  career yards per flag run from 8.07 to 8.74.
- Same rule as D7: the fix shouldn't hard-code a new number. Either take it
  from `crew_styles.json`, which the page already loads, or say it without a
  number.

## D9. Touchdowns lost to offsetting penalties counted twice

**What's wrong:** `flag_impact.json` → `tdsErased` already includes
touchdowns lost to offsetting penalties (`tdsLostOffsetting` = "Of those"),
but the What Flags Cost table and the team pop-up added `tdsLostOffsetting`
again, and the tile's "<n> by own flags" showed `tdsErased`. JAX 2026 showed
**6** ("5 by own flags, 1 by offsetting"); actual **5** (4 + 1, recomputed
from play-by-play). GB 2026 3 (actual 2), NE 2025 4 (actual 3). Since
`502c440` (2026-10-20). Entry M94.

**Fixed:** #114, PR #115 (merged 2026-10-29), page only. Live after the
merge: JAX 5 (1 off.).

## D10. What Flags Cost: "≈ Wins given away" and "Own turnovers erased" columns swapped

**What's wrong:** the league table's row wrote `turnoversErased` under "≈
Wins given away" and `winsGivenAway` under "Own turnovers erased". GB 2026
showed "≈ Wins given away" **3** (its turnovers erased; actual 1.45), NYJ 3
(1.64), JAX 1 (1.78). Since `555c178` (2026-10-20). The team pop-up's tiles
were right. Entries M91, M95.

**Fixed:** #114, PR #115 (merged 2026-10-29), page only. Live after the
merge: GB 1.5.

## D11. "How is this data collected?" says "updated weekly … on Tuesdays"

**What's wrong:** the explainer (`frontend/js/app.js`
`EXPLAINERS['data-methodology']`) says "Data is updated weekly during the NFL
season, typically on Tuesdays after Monday Night Football". The data
workflow (`.github/workflows/update-data.yml`) runs about hourly through
Thursday night, Sunday and Monday night games, on Tuesday (06:00 and 19:00
UTC) and Wednesday (15:00 UTC), and on every push to `main`: 44 runs from
2026-10-22 to 2026-10-29 (10 scheduled, 30 on pushes, 4 started by hand). Entry M24. Text only: no number changes. Fix without a
fixed schedule ("updated during and after every game day"), or from
`stats.json` → `lastUpdated`, which the page already shows.

**Issue:** #112 (text-only fixes; comment added 2026-10-29).

## D12. Cost method text leaves out "touchdown value"

**What's wrong:** three descriptions of how a flag's cost is valued list
play value, penalty yards and two-point tries, but not **touchdown value**
(7 − expected points before the play − what the play kept), added in
`502c440`: the What Flags Cost footnote ("How it's valued: …",
`renderFlagCost()`), the guide's "How a penalty's cost is measured"
(`build_static.py` `guide_page()`), and `flag_impact.json` →
`definitions.method` (`flag_impact.py`). That method values 27 of 2026's
1,570 flags, and 9 of the 10 costliest the page lists. Entries M89, M96.
Text only: no number changes.

**Issue:** #112 (text-only fixes; comment added 2026-10-29).
