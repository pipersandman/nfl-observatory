# Metric dictionary (v0)

Every number the site publishes: what it counts, over which games and weeks,
and how it is rounded. Built in V2.0a step 1 (#104); format from
`docs/V2_BUILD_PLAN.md` section 6. Where two places calculate the same idea
differently, the entry links to the conflict in
[`audits/metric-conflicts-2026-10-28.md`](audits/metric-conflicts-2026-10-28.md).

**Status:** sessions 1–8 of 10 done. Session 1: home page (summary line, This Season vs Last, The Scoreboard, What The Data Shows, update notice). Session 2: crew chiefs (cards, table, pop-up, Crew Chief Flag Rates chart, static `/crew/` pages, `crew_chiefs_<season>.csv`). Session 3: crew styles (pop-up style block and trajectory, Crew Chief Style Map, style fields on the static pages and CSV, game-preview style note) and `/assignments/`. Session 4: teams (Team Discipline cards, team pop-up, static `/team/` pages, `teams_<season>.csv`). Session 5: The Big Picture (season, quarter, week and type charts, "Which calls are rising?", static `/trends/`, the guide's trend questions, three trend CSVs). Session 6: game previews (cards, pop-up, `/assignments/` projections, the guide's "How projections work"). Session 7: scorecard and history (Track record, the scorecard pop-up and its week-by-week ledger, the guide's accuracy question). Session 8: What Flags Cost (league block, team tiles, static pages, guide), `wp_tables.json`, `/gameday/` and the live strip. Session 9: the cross-page pass and the full coverage check (with full paths for sessions 1–3); session 10: decisions. Areas still to do are marked below. Entries are numbered in the order they were written, so numbers jump between sections.

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
| Limitations | Counts flagged **plays**, not flags: two accepted penalties on one play count once. It's a game total for both teams, not one team's rate: team pages use a different per-game rate (one team's penalties, M46), under similar labels (C16). A crew chief's rate reflects the games and teams they drew, not how strictly they call games (plan section 8). |
| Where it appears | **Home, This Season vs Last:** league tile "Penalties per game" (value and "vs" comparison); "Penalties Per Game By Crew Chief" bar chart (current-season and comparison bars); "Crew Chiefs in <season>" table, "Pen / Game" column and the comparison column's "(x/g, n g)". JSON: `season_comparison.json` → `league.current.perGame`, `league.baselines.<key>.perGame`, `crewChiefs[].current.perGame`, `crewChiefs[].baselines.<key>.perGame`. **Home, The Scoreboard:** "Flags per game" cell, the week menu and the running log (`scoreboard.json` → `frames[].perGame`, `weekFrames[].perGame`, `weeklyLog[].perGame`). **Summary line** (`index.html` `SEO:SUMMARY`, from `scoreboard.json` `season` and `lastSeason` frames). **Pre-filled page source** for search engines (`build_static.py` `home_prefill()`: `SEASON_LEAGUE` tiles and `SEASON_TABLE`, from `season_comparison.json`). **Crew chiefs (session 2):** Meet The Officials card rows ("Pen/g") and the crew pop-up's "2026 vs history" block (`crewChiefs[]`/`inactiveCrewChiefs[]` → `current`, `baselines.lastSeason`, `baselines.all`); "Crew Chief Flag Rates" chart in League Trends (current or `all`, with the league marker, M35); static `/crew/` table, top-3 summary and former crew chiefs table; static `/crew/<slug>/` tiles, summary and FAQ; `crew_chiefs_<season>.csv` (`flags_per_game_<season>`, `career_flags_per_game_2015_25`); pre-filled `REFEREES`. Team pages: a different rate (one team's penalties), M46. Trends: M64; previews compare with the model's level instead (M73). Scorecard: M81–M88; What Flags Cost and gameday: M89–M99. |
| Example | League 2026 through Week 7: **14.67** per game (1,570 penalties in 107 games), shown as 14.7. 2025 Weeks 1–7: 14.21 (1,535 in 108). Recomputed from play-by-play: 1,570 plays with `penalty == 1` in 107 games, a match. |
| Conflicts | [C4: partial-week games](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison); [C5: "penalties" counts plays](audits/metric-conflicts-2026-10-28.md#c5-penalties-counts-plays-with-an-accepted-penalty); [C7: summary line compares with all of last season](audits/metric-conflicts-2026-10-28.md#c7-the-home-summary-line-compares-with-all-of-last-season); [C8: "All seasons" vs "Since 2015"](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names); [C16: team and game "flags per game"](audits/metric-conflicts-2026-10-28.md#c16-flags-per-game-a-game-total-and-one-teams-total-under-one-label); [D4: scoreboard crew assignments](audits/metric-conflicts-2026-10-28.md#d4-scoreboard-crew-leader-uses-incomplete-crew-assignments) (fixed in #107) |

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
| Where it appears | **Home, This Season vs Last:** league tiles (penalties per game, penalty yards per game, yards per penalty); bar-end labels on both crew chief charts; "Pen / Game" and "Yds / Game" columns of the crew chief table. **Crew chiefs (session 2):** Meet The Officials cards ("vs 2025", "vs 2015–25") and the crew pop-up ("Pen/g vs 2025", "Yds/g vs 2025", "vs 2015–25"; the per-type and per-quarter bars, M33 and M34). **Teams (session 4):** team cards (vs league average and vs the selected comparison, M47, M48); team pop-up ("Pen/g", "Yds/g", "Drawn/g" badges; per-type and per-quarter bars, M55–M57; "Which calls are rising", M58; crew chief rows, M60). |
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
| Where it appears | **This Season vs Last:** first league tile (`league.current.games`); crew chief table "Games" and comparison column (`crewChiefs[].current.games`, `…baselines.<key>.games`). **Scoreboard:** "Games", running log, week menu (`frames[].games`, `weekFrames[].games`, `weekFrames[].scheduled`, `weeklyLog[].games`). **Crew chiefs (session 2):** card and pop-up rows ("<n> g"), pop-up subtitle ("<n> games this season"), static `/crew/` ("2026 games", former crew chiefs "Games"), static `/crew/<slug>/` tiles, `crew_chiefs_<season>.csv` (`games_<season>`, `career_games_2015_25`). Career games (playoffs included) are a different count: M25. |
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
| Where it appears | **This Season vs Last:** league tile (`league.current.yardsPerGame`, `league.baselines.<key>.yardsPerGame`); "Penalty Yards Per Game By Crew Chief" chart and the "Yds / Game" column (`crewChiefs[].current.yardsPerGame`, `…baselines.<key>.yardsPerGame`). **Scoreboard:** "Penalty yards per game" and the running log (`frames[].yardsPerGame`, `weeklyLog[].yardsPerGame`). Pre-filled page source. **Crew chiefs (session 2):** card and pop-up rows ("Yds/g", whole yards on cards), static `/crew/<slug>/` "2026 yards / game" tile, `crew_chiefs_<season>.csv` (`yards_per_game_<season>`). |
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
| Where it appears | **This Season vs Last:** league tile (`league.current.yardsPerPenalty`, `league.baselines.<key>.yardsPerPenalty`). **Scoreboard:** under "Penalty yards per game" (`frames[].yardsPerPenalty`). Pre-filled page source. Per crew chief (`crewChiefs[].current.yardsPerPenalty`, `…baselines.<key>.yardsPerPenalty`): the crew pop-up's "Yds/pen" column (session 2). |
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
| Limitations | "Handed over" says the penalty gave the first down; nflverse's field marks a first down awarded by penalty, and whether the offense would have gained one on the play anyway isn't recorded. Checked in session 8: equal to What Flags Cost's first downs given (M92: 432 in 2026, 973 in 2025), so every first-down penalty counted here is a defensive flag. |
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
| Calculation | **Scoreboard:** `stats()`: team games from the schedule's `home_team`/`away_team` (mapped to today's abbreviations as the schedule is loaded, `scripts/teams.py`), flags from play-by-play `penalty_team` (`mostFlaggedTeam`, `cleanestTeam`). **Summary line:** `teams/index.json` → highest `perGame` (`team_pages.py`, M46). |
| Rounding | 1 decimal |
| Provenance | nflverse schedules and play-by-play. Every data run. |
| Limitations | A team's own penalties, under the same "flags per game" label as M1's game total (both teams), at about half the value (C16). No games count is shown. "Cleanest" reads as a judgment (C6). In a week frame each team has one game. **Fixed in #105 (D1):** relocated teams' seasons before the move were split off ("Since 2015": LV 12.0, STL 0.0). |
| Where it appears | Scoreboard leaders (`scoreboard.json` → `frames[].mostFlaggedTeam`, `frames[].cleanestTeam`). Summary line (`index.html` `SEO:SUMMARY`). Team pages: M46 (same rate, computed again in `team_pages.py`; GB 9.29 there, 9.3 here). |
| Example | At `5091e57`: 2026 season GB 9.3 (most), IND 5.1 (fewest). "Since 2015": LV 6.9, CIN 5.7. |
| Conflicts | [D1](audits/metric-conflicts-2026-10-28.md#d1-relocated-teams-two-team-abbreviations-joined) (fixed in #105), [C5](audits/metric-conflicts-2026-10-28.md#c5-penalties-counts-plays-with-an-accepted-penalty), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page), [C16](audits/metric-conflicts-2026-10-28.md#c16-flags-per-game-a-game-total-and-one-teams-total-under-one-label) |

### M19. Crew chief with the most penalties per game (leaders)

| Field | Value |
|---|---|
| Label on site | Scoreboard: "Flag-heaviest crew" ("Scott Novak", "**20.1** flags per game · 7 games"). Summary line: "Most flags per game: <name>'s crew (20.1)". |
| Kind | Exposure rate (the highest crew chief value of M1) |
| Numerator / Denominator | As M1, for one crew chief |
| Population | **Scoreboard:** crew chiefs with at least 3 games in the timeframe (1 in a frame of 16 games or fewer). **Summary line:** every crew chief with a game this season, from `season_comparison.json`, no minimum. Both take the crew chief from the merged assignment (`data['officials']`: officials feed, then the schedule's `referee` column, then Football Zebras). |
| Time window | Scoreboard: the timeframe, and each week in the week picker. Summary line: the current season so far. |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | Scoreboard: `scripts/scoreboard.py` `stats()` (`topCrew`: `name`, `perGame`, `games`), for `frames[]` and `weekFrames[]`. Summary line: `build_static.py` `home_summary()` (first of `crews_now`, sorted by `current.perGame`). |
| Rounding | 1 decimal |
| Provenance | nflverse play-by-play, schedules and officials; Football Zebras assignments. Every data run. |
| Limitations | **Small samples (for the small-sample label, V2.0a step 3, decision D13):** the "Since 2015" leader, Alex Moore (16.5 per game), has **22 games**, the fewest of the 28 crew chiefs in that frame. The other 27 have 43 to 178 regular-season games since 2015 (median 115); 7 have 150 or more (counts from `referee/<slug>.json` → `regularSeasonStats[].games`). The 3-game minimum lets a short career outrank long ones. In a week frame each crew chief has one game. The summary line shows no games count. **Fixed in #107 (D4):** the scoreboard used the schedule's `referee` column only, empty for 42 of 107 games in 2026 (Scott Novak was rated on 4 of his 7 games, 22.0). |
| Where it appears | Scoreboard (`scoreboard.json` → `frames[].topCrew`, `weekFrames[].topCrew`); summary line |
| Example | At `5091e57`: 2026 season, Scott Novak **20.1** over 7 games (scoreboard and summary line agree; `season_comparison.json` 20.14). Week 7: Craig Wrolstad 20.0, 1 game. "Since 2015": Alex Moore 16.5, 22 games. |
| Conflicts | [D4](audits/metric-conflicts-2026-10-28.md#d4-scoreboard-crew-leader-uses-incomplete-crew-assignments) (fixed in #107), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

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
| Where it appears | **Home, What The Data Shows:** "Penalty Surge Since 2022" card. JSON: `insights.json` → `season_trend`, built from `trends.json` → `bySeason[].season`, `bySeason[].avg_per_game` (`bySeason[].penalties`, `bySeason[].games` not displayed; the page reads this file only in the fallback, [Published but not displayed](audits/metric-conflicts-2026-10-28.md#published-but-not-displayed)). The regular-season version is M64. A fallback in `app.js` (`generateInsightsFromTrends()`, used only if `insights.json` is empty) computes a different comparison (latest vs previous season). |
| Example | +32%, "from 11.1 to 14.7" |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

### M21. Home Field Bias (home vs road share of penalties)

| Field | Value |
|---|---|
| Label on site | Card title: "Home Field Bias"; value "+5.8%"; description "Away teams are penalized 5.8% more than home teams". |
| Kind | Derived: relative difference between two raw counts (road vs home) |
| Numerator | Penalties on the road team minus penalties on the home team |
| Denominator | Penalties on the home team (the card's value and description). `bias_pct`, kept in `trends.json` and used for the card's styling, divides by all penalties instead. |
| Population | League, every game 2015 to now, **regular season and playoffs**. Home = nflverse play-by-play `home_team` (the designated home team at neutral sites). |
| Time window | Every season from 2015, including the current partial season |
| Inclusion rules | As in Terms |
| Benchmark | None (0 = equal) |
| Calculation | **Card value and description:** `(road ÷ home − 1) × 100` = `trends.json` → `homeVsAway.awayMorePct`. **Card styling** (`isPositive`, "positive" when below 3): `bias_pct` = `(road − home) ÷ (road + home) × 100`, the gap between the road and home shares in percentage points. `scripts/update_data.py` `calculate_league_trends()` → `generate_insights()` (`home_bias`). The fallback in `app.js` (`generateInsightsFromTrends()`) uses the same two fields. |
| Rounding | 1 decimal (both fields) |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | The styling threshold (3) is on `bias_pct`, a different measure from the value shown: +5.8% is styled "positive" because `bias_pct` is 2.8 (left for C6 / #76). "Bias" and the explanation's "crowd influence" claim a cause (C6). No counts are shown. **Fixed in #107 (D2):** the card showed `bias_pct` (+2.8) as "% more". |
| Where it appears | **Home, What The Data Shows:** "Home Field Bias" card. JSON: `insights.json` → `home_bias`, built from `trends.json` → `homeVsAway.home`, `homeVsAway.away`, `homeVsAway.awayMorePct`, `homeVsAway.bias_pct` (read by the page only in the fallback, [Published but not displayed](audits/metric-conflicts-2026-10-28.md#published-but-not-displayed)). |
| Example | At `5091e57`: **+5.8%** (20,218 road, 19,117 home: 20,218 ÷ 19,117 − 1 = 5.76%). `bias_pct` 2.8 (road share 51.4%, home 48.6%). |
| Conflicts | [D2](audits/metric-conflicts-2026-10-28.md#d2-home-field-bias-card-misstates-its-number) (fixed in #107), [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

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
| Where it appears | **Home, What The Data Shows:** '"Let Them Play" Effect' card. JSON: `insights.json` → `let_them_play`, built from `trends.json` → `byQuarter[].quarter`, `byQuarter[].count` (the page doesn't read the file's copy; the pipeline uses the same values before writing it, [Published but not displayed](audits/metric-conflicts-2026-10-28.md#published-but-not-displayed)). The chart's per-game quarter rates are M67. |
| Example | +24% (Q1 8,211, Q4 10,199) |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C6](audits/metric-conflicts-2026-10-28.md#c6-wording-and-framing-section-17-on-the-home-page) |

### M16. Most common penalty type and its share

| Field | Value |
|---|---|
| Label on site | **Insight card:** title "Most Common Call"; value "Holding"; description "7,671 total calls (20% of all penalties)". **Scoreboard:** "Most common call"; "Offensive Holding"; "348 calls · 22% of all flags". |
| Kind | Raw count, plus a share (derived) |
| Numerator | Penalties of the most common type |
| Denominator | All penalties: **insight card**, every penalty in its population (since #107; it used the 10 most common types only); **scoreboard**, all penalties in the timeframe. |
| Population | **Insight card:** league, 2015 to now, regular season and playoffs. **Scoreboard:** league, regular season, the selected timeframe. |
| Time window | Insight card: every season from 2015. Scoreboard: the timeframe button (see M10). |
| Inclusion rules | As in Terms; type = nflverse `penalty_type` |
| Benchmark | None |
| Calculation | **Insight card:** `generate_insights()` (`top_penalty`): count of the top type in `trends.json` → `byType` ÷ all penalties (`len(data['penalties'])`); the value drops "Offensive " and "Defensive " from the name. The fallback in `app.js` (`generateInsightsFromTrends()`, used only if `insights.json` is empty) divides by `trends.json` → `homeVsAway.home + .away`, the same total (39,335). **Scoreboard:** `scripts/scoreboard.py` `stats()` → `mostCommon` (`count ÷ flags`). |
| Rounding | Counts integer; share whole percent. Matches the default. |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | Dropping "Offensive" turns "Offensive Holding" into "Holding", which reads as offensive and defensive holding combined. **Fixed in #107 (D3):** the card's share was of the 10 most common types (26%), not of all penalties. |
| Where it appears | **Home, What The Data Shows:** "Most Common Call" card (`insights.json` → `top_penalty`, built from `trends.json` → `byType[].type`, `byType[].count`; read by the page only in the fallback, [Published but not displayed](audits/metric-conflicts-2026-10-28.md#published-but-not-displayed)). Share chart: M68. **Home, The Scoreboard:** "Most common call" (`scoreboard.json` → `frames[].mostCommon.type`, `.count`, `.pct`). |
| Example | At `5091e57`: card, Holding, 7,671 of 39,335 = 19.5%, shown as "20%". Scoreboard, 2026 season: Offensive Holding, 348, 22%. |
| Conflicts | [D3](audits/metric-conflicts-2026-10-28.md#d3-most-common-call-card-uses-the-wrong-denominator) (fixed in #107), [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

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
| Limitations | It's the time the pipeline ran, not the time of the latest game in the data. No page shows "data through Week N, updated <time>" yet (V2.0a step 9). **Session 8:** the "How is this data collected?" explainer (`frontend/js/app.js` `EXPLAINERS['data-methodology']`) says "Data is updated weekly during the NFL season, typically on Tuesdays after Monday Night Football"; the data workflow runs about hourly on game nights and Sundays, on Tuesday and Wednesday, and on every merge to `main` ([D11](audits/metric-conflicts-2026-10-28.md#d11-how-is-this-data-collected-says-updated-weekly--on-tuesdays), text only). |
| Where it appears | Home page update notice (`stats.json` → `lastUpdated`). The rest of the live strip (live game flags from the gameday worker): M98, M99. |
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

Session 2. **Examples are from `5091e57`** (2026-10-29: 2026 regular season
through Week 7). Places covered: "Meet The Officials" cards (section 05),
"Complete Crew Chief Stats" table (section 06), the crew pop-up, the "Crew
Chief Flag Rates" chart (section 04), the static `/crew/` and
`/crew/<slug>/` pages, and `crew_chiefs_<season>.csv`.

**Two data sources, two populations.** The cards, pop-up, static pages and
CSV mix:
- **Season figures** from `season_comparison.json` (M1, M2, M4–M8):
  regular season only, current season and the comparison periods.
- **Career figures** from `referees.json` and `referee/<slug>.json`
  (`scripts/update_data.py` `calculate_referee_stats()`,
  `generate_referee_profiles()`): **every game, playoffs included**, 2015 to
  now, current season included. See [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season)
  and [C11](audits/metric-conflicts-2026-10-28.md#c11-career-means-three-different-windows).

Spot checks (recomputed from play-by-play and the merged crew chief
assignment): Bill Vinovich (190 games) and Alex Moore (22 games), every
field below, match. The assignment has one crew chief for each of the 3,135
games, no repeated rows, and no game without a penalty (so the career join
that drops penalty-free games drops none).

**Crew styles** (the pop-up's style block and trajectory, the Crew Chief
Style Map, every `crew_styles.json` field on the static pages and the CSV's
`career_style`) and the `/assignments/` page: see "Crew styles (session 3)"
below, M37–M45.

### M25. Crew chief career games

| Field | Value |
|---|---|
| Label on site | Card: "2015–2026 • **190** games" under the name. Table "Complete Crew Chief Stats": column "Games" (with a `?` explainer, "Games Worked"). Pop-up subtitle: "Active 2026 • 6 games this season • **190** career games". |
| Kind | Raw count (sample) |
| Numerator | Games the crew chief worked |
| Denominator | None |
| Population | One crew chief; **regular season and playoffs**; crew chief from the merged assignment (officials feed, then the schedule's `referee`, then Football Zebras) |
| Time window | 2015 to now, including the current season |
| Inclusion rules | Only games with at least one penalty (inner join with per-game penalty totals); none are left out at `5091e57` |
| Benchmark | None |
| Calculation | Count of games per crew chief. `calculate_referee_stats()` (`games`) → `referees.json` → `games`; `referee/<slug>.json` → `stats.games`. |
| Rounding | Integer |
| Provenance | nflverse officials, schedules and play-by-play; Football Zebras. Every data run. |
| Limitations | **Includes playoffs**, while the card's rate rows beside it, the season table and the static pages count regular-season games only. The "Games Worked" explainer says so: "Total number of games this crew chief has led in the data (2015 onward), including playoff games." **Fixed in #110 (D6):** it said "regular-season games"; the table subtitle said "All active head referees" (it lists all 28; now "Every crew chief since 2015, most games first"). |
| Where it appears | Home, Meet The Officials: card header. Home, Complete Crew Chief Stats: "Games" column. Crew pop-up: subtitle. JSON: `referees.json` → `games`; `referee/<slug>.json` → `stats.games`. |
| Example | Bill Vinovich **190** (177 regular season + 13 playoff). Alex Moore 22 (all regular season). |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C11](audits/metric-conflicts-2026-10-28.md#c11-career-means-three-different-windows), [D6](audits/metric-conflicts-2026-10-28.md#d6-crew-chief-table-labels-dont-match-what-it-shows) (fixed in #110) |

### M26. Crew chief career penalties per game

| Field | Value |
|---|---|
| Label on site | Table: "Avg/Game" (explainer "Average Penalties Per Game"); table title "Crew Chief Statistics (All Seasons)". Pop-up: "Career (all games incl. playoffs, 2015–2026)" → "Avg/Game". Card of a crew chief with no season numbers: "Avg/Game". |
| Kind | Exposure rate |
| Numerator | Penalties (as counted), both teams, in the crew chief's games |
| Denominator | Career games (M25) |
| Population | As M25 (playoffs included) |
| Time window | As M25 |
| Inclusion rules | As in Terms |
| Benchmark | None on the table. The explainer points to where the league average for the same seasons is shown (the Crew Chief Flag Rates chart and each crew chief's profile, M35), with no number of its own. |
| Calculation | Mean of per-game totals, **rounded to 1 decimal** in `calculate_referee_stats()` (`avg_per_game`). Also the input to M3 (Referee Variance), M23 (Crew Chief Spread) and the career tendency (M35). |
| Rounding | 1 decimal. Matches the default. |
| Provenance | As M25 |
| Limitations | A different rate from the crew chief's "2015–25" row on the card (M1, `all` baseline: regular season, seasons before this one): Vinovich 11.0 here vs 11.02 there, Moore 16.5 vs 16.12. The explainer calls crews "flag-heavy" or "let them play" (C13). **Fixed in #110 (D7):** the explainer said "League average is typically around 11-12 penalties per game" (12.59 for 2015–25; 14.67 in 2026); it no longer states a number. A crew chief's rate reflects the games and teams they drew (plan section 8). |
| Where it appears | Home, Complete Crew Chief Stats: "Avg/Game". Crew pop-up: "Career" block. Card fallback (no season data). JSON: `referees.json` → `avg_per_game`; `referee/<slug>.json` → `stats.avgPerGame`. |
| Example | Vinovich 11.0 (2,091 penalties in 190 games). Moore 16.5 (364 in 22). |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C11](audits/metric-conflicts-2026-10-28.md#c11-career-means-three-different-windows), [D7](audits/metric-conflicts-2026-10-28.md#d7-fixed-league-average-text-out-of-date) (fixed in #110) |

### M27. Crew chief game range (fewest and most penalties in a game)

| Field | Value |
|---|---|
| Label on site | Table: "Range", value "2-26". Pop-up "Career" block: "Range". |
| Kind | Raw counts (minimum and maximum of a per-game count) |
| Numerator | Fewest and most penalties in one of the crew chief's games |
| Denominator | None |
| Population / Time window | As M25 (playoffs included, 2015 to now) |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | `min` and `max` of per-game totals. `calculate_referee_stats()` (`min_penalties`, `max_penalties`) → `stats.minGame`, `stats.maxGame`. |
| Rounding | Integers |
| Provenance | As M25 |
| Limitations | Extremes depend on how many games a crew chief has worked: a long career has more chances at a 26-flag game. No date or game is linked to either value. |
| Where it appears | Home, Complete Crew Chief Stats: "Range". Crew pop-up: "Career" → "Range". JSON: `referees.json` → `min_penalties`, `max_penalties`; `referee/<slug>.json` → `stats.minGame`, `stats.maxGame`. |
| Example | Vinovich 2–26 (190 games). Moore 8–24 (22 games). |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

### M28. Home Bias (crew chief)

| Field | Value |
|---|---|
| Label on site | Card footer: "Home bias **+2.5 pts**". Table column: "Home Bias" (explainer "What is Home Bias?"), red above 5, green below 0; legend "Home Bias above 5 pts" / "Home Bias below 0". Pop-up "Career" block: "Home Bias". Explainer: "the road teams' share of the crew's penalties minus the home teams' share, in percentage points (pts). For example, +4 pts means 52% of the flags went against road teams and 48% against home teams." |
| Kind | Derived: difference between two shares of a raw count |
| Numerator | Penalties on the road team minus penalties on the home team, in the crew chief's games |
| Denominator | All penalties in those games |
| Population / Time window | As M25 (playoffs included, 2015 to now) |
| Inclusion rules | As in Terms; home = play-by-play `home_team` |
| Benchmark | None shown. The league's own value for the same population is 2.8 (`trends.json` → `homeVsAway.bias_pct`, M21). |
| Calculation | `(road − home) ÷ (road + home) × 100`: the road share minus the home share, in **percentage points**. `calculate_referee_stats()` (`home_bias_pct`) → `stats.homeBiasPct`. Per season: `seasonStats[].homeBias` (not displayed). |
| Rounding | 1 decimal, shown with "pts" (was "%" before #110) |
| Provenance | As M25 |
| Limitations | A gap in points, not "how much more": Moore's +8.2 pts means road teams drew **18.0% more** flags in his games (197 vs 167); Vinovich +2.5 pts, 5.2% more. The colors use fixed cut-offs (above 5 pts, below 0), not the league value. Red marks road teams penalized more, not more penalties (C13). "Bias", and the explainer's "likely reflects crowd influence" and "Research shows home bias is strongest in Q1", claim causes the data doesn't test (C13). A different measure from the league card (M21, relative difference since #107) and from the style profile's home share (M40) ([C12](audits/metric-conflicts-2026-10-28.md#c12-three-measures-of-home-vs-road-for-one-idea)). No counts shown. **Fixed in #110 (D5):** the explainer said the number "measures how much more (or less) the away team gets penalized … shown as a percentage", the values showed "%", and the legend read "Above average" / "Below average". |
| Where it appears | Home, Meet The Officials: card footer. Home, Complete Crew Chief Stats: "Home Bias". Crew pop-up: "Career" → "Home Bias". Pre-filled page source (`build_static.py` `home_prefill()`, `DATA_TABLE`). JSON: `referees.json` → `home_bias_pct`; `referee/<slug>.json` → `stats.homeBiasPct`. |
| Example | Vinovich +2.5 pts (road 1,072, home 1,019). Moore +8.2 pts (road 197, home 167). |
| Conflicts | [D5](audits/metric-conflicts-2026-10-28.md#d5-crew-chief-home-bias-explained-as-how-much-more) (fixed in #110), [C12](audits/metric-conflicts-2026-10-28.md#c12-three-measures-of-home-vs-road-for-one-idea), [C13](audits/metric-conflicts-2026-10-28.md#c13-wording-and-framing-section-17-on-crew-chief-pages), [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

### M29. Consistency (crew chief style label)

| Field | Value |
|---|---|
| Label on site | Table: "Consistency" (explainer "What does Consistency mean?"). Pop-up "Career" block: "**Style**". Values: "Very Consistent", "Consistent", "Variable", "Highly Variable". |
| Kind | Derived: a label from the standard deviation of per-game penalties |
| Numerator / Denominator | Standard deviation of the crew chief's per-game totals (sample, `ddof=1`) |
| Population / Time window | As M25 (playoffs included, 2015 to now) |
| Inclusion rules | As in Terms |
| Benchmark | Fixed cut-offs: below 2 "Very Consistent", 2–3 "Consistent", 3–4 "Variable", 4 and above "Highly Variable" |
| Calculation | `calculate_referee_stats()` `get_consistency()` on `std_dev` → `consistency`, `stats.consistency`. The standard deviation itself (`std_dev`, `stats.stdDev`) isn't displayed. |
| Rounding | Label only; `std_dev` stored to 2 decimals |
| Provenance | As M25 |
| Limitations | The spread mixes seasons with different league levels (13.8 per game in 2015, 11.2 in 2022, 14.7 in 2026), so a long career looks less consistent partly because the league moved. Fewer games give a noisier value. The same label is called "Style" in the pop-up. The explainer ties it to "game planning and betting analysis" and calls the top band a "Wildcard crew" (C13). |
| Where it appears | Home, Complete Crew Chief Stats: "Consistency". Crew pop-up: "Career" → "Style". JSON: `referees.json` → `consistency` (`std_dev` not displayed); `referee/<slug>.json` → `stats.consistency` (`stats.stdDev` not displayed). |
| Example | Vinovich: std dev 3.86 → "Variable". Moore: 4.39 → "Highly Variable" (22 games). |
| Conflicts | [C13](audits/metric-conflicts-2026-10-28.md#c13-wording-and-framing-section-17-on-crew-chief-pages), [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

### M30. Seasons in the data

| Field | Value |
|---|---|
| Label on site | Card: "**2015–2026** • 190 games". Pop-up (inactive crew chief): "<n> seasons". Static `/crew/` former crew chiefs table: "Seasons in the data". Pop-up "Career" heading: "(…, 2015–2026)". |
| Kind | Not a metric: the first and last season with a game in the data |
| Numerator / Denominator | None |
| Population | As M25 |
| Time window | 2015 to now |
| Inclusion rules | — |
| Benchmark | None |
| Calculation | `min` and `max` of `season` in `calculate_referee_stats()` (`first_season`, `last_season`); `experience` = last − first + 1 seasons. |
| Rounding | — |
| Provenance | As M25 |
| Limitations | Starts at 2015 for anyone whose career began earlier. `experience` counts calendar seasons between the first and last, not seasons worked. |
| Where it appears | Card header; pop-up subtitle and "Career" heading; static `/crew/` former crew chiefs table. JSON: `referees.json` → `first_season`, `last_season`; `referee/<slug>.json` → `firstSeason`, `lastSeason`, `experience`. |
| Example | Vinovich 2015–2026. Moore 2025–2026. |
| Conflicts | None |

### M31. Crew chief penalties per game, by season

| Field | Value |
|---|---|
| Label on site | Pop-up chart: "Penalties per game by season (**regular season**)", with a dashed "Prior-years avg" line. Static `/crew/<slug>/`: table "Season by season" ("Season", "Games", "Flags / game"). |
| Kind | Exposure rate, one per season |
| Numerator / Denominator | As M1, for one crew chief and one season |
| Population | **Pop-up chart: regular season only** (`regularSeasonStats`). **Static page table: every game, playoffs included** (`seasonStats`). |
| Time window | Each season from 2015 the crew chief worked, including the current one. The dashed line is the crew chief's `all` baseline (2015–25, regular season, M1). |
| Inclusion rules | As in Terms |
| Benchmark | Pop-up: the crew chief's own prior-years rate. Static table: none. |
| Calculation | `generate_referee_profiles()`: `regularSeasonStats[]` (`games`, `penalties`, `yards`, `perGame` 2 decimals, `yardsPerGame`) and `seasonStats[]` (`games`, `penalties`, `avg` 1 decimal). The pop-up falls back to `seasonStats` only when `regularSeasonStats` is empty. |
| Rounding | Pop-up: stored 2 decimals; the chart shows bars, tooltip values. Static table: 1 decimal. |
| Provenance | As M25 |
| Limitations | **Same idea, two populations:** the static table and the pop-up chart differ in every season with playoff games, under labels that don't say so on the static page (Vinovich 2015: 12.1 in 16 games on the static page, 12.0 in 15 in the pop-up). A season with few games (a partial current season) swings. No games count on the chart. |
| Where it appears | Crew pop-up: season chart (`referee/<slug>.json` → `regularSeasonStats[].perGame`, `season`). Static `/crew/<slug>/`: "Season by season" (`seasonStats[].season`, `.games`, `.avg`). `regularSeasonStats[].penalties`, `.yards`, `.yardsPerGame` and `seasonStats[].penalties` aren't displayed. |
| Example | Vinovich 2025: 13.53 (17 games, regular season); 2026: 13.67 (6 games). |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

### M32. Crew chief penalty types: share of the crew's penalties

| Field | Value |
|---|---|
| Label on site | Card footer: "Most common: **False Start**" (Vinovich). Pop-up of a crew chief with no current-season games: "Penalty Type Breakdown" (type, "20.9%"). |
| Kind | Raw count, plus a share (derived) |
| Numerator | Penalties of one type in the crew chief's games |
| Denominator | All penalties in the crew chief's games |
| Population / Time window | As M25 (playoffs included, 2015 to now) |
| Inclusion rules | As in Terms; type = nflverse `penalty_type` |
| Benchmark | None |
| Calculation | `generate_referee_profiles()` `penaltyTypes[]`: the 10 most common types, `count` and `pct` = count ÷ all the crew's penalties. The card drops "Offensive ", "Defensive " and " (Offense)" from the name. |
| Rounding | Share 1 decimal ("20.9%"); the plan default for a share above 10% is a whole number |
| Provenance | As M25 |
| Limitations | Shares, not rates: a crew chief with more flags overall can have a lower share of a type and still call it more often per game. Dropping "Offensive" turns "Offensive Holding" into "Holding" (as M16). |
| Where it appears | Home, Meet The Officials: card footer ("Most common"). Crew pop-up (inactive crew chiefs): "Penalty Type Breakdown" (top 8). JSON: `referee/<slug>.json` → `penaltyTypes[].type`, `.count`, `.pct`. |
| Example | Vinovich: False Start, 20.9% of his penalties. Moore: Offensive Holding, 22.5%. |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

### M33. Crew chief penalty types per game: this season vs prior seasons

| Field | Value |
|---|---|
| Label on site | Pop-up (active crew chief): "What's being called: 2026 vs 2015–25", paired bars with "2026" and "2015–25 avg" values and a change badge; footnote "Penalties per game of each type in this crew's regular-season games. Sorted by 2026 rate, most first." |
| Kind | Exposure rate per type, plus a change badge (M2) |
| Numerator | Penalties of the type in the crew chief's games |
| Denominator | The crew chief's games in the period (`currentSeasonGames`, `priorSeasonGames`, neither displayed) |
| Population | One crew chief, **regular season** |
| Time window | Current season so far vs every earlier regular season the crew chief worked (2015 on) |
| Inclusion rules | As in Terms |
| Benchmark | The crew chief's own prior seasons |
| Calculation | `generate_referee_profiles()` `penaltyTypeComparison[]`: types in this season's top 8 plus the prior top 6; `count ÷ games`, 2 decimals; sorted by current rate. Badge: `pctBadge()` (M2), dimmed under 4 games. |
| Rounding | Shown to 1 decimal |
| Provenance | As M25 |
| Limitations | Current-season rates rest on a few games (6 for most crew chiefs at Week 7); the badge is dimmed only below 4 games. Games counts aren't shown. The legend calls the prior period "2015–25 avg", but it's this crew chief's prior seasons only (Moore: 2025 alone). |
| Where it appears | Crew pop-up, active crew chiefs. JSON: `referee/<slug>.json` → `penaltyTypeComparison[].type`, `.currentPerGame`, `.priorPerGame` (`.currentCount`, `.priorCount` not displayed). |
| Example | At `5091e57`, see each profile; Vinovich 2026 is 6 games against 171 prior. |
| Conflicts | [C11](audits/metric-conflicts-2026-10-28.md#c11-career-means-three-different-windows) |

### M34. Crew chief penalties by quarter

| Field | Value |
|---|---|
| Label on site | **Active crew chief:** "⏱️ When flags fly: 2026 vs 2015–25" (paired bars per quarter, per game, change badge). **Inactive:** "⏱️ Penalties By Quarter" (share of the crew's penalties, "%"). |
| Kind | Active: exposure rate per quarter. Inactive: share (derived). |
| Numerator | Penalties in quarters 1–4 |
| Denominator | Active: the crew chief's games in the period. Inactive: the crew's penalties in quarters 1–4. |
| Population | Active: regular season. **Inactive: every game, playoffs included.** Overtime left out of both. |
| Time window | Active: current season vs prior seasons (as M33). Inactive: 2015 to now. |
| Inclusion rules | As in Terms |
| Benchmark | Active: the crew chief's prior seasons. Inactive: none. |
| Calculation | `generate_referee_profiles()`: `quarterComparison[]` (`currentPerGame`, `priorPerGame`, 2 decimals) and `quarterDistribution[]` (`count`, `pct` 1 decimal). |
| Rounding | Rates 1 decimal; shares 1 decimal |
| Provenance | As M25 |
| Limitations | Overtime flags count in the crew chief's totals (M26) but not here, so the quarters don't add up to the per-game rate. Quarters differ in plays (the second quarter has the two-minute drill), so a busier quarter isn't a calling pattern by itself. |
| Where it appears | Crew pop-up. JSON: `referee/<slug>.json` → `quarterComparison[].quarter`, `.currentPerGame`, `.priorPerGame`; `quarterDistribution[].quarter`, `.pct` (`.count` not displayed). |
| Example | Vinovich, career shares Q1–Q4: 22.6%, 29.1%, 22.9%, 25.3%. |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

### M35. Crew chief compared with the league average

| Field | Value |
|---|---|
| Label on site | **Pop-up, "2026 so far":** "In 2026, Vinovich's crew is calling **13.7** penalties per game vs a league average of **14.7** ▼ 6.8% — letting them play more than most this season." **Pop-up, "Career:"** (or "Tendencies"): "Let-them-play style — fewer flags than average. Bill Vinovich's games average 1.8 fewer penalties per game." **Static `/crew/<slug>/`:** "…average **13.7** accepted penalties over 6 games, 7% below the league's 14.7". **Chart "Crew Chief Flag Rates"** (section 04): a "League avg" marker; red 5%+ above, green 5%+ below. |
| Kind | Derived: a crew chief's rate relative to a league average |
| Numerator | Crew chief rate minus league average |
| Denominator | League average |
| Population | **Season line, static page, chart:** the league's own regular-season rate for the same window (`season_comparison.json` → `league.current`, or `league.baselines.all` on the chart's "2015–25" view). **Career line:** the **unweighted mean of every crew chief's career average** (M26: playoffs included, each rounded to 1 decimal). |
| Time window | Season line and static page: current season. Career line: 2015 to now. Chart: current season or 2015–25. |
| Inclusion rules | As in Terms |
| Benchmark | The league average (the point of the metric) |
| Calculation | Season line: `pctChange()` and `pctBadge()` in `app.js` `openRefereeModal()`; wording bands ±5%. Static page: `(crew ÷ league − 1) × 100`, whole percent (`build_static.py` `crew_pages()`). Career line: `generate_referee_profiles()` `tendencies` (`avgVsLeague`, `avgVsLeaguePct` not displayed; `description` from bands ±5% and ±10%). Chart: `renderPenaltiesByRefChart()`, at least 1 game (current) or 10 (2015–25). |
| Rounding | Rates 1 decimal; change as M2 (pop-up) or whole percent (static page) |
| Provenance | As M25 and M1 |
| Limitations | **Two different league averages in one panel** (C10): the career line's 12.80 (mean of crews, playoffs in) vs the league's 12.59 (2015–25 regular season, games-weighted) and 14.67 (2026). The career line compares a career rate including 2026 with a career mean. The descriptions ("Flag-heavy crew", "Let-them-play style", "Tends to let minor infractions go", "one of the more flag-heavy crews", "letting them play more than most") describe a calling style the rate alone doesn't show (C13). The season line shows the percentage without the absolute difference (rule 3). The "Average Penalties Per Game" explainer points here instead of stating a league average (since #110, D7). |
| Where it appears | Crew pop-up ("2026 so far", "Career:" / "Tendencies"). Static `/crew/<slug>/` summary and FAQ ("the 2026 league average is 14.7"). Static `/crew/` former crew chiefs note ("league average 12.6 per game in 2015–25, 14.7 in 2026 through Week 7", from `league.baselines.all.perGame` and `league.current.perGame`, `build_static.py` `league_levels()`, since #110). Home, League Trends: "Crew Chief Flag Rates" chart (marker, colors, "(<n> g)" labels). JSON: `referee/<slug>.json` → `tendencies.description`; `season_comparison.json` → `league.current.perGame`, `league.baselines.all.perGame`, `crewChiefs[].current`, `crewChiefs[].baselines.all`. |
| Example | Vinovich: season line 13.67 vs 14.67, ▼ 6.8%; static page "7% below"; career line −1.8 (11.0 vs 12.80, −14.1%). Moore: career line +3.7 (16.5 vs 12.80, +28.9%), "Flag-heavy crew". |
| Conflicts | [C10](audits/metric-conflicts-2026-10-28.md#c10-league-average-means-three-things-on-crew-chief-pages), [C13](audits/metric-conflicts-2026-10-28.md#c13-wording-and-framing-section-17-on-crew-chief-pages), [D7](audits/metric-conflicts-2026-10-28.md#d7-fixed-league-average-text-out-of-date) (fixed in #110) |

### M36. Recent games (per-game penalties)

| Field | Value |
|---|---|
| Label on site | Pop-up "Recent Games": teams, score, date ("<season> Wk <n>" tag for this season), "**<n>** flags · <yards> yds". Static `/crew/<slug>/` "Recent games": "Date", "Game", "Score", "Flags", "By team" ("<away> <n> · <home> <n>"). |
| Kind | Raw counts per game |
| Numerator | Penalties (and penalty yards) in one game; by team: penalties on each team |
| Denominator | None |
| Population | The crew chief's games, **playoffs included** |
| Time window | The 10 most recent (20 stored) |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | `generate_referee_profiles()` `recentGames[]`, newest first by date. |
| Rounding | Integers |
| Provenance | nflverse play-by-play and schedules (scores, dates). Every data run. |
| Limitations | Single games vary widely (M27); no league or crew average is shown beside them. Playoff games appear without a label. |
| Where it appears | Crew pop-up; static `/crew/<slug>/`. JSON: `referee/<slug>.json` → `recentGames[].season`, `.week`, `.date`, `.homeTeam`, `.awayTeam`, `.homeScore`, `.awayScore`, `.penalties`, `.yards`, `.homePenalties`, `.awayPenalties` (`.gameId`, `.gameType`, `.stadium`, `.weather`, `.temp` not displayed). |
| Example | See each profile. |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season) |

### Crew styles (session 3)

Session 3. **Examples are from `53e0bd1`** (2026-10-29: 2026 regular season
through Week 7). Source: `crew_styles.json`, built by
`scripts/crew_styles.py` `build_crew_styles()`. Places: the crew pop-up's
"Crew style" block (tabs "2026 style", "Career 2015–25", "Compare years",
with the trajectory chart), the "Crew Chief Style Map" (League Trends,
section 04), the static `/crew/` and `/crew/<slug>/` pages, the CSV's
`career_style`, `/assignments/`, and the one-line style note in game
previews.

**Population and windows** (all entries below):
- **Regular season only**; penalty plays with a `penalty_team`; active crew
  chiefs only (those with a game this season); crew chief from the merged
  assignment.
- **Career** = every regular season **before** the current one (2015–25), at
  least **10 games** (`MIN_GAMES`). **Season** = one regular season, at least
  1 game. **Weekly** (Style Map only) = the current season "through Week N"
  (cumulative) or "Week N only".
- **Benchmarks:** `league` (2015–25), `leagueBySeason.<season>`,
  `leagueCurrent` (the current season) and `weekly.<through|only>.<week>.league`,
  each over the same games as the crew figures it's compared with.

**Season adjustment (career only).** League levels moved a lot over the
window (13.82 per game in 2015, 11.18 in 2022). For career figures each crew
chief is compared with the league **in the seasons they worked**, then
expressed at the 2015–25 league level (`_profiles()`):
- per-game rates: `league rate × crew count ÷ expected count from its seasons`;
- per-flag measures (yards, points, shares): `league value + (crew value −
  league value in its seasons, weighted by the crew's flags)`.
- Unadjusted values are kept in `raw` and shown only in the pop-up's career
  footnote ("Unadjusted: 16.1 flags per game, 7.9 yards per flag").

Spot checks (recomputed with separate code from play-by-play and the merged
assignment): the 2015–25 league values, the top-10 type list, Bill Vinovich's
and Alex Moore's adjusted rates, yards per flag, home share, a shrunk
roughing-the-passer rate, their quadrants, Moore's flags-per-game trait
z-score, and both crew chiefs' "through Week 7" Style Map values: all 30
match. Points per flag isn't recomputed here (What Flags Cost, session 8).

### M37. Crew style: flags per game (season-adjusted career; season; weekly)

| Field | Value |
|---|---|
| Label on site | Pop-up "Crew style" tile "Flags / game" ("16.0", "league 12.6"). Style Map x-axis "Flags per game →", tooltip "<name>: 16.0 flags/game · 8.28 yds/flag (16 games)". Trajectory x-axis "Flags vs that season's league average →" (tooltip "+27% flags vs league"). Trait "More flags: 16.0 per game (league 12.6)". "Compare years" table row "Flags / game". |
| Kind | **Career: derived (season-adjusted exposure rate).** Season and weekly: exposure rate. Trajectory: derived (relative to that season's league). |
| Numerator | Penalties in the crew chief's games (career: adjusted to the 2015–25 league level) |
| Denominator | The crew chief's games in the window |
| Population / Time window | See the section notes: career 2015–25 (10+ games), one season, or the current season through / in a week |
| Inclusion rules | As in Terms, plus penalty plays with a `penalty_team` |
| Benchmark | The league over the same games (`league`, `leagueBySeason`, `leagueCurrent`, `weekly…league`); the Style Map's dashed vertical line |
| Calculation | `crew_styles.py` `_profiles()` (`perGame`; career adjusted as in the section notes); `vsLeague.perGamePct = (crew ÷ league − 1) × 100`; weekly `period()`. |
| Rounding | Stored 2 decimals (`vsLeague` 1); shown 1 decimal (tiles, tooltip), whole percent (trajectory tooltip) |
| Provenance | nflverse play-by-play, officials, schedules; Football Zebras. Every data run. |
| Limitations | **The career value is adjusted, but sits beside raw rates under the same label** (C14): in one pop-up, Moore's "2015–25" row (M1) says 16.1 and the Crew style tile says 16.0, both "flags per game". Season and weekly views rest on few games: the pop-up opens on the current season (6 games for most crew chiefs), flagged "Only <n> games…" below 8 games; the Style Map's "Week N only" is one game per crew, which its subtitle says. The Style Map explainer says career views use "about 95 games each"; the active crew chiefs average 128 (median 125, range 16–172) (D8). |
| Where it appears | Crew pop-up "Crew style" (career, season, compare, trajectory); Home, League Trends: "Crew Chief Style Map" (every period). JSON: `crew_styles.json` → `crews[].perGame`, `crews[].raw.perGame`, `crews[].vsLeague.perGamePct`, `crews[].seasons.<season>.perGame`, `.vsLeague.perGamePct`, `weekly.through.<week>.crews.<name>.perGame`, `weekly.only.<week>.crews.<name>.perGame`, the `league…perGame` fields. |
| Example | Moore career 15.96 adjusted (raw 16.12, 16 games; league 12.59; +26.7%). Vinovich 11.02 (raw 11.02, 171 games; −12.5%). Through Week 7, 2026: Moore 17.67 (6 games), league 14.67. |
| Conflicts | [C14](audits/metric-conflicts-2026-10-28.md#c14-season-adjusted-and-raw-career-rates-under-one-label), [C11](audits/metric-conflicts-2026-10-28.md#c11-career-means-three-different-windows), [D8](audits/metric-conflicts-2026-10-28.md#d8-style-map-explainer-about-95-games-each) |

### M38. Crew style: yards per flag

| Field | Value |
|---|---|
| Label on site | Pop-up tile "Yards / flag" ("8.3", "league 8.4"). Style Map y-axis "Yards per flag (bigger calls) →". Trajectory y-axis "Yards per flag vs league →" (tooltip "−0.14 yds/flag"). Traits "Bigger calls: …" / "Smaller calls: …". |
| Kind | Career: derived (season-adjusted average size of a penalty). Season and weekly: derived (yards ÷ penalties, as M8). |
| Numerator | Penalty yards (as M5) |
| Denominator | Penalties (as M4) |
| Population / Time window | As M37 |
| Inclusion rules | As M5 |
| Benchmark | As M37; the Style Map's dashed horizontal line |
| Calculation | `_profiles()` (`yardsPerFlag`; career adjusted); `vsLeague.yardsPerFlagDiff = crew − league`. |
| Rounding | Stored 2 decimals; shown 1 decimal (tiles), 2 decimals (map tooltip) |
| Provenance | As M37 |
| Limitations | The adjustment can be larger than the differences between crews: Moore's raw 7.89 becomes 8.28 adjusted, while every crew's career value lies between 8.07 and 8.74 (the explainer says "under a yard per flag between crews", which holds). The y-axis is zoomed, so small gaps look large; the explainer says so. Yards depend on where fouls happen as well as which. |
| Where it appears | As M37. JSON: `crews[].yardsPerFlag`, `.raw.yardsPerFlag`, `.vsLeague.yardsPerFlagDiff`, `.seasons.<season>.yardsPerFlag`, `weekly.<through|only>.<week>.crews.<name>.yardsPerFlag`, `league…yardsPerFlag`. |
| Example | Moore 8.28 adjusted (raw 7.89); Vinovich 8.23 (raw 8.22); league 8.42. |
| Conflicts | [C14](audits/metric-conflicts-2026-10-28.md#c14-season-adjusted-and-raw-career-rates-under-one-label) |

### M39. Crew style: points per flag

| Field | Value |
|---|---|
| Label on site | Pop-up tile "Points / flag" ("0.80", "league 0.89"). Traits "Costlier flags: <v> points each (league <l>)" / "Cheaper flags: …". |
| Kind | **Model estimate** (average expected-points cost of a flag) |
| Numerator | Sum of each flag's cost to the penalized team, in expected points (`flag_impact.py` `classify()` → `cost_epa`): for plays wiped out by the foul, nflverse's EPA of the play (sign by side); otherwise penalty yards × a fixed points-per-yard rate; two-point tries and nullified touchdowns handled separately |
| Denominator | Penalties |
| Population / Time window | As M37 |
| Inclusion rules | As M37 |
| Benchmark | `league.costPerFlag` (and per season) |
| Calculation | Mean of `cost_epa` (`_profiles()`, `costPerFlag`; career adjusted as a per-flag measure). |
| Rounding | Stored and shown to 2 decimals |
| Provenance | nflverse play-by-play (EPA from nflverse's expected-points model) and `flag_impact.py`'s constants. Every data run. |
| Limitations | **An estimate presented without the word** (C15): "points" isn't explained in the pop-up, and the trait states it as a fact. It mixes two methods by play type. Defined in full with What Flags Cost (M89; same `classify()` cost, averaged per flag). |
| Where it appears | Crew pop-up "Crew style" (tile, traits, compare table). JSON: `crews[].costPerFlag`, `.raw.costPerFlag`, `.seasons.<season>.costPerFlag`, `league…costPerFlag`. |
| Example | Moore 0.80 (league 0.89): "Cheaper flags: 0.80 points each (league 0.89)". Vinovich 0.87. |
| Conflicts | [C15](audits/metric-conflicts-2026-10-28.md#c15-model-estimates-on-crew-style-pages-not-labeled-as-estimates) |

### M40. Crew style: shares (pre-snap, fourth quarter, on offense, on home team)

| Field | Value |
|---|---|
| Label on site | Pop-up tiles "Pre-snap", "4th quarter", "On offense", "On home team" ("34%", "league 35%"). Traits ("More pre-snap fouls: 40% of flags (league 35%)", "Busier 4th quarters…", "More flags on defenses: 50% on offenses (league 54%)", "More flags on road teams: 42% on home teams (league 50%)"). Static `/crew/<slug>/` FAQ: "In 2015–25, 49% of the flags in his games were on the home team (league: 49%)". |
| Kind | Derived: shares of the crew chief's penalties (career: season-adjusted) |
| Numerator | Penalties that are pre-snap (a fixed list of 13 types), in the 4th quarter, on the offense (`penalty_team == posteam`), or on the home team |
| Denominator | The crew chief's penalties |
| Population / Time window | As M37 |
| Inclusion rules | As M37 |
| Benchmark | The league share over the same games |
| Calculation | `_profiles()` (`preSnapShare`, `q4Share`, `offenseShare`, `homeShare`; career adjusted as per-flag measures). |
| Rounding | Stored 3 decimals; shown whole percent |
| Provenance | As M37 |
| Limitations | Same names as the scoreboard's shares (M15) over different windows. "On offense" follows `posteam`, which on kicks is the kicking team. The home share is a third home-vs-road measure (C12). A trait needs a 3-point gap and a z-score of 1 across crews, so it can rest on a few games in a season view (Moore's 2026 home-share trait is 6 games). |
| Where it appears | Crew pop-up "Crew style"; static `/crew/<slug>/` FAQ (home share). JSON: `crews[].preSnapShare`, `.q4Share`, `.offenseShare`, `.homeShare`, `.raw.*`, `.seasons.<season>.*`, `league…*`. |
| Example | Vinovich: pre-snap 39.5% (league 35.4%), home 48.9% (league 48.6%). Moore: offense 50.0% (league 54.5%). |
| Conflicts | [C12](audits/metric-conflicts-2026-10-28.md#c12-three-measures-of-home-vs-road-for-one-idea), [C14](audits/metric-conflicts-2026-10-28.md#c14-season-adjusted-and-raw-career-rates-under-one-label) |

### M41. Crew style: penalty-type rates vs the league (shrunk)

| Field | Value |
|---|---|
| Label on site | Pop-up "How often they call each type vs the league" (bars, "+79%"). "Compare years" rows under "Penalty types vs that season's league rate". Traits "Calls more roughing the passer: 79% above the league rate". Static `/crew/<slug>/`: table "Penalty types vs the league (2015–25, season-adjusted, per game)" ("Penalty", "Per game", "vs league rate"); FAQ "What penalties does <name> call most? Per game, 2015–25: …". |
| Kind | **Model estimate** (rate shrunk toward the league), plus a relative difference |
| Numerator | Penalties of the type in the crew chief's games (career: adjusted to the 2015–25 level), **plus 20 games' worth of the league rate** (`SHRINK = 20`) |
| Denominator | The crew chief's games plus 20 |
| Population / Time window | As M37; the same 10 types (the most common in 2015–25) in every view |
| Inclusion rules | As M37 |
| Benchmark | The league's per-game rate of the type over the same games (`types.<type>.league`) |
| Calculation | `_profiles()`: `shrunk = (count + 20 × league rate) ÷ (games + 20)`; `diffPct = (shrunk ÷ league − 1) × 100`. |
| Rounding | Rate stored 3 decimals, shown 2 (static table); difference whole percent |
| Provenance | As M37 |
| Limitations | **Shown as observed, not labeled as estimates** (C15): Moore's "79% above" is the shrunk value; observed, he had 15 in 16 games (0.94 per game vs the league's 0.41, +129%). The pop-up's footnote says rates are "pulled toward the league average" but doesn't call them estimates; the static FAQ gives the shrunk rates as "per game". Shrinkage matters most for short careers and single seasons. "Calls more" attributes the rate to the crew chief (C13). |
| Where it appears | Crew pop-up (fingerprint bars, compare table, traits); static `/crew/<slug>/` (type table, FAQ). JSON: `crews[].types.<type>.perGame`, `.league`, `.diffPct`; `crews[].seasons.<season>.types.<type>.*`; `types[]` (the list). |
| Example | Roughing the passer: Moore 0.732 shrunk (raw 0.938), +79%; Vinovich 0.205 (raw 0.181), −50%; league 0.409. |
| Conflicts | [C15](audits/metric-conflicts-2026-10-28.md#c15-model-estimates-on-crew-style-pages-not-labeled-as-estimates), [C13](audits/metric-conflicts-2026-10-28.md#c13-wording-and-framing-section-17-on-crew-chief-pages) |

### M42. Crew style traits

| Field | Value |
|---|---|
| Label on site | Pop-up bullet list under the tiles (up to 4); "Close to the league average on everything we track" when none. Static `/crew/<slug>/` list and FAQ ("Compared with other crews: …"). Game previews: the first trait in the crew's style note. |
| Kind | Derived: a selection of M37–M41 written as sentences |
| Numerator / Denominator | — (each trait quotes one metric and its league value) |
| Population / Time window | As M37 (career or one season); compared across **active crew chiefs only** |
| Inclusion rules | A metric qualifies when it differs from the league by a minimum (flags per game 5% relative; yards 0.2; points 0.03; shares 3 points; a type 15%) **and** its z-score across active crews is at least 1; the 4 largest by z-score are kept |
| Benchmark | The league value (in the text) and the other active crews (the z-score) |
| Calculation | `build_crew_styles()` `styles_for()` → `traits[]` (`text`, `key`, `z`, `direction`); wording in `TRAIT_TEXT`. |
| Rounding | Values in the text: 1 decimal (per game, yards), 2 (points), whole percent (shares, types) |
| Provenance | As M37 |
| Limitations | Relative to whichever crews are active this year, so a trait can appear or vanish when the group changes. Type traits quote shrunk estimates as facts (C15). Season traits can rest on 6 games. Phrases like "Calls more …" and "Busier 4th quarters" describe the crew chief, not the games (C13). |
| Where it appears | Crew pop-up; static `/crew/<slug>/`; game previews (`previewCrewStyleHtml()`). JSON: `crews[].traits[].text` (`.key`, `.z`, `.direction` not displayed); `crews[].seasons.<season>.traits[]`. |
| Example | Moore career: "Cheaper flags: 0.80 points each (league 0.89)", "More flags: 16.0 per game (league 12.6)" (z 3.0), "Calls more roughing the passer: 79% above the league rate", "More flags on defenses: 50% on offenses (league 54%)". |
| Conflicts | [C15](audits/metric-conflicts-2026-10-28.md#c15-model-estimates-on-crew-style-pages-not-labeled-as-estimates), [C13](audits/metric-conflicts-2026-10-28.md#c13-wording-and-framing-section-17-on-crew-chief-pages) |

### M43. Crew style: "Calls most like" (similar crew chiefs)

| Field | Value |
|---|---|
| Label on site | Pop-up (career tab): "Calls most like: John Hussey · Clay Martin". Static `/crew/<slug>/`: "Calls most like: …". |
| Kind | Derived: nearest neighbours on the career fingerprint |
| Numerator / Denominator | — |
| Population / Time window | Active crew chiefs, career (2015–25, 10+ games) |
| Inclusion rules | — |
| Benchmark | The other active crew chiefs |
| Calculation | Distance between crews on the standardized career metrics (M37–M41: 7 metrics and 10 type rates, each as a z-score across active crews, equally weighted); the two smallest (`crews[].similar[]`: `name`, `slug`, `distance`). |
| Rounding | Names only; `distance` stored 2 decimals, not displayed |
| Provenance | As M37 |
| Limitations | Equal weights make the 10 type rates count for more than the 7 other metrics together. A short career's shrunk type rates sit near the league, which pulls it toward the middle. Nothing says how close "most like" is. |
| Where it appears | Crew pop-up; static `/crew/<slug>/`. JSON: `crews[].similar[].name`, `.slug` (`.distance` not displayed). |
| Example | Vinovich: John Hussey (4.92), Clay Martin (5.09). Moore: Clete Blakeman (6.77), Alex Kemp (6.88). |
| Conflicts | None |

### M44. Crew style quadrant ("Game-changers", "Stop-and-start", "Few but costly", "Let them play")

| Field | Value |
|---|---|
| Label on site | Pop-up badge and line ("Let them play" · "fewer flags, smaller calls"). Style Map and trajectory quadrant labels and dot colors. "Compare years" row "Style". Static `/crew/`: column "Career style"; `/crew/<slug>/`: "Calling style": "Career (2015–25): **Let them play**, fewer flags, smaller calls. 2026 so far: **Let them play**." `/assignments/`: "Crew career style". `crew_chiefs_<season>.csv`: `career_style`. Game previews: the style note. |
| Kind | Derived: a label from two comparisons |
| Numerator / Denominator | — |
| Population / Time window | As M37 (career, each season, each Style Map period) |
| Inclusion rules | — |
| Benchmark | The league's flags per game and yards per flag over the same games |
| Calculation | `QUADS[(perGame > league, yardsPerFlag > league)]`: more flags + bigger calls "Game-changers"; more + smaller "Stop-and-start"; fewer + bigger "Few but costly"; fewer + smaller "Let them play". Style Map colors: red, yellow, blue, green. |
| Rounding | Label only |
| Provenance | As M37 |
| Limitations | Any difference counts, however small: a crew 0.01 yards above the league is "bigger calls". It can change with a few games (Moore: "Stop-and-start" career, "Game-changers" in 2026 over 6 games). The names describe a style or effect ("Game-changers", "Let them play") that two averages don't show (C13). Red marks "Game-changers" but yellow marks "Stop-and-start", also more flags (C13). |
| Where it appears | As the label row. JSON: `crews[].archetype` (`key`, `title`, `description`), `crews[].seasons.<season>.archetype`. |
| Example | Career: 8 "Game-changers", 4 "Few but costly", 3 "Let them play", 2 "Stop-and-start" (17 active crew chiefs). |
| Conflicts | [C13](audits/metric-conflicts-2026-10-28.md#c13-wording-and-framing-section-17-on-crew-chief-pages) |

### M45. Games with a crew chief assigned (this week)

| Field | Value |
|---|---|
| Label on site | Static `/assignments/`: "14 of 14 Week 8 games have a crew chief assigned." Table "Game", "Date", "TV", "Crew chief" ("TBA" when none). |
| Kind | Raw count |
| Numerator | This week's games with a published crew chief |
| Denominator | This week's games |
| Population | The upcoming week in `previews/latest.json` |
| Time window | One week |
| Inclusion rules | Crew chief from Football Zebras assignments, matched to the schedule (`previews.py`) |
| Benchmark | None |
| Calculation | `build_static.py` `assignments_page()`: count of `games[]` with a `crew`. The previews' own count is `previews/<week>.json` → `assignments.assigned`, `.games` (previews session). |
| Rounding | Integers |
| Provenance | Football Zebras (`fetch_assignments.py` → `assignments/<season>-week-<nn>.json`); nflverse schedules. Every data run. |
| Limitations | Shows the latest published assignments; a late change appears on the next run. |
| Where it appears | Static `/assignments/` summary and table. The page's other columns: "Crew 2026 flags / game" (M1), "Crew career style" (M44), "Projected flags" (model estimate; previews session). `assignments/*.json` files are pipeline inputs (crew chief fallback, previews); the site doesn't read them directly. |
| Example | Week 8: 14 of 14 (source posted Tue 27 Oct 2026). |
| Conflicts | None |

**Crew style fields not displayed anywhere:** `crew_styles.json` →
`crews[].slug` (link), `crews[].current` (a copy of the current season's rates; the map and pop-up read `seasons.<season>`), `.traits[].key`, `.z`, `.direction`,
`.similar[].distance`, `.seasonAdjusted`, `.raw.*` other than the career
footnote's two values, `.archetype.key` (styling), `careerSeasons` (used
for labels), `season`, `weekly.complete` (menu notes "cumulative" / "in
progress"), `weekly.weeks`, `weekly.season`, `notes`, `generatedAt`;
`assignments/<season>-week-<nn>.json` (all fields).

**Season figures on crew chief pages** use session 1's entries:
- **Card rows** ("2026", "2025", "2015–25": "Pen/g", "Yds/g", "<n> g") and
  the pop-up's "2026 vs history" block ("Pen/g", "Yds/g", "Yds/pen"): M1,
  M7, M8, M6, from `season_comparison.json` → `crewChiefs[]` /
  `inactiveCrewChiefs[]` → `current`, `baselines.lastSeason`,
  `baselines.all`.
- **Change badges** on cards and in the pop-up ("vs 2025", "vs 2015–25"):
  M2. Under 4 games this season the badge is dimmed and the card adds "Only
  <n> games this season — early numbers swing a lot."
- **Static `/crew/`:** table "Crew chief", "2026 games" (M6), "2026 flags /
  game" (M1), "2015–25 flags / game" (M1, `all`), "Career style" (M44);
  top-3 summary (M1); former crew chiefs: "Seasons in the data" (M30),
  "Games" and "Flags / game" (M6, M1 `all`). Its note "league levels vary by
  season (league average 12.6 per game in 2015–25, 14.7 in 2026 through Week
  7)" takes both numbers from `season_comparison.json` (M35; since #110 it
  replaced the fixed "about 13.5 per game in 2015–19, 11–13 since").
- **Static `/crew/<slug>/` tiles:** "2026 flags / game" (M1, with games and
  "league 14.7"), "2026 yards / game" (M7), "2025 flags / game", "2015–25
  flags / game" (M1, with games).
- **Pre-filled page source** (`build_static.py` `home_prefill()`): `REFEREES`
  (each active crew chief's season and 2015–25 rate: M1) and `DATA_TABLE`
  (the Complete Crew Chief Stats rows: M25–M29).
- **`crew_chiefs_<season>.csv`** (`build_static.py` `dataset_page()`, active
  crew chiefs, most flags per game first): `crew_chief`, `games_<season>`
  (M6), `flags_per_game_<season>` (M1), `yards_per_game_<season>` (M7),
  `career_games_2015_25` (M6, `all`), `career_flags_per_game_2015_25` (M1,
  `all`), `career_style` (M44). Values are stored precision (2
  decimals), not rounded for display.

**Fields in these files not displayed anywhere:** `referees.json` →
`total_penalties`, `std_dev`; `referee/<slug>.json` → `stats.totalPenalties`,
`stats.stdDev`, `seasonStats[].penalties`, `seasonStats[].homeBias`,
`currentSeasonGames`, `priorSeasonGames`, `tendencies.avgVsLeague`,
`tendencies.avgVsLeaguePct`, `explanations.*`, `penaltyTypeComparison[]`
counts, `quarterDistribution[].count`, `regularSeasonStats[]` penalties and
yards, and `recentGames[]` `gameType`, `stadium`, `weather`, `temp`. They are
public in the JSON. `explanations.homeBiasPct` matches the explainer since
#110 ("Road teams' share of this crew's penalties minus home teams' share, in
percentage points").

## Teams

Session 4. **Examples are from `53e0bd1`** (2026-10-29: 2026 regular season
through Week 7). Places covered: the "Team Discipline" section (02: division
tiles, team cards, comparison buttons), the team pop-up, the static `/team/`
and `/team/<ABBR>/` pages, the guide's team question, the home page's
pre-filled division lists, and `teams_<season>.csv`. The pop-up's "What flags
cost <team>" block and the static pages' "Points given away / game" come from
`flag_impact.json`: What Flags Cost, M89–M97.

**One source.** Every number here comes from `scripts/team_pages.py`
`build_team_pages()`, which writes `teams/index.json` and `teams/<ABBR>.json`:
- **Population:** regular season only; a team's **own games** with
  play-by-play; penalties as counted (Terms) **that name a `penalty_team`**
  (0 left out in 2026). Overtime counts, except in the quarter rows (M57).
- **Teams by today's abbreviation:** seasons before a move count for the team
  as it is now (STL → LA, SD → LAC, OAK → LV; `scripts/teams.py`, #105).
- **"Current"** is every regular-season game played so far, partial-week
  games included.
- **Paths:** fields are written `file` → `path`. Braces list alternatives:
  `{current,lastSeason}.perGame` means `current.perGame` and
  `lastSeason.perGame`. `<key>` is a comparison (`sameWeeks`, `lastSeason`,
  `last3`, `all`); `<type>` is a penalty type.

**Spot checks** (separate code, from nflverse play-by-play, schedules,
officials and the saved crew assignments): Las Vegas (Oakland through 2019)
and Kansas City. For each: current games, per game, yards per game, drawn,
net, offense and defense, home and away, last season, rank, the same-weeks
comparison, 2016 per game and rank (LV's Oakland seasons), one crew chief
row, one opponent row and one type trend in three seasons. **47 of 47
match**, plus the team "league" rate (7.34). nflverse play-by-play already
uses today's abbreviations (no `OAK`, `SD` or `STL` penalties in 2015).

### M46. Team penalties per game (committed)

| Field | Value |
|---|---|
| Label on site | **Team cards:** big number, then "penalties/game · <yards> yds". **Pop-up:** "Pen/g" column (rows "<season>" and the comparison's short label, each "<n> g"); change badge "Pen/g". **Static `/team/`:** "<season> flags / game", "<season − 1> flags / game"; summary "Most penalized per game in 2026 through Week 7: …". **Static `/team/<ABBR>/`:** tile "Flags / game" ("<n> games · league 7.3"); summary "averaging **6.8 accepted penalties per game** in 2026 (6 games) … Last season: 7.0 per game"; FAQ "How many penalties do the <team> average in <season>?". **Guide:** "Which NFL team commits the most penalties in 2026?". **Home page source:** "<team> 9.3 flags/game" (division lists). **Summary line:** "Most penalized team: <team> (<rate> per game)". |
| Kind | Exposure rate |
| Numerator | Penalties on **one team** (`penalty_team` = the team) |
| Denominator | That team's games |
| Population | One team's regular-season games; overtime included; no minimum games |
| Time window | **Current:** every game this season so far, partial week included. **Comparisons:** see M48. **Last season:** all of the previous regular season. **All prior:** every season from 2015 to last season. |
| Inclusion rules | As in Terms, and the penalty must name a team |
| Benchmark | The team "league" rate (M47) on the cards and static pages; the selected comparison (M48) on the cards and in the pop-up |
| Calculation | Mean of the team's flags per game (games with no flag count as 0), so multi-season windows are games-weighted. `block()` → `perGame`, `games`, `penalties`. |
| Rounding | Stored 2 decimals → shown 1 decimal everywhere; `teams_<season>.csv` keeps 2. Matches the default. |
| Provenance | nflverse play-by-play and schedules. Every data run. |
| Limitations | **About half M1's rate, under the same words:** M1 ("Penalties per game", "Flags per game", `flags_per_game` in `flags_by_season.csv`) is a game total for both teams, 14.7; a team's rate is one team, 7.3 on average ([C16](audits/metric-conflicts-2026-10-28.md#c16-flags-per-game-a-game-total-and-one-teams-total-under-one-label)). Counts flagged plays, not flags (C5). Current-season rates rest on 6 or 7 games; the pop-up's "Only <n> games this season" note appears only below 4 games ([C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways)). A team's rate reflects its opponents and crews as well as its own play. |
| Where it appears | `teams/index.json` → `divisions[].teams[].perGame`, `divisions[].teams[].games`, `divisions[].teams[].lastSeasonPerGame` (team cards, static `/team/` table and summary, guide, home page source, summary line). `teams/<ABBR>.json` → `{current,lastSeason,allPrior,baselines.<key>}.perGame`, `{current,lastSeason,allPrior,baselines.<key>}.games`, `{current,lastSeason,allPrior,baselines.<key>}.penalties` (pop-up rows; static `/team/<ABBR>/` tile, summary and FAQ). Not displayed: `penalties` (all four), and `allPrior` (only a fallback when a file has no `baselines`). `teams_<season>.csv` → `team`, `games`, `flags_per_game`, `last_season_flags_per_game`. |
| Example | KC 2026: 41 penalties in 6 games = **6.83**, shown 6.8; 2025: 119 in 17 = 7.00; 2015–25: 1,183 in 181 = 6.54. Most: GB 9.29 (7 games); fewest: IND 5.14 (7). Spot-checked (see above). |
| Conflicts | [C5](audits/metric-conflicts-2026-10-28.md#c5-penalties-counts-plays-with-an-accepted-penalty), [C16](audits/metric-conflicts-2026-10-28.md#c16-flags-per-game-a-game-total-and-one-teams-total-under-one-label), [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways), [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages) |

### M47. Team "league average" (penalties per team per game)

| Field | Value |
|---|---|
| Label on site | Team cards: "vs league avg 7.3" (with a change badge). Static `/team/`: "League average: 7.3 per team per game." Static `/team/<ABBR>/`: "league 7.3" (tile and summary). |
| Kind | Exposure rate (benchmark) |
| Numerator | Every team's penalties this season |
| Denominator | Team-games (2 per game) |
| Population | All 32 teams, regular season |
| Time window | **Current season only.** It doesn't follow the comparison buttons. |
| Inclusion rules | As M46 |
| Benchmark | It is the benchmark: the card's badge compares the team's current rate with it |
| Calculation | Mean flags per team-game in the current season = league penalties ÷ (2 × games). `league_pg` → `leaguePerGame`. |
| Rounding | Stored 2 decimals → shown 1 |
| Provenance | As M46 |
| Limitations | **Half M1's league rate** (14.67 per game): both are "league average", one per team and one per game ([C16](audits/metric-conflicts-2026-10-28.md#c16-flags-per-game-a-game-total-and-one-teams-total-under-one-label)). Only the static `/team/` page says "per team per game". The badge shows the percentage only (M2). |
| Where it appears | `teams/index.json` → `leaguePerGame`; `teams/<ABBR>.json` → `leaguePerGame` (not displayed; the pages read the index) |
| Example | 2026: 1,570 penalties in 214 team-games = **7.34**, shown 7.3 (M1: 1,570 in 107 games = 14.67). Recomputed: 7.336, a match. |
| Conflicts | [C10](audits/metric-conflicts-2026-10-28.md#c10-league-average-means-three-things-on-crew-chief-pages), [C16](audits/metric-conflicts-2026-10-28.md#c16-flags-per-game-a-game-total-and-one-teams-total-under-one-label) |

### M48. Team comparison periods ("same weeks", last season, last 3, all seasons)

| Field | Value |
|---|---|
| Label on site | Buttons (cards and pop-up, shared): "2025 thru Wk 7", "All of 2025", "Last 3 seasons", "All seasons". Pop-up: "Comparing 2026 with **2025 through Week 7**. Every comparison below follows this choice."; heading "2026 vs 2025 through week 7"; row label and legends use the short label ("2025 Wk 1–7", "2023–25 avg", "2015–25 avg"). Card footer: "2025 Wk 1–7 6.7/g" with a badge. |
| Kind | Definition of the comparison windows (applies to M46, M49–M53, M55–M58) |
| Numerator / Denominator | As the metric compared |
| Population | The same team |
| Time window | `sameWeeks`: previous season, Weeks 1 to the **team's own week** = the later of the league's last completed week and the team's latest game this season. `lastSeason`: all of the previous regular season. `last3`: the three previous seasons. `all`: every season from 2015 to last season. Default: `sameWeeks`. |
| Inclusion rules | As M46 |
| Benchmark | — |
| Calculation | `baseline_defs`, `team_week`; each baseline holds the `block()` fields plus `types`, `drawnTypes`, `quarters` (M55–M57). Multi-season windows are games-weighted. |
| Rounding | — |
| Provenance | `scripts/weeks.py` `completed_week()` and the schedule |
| Limitations | **Teams follow the crew chief rule** (a team that has played into a partial week is compared through that week; [C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison)); the index's button label uses the league's week, so on a day with a partial week a card can read "Wk 1–8" under a "thru Wk 7" button. At `53e0bd1` every team's week is 7. "Same weeks" means the same calendar weeks, not the same number of games: KC has 6 games in 2026 (bye) and 7 in 2025 Weeks 1–7 (both are per-game rates). |
| Where it appears | `teams/index.json` → `baselines[].key`, `baselines[].label`, `baselines[].short`, `defaultBaseline`, `throughWeek`, `divisions[].teams[].baselinePerGame.<key>`, `divisions[].teams[].throughWeek`. `teams/<ABBR>.json` → `baselines.<key>.label`, `baselines.<key>.short`, `defaultBaseline`, `throughWeek`, `priorSeasons[]` (start year of the crew chief and opponent headings, "2015–2026"). |
| Example | KC same weeks: 2025 Weeks 1–7, 7 games, 6.71 per game; last 3 (2023–25): 51 games, 6.06; all (2015–25): 181 games, 6.54. LV same weeks: 6.43 (recomputed: 6.429). |
| Conflicts | [C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison), [C8](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names) |

### M49. Penalties drawn per game (opponents' penalties in the team's games)

| Field | Value |
|---|---|
| Label on site | Pop-up: "Drawn/g" column and change badge. Static `/team/<ABBR>/`: tile "Opponent flags / game" ("flags drawn"); FAQ "Opponents have been flagged <x> times per game". |
| Kind | Exposure rate |
| Numerator | Penalties on the **opponent** in the team's games |
| Denominator | The team's games |
| Population, Time window, Inclusion rules | As M46 |
| Benchmark | The selected comparison (M48) |
| Calculation | Per game, the opponent's flags; mean over the team's games. `block()` → `drawnPerGame`, `drawnYardsPerGame`. |
| Rounding | Stored 2 decimals (yards 1) → shown 1 decimal |
| Provenance | As M46 |
| Limitations | "Drawn" reads as something the team did; it's the opponents' flags in its games ([C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages)). The badge is red when opponents were flagged more (red = more penalties). Drawn yards per game isn't displayed. |
| Where it appears | `teams/<ABBR>.json` → `{current,lastSeason,allPrior,baselines.<key>}.drawnPerGame`; not displayed: `{current,lastSeason,allPrior,baselines.<key>}.drawnYardsPerGame` |
| Example | KC 2026: **6.17** (37 opponent flags in 6 games); LV 2026: 8.29. Recomputed, a match. |
| Conflicts | [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages) |

### M50. Flag margin (net: drawn minus committed)

| Field | Value |
|---|---|
| Label on site | Pop-up tile "Flag margin": "+2.0", with "drew more than committed per game" / "committed more than drew per game" / "even". Opponent table: "Net" (M61). |
| Kind | Derived: difference of two exposure rates (M49 − M46) |
| Numerator | Opponents' flags minus the team's flags, per game |
| Denominator | The team's games |
| Population, Time window, Inclusion rules | As M46. The tile shows the current season only (it doesn't follow the buttons). |
| Benchmark | None |
| Calculation | Mean of (drawn − committed) per game. `block()` → `netPerGame`. Positive = opponents flagged more. |
| Rounding | Stored 2 decimals → shown 1, with a sign |
| Provenance | As M46 |
| Limitations | A difference of two rates with no baseline beside it on the tile. "Drew" ([C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages)). |
| Where it appears | `teams/<ABBR>.json` → `current.netPerGame` (tile); not displayed: `{lastSeason,allPrior,baselines.<key>}.netPerGame` |
| Example | LV 2026: 8.29 − 6.29 = **+2.0**; KC: −0.67, shown "-0.7". Recomputed, a match. |
| Conflicts | [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages) |

### M51. Offense / defense split (team)

| Field | Value |
|---|---|
| Label on site | Pop-up tile "Offense / Defense": "3.0 / 3.8", "flags per game on each side" |
| Kind | Exposure rate (two) |
| Numerator | The team's penalties when it had the ball (`penalty_team` = `posteam`) / all its other penalties |
| Denominator | The team's games |
| Population, Inclusion rules | As M46 |
| Time window | Current season only (the tile doesn't follow the buttons) |
| Benchmark | None |
| Calculation | `offense` flag per penalty; `block()` → `offensePerGame`, `defensePerGame` (= per game minus offense) |
| Rounding | Stored 2 decimals → shown 1 |
| Provenance | As M46 |
| Limitations | Same split as M15: on kicking plays `posteam` is the receiving team, so special-teams fouls are split by that field and "defense" means "everything not on offense". |
| Where it appears | `teams/<ABBR>.json` → `current.offensePerGame`, `current.defensePerGame` (tile); not displayed: `{lastSeason,allPrior,baselines.<key>}.offensePerGame`, `{lastSeason,allPrior,baselines.<key>}.defensePerGame` |
| Example | KC 2026: 3.00 / 3.83; LV: 3.29 / 3.00. Recomputed, a match. |
| Conflicts | None |

### M52. Home / away penalties per game (team)

| Field | Value |
|---|---|
| Label on site | Pop-up tile "Home / Away": "7.7 / 6.0", "flags per game" |
| Kind | Exposure rate (two) |
| Numerator | The team's penalties in its home games / in its road games |
| Denominator | Its home games / its road games |
| Population, Inclusion rules | As M46. Home = the schedule's `home_team` (the designated team at neutral sites). |
| Time window | Current season only (the tile doesn't follow the buttons) |
| Benchmark | None |
| Calculation | `block()` → `homePerGame`, `awayPerGame`; empty (—) when the team has no game of that kind |
| Rounding | Stored 2 decimals → shown 1 |
| Provenance | As M46 |
| Limitations | No games count on the tile: each side rests on 3 or 4 games this season (KC: 3 home, 3 road). A different idea from a crew chief's Home Bias (M28) and the league's home share (M15, M21): see [C12](audits/metric-conflicts-2026-10-28.md#c12-three-measures-of-home-vs-road-for-one-idea). |
| Where it appears | `teams/<ABBR>.json` → `current.homePerGame`, `current.awayPerGame` (tile); not displayed: `{lastSeason,allPrior,baselines.<key>}.homePerGame`, `{lastSeason,allPrior,baselines.<key>}.awayPerGame` |
| Example | KC 2026: 7.67 home, 6.00 road; LV: 6.25 (4 home games), 6.33 (3 road). Recomputed, a match. |
| Conflicts | [C12](audits/metric-conflicts-2026-10-28.md#c12-three-measures-of-home-vs-road-for-one-idea), [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways) |

### M53. Team penalty yards per game

| Field | Value |
|---|---|
| Label on site | Team cards: "· 72 yds". Pop-up: "Yds/g" column and change badge. Static `/team/<ABBR>/`: tile "Penalty yards / game" ("2025: <x>"); FAQ "<x> penalty yards per game". |
| Kind | Exposure rate |
| Numerator | Penalty yards on the team (`penalty_yards`, absolute value) |
| Denominator | The team's games |
| Population, Time window, Inclusion rules | As M46 |
| Benchmark | The selected comparison (M48); static page: last season |
| Calculation | `block()` → `yardsPerGame`, `yards` |
| Rounding | Stored 1 decimal → **cards and pop-up show whole yards**, static pages 1 decimal. M7 (league) shows 1 decimal. |
| Provenance | As M46 |
| Limitations | Same yardage as M7 (yards assessed on the play). Total yards aren't displayed. |
| Where it appears | `teams/index.json` → `divisions[].teams[].yardsPerGame`. `teams/<ABBR>.json` → `{current,lastSeason,allPrior,baselines.<key>}.yardsPerGame`; not displayed: `{current,lastSeason,allPrior,baselines.<key>}.yards` |
| Example | KC 2026: 359 yards in 6 games = **59.8**, shown "60 yds" in the pop-up and 59.8 on the static page. Recomputed, a match. |
| Conflicts | None |

### M54. Most-penalized rank

| Field | Value |
|---|---|
| Label on site | Team cards: "Most-penalized rank **#22**". Pop-up tile "Most-penalized rank": "#22", "of 32 · last season #7"; season chart tooltip "rank #22". Static `/team/`: "Rank" column; static `/team/<ABBR>/`: "#22 most in the NFL". |
| Kind | Derived: rank of M46 among teams |
| Numerator / Denominator | M46 for each team in the season |
| Population | Every team that played that regular season (32) |
| Time window | Each season; the current one so far |
| Inclusion rules | As M46 |
| Benchmark | Last season's rank (pop-up) |
| Calculation | `rank(ascending=False, method='min')` on per-game rates by season: 1 = most per game; **tied teams share the higher rank** and the next rank is skipped. `rank_of`. |
| Rounding | Whole number |
| Provenance | As M46 |
| Limitations | Ranks rates from 6 or 7 games with no sample label and no "observed" label ([C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways), [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages)). Ties aren't marked: 8 tied groups in 2026 (CLE 9.00 in 7 games and LAC 9.00 in 6 are both #2; the next is #4). Teams with a bye are ranked on one game fewer. |
| Where it appears | `teams/index.json` → `divisions[].teams[].rank`. `teams/<ABBR>.json` → `rank.current`, `rank.lastSeason`, `rank.of`, `history[].rank`. `teams_<season>.csv` → `rank`. |
| Example | KC #22 (2026), #7 (2025); LV #27 (2026); LV 2016 (as Oakland) #1 at 9.19. Recomputed, a match. |
| Conflicts | [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways), [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages) |

### M55. Team penalty types committed per game

| Field | Value |
|---|---|
| Label on site | Pop-up: "What they get flagged for: 2026 vs 2025 Wk 1–7", legend "2026" / "2025 Wk 1–7 avg" / "per game", paired bars with values and a badge. Static `/team/<ABBR>/`: "Most common penalties" table ("Penalty", "2026 / game", "2015–25 / game"); FAQ "What penalties are the <team> called for most?". |
| Kind | Exposure rate, one per type |
| Numerator | The team's penalties of that `penalty_type` |
| Denominator | The team's games in the window |
| Population, Inclusion rules | As M46 |
| Time window | Current season vs the selected comparison (pop-up); vs all prior seasons, 2015–25 (static page, `priorPerGame`) |
| Benchmark | The comparison window's rate for the same type |
| Calculation | Types shown: the team's 8 most common this season plus its 5 most common in prior seasons. `committedTypes[]`; each baseline's `types.<type>` (keys also include the type-trend types, M58). The pop-up swaps `priorPerGame` for the selected baseline's rate. |
| Rounding | Stored 2 decimals → pop-up 1 decimal, static page 2 decimals |
| Provenance | As M46 |
| Limitations | Rare types on 6 games swing (a type at 0.17 per game is one flag). The count this season isn't shown here (it is in M58). Badge percentage only (M2). |
| Where it appears | `teams/<ABBR>.json` → `committedTypes[].type`, `committedTypes[].currentPerGame`, `committedTypes[].priorPerGame`, `baselines.<key>.types.<type>`; `committedTypes[].currentCount` not displayed |
| Example | KC 2026: offensive holding 1.67 per game (10), vs 1.43 in 2015–25 and 1.43 in 2025 Weeks 1–7; illegal formation 0.83 (5) vs 0.13. |
| Conflicts | [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways) |

### M56. Team penalty types drawn per game

| Field | Value |
|---|---|
| Label on site | Pop-up: "What they draw from opponents", paired bars (legend as M55) |
| Kind | Exposure rate, one per type |
| Numerator | Opponents' penalties of that type in the team's games |
| Denominator | The team's games in the window |
| Population, Time window, Inclusion rules | As M55 |
| Benchmark | The selected comparison |
| Calculation | Types shown: the 6 most common this season plus the 3 most common in prior seasons. `drawnTypes[]`; each baseline's `drawnTypes.<type>`. |
| Rounding | Stored 2 decimals → shown 1 |
| Provenance | As M46 |
| Limitations | "Draw" ([C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages)); small samples as M55 |
| Where it appears | `teams/<ABBR>.json` → `drawnTypes[].type`, `drawnTypes[].currentPerGame`, `drawnTypes[].priorPerGame`, `baselines.<key>.drawnTypes.<type>` |
| Example | KC 2026: offensive holding, false start and delay of game 1.33 each (8 in 6 games); delay of game 0.28 in 2015–25. |
| Conflicts | [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages) |

### M57. Team penalties by quarter

| Field | Value |
|---|---|
| Label on site | Pop-up: "⏱️ When they get flagged", rows by quarter, paired bars (legend as M55) |
| Kind | Exposure rate, one per quarter |
| Numerator | The team's penalties in quarter 1, 2, 3 or 4 (`qtr`) |
| Denominator | The team's games in the window |
| Population, Time window, Inclusion rules | As M55, **overtime left out** |
| Benchmark | The selected comparison |
| Calculation | `quarters[]` (current, all prior); each baseline's `quarters[]` (4 values) |
| Rounding | Stored 2 decimals → shown 1 |
| Provenance | As M46 |
| Limitations | The four quarters don't add up to M46 when the team had an overtime flag (KC 2026: 6.66 vs 6.83; 10 team flags in overtime league-wide in 2026). Same per-quarter idea as M34 for crew chiefs. |
| Where it appears | `teams/<ABBR>.json` → `quarters[].quarter`, `quarters[].currentPerGame`, `quarters[].priorPerGame`, `baselines.<key>.quarters[]` |
| Example | KC 2026 2nd quarter: 2.33 per game vs 1.57 in 2025 Weeks 1–7. |
| Conflicts | None |

### M58. "Which calls are rising" (team penalty-type trends)

| Field | Value |
|---|---|
| Label on site | Pop-up: "Which calls are rising for KC? 2026 vs 2025 Wk 1–7, biggest increases first"; columns "Penalty" (count this season in brackets), "2026", the comparison, "Change" (absolute and badge), "Since 2015 ▾" (trend line). Footnote: "Flags on KC per game … Trend line: each season since 2015 (pick the start in the column header), this season in yellow." |
| Kind | Exposure rate per type and season; Change is derived (difference) |
| Numerator | The team's penalties of that type |
| Denominator | The team's games in that season (or window) |
| Population, Inclusion rules | As M46 |
| Time window | Current season vs the selected comparison; the trend line has every season from 2015 (the start can be picked) |
| Benchmark | The selected comparison |
| Calculation | Types: the team's 12 most common over **all seasons from 2015** plus every type in M55. `typeTrends[]`; rows sorted by `current − base`. |
| Rounding | Stored 2 decimals → shown 2 decimals |
| Provenance | As M46 |
| Limitations | Shows the absolute change and the baseline beside the percentage (rule 3 met). Rare types swing; the footnote says so ("<n> games in, so rarer penalties can swing"). The code comment says "since 2020"; the code and the page use every season from 2015 (comment only). |
| Where it appears | `teams/<ABBR>.json` → `typeTrends[].type`, `typeTrends[].current`, `typeTrends[].currentCount`, `typeTrends[].bySeason[].season`, `typeTrends[].bySeason[].perGame`; the comparison from `baselines.<key>.types.<type>` |
| Example | KC 2026 vs 2025 Weeks 1–7, top row: illegal use of hands 0.50 (3) vs 0.00, "+0.50". KC offensive holding: 1.19 (2015), 1.71 (2025), 1.67 (2026). Recomputed, a match. |
| Conflicts | [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways) |

### M59. Watchlist (players flagged this season)

| Field | Value |
|---|---|
| Label on site | Pop-up: "Watchlist (2026)": player, "<n> flags · <yards> yds", the top 3 types ("×2" when repeated) |
| Kind | Raw count |
| Numerator | The team's penalties naming the player (`penalty_player_name`) |
| Denominator | None |
| Population | The team's players, current season; the top 8 by count, then yards |
| Time window | Current season so far |
| Inclusion rules | As M46; penalties with no player named (most delay of game, too many men) don't count |
| Benchmark | None |
| Calculation | `players[]`: group by `penalty_player_name` |
| Rounding | Whole numbers |
| Provenance | nflverse play-by-play |
| Limitations | Names are nflverse's short form ("N.Williams"): two players with the same short name on one team would be joined. Only flags with this team count. "Watchlist" suggests players to watch for misconduct ([C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages)). |
| Where it appears | `teams/<ABBR>.json` → `players[].player`, `players[].count`, `players[].yards`, `players[].types[].type`, `players[].types[].count` |
| Example | KC 2026: N.Williams 4 flags, 28 yards; L.Sneed 4, 26 (defensive holding ×2). |
| Conflicts | [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages) |

### M60. Flags on a team by crew chief

| Field | Value |
|---|---|
| Label on site | Pop-up: "Flags on KC by crew chief (2015–2026, 2+ games)"; columns "Crew chief", "Games", "KC flags/g" (with badge), "Opp flags/g", "Last worked"; footnote "Sorted by flags on KC per game, most first. Badge compares with KC's rate in <comparison>." Static `/team/<ABBR>/`: "By crew chief (since 2015)" ("Crew chief", "Games", "Flags on KC / game"), top 8. |
| Kind | Exposure rate (two) |
| Numerator | The team's penalties / its opponents' penalties, in games that crew chief worked |
| Denominator | Those games |
| Population | Every crew chief (active or not) with **at least 2** of the team's regular-season games |
| Time window | Every season from 2015, the current one included |
| Inclusion rules | As M46; crew chief from the merged assignment (officials feed, then the schedule's `referee`, then the saved assignments), as M1 |
| Benchmark | The team's own rate in the selected comparison (badge) |
| Calculation | `crews[]`: group the team's games by crew chief; `lastSeason` = the last season that crew chief worked one of the team's games |
| Rounding | Stored 2 decimals → shown 1 |
| Provenance | nflverse officials and schedules, Football Zebras assignments |
| Limitations | **Small samples, most first:** 175 of the 847 rows across all teams have 2 or 3 games, and the badge is only dimmed (under 4 games) with no label. The static page lists the top 8 by rate, so it leads with the smallest samples: LV's first row is Terry McAulay, 14.3 in 3 games ([C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways)). The window (2015–2026, current season in) differs from the badge's comparison. A crew chief's games with a team reflect that team's seasons, not only the crew. |
| Where it appears | `teams/<ABBR>.json` → `crews[].name`, `crews[].games`, `crews[].perGame`, `crews[].opponentPerGame`, `crews[].lastSeason`, `crews[].slug` (link to the crew pop-up) |
| Example | KC with Jerome Boger: 6 games, 8.83 KC flags and 7.00 opponent flags per game, last 2021. LV with Gene Steratore: 2 games, 10.0. Recomputed, a match. |
| Conflicts | [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways) |

### M61. By opponent (head to head)

| Field | Value |
|---|---|
| Label on site | Pop-up: "By opponent (2015–2026, every regular-season meeting)"; columns "Opponent" (seasons met), "Games", "KC flags/g" ("<n> total"), "Opp flags/g", "Net" (green when positive), "Last met" ("2025 Wk 3 · away · W 22-9 · 8–7 flags"); top 10, "Show all 31 opponents"; footnote "… Net = opponent's flags minus KC's per game (green: KC came out ahead). Few meetings = small samples." |
| Kind | Exposure rate (two), derived net; last meeting raw counts |
| Numerator | The team's / the opponent's penalties in their meetings |
| Denominator | Their meetings |
| Population | Every regular-season meeting from 2015, current season included |
| Time window | 2015 to now |
| Inclusion rules | As M46 |
| Benchmark | None |
| Calculation | `opponents[]`, sorted by `flagsPerGame`, then games |
| Rounding | Stored 2 decimals (yards 1) → shown 1 |
| Provenance | As M46 |
| Limitations | 56 of the 992 rows rest on 2 meetings; the footnote names small samples but no row is marked ([C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways)). "Came out ahead" and green for a net of flags read as a result ([C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages)). Yards and home-game counts aren't displayed. |
| Where it appears | `teams/<ABBR>.json` → `opponents[].opponent`, `opponents[].games`, `opponents[].seasons[]`, `opponents[].flagsPerGame`, `opponents[].oppFlagsPerGame`, `opponents[].netPerGame`, `opponents[].totalFlags`, `opponents[].lastMet.season`, `opponents[].lastMet.week`, `opponents[].lastMet.home`, `opponents[].lastMet.result`, `opponents[].lastMet.score`, `opponents[].lastMet.flags`, `opponents[].lastMet.oppFlags`; not displayed: `opponents[].yardsPerGame`, `opponents[].oppYardsPerGame`, `opponents[].totalOppFlags`, `opponents[].homeGames` |
| Example | KC vs NYG: 3 games (2017, 2021, 2025), 9.67 KC flags and 7.33 NYG flags per game, net −2.33. LV vs DAL: 3 games, 11.33. Recomputed, a match. |
| Conflicts | [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways), [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages) |

### M62. Team game log, record and next game

| Field | Value |
|---|---|
| Label on site | Pop-up: "2026 game log" ("Week", "Opponent", "Result", "KC flags" with yards, "Opp flags", "Crew"); subtitle "<division> · 2026 record 5-1 · Next: @ DEN, Wk 8"; button "Preview next game: @ DEN →" (when a preview exists). Cards: "<record> · <n> games". Static `/team/<ABBR>/`: "Game log" ("Week", "Opponent", "Result", "Flags on KC", "Flags on opponent"); "TEAM PROFILE · <division>". |
| Kind | Raw counts per game; record is a count of results |
| Numerator | The team's and the opponent's penalties (and the team's yards) in each game |
| Denominator | None |
| Population | The team's regular-season games this season, newest first |
| Time window | Current season so far |
| Inclusion rules | As M46 |
| Benchmark | None |
| Calculation | `games[]`; `record` = wins-losses(-ties) from the scores; `nextGame` = the team's first unplayed regular-season game |
| Rounding | Whole numbers |
| Provenance | nflverse schedules (scores, dates), play-by-play, crew assignment as M60 |
| Limitations | Record counts regular-season games with play-by-play only. |
| Where it appears | `teams/index.json` → `divisions[].name`, `divisions[].teams[].abbr`, `divisions[].teams[].name`, `divisions[].teams[].logo`, `divisions[].teams[].record`, `season`, `generatedAt` (not displayed). `teams/<ABBR>.json` → `abbr`, `name`, `logo`, `division`, `season`, `record`, `games[].week`, `games[].opponent`, `games[].home`, `games[].result`, `games[].score`, `games[].flags`, `games[].yards`, `games[].opponentFlags`, `games[].crew`, `nextGame.opponent`, `nextGame.home`, `nextGame.week`, `nextGame.gameId` (finds the preview); not displayed: `games[].gameId`, `games[].date`, `nextGame.date` |
| Example | KC Week 7 at SEA: L 3-20, 2 KC flags (15 yards), 4 SEA flags, John Hussey. Record 5-1. |
| Conflicts | None |

### M63. Team penalties per game, by season (chart and history)

| Field | Value |
|---|---|
| Label on site | Pop-up chart: "Penalties per game by season (regular season)", bars per season (this season in yellow), dashed line "<comparison short> rate"; tooltip "6.8/g · 60 yds/g · rank #22 · 6 games" |
| Kind | Exposure rate, one per season |
| Numerator / Denominator | As M46, for one season |
| Population | As M46 |
| Time window | Each season from 2015, the current one included |
| Inclusion rules | As M46 |
| Benchmark | The selected comparison's rate (dashed line) |
| Calculation | `history[]` from `block()` per season, with `rank_of` (M54) |
| Rounding | Stored 2 decimals (yards 1) → tooltip 1 decimal per game, whole yards |
| Provenance | As M46 |
| Limitations | The current season's bar rests on 6 or 7 games beside full seasons; the games count is only in the tooltip. Chronological, like M31 (the design rule's "most penalties first" is for rankings). Drawn per game isn't displayed. |
| Where it appears | `teams/<ABBR>.json` → `history[].season`, `history[].games`, `history[].perGame`, `history[].yardsPerGame`, `history[].rank`; not displayed: `history[].drawnPerGame` |
| Example | LV 2016 (Oakland): 9.19 per game, 16 games, rank #1. Recomputed, a match. |
| Conflicts | [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways) |

## The Big Picture (trends)

Session 5. **Examples are from `53e0bd1`** (2026-10-29: 2026 regular season
through Week 7). Places covered: the "The Big Picture" section (04: "Penalties
Per Game By Season", "Penalties Per Game By Quarter" with its penalty-type
menu, "Penalties Per Game By Week Of Season", "Share Of All Flags By Penalty
Type", "Which calls are rising?"), their `?` explainers, the static `/trends/`
page, the guide's trend questions, and `flags_by_season.csv`,
`flags_by_week.csv` and `penalty_types_by_season.csv`. Also in section 04 but
covered elsewhere: "Crew Chief Flag Rates" (M35), "Crew Chief Style Map"
(M37–M44), What Flags Cost (M89–M97).

**Two files.**
- **`type_trends.json`** (`scripts/type_trends.py` `build_type_trends()`)
  feeds every chart and table in this section, the static page, the guide and
  the CSVs. **Regular season only**; penalties as counted (Terms) that name a
  `penalty_team` (none left out in any season); every game with play-by-play,
  including games with no penalty.
- **`trends.json`** (`scripts/update_data.py` `calculate_league_trends()`)
  is not read by any chart. The pipeline computes it first and builds four
  insight cards from it (M16, M20, M21, M22); the page reads it only in a
  fallback, when `insights.json` is empty. **Regular season and playoffs**;
  games are those with at least one penalty. `byQuarterAndType` is read by
  nothing. See "Published but not displayed" in the conflicts file.
- **Paths:** as in Teams (`file` → `path`, braces list alternatives).
  `<scope>` is `current` (this season) or `all` ("Since 2015", this season
  included); `<key>` is a comparison (`sameWeeks`, `lastSeason`,
  `allPrior`); `<type>` is a penalty type.

**Spot checks** (separate code, from nflverse play-by-play and schedules):
season rates for 2016, 2025 and 2026 (full season, Weeks 1–7, games); 2026
Week 3 and its 2015–25 average and range; quarter rates for both scopes,
total and offensive holding; type shares (total, count, share, per game, "All
other"); one "rising" row in four windows and 2016; `trends.json` 2025 and a
quarter count. **42 of 42 match.** The explainers' claims hold at
`53e0bd1`: the second quarter has the most flags in all 11 past seasons;
Weeks 17 and 18 are the lowest weeks; Weeks 1–4 beat Weeks 15–18 in every
season from 2015 (2024 closest: 13.2 vs 13.0).

### M64. Penalties per game by season (full season and the same early weeks)

| Field | Value |
|---|---|
| Label on site | Chart "Penalties Per Game By Season": gray bars "Full season", yellow bars "Weeks 1–7"; subtitle "Regular season. 2026 is only 7 weeks in, so compare the yellow bars: every season's Weeks 1–7. Gray bars are full seasons. Axis starts at zero."; tooltip "Full season: 12.72 flags/game (272 games)", "Weeks 1–7: 14.21 flags/game (108 games)". Static `/trends/`: table "Penalties per game by season" ("Season", "Games", "Full season / game", "Weeks 1–7 / game"). |
| Kind | Exposure rate, one per season (two windows) |
| Numerator | Penalties by both teams in the games (as M1) |
| Denominator | Games |
| Population | League, regular season, overtime included |
| Time window | **Full season:** every regular-season game; shown for complete seasons only (the current one is a dash). **Weeks 1–N:** Weeks 1 to the league's last completed week (N = 7), every season including the current one; a partial week's games are left out (unlike M1's current-season rate, [C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison)). |
| Inclusion rules | As in Terms |
| Benchmark | Each other: every season over the same weeks |
| Calculation | Mean flags per game. `seasonCompare[]` (`fullSeason`, `early`, `games`, `earlyGames`, `complete` = season before the current one). |
| Rounding | Stored 2 decimals → bars 1 decimal, tooltip 2, static table 1; CSV 2 |
| Provenance | nflverse play-by-play and schedules. Every data run. |
| Limitations | **A second by-season rate with different rules:** `trends.json` → `bySeason` (M20's card) includes playoffs and counts only games with a penalty: 2025 is 12.5 there (3,559 in 285 games, 13 of them playoffs) and 12.72 here (3,461 in 272) ([C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season)). The CSV's `games` is the full-season count; the early-weeks sample (`earlyGames`) isn't in the CSV. Seasons before 2021 had 17 weeks, after it 18. Chronological, like M31. |
| Where it appears | `type_trends.json` → `seasonCompare[].season`, `seasonCompare[].games`, `seasonCompare[].fullSeason`, `seasonCompare[].early`, `seasonCompare[].earlyGames`, `seasonCompare[].complete`, `throughWeek` (chart, static table). `flags_by_season.csv` → `season`, `games`, `flags_per_game_full_season` (blank for the current season), `flags_per_game_same_early_weeks`. |
| Example | 2025: 12.72 full season (272 games), 14.21 in Weeks 1–7 (108); 2026: 14.67 (107); 2016: 13.42 and 13.92. Recomputed, a match. |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison) |

### M65. Penalties per game by week of season

| Field | Value |
|---|---|
| Label on site | Chart "Penalties Per Game By Week Of Season": yellow line "2026"; white line "2015–25 average"; shaded band "Range" (tooltip "Past seasons ranged 10.5–15.6"); season buttons for each past season, "All seasons" / "Clear seasons"; axes "Week of the season", "Flags per game"; tooltip "<series>: 14.8 flags per game"; note "Week <n> is added once all of its games are played (<n> played so far)". |
| Kind | Exposure rate, one per week and season; the average and range are derived |
| Numerator | Penalties by both teams in that week's games |
| Denominator | That week's games |
| Population | League, regular season |
| Time window | Each week of each season from 2015. **Average and range:** every season before the current one (2015–25). The current season's line shows complete weeks only. |
| Inclusion rules | As in Terms |
| Benchmark | The 2015–25 average and range for the same week |
| Calculation | `weekly.seasons[].weeks[]` (`perGame`, `games`, `complete` = all scheduled games played); `weekly.priorAverage[]` = games-weighted mean over 2015–25 for that week; `weekly.priorRange[]` = the lowest and highest season's rate for that week; `weekly.priorLabel`. |
| Rounding | Stored 2 decimals → tooltip 1 decimal; CSV 2 |
| Provenance | As M64 |
| Limitations | Week 18 exists only from 2021: its average and range rest on 5 seasons (80 games), Weeks 1–17 on 11. The CSV lists every week with its games count, but not whether the week is complete (the chart hides incomplete ones). No games count on the chart. |
| Where it appears | `type_trends.json` → `weekly.seasons[].season`, `weekly.seasons[].weeks[].week`, `weekly.seasons[].weeks[].perGame`, `weekly.seasons[].weeks[].games` (note), `weekly.seasons[].weeks[].complete`, `weekly.priorAverage[].week`, `weekly.priorAverage[].perGame`, `weekly.priorRange[].week`, `weekly.priorRange[].low`, `weekly.priorRange[].high`, `weekly.priorLabel`; not displayed: `weekly.priorAverage[].games`. `flags_by_week.csv` → `season`, `week`, `games`, `flags_per_game` (199 rows). |
| Example | 2026 Week 3: 14.81 (16 games); 2015–25 Week 3 average 13.38, range 10.50–15.62. Recomputed, a match. |
| Conflicts | [C20](audits/metric-conflicts-2026-10-28.md#c20-averages-of-averages-in-the-week-of-season-text) |

### M66. Early vs late season, and this season vs "the usual" (week-of-season text)

| Field | Value |
|---|---|
| Label on site | Week chart takeaway: "Flags usually **fade as the season goes on** (Weeks 15–18 average about 19% fewer than Weeks 1–4). Through Week 7, 2026 is averaging **14.7** per game, **11% above** the usual 13.3 for those weeks." Static `/trends/` summary: "Flags usually fade as the season goes on: Weeks 15–18 average 19% fewer than Weeks 1–4." Guide: "Do refs call more penalties early in the season?" → "Usually. Since 2015, Weeks 1–4 average 13.5 flags per game and Weeks 15–18 average 11.0. The last two weeks are lowest of all…". |
| Kind | Derived: averages of M65's weekly rates, and their relative difference |
| Numerator | Fade: mean of the Weeks 15–18 averages. This season: the current season's flags in its complete weeks. |
| Denominator | Fade: mean of the Weeks 1–4 averages. This season: the 2015–25 averages for the same weeks. |
| Population | League, regular season |
| Time window | 2015–25 (the weekly averages); the current season's complete weeks |
| Inclusion rules | As in Terms |
| Benchmark | Weeks 1–4; the usual for the same weeks |
| Calculation | `app.js` `renderWeekChart()` and `build_static.py` (`trends_page()`, `guide_page()`): **plain means of the weekly averages** (each week counts once, whatever its games); this season's figure is games-weighted. |
| Rounding | Percent whole; rates 1 decimal |
| Provenance | Computed from `type_trends.json` → `weekly` |
| Limitations | **Averages of averages** ([C20](audits/metric-conflicts-2026-10-28.md#c20-averages-of-averages-in-the-week-of-season-text)): Week 18 (5 seasons) counts as much as Week 15 (11 seasons). Games-weighted, Weeks 15–18 average 11.31 and the fade is 16.5%, not 19%. The fade's percentage is shown without the two rates on the chart and the static page (the guide shows them, without the percentage). The causes given ("resting starters and games with nothing at stake") aren't measured ([C19](audits/metric-conflicts-2026-10-28.md#c19-trend-text-fixed-answers-and-stated-causes)). "Since 2015" in the guide means 2015–25. |
| Where it appears | `type_trends.json` → `weekly.priorAverage[].week`, `weekly.priorAverage[].perGame`, `weekly.seasons[].weeks[].perGame`, `weekly.seasons[].weeks[].games`, `weekly.seasons[].weeks[].complete` |
| Example | Weeks 1–4: 13.55; Weeks 15–18: 11.02 (plain mean) → 18.7% fewer, shown "about 19%". 2026 Weeks 1–7: 14.67 vs 13.27 → +10.6%, shown "11% above the usual 13.3". |
| Conflicts | [C19](audits/metric-conflicts-2026-10-28.md#c19-trend-text-fixed-answers-and-stated-causes), [C20](audits/metric-conflicts-2026-10-28.md#c20-averages-of-averages-in-the-week-of-season-text) |

### M67. Penalties per game by quarter (league)

| Field | Value |
|---|---|
| Label on site | Chart "Penalties Per Game By Quarter": buttons "2026 season" / "Since 2015"; type menu ("All penalties" plus 8 types); subtitle "Accepted penalties per game in each quarter, regular season (2026 season, 107 games, overtime excluded). Busiest: **Q2**. The second quarter usually leads, partly because the two-minute drill packs in extra plays."; bars labeled to 2 decimals, the busiest in yellow. Static `/trends/`: "Since 2015, flags per game by quarter: Q1 2.65, Q2 3.69, Q3 2.98, Q4 3.28. The second quarter usually leads…". |
| Kind | Exposure rate, one per quarter (all penalties or one type) |
| Numerator | Penalties in quarter 1, 2, 3 or 4 (`qtr`), all or one `penalty_type` |
| Denominator | Games in the scope |
| Population | League, regular season, **overtime left out** |
| Time window | `current`: this season so far. `all`: **every season from 2015, this season included** ("Since 2015"). |
| Inclusion rules | As in Terms |
| Benchmark | None (the busiest quarter is highlighted) |
| Calculation | `quarters.<scope>.total[]` (4 values), `quarters.<scope>.types.<type>[]` for the scope's 8 most common types, `quarters.<scope>.games`. |
| Rounding | Stored 2 decimals → shown 2 decimals (default: 1) |
| Provenance | As M64 |
| Limitations | **Still displayed, from `type_trends.json`:** the chart and its type menu read `quarters`. The older `trends.json` → `byQuarter` (counts, playoffs included) feeds only M22's card inside the pipeline; `trends.json` → `byQuarterAndType` (shares by quarter for 6 types) is read by nothing. The menu's types differ by scope (the scope's own top 8). "Since 2015" includes 2026, unlike "All seasons (2015–25)" in M69 ([C8](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names)). The two-minute-drill reason isn't measured ([C19](audits/metric-conflicts-2026-10-28.md#c19-trend-text-fixed-answers-and-stated-causes)). |
| Where it appears | `type_trends.json` → `quarters.<scope>.total[]`, `quarters.<scope>.types.<type>[]`, `quarters.<scope>.games`, `scopeLabels.<scope>`. Not displayed: `trends.json` → `byQuarterAndType.quarters[]`, `byQuarterAndType.types[]`, `byQuarterAndType.data.<type>[]`. |
| Example | 2026: Q1 3.16, Q2 4.24, Q4 3.76 (107 games); since 2015: Q1 2.65, Q2 3.69, Q4 3.28 (3,002 games). Offensive holding, Q2: 1.00 (2026), 0.70 (since 2015). Recomputed, a match. |
| Conflicts | [C8](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names), [C19](audits/metric-conflicts-2026-10-28.md#c19-trend-text-fixed-answers-and-stated-causes) |

### M68. Share of all flags by penalty type

| Field | Value |
|---|---|
| Label on site | Chart "Share Of All Flags By Penalty Type": buttons "2026 season" / "Since 2015"; subtitle "What share of all accepted penalties each call makes up, regular season (1,570 flags in 107 games, 14.7 per game). The top two calls alone are 40% of every flag."; bars "22.2%" and "3.25/g" (per game hidden on phones); "All other (38 types)"; axis "% of all flags"; tooltip "348 flags · 22.2% of all". |
| Kind | Raw count and share (derived); per game is an exposure rate |
| Numerator | Penalties of the type |
| Denominator | All penalties in the scope (share); games in the scope (per game) |
| Population | League, regular season |
| Time window | As M67 (`current`, `all` = 2015 to now) |
| Inclusion rules | As in Terms |
| Benchmark | None |
| Calculation | `typeShare.<scope>`: the 10 most common types, then one "All other" row (`other: true`, drawn darker); `total`, `games`, `perGame` for the scope |
| Rounding | Share stored and shown to 1 decimal (default: whole numbers from 10%); per game 2 decimals |
| Provenance | As M64 |
| Limitations | **Same idea as M16's "Most Common Call" card on a different population:** the card is "Holding", 20% (playoffs in, 2015–2026); since 2015 here, offensive holding is 19.7% (regular season) ([C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season)). The code comment says "since 2020"; the chart uses 2015 onward (comment only). |
| Where it appears | `type_trends.json` → `typeShare.<scope>.types[].type`, `typeShare.<scope>.types[].count`, `typeShare.<scope>.types[].pct`, `typeShare.<scope>.types[].perGame`, `typeShare.<scope>.types[].other`, `typeShare.<scope>.total`, `typeShare.<scope>.games`, `typeShare.<scope>.perGame`, `scopeLabels.<scope>` |
| Example | 2026: offensive holding 348 of 1,570 = 22.2%, 3.25 per game; false start 17.5%. Since 2015: 7,481 of 38,028 = 19.7%. Recomputed, a match. |
| Conflicts | [C1](audits/metric-conflicts-2026-10-28.md#c1-two-meanings-of-season), [C8](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names) |

### M69. "Which calls are rising?" (league penalty-type trends)

| Field | Value |
|---|---|
| Label on site | Table "Which calls are rising?": subtitle "2026 accepted penalties per game vs 2025 through week 7, all teams · biggest increases first"; buttons "2025 thru Wk 7", "All of 2025", "All seasons (2015–25)"; columns "Penalty" ("<n> this season"), "2026 / game", "<comparison> / game", "Change" (absolute and badge), "Since 2015 ▾" (trend line); footnote "Regular season. Accepted penalties per game, all teams combined. Trend line: each season since 2015 … 2026 is 107 games in, so rare penalties can swing." Static `/trends/`: "Which penalties are increasing?" ("Penalty", "2026 / game", "2025 Wk 1–7 / game", "Change"); summary "The biggest increases vs 2025 through Week 7: …". Guide: "Are NFL penalties up in 2026?" ("The biggest increases are in …"). |
| Kind | Exposure rate per type and window; Change is derived (difference) |
| Numerator | Penalties of the type |
| Denominator | Games in the window |
| Population | League, regular season |
| Time window | Current season so far (partial week included) vs `sameWeeks` (previous season, Weeks 1 to the league's last completed week), `lastSeason`, or `allPrior` (2015–25). Trend line: every season from 2015, current included. |
| Inclusion rules | As in Terms |
| Benchmark | The selected comparison |
| Calculation | Types: the 18 most common over all seasons plus this season's top 8. `types[]` sorted by `current − compare.<key>`. |
| Rounding | Stored 2 decimals → shown 2 |
| Provenance | As M64 |
| Limitations | Shows the absolute change and the baseline beside the percentage (rule 3 met). Same-weeks follows the league's week, not a partial one ([C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison)). The CSV gives per game by season with no games count, and its current season is partial. Same idea as the team version (M58). |
| Where it appears | `type_trends.json` → `types[].type`, `types[].current`, `types[].currentCount`, `types[].compare.<key>`, `types[].bySeason[].season`, `types[].bySeason[].perGame`. `penalty_types_by_season.csv` → `penalty_type`, `season`, `per_game` (216 rows). |
| Example | Offensive holding: 3.25 in 2026 (348), 2.80 in 2025 Weeks 1–7, 2.47 all of 2025, 2.46 in 2015–25, 2.74 in 2016. Top three rising vs same weeks: offensive holding (+0.45), delay of game (+0.25), neutral zone infraction (+0.15). Recomputed, a match. |
| Conflicts | [C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison), [C8](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names) |

### M70. League trends: windows, labels and samples

| Field | Value |
|---|---|
| Label on site | Comparison buttons and short labels (M69); scope buttons "2026 season" / "Since 2015" (M67, M68); "2026 is 107 games in" (footnote); "Regular season. Accepted penalties per game, all teams combined." |
| Kind | Definitions of the windows (no number of their own) |
| Numerator / Denominator | — |
| Population | League, regular season |
| Time window | `throughWeek` = the league's last completed week (`scripts/weeks.py` `completed_week()`); `currentGames` = every current-season game so far |
| Inclusion rules | — |
| Benchmark | — |
| Calculation | `build_type_trends()`: `comparisons[]` (`key`, `label`, `short`, `games`), `defaultComparison` (`sameWeeks`), `scopeLabels`, `notes`, `season`, `generatedAt` |
| Rounding | — |
| Provenance | As M64 |
| Limitations | Two "all" windows in one section: "Since 2015" (2015–2026) for the charts and "All seasons (2015–25)" for the table ([C8](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names)). Each comparison's games count is stored but not shown. |
| Where it appears | `type_trends.json` → `comparisons[].key`, `comparisons[].label`, `comparisons[].short`, `defaultComparison`, `scopeLabels.<scope>`, `notes`, `currentGames`, `season`, `throughWeek`; not displayed: `comparisons[].games`, `generatedAt` |
| Example | Comparisons: 2025 through Week 7 (108 games), all of 2025 (272), 2015–25 (2,895). |
| Conflicts | [C8](audits/metric-conflicts-2026-10-28.md#c8-all-seasons-and-since-2015-two-windows-similar-names) |

## Game previews

Session 6. **Examples are from `53e0bd1`** (2026-10-29: Week 8 previews, 14
games, every crew chief assigned). Places covered: "Game Previews" (section
03: title, subtitle, crew note, cards, credit line), the preview pop-up, the
"How projections work" explainer, the static `/assignments/` page's
"Projected flags", the home page source's pre-filled previews list, and the
guide's "How projections work". The cards' "Track record" and the scorecard
pop-up are session 7; the gameday worker's and the social images' use of
`previews/latest.json` are session 8 (worker) or outside the site (social).

**One source, two kinds of number.** `scripts/previews.py`
`build_previews()` writes `previews/latest.json` (which weeks to show) and
one file per week, `previews/<season>-week-NN.json`.
- **Model estimates** (M71–M76): projected flags, the likely range, the
  chance of N+ flags, projected yards and quarters, the league level, the
  drivers and the crew effect. Model `v1.0`.
- **Observed numbers** (M77–M79): team discipline, recent meetings, game
  context averages. The team numbers are the team pages' numbers (M46–M54):
  equal for all 28 Week 8 teams, 224 of 224 values.
- **Old week files** (Weeks 4–7) stay published; the page reads only the
  weeks in `latest.json`. `scripts/scorecard.py` reads them (session 7).
- **Paths:** `previews/<week>` stands for every week file. Braces as in Teams;
  `teams.{home,away}` means both sides.

**The model, once** (`build_previews()`, module notes):
- **League level:** flags per team-game, regular season 2024–2026, seasons
  weighted 0.3 / 0.6 / 1.0; the current season is mixed with that weighted
  level using a prior of 100 team-games; split by type (10 most common plus
  "Other") and by home and away.
- **Factors**, per type, each a ratio to the league over the same games and
  weights, shrunk toward 1.0 (team: a prior of 6 team-games; crew chief: 10
  games) and clamped to 0.5–2.0: the team's **commit** rate, the opponent's
  **draw** rate (opponents' flags in its games), and the crew chief's **call**
  rate (1.0 when the crew is TBA).
- **Projection** for each side and type = league level × team commit ×
  opponent draw × crew call. Quarters use league quarter shares, tilted by the
  crew chief's own (prior of 300 flags). Yards use the league's average yards
  per flag of each type.
- **Range and chance:** a negative binomial with the projected mean and a
  dispersion (variance ÷ mean of real game totals, 2025–26, clamped to
  1.05–3.0): the 10th and 90th percentiles, and the chance of more than the
  rounded league level.

**Spot checks** (separate code, from nflverse play-by-play, schedules,
officials and the saved assignments):
- **Observed:** team inputs vs team pages, 224 of 224 equal; one meeting
  (2025 CAR @ GB: 12 flags, 7 on GB); the four context averages (Thursday,
  Sunday, division, non-division, 2024–26).
- **Model arithmetic, rebuilt:** the league level (14.25, shown 14.3) and the
  dispersion (1.47) from play-by-play; for all 14 games, total, home, away,
  yards, quarters, drivers, the crew's overall factor and driver, the range
  and the chance of N+ from the published rows (168 of 168); every crew
  chief's games in the model (14 of 14).
- **25 of 25 checks pass.** These check the arithmetic, not whether the model
  is right: that is the scorecard's job (session 7).

### M71. Projected flags (game, home team, away team)

| Field | Value |
|---|---|
| Label on site | **Cards:** big number, "projected flags · 10–23 likely"; split bar "CAR **7.3** … **8.8** GB" (team colors); ranked "most flags first". **Pop-up:** tiles "Projected flags" (16.1), "On CAR (away)" (7.3), "On GB (home)" (8.8); "Projected penalties by type" ("Type", "On CAR", "On GB", "Total vs league", "Yards"); footnote "Projection uses 2026, 2025, 2024 regular seasons, weighted toward 2026." **Static `/assignments/`:** "Projected flags"; summary "Projected most flags: CAR @ GB with Scott Novak (16.1); …"; note "Projections are our model's expected accepted penalties for the game". **Home page source:** "projected 16.1 flags". **Guide:** "How projections work". |
| Kind | **Model estimate** |
| Numerator | Expected accepted penalties (as counted, Terms) by each team in the game |
| Denominator | One game |
| Population | One upcoming regular-season game; inputs from regular-season games 2024–2026 |
| Time window | Inputs: every game played before the data run, seasons weighted 0.3 / 0.6 / 1.0. A game's projection updates every run until kickoff (C9, session 7). |
| Inclusion rules | As in Terms, penalties naming a team |
| Benchmark | The model's league level (M73) |
| Calculation | See "The model, once" above. `projection.total` = home + away; each `byType[]` row has `home`, `away`, `total`, `leagueTotal` and the five `factors`. Games sorted by total. |
| Rounding | Total, home, away stored 1 decimal → shown 1; type rows stored 2 → shown 1; factors stored 2 |
| Provenance | nflverse play-by-play, schedules and officials; Football Zebras assignments. Every data run. |
| Limitations | **An estimate**, labeled "projected" on the cards, pop-up, static page and home page source; the static page says "our model's expected accepted penalties". Nothing says how far off projections usually are, except the separate Track record. "Crew TBA" uses a neutral crew (all crew factors 1.0). At Week 8 a team's 2024–25 games still carry about two-thirds of the weight (17 × 0.6 + 17 × 0.3 = 15.3, vs 7 × 1.0 this season), so earlier rosters still count. |
| Where it appears | `previews/<week>` → `games[].projection.total`, `games[].projection.home`, `games[].projection.away`, `games[].byType[].type`, `games[].byType[].home`, `games[].byType[].away`, `games[].byType[].total`, `games[].byType[].leagueTotal`, `model.seasons[]`, `model.version` (not displayed), `model.seasonWeights.<season>` (not displayed), `model.regularSeasonOnly` (not displayed); not displayed: `games[].byType[].factors.homeCommit`, `games[].byType[].factors.awayCommit`, `games[].byType[].factors.homeDraw`, `games[].byType[].factors.awayDraw`, `games[].byType[].factors.crew`, `games[].teams.{home,away}.gamesInModel` |
| Example | CAR @ GB: 16.1 (GB 8.8, CAR 7.3), Scott Novak. Offensive holding row: 4.00 (GB 2.38, CAR 1.61), league 2.90, crew factor 1.23. Lowest: BAL @ BUF 12.9. Arithmetic rebuilt from the rows, a match. |
| Conflicts | [C9](audits/metric-conflicts-2026-10-28.md#c9-scorecard-which-projection-is-graded), [C22](audits/metric-conflicts-2026-10-28.md#c22-model-estimates-in-previews-labels-and-attribution) |

### M72. Likely range and chance of N+ flags

| Field | Value |
|---|---|
| Label on site | Cards: "10–23 likely", range bar (one shared scale). Pop-up: "likely 10–23" under each tile; "Chance of **15+** flags": "61%", "league avg game: 14.3". Explainer: "The range covers 80% of likely outcomes, based on how much real game totals vary." Guide: "The projection includes a likely range and the chance of 15 or more flags." |
| Kind | **Model estimate** (interval and probability) |
| Numerator | — |
| Denominator | — |
| Population | As M71 |
| Time window | Dispersion from regular-season games 2025–26 |
| Inclusion rules | As M71 |
| Benchmark | Threshold = the model's league level, rounded (14 → "15+") |
| Calculation | Negative binomial with mean = the projection and variance = dispersion × mean: 10th and 90th percentiles (`range`, `homeRange`, `awayRange`); `probOver` = chance of at least threshold + 1; `overThreshold`; `model.dispersion`. |
| Rounding | Range whole flags; chance stored 3 decimals → whole percent |
| Provenance | As M71 |
| Limitations | "Likely" doesn't say 80% on the cards or pop-up (the explainer does). The range reflects game-to-game variation only, not uncertainty in the factors. **The guide's "15 or more" is fixed text:** it matches the threshold only while the league level rounds to 14 ([C19](audits/metric-conflicts-2026-10-28.md#c19-trend-text-fixed-answers-and-stated-causes)). The scorecard grades the range's hit rate against a "target ≈ 80%", but the model itself expects more than 80% inside the range (83.5% for the live projections; M83, [C23](audits/metric-conflicts-2026-10-28.md#c23-in-the-likely-range-target--80-vs-the-ranges-design)). |
| Where it appears | `previews/<week>` → `games[].projection.range[]`, `games[].projection.homeRange[]`, `games[].projection.awayRange[]`, `games[].projection.overThreshold`, `games[].projection.probOver`, `model.dispersion` (not displayed) |
| Example | CAR @ GB: 10–23 (GB 4–14, CAR 3–12); chance of 15+: 61%. Dispersion 1.47. Recomputed with separate code, a match. |
| Conflicts | [C19](audits/metric-conflicts-2026-10-28.md#c19-trend-text-fixed-answers-and-stated-causes), [C22](audits/metric-conflicts-2026-10-28.md#c22-model-estimates-in-previews-labels-and-attribution), [C23](audits/metric-conflicts-2026-10-28.md#c23-in-the-likely-range-target--80-vs-the-ranges-design) |

### M73. League level in previews ("vs league", "league avg game")

| Field | Value |
|---|---|
| Label on site | Cards: badge and "vs league 14.3". Pop-up: badge under "Projected flags"; "league avg game: 14.3"; per-type badges in "Total vs league". |
| Kind | **Model estimate** (the model's expected flags in a league-average game); the badges are derived |
| Numerator | The model's league level per type, home plus away |
| Denominator | One game |
| Population | League, regular season 2024–2026 |
| Time window | Current season mixed with the weighted 2024–26 level (prior of 100 team-games) |
| Inclusion rules | As M71 |
| Benchmark | It is the benchmark for M71 |
| Calculation | `league_game` = sum of the home and away base rates → `model.leagueAveragePerGame`, `games[].projection.leagueAverage`; `games[].projection.vsLeaguePct` = total ÷ level − 1 (unrounded). The page's badges compute the percentage again from the rounded values (`pctBadge(16.1, 14.3)`: +12.6%; stored +13.3%). |
| Rounding | Stored 1 decimal (level), 1 decimal (percent) |
| Provenance | As M71 |
| Limitations | **Labeled as the league average, but it's the model's level:** 14.25 (shown 14.3), while the observed 2026 league rate on the home page is 14.67 (M1) ([C21](audits/metric-conflicts-2026-10-28.md#c21-league-in-previews-is-the-models-level-not-the-observed-rate)). The badges show the percentage only, no absolute difference (M2). |
| Where it appears | `previews/<week>` → `model.leagueAveragePerGame`, `games[].byType[].leagueTotal`; not displayed: `games[].projection.leagueAverage`, `games[].projection.vsLeaguePct` |
| Example | Week 8: 14.3. Rebuilt from play-by-play: 14.25, a match (observed 2026: 14.67). |
| Conflicts | [C10](audits/metric-conflicts-2026-10-28.md#c10-league-average-means-three-things-on-crew-chief-pages), [C21](audits/metric-conflicts-2026-10-28.md#c21-league-in-previews-is-the-models-level-not-the-observed-rate) |

### M74. Projected penalty yards

| Field | Value |
|---|---|
| Label on site | Cards: "~133 penalty yds". Pop-up tiles: "~60 yds", "~72 yds"; type table "Yards" ("38 yds"). |
| Kind | **Model estimate** |
| Numerator | Projected flags of each type × the league's average yards per flag of that type |
| Denominator | One game |
| Population, Time window | As M71 (yards per flag: 2024–26, weighted) |
| Inclusion rules | As M71; yards as M7 |
| Benchmark | None |
| Calculation | `yards`, `homeYards`, `awayYards` = Σ type projection × `yardsEach` |
| Rounding | Whole yards |
| Provenance | As M71 |
| Limitations | Uses league yards per flag for every team and crew: a crew's or team's own yardage (M38, M53) doesn't enter. |
| Where it appears | `previews/<week>` → `games[].projection.yards`, `games[].projection.homeYards`, `games[].projection.awayYards`, `games[].byType[].yardsEach` |
| Example | CAR @ GB: 133 (GB 72, CAR 60); offensive holding 9.6 yards each. Rebuilt from the rows, a match. |
| Conflicts | [C22](audits/metric-conflicts-2026-10-28.md#c22-model-estimates-in-previews-labels-and-attribution) |

### M75. Projected flags by quarter

| Field | Value |
|---|---|
| Label on site | Pop-up: "⏱️ Quarter by quarter": stacked bars (team colors), total per quarter, "CAR 1.6 · GB 2.0", labels from `qLabel()` |
| Kind | **Model estimate** |
| Numerator | Projected flags of each type × the league's quarter shares for that type, tilted by the crew chief's quarter shares |
| Denominator | One game |
| Population, Time window | As M71; quarters 1–4 (overtime left out of the shares) |
| Inclusion rules | As M71 |
| Benchmark | None |
| Calculation | `byQuarter[]` (`home`, `away`); `crew.quarterTilt[]` = the crew chief's quarter shares ÷ the league's, with a prior of 300 flags |
| Rounding | Stored 2 decimals → shown 1 |
| Provenance | As M71 |
| Limitations | The four quarters add up to the full projection, so overtime flags are spread across regulation. The crew's tilt isn't shown. |
| Where it appears | `previews/<week>` → `games[].projection.byQuarter[].quarter`, `games[].projection.byQuarter[].home`, `games[].projection.byQuarter[].away`; not displayed: `games[].crew.quarterTilt[]` |
| Example | CAR @ GB, 2nd quarter: 4.57 (GB 2.49, CAR 2.08); Novak's tilt 1.04 / 0.96 / 1.05 / 0.97. |
| Conflicts | None |

### M76. "What's driving the projection" and the crew effect

| Field | Value |
|---|---|
| Label on site | Pop-up: "What's driving the projection": rows "Crew chief", "<home> discipline & what it draws", "<away> discipline & what it draws" with "+0.8" etc.; footnote "Extra or fewer flags vs a league-average matchup with an average crew." "The crew: <name>": tile "Crew effect on this game" "+0.8", "flags vs an average crew (6%)"; type tilts with badges ("Offensive Holding ▲ 23%"); footnote "Tilts compare how often this crew calls each type vs the league (last 3 seasons, 41 games, shrunk toward average)." |
| Kind | **Model estimate** (a split of M71 into three parts) |
| Numerator | Crew: projection with the crew factor only, minus the league level. Home: adding the home team's commit and draw factors. Away: adding the away team's. |
| Denominator | One game |
| Population, Time window | As M71; crew chief games 2024–26 |
| Inclusion rules | As M71 |
| Benchmark | A league-average matchup with an average crew |
| Calculation | `drivers[]`: L1 − L0, L2 − L1, L3 − L2 (they add up to total − league level). `crew.overallFactor` = L1 ÷ L0; `crew.typeTilts[]` = the 4 types whose crew factor is furthest from 1.0; `crew.gamesInModel`. |
| Rounding | Drivers stored 2 decimals → shown 1; factor 3 decimals → whole percent |
| Provenance | As M71 |
| Limitations | **Order matters:** the crew is applied first and each team's part is measured on top of the earlier ones, so effects that multiply (a heavy-calling crew with a team that commits that type) are credited to the later step. "Crew effect on this game" and "What's driving" read as causes; they're the model's split of its own estimate ([C22](audits/metric-conflicts-2026-10-28.md#c22-model-estimates-in-previews-labels-and-attribution)). Same crew rates as the crew style block (M41), measured differently (3 seasons, shrunk with 10 games). |
| Where it appears | `previews/<week>` → `games[].projection.drivers[].label`, `games[].projection.drivers[].value`, `games[].crew.overallFactor`, `games[].crew.typeTilts[].type`, `games[].crew.typeTilts[].factor`, `games[].crew.gamesInModel` |
| Example | CAR @ GB: crew +0.82, GB +0.09, CAR +0.99 (sum 1.90; the type rows give 16.15 − 14.26 = 1.89); Novak overall 1.057 ("6%"), 41 games. Rebuilt from the type rows, a match. |
| Conflicts | [C22](audits/metric-conflicts-2026-10-28.md#c22-model-estimates-in-previews-labels-and-attribution) |

### M77. Team discipline in previews

| Field | Value |
|---|---|
| Label on site | Pop-up: "🏈 Team discipline (2026)", one column per team: "Penalties/game" (badge vs last season, dimmed under 4 games), "Most-penalized rank" ("#1 of 32"), "Offense / Defense", "Drawn from opponents", "Penalty yds/game", "Most common", "Watchlist (2026)" (top 4, or "No individual penalties yet"). |
| Kind | Observed: exposure rates, rank, raw counts |
| Numerator / Denominator | As M46 (per game), M51 (offense / defense), M49 (drawn), M53 (yards), M54 (rank), M59 (players) |
| Population | The team's regular-season games this season |
| Time window | Current season so far; badge vs all of last season |
| Inclusion rules | As M46 |
| Benchmark | Last season's rate (badge) |
| Calculation | `discipline()` and `watchlist()` in `previews.py`: computed again from the same data as `team_pages.py`. `mostCommon` = the team's most frequent type this season. |
| Rounding | Per game 1 decimal; yards per game whole (team pages: whole in the pop-up, 1 decimal on static pages) |
| Provenance | nflverse play-by-play. Every data run. |
| Limitations | **The same numbers as the team pages** (224 of 224 equal at `53e0bd1`), calculated a second time in a second script. The badge compares with all of last season, while the team pop-up defaults to the same weeks (M48). "Team discipline" and "Watchlist" ([C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages)). |
| Where it appears | `previews/<week>` → `games[].teams.{home,away}.perGame`, `games[].teams.{home,away}.games`, `games[].teams.{home,away}.rank`, `games[].teams.{home,away}.offensePerGame`, `games[].teams.{home,away}.defensePerGame`, `games[].teams.{home,away}.drawnPerGame`, `games[].teams.{home,away}.yardsPerGame`, `games[].teams.{home,away}.lastSeasonPerGame`, `games[].teams.{home,away}.mostCommon`, `games[].teams.{home,away}.watchlist[].player`, `games[].teams.{home,away}.watchlist[].count`, `games[].teams.{home,away}.watchlist[].yards`, `games[].teams.{home,away}.watchlist[].types[].type`, `games[].teams.{home,away}.watchlist[].types[].count` |
| Example | GB: 9.29 per game (7 games), #1, 5.00 / 4.29, drawn 6.43, 78 yards, last season 6.18; equal to `teams/GB.json`. |
| Conflicts | [C7](audits/metric-conflicts-2026-10-28.md#c7-the-home-summary-line-compares-with-all-of-last-season), [C18](audits/metric-conflicts-2026-10-28.md#c18-wording-and-framing-section-17-on-team-pages) |

### M78. Recent meetings (preview head to head)

| Field | Value |
|---|---|
| Label on site | Pop-up: "Recent meetings": "CAR @ GB", score, "2025 Wk 9 · Land Clark", flags "12", "CAR 5 · GB 7" |
| Kind | Raw counts |
| Numerator | Flags in each meeting: all, and on each team |
| Denominator | None |
| Population | The last 3 regular-season meetings of the two teams with play-by-play, any season |
| Time window | Every season from 2015 |
| Inclusion rules | As in Terms; the total counts every penalty play, including any with no team named |
| Benchmark | None |
| Calculation | `head_to_head()` |
| Rounding | Whole numbers |
| Provenance | nflverse schedules and play-by-play; crew from the merged assignment |
| Limitations | A different table from the team pop-up's "By opponent" (M61: every meeting, per game). No small-sample note. |
| Where it appears | `previews/<week>` → `games[].headToHead[].away`, `games[].headToHead[].home`, `games[].headToHead[].awayScore`, `games[].headToHead[].homeScore`, `games[].headToHead[].season`, `games[].headToHead[].week`, `games[].headToHead[].crew`, `games[].headToHead[].flags`, `games[].headToHead[].awayFlags`, `games[].headToHead[].homeFlags`; not displayed: `games[].headToHead[].gameId` |
| Example | 2025 Week 9 CAR @ GB, 16–13: 12 flags (GB 7, CAR 5), Land Clark. Recomputed, a match. |
| Conflicts | None |

### M79. Game context and its reference averages

| Field | Value |
|---|---|
| Label on site | Pop-up "Context" chips: "Primetime", "Thursday night (avg 13.4 flags vs 13.1 Sunday)", "Division game (avg 12.9 vs 13.2)", "Neutral site", "Roof: outdoors", "Surface: grass", "Rest: CAR 4d · GB 4d", "Spread: GB −3.5" (and "(expected close — late flags tend to drop)" when within 3), "O/U 47.5", "<temp>°F", "Wind <n> mph", "QBs: …"; footnote "Shown for reference; not added into the projection." |
| Kind | Observed: game facts; the averages are exposure rates |
| Numerator | Averages: flags by both teams in the games of that kind |
| Denominator | Games of that kind |
| Population | Regular-season games 2024–2026 with play-by-play |
| Time window | 2024 to now (unweighted) |
| Inclusion rules | Penalties naming a team |
| Benchmark | Thursday vs Sunday; division vs non-division |
| Calculation | `contextReference` (`ctx_avg()`); context fields from the nflverse schedule (`spread_line`, `total_line`, `roof`, `surface`, `temp`, `wind`, rest, QBs, coaches, stadium) |
| Rounding | Averages 1 decimal |
| Provenance | nflverse schedules (betting lines as published there) and play-by-play |
| Limitations | **The averages show no window or sample** (Thursday: 47 games; Sunday 535; division 225; non-division 426; [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways)). "Late flags tend to drop" in close games isn't measured here ([C19](audits/metric-conflicts-2026-10-28.md#c19-trend-text-fixed-answers-and-stated-causes)). Thursday includes every Thursday game, not only Thursday night. |
| Where it appears | `previews/<week>` → `contextReference.thursday`, `contextReference.sunday`, `contextReference.division`, `contextReference.nonDivision`, `games[].context.primetime`, `games[].context.divisionGame`, `games[].context.neutralSite`, `games[].context.roof`, `games[].context.surface`, `games[].context.homeRest`, `games[].context.awayRest`, `games[].context.spread`, `games[].context.total`, `games[].context.temp`, `games[].context.wind`, `games[].context.homeQB`, `games[].context.awayQB`; not displayed: `games[].context.stadium`, `games[].context.homeCoach`, `games[].context.awayCoach` |
| Example | Thursday 13.4 (47 games) vs Sunday 13.1 (535); division 12.9 vs 13.2. Recomputed, a match. |
| Conflicts | [C17](audits/metric-conflicts-2026-10-28.md#c17-small-samples-handled-four-ways), [C19](audits/metric-conflicts-2026-10-28.md#c19-trend-text-fixed-answers-and-stated-causes) |

### M80. Preview weeks, games and crew assignments

| Field | Value |
|---|---|
| Label on site | Title "Week 8 Previews" (or "Week 7 Finale & Week 8 Previews"); groups "Week 8 · 14 games", "Week 7 · Tonight / Remaining"; subtitle "Projected penalties for every upcoming game, ranked most flags first. All crews assigned." (or "Week 8 crews assigned for <n> of <n> games." / "Week 8 crew assignments usually post Tuesday — projections update automatically."); card header (teams, logos, "home", "Today", "Thu · Oct 29 · 8:15 PM ET · Prime"); "Crew: <name>" / "Crew TBA"; credit "Crew assignments via Football Zebras." Static `/assignments/`: "14 of 14 Week 8 games have a crew chief assigned", columns "Game", "Date", "TV", "Crew chief", "Crew 2026 flags / game" (M1), "Crew career style" (M44). |
| Kind | Raw counts (games, games with a crew assigned) and game facts |
| Numerator | Games with a crew chief assigned |
| Denominator | Games in the week (or those still to play) |
| Population | Upcoming regular-season games |
| Time window | The first week with games still to play (US Eastern dates), plus the next week when the first is part-played |
| Inclusion rules | — |
| Benchmark | — |
| Calculation | `build_previews()` target weeks; `assignments` from `frontend/data/assignments/<season>-week-NN.json` (M45) |
| Rounding | — |
| Provenance | nflverse schedules; Football Zebras |
| Limitations | The static page uses the first week file only. Old week files stay published (see the section notes). |
| Where it appears | `previews/latest.json` → `season`, `week`, `file`, `weeks[].week`, `weeks[].file`, `weeks[].remainingOnly`, `weeks[].games`, `generatedAt` (not displayed). `previews/<week>` → `season`, `week`, `file`, `remainingOnly`, `assignments.assigned`, `assignments.games`, `assignments.source.url`, `games[].gameId`, `games[].season`, `games[].week`, `games[].gameday`, `games[].gametime`, `games[].weekday`, `games[].network`, `games[].homeTeam.abbr`, `games[].homeTeam.name`, `games[].homeTeam.logo`, `games[].awayTeam.abbr`, `games[].awayTeam.name`, `games[].awayTeam.logo`, `games[].crew.name`, `games[].crew.slug` (link); not displayed: `assignments.source.name`, `assignments.source.published`, `generatedAt` |
| Example | Week 8: 14 games, 14 assigned (Football Zebras, posted Tue 27 Oct 2026 16:19 UTC). |
| Conflicts | None |

## Scorecard and history

Session 7. **Examples are from `53e0bd1`** (2026-10-29: 44 live projections
graded, Weeks 4–7 of 2026; history ledger from 2025 Week 1 to 2026 Week 7).
Places covered: the "Track record" box under the previews, the "Track
Record" pop-up ("See every game"), its "Week by week" history block, and
the guide's "How accurate are the penalty projections?". The live strip's use
of `history/index.json` is session 8.

**Three files on the page, three folders behind them.**
- **`scorecard/public.json`** (`scripts/scorecard.py` `grade()`): the
  graded summaries and every graded live projection.
- **`history/index.json`** and **`history/games/<season>-week-NN.json`**
  (`scripts/history.py` `build_history()`): one file per completed week, each
  game's prediction, outcome and grade, written once and kept.
- **Not read by any page** (they're what the two above are built from):
  `scorecard/live/` (the frozen projections), `scorecard/backtest/` (the
  rebuilt ones) and `history/snapshots/` (the league as it stood after each
  week). See P5–P7 in the conflicts file.
- **Actual flags** everywhere here are penalties as counted (Terms) that name
  a team, regular season, overtime included in the totals.
- **Paths:** `history/<week>` stands for every history week file; `<type>`
  is a penalty type.

**Three sources of a graded projection** (M81): `live` (saved by the
pipeline before kickoff), `live-post` (a projection posted on social media
before kickoff, imported when the pipeline hadn't saved that game: 2 games)
and `backtest` (rebuilt afterward from earlier games only).

**Checks** (separate code, from nflverse play-by-play and git history):
- **Backtest uses earlier games only:** five weeks (2025 Weeks 1, 10, 18;
  2026 Weeks 3, 7) rebuilt from data cut off before each week equal the
  full-data rebuild and the stored files in 76 of 76 games. The 336 backtest
  records without a model version are reproduced exactly by today's model.
- **Outcomes:** every 2026 Week 7 game's flags, yards, quarters (overtime
  included), totals and types per team: 56 of 56 equal.
- **Summaries rebuilt:** the live summary (44 games: average miss, in range,
  within ±3, guess miss, skill), live Week 5, the 2025 backtest (272 games),
  and the 2026 Week 7 history summary with its index row. **22 of 22 match.**
- **Timing (C9):** no change after kickoff in 100 commits; every final live
  record equals the last preview committed before kickoff (56 of 56).
- **The range's own expected coverage:** 83.5% for the 56 live projections
  (see M83).

### M81. Graded projection sources: live, posted, backtest

| Field | Value |
|---|---|
| Label on site | Track record rows: "Published before kickoff" ("<n> games graded so far"), "2025 full season (backtest)", "2026 so far (backtest)". Pop-up blocks with the same titles; "Projections exactly as they appeared on the site before each game. Grows every week."; "Rebuilt afterward, game by game, using only data that existed before each week. Shows how the model would have done."; "How it's graded": the definitions joined. History: "published" tag on live rows; "This week predates live tracking: projections were reconstructed afterward…" (only when every game of the week is backtest); footnote "Games marked "published" were projected live before kickoff; the rest were reconstructed." |
| Kind | Definitions (which projection is graded) |
| Numerator / Denominator | — |
| Population | Regular-season games of the current and previous season |
| Time window | **live:** saved by every data run until kickoff, the last save before kickoff is kept (C9). **live-post:** the social post's projection, when the pipeline has no live record for the game. **backtest:** every fully played week of the previous and current season, rebuilt with `build_previews(as_of=…)` from games before that week, with the crew that worked it; cached once per week. |
| Inclusion rules | A live record is graded once the game has play-by-play |
| Benchmark | — |
| Calculation | `scorecard.py` `freeze()`, `backtest()`; `history.py` keeps each game's first recorded prediction (`live`, else `backtest`) |
| Rounding | — |
| Provenance | `scorecard/live/`, `scorecard/backtest/`, `social/snapshots/` |
| Limitations | **A history week can mix sources** (2026 Week 4: 1 posted, 15 backtest) and its summary averages them together ([C24](audits/metric-conflicts-2026-10-28.md#c24-live-and-backtest-projections-mixed-in-one-week-summary)). "Published" covers both `live` and `live-post`. Backtest weeks are cached and not rebuilt if the model changes (today's model reproduces them). The time each graded projection was saved (`frozenAt`) isn't shown anywhere ([C9](audits/metric-conflicts-2026-10-28.md#c9-scorecard-which-projection-is-graded)). |
| Where it appears | `scorecard/public.json` → `definitions.live`, `definitions.backtest`, `season`, `backtest.lastSeason.season`, `backtest.currentSeason.season`, `live.games[].source` (not displayed), `generatedAt` (not displayed). `history/<week>` → `games[].prediction.source`, `notes` (not displayed), `games[].prediction.frozenAt` (not displayed), `games[].prediction.modelVersion` (not displayed), `games[].recordedAt` (not displayed). |
| Example | Live records: 56 `live`, 2 `live-post` (ATL @ NO, Week 4; TB @ DAL, Week 5); 44 graded. Backtest: 379 games (272 in 2025, 107 in 2026). |
| Conflicts | [C9](audits/metric-conflicts-2026-10-28.md#c9-scorecard-which-projection-is-graded), [C24](audits/metric-conflicts-2026-10-28.md#c24-live-and-backtest-projections-mixed-in-one-week-summary) |

### M82. Average miss (and each game's miss)

| Field | Value |
|---|---|
| Label on site | Track record: "**3.5** avg miss". Pop-up tile "Average miss": "3.5", "flags per game". Table "Every published projection": "Miss" ("+2.1", red when more flags than projected); history "Miss", sorted "Biggest misses first"; week menu "3.5 avg miss"; pop-up "2026 by week (backtest)": "Avg miss". Guide: "missed the actual flag count by 3.48 on average". Definition: "Average gap between projected and actual accepted penalties per game". |
| Kind | Derived: mean absolute error of a model estimate against an observed count |
| Numerator | Σ \|actual − projected\| (game totals) |
| Denominator | Graded games |
| Population | The graded projections of one source (M81) |
| Time window | Live: every graded live game so far. Backtest: one season. By week: one week. |
| Inclusion rules | Actual flags as in the section notes |
| Benchmark | The guess's miss (M85) |
| Calculation | `summarize()` → `avgMiss`; per game `miss` = actual − projected (signed), `absMiss` |
| Rounding | Stored 2 decimals → pop-up and track record 1, guide 2; per-game miss 1 |
| Provenance | `scorecard/live/`, `scorecard/backtest/`; nflverse play-by-play |
| Limitations | Measures the game total only (home and away misses are stored, not shown on the scorecard). Red/green on the miss follows the color rule (red = more flags than projected). |
| Where it appears | `scorecard/public.json` → `live.summary.avgMiss`, `backtest.lastSeason.summary.avgMiss`, `backtest.currentSeason.summary.avgMiss`, `backtest.currentSeason.byWeek[].avgMiss`, `live.games[].miss`; not displayed: `live.byWeek[].avgMiss`, `backtest.lastSeason.byWeek[].avgMiss`, `definitions.avgMiss` (shown in "How it's graded"). `history/<week>` → `games[].grade.miss`, `games[].grade.absMiss` (sort order). `history/index.json` → `weeks[].avgMiss` (week menu). |
| Example | Live: 3.48 (44 games); 2025 backtest: 3.43 (272); 2026 backtest: 3.53 (107). Recomputed, a match. |
| Conflicts | None |

### M83. In the likely range (hit rate)

| Field | Value |
|---|---|
| Label on site | Track record: "**89%** in range". Pop-up tile "In the likely range": "89%", "target ≈ 80%". Tables: "In range" ✓ / ✗; history "92% in range"; week menu "… · 93% in range". Guide: "88.6% landed inside the projected range". Definition: "Share of games where the actual count landed inside the projected likely range (target ~80%)". |
| Kind | Derived: share of graded games (coverage of a model interval) |
| Numerator | Games where low ≤ actual ≤ high (both ends counted) |
| Denominator | Graded games |
| Population, Time window | As M82 |
| Inclusion rules | As M82 |
| Benchmark | "Target ≈ 80%" |
| Calculation | `summarize()` → `hitRate`; per game `inRange` |
| Rounding | Stored 1 decimal → whole percent (guide 1 decimal) |
| Provenance | As M82 |
| Limitations | **The stated target isn't what the range is built to give** ([C23](audits/metric-conflicts-2026-10-28.md#c23-in-the-likely-range-target--80-vs-the-ranges-design)): the range is the 10th to 90th percentile in whole flags with both ends counted, so the model itself expects **more** than 80% inside it: 83.5% for the 56 live projections, and never 80% or less for any mean and dispersion the model uses. Against that, live 88.6% is about 5 points above expectation, and the 2025 backtest's 80.1% slightly below. |
| Where it appears | `scorecard/public.json` → `live.summary.hitRate`, `backtest.lastSeason.summary.hitRate`, `backtest.currentSeason.summary.hitRate`, `backtest.currentSeason.byWeek[].hitRate`, `live.games[].inRange`, `live.games[].low`, `live.games[].high`, `definitions.hitRate`; not displayed: `live.byWeek[].hitRate`, `backtest.lastSeason.byWeek[].hitRate`. `history/<week>` → `games[].grade.inRange`, `games[].prediction.range[]`. `history/index.json` → `weeks[].hitRate`. |
| Example | Live 88.6% (39 of 44); 2025 backtest 80.1%; 2026 backtest 86.0%. Recomputed, a match. |
| Conflicts | [C23](audits/metric-conflicts-2026-10-28.md#c23-in-the-likely-range-target--80-vs-the-ranges-design) |

### M84. Within ±3 flags

| Field | Value |
|---|---|
| Label on site | Pop-up tile "Within ±3 flags": "48%", "<n> games" |
| Kind | Derived: share of graded games |
| Numerator | Games with \|actual − projected\| ≤ 3 |
| Denominator | Graded games |
| Population, Time window, Inclusion rules | As M82 |
| Benchmark | None |
| Calculation | `summarize()` → `within3` |
| Rounding | Stored 1 decimal → whole percent |
| Provenance | As M82 |
| Limitations | No benchmark beside it (what a guess would score isn't stored). |
| Where it appears | `scorecard/public.json` → `live.summary.within3`, `backtest.lastSeason.summary.within3`, `backtest.currentSeason.summary.within3`, `live.summary.games`, `backtest.lastSeason.summary.games`, `backtest.currentSeason.summary.games`, `backtest.currentSeason.byWeek[].games`; not displayed: `live.byWeek[].within3`, `backtest.lastSeason.byWeek[].within3`, `backtest.currentSeason.byWeek[].within3`, `live.byWeek[].games`, `backtest.lastSeason.byWeek[].games` |
| Example | Live 47.7% (44 games); 2025 backtest 51.8% (272). Recomputed, a match. |
| Conflicts | None |

### M85. Skill vs guessing the average

| Field | Value |
|---|---|
| Label on site | Pop-up tile "vs guessing the average": "+3.3%", "league-average guess misses by 3.6". Guide: "Guessing the league average every game would have missed by 3.60." Definition: "How much smaller our average miss is than guessing the league average every game". |
| Kind | Derived: relative reduction in average miss (model estimate vs a benchmark guess) |
| Numerator | Guess miss − model miss |
| Denominator | Guess miss |
| Population, Time window | As M82 |
| Inclusion rules | As M82 |
| Benchmark | **The guess is the model's league level** (M73) for that week: the record's own, else the game's backtest, else that week's preview file, else the latest backtest week |
| Calculation | Per game `baselineMiss` = \|actual − level\|; `baselineAvgMiss`; `skillPct` = (1 − avgMiss ÷ baselineAvgMiss) × 100 |
| Rounding | Stored 1–2 decimals → 1 decimal |
| Provenance | As M82; previews week files (P4) |
| Limitations | **"League average" is the model's level**, not the observed rate ([C21](audits/metric-conflicts-2026-10-28.md#c21-league-in-previews-is-the-models-level-not-the-observed-rate)): the live guesses were 13.7–14.5, while the observed 2026 rate before each week was 14.4–15.0. Guessing the observed rate misses by 3.67, which would make skill +5.2%. A small edge: 0.12 flags per game on 44 games. A percentage without the absolute difference on the tile (the guess's miss is beside it). |
| Where it appears | `scorecard/public.json` → `live.summary.skillPct`, `live.summary.baselineAvgMiss`, `backtest.lastSeason.summary.skillPct`, `backtest.lastSeason.summary.baselineAvgMiss`, `backtest.currentSeason.summary.skillPct`, `backtest.currentSeason.summary.baselineAvgMiss`, `definitions.skillPct`; not displayed: `live.games[].baselineMiss`, `live.byWeek[].skillPct`, `live.byWeek[].baselineAvgMiss`, `backtest.lastSeason.byWeek[].skillPct`, `backtest.lastSeason.byWeek[].baselineAvgMiss`, `backtest.currentSeason.byWeek[].skillPct`, `backtest.currentSeason.byWeek[].baselineAvgMiss`. `history/<week>` → `games[].prediction.leagueAverage` (not displayed). |
| Example | Live: 3.48 vs 3.60 → +3.3%; 2025 backtest: 3.43 vs 3.49 → +1.8%. Recomputed, a match. |
| Conflicts | [C21](audits/metric-conflicts-2026-10-28.md#c21-league-in-previews-is-the-models-level-not-the-observed-rate) |

### M86. Every published projection, and the by-week tables

| Field | Value |
|---|---|
| Label on site | Pop-up table "Every published projection": "Week", "Game", "Crew", "Projected" ("15.1 (9–21)"), "Actual", "Miss", "In range"; footnote "Miss = actual − projected: red means more flags than projected, green fewer." Table "2026 by week (backtest)": "Week", "Games", "Avg miss", "In range". |
| Kind | Model estimate (projected) beside observed counts (actual); derived grades |
| Numerator / Denominator | As M71 (projected) and M82–M83 (grades) |
| Population | Every graded live projection, newest first; backtest weeks of the current season |
| Time window | Current season |
| Inclusion rules | As M82 |
| Benchmark | — |
| Calculation | `grade()` → `live.games[]`, `backtest.currentSeason.byWeek[]`; crew from the officials record, else the projection's |
| Rounding | Projected 1 decimal; actual whole |
| Provenance | As M82 |
| Limitations | Clicking a row opens `openPreviewModal()`, which only knows the current week's previews, so past games open nothing. A live by-week table exists in the data but isn't shown. Home and away projected and actual aren't shown. |
| Where it appears | `scorecard/public.json` → `live.games[].week`, `live.games[].away`, `live.games[].home`, `live.games[].crew`, `live.games[].projected`, `live.games[].actual`, `live.games[].gameId`, `backtest.currentSeason.byWeek[].week`; not displayed: `live.games[].season`, `live.games[].homeProjected`, `live.games[].awayProjected`, `live.games[].homeActual`, `live.games[].awayActual`, `live.byWeek[].season`, `live.byWeek[].week`, `backtest.lastSeason.byWeek[].season`, `backtest.lastSeason.byWeek[].week`, `backtest.currentSeason.byWeek[].season` |
| Example | TB @ CAR, Week 7, Carl Cheffers: projected 15.1 (9–21), actual 10, miss −5.1, in range. |
| Conflicts | None |

### M87. History week summary

| Field | Value |
|---|---|
| Label on site | Pop-up "Week by week": week menu "2026 Week 7" (items "2026 Week 7 · 3.5 avg miss · 86% in range", or "<n> games" when ungraded); stats "**3.5** avg miss", "**86%** in range", "**3** over · **11** under", "**12.6** flags/game". |
| Kind | Derived summaries (as M82, M83) plus an observed rate (flags per game) |
| Numerator | As M82, M83; over / under = games with actual above / below projected; flags per game = Σ actual |
| Denominator | Graded games (grades); every game of the week (flags per game) |
| Population | One completed regular-season week, every game, **whatever the prediction's source** |
| Time window | 2025 Week 1 to the last completed week |
| Inclusion rules | As in the section notes |
| Benchmark | None |
| Calculation | `history.py` `_summary()`; the index repeats each week's summary |
| Rounding | Stored 2 decimals (1 for hit rate) → 1 decimal and whole percent |
| Provenance | `history/games/`; nflverse play-by-play |
| Limitations | **Mixes sources within a week:** 2026 Week 4's "4.4 avg miss, 75% in range" averages 1 posted and 15 backtest projections; the footnote appears only for all-backtest weeks ([C24](audits/metric-conflicts-2026-10-28.md#c24-live-and-backtest-projections-mixed-in-one-week-summary)). Flags per game here counts both teams (as M1). Bias and exact matches are stored, not shown. |
| Where it appears | `history/index.json` → `weeks[].season`, `weeks[].week`, `weeks[].file`, `weeks[].games`, `weeks[].graded`, `weeks[].avgMiss`, `weeks[].hitRate`; not displayed: `weeks[].bias`, `weeks[].over`, `weeks[].under`, `weeks[].exact`, `weeks[].live`, `weeks[].flagsPerGame`, `generatedAt`. `history/<week>` → `season`, `week`, `summary.graded`, `summary.live` (footnote), `summary.avgMiss`, `summary.hitRate`, `summary.over`, `summary.under`, `summary.flagsPerGame`; not displayed: `summary.games`, `summary.bias`, `summary.exact`. |
| Example | 2026 Week 7: 14 games, all live; 3.48 avg miss, bias −1.68, 85.7% in range, 3 over / 11 under, 12.57 flags per game. Recomputed, a match. |
| Conflicts | [C24](audits/metric-conflicts-2026-10-28.md#c24-live-and-backtest-projections-mixed-in-one-week-summary) |

### M88. History game record: prediction, outcome, grade

| Field | Value |
|---|---|
| Label on site | History table: "Game" (+ "published"), "Final" ("TB 43–13 CAR"), "Crew", "Projected" ("15.1 (9–21)"), "Actual flags" ("10 TB 6 · CAR 4"), "Miss", ✓ / ✗ |
| Kind | Observed outcome (counts, score, context); model estimate (the prediction, copied); derived grade |
| Numerator | Outcome: each team's flags, yards, types and quarters (four quarters plus overtime) |
| Denominator | None |
| Population | Every game of a completed week |
| Time window | 2025 Week 1 onward |
| Inclusion rules | As in the section notes; yards as M7 |
| Benchmark | The prediction |
| Calculation | `history.py` `_outcome()`, `_grade()`: `miss`, `absMiss`, `inRange`, `homeMiss`, `awayMiss`, `typeErrors` (actual − projected per type, "Other" for the rest), `quarterErrors`. Crew: the officials record (`crewSource: official`), else the assignment from the prediction. **Corrections:** if nflverse later changes a game's outcome (`hash`), the new outcome replaces it and the old one goes into `corrections[]`. |
| Rounding | Counts whole; errors 1–2 decimals |
| Provenance | nflverse schedules (scores, closing lines, roof, weather, rest) and play-by-play; `scorecard/live/`, `scorecard/backtest/` |
| Limitations | Most of the record isn't shown: per-team misses, type and quarter errors, yards, context, corrections. **No correction has been recorded yet** (0 at `53e0bd1`), and none would be visible on the page. |
| Where it appears | `history/<week>` → `games[].gameId`, `games[].season`, `games[].week`, `games[].away`, `games[].home`, `games[].outcome.awayScore`, `games[].outcome.homeScore`, `games[].outcome.crew`, `games[].prediction.crew`, `games[].prediction.total`, `games[].outcome.total`, `games[].outcome.away.flags`, `games[].outcome.home.flags`. Not displayed: `games[].outcome.crewSource`, `games[].outcome.yards`, `games[].outcome.{home,away}.yards`, `games[].outcome.{home,away}.types.<type>`, `games[].outcome.{home,away}.quarters[]`, `games[].outcome.context.{gameday,weekday,gametime,divisionGame,overtime,closingSpread,closingTotal,roof,surface,temp,wind,homeRest,awayRest,stadium}`, `games[].outcome.hash`, `games[].grade.{homeMiss,awayMiss,quarterErrors}`, `games[].grade.quarterErrors[]`, `games[].grade.typeErrors.<type>`, `games[].corrections[]`, and the rest of the copied prediction: `games[].prediction.{gameId,season,week,away,home,gameday,gametime,home_proj,away_proj,yards,probOver,overThreshold,crewKnown,byQuarter}`, `games[].prediction.{homeRange,awayRange,byQuarter}[]`, `games[].prediction.byType.<type>`, `games[].prediction.byTypeTeams.<type>.{home,away}`, `games[].prediction.byTypeFactors.<type>.{homeCommit,awayCommit,homeDraw,awayDraw,crew}`, `games[].prediction.drivers[].{label,value}`, `games[].prediction.context.{primetime,divisionGame,neutralSite,roof,surface,temp,wind,homeRest,awayRest,spread,total,stadium,homeQB,awayQB,homeCoach,awayCoach}` |
| Example | 2026 Week 7 TB @ CAR: 10 flags (TB 6, CAR 4), projected 15.1 (9–21), miss −5.1. Every Week 7 outcome recomputed, 56 of 56 equal. |
| Conflicts | None |

## What Flags Cost and gameday (including the live strip)

Session 8. **Examples are from `64e6587`** (2026-10-29: 2026 regular season
through Week 7, after PR #115). Places covered: the "What Flags Cost" block
in The Big Picture (section 04: team table, season buttons, "Costliest
flags", ranking toggle, footnotes), the team pop-up's "What flags cost
<team>" tiles and list, "Points given away / game" on the static `/team/`
and `/team/<ABBR>/` pages, `/trends/`'s "What penalties cost", the guide's
"How much does a penalty cost a team?" and "How a penalty's cost is
measured", the `/gameday/` page, and the home page's live strip.

**Sources.**
- **`flag_impact.json`** (`scripts/flag_impact.py` `build_flag_impact()`):
  every accepted penalty naming a team, regular season, current and previous
  season, valued from the penalized team's side. **Model estimates** (expected
  points and win chances from nflverse's models) beside **observed counts**
  (first downs, touchdowns and turnovers wiped out).
- **`wp_tables.json`** (`build_wp_tables()`): two lookup tables measured from
  every regular-season play since 2015, used for win chances here and by the
  gameday worker.
- **The gameday feed** (`worker/gameday/`, a Cloudflare Worker at
  `…workers.dev/live`): ESPN's live scoreboard and play-by-play, parsed every
  15 seconds while games are live, with each game's projection from
  `previews/latest.json` and win-chance costs from ESPN's live win
  probability plus `wp_tables.json`. Read by `/gameday/` (`gameday.js`) and
  the live strip (`livestrip.js`). Paths below are written `gameday feed` →
  `path`.
- **Paths:** `<scope>` is `current` or `lastSeason`; `<team>` a team; `<cell>`
  a table cell key; `<list>` one of `scopes.<scope>.costliest`,
  `scopes.<scope>.costliestWinProb`, `week.costliest`,
  `week.costliestWinProb`, `teamCostliest.<team>` (same row fields).

**The cost model, once** (`classify()`; module notes and `definitions`):
- **Points** (expected points lost by the penalized team):
  - the flag wipes out the play (`no_play`): the play's change in expected
    points (EPA), charged to the penalized team (**play value**)
  - the flag is added on top of a play that counts: penalty yards × 0.0615
    points (**penalty yards**)
  - a touchdown wiped out by the offense's own flag (play text "TOUCHDOWN
    NULLIFIED", or a "no play" touchdown): 7 − expected points before the play
    − what the play kept, at least 0 (**touchdown value**)
  - a defensive flag that wiped out a failed two-point try: 2 × 46.8%
    (**two-point retry**); other two-point flags: penalty yards
- **Win chances** (percentage points of the penalized team's chance of
  winning): the play's change in nflverse win probability (play value); for
  a wiped-out touchdown, the kicking team's chance had it stood (kickoff
  table) minus the chance after the play; otherwise points × what a point is
  worth at that score and clock (leverage table).
- **2026 flags by method:** 1,127 play value, 413 penalty yards, 27
  touchdown value, 3 two-point retry (1,570).

**Spot checks** (my own implementation of the rules above, from nflverse
play-by-play):
- `wp_tables.json`: the number of kickoff and leverage cells, and one cell
  of each, rebuilt from every regular-season play 2015–2026.
- Every team figure for JAX, GB, NYJ and KC (2026) and NE and PHI (2025):
  points per game, rank, flags, key first downs, drives stalled, big plays
  erased, own turnovers erased, touchdowns erased (with offsetting), wins
  given away; each season's league points per team-game, league touchdowns
  erased, and the costliest flag. **71 of 71 match.**
- First downs given (2026: 432; 2025: 973) equal the scoreboard's "First
  downs by penalty" (M14).

**Fixed during this session:** D9 and D10 (#114, PR #115, merged
2026-10-29): the table's "≈ Wins given away" and "Own turnovers erased"
columns were swapped, and offsetting touchdowns were counted twice in the
table and the pop-up. Examples below are after the fix.

### M89. Points given away (a flag's cost in expected points)

| Field | Value |
|---|---|
| Label on site | "Costliest flags" rows: rank, type, player · team · "IND @ WAS, Wk 4", quarter and clock, labels ("Touchdown erased", "Key first down given", "<n>-yd gain erased"…), then "**9.0** pts" and "**28%** win chance". Ranking toggle "By points" / "By win chances"; footnote "Ranked by expected points lost, whatever the score and clock." and "How it's valued: when a flag erases the play, its cost is the change in expected points (nflverse's model). When a flag is added on top of a play that counts, only the penalty yards are charged (about 0.06 points per yard). Two-point tries use the 46.8% conversion rate." Guide: "How a penalty's cost is measured". |
| Kind | **Model estimate** (nflverse's expected-points model), per flag |
| Numerator | Expected points lost by the penalized team on the flagged play (see "The cost model, once") |
| Denominator | One flag |
| Population | Accepted penalties naming a team, regular season, current and previous season |
| Time window | Each flag |
| Inclusion rules | As in Terms; offsetting plays carry no accepted flag (they appear only as touchdowns erased, M94) |
| Benchmark | None per flag |
| Calculation | `classify()` → `cost_epa`, `cost_method` → each row's `pointsCost`, `method` |
| Rounding | Stored 2 decimals → shown 1 (rows) |
| Provenance | nflverse play-by-play (`epa`, `ep`, `penalty_yards`, `desc`, `play_type`, `two_point_attempt`). Every data run. |
| Limitations | **The method description is incomplete** (D12): the footnote, the guide and `definitions.method` describe play value, penalty yards and two-point tries, but not **touchdown value**, the method behind 9 of 2026's 10 costliest flags. "Points" isn't called an estimate where it's shown ([C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased)). EPA describes the play as a whole, not the flag alone (module notes). |
| Where it appears | `flag_impact.json` → `<list>[].pointsCost`, `<list>[].method` (not displayed), `definitions.pointsCost` (not displayed), `definitions.method` (not displayed), `notes` (not displayed). `wp_tables.json` → `pointsPerYard` (worker). |
| Example | 2026's costliest flag by points: WAS illegal shift, Week 4 vs IND, 3rd quarter, 9.04 points (touchdown value; 28.2% win chance). By win chance: TB offensive holding, 33.6% (touchdown erased). 2026 averages: 0.89 points per flag; defensive pass interference 1.64; flags that erased a touchdown 4.16. Recomputed, a match. |
| Conflicts | [C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased), [D12](audits/metric-conflicts-2026-10-28.md#d12-cost-method-text-leaves-out-touchdown-value) |

### M90. Points given away per game (team) and the league rate

| Field | Value |
|---|---|
| Label on site | Table "What Flags Cost": subtitle "Not every flag hurts the same. Expected points each team has given away to penalties, and what those flags did. Regular season 2026, through Week 7. Most costly first."; buttons "2026" / "2025"; columns "#", "Team", "Points given away / game" (bar), "Season total" ("57.2 (6 g)"), "Flags". Team pop-up tile "Points given away / game": "9.53", "#1 of 32 most costly · league 6.51" with a badge. Static `/team/`: "Points given away / game"; static `/team/<ABBR>/`: tile ("#1 most costly"), summary "Their flags have cost 9.53 expected points per game." `/trends/`: "League-wide, flags cost each team about 6.51 expected points per game in 2026. Most costly: …". Guide: "About 6.51 expected points per team per game in 2026. The most costly flags are pass interference and personal fouls that hand the offense a first down on third down." |
| Kind | **Model estimate** summed per team, then per game (exposure rate); rank derived |
| Numerator | Σ points given away (M89) on the team's flags |
| Denominator | The team's regular-season games |
| Population | Each team; league = all teams (per team-game) |
| Time window | Current season through the last completed week (buttons: current or previous season) |
| Inclusion rules | As M89 |
| Benchmark | The league's points per team-game (pop-up badge) |
| Calculation | `_team_block()`: `pointsCost`, `pointsCostPerGame`, `games`, `flags`, `rank` (1 = most costly per game; ties by order, not shared); league `pointsCostPerTeamGame` = Σ cost ÷ (2 × games) |
| Rounding | Per game 2 decimals (shown 2: false precision for an estimate); season total 1 |
| Provenance | As M89 |
| Limitations | An estimate shown to 2 decimals with no interval ([C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased)). "Most costly" ranks reflect play volume and game situations as well as discipline. Ties don't share a rank (unlike M54). The pop-up badge is a percentage only (M2). |
| Where it appears | `flag_impact.json` → `scopes.<scope>.teams[].team`, `scopes.<scope>.teams[].pointsCostPerGame`, `scopes.<scope>.teams[].pointsCost`, `scopes.<scope>.teams[].games`, `scopes.<scope>.teams[].flags`, `scopes.<scope>.teams[].rank`, `scopes.<scope>.league.pointsCostPerTeamGame` |
| Example | 2026: JAX 9.53 (57.2 in 6 games, #1), GB 8.46 (#4), NYJ 8.09 (#5); league 6.51. 2025: NE 5.45 (#19), league 5.57. Recomputed, a match. |
| Conflicts | [C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased) |

### M91. Win chances lost and "≈ Wins given away"

| Field | Value |
|---|---|
| Label on site | Table column "≈ Wins given away" (hover "Win chances lost to flags, added up: about this many wins"); pop-up tile "≈ Wins given away" "1.8", "win chances lost to flags, added up". "Costliest flags" ranked "By win chances": rows "34% win chance" (hover "Win chances this flag cost the penalized team (nflverse win probability)"); footnote "Ranked by win chances lost: flags late in close games count most. Win chance = how much the flag changed the penalized team's chance of winning (nflverse win-probability model; for a wiped-out touchdown, the chance had it stood, assuming the extra point)." |
| Kind | **Model estimate** (nflverse win probability plus `wp_tables.json`); sum across flags |
| Numerator | Per flag: win-chance points lost (see "The cost model, once"); team: their sum |
| Denominator | None (a season sum, read as "wins") |
| Population, Time window | As M90 |
| Inclusion rules | As M89; flags with no win-probability value count 0 |
| Benchmark | None |
| Calculation | `classify()` → `cost_wp`, `wp_method` → rows' `winProbCost` (×100), `winProbMethod`; teams' `winsGivenAway` = Σ `cost_wp`. Tables: `wp_tables.json` → `kick.<cell>` (kicking team's win chance by lead and clock, with games) and `lev.<cell>` (win chance per expected point by clock and margin). |
| Rounding | Per flag 1 decimal (percent) → whole percent; wins 2 decimals → 1 |
| Provenance | nflverse play-by-play (`wp`, `wpa`, `score_differential`, `game_seconds_remaining`); tables from every regular-season play 2015–2026 |
| Limitations | Adding win chances across games and calling it "wins" assumes the changes are independent; it's an estimate, marked "≈" but not called one ([C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased)). The season pages use nflverse's model; the gameday page uses ESPN's (M99). **Fixed in #114 (D10):** the table showed own turnovers erased under this header. |
| Where it appears | `flag_impact.json` → `scopes.<scope>.teams[].winsGivenAway`, `<list>[].winProbCost`, `<list>[].winProbMethod` (not displayed), `definitions.winProbCost` (not displayed), `definitions.winsGivenAway` (not displayed). `wp_tables.json` → `kick.<cell>[]`, `lev.<cell>[]`, `seasons`, `note` (not displayed; read by the worker). |
| Example | 2026: JAX 1.78, GB 1.45, NYJ 1.64 (shown 1.8, 1.5, 1.6); 2025 NE 2.47. Recomputed with rebuilt tables, a match. |
| Conflicts | [C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased), [D10](audits/metric-conflicts-2026-10-28.md#d10-what-flags-cost--wins-given-away-and-own-turnovers-erased-columns-swapped) (fixed in #114) |

### M92. Key first downs given (and first downs given)

| Field | Value |
|---|---|
| Label on site | Table "Key 1st downs given" (hover "Defensive flags that gave a first down on 3rd or 4th down"); pop-up tile "Key 1st downs given", "3rd/4th-down flags that moved the chains"; row label "Key first down given" / "First down given" |
| Kind | Raw count (observed) |
| Numerator | Defensive flags with `first_down_penalty` = 1 on 3rd or 4th down (all downs: first downs given) |
| Denominator | None |
| Population, Time window | As M90 |
| Inclusion rules | As M89 |
| Benchmark | None |
| Calculation | `classify()` → `first_down_given`, `key_first_down` |
| Rounding | Whole numbers |
| Provenance | nflverse play-by-play |
| Limitations | A season count, not per game: teams with a bye have one game fewer. **All first downs given equal the scoreboard's "First downs by penalty" (M14):** 432 in 2026, 973 in 2025, so every first-down penalty counted there is a defensive flag. |
| Where it appears | `flag_impact.json` → `scopes.<scope>.teams[].keyFirstDownsGiven`, `scopes.<scope>.league.keyFirstDownsGiven` (not displayed), `definitions.keyFirstDownsGiven` (not displayed); not displayed: `scopes.<scope>.teams[].firstDownsGiven` |
| Example | 2026: GB 12, JAX 8, NYJ 7; league 173. Recomputed, a match. |
| Conflicts | None |

### M93. Drives stalled and big plays erased

| Field | Value |
|---|---|
| Label on site | Table "Drives stalled" (hover "Offensive flags inside the opponent 40 on drives that then didn't score"), "Big plays erased" (hover "Offensive flags that wiped out a 15+ yard gain or a touchdown"); pop-up tile "Drives stalled / big plays erased", "offensive flags in scoring range / on 15+ yd gains or TDs"; row labels "Drive stalled after", "Big play erased"; footnote '"Drives stalled" shows flags on drives that came up empty, not proof the flag caused it.' |
| Kind | Raw counts (observed) |
| Numerator | Drives stalled: offensive flags on scrimmage plays inside the opponent's 40 on drives that ended without a score. Big plays erased: offensive flags that wiped out a 15+ yard gain ("for N yards" in the play text) or a touchdown. |
| Denominator | None |
| Population, Time window | As M90 |
| Inclusion rules | As M89 |
| Benchmark | None |
| Calculation | `classify()` → `drive_killed`, `big_play_erased`; `gain_erased` from the play text before "PENALTY" |
| Rounding | Whole numbers |
| Provenance | nflverse play-by-play (`yardline_100`, `fixed_drive_result`, `desc`) |
| Limitations | The footnote says "not proof the flag caused it"; the column title "Drives stalled" and the field name `drivesKilled` say more ([C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased)). The gain comes from parsing text. |
| Where it appears | `flag_impact.json` → `scopes.<scope>.teams[].drivesKilled`, `scopes.<scope>.teams[].bigPlaysErased`, `<list>[].labels[]`, `<list>[].gainErased` (not displayed), `scopes.<scope>.league.drivesKilled` (not displayed), `scopes.<scope>.league.bigPlaysErased` (not displayed), `definitions.drivesKilled` (not displayed), `definitions.bigPlaysErased` (not displayed) |
| Example | 2026: JAX 4 / 4, GB 3 / 2, NYJ 1 / 2. Recomputed, a match. |
| Conflicts | [C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased) |

### M94. Touchdowns erased (own flags and offsetting penalties)

| Field | Value |
|---|---|
| Label on site | Table "TDs erased" ("5 (1 off.)"; hover "Touchdowns wiped out by the team's own flags (plus any lost to offsetting penalties)"); pop-up tile "Touchdowns erased": "5", "4 by own flags, 1 by offsetting penalties" (or "wiped out by own flags"); row label "Touchdown erased" |
| Kind | Raw count (observed) |
| Numerator | Touchdowns wiped out by the scoring team's own accepted flag ("TOUCHDOWN NULLIFIED" or a "no play" touchdown), plus touchdowns wiped out by offsetting fouls credited to the team that lost them |
| Denominator | None |
| Population, Time window | As M90 |
| Inclusion rules | Offsetting plays have no accepted flag in nflverse; they come from the full play-by-play (`offsetting_tds`, C2) |
| Benchmark | None |
| Calculation | `_team_block()`: `tdsErased` = own-flag touchdowns + offsetting; `tdsLostOffsetting` = the offsetting ones (**of those**) |
| Rounding | Whole numbers |
| Provenance | nflverse play-by-play (`desc`) |
| Limitations | The only place offsetting plays count (C2). **Fixed in #114 (D9):** the page added `tdsLostOffsetting` to `tdsErased` again (JAX showed 6, actual 5). |
| Where it appears | `flag_impact.json` → `scopes.<scope>.teams[].tdsErased`, `scopes.<scope>.teams[].tdsLostOffsetting`, `scopes.<scope>.league.tdsErased` (not displayed), `scopes.<scope>.league.tdsLostOffsetting` (not displayed), `definitions.tdsErased` (not displayed), `definitions.tdsLostOffsetting` (not displayed) |
| Example | 2026: JAX 5 (4 + 1), GB 2 (1 + 1), NYJ 2; league 29 (2 offsetting). 2025: NE 3 (2 + 1). Recomputed, a match. |
| Conflicts | [C2](audits/metric-conflicts-2026-10-28.md#c2-offsetting-penalty-plays-counted-as-flags), [C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased), [D9](audits/metric-conflicts-2026-10-28.md#d9-touchdowns-lost-to-offsetting-penalties-counted-twice) (fixed in #114) |

### M95. Own turnovers erased

| Field | Value |
|---|---|
| Label on site | Table "Own turnovers erased" (hover "Defensive flags that wiped out their own interception or fumble recovery"); pop-up tile "Own turnovers erased", "defensive flags that wiped out a takeaway"; row label "Turnover erased" |
| Kind | Raw count (observed) |
| Numerator | Defensive flags on "no play" plays whose text before "PENALTY" has an interception or a recovered fumble |
| Denominator | None |
| Population, Time window | As M90 |
| Inclusion rules | As M89 |
| Benchmark | None |
| Calculation | `classify()` → `to_erased` |
| Rounding | Whole numbers |
| Provenance | nflverse play-by-play (`desc`) |
| Limitations | From play text. **Fixed in #114 (D10):** shown under "≈ Wins given away" in the table before the fix. |
| Where it appears | `flag_impact.json` → `scopes.<scope>.teams[].turnoversErased`, `scopes.<scope>.league.turnoversErased` (not displayed), `definitions.turnoversErased` (not displayed) |
| Example | 2026: GB 3, NYJ 3, JAX 1; 2025 NE 0. Recomputed, a match. |
| Conflicts | [D10](audits/metric-conflicts-2026-10-28.md#d10-what-flags-cost--wins-given-away-and-own-turnovers-erased-columns-swapped) (fixed in #114) |

### M96. Costliest flags (season, week, team)

| Field | Value |
|---|---|
| Label on site | "Costliest flags of Week 7" (current season) or "of 2025"; rows: rank, type, player · team · "away @ home, Wk N" (team list: "Wk N vs/@ opponent"), quarter and clock, cost, labels; 8 shown. Team pop-up: "Costliest <team> flags this season" (5). Live strip, between game weeks: last week's costliest flag by win chance. |
| Kind | A list of flags with their model estimates (M89, M91) and observed details |
| Numerator / Denominator | — |
| Population | Season lists: the 10 costliest flags of the scope; week lists: the last completed week; team lists: the team's 5 costliest this season |
| Time window | As named |
| Inclusion rules | As M89 |
| Benchmark | — |
| Calculation | `_flag_row()`; sorted by `cost_epa` (or `cost_wp` for the win-chance lists) |
| Rounding | As M89, M91 |
| Provenance | As M89 |
| Limitations | Mostly touchdown-erasing offensive flags (9 of 2026's 10 by points), valued by the method the footnote leaves out (D12). |
| Where it appears | `flag_impact.json` → `<list>[].type`, `<list>[].player`, `<list>[].team`, `<list>[].away`, `<list>[].home`, `<list>[].week`, `<list>[].qtr`, `<list>[].time`, `<list>[].labels[]`, `<list>[].gameId` (not displayed), `<list>[].side` (not displayed), `<list>[].yards` (not displayed), `<list>[].twoPoint` (not displayed), `week.week` |
| Example | 2026 top 10 by points: offensive holding 5, plus illegal shift, offensive and defensive pass interference, illegal formation, face mask; 9 erased a touchdown. |
| Conflicts | [D12](audits/metric-conflicts-2026-10-28.md#d12-cost-method-text-leaves-out-touchdown-value) |

### M97. What Flags Cost: windows and labels

| Field | Value |
|---|---|
| Label on site | Season buttons "2026" / "2025"; subtitle "Regular season 2026, through Week 7"; pop-up heading "What flags cost <team> (2026)" |
| Kind | Definitions of the windows |
| Numerator / Denominator | — |
| Population | Regular season |
| Time window | `current` = the current season (every game so far; "through Week N" = the last completed week); `lastSeason` = the previous season |
| Inclusion rules | — |
| Benchmark | — |
| Calculation | `build_flag_impact()` |
| Rounding | — |
| Provenance | As M89 |
| Limitations | "Through Week 7" is the last completed week, but the current scope includes any partial-week games (as C4). |
| Where it appears | `flag_impact.json` → `season`, `throughWeek`, `scopes.<scope>.season`, `scopes.<scope>.games` (not displayed), `scopes.<scope>.flags` (not displayed), `generatedAt` (not displayed) |
| Example | Current 2026, through Week 7 (107 games, 1,570 flags); previous 2025 (272 games). |
| Conflicts | [C4](audits/metric-conflicts-2026-10-28.md#c4-partial-week-games-in-the-current-season-not-in-the-comparison) |

### M98. Live flags (gameday feed)

| Field | Value |
|---|---|
| Label on site | `/gameday/`: "Flags as they happen", "Every penalty in every game, ranked live."; league tiles "Games live" ("<n> final · <n> to come"), "Flags" ("<n> per game"), "Penalty yards" ("<n> per game"), "Most flagged" ("<team> <n>", "team, this week's games"); game cards ranked by flags, each with score, status, team flags and yards, "Projected 14.7 · on pace for 18"; "Flags by team"; "Flag log" (team, player, type, yards, "accepted" / "declined or offsetting", clock); "Latest flags" ticker; note "Accepted penalties; declined and offsetting flags are listed but not counted. Totals come from the live box score. Play-by-play via ESPN, updated about every 20 seconds; official numbers on the rest of the site come from nflverse after each game." Live strip: "LIVE" / "GAMEDAY" / "FINAL", "Week 8", "<n> flags", a tile per game (status, network, each team's flags and score, "Proj 14.7 flags · <crew chief's last name>"), "Most flags" marker. |
| Kind | Raw counts (observed, live) and a pace (derived) |
| Numerator | Each team's accepted penalties in the live box score (if missing: accepted flags parsed from the play text) |
| Denominator | Games played (per game); elapsed share of 60 minutes (pace) |
| Population | This week's games on ESPN's scoreboard |
| Time window | Live, refreshed about every 15–20 seconds |
| Inclusion rules | **ESPN's box score counts penalties, not plays:** two accepted flags on one play count twice (the rest of the site counts plays, C5). Declined and offsetting flags are listed, not counted. |
| Benchmark | The preview's projection (M71) |
| Calculation | `parse.js` `compactGame()`, `boxPenalties()`, `parsePlayPenalties()`; `gameday.js` `pace()` = flags ÷ elapsed share, from 15% of the game; red / green when pace is 10% above / below the projection |
| Rounding | Whole numbers; per game 1 decimal; projection 1 decimal |
| Provenance | ESPN's undocumented scoreboard and summary feeds; `previews/latest.json` (first week file only) |
| Limitations | Live counts can differ from nflverse's final counts for the same game (penalties vs plays, and ESPN's own corrections); the note says the official numbers come later. Between game weeks the live strip shows last week's finals from `history/` instead (nflverse counts) and puts the crew chief's last name where the network goes. The feed's `preview.low` and `preview.high` are always empty: the worker reads `projection.low` / `.high`, which don't exist (the range is `projection.range`); nothing shows them. |
| Where it appears | `gameday feed` → `week`, `season`, `live`, `updatedAt`, `games[].id`, `games[].name`, `games[].start`, `games[].state`, `games[].detail`, `games[].period`, `games[].clock`, `games[].network`, `games[].{home,away}.abbr`, `games[].{home,away}.score`, `games[].{home,away}.flags`, `games[].{home,away}.yards`, `games[].flags`, `games[].yards`, `games[].log[].team`, `games[].log[].player`, `games[].log[].type`, `games[].log[].yards`, `games[].log[].status`, `games[].log[].noPlay`, `games[].log[].qtr`, `games[].log[].clock`, `games[].log[].wall`, `games[].log[].id`, `games[].preview.projected`, `games[].preview.crew`, `games[].preview.crewSlug`, `error`; not displayed: `games[].{home,away}.source`, `games[].log[].seq`, `games[].preview.low`, `games[].preview.high`, `wpModel`, `source`. `history/<week>` and `flag_impact.json` (between weeks, M87, M96). |
| Example | Not run at `64e6587`: no Week 8 game had finished (see the session notes). |
| Conflicts | [C5](audits/metric-conflicts-2026-10-28.md#c5-penalties-counts-plays-with-an-accepted-penalty), [C26](audits/metric-conflicts-2026-10-28.md#c26-live-counts-and-win-chances-come-from-espn-final-ones-from-nflverse) |

### M99. Costliest flag so far (live win chance)

| Field | Value |
|---|---|
| Label on site | `/gameday/`: "Costliest flag so far", "win chances lost · live estimate", "−<n>% win chance", team, type, game, quarter (and "TD erased"), the next two below it; per game "Costliest: …"; hover "Live estimate of the win chances this flag cost …". Live strip tile "Costliest flag", "win chance", "−<n>%", "<team> <type>", "<game> · <quarter>". Note: '"Costliest flag" is a live estimate of the win chances a flag cost the penalized team, using ESPN's live win probability and our own tables (the same method as What Flags Cost)…'. |
| Kind | **Model estimate** (ESPN's live win probability plus `wp_tables.json`) |
| Numerator | Per flag: as M91, with ESPN's win probability in place of nflverse's |
| Denominator | One flag |
| Population | Accepted flags in this week's games |
| Time window | Live |
| Inclusion rules | Accepted flags only |
| Benchmark | None |
| Calculation | `parse.js` `addWinChanceCost()`: play value (no play), touchdown value (kickoff table), else leverage × yards × 0.0615; the feed's top 3 by `wpCost` |
| Rounding | Whole percent |
| Provenance | ESPN; `wp_tables.json` |
| Limitations | Called a "live estimate" on `/gameday/` ("win chances lost · live estimate"), not on the live strip. Shown with a minus sign here and without one on What Flags Cost (M91). ESPN's model, not nflverse's: the same flag can carry a different cost on What Flags Cost after the game ([C26](audits/metric-conflicts-2026-10-28.md#c26-live-counts-and-win-chances-come-from-espn-final-ones-from-nflverse)). The "flag on top of a play" case values only the yards (the season pages value expected points the same way). |
| Where it appears | `gameday feed` → `costliest[].wpCost`, `costliest[].team`, `costliest[].type`, `costliest[].game`, `costliest[].gameId`, `costliest[].qtr`, `costliest[].clock`, `costliest[].tdErased`, `games[].costliest.wpCost`, `games[].costliest.team`, `games[].costliest.type`, `games[].costliest.qtr`, `games[].costliest.clock`, `games[].costliest.tdErased`, `games[].log[].wpCost`, `games[].log[].tdErased`, `costliest[].player`, `costliest[].yards`, `costliest[].noPlay`, `costliest[].id` (highlights a new flag); not displayed: `games[].log[].wpMethod`, `costliest[].wpMethod`, `games[].costliest.wpMethod`, `costliest[].{seq,status,wall}`, `games[].costliest.{id,noPlay,player,seq,status,wall,yards}` |
| Example | Not run at `64e6587` (see M98). |
| Conflicts | [C25](audits/metric-conflicts-2026-10-28.md#c25-what-flags-cost-model-estimates-precision-and-erased), [C26](audits/metric-conflicts-2026-10-28.md#c26-live-counts-and-win-chances-come-from-espn-final-ones-from-nflverse) |

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
| Home, What The Data Shows | '"Let Them Play" Effect' card | `insights.json` → `let_them_play`; `trends.json` → `byQuarter[]` (pipeline only) | M22 |
| Home, What The Data Shows | "Most Common Call" card | `insights.json` → `top_penalty`; `trends.json` → `byType` | M16 |
| Home, What The Data Shows | "Crew Chief Spread" card | `insights.json` → `crew_spread` | M23 |
| Home (search-engine page source) | Pre-filled tiles, crew chief table, subtitle | `build_static.py` `home_prefill()` → `SEASON_SUB`, `SEASON_LEAGUE`, `SEASON_TABLE` (from `season_comparison.json`) | M1, M4–M9 |
| Site, update notice | "New results are in · updated <time>" | `stats.json` → `lastUpdated` | M24 |
| (not displayed) | — | `stats.json` → `totalPenalties`, `totalGames`, `totalReferees`, `seasonsRange`, `refereeVariance` | M24 note, M3 |
| (not displayed in this section) | — | `season_comparison.json` → `crewChiefs[].throughWeek`, `regularSeasonOnly`, `generatedAt`; `crewChiefs[].slug` (link to the crew pop-up, not a number). `crewChiefs[].current.yardsPerPenalty` and `inactiveCrewChiefs[]`: crew pop-up and cards (session 2 rows below) | M8, M1 |
| Home, League Trends | "Crew Chief Flag Rates" chart (current / 2015–25 toggle, league marker, red/green, "(<n> g)") | `season_comparison.json` → `crewChiefs[].current`, `crewChiefs[].baselines.all`, `league.current.perGame`, `league.baselines.all.perGame`, `baselines[]` (`short`) | M1, M6, M35 |
| Home, Meet The Officials | Section subtitle; card header (name, "2015–2026 • <n> games", "Active 2026" / "Not active in 2026") | `referees.json` → `name`, `first_season`, `last_season`, `games`; `season_comparison.json` → `crewChiefs[]`, `inactiveCrewChiefs[]`, `currentSeason` | M30, M25 |
| Home, Meet The Officials | Card rows "2026", "2025", "2015–25": "Pen/g", "Yds/g", "<n> g"; change badges "vs 2025", "vs 2015–25"; small-sample note | `season_comparison.json` → `crewChiefs[].current`, `.baselines.lastSeason`, `.baselines.all` (`perGame`, `yardsPerGame`, `games`); `baselines[]` | M1, M7, M6, M2 |
| Home, Meet The Officials | Card fallback "Avg/Game" (no season data); "Show former crew chiefs (<n>)" | `referees.json` → `avg_per_game`; `season_comparison.json` → `inactiveCrewChiefs[]` | M26 |
| Home, Meet The Officials | Card footer "Most common: <type>", "Home bias <x>%" | `referee/<slug>.json` → `penaltyTypes[0].type`; `referees.json` → `home_bias_pct` | M32, M28 |
| Home, Complete Crew Chief Stats | Title, subtitle, legend; columns "Crew Chief", "Games", "Avg/Game", "Range", "Home Bias", "Consistency" (and their `?` explainers) | `referees.json` → `name`, `games`, `avg_per_game`, `min_penalties`, `max_penalties`, `home_bias_pct`, `consistency` | M25, M26, M27, M28, M29 |
| Crew pop-up | Title and subtitle ("Active 2026 • <n> games this season • <n> career games") | `referee/<slug>.json` → `name`, `stats.games`, `experience`, `currentSeason`; `season_comparison.json` → `crewChiefs[].current.games` | M6, M25, M30 |
| Crew pop-up | "2026 vs history" ("Pen/g", "Yds/g", "Yds/pen"; change badges) | `season_comparison.json` → `crewChiefs[].current`, `.baselines.lastSeason`, `.baselines.all` (`perGame`, `yardsPerGame`, `yardsPerPenalty`, `games`) | M1, M7, M8, M6, M2 |
| Crew pop-up | "2026 so far" line; "Career:" / "Tendencies" | `season_comparison.json` → `league.current.perGame`, `crewChiefs[].current.perGame`; `referee/<slug>.json` → `tendencies.description` | M35 |
| Crew pop-up | "Penalties per game by season (regular season)" chart, "Prior-years avg" line | `referee/<slug>.json` → `regularSeasonStats[].season`, `.perGame` (fallback `seasonStats[]`); `season_comparison.json` → `crewChiefs[].baselines.all.perGame` | M31, M1 |
| Crew pop-up | "What's being called: 2026 vs 2015–25" / "Penalty Type Breakdown" | `referee/<slug>.json` → `penaltyTypeComparison[]` / `penaltyTypes[]` | M33, M32 |
| Crew pop-up | "⏱️ When flags fly: 2026 vs 2015–25" / "⏱️ Penalties By Quarter" | `referee/<slug>.json` → `quarterComparison[]` / `quarterDistribution[]` | M34 |
| Crew pop-up | "Career (all games incl. playoffs, 2015–2026)": "Avg/Game", "Range", "Home Bias", "Style" | `referee/<slug>.json` → `firstSeason`, `lastSeason`, `stats.avgPerGame`, `stats.minGame`, `stats.maxGame`, `stats.homeBiasPct`, `stats.consistency` | M30, M26, M27, M28, M29 |
| Crew pop-up | "Recent Games" | `referee/<slug>.json` → `recentGames[]` | M36 |
| Crew pop-up | "Crew style": tabs, quadrant badge, tiles ("Flags / game", "Yards / flag", "Points / flag", "Pre-snap", "4th quarter", "On offense", "On home team", each with "league"), traits, "Calls most like", type bars, footnote; "Compare years" chips, table and trajectory chart | `crew_styles.json` → `crews[]` (career fields, `seasons.<season>`, `raw`, `vsLeague`, `types`, `traits`, `similar`, `archetype`), `league`, `leagueBySeason`, `careerSeasons`, `season`, `types[]` | M37–M44 |
| Home, League Trends | "Crew Chief Style Map": period menu, subtitle, dots, tooltip, quadrant labels and colors, league lines | `crew_styles.json` → `crews[]` (career, `seasons.<season>`), `weekly.through.<week>`, `weekly.only.<week>`, `weekly.complete`, `league`, `leagueBySeason`, `careerSeasons` | M37, M38, M44 |
| Game previews | Crew style note (quadrant, description, first trait) | `crew_styles.json` → `crews[].archetype`, `.traits[0].text` | M44, M42 |
| Static `/crew/` | Summary, table ("2026 games", "2026 flags / game", "2015–25 flags / game", "Career style"), former crew chiefs table and note | `season_comparison.json` → `crewChiefs[]`, `inactiveCrewChiefs[]`, `league.current.perGame`, `throughWeek`; `referees.json` → `first_season`, `last_season`; `crew_styles.json` → `crews[].archetype.title` | M1, M6, M30, M44 |
| Static `/crew/<slug>/` | Summary, tiles ("2026 flags / game", "2026 yards / game", "2025 flags / game", "2015–25 flags / game"), FAQ (per game, yards) | `season_comparison.json` → `crewChiefs[]` (`current`, `baselines.lastSeason`, `baselines.all`), `league.current` | M1, M7, M6, M35 |
| Static `/crew/<slug>/` | "Season by season", "Recent games" | `referee/<slug>.json` → `seasonStats[]`, `recentGames[]` | M31, M36 |
| Static `/crew/<slug>/` | "Calling style" (career and current-season quadrant), traits list, "Calls most like", "Penalty types vs the league (2015–25, season-adjusted, per game)", FAQ (types per game, "Compared with other crews", home share) | `crew_styles.json` → `crews[].archetype`, `.seasons.<season>.archetype`, `.traits[].text`, `.similar[]`, `.types.<type>.perGame`, `.diffPct`, `.homeShare`, `league.homeShare`, `careerSeasons` | M44, M42, M43, M41, M40 |
| Static `/assignments/` | Summary ("<n> of <n> Week <n> games have a crew chief assigned", projected most flags), table ("Game", "Date", "TV", "Crew chief", "Crew 2026 flags / game", "Crew career style", "Projected flags"), note | `previews/latest.json` → week file `games[]` (`awayTeam`, `homeTeam`, `gameday`, `network`, `crew`, `projection.total`); `season_comparison.json` → `crewChiefs[].current.perGame`; `crew_styles.json` → `crews[].archetype.title` | M45, M1, M44; projections: previews session |
| Home (search-engine page source) | Pre-filled crew chiefs list and Complete Crew Chief Stats rows | `build_static.py` `home_prefill()` → `REFEREES` (`season_comparison.json`), `DATA_TABLE` (`referees.json`) | M1, M25–M29 |
| `/data/exports/crew_chiefs_<season>.csv` | `crew_chief`, `games_<season>`, `flags_per_game_<season>`, `yards_per_game_<season>`, `career_games_2015_25`, `career_flags_per_game_2015_25`, `career_style` | `season_comparison.json` → `crewChiefs[]`; `crew_styles.json` → `crews[].archetype.title` | M6, M1, M7, M44 |
| (not displayed) | — | `referees.json` → `total_penalties`, `std_dev`, `slug`; `referee/<slug>.json` → `stats.totalPenalties`, `stats.stdDev`, `seasonStats[].penalties`, `.homeBias`, `currentSeasonGames`, `priorSeasonGames`, `tendencies.avgVsLeague`, `.avgVsLeaguePct`, `explanations.*`, `penaltyTypeComparison[].currentCount`, `.priorCount`, `quarterDistribution[].count`, `regularSeasonStats[].penalties`, `.yards`, `.yardsPerGame`, `recentGames[].gameType`, `.stadium`, `.weather`, `.temp`, `generatedAt` | M25–M36 notes |
| Home, Team Discipline | Section title and subtitle; division tiles; "<division> <season> · ranked by penalties per game"; comparison buttons | `teams/index.json` → `divisions[].name`, `divisions[].teams[].abbr`, `.name`, `.logo`, `season`, `baselines[]`, `defaultBaseline`, `throughWeek` | M48, M62 |
| Home, Team Discipline | Team card: record and games; "penalties/game · <n> yds"; "vs league avg"; "Most-penalized rank"; comparison and badge | `divisions[].teams[].record`, `.games`, `.perGame`, `.yardsPerGame`, `.rank`, `.baselinePerGame.<key>`, `.lastSeasonPerGame`, `.throughWeek`; `leaguePerGame` | M62, M46, M53, M47, M54, M48, M2 |
| Team pop-up | Title, subtitle (division, record, next game), "Preview next game" button | `teams/<ABBR>.json` → `name`, `logo`, `division`, `season`, `record`, `nextGame` | M62 |
| Team pop-up | Comparison buttons and footnote; "<season> vs <comparison>": "Pen/g", "Yds/g", "Drawn/g", change badges, small-sample note | `baselines.<key>` (`label`, `short`, `games`, `perGame`, `yardsPerGame`, `drawnPerGame`), `current`, `defaultBaseline` | M48, M46, M53, M49, M2 |
| Team pop-up | Tiles "Most-penalized rank", "Offense / Defense", "Home / Away", "Flag margin" | `rank.current`, `rank.lastSeason`, `rank.of`; `current.offensePerGame`, `.defensePerGame`, `.homePerGame`, `.awayPerGame`, `.netPerGame` | M54, M51, M52, M50 |
| Team pop-up | "Penalties per game by season (regular season)" chart and tooltip | `history[]`; `baselines.<key>.perGame` | M63, M54 |
| Team pop-up | "What they get flagged for", "Which calls are rising", "What they draw from opponents", "⏱️ When they get flagged" | `committedTypes[]`, `typeTrends[]`, `drawnTypes[]`, `quarters[]`; `baselines.<key>.types`, `.drawnTypes`, `.quarters` | M55, M58, M56, M57 |
| Team pop-up | "What flags cost <team>" | `flag_impact.json` | M90, M92–M96 |
| Team pop-up | "Flags on <team> by crew chief", "Watchlist", "By opponent", "<season> game log" | `crews[]`, `players[]`, `opponents[]`, `games[]`; `priorSeasons[]` | M60, M59, M61, M62 |
| Static `/team/` | Summary (most, least, league average), table ("Rank", "Team", "Games", "<season> flags / game", "<season − 1> flags / game", "Points given away / game"), note | `teams/index.json` → `divisions[].teams[]` (`rank`, `games`, `perGame`, `lastSeasonPerGame`), `leaguePerGame`; `flag_impact.json` | M54, M46, M47; points: M90 |
| Static `/team/<ABBR>/` | Summary; tiles "Flags / game", "Opponent flags / game", "Penalty yards / game", "Points given away / game"; "Most common penalties"; "Game log"; "By crew chief (since 2015)"; FAQ | `teams/<ABBR>.json` → `current`, `lastSeason`, `rank.current`, `committedTypes[]`, `games[]`, `crews[]`; `teams/index.json` → `leaguePerGame`; `flag_impact.json` | M46, M47, M49, M53, M54, M55, M62, M60; points: M90 |
| Static `/guide/` | "Which NFL team commits the most penalties in <season>?" | `teams/index.json` → `divisions[].teams[].perGame` | M46 |
| Home (search-engine page source) | Pre-filled division lists ("<team> <rate> flags/game") | `build_static.py` `home_prefill()` → `DIVISIONS` (`teams/index.json`) | M46 |
| `/data/exports/teams_<season>.csv` | `team`, `games`, `flags_per_game`, `last_season_flags_per_game`, `rank` | `teams/index.json` → `divisions[].teams[]` (`abbr`, `games`, `perGame`, `lastSeasonPerGame`, `rank`) | M46, M54 |
| (not displayed) | — | `teams/index.json` → `generatedAt`; `teams/<ABBR>.json` → `leaguePerGame`, `allPrior.*`, `{current,lastSeason,baselines.<key>}.penalties`, `.yards`, `.drawnYardsPerGame`, `{lastSeason,allPrior,baselines.<key>}` offense, defense, home, away and net fields, `committedTypes[].currentCount`, `history[].drawnPerGame`, `opponents[].yardsPerGame`, `.oppYardsPerGame`, `.totalOppFlags`, `.homeGames`, `games[].gameId`, `games[].date`, `nextGame.date` | M46–M63 notes |
| Home, The Big Picture | "Penalties Per Game By Season" chart (subtitle, legend, bars, tooltip) | `type_trends.json` → `seasonCompare[]`, `throughWeek` | M64 |
| Home, The Big Picture | "Penalties Per Game By Quarter" chart: scope buttons, type menu, subtitle, bars | `type_trends.json` → `quarters.<scope>` (`total`, `types`, `games`), `scopeLabels` | M67 |
| Home, The Big Picture | "Penalties Per Game By Week Of Season": takeaway, season buttons, lines, band, tooltip, note | `type_trends.json` → `weekly` (`seasons[].weeks[]`, `priorAverage[]`, `priorRange[]`, `priorLabel`), `season` | M65, M66 |
| Home, The Big Picture | "Share Of All Flags By Penalty Type": scope buttons, subtitle, bars, "All other" | `type_trends.json` → `typeShare.<scope>`, `scopeLabels` | M68 |
| Home, The Big Picture | "Which calls are rising?": subtitle, comparison buttons, table, trend line, footnote | `type_trends.json` → `types[]`, `comparisons[]`, `defaultComparison`, `notes`, `currentGames` | M69, M70 |
| Home, The Big Picture | `?` explainers: season-trend, quarter-penalties, week-of-season, penalty-types | `app.js` `EXPLAINERS` (fixed text) | M64, M67, M65, M68; C19 |
| Static `/trends/` | Summary (this season vs all of last season, plays with a flag, biggest increases, fade) | `scoreboard.json` → `frames[season]`, `frames[lastSeason]` (`perGame`, `pctPlays`, `flagEveryPlays`); `type_trends.json` → `types[]`, `weekly.priorAverage[]` | M1, M12, M69, M66; C7 |
| Static `/trends/` | "Penalties per game by season" table and note; "Which penalties are increasing?"; "When are penalties called?" | `type_trends.json` → `seasonCompare[]`, `types[]`, `comparisons[]`, `quarters.all.total` | M64, M69, M67 |
| Static `/trends/` | "Home vs road"; "What penalties cost" | `scoreboard.json` → `frames[season].homeShare`; `crew_styles.json` → `league.homeShare`; `flag_impact.json` | M15, M40; C12; points: M90 |
| Static `/guide/` | "Are NFL penalties up in <season>?", "Do refs call more penalties early in the season?", methodology "Comparisons" | `scoreboard.json` → `frames[season]`, `frames[lastSeason]`; `type_trends.json` → `types[]`, `weekly.priorAverage[]` | M1, M69, M66; C7, C19 |
| `/data/exports/flags_by_season.csv` | `season`, `games`, `flags_per_game_full_season`, `flags_per_game_same_early_weeks` | `type_trends.json` → `seasonCompare[]` | M64 |
| `/data/exports/flags_by_week.csv` | `season`, `week`, `games`, `flags_per_game` | `type_trends.json` → `weekly.seasons[].weeks[]` | M65 |
| `/data/exports/penalty_types_by_season.csv` | `penalty_type`, `season`, `per_game` | `type_trends.json` → `types[].bySeason[]` | M69 |
| (not displayed) | — | `trends.json` → `byQuarterAndType`; `bySeason`, `homeVsAway`, `byType`, `byQuarter` (pipeline and fallback only); `type_trends.json` → `comparisons[].games`, `weekly.priorAverage[].games`, `generatedAt` | M64–M70 notes; conflicts file, "Published but not displayed" |
| Home, Game Previews | Title, group headers, subtitle and crew note, credit line | `previews/latest.json` → `weeks[]`; `previews/<week>` → `week`, `remainingOnly`, `assignments` | M80 |
| Home, Game Previews | Card: matchup, kickoff, network, "Today"; "projected flags · <lo>–<hi> likely"; range bar; badge "vs league"; split bar; "Crew: <name>"; "~<n> penalty yds" | `previews/<week>` → `games[]` (`projection.total`, `.home`, `.away`, `.range`, `.yards`; `crew.name`); `model.leagueAveragePerGame` | M80, M71, M72, M73, M74 |
| Preview pop-up | Tiles "Projected flags", "On <away> (away)", "On <home> (home)", "Chance of <n>+ flags" | `games[].projection` (`total`, `away`, `home`, `range`, `awayRange`, `homeRange`, `awayYards`, `homeYards`, `overThreshold`, `probOver`); `model.leagueAveragePerGame` | M71, M72, M73, M74 |
| Preview pop-up | "What's driving the projection"; "Projected penalties by type"; "⏱️ Quarter by quarter" | `games[].projection.drivers[]`, `games[].byType[]`, `games[].projection.byQuarter[]` | M76, M71, M73, M74, M75 |
| Preview pop-up | "The crew": "Crew effect on this game", "<season> pen/game", type tilts, crew style note, footnote | `games[].crew` (`overallFactor`, `typeTilts`, `gamesInModel`); `season_comparison.json` → `crewChiefs[].current`; `crew_styles.json` | M76, M1, M44 |
| Preview pop-up | "🏈 Team discipline (<season>)" and "Watchlist" | `games[].teams.{home,away}` | M77 |
| Preview pop-up | "Context" chips; "Recent meetings"; model footnote | `games[].context`, `contextReference`, `games[].headToHead[]`, `model.seasons` | M79, M78, M71 |
| Home, Game Previews | "How projections work" explainer | `app.js` `EXPLAINERS['previews']` (fixed text) | M71, M72, M73; C21 |
| Static `/assignments/` | "Projected flags" column; "Projected most flags" summary | `previews/<week>` → `games[].projection.total` | M71 |
| Home (search-engine page source) | Pre-filled previews list ("<away> @ <home>: crew chief <name>, projected <n> flags") | `build_static.py` `home_prefill()` → `PREVIEWS` | M71, M80 |
| Static `/guide/` | "How projections work" | fixed text | M71, M72; C19 |
| (not displayed) | — | `previews/<week>` → `byType[].factors`, `crew.quarterTilt`, `teams.*.gamesInModel`, `projection.leagueAverage`, `.vsLeaguePct`, `headToHead[].gameId`, `context.stadium`, `.homeCoach`, `.awayCoach`, `model.version`, `.seasonWeights`, `.regularSeasonOnly`, `.dispersion`, `assignments.source.name`, `.published`, `generatedAt`; past week files (P4) | M71–M80 notes |
| Home, Game Previews | "Track record" box: "Published before kickoff", "<season − 1> full season (backtest)", "<season> so far (backtest)" ("<n> avg miss · <n>% in range", games), "See every game →" | `scorecard/public.json` → `live.summary`, `backtest.lastSeason`, `backtest.currentSeason` (`season`, `summary.avgMiss`, `.hitRate`, `.games`) | M81, M82, M83 |
| Track Record pop-up | "Week by week": week menu, week stats, game table, footnotes | `history/index.json` → `weeks[]`; `history/<week>` → `summary`, `games[]` (`prediction`, `outcome`, `grade`) | M87, M88, M81 |
| Track Record pop-up | Blocks "Published before kickoff", "<season − 1> full season (backtest)", "<season> so far (backtest)": tiles "Average miss", "In the likely range", "Within ±3 flags", "vs guessing the average" | `scorecard/public.json` → `live.summary`, `backtest.*.summary` | M82, M83, M84, M85 |
| Track Record pop-up | "Every published projection"; "<season> by week (backtest)"; "How it's graded" | `scorecard/public.json` → `live.games[]`, `backtest.currentSeason.byWeek[]`, `definitions` | M86, M82, M83, M81 |
| Static `/guide/` | "How accurate are the penalty projections?" | `scorecard/public.json` → `live.summary` (`avgMiss`, `hitRate`, `games`, `baselineAvgMiss`) | M82, M83, M85; C21, C23 |
| (not displayed) | — | `scorecard/public.json` → `live.byWeek[]`, `backtest.lastSeason.byWeek[]`, `live.games[]` home/away and baseline fields, `generatedAt`; `history/<week>` → most of `prediction`, `outcome`, `grade`, `corrections`, `recordedAt`; `scorecard/live/`, `scorecard/backtest/`, `history/snapshots/` (P5–P7) | M81–M88 notes |
| Home, The Big Picture | "What Flags Cost": subtitle, season buttons, table ("#", "Team", "Points given away / game", "Season total", "Flags", "Key 1st downs given", "Drives stalled", "Big plays erased", "TDs erased", "≈ Wins given away", "Own turnovers erased"), footnote | `flag_impact.json` → `season`, `throughWeek`, `scopes.<scope>` (`season`, `teams[]`) | M97, M90, M92, M93, M94, M91, M95, M89 |
| Home, The Big Picture | "Costliest flags of Week N / <season>", "By points" / "By win chances", footnote | `flag_impact.json` → `week.costliest[]`, `week.costliestWinProb[]`, `scopes.<scope>.costliest[]`, `.costliestWinProb[]` | M96, M89, M91 |
| Team pop-up | "What flags cost <team>": tiles ("Points given away / game", "Key 1st downs given", "Drives stalled / big plays erased", "≈ Wins given away", "Touchdowns erased", "Own turnovers erased"), "Costliest <team> flags this season" | `flag_impact.json` → `scopes.current.teams[]`, `scopes.current.league.pointsCostPerTeamGame`, `teamCostliest.<team>[]` | M90–M96 |
| Static `/team/`, `/team/<ABBR>/`, `/trends/`, `/guide/` | "Points given away / game", "#<n> most costly", "Their flags have cost …", "What penalties cost", "How much does a penalty cost a team?", "How a penalty's cost is measured" | `flag_impact.json` → `scopes.current.teams[]` (`pointsCostPerGame`, `rank`), `scopes.current.league.pointsCostPerTeamGame` | M90, M89; C19, D12 |
| `/gameday/` | Title, subtitle, status ("Connecting…", "updated …"), league tiles, "Costliest flag so far", "Latest flags", game cards (score, flags, yards, projection and pace, "Flags by team", "Flag log"), note | `gameday feed` → `updatedAt`, `week`, `season`, `live`, `games[]`, `costliest[]` | M98, M99, M71 |
| Home, live strip | Tag ("LIVE", "GAMEDAY", "FINAL"), "Week N", "<n> flags", game tiles, "Costliest flag" tile, "Most flags" marker, "Full scoreboard →"; between game weeks: last week's finals | `gameday feed` → `games[]`, `costliest[]`; `history/index.json`, `history/<week>`; `flag_impact.json` → `week.costliestWinProb[]` | M98, M99, M87, M96 |
| Home, update notice and "How is this data collected?" | "New results are in · updated <time>"; "Data is updated weekly …" | `stats.json` → `lastUpdated`; `app.js` `EXPLAINERS['data-methodology']` | M24; D11 |
| (not displayed) | — | `flag_impact.json` → `definitions.*`, `notes`, `generatedAt`, `scopes.<scope>.games`, `.flags`, `.league.*` (except `pointsCostPerTeamGame`), `teams[].firstDownsGiven`, rows' `gameId`, `side`, `yards`, `twoPoint`, `method`, `winProbMethod`, `gainErased`; `wp_tables.json` (worker only); `run_status.json`, `source_stamp.json` (P8, P9); `gameday feed` → `games[].{home,away}.source`, `log[].seq`, `log[].wpMethod`, `preview.low`, `preview.high`, `wpModel`, `source` | M89–M99 notes |
