"""Wave 2 / Task 5 — live-output coalescing (plan §2.8).

Verifies the worker-side token/reasoning batcher in
:class:`core.session_worker._OutputBatcher` and the SINGLE re-expansion point in
:meth:`core.atlas_multiuser._MultiUserBridge._poll_process_outputs`:

1. size-trigger — 1000 small ``emit_content`` calls with the 50ms timer FROZEN
   plus a manual ``flush()`` produce a row count bounded by the 4KB math, and
   the concatenated re-expanded text equals the input EXACTLY (no loss / no
   reorder / no duplication);
2. time-trigger (SEPARATE) — advancing the injected fake clock past 50ms yields
   EXACTLY ONE flush;
3. ordering — ``token A``, then a non-mergeable event (ask_user / tool / cost /
   flush / agent_state), then ``token B`` re-expands to the outbox order
   ``A, event, B`` — the event is NEVER delayed behind B;
4. expansion parity — ``token_batch``/``reasoning_batch`` rows re-expand to the
   SAME per-event shape (``{"type":"token","text":..,"cls"?}`` /
   ``{"type":"reasoning","text":..,"blank":..}``) the browser already consumes
   for un-coalesced rows.

The never-coalesce set verified here (all real worker emits): tool, tool_result,
cost, token_usage (TWO rows), context, ask_user / ask_user_answered, agent_state,
worker_started / worker_stopped / worker_exited, error, flush. file_changed /
stop / interrupt are intentionally NOT worker emits and are not in the set.

Pure-Python / direct-DB (no real subprocess) so the suite is fast and the clock
is fully deterministic.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.atlas_db import AtlasDB  # noqa: E402
from core.atlas_multiuser import _MultiUserBridge  # noqa: E402
from core.session_worker import (  # noqa: E402
    COALESCE_FLUSH_INTERVAL_S,
    COALESCE_FLUSH_MAX_BYTES,
    SessionWorker,
    _OutputBatcher,
)


# ──────────────────────────────────────────────────────────────────────────
# fakes
# ──────────────────────────────────────────────────────────────────────────


class _FakeClock:
    """Deterministic monotonic clock the batcher reads via ``monotonic_fn``."""

    def __init__(self, start: float = 0.0) -> None:
        self.t = float(start)

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += float(dt)


class _RecordingSink:
    """Captures (msg_type, payload) the batcher would enqueue, no DB needed."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, object]] = []

    def __call__(self, msg_type: str, payload: object) -> str:
        self.rows.append((msg_type, payload))
        return f"row-{len(self.rows)}"


class _DBPollManager:
    """Minimal SessionProcessManager stand-in for the bridge poll path.

    ``poll_output`` returns the session's undelivered out-rows from a real
    AtlasDB exactly like the production manager, so the bridge's single
    expansion point runs against genuine queue rows. It deliberately does NOT
    accept ``on_absent_cursor`` (the bridge falls back to the 2-arg call) and
    never swaps the DB — that recovery path is Task-4's concern, not Task-5's.
    """

    def __init__(self, db: AtlasDB, session_id: str) -> None:
        self._db = db
        self._session_id = session_id

    def list_active(self) -> list[str]:
        return [self._session_id]

    def poll_output(self, session_id, since_id=None):
        return self._db.poll_messages(session_id, "out", since_id=since_id, limit=1000)

    # The bridge calls these defensively; keep them no-ops/None.
    def cleanup_zombies(self):
        return []

    def mark_outputs_delivered(self, session_id, up_to_id):
        return None


# ──────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────


def _expanded_events_via_bridge(db: AtlasDB, session_id: str) -> list[dict]:
    """Drive the REAL single expansion point and return the ordered events.

    Builds a bridge wired to a manager that reads ``db``'s out-rows, polls once,
    then drains the session outbox preserving order. This is the production
    re-expansion path (``_poll_process_outputs`` ->
    ``_expand_outbox_events`` -> ``_deliver_outbox_event``), not a re-impl.
    """
    bridge = _MultiUserBridge()
    bridge._process_manager = _DBPollManager(db, session_id)
    bridge._poll_process_outputs()
    session = bridge._ensure_session(session_id)
    events: list[dict] = []
    while True:
        try:
            events.append(session._outbox.get_nowait())
        except Exception:
            break
    return events


