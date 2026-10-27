"""
Crew styles: each active crew chief's calling fingerprint
=========================================================
Career window: every regular season before the current one (2015 onward), so
styles are stable. Multi-season numbers are season-adjusted: each crew is compared
with the league in the seasons it worked (league levels moved ~18% over the
window), expressed at the window's overall league level. Also single-season and
current-season (week-by-week) views for the map.

For each crew chief, compared with the league over the same games:
  volume        flags per game
  size          yards per flag, expected points per flag (from flag_impact)
  timing        share pre-snap, share in the 4th quarter
  side          share on the offense, share on the home team
  mix           per-game rate of each common penalty type, shrunk toward the
                league rate (SHRINK games of prior) so rare calls don't dominate

Outputs the standout traits (largest differences across crews, in plain words),
the two most similar crews (distance on the standardized fingerprint) and the
style quadrant (flags per game x yards per flag, the Crew Style Map).

Crews change around the chief every year, so these are crew-chief-level styles.
"""
import re
from datetime import datetime, timezone

import pandas as pd

from flag_impact import classify

SHRINK = 20          # games of league-average prior for per-type rates
MIN_GAMES = 10
TOP_TYPES = 10
PRE_SNAP = {
    'False Start', 'Delay of Game', 'Defensive Offside', 'Neutral Zone Infraction', 'Encroachment',
    'Illegal Formation', 'Illegal Shift', 'Illegal Motion', 'Offensive Offside', 'Defensive Delay of Game',
    'Illegal Substitution', 'Too Many Men on Field', 'Offside on Free Kick',
}


def _slug(name):
    s = re.sub(r'[^a-z0-9\s-]', '', name.lower())
    return re.sub(r'[\s_]+', '-', s).strip('-')


def _r(x, d=2):
    return None if x is None or pd.isna(x) else round(float(x), d)


QUADS = {(True, True): ('game-changers', 'Game-changers', 'lots of flags, and big ones'),
         (True, False): ('stop-and-start', 'Stop-and-start', 'lots of flags, mostly small calls'),
         (False, True): ('few-but-costly', 'Few but costly', 'fewer flags, bigger yardage per call'),
         (False, False): ('let-them-play', 'Let them play', 'fewer flags, smaller calls')}


