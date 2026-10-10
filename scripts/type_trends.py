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
    print(f"   ✓ {len(types)} penalty types, {len(seasons)} seasons")
    return {
        'season': season, 'throughWeek': through, 'currentGames': cur_n,
        'comparisons': [{'key': k, 'label': v[0], 'short': v[1], 'games': v[3]} for k, v in comps.items()],
        'defaultComparison': 'sameWeeks' if 'sameWeeks' in comps else next(iter(comps), None),
        'types': types,
        'notes': 'Regular season. Accepted penalties per game, all teams combined.',
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
