"""
Captions: hook first, facts second, one question to spark replies.
=================================================================
Each post's facts are checked for the most interesting STORY ANGLE (record game,
lopsided split, one call piling up, a crew that swings the projection...).
The strongest angle becomes the hook. Each angle has several wordings that rotate
by week/game, so the feed never reads the same twice. Every number comes straight
from the data; nothing is invented.

Ground rules baked in:
- Patterns, never motives: no "rigged", "biased", "agenda" language about officials.
- Small samples get flagged ("4 games in").
- Questions invite opinions about calls and teams, not attacks on people.
"""

import hashlib

UMBRELLA = '#FlagData'


def pick(options, key):
    """Stable rotation: same post always gets the same wording, different posts differ."""
    h = int(hashlib.md5(str(key).encode()).hexdigest(), 16)
    return options[h % len(options)]


def tags(series_tag, *extra):
    return ' '.join([series_tag, UMBRELLA, '#NFL'] + [x for x in extra if x])


def pct(a, b):
    return None if not b else (a - b) / b * 100


def _fmt_pct(p):
    return f'{abs(p):.0f}%'


# -----------------------------------------------------------------------------
# Final Flags (one game, after)
# -----------------------------------------------------------------------------

def final_flags(f, url):
    """f: A, H, total, fa, fh, yards, crew, season_avg, season_max_before, top_type, top_type_n,
    top_player, top_player_n, projected (or None), proj_range, week, game_id"""
    A, H, k = f['A'], f['H'], f['game_id']
    hooks = []
    if f['season_max_before'] is not None and f['total'] > f['season_max_before']:
        hooks.append((100, pick([
            f"{f['total']} flags. No game has had more this season.",
            f"New season high: {f['total']} accepted penalties in {A} @ {H}.",
            f"The laundry basket overflowed. {f['total']} flags — a {f['season']} high.",
        ], k)))
    if f['projected'] is not None:
        miss = f['total'] - f['projected']
        inside = f['proj_range'][0] <= f['total'] <= f['proj_range'][1]
        if abs(miss) >= 5:
            hooks.append((90, pick([
                f"We projected {f['projected']:.0f}. The officials threw {f['total']}.",
                f"Our number: {f['projected']:.1f}. Reality: {f['total']}. {'Way more' if miss > 0 else 'Way fewer'} flags than expected.",
            ], k)))
        elif inside:
            hooks.append((60, pick([
                f"Called it: we projected {f['projected']:.1f} flags. Final count: {f['total']}.",
                f"Projection {f['projected']:.1f}. Actual {f['total']}. Right in the window.",
            ], k)))
    lo, hi = min(f['fa'], f['fh']), max(f['fa'], f['fh'])
    heavy, light = (A, H) if f['fa'] > f['fh'] else (H, A)
    if hi >= 2 * max(lo, 1) and hi - lo >= 5:
        hooks.append((85, pick([
            f"{heavy}: {hi} flags. {light}: {lo}. Same field, same crew.",
            f"One sideline kept getting flagged. {heavy} {hi}, {light} {lo}.",
            f"{hi} to {lo}. {heavy} couldn't get out of its own way.",
        ], k)))
    if f['top_type_n'] >= 4:
        hooks.append((75, pick([
            f"{f['top_type_n']} {f['top_type']} calls. In one game.",
            f"The call of the day: {f['top_type']}. Thrown {f['top_type_n']} times.",
        ], k)))
    if f['top_player_n'] and f['top_player_n'] >= 3:
        hooks.append((70, pick([
            f"{f['top_player']} alone was flagged {f['top_player_n']} times.",
            f"{f['top_player_n']} flags on one player: {f['top_player']}.",
        ], k)))
    p = pct(f['total'], f['season_avg'])
    if p is not None and p <= -40:
        hooks.append((65, pick([
            f"Barely any laundry: just {f['total']} flags in {A} @ {H}.",
            f"The cleanest game of the week? {f['total']} flags, {_fmt_pct(p)} under the {f['season']} average.",
        ], k)))
    if p is not None and p >= 35:
        hooks.append((55, pick([
            f"{f['total']} flags — {_fmt_pct(p)} above the {f['season']} average.",
            f"A long afternoon for the yellow flags: {f['total']} accepted penalties.",
        ], k)))
    hooks.append((0, pick([
        f"{A} @ {H} by the flags: {f['total']} accepted penalties.",
        f"Final count from {A} @ {H}: {f['total']} flags, {f['yards']} yards.",
    ], k)))
    hook = max(hooks, key=lambda x: x[0])[1]
    facts = (f"{A} {f['fa']} · {H} {f['fh']} · {f['yards']} penalty yards"
             f"{' · Crew: ' + f['crew'] if f['crew'] else ''}"
             f"{' · Top call: ' + f['top_type'] + ' (' + str(f['top_type_n']) + ')' if f['top_type'] else ''}")
    q = pick([
        "Which call swung it?",
        f"Who earned their flags today, {A} or {H}?",
        "Fair whistle or too many flags?",
        "Which one would you challenge?",
    ], k + 'q')
    return f"🏁 {hook}\n\n{facts}\n\n{q}\n\nEvery game, every crew → {url}\n\n{tags('#FinalFlags', '#' + A + 'vs' + H)}"


