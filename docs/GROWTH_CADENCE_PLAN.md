# Growth Cadence Plan: Weekly Content and Indexing

**Goal:** win real-time NFL officiating searches (referee assignments, penalty
projections, team penalty profiles) by publishing faster and with more context
than the large stats databases, on a fixed weekly rhythm tied to the NFL
schedule, and by getting every new page discovered within hours.

**Status:** Phase 0 and Phase 1 are buildable on the current static site
(GitHub Actions + HostGator). Phase 2 is the V2 buildout.

**How to use this doc:** each step lists what it depends on, the files it
touches, its micro-steps, and how to confirm it's done. Steps can be drilled
into further before building.

---

## Contents

1. [Reality checks (read first)](#1-reality-checks-read-first)
2. [The weekly playbook](#2-the-weekly-playbook)
3. [Quality guardrails for every generated page](#3-quality-guardrails-for-every-generated-page)
4. [Phase 0: Prerequisites](#4-phase-0-prerequisites-you-about-1-hour-total)
5. [Phase 1: Build now (current static site)](#5-phase-1-build-now-current-static-site)
6. [Phase 2: V2 buildout](#6-phase-2-v2-buildout)
7. [Dependency map](#7-dependency-map)
8. [Measurement](#8-measurement)
9. [Open decisions](#9-open-decisions)

---

## 1. Reality checks (read first)

These change how the strategy is executed. Each one is reflected in the steps below.

| Assumption in the original strategy | What's actually true | What we do instead |
|---|---|---|
| The NFL releases referee assignments Tuesday morning | The NFL doesn't publish them. Football Zebras reports them, usually Tuesday 9–10am PT, sometimes Wednesday | Poll Football Zebras every 30 min on Tuesday and Wednesday; publish the hub within minutes of their post |
| Force-submit URLs to Google daily via API | Google's Indexing API is only for job postings and livestream events; using it for other pages violates its guidelines. Search Console's "Request indexing" is manual and limited (roughly 10/day) | **IndexNow** pings on every deploy (Bing, which feeds ChatGPT search and Copilot, plus Yandex, Seznam, Naver); accurate sitemap `lastmod`; RSS feed; manual Search Console requests for the 3–5 most important new pages each week |
| Tag high-profile analysts and beat writers on every post | Mass tagging reads as spam and can get the account limited | Reply with a relevant chart under their posts, tag only when the post is about their team or their own work, quote-post with value |
| Narratives like "Novak flags away teams 12% more often" | Only true if the data supports it at a meaningful size; home/road splits are sensitive | Narratives are built only from facts that pass the site's thresholds, framed as patterns, never motives |
| Monday morning recap of the week | Monday Night Football isn't played until Monday night | Monday edition (Sunday games), Tuesday final edition (adds MNF) |
| Publish lots of programmatic pages | Google penalizes "scaled content" that adds no unique value | Every template has a content minimum; pages that don't meet it aren't published |

---

## 2. The weekly playbook

All times Pacific; cron times in UTC (PT + 7 during daylight time, + 8 in winter).

| When (PT) | Run | Publishes | Cron (UTC, DST) |
|---|---|---|---|
| **Tue 6:00am** | Post-MNF data update | Recap **final** edition (adds MNF), team-week pages final, scorecard grades | existing `0 6 * * 2` runs 11pm Mon PT; add `0 13 * * 2` |
| **Tue 9:00am–6:00pm, every 30 min** | Assignment watch | **Weekly Referee Assignment Hub** the moment Football Zebras posts | `*/30 16-23 * * 2` and `*/30 0-1 * * 3` (6pm PT is 1am UTC Wednesday) |
| **Wed 7:00am–3:00pm, every 30 min** | Assignment watch (backstop) | Same, if posted late | `*/30 14-22 * * 3` |
| **Thu 6:00am** | Preview drop | **Game preview pages** for the week, refreshed projections | `0 13 * * 4` |
| **Fri 10:00am** | Social pack | Weekly image pack + captions (style map, assignment card, most-flagged-projections card) | `0 17 * * 5` |
| **Sat 6:00am** | Late-change sweep | Re-check assignments (crew swaps), refresh previews | `0 13 * * 6` |
| **Sun 9:00pm** | Sunday night refresh | Recap **early** (once nflverse posts Sunday play-by-play, else skipped) | `0 4 * * 1` |
| **Mon 6:00am** | Recap drop | **Week [N] Officiating Report Card** (Sunday games) + team-week pages | `0 13 * * 1` |
| **Every day 7:00am** | Daily run | **Fact of the Day** on /live/, sitemap dates, IndexNow ping | `0 14 * * *` |

GitHub Actions minutes are free for public repositories, so frequent runs cost nothing.

---

## 3. Quality guardrails for every generated page

These apply to every template in Phase 1 and Phase 2. A page that fails them is not published.

1. **Accurate:** every number comes from that run's data files; no number is typed into a template.
2. **Meaningful:** traits, splits and "X% more" claims only appear when they pass the site's thresholds (5% volume, 3 points for shares, 15% for a penalty type) and minimum samples (crew: 3+ games this season; team: 2+).
3. **Patterns, not motives:** never "biased," "targets," "rigged." Home/road splits always carry the crowd-noise caveat.
4. **Content minimum:** a preview page needs a crew assignment or a team profile with 2+ games; a team-week page needs the game to be final; otherwise it isn't generated (no thin pages).
5. **Unique per page:** each page has a different title, description, H1, TL;DR and at least three page-specific facts.
6. **Self-linking:** every page links to its hub, the relevant crew/team pages, `/dataset/` and `/guide/` (see 5.8).
7. **Dated:** visible "Updated [date]" and `dateModified` in schema; `lastmod` in the sitemap only changes when the content does.
8. **Small samples labeled:** early-season numbers say how many games they're based on.

---

## 4. Phase 0: Prerequisites (you, about 1 hour total)

**Depends on:** the static pages update (`feature/seo-static`) being merged and live.

### 0.1 Google Search Console (15 min)

1. Go to search.google.com/search-console → **Add property** → **Domain** → `nflobservatory.com`.
2. Copy the TXT record shown.
3. In Cloudflare: **DNS** → **Records** → **Add record** → Type **TXT**, Name **@**, Content = the copied value → **Save**.
4. Back in Search Console → **Verify** (can take a few minutes).
5. **Sitemaps** → enter `sitemap.xml` → **Submit**.
6. **Done when:** Sitemaps shows "Success."

### 0.2 Bing Webmaster Tools (5 min)

1. Go to bing.com/webmasters → sign in.
2. **Import from Google Search Console** → select `nflobservatory.com` → **Import**.
3. **Done when:** the site appears with the sitemap listed.

### 0.3 IndexNow key (5 min, needed for step 5.7)

1. I generate the key file in the build (step 5.7); you don't create it by hand.
2. After step 5.7 deploys, open `nflobservatory.com/<key>.txt` and confirm it shows the key.
3. In Bing Webmaster Tools → **IndexNow** → confirm submissions appear after the next deploy.

### 0.4 Decide X posting mode (decision, see section 9)

- **Manual** (free): the pipeline produces images + captions; you post.
- **Scheduled** (Buffer or similar, ~$6/mo): you queue the pack Friday.
- **Automated** (X API paid tier): the pipeline posts itself. Check current X API pricing before choosing.

### 0.5 Accounts list for engagement (20 min)

1. Make a list of ~30 accounts: national NFL analysts, fantasy analysts, betting analysts, one or two beat writers per team, officiating accounts (Football Zebras).
2. Save it as a private X list named "Observatory engagement."
3. **Done when:** the list exists. It's used for replies in step 5.9, not mass tags.

---

## 5. Phase 1: Build now (current static site)

**Order:** 5.1 → 5.2 → (5.3, 5.4, 5.5, 5.6 in any order) → 5.7 → 5.8 → 5.9 → 5.10. Step 5.11 (backlinks) runs alongside, from now on.

**Already done (foundation, live):** static crawlable pages for every crew chief and team, assignments, trends, guide/FAQ and dataset; schema markup; robots.txt welcoming AI crawlers; sitemap; llms.txt; home page summary; home page sections pre-filled with real numbers in the HTML source (the app replaces them on load); permanent redirects from descriptive URLs that people and AI tools guess (`/referee-stats/`, `/team-penalty-stats/`, `/penalty-trends/`, `/full-data/`, `/faq/`, and others) to the real pages.

### 5.1 Workflow schedule and run modes

**Depends on:** nothing. **Files:** `.github/workflows/update-data.yml`, `scripts/update_data.py`.

1. Add the crons from section 2 to the workflow.
2. Add a `MODE` environment variable set from the schedule (`assignments`, `previews`, `recap`, `social`, `daily`, `full`).
3. `assignments` mode: run `fetch_assignments.py` only; if no new assignments, exit without deploying (so 30-minute polling doesn't redeploy unchanged files).
4. `daily` mode: skip the heavy play-by-play reload; rebuild only static pages, Fact of the Day, sitemap and IndexNow.
5. Add a concurrency guard so two runs never overlap (already present; confirm it covers all modes).
6. **Done when:** the Actions tab shows each mode running on schedule, and unchanged assignment polls end with "No new assignments" in under 2 minutes.

### 5.2 Permanent weekly URLs (archive structure)

**Depends on:** 5.1. **Files:** `scripts/build_static.py`.

1. Keep the "latest" pages (`/assignments/`, `/recap/`) and add permanent week URLs:
   - `/assignments/2026-week-07/`
   - `/previews/2026-week-07/` (week index) and `/previews/2026-week-07/kc-at-buf/` (per game)
   - `/recap/2026-week-07/`
   - `/team/DAL/2026-week-07/`
2. "Latest" pages show the current week and link to every past week (archive list).
3. Past weeks are rebuilt from the history ledger, so they never break.
4. Canonical: each week page is its own canonical; the latest page canonicalizes to itself (not a duplicate, since it changes weekly).
5. **Done when:** all past 2026 weeks have working permanent URLs in the sitemap.

### 5.3 Tuesday: Weekly Referee Assignment Hub

**Depends on:** 5.1, 5.2. **Files:** `scripts/build_static.py`, `scripts/narratives.py` (new).

1. **Title pattern:** "NFL Referee Assignments Week 7 2026: Crew Chief for Every Game."
2. **Top of page:** TL;DR (how many games assigned, the most flag-heavy crew this week, the biggest crew-vs-team mismatch).
3. **Top 5 games get a 3-sentence narrative**, ranked by projected flags and public interest (primetime first):
   1. Sentence 1, the assignment: "Scott Novak's crew has Chiefs at Bills (Sunday, 4:25pm ET, CBS)."
   2. Sentence 2, the crew's strongest fact that passes the guardrails: e.g. "His crew is calling 22.4 flags a game in 2026, 49% above the league and nearly double his 2020–25 rate."
   3. Sentence 3, the matchup angle: the team fact that interacts with the crew fact: e.g. "Kansas City has drawn the most defensive holding calls in the AFC, a call Novak's crew makes 18% more often than average."
4. **Narrative engine** (`narratives.py`): a library of ~20 fact templates, each with a data check (threshold, sample size) and priority. It picks the highest-priority facts that pass for each crew and team, never repeats a fact twice on a page, and logs which templates fired.
5. **Every other game:** one row in a table (game, time, TV, crew chief, crew rate, style, projected flags).
6. **Per-crew deep links** to `/crew/<slug>/`, per-team links to `/team/<abbr>/`.
7. **Schema:** `ItemList` of `SportsEvent` (each with `referee`-style description text), `BreadcrumbList`, `FAQPage` ("Who is refereeing the Chiefs game this week?" per top game).
8. **Done when:** the hub publishes within one polling cycle (30 min) of Football Zebras posting, with 5 narratives that pass the guardrails.

### 5.4 Thursday: Game preview pages

**Depends on:** 5.2, 5.3. **Files:** `scripts/build_static.py`.

1. **Week index title:** "NFL Referees for Week 7: Holding Calls & Penalty Projections."
2. **Per-game title:** "Chiefs vs Bills Referee & Penalty Projection: Week 7 2026."
3. **Structure (bullets, for featured snippets):**
   - Crew chief and his 2026 / career rate
   - Projected flags (range, chance of 15+)
   - Most likely calls (top 3 penalty types with projected counts)
   - Each team's discipline (rank, flags per game, most common call)
   - Last meeting's flags
4. **Dedicated holding section** (high-volume query): projected offensive holding for each team and the crew's holding rate vs league.
5. **FAQ:** "Who is the referee for Chiefs vs Bills?", "How many penalties are expected in Chiefs vs Bills?"
6. **Schema:** `SportsEvent` (homeTeam, awayTeam, startDate, location) + `FAQPage`.
7. **Done when:** all games with an assigned crew have a page Thursday 6am PT; TNF's page exists before kickoff.

### 5.5 Monday / Tuesday: Officiating Report Card

**Depends on:** 5.2, the history ledger. **Files:** `scripts/build_static.py`.

1. **Title:** "Week 7 NFL Officiating Report Card: Most Penalized Teams & Biggest Calls."
2. **Sections:**
   1. Headline numbers (flags per game, vs season, vs same week last year)
   2. Most and least flagged teams this week
   3. Tightest- and loosest-called games
   4. **Biggest deviations from history** (crew or team far from its normal, passing guardrails)
   5. Costliest flags of the week (from flag impact)
   6. Projections vs actual (track record for the week)
3. **Monday edition** at 6am (Sunday games) labeled "MNF pending"; **Tuesday final** replaces it.
4. **Done when:** both editions publish on schedule; the Tuesday edition shows "Final."

### 5.6 Monday: Team-week pages

**Depends on:** 5.5. **Files:** `scripts/build_static.py`.

1. **Title:** "Dallas Cowboys Penalty Breakdown: Week 7 2026."
2. **Content:** every flag on the team (quarter, time, type, player, yards, what it changed), compared with its season average, what the flags cost, the crew, the opponent's flags.
3. Links: team profile, game recap, crew page, report card.
4. Generated only for completed games (guardrail 4).
5. **Done when:** 26–32 pages per week (bye weeks excluded), each with unique facts.

### 5.7 Index signaling: sitemap dates, IndexNow, RSS

**Depends on:** 5.2. **Files:** `scripts/build_static.py`, `scripts/indexnow.py` (new), workflow.

1. **Sitemap index:** split into `sitemap-core.xml` (hubs, crews, teams), `sitemap-weekly.xml` (this season's week pages), `sitemap-archive.xml` (past seasons). `sitemap.xml` becomes the index.
2. **Accurate `lastmod`:** store a hash of each page's content; only change `lastmod` when the hash changes.
3. **IndexNow:**
   1. Generate a key once (stored as a GitHub secret `INDEXNOW_KEY`) and publish `/<key>.txt`.
   2. After each deploy, POST the list of changed URLs (from step 2) to `api.indexnow.org/indexnow`.
   3. Log the response code in the Actions output.
4. **RSS feed** `/feed.xml`: the 30 most recent hub, preview, recap and fact entries (title, link, date, summary). Linked from every page head.
5. **Manual Google requests** (you, 5 min weekly): Search Console → **URL inspection** → paste the new week's assignment hub, preview index and report card → **Request indexing.**
6. **Done when:** Bing Webmaster shows IndexNow submissions after each deploy, and Search Console shows the sitemap index with all three child sitemaps.

### 5.8 Internal linking

**Depends on:** 5.3–5.6. **Files:** `scripts/build_static.py`.

1. **Every new page links to:** `/dataset/` (with keyword anchor text, e.g. "full NFL penalty database"), `/guide/`, `/trends/`, the relevant crew and team pages.
2. **Hubs link back:** `/crew/`, `/team/`, `/trends/`, `/dataset/` each get a "Latest" box with the current assignment hub, report card, previews and Fact of the Day.
3. **Crew and team pages** link to their most recent week pages ("This week: Novak's crew has Chiefs at Bills").
4. **Footer** on every page: links to this week's hub and report card.
5. **Done when:** a crawl of the built site (script check) shows no orphan pages and every page reachable within 3 clicks of the home page.

### 5.9 Daily: Fact of the Day and /live/

> **Source of facts:** the [Stat Miner](STAT_MINER.md) (live). Its weekly report already ranks and luck-filters candidates; this step adds a daily pick from it, the novelty log (Stat Miner Phase 2.5) and the public page.

**Depends on:** 5.1, `narratives.py` (5.3). **Files:** `scripts/facts.py` (new), `scripts/build_static.py`.

1. **Candidate facts** from the week's data: crew streaks ("5 roughing-the-passer calls in his last 2 games"), team streaks, rare events, record-setting games, rising penalty types, projection hits.
2. **Rank** by unusualness (how far from normal, adjusted for sample size) using the shift/anomaly logic from the roadmap.
3. **Never repeat** a fact within 30 days (store published facts in `frontend/data/facts/log.json`).
4. **Publish** to `/live/` (today's fact + the last 30, permanent URL per fact `/live/2026-10-21/`), the home page summary, and the RSS feed.
5. **Done when:** a new, verified fact appears every morning.

### 5.10 Friday: X amplification pack

**Depends on:** the social generator (existing), 5.3, 5.4. **Files:** `scripts/social/generate.py`, `scripts/social/captions.py`.

1. **Pack (generated Friday 10am PT, saved to `social/output/week-NN/`):**
   1. Crew Chief Style Map (this season, vs last season's averages)
   2. Assignment card: the 5 most flag-heavy matchups with crews
   3. Team discipline map
2. **Captions** link to the exact sub-page (assignment hub, a specific preview, a crew page) with UTM tags (`utm_source=x&utm_medium=social&utm_campaign=week-07`).
3. **Engagement routine (you, 15 min Friday + 10 min Sunday):**
   1. Post the pack.
   2. From the "Observatory engagement" list, reply under 3–5 relevant posts with the matching chart (e.g. a Bills beat writer's post → reply with the Bills preview card).
   3. Tag accounts only when the post is about their team or cites their work.
4. **Done when:** the pack is in `social/output/` every Friday with captions and UTM links.

### 5.11 Backlinks (ongoing, you + me)

**Depends on:** nothing. The biggest lever against established sites, and the one code can't do.
In order of payoff:

1. **Dataset listings (one time, 45 min):**
   1. **Kaggle:** kaggle.com → **Datasets** → **New Dataset** → upload the five CSVs from `nflobservatory.com/dataset/` → title "NFL Penalties by Referee (Crew Chief), Team and Week, 2020–2026" → in the description, link `https://nflobservatory.com/dataset/` and credit nflverse → **Create**. Update monthly (Kaggle → dataset → **New Version**).
   2. **data.world:** same files and description.
   3. **Done when:** both listings are public and link back.
2. **nflverse community (one time, 15 min):** post in nflverse's GitHub Discussions ("Show and tell") and Discord: a short "built with nflverse" note with one chart and the `/dataset/` link. The data comes from them, so it's on-topic.
3. **Story-driven outreach (when a story breaks, 15 min each):**
   1. When a finding is newsworthy (e.g. Novak's crew, the pre-snap rise), send a 3-sentence note to 3–5 relevant writers: the finding, one number, the page that backs it up.
   2. Officiating writers (Football Zebras), analytics writers, team beat writers for the teams involved.
   3. Track who responds in a simple list so follow-ups go to warm contacts.
4. **Reddit and X (weekly):** link the specific page (crew page, report card, preview) rather than the home page; r/nfl for league stories, team subreddits for team stories. Answer comments; link the guide when asked about methodology.
5. **Measure:** Search Console → **Links** shows new referring sites; check monthly.

---

## 6. Phase 2: V2 buildout

> The full V2 architecture, tool choices and migration sequence are in the [V2 Build Plan](V2_BUILD_PLAN.md). The items below are the growth-specific pieces of V2.

**Depends on:** Phase 1 running for at least 4 weeks (so there's traffic data to prioritize with).

### 6.1 Clean URLs for the interactive app

1. Replace hash links (`/#crew=scott-novak`) with real routes (`/crew/scott-novak/`) served as pre-rendered HTML that the app then enhances.
2. One URL per entity for people *and* crawlers; the static and interactive versions merge.
3. 301 redirects from every old hash link pattern (handled in the app on load).

### 6.2 Hosting move for speed and indexing

1. Move from HostGator FTP to Cloudflare Pages (or Workers): global CDN, instant deploys, preview builds per pull request.
2. Turn on **Cloudflare Crawler Hints**, which sends IndexNow pings automatically when content changes.
3. Track Core Web Vitals (speed is a ranking factor) in Search Console.

### 6.3 Data backend

1. Database (the roadmap's R2 + Parquet + DuckDB warehouse, or Postgres) as the single source for every page.
2. Public read-only API (JSON) for journalists and developers; listed on `/dataset/`.

### 6.4 Real-time assignment ingestion

1. Watch Football Zebras' RSS every 5 minutes (instead of 30) via a scheduled Worker.
2. Publish the assignment hub and post to X within 10 minutes of their post.
3. Alert on crew swaps after publication.

### 6.5 Narrative engine v2

1. LLM-written narratives constrained to verified facts: the model only rewrites facts the data engine supplies, a checker confirms every number in the output matches the data, and anything unverifiable is rejected.
2. Human review queue for the top 5 narratives each week (optional, 10 min).

### 6.6 Automated anomaly engine

> Now planned in detail as [Stat Miner](STAT_MINER.md) Phase 3 (pattern finding) and Phase 4 (publishing loop).

1. Shift detection (control charts) for every crew and team, plus the anomaly finder from the roadmap.
2. Feeds Fact of the Day, report cards, alerts, and X posts.

### 6.7 Social automation

1. X API posting (if the paid tier is chosen), Threads/Bluesky cross-posting.
2. Per-team auto-posts (each team's preview card the day before its game) for team-specific search and social demand.

### 6.8 Newsletter

1. Tuesday "Assignments" and Monday "Report Card" emails, auto-built from the same pages.
2. Email traffic is another fresh-engagement signal.

### 6.9 "Ask the Observatory"

1. Plain-English questions over all data, generating SQL and charts (from the roadmap).
2. Saved queries become public, indexable pages when shared (each a unique long-tail answer).

### 6.10 Expanded structured data

1. `SportsEvent` for every game (past and upcoming), `Dataset` per downloadable file, `ClaimReview`-style fact pages for widely shared claims about officiating.

---

## 7. Dependency map

```
Phase 0  ── 0.1 Search Console ─┐
            0.2 Bing ───────────┤
            0.3 IndexNow check ─┤ (after 5.7 deploys)
            0.4 X mode ─────────┼──────────────────────────────► 5.10
            0.5 Engagement list ┘──────────────────────────────► 5.10

Phase 1  5.1 Schedule & modes
           └► 5.2 Weekly URLs
                ├► 5.3 Assignment hub (+ narratives.py) ─┬► 5.4 Previews
                │                                         └► 5.9 Fact of the Day
                ├► 5.5 Report card ─► 5.6 Team-week pages
                └► 5.7 Sitemaps, IndexNow, RSS
           5.3–5.6 ─► 5.8 Internal linking
           5.3, 5.4 ─► 5.10 X pack

Phase 2  (after 4+ weeks of Phase 1)
         6.1 Clean URLs ─► 6.2 Cloudflare Pages ─► 6.4 Real-time ingestion
         6.3 Backend ─► 6.9 Ask the Observatory
         6.6 Anomaly engine ─► 6.5 Narratives v2 ─► 6.7 Social automation ─► 6.8 Newsletter
```

**Suggested build order for Phase 1 sessions:**

| Session | Steps | Result |
|---|---|---|
| 1 | 5.1, 5.2, 5.7 | Schedule, permanent week URLs, IndexNow + RSS + sitemap index |
| 2 | 5.3 (+ `narratives.py`) | Tuesday assignment hub with narratives |
| 3 | 5.4 | Thursday preview pages |
| 4 | 5.5, 5.6 | Monday/Tuesday report card + team-week pages |
| 5 | 5.8, 5.9 | Internal linking + Fact of the Day |
| 6 | 5.10 | Friday X pack |

---

## 8. Measurement

| Metric | Where | Target after 8 weeks |
|---|---|---|
| Indexed pages | Search Console → Pages | 90%+ of sitemap URLs |
| Impressions for "nfl referee week N" queries | Search Console → Performance → Queries | Top 10 position |
| Clicks from search | Search Console | Week-over-week growth |
| Time from Football Zebras post to hub live | Actions logs | Under 30 min (Phase 1), under 10 (Phase 2) |
| Referral clicks from X | Cloudflare analytics + UTM | Growth each week |
| AI assistant referrals (chatgpt.com, perplexity.ai, claude.ai) | Cloudflare analytics → Referrers | Growth each week |
| Bing IndexNow accepted submissions | Bing Webmaster → IndexNow | Every deploy |

Weekly review (you, 10 min, Tuesday): check the queries that gained impressions and tell me; I'll adjust titles and FAQ questions to match.

---

## 9. Open decisions

1. **X posting mode:** manual, scheduled (Buffer), or automated (X API paid tier).
2. **Narrative tone:** strictly factual (default), or a slightly more editorial voice for the top 5 games.
3. **Report card grades:** letter grades per crew are shareable but invite "the refs got an F" headlines; recommendation is no letter grades for officials, only "most/least flags vs normal."
4. **Data license** on `/dataset/` (currently CC BY 4.0).
5. **Hosting move timing** for Phase 2 (Cloudflare Pages).
