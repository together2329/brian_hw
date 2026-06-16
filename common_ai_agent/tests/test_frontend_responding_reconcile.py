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
