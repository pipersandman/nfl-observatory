"""
Team pages: every team's penalty profile, this season vs last season vs all prior.
================================================================================
Called from update_data.py with the data it already loaded. Regular season only.

Writes:
  frontend/data/teams/index.json   - 8 divisions x 4 teams, summary per team
  frontend/data/teams/{ABBR}.json  - full profile per team
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from jsonsafe import dumps as safe_dumps

DIVISION_ORDER = ['AFC East', 'AFC North', 'AFC South', 'AFC West',
                  'NFC East', 'NFC North', 'NFC South', 'NFC West']
MIN_CREW_GAMES = 2


def _r(x, d=2):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)


def build_team_pages(data: dict, team_info, slugify, data_dir: Path) -> dict:
    print("\n🏟️  Building team pages...")
    import nflreadpy as nfl

    schedules = data.get('schedules', pd.DataFrame())
    penalties = data.get('penalties', pd.DataFrame())
    games_played = data.get('games_played', pd.DataFrame())
    officials = data.get('officials', pd.DataFrame())
    if schedules.empty or penalties.empty or games_played.empty:
        print("   ✗ Missing data")
        return {}

    reg = schedules[schedules['game_type'] == 'REG'].copy()
    season = int(reg['season'].max())

    # Divisions (current 32 teams, as they appear in this season's schedule)
    teams_meta = nfl.load_teams().to_pandas().set_index('team_abbr')
    current_teams = sorted(set(reg.loc[reg['season'] == season, 'home_team']) |
                           set(reg.loc[reg['season'] == season, 'away_team']))

    # ---- Team-game table (one row per team per regular-season game with pbp) ----
    gp = games_played
    if 'season_type' in gp.columns:
        gp = gp[gp['season_type'] == 'REG']
    gp = gp[['game_id']].drop_duplicates().merge(
        reg[['game_id', 'season', 'week', 'gameday', 'home_team', 'away_team', 'home_score', 'away_score']],
        on='game_id', how='inner')
    chiefs = (officials[officials['position'] == 'Referee'][['game_id', 'name']]
              .dropna().drop_duplicates('game_id').rename(columns={'name': 'crew'}))
    gp = gp.merge(chiefs, on='game_id', how='left')

    pen = penalties[penalties['game_id'].isin(gp['game_id'])].copy()
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    pen = pen[pen['penalty_team'].notna()]
    pen['penalty_yards'] = pd.to_numeric(pen['penalty_yards'], errors='coerce').fillna(0).abs()
    pen['offense'] = pen['penalty_team'] == pen['posteam']

    by_team = pen.groupby(['game_id', 'penalty_team']).agg(
        flags=('penalty_team', 'size'), yards=('penalty_yards', 'sum'),
        off=('offense', 'sum')).reset_index().rename(columns={'penalty_team': 'team'})

    tg = pd.concat([
        gp.assign(team=gp['home_team'], opp=gp['away_team'], is_home=True,
                  pts=gp['home_score'], opp_pts=gp['away_score']),
        gp.assign(team=gp['away_team'], opp=gp['home_team'], is_home=False,
                  pts=gp['away_score'], opp_pts=gp['home_score']),
    ], ignore_index=True)
    tg = tg.merge(by_team, on=['game_id', 'team'], how='left')
    opp = by_team.rename(columns={'team': 'opp', 'flags': 'drawn', 'yards': 'drawn_yards', 'off': 'drawn_off'})
    tg = tg.merge(opp, on=['game_id', 'opp'], how='left')
    for c in ['flags', 'yards', 'off', 'drawn', 'drawn_yards', 'drawn_off']:
        tg[c] = tg[c].fillna(0)
    tg['deff'] = tg['flags'] - tg['off']

    def block(rows):
        n = len(rows)
        if n == 0:
            return None
        home, away = rows[rows['is_home']], rows[~rows['is_home']]
        return {
            'games': int(n),
            'penalties': int(rows['flags'].sum()),
            'yards': int(rows['yards'].sum()),
            'perGame': _r(rows['flags'].mean()),
            'yardsPerGame': _r(rows['yards'].mean(), 1),
            'offensePerGame': _r(rows['off'].mean()),
            'defensePerGame': _r(rows['deff'].mean()),
            'drawnPerGame': _r(rows['drawn'].mean()),
            'drawnYardsPerGame': _r(rows['drawn_yards'].mean(), 1),
            'netPerGame': _r((rows['drawn'] - rows['flags']).mean()),   # + = drew more than committed
            'homePerGame': _r(home['flags'].mean()) if len(home) else None,
            'awayPerGame': _r(away['flags'].mean()) if len(away) else None,
        }

    # Ranks per season (1 = most penalized per game)
    season_team = tg.groupby(['season', 'team'])['flags'].mean().rename('pg').reset_index()
    season_team['rank'] = season_team.groupby('season')['pg'].rank(ascending=False, method='min').astype(int)
    rank_of = {(r.season, r.team): int(r.rank) for r in season_team.itertuples()}
    league_pg = tg[tg['season'] == season]['flags'].mean()

    cur_pen = pen[pen['season'] == season]
    prior_pen = pen[pen['season'] < season]
    prior_seasons = sorted(int(s) for s in tg['season'].unique() if s < season)

    def per_game_types(df, team_col, n_games):
        if not n_games:
            return pd.Series(dtype=float)
        return df.groupby('penalty_type').size() / n_games

    profiles, index = {}, {d: [] for d in DIVISION_ORDER}
    upcoming = reg[(reg['season'] == season) & reg['result'].isna()].sort_values(['gameday', 'gametime'])

    # Comparison baselines (same choices as the home page toggle). "Same weeks" follows the
    # latest week played this season, so it moves forward automatically every week.
    # League "through week" = last week with every game played (a lone Thursday game doesn't
    # count). Each team then compares through its own latest game if that's later.
    from weeks import completed_week
    through_week, _partial = completed_week(schedules, games_played, season)
    span = lambda ss: f"{ss[0]}" if len(ss) == 1 else f"{ss[0]}–{str(ss[-1])[2:]}"
    last3 = prior_seasons[-3:]
    baseline_defs = []
    if (season - 1) in prior_seasons:
        if through_week or len(tg[tg['season'] == season]):
            baseline_defs.append(('sameWeeks', f"{season - 1} through Week {through_week}", f"{season - 1} Wk 1–{through_week}",
                                  None))   # filled in per team below (its own week)
        baseline_defs.append(('lastSeason', f"All of {season - 1}", f"{season - 1}", lambda r: r['season'] == season - 1))
    if len(last3) == 3:
        baseline_defs.append(('last3', f"Last 3 seasons ({span(last3)})", f"{span(last3)} avg", lambda r: r['season'].isin(last3)))
    if len(prior_seasons) > 3:
        baseline_defs.append(('all', f"All seasons ({span(prior_seasons)})", f"{span(prior_seasons)} avg",
                              lambda r: r['season'].isin(prior_seasons)))

    for team in current_teams:
        rows = tg[tg['team'] == team]
        cur = rows[rows['season'] == season]
        last = rows[rows['season'] == season - 1]
        prior = rows[rows['season'] < season]
        cb, lb, ab = block(cur), block(last), block(prior)

        # Penalty types committed (per game), this season vs prior years
        tp_cur = cur_pen[cur_pen['penalty_team'] == team]
        tp_prior = prior_pen[prior_pen['penalty_team'] == team]
        cur_types = per_game_types(tp_cur, 'penalty_team', len(cur))
        prior_types = per_game_types(tp_prior, 'penalty_team', len(prior))
        keys = list(dict.fromkeys(list(cur_types.sort_values(ascending=False).head(8).index) +
                                  list(prior_types.sort_values(ascending=False).head(5).index)))
        committed_types = sorted([{
            'type': str(t),
            'currentPerGame': _r(cur_types.get(t, 0.0)), 'currentCount': int((tp_cur['penalty_type'] == t).sum()),
            'priorPerGame': _r(prior_types.get(t, 0.0)),
        } for t in keys], key=lambda x: (x['currentPerGame'] or 0, x['priorPerGame'] or 0), reverse=True)

        # Penalty types drawn (opponents' penalties in this team's games)
        cur_ids, prior_ids = set(cur['game_id']), set(prior['game_id'])
        dr_cur = cur_pen[cur_pen['game_id'].isin(cur_ids) & (cur_pen['penalty_team'] != team)]
        dr_prior = prior_pen[prior_pen['game_id'].isin(prior_ids) & (prior_pen['penalty_team'] != team)]
        d_cur = per_game_types(dr_cur, 'penalty_team', len(cur))
        d_prior = per_game_types(dr_prior, 'penalty_team', len(prior))
        dkeys = list(dict.fromkeys(list(d_cur.sort_values(ascending=False).head(6).index) +
                                   list(d_prior.sort_values(ascending=False).head(3).index)))
        drawn_types = sorted([{
            'type': str(t), 'currentPerGame': _r(d_cur.get(t, 0.0)), 'priorPerGame': _r(d_prior.get(t, 0.0)),
        } for t in dkeys], key=lambda x: (x['currentPerGame'] or 0, x['priorPerGame'] or 0), reverse=True)

        # Quarters (per game)
        quarters = [{
            'quarter': q,
            'currentPerGame': _r((tp_cur['qtr'] == q).sum() / len(cur)) if len(cur) else None,
            'priorPerGame': _r((tp_prior['qtr'] == q).sum() / len(prior)) if len(prior) else None,
        } for q in (1, 2, 3, 4)]

        # Each comparison baseline: overall rates + per-game rates by type (committed and
        # drawn) and by quarter, so the site can switch comparisons without refetching
        # Penalty-type trends for this team: its most common types since 2020 (+ this
        # season's), per game in every season
        team_all = pen[pen['penalty_team'] == team]
        trend_keys = list(dict.fromkeys(list(team_all['penalty_type'].value_counts().head(12).index) +
                                        [t['type'] for t in committed_types]))
        games_by_season = rows.groupby('season').size()
        type_trends = []
        for t in trend_keys:
            per = team_all[team_all['penalty_type'] == t].groupby('season').size()
            type_trends.append({
                'type': str(t),
                'current': _r(per.get(season, 0) / len(cur)) if len(cur) else None,
                'currentCount': int(per.get(season, 0)),
                'bySeason': [{'season': int(sz), 'perGame': _r(per.get(sz, 0) / n)} for sz, n in games_by_season.items()],
            })

        all_type_keys = set(t['type'] for t in committed_types) | set(trend_keys)
        all_drawn_keys = set(t['type'] for t in drawn_types)
        baselines = {}
        team_week = max(through_week, int(cur['week'].max()) if len(cur) else 0)
        for key, label, short, mask in baseline_defs:
            if key == 'sameWeeks':
                label, short = f"{season - 1} through Week {team_week}", f"{season - 1} Wk 1–{team_week}"
                mask = (lambda tw: (lambda r: (r['season'] == season - 1) & (r['week'] <= tw)))(team_week)
            brows = rows[mask(rows)]
            n = len(brows)
            ids = set(brows['game_id'])
            bp = pen[pen['game_id'].isin(ids)]
            mine, theirs = bp[bp['penalty_team'] == team], bp[bp['penalty_team'] != team]
            tvc, dvc = mine['penalty_type'].value_counts(), theirs['penalty_type'].value_counts()
            baselines[key] = {
                'label': label, 'short': short, **(block(brows) or {'games': 0}),
                'types': {t: _r(tvc.get(t, 0) / n) if n else None for t in all_type_keys},
                'drawnTypes': {t: _r(dvc.get(t, 0) / n) if n else None for t in all_drawn_keys},
                'quarters': [_r((mine['qtr'] == q).sum() / n) if n else None for q in (1, 2, 3, 4)],
            }

        # Players this season
        players = []
        for name, d in tp_cur[tp_cur['penalty_player_name'].notna()].groupby('penalty_player_name'):
            vc = d['penalty_type'].value_counts()
            players.append({'player': name, 'count': int(len(d)), 'yards': int(d['penalty_yards'].sum()),
                            'types': [{'type': k, 'count': int(v)} for k, v in vc.head(3).items()]})
        players.sort(key=lambda x: (x['count'], x['yards']), reverse=True)

        # Crew chiefs: this team's flags per game in each crew's games (all regular seasons)
        crews = []
        for crew, d in rows[rows['crew'].notna()].groupby('crew'):
            if len(d) < MIN_CREW_GAMES:
                continue
            crews.append({'name': crew, 'slug': slugify(crew), 'games': int(len(d)),
                          'perGame': _r(d['flags'].mean()), 'opponentPerGame': _r(d['drawn'].mean()),
                          'lastSeason': int(d['season'].max())})
        crews.sort(key=lambda x: x['perGame'], reverse=True)   # most flags on this team first

        # Season history
        history = []
        for s, d in rows.groupby('season'):
            b = block(d)
            history.append({'season': int(s), 'games': b['games'], 'perGame': b['perGame'],
                            'yardsPerGame': b['yardsPerGame'], 'drawnPerGame': b['drawnPerGame'],
                            'rank': rank_of.get((s, team))})

        # Game log (this season, newest first) + record
        # Head-to-head by opponent, every regular-season meeting in the data
        opponents = []
        for opp_abbr, d in rows.groupby('opp'):
            d = d.sort_values(['season', 'week'])
            last_g = d.iloc[-1]
            res = None
            if pd.notna(last_g['pts']) and pd.notna(last_g['opp_pts']):
                res = 'W' if last_g['pts'] > last_g['opp_pts'] else 'L' if last_g['pts'] < last_g['opp_pts'] else 'T'
            opponents.append({
                'opponent': opp_abbr, 'games': int(len(d)),
                'seasons': sorted(int(x) for x in d['season'].unique()),
                'flagsPerGame': _r(d['flags'].mean()), 'oppFlagsPerGame': _r(d['drawn'].mean()),
                'yardsPerGame': _r(d['yards'].mean(), 1), 'oppYardsPerGame': _r(d['drawn_yards'].mean(), 1),
                'netPerGame': _r((d['drawn'] - d['flags']).mean()),
                'totalFlags': int(d['flags'].sum()), 'totalOppFlags': int(d['drawn'].sum()),
                'homeGames': int(d['is_home'].sum()),
                'lastMet': {'season': int(last_g['season']), 'week': int(last_g['week']), 'home': bool(last_g['is_home']),
                            'score': None if res is None else f"{int(last_g['pts'])}-{int(last_g['opp_pts'])}", 'result': res,
                            'flags': int(last_g['flags']), 'oppFlags': int(last_g['drawn'])},
            })
        opponents.sort(key=lambda o: (o['flagsPerGame'] or 0, o['games']), reverse=True)   # most flags on this team first

        log, w, l, t_ = [], 0, 0, 0
        for _, g in cur.sort_values('week', ascending=False).iterrows():
            res = None
            if pd.notna(g['pts']) and pd.notna(g['opp_pts']):
                res = 'W' if g['pts'] > g['opp_pts'] else 'L' if g['pts'] < g['opp_pts'] else 'T'
                w += res == 'W'; l += res == 'L'; t_ += res == 'T'
            log.append({'gameId': g['game_id'], 'week': int(g['week']), 'date': str(g['gameday']),
                        'opponent': g['opp'], 'home': bool(g['is_home']),
                        'score': None if res is None else f"{int(g['pts'])}-{int(g['opp_pts'])}", 'result': res,
                        'flags': int(g['flags']), 'yards': int(g['yards']), 'opponentFlags': int(g['drawn']),
                        'crew': g['crew'] if pd.notna(g['crew']) else None})

        nxt = upcoming[(upcoming['home_team'] == team) | (upcoming['away_team'] == team)].head(1)
        next_game = None
        if len(nxt):
            n = nxt.iloc[0]
            next_game = {'gameId': n['game_id'], 'week': int(n['week']), 'date': str(n['gameday']),
                         'opponent': n['away_team'] if n['home_team'] == team else n['home_team'],
                         'home': bool(n['home_team'] == team)}

        meta = teams_meta.loc[team] if team in teams_meta.index else None
        division = meta['team_division'] if meta is not None else None
        info = team_info(team)
        rank_cur, rank_last = rank_of.get((season, team)), rank_of.get((season - 1, team))

        profile = {
            'abbr': team, 'name': info.get('name', team), 'logo': info.get('logo'),
            'division': division, 'season': season, 'record': f'{w}-{l}' + (f'-{t_}' if t_ else ''),
            'leaguePerGame': _r(league_pg),
            'current': cb, 'lastSeason': lb, 'allPrior': ab,
            'throughWeek': team_week,
            'baselines': baselines,
            'defaultBaseline': 'sameWeeks' if 'sameWeeks' in baselines else next(iter(baselines), None),
            'priorSeasons': prior_seasons,
            'rank': {'current': rank_cur, 'lastSeason': rank_last, 'of': len(current_teams)},
            'committedTypes': committed_types, 'drawnTypes': drawn_types, 'quarters': quarters,
            'players': players[:8], 'crews': crews, 'history': history, 'games': log,
            'opponents': opponents,
            'typeTrends': type_trends,
            'nextGame': next_game,
            'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        }
        profiles[team] = profile
        if division in index:
            index[division].append({
                'abbr': team, 'name': profile['name'], 'logo': profile['logo'], 'record': profile['record'],
                'games': cb['games'] if cb else 0,
                'perGame': cb['perGame'] if cb else None,
                'yardsPerGame': cb['yardsPerGame'] if cb else None,
                'lastSeasonPerGame': lb['perGame'] if lb else None,
                'baselinePerGame': {k: v.get('perGame') for k, v in baselines.items()},
                'throughWeek': team_week,
                'rank': rank_cur,
            })

    out = data_dir / 'teams'
    out.mkdir(parents=True, exist_ok=True)
    for team, p in profiles.items():
        (out / f'{team}.json').write_text(safe_dumps(p, indent=2, default=str))
    divisions = [{'name': d, 'teams': sorted(index[d], key=lambda x: (x['perGame'] or 0), reverse=True)}
                 for d in DIVISION_ORDER]
    (out / 'index.json').write_text(safe_dumps({
        'season': season, 'leaguePerGame': _r(league_pg), 'divisions': divisions,
        'throughWeek': through_week,
        'baselines': [{'key': k, 'label': l, 'short': sh} for k, l, sh, _ in baseline_defs],
        'defaultBaseline': 'sameWeeks' if any(k == 'sameWeeks' for k, *_ in baseline_defs) else (baseline_defs[0][0] if baseline_defs else None),
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }, indent=2))
    print(f"   ✓ {len(profiles)} team pages ({season}), 8 divisions")
    return {'teams': len(profiles)}
