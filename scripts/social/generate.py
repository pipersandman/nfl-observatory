#!/usr/bin/env python3
"""
Weekly social posts for the NFL Officiating Observatory
=======================================================
Renders 1080x1350 post images (+ captions) from the same data as the website.

Series (repeatable names / hashtags):
  forecast   #FlagForecast     Tue   Crews are in: most flags expected this week
  watch      #FlagWatch        pre   Single-game preview (writes a projection snapshot)
  final      #FinalFlags       post  Single-game recap: what was called (vs projection if snapshotted)
  laundry    #LaundryDay       Mon   Weekly totals vs last week and vs same week last year
  team       #TeamLaundry      Wed   One team's weekly discipline card
  division   #DivisionLaundry  Wed   A division's four teams, most flags first
  magnets    #FlagMagnets      Sat   Most-penalized players this season
  hood       #UnderTheHood     Fri   New question each week (deep-dive template)

Usage (from repo root, venv active):
  pip install playwright && python -m playwright install chromium     # once
  python scripts/social/generate.py --week 4 --all                       # everything for a week
  python scripts/social/generate.py --kind watch --game 2026_04_ATL_NO
  python scripts/social/generate.py --kind final --week 4                # every game that week
  python scripts/social/generate.py --kind team --team DAL --week 4
Output: social/output/{season}-week-NN/*.png + captions.md
"""

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
DATA = ROOT / 'frontend' / 'data'
OUT = ROOT / 'social' / 'output'
SNAP = ROOT / 'social' / 'snapshots'
sys.path.insert(0, str(HERE))
from colors import matchup_colors  # noqa: E402

SITE = 'nflobservatory.com'
NAME_FIXES = {'Ronald Torbert': 'Ron Torbert', 'Adrian Hall': 'Adrian Hill'}
FONTS = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700"
         "&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600;700&display=swap")
UMBRELLA = '#FlagData'
SERIES = {
    'forecast': ('FLAG FORECAST', '#FlagForecast'),
    'watch': ('FLAG WATCH', '#FlagWatch'),
    'final': ('FINAL FLAGS', '#FinalFlags'),
    'laundry': ('LAUNDRY DAY', '#LaundryDay'),
    'team': ('TEAM LAUNDRY', '#TeamLaundry'),
    'division': ('DIVISION LAUNDRY', '#DivisionLaundry'),
    'magnets': ('FLAG MAGNETS', '#FlagMagnets'),
    'hood': ('UNDER THE HOOD', '#UnderTheHood'),
}
TEAM_NAMES = {}


# =============================================================================
# Data
# =============================================================================

class Data:
    def __init__(self, season):
        import nflreadpy as nfl
        self.season = season
        self.sched = nfl.load_schedules([season - 1, season]).to_pandas()
        self.sched = self.sched[self.sched['game_type'] == 'REG'].copy()
        self.sched['referee'] = self.sched['referee'].replace(NAME_FIXES)
        frames = []
        for s in (season - 1, season):
            try:
                frames.append(nfl.load_pbp(s).to_pandas())
            except Exception as e:
                print(f'   ⚠️  pbp {s}: {e}')
        pbp = pd.concat(frames, ignore_index=True)
        pbp = pbp[pbp['season_type'] == 'REG']
        self.plays = pbp
        pen = pbp[(pbp['penalty'] == 1) & pbp['penalty_team'].notna()].copy()
        pen['penalty_yards'] = pd.to_numeric(pen['penalty_yards'], errors='coerce').fillna(0).abs()
        self.pen = pen
        self.played = pbp[['game_id', 'season', 'week']].drop_duplicates('game_id')
        t = nfl.load_teams().to_pandas()
        for r in t.itertuples():
            TEAM_NAMES[r.team_abbr] = r.team_name
        self.divisions = t.set_index('team_abbr')['team_division'].to_dict()

    def game_rows(self):
        g = self.played.merge(self.sched[['game_id', 'home_team', 'away_team', 'home_score', 'away_score',
                                          'referee', 'gameday', 'weekday', 'gametime']], on='game_id')
        cnt = self.pen.groupby('game_id').agg(flags=('penalty_team', 'size'), yards=('penalty_yards', 'sum'))
        g = g.merge(cnt, on='game_id', how='left').fillna({'flags': 0, 'yards': 0})
        return g

    def team_games(self):
        g = self.game_rows()
        per = self.pen.groupby(['game_id', 'penalty_team']).agg(f=('penalty_team', 'size'), y=('penalty_yards', 'sum')).reset_index()
        rows = []
        for side, opp in (('home', 'away'), ('away', 'home')):
            x = g.assign(team=g[f'{side}_team'], opp=g[f'{opp}_team'], is_home=side == 'home')
            rows.append(x)
        tg = pd.concat(rows, ignore_index=True)
        tg = tg.merge(per.rename(columns={'penalty_team': 'team'}), on=['game_id', 'team'], how='left').fillna({'f': 0, 'y': 0})
        return tg


