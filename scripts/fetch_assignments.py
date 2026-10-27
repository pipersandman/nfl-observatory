#!/usr/bin/env python3
"""
Fetch upcoming crew chief assignments from Football Zebras.
===========================================================
1. Find the next NFL week with unplayed games (nflverse schedule).
2. Read the Football Zebras "Assignments" RSS feed and find the post tagged
   "Week N, YYYY" for that week.
3. Fetch that one article and parse "Away at Home" / "Away vs. Home" + referee.
4. Apply manual overrides from data/assignments_overrides.csv.
5. Write frontend/data/assignments/{season}-week-{NN}.json

Polite by design: one feed request + one article request per run, an
identifying User-Agent, and no refetch once every game in the week is assigned.
Only the game -> referee facts are published; no article text is published.
Source credit/link is stored so the site can attribute Football Zebras.
Raw capture (#88): the feed and the article page are kept exactly as received in
the private R2 bucket nflobs-raw (never published), so they can be re-parsed;
see scripts/raw_capture.py. A capture problem is a warning, never exit 2.

Usage:
    python scripts/fetch_assignments.py              # next unplayed regular-season week
    python scripts/fetch_assignments.py --week 5     # specific week (season the default would pick)
    python scripts/fetch_assignments.py --season 2027 --week 1

Season (#84): by default the next upcoming regular-season games across nflverse's
current season and, when later, the calendar year (scripts/seasons.py). January
finds Week 18 of the season in progress; August finds next season's Week 1 once
its schedule is out. Playoff games are never fetched.
    python scripts/fetch_assignments.py --html page.html --week 4   # parse a saved page (testing)

Exit codes (the workflow step is allowed to fail, so these never block the data run):
    0  fetched, week already complete, or not posted yet (normal until 2 days before kickoff)
    2  fetch or parse failed, the post had no games, or the week's first game kicked off
       with no post found
Problems also print a ::warning:: line when running in GitHub Actions.
"""

import argparse
import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

import raw_capture
from seasons import nflverse_current_season, schedule_seasons

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUT_DIR = PROJECT_DIR / 'frontend' / 'data' / 'assignments'
OVERRIDES = PROJECT_DIR / 'data' / 'assignments_overrides.csv'

FEED_URL = 'https://www.footballzebras.com/category/assignments/feed/'
USER_AGENT = 'NFLOfficiatingObservatory/1.0 (+https://nflobservatory.com; weekly crew-assignment check)'
TIMEOUT = 20

# Team nicknames as Football Zebras writes them -> nflverse abbreviations
NICKNAMES = {
    'cardinals': 'ARI', 'falcons': 'ATL', 'ravens': 'BAL', 'bills': 'BUF',
    'panthers': 'CAR', 'bears': 'CHI', 'bengals': 'CIN', 'browns': 'CLE',
    'cowboys': 'DAL', 'broncos': 'DEN', 'lions': 'DET', 'packers': 'GB',
    'texans': 'HOU', 'colts': 'IND', 'jaguars': 'JAX', 'chiefs': 'KC',
    'rams': 'LA', 'chargers': 'LAC', 'raiders': 'LV', 'dolphins': 'MIA',
    'vikings': 'MIN', 'patriots': 'NE', 'saints': 'NO', 'giants': 'NYG',
    'jets': 'NYJ', 'eagles': 'PHI', 'steelers': 'PIT', '49ers': 'SF',
    'niners': 'SF', 'seahawks': 'SEA', 'buccaneers': 'TB', 'bucs': 'TB',
    'titans': 'TEN', 'commanders': 'WAS',
}

NAME_FIXES = {
    'Ronald Torbert': 'Ron Torbert',
    'Adrian Hall': 'Adrian Hill',
}

MATCHUP_RE = re.compile(r'^\s*([A-Za-z0-9]+)\s+(at|vs\.?|@)\s+([A-Za-z0-9]+)\s*$', re.IGNORECASE)
NAME_RE = re.compile(r"^[A-Z][a-zA-Z'.\-]+(?:\s+[A-Z][a-zA-Z'.\-]+){1,2}$")
SAFE_NETWORK_RE = re.compile(r"^[A-Za-z0-9 +&./'-]{1,40}$")
TIME_RE = re.compile(r'^\d{1,2}(:\d{2})?\s*[ap]\.?m\.?$', re.IGNORECASE)

# "Not posted yet" becomes a warning this close to the week's first kickoff. Football
# Zebras usually posts Tuesday ~9am PT; 2 days before a Thursday opener is Tuesday evening.
WARN_BEFORE_KICKOFF = timedelta(days=2)


