// NFL Officiating Observatory: Gameday Flag Tracker feed (Cloudflare Worker)
// GET /live -> { updatedAt, week, games: [...] } for the week's games, penalties as they happen.
// ESPN's public site API is undocumented: fetch politely (one shared fetch per 15 s for everyone).
import { compactGame } from './parse.js';

const ESPN = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl';
const PREVIEWS = 'https://nflobservatory.com/data/previews/latest.json';
const TTL_LIVE = 15;          // seconds: cache while any game is live
const TTL_IDLE = 300;         // seconds: no game live
const ALLOWED = ['https://nflobservatory.com', 'https://www.nflobservatory.com', 'http://localhost:8000', 'http://127.0.0.1:8000'];

async function getJSON(url, ttl) {
  const r = await fetch(url, { headers: { 'User-Agent': 'nflobservatory.com gameday tracker' }, cf: { cacheTtl: ttl, cacheEverything: true } });
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}

async function previewsByMatchup() {
  try {
    const idx = await getJSON(PREVIEWS, 600);
    const wk = await getJSON(`https://nflobservatory.com/data/${idx.file}`, 600);
    const map = {};
    for (const g of wk.games || []) map[`${g.awayTeam.abbr}@${g.homeTeam.abbr}`] = {
      crew: g.crew?.name || null, crewSlug: g.crew?.slug || null,
      projected: g.projection?.total ?? null, low: g.projection?.low ?? null, high: g.projection?.high ?? null,
    };
    return map;
  } catch { return {}; }
}

async function build() {
  const sb = await getJSON(`${ESPN}/scoreboard`, TTL_LIVE);
  const prev = await previewsByMatchup();
  const events = sb.events || [];
  const games = await Promise.all(events.map(async ev => {
    const state = ev.status?.type?.state;
    let summary = null;
    if (state === 'in' || state === 'post') {
      try { summary = await getJSON(`${ESPN}/summary?event=${ev.id}`, state === 'in' ? TTL_LIVE : 600); } catch { summary = null; }
    }
    const c = ev.competitions?.[0] || {};
    const ab = h => (c.competitors?.find(x => x.homeAway === h)?.team?.abbreviation) || '';
    const n = a => ({ WSH: 'WAS', LAR: 'LA' }[a] || a);
    return compactGame(ev, summary, prev[`${n(ab('away'))}@${n(ab('home'))}`]);
  }));
  const live = games.some(g => g.state === 'in');
  return { updatedAt: new Date().toISOString(), week: sb.week?.number ?? null, season: sb.season?.year ?? null, live, games, source: 'ESPN' };
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    const origin = req.headers.get('Origin');
    const cors = { 'Access-Control-Allow-Origin': ALLOWED.includes(origin) ? origin : 'https://nflobservatory.com', 'Vary': 'Origin' };
    if (req.method === 'OPTIONS') return new Response(null, { headers: { ...cors, 'Access-Control-Allow-Methods': 'GET' } });
    if (url.pathname !== '/live') return new Response('Not found', { status: 404 });

    const cache = caches.default;
    const key = new Request(`${url.origin}/live`);
    let res = await cache.match(key);
    if (!res) {
      try {
        const data = await build();
        const ttl = data.live ? TTL_LIVE : TTL_IDLE;
        res = new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json', 'Cache-Control': `public, max-age=${ttl}` } });
        ctx.waitUntil(cache.put(key, res.clone()));
      } catch (e) {
        return new Response(JSON.stringify({ error: 'feed unavailable', updatedAt: new Date().toISOString() }),
          { status: 502, headers: { 'Content-Type': 'application/json', ...cors } });
      }
    }
    const out = new Response(res.body, res);
    Object.entries(cors).forEach(([k, v]) => out.headers.set(k, v));
    return out;
  },
};
