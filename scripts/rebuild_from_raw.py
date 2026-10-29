#!/usr/bin/env python3
"""Rebuild a past run's site data from raw files alone, and compare (#88).

    python scripts/rebuild_from_raw.py --run 40557839336        (GitHub run id; R2_* secrets)
    python scripts/rebuild_from_raw.py --store-dir <folder> --manifest <key> --compare-dir <folder>
                                                                (local test, no R2)

1. Reads the run's manifest (raw/_runs/...), downloads every file it lists and
   checks each sha256.
2. Creates a git worktree at the commit the run started from (it holds that
   moment's state: assignments, overrides, ledger, frozen projections).
3. Runs fetch_assignments.py and update_data.py there, with the same arguments,
   through a launcher that fixes the clock to the run's start time, blocks the
   network (an input that wasn't captured fails loudly) and makes nflreadpy and
   http_get read the downloaded files. Raw capture is off during a rebuild.
4. Compares frontend/data/ and reports/miner/ with what the run committed: the
   data bot's commit right after the start commit, or the start commit itself if
   the run committed nothing. Run-time fields listed in IGNORE_KEYS are ignored.

Exit 0 when there are no differences, 1 otherwise.

Options (#134):
    --all            List every changed path (not just the first per file), then a
                     summary by pattern with three counts: changed numbers, removed
                     fields or files, and paths in previews/ or scorecard/.
    --keep           Keep the temporary folder, including the rebuilt data
                     (<folder>/rebuilt/frontend/data and reports/miner).
    --at <commit>    Run the manifest's inputs on another commit's code (the
                     worktree is created there instead of at the run's start commit).
                     Same as a copy of the manifest with startSha set to that commit.

Before/after check for a code change (local, no R2; on Windows prefix each command
with PYTHONUTF8=1, see #91):
    1. On the old code, capture the inputs:
         NFLOBS_RAW_STORE_DIR=<store> python scripts/update_data.py --full
       then git restore frontend/data reports/miner. The manifest is
       raw/_runs/<date>/<time>Z_local.json inside <store>.
    2. Before: replay on the old commit and keep the rebuilt data:
         python scripts/rebuild_from_raw.py --store-dir <store> --manifest <key> --at <old> --keep
       Control: the same with --compare-dir <kept folder>/rebuilt --all prints
       "no differences".
    3. Commit the change locally (no push), then replay the same inputs on it:
         python scripts/rebuild_from_raw.py --store-dir <store> --manifest <key> --at <new>
             --compare-dir <kept folder>/rebuilt --all
       Every changed path is listed; the summary shows whether any number moved.
"""

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import raw_capture as rc

ROOT = Path(__file__).resolve().parent.parent
BOT = 'github-actions[bot]'
COMPARE_DIRS = ('frontend/data', 'reports/miner')
# Written by the workflow gate (not the pipeline), from a live API call
IGNORE_FILES = {'frontend/data/source_stamp.json'}
# Run-time fields: when something was written, not what it says. The rebuild's clock
# is fixed at the run's start, so these differ by the seconds the original run took;
# they must still agree within TIME_TOLERANCE.
TIME_KEYS = {'fetchedAt', 'generatedAt', 'updatedAt', 'lastUpdated', 'runAt', 'checkedAt',
             'lastSuccess', 'frozenAt', 'snapshotAt', 'failingSince'}
TIME_TOLERANCE_MIN = 20
# Ignored entirely: raw capture is off during a rebuild
IGNORE_KEYS = {'rawCapture'}

