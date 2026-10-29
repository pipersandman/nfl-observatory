"""
Static, crawlable pages for search engines and AI assistants
============================================================
The site itself is a JavaScript app: numbers appear after the page loads, which
most crawlers (and every LLM scraper) never see. This script pre-renders the key
facts into plain HTML from the weekly data files:

  /crew/                 every active crew chief, with links
  /crew/<slug>/          one page per crew chief   (ProfilePage + Person schema)
  /team/                 all 32 teams
  /team/<abbr>/          one page per team         (WebPage about SportsTeam)
  /assignments/          this week's games and crew chiefs
  /trends/               league trends in words and tables
  /dataset/              downloadable CSVs         (Dataset schema)
  /guide/                methodology, glossary, FAQ (FAQPage schema)
  sitemap.xml, llms.txt, data/exports/*.csv
  index.html             the "This week in NFL officiating" summary block

Run after update_data.py (the deploy workflow does this). Output is generated, not
committed (see .gitignore). Pages use the site's own styles plus css/static.css.
"""
import csv
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import weeks
from weeks import HISTORICAL_START

ROOT = Path(__file__).resolve().parent.parent / 'frontend'
DATA = ROOT / 'data'
SITE = 'https://nflobservatory.com'
V = (os.environ.get('GITHUB_SHA') or 'local')[:8]
NOW = datetime.now(timezone.utc)
TODAY = NOW.strftime('%Y-%m-%d')

TEAM_NAMES = {
    'ARI': 'Arizona Cardinals', 'ATL': 'Atlanta Falcons', 'BAL': 'Baltimore Ravens', 'BUF': 'Buffalo Bills',
    'CAR': 'Carolina Panthers', 'CHI': 'Chicago Bears', 'CIN': 'Cincinnati Bengals', 'CLE': 'Cleveland Browns',
    'DAL': 'Dallas Cowboys', 'DEN': 'Denver Broncos', 'DET': 'Detroit Lions', 'GB': 'Green Bay Packers',
    'HOU': 'Houston Texans', 'IND': 'Indianapolis Colts', 'JAX': 'Jacksonville Jaguars', 'KC': 'Kansas City Chiefs',
    'LA': 'Los Angeles Rams', 'LAC': 'Los Angeles Chargers', 'LV': 'Las Vegas Raiders', 'MIA': 'Miami Dolphins',
    'MIN': 'Minnesota Vikings', 'NE': 'New England Patriots', 'NO': 'New Orleans Saints', 'NYG': 'New York Giants',
    'NYJ': 'New York Jets', 'PHI': 'Philadelphia Eagles', 'PIT': 'Pittsburgh Steelers', 'SEA': 'Seattle Seahawks',
    'SF': 'San Francisco 49ers', 'TB': 'Tampa Bay Buccaneers', 'TEN': 'Tennessee Titans', 'WAS': 'Washington Commanders',
}

e = lambda x: html.escape('' if x is None else str(x))


def load(name):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else None


def f1(x):
    return '—' if x is None else f'{x:.1f}'


def f2(x):
    return '—' if x is None else f'{x:.2f}'


def pct(x, d=0):
    return '—' if x is None else f'{x * 100:.{d}f}%'


def team_name(a):
    return TEAM_NAMES.get(a, a)


# --------------------------------------------------------------------------- layout

NAV = [('/', 'Home'), ('/gameday/', 'Gameday'), ('/assignments/', 'This week'), ('/crew/', 'Crew chiefs'), ('/team/', 'Teams'),
       ('/trends/', 'Trends'), ('/guide/', 'Guide'), ('/dataset/', 'Data')]


def page(path, title, description, body, schema=None, crumbs=None):
    url = SITE + path
    blocks = list(schema or [])
    if crumbs:
        blocks.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (u, n) in enumerate(crumbs)]})
    ld = ''.join(f'\n    <script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>' for b in blocks)
    nav = ''.join(f'<a href="{u}"{" aria-current=page" if u == path else ""}>{n}</a>' for u, n in NAV)
    crumb_html = '' if not crumbs else '<div class="st-crumbs" role="navigation" aria-label="Breadcrumb">' + ' / '.join(
        f'<a href="{u}">{e(n)}</a>' if i < len(crumbs) - 1 else f'<span>{e(n)}</span>' for i, (u, n) in enumerate(crumbs)) + '</div>'
    out = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{e(title)}</title>
    <meta name="description" content="{e(description)}">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="NFL Officiating Observatory">
    <meta property="og:title" content="{e(title)}">
    <meta property="og:description" content="{e(description)}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{SITE}/og-image.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@NFLObservatory">
    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <meta name="theme-color" content="#0c0d0f">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/css/styles.css?v={V}">
    <link rel="stylesheet" href="/css/static.css?v={V}">{ld}
</head>
<body class="static-page">
    <header class="st-header">
        <a class="logo" href="/"><img src="/favicon.svg" alt="" class="logo-mark">NFL Officiating Observatory</a>
        <div class="st-nav" role="navigation" aria-label="Site">{nav}</div>
    </header>
    <main class="container st-main">
        {crumb_html}
        {body}
    </main>
    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-disclaimer"><strong>Data Note:</strong> Statistics reflect crew chief assignments, not individual
                    flag-throwers. Regular season, accepted penalties, from NFL play-by-play via nflverse. Updated automatically during and after every game day. Last updated {NOW.strftime('%B %-d, %Y')}.</div>
                <div class="footer-links"><a href="/guide/#methodology">Methodology</a><a href="/guide/#about">About</a><a href="/dataset/">Data</a></div>
            </div>
            <p class="footer-copyright">NFL Officiating Observatory. Not affiliated with the NFL. For educational purposes only.</p>
        </div>
    </footer>
