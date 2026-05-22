"""Phase 3.5 Step 1 spike — verify the orchestrator can run on top of
``core/react_loop.py`` via ``ReactLoopDeps`` injection.

Run from common_ai_agent/:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 _runspaces/orchestrator_react_spike.py

What this proves (or fails to prove):

1. ``src/orchestrator/react_bridge.build_orchestrator_deps`` constructs a
   ReactLoopDeps without importing ``src.main`` (no leakage of generic-agent
   tool surface).
2. The resulting ``deps.available_tools`` has exactly the 8 orchestrator
   callables — generic agent tools (Read, Write, Edit, web_search, …) are
   NOT present.
3. Calling one of those callables persists an ``orchestrator_steps`` row.
4. yield_run is intercepted by ``deps.execute_tool_fn`` (not via
   ``available_tools``) and produces its own step row.
5. ``deps.build_prompt_fn`` embeds the 9 tool schemas (8 + yield_run) in the
   system prompt the LLM would see.
6. ``deps.compress_fn`` is a real compressor, not a stub.

Anything that's NOT here:
- End-to-end run of ``run_react_agent_impl`` with a stub LLM. That's Step 2.
- ``orchestrator_inject_fn`` exercise — needs an IP block + recent trace
  events to render context. Stubbed assertion only.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


def main() -> int:
    from core.atlas_db import AtlasDB
    from src.orchestrator.loop import OrchestratorContext
    from src.orchestrator.react_bridge import build_orchestrator_deps
    from src.orchestrator.runner import OrchestratorRunner

    failures = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        marker = "✓" if cond else "✗"
        line = f"  {marker} {label}"
        if not cond:
            failures.append((label, detail))
            line += f"\n      detail: {detail}"
        elif detail:
            line += f"  ({detail})"
        print(line, flush=True)

    with tempfile.TemporaryDirectory(prefix="orch_react_spike_") as workdir:
        db_path = str(Path(workdir) / "atlas.db")
        db = AtlasDB(db_path)
        db.init_db()
        runner = OrchestratorRunner(db, max_workers=1)
        try:
            run = db.create_orchestrator_run(
                user_id="spike-user", ip_id="spike-ip", session_id="spike-sess"
            )
            ctx = OrchestratorContext(
                run_id=run["id"],
                user_id="spike-user",
                ip_id="spike-ip",
                ip_name="ipSpike",
                session_id="spike-sess",
                project_root=Path(workdir),
                runner=runner,
            )

            print("[spike] building deps via build_orchestrator_deps(...)")
            bridge = build_orchestrator_deps(ctx=ctx, runner=runner, db=db)
            deps = bridge.deps

            # 1. No src.main import — confirms P1 finding addressed.
            check(
                "no `src.main` import",
                "src.main" not in sys.modules and "main" not in sys.modules,
                detail=(
                    "leaked module" if "src.main" in sys.modules else ""
                ),
            )

            # 2. available_tools has exactly the 8 orchestrator callables.
            expected = {
                "read_pipeline_state", "dispatch_workflow", "wait_job",
                "read_artifact", "classify_failure", "ask_user",
                "write_handoff", "mark_downstream_stale",
            }
            actual = set(deps.available_tools.keys())
            check(
                "available_tools == 8 orchestrator callables",
                actual == expected,
                detail=f"missing={sorted(expected - actual)} extra={sorted(actual - expected)}",
            )

            # 3. Calling a callable persists a step row.
            steps_before = len(db.list_orchestrator_steps(run["id"]))
            obs = deps.available_tools["read_pipeline_state"](
                pre_parsed_kwargs={"ip": "ipSpike"}
            )
            steps_after = len(db.list_orchestrator_steps(run["id"]))
            check(
                "read_pipeline_state callable returns a string observation",
                isinstance(obs, str) and len(obs) > 0,
                detail=f"observation={obs[:60]!r}",
            )
            check(
                "read_pipeline_state callable persists exactly +1 step row",
                steps_after - steps_before == 1,
                detail=f"before={steps_before} after={steps_after}",
            )
            latest = db.latest_orchestrator_step(run["id"])
            check(
                "latest step.tool_name == 'read_pipeline_state'",
                latest and latest["tool_name"] == "read_pipeline_state",
                detail=f"tool_name={latest and latest['tool_name']!r}",
            )

            # 4. yield_run is intercepted via execute_tool_fn (not via available_tools).
            check(
                "yield_run is NOT in available_tools",
                "yield_run" not in deps.available_tools,
                detail="yield_run must be wrapper-handled",
            )
            check(
                "execute_tool_fn callable is wired",
                callable(deps.execute_tool_fn),
            )

            # Exercise yield_run path with an after_seconds=0.05 timer so it
            # doesn't block forever.
            steps_before = len(db.list_orchestrator_steps(run["id"]))
            wake_reply = deps.execute_tool_fn(
                "yield_run",
                "",
                pre_parsed_kwargs={"wake_on": {"after_seconds": 0.05}},
            )
            steps_after = len(db.list_orchestrator_steps(run["id"]))
            check(
                "yield_run returned a wake reason string",
                isinstance(wake_reply, str) and "woken" in wake_reply,
                detail=f"reply={wake_reply!r}",
            )
            check(
                "yield_run persisted +1 step row",
                steps_after - steps_before == 1,
                detail=f"before={steps_before} after={steps_after}",
            )
            latest = db.latest_orchestrator_step(run["id"])
            check(
                "latest step.tool_name == 'yield_run'",
                latest and latest["tool_name"] == "yield_run",
                detail=f"tool_name={latest and latest['tool_name']!r}",
            )

            # 5. build_prompt_fn embeds 9 schemas (8 callables + yield_run).
            sys_prompt = deps.build_prompt_fn(
                messages=[{"role": "user", "content": "hi"}],
                allowed_tools=set(deps.available_tools.keys()),
                agent_mode="normal",
            )
            check(
                "build_prompt_fn returns a non-empty string",
                isinstance(sys_prompt, str) and len(sys_prompt) > 100,
                detail=f"len={len(sys_prompt) if isinstance(sys_prompt, str) else 0}",
            )
            names_seen = sum(
                1 for n in expected | {"yield_run"} if f'"name": "{n}"' in sys_prompt
            )
            check(
                "system prompt embeds all 9 tool schemas (8 + yield_run)",
                names_seen == 9,
                detail=f"names_seen={names_seen} of 9",
            )

            # 6. compress_fn is real (callable, not no-op stub).
            from core import compressor

            check(
                "compress_fn === core.compressor.compress_history",
                deps.compress_fn is compressor.compress_history,
                detail=f"compress_fn={deps.compress_fn!r}",
            )

            # 7. orchestrator_inject_fn is wired (ctx-bound).
            check(
                "orchestrator_inject_fn is wired",
                callable(deps.orchestrator_inject_fn),
            )

        finally:
            runner.shutdown(wait=True)
            db.close()

    print()
    if failures:
        print(f"[spike] FAILED — {len(failures)} check(s):")
        for label, detail in failures:
            print(f"   - {label}: {detail}")
        return 1
    print("[spike] OK — all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
