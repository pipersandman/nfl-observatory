"""
Stat miner: the most unusual stats of the latest completed week
================================================================
Every week, generate thousands of candidate stats (who x what x when), score each
for how unusual it really is, remove what's likely just luck, and write a ranked,
verified shortlist for posts, recaps and Fact of the Day.

  1. Candidates   league week, games, team-games, crew games, player games, and
                  season-to-date for teams, crews and players, across ~25 metrics
  2. Rarity       rank against every comparable since 2015 (records, top-5s,
                  "first since"); season-to-date compared through the same week
  3. Surprise     how unlikely the count is given the entity's own normal
                  (Poisson tail probability vs its baseline, shrunk for small samples)
  4. Luck filter  Benjamini-Hochberg false-discovery control across all candidates;
                  near-duplicates collapsed (same entity and play, best one kept)
  5. Evidence     every stat is recomputed from the play-by-play, with the plays listed

Output (not deployed to the site): reports/miner/<season>-week-NN.md and .json.
Internal research: patterns, not motives; check context before publishing.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from flag_impact import classify
from weeks import completed_week

OUT = Path(__file__).resolve().parent.parent / 'reports' / 'miner'
FDR_Q = 0.10            # keep candidates whose false-discovery-adjusted p-value is under 10%
TOP_N = 30
PRE_SNAP = {'False Start', 'Defensive Offside', 'Neutral Zone Infraction', 'Encroachment', 'Delay of Game',
            'Illegal Formation', 'Illegal Shift', 'Illegal Motion', 'Defensive Delay of Game'}
TOP_TYPES = 12          # penalty types tracked individually


# --------------------------------------------------------------------------- helpers

def _pois_tail(k, mu):
    """P(X >= k) for X ~ Poisson(mu): how surprising a count this high is."""
    if mu <= 0:
        return 1.0 if k <= 0 else 0.0
    if k <= 0:
        return 1.0
    # 1 - CDF(k-1), computed in log space for stability
    terms = [math.exp(-mu + i * math.log(mu) - math.lgamma(i + 1)) for i in range(int(k))]
    return max(0.0, min(1.0, 1 - sum(terms)))


def _rank(values, value):
    """Rank (1 = highest) of value among values, plus the number of comparables."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    return int((v > value).sum()) + 1, int(len(v))


