"""The one site menu (#153), hub model: scripts/site_nav.py, sync_nav.py, check.py's
"Menus match", the live dot, "See all ->" and the pop-ups' "Full profile ->"."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import check
import site_nav
import sync_nav

ROOT = Path(__file__).resolve().parent.parent
HOME = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
APP_JS = (ROOT / 'frontend' / 'js' / 'app.js').read_text(encoding='utf-8')

LABELS = ['Home', 'Live Games', 'Assignments & Projections', 'Crew chiefs', 'Team Stats', 'Trends', 'Guide', 'Data']
SECTION_ITEMS = {'Assignments & Projections': 'previews', 'Crew chiefs': 'referees', 'Team Stats': 'teams', 'Trends': 'trends'}
PAGE_ITEMS = {'Home': '/', 'Live Games': '/gameday/', 'Guide': '/guide/', 'Data': '/dataset/'}


def items(block):
    """[(href, aria-current or None, label)] of the menu's links."""
    links = block.split('class="nav-links"')[1].split('</div>')[0]
    out = []
    for m in re.finditer(r'<a href="([^"]+)"([^>]*)>(.*?)</a>', links):
        cur = re.search(r'aria-current="([^"]+)"', m.group(2))
        label = re.sub(r'<span class="sr-only[^"]*"[^>]*>.*?</span>|<[^>]+>', '', m.group(3)).replace('&amp;', '&')
        out.append((m.group(1), cur.group(1) if cur else None, label))
    return out


# ---- targets and labels --------------------------------------------------------

def test_labels_and_order():
    assert [label for _, label, _ in site_nav.NAV] == LABELS


def test_topics_go_to_home_sections_and_the_rest_to_pages():
    for href, _, label in items(site_nav.nav_html('/crew/')):
        if label in SECTION_ITEMS:
            assert href == f'/#{SECTION_ITEMS[label]}'
            assert f'id="{SECTION_ITEMS[label]}"' in HOME          # the section exists
        else:
            assert href == PAGE_ITEMS[label] and '#' not in href


@pytest.mark.parametrize('page, expected', [
    ('/', [('Home', 'page')]),
    ('/gameday/', [('Live Games', 'page')]),
    ('/guide/', [('Guide', 'page')]),
    ('/dataset/', [('Data', 'page')]),
    ('/crew/', [('Crew chiefs', 'true')]),
    ('/crew/bill-vinovich/', [('Crew chiefs', 'true')]),
    ('/team/', [('Team Stats', 'true')]),
    ('/team/MIA/', [('Team Stats', 'true')]),
    ('/assignments/', [('Assignments & Projections', 'true')]),
    ('/trends/', [('Trends', 'true')]),
])
def test_highlight_rules(page, expected):
    assert [(label, cur) for _, cur, label in items(site_nav.nav_html(page)) if cur] == expected


def test_screen_readers_hear_live_games_in_progress():
    live = site_nav.nav_html('/crew/').split('class="nav-live"')[1].split('</a>')[0]
    assert 'class="live-dot" aria-hidden="true"' in live
    assert '<span class="sr-only live-sr" hidden>, games in progress</span>' in live


# ---- the committed pages and "Menus match" --------------------------------------

@pytest.mark.parametrize('path', list(sync_nav.PAGES))
def test_committed_pages_have_the_menu(path):
    text = sync_nav.PAGES[path].read_text(encoding='utf-8')
    assert text.count(site_nav.START) == 1 and text.count(site_nav.END) == 1
    assert sync_nav.expected(path, text) == text
    assert 'data-kickoffs=""' in site_nav.menu_block(text)            # filled only at deploy


def test_sync_is_idempotent(tmp_path, monkeypatch):
    page = tmp_path / 'index.html'
    page.write_text('<body>\n    <!-- nav:start -->\n    <!-- nav:end -->\n    <main></main>\n</body>\n', encoding='utf-8')
    monkeypatch.setattr(sync_nav, 'PAGES', {'/': page})
    sync_nav.main()
    once = page.read_text(encoding='utf-8')
    sync_nav.main()
    assert page.read_text(encoding='utf-8') == once
    assert '    <nav class="site-nav"' in once and once.endswith('    <main></main>\n</body>\n')


def test_menus_match_fails_on_a_hand_edit_and_ignores_kickoffs(tmp_path, monkeypatch):
    real = sync_nav.PAGES['/'].read_text(encoding='utf-8')
    page = tmp_path / 'index.html'
    monkeypatch.setattr(sync_nav, 'PAGES', {'/': page})
    page.write_text(real.replace('>Trends</a>', '>Penalty trends</a>', 1), encoding='utf-8')
    assert check.check_menus()[0] is False
    page.write_text(sync_nav.expected('/', real, ['2026-11-01T17:00Z']), encoding='utf-8')   # a deploy copy
    assert check.check_menus()[0] is True
    page.write_text(real, encoding='utf-8')
    assert check.check_menus()[0] is True


def test_menus_match_fails_without_markers(tmp_path, monkeypatch):
    page = tmp_path / 'index.html'
    page.write_text('<body><nav>old menu</nav></body>', encoding='utf-8')
    monkeypatch.setattr(sync_nav, 'PAGES', {'/': page})
    assert check.check_menus()[0] is False


