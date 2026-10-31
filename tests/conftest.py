"""Shared setup for every test (#89).

- scripts/ and tests/ go on the import path, so tests can `import seasons`,
  `import raw_capture` and the helper in tests/workflow_scripts.py.
- No network: any connection or name lookup for a host other than this machine
  fails with NetworkBlocked. Tests that need a server use 127.0.0.1.
- A clean environment for each test: GitHub Actions, R2 and NFLOBS_* variables
  are removed (CI sets GITHUB_ACTIONS itself), so each test sets only what it
  needs.
"""

import os
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / 'scripts', ROOT / 'tests'):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


# ---- network guard -----------------------------------------------------------

LOCAL_HOSTS = {'127.0.0.1', '::1', 'localhost', None}


class NetworkBlocked(RuntimeError):
    pass


def _host(address):
    if isinstance(address, tuple) and address:
        return address[0]
    return address   # Unix socket path or similar: local


_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_getaddrinfo = socket.getaddrinfo


def _check(host):
    if isinstance(host, bytes):
        host = host.decode()
    if host in LOCAL_HOSTS or (isinstance(host, str) and host.startswith('/')):
        return
    raise NetworkBlocked(f'network call blocked in tests: {host}')


def _guarded_connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        _check(_host(address))
    return _real_connect(self, address)


def _guarded_connect_ex(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        _check(_host(address))
    return _real_connect_ex(self, address)


def _guarded_getaddrinfo(host, *args, **kwargs):
    _check(host)
    return _real_getaddrinfo(host, *args, **kwargs)


socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect_ex
socket.getaddrinfo = _guarded_getaddrinfo


# ---- clean environment -------------------------------------------------------

CLEARED_PREFIXES = ('GITHUB_', 'RUNNER_', 'R2_', 'NFLOBS_')


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in list(os.environ):
        if name.startswith(CLEARED_PREFIXES):
            monkeypatch.delenv(name, raising=False)
    try:
        import raw_capture
        monkeypatch.setattr(raw_capture, '_instance', None)
    except ImportError:
        pass
    yield
