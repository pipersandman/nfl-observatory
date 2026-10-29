"""Shared windows and their labels (#116).

One place defines the windows every number uses, and builds their labels from the
data, so no script or page hard-codes a year, window or value:

- regular season:        regular_season()
- last completed week:   completed_week() (plus the partial week, if one is in progress)
- prior seasons:         prior_seasons() (every season in the data before the current one)
- last N seasons:        last_n()
- career:                career_window() (= the prior seasons; seasons before this one)
- labels:                span_label() "2015–25", weeks_label() "Weeks 1–7",
                         through_label() "2025 through Week 7", short_through() "2025 Wk 1–7",
                         button_through() "2025 thru Wk 7"
- the block the pages read: windows_block() → season_comparison.json → windows
"""

HISTORICAL_START = 2015   # first season nflverse publishes all seven officials per game

# The fade comparison (flags early in a season vs late): the first and last weeks
# compared. LATE_WEEKS runs to the last regular-season week.
EARLY_WEEKS = (1, 4)
LATE_WEEKS_FROM = 15


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


# ---- windows ---------------------------------------------------------------------

def regular_season(df, column='season_type'):
    """Regular-season rows only. Play and game tables use season_type; schedules use
    game_type. A table without the column is returned as it is."""
    return df[df[column] == 'REG'] if column in df else df


def prior_seasons(seasons, season):
    """Every season in `seasons` before `season`, oldest first."""
    return sorted(int(s) for s in seasons if int(s) < int(season))


def last_n(prior, n=3):
    """The last n of the prior seasons (fewer if the data has fewer)."""
    return list(prior)[-n:]


def career_window(seasons, season):
    """Career = every season before the current one: (first, last), or None."""
    prior = prior_seasons(seasons, season)
    return (prior[0], prior[-1]) if prior else None


# ---- labels ----------------------------------------------------------------------

def span_label(seasons):
    """'2015–25' for a range, '2025' for one season."""
    s = sorted(int(x) for x in seasons)
    if not s:
        return ''
    return f"{s[0]}" if s[0] == s[-1] else f"{s[0]}–{str(s[-1])[2:]}"


def weeks_label(last, first=1):
    """'Weeks 1–7', or 'Week 1' when the window is one week."""
    return f"Week {first}" if first == last else f"Weeks {first}–{last}"


def through_label(season, week):
    """'2025 through Week 7'."""
    return f"{season} through Week {week}"


def short_through(season, week, first=1):
    """'2025 Wk 1–7'."""
    return f"{season} Wk {first}–{week}"


def button_through(season, week):
    """'2025 thru Wk 7'."""
    return f"{season} thru Wk {week}"


def baseline_button(key, seasons, week=None):
    """The comparison toggle's button text: '2025 thru Wk 7', 'All of 2025',
    'Last 3 seasons', 'All seasons'."""
    if key == 'sameWeeks':
        return button_through(seasons[0], week)
    if key == 'lastSeason':
        return f"All of {seasons[0]}"
    if key == 'last3':
        return f"Last {len(seasons)} seasons"
    return "All seasons"


def since_label(first):
    """'Since 2015'."""
    return f"Since {first}"


def fade_windows(last_week):
    """The fade comparison's two windows, with labels, for the text and its filter."""
    early, late = EARLY_WEEKS, (LATE_WEEKS_FROM, int(last_week))
    return {'early': {'from': early[0], 'to': early[1], 'label': weeks_label(early[1], early[0])},
            'late': {'from': late[0], 'to': late[1], 'label': weeks_label(late[1], late[0])}}


def windows_block(seasons, season, through_week, partial):
    """Every window the pages name, with its label. Written to
    season_comparison.json → windows; app.js and build_static.py read it."""
    prior = prior_seasons(seasons, season)
    previous = int(season) - 1
    car = career_window(seasons, season)
    l3 = last_n(prior)
    return {
        'season': int(season),
        'previous': previous,
        'dataStart': int(min(seasons)) if len(seasons) else HISTORICAL_START,
        'throughWeek': int(through_week),
        'partialWeek': partial,
        'weeksLabel': weeks_label(through_week) if through_week else '',
        'sameWeeks': {'label': through_label(previous, through_week), 'short': short_through(previous, through_week),
                      'button': button_through(previous, through_week)} if through_week else None,
        'prior': {'seasons': [prior[0], prior[-1]], 'label': span_label(prior)} if prior else None,
        'last3': {'seasons': [l3[0], l3[-1]], 'count': len(l3), 'label': span_label(l3)} if l3 else None,
        'career': {'seasons': list(car), 'label': span_label(car)} if car else None,
    }
