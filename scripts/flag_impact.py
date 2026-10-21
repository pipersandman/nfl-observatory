"""
Flag impact: what every accepted penalty cost, and what it did to the drive
==========================================================================
Regular season. For each flag, from the penalized team's point of view:

  cost (points)     expected points the flag cost the penalized team:
                    - flag erased the play (no play): the play's change in expected
                      points (EPA), charged to the penalized team. A defensive flag
                      that hands the offense +1.5 expected points costs it 1.5
                    - flag added on top of a play that counts (e.g. roughness after a
                      catch or an interception): only the penalty yards, at
                      POINTS_PER_YARD, so the play itself isn't charged to the flag
                    - two-point tries: a defensive flag that erased a failed try is
                      worth a retry (2 x the league success rate)

What it did (labels, one flag can have several):
  first down given  a flag on the defense that gave the offense a first down
  key first down    ...on 3rd or 4th down
  drive stalled     a flag on the offense in scoring range (inside the opponent's
                    40) on a drive that then didn't score. Shows association, not
                    that the flag caused it
  big play erased   a flag on the offense that wiped out a 15+ yard gain or a TD
  turnover erased   a flag on the defense that wiped out its own interception or
                    fumble recovery

Notes: EPA/WPA come from nflverse's models and describe the flagged play as a
whole; they're estimates, not exact accounting.
"""
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from weeks import completed_week

GAIN_RE = re.compile(r'for (-?\d+) yards?')
POINTS_PER_YARD = 0.0615      # expected points per yard, 1st & 10 between the 20s, 2020-25 (measured)
TWO_POINT_RATE = 0.468        # two-point conversion success rate, 2020-25 regular season (measured)
SPECIAL = {'kickoff', 'punt', 'field_goal', 'extra_point'}
SCORELESS = {'Punt', 'Turnover', 'Turnover on downs', 'Missed field goal', 'End of half', 'Opp touchdown', 'Safety'}


def _r(x, d=2):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)


def _erased(desc):
    """Text of the play before the penalty: (gain erased, touchdown erased, turnover erased)."""
    pre = str(desc).split('PENALTY')[0]
    m = GAIN_RE.findall(pre)
    gain = int(m[-1]) if m else (0 if 'no gain' in pre else None)
    td = 'TOUCHDOWN' in pre
    to = ('INTERCEPTED' in pre) or ('RECOVERED by' in pre and 'FUMBLES' in pre)
    return gain, td, to


def _tbucket(sec):
    """Clock bucket: 1-minute buckets in the last 10 minutes, 5-minute buckets before that."""
    sec = float(sec)
    return int(sec // 60) if sec < 600 else 10 + int((sec - 600) // 300)


def _dbucket(diff):
    d = abs(float(diff))
    return 0 if d <= 3 else 1 if d <= 8 else 2 if d <= 16 else 3


def build_wp_tables(pbp):
    """From every regular-season play: (1) the kicking team's win chance at a kickoff by its lead
    and the clock (used when a flag wipes out a touchdown: 'what if it had stood?'), and (2) how
    much one expected point is worth in win chances by score margin and clock (used for flags
    added on top of a play that counts)."""
    r = pbp[(pbp.get('season_type', 'REG') == 'REG') & pbp['wp'].notna() & pbp['game_seconds_remaining'].notna()]
    k = r[(r['play_type'] == 'kickoff') & r['score_differential'].notna()].copy()
    k['lead'] = (-k['score_differential']).clip(-28, 28).astype(int)          # kicking team's lead
    k['tb'] = k['game_seconds_remaining'].map(_tbucket)
    kick = {f'{a}|{b}': [round(float(1 - g['wp'].mean()), 4), int(len(g))] for (a, b), g in k.groupby(['lead', 'tb'])}
    sp = r[r['play_type'].isin(['pass', 'run']) & r['epa'].notna() & r['wpa'].notna() & (r['epa'].abs() >= 0.3)].copy()
    sp['tb'] = sp['game_seconds_remaining'].map(_tbucket)
    sp['db'] = sp['score_differential'].fillna(0).map(_dbucket)
    sp['lev'] = sp['wpa'].abs() / sp['epa'].abs()
    lev = {f'{a}|{b}': [round(float(g['lev'].median()), 4), int(len(g))] for (a, b), g in sp.groupby(['tb', 'db'])}
    print(f"   ✓ Win-probability tables: {len(kick)} kickoff cells, {len(lev)} leverage cells")
    return {'kick': kick, 'lev': lev}


def _kick_wp(tables, lead, sec, min_n=8):
    """Kicking team's win chance with this lead at this time; widens the search if the cell is thin."""
    lead = int(max(-28, min(28, round(lead))))
    tb = _tbucket(sec)
    for dl, dt in ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (0, 2), (0, -2)):
        v = tables['kick'].get(f'{lead + dl}|{tb + dt}')
        if v and v[1] >= min_n:
            return v[0]
    return None


