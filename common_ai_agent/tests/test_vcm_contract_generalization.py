"""GEN-A: generic regression suite locking the VCM (Verification Contract Model)
content-equivalence generalization.

These six cases assert on the MECHANISM — gate names, statuses, condition kinds,
and the contract-check / sim-freshness / signoff primitives — NOT on MCTP/payload
strings, so the rule is proven to be a reusable workflow primitive rather than
something hard-wired to mctp_assembler_v3.

  1. content pass            : a contract IP with a granularity:content obligation
                               whose digest row matches -> contract-check PASS,
                               that obligation status=pass.
  2. content corruption fail : mutate the observed digest -> contract-check fails,
                               the obligation fails on the equality condition.
  3. input change -> stale   : touch an RTL/SSOT/TB input after a sim-stage stamp ->
                               sim_freshness_issues reports stale (then restored).
  4. no content obligation   : evidence_contract.json with only COUNT obligations ->
                               check_ip_signoff contract_content_coverage = fail.
  5. legacy IP, no closure   : a synthetic minimal IP with NO semantic_contracts.json,
                               contract-check WITHOUT --require-contract-closure ->
                               not blocked; contract_content_coverage = pass (n/a).
  6. strict closure, no src  : same legacy IP WITH --require-contract-closure -> BLOCKED.

ALL six cases run on SYNTHETIC IPs built under pytest's tmp_path — including the
destructive cases 2 (digest corruption) and 3 (input change) — so the suite is
fully self-contained and NEVER mutates the live mctp_assembler_v3 tree. An autouse
guard fixture fingerprints the real mctp_v3 files before/after each test and fails
if any case touches them, so the no-touch guarantee is enforced.

Run: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_vcm_contract_generalization.py
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from .contract_reflection_helpers import (
    CONTRACT_CHECK_SCRIPT,
    REPO,
    JsonMap,
    JsonValue,
    make_contract_ip,
    read_json,
    write_json,
    write_rows,
)
from .sim_freshness_helpers import make_reflected_ip, run_stamp
from .test_semantic_contract_required_closure import _write_legacy_reflection, _write_stage_artifacts

SIGNOFF_SCRIPT = REPO / "workflow" / "signoff" / "scripts" / "check_ip_signoff.py"
SIM_FRESHNESS_MOD = REPO / "workflow" / "contract_reflection" / "sim_freshness.py"

# The two VCM gate names this suite locks (coordinated with GEN-B). Only
# contract_content_coverage is asserted here; contract_sim_freshness is GEN-B's
# signoff gate, so case 3 exercises its underlying primitive (sim_freshness_issues)
# directly AND (now that GEN-B's gate has landed) asserts on the gate by name.
CONTENT_GATE = "contract_content_coverage"
SIM_FRESHNESS_GATE = "contract_sim_freshness"
DIGEST = "9f" * 32  # opaque non-MCTP content fingerprint used by cases 1/2

# Every case runs on a SYNTHETIC IP under pytest's tmp_path; nothing here may
# touch the real mctp_assembler_v3 tree. This autouse guard snapshots the live
# mctp_v3 files the freshness/contract gates fingerprint and FAILS the test if a
# case mutates any of them — so the suite can never leave mctp_v3 dirty/stale and
# the no-touch guarantee is enforced, not just intended.
_MCTP_V3 = REPO / "mctp_assembler_v3"
_MCTP_V3_GUARDED = (
    "sim/scoreboard_events.jsonl",
    "sim/evidence_freshness.json",
    "verify/semantic_contracts.json",
    "verify/evidence_contract.json",
    "yaml/mctp_assembler_v3.ssot.yaml",
    "rtl/mctp_assembler_v3.sv",
)


def _mctp_v3_snapshot() -> dict[str, str | None]:
    snap: dict[str, str | None] = {}
    for rel in _MCTP_V3_GUARDED:
        path = _MCTP_V3 / rel
        snap[rel] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return snap


@pytest.fixture(autouse=True)
def _mctp_v3_must_stay_untouched():
    before = _mctp_v3_snapshot()
    yield
    after = _mctp_v3_snapshot()
    changed = [rel for rel in before if before[rel] != after[rel]]
    assert not changed, (
        "GEN-A must never mutate the live mctp_assembler_v3 tree; these files "
        f"changed during the test: {changed}"
    )


# ---------------------------------------------------------------------------
# Programmatic access to the workflow primitives (no CLI parsing of strings).
# ---------------------------------------------------------------------------
def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _content_coverage_gate(ip: str, root: Path):
    """Run ONLY the contract_content_coverage gate and return its recorded Gate."""
    module = _load_module("check_ip_signoff_vcm_gen", SIGNOFF_SCRIPT)
    checker = module.SignoffChecker(ip, root, require_human_waiver_approval=False)
    checker.check_contract_content_coverage()
    gates = [g for g in checker.gates if g.name == CONTENT_GATE]
    assert len(gates) == 1, f"expected exactly one {CONTENT_GATE} gate, got {checker.gates}"
    return gates[0]


def _sim_freshness_gate(ip: str, root: Path, *, require_sim_freshness: bool = False):
    """Run ONLY the contract_sim_freshness gate (GEN-B) and return its Gate.

    Returns None if the running check_ip_signoff predates GEN-B (no such gate),
    so GEN-A stays robust whether or not GEN-B has landed in the tree under test.
    """
    module = _load_module("check_ip_signoff_vcm_gen", SIGNOFF_SCRIPT)
    checker = module.SignoffChecker(
        ip, root, require_human_waiver_approval=False, require_sim_freshness=require_sim_freshness
    )
    check = getattr(checker, "check_contract_sim_freshness", None)
    if check is None:
        return None
    check()
    gates = [g for g in checker.gates if g.name == SIM_FRESHNESS_GATE]
    assert len(gates) == 1, f"expected exactly one {SIM_FRESHNESS_GATE} gate, got {checker.gates}"
    return gates[0]


def _sim_freshness_issues(ip_dir: Path) -> list[str]:
    module = _load_module("sim_freshness_vcm_gen", SIM_FRESHNESS_MOD)
    return module.sim_freshness_issues(ip_dir)


def _run_contract_check(root: Path, ip: str = "contract_ip", *, require_contract_closure: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = ["python3", str(CONTRACT_CHECK_SCRIPT), ip, "--root", str(root)]
    if require_contract_closure:
        cmd.append("--require-contract-closure")
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def _coverage_report(ip_dir: Path) -> JsonMap:
    return read_json(ip_dir / "signoff" / "evidence_contract_coverage.json")


def _obligation_result(ip_dir: Path, obligation_id: str) -> JsonMap:
    for item in _coverage_report(ip_dir).get("obligations", []):  # type: ignore[union-attr]
        if isinstance(item, dict) and item.get("obligation_id") == obligation_id:
            return item
    raise AssertionError(f"obligation {obligation_id} absent from evidence_contract_coverage.json")


# ---------------------------------------------------------------------------
# Fixtures.
# ---------------------------------------------------------------------------
def _content_obligation(observed_digest: str, expected_digest: str) -> JsonMap:
    """A granularity:content obligation + its scoreboard row (digest equality).

    Mechanism-only: 'content_digest' is a generic field name, not MCTP-specific.
    """
    return {
        "obligation": {
            "contract_refs": ["SEMANTIC_STATE_CONTENT"],
            "evidence_rows": [
                {"artifact": "sim/scoreboard_events.jsonl", "match": {"scenario_id": "SC_CONTENT"}}
            ],
            "granularity": "content",
            "obligation_id": "OBL_CONTENT_001",
            "pass_conditions": [
                {"id": "row_passed", "kind": "row_passed_with_fl_expected"},
                {
                    "id": "content_digest_matches_fl",
                    "kind": "observed_equals_fl_expected",
                    "field": "content_digest",
                    "expected_path": "fl_expected.model_result.state_updates.content_digest",
                },
            ],
            "required": True,
            "required_observables": ["content_digest"],
            "scenario_ids": ["SC_CONTENT"],
        },
        "row": {
            "goal_id": "EQ_CONTENT",
            "scenario_id": "SC_CONTENT",
            "passed": True,
            "mismatch": "",
            "fl_expected": {"model_api": "X.apply", "model_result": {"state_updates": {"content_digest": expected_digest}}},
            "rtl_observed": {"content_digest": observed_digest},
        },
    }


def _make_content_ip(root: Path, observed_digest: str = DIGEST, expected_digest: str = DIGEST) -> Path:
    """Synthetic contract IP that carries a granularity:content obligation."""
    ip_dir = make_contract_ip(root)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    parts = _content_obligation(observed_digest, expected_digest)
    semantic: JsonMap = {
        "contract_refs": [
            {
                "contract_ref": "SEMANTIC_STATE_CONTENT",
                "fl": {"path": "model/functional_model.py"},
                "cl": {"path": "model/cycle_model.py"},
                # observable_via must be a signal the reflection stage can sample
                # in the wave; the content equality itself is checked in the
                # evidence stage against the scoreboard row's content_digest.
                "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["payload_byte_count"]},
                "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
                "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
                "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "content_monitor"},
            }
        ],
        "requirements": [
            {
                "claim": "Content equivalence (byte digest) is required, not just count.",
                "obligations": [parts["obligation"]],
                "required": True,
                "requirement_id": "REQ_CONTENT",
                "source_refs": ["yaml/contract_ip.ssot.yaml"],
            }
        ],
        "schema_version": 1,
        "type": "semantic_contracts",
    }
    write_json(ip_dir / "verify" / "semantic_contracts.json", semantic)
    # Carry BOTH the default count row (from make_contract_ip) and the content row.
    existing = ip_dir / "sim" / "scoreboard_events.jsonl"
    count_rows = [
        {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD", "passed": True,
         "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF}},
    ]
    write_rows(existing, [*count_rows, parts["row"]])
    return ip_dir


def _make_legacy_generated_ip(root: Path) -> Path:
    """A SYNTHETIC non-MCTP 'legacy' IP that carries the GENERATED contract
    artifacts (requirements_index + evidence_contract + contract_reflection +
    scoreboard) — i.e. a real workable contract IP — but has NOT been migrated to
    semantic closure: NO verify/semantic_contracts.json. This is the posture for
    'run_contract_check WITHOUT closure -> not blocked' (5b) and 'WITH closure ->
    blocked' (6). Built on the shared synthetic contract_ip fixture (not mctp_v3)."""
    ip_dir = make_contract_ip(root)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    assert not (ip_dir / "verify" / "semantic_contracts.json").exists()
    assert (ip_dir / "verify" / "evidence_contract.json").exists()
    return ip_dir