def _new_worker(tmp_path, *, monotonic_fn=None) -> SessionWorker:
    db_path = tmp_path / "runtime.db"
    return SessionWorker(
        session_id="alice/ip_alpha/rtl-gen",
        db_path=str(db_path),
        monotonic_fn=monotonic_fn,
    )


# ──────────────────────────────────────────────────────────────────────────
# 1. size-trigger
# ──────────────────────────────────────────────────────────────────────────


def test_size_trigger_bounds_rows_and_preserves_text_exactly(tmp_path):
    """1000 small emits + frozen timer + manual flush => bounded rows, exact text."""
    clock = _FakeClock()  # frozen: never advances -> the 50ms timer never fires.
    worker = _new_worker(tmp_path, monotonic_fn=clock)

    chunks = [f"<{i}>" for i in range(1000)]  # each is small (<4KB), 4 bytes each
    expected_text = "".join(chunks)
    for c in chunks:
        worker.emit_content(c)
    worker.flush_batcher()  # flush the final partial batch
    worker.close()

    events = _expanded_events_via_bridge(worker.db, worker.session_id)
    token_events = [e for e in events if e.get("type") == "token"]

    # Re-expansion must reproduce the input byte-for-byte, in order, once each.
    assert len(token_events) == len(chunks), "lost or duplicated token chunks"
    assert "".join(str(e.get("text")) for e in token_events) == expected_text

    # Row count is bounded by the documented 4KB math (size trigger only, since
    # the timer is frozen): rows ≈ ceil(total_bytes / 4096), with a small slack
    # because a chunk that crosses the boundary closes the current row.
    rows = worker.db.poll_messages(worker.session_id, "out", since_id=None, limit=10000)
    batch_rows = [r for r in rows if r.get("msg_type") == "token_batch"]
    total_bytes = len(expected_text.encode("utf-8"))
    bound = math.ceil(total_bytes / COALESCE_FLUSH_MAX_BYTES) + 1
    assert len(batch_rows) <= bound, (
        f"{len(batch_rows)} batch rows exceeds 4KB bound {bound} "
        f"(total_bytes={total_bytes})"
    )
    # And materially fewer than the un-coalesced 1000 (the whole point).
    assert len(batch_rows) < 50, "coalescing did not reduce row amplification"


def test_size_trigger_no_single_row_exceeds_cap_plus_one_chunk(tmp_path):
    """No emitted batch row holds more than ~4KB of text (cap is enforced)."""
    clock = _FakeClock()
    sink = _RecordingSink()
    batcher = _OutputBatcher(sink, monotonic_fn=clock)
    big = "x" * 500  # 500-byte chunks; 9 of them = 4500 bytes crosses 4096
    for _ in range(20):
        batcher.add_content(big)
    batcher.flush()
    for msg_type, payload in sink.rows:
        assert msg_type == "token_batch"
        text = "".join(c["text"] for c in payload["chunks"])
        # A row may overshoot by at most ONE final chunk (the one that crossed).
        assert len(text.encode("utf-8")) <= COALESCE_FLUSH_MAX_BYTES + len(big)


# ──────────────────────────────────────────────────────────────────────────
# 2. time-trigger (SEPARATE)
# ──────────────────────────────────────────────────────────────────────────


def test_time_trigger_advancing_past_50ms_flushes_exactly_once(tmp_path):
    """Advancing the fake clock past 50ms yields EXACTLY one flush."""
    clock = _FakeClock()
    sink = _RecordingSink()
    batcher = _OutputBatcher(sink, monotonic_fn=clock)

    # Buffer a few small chunks WELL under 4KB so the size trigger cannot fire.
    batcher.add_content("a")
    batcher.add_content("b")
    batcher.add_content("c")
    assert sink.rows == [], "size trigger fired prematurely"

    # Below the threshold: no flush yet.
    clock.advance(COALESCE_FLUSH_INTERVAL_S / 2)
    batcher.maybe_flush_timer()
    assert sink.rows == [], "timer flushed before 50ms elapsed"

    # Past the threshold: exactly one flush of the whole buffer.
    clock.advance(COALESCE_FLUSH_INTERVAL_S)
    batcher.maybe_flush_timer()
    assert len(sink.rows) == 1, f"expected exactly one flush, got {len(sink.rows)}"
    msg_type, payload = sink.rows[0]
    assert msg_type == "token_batch"
    assert [c["text"] for c in payload["chunks"]] == ["a", "b", "c"]

    # A second timer poll with nothing buffered must NOT flush again.
    clock.advance(COALESCE_FLUSH_INTERVAL_S * 10)
    batcher.maybe_flush_timer()
    assert len(sink.rows) == 1, "timer flushed an empty buffer"


