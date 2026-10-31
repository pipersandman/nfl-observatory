"""Cloudflare Web Analytics export (scripts/analytics_export.py, #164), with a stubbed
GraphQL API and raw_capture.LocalStore standing in for R2."""

import gzip
import json
from datetime import date, datetime, timedelta, timezone

import analytics_export as ae
import raw_capture as rc

TOKEN = 'tok-SECRET-1234567890'
ACCOUNT = 'acct-SECRET-abcdef'
SITE = '8db64f3b97744e96bc6630d4dd4fbece'
NOW = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)   # a Monday


def row(path='/', ref='x.com', country='United States', count=5, visits=3):
    return {'count': count, 'sum': {'visits': visits}, 'avg': {'sampleInterval': 1},
            'dimensions': {'requestPath': path, 'refererHost': ref, 'countryName': country}}


class FakeAPI:
    """Answers the settings query and day queries; records every request."""

    def __init__(self, days=None, settings=None, errors=None):
        self.days = days or {}          # 'YYYY-MM-DD' -> list of groups
        self.settings = settings if settings is not None else {
            'enabled': True, 'maxDuration': 86400 * 31, 'maxPageSize': 10000, 'notOlderThan': 86400 * 183}
        self.errors = errors
        self.calls = []

    def __call__(self, url, headers, payload):
        assert url == ae.GRAPHQL_URL
        assert headers['Authorization'] == f'Bearer {TOKEN}'
        self.calls.append(payload)
        if self.errors:
            return {'data': None, 'errors': self.errors}
        v = payload['variables']
        assert v['account'] == ACCOUNT
        if 'settings' in payload['query']:
            return {'data': {'viewer': {'accounts': [{'settings': {ae.DATASET: self.settings}}]}}}
        assert v['site'] == SITE and 'bot: 0' in payload['query']
        day = v['start'][:10]
        assert v['end'] == f'{date.fromisoformat(day) + timedelta(days=1)}T00:00:00Z'   # one UTC day
        return {'data': {'viewer': {'accounts': [{ae.DATASET: self.days.get(day, [])}]}}}

    def day_queries(self):
        return [c['variables']['start'][:10] for c in self.calls if 'site' in c['variables']]


def api(fake):
    return ae.CloudflareAPI(TOKEN, ACCOUNT, fake)


def keys(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())


def run(fake, store, start, end, **kw):
    return ae.run(api(fake), store, SITE, start, end, now=NOW, pause=0, **kw)


# ---- key layout and content ---------------------------------------------------

def test_key_layout_and_content(tmp_path):
    fake = FakeAPI({'2026-10-31': [row('/', 'x.com'), row('/crew/', '', count=2, visits=2)]})
    assert run(fake, rc.LocalStore(tmp_path), date(2026, 10, 31), date(2026, 10, 31)) == 0
    assert keys(tmp_path) == ['internal/analytics/cloudflare-web/2026-10-31.json.gz']
    doc = json.loads(gzip.decompress((tmp_path / keys(tmp_path)[0]).read_bytes()))
    assert doc['date'] == '2026-10-31' and doc['siteTag'] == SITE
    assert doc['filter'] == {'siteTag': SITE, 'bot': 0}
    assert doc['totals'] == {'rows': 2, 'pageViews': 7, 'visits': 5}
    assert doc['rows'][1] == {'path': '/crew/', 'referrerHost': '', 'country': 'United States',
                              'pageViews': 2, 'visits': 2, 'sampleInterval': 1}


def test_nothing_written_outside_internal(tmp_path):
    days = {f'2026-10-{d:02d}': [row()] for d in range(20, 32)}
    run(FakeAPI(days), rc.LocalStore(tmp_path), date(2026, 10, 20), date(2026, 10, 31))
    assert len(keys(tmp_path)) == 12
    assert all(k.startswith('internal/analytics/cloudflare-web/') for k in keys(tmp_path))


# ---- append-only --------------------------------------------------------------

def test_stored_day_is_skipped_and_not_queried(tmp_path, capsys):
    store = rc.LocalStore(tmp_path)
    fake = FakeAPI({'2026-10-30': [row()], '2026-10-31': [row()]})
    run(fake, store, date(2026, 10, 30), date(2026, 10, 30))
    before = (tmp_path / 'internal/analytics/cloudflare-web/2026-10-30.json.gz').read_bytes()
    fake2 = FakeAPI({'2026-10-30': [row(count=99)], '2026-10-31': [row()]})
    assert run(fake2, store, date(2026, 10, 30), date(2026, 10, 31)) == 0
    assert fake2.day_queries() == ['2026-10-31']
    assert (tmp_path / 'internal/analytics/cloudflare-web/2026-10-30.json.gz').read_bytes() == before
    assert '2026-10-30: already stored, skipped' in capsys.readouterr().out