LAUNCHER = r'''
import datetime as _dt, json, os, runpy, socket, sys
from pathlib import Path
cfg = json.loads(Path(sys.argv[1]).read_text())
FIXED = _dt.datetime.fromisoformat(cfg['clock'])
RealDT, RealDate = _dt.datetime, _dt.date

class FakeDT(RealDT):
    @classmethod
    def now(cls, tz=None):
        return FIXED.astimezone(tz) if tz else FIXED.replace(tzinfo=None)
    @classmethod
    def utcnow(cls):
        return FIXED.replace(tzinfo=None)
    @classmethod
    def today(cls):
        return FIXED.replace(tzinfo=None)

class FakeDate(RealDate):
    @classmethod
    def today(cls):
        return FIXED.date()

# Libraries load with the real clock classes
import numpy, pandas, polars as pl, pyarrow, requests, bs4  # noqa
import nflreadpy, nflreadpy.utils_date as ud
ud.date = FakeDate          # nflreadpy.get_current_season()

def blocked(*a, **k):
    raise OSError('network blocked during rebuild: an input was not captured')
socket.socket.connect = blocked
socket.create_connection = blocked
socket.getaddrinfo = blocked

frames = cfg['frames']
def frame(name):
    if name not in frames:
        raise RuntimeError(f'not captured in this run: {name}')
    return pl.read_parquet(frames[name])
def span(seasons):
    s = [seasons] if isinstance(seasons, int) else list(seasons)
    return f'{min(s)}-{max(s)}'
nflreadpy.load_pbp = lambda seasons=None, **k: frame(f'play_by_play_{seasons}')
nflreadpy.load_schedules = lambda seasons=None, **k: frame(f'games_{span(seasons)}')
nflreadpy.load_officials = lambda seasons=None, **k: frame(f'officials_{span(seasons)}')
nflreadpy.load_teams = lambda **k: frame('teams_colors_logos')

# Pipeline modules bind the fixed clock (they all use "from datetime import datetime")
_dt.datetime, _dt.date = FakeDT, FakeDate
sys.path.insert(0, 'scripts')
skip = {'rebuild_from_raw', 'r2_access_check', 'build_static', 'scorecard_report', 'check',
        'update_data', 'fetch_assignments'}
for f in sorted(Path('scripts').glob('*.py')):
    if f.stem not in skip:
        __import__(f.stem)
g = runpy.run_path(cfg['script'], run_name='rebuild_target')
_dt.datetime, _dt.date = RealDT, RealDate

pages = cfg['pages']
def http_get(url, source=None, name=None):
    if url not in pages:
        raise RuntimeError(f'not captured in this run: {url}')
    p = pages[url]
    return Path(p['path']).read_bytes().decode(p.get('encoding') or 'utf-8')
g['http_get'] = http_get

sys.argv = [cfg['script']] + cfg['argv']
code = g['main']()
print(f'REBUILD STEP EXIT {code}')
sys.exit(code or 0)
'''


def git(*args, cwd=ROOT) -> str:
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def find_manifest(client, run: str) -> str:
    keys = rc.list_keys(client, rc.RUNS_PREFIX)
    pat = re.compile(rf'_{re.escape(run)}(-\d+)?\.json$' if '-' not in run else rf'_{re.escape(run)}\.json$')
    hits = sorted(k for k in keys if pat.search(k))
    if not hits:
        sys.exit(f'No manifest for run {run} under {rc.RUNS_PREFIX}')
    return hits[-1]   # latest attempt


def download(client, manifest: dict, dest: Path) -> dict:
    """Download every input, check sha256. Returns {step: {'frames': {...}, 'pages': {...}}}."""
    out = {}
    for e in manifest['inputs']:
        if not e.get('key'):
            sys.exit(f"Input {e['source']}/{e['name']} has no stored object (capture failed in that run)")
        path = dest / e['key']
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(client.get_object(Bucket=rc.BUCKET, Key=e['key'])['Body'].read())
        data = path.read_bytes()
        content = gzip.decompress(data) if e['key'].endswith('.gz') else data
        if hashlib.sha256(content).hexdigest() != e['sha256']:
            sys.exit(f"sha256 mismatch for {e['key']}")
        step = out.setdefault(e.get('step', 'update_data'), {'frames': {}, 'pages': {}})
        if e['key'].endswith('.parquet'):
            step['frames'][e['name']] = str(path)
        else:
            plain = path.with_suffix('')
            plain.write_bytes(content)
            step['pages'][e['url']] = {'path': str(plain), 'encoding': e.get('encoding')}
    return out


def committed_target(start: str) -> str:
    """The data bot's commit right after `start`, or `start` if the run committed nothing."""
    try:
        after = git('rev-list', '--reverse', '--ancestry-path', f'{start}..origin/main').split()
    except subprocess.CalledProcessError:
        after = []
    if after:
        first = after[0]
        if git('rev-parse', f'{first}^') == start and git('log', '-1', '--format=%an', first) == BOT:
            return first
    return start


