"""Crew reassignments (#142): marks beside names, refetching a complete week when the
Football Zebras post changes, the fewer-games warning, stale overrides, and the
run_status.json notices. No network: HTTP calls are replaced.

tests/fixtures/fz_week8_lines.txt holds only the game lines of the updated Week 8,
2026 post (day, matchup, crew chief, time, network), written for these tests; the
post itself is never committed."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

import fetch_assignments as fa
import update_data as ud

LINES = (Path(__file__).parent / 'fixtures' / 'fz_week8_lines.txt').read_text(encoding='utf-8').splitlines()
POST_URL = 'https://www.footballzebras.com/2026/10/week-8-referee-assignments-2026/'
PUBLISHED = 'Tue, 27 Oct 2026 16:19:15 +0000'
FIRST_POST = '2026-10-27T16:19:15Z'     # the post as first published
UPDATED = '2026-10-29T23:58:49Z'        # Thursday's update (the swap)

# Week 8, 2026: (away, home, gameday, gametime, crew chief after the update)
WEEK8 = [
    ('CAR', 'GB', '2026-10-29', '20:15', 'Scott Novak'),
    ('BAL', 'BUF', '2026-11-01', '13:00', 'Clay Martin'),
    ('TEN', 'CIN', '2026-11-01', '13:00', 'Brad Allen'),
    ('ARI', 'DAL', '2026-11-01', '13:00', 'Ron Torbert'),
    ('MIN', 'DET', '2026-11-01', '13:00', 'Craig Wrolstad'),
    ('IND', 'JAX', '2026-11-01', '13:00', 'Adrian Hill'),
    ('LV', 'NYJ', '2026-11-01', '13:00', 'John Hussey'),
    ('CLE', 'PIT', '2026-11-01', '13:00', 'Alex Kemp'),
    ('ATL', 'TB', '2026-11-01', '13:00', 'Alan Eck'),
    ('LAC', 'LA', '2026-11-01', '16:05', 'Brad Rogers'),
    ('KC', 'DEN', '2026-11-01', '16:25', 'Clete Blakeman'),
    ('NE', 'MIA', '2026-11-01', '16:25', 'Alex Moore'),
    ('PHI', 'WAS', '2026-11-01', '20:20', 'Shawn Hochuli'),
    ('CHI', 'SEA', '2026-11-02', '20:15', 'Shawn Smith'),
]
BEFORE_SWAP = {'2026_08_NE_MIA': 'Shawn Hochuli', '2026_08_PHI_WAS': 'Alex Moore'}

THU_NOON = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)    # after Thursday's game
AFTER_MNF = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)    # every game kicked off


def gid(away, home):
    return f'2026_08_{away}_{home}'


SCHEDULE = pd.DataFrame([{'game_id': gid(a, h), 'season': 2026, 'week': 8, 'game_type': 'REG',
                          'away_team': a, 'home_team': h, 'gameday': d, 'gametime': t}
                         for a, h, d, t, _ in WEEK8])


def page(lines=LINES, modified=UPDATED):
    """A stand-in article page: the meta tag and the game lines, one per paragraph."""
    meta = f'<meta property="article:modified_time" content="{modified.replace("Z", "+00:00")}" />' if modified else ''
    body = ''.join(f'<p>{ln}</p>' for ln in lines)
    return f'<html><head>{meta}</head><body><div class="entry-content">{body}</div></body></html>'


FEED = (f'<rss><channel><item><link>{POST_URL}</link><pubDate>{PUBLISHED}</pubDate>'
        '<category>Week 8, 2026</category></item></channel></rss>')


def saved_file(crews=None, modified=FIRST_POST, **extra):
    """An assignment file as saved before the swap (all 14 assigned)."""
    crews = crews or {}
    games = [{'game_id': gid(a, h), 'away': a, 'home': h,
              'referee': crews.get(gid(a, h), BEFORE_SWAP.get(gid(a, h), ref)),
              'source': 'footballzebras', 'kickoff': None, 'network': None} for a, h, _, _, ref in WEEK8]
    src = {'name': 'Football Zebras', 'url': POST_URL, 'published': PUBLISHED}
    if modified:
        src['modified'] = modified
    return {'season': 2026, 'week': 8, 'gamesScheduled': 14, 'gamesAssigned': 14, 'source': src,
            'fetchedAt': '2026-10-27T19:00:00+00:00', 'games': games, **extra}


class Run:
    """process_week() for Week 8 in a temporary folder, with a fixed clock and fake HTTP."""

    def __init__(self, monkeypatch, tmp_path, now, html=None, api=UPDATED, existing=None, overrides=''):
        self.calls = []
        self.html, self.api = html or page(), api
        out = tmp_path / 'frontend' / 'data' / 'assignments'
        out.mkdir(parents=True)
        self.path = out / '2026-week-08.json'
        if existing:
            self.path.write_text(json.dumps(existing))
        (tmp_path / 'overrides.csv').write_text('game_id,referee\n' + overrides)
        monkeypatch.setattr(fa, 'PROJECT_DIR', tmp_path)
        monkeypatch.setattr(fa, 'OUT_DIR', out)
        monkeypatch.setattr(fa, 'OVERRIDES', tmp_path / 'overrides.csv')
        monkeypatch.setattr(fa, 'now_utc', lambda: now)
        monkeypatch.setattr(fa, 'http_get', self.http_get)

    def http_get(self, url, source=None, name=None):
        self.calls.append('api' if 'wp-json' in url else 'post')
        if 'wp-json' in url:
            if self.api == 'fail':
                raise ConnectionError('stubbed')
            return json.dumps([{'modified_gmt': self.api.rstrip('Z')}])
        assert url == POST_URL
        return self.html

    def feed(self):
        self.calls.append('feed')
        return FEED

    def __call__(self, capsys, force=False):
        self.problems = fa.process_week(2026, 8, SCHEDULE, set(), self.feed, force=force)
        self.out = capsys.readouterr().out
        self.saved = json.loads(self.path.read_text()) if self.path.exists() else None
        return self

    def crew(self, game_id):
        return next(g['referee'] for g in self.saved['games'] if g['game_id'] == game_id)


# ---- marks beside names -------------------------------------------------------

@pytest.mark.parametrize('line, name', [
    ('Alex Moore ⇅', 'Alex Moore'),
    ('Shawn Hochuli ⇅', 'Shawn Hochuli'),
    ('Alex Moore ↔', 'Alex Moore'),
    ('Alex Moore*', 'Alex Moore'),
    ('Alex Moore †', 'Alex Moore'),
    ('‡ Alex Moore', 'Alex Moore'),
    ('Alex Moore (sub)', 'Alex Moore'),
    ("Shawn O'Neill-Smith", "Shawn O'Neill-Smith"),
    ('Alex Moore', 'Alex Moore'),
])
def test_clean_name(line, name):
    assert fa.clean_name(line) == name


def test_week8_fixture_parses_all_14_games_with_swapped_crews():
    games = fa.parse_assignments(fa.article_lines(page()), set())
    assert len(games) == 14
    by_game = {(g['away'], g['home']): g['referee'] for g in games}
    assert by_game == {(a, h): ref for a, h, _, _, ref in WEEK8}
    assert by_game[('NE', 'MIA')] == 'Alex Moore' and by_game[('PHI', 'WAS')] == 'Shawn Hochuli'


def test_page_modified_and_utc_stamp():
    assert fa.page_modified(page()) == UPDATED
    assert fa.utc_stamp('2026-10-29T23:58:49') == UPDATED
    assert fa.utc_stamp('2026-10-29T19:58:49-04:00') == UPDATED
    assert fa.utc_stamp('not a time') is None


# ---- first fetch -----------------------------------------------------------------

def test_first_fetch_saves_modified_time(monkeypatch, tmp_path, capsys):
    run = Run(monkeypatch, tmp_path, THU_NOON - pd.Timedelta(days=2))(capsys)
    assert run.calls == ['feed', 'post']
    assert run.saved['source'] == {'name': 'Football Zebras', 'url': POST_URL,
                                   'published': PUBLISHED, 'modified': UPDATED}
    assert run.saved['gamesAssigned'] == 14
    assert run.saved['warnings'] == [] and run.saved['changes'] == []
    assert run.problems == []


# ---- refetch when the post changes -----------------------------------------------

def test_updated_post_is_refetched_and_changes_reported(monkeypatch, tmp_path, capsys):
    run = Run(monkeypatch, tmp_path, THU_NOON, existing=saved_file())(capsys)
    assert run.calls == ['api', 'post']                      # no feed request
    assert run.crew('2026_08_NE_MIA') == 'Alex Moore'
    assert run.crew('2026_08_PHI_WAS') == 'Shawn Hochuli'
    assert run.saved['source']['modified'] == UPDATED
    assert 'Crew change: NE @ MIA: Shawn Hochuli → Alex Moore (Football Zebras update, modified 2026-10-29T23:58:49Z)' in run.out
    assert [(c['gameId'], c['from'], c['to'], c['source']) for c in run.saved['changes']] == [
        ('2026_08_NE_MIA', 'Shawn Hochuli', 'Alex Moore', 'footballzebras-update'),
        ('2026_08_PHI_WAS', 'Alex Moore', 'Shawn Hochuli', 'footballzebras-update')]
    assert all(c['postModified'] == UPDATED and c['foundAt'] == '2026-10-30T12:00:00Z' for c in run.saved['changes'])
    assert [k for k, _ in run.problems] == ['warn', 'warn']   # changes never fail the step


def test_changes_are_kept_across_fetches(monkeypatch, tmp_path, capsys):
    earlier = {'gameId': '2026_08_KC_DEN', 'from': 'A', 'to': 'Clete Blakeman', 'source': 'footballzebras-update',
               'postModified': FIRST_POST, 'foundAt': '2026-10-28T00:00:00Z'}
    run = Run(monkeypatch, tmp_path, THU_NOON, existing=saved_file(changes=[earlier]))(capsys)
    assert run.saved['changes'][0] == earlier and len(run.saved['changes']) == 3


def test_unchanged_post_is_not_refetched(monkeypatch, tmp_path, capsys):
    existing = saved_file(modified=UPDATED)
    run = Run(monkeypatch, tmp_path, THU_NOON, existing=existing)(capsys)
    assert run.calls == ['api']
    assert run.saved == existing                             # file untouched
    assert 'post unchanged since 2026-10-29T23:58:49Z' in run.out


def test_week_fully_kicked_off_makes_no_requests(monkeypatch, tmp_path, capsys):
    existing = saved_file()
    run = Run(monkeypatch, tmp_path, AFTER_MNF, existing=existing)(capsys)
    assert run.calls == [] and run.saved == existing


def test_failed_update_check_skips_this_run(monkeypatch, tmp_path, capsys):
    existing = saved_file()
    run = Run(monkeypatch, tmp_path, THU_NOON, api='fail', existing=existing)(capsys)
    assert run.calls == ['api'] and run.saved == existing
    assert 'update check failed' in run.out


def test_file_without_modified_time_is_refetched_once(monkeypatch, tmp_path, capsys):
    run = Run(monkeypatch, tmp_path, THU_NOON, api='fail', existing=saved_file(modified=None))(capsys)
    assert run.calls == ['api', 'post']
    assert run.saved['source']['modified'] == UPDATED         # from the page's meta tag


def test_kicked_off_game_never_changes_crew(monkeypatch, tmp_path, capsys):
    lines = [('Bill Vinovich' if ln == 'Scott Novak' else ln) for ln in LINES]
    run = Run(monkeypatch, tmp_path, THU_NOON, html=page(lines), existing=saved_file())(capsys)
    assert run.crew('2026_08_CAR_GB') == 'Scott Novak'
    msg = 'Week 8: CAR @ GB already kicked off; the post now lists Bill Vinovich, kept Scott Novak'
    assert msg in run.out and msg in run.saved['warnings']
    assert '2026_08_CAR_GB' not in {c['gameId'] for c in run.saved['changes']}


# ---- fewer games than scheduled ------------------------------------------------------

def without(name):
    return [ln for ln in LINES if not ln.startswith(name)]


def test_fewer_games_warning_names_kept_crew(monkeypatch, tmp_path, capsys):
    run = Run(monkeypatch, tmp_path, THU_NOON, html=page(without('Alex Moore')), existing=saved_file())(capsys)
    msg = ('Week 8: the post lists 13 of 14 scheduled games; '
           'missing NE @ MIA: kept from earlier fetch (Shawn Hochuli)')
    assert msg in run.out and run.saved['warnings'] == [msg]
    assert run.crew('2026_08_NE_MIA') == 'Shawn Hochuli'
    assert ('warn', msg) in run.problems


def test_fewer_games_warning_without_saved_crew(monkeypatch, tmp_path, capsys):
    run = Run(monkeypatch, tmp_path, THU_NOON - pd.Timedelta(days=2), html=page(without('Alex Moore')))(capsys)
    assert run.saved['warnings'] == ['Week 8: the post lists 13 of 14 scheduled games; missing NE @ MIA: no crew']
    assert run.saved['gamesAssigned'] == 13


# ---- overrides -------------------------------------------------------------------

def test_override_matching_the_post_is_flagged_as_no_longer_needed(monkeypatch, tmp_path, capsys):
    rows = '2026_08_NE_MIA,Alex Moore\n2026_08_PHI_WAS,Shawn Hochuli\n'
    run = Run(monkeypatch, tmp_path, THU_NOON, existing=saved_file(), overrides=rows)(capsys)
    flagged = [w for w in run.saved['warnings'] if 'no longer needed' in w]
    assert flagged == [
        'Week 8: override for 2026_08_NE_MIA (Alex Moore) is no longer needed: Football Zebras now lists the same '
        'crew; remove it from data/assignments_overrides.csv',
        'Week 8: override for 2026_08_PHI_WAS (Shawn Hochuli) is no longer needed: Football Zebras now lists the '
        'same crew; remove it from data/assignments_overrides.csv']
    assert run.crew('2026_08_NE_MIA') == 'Alex Moore'
    assert {g['source'] for g in run.saved['games'] if g['game_id'] in BEFORE_SWAP} == {'override'}


def test_override_that_differs_is_applied_without_flag(monkeypatch, tmp_path, capsys):
    run = Run(monkeypatch, tmp_path, THU_NOON, existing=saved_file(),
              overrides='2026_08_KC_DEN,Bill Vinovich\n')(capsys)
    assert run.crew('2026_08_KC_DEN') == 'Bill Vinovich'
    assert not [w for w in run.saved['warnings'] if 'no longer needed' in w]
    assert ('2026_08_KC_DEN', 'Clete Blakeman', 'Bill Vinovich', 'override') in {
        (c['gameId'], c['from'], c['to'], c['source']) for c in run.saved['changes']}


# ---- run_status.json notices (update_data.py) -------------------------------------

def test_notices_for_weeks_with_games_to_play(tmp_path):
    change = {'gameId': '2026_08_NE_MIA', 'from': 'Shawn Hochuli', 'to': 'Alex Moore',
              'source': 'footballzebras-update', 'postModified': UPDATED, 'foundAt': '2026-10-30T12:00:00Z'}
    (tmp_path / '2026-week-08.json').write_text(json.dumps({'season': 2026, 'week': 8,
                                                             'warnings': ['Week 8: a warning'], 'changes': [change]}))
    (tmp_path / '2026-week-07.json').write_text(json.dumps({'season': 2026, 'week': 7,
                                                             'warnings': ['Week 7: old'], 'changes': [change]}))
    sched = pd.DataFrame([
        {'season': 2026, 'week': 7, 'game_type': 'REG', 'result': 3.0},
        {'season': 2026, 'week': 8, 'game_type': 'REG', 'result': 7.0},
        {'season': 2026, 'week': 8, 'game_type': 'REG', 'result': float('nan')},
    ])
    assert ud.assignment_notices(tmp_path, sched) == [
        {'source': 'assignments', 'message': 'Week 8: a warning'},
        {'source': 'assignments', 'message': 'Crew change 2026_08_NE_MIA: Shawn Hochuli → Alex Moore '
                                             '(footballzebras-update, found 2026-10-30T12:00:00Z)'},
    ]


def test_notices_skip_finished_weeks_and_report_unreadable_files(tmp_path):
    (tmp_path / '2026-week-08.json').write_text('{not json')
    sched = pd.DataFrame([{'season': 2026, 'week': 8, 'game_type': 'REG', 'result': float('nan')}])
    [n] = ud.assignment_notices(tmp_path, sched)
    assert n['file'] == '2026-week-08.json' and 'error' in n
