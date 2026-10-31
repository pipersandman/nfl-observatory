"""Names, headings and home layout (#158): one name per topic in the menu and buttons,
search-aware headings computed from the data, no doubled labels, no Key Findings, and
the home sections in menu order."""

import re
from pathlib import Path

import site_nav

ROOT = Path(__file__).resolve().parent.parent
HOME = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
GAMEDAY = (ROOT / 'frontend' / 'gameday' / 'index.html').read_text(encoding='utf-8')
APP_JS = (ROOT / 'frontend' / 'js' / 'app.js').read_text(encoding='utf-8')
LIVESTRIP = (ROOT / 'frontend' / 'js' / 'livestrip.js').read_text(encoding='utf-8')
BUILD = (ROOT / 'scripts' / 'build_static.py').read_text(encoding='utf-8')
UPDATE = (ROOT / 'scripts' / 'update_data.py').read_text(encoding='utf-8')


def home_section_order():
    return re.findall(r'<section id="([a-z]+)"', HOME)


def test_home_sections_follow_the_menu():
    assert home_section_order() == ['season', 'previews', 'referees', 'teams', 'trends']
    menu_topics = [h[2:] for h, _, topic in site_nav.NAV if topic]            # '/#previews' -> 'previews'
    assert [s for s in home_section_order() if s in menu_topics] == menu_topics


def test_full_crew_table_is_inside_crew_chiefs():
    crew = HOME.split('<section id="referees">')[1].split('</section>')[0]
    assert 'id="data"' in crew and 'id="dataTable"' in crew
    assert crew.count('class="see-all"') == 1 and 'See all Crew Chiefs →' in crew


def test_no_doubled_labels():
    for name, text in (('index.html', HOME), ('gameday/index.html', GAMEDAY), ('build_static.py', BUILD)):
        assert 'class="section-number"' not in text, name


def test_key_findings_is_gone():
    assert 'What The Data Shows' not in HOME and 'id="insights"' not in HOME
    assert 'insights.json' not in APP_JS and 'Carousel' not in APP_JS
    assert 'generate_insights' not in UPDATE and 'insights.json' not in UPDATE
    assert not (ROOT / 'frontend' / 'data' / 'insights.json').exists()


def test_see_all_buttons_use_the_menu_names():
    labels = {topic: label for _, label, topic in site_nav.NAV if topic}
    expect = {'/assignments/': labels['/assignments/'], '/crew/': labels['/crew/'], '/team/': labels['/team/'],
              '/trends/': labels['/trends/']}
    found = re.findall(r'<p class="see-all"><a href="([^"]+)">See all (.+?) →</a></p>', HOME)
    assert [(h, n.replace('&amp;', '&')) for h, n in found] == list(expect.items())


def test_menu_labels():
    assert [label for _, label, _ in site_nav.NAV] == [
        'Home', 'Live Games', 'Assignments & Projections', 'Crew Chiefs', 'Team Stats', 'League Trends', 'Guide', 'Data']


def test_old_names_are_gone():
    for old in ('Meet The Officials', 'The Big Picture', 'Team Discipline', 'Flags as they happen',
                'Full<br>scoreboard', 'Gameday scoreboard', '>Referee stats<', "This week\\'s referee assignments",
                'Flag-heaviest crew', 'Cleanest team', 'The Scoreboard', 'Which calls are rising?'):
        for name, text in (('index.html', HOME), ('gameday', GAMEDAY), ('app.js', APP_JS), ('livestrip.js', LIVESTRIP),
                           ('build_static.py', BUILD)):
            assert old not in text, (old, name)


# ---- headings: what people search for, computed, and the page title follows -------------

H1_TITLE = [
    # (H1 source in build_static.py, title source that must start with the same words)
    ('<h1 class="section-title">NFL Referee Stats {SEASON}</h1>', "page('/crew/', f'NFL Referee Stats {SEASON} |"),
    ('<h1 class="section-title">NFL Team Penalty Stats {SEASON}</h1>', "page('/team/', f'NFL Team Penalty Stats {SEASON} |"),
    ('<h1 class="section-title">NFL Penalty Trends {SEASON}</h1>', "page('/trends/', f'NFL Penalty Trends {SEASON} |"),
    ('<h1 class="section-title">NFL Referee Assignments: Week {wk}, {pv_season}</h1>',
     "page('/assignments/', f'NFL Referee Assignments: Week {wk}, {pv_season}'"),
    ('<h1 class="section-title">NFL Penalty Data: CSV Downloads</h1>', "page('/dataset/', 'NFL Penalty Data: CSV Downloads |"),
]


def test_full_page_h1s_and_titles():
    for h1, title in H1_TITLE:
        assert h1 in BUILD, h1
        assert title in BUILD, title


def test_gameday_heading_and_title():
    assert '<h1 class="section-title">Live NFL Penalty Tracker</h1>' in GAMEDAY
    assert '<title>Live NFL Penalty Tracker | NFL Officiating Observatory</title>' in GAMEDAY
    assert "Every accepted penalty in this week's games, updated live during games." in GAMEDAY


def test_home_headings_are_computed():
    # The season and week in home headings come from the data, never typed in
    assert '<h2 class="section-title">NFL Referee Stats <span data-season></span></h2>' in HOME
    assert '<h2 class="section-title">NFL Team Penalty Stats <span data-season></span></h2>' in HOME
    assert "`NFL Penalties Per Game in ${d.currentSeason}`" in APP_JS
    assert "`NFL Referee Assignments: Week ${full.week}`" in APP_JS
    assert "querySelectorAll('[data-season]')" in APP_JS