def test_live_timer_flushes_on_emit_path_without_manual_poll(tmp_path):
    """#4 LIVE streaming timer: the emit/add path itself flushes once the 50ms
    interval has elapsed since the buffer's first chunk — WITHOUT anyone calling
    ``maybe_flush_timer()`` (which never runs mid-stream while the worker is busy
    streaming LLM tokens).

    Drives ``SessionWorker.emit_content`` (the real production emit path, not the
    raw batcher) with a fake monotonic clock: a few small tokens buffer with the
    clock frozen (no premature flush, all under 4KB), then advancing the clock
    past the interval and emitting one more token must flush the already-buffered
    chunks via the emit path alone. Text/order are preserved exactly.
    """
    clock = _FakeClock()
    worker = _new_worker(tmp_path, monotonic_fn=clock)

    # A few small tokens with the clock frozen: each is well under 4KB so the
    # size trigger cannot fire, and the live timer cannot fire (0 elapsed). No
    # out-row should exist yet — they are all still buffered.
    worker.emit_content("tok0")
    worker.emit_content("tok1")
    worker.emit_content("tok2")

    def _batch_rows():
        rows = worker.db.poll_messages(
            worker.session_id, "out", since_id=None, limit=10000
        )
        return [r for r in rows if r.get("msg_type") == "token_batch"]

    # No flush before the interval — the emit path must NOT flush early.
    assert _batch_rows() == [], "emit path flushed before the 50ms interval"

    # Stay strictly UNDER the interval, emit again: still no flush.
    clock.advance(COALESCE_FLUSH_INTERVAL_S / 2)
    worker.emit_content("tok3")
    assert _batch_rows() == [], "emit path flushed before the 50ms interval"

    # Cross the interval (since the buffer's FIRST chunk at t=0), then emit one
    # more token. The emit path itself must flush the accumulated buffer — we do
    # NOT call worker.maybe_flush_batcher_timer() / batcher.maybe_flush_timer().
    clock.advance(COALESCE_FLUSH_INTERVAL_S)  # now well past the interval
    worker.emit_content("tok4")

    rows_after = _batch_rows()
    assert len(rows_after) == 1, (
        "emit path did not live-flush after the interval "
        f"(got {len(rows_after)} batch rows)"
    )

    # The live flush emitted the chunks accumulated BEFORE tok4 (tok0..tok3);
    # tok4 opened a fresh buffer and is still pending until an explicit flush.
    worker.flush_batcher()
    worker.close()

    events = _expanded_events_via_bridge(worker.db, worker.session_id)
    token_events = [e for e in events if e.get("type") == "token"]
    # Exact text + order preserved across the live flush boundary, no loss/dup.
    assert [e.get("text") for e in token_events] == [
        "tok0", "tok1", "tok2", "tok3", "tok4",
    ]


def test_live_timer_flush_via_raw_batcher_add_path(tmp_path):
    """Same #4 guarantee at the batcher seam: ``add_content`` live-flushes the
    open buffer when the interval has elapsed, without ``maybe_flush_timer``."""
    clock = _FakeClock()
    sink = _RecordingSink()
    batcher = _OutputBatcher(sink, monotonic_fn=clock)

    batcher.add_content("a")  # opens buffer at t=0
    batcher.add_content("b")
    assert sink.rows == [], "size/live trigger fired prematurely"

    # Under the interval: another add must NOT flush.
    clock.advance(COALESCE_FLUSH_INTERVAL_S / 2)
    batcher.add_content("c")
    assert sink.rows == [], "add path flushed before the 50ms interval"

    # Past the interval: the next add flushes the open buffer FIRST (a,b,c),
    # then opens a new buffer holding the new chunk.
    clock.advance(COALESCE_FLUSH_INTERVAL_S)
    batcher.add_content("d")
    assert len(sink.rows) == 1, "add path did not live-flush after the interval"
    msg_type, payload = sink.rows[0]
    assert msg_type == "token_batch"
    assert [c["text"] for c in payload["chunks"]] == ["a", "b", "c"]

    # "d" is still buffered (new buffer opened at the live-flush time); an
    # explicit flush emits it on its own, preserving order.
    batcher.flush()
    assert len(sink.rows) == 2
    assert [c["text"] for c in sink.rows[1][1]["chunks"]] == ["d"]


