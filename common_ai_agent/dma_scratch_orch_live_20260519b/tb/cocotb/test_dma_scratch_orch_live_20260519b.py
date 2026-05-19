from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import cocotb
from cocotb.binary import BinaryValue
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _project_root() -> Path:
    return Path(os.environ.get("PROJECT_ROOT") or _ip_dir().parent).resolve()


def _load_manifest() -> dict[str, Any]:
    manifest = json.loads((_ip_dir() / "tb" / "cocotb" / "tb_manifest.json").read_text(encoding="utf-8"))
    runtime = Path(os.environ.get("COMMON_AI_AGENT_ROOT") or manifest["common_ai_agent_root"]) / "workflow" / "tb-gen" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    return manifest


def _goals(ip_dir: Path) -> list[dict[str, Any]]:
    doc = json.loads((ip_dir / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))
    return [goal for goal in doc.get("goals", []) if isinstance(goal, dict) and goal.get("blocked") is not True]


def _has_signal(dut, name: str) -> bool:
    return hasattr(dut, name)


def _set_signal(dut, name: str, value: int | str) -> None:
    if not _has_signal(dut, name):
        raise AssertionError(f"DUT missing signal {name}")
    getattr(dut, name).value = BinaryValue(value) if isinstance(value, str) else int(value)


def _get_signal(dut, name: str) -> int | str:
    if not _has_signal(dut, name):
        raise AssertionError(f"DUT missing signal {name}")
    value = getattr(dut, name).value
    try:
        return int(value)
    except ValueError:
        return str(value)


def _default_field_value(field: str, idx: int) -> int:
    low = field.lower()
    if low in {"rst", "reset", "areset", "reset_n", "rst_n", "aresetn"}:
        return 0
    if low.endswith("_hresp") or low == "hresp" or low.endswith("_resp"):
        return 0
    if low.endswith("_hready") or low == "hready":
        return 1
    if low.endswith("_hrdata") or low == "hrdata":
        return 0
    bool_exact = {
        "valid", "in_valid", "cfg_valid", "req_valid", "ready", "result_valid",
        "packet_ok", "ack", "nack", "rw", "read", "write", "broadcast",
        "accept", "reject", "miss",
    }
    bool_suffixes = (
        "_valid", "_ready", "_enable", "_pending", "_error", "_unsupported",
        "_illegal", "_hit", "_ok", "_req", "_seen", "_flag",
    )
    if low in bool_exact or low.startswith(("is_", "has_", "illegal_", "unsupported_", "enable_", "disable_")) or low.endswith(bool_suffixes):
        return 1
    if "addr" in low:
        return idx + 1
    if "pec" in low or "crc" in low:
        return 13 + idx
    if "data" in low or "value" in low or "payload" in low or "count" in low:
        return 13 + idx
    return idx + 1


def _goal_text(goal: dict[str, Any]) -> str:
    pieces = []
    for key in ("goal_id", "title", "description", "scenario", "intent"):
        value = goal.get(key)
        if value:
            pieces.append(str(value))
    for key in ("constraints", "pass_criteria", "coverage_refs", "tags"):
        value = goal.get(key)
        if value:
            try:
                pieces.append(json.dumps(value, sort_keys=True))
            except TypeError:
                pieces.append(str(value))
    for key in ("stimulus_contract", "expected_contract"):
        value = goal.get(key)
        if value:
            try:
                pieces.append(json.dumps(value, sort_keys=True))
            except TypeError:
                pieces.append(str(value))
    text = " ".join(pieces).lower()
    normalized = text.replace("_", " ").replace("-", " ")
    return f"{text} {normalized}"


def _goal_stimulus_text(goal: dict[str, Any]) -> str:
    """Text that describes what the TB should drive.

    Keep expected error-policy prose out of stimulus selection. A positive APB
    write transaction can still document its invalid-address error case, but
    that should not make the generated stimulus choose an invalid address.
    """
    pieces = []
    for key in ("goal_id", "title", "description", "scenario", "intent"):
        value = goal.get(key)
        if value:
            pieces.append(str(value))
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    if contract:
        try:
            pieces.append(json.dumps(contract, sort_keys=True))
        except TypeError:
            pieces.append(str(contract))
    text = " ".join(pieces).lower()
    normalized = text.replace("_", " ").replace("-", " ")
    return f"{text} {normalized}"


def _constraint_field_value(manifest: dict[str, Any], goal: dict[str, Any], field: str) -> int | None:
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    text = " ".join(str(item).lower() for item in contract.get("constraints") or [])
    compact = re.sub(r"\s+", "", text)
    low = field.lower()
    active_reset = 0 if manifest.get("reset_active") == "low" else 1
    inactive_reset = 1 - active_reset
    if low in {"rst", "reset", "areset", "reset_n", "rst_n", "aresetn"}:
        if any(token in text for token in ("rst deasserted", "reset deasserted", "reset released")):
            return inactive_reset
        if any(token in text for token in ("rst asserted", "reset asserted", "reset active")):
            return active_reset
    if low.endswith("_hready") or low == "hready":
        if f"{low}==0" in compact or f"{low}=0" in compact or f"deassert{low}" in compact:
            return 0
        if f"{low}==1" in compact or f"{low}=1" in compact or f"assert{low}" in compact:
            return 1
    if low.endswith("_hresp") or low == "hresp" or low.endswith("_resp"):
        if f"{low}==error" in compact or f"{low}=error" in compact:
            return 1
        if f"{low}==okay" in compact or f"{low}=okay" in compact or f"{low}==ok" in compact:
            return 0
    return None


