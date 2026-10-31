"""Raw capture (scripts/raw_capture.py, #88), with raw_capture.LocalStore standing
in for R2. The unreachable-endpoint test uses a closed port on this machine."""

import gzip
import hashlib
import json
import re
import time
from datetime import datetime, timezone

import polars as pl

import raw_capture as rc

FEED = b'<rss><item>Week 9 referee assignments</item></rss>'
URL = 'https://www.footballzebras.com/feed/'


def capture(store, process='update_data'):
    return rc.RawCapture(client=store, mode='on', process=process)


def grab(cap, content=FEED, name='assignments_feed'):
    cap.capture_bytes('footballzebras-feed', name, content, 'xml', 'application/rss+xml', URL)


def objects(root, prefix='raw/footballzebras-feed/'):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob('*')
                  if p.is_file() and not p.name.endswith('.meta.json')
                  and p.relative_to(root).as_posix().startswith(prefix))


def manifest(root, key):
    return json.loads((root / key).read_text())


# ---- key layout ---------------------------------------------------------------

def test_page_key_layout_and_content(tmp_path):
    cap = capture(rc.LocalStore(tmp_path))
    grab(cap)
    sha = hashlib.sha256(FEED).hexdigest()
    [key] = objects(tmp_path)
    assert re.fullmatch(rf'raw/footballzebras-feed/\d{{4}}-\d{{2}}-\d{{2}}/assignments_feed_\d{{6}}Z_{sha[:8]}\.xml\.gz', key)
    assert gzip.decompress((tmp_path / key).read_bytes()) == FEED   # exact bytes, sha of content
    meta = json.loads((tmp_path / (key + '.meta.json')).read_text())
    assert meta['sha256'] == sha and meta['source-url'] == URL and meta['run-id'] == 'local'


def test_table_key_layout(tmp_path):
    cap = capture(rc.LocalStore(tmp_path))
    cap.capture_frame('nflverse-teams', 'teams_colors_logos', pl.DataFrame({'team': ['KC', 'BUF']}))
    [key] = objects(tmp_path, 'raw/nflverse-teams/')
    assert re.fullmatch(r'raw/nflverse-teams/\d{4}-\d{2}-\d{2}/teams_colors_logos_\d{6}Z_[0-9a-f]{8}\.parquet', key)
    assert pl.read_parquet(tmp_path / key)['team'].to_list() == ['KC', 'BUF']
    assert cap.inputs[0]['rows'] == 2
    assert cap.inputs[0]['url'].endswith('teams/teams_colors_logos.parquet')


# ---- skip unchanged, new key when changed -------------------------------------

def first_run(tmp_path, monkeypatch):
    monkeypatch.setenv('GITHUB_RUN_ID', '101')
    cap1 = capture(rc.LocalStore(tmp_path))
    grab(cap1)
    cap1.write_manifest()
    assert cap1.manifest_key
    return cap1


def test_unchanged_file_is_not_written_again(tmp_path, monkeypatch):
    cap1 = first_run(tmp_path, monkeypatch)
    first_key = cap1.inputs[0]['key']
    monkeypatch.setenv('GITHUB_RUN_ID', '102')
    cap2 = capture(rc.LocalStore(tmp_path))
    grab(cap2)
    cap2.write_manifest()
    assert objects(tmp_path) == [first_key]                      # nothing new stored
    assert cap2.inputs[0]['key'] == first_key and cap2.inputs[0]['new'] is False
    [entry] = manifest(tmp_path, cap2.manifest_key)['inputs']   # still listed, earlier key
    assert entry['key'] == first_key and entry['new'] is False
    assert cap2.status() == {'status': 'ok', 'new': 0, 'unchanged': 1, 'manifest': cap2.manifest_key}


