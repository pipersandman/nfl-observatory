# Data Sources and Data Lake Design

**Goal:** one data lake that combines every useful source on games, plays,
players, teams, officials, betting markets, weather and context into the most
valuable single source of NFL officiating data, with clear provenance and
licensing for every row.

**Related docs:** [V2 Build Plan](V2_BUILD_PLAN.md) (V2.0 data platform, Q0 data
additions) · [Data & Modeling Roadmap](DATA_AND_MODELING_ROADMAP.md).

**Coverage years** are as each source publishes them at the time of writing (October 2026); verify each when ingesting.

**Status key:** **In use** (already ingested) · **P0** (add now, free, high value)
· **P1** (add in V2.0/Q0) · **P2** (later / research) · **P3** (premium, only if
justified) · **Avoid** (terms or quality make it unsuitable).

---

## Contents

1. [Catalog: games, plays and teams](#1-catalog-games-plays-and-teams)
2. [Catalog: players](#2-catalog-players)
3. [Catalog: officials](#3-catalog-officials)
4. [Catalog: betting markets](#4-catalog-betting-markets)
5. [Catalog: weather, venues and travel](#5-catalog-weather-venues-and-travel)
6. [Catalog: rules, discipline and context](#6-catalog-rules-discipline-and-context)
7. [Catalog: tracking and charting](#7-catalog-tracking-and-charting)
8. [Catalog: attention and media signals](#8-catalog-attention-and-media-signals)
9. [Catalog: premium commercial (optional)](#9-catalog-premium-commercial-optional)
10. [Licensing rules for the lake](#10-licensing-rules-for-the-lake)
11. [Data lake design](#11-data-lake-design)
12. [Identity: joining everything](#12-identity-joining-everything)
13. [Ingestion plan](#13-ingestion-plan)

---

## 1. Catalog: games, plays and teams

| Source | Contents | Coverage | Access | License / terms | Status |
|---|---|---|---|---|---|
| **nflverse play-by-play** (`load_pbp`) | Every play: down, distance, field position, play type, penalty fields (team, type, yards, player), EPA, WPA, drive results, replay/challenge flags, play description text | 1999 → current | nflreadpy (Python), Parquet releases on GitHub | nflverse-data repository license CC BY 4.0 (attribution) | **In use** (2015+, all seven officials begin); 1999–2014 available if ever needed |
| **nflverse schedules** (`load_schedules`) | Game id, date, time, weekday, home/away, scores, overtime, roof, surface, temperature/wind (outdoor), rest days, division game, **closing spread, total and moneylines**, stadium, ESPN/PFR game ids, referee | 1999 → current | nflreadpy | CC BY 4.0 | **In use**; closing lines **P0** (already in the file, not yet used) |
| **nflverse team stats** (`load_team_stats`) | Team-level weekly stats | 1999 → current | nflreadpy | CC BY 4.0 | **P0** |
| **nflverse teams** (`load_teams`) | Team metadata, abbreviation history, colors, logos | All | nflreadpy | CC BY 4.0 | **P0** (team crosswalk) |
| **NFL official gamebooks** | Official game summary PDFs: full officials list, every penalty **including declined and offsetting**, inactive players, weather, attendance, scoring summary | Recent seasons on NFL.com / NFL Football Operations | PDF download, parse | NFL terms of use; personal/analysis use; don't republish PDFs | **P1** (only source for declined/offsetting penalties at full fidelity) |
| **ESPN site/core API** | Scoreboard, game summaries (officials, injuries, odds snapshot, broadcast network), team schedules, rosters, news | Current + recent seasons | Undocumented JSON endpoints (`site.api.espn.com`) | Unofficial and undocumented; can change without notice | **P1** as a *cross-check and fallback*, never the only source |
| **Pro Football Reference** | Game, team, player and official pages; official game logs | 1920 → current | Website | Sports Reference data-use and bot-traffic policies restrict automated collection; custom datasets can be purchased | **Avoid** scraping; **P3** purchase a custom dataset if needed |

## 2. Catalog: players

| Source | Contents | Coverage | Access | License / terms | Status |
|---|---|---|---|---|---|
| **nflverse players** (`load_players`) | Master player table and cross-ids (GSIS, ESPN, PFR, PFF, Sportradar…); v2 is sourced from ESPN | All | nflreadpy | CC BY 4.0 | **P0** (player crosswalk) |
| **nflverse rosters** (`load_rosters`, weekly) | Team, position, jersey, status by week | 1920 / 2002 → current | nflreadpy | CC BY 4.0 | **P0** |
| **nflverse depth charts** | Weekly depth charts | 2001 → current | nflreadpy | CC BY 4.0 | **P1** (backup OL/CB as features) |
| **nflverse injuries** | Weekly injury reports and game status | 2009 → current | nflreadpy | CC BY 4.0 | **P0** (Q0 item 4) |
| **nflverse snap counts** (PFR) | Offensive/defensive/special-teams snaps per player per game | 2012 → current | nflreadpy | CC BY 4.0 via nflverse | **P0** (penalties per snap) |
| **nflverse player stats** | Weekly offense/defense/kicking stats | 1999 → current | nflreadpy | CC BY 4.0 | **P1** |
| **nflverse contracts** (Over The Cap) | Contracts, cap hits, guarantees | Historical | nflreadpy | via nflverse | **P2** (veteran vs rookie, "star treatment" research) |
| **nflverse draft picks / combine / trades** | Draft position, combine measurements, trades | Decades | nflreadpy | via nflverse | **P2** |
| **nflverse PFR advanced stats** | Pressures, blitzes, drops, broken tackles | 2018 → current | nflreadpy | via nflverse | **P2** |
| **ESPN QBR** (nflverse) | QB quality | 2006 → current | nflreadpy | via nflverse | **P2** |

## 3. Catalog: officials

| Source | Contents | Coverage | Access | License / terms | Status |
|---|---|---|---|---|---|
| **nflverse officials** (`load_officials`) | All **seven officials per game** with positions | Recent seasons | nflreadpy | CC BY 4.0 | **In use** for the referee; **P0** ingest all seven positions (Q0 item 2) |
| **Football Zebras weekly assignments** | Crew chief per game, published before kickoff (usually Tuesday) | Current seasons | Website / RSS | Editorial site; light, polite fetching; attribute | **In use** |
| **Football Zebras crew rosters** | Every crew's seven officials, years of experience, previous crew, college, occupation, replay staff, swing officials | Yearly (e.g. 2026: 121 officials, 17 crews, 2 swing officials) | Website, one page per season | Attribute; small yearly snapshot | **P0** (crew composition changes, experience) |
| **Football Zebras news** | Crew swaps, injuries to officials, retirements, promotions, rule explainers | Ongoing | RSS | Attribute; link rather than copy | **P1** (event log; Claude extracts structured events) |
| **NFL Football Operations** | Official roster announcements, officiating staff, promotions to referee, rule explanations | Yearly / ongoing | operations.nfl.com | NFL terms | **P1** (authoritative roster check) |
| **Officiating discipline news** | Suspensions and discipline of officials (e.g. two officials suspended in October 2026; the referees' union challenging it) | Event-based | News (Front Office Sports, PFT, Football Zebras) | Facts only; link sources | **P1** (event log: availability changes, crew changes) |
| **Gamebooks** (see section 1) | Officials list per game | Recent | PDF | NFL terms | **P1** (cross-check) |

## 4. Catalog: betting markets

| Source | Contents | Coverage | Access | Cost | Status |
|---|---|---|---|---|---|
| **nflverse schedules** | **Closing** spread, total, moneylines | 1999 → current | nflreadpy | Free | **P0** |
| **The Odds API** | Live and historical odds snapshots; featured markets (moneyline, spreads, totals) from June 2020 at 10-minute intervals, 5-minute from September 2022; player props and period markets from May 2023 | 2020 → current | JSON API | Historical endpoints require a paid plan | **P1** (primary candidate for line history; decision D5) |
| **SportsGameOdds / OddsPapi / TheRundown** | Odds across many books, props, alternate lines, line movement history | Varies | JSON APIs | Free tiers + paid | **P1** alternatives / second source for D5 |
| **Kaggle "NFL scores and betting data"** (spreadspoke) and similar | Historical spreads and totals for decades | 1966/1979 → recent | CSV download | Free; community-maintained (check each dataset's license) | **P2** (long-history backtests only; validate against nflverse closing lines) |

## 5. Catalog: weather, venues and travel

| Source | Contents | Coverage | Access | License / terms | Status |
|---|---|---|---|---|---|
| **Open-Meteo historical weather** (ERA5) | Hourly temperature, wind, gusts, precipitation, humidity at any coordinates; gap-free | 1940 → present (5-day delay) | Free JSON API | Data CC BY 4.0 with attribution; free API for non-commercial use (<10,000 calls/day); commercial use needs a paid plan | **P0** (actual game-time weather for every outdoor game) |
| **Open-Meteo historical forecast archive** | What the forecast *said* before kickoff | 2021 → present | Free JSON API | Same as above | **P0** (the correct pre-game feature for models: no lookahead) |
| **NOAA ISD / Meteostat** | Station observations | Decades | Free | Public domain (NOAA) | **P2** (cross-check) |
| **nflverse schedules** | Stadium id, roof, surface | 1999 → current | nflreadpy | CC BY 4.0 | **In use** |
| **Stadium coordinates** (Wikidata / OpenStreetMap) | Latitude/longitude, altitude, time zone per stadium | All | SPARQL / download | CC0 (Wikidata), ODbL (OSM) | **P0** (one small table; needed for weather and travel) |
| **Computed travel** | Distance traveled, time-zone change, short weeks, international games | From schedules + coordinates | Computed | Ours | **P0** (Q0 item 6) |

## 6. Catalog: rules, discipline and context

| Source | Contents | Coverage | Access | Status |
|---|---|---|---|---|
| **NFL rulebook and rule changes by year** | Rules, enforcement, yearly changes (e.g. kickoff rules) | Yearly | operations.nfl.com | **P1** (our own `rule_changes` timeline table, curated) |
| **Points of emphasis** | Officiating emphasis each season (e.g. illegal shift, holding) | Yearly | NFL Football Operations, media coverage | **P1** (text → features via Claude; Q0 item 5) |
| **Player fines** | Fines by player, type, amount | Ongoing | Public trackers (e.g. Spotrac) and league announcements | **P2** (only from sources whose terms allow use) |
| **Replay and challenges** | Reviews, overturns | 1999 → current | nflverse play-by-play replay fields | **P1** |
| **Coaching staffs** | Head coach and coordinators by team-season | Decades | nflverse schedules (head coaches) + curated | **P2** (coaching discipline research) |

## 7. Catalog: tracking and charting

| Source | Contents | Coverage | Access | License / terms | Status |
|---|---|---|---|---|---|
| **Next Gen Stats aggregates** (nflverse `load_nextgen_stats`) | Weekly passing, rushing, receiving tracking-derived stats | 2016 → current | nflreadpy | via nflverse | **P2** |
| **FTN charting** (nflverse `load_ftn_charting`) | Manually charted play details | 2022 → current | nflreadpy | **CC BY-SA 4.0**, credit "FTN Data via nflverse" | **P1** |
| **Participation** (nflverse `load_participation`) | Players on the field per play, formation, personnel | NGS-era seasons; FTN provides 2023+ after each season ends | nflreadpy | 2023+ is **CC BY-SA 4.0** (FTN) | **P1** (who was on the field when a flag was thrown) |
| **NFL Big Data Bowl** (Kaggle) | Raw player tracking (x/y, speed, acceleration) for selected games; 2027 edition pairs Combine tracking with in-game tracking | Small samples per competition | Kaggle | Competition rules govern use | **P2** research only; check each year's rules before any use beyond the competition |

## 8. Catalog: attention and media signals

| Source | Contents | Access | Use | Status |
|---|---|---|---|---|
| **Google Trends** | Search interest by topic and region | Website / unofficial libraries | Which teams, crews and calls people care about this week (content priority) | **P2** |
| **Wikipedia pageviews** | Daily pageviews for teams, players, officials | Free API | Same, plus spikes after controversies | **P2** |
| **Reddit API** | Posts and comments (r/nfl, team subs) | Free tier with limits | Detect officiating controversies early; community feedback | **P2** (respect API terms) |
| **Our own analytics** | Search Console queries, Cloudflare/Plausible traffic | Exports | What users search for → FAQ and titles | **P1** |

## 9. Catalog: premium commercial (optional)

Only if a specific product need or research result justifies the cost.

| Source | What it adds | Notes |
|---|---|---|
| **Sportradar / Stats Perform / SportsDataIO** | Official real-time feeds, officials, injuries, odds | Expensive; commercial licensing |
| **PFF** | Player grades, charting | Paid; strict redistribution limits |
| **Sports Reference custom datasets** | Clean historical tables (including officials) | Purchase instead of scraping |
| **Commercial weather** | Station-level stadium observations | Open-Meteo is usually enough |

---

## 10. Licensing rules for the lake

1. **Every row carries `source`, `license`, `fetched_at` and `source_version`.** Public exports filter by license automatically.
2. **CC BY 4.0 sources** (nflverse core, Open-Meteo data): free to publish derived data with attribution. Our public `/dataset/` (CC BY 4.0) may include these.
3. **CC BY-SA 4.0 sources** (FTN charting, 2023+ participation): anything *derived from them* that we publish must also be CC BY-SA and credit "FTN Data via nflverse". **Keep FTN-derived columns out of the CC BY exports**, or publish them as a separate CC BY-SA file.
4. **Terms-restricted sources** (NFL gamebooks, ESPN, Football Zebras, odds APIs): use internally for analysis; publish our *own derived statistics*, never the raw data or documents; attribute where facts come from.
5. **Odds data:** most odds APIs prohibit redistributing raw odds. Keep raw lines private; publish only our derived findings.
6. **Open-Meteo:** the free API is for non-commercial use. If the site ever becomes commercial (ads, subscriptions), switch to a paid Open-Meteo plan.
7. **Don't scrape sites whose terms forbid it** (Sports Reference). Buy data instead.

## 11. Data lake design

Built on the V2.0 platform (Cloudflare R2 + DuckDB + dbt + Dagster).

| Zone | Where | What | Rules |
|---|---|---|---|
| **Raw** (live since #88) | `r2://nflobs-raw/raw/<source>/<YYYY-MM-DD>/<name>_<HHMMSS>Z_<sha8>.<ext>`, plus one manifest per run in `raw/_runs/<YYYY-MM-DD>/<HHMMSS>Z_<run id>.json` | Exactly what each source returned: tables as zstd Parquet (the frame the pipeline used), pages as the exact bytes received, gzip-compressed (`.html.gz`, `.xml.gz`). An unchanged file isn't stored again; the run's manifest points to the existing copy | Append-only (conditional writes, never overwritten or deleted); private bucket, never published. Written by `scripts/raw_capture.py`; any past run is rebuilt with `scripts/rebuild_from_raw.py`. Sources today: `nflverse-pbp`, `nflverse-schedules`, `nflverse-officials`, `nflverse-teams`, `footballzebras-feed`, `footballzebras-post` |
| **Staging** | DuckDB (dbt `staging/`) | Cleaned, typed, renamed to our conventions; one model per source dataset | IDs mapped to canonical ids (section 12); duplicates removed; provenance columns kept |
| **Core** | DuckDB (dbt `core/`) | Canonical tables: `games`, `plays`, `penalties` (accepted, declined, offsetting), `officials`, `game_officials` (all seven), `crews`, `players`, `teams`, `rosters`, `injuries`, `snaps`, `odds_snapshots`, `weather_hourly`, `weather_forecast`, `stadiums`, `travel`, `rule_changes`, `events` (discipline, swaps) | One definition of every entity; tested |
| **Marts** | DuckDB (dbt `marts/`) | What the site, API, models and Ask the Observatory read: crew/team/player season and week summaries, projections, ledger, flag impact, crew styles | Metric definitions live here (the semantic layer) |
| **Exports** | R2 public bucket / `/dataset/` | Public CSV/Parquet by license | Generated from marts with license filters |

**Snapshots:** slowly changing data (rosters, crews, injuries, odds) keeps every version with `valid_from`/`valid_to`, so any past moment can be reconstructed ("what did we know before kickoff?").

## 12. Identity: joining everything

The value of the lake comes from joining sources reliably. Canonical ids:

| Entity | Canonical id | Crosswalk from |
|---|---|---|
| Game | nflverse `game_id` (e.g. `2026_05_SF_SEA`) | nflverse schedules carry `old_game_id` (GSIS), `espn` and `pfr` ids; odds providers matched by date + teams, then verified |
| Play | `game_id` + `play_id` | nflverse; FTN/participation share these keys |
| Team | nflverse team abbreviation per season | `load_teams` handles relocations (OAK→LV, SD→LAC, STL→LA) |
| Player | `gsis_id` | `load_players` maps ESPN, PFR, PFF, Sportradar and others |
| Official | Our own `official_id` | Built from name + uniform number + position, with an alias table for spelling variants (the pipeline already fixes "Ronald Torbert" → "Ron Torbert"); Football Zebras rosters and nflverse officials matched to it |
| Crew | `season` + crew chief `official_id` | Crew membership by game from `game_officials` |
| Stadium | nflverse `stadium_id` | Wikidata ids for coordinates |
| Odds event | Provider event id | Mapped to `game_id`; mismatches flagged by a test |

**Tests that protect identity:** every play maps to a game; every game has exactly seven officials once nflverse publishes them; every penalty player id maps to a player or is flagged; every odds event maps to exactly one game.

## 13. Ingestion plan

### P0: add now (free; fits the current pipeline, then moves to Dagster)

1. ~~Extend history~~ Done: the site now covers **2015 onward** (season-adjusted career comparisons). 1999–2014 remains available.
2. **Closing lines** from schedules (spread, total, moneylines) into the history ledger and models.
3. **All seven officials** per game, plus the yearly **Football Zebras crew rosters** (experience, previous crew).
4. **Players, rosters, injuries, snap counts** (penalties per snap; backup players).
5. **Weather:** stadium coordinates table; Open-Meteo hourly weather for every outdoor game since 1999; historical *forecasts* since 2021.
6. **Travel:** distance, time zones, short weeks.

**Done when:** each new table has tests, provenance columns, and appears in a nightly row-count report.

### P1: with V2.0 and Q0

1. **Odds line history** (decision D5: The Odds API or an alternative): openers, movement and props.
2. **Gamebooks:** download and parse for declined/offsetting penalties and the official officials list.
3. **FTN charting and participation** (with CC BY-SA handling).
4. **Event log:** Football Zebras news and discipline news turned into structured events by Claude, reviewed before use.
5. **Rule changes and points of emphasis** timeline.
6. **ESPN** summaries as a cross-check (officials, injuries).

### P2: research and content

Next Gen Stats aggregates, PFR advanced stats, contracts, draft/combine, coaching staffs, attention signals (Google Trends, Wikipedia pageviews, Reddit), Big Data Bowl samples (within competition rules), long-history betting datasets.

### P3: premium, only if justified

Sportradar/SportsDataIO/Stats Perform feeds, PFF, Sports Reference custom datasets.
