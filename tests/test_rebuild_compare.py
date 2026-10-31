"""The rebuild check's comparison and download (scripts/rebuild_from_raw.py, #88)."""

import gzip
import hashlib
import json

import pytest

import raw_capture as rc
import rebuild_from_raw as rb

GAME = {'season': 2026, 'week': 8, 'penalties': 14, 'generatedAt': '2026-10-30T12:00:00Z'}


def write_data(base, files: dict, newline='\n'):
    for name, obj in files.items():
        p = base / 'frontend' / 'data' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(obj, indent=1) if not isinstance(obj, str) else obj
        p.write_bytes(text.replace('\n', newline).encode())


@pytest.fixture
def dirs(tmp_path):
    rebuilt, original = tmp_path / 'rebuilt', tmp_path / 'original'
    rebuilt.mkdir()
    original.mkdir()
    return rebuilt, original


# ---- caught ------------------------------------------------------------------

def test_changed_number_is_caught(dirs):
    rebuilt, original = dirs
    write_data(original, {'game.json': GAME})
    write_data(rebuilt, {'game.json': {**GAME, 'penalties': 15}})
    assert rb.compare(rebuilt, original) == ["frontend/data/game.json: $.penalties: '15' vs '14'"]


def test_missing_file_is_caught(dirs):
    rebuilt, original = dirs
    write_data(original, {'game.json': GAME, 'crews.json': {'a': 1}})
    write_data(rebuilt, {'game.json': GAME})
    assert rb.compare(rebuilt, original) == ['frontend/data/crews.json: missing from rebuild']


def test_time_more_than_20_minutes_off_is_caught(dirs):
    rebuilt, original = dirs
    write_data(original, {'game.json': GAME})
    write_data(rebuilt, {'game.json': {**GAME, 'generatedAt': '2026-10-30T12:21:00Z'}})
    [d] = rb.compare(rebuilt, original)
    assert d.startswith('frontend/data/game.json: $.generatedAt:') and 'more than 20 min apart' in d


def test_first_diff_finds_nested_change():
    a = {'crews': [{'name': 'Alex Moore', 'rate': 15.7}]}
    b = {'crews': [{'name': 'Alex Moore', 'rate': 15.6}]}
    assert rb.first_diff(a, b) == "$.crews[0].rate: '15.7' vs '15.6'"
    assert rb.first_diff(a, {'crews': []}) == '$.crews: 1 vs 0 items'


# ---- accepted ----------------------------------------------------------------

def test_time_within_20_minutes_is_accepted(dirs):
    rebuilt, original = dirs
    write_data(original, {'game.json': GAME})
    write_data(rebuilt, {'game.json': {**GAME, 'generatedAt': '2026-10-30T12:19:59Z'}})
    assert rb.compare(rebuilt, original) == []


def test_crlf_line_endings_are_accepted(dirs):
    rebuilt, original = dirs
    write_data(original, {'game.json': GAME, 'notes.md': 'line one\nline two\n'})
    write_data(rebuilt, {'game.json': GAME, 'notes.md': 'line one\nline two\n'}, newline='\r\n')
    assert rb.compare(rebuilt, original) == []


def test_raw_capture_block_and_source_stamp_are_ignored(dirs):
    rebuilt, original = dirs
    write_data(original, {'run_status.json': {'ok': True, 'rawCapture': {'status': 'ok'}},
                          'source_stamp.json': {'pbp': 'T1'}})
    write_data(rebuilt, {'run_status.json': {'ok': True}})
    assert rb.compare(rebuilt, original) == []


# ---- download() --------------------------------------------------------------

def stored_page(tmp_path, content: bytes, sha: str):
    store = rc.LocalStore(tmp_path / 'store')
    key = 'raw/footballzebras-feed/2026-10-30/assignments_feed_120000Z_abcdef12.xml.gz'
    store.put_object(Bucket=rc.BUCKET, Key=key, Body=gzip.compress(content))
    entry = {'source': 'footballzebras-feed', 'name': 'assignments_feed', 'key': key,
             'sha256': sha, 'url': 'https://www.footballzebras.com/feed/', 'step': 'fetch_assignments'}
    return store, {'inputs': [entry]}


def test_download_accepts_matching_sha(tmp_path):
    content = b'<rss/>'
    store, manifest = stored_page(tmp_path, content, hashlib.sha256(content).hexdigest())
    out = rb.download(store, manifest, tmp_path / 'dl')
    page = out['fetch_assignments']['pages']['https://www.footballzebras.com/feed/']
    assert (tmp_path / 'dl').joinpath(page['path']).read_bytes() == content


def test_download_refuses_sha_mismatch(tmp_path):
    store, manifest = stored_page(tmp_path, b'<rss/>', hashlib.sha256(b'something else').hexdigest())
    with pytest.raises(SystemExit, match='sha256 mismatch'):
        rb.download(store, manifest, tmp_path / 'dl')
