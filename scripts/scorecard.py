"""
Prediction scorecard
====================
1. FREEZE  - every pipeline run saves the projection of every game that hasn't kicked
             off yet. "Last update before kickoff wins"; once a game starts its
             projection is locked forever. -> frontend/data/scorecard/live/
             (Projections already posted via the social generator are imported too.)
2. BACKTEST- for every completed week of last season and this season, rebuild the
             projection using ONLY data from before that week (cached once per week).
             -> frontend/data/scorecard/backtest/
3. GRADE   - compare each projection with what actually happened and publish the
             headline numbers. -> frontend/data/scorecard/public.json

Live ("published before the game") and backtest ("reconstructed") are always kept
and labeled separately.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo('America/New_York')


def _kickoff(gameday, gametime):
    try:
        h, m = (int(x) for x in str(gametime or '13:00').split(':')[:2])
        d = datetime.fromisoformat(str(gameday)[:10])
        return d.replace(hour=h, minute=m, tzinfo=ET)
    except Exception:
        return None


def _record(g, model, source):
    p = g['projection']
    return {
        'gameId': g['gameId'], 'season': g['season'], 'week': g['week'],
        'away': g['awayTeam']['abbr'], 'home': g['homeTeam']['abbr'],
        'gameday': g.get('gameday'), 'gametime': g.get('gametime'),
        'total': p['total'], 'home_proj': p['home'], 'away_proj': p['away'],
        'range': p['range'], 'leagueAverage': model.get('leagueAveragePerGame'),
        'byType': {r['type']: r['total'] for r in g['byType']},
        'byQuarter': [round(q['home'] + q['away'], 2) for q in p['byQuarter']],
        'crew': (g.get('crew') or {}).get('name'), 'crewKnown': bool(g.get('crew')),
        'source': source,
        'frozenAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }


def _load(path):
    return json.loads(path.read_text()) if path.exists() else {}


def _save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str))


# -----------------------------------------------------------------------------
# 1. Freeze
# -----------------------------------------------------------------------------

def freeze(preview_results, data_dir: Path, project_dir: Path):
    live_dir = data_dir / 'scorecard' / 'live'
    now = datetime.now(ET)
    frozen = 0
    for wk in preview_results or []:
        path = live_dir / f"{wk['season']}-week-{wk['week']:02d}.json"
        live = _load(path)
        for g in wk['games']:
            ko = _kickoff(g.get('gameday'), g.get('gametime'))
            if ko is None or now >= ko:
                continue                      # kicked off: never overwrite
            live[g['gameId']] = _record(g, wk['model'], 'live')
            frozen += 1
        if live:
            _save(path, live)

    # Projections already posted on social (Flag Watch) count as published, if the
    # pipeline didn't capture that game itself.
    imported = 0
    for snap_file in sorted((project_dir / 'social' / 'snapshots').glob('*.json')):
        season, week = snap_file.stem.split('-week-')
        path = live_dir / f'{season}-week-{int(week):02d}.json'
        live = _load(path)
        changed = False
        for gid, sn in _load(snap_file).items():
            if gid in live:
                continue
            _, _, away, home = gid.split('_')
            live[gid] = {'gameId': gid, 'season': int(season), 'week': int(week), 'away': away, 'home': home,
                         'total': sn['total'], 'home_proj': sn.get('home'), 'away_proj': sn.get('away'),
                         'range': sn['range'], 'leagueAverage': None, 'byType': sn.get('byType', {}),
                         'byQuarter': None, 'crew': sn.get('crew'), 'crewKnown': bool(sn.get('crew')),
                         'source': 'live-post', 'frozenAt': sn.get('snapshotAt')}
            changed = True
            imported += 1
        if changed:
            _save(path, live)
    print(f"   ✓ Froze {frozen} upcoming projections" + (f", imported {imported} posted" if imported else ''))


# -----------------------------------------------------------------------------
# 2. Backtest
# -----------------------------------------------------------------------------

def backtest(data, build_previews_fn, args, data_dir: Path):
    sched = data['schedules']
    reg = sched[sched['game_type'] == 'REG']
    played = set(data['games_played']['game_id'])
    season = int(reg['season'].max())
    bt_dir = data_dir / 'scorecard' / 'backtest'
    built = 0
    for s in (season - 1, season):
        for w in sorted(reg.loc[reg['season'] == s, 'week'].unique()):
            ids = set(reg[(reg['season'] == s) & (reg['week'] == w)]['game_id'])
            if not ids or not ids <= played:          # only fully played weeks
                continue
            path = bt_dir / f'{s}-week-{int(w):02d}.json'
            if path.exists():
                continue                               # cached: past weeks don't change
            res = build_previews_fn(data, *args, as_of=(s, int(w)))
            if not res:
                continue
            _save(path, {g['gameId']: _record(g, res['model'], 'backtest') for g in res['games']})
            built += 1
    print(f"   ✓ Backtest: {built} new week(s) reconstructed")


# -----------------------------------------------------------------------------
# 3. Grade
# -----------------------------------------------------------------------------

def _actuals(data):
    pen = data['penalties']
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    pen = pen[pen['penalty_team'].notna()]
    out = {}
    for gid, d in pen.groupby('game_id'):
        out[gid] = {'total': len(d), 'home': int((d['penalty_team'] == d['home_team']).sum()),
                    'away': int((d['penalty_team'] == d['away_team']).sum()),
                    'types': d['penalty_type'].value_counts().to_dict(),
                    'quarters': [int((d['qtr'] == q).sum()) for q in (1, 2, 3, 4)]}
    for gid in set(data['games_played']['game_id']) - set(out):
        out[gid] = {'total': 0, 'home': 0, 'away': 0, 'types': {}, 'quarters': [0, 0, 0, 0]}
    return out


def _grade_games(records, actuals, crews):
    rows = []
    for r in records:
        a = actuals.get(r['gameId'])
        if a is None:
            continue
        lo, hi = r['range']
        base = r.get('leagueAverage')
        rows.append({
            'gameId': r['gameId'], 'season': r['season'], 'week': r['week'], 'away': r['away'], 'home': r['home'],
            'crew': crews.get(r['gameId']) or r.get('crew'), 'source': r['source'],
            'projected': r['total'], 'low': lo, 'high': hi, 'actual': a['total'],
            'miss': round(a['total'] - r['total'], 1), 'inRange': bool(lo <= a['total'] <= hi),
            'baselineMiss': round(abs(a['total'] - base), 1) if base else None,
            'homeProjected': r.get('home_proj'), 'awayProjected': r.get('away_proj'),
            'homeActual': a['home'], 'awayActual': a['away'],
        })
    return rows


def summarize(rows):
    if not rows:
        return None
    miss = np.array([r['miss'] for r in rows], dtype=float)
    base = [r['baselineMiss'] for r in rows if r['baselineMiss'] is not None]
    mae = float(np.abs(miss).mean())
    base_mae = float(np.mean(base)) if base else None
    return {
        'games': len(rows),
        'avgMiss': round(mae, 2),
        'hitRate': round(float(np.mean([r['inRange'] for r in rows])) * 100, 1),
        'within3': round(float((np.abs(miss) <= 3).mean()) * 100, 1),
        'baselineAvgMiss': round(base_mae, 2) if base_mae else None,
        'skillPct': round((1 - mae / base_mae) * 100, 1) if base_mae else None,   # vs guessing league average
    }


def by_week(rows):
    out = []
    for (s, w), grp in pd.DataFrame(rows).groupby(['season', 'week']):
        sm = summarize(grp.to_dict('records'))
        out.append({'season': int(s), 'week': int(w), **sm})
    return out


def grade(data, data_dir: Path):
    actuals = _actuals(data)
    officials = data['officials']
    crews = (officials[officials['position'] == 'Referee'].dropna(subset=['game_id'])
             .drop_duplicates('game_id').set_index('game_id')['name'].to_dict())
    sc = data_dir / 'scorecard'

    def collect(sub):
        recs = []
        for f in sorted((sc / sub).glob('*.json')):
            recs += list(_load(f).values())
        return recs

    bt_recs = collect('backtest')
    league_by_game = {r['gameId']: r.get('leagueAverage') for r in bt_recs}
    live_recs = collect('live')
    for r in live_recs:   # posted snapshots don't store the league average: use that week's
        if not r.get('leagueAverage'):
            r['leagueAverage'] = league_by_game.get(r['gameId'])
    live = _grade_games(live_recs, actuals, crews)
    bt = _grade_games(bt_recs, actuals, crews)
    season = int(data['schedules']['season'].max())
    bt_cur = [r for r in bt if r['season'] == season]
    bt_last = [r for r in bt if r['season'] == season - 1]
    out = {
        'season': season,
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'definitions': {
            'avgMiss': 'Average gap between projected and actual accepted penalties per game',
            'hitRate': 'Share of games where the actual count landed inside the projected likely range (target ~80%)',
            'skillPct': 'How much smaller our average miss is than guessing the league average every game',
            'live': 'Projections published on the site before kickoff',
            'backtest': 'Projections reconstructed afterward using only data available before each week',
        },
        'live': {'summary': summarize(live), 'byWeek': by_week(live) if live else [],
                 'games': sorted(live, key=lambda r: (r['season'], r['week'], r['gameId']), reverse=True)},
        'backtest': {
            'currentSeason': {'season': season, 'summary': summarize(bt_cur), 'byWeek': by_week(bt_cur) if bt_cur else []},
            'lastSeason': {'season': season - 1, 'summary': summarize(bt_last), 'byWeek': by_week(bt_last) if bt_last else []},
        },
    }
    _save(sc / 'public.json', out)
    L, B = out['live']['summary'], out['backtest']['lastSeason']['summary']
    print(f"   ✓ Scorecard: live {L['games'] if L else 0} games"
          + (f" (avg miss {L['avgMiss']}, {L['hitRate']}% in range)" if L else '')
          + (f" · {season - 1} backtest {B['games']} games, avg miss {B['avgMiss']}, {B['hitRate']}% in range, "
             f"skill {B['skillPct']}%" if B else ''))
    return out


def run(data, build_previews_fn, preview_args, preview_results, data_dir: Path, project_dir: Path):
    print("\n📏 Prediction scorecard...")
    freeze(preview_results, data_dir, project_dir)
    backtest(data, build_previews_fn, preview_args, data_dir)
    return grade(data, data_dir)
