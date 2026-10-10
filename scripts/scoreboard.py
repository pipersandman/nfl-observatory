"""
Scoreboard: league-wide running totals by timeframe, plus a week-by-week log.
Regular season only. Accepted penalties.
"""
from datetime import datetime, timezone

import pandas as pd

from weeks import completed_week

PRE_SNAP = {
    'False Start', 'Delay of Game', 'Defensive Offside', 'Neutral Zone Infraction', 'Encroachment',
    'Illegal Formation', 'Illegal Shift', 'Illegal Motion', 'Offensive Offside', 'Defensive Delay of Game',
    'Illegal Substitution', 'Too Many Men on Field', 'Offside on Free Kick',
}


def _r(x, d=1):
    return None if x is None or pd.isna(x) else round(float(x), d)


def build_scoreboard(data: dict) -> dict:
    print("\n🏟️  Building scoreboard...")
    sched = data['schedules']
    reg = sched[sched['game_type'] == 'REG']
    season = int(reg['season'].max())

    gp = data['games_played']
    if 'season_type' in gp.columns:
        gp = gp[gp['season_type'] == 'REG']
    games = gp[['game_id']].drop_duplicates().merge(
        reg[['game_id', 'season', 'week', 'home_team', 'away_team', 'referee']], on='game_id')
    games = games.merge(data['plays'], on='game_id', how='left').fillna({'plays': 0})

    pen = data['penalties']
    if 'season_type' in pen.columns:
        pen = pen[pen['season_type'] == 'REG']
    pen = pen[pen['penalty_team'].notna() & pen['game_id'].isin(games['game_id'])].copy()
    pen['penalty_yards'] = pd.to_numeric(pen['penalty_yards'], errors='coerce').fillna(0).abs()
    pen = pen.merge(games[['game_id', 'season', 'week']].rename(columns={'season': 's', 'week': 'w'}), on='game_id')

    done_week, partial = completed_week(sched, gp, season)
    seasons = sorted(int(x) for x in games['season'].unique())
    prior = [x for x in seasons if x < season]
    last3 = prior[-3:]

    frames = []
    if done_week:
        frames.append(('latestWeek', f'Week {done_week}', f'{season} Week {done_week}',
                       lambda g: (g['season'] == season) & (g['week'] == done_week)))
    frames += [
        ('season', f'{season} season', f'{season} regular season so far', lambda g: g['season'] == season),
        ('lastSeason', f'{season - 1}', f'{season - 1} regular season', lambda g: g['season'] == season - 1),
    ]
    if len(last3) == 3:
        frames.append(('last3', f'{last3[0]}–{str(last3[-1])[2:]}', f'{last3[0]}–{last3[-1]} regular seasons',
                       lambda g, s3=tuple(last3): g['season'].isin(s3)))
    frames.append(('all', f'Since {seasons[0]}', f'Every regular-season game since {seasons[0]}', lambda g: g['season'] >= seasons[0]))

    def stats(gm):
        ids = set(gm['game_id'])
        p = pen[pen['game_id'].isin(ids)]
        n, plays, flags = len(gm), int(gm['plays'].sum()), len(p)
        if not n:
            return None
        yards = int(p['penalty_yards'].sum())
        fd = int((pd.to_numeric(p.get('first_down_penalty'), errors='coerce') == 1).sum()) if 'first_down_penalty' in p else None
        vc = p['penalty_type'].value_counts()
        team_rows = pd.concat([gm[['game_id', 'home_team']].rename(columns={'home_team': 'team'}),
                               gm[['game_id', 'away_team']].rename(columns={'away_team': 'team'})])
        tgames = team_rows.groupby('team').size()
        tflags = p.groupby('penalty_team').size().reindex(tgames.index, fill_value=0)
        tpg = (tflags / tgames).sort_values(ascending=False)
        crews = gm.dropna(subset=['referee']).groupby('referee')['game_id'].apply(set)
        crew_pg = {c: len(p[p['game_id'].isin(g)]) / len(g) for c, g in crews.items() if len(g) >= (1 if n <= 16 else 3)}
        top_crew = max(crew_pg.items(), key=lambda x: x[1]) if crew_pg else None
        return {
            'games': n, 'plays': plays, 'penalties': flags, 'yards': yards,
            'pctPlays': _r(flags / plays * 100, 1) if plays else None,
            'flagEveryPlays': _r(plays / flags, 1) if flags else None,
            'perGame': _r(flags / n, 1), 'yardsPerGame': _r(yards / n, 1),
            'yardsPerPenalty': _r(yards / flags, 1) if flags else None,
            'firstDowns': fd, 'firstDownsPerGame': _r(fd / n, 1) if fd is not None else None,
            'offenseShare': _r((p['penalty_team'] == p['posteam']).mean() * 100, 0) if flags else None,
            'preSnapShare': _r(p['penalty_type'].isin(PRE_SNAP).mean() * 100, 0) if flags else None,
            'homeShare': _r((p['penalty_team'] == p['home_team']).mean() * 100, 0) if flags else None,
            'minutesPerFlag': _r(60 / (flags / n), 1) if flags else None,
            'mostCommon': {'type': vc.index[0], 'count': int(vc.iloc[0]), 'pct': _r(vc.iloc[0] / flags * 100, 0)} if flags else None,
            'mostFlaggedTeam': {'team': tpg.index[0], 'perGame': _r(tpg.iloc[0], 1)} if len(tpg) else None,
            'cleanestTeam': {'team': tpg.index[-1], 'perGame': _r(tpg.iloc[-1], 1)} if len(tpg) else None,
            'topCrew': {'name': top_crew[0], 'perGame': _r(top_crew[1], 1)} if top_crew else None,
        }

    out_frames = []
    for key, label, desc, mask in frames:
        st = stats(games[mask(games)])
        if st:
            out_frames.append({'key': key, 'label': label, 'description': desc, **st})

    # Every week of this season as its own frame (the Week picker), incl. a week in progress
    week_frames = []
    for wk in sorted(games.loc[games['season'] == season, 'week'].unique()):
        st = stats(games[(games['season'] == season) & (games['week'] == wk)])
        sched_n = int(((reg['season'] == season) & (reg['week'] == wk)).sum())
        if st:
            complete = st['games'] >= sched_n
            week_frames.append({'key': f'week-{int(wk)}', 'week': int(wk), 'complete': complete, 'scheduled': sched_n,
                                'label': f'Week {int(wk)}',
                                'description': f'{season} Week {int(wk)}' + ('' if complete else f" (in progress: {st['games']} of {sched_n} games)"),
                                **st})

    log = []
    cur = games[games['season'] == season]
    for wk in sorted(cur['week'].unique()):
        st = stats(cur[cur['week'] == wk])
        sched_n = int(((reg['season'] == season) & (reg['week'] == wk)).sum())
        log.append({'week': int(wk), 'complete': st['games'] >= sched_n, 'scheduled': sched_n,
                    **{k: st[k] for k in ('games', 'plays', 'penalties', 'yards', 'pctPlays', 'perGame', 'yardsPerGame', 'firstDowns')}})

    print(f"   ✓ {len(out_frames)} timeframes, {len(log)} weeks logged")
    return {
        'season': season, 'throughWeek': done_week, 'partialWeek': partial,
        'defaultFrame': 'season', 'frames': out_frames, 'weeklyLog': log,
        'weekFrames': week_frames, 'defaultWeek': done_week or (week_frames[-1]['week'] if week_frames else None),
        'notes': 'Regular season. Accepted penalties. Plays = snaps plus pre-snap penalty plays.',
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