def _norm_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _word_tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _infer_access_op(goal: dict[str, Any], tx_type: str = "") -> str:
    tx_tokens = _word_tokens(str(tx_type).replace("_", " ").replace("-", " "))
    if {"wr", "write"} & tx_tokens:
        return "write"
    if {"rd", "read"} & tx_tokens:
        return "read"
    text = _goal_identity_text(goal, tx_type)
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    text += " " + str(contract.get("transaction_type") or "")
    text += " " + _goal_stimulus_text(goal)
    tokens = _word_tokens(text.replace("_", " ").replace("-", " "))
    if {"wr", "write"} & tokens:
        return "write"
    if {"rd", "read"} & tokens:
        return "read"
    return "write"


def _contract_tx_type(contract: dict[str, Any], manifest: dict[str, Any]) -> str:
    raw = contract.get("transaction_type")
    if raw is None or str(raw).strip().lower() in {"", "none", "null"}:
        raw = manifest.get("transaction_kind") or "FM_PRIMARY"
    return str(raw)


def _goal_identity_text(goal: dict[str, Any], tx_type: str = "") -> str:
    pieces = [tx_type]
    for key in ("goal_id", "title", "kind", "scenario", "intent"):
        value = goal.get(key)
        if value:
            pieces.append(str(value))
    text = " ".join(pieces).lower()
    normalized = text.replace("_", " ").replace("-", " ")
    return f"{text} {normalized}"


def _is_csr_goal(goal: dict[str, Any], tx_type: str) -> bool:
    goal_kind = _norm_token(goal.get("kind"))
    tx_norm = _norm_token(tx_type)
    identity = _goal_identity_text(goal, tx_type)
    stimulus_text = _goal_stimulus_text(goal)
    full_text = _goal_text(goal)
    if goal_kind == "register":
        return True
    if tx_norm in {"csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr"}:
        return True
    if any(token in tx_norm for token in ("csr", "register", "control_status", "apb")):
        return True
    if any(token in stimulus_text for token in ("apb_valid", "apb_access", "paddr", "psel", "penable", "pwrite", "addr ==")):
        return True
    if any(token in full_text for token in ("apb", "pstrb", "pready", "pslverr", "psel_penable")):
        return True
    return any(token in identity for token in ("register access", "control status", "apb", "csr"))


def _is_reset_goal(goal: dict[str, Any], tx_type: str, *, is_csr: bool = False) -> bool:
    if is_csr:
        return False
    goal_kind = _norm_token(goal.get("kind"))
    tx_norm = _norm_token(tx_type)
    identity = _goal_identity_text(goal, tx_type)
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    constraints_text = " ".join(str(item).lower() for item in contract.get("constraints") or [])
    if "backpressure" in identity or "ready is high after reset" in identity:
        return False
    if any(token in constraints_text for token in ("rst deasserted", "reset deasserted", "reset released")):
        return False
    if any(token in constraints_text for token in ("rst asserted", "reset asserted", "reset active")):
        return True
    return (
        goal_kind == "reset"
        or tx_norm in {"reset", "fm_reset", "sc_reset", "reset_defaults", "reset_boot"}
        or "fm_reset" in identity
        or "sc_reset" in identity
        or "reset_defaults" in identity
        or "reset boot" in identity
    )


def _sample_condition_names(manifest: dict[str, Any]) -> set[str]:
    names = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", str(manifest.get("sample_condition") or "")))
    return names - {"and", "or", "not", "true", "false", "True", "False"}


def _is_sampled_goal(goal: dict[str, Any], tx_type: str, *, is_reset: bool = False, is_csr: bool = False) -> bool:
    if is_reset or is_csr:
        return False
    goal_kind = _norm_token(goal.get("kind"))
    tx_norm = _norm_token(tx_type)
    identity = _goal_identity_text(goal, tx_type)
    goal_text = _goal_text(goal)
    if "backpressure" in identity or "backpressure" in goal_text or "ready is high" in goal_text:
        return True
    if tx_norm in {"fm_primary", "primary", "primary_behavior"} or "primary_behavior" in tx_norm:
        return True
    if re.fullmatch(r"sc\d+", tx_norm) and not any(token in identity for token in ("apb", "csr", "register", "reset")):
        return True
    if goal_kind == "state":
        return True
    if any(
        token in identity
        for token in (
            "accepted transaction",
            "valid ready",
            "channel start",
            "command start",
            "transaction accept",
            "transfer start",
            "packet accept",
        )
    ):
        return True
    if any(
        token in goal_text
        for token in (
            "valid is high",
            "valid high",
            "assert valid",
            "valid &&",
            "valid ready",
            "sampled",
            "sample data",
            "accepted",
            "result_valid",
            "produce result",
            "emit result",
            "observe result",
            "waveform",
        )
    ):
        return True
    return False


