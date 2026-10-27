# ADR-0002: Raw capture to R2 with boto3, Parquet and per-run manifests

- **Status:** Decided
- **Date:** 2026-10-27
- **Plan reference:** `docs/V2_BUILD_PLAN.md` section 4 (V2.0 step 1), section 3 (raw storage), decisions D15 and D20
- **Issue / PR:** #88

## Context

V2.0 step 1 asks every pipeline run to save its raw pulls to Cloudflare R2
(`nflobs-raw`), append-only, so a script can rebuild any past week from raw
files alone. Facts at the time:

- A `--full` run loads about 232 MB of nflverse files (12 play-by-play seasons
  of 19–21 MB, schedules 0.5 MB, officials 0.15 MB, teams 13 KB), plus the
  Football Zebras feed (about 10 KB) and post (about 190 KB) when a week needs crews.
- About 10–15 runs a week pass the gate in season. Storing every pull would be
  2.5–3.5 GB a week; R2's free tier is 10 GB.
- Saving the 12 seasons as zstd Parquet and hashing them takes 0.8 s, and the
  output is byte-identical for the same data (checked).
- The R2 token is scoped to `nflobs-raw` only; the laptop has no R2 credentials.

## Options considered

1. **Client: boto3:** the client Cloudflare's R2 docs use; conditional PUT,
   listing and clear error codes. Con: about 16.6 MB more to download (botocore).
2. **Client: polars' built-in S3 writing:** no new dependency, but it can't upload
   pages, do conditional writes, list, or run the access check.
3. **Client: obstore:** smaller, but less familiar.
4. **Storage: every pull, every run:** simplest; fills the free tier in weeks.
5. **Storage: skip files identical to their latest capture, with a manifest per
   run:** small, and every run still records exactly which version it used.

## Decision

boto3, with storage option 5. Tables are saved as zstd Parquet from the polars
frame nflreadpy returned, and pages as the exact bytes received, gzip-compressed.
Keys are `raw/<source>/<date>/<name>_<time>Z_<sha8>.<ext>`, and every write is
conditional (`If-None-Match: *`). Each run writes a manifest in `raw/_runs/`
listing every input, new or reused. Capture never stops the site update; failing
for more than 24 hours turns the run red. The full Football Zebras page is kept
privately (never published).

## Consequences

- Any past run can be rebuilt (`scripts/rebuild_from_raw.py`): its manifest
  names every input, and its start commit holds the state files.
- About 1.6 GB in the first year; the PR records actual growth after a week.
- The token can still delete objects; append-only is enforced by the code and
  conditional writes. An R2 bucket lock on `raw/` (decided: later) would make it
  hold even against the token. Test objects live under `_checks/` so a lock
  won't block the access check's cleanup.
- Revisit if R2 stops honouring `If-None-Match`, if storage grows faster than
  the estimate, or when Dagster (V2.0 step 4) takes over the pulls.