def _leverage(tables, sec, diff):
    v = tables['lev'].get(f'{_tbucket(sec)}|{_dbucket(diff)}')
    return v[0] if v else None


def classify(pen, wp_tables=None):
    p = pen.copy()
    on_off = p['penalty_team'] == p['posteam']
    p['side'] = np.where(on_off, 'offense', 'defense')
    # nflverse doesn't always mark penalty plays on two-point tries; the play text does
    two = (p['two_point_attempt'].fillna(0).astype(bool) |
           p['desc'].str.contains('TWO-POINT CONVERSION ATTEMPT', na=False))
    no_play = p['play_type'] == 'no_play'
    erased_fail_2pt = two & ~on_off & p['desc'].str.contains('ATTEMPT FAILS', na=False)
    epa_cost = np.where(on_off, -p['epa'], p['epa'])                  # positive = hurt the penalized team
    yards_cost = p['penalty_yards'] * POINTS_PER_YARD
    p['cost_epa'] = np.where(erased_fail_2pt, 2 * TWO_POINT_RATE,
                    np.where(two, yards_cost,
                    np.where(no_play, epa_cost, yards_cost)))
    p['cost_method'] = np.where(erased_fail_2pt, 'two-point retry',
                       np.where(two | ~no_play, 'penalty yards', 'play value'))
    er = p['desc'].map(_erased)
    p['gain_erased'] = [g if (np_ and off) else None for (g, _, _), np_, off in zip(er, no_play, on_off)]
    # A touchdown wiped out by the offense's own flag. nflverse marks most as 'no play', but a
    # foul enforced at the spot (e.g. holding on a long run) leaves the play standing without
    # the score; the play text says 'TOUCHDOWN NULLIFIED' in every case, so use both
    nullified = p['desc'].str.contains('TOUCHDOWN NULLIFIED', case=False, na=False)
    p['td_erased'] = [bool(off and ((td and np_) or nul)) for (_, td, _), np_, off, nul in zip(er, no_play, on_off, nullified)]
    # Touchdowns wiped out (whether recorded as 'no play' or enforced at the spot): charge the
    # touchdown's value minus what the offense actually got
    if 'ep' in p.columns:
        td_cost = (7 - pd.to_numeric(p['ep'], errors='coerce')) - pd.to_numeric(p['epa'], errors='coerce')
        m = p['td_erased'] & td_cost.notna()
        p.loc[m, 'cost_epa'] = td_cost[m].clip(lower=0)
        p.loc[m, 'cost_method'] = 'touchdown value'

    # Win chances the flag cost the penalized team (0-1; nflverse win-probability model)
    p['cost_wp'] = np.nan
    p['wp_method'] = None
    if 'wpa' in p.columns:
        wpa = pd.to_numeric(p['wpa'], errors='coerce')
        wp_cost = np.where(on_off, -wpa, wpa)
        plain_np = no_play & ~two & ~p['td_erased']
        p.loc[plain_np, 'cost_wp'] = wp_cost[plain_np]
        p.loc[plain_np, 'wp_method'] = 'play value'
        if wp_tables and 'wp' in p.columns:
            for i in p.index[p['td_erased']]:
                r = p.loc[i]
                if pd.isna(r['wp']) or pd.isna(r['wpa']) or pd.isna(r.get('score_differential')) or pd.isna(r.get('game_seconds_remaining')):
                    continue
                stood = _kick_wp(wp_tables, r['score_differential'] + 7, r['game_seconds_remaining'])
                if stood is not None:
                    p.at[i, 'cost_wp'] = max(0.0, stood - (r['wp'] + r['wpa']))
                    p.at[i, 'wp_method'] = 'touchdown value'
            rest = p['cost_wp'].isna() & p['game_seconds_remaining'].notna()
            for i in p.index[rest]:
                r = p.loc[i]
                lv = _leverage(wp_tables, r['game_seconds_remaining'], r.get('score_differential', 0) or 0)
                if lv is not None and pd.notna(r['cost_epa']):
                    p.at[i, 'cost_wp'] = lv * r['cost_epa']
                    p.at[i, 'wp_method'] = 'points at this score and clock'
    p['to_erased'] = [bool(to and np_ and not off) for (_, _, to), np_, off in zip(er, no_play, on_off)]
    p['first_down_given'] = (~on_off) & (p['first_down_penalty'] == 1)
    p['key_first_down'] = p['first_down_given'] & p['down'].isin([3, 4])
    p['big_play_erased'] = p['td_erased'] | (pd.to_numeric(p['gain_erased'], errors='coerce') >= 15)
    scrimmage = ~p['play_type'].isin(SPECIAL) & ~two
    p['drive_killed'] = on_off & scrimmage & (p['yardline_100'] <= 40) & p['fixed_drive_result'].isin(SCORELESS)
    p['two_point_retry'] = erased_fail_2pt
    return p


