#!/usr/bin/env python3
"""R2 access check (#88): proves the pipeline's token is scoped to nflobs-raw only.

Run from the manual workflow "R2 access check" (GitHub secrets R2_*). Steps:
  1. write _checks/<id>.txt to nflobs-raw                 -> must succeed
  2. write the same key again with If-None-Match: *       -> must be refused (412)
  3. list drsplus-tiles                                   -> must be denied
  4. write _checks/<id>.txt to drsplus-tiles              -> must be denied
     (if it unexpectedly succeeds, the object is deleted at once)
  5. always: delete the test object from nflobs-raw, then confirm it's gone (404)

Test objects live under _checks/, outside raw/, so a future bucket lock on raw/
won't block the cleanup. Prints PASS/FAIL per step; never prints keys, secrets or
the endpoint. Exit 0 only if every step gave the expected result.
"""

import os
import sys
from datetime import datetime, timezone

import raw_capture as rc

OWN = rc.BUCKET
OTHER = 'drsplus-tiles'
DENIED = {'AccessDenied', 'Unauthorized', '401', '403', 'Forbidden'}


def main():
    missing = [n for n in rc.ENV_NAMES if not os.environ.get(n)]
    if missing:
        print(f'FAIL  R2 secrets missing: {", ".join(missing)}')
        return 1
    client = rc.make_client()
    key = f"_checks/{os.environ.get('GITHUB_RUN_ID', 'local')}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.txt"
    body = b'nflobs access check; safe to delete\n'
    results = []

    def step(n, label, ok, detail):
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {n}. {label}: {detail}")

    try:
        # 1. write to our bucket
        try:
            client.put_object(Bucket=OWN, Key=key, Body=body, IfNoneMatch='*', ContentType='text/plain')
            step(1, f'write test object to {OWN}', True, 'written')
        except Exception as e:
            step(1, f'write test object to {OWN}', False, rc.short(e))

        # 2. the same key again must be refused (append-only works on R2)
        try:
            client.put_object(Bucket=OWN, Key=key, Body=b'overwrite attempt\n', IfNoneMatch='*', ContentType='text/plain')
            step(2, 'second write to the same key', False, 'accepted: an existing object was OVERWRITTEN')
        except Exception as e:
            code = rc.error_code(e)
            step(2, 'second write to the same key', code in {'PreconditionFailed', '412'}, f'refused ({code})')

        # 3. list the other bucket
        try:
            client.list_objects_v2(Bucket=OTHER, MaxKeys=1)
            step(3, f'list {OTHER}', False, 'ALLOWED: the token can see another bucket')
        except Exception as e:
            code = rc.error_code(e)
            step(3, f'list {OTHER}', code in DENIED, f'denied ({code})' if code in DENIED else rc.short(e))

        # 4. write to the other bucket
        try:
            client.put_object(Bucket=OTHER, Key=key, Body=body, IfNoneMatch='*', ContentType='text/plain')
            try:
                client.delete_object(Bucket=OTHER, Key=key)
                cleanup = 'test object deleted again'
            except Exception as e:
                cleanup = f'COULD NOT DELETE {key}: {rc.error_code(e)}'
            step(4, f'write to {OTHER}', False, f'ALLOWED: the token can write another bucket ({cleanup})')
        except Exception as e:
            code = rc.error_code(e)
            step(4, f'write to {OTHER}', code in DENIED, f'denied ({code})' if code in DENIED else rc.short(e))
    finally:
        # 5. always clean up our test object
        try:
            client.delete_object(Bucket=OWN, Key=key)
            try:
                client.head_object(Bucket=OWN, Key=key)
                step(5, 'delete test object', False, 'still there after delete')
            except Exception as e:
                code = rc.error_code(e)
                step(5, 'delete test object', code in {'404', 'NoSuchKey', 'NotFound'}, f'gone ({code})')
        except Exception as e:
            step(5, 'delete test object', False, rc.short(e))

    ok = all(results) and len(results) == 5
    print(f"\n{'ALL 5 STEPS PASSED' if ok else 'ACCESS CHECK FAILED'}")
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write(f"### R2 access check\n\n{'All 5 steps passed' if ok else 'FAILED, see the log'}\n")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
