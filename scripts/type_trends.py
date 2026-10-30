"""
Penalty type trends: which calls are becoming more (or less) common.
Per-game rate of each penalty type, by regular season, plus this season vs
three comparisons (last season through the same week, all of last season,
all prior seasons). Writes frontend/data/type_trends.json via update_data.py.
"""
import math
from datetime import datetime, timezone

import pandas as pd

import weeks

TOP_N = 18


def _r(x, d=2):
    return None if x is None or pd.isna(x) else round(float(x), d)


def _whole_pct(x):
    """A percentage rounded half away from zero, stored once so every page shows the same number."""
    return int(math.copysign(math.floor(abs(x) + 0.5), x))


def _rate(frame):
    """Games-weighted flags per game for a set of games: {'perGame', 'games'}."""
    n = int(len(frame))
    return {'perGame': _r(frame['flags'].sum() / n) if n else None, 'games': n}


def build_type_trends(data: dict) -> dict:
    print("\n📈 Building penalty type trends...")
    sched = data['schedules']
    reg = weeks.regular_season(sched, 'game_type')
    season = int(reg['season'].max())
    gp = data['games_played']
    if 'season_type' in gp.columns:
        gp = weeks.regular_season(gp)
    games = gp[['game_id']].drop_duplicates().merge(reg[['game_id', 'season', 'week']], on='game_id')
    pen = data['penalties']
    if 'season_type' in pen.columns:
        pen = weeks.regular_season(pen)
    pen = pen[pen['penalty_team'].notna() & pen['game_id'].isin(games['game_id'])]
    pen = pen.merge(games.rename(columns={'season': 's', 'week': 'w'}), on='game_id')

    through, _ = weeks.completed_week(sched, gp, season)
    # Same-weeks comparison: through the partial week while one is in progress (#118)
    same_week = weeks.compare_week(through, games.loc[games['season'] == season, 'week'])
    seasons = sorted(int(x) for x in games['season'].unique())
    prior = weeks.prior_seasons(seasons, season)
    n_games = games.groupby('season').size()

    def rate(mask_games, mask_pen):
        n = int(mask_games.sum())
        if not n:
            return {}, 0
        return (pen[mask_pen].groupby('penalty_type').size() / n).to_dict(), n

    cur_rates, cur_n = rate(games['season'] == season, pen['s'] == season)
    comps = {}
    if (season - 1) in prior:
        comps['sameWeeks'] = (weeks.through_label(season - 1, same_week), weeks.short_through(season - 1, same_week),
                              *rate((games['season'] == season - 1) & (games['week'] <= same_week),
                                    (pen['s'] == season - 1) & (pen['w'] <= same_week)))
        comps['lastSeason'] = (f"All of {season - 1}", f"{season - 1}",
                               *rate(games['season'] == season - 1, pen['s'] == season - 1))
    if prior:
        span = weeks.span_label(prior)
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
        'priorLabel': f"{weeks.span_label(prior)} avg" if prior else None,
    }
    # This season vs the usual for the same (completed) weeks, games-weighted on both sides (#118, C20)
    if through and prior:
        g_prior = gw[gw['season'].isin(prior)]
        cur_u = _rate(gw[(gw['season'] == season) & (gw['week'] <= through)])
        prior_u = _rate(g_prior[g_prior['week'] <= through])
        if cur_u['games'] and prior_u['games']:
            cur_x = gw[(gw['season'] == season) & (gw['week'] <= through)]['flags'].mean()
            prior_x = g_prior[g_prior['week'] <= through]['flags'].mean()
            weekly['usual'] = {'through': int(through), 'label': weeks.weeks_label(through),
                               'seasons': weeks.span_label(prior), 'current': cur_u, 'prior': prior_u,
                               'diff': _r(cur_x - prior_x), 'pct': _whole_pct((cur_x / prior_x - 1) * 100)}
    # The fade: late-season weeks vs the first weeks, every prior season, games-weighted (#118, C20)
    fade = weeks.fade_windows(int(pw.index.max())) if len(pw) else None
    if fade:
        g_prior = gw[gw['season'].isin(prior)]
        sides = {k: g_prior[g_prior['week'].between(fade[k]['from'], fade[k]['to'])] for k in ('early', 'late')}
        for k, f in sides.items():
            fade[k].update(_rate(f))
        e_x, l_x = sides['early']['flags'].mean(), sides['late']['flags'].mean()
        fade['seasons'] = weeks.span_label(prior)
        fade['fewer'] = _r(e_x - l_x)
        fade['pctFewer'] = _whole_pct((1 - l_x / e_x) * 100)
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
        'comparisons': [{'key': k, 'label': v[0], 'short': v[1], 'games': v[3],
                         'button': weeks.button_through(season - 1, same_week) if k == 'sameWeeks' else v[0]}
                        for k, v in comps.items()],
        'defaultComparison': 'sameWeeks' if 'sameWeeks' in comps else next(iter(comps), None),
        'types': types,
        'weekly': weekly,
        'fadeWindows': fade,
        'seasonCompare': season_compare,
        'quarters': quarters,
        'typeShare': shares,
        'scopeLabels': {'current': f'{season} season', 'all': weeks.since_label(seasons[0])},
        'notes': 'Regular season. Accepted penalties per game, all teams combined.',
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
