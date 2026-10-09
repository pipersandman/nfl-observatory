#!/usr/bin/env python3
"""
Internal scorecard report (runs on your laptop; nothing is published)
=====================================================================
Over/under split, bias, and where the projections miss: by crew, team, slot,
penalty type, quarter, crew-known vs TBA, early vs late season.

    python scripts\\scorecard_report.py            # prints + saves reports\\scorecard-YYYY-MM-DD.md
"""

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
SC = ROOT / 'frontend' / 'data' / 'scorecard'
NAME_FIXES = {'Ronald Torbert': 'Ron Torbert', 'Adrian Hall': 'Adrian Hill'}


def load_records(sub):
    recs = []
    for f in sorted((SC / sub).glob('*.json')):
        recs += list(json.loads(f.read_text()).values())
    return recs


def actuals(seasons):
    import nflreadpy as nfl
    frames = []
    for s in seasons:
        try:
            frames.append(nfl.load_pbp(s).to_pandas())
        except Exception as e:
            print(f'  (pbp {s} unavailable: {e})')
    pbp = pd.concat(frames)
    pbp = pbp[(pbp['season_type'] == 'REG')]
    games = set(pbp['game_id'])
    pen = pbp[(pbp['penalty'] == 1) & pbp['penalty_team'].notna()]
    sched = nfl.load_schedules(seasons).to_pandas().set_index('game_id')
    out = {}
    for gid in games:
        d = pen[pen['game_id'] == gid]
        sc = sched.loc[gid] if gid in sched.index else None
        out[gid] = {'total': len(d), 'home': int((d['penalty_team'] == d['home_team']).sum()) if len(d) else 0,
                    'away': int((d['penalty_team'] == d['away_team']).sum()) if len(d) else 0,
                    'types': d['penalty_type'].value_counts().to_dict(),
                    'quarters': [int((d['qtr'] == q).sum()) for q in (1, 2, 3, 4)],
                    'crew': NAME_FIXES.get(sc['referee'], sc['referee']) if sc is not None and isinstance(sc['referee'], str) else None,
                    'weekday': sc['weekday'] if sc is not None else None,
                    'div': bool(sc['div_game']) if sc is not None else None}
    return out


def table(rows, cols):
    if not rows:
        return '_none_\n'
    out = '| ' + ' | '.join(cols) + ' |\n|' + '---|' * len(cols) + '\n'
    for r in rows:
        out += '| ' + ' | '.join(str(r.get(c, '')) for c in cols) + ' |\n'
    return out


def group_stats(df, key, min_n=5):
    rows = []
    for k, g in df.groupby(key):
        if len(g) < min_n:
            continue
        rows.append({key: k, 'games': len(g), 'bias': round(g['diff'].mean(), 2),
                     'avg miss': round(g['diff'].abs().mean(), 2), 'over %': round((g['diff'] > 0).mean() * 100),
                     'in range %': round(g['inRange'].mean() * 100)})
    return sorted(rows, key=lambda r: -abs(r['bias']))