# ---------------------------------------------------------------------------
# Case 1: content obligation closes green.
# ---------------------------------------------------------------------------
def test_case1_content_obligation_passes(tmp_path: Path) -> None:
    ip_dir = _make_content_ip(tmp_path)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 0, result.stdout
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] == "pass", report["status"]
    obl = _obligation_result(ip_dir, "OBL_CONTENT_001")
    assert obl["status"] == "pass", obl
    conditions = obl["condition_results"]
    assert isinstance(conditions, dict)
    assert conditions["content_digest_matches_fl"] is True
    assert conditions["row_passed"] is True


# ---------------------------------------------------------------------------
# Case 2: corrupt the observed content -> the equality condition fails.
# ---------------------------------------------------------------------------
def test_case2_content_corruption_fails_on_equality(tmp_path: Path) -> None:
    ip_dir = _make_content_ip(tmp_path, observed_digest="00" * 32, expected_digest=DIGEST)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode != 0, "corrupted content must not pass contract-check"
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] in {"fail", "blocked"}, report["status"]
    obl = _obligation_result(ip_dir, "OBL_CONTENT_001")
    assert obl["status"] == "fail", obl
    conditions = obl["condition_results"]
    assert isinstance(conditions, dict)
    # The equality condition is the one that fails; the row still "passed".
    assert conditions["content_digest_matches_fl"] is False
    assert any("content_digest_matches_fl" in str(i) for i in obl["issues"]), obl["issues"]  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Case 3: input change after a sim-stage stamp -> sim freshness reports stale.