def load_previews():
    latest = json.loads((DATA / 'previews' / 'latest.json').read_text())
    files = [w['file'] for w in latest.get('weeks', [])] or [latest['file']]
    return [json.loads((DATA / f).read_text()) for f in files]


# =============================================================================
# Helpers
# =============================================================================

e = html.escape


def pct(cur, base):
    if base in (None, 0) or cur is None:
        return None
    return (cur - base) / base * 100


def badge(cur, base, suffix=''):
    p = pct(cur, base)
    if p is None:
        return ''
    cls = 'flat' if abs(p) < 2 else ('up' if p > 0 else 'down')
    arrow = '●' if cls == 'flat' else ('▲' if p > 0 else '▼')
    val = f'{abs(p):.1f}' if abs(p) < 10 else f'{abs(p):.0f}'
    return f"<span class='badge {cls}'>{arrow} {val}%{suffix}</span>"


def short_type(t):
    return t.replace('Offensive ', 'Off. ').replace('Defensive ', 'Def. ')


def frame(kind, kicker_extra, body, foot_right=''):
    label, tag = SERIES[kind]
    css = (HERE / 'base.css').read_text()
    return f"""<html><head><meta charset='utf-8'><link href='{FONTS}' rel='stylesheet'><style>{css}</style></head>
<body><div class='card'><div class='in'>
<div class='series'><span class='kick'>{label}{' · ' + e(kicker_extra) if kicker_extra else ''}</span><span class='tag'>{tag}</span></div>
{body}
<div class='foot'><div class='brand'><span class='flag'><i></i></span>{SITE}</div><span>{foot_right}</span></div>
</div></div></body></html>"""


class Writer:
    def __init__(self, season, week):
        self.dir = OUT / f'{season}-week-{week:02d}'
        self.dir.mkdir(parents=True, exist_ok=True)
        self.items = []

    def add(self, name, html_doc, caption, alt):
        (self.dir / f'{name}.html').write_text(html_doc, encoding='utf-8')
        self.items.append((name, caption, alt))

    def render(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={'width': 1080, 'height': 1350})
            for name, _, _ in self.items:
                pg.goto((self.dir / f'{name}.html').resolve().as_uri())
                try:
                    pg.wait_for_load_state('networkidle', timeout=8000)
                except Exception:
                    pass
                pg.wait_for_timeout(250)
                pg.screenshot(path=str(self.dir / f'{name}.png'))
                (self.dir / f'{name}.html').unlink()
            b.close()
        md = [f'# Posts · {self.dir.name}\n', f'Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. '
              'Review every number before posting.\n']
        for name, cap, alt in self.items:
            md.append(f'\n## {name}.png\n\n**Caption**\n\n{cap}\n\n**Alt text**\n\n{alt}\n')
        cap_path = self.dir / 'captions.md'
        existing = cap_path.read_text() if cap_path.exists() else ''
        # append new items to an existing captions file for the week
        cap_path.write_text((existing + '\n'.join(md[2:])) if existing else ''.join(md[:2]) + '\n'.join(md[2:]))
        print(f'   ✓ {len(self.items)} posts → {self.dir.relative_to(ROOT)}')


def tags(kind, *extra):
    return ' '.join([SERIES[kind][1], UMBRELLA, '#NFL'] + [x for x in extra if x])


def link(kind, week):
    return f'https://{SITE}/?utm_source=social&utm_medium=post&utm_campaign={kind}-wk{week}'


# =============================================================================
# Templates
# =============================================================================