def test_refused_write_warns_and_does_not_overwrite(tmp_path, capsys, monkeypatch):
    store = rc.LocalStore(tmp_path)
    target = tmp_path / 'internal/analytics/cloudflare-web/2026-10-31.json.gz'
    target.parent.mkdir(parents=True)
    target.write_bytes(b'original')
    monkeypatch.setattr(ae, 'stored_days', lambda client: set())   # object appears after the listing
    assert run(FakeAPI({'2026-10-31': [row()]}), store, date(2026, 10, 31), date(2026, 10, 31)) == 0
    assert target.read_bytes() == b'original'
    out = capsys.readouterr().out
    assert 'already exists; not overwritten' in out and '1 refused writes' in out


# ---- which days ---------------------------------------------------------------

def test_today_is_never_stored(tmp_path):
    fake = FakeAPI({'2026-11-01': [row()], '2026-11-02': [row()]})
    run(fake, rc.LocalStore(tmp_path), date(2026, 11, 1), date(2026, 11, 2))
    assert fake.day_queries() == ['2026-11-01']
    assert keys(tmp_path) == ['internal/analytics/cloudflare-web/2026-11-01.json.gz']


def test_start_clamped_to_api_history(tmp_path, capsys):
    fake = FakeAPI(settings={'enabled': True, 'maxPageSize': 10000, 'notOlderThan': 86400 * 3})
    run(fake, rc.LocalStore(tmp_path), date(2026, 1, 1), date(2026, 11, 1))
    assert fake.day_queries() == ['2026-10-31', '2026-11-01']
    assert 'Oldest full day the API returns: 2026-10-31' in capsys.readouterr().out


def test_empty_day_not_stored(tmp_path):
    run(FakeAPI({'2026-10-31': [row()]}), rc.LocalStore(tmp_path), date(2026, 10, 30), date(2026, 10, 31))
    assert keys(tmp_path) == ['internal/analytics/cloudflare-web/2026-10-31.json.gz']


def test_row_limit_hit_stores_nothing_and_fails(tmp_path):
    fake = FakeAPI({'2026-10-31': [row(f'/p{i}') for i in range(3)]},
                   settings={'enabled': True, 'maxPageSize': 3, 'notOlderThan': 86400 * 30})
    assert run(fake, rc.LocalStore(tmp_path), date(2026, 10, 31), date(2026, 10, 31)) == 1
    assert keys(tmp_path) == []


def test_probe_writes_nothing(tmp_path, capsys):
    fake = FakeAPI({'2026-10-31': [row(), row('/team/')]})
    assert run(fake, rc.LocalStore(tmp_path), date(2026, 10, 31), date(2026, 10, 31), probe=True) == 0
    assert keys(tmp_path) == []
    assert '2026-10-31: 2 rows, 10 page views (probe, not stored)' in capsys.readouterr().out


# ---- main(): settings and secrets ---------------------------------------------

def env(monkeypatch, tmp_path):
    monkeypatch.setenv('CF_ANALYTICS_TOKEN', TOKEN)
    monkeypatch.setenv('CF_ACCOUNT_ID', ACCOUNT)
    monkeypatch.setenv('CF_WEB_ANALYTICS_SITE_TAG', SITE)
    monkeypatch.setenv('NFLOBS_RAW_STORE_DIR', str(tmp_path))


def test_main_weekly_default_is_last_8_finished_days(tmp_path, monkeypatch, capsys):
    env(monkeypatch, tmp_path)
    fake = FakeAPI()
    assert ae.main([], post=fake) == 0
    queried = fake.day_queries()
    assert len(queried) == 8
    today = datetime.now(timezone.utc).date()
    assert queried[-1] == (today - timedelta(days=1)).isoformat()


def test_secrets_never_printed(tmp_path, monkeypatch, capsys):
    env(monkeypatch, tmp_path)
    monkeypatch.setattr(ae.time, 'sleep', lambda s: None)
    ok = FakeAPI({'2026-10-31': [row()]})
    ae.main(['--from', '2026-10-30', '--to', '2026-10-31'], post=ok)
    # an API error that echoes both values back
    bad = FakeAPI(errors=[{'message': f'account {ACCOUNT} not allowed for token {TOKEN}'}])
    assert ae.main(['--from', '2026-10-30'], post=bad) == 1
    out = capsys.readouterr()
    text = out.out + out.err
    assert TOKEN not in text and ACCOUNT not in text
    assert 'account <hidden> not allowed for token <hidden>' in text


def test_missing_settings_fail_without_calling_api(monkeypatch, capsys):
    fake = FakeAPI()
    assert ae.main([], post=fake) == 1
    assert fake.calls == []
    assert 'missing settings: CF_ANALYTICS_TOKEN, CF_ACCOUNT_ID, CF_WEB_ANALYTICS_SITE_TAG' in capsys.readouterr().out


def test_missing_r2_settings_fail_unless_probe(monkeypatch, capsys):
    monkeypatch.setenv('CF_ANALYTICS_TOKEN', TOKEN)
    monkeypatch.setenv('CF_ACCOUNT_ID', ACCOUNT)
    monkeypatch.setenv('CF_WEB_ANALYTICS_SITE_TAG', SITE)
    assert ae.main([], post=FakeAPI()) == 1
    assert 'missing R2 settings' in capsys.readouterr().out
    assert ae.main(['--probe'], post=FakeAPI()) == 0
