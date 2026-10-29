# Metric dictionary (v0)

Every number the site publishes: what it counts, over which games and weeks,
and how it is rounded. Built in V2.0a step 1 (#104); format from
`docs/V2_BUILD_PLAN.md` section 6. Where two places calculate the same idea
differently, the entry links to the conflict in
[`audits/metric-conflicts-2026-10-28.md`](audits/metric-conflicts-2026-10-28.md).

**Status:** session 1 of 7 done (home page: summary line, This Season vs Last, The Scoreboard, What The Data Shows, update notice). Areas still to do are marked below. Entries are numbered in the order they were written, so numbers jump between sections.

## How to read an entry

- **One entry per metric, not per field.** The same metric shown for the
  league, a crew chief or a team is one entry; "Where it appears" lists every
  place.
- **Kind** is one of the four in plan section 5: raw count, exposure rate
  (per game), opportunity rate (per play or attempt; none published yet), or
  model estimate. Numbers that compare or summarize other metrics (a change
  between two periods, a spread across crews) are marked **derived**, with the
  kind of the metric they're built from.
- **Example values** come from the data committed at `9add749`
  (2026-10-28: 2026 regular season through Week 7). Later sessions state their
  own commit.
- **Rounding** records what the site shows today. Plan section 6 default:
  per-game rates to one decimal; percentages to whole numbers (one decimal
  below 10%); model estimates to the precision their interval supports; counts
  as integers. A difference is noted on the entry; V2.0a step 8 applies the
  rules.

## Terms used in every entry

- **Penalty (as counted):** a play where nflverse play-by-play has
  `penalty == 1`. That is a play with at least one **accepted** penalty,
  counted **once per play**. Spot check, 2026 regular season through Week 7
  (107 games):
  - **counted:** 1,570 plays, including 1,151 where the play didn't count
    (`no_play`: pre-snap fouls and plays wiped out by the penalty) and 10 in
    overtime
  - **not counted:** 156 plays where every penalty was declined, and 20
    offsetting-penalty plays
  - **one per play:** 5 plays had two or more penalties in the description
    and count once
- **Game:** a game with play-by-play in nflverse. Regular season only unless
  the entry says otherwise.
- **Through Week N:** the last regular-season week in which every scheduled
  game has been played (`scripts/weeks.py`, `completed_week()`). Games already
  played in the next week are the **partial week**.

## Entry template

```markdown
### M<n>. <Metric name>

| Field | Value |
|---|---|
| Label on site | The exact text visitors see for the number: tile title, card title, column header, chart title |
| Kind | Raw count / exposure rate / opportunity rate / model estimate (or derived: …) |
| Numerator | Which events count |
| Denominator | Games, plays, snaps, attempts (or none) |
| Population | Who: league, crew chiefs, teams; regular season, playoffs, overtime |
| Time window | Exact weeks and season boundaries; partial-week rule |
| Inclusion rules | Accepted, declined, offsetting, nullified |
| Benchmark | What it's compared with on the page (or none) |
| Calculation | Formula, weighting, missing data; `script.py` `function()` |
| Rounding | Stored precision → displayed precision; vs the section 6 default |
| Provenance | Source data; update cadence |
| Limitations | What it does not mean; known issues |
| Where it appears | JSON file → field; page → element; CSV → column |
| Example | Value at `9add749` |
| Conflicts | Links to the conflicts file, or none |
```

---

## Home: This Season vs Last

### M1. Penalties per game

| Field | Value |
|---|---|
| Label on site | League tile: "Penalties per game", with "vs 2025 Wk 1–7: **14.2**" beneath. Chart title: "Penalties Per Game By Crew Chief" (axis "Penalties per game"; tooltip unit "penalties/game"). Crew chief table header: "Pen / Game"; comparison column header = the comparison's short label (e.g. "2025 Wk 1–7"), values in the form "(<rate>/g, <games> g)". **Scoreboard:** "Flags per game"; running log column "Flags / game"; week menu "<rate> flags/game". **Summary line** (top of the home page): "<season> games average 14.7 accepted penalties through Week 7 (vs 12.7 in 2025)". |
| Kind | Exposure rate |
| Numerator | Penalties (as counted) by **both teams** in the games |
| Denominator | Games |
| Population | **League:** every regular-season game. **Crew chief:** the regular-season games the crew chief worked. Overtime included. Playoffs excluded. |
| Time window | **Current season:** every regular-season game played so far, **including any partial-week games**. **Comparison** (the toggle): `sameWeeks` = previous season, Weeks 1 to N (N = this season's through week; a crew chief who already worked a partial-week game is compared through that week); `lastSeason` = all of the previous regular season; `last3` = the three previous seasons; `all` = every season from 2015 to last season. Multi-season comparisons are games-weighted (total penalties ÷ total games). |
| Inclusion rules | Accepted penalties only, one per play; plays wiped out by the penalty count; declined-only and offsetting plays don't count (see Terms) |
| Benchmark | The selected comparison period, for the same league or crew chief. No league-average benchmark is shown beside a crew chief's rate. |
| Calculation | `penalties ÷ games`, from per-game totals of penalty plays. Games with no penalties count (as 0). `scripts/update_data.py` `calculate_season_comparison()` → `_season_block()`. **The scoreboard computes it again** in `scripts/scoreboard.py` `stats()` (`flags ÷ games` per timeframe and week), leaving out penalty plays with no `penalty_team` (0 in 2026). The summary line takes the scoreboard's value (`scripts/build_static.py` `home_summary()`). |
| Rounding | `season_comparison.json`: stored to 2 decimals → shown to 1 decimal (`fmtNum(…, 1)`). `scoreboard.json`: stored to 1 decimal. Matches the default. |
| Provenance | nflverse play-by-play (`penalty`, `season_type`), schedules (completed weeks) and officials (crew chief; filled from the schedule's `referee` column and Football Zebras assignments when the officials feed lags). Every data run. |
| Limitations | Counts flagged **plays**, not flags: two accepted penalties on one play count once. It's a game total for both teams, not one team's rate: team pages use a different per-game rate (one team's penalties), under similar labels; to check in session 3. A crew chief's rate reflects the games and teams they drew, not how strictly they call games (plan section 8). |
| Where it appears | **Home, This Season vs Last:** league tile "Penalties per game" (value and "vs" comparison); "Penalties Per Game By Crew Chief" bar chart (current-season and comparison bars); "Crew Chiefs in <season>" table, "Pen / Game" column and the comparison column's "(x/g, n g)". JSON: `season_comparison.json` → `league.current.perGame`, `league.baselines.<key>.perGame`, `crewChiefs[].current.perGame`, `crewChiefs[].baselines.<key>.perGame`. **Home, The Scoreboard:** "Flags per game" cell, the week menu and the running log (`scoreboard.json` → `frames[].perGame`, `weekFrames[].perGame`, `weeklyLog[].perGame`). **Summary line** (`index.html` `SEO:SUMMARY`, from `scoreboard.json` `season` and `lastSeason` frames). **Pre-filled page source** for search engines (`build_static.py` `home_prefill()`: `SEASON_LEAGUE` tiles and `SEASON_TABLE`, from `season_comparison.json`). *Sessions 2–6 add the crew pop-up, static pages and CSVs.* |
| Example | League 2026 through Week 7: **14.67** per game (1,570 penalties in 107 games), shown as 14.7. 2025 Weeks 1–7: 14.21 (1,535 in 108). Recomputed from play-by-play: 1,570 plays with `penalty == 1` in 107 games, a match. |
| Conflicts | [C4: partial-week games](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison); [C5: "penalties" counts plays](audits/metric-conflicts-2026-10-28.md#c5-penalties-counts-plays-with-an-accepted-penalty); [C7: summary line compares with all of last season](audits/metric-conflicts-2026-10-28.md#c7-the-home-summary-line-compares-with-all-of-last-season); [C8: "All seasons" vs "Since 2015"](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names); [D4: scoreboard crew assignments](audits/metric-conflicts-2026-10-28.md#d4-scoreboard-crew-leader-uses-incomplete-crew-assignments) |

### M2. Change vs comparison period (percent badge)

| Field | Value |
|---|---|
| Label on site | No label on the badge itself: "▲ 3.2%" / "▼ 4.0%" / "● 1.1%" / "new". Table legend: "▲ More than comparison", "▼ Fewer than comparison". Hover text: "+3.2%". |
| Kind | Derived: relative change between two exposure rates |
| Numerator | Current-season rate minus comparison-period rate |
| Denominator | Comparison-period rate |
| Population | Same as the rate it compares (league, or one crew chief) |
| Time window | Current season vs the period picked in the toggle (see M1) |
| Inclusion rules | Same as the rate it compares |
| Benchmark | The comparison period itself |
| Calculation | `(current − comparison) ÷ comparison × 100`, from the stored 2-decimal rates. No comparison value: badge reads "new". `frontend/js/app.js` `pctChange()`, `pctText()`, `pctBadge()` |
| Rounding | One decimal below 10%, whole number from 10% (`pctText()`). Matches the default. |
| Provenance | Computed in the browser from `season_comparison.json` |
| Limitations | **Shows only the percentage:** the absolute change and the baseline value sit beside it on the league tiles, but the crew chief table and bar labels show the percentage alone (rule 3 in `CLAUDE.md`; V2.0a step 4). Within ±2% the badge is gray "●" (`PCT_NEUTRAL`); above, red "▲" (more) or green "▼" (fewer): the arrow is the shape that goes with the color. Crew chiefs with fewer than 4 games this season get a dimmed badge (`MIN_GAMES_FOR_PCT`), with no text label saying why. |
| Where it appears | **Home, This Season vs Last:** league tiles (penalties per game, penalty yards per game, yards per penalty); bar-end labels on both crew chief charts; "Pen / Game" and "Yds / Game" columns of the crew chief table. *Later sessions add the crew and team pop-ups.* |
| Example | League penalties per game, 2026 vs 2025 Weeks 1–7: (14.67 − 14.21) ÷ 14.21 = **+3.2%**, shown "▲ 3.2%" in red. The absolute change (+0.46 per game) isn't shown. |
| Conflicts | [C4: partial-week games](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison) |

### M4. Penalties (count)

| Field | Value |
|---|---|
| Label on site | League tile: "<season> so far", value "1,570", beneath "penalties for **12,754** yards in **107** games". Crew chief table: "Penalties / Yards", values "<n> for <yards> yds". Scoreboard: "Flags" (beneath: "accepted penalties"); running log column "Flags". |
| Kind | Raw count |
| Numerator | Penalties (as counted) by both teams |
| Denominator | None |
| Population | As M1 (league or crew chief; regular season; overtime included) |
| Time window | As M1; scoreboard: the timeframe button (M10) |
| Inclusion rules | As in Terms |
| Benchmark | Tile: none for the count itself. Crew chief table: the comparison column shows the comparison period's count ("<n> for <yards> yds (x/g, n g)"). |
| Calculation | Count of penalty plays. `calculate_season_comparison()` → `_season_block()` (`penalties`); `scoreboard.py` `stats()` (`penalties`). |
| Rounding | Integer, with thousands separators. Matches the default. |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | Counts plays, not flags (C5). A count depends on how many games were played; compare rates (M1), not counts, across periods. |
| Where it appears | **This Season vs Last:** first league tile (`season_comparison.json` → `league.current.penalties`); crew chief table "Penalties / Yards" and comparison column (`crewChiefs[].current.penalties`, `crewChiefs[].baselines.<key>.penalties`). **Scoreboard:** "Flags" and the running log (`scoreboard.json` → `frames[].penalties`, `weekFrames[].penalties`, `weeklyLog[].penalties`). Pre-filled page source (`SEASON_LEAGUE`, `SEASON_TABLE`). |
| Example | 2026 through Week 7: 1,570 |
| Conflicts | [C5](audits/metric-conflicts-2026-10-28.md#c5-penalties-counts-plays-with-an-accepted-penalty) |

### M5. Penalty yards (count)

| Field | Value |
|---|---|
| Label on site | League tile: "… for **12,754** yards …". Crew chief table: "Penalties / Yards" ("<n> for <yards> yds"). Scoreboard: "Penalty yards"; running log column "Yards". |
| Kind | Raw count |
| Numerator | Yards assessed on penalty plays (`penalty_yards`, absolute value) |
| Denominator | None |
| Population | As M1 |
| Time window | As M1; scoreboard: the timeframe button |
| Inclusion rules | Penalty plays as in Terms. Yards are the enforced yards nflverse records for the play (one value per play, so a second accepted penalty's yards aren't added). Missing yards count as 0. |
| Benchmark | As M4 |
| Calculation | Sum of `abs(penalty_yards)`, missing values as 0. `calculate_season_comparison()` (`yards`, rounded to an integer); `scoreboard.py` `stats()` (`yards`). |
| Rounding | Integer. Matches the default. |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | The absolute value turns any negative recorded yardage into a positive one. Half-the-distance enforcements count the yards actually enforced, not the full penalty. |
| Where it appears | **This Season vs Last:** first league tile (`league.current.yards`); crew chief table (`crewChiefs[].current.yards`, `…baselines.<key>.yards`). **Scoreboard:** "Penalty yards" and the running log (`frames[].yards`, `weeklyLog[].yards`). Pre-filled page source. |
| Example | 2026 through Week 7: 12,754 |
| Conflicts | None |

### M6. Games (sample)

| Field | Value |
|---|---|
| Label on site | League tile: "… in **107** games". Crew chief table header "Games"; comparison column "(…, <n> g)". Scoreboard: "Games"; running log column "Games"; "in progress · <games> of <scheduled>". |
| Kind | Raw count (the denominator behind every per-game rate) |
| Numerator | Regular-season games with play-by-play |
| Denominator | None |
| Population | League: every game. Crew chief: games they worked (officials feed, then the schedule's `referee`, then Football Zebras assignments). Scoreboard "in progress" also uses the number of scheduled games in that week. |
| Time window | As M1 |
| Inclusion rules | A game counts once it has play-by-play in nflverse, whether or not it had a penalty |
| Benchmark | None |
| Calculation | `len(games)`. `calculate_season_comparison()` → `_season_block()` (`games`); `scoreboard.py` (`games`, `scheduled`). |
| Rounding | Integer |
| Provenance | nflverse play-by-play and schedules. Every data run. |
| Limitations | Shown beside crew chief rates in the table, but not on the bar charts or the league tiles' comparison values (V2.0a step 3). |
| Where it appears | **This Season vs Last:** first league tile (`league.current.games`); crew chief table "Games" and comparison column (`crewChiefs[].current.games`, `…baselines.<key>.games`). **Scoreboard:** "Games", running log, week menu (`frames[].games`, `weekFrames[].games`, `weekFrames[].scheduled`, `weeklyLog[].games`). |
| Example | 2026 through Week 7: 107 games (2025 Weeks 1–7: 108) |
| Conflicts | None |

### M7. Penalty yards per game

| Field | Value |
|---|---|
| Label on site | League tile "Penalty yards per game" (beneath: "vs 2025 Wk 1–7: **113.2**"). Chart title "Penalty Yards Per Game By Crew Chief" (axis "Penalty yards per game"; each row labeled "<name>" / "<n> yds · vs <n>"). Crew chief table header "Yds / Game". Scoreboard: "Penalty yards per game". |
| Kind | Exposure rate |
| Numerator | Penalty yards (M5) |
| Denominator | Games (M6) |
| Population | As M1 |
| Time window | As M1 |
| Inclusion rules | As M5 |
| Benchmark | As M1: the selected comparison period |
| Calculation | `yards ÷ games`. `_season_block()` (`yardsPerGame`); `scoreboard.py` `stats()` (`yardsPerGame`). |
| Rounding | Stored to 1 decimal; shown to 1 decimal on tiles and in the table; **whole yards on the chart's row labels** (`fmtNum(…)` with no decimals). Matches the default except the row labels. |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | As M1 and M5 |
| Where it appears | **This Season vs Last:** league tile (`league.current.yardsPerGame`, `league.baselines.<key>.yardsPerGame`); "Penalty Yards Per Game By Crew Chief" chart and the "Yds / Game" column (`crewChiefs[].current.yardsPerGame`, `…baselines.<key>.yardsPerGame`). **Scoreboard:** "Penalty yards per game" and the running log (`frames[].yardsPerGame`, `weeklyLog[].yardsPerGame`). Pre-filled page source. |
| Example | 2026 through Week 7: 119.2 (2025 Weeks 1–7: 113.2; ▲ 5.3%) |
| Conflicts | [C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison) |

### M8. Yards per penalty

| Field | Value |
|---|---|
| Label on site | League tile "Yards per penalty" (beneath: "vs 2025 Wk 1–7: **8.0**"). Scoreboard: "**8.1** yards per flag", beneath "Penalty yards per game". |
| Kind | Derived: average size of a penalty (yards ÷ penalties) |
| Numerator | Penalty yards (M5) |
| Denominator | Penalties (M4) |
| Population | As M1 (league only on the tile) |
| Time window | As M1 |
| Inclusion rules | As M5 |
| Benchmark | Tile: the selected comparison period. Scoreboard: none. |
| Calculation | `yards ÷ penalties` (0 when there are no penalties). `_season_block()` (`yardsPerPenalty`); `scoreboard.py` `stats()` (`yardsPerPenalty`). |
| Rounding | 1 decimal |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | Per penalty play: a play with two accepted penalties has one yardage. Labeled "per penalty" on the tile and "per flag" on the scoreboard (C5). |
| Where it appears | **This Season vs Last:** league tile (`league.current.yardsPerPenalty`, `league.baselines.<key>.yardsPerPenalty`). **Scoreboard:** under "Penalty yards per game" (`frames[].yardsPerPenalty`). Pre-filled page source. Also stored per crew chief (`crewChiefs[].current.yardsPerPenalty`), not shown in this section. |
| Example | 2026 through Week 7: 8.1 (2025 Weeks 1–7: 8.0) |
| Conflicts | [C5](audits/metric-conflicts-2026-10-28.md#c5-penalties-counts-plays-with-an-accepted-penalty) |

### M9. Data through (completed week)

| Field | Value |
|---|---|
| Label on site | Section subtitle: "Regular season through Week 7 (plus <k> games from Week 8), compared with 2025 through week 7." (the part in brackets only while a week is in progress). Toggle button "2025 thru Wk 7". Section title "<season> Season". Scoreboard: "Week 7" button; week menu "in progress · <k> of <n>". Summary line: "through Week 7". |
| Kind | Time window marker (not a metric) |
| Numerator / Denominator | None |
| Population | League schedule, regular season |
| Time window | The last regular-season week in which every scheduled game has been played; games already played in a later week are the partial week |
| Inclusion rules | A game counts as played when it has play-by-play |
| Benchmark | None |
| Calculation | `scripts/weeks.py` `completed_week()`, used by `calculate_season_comparison()` (`throughWeek`, `partialWeek`), `scoreboard.py` (`throughWeek`, `partialWeek`, `defaultWeek`) and `team_pages.py` |
| Rounding | Integer week |
| Provenance | nflverse schedules and play-by-play. Every data run. |
| Limitations | "Week" is the NFL schedule week, not a calendar week. A postponed game holds the completed week back until it's played. The subtitle lowercases the comparison label's first letter, which leaves "2025 through week 7" with a lowercase "week". |
| Where it appears | `season_comparison.json` → `currentSeason`, `previousSeason`, `throughWeek`, `partialWeek`, `baselines[].label`/`short`/`seasons`; `scoreboard.json` → `throughWeek`, `partialWeek`, `defaultWeek`, `frames[].label`/`description`, `weekFrames[].complete`/`scheduled`. Summary line and pre-filled page source (`SEASON_SUB`). |
| Example | Week 7, no partial week |
| Conflicts | [C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison) |

---

## Home: The Scoreboard

Inside "This Season vs Last". Every scoreboard number is computed in
`scripts/scoreboard.py` `build_scoreboard()` → `stats()`, written to
`scoreboard.json`, and is **regular season, accepted penalties** (footnote:
"Regular season. Accepted penalties. Plays = snaps plus pre-snap penalty
plays.").

### M10. Scoreboard timeframes

| Field | Value |
|---|---|
| Label on site | Title "The Scoreboard"; description "<frame description> · accepted penalties" (e.g. "2026 regular season so far · accepted penalties"). Buttons: "Week 7" (with a week menu), "2026 season", "2025", "2023–25", "Since 2015". Running log heading "2026 running log". |
| Kind | Time window definitions (not a metric) |
| Numerator / Denominator | None |
| Population | League, regular season |
| Time window | `latestWeek`: the completed week (any week of the current season from the menu, including one in progress). `season`: every current-season game so far, including partial-week games. `lastSeason`: all of last season. `last3`: the three seasons before this one. **`all`: every season from 2015, including the current one.** |
| Inclusion rules | As in Terms |
| Benchmark | None: frames are shown one at a time, not compared |
| Calculation | `build_scoreboard()` `frames`, `weekFrames`, `weeklyLog` |
| Rounding | — |
| Provenance | nflverse schedules and play-by-play. Every data run. |
| Limitations | "Since 2015" includes the current season, while the comparison toggle's "All seasons" doesn't (C8). The default frame is the season so far. |
| Where it appears | `scoreboard.json` → `frames[].key`/`label`/`description`, `defaultFrame`, `weekFrames[]`, `defaultWeek`, `notes` |
| Example | Default: "2026 season" (107 games) |
| Conflicts | [C8](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names) |

### M11. Plays (count)

| Field | Value |
|---|---|
| Label on site | "Plays"; running log column "Plays" |
| Kind | Raw count |
| Numerator | Snaps (`play_type` run, pass, punt, field goal, kickoff, extra point, kneel, spike) plus `no_play` rows that had a penalty (pre-snap fouls that never became a snap) |
| Denominator | None |
| Population | League, regular season, the timeframe |
| Time window | The timeframe (M10) |
| Inclusion rules | Plays wiped out by a live-ball penalty are `no_play` with a penalty, so they count once |
| Benchmark | None |
| Calculation | `scripts/update_data.py` `load_all_data()` (`SNAP_TYPES`, `plays_per_game`), summed per frame in `stats()` |
| Rounding | Integer |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | Includes kickoffs, punts and extra points, so it isn't the scrimmage-play count a "per 100 offensive plays" rate would need (section 5). |
| Where it appears | Scoreboard "Plays" and the running log (`frames[].plays`, `weekFrames[].plays`, `weeklyLog[].plays`) |
| Example | 2026 season: 17,372 |
| Conflicts | None |

### M12. Plays with a flag (share of plays)

| Field | Value |
|---|---|
| Label on site | "Plays with a flag", value "9.0%"; beneath "a flag every **11.1** plays". Running log column "% of plays". |
| Kind | Opportunity rate (penalty plays per play), and its inverse (derived) |
| Numerator | Penalties (M4) |
| Denominator | Plays (M11) |
| Population | League, regular season, the timeframe |
| Time window | The timeframe |
| Inclusion rules | As M4 and M11 |
| Benchmark | None |
| Calculation | `pctPlays = penalties ÷ plays × 100`; `flagEveryPlays = plays ÷ penalties`. `stats()`. |
| Rounding | Percent to 1 decimal (below 10%, so it matches the default; it would stay at 1 decimal above 10%). "Every N plays" to 1 decimal. |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | The one published rate per play: the denominator includes special-teams snaps (M11). |
| Where it appears | Scoreboard (`frames[].pctPlays`, `frames[].flagEveryPlays`, `weeklyLog[].pctPlays`) |
| Example | 2026 season: 9.0%; every 11.1 plays |
| Conflicts | None |

### M13. Minutes of game clock per flag

| Field | Value |
|---|---|
| Label on site | Beneath "Flags per game": "one every **4.1** min of game clock" |
| Kind | Derived: inverse of penalties per game, in minutes |
| Numerator | 60 minutes |
| Denominator | Penalties per game (M1, scoreboard version) |
| Population | League, regular season, the timeframe |
| Time window | The timeframe |
| Inclusion rules | As M1 |
| Benchmark | None |
| Calculation | `60 ÷ (penalties ÷ games)`. `stats()` (`minutesPerFlag`). |
| Rounding | 1 decimal |
| Provenance | Computed from M1 |
| Limitations | Assumes 60 minutes a game: overtime minutes aren't added, while overtime penalties are counted. |
| Where it appears | Scoreboard (`frames[].minutesPerFlag`) |
| Example | 2026 season: 4.1 |
| Conflicts | None |

### M14. First downs by penalty

| Field | Value |
|---|---|
| Label on site | "First downs by penalty", value "432"; beneath "**4.0** per game handed over". Running log column "1st downs". |
| Kind | Raw count, and its exposure rate |
| Numerator | Penalty plays where nflverse marks `first_down_penalty == 1` |
| Denominator | Games (for the per-game figure) |
| Population | League, regular season, the timeframe |
| Time window | The timeframe |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | `stats()` (`firstDowns`, `firstDownsPerGame`) |
| Rounding | Count integer; per game 1 decimal |
| Provenance | nflverse play-by-play (`first_down_penalty`). Every data run. |
| Limitations | "Handed over" says the penalty gave the first down; nflverse's field marks a first down awarded by penalty, and whether the offense would have gained one on the play anyway isn't recorded. To check in session 6 against What Flags Cost's "key first down given". |
| Where it appears | Scoreboard (`frames[].firstDowns`, `frames[].firstDownsPerGame`, `weeklyLog[].firstDowns`) |
| Example | 2026 season: 432 (4.0 per game) |
| Conflicts | None yet |

### M15. Share of penalties: offense, pre-snap, home

| Field | Value |
|---|---|
| Label on site | Three split bars: "Who gets flagged" ("**59%** offense" / "defense **41%**"); "Before or after the snap" ("pre-snap" / "live ball"); "Home or road" ("home team" / "road team") |
| Kind | Derived: shares of a raw count |
| Numerator | **Offense:** penalties where `penalty_team == posteam`. **Pre-snap:** penalties whose `penalty_type` is in a fixed list of 13 pre-snap fouls (`PRE_SNAP` in `scoreboard.py`). **Home:** penalties where `penalty_team == home_team` (play-by-play's home team). |
| Denominator | Penalties (M4) |
| Population | League, regular season, the timeframe |
| Time window | The timeframe |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | `stats()` (`offenseShare`, `preSnapShare`, `homeShare`); the second half of each bar is 100 minus the first |
| Rounding | Whole percent. Matches the default. |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | "Offense" is the team nflverse lists as having possession (`posteam`); on kicking plays that isn't the offense in the everyday sense, so special-teams fouls are split by that field. The pre-snap list is fixed in code; types outside it count as live ball. The home team at neutral sites is the designated one. |
| Where it appears | Scoreboard (`frames[].offenseShare`, `frames[].preSnapShare`, `frames[].homeShare`) |
| Example | 2026 season: offense 59%, pre-snap 38%, home 50% |
| Conflicts | None |

### M18. Team penalties per game (scoreboard leaders)

| Field | Value |
|---|---|
| Label on site | "Most flagged team" ("GB", "**9.3** flags per game"); "Cleanest team" ("IND", "**5.1** flags per game"). Summary line: "Most penalized team: <team> (<rate> per game)". |
| Kind | Exposure rate |
| Numerator | Penalties on **one team** |
| Denominator | That team's games |
| Population | Every team that played in the timeframe, regular season; no minimum games |
| Time window | The timeframe (scoreboard); the current season so far (summary line) |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | **Scoreboard:** `stats()`: team games from the schedule's `home_team`/`away_team`, flags from play-by-play `penalty_team` (`mostFlaggedTeam`, `cleanestTeam`). **Summary line:** `teams/index.json` → highest `perGame` (`team_pages.py`; session 3). |
| Rounding | 1 decimal |
| Provenance | nflverse schedules and play-by-play. Every data run. |
| Limitations | A team's own penalties, under the same "flags per game" label as M1's game total (both teams), at about half the value. **Wrong for "Since 2015"** (D1): LV 12.0, STL 0.0. "Cleanest" reads as a judgment (C6). In a week frame each team has one game. |
| Where it appears | Scoreboard leaders (`scoreboard.json` → `frames[].mostFlaggedTeam`, `frames[].cleanestTeam`). Summary line (`index.html` `SEO:SUMMARY`). *Session 3 adds the team pages.* |
| Example | 2026 season: GB 9.3 (most), IND 5.1 (fewest). "Since 2015": LV 12.0, STL 0.0 (D1). |
| Conflicts | [D1](audits/metric-conflicts-2026-10-28.md#d1-relocated-teams-two-team-abbreviations-joined), [C5](audits/metric-conflicts-2026-10-28.md#c5-penalties-counts-plays-with-an-accepted-penalty), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

### M19. Crew chief with the most penalties per game (leaders)

| Field | Value |
|---|---|
| Label on site | Scoreboard: "Flag-heaviest crew" ("Scott Novak", "**22.0** flags per game"). Summary line: "Most flags per game: <name>'s crew (20.1)". |
| Kind | Exposure rate (the highest crew chief value of M1) |
| Numerator / Denominator | As M1, for one crew chief |
| Population | **Scoreboard:** crew chiefs with at least 3 games in the timeframe (1 in a frame of 16 games or fewer), crew chief from the schedule's `referee` column only. **Summary line:** every crew chief with a game this season, from `season_comparison.json` (officials feed with fallbacks), no minimum. |
| Time window | Scoreboard: the timeframe. Summary line: the current season so far. |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | Scoreboard: `stats()` (`topCrew`). Summary line: `build_static.py` `home_summary()` (first of `crews_now`, sorted by `current.perGame`). |
| Rounding | 1 decimal |
| Provenance | nflverse play-by-play, schedules and officials. Every data run. |
| Limitations | **The two pick from different assignments** (D4): the schedule's `referee` column is empty for 42 of 107 games, so the scoreboard rates Scott Novak on 4 of his 7 games. No games count is shown with either. A leader on a few games is a small sample (section 7). |
| Where it appears | Scoreboard (`scoreboard.json` → `frames[].topCrew`); summary line |
| Example | Scoreboard: Scott Novak 22.0 (4 games). Summary line: Scott Novak 20.1 (7 games). |
| Conflicts | [D4](audits/metric-conflicts-2026-10-28.md#d4-scoreboard-crew-leader-uses-incomplete-crew-assignments), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

Also on the scoreboard: "Most common call" (M16), "Flags per game" (M1),
"Flags" (M4), "Penalty yards" (M5), "Games" (M6), "Penalty yards per game"
(M7) and "yards per flag" (M8).

---

## Home: What The Data Shows (insight cards)

### M3. Referee Variance

| Field | Value |
|---|---|
| Label on site | Card title: "Referee Variance"; value "9%"; description "Crew chiefs range from 11.0 to 16.5 penalties/game"; explainer headed "What this means:". |
| Kind | Derived: spread of an exposure rate across crew chiefs (coefficient of variation) |
| Numerator | Standard deviation of crew chiefs' career penalties per game |
| Denominator | Mean of the same crew chiefs' career penalties per game |
| Population | Every crew chief with at least one game, 2015 to now (28 at `9add749`, from 22 to 190 games). **Regular season and playoffs** (no `season_type` filter). Unweighted: each crew chief counts once, whatever their games. |
| Time window | Career: every season from 2015, including the current partial season |
| Inclusion rules | Accepted penalties, one per play (see Terms). Games with no penalty at all are left out of a crew chief's average (inner join); this should be rare. |
| Benchmark | None. The card turns "positive" (green styling) below 15% (`isPositive`). |
| Calculation | `std(avg_per_game) ÷ mean(avg_per_game) × 100`, where `avg_per_game` is each crew chief's mean penalties per game, **rounded to 1 decimal first**. `scripts/update_data.py` `calculate_referee_stats()` → `generate_insights()` (`ref_variance`). The description's range is the min and max of the same `avg_per_game`. |
| Rounding | Value: whole percent (`:.0f`). Range: 1 decimal. Matches the default. |
| Provenance | nflverse play-by-play and officials, 2015 to now. Every data run. |
| Limitations | **Different population from the rest of the home page:** it includes playoffs, which `season_comparison.json` leaves out because playoff games are worked by all-star crews. No minimum games: a crew chief with few games moves the spread as much as one with many. The explanation refers to "the spread" (never shown) and to "the most lenient and strictest crews" (against the section 17 wording checklist). There's no games count beside the rates, and the green "positive" styling reads as a judgment. |
| Where it appears | **Home, What The Data Shows:** "Referee Variance" card (value, description). JSON: `insights.json` → item `id: ref_variance` (`value`, `description`, `explanation`, `isPositive`). Also computed by the same formula into `stats.json` → `refereeVariance`, which the site doesn't display. |
| Example | **9%**; "Crew chiefs range from 11.0 to 16.5 penalties/game": Bill Vinovich 11.0 (190 games) to Alex Moore 16.5 (22 games). |
| Conflicts | [C3: Referee Variance card](audits/metric-conflicts-2026-10-28.md#c3-referee-variance-card-76); also C1 (season meaning: playoffs included here) |

### M20. Penalty Surge (change in penalties per game since 2022)

| Field | Value |
|---|---|
| Label on site | Card title: "Penalty Surge Since 2022"; value "+32%"; description "Penalties per game jumped from 11.1 to 14.7". |
| Kind | Derived: relative change between two exposure rates |
| Numerator | Latest season's penalties per game minus 2022's |
| Denominator | 2022's penalties per game |
| Population | League. **Regular season and playoffs** (`trends.json` has no `season_type` filter). Games: only games with at least one penalty (`game_id` counted from penalty plays). |
| Time window | 2022 (full season, playoffs included) vs the latest season in the data (2026: regular season through Week 7, partial) |
| Inclusion rules | As in Terms |
| Benchmark | 2022 (fixed) |
| Calculation | `(latest − 2022) ÷ 2022 × 100`, from `trends.json` → `bySeason[].avg_per_game`, which is **already rounded to 1 decimal**. `scripts/update_data.py` `calculate_league_trends()` → `generate_insights()` (`season_trend`). |
| Rounding | Whole percent; rates 1 decimal. Matches the default, but rounding before dividing moves the result (11.1 and 14.7 give +32.4%; unrounded 11.10 and 14.67 give +32.2%). |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | Compares a full season including playoffs with a partial regular season. On the same basis (regular season, Weeks 1–7) the change is +21.6% (see C1). The title "Surge" and "jumped" are stronger than a description needs (C6). The card has red styling for an increase (`isPositive: change < 0`), which matches red = more penalties. |
| Where it appears | **Home, What The Data Shows:** "Penalty Surge Since 2022" card. JSON: `insights.json` → `season_trend`. A fallback in `app.js` (`generateInsightsFromTrends()`, used only if `insights.json` is empty) computes a different comparison (latest vs previous season). |
| Example | +32%, "from 11.1 to 14.7" |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

### M21. Home Field Bias (home vs road share of penalties)

| Field | Value |
|---|---|
| Label on site | Card title: "Home Field Bias"; value "+2.8%"; description "Away teams are penalized 2.8% more than home teams". |
| Kind | Derived: difference between two shares of a raw count |
| Numerator | Penalties on the road team minus penalties on the home team |
| Denominator | All penalties |
| Population | League, every game 2015 to now, **regular season and playoffs**. Home = nflverse play-by-play `home_team` (the designated home team at neutral sites). |
| Time window | Every season from 2015, including the current partial season |
| Inclusion rules | As in Terms |
| Benchmark | None (0 = equal) |
| Calculation | `(road − home) ÷ (road + home) × 100`. `scripts/update_data.py` `calculate_league_trends()` (`homeVsAway.bias_pct`) → `generate_insights()` (`home_bias`). |
| Rounding | 1 decimal |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | **The description misstates the number:** 2.8 is the gap between the road share (51.4%) and the home share (48.6%) in percentage points. Road teams were penalized 5.8% more than home teams (20,218 vs 19,117) (D2). "Bias" and the explanation's "crowd influence" claim a cause (C6). |
| Where it appears | **Home, What The Data Shows:** "Home Field Bias" card. JSON: `insights.json` → `home_bias`; `trends.json` → `homeVsAway`. |
| Example | +2.8% (20,218 road, 19,117 home) |
| Conflicts | [D2](audits/metric-conflicts-2026-10-28.md#d2-home-field-bias-card-misstates-its-number), [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

### M22. "Let Them Play" Effect (fourth quarter vs first quarter)

| Field | Value |
|---|---|
| Label on site | Card title: '"Let Them Play" Effect' (🏈 icon); value "+24%"; description "Q4 has 24% more penalties than Q1". |
| Kind | Derived: relative change between two raw counts |
| Numerator | Fourth-quarter penalties minus first-quarter penalties |
| Denominator | First-quarter penalties |
| Population | League, every game 2015 to now, regular season and playoffs; quarters 1–4 only (overtime left out) |
| Time window | Every season from 2015, including the current partial season |
| Inclusion rules | As in Terms |
| Benchmark | First quarter |
| Calculation | `(Q4 − Q1) ÷ Q1 × 100` on counts. `calculate_league_trends()` (`byQuarter`) → `generate_insights()` (`let_them_play`). |
| Rounding | Whole percent |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | Counts, not rates: quarters with more plays get more penalties. The second quarter has the most (11,462), which a Q1/Q4 comparison doesn't show. The title and explanation describe a cause ("refs are reluctant to 'decide' games") that the number doesn't test, and the value (+24%: more flags in Q4) runs against the title (C6). |
| Where it appears | **Home, What The Data Shows:** '"Let Them Play" Effect' card. JSON: `insights.json` → `let_them_play`; `trends.json` → `byQuarter`. |
| Example | +24% (Q1 8,211, Q4 10,199) |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

### M16. Most common penalty type and its share

| Field | Value |
|---|---|
| Label on site | **Insight card:** title "Most Common Call"; value "Holding"; description "7,671 total calls (26% of all penalties)". **Scoreboard:** "Most common call"; "Offensive Holding"; "348 calls · 22% of all flags". |
| Kind | Raw count, plus a share (derived) |
| Numerator | Penalties of the most common type |
| Denominator | **Insight card: the 10 most common types only.** Scoreboard: all penalties in the timeframe. |
| Population | **Insight card:** league, 2015 to now, regular season and playoffs. **Scoreboard:** league, regular season, the selected timeframe. |
| Time window | Insight card: every season from 2015. Scoreboard: the timeframe button (see M10). |
| Inclusion rules | As in Terms; type = nflverse `penalty_type` |
| Benchmark | None |
| Calculation | **Insight card:** `generate_insights()` (`top_penalty`): count ÷ sum of the top-10 counts in `trends.json` → `byType`; the value drops "Offensive " and "Defensive " from the name. **Scoreboard:** `scripts/scoreboard.py` `stats()` → `mostCommon` (`count ÷ flags`). |
| Rounding | Counts integer; share whole percent. Matches the default. |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | **The insight card's share is wrong for its label:** 7,671 is 25.8% of the top 10 types but 19.5% of all 39,335 penalties (D3). Dropping "Offensive" turns "Offensive Holding" into "Holding", which reads as offensive and defensive holding combined. |
| Where it appears | **Home, What The Data Shows:** "Most Common Call" card (`insights.json` → `top_penalty`). **Home, The Scoreboard:** "Most common call" (`scoreboard.json` → `frames[].mostCommon.type`, `.count`, `.pct`). |
| Example | Card: Holding, 7,671, "26%" (19.5% of all). Scoreboard, 2026 season: Offensive Holding, 348, 22%. |
| Conflicts | [D3](audits/metric-conflicts-2026-10-28.md#d3-most-common-call-card-uses-the-wrong-denominator), [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

### M23. Crew Chief Spread

| Field | Value |
|---|---|
| Label on site | Card title: "Crew Chief Spread"; value "11.0 - 16.5"; description "Vinovich (11.0/g) vs Moore (16.5/g)". |
| Kind | Derived: lowest and highest of an exposure rate across crew chiefs |
| Numerator / Denominator | As M3: each crew chief's career penalties per game |
| Population | As M3: every crew chief with a game, 2015 to now, regular season and playoffs, no minimum games |
| Time window | Career, including the current partial season |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | Min and max of `avg_per_game` (rounded to 1 decimal). `generate_insights()` (`crew_spread`). |
| Rounding | 1 decimal |
| Provenance | nflverse play-by-play and officials. Every data run. |
| Limitations | Same range as M3's description. No games counts (Vinovich 190 games, Moore 22). The explanation says "most lenient and strictest crews" (C6). |
| Where it appears | **Home, What The Data Shows:** "Crew Chief Spread" card (`insights.json` → `crew_spread`) |
| Example | 11.0 – 16.5 |
| Conflicts | [C3](audits/metric-conflicts-2026-10-28.md#c3-referee-variance-card-76), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

**Section subtitle:** "Swipe through headline discoveries from five seasons of
penalty data" (`frontend/index.html`). The cards cover 12 seasons (2015–2026);
see C6.

---

## Site: update notice

### M24. Data updated time

| Field | Value |
|---|---|
| Label on site | A button that appears when newer data is published while the page is open: "New results are in · updated 4:25 PM **Refresh**" (time in the visitor's local time zone) |
| Kind | Timestamp (not a metric) |
| Numerator / Denominator | None |
| Population | — |
| Time window | The time the last data run wrote `stats.json` |
| Inclusion rules | — |
| Benchmark | The value seen when the page loaded: the notice appears when it changes |
| Calculation | `scripts/update_data.py` `generate_hero_stats()` (`lastUpdated`, UTC); `frontend/js/livestrip.js` checks it every 5 minutes while the page is visible |
| Rounding | Hour and minute |
| Provenance | Pipeline run time. Every data run. |
| Limitations | It's the time the pipeline ran, not the time of the latest game in the data. No page shows "data through Week N, updated <time>" yet (V2.0a step 9). |
| Where it appears | Home page update notice (`stats.json` → `lastUpdated`). The rest of the live strip (live game flags from the gameday worker) is in session 6. |
| Example | `2026-10-28T23:25:59Z` |
| Conflicts | None |

**`stats.json` fields not displayed anywhere:** `totalPenalties` (39,335),
`totalGames` (3,135), `totalReferees` (28), `seasonsRange` ("2015-2026") and
`refereeVariance` ("9%", M3). They are public in the JSON file. Two of them
cover a different population from the home page: `totalPenalties` and
`totalGames` include playoffs, and `totalGames` counts only games with at least
one penalty.

---

## Crew chiefs

*To do in session 2.*

## Teams

*To do in session 3.*

## The Big Picture (trends)

*To do in session 4.*

## Previews, scorecard and history

*To do in session 5.*

## What Flags Cost and gameday (including the live strip)

*To do in session 6.*

---

## Where it appears (index)

| Place | Element | JSON field or CSV column | Entry |
|---|---|---|---|
| Home, top | Summary line ("This week in NFL officiating: …") | `scoreboard.json` → `frames[season].perGame`, `frames[lastSeason].perGame`; `season_comparison.json` → `crewChiefs[0]`; `teams/index.json` → highest `perGame` | M1, M9, M18, M19 |
| Home, This Season vs Last | Section title, subtitle, comparison toggle | `season_comparison.json` → `currentSeason`, `throughWeek`, `partialWeek`, `baselines[]`, `defaultBaseline` | M9 |
| Home, This Season vs Last | League tile "<season> so far" | `season_comparison.json` → `league.current.penalties`, `.yards`, `.games` | M4, M5, M6 |
| Home, This Season vs Last | League tile "Penalties per game" | `league.current.perGame`, `league.baselines.<key>.perGame` | M1, M2 |
| Home, This Season vs Last | League tile "Penalty yards per game" | `league.current.yardsPerGame`, `league.baselines.<key>.yardsPerGame` | M7, M2 |
| Home, This Season vs Last | League tile "Yards per penalty" | `league.current.yardsPerPenalty`, `league.baselines.<key>.yardsPerPenalty` | M8, M2 |
| Home, This Season vs Last | "Penalties Per Game By Crew Chief" chart | `crewChiefs[].current.perGame`, `crewChiefs[].baselines.<key>.perGame` | M1, M2 |
| Home, This Season vs Last | "Penalty Yards Per Game By Crew Chief" chart | `crewChiefs[].current.yardsPerGame`, `crewChiefs[].baselines.<key>.yardsPerGame` | M7, M2 |
| Home, This Season vs Last | Crew chief table: "Games", "Penalties / Yards", "Pen / Game", "Yds / Game", comparison column | `crewChiefs[].current.games`, `.penalties`, `.yards`, `.perGame`, `.yardsPerGame`; `crewChiefs[].baselines.<key>.*` | M6, M4, M5, M1, M7, M2 |
| Home, The Scoreboard | Title, description, timeframe buttons, week menu, footnote | `scoreboard.json` → `frames[].key`/`label`/`description`, `defaultFrame`, `weekFrames[]`, `defaultWeek`, `notes`, `throughWeek`, `partialWeek` | M10, M9 |
| Home, The Scoreboard | "Games", "Plays", "Flags", "Penalty yards" | `frames[].games`, `.plays`, `.penalties`, `.yards` | M6, M11, M4, M5 |
| Home, The Scoreboard | "Plays with a flag" (+ "a flag every N plays") | `frames[].pctPlays`, `.flagEveryPlays` | M12 |
| Home, The Scoreboard | "Flags per game" (+ "one every N min") | `frames[].perGame`, `.minutesPerFlag` | M1, M13 |
| Home, The Scoreboard | "Penalty yards per game" (+ "N yards per flag") | `frames[].yardsPerGame`, `.yardsPerPenalty` | M7, M8 |
| Home, The Scoreboard | "First downs by penalty" (+ "N per game handed over") | `frames[].firstDowns`, `.firstDownsPerGame` | M14 |
| Home, The Scoreboard | "Who gets flagged", "Before or after the snap", "Home or road" | `frames[].offenseShare`, `.preSnapShare`, `.homeShare` | M15 |
| Home, The Scoreboard | "Most common call" | `frames[].mostCommon` | M16 |
| Home, The Scoreboard | "Most flagged team", "Cleanest team" | `frames[].mostFlaggedTeam`, `.cleanestTeam` | M18 |
| Home, The Scoreboard | "Flag-heaviest crew" | `frames[].topCrew` | M19 |
| Home, The Scoreboard | "<season> running log" table | `weeklyLog[]` (`games`, `plays`, `penalties`, `yards`, `pctPlays`, `perGame`, `yardsPerGame`, `firstDowns`, `complete`, `scheduled`) | M6, M11, M4, M5, M12, M1, M7, M14, M9 |
| Home, What The Data Shows | Section subtitle ("… five seasons of penalty data") | `frontend/index.html` (fixed text) | C6 |
| Home, What The Data Shows | "Penalty Surge Since 2022" card | `insights.json` → `season_trend`; `trends.json` → `bySeason` | M20 |
| Home, What The Data Shows | "Home Field Bias" card | `insights.json` → `home_bias`; `trends.json` → `homeVsAway` | M21 |
| Home, What The Data Shows | "Referee Variance" card | `insights.json` → `ref_variance` | M3 |
| Home, What The Data Shows | '"Let Them Play" Effect' card | `insights.json` → `let_them_play`; `trends.json` → `byQuarter` | M22 |
| Home, What The Data Shows | "Most Common Call" card | `insights.json` → `top_penalty`; `trends.json` → `byType` | M16 |
| Home, What The Data Shows | "Crew Chief Spread" card | `insights.json` → `crew_spread` | M23 |
| Home (search-engine page source) | Pre-filled tiles, crew chief table, subtitle | `build_static.py` `home_prefill()` → `SEASON_SUB`, `SEASON_LEAGUE`, `SEASON_TABLE` (from `season_comparison.json`) | M1, M4–M9 |
| Site, update notice | "New results are in · updated <time>" | `stats.json` → `lastUpdated` | M24 |
| (not displayed) | — | `stats.json` → `totalPenalties`, `totalGames`, `totalReferees`, `seasonsRange`, `refereeVariance` | M24 note, M3 |
| (not displayed in this section) | — | `season_comparison.json` → `crewChiefs[].current.yardsPerPenalty`, `crewChiefs[].throughWeek`, `inactiveCrewChiefs[]`, `regularSeasonOnly`, `generatedAt`; `crewChiefs[].slug` (link to the crew pop-up, not a number) | M8; session 2 |
