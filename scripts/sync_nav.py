"""Write the site menu into the two hand-written pages (#153).

    venv/Scripts/python scripts/sync_nav.py

frontend/index.html (Home) and frontend/gameday/index.html (Gameday) get
site_nav.nav_html() between <!-- nav:start --> and <!-- nav:end -->. Run it after
changing NAV in scripts/site_nav.py; check.py ("Menus match") fails until you do.
The pre-rendered pages get the same menu from build_static.py at deploy.
"""

import sys
from pathlib import Path

from site_nav import BLOCK_RE, nav_html

ROOT = Path(__file__).resolve().parent.parent
PAGES = {'/': ROOT / 'frontend' / 'index.html', '/gameday/': ROOT / 'frontend' / 'gameday' / 'index.html'}


def expected(path: str, text: str) -> str:
    """The page text with its menu block replaced by nav_html(path), keeping the indent
    the block has in the page."""
    m = BLOCK_RE.search(text)
    if not m:
        raise ValueError(f'{path}: no <!-- nav:start --> ... <!-- nav:end --> block')
    line_start = text.rfind('\n', 0, m.start()) + 1
    indent = text[line_start:m.start()]
    return text[:line_start] + nav_html(path, indent) + text[m.end():]


def main() -> int:
    for path, f in PAGES.items():
        text = f.read_text(encoding='utf-8')
        new = expected(path, text)
        name = f.relative_to(ROOT).as_posix() if f.is_relative_to(ROOT) else str(f)
        if new != text:
            f.write_text(new, encoding='utf-8', newline='\n')
            print(f'updated {name}')
        else:
            print(f'unchanged {name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
