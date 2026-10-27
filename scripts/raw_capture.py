"""Raw capture to Cloudflare R2 (#88).

Every pipeline run saves the raw data it pulled to the private bucket nflobs-raw,
append-only, so any past run's site data can be rebuilt from those files alone
(scripts/rebuild_from_raw.py).

Layout:
    raw/<source>/<YYYY-MM-DD>/<name>_<HHMMSS>Z_<sha8>.<ext>     one pulled file
    raw/_runs/<YYYY-MM-DD>/<HHMMSS>Z_<run id>.json              one manifest per run

- Tables are saved as zstd Parquet from the polars frame nflreadpy returned (what
  the pipeline used). Pages (Football Zebras feed and post) are saved as the exact
  bytes received, gzip-compressed. sha256 is always of the content before gzip.
- Every write is conditional (If-None-Match: *), so nothing is ever overwritten.
- A file whose sha256 matches its latest capture isn't written again; the run's
  manifest still lists it, pointing to the existing object.

Capture never stops the site update:
- No R2_* variables on a local run: capture is off (one log line).
- No R2_* variables inside GitHub Actions, or any R2 problem: capture is "failed",
  a warning is printed, and this process makes no more R2 calls. The run's result
  is unchanged; update_data.py turns the run red only if capture has been failing
  for more than 24 hours (run_status.json rawCapture).

Test hooks (ignored in GitHub Actions, like update_data.py's):
    NFLOBS_FAIL=raw_capture         capture fails at start
    NFLOBS_RAW_STORE_DIR=<folder>   use a local folder laid out like the bucket
Secrets and the endpoint (it contains the Cloudflare account ID) are never printed.
"""

import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

BUCKET = 'nflobs-raw'
RUNS_PREFIX = 'raw/_runs/'
ENV_NAMES = ('R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_ENDPOINT')
BUDGET_SECONDS = 120        # total time this process may spend on R2 calls
LOOKBACK_DAYS = 14          # how far back to look for the latest run manifest
NFLVERSE = 'https://github.com/nflverse/nflverse-data/releases/download/'
URLS = {
    'nflverse-pbp': NFLVERSE + 'pbp/{name}.parquet',
    'nflverse-schedules': NFLVERSE + 'schedules/games.parquet',
    'nflverse-officials': NFLVERSE + 'officials/officials.parquet',
    'nflverse-teams': NFLVERSE + 'teams/teams_colors_logos.parquet',
}


def in_actions() -> bool:
    return bool(os.environ.get('GITHUB_ACTIONS'))


def _test_hook(name: str) -> str:
    """A local-only test variable (never honoured in GitHub Actions)."""
    return '' if in_actions() else os.environ.get(name, '')


def warn(message: str) -> None:
    print(f'   ⚠️  Raw capture: {message}')
    if in_actions():
        print(f'::warning title=Raw capture::{message}')


