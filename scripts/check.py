"""Run every check CI runs. Same command on Windows and Linux:

    venv/Scripts/python scripts/check.py     (laptop)
    python scripts/check.py                  (GitHub Actions)

Needs only the tools in scripts/requirements-dev.txt and Node. No network, no
secrets. Exit code 0 means every check passed.
"""

import compileall
import json
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


CHECKS = [
    ('Ruff lint', check_ruff),
    ('Python compiles', check_compile),
    ('Data JSON parses', check_json),
    ('Worker JS syntax', check_node),
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
