"""Gameday archive (#193): the week-complete rule, the schedule match, the per-flag
line, what the published file may hold, and the write-once R2 copy."""

import json

import gameday_archive as ga
import pandas as pd
import pytest
import raw_capture

SEASON = 2026


def flag(team='CHI', type_='Defensive Holding', player='T.Edwards', yards=10, status='accepted',
         qtr=3, clock='4:12'):
    return {'id': '1-0', 'seq': 1, 'qtr': qtr, 'clock': clock, 'wall': '2026-11-22T19:01:02Z',
            'team': team, 'player': player, 'type': type_, 'yards': yards, 'status': status,
            'noPlay': False, 'wpCost': 0.031, 'wpMethod': 'play value', 'tdErased': False}


def game(gid, away, home, start, state='post', detail='Final', log=None):
    return {'id': gid, 'name': f'{away} @ {home}', 'start': start, 'state': state, 'detail': detail,
            'period': 4, 'clock': '0:00', 'network': 'CBS',
            'home': {'abbr': home, 'score': 24, 'flags': 6, 'yards': 50, 'source': 'boxscore'},
            'away': {'abbr': away, 'score': 17, 'flags': 5, 'yards': 41, 'source': 'boxscore'},
            'flags': 11, 'yards': 91, 'log': log or [], 'costliest': None,
            'preview': {'crew': 'Shawn Hochuli', 'projected': 12.1}}


def live(games, week=12, season=SEASON):
    return {'updatedAt': '2026-12-01T06:00:00.000Z', 'week': week, 'season': season, 'live': False,
            'games': games, 'costliest': [], 'wpModel': 'ESPN live win probability', 'source': 'ESPN'}


def schedule(rows):
    return pd.DataFrame(rows, columns=['season', 'game_type', 'week', 'gameday', 'away_team', 'home_team'])


# Week 12: Thursday, Saturday (late season) and Monday; times in UTC, dates in Eastern
WEEK12 = [
    game('1', 'GB', 'LA', '2026-11-26T01:00Z'),       # Wednesday 8 PM ET = Nov 25 in Eastern
    game('2', 'CHI', 'DET', '2026-11-26T18:00Z',
         log=[flag(team='DET', type_='Face Mask', player='D.Reed', yards=15, qtr=4, clock='1:29'),
              flag(team='CHI', status='declined', yards=0, qtr=2, clock='0:16'),
              flag(qtr=1, clock='14:05')]),
    game('3', 'DEN', 'PIT', '2026-11-28T21:30Z'),     # a Saturday game
    game('4', 'CAR', 'TB', '2026-12-01T01:15Z'),      # Monday night = Nov 30 in Eastern
]
SCHED12 = schedule([
    (SEASON, 'REG', 12, '2026-11-25', 'GB', 'LA'), (SEASON, 'REG', 12, '2026-11-26', 'CHI', 'DET'),
    (SEASON, 'REG', 12, '2026-11-28', 'DEN', 'PIT'), (SEASON, 'REG', 12, '2026-11-30', 'CAR', 'TB'),
])


@pytest.fixture
def out_dir(tmp_path, monkeypatch):
    d = tmp_path / 'gameday'
    monkeypatch.setattr(ga, 'OUT_DIR', d)
    monkeypatch.setattr(ga, 'ROOT', tmp_path)
    return d


@pytest.fixture
def store(tmp_path):
    return raw_capture.LocalStore(tmp_path / 'r2'), ''


def run(feed, sched=SCHED12, **kw):
    return ga.run(json.dumps(feed).encode(), schedule_loader=lambda s: sched, **kw)


# ---- the "week complete" rule --------------------------------------------------

def test_one_game_still_live_is_not_complete():
    games = [dict(g) for g in WEEK12]
    games[3] = game('4', 'CAR', 'TB', '2026-12-01T01:15Z', state='in', detail='Q4 2:10')
    st = ga.week_status(live(games))
    assert not st['complete'] and st['final'] == 3 and st['total'] == 4


def test_all_final_is_complete():
    assert ga.week_status(live(WEEK12))['complete']


def test_saturday_game_counts_like_any_other():
    games = [dict(g) for g in WEEK12]
    games[2] = game('3', 'DEN', 'PIT', '2026-11-28T21:30Z', state='pre', detail='11/28 - 4:30 PM EST')
    assert not ga.week_status(live(games))['complete']        # Saturday game not played yet
    assert ga.week_status(live(WEEK12))['complete']           # once final, the week can close


def test_postponed_game_holds_the_week_open():
    games = [dict(g) for g in WEEK12]
    games[3] = game('4', 'CAR', 'TB', '2026-12-01T01:15Z', state='post', detail='Postponed')
    st = ga.week_status(live(games))
    assert not st['complete'] and len(st['postponed']) == 1 and not st['unfinished']


def test_empty_feed_is_not_complete():
    assert not ga.week_status(live([]))['complete']


