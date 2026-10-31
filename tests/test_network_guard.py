"""The no-network guard in conftest.py works (#89)."""

import socket
import urllib.request

import pytest
from conftest import NetworkBlocked


def test_outside_connection_is_blocked():
    with pytest.raises(NetworkBlocked):
        socket.create_connection(('93.184.215.14', 443), timeout=1)


def test_name_lookup_is_blocked():
    with pytest.raises(NetworkBlocked):
        socket.getaddrinfo('github.com', 443)


def test_http_request_is_blocked():
    with pytest.raises(Exception) as e:
        urllib.request.urlopen('https://api.github.com/', timeout=1)
    assert 'network call blocked' in str(e.value)


def test_local_connection_is_allowed():
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    try:
        socket.create_connection(server.getsockname(), timeout=1).close()
    finally:
        server.close()
