"""Analytics (#165, #179): the shared snippet (scripts/site_analytics.py) on every page,
PostHog's cookieless settings in frontend/js/track.js, the security policy, and every
track() event name listed in docs/ANALYTICS.md."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import build_static
import check
import site_analytics as sa
import sync_nav

ROOT = Path(__file__).resolve().parent.parent
TRACK_JS = (ROOT / 'frontend' / 'js' / 'track.js').read_text(encoding='utf-8')
DOC = (ROOT / 'docs' / 'ANALYTICS.md').read_text(encoding='utf-8')
NODE = shutil.which('node')


def assert_snippet_once(text):
    assert text.count(sa.START) == 1 and text.count(sa.END) == 1
    assert text.count(sa.POSTHOG_SRC) == 1
    assert text.count('static.cloudflareinsights.com/beacon.min.js') == 1
    assert len(re.findall(r'src="/js/track\.js(\?v=[^"]*)?"', text)) == 1
    head = text.split('</head>')[0]
    assert sa.START in head                       # in <head>, before the page's own scripts


# ---- the snippet on every page -----------------------------------------------------

@pytest.mark.parametrize('path', list(sync_nav.PAGES))
def test_hand_written_pages_have_the_snippet_once(path):
    text = sync_nav.PAGES[path].read_text(encoding='utf-8')
    assert_snippet_once(text)
    assert sync_nav.expected(path, text) == text


def test_every_pre_built_page_has_the_snippet(tmp_path, monkeypatch):
    """Every pre-built page comes from build_static.page(), the one page template."""
    src = (ROOT / 'scripts' / 'build_static.py').read_text(encoding='utf-8')
    assert src.count('<head>') == 1
    monkeypatch.setattr(build_static, 'ROOT', tmp_path)
    monkeypatch.setattr(build_static, 'V', 'abc12345')
    monkeypatch.setattr(build_static, 'NOW', type('Now', (), {'strftime': lambda self, f: 'November 1, 2026'})())
    monkeypatch.setattr(build_static, 'SITEMAP', [])
    build_static.page('/crew/test-crew/', 'Title', 'Description', '<p>body</p>')
    text = (tmp_path / 'crew' / 'test-crew' / 'index.html').read_text(encoding='utf-8')
    assert_snippet_once(text)
    assert 'src="/js/track.js?v=abc12345"' in text
    assert 'privacy' not in text.lower()          # no privacy text on the site yet (Ty, 2026-10-31)


def test_deploy_copy_is_stamped_and_still_matches(tmp_path, monkeypatch):
    real = sync_nav.PAGES['/gameday/'].read_text(encoding='utf-8')
    deploy = sync_nav.expected('/gameday/', real, ['2026-11-01T17:00Z'], 'abc12345')
    assert 'src="/js/track.js?v=abc12345"' in deploy
    page = tmp_path / 'index.html'
    monkeypatch.setattr(sync_nav, 'PAGES', {'/gameday/': page})
    page.write_text(deploy, encoding='utf-8')
    assert check.check_menus()[0] is True


def test_drift_in_the_snippet_fails_menus_match(tmp_path, monkeypatch):
    real = sync_nav.PAGES['/'].read_text(encoding='utf-8')
    page = tmp_path / 'index.html'
    monkeypatch.setattr(sync_nav, 'PAGES', {'/': page})
    page.write_text(real.replace(sa.POSTHOG_VERSION, '1.0.0', 1), encoding='utf-8')
    assert check.check_menus()[0] is False


def test_posthog_is_pinned_with_integrity():
    block = sa.analytics_html()
    assert re.fullmatch(r'\d+\.\d+\.\d+', sa.POSTHOG_VERSION)
    assert f'posthog-js@{sa.POSTHOG_VERSION}/dist/array.no-external.js' in block
    assert f'integrity="{sa.POSTHOG_SRI}"' in block and sa.POSTHOG_SRI.startswith('sha384-')


# ---- cookieless, events only ---------------------------------------------------------

@pytest.mark.parametrize('setting', [
    "api_host: 'https://us.i.posthog.com'",
    "persistence: 'memory'",
    'disable_session_recording: true',
    'autocapture: false',
    'capture_pageview: true',
    'respect_dnt: true',
    'capture_heatmaps: false',
    'advanced_disable_flags: true',
])
def test_track_js_settings(setting):
    assert setting in TRACK_JS


def test_security_policy_allows_the_analytics_hosts():
    csp = next(ln for ln in (ROOT / 'frontend' / '.htaccess').read_text(encoding='utf-8').splitlines()
               if 'Content-Security-Policy' in ln)
    script_src = re.search(r'script-src ([^;]*)', csp).group(1)
    connect_src = re.search(r'connect-src ([^;]*)', csp).group(1)
    assert 'https://cdn.jsdelivr.net' in script_src and 'https://static.cloudflareinsights.com' in script_src
    for host in ('https://us.i.posthog.com', 'https://us-assets.i.posthog.com', 'https://cloudflareinsights.com'):
        assert host in connect_src


# ---- event names -----------------------------------------------------------------------

def documented_events():
    section = DOC.split('## Events')[1]
    return set(re.findall(r'^\| `([a-z_]+)` \|', section, re.M))


def used_events():
    names = set()
    for f in (ROOT / 'frontend' / 'js').glob('*.js'):
        names |= set(re.findall(r"\btrack(?:\?\.)?\(\s*'([^']+)'", f.read_text(encoding='utf-8')))
    return names


def test_every_event_is_documented_and_every_documented_event_is_used():
    assert used_events() == documented_events()
    assert all(re.fullmatch(r'[a-z]+(_[a-z]+)+', n) for n in used_events())   # object_action


# ---- track.js behaviour, run in Node ---------------------------------------------------

def run_track(host='nflobservatory.com', with_posthog=True):
    """Run track.js with a fake page and a fake PostHog. Returns what PostHog got."""
    js = """
