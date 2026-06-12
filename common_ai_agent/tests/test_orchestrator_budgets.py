"""Deep tests for Phase 4 per-stage retry budget tracker.

Covers:
- BudgetTracker unit behavior (allow/refuse, snapshot, reset)
- Integration through react_bridge.dispatch_workflow callable: the 6th
  rtl-gen dispatch is refused with a clean error visible to the LLM.
"""

from __future__ import annotations

import pytest

from core.atlas_db import AtlasDB
from src.orchestrator import tools as orch_tools
from src.orchestrator.budgets import BudgetTracker, default_budget_for
from src.orchestrator.loop import OrchestratorContext
from src.orchestrator.react_bridge import build_orchestrator_deps
from src.orchestrator.runner import OrchestratorRunner


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


class TestDefaultBudgets:
    def test_known_stages_match_system_prompt_table(self):
        # workflow/orchestrator/system_prompt.md lines 65-73
        assert default_budget_for("ssot-gen") == 3
        assert default_budget_for("rtl-gen") == 5
        assert default_budget_for("tb-gen") == 3
        assert default_budget_for("sim") == 2
        assert default_budget_for("sim_debug") == 1
        assert default_budget_for("coverage") == 2
        assert default_budget_for("goal-audit") == 1

    def test_unknown_stage_gets_fallback(self):
        # The doc table is incomplete (no syn/sta/pnr in retry section);
        # the tracker has its own conservative defaults for those.
        assert default_budget_for("magic-stage-99") == 4


class TestBudgetTracker:
    def test_allows_until_budget_exhausted(self):
        bt = BudgetTracker()
        budget = default_budget_for("rtl-gen")
        for i in range(1, budget + 1):
            d = bt.attempt("rtl-gen")
            assert d["allowed"] is True, f"attempt {i} should be allowed"
            assert d["attempts"] == i
            assert d["budget"] == budget
        # The (budget+1)th attempt is refused.
        d = bt.attempt("rtl-gen")
        assert d["allowed"] is False
        assert d["attempts"] == budget + 1

    def test_subsequent_calls_after_exhaustion_stay_refused(self):
        bt = BudgetTracker()
        for _ in range(default_budget_for("sim") + 5):
            d = bt.attempt("sim")
        assert d["allowed"] is False
        assert d["attempts"] == default_budget_for("sim") + 5

    def test_reset_clears_counter(self):
        bt = BudgetTracker()
        for _ in range(3):
            bt.attempt("sim")
        bt.reset("sim")
        d = bt.attempt("sim")
        assert d["allowed"] is True
        assert d["attempts"] == 1

    def test_override_takes_precedence_over_default(self):
        bt = BudgetTracker(overrides={"rtl-gen": 1})
        d1 = bt.attempt("rtl-gen")
        d2 = bt.attempt("rtl-gen")
        assert d1["allowed"] is True and d1["budget"] == 1
        assert d2["allowed"] is False

    def test_snapshot_shows_per_stage_attempts(self):
        bt = BudgetTracker()
        bt.attempt("rtl-gen")
        bt.attempt("rtl-gen")
        bt.attempt("sim")
        snap = bt.snapshot()
        assert snap == {"rtl-gen": 2, "sim": 1}

    def test_empty_workflow_is_passthrough_allowed(self):
        bt = BudgetTracker()
        d = bt.attempt("")
        assert d["allowed"] is True


