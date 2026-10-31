"""The analytics snippet: one block, the same on every page (#165, #179).

Standard library only. Used like the site menu (site_nav.py):
- build_static.py: in every pre-rendered page's <head>, and in the deploy copies of
  the home page and /gameday/ (with the deploy's ?v= stamp on track.js)
- sync_nav.py: writes it into frontend/index.html and frontend/gameday/index.html,
  between <!-- analytics:start --> and <!-- analytics:end -->
- check.py ("Menus match"): fails if either hand-written page's block differs

What it loads:
- Cloudflare Web Analytics (D18): page views, cookieless. Token is public by design.
- PostHog (D21), US cloud: the pinned no-external build (it never loads other
  scripts), with a Subresource Integrity hash. Set up in frontend/js/track.js:
  cookieless, events only, no session replay, no autocapture.
- frontend/js/track.js: the track() helper. A one-line stub before it queues
  track() calls made before the deferred scripts run (app.js isn't deferred).
"""

import re
from html import escape

POSTHOG_VERSION = '1.438.12'      # published 2026-10-15; bump with a new integrity hash
POSTHOG_SRC = f'https://cdn.jsdelivr.net/npm/posthog-js@{POSTHOG_VERSION}/dist/array.no-external.js'
POSTHOG_SRI = 'sha384-+Lkmn19DYonVgUwLkn6wB27C9VRu21N4rIsR+Y5JGqhmp6JLZKAzUV0uUwgMMdiY'
CF_BEACON_TOKEN = '77bd1d7e32bb4f60ad87189467fae090'
TRACK_SRC = '/js/track.js'

START, END = '<!-- analytics:start -->', '<!-- analytics:end -->'
BLOCK_RE = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.S)
STAMP_RE = re.compile(re.escape(TRACK_SRC) + r'\?v=[^"]*')

STUB_JS = ('<script>window.track = window.track || function (n, p, o) '
           '{ (window.__trackQ = window.__trackQ || []).push([n, p, o]); };</script>')


def analytics_html(indent: str = '    ', version: str | None = None) -> str:
    """The analytics block with its markers. version: the deploy's ?v= stamp for
    track.js (build_static.py); the committed pages have none."""
    track = TRACK_SRC + (f'?v={escape(version)}' if version else '')
    lines = [
        START,
        STUB_JS,
        f'<script src="{POSTHOG_SRC}" integrity="{POSTHOG_SRI}" crossorigin="anonymous" defer></script>',
        f'<script src="{track}" defer></script>',
        "<script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
        f"""data-cf-beacon='{{"token": "{CF_BEACON_TOKEN}"}}'></script>""",
        END,
    ]
    return '\n'.join(indent + ln for ln in lines)


def without_stamp(text: str) -> str:
    """Text with track.js's ?v= stamp removed (it changes every deploy)."""
    return STAMP_RE.sub(TRACK_SRC, text)