def make_client():
    """boto3 S3 client for R2 from the R2_* variables, with short timeouts."""
    import boto3
    from botocore.config import Config
    cfg = Config(connect_timeout=5, read_timeout=30, retries={'max_attempts': 3, 'mode': 'standard'},
                 signature_version='s3v4',
                 # R2 doesn't accept boto3's default extra checksums on every request
                 request_checksum_calculation='when_required', response_checksum_validation='when_required')
    return boto3.client('s3', endpoint_url=os.environ['R2_ENDPOINT'], region_name='auto',
                        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
                        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'], config=cfg)


def error_code(e) -> str:
    """'PreconditionFailed', 'AccessDenied', '404', ... from a botocore error, else the type."""
    resp = getattr(e, 'response', None) or {}
    return str((resp.get('Error') or {}).get('Code') or type(e).__name__)


def short(e) -> str:
    msg = str(e).replace('\n', ' ')
    endpoint = os.environ.get('R2_ENDPOINT')
    if endpoint:
        msg = msg.replace(endpoint, '<R2 endpoint>')
    return f'{error_code(e)}: {msg[:200]}'


class LocalStore:
    """A folder laid out like the bucket, with the few S3 calls capture and rebuild use.
    For local tests only (NFLOBS_RAW_STORE_DIR, rebuild_from_raw.py --store-dir)."""

    def __init__(self, root):
        self.root = Path(root)

    def _path(self, key):
        return self.root / key

    @staticmethod
    def _err(code, status, op):
        from botocore.exceptions import ClientError
        return ClientError({'Error': {'Code': code, 'Message': code}, 'ResponseMetadata': {'HTTPStatusCode': status}}, op)

    def put_object(self, Bucket, Key, Body, IfNoneMatch=None, **kw):
        p = self._path(Key)
        if IfNoneMatch == '*' and p.exists():
            raise self._err('PreconditionFailed', 412, 'PutObject')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(Body if isinstance(Body, bytes) else Body.read())
        if kw.get('Metadata'):
            p.with_name(p.name + '.meta.json').write_text(json.dumps(kw['Metadata']))
        return {}

    def get_object(self, Bucket, Key):
        p = self._path(Key)
        if not p.exists():
            raise self._err('NoSuchKey', 404, 'GetObject')
        return {'Body': io.BytesIO(p.read_bytes())}

    def head_object(self, Bucket, Key):
        if not self._path(Key).exists():
            raise self._err('404', 404, 'HeadObject')
        return {}

    def delete_object(self, Bucket, Key):
        self._path(Key).unlink(missing_ok=True)
        return {}

    def list_objects_v2(self, Bucket, Prefix='', **kw):
        base = self.root
        keys = sorted(p.relative_to(base).as_posix() for p in base.rglob('*')
                      if p.is_file() and not p.name.endswith('.meta.json'))
        return {'Contents': [{'Key': k} for k in keys if k.startswith(Prefix)], 'IsTruncated': False}


def list_keys(client, prefix: str) -> list[str]:
    keys, token = [], None
    while True:
        kw = {'Bucket': BUCKET, 'Prefix': prefix, **({'ContinuationToken': token} if token else {})}
        resp = client.list_objects_v2(**kw)
        keys += [o['Key'] for o in resp.get('Contents', [])]
        if not resp.get('IsTruncated'):
            return keys
        token = resp.get('NextContinuationToken')


def _versions() -> dict:
    out = {'python': sys.version.split()[0]}
    for mod in ('nflreadpy', 'polars', 'pandas', 'boto3'):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            pass
    return out


def _git_head() -> str | None:
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True,
                              cwd=Path(__file__).resolve().parent, timeout=10).stdout.strip() or None
    except Exception:
        return os.environ.get('GITHUB_SHA')


def run_id() -> str | None:
    rid = os.environ.get('GITHUB_RUN_ID')
    return f"{rid}-{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}" if rid else None


def handoff_path() -> Path | None:
    """Where fetch_assignments.py leaves its captures for update_data.py (same run only)."""
    rid = run_id()
    if not rid:
        return None
    return Path(os.environ.get('RUNNER_TEMP') or tempfile.gettempdir()) / f'nflobs_raw_capture_{rid}.json'