def _bh(pvals):
    """Benjamini-Hochberg adjusted p-values."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    if not n:
        return p
    order = np.argsort(p)
    adj = np.empty(n)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        j = order[i]
        prev = min(prev, p[j] * n / (i + 1))
        adj[j] = prev
    return adj


def _ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _rank_phrase(r, n, what):
    if r == 1:
        return f"the most {what}"
    return f"the {_ordinal(r)} most {what}"


# --------------------------------------------------------------------------- data

def _prepare(data):
    sched = data['schedules']
    reg = sched[sched['game_type'] == 'REG']
    season = int(reg['season'].max())
    done, _ = completed_week(sched, data['games_played'], season)
    pen = data['penalties']
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    pen = pen[pen['penalty_team'].notna()].copy()
    pen['penalty_yards'] = pd.to_numeric(pen['penalty_yards'], errors='coerce').fillna(0).abs()
    fl = classify(pen, data.get('wp_tables'))
    fl['pre_snap'] = fl['penalty_type'].isin(PRE_SNAP)
    off = data['officials']
    crew = (off[off['position'] == 'Referee'].dropna(subset=['game_id']).drop_duplicates('game_id')
            .set_index('game_id')['name'].to_dict())
    gp = data['games_played']
    if 'season_type' in gp.columns:
        gp = gp[gp['season_type'] == 'REG']
    games = gp[['game_id']].drop_duplicates().merge(
        reg[['game_id', 'season', 'week', 'home_team', 'away_team', 'home_score', 'away_score', 'gameday']], on='game_id')
    games['crew'] = games['game_id'].map(crew)
    fl = fl.merge(games[['game_id', 'crew']], on='game_id', how='left')
    return season, done, fl, games


def _game_table(fl, games):
    """One row per game: totals and splits."""
    g = fl.groupby('game_id')
    t = pd.DataFrame({
        'flags': g.size(), 'yards': g['penalty_yards'].sum(), 'firstDowns': g['first_down_given'].sum(),
        'points': g['cost_epa'].sum(), 'winChances': g['cost_wp'].sum() if 'cost_wp' in fl else np.nan,
        'tdsErased': g['td_erased'].sum(), 'q4': g.apply(lambda d: (d['qtr'] >= 4).sum()),
        'preSnap': g['pre_snap'].sum(),
    })
    out = games.merge(t, left_on='game_id', right_index=True, how='left').fillna({c: 0 for c in t.columns})
    by_team = fl.groupby(['game_id', 'penalty_team']).size()
    home = [by_team.get((g, h), 0) for g, h in zip(out['game_id'], out['home_team'])]
    away = [by_team.get((g, a_), 0) for g, a_ in zip(out['game_id'], out['away_team'])]
    out['oneSided'] = np.abs(np.array(home) - np.array(away))     # flag gap between the two teams
    return out


def _team_games(fl, games):
    g = fl.groupby(['game_id', 'penalty_team'])
    t = pd.DataFrame({'flags': g.size(), 'yards': g['penalty_yards'].sum(), 'points': g['cost_epa'].sum(),
                      'firstDowns': g['first_down_given'].sum(), 'tdsErased': g['td_erased'].sum()}).reset_index()
    t = t.rename(columns={'penalty_team': 'team'}).merge(games[['game_id', 'season', 'week', 'home_team', 'away_team', 'crew']], on='game_id')
    # include team-games with zero flags
    allg = pd.concat([games[['game_id', 'season', 'week', 'crew', 'home_team', 'away_team']].assign(team=games['home_team']),
                      games[['game_id', 'season', 'week', 'crew', 'home_team', 'away_team']].assign(team=games['away_team'])])
    t = allg.merge(t.drop(columns=['season', 'week', 'home_team', 'away_team', 'crew']), on=['game_id', 'team'], how='left').fillna(
        {'flags': 0, 'yards': 0, 'points': 0, 'firstDowns': 0, 'tdsErased': 0})
    t['opponent'] = np.where(t['team'] == t['home_team'], t['away_team'], t['home_team'])
    return t


# --------------------------------------------------------------------------- candidates

def _cands_week(fl, games, season, week, types):
    """League week vs every regular-season week since the data begins."""
    gw = games.groupby(['season', 'week']).size().rename('games')
    f = fl.merge(games[['game_id', 'season', 'week']], on=['game_id'], suffixes=('', '_g'))
    if 'season_g' in f.columns:
        f['season'], f['week'] = f['season_g'], f['week_g']
    agg = f.groupby(['season', 'week']).agg(flags=('penalty_type', 'size'), yards=('penalty_yards', 'sum'),
                                            firstDowns=('first_down_given', 'sum'), points=('cost_epa', 'sum'),
                                            tdsErased=('td_erased', 'sum'))
    for t in types:
        agg[f't:{t}'] = f[f['penalty_type'] == t].groupby(['season', 'week']).size()
    agg = agg.join(gw).fillna(0)
    out = []
    if (season, week) not in agg.index:
        return out
    cur = agg.loc[(season, week)]
    hist = agg
    metrics = [('flags', 'flags per game', True), ('yards', 'penalty yards per game', True),
               ('firstDowns', 'first downs by penalty per game', True), ('points', 'expected points given away to flags per game', True),
               ('tdsErased', 'touchdowns wiped out by penalties', False)] + [(f't:{t}', f'{t.lower()} calls', False) for t in types]
    for col, label, per_game in metrics:
        vals = hist[col] / hist['games'] if per_game else hist[col]
        v = cur[col] / cur['games'] if per_game else cur[col]
        r, n = _rank(vals.values, v)
        # surprise: count vs the average week, scaled to this week's games
        base = (hist[col] / hist['games']).drop(index=(season, week), errors='ignore').mean() * cur['games']
        p = _pois_tail(cur[col], base) if not per_game or col in ('flags', 'firstDowns', 'tdsErased') or col.startswith('t:') else r / (n + 1)
        out.append({'level': 'league week', 'entity': f'Week {week}', 'metric': label, 'value': round(float(v), 2),
                    'count': int(cur[col]) if not per_game else None, 'baseline': round(float(base / cur['games'] if per_game else base), 2),
                    'rank': r, 'of': n, 'scope': f'regular-season weeks since {int(hist.index.get_level_values(0).min())}',
                    'p': min(p, r / (n + 1) * 2), 'key': ('week', col)})
    return out


def _cands_games(gt, season, week):
    out = []
    cur = gt[(gt['season'] == season) & (gt['week'] == week)]
    first = int(gt['season'].min())
    for col, label in [('flags', 'flags'), ('yards', 'penalty yards'), ('points', 'expected points given away'),
                       ('winChances', 'win chances swung by flags'), ('firstDowns', 'first downs by penalty'),
                       ('q4', 'fourth-quarter flags'), ('oneSided', 'more flags on one team than the other'),
                       ('tdsErased', 'touchdowns wiped out')]:
        if col not in gt:
            continue
        allv = gt[col].values
        mean = gt[col].mean()
        for _, g in cur.iterrows():
            r, n = _rank(allv, g[col])
            if r > max(25, n * 0.01):          # only top ~1% of games
                continue
            p = _pois_tail(g[col], mean) if col in ('flags', 'firstDowns', 'q4', 'tdsErased') else r / (n + 1)
            out.append({'level': 'game', 'entity': f"{g['away_team']} @ {g['home_team']}", 'game_id': g['game_id'], 'crew': g['crew'],
                        'metric': label, 'value': round(float(g[col]), 2), 'baseline': round(float(mean), 2),
                        'rank': r, 'of': n, 'scope': f'regular-season games since {first}', 'p': p, 'key': ('game', g['game_id'])})
    return out


def _cands_team_games(tg, season, week):
    out = []
    cur = tg[(tg['season'] == season) & (tg['week'] == week)]
    first = int(tg['season'].min())
    for col, label in [('flags', 'flags on one team'), ('yards', 'penalty yards on one team'),
                       ('points', 'expected points one team gave away'), ('firstDowns', 'first downs one team gave by penalty')]:
        allv = tg[col].values
        for _, t in cur.iterrows():
            r, n = _rank(allv, t[col])
            if r > max(30, n * 0.01):
                continue
            # surprise vs the team's own average before this game
            own = tg[(tg['team'] == t['team']) & ((tg['season'] < season) | (tg['week'] < week))][col]
            mu = (own.sum() + 10 * tg[col].mean()) / (len(own) + 10)        # shrunk toward league
            p = _pois_tail(t[col], mu) if col in ('flags', 'firstDowns') else r / (n + 1)
            out.append({'level': 'team game', 'entity': f"{t['team']} vs {t['opponent']}", 'team': t['team'], 'game_id': t['game_id'], 'crew': t['crew'],
                        'metric': label, 'value': round(float(t[col]), 2), 'baseline': round(float(mu), 2),
                        'rank': r, 'of': n, 'scope': f'team-games since {first}', 'p': p, 'key': ('game', t['game_id'], t['team'])})
    return out


def _cands_crews(gt, season, week):
    """This week's game vs the crew chief's own normal, and crew season-to-date vs all crew-seasons through the same week."""
    out = []
    cur = gt[(gt['season'] == season) & (gt['week'] == week) & gt['crew'].notna()]
    for _, g in cur.iterrows():
        prior = gt[(gt['crew'] == g['crew']) & ((gt['season'] < season) | (gt['week'] < week))]
        if len(prior) < 10:
            continue
        mu = prior['flags'].mean()
        p = _pois_tail(g['flags'], mu)
        r, n = _rank(prior['flags'].values.tolist() + [g['flags']], g['flags'])
        out.append({'level': 'crew game', 'entity': g['crew'], 'game_id': g['game_id'], 'crew': g['crew'],
                    'metric': f"flags in {g['away_team']} @ {g['home_team']} vs his crew's average",
                    'value': int(g['flags']), 'baseline': round(float(mu), 2), 'rank': r, 'of': n,
                    'scope': f"his crew's games since {int(prior['season'].min())}", 'p': p, 'key': ('game', g['game_id'])})
    # season to date through the same week
    s2d = gt[gt['week'] <= week].groupby(['season', 'crew']).agg(games=('flags', 'size'), flags=('flags', 'sum'))
    s2d = s2d[s2d['games'] >= max(2, week // 2)]
    s2d['perGame'] = s2d['flags'] / s2d['games']
    if season in s2d.index.get_level_values(0):
        lg = s2d['flags'].sum() / s2d['games'].sum()
        for (s_, c), row in s2d.loc[season].assign(season=season).reset_index().set_index(['season', 'crew']).iterrows():
            r, n = _rank(s2d['perGame'].values, row['perGame'])
            if r > 5:
                continue
            out.append({'level': 'crew season', 'entity': c, 'crew': c, 'metric': f'flags per game through Week {week}',
                        'value': round(float(row['perGame']), 2), 'baseline': round(float(lg), 2), 'rank': r, 'of': n,
                        'scope': f'crew-seasons through Week {week} since {int(s2d.index.get_level_values(0).min())}',
                        'p': _pois_tail(row['flags'], lg * row['games']), 'key': ('crewseason', c)})
    return out


def _cands_team_seasons(tg, season, week):
    out = []
    s2d = tg[tg['week'] <= week].groupby(['season', 'team']).agg(games=('flags', 'size'), flags=('flags', 'sum'),
                                                                    yards=('yards', 'sum'), points=('points', 'sum'),
                                                                    tdsErased=('tdsErased', 'sum'))
    first = int(s2d.index.get_level_values(0).min())
    for col, label, per in [('flags', 'flags per game', True), ('yards', 'penalty yards per game', True),
                            ('points', 'expected points given away per game', True), ('tdsErased', 'touchdowns wiped out by own flags', False)]:
        vals = s2d[col] / s2d['games'] if per else s2d[col]
        lg = (s2d[col].sum() / s2d['games'].sum())
        for team, row in s2d.loc[season].iterrows() if season in s2d.index.get_level_values(0) else []:
            v = row[col] / row['games'] if per else row[col]
            r, n = _rank(vals.values, v)
            if r > 5:
                continue
            p = _pois_tail(row[col], lg * row['games']) if col in ('flags', 'tdsErased') else r / (n + 1)
            out.append({'level': 'team season', 'entity': team, 'team': team, 'metric': f'{label} through Week {week}',
                        'value': round(float(v), 2), 'baseline': round(float(lg if per else lg * row['games']), 2),
                        'rank': r, 'of': n, 'scope': f'team-seasons through Week {week} since {first}', 'p': p, 'key': ('teamseason', team, col)})
    # fewest (clean) as well
    v = s2d['flags'] / s2d['games']
    for team, row in s2d.loc[season].iterrows() if season in s2d.index.get_level_values(0) else []:
        x = row['flags'] / row['games']
        r = int((v < x).sum()) + 1
        if r <= 3:
            out.append({'level': 'team season', 'entity': team, 'team': team, 'metric': f'fewest flags per game through Week {week}',
                        'value': round(float(x), 2), 'baseline': round(float(v.mean()), 2), 'rank': r, 'of': int(len(v)),
                        'scope': f'team-seasons through Week {week} since {first}', 'p': r / (len(v) + 1), 'key': ('teamseason', team, 'fewest')})
    return out


def _cands_players(fl, season, week):
    out = []
    f = fl[fl['penalty_player_name'].notna()].copy()
    f['player'] = f['penalty_player_name'] + ' (' + f['penalty_team'] + ')'
    # single game: 3+ flags on one player
    pg = f.groupby(['season', 'week', 'game_id', 'player']).size().rename('flags').reset_index()
    cur = pg[(pg['season'] == season) & (pg['week'] == week)]
    first = int(pg['season'].min())
    for _, r_ in cur[cur['flags'] >= 3].iterrows():
        r, n = _rank(pg['flags'].values, r_['flags'])
        out.append({'level': 'player game', 'entity': r_['player'], 'game_id': r_['game_id'], 'metric': 'flags on one player in a game',
                    'value': int(r_['flags']), 'baseline': round(float(pg['flags'].mean()), 2), 'rank': r, 'of': n,
                    'scope': f'player-games with a flag since {first}', 'p': r / (n + 1), 'key': ('player', r_['player'], 'game')})
    # season to date: overall and by type
    s2d = f[f['week'] <= week].groupby(['season', 'player']).size().rename('flags')
    for player, v in s2d.loc[season].items() if season in s2d.index.get_level_values(0) else []:
        r, n = _rank(s2d.values, v)
        if r <= 5:
            out.append({'level': 'player season', 'entity': player, 'metric': f'flags through Week {week}', 'value': int(v),
                        'baseline': round(float(s2d.mean()), 2), 'rank': r, 'of': n,
                        'scope': f'player-seasons through Week {week} since {first}', 'p': r / (n + 1), 'key': ('player', player, 'season')})
    for t in ['Offensive Holding', 'Defensive Pass Interference', 'False Start', 'Roughing the Passer', 'Unnecessary Roughness', 'Defensive Holding']:
        s2t = f[(f['week'] <= week) & (f['penalty_type'] == t)].groupby(['season', 'player']).size()
        if season not in s2t.index.get_level_values(0):
            continue
        for player, v in s2t.loc[season].items():
            r, n = _rank(s2t.values, v)
            if r <= 3 and v >= 3:
                out.append({'level': 'player season', 'entity': player, 'metric': f'{t.lower()} calls through Week {week}', 'value': int(v),
                            'baseline': round(float(s2t.mean()), 2), 'rank': r, 'of': n,
                            'scope': f'player-seasons through Week {week} since {first}', 'p': r / (n + 1), 'key': ('player', player, t)})
    return out


def _cands_flags(fl, season, week):
    """Single flags: the costliest by points and by win chances, vs every flag since the data begins."""
    out = []
    cur = fl[(fl['season'] == season) & (fl['week'] == week)]
    first = int(fl['season'].min())
    for col, label in [('cost_epa', 'expected points cost of one flag'), ('cost_wp', 'win chances cost of one flag')]:
        if col not in fl:
            continue
        allv = fl[col].values
        for _, r_ in cur.sort_values(col, ascending=False).head(3).iterrows():
            if pd.isna(r_[col]):
                continue
            r, n = _rank(allv, r_[col])
            out.append({'level': 'flag', 'entity': f"{r_['penalty_type']} on {r_['penalty_team']} ({r_.get('penalty_player_name') or 'team'})",
                        'game_id': r_['game_id'], 'metric': label,
                        'value': round(float(r_[col] * (100 if col == 'cost_wp' else 1)), 2), 'baseline': None,
                        'rank': r, 'of': n, 'scope': f'flags since {first}', 'p': r / (n + 1),
                        'desc': r_['desc'], 'key': ('flag', r_['game_id'], int(r_['qtr']), str(r_['time']))})
    return out


# --------------------------------------------------------------------------- write-up

def _fmt(v):
    v = float(v)
    return f"{int(v):,}" if v.is_integer() else f"{v:,.1f}" if abs(v) >= 10 else f"{v:,.2f}"


def _sentence(c):
    v = _fmt(c['value'])
    pct = '%' if 'win chances' in c['metric'] else ''
    rk = _rank_phrase(c['rank'], c['of'], 'of ' + c['scope'] if c['rank'] > 1 else 'of ' + c['scope'])
    vs = f" (normal: {_fmt(c['baseline'])})" if c.get('baseline') not in (None, 0) and c['level'] not in ('flag',) else ''
    if c['rank'] == 1:
        head = 'Record'
    elif c['rank'] <= 3:
        head = f"{_ordinal(c['rank'])} highest"
    else:
        head = f"Top {c['rank']}"
    return f"**{head}: {c['entity']}, {v}{pct} {c['metric']}**{vs}: {_ordinal(c['rank'])} of {c['of']:,} {c['scope']}."


def _evidence(c, fl):
    if c['level'] == 'flag':
        return [c.get('desc', '')[:240]]
    gid = c.get('game_id')
    if not gid:
        return []
    f = fl[fl['game_id'] == gid]
    if c.get('team'):
        f = f[f['penalty_team'] == c['team']]
    if c['level'] == 'player game':
        f = f[(f['penalty_player_name'] + ' (' + f['penalty_team'] + ')') == c['entity']]
    f = f.sort_values('cost_epa', ascending=False)
    return [f"Q{int(r.qtr)} {r.time} {r.penalty_team} {r.penalty_type}"
            + (f" ({r.penalty_player_name})" if isinstance(r.penalty_player_name, str) else '')
            + f", {int(r.penalty_yards)} yds, {r.cost_epa:.1f} pts" for r in f.head(4).itertuples()]


def build_stat_miner(data):
    print("\n⛏️  Mining this week's unusual stats...")
    season, week, fl, games = _prepare(data)
    if not week:
        print('   (no completed week yet)')
        return None
    types = list(fl['penalty_type'].value_counts().head(TOP_TYPES).index)
    gt = _game_table(fl, games)
    tg = _team_games(fl, games)
    cands = (_cands_week(fl, games, season, week, types) + _cands_games(gt, season, week) + _cands_team_games(tg, season, week)
             + _cands_crews(gt, season, week) + _cands_team_seasons(tg, season, week) + _cands_players(fl, season, week)
             + _cands_flags(fl, season, week))
    if not cands:
        return None
    df = pd.DataFrame(cands)
    df['p'] = df['p'].clip(1e-12, 1)
    df['q'] = _bh(df['p'].values)
    # keep the luck-filtered ones, best per key (one stat per game / entity)
    keep = df[(df['q'] <= FDR_Q) | (df['rank'] == 1)].copy()
    keep['score'] = -np.log10(keep['p']) + np.where(keep['rank'] == 1, 2.0, np.where(keep['rank'] <= 3, 1.0, 0)) \
        + keep['level'].map({'league week': 1.5, 'crew game': 0.8, 'game': 0.6, 'team season': 0.6, 'crew season': 0.6}).fillna(0)
    keep['k'] = keep['key'].map(str)
    keep = keep.sort_values('score', ascending=False).drop_duplicates('k').head(TOP_N)

    items = []
    for _, c in keep.iterrows():
        c = c.to_dict()
        items.append({**{k: c[k] for k in ('level', 'entity', 'metric', 'value', 'baseline', 'rank', 'of', 'scope') if k in c},
                      'p': float(c['p']), 'q': float(c['q']), 'score': round(float(c['score']), 2),
                      'sentence': _sentence(c), 'evidence': _evidence(c, fl), 'crew': c.get('crew')})
    OUT.mkdir(parents=True, exist_ok=True)
    stem = f'{season}-week-{week:02d}'
    (OUT / f'{stem}.json').write_text(json.dumps({'season': season, 'week': week, 'candidates': int(len(df)),
                                                  'kept': int(len(keep)), 'fdr': FDR_Q, 'items': items}, indent=2, default=str))
    md = [f"# Week {week} {season}: unusual stats (stat miner)", '',
          f"{len(df):,} standout candidates (each already in the top 1–5% of its comparables) scored; "
          f"{int(((df['q'] <= FDR_Q) | (df['rank'] == 1)).sum())} passed the luck filter "
          f"(false discovery rate ≤ {int(FDR_Q * 100)}%, or an outright record); top {len(items)} shown, one per game or entity.",
          '', '*Internal research. Every number is computed from nflverse play-by-play (regular season, accepted penalties). '
          'Crew stats are by crew chief. Patterns, not motives; check context before publishing.*', '']
    for i, it in enumerate(items, 1):
        md.append(f"{i}. {it['sentence']}" + (f" Crew chief: {it['crew']}." if it.get('crew') and it['level'] in ('game', 'team game') else '')
                  + f"  \n   <sub>{it['level']} · surprise p={it['p']:.1e} · q={it['q']:.2f}</sub>")
        for ev in it['evidence']:
            md.append(f"   - {ev}")
    (OUT / f'{stem}.md').write_text('\n'.join(md) + '\n')
    print(f"   ✓ {len(df):,} candidates · {len(items)} kept → reports/miner/{stem}.md")
    return items
