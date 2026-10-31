"""Run every check CI runs. Same command on Windows and Linux:

    venv/Scripts/python scripts/check.py     (laptop)
    python scripts/check.py                  (GitHub Actions)

Needs the tools in scripts/requirements-dev.txt, the runtime packages in
scripts/requirements.txt (the tests import the pipeline) and Node. No network,
no secrets. Exit code 0 means every check passed.
"""

import compileall
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_ruff():
    """Ruff lint (rules in pyproject.toml)."""
    r = subprocess.run([sys.executable, '-m', 'ruff', 'check', '--no-cache', '.'], cwd=ROOT)
    return r.returncode == 0, ''


def check_compile():
    """Every Python file under scripts/ compiles."""
    ok = compileall.compile_dir(str(ROOT / 'scripts'), quiet=1, force=True, legacy=False)
    return bool(ok), ''


def check_json():
    """Every JSON file under frontend/data/ parses."""
    files = sorted((ROOT / 'frontend' / 'data').rglob('*.json'))
    bad = []
    for f in files:
        try:
            with open(f, encoding='utf-8') as fh:
                json.load(fh)
        except (OSError, ValueError) as ex:
            bad.append(f'{f.relative_to(ROOT).as_posix()}: {ex}')
    for b in bad:
        print('   ', b)
    return not bad, f'{len(files)} files'


def check_node():
    """Gameday worker JavaScript has no syntax errors."""
    node = shutil.which('node')
    if not node:
        print('    node not found (install Node LTS)')
        return False, ''
    files = sorted((ROOT / 'worker' / 'gameday').glob('*.js')) + sorted((ROOT / 'worker' / 'gameday').glob('*.mjs'))
    failed = [f for f in files if subprocess.run([node, '--check', str(f)]).returncode != 0]
    return not failed, f'{len(files)} files'


# No hard-coded seasons or week windows in what the site shows (#116; Ty's rule of
# 2026-10-29): labels and text take years and windows from the data.
LITERAL_FILES = ['frontend/js/*.js', 'frontend/index.html', 'scripts/build_static.py']
LITERAL_PATTERNS = [
    re.compile(r'\b20(1[5-9]|[23]\d)\b'),              # a season year, 2015-2039
    re.compile(r'\bWeeks? \d+(\s*[–-]\s*\d+)?\b'),     # "Week 7", "Weeks 1–4"
    re.compile(r'\bWk \d+'),                            # "Wk 7"
]
# True constants only. Each entry: (file, text the line contains, why it's allowed).
LITERAL_ALLOW = [
    ('frontend/js/gameday.js', 'week: 7, season: 2026',
     'demo mode only (?demo): simulated games, labeled "Demo mode" on the page'),
]


def _code_part(line, suffix):
    """The line without comments: whole-line comments are skipped, trailing ones cut."""
    s = line.strip()
    if s.startswith(('//', '#', '/*', '*', '<!--')):
        return ''
    if suffix == '.js':
        return re.split(r'\s//\s', line, maxsplit=1)[0]
    if suffix == '.py':
        return re.split(r'\s{2}#\s', line, maxsplit=1)[0]
    return line


def check_literals():
    """No literal season year or week window in site labels and text (allow-list above)."""
    found, n = [], 0
    for pattern in LITERAL_FILES:
        for f in sorted(ROOT.glob(pattern)):
            rel = f.relative_to(ROOT).as_posix()
            n += 1
            for i, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
                code = _code_part(line, f.suffix)
                if not any(p.search(code) for p in LITERAL_PATTERNS):
                    continue
                if any(rel == af and text in line for af, text, _ in LITERAL_ALLOW):
                    continue
                found.append(f'{rel}:{i}: {line.strip()[:110]}')
    for x in found:
        print('   ', x)
    return not found, f'{n} files' + (f', {len(found)} literal(s)' if found else '')


def check_menus():
    """The home page and /gameday/ carry the shared site menu (#153) and analytics
    snippet (#165): run scripts/sync_nav.py after changing scripts/site_nav.py or
    scripts/site_analytics.py."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from site_analytics import without_stamp
    from site_nav import without_kickoffs
    from sync_nav import PAGES, expected
    bad = []
    for path, f in PAGES.items():
        # The kickoff list for the live dot and track.js's ?v= stamp are filled at deploy;
        # they aren't part of the match
        text = without_stamp(without_kickoffs(f.read_text(encoding='utf-8')))
        try:
            if expected(path, text) != text:
                bad.append(f'{f.relative_to(ROOT).as_posix()}: menu or analytics snippet differs from scripts/site_nav.py / site_analytics.py (run scripts/sync_nav.py)')
        except ValueError as ex:
            bad.append(str(ex))
    for b in bad:
        print('   ', b)
    return not bad, f'{len(PAGES)} pages'


def check_pytest():
    """Tests in tests/ (#89). No network: tests/conftest.py blocks it."""
    # -q comes from pyproject.toml; passing it again would hide the summary line
    r = subprocess.run([sys.executable, '-m', 'pytest', '-p', 'no:cacheprovider'],
                       cwd=ROOT, capture_output=True, text=True)
    print(r.stdout + r.stderr, end='')
    summary = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''
    m = re.search(r'\d+ (passed|failed).*? in [\d.]+s', summary)
    return r.returncode == 0, m.group(0) if m else summary


CHECKS = [
    ('Ruff lint', check_ruff),
    ('Python compiles', check_compile),
    ('Data JSON parses', check_json),
    ('Worker JS syntax', check_node),
    ('No hard-coded years or windows', check_literals),
    ('Menus match', check_menus),
    ('pytest', check_pytest),
]


def main():
    results = []
    for name, fn in CHECKS:
        print(f'--- {name}', flush=True)
        ok, note = fn()
        results.append((name, ok, note))
    print()
    for name, ok, note in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}{f' ({note})' if note else ''}")
    failed = [n for n, ok, _ in results if not ok]
    print()
    print('ALL CHECKS PASSED' if not failed else f'{len(failed)} CHECK(S) FAILED: {", ".join(failed)}')
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main())
