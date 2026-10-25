/* Home page: live scoreboard strip on game days (ESPN-style tiles, our data and design).
   Game tiles scroll continuously; updates change the tiles in place (no jump), and anything
   that changed lights up: a new flag flashes the tile and pops the team's flag count, a score
   change pulses, and the 'Most flags' marker moves to the leader. Links to /gameday/. */
(() => {
    const strip = document.getElementById('liveStrip');
    if (!strip) return;
    const params = new URLSearchParams(location.search);
    const FEED = params.get('livefeed') || 'https://nflobs-gameday.tfostery.workers.dev/live';
    const SOON = 3 * 3600e3, RECENT = 6 * 3600e3;
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const LOGO = { WAS: 'wsh', LA: 'lar' };
    const logo = a => `https://a.espncdn.com/i/teamlogos/nfl/500/${(LOGO[a] || a).toLowerCase()}.png`;
    const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const qLabel = q => (q == null || q === '') ? '' : +q >= 6 ? `${+q - 4}OT` : +q === 5 ? 'OT' : `Q${q}`;   // overtime reads OT, never Q5
    const time = iso => new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    const day = iso => new Date(iso).toLocaleDateString([], { weekday: 'short' });
    const last = new Map();             // game id -> {away, home, af, hf, flags}
    let signature = null, timer;

    // ---------------------------------------------------------------- what each tile says
    const status = g => g.state === 'in' ? (g.detail || `${qLabel(g.period)} ${g.clock}`) : g.state === 'post' ? (g.detail || 'Final')
        : (new Date(g.start) - Date.now() < 20 * 3600e3 ? time(g.start) : `${day(g.start)} ${time(g.start)}`);
    const foot = g => g.state === 'pre'
        ? (g.preview?.projected != null ? `Proj <b>${g.preview.projected.toFixed(1)}</b> flags${g.preview.crew ? ` · ${esc(g.preview.crew.split(' ').slice(-1)[0])}` : ''}` : 'Flags start at kickoff')
        : `<b>${g.flags}</b> flags · ${g.yards} yds`;

    function tileHtml(g) {
        const row = (side, t) => `<div class="lt-row" data-side="${side}">
            <img src="${logo(t.abbr)}" alt="" loading="lazy"><span class="lt-abbr">${esc(t.abbr)}</span>
            <span class="lt-fl" title="Flags on ${esc(t.abbr)}"><i aria-hidden="true"></i><b>${g.state === 'pre' ? '' : t.flags}</b></span>
            <span class="lt-sc">${g.state === 'pre' ? '' : t.score}</span></div>`;
        return `<div class="lt st-${g.state}" data-g="${esc(g.id)}">
            <div class="lt-top"><span class="lt-st">${esc(status(g))}</span><span class="lt-net">${esc(g.network || '')}</span></div>
            ${row('away', g.away)}${row('home', g.home)}
            <div class="lt-foot">${foot(g)}</div><span class="lt-lead" title="Most flags this week">Most flags</span></div>`;
    }
    function costHtml(c) {
        return `<div class="lt lt-cost" data-g="costliest">
            <div class="lt-top"><span class="lt-st">Costliest flag</span><span class="lt-net">win chance</span></div>
            <div class="lt-cost-main"><b class="lt-cost-n">${c ? `−${Math.round(c.wpCost * 100)}%` : '—'}</b>
                <span class="lt-cost-what">${c ? `${esc(c.team)} ${esc(c.type)}` : 'No costly flags yet'}</span></div>
            <div class="lt-foot">${c ? `${esc(c.game || '')} · ${qLabel(c.qtr)}` : '&nbsp;'}</div></div>`;
    }

    // ---------------------------------------------------------------- build / update
    const order = gs => gs.slice().sort((a, b) => ({ in: 0, pre: 1, post: 2 }[a.state] - { in: 0, pre: 1, post: 2 }[b.state])
        || (a.state === 'post' ? new Date(b.start) - new Date(a.start) : new Date(a.start) - new Date(b.start)));

    function build(d, games, cost, live) {
        const track = costHtml(cost) + games.map(tileHtml).join('');
        strip.innerHTML = `<div class="lt-label${live ? ' is-live' : ''}"><span class="lt-tag">${live ? '<span class="lt-dot"></span>LIVE' : 'GAMEDAY'}</span>
                <span class="lt-week">Week ${esc(d.week ?? '')}</span><span class="lt-total"><b data-k="flags">0</b> flags</span></div>
            <div class="lt-viewport"><div class="lt-track${reduce ? ' still' : ''}">${track}${reduce ? '' : track}</div></div>
            <span class="lt-cta">Full<br>scoreboard →</span>`;
        if (!reduce) requestAnimationFrame(() => {
            const t = strip.querySelector('.lt-track');
            t.style.animationDuration = `${Math.max(24, t.scrollWidth / 2 / 40)}s`;     // ~40 px a second
        });
    }

    const all = sel => strip.querySelectorAll(sel);           // both copies of a tile (the loop)
    function flash(el, cls) { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); }

    function update(d, games, cost, live, firstTime) {
        const played = d.games.filter(g => g.state !== 'pre');
        const total = played.reduce((s, g) => s + g.flags, 0);
        strip.querySelector('[data-k="flags"]').textContent = total;
        strip.querySelector('.lt-label').classList.toggle('is-live', live);
        const leader = played.slice().sort((a, b) => b.flags - a.flags)[0];
        games.forEach(g => {
            const was = last.get(g.id);
            all(`.lt[data-g="${CSS.escape(g.id)}"]`).forEach(tile => {
                ['pre', 'in', 'post'].forEach(st => tile.classList.toggle(`st-${st}`, g.state === st));   // keeps a running flash
                tile.classList.toggle('is-lead', !!(leader && leader.id === g.id && leader.flags > 0));
                tile.querySelector('.lt-st').textContent = status(g);
                tile.querySelector('.lt-foot').innerHTML = foot(g);
                ['away', 'home'].forEach(side => {
                    const t = g[side], row = tile.querySelector(`[data-side="${side}"]`);
                    row.querySelector('.lt-fl b').textContent = g.state === 'pre' ? '' : t.flags;
                    row.querySelector('.lt-sc').textContent = g.state === 'pre' ? '' : t.score;
                    if (firstTime || !was) return;
                    if (t.flags > was[side].flags) { flash(row.querySelector('.lt-fl'), 'pop'); flash(tile, 'hit'); }
                    if (t.score !== was[side].score) flash(row.querySelector('.lt-sc'), 'pulse');
                });
            });
            last.set(g.id, { away: { flags: g.away.flags, score: g.away.score }, home: { flags: g.home.flags, score: g.home.score } });
        });
        all('.lt[data-g="costliest"]').forEach(tile => {
            tile.querySelector('.lt-cost-n').textContent = cost ? `−${Math.round(cost.wpCost * 100)}%` : '—';
            tile.querySelector('.lt-cost-what').textContent = cost ? `${cost.team} ${cost.type}` : 'No costly flags yet';
            tile.querySelector('.lt-foot').textContent = cost ? `${cost.game || ''} · ${qLabel(cost.qtr)}` : '';
        });
        if (!firstTime && cost) {
            const n = `−${Math.round(cost.wpCost * 100)}%`;
            if (n !== strip.dataset.cost) all('.lt[data-g="costliest"]').forEach(t => flash(t, 'hit'));
        }
        strip.dataset.cost = cost ? `−${Math.round(cost.wpCost * 100)}%` : '';
    }

    function render(d) {
        const now = Date.now();
        const live = d.games.some(g => g.state === 'in');
        const soon = d.games.some(g => g.state === 'pre' && new Date(g.start) - now < SOON);
        const recent = d.games.some(g => g.state === 'post' && now - new Date(g.start) < RECENT + 4 * 3600e3);
        if (!live && !soon && !recent) { strip.hidden = true; signature = null; return; }
        const games = order(d.games);
        const cost = (d.costliest || []).find(c => c.wpCost > 0.005) || null;
        const sig = games.map(g => g.id).join(',');
        const firstTime = sig !== signature;
        if (firstTime) { build(d, games, cost, live); signature = sig; }
        strip.hidden = false;
        update(d, games, cost, live, firstTime);
        const nav = document.querySelector('nav'), box = strip.parentElement;
        if (nav && box) box.style.paddingTop = `${Math.ceil(nav.getBoundingClientRect().height) + 12}px`;
    }

    async function load() {
        let live = false;
        try {
            const d = await (await fetch(FEED, { cache: 'no-store' })).json();
            if (d && Array.isArray(d.games)) { render(d); live = d.games.some(g => g.state === 'in'); }
        } catch { /* no strip if the feed is unavailable */ }
        clearTimeout(timer);
        if (!document.hidden) timer = setTimeout(load, params.has('livefast') ? 3000 : live ? 60000 : 300000);
    }
    document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
    load();
})();
