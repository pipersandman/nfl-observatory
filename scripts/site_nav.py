"""The site menu: one list, the same markup on every page (#153).

Standard library only. Used by:
- build_static.py: every pre-rendered page (/crew/, /team/, /trends/, ...)
- sync_nav.py: writes the menu into the two hand-written pages, frontend/index.html
  and frontend/gameday/index.html, between <!-- nav:start --> and <!-- nav:end -->
- check.py ("Menus match"): fails if either hand-written page's menu differs

Every item goes to a real page. The home page's sections keep their #ids, so
old links like /#trends still work; the menu just doesn't use them.
"""

import re
from html import escape

# Labels and order as the static pages had them (Ty, 2026-10-31). V2.1 regroups
# these into its six sections (plan section 14).
NAV = [('/', 'Home'), ('/gameday/', 'Gameday'), ('/assignments/', 'This week'), ('/crew/', 'Crew chiefs'), ('/team/', 'Teams'),
       ('/trends/', 'Trends'), ('/guide/', 'Guide'), ('/dataset/', 'Data')]

START, END = '<!-- nav:start -->', '<!-- nav:end -->'
CURRENT = ' aria-current="page"'
BLOCK_RE = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.S)

X_ICON = ('<svg class="x-logo" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.244 2.25h3.308l-7.227 '
          '8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 '
          '4.126H5.117z"/></svg>')

# Phone menu: the button opens and closes the links (below 768px wide). Inline, so it
# works on pages that load no other script.
TOGGLE_JS = """<script>(() => {
    const nav = document.getElementById('siteNav'), toggle = document.getElementById('navToggle');
    if (!nav || !toggle) return;
    const setOpen = (open) => {
        nav.classList.toggle('nav-open', open);
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    };
    toggle.addEventListener('click', (e) => { e.stopPropagation(); setOpen(!nav.classList.contains('nav-open')); });
    nav.querySelectorAll('.nav-links a').forEach(a => a.addEventListener('click', () => setOpen(false)));
    document.addEventListener('click', (e) => { if (!nav.contains(e.target)) setOpen(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
    window.addEventListener('resize', () => { if (window.innerWidth > 768) setOpen(false); });
})();</script>"""


def nav_html(current: str, indent: str = '    ') -> str:
    """The menu block for the page at path `current` (e.g. '/', '/crew/'), with its
    markers. The item for the current page (or its section, e.g. /crew/<slug>/ ->
    Crew chiefs) is marked aria-current="page"."""
    def is_current(path):
        return current == path or (path != '/' and current.startswith(path))
    links = ''.join(f'<a href="{p}"{CURRENT if is_current(p) else ""}>{escape(label)}</a>' for p, label in NAV)
    lines = [
        START,
        '<nav class="site-nav" id="siteNav" aria-label="Site">',
        '    <a class="logo" href="/"><img src="/favicon.svg" alt="" class="logo-mark">NFL Officiating Observatory</a>',
        '    <button class="nav-toggle" id="navToggle" type="button" aria-label="Open menu" aria-expanded="false" '
        'aria-controls="navLinks"><span></span><span></span><span></span></button>',
        f'    <div class="nav-links" id="navLinks">{links}</div>',
        '    <a class="nav-x" href="https://x.com/NFLObservatory" target="_blank" rel="noopener" '
        'aria-label="Follow @NFLObservatory on X" title="Follow @NFLObservatory on X">' + X_ICON + '<span>Follow</span></a>',
        '</nav>',
        *TOGGLE_JS.splitlines(),
        END,
    ]
    return '\n'.join(indent + ln if ln else ln for ln in lines)


def menu_block(text: str) -> str | None:
    """The menu block (markers included) in a page's text, or None."""
    m = BLOCK_RE.search(text)
    return m.group(0) if m else None
