"""Deep DB↔Frontend integration test for the Phase 3 Pipeline UI redesign.

Locks the data contracts that EnhancedFlowCanvas / EnhancedDetailCards /
PhaseStrip / OrchestratorAskUserBanner read from atlas_ui.py routes so a
future code change can't silently break the redesign.

Coverage (gaps identified in /Users/brian/.claude/plans/database-shiny-liskov.md):
  1. /api/pipeline/state 15-stage idle fallback (canvas empty-state path)
  2. status enum normalization (frontend data-state contract)
  3. Two stages running concurrently (mockup parallel-dispatch scenario)
  4. /api/orchestrator/active_run paused + awaiting_user (banner contract)
  5. /api/orchestrator/active_run null when no active run (banner-hidden path)
  6. trigger_source round-trip workflow_runs → /api/pipeline/state (orch pill)
  7. PhaseStrip 6-phase aggregation against real backend stage ids
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Mirror frontend/atlas/pipeline.jsx — these are the only stage ids
# EnhancedFlowCanvas, EnhancedDetailCards, PhaseStrip ever render.
_EXPECTED_STAGE_IDS = [
    "ssot", "fl-model", "cl-model", "equivalence", "rtl",
    "lint", "tb", "sim", "coverage", "sim-debug",
    "syn", "sta", "pnr", "sta-post", "goal-audit",
]

# Mirror window.PIPELINE_PHASES in pipeline.jsx:97-103.
_PHASE_BANDS = [
    ("SSOT",       ["ssot"]),
    ("MODELS",     ["fl-model", "cl-model", "equivalence"]),
    ("RTL",        ["rtl"]),
    ("BRANCH",     ["lint", "tb", "sim"]),
    ("VERIFY·EDA", ["sim-debug", "coverage", "syn", "sta"]),
    ("SIGNOFF",    ["pnr", "sta-post", "goal-audit"]),
]


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    """Pattern lifted from tests/test_orchestrator_route.py:_make_client.

    Brings up atlas_ui.create_app() against a per-test ATLAS_DB_PATH, registers
    user 'u' with password 'pw', and returns the authenticated TestClient.
    Session cookie is retained for every subsequent request on this client.
    """
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def _lookup_user_id(db_path: Path) -> str:
    """Read back the DB user_id for the just-registered user 'u'. Needed so DB
    seeding of orchestrator_runs/workflow_runs uses an id the authenticated API
    request will match in find_active_run_for(user_id=...)."""
    from core.atlas_db import AtlasDB

    with AtlasDB(str(db_path)) as db:
        row = db._fetchone("SELECT id FROM users WHERE username = ?", ("u",))
    assert row is not None, "user 'u' not found in DB after register"
    return row["id"]


def _seed_workspace_and_ip(db_path: Path, tmp_path: Path, ip_name: str, user_id: str):
    """Replicate the upsert path the API takes when it hydrates an ip. Returns
    (workspace_id, ip_id) so the caller can attach workflow_runs / orchestrator_runs."""
    from core.atlas_db import AtlasDB

    (tmp_path / ip_name).mkdir(exist_ok=True)
    with AtlasDB(str(db_path)) as db:
        ws = db.upsert_workspace(
            tmp_path.name or "default",
            owner_user_id=user_id,
            local_path=str(tmp_path),
        )
        ipb = db.upsert_ip_block(ws["id"], ip_name)
    return ws["id"], ipb["id"]


# ── 1 ─────────────────────────────────────────────────────────────────────────
def test_pipeline_state_15_stages_all_idle_when_no_runs(tmp_path: Path, monkeypatch) -> None:
    """EnhancedFlowCanvas fallback render path: empty DB → 15 stage keys exist
    and every state is in the safe set {idle, locked, ready} so the canvas can
    paint a complete grid even before any run has fired."""
    ip = "fresh_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert list(data["stages"].keys()) == _EXPECTED_STAGE_IDS
    # ssot has no upstream → idle; everything downstream is locked until ssot fires.
    assert data["stages"]["ssot"]["state"] == "idle"
    for sid in _EXPECTED_STAGE_IDS:
        state = data["stages"][sid]["state"]
        assert state in {"idle", "locked", "ready"}, f"{sid}: unexpected initial state {state!r}"


# ── 2 ─────────────────────────────────────────────────────────────────────────
def test_pipeline_state_status_normalization(tmp_path: Path, monkeypatch) -> None:
    """Locks EnhancedFlowCanvas's data-state contract: every DB status value the
    backend may write must normalize to exactly one of the four UI states the
    canvas knows how to paint."""
    from core.atlas_db import AtlasDB

    ip = "norm_ip"
    db_path = tmp_path / "atlas.db"
    client = _make_client(tmp_path, monkeypatch)
    user_id = _lookup_user_id(db_path)
    ws_id, ip_id = _seed_workspace_and_ip(db_path, tmp_path, ip, user_id)

    # (workflow, db_status, expected_frontend_state)
    cases = [
        ("ssot-gen", "completed", "passed"),
        ("rtl-gen",  "running",   "running"),
        ("lint",     "error",     "failed"),
        ("tb-gen",   "blocked",   "failed"),
        ("sim",      "cancelled", "failed"),
        ("coverage", "success",   "passed"),  # 'success' is an accepted alias
    ]
    with AtlasDB(str(db_path)) as db:
        for wf, db_status, _ in cases:
            run = db.start_workflow_run(
                session_id="s", workspace_id=ws_id, ip_id=ip_id,
                workflow=wf, mode="pipeline", trigger="test",
            )
            if db_status != "running":
                err = f"{wf}-{db_status}" if db_status in {"error", "blocked", "cancelled"} else None
                db.finish_workflow_run(run["id"], status=db_status, error_summary=err)

    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text
    stages = resp.json()["stages"]

    # Per _PIPELINE_STAGES in src/atlas_api_jobs.py:40-55
    workflow_to_stage = {
        "ssot-gen": "ssot",
        "rtl-gen":  "rtl",
        "lint":     "lint",
        "tb-gen":   "tb",
        "sim":      "sim",
        "coverage": "coverage",
    }
    for wf, db_status, expected in cases:
        sid = workflow_to_stage[wf]
        actual = stages[sid]["state"]
        assert actual == expected, (
            f"{sid} (wf={wf}, db_status={db_status}): "
            f"expected {expected!r}, got {actual!r}"
        )


# ── 3 ─────────────────────────────────────────────────────────────────────────
def test_pipeline_state_two_stages_running_concurrently(tmp_path: Path, monkeypatch) -> None:
    """Pipeline Image mockup parallel-dispatch scenario: rtl-gen + sim both in
    flight. Locks the contract that lets EnhancedFlowCanvas pulse two cyan
    nodes simultaneously and EnhancedDetailCards emit two running detail cards
    side-by-side."""
    from core.atlas_db import AtlasDB

    ip = "parallel_ip"
    db_path = tmp_path / "atlas.db"
    client = _make_client(tmp_path, monkeypatch)
    user_id = _lookup_user_id(db_path)
    ws_id, ip_id = _seed_workspace_and_ip(db_path, tmp_path, ip, user_id)

    with AtlasDB(str(db_path)) as db:
        db.start_workflow_run(
            session_id="s", workspace_id=ws_id, ip_id=ip_id,
            workflow="rtl-gen", mode="pipeline", trigger="test",
        )  # left in default status='running'
        db.start_workflow_run(
            session_id="s", workspace_id=ws_id, ip_id=ip_id,
            workflow="sim", mode="pipeline", trigger="test",
        )

    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text
    stages = resp.json()["stages"]
    assert stages["rtl"]["state"] == "running"
    assert stages["sim"]["state"] == "running"
    # Sanity: at least these two are concurrently running.
    running_ids = {sid for sid, info in stages.items() if info["state"] == "running"}
    assert {"rtl", "sim"}.issubset(running_ids), running_ids


# ── 4 ─────────────────────────────────────────────────────────────────────────
def test_active_run_returns_paused_with_awaiting_user_question(tmp_path: Path, monkeypatch) -> None:
    """Locks the exact JSON shape OrchestratorAskUserBanner reads (pipeline.jsx
    lines 441-482):
        run.status === 'paused' && latest_step.verdict === 'awaiting_user'
            → render banner with latest_step.decision_json.args.question
    """
    from core.atlas_db import AtlasDB

    ip = "ask_user_ip"
    db_path = tmp_path / "atlas.db"
    client = _make_client(tmp_path, monkeypatch)
    user_id = _lookup_user_id(db_path)
    ws_id, ip_id = _seed_workspace_and_ip(db_path, tmp_path, ip, user_id)

    question = "need RTL approval before proceeding to lint"
    with AtlasDB(str(db_path)) as db:
        orun = db.create_orchestrator_run(
            user_id=user_id, ip_id=ip_id,
            session_id="s", workspace_id=ws_id,
            status="paused",
        )
        db.append_orchestrator_step(
            orun["id"],
            tool_name="ask_user",
            decision={"args": {"question": question}},
            verdict="awaiting_user",
        )

    resp = client.get(f"/api/orchestrator/active_run?ip={ip}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["ip"] == ip
    assert body["run"] is not None, "paused run not returned"
    assert body["run"]["status"] == "paused"
    assert body["latest_step"] is not None, "latest step not attached"
    assert body["latest_step"]["verdict"] == "awaiting_user"
    # decision_json may come back as a dict (json-parsed) or a JSON string —
    # accept both shapes so the assertion is robust against either DB driver.
    dec = body["latest_step"]["decision_json"]
    if isinstance(dec, str):
        dec = json.loads(dec)
    assert dec["args"]["question"] == question


# ── 5 ─────────────────────────────────────────────────────────────────────────
def test_active_run_returns_null_when_no_active(tmp_path: Path, monkeypatch) -> None:
    """Banner-hidden path: when no run is running/paused for the (user, ip),
    /api/orchestrator/active_run must return run=None so the React component
    short-circuits its render (pipeline.jsx line ~458 `if (!question) return null`)."""
    from core.atlas_db import AtlasDB

    ip = "no_active_ip"
    db_path = tmp_path / "atlas.db"
    client = _make_client(tmp_path, monkeypatch)
    user_id = _lookup_user_id(db_path)
    ws_id, ip_id = _seed_workspace_and_ip(db_path, tmp_path, ip, user_id)

    with AtlasDB(str(db_path)) as db:
        # 'completed' status does NOT match find_active_run_for's
        # status IN ('running', 'paused') filter.
        db.create_orchestrator_run(
            user_id=user_id, ip_id=ip_id,
            session_id="s", workspace_id=ws_id,
            status="completed",
        )

    resp = client.get(f"/api/orchestrator/active_run?ip={ip}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["run"] is None
    assert body["latest_step"] is None


# ── 6 ─────────────────────────────────────────────────────────────────────────
def test_trigger_source_orchestrator_chat_round_trips_to_pipeline_state(tmp_path: Path, monkeypatch) -> None:
    """Closes the gap test_trigger_source_write.py left open: the write path
    persists `trigger_source` to workflow_runs, but until now no test proved the
    value round-trips back through /api/pipeline/state. Without that
    round-trip the StageCard `pipe-stage-orch-pill` (restored in the swap-restoration
    session) never renders even when the DB row has the value."""
    from core.atlas_db import AtlasDB

    ip = "orch_trigger_ip"
    db_path = tmp_path / "atlas.db"
    client = _make_client(tmp_path, monkeypatch)
    user_id = _lookup_user_id(db_path)
    ws_id, ip_id = _seed_workspace_and_ip(db_path, tmp_path, ip, user_id)

    with AtlasDB(str(db_path)) as db:
        orun = db.create_orchestrator_run(
            user_id=user_id, ip_id=ip_id,
            session_id="s", workspace_id=ws_id,
            status="running",
        )
        db.start_workflow_run(
            session_id="s", workspace_id=ws_id, ip_id=ip_id,
            workflow="rtl-gen", mode="pipeline", trigger="orchestrator",
            trigger_source="orchestrator_chat",
            orchestrator_run_id=orun["id"],
        )

    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text
    rtl = resp.json()["stages"]["rtl"]
    assert rtl["state"] == "running"
    assert rtl.get("trigger_source") == "orchestrator_chat", (
        "trigger_source not surfaced in /api/pipeline/state — the orch pill "
        "won't render in StageCard. Field added in src/atlas_api_jobs.py:3157-3178."
    )
    assert rtl.get("orchestrator_run_id") == orun["id"]


# ── 7 ─────────────────────────────────────────────────────────────────────────
def test_phase_strip_aggregation_mixed_states(tmp_path: Path, monkeypatch) -> None:
    """PhaseStrip computes per-phase done/running/failed counts from
    pipelineState.stages. Verify the 6-phase taxonomy (SSOT/MODELS/RTL/BRANCH/
    VERIFY·EDA/SIGNOFF) aggregates correctly against real backend stage ids."""
    from core.atlas_db import AtlasDB

    ip = "mid_flight_ip"
    db_path = tmp_path / "atlas.db"
    client = _make_client(tmp_path, monkeypatch)
    user_id = _lookup_user_id(db_path)
    ws_id, ip_id = _seed_workspace_and_ip(db_path, tmp_path, ip, user_id)

    # fl-model-gen drives THREE stages (fl-model, cl-model, equivalence) per
    # _PIPELINE_STAGES, so a single completed row populates all of MODELS.
    seeds = [
        ("ssot-gen",     "completed"),
        ("fl-model-gen", "completed"),
        ("rtl-gen",      "running"),
        ("sim",          "running"),
    ]
    with AtlasDB(str(db_path)) as db:
        for wf, status in seeds:
            run = db.start_workflow_run(
                session_id="s", workspace_id=ws_id, ip_id=ip_id,
                workflow=wf, mode="pipeline", trigger="test",
            )
            if status != "running":
                db.finish_workflow_run(run["id"], status=status)

    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text
    stages = resp.json()["stages"]

    def _phase_counts(stage_ids):
        passed = sum(1 for s in stage_ids if stages.get(s, {}).get("state") == "passed")
        running = sum(1 for s in stage_ids if stages.get(s, {}).get("state") == "running")
        failed = sum(1 for s in stage_ids if stages.get(s, {}).get("state") == "failed")
        return (passed, running, failed)

    counts = {name: _phase_counts(stage_ids) for name, stage_ids in _PHASE_BANDS}

    # SSOT: 1 passed (ssot-gen completed) → 1/1 done
    assert counts["SSOT"] == (1, 0, 0), counts
    # MODELS: fl-model-gen completed drives fl-model/cl-model/equivalence → 3/3 done
    assert counts["MODELS"] == (3, 0, 0), counts
    # RTL: rtl-gen running → 0 done, 1 running
    assert counts["RTL"] == (0, 1, 0), counts
    # BRANCH (lint, tb, sim): only sim is running → 1 running
    assert counts["BRANCH"][1] == 1, counts
    assert counts["BRANCH"][0] == 0, counts
    # VERIFY·EDA, SIGNOFF: nothing seeded
    assert counts["VERIFY·EDA"] == (0, 0, 0), counts
    assert counts["SIGNOFF"] == (0, 0, 0), counts