def test_time_trigger_does_not_double_count_with_size(tmp_path):
    """Frozen clock + tiny payload => only a manual/explicit flush emits a row."""
    clock = _FakeClock()
    sink = _RecordingSink()
    batcher = _OutputBatcher(sink, monotonic_fn=clock)
    batcher.add_content("tiny")
    batcher.maybe_flush_timer()  # frozen clock -> no flush
    assert sink.rows == []
    batcher.flush()
    assert len(sink.rows) == 1


# ──────────────────────────────────────────────────────────────────────────
# 3. ordering — non-mergeable event forces flush in-position
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "emit_event",
    [
        lambda w: w.emit("tool", {"text": "ran_tool"}),
        lambda w: w.emit("cost", {"input": 1, "output": 2}),
        lambda w: w.emit("flush", {}),
        lambda w: w.emit("agent_state", {"running": True}),
        lambda w: w.emit("ask_user", {"flow_id": "qa_x", "question": "ok?"}),
        lambda w: w.emit("tool_result", {"text": "obs", "tool": "t"}),
        lambda w: w.emit("context", {"used": 1, "max": 2}),
        lambda w: w.emit("error", {"message": "boom"}),
    ],
    ids=["tool", "cost", "flush", "agent_state", "ask_user",
         "tool_result", "context", "error"],
)
def test_ordering_non_mergeable_flushes_between_tokens(tmp_path, emit_event):
    """token A, <non-mergeable>, token B => expanded order is A, event, B."""
    clock = _FakeClock()  # frozen: only the explicit-event flush moves rows
    worker = _new_worker(tmp_path, monotonic_fn=clock)

    worker.emit_content("A")
    emit_event(worker)
    worker.emit_content("B")
    worker.flush_batcher()
    worker.close()

    events = _expanded_events_via_bridge(worker.db, worker.session_id)
    types = [e.get("type") for e in events]

    # There must be a token A, then the non-mergeable event, then token B,
    # with the event strictly BETWEEN the two tokens (never after B).
    token_idxs = [i for i, e in enumerate(events) if e.get("type") == "token"]
    assert len(token_idxs) == 2, f"expected 2 token events, got {types}"
    a_idx, b_idx = token_idxs
    assert events[a_idx].get("text") == "A"
    assert events[b_idx].get("text") == "B"
    middle = types[a_idx + 1:b_idx]
    assert len(middle) >= 1, f"non-mergeable event was dropped or misordered: {types}"
    assert "token" not in middle, "a token leaked into the middle slot"
    # The non-mergeable event is delivered in-position (not behind B).
    assert b_idx == max(token_idxs)


def test_ordering_token_usage_emits_two_rows_uncoalesced(tmp_path):
    """token_usage emits TWO rows (cost + token_usage); neither is coalesced."""
    clock = _FakeClock()
    sink = _RecordingSink()
    batcher = _OutputBatcher(sink, monotonic_fn=clock)

    batcher.add_content("A")
    # Mirror SessionWorker.emit_token_usage: it calls emit("cost") then
    # emit("token_usage") — both non-mergeable, each flushes any open buffer.
    batcher.emit_passthrough("cost", {"input": 1})
    batcher.emit_passthrough("token_usage", {"input": 1})
    batcher.add_content("B")
    batcher.flush()

    types = [t for t, _ in sink.rows]
    # token_batch(A), cost, token_usage, token_batch(B) — order preserved,
    # token_usage's two rows both present and un-coalesced.
    assert types == ["token_batch", "cost", "token_usage", "token_batch"]


