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
Only the game -> referee facts are stored; no article text is copied.
Source credit/link is stored so the site can attribute Football Zebras.

Usage:
    python scripts/fetch_assignments.py              # next unplayed week
    python scripts/fetch_assignments.py --week 5     # specific week (current season)
    python scripts/fetch_assignments.py --html page.html --week 4   # parse a saved page (testing)
"""

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

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
TIME_RE = re.compile(r'^\d{1,2}(:\d{2})?\s*[ap]\.?m\.?$', re.IGNORECASE)


# -----------------------------------------------------------------------------
# Schedule helpers
# -----------------------------------------------------------------------------

def load_schedule(season: int) -> pd.DataFrame:
    import nflreadpy as nfl
    return nfl.load_schedules([season]).to_pandas()


def next_unplayed_week(schedule: pd.DataFrame):
    """Earliest week with games still to come (skips a week whose only unplayed
    games are today or earlier, e.g. Monday night)."""
    reg = schedule[schedule['game_type'] == 'REG']
    unplayed = reg[reg['result'].isna()]
    if unplayed.empty:
        return None
    today = datetime.now(timezone.utc).date().isoformat()
    for wk in sorted(unplayed['week'].unique()):
        if (unplayed[unplayed['week'] == wk]['gameday'].astype(str) > today).any():
            return int(wk)
    return int(unplayed['week'].max())


# -----------------------------------------------------------------------------
# Football Zebras
# -----------------------------------------------------------------------------

def http_get(url: str) -> str:
    import requests
    r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=TIMEOUT)
    r.raise_for_status()
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
                elif referee and kickoff and network is None and len(ln) <= 40:
                    network = ln
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

def main():
    ap = argparse.ArgumentParser(description='Fetch crew chief assignments from Football Zebras')
    ap.add_argument('--season', type=int, default=datetime.now().year)
    ap.add_argument('--week', type=int)
    ap.add_argument('--html', help='Parse a saved article HTML file instead of fetching (testing)')
    ap.add_argument('--force', action='store_true', help='Refetch even if the week is complete')
    args = ap.parse_args()

    print('\n🦓 Crew assignments (Football Zebras)')
    print('=' * 60)

    schedule = load_schedule(args.season)
    week = args.week or next_unplayed_week(schedule)
    if week is None:
        print('   No unplayed regular-season games. Nothing to do.')
        return 0

    wk = schedule[(schedule['game_type'] == 'REG') & (schedule['week'] == week)].copy()
    out_path = OUT_DIR / f'{args.season}-week-{week:02d}.json'
    print(f'   Target: {args.season} Week {week} ({len(wk)} games)')

    existing = json.loads(out_path.read_text()) if out_path.exists() else None
    if existing and not args.force and not args.html:
        assigned = sum(1 for g in existing.get('games', []) if g.get('referee'))
        if assigned >= len(wk):
            print(f'   ✓ Already have all {assigned} assignments — skipping fetch')
            return 0

    # Known referee names help the parser (from schedule history + overrides)
    known_refs = set(NAME_FIXES.values())
    try:
        import nflreadpy as nfl
        hist = nfl.load_schedules([args.season - 1, args.season]).to_pandas()
        known_refs |= set(hist['referee'].dropna().replace(NAME_FIXES))
    except Exception:
        pass

    source_url, published = None, None
    parsed = []
    try:
        if args.html:
            html = Path(args.html).read_text(encoding='utf-8')
            source_url = args.html
        else:
            source_url, published = find_post_url(http_get(FEED_URL), week, args.season)
            if not source_url:
                print(f'   … Week {week} assignments not posted yet (checked feed)')
                html = None
            else:
                print(f'   ✓ Found post: {source_url}')
                html = http_get(source_url)
        if html:
            parsed = parse_assignments(article_lines(html), known_refs)
            print(f'   ✓ Parsed {len(parsed)} games from article')
    except Exception as e:
        print(f'   ⚠️  Fetch/parse failed: {type(e).__name__}: {e}')

    # Match parsed games to schedule game_ids (order-insensitive for neutral sites)
    by_pair = {}
    for g in parsed:
        by_pair[(g['away'], g['home'])] = g
        by_pair.setdefault((g['home'], g['away']), g)

    overrides = load_overrides(args.season, week)
    games = []
    for _, row in wk.sort_values(['gameday', 'gametime', 'game_id']).iterrows():
        g = by_pair.get((row['away_team'], row['home_team']))
        ref = overrides.get(row['game_id']) or (g['referee'] if g else None)
        prev = next((x for x in (existing or {}).get('games', []) if x['game_id'] == row['game_id']), None)
        if not ref and prev:  # keep an earlier successful parse if this run failed
            ref = prev.get('referee')
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
    unmatched = [f"{g['away']}@{g['home']}" for g in parsed
                 if not any(x['away'] in (g['away'], g['home']) and x['home'] in (g['away'], g['home']) for x in games)]

    result = {
        'season': args.season,
        'week': week,
        'gamesScheduled': len(wk),
        'gamesAssigned': assigned,
        'source': {
            'name': 'Football Zebras',
            'url': source_url if source_url and source_url.startswith('http') else (existing or {}).get('source', {}).get('url'),
            'published': published or (existing or {}).get('source', {}).get('published'),
        },
        'fetchedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'games': games,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))

    print(f'   💾 {out_path.relative_to(PROJECT_DIR)}: {assigned}/{len(wk)} games assigned')
    if unmatched:
        print(f'   ⚠️  Parsed but not on schedule: {", ".join(unmatched)}')
    if parsed and assigned < len(wk):
        missing = [f"{g['away']}@{g['home']}" for g in games if not g['referee']]
        print(f'   ⚠️  Missing: {", ".join(missing)} (add to data/assignments_overrides.csv if needed)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
