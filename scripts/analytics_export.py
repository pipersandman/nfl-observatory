"""Cloudflare Web Analytics export to private R2 (#164).

Cloudflare's dashboard keeps a limited history, so each finished UTC day is
copied to the private bucket nflobs-raw:

    internal/analytics/cloudflare-web/<YYYY-MM-DD>.json.gz

One file per day: page views and visits grouped by page path, referrer host and
country, from the GraphQL Analytics API dataset rumPageloadEventsAdaptiveGroups,
filtered to the site tag, with bot traffic excluded (bot = 0, the dashboard's
"Exclude bots").

Rules (raw capture's, #88):
- Append-only: a day already stored is skipped, and every write is conditional
  (If-None-Match: *). A refused write is a warning, never an overwrite.
- Only finished days: today (UTC) is never stored, and neither is a day with no
  rows (a later run tries it again).
- A day that hits the API's row limit isn't stored (it would be incomplete for
  good); the run ends red.
- Nothing is written outside internal/. The token and account ID are never
  printed.

Usage:
    python scripts/analytics_export.py                    last 8 finished days
    python scripts/analytics_export.py --from 2026-05-01  backfill (to yesterday)
    python scripts/analytics_export.py --probe [...]      report only, no writes

Environment: CF_ANALYTICS_TOKEN, CF_ACCOUNT_ID, CF_WEB_ANALYTICS_SITE_TAG, and
R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT (not needed with --probe).
Local test hook (ignored in GitHub Actions): NFLOBS_RAW_STORE_DIR=<folder> uses
a folder laid out like the bucket instead of R2.
"""

import argparse
import gzip
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import raw_capture as rc

GRAPHQL_URL = 'https://api.cloudflare.com/client/v4/graphql'
DATASET = 'rumPageloadEventsAdaptiveGroups'
PREFIX = 'internal/analytics/cloudflare-web/'
BOT_FILTER = {'bot': 0}          # the dashboard's "Exclude bots" (also written in DAY_QUERY)
DEFAULT_DAYS = 8
DEFAULT_LIMIT = 10000            # used if the API doesn't report its page size
PAUSE_SECONDS = 1.0              # between day queries (API limit: 300 per 5 minutes)

SETTINGS_QUERY = """
query Settings($account: string!) {
  viewer {
    accounts(filter: {accountTag: $account}) {
      settings {
        rumPageloadEventsAdaptiveGroups { enabled maxDuration maxPageSize notOlderThan }
      }
    }
  }
}
"""

DAY_QUERY = """
query Day($account: string!, $site: string!, $start: Time!, $end: Time!) {
  viewer {
    accounts(filter: {accountTag: $account}) {
      rumPageloadEventsAdaptiveGroups(
        limit: LIMIT
        filter: {AND: [{siteTag: $site}, {bot: 0}, {datetime_geq: $start}, {datetime_lt: $end}]}
        orderBy: [count_DESC]
      ) {
        count
        sum { visits }
        avg { sampleInterval }
        dimensions { requestPath refererHost countryName }
      }
    }
  }
}
"""


class ExportError(RuntimeError):
    pass


# ---- secrets never printed ------------------------------------------------------

def _secrets() -> list[str]:
    values = [os.environ.get(n) for n in ('CF_ANALYTICS_TOKEN', 'CF_ACCOUNT_ID', 'R2_ENDPOINT')]
    values += [v.strip() for v in values if v]
    return sorted({v for v in values if v}, key=len, reverse=True)


def setting(name: str) -> str:
    """An environment value with spaces and line breaks around it removed (a pasted
    secret often ends with a newline). Says so when it removed any, never the value."""
    raw = os.environ.get(name) or ''
    value = raw.strip()
    if value != raw:
        say(f'Note: {name} had spaces or line breaks around it; removed.')
    return value


def scrub(text: str) -> str:
    for s in _secrets():
        text = text.replace(s, '<hidden>')
    return text


def say(message: str) -> None:
    print(scrub(message), flush=True)


def warn(message: str) -> None:
    message = scrub(message)
    print(f'   ⚠️  {message}', flush=True)
    if rc.in_actions():
        print(f'::warning title=Analytics export::{message}', flush=True)


# ---- Cloudflare API ---------------------------------------------------------------

def http_post(url, headers, payload):
    """POST JSON, return the decoded JSON body (separate so tests can stub it)."""
    import requests
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    try:
        body = r.json()
    except ValueError:
        raise ExportError(f'HTTP {r.status_code}, not JSON: {r.text[:200]}')
    if r.status_code != 200 and not body.get('errors'):
        raise ExportError(f'HTTP {r.status_code}')
    return body