# ---------------------------------------------------------------------------
def test_case3_input_change_after_stamp_is_stale(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    # Fresh immediately after the stamp.
    assert _sim_freshness_issues(ip_dir) == [], "freshly stamped evidence must be clean"

    rtl_input = ip_dir / "rtl" / "contract_ip.sv"
    original = rtl_input.read_text(encoding="utf-8")
    _ = rtl_input.write_text("// changed after sim evidence stamp\n", encoding="utf-8")

    issues = _sim_freshness_issues(ip_dir)
    assert issues, "changing an RTL input after the stamp must make evidence stale"
    assert any("rtl/contract_ip.sv" in str(i) for i in issues), issues

    # And the GEN-B signoff gate (contract_sim_freshness) reports the same stale
    # verdict by name. require_sim_freshness=True forces the "always required"
    # path, so the input/stamp mismatch -> fail (not "not applicable").
    gate = _sim_freshness_gate("contract_ip", tmp_path, require_sim_freshness=True)
    if gate is not None:  # GEN-B landed
        assert gate.status == "fail", gate
        assert any("rtl/contract_ip.sv" in i for i in gate.issues), gate.issues

    # Restore the input as instructed.
    _ = rtl_input.write_text(original, encoding="utf-8")
    # NOTE: content restored; a re-stamp would be needed to re-clean (mtime moved).


# ---------------------------------------------------------------------------
# Case 4: an IP that OPTED INTO the semantic contract layer but whose obligations
# are all COUNT (no granularity:content) fails the content-coverage gate.
#
# The gate keys applicability off verify/semantic_contracts.json (the VCM opt-in),
# NOT evidence_contract.json — so a count-only contract that has migrated to the
# semantic layer must still prove a content obligation or it fails.
# ---------------------------------------------------------------------------
def test_case4_no_content_obligation_fails_signoff_gate(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    # Opt into the semantic layer with a COUNT-only obligation (no granularity).
    write_json(
        ip_dir / "verify" / "semantic_contracts.json",
        {
            "contract_refs": [
                {
                    "contract_ref": "SEMANTIC_STATE_COUNT",
                    "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
                }
            ],
            "requirements": [
                {
                    "claim": "Payload byte count is tracked (count-only, no content axis).",
                    "obligations": [
                        {
                            "contract_refs": ["SEMANTIC_STATE_COUNT"],
                            "evidence_rows": [
                                {"artifact": "sim/scoreboard_events.jsonl", "match": {"scenario_id": "SC_PAYLOAD"}}
                            ],
                            "obligation_id": "OBL_SEMANTIC_COUNT",
                            "pass_conditions": [
                                {"field": "payload_byte_count", "id": "count_is_17", "kind": "observed_equals", "value": 17}
                            ],
                            "required": True,
                            "required_observables": ["payload_byte_count"],
                            "scenario_ids": ["SC_PAYLOAD"],
                        }
                    ],
                    "required": True,
                    "requirement_id": "REQ_SEMANTIC_COUNT",
                    "source_refs": ["yaml/contract_ip.ssot.yaml"],
                }
            ],
            "schema_version": 1,
            "type": "semantic_contracts",
        },
    )
    # Make the coverage report 'pass' so the failure is SPECIFICALLY the missing
    # content obligation, not a stale/failed contract-check.
    write_json(
        ip_dir / "signoff" / "evidence_contract_coverage.json",
        {"obligations": [], "schema_version": 1, "status": "pass", "summary": {"failed": 0, "passed": 1, "total": 1}, "type": "evidence_contract_coverage"},
    )
    gate = _content_coverage_gate("contract_ip", tmp_path)
    assert gate.status == "fail", gate
    assert any("granularity:content" in i for i in gate.issues), gate.issues


# ---------------------------------------------------------------------------
# Case 5: legacy IP (no semantic_contracts.json), no closure flag -> skip/pass.
#
# A single legacy fixture now satisfies BOTH sub-claims of the task's case 5,
# because the gates key applicability off the VCM opt-in signal
# (verify/semantic_contracts.json), not evidence_contract.json:
#   - run_contract_check WITHOUT --require-contract-closure -> not blocked (skip);
#   - contract_content_coverage -> pass (no semantic contract layer => n/a);
#   - contract_sim_freshness    -> pass (no sim-owned obligation, no flag => n/a).
# (An earlier gate revision keyed the content gate off evidence_contract.json,
#  which over-reached on legacy goal-overlay IPs; that was fixed to key off the
#  semantic layer, so the two sub-claims are now consistent for one IP.)
# ---------------------------------------------------------------------------
def test_case5_legacy_ip_without_closure_flag_skips(tmp_path: Path) -> None:
    ip_dir = _make_legacy_generated_ip(tmp_path)

    result = _run_contract_check(tmp_path, require_contract_closure=False)

    assert result.returncode == 0, result.stdout
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] != "blocked", report["status"]
    assert "skipped: verify/semantic_contracts.json not present" in str(report["runs"])

    # Both VCM signoff gates are NOT applicable for this legacy IP (no semantic
    # contract layer, no sim-owned obligation, no --require-sim-freshness).
    content_gate = _content_coverage_gate("contract_ip", tmp_path)
    assert content_gate.status == "pass", content_gate
    assert "not applicable" in "; ".join([content_gate.summary, *content_gate.issues])

    sim_gate = _sim_freshness_gate("contract_ip", tmp_path, require_sim_freshness=False)
    if sim_gate is not None:  # GEN-B landed
        assert sim_gate.status == "pass", sim_gate
        assert "not applicable" in "; ".join([sim_gate.summary, *sim_gate.issues])


# ---------------------------------------------------------------------------
# Case 6: same legacy generated IP WITH strict closure -> blocked.
# ---------------------------------------------------------------------------
def test_case6_legacy_ip_with_strict_closure_blocked(tmp_path: Path) -> None:
    ip_dir = _make_legacy_generated_ip(tmp_path)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 1, result.stdout
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] in {"fail", "blocked"}, report["status"]
    assert "required: missing verify/semantic_contracts.json" in str(report["runs"])