def test_changed_file_gets_new_key(tmp_path, monkeypatch):
    cap1 = first_run(tmp_path, monkeypatch)
    monkeypatch.setenv('GITHUB_RUN_ID', '102')
    cap2 = capture(rc.LocalStore(tmp_path))
    grab(cap2, FEED + b'<!-- updated -->')
    assert cap2.inputs[0]['new'] is True
    assert cap2.inputs[0]['key'] != cap1.inputs[0]['key']
    assert len(objects(tmp_path)) == 2


# ---- refused second write -----------------------------------------------------

class CountingStore(rc.LocalStore):
    def __init__(self, root):
        super().__init__(root)
        self.puts = 0

    def put_object(self, **kw):
        self.puts += 1
        return super().put_object(**kw)


def test_refused_write_never_overwrites(tmp_path, monkeypatch, capsys):
    fixed = datetime(2026, 11, 1, 17, 0, 5, tzinfo=timezone.utc)

    class FixedDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(rc, 'datetime', FixedDT)
    sha = hashlib.sha256(FEED).hexdigest()
    key = f'raw/footballzebras-feed/2026-11-01/assignments_feed_170005Z_{sha[:8]}.xml.gz'
    (tmp_path / key).parent.mkdir(parents=True)
    (tmp_path / key).write_bytes(b'already here')          # an object already at that key
    store = CountingStore(tmp_path)
    cap = capture(store)
    grab(cap)
    assert (tmp_path / key).read_bytes() == b'already here'   # never overwritten
    assert store.puts == 1                                    # one attempt
    assert cap.mode == 'failed' and 'PreconditionFailed' in cap.error
    grab(cap, b'other content')                               # no more R2 calls
    cap.write_manifest()
    assert store.puts == 1
    out = capsys.readouterr().out
    assert out.count('Raw capture:') == 1                     # one warning
    assert cap.status()['status'] == 'failed'


# ---- manifest and input fields ------------------------------------------------

def test_manifest_and_input_fields(tmp_path, monkeypatch):
    monkeypatch.setenv('GITHUB_RUN_ID', '777')
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'schedule')
    cap = capture(rc.LocalStore(tmp_path))
    grab(cap)
    cap.write_manifest()
    assert re.fullmatch(r'raw/_runs/\d{4}-\d{2}-\d{2}/\d{6}Z_777-1\.json', cap.manifest_key)
    m = manifest(tmp_path, cap.manifest_key)
    assert set(m) == {'runId', 'startSha', 'event', 'schedule', 'startedAt', 'fetchStartedAt',
                      'fetchArgv', 'argv', 'finishedAt', 'versions', 'error', 'inputs'}
    assert m['runId'] == '777-1' and m['event'] == 'schedule' and m['error'] is None
    assert {'python', 'nflreadpy', 'polars', 'pandas', 'boto3'} <= set(m['versions'])
    [e] = m['inputs']
    assert set(e) == {'source', 'name', 'sha256', 'bytes', 'url', 'capturedAt', 'key', 'new', 'step'}
    assert e['sha256'] == hashlib.sha256(FEED).hexdigest()
    assert e['bytes'] == (tmp_path / e['key']).stat().st_size
    assert e['step'] == 'update_data' and e['new'] is True and e['url'] == URL


# ---- handoff fetch_assignments.py -> update_data.py ---------------------------

def test_handoff_between_steps(tmp_path, monkeypatch):
    store_dir, temp = tmp_path / 'store', tmp_path / 'runner_temp'
    temp.mkdir()
    monkeypatch.setenv('GITHUB_RUN_ID', '555')
    monkeypatch.setenv('RUNNER_TEMP', str(temp))
    fetch = capture(rc.LocalStore(store_dir), process='fetch_assignments')
    grab(fetch)
    fetch.save_handoff()
    assert rc.handoff_path().exists()

    update = capture(rc.LocalStore(store_dir))
    update.load_handoff()
    assert not rc.handoff_path().exists()                 # used once, then removed
    update.capture_frame('nflverse-teams', 'teams_colors_logos', pl.DataFrame({'team': ['KC']}))
    update.write_manifest()
    m = manifest(store_dir, update.manifest_key)
    assert [(e['step'], e['source']) for e in m['inputs']] == [
        ('fetch_assignments', 'footballzebras-feed'), ('update_data', 'nflverse-teams')]
    assert m['fetchStartedAt'] == fetch.started_at.isoformat(timespec='seconds')
    assert update.status()['new'] == 2