# -----------------------------------------------------------------------------
# Flag Watch (one game, before)
# -----------------------------------------------------------------------------

def flag_watch(f, url):
    """f: A, H, total, range, home, away, league, crew, crew_effect, top_type, top_type_val,
    home_rank, away_rank, game_id, primetime"""
    A, H, k = f['A'], f['H'], f['game_id']
    p = pct(f['total'], f['league'])
    hooks = []
    if f['crew'] and f['crew_effect'] is not None and abs(f['crew_effect']) >= 1.0:
        more = f['crew_effect'] > 0
        hooks.append((90, pick([
            f"The crew matters tonight. {f['crew']}'s games run {abs(f['crew_effect']):.1f} flags {'heavier' if more else 'lighter'} than an average crew.",
            f"{f['crew']} has the whistle — and that alone {'adds' if more else 'takes away'} about {abs(f['crew_effect']):.1f} flags.",
        ], k)))
    if p is not None and p >= 8:
        hooks.append((80, pick([
            f"Pack extra laundry: {A} @ {H} projects {f['total']:.1f} flags, {_fmt_pct(p)} over the league average.",
            f"One of the most flag-heavy matchups on the board: {f['total']:.1f} projected.",
        ], k)))
    if p is not None and p <= -8:
        hooks.append((70, pick([
            f"Expect a clean one: {f['total']:.1f} projected flags, {_fmt_pct(p)} under average.",
            f"Low-laundry alert. {A} @ {H} projects just {f['total']:.1f} flags.",
        ], k)))
    for team, rk in ((A, f['away_rank']), (H, f['home_rank'])):
        if rk and rk <= 3:
            hooks.append((75, pick([
                f"{team} comes in as the #{rk} most-penalized team in the league.",
                f"Discipline check: {team} ranks #{rk} in flags per game.",
            ], k + team)))
    hooks.append((0, pick([
        f"{A} @ {H}: {f['total']:.1f} projected flags.",
        f"Flag Watch: {A} @ {H} projects {f['total']:.1f} accepted penalties.",
    ], k)))
    hook = max(hooks, key=lambda x: x[0])[1]
    facts = (f"Projected {f['total']:.1f} (likely {f['range'][0]}–{f['range'][1]}) · {A} {f['away']:.1f} · {H} {f['home']:.1f}"
             f"{' · Crew: ' + f['crew'] if f['crew'] else ''}"
             f"{' · Most likely call: ' + f['top_type'] if f['top_type'] else ''}")
    q = pick([
        f"Over or under {f['range'][0] + (f['range'][1] - f['range'][0]) // 2}.5 flags?",
        f"Which team draws more flags: {A} or {H}?",
        "What's the first flag of the game going to be?",
    ], k + 'q')
    return f"🚩 {hook}\n\n{facts}\n\n{q}\n\nFull game report → {url}\n\n{tags('#FlagWatch', '#' + A + 'vs' + H)}"


# -----------------------------------------------------------------------------
# Flag Forecast (week, before)
# -----------------------------------------------------------------------------