def problem(problems: list, kind: str, message: str) -> None:
    """Record a 'fail' (exit 2) or 'warn' (exit 0) and show it on the Actions run page."""
    problems.append((kind, message))
    if os.environ.get('GITHUB_ACTIONS'):
        print(f'::warning title=Crew assignments::{message}')


def first_kickoff(wk: pd.DataFrame):
    """Earliest kickoff of the week, US Eastern (schedule gameday + gametime)."""
    from zoneinfo import ZoneInfo
    times = []
    for _, r in wk.iterrows():
        t = r.get('gametime') if isinstance(r.get('gametime'), str) and r.get('gametime') else '00:00'
        try:
            times.append(datetime.fromisoformat(f"{r['gameday']} {t}").replace(tzinfo=ZoneInfo('America/New_York')))
        except (TypeError, ValueError):
            continue
    return min(times) if times else None


# -----------------------------------------------------------------------------
# Schedule helpers
# -----------------------------------------------------------------------------

def load_schedule(seasons: list[int]) -> pd.DataFrame:
    import nflreadpy as nfl
    df = nfl.load_schedules(seasons)
    raw_capture.get('fetch_assignments').capture_frame(
        'nflverse-schedules', f'games_{min(seasons)}-{max(seasons)}', df)
    return df.to_pandas()


def upcoming_weeks(schedule: pd.DataFrame, today=None) -> list[int]:
    """Weeks to cover in one season's schedule: the earliest regular-season week with
    games still to come (US Eastern date, so Monday night stays 'upcoming' all
    evening), plus the next week when the current one is already partly played.
    Playoff games are ignored. `today` (a date) defaults to today in US Eastern."""
    from zoneinfo import ZoneInfo
    reg = schedule[schedule['game_type'] == 'REG']
    today_et = (today or datetime.now(ZoneInfo('America/New_York')).date()).isoformat()
    up = reg[reg['result'].isna() & (reg['gameday'].astype(str) >= today_et)]
    if up.empty:
        return []
    weeks = sorted(int(w) for w in up['week'].unique())
    first = weeks[0]
    out = [first]
    if len(up[up['week'] == first]) < len(reg[reg['week'] == first]) and len(weeks) > 1:
        out.append(weeks[1])
    return out


def select_weeks(schedule: pd.DataFrame, seasons: list[int], today=None):
    """(season, weeks) for the first of `seasons` with regular-season games still to
    come, or (None, []). In January that's Week 18 of the season in progress; in
    August, once next season's schedule is out, its Week 1."""
    for season in seasons:
        weeks = upcoming_weeks(schedule[schedule['season'] == season], today)
        if weeks:
            return season, weeks
    return None, []


# -----------------------------------------------------------------------------
# Football Zebras
# -----------------------------------------------------------------------------

def http_get(url: str, source: str | None = None, name: str | None = None) -> str:
    """GET a page; with source/name, also keep the exact bytes in raw capture."""
    import requests
    r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=TIMEOUT)
    r.raise_for_status()
    if source:
        is_xml = 'xml' in (r.headers.get('Content-Type') or '') or source.endswith('feed')
        raw_capture.get('fetch_assignments').capture_bytes(
            source, name, r.content, 'xml' if is_xml else 'html',
            'application/xml' if is_xml else 'text/html', url, encoding=r.encoding)
    return r.text


def find_post_url(feed_xml: str, week: int, season: int):
    """Return (url, published) for the item tagged 'Week N, YYYY'."""
    want_cat = f'week {week}, {season}'
    want_slug = f'week-{week}-referee-assignments-{season}'
    root = ET.fromstring(feed_xml)
    for item in root.iter('item'):
        link = (item.findtext('link') or '').strip()
        cats = [(c.text or '').strip().lower() for c in item.findall('category')]
        if want_cat in cats or want_slug in link:
            return link, (item.findtext('pubDate') or '').strip()
    return None, None


