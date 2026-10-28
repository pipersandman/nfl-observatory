"""JSON writing that browsers can always read, and file writes that never leave a mix.

pandas/numpy produce NaN for missing values (e.g. a QB not named yet). NaN is not
valid JSON, and a single NaN makes the browser reject the whole file, which breaks
that part of the site. Every pipeline file is written through dumps() below.

atomic_write() writes one file so a crash can't leave it half-written. PendingWrites
lets a module that writes several files build them all first and write them only at
the end, so a failure partway leaves the complete old set (#81).
"""
import json
import math
import os
from pathlib import Path

import numpy as np


def forced_failure(name: str):
    """Test hook: NFLOBS_FAIL=team_pages,load_pbp,... makes the named step fail.
    Ignored in GitHub Actions so a forced failure can never reach production."""
    raw = os.environ.get('NFLOBS_FAIL', '')
    if raw and not os.environ.get('GITHUB_ACTIONS') and name in {x.strip() for x in raw.split(',')}:
        raise RuntimeError('forced failure (NFLOBS_FAIL)')


def atomic_write(path, text: str):
    """Write text (UTF-8) to <name>.tmp, then rename it into place. If anything fails,
    the old file is left untouched and the .tmp is removed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(text)
        forced_failure(f'atomic:{path.name}')
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


class PendingWrites:
    """Files a module will write, kept in memory until commit().

    Reads go through it: read_json(), exists() and glob() see this run's pending files
    as well as what's on disk, so a module that reads its own earlier output gets the
    same text it would have read back from disk."""

    def __init__(self, fail_point: str):
        self.fail_point = fail_point     # NFLOBS_FAIL=<fail_point> fails at the first put()
        self.files = {}                  # Path -> text, in the order they were added

    def put(self, path, text: str):
        self.files[Path(path)] = text
        forced_failure(self.fail_point)  # after at least one output is built, before any write

    def read_json(self, path, default=None):
        path = Path(path)
        if path in self.files:
            return json.loads(self.files[path])
        return json.loads(path.read_text()) if path.exists() else default

    def exists(self, path) -> bool:
        path = Path(path)
        return path in self.files or path.exists()

    def glob(self, folder, pattern: str):
        folder = Path(folder)
        found = set(folder.glob(pattern)) | {p for p in self.files if p.parent == folder and p.match(pattern)}
        return sorted(found)

    def commit(self):
        for path, text in self.files.items():
            atomic_write(path, text)
        self.files = {}


def clean(o):
    if isinstance(o, float):
        return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.generic):
        return clean(o.item())
    return o


def dumps(obj, **kw):
    kw.setdefault('indent', 2)
    kw.setdefault('default', str)
    return json.dumps(clean(obj), allow_nan=False, **kw)