def t_forecast(w, pv):
    league = pv['model']['leagueAveragePerGame']
    games = sorted(pv['games'], key=lambda g: -g['projection']['total'])[:6]
    rows = ''.join(f"""<div class='row'><span class='rk'>{i + 1}</span>
        <span class='m'>{g['awayTeam']['abbr']} @ {g['homeTeam']['abbr']}<small>{e((g['crew'] or {}).get('name', 'Crew TBA'))} · {g['weekday'][:3]}</small></span>
        <span class='n'>{g['projection']['total']:.1f}<small class='{'up' if g['projection']['total'] > league else 'down'}'>{'▲' if g['projection']['total'] > league else '▼'} {abs(pct(g['projection']['total'], league)):.0f}%</small></span></div>"""
                   for i, g in enumerate(games))
    a = pv.get('assignments') or {}
    body = f"""<div class='h'>Most flags<br>expected</div>
<div class='sub'>Week {pv['week']} projected accepted penalties · league avg {league}</div>{rows}"""
    top = games[0]
    cap = (f"🚩 Week {pv['week']} Flag Forecast: {top['awayTeam']['abbr']} @ {top['homeTeam']['abbr']} projects as the most flag-heavy game "
           f"({top['projection']['total']:.1f} vs a {league} league average)"
           f"{' with ' + top['crew']['name'] + ' calling it' if top.get('crew') else ''}.\n\n"
           f"All {len(pv['games'])} previews → {link('forecast', pv['week'])}\n\n{tags('forecast')}")
    alt = (f"Week {pv['week']} Flag Forecast. Top projected penalty totals: " +
           '; '.join(f"{g['awayTeam']['abbr']} at {g['homeTeam']['abbr']} {g['projection']['total']:.1f}" for g in games) + '.')
    w.add('flag-forecast', frame('forecast', f"WEEK {pv['week']}", body,
                                 f"Crews {a.get('assigned', 0)}/{a.get('games', 0)} assigned"), cap, alt)


def t_watch(w, pv, g):
    p, league = g['projection'], pv['model']['leagueAveragePerGame']
    hc, ac = matchup_colors(g['homeTeam']['abbr'], g['awayTeam']['abbr'])
    A, H = g['awayTeam']['abbr'], g['homeTeam']['abbr']
    types = [r for r in g['byType'] if r['type'] != 'Other'][:5]
    mx = max(r['total'] for r in types) or 1
    trows = ''.join(f"<div class='typ'><span>{e(short_type(r['type']))}</span><span class='tb'><span><i class='cur' style='width:{r['total'] / mx * 100:.0f}%'></i></span></span><b style='text-align:right'>{r['total']:.1f}</b></div>" for r in types)
    crew = g.get('crew')
    crew_line = f"Crew: {e(crew['name'])}" if crew else 'Crew: TBA'
    when = f"{(g.get('weekday') or '')[:3]} {g.get('gameday', '')[5:].replace('-', '/')}"
    if g.get('gametime'):
        hh, mm = (int(x) for x in g['gametime'].split(':'))
        when += f" · {(hh + 11) % 12 + 1}:{mm:02d} {'PM' if hh >= 12 else 'AM'} ET"
    drv = p['drivers'][0]['value'] if crew else None
    chips = ''.join(f"<span class='chip'>{c}</span>" for c in [
        e(crew_line),
        f"Crew effect {drv:+.1f} flags" if drv is not None else None,
        f"League avg {league}",
        g.get('network') and e(g['network']),
    ] if c)
    body = f"""<div class='h' style='font-size:120px'>{A} @ {H}</div>
<div class='sub'>{e(when)} · {e(crew_line)}</div>
<div style='display:flex;align-items:flex-end;gap:28px'><div class='big'>{p['total']:.1f}</div>
<div style='padding-bottom:20px'>{badge(p['total'], league, ' vs avg')}<div class='sub' style='margin:12px 0 0;font-size:28px'>projected flags · likely {p['range'][0]}–{p['range'][1]}</div></div></div>
<div class='split' style='margin:38px 0 40px'><span>{A} {p['away']:.1f}</span><div class='bar'><i style='flex:{p['away']};background:{ac}'></i><i style='flex:{p['home']};background:{hc}'></i></div><span>{p['home']:.1f} {H}</span></div>
<div class='tt'>Most likely calls</div>{trows}<div style='margin-top:18px'>{chips}</div>"""
    cap = (f"🚩 {A} @ {H} — Flag Watch\n\nProjected {p['total']:.1f} flags (likely {p['range'][0]}–{p['range'][1]}), "
           f"{abs(pct(p['total'], league)):.0f}% {'above' if p['total'] > league else 'below'} the league average."
           f"{' ' + crew['name'] + ' has the crew.' if crew else ''}\n\nFull game report → {link('watch', g['week'])}\n\n"
           f"{tags('watch', '#' + A + 'vs' + H)}")
    alt = (f"Flag Watch for {A} at {H}: projected {p['total']:.1f} accepted penalties, {p['away']:.1f} on {A} and {p['home']:.1f} on {H}. "
           f"Most likely: " + ', '.join(f"{r['type']} {r['total']:.1f}" for r in types) + '.')
    w.add(f"flag-watch-{A.lower()}-{H.lower()}", frame('watch', f"WEEK {g['week']}", body, 'Full report on site'), cap, alt)
    # Freeze the projection the first time a game is posted (recaps compare against it)
    SNAP.mkdir(parents=True, exist_ok=True)
    sp = SNAP / f"{g['season']}-week-{g['week']:02d}.json"
    snap = json.loads(sp.read_text()) if sp.exists() else {}
    if g['gameId'] not in snap:
        snap[g['gameId']] = {'total': p['total'], 'home': p['home'], 'away': p['away'], 'range': p['range'],
                             'byType': {r['type']: r['total'] for r in g['byType']},
                             'crew': crew['name'] if crew else None,
                             'snapshotAt': datetime.now(timezone.utc).isoformat(timespec='seconds')}
        sp.write_text(json.dumps(snap, indent=2))