def normalize(obj):
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items() if k not in IGNORE_KEYS}
    if isinstance(obj, list):
        return [normalize(v) for v in obj]
    return obj


def close_in_time(a, b) -> bool:
    from datetime import datetime
    try:
        ta, tb = (datetime.fromisoformat(str(x).replace('Z', '+00:00')) for x in (a, b))
        return abs((ta - tb).total_seconds()) <= TIME_TOLERANCE_MIN * 60
    except (TypeError, ValueError):
        return a == b


def first_diff(a, b, path='$'):
    if path.rsplit('.', 1)[-1] in TIME_KEYS and isinstance(a, str) and isinstance(b, str):
        return None if close_in_time(a, b) else f'{path}: {a!r} vs {b!r} (more than {TIME_TOLERANCE_MIN} min apart)'
    if type(a) is not type(b):
        return f'{path}: {type(a).__name__} vs {type(b).__name__}'
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                return f'{path}.{k}: only in {"rebuild" if k in a else "original"}'
            d = first_diff(a[k], b[k], f'{path}.{k}')
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f'{path}: {len(a)} vs {len(b)} items'
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f'{path}[{i}]')
            if d:
                return d
        return None
    return None if a == b else f'{path}: {str(a)[:60]!r} vs {str(b)[:60]!r}'


def file_pairs(rebuilt: Path, original):
    """Each compared file: (name, rebuilt bytes or None, original bytes or None), sorted.
    original: a commit (str) or a folder (Path). Line endings are normalized to LF."""
    def files_in(base):
        return {p.relative_to(base).as_posix() for d in COMPARE_DIRS if (base / d).exists()
                for p in (base / d).rglob('*') if p.is_file()}
    if isinstance(original, Path):
        orig_files = files_in(original)
        read_orig = lambda f: (original / f).read_bytes()  # noqa: E731
    else:
        orig_files = set(git('ls-tree', '-r', '--name-only', original, '--', *COMPARE_DIRS).splitlines())
        read_orig = lambda f: subprocess.run(['git', 'show', f'{original}:{f}'], cwd=ROOT,  # noqa: E731
                                             capture_output=True, check=True).stdout
    new_files = files_in(rebuilt)
    for f in sorted((orig_files | new_files) - IGNORE_FILES):
        # Git stores LF; a Windows checkout may have CRLF
        a = (rebuilt / f).read_bytes().replace(b'\r\n', b'\n') if f in new_files else None
        b = read_orig(f).replace(b'\r\n', b'\n') if f in orig_files else None
        yield f, a, b


def compare(rebuilt: Path, original) -> list[str]:
    """original: a commit (str) or a folder (Path). Returns difference lines (the first per file)."""
    diffs = []
    for f, a, b in file_pairs(rebuilt, original):
        if a is None:
            diffs.append(f'{f}: missing from rebuild')
            continue
        if b is None:
            diffs.append(f'{f}: only in rebuild')
            continue
        if a == b:
            continue
        if f.endswith('.json'):
            try:
                ja, jb = normalize(json.loads(a)), normalize(json.loads(b))
            except ValueError:
                diffs.append(f'{f}: unreadable JSON')
                continue
            d = first_diff(ja, jb)
            if d:
                diffs.append(f'{f}: {d}')
        else:
            diffs.append(f'{f}: content differs')
    return diffs


# ---- --all: every changed path (#134) -------------------------------------------

def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def walk_all(a, b, path='$'):
    """Every difference between a (rebuild) and b (original), same rules as first_diff:
    a list of (path, kind, original value, rebuilt value)."""
    out = []
    if path.rsplit('.', 1)[-1] in TIME_KEYS and isinstance(a, str) and isinstance(b, str):
        if not close_in_time(a, b):
            out.append((path, 'time', b, a))
        return out
    if type(a) is not type(b):
        out.append((path, 'number' if _is_number(a) and _is_number(b) else 'type', b, a))
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in b:
                out.append((f'{path}.{k}', 'added', None, a[k]))
            elif k not in a:
                out.append((f'{path}.{k}', 'removed', b[k], None))
            else:
                out += walk_all(a[k], b[k], f'{path}.{k}')
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            out.append((path, 'length', len(b), len(a)))
        for i, (x, y) in enumerate(zip(a, b)):
            out += walk_all(x, y, f'{path}[{i}]')
        return out
    if a != b:
        out.append((path, 'number' if _is_number(a) else 'text' if isinstance(a, str) else 'value', b, a))
    return out