# ---- regular season only ---------------------------------------------------------

def test_week_18_game_in_january_saves(out_dir, store):
    feed = live([game('9', 'DAL', 'NYG', '2027-01-10T18:00Z')], week=18)
    sched = schedule([(SEASON, 'REG', 18, '2027-01-10', 'DAL', 'NYG')])
    assert run(feed, sched, store=store) == 0
    assert (out_dir / f'{SEASON}-week-18.json').exists()


def test_wild_card_game_does_not_save(out_dir, store, capsys):
    feed = live([game('9', 'DAL', 'NYG', '2027-01-16T21:30Z')], week=1)
    sched = schedule([(SEASON, 'REG', 18, '2027-01-10', 'DAL', 'NYG'),
                      (SEASON, 'WC', 19, '2027-01-16', 'DAL', 'NYG')])
    assert run(feed, sched, store=store) == 1
    assert 'postseason not supported yet' in capsys.readouterr().out
    assert not out_dir.exists() and not (store[0].root).exists()


def test_games_not_in_schedule_do_not_save(out_dir, store, capsys):
    sched = schedule([(SEASON, 'REG', 12, '2026-11-25', 'GB', 'LA')])
    assert run(live(WEEK12), sched, store=store) == 1
    assert "feed games don't match the schedule" in capsys.readouterr().out
    assert not out_dir.exists()


def test_wrong_week_in_schedule_does_not_save(out_dir, store, capsys):
    sched = SCHED12.assign(week=11)
    assert run(live(WEEK12), sched, store=store) == 1
    assert "don't match" in capsys.readouterr().out


def test_wednesday_night_game_matches_on_eastern_date():
    assert ga.match_schedule(live(WEEK12), SCHED12) == ('regular', '')


# ---- the per-flag line ---------------------------------------------------------------

def test_flag_line_format():
    assert ga.flag_line(flag()) == 'Q3 4:12 · CHI · Defensive Holding · T.Edwards · 10 yds'


def test_flag_line_variants():
    assert ga.flag_line(flag(player=None, type_='Delay of Game', yards=5, qtr=1, clock='9:00')) == \
        'Q1 9:00 · CHI · Delay of Game · 5 yds'
    assert ga.flag_line(flag(status='declined', yards=0)) == 'Q3 4:12 · CHI · Defensive Holding · T.Edwards · declined'
    assert ga.flag_line(flag(status='offsetting', yards=0)).endswith('· offsetting')
    assert ga.flag_line(flag(qtr=5, clock='8:30', yards=1)) == 'OT 8:30 · CHI · Defensive Holding · T.Edwards · 1 yd'


# ---- the published file ------------------------------------------------------------------

def test_published_file_has_no_play_text_or_probabilities():
    feed = live([dict(g) for g in WEEK12])
    secret = 'PENALTY on CHI-T.Edwards, Defensive Holding, 10 yards, enforced at DET 30 - No Play.'
    for g in feed['games']:
        g['text'] = secret
        for f in g['log']:
            f['text'] = secret
    out = ga.build_public(feed, '2026-12-01T06:00:00+00:00')
    text = json.dumps(out)
    assert 'PENALTY on' not in text and 'enforced at' not in text
    for banned in ('"text"', '"wpCost"', '"wpMethod"', '"wall"', '"costliest"', '"preview"', '"network"'):
        assert banned not in text
    g = out['games'][1]
    assert set(g) == {'id', 'start', 'status', 'away', 'home', 'acceptedByType', 'flagLines'}
    assert set(g['home']) <= {'abbr', 'score', 'flags', 'yards', 'typeNotIdentified'}


def test_published_game_summary():
    out = ga.build_public(live(WEEK12), 'x')
    g = next(g for g in out['games'] if g['id'] == '2')
    # oldest first; declined listed but not counted
    assert g['flagLines'] == ['Q1 14:05 · CHI · Defensive Holding · T.Edwards · 10 yds',
                              'Q2 0:16 · CHI · Defensive Holding · T.Edwards · declined',
                              'Q4 1:29 · DET · Face Mask · D.Reed · 15 yds']
    assert g['acceptedByType'] == {'CHI': {'Defensive Holding': 1}, 'DET': {'Face Mask': 1}}
    assert g['home'] == {'abbr': 'DET', 'score': 24, 'flags': 6, 'yards': 50, 'typeNotIdentified': 5}
    assert g['status'] == 'final'


