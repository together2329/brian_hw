"""
Meta-gate: a gate is not trusted until it proves it can REJECT bad input.

This is the workflow-level fix for the recurring silent-PASS failure mode. A
"gate" (a check/closure command in STAGE_MANIFEST, or an engine-internal content
gate) is only meaningful if a deliberately-degraded input makes it fail. Per-gate
predicate fixes (the A-series) close individual holes; this file closes the
*process* hole that let hollow gates ship in the first place:

  1. enumerate every gate-like command in STAGE_MANIFEST,
  2. RATCHET — require each to be acknowledged in the registry (covered,
     uncovered-backlog, or advisory); a NEW gate that ships unregistered fails,
  3. run the self-test (good fixture + mutation battery -> assert kill-all) for
     every COVERED gate,
  4. keep the UNCOVERED backlog explicit and FROZEN, so it can only shrink by a
     reviewed change, never grow silently.

To retire backlog: write a GateSelfTest for the gate, move it from UNCOVERED_GATES
into COVERED_GATES, and update the frozen set. Goal state: UNCOVERED_GATES == {}.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_derive_tb_todos import (
    _GOOD_COVERAGE,
    _GOOD_EVENT,
    _mut_comment_only_scoreboard,
    _mut_empty_tb_bodies,
    _run,
    _write_evidence,
    _write_ip,
    _write_tb_artifacts,
)

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "workflow" / "STAGE_MANIFEST.json"


# ---------------------------------------------------------------------------
# Reusable harness: the known-good fixture must pass; each mutation must NOT.
# ---------------------------------------------------------------------------

class GateSelfTest:
    """A gate's defining proof: it passes a known-good fixture and rejects every
    deliberate degradation of the property it claims to enforce."""

    def __init__(self, *, build_good, run_gate, read_status, mutations):
        self.build_good = build_good    # (work_dir) -> ctx
        self.run_gate = run_gate        # (work_dir, ctx) -> None (invokes the gate)
        self.read_status = read_status  # (work_dir, ctx) -> str  (the gate verdict)
        self.mutations = mutations      # list[(name, mutate(work_dir, ctx))]

    def assert_kills_all(self, tmp_path_factory, gate_id: str) -> None:
        good = tmp_path_factory.mktemp(f"{gate_id}__good")
        ctx = self.build_good(good)
        self.run_gate(good, ctx)
        assert self.read_status(good, ctx) == "pass", (
            f"{gate_id}: known-good fixture must pass, gate is broken the other way"
        )
        for name, mutate in self.mutations:
            work = tmp_path_factory.mktemp(f"{gate_id}__{name}")
            ctx = self.build_good(work)
            mutate(work, ctx)
            self.run_gate(work, ctx)
            assert self.read_status(work, ctx) != "pass", (
                f"{gate_id}: SILENT-PASS on mutation `{name}` — gate does not enforce its contract"
            )


# ---------------------------------------------------------------------------
# tb contract-ledger gate self-test (reuses the A0 fixtures/mutations)
# ---------------------------------------------------------------------------

_TB_IP = "gate_tb"


def _tb_build_good(work: Path) -> str:
    ip_dir = _write_ip(work, _TB_IP)
    _write_tb_artifacts(ip_dir, _TB_IP)
    _write_evidence(ip_dir, event=_GOOD_EVENT, coverage=_GOOD_COVERAGE)
    return _TB_IP


def _tb_run_gate(work: Path, ip: str) -> None:
    _run(work, ip, "--audit-tb")
    _run(work, ip, "--audit-evidence")


def _tb_read_status(work: Path, ip: str) -> str:
    plan = json.loads((work / ip / "tb" / "tb_todo_plan.json").read_text(encoding="utf-8"))
    return plan["gate"]["status"]


def _tb_mut_vacuous_row(work: Path, ip: str) -> None:
    _write_evidence(
        work / ip,
        event={
            "goal_id": "EQ_READ", "scenario_id": "", "stimulus": {},
            "fl_expected": {}, "rtl_observed": {}, "passed": True, "coverage_refs": [],
        },
        coverage=_GOOD_COVERAGE,
    )


def _tb_mut_coverage_without_status(work: Path, ip: str) -> None:
    _write_evidence(work / ip, event=_GOOD_EVENT, coverage={"note": "no status field"})


TB_CONTRACT_LEDGER_SELF_TEST = GateSelfTest(
    build_good=_tb_build_good,
    run_gate=_tb_run_gate,
    read_status=_tb_read_status,
    mutations=[
        ("comment_only_scoreboard", lambda w, ip: _mut_comment_only_scoreboard(w / ip, ip)),
        ("empty_tb_bodies", lambda w, ip: _mut_empty_tb_bodies(w / ip, ip)),
        ("vacuous_scoreboard_row", _tb_mut_vacuous_row),
        ("coverage_without_status", _tb_mut_coverage_without_status),
    ],
)


# ---------------------------------------------------------------------------
# Gate registry — single source of truth.
# ---------------------------------------------------------------------------

# Covered: gate has a mutation self-test proving it kills hollow input.
COVERED_GATES = {
    # Engine-internal content gate (NOT listed as a STAGE_MANIFEST stage command).
    "tb_contract_ledger": {
        "scripts": ("derive_tb_todos.py",),
        "self_test": TB_CONTRACT_LEDGER_SELF_TEST,
    },
}

# Explicit, FROZEN backlog: acknowledged gates that still lack a direct
# mutation self-test. Shrinks only by a reviewed change (see module docstring).
UNCOVERED_GATES = {
    "check_contract_bundle.py": "req contract-authority gate (content-mutation covered indirectly in test_workflow_stage_engine; needs a direct gate self-test)",
    "check_ip_signoff.py": "final signoff aggregate gate",
    "check_truth_coverage.py": "locked-truth obligation coverage gate",
    "run_contract_check.py": "contract-reflection closure gate (incl. --require-contract-closure strict)",
    "check_scoreboard_events.py": "scoreboard schema / FL-source / observable gate",
    "check_tb_python_compile.py": "pre-sim TB python compile gate",
    "ssot_coverage_summary.py": "functional coverage summary (pass/fail status)",
    "dut_lint_report.py": "DUT lint/suppression gate",
    "rtl_compile_report.py": "DUT RTL compile gate",
    "derive_rtl_todos.py": "RTL final static/todo closure gate (--enforce)",
}

# Gate-shaped but advisory: no hard pass/fail contract, so no kill-proof required.
ADVISORY_NOT_GATE = {
    "mutation_guard.py": "advisory mutant kill-rate signal, not a pass/fail gate",
}


# ---------------------------------------------------------------------------
# Manifest enumeration + gate detection
# ---------------------------------------------------------------------------

def _iter_manifest_commands() -> list[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cmds: list[str] = []
    for ep in (data.get("entrypoints") or {}).values():
        if ep.get("command"):
            cmds.append(ep["command"])
    for stage in data.get("stages") or []:
        for key in ("command", "strict_command"):
            if stage.get(key):
                cmds.append(stage[key])
    return cmds


def _script_basename(command: str) -> str | None:
    for tok in command.split():
        if tok.endswith(".py") or tok.endswith(".sh"):
            return Path(tok).name
    return None


# A command is a gate if its job is to REJECT bad input: a check_* script, an
# explicit enforcement flag, or a known closure/report gate.
_EXPLICIT_GATE_SCRIPTS = {
    "run_contract_check.py",
    "ssot_coverage_summary.py",
    "dut_lint_report.py",
    "rtl_compile_report.py",
}


def _is_gate_command(command: str) -> bool:
    base = _script_basename(command) or ""
    if base.startswith("check_"):
        return True
    if "--enforce" in command or "--require" in command:
        return True
    return base in _EXPLICIT_GATE_SCRIPTS


def _registered_scripts() -> set[str]:
    reg = set(UNCOVERED_GATES) | set(ADVISORY_NOT_GATE)
    for spec in COVERED_GATES.values():
        reg |= set(spec["scripts"])
    return reg


# ---------------------------------------------------------------------------
# Meta-gate tests
# ---------------------------------------------------------------------------

def test_every_manifest_gate_is_registered():
    """Ratchet: a gate-like command in STAGE_MANIFEST must be acknowledged in the
    registry. A new hollow gate cannot ship without either a self-test or an
    explicit UNCOVERED_GATES entry."""
    registered = _registered_scripts()
    unregistered = sorted({
        _script_basename(cmd)
        for cmd in _iter_manifest_commands()
        if _is_gate_command(cmd) and _script_basename(cmd) not in registered
    })
    assert not unregistered, (
        "Unregistered gate(s) in STAGE_MANIFEST — add a GateSelfTest or acknowledge "
        f"in UNCOVERED_GATES: {unregistered}"
    )


def test_ratchet_can_fail_on_an_unregistered_gate():
    """The meta-gate must itself be killable: a gate-shaped command that is not in
    the registry is detected as unregistered. (A meta-gate that cannot fail would
    be the same silent-PASS sin one level up.)"""
    fake = "python3 workflow/new/scripts/check_brand_new_thing.py <ip> --root <ip-parent>"
    assert _is_gate_command(fake), "detector failed to recognize a check_* gate"
    assert _script_basename(fake) == "check_brand_new_thing.py"
    assert _script_basename(fake) not in _registered_scripts(), (
        "fixture script should be unregistered for this proof"
    )


@pytest.mark.parametrize("gate_id", sorted(COVERED_GATES))
def test_covered_gate_self_test_kills_all_mutations(gate_id, tmp_path_factory):
    """Every covered gate must pass a known-good fixture and reject every mutation."""
    COVERED_GATES[gate_id]["self_test"].assert_kills_all(tmp_path_factory, gate_id)


def test_uncovered_backlog_is_explicit_and_frozen(capsys):
    """The backlog of not-yet-self-tested gates is explicit and frozen, so it can
    only shrink by a reviewed change. Goal state: UNCOVERED_GATES == {}."""
    with capsys.disabled():
        print(
            f"\n[gate-self-test] covered={sorted(COVERED_GATES)} | "
            f"uncovered={len(UNCOVERED_GATES)} -> {sorted(UNCOVERED_GATES)}"
        )
    frozen = {
        "check_contract_bundle.py",
        "check_ip_signoff.py",
        "check_truth_coverage.py",
        "run_contract_check.py",
        "check_scoreboard_events.py",
        "check_tb_python_compile.py",
        "ssot_coverage_summary.py",
        "dut_lint_report.py",
        "rtl_compile_report.py",
        "derive_rtl_todos.py",
    }
    assert set(UNCOVERED_GATES) == frozen, (
        "Gate self-test backlog changed — if you added coverage, move the gate to "
        "COVERED_GATES and update this frozen set deliberately."
    )
