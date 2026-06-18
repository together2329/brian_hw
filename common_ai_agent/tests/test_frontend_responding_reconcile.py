"""Frontend responding-state reconciliation source invariants.

The behavioral UI coverage lives in
frontend/atlas/__tests__/workspace-render-smoke.test.tsx (vitest). This pytest
node is the platform-ontology evidence hook: it keeps the fix visible to the
repo-level checker and makes sure the worker-status poll still routes stale
responding state through the normal finishLiveRun path.
"""
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_HOOK = PROJECT_ROOT / "frontend" / "atlas" / "workspace-root-data-hook.tsx"
APP_SESSION_HOOK = PROJECT_ROOT / "frontend" / "atlas" / "app-session-hook.tsx"
FEED_CARDS = PROJECT_ROOT / "frontend" / "atlas" / "workspace-feed-cards.tsx"
FEED_COMPLETION = PROJECT_ROOT / "frontend" / "atlas" / "workspace-rootdata-feed-completion.tsx"
CHAT_FRAME = PROJECT_ROOT / "frontend" / "atlas" / "workspace-chat-markdown-frame.tsx"
STYLES = PROJECT_ROOT / "frontend" / "atlas" / "styles.css"
VITEST = (
    PROJECT_ROOT
    / "frontend"
    / "atlas"
    / "__tests__"
    / "workspace-render-smoke.test.tsx"
)


def test_frontend_responding_reconciles_ready_idle_worker_status():
    src = DATA_HOOK.read_text(encoding="utf-8")
    vitest = VITEST.read_text(encoding="utf-8")

    assert "RESPONDING_IDLE_RECONCILE_GRACE_MS = 10_000" in src
    assert "workerStatusConfirmsRespondingIdle" in src
    assert "status.state === 'ready'" in src
    assert "status.alive === true" in src
    assert "status.running === false" in src
    assert "shouldReconcileRespondingFromWorkerStatus" in src
    assert "orchestratorMode" in src
    assert "finishLiveRunRef.current?.()" in src
    assert "streaming: !!streamingRef.current" in src
    assert "agentRunning: w.ATLAS_AGENT_RUNNING === true" in src
    assert "reconciles stale Agent responding from ready/not-running worker status only after grace" in vitest


def test_frontend_completed_run_hydrates_persisted_assistant_snapshot():
    src = DATA_HOOK.read_text(encoding="utf-8")
    vitest = VITEST.read_text(encoding="utf-8")

    assert "conversationSnapshotExtendsLiveFeed" in src
    assert "preservingLiveFeed && !conversationSnapshotExtendsLiveFeed(prev, newFeed)" in src
    assert "refreshActiveConversation(sid, { force: true })" in src
    assert "streamingRef.current = false" in src
    assert "hydrates persisted assistant output when the saved conversation extends the live feed" in vitest


def test_frontend_completed_agent_cards_keep_runtime_metadata_and_tight_body():
    completion = FEED_COMPLETION.read_text(encoding="utf-8")
    cards = FEED_CARDS.read_text(encoding="utf-8")
    frame = CHAT_FRAME.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")
    vitest = VITEST.read_text(encoding="utf-8")

    assert "runtimeMetaFromConversationMessage" in completion
    assert "newFeed.push({ kind: 'agent', text: content, ...runtimeMetaFromConversationMessage(m) })" in completion
    assert "agentRuntimeParts" in cards
    assert "AgentRuntimePill" in cards
    assert "<AgentRuntimePill entry={entry} />" in cards
    assert ".chat-message-runtime" in styles
    assert ".feed-entry-agent .chat-message-head" in styles
    assert "useState(24)" in frame
    assert "minHeight: 24" in frame
    assert "preserves completed assistant runtime metadata when hydrating conversation history" in vitest


def test_frontend_roster_refresh_preserves_confirmed_session_route():
    src = APP_SESSION_HOOK.read_text(encoding="utf-8")

    assert "initialUrlStillOwnsLiveRoute" in src
    assert "healthzConfirmsLiveRoute" in src
    assert "ctx.active_session || ctx.activeSession" in src
    assert "ctx.active_ip || ctx.activeIp" in src
    assert "!healthzConfirmsLiveRoute" in src
    assert "liveNamespace = namespaceFor(owner, WORKFLOW_DEFAULT, wf)" in src
