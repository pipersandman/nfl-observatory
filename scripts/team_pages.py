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
            'priorSeasons': prior_seasons,
            'rank': {'current': rank_cur, 'lastSeason': rank_last, 'of': len(current_teams)},
            'committedTypes': committed_types, 'drawnTypes': drawn_types, 'quarters': quarters,
            'players': players[:8], 'crews': crews, 'history': history, 'games': log,
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
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }, indent=2))
    print(f"   ✓ {len(profiles)} team pages ({season}), 8 divisions")
    return {'teams': len(profiles)}