def _set_sample_activity(stimulus: dict[str, Any], manifest: dict[str, Any], active: bool) -> None:
    stimulus["_sample_active"] = bool(active)
    value = 1 if active else 0
    input_ports = {str(port) for port in (manifest.get("input_ports") or [])}
    for port in manifest.get("sample_inputs") or []:
        stimulus[str(port)] = value
    sample_names = _sample_condition_names(manifest)
    if not sample_names:
        return
    input_map = manifest.get("input_map") or {}
    for name in sample_names:
        if name in input_ports:
            stimulus[name] = value
    for field, port in input_map.items():
        if field in sample_names or str(port) in sample_names:
            stimulus[field] = value


def _param_int(manifest: dict[str, Any], key: str, default: int = 0) -> int:
    raw = (manifest.get("parameters") or {}).get(key, default)
    try:
        return int(raw)
    except Exception:
        text = str(raw or "").replace("_", "").strip()
        try:
            return int(text, 16) if text.lower().startswith("0x") else int(text)
        except Exception:
            return default


def _named_windows(manifest: dict[str, Any]) -> list[dict[str, int | str]]:
    params = manifest.get("parameters") if isinstance(manifest.get("parameters"), dict) else {}
    windows = []
    for key in sorted(params):
        if not key.endswith("_BASE"):
            continue
        prefix = key[:-5]
        size = 0
        for size_key in (
            f"{prefix}_WINDOW_BYTES",
            f"{prefix}_WINDOW_SIZE",
            f"{prefix}_SIZE_BYTES",
            f"{prefix}_SIZE",
        ):
            if size_key in params:
                size = _param_int(manifest, size_key, 0)
                break
        if size <= 0:
            size = 4096
        windows.append({"prefix": prefix, "base": _param_int(manifest, key, 0), "size": max(size, 4)})
    return windows


def _register_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    regs = manifest.get("registers") if isinstance(manifest.get("registers"), dict) else {}
    rows = regs.get("register_list") if isinstance(regs.get("register_list"), list) else []
    return [row for row in rows if isinstance(row, dict) and "offset" in row]


def _register_access_allowed(row: dict[str, Any], op: str) -> bool:
    access = str(row.get("access") or "rw").lower()
    if op == "read":
        return "r" in access
    if op == "write":
        return "w" in access
    return True


def _register_row_for_goal(manifest: dict[str, Any], goal: dict[str, Any]) -> dict[str, Any] | None:
    text = _goal_stimulus_text(goal)
    text_norm = _norm_token(text)
    for row in _register_rows(manifest):
        name = str(row.get("name") or "")
        norm = _norm_token(name)
        if norm and (norm in text_norm or name.lower() in text):
            return row
    return None


def _adjust_register_op_for_access(row: dict[str, Any] | None, op: str) -> str:
    if row is None or _register_access_allowed(row, op):
        return op
    if _register_access_allowed(row, "read"):
        return "read"
    if _register_access_allowed(row, "write"):
        return "write"
    return op


def _wants_error_access(goal: dict[str, Any]) -> bool:
    text = _goal_stimulus_text(goal)
    if "always high during access phase for legal and illegal accesses" in text:
        return False
    return any(
        token in text
        for token in (
            "illegal_offset",
            "illegal offset",
            "offset is illegal",
            "invalid address",
            "addr_valid == 0",
            "complete with error",
            "outside register",
            "non-register",
            "unmapped",
            "error_qualify",
            "pslverr is high",
            "write to read-only",
            "write to readonly",
            "not equal to supported",
            "not ((addr ==",
            "not (addr ==",
        )
    )


def _register_offset_for_goal(manifest: dict[str, Any], goal: dict[str, Any], idx: int, default: int) -> int:
    rows = _register_rows(manifest)
    if not rows:
        return default
    text = _goal_stimulus_text(goal)
    if _wants_error_access(goal) and not _register_row_for_goal(manifest, goal):
        max_offset = max(int(row.get("offset", 0)) for row in rows)
        return max_offset + 4
    row = _register_row_for_goal(manifest, goal)
    if row is not None:
        return int(row.get("offset", default))
    op = _infer_access_op(goal, _contract_tx_type(goal.get("stimulus_contract") or {}, manifest))
    candidates = [row for row in rows if _register_access_allowed(row, op)]
    if not candidates:
        candidates = rows
    return int(candidates[idx % len(candidates)].get("offset", default))


def _window_matches_text(window: dict[str, int | str], text: str) -> bool:
    prefix = str(window["prefix"]).lower()
    tokens = {prefix, prefix.replace("_", " "), prefix.split("_", 1)[0]}
    return any(token and token in text for token in tokens)


def _selected_window(manifest: dict[str, Any], goal: dict[str, Any]) -> dict[str, int | str] | None:
    text = _goal_text(goal)
    windows = _named_windows(manifest)
    for window in windows:
        if _window_matches_text(window, text):
            return window
    if windows and any(
        token in text
        for token in (
            "window",
            "mapped",
            "decoded",
            "decode",
            "route",
            "from memory",
            "memory route",
            "route to memory",
            "mux from memory",
        )
    ):
        return windows[0]
    return None


