"""Tests for the react-loop run-level stall backstop watchdog.

Regression coverage for the rare worker hang: a lazy worker (src/main.py --serve,
running via core/react_loop.py) was observed stuck for 4+ hours mid-LLM-stream at
iteration ~60/60 — CPU 0%, no outbound connection, all threads idle. The inner
stream watchdog (in llm_client) did not unblock the parked `for chunk` consumer.

These tests exercise the run-level backstop watchdog
``core.react_loop._make_react_stall_watchdog`` directly with fakes, mirroring the
style of tests/test_stream_watchdog.py:
  - it fires after ``stall_s`` when no new chunk timestamp arrives, invoking the
    ``on_stall`` callback (which in production calls cancel_current_stream);
  - it does NOT fire while chunks keep arriving (healthy turn — no-op).
"""

import time

import core.react_loop as react_loop


def test_stall_watchdog_fires_when_no_chunks():
    """No chunk for longer than stall_s => watchdog fires and calls on_stall."""
    # Last-chunk timestamp frozen in the past => already stalled from the start.
    last_chunk = [time.time() - 100]
    calls = [0]

    def _on_stall():
        calls[0] += 1

    # stall_s small; poll cadence is 5s so allow up to ~6s for the first wake.
    stop, fired, thread = react_loop._make_react_stall_watchdog(
        last_chunk, stall_s=1, on_stall=_on_stall,
    )
    try:
        t0 = time.time()
        while time.time() - t0 < 7 and not fired[0]:
            time.sleep(0.1)
    finally:
        stop.set()
        thread.join(timeout=2)

    assert fired[0], "stall watchdog should have fired with a frozen last-chunk ts"
    assert calls[0] == 1, f"on_stall should be invoked exactly once, got {calls[0]}"


def test_stall_watchdog_no_trigger_while_chunks_arrive():
    """A healthy turn that keeps bumping the last-chunk ts must NOT fire."""
    last_chunk = [time.time()]
    calls = [0]

    def _on_stall():
        calls[0] += 1

    stop, fired, thread = react_loop._make_react_stall_watchdog(
        last_chunk, stall_s=1, on_stall=_on_stall,
    )
    try:
        t0 = time.time()
        # Keep bumping the timestamp for longer than one poll interval (>5s)
        # so the watchdog gets a chance to evaluate but never sees a stall.
        while time.time() - t0 < 7:
            last_chunk[0] = time.time()
            time.sleep(0.1)
    finally:
        stop.set()
        thread.join(timeout=2)

    assert not fired[0], "watchdog wrongly fired on a healthy (progressing) stream"
    assert calls[0] == 0, "on_stall must not be called when chunks keep arriving"


def test_stall_watchdog_disabled_when_stall_s_zero():
    """stall_s == 0 disables the watchdog entirely (never fires)."""
    last_chunk = [time.time() - 10000]  # very stale, but disabled
    calls = [0]

    def _on_stall():
        calls[0] += 1

    stop, fired, thread = react_loop._make_react_stall_watchdog(
        last_chunk, stall_s=0, on_stall=_on_stall,
    )
    try:
        t0 = time.time()
        while time.time() - t0 < 7 and not fired[0]:
            time.sleep(0.1)
    finally:
        stop.set()
        thread.join(timeout=2)

    assert not fired[0], "watchdog must be a no-op when stall_s is 0"
    assert calls[0] == 0
