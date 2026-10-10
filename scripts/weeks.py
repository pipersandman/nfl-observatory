"""Week bookkeeping shared by the pipeline modules."""


def completed_week(schedules, games_played, season):
    """Last regular-season week in which every scheduled game has been played, plus the
    games already played in later (unfinished) weeks: (week, {'week': n, 'games': k} or None)."""
    sched = schedules[(schedules['season'] == season) & (schedules['game_type'] == 'REG')]
    played = set(games_played['game_id'])
    done = 0
    for wk in sorted(sched['week'].unique()):
        if set(sched.loc[sched['week'] == wk, 'game_id']) <= played:
            done = int(wk)
        else:
            break
    extra = sched[(sched['week'] > done) & sched['game_id'].isin(played)]
    partial = {'week': int(extra['week'].min()), 'games': int(len(extra))} if len(extra) else None
    return done, partial