def compare_all(rebuilt: Path, original) -> list[tuple]:
    """Every changed path in every file: (file, path, kind, original value, rebuilt value)."""
    out = []
    for f, a, b in file_pairs(rebuilt, original):
        if a is None:
            out.append((f, '', 'file removed', None, None))
        elif b is None:
            out.append((f, '', 'file added', None, None))
        elif a == b:
            continue
        elif f.endswith('.json'):
            try:
                ja, jb = normalize(json.loads(a)), normalize(json.loads(b))
            except ValueError:
                out.append((f, '', 'unreadable JSON', None, None))
                continue
            out += [(f, *d) for d in walk_all(ja, jb)]
        else:
            out.append((f, '', 'content', None, None))
    return out


# Patterns that group many files or keys into one summary line
_GROUPS = [
    (re.compile(r'\[\d+\]'), '[*]'),
    (re.compile(r'/referee/[^/]+\.json'), '/referee/<slug>.json'),
    (re.compile(r'/teams/(?!index\.json)[^/]+\.json'), '/teams/<abbr>.json'),
    (re.compile(r'\d{4}-week-\d{2}'), '<season>-week-<nn>'),
    (re.compile(r'\.\d{4}_\d{2}_[A-Z]+_[A-Z]+'), '.<game>'),
]


def summarize(changes) -> list[str]:
    """Summary lines for compare_all() output: counts by pattern, then the three totals."""
    def pattern(f, p):
        s = f + (': ' + p if p else '')
        for rx, rep in _GROUPS:
            s = rx.sub(rep, s)
        return s
    counts = {}
    for f, p, kind, _, _ in changes:
        key = f'{pattern(f, p)}  ({kind})'
        counts[key] = counts.get(key, 0) + 1
    numbers = sum(1 for c in changes if c[2] == 'number')
    removed = sum(1 for c in changes if c[2] in ('removed', 'file removed'))
    gated = sum(1 for c in changes if c[0].startswith(('frontend/data/previews/', 'frontend/data/scorecard/')))
    lines = [f'{n:6}  {k}' for k, n in sorted(counts.items())]
    lines += ['', f'Changed paths: {len(changes)}', f'Changed numbers: {numbers}',
              f'Removed fields or files: {removed}', f'Paths in previews/ or scorecard/: {gated}']
    return lines


def _short(v):
    return '' if v is None else repr(v if isinstance(v, (int, float, bool)) else str(v)[:60])


