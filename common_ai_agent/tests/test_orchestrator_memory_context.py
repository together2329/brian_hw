from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.atlas_db import AtlasDB
from src.orchestrator.loop import OrchestratorContext
from src.orchestrator.react_bridge import build_orchestrator_deps
from src.orchestrator.runner import OrchestratorRunner


def test_orchestrator_prompt_includes_db_backed_user_memory(
    tmp_path: Path, monkeypatch
) -> None:
    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    user = db.ensure_user_by_username("alice")
    db.add_user_memory_rule(user["id"], "Always answer Alice in Korean")
    db.add_user_memory_rule(
        user["id"],
        "Mention live pipeline status first",
        workflow="orchestrator",
    )
    runner = OrchestratorRunner(db, max_workers=1)
    try:
        ctx = OrchestratorContext(
            run_id="run-1",
            user_id=user["id"],
            ip_id="ip-1",
            ip_name="ipA",
            session_id="alice/default/ipA/orchestrator",
            project_root=tmp_path,
            runner=runner,
        )
        monkeypatch.setenv("ATLAS_ACTIVE_SESSION", ctx.session_id)
        monkeypatch.setenv("ATLAS_MEMORY_USER", "alice")
        monkeypatch.setenv("ATLAS_MEMORY_DB_PATH", str(db_path))
        monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "runtime.db"))

        bridge = build_orchestrator_deps(ctx=ctx, runner=runner, db=db)
        prompt = bridge.deps.build_prompt_fn(
            messages=[{"role": "user", "content": "status?"}],
            allowed_tools=set(bridge.available_tools.keys()),
            agent_mode="normal",
        )

        assert "=== MEMORY RULES ===" in prompt
        assert "User memory scope: alice" in prompt
        assert "Active workflow scope: orchestrator" in prompt
        assert "Always answer Alice in Korean" in prompt
        assert "Mention live pipeline status first" in prompt
    finally:
        runner.shutdown(wait=True)
        db.close()