class TestBridgeIntegration:
    @pytest.fixture
    def runner(self, db):
        r = OrchestratorRunner(db, max_workers=1)
        yield r
        r.shutdown(wait=True)

    @pytest.fixture
    def ctx(self, db, runner, tmp_path):
        run = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        return OrchestratorContext(
            run_id=run["id"],
            user_id="u1",
            ip_id="ip1",
            ip_name="ipA",
            session_id="s1",
            project_root=tmp_path,
            runner=runner,
        )

    def test_dispatch_workflow_callable_refuses_after_budget_exhausted(self, db, ctx, monkeypatch):
        # Stub the underlying dispatch bridge so we only test budget logic.
        monkeypatch.setattr(
            orch_tools, "_dispatch_workflow_bridge",
            lambda: lambda **kw: {"ok": True, "pipeline_run_id": "pr", "jobs": []},
        )
        bridge = build_orchestrator_deps(ctx=ctx, runner=ctx.runner, db=db)
        budget = default_budget_for("rtl-gen")
        # First `budget` calls succeed.
        for i in range(budget):
            obs = bridge.available_tools["dispatch_workflow"](
                pre_parsed_kwargs={"workflow": "rtl-gen", "ip": "ipA"}
            )
            assert "exhausted" not in obs.lower(), f"call {i+1} should be allowed: {obs!r}"
        # Next call must be refused.
        obs = bridge.available_tools["dispatch_workflow"](
            pre_parsed_kwargs={"workflow": "rtl-gen", "ip": "ipA"}
        )
        assert "exhausted" in obs.lower()
        # The step row records tool_failed verdict so the LLM can react.
        step = db.latest_orchestrator_step(ctx.run_id)
        assert step["tool_name"] == "dispatch_workflow"
        assert step["verdict"] == "tool_failed"

    def test_stages_list_each_counted_separately(self, db, ctx, monkeypatch):
        monkeypatch.setattr(
            orch_tools, "_dispatch_workflow_bridge",
            lambda: lambda **kw: {"ok": True, "pipeline_run_id": "pr", "jobs": []},
        )
        bridge = build_orchestrator_deps(ctx=ctx, runner=ctx.runner, db=db)
        # One call with stages=["rtl-gen","lint","syn"] consumes one attempt
        # FROM EACH stage's budget.
        bridge.available_tools["dispatch_workflow"](
            pre_parsed_kwargs={"stages": ["rtl-gen", "lint", "syn"], "ip": "ipA"}
        )
        snap = bridge.budgets.snapshot()
        assert snap.get("rtl-gen") == 1
        assert snap.get("lint") == 1
        assert snap.get("syn") == 1

    def test_final_workflow_does_not_consume_budget(self, db, ctx, monkeypatch):
        monkeypatch.setattr(
            orch_tools, "_dispatch_workflow_bridge",
            lambda: lambda **kw: {"ok": True, "pipeline_run_id": "pr", "jobs": []},
        )
        bridge = build_orchestrator_deps(ctx=ctx, runner=ctx.runner, db=db)
        # Many __final__ calls — the loop terminator — must not consume budget.
        for _ in range(10):
            bridge.available_tools["dispatch_workflow"](
                pre_parsed_kwargs={"workflow": "__final__",
                                    "payload": {"state": "completed"}}
            )
        # __final__ is not a real workflow; budgets snapshot should be empty.
        assert bridge.budgets.snapshot() == {}

    def test_mark_downstream_stale_resets_downstream_budget(self, db, ctx, monkeypatch):
        monkeypatch.setattr(
            orch_tools, "_dispatch_workflow_bridge",
            lambda: lambda **kw: {"ok": True, "pipeline_run_id": "pr", "jobs": []},
        )
        monkeypatch.setattr(
            orch_tools,
            "_pipeline_stage_deps",
            lambda: {
                "sim": ("tb",),
                "sim-debug": ("sim",),
                "coverage": ("sim",),
            },
        )
        bridge = build_orchestrator_deps(ctx=ctx, runner=ctx.runner, db=db)

        # Exhaust sim_debug in this orchestrator run.
        for _ in range(default_budget_for("sim_debug") + 1):
            obs = bridge.available_tools["dispatch_workflow"](
                pre_parsed_kwargs={"workflow": "sim_debug", "ip": "ipA"}
            )
        assert "exhausted" in obs.lower()

        # A new sim artifact makes sim_debug/coverage fresh downstream work.
        bridge.available_tools["mark_downstream_stale"](
            pre_parsed_kwargs={"from_stage": "sim"}
        )
        obs = bridge.available_tools["dispatch_workflow"](
            pre_parsed_kwargs={"workflow": "sim_debug", "ip": "ipA"}
        )
        assert "exhausted" not in obs.lower()
        assert bridge.budgets.snapshot().get("sim_debug") == 1

    def test_upstream_dispatch_resets_downstream_budget_automatically(self, db, ctx, monkeypatch):
        """Finding 40: a fresh upstream dispatch invalidates downstream evidence.

        The live cnt8 autonomy probe reran sim after sim_debug had already used
        its only retry. That newer sim made sim-debug stale, but the second
        sim_debug dispatch was refused as attempts=2 budget=1 because only the
        optional mark_downstream_stale tool reset budgets. Dispatching the
        upstream stage itself must reset downstream budgets deterministically.
        """
        monkeypatch.setattr(
            orch_tools, "_dispatch_workflow_bridge",
            lambda: lambda **kw: {"ok": True, "pipeline_run_id": "pr", "jobs": []},
        )
        monkeypatch.setattr(
            orch_tools,
            "_pipeline_stage_deps",
            lambda: {
                "sim": ("tb",),
                "sim-debug": ("sim",),
                "coverage": ("sim",),
            },
        )
        bridge = build_orchestrator_deps(ctx=ctx, runner=ctx.runner, db=db)

        for _ in range(default_budget_for("sim_debug") + 1):
            obs = bridge.available_tools["dispatch_workflow"](
                pre_parsed_kwargs={"workflow": "sim_debug", "ip": "ipA"}
            )
        assert "exhausted" in obs.lower()

        obs = bridge.available_tools["dispatch_workflow"](
            pre_parsed_kwargs={"workflow": "sim", "ip": "ipA"}
        )
        assert "exhausted" not in obs.lower()
        assert "sim_debug" not in bridge.budgets.snapshot()

        obs = bridge.available_tools["dispatch_workflow"](
            pre_parsed_kwargs={"workflow": "sim_debug", "ip": "ipA"}
        )
        assert "exhausted" not in obs.lower()
        assert bridge.budgets.snapshot().get("sim_debug") == 1
