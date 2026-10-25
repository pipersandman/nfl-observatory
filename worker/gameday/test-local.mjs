// Run on your machine (Node 18+): node worker/gameday/test-local.mjs [espnEventId]
// Fetches ESPN directly and prints what the Worker would serve for that game.
import { compactGame } from './parse.js';
const ESPN = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl';
const id = process.argv[2];
const sb = await (await fetch(`${ESPN}/scoreboard`)).json();
const evs = (sb.events || []).filter(e => !id || e.id === id);
for (const ev of evs) {
  const st = ev.status?.type?.state;
  const summary = st === 'pre' ? null : await (await fetch(`${ESPN}/summary?event=${ev.id}`)).json();
  const g = compactGame(ev, summary, null);
  console.log(`\n${g.name}  ${g.detail}  flags ${g.flags} (${g.away.abbr} ${g.away.flags}/${g.away.yards}y [${g.away.source}], ${g.home.abbr} ${g.home.flags}/${g.home.yards}y [${g.home.source}])`);
  const acc = g.log.filter(f => f.status === 'accepted').length;
  console.log(`  parsed from plays: ${g.log.length} flags (${acc} accepted) | box score total ${g.flags}${acc === g.flags ? '  ✓ match' : '  (differs: box score is used for totals)'}`);
  g.log.slice(0, 6).forEach(f => console.log(`   Q${f.qtr} ${f.clock}  ${f.team} ${f.type}${f.player ? ' (' + f.player + ')' : ''} ${f.yards}y ${f.status}${f.noPlay ? ' no play' : ''}`));
}