class CloudflareAPI:
    def __init__(self, token, account, post=http_post):
        self.token, self.account, self.post = token, account, post

    def query(self, text, variables):
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        body = self.post(GRAPHQL_URL, headers, {'query': text, 'variables': {'account': self.account, **variables}})
        if body.get('errors'):
            msgs = '; '.join(str(e.get('message', e)) for e in body['errors'])
            raise ExportError(f'Cloudflare API error: {msgs[:500]}')
        accounts = ((body.get('data') or {}).get('viewer') or {}).get('accounts') or []
        if not accounts:
            raise ExportError('Cloudflare API returned no account (check the token and account ID)')
        return accounts[0]

    def settings(self) -> dict:
        acct = self.query(SETTINGS_QUERY, {})
        return ((acct.get('settings') or {}).get(DATASET)) or {}

    def day_rows(self, site_tag, day: date, limit: int) -> list[dict]:
        start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        acct = self.query(DAY_QUERY.replace('LIMIT', str(int(limit))),
                          {'site': site_tag, 'start': iso(start), 'end': iso(start + timedelta(days=1))})
        out = []
        for g in acct.get(DATASET) or []:
            d = g.get('dimensions') or {}
            out.append({
                'path': d.get('requestPath'),
                'referrerHost': d.get('refererHost') or '',
                'country': d.get('countryName') or '',
                'pageViews': int(g.get('count') or 0),
                'visits': int((g.get('sum') or {}).get('visits') or 0),
                'sampleInterval': (g.get('avg') or {}).get('sampleInterval'),
            })
        return out


