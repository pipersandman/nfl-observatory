"""The one site menu (#153): scripts/site_nav.py, sync_nav.py and check.py's
"Menus match"."""

import re
from pathlib import Path

import pytest

import check
import site_nav
import sync_nav

ROOT = Path(__file__).resolve().parent.parent
LABELS = ['Home', 'Gameday', 'This week', 'Crew chiefs', 'Teams', 'Trends', 'Guide', 'Data']


def links(block):
    return re.findall(r'<a href="([^"]+)"( aria-current="page")?>([^<]+)</a>', block.split('nav-links')[1].split('</div>')[0])


def test_labels_and_order_unchanged():
    assert [label for _, label in site_nav.NAV] == LABELS


@pytest.mark.parametrize('page', ['/', '/gameday/', '/assignments/', '/crew/', '/team/', '/trends/', '/guide/', '/dataset/'])
def test_every_item_is_a_real_page_and_one_is_current(page):
    found = links(site_nav.nav_html(page))
    assert [label for _, _, label in found] == LABELS
    assert all(href.startswith('/') and '#' not in href for href, _, _ in found)
    assert [href for href, cur, _ in found if cur] == [page]


@pytest.mark.parametrize('page, current', [('/crew/bill-vinovich/', '/crew/'), ('/team/MIA/', '/team/')])
def test_detail_pages_mark_their_section(page, current):
    assert [href for href, cur, _ in links(site_nav.nav_html(page)) if cur] == [current]


def test_phone_menu_button_and_script_are_in_the_block():
    block = site_nav.nav_html('/crew/')
    assert 'id="navToggle"' in block and 'aria-controls="navLinks"' in block
    assert "document.getElementById('siteNav')" in block and block.count('<script>') == 1
    assert block.strip().startswith(site_nav.START) and block.strip().endswith(site_nav.END)


@pytest.mark.parametrize('path', list(sync_nav.PAGES))
def test_committed_pages_have_the_menu(path):
    text = sync_nav.PAGES[path].read_text(encoding='utf-8')
    assert text.count(site_nav.START) == 1 and text.count(site_nav.END) == 1
    assert sync_nav.expected(path, text) == text            # in step with NAV
    assert [href for href, cur, _ in links(site_nav.menu_block(text)) if cur] == [path]


def test_sync_is_idempotent(tmp_path, monkeypatch):
    page = tmp_path / 'index.html'
    page.write_text('<body>\n    <!-- nav:start -->\n    <!-- nav:end -->\n    <main></main>\n</body>\n', encoding='utf-8')
    monkeypatch.setattr(sync_nav, 'PAGES', {'/': page})
    sync_nav.main()
    once = page.read_text(encoding='utf-8')
    sync_nav.main()
    assert page.read_text(encoding='utf-8') == once
    assert '    <nav class="site-nav"' in once and once.endswith('    <main></main>\n</body>\n')


def test_menus_match_check_fails_on_a_hand_edit(tmp_path, monkeypatch):
    real = sync_nav.PAGES['/'].read_text(encoding='utf-8')
    page = tmp_path / 'index.html'
    page.write_text(real.replace('>Trends</a>', '>Penalty trends</a>', 1), encoding='utf-8')
    monkeypatch.setattr(sync_nav, 'PAGES', {'/': page})
    ok, _ = check.check_menus()
    assert ok is False
    page.write_text(real, encoding='utf-8')
    assert check.check_menus()[0] is True


def test_menus_match_check_fails_without_markers(tmp_path, monkeypatch):
    page = tmp_path / 'index.html'
    page.write_text('<body><nav>old menu</nav></body>', encoding='utf-8')
    monkeypatch.setattr(sync_nav, 'PAGES', {'/': page})
    assert check.check_menus()[0] is False


def test_home_sections_keep_their_ids_and_see_all_links():
    home = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
    for sid in ('season', 'teams', 'previews', 'trends', 'referees', 'data', 'insights'):
        assert f'id="{sid}"' in home                          # old /#section links still land
    see_all = re.findall(r'<p class="see-all"><a href="([^"]+)"', home)
    # Data's table is "Complete Crew Chief Stats", so its full page is /crew/ (Ty, 2026-10-31)
    assert see_all == ['/team/', '/assignments/', '/trends/', '/crew/', '/crew/']
    assert 'href="#' not in site_nav.menu_block(home)


def test_section_tiles_jump_to_every_home_section():
    home = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
    block = home.split('class="section-tiles"')[1].split('</div>')[0]
    tiles = re.findall(r'<a href="#([a-z]+)">([^<]+)</a>', block)
    assert tiles == [('season', 'This Season'), ('insights', 'Findings'), ('teams', 'Teams'), ('previews', 'Upcoming Games'),
                     ('trends', 'Trends'), ('referees', 'Crew Chiefs'), ('data', 'Data')]
    assert all(f'id="{sid}"' in home for sid, _ in tiles)
    assert home.index('class="section-tiles"') < home.index('id="season"')     # at the top, before the first section
