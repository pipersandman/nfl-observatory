"""Week selection in fetch_assignments.py (#84), with made-up schedules and no network."""

import sys
from datetime import date, datetime, timedelta

import pandas as pd
import pytest

import fetch_assignments as fa
from seasons import schedule_seasons, season_start


def make_schedule(season: int, today: date) -> pd.DataFrame:
    """18 regular-season weeks of 2 Sunday games, then 2 playoff Saturdays.
    Games before `today` have a result; the rest are unplayed."""
    rows = []
    first_sunday = season_start(season) + timedelta(days=3)
    for week in range(1, 19):
        day = first_sunday + timedelta(weeks=week - 1)
        rows += [{'season': season, 'week': week, 'game_type': 'REG', 'gameday': day.isoformat()}] * 2
    for i, week in enumerate((19, 20)):
        day = first_sunday + timedelta(weeks=17, days=6 + 7 * i)
        rows.append({'season': season, 'week': week, 'game_type': 'WC' if i == 0 else 'DIV',
                     'gameday': day.isoformat()})
    df = pd.DataFrame(rows)
    df['result'] = [3.0 if g < today.isoformat() else float('nan') for g in df['gameday']]
    return df


def schedules(today: date, seasons) -> pd.DataFrame:
    return pd.concat([make_schedule(s, today) for s in seasons], ignore_index=True)


def test_made_up_schedule_shape():
    s = make_schedule(2026, date(2026, 1, 1))
    assert s[s['week'] == 18]['gameday'].iloc[0] == '2027-01-10'
    assert s[s['game_type'] != 'REG']['gameday'].min() == '2027-01-16'


def test_january_week_18_still_to_come():
    today = date(2027, 1, 5)
    sched = schedules(today, [2026])   # 2027 schedule not out yet
    assert fa.select_weeks(sched, schedule_seasons(today), today) == (2026, [18])


def test_mid_january_after_week_18_playoffs_ignored():
    today = date(2027, 1, 14)
    sched = schedules(today, [2026])
    assert fa.select_weeks(sched, schedule_seasons(today), today) == (None, [])


def test_mid_january_with_next_schedule_out():
    today = date(2027, 1, 14)
    sched = schedules(today, [2026, 2027])
    assert fa.select_weeks(sched, schedule_seasons(today), today) == (2027, [1])


def test_august_with_next_schedule():
    today = date(2027, 8, 20)
    sched = schedules(today, [2026, 2027])
    assert fa.select_weeks(sched, schedule_seasons(today), today) == (2027, [1])


def test_august_without_next_schedule():
    today = date(2027, 8, 20)
    sched = schedules(today, [2026])
    assert fa.select_weeks(sched, schedule_seasons(today), today) == (None, [])


def run_main(monkeypatch, capsys, today: date, seasons):
    """fetch_assignments.main() on a faked date with a made-up schedule."""
    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(today.year, today.month, today.day, 12, 0, tzinfo=tz)

    def no_feed(*a, **k):
        raise AssertionError('Football Zebras should not be fetched')

    monkeypatch.setattr(fa, 'datetime', FakeDT)
    monkeypatch.setattr(fa, 'schedule_seasons', lambda: schedule_seasons(today))
    monkeypatch.setattr(fa, 'load_schedule', lambda s: schedules(today, seasons))
    monkeypatch.setattr(fa, 'http_get', no_feed)
    monkeypatch.setattr(sys, 'argv', ['fetch_assignments.py'])
    code = fa.main()
    return code, capsys.readouterr().out


@pytest.mark.parametrize('today, seasons', [
    (date(2027, 1, 14), [2026]),   # after Week 18, playoffs to come
    (date(2027, 8, 20), [2026]),   # August, next season's schedule not out
])
def test_main_nothing_to_do(monkeypatch, capsys, today, seasons):
    code, out = run_main(monkeypatch, capsys, today, seasons)
    assert code == 0
    assert 'Nothing to do' in out