def _profiles(pen, games, crew_by_game, types=None):
    """Per-crew stats for a set of games (pen already classified)."""
    games = games.copy()
    games['crew'] = games['game_id'].map(crew_by_game)
    games = games.dropna(subset=['crew'])
    p = pen[pen['game_id'].isin(games['game_id'])].copy()
    p['crew'] = p['game_id'].map(crew_by_game)
    n_league = len(games)
    lg = {
        'games': n_league, 'perGame': len(p) / n_league,
        'yardsPerFlag': p['penalty_yards'].sum() / len(p), 'costPerFlag': p['cost_epa'].mean(),
        'preSnapShare': p['penalty_type'].isin(PRE_SNAP).mean(), 'q4Share': (p['qtr'] == 4).mean(),
        'offenseShare': (p['side'] == 'offense').mean(), 'homeShare': (p['penalty_team'] == p['home_team']).mean(),
    }
    types = types or list(p['penalty_type'].value_counts().head(TOP_TYPES).index)
    lg_type = {t: (p['penalty_type'] == t).sum() / n_league for t in types}

    # Season adjustment (multi-season windows only). League penalty levels move a lot between
    # seasons (2015-19 ~13.5 flags/game, 2021-23 ~11.4), so a crew is compared with the league
    # *in the seasons it worked*, then expressed at the window's overall league level:
    #   rates (per game):   pooled league rate x (crew count / expected count from its seasons)
    #   per-flag measures:  pooled league value + (crew value - league value in its seasons,
    #                       weighted by the crew's flags)
    seasons_in = sorted(games['season'].unique()) if 'season' in games.columns else []
    adjust = len(seasons_in) > 1
    per_flag = {
        'yardsPerFlag': lambda d: d['penalty_yards'].mean(), 'costPerFlag': lambda d: d['cost_epa'].mean(),
        'preSnapShare': lambda d: d['penalty_type'].isin(PRE_SNAP).mean(), 'q4Share': lambda d: (d['qtr'] == 4).mean(),
        'offenseShare': lambda d: (d['side'] == 'offense').mean(), 'homeShare': lambda d: (d['penalty_team'] == d['home_team']).mean(),
    }
    if adjust:
        p = p.merge(games[['game_id', 'season']], on='game_id', how='left', suffixes=('', '_g'))
        if 'season_g' in p.columns:
            p['season'] = p['season'].fillna(p['season_g'])
        sg = games.groupby('season').size()
        sp = p.groupby('season')
        s_rate = (sp.size() / sg).to_dict()
        s_flag = {m: sp.apply(f).to_dict() for m, f in per_flag.items()}
        s_type = {t: (sp.apply(lambda d, t=t: (d['penalty_type'] == t).sum()) / sg).to_dict() for t in types}

    rows = {}
    for crew, gg in games.groupby('crew'):
        n = len(gg)
        q = p[p['crew'] == crew]
        if n < 1 or not len(q):
            continue
        raw = {'perGame': len(q) / n, **{m: f(q) for m, f in per_flag.items()}}
        if adjust:
            n_by_s = gg.groupby('season').size()
            m_by_s = q.groupby('season').size()
            exp_flags = sum(n_by_s[s_] * s_rate.get(s_, lg['perGame']) for s_ in n_by_s.index)
            vals = {'perGame': lg['perGame'] * len(q) / exp_flags if exp_flags else raw['perGame']}
            for m in per_flag:
                exp_m = sum(m_by_s.get(s_, 0) * s_flag[m].get(s_, lg[m]) for s_ in m_by_s.index) / max(1, m_by_s.sum())
                vals[m] = lg[m] + (raw[m] - exp_m)
        else:
            vals = dict(raw)
        tr = {}
        for t in types:
            c = (q['penalty_type'] == t).sum()
            if adjust:
                exp_c = sum(n_by_s[s_] * s_type[t].get(s_, lg_type[t]) for s_ in n_by_s.index)
                c = n * lg_type[t] * (c / exp_c) if exp_c else c        # count at the window's league level
            shrunk = (c + SHRINK * lg_type[t]) / (n + SHRINK)
            tr[t] = {'perGame': _r(shrunk, 3), 'league': _r(lg_type[t], 3), 'diffPct': _r((shrunk / lg_type[t] - 1) * 100, 0)}
        rows[crew] = {
            'games': n, 'flags': int(len(q)), **vals, 'types': tr,
            'seasonAdjusted': adjust,
            'raw': {k: _r(v, 3 if 'Share' in k else 2) for k, v in raw.items()} if adjust else None,
        }
    return lg, types, rows


# plain-English wording (up, down), value format, and the smallest difference worth calling a trait
TRAIT_TEXT = {
    'perGame':      ('More flags: {v} per game (league {l})', 'Fewer flags: {v} per game (league {l})', '{:.1f}', ('rel', 0.05)),
    'yardsPerFlag': ('Bigger calls: {v} yards per flag (league {l})', 'Smaller calls: {v} yards per flag (league {l})', '{:.1f}', ('abs', 0.2)),
    'costPerFlag':  ('Costlier flags: {v} points each (league {l})', 'Cheaper flags: {v} points each (league {l})', '{:.2f}', ('abs', 0.03)),
    'preSnapShare': ('More pre-snap fouls: {v} of flags (league {l})', 'Fewer pre-snap fouls: {v} of flags (league {l})', '{:.0%}', ('abs', 0.03)),
    'q4Share':      ('Busier 4th quarters: {v} of flags (league {l})', 'Quieter 4th quarters: {v} of flags (league {l})', '{:.0%}', ('abs', 0.03)),
    'offenseShare': ('More flags on offenses: {v} (league {l})', 'More flags on defenses: {v} on offenses (league {l})', '{:.0%}', ('abs', 0.03)),
    'homeShare':    ('More flags on home teams: {v} (league {l})', 'More flags on road teams: {v} on home teams (league {l})', '{:.0%}', ('abs', 0.03)),
}
TYPE_MIN_PCT = 15