def _address_value_for_goal(manifest: dict[str, Any], goal: dict[str, Any], idx: int, default: int) -> int:
    text = _goal_text(goal)
    stimulus_text = _goal_stimulus_text(goal)
    rows = _register_rows(manifest)
    if rows and _wants_error_access(goal) and not _register_row_for_goal(manifest, goal):
        max_offset = max(int(row.get("offset", 0)) for row in rows)
        return max_offset + 4
    for pattern in (
        r"['\"]offset['\"]\s*:\s*(0x[0-9a-fA-F]+|\d+)",
        r"\boffset\s*(?:=|:)\s*(0x[0-9a-fA-F]+|\d+)",
        r"\b(?:paddr|addr)\s*==\s*(0x[0-9a-fA-F]+|\d+)",
        r"\b(?:paddr|addr)\s*(?:=|:)\s*(0x[0-9a-fA-F]+|\d+)",
        r"\bat\s+(0x[0-9a-fA-F]+)",
    ):
        match = re.search(pattern, text)
        if match:
            raw = match.group(1)
            return int(raw, 16) if raw.lower().startswith("0x") else int(raw, 10)
    window = _selected_window(manifest, goal)
    windows = _named_windows(manifest)
    if window is None and windows and any(token in text for token in ("memory", "outside", "non-", "non_")):
        window = windows[0]
        base = int(window["base"])
        size = int(window["size"])
        return base + size + ((idx % 8) * 4)
    if window is None:
        return _register_offset_for_goal(manifest, goal, idx, default)
    base = int(window["base"])
    size = int(window["size"])
    if any(token in text for token in ("below", "underflow", "before")):
        return max(base - 4, 0)
    if any(
        token in text
        for token in (
            "above",
            "overflow",
            "after",
            "outside",
            "non-",
            "non_",
            "from memory",
            "memory route",
            "route to memory",
            "mux from memory",
        )
    ):
        return base + size
    if "boundary" in text:
        choices = [base, base + max(size - 4, 0), max(base - 4, 0), base + size]
        return choices[idx % len(choices)]
    return base + ((idx * 4) % size)


def _outside_selected_window(manifest: dict[str, Any], goal: dict[str, Any]) -> bool:
    window = _selected_window(manifest, goal)
    if window is None:
        return False
    text = _goal_text(goal)
    prefix = str(window["prefix"]).lower()
    return any(
        token in text
        for token in (
            f"non_{prefix}",
            f"non-{prefix}",
            f"non {prefix}",
            "outside",
            "above",
            "below",
            "before",
            "after",
            "from memory",
            "memory route",
            "route to memory",
            "mux from memory",
        )
    )


def _field_route_prefix(field: str) -> str:
    low = field.lower()
    for suffix in ("_ready", "_valid", "_error", "_rdata", "_wdata", "_cmd_valid", "_cmd_ready"):
        if low.endswith(suffix):
            return low[: -len(suffix)]
    if "_" in low:
        return low.split("_", 1)[0]
    return ""


def _port_width(manifest: dict[str, Any], port: str) -> int:
    raw = (manifest.get("port_widths") or {}).get(port, 1)
    params = manifest.get("parameters") or {}
    if isinstance(raw, str) and raw in params:
        raw = params[raw]
    try:
        return max(int(raw), 1)
    except Exception:
        return 1


def _fit_port_value(manifest: dict[str, Any], port: str, value: int) -> int:
    width = _port_width(manifest, port)
    if width <= 0:
        return int(value)
    return int(value) & ((1 << width) - 1)


def _highz_value(manifest: dict[str, Any], port: str) -> str:
    return "z" * max(_port_width(manifest, port), 1)


def _inout_ports(manifest: dict[str, Any]) -> set[str]:
    explicit = {str(port) for port in (manifest.get("inout_ports") or [])}
    if explicit:
        return explicit
    # Backward compatibility for manifests written before inout_ports existed:
    # a port declared as both input and output is a bidirectional pad.
    return set(manifest.get("input_ports") or []) & set(manifest.get("output_ports") or [])


def _should_drive_inout_port(manifest: dict[str, Any], stimulus: dict[str, Any], port: str) -> bool:
    if port not in _inout_ports(manifest):
        return True
    text = " ".join(
        str(stimulus.get(key, ""))
        for key in ("kind", "op", "scenario_id", "goal_id")
    ).lower()
    if any(token in text for token in ("output", "pin_drive", "pad_drive", "drive_output")):
        return False
    if any(token in text for token in ("input", "capture", "sample", "external", "pad_input")):
        return port in stimulus or any(str(p) == port for p in (manifest.get("sample_inputs") or []))
    return False


