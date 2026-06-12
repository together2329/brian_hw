"""Evidence for the content-keyed semantic-judge verdict cache.

Closes ``OBL_SEMANTIC_JUDGE_CACHED_DETERMINISTIC`` (campaign finding 29): the
FL/CL semantic gates ran the LLM judge on EVERY validation pass even when the
judged inputs were unchanged, with nondeterministic same-input verdicts. The
cache turns determinism into a structural property and eliminates redundant LLM
calls.

These tests pin:
  * first pass invokes the (stubbed) judge N times; an identical second pass
    invokes it 0 times and verdicts carry ``cache_hit=True``;
  * mutating one transaction's judged content re-judges ONLY the affected
    contract (the other contract is still served from cache);
  * ``ATLAS_JUDGE_CACHE=0`` disables the cache (judge invoked every time);
  * a stored verdict is reused verbatim even if the stub would now answer
    differently (determinism pin);
  * a corrupt cache file is treated as a miss and never crashes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workflow" / "fl-model-gen" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_fl_semantics import validate_fl_semantics  # noqa: E402
from validate_cl_semantics import validate_cl_semantics  # noqa: E402


# --------------------------------------------------------------------------- #
# Stub provider — counts calls, returns a faithful verdict per contract
# --------------------------------------------------------------------------- #
class _StubProvider:
    """Records every ``complete`` call and returns a ``faithful`` JSON verdict.

    ``per_contract_calls`` maps the per-contract id (from the call context) to a
    hit count so a test can assert which contracts were (re-)judged.
    """

    def __init__(self, faithful: bool = True) -> None:
        self.faithful = faithful
        self.calls: list[dict[str, Any]] = []
        self.per_contract_calls: dict[str, int] = {}

    def complete(self, *, stage, model, system_prompt, prompt, context, output_schema=None):
        cid = str(context.get("contract"))
        self.calls.append({"stage": stage, "model": model, "contract": cid})
        self.per_contract_calls[cid] = self.per_contract_calls.get(cid, 0) + 1
        raw = json.dumps({"faithful": self.faithful, "violations": []})
        return type("R", (), {"raw_response": raw, "status": "", "error": ""})()


# --------------------------------------------------------------------------- #
# Fixtures: minimal non-waived (sequential) IP so the deterministic backstop
# passes and the LLM judge actually runs over the contracts.
# --------------------------------------------------------------------------- #
def _write_fl_ip(root: Path, ip: str, transactions: list[dict], contracts: list[dict]) -> None:
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "req").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)

    ssot = {"ip": ip, "top_module": {"name": ip},
            "function_model": {"transactions": transactions}}
    import yaml
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        yaml.safe_dump(ssot, sort_keys=False), encoding="utf-8")

    obligation_ids = []
    for c in contracts:
        obligation_ids.extend(c.get("obligations", []))
    (ip_dir / "req" / "behavioral_contracts.json").write_text(
        json.dumps({"ip": ip, "schema_version": 1, "type": "behavioral_contracts",
                    "contracts": contracts}, indent=2), encoding="utf-8")
    (ip_dir / "req" / "obligations.json").write_text(
        json.dumps({"ip": ip, "obligations": [{"obligation_id": o} for o in obligation_ids]}),
        encoding="utf-8")


def _seq_contract(cid: str, obl: str) -> dict:
    """A sequential (non-waived) contract so the deterministic backstop is silent."""
    return {
        "id": cid,
        "decision_table": [{"when": "en==1 at rising clk", "then": "count += 1 next cycle"}],
        "obligations": [obl],
        "stage_contracts": [
            {"stage": "rtl", "check": "RTL realizes step",
             "pass_condition": "rtl_compile PASS", "validator": "rtl_compile_report.py"},
            {"stage": "tb", "check": "scoreboard matches decision table",
             "pass_condition": "scoreboard PASS", "validator": "check_scoreboard_events.py"},
        ],
    }


def _txn(name: str, cid: str, rule: str = "out = f(in)") -> dict:
    return {"id": name, "name": name, "contract_refs": [cid], "output_rules": [rule]}


@pytest.fixture(autouse=True)
def _enable_cache(monkeypatch):
    """Default the cache ON for every test (some tests override to 0)."""
    monkeypatch.setenv("ATLAS_JUDGE_CACHE", "1")


# --------------------------------------------------------------------------- #
# Test 1 — first pass judges N times, identical second pass judges 0 times
# --------------------------------------------------------------------------- #
def test_second_identical_pass_is_all_cache_hits(tmp_path: Path) -> None:
    _write_fl_ip(
        tmp_path, "cache_fl",
        transactions=[_txn("op_a", "BC-A"), _txn("op_b", "BC-B")],
        contracts=[_seq_contract("BC-A", "OBL_A"), _seq_contract("BC-B", "OBL_B")],
    )
    stub = _StubProvider()
    first = validate_fl_semantics("cache_fl", tmp_path, llm_provider=stub, model="stub-model")
    assert first["llm_judge"]["status"] == "pass"
    assert len(stub.calls) == 2  # one LLM call per contract
    assert all(not pc.get("cache_hit") for pc in first["llm_judge"]["per_contract"])

    # Identical second pass: zero new LLM calls, every verdict served from cache.
    second = validate_fl_semantics("cache_fl", tmp_path, llm_provider=stub, model="stub-model")
    assert len(stub.calls) == 2  # unchanged — no new calls
    assert second["llm_judge"]["status"] == "pass"
    assert len(second["llm_judge"]["per_contract"]) == 2
    assert all(pc.get("cache_hit") is True for pc in second["llm_judge"]["per_contract"])


# --------------------------------------------------------------------------- #
# Test 2 — mutating one transaction re-judges ONLY the affected contract
# --------------------------------------------------------------------------- #
def test_mutating_one_contract_only_rejudges_that_contract(tmp_path: Path) -> None:
    _write_fl_ip(
        tmp_path, "cache_fl2",
        transactions=[_txn("op_a", "BC-A"), _txn("op_b", "BC-B")],
        contracts=[_seq_contract("BC-A", "OBL_A"), _seq_contract("BC-B", "OBL_B")],
    )
    stub = _StubProvider()
    validate_fl_semantics("cache_fl2", tmp_path, llm_provider=stub, model="stub-model")
    assert stub.per_contract_calls == {"BC-A": 1, "BC-B": 1}

    # Mutate only op_b's judged content (output rule) in place and re-run.
    import yaml
    ssot_path = tmp_path / "cache_fl2" / "yaml" / "cache_fl2.ssot.yaml"
    ssot = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    for tx in ssot["function_model"]["transactions"]:
        if tx["name"] == "op_b":
            tx["output_rules"] = ["out = g(in) + 1"]  # content change → new key for BC-B only
    ssot_path.write_text(yaml.safe_dump(ssot, sort_keys=False), encoding="utf-8")

    stub2 = _StubProvider()
    report = validate_fl_semantics("cache_fl2", tmp_path, llm_provider=stub2, model="stub-model")
    # BC-A unchanged → cache hit (0 calls); BC-B changed → re-judged (1 call).
    assert stub2.per_contract_calls == {"BC-B": 1}
    pc = {p["contract_id"]: p for p in report["llm_judge"]["per_contract"]}
    assert pc["BC-A"].get("cache_hit") is True
    assert pc["BC-B"].get("cache_hit") is not True


# --------------------------------------------------------------------------- #
# Test 3 — ATLAS_JUDGE_CACHE=0 disables the cache (judge invoked every time)
# --------------------------------------------------------------------------- #
def test_cache_disabled_judges_every_time(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_JUDGE_CACHE", "0")
    _write_fl_ip(
        tmp_path, "cache_fl3",
        transactions=[_txn("op_a", "BC-A")],
        contracts=[_seq_contract("BC-A", "OBL_A")],
    )
    stub = _StubProvider()
    validate_fl_semantics("cache_fl3", tmp_path, llm_provider=stub, model="stub-model")
    validate_fl_semantics("cache_fl3", tmp_path, llm_provider=stub, model="stub-model")
    assert len(stub.calls) == 2  # judged both passes — cache bypassed
    # No cache directory was written.
    assert not (tmp_path / "cache_fl3" / "model" / ".judge_cache").exists()


# --------------------------------------------------------------------------- #
# Test 4 — determinism pin: stored verdict reused verbatim even if the stub
# would now answer differently.
# --------------------------------------------------------------------------- #
def test_stored_verdict_is_pinned_against_stub_flip(tmp_path: Path) -> None:
    _write_fl_ip(
        tmp_path, "cache_fl4",
        transactions=[_txn("op_a", "BC-A")],
        contracts=[_seq_contract("BC-A", "OBL_A")],
    )
    faithful_stub = _StubProvider(faithful=True)
    first = validate_fl_semantics("cache_fl4", tmp_path, llm_provider=faithful_stub, model="stub-model")
    assert first["llm_judge"]["per_contract"][0]["faithful"] is True

    # A second provider that would now flip to unfaithful must NEVER be consulted:
    # the content is unchanged, so the pinned PASS verdict is reused verbatim.
    flip_stub = _StubProvider(faithful=False)
    second = validate_fl_semantics("cache_fl4", tmp_path, llm_provider=flip_stub, model="stub-model")
    assert len(flip_stub.calls) == 0  # the flipping stub is never called
    assert second["llm_judge"]["per_contract"][0]["faithful"] is True  # pinned, not flipped
    assert second["llm_judge"]["per_contract"][0]["cache_hit"] is True


# --------------------------------------------------------------------------- #
# Test 5 — a corrupt cache file is treated as a miss and never crashes
# --------------------------------------------------------------------------- #
def test_corrupt_cache_file_is_a_miss(tmp_path: Path) -> None:
    _write_fl_ip(
        tmp_path, "cache_fl5",
        transactions=[_txn("op_a", "BC-A")],
        contracts=[_seq_contract("BC-A", "OBL_A")],
    )
    stub = _StubProvider()
    validate_fl_semantics("cache_fl5", tmp_path, llm_provider=stub, model="stub-model")
    assert len(stub.calls) == 1

    # Corrupt every cache file on disk.
    cache_dir = tmp_path / "cache_fl5" / "model" / ".judge_cache"
    files = list(cache_dir.glob("*.json"))
    assert files, "expected the first pass to have written a cache file"
    for f in files:
        f.write_text("{ this is not valid json ", encoding="utf-8")

    stub2 = _StubProvider()
    report = validate_fl_semantics("cache_fl5", tmp_path, llm_provider=stub2, model="stub-model")
    # Corrupt file => miss => the judge runs again (no crash) and re-stores.
    assert len(stub2.calls) == 1
    assert report["llm_judge"]["status"] == "pass"
    # The re-store overwrote the corrupt file with a valid record.
    record = json.loads(next(cache_dir.glob("*.json")).read_text(encoding="utf-8"))
    assert record["key"] and isinstance(record["verdict"], dict)


# --------------------------------------------------------------------------- #
# Test 6 — the cache also covers the CL judge (parallel structure)
# --------------------------------------------------------------------------- #
def _write_cl_ip(root: Path, ip: str) -> None:
    """A non-waived (sequential) IP with a real cycle_model so the CL judge runs."""
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "req").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    ssot = {
        "ip": ip, "top_module": {"name": ip},
        "function_model": {"transactions": [_txn("op_a", "BC-A")]},
        "cycle_model": {"executable": "python",
                        "latency": {"op_a": {"min_cycles": 2, "max_cycles": 4}}},
    }
    import yaml
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        yaml.safe_dump(ssot, sort_keys=False), encoding="utf-8")
    (ip_dir / "req" / "behavioral_contracts.json").write_text(
        json.dumps({"ip": ip, "schema_version": 1, "type": "behavioral_contracts",
                    "contracts": [_seq_contract("BC-A", "OBL_A")]}, indent=2), encoding="utf-8")
    (ip_dir / "req" / "obligations.json").write_text(
        json.dumps({"ip": ip, "obligations": [{"obligation_id": "OBL_A"}]}), encoding="utf-8")


def test_cl_judge_second_pass_is_cache_hit(tmp_path: Path) -> None:
    _write_cl_ip(tmp_path, "cache_cl")
    stub = _StubProvider()
    first = validate_cl_semantics("cache_cl", tmp_path, llm_provider=stub, model="stub-model")
    assert first["llm_judge"]["status"] == "pass"
    assert len(stub.calls) == 1

    second = validate_cl_semantics("cache_cl", tmp_path, llm_provider=stub, model="stub-model")
    assert len(stub.calls) == 1  # no new LLM call
    assert second["llm_judge"]["per_contract"][0]["cache_hit"] is True
    # FL and CL keep separate cache namespaces (domain prefix).
    cache_dir = tmp_path / "cache_cl" / "model" / ".judge_cache"
    assert all(p.name.startswith("cl-") for p in cache_dir.glob("*.json"))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