def _team_block(fl, games_by_team, offsetting_tds=None):
    out = []
    offsetting_tds = offsetting_tds or {}
    for team, d in fl.groupby('penalty_team'):
        n = int(games_by_team.get(team, 0))
        if not n:
            continue
        out.append({
            'team': team, 'games': n, 'flags': int(len(d)),
            'pointsCost': _r(d['cost_epa'].sum(), 1), 'pointsCostPerGame': _r(d['cost_epa'].sum() / n, 2),
            'firstDownsGiven': int(d['first_down_given'].sum()), 'keyFirstDownsGiven': int(d['key_first_down'].sum()),
            'drivesKilled': int(d['drive_killed'].sum()), 'bigPlaysErased': int(d['big_play_erased'].sum()),
            'turnoversErased': int(d['to_erased'].sum()),
            'tdsErased': int(d['td_erased'].sum()),
            'winsGivenAway': _r(d['cost_wp'].fillna(0).sum(), 2),
            'tdsLostOffsetting': int(offsetting_tds.get(team, 0)),
        })
    out.sort(key=lambda r: r['pointsCostPerGame'] or 0, reverse=True)       # most costly first
    for i, r in enumerate(out, 1):
        r['rank'] = i
    return out


def _flag_row(r, games):
    g = games.get(r['game_id'], {})
    labels = [lab for lab, on in (('Key first down given', r['key_first_down']),
                                  ('First down given', r['first_down_given'] and not r['key_first_down']),
                                  ('Drive stalled after', r['drive_killed']),
                                  ('Touchdown erased', r['td_erased']),
                                  ('Big play erased', r['big_play_erased'] and not r['td_erased']),
                                  ('Turnover erased', r['to_erased']),
                                  ('Failed two-point try erased', r['two_point_retry'])) if on]
    return {
        'gameId': r['game_id'], 'week': int(r['week']), 'away': g.get('away'), 'home': g.get('home'),
        'team': r['penalty_team'], 'side': r['side'], 'type': r['penalty_type'], 'player': r['penalty_player_name'],
        'qtr': int(r['qtr']), 'time': r['time'], 'yards': int(r['penalty_yards']),
        'pointsCost': _r(r['cost_epa'], 2), 'method': r['cost_method'],
        'winProbCost': None if pd.isna(r.get('cost_wp')) else _r(r['cost_wp'] * 100, 1), 'winProbMethod': r.get('wp_method'),
        'gainErased': None if pd.isna(r['gain_erased']) else int(r['gain_erased']),
        'twoPoint': bool(r['two_point_retry']) or 'TWO-POINT' in str(r['desc']), 'labels': labels,
    }


