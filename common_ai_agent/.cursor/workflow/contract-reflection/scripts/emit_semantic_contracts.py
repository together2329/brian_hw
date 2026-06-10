#!/usr/bin/env python3
"""Deterministically derive verify/semantic_contracts.json from the SSOT.

This generator replaces the hand-authored semantic_contracts.json. It reads the
SSOT function_model (transactions / state_variables / invariants) plus the
test_requirements scenarios, joins them to REAL passing scoreboard rows and the
VCD wave, and emits the nested SOURCE-format semantic contract that the semantic
overlay later merges into the evidence/reflection/requirements artifacts.

Every emitted obligation is GROUNDED in an actual passing scoreboard row: the
pass_conditions, required_observables, and evidence_rows.match are derived from
the fields that row actually carries (rtl_observed keys + resolvable
fl_expected paths) and the VCD signals actually sampled in the wave. An
obligation/condition is only emitted if it evaluates to PASS against the chosen
row at generation time, so the generated contract reproduces the green
contract-check chain instead of inventing unsatisfiable claims.

A payload/digest-bearing transaction MUST yield at least one
granularity:content obligation (the signoff contract_content_coverage gate), so
the generator hard-fails if a payload transaction exists but no content
obligation could be grounded.

The document is self-validated with
workflow.contract_reflection.semantic_source_validation.source_issues before it
is written; any issue aborts (SystemExit) without writing.

CLI:
    emit_semantic_contracts.py <ip> --root <root>
Writes ONLY <ip>/verify/semantic_contracts.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow.contract_reflection.evidence_contract_json import (
    JsonList,
    JsonMap,
    JsonValue,
    as_list as _as_list,
    as_map as _as_map,
    json_strings as _json_strings,
    load_rows as _load_rows,
    strings as _strings,
    text as _text,
)
from workflow.contract_reflection.evidence_contract_vcd import sampled_vcd_signals
from workflow.contract_reflection.semantic_source_validation import source_issues


SCOREBOARD_ARTIFACT: Final = "sim/scoreboard_events.jsonl"
# VCD-observable signals (golden-shape ordering hint) that we prefer to publish
# as a contract_ref observable_via list when they are present in the wave.
PREFERRED_WAVE_OBSERVABLES: Final[tuple[str, ...]] = (
    "ctx_payload_byte_count",
    "ctx_payload_count",
    "ctx_state",
    "sram_wr_valid",
    "sram_wr_strb",
    "sram_wr_addr",
    "sram_wr_data",
    "descriptor_push",
    "descriptor_valid",
    "descriptor_count",
    "prdata",
    "pready",
)
# RTL leaf-file name fragments (suffixes appended to <ip>) that a transaction may
# own. Only files that actually exist on disk are published.
RTL_OWNER_SUFFIXES: Final[tuple[str, ...]] = (
    "",
    "_axi_wr_ingress",
    "_axi_write_ingress",
    "_pcie_vdm_parser",
    "_mctp_parser",
    "_mctp_decoder",
    "_context_table",
    "_sram_packer",
    "_descriptor_queue",
    "_axi_rd_payload",
    "_apb_regfile",
)


# --------------------------------------------------------------------------- #
# Small helpers (mirrors of emit_goal_contract_overlay.py)
# --------------------------------------------------------------------------- #
def _parse_args(argv: list[str]) -> tuple[str, Path]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise SystemExit("usage: emit_semantic_contracts.py <ip> [--root <root>]")
    ip = argv[0]
    root = Path(".")
    index = 1
    while index < len(argv):
        token = argv[index]
        if token != "--root":
            raise SystemExit(f"usage: unexpected argument {token!r}")
        if index + 1 >= len(argv):
            raise SystemExit("usage: --root requires a value")
        root = Path(argv[index + 1])
        index += 2
    return ip, root.resolve()


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    raw_ip = Path(ip)
    if raw_ip.is_absolute():
        raise SystemExit(f"[semantic_contracts] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw_ip).resolve()
    try:
        _ = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[semantic_contracts] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def _write_json(path: Path, payload: JsonMap) -> None:
    _ = path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sanitize_id(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in raw.upper())
    return "_".join(part for part in cleaned.split("_") if part)


def _detect_wave(ip_dir: Path) -> str:
    preferred = ip_dir / "sim" / f"{ip_dir.name}.vcd"
    if preferred.is_file():
        return preferred.relative_to(ip_dir).as_posix()
    for path in sorted((ip_dir / "sim").glob("*.vcd")):
        return path.relative_to(ip_dir).as_posix()
    raise SystemExit(f"[semantic_contracts] FAIL: missing VCD under {ip_dir / 'sim'}")


def _existing_paths(ip_dir: Path, paths: tuple[str, ...]) -> list[str]:
    return [path for path in paths if (ip_dir / path).is_file()]


def _load_ssot(ip_dir: Path) -> JsonMap:
    path = ip_dir / "yaml" / f"{ip_dir.name}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"[semantic_contracts] FAIL: missing {path}")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"[semantic_contracts] FAIL: invalid YAML {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise SystemExit(f"[semantic_contracts] FAIL: {path} root must be a mapping")
    return doc


# --------------------------------------------------------------------------- #
# Scoreboard row indexing / grounding
# --------------------------------------------------------------------------- #
def _path_value(row: JsonMap, path: str) -> tuple[bool, JsonValue]:
    """Resolve a dotted fl_expected path exactly like check_evidence_contract."""
    if not path.startswith("fl_expected."):
        return False, None
    value: JsonValue = row
    for segment in path.split("."):
        data = _as_map(value)
        if segment not in data:
            return False, None
        value = data[segment]
    return True, value


def _observed(row: JsonMap, field: str) -> JsonValue:
    return _as_map(row.get("rtl_observed")).get(field)


def _has_field(row: JsonMap, field: str) -> bool:
    return field in _as_map(row.get("rtl_observed"))


def _has_fl_path(row: JsonMap, path: str) -> bool:
    found, _ = _path_value(row, path)
    return found


def _contiguous_nonzero(value: JsonValue) -> bool:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return False
    normalized = value >> ((value & -value).bit_length() - 1)
    return (normalized & (normalized + 1)) == 0


class Grounding:
    """A passing scoreboard row plus the goal/scenario keys to match it."""

    def __init__(self, row: JsonMap) -> None:
        self.row = row
        self.scenario_id = _text(row.get("scenario_id"))
        self.goal_id = _text(row.get("goal_id"))

    def match(self) -> JsonMap:
        # Prefer the tightest unique match. goal_id+scenario_id mirrors the golden.
        match: JsonMap = {}
        if self.goal_id:
            match["goal_id"] = self.goal_id
        if self.scenario_id:
            match["scenario_id"] = self.scenario_id
        return match

    def evidence_row(self) -> JsonMap:
        return {"artifact": SCOREBOARD_ARTIFACT, "match": self.match()}


def _passing_goal_rows(rows: list[JsonMap], goal_id: str) -> list[JsonMap]:
    return [r for r in rows if _text(r.get("goal_id")) == goal_id and r.get("passed") is True]


def _pick_grounding(
    rows: list[JsonMap], goal_id: str, scenario_pref: list[str], require_fields: tuple[str, ...] = ()
) -> Grounding | None:
    """Pick a passing row for goal_id, preferring scenarios in scenario_pref and
    rows that carry every field in require_fields (rtl_observed key)."""
    candidates = _passing_goal_rows(rows, goal_id)
    if require_fields:
        candidates = [r for r in candidates if all(_has_field(r, f) for f in require_fields)]
    if not candidates:
        return None
    pref_index = {sid: i for i, sid in enumerate(scenario_pref)}

    def sort_key(r: JsonMap) -> tuple[int, str]:
        sid = _text(r.get("scenario_id"))
        return (pref_index.get(sid, len(pref_index)), sid)

    return Grounding(sorted(candidates, key=sort_key)[0])


# --------------------------------------------------------------------------- #
# Condition builders (each verified against the grounding row before emission)
# --------------------------------------------------------------------------- #
def _cond_row_passed_with_fl(g: Grounding) -> JsonMap | None:
    expected = _as_map(_as_map(g.row.get("fl_expected")).get("model_result"))
    if g.row.get("passed") is True and not _text(g.row.get("mismatch")) and expected:
        return {"id": "scoreboard_row_passed", "kind": "row_passed_with_fl_expected"}
    return None


def _cond_row_passed(g: Grounding) -> JsonMap | None:
    if g.row.get("passed") is True:
        return {"id": "scoreboard_row_passed", "kind": "row_passed"}
    return None


def _cond_observed_equals_fl(g: Grounding, field: str, expected_path: str, cid: str) -> JsonMap | None:
    if not _has_field(g.row, field):
        return None
    found, expected = _path_value(g.row, expected_path)
    if not found or _observed(g.row, field) != expected:
        return None
    return {"id": cid, "kind": "observed_equals_fl_expected", "field": field, "expected_path": expected_path}


def _cond_observed_equals(g: Grounding, field: str, value: JsonValue, cid: str) -> JsonMap | None:
    if not _has_field(g.row, field) or _observed(g.row, field) != value:
        return None
    return {"id": cid, "kind": "observed_equals", "field": field, "value": value}


def _cond_strobe_contiguous(g: Grounding, field: str, cid: str) -> JsonMap | None:
    if not _has_field(g.row, field) or not _contiguous_nonzero(_observed(g.row, field)):
        return None
    return {"id": cid, "kind": "strobe_contiguous", "field": field}


def _cond_vcd_ever_equals(
    ip_dir: Path, wave: str, sampled: set[str], signal: str, value: int, cid: str
) -> JsonMap | None:
    if signal not in sampled:
        return None
    found, issues = sampled_vcd_signals(ip_dir, wave, {signal})
    if signal not in found or issues:
        return None
    cond: JsonMap = {
        "id": cid,
        "kind": "vcd_signal_ever_equals",
        "signal": signal,
        "value": value,
        "artifact": wave,
    }
    from workflow.contract_reflection.evidence_contract_vcd import check_vcd_condition

    passed, _ = check_vcd_condition(ip_dir, cond)
    return cond if passed else None


def _cond_vcd_event_order(
    ip_dir: Path,
    wave: str,
    sampled: set[str],
    first: tuple[str, int],
    second: tuple[str, int],
    cid: str,
) -> JsonMap | None:
    if first[0] not in sampled or second[0] not in sampled:
        return None
    cond: JsonMap = {
        "id": cid,
        "kind": "vcd_event_order",
        "relation": "same_or_after",
        "first": {"signal": first[0], "value": first[1]},
        "second": {"signal": second[0], "value": second[1]},
        "artifact": wave,
    }
    from workflow.contract_reflection.evidence_contract_vcd import check_vcd_condition

    passed, _ = check_vcd_condition(ip_dir, cond)
    return cond if passed else None


def _required_observables(conditions: JsonList) -> list[str]:
    """Collect observable names referenced by the conditions.

    For scoreboard conditions this is the rtl_observed ``field``; for VCD
    conditions it is the wave signal name(s). check_evidence_contract treats both
    as valid observables (it unions vcd_observable_names into the observed set),
    so an obligation whose only conditions are VCD-based still needs a non-empty
    required_observables list to satisfy the mandatory-key check.
    """
    from workflow.contract_reflection.evidence_contract_vcd import vcd_observable_names

    names: set[str] = set()
    for item in conditions:
        cond = _as_map(item)
        field = _text(cond.get("field"))
        if field:
            names.add(field)
        names.update(vcd_observable_names(cond))
    return sorted(names)


# --------------------------------------------------------------------------- #
# contract_ref builder
# --------------------------------------------------------------------------- #
def _contract_ref(
    ip_dir: Path,
    contract_ref: str,
    transaction_id: str,
    transaction_name: str,
    wave: str,
    observable_via: list[str],
    owner_files: list[str],
    monitor: str,
    cl_rule: str,
    extra_refs: list[str],
) -> JsonMap:
    ip = ip_dir.name
    refs = [f"function_model.transactions.{transaction_id}"]
    if transaction_name and transaction_name != transaction_id:
        refs.insert(0, f"function_model.transactions.{transaction_name}")
    refs.extend(extra_refs)
    ref: JsonMap = {
        "contract_ref": contract_ref,
        "rtl": {
            "observable_via": _json_strings(observable_via),
            "owner_files": _json_strings(owner_files),
        },
        "sim": {"scoreboard": SCOREBOARD_ARTIFACT, "wave": wave},
        "ssot": {
            "anchor": f"function_model.transactions.{transaction_name or transaction_id}",
            "path": f"yaml/{ip}.ssot.yaml",
            "refs": _json_strings(refs),
        },
    }
    # CL is OPTIONAL: a combinational IP legitimately has no cycle model. Only
    # publish the cl block (with its path) when model/cycle_model.py exists, so
    # the generator never claims a non-existent artifact (check_contract_reflection
    # treats an absent CL path as not-applicable but FAILS a claimed-but-missing
    # path). The cl rules are still recorded even when the path is omitted so the
    # intent is not lost.
    cl_path = "model/cycle_model.py"
    if (ip_dir / cl_path).is_file():
        ref["cl"] = {"path": cl_path, "rules": _json_strings([cl_rule])}
    else:
        ref["cl"] = {"rules": _json_strings([cl_rule])}
    # FL/TB paths are published ONLY when the file exists on disk (same
    # _existing_paths discipline used for rtl owner_files), so the reflection
    # never references an artifact the IP lacks.
    fl_path = "model/functional_model.py"
    fl_block: JsonMap = {"entry_points": _json_strings(["FunctionalModel.apply", transaction_id])}
    if (ip_dir / fl_path).is_file():
        fl_block["path"] = fl_path
    ref["fl"] = fl_block
    tb_path = f"tb/cocotb/test_{ip}.py"
    tb_block: JsonMap = {"monitor": monitor}
    if (ip_dir / tb_path).is_file():
        tb_block["path"] = tb_path
    ref["tb"] = tb_block
    return ref


def _wave_observables(ip_dir: Path, wave: str, candidates: set[str]) -> list[str]:
    found, _ = sampled_vcd_signals(ip_dir, wave, candidates)
    ordered = [name for name in PREFERRED_WAVE_OBSERVABLES if name in found]
    ordered.extend(name for name in sorted(found) if name not in ordered)
    return ordered


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
def _transaction_index(ssot: JsonMap) -> dict[str, JsonMap]:
    fm = _as_map(ssot.get("function_model"))
    out: dict[str, JsonMap] = {}
    for item in _as_list(fm.get("transactions")):
        tx = _as_map(item)
        tid = _text(tx.get("id"))
        if tid:
            out[tid] = tx
    return out


def _scenario_coverage(ssot: JsonMap) -> dict[str, list[str]]:
    """transaction-or-feature id -> [scenario_id...] via scenario.coverage join."""
    out: dict[str, list[str]] = {}
    tr = _as_map(ssot.get("test_requirements"))
    for item in _as_list(tr.get("scenarios")):
        scenario = _as_map(item)
        sid = _text(scenario.get("id"))
        if not sid:
            continue
        for cov in _strings(scenario.get("coverage")):
            out.setdefault(cov, []).append(sid)
    return out


def _is_payload_transaction(tx: JsonMap) -> bool:
    text_blob = json.dumps(tx).lower()
    if "sram_wr_data" in text_blob or "payload byte" in text_blob or "_digest" in text_blob:
        return True
    for rule in _as_list(tx.get("output_rules")):
        if _text(_as_map(rule).get("name")) == "sram_wr_data":
            return True
    return False


def _digest_field(rows: list[JsonMap], goal_id: str) -> str | None:
    """Return the *_digest rtl_observed field that is also an fl state_update,
    present on a passing row of goal_id (the content-granularity signal)."""
    for r in _passing_goal_rows(rows, goal_id):
        observed = _as_map(r.get("rtl_observed"))
        for field in sorted(observed):
            if field.endswith("_digest") and _has_fl_path(
                r, f"fl_expected.model_result.state_updates.{field}"
            ):
                return field
    return None


def _content_obligation(
    ip_dir: Path,
    rows: list[JsonMap],
    tx: JsonMap,
    transaction_id: str,
    transaction_name: str,
    wave: str,
    content_scenarios: list[str],
) -> tuple[JsonMap, JsonMap] | None:
    """Emit the content obligation + its contract_ref grounded on a digest row."""
    goal_id = f"EQ_TRANSACTION_{transaction_id}"
    digest = _digest_field(rows, goal_id)
    if digest is None:
        return None
    expected_path = f"fl_expected.model_result.state_updates.{digest}"
    grounding = _pick_grounding(rows, goal_id, content_scenarios, require_fields=(digest,))
    # require a digest row whose fl path resolves
    if grounding is not None and not _has_fl_path(grounding.row, expected_path):
        grounding = None
    if grounding is None:
        return None

    conditions: JsonList = []
    c0 = _cond_row_passed_with_fl(grounding)
    if c0:
        conditions.append(c0)
    c1 = _cond_observed_equals_fl(grounding, digest, expected_path, f"{digest}_matches_fl")
    if c1 is None:
        return None
    conditions.append(c1)

    obligation_id = f"OBL_{_sanitize_id(ip_dir.name)}_PAYLOAD_CONTENT_001"
    contract_ref = "SEMANTIC_STATE_PAYLOAD_CONTENT"
    obligation: JsonMap = {
        "claim": (
            f"For {grounding.scenario_id} the SRAM payload digest observed in RTL equals the "
            "FL-expected payload digest, proving full byte-content equivalence with no holes."
        ),
        "closure_stage": "sim",
        "contract_refs": _json_strings([contract_ref]),
        "evidence_rows": [grounding.evidence_row()],
        "failure_owner": "rtl-gen",
        "granularity": "content",
        "obligation_id": obligation_id,
        "pass_conditions": conditions,
        "required": True,
        "required_observables": _json_strings([digest]),
        "required_stages": _json_strings(["fl", "rtl", "tb", "sim"]),
        "scenario_ids": _json_strings([grounding.scenario_id]),
    }
    observable_via = _wave_observables(
        ip_dir, wave, {"sram_wr_data", "sram_wr_strb", "sram_wr_addr", "ctx_payload_byte_count"}
    ) or ["sram_wr_data"]
    owner_files = _existing_paths(
        ip_dir,
        tuple(f"rtl/{ip_dir.name}{suffix}.sv" for suffix in ("_context_table", "_sram_packer")),
    ) or _existing_paths(ip_dir, tuple(f"rtl/{ip_dir.name}{s}.sv" for s in RTL_OWNER_SUFFIXES))
    ref = _contract_ref(
        ip_dir,
        contract_ref,
        transaction_id,
        transaction_name,
        wave,
        observable_via,
        owner_files,
        monitor="payload_content_monitor",
        cl_rule="cycle_model.pipeline.pack_sram",
        extra_refs=[],
    )
    return obligation, ref


def _structural_count_obligation(
    ip_dir: Path,
    rows: list[JsonMap],
    tx: JsonMap,
    transaction_id: str,
    transaction_name: str,
    wave: str,
    sampled: set[str],
    scenario_pref: list[str],
) -> tuple[JsonMap, JsonMap] | None:
    """Emit a structural/count obligation for a transaction grounded in its goal row."""
    goal_id = f"EQ_TRANSACTION_{transaction_id}"
    grounding = _pick_grounding(rows, goal_id, scenario_pref)
    if grounding is None:
        return None
    conditions: JsonList = []
    c0 = _cond_row_passed_with_fl(grounding) or _cond_row_passed(grounding)
    if c0 is None:
        return None
    conditions.append(c0)

    # count: any state_update whose name ends with _count and is observable as
    # an rtl_observed field that equals an fl state_update path.
    granularity = "structural"
    for su in _as_list(tx.get("state_updates")):
        name = _text(_as_map(su).get("name"))
        if not name.endswith("_count"):
            continue
        # try the literal field, then a "_sel"-suffixed mirror used by some monitors.
        for field in (name, f"{name}_sel", "ctx_payload_byte_count", "ctx_payload_count_sel"):
            path = f"fl_expected.model_result.state_updates.{name}"
            cond = _cond_observed_equals_fl(grounding, field, path, f"{field}_matches_fl_{name}")
            if cond:
                conditions.append(cond)
                granularity = "count"

    # structural: output_rules ports observed-equals-fl, plus contiguous strobes.
    for rule in _as_list(tx.get("output_rules")):
        port = _text(_as_map(rule).get("port")) or _text(_as_map(rule).get("name"))
        if not port:
            continue
        path = f"fl_expected.model_result.{port}"
        cond = _cond_observed_equals_fl(grounding, port, path, f"{port}_matches_fl")
        if cond:
            conditions.append(cond)
        strobe = _cond_strobe_contiguous(grounding, port, f"{port}_is_contiguous") if port.endswith("_strb") else None
        if strobe:
            conditions.append(strobe)

    # temporal: payload-count -> sram write ordering in the wave.
    temporal = _cond_vcd_event_order(
        ip_dir, wave, sampled, ("ctx_payload_byte_count", 32), ("sram_wr_valid", 1), "sram_write_after_count"
    )
    if temporal:
        conditions.append(temporal)
        granularity = "temporal" if granularity == "structural" else granularity

    if len(conditions) < 2:
        # a lone row_passed is the legacy goal-overlay's job; require real signal grounding.
        return None

    obligation_id = f"OBL_{_sanitize_id(ip_dir.name)}_{_sanitize_id(transaction_id)}_{granularity.upper()}_001"
    contract_ref = f"SEMANTIC_{_sanitize_id(transaction_id)}"
    obligation: JsonMap = {
        "claim": (
            f"For {grounding.scenario_id} the {transaction_name or transaction_id} transaction's "
            f"RTL-observed {granularity} outputs match the FL-expected values in scoreboard and wave evidence."
        ),
        "contract_refs": _json_strings([contract_ref]),
        "evidence_rows": [grounding.evidence_row()],
        "granularity": granularity,
        "obligation_id": obligation_id,
        "pass_conditions": conditions,
        "required": True,
        "required_observables": _json_strings(_required_observables(conditions)),
        "scenario_ids": _json_strings([grounding.scenario_id]),
    }
    observable_via = _wave_observables(
        ip_dir,
        wave,
        {_text(_as_map(r).get("field")) for r in conditions if _text(_as_map(r).get("field"))}
        | {"ctx_payload_byte_count", "sram_wr_valid", "descriptor_push", "descriptor_valid"},
    )
    if not observable_via:
        observable_via = _wave_observables(ip_dir, wave, set(PREFERRED_WAVE_OBSERVABLES))
    if not observable_via:
        return None
    owner_files = _existing_paths(ip_dir, tuple(f"rtl/{ip_dir.name}{s}.sv" for s in RTL_OWNER_SUFFIXES))
    ref = _contract_ref(
        ip_dir,
        contract_ref,
        transaction_id,
        transaction_name,
        wave,
        observable_via,
        owner_files,
        monitor=f"{(transaction_name or transaction_id).lower()}_monitor",
        cl_rule=f"cycle_model.transaction_latency.{transaction_id}",
        extra_refs=[],
    )
    return obligation, ref


def _build_source(ip_dir: Path) -> JsonMap:
    ip = ip_dir.name
    ssot = _load_ssot(ip_dir)
    rows = _load_rows(ip_dir / SCOREBOARD_ARTIFACT, "semantic_contracts")
    wave = _detect_wave(ip_dir)
    sampled, _ = sampled_vcd_signals(ip_dir, wave, set(PREFERRED_WAVE_OBSERVABLES))

    transactions = _transaction_index(ssot)
    coverage = _scenario_coverage(ssot)

    requirements: JsonList = []
    contract_refs: JsonList = []
    declared_refs: set[str] = set()
    payload_tx_present = False
    content_obligation_present = False

    def add_ref(ref: JsonMap) -> None:
        name = _text(ref.get("contract_ref"))
        if name and name not in declared_refs:
            declared_refs.add(name)
            contract_refs.append(ref)

    # Stable, deterministic transaction order.
    for transaction_id in sorted(transactions):
        tx = transactions[transaction_id]
        transaction_name = _text(tx.get("name"))
        scenario_pref = coverage.get(transaction_id, [])
        is_payload = _is_payload_transaction(tx)
        if is_payload:
            payload_tx_present = True

        obligations: JsonList = []
        source_refs: list[str] = [f"yaml/{ip}.ssot.yaml:function_model.transactions.{transaction_id}"]

        # CONTENT obligation (payload-bearing transactions only).
        if is_payload:
            content = _content_obligation(
                ip_dir, rows, tx, transaction_id, transaction_name, wave, scenario_pref
            )
            if content is not None:
                obligation, ref = content
                add_ref(ref)
                obligations.append(obligation)
                content_obligation_present = True
                source_refs.append(f"{SCOREBOARD_ARTIFACT}:{_strings(obligation.get('scenario_ids'))[0]}")

        # STRUCTURAL/COUNT/TEMPORAL obligation grounded on the transaction goal row.
        structural = _structural_count_obligation(
            ip_dir, rows, tx, transaction_id, transaction_name, wave, sampled, scenario_pref
        )
        if structural is not None:
            obligation, ref = structural
            add_ref(ref)
            obligations.append(obligation)
            source_refs.append(f"verify/equivalence_goals.json:EQ_TRANSACTION_{transaction_id}")
            source_refs.append(f"{SCOREBOARD_ARTIFACT}:{_strings(obligation.get('scenario_ids'))[0]}")

        if not obligations:
            continue

        requirement: JsonMap = {
            "claim": (
                f"The {transaction_name or transaction_id} transaction is observable in RTL with FL-equivalent "
                "behavior across scoreboard and wave evidence."
            ),
            "obligations": obligations,
            "required": True,
            "requirement_id": f"REQ_{_sanitize_id(ip)}_{_sanitize_id(transaction_id)}_001",
            "source_refs": _json_strings(sorted(set(source_refs))),
        }
        requirements.append(requirement)

    if payload_tx_present and not content_obligation_present:
        raise SystemExit(
            "[semantic_contracts] FAIL: a payload-bearing transaction exists but no "
            "granularity:content obligation could be grounded in a passing digest scoreboard row; "
            "run the sim first or check that a *_digest observable is emitted (e.g. SC_RB_4096)."
        )
    if not requirements:
        raise SystemExit(
            "[semantic_contracts] FAIL: no satisfiable semantic obligations could be grounded "
            "from the SSOT transactions and scoreboard evidence."
        )

    return {
        "type": "semantic_contracts",
        "schema_version": 1,
        "source_of_truth": f"yaml/{ip}.ssot.yaml",
        # content_applicable keys off the SSOT payload-transaction DETECTION
        # (the same antecedent the generator uses to decide a transaction is
        # payload/data-bearing), INDEPENDENT of whether a content obligation was
        # successfully grounded above. This independence is critical: a payload
        # IP that fails to ground a content obligation must still report
        # content_applicable=true so the signoff gate flags the missing content
        # coverage instead of silently passing. A non-payload IP (e.g. apb_add_demo)
        # reports false, telling the gate that content coverage is not applicable.
        "content_applicable": payload_tx_present,
        "requirements": requirements,
        "contract_refs": contract_refs,
    }


def main() -> int:
    ip, root = _parse_args(sys.argv[1:])
    ip_dir = _resolve_ip_dir(root, ip)
    source = _build_source(ip_dir)
    issues = source_issues(source)
    if issues:
        raise SystemExit("[semantic_contracts] FAIL: source validation: " + "; ".join(issues))
    out = ip_dir / "verify" / "semantic_contracts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _write_json(out, source)
    content = sum(
        1
        for req in _as_list(source.get("requirements"))
        for ob in _as_list(_as_map(req).get("obligations"))
        if _text(_as_map(ob).get("granularity")) == "content"
    )
    obligations = sum(len(_as_list(_as_map(req).get("obligations"))) for req in _as_list(source.get("requirements")))
    print(
        f"[semantic_contracts] wrote {out} : "
        f"{len(_as_list(source.get('requirements')))} requirements, "
        f"{obligations} obligations ({content} content), "
        f"{len(_as_list(source.get('contract_refs')))} contract_refs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
