"""analytics-export.yml (#164): the manual inputs (from, to, probe) become the script's
arguments. Runs the export step's own shell script from the workflow file with bash;
a `python` function stands in for the script and prints the arguments it got."""

import os
import shutil
import subprocess

import pytest
from workflow_scripts import WORKFLOWS

WORKFLOW = WORKFLOWS / 'analytics-export.yml'


def step_run_block(marker='id: export') -> str:
    """The `run: |` block of the step whose text contains `marker`."""
    lines = WORKFLOW.read_text(encoding='utf-8').splitlines()
    i = next(n for n, line in enumerate(lines) if line.strip() == marker)
    i = next(n for n in range(i, len(lines)) if lines[n].strip() == 'run: |')
    indent = len(lines[i]) - len(lines[i].lstrip())
    block = []
    for line in lines[i + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        block.append(line)
    width = min(len(x) - len(x.lstrip()) for x in block if x.strip())
    return '\n'.join(x[width:] for x in block) + '\n'


def find_bash():
    bash = shutil.which('bash')
    if not bash or 'system32' in bash.lower():   # WSL's launcher on Windows, not a bash for us
        git_bash = r'C:\Program Files\Git\bin\bash.exe'
        bash = git_bash if os.path.exists(git_bash) else None
    return bash


BASH = find_bash()


def run_step(probe='false', from_='', to=''):
    """GitHub sets FROM, TO and PROBE from the inputs; a boolean input arrives as 'true'/'false'."""
    script = 'python() { printf "ARG:%s\\n" "$@"; }\n' + step_run_block()
    env = {**os.environ, 'PROBE': probe, 'FROM': from_, 'TO': to}
    r = subprocess.run([BASH, '-c', script], capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0, r.stderr
    out = r.stdout.splitlines()
    args = [x[len('ARG:'):] for x in out if x.startswith('ARG:')]
    shown = next(x for x in out if x.startswith('Arguments: '))
    return args, shown


pytestmark = pytest.mark.skipif(BASH is None, reason='bash not found')


def test_runs_the_export_script():
    assert 'python scripts/analytics_export.py "${args[@]}"' in step_run_block()


def test_no_inputs_is_the_weekly_run():
    assert run_step() == (['scripts/analytics_export.py'], 'Arguments: (none)')


def test_probe_ticked_passes_probe():
    assert run_step(probe='true') == (['scripts/analytics_export.py', '--probe'], 'Arguments: --probe')


def test_from_and_to_pass_through():
    args, shown = run_step(from_='2026-05-01', to='2026-05-31')
    assert args == ['scripts/analytics_export.py', '--from', '2026-05-01', '--to', '2026-05-31']
    assert shown == 'Arguments: --from 2026-05-01 --to 2026-05-31'


def test_all_inputs_together():
    args, shown = run_step(probe='true', from_='2026-10-13', to='2026-10-13')
    assert args == ['scripts/analytics_export.py', '--from', '2026-10-13', '--to', '2026-10-13', '--probe']
    assert shown == 'Arguments: --from 2026-10-13 --to 2026-10-13 --probe'


def test_workflow_maps_inputs_to_env():
    text = WORKFLOW.read_text(encoding='utf-8')
    for line in ('FROM: ${{ inputs.from }}', 'TO: ${{ inputs.to }}', 'PROBE: ${{ inputs.probe }}'):
        assert line in text