def article_lines(html: str) -> list[str]:
    """Visible text lines of the article body (falls back to the whole page)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    body = (soup.select_one('#mvp-content-main') or soup.select_one('.entry-content')
            or soup.select_one('article') or soup)
    text = body.get_text('\n')
    return [ln.strip() for ln in text.split('\n') if ln.strip()]


def parse_assignments(lines: list[str], known_refs: set[str]) -> list[dict]:
    """
    Walk the text looking for 'Team at Team' (or 'vs.') followed within a few
    lines by a referee name. Works whether the post is a table or plain lines.
    """
    games = []
    i = 0
    while i < len(lines):
        m = MATCHUP_RE.match(lines[i])
        if m and m.group(1).lower() in NICKNAMES and m.group(3).lower() in NICKNAMES:
            away, home = NICKNAMES[m.group(1).lower()], NICKNAMES[m.group(3).lower()]
            neutral = not m.group(2).lower().startswith('at') and m.group(2) != '@'
            referee, kickoff, network = None, None, None
            j = i + 1
            while j < len(lines) and j <= i + 5 and not MATCHUP_RE.match(lines[j]):
                ln = lines[j]
                cand = NAME_FIXES.get(ln, ln)
                if referee is None and (cand in known_refs or NAME_RE.match(cand)):
                    referee = cand
                elif kickoff is None and TIME_RE.match(ln):
                    kickoff = ln
                elif referee and kickoff and network is None and len(ln) <= 40 and SAFE_NETWORK_RE.match(ln):
                    network = ln   # only plain network names (letters/numbers/+/&/./-/space) are kept
                j += 1
            if referee:
                games.append({'away': away, 'home': home, 'neutral': neutral,
                              'referee': referee, 'kickoff': kickoff, 'network': network})
            i = j
            continue
        i += 1
    return games


def load_overrides(season: int, week: int) -> dict:
    """data/assignments_overrides.csv: game_id,referee  (e.g. 2026_05_TB_DAL,Shawn Smith)"""
    out = {}
    if OVERRIDES.exists():
        with open(OVERRIDES, newline='') as f:
            for row in csv.DictReader(f):
                gid = (row.get('game_id') or '').strip()
                ref = (row.get('referee') or '').strip()
                if gid.startswith(f'{season}_{week:02d}_') and ref:
                    out[gid] = ref
    return out


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def process_week(season: int, week: int, schedule: pd.DataFrame, known_refs: set,
                 get_feed, html_override: str | None = None, force: bool = False) -> list:
    """Fetch, parse and save one week. Returns the problems found: [(kind, message)],
    kind 'fail' (exit 2) or 'warn'."""
    problems = []
    wk = schedule[(schedule['game_type'] == 'REG') & (schedule['week'] == week)].copy()
    out_path = OUT_DIR / f'{season}-week-{week:02d}.json'
    print(f'   Target: {season} Week {week} ({len(wk)} games)')

    existing = json.loads(out_path.read_text()) if out_path.exists() else None
    if existing and not force and not html_override:
        assigned = sum(1 for g in existing.get('games', []) if g.get('referee'))
        if assigned >= len(wk):
            print(f'   ✓ Already have all {assigned} assignments — skipping fetch')
            return problems

    source_url, published = None, None
    parsed = []
    try:
        if html_override:
            html = Path(html_override).read_text(encoding='utf-8')
            source_url = html_override
        else:
            source_url, published = find_post_url(get_feed(), week, season)
            if not source_url:
                print(f'   … Week {week} assignments not posted yet (checked feed)')
                html = None
                # Judge "not posted yet" against the week's first kickoff
                from zoneinfo import ZoneInfo
                kick = first_kickoff(wk)
                now = datetime.now(ZoneInfo('America/New_York'))
                if kick and now >= kick:
                    msg = (f'Week {week}: first game kicked off {kick:%a %Y-%m-%d %H:%M} ET '
                           f'without published assignments')
                    print(f'   ⚠️  {msg}')
                    problem(problems, 'fail', msg)
                elif kick and kick - now <= WARN_BEFORE_KICKOFF:
                    msg = f'Week {week} assignments not posted yet, first game {kick:%a %Y-%m-%d %H:%M} ET'
                    print(f'   ⚠️  {msg}')
                    problem(problems, 'warn', msg)
            else:
                print(f'   ✓ Found post: {source_url}')
                html = http_get(source_url, 'footballzebras-post', f'{season}-week-{week:02d}')
        if html:
            parsed = parse_assignments(article_lines(html), known_refs)
            print(f'   ✓ Parsed {len(parsed)} games from article')
            if not parsed:
                msg = f'Week {week}: found the post but parsed 0 games (page layout may have changed)'
                print(f'   ⚠️  {msg}')
                problem(problems, 'fail', msg)
    except Exception as e:
        print(f'   ⚠️  Fetch/parse failed: {type(e).__name__}: {e}')
        problem(problems, 'fail', f'Week {week}: fetch/parse failed: {type(e).__name__}: {e}')

    by_pair = {}
    for g in parsed:
        by_pair[(g['away'], g['home'])] = g
        by_pair.setdefault((g['home'], g['away']), g)

    overrides = load_overrides(season, week)
    games = []
    for _, row in wk.sort_values(['gameday', 'gametime', 'game_id']).iterrows():
        g = by_pair.get((row['away_team'], row['home_team']))
        prev = next((x for x in (existing or {}).get('games', []) if x['game_id'] == row['game_id']), None)
        ref = overrides.get(row['game_id']) or (g['referee'] if g else None) or (prev or {}).get('referee')
        games.append({
            'game_id': row['game_id'],
            'away': row['away_team'],
            'home': row['home_team'],
            'referee': ref,
            'source': 'override' if row['game_id'] in overrides else ('footballzebras' if g else (prev or {}).get('source')),
            'kickoff': g.get('kickoff') if g else (prev or {}).get('kickoff'),
            'network': g.get('network') if g else (prev or {}).get('network'),
        })

    assigned = sum(1 for g in games if g['referee'])
    scheduled_pairs = {(x['away'], x['home']) for x in games} | {(x['home'], x['away']) for x in games}
    unmatched = [f"{g['away']}@{g['home']}" for g in parsed if (g['away'], g['home']) not in scheduled_pairs]

    prev_src = (existing or {}).get('source', {})
    result = {
        'season': season,
        'week': week,
        'gamesScheduled': len(wk),
        'gamesAssigned': assigned,
        'source': {
            'name': 'Football Zebras',
            'url': source_url if source_url and source_url.startswith('http') else prev_src.get('url'),
            'published': published or prev_src.get('published'),
        },
        'fetchedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'games': games,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(f'   💾 {out_path.relative_to(PROJECT_DIR)}: {assigned}/{len(wk)} games assigned')
    if unmatched:
        print(f'   ⚠️  Parsed but not on schedule: {", ".join(unmatched)}')
        problem(problems, 'warn', f'Week {week}: parsed but not on schedule: {", ".join(unmatched)}')
    if parsed and assigned < len(wk):
        missing = [f"{g['away']}@{g['home']}" for g in games if not g['referee']]
        print(f'   ⚠️  Missing: {", ".join(missing)} (add to data/assignments_overrides.csv if needed)')
        problem(problems, 'warn', f'Week {week}: missing crews for {", ".join(missing)}')
    return problems


def main():
    ap = argparse.ArgumentParser(description='Fetch crew chief assignments from Football Zebras')
    ap.add_argument('--season', type=int,
                    help="Season to use (default: the next upcoming regular-season games across "
                         "nflverse's current season and, when later, the calendar year)")
    ap.add_argument('--week', type=int, help='Specific week (default: the next unplayed week)')
    ap.add_argument('--html', help='Parse a saved article HTML file instead of fetching (testing)')
    ap.add_argument('--force', action='store_true', help='Refetch even if the week is complete')
    args = ap.parse_args()

    print('\n🦓 Crew assignments (Football Zebras)')
    print('=' * 60)

    seasons = [args.season] if args.season else schedule_seasons()
    schedule = load_schedule(seasons)
    season, weeks = select_weeks(schedule, seasons)
    if args.week:
        # --week alone: the season the default would pick, else nflverse's current season
        season = args.season or season or nflverse_current_season()
        weeks = [args.week]
    if not weeks:
        print('   No upcoming regular-season games. Nothing to do.')
        return 0
    schedule = schedule[schedule['season'] == season]

    problems = []
    known_refs = set(NAME_FIXES.values())
    try:
        import nflreadpy as nfl
        hist_pl = nfl.load_schedules([season - 1, season])
        raw_capture.get('fetch_assignments').capture_frame(
            'nflverse-schedules', f'games_{season - 1}-{season}', hist_pl)
        hist = hist_pl.to_pandas()
        known_refs |= set(hist['referee'].dropna().replace(NAME_FIXES))
    except Exception as e:
        # Parsing still works (any "First Last" line counts as a name), just less strictly
        msg = f'known-referee list failed to load ({type(e).__name__}: {e}); parsing with a shorter list'
        print(f'   ⚠️  {msg}')
        problem(problems, 'warn', msg)

    feed_cache = {}
    def get_feed():   # fetched at most once per run, and only if a week needs it
        if 'xml' not in feed_cache:
            feed_cache['xml'] = http_get(FEED_URL, 'footballzebras-feed', 'assignments_feed')
        return feed_cache['xml']

    for week in weeks:
        problems += process_week(season, week, schedule, known_refs, get_feed, args.html, args.force)

    fails = [m for k, m in problems if k == 'fail']
    if fails:
        print(f'\n   FAILED ({len(fails)}): ' + '; '.join(fails))
        return 2
    return 0


def run():
    """main(), then hand this step's raw captures to update_data.py (same workflow run)."""
    try:
        return main()
    finally:
        raw_capture.get('fetch_assignments').save_handoff()


if __name__ == '__main__':
    sys.exit(run())
