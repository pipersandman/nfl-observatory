# Metric conflicts audit (2026-10-28)

Places where the site calculates or labels the same idea in different ways.
Found while building the metric dictionary ([`../METRICS.md`](../METRICS.md))
in V2.0a step 1 (#104).

**For each conflict, Ty picks one definition.** V2.0a step 2 then changes the
code to match (#76 keeps the Referee Variance card fix). This file only
records the conflicts and the decisions; it changes nothing on the site.

**Status:** session 3 of 8 (home page, crew chiefs, crew styles). C1's trends
evidence is completed in the trends session. Data errors are listed at the
end; D1–D7 are fixed, D8 is drafted.

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
| C9 | Scorecard grades each game's last projection before kickoff (updates until then) | After PR #108 | A: keep it, say so plainly, show `frozenAt` | |
| C10 | "League average" means three things on crew chief pages | Session 2 | A: the league's own rate, same games and window | |
| C11 | "Career" means three different windows | Session 2 | A: 2015 to last season, regular season | |
| C12 | Three measures of home vs road for one idea | Session 2 | B: home share with the league share beside it | |
| C13 | Wording and framing (section 17) on crew chief pages | Session 2 | A: descriptive wording, listed per item | |
| C14 | Season-adjusted and raw career rates under one label | Session 3 | A: raw by default; adjusted labeled each time | |
| C15 | Model estimates on crew style pages not labeled as estimates | Session 3 | A: label each estimate, observed count beside it | |

**Data errors (own issues):** wrong numbers on the live site, not definition
choices. Each gets its own issue; the dictionary entries note them.

| ID | Error | Where | Issue |
|---|---|---|---|
| D1 | Relocated teams: two team abbreviations joined (STL/SD/OAK vs LA/LAC/LV) | `team_pages.py`, `scoreboard.py`, `stat_miner.py` | #105: **fixed** (PR #108, merged 2026-10-29) |
| D2 | "Home Field Bias" card misstates its number | `update_data.py` `generate_insights()` | #107: **fixed** (PR #109, merged 2026-10-29) |
| D3 | "Most Common Call" card uses the wrong denominator | `update_data.py` `generate_insights()` | #107: **fixed** (PR #109, merged 2026-10-29) |
| D4 | Scoreboard crew leader uses incomplete crew assignments | `scoreboard.py` | #107: **fixed** (PR #109, merged 2026-10-29) |
| D5 | Crew chief Home Bias explained as "how much more" | `app.js` `EXPLAINERS['home-bias']`, table legend | #110: **fixed** (PR #111, merged 2026-10-29) |
| D6 | Crew chief table labels don't match what it shows | `app.js` `EXPLAINERS['games']`, `index.html` | #110: **fixed** (PR #111, merged 2026-10-29) |
| D7 | Fixed league-average text out of date | `app.js` `EXPLAINERS['avg-per-game']`, `build_static.py` `/crew/` note | #110: **fixed** (PR #111, merged 2026-10-29) |
| D8 | Style Map explainer: "about 95 games each" | `app.js` `EXPLAINERS['crew-style-map']` | (drafted, session 3) |

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

**Evidence (sessions 1–2; trends side completed in session 5):**
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
  offsetting penalties as `offsetting_tds` (for What Flags Cost, session 7).

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

**Ty's decision:**

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

**Ty's decision:**

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

**Ty's decision:**

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

**Ty's decision:**

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

**Ty's decision:**

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

**Ty's decision:**

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