def t_final(w, d, game_id, season_avg):
    g = d.game_rows().set_index('game_id').loc[game_id]
    A, H = g['away_team'], g['home_team']
    hc, ac = matchup_colors(H, A)
    pen = d.pen[d.pen['game_id'] == game_id]
    fa, fh = int((pen['penalty_team'] == A).sum()), int((pen['penalty_team'] == H).sum())
    ya, yh = int(pen.loc[pen['penalty_team'] == A, 'penalty_yards'].sum()), int(pen.loc[pen['penalty_team'] == H, 'penalty_yards'].sum())
    total = fa + fh
    vc = pen['penalty_type'].value_counts().head(5)
    mx = vc.max() if len(vc) else 1
    trows = ''.join(f"<div class='typ'><span>{e(short_type(t))}</span><span class='tb'><span><i class='cur' style='width:{n / mx * 100:.0f}%'></i></span></span><b style='text-align:right'>{n}</b></div>" for t, n in vc.items())
    pl = pen[pen['penalty_player_name'].notna()]['penalty_player_name'].value_counts()
    top_player = f"{pl.index[0]} ({pl.iloc[0]})" if len(pl) and pl.iloc[0] > 1 else None
    snap_file = SNAP / f"{d.season}-week-{int(g['week']):02d}.json"
    snap = json.loads(snap_file.read_text()).get(game_id) if snap_file.exists() else None
    crew = g['referee'] if isinstance(g['referee'], str) else None
    proj_html = ''
    if snap:
        inside = snap['range'][0] <= total <= snap['range'][1]
        proj_html = (f"<span class='chip'>Projected {snap['total']:.1f} → actual {total} "
                     f"{'✓ in range' if inside else '✗ outside range'}</span>")
    score = '' if pd.isna(g['home_score']) else f"{A} {int(g['away_score'])} – {int(g['home_score'])} {H}"
    body = f"""<div class='h' style='font-size:120px'>{A} @ {H}</div>
<div class='sub'>{e(score)}{' · ' + e(crew) if crew else ''}</div>
<div style='display:flex;align-items:flex-end;gap:28px'><div class='big'>{total}</div>
<div style='padding-bottom:20px'>{badge(total, season_avg, ' vs avg')}<div class='sub' style='margin:12px 0 0;font-size:28px'>accepted penalties · {ya + yh} yards</div></div></div>
<div class='split' style='margin:38px 0 10px'><span>{A} {fa}</span><div class='bar'><i style='flex:{max(fa, .3)};background:{ac}'></i><i style='flex:{max(fh, .3)};background:{hc}'></i></div><span>{fh} {H}</span></div>
<div class='note' style='margin:0 0 34px;display:flex;justify-content:space-between'><span>{ya} yds</span><span>{yh} yds</span></div>
<div class='tt'>What was called</div>{trows}
<div style='margin-top:14px'>{proj_html}{f"<span class='chip'>Most flagged: {e(top_player)}</span>" if top_player else ''}<span class='chip'>{d.season} avg {season_avg:.1f}/game</span></div>"""
    proj_txt = f" We projected {snap['total']:.1f}." if snap else ''
    cap = (f"🏁 {A} @ {H} — Final Flags\n\n{total} accepted penalties for {ya + yh} yards ({A} {fa}, {H} {fh})"
           f"{', with ' + crew + ' calling it' if crew else ''}. Top call: {vc.index[0] if len(vc) else '—'} ({vc.iloc[0] if len(vc) else 0})."
           f"{proj_txt}\n\n"
           f"Every game, every crew → {link('final', int(g['week']))}\n\n{tags('final', '#' + A + 'vs' + H)}")
    alt = (f"Final Flags for {A} at {H}: {total} accepted penalties, {fa} on {A} and {fh} on {H}, {ya + yh} total yards. "
           f"Most called: " + ', '.join(f'{t} {n}' for t, n in vc.items()) + '.')
    w.add(f"final-flags-{A.lower()}-{H.lower()}", frame('final', f"WEEK {int(g['week'])}", body, 'Full game log on site'), cap, alt)
    return total