def _stimulus_value_for_field(manifest: dict[str, Any], field: str, idx: int, goal: dict[str, Any] | None = None) -> Any:
    goal = goal or {}
    text = _goal_text(goal)
    low = field.lower()
    goal_kind = str(goal.get("kind") or "").lower()
    if low in {"op", "operation", "cmd", "command"} and low not in (manifest.get("input_map") or {}):
        if goal_kind == "register" or any(token in text for token in ("csr", "register", "apb")):
            return _infer_access_op(goal)
        if goal_kind == "memory":
            return _infer_access_op(goal)
    value = _default_field_value(field, idx)
    selected = _selected_window(manifest, goal)
    selected_prefix = str(selected["prefix"]).lower() if selected else ""
    selected_token = selected_prefix.split("_", 1)[0] if selected_prefix else ""
    outside_selected = _outside_selected_window(manifest, goal)
    if "addr" in low:
        value = _address_value_for_goal(manifest, goal, idx, value)
    elif low == "read" or low.endswith("_read"):
        if "write" in text and "read" not in text:
            value = 0
        elif "read" in text:
            value = 1
    elif low.endswith(("_write", "_we")) or low in {"write", "rw"}:
        if "read" in text and "write" not in text:
            value = 0
        elif "write" in text:
            value = 1
    elif low == "quad_enable" or low.endswith("_quad_enable"):
        if "single" in text or "1 lane" in text or "one lane" in text:
            value = 0
        elif "quad" in text:
            value = 1
    elif low == "ddr_enable" or low.endswith("_ddr_enable"):
        if any(token in text for token in ("sdr", "ddr disabled", "ddr disable", "disabled fall", "fall edge suppression")):
            value = 0
        elif "ddr" in text:
            value = 1
    elif low == "illegal_mode" or low.endswith("_illegal_mode") or low.endswith("_illegal"):
        value = 1 if "illegal" in text else 0
    elif low == "unsupported_width" or low.endswith("_unsupported_width") or low.endswith("_unsupported"):
        value = 1 if "unsupported" in text else 0
    elif low in {"axi_error", "invalid_operand", "undefined_instr", "watchdog_timeout", "kill_req"}:
        value = 1 if any(token in text for token in ("error", "fault", "abort", "illegal", "invalid", "undefined", "watchdog", "kill", "halt")) else 0
    elif low.endswith("_hresp") or low == "hresp" or low.endswith("_resp"):
        stimulus_text = _goal_stimulus_text(goal)
        if any(token in stimulus_text for token in ("bus error", "bus_error", "fault_halt", "fault halt", "hresp==error", "hresp == error")):
            value = 1
    elif low in {"op_is_load", "is_load"} or low.endswith("_is_load"):
        value = 0 if goal_kind == "memory" and "write" in text else (1 if "read" in text or ("memory" in text and "write" not in text) else 0)
    elif low in {"op_is_store", "is_store"} or low.endswith("_is_store"):
        value = 1 if "write" in text or "store" in text or "memory" in text else 0
    elif low == "irq_enable" or low.endswith("_irq_enable"):
        value = 1 if "irq" in text else value
    elif low.endswith("_ready"):
        route = _field_route_prefix(field)
        if selected_token and outside_selected and selected_token in route:
            value = 0
        elif selected_token and outside_selected and route.startswith(("mem", "memory")):
            value = 1
        elif selected_token and selected_token in route:
            value = 1
        elif selected_token and route and route not in {"cpu", "bus", "req"}:
            value = 0
        elif not selected_token and "memory" in text and route.startswith(("mem", "memory")):
            value = 1
    elif low.endswith("_error"):
        route = _field_route_prefix(field)
        wants_error = "error" in text or "fault" in text
        if selected_token and outside_selected and selected_token in route:
            value = 0
        elif selected_token and outside_selected and route.startswith(("mem", "memory")):
            value = 1 if wants_error else 0
        elif selected_token and selected_token in route:
            value = 1 if wants_error else 0
        elif selected_token and route and route not in {"cpu", "bus", "req"}:
            value = 0
    elif "rdata" in low or "read_data" in low:
        route = _field_route_prefix(field)
        if low.endswith("_hrdata") and low.startswith("i_") and any(token in text for token in ("load", "store", "stall_mem", "d_hresp")):
            value = 0x8000 if "store" in text and "load" not in text else 0x7000
        elif selected_token and outside_selected and selected_token in route:
            value = 0x0BAD0000 + idx
        elif selected_token and outside_selected and route.startswith(("mem", "memory")):
            value = 0x5A000000 + idx
        elif selected_token and selected_token in route:
            value = 0xA5000000 + idx
        elif selected_token and route:
            value = 0x5A000000 + idx
        elif "memory" in text and route.startswith(("mem", "memory")):
            value = 0x5A000000 + idx
    constraint_value = _constraint_field_value(manifest, goal, field)
    if constraint_value is not None:
        value = constraint_value
    port = (manifest.get("input_map") or {}).get(field)
    if port:
        value = _fit_port_value(manifest, str(port), value)
    return int(value)