def test_type_not_identified_chi_at_det():
    """2026 Week 12, CHI at DET: box score 4 accepted for CHI, 3 typed from the play text."""
    g = game('2', 'CHI', 'DET', '2026-11-26T18:00Z',
             log=[flag(team='CHI', type_='Face Mask', yards=15),
                  flag(team='CHI', type_='Defensive Offside', yards=5),
                  flag(team='CHI', type_='Defensive Pass Interference', yards=5),
                  flag(team='CHI', status='declined', yards=0)]
                 + [flag(team='DET', type_='False Start', yards=5)] * 9)
    g['away'].update(flags=4, yards=25)
    g['home'].update(flags=9, yards=45)
    out = ga.build_public(live([g]), 'x')['games'][0]
    assert out['away']['typeNotIdentified'] == 1
    assert sum(out['acceptedByType']['CHI'].values()) + out['away']['typeNotIdentified'] == out['away']['flags']
    assert 'typeNotIdentified' not in out['home']                  # no gap: left out
    assert sum(out['acceptedByType']['DET'].values()) == out['home']['flags']


# ---- saving -------------------------------------------------------------------------------

def test_complete_week_saves_both_files(out_dir, store, capsys):
    assert run(live(WEEK12), store=store) == 0
    assert 'Week 12 saved' in capsys.readouterr().out
    pub = json.loads((out_dir / f'{SEASON}-week-12.json').read_text(encoding='utf-8'))
    assert pub['week'] == 12 and len(pub['games']) == 4
    stored = json.loads((store[0].root / f'espn/gameday/{SEASON}/week-12.json').read_bytes())
    assert stored['games'][1]['log'][0]['wpCost'] == 0.031      # the full copy keeps everything


def test_incomplete_week_saves_nothing(out_dir, store, capsys):
    games = [dict(g) for g in WEEK12]
    games[3] = game('4', 'CAR', 'TB', '2026-12-01T01:15Z', state='in', detail='Q2')
    assert run(live(games), store=store) == 0
    assert 'not complete (3 of 4 final)' in capsys.readouterr().out
    assert not out_dir.exists() and not store[0].root.exists()


def test_already_saved_week_is_left_alone(out_dir, store, capsys):
    out_dir.mkdir()
    (out_dir / f'{SEASON}-week-12.json').write_text('{"keep": true}', encoding='utf-8')
    assert run(live(WEEK12), store=store) == 0
    assert 'already saved' in capsys.readouterr().out
    assert json.loads((out_dir / f'{SEASON}-week-12.json').read_text()) == {'keep': True}


def test_r2_copy_is_never_overwritten_and_wins(out_dir, store, capsys):
    key = store[0].root / f'espn/gameday/{SEASON}/week-12.json'
    first = live(WEEK12)
    first['updatedAt'] = 'FIRST'
    key.parent.mkdir(parents=True)
    key.write_bytes(json.dumps(first).encode())
    assert run(live(WEEK12), store=store) == 0
    assert 'already existed' in capsys.readouterr().out
    assert json.loads(key.read_bytes())['updatedAt'] == 'FIRST'
    pub = json.loads((out_dir / f'{SEASON}-week-12.json').read_text(encoding='utf-8'))
    assert pub['feedUpdatedAt'] == 'FIRST'


def test_r2_unavailable_saves_nothing(out_dir, capsys):
    assert run(live(WEEK12), store=(None, 'no R2 credentials')) == 1
    assert 'R2 unavailable' in capsys.readouterr().out
    assert not out_dir.exists()


def test_dry_run_writes_nothing(out_dir, store, capsys):
    assert run(live(WEEK12), store=store, dry_run=True) == 0
    out = capsys.readouterr().out
    assert 'would be saved' in out and 'published file' in out
    assert not out_dir.exists() and not store[0].root.exists()


# ---- manual runs ---------------------------------------------------------------------------

def test_manual_run_for_another_week_saves_nothing(out_dir, store, capsys):
    assert run(live(WEEK12), store=store, want_week=11) == 1
    assert '/live shows Week 12, not Week 11' in capsys.readouterr().out
    assert not out_dir.exists()


def test_manual_run_saves_final_games_and_marks_postponed(out_dir, store):
    games = [dict(g) for g in WEEK12]
    games[3] = game('4', 'CAR', 'TB', '2026-12-01T01:15Z', state='post', detail='Postponed')
    assert run(live(games), store=store) == 0                       # scheduled run waits
    assert not out_dir.exists()
    assert run(live(games), store=store, want_week=12) == 0         # manual run saves
    pub = json.loads((out_dir / f'{SEASON}-week-12.json').read_text(encoding='utf-8'))
    assert [g['status'] for g in pub['games']] == ['final', 'final', 'final', 'postponed']


def test_manual_run_still_waits_for_a_live_game(out_dir, store):
    games = [dict(g) for g in WEEK12]
    games[3] = game('4', 'CAR', 'TB', '2026-12-01T01:15Z', state='in', detail='Q3')
    assert run(live(games), store=store, want_week=12) == 0
    assert not out_dir.exists()


def test_missed_week_warning_when_feed_rolled_over(out_dir, store, capsys):
    games = [game('1', 'GB', 'LA', '2026-12-03T01:15Z', state='pre', detail='12/2 - 8:15 PM EST')]
    assert run(live(games, week=13), store=store) == 0
    assert 'Week 12 missed: /live already shows Week 13' in capsys.readouterr().out