def t_laundry(w, d, week):
    g = d.game_rows()
    S = d.season
    def rate(mask):
        x = g[mask]
        return (x['flags'].mean() if len(x) else None, x['yards'].mean() if len(x) else None, len(x))
    wk, wk_y, wk_n = rate((g['season'] == S) & (g['week'] == week))
    prev, prev_y, _ = rate((g['season'] == S) & (g['week'] == week - 1))
    ly, ly_y, _ = rate((g['season'] == S - 1) & (g['week'] == week))
    std, std_y, std_n = rate((g['season'] == S) & (g['week'] <= week))
    lstd, lstd_y, _ = rate((g['season'] == S - 1) & (g['week'] <= week))
    games = g[(g['season'] == S) & (g['week'] == week)].sort_values('flags', ascending=False)
    hi, lo = games.iloc[0], games.iloc[-1]
    tg = d.team_games()
    tw = tg[(tg['season'] == S) & (tg['week'] == week)].sort_values('f', ascending=False)
    tm = tw.iloc[0]
    sched_n = len(d.sched[(d.sched['season'] == S) & (d.sched['week'] == week)])
    pending = sched_n - wk_n
    tile = lambda l, v, s: f"<div class='tile'><div class='l'>{l}</div><div class='v'>{v}</div><div class='s'>{s}</div></div>"
    body = f"""<div class='h'>Week {week}<br>by the flags</div>
<div class='sub'>{wk_n} games{f' · {pending} still to play' if pending > 0 else ''} · {int(games['flags'].sum())} accepted penalties</div>
<div style='display:flex;align-items:flex-end;gap:26px;margin-bottom:30px'><div class='big' style='font-size:190px'>{wk:.1f}</div>
<div style='padding-bottom:18px' class='sub'>flags per game<br>{wk_y:.0f} penalty yards per game</div></div>
<div class='tiles three'>
{tile('vs Week ' + str(week - 1), badge(wk, prev), f'{prev:.1f} per game') if prev else ''}
{tile(f'vs {S - 1} Week {week}', badge(wk, ly), f'{ly:.1f} per game') if ly else ''}
{tile(f'{S} so far vs {S - 1}', badge(std, lstd), f'{std:.1f} vs {lstd:.1f} thru Wk {week}') if lstd else ''}
</div>
<div class='tiles three'>
{tile('Most flags', f"{int(hi['flags'])}", f"{hi['away_team']} @ {hi['home_team']} · {e(str(hi['referee']).split()[-1])}")}
{tile('Fewest flags', f"{int(lo['flags'])}", f"{lo['away_team']} @ {lo['home_team']} · {e(str(lo['referee']).split()[-1])}")}
{tile('Most-flagged team', f"{int(tm['f'])}", f"{tm['team']} vs {tm['opp']}")}
</div>"""
    cap = (f"🧺 Laundry Day — Week {week}\n\n{wk:.1f} flags per game this week "
           f"({'up' if prev and wk > prev else 'down'} from {prev:.1f} in Week {week - 1}; {S - 1} Week {week}: {ly:.1f}). "
           f"{S} is running {abs(pct(std, lstd)):.0f}% {'above' if std > lstd else 'below'} {S - 1} through Week {week}.\n\n"
           f"Most flags: {hi['away_team']} @ {hi['home_team']} ({int(hi['flags'])}). Fewest: {lo['away_team']} @ {lo['home_team']} ({int(lo['flags'])}).\n\n"
           f"Full breakdown → {link('laundry', week)}\n\n{tags('laundry')}")
    alt = (f"Laundry Day Week {week}: {wk:.1f} accepted penalties per game across {wk_n} games. Previous week {prev:.1f}; "
           f"same week last season {ly:.1f}; season to date {std:.1f} vs {lstd:.1f} last season. Most flags {int(hi['flags'])} in "
           f"{hi['away_team']} at {hi['home_team']}; fewest {int(lo['flags'])} in {lo['away_team']} at {lo['home_team']}.")
    w.add('laundry-day', frame('laundry', f'WEEK {week}', body, 'Every game, every crew on site'), cap, alt)
    return std


