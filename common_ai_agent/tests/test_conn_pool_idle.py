"""Tests for persistent-connection idle-expiry (long-stream connection-drop fix).

Root cause being covered: a pooled keep-alive connection that sits unused longer
than the provider's load-balancer idle window is silently dropped (CLOSE_WAIT);
reusing it blocks in getresponse() until the socket read timeout — a 30+ min
hang observed on long rtl-gen runs. _persistent_post now pre-emptively discards a
pooled connection idle longer than LLM_CONN_MAX_IDLE_SEC and opens a fresh one.
"""

import time

import config
import llm_client


class _FakeSock:
    def settimeout(self, t):
        self.timeout = t


class _FakeResp:
    status = 200

    def read(self):
        return b""


class _FakeConn:
    def __init__(self):
        self.sock = _FakeSock()
        self.timeout = None
        self.closed = False
        self.requested = False

    def request(self, *a, **k):
        self.requested = True

    def getresponse(self):
        return _FakeResp()

    def close(self):
        self.closed = True


def _patch(monkeypatch, host):
    """Reset pool state and stub connection creation; returns a counter list."""
    created = []

    def _fake_make(h, timeout=10):
        c = _FakeConn()
        created.append(c)
        return c

    monkeypatch.setattr(llm_client, "_make_https_conn", _fake_make)
    llm_client._http_conn_pool.pop(host, None)
    llm_client._http_conn_last_used.pop(host, None)
    return created


URL = "https://api.example-llm.test/v1/chat/completions"
HOST = "api.example-llm.test"


def test_stale_pooled_connection_is_discarded(monkeypatch):
    monkeypatch.setattr(config, "LLM_CONN_MAX_IDLE_SEC", 45)
    created = _patch(monkeypatch, HOST)

    # Seed pool with a connection last used 100s ago (> 45s idle window).
    stale = _FakeConn()
    llm_client._http_conn_pool[HOST] = stale
    llm_client._http_conn_last_used[HOST] = time.time() - 100

    resp = llm_client._persistent_post(URL, {"Authorization": "x"}, b"{}", timeout=1800)

    assert resp.status == 200
    assert stale.closed, "stale pooled connection should have been closed"
    assert len(created) == 1, "a fresh connection should have been opened"
    assert llm_client._http_conn_pool[HOST] is created[0]
    # last_used refreshed to ~now
    assert time.time() - llm_client._http_conn_last_used[HOST] < 5


def test_fresh_pooled_connection_is_reused(monkeypatch):
    monkeypatch.setattr(config, "LLM_CONN_MAX_IDLE_SEC", 45)
    created = _patch(monkeypatch, HOST)

    fresh = _FakeConn()
    llm_client._http_conn_pool[HOST] = fresh
    llm_client._http_conn_last_used[HOST] = time.time() - 5  # well within window

    resp = llm_client._persistent_post(URL, {"Authorization": "x"}, b"{}", timeout=1800)

    assert resp.status == 200
    assert not fresh.closed, "a fresh pooled connection must be reused, not dropped"
    assert len(created) == 0, "no new connection should be created on reuse"
    assert llm_client._http_conn_pool[HOST] is fresh


def test_headers_phase_uses_bounded_timeout_then_raises(monkeypatch):
    """getresponse() runs under the bounded header timeout; the socket timeout is
    raised to the full streaming budget once headers land."""
    monkeypatch.setattr(config, "LLM_CONN_MAX_IDLE_SEC", 45)
    monkeypatch.setattr(config, "LLM_HEADERS_TIMEOUT", 120)
    created = _patch(monkeypatch, HOST)

    resp = llm_client._persistent_post(URL, {"Authorization": "x"}, b"{}", timeout=1800)

    assert resp.status == 200
    conn = created[0]
    # After headers landed the connection's timeout is bumped to the full budget
    # so the streaming body read gets the long window.
    assert conn.timeout == 1800
    assert conn.sock.timeout == 1800
