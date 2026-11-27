"""Gameday archive (#193): save each week's final gameday state, once.

The gameday worker's /live response covers ESPN's current week only and keeps
nothing. This step, run by the data workflow, saves a week once every game in it is
final:

    nflobs-raw  espn/gameday/<season>/week-NN.json      the full /live response (private)
    frontend/data/gameday/<season>-week-NN.json          our own summary (published)

ESPN data is terms-restricted (docs/DATA_SOURCES.md section 10): the full copy stays
in the private bucket; the published file holds only facts we derive from it: the
teams, final score, flags and yards per team, accepted flags by type, and one line of
our own per flag ("Q3 4:12 · CHI · Defensive Holding · T.Edwards · 10 yds"). It never
copies a feed field as-is beyond those facts, and never ESPN's play text or win
probability.

Rules:
- Complete: every game is final (state "post", not postponed or canceled). A
  postponed game holds the week open; a manual run (--week N) saves the final games
  and marks the postponed one.
- Regular season only: the feed's games must match the nflverse schedule's
  regular-season games of that season and week (teams and Eastern date). Playoff
  games, or games that match nothing, save nothing.
- Written once: the R2 write is conditional (If-None-Match: *). If the R2 copy
  already exists, the published file is built from that stored copy. The published
  file is written only after the R2 copy is safe, so a failed run retries both.

Test hooks (ignored in GitHub Actions, like raw_capture.py's):
    NFLOBS_RAW_STORE_DIR=<folder>   a local folder in place of the bucket
Use --dry-run to build everything and write nothing.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import raw_capture
from jsonsafe import atomic_write, dumps

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'frontend' / 'data' / 'gameday'
LIVE_URL = 'https://nflobs-gameday.tfostery.workers.dev/live'
USER_AGENT = 'nflobservatory.com gameday archive'
R2_KEY = 'espn/gameday/{season}/week-{week:02d}.json'
NOT_PLAYED = re.compile(r'postpon|cancel|suspend', re.I)
# Feed team codes -> ours. Mirrors ALIAS in worker/gameday/parse.js, plus ARZ (#206: ESPN's
# play text codes Arizona as ARZ). A safety net: kept even once the worker maps them all.
FEED_TEAM = {'ARZ': 'ARI', 'WSH': 'WAS', 'LAR': 'LA', 'JAC': 'JAX', 'OAK': 'LV', 'SD': 'LAC', 'STL': 'LA'}
SOURCE_NOTE = ("NFL Officiating Observatory summary of ESPN's live game feed: scores, flags and yards "
               "per team, and one line per flag. ESPN's play text is not included.")


def log(msg: str) -> None:
    print(f'Gameday archive: {msg}', flush=True)


def warn(msg: str) -> None:
    log(msg)
    if raw_capture.in_actions():
        print(f'::warning title=Gameday archive::{msg}', flush=True)


# ---- the rules ---------------------------------------------------------------

def not_played(game: dict) -> bool:
    """Postponed, canceled or suspended (ESPN marks these 'post' too)."""
    return bool(NOT_PLAYED.search(game.get('detail') or ''))


def week_status(live: dict) -> dict:
    """How many of the week's games are final, and which ones aren't played."""
    games = live.get('games') or []
    final = [g for g in games if g.get('state') == 'post' and not not_played(g)]
    postponed = [g for g in games if not_played(g)]
    unfinished = [g for g in games if g not in final and g not in postponed]
    return {'total': len(games), 'final': len(final), 'postponed': postponed, 'unfinished': unfinished,
            'complete': bool(games) and len(final) == len(games)}


def eastern_date(iso: str) -> str:
    import pandas as pd
    return str(pd.Timestamp(iso).tz_convert('America/New_York').date())


def match_schedule(live: dict, schedule) -> tuple[str, str]:
    """('regular', '') if every feed game is a regular-season game of the feed's season
    and week in the nflverse schedule; ('postseason', why) if they're all playoff
    games; ('nomatch', why) otherwise. Teams must match; the Eastern date too, except
    for a postponed game (its date may move)."""
    season, week = live.get('season'), live.get('week')
    sched = schedule[schedule['season'] == season]
    types, problems = set(), []
    for g in live.get('games') or []:
        away, home = (g.get('away') or {}).get('abbr'), (g.get('home') or {}).get('abbr')
        rows = sched[(sched['away_team'] == away) & (sched['home_team'] == home)]
        if not not_played(g) and g.get('start'):
            rows = rows[rows['gameday'].astype(str) == eastern_date(g['start'])]
        if rows.empty:
            problems.append(f'{away} @ {home} not in the {season} schedule')
            continue
        row = rows.iloc[0]
        types.add(row['game_type'])
        if row['game_type'] == 'REG' and int(row['week']) != week:
            problems.append(f'{away} @ {home} is Week {int(row["week"])}, feed says Week {week}')
    if not live.get('games'):
        return 'nomatch', 'feed has no games'
    if types and 'REG' not in types and not problems:
        return 'postseason', ', '.join(sorted(types))
    if problems or types != {'REG'}:
        return 'nomatch', '; '.join(problems) or f'mixed game types {sorted(types)}'
    return 'regular', ''


# ---- the published file -------------------------------------------------------

def flag_line(f: dict) -> str:
    """'Q3 4:12 · CHI · Defensive Holding · T.Edwards · 10 yds' from the parsed facts."""
    q = f.get('qtr')
    when = ' '.join(x for x in ((('OT' if q == 5 else f'OT{q - 4}') if isinstance(q, int) and q >= 5
                                 else f'Q{q}' if q else ''), f.get('clock') or '') if x)
    status = f.get('status')
    if status in ('declined', 'offsetting'):
        result = status
    else:
        y = int(f.get('yards') or 0)
        result = f'{y} yd' if y == 1 else f'{y} yds'
    parts = [when, f.get('team') or '', f.get('type') or '', f.get('player') or '', result]
    return ' · '.join(p for p in parts if p)


def _team(t: dict, by_type: dict) -> dict:
    """Score, flags and yards (box score). typeNotIdentified: accepted flags in the box score
    that the play text didn't give a type for, so acceptedByType plus it equals flags.
    Left out when there's no gap."""
    out = {'abbr': t.get('abbr'), 'score': int(t.get('score') or 0),
           'flags': int(t.get('flags') or 0), 'yards': int(t.get('yards') or 0)}
    gap = out['flags'] - sum(by_type.get(out['abbr'], {}).values())
    if gap > 0:
        out['typeNotIdentified'] = gap
    return out