const out = { init: null, captured: [], logged: [] };
globalThis.window = globalThis;
globalThis.location = { hostname: HOST, host: HOST, pathname: '/gameday/', href: 'https://' + HOST + '/gameday/' };
globalThis.document = { addEventListener() {}, querySelectorAll() { return []; } };
globalThis.console = { debug: (tag, name, props) => out.logged.push([name, props]) };
if (WITH_PH) window.posthog = { init(k, c) { out.init = { key: k, config: c }; }, capture(n, p) { out.captured.push([n, p]); } };
window.__trackQ = [['early_event', { a: 1 }]];
TRACK_JS
track('later_event', { b: 2 });
process.stdout.write(JSON.stringify({ ...out, queueLeft: window.__trackQ.length }));
"""
    js = (js.replace('HOST', json.dumps(host)).replace('WITH_PH', 'true' if with_posthog else 'false')
          .replace('TRACK_JS', TRACK_JS))
    r = subprocess.run([NODE, '-e', js], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@pytest.mark.skipif(not NODE, reason='node not installed')
def test_queued_calls_are_sent_in_order_with_cookieless_settings():
    out = run_track()
    assert out['init']['key'].startswith('phc_')
    cfg = out['init']['config']
    assert cfg['persistence'] == 'memory' and cfg['autocapture'] is False and cfg['disable_session_recording'] is True
    assert out['captured'] == [['early_event', {'a': 1}], ['later_event', {'b': 2}]]
    assert out['queueLeft'] == 0


@pytest.mark.skipif(not NODE, reason='node not installed')
def test_blocked_posthog_does_nothing_and_never_throws():
    out = run_track(with_posthog=False)
    assert out['init'] is None and out['captured'] == [] and out['queueLeft'] == 0


@pytest.mark.skipif(not NODE, reason='node not installed')
def test_localhost_sends_nothing_and_logs_instead():
    out = run_track(host='localhost')
    assert out['init'] is None and out['captured'] == []
    assert out['logged'] == [['early_event', {'a': 1}], ['later_event', {'b': 2}]]
