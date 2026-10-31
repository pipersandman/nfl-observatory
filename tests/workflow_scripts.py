"""Take an inline Python script out of a workflow step, so tests run the exact code
the workflow runs (#89). Steps use `python - <<'EOF'` ... `EOF` heredocs."""

import re
import textwrap
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / '.github' / 'workflows'


def step_script(workflow: str, marker: str) -> str:
    """The heredoc script of the first step whose text contains `marker`
    (e.g. 'id: gate' or 'name: Fail if any module failed')."""
    text = (WORKFLOWS / workflow).read_text(encoding='utf-8')
    start = text.index(marker)
    m = re.compile(r"<<'EOF'\n(.*?)\n\s*EOF\n", re.S).search(text, start)
    if not m:
        raise ValueError(f'no heredoc after {marker!r} in {workflow}')
    return textwrap.dedent(m.group(1)) + '\n'