def t_team(w, d, team, week):
    tg = d.team_games()
    S = d.season
    rows = tg[tg['team'] == team]
    cur = rows[rows['season'] == S]
    last = rows[rows['season'] == S - 1]
    this_wk = cur[cur['week'] == week]
    season_rank = (tg[tg['season'] == S].groupby('team')['f'].mean().rank(ascending=False, method='min'))
    last_rank = (tg[tg['season'] == S - 1].groupby('team')['f'].mean().rank(ascending=False, method='min'))
    pg, lpg = cur['f'].mean(), last['f'].mean() if len(last) else None
    drawn = (cur.merge(tg[['game_id', 'team', 'f']].rename(columns={'team': 'opp', 'f': 'd'}), on=['game_id', 'opp'])['d'].mean())
    tp = d.pen[(d.pen['penalty_team'] == team) & (d.pen['season'] == S)]
    top_type = tp['penalty_type'].value_counts()
    wk_line = ''
    if len(this_wk):
        r = this_wk.iloc[0]
        wk_line = f"Week {week}: {int(r['f'])} flags {'vs' if r['is_home'] else '@'} {r['opp']}"
    tile = lambda l, v, s: f"<div class='tile'><div class='l'>{l}</div><div class='v'>{v}</div><div class='s'>{s}</div></div>"
    name = TEAM_NAMES.get(team, team)
    rk, lrk = int(season_rank.get(team, 0)), int(last_rank.get(team, 0)) if team in last_rank else None
    headline = (f"From #{lrk}<br>to #{rk}" if lrk and abs(lrk - rk) >= 8 else f"#{rk} most<br>penalized")
    body = f"""<div class='h'>{headline}</div>
<div class='sub'>{e(name)} · {S} through Week {week}{' · ' + wk_line if wk_line else ''}</div>
<div class='tiles'>
{tile(f'{S} flags / game', f'{pg:.1f}', f"{S - 1}: {lpg:.1f} {badge(pg, lpg)}" if lpg else '')}
{tile('Flag margin', f"{drawn - pg:+.1f}", 'drawn minus committed per game')}
{tile('Most common', e(short_type(top_type.index[0])) if len(top_type) else '—', f"{int(top_type.iloc[0])} this season" if len(top_type) else '')}
{tile('Penalty yards / game', f"{cur['y'].mean():.0f}", f"rank #{rk} of 32 in flags")}
</div>"""
    cap = (f"🧺 Team Laundry: {name}\n\n{pg:.1f} flags per game in {S} (#{rk} most penalized)"
           f"{f', vs {lpg:.1f} in {S - 1} (#{lrk})' if lpg else ''}. Flag margin {drawn - pg:+.1f} per game.\n\n"
           f"Full team profile → {link('team', week)}\n\n{tags('team', '#' + team)}")
    alt = f"Team Laundry for the {name}: {pg:.1f} accepted penalties per game in {S}, ranked {rk} most penalized of 32."
    w.add(f'team-laundry-{team.lower()}', frame('team', team, body, 'Every team on site'), cap, alt)