class RawCapture:
    def __init__(self, client=None, mode='off', error=None, process='update_data'):
        self.client, self.mode, self.error, self.process = client, mode, error, process
        self.started_at = datetime.now(timezone.utc)
        self.inputs = []          # one entry per file this run used
        self.extra_errors = []    # from fetch_assignments.py's handoff
        self.extra_inputs = []
        self.extra_started = None
        self.extra_argv = None
        self._latest = None       # (source, name) -> latest captured entry
        self._deadline = None
        self.manifest_key = None

    # ---- setup ----------------------------------------------------------------
    @classmethod
    def from_env(cls, process='update_data'):
        if _test_hook('NFLOBS_FAIL') and 'raw_capture' in {x.strip() for x in _test_hook('NFLOBS_FAIL').split(',')}:
            cap = cls(mode='failed', error='forced failure (NFLOBS_FAIL)', process=process)
            warn(cap.error)
            return cap
        store_dir = _test_hook('NFLOBS_RAW_STORE_DIR')
        if store_dir:
            print(f'   📦 Raw capture: on (local folder {store_dir})')
            return cls(client=LocalStore(store_dir), mode='on', process=process)
        missing = [n for n in ENV_NAMES if not os.environ.get(n)]
        if missing:
            if in_actions():
                cap = cls(mode='failed', error=f'R2 credentials missing in GitHub Actions ({", ".join(missing)})', process=process)
                warn(cap.error)
                return cap
            print('   📦 Raw capture: off (no R2 credentials; normal on a local run)')
            return cls(mode='off', process=process)
        try:
            client = make_client()
        except Exception as e:
            cap = cls(mode='failed', error=short(e), process=process)
            warn(cap.error)
            return cap
        print('   📦 Raw capture: on')
        return cls(client=client, mode='on', process=process)

    # ---- R2 calls with the time budget ---------------------------------------
    def _call(self, fn, **kw):
        now = time.monotonic()
        if self._deadline is None:
            self._deadline = now + BUDGET_SECONDS
        if now > self._deadline:
            raise TimeoutError(f'gave up after {BUDGET_SECONDS} s')
        return fn(Bucket=BUCKET, **kw)

    def _fail(self, what, e):
        self.mode = 'failed'
        self.error = f'{what}: {short(e)}'
        warn(f'{self.error} (no more R2 calls this run; the update carries on)')

    def _latest_for(self, source, name):
        if self._latest is None:
            self._latest = {}
            day = self.started_at.date()
            for back in range(LOOKBACK_DAYS):
                keys = list_keys(_Bound(self), f'{RUNS_PREFIX}{day - timedelta(days=back)}/')
                if keys:
                    body = self._call(self.client.get_object, Key=max(keys))['Body'].read()
                    for e in json.loads(body).get('inputs', []):
                        if e.get('key'):
                            self._latest[(e['source'], e['name'])] = e
                    break
        return self._latest.get((source, name))

    # ---- capture --------------------------------------------------------------
    def capture_frame(self, source, name, df, url=None):
        """Save a polars frame as Parquet (skipped if unchanged since the last capture)."""
        if self.mode != 'on':
            return
        try:
            buf = io.BytesIO()
            df.write_parquet(buf, compression='zstd')
            body = buf.getvalue()
            self._store(source, name, 'parquet', body, body, 'application/vnd.apache.parquet',
                        url or URLS.get(source, '').format(name=name), {'rows': len(df)})
        except Exception as e:
            self._fail(f'{source}/{name}', e)

    def capture_bytes(self, source, name, content: bytes, ext, content_type, url, encoding=None):
        """Save a page exactly as received, gzip-compressed (skipped if unchanged)."""
        if self.mode != 'on':
            return
        try:
            body = gzip.compress(content, mtime=0)
            self._store(source, name, ext + '.gz', content, body, content_type, url,
                        {'encoding': encoding} if encoding else {})
        except Exception as e:
            self._fail(f'{source}/{name}', e)

    def _store(self, source, name, ext, content, body, content_type, url, extra):
        sha = hashlib.sha256(content).hexdigest()
        entry = {'source': source, 'name': name, 'sha256': sha, 'bytes': len(body), 'url': url,
                 'capturedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'), **extra}
        prev = self._latest_for(source, name)
        if prev and prev.get('sha256') == sha:
            self.inputs.append({**entry, 'key': prev['key'], 'new': False, 'bytes': prev.get('bytes', len(body))})
            return
        t = datetime.now(timezone.utc)
        key = f'raw/{source}/{t:%Y-%m-%d}/{name}_{t:%H%M%S}Z_{sha[:8]}.{ext}'
        meta = {'sha256': sha, 'source-url': url or '', 'captured-at': entry['capturedAt'],
                'run-id': run_id() or 'local', 'git-sha': _git_head() or ''}
        meta.update({k: str(v) for k, v in extra.items()})
        self._call(self.client.put_object, Key=key, Body=body, IfNoneMatch='*',
                   ContentType=content_type, Metadata=meta)
        self.inputs.append({**entry, 'key': key, 'new': True})
        self._latest[(source, name)] = self.inputs[-1]

    # ---- handoff between the two steps of one workflow run -------------------
    def save_handoff(self):
        path = handoff_path()
        if path and self.mode != 'off':
            path.write_text(json.dumps({'runId': run_id(), 'startedAt': self.started_at.isoformat(timespec='seconds'),
                                        'argv': sys.argv[1:],
                                        'mode': self.mode, 'error': self.error, 'inputs': self.inputs}))

    def load_handoff(self):
        path = handoff_path()
        if not path or not path.exists():
            return
        try:
            h = json.loads(path.read_text())
            if h.get('runId') == run_id():
                self.extra_inputs = h.get('inputs', [])
                self.extra_started = h.get('startedAt')
                self.extra_argv = h.get('argv', [])
                if h.get('mode') == 'failed':
                    self.extra_errors.append(f"fetch_assignments.py: {h.get('error')}")
            path.unlink()
        except Exception as e:
            self.extra_errors.append(f'handoff unreadable: {type(e).__name__}')

    # ---- manifest and status --------------------------------------------------
    def write_manifest(self, error=None):
        """One manifest per run, listing every input it used (new or reused)."""
        if self.mode != 'on':
            return
        t = datetime.now(timezone.utc)
        manifest = {
            'runId': run_id() or 'local', 'startSha': _git_head(),
            'event': os.environ.get('GITHUB_EVENT_NAME'), 'schedule': _schedule(),
            'startedAt': self.started_at.isoformat(timespec='seconds'),
            'fetchStartedAt': self.extra_started,
            'fetchArgv': self.extra_argv,
            'argv': sys.argv[1:],
            'finishedAt': t.isoformat(timespec='seconds'),
            'versions': _versions(), 'error': error,
            'inputs': [{**e, 'step': 'fetch_assignments'} for e in self.extra_inputs] +
                      [{**e, 'step': self.process} for e in self.inputs],
        }
        key = f"{RUNS_PREFIX}{t:%Y-%m-%d}/{t:%H%M%S}Z_{run_id() or 'local'}.json"
        try:
            self._call(self.client.put_object, Key=key, Body=json.dumps(manifest, indent=1).encode(),
                       IfNoneMatch='*', ContentType='application/json')
            self.manifest_key = key
        except Exception as e:
            self._fail('run manifest', e)

    def status(self) -> dict:
        """rawCapture block for run_status.json (update_data.py adds lastSuccess/failingSince)."""
        errors = ([self.error] if self.error else []) + self.extra_errors
        status = 'off' if self.mode == 'off' and not errors else ('failed' if errors else 'ok')
        all_inputs = self.extra_inputs + self.inputs
        out = {'status': status,
               'new': sum(1 for e in all_inputs if e.get('new')),
               'unchanged': sum(1 for e in all_inputs if e.get('new') is False)}
        if errors:
            out['error'] = '; '.join(errors)
        if self.manifest_key:
            out['manifest'] = self.manifest_key
        return out


class _Bound:
    """list_keys() helper that routes through RawCapture._call (budget applies)."""
    def __init__(self, cap):
        self.cap = cap

    def list_objects_v2(self, Bucket, **kw):
        return self.cap._call(self.cap.client.list_objects_v2, **kw)


def _schedule():
    try:
        return json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text()).get('schedule')
    except Exception:
        return None


_instance = None


def get(process='update_data') -> RawCapture:
    """The process-wide capture (created from the environment on first use)."""
    global _instance
    if _instance is None:
        _instance = RawCapture.from_env(process)
    return _instance
