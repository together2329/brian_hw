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
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_atlas_to_ssot_locked_truth import _write_locked_contract_bundle
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
from tests.test_workflow_stage_engine import _clear_obligation_authority_refs

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
# req contract-authority gate self-test (check_contract_bundle.py)
# ---------------------------------------------------------------------------

_REQ_IP = "gate_req"
_REQ_GATE = REPO / "workflow" / "req-gen" / "scripts" / "check_contract_bundle.py"


def _req_build_good(work: Path) -> dict:
    # Writes + locks a full valid contract bundle under work/<ip>/req/.
    _write_locked_contract_bundle(work, _REQ_IP)
    return {"ip": _REQ_IP}


def _req_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_REQ_GATE), ctx["ip"], "--root", str(work)],
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode
    ctx["out"] = proc.stdout + proc.stderr


def _req_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _req_mut_anchor_only(work: Path, ctx: dict) -> None:
    # Content authority: obligation with no structural/behavioral contract refs
    # (manifest hash refreshed so it fails on the anchor-ref check, not the hash).
    _clear_obligation_authority_refs(work / ctx["ip"] / "req")


def _req_mut_tamper_without_rehash(work: Path, ctx: dict) -> None:
    # Lock integrity: edit a hashed req-graph file but do NOT refresh the manifest
    # hash — the gate must reject the tampered locked bundle.
    obl_path = work / ctx["ip"] / "req" / "obligations.json"
    obl = json.loads(obl_path.read_text(encoding="utf-8"))
    obl["_tamper"] = "edited after lock; manifest hash intentionally not refreshed"
    obl_path.write_text(json.dumps(obl, indent=2, sort_keys=True) + "\n", encoding="utf-8")


REQ_CONTRACT_AUTHORITY_SELF_TEST = GateSelfTest(
    build_good=_req_build_good,
    run_gate=_req_run_gate,
    read_status=_req_read_status,
    mutations=[
        ("anchor_only_obligation", _req_mut_anchor_only),
        ("tamper_without_rehash", _req_mut_tamper_without_rehash),
    ],
)


# ---------------------------------------------------------------------------
# scoreboard schema/observable gate self-test (check_scoreboard_events.py)
# ---------------------------------------------------------------------------

_SB_IP = "gate_sb"
_SB_GATE = REPO / "workflow" / "tb-gen" / "scripts" / "check_scoreboard_events.py"

_SB_GOOD_ROW = {
    "goal_id": "EQ_DATA",
    "scenario_id": "SC_DATA",
    "cycle": 1,
    "stimulus": {"kind": "READ"},
    "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"data_o": 3}},
    "rtl_observed": {"data_o": 3},
    "passed": True,
    "mismatch": "",
    "coverage_refs": ["SC_DATA_executed"],
}


def _sb_write_events(ip_dir: Path, rows: list) -> None:
    path = ip_dir / "sim" / "scoreboard_events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def _sb_build_good(work: Path) -> dict:
    ip_dir = work / _SB_IP
    (ip_dir / "verify").mkdir(parents=True, exist_ok=True)
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps({"goals": [{"goal_id": "EQ_DATA"}]}), encoding="utf-8"
    )
    _sb_write_events(ip_dir, [dict(_SB_GOOD_ROW)])
    sb = ip_dir / "tb" / "cocotb" / "scoreboard.py"
    sb.parent.mkdir(parents=True, exist_ok=True)
    sb.write_text(
        "from equivalence_scoreboard import EquivalenceScoreboard\nsb = EquivalenceScoreboard()\n",
        encoding="utf-8",
    )
    return {"ip": _SB_IP}


def _sb_run_gate(work: Path, ctx: dict) -> None:
    proc = subprocess.run(
        [sys.executable, str(_SB_GATE), ctx["ip"], "--root", str(work), "--source-check", "--require-events"],
        capture_output=True, text=True, check=False,
    )
    ctx["rc"] = proc.returncode
    ctx["out"] = proc.stdout + proc.stderr


def _sb_read_status(work: Path, ctx: dict) -> str:
    return "pass" if ctx.get("rc") == 0 else "fail"


def _sb_mut_empty_events(work: Path, ctx: dict) -> None:
    _sb_write_events(work / ctx["ip"], [])  # --require-events must reject 0 rows


def _sb_mut_vacuous_observed(work: Path, ctx: dict) -> None:
    row = dict(_SB_GOOD_ROW)
    row["rtl_observed"] = {}  # empty observed = no real DUT evidence
    _sb_write_events(work / ctx["ip"], [row])


def _sb_mut_observed_copies_fl(work: Path, ctx: dict) -> None:
    row = dict(_SB_GOOD_ROW)
    row["rtl_observed"] = dict(row["fl_expected"])  # FL-copy cheat (observed == expected)
    _sb_write_events(work / ctx["ip"], [row])


def _sb_mut_fl_not_from_model(work: Path, ctx: dict) -> None:
    row = dict(_SB_GOOD_ROW)
    row["fl_expected"] = {"model_result": {"data_o": 3}}  # missing model_api authenticity
    _sb_write_events(work / ctx["ip"], [row])


SCOREBOARD_EVENTS_SELF_TEST = GateSelfTest(
    build_good=_sb_build_good,
    run_gate=_sb_run_gate,
    read_status=_sb_read_status,
    mutations=[
        ("empty_events", _sb_mut_empty_events),
        ("vacuous_rtl_observed", _sb_mut_vacuous_observed),
        ("rtl_observed_copies_fl", _sb_mut_observed_copies_fl),
        ("fl_expected_not_from_model", _sb_mut_fl_not_from_model),
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
    # req contract-authority gate (manifest "contract_authority" entrypoint).
    "req_contract_authority": {
        "scripts": ("check_contract_bundle.py", "check_locked_truth_bundle.py"),
        "self_test": REQ_CONTRACT_AUTHORITY_SELF_TEST,
    },
    # scoreboard schema/observable gate (manifest "scoreboard_schema" stage).
    "scoreboard_events": {
        "scripts": ("check_scoreboard_events.py",),
        "self_test": SCOREBOARD_EVENTS_SELF_TEST,
    },
}

# Explicit, FROZEN backlog: acknowledged gates that still lack a direct
# mutation self-test. Shrinks only by a reviewed change (see module docstring).
UNCOVERED_GATES = {
    "check_ip_signoff.py": "final signoff aggregate gate",
    "check_truth_coverage.py": "locked-truth obligation coverage gate",
    "run_contract_check.py": "contract-reflection closure gate (incl. --require-contract-closure strict)",
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
        "check_ip_signoff.py",
        "check_truth_coverage.py",
        "run_contract_check.py",
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