def t_division(w, d, division, week):
    tg = d.team_games()
    S = d.season
    teams = [t for t, dv in d.divisions.items() if dv == division and t in set(tg['team'])]
    cur = tg[(tg['season'] == S)].groupby('team')['f'].mean()
    last = tg[(tg['season'] == S - 1)].groupby('team')['f'].mean()
    order = sorted(teams, key=lambda t: -cur.get(t, 0))
    rows = ''.join(f"""<div class='row'><span class='rk'>{i + 1}</span><span class='m'>{e(TEAM_NAMES.get(t, t))}<small>{S - 1}: {last.get(t, float('nan')):.1f} per game</small></span>
        <span class='n'>{cur.get(t, 0):.1f}<small>{badge(cur.get(t), last.get(t))}</small></span></div>""" for i, t in enumerate(order))
    body = f"<div class='h'>{e(division)}</div><div class='sub'>Flags per game, {S} through Week {week} · most first</div>{rows}"
    cap = (f"🧺 Division Laundry: {division}\n\nMost penalized: {TEAM_NAMES.get(order[0], order[0])} ({cur.get(order[0]):.1f}/game). "
           f"Cleanest: {TEAM_NAMES.get(order[-1], order[-1])} ({cur.get(order[-1]):.1f}/game).\n\n{link('division', week)}\n\n{tags('division')}")
    alt = f"Division Laundry for the {division}: " + '; '.join(f"{TEAM_NAMES.get(t, t)} {cur.get(t, 0):.1f} flags per game" for t in order) + '.'
    w.add(f"division-laundry-{division.lower().replace(' ', '-')}", frame('division', f'WEEK {week}', body, 'All 8 divisions on site'), cap, alt)


def t_magnets(w, d, week):
    S = d.season
    p = d.pen[(d.pen['season'] == S) & d.pen['penalty_player_name'].notna()]
    top = (p.groupby(['penalty_player_name', 'penalty_team']).agg(n=('penalty_type', 'size'), y=('penalty_yards', 'sum'))
           .reset_index().sort_values(['n', 'y'], ascending=False).head(6))
    rows = ''
    for i, r in enumerate(top.itertuples()):
        t = p[(p['penalty_player_name'] == r.penalty_player_name) & (p['penalty_team'] == r.penalty_team)]['penalty_type'].value_counts()
        rows += (f"<div class='row'><span class='rk'>{i + 1}</span><span class='m'>{e(r.penalty_player_name)} <span class='dim' style='font-weight:400'>{r.penalty_team}</span>"
                 f"<small>{e(', '.join(f'{short_type(k)} ×{v}' if v > 1 else short_type(k) for k, v in t.head(2).items()))}</small></span>"
                 f"<span class='n'>{r.n}<small class='dim'>{int(r.y)} yds</small></span></div>")
    body = f"<div class='h'>Flag<br>magnets</div><div class='sub'>Most accepted penalties, {S} through Week {week}</div>{rows}"
    lead = top.iloc[0]
    cap = (f"🧲 Flag Magnets: {lead['penalty_player_name']} ({lead['penalty_team']}) leads the league with {lead['n']} accepted penalties "
           f"through Week {week}.\n\n{link('magnets', week)}\n\n{tags('magnets')}")
    alt = 'Flag Magnets, most penalized players: ' + '; '.join(f"{r.penalty_player_name} {r.penalty_team} {r.n}" for r in top.itertuples()) + '.'
    w.add('flag-magnets', frame('magnets', f'WEEK {week}', body, 'Watchlists for every game on site'), cap, alt)


def t_hood(w, week, spec):
    """New-question template. spec = {question, stat, stat_label, bars:[(label, value, highlight)], unit,
    takeaway, method, slug}"""
    mx = max(v for _, v, _ in spec['bars']) or 1
    bars = ''.join(f"<div class='hbar'><span style='background:none;height:auto;font-size:32px'>{e(l)}</span>"
                   f"<span><i class='{'cur' if hi else 'hist'}' style='width:{v / mx * 100:.0f}%'></i></span>"
                   f"<b style='text-align:right'>{v:.{spec.get('decimals', 1)}f}{spec.get('unit', '')}</b></div>"
                   for l, v, hi in spec['bars'])
    body = f"""<div class='q'>{e(spec['question'])}</div>
<div style='display:flex;align-items:flex-end;gap:24px;margin-bottom:30px'><div class='big' style='font-size:180px'>{e(spec['stat'])}</div>
<div class='sub' style='padding-bottom:18px;margin:0'>{e(spec['stat_label'])}</div></div>
{bars}
<div class='sub' style='margin:22px 0 0;color:#ecebe7;font-size:32px'>{e(spec['takeaway'])}</div>
<div class='note'>{e(spec['method'])}</div>"""
    cap = f"🔎 Under the Hood: {spec['question']}\n\n{spec['takeaway']}\n\n{link('hood', week)}\n\n{tags('hood')}"
    alt = f"Under the Hood. {spec['question']} " + '; '.join(f'{l}: {v:.1f}{spec.get("unit", "")}' for l, v, _ in spec['bars']) + f'. {spec["takeaway"]}'
    w.add(f"under-the-hood-{spec['slug']}", frame('hood', f'WEEK {week}', body, 'Method on site'), cap, alt)