# ---- live dot ----------------------------------------------------------------------

def write_previews(data_dir, games_by_file):
    (data_dir / 'previews').mkdir(parents=True)
    weeks = []
    for name, games in games_by_file.items():
        (data_dir / 'previews' / name).write_text(json.dumps({'games': games}))
        weeks.append({'file': f'previews/{name}'})
    (data_dir / 'previews' / 'latest.json').write_text(json.dumps({'weeks': weeks}))


def test_kickoffs_from_previews_in_utc(tmp_path):
    write_previews(tmp_path, {
        'w8.json': [{'gameday': '2026-10-29', 'gametime': '20:15'},      # EDT: UTC-4
                    {'gameday': '2026-11-01', 'gametime': '13:00'},      # EST from Nov 1: UTC-5
                    {'gameday': '2026-11-01', 'gametime': '13:00'}],     # same kickoff once
        'w9.json': [{'gameday': '2026-11-08', 'gametime': '09:30'}, {'gameday': None}],
    })
    assert site_nav.kickoffs_utc(tmp_path) == ['2026-10-30T00:15Z', '2026-11-01T18:00Z', '2026-11-08T14:30Z']


def test_no_previews_no_kickoffs(tmp_path):
    assert site_nav.kickoffs_utc(tmp_path) == []


def test_deploy_fills_kickoffs_into_the_menu():
    block = site_nav.nav_html('/trends/', kickoffs=['2026-11-01T18:00Z', '2026-11-01T21:05Z'])
    assert 'data-kickoffs="2026-11-01T18:00Z,2026-11-01T21:05Z"' in block


NODE = shutil.which('node')


def live_now(kickoffs_iso, now_iso):
    """Run the menu's own navLiveNow() in Node."""
    js = (site_nav.LIVE_JS + '\nconst k = ' + json.dumps(kickoffs_iso) + '.map(Date.parse);\n'
          + 'process.stdout.write(String(navLiveNow(k, Date.parse(' + json.dumps(now_iso) + '))));')
    return subprocess.run([NODE, '-e', js], capture_output=True, text=True, check=True).stdout == 'true'


@pytest.mark.skipif(not NODE, reason='node not installed')
@pytest.mark.parametrize('now, on', [
    ('2026-11-01T17:59:00Z', False),     # before kickoff
    ('2026-11-01T18:00:00Z', True),      # kickoff
    ('2026-11-01T21:59:00Z', True),      # 3 h 59 min in
    ('2026-11-01T22:01:00Z', False),     # 4 h 1 min in
    ('2026-11-02T01:30:00Z', True),      # the night game's window
    ('2026-11-02T05:30:00Z', False),     # after everything
])
def test_live_dot_window(now, on):
    assert live_now(['2026-11-01T18:00Z', '2026-11-02T01:20Z'], now) is on


@pytest.mark.skipif(not NODE, reason='node not installed')
def test_live_dot_off_without_kickoffs():
    assert live_now([], '2026-11-01T18:30:00Z') is False


def test_dot_respects_reduced_motion():
    css = (ROOT / 'frontend' / 'css' / 'styles.css').read_text(encoding='utf-8')
    assert re.search(r'@media \(prefers-reduced-motion: reduce\) \{ \.nav-live\.is-live \.live-dot \{ animation: none; \} \}', css)


# ---- home sections, See all, pop-ups ---------------------------------------------------

def test_home_sections_keep_their_ids_and_see_all_links():
    for sid in ('season', 'teams', 'previews', 'trends', 'referees', 'data', 'insights'):
        assert f'id="{sid}"' in HOME
    see_all = re.findall(r'<p class="see-all"><a href="([^"]+)"', HOME)
    # Data's table is "Complete Crew Chief Stats", so its full page is /crew/ (Ty, 2026-10-31)
    assert see_all == ['/team/', '/assignments/', '/trends/', '/crew/', '/crew/']
    assert 'section-tiles' not in HOME                                    # removed (hub model)


def test_section_headings_match_the_menu():
    assert '02 / TEAM STATS' in HOME and '<h2 class="section-title">Team Stats</h2>' in HOME
    assert '03 / ASSIGNMENTS &amp; PROJECTIONS' in HOME
    assert 'id="previewsTitle">Assignments &amp; Projections</h2>' in HOME
    assert "previewsTitle').textContent" not in APP_JS                   # week text moved to the subtitle


def function_body(name):
    m = re.search(rf'(?:async )?function {name}\(.*?\n}}\n', APP_JS, re.S)
    assert m, name
    return m.group(0)


def test_crew_and_team_popups_link_to_their_full_page():
    assert 'id="modalProfileLink"' in HOME and 'Full profile →' in HOME
    assert 'setProfileLink(`/crew/${encodeURIComponent(slug)}/`)' in function_body('openRefereeModal')
    assert 'setProfileLink(`/team/${encodeURIComponent(t.abbr)}/`)' in function_body('renderTeamProfile')
    for other in ('openPreviewModal', 'openScorecardModal', 'closeModal'):
        assert 'setProfileLink(null)' in function_body(other)
