"""The site menu: one list, the same markup on every page (#153).

Standard library only. Used by:
- build_static.py: every pre-rendered page, plus the deploy copies of the home page
  and /gameday/ (it fills in this week's kickoff times for the live dot)
- sync_nav.py: writes the menu into the two hand-written pages, frontend/index.html
  and frontend/gameday/index.html, between <!-- nav:start --> and <!-- nav:end -->
- check.py ("Menus match"): fails if either hand-written page's menu differs

Hub model (Ty, 2026-10-31): a topic with a home section goes to that section from
every page (/#teams scrolls on the home page and opens it elsewhere); its full page
is reached from the section's "See all ->". Live Games, Guide and Data are pages.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

# (href, label, topic pages). Order as before; labels per Ty, 2026-10-31. A topic's own
# pages (e.g. /crew/ and /crew/<slug>/) mark its item aria-current="true".
NAV = [
    ('/', 'Home', None),
    ('/gameday/', 'Live Games', None),
    ('/#previews', 'Assignments & Projections', '/assignments/'),
    ('/#referees', 'Crew chiefs', '/crew/'),
    ('/#teams', 'Team Stats', '/team/'),
    ('/#trends', 'Trends', '/trends/'),
    ('/guide/', 'Guide', None),
    ('/dataset/', 'Data', None),
]
LIVE_HREF = '/gameday/'
LIVE_HOURS = 4          # the dot shows from kickoff to this many hours after

START, END = '<!-- nav:start -->', '<!-- nav:end -->'
BLOCK_RE = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.S)
KICKOFFS_RE = re.compile(r'data-kickoffs="[^"]*"')

X_ICON = ('<svg class="x-logo" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.244 2.25h3.308l-7.227 '
          '8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 '
          '4.126H5.117z"/></svg>')

# True while any game is in progress: from kickoff to LIVE_HOURS after. kickoffs are
# epoch milliseconds. Pure, so tests run it in Node with fake times.
LIVE_JS = f"""function navLiveNow(kickoffs, now) {{
        return kickoffs.some(k => now >= k && now < k + {LIVE_HOURS} * 3600 * 1000);
    }}"""

# ☰ menu (open/close up to 1240px wide, matching styles.css) and the live dot. Inline, so it works on pages
# that load no other script; no network request.
MENU_JS = """<script>(() => {
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
    window.addEventListener('resize', () => { if (window.innerWidth > 1240) setOpen(false); });

    // Live dot: this week's kickoffs are written into the menu at deploy (no request)
    """ + LIVE_JS + """
    const live = nav.querySelector('.nav-live');
    const kickoffs = (nav.dataset.kickoffs || '').split(',').map(Date.parse).filter(Number.isFinite);
    const update = () => {
        const on = !!live && navLiveNow(kickoffs, Date.now());
        if (!live) return;
        live.classList.toggle('is-live', on);
        live.querySelector('.live-sr').hidden = !on;
    };
    update();
    if (kickoffs.length) setInterval(update, 60 * 1000);
})();</script>"""


def _item(href, label, topic, current):
    if href == current:
        cur = ' aria-current="page"'
    elif topic and current.startswith(topic):
        cur = ' aria-current="true"'
    else:
        cur = ''
    if href == LIVE_HREF:
        return (f'<a href="{href}" class="nav-live"{cur}><span class="live-dot" aria-hidden="true"></span>{escape(label)}'
                f'<span class="sr-only live-sr" hidden>, games in progress</span></a>')
    return f'<a href="{href}"{cur}>{escape(label)}</a>'


def nav_html(current: str, indent: str = '    ', kickoffs: list[str] | None = None) -> str:
    """The menu block for the page at path `current` (e.g. '/', '/crew/'), with its
    markers. kickoffs: UTC ISO times for the live dot (filled at deploy; empty in the
    committed pages)."""
    links = ''.join(_item(h, label, topic, current) for h, label, topic in NAV)
    lines = [
        START,
        f'<nav class="site-nav" id="siteNav" aria-label="Site" data-kickoffs="{escape(",".join(kickoffs or []))}">',
        '    <a class="logo" href="/"><img src="/favicon.svg" alt="" class="logo-mark">NFL Officiating Observatory</a>',
        '    <button class="nav-toggle" id="navToggle" type="button" aria-label="Open menu" aria-expanded="false" '
        'aria-controls="navLinks"><span></span><span></span><span></span></button>',
        f'    <div class="nav-links" id="navLinks">{links}</div>',
        '    <a class="nav-x" href="https://x.com/NFLObservatory" target="_blank" rel="noopener" '
        'aria-label="Follow @NFLObservatory on X" title="Follow @NFLObservatory on X">' + X_ICON + '<span>Follow</span></a>',
        '</nav>',
        *MENU_JS.splitlines(),
        END,
    ]
    return '\n'.join(indent + ln if ln else ln for ln in lines)


def menu_block(text: str) -> str | None:
    """The menu block (markers included) in a page's text, or None."""
    m = BLOCK_RE.search(text)
    return m.group(0) if m else None


def without_kickoffs(text: str) -> str:
    """Text with the menu's kickoff list emptied (it changes every week at deploy)."""
    return KICKOFFS_RE.sub('data-kickoffs=""', text)


def kickoffs_utc(data_dir: Path) -> list[str]:
    """This week's kickoffs as UTC ISO strings ('2026-11-01T17:00Z'), from the preview
    files previews/latest.json lists (the rest of this week plus next week). Schedule
    times are US Eastern; daylight saving is handled. Regular season only: the preview
    files don't cover playoff games yet (#153 notes)."""
    from zoneinfo import ZoneInfo
    et = ZoneInfo('America/New_York')
    try:
        latest = json.loads((data_dir / 'previews' / 'latest.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    files = [w['file'] for w in latest.get('weeks', []) if w.get('file')] or ([latest['file']] if latest.get('file') else [])
    out = set()
    for f in files:
        try:
            games = json.loads((data_dir / f).read_text(encoding='utf-8')).get('games', [])
        except (OSError, ValueError):
            continue
        for g in games:
            day, time = g.get('gameday'), g.get('gametime') or '00:00'
            try:
                t = datetime.fromisoformat(f'{day} {time}').replace(tzinfo=et).astimezone(timezone.utc)
            except (TypeError, ValueError):
                continue
            out.add(t.strftime('%Y-%m-%dT%H:%MZ'))
    return sorted(out)


def live_window(kickoff_iso: str) -> tuple[datetime, datetime]:
    """(start, end) of the live dot for one kickoff, for tests and docs."""
    t = datetime.strptime(kickoff_iso, '%Y-%m-%dT%H:%MZ').replace(tzinfo=timezone.utc)
    return t, t + timedelta(hours=LIVE_HOURS)