</body>
</html>
"""
    dest = ROOT / path.strip('/') / 'index.html' if path != '/' else ROOT / 'index.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding='utf-8')
    SITEMAP.append(path)


SITEMAP = []


def tldr(text):
    return f'<div class="st-tldr"><span class="st-tldr-label">TL;DR</span><p>{text}</p></div>'


def faq(items, add_schema=None):
    """items: [(question, answer_html)] -> details blocks; add FAQPage schema to add_schema list."""
    if add_schema is not None:
        add_schema.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': html.unescape(_strip(a))}} for q, a in items]})
    return '<div class="st-faq">' + ''.join(f'<details open><summary><h3>{e(q)}</h3></summary><div class="st-answer">{a}</div></details>' for q, a in items) + '</div>'


def _strip(s):
    import re
    return re.sub(r'<[^>]+>', '', s)


def table(head, rows, cls=''):
    return (f'<div class="table-scroll"><table class="pv-table st-table {cls}"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head)
            + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table></div>')


def open_app(hashpart, label='Open the interactive view'):
    return f'<p class="st-open"><a class="st-btn" href="/#{hashpart}">{label} →</a></p>'


# --------------------------------------------------------------------------- data

sc = load('season_comparison.json') or {}
styles = load('crew_styles.json') or {}
teams_idx = load('teams/index.json') or {}
sb = load('scoreboard.json') or {}
tt = load('type_trends.json') or {}
fi = load('flag_impact.json') or {}
card = load('scorecard/public.json') or {}
prev_latest = load('previews/latest.json') or {}
previews = load(prev_latest.get('file', '')) if prev_latest.get('file') else None

SEASON = sc.get('currentSeason') or styles.get('season')
THRU = sc.get('throughWeek')
LG = (sc.get('league') or {}).get('current') or {}
style_by_name = {c['name']: c for c in styles.get('crews', [])}
WIN = sc.get('windows') or {}                      # shared windows and labels (scripts/weeks.py, #116)
_cs = (styles.get('careerSeasons') or (WIN.get('career') or {}).get('seasons')
       or [HISTORICAL_START, (SEASON or HISTORICAL_START + 1) - 1])
CAREER = weeks.span_label(_cs)                     # the career window (seasons before this one)
CAREER_US = CAREER.replace('–', '_')
START = WIN.get('dataStart') or _cs[0]             # first season in the data


def fade_lists():
    """The fade comparison's windows (type_trends.json → fadeWindows) and the prior-season
    average per game for each week in them."""
    fw = tt.get('fadeWindows') or {}
    wk = tt.get('weekly', {}).get('priorAverage', [])
    pick = lambda k: [w['perGame'] for w in wk if fw and fw[k]['from'] <= w['week'] <= fw[k]['to']]  # noqa: E731
    return fw, pick('early'), pick('late')


crews_now = sorted([c for c in sc.get('crewChiefs', []) if c.get('current', {}).get('games')],
                   key=lambda c: -c['current']['perGame'])
teams = []
for d in teams_idx.get('divisions', []):
    for t in d['teams']:
        teams.append({**t, 'division': d['name']})
teams.sort(key=lambda t: -(t.get('perGame') or 0))
season_frame = next((f for f in sb.get('frames', []) if f['key'] == 'season'), {})
last_frame = next((f for f in sb.get('frames', []) if f['key'] == 'lastSeason'), {})
thru_txt = f'through Week {THRU}' if THRU else 'so far'


def crew_link(name):
    c = style_by_name.get(name) or next((x for x in sc.get('crewChiefs', []) if x['name'] == name), None)
    slug = (c or {}).get('slug')
    return f'<a href="/crew/{slug}/">{e(name)}</a>' if slug else e(name)


def type_rate(crew, t, career=True):
    s = style_by_name.get(crew)
    if not s:
        return None
    src = s['types'] if career else (s.get('seasons', {}).get(str(SEASON), {}) or {}).get('types', {})
    return (src.get(t) or {}).get('perGame')


# --------------------------------------------------------------------------- pages

def league_levels():
    """League per-game levels from season_comparison.json, with their windows (no fixed numbers)."""
    all_seasons = next((b.get('seasons') for b in sc.get('baselines', []) if b.get('key') == 'all'), None)
    lg_all = (((sc.get('league') or {}).get('baselines') or {}).get('all') or {}).get('perGame')
    parts = []
    if all_seasons and lg_all is not None:
        parts.append(f"{f1(lg_all)} per game in {all_seasons[0]}–{str(all_seasons[-1])[2:]}")
    if LG.get('perGame') is not None:
        parts.append(f"{f1(LG['perGame'])} in {SEASON} {thru_txt}")
    return f" (league average {', '.join(parts)})" if parts else ''


def crew_pages():
    rows = []
    for c in crews_now:
        s = style_by_name.get(c['name'], {})
        allb = (c.get('baselines') or {}).get('all') or {}
        rows.append([f'<a href="/crew/{c["slug"]}/">{e(c["name"])}</a>', c['current']['games'], f'<strong>{f1(c["current"]["perGame"])}</strong>',
                     f1(allb.get('perGame')), e((s.get('archetype') or {}).get('title', '—'))])
    top = crews_now[:3]
    refs = {r['slug']: r for r in (load('referees.json') or [])}
    former = sorted(sc.get('inactiveCrewChiefs', []), key=lambda c: -(refs.get(c['slug'], {}).get('last_season') or 0))
    former_rows = [[f'<a href="/crew/{c["slug"]}/">{e(c["name"])}</a>',
                    f"{refs.get(c['slug'], {}).get('first_season', '—')}–{refs.get(c['slug'], {}).get('last_season', '—')}",
                    ((c.get('baselines') or {}).get('all') or {}).get('games', '—'),
                    f1(((c.get('baselines') or {}).get('all') or {}).get('perGame'))] for c in former]
    former_html = ('<h2>Former crew chiefs (since ' + str(START) + ')</h2>'
                   + table(['Crew chief', 'Seasons in the data', 'Games', 'Flags / game'], former_rows)
                   + f'<p class="st-note">Flags per game are raw averages; league levels vary by season{league_levels()}.</p>') if former_rows else ''
    body = f"""<h1 class="section-title">NFL referee stats {SEASON}: penalties per game by crew chief</h1>
    {tldr(f"Through Week {THRU} of {SEASON}, NFL games average <strong>{f1(LG.get('perGame'))} accepted penalties</strong>. "
          + ("The most flags per game have come in games worked by " + ', '.join(f"{crew_link(c['name'])} ({f1(c['current']['perGame'])})" for c in top) + ". " if top else '')
          + "Each crew chief's page lists his season and career numbers, style and most common calls.")}
    {table(['Crew chief', f'{SEASON} games', f'{SEASON} flags / game', f'{CAREER} flags / game', 'Career style'], rows)}
    {former_html}
    <p class="st-note">Accepted penalties in regular-season games each crew chief worked. Crew chiefs lead a seven-official crew; the data doesn't say which official threw each flag.</p>
    {open_app('referees', 'See the interactive crew chief profiles')}"""
    page('/crew/', f'NFL Referee Stats {SEASON}: Penalties Per Game by Crew Chief | NFL Officiating Observatory',
         f'Every active NFL crew chief ranked by penalties per game in {SEASON} {thru_txt}, with career averages and calling style.',
         body, crumbs=[('/', 'Home'), ('/crew/', 'Crew chiefs')])

    for c in sc.get('crewChiefs', []) + sc.get('inactiveCrewChiefs', []):
        name, slug = c['name'], c['slug']
        prof = load(f'referee/{slug}.json') or {}
        s = style_by_name.get(name, {})
        cur = c.get('current') or {}
        allb = (c.get('baselines') or {}).get('all') or {}
        last = (c.get('baselines') or {}).get('lastSeason') or {}
        diff = (cur['perGame'] / LG['perGame'] - 1) * 100 if cur.get('perGame') and LG.get('perGame') else None
        arch = (s.get('archetype') or {})
        cur_style = (s.get('seasons', {}).get(str(SEASON)) or {}).get('archetype') or {}
        types = sorted(((t, v['perGame'], v['diffPct']) for t, v in (s.get('types') or {}).items()), key=lambda x: -abs(x[2] or 0))
        type_rows = [[e(t), f2(pg), f"{'+' if dp > 0 else ''}{dp:.0f}%" if dp is not None else '—'] for t, pg, dp in types]
        season_rows = [[str(r['season']), r['games'], f1(r.get('avg'))] for r in prof.get('seasonStats', [])]
        recent = prof.get('recentGames', [])[:10]
        rec_rows = [[e(g.get('date', '')), f"{e(g['awayTeam']['abbr'])} @ {e(g['homeTeam']['abbr'])}",
                     f"{g.get('awayScore', '')}–{g.get('homeScore', '')}", g.get('penalties'),
                     f"{g['awayTeam']['abbr']} {g.get('awayPenalties')} · {g['homeTeam']['abbr']} {g.get('homePenalties')}"] for g in recent]
        summary = (f"{e(name)} is an NFL referee (crew chief). In {SEASON}, games his crew has worked average <strong>{f1(cur.get('perGame'))} accepted penalties</strong>"
                   f" over {cur.get('games', 0)} games" + (f", {abs(diff):.0f}% {'above' if diff > 0 else 'below'} the league's {f1(LG.get('perGame'))}" if diff is not None else '')
                   + f". Across {CAREER} his crew averaged {f1(allb.get('perGame'))} per game"
                   + (f" ({allb.get('games')} games), a <strong>{e(arch.get('title', '').lower())}</strong> style: {e(arch.get('description', ''))}." if arch else '.')) if cur.get('games') else \
                  (f"{e(name)} is an NFL referee (crew chief). Across {CAREER} his crew averaged {f1(allb.get('perGame'))} accepted penalties per game ({allb.get('games')} games).")
        traits = ''.join(f'<li>{e(t["text"])}</li>' for t in s.get('traits', []))
        sims = ', '.join(crew_link(x['name']) for x in s.get('similar', []))
        qa = []
        if cur.get('games'):
            qa.append((f'How many penalties does {name} call per game?',
                       f"<p>In {SEASON} {thru_txt}, games {e(name)}'s crew worked averaged {f1(cur['perGame'])} accepted penalties and {f1(cur.get('yardsPerGame'))} penalty yards per game ({cur['games']} games). "
                       f"His {CAREER} average was {f1(allb.get('perGame'))}; the {SEASON} league average is {f1(LG.get('perGame'))}.</p>"))
        if types:
            top = sorted(types, key=lambda x: -(x[1] or 0))[:3]
            qa.append((f'What penalties does {name} call most?',
                       f'<p>Per game, {CAREER}: ' + ', '.join(f"{e(t.lower())} ({f2(pg)})" for t, pg, _ in top) + '. '
                       + ('Compared with other crews: ' + '; '.join(e(t['text']) for t in s.get('traits', [])[:2]) + '.' if s.get('traits') else 'His mix of calls is close to the league average.') + '</p>'))
        if s.get('homeShare') is not None:
            qa.append((f'Does {name} call more penalties on the home team?',
                       f"<p>In {CAREER}, {pct(s['homeShare'])} of the flags in his games were on the home team (league: {pct(styles['league']['homeShare'])}). "
                       "Small differences like this are normal and are not evidence of bias.</p>"))
        schema = [{'@context': 'https://schema.org', '@type': 'ProfilePage', 'dateModified': NOW.isoformat(timespec='seconds'),
                   'name': f'{name}: NFL referee penalty stats', 'url': f'{SITE}/crew/{slug}/',
                   'mainEntity': {'@type': 'Person', 'name': name, 'jobTitle': 'NFL referee (crew chief)',
                                  'description': _strip(summary)[:300]}}]
        faq_html = faq(qa, schema) if qa else ''
        body = f"""<p class="section-number">CREW CHIEF PROFILE</p>
        <h1 class="section-title">{e(name)}: NFL referee penalty stats ({SEASON})</h1>
        {tldr(summary)}
        <div class="st-stats">
            <div><span>{SEASON} flags / game</span><b>{f1(cur.get('perGame'))}</b><em>{cur.get('games', 0)} games · league {f1(LG.get('perGame'))}</em></div>
            <div><span>{SEASON} yards / game</span><b>{f1(cur.get('yardsPerGame'))}</b><em>league {f1(LG.get('yardsPerGame'))}</em></div>
            <div><span>{(last or {}).get('games') and (SEASON - 1) or 'Last season'} flags / game</span><b>{f1(last.get('perGame'))}</b><em>{last.get('games', 0)} games</em></div>
            <div><span>{CAREER} flags / game</span><b>{f1(allb.get('perGame'))}</b><em>{allb.get('games', 0)} games</em></div>
        </div>
        <h2>Calling style</h2>
        <p>Career ({CAREER}): <strong>{e(arch.get('title', '—'))}</strong>, {e(arch.get('description', ''))}.{f" {SEASON} so far: <strong>{e(cur_style.get('title'))}</strong>." if cur_style else ''}</p>
        {f'<ul class="st-list">{traits}</ul>' if traits else '<p>Close to the league average on every measure we track.</p>'}
        {f'<p>Calls most like: {sims}.</p>' if sims else ''}
        {f'<h2>Penalty types vs the league ({CAREER}, season-adjusted, per game)</h2>' + table(['Penalty', 'Per game', 'vs league rate'], type_rows) if type_rows else ''}
        {'<h2>Season by season (regular season)</h2>' + table(['Season', 'Games', 'Flags / game'], season_rows) if season_rows else ''}
        {'<h2>Recent games (regular season)</h2>' + table(['Date', 'Game', 'Score', 'Flags', 'By team'], rec_rows) if rec_rows else ''}
        {f'<p class="st-note">Playoff games worked: {prof["playoffGames"]} (mixed crews; not included in rates).</p>' if prof.get('playoffGames') is not None else ''}
        <h2>Questions</h2>
        {faq_html}
        <p class="st-note">Statistics reflect the crew chief's assignment; crews change around the chief each year. Patterns, not motives.</p>
        {open_app(f'crew={slug}')}"""
        page(f'/crew/{slug}/', f'{name} NFL Referee Stats {SEASON}: Penalties Per Game & Calling Style',
             f"{name}'s crew averages {f1(cur.get('perGame'))} penalties per game in {SEASON} (career {f1(allb.get('perGame'))}). Calling style, most common penalties, season-by-season and recent games.",
             body, schema, crumbs=[('/', 'Home'), ('/crew/', 'Crew chiefs'), (f'/crew/{slug}/', name)])


def team_pages():
    cost = {t['team']: t for t in ((fi.get('scopes') or {}).get('current') or {}).get('teams', [])}
    rows = [[t.get('rank'), f'<a href="/team/{t["abbr"]}/">{e(team_name(t["abbr"]))}</a>', t.get('games'), f'<strong>{f1(t.get("perGame"))}</strong>',
             f1(t.get('lastSeasonPerGame')), f2(cost.get(t['abbr'], {}).get('pointsCostPerGame'))] for t in teams]
    most, least = teams[:3], teams[-3:]
    body = f"""<h1 class="section-title">NFL team penalty stats {SEASON}: most and least penalized teams</h1>
    {tldr(f"Most penalized per game in {SEASON} {thru_txt}: " + ', '.join(f"{e(team_name(t['abbr']))} ({f1(t['perGame'])})" for t in most)
          + ". Least: " + ', '.join(f"{e(team_name(t['abbr']))} ({f1(t['perGame'])})" for t in reversed(least)) + f". League average: {f1(teams_idx.get('leaguePerGame'))} per team per game.")}
    {table(['Rank', 'Team', 'Games', f'{SEASON} flags / game', f'{SEASON - 1} flags / game', 'Points given away / game'], rows)}
    <p class="st-note">Accepted penalties on each team, regular season. "Points given away" is the expected-points cost of those flags (see the <a href="/guide/#flag-cost">guide</a>).</p>
    {open_app('teams', 'See the interactive team profiles')}"""
    page('/team/', f'NFL Team Penalty Stats {SEASON}: Most Penalized Teams | NFL Officiating Observatory',
         f'All 32 NFL teams ranked by penalties per game in {SEASON} {thru_txt}, with last season and the points their flags cost.',
         body, crumbs=[('/', 'Home'), ('/team/', 'Teams')])

    for t in teams:
        a = t['abbr']
        p = load(f'teams/{a}.json') or {}
        cur, last = p.get('current') or {}, p.get('lastSeason') or {}
        ct = cost.get(a, {})
        name = team_name(a)
        types = [[e(x['type']), f2(x.get('currentPerGame')), f2(x.get('priorPerGame'))] for x in (p.get('committedTypes') or [])[:8]]
        crews = [[crew_link(x.get('name')), x.get('games'), f1(x.get('perGame'))] for x in (p.get('crews') or [])[:8]]
        games = [[f"Wk {g['week']}", f"{'vs' if g.get('home') else '@'} {e(g['opponent'])}", e(g.get('result', '')) + ' ' + e(g.get('score', '')), g.get('flags'), g.get('opponentFlags')]
                 for g in (p.get('games') or [])]
        summary = (f"The {e(name)} are averaging <strong>{f1(cur.get('perGame'))} accepted penalties per game</strong> in {SEASON} ({cur.get('games', 0)} games), "
                   f"#{p.get('rank', {}).get('current', '—') if isinstance(p.get('rank'), dict) else t.get('rank', '—')} most in the NFL"
                   f" (league {f1(teams_idx.get('leaguePerGame'))}). Last season: {f1(last.get('perGame'))} per game."
                   + (f" Their flags have cost {f2(ct.get('pointsCostPerGame'))} expected points per game." if ct else ''))
        qa = [(f'How many penalties do the {name} average in {SEASON}?',
               f"<p>{f1(cur.get('perGame'))} accepted penalties and {f1(cur.get('yardsPerGame'))} penalty yards per game over {cur.get('games', 0)} games, "
               f"vs {f1(last.get('perGame'))} per game in {SEASON - 1}. Opponents have been flagged {f1(cur.get('drawnPerGame'))} times per game.</p>")]
        if types:
            qa.append((f'What penalties are the {name} called for most?',
                       '<p>Per game in ' + str(SEASON) + ': ' + ', '.join(f"{r[0].lower()} ({r[1]})" for r in types[:3]) + '.</p>'))
        schema = [{'@context': 'https://schema.org', '@type': 'WebPage', 'name': f'{name} penalty stats {SEASON}', 'url': f'{SITE}/team/{a}/',
                   'dateModified': NOW.isoformat(timespec='seconds'), 'about': {'@type': 'SportsTeam', 'name': name, 'sport': 'American football',
                                                                              'memberOf': {'@type': 'SportsOrganization', 'name': 'National Football League'}}}]
        body = f"""<p class="section-number">TEAM PROFILE · {e(t['division'])}</p>
        <h1 class="section-title">{e(name)} penalty stats ({SEASON})</h1>
        {tldr(summary)}
        <div class="st-stats">
            <div><span>Flags / game</span><b>{f1(cur.get('perGame'))}</b><em>{cur.get('games', 0)} games · league {f1(teams_idx.get('leaguePerGame'))}</em></div>
            <div><span>Opponent flags / game</span><b>{f1(cur.get('drawnPerGame'))}</b><em>flags drawn</em></div>
            <div><span>Penalty yards / game</span><b>{f1(cur.get('yardsPerGame'))}</b><em>{SEASON - 1}: {f1(last.get('yardsPerGame'))}</em></div>
            <div><span>Points given away / game</span><b>{f2(ct.get('pointsCostPerGame'))}</b><em>#{ct.get('rank', '—')} most costly</em></div>
        </div>
        {'<h2>Most common penalties</h2>' + table(['Penalty', f'{SEASON} / game', f'{CAREER} / game'], types) if types else ''}
        {'<h2>Game log</h2>' + table(['Week', 'Opponent', 'Result', 'Flags on ' + a, 'Flags on opponent'], games) if games else ''}
        {f'<h2>By crew chief (since {START})</h2>' + table(['Crew chief', 'Games', f'Flags on {a} / game'], crews) if crews else ''}
        <h2>Questions</h2>
        {faq(qa, schema)}
        {open_app(f'team={a}')}"""
        page(f'/team/{a}/', f'{name} Penalty Stats {SEASON}: Flags Per Game, Most Common Penalties',
             f"The {name} average {f1(cur.get('perGame'))} penalties per game in {SEASON}. Most common penalties, game log, crew chiefs and the points their flags cost.",
             body, schema, crumbs=[('/', 'Home'), ('/team/', 'Teams'), (f'/team/{a}/', name)])


def assignments_page():
    if not previews or not previews.get('games'):
        return
    wk = previews['week']
    rows = []
    for g in previews['games']:
        c = g.get('crew') or {}
        s = style_by_name.get(c.get('name'), {})
        cur = (next((x for x in sc.get('crewChiefs', []) if x['name'] == c.get('name')), {}) or {}).get('current') or {}
        rows.append([f"{e(g['awayTeam']['abbr'])} @ {e(g['homeTeam']['abbr'])}", e(g.get('gameday', '')), e(g.get('network') or ''),
                     crew_link(c['name']) if c.get('name') else 'TBA', f1(cur.get('perGame')), e((s.get('archetype') or {}).get('title', '—')),
                     f1((g.get('projection') or {}).get('total'))])
    known = [g for g in previews['games'] if g.get('crew')]
    heavy = sorted(known, key=lambda g: -((g.get('projection') or {}).get('total') or 0))[:2]
    body = f"""<p class="section-number">WEEK {wk} · {SEASON}</p>
    <h1 class="section-title">NFL referee assignments, Week {wk} {SEASON}</h1>
    {tldr(f"{len(known)} of {len(previews['games'])} Week {wk} games have a crew chief assigned. "
          + ('Projected most flags: ' + '; '.join(f"{e(g['awayTeam']['abbr'])} @ {e(g['homeTeam']['abbr'])} with {crew_link(g['crew']['name'])} ({f1(g['projection']['total'])})" for g in heavy) + '.' if heavy else ''))}
    {table(['Game', 'Date', 'TV', 'Crew chief', f'Crew {SEASON} flags / game', 'Crew career style', 'Projected flags'], rows)}
    <p class="st-note">Assignments as published before kickoff (Football Zebras). Projections are our model's expected accepted penalties for the game; see <a href="/guide/#projections">how projections work</a>.</p>
    {open_app('previews', 'See full game previews')}"""
    page('/assignments/', f'NFL Referee Assignments Week {wk} {SEASON}: Crew Chief for Every Game',
         f'Who is refereeing every NFL Week {wk} {SEASON} game, each crew chief\'s penalty rate and style, and projected flags.',
         body, crumbs=[('/', 'Home'), ('/assignments/', f'Week {wk} assignments')])


def trends_page():
    scmp = tt.get('seasonCompare', [])
    rows = [[str(x['season']), x['games'], f1(x.get('fullSeason')) if x.get('complete') else '—', f1(x.get('early'))] for x in scmp]
    comp = next((c for c in tt.get('comparisons', []) if c['key'] == tt.get('defaultComparison')), {})
    rising = sorted(tt.get('types', []), key=lambda r: -((r.get('current') or 0) - ((r.get('compare') or {}).get(comp.get('key')) or 0)))
    rrows = [[e(r['type']), f2(r.get('current')), f2((r.get('compare') or {}).get(comp.get('key'))),
              f"{((r.get('current') or 0) - ((r.get('compare') or {}).get(comp.get('key')) or 0)):+.2f}"] for r in rising]
    fw, early, late = fade_lists()
    q = (tt.get('quarters') or {}).get('all') or {}
    cost = ((fi.get('scopes') or {}).get('current') or {})
    sea, lastsea = season_frame, last_frame
    body = f"""<p class="section-number">LEAGUE TRENDS</p>
    <h1 class="section-title">NFL penalty trends {SEASON}: are penalties up?</h1>
    {tldr(f"{SEASON} games average <strong>{f1(sea.get('perGame'))} accepted penalties</strong> {thru_txt}, vs {f1(lastsea.get('perGame'))} across all of {SEASON - 1}. "
          f"About {f1(sea.get('pctPlays'))}% of plays draw a flag (one every {f1(sea.get('flagEveryPlays'))} plays). "
          + (f"The biggest increases vs {e(comp.get('label', 'last season'))}: " + ', '.join(f"{e(r['type'].lower())}" for r in rising[:3]) + '. ' if rising else '')
          + (f"Flags usually fade as the season goes on: {fw['late']['label']} average {abs(1 - (sum(late) / len(late)) / (sum(early) / len(early))) * 100:.0f}% fewer than {fw['early']['label']}." if early and late else ''))}
    <h2>Penalties per game by season</h2>
    {table(['Season', 'Games', 'Full season / game', f"{weeks.weeks_label(tt.get('throughWeek'))} / game"], rows)}
    <p class="st-note">Regular season. The early-weeks column compares every season over the same weeks as the current one, the fair comparison while a season is in progress.</p>
    <h2>Which penalties are increasing?</h2>
    {table(['Penalty', f'{SEASON} / game', f"{e(comp.get('short', 'Comparison'))} / game", 'Change'], rrows)}
    <h2>When are penalties called?</h2>
    <p>Since {START}, flags per game by quarter: Q1 {f2((q.get('total') or [None]*4)[0])}, Q2 {f2((q.get('total') or [None]*4)[1])}, Q3 {f2((q.get('total') or [None]*4)[2])}, Q4 {f2((q.get('total') or [None]*4)[3])}. The second quarter usually leads, partly because the two-minute drill packs in extra plays.</p>
    <h2>Home vs road</h2>
    <p>In {SEASON}, {f1(100 - (sea.get('homeShare') or 50))}% of flags are on road teams and {f1(sea.get('homeShare'))}% on home teams ({CAREER} crews: {pct(styles.get('league', {}).get('homeShare'))} on the home team).</p>
    <h2>What penalties cost</h2>
    <p>League-wide, flags cost each team about {f2((cost.get('league') or {}).get('pointsCostPerTeamGame'))} expected points per game in {SEASON}. Most costly: {', '.join(f"{e(team_name(x['team']))} ({f2(x['pointsCostPerGame'])})" for x in cost.get('teams', [])[:3])}.</p>
    {open_app('trends', 'See the interactive League Trends charts')}"""
    page('/trends/', f'NFL Penalty Trends {SEASON}: Penalties Per Game by Season, Week and Type',
         f'Are NFL penalties up in {SEASON}? Penalties per game by season and week, which penalties are rising, home vs road and what flags cost.',
         body, crumbs=[('/', 'Home'), ('/trends/', 'League trends')])


def dataset_page():
    exp = DATA / 'exports'
    exp.mkdir(parents=True, exist_ok=True)
    files = []

    def write(name, head, rows, desc):
        with open(exp / name, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(head)
            w.writerows(rows)
        files.append((name, desc, len(rows)))
    write(f'crew_chiefs_{SEASON}.csv', ['crew_chief', f'games_{SEASON}', f'flags_per_game_{SEASON}', f'yards_per_game_{SEASON}', f'career_games_{CAREER_US}', f'career_flags_per_game_{CAREER_US}', 'career_style'],
          [[c['name'], c['current'].get('games'), c['current'].get('perGame'), c['current'].get('yardsPerGame'),
            ((c.get('baselines') or {}).get('all') or {}).get('games'), ((c.get('baselines') or {}).get('all') or {}).get('perGame'),
            (style_by_name.get(c['name'], {}).get('archetype') or {}).get('title')] for c in crews_now], f'Penalties per game by crew chief, current season and {CAREER}')
    write(f'teams_{SEASON}.csv', ['team', 'games', 'flags_per_game', 'last_season_flags_per_game', 'rank'],
          [[t['abbr'], t.get('games'), t.get('perGame'), t.get('lastSeasonPerGame'), t.get('rank')] for t in teams], 'Penalties per game by team, current season')
    write('flags_by_season.csv', ['season', 'games', 'flags_per_game_full_season', 'flags_per_game_same_early_weeks'],
          [[x['season'], x['games'], x.get('fullSeason') if x.get('complete') else '', x.get('early')] for x in tt.get('seasonCompare', [])], 'League penalties per game by season')
    write('flags_by_week.csv', ['season', 'week', 'games', 'flags_per_game'],
          [[s_['season'], w['week'], w['games'], w['perGame']] for s_ in tt.get('weekly', {}).get('seasons', []) for w in s_['weeks']], f'League penalties per game by week of season, {START} to now')
    write('penalty_types_by_season.csv', ['penalty_type', 'season', 'per_game'],
          [[r['type'], b['season'], b['perGame']] for r in tt.get('types', []) for b in r.get('bySeason', [])], 'Per-game rate of each common penalty type by season')
    dist = [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'name': n, 'contentUrl': f'{SITE}/data/exports/{n}'} for n, _, _ in files]
    schema = [{'@context': 'https://schema.org', '@type': 'Dataset',
               'name': 'NFL Officiating Observatory: NFL penalty and referee (crew chief) statistics',
               'description': (f'Accepted penalties in NFL regular-season games since {START}, aggregated by crew chief (head referee), team, season, '
                               'week and penalty type. Updated automatically during and after every game day. Includes penalties per game, penalty yards, calling-style '
                               'measures and the expected-points cost of penalties.'),
               'url': f'{SITE}/dataset/', 'sameAs': SITE,
               'keywords': ['NFL', 'penalties', 'referees', 'crew chief', 'officiating', 'football statistics', 'sports data'],
               'creator': {'@type': 'Organization', 'name': 'NFL Officiating Observatory', 'url': SITE},
               'isBasedOn': 'https://github.com/nflverse',
               'temporalCoverage': f'{START}-09/{TODAY}', 'spatialCoverage': 'United States',
               'dateModified': NOW.isoformat(timespec='seconds'),
               'license': 'https://creativecommons.org/licenses/by/4.0/',
               'creditText': 'NFL Officiating Observatory (nflobservatory.com), from nflverse play-by-play',
               'isAccessibleForFree': True, 'distribution': dist,
               'variableMeasured': ['penalties per game', 'penalty yards per game', 'penalties by type', 'expected points cost of penalties']}]
    rows = [[f'<a href="/data/exports/{n}">{e(n)}</a>', e(d), r] for n, d, r in files]
    body = f"""<p class="section-number">FULL DATA</p>
    <h1 class="section-title">NFL penalty and referee data (downloads)</h1>
    {tldr(f"Free CSV downloads of NFL penalty statistics: by crew chief, team, season, week and penalty type, regular season since {START}. Updated automatically during and after every game day. "
          "Please credit nflobservatory.com.")}
    {table(['File', 'What it contains', 'Rows'], rows)}
    <h2>About the data</h2>
    <p>Built from NFL play-by-play published by <a href="https://github.com/nflverse" rel="noopener">nflverse</a>, with crew assignments from nflverse and Football Zebras.
    Counts are accepted penalties in regular-season games. Declined and offsetting penalties are not counted. See the <a href="/guide/#methodology">methodology</a>.</p>
    {open_app('data', 'See the full interactive tables')}"""
    page('/dataset/', 'NFL Penalty & Referee Data: Free CSV Downloads | NFL Officiating Observatory',
         f'Free CSV downloads of NFL penalty statistics by crew chief, team, season, week and penalty type since {START}. Updated automatically during and after every game day.',
         body, schema, crumbs=[('/', 'Home'), ('/dataset/', 'Data')])


def guide_page():
    hold = sorted(((n, type_rate(n, 'Offensive Holding')) for n in style_by_name), key=lambda x: -(x[1] or 0))[:3]
    dpi = sorted(((n, type_rate(n, 'Defensive Pass Interference')) for n in style_by_name), key=lambda x: -(x[1] or 0))[:3]
    g_of = lambda n: style_by_name[n]['games']
    top_now = crews_now[:3]
    car = sorted(style_by_name.values(), key=lambda c: -c['perGame'])[:3]
    live = (card.get('live') or {}).get('summary') or {}
    fw, early, late = fade_lists()
    comp = next((c for c in tt.get('comparisons', []) if c['key'] == tt.get('defaultComparison')), {})
    rising = sorted(tt.get('types', []), key=lambda r: -((r.get('current') or 0) - ((r.get('compare') or {}).get(comp.get('key')) or 0)))[:3]
    cost = ((fi.get('scopes') or {}).get('current') or {})
    lgs = styles.get('league', {})
    schema = []
    qa = [
        (f'Which NFL referees call the most penalties in {SEASON}?',
         f"<p>Through Week {THRU}, the most accepted penalties per game have come in games worked by " + '; '.join(f"{crew_link(c['name'])} ({f1(c['current']['perGame'])} in {c['current']['games']} games)" for c in top_now)
         + f". The league average is {f1(LG.get('perGame'))}. Early-season samples are small. <a href=\"/crew/\">All crew chiefs</a>.</p>"),
        ('Which NFL referees call the most penalties overall?',
         f'<p>Across the {CAREER} regular seasons (season-adjusted): ' + '; '.join(f"{crew_link(c['name'])} ({f1(c['perGame'])} per game, {c['games']} games)" for c in car)
         + f". League average: {f1(lgs.get('perGame'))}.</p>"),
        ('Which NFL referees call the most holding penalties?',
         f'<p>Offensive holding per game in each crew chief\'s games, {CAREER}: ' + '; '.join(f"{crew_link(n)} ({f2(v)}, {g_of(n)} games)" for n, v in hold if v)
         + '. Rates are adjusted toward the league average to account for sample size.</p>'),
        ('Which NFL referees call the most pass interference?',
         f'<p>Defensive pass interference per game, {CAREER}: ' + '; '.join(f"{crew_link(n)} ({f2(v)}, {g_of(n)} games)" for n, v in dpi if v) + '.</p>'),
        ('Do NFL referees favor the home team?',
         f"<p>Slightly fewer flags go against home teams: across {CAREER} crews, {pct(lgs.get('homeShare'), 1)} of accepted penalties were on the home team "
         f"and {pct(1 - lgs.get('homeShare', 0.5), 1)} on the road team. In {SEASON}, {f1(season_frame.get('homeShare'))}% are on the home team. "
         "The gap is small and can reflect crowd noise (more false starts for road offenses) as much as officiating.</p>"),
        (f'Which NFL team commits the most penalties in {SEASON}?',
         '<p>' + ', '.join(f"<a href=\"/team/{t['abbr']}/\">{e(team_name(t['abbr']))}</a> ({f1(t['perGame'])} per game)" for t in teams[:3])
         + f" lead the league {thru_txt}. Fewest: " + ', '.join(f"<a href=\"/team/{t['abbr']}/\">{e(team_name(t['abbr']))}</a> ({f1(t['perGame'])})" for t in teams[-2:]) + '.</p>'),
        (f'Are NFL penalties up in {SEASON}?',
         f"<p>Yes. {SEASON} games average {f1(season_frame.get('perGame'))} accepted penalties {thru_txt}, vs {f1(last_frame.get('perGame'))} in {SEASON - 1}. "
         + ('The biggest increases are in ' + ', '.join(e(r['type'].lower()) for r in rising) + '. ' if rising else '') + '<a href="/trends/">League trends</a>.</p>'),
        ('Do refs call more penalties early in the season?',
         (f"<p>Usually. Since {START}, {fw['early']['label']} average {f1(sum(early) / len(early))} flags per game and {fw['late']['label']} average {f1(sum(late) / len(late))}. "
          "The last two weeks are lowest of all, partly because of resting starters and games with nothing at stake.</p>") if early and late else '<p>Data not available.</p>'),
        ('How much does a penalty cost a team?',
         f"<p>About {f2((cost.get('league') or {}).get('pointsCostPerTeamGame'))} expected points per team per game in {SEASON}. The most costly flags are pass interference "
         "and personal fouls that hand the offense a first down on third down. <a href=\"#flag-cost\">How it's measured</a>.</p>"),
        ('How accurate are the penalty projections?',
         (f"<p>Projections published before kickoff have missed the actual flag count by {f2(live.get('avgMiss'))} on average, and {f1(live.get('hitRate'))}% landed inside the "
          f"projected range ({live.get('games')} games). Guessing the league average every game would have missed by {f2(live.get('baselineAvgMiss'))}.</p>") if live else '<p>The track record starts once games are graded.</p>'),
        ('What is an NFL crew chief?',
         '<p>The referee: the white-hat official who leads a seven-person officiating crew, announces penalties and has final authority on the field. '
         'The NFL assigns crews by crew chief each week. Play-by-play doesn\'t record which official threw a flag, so statistics are tracked by crew chief.</p>'),
    ]
    body = f"""<p class="section-number">GUIDE</p>
    <h1 class="section-title">NFL referee and penalty statistics: methodology, glossary and FAQ</h1>
    {tldr("How the NFL Officiating Observatory measures penalties, crew chiefs and teams, what every term means, and answers to the most common questions, with live numbers.")}
    <h2 id="faq">Frequently asked questions</h2>
    {faq(qa, schema)}
    <h2 id="methodology">Methodology</h2>
    <p><strong>What's counted.</strong> Accepted penalties in regular-season games since {START}, from NFL play-by-play published by nflverse. Declined and offsetting
    penalties are not counted. Playoffs are excluded so seasons compare fairly.</p>
    <p><strong>Crew chiefs.</strong> Each game is credited to its referee (crew chief), using nflverse officials data, the NFL schedule, and, for the newest week,
    the assignments published before kickoff by Football Zebras. Crews change around the chief each year, so these are crew-chief-level patterns, not
    individual officials. We describe patterns, not motives.</p>
    <p><strong>Comparisons.</strong> Penalties are up in recent seasons and run higher early in every season, so a current season is compared with the same
    weeks of past seasons, and crews and teams are compared with the league in the same games.</p>
    <h3 id="projections">How projections work</h3>
    <p>Before each game we project accepted penalties for each team from three things: the team's own discipline, what its opponent tends to draw,
    and the assigned crew chief's calling rate, each adjusted toward the league average when the sample is small. The projection includes a likely range
    and the chance of 15 or more flags. Every projection is saved before kickoff and graded after the game in the public track record.</p>
    <h3 id="flag-cost">How a penalty's cost is measured</h3>
    <p>When a flag erases the play, its cost is the change in expected points (nflverse's model) charged to the penalized team. When a flag is added on top
    of a play that counts, only the penalty yards are charged, at the league's expected points per yard. A flag that wipes out the offense's own touchdown
    is charged the touchdown's value (with the extra point), less the expected points before the play and anything the play kept. A flag that erases a
    failed two-point try is worth a retry at the league's two-point conversion rate.</p>
    <h3 id="styles">Crew styles</h3>
    <p>Each crew chief is placed by flags per game and yards per flag against the league average: <strong>game-changers</strong> (more flags, bigger calls),
    <strong>stop-and-start</strong> (more flags, smaller calls), <strong>few but costly</strong> and <strong>let them play</strong>. A trait is only listed when the
    difference is meaningful (5% for volume, 3 percentage points for shares, 15% for a penalty type).</p>
    <h2 id="glossary">Glossary</h2>
    <dl class="st-dl">
        <dt>Accepted penalty</dt><dd>A flag the offended team accepted; the only kind counted here.</dd>
        <dt>Flags per game</dt><dd>Accepted penalties on both teams in a game, averaged.</dd>
        <dt>Penalty yards</dt><dd>Yards assessed for accepted penalties.</dd>
        <dt>Pre-snap penalty</dt><dd>Fouls before the snap: false start, offside, encroachment, delay of game, illegal formation and similar.</dd>
        <dt>Flags drawn</dt><dd>Penalties called on a team's opponents.</dd>
        <dt>Expected points (EPA)</dt><dd>How many points a play changed a team's expected scoring, from nflverse's model.</dd>
        <dt>Key first down given</dt><dd>A defensive penalty that gave the offense a first down on 3rd or 4th down.</dd>
        <dt>Same-weeks comparison</dt><dd>Comparing a season in progress with past seasons over the same weeks.</dd>
    </dl>
    <h2 id="about">About</h2>
    <p>The NFL Officiating Observatory is an independent, data-driven project tracking NFL penalties and officiating patterns. Updated automatically during and after every game day.
    It is not affiliated with the NFL. Data is free to use with credit; see <a href="/dataset/">the data page</a>. Follow <a href="https://x.com/NFLObservatory" rel="noopener">@NFLObservatory</a>.</p>
    {open_app('season', 'Explore the live dashboard')}"""
    page('/guide/', 'NFL Referee & Penalty Stats Guide: Methodology, Glossary and FAQ | NFL Officiating Observatory',
         'Which NFL referees call the most penalties? Do refs favor home teams? Methodology, glossary and answers with live NFL penalty data.',
         body, schema, crumbs=[('/', 'Home'), ('/guide/', 'Guide')])


def home_summary():
    """Replace the marked block in index.html with this week's facts (visible + crawlable)."""
    idx = ROOT / 'index.html'
    s = idx.read_text(encoding='utf-8')
    a, b = '<!-- SEO:SUMMARY -->', '<!-- /SEO:SUMMARY -->'
    if a not in s or b not in s:
        return
    top = crews_now[:1]
    most = teams[:1]
    txt = (f"<strong>This week in NFL officiating:</strong> {SEASON} games average {f1(season_frame.get('perGame'))} accepted penalties {thru_txt} "
           f"(vs {f1(last_frame.get('perGame'))} in {SEASON - 1})."
           + (f" Most flags per game: {crew_link(top[0]['name'])}'s crew ({f1(top[0]['current']['perGame'])})." if top else '')
           + (f" Most penalized team: <a href=\"/team/{most[0]['abbr']}/\">{e(team_name(most[0]['abbr']))}</a> ({f1(most[0]['perGame'])} per game)." if most else '')
           + ' <a href="/assignments/">This week\'s referee assignments</a> · <a href="/guide/">FAQ</a>')
    block = f'{a}\n        <p class="tldr-text">{txt}</p>\n        {b}'
    i, j = s.index(a), s.index(b) + len(b)
    idx.write_text(s[:i] + block + s[j:], encoding='utf-8')


def home_prefill():
    """Write real numbers into the home page sections the app fills with JavaScript, so the
    page source isn't 'Loading...' and empty tables. The app replaces each block on load."""
    idx = ROOT / 'index.html'
    s = idx.read_text(encoding='utf-8')

    def put(key, content):
        nonlocal s
        a, b = f'<!-- SEO:{key} -->', f'<!-- /SEO:{key} -->'
        if a in s and b in s:
            i, j = s.index(a) + len(a), s.index(b)
            s = s[:i] + content + s[j:]

    base = next((b for b in sc.get('baselines', []) if b['key'] == sc.get('defaultBaseline')), {})
    lb = ((sc.get('league') or {}).get('baselines') or {}).get(base.get('key'), {}) or {}
    pw = sc.get('partialWeek')
    put('SEASON_SUB', e(f"Regular season through Week {THRU}" + (f" (plus {pw['games']} game{'s' if pw['games'] != 1 else ''} from Week {pw['week']})" if pw else '')
                      + f", compared with {(base.get('label') or 'last season')[:1].lower() + (base.get('label') or 'last season')[1:]}."))

    def tile(label, val, cmp):
        return (f'<div class="season-stat"><div class="season-stat-label">{label}</div><div class="season-stat-value">{val}</div>'
                f'<div class="season-stat-compare">{cmp}</div></div>')
    put('SEASON_LEAGUE', ''.join([
        tile(f'{SEASON} so far', f"{LG.get('penalties', 0):,}", f"penalties · {LG.get('yards', 0):,} yards in {LG.get('games', 0)} games"),
        tile('Penalties per game', f1(LG.get('perGame')), f"{e(base.get('short', ''))}: {f1(lb.get('perGame'))}"),
        tile('Penalty yards per game', f1(LG.get('yardsPerGame')), f"{e(base.get('short', ''))}: {f1(lb.get('yardsPerGame'))}"),
        tile('Yards per penalty', f1(LG.get('yardsPerPenalty')), f"{e(base.get('short', ''))}: {f1(lb.get('yardsPerPenalty'))}"),
    ]))
    put('SEASON_TABLE', ''.join(
        f"<tr><td><a href=\"/crew/{c['slug']}/\">{e(c['name'])}</a></td><td>{c['current']['games']}</td>"
        f"<td>{c['current'].get('penalties', '')} / {c['current'].get('yards', '')}</td><td>{f1(c['current'].get('perGame'))}</td>"
        f"<td>{f1(c['current'].get('yardsPerGame'))}</td><td>{f1(((c.get('baselines') or {}).get(base.get('key')) or {}).get('perGame'))} {e(base.get('short', ''))}</td></tr>"
        for c in crews_now))
    divs = ''
    for d in teams_idx.get('divisions', []):
        rows = ''.join(f'<li><a href="/team/{t["abbr"]}/">{e(team_name(t["abbr"]))}</a> {f1(t.get("perGame"))} flags/game</li>'
                       for t in sorted(d['teams'], key=lambda t: -(t.get('perGame') or 0)))
        divs += f'<div class="seo-prefill-col"><h3>{e(d["name"])}</h3><ul>{rows}</ul></div>'
    put('DIVISIONS', f'<div class="seo-prefill">{divs}</div>')
    if previews and previews.get('games'):
        g_rows = ''.join(
            f"<li>{e(g['awayTeam']['abbr'])} @ {e(g['homeTeam']['abbr'])}: "
            + (f"crew chief {crew_link(g['crew']['name'])}, " if g.get('crew') else 'crew TBA, ')
            + f"projected {f1((g.get('projection') or {}).get('total'))} flags</li>" for g in previews['games'])
        put('PREVIEWS', f'<div class="seo-prefill"><div class="seo-prefill-col wide"><h3>Week {previews["week"]} games and referee assignments</h3>'
                        f'<ul>{g_rows}</ul><p><a href="/assignments/">All Week {previews["week"]} referee assignments</a></p></div></div>')
    put('REFEREES', '<div class="seo-prefill"><div class="seo-prefill-col wide"><h3>Crew chiefs</h3><ul>' + ''.join(
        f"<li>{crew_link(c['name'])}: {f1(c['current']['perGame'])} flags/game in {SEASON}, "
        f"{f1(((c.get('baselines') or {}).get('all') or {}).get('perGame'))} in {CAREER}</li>" for c in crews_now) + '</ul></div></div>')
    refs = load('referees.json') or []
    put('DATA_TABLE', ''.join(
        f"<tr><td>{crew_link(r['name'])}</td><td>{r.get('games')}</td><td>{f1(r.get('avg_per_game'))}</td>"
        f"<td>{r.get('min_penalties')}–{r.get('max_penalties')}</td><td>{f1(r.get('home_bias_pct'))} pts</td><td>{e(r.get('consistency', ''))}</td></tr>"
        for r in refs))
    idx.write_text(s, encoding='utf-8')


def sitemap_and_llms():
    urls = ['/', '/gameday/'] + [p for p in SITEMAP if p != '/']
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in dict.fromkeys(urls):
        pr = '1.0' if u == '/' else '0.8' if u.count('/') <= 2 else '0.6'
        xml.append(f'  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{pr}</priority></url>')
    xml.append('</urlset>')
    (ROOT / 'sitemap.xml').write_text('\n'.join(xml) + '\n', encoding='utf-8')
    top = ', '.join(f"{c['name']} ({f1(c['current']['perGame'])}/game)" for c in crews_now[:3])
    llms = f"""# NFL Officiating Observatory

> Independent, data-driven tracking of NFL penalties and officiating: accepted penalties in regular-season games since {START}, by crew chief (head referee), team, season, week and penalty type, with pre-game flag projections and a public track record. Updated automatically during and after every game day. Not affiliated with the NFL.

Current numbers ({SEASON}, {thru_txt}): {f1(season_frame.get('perGame'))} accepted penalties per game (vs {f1(last_frame.get('perGame'))} in {SEASON - 1}). Most flags per game by crew chief: {top}.

## Key pages
- [Referee (crew chief) stats]({SITE}/crew/): every active crew chief, penalties per game, career and style
- [Team penalty stats]({SITE}/team/): all 32 teams ranked by penalties per game
- [This week's referee assignments]({SITE}/assignments/): crew chief for every game, with projections
- [League penalty trends]({SITE}/trends/): by season, week, penalty type, home vs road, cost of penalties
- [Guide and FAQ]({SITE}/guide/): methodology, glossary, common questions with live numbers
- [Data downloads]({SITE}/dataset/): CSVs, free to use with credit

## Notes for accurate use
- Counts are accepted penalties, regular season only.
- Statistics are tracked by crew chief; play-by-play doesn't say which official threw a flag.
- Early-season samples are small; patterns, not motives.
"""
    (ROOT / 'llms.txt').write_text(llms, encoding='utf-8')


if __name__ == '__main__':
    crew_pages()
    team_pages()
    assignments_page()
    trends_page()
    dataset_page()
    guide_page()
    home_summary()
    home_prefill()
    sitemap_and_llms()
    print(f'✓ static pages: {len(SITEMAP)} · sitemap.xml · llms.txt · data/exports/*.csv · home summary')
