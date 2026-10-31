"""Write the site menu and the analytics snippet into the two hand-written pages (#153, #165).

    venv/Scripts/python scripts/sync_nav.py

frontend/index.html (Home) and frontend/gameday/index.html (Gameday) get
site_nav.nav_html() between <!-- nav:start --> and <!-- nav:end -->, and
site_analytics.analytics_html() between <!-- analytics:start --> and
<!-- analytics:end -->. Run it after changing either script; check.py ("Menus
match") fails until you do. The pre-rendered pages get both from build_static.py.
"""

import sys
from pathlib import Path

import site_analytics
from site_nav import BLOCK_RE, nav_html

ROOT = Path(__file__).resolve().parent.parent
PAGES = {'/': ROOT / 'frontend' / 'index.html', '/gameday/': ROOT / 'frontend' / 'gameday' / 'index.html'}


def _replace(path: str, text: str, block_re, markers: str, make) -> str:
    """text with the block block_re finds replaced by make(indent), keeping the indent
    the block has in the page."""
    m = block_re.search(text)
    if not m:
        raise ValueError(f'{path}: no {markers} block')
    line_start = text.rfind('\n', 0, m.start()) + 1
    indent = text[line_start:m.start()]
    return text[:line_start] + make(indent) + text[m.end():]


def expected(path: str, text: str, kickoffs: list[str] | None = None, version: str | None = None) -> str:
    """The page text with its menu block replaced by nav_html(path) and its analytics
    block by analytics_html(). kickoffs and version (track.js's ?v= stamp): only at
    deploy (build_static.py); the committed pages keep neither."""
    text = _replace(path, text, BLOCK_RE, '<!-- nav:start --> ... <!-- nav:end -->',
                    lambda indent: nav_html(path, indent, kickoffs))
    return _replace(path, text, site_analytics.BLOCK_RE, '<!-- analytics:start --> ... <!-- analytics:end -->',
                    lambda indent: site_analytics.analytics_html(indent, version))


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