def hood_close_games(d):
    """Example question: do refs swallow the whistle late in close games? (penalties per 100 plays)"""
    pl = d.plays[d.plays['qtr'].between(1, 4) & d.plays['play_type'].notna()]
    pl = pl.assign(close=pl['score_differential'].abs() <= 8)
    r = pl.groupby(['qtr', 'close'])['penalty'].mean() * 100
    q4c, q4n = r.get((4, True)), r.get((4, False))
    q13c = pl[(pl['qtr'] <= 3) & pl['close']]['penalty'].mean() * 100
    seasons = sorted(pl['season'].unique())
    return {
        'slug': 'late-close-games',
        'question': 'Do refs swallow the whistle late in close games?',
        'stat': f"{(q4c / q13c - 1) * 100:+.0f}%",
        'stat_label': 'penalty rate in one-score 4th quarters vs one-score Q1–Q3',
        'bars': [('Q1–Q3, one-score game', q13c, False), ('Q4, one-score game', q4c, True), ('Q4, not close', q4n, False)],
        'unit': '', 'decimals': 1,
        'takeaway': (f"Flags per 100 plays {'drop' if q4c < q13c else 'rise'} in tight fourth quarters "
                     f"({q13c:.1f} → {q4c:.1f})."),
        'method': f"Regular season {seasons[0]}–{seasons[-1]}, all plays; one-score = within 8 points. Accepted penalties per 100 plays.",
    }


# =============================================================================
# Main
# =============================================================================

def main():
    ap = argparse.ArgumentParser(description='Generate weekly social posts')
    ap.add_argument('--season', type=int, default=datetime.now().year)
    ap.add_argument('--week', type=int, help='Week for recaps / reports (default: last completed week)')
    ap.add_argument('--kind', choices=list(SERIES), action='append')
    ap.add_argument('--all', action='store_true', help='Every post type for the week')
    ap.add_argument('--game', help='Game id for watch/final, e.g. 2026_04_ATL_NO')
    ap.add_argument('--team', action='append', help='Team(s) for team cards (default: 3 most notable)')
    ap.add_argument('--division', action='append')
    args = ap.parse_args()
    kinds = set(SERIES) if args.all else set(args.kind or [])
    if not kinds:
        ap.error('pick --kind (repeatable) or --all')

    print('\n📣 Social posts')
    d = Data(args.season)
    played_cur = d.played[d.played['season'] == args.season]
    week = args.week or int(played_cur['week'].max())
    w = Writer(args.season, week)

    previews = load_previews()
    season_avg = d.game_rows().query('season == @args.season')['flags'].mean()

    if 'forecast' in kinds:
        full = next((p for p in previews if not p.get('remainingOnly')), previews[-1])
        wf = Writer(args.season, full['week']); t_forecast(wf, full); wf.render()
    if 'watch' in kinds:
        for pv in previews:
            for g in pv['games']:
                if args.game and g['gameId'] != args.game:
                    continue
                ww = Writer(args.season, g['week']); t_watch(ww, pv, g); ww.render()
    if 'final' in kinds:
        ids = [args.game] if args.game else d.game_rows().query('season == @args.season and week == @week')['game_id']
        for gid in ids:
            t_final(w, d, gid, season_avg)
    if 'laundry' in kinds:
        t_laundry(w, d, week)
    if 'team' in kinds:
        teams = args.team
        if not teams:   # default: the 3 biggest movers vs last season
            tg = d.team_games()
            cur = tg[tg['season'] == args.season].groupby('team')['f'].mean()
            last = tg[tg['season'] == args.season - 1].groupby('team')['f'].mean()
            teams = list((cur - last).abs().sort_values(ascending=False).head(3).index)
        for t in teams:
            t_team(w, d, t, week)
    if 'division' in kinds:
        divs = args.division or ['AFC East', 'AFC North', 'AFC South', 'AFC West', 'NFC East', 'NFC North', 'NFC South', 'NFC West'][week % 8: week % 8 + 1]
        for dv in divs:
            t_division(w, d, dv, week)
    if 'magnets' in kinds:
        t_magnets(w, d, week)
    if 'hood' in kinds:
        t_hood(w, week, hood_close_games(d))
    if w.items:
        w.render()


if __name__ == '__main__':
    main()