def _meaningful(m, v, l):
    kind, t = TRAIT_TEXT[m][3]
    return abs(v / l - 1) >= t if kind == 'rel' else abs(v - l) >= t


def build_crew_styles(data: dict, active_names) -> dict:
    print("\n🦓 Building crew styles...")
    sched = data['schedules']
    reg = sched[sched['game_type'] == 'REG']
    season = int(reg['season'].max())
    off = data['officials']
    crew_by_game = (off[off['position'] == 'Referee'].dropna(subset=['game_id'])
                    .drop_duplicates('game_id').set_index('game_id')['name'].to_dict())
    gp = data['games_played']
    if 'season_type' in gp.columns:
        gp = gp[gp['season_type'] == 'REG']
    games = gp[['game_id']].drop_duplicates().merge(reg[['game_id', 'season', 'week', 'home_team', 'away_team']], on='game_id')
    pen = data['penalties']
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    pen = pen[pen['penalty_team'].notna()].copy()
    pen['penalty_yards'] = pd.to_numeric(pen['penalty_yards'], errors='coerce').fillna(0).abs()
    pen = classify(pen)

    career_games = games[games['season'] < season]
    seasons_all = sorted(int(x) for x in games['season'].unique())

    def styles_for(gset, min_games, types_fixed=None):
        """Style per crew for one set of games: metrics vs that set's league, traits, archetype, fingerprint."""
        lg, types_, prof = _profiles(pen, gset, crew_by_game, types_fixed)
        names = [c for c in prof if c in set(active_names) and prof[c]['games'] >= min_games]
        if not names:
            return lg, types_, {}, None
        feats = pd.DataFrame({c: {**{m: prof[c][m] for m in metrics},
                                  **{f't:{t}': prof[c]['types'][t]['perGame'] for t in types_}} for c in names}).T.astype(float)
        zz = (feats - feats.mean()) / feats.std(ddof=0).replace(0, 1) if len(names) > 1 else feats * 0
        out = {}
        for c in names:
            pc = prof[c]
            cand = []
            for m in metrics:
                if not _meaningful(m, pc[m], lg[m]):
                    continue
                up, down, fmt, _ = TRAIT_TEXT[m]
                cand.append((abs(zz.loc[c, m]), (up if pc[m] > lg[m] else down).format(v=fmt.format(pc[m]), l=fmt.format(lg[m])), m, zz.loc[c, m]))
            for t in types_:
                d = pc['types'][t]['diffPct']
                if abs(d) < TYPE_MIN_PCT:
                    continue
                cand.append((abs(zz.loc[c, f't:{t}']), f"{'Calls more' if d > 0 else 'Calls fewer'} {t.lower()}: {abs(d):.0f}% {'above' if d > 0 else 'below'} the league rate",
                             f't:{t}', zz.loc[c, f't:{t}']))
            traits = [{'text': txt, 'key': k, 'z': _r(z_, 2), 'direction': 'up' if z_ > 0 else 'down'}
                      for a, txt, k, z_ in sorted(cand, key=lambda x: -x[0]) if a >= 1.0][:4]
            key, title, desc = QUADS[(pc['perGame'] > lg['perGame'], pc['yardsPerFlag'] > lg['yardsPerFlag'])]
            out[c] = {
                'games': pc['games'], **{m: _r(pc[m], 3 if 'Share' in m else 2) for m in metrics},
                # position vs that season's league (lets seasons be compared on one chart)
                'vsLeague': {'perGamePct': _r((pc['perGame'] / lg['perGame'] - 1) * 100, 1),
                             'yardsPerFlagDiff': _r(pc['yardsPerFlag'] - lg['yardsPerFlag'], 2)},
                'types': pc['types'], 'traits': traits,
                'archetype': {'key': key, 'title': title, 'description': desc},
                'seasonAdjusted': bool(pc.get('seasonAdjusted')), 'raw': pc.get('raw'),
            }
        return lg, types_, out, zz

    metrics = list(TRAIT_TEXT)
    lg, types, career, z = styles_for(career_games, MIN_GAMES)
    by_season = {}
    league_by_season = {}
    for s_ in seasons_all:
        lg_s, _, st, _ = styles_for(games[games['season'] == s_], 1, types)   # same type list every season
        league_by_season[s_] = {m: _r(lg_s[m], 3 if 'Share' in m else 2) for m in metrics} | {'games': int(lg_s['games'])}
        for c, v in st.items():
            by_season.setdefault(c, {})[str(s_)] = v

    active = list(career)
    crews = []
    for c in active:
        dist = ((z.loc[active] - z.loc[c]) ** 2).sum(axis=1) ** 0.5
        sims = [{'name': o, 'slug': _slug(o), 'distance': _r(dist[o], 2)} for o in dist.drop(c).sort_values().index[:2]]
        car = career[c]
        cur = by_season.get(c, {}).get(str(season))
        crews.append({
            'name': c, 'slug': _slug(c), 'games': car['games'],
            **{m: car[m] for m in metrics},
            'types': car['types'], 'traits': car['traits'], 'similar': sims, 'archetype': car['archetype'],
            'vsLeague': car['vsLeague'],
            'seasonAdjusted': car['seasonAdjusted'], 'raw': car['raw'],   # raw = unadjusted career values
            'seasons': by_season.get(c, {}),      # every season this crew chief worked, same fields
            'current': None if not cur else {'games': cur['games'], 'perGame': cur['perGame'],
                                             'yardsPerFlag': cur['yardsPerFlag'], 'costPerFlag': cur['costPerFlag']},
        })
    crews.sort(key=lambda x: -x['perGame'])

    # Current season, week by week, for the style map: cumulative ("through week N")
    # and single-week ("week N only") flags per game and yards per flag
    cur_games = games[games['season'] == season].copy()
    cur_games['crew'] = cur_games['game_id'].map(crew_by_game)
    cur_pen = pen[pen['game_id'].isin(cur_games['game_id'])].copy()
    cur_pen['crew'] = cur_pen['game_id'].map(crew_by_game)
    if 'week' not in cur_pen.columns:
        cur_pen = cur_pen.merge(cur_games[['game_id', 'week']], on='game_id', how='left')

    def period(gmask, pmask):
        g, p = cur_games[gmask], cur_pen[pmask]
        if not len(g) or not len(p):
            return None
        out = {'league': {'games': int(len(g)), 'perGame': _r(len(p) / len(g), 2),
                          'yardsPerFlag': _r(p['penalty_yards'].sum() / len(p), 2)}, 'crews': {}}
        for c, gg in g.dropna(subset=['crew']).groupby('crew'):
            if c not in set(active_names):
                continue
            q = p[p['crew'] == c]
            if not len(q):
                continue
            out['crews'][c] = {'games': int(len(gg)), 'perGame': _r(len(q) / len(gg), 2),
                               'yardsPerFlag': _r(q['penalty_yards'].sum() / len(q), 2)}
        return out

    weeks_played = sorted(int(w) for w in cur_games['week'].unique())
    sched_n = reg[reg['season'] == season].groupby('week').size()
    played_n = cur_games.groupby('week').size()
    weekly = {'season': season, 'weeks': weeks_played, 'through': {}, 'only': {},
              'complete': {str(w): bool(played_n.get(w, 0) >= sched_n.get(w, 0)) for w in weeks_played}}
    for w in weeks_played:
        t = period(cur_games['week'] <= w, cur_pen['week'] <= w)
        o = period(cur_games['week'] == w, cur_pen['week'] == w)
        if t:
            weekly['through'][str(w)] = t
        if o:
            weekly['only'][str(w)] = o
    span = sorted(career_games['season'].unique())
    print(f"   ✓ {len(crews)} crew styles ({span[0]}-{span[-1]}), {len(types)} penalty types in the fingerprint")
    return {
        'season': season, 'careerSeasons': [int(span[0]), int(span[-1])],
        'league': {m: _r(lg[m], 3 if 'Share' in m else 2) for m in metrics},
        'leagueCurrent': league_by_season.get(season),
        'leagueBySeason': {str(k): v for k, v in league_by_season.items()},
        'weekly': weekly,
        'types': types, 'crews': crews,
        'notes': 'Regular season. Career = seasons before the current one; per-type rates are shrunk toward the league rate. '
                 'Crews change around the chief each year, so these are crew-chief-level styles. Patterns, not motives.',
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