def _stimulus_for_goal(goal: dict[str, Any], manifest: dict[str, Any], idx: int) -> dict[str, Any]:
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    required = [str(x) for x in contract.get("required_fields") or [] if str(x).strip()]
    goal_text = _goal_text(goal)
    goal_kind = str(goal.get("kind") or "").lower()
    tx_type = _contract_tx_type(contract, manifest)
    tx_type_norm = tx_type.lower()
    is_csr_goal = _is_csr_goal(goal, tx_type)
    is_reset_goal = _is_reset_goal(goal, tx_type, is_csr=is_csr_goal)
    sample_active = _is_sampled_goal(goal, tx_type, is_reset=is_reset_goal, is_csr=is_csr_goal)
    stimulus: dict[str, Any] = {
        "kind": tx_type,
        "scenario_id": f"SC_{idx + 1:03d}_{goal.get('goal_id')}",
        "cycle": idx,
        "observed_signals": {},
    }
    for field in manifest.get("input_map", {}):
        stimulus[field] = _stimulus_value_for_field(manifest, field, idx, goal)
    for field in required:
        if field in {"kind", "scenario_id", "cycle", "observed_signals"}:
            continue
        stimulus.setdefault(field, _stimulus_value_for_field(manifest, field, idx, goal))
    if is_reset_goal:
        stimulus["kind"] = "reset"
        for field in manifest.get("input_map", {}):
            stimulus[field] = 0
        _set_sample_activity(stimulus, manifest, False)
        return stimulus
    if is_csr_goal:
        matched_row = _register_row_for_goal(manifest, goal)
        inferred_op = _infer_access_op(goal, tx_type)
        op_norm = inferred_op if _wants_error_access(goal) else _adjust_register_op_for_access(matched_row, inferred_op)
        stimulus.setdefault("op", op_norm)
        if matched_row is not None:
            addr = int(matched_row.get("offset", _stimulus_value_for_field(manifest, "addr", idx, goal)))
        else:
            addr = stimulus.get("addr_or_name", stimulus.get("addr", _stimulus_value_for_field(manifest, "addr", idx, goal)))
        stimulus.setdefault("addr", addr)
        generic_register_goal = goal_kind == "register" or _norm_token(tx_type) in {
            "csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr",
        }
        if generic_register_goal:
            stimulus.setdefault("reg", addr)
            stimulus.setdefault("addr_or_name", addr)
        data = stimulus.get("data", stimulus.get("value", _stimulus_value_for_field(manifest, "data", idx, goal)))
        stimulus.setdefault("data", data)
        stimulus.setdefault("value", data)
        input_ports = set(manifest.get("input_ports") or [])
        stimulus["op"] = op_norm
        if "psel" in input_ports:
            stimulus["psel"] = 1
        if "penable" in input_ports:
            stimulus["penable"] = 1
        if "pwrite" in input_ports:
            stimulus["pwrite"] = 0 if op_norm == "read" else 1
        if "paddr" in input_ports:
            stimulus["paddr"] = addr
        if "pwdata" in input_ports:
            stimulus.setdefault("pwdata", data)
        if "pstrb" in input_ports:
            stimulus["pstrb"] = (1 << _port_width(manifest, "pstrb")) - 1
    elif any(token in goal_text for token in ("error_handling", "error source", "invalid address", "unmapped", "addr_valid == 0")):
        input_ports = set(manifest.get("input_ports") or [])
        if {"psel", "penable", "paddr"}.issubset(input_ports):
            rows = _register_rows(manifest)
            max_offset = max([int(row.get("offset", 0)) for row in rows] or [0])
            stimulus["op"] = _infer_access_op(goal, tx_type)
            stimulus["psel"] = 1
            stimulus["penable"] = 1
            if "pwrite" in input_ports:
                stimulus["pwrite"] = 1 if stimulus["op"] == "write" else 0
            stimulus["paddr"] = max_offset + 4
            if "pwdata" in input_ports:
                stimulus.setdefault("pwdata", _stimulus_value_for_field(manifest, "pwdata", idx, goal))
            if "pstrb" in input_ports:
                stimulus["pstrb"] = (1 << _port_width(manifest, "pstrb")) - 1
    if goal_kind == "memory" or "memory_access" in tx_type_norm:
        stimulus.setdefault("op", _stimulus_value_for_field(manifest, "op", idx, goal))
        stimulus.setdefault("addr", _stimulus_value_for_field(manifest, "addr", idx, goal))
        data = stimulus.get("data", stimulus.get("value", _stimulus_value_for_field(manifest, "data", idx, goal)))
        stimulus.setdefault("data", data)
        stimulus.setdefault("value", data)
    _set_sample_activity(stimulus, manifest, sample_active)
    return stimulus


def _goal_wait_cycles(goal: dict[str, Any], manifest: dict[str, Any]) -> int:
    base = max(int(manifest.get("latency_cycles") or 1), 1)
    text = _goal_text(goal)
    if any(token in text for token in ("stall_mem", "load/store", "load store", "d_hresp", "d_hready")):
        return max(base, 3)
    if any(token in text for token in ("bus_error", "bus error", "fault_halt", "fault halt")):
        return max(base, 3)
    return base


def _idle_input_value(manifest: dict[str, Any], port: str) -> int:
    input_map = manifest.get("input_map") or {}
    for field, mapped_port in input_map.items():
        if str(mapped_port) == str(port):
            return _fit_port_value(manifest, str(port), _stimulus_value_for_field(manifest, str(field), 0, {}))
    return _fit_port_value(manifest, str(port), _default_field_value(str(port), 0))


async def _reset_dut(dut, manifest: dict[str, Any], *, release: bool = True) -> None:
    input_ports = set(manifest.get("input_ports") or [])
    inout_ports = _inout_ports(manifest)
    clock = manifest["clock"]
    reset = manifest["reset"]
    active = 0 if manifest.get("reset_active") == "low" else 1
    inactive = 1 - active
    for port in input_ports:
        if port == clock:
            continue
        if port in inout_ports and port != reset:
            _set_signal(dut, port, _highz_value(manifest, port))
            continue
        _set_signal(dut, port, active if port == reset else _idle_input_value(manifest, str(port)))
    await ClockCycles(getattr(dut, clock), 3)
    if not release:
        return
    _set_signal(dut, reset, inactive)


