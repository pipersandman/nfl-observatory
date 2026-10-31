"""The one season rule (scripts/seasons.py, #84)."""

from datetime import date, timedelta

import nflreadpy
import nflreadpy.utils_date as ud
import pytest

from seasons import nflverse_current_season, schedule_seasons


def test_matches_nflreadpy_every_day_2015_to_2035(monkeypatch):
    """Same answer as nflreadpy.get_current_season() on every day, with nflreadpy's
    date patched (it reads date.today() inside nflreadpy.utils_date)."""
    day = {'today': None}

    class FakeDate(date):
        @classmethod
        def today(cls):
            return day['today']

    monkeypatch.setattr(ud, 'date', FakeDate)
    d, end, mismatches, n = date(2015, 1, 1), date(2035, 12, 31), [], 0
    while d <= end:
        day['today'] = d
        if nflverse_current_season(d) != nflreadpy.get_current_season():
            mismatches.append(d.isoformat())
        d += timedelta(days=1)
        n += 1
    assert n == 7670
    assert mismatches == []


@pytest.mark.parametrize('today, expected', [
    (date(2027, 1, 10), [2026, 2027]),   # January: season in progress + calendar year
    (date(2027, 8, 20), [2026, 2027]),   # August: next season's schedule in view
    (date(2027, 9, 8), [2026, 2027]),    # day before the turnover (Wednesday)
    (date(2027, 9, 9), [2027]),          # Thursday after Labor Day: 2027 is current
])
def test_schedule_seasons_key_dates(today, expected):
    assert schedule_seasons(today) == expected


def test_turnover_is_thursday_after_labor_day():
    assert nflverse_current_season(date(2027, 9, 8)) == 2026
    assert nflverse_current_season(date(2027, 9, 9)) == 2027
