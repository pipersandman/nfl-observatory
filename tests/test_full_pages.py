"""Full pages are supersets of their home sections (#166): scripts/full_pages.py,
check.py's "Full pages", and /crew/ as built by build_static.py."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

import build_static as bs
import check
import full_pages as fp

ROOT = Path(__file__).resolve().parent.parent
HOME = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')


class Now(datetime):
    """The build's clock; '%-d' (Linux only) works on Windows too."""

    def strftime(self, fmt):
        return super().strftime(fmt.replace('%-d', str(self.day)))


# ---- finding a block by id ------------------------------------------------------------

def test_element_by_id_matches_nested_tags():
    text = '<div id="a"><div class="x"><div>in</div></div><img src="i.png"><p>p</p></div><div id="b"></div>'
    assert fp.element_by_id(text, 'a') == '<div id="a"><div class="x"><div>in</div></div><img src="i.png"><p>p</p></div>'
    assert fp.element_by_id(text, 'b') == '<div id="b"></div>'
    with pytest.raises(ValueError):
        fp.element_by_id(text, 'missing')


def test_home_blocks_are_the_template_not_the_summary_fill():
    grid = bs.home_block('refereeGrid')
    assert grid.startswith('<div class="referee-grid fade-in" id="refereeGrid">') and grid.endswith('</div>')
    assert '<!-- SEO:REFEREES --><div class="loading">' in grid      # the spinner, not pre-filled cards
    assert '<table>' in bs.home_block('data') and "openExplainer('home-bias')" in bs.home_block('data')


# ---- the superset rule ------------------------------------------------------------------

def test_check_passes_and_lists_the_pending_pages(capsys):
    ok, note = check.check_full_pages()
    assert ok, capsys.readouterr().out
    assert note.startswith('2 done (/crew/, /team/), 2 pending')
    assert 'pending: /assignments/ (#167), /trends/ (#169)' in capsys.readouterr().out


def test_every_see_all_goes_to_a_full_page():
    targets = fp.see_all_targets(HOME)
    assert sorted(targets) == sorted(fp.FULL_PAGES)


def test_leaving_out_a_block_fails():
    spec = {**fp.FULL_PAGES['/crew/'], 'blocks': ['refereeGrid']}
    problems = fp.section_problems(HOME, '/crew/', spec)
    assert any('id="data"' in p for p in problems) and any('id="dataTable"' in p for p in problems)


def test_leaving_out_the_header_explainer_fails():
    spec = {**fp.FULL_PAGES['/crew/'], 'explainers': []}
    assert fp.section_problems(HOME, '/crew/', spec) == [
        "/crew/: explainer 'crew-chief' in #referees is not on the page (add it to FULL_PAGES explainers)"]


def test_a_new_see_all_link_must_be_listed(tmp_path, monkeypatch):
    fake_root = tmp_path
    (fake_root / 'frontend').mkdir()
    (fake_root / 'frontend' / 'index.html').write_text(
        HOME.replace('<p class="see-all"><a href="/crew/">', '<p class="see-all"><a href="/officials/">'), encoding='utf-8')
    monkeypatch.setattr(check, 'ROOT', fake_root)
    monkeypatch.syspath_prepend(str(ROOT / 'scripts'))
    assert check.check_full_pages()[0] is False


# ---- /crew/ as built ----------------------------------------------------------------------

@pytest.fixture
def built(tmp_path, monkeypatch):
    monkeypatch.setattr(bs, 'ROOT', tmp_path)
    monkeypatch.setattr(bs, 'V', 'abc12345')
    monkeypatch.setattr(bs, 'NOW', Now(2026, 11, 1, 12, tzinfo=timezone.utc))
    monkeypatch.setattr(bs, 'SITEMAP', [])
    bs.crew_pages()
    bs.team_pages()
    return tmp_path


def test_crew_page_has_every_block_once_in_order(built):
    text = (built / 'crew' / 'index.html').read_text(encoding='utf-8')
    for i in fp.FULL_PAGES['/crew/']['blocks'] + fp.SHELLS:
        assert text.count(f'id="{i}"') == 1, i
    h1 = text.index('<h1')
    tldr = text.index('st-tldr')
    grid = text.index('id="refereeGrid"')
    data = text.index('id="data"')
    heading = text.index(f'<h2>{bs.SEASON} Crew Chief Stats This Season</h2>')
    written = text.index('<table class="pv-table st-table')
    assert h1 < tldr < grid < data < heading < written
    assert text.count('class="st-app"') == 1


def test_crew_page_loads_the_home_code_and_nothing_else(built):
    text = (built / 'crew' / 'index.html').read_text(encoding='utf-8')
    assert text.count(bs.CHART_TAG) == 1 and 'integrity="sha384-' in bs.CHART_TAG
    assert text.count('<script src="/js/app.js?v=abc12345"></script>') == 1
    assert 'livestrip.js' not in text


def test_crew_page_has_the_explainer_and_no_home_page_button(built):
    text = (built / 'crew' / 'index.html').read_text(encoding='utf-8')
    for key in fp.FULL_PAGES['/crew/']['explainers']:
        assert f"openExplainer('{key}')" in text.split('id="refereeGrid"')[0]   # in the page's own header
    assert 'on the home page' not in text and 'href="/#referees"' not in text.split('</nav>')[1]


def test_pages_without_blocks_stay_static(built):
    text = (built / 'crew' / 'bill-vinovich' / 'index.html').read_text(encoding='utf-8')
    assert 'app.js' not in text and 'chart.umd.js' not in text and 'class="st-app"' not in text


def test_blocks_need_a_place_in_the_body(tmp_path, monkeypatch):
    monkeypatch.setattr(bs, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='no <!-- full-page blocks -->'):
        bs.page('/x/', 'T', 'D', '<p>no place</p>', blocks=['refereeGrid'])


def test_app_reads_data_from_the_site_root():
    app = (ROOT / 'frontend' / 'js' / 'app.js').read_text(encoding='utf-8')
    assert "dataPath: '/data'" in app


# ---- /team/ (#168) ------------------------------------------------------------------------

def test_team_page_order_ranking_then_divisions_then_note(built):
    text = (built / 'team' / 'index.html').read_text(encoding='utf-8')
    for i in fp.FULL_PAGES['/team/']['blocks'] + fp.SHELLS:
        assert text.count(f'id="{i}"') == 1, i
    h1 = text.index('<h1')
    tldr = text.index('st-tldr')
    ranking = text.index('<table class="pv-table st-table')
    heading = text.index(f'<h2>NFL Team Penalties by Division {bs.SEASON}</h2>')
    picker = text.index('id="divisionGrid"')
    cards = text.index('id="divisionTeams"')
    note = text.index('Accepted penalties on each team')
    assert h1 < tldr < ranking < heading < picker < cards < note


def test_team_page_loads_the_home_code_and_has_no_home_page_button(built):
    text = (built / 'team' / 'index.html').read_text(encoding='utf-8')
    assert text.count(bs.CHART_TAG) == 1
    assert text.count('<script src="/js/app.js?v=abc12345"></script>') == 1
    assert 'livestrip.js' not in text
    assert 'on the home page' not in text and 'href="/#teams"' not in text.split('</nav>')[1]


def test_team_profile_pages_stay_static(built):
    text = (built / 'team' / 'MIA' / 'index.html').read_text(encoding='utf-8')
    assert 'app.js' not in text and 'class="st-app"' not in text
