#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final, Union

from pydantic import TypeAdapter, ValidationError
from typing_extensions import TypeAliasType

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow.contract_reflection.evidence_contract_vcd import sampled_vcd_signals


JsonValue = TypeAliasType("JsonValue", Union[None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]])
JsonMap = dict[str, JsonValue]
JsonList = list[JsonValue]
JSON_ADAPTER: Final[TypeAdapter[JsonValue]] = TypeAdapter(JsonValue)
LEGACY_REQ: Final = "REQ_LEGACY_EQUIVALENCE_GOAL_CLOSURE_001"
LEGACY_REF: Final = "LEGACY_SCOREBOARD_GOAL_CLOSURE"
SCOREBOARD_ARTIFACT: Final = "sim/scoreboard_events.jsonl"
PREFERRED_WAVE_OBSERVABLES: Final[tuple[str, ...]] = (
    "payload_byte_count",
    "ctx_payload_count",
    "ctx_state",
    "descriptor_count",
    "sram_wr_valid",
    "sram_wr_strb",
    "prdata",
    "pready",
)


def _load_json(path: Path, label: str) -> JsonMap:
    if not path.is_file():
        raise SystemExit(f"[{label}] FAIL: missing {path}")
    try:
        value = JSON_ADAPTER.validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise SystemExit(f"[{label}] FAIL: invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"[{label}] FAIL: {path} root must be an object")
    return value


def _load_json_or_default(path: Path, label: str, default: JsonMap) -> JsonMap:
    if path.is_file():
        return _load_json(path, label)
    return default


def _load_rows(path: Path) -> list[JsonMap]:
    if not path.is_file():
        raise SystemExit(f"[goal_overlay] FAIL: missing {path}")
    rows: list[JsonMap] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = JSON_ADAPTER.validate_json(raw)
        except ValidationError as exc:
            raise SystemExit(f"[goal_overlay] FAIL: {path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise SystemExit(f"[goal_overlay] FAIL: {path}:{line_no}: row must be an object")
        rows.append(value)
    return rows


def _as_list(value: JsonValue) -> JsonList:
    return value if isinstance(value, list) else []


def _as_map(value: JsonValue) -> JsonMap:
    return value if isinstance(value, dict) else {}


def _text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def _json_strings(values: list[str] | tuple[str, ...]) -> JsonList:
    out: JsonList = []
    for value in values:
        out.append(value)
    return out


def _write_json(path: Path, payload: JsonMap) -> None:
    _ = path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    raw_ip = Path(ip)
    if raw_ip.is_absolute():
        raise SystemExit(f"[goal_overlay] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw_ip).resolve()
    try:
        _ = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[goal_overlay] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def _sanitize_id(raw: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in raw.upper())
    return "_".join(part for part in cleaned.split("_") if part)


def _rows_by_goal(rows: list[JsonMap]) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for row in rows:
        goal_id = _text(row.get("goal_id"))
        if goal_id and goal_id not in out:
            out[goal_id] = row
    return out


def _goal_ids(goals_doc: JsonMap) -> list[str]:
    goal_ids: list[str] = []
    for item in _as_list(goals_doc.get("goals")):
        goal_id = _text(_as_map(item).get("goal_id"))
        if goal_id:
            goal_ids.append(goal_id)
    return goal_ids


def _goal_obligation(goal_id: str, row: JsonMap | None) -> JsonMap:
    scenario_id = _text(row.get("scenario_id")) if row is not None else ""
    observed = _as_map(row.get("rtl_observed")) if row is not None else {}
    obligation_id = f"OBL_GOAL_{_sanitize_id(goal_id)}"
    evidence_rows: JsonList = []
    if scenario_id:
        evidence_rows.append({"artifact": SCOREBOARD_ARTIFACT, "match": {"goal_id": goal_id, "scenario_id": scenario_id}})
    claim = f"Generated equivalence goal {goal_id} closes through its scoreboard row."
    if row is None:
        claim = f"Generated equivalence goal {goal_id} requires a matching scoreboard row before closure."
    return {
        "claim": claim,
        "contract_refs": _json_strings([LEGACY_REF]),
        "evidence_rows": evidence_rows,
        "obligation_id": obligation_id,
        "pass_conditions": [{"id": "scoreboard_row_passed", "kind": "row_passed"}],
        "required": True,
        "required_observables": _json_strings(sorted(observed.keys())),
        "requirement_ids": _json_strings([LEGACY_REQ]),
        "scenario_ids": _json_strings([scenario_id] if scenario_id else []),
    }


def _replace_by_id(items: JsonList, id_key: str, replacement: JsonMap) -> JsonList:
    out: JsonList = []
    for item in items:
        data = _as_map(item)
        if data.get(id_key) != replacement.get(id_key):
            out.append(data)
    out.append(replacement)
    return out


def _without_legacy_obligations(items: JsonList) -> JsonList:
    out: JsonList = []
    for item in items:
        data = _as_map(item)
        if LEGACY_REQ not in _as_list(data.get("requirement_ids")):
            out.append(data)
    return out


def _detect_wave(ip_dir: Path) -> str:
    preferred = ip_dir / "sim" / f"{ip_dir.name}.vcd"
    if preferred.is_file():
        return preferred.relative_to(ip_dir).as_posix()
    for path in sorted((ip_dir / "sim").glob("*.vcd")):
        return path.relative_to(ip_dir).as_posix()
    raise SystemExit(f"[goal_overlay] FAIL: missing VCD under {ip_dir / 'sim'}")


def _existing_paths(ip_dir: Path, paths: tuple[str, ...]) -> JsonList:
    return _json_strings([path for path in paths if (ip_dir / path).is_file()])


def _sampled_observables(ip_dir: Path, wave: str, rows: list[JsonMap]) -> JsonList:
    candidates: set[str] = set()
    for row in rows:
        candidates.update(_as_map(row.get("rtl_observed")).keys())
    ordered = [name for name in PREFERRED_WAVE_OBSERVABLES if name in candidates]
    ordered.extend(name for name in sorted(candidates) if name not in ordered)
    sampled: list[str] = []
    for name in ordered:
        found, _ = sampled_vcd_signals(ip_dir, wave, {name})
        if found:
            sampled.append(name)
        if len(sampled) >= 8:
            break
    if not sampled and ordered:
        sampled.append(ordered[0])
    return _json_strings(sampled)


def _legacy_reflection(ip_dir: Path, wave: str, rows: list[JsonMap]) -> JsonMap:
    ip = ip_dir.name
    return {
        "cl": {"path": "model/cycle_model.py", "rules": _json_strings(["generated_equivalence_goals"])},
        "contract_ref": LEGACY_REF,
        "fl": {"entry_points": _json_strings(["FunctionalModel.apply"]), "path": "model/functional_model.py"},
        "rtl": {
            "observable_via": _sampled_observables(ip_dir, wave, rows),
            "owner_files": _existing_paths(
                ip_dir,
                (
                    f"rtl/{ip}.sv",
                    f"rtl/{ip}_axi_write_ingress.sv",
                    f"rtl/{ip}_mctp_parser.sv",
                    f"rtl/{ip}_context_table.sv",
                    f"rtl/{ip}_sram_packer.sv",
                    f"rtl/{ip}_descriptor_queue.sv",
                    f"rtl/{ip}_apb_regfile.sv",
                ),
            ),
        },
        "sim": {"scoreboard": SCOREBOARD_ARTIFACT, "wave": wave},
        "ssot": {"path": f"yaml/{ip}.ssot.yaml", "refs": _json_strings(["verify.equivalence_goals"])},
        "tb": {"monitor": "legacy_scoreboard_goal_monitor", "path": f"tb/cocotb/test_{ip}.py"},
    }


def _parse_args(argv: list[str]) -> tuple[str, Path]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise SystemExit("usage: emit_goal_contract_overlay.py <ip> [--root <root>]")
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


def main() -> int:
    ip, root = _parse_args(sys.argv[1:])
    ip_dir = _resolve_ip_dir(root, ip)
    verify_dir = ip_dir / "verify"
    requirements = _load_json_or_default(
        verify_dir / "requirements_index.json",
        "goal_overlay",
        {"requirements": [], "schema_version": 1, "type": "requirements_index"},
    )
    contract = _load_json_or_default(
        verify_dir / "evidence_contract.json",
        "goal_overlay",
        {"obligations": [], "schema_version": 1, "type": "evidence_contract"},
    )
    reflection = _load_json_or_default(
        verify_dir / "contract_reflection.json",
        "goal_overlay",
        {"contract_refs": [], "schema_version": 1, "type": "contract_reflection"},
    )
    goals_doc = _load_json(verify_dir / "equivalence_goals.json", "goal_overlay")
    rows = _load_rows(ip_dir / SCOREBOARD_ARTIFACT)
    row_by_goal = _rows_by_goal(rows)
    goal_obligations = [_goal_obligation(goal_id, row_by_goal.get(goal_id)) for goal_id in _goal_ids(goals_doc)]
    requirement: JsonMap = {
        "claim": "Every generated equivalence goal has a scoreboard row tied to RTL-observed fields.",
        "obligation_ids": _json_strings([_text(item.get("obligation_id")) for item in goal_obligations]),
        "required": True,
        "requirement_id": LEGACY_REQ,
        "source_refs": _json_strings(["verify/equivalence_goals.json", SCOREBOARD_ARTIFACT]),
    }
    wave = _detect_wave(ip_dir)
    requirements["requirements"] = _replace_by_id(_as_list(requirements.get("requirements")), "requirement_id", requirement)
    contract["obligations"] = [*_without_legacy_obligations(_as_list(contract.get("obligations"))), *goal_obligations]
    reflection["contract_refs"] = _replace_by_id(_as_list(reflection.get("contract_refs")), "contract_ref", _legacy_reflection(ip_dir, wave, rows))
    _write_json(verify_dir / "requirements_index.json", requirements)
    _write_json(verify_dir / "evidence_contract.json", contract)
    _write_json(verify_dir / "contract_reflection.json", reflection)
    print(f"[goal_overlay] wrote {len(goal_obligations)} goal obligations with wave={wave}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
