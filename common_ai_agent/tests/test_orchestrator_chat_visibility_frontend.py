"""Orchestrator chat panel output-visibility invariants (pipeline-rail.tsx).

Defect (2026-06-10): the panel disabled polling whenever a live WS backend was
connected (`if (!hasLiveBackend) schedulePoll(...)`) while the server has no
`orchestrator_chat` WS emitter, so after the mount fetch the feed never
updated; submitMessage also ignored the POST response, so rejected sends
(401/403) were invisible. Behavioral coverage lives in
frontend/atlas/__tests__/pipeline-rail-orchestrator-chat-visibility.test.tsx
(vitest); these source invariants keep the fix from regressing silently.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAIL = PROJECT_ROOT / "frontend" / "atlas" / "pipeline-rail.tsx"
VITEST = (
    PROJECT_ROOT / "frontend" / "atlas" / "__tests__"
    / "pipeline-rail-orchestrator-chat-visibility.test.tsx"
)


def test_orchestrator_chat_polls_regardless_of_live_backend():
    src = RAIL.read_text(encoding="utf-8")
    # No poll-scheduling call may be gated on the WS channel being absent.
    assert "if (!hasLiveBackend) schedulePoll" not in src
    assert "if (!hasLiveBackend) {" not in src
    # Success path reschedules unconditionally at the active/idle cadence.
    assert (
        "schedulePoll(isActive ? ORCH_CHAT_POLL_INTERVAL_ACTIVE_MS : "
        "ORCH_CHAT_POLL_INTERVAL_IDLE_MS);" in src
    )


def test_orchestrator_chat_send_surfaces_failures_and_refetches():
    src = RAIL.read_text(encoding="utf-8")
    assert "notifySendFailure" in src
    assert "message not delivered" in src
    # Rejected sends must be checked and surfaced, successful sends must pull
    # the persisted user message + ack into the feed immediately.
    assert "if (!r.ok)" in src
    assert "fetchOnceRef.current?.()" in src


def test_behavioral_vitest_suite_present():
    src = VITEST.read_text(encoding="utf-8")
    for name in (
        "keeps polling /api/orchestrator/chat/messages even when a live WS backend is subscribed",
        "renders a local failure notice when the send POST is rejected",
        "refetches messages immediately after a successful send",
    ):
        assert name in src, f"vitest case missing: {name}"
