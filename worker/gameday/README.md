# Gameday feed (Cloudflare Worker)

Serves `GET /live`: this week's NFL games with every penalty as it happens, for
`/gameday/` on the site. Source: ESPN's public (undocumented) site API, fetched
once per 15 seconds for everyone (cached at Cloudflare), so ESPN sees a handful of
requests no matter how many people watch.

| File | Purpose |
|---|---|
| `parse.js` | Penalty extraction (play text → team, type, player, yards, accepted/declined/offsetting; box-score totals) |
| `worker.js` | The Worker: scoreboard + live game summaries + our projections → compact JSON |
| `worker.bundle.js` | Both in one file, for pasting into the Cloudflare dashboard (`node bundle.mjs` regenerates it) |
| `test-local.mjs` | Check the parser against real ESPN data from your machine |
| `wrangler.toml` | For deploying with Wrangler instead of the dashboard |

## Check it against a real game (any time)

```powershell
cd C:\Users\tfost\nfl-observatory
node worker\gameday\test-local.mjs 401873010
```

(401873010 = Week 7 Patriots at Bears.) It prints each team's flags and yards from
the box score, how many flags were parsed from the play-by-play, whether they
match, and the latest flags.

## Notes
- Counts are accepted penalties from the live box score; declined and offsetting
  flags are listed but not counted (matches the rest of the site).
- Free plan: 100,000 requests a day. Each open Gameday tab makes about 3 requests a
  minute while games are live (and pauses when the tab is in the background), so
  roughly 25 people watching for 6 hours. If it grows past that, switch the Worker
  to the $5/month plan or move to a cron-written file (see V2 plan).
- ESPN's API is unofficial and can change; the page shows "feed unavailable" and
  retries if it breaks.
