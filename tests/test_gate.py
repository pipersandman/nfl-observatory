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
    if _os.environ['TEST_API'] == 'fail':
        raise RuntimeError('stubbed API failure')
    return _io.BytesIO(_os.environ['TEST_API'].encode())
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


def run_gate(tmp_path, today, event, schedule, api_reply):
    (tmp_path / 'scripts').mkdir()
    shutil.copy(ROOT / 'scripts' / 'seasons.py', tmp_path / 'scripts' / 'seasons.py')
    data = tmp_path / 'frontend' / 'data'
    data.mkdir(parents=True)
    (data / 'source_stamp.json').write_text(json.dumps({'pbp': 'T1'}))
    out_file = tmp_path / 'github_output'
    out_file.write_text('')
    env = {k: v for k, v in os.environ.items() if k != 'GH_TOKEN'}
    env.update(EVENT=event, SCHEDULE=schedule, GITHUB_OUTPUT=str(out_file),
               TEST_TODAY=today, TEST_API=api_reply)
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