def build_public(live: dict, saved_at: str) -> dict:
    """Our own summary of the week. Built from an explicit list of fields, so nothing
    else in the feed (play text, win probability, wall clock) can reach it."""
    games = []
    for g in sorted(live.get('games') or [], key=lambda g: (g.get('start') or '', str(g.get('id')))):
        # the feed is newest first; copies, so the feed (and the R2 copy) keep their codes
        log_ = [dict(f, team=FEED_TEAM.get(f.get('team'), f.get('team'))) for f in reversed(g.get('log') or [])]
        away, home = (g.get('away') or {}).get('abbr'), (g.get('home') or {}).get('abbr')
        for code in sorted({f.get('team') for f in log_} - {away, home}, key=str):
            warn(f'{away} @ {home} has a flag under unknown team code {code}')
        by_type = {}
        for f in log_:
            if f.get('status') == 'accepted':
                counts = by_type.setdefault(f.get('team'), {})
                counts[f.get('type')] = counts.get(f.get('type'), 0) + 1
        games.append({
            'id': str(g.get('id')), 'start': g.get('start'),
            'status': 'postponed' if not_played(g) else 'final' if g.get('state') == 'post' else 'not final',
            'away': _team(g.get('away') or {}, by_type), 'home': _team(g.get('home') or {}, by_type),
            'acceptedByType': {t: dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
                               for t, c in sorted(by_type.items())},
            'flagLines': [flag_line(f) for f in log_],
        })
    return {'season': live.get('season'), 'week': live.get('week'), 'savedAt': saved_at,
            'feedUpdatedAt': live.get('updatedAt'), 'source': SOURCE_NOTE, 'games': games}


def public_path(season: int, week: int) -> Path:
    return OUT_DIR / f'{season}-week-{week:02d}.json'


# ---- R2 ------------------------------------------------------------------------

def make_store():
    """(client, why_not): the bucket, a local test folder, or None with the reason."""
    store_dir = raw_capture._test_hook('NFLOBS_RAW_STORE_DIR')
    if store_dir:
        return raw_capture.LocalStore(store_dir), ''
    missing = [n for n in raw_capture.ENV_NAMES if not os.environ.get(n)]
    if missing:
        return None, f'no R2 credentials ({", ".join(missing)})'
    try:
        return raw_capture.make_client(), ''
    except Exception as e:
        return None, raw_capture.short(e)


