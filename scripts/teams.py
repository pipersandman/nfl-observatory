"""Team abbreviations shared by the pipeline modules (#105).

nflverse play-by-play uses today's abbreviations for every season (LA, LAC, LV even
in 2015), while schedules use the ones of the time (STL, SD, OAK). Mapping the
schedule to today's abbreviations makes the two sources agree, so a team's games and
its flags line up in every season. Game ids keep their original form: they're ids,
not team labels.
"""

# Old abbreviation -> today's, for teams that moved since 2015 (the first season in the data)
RELOCATED = {'STL': 'LA', 'SD': 'LAC', 'OAK': 'LV'}


def normalize_teams(df, cols=('home_team', 'away_team')):
    """Return df with the team columns mapped to today's abbreviations."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = df[c].replace(RELOCATED)
    return df
