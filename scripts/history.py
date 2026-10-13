"""
History ledger: a permanent, week-by-week record
================================================
Once every game of a week has been played, this writes that week to
frontend/data/history/games/{season}-week-NN.json, one entry per game:

  prediction  the projection published before kickoff (live) or, for weeks before
              live tracking began, the reconstructed one (backtest), labeled as such
  outcome     what happened: final score, crew, flags and yards for each team,
              by penalty type and by quarter, plus the game's context (closing
              spread/total, roof, surface, weather, rest)
  grade       miss, in-range, each team's miss, and the error for each penalty type

Weeks are written once and kept. If nflverse later revises a game's play-by-play,
the new outcome replaces the old one and the previous version is kept in a
'corrections' log, so nothing is silently rewritten.

It also saves a snapshot of the league after each completed week
(history/snapshots/{season}-week-NN.json): every team's and crew's season-to-date
numbers and ranks, as they stood that week, which can't be rebuilt later.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from jsonsafe import dumps as safe_dumps

NAME_FIXES = {'Ronald Torbert': 'Ron Torbert', 'Adrian Hall': 'Adrian Hill'}


def _load(path):
    return json.loads(path.read_text()) if path.exists() else None


def _save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(safe_dumps(obj))


def _num(x, d=2):
    return None if x is None or pd.isna(x) else round(float(x), d)


def _outcome(game, pen, crew_by_game):
    gid, home, away = game['game_id'], game['home_team'], game['away_team']
    p = pen[pen['game_id'] == gid]

    def side(team):
        q = p[p['penalty_team'] == team]
        return {'flags': int(len(q)), 'yards': int(q['penalty_yards'].sum()),
                'types': {k: int(v) for k, v in q['penalty_type'].value_counts().items()},
                'quarters': [int((q['qtr'] == n).sum()) for n in (1, 2, 3, 4)] + [int((q['qtr'] >= 5).sum())]}
    h, a = side(home), side(away)
    out = {
        'homeScore': None if pd.isna(game['home_score']) else int(game['home_score']),
        'awayScore': None if pd.isna(game['away_score']) else int(game['away_score']),
        'crew': crew_by_game.get(gid) or (NAME_FIXES.get(game['referee'], game['referee']) if isinstance(game['referee'], str) else None),
        'total': h['flags'] + a['flags'], 'yards': h['yards'] + a['yards'],
        'home': h, 'away': a,
        'context': {
            'gameday': str(game['gameday']), 'weekday': game.get('weekday'), 'gametime': game.get('gametime'),
            'divisionGame': bool(game.get('div_game')) if not pd.isna(game.get('div_game')) else None,
            'overtime': bool(game.get('overtime')) if not pd.isna(game.get('overtime')) else None,
            'closingSpread': _num(game.get('spread_line'), 1), 'closingTotal': _num(game.get('total_line'), 1),
            'roof': game.get('roof') if isinstance(game.get('roof'), str) else None,
            'surface': game.get('surface') if isinstance(game.get('surface'), str) else None,
            'temp': _num(game.get('temp'), 0), 'wind': _num(game.get('wind'), 0),
            'homeRest': _num(game.get('home_rest'), 0), 'awayRest': _num(game.get('away_rest'), 0),
            'stadium': game.get('stadium') if isinstance(game.get('stadium'), str) else None,
        },
    }
    key = json.dumps([out['homeScore'], out['awayScore'], h, a], sort_keys=True)
    out['hash'] = hashlib.sha1(key.encode()).hexdigest()[:12]
    return out


def _grade(pred, out):
    if not pred:
        return None
    lo, hi = pred['range']
    actual_types = {}
    for side in ('home', 'away'):
        for t, n in out[side]['types'].items():
            actual_types[t] = actual_types.get(t, 0) + n
    proj_types = pred.get('byType') or {}
    named = set(proj_types) - {'Other'}
    errors = {t: round(actual_types.get(t, 0) - v, 2) for t, v in proj_types.items() if t != 'Other'}
    if 'Other' in proj_types:
        errors['Other'] = round(sum(n for t, n in actual_types.items() if t not in named) - proj_types['Other'], 2)
    q_actual = [out['home']['quarters'][i] + out['away']['quarters'][i] for i in range(4)]
    return {
        'miss': round(out['total'] - pred['total'], 1),
        'absMiss': round(abs(out['total'] - pred['total']), 1),
        'inRange': bool(lo <= out['total'] <= hi),
        'homeMiss': round(out['home']['flags'] - pred['home_proj'], 1) if pred.get('home_proj') is not None else None,
        'awayMiss': round(out['away']['flags'] - pred['away_proj'], 1) if pred.get('away_proj') is not None else None,
        'typeErrors': errors,
        'quarterErrors': [round(q_actual[i] - pred['byQuarter'][i], 2) for i in range(4)] if pred.get('byQuarter') else None,
    }


def _summary(games):
    graded = [g for g in games if g.get('grade')]
    if not graded:
        return {'games': len(games), 'graded': 0}
    miss = [g['grade']['miss'] for g in graded]
    return {
        'games': len(games), 'graded': len(graded),
        'live': sum(1 for g in graded if g['prediction']['source'] != 'backtest'),
        'avgMiss': round(sum(abs(m) for m in miss) / len(miss), 2),
        'bias': round(sum(miss) / len(miss), 2),
        'hitRate': round(sum(g['grade']['inRange'] for g in graded) / len(graded) * 100, 1),
        'over': sum(1 for m in miss if m > 0), 'under': sum(1 for m in miss if m < 0), 'exact': sum(1 for m in miss if m == 0),
        'flagsPerGame': round(sum(g['outcome']['total'] for g in games) / len(games), 2),
    }


def build_history(data: dict, data_dir: Path) -> dict:
    print("\n📚 History ledger...")
    sched = data['schedules']
    reg = sched[sched['game_type'] == 'REG']
    played = set(data['games_played']['game_id'])
    pen = data['penalties']
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    pen = pen[pen['penalty_team'].notna()].copy()
    pen['penalty_yards'] = pd.to_numeric(pen['penalty_yards'], errors='coerce').fillna(0).abs()
    off = data['officials']
    crew_by_game = (off[off['position'] == 'Referee'].dropna(subset=['game_id'])
                    .drop_duplicates('game_id').set_index('game_id')['name'].to_dict())

    sc, hist = data_dir / 'scorecard', data_dir / 'history'
    season = int(reg['season'].max())
    seasons = [season - 1, season]
    written, corrected = 0, 0
    index = _load(hist / 'index.json') or {'weeks': []}
    idx = {(w['season'], w['week']): w for w in index['weeks']}

    for s in seasons:
        for wk in sorted(reg.loc[reg['season'] == s, 'week'].unique()):
            wk = int(wk)
            wgames = reg[(reg['season'] == s) & (reg['week'] == wk)]
            if not set(wgames['game_id']) <= played:
                continue                                    # only finished weeks
            path = hist / 'games' / f'{s}-week-{wk:02d}.json'
            existing = _load(path)
            live = _load(sc / 'live' / f'{s}-week-{wk:02d}.json') or {}
            bt = _load(sc / 'backtest' / f'{s}-week-{wk:02d}.json') or {}
            prev = {g['gameId']: g for g in (existing or {}).get('games', [])}
            games, changed = [], existing is None
            for _, g in wgames.sort_values(['gameday', 'gametime', 'game_id']).iterrows():
                gid = g['game_id']
                out = _outcome(g, pen, crew_by_game)
                old = prev.get(gid)
                pred = (old or {}).get('prediction') or live.get(gid) or bt.get(gid)
                if pred and old is None:
                    pred = {**pred, 'source': pred.get('source', 'live')}
                # Crew: the official record when nflverse has it (it lags games by a few days);
                # until then, the assignment published before kickoff
                if out['crew']:
                    out['crewSource'] = 'official'
                elif pred and pred.get('crew'):
                    out['crew'], out['crewSource'] = pred['crew'], 'assignment'
                entry = {'gameId': gid, 'season': s, 'week': wk, 'away': g['away_team'], 'home': g['home_team'],
                         'prediction': pred, 'outcome': out, 'grade': _grade(pred, out) if pred else None,
                         'corrections': (old or {}).get('corrections', []), 'recordedAt': (old or {}).get('recordedAt')
                         or datetime.now(timezone.utc).isoformat(timespec='seconds')}
                if old and old['outcome'].get('hash') != out['hash']:
                    entry['corrections'] = entry['corrections'] + [{
                        'replacedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                        'previousOutcome': old['outcome']}]
                    changed, corrected = True, corrected + 1
                elif old:
                    entry = old                                # unchanged: keep exactly as recorded
                    # ...except fill in the crew once it's known (not a data correction)
                    if out.get('crew') and (not old['outcome'].get('crew') or
                                            (old['outcome'].get('crewSource') != 'official' and out.get('crewSource') == 'official')):
                        entry = {**old, 'outcome': {**old['outcome'], 'crew': out['crew'], 'crewSource': out['crewSource']}}
                        changed = True
                games.append(entry)
            if changed:
                _save(path, {'season': s, 'week': wk, 'summary': _summary(games), 'games': games,
                             'notes': 'prediction.source: live = published before kickoff; backtest = reconstructed afterward.'})
                written += 1
                idx[(s, wk)] = {'season': s, 'week': wk, 'file': f'history/games/{s}-week-{wk:02d}.json', **_summary(games)}

    # League snapshot as of the latest completed week (can't be rebuilt later)
    from weeks import completed_week
    done, _ = completed_week(sched, data['games_played'], season)
    if done:
        snap_path = hist / 'snapshots' / f'{season}-week-{done:02d}.json'
        if not snap_path.exists():
            teams = _load(data_dir / 'teams' / 'index.json') or {}
            sc_json = _load(data_dir / 'season_comparison.json') or {}
            sb = _load(data_dir / 'scoreboard.json') or {}
            _save(snap_path, {
                'season': season, 'throughWeek': done,
                'takenAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'teams': [{k: t.get(k) for k in ('abbr', 'record', 'games', 'perGame', 'yardsPerGame', 'rank')}
                          for d in teams.get('divisions', []) for t in d['teams']],
                'crews': [{'name': c['name'], **(c.get('current') or {})} for c in sc_json.get('crewChiefs', [])],
                'league': (sc_json.get('league') or {}).get('current'),
                'scoreboardSeason': next((f for f in sb.get('frames', []) if f['key'] == 'season'), None),
            })
            print(f"   ✓ League snapshot saved: {season} through Week {done}")

    index['weeks'] = sorted(idx.values(), key=lambda w: (w['season'], w['week']), reverse=True)
    index['generatedAt'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    _save(hist / 'index.json', index)
    print(f"   ✓ {written} week file(s) written, {corrected} correction(s), {len(index['weeks'])} weeks in the ledger")
    return index