def _drive_inputs(dut, manifest: dict[str, Any], stimulus: dict[str, Any]) -> None:
    clock = manifest["clock"]
    reset = manifest["reset"]
    input_map = manifest.get("input_map") or {}
    inout_ports = _inout_ports(manifest)
    driven = {clock, reset}
    for field, port in input_map.items():
        if port in {clock, reset}:
            continue
        if port in inout_ports and not _should_drive_inout_port(manifest, stimulus, str(port)):
            _set_signal(dut, port, _highz_value(manifest, str(port)))
            driven.add(port)
            continue
        _set_signal(dut, port, _fit_port_value(manifest, port, int(stimulus.get(field, 0))))
        driven.add(port)
    sample_active = bool(stimulus.get("_sample_active", True))
    for port in manifest.get("sample_inputs") or []:
        raw = int(stimulus.get(port, 1 if sample_active else 0))
        if _port_width(manifest, port) == 1:
            value = 1 if raw else 0
        else:
            value = _fit_port_value(manifest, port, raw)
        _set_signal(dut, port, value)
        driven.add(port)
    input_ports = set(manifest.get("input_ports") or [])
    kind_text = " ".join(str(stimulus.get(k, "")) for k in ("kind", "op", "scenario_id")).lower()
    is_csr = any(token in kind_text for token in ("csr", "register", "control_status", "apb")) or "addr_or_name" in stimulus or "reg" in stimulus
    if is_csr and {"psel", "penable"}.issubset(input_ports):
        op = str(stimulus.get("op") or "").lower()
        addr = stimulus.get("addr", stimulus.get("addr_or_name", stimulus.get("reg", 0)))
        data = stimulus.get("data", stimulus.get("value", 0))
        _set_signal(dut, "psel", 1); driven.add("psel")
        _set_signal(dut, "penable", 1); driven.add("penable")
        if "pwrite" in input_ports:
            _set_signal(dut, "pwrite", 1 if "write" in op or op in {"wr", "csr_write"} else 0); driven.add("pwrite")
        if "paddr" in input_ports:
            _set_signal(dut, "paddr", _fit_port_value(manifest, "paddr", int(addr))); driven.add("paddr")
        if "pwdata" in input_ports:
            _set_signal(dut, "pwdata", _fit_port_value(manifest, "pwdata", int(data))); driven.add("pwdata")
        if "pstrb" in input_ports:
            _set_signal(dut, "pstrb", (1 << _port_width(manifest, "pstrb")) - 1); driven.add("pstrb")
    for port in manifest.get("input_ports") or []:
        if port not in driven:
            if port in inout_ports and port != reset:
                _set_signal(dut, port, _highz_value(manifest, str(port)))
            else:
                _set_signal(dut, port, _idle_input_value(manifest, str(port)))


def _clear_sample_inputs(dut, manifest: dict[str, Any]) -> None:
    inout_ports = _inout_ports(manifest)
    for port in manifest.get("sample_inputs") or []:
        if port in inout_ports:
            _set_signal(dut, port, _highz_value(manifest, str(port)))
        else:
            _set_signal(dut, port, 0)
    for port in (manifest.get("input_map") or {}).values():
        if port not in {manifest["clock"], manifest["reset"]}:
            if port in inout_ports:
                _set_signal(dut, str(port), _highz_value(manifest, str(port)))
            else:
                _set_signal(dut, str(port), _idle_input_value(manifest, str(port)))
    for port in ("psel", "penable", "pwrite", "paddr", "pwdata", "pstrb"):
        if port in set(manifest.get("input_ports") or []):
            _set_signal(dut, port, 0)