def iso(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


# ---- storage ----------------------------------------------------------------------

def day_key(day: date) -> str:
    key = f'{PREFIX}{day.isoformat()}.json.gz'
    if not key.startswith('internal/'):
        raise ExportError(f'refusing to write outside internal/: {key}')
    return key


def stored_days(client) -> set[str]:
    return set(rc.list_keys(client, PREFIX))


def day_document(site_tag, day: date, rows, limit, now: datetime) -> dict:
    return {
        'source': 'cloudflare-web-analytics',
        'dataset': DATASET,
        'siteTag': site_tag,
        'date': day.isoformat(),
        'timezone': 'UTC',
        'filter': {'siteTag': site_tag, **BOT_FILTER},
        'groupedBy': ['path', 'referrerHost', 'country'],
        'note': 'pageViews = count, visits = sum.visits; adaptive (possibly sampled) data, see sampleInterval',
        'fetchedAt': iso(now),
        'runId': rc.run_id() or 'local',
        'rowLimit': limit,
        'totals': {'rows': len(rows), 'pageViews': sum(r['pageViews'] for r in rows),
                   'visits': sum(r['visits'] for r in rows)},
        'rows': rows,
    }


def encode(doc: dict) -> bytes:
    raw = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return gzip.compress(raw, mtime=0)


def put_new(client, key: str, body: bytes) -> bool:
    """Conditional write. False (with a warning) if the object already exists."""
    try:
        client.put_object(Bucket=rc.BUCKET, Key=key, Body=body, IfNoneMatch='*',
                          ContentType='application/gzip')
        return True
    except Exception as e:
        if rc.error_code(e) in ('PreconditionFailed', '412'):
            warn(f'{key} already exists; not overwritten')
            return False
        raise ExportError(f'R2 write failed for {key}: {rc.short(e)}')


def has_store() -> bool:
    return bool(rc._test_hook('NFLOBS_RAW_STORE_DIR')) or all(os.environ.get(n) for n in rc.ENV_NAMES)


def make_store():
    folder = rc._test_hook('NFLOBS_RAW_STORE_DIR')
    if folder:
        say(f'Store: local folder {folder} (test hook)')
        return rc.LocalStore(folder)
    missing = [n for n in rc.ENV_NAMES if not os.environ.get(n)]
    if missing:
        raise ExportError(f'missing R2 settings: {", ".join(missing)}')
    return rc.make_client()


# ---- the run ----------------------------------------------------------------------

def day_range(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def run(api, store, site_tag, start: date, end: date, probe=False, now=None, pause=PAUSE_SECONDS) -> int:
    now = now or datetime.now(timezone.utc)
    yesterday = now.date() - timedelta(days=1)
    settings = api.settings()
    limit = int(settings.get('maxPageSize') or DEFAULT_LIMIT)
    oldest = None
    if settings.get('notOlderThan'):
        oldest = (now - timedelta(seconds=int(settings['notOlderThan']))).date() + timedelta(days=1)
    say(f'Dataset {DATASET}: enabled={settings.get("enabled")}, maxDuration={settings.get("maxDuration")}s, '
        f'maxPageSize={settings.get("maxPageSize")}, notOlderThan={settings.get("notOlderThan")}s')
    say(f'Oldest full day the API returns: {oldest.isoformat() if oldest else "not reported"}')
    say(f'Filter: siteTag = {site_tag}, bot = 0 (bots excluded)')

    if end > yesterday:
        say(f'End date moved from {end} to {yesterday} (only finished UTC days are stored)')
        end = yesterday
    if oldest and start < oldest:
        say(f'Start date moved from {start} to {oldest} (older days are past the API history)')
        start = oldest
    if start > end:
        say('No days to export.')
        return 0
    say(f'Days: {start} to {end}' + (' (probe: nothing is written)' if probe else ''))

    have = stored_days(store) if store is not None else set()
    counts = {'stored': 0, 'skipped': 0, 'empty': 0, 'refused': 0, 'limit': 0}
    first_query = True
    for day in day_range(start, end):
        key = day_key(day)
        if key in have:
            counts['skipped'] += 1
            say(f'  {day}: already stored, skipped')
            continue
        if not first_query:
            time.sleep(pause)
        first_query = False
        rows = api.day_rows(site_tag, day, limit)
        views = sum(r['pageViews'] for r in rows)
        if len(rows) >= limit:
            counts['limit'] += 1
            warn(f'{day}: {len(rows)} rows hit the API row limit ({limit}); not stored')
            continue
        if not rows:
            counts['empty'] += 1
            say(f'  {day}: no data, not stored')
            continue
        if probe:
            say(f'  {day}: {len(rows)} rows, {views} page views (probe, not stored)')
            continue
        if put_new(store, key, encode(day_document(site_tag, day, rows, limit, now))):
            counts['stored'] += 1
            say(f'  {day}: stored {len(rows)} rows, {views} page views')
        else:
            counts['refused'] += 1

    say(f'Done: {counts["stored"]} days stored, {counts["skipped"]} already stored, {counts["empty"]} with no data, '
        f'{counts["refused"]} refused writes, {counts["limit"]} over the row limit.')
    if counts['limit']:
        say('Stop: days over the row limit need smaller queries before they can be stored.')
        return 1
    return 0


def parse_day(text: str) -> date:
    return date.fromisoformat(text)


def main(argv=None, post=http_post) -> int:
    p = argparse.ArgumentParser(description='Export Cloudflare Web Analytics days to private R2 (#164).')
    p.add_argument('--from', dest='start', type=parse_day, help='first day (YYYY-MM-DD); backfill')
    p.add_argument('--to', dest='end', type=parse_day, help='last day (default: yesterday, UTC)')
    p.add_argument('--days', type=int, default=DEFAULT_DAYS, help='without --from: this many days ending yesterday')
    p.add_argument('--probe', action='store_true', help='report what the API returns; write nothing')
    args = p.parse_args(argv)

    try:
        token, account = setting('CF_ANALYTICS_TOKEN'), setting('CF_ACCOUNT_ID')
        site_tag = setting('CF_WEB_ANALYTICS_SITE_TAG')
        missing = [n for n, v in (('CF_ANALYTICS_TOKEN', token), ('CF_ACCOUNT_ID', account),
                                  ('CF_WEB_ANALYTICS_SITE_TAG', site_tag)) if not v]
        if missing:
            raise ExportError(f'missing settings: {", ".join(missing)}')
        now = datetime.now(timezone.utc)
        end = args.end or (now.date() - timedelta(days=1))
        start = args.start or (end - timedelta(days=args.days - 1))
        # A probe writes nothing; it reads the store only to show which days are already there
        store = make_store() if not args.probe or has_store() else None
        return run(CloudflareAPI(token, account, post), store, site_tag, start, end, probe=args.probe, now=now)
    except Exception as e:
        msg = str(e) if isinstance(e, ExportError) else f'{type(e).__name__}: {e}'
        say(f'❌ Analytics export failed: {msg}')
        if rc.in_actions():
            print(f'::error title=Analytics export::{scrub(msg)}', flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