def test_ordering_reasoning_then_token_does_not_mix_buffers(tmp_path):
    """Switching mergeable kind flushes first; no mixed token/reasoning row."""
    clock = _FakeClock()
    sink = _RecordingSink()
    batcher = _OutputBatcher(sink, monotonic_fn=clock)
    batcher.add_reasoning("r1")
    batcher.add_reasoning("r2")
    batcher.add_content("t1")  # switch kind -> flush the reasoning batch first
    batcher.flush()
    types = [t for t, _ in sink.rows]
    assert types == ["reasoning_batch", "token_batch"]
    # Each row holds ONLY its own kind's chunks.
    assert [c["text"] for c in sink.rows[0][1]["chunks"]] == ["r1", "r2"]
    assert [c["text"] for c in sink.rows[1][1]["chunks"]] == ["t1"]


# ──────────────────────────────────────────────────────────────────────────
# 4. expansion parity
# ──────────────────────────────────────────────────────────────────────────


def test_expansion_parity_token_batch_matches_browser_shape(tmp_path):
    """token_batch expands to per-event {type:'token', text, cls?} (browser shape)."""
    clock = _FakeClock()
    worker = _new_worker(tmp_path, monotonic_fn=clock)
    worker.emit_content("hello ", cls="assistant")
    worker.emit_content("world")           # no cls
    worker.flush_batcher()
    worker.close()

    events = _expanded_events_via_bridge(worker.db, worker.session_id)
    token_events = [e for e in events if e.get("type") == "token"]
    assert len(token_events) == 2
    # First carries cls, second does not (parity with un-coalesced emit_content).
    assert token_events[0]["type"] == "token"
    assert token_events[0]["text"] == "hello "
    assert token_events[0]["cls"] == "assistant"
    assert token_events[1]["text"] == "world"
    assert "cls" not in token_events[1]
    # session_id is stamped (browser routes per session).
    assert token_events[0].get("session_id") == worker.session_id


def test_expansion_parity_reasoning_batch_matches_browser_shape(tmp_path):
    """reasoning_batch expands to per-event {type:'reasoning', text, blank}."""
    clock = _FakeClock()
    worker = _new_worker(tmp_path, monotonic_fn=clock)
    worker.emit_reasoning("thinking...", blank=False)
    worker.emit_reasoning("", blank=True)
    worker.flush_batcher()
    worker.close()

    events = _expanded_events_via_bridge(worker.db, worker.session_id)
    reasoning_events = [e for e in events if e.get("type") == "reasoning"]
    assert len(reasoning_events) == 2
    assert reasoning_events[0]["type"] == "reasoning"
    assert reasoning_events[0]["text"] == "thinking..."
    assert reasoning_events[0]["blank"] is False
    assert reasoning_events[1]["text"] == ""
    assert reasoning_events[1]["blank"] is True


def test_expansion_parity_matches_uncoalesced_single_row(tmp_path):
    """Coalesced expansion == what an un-coalesced single token row would yield.

    Writes ONE legacy un-coalesced ``token`` row directly, plus a ``token_batch``
    carrying the SAME chunk, and asserts the bridge produces an identical event
    dict for both (proves the browser can't tell them apart)."""
    db_path = tmp_path / "runtime.db"
    db = AtlasDB(str(db_path), schema_set="runtime")
    db.init_db()
    session_id = "bob/ip_beta/rtl-gen"

    # Legacy path: a single un-coalesced token row.
    db.enqueue_message(session_id, "out", "token", {"text": "chunk", "cls": "x"})
    legacy_events = _expanded_events_via_bridge(db, session_id)

    # Coalesced path: a token_batch carrying the identical chunk.
    db2_path = tmp_path / "runtime2.db"
    db2 = AtlasDB(str(db2_path), schema_set="runtime")
    db2.init_db()
    db2.enqueue_message(
        session_id, "out", "token_batch",
        {"chunks": [{"text": "chunk", "cls": "x"}]},
    )
    coalesced_events = _expanded_events_via_bridge(db2, session_id)

    legacy_tokens = [e for e in legacy_events if e.get("type") == "token"]
    coalesced_tokens = [e for e in coalesced_events if e.get("type") == "token"]
    assert len(legacy_tokens) == len(coalesced_tokens) == 1
    assert legacy_tokens[0] == coalesced_tokens[0]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
