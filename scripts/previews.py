"""
Game previews: projected penalties for the next week's games.
=============================================================
Called from update_data.py with the data it already loaded.

Model (per team, per penalty type, regular season only):

    expected = league rate (for home or away side, current-season level)
             x team's tendency to COMMIT that type
             x opponent's tendency to DRAW that type
             x crew chief's tendency to CALL that type   (1.0 if crew TBA)

Every factor is a ratio vs the league for the same seasons, weighted toward
recent seasons and shrunk toward 1.0 by a prior worth N games, so thin
samples (4 games, a crew's 3 roughing calls) can't produce wild projections.
Ranges use a negative binomial with dispersion measured from real game totals.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

SEASON_WEIGHTS = {0: 1.0, 1: 0.6, 2: 0.3}   # seasons back -> weight
TEAM_PRIOR_GAMES = 6        # weighted team-games of "league average" mixed into team factors
CREW_PRIOR_GAMES = 10       # weighted crew games mixed into crew factors
LEVEL_PRIOR_TEAM_GAMES = 100  # how fast the league level moves to this season's rate
FACTOR_CLAMP = (0.5, 2.0)
TOP_TYPES = 10


def _poisson_nb_quantiles(mu, phi, qs=(0.1, 0.9)):
    """Quantiles of a negative binomial with mean mu and variance phi*mu."""
    if mu <= 0:
        return [0 for _ in qs]
    if phi <= 1.0001:
        logp = lambda k: -mu + k * math.log(mu) - math.lgamma(k + 1)
    else:
        r = mu / (phi - 1)
        p = r / (r + mu)
        logp = lambda k: (math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
                          + r * math.log(p) + k * math.log(1 - p))
    cdf, k, out, qi = 0.0, 0, [], 0
    qs = sorted(qs)
    while qi < len(qs) and k < 200:
        cdf += math.exp(logp(k))
        while qi < len(qs) and cdf >= qs[qi]:
            out.append(k)
            qi += 1
        k += 1
    return out + [k] * (len(qs) - len(out))


def _nb_prob_at_least(mu, phi, x):
    if mu <= 0:
        return 0.0
    if phi <= 1.0001:
        logp = lambda k: -mu + k * math.log(mu) - math.lgamma(k + 1)
    else:
        r = mu / (phi - 1)
        p = r / (r + mu)
        logp = lambda k: (math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
                          + r * math.log(p) + k * math.log(1 - p))
    return max(0.0, 1.0 - sum(math.exp(logp(k)) for k in range(int(x))))


def _clamp(v):
    return float(min(FACTOR_CLAMP[1], max(FACTOR_CLAMP[0], v)))


def build_previews(data: dict, slugify, team_info, name_fixes: dict, data_dir: Path) -> dict:
    print("\n🔮 Building game previews...")

    schedules = data.get('schedules', pd.DataFrame())
    penalties = data.get('penalties', pd.DataFrame())
    games_played = data.get('games_played', pd.DataFrame())
    officials = data.get('officials', pd.DataFrame())
    if schedules.empty or penalties.empty or games_played.empty:
        print("   ✗ Missing data")
        return {}

    # ---- Target weeks ----
    # Games still to come (dates compared in US Eastern, so a Monday-night game stays
    # "upcoming" all evening). If the current week is partly played (e.g. only Monday
    # night is left), preview those remaining games AND the following week.
    reg_sched = schedules[schedules['game_type'] == 'REG']
    season = int(reg_sched['season'].max())
    today_et = datetime.now(ZoneInfo('America/New_York')).date().isoformat()
    upcoming = reg_sched[(reg_sched['season'] == season) & reg_sched['result'].isna()
                         & (reg_sched['gameday'].astype(str) >= today_et)]
    if upcoming.empty:
        print("   … No upcoming regular-season games")
        return {}
    up_weeks = sorted(int(w) for w in upcoming['week'].unique())
    first = up_weeks[0]
    first_full = reg_sched[(reg_sched['season'] == season) & (reg_sched['week'] == first)]
    target_weeks = [first]
    if len(upcoming[upcoming['week'] == first]) < len(first_full) and len(up_weeks) > 1:
        target_weeks.append(up_weeks[1])   # current week is partly played -> also preview next week

    def load_assignments(week):
        path = data_dir / 'assignments' / f'{season}-week-{week:02d}.json'
        out, meta = {}, {}
        if path.exists():
            a = json.loads(path.read_text())
            meta = a.get('source', {})
            for g in a.get('games', []):
                if g.get('referee'):
                    out[g['game_id']] = {**g, 'referee': name_fixes.get(g['referee'], g['referee'])}
        return out, meta

    # ---- Historical regular-season data (last 3 seasons, weighted) ----
    seasons = [s for s in (season, season - 1, season - 2)]
    weights = {s: SEASON_WEIGHTS[season - s] for s in seasons}

    gp = games_played[games_played.get('season_type', 'REG') == 'REG'] if 'season_type' in games_played else games_played
    gp = gp[gp['season'].isin(seasons)][['game_id', 'season', 'week']].drop_duplicates('game_id')
    teams_by_game = reg_sched[['game_id', 'home_team', 'away_team', 'gameday', 'gametime', 'weekday', 'div_game']]
    gp = gp.merge(teams_by_game, on='game_id', how='inner')
    gp['w'] = gp['season'].map(weights)

    pen = penalties[penalties['game_id'].isin(gp['game_id'])].copy()
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    pen['penalty_yards'] = pd.to_numeric(pen['penalty_yards'], errors='coerce').fillna(0).abs()
    pen = pen[pen['penalty_team'].notna()]
    pen['is_home'] = pen['penalty_team'] == pen['home_team']
    pen['side'] = np.where(pen['penalty_team'] == pen['posteam'], 'offense', 'defense')
    pen['w'] = pen['season'].map(weights)

    top_types = (pen.groupby('penalty_type')['w'].sum().sort_values(ascending=False)
                 .head(TOP_TYPES).index.tolist())
    pen['ptype'] = np.where(pen['penalty_type'].isin(top_types), pen['penalty_type'], 'Other')
    types = top_types + ['Other']

    # Crew chief per game
    chiefs = (officials[officials['position'] == 'Referee'][['game_id', 'name']]
              .dropna().drop_duplicates('game_id').rename(columns={'name': 'crew'}))
    gp = gp.merge(chiefs, on='game_id', how='left')

    # Team-game rows: one per team per game
    tg = pd.concat([
        gp.assign(team=gp['home_team'], opp=gp['away_team'], is_home=True),
        gp.assign(team=gp['away_team'], opp=gp['home_team'], is_home=False),
    ], ignore_index=True)[['game_id', 'season', 'week', 'w', 'team', 'opp', 'is_home', 'crew']]

    counts = (pen.groupby(['game_id', 'penalty_team', 'ptype']).size()
              .unstack(fill_value=0).reindex(columns=types, fill_value=0))
    counts.index = counts.index.set_names(['game_id', 'team'])
    tg = tg.merge(counts.reset_index(), on=['game_id', 'team'], how='left').fillna({t: 0 for t in types})

    # League rate per team-game, by season and side (home/away), per type
    rate = tg.groupby(['season', 'is_home'])[types].mean()   # unweighted within season
    def league_rate(s, home):
        return rate.loc[(s, home)] if (s, home) in rate.index else rate.xs(home, level='is_home').mean()

    tg_exp = np.vstack([league_rate(s, h).values for s, h in zip(tg['season'], tg['is_home'])])
    exp_df = pd.DataFrame(tg_exp, columns=types, index=tg.index)

    # Current league level (shrunk toward the weighted multi-season level)
    cur = tg[tg['season'] == season]
    blend_total = float((tg[types].sum(axis=1) * tg['w']).sum() / tg['w'].sum())
    cur_total = float(cur[types].sum(axis=1).sum())
    level_total = (cur_total + LEVEL_PRIOR_TEAM_GAMES * blend_total) / (len(cur) + LEVEL_PRIOR_TEAM_GAMES)
    mix = {}
    for home in (True, False):
        side = tg[tg['is_home'] == home]
        wt = (side[types].multiply(side['w'], axis=0).sum() / side['w'].sum())
        mix[home] = wt / wt.sum()
    side_level = {h: level_total * (tg[tg['is_home'] == h][types].sum(axis=1) * tg['w']).sum()
                     / (tg[tg['is_home'] == h]['w'].sum() * blend_total) for h in (True, False)}
    base_rate = {h: mix[h] * side_level[h] for h in (True, False)}   # per team-game, by type

    # Average yards per penalty by type
    yds = pen.groupby('ptype').apply(lambda d: np.average(d['penalty_yards'], weights=d['w'])).reindex(types).fillna(8.0)

    # Quarter shares by type (league)
    pq = pen[pen['qtr'].between(1, 4)]
    q_share = (pq.groupby(['ptype', 'qtr'])['w'].sum().unstack(fill_value=0).reindex(index=types, columns=[1, 2, 3, 4], fill_value=0))
    q_share = q_share.div(q_share.sum(axis=1).replace(0, 1), axis=0)

    # ---- Factors ----
    def shrunk_ratio(obs, exp, prior_exp):
        return _clamp((obs + prior_exp) / (exp + prior_exp))

    avg_rate = (base_rate[True] + base_rate[False]) / 2

    def team_factors(team):
        rows = tg[tg['team'] == team]
        e = exp_df.loc[rows.index]
        f = {}
        for t in types:
            obs = float((rows[t] * rows['w']).sum())
            ex = float((e[t] * rows['w']).sum())
            f[t] = shrunk_ratio(obs, ex, TEAM_PRIOR_GAMES * float(avg_rate[t]))
        return f, int((rows['season'] == season).sum())

    def draw_factors(team):
        rows = tg[tg['opp'] == team]     # opponents' penalties against this team
        e = exp_df.loc[rows.index]
        return {t: shrunk_ratio(float((rows[t] * rows['w']).sum()), float((e[t] * rows['w']).sum()),
                                TEAM_PRIOR_GAMES * float(avg_rate[t])) for t in types}

    crew_games = tg.groupby('game_id').agg(crew=('crew', 'first'), w=('w', 'first'))
    game_counts = tg.groupby('game_id')[types].sum()
    game_exp = exp_df.groupby(tg['game_id']).sum()

    def crew_factors(crew):
        ids = crew_games.index[crew_games['crew'] == crew]
        if len(ids) == 0:
            return {t: 1.0 for t in types}, 0, None
        w = crew_games.loc[ids, 'w']
        f = {t: shrunk_ratio(float((game_counts.loc[ids, t] * w).sum()), float((game_exp.loc[ids, t] * w).sum()),
                             CREW_PRIOR_GAMES * 2 * float(avg_rate[t])) for t in types}
        cp = pq[pq['game_id'].isin(ids)]
        tilt = None
        if len(cp):
            cq = cp.groupby('qtr')['w'].sum().reindex([1, 2, 3, 4], fill_value=0)
            lq = pq.groupby('qtr')['w'].sum().reindex([1, 2, 3, 4], fill_value=0)
            prior = 300
            tilt = ((cq + prior * lq / lq.sum()) / (cq.sum() + prior)) / (lq / lq.sum())
        return f, int(len(ids)), tilt

    # Dispersion of real game totals around model-free expectation (var/mean)
    totals = game_counts.sum(axis=1)
    recent = totals[crew_games.index[crew_games.index.isin(gp[gp['season'] >= season - 1]['game_id'])]]
    phi = float(np.clip(recent.var() / recent.mean(), 1.05, 3.0)) if len(recent) > 30 else 1.3

    # League per-game reference for "vs league" and probability thresholds
    league_game = float(base_rate[True].sum() + base_rate[False].sum())

    # ---- Context reference numbers (descriptive only, not in projection) ----
    gtot = gp.set_index('game_id').join(totals.rename('flags'))
    def ctx_avg(mask):
        m = gtot[mask & gtot['season'].ge(season - 2)]
        return (round(float(m['flags'].mean()), 1), int(len(m))) if len(m) else (None, 0)
    thu = ctx_avg(gtot['weekday'] == 'Thursday')
    sun = ctx_avg(gtot['weekday'] == 'Sunday')
    div = ctx_avg(gtot['div_game'] == 1)
    nondiv = ctx_avg(gtot['div_game'] == 0)

    # ---- Current-season team discipline (for the report) ----
    cur_pen = pen[pen['season'] == season]
    cur_tg = tg[tg['season'] == season]
    team_tot = cur_tg.assign(flags=cur_tg[types].sum(axis=1)).groupby('team')['flags'].agg(['sum', 'count'])
    team_tot['per_game'] = team_tot['sum'] / team_tot['count']
    rank = team_tot['per_game'].rank(ascending=False, method='min')

    def discipline(team):
        rows = cur_tg[cur_tg['team'] == team]
        n = len(rows)
        tp = cur_pen[cur_pen['penalty_team'] == team]
        drawn = cur_pen[(cur_pen['penalty_team'] != team) &
                        ((cur_pen['home_team'] == team) | (cur_pen['away_team'] == team))]
        prev = tg[(tg['team'] == team) & (tg['season'] == season - 1)]
        prev_pg = float(prev[types].sum(axis=1).mean()) if len(prev) else None
        return {
            'games': n,
            'perGame': round(len(tp) / n, 2) if n else None,
            'offensePerGame': round((tp['side'] == 'offense').sum() / n, 2) if n else None,
            'defensePerGame': round((tp['side'] == 'defense').sum() / n, 2) if n else None,
            'drawnPerGame': round(len(drawn) / n, 2) if n else None,
            'yardsPerGame': round(tp['penalty_yards'].sum() / n, 1) if n else None,
            'lastSeasonPerGame': round(prev_pg, 2) if prev_pg is not None else None,
            'rank': int(rank.get(team)) if team in rank.index else None,
            'mostCommon': (tp['penalty_type'].value_counts().index[0] if len(tp) else None),
        }

    def watchlist(team, n=4):
        tp = cur_pen[(cur_pen['penalty_team'] == team) & cur_pen['penalty_player_name'].notna()]
        out = []
        for name, d in tp.groupby('penalty_player_name'):
            vc = d['penalty_type'].value_counts()
            out.append({'player': name, 'count': int(len(d)), 'yards': int(d['penalty_yards'].sum()),
                        'types': [{'type': k, 'count': int(v)} for k, v in vc.head(3).items()]})
        out.sort(key=lambda x: (x['count'], x['yards']), reverse=True)
        return out[:n]

    def head_to_head(a, b, n=3):
        mask = (((gp['home_team'] == a) & (gp['away_team'] == b)) | ((gp['home_team'] == b) & (gp['away_team'] == a)))
        allg = gp.copy()
        hist_ids = games_played[games_played['game_id'].isin(
            reg_sched[(((reg_sched['home_team'] == a) & (reg_sched['away_team'] == b)) |
                       ((reg_sched['home_team'] == b) & (reg_sched['away_team'] == a))) &
                      reg_sched['result'].notna()]['game_id'])]['game_id']
        rows = reg_sched[reg_sched['game_id'].isin(hist_ids)].sort_values('gameday', ascending=False).head(n)
        out = []
        for _, r in rows.iterrows():
            p = penalties[penalties['game_id'] == r['game_id']]
            out.append({
                'gameId': r['game_id'], 'season': int(r['season']), 'week': int(r['week']),
                'home': r['home_team'], 'away': r['away_team'],
                'homeScore': None if pd.isna(r['home_score']) else int(r['home_score']),
                'awayScore': None if pd.isna(r['away_score']) else int(r['away_score']),
                'flags': int(len(p)),
                'homeFlags': int((p['penalty_team'] == r['home_team']).sum()),
                'awayFlags': int((p['penalty_team'] == r['away_team']).sum()),
                'crew': chiefs.set_index('game_id')['crew'].get(r['game_id']),
            })
        return out

    def build_week(week, week_games):
        # ---- Build each game ----
        assignments, assign_meta = load_assignments(week)
        all_week = reg_sched[(reg_sched['season'] == season) & (reg_sched['week'] == week)]
        remaining_only = len(week_games) < len(all_week)
        previews = []
        for _, g in week_games.sort_values(['gameday', 'gametime', 'game_id']).iterrows():
            home, away = g['home_team'], g['away_team']
            crew = assignments.get(g['game_id'], {}).get('referee')
            hc, h_games = team_factors(home)
            ac, a_games = team_factors(away)
            hd, ad = draw_factors(home), draw_factors(away)
            cf, crew_n, crew_tilt = crew_factors(crew) if crew else ({t: 1.0 for t in types}, 0, None)

            rows = []
            lam_h = lam_a = 0.0
            L0 = L1 = L2 = 0.0
            q_home = np.zeros(4)
            q_away = np.zeros(4)
            for t in types:
                bh, ba = float(base_rate[True][t]), float(base_rate[False][t])
                eh = bh * hc[t] * ad[t] * cf[t]     # home team commits, away team draws
                ea = ba * ac[t] * hd[t] * cf[t]
                lam_h += eh
                lam_a += ea
                L0 += bh + ba
                L1 += (bh + ba) * cf[t]
                L2 += bh * cf[t] * hc[t] + ba * cf[t] * hd[t]
                share = q_share.loc[t].values
                if crew_tilt is not None:
                    share = share * crew_tilt.values
                    share = share / share.sum()
                q_home += eh * share
                q_away += ea * share
                rows.append({
                    'type': t, 'home': round(eh, 2), 'away': round(ea, 2), 'total': round(eh + ea, 2),
                    'leagueTotal': round(bh + ba, 2), 'yardsEach': round(float(yds[t]), 1),
                    'factors': {'homeCommit': round(hc[t], 2), 'awayCommit': round(ac[t], 2),
                                'homeDraw': round(hd[t], 2), 'awayDraw': round(ad[t], 2), 'crew': round(cf[t], 2)},
                })
            rows.sort(key=lambda r: (r['type'] != 'Other', r['total']), reverse=True)   # most expected first, Other last
            total = lam_h + lam_a
            L3 = total
            lo, hi = _poisson_nb_quantiles(total, phi, (0.1, 0.9))
            h_lo, h_hi = _poisson_nb_quantiles(lam_h, phi, (0.1, 0.9))
            a_lo, a_hi = _poisson_nb_quantiles(lam_a, phi, (0.1, 0.9))
            threshold = int(round(league_game))

            crew_block = None
            if crew:
                tilts = sorted(((t, cf[t]) for t in types if t != 'Other'), key=lambda x: abs(math.log(x[1])), reverse=True)
                crew_block = {
                    'name': crew, 'slug': slugify(crew), 'gamesInModel': crew_n,
                    'overallFactor': round(L1 / L0, 3) if L0 else 1.0,
                    'typeTilts': [{'type': t, 'factor': round(f, 2)} for t, f in tilts[:4]],
                    'quarterTilt': [round(float(x), 2) for x in crew_tilt.values] if crew_tilt is not None else None,
                }

            gametime = str(g.get('gametime') or '')
            hour = int(gametime.split(':')[0]) if gametime[:2].isdigit() else None
            primetime = bool((hour is not None and hour >= 19) or g.get('weekday') in ('Thursday', 'Monday'))
            spread = None if pd.isna(g.get('spread_line')) else float(g['spread_line'])
            a_meta = assignments.get(g['game_id'], {})

            previews.append({
                'gameId': g['game_id'], 'season': season, 'week': week,
                'gameday': str(g['gameday']), 'gametime': gametime or None, 'weekday': g.get('weekday'),
                'network': a_meta.get('network'),
                'homeTeam': {'abbr': home, **team_info(home)}, 'awayTeam': {'abbr': away, **team_info(away)},
                'crew': crew_block,
                'projection': {
                    'total': round(total, 1), 'home': round(lam_h, 1), 'away': round(lam_a, 1),
                    'range': [lo, hi], 'homeRange': [h_lo, h_hi], 'awayRange': [a_lo, a_hi],
                    'yards': round(sum(r['total'] * r['yardsEach'] for r in rows), 0),
                    'homeYards': round(sum(r['home'] * r['yardsEach'] for r in rows), 0),
                    'awayYards': round(sum(r['away'] * r['yardsEach'] for r in rows), 0),
                    'leagueAverage': round(league_game, 1),
                    'vsLeaguePct': round((total / league_game - 1) * 100, 1),
                    'overThreshold': threshold,
                    'probOver': round(_nb_prob_at_least(total, phi, threshold + 1), 3),
                    'byQuarter': [{'quarter': i + 1, 'home': round(float(q_home[i]), 2), 'away': round(float(q_away[i]), 2)}
                                  for i in range(4)],
                    'drivers': [
                        {'label': 'Crew chief' if crew else 'Crew chief (TBA)', 'value': round(L1 - L0, 2)},
                        {'label': f'{home} discipline & what it draws', 'value': round(L2 - L1, 2)},
                        {'label': f'{away} discipline & what it draws', 'value': round(L3 - L2, 2)},
                    ],
                },
                'byType': rows,
                'teams': {
                    'home': {**discipline(home), 'watchlist': watchlist(home), 'gamesInModel': h_games},
                    'away': {**discipline(away), 'watchlist': watchlist(away), 'gamesInModel': a_games},
                },
                'headToHead': head_to_head(home, away),
                'context': {
                    'primetime': primetime,
                    'divisionGame': bool(g.get('div_game') == 1),
                    'neutralSite': g.get('location') == 'Neutral',
                    'roof': None if pd.isna(g.get('roof')) else g.get('roof'),
                    'surface': None if pd.isna(g.get('surface')) else g.get('surface'),
                    'temp': None if pd.isna(g.get('temp')) else int(g['temp']),
                    'wind': None if pd.isna(g.get('wind')) else int(g['wind']),
                    'homeRest': None if pd.isna(g.get('home_rest')) else int(g['home_rest']),
                    'awayRest': None if pd.isna(g.get('away_rest')) else int(g['away_rest']),
                    'spread': spread, 'total': None if pd.isna(g.get('total_line')) else float(g['total_line']),
                    'stadium': None if pd.isna(g.get('stadium')) else g.get('stadium'),
                    'homeQB': g.get('home_qb_name'), 'awayQB': g.get('away_qb_name'),
                    'homeCoach': g.get('home_coach'), 'awayCoach': g.get('away_coach'),
                },
            })

        previews.sort(key=lambda p: p['projection']['total'], reverse=True)   # most flags first

        result = {
            'season': season, 'week': week,
            'remainingOnly': remaining_only,   # True when earlier games this week are already played
            'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'assignments': {'assigned': sum(1 for g in week_games['game_id'] if g in assignments), 'games': len(week_games),
                            'source': assign_meta or None},
            'model': {
                'seasons': seasons, 'seasonWeights': {str(k): v for k, v in weights.items()},
                'leagueAveragePerGame': round(league_game, 1), 'dispersion': round(phi, 2),
                'regularSeasonOnly': True,
            },
            'contextReference': {
                'thursday': thu[0], 'sunday': sun[0], 'division': div[0], 'nonDivision': nondiv[0],
            },
            'games': previews,
        }

        out_dir = data_dir / 'previews'
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f'{season}-week-{week:02d}.json'
        result['file'] = f'previews/{fname}'
        (out_dir / fname).write_text(json.dumps(result, indent=2, default=str))
        print(f"   ✓ {season} Week {week}{' (remaining games)' if remaining_only else ''}: {len(previews)} games, "
              f"crews assigned for {result['assignments']['assigned']}")
        print(f"   💾 previews/{fname}")
        return result

    results = []
    for wk in target_weeks:
        wk_games = upcoming[upcoming['week'] == wk].copy()
        results.append(build_week(wk, wk_games))

    out_dir = data_dir / 'previews'
    (out_dir / 'latest.json').write_text(json.dumps({
        'season': season,
        'weeks': [{'week': r['week'], 'file': r['file'], 'remainingOnly': r['remainingOnly'],
                   'games': len(r['games'])} for r in results],
        # backward compatible single pointer (first week)
        'week': results[0]['week'], 'file': results[0]['file'],
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }, indent=2))
    return {'weeks': results}
