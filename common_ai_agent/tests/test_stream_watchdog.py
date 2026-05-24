"""Tests for the streaming watchdog's stall detection + forced abort.

Regression coverage for the gpt-5.5 / Responses-API hang: a provider that keeps
the connection alive with periodic SSE heartbeats (events arriving under the
inactivity threshold) could keep a single streaming turn "live" for 40+ minutes
while making no real forward progress. The inactivity lane never fired because
``_last_progress`` kept getting bumped. The fix adds a per-turn wall-clock hard
cap and makes the abort tear down the underlying socket so a thread blocked in a
C-level ``recv()`` actually unblocks.
"""

import time

import llm_client


class _FakeSock:
    def __init__(self):
        self.shutdown_called = False
        self.close_called = False

    def shutdown(self, how):
        self.shutdown_called = True

    def close(self):
        self.close_called = True


class _FakeRaw:
    def __init__(self, sock):
        self._sock = sock


class _FakeFP:
    def __init__(self, sock):
        self.raw = _FakeRaw(sock)


class _FakeResponse:
    """Mimics http.client.HTTPResponse just enough for the watchdog."""

    def __init__(self, sock):
        self.fp = _FakeFP(sock)
        self.close_called = False

    def close(self):
        self.close_called = True


def test_hard_cap_fires_under_heartbeats():
    """Even with continuous heartbeats (inactivity never trips), the per-turn
    wall-clock hard cap must fire and forcibly tear down the socket."""
    sock = _FakeSock()
    resp = _FakeResponse(sock)
    last_data = [time.time()]
    last_progress = [time.time()]

    stop, triggered = llm_client._make_stream_watchdog(
        resp,
        inactivity_s=999,          # inactivity lane effectively disabled
        last_data_ref=last_data,
        last_progress_ref=last_progress,
        max_total_s=2,             # hard cap should fire ~2s in
    )
    try:
        t0 = time.time()
        # Simulate a provider streaming heartbeats: keep bumping both timers so
        # the inactivity lane can never trigger.
        while time.time() - t0 < 5 and not triggered[0]:
            now = time.time()
            last_data[0] = now
            last_progress[0] = now
            time.sleep(0.1)
    finally:
        stop.set()

    assert triggered[0], "hard cap should have fired despite heartbeats"
    assert "hard-cap" in triggered[0], f"unexpected reason: {triggered[0]!r}"
    # Forced teardown: response closed AND underlying socket shut down + closed,
    # which is what actually unblocks a parked readline().
    assert resp.close_called
    assert sock.shutdown_called
    assert sock.close_called


def test_inactivity_still_fires_when_idle():
    """The original inactivity lane must still work when no data arrives."""
    sock = _FakeSock()
    resp = _FakeResponse(sock)
    # Both timers frozen in the past => idle from the start.
    frozen = time.time() - 100
    last_data = [frozen]
    last_progress = [frozen]

    stop, triggered = llm_client._make_stream_watchdog(
        resp,
        inactivity_s=1,            # 1s idle limit, already exceeded
        last_data_ref=last_data,
        last_progress_ref=last_progress,
        max_total_s=0,             # hard cap disabled => only inactivity can fire
    )
    try:
        t0 = time.time()
        while time.time() - t0 < 3 and not triggered[0]:
            time.sleep(0.1)
    finally:
        stop.set()

    assert triggered[0], "inactivity lane should have fired"
    assert "inactivity" in triggered[0], f"unexpected reason: {triggered[0]!r}"
    assert sock.shutdown_called and sock.close_called


def test_no_trigger_when_progressing_within_budget():
    """A healthy stream that finishes before the cap must NOT be aborted."""
    sock = _FakeSock()
    resp = _FakeResponse(sock)
    last_data = [time.time()]
    last_progress = [time.time()]

    stop, triggered = llm_client._make_stream_watchdog(
        resp,
        inactivity_s=5,
        last_data_ref=last_data,
        last_progress_ref=last_progress,
        max_total_s=10,
    )
    try:
        t0 = time.time()
        while time.time() - t0 < 2:
            now = time.time()
            last_data[0] = now
            last_progress[0] = now
            time.sleep(0.1)
    finally:
        stop.set()

    assert not triggered[0], f"healthy stream wrongly aborted: {triggered[0]!r}"
    assert not resp.close_called
    assert not sock.shutdown_called