def build_flag_impact(data: dict) -> dict:
    print("\n💸 Building flag impact...")
    sched = data['schedules']
    reg = sched[sched['game_type'] == 'REG']
    season = int(reg['season'].max())
    pen = data['penalties']
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    # Touchdowns wiped out by offsetting penalties: no accepted flag on either team, but the
    # scoring team lost the touchdown (on kicks, nflverse's posteam is the returning team)
    offs = data.get('offsetting_tds')
    if offs is None or not len(offs):
        offs = pd.DataFrame(columns=['season', 'posteam'])
    elif 'season_type' in offs.columns:
        offs = offs[offs['season_type'] == 'REG']
    offsetting_by_season = {s_: d['posteam'].value_counts().to_dict() for s_, d in offs.groupby('season')}
    pen = pen[pen['penalty_team'].notna() & pen['season'].isin([season - 1, season])].copy()
    pen['penalty_yards'] = pd.to_numeric(pen['penalty_yards'], errors='coerce').fillna(0).abs()
    fl = classify(pen, data.get('wp_tables'))

    gp = data['games_played']
    if 'season_type' in gp.columns:
        gp = gp[gp['season_type'] == 'REG']
    g = gp[['game_id']].drop_duplicates().merge(reg[['game_id', 'season', 'week', 'home_team', 'away_team']], on='game_id')
    games = {r.game_id: {'away': r.away_team, 'home': r.home_team} for r in g.itertuples()}
    done, _ = completed_week(sched, data['games_played'], season)

    scopes = {}
    for key, s_ in (('current', season), ('lastSeason', season - 1)):
        gs = g[g['season'] == s_]
        gbt = pd.concat([gs['home_team'], gs['away_team']]).value_counts()
        f = fl[fl['season'] == s_]
        top = f.sort_values('cost_epa', ascending=False).head(10)
        scopes[key] = {
            'season': s_, 'games': int(len(gs)), 'flags': int(len(f)),
            'league': {'pointsCostPerTeamGame': _r(f['cost_epa'].sum() / max(1, 2 * len(gs)), 2),
                       'keyFirstDownsGiven': int(f['key_first_down'].sum()), 'drivesKilled': int(f['drive_killed'].sum()),
                       'bigPlaysErased': int(f['big_play_erased'].sum()), 'turnoversErased': int(f['to_erased'].sum()),
                       'tdsErased': int(f['td_erased'].sum()),
                       'tdsLostOffsetting': int(sum(offsetting_by_season.get(s_, {}).values()))},
            'teams': _team_block(f, gbt, offsetting_by_season.get(s_)),
            'costliest': [_flag_row(r, games) for _, r in top.iterrows()],
            'costliestWinProb': [_flag_row(r, games) for _, r in f.sort_values('cost_wp', ascending=False, na_position='last').head(10).iterrows()],
        }
    week_flags = fl[(fl['season'] == season) & (fl['week'] == done)] if done else fl.iloc[0:0]
    team_flags = {t: [_flag_row(r, games) for _, r in d.sort_values('cost_epa', ascending=False).head(5).iterrows()]
                  for t, d in fl[fl['season'] == season].groupby('penalty_team')}
    print(f"   ✓ {len(fl)} flags valued · costliest of Week {done}: "
          + (f"{week_flags.sort_values('cost_epa', ascending=False).iloc[0]['penalty_type']}" if len(week_flags) else '—'))
    return {
        'season': season, 'throughWeek': done,
        'scopes': scopes,
        'week': {'week': done, 'costliest': [_flag_row(r, games) for _, r in week_flags.sort_values('cost_epa', ascending=False).head(10).iterrows()],
                 'costliestWinProb': [_flag_row(r, games) for _, r in week_flags.sort_values('cost_wp', ascending=False, na_position='last').head(10).iterrows()]},
        'teamCostliest': team_flags,
        'definitions': {
            'pointsCost': 'Expected points the flag cost the penalized team (nflverse EPA model)',
            'winProbCost': 'Win chances (percentage points) the flag cost the penalized team: the change in nflverse win probability when the flag erases the play; for a wiped-out touchdown, the chance had it stood (similar kickoffs since 2015, assuming the extra point) minus the chance after the play; otherwise the points cost times what a point is worth at that score and clock (measured since 2015)',
            'winsGivenAway': 'Sum of win chances lost to flags, in wins',
            'method': 'play value = the erased play\'s change in expected points; penalty yards = flag added on top of a play that counts, valued at ~0.06 points per yard; two-point retry = 2 x the 46.8% conversion rate',
            'keyFirstDownsGiven': 'Defensive flags that gave the offense a first down on 3rd or 4th down',
            'drivesKilled': 'Drives stalled: offensive flags inside the opponent 40 on drives that then did not score (the flag may or may not be why)',
            'bigPlaysErased': 'Offensive flags that wiped out a 15+ yard gain or a touchdown',
            'tdsErased': "Touchdowns wiped out by the scoring team's own flag (including fouls enforced at the spot)",
            'tdsLostOffsetting': 'Touchdowns wiped out by offsetting penalties (no team charged with a flag)',
            'turnoversErased': 'Defensive flags that wiped out their own interception or fumble recovery',
        },
        'notes': 'Regular season, accepted penalties. Points and win chances are estimates from nflverse\'s expected-points and win-probability models and league rates since 2015.',
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
