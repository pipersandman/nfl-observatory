/* Gameday Flag Tracker: every penalty as it happens.
   Polls the Worker feed (see worker/gameday), ranks games by flags or penalty yards,
   and animates what changed: new flags flash the game, counts pop, rows slide to
   their new rank, and the newest flag drops into the ticker.
   ?demo=1 simulates a slate of games (for previews and testing); ?feed=URL overrides the feed. */
(() => {
    const params = new URLSearchParams(location.search);
    const FEED = params.get('feed') || document.body.dataset.feed;
    const DEMO = params.has('demo') || /YOUR-SUBDOMAIN/.test(FEED || '');
    const POLL_LIVE = 20000, POLL_IDLE = 120000;
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ESPN_LOGO = { WAS: 'wsh', LA: 'lar' };
    const logo = a => `https://a.espncdn.com/i/teamlogos/nfl/500/${(ESPN_LOGO[a] || a).toLowerCase()}.png`;
    const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    const state = { sort: 'flags', show: 'all', data: null, prev: new Map(), seenFlags: new Set(), first: true, lastOk: null, timer: null, openLogs: new Set() };
    const $ = id => document.getElementById(id);
const qLabel = q => (q == null || q === '') ? '' : +q >= 6 ? `${+q - 4}OT` : +q === 5 ? 'OT' : `Q${q}`;   // overtime reads OT, never Q5

    // ------------------------------------------------------------------ helpers
    const clockSecs = c => { const m = /^(\d+):(\d+)$/.exec(c || ''); return m ? (+m[1]) * 60 + (+m[2]) : 0; };
    function elapsedFrac(g) {
        if (g.state === 'post') return 1;
        if (g.state !== 'in' || !g.period) return 0;
        const p = Math.min(g.period, 4);
        return Math.min(1, ((p - 1) * 900 + (900 - clockSecs(g.clock))) / 3600);
    }
    function pace(g) {
        const f = elapsedFrac(g);
        return g.state === 'in' && f >= 0.15 ? Math.round(g.flags / f) : null;
    }
    const kickoff = iso => new Date(iso).toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' });
    function statusText(g) {
        if (g.state === 'in') return `<span class="gd-live">LIVE</span> ${esc(g.detail || `${qLabel(g.period)} ${g.clock}`)}`;
        if (g.state === 'post') return esc(g.detail || 'Final');
        return esc(kickoff(g.start));
    }

    // ------------------------------------------------------------------ render
    function leagueStrip(d) {
        const played = d.games.filter(g => g.state !== 'pre');
        const live = d.games.filter(g => g.state === 'in');
        const flags = played.reduce((s, g) => s + g.flags, 0), yards = played.reduce((s, g) => s + g.yards, 0);
        const recent = d.games.flatMap(g => (g.log || []).filter(f => f.status === 'accepted').map(f => ({ ...f, game: g }))).length;
        $('gdLeague').innerHTML = [
            ['Games live', live.length, `${played.length - live.length} final · ${d.games.length - played.length} to come`],
            ['Flags', flags, played.length ? `${(flags / played.length).toFixed(1)} per game` : 'none yet'],
            ['Penalty yards', yards, played.length ? `${Math.round(yards / played.length)} per game` : ''],
            ['Most flagged', played.length ? (() => { const t = played.flatMap(g => [g.home, g.away]).sort((a, b) => b.flags - a.flags)[0]; return t ? `${t.abbr} ${t.flags}` : '—'; })() : '—', 'team, this week\'s games'],
        ].map(([l, v, s]) => `<div class="gd-stat"><span>${l}</span><b data-v="${esc(v)}">${esc(v)}</b><em>${esc(s)}</em></div>`).join('');
    }

    function card(g, rank) {
        const p = g.preview || {};
        const pc = pace(g);
        const proj = p.projected;
        const max = Math.max(proj || 0, g.flags, pc || 0, 16) * 1.1;
        const paceCls = pc != null && proj != null ? (pc > proj * 1.1 ? 'pct-up' : pc < proj * 0.9 ? 'pct-down' : '') : '';
        const share = g.flags ? Math.round(g.away.flags / g.flags * 100) : 0;
        const metric = state.sort === 'yards' ? g.yards : g.flags;
        // every flag in the game, newest first, grouped by quarter
        const all = g.log || [];
        let lastQ = null;
        const log = all.map(f => {
            const head = f.qtr !== lastQ ? `<li class="gd-qhead">${f.qtr >= 5 ? 'Overtime' : `Quarter ${esc(f.qtr ?? '')}`}</li>` : '';
            lastQ = f.qtr;
            return head + `<li class="gd-flag ${f.status}"><span class="gd-q">${esc(f.clock ?? '')}</span>
            <b>${esc(f.team)}</b> ${esc(f.type)}${f.player ? ` <span class="modal-muted">${esc(f.player)}</span>` : ''}${f.tdErased ? ' <span class="gd-tag">TD erased</span>' : ''}
            <span class="gd-y">${f.status === 'accepted' ? `${f.yards} yds` : esc(f.status)}</span></li>`;
        }).join('');
        const accepted = all.filter(f => f.status === 'accepted').length;
        const other = all.length - accepted;
        const logOpen = state.openLogs.has(String(g.id));
        const cf = g.costliest;
        const costLine = cf && cf.wpCost > 0.005 ? `<div class="gd-costline" title="Live estimate of the win chances this flag cost ${esc(cf.team)}">Costliest: <b>${esc(cf.team)}</b> ${esc(cf.type)}${cf.tdErased ? ' <span class="gd-tag">TD erased</span>' : ''} · ${qLabel(cf.qtr)} ${esc(cf.clock ?? '')} <span class="gd-wp">−${Math.round(cf.wpCost * 100)}% win chance</span></div>` : '';
        return `<li class="gd-card st-${g.state}" data-id="${esc(g.id)}">
            <div class="gd-rank">${g.state === 'pre' ? '' : rank}</div>
            <div class="gd-match">
                <div class="gd-teams">
                    <span class="gd-team"><img src="${logo(g.away.abbr)}" alt="" loading="lazy">${esc(g.away.abbr)} <b>${g.state === 'pre' ? '' : g.away.score}</b></span>
                    <span class="gd-at">@</span>
                    <span class="gd-team"><img src="${logo(g.home.abbr)}" alt="" loading="lazy">${esc(g.home.abbr)} <b>${g.state === 'pre' ? '' : g.home.score}</b></span>
                </div>
                <div class="gd-meta">${statusText(g)}${g.network ? ` · ${esc(g.network)}` : ''}${p.crew ? ` · Crew: ${p.crewSlug ? `<a href="/crew/${esc(p.crewSlug)}/">${esc(p.crew)}</a>` : esc(p.crew)}` : ''}</div>
                ${g.state !== 'pre' ? `<div class="gd-split" title="Flags by team"><i style="width:${share}%"></i><span>${esc(g.away.abbr)} ${g.away.flags} · ${g.away.yards} yds</span><span>${esc(g.home.abbr)} ${g.home.flags} · ${g.home.yards} yds</span></div>` : ''}
                ${proj != null ? `<div class="gd-pace"><div class="gd-pace-bar"><i class="now" style="width:${Math.min(100, g.flags / max * 100)}%"></i>${pc != null ? `<i class="pace" style="left:${Math.min(100, pc / max * 100)}%"></i>` : ''}<i class="proj" style="left:${Math.min(100, proj / max * 100)}%"></i></div>
                    <span>${g.state === 'pre' ? `Projected <b>${proj.toFixed(1)}</b> flags` : `Projected ${proj.toFixed(1)}${pc != null ? ` · <b class="${paceCls}">on pace for ${pc}</b>` : ''}`}</span></div>` : ''}
                ${costLine}
            </div>
            <div class="gd-count"><b class="gd-num">${g.state === 'pre' ? '—' : metric}</b><span>${state.sort === 'yards' ? 'penalty yds' : 'flags'}</span>
                ${g.state !== 'pre' ? `<em>${state.sort === 'yards' ? `${g.flags} flags` : `${g.yards} yds`}</em>` : ''}</div>
            ${log ? `<details class="gd-log" data-log="${esc(g.id)}"${logOpen ? ' open' : ''}><summary>Flag log · ${accepted} flag${accepted === 1 ? '' : 's'}${other ? `, ${other} declined or offsetting` : ''}</summary><ol>${log}</ol></details>` : ''}
            <span class="gd-drop" aria-hidden="true"></span>
        </li>`;
    }

    function order(games) {
        const key = state.sort;
        const shown = state.show === 'live' ? games.filter(g => g.state === 'in') : games;
        const playedFirst = (a, b) => (a.state === 'pre') - (b.state === 'pre');
        return shown.slice().sort((a, b) => playedFirst(a, b) || (a.state === 'pre' ? new Date(a.start) - new Date(b.start)
            : (b[key] - a[key]) || (b[key === 'flags' ? 'yards' : 'flags'] - a[key === 'flags' ? 'yards' : 'flags'])));
    }

    function render() {
        const d = state.data;
        if (!d) return;
        $('gdWeek').textContent = d.week ? `Week ${d.week}${d.season ? `, ${d.season}` : ''}: ` : '';   // leads the subtitle (#158)
        leagueStrip(d);
        const board = $('gdBoard');
        // FLIP: remember positions, re-render, animate from old to new
        const before = new Map([...board.children].map(el => [el.dataset.id, el.getBoundingClientRect().top]));
        const games = order(d.games);
        board.innerHTML = games.length ? games.map((g, i) => card(g, i + 1)).join('')
            : `<li class="gd-empty">${state.show === 'live' ? 'No games live right now.' : 'No games this week.'}</li>`;
        if (!reduce && !state.first) {
            [...board.children].forEach(el => {
                const old = before.get(el.dataset.id);
                if (old == null) return;
                const dy = old - el.getBoundingClientRect().top;
                if (Math.abs(dy) < 2) return;
                el.animate([{ transform: `translateY(${dy}px)` }, { transform: 'translateY(0)' }], { duration: 650, easing: 'cubic-bezier(.2,.8,.2,1)' });
            });
        }
        // highlight what changed since the last update
        games.forEach(g => {
            const was = state.prev.get(g.id);
            const el = board.querySelector(`[data-id="${CSS.escape(g.id)}"]`);
            if (!el || !was || state.first) return;
            if (g.flags > was.flags || g.yards > was.yards) {
                el.classList.add('gd-hit');
                el.querySelector('.gd-num')?.classList.add('gd-pop');
                setTimeout(() => el.classList.remove('gd-hit'), 2600);
            }
            if (g.state !== was.state && g.state === 'post') el.classList.add('gd-final-now');
        });
        state.prev = new Map(d.games.map(g => [g.id, { flags: g.flags, yards: g.yards, state: g.state }]));
        costly(d);
        ticker(d);
        state.first = false;
    }

    let lastCostKey = null;
    function costly(d) {
        const box = $('gdCostly');
        const list = (d.costliest || []).filter(f => f.wpCost > 0.005);
        if (!list.length) { box.innerHTML = ''; box.hidden = true; return; }
        box.hidden = false;
        const top = list[0];
        const key = `${top.gameId}:${top.id}`;
        const changed = !state.first && lastCostKey && key !== lastCostKey;
        lastCostKey = key;
        const pct = Math.round(top.wpCost * 100);
        box.innerHTML = `<div class="gd-costly-head"><span class="gd-costly-title">Costliest flag so far</span><span class="modal-muted">win chances lost · live estimate</span></div>
            <div class="gd-costly-main">
                <div class="gd-costly-num"><b data-to="${pct}">−${changed ? 0 : pct}%</b><span>win chance</span></div>
                <div class="gd-costly-what"><div class="gd-costly-type"><span class="gd-tick-flag" aria-hidden="true"></span>${esc(top.type)} on <b>${esc(top.team)}</b>${top.player ? ` <span class="modal-muted">${esc(top.player)}</span>` : ''}</div>
                    <div class="modal-muted">${esc(top.game)} · ${qLabel(top.qtr)} ${esc(top.clock ?? '')} · ${top.yards} yds${top.tdErased ? ' · <span class="gd-tag">touchdown erased</span>' : top.noPlay ? ' · play wiped out' : ''}</div></div>
            </div>
            ${list.length > 1 ? `<ol class="gd-costly-rest">${list.slice(1).map(f => `<li><b>${esc(f.team)}</b> ${esc(f.type)} <span class="modal-muted">${esc(f.game)} · ${qLabel(f.qtr)}</span><span class="gd-wp">−${Math.round(f.wpCost * 100)}%</span></li>`).join('')}</ol>` : ''}`;
        if (changed) {
            box.classList.remove('gd-costly-new'); void box.offsetWidth; box.classList.add('gd-costly-new');
            const el = box.querySelector('.gd-costly-num b'); const to = pct; const t0 = performance.now();
            const step = t => { const k = Math.min(1, (t - t0) / 900); el.textContent = `−${Math.round(to * (1 - Math.pow(1 - k, 3)))}%`; if (k < 1) requestAnimationFrame(step); };
            reduce ? (el.textContent = `−${to}%`) : requestAnimationFrame(step);
        }
    }

    function ticker(d) {
        // newest first across every game, by real-world time of the play (ESPN's timestamp); if a
        // play has none, estimate it from kickoff plus game time elapsed (~3 hours for 60 minutes)
        const when = (f, g) => {
            if (f.wall) { const t = Date.parse(f.wall); if (!Number.isNaN(t)) return t; }
            const q = Math.max(1, f.qtr || 1), el = (Math.min(q, 5) - 1) * 900 + (900 - clockSecs(f.clock));
            return Date.parse(g.start) + el * 3000;
        };
        const all = d.games.flatMap(g => (g.log || []).map(f => ({ ...f, g, t: when(f, g) })))
            .sort((a, b) => b.t - a.t);
        const fresh = all.filter(f => !state.seenFlags.has(`${f.g.id}:${f.id}`));
        all.forEach(f => state.seenFlags.add(`${f.g.id}:${f.id}`));
        $('gdTicker').innerHTML = all.slice(0, 10).map(f => `<li class="gd-tick ${f.status}${!state.first && fresh.includes(f) ? ' gd-new' : ''}">
            <span class="gd-tick-flag" aria-hidden="true"></span><b>${esc(f.team)}</b> ${esc(f.type)}
            <span class="modal-muted">${esc(f.g.away.abbr)} @ ${esc(f.g.home.abbr)} · ${qLabel(f.qtr)} ${esc(f.clock ?? '')}</span>
            <span class="gd-y">${f.status === 'accepted' ? `${f.yards} yds` : esc(f.status)}</span></li>`).join('')
            || '<li class="gd-tick modal-muted">No flags yet.</li>';
        if (!state.first && fresh.length) {
            const f = fresh.find(x => x.status === 'accepted') || fresh[0];
            toast(`<span class="gd-tick-flag" aria-hidden="true"></span><b>FLAG</b> ${esc(f.team)} · ${esc(f.type)}${f.status === 'accepted' ? ` · ${f.yards} yds` : ` (${esc(f.status)})`}<br><span>${esc(f.g.away.abbr)} @ ${esc(f.g.home.abbr)} · ${qLabel(f.qtr)} ${esc(f.clock ?? '')}${fresh.length > 1 ? ` · +${fresh.length - 1} more` : ''}</span>`);
        }
    }

    let toastTimer;
    function toast(html) {
        const t = $('gdToast');
        t.innerHTML = html;
        t.classList.remove('show'); void t.offsetWidth; t.classList.add('show');
        clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('show'), 4200);
    }

    function setUpdated() {
        const s = state.lastOk ? Math.round((Date.now() - state.lastOk) / 1000) : null;
        $('gdUpdated').textContent = s == null ? 'Connecting…' : DEMO ? `Demo · updated ${s}s ago` : `Updated ${s}s ago`;
        $('gdDot').classList.toggle('live', !!state.data?.live);
        $('gdDot').classList.toggle('stale', s != null && s > 90);
    }

    // ------------------------------------------------------------------ data
    async function load() {
        try {
            const d = DEMO ? demo.next() : await (await fetch(FEED, { cache: 'no-store' })).json();
            if (!d || d.error || !Array.isArray(d.games)) throw new Error(d?.error || 'bad feed');
            state.data = d; state.lastOk = Date.now();
            render();
        } catch (e) {
            $('gdUpdated').textContent = 'Live feed unavailable; retrying…';
        }
        schedule();
    }
    function schedule() {
        clearTimeout(state.timer);
        if (document.hidden) return;                       // pause while the tab is in the background
        state.timer = setTimeout(load, DEMO ? 6000 : state.data?.live ? POLL_LIVE : POLL_IDLE);
    }
    document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
    document.querySelectorAll('[data-sort]').forEach(b => b.addEventListener('click', () => {
        window.track?.('table_sort', { table: 'gameday', column: b.dataset.sort });
        state.sort = b.dataset.sort; document.querySelectorAll('[data-sort]').forEach(x => x.classList.toggle('active', x === b)); render();
    }));
    document.querySelectorAll('[data-show]').forEach(b => b.addEventListener('click', () => {
        state.show = b.dataset.show; document.querySelectorAll('[data-show]').forEach(x => x.classList.toggle('active', x === b)); render();
    }));
    document.addEventListener('toggle', e => {
        const d = e.target;
        if (!(d instanceof HTMLDetailsElement) || !d.dataset.log) return;
        d.open ? state.openLogs.add(d.dataset.log) : state.openLogs.delete(d.dataset.log);
    }, true);
    setInterval(setUpdated, 1000);

    // Seconds the page was visible, sent each time the visitor switches away or leaves
    // (#165). A visit's events add up to its total time on the page.
    let shownAt = document.hidden ? null : Date.now();
    const sendView = () => {
        if (shownAt === null) return;
        const seconds = Math.round((Date.now() - shownAt) / 1000);
        shownAt = null;
        if (seconds > 0) window.track?.('gameday_view', { seconds }, { beacon: true });
    };
    addEventListener('pagehide', sendView);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) sendView();
        else if (shownAt === null) shownAt = Date.now();
    });

    // ------------------------------------------------------------------ demo slate
    const demo = (() => {
        const TYPES = [['Offensive Holding', 10], ['False Start', 5], ['Defensive Pass Interference', 18], ['Defensive Holding', 5],
                       ['Unnecessary Roughness', 15], ['Delay of Game', 5], ['Roughing the Passer', 15], ['Illegal Formation', 5], ['Defensive Offside', 5]];
        const M = [['SF', 'ATL', 'Scott Novak', 'scott-novak', 17.0], ['CLE', 'TEN', 'Alex Moore', 'alex-moore', 15.6], ['IND', 'MIN', 'Brad Allen', 'brad-allen', 13.9],
                   ['MIA', 'NYJ', 'Land Clark', 'land-clark', 14.2], ['TB', 'CAR', 'Clay Martin', 'clay-martin', 12.4], ['DAL', 'PHI', 'Carl Cheffers', 'carl-cheffers', 14.8]];
        let t = 0;
        const games = M.map(([a, h, crew, slug, proj], i) => ({
            id: `demo${i}`, name: `${a} @ ${h}`, start: new Date(Date.now() + (i > 4 ? 3 : 0) * 3600e3).toISOString(),
            state: i > 4 ? 'pre' : 'in', period: 1, clock: '15:00', detail: '', network: ['FOX', 'CBS', 'CBS', 'CBS', 'FOX', 'NBC'][i],
            home: { abbr: h, score: 0, flags: 0, yards: 0 }, away: { abbr: a, score: 0, flags: 0, yards: 0 },
            flags: 0, yards: 0, log: [], preview: { crew, crewSlug: slug, projected: proj },
        }));
        return { next() {
            t++;
            games.forEach((g, i) => {
                if (g.state !== 'in') return;
                const secs = Math.max(0, clockSecs(g.clock) - 70 - Math.floor(Math.random() * 60));
                if (secs === 0) { g.period++; g.clock = '15:00'; if (g.period > 4) { g.state = 'post'; g.detail = 'Final'; return; } }
                else g.clock = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
                g.detail = `${qLabel(g.period)} ${g.clock}`;
                if (Math.random() < 0.18) { const side = Math.random() < 0.5 ? 'home' : 'away'; g[side].score += Math.random() < 0.5 ? 3 : 7; }
                const chance = 0.22 + (i === 0 ? 0.25 : 0);           // Novak's crew throws more, naturally
                if (Math.random() < chance) {
                    const [type, yds] = TYPES[Math.floor(Math.random() * TYPES.length)];
                    const side = Math.random() < 0.5 ? 'home' : 'away';
                    const status = Math.random() < 0.1 ? 'declined' : 'accepted';
                    const late = g.period >= 4 ? 2.2 : g.period === 3 ? 1.3 : 0.8, close = Math.abs(g.home.score - g.away.score) <= 8 ? 1.4 : 0.6;
                    const td = status === 'accepted' && type === 'Offensive Holding' && Math.random() < 0.25;
                    const wpCost = status !== 'accepted' ? null : td ? 0.12 + Math.random() * 0.2 : Math.min(0.25, yds * 0.0615 * 0.03 * late * close * (0.6 + Math.random()));
                    g.log.unshift({ id: `${t}-${i}`, wall: new Date().toISOString(), qtr: g.period, clock: g.clock, team: g[side].abbr, type, yards: status === 'accepted' ? yds : 0, status, player: null, wpCost, tdErased: td, noPlay: td });
                    if (status === 'accepted') { g[side].flags++; g[side].yards += yds; }
                }
                g.flags = g.home.flags + g.away.flags; g.yards = g.home.yards + g.away.yards;
                g.costliest = g.log.filter(f => f.wpCost != null).sort((a, b) => b.wpCost - a.wpCost)[0] || null;
            });
            if (t === 8) games[5].state = 'in';
            const costliest = games.flatMap(g => g.log.filter(f => f.wpCost != null).map(f => ({ ...f, game: g.name, gameId: g.id }))).sort((a, b) => b.wpCost - a.wpCost).slice(0, 3);
            return { updatedAt: new Date().toISOString(), week: 7, season: 2026, live: games.some(g => g.state === 'in'), games: JSON.parse(JSON.stringify(games)), costliest };
        } };
    })();

    if (DEMO) $('gdSub').lastChild.textContent = 'Demo mode: simulated games, so you can see how the board behaves. Live data appears once the feed is connected.';
    load();
})();