def flag_forecast(f, url):
    """f: week, top (A,H,total,crew), bottom (A,H,total,crew), league, n_games, crews_assigned"""
    t, b, k = f['top'], f['bottom'], f"forecast{f['week']}"
    options = [
        f"Week {f['week']}'s laundry forecast: heaviest in {t['A']} @ {t['H']}, lightest in {b['A']} @ {b['H']}.",
        f"Where the yellow flags fly in Week {f['week']}: {t['A']} @ {t['H']} leads at {t['total']:.1f} projected.",
    ]
    if f.get('crews_assigned'):   # only claim crews are in when they are
        options.append(f"Crews are in. The most flags expected in Week {f['week']}: {t['A']} @ {t['H']} ({t['total']:.1f}).")
    hook = pick(options, k)
    if not f.get('crews_assigned'):
        hook += ' (Crews post Tuesday; numbers update.)'
    crew_line = f" with {t['crew']} calling it" if t.get('crew') else ''
    facts = (f"Top: {t['A']} @ {t['H']} {t['total']:.1f}{crew_line}\n"
             f"Cleanest: {b['A']} @ {b['H']} {b['total']:.1f}{' (' + b['crew'] + ')' if b.get('crew') else ''}\n"
             f"League average: {f['league']}")
    q = pick(["Which game are you expecting a flag-fest from?", "Which crew are you dreading this week?",
              "Agree with the top of the list?"], k + 'q')
    return f"🔮 {hook}\n\n{facts}\n\n{q}\n\nAll {f['n_games']} previews → {url}\n\n{tags('#FlagForecast')}"


# -----------------------------------------------------------------------------
# Laundry Day (week, after)
# -----------------------------------------------------------------------------

def laundry_day(f, url):
    """f: week, season, wk, prev, ly, std, lstd, hi (A,H,flags,crew), lo (...), team (abbr, flags, opp), n_games, pending"""
    k = f"laundry{f['season']}{f['week']}"
    d_prev, d_ly, d_std = pct(f['wk'], f['prev']), pct(f['wk'], f['ly']), pct(f['std'], f['lstd'])
    hooks = []
    if d_prev is not None and abs(d_prev) >= 10:
        hooks.append((abs(d_prev), pick([
            f"Flags {'jumped' if d_prev > 0 else 'dropped'} {_fmt_pct(d_prev)} in Week {f['week']}.",
            f"The officials got {'busier' if d_prev > 0 else 'quieter'}: {f['wk']:.1f} flags per game, {'up' if d_prev > 0 else 'down'} {_fmt_pct(d_prev)} from Week {f['week'] - 1}.",
        ], k)))
    if d_std is not None and abs(d_std) >= 4:
        hooks.append((abs(d_std) * 1.5, pick([
            f"{f['season']} is on pace for {'more' if d_std > 0 else 'fewer'} flags than {f['season'] - 1}: {f['std']:.1f} vs {f['lstd']:.1f} per game through Week {f['week']}.",
            f"Through {f['week']} weeks, flags are {'up' if d_std > 0 else 'down'} {_fmt_pct(d_std)} on last season.",
        ], k)))
    hooks.append((f['hi']['flags'] - f['wk'], pick([
        f"{f['hi']['flags']} flags in {f['hi']['A']} @ {f['hi']['H']}. Then there was everyone else.",
        f"Week {f['week']}'s laundry champion: {f['hi']['A']} @ {f['hi']['H']} with {f['hi']['flags']} flags.",
    ], k)))
    hook = max(hooks, key=lambda x: x[0])[1]
    facts = (f"Week {f['week']}: {f['wk']:.1f} flags/game (Week {f['week'] - 1}: {f['prev']:.1f} · {f['season'] - 1} Week {f['week']}: {f['ly']:.1f})\n"
             f"Most: {f['hi']['A']} @ {f['hi']['H']} {f['hi']['flags']} ({f['hi']['crew']}) · Fewest: {f['lo']['A']} @ {f['lo']['H']} {f['lo']['flags']} ({f['lo']['crew']})\n"
             f"Most-flagged team: {f['team']['abbr']} ({f['team']['flags']} vs {f['team']['opp']})"
             + (f"\n({f['pending']} game still to play)" if f['pending'] else ''))
    q = pick(["Was your team on the right side of the laundry pile?", "Which game had the worst whistle this week?",
              "Too many flags this season, or just right?"], k + 'q')
    return f"🧺 {hook}\n\n{facts}\n\n{q}\n\nFull breakdown → {url}\n\n{tags('#LaundryDay')}"


# -----------------------------------------------------------------------------
# Team Laundry, Division Laundry, Flag Magnets, Under the Hood
# -----------------------------------------------------------------------------