def store_raw(client, key: str, body: bytes) -> tuple[str, bytes]:
    """Write once. ('new', body) if written; ('exists', stored) if already there."""
    try:
        client.put_object(Bucket=raw_capture.BUCKET, Key=key, Body=body, IfNoneMatch='*',
                          ContentType='application/json')
        return 'new', body
    except Exception as e:
        if raw_capture.error_code(e) not in ('PreconditionFailed', '412'):
            raise
    return 'exists', client.get_object(Bucket=raw_capture.BUCKET, Key=key)['Body'].read()


# ---- inputs ----------------------------------------------------------------------

def fetch_live(url: str = LIVE_URL) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Origin': 'https://nflobservatory.com'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def load_schedule(season: int):
    import nflreadpy as nfl
    from teams import normalize_teams
    return normalize_teams(nfl.load_schedules([season]).to_pandas())


# ---- run -------------------------------------------------------------------------

def _report_sizes(live, raw, now, final):
    """Dry run: sizes of the two files as they'd be written from this /live state."""
    saved_at = (now or datetime.now(timezone.utc)).isoformat(timespec='seconds')
    size = len(dumps(build_public(live, saved_at), ensure_ascii=False).encode())
    games = len(live.get('games') or [])
    flags = sum(len(g.get('log') or []) for g in live.get('games') or [])
    log(f'dry run sizes from this /live ({final} of {games} games final, {flags} flags listed): '
        f'R2 copy {len(raw):,} bytes; published file {size:,} bytes')


def run(raw: bytes, schedule_loader=load_schedule, want_week=None, dry_run=False, store=None, now=None) -> int:
    """0 = done (saved, already saved, or nothing to save yet); 1 = a problem worth a warning."""
    live = json.loads(raw)
    season, week = live.get('season'), live.get('week')
    if not isinstance(season, int) or not isinstance(week, int):
        warn('/live has no season or week; nothing saved')
        return 1
    if want_week is not None and week != want_week:
        warn(f'/live shows Week {week}, not Week {want_week}; nothing saved')
        return 1
    out = public_path(season, week)
    if out.exists():
        log(f'Week {week} already saved')
        return 0

    st = week_status(live)
    manual = want_week is not None
    if not st['complete']:
        if st['unfinished'] or not manual:
            log(f"Week {week} not complete ({st['final']} of {st['total']} final"
                + (f", {len(st['postponed'])} postponed" if st['postponed'] else '') + ')')
            prev = public_path(season, week - 1)
            started = any(g.get('state') != 'pre' for g in live.get('games') or [])
            if not started and week > 1 and not prev.exists():
                warn(f'Week {week - 1} missed: /live already shows Week {week}')
            if dry_run:
                _report_sizes(live, raw, now, st['final'])
            return 0
        log(f"manual run: saving {st['final']} final games, {len(st['postponed'])} marked postponed")

    kind, why = match_schedule(live, schedule_loader(season))
    if kind == 'postseason':
        warn(f'postseason not supported yet ({why}); nothing saved')
        return 1
    if kind != 'regular':
        warn(f"feed games don't match the schedule ({why}); nothing saved")
        return 1

    saved_at = (now or datetime.now(timezone.utc)).isoformat(timespec='seconds')
    key = R2_KEY.format(season=season, week=week)
    if dry_run:
        log(f'dry run: Week {week} would be saved')
        _report_sizes(live, raw, now, st['final'])
        return 0

    client, why_not = store if store is not None else make_store()
    if client is None:
        warn(f'R2 unavailable ({why_not}); nothing saved, the next run tries again')
        return 1
    try:
        result, stored = store_raw(client, key, raw)
    except Exception as e:
        warn(f'R2 write failed ({raw_capture.short(e)}); nothing saved, the next run tries again')
        return 1
    if result == 'exists':
        log(f'R2 copy {key} already existed; the published file is built from it')
        live = json.loads(stored)
    text = dumps(build_public(live, saved_at), ensure_ascii=False)
    atomic_write(out, text + '\n')
    log(f'Week {week} saved ({out.relative_to(ROOT).as_posix()}, {len(text.encode()):,} bytes; R2 {key})')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--week', type=int, help='manual run: save this week (must be the week /live shows)')
    ap.add_argument('--dry-run', action='store_true', help='build everything, write nothing')
    ap.add_argument('--live-file', help='read /live from this file instead of the worker (local testing)')
    a = ap.parse_args(argv)
    try:
        raw = Path(a.live_file).read_bytes() if a.live_file else fetch_live()
    except Exception as e:
        warn(f'could not read /live ({type(e).__name__}: {str(e)[:150]}); nothing saved')
        return 1
    return run(raw, want_week=a.week, dry_run=a.dry_run)


if __name__ == '__main__':
    sys.exit(main())
