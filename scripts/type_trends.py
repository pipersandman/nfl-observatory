"""
Penalty type trends: which calls are becoming more (or less) common.
Per-game rate of each penalty type, by regular season, plus this season vs
three comparisons (last season through the same week, all of last season,
all prior seasons). Writes frontend/data/type_trends.json via update_data.py.
"""
from datetime import datetime, timezone

import pandas as pd

from weeks import completed_week

TOP_N = 18


def _r(x, d=2):
    return None if x is None or pd.isna(x) else round(float(x), d)


def build_type_trends(data: dict) -> dict:
    print("\n📈 Building penalty type trends...")
    sched = data['schedules']
    reg = sched[sched['game_type'] == 'REG']
    season = int(reg['season'].max())
    gp = data['games_played']
    if 'season_type' in gp.columns:
        gp = gp[gp['season_type'] == 'REG']
    games = gp[['game_id']].drop_duplicates().merge(reg[['game_id', 'season', 'week']], on='game_id')
    pen = data['penalties']
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    pen = pen[pen['penalty_team'].notna() & pen['game_id'].isin(games['game_id'])]
    pen = pen.merge(games.rename(columns={'season': 's', 'week': 'w'}), on='game_id')

    through, _ = completed_week(sched, gp, season)
    seasons = sorted(int(x) for x in games['season'].unique())
    prior = [x for x in seasons if x < season]
    n_games = games.groupby('season').size()

    def rate(mask_games, mask_pen):
        n = int(mask_games.sum())
        if not n:
            return {}, 0
        return (pen[mask_pen].groupby('penalty_type').size() / n).to_dict(), n

    cur_rates, cur_n = rate(games['season'] == season, pen['s'] == season)
    comps = {}
    if (season - 1) in prior:
        comps['sameWeeks'] = (f"{season - 1} through Week {through}", f"{season - 1} Wk 1–{through}",
                              *rate((games['season'] == season - 1) & (games['week'] <= through),
                                    (pen['s'] == season - 1) & (pen['w'] <= through)))
        comps['lastSeason'] = (f"All of {season - 1}", f"{season - 1}",
                               *rate(games['season'] == season - 1, pen['s'] == season - 1))
    if prior:
        span = f"{prior[0]}–{str(prior[-1])[2:]}"
        comps['allPrior'] = (f"All seasons ({span})", f"{span} avg",
                             *rate(games['season'].isin(prior), pen['s'].isin(prior)))

    by_season = {s: (pen[pen['s'] == s].groupby('penalty_type').size() / n_games[s]).to_dict() for s in seasons}
    # The most common types overall, plus anything big this season
    overall = pen.groupby('penalty_type').size().sort_values(ascending=False)
    keys = list(dict.fromkeys(list(overall.head(TOP_N).index) +
                              list(pd.Series(cur_rates).sort_values(ascending=False).head(8).index)))

    types = []
    for t in keys:
        types.append({
            'type': t,
            'current': _r(cur_rates.get(t, 0)),
            'currentCount': int(((pen['s'] == season) & (pen['penalty_type'] == t)).sum()),
            'compare': {k: _r(v[2].get(t, 0)) for k, v in comps.items()},
            'bySeason': [{'season': s, 'perGame': _r(by_season[s].get(t, 0))} for s in seasons],
        })
    # Flags per game by week of the season, every season (+ prior-seasons average per week)
    per_game = pen.groupby('game_id').size().rename('flags')
    gw = games.set_index('game_id').join(per_game).fillna({'flags': 0}).reset_index()
    weekly_seasons = []
    for s_ in seasons:
        d = gw[gw['season'] == s_].groupby('week')['flags'].agg(['mean', 'size'])
        sched_n = reg[reg['season'] == s_].groupby('week').size()
        weekly_seasons.append({'season': s_, 'weeks': [
            {'week': int(w), 'perGame': _r(r['mean'], 2), 'games': int(r['size']),
             'complete': bool(r['size'] >= sched_n.get(w, 0))} for w, r in d.iterrows()]})
    pw = gw[gw['season'].isin(prior)].groupby('week')['flags'].agg(['mean', 'size'])
    # Typical range per week across past seasons (lowest and highest season)
    pr = gw[gw['season'].isin(prior)].groupby(['season', 'week'])['flags'].mean().reset_index()
    rng = pr.groupby('week')['flags'].agg(['min', 'max'])
    weekly = {
        'priorRange': [{'week': int(w), 'low': _r(r['min'], 2), 'high': _r(r['max'], 2)} for w, r in rng.iterrows()],
        'seasons': weekly_seasons,
        'priorAverage': [{'week': int(w), 'perGame': _r(r['mean'], 2), 'games': int(r['size'])} for w, r in pw.iterrows()],
        'priorLabel': f"{prior[0]}–{str(prior[-1])[2:]} avg" if prior else None,
    }
    # ---- Charts for League Trends (regular season only) ----
    # Full season vs the same early weeks for every season (fair comparison for a
    # season in progress)
    season_compare = []
    for s_ in seasons:
        g_all = gw[gw['season'] == s_]
        g_early = g_all[g_all['week'] <= through] if through else g_all.iloc[0:0]
        season_compare.append({
            'season': s_, 'games': int(len(g_all)),
            'fullSeason': _r(g_all['flags'].mean(), 2) if len(g_all) else None,
            'complete': bool(s_ < season),
            'earlyGames': int(len(g_early)), 'early': _r(g_early['flags'].mean(), 2) if len(g_early) else None,
        })

    def quarter_block(mask_g, mask_p):
        n = int(mask_g.sum())
        p = pen[mask_p & pen['qtr'].between(1, 4)]
        top = p['penalty_type'].value_counts().head(8).index
        return {'games': n,
                'total': [_r((p['qtr'] == q).sum() / n, 2) if n else None for q in (1, 2, 3, 4)],
                'types': {t: [_r(((p['qtr'] == q) & (p['penalty_type'] == t)).sum() / n, 2) for q in (1, 2, 3, 4)] for t in top}}

    def share_block(mask_g, mask_p):
        n = int(mask_g.sum())
        p = pen[mask_p]
        vc = p['penalty_type'].value_counts()
        total = int(vc.sum())
        top = [{'type': t, 'count': int(c), 'pct': _r(c / total * 100, 1), 'perGame': _r(c / n, 2)} for t, c in vc.head(10).items()]
        rest = int(vc.iloc[10:].sum())
        if rest:
            top.append({'type': f'All other ({len(vc) - 10} types)', 'count': rest, 'pct': _r(rest / total * 100, 1), 'perGame': _r(rest / n, 2), 'other': True})
        return {'games': n, 'total': total, 'perGame': _r(total / n, 2) if n else None, 'types': top}

    scopes = {'current': (games['season'] == season, pen['s'] == season),
              'all': (games['season'] >= seasons[0], pen['s'] >= seasons[0])}
    quarters = {k: quarter_block(*m) for k, m in scopes.items()}
    shares = {k: share_block(*m) for k, m in scopes.items()}

    print(f"   ✓ {len(types)} penalty types, {len(seasons)} seasons, weekly profile, trend charts")
    return {
        'season': season, 'throughWeek': through, 'currentGames': cur_n,
        'comparisons': [{'key': k, 'label': v[0], 'short': v[1], 'games': v[3]} for k, v in comps.items()],
        'defaultComparison': 'sameWeeks' if 'sameWeeks' in comps else next(iter(comps), None),
        'types': types,
        'weekly': weekly,
        'seasonCompare': season_compare,
        'quarters': quarters,
        'typeShare': shares,
        'scopeLabels': {'current': f'{season} season', 'all': f'Since {seasons[0]}'},
        'notes': 'Regular season. Accepted penalties per game, all teams combined.',
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