def test_handoff_carries_a_fetch_failure(tmp_path, monkeypatch):
    monkeypatch.setenv('GITHUB_RUN_ID', '556')
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    fetch = rc.RawCapture(mode='failed', error='AccessDenied: no', process='fetch_assignments')
    fetch.save_handoff()
    update = capture(rc.LocalStore(tmp_path / 'store'))
    update.load_handoff()
    s = update.status()
    assert s['status'] == 'failed' and 'fetch_assignments.py: AccessDenied: no' in s['error']


def test_handoff_from_another_run_is_ignored(tmp_path, monkeypatch):
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setenv('GITHUB_RUN_ID', '600')
    fetch = capture(rc.LocalStore(tmp_path / 'store'), process='fetch_assignments')
    grab(fetch)
    fetch.save_handoff()
    path = rc.handoff_path()
    data = json.loads(path.read_text())
    data['runId'] = '599-1'
    path.write_text(json.dumps(data))
    update = capture(rc.LocalStore(tmp_path / 'store'))
    update.load_handoff()
    assert update.extra_inputs == []


# ---- missing variables ---------------------------------------------------------

def test_no_variables_locally_is_off(capsys):
    cap = rc.RawCapture.from_env()
    assert cap.mode == 'off'
    assert cap.status() == {'status': 'off', 'new': 0, 'unchanged': 0}
    assert 'off (no R2 credentials' in capsys.readouterr().out


def test_no_variables_in_actions_is_failed(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv('GITHUB_ACTIONS', 'true')
    monkeypatch.setenv('R2_ENDPOINT', 'http://127.0.0.1:9')
    monkeypatch.setenv('NFLOBS_RAW_STORE_DIR', str(tmp_path))   # test hook ignored in Actions
    cap = rc.RawCapture.from_env()
    assert cap.mode == 'failed'
    assert cap.error == 'R2 credentials missing in GitHub Actions (R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY)'
    out = capsys.readouterr().out
    assert '::warning title=Raw capture::R2 credentials missing' in out
    assert cap.status()['status'] == 'failed'


# ---- unreachable endpoint ------------------------------------------------------

FAKE_ACCOUNT = 'acct0fake0id0for0tests'


def test_unreachable_endpoint_fails_fast_and_hides_endpoint(monkeypatch, capsys):
    endpoint = f'http://127.0.0.1:9/{FAKE_ACCOUNT}'   # closed port on this machine
    monkeypatch.setenv('R2_ENDPOINT', endpoint)
    monkeypatch.setenv('R2_ACCESS_KEY_ID', 'fake-key-id')
    monkeypatch.setenv('R2_SECRET_ACCESS_KEY', 'fake-secret')
    start = time.monotonic()
    cap = rc.RawCapture.from_env()
    assert cap.mode == 'on'
    grab(cap)
    cap.write_manifest()
    elapsed = time.monotonic() - start
    assert cap.mode == 'failed'
    assert elapsed < 30, f'took {elapsed:.1f} s'
    out = capsys.readouterr()
    text = out.out + out.err + (cap.error or '') + json.dumps(cap.status())
    assert FAKE_ACCOUNT not in text and '127.0.0.1:9' not in text
    assert 'fake-secret' not in text


def test_short_hides_endpoint(monkeypatch):
    endpoint = f'http://127.0.0.1:9/{FAKE_ACCOUNT}'
    monkeypatch.setenv('R2_ENDPOINT', endpoint)
    msg = rc.short(RuntimeError(f'Could not connect to the endpoint URL: "{endpoint}/nflobs-raw"'))
    assert FAKE_ACCOUNT not in msg and '<R2 endpoint>' in msg
