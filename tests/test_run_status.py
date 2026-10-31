"""Raw capture's 24-hour rule (#88): raw_capture_status() and write_run_status() in
update_data.py, and the "Fail if any module failed" step in update-data.yml."""

import json
import os
import subprocess
import sys

import pytest

import update_data as ud
from workflow_scripts import step_script

FINAL_STEP = step_script('update-data.yml', 'name: Fail if any module failed')
FAILED = {'status': 'failed', 'new': 0, 'unchanged': 0, 'error': 'AccessDenied: denied'}
OK = {'status': 'ok', 'new': 2, 'unchanged': 5}
MODULES = {'scorecard': {'status': 'ok', 'outputs': ['scorecard.json']}}


# ---- raw_capture_status() -----------------------------------------------------

def test_25_hours_since_last_success_is_stale():
    rc = ud.raw_capture_status(FAILED, {'lastSuccess': '2026-11-01T06:00:00Z'}, '2026-11-02T07:00:00Z')
    assert rc['stale'] is True and rc['failingHours'] == 25.0
    assert rc['lastSuccess'] == '2026-11-01T06:00:00Z'
    assert rc['failingSince'] == '2026-11-02T07:00:00Z'   # first failure seen in this run


def test_23_hours_is_not_stale():
    rc = ud.raw_capture_status(FAILED, {'lastSuccess': '2026-11-01T06:00:00Z'}, '2026-11-02T05:00:00Z')
    assert rc['stale'] is False and rc['failingHours'] == 23.0


def test_never_succeeded_failing_25_hours_is_stale():
    rc = ud.raw_capture_status(FAILED, {'failingSince': '2026-11-01T06:00:00Z'}, '2026-11-02T07:00:00Z')
    assert rc['lastSuccess'] is None
    assert rc['stale'] is True and rc['failingHours'] == 25.0


def test_success_clears_failing_since():
    prev = {'lastSuccess': '2026-11-01T06:00:00Z', 'failingSince': '2026-11-01T07:00:00Z'}
    rc = ud.raw_capture_status(OK, prev, '2026-11-02T07:00:00Z')
    assert rc['lastSuccess'] == '2026-11-02T07:00:00Z'
    assert 'failingSince' not in rc and 'stale' not in rc


def test_local_run_keeps_last_record():
    prev = {'lastSuccess': '2026-11-01T06:00:00Z', 'failingSince': '2026-11-01T07:00:00Z'}
    rc = ud.raw_capture_status({'status': 'off', 'new': 0, 'unchanged': 0}, prev, '2026-11-02T07:00:00Z')
    assert rc['lastSuccess'] == prev['lastSuccess'] and rc['failingSince'] == prev['failingSince']


# ---- write_run_status() and the workflow's final step --------------------------

@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(ud, 'DATA_DIR', tmp_path)
    return tmp_path


def write(data_dir, prev_raw, raw, run_at):
    if prev_raw is not None:
        (data_dir / 'run_status.json').write_text(json.dumps({'rawCapture': prev_raw}))
    warnings = []
    ok = ud.write_run_status(dict(MODULES), warnings, run_at, raw)
    return ok, warnings, json.loads((data_dir / 'run_status.json').read_text())


def final_step(path):
    env = {**os.environ, 'RUN_STATUS': str(path)}
    return subprocess.run([sys.executable, '-c', FINAL_STEP], env=env,
                          capture_output=True, text=True, timeout=60)


def test_stale_turns_run_red(data_dir):
    ok, warnings, status = write(data_dir, {'lastSuccess': '2026-11-01T06:00:00Z'}, FAILED, '2026-11-02T07:00:00Z')
    assert ok is False and status['ok'] is False
    assert warnings[0]['message'].startswith('raw capture failing for 25.0 h')
    r = final_step(data_dir / 'run_status.json')
    assert r.returncode == 1
    assert '  - raw capture: failing for 25.0 h since 2026-11-01T06:00:00Z (AccessDenied: denied)' in r.stdout


def test_23_hours_is_warning_only(data_dir):
    ok, warnings, status = write(data_dir, {'lastSuccess': '2026-11-01T06:00:00Z'}, FAILED, '2026-11-02T05:00:00Z')
    assert ok is True and status['ok'] is True
    assert warnings == [{'source': 'raw_capture', 'message': 'raw capture failed: AccessDenied: denied'}]
    r = final_step(data_dir / 'run_status.json')
    assert r.returncode == 0 and 'All modules OK' in r.stdout


def test_never_succeeded_turns_run_red(data_dir):
    ok, _, _ = write(data_dir, {'failingSince': '2026-11-01T06:00:00Z'}, FAILED, '2026-11-02T07:00:00Z')
    assert ok is False
    r = final_step(data_dir / 'run_status.json')
    assert r.returncode == 1 and 'raw capture: failing for 25.0 h since 2026-11-01T06:00:00Z' in r.stdout


def test_success_after_failures_is_green(data_dir):
    ok, warnings, status = write(data_dir, {'lastSuccess': '2026-11-01T06:00:00Z',
                                            'failingSince': '2026-11-01T07:00:00Z'}, OK, '2026-11-02T07:00:00Z')
    assert ok is True and warnings == []
    assert 'failingSince' not in status['rawCapture']
    assert final_step(data_dir / 'run_status.json').returncode == 0


def test_failed_module_turns_run_red(data_dir):
    (data_dir / 'run_status.json').write_text(json.dumps({
        'ok': False, 'modules': {'previews': {'status': 'failed', 'error': 'KeyError: x'}}}))
    r = final_step(data_dir / 'run_status.json')
    assert r.returncode == 1 and '  - previews: failed (KeyError: x)' in r.stdout
