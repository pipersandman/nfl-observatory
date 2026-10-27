"""One season rule for the whole pipeline (#84).

Standard library only, so the workflow gate can import it before dependencies
are installed.

- nflverse_current_season(): the season nflverse treats as current. Same rule as
  nflreadpy.get_current_season(): the calendar year from the Thursday after
  Labor Day, otherwise the previous year. update_data.py keeps calling nflreadpy
  directly; this copy is for code that runs without it.
- schedule_seasons(): the current season, plus the calendar year when it's later,
  so next season's schedule is in view as soon as nflverse publishes it.

Both take an optional `today` (a date); the default is the real date.
"""

from datetime import date, timedelta


def season_start(year: int) -> date:
    """The Thursday after Labor Day (the first Monday in September)."""
    sept1 = date(year, 9, 1)
    labor_day = sept1 + timedelta(days=(0 - sept1.weekday()) % 7)
    return labor_day + timedelta(days=3)


def nflverse_current_season(today: date | None = None) -> int:
    today = today or date.today()
    return today.year if today >= season_start(today.year) else today.year - 1


def schedule_seasons(today: date | None = None) -> list[int]:
    today = today or date.today()
    current = nflverse_current_season(today)
    return list(range(current, max(current, today.year) + 1))
