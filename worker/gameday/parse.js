// Penalty extraction from ESPN's (undocumented) NFL feed. Shared by the Worker and the local test.

const ALIAS = { WSH: 'WAS', LAR: 'LA', JAC: 'JAX', OAK: 'LV', SD: 'LAC', STL: 'LA' };
export const norm = a => ALIAS[a] || a;

// "PENALTY on CHI-T.Edwards, Defensive Holding, 5 yards, enforced at NE 30 - No Play."
// "PENALTY on CHI, Delay of Game, 5 yards, enforced at CHI 25."
// "PENALTY on NE-M.Judon, Roughing the Passer, declined."
// Several flags can appear on one play; offsetting flags are marked as such.
const RE = /PENALTY on ([A-Z]{2,3})(?:-([^,]+?))?,\s*([^,]+?),\s*(?:(\d+)\s*yards?|(declined)|(offsetting))/gi;

export function parsePlayPenalties(text) {
  const out = [];
  if (!text || !/PENALTY on/i.test(text)) return out;
  const offsetting = /offset/i.test(text);
  const noPlay = /No Play/i.test(text);
  let m;
  RE.lastIndex = 0;
  while ((m = RE.exec(text))) {
    const declined = !!m[5];
    const status = offsetting ? 'offsetting' : declined ? 'declined' : 'accepted';
    out.push({
      team: norm(m[1].toUpperCase()),
      player: m[2] ? m[2].replace(/^\d+\s*-?\s*/, '').trim() : null,
      type: m[3].trim().replace(/\s+/g, ' '),
      yards: m[4] ? Number(m[4]) : 0,
      status,
      noPlay,
    });
  }
  return out;
}

// Official per-team totals from the box score: "7-55" (accepted penalties - yards)
export function boxPenalties(summary) {
  const res = {};
  for (const t of summary?.boxscore?.teams || []) {
    const abbr = norm(t.team?.abbreviation);
    const s = (t.statistics || []).find(x => /totalPenaltiesYards|penalties/i.test(x.name || x.label || ''));
    if (!s) continue;
    const m = String(s.displayValue || '').match(/(\d+)\s*-\s*(\d+)/);
    if (m) res[abbr] = { flags: Number(m[1]), yards: Number(m[2]) };
  }
  return res;
}

export function playsFrom(summary) {
  const drives = [...(summary?.drives?.previous || []), ...(summary?.drives?.current ? [summary.drives.current] : [])];
  const seen = new Set();
  const plays = [];
  for (const d of drives) for (const p of d.plays || []) {
    if (!p || seen.has(p.id)) continue;
    seen.add(p.id);
    plays.push(p);
  }
  // fallback: some live feeds only carry "plays" at the top level
  for (const p of summary?.plays || []) if (p && !seen.has(p.id)) { seen.add(p.id); plays.push(p); }
  return plays.sort((a, b) => Number(a.sequenceNumber || 0) - Number(b.sequenceNumber || 0));
}

export function gamePenalties(summary) {
  const flags = [];
  for (const p of playsFrom(summary)) {
    const list = parsePlayPenalties(p.text);
    list.forEach((f, i) => flags.push({
      id: `${p.id}-${i}`, seq: Number(p.sequenceNumber || 0),
      qtr: p.period?.number ?? null, clock: p.clock?.displayValue ?? null, ...f,
    }));
  }
  return flags;
}

// One compact record per game for the board
export function compactGame(ev, summary, preview) {
  const c = ev.competitions?.[0] || {};
  const side = h => c.competitors?.find(x => x.homeAway === h) || {};
  const home = side('home'), away = side('away');
  const hA = norm(home.team?.abbreviation), aA = norm(away.team?.abbreviation);
  const st = ev.status || c.status || {};
  const flags = summary ? gamePenalties(summary) : [];
  const acc = flags.filter(f => f.status === 'accepted');
  const box = summary ? boxPenalties(summary) : {};
  const team = abbr => {
    const fromPlays = acc.filter(f => f.team === abbr);
    const b = box[abbr];
    return { abbr, score: Number(side(abbr === hA ? 'home' : 'away').score || 0),
             flags: b ? b.flags : fromPlays.length, yards: b ? b.yards : fromPlays.reduce((s, f) => s + f.yards, 0),
             source: b ? 'boxscore' : 'plays' };
  };
  const H = team(hA), A = team(aA);
  return {
    id: ev.id, name: ev.shortName, start: ev.date,
    state: st.type?.state || 'pre', detail: st.type?.shortDetail || st.type?.detail || '',
    period: st.period ?? 0, clock: st.displayClock || '',
    network: (c.broadcasts?.[0]?.names || [])[0] || ev.broadcast || '',
    home: H, away: A,
    flags: H.flags + A.flags, yards: H.yards + A.yards,
    // newest first; declined and offsetting kept and labeled
    log: flags.slice().reverse().slice(0, 40),
    preview: preview || null,
  };
}