def _sweep_values_for_port(manifest: dict[str, Any], port: str) -> list[int]:
    width = _port_width(manifest, port)
    mask = (1 << width) - 1
    a5 = int("a5" * max((width + 7) // 8, 1), 16) & mask
    values = [0, mask, 1 & mask, (mask ^ 1) & mask, a5, (~a5) & mask]
    if width > 1:
        values.append(1 << (width - 1))
    out: list[int] = []
    for value in values:
        value = int(value) & mask
        if value not in out:
            out.append(value)
    return out


def _apb_sweep_vectors(manifest: dict[str, Any]) -> list[dict[str, int]]:
    input_ports = set(manifest.get("input_ports") or [])
    if not {"psel", "penable", "paddr"}.issubset(input_ports):
        return []
    rows = _register_rows(manifest)
    offsets = [int(row.get("offset", 0)) for row in rows] or [0]
    illegal_offset = max(offsets) + 4
    addrs = offsets + [illegal_offset]
    pstrb_values = [1]
    if "pstrb" in input_ports:
        strobe_mask = (1 << _port_width(manifest, "pstrb")) - 1
        if _port_width(manifest, "pstrb") <= 4:
            pstrb_values = list(range(strobe_mask + 1))
        else:
            pstrb_values = [1 & strobe_mask, 2 & strobe_mask, strobe_mask]
    data_values = _sweep_values_for_port(manifest, "pwdata") if "pwdata" in input_ports else [0]
    vectors: list[dict[str, int]] = []
    for addr in addrs:
        for write in ([0, 1] if "pwrite" in input_ports else [0]):
            strobes = pstrb_values
            for strobe in strobes:
                data = data_values[(len(vectors) + addr + write + strobe) % len(data_values)]
                vectors.append({"addr": addr, "write": write, "data": data, "pstrb": strobe})
    return vectors


async def _drive_apb_sweep_access(dut, manifest: dict[str, Any], vector: dict[str, int]) -> None:
    clock = manifest["clock"]
    input_ports = set(manifest.get("input_ports") or [])
    await FallingEdge(getattr(dut, clock))
    _set_signal(dut, "psel", 1)
    _set_signal(dut, "penable", 0)
    _set_signal(dut, "paddr", _fit_port_value(manifest, "paddr", vector["addr"]))
    if "pwrite" in input_ports:
        _set_signal(dut, "pwrite", vector["write"])
    if "pwdata" in input_ports:
        _set_signal(dut, "pwdata", _fit_port_value(manifest, "pwdata", vector["data"]))
    if "pstrb" in input_ports:
        _set_signal(dut, "pstrb", _fit_port_value(manifest, "pstrb", vector["pstrb"]))
    await RisingEdge(getattr(dut, clock))
    await FallingEdge(getattr(dut, clock))
    _set_signal(dut, "penable", 1)
    await RisingEdge(getattr(dut, clock))
    await FallingEdge(getattr(dut, clock))
    _set_signal(dut, "psel", 0)
    _set_signal(dut, "penable", 0)
    if "pwrite" in input_ports:
        _set_signal(dut, "pwrite", 0)


async def _run_static_coverage_sweep(dut, manifest: dict[str, Any]) -> None:
    """Exercise generic input/code paths after scoreboard signoff.

    The equivalence scoreboard remains the functional authority. This sweep is
    only for reusable Verilator line/branch/toggle evidence and intentionally
    avoids writing scoreboard rows.
    """
    clock = manifest["clock"]
    reset = manifest["reset"]
    inout_ports = _inout_ports(manifest)
    input_ports = [
        str(port)
        for port in manifest.get("input_ports") or []
        if str(port) not in {clock, reset} and str(port) not in inout_ports
    ]
    for port in input_ports:
        if port in {"psel", "penable"}:
            continue
        for value in _sweep_values_for_port(manifest, port)[:6]:
            await FallingEdge(getattr(dut, clock))
            _set_signal(dut, port, _fit_port_value(manifest, port, value))
            await RisingEdge(getattr(dut, clock))
    for idx, vector in enumerate(_apb_sweep_vectors(manifest)[:512]):
        if "gpio_in" in input_ports:
            gpio_values = _sweep_values_for_port(manifest, "gpio_in")
            _set_signal(dut, "gpio_in", gpio_values[idx % len(gpio_values)])
        await _drive_apb_sweep_access(dut, manifest, vector)
    await FallingEdge(getattr(dut, clock))
    _clear_sample_inputs(dut, manifest)


def _observe_outputs(dut, manifest: dict[str, Any], stimulus: dict[str, Any] | None = None) -> dict[str, Any]:
    observed = {}
    for item in manifest.get("outputs") or []:
        observed[str(item["name"])] = _get_signal(dut, str(item["port"]))
    for _kind, port in (manifest.get("special_outputs") or {}).items():
        observed[str(port)] = _get_signal(dut, str(port))
    aliases = manifest.get("state_observable_aliases") if isinstance(manifest.get("state_observable_aliases"), dict) else {}
    for name in manifest.get("state_observables") or []:
        if _has_signal(dut, str(name)):
            observed[str(name)] = _get_signal(dut, str(name))
            continue
        for alias in aliases.get(str(name), []) or []:
            if not _has_signal(dut, str(alias)):
                continue
            value = _get_signal(dut, str(alias))
            observed[str(name)] = value
            observed[str(alias)] = value
            break
    return observed


def _is_reset_stimulus(stimulus: dict[str, Any]) -> bool:
    text = " ".join(str(stimulus.get(k, "")) for k in ("kind", "scenario_id")).lower()
    return "reset" in text


@cocotb.test()
async def fl_rtl_equivalence_goals(dut):
    manifest = _load_manifest()
    ip_dir = _ip_dir()
    ip = manifest["ip"]
    clock = manifest["clock"]
    cocotb.start_soon(Clock(getattr(dut, clock), 10, units="ns").start())
    await _reset_dut(dut, manifest)

    from scoreboard import GoalScoreboard
    from tb_coverage import FunctionalCoverageCollector

    scoreboard = GoalScoreboard("scoreboard", ip, _project_root())
    coverage = FunctionalCoverageCollector("coverage")
    goals = _goals(ip_dir)
    assert goals, "equivalence_goals.json must contain unblocked goals"

    for idx, goal in enumerate(goals):
        goal_id = str(goal["goal_id"])
        stimulus = _stimulus_for_goal(goal, manifest, idx)
        if _is_reset_stimulus(stimulus):
            await _reset_dut(dut, manifest, release=False)
        else:
            await _reset_dut(dut, manifest)
            await FallingEdge(getattr(dut, clock))
            _drive_inputs(dut, manifest, stimulus)
            for _ in range(_goal_wait_cycles(goal, manifest)):
                await RisingEdge(getattr(dut, clock))
        await ReadOnly()
        observed = _observe_outputs(dut, manifest, stimulus)
        row = scoreboard.check_goal(
            goal_id,
            scenario_id=stimulus["scenario_id"],
            cycle=idx + _goal_wait_cycles(goal, manifest),
            stimulus=stimulus,
            rtl_observed=observed,
        )
        coverage.sample(goal, row)
        await FallingEdge(getattr(dut, clock))
        _clear_sample_inputs(dut, manifest)

    scoreboard.final_check()
    await _run_static_coverage_sweep(dut, manifest)
    coverage.write(ip_dir)