def section(name, recs, act):
    rows = []
    type_diff = defaultdict(list)
    q_diff = [[], [], [], []]
    side = []
    for r in recs:
        a = act.get(r['gameId'])
        if a is None:
            continue
        lo, hi = r['range']
        d = a['total'] - r['total']
        rows.append({'gameId': r['gameId'], 'season': r['season'], 'week': r['week'], 'diff': d,
                     'inRange': lo <= a['total'] <= hi, 'crew': a['crew'] or r.get('crew') or 'TBA',
                     'slot': a['weekday'], 'division': 'division' if a['div'] else 'non-division',
                     'crewKnown': 'crew known' if r.get('crewKnown') else 'crew TBA',
                     'phase': 'weeks 1–4' if r['week'] <= 4 else ('weeks 5–12' if r['week'] <= 12 else 'weeks 13+')})
        for team, proj, actual in ((r['home'], r.get('home_proj'), a['home']), (r['away'], r.get('away_proj'), a['away'])):
            if proj is not None:
                side.append({'team': team, 'diff': actual - proj, 'inRange': True})
        keys = set(r.get('byType', {}))
        other = sum(v for t, v in a['types'].items() if t not in keys)
        for t, pv in (r.get('byType') or {}).items():
            type_diff[t].append((other if t == 'Other' else a['types'].get(t, 0)) - pv)
        if r.get('byQuarter'):
            for i in range(4):
                q_diff[i].append(a['quarters'][i] - r['byQuarter'][i])
    if not rows:
        return f'## {name}\n\n_No graded games yet._\n'
    df = pd.DataFrame(rows)
    d = df['diff']
    over, under = d[d > 0], d[d < 0]
    md = [f'## {name}\n',
          f"**{len(df)} games** · avg miss **{d.abs().mean():.2f}** · bias **{d.mean():+.2f}** "
          f"({'we under-project' if d.mean() > 0 else 'we over-project'}) · in range **{df['inRange'].mean() * 100:.0f}%**\n",
          f"- Over the projection: **{(d > 0).mean() * 100:.0f}%** of games, by **{(over.mean() if len(over) else 0):.1f}** flags on average (max {over.max() if len(over) else 0:.0f})",
          f"- Under the projection: **{(d < 0).mean() * 100:.0f}%**, by **{(-under.mean() if len(under) else 0):.1f}** on average (max {-under.min() if len(under) else 0:.0f})",
          f"- Within ±3 flags: **{(d.abs() <= 3).mean() * 100:.0f}%** · within ±5: **{(d.abs() <= 5).mean() * 100:.0f}%**\n",
          '**Biggest misses**\n', table(df.reindex(df['diff'].abs().sort_values(ascending=False).index).head(8)
                                         .assign(diff=lambda x: x['diff'].round(1)).to_dict('records'),
                                         ['gameId', 'crew', 'diff']),
          '\n**By crew chief** (5+ games, largest bias first)\n', table(group_stats(df, 'crew'), ['crew', 'games', 'bias', 'avg miss', 'over %', 'in range %']),
          '\n**By slot**\n', table(group_stats(df, 'slot', 3), ['slot', 'games', 'bias', 'avg miss', 'over %', 'in range %']),
          '\n**Division vs non-division**\n', table(group_stats(df, 'division', 3), ['division', 'games', 'bias', 'avg miss', 'over %', 'in range %']),
          '\n**Crew known vs TBA**\n', table(group_stats(df, 'crewKnown', 1), ['crewKnown', 'games', 'bias', 'avg miss', 'over %', 'in range %']),
          '\n**Season phase**\n', table(group_stats(df, 'phase', 1), ['phase', 'games', 'bias', 'avg miss', 'over %', 'in range %'])]
    if side:
        sd = pd.DataFrame(side)
        tr = [{'team': t, 'games': len(g), 'bias': round(g['diff'].mean(), 2), 'avg miss': round(g['diff'].abs().mean(), 2)}
              for t, g in sd.groupby('team') if len(g) >= 4]
        md += ['\n**By team (flags on that team)**, largest bias first\n',
               table(sorted(tr, key=lambda r: -abs(r['bias']))[:12], ['team', 'games', 'bias', 'avg miss'])]
    tt = [{'type': t, 'games': len(v), 'bias per game': round(float(np.mean(v)), 2)} for t, v in type_diff.items()]
    md += ['\n**By penalty type** (actual − projected per game)\n', table(sorted(tt, key=lambda r: -abs(r['bias per game'])), ['type', 'games', 'bias per game'])]
    if q_diff[0]:
        md += ['\n**By quarter** (actual − projected per game)\n',
               table([{'quarter': f'Q{i + 1}', 'bias': round(float(np.mean(q_diff[i])), 2)} for i in range(4)], ['quarter', 'bias'])]
    return '\n'.join(md) + '\n'


def main():
    live, bt = load_records('live'), load_records('backtest')
    seasons = sorted({r['season'] for r in live + bt})
    if not seasons:
        sys.exit('No projections yet. Run the pipeline first.')
    print(f'Loading results for {seasons}...')
    act = actuals(seasons)
    cur = max(seasons)
    md = [f'# Scorecard: internal report ({date.today()})\n',
          'Bias = actual − projected. Positive means more flags than we projected.\n',
          section('Live (published before kickoff)', live, act),
          section(f'Backtest {cur}', [r for r in bt if r['season'] == cur], act),
          section(f'Backtest {cur - 1}', [r for r in bt if r['season'] == cur - 1], act)]
    text = '\n'.join(md)
    out = ROOT / 'reports' / f'scorecard-{date.today()}.md'
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding='utf-8')
    print(text)
    print(f'\nSaved {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