def main():
    ap = argparse.ArgumentParser(description='Rebuild a past run from raw files alone and compare')
    ap.add_argument('--run', help='GitHub run id (optionally id-attempt)')
    ap.add_argument('--manifest', help='Manifest key instead of --run')
    ap.add_argument('--store-dir', help='Local folder laid out like the bucket (testing; no R2)')
    ap.add_argument('--compare-dir', help='Compare with this folder instead of the committed data (testing)')
    ap.add_argument('--keep', action='store_true', help='Keep the temporary folder, including the rebuilt data')
    ap.add_argument('--all', action='store_true', help='List every changed path, then a summary')
    ap.add_argument('--at', metavar='COMMIT', help="Run the manifest's inputs on this commit's code")
    args = ap.parse_args()
    if not (args.run or args.manifest):
        ap.error('pass --run or --manifest')
    if args.run and not re.fullmatch(r'\d+(-\d+)?', args.run):
        ap.error('--run must be a GitHub run id')
    if args.at:
        try:
            at_sha = git('rev-parse', '--verify', f'{args.at}^{{commit}}')
        except subprocess.CalledProcessError:
            ap.error(f'--at: {args.at} is not a commit')

    client = rc.LocalStore(args.store_dir) if args.store_dir else rc.make_client()
    key = args.manifest or find_manifest(client, args.run)
    manifest = json.loads(client.get_object(Bucket=rc.BUCKET, Key=key)['Body'].read())
    if args.at:
        print(f"   (--at: code from {at_sha[:8]} instead of the run's start commit {manifest['startSha'][:8]})")
        manifest['startSha'] = at_sha
    print(f"🔁 Rebuilding run {manifest['runId']} (started {manifest['startedAt']}, commit {manifest['startSha'][:8]})")
    if manifest.get('error'):
        sys.exit(f"That run stopped early ({manifest['error']}); nothing to compare")

    tmp = Path(tempfile.mkdtemp(prefix='nflobs-rebuild-'))
    wt = tmp / 'wt'
    try:
        inputs = download(client, manifest, tmp / 'inputs')
        print(f"   ✓ {len(manifest['inputs'])} inputs downloaded, sha256 checked")
        git('worktree', 'add', '--detach', str(wt), manifest['startSha'])
        (tmp / 'launch.py').write_text(LAUNCHER, encoding='utf-8')
        env = {k: v for k, v in os.environ.items()
               if k not in rc.ENV_NAMES and not k.startswith(('GITHUB_', 'RUNNER_', 'NFLOBS_'))}
        env['PYTHONIOENCODING'] = 'utf-8'
        steps = []
        if 'fetch_assignments' in inputs or manifest.get('fetchStartedAt'):
            steps.append(('scripts/fetch_assignments.py', manifest.get('fetchArgv') or [],
                          manifest.get('fetchStartedAt') or manifest['startedAt'], 'fetch_assignments'))
        steps.append(('scripts/update_data.py', manifest.get('argv') or ['--full'], manifest['startedAt'], 'update_data'))
        for script, argv, clock, step in steps:
            cfg = {'script': script, 'argv': argv, 'clock': clock, **inputs.get(step, {'frames': {}, 'pages': {}})}
            cfg_path = tmp / f'{step}.json'
            cfg_path.write_text(json.dumps(cfg))
            print(f"   ▶ {script} {' '.join(argv)} at {clock}")
            r = subprocess.run([sys.executable, str(tmp / 'launch.py'), str(cfg_path)], cwd=wt, env=env,
                               capture_output=True, text=True, encoding='utf-8', errors='replace')
            (tmp / f'{step}.log').write_text(r.stdout + r.stderr, encoding='utf-8')
            if r.returncode not in (0, 3) and not (step == 'fetch_assignments' and r.returncode == 2):
                print((r.stdout + r.stderr)[-3000:])
                sys.exit(f'{script} failed in the rebuild (exit {r.returncode})')

        if args.compare_dir:
            original, label = Path(args.compare_dir), args.compare_dir
        else:
            original = committed_target(manifest['startSha'])
            label = f'commit {original[:8]}'
        diffs = compare(wt, original)
        lines = [f"Rebuilt run {manifest['runId']} vs {label}: "
                 + ('no differences' if not diffs else f'{len(diffs)} files differ')]
        lines += [f'  - {d}' for d in diffs[:50]]
        print('\n'.join(lines))
        summary = []
        if args.all:
            changes = compare_all(wt, original)
            print(f'\nEvery changed path ({len(changes)}): kind, file: path: original -> rebuild')
            for f, p, kind, before, after in changes:
                print(f"  {kind:15} {f}{': ' + p if p else ''}: {_short(before)} -> {_short(after)}")
            summary = summarize(changes)
            print('\nSummary by pattern\n' + '\n'.join(summary))
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
                f.write('### Rebuild from raw\n\n' + '\n'.join(lines) + '\n')
                if summary:
                    f.write('\n#### Every changed path, by pattern\n\n```\n' + '\n'.join(summary) + '\n```\n')
        return 0 if not diffs else 1
    finally:
        if args.keep and wt.exists():
            for d in COMPARE_DIRS:
                if (wt / d).exists():
                    shutil.copytree(wt / d, tmp / 'rebuilt' / d)
        if wt.exists():
            subprocess.run(['git', 'worktree', 'remove', '--force', str(wt)], cwd=ROOT, capture_output=True)
        if args.keep:
            print(f"   (kept {tmp}; rebuilt data in {tmp / 'rebuilt'})")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