def team_laundry(f, url):
    """f: team, name, season, pg, lpg, rank, lrank, margin, top_type, top_n, week"""
    k = f"team{f['team']}{f['week']}"
    hooks = []
    if f['lrank'] and abs(f['lrank'] - f['rank']) >= 8:
        worse = f['rank'] < f['lrank']
        hooks.append((90, pick([
            f"Last season: #{f['lrank']} most penalized. This season: #{f['rank']}.",
            f"{'What happened?' if worse else 'Cleaned up.'} The {f['name']} went from #{f['lrank']} to #{f['rank']} in flags per game.",
        ], k)))
    if f['margin'] is not None and abs(f['margin']) >= 2.5:
        hooks.append((70, pick([
            f"The {f['name']} {'draw' if f['margin'] > 0 else 'give away'} {abs(f['margin']):.1f} more flags per game than {'they commit' if f['margin'] > 0 else 'they get'}.",
            f"Flag margin: {f['margin']:+.1f} per game. {'Opponents keep getting flagged against them.' if f['margin'] > 0 else 'They keep handing out free yards.'}",
        ], k)))
    hooks.append((0, f"The {f['name']}: {f['pg']:.1f} flags per game in {f['season']} (#{f['rank']})."))
    hook = max(hooks, key=lambda x: x[0])[1]
    last = f"{f['season'] - 1}: {f['lpg']:.1f}/game (#{f['lrank']})" if f['lpg'] else ''
    facts = (f"{f['season']}: {f['pg']:.1f}/game (#{f['rank']} of 32)" + (f" · {last}" if last else '')
             + (f"\nMost common: {f['top_type']} ({f['top_n']})" if f['top_type'] else ''))
    if f.get('games', 99) <= 4:
        facts += f"\n({f['games']} games in, so it can still swing.)"
    q = pick([f"{f['name']} fans: fair, or are they getting squeezed?", "Coaching problem or just a bad stretch?",
              "Will it last?"], k + 'q')
    return f"🧺 {hook}\n\n{facts}\n\n{q}\n\nFull team profile → {url}\n\n{tags('#TeamLaundry', '#' + f['team'])}"


def division_laundry(f, url):
    """f: division, order [(name, pg, lpg)], week"""
    k = f"div{f['division']}{f['week']}"
    top, bot = f['order'][0], f['order'][-1]
    hook = pick([
        f"The {f['division']} discipline ladder: {top[0]} at the top, {bot[0]} at the bottom.",
        f"Most flagged in the {f['division']}: the {top[0]} ({top[1]:.1f}/game).",
        f"{top[1] - bot[1]:.1f} flags per game separate the top and bottom of the {f['division']}.",
    ], k)
    facts = '\n'.join(f"{i + 1}. {n} {pg:.1f}" + (f" (last season {lpg:.1f})" if lpg == lpg and lpg else '')
                      for i, (n, pg, lpg) in enumerate(f['order']))
    q = pick(["Which of these four cleans it up first?", "Surprised by the order?"], k + 'q')
    return f"🧺 {hook}\n\n{facts}\n\n{q}\n\n{url}\n\n{tags('#DivisionLaundry')}"


def flag_magnets(f, url):
    """f: week, leaders [(player, team, n, yards, top_type)]"""
    k = f"magnets{f['week']}"
    p, t, n, y, tt = f['leaders'][0]
    hook = pick([
        f"{n} accepted penalties in {f['week']} weeks. {p} ({t}) leads the league.",
        f"The NFL's flag magnet so far: {p}, {t}. {n} flags, {y} yards.",
        f"Nobody has been flagged more than {p} ({n}).",
    ], k)
    facts = '\n'.join(f"{i + 1}. {pl} ({tm}) {nn}" + (f" — mostly {ty}" if ty else '')
                      for i, (pl, tm, nn, yy, ty) in enumerate(f['leaders'][:5]))
    q = pick(["Who catches them by season's end?", "Which one surprises you?"], k + 'q')
    return f"🧲 {hook}\n\n{facts}\n\n{q}\n\n{url}\n\n{tags('#FlagMagnets')}"


def under_the_hood(f, url):
    """f: question, takeaway, stat, stat_label"""
    k = f['question']
    hook = pick([f"{f['question']}", f"We ran the numbers: {f['question'].rstrip('?').lower()}?"], k)
    return (f"🔎 {hook}\n\n{f['stat']} — {f['stat_label']}.\n{f['takeaway']}\n\n"
            f"{pick(['What should we check next?', 'Does that match what you see on Sundays?'], k + 'q')}\n\n"
            f"Method + data → {url}\n\n{tags('#UnderTheHood')}")
