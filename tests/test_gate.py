"""The game-day gate in update-data.yml (#84): the step's script, taken from the
workflow file, run with a faked date, a stubbed nflverse releases API and a
temporary GITHUB_OUTPUT. The 11 cases from PR #87."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from workflow_scripts import step_script

ROOT = Path(__file__).resolve().parent.parent
GATE = step_script('update-data.yml', 'id: gate')

GAMEDAY = '0 15-23 * * 0'
WEEKLY = '0 6 * * 2'

# Runs before the gate script in the child process: fixed clock, fake API, no sockets.
PRELUDE = '''
import datetime as _d, io as _io, json as _json, os as _os, socket as _socket, urllib.request as _ur
_Y, _M, _D = (int(x) for x in _os.environ['TEST_TODAY'].split('-'))
class _FakeDT(_d.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(_Y, _M, _D, 16, 0, tzinfo=tz)
_d.datetime = _FakeDT
def _urlopen(req, timeout=None):
    url = getattr(req, 'full_url', req)
    with open(_os.environ['TEST_LOG'], 'a') as f:
        print(url, file=f)
    reply = _os.environ['TEST_FZ'] if 'footballzebras.com' in url else _os.environ['TEST_API']
    if reply == 'fail':
        raise RuntimeError('stubbed API failure')
    return _io.BytesIO(reply.encode())
_ur.urlopen = _urlopen
def _blocked(*a, **k):
    raise RuntimeError('network call blocked in tests')
_socket.socket.connect = _blocked
_socket.getaddrinfo = _blocked
'''


def api(assets: dict) -> str:
    return json.dumps({'assets': [{'name': f'play_by_play_{s}.parquet', 'updated_at': t}
                                  for s, t in assets.items()]})


# (id, date, event, schedule, API reply, skip, log line)
CASES = [
    ('jan-unchanged', '2027-01-10', 'schedule', GAMEDAY, api({2026: 'T1'}), 'true',
     'play-by-play 2026: last used T1, now T1 -> no new games, skipping'),
    ('mar-unchanged', '2027-03-15', 'schedule', GAMEDAY, api({2026: 'T1'}), 'true',
     'play-by-play 2026: last used T1, now T1 -> no new games, skipping'),
    ('mar-reuploaded', '2027-03-15', 'schedule', GAMEDAY, api({2026: 'T2'}), 'false',
     'play-by-play 2026: last used T1, now T2 -> updating'),
    ('opening-unpublished', '2027-09-09', 'schedule', GAMEDAY, api({2026: 'T1'}), 'true',
     'play-by-play 2027: last used T1, now None -> not published yet, skipping'),
    ('opening-api-fails', '2027-09-09', 'schedule', GAMEDAY, 'fail', 'false',
     'play-by-play 2027: last used T1, now None -> updating'),
    ('weekly-unpublished', '2027-09-14', 'schedule', WEEKLY, api({2026: 'T1'}), 'false',
     'play-by-play 2027: last used T1, now None -> not published yet, updating anyway (not a game-day run)'),
    ('weekly-unchanged', '2027-03-15', 'schedule', WEEKLY, api({2026: 'T1'}), 'false',
     'play-by-play 2026: last used T1, now T1 -> updating'),
    ('manual-unchanged', '2027-03-15', 'workflow_dispatch', '', api({2026: 'T1'}), 'false',
     'play-by-play 2026: last used T1, now T1 -> updating'),
    ('push-unchanged', '2027-03-15', 'push', '', api({2026: 'T1'}), 'false',
     'play-by-play 2026: last used T1, now T1 -> updating'),
    ('manual-unpublished', '2027-09-09', 'workflow_dispatch', '', api({2026: 'T1'}), 'false',
     'play-by-play 2027: last used T1, now None -> not published yet, updating anyway (not a game-day run)'),
    ('today-unchanged', '2026-10-27', 'schedule', GAMEDAY, api({2025: 'T0', 2026: 'T1'}), 'true',
     'play-by-play 2026: last used T1, now T1 -> no new games, skipping'),
]


def run_gate(tmp_path, today, event, schedule, api_reply, fz_reply='fail', assignments=None):
    """Run the gate. assignments: {file name: content} for frontend/data/assignments/.
    Returns (result, GITHUB_OUTPUT text, stamp); self-check URLs land in tmp_path/requests."""
    (tmp_path / 'scripts').mkdir()
    shutil.copy(ROOT / 'scripts' / 'seasons.py', tmp_path / 'scripts' / 'seasons.py')
    data = tmp_path / 'frontend' / 'data'
    data.mkdir(parents=True)
    (data / 'source_stamp.json').write_text(json.dumps({'pbp': 'T1'}))
    out_file = tmp_path / 'github_output'
    out_file.write_text('')
    env = {k: v for k, v in os.environ.items() if k != 'GH_TOKEN'}
    env.update(EVENT=event, SCHEDULE=schedule, GITHUB_OUTPUT=str(out_file),
               TEST_TODAY=today, TEST_API=api_reply, TEST_FZ=fz_reply,
               TEST_LOG=str(tmp_path / 'requests'))
    if assignments:
        folder = data / 'assignments'
        folder.mkdir()
        for name, content in assignments.items():
            (folder / name).write_text(json.dumps(content))
    r = subprocess.run([sys.executable, '-c', PRELUDE + GATE], cwd=tmp_path, env=env,
                       capture_output=True, text=True, timeout=60)
    stamp = json.loads((data / 'source_stamp.json').read_text())
    return r, out_file.read_text(), stamp


def test_gate_script_found():
    assert 'nflverse_current_season' in GATE and 'GITHUB_OUTPUT' in GATE


@pytest.mark.parametrize('case', CASES, ids=[c[0] for c in CASES])
def test_gate_case(tmp_path, case):
    _, today, event, schedule, api_reply, skip, line = case
    r, output, stamp = run_gate(tmp_path, today, event, schedule, api_reply)
    assert r.returncode == 0, r.stderr
    assert line in r.stdout.splitlines()
    assert output == f'skip={skip}\n'
    if api_reply == 'fail':
        assert 'Could not check nflverse (stubbed API failure); continuing with the update' in r.stdout


@pytest.mark.parametrize('case', [c for c in CASES if 'now None' in c[6]], ids=lambda c: c[0])
def test_stamp_kept_while_file_missing(tmp_path, case):
    _, today, event, schedule, api_reply, _, _ = case
    _, _, stamp = run_gate(tmp_path, today, event, schedule, api_reply)
    assert stamp == {'pbp': 'T1'}


def test_stamp_updated_when_file_changes(tmp_path):
    _, _, stamp = run_gate(tmp_path, '2027-03-15', 'schedule', GAMEDAY, api({2026: 'T2'}))
    assert stamp['pbp'] == 'T2'
    assert stamp['checkedAt'] == '2027-03-15T16:00:00Z'


# ---- Football Zebras check on runs that would skip (#142) -----------------------

SATURDAY = '0 15 * * 6'
SUNDAY_EARLY = '0 12 * * 0'
POST = 'https://www.footballzebras.com/2026/10/week-8-referee-assignments-2026/'
SAVED = '2026-10-27T16:19:15Z'


def fz(modified):
    return json.dumps([{'modified_gmt': modified}])


def week(n, modified=SAVED, url=POST):
    src = {'name': 'Football Zebras', 'url': url}
    if modified:
        src['modified'] = modified
    return {f'2026-week-{n:02d}.json': {'season': 2026, 'week': n, 'source': src, 'games': []}}


def requests_made(tmp_path):
    f = tmp_path / 'requests'
    return f.read_text().splitlines() if f.exists() else []


def fz_requests(tmp_path):
    return [u for u in requests_made(tmp_path) if 'footballzebras.com' in u]


def test_new_crew_check_runs_are_game_day_runs():
    assert "'0 15 * * 6'" in GATE and "'0 12 * * 0'" in GATE


@pytest.mark.parametrize('schedule', [GAMEDAY, SATURDAY, SUNDAY_EARLY])
def test_updated_post_lets_the_run_go_ahead(tmp_path, schedule):
    r, output, _ = run_gate(tmp_path, '2026-10-31', 'schedule', schedule, api({2026: 'T1'}),
                            fz_reply=fz('2026-10-29T23:58:49'), assignments=week(8))
    assert output == 'skip=false\n'
    lines = r.stdout.splitlines()
    assert 'play-by-play 2026: last used T1, now T1 -> no new games' in lines
    assert ('Football Zebras 2026-week-08.json: post modified 2026-10-29T23:58:49Z, saved 2026-10-27T16:19:15Z '
            '-> updating (crews may have changed)') in lines
    assert fz_requests(tmp_path) == [
        'https://www.footballzebras.com/wp-json/wp/v2/posts?slug=week-8-referee-assignments-2026&_fields=modified_gmt']


@pytest.mark.parametrize('schedule', [GAMEDAY, SATURDAY, SUNDAY_EARLY])
def test_unchanged_post_still_skips(tmp_path, schedule):
    r, output, _ = run_gate(tmp_path, '2026-10-31', 'schedule', schedule, api({2026: 'T1'}),
                            fz_reply=fz('2026-10-27T16:19:15'), assignments=week(8))
    assert output == 'skip=true\n'
    assert 'play-by-play 2026: last used T1, now T1 -> no new games, skipping' in r.stdout.splitlines()
    assert len(fz_requests(tmp_path)) == 1


def test_only_the_two_latest_files_are_checked(tmp_path):
    files = {**week(7, url=POST.replace('week-8', 'week-7')), **week(8),
             **week(9, url=POST.replace('week-8', 'week-9'))}
    run_gate(tmp_path, '2026-10-31', 'schedule', GAMEDAY, api({2026: 'T1'}),
             fz_reply=fz('2026-10-27T16:19:15'), assignments=files)
    assert [u.split('slug=')[1].split('&')[0] for u in fz_requests(tmp_path)] == [
        'week-8-referee-assignments-2026', 'week-9-referee-assignments-2026']


def test_failed_check_is_not_a_change(tmp_path):
    r, output, _ = run_gate(tmp_path, '2026-10-31', 'schedule', GAMEDAY, api({2026: 'T1'}),
                            fz_reply='fail', assignments=week(8))
    assert output == 'skip=true\n'
    assert ('Could not check Football Zebras for 2026-week-08.json (RuntimeError); not counted as a change'
            in r.stdout.splitlines())


def test_file_without_saved_time_is_not_checked(tmp_path):
    _, output, _ = run_gate(tmp_path, '2026-10-31', 'schedule', GAMEDAY, api({2026: 'T1'}),
                            fz_reply=fz('2026-10-29T23:58:49'), assignments=week(8, modified=None))
    assert output == 'skip=true\n' and fz_requests(tmp_path) == []


@pytest.mark.parametrize('event, schedule, reply', [
    ('schedule', GAMEDAY, api({2026: 'T2'})),        # new play-by-play: going ahead anyway
    ('schedule', WEEKLY, api({2026: 'T1'})),         # not a game-day run
    ('workflow_dispatch', '', api({2026: 'T1'})),
])
def test_no_football_zebras_request_when_the_run_goes_ahead(tmp_path, event, schedule, reply):
    _, output, _ = run_gate(tmp_path, '2026-10-31', event, schedule, reply,
                            fz_reply=fz('2026-10-29T23:58:49'), assignments=week(8))
    assert output == 'skip=false\n' and fz_requests(tmp_path) == []


def test_updated_post_while_season_file_unpublished(tmp_path):
    r, output, _ = run_gate(tmp_path, '2027-09-12', 'schedule', GAMEDAY, api({2026: 'T1'}),
                            fz_reply=fz('2027-09-10T12:00:00'),
                            assignments={'2027-week-01.json': {'source': {'url': POST.replace('2026', '2027'),
                                                                          'modified': '2027-09-08T16:00:00Z'}}})
    assert output == 'skip=false\n'
    assert 'play-by-play 2027: last used T1, now None -> not published yet' in r.stdout.splitlines()
