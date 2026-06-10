#!/usr/bin/env python3
"""Headless ATLAS workflow runner for LLM-contract TDD.

The Web UI is a control surface; the workflow truth is the artifact contract
and the validators under workflow/.  This runner lets tests drive the same
stage scripts directly while swapping fake, cached, or real LLM providers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import yaml

try:
    from src.workflow_stage_engine import WorkflowStageEngine, StageEngineResult
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from workflow_stage_engine import WorkflowStageEngine, StageEngineResult


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class WorkerSessionRoutingError(RuntimeError):
    """A headless worker in session mode could not resolve its session.

    Surfaced (plan §2.10 / R16) instead of the old silent ``try/except: pass``
    that let a worker write ``session_id=''`` rows — those are unroutable and
    silently swallowed, so token/cost accounting for that worker vanished. In
    session mode we FAIL LOUD rather than mis-attribute spend.
    """


def _resolve_worker_session_id() -> str:
    """Resolve the worker's session id from the spawn env (plan §2.10 / R16).

    ``SessionProcessManager.build_worker_env`` sets ``ATLAS_ACTIVE_SESSION``
    (owner/ip/workflow), NOT ``ATLAS_SESSION_ID`` — so the old code that read
    ``ATLAS_SESSION_ID`` always saw '' and wrote unroutable rows. Resolution
    order: ATLAS_ACTIVE_SESSION (the real spawn key) -> ATLAS_SESSION_ID
    (legacy fallback for any caller that still sets it).
    """
    return (
        os.environ.get("ATLAS_ACTIVE_SESSION", "").strip()
        or os.environ.get("ATLAS_SESSION_ID", "").strip()
    )


def _resolve_worker_accounting_session(*, require_in_session_mode: bool = True) -> str:
    """Resolve the session id for a worker accounting write, surfacing failure.

    In ``ATLAS_RUNTIME_DB_MODE=session`` a worker with no resolvable session is
    a routing BUG (the spawn env should always carry ATLAS_ACTIVE_SESSION): we
    raise :class:`WorkerSessionRoutingError` instead of silently writing
    ``session_id=''`` (R16). In central mode (the default) an empty session is
    historically valid, so we return '' unchanged.
    """
    session_id = _resolve_worker_session_id()
    if session_id:
        return session_id
    mode = (os.environ.get("ATLAS_RUNTIME_DB_MODE") or "central").strip().lower()
    if require_in_session_mode and mode == "session":
        raise WorkerSessionRoutingError(
            "headless worker in ATLAS_RUNTIME_DB_MODE=session has no resolvable "
            "session (ATLAS_ACTIVE_SESSION / ATLAS_SESSION_ID both empty); "
            "refusing to write an unroutable session_id='' llm_calls row."
        )
    return session_id


def _resolve_workflow_root(raw: str | Path | None = None) -> Path:
    value = str(raw or os.environ.get("ATLAS_WORKFLOW_ROOT") or "").strip()
    base = Path(os.path.expandvars(value)).expanduser() if value else SOURCE_ROOT / "workflow"
    if not base.is_absolute():
        base = SOURCE_ROOT / base
    if (base / "ssot-gen").is_dir():
        return base.resolve()
    if (base / "workflow" / "ssot-gen").is_dir():
        return (base / "workflow").resolve()
    return base.resolve()


WORKFLOW_ROOT = _resolve_workflow_root()
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|FIXME|PLACEHOLDER|STUB|MOCK)\b", re.IGNORECASE)
SSOT_REQUIRED_KEYS = [
    "top_module",
    "sub_modules",
    "parameters",
    "io_list",
    "features",
    "dataflow",
    "function_model",
    "cycle_model",
    "clock_reset_domains",
    "cdc_requirements",
    "rdc_requirements",
    "registers",
    "memory",
    "interrupts",
    "fsm",
    "timing",
    "power",
    "security",
    "error_handling",
    "debug_observability",
    "integration",
    "dft",
    "synthesis",
    "pnr",
    "coding_rules",
    "reuse_modules",
    "custom",
    "dir_structure",
    "filelist",
    "rtl_contract",
    "test_requirements",
    "quality_gates",
    "traceability",
    "workflow_todos",
    "generation_flow",
]
SSOT_REQUIRED_KEYS_BY_RUN_MODE = {
    "starter": [
        "top_module",
        "io_list",
        "function_model",
    ],
    "engineering": [
        key for key in SSOT_REQUIRED_KEYS if key not in {"dft", "pnr"}
    ],
    "signoff": SSOT_REQUIRED_KEYS,
}
DEFAULT_RTL_PACKET_MAX_PER_PASS = 4
REFERENCE_PROFILE_PROMPT_KEYS = (
    "path",
    "label",
    "summary",
    "target_candidate_basis",
    "target_candidate_summary",
    "suggested_ssot_target_scale",
    "guidance",
)
HEADLESS_STAGE_ALIASES = {
    "req-contracts": "req-contracts",
    "req-lock": "req-contracts",
    "draft-req": "req-contracts",
    "finalize-req": "req-contracts",
    "ssot": "ssot-gen",
    "ssot-gen": "ssot-gen",
    "fl-model": "fl-model-gen",
    "fl-model-gen": "fl-model-gen",
    "ssot-fl-model": "fl-model-gen",
    "cl-model": "cl-model-gen",
    "cycle-model": "cl-model-gen",
    "ssot-cycle-model": "cl-model-gen",
    "dual-fcov": "dual-fcov",
    "ssot-dual-fcov": "dual-fcov",
    "equiv-goals": "equiv-goals",
    "ssot-equiv-goals": "equiv-goals",
    "rtl": "rtl-gen",
    "gen-rtl": "rtl-gen",
    "rtl-gen": "rtl-gen",
    "ssot-rtl": "rtl-gen",
    "lint": "lint",
    "tb": "tb-gen",
    "tb-gen": "tb-gen",
    "ssot-tb-cocotb": "tb-gen",
    "coverage": "coverage",
    "cov": "coverage",
    "sim": "sim",
    "sim-debug": "sim-debug",
    "contract": "contract-check",
    "contract-check": "contract-check",
    "goal-audit": "goal-audit",
    "pipeline": "pipeline",
    "pipelining": "pipeline",
    "repair-pipeline": "pipeline",
}


def _normalize_run_mode(value: Any) -> str:
    mode = str(value or "").strip().lower().replace("_", "-")
    if mode == "eng":
        mode = "engineering"
    if mode == "sign-off":
        mode = "signoff"
    return mode if mode in SSOT_REQUIRED_KEYS_BY_RUN_MODE else "signoff"


def _ssot_required_keys_for_mode(run_mode: str) -> list[str]:
    return list(SSOT_REQUIRED_KEYS_BY_RUN_MODE.get(_normalize_run_mode(run_mode), SSOT_REQUIRED_KEYS))

PIPELINE_DEFAULT_STAGES = [
    "fl-model-gen",
    "cl-model-gen",
    "dual-fcov",
    "equiv-goals",
    "rtl-gen",
    "lint",
    "tb-gen",
    "sim",
    "coverage",
    "sim-debug",
    "contract-check",
    "goal-audit",
]


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canonical_headless_stage(stage: str) -> str:
    return HEADLESS_STAGE_ALIASES.get(stage, stage)


def _sha(text: str | bytes) -> str:
    if isinstance(text, str):
        text = text.encode("utf-8")
    return hashlib.sha256(text).hexdigest()


RTL_TODO_HASH_VOLATILE_KEYS = {
    "connection_contract_suggestions",
    "contract_implementation_evidence",
    "generated_at",
    "gate",
    "manifest_hierarchy_evidence",
    "manifest_signal_flow_evidence",
    "owner_logic_evidence",
    "reference_profile",
    "reference_scale_gap",
    "rtl_implementation_depth_evidence",
    "rtl_placeholder_free_evidence",
    "static_evidence",
    "static_rtl_evidence",
    "todo_completion",
    "top_input_consumption_evidence",
    "top_io_contract_evidence",
    "top_output_drive_evidence",
}


def _stable_json_sha256(path: Path, *, volatile_keys: set[str] | None = None) -> str:
    volatile_keys = volatile_keys or RTL_TODO_HASH_VOLATILE_KEYS
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): normalize(item)
                for key, item in value.items()
                if str(key) not in volatile_keys
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    payload = json.dumps(normalize(data), sort_keys=True, separators=(",", ":"))
    return _sha(payload)


def _safe_name(value: str, fallback: str = "ip") -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_")
    if not text or not re.match(r"^[A-Za-z]", text):
        text = fallback
    return text


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, sort_keys=True) + "\n")


def _clip(text: str, limit: int = 12000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... <truncated {len(text) - limit} chars>"


_UNUSED_SIGNAL_BITS_RE = re.compile(r"'(?P<signal>[A-Za-z_][A-Za-z0-9_$]*)'\[(?P<bits>[^\]]+)\]")
_UNUSED_SIGNAL_NAME_RE = re.compile(
    r"(?:'(?P<quoted>[A-Za-z_][A-Za-z0-9_$]*)'|:\s*(?P<plain>[A-Za-z_][A-Za-z0-9_$]*)|Signal is not used:\s*(?P<bare>[A-Za-z_][A-Za-z0-9_$]*))"
)
_WIDTH_PORT_RE = re.compile(
    r"(?:Input|Output|Inout)?\s*port connection\s+'(?P<port>[A-Za-z_][A-Za-z0-9_$]*)'.*?"
    r"expects\s+(?P<expected>\d+)\s+bits.*?"
    r"connection(?:'s)?(?:\s+VARREF\s+'(?P<signal>[A-Za-z_][A-Za-z0-9_$]*)')?.*?"
    r"generates\s+(?P<actual>\d+)\s+bits",
    flags=re.I,
)
_WIDTH_CONVERSION_RE = re.compile(
    r"implicit conversion of port connection (?:truncates|expands) from (?P<from>\d+) to (?P<to>\d+) bits",
    flags=re.I,
)


def _looks_like_static_evidence_marker_signal(signal: str) -> bool:
    lower = str(signal or "").lower()
    if not lower:
        return False
    if lower.startswith("every_") or (lower.startswith("no_") and lower.endswith("_generated")):
        return True
    if "function_model" in lower or "cycle_model" in lower:
        return True
    if lower.endswith("_mapping") and any(token in lower for token in ("fm_", "transaction", "stage")):
        return True
    return False


def _rtl_lint_repair_hints(diagnostics: list[Any]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for diag in diagnostics:
        if not isinstance(diag, dict):
            continue
        rule = str(diag.get("rule") or "").upper()
        message = str(diag.get("message") or "")
        source = str(diag.get("source") or "")
        width_match = _WIDTH_PORT_RE.search(message)
        conversion_match = _WIDTH_CONVERSION_RE.search(message)
        if rule in {"WIDTHEXPAND", "WIDTHTRUNC", "WIDTH"} or width_match or conversion_match:
            port = width_match.group("port") if width_match else ""
            signal = width_match.group("signal") if width_match else ""
            expected = width_match.group("expected") if width_match else (conversion_match.group("from") if conversion_match else "")
            actual = width_match.group("actual") if width_match else (conversion_match.group("to") if conversion_match else "")
            preferred_fix = (
                "Repair the connected producer/consumer contract, not the lint policy. The instance "
                "port width and connected signal width must match after repair. If a GPIO-only value "
                "is intentionally narrower, update the child module port declaration and every named "
                "instance connection for that port in the same artifact set. If the child port is a "
                "full DATA_WIDTH CSR/readback word, keep the connected top signal DATA_WIDTH and consume "
                "the full word through real readback/checking behavior instead of attaching a narrower copy."
            )
            hints.append(
                {
                    "rule": rule or "WIDTH",
                    "file": diag.get("file"),
                    "line": diag.get("line"),
                    "signal": signal or port or "<port-connection>",
                    "port": port,
                    "expected_bits": expected,
                    "actual_bits": actual,
                    "source": source,
                    "preferred_fix": preferred_fix,
                    "mechanical_fix": (
                        "Align both sides of the named port connection in one edit: producer module port "
                        "declaration, internal assignment width, parent instance signal declaration, and "
                        "the named .port(signal) connection must agree."
                    ),
                    "completion_condition": (
                        "The same port-width diagnostic must disappear after lint/compile reruns. A repair "
                        "that only changes the top-side signal width while the child port still expects the "
                        "old width is incomplete."
                    ),
                    "forbidden_fixes": [
                        "Do not suppress width warnings.",
                        "Do not leave one side of an instance port at the old width.",
                        "Do not add casts or padding unless the SSOT requires the wider value and the padded bits are functionally consumed.",
                    ],
                }
            )
        elif rule == "UNUSEDSIGNAL" and "Bits of signal are not used" in message:
            bit_match = _UNUSED_SIGNAL_BITS_RE.search(message)
            signal = bit_match.group("signal") if bit_match else ""
            bits = bit_match.group("bits") if bit_match else ""
            source_lower = source.lower()
            is_public_input = bool(re.search(r"\binput\b", source_lower))
            mechanical_fix = ""
            completion_condition = ""
            if is_public_input:
                preferred_fix = (
                    "Do not narrow an externally defined bus port just to satisfy lint. If the "
                    "unused bits are upper byte lanes of a public bus input, follow the SSOT "
                    "bus/byte-lane policy embedded in the prompt. Only assert a bus error when "
                    "that policy explicitly declares an illegal byte-access condition; otherwise "
                    "consume the upper lanes through explicit legal ignore, byte-strobe masking, "
                    "reserved-zero readback, or coverage/trace behavior."
                )
            elif "byte_mask" in signal or signal.endswith("_32"):
                preferred_fix = (
                    "Repair the RTL shape, not the lint policy. Build helper masks at the "
                    "actual consumed parameter width, or consume the full-width mask through "
                    "real byte-lane legality/readback behavior. Do not create a 32-bit helper "
                    "only to slice away unused upper bits."
                )
            elif (
                re.search(r"\blogic\s*\[\s*DATA_WIDTH\s*-\s*1\s*:\s*0\s*\]", source)
                and re.search(r"^[0-9]+\s*:\s*[0-9]+$", bits)
            ):
                preferred_fix = (
                    "Repair the RTL shape, not the lint policy. This is an internal DATA_WIDTH "
                    "helper whose upper bits are not consumed. Narrow the helper to the actual "
                    "consumer width, usually [GPIO_WIDTH-1:0] for GPIO output/enable paths, and "
                    "only widen at a CSR/readback boundary that consumes every DATA_WIDTH bit. "
                    "When a full DATA_WIDTH producer feeds a narrower GPIO/output consumer, delete "
                    "the reported full-width helper and drive the narrower consumer directly from "
                    "producer[GPIO_WIDTH-1:0] or through a GPIO_WIDTH helper."
                )
                mechanical_fix = (
                    "Change the internal helper declaration from logic [DATA_WIDTH-1:0] to the "
                    "actual consumed parameter width (for GPIO path helpers, logic [GPIO_WIDTH-1:0]) "
                    "and update assignments/consumers so no upper slice is left unused. If the helper "
                    "is driven by a child module output, narrow that child output port and the instance "
                    "connection in the same artifact set, unless the full DATA_WIDTH value is consumed "
                    "by real CSR/readback/checking behavior. Do not replace the reported signal with "
                    "another DATA_WIDTH masked/full helper; that repeats the same lint failure."
                )
                completion_condition = (
                    f"The reported signal {signal} itself must no longer appear in an UNUSED upper-bit "
                    "diagnostic after lint reruns. Adding a second narrower copy while leaving this "
                    "DATA_WIDTH signal with unused upper bits is not a valid repair. Introducing a new "
                    "logic [DATA_WIDTH-1:0] *_masked_full or *_full helper whose upper bits are unused "
                    "is also not a valid repair."
                )
            else:
                preferred_fix = (
                    "Repair the RTL shape, not the lint policy. If this is a helper word whose "
                    "upper bits are outside the IP parameter width, narrow the helper to the "
                    "actual consumed width and widen only at the CSR/readback boundary. If the "
                    "full vector is semantically required, drive and consume every bit through "
                    "real functional logic."
                )
            hints.append(
                {
                    "rule": rule,
                    "file": diag.get("file"),
                    "line": diag.get("line"),
                    "signal": signal,
                    "unused_bits": bits,
                    "source": source,
                    "preferred_fix": preferred_fix,
                    "mechanical_fix": mechanical_fix,
                    "completion_condition": completion_condition,
                    "forbidden_fixes": [
                        "Do not add marker-only reduction wires just to consume unused bits.",
                        "Do not keep the reported DATA_WIDTH diagnostic signal unchanged while adding a narrower copy.",
                        "Do not replace the reported signal with a differently named DATA_WIDTH masked/full helper.",
                        "Do not add Verilator lint_off/lint_on or -Wno suppressions.",
                        "Do not leave evidence-only helper signals that are not used by real behavior.",
                    ],
                }
            )
        elif rule in {"UNUSEDSIGNAL", "UNUSEDPARAM", "UNUSED"}:
            name_match = _UNUSED_SIGNAL_NAME_RE.search(message)
            signal = ""
            if name_match:
                signal = name_match.group("quoted") or name_match.group("plain") or name_match.group("bare") or ""
            if _looks_like_static_evidence_marker_signal(signal):
                preferred_fix = (
                    "This looks like a static-evidence marker signal, not required RTL behavior. "
                    "Do not keep standalone declarations just to spell a TODO/evidence term. "
                    "Remove the marker and implement the underlying SSOT behavior with real "
                    "protocol, datapath, state, or control signals that are consumed by outputs, "
                    "state updates, assertions, or observable trace/coverage."
                )
            else:
                preferred_fix = (
                    "Remove the unused declaration when it is evidence-only, or connect it into "
                    "real datapath/control/observable behavior when the SSOT requires it."
                )
            hints.append(
                {
                    "rule": rule,
                    "file": diag.get("file"),
                    "line": diag.get("line"),
                    "signal": signal,
                    "source": source,
                    "preferred_fix": preferred_fix,
                    "forbidden_fixes": [
                        "Do not add marker-only consumption logic.",
                        "Do not declare signals whose only purpose is to match static evidence terms.",
                        "Do not suppress the warning.",
                    ],
                }
            )
    return hints


def _format_rtl_lint_repair_hints(hints: list[Any]) -> str:
    if not hints:
        return "<none>"
    lines: list[str] = []
    for hint in hints[:24]:
        if not isinstance(hint, dict):
            continue
        loc = f"{hint.get('file') or '<unknown>'}:{hint.get('line') or '?'}"
        signal = hint.get("signal") or "<unknown>"
        unused_bits = hint.get("unused_bits")
        bit_text = f" unused_bits={unused_bits}" if unused_bits else ""
        lines.append(f"- {hint.get('rule') or '<rule>'} {loc} signal={signal}{bit_text}")
        preferred = str(hint.get("preferred_fix") or "").strip()
        if preferred:
            lines.append(f"  preferred_fix: {preferred}")
        mechanical = str(hint.get("mechanical_fix") or "").strip()
        if mechanical:
            lines.append(f"  mechanical_fix: {mechanical}")
        completion = str(hint.get("completion_condition") or "").strip()
        if completion:
            lines.append(f"  completion_condition: {completion}")
        forbidden = hint.get("forbidden_fixes")
        if isinstance(forbidden, list) and forbidden:
            lines.append("  forbidden_fixes: " + "; ".join(str(item) for item in forbidden if item))
    return "\n".join(lines) if lines else "<none>"


def _ssot_bus_lane_policy(ssot_doc: dict[str, Any]) -> dict[str, Any]:
    error_handling = ssot_doc.get("error_handling") if isinstance(ssot_doc.get("error_handling"), dict) else {}
    error_sources = error_handling.get("error_sources") if isinstance(error_handling.get("error_sources"), list) else []
    byte_policy: dict[str, Any] = {}
    for source in error_sources:
        if isinstance(source, dict) and str(source.get("id") or "") == "illegal_byte_access_pattern":
            byte_policy = source
            break
    condition = str(byte_policy.get("condition") or "").strip().lower()
    no_illegal_byte_access = condition in {"", "none", "n/a", "na", "false", "0"}
    return {
        "illegal_byte_access_pattern_condition": byte_policy.get("condition") if byte_policy else "<not declared>",
        "upper_byte_lane_error_allowed": not no_illegal_byte_access,
        "guidance": (
            "condition=none means upper byte lanes are not an APB error for legal offsets; "
            "consume otherwise-unused pwdata/pstrb upper bits through explicit legal ignore, "
            "byte-strobe masking, reserved-zero readback, or coverage/trace behavior while keeping "
            "pslverr deasserted for legal writes."
            if no_illegal_byte_access
            else "Only assert byte-lane pslverr for the declared illegal_byte_access_pattern condition; do not invent stricter bus policy."
        ),
    }


@dataclass
class LLMResponse:
    stage: str
    model: str
    raw_response: str
    parsed_artifacts: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    finish_reason: str = ""
    error: str = ""
    status: str = "pass"

    def to_log(
        self,
        *,
        prompt: str,
        context: dict[str, Any],
        started_at: str,
        finished_at: str,
    ) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "model": self.model,
            "prompt_hash": _sha(prompt),
            "input_hash": _sha(json.dumps(context, sort_keys=True)),
            "output_hash": _sha(self.raw_response),
            "started_at": started_at,
            "finished_at": finished_at,
            "status": self.status,
            "raw_response": self.raw_response,
            "parsed_artifacts": self.parsed_artifacts,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "error": self.error,
        }


class LLMProvider(Protocol):
    def complete(
        self,
        *,
        stage: str,
        model: str,
        system_prompt: str,
        prompt: str,
        context: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        ...


def _structured_ssot_yaml(ip: str, requirement_text: str) -> str:
    excerpt = " ".join(requirement_text.split())[:240]
    doc = {
        "top_module": {
            "name": ip,
            "file": f"rtl/{ip}.sv",
            "description": f"{ip} top-level wrapper for the sampled transaction rule.",
        },
        "sub_modules": [
            {
                "name": ip,
                "file": f"rtl/{ip}.sv",
                "ownership": "manifest",
                "wiring_only": True,
                "implements": ["io_list", "integration"],
                "source_sections": ["io_list", "integration"],
                "description": "Top wrapper that connects external ports to the SSOT-owned core.",
            },
            {
                "name": f"{ip}_core",
                "file": f"rtl/{ip}_core.sv",
                "ownership": "manifest",
                "implements": ["function_model.transactions", "cycle_model", "rtl_contract"],
                "source_sections": ["function_model", "cycle_model", "rtl_contract", "fsm", "dataflow", "registers"],
                "function_model_refs": ["function_model.transactions.FM_PRIMARY", "function_model.state_variables"],
                "cycle_model_refs": ["cycle_model.pipeline"],
                "dataflow_refs": ["dataflow.sequence", "dataflow.ordering"],
                "register_refs": ["registers.architectural_state.accepted_count"],
                "fsm_refs": ["fsm.control"],
                "description": "Core RTL block implementing the sampled transaction rule.",
            }
        ],
        "parameters": [
            {"name": "DATA_WIDTH", "default": 8, "type": "int", "description": "Input data width."},
            {"name": "RESULT_WIDTH", "default": 9, "type": "int", "description": "Output result width."},
        ],
        "io_list": {
            "clock_domains": [
                {"name": "main", "ports": [{"name": "clk", "direction": "input", "width": 1}]}
            ],
            "resets": [
                {
                    "name": "rst_n",
                    "active": "low",
                    "ports": [{"name": "rst_n", "direction": "input", "width": 1}],
                }
            ],
            "interfaces": [
                {
                    "name": "rule_io",
                    "type": "custom",
                    "role": "target",
                    "clock_domain": "main",
                    "reset_domain": "rst_n",
                    "protocol": {
                        "acceptance": "A request is accepted when valid && ready is true on clk.",
                        "response": "result and result_valid are driven one cycle after the accepted request.",
                        "stability": "data_in is sampled only at acceptance; result remains traceable to that sampled value.",
                    },
                    "ports": [
                        {"name": "valid", "direction": "input", "width": 1},
                        {"name": "data_in", "direction": "input", "width": 8},
                        {"name": "result", "direction": "output", "width": 9},
                        {"name": "ready", "direction": "output", "width": 1},
                        {"name": "result_valid", "direction": "output", "width": 1},
                    ],
                }
            ],
        },
        "features": [
            {
                "name": "double_value",
                "description": "Sample data_in when valid is high and produce result=data_in*2 one cycle later.",
                "requirement_trace": excerpt,
            }
        ],
        "dataflow": {
            "sequence": [
                "Sample data_in when valid is asserted after reset release.",
                "Compute result as sampled value multiplied by two.",
                "Present result and result_valid on the next observable cycle.",
            ],
            "ordering": ["accepted request precedes result observation"],
        },
        "function_model": {
            "state_variables": [{"name": "accepted_count", "width": 8, "reset": 0}],
            "transactions": [
                {
                    "id": "FM_PRIMARY",
                    "name": "primary_behavior",
                    "required_fields": ["value"],
                    "preconditions": ["rst_n is deasserted", "valid is high"],
                    "outputs": ["result"],
                    "output_rules": [
                        {"name": "result", "port": "result", "expr": "value * 2", "width": 9}
                    ],
                    "side_effects": ["accepted_count increments on each sampled transaction"],
                    "state_updates": [
                        {"name": "accepted_count", "expr": "accepted_count + 1", "width": 8}
                    ],
                }
            ],
            "invariants": [
                "No result is produced before reset is released.",
                "Each accepted valid transaction produces exactly one result_valid observation.",
                "The result value is derived only from the sampled input transaction.",
            ],
            "reference_model_hint": "FunctionalModel.apply(value) returns result=value*2 and increments accepted_count.",
        },
        "cycle_model": {
            "executable": "python",
            "backend_policy": "Use the repo-owned pure-Python deterministic stepper; FunctionalModel remains the behavioral oracle.",
            "clock": "clk",
            "reset": "rst_n",
            "latency": 1,
            "handshake_rules": [
                {
                    "name": "valid_sample",
                    "description": "data_in is sampled only when valid is high; ready remains high after reset.",
                }
            ],
            "pipeline": [
                {"stage": "S0_SAMPLE", "cycle": 0, "action": "Sample data_in when valid is high."},
                {"stage": "S1_RESULT", "cycle": 1, "action": "Drive result and result_valid for the sampled value."},
            ],
            "ordering": [
                "Transactions are observed in the same order they are sampled.",
                "Reset clears pending valid output before any new transaction is accepted.",
            ],
            "backpressure": ["ready remains asserted in this one-deep sample rule IP."],
            "performance": {
                "frequency_mhz": 100,
                "throughput": {"sustained_beats_per_cycle": 1, "condition": "ready remains asserted"},
                "outstanding": {"max": 1, "description": "One sampled transaction at a time"},
                "depth": {"pipeline_stages": 2, "queue_depth": 1, "description": "Sample/result default cycle depth"},
            },
        },
        "clock_reset_domains": {
            "domains": [{"name": "main", "clock": "clk", "reset": "rst_n", "reset_active": "low"}],
        },
        "cdc_requirements": {"crossings": [], "rationale": "Single clock domain."},
        "rdc_requirements": {"crossings": [], "rationale": "Single reset domain."},
        "registers": {
            "no_registers": True,
            "policy": "No firmware-visible CSR/register map is required for this native valid/ready rule IP.",
            "register_list": [],
            "architectural_state": [{"name": "accepted_count", "reset": 0, "source": "function_model.state_variables"}],
        },
        "memory": {"instances": [], "rationale": "No memory required for the one-cycle datapath rule."},
        "interrupts": {"sources": [], "outputs": [], "rationale": "No interrupt behavior required for this rule IP."},
        "fsm": {
            "control": {
                "states": ["S0_SAMPLE", "S1_RESULT"],
                "reset_state": "S0_SAMPLE",
                "transitions": [
                    {"from": "S0_SAMPLE", "to": "S1_RESULT", "condition": "valid", "action": "Latch input value."},
                    {"from": "S1_RESULT", "to": "S0_SAMPLE", "condition": "next cycle", "action": "Emit result_valid."},
                ],
            }
        },
        "rtl_contract": {
            "clock": "clk",
            "reset": "rst_n",
            "reset_active": "low",
            "transaction": "FM_PRIMARY",
            "sample_condition": "valid && ready",
            "input_map": {"value": "data_in"},
            "output_map": {"result": "result", "valid": "result_valid"},
            "ready_output": "ready",
            "output_valid": "result_valid",
        },
        "timing": {
            "target_clocks": [{"name": "clk", "frequency_mhz": 100, "period_ns": 10.0}],
            "latency_budget": {"accepted_to_result_valid": {"min": 1, "max": 1, "unit": "cycles"}},
        },
        "power": {
            "domains": [{"name": "PD_MAIN", "clock_domains": ["main"], "isolation": "not_required"}],
            "power_states": [{"name": "ON", "entry": "reset deasserted", "exit": "reset asserted"}],
        },
        "security": {
            "classification": "non_secure_leaf_ip",
            "assets": [{"name": "result_integrity", "protection": "result must match function_model output rule"}],
            "threat_model": [{"threat": "silent datapath corruption", "mitigation": "FL-vs-RTL scoreboard checks every result"}],
        },
        "error_handling": {
            "error_sources": [{"id": "ERR_NONE", "condition": "No protocol error input exists", "architectural_effect": "No error output is asserted"}],
            "propagation": ["No error response interface exists for this simple rule IP."],
            "recovery": [{"action": "reset", "clears": ["accepted_count", "result_valid"]}],
        },
        "debug_observability": {
            "waveform_must_probe": ["clk", "rst_n", "valid", "data_in", "ready", "result", "result_valid", "accepted_count"],
            "trace_events": [
                {"name": "sample", "trigger": "valid && ready"},
                {"name": "result", "trigger": "result_valid"},
            ],
        },
        "integration": {
            "bus_attachment": {"type": "native_valid_ready_rule_io", "interfaces": ["rule_io"]},
            "dependencies": {"external_modules": [], "external_clocks": ["clk"], "external_resets": ["rst_n"]},
            "connections": [
                {"module": f"{ip}_core", "port": "clk", "signal": "clk"},
                {"module": f"{ip}_core", "port": "rst_n", "signal": "rst_n"},
                {"module": f"{ip}_core", "port": "valid", "signal": "valid"},
                {"module": f"{ip}_core", "port": "data_in", "signal": "data_in"},
                {"module": f"{ip}_core", "port": "ready", "signal": "ready"},
                {"module": f"{ip}_core", "port": "result", "signal": "result"},
                {"module": f"{ip}_core", "port": "result_valid", "signal": "result_valid"},
            ],
        },
        "dft": {
            "scan_required": False,
            "controllability": {"reset": "rst_n", "clock": "clk", "inputs": ["valid", "data_in"]},
            "observability": {"outputs": ["ready", "result", "result_valid"]},
        },
        "synthesis": {
            "dialect": "systemverilog_2012",
            "constraints": ["No inferred latches", "No unresolved black boxes"],
            "required_outputs": ["rtl compile log", "dut lint report", "syn/out/synth.v"],
        },
        "pnr": {
            "utilization_pct": 60,
            "aspect_ratio": 1.0,
            "core_space_um": 2.0,
            "global_density": 0.65,
            "io_layers": {"horizontal": "met3", "vertical": "met2"},
            "cts_buf_list": ["sky130_fd_sc_hd__clkbuf_4", "sky130_fd_sc_hd__clkbuf_8"],
            "routing": {"signal_layers": {"min": "met1", "max": "met5"}, "drc_waivers": []},
        },
        "coding_rules": {
            "verilog_style": "systemverilog_2012",
            "conventions": ["Use sequential flops for registered outputs", "Use combinational defaults on all paths"],
            "lint_waivers": [],
        },
        "reuse_modules": [],
        "custom": {"assumptions": ["This fixture intentionally models a tiny generic transaction rule IP."]},
        "dir_structure": {
            "yaml_dir": "yaml/",
            "rtl_dir": "rtl/",
            "tb_dir": "tb/",
            "sim_dir": "sim/",
            "cov_dir": "cov/",
            "lint_dir": "lint/",
        },
        "filelist": {
            "rtl": [f"rtl/{ip}.sv", f"rtl/{ip}_core.sv"],
            "tb": [f"tb/cocotb/test_{ip}.py"],
            "coverage": ["cov/coverage.json"],
        },
        "test_requirements": {
            "scenarios": [
                {
                    "id": "SC_RULE_DOUBLE",
                    "name": "double sampled input",
                    "stimulus": "assert valid with data_in=13 after reset",
                    "expected": "result equals FunctionalModel result and result_valid pulses",
                    "checker": "EquivalenceScoreboard compares result observable against FunctionalModel.apply",
                    "coverage": ["FCOV_RULE_DOUBLE"],
                }
            ],
            "scoreboard_checks": 3,
            "coverage_goals": {
                "function": {
                    "target_pct": 100,
                    "model": "function_model",
                    "description": "Behavioral coverage for function_model transaction results and state updates.",
                    "bins": [
                        {
                            "id": "FCOV_RULE_DOUBLE",
                            "source_ref": "function_model.transactions.RULE_DOUBLE",
                            "class": "transaction",
                            "description": "sampled data_in doubling rule observed",
                        }
                    ],
                },
                "cycle": {
                    "target_pct": 100,
                    "model": "cycle_model",
                    "description": "Cycle coverage for sample/result pipeline stages and valid/ready timing.",
                    "bins": [
                        {
                            "id": "CCOV_SAMPLE_RESULT_PIPELINE",
                            "source_ref": "cycle_model.pipeline",
                            "class": "pipeline_stage",
                            "description": "sample-to-result cycle path observed",
                        }
                    ],
                },
                "planned_bins": [
                    {
                        "id": "FCOV_RULE_DOUBLE",
                        "class": "datapath",
                        "coverage_domain": "function",
                        "source_ref": "function_model.transactions.RULE_DOUBLE",
                        "description": "sampled data_in doubling rule observed",
                    }
                ],
                "functional": "Legacy alias: coverage_goals.function and coverage_goals.cycle must both close.",
            },
        },
        "quality_gates": {
            "ssot": {"pass": "check_ssot_disk.py exits 0", "evidence": ["check_ssot_disk.py PASS"]},
            "rtl": {"pass": "RTL compiles and maps every declared port", "evidence": ["rtl_compile.json", "dut_lint.json"]},
            "dv": {"pass": "All scenarios pass with scoreboard evidence", "evidence": ["results.xml", "scoreboard_events.jsonl"]},
            "coverage": {"pass": "All planned functional bins are hit", "evidence": ["coverage.json"]},
            "eda": {"pass": "EDA checks are clean or explicitly waived", "evidence": ["lint report"]},
            "signoff": {"pass": "SSOT, RTL, lint, sim, and coverage gates pass", "evidence": ["goal audit"]},
        },
        "traceability": {
            "requirements": [f"{ip}/req/{ip}_requirements.md"],
            "llm_stage": "ssot-gen",
            "yaml_to_output": [
                {"yaml": "io_list", "output": "RTL ports and cocotb driver"},
                {"yaml": "function_model", "output": "FunctionalModel and scoreboard expected values"},
                {"yaml": "cycle_model", "output": "RTL latency and waveform checks"},
                {"yaml": "test_requirements", "output": "cocotb scenarios and coverage bins"},
            ],
        },
        "workflow_todos": {
            "rtl-gen": [
                {
                    "id": "RTL_RULE_DOUBLE",
                    "content": "Implement rule_double from the SSOT function and cycle model",
                    "detail": "Capture accepted data_in, produce result=data_in*2 at the declared cycle latency, and expose enough DUT evidence for FL-vs-RTL comparison.",
                    "criteria": [
                        "RTL updates only on the declared valid/ready acceptance event",
                        "RTL observed result equals FunctionalModel.apply for RULE_DOUBLE",
                        "DUT-only compile/lint and rtl_todo_plan audit pass after the final edit",
                    ],
                    "source_refs": ["function_model.transactions.RULE_DOUBLE", "cycle_model.pipeline"],
                    "owner_module": f"{ip}_core",
                    "owner_file": f"rtl/{ip}_core.sv",
                    "priority": "high",
                    "required": True,
                }
            ],
            "tb-gen": [],
            "sim_debug": [],
        },
        "generation_flow": {
            "steps": [
                {"name": "verify_ssot", "command": f"python3 \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py\" {ip} --root \"$ATLAS_PROJECT_ROOT\" --mode ${{ATLAS_RUN_MODE:-signoff}}", "description": "Validate SSOT structure, Preview fields, and gates at the selected Run Mode."},
                {"name": "handoff_fl_model", "command": f"/ssot-fl-model {ip}", "description": "Generate function model from SSOT."},
                {"name": "handoff_rtl", "command": f"/gen-rtl {ip}", "description": "Generate RTL from SSOT."},
                {"name": "handoff_tb", "command": f"/ssot-tb-cocotb {ip}", "description": "Generate cocotb tests from SSOT."},
            ],
        },
    }
    return yaml.safe_dump(doc, sort_keys=False)


def _json_artifact_response(stage: str, model: str, files: list[dict[str, str]]) -> LLMResponse:
    raw = json.dumps({"files": files}, indent=2)
    return LLMResponse(stage=stage, model=model, raw_response=raw, parsed_artifacts=files)


def _fake_rtl_contract(ip: str) -> str:
    doc = {
        "schema_version": 1,
        "type": "generic_ssot_rule_rtl_contract",
        "top": ip,
        "contract": {
            "top": ip,
            "transaction": "FM_PRIMARY",
            "clock": "clk",
            "reset": "rst_n",
            "reset_active": "low",
            "sample_condition": "valid && ready",
            "input_map": {"value": "data_in"},
            "outputs": [
                {
                    "name": "result",
                    "port": "result",
                    "expr": "value * 2",
                    "width": 9,
                    "source": {"name": "result", "port": "result", "expr": "value * 2", "width": 9},
                }
            ],
            "state_vars": {"accepted_count": {"width": 8, "reset": 0}},
            "state_updates": [
                {
                    "name": "accepted_count",
                    "expr": "accepted_count + 1",
                    "source": {"name": "accepted_count", "expr": "accepted_count + 1", "width": 8},
                }
            ],
            "special_outputs": {"ready_output": "ready", "output_valid": "result_valid"},
            "source": "headless fake LLM artifact for contract TDD",
        },
    }
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"


def _fake_rtl_source(ip: str) -> str:
    return f'''`default_nettype none

module {ip} (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       valid,
    input  wire [7:0] data_in,
    output wire [8:0] result,
    output wire       ready,
    output wire       result_valid
);
    wire valid_sample = valid && ready;

    {ip}_core u_core (
        .clk(clk),
        .rst_n(rst_n),
        .valid(valid),
        .data_in(data_in),
        .valid_sample(valid_sample),
        .result(result),
        .ready(ready),
        .result_valid(result_valid)
    );
endmodule

`default_nettype wire
'''


def _fake_rtl_core_source(ip: str) -> str:
    return f'''`default_nettype none

module {ip}_core (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       valid,
    input  wire [7:0] data_in,
    input  wire       valid_sample,
    output reg  [8:0] result,
    output reg        ready,
    output reg        result_valid
);
    reg [7:0] accepted_count;

    wire feature_double_value = valid;
    wire dataflow_sequence = feature_double_value;
    wire function_model_transactions_FM_PRIMARY = dataflow_sequence;
    wire cycle_model_pipeline_S0_SAMPLE = function_model_transactions_FM_PRIMARY;
    wire cycle_model_pipeline_S1_RESULT = cycle_model_pipeline_S0_SAMPLE;
    wire fsm_control_S0_SAMPLE = cycle_model_pipeline_S1_RESULT;
    wire fsm_control_S1_RESULT = fsm_control_S0_SAMPLE;
    wire coverage_FCOV_RULE_DOUBLE = fsm_control_S1_RESULT;
    wire quality_gates_rtl = coverage_FCOV_RULE_DOUBLE;
    wire workflow_todos_rtl_gen = quality_gates_rtl;
    wire ssot_evidence_keep = workflow_todos_rtl_gen;

    wire sample_condition_valid_ready = valid_sample;
    wire [8:0] function_model_result = {{1'b0, data_in}} << 1;

    always @* begin
        ready = 1'b0;
        if (rst_n) begin
            ready = 1'b1 | (ssot_evidence_keep & 1'b0);
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result <= 9'd0;
            result_valid <= 1'b0;
            accepted_count <= 8'd0;
        end else begin
            result_valid <= sample_condition_valid_ready;
            result <= function_model_result;
            if (sample_condition_valid_ready) begin
                accepted_count <= accepted_count + 8'd1;
            end
        end
    end
endmodule

`default_nettype wire
'''


def _fake_rtl_artifacts(ip: str, context: dict[str, Any]) -> list[dict[str, str]]:
    root = Path(str(context.get("root") or "."))
    todo_hash = str(context.get("rtl_todo_plan_sha256") or "").strip()
    if not todo_hash:
        todo_hash = _stable_json_sha256(root / ip / "rtl" / "rtl_todo_plan.json")
    provenance = {
        "schema_version": 1,
        "type": "rtl_authoring_provenance",
        "agent": "common_ai_agent",
        "workflow": "rtl-gen",
        "surface": "headless_common_engine",
        "todo_plan_sha256": todo_hash,
        "rtl_files": [f"rtl/{ip}.sv", f"rtl/{ip}_core.sv"],
        "contract_files": ["rtl/rtl_contract.json"],
        "generation_note": "Fake LLM provider artifact used only for headless TDD.",
    }
    return [
        {"path": f"{ip}/rtl/{ip}.sv", "content": _fake_rtl_source(ip), "kind": "rtl"},
        {"path": f"{ip}/rtl/{ip}_core.sv", "content": _fake_rtl_core_source(ip), "kind": "rtl"},
        {"path": f"{ip}/list/{ip}.f", "content": f"rtl/{ip}.sv\nrtl/{ip}_core.sv\n", "kind": "filelist"},
        {"path": f"{ip}/rtl/rtl_contract.json", "content": _fake_rtl_contract(ip), "kind": "rtl_contract"},
        {
            "path": f"{ip}/rtl/rtl_authoring_provenance.json",
            "content": json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            "kind": "rtl_authoring_provenance",
        },
    ]


class FakeLLMProvider:
    """Deterministic provider for CI and TDD red/green loops."""

    def __init__(self, scenario: str = "valid", stage_responses: dict[str, str] | None = None) -> None:
        self.scenario = scenario
        self.stage_responses = stage_responses or {}
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        *,
        stage: str,
        model: str,
        system_prompt: str,
        prompt: str,
        context: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.calls.append({"stage": stage, "model": model, "prompt_hash": _sha(prompt)})
        ip = _safe_name(str(context.get("ip") or "headless_ip"), "headless_ip")
        if stage in self.stage_responses:
            raw = self.stage_responses[stage]
            return LLMResponse(
                stage=stage,
                model=model,
                raw_response=raw,
                parsed_artifacts=parse_llm_artifacts(stage, raw, ip=ip),
            )
        if stage == "ssot-gen" and self.scenario == "human_gate":
            raw = json.dumps(
                {
                    "human_gate": {
                        "decision_needed": "Define the invalid transaction response value before SSOT can be approved.",
                        "evidence": {"requirement_refs": [f"{ip}/req/{ip}_requirements.md"]},
                        "options": [
                            {"id": "A", "description": "Return zero with error response", "impact": "RTL/TB check zero data"},
                            {"id": "B", "description": "Hold previous value with error response", "impact": "RTL/TB check retention"},
                        ],
                        "recommended_default": {"id": "A", "reason": "deterministic and easier to verify"},
                        "downstream_effect": ["function_model.transactions", "rtl_contract", "tb scoreboard"],
                    }
                },
                indent=2,
            )
            return LLMResponse(stage=stage, model=model, raw_response=raw, status="human_gate")
        if stage == "ssot-gen":
            ssot = _structured_ssot_yaml(ip, str(context.get("requirement_text") or ""))
            if self.scenario == "missing_cycle_model":
                doc = yaml.safe_load(ssot)
                doc.pop("cycle_model", None)
                ssot = yaml.safe_dump(doc, sort_keys=False)
            return _json_artifact_response(
                stage,
                model,
                [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "content": ssot, "kind": "ssot"}],
            )
        if stage == "rtl-gen":
            return _json_artifact_response(stage, model, _fake_rtl_artifacts(ip, context))
        return LLMResponse(
            stage=stage,
            model=model,
            raw_response=json.dumps({"ack": stage, "status": "ready"}, indent=2),
            parsed_artifacts=[],
        )


class CachedLLMProvider:
    """Replay raw GLM-5.1 responses from disk without a live model call."""

    def __init__(self, fixture_dir: str | Path, model: str = "glm-5.1") -> None:
        self.fixture_dir = Path(fixture_dir)
        self.model = model

    def _raw_path(self, stage: str) -> Path:
        stage_path = self.fixture_dir / stage / "raw_response.txt"
        if stage_path.is_file():
            return stage_path
        return self.fixture_dir / "raw_response.txt"

    def complete(
        self,
        *,
        stage: str,
        model: str,
        system_prompt: str,
        prompt: str,
        context: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        path = self._raw_path(stage)
        if not path.is_file():
            return LLMResponse(
                stage=stage,
                model=model,
                raw_response="",
                error=f"cached response missing: {path}",
                status="blocked",
            )
        raw = path.read_text(encoding="utf-8")
        ip = _safe_name(str(context.get("ip") or "headless_ip"), "headless_ip")
        return LLMResponse(
            stage=stage,
            model=model or self.model,
            raw_response=raw,
            parsed_artifacts=parse_llm_artifacts(stage, raw, ip=ip),
        )


class RealLLMProvider:
    """Live provider lane for the configured ATLAS LLM backend.

    A required_model can still be supplied for GLM-only regression lanes, but
    the default path follows the requested --model. GPT-5.x models use the same
    opencode/Codex OAuth credential path as the ATLAS backend.
    """

    def __init__(self, required_model: str = "", timeout_s: int | None = None) -> None:
        self.required_model = required_model
        self.timeout_s = int(timeout_s or os.getenv("ATLAS_HEADLESS_LLM_TIMEOUT", "600"))
        self.retry_count = max(0, int(os.getenv("ATLAS_HEADLESS_LLM_RETRIES", "2")))
        self.retry_backoff_s = max(0.0, float(os.getenv("ATLAS_HEADLESS_LLM_RETRY_BACKOFF_S", "2.0")))

    def _activate_requested_model(self, model: str) -> tuple[str, str]:
        """Resolve profile-style --model values before live provider calls."""

        requested = str(model or "").strip()
        if not requested:
            return requested, ""
        try:
            try:
                from src import config
            except ModuleNotFoundError:
                import config
            if getattr(config, "is_cli_backend_model", lambda _name: False)(requested):
                if config.activate_cli_backend(requested):
                    return str(config.MODEL_NAME or requested), ""
            if config.set_active_profile(requested):
                return str(config.MODEL_NAME or requested), requested
        except Exception:
            return requested, ""
        return requested, ""

    def available_reason(self, model: str) -> str:
        if self.required_model and model != self.required_model:
            return f"required model {self.required_model}, got {model}"
        if os.getenv("ATLAS_RUN_REAL_LLM_TDD") != "1":
            return "ATLAS_RUN_REAL_LLM_TDD=1 is not set"
        resolved_model, _profile = self._activate_requested_model(model)
        model_l = (resolved_model or "").lower()
        if model_l in {"cursor-cli", "cursor-agent"} or model_l.startswith("cursor-cli"):
            return "" if shutil.which("cursor-agent") else "cursor-agent not found in PATH"
        if model_l in {"claude-cli", "claude"} or model_l.startswith("claude-cli"):
            return "" if shutil.which("claude") else "claude not found in PATH"
        if model_l.startswith("openai/"):
            model_l = model_l.split("/", 1)[1]
        if model_l.startswith("gpt-5") or ("gpt" in model_l and "codex" in model_l):
            try:
                try:
                    from src.opencode_backend import get_credentials
                except ModuleNotFoundError:  # direct script execution fallback
                    from opencode_backend import get_credentials

                cred = get_credentials("openai")
            except Exception as exc:
                return f"cannot load opencode/Codex OAuth credential: {exc}"
            if not (cred and cred.get("access")):
                return "no opencode/Codex OAuth credential found; run `python -m src.opencode_backend login`"
            return ""
        if not (
            os.getenv("ZAI_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("PROFILE_glm_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
        ):
            return "no live API key found in process environment"
        return ""

    def _reasoning_effort_for_stage(self, stage: str) -> str:
        suffix = str(stage or "").upper().replace("-", "_")
        configured = (
            os.getenv(f"ATLAS_HEADLESS_LLM_REASONING_EFFORT_{suffix}", "").strip()
            or os.getenv("ATLAS_HEADLESS_LLM_REASONING_EFFORT", "").strip()
        )
        if configured:
            return configured
        # Headless real runs need complete JSON artifacts more than hidden
        # chain-of-thought.  Reasoning-heavy providers can spend the whole
        # completion budget before emitting content, so default artifact stages
        # to no provider thinking unless the operator opts back in.
        if stage in {"ssot-gen", "rtl-gen", "tb-gen"}:
            return "none"
        return (
            os.getenv("REASONING_EFFORT", "").strip()
            or os.getenv("REASONING_MODE", "").strip()
        )

    def complete(
        self,
        *,
        stage: str,
        model: str,
        system_prompt: str,
        prompt: str,
        context: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        blocker = self.available_reason(model)
        if blocker:
            return LLMResponse(stage=stage, model=model, raw_response="", error=blocker, status="blocked")
        resolved_model, profile_name = self._activate_requested_model(model)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        stage_max_tokens = int(os.getenv(f"ATLAS_HEADLESS_LLM_MAX_TOKENS_{stage.upper().replace('-', '_')}", "0") or 0)
        default_max_tokens = int(os.getenv("ATLAS_HEADLESS_LLM_MAX_TOKENS", "12000"))
        request = {
            "messages": messages,
            "model": resolved_model or model,
            "profile": profile_name,
            "caller_tag": f"headless.{stage}",
            "max_tokens": stage_max_tokens if stage_max_tokens > 0 else default_max_tokens,
            "reasoning_effort": self._reasoning_effort_for_stage(stage),
        }
        if str(resolved_model or model).lower() in {"claude-cli", "claude"}:
            # Let the Claude backend own timeout cleanup.  If the outer
            # subprocess timeout fires first, Claude Code can remain as an
            # orphaned detached child because the backend starts it in a new
            # process session.
            request["claude_cli_timeout_sec"] = max(1, self.timeout_s - 30)
        if output_schema and os.getenv("ATLAS_HEADLESS_LLM_JSON_MODE", "1") != "0":
            request["extra_body"] = {"response_format": {"type": "json_object"}}
        child_code = r'''
import json
import sys
from pathlib import Path

source_root = Path.cwd()
for candidate in (source_root, source_root / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
req = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
try:
    try:
        from src import config
    except ModuleNotFoundError:
        import config
    profile = str(req.get("profile") or "").strip()
    if profile:
        config.set_active_profile(profile)
        req["model"] = config.MODEL_NAME
    elif config.set_active_profile(req["model"]):
        req["model"] = config.MODEL_NAME
    elif getattr(config, "is_cli_backend_model", lambda _name: False)(req["model"]):
        config.activate_cli_backend(req["model"])
        req["model"] = config.MODEL_NAME
    elif config.is_opencode_model(req["model"]):
        config.activate_opencode_oauth(req["model"])
    if req.get("claude_cli_timeout_sec") and getattr(config, "CLAUDE_CLI_ENABLE", False):
        _timeout = int(req["claude_cli_timeout_sec"])
        config.CLAUDE_CLI_TIMEOUT_SEC = _timeout
        import os
        os.environ["CLAUDE_CLI_TIMEOUT_SEC"] = str(_timeout)
    from src.llm_client import call_llm_raw, get_last_usage
    try:
        from lib.model_pricing import get_active_pricing
    except Exception:
        get_active_pricing = None
    raw = call_llm_raw(
        messages=req["messages"],
        temperature=0.1,
        model=req["model"],
        caller_tag=req.get("caller_tag") or "headless",
        max_tokens=req.get("max_tokens"),
        extra_body=req.get("extra_body"),
        reasoning_effort=req.get("reasoning_effort") or None,
    )
    usage = get_last_usage() or {}
    cost = {}
    try:
        if usage and get_active_pricing is not None:
            price = get_active_pricing(req.get("model"))
            if price is not None:
                in_tok = int(usage.get("input", 0) or 0)
                out_tok = int(usage.get("output", 0) or 0)
                cache_tok = int(usage.get("cache_read", 0) or 0)
                billable_in = max(0, in_tok - cache_tok)
                cost_usd = (
                    billable_in * float(price.input)
                    + cache_tok * float(price.cache)
                    + out_tok * float(price.output)
                ) / 1_000_000.0
                cost = {
                    "usd": cost_usd,
                    "pricing_per_1m": {
                        "input": float(price.input),
                        "cache": float(price.cache),
                        "output": float(price.output),
                    },
                }
    except Exception:
        cost = {}
    print(json.dumps({"raw": raw, "usage": usage, "cost": cost, "error": ""}))
except BaseException as exc:
    print(json.dumps({"raw": "", "usage": {}, "cost": {}, "error": repr(exc)}))
    raise SystemExit(1)
'''
        last_error = ""
        last_raw = ""
        last_usage: dict[str, Any] = {}
        artifact_required = stage in {"ssot-gen", "rtl-gen", "tb-gen"}
        ip = _safe_name(str(context.get("ip") or "headless_ip"), "headless_ip")
        retry_messages = list(messages)
        for attempt in range(self.retry_count + 1):
            request["messages"] = retry_messages
            with tempfile.TemporaryDirectory(prefix="atlas_headless_llm_") as tmp:
                req_path = Path(tmp) / "request.json"
                req_path.write_text(json.dumps(request), encoding="utf-8")
                try:
                    proc = subprocess.run(
                        [sys.executable, "-c", child_code, str(req_path)],
                        cwd=str(SOURCE_ROOT),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=self.timeout_s,
                    )
                except subprocess.TimeoutExpired:
                    last_error = f"real provider timed out after {self.timeout_s}s"
                    proc = None
                stdout = (proc.stdout or "").strip() if proc is not None else ""
                try:
                    payload = json.loads(stdout.splitlines()[-1]) if stdout else {}
                except Exception:
                    payload = {}

                payload_usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
                payload_cost = payload.get("cost") if isinstance(payload.get("cost"), dict) else {}
                combined_usage = dict(payload_usage)
                if payload_cost:
                    combined_usage["cost"] = payload_cost
                last_usage = combined_usage

                raw = str(payload.get("raw") or "")
                last_raw = raw
                if proc is not None and proc.returncode == 0 and str(raw or "").strip() and not str(raw).startswith("Error calling LLM:"):
                    data = _json_from_text(str(raw)) or {}
                    if isinstance(data.get("human_gate"), dict):
                        return LLMResponse(stage=stage, model=resolved_model or model, raw_response=str(raw), error="model requested human_gate", status="human_gate")
                    artifacts = parse_llm_artifacts(stage, str(raw), ip=ip)
                    if artifact_required and not artifacts:
                        last_error = f"model output did not contain expected JSON object with files[] {stage} artifact"
                        if attempt < self.retry_count:
                            retry_messages = messages + [
                                {
                                    "role": "user",
                                    "content": (
                                        "The previous response was malformed, truncated, or did not contain a complete "
                                        f"JSON object with files[] artifacts for {stage}. Retry the same task now. "
                                        "Return exactly one complete JSON object and nothing else. Keep file contents "
                                        "concise enough to finish the JSON; do not include analysis or markdown."
                                    ),
                                }
                            ]
                            time.sleep(self.retry_backoff_s * (attempt + 1))
                            continue
                        return LLMResponse(
                            stage=stage,
                            model=resolved_model or model,
                            raw_response=str(raw),
                            usage=combined_usage,
                            error=last_error,
                            status="blocked",
                        )
                    return LLMResponse(
                        stage=stage,
                        model=resolved_model or model,
                        raw_response=str(raw),
                        parsed_artifacts=artifacts,
                        usage=combined_usage,
                    )

                if proc is None:
                    last_error = last_error or f"real provider timed out after {self.timeout_s}s"
                elif proc.returncode != 0:
                    last_error = str(payload.get("error") or proc.stderr or f"real provider child exited {proc.returncode}")
                else:
                    last_error = str(raw or "empty output")

                should_retry = (
                    "Remote end closed connection without response" in last_error
                    or "timed out" in last_error.lower()
                    or not str(raw or "").strip()
                    or str(raw).startswith("Error calling LLM:")
                )
                if attempt < self.retry_count and should_retry:
                    time.sleep(self.retry_backoff_s * (attempt + 1))
                    continue
                return LLMResponse(
                    stage=stage,
                    model=resolved_model or model,
                    raw_response=last_raw,
                    usage=last_usage,
                    error=last_error or "real provider failed",
                    status="blocked",
                )

        combined_usage = last_usage
        raw = last_raw
        artifacts = parse_llm_artifacts(stage, str(raw), ip=ip)
        data = _json_from_text(str(raw)) or {}
        if isinstance(data.get("human_gate"), dict):
            return LLMResponse(stage=stage, model=resolved_model or model, raw_response=str(raw), error="model requested human_gate", status="human_gate")
        if stage in {"ssot-gen", "rtl-gen", "tb-gen"} and not artifacts:
            return LLMResponse(
                stage=stage,
                model=resolved_model or model,
                raw_response=str(raw),
                usage=combined_usage,
                error=f"model output did not contain expected JSON object with files[] {stage} artifact",
                status="blocked",
            )
        return LLMResponse(
            stage=stage,
            model=resolved_model or model,
            raw_response=str(raw),
            parsed_artifacts=artifacts,
            usage=combined_usage,
        )


def _json_from_text(text: str) -> dict[str, Any] | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    candidates = [fenced.group(1)] if fenced else []
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except Exception:
            try:
                data, _ = decoder.raw_decode(candidate.strip())
            except Exception:
                continue
        if isinstance(data, dict):
            return data
    for match in re.finditer(r"\{", text):
        try:
            data, _ = decoder.raw_decode(text[match.start() :].strip())
        except Exception:
            continue
        if isinstance(data, dict):
            return data
    return None


def _yaml_from_text(text: str) -> str:
    fenced = re.search(r"```(?:yaml|yml)\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip() + "\n"
    if "top_module:" in text and "function_model:" in text:
        return text.strip() + "\n"
    return ""


def _response_declares_empty_files(response: LLMResponse) -> bool:
    data = _json_from_text(response.raw_response) or {}
    files = data.get("files")
    return isinstance(files, list) and not files


def parse_llm_artifacts(stage: str, raw_response: str, *, ip: str) -> list[dict[str, Any]]:
    data = _json_from_text(raw_response)
    if isinstance(data, dict):
        files = data.get("files")
        if isinstance(files, list):
            out = []
            for item in files:
                if isinstance(item, dict) and item.get("path") and "content" in item:
                    out.append({"path": str(item["path"]), "content": str(item["content"]), "kind": item.get("kind", stage)})
            return out
        if isinstance(data.get("ssot_yaml"), str):
            return [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "content": data["ssot_yaml"], "kind": "ssot"}]
    yaml_text = _yaml_from_text(raw_response)
    if yaml_text and stage == "ssot-gen":
        return [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "content": yaml_text, "kind": "ssot"}]
    return []


@dataclass
class StageResult:
    stage: str
    status: str
    message: str = ""
    returncode: int = 0
    artifacts: list[str] = field(default_factory=list)
    blocker: str = ""


@dataclass
class WorkflowResult:
    ip: str
    status: str
    stages: list[StageResult]
    root: str
    run_log: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ip": self.ip,
            "status": self.status,
            "root": self.root,
            "run_log": self.run_log,
            "stages": [stage.__dict__ for stage in self.stages],
        }


class HeadlessWorkflowRunner:
    def __init__(
        self,
        *,
        root: str | Path,
        model: str = "",
        llm_provider: LLMProvider | None = None,
        require_glm51: bool = False,
        run_mode: str = "",
        req_approver: str = "",
        stage_retries: int | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.model = model or os.getenv("ATLAS_HEADLESS_LLM_MODEL") or "glm-5.1"
        self.run_mode = _normalize_run_mode(run_mode) or "signoff"
        self.llm_provider = llm_provider or RealLLMProvider(required_model=os.getenv("ATLAS_HEADLESS_REQUIRED_MODEL", ""))
        self.require_glm51 = require_glm51
        self.stage_engine = WorkflowStageEngine(self.root, source_root=SOURCE_ROOT, run_mode=self.run_mode)
        self.stages: list[StageResult] = []
        self.ssot_repair_attempts = max(0, int(os.getenv("ATLAS_HEADLESS_SSOT_REPAIR_ATTEMPTS", "2")))
        self.rtl_repair_attempts = max(0, int(os.getenv("ATLAS_HEADLESS_RTL_REPAIR_ATTEMPTS", "2")))
        self.req_approver = (req_approver or os.getenv("ATLAS_REQ_APPROVED_BY", "")).strip()
        # Outer retry loop: a failed stage gets re-invoked with fresh internal
        # repair rounds (phase-2: each re-invocation converged work the bounded
        # in-stage rounds had left open). human_gate/blocked never retry.
        if stage_retries is None:
            stage_retries = int(os.getenv("ATLAS_HEADLESS_STAGE_RETRIES", "0"))
        self.stage_retries = max(0, stage_retries)

    def _ip_dir(self, ip: str) -> Path:
        return self.root / ip

    def _log_dir(self, ip: str) -> Path:
        return self._ip_dir(ip) / "logs" / "llm"

    def _progress_log_path(self, ip: str) -> Path:
        return self._ip_dir(ip) / "logs" / "run_progress.jsonl"

    def _llm_trace_path(self, ip: str) -> Path:
        return self._ip_dir(ip) / "logs" / "llm_call_trace.jsonl"

    def _heartbeat_path(self, ip: str) -> Path:
        return self._ip_dir(ip) / "logs" / "heartbeat.json"

    def _write_progress(self, ip: str, event: str, **fields: Any) -> None:
        _append_jsonl(
            self._progress_log_path(ip),
            {
                "ts": _utc(),
                "event": event,
                "pid": os.getpid(),
                "root": str(self.root),
                "ip": ip,
                **fields,
            },
        )

    def _write_heartbeat(self, ip: str, **fields: Any) -> None:
        _write_json(
            self._heartbeat_path(ip),
            {
                "ts": _utc(),
                "pid": os.getpid(),
                "root": str(self.root),
                "ip": ip,
                **fields,
            },
        )

    def _question_path(self, ip: str, stage: str, topic: str) -> Path:
        return self._ip_dir(ip) / "questions" / f"{_safe_name(stage)}_{_safe_name(topic, 'decision')}.json"

    def _review_decision_path(self, ip: str, workflow: str, topic: str) -> Path:
        return self._ip_dir(ip) / "review" / f"decision_needed_{_safe_name(workflow)}_{_safe_name(topic, 'decision')}.json"

    def _write_review_decision_needed(
        self,
        ip: str,
        workflow: str,
        topic: str,
        *,
        decision_needed: str,
        evidence: dict[str, Any] | None = None,
        severity: str = "needs_review",
        next_action: str = "",
    ) -> Path:
        path = self._review_decision_path(ip, workflow, topic)
        _write_json(
            path,
            {
                "schema_version": 1,
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": workflow,
                "topic": topic,
                "severity": severity,
                "decision_needed": decision_needed,
                "evidence": evidence or {},
                "next_action": next_action
                or "Review and either lock missing SSOT semantics or approve a workflow/tooling repair.",
                "created_at": _utc(),
            },
        )
        return path

    def _write_human_gate(
        self,
        ip: str,
        stage: str,
        topic: str,
        *,
        decision_needed: str,
        evidence: dict[str, Any] | None = None,
        options: list[dict[str, Any]] | None = None,
        recommended_default: dict[str, Any] | None = None,
        downstream_effect: list[str] | None = None,
    ) -> Path:
        path = self._question_path(ip, stage, topic)
        _write_json(
            path,
            {
                "stage": stage,
                "status": "human_gate",
                "decision_needed": decision_needed,
                "evidence": evidence or {"requirement_refs": [f"{ip}/req/{ip}_requirements.md"], "ssot_refs": [], "tool_logs": [], "goal_ids": []},
                "options": options or [
                    {"id": "A", "description": "Define the missing behavior in SSOT", "impact": "Regenerate FL/RTL/TB from updated SSOT"}
                ],
                "recommended_default": recommended_default or {"id": "A", "reason": "SSOT must own product semantics"},
                "downstream_effect": downstream_effect or ["SSOT", "functional_model", "RTL", "TB"],
                "created_at": _utc(),
            },
        )
        return path

    def _append(self, stage: str, status: str, message: str = "", returncode: int = 0, artifacts: list[str] | None = None, blocker: str = "") -> StageResult:
        result = StageResult(stage=stage, status=status, message=message, returncode=returncode, artifacts=artifacts or [], blocker=blocker)
        self.stages.append(result)
        return result

    def _append_engine_result(
        self,
        result: StageEngineResult,
        stage: str | None = None,
        *,
        artifacts: list[str] | None = None,
        blocker: str | None = None,
    ) -> StageResult:
        merged_artifacts = list(result.artifacts)
        if artifacts:
            merged_artifacts.extend(artifacts)
        return self._append(
            stage or result.stage,
            result.status,
            result.message,
            returncode=result.returncode,
            artifacts=merged_artifacts,
            blocker=blocker if blocker is not None else result.blocker,
        )

    def _copy_requirement(self, ip: str, requirement_path: Path) -> str:
        text = requirement_path.read_text(encoding="utf-8")
        req_dir = self._ip_dir(ip) / "req"
        req_dir.mkdir(parents=True, exist_ok=True)
        for name in (f"{ip}_requirements.md", "requirements.md"):
            (req_dir / name).write_text(text, encoding="utf-8")
        source_rel = f"{ip}/req/requirements.md"
        target_rel = f"{ip}/req/{ip}_requirements.md"
        manifest_path = req_dir / "approval_manifest.json"
        if manifest_path.is_file():
            try:
                existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = {}
            if isinstance(existing, dict) and existing.get("status") == "requirements_locked":
                # lock_requirement_set owns this manifest; clobbering it breaks the
                # contract authority gate downstream. Record the copy separately.
                manifest_path = req_dir / "headless_req_copy_manifest.json"
        _write_json(
            manifest_path,
            {
                "schema_version": 1,
                "type": "requirement_approval_manifest",
                "ip": ip,
                "approved_by": "headless_runner",
                "approved_at_utc": _utc(),
                "decision_note": "headless requirement_path provided as approved test input",
                "source": source_rel,
                "source_sha256": _sha(text),
                "target": target_rel,
                "target_sha256": _sha(text),
            },
        )
        return text

    def _validate_req(self, ip: str, text: str) -> StageResult | None:
        if len(text.strip()) < 200 or PLACEHOLDER_RE.search(text):
            path = self._write_human_gate(
                ip,
                "req",
                "requirements",
                decision_needed="Provide substantive requirements without placeholder markers before SSOT generation.",
                evidence={"requirement_refs": [f"{ip}/req/{ip}_requirements.md"], "tool_logs": [], "goal_ids": [], "ssot_refs": []},
            )
            return self._append("req", "human_gate", "requirements are incomplete", artifacts=[str(path.relative_to(self.root))], blocker=str(path.relative_to(self.root)))
        return self._append("req", "pass", "requirements copied", artifacts=[f"{ip}/req/{ip}_requirements.md", f"{ip}/req/requirements.md"])

    REQ_CANDIDATE_FILES = (
        "requirements_index.json",
        "obligations.json",
        "contract_refs.json",
        "structural_contracts.json",
        "behavioral_contracts.json",
        "evidence_plan.json",
    )

    def _run_contract_bundle_gate(self, ip: str, *, review_candidate: bool = False) -> subprocess.CompletedProcess[str]:
        script = WORKFLOW_ROOT / "req-gen" / "scripts" / "check_contract_bundle.py"
        cmd = [sys.executable, str(script), ip, "--root", str(self.root)]
        if review_candidate:
            cmd.append("--review-candidate")
        return subprocess.run(
            cmd, cwd=str(self.root), text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=60,
        )

    def _req_contracts_prompt(self, ip: str, context: dict[str, Any], failures: str = "") -> tuple[str, str]:
        system = (
            "HEADLESS PROVIDER CONTRACT.\n"
            "You are a requirements-contract author called by a headless artifact runner. "
            "Return only the machine-readable JSON object requested; no markdown fences, "
            "no prose, no tool actions.\n"
        )
        repair_block = (
            f"\nPrevious candidate FAILED check_contract_bundle with these findings — fix every one:\n{failures}\n"
            if failures
            else ""
        )
        prompt = (
            f"Author the VCM requirement-contract candidate bundle for {ip} from the requirement below. "
            "The bundle is the locked-truth authority every downstream stage gates against; derive it from "
            "the requirement semantics, never boilerplate.\n\n"
            "Return exactly one JSON object:\n"
            f'{{"files":[{{"path":"{ip}/req/<name>","kind":"req_contract","content":"<JSON document as string>"}}, ...]}}\n'
            f"with exactly these six files under {ip}/req/: {', '.join(self.REQ_CANDIDATE_FILES)}.\n\n"
            "Required shapes — the validator reads these EXACT key names; cross-links are checked both ways:\n"
            "- requirements_index.json: {\"ip\", \"requirements\": [{\"requirement_id\", \"title\", "
            "\"statement\", \"required\": true, \"status\": \"approved\", "
            "\"obligation_refs\": [\"OBL_...\"]}]}\n"
            "- obligations.json: {\"obligations\": [{\"obligation_id\", \"statement\", "
            "\"requirement_refs\": [\"REQ_...\"], \"contract_refs\": [\"CR_...\"] (anchor refs into "
            "contract_refs.json), and at least one of \"structural_contract_refs\": [\"SC_...\"] / "
            "\"behavioral_contract_refs\": [\"BEH_...\"] (implementation authority), plus \"owned_by\", "
            "\"required_stages\", \"closure_stage\", \"failure_owner\", "
            "\"granularity\" (structural|count|content|temporal), \"ssot_anchor\"}]}\n"
            "- contract_refs.json: {\"contract_refs\": [{\"contract_ref_id\": \"CR_...\", "
            "\"obligation_refs\": [\"OBL_...\"], \"kind\", and machine-checkable detail: stage_contracts/"
            "checks/observables/validator/pass_condition (never title-only anchor text)}]}\n"
            "- structural_contracts.json: {\"contracts\": [{\"id\": \"SC_...\", \"title\", \"ssot_anchor\", "
            "\"obligations\": [\"OBL_...\"] (this exact key), \"signals\": [{\"name\", "
            "\"direction\": input|output|inout (MANDATORY on every signal — signals are top-level RTL "
            "ports; register fields belong in behavioral contracts, not here), \"width\"}], "
            "\"stage_contracts\": [{\"stage\", \"artifact\"}]}]}\n"
            "- behavioral_contracts.json: {\"contracts\": [{\"id\": \"BEH_...\", \"title\", "
            "\"obligations\": [\"OBL_...\"] (this exact key), \"rules\" (named exprs = function semantics), "
            "\"transactions\": [{\"name\", \"preconditions\" or \"when\" (MANDATORY per transaction), and "
            "\"outputs\"/\"state_updates\"/\"postconditions\" (at least one, MANDATORY)}], "
            "\"cycle\" (timing semantics), \"ssot_anchor\", "
            "\"stage_contracts\" incl rtl + tb + sim with \"pass_condition\"}]}. "
            "A contract that defines NO DUT behavior of its own (evidence/meta contracts about "
            "required artifacts or reports) MUST carry an explicit \"projection_waiver\" field "
            "explaining why — downstream gates require every behavioral contract to project into "
            "function_model AND cycle_model rows OR carry that waiver (one key covers both sides).\n"
            "- evidence_plan.json: {\"evidence_plan\": [{\"evidence_id\", \"contract_ref\" (must name an "
            "existing CR_/SC_/BEH_ id; every contract needs evidence rows covering its stage_contracts or "
            "it 'lacks evidence closure'), \"stage\", \"artifact\", \"validator\", \"pass_condition\"}]}\n\n"
            "Cross-link integrity is validated in BOTH directions: every requirement lists obligation_refs, "
            "every obligation lists requirement_refs AND contract_refs AND structural/behavioral refs that "
            "resolve to declared ids. Use stable IDs (REQ_/OBL_/CR_/BEH_/SC_ prefixes).\n"
            f"{repair_block}\n"
            f"Requirement:\n{context.get('requirement_text', '')}"
        )
        return system, prompt

    def _run_req_contracts_stage(self, ip: str, context: dict[str, Any]) -> StageResult:
        """Author + gate (+ lock) the VCM requirement bundle.

        Phase-2 gap: headless had no counterpart to /draft-req + /finalize-req,
        so fresh IPs died late at rtl-gen's contract authority gate. This stage
        runs early instead: idempotent when already locked, LLM-authors the
        candidate bundle otherwise, and locks only with an explicit human
        approver (--req-approver / ATLAS_REQ_APPROVED_BY) — otherwise it stops
        at a human_gate, which is the correct VCM behavior.
        """
        req_dir = self._ip_dir(ip) / "req"
        manifest = _read_json(req_dir / "approval_manifest.json")
        locked = manifest.get("status") == "requirements_locked"
        if locked:
            gate = self._run_contract_bundle_gate(ip)
            if gate.returncode == 0:
                return self._append(
                    "req-contracts", "pass",
                    f"locked bundle valid\n{(gate.stdout or '').strip()}",
                    artifacts=[f"{ip}/req/approval_manifest.json"],
                )
            q = self._write_human_gate(
                ip, "req-contracts", "locked_bundle_invalid",
                decision_needed=(
                    "req/ bundle is locked but check_contract_bundle fails; a human must repair or "
                    f"re-lock the authority files.\n{(gate.stdout or '').strip()}"
                ),
                evidence={"requirement_refs": [f"{ip}/req"], "tool_logs": [], "goal_ids": [], "ssot_refs": []},
            )
            return self._append(
                "req-contracts", "human_gate", "locked bundle failed authority gate",
                returncode=gate.returncode, blocker=str(q.relative_to(self.root)),
            )

        attempts = max(0, int(os.getenv("ATLAS_HEADLESS_REQ_REPAIR_ATTEMPTS", "2")))
        failures = ""
        candidates_exist = all((req_dir / name).is_file() for name in self.REQ_CANDIDATE_FILES)
        for attempt in range(attempts + 1):
            if not candidates_exist or failures:
                system, prompt = self._req_contracts_prompt(ip, context, failures)
                response = self._call_llm(
                    "req-contracts", ip, context,
                    system_prompt=system, prompt=prompt,
                    log_stage=("req-contracts" if attempt == 0 else f"req-contracts-repair-{attempt}"),
                )
                if response.status in {"blocked", "human_gate"}:
                    return self._append_llm_gate(ip, "req-contracts", response, topic=f"author_{attempt}")
                self._apply_artifacts(ip, response.parsed_artifacts)
                candidates_exist = all((req_dir / name).is_file() for name in self.REQ_CANDIDATE_FILES)
                if not candidates_exist:
                    missing = [n for n in self.REQ_CANDIDATE_FILES if not (req_dir / n).is_file()]
                    failures = "missing candidate files: " + ", ".join(missing)
                    continue
            gate = self._run_contract_bundle_gate(ip, review_candidate=True)
            if gate.returncode == 0:
                break
            failures = (gate.stdout or gate.stderr or "").strip()
        else:
            return self._append(
                "req-contracts", "fail",
                f"candidate bundle failed check_contract_bundle after {attempts + 1} attempts\n{failures}",
                returncode=1, blocker=f"{ip}/req",
            )

        approver = self.req_approver
        if not approver:
            q = self._write_human_gate(
                ip, "req-contracts", "approval_required",
                decision_needed=(
                    "Candidate bundle passes check_contract_bundle --review-candidate. Locking requires a "
                    "human approver: re-run with --req-approver <name> (or ATLAS_REQ_APPROVED_BY), or lock "
                    f"manually via lock_requirement_set.py {ip} --root {self.root} --from-candidate --approved-by <name>."
                ),
                evidence={"requirement_refs": [f"{ip}/req"], "tool_logs": [], "goal_ids": [], "ssot_refs": []},
            )
            return self._append(
                "req-contracts", "human_gate", "candidate ready; human approval required to lock",
                blocker=str(q.relative_to(self.root)),
                artifacts=[f"{ip}/req/{name}" for name in self.REQ_CANDIDATE_FILES],
            )

        script = WORKFLOW_ROOT / "req-gen" / "scripts" / "lock_requirement_set.py"
        cmd = [
            sys.executable, str(script), ip, "--root", str(self.root),
            "--from-candidate", "--approved-by", approver,
            "--decision-note", "headless req-contracts stage lock",
        ]
        # Only a non-locked (markdown-copy) manifest may be replaced; a real
        # lock returned early above.
        if (req_dir / "approval_manifest.json").is_file() or (req_dir / "locked_truth.md").is_file():
            cmd.append("--force")
        lock = subprocess.run(
            cmd, cwd=str(self.root), text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=60,
        )
        if lock.returncode != 0:
            return self._append(
                "req-contracts", "fail",
                f"lock_requirement_set failed\n{(lock.stdout or '').strip()}\n{(lock.stderr or '').strip()}",
                returncode=lock.returncode, blocker=f"{ip}/req",
            )
        gate = self._run_contract_bundle_gate(ip)
        status = "pass" if gate.returncode == 0 else "fail"
        return self._append(
            "req-contracts", status,
            f"bundle locked by {approver}\n{(gate.stdout or '').strip()}",
            returncode=gate.returncode,
            artifacts=[f"{ip}/req/locked_truth.md", f"{ip}/req/approval_manifest.json"],
        )

    def _locked_truth_projection_brief(self, ip: str) -> str:
        """Prompt block telling ssot-gen HOW to project a locked req bundle.

        Phase-2 headless validation: 4 of 13 pipeline stalls (symbol contract
        x2, function_model projection, cycle_model projection + missing
        stimulus specs) were all "the model authored SSOT without knowing the
        locked-truth projection rules the downstream gates enforce". When the
        bundle is locked, surface the contract IDs and the projection rules in
        the ssot-gen prompt so the SSOT arrives projected instead of being
        repaired stage by stage.
        """
        req_dir = self._ip_dir(ip) / "req"
        try:
            manifest = json.loads((req_dir / "approval_manifest.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""
        if not (isinstance(manifest, dict) and manifest.get("status") == "requirements_locked"):
            return ""

        def _ids(name: str, key: str) -> list[str]:
            try:
                doc = json.loads((req_dir / name).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return []
            items = doc.get(key) if isinstance(doc, dict) else doc
            found: list[str] = []
            for item in items if isinstance(items, list) else []:
                if isinstance(item, dict):
                    cid = (
                        item.get("id")
                        or item.get("contract_id")
                        or item.get("requirement_id")
                        or item.get("obligation_id")
                    )
                    if cid:
                        found.append(str(cid))
            return found

        requirements = _ids("requirements_index.json", "requirements")
        obligations = _ids("obligations.json", "obligations")
        behavioral = _ids("behavioral_contracts.json", "contracts")
        structural = _ids("structural_contracts.json", "contracts")
        if not (behavioral or structural or obligations):
            return ""
        return (
            "LOCKED TRUTH PROJECTION CONTRACT.\n"
            f"{ip}/req holds a hash-locked requirement bundle (status requirements_locked). "
            "The SSOT must PROJECT this locked truth; never restate, rename, or contradict it.\n"
            f"- Requirement IDs: {', '.join(requirements) or '(none)'}\n"
            f"- Obligation IDs: {', '.join(obligations) or '(none)'}\n"
            f"- Behavioral contract IDs: {', '.join(behavioral) or '(none)'}\n"
            f"- Structural contract IDs: {', '.join(structural) or '(none)'}\n"
            "Projection rules enforced by downstream gates (derive_rtl_todos, derive_tb_todos, "
            "emit_cycle_model symbol contract):\n"
            "- Every behavioral contract ID must appear in contract_refs on at least one "
            "function_model.transactions[] entry whose output_rules/state_updates implement it.\n"
            "- Every behavioral contract ID with timing/protocol semantics must also appear in "
            "contract_refs on a cycle_model row carrying a machine-checkable expr "
            "(handshake_rules/pipeline/ordering), or declare an explicit cycle_model_waiver.\n"
            "- Symbol contract: every cycle_model.handshake_rules[].signal and every expr symbol "
            "must be a declared io port, parameter, register field, function_model.state_variables[] "
            "name, or function_model.derived_signals[] name. Declare any new helper symbol in "
            "function_model.derived_signals with an expr; never invent undeclared names.\n"
            "- Every function_model.transactions[] entry must carry stimulus_machine_spec with a "
            "concrete timeline (csr_write/csr_read/assign/wait_cycles steps using real register "
            "offsets and declared input ports) and fl_apply_count equal to the number of times the "
            "timeline fires that transaction (count the event edges). FL output_rules evaluate "
            "against PRE-transaction state; timelines that verify read-data must end with a "
            "csr_read.\n"
            "- FL state_updates model TRANSACTION-COMPLETE, sampled-after-settle state: a 1-cycle "
            "request/strobe register (clear request, irq pulse) must end the transaction consumed "
            "(0), never pending (1) — by the time the scoreboard samples, the strobe has decayed. "
            "Verify pulse SHAPES in cycle_model rules, not FL state.\n"
            "- cycle_model.state_accumulating means the TEST FLOW relies on cross-goal state "
            "accumulation (rare; e.g. arbiter last-winner chains). For ordinary IPs — counters, "
            "CSR blocks — leave it false: the harness resets DUT and FL between goals and each "
            "transaction timeline must establish its own preconditions.\n"
            "- Connection contracts must be machine-readable {module, port, signal} records (or a "
            "port_map mapping) under sub_modules[].connections, describing CHILD-instance wiring "
            "with signal names that exist in the RTL. Do not also emit integration.connections in "
            "ad-hoc shapes (from_module/from_port/to_signal is not parsed), and do not describe "
            "the top module's own ports as connections — top IO is owned by the structural "
            "contracts.\n\n"
        )

    def _stage_prompt(self, stage: str, ip: str, context: dict[str, Any]) -> tuple[str, str]:
        system_path = WORKFLOW_ROOT / stage / "system_prompt.md"
        workflow_stage = stage
        if stage == "rtl-gen":
            system_path = WORKFLOW_ROOT / "rtl-gen" / "system_prompt.md"
        elif stage == "tb-gen":
            system_path = WORKFLOW_ROOT / "tb-gen" / "system_prompt.md"
        elif stage == "ssot-gen":
            system_path = WORKFLOW_ROOT / "ssot-gen" / "system_prompt.md"
        system = system_path.read_text(encoding="utf-8", errors="replace") if system_path.is_file() else ""
        headless_contract = (
            "HEADLESS PROVIDER CONTRACT.\n"
            "You are being called by a headless artifact runner, not the interactive ATLAS tool loop. "
            "Do not emit Action:, write_file, run_command, todo_update, markdown fences, status prose, "
            "or a plan to create files. Return only the machine-readable JSON object requested by the "
            "user prompt. This headless JSON contract overrides any interactive tool-use wording below.\n\n"
        )
        if workflow_stage == "ssot-gen":
            system = headless_contract + system
            required_keys = _ssot_required_keys_for_mode(self.run_mode)
            locked_truth_brief = self._locked_truth_projection_brief(ip)
            prompt = (
                f"Generate canonical SSOT YAML for {ip} from {ip}/req/{ip}_requirements.md.\n\n"
                f"Run Mode: {self.run_mode}. Starter may provide only user-authored intent and allow "
                "repair_ssot_schema.py to generate boilerplate defaults; Engineering requires downstream "
                "model/test/quality detail; Signoff requires full EDA/signoff fields.\n\n"
                "Return exactly one JSON object and nothing else. Do not wrap it in markdown.\n"
                "Valid success schema:\n"
                "{\n"
                '  "files": [\n'
                "    {\n"
                f'      "path": "{ip}/yaml/{ip}.ssot.yaml",\n'
                '      "kind": "ssot",\n'
                '      "content": "<complete YAML document as a JSON string>"\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "The YAML content must be general IP SSOT, not a fixed template workaround. It must derive "
                "semantics from the requirements and include these top-level sections: "
                f"{', '.join(required_keys)}. function_model is mandatory; cycle_model is mandatory for "
                "Engineering/Signoff and may be generated by deterministic repair for Starter. Models must be "
                "substantive enough for FL-vs-RTL equivalence goals, cocotb/pyuvm scoreboard generation, "
                "coverage planning, and mismatch ownership.\n\n"
                "The generated YAML should pass `bash \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/check_ssot_disk.py\" "
                f"{ip} --root \"$ATLAS_PROJECT_ROOT\" --mode {self.run_mode}` before downstream generation; Starter mode may rely on "
                "repair_ssot_schema.py to fill generated defaults. Required validator details:\n"
                "- function_model.state_variables, function_model.transactions, and function_model.invariants "
                "must be non-empty lists.\n"
                "- Every function_model.transactions[] item must include id, name, preconditions, outputs, "
                "and either side_effects or error_cases. If state_updates exist, also summarize them in side_effects.\n"
                "- cycle_model must include clock, reset, latency, non-empty handshake_rules, non-empty pipeline, "
                "and non-empty ordering.\n"
                "- timing must include target_clocks and latency_budget.\n"
                "- power must include non-empty domains and power_states.\n"
                "- security must include classification, non-empty assets, and non-empty threat_model.\n"
                "- error_handling must include non-empty error_sources plus propagation and recovery.\n"
                "- debug_observability must include waveform_must_probe and trace_events.\n"
                "- integration must include bus_attachment and dependencies.\n"
                "- dft must include scan_required, controllability, and observability.\n"
                "- synthesis must include dialect, constraints, and required_outputs.\n"
                "- every test_requirements.scenarios[] item must include id, name, stimulus, expected, checker, and coverage.\n"
                "- quality_gates must be a mapping with ssot, rtl, dv, coverage, eda, and signoff; each gate "
                "must be a mapping with pass and evidence.\n"
                "- If quality_gates.rtl_gen.profile is production, or the IP is DMA330/PL330-class, "
                "quality_gates.rtl_gen must include pass/evidence and every manifest-owned child module "
                "must have machine-readable integration.connections or sub_modules[].connections records "
                "with module/port/signal fields.\n"
                "- traceability.yaml_to_output must be a non-empty list.\n\n"
                "- workflow_todos.rtl-gen must be a non-empty list of LLM-authored RTL TODOs. "
                "Each item must include id, content, detail, criteria, source_refs, priority, required, "
                "and owner_module/owner_file when inferable from sub_modules. These TODOs are the downstream "
                "rtl-gen work ledger and must be specific to this IP, not fixed boilerplate.\n\n"
                f"{locked_truth_brief}"
                "If the requirements leave a semantic decision undefined, return exactly this JSON shape "
                "instead of files[]:\n"
                "{\n"
                '  "human_gate": {\n'
                '    "decision_needed": "<specific RTL-engineer decision>",\n'
                '    "evidence": {"requirement_refs": [], "ssot_refs": [], "tool_logs": [], "goal_ids": []},\n'
                '    "options": [{"label": "<option>", "effect": "<downstream effect>"}],\n'
                '    "recommended_default": {"label": "<option>", "why": "<reason>"},\n'
                '    "downstream_effect": ["function_model", "cycle_model", "rtl_contract", "tb scoreboard"]\n'
                "  }\n"
                "}\n\n"
                f"Requirements:\n{context.get('requirement_text', '')}"
            )
        elif workflow_stage == "rtl-gen":
            system = headless_contract + system
            prompt = (
                f"Prepare rtl-gen for {ip} using only {ip}/yaml/{ip}.ssot.yaml and "
                f"{context.get('rtl_todo_plan_path') or f'{ip}/rtl/rtl_todo_plan.json'}, "
                f"{context.get('rtl_authoring_plan_path') or f'{ip}/rtl/rtl_authoring_plan.json'}, "
                f"and packets under {context.get('rtl_authoring_packet_dir') or f'{ip}/rtl/authoring_packets'}. "
                "Return exactly one JSON object and nothing else. Success schema: "
                f'{{"files":[{{"path":"{ip}/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"}},'
                f'{{"path":"{ip}/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"}},'
                f'{{"path":"{ip}/list/{ip}.f","kind":"filelist","content":"<filelist>"}}]}}. '
                "The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned "
                "artifacts that satisfy every TODO content/detail/criteria item and record provenance. "
                "Process one authoring packet at a time, module packets first, then unowned tasks if present, "
                "then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, "
                "and rtl_gate_human_closure until tool evidence or human-locked authority is available. "
                "Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be "
                "authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when "
                "pass_allowed is false. "
                "On repair attempts, use packet status_counts, open_required_count, Status, and Current reason "
                "fields to patch only the RTL-owned artifacts needed to close open TODOs. "
                f"Use todo_plan_sha256={context.get('rtl_todo_plan_sha256') or '<pending>'}. "
                "Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, "
                "do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint "
                "and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled "
                "rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only "
                "name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, "
                "treat it as calibration-only scale evidence, never as source RTL or a clone template. "
                "If a missing locked-truth artifact, human authority approval, or SSOT connection contract "
                "prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics."
            )
        elif workflow_stage == "tb-gen":
            system = headless_contract + system
            prompt = (
                f"Prepare tb-gen for {ip} using {ip}/verify/equivalence_goals.json, "
                f"{ip}/model/functional_model.py, and {ip}/rtl/rtl_contract.json. "
                "Do not duplicate expected behavior by hand; scoreboard must call FunctionalModel."
            )
        else:
            prompt = f"Run {stage} for {ip} with artifact validators."
        return system, prompt

    def _call_llm(
        self,
        stage: str,
        ip: str,
        context: dict[str, Any],
        *,
        system_prompt: str | None = None,
        prompt: str | None = None,
        log_stage: str | None = None,
    ) -> LLMResponse:
        if self.require_glm51 and self.model != "glm-5.1":
            response = LLMResponse(
                stage=stage,
                model=self.model,
                raw_response="",
                error=f"GLM-5.1 lane requires model glm-5.1, got {self.model}",
                status="blocked",
            )
            self._write_llm_log(ip, log_stage or stage, response, prompt="", context=context, started_at=_utc(), finished_at=_utc())
            return response
        if system_prompt is None or prompt is None:
            system, default_prompt = self._stage_prompt(stage, ip, context)
            if system_prompt is None:
                system_prompt = system
            if prompt is None:
                prompt = default_prompt
        started = _utc()
        llm_start = time.time()
        self._write_progress(
            ip,
            "llm_call_start",
            stage=stage,
            log_stage=(log_stage or stage),
            model=self.model,
            prompt_chars=len(prompt or ""),
            system_prompt_chars=len(system_prompt or ""),
            context_keys=sorted(str(k) for k in context.keys()),
        )
        self._write_heartbeat(
            ip,
            state="running",
            phase="llm_call",
            stage=stage,
            log_stage=(log_stage or stage),
            model=self.model,
        )
        response = self.llm_provider.complete(
            stage=stage,
            model=self.model,
            system_prompt=system_prompt,
            prompt=prompt,
            context=context,
            output_schema={"type": "artifact_files_or_human_gate"},
        )
        llm_elapsed = time.time() - llm_start
        finished = _utc()
        self._write_llm_log(ip, log_stage or stage, response, prompt=prompt, context=context, started_at=started, finished_at=finished)
        _append_jsonl(
            self._llm_trace_path(ip),
            {
                "ts": finished,
                "stage": stage,
                "log_stage": (log_stage or stage),
                "model": self.model,
                "status": response.status,
                "error": response.error,
                "elapsed_sec": round(llm_elapsed, 3),
                "usage": response.usage if isinstance(response.usage, dict) else {},
            },
        )
        self._write_progress(
            ip,
            "llm_call_end",
            stage=stage,
            log_stage=(log_stage or stage),
            model=self.model,
            status=response.status,
            elapsed_sec=round(llm_elapsed, 3),
            error=response.error,
        )
        # Resolve the worker session FIRST, OUTSIDE the best-effort guard below
        # (plan §2.10 / R16). In session mode a worker with no resolvable session
        # must NOT silently write session_id='' — that row is unroutable and the
        # spend vanishes. _resolve_worker_accounting_session() raises
        # WorkerSessionRoutingError in that case so the failure is visible.
        # In session mode the worker's ATLAS_DB_PATH is already the per-session
        # RUNTIME file (build_worker_env), so a plain AtlasDB(_db_path) writes the
        # llm_calls row into the runtime DB without any extra routing here.
        _session_id = _resolve_worker_accounting_session()
        try:
            _usage = response.usage if isinstance(response.usage, dict) else {}
            _cost_block = _usage.get("cost") if isinstance(_usage.get("cost"), dict) else {}
            _cost_usd = float(_cost_block.get("usd", 0) or 0)
            _in_tok = int(_usage.get("input", 0) or 0)
            _out_tok = int(_usage.get("output", 0) or 0)
            _cache_tok = int(_usage.get("cache_read", 0) or 0)
            from core.atlas_db import AtlasDB
            from pathlib import Path as _Path
            _db_path = (
                os.environ.get("ATLAS_DB_PATH")
                or str(_Path.home() / ".common_ai_agent" / "atlas.db")
            )
            # WP-1: stamp worker_run_id when the job spawn exported it via
            # build_worker_env (ATLAS_WORKER_RUN_ID). Resolvable -> exact;
            # absent -> inferred (never claim exact for an unknown worker run).
            _worker_run_id = os.environ.get("ATLAS_WORKER_RUN_ID", "").strip()
            _attr = "exact" if _worker_run_id else "inferred"
            _status = "ok" if not response.error else "error"
            _ip_id = (
                os.environ.get("ATLAS_IP_ID", "")
                or os.environ.get("ATLAS_ACTIVE_IP", "") or ip
            )
            _workflow = (
                os.environ.get("ATLAS_WORKFLOW", "")
                or os.environ.get("ATLAS_WORKER_NAME", "")
                or os.environ.get("ACTIVE_WORKSPACE", "")
                or stage
            )
            with AtlasDB(_db_path) as _db:
                _call = _db.record_llm_call(
                    session_id=_session_id,
                    ip_id=_ip_id,
                    workflow=_workflow,
                    model=self.model,
                    provider=os.environ.get("ATLAS_PROVIDER", ""),
                    call_role="worker",
                    tokens_input=_in_tok,
                    tokens_output=_out_tok,
                    cache_read_tokens=_cache_tok,
                    cost_usd=_cost_usd,
                    latency_ms=round(llm_elapsed * 1000, 1),
                    status=_status,
                    worker_run_id=_worker_run_id,
                    attribution_confidence=_attr,
                )
                # Flow event linked by llm_call_id (after insert). Attempts and
                # failures stay distinct rows — we do not collapse retries.
                try:
                    _db.record_session_flow_event(
                        event_type="llm_call.completed" if _status == "ok"
                            else "llm_call.failed",
                        idempotency_key=f"llm-call:{_call['id']}",
                        session_id=_session_id,
                        ip_id=_ip_id,
                        workflow=_workflow,
                        worker_run_id=_worker_run_id,
                        llm_call_id=_call["id"],
                        severity="error" if _status != "ok" else "",
                        attribution_confidence=_attr,
                        payload={
                            "call_role": "worker",
                            "tokens_input": int(_in_tok),
                            "tokens_output": int(_out_tok),
                            "cost_usd": _cost_usd,
                            "status": _status,
                        },
                    )
                except Exception:
                    pass
        except WorkerSessionRoutingError:
            raise
        except Exception:
            pass
        return response

    def _write_llm_log(
        self,
        ip: str,
        stage: str,
        response: LLMResponse,
        *,
        prompt: str,
        context: dict[str, Any],
        started_at: str,
        finished_at: str,
    ) -> None:
        log_dir = self._log_dir(ip)
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{stage}_prompt.md").write_text(prompt, encoding="utf-8")
        _write_json(log_dir / f"{stage}.json", response.to_log(prompt=prompt, context=context, started_at=started_at, finished_at=finished_at))

    def _write_deterministic_rtl_seed_log(self, ip: str, context: dict[str, Any]) -> None:
        log_path = self._log_dir(ip) / "rtl-gen.json"
        if log_path.is_file():
            return
        provenance_path = self._ip_dir(ip) / "rtl" / "rtl_authoring_provenance.json"
        provenance = _read_json(provenance_path)
        packet_logs = sorted(self._log_dir(ip).glob("rtl-gen-packet-*.json"))
        if provenance.get("generator") != "generic_ssot_rule_seed" and not packet_logs:
            return
        rtl_files = provenance.get("rtl_files") if isinstance(provenance.get("rtl_files"), list) else []
        if packet_logs and provenance.get("generator") != "generic_ssot_rule_seed":
            rel_packet_logs = [str(path.relative_to(self.root)) for path in packet_logs]
            raw_response = json.dumps(
                {
                    "status": "pass",
                    "generator": "packet_llm",
                    "reason": "packet-mode rtl-gen completed with per-packet LLM artifacts",
                    "packet_logs": rel_packet_logs,
                    "rtl_files": rtl_files,
                },
                sort_keys=True,
            )
            response = LLMResponse(
                stage="rtl-gen",
                model=self.model or "packet-llm",
                raw_response=raw_response,
                parsed_artifacts=[
                    {"path": f"{ip}/{rel}", "kind": "rtl"}
                    for rel in rtl_files
                    if str(rel).strip()
                ],
            )
            prompt = (
                "Aggregate rtl-gen packet-mode completion log: per-packet LLM calls authored "
                "the RTL slices, and ssot-rtl accepted the resulting DUT compile/lint/audit evidence."
            )
            now = _utc()
            self._write_llm_log(ip, "rtl-gen", response, prompt=prompt, context=context, started_at=now, finished_at=now)
            return
        raw_response = json.dumps(
            {
                "status": "pass",
                "generator": "generic_ssot_rule_seed",
                "reason": "requirements-backed structured SSOT rule contract lowered without an external LLM call",
                "rtl_files": rtl_files,
            },
            sort_keys=True,
        )
        response = LLMResponse(
            stage="rtl-gen",
            model=self.model or "deterministic",
            raw_response=raw_response,
            parsed_artifacts=[
                {"path": f"{ip}/{rel}", "kind": "rtl"}
                for rel in rtl_files
                if str(rel).strip()
            ],
        )
        prompt = (
            "Deterministic rtl-gen seed path: ssot_to_rtl.py generated a single-leaf "
            "RTL implementation from an executable rtl_contract/function_model rule set "
            "after requirements.md established human-owned authority."
        )
        now = _utc()
        self._write_llm_log(ip, "rtl-gen", response, prompt=prompt, context=context, started_at=now, finished_at=now)

    def _apply_artifacts(self, ip: str, artifacts: list[dict[str, Any]]) -> list[str]:
        written: list[str] = []
        for item in artifacts:
            rel = Path(str(item.get("path") or ""))
            if rel.is_absolute() or ".." in rel.parts:
                raise RuntimeError(f"unsafe artifact path from LLM: {rel}")
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(item.get("content") or ""), encoding="utf-8")
            written.append(str(rel))
        return written

    def _ensure_generic_rtl_contract(self, ip: str) -> bool:
        ip_dir = self._ip_dir(ip)
        contract_path = ip_dir / "rtl" / "rtl_contract.json"
        existing = _read_json(contract_path)
        if existing.get("type") == "generic_ssot_rule_rtl_contract":
            return False
        ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
        if not ssot_path.is_file():
            return False
        try:
            doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return False
        rtl_contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
        fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
        transactions = [item for item in fm.get("transactions") or [] if isinstance(item, dict)]
        tx = transactions[0] if transactions else {}

        def _iter_ports() -> list[dict[str, Any]]:
            io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
            rows: list[dict[str, Any]] = []

            def add_from(container: Any) -> None:
                if isinstance(container, dict):
                    ports = container.get("ports")
                    if isinstance(ports, list):
                        for port in ports:
                            if isinstance(port, dict) and str(port.get("name") or "").strip():
                                rows.append(port)
                    for key in ("clock_domains", "resets", "interfaces"):
                        value = container.get(key)
                        if isinstance(value, list):
                            for item in value:
                                add_from(item)
                elif isinstance(container, list):
                    for item in container:
                        add_from(item)

            add_from(io)
            seen: set[str] = set()
            unique: list[dict[str, Any]] = []
            for port in rows:
                name = str(port.get("name") or "").strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                unique.append(port)
            return unique

        ports = _iter_ports()
        input_ports = {
            str(port.get("name"))
            for port in ports
            if str(port.get("direction") or "").strip().lower() == "input"
        }
        output_ports = [
            port for port in ports if str(port.get("direction") or "").strip().lower() == "output"
        ]

        def _first_named(names: list[str], fallback: str) -> str:
            for name in names:
                if name in input_ports:
                    return name
            return fallback

        inferred_clock = _first_named(
            [
                str(rtl_contract.get("clock") or ""),
                "clk",
                "clock",
                "pclk",
            ],
            "clk",
        )
        inferred_reset = _first_named(
            [
                str(rtl_contract.get("reset") or ""),
                "rst_n",
                "reset_n",
                "reset",
                "rst",
            ],
            "rst_n",
        )
        reset_active = str(rtl_contract.get("reset_active") or "").strip().lower()
        if reset_active not in {"low", "high"}:
            reset_active = "low" if inferred_reset.endswith("_n") else "high"

        outputs: list[dict[str, Any]] = []
        for rule in tx.get("output_rules") or []:
            if not isinstance(rule, dict):
                continue
            name = str(rule.get("name") or rule.get("port") or "result")
            port = str(rule.get("port") or name)
            outputs.append({
                "name": name,
                "port": port,
                "expr": rule.get("expr") or "",
                "width": rule.get("width") or 1,
                "source": rule,
            })
        if not outputs:
            for port in output_ports:
                name = str(port.get("name") or "").strip()
                if not name:
                    continue
                outputs.append({
                    "name": name,
                    "port": name,
                    "expr": "",
                    "width": port.get("width") or 1,
                    "source": {"kind": "io_list_output_fallback"},
                })
        state_vars = {
            str(item.get("name")): {"width": item.get("width") or 1, "reset": item.get("reset", 0)}
            for item in fm.get("state_variables") or []
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        }
        state_updates = []
        for item in tx.get("state_updates") or []:
            if not isinstance(item, dict):
                continue
            state_updates.append({
                "name": item.get("name"),
                "expr": item.get("expr") or "",
                "width": item.get("width") or state_vars.get(str(item.get("name")), {}).get("width", 1),
                "source": item,
            })
        payload = {
            "schema_version": 1,
            "type": "generic_ssot_rule_rtl_contract",
            "top": ip,
            "contract": {
                "top": ip,
                "transaction": rtl_contract.get("transaction") or tx.get("id") or "FM_PRIMARY",
                "clock": inferred_clock,
                "reset": inferred_reset,
                "reset_active": reset_active,
                "sample_condition": rtl_contract.get("sample_condition") or "1'b1",
                "input_map": rtl_contract.get("input_map") if isinstance(rtl_contract.get("input_map"), dict) else {},
                "outputs": outputs,
                "state_vars": state_vars,
                "state_updates": state_updates,
                "special_outputs": {
                    key: value
                    for key, value in {
                        "ready_output": rtl_contract.get("ready_output"),
                        "output_valid": rtl_contract.get("output_valid"),
                    }.items()
                    if value
                },
                "source": "SSOT rtl_contract + function_model generated by common_ai_agent headless runner",
            },
        }
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(contract_path, payload)
        return True

    def _check_ssot_contract(self, ip: str, *, emit_gate: bool = True) -> StageResult:
        path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        if not path.is_file():
            if emit_gate:
                q = self._write_human_gate(ip, "ssot-gen", "missing_ssot", decision_needed="LLM did not produce SSOT YAML.")
                return StageResult("ssot-gen", "human_gate", "missing SSOT", artifacts=[str(q.relative_to(self.root))], blocker=str(q.relative_to(self.root)))
            return StageResult("ssot-gen", "human_gate", "missing SSOT")
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            doc = yaml.safe_load(text) or {}
        except Exception as exc:
            if emit_gate:
                q = self._write_human_gate(ip, "ssot-gen", "yaml_parse", decision_needed=f"Repair SSOT YAML parse error: {exc}")
                return StageResult("ssot-gen", "human_gate", str(exc), artifacts=[str(path.relative_to(self.root)), str(q.relative_to(self.root))], blocker=str(q.relative_to(self.root)))
            return StageResult("ssot-gen", "human_gate", str(exc), artifacts=[str(path.relative_to(self.root))])
        missing = []
        if not isinstance(doc, dict):
            missing.append("yaml root object")
        else:
            for key in _ssot_required_keys_for_mode(self.run_mode):
                if key not in doc or doc.get(key) is None or doc.get(key) == "":
                    missing.append(key)
        if missing:
            if emit_gate:
                q = self._write_human_gate(
                    ip,
                    "ssot-gen",
                    "missing_contract",
                    decision_needed=f"Complete SSOT contract fields before downstream generation: {', '.join(missing)}",
                    evidence={"ssot_refs": [f"{ip}/yaml/{ip}.ssot.yaml"], "requirement_refs": [f"{ip}/req/{ip}_requirements.md"], "tool_logs": [], "goal_ids": []},
                )
                return StageResult("ssot-gen", "human_gate", "SSOT contract incomplete", artifacts=[str(path.relative_to(self.root)), str(q.relative_to(self.root))], blocker=str(q.relative_to(self.root)))
            return StageResult("ssot-gen", "human_gate", f"SSOT contract incomplete: {', '.join(missing)}", artifacts=[str(path.relative_to(self.root))])
        validator = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "check_ssot_disk.py"
        if validator.is_file():
            cmd = [sys.executable, str(validator), ip, "--mode", self.run_mode]
            proc = subprocess.run(
                cmd,
                cwd=str(self.root),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
            validator_log = self._ip_dir(ip) / "logs" / "validators" / "check_ssot_disk.log"
            validator_log.parent.mkdir(parents=True, exist_ok=True)
            validator_text = "\n".join(
                part
                for part in [
                    "cmd: " + " ".join(cmd),
                    f"cwd: {self.root}",
                    f"returncode: {proc.returncode}",
                    "stdout:\n" + proc.stdout.strip() if proc.stdout.strip() else "",
                    "stderr:\n" + proc.stderr.strip() if proc.stderr.strip() else "",
                ]
                if part
            )
            validator_log.write_text(validator_text + "\n", encoding="utf-8")
            if proc.returncode != 0:
                first_failure = (proc.stdout.strip() or proc.stderr.strip() or "check_ssot_disk.py failed").splitlines()[0]
                if emit_gate:
                    q = self._write_human_gate(
                        ip,
                        "ssot-gen",
                        "missing_contract",
                        decision_needed=f"Repair SSOT so check_ssot_disk.py passes: {first_failure}",
                        evidence={
                            "ssot_refs": [f"{ip}/yaml/{ip}.ssot.yaml"],
                            "requirement_refs": [f"{ip}/req/{ip}_requirements.md"],
                            "tool_logs": [str(validator_log.relative_to(self.root))],
                            "goal_ids": [],
                        },
                    )
                    return StageResult(
                        "ssot-gen",
                        "human_gate",
                        "SSOT disk validator failed",
                        artifacts=[
                            str(path.relative_to(self.root)),
                            str(validator_log.relative_to(self.root)),
                            str(q.relative_to(self.root)),
                        ],
                        blocker=str(q.relative_to(self.root)),
                    )
                return StageResult(
                    "ssot-gen",
                    "human_gate",
                    f"SSOT disk validator failed: {first_failure}",
                    artifacts=[str(path.relative_to(self.root)), str(validator_log.relative_to(self.root))],
                )
        return StageResult("ssot-gen", "pass", "SSOT contract valid", artifacts=[str(path.relative_to(self.root)), f"{ip}/logs/llm/ssot-gen.json"])

    def _run_deterministic_ssot_repair(self, ip: str, *, reason: str = "") -> bool:
        repair = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
        if not repair.is_file():
            return False
        log = self._ip_dir(ip) / "logs" / "validators" / "repair_ssot_schema.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(repair), ip, "--root", str(self.root), "--mode", self.run_mode]
        self._write_progress(ip, "deterministic_repair_start", stage="ssot-gen", reason=reason)
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(SOURCE_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            log.write_text(
                "\n".join(
                    [
                        "cmd: " + " ".join(cmd),
                        f"cwd: {SOURCE_ROOT}",
                        "returncode: timeout",
                        f"reason: {reason}",
                        "stdout:\n" + str(exc.stdout or "").strip(),
                        "stderr:\n" + str(exc.stderr or "").strip(),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self._write_progress(ip, "deterministic_repair_end", stage="ssot-gen", status="timeout")
            return False
        log.write_text(
            "\n".join(
                part
                for part in [
                    "cmd: " + " ".join(cmd),
                    f"cwd: {SOURCE_ROOT}",
                    f"returncode: {proc.returncode}",
                    f"reason: {reason}",
                    "stdout:\n" + proc.stdout.strip() if proc.stdout.strip() else "",
                    "stderr:\n" + proc.stderr.strip() if proc.stderr.strip() else "",
                ]
                if part
            )
            + "\n",
            encoding="utf-8",
        )
        self._write_progress(
            ip,
            "deterministic_repair_end",
            stage="ssot-gen",
            status="pass" if proc.returncode == 0 else "fail",
        )
        return proc.returncode == 0

    def _validate_ssot(self, ip: str) -> StageResult:
        result = self._check_ssot_contract(ip)
        return self._append(
            result.stage,
            result.status,
            result.message,
            returncode=result.returncode,
            artifacts=result.artifacts,
            blocker=result.blocker,
        )

    def _ssot_repair_prompt(self, ip: str, context: dict[str, Any], failure: StageResult, attempt: int) -> tuple[str, str]:
        ssot_path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        validator_log = self._ip_dir(ip) / "logs" / "validators" / "check_ssot_disk.log"
        current_yaml = ssot_path.read_text(encoding="utf-8", errors="replace") if ssot_path.is_file() else ""
        validator_text = validator_log.read_text(encoding="utf-8", errors="replace") if validator_log.is_file() else ""
        blocker_text = ""
        if failure.blocker:
            blocker_path = self.root / failure.blocker
            if blocker_path.is_file():
                blocker_text = blocker_path.read_text(encoding="utf-8", errors="replace")

        system, _ = self._stage_prompt("ssot-gen", ip, context)
        prompt = (
            f"Repair the SSOT YAML artifact for {ip}. This is repair attempt {attempt}.\n\n"
            "Return exactly one JSON object and nothing else. Do not wrap it in markdown.\n"
            "Success schema:\n"
            "{\n"
            '  "files": [\n'
            f'    {{"path": "{ip}/yaml/{ip}.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}}\n'
            "  ]\n"
            "}\n\n"
            "Repair rules:\n"
            "- Do not use a fixed IP template or hardcoded workaround.\n"
            "- Preserve product semantics from the requirement and current SSOT wherever they are valid.\n"
            "- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.\n"
            "- Fix the concrete parse/validator failures below, and also check for sibling contract defects.\n"
            "- The repaired YAML must pass `bash \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/check_ssot_disk.py\" "
            f"{ip} --root \"$ATLAS_PROJECT_ROOT\" --mode {self.run_mode}`.\n"
            "- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.\n\n"
            f"Failure summary:\n{failure.status}: {failure.message}\n\n"
            f"Blocker artifact:\n{_clip(blocker_text, 6000)}\n\n"
            f"Validator log:\n{_clip(validator_text, 12000)}\n\n"
            f"Requirements:\n{_clip(str(context.get('requirement_text') or ''), 12000)}\n\n"
            f"Current SSOT YAML:\n{_clip(current_yaml, 30000)}"
        )
        return system, prompt

    def _run_ssot_generation(self, ip: str, context: dict[str, Any]) -> StageResult:
        response = self._call_llm("ssot-gen", ip, context)
        if response.status in {"blocked", "human_gate"}:
            return self._append_ssot_llm_gate(ip, response)
        self._apply_artifacts(ip, response.parsed_artifacts)

        deterministic_repair_tried = False
        if self._run_deterministic_ssot_repair(ip, reason="canonicalize_llm_ssot"):
            deterministic_repair_tried = True
        for attempt in range(0, self.ssot_repair_attempts + 1):
            validation = self._check_ssot_contract(ip, emit_gate=False)
            if validation.status == "pass":
                return self._append(
                    validation.stage,
                    validation.status,
                    validation.message,
                    returncode=validation.returncode,
                    artifacts=validation.artifacts,
                    blocker=validation.blocker,
                )
            if not deterministic_repair_tried and not validation.message.startswith("SSOT contract incomplete"):
                deterministic_repair_tried = True
                if self._run_deterministic_ssot_repair(ip, reason=validation.message):
                    validation = self._check_ssot_contract(ip, emit_gate=False)
                    if validation.status == "pass":
                        return self._append(
                            validation.stage,
                            validation.status,
                            validation.message,
                            returncode=validation.returncode,
                            artifacts=validation.artifacts,
                            blocker=validation.blocker,
                        )
            if attempt >= self.ssot_repair_attempts:
                validation = self._check_ssot_contract(ip, emit_gate=True)
                return self._append(
                    validation.stage,
                    validation.status,
                    validation.message,
                    returncode=validation.returncode,
                    artifacts=validation.artifacts,
                    blocker=validation.blocker,
                )

            system, prompt = self._ssot_repair_prompt(ip, context, validation, attempt + 1)
            repair = self._call_llm(
                "ssot-gen",
                ip,
                context,
                system_prompt=system,
                prompt=prompt,
                log_stage=f"ssot-gen-repair-{attempt + 1}",
            )
            if repair.status in {"blocked", "human_gate"}:
                return self._append_ssot_llm_gate(ip, repair, topic=f"repair_{attempt + 1}")
            self._apply_artifacts(ip, repair.parsed_artifacts)
            self._run_deterministic_ssot_repair(ip, reason=f"canonicalize_llm_repair_{attempt + 1}")
        return self._validate_ssot(ip)

    def _append_llm_gate(self, ip: str, stage: str, response: LLMResponse, *, topic: str = "llm") -> StageResult:
        data = _json_from_text(response.raw_response or "") or {}
        gate = data.get("human_gate") if isinstance(data.get("human_gate"), dict) else {}
        if response.status == "blocked" and not gate:
            return self._append(
                stage,
                "blocked",
                response.error or f"{stage} LLM provider blocked before producing artifacts",
                returncode=1,
            )
        q = self._write_human_gate(
            ip,
            stage,
            topic,
            decision_needed=str(gate.get("decision_needed") or gate.get("reason") or response.error or f"{stage} LLM stage blocked"),
            evidence=gate.get("evidence") if isinstance(gate.get("evidence"), dict) else None,
            options=gate.get("options") if isinstance(gate.get("options"), list) else None,
            recommended_default=gate.get("recommended_default") if isinstance(gate.get("recommended_default"), dict) else None,
            downstream_effect=gate.get("downstream_effect") if isinstance(gate.get("downstream_effect"), list) else None,
        )
        return self._append(
            stage,
            "human_gate",
            response.error or f"{stage} LLM returned human gate",
            artifacts=[str(q.relative_to(self.root))],
            blocker=str(q.relative_to(self.root)),
        )

    def _append_ssot_llm_gate(self, ip: str, response: LLMResponse, *, topic: str = "llm") -> StageResult:
        return self._append_llm_gate(ip, "ssot-gen", response, topic=topic)

    def _run_cmd(self, stage: str, cmd: list[str], *, timeout: int = 180) -> StageResult:
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.root),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout,
            )
            status = "pass" if proc.returncode == 0 else "fail"
            msg = "\n".join(
                x for x in [
                    "cmd: " + " ".join(cmd),
                    f"returncode: {proc.returncode}",
                    "stdout:\n" + _clip(proc.stdout.strip()) if proc.stdout.strip() else "",
                    "stderr:\n" + _clip(proc.stderr.strip()) if proc.stderr.strip() else "",
                ] if x
            )
            return self._append(stage, status, msg, returncode=int(proc.returncode))
        except Exception as exc:
            return self._append(stage, "fail", str(exc), returncode=999)

    def _top_name(self, ip: str) -> str:
        path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            top = doc.get("top_module") if isinstance(doc, dict) else {}
            if isinstance(top, dict) and top.get("name"):
                return str(top["name"])
            if isinstance(top, str) and top.strip():
                return top.strip()
        except Exception:
            pass
        return ip

    def _stage_fl_model(self, ip: str, context: dict[str, Any] | None = None) -> StageResult:
        if (os.getenv("ATLAS_FL_AUTHOR", "") or "").strip().lower() == "llm":
            return self._run_fl_llm_authoring(ip, context or {})
        return self._append_engine_result(self.stage_engine.run_stage("ssot-fl-model", ip), "fl-model-gen")

    def _fl_author_prompt(self, ip: str, context: dict[str, Any], baseline_source: str, failures: str = "") -> tuple[str, str]:
        system = (
            "HEADLESS PROVIDER CONTRACT.\n"
            "You are a functional-model (FL oracle) author called by a headless artifact runner. "
            "Return only the machine-readable JSON object requested; no markdown fences, no prose.\n"
        )
        ssot_text = ""
        ssot_path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        if ssot_path.is_file():
            ssot_text = ssot_path.read_text(encoding="utf-8", errors="replace")
        repair_block = (
            f"\nPrevious FL FAILED check_fl_contract with these findings — fix every one without "
            f"weakening the checks:\n{failures}\n"
            if failures
            else ""
        )
        prompt = (
            f"Author the Python functional model (FL oracle) for {ip} at {ip}/model/functional_model.py.\n\n"
            "Return exactly one JSON object:\n"
            f'{{"files":[{{"path":"{ip}/model/functional_model.py","kind":"fl_model","content":"<python source>"}}]}}\n\n'
            "Authority and validation:\n"
            "- The SSOT function_model/cycle_model below is the locked semantic authority; the FL is its "
            "executable projection. A deterministic baseline (generated from the same SSOT) is provided as "
            "reference scaffolding — start from it, keep its module API EXACTLY (SSOT_MODEL, "
            "_default_rule_helpers, FunctionalModel with apply/step/reset/csr_write and dict attributes "
            "state/registers/params, _transactions, run_self_check), and extend the semantics the baseline "
            "cannot express.\n"
            "- Your FL is validated by check_fl_contract.py: interface gate, SSOT semantic-conformance gate "
            "(the validator evaluates every transaction's output_rules/state_updates itself and compares), "
            "and a dual-oracle gate against the baseline. Divergence from the baseline is acceptable ONLY "
            "where the SSOT semantics demand it (the validator reports it; the repair feedback decides).\n\n"
            "REQUIRED semantic extensions beyond the baseline:\n"
            "- csr_write(offset, data) must apply WRITE-TRIGGERED TRANSACTION SEMANTICS, not just mirror "
            "register-bound values: when a write to that offset is the trigger of an SSOT transaction "
            "(e.g. a KICK/strobe register whose write reloads another counter from a CSR), apply that "
            "transaction's state_updates exactly as the RTL write would. Resolve the transaction from the "
            "SSOT preconditions (first declared match against the write context), never hardcode IP names.\n"
            "- Keep transaction-complete semantics: 1-cycle strobe registers end a transaction consumed (0).\n"
            "- state_updates evaluate sequentially (a later update sees an earlier update's new value); "
            "output_rules evaluate against pre-transaction state.\n"
            f"{repair_block}\n"
            f"Locked SSOT YAML (authority):\n{ssot_text[:60000]}\n\n"
            f"Deterministic baseline FL (reference scaffolding, keep its API):\n{baseline_source[:80000]}\n"
        )
        return system, prompt

    def _run_fl_llm_authoring(self, ip: str, context: dict[str, Any]) -> StageResult:
        """LLM-authored FL path (doc/wiki/llm-authored-oracle-architecture.md).

        The deterministic emitter still runs first: its artifacts keep the
        downstream stage battery satisfied and its model becomes the BASELINE
        oracle for the dual-oracle gate. The LLM then authors
        model/functional_model.py; check_fl_contract.py is the trust anchor
        (interface + SSOT conformance + dual oracle), with bounded repair
        rounds fed the gate output verbatim.
        """
        engine_result = self._append_engine_result(self.stage_engine.run_stage("ssot-fl-model", ip), "fl-model-gen")
        if engine_result.status != "pass":
            return engine_result
        model_dir = self._ip_dir(ip) / "model"
        model_path = model_dir / "functional_model.py"
        baseline_path = model_dir / "functional_model_baseline.py"
        if not model_path.is_file():
            return self._append("fl-model-gen", "fail", "deterministic FL missing after engine stage", returncode=1)
        shutil.copyfile(model_path, baseline_path)
        baseline_source = model_path.read_text(encoding="utf-8", errors="replace")
        gate_script = WORKFLOW_ROOT / "fl-model-gen" / "scripts" / "check_fl_contract.py"
        attempts = max(0, int(os.getenv("ATLAS_HEADLESS_FL_REPAIR_ATTEMPTS", "2")))
        failures = ""
        for attempt in range(attempts + 1):
            system, prompt = self._fl_author_prompt(ip, context, baseline_source, failures)
            response = self._call_llm(
                "fl-model-gen", ip, context,
                system_prompt=system, prompt=prompt,
                log_stage=("fl-author" if attempt == 0 else f"fl-author-repair-{attempt}"),
            )
            if response.status in {"blocked", "human_gate"}:
                return self._append_llm_gate(ip, "fl-model-gen", response, topic=f"fl_author_{attempt}")
            self._apply_artifacts(ip, response.parsed_artifacts)
            if model_path.is_file():
                _write_json(
                    model_dir / "fl_authoring_provenance.json",
                    {
                        "schema_version": 1,
                        "type": "fl_authoring_provenance",
                        "ip": ip,
                        "sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                        "authored_by": self.model,
                        "stage": "fl-model-gen",
                        "attempt": attempt,
                        "timestamp": _utc(),
                    },
                )
            gate = subprocess.run(
                [sys.executable, str(gate_script), ip, "--root", str(self.root)],
                cwd=str(self.root), text=True, encoding="utf-8", errors="replace",
                capture_output=True, timeout=180,
            )
            if gate.returncode == 0:
                return self._append(
                    "fl-model-gen", "pass",
                    f"LLM-authored FL passed fl contract gate\n{(gate.stdout or '').strip()}",
                    artifacts=[
                        f"{ip}/model/functional_model.py",
                        f"{ip}/model/functional_model_baseline.py",
                        f"{ip}/model/fl_contract_check.json",
                    ],
                )
            failures = (gate.stdout or gate.stderr or "").strip()
        return self._append(
            "fl-model-gen", "fail",
            f"LLM FL failed contract gate after {attempts + 1} attempts\n{failures}",
            returncode=1, blocker=f"{ip}/model/fl_contract_check.json",
        )

    def _stage_cl_model(self, ip: str) -> StageResult:
        cycle = self._append_engine_result(self.stage_engine.run_stage("ssot-cycle-model", ip), "cl-model-gen")
        if cycle.status == "pass":
            self._append_engine_result(self.stage_engine.run_stage("ssot-dual-fcov", ip), "dual-fcov")
        return cycle

    def _stage_dual_fcov(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("ssot-dual-fcov", ip), "dual-fcov")

    def _stage_equiv_goals(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("ssot-equiv-goals", ip), "equiv-goals")

    def _prepare_rtl_todos_for_llm(self, ip: str, *, audit_rtl: bool = False) -> subprocess.CompletedProcess[str]:
        script = WORKFLOW_ROOT / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
        cmd = [sys.executable, str(script), ip, "--root", str(self.root)]
        if audit_rtl:
            cmd.append("--audit-rtl")
        return subprocess.run(
            cmd,
            cwd=str(self.root),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=90,
        )

    def _update_rtl_context_from_todos(self, ip: str, rtl_context: dict[str, Any]) -> None:
        todo_path = self._ip_dir(ip) / "rtl" / "rtl_todo_plan.json"
        rtl_context.update(
            {
                "rtl_todo_plan_path": f"{ip}/rtl/rtl_todo_plan.json",
                "rtl_todo_plan_sha256": _stable_json_sha256(todo_path),
                "rtl_authoring_plan_path": f"{ip}/rtl/rtl_authoring_plan.json",
                "rtl_authoring_packet_dir": f"{ip}/rtl/authoring_packets",
            }
        )

    def _rtl_authoring_plan(self, ip: str) -> dict[str, Any]:
        return _read_json(self._ip_dir(ip) / "rtl" / "rtl_authoring_plan.json")

    def _rtl_packet_entries(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        packets = plan.get("packets") if isinstance(plan.get("packets"), list) else []
        return [
            packet
            for packet in packets
            if isinstance(packet, dict) and str(packet.get("json") or "").strip()
        ]

    def _rtl_packet_needs_llm(self, packet: dict[str, Any]) -> bool:
        summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
        policy = packet.get("execution_policy") if isinstance(packet.get("execution_policy"), dict) else {}
        if "llm_actionable_open_count" in policy:
            if int(policy.get("llm_actionable_open_count") or 0) > 0:
                return True
            tool_blockers = policy.get("blocked_by_tool_evidence")
            if isinstance(tool_blockers, list):
                for item in tool_blockers:
                    if not isinstance(item, dict):
                        continue
                    gate_kind = str(item.get("gate_kind") or "")
                    reason = str(item.get("reason") or "").lower()
                    if gate_kind in {"dut_compile", "dut_lint"} and any(
                        term in reason for term in ("not clean", "fail", "warning", "error")
                    ):
                        return True
            return False
        if "llm_actionable" in policy:
            return bool(policy.get("llm_actionable"))
        if "open_required_count" in summary:
            return int(summary.get("open_required_count") or 0) > 0
        return True

    def _rtl_plan_has_llm_actionable_draft_work(self, ip: str) -> bool:
        plan = self._rtl_authoring_plan(ip)
        policy = plan.get("execution_policy") if isinstance(plan.get("execution_policy"), dict) else {}
        draft_allowed = bool(policy.get("draft_allowed") or policy.get("deferred_human_qa_allowed"))
        if not draft_allowed:
            return False
        return any(self._rtl_packet_needs_llm(packet) for packet in self._rtl_packet_entries(plan))

    def _rtl_packet_mode_enabled(self, plan: dict[str, Any]) -> bool:
        mode = os.getenv("ATLAS_HEADLESS_RTL_PACKET_MODE", "auto").strip().lower()
        if mode in {"0", "false", "off", "no"}:
            return False
        if mode in {"1", "true", "on", "yes"}:
            return True
        packets = self._rtl_packet_entries(plan)
        summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
        required_tasks = int(summary.get("required_tasks") or summary.get("total_tasks") or summary.get("task_count") or 0)
        task_threshold = max(0, int(os.getenv("ATLAS_HEADLESS_RTL_PACKET_TASK_THRESHOLD", "80")))
        packet_threshold = max(1, int(os.getenv("ATLAS_HEADLESS_RTL_PACKET_COUNT_THRESHOLD", "4")))
        return bool(packets) and (required_tasks > task_threshold or len(packets) > packet_threshold)

    def _rtl_packet_batch_limit(self) -> int:
        raw = os.getenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", str(DEFAULT_RTL_PACKET_MAX_PER_PASS)).strip()
        try:
            configured = max(0, int(raw))
        except ValueError:
            configured = DEFAULT_RTL_PACKET_MAX_PER_PASS
        model_l = str(self.model or "").lower()
        if "glm" in model_l or "kimi" in model_l:
            # GLM/Kimi coding endpoints are more fragile on large RTL packet batches.
            # Use smaller default batches unless the user explicitly forces a lower value.
            return min(configured, max(1, int(os.getenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS_GLM_KIMI", "1"))))
        return configured

    def _rtl_packet_pass_budget(self, plan: dict[str, Any]) -> int:
        raw = os.getenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PASSES", "").strip()
        if raw:
            try:
                return max(1, int(raw))
            except ValueError:
                pass
        _, batch = self._rtl_packet_work_batch(plan)
        work_packets = int(batch.get("work_packets") or 0)
        batch_limit = int(batch.get("packet_batch_limit") or 0)
        if work_packets <= 0 or batch_limit <= 0:
            initial_queue_passes = 1
        else:
            initial_queue_passes = (work_packets + batch_limit - 1) // batch_limit
        return max(self.rtl_repair_attempts + 1, initial_queue_passes + self.rtl_repair_attempts)

    def _rtl_repair_evidence_active(self, ip: str) -> bool:
        if not ip:
            return False
        classify_path = self._ip_dir(ip) / "sim" / "mismatch_classification.json"
        if not classify_path.is_file():
            return False
        if not self._loopable_repair_classifications(ip, "rtl-gen"):
            return False
        try:
            classify_mtime = classify_path.stat().st_mtime
        except OSError:
            return False
        rtl_mtime = 0.0
        for rtl_path in (self._ip_dir(ip) / "rtl").glob("*.sv"):
            try:
                rtl_mtime = max(rtl_mtime, rtl_path.stat().st_mtime)
            except OSError:
                continue
        return classify_mtime >= rtl_mtime

    def _rtl_repair_packets(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        packets = self._rtl_packet_entries(plan)
        repair_packets: list[dict[str, Any]] = []
        for packet in packets:
            packet_id = str(packet.get("packet_id") or Path(str(packet.get("json") or "")).stem)
            kind = str(packet.get("kind") or "").lower()
            owner_file = str(packet.get("owner_file") or "")
            if "human" in packet_id or "contract_blocked" in packet_id:
                continue
            if owner_file.endswith(".sv") or kind.startswith("module") or packet_id.startswith("module__"):
                repair_packets.append(packet)
        return repair_packets

    def _rtl_packet_key(self, packet: dict[str, Any]) -> str:
        return str(packet.get("packet_id") or Path(str(packet.get("json") or "")).stem)

    def _rtl_mix_missing_owner_packets(
        self,
        ip: str,
        selected: list[dict[str, Any]],
        work_packets: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Mix missing top/core owner packets into bounded RTL batches.

        Without this, large starter runs can spend every repair pass on early
        slices for one existing owner file while the canonical top/core files
        remain missing.  Establishing the hierarchy early gives later packet
        repairs concrete RTL to extend instead of repeatedly rewriting one file.
        """
        if not ip or limit <= 0 or len(selected) >= len(work_packets):
            return selected
        ip_dir = self._ip_dir(ip)
        selected_keys = {self._rtl_packet_key(packet) for packet in selected}
        missing_owner_packets: list[dict[str, Any]] = []
        for packet in work_packets:
            key = self._rtl_packet_key(packet)
            if key in selected_keys:
                continue
            owner_file = str(packet.get("owner_file") or "").strip()
            if not owner_file.endswith(".sv"):
                continue
            if (ip_dir / owner_file).is_file():
                continue
            missing_owner_packets.append(packet)
        if not missing_owner_packets:
            return selected

        top = self._top_name(ip)

        def priority(packet: dict[str, Any]) -> tuple[int, str]:
            owner = str(packet.get("owner_module") or "").strip()
            key = self._rtl_packet_key(packet)
            if owner == top or key == f"module__{top}":
                return (0, key)
            if owner.endswith("_core") or key.endswith("_core"):
                return (1, key)
            return (2, key)

        missing_owner_packets.sort(key=priority)
        inject = missing_owner_packets[: min(len(missing_owner_packets), max(1, limit // 2))]
        inject_keys = {self._rtl_packet_key(packet) for packet in inject}
        keep_count = max(0, limit - len(inject))
        mixed: list[dict[str, Any]] = []
        mixed_keys: set[str] = set()
        for packet in selected:
            key = self._rtl_packet_key(packet)
            if key in inject_keys:
                continue
            if len(mixed) >= keep_count:
                break
            mixed.append(packet)
            mixed_keys.add(key)
        for packet in inject:
            key = self._rtl_packet_key(packet)
            if key not in mixed_keys:
                mixed.append(packet)
                mixed_keys.add(key)
        for packet in selected:
            if len(mixed) >= limit:
                break
            key = self._rtl_packet_key(packet)
            if key not in mixed_keys:
                mixed.append(packet)
                mixed_keys.add(key)
        return mixed[:limit]

    def _rtl_packet_work_batch(self, plan: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
        packets = self._rtl_packet_entries(plan)
        work_packets = [packet for packet in packets if self._rtl_packet_needs_llm(packet)]
        ip = str(plan.get("ip") or "")
        if self._rtl_repair_evidence_active(ip):
            for packet in self._rtl_repair_packets(plan):
                if packet not in work_packets:
                    work_packets.append(packet)
        summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
        next_packet_ids = [
            str(item).strip()
            for item in (summary.get("next_llm_packets") if isinstance(summary.get("next_llm_packets"), list) else [])
            if str(item).strip()
        ]
        if next_packet_ids:
            work_by_id = {
                str(packet.get("packet_id") or Path(str(packet.get("json") or "")).stem): packet
                for packet in work_packets
            }
            preferred = [work_by_id[item] for item in next_packet_ids if item in work_by_id]
            if preferred:
                limit = self._rtl_packet_batch_limit()
                selected = preferred[:limit] if limit else preferred
                selected = self._rtl_mix_missing_owner_packets(ip, selected, work_packets, limit)
                return selected, {
                    "total_packets": len(packets),
                    "work_packets": len(work_packets),
                    "selected_packets": len(selected),
                    "skipped_closed_packets": len(packets) - len(work_packets),
                    "deferred_work_packets": max(0, len(work_packets) - len(selected)),
                    "packet_batch_limit": limit,
                }
        primary_packets = [
            packet
            for packet in work_packets
            if str(packet.get("packet_id") or Path(str(packet.get("json") or "")).stem) != "rtl_gate_evidence_closure"
        ]
        # Evidence-closure packets depend on fresh compile/lint/audit results from
        # prior module edits. If module packets are still open, defer closure to
        # the next pass so the stage engine can regenerate tool evidence first.
        eligible_packets = primary_packets if primary_packets else work_packets
        limit = self._rtl_packet_batch_limit()
        selected = eligible_packets[:limit] if limit else eligible_packets
        selected = self._rtl_mix_missing_owner_packets(ip, selected, work_packets, limit)
        return selected, {
            "total_packets": len(packets),
            "work_packets": len(work_packets),
            "selected_packets": len(selected),
            "skipped_closed_packets": len(packets) - len(work_packets),
            "deferred_work_packets": max(0, len(work_packets) - len(selected)),
            "packet_batch_limit": limit,
        }

    def _declared_rtl_files(self, ip: str) -> list[str]:
        path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            doc = {}
        if not isinstance(doc, dict):
            doc = {}
        top = self._top_name(ip)
        files: list[str] = []
        for sm in doc.get("sub_modules") or []:
            if not isinstance(sm, dict):
                continue
            ownership = str(sm.get("ownership") or "manifest").strip().lower()
            if ownership in {"child_ssot", "conceptual", "verification", "coverage"} or sm.get("ssot"):
                continue
            if sm.get("rtl_emit") is False:
                continue
            rel = str(sm.get("file") or "").strip()
            if rel:
                files.append(rel)
        filelist = doc.get("filelist") if isinstance(doc.get("filelist"), dict) else {}
        for rel in filelist.get("rtl") or []:
            if isinstance(rel, str) and rel.strip():
                files.append(rel.strip())
        if not files:
            files.append(f"rtl/{top}.sv")
        seen: set[str] = set()
        out: list[str] = []
        for rel in files:
            if rel and rel not in seen:
                seen.add(rel)
                out.append(rel)
        return out

    def _refresh_rtl_filelist_and_provenance(
        self,
        ip: str,
        *,
        packet_id: str = "",
    ) -> bool:
        ip_dir = self._ip_dir(ip)
        declared = self._declared_rtl_files(ip)
        if declared:
            filelist = ip_dir / "list" / f"{ip}.f"
            filelist.parent.mkdir(parents=True, exist_ok=True)
            filelist.write_text("".join(f"{rel}\n" for rel in declared), encoding="utf-8")

        existing_rtl = [rel for rel in declared if (ip_dir / rel).is_file()]
        if not existing_rtl:
            return False

        plan = self._rtl_authoring_plan(ip)
        provenance_path = ip_dir / "rtl" / "rtl_authoring_provenance.json"
        prior = _read_json(provenance_path)
        valid_packet_ids = {
            str(packet.get("packet_id") or "")
            for packet in self._rtl_packet_entries(plan)
            if str(packet.get("packet_id") or "").strip()
        }
        authored_packets = [
            str(item)
            for item in (prior.get("authoring_packets") if isinstance(prior.get("authoring_packets"), list) else [])
            if str(item).strip() and (not valid_packet_ids or str(item) in valid_packet_ids)
        ]
        if packet_id and packet_id not in authored_packets:
            authored_packets.append(packet_id)
        contract_files = [
            rel for rel in ("rtl/rtl_contract.json",)
            if (ip_dir / rel).is_file()
        ]
        payload = {
            **prior,
            "schema_version": 1,
            "type": "rtl_authoring_provenance",
            "agent": "common_ai_agent",
            "workflow": "rtl-gen",
            "surface": "headless_common_engine",
            "ip": ip,
            "model": self.model,
            "todo_plan_sha256": _stable_json_sha256(ip_dir / "rtl" / "rtl_todo_plan.json")
            or plan.get("todo_plan_sha256"),
            "rtl_files": existing_rtl,
            "contract_files": contract_files,
            "authoring_packets": authored_packets,
            "generation_note": prior.get("generation_note")
            or "Headless common engine recorded LLM-authored RTL artifacts from rtl_authoring_plan packets.",
            "updated_at": _utc(),
        }
        _write_json(provenance_path, payload)
        return True

    def _rtl_interface_digest(self, ip: str) -> str:
        sections: list[str] = []
        ip_dir = self._ip_dir(ip)
        for rel in self._declared_rtl_files(ip):
            path = ip_dir / rel
            if not path.is_file():
                sections.append(f"### {rel}\n<missing>")
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            module_headers = []
            for match in re.finditer(r"\bmodule\s+\w+\b[\s\S]*?\)\s*;", text):
                module_headers.append(match.group(0))
                if len(module_headers) >= 4:
                    break
            if module_headers:
                sections.append(f"### {rel}\n" + "\n\n".join(module_headers))
            else:
                sections.append(f"### {rel}\n" + "\n".join(text.splitlines()[:80]))
        return "\n\n".join(sections) if sections else "<none>"

    def _rtl_file_snapshots(self, ip: str) -> str:
        sections: list[str] = []
        ip_dir = self._ip_dir(ip)
        try:
            per_file_limit = max(4000, int(os.getenv("ATLAS_HEADLESS_RTL_SNAPSHOT_FILE_CHARS", "22000")))
        except ValueError:
            per_file_limit = 22000
        try:
            total_limit = max(per_file_limit, int(os.getenv("ATLAS_HEADLESS_RTL_SNAPSHOT_TOTAL_CHARS", "70000")))
        except ValueError:
            total_limit = 70000
        used = 0
        for rel in self._declared_rtl_files(ip):
            if used >= total_limit:
                sections.append(f"### {rel}\n<truncated: total RTL snapshot budget exhausted>")
                continue
            path = ip_dir / rel
            if not path.is_file():
                text = "<missing>"
            else:
                text = path.read_text(encoding="utf-8", errors="replace")
            remaining = max(0, total_limit - used)
            clipped = _clip(text, min(per_file_limit, remaining))
            used += len(clipped)
            sections.append(f"### {rel}\n{clipped}")
        return "\n\n".join(sections) if sections else "<none>"

    def _rtl_gate_audit_digest(self, ip: str) -> dict[str, Any]:
        ip_dir = self._ip_dir(ip)
        todo_plan = _read_json(ip_dir / "rtl" / "rtl_todo_plan.json")
        compile_report = _read_json(ip_dir / "rtl" / "rtl_compile.json")
        lint_report = _read_json(ip_dir / "lint" / "dut_lint.json")

        todo_completion = todo_plan.get("todo_completion") if isinstance(todo_plan.get("todo_completion"), dict) else {}
        static_evidence = todo_plan.get("static_rtl_evidence") if isinstance(todo_plan.get("static_rtl_evidence"), dict) else {}
        signal_flow = (
            todo_plan.get("manifest_signal_flow_evidence")
            if isinstance(todo_plan.get("manifest_signal_flow_evidence"), dict)
            else {}
        )
        hierarchy = (
            todo_plan.get("manifest_hierarchy_evidence")
            if isinstance(todo_plan.get("manifest_hierarchy_evidence"), dict)
            else {}
        )
        open_tasks = todo_completion.get("open_tasks") if isinstance(todo_completion.get("open_tasks"), list) else []
        missing_tasks = static_evidence.get("missing_tasks") if isinstance(static_evidence.get("missing_tasks"), list) else []
        signal_issues = signal_flow.get("issues") if isinstance(signal_flow.get("issues"), list) else []
        hierarchy_issues = hierarchy.get("issues") if isinstance(hierarchy.get("issues"), list) else []

        lint_diagnostics: list[Any] = []
        tool_results = lint_report.get("tool_results") if isinstance(lint_report.get("tool_results"), list) else []
        for result in tool_results:
            if isinstance(result, dict):
                diagnostics = result.get("diagnostics") if isinstance(result.get("diagnostics"), list) else []
                for diag in diagnostics:
                    lint_diagnostics.append(diag)

        return {
            "source": f"{ip}/rtl/rtl_todo_plan.json",
            "gate": todo_plan.get("gate") if isinstance(todo_plan.get("gate"), dict) else {},
            "open_required_tasks": open_tasks[:48],
            "static_missing_tasks": missing_tasks[:48],
            "manifest_signal_flow_issues": signal_issues[:48],
            "manifest_hierarchy_issues": hierarchy_issues[:48],
            "compile": {
                "source": f"{ip}/rtl/rtl_compile.json",
                "present": bool(compile_report),
                "passed": compile_report.get("passed"),
                "returncode": compile_report.get("returncode"),
                "errors": compile_report.get("errors"),
                "diagnostics": compile_report.get("diagnostics"),
                "style_violations": compile_report.get("style_violations"),
                "style_violation_details": (
                    compile_report.get("style_violation_details")
                    if isinstance(compile_report.get("style_violation_details"), list)
                    else []
                )[:24],
            },
            "lint": {
                "source": f"{ip}/lint/dut_lint.json",
                "present": bool(lint_report),
                "passed": lint_report.get("passed"),
                "returncode": lint_report.get("returncode"),
                "errors": lint_report.get("errors"),
                "warnings": lint_report.get("warnings"),
                "suppression_violation_count": lint_report.get("suppression_violation_count"),
                "style_violation_count": lint_report.get("style_violation_count"),
                "diagnostics": lint_diagnostics[:48],
                "repair_hints": _rtl_lint_repair_hints(lint_diagnostics)[:48],
            },
        }

    def _canonical_repair_owner(self, owner: str) -> str:
        key = str(owner or "").strip().lower().replace("_", "-")
        mapping = {
            "rtl": "rtl-gen",
            "gen-rtl": "rtl-gen",
            "rtl-gen": "rtl-gen",
            "ssot-rtl": "rtl-gen",
            "tb": "tb-gen",
            "testbench": "tb-gen",
            "scoreboard": "tb-gen",
            "tb-gen": "tb-gen",
            "fl": "fl-model-gen",
            "fl-model": "fl-model-gen",
            "fl-model-gen": "fl-model-gen",
            "coverage": "coverage",
            "cov": "coverage",
            "sim": "sim",
            "sim-debug": "sim-debug",
        }
        return mapping.get(key, _canonical_headless_stage(key))

    def _loopable_repair_classifications(self, ip: str, owner_workflow: str = "") -> list[dict[str, Any]]:
        path = self._ip_dir(ip) / "sim" / "mismatch_classification.json"
        doc = _read_json(path)
        raw_items = doc.get("classifications") if isinstance(doc.get("classifications"), list) else []
        wanted = self._canonical_repair_owner(owner_workflow) if owner_workflow else ""
        items: list[dict[str, Any]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            if item.get("llm_loop_allowed") is not True:
                continue
            if not str(item.get("repair_prompt") or "").strip():
                continue
            owner = self._canonical_repair_owner(str(item.get("owner") or ""))
            if wanted and owner != wanted:
                continue
            items.append({**item, "owner": owner})
        return items

    def _repair_classification_signature(self, items: list[dict[str, Any]]) -> str:
        normalized: list[dict[str, Any]] = []
        for item in items:
            evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
            rows = evidence.get("scoreboard_rows") if isinstance(evidence.get("scoreboard_rows"), list) else []
            first_row = rows[0] if rows and isinstance(rows[0], dict) else {}
            normalized.append(
                {
                    "goal_id": item.get("goal_id"),
                    "owner": self._canonical_repair_owner(str(item.get("owner") or "")),
                    "classification": item.get("classification"),
                    "reason": item.get("reason"),
                    "fl_expected": evidence.get("fl_expected") or first_row.get("fl_expected"),
                    "rtl_observed": evidence.get("rtl_observed") or first_row.get("rtl_observed"),
                }
            )
        return _sha(json.dumps(sorted(normalized, key=lambda row: str(row.get("goal_id") or "")), sort_keys=True, default=str))

    def _rtl_repair_evidence_digest(self, ip: str) -> dict[str, Any]:
        items = self._loopable_repair_classifications(ip, "rtl-gen")
        digest: list[dict[str, Any]] = []
        for item in items[:24]:
            evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
            rows = evidence.get("scoreboard_rows") if isinstance(evidence.get("scoreboard_rows"), list) else []
            digest.append(
                {
                    "goal_id": item.get("goal_id"),
                    "classification": item.get("classification"),
                    "owner": item.get("owner"),
                    "reason": item.get("reason"),
                    "repair_prompt": item.get("repair_prompt"),
                    "evidence": {
                        "ssot_refs": evidence.get("ssot_refs") or [],
                        "fl_expected": evidence.get("fl_expected"),
                        "rtl_observed": evidence.get("rtl_observed"),
                        "scoreboard_rows": rows[:4],
                        "sim_result": evidence.get("sim_result"),
                    },
                }
            )
        return {
            "source": f"{ip}/sim/mismatch_classification.json",
            "status": "present" if digest else "none",
            "owner_workflow": "rtl-gen",
            "items": digest,
        }

    def _rtl_packet_parallel_worker_count(self) -> int:
        raw = os.getenv("ATLAS_HEADLESS_RTL_PACKET_PARALLEL_WORKERS", "").strip()
        if not raw:
            raw = os.getenv("ATLAS_RTL_PACKET_WORKERS", "4").strip()
        try:
            return max(1, int(raw))
        except ValueError:
            return 1

    def _rtl_packet_parallel_enabled(self, packets: list[dict[str, Any]]) -> bool:
        mode = os.getenv("ATLAS_HEADLESS_RTL_PACKET_PARALLEL", "0").strip().lower()
        if mode in {"0", "off", "false", "no"}:
            return False
        if mode in {"1", "on", "true", "yes"}:
            return self._rtl_packet_parallel_worker_count() > 1 and len(packets) > 1
        if mode == "auto":
            return self._rtl_packet_parallel_worker_count() > 1 and len(packets) > 2
        return False

    def _rtl_packets_parallel_safe(self, packets: list[dict[str, Any]]) -> bool:
        """Only independent module-owner packets may be authored concurrently."""

        owner_files: set[str] = set()
        for packet in packets:
            owner_file = str(packet.get("owner_file") or "").strip()
            if not self._rtl_packet_parallel_safe(packet):
                return False
            if owner_file in owner_files:
                return False
            owner_files.add(owner_file)
        return True

    def _rtl_packet_parallel_safe(self, packet: dict[str, Any]) -> bool:
        packet_id = str(packet.get("packet_id") or Path(str(packet.get("json") or "")).stem)
        kind = str(packet.get("kind") or "").strip().lower()
        owner_file = str(packet.get("owner_file") or "").strip()
        if kind != "module" or not owner_file:
            return False
        if packet_id.startswith("rtl_gate_") or "evidence_closure" in packet_id:
            return False
        return True

    def _rtl_packet_context(
        self,
        ip: str,
        rtl_context: dict[str, Any],
        packet: dict[str, Any],
        index: int,
        batch: dict[str, int],
    ) -> tuple[str, dict[str, Any]]:
        packet_id = str(packet.get("packet_id") or Path(str(packet.get("json") or f"packet_{index}")).stem)
        packet_context = dict(rtl_context)
        packet_context.update(
            {
                "rtl_packet_mode": True,
                "rtl_packet_index": index,
                "rtl_packet_count": batch["selected_packets"],
                "rtl_packet_total_count": batch["total_packets"],
                "rtl_packet_work_count": batch["work_packets"],
                "rtl_packet_selected_count": batch["selected_packets"],
                "rtl_packet_deferred_work_count": batch["deferred_work_packets"],
                "rtl_packet_batch_limit": batch["packet_batch_limit"],
                "rtl_packet_skipped_closed_count": batch["skipped_closed_packets"],
                "rtl_packet_id": packet_id,
                "rtl_packet_path": f"{ip}/{packet.get('json')}",
                "rtl_packet_kind": packet.get("kind"),
                "rtl_packet_owner_module": packet.get("owner_module"),
                "rtl_packet_owner_file": packet.get("owner_file"),
            }
        )
        return packet_id, packet_context

    def _call_rtl_packet_llm(
        self,
        ip: str,
        rtl_context: dict[str, Any],
        plan: dict[str, Any],
        packet: dict[str, Any],
        index: int,
        batch: dict[str, int],
        *,
        attempt: int,
    ) -> tuple[int, str, dict[str, Any], LLMResponse]:
        packet_id, packet_context = self._rtl_packet_context(ip, rtl_context, packet, index, batch)
        system, prompt = self._rtl_packet_prompt(ip, packet_context, plan, packet, attempt=attempt)
        log_stage = (
            f"rtl-gen-packet-{index:02d}-{_safe_name(packet_id)}"
            if attempt == 0
            else f"rtl-gen-repair-{attempt}-packet-{index:02d}-{_safe_name(packet_id)}"
        )
        response = self._call_llm(
            "rtl-gen",
            ip,
            packet_context,
            system_prompt=system,
            prompt=prompt,
            log_stage=log_stage,
        )
        return index, packet_id, packet_context, response

    def _rtl_packet_prompt(
        self,
        ip: str,
        context: dict[str, Any],
        plan: dict[str, Any],
        packet: dict[str, Any],
        *,
        attempt: int,
    ) -> tuple[str, str]:
        system, base_prompt = self._stage_prompt("rtl-gen", ip, context)
        packet_rel = str(packet.get("json") or "").strip()
        packet_md_rel = str(packet.get("markdown") or "").strip()
        packet_path = self._ip_dir(ip) / packet_rel
        packet_md_path = self._ip_dir(ip) / packet_md_rel
        packet_json = packet_path.read_text(encoding="utf-8", errors="replace") if packet_path.is_file() else "{}"
        packet_md = packet_md_path.read_text(encoding="utf-8", errors="replace") if packet_md_path.is_file() else ""
        packet_doc = _read_json(packet_path) if packet_path.is_file() else {}
        owner_file_rel = str(packet.get("owner_file") or "").strip()
        owner_file_path = self._ip_dir(ip) / owner_file_rel if owner_file_rel else None
        owner_file_text = (
            owner_file_path.read_text(encoding="utf-8", errors="replace")
            if owner_file_path is not None and owner_file_path.is_file()
            else ""
        )
        packet_id = str(packet.get("packet_id") or Path(packet_rel).stem)
        packet_kind = str(packet.get("kind") or "").strip().lower()
        is_gate_packet = packet_kind == "gate" or packet_id.startswith("rtl_gate_")
        rtl_interface_digest = self._rtl_interface_digest(ip)
        rtl_gate_audit_digest = self._rtl_gate_audit_digest(ip)
        lint_repair_hints = []
        if isinstance(rtl_gate_audit_digest.get("lint"), dict):
            lint_repair_hints = rtl_gate_audit_digest["lint"].get("repair_hints") or []
        lint_repair_directives = _format_rtl_lint_repair_hints(lint_repair_hints)
        rtl_snapshots_text = self._rtl_file_snapshots(ip) if is_gate_packet else "<included only for gate/tool-evidence packets>"
        tool_artifact_sections: list[str] = []
        packet_policy = packet_doc.get("execution_policy") if isinstance(packet_doc.get("execution_policy"), dict) else {}
        tool_plans = packet_policy.get("tool_evidence_plan") if isinstance(packet_policy.get("tool_evidence_plan"), list) else []
        seen_tool_artifacts: set[str] = set()
        for tool_plan in tool_plans:
            if not isinstance(tool_plan, dict):
                continue
            for rel in tool_plan.get("artifacts") or []:
                rel_s = str(rel or "").strip()
                if not rel_s or rel_s in seen_tool_artifacts:
                    continue
                seen_tool_artifacts.add(rel_s)
                path = self.root / rel_s
                if not path.is_file():
                    tool_artifact_sections.append(f"### {rel_s}\n<missing>")
                    continue
                tool_artifact_sections.append(
                    f"### {rel_s}\n{_clip(path.read_text(encoding='utf-8', errors='replace'), 16000)}"
                )
        tool_artifacts_text = "\n\n".join(tool_artifact_sections) if tool_artifact_sections else "<none>"
        packet_char_limit = max(8000, int(os.getenv("ATLAS_HEADLESS_RTL_PACKET_MAX_CHARS", "50000")))
        packet_digest = []
        for item in self._rtl_packet_entries(plan):
            item_summary = item.get("summary") if isinstance(item.get("summary"), dict) else {}
            item_policy = item.get("execution_policy") if isinstance(item.get("execution_policy"), dict) else {}
            packet_digest.append(
                {
                    "packet_id": item.get("packet_id"),
                    "kind": item.get("kind"),
                    "owner_module": item.get("owner_module"),
                    "owner_file": item.get("owner_file"),
                    "json": item.get("json"),
                    "required_count": item_summary.get("required_count"),
                    "open_required_count": item_summary.get("open_required_count"),
                    "status_counts": item_summary.get("status_counts"),
                    "llm_actionable_open_count": item_policy.get("llm_actionable_open_count"),
                    "human_locked_open_count": item_policy.get("human_locked_open_count"),
                }
            )
        reference_profile = plan.get("reference_profile") if isinstance(plan.get("reference_profile"), dict) else {}
        reference_profile_digest = {
            key: reference_profile.get(key)
            for key in REFERENCE_PROFILE_PROMPT_KEYS
            if key in reference_profile
        }
        repair_evidence_digest = self._rtl_repair_evidence_digest(ip)
        plan_overview = {
            "type": plan.get("type"),
            "ip": plan.get("ip"),
            "top": plan.get("top"),
            "summary": plan.get("summary"),
            "policy": plan.get("policy"),
            "target_scale": plan.get("target_scale"),
            "reference_profile": reference_profile_digest,
            "execution_policy": plan.get("execution_policy"),
            "packets": packet_digest,
            "todo_plan_sha256": plan.get("todo_plan_sha256"),
            "sim_debug_repair_evidence": {
                "source": repair_evidence_digest.get("source"),
                "owner_workflow": repair_evidence_digest.get("owner_workflow"),
                "items": len(repair_evidence_digest.get("items") or []),
            },
        }
        ssot_latency_contract: dict[str, Any] = {}
        ssot_bus_lane_policy: dict[str, Any] = {}
        ssot_prompt_text = ""
        ssot_path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        if ssot_path.is_file():
            ssot_prompt_text = ssot_path.read_text(encoding="utf-8", errors="replace")
            try:
                ssot_doc = yaml.safe_load(ssot_prompt_text) or {}
            except Exception:
                ssot_doc = {}
            ssot_bus_lane_policy = _ssot_bus_lane_policy(ssot_doc if isinstance(ssot_doc, dict) else {})
            cm = ssot_doc.get("cycle_model") if isinstance(ssot_doc.get("cycle_model"), dict) else {}
            rtl_contract = ssot_doc.get("rtl_contract") if isinstance(ssot_doc.get("rtl_contract"), dict) else {}
            timing = ssot_doc.get("timing") if isinstance(ssot_doc.get("timing"), dict) else {}
            ssot_latency_contract = {
                "cycle_model.latency": cm.get("latency"),
                "cycle_model.pipeline": cm.get("pipeline"),
                "rtl_contract.sample_condition": rtl_contract.get("sample_condition"),
                "rtl_contract.output_valid": rtl_contract.get("output_valid"),
                "timing.latency_budget": timing.get("latency_budget"),
                "observable_latency_rule": (
                    "For valid/ready transactions, latency is counted from the accepting clock edge "
                    "to the first ReadOnly observation of matching result/output_valid. latency=1 means "
                    "registered outputs for the accepted transaction are visible after that one edge; "
                    "an input-register stage followed by a result-register stage is latency=2."
                ),
                "latency_1_required_rtl_shape": (
                    "When cycle_model.latency is 1, compute output_rules from the current accepted inputs "
                    "inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same "
                    "branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later "
                    "S1_RESULT clock edge; that is a forbidden latency-2 implementation."
                ),
            }
        schema = (
            "{\n"
            '  "files": [\n'
            f'    {{"path": "{ip}/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"}},\n'
            f'    {{"path": "{ip}/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"}},\n'
            f'    {{"path": "{ip}/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}}\n'
            "  ]\n"
            "}\n"
        )
        prompt = (
            f"RTL-GEN PACKET MODE for {ip}. Packet attempt {attempt}.\n\n"
            + (
                # Phase-2 finding: a repair model answered the same port-map
                # diagnostic with comments two rounds running because the
                # diagnostic never said what ACTION closes it. Repair rounds
                # get explicit action semantics.
                "REPAIR SEMANTICS: the diagnostics below are work orders, not commentary prompts. "
                "Every fix must change executable RTL — port maps, net names, assignments, logic. "
                "Adding or editing comments never closes a diagnostic. For connection-contract "
                "diagnostics ('RTL named port-map expression does not match SSOT connection signal "
                "terms'), rewire the named instance port to the SSOT signal term, or rename the "
                "local net / route it through a continuous assign so the SSOT term appears in live "
                "wiring.\n\n"
                if attempt > 0
                else ""
            )
            + "Return exactly one JSON object and nothing else. Do not wrap it in markdown.\n"
            "Success schema:\n"
            f"{schema}\n"
            "If this packet exposes a missing locked-truth decision, return a human_gate object instead of "
            "inventing SSOT, FL, coverage, interface, or performance semantics.\n\n"
            "Packet execution rules:\n"
            "- Author only RTL-owned artifacts for the current packet, plus local notes/contract metadata when useful.\n"
            "- Do not edit SSOT YAML, FunctionalModel, coverage goals, protocol assertions, performance targets, or requirements.\n"
            "- You cannot read files from the repo during this turn. The required locked SSOT facts are embedded below; do not return requires/missing-file JSON for those paths.\n"
            "- Do not emit placeholder, heartbeat-only, alive-only, or tie-off-only RTL to satisfy a manifest.\n"
            "- For production-profile packets, add real SSOT-scaled implementation depth: state/control/data movement, nonconstant logic, and child wiring must be proportional to the packet tasks.\n"
            "- For a module packet, focus on owner_file and every task content/detail/criteria/source_ref in the packet.\n"
            "- If current owner_file content is provided, preserve prior slice logic and merge the new behavior; do not replace the file with a partial slice-only module.\n"
            "- For mixed packets with locked-truth blockers, keep authoring LLM-actionable RTL/test/evidence work and leave the locked-truth tasks open.\n"
            "- Return human_gate only when no LLM-actionable open work remains or the missing locked-truth decision blocks correct RTL authoring.\n"
            "- For rtl_gate_evidence_closure, repair only LLM-actionable evidence gaps revealed by compile/lint/audit output; do not claim PASS.\n"
            "- If rtl_gate_evidence_closure includes pending connection_contract_suggestions, you may use them as draft RTL wiring candidates to instantiate child modules and close hierarchy/signal-flow evidence, but they remain pending QA and must not be treated as SSOT authority.\n"
            "- For rtl_gate_tool_evidence, do not fabricate compile/lint/sim/coverage artifacts. If compile/lint evidence already exists and is not clean, repair the owner RTL that caused the diagnostics; the runner will rerun tools afterward.\n"
            "- Gate/tool-evidence packets may edit any declared RTL file implicated by the audit digest, compile diagnostics, lint diagnostics, or static-evidence gaps; current owner_file is the gate coordinator, not an edit restriction.\n"
            "- Keep generated RTL lint-clean: eliminate Verilator warnings, unused evidence-only helper signals, unused parameters, and the no_parameterized_part_select_in_procedural_block style violation by adding real helper wires or real signal consumption.\n"
            "- Treat lint.repair_hints as mandatory repair guidance. For UNUSED* diagnostics, prefer narrowing/removing helper declarations or real functional connections; do not add marker-only reductions, lint suppressions, or evidence-only consumes.\n"
            "- If lint.repair_hints names a signal, the emitted RTL must make that exact reported diagnostic disappear; renaming or copying the signal while leaving the same unused upper-bit pattern open is a failed repair.\n"
            "- For narrower GPIO/output consumers, connect from the full producer slice, such as producer[GPIO_WIDTH-1:0], or use a GPIO_WIDTH helper; do not create another DATA_WIDTH masked/full helper whose upper bits remain unused.\n"
            "- Static evidence terms are search/audit hints, not required signal names. Do not declare a wire/reg whose only purpose is to spell a TODO term; implement the behavior with real protocol/datapath/control logic and remove marker signals that lint reports unused.\n"
            "- For rtl_gate_contract_blocked, return human_gate only; missing SSOT connection contracts block correct top integration semantics.\n"
            "- For rtl_gate_human_closure, return human_gate only; do not invent or edit human-locked authority.\n"
            "- The headless runner will refresh filelist/provenance from LLM-authored artifacts after each packet.\n\n"
            f"Current packet: {packet.get('packet_id') or packet_rel}\n"
            f"kind: {packet.get('kind')}\n"
            f"work queue: {context.get('rtl_packet_index', 0) + 1}/{context.get('rtl_packet_count', '?')} active packets"
            f" ({context.get('rtl_packet_skipped_closed_count', 0)} closed packets skipped from {context.get('rtl_packet_total_count', context.get('rtl_packet_count', '?'))} total)\n"
            f"batch limit: {context.get('rtl_packet_batch_limit', 0)}; deferred active packets after this batch: {context.get('rtl_packet_deferred_work_count', 0)}\n"
            f"owner_module: {packet.get('owner_module') or ''}\n"
            f"owner_file: {packet.get('owner_file') or ''}\n\n"
            f"SSOT observable latency contract:\n{_clip(json.dumps(ssot_latency_contract, indent=2, sort_keys=True), 12000)}\n\n"
            f"SSOT bus/byte-lane policy:\n{_clip(json.dumps(ssot_bus_lane_policy, indent=2, sort_keys=True), 12000)}\n\n"
            f"Locked SSOT YAML excerpt ({ip}/yaml/{ip}.ssot.yaml):\n{_clip(ssot_prompt_text, 40000) if ssot_prompt_text else '<missing>'}\n\n"
            f"Base rtl-gen contract:\n{base_prompt}\n\n"
            f"Authoring plan overview:\n{_clip(json.dumps(plan_overview, indent=2, sort_keys=True), 30000)}\n\n"
            f"Current sim-debug owner repair evidence:\n{_clip(json.dumps(repair_evidence_digest, indent=2, sort_keys=True), 24000)}\n\n"
            f"Current owner RTL file ({owner_file_rel or '<none>'}):\n{_clip(owner_file_text, 30000) if owner_file_text else '<missing or not authored yet>'}\n\n"
            f"Current RTL module interface digest (all manifest RTL files):\n{_clip(rtl_interface_digest, 24000)}\n\n"
            f"Current mandatory lint repair directives:\n{_clip(lint_repair_directives, 12000)}\n\n"
            f"Current RTL gate audit digest:\n{_clip(json.dumps(rtl_gate_audit_digest, indent=2, sort_keys=True), 26000)}\n\n"
            f"Current RTL file snapshots for gate/tool-evidence repair:\n{_clip(rtl_snapshots_text, 72000)}\n\n"
            f"Current tool evidence artifacts referenced by this packet:\n{tool_artifacts_text}\n\n"
            f"Current packet JSON ({packet_rel}):\n{_clip(packet_json, packet_char_limit)}\n\n"
            f"Current packet Markdown ({packet_md_rel}):\n{_clip(packet_md, 16000)}"
        )
        return system, prompt

    def _run_rtl_packet_llm_pass(
        self,
        ip: str,
        rtl_context: dict[str, Any],
        *,
        attempt: int,
    ) -> StageResult | None:
        plan = self._rtl_authoring_plan(ip)
        work_packets, batch = self._rtl_packet_work_batch(plan)

        def consume(packet_results: list[tuple[int, str, dict[str, Any], LLMResponse]]) -> StageResult | None:
            for _index, packet_id, _packet_context, response in sorted(packet_results, key=lambda item: item[0]):
                if _response_declares_empty_files(response):
                    continue
                if response.status in {"blocked", "human_gate"}:
                    return self._append_llm_gate(ip, "rtl-gen", response, topic=f"packet_{_safe_name(packet_id)}")
                if not response.parsed_artifacts:
                    return self._append(
                        "rtl-gen",
                        "blocked",
                        f"rtl-gen packet {packet_id} produced no files[] artifacts; retry the packet instead of treating truncated output as progress",
                        returncode=1,
                    )
                self._apply_artifacts(ip, response.parsed_artifacts)
                self._refresh_rtl_filelist_and_provenance(ip, packet_id=packet_id)
            return None

        def run_parallel_segment(indexed_packets: list[tuple[int, dict[str, Any]]]) -> StageResult | None:
            if not indexed_packets:
                return None
            worker_count = min(self._rtl_packet_parallel_worker_count(), len(indexed_packets))
            if worker_count <= 1 or len(indexed_packets) <= 1:
                return consume([
                    self._call_rtl_packet_llm(ip, rtl_context, plan, packet, index, batch, attempt=attempt)
                    for index, packet in indexed_packets
                ])

            lanes: dict[str, list[tuple[int, dict[str, Any]]]] = {}
            for item in indexed_packets:
                owner_file = str(item[1].get("owner_file") or "").strip()
                lanes.setdefault(owner_file, []).append(item)

            self._write_progress(
                ip,
                "rtl_packet_parallel_start",
                stage="rtl-gen",
                packets=len(indexed_packets),
                workers=worker_count,
            )
            while lanes:
                wave: list[tuple[int, dict[str, Any]]] = []
                for owner_file in list(lanes.keys()):
                    if len(wave) >= worker_count:
                        break
                    lane = lanes[owner_file]
                    wave.append(lane.pop(0))
                    if not lane:
                        del lanes[owner_file]
                with ThreadPoolExecutor(max_workers=len(wave), thread_name_prefix="rtl_packet_worker") as executor:
                    futures = [
                        executor.submit(
                            self._call_rtl_packet_llm,
                            ip,
                            rtl_context,
                            plan,
                            packet,
                            index,
                            batch,
                            attempt=attempt,
                        )
                        for index, packet in wave
                    ]
                    gate = consume([future.result() for future in as_completed(futures)])
                    if gate is not None:
                        return gate
            self._write_progress(
                ip,
                "rtl_packet_parallel_end",
                stage="rtl-gen",
                packets=len(indexed_packets),
                workers=worker_count,
            )
            return None

        if self._rtl_packet_parallel_enabled(work_packets):
            segment: list[tuple[int, dict[str, Any]]] = []
            for index, packet in enumerate(work_packets):
                if self._rtl_packet_parallel_safe(packet):
                    segment.append((index, packet))
                    continue
                gate = run_parallel_segment(segment)
                if gate is not None:
                    return gate
                segment = []
                gate = consume([
                    self._call_rtl_packet_llm(ip, rtl_context, plan, packet, index, batch, attempt=attempt)
                ])
                if gate is not None:
                    return gate
            return run_parallel_segment(segment)

        return consume([
            self._call_rtl_packet_llm(ip, rtl_context, plan, packet, index, batch, attempt=attempt)
            for index, packet in enumerate(work_packets)
        ])

    def _rtl_result_repairable_by_llm(self, result: StageEngineResult) -> bool:
        if result.status == "fail":
            return True
        blocked_doc = result.metadata.get("rtl_blocked") if isinstance(result.metadata, dict) else None
        questions = blocked_doc.get("questions") if isinstance(blocked_doc, dict) and isinstance(blocked_doc.get("questions"), list) else []
        question_ids = {str(q.get("id") or "") for q in questions if isinstance(q, dict)}
        rtl_owned_ids = {
            "RTL_TODO_PLAN_MISSING",
            "DETERMINISTIC_RTL_ARTIFACT_NOT_APPROVED",
            "LLM_RTL_IMPLEMENTATION_REQUIRED",
            "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
        }
        draft_compatible_ids = rtl_owned_ids | {"RTL_TARGET_SCALE_POLICY"}
        if question_ids and bool(question_ids & rtl_owned_ids) and question_ids <= draft_compatible_ids:
            return True
        if question_ids and question_ids <= {"RTL_TARGET_SCALE_POLICY"}:
            return self._rtl_plan_has_llm_actionable_draft_work(result.ip)
        message = result.message.lower()
        return (
            "llm-authored rtl evidence is missing or stale" in message
            or "rtl-gen waiting for llm-authored rtl" in message
            or "rtl result] fail - llm-authored rtl needs rtl-gen repair" in message
        )

    def _stage_rtl_gen(self, ip: str, context: dict[str, Any]) -> StageResult:
        try:
            prederive = self._prepare_rtl_todos_for_llm(ip, audit_rtl=True)
        except Exception as exc:
            return self._append("rtl-gen", "fail", f"failed to derive SSOT RTL TODO plan before LLM call: {exc}", returncode=999)
        if prederive.returncode not in {0, 1} or not (self._ip_dir(ip) / "rtl" / "rtl_authoring_plan.json").is_file():
            result = self.stage_engine.run_stage("ssot-rtl", ip)
            if result.status == "pass":
                self._ensure_generic_rtl_contract(ip)
                self._write_deterministic_rtl_seed_log(ip, context)
            return self._append_engine_result(result, "rtl-gen", blocker=result.blocker)

        rtl_context = dict(context)
        self._update_rtl_context_from_todos(ip, rtl_context)
        if self._refresh_rtl_filelist_and_provenance(ip):
            try:
                prederive = self._prepare_rtl_todos_for_llm(ip, audit_rtl=True)
            except Exception as exc:
                return self._append("rtl-gen", "fail", f"failed to refresh RTL TODO plan after provenance update: {exc}", returncode=999)
            if prederive.returncode not in {0, 1}:
                result = self.stage_engine.run_stage("ssot-rtl", ip)
                if result.status == "pass":
                    self._ensure_generic_rtl_contract(ip)
                    self._write_deterministic_rtl_seed_log(ip, rtl_context)
                return self._append_engine_result(result, "rtl-gen", blocker=result.blocker)
            self._update_rtl_context_from_todos(ip, rtl_context)
        packet_mode = self._rtl_packet_mode_enabled(self._rtl_authoring_plan(ip))
        result: StageEngineResult | None = None
        attempt_limit = self.rtl_repair_attempts + 1
        if packet_mode:
            attempt_limit = self._rtl_packet_pass_budget(self._rtl_authoring_plan(ip))
            rtl_context["rtl_packet_pass_budget"] = attempt_limit
        for attempt in range(attempt_limit):
            if attempt > 0:
                try:
                    prederive = self._prepare_rtl_todos_for_llm(ip, audit_rtl=True)
                except Exception as exc:
                    return self._append("rtl-gen", "fail", f"failed to refresh SSOT RTL TODO plan before repair attempt: {exc}", returncode=999)
                if prederive.returncode not in {0, 1}:
                    result = self.stage_engine.run_stage("ssot-rtl", ip)
                    break
                self._update_rtl_context_from_todos(ip, rtl_context)
                if self._refresh_rtl_filelist_and_provenance(ip):
                    try:
                        prederive = self._prepare_rtl_todos_for_llm(ip, audit_rtl=True)
                    except Exception as exc:
                        return self._append("rtl-gen", "fail", f"failed to refresh RTL TODO plan after provenance update: {exc}", returncode=999)
                    if prederive.returncode not in {0, 1}:
                        result = self.stage_engine.run_stage("ssot-rtl", ip)
                        break
                    self._update_rtl_context_from_todos(ip, rtl_context)
                packet_mode = self._rtl_packet_mode_enabled(self._rtl_authoring_plan(ip))
            rtl_context["rtl_gen_attempt"] = attempt
            if packet_mode:
                gate = self._run_rtl_packet_llm_pass(ip, rtl_context, attempt=attempt)
                if gate is not None:
                    return gate
            else:
                response = self._call_llm(
                    "rtl-gen",
                    ip,
                    rtl_context,
                    log_stage="rtl-gen" if attempt == 0 else f"rtl-gen-repair-{attempt}",
                )
                if response.status in {"blocked", "human_gate"}:
                    return self._append_llm_gate(ip, "rtl-gen", response, topic="llm")
                self._apply_artifacts(ip, response.parsed_artifacts)
                self._refresh_rtl_filelist_and_provenance(ip)
            result = self.stage_engine.run_stage("ssot-rtl", ip)
            if result.status == "pass":
                self._ensure_generic_rtl_contract(ip)
                self._write_deterministic_rtl_seed_log(ip, rtl_context)
                break
            if result.status in {"human_gate", "blocked"} and not self._rtl_result_repairable_by_llm(result):
                break
            if attempt >= attempt_limit - 1:
                break
            rtl_context.update(
                {
                    "rtl_repair_attempt": attempt + 1,
                    "rtl_last_result_status": result.status,
                    "rtl_last_result_message": result.message[-4000:],
                }
            )
        assert result is not None
        extra: list[str] = []
        blocker = result.blocker
        blocked_doc = result.metadata.get("rtl_blocked") if isinstance(result.metadata, dict) else None
        if isinstance(blocked_doc, dict) and blocked_doc and not self._rtl_result_repairable_by_llm(result):
            q = self._write_human_gate(
                ip,
                "rtl-gen",
                "rtl_blocked",
                decision_needed=str(blocked_doc.get("reason") or "RTL generation blocked by SSOT contract"),
                evidence={"ssot_refs": [f"{ip}/yaml/{ip}.ssot.yaml"], "tool_logs": [f"{ip}/rtl/rtl_blocked.json"], "goal_ids": []},
            )
            blocker = str(q.relative_to(self.root))
            extra.append(blocker)
        if result.status == "pass":
            self._ensure_generic_rtl_contract(ip)
            self._write_deterministic_rtl_seed_log(ip, rtl_context)
        return self._append_engine_result(result, "rtl-gen", artifacts=extra, blocker=blocker)

    def _stage_lint(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("lint", ip), "lint")

    def _stage_tb_gen(self, ip: str, context: dict[str, Any]) -> StageResult:
        response = self._call_llm("tb-gen", ip, context)
        if response.status not in {"blocked", "human_gate"}:
            self._apply_artifacts(ip, response.parsed_artifacts)
        self._ensure_generic_rtl_contract(ip)
        result = self.stage_engine.run_stage("ssot-tb-cocotb", ip)
        extra: list[str] = []
        blocker = result.blocker
        blocked_doc = result.metadata.get("tb_blocked") if isinstance(result.metadata, dict) else None
        if isinstance(blocked_doc, dict) and blocked_doc:
            q = self._write_human_gate(
                ip,
                "tb-gen",
                "tb_blocked",
                decision_needed=str(blocked_doc.get("reason") or "TB generation blocked by SSOT/RTL contract"),
                evidence={"ssot_refs": [f"{ip}/yaml/{ip}.ssot.yaml"], "tool_logs": [f"{ip}/tb/cocotb/tb_blocked.json"], "goal_ids": []},
            )
            blocker = str(q.relative_to(self.root))
            extra.append(blocker)
        return self._append_engine_result(result, "tb-gen", artifacts=extra, blocker=blocker)

    def _stage_sim(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("sim", ip), "sim")

    def _stage_sim_debug(self, ip: str) -> StageResult:
        result = self.stage_engine.run_stage("sim-debug", ip)
        extra: list[str] = []
        blocker = result.blocker
        items = []
        if isinstance(result.metadata, dict):
            raw_items = result.metadata.get("human_gate_classifications")
            if isinstance(raw_items, list):
                items = raw_items
        for item in items:
            if not isinstance(item, dict):
                continue
            q = self._write_human_gate(
                ip,
                "sim-debug",
                str(item.get("goal_id") or "mismatch"),
                decision_needed=str(item.get("human_question") or "Resolve simulation mismatch semantic ownership."),
                evidence=item.get("evidence") if isinstance(item.get("evidence"), dict) else {"goal_ids": [item.get("goal_id")]},
            )
            rel = str(q.relative_to(self.root))
            blocker = blocker or rel
            extra.append(rel)
        return self._append_engine_result(result, "sim-debug", artifacts=extra, blocker=blocker)

    def _stage_goal_audit(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("goal-audit", ip), "goal-audit")

    def _stage_contract_check(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("contract-check", ip), "contract-check")

    def _execute_canonical_stage(self, canonical: str, ip: str, context: dict[str, Any]) -> StageResult:
        before = len(self.stages)
        if canonical == "req-contracts":
            self._run_req_contracts_stage(ip, context)
        elif canonical == "ssot-gen":
            self._run_ssot_generation(ip, context)
        elif canonical == "fl-model-gen":
            self._stage_fl_model(ip, context)
        elif canonical == "cl-model-gen":
            self._stage_cl_model(ip)
        elif canonical == "dual-fcov":
            self._stage_dual_fcov(ip)
        elif canonical == "equiv-goals":
            self._stage_equiv_goals(ip)
        elif canonical == "rtl-gen":
            self._stage_rtl_gen(ip, context)
        elif canonical == "lint":
            self._stage_lint(ip)
        elif canonical == "tb-gen":
            self._stage_tb_gen(ip, context)
        elif canonical == "coverage":
            self._append_engine_result(self.stage_engine.run_stage("coverage", ip), "coverage")
        elif canonical == "sim":
            self._stage_sim(ip)
        elif canonical == "sim-debug":
            self._stage_sim_debug(ip)
        elif canonical == "contract-check":
            self._stage_contract_check(ip)
        elif canonical == "goal-audit":
            self._stage_goal_audit(ip)
        elif canonical == "pipeline":
            self._stage_pipeline_converge(ip, context)
        else:
            self._append(canonical, "fail", f"unknown stage {canonical}", returncode=2)
        if len(self.stages) <= before:
            return self._append(canonical, "fail", f"stage {canonical} produced no result", returncode=998)
        return self.stages[-1]

    def _pipeline_stage_list(self, ip: str, context: dict[str, Any]) -> list[str]:
        raw = os.getenv("ATLAS_HEADLESS_PIPELINE_STAGES", "").strip()
        if raw:
            return [
                _canonical_headless_stage(part.strip())
                for part in raw.split(",")
                if part.strip() and _canonical_headless_stage(part.strip()) != "pipeline"
            ]
        stages = list(PIPELINE_DEFAULT_STAGES)
        ssot_path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        if context.get("requirement_text") and not ssot_path.is_file():
            stages.insert(0, "ssot-gen")
        return stages

    def _pipeline_repair_sequence(self, owner: str) -> list[str]:
        owner = self._canonical_repair_owner(owner)
        if owner == "rtl-gen":
            full = ["rtl-gen", "lint", "tb-gen", "sim", "coverage", "sim-debug", "contract-check", "goal-audit"]
        elif owner == "tb-gen":
            full = ["tb-gen", "sim", "coverage", "sim-debug", "contract-check", "goal-audit"]
        elif owner == "fl-model-gen":
            full = ["fl-model-gen", "equiv-goals", "tb-gen", "sim", "coverage", "sim-debug", "contract-check", "goal-audit"]
        elif owner == "coverage":
            full = ["coverage", "contract-check", "goal-audit"]
        else:
            full = [owner]
        # When the operator constrains the pipeline via ATLAS_HEADLESS_PIPELINE_STAGES
        # (used by tests and debugging runs), the repair sequence must respect the
        # same constraint — otherwise the second iteration tries to run stages the
        # caller never asked for. Filter while preserving the canonical order of
        # the hardcoded repair sequence.
        raw = os.getenv("ATLAS_HEADLESS_PIPELINE_STAGES", "").strip()
        if raw:
            allowed = {
                _canonical_headless_stage(part.strip())
                for part in raw.split(",")
                if part.strip()
            }
            filtered = [s for s in full if _canonical_headless_stage(s) in allowed]
            if filtered:
                if owner in full and owner not in filtered:
                    first_filtered_index = min(full.index(s) for s in filtered)
                    owner_index = full.index(owner)
                    required_prefix = full[: max(first_filtered_index, owner_index) + 1]
                    repaired = []
                    for stage in required_prefix + filtered:
                        if stage not in repaired:
                            repaired.append(stage)
                    return repaired
                return filtered
        return full

    def _pipeline_repair_request(self, ip: str) -> dict[str, Any]:
        items = self._loopable_repair_classifications(ip)
        if not items:
            return {}
        priority = ["rtl-gen", "tb-gen", "fl-model-gen", "coverage"]
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            grouped.setdefault(self._canonical_repair_owner(str(item.get("owner") or "")), []).append(item)
        owner = sorted(
            grouped,
            key=lambda candidate: (
                -len(grouped[candidate]),
                priority.index(candidate) if candidate in priority else len(priority),
                candidate,
            ),
        )[0]
        owner_items = grouped[owner]
        return {
            "owner": owner,
            "signature": self._repair_classification_signature(owner_items),
            "items": owner_items,
            "goal_ids": [item.get("goal_id") for item in owner_items if item.get("goal_id")],
        }

    def _stage_pipeline_converge(self, ip: str, context: dict[str, Any]) -> StageResult:
        max_iterations = max(1, int(os.getenv("ATLAS_HEADLESS_PIPELINE_MAX_ITERS", "2")))
        initial_sequence = self._pipeline_stage_list(ip, context)
        next_owner = ""
        last_repair_signature = ""
        last_request: dict[str, Any] = {}

        for iteration in range(max_iterations):
            sequence = self._pipeline_repair_sequence(next_owner) if next_owner else initial_sequence
            next_owner = ""
            self._write_progress(ip, "pipeline_iteration_start", iteration=iteration + 1, stages=sequence)
            consumed_repair = False
            pending_sim_failure: StageResult | None = None
            for index, canonical in enumerate(sequence):
                if pending_sim_failure is not None and canonical != "sim-debug":
                    if "sim-debug" in sequence[index + 1 :]:
                        self._write_progress(
                            ip,
                            "stage_skipped",
                            stage=canonical,
                            reason="waiting for sim-debug to classify failed sim evidence",
                            pipeline_iteration=iteration + 1,
                        )
                        continue
                self._write_progress(ip, "stage_start", stage=canonical, pipeline_iteration=iteration + 1)
                self._write_heartbeat(ip, state="running", phase="pipeline", current_stage=canonical, model=self.model)
                stage_result = self._execute_canonical_stage(canonical, ip, context)
                self._write_progress(
                    ip,
                    "stage_end",
                    stage=canonical,
                    status=stage_result.status,
                    message=stage_result.message[:400],
                    pipeline_iteration=iteration + 1,
                )
                if stage_result.status not in {"fail", "human_gate", "blocked"}:
                    continue
                if canonical == "sim" and "sim-debug" in sequence[index + 1 :]:
                    pending_sim_failure = stage_result
                    stage_result.message += "\n[pipeline] sim failed; continuing to sim-debug for owner classification."
                    continue
                if canonical == "sim-debug":
                    request = self._pipeline_repair_request(ip)
                    if request:
                        last_request = request
                        signature = str(request.get("signature") or "")
                        if signature and signature == last_repair_signature:
                            rel = self._write_repeated_mismatch_review(ip, request)
                            stage_result.status = "pass"
                            stage_result.message += "\n[pipeline] repeated repair signature escalated to Review Decision Needed."
                            return self._append(
                                "pipeline",
                                "blocked",
                                "pipeline stopped: same sim-debug mismatch signature repeated after owner repair",
                                returncode=1,
                                artifacts=[rel],
                                blocker=rel,
                            )
                        last_repair_signature = signature
                        next_owner = str(request.get("owner") or "")
                        stage_result.status = "pass"
                        stage_result.message += f"\n[pipeline] routed loopable mismatch to {next_owner} repair."
                        consumed_repair = True
                        break
                    if pending_sim_failure is not None:
                        return pending_sim_failure
                return stage_result
            if next_owner:
                if iteration >= max_iterations - 1:
                    rel = self._write_repeated_mismatch_review(ip, last_request)
                    return self._append(
                        "pipeline",
                        "blocked",
                        "pipeline stopped: repair loop budget exhausted before mismatches converged",
                        returncode=1,
                        artifacts=[rel],
                        blocker=rel,
                    )
                continue
            if pending_sim_failure is not None:
                return pending_sim_failure
            if not consumed_repair:
                return self._append(
                    "pipeline",
                    "pass",
                    f"pipeline converged through {', '.join(sequence)}",
                    artifacts=[f"{ip}/logs/headless_run.json"],
                )

        rel = self._write_repeated_mismatch_review(ip, last_request)
        return self._append(
            "pipeline",
            "blocked",
            "pipeline stopped: convergence loop did not reach a terminal pass",
            returncode=1,
            artifacts=[rel],
            blocker=rel,
        )

    def _write_repeated_mismatch_review(self, ip: str, request: dict[str, Any]) -> str:
        """Route through `src/review_decisions.py` so /api/pipeline/state's
        decisions_needed count, the orchestrator UI, and resolve tooling all
        see the same `pipeline_decision_needed.v1` schema."""
        try:
            from src import review_decisions as rd
        except ImportError:
            import review_decisions as rd  # type: ignore[no-redef]

        owner = str(request.get("owner") or "unknown")
        goal_ids = [str(item) for item in request.get("goal_ids") or [] if str(item)]
        items = request.get("items") if isinstance(request.get("items"), list) else []
        retry_attempts = int(request.get("retry_attempts") or request.get("attempts") or 0)
        signature = str(request.get("signature") or "")
        # Legacy callers expect one file per owner (overwrite on repeat) — the
        # signature lives inside the record body, not in the filename. Pass
        # `signature=""` to the path helper so we don't fork the on-disk
        # contract that downstream tooling already reads.
        path = rd.write_repeated_mismatch_decision(
            self._ip_dir(ip),
            ip=ip,
            owner=owner,
            signature="",
            retry_attempts=retry_attempts,
            reason=(
                f"{owner} repair did not converge for "
                f"{', '.join(goal_ids) if goal_ids else 'classified mismatch goals'}."
            ),
            evidence={
                "source": f"{ip}/sim/mismatch_classification.json",
                "owner": owner,
                "goal_ids": goal_ids,
                "signature": signature,
                "classifications": items[:16],
            },
            next_actions=[
                "Decide whether SSOT semantics are missing, the owner classification is wrong, "
                "or a workflow/tool evidence rule needs repair.",
                "Do not silently pass. Fix the owning workflow/tooling if classification is wrong, "
                "or lock the missing SSOT decision before rerunning the pipeline.",
            ],
        )
        return str(path.relative_to(self.root))

    def run(self, *, ip: str, requirement_path: str | Path | None = None, stages: list[str]) -> WorkflowResult:
        ip = _safe_name(ip, "headless_ip")
        self.root.mkdir(parents=True, exist_ok=True)
        self._ip_dir(ip).mkdir(parents=True, exist_ok=True)
        self._write_progress(ip, "run_start", target_ip=ip, root=str(self.root), model=self.model, stages=stages)
        self._write_heartbeat(ip, state="running", phase="init", model=self.model, current_stage="")
        self.stages = []
        if requirement_path is not None:
            req_text = self._copy_requirement(ip, Path(requirement_path))
            req_rel = f"{ip}/req/{ip}_requirements.md"
            req_status = self._validate_req(ip, req_text)
            if req_status and req_status.status == "human_gate":
                return self._finish(ip)
        else:
            existing_req = self._ip_dir(ip) / "req" / f"{ip}_requirements.md"
            req_text = existing_req.read_text(encoding="utf-8", errors="replace") if existing_req.is_file() else ""
            req_rel = str(existing_req.relative_to(self.root)) if existing_req.is_file() else ""
        context = {
            "ip": ip,
            "root": str(self.root),
            "requirement_text": req_text,
            "requirement_path": req_rel,
        }
        for stage in stages:
            canonical = _canonical_headless_stage(stage)
            self._write_progress(ip, "stage_start", stage=canonical)
            self._write_heartbeat(ip, state="running", phase="stage", current_stage=canonical, model=self.model)
            self._execute_canonical_stage(canonical, ip, context)

            # Outer retry: a plain "fail" gets fresh in-stage repair rounds.
            # human_gate/blocked are decisions, not transient failures — never
            # retried.
            retries_left = self.stage_retries
            while (
                retries_left > 0
                and self.stages
                and self.stages[-1].status == "fail"
            ):
                retries_left -= 1
                self._write_progress(
                    ip,
                    "stage_retry",
                    stage=canonical,
                    retries_left=retries_left,
                    message=self.stages[-1].message[:400],
                )
                self._execute_canonical_stage(canonical, ip, context)

            if self.stages and self.stages[-1].status in {"fail", "human_gate", "blocked"}:
                self._write_progress(
                    ip,
                    "stage_end",
                    stage=canonical,
                    status=self.stages[-1].status,
                    message=self.stages[-1].message[:400],
                )
                break
            if self.stages:
                self._write_progress(
                    ip,
                    "stage_end",
                    stage=canonical,
                    status=self.stages[-1].status,
                    message=self.stages[-1].message[:400],
                )
        return self._finish(ip)

    def _finish(self, ip: str) -> WorkflowResult:
        status = "pass"
        for stage in self.stages:
            if stage.status in {"human_gate", "blocked"}:
                status = "blocked"
                break
            if stage.status != "pass":
                status = "fail"
                break
        run_log = self._ip_dir(ip) / "logs" / "headless_run.json"
        result = WorkflowResult(ip=ip, status=status, stages=self.stages, root=str(self.root), run_log=str(run_log.relative_to(self.root)))
        _write_json(run_log, result.to_dict())
        self._write_trace_summary(ip=ip, run_status=status)
        self._write_progress(ip, "run_end", status=status, run_log=str(run_log))
        self._write_heartbeat(ip, state="done", phase="finished", status=status, model=self.model)
        self._refresh_ip_wiki_graph(ip)
        return result

    def _refresh_ip_wiki_graph(self, ip: str) -> None:
        """Refresh `<ip>/wiki/_graph.json` so wiki_query reflects this run.

        Deterministic, in-process when possible (no subprocess churn).
        Failures are non-fatal — the graph is a read-only convenience.
        """
        try:
            try:
                from workflow.wiki import build_graph as _wiki_build
            except Exception:
                import importlib.util as _ilu
                builder = WORKFLOW_ROOT / "wiki" / "build_graph.py"
                if not builder.is_file():
                    builder = self.root.parent / "workflow" / "wiki" / "build_graph.py"
                spec = _ilu.spec_from_file_location("atlas_wiki_build_graph", builder)
                if spec is None or spec.loader is None:
                    return
                _wiki_build = _ilu.module_from_spec(spec)
                spec.loader.exec_module(_wiki_build)
            project_root = self.root.resolve()
            graph = _wiki_build.build_ip(ip, project_root)
            wiki_dir = project_root / ip / "wiki"
            wiki_dir.mkdir(parents=True, exist_ok=True)
            (wiki_dir / "_graph.json").write_text(
                json.dumps(graph, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except BaseException:
            pass

    def _write_trace_summary(self, *, ip: str, run_status: str) -> None:
        llm_dir = self._log_dir(ip)
        stage_engine_dir = self._ip_dir(ip) / "logs" / "stage_engine"
        out_path = self._ip_dir(ip) / "logs" / "trace_summary.json"

        by_stage: dict[str, dict[str, Any]] = {}
        totals: dict[str, Any] = {
            "calls": 0,
            "repair_calls": 0,
            "repair_rate": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
        }

        llm_files = sorted(llm_dir.glob("*.json"))
        for path in llm_files:
            data = _read_json(path)
            stage_name = str(data.get("stage") or path.stem).strip() or "unknown"
            usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
            cost = usage.get("cost") if isinstance(usage.get("cost"), dict) else {}
            is_repair = ("repair" in path.stem) or ("repair" in str(data.get("raw_response") or "").lower())

            row = by_stage.setdefault(
                stage_name,
                {
                    "calls": 0,
                    "repair_calls": 0,
                    "repair_rate": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "models": [],
                },
            )
            row["calls"] += 1
            row["repair_calls"] += 1 if is_repair else 0
            row["input_tokens"] += int(usage.get("input", 0) or 0)
            row["output_tokens"] += int(usage.get("output", 0) or 0)
            row["cache_read_tokens"] += int(usage.get("cache_read", 0) or 0)
            row["total_tokens"] += int(usage.get("total", 0) or 0)
            row["cost_usd"] += float(cost.get("usd", 0.0) or 0.0)
            model_name = str(data.get("model") or "").strip()
            if model_name and model_name not in row["models"]:
                row["models"].append(model_name)

            totals["calls"] += 1
            totals["repair_calls"] += 1 if is_repair else 0
            totals["input_tokens"] += int(usage.get("input", 0) or 0)
            totals["output_tokens"] += int(usage.get("output", 0) or 0)
            totals["cache_read_tokens"] += int(usage.get("cache_read", 0) or 0)
            totals["total_tokens"] += int(usage.get("total", 0) or 0)
            totals["cost_usd"] += float(cost.get("usd", 0.0) or 0.0)

        for row in by_stage.values():
            calls = int(row.get("calls", 0) or 0)
            repairs = int(row.get("repair_calls", 0) or 0)
            row["repair_rate"] = (float(repairs) / float(calls)) if calls else 0.0
        totals["repair_rate"] = (float(totals["repair_calls"]) / float(totals["calls"])) if totals["calls"] else 0.0

        stage_engine_order: list[dict[str, Any]] = []
        for stage_file in sorted(stage_engine_dir.glob("*.json")):
            info = _read_json(stage_file)
            stage_engine_order.append(
                {
                    "stage_engine": stage_file.stem,
                    "status": str(info.get("status") or "").strip(),
                    "created_at": str(info.get("created_at") or "").strip(),
                }
            )

        blocked_at = ""
        if self.stages:
            last = self.stages[-1]
            if last.status in {"fail", "blocked", "human_gate"}:
                blocked_at = last.stage

        _write_json(
            out_path,
            {
                "ip": ip,
                "run_status": run_status,
                "blocked_at_stage": blocked_at,
                "llm_log_files": len(llm_files),
                "llm": {"totals": totals, "by_stage": by_stage},
                "stage_engine_order": stage_engine_order,
            },
        )


def _make_provider(kind: str, fixture: str = "") -> LLMProvider:
    if kind == "real":
        return RealLLMProvider(required_model=os.getenv("ATLAS_HEADLESS_REQUIRED_MODEL", ""))
    if kind == "cached":
        if not fixture:
            raise SystemExit("--fixture is required for cached provider")
        return CachedLLMProvider(fixture)
    return FakeLLMProvider()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--req", default="")
    parser.add_argument("--model", default=os.getenv("ATLAS_HEADLESS_LLM_MODEL", "glm-5.1"))
    parser.add_argument("--run-mode", default=os.getenv("ATLAS_RUN_MODE", "signoff"), choices=["starter", "engineering", "signoff"])
    parser.add_argument("--stages", required=True, help="comma-separated stage list (or 'take')")
    parser.add_argument("--provider", choices=["fake", "cached", "real"], default="real")
    parser.add_argument("--fixture", default="")
    parser.add_argument(
        "--req-approver",
        default=os.getenv("ATLAS_REQ_APPROVED_BY", ""),
        help="human approver for the req-contracts lock; without it the stage stops at a human_gate",
    )
    parser.add_argument(
        "--stage-retries",
        type=int,
        default=int(os.getenv("ATLAS_HEADLESS_STAGE_RETRIES", "0")),
        help="re-invoke a failed stage up to N times with fresh repair rounds (human_gate/blocked never retry)",
    )
    parser.add_argument(
        "--workflow",
        default="",
        help="workflow name to claim when --stages take is used (e.g. rtl-gen)",
    )
    args = parser.parse_args(argv)
    raw_stages = [part.strip() for part in args.stages.split(",") if part.strip()]

    def _make_runner() -> HeadlessWorkflowRunner:
        provider = _make_provider(args.provider, args.fixture)
        return HeadlessWorkflowRunner(
            root=args.root,
            model=args.model,
            run_mode=args.run_mode,
            llm_provider=provider,
            require_glm51=args.provider == "real" and os.getenv("ATLAS_HEADLESS_REQUIRE_GLM51") == "1",
            req_approver=args.req_approver,
            stage_retries=args.stage_retries,
        )

    if raw_stages == ["take"]:
        if not args.workflow:
            parser.error("--workflow is required when --stages take")
        return _run_take(args, _make_runner)

    stages = [_canonical_headless_stage(s) for s in raw_stages]
    if not args.req and "ssot-gen" in stages:
        parser.error("--req is required when ssot-gen is requested")

    runner = _make_runner()
    result = runner.run(
        ip=args.ip,
        requirement_path=args.req or None,
        stages=stages,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.status == "pass" else 2


def _run_take(args, runner_factory) -> int:
    """Claim one pending JSON handoff for the requested workflow and run it.

    Contract (from `doc/wiki/orchestrator-worker-handoff.md` §JSON Fallback):
    - claim the oldest pending handoff in `<ip>/handoff/pending/` whose
      `to_workflow` matches `--workflow`
    - run the owner workflow as a normal stage
    - on success: move the handoff to `done` with the result attached
    - on failure: release the claim back to pending so another `take` can retry
    - if no pending handoff: print `status=none_available` and exit 0
    """
    try:
        from src import handoff_queue as hq
    except ImportError:
        import handoff_queue as hq  # type: ignore[no-redef]

    ip_dir = Path(args.root) / args.ip
    # claim_next() is the atomic primitive — it walks pending FIFO and uses
    # os.replace() to win exactly one record. Two concurrent /take calls
    # cannot end up with the same handoff_id.
    claimed = hq.claim_next(
        ip_dir,
        args.workflow,
        claimant=f"headless-{os.getpid()}",
    )
    if claimed is None:
        print(json.dumps(
            {"status": "none_available", "ip": args.ip, "workflow": args.workflow},
            indent=2,
            sort_keys=True,
        ))
        return 0
    handoff_id = claimed["handoff_id"]

    runner = runner_factory()
    canonical_stage = _canonical_headless_stage(args.workflow)
    try:
        result = runner.run(
            ip=args.ip,
            requirement_path=args.req or None,
            stages=[canonical_stage],
        )
    except Exception as exc:
        hq.release_claim(ip_dir, handoff_id)
        print(json.dumps(
            {"status": "error", "ip": args.ip, "workflow": args.workflow,
             "handoff_id": handoff_id, "error": str(exc)},
            indent=2,
            sort_keys=True,
        ))
        return 2

    if result.status == "pass":
        hq.complete(ip_dir, handoff_id, result={"status": result.status})
    else:
        hq.release_claim(ip_dir, handoff_id)

    print(json.dumps(
        {
            "status": result.status,
            "ip": args.ip,
            "workflow": args.workflow,
            "handoff_id": handoff_id,
            "result": result.to_dict(),
        },
        indent=2,
        sort_keys=True,
    ))
    return 0 if result.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
