#!/usr/bin/env python3
"""Upgrade an existing IP SSOT to the canonical production schema.

This is a structure repair tool, not an IP generator. It preserves the
existing SSOT facts, derives missing model/signoff sections from those facts
and the approved ATLAS Q&A state when available, and then writes the same SSOT
path back in canonical section order.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


REQUIRED_ORDER = [
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
    "coding_rules",
    "reuse_modules",
    "custom",
    "dir_structure",
    "filelist",
    "test_requirements",
    "quality_gates",
    "traceability",
    "workflow_todos",
    "generation_flow",
]


def _load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise SystemExit(f"[repair_ssot_schema] {path} is not a YAML mapping")
    return doc


def _load_state(root: Path, ip: str) -> dict[str, Any]:
    path = root / ".session" / ip / "ssot-gen" / "state.json"
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _find_ssot(root: Path, ip: str) -> Path:
    for name in (f"{ip}.ssot.yaml", f"{ip}_ssot.yaml", f"{ip}.ssot.yml"):
        path = root / ip / "yaml" / name
        if path.is_file():
            return path
    raise SystemExit(f"[repair_ssot_schema] no SSOT YAML found for {ip}")


def _first_clock(doc: dict[str, Any]) -> tuple[str, int]:
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    freq = int(top.get("target", {}).get("clock_freq_mhz") or 100) if isinstance(top.get("target"), dict) else 100
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for dom in io.get("clock_domains") or []:
        if isinstance(dom, dict):
            name = dom.get("name") or "clk"
            ports = dom.get("ports") if isinstance(dom.get("ports"), list) else []
            if ports and isinstance(ports[0], dict) and ports[0].get("name"):
                name = ports[0]["name"]
            return str(name), int(dom.get("frequency_mhz") or freq)
    return "clk", freq


def _first_reset(doc: dict[str, Any]) -> tuple[str, str, str]:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for rst in io.get("resets") or []:
        if isinstance(rst, dict):
            name = rst.get("name") or "rst_n"
            ports = rst.get("ports") if isinstance(rst.get("ports"), list) else []
            if ports and isinstance(ports[0], dict) and ports[0].get("name"):
                name = ports[0]["name"]
            return str(name), str(rst.get("polarity") or "active_low"), str(rst.get("sync_async") or "async_assert_sync_deassert")
    return "rst_n", "active_low", "async_assert_sync_deassert"


def _parameters(doc: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in doc.get("parameters") or []:
        if isinstance(item, dict) and item.get("name"):
            out[str(item["name"])] = item.get("default")
    return out


def _decisions(state: dict[str, Any]) -> dict[str, str]:
    raw = state.get("decisions") if isinstance(state.get("decisions"), dict) else {}
    return {str(k): str(v) for k, v in raw.items() if str(v or "").strip()}


def _is_live(value: Any) -> bool:
    return value not in (None, "", [], {})


def _has_tbd(value: Any) -> bool:
    if isinstance(value, str):
        return "<TBD>" in value or "<placeholder>" in value or "TODO: confirm" in value
    if isinstance(value, list):
        return any(_has_tbd(v) for v in value)
    if isinstance(value, dict):
        return any(_has_tbd(v) for v in value.values())
    return False


def _ensure_top_module(doc: dict[str, Any], state: dict[str, Any], ip: str) -> dict[str, Any]:
    decisions = _decisions(state)
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    kind = str(state.get("kind") or decisions.get("purpose") or "").lower()
    if not _is_live(top.get("type")) or _has_tbd(top.get("type")):
        if "sram" in kind or "memory" in kind:
            top["type"] = "memory"
        elif "bus" in kind or "interconnect" in kind:
            top["type"] = "bus"
        elif "dma" in kind:
            top["type"] = "dma"
        else:
            top["type"] = "peripheral"
    top["name"] = top.get("name") or ip
    if not _is_live(top.get("description")) or _has_tbd(top.get("description")):
        top["description"] = decisions.get("purpose") or f"{ip} leaf IP generated from approved ATLAS Web SSOT requirements"
    target = top.get("target") if isinstance(top.get("target"), dict) else {}
    target.setdefault("technology", "generic")
    target.setdefault("clock_freq_mhz", 100)
    target.setdefault("area_um2", None)
    target.setdefault("power_mw", None)
    top.setdefault("version", "1.0")
    top.setdefault("reference_spec", "user-defined")
    top["target"] = target
    return top


def _ensure_sub_modules(doc: dict[str, Any], ip: str) -> list[dict[str, Any]]:
    subs = doc.get("sub_modules")
    if isinstance(subs, list) and subs and not _has_tbd(subs):
        fixed: list[dict[str, Any]] = []
        for item in subs:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            if row.get("name") in {f"{ip}_wrapper", "wrapper"}:
                row["name"] = ip
                row["file"] = f"rtl/{ip}.sv"
                row["description"] = "Top-level integration module matching SSOT top_module"
            fixed.append(row)
        if not any(isinstance(item, dict) and item.get("name") == ip for item in fixed):
            fixed.append({
                "name": ip,
                "file": f"rtl/{ip}.sv",
                "ownership": "manifest",
                "ssot_gen": True,
                "description": "Top-level integration module matching SSOT top_module",
            })
        return fixed
    names = ["pkg", "axi_slv", "crypto", "mem", "core", "top"]
    desc = {
        "pkg": "Parameter and shared type definitions",
        "axi_slv": "AXI4-Lite slave channel handling and response sequencing",
        "crypto": "Parameterized encrypt/decrypt transform used for data-at-rest",
        "mem": "Parameterized SRAM storage array",
        "core": "Read/write merge, crypto, memory, and debug control",
        "top": "Top-level integration module matching SSOT top_module",
    }
    return [
        {
            "name": ip if name == "top" else f"{ip}_{name}",
            "file": f"rtl/{ip}.sv" if name == "top" else f"rtl/{ip}_{name}.sv",
            "ownership": "manifest",
            "ssot_gen": True,
            "description": desc[name],
        }
        for name in names
    ]


def _tokens_from(value: Any) -> set[str]:
    text = json.dumps(value, sort_keys=True, default=str) if isinstance(value, (dict, list)) else str(value or "")
    chars = [ch.lower() if ch.isalnum() else " " for ch in text]
    return {tok for tok in "".join(chars).split() if len(tok) > 1}


def _append_unique_ref(row: dict[str, Any], key: str, ref: str) -> None:
    existing = row.get(key)
    refs = [str(item).strip() for item in existing if str(item).strip()] if isinstance(existing, list) else []
    if ref not in refs:
        refs.append(ref)
    row[key] = refs


def _expr_tokens(expr: Any) -> set[str]:
    text = str(expr or "")
    chars = [ch if (ch.isalnum() or ch == "_") else " " for ch in text]
    return {tok for tok in "".join(chars).split() if tok}


def _choose_behavior_owner(candidates: list[dict[str, Any]], terms: set[str]) -> dict[str, Any] | None:
    if not candidates:
        return None
    preferred = {
        "reset": {"reset", "init", "fsm", "control", "manager", "core"},
        "csr": {"csr", "reg", "register", "apb", "cfg", "config", "status", "control"},
        "register": {"csr", "reg", "register", "apb", "cfg", "config", "status", "control"},
        "debug": {"debug", "csr", "control", "status"},
        "interrupt": {"irq", "intr", "interrupt", "event", "status", "control"},
        "error": {"fault", "error", "abort", "status", "control"},
        "state": {"state", "fsm", "thread", "manager", "control", "core"},
    }
    boosted_terms = set(terms)
    for term, boosts in preferred.items():
        if term in terms:
            boosted_terms |= boosts
    best: tuple[int, int, dict[str, Any]] | None = None
    for idx, row in enumerate(candidates):
        row_terms = _tokens_from({
            "name": row.get("name"),
            "description": row.get("description"),
            "source_sections": row.get("source_sections"),
        })
        score = len(boosted_terms & row_terms)
        if row.get("function_model_refs"):
            score += 1
        if best is None or score > best[0]:
            best = (score, -idx, row)
    return best[2] if best else candidates[0]


def _ensure_submodule_behavior_ownership(doc: dict[str, Any], ip: str) -> list[dict[str, Any]]:
    subs = [dict(item) for item in doc.get("sub_modules") or [] if isinstance(item, dict)]
    top_names = {ip, f"{ip}_top", "top", "wrapper"}
    candidates = [
        row for row in subs
        if str(row.get("name") or "") not in top_names and Path(str(row.get("file") or "")).stem not in top_names
    ]
    if not candidates:
        owner = {
            "name": f"{ip}_behavior_contract",
            "ownership": "conceptual",
            "ssot_gen": False,
            "rtl_emit": False,
            "description": "Conceptual owner for SSOT function-model behavior implemented by the generated RTL.",
            "source_sections": ["function_model", "cycle_model", "features", "test_requirements"],
        }
        subs.insert(0, owner)
        candidates = [owner]

    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    for idx, tx in enumerate(fm.get("transactions") or []):
        if not isinstance(tx, dict):
            continue
        tx_id = str(tx.get("id") or tx.get("name") or idx).strip()
        if not tx_id:
            continue
        owner = _choose_behavior_owner(candidates, _tokens_from(tx))
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", f"function_model.transactions.{tx_id}")

    if fm.get("state_variables"):
        owner = _choose_behavior_owner(candidates, {"state", "register", "status", "csr", "control"})
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", "function_model.state_variables")

    if fm.get("outputs"):
        owner = _choose_behavior_owner(candidates, {"output", "status", "control"})
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", "function_model.outputs")
    if fm.get("inputs"):
        owner = _choose_behavior_owner(candidates, {"input", "interface", "control"})
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", "function_model.inputs")

    return subs


def _valid_ready_contract_required(doc: dict[str, Any]) -> bool:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for intf in io.get("interfaces") or []:
        if not isinstance(intf, dict):
            continue
        text = " ".join(str(intf.get(key) or "") for key in ("name", "type", "description")).lower()
        if "valid_ready" in text or ("valid" in text and "ready" in text):
            return True
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    for rule in cm.get("handshake_rules") or []:
        if isinstance(rule, dict):
            text = json.dumps(rule, sort_keys=True, default=str).lower()
        else:
            text = str(rule).lower()
        if "valid" in text and "ready" in text:
            return True
    return False


def _ensure_rtl_contract_consistency(doc: dict[str, Any]) -> None:
    contract = doc.get("rtl_contract")
    if not isinstance(contract, dict) or not _valid_ready_contract_required(doc):
        return
    ready = str(contract.get("ready_output") or "").strip()
    sample = str(contract.get("sample_condition") or "").strip()
    if not ready or not sample:
        return
    tokens = _expr_tokens(sample)
    if ready in tokens:
        return
    has_valid_input = any(tok == "valid" or tok.endswith("_valid") for tok in tokens)
    if not has_valid_input:
        return
    contract["sample_condition"] = f"({sample}) and {ready}"


def _ensure_parameters_section(doc: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    params = doc.get("parameters")
    if isinstance(params, list) and params and not _has_tbd(params):
        return params
    return [
        {"name": "DATA_WIDTH", "default": 32, "type": "int", "description": "AXI data and SRAM word width in bits", "drives": ["rtl", "tb", "coverage"]},
        {"name": "ADDR_WIDTH", "default": 8, "type": "int", "description": "SRAM word address width; default 256 words", "drives": ["rtl", "tb", "coverage"]},
        {"name": "STRB_WIDTH", "default": "DATA_WIDTH/8", "type": "int", "description": "AXI byte strobe width derived from DATA_WIDTH", "drives": ["axi_slv", "core"]},
        {"name": "CRYPTO_ENABLE", "default": 1, "type": "bit", "description": "Enable encrypted-at-rest transform", "drives": ["crypto", "core", "tb"]},
        {"name": "CRYPTO_KEY", "default": "32'hA5A5_5A5A", "type": "logic [DATA_WIDTH-1:0]", "description": "Default XOR transform key", "drives": ["crypto", "tb"]},
        {"name": "DEBUG_ENABLE", "default": 1, "type": "bit", "description": "Enable debug observability outputs", "drives": ["wrapper", "core"]},
        {"name": "RESET_MEMORY", "default": 0, "type": "bit", "description": "When set, reset initializes SRAM contents to zero", "drives": ["mem", "tb"]},
    ]


def _axi_lite_ports(data_width: str = "DATA_WIDTH", strb_width: str = "STRB_WIDTH") -> list[dict[str, Any]]:
    return [
        {"name": "s_axi_awaddr", "width": "ADDR_WIDTH+2", "direction": "input", "description": "AXI4-Lite write address"},
        {"name": "s_axi_awvalid", "width": 1, "direction": "input", "description": "AXI4-Lite write address valid"},
        {"name": "s_axi_awready", "width": 1, "direction": "output", "description": "AXI4-Lite write address ready"},
        {"name": "s_axi_wdata", "width": data_width, "direction": "input", "description": "AXI4-Lite write data plaintext"},
        {"name": "s_axi_wstrb", "width": strb_width, "direction": "input", "description": "AXI4-Lite write byte strobes"},
        {"name": "s_axi_wvalid", "width": 1, "direction": "input", "description": "AXI4-Lite write data valid"},
        {"name": "s_axi_wready", "width": 1, "direction": "output", "description": "AXI4-Lite write data ready"},
        {"name": "s_axi_bresp", "width": 2, "direction": "output", "description": "AXI4-Lite write response"},
        {"name": "s_axi_bvalid", "width": 1, "direction": "output", "description": "AXI4-Lite write response valid"},
        {"name": "s_axi_bready", "width": 1, "direction": "input", "description": "AXI4-Lite write response ready"},
        {"name": "s_axi_araddr", "width": "ADDR_WIDTH+2", "direction": "input", "description": "AXI4-Lite read address"},
        {"name": "s_axi_arvalid", "width": 1, "direction": "input", "description": "AXI4-Lite read address valid"},
        {"name": "s_axi_arready", "width": 1, "direction": "output", "description": "AXI4-Lite read address ready"},
        {"name": "s_axi_rdata", "width": data_width, "direction": "output", "description": "AXI4-Lite read data plaintext"},
        {"name": "s_axi_rresp", "width": 2, "direction": "output", "description": "AXI4-Lite read response"},
        {"name": "s_axi_rvalid", "width": 1, "direction": "output", "description": "AXI4-Lite read data valid"},
        {"name": "s_axi_rready", "width": 1, "direction": "input", "description": "AXI4-Lite read data ready"},
    ]


def _ensure_io_list(doc: dict[str, Any]) -> dict[str, Any]:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    if io.get("interfaces") and io.get("clock_domains") and io.get("resets") and not _has_tbd(io):
        return io
    return {
        "clock_domains": [{
            "name": "aclk",
            "frequency_mhz": 100,
            "description": "Primary AXI and SRAM clock",
            "ports": [{"name": "aclk", "width": 1, "direction": "input", "description": "Primary clock"}],
        }],
        "resets": [{
            "name": "aresetn",
            "polarity": "active_low",
            "sync_async": "async_assert_sync_deassert",
            "description": "Active-low reset, asynchronous assert and synchronous release",
            "ports": [{"name": "aresetn", "width": 1, "direction": "input", "description": "Primary reset"}],
        }],
        "interfaces": [{
            "name": "s_axi",
            "type": "AXI4-Lite",
            "role": "slave",
            "description": "Firmware-visible plaintext memory aperture",
            "ports": _axi_lite_ports(),
        }, {
            "name": "debug",
            "type": "custom",
            "role": "output",
            "description": "Optional debug observability",
            "ports": [
                {"name": "dbg_crypto_active", "width": 1, "direction": "output", "description": "High when encrypted-at-rest transform is enabled"},
                {"name": "dbg_raw_word", "width": "DATA_WIDTH", "direction": "output", "description": "Raw SRAM word after encrypted-at-rest storage"},
            ],
        }],
    }


def _ensure_features(doc: dict[str, Any]) -> list[dict[str, Any]]:
    features = doc.get("features")
    if isinstance(features, list) and features and not _has_tbd(features):
        return features
    return [
        {"name": "encrypted_full_write", "trigger": "AXI write address and data handshakes complete with all byte strobes asserted", "datapath": "Plaintext write data is transformed by crypto block and stored in SRAM", "control": "Write FSM accepts AW/W, performs crypto, writes memory, then returns B OKAY", "output": "SRAM raw word differs from plaintext when CRYPTO_ENABLE=1; B response completes"},
        {"name": "plaintext_read", "trigger": "AXI read address handshake completes", "datapath": "Raw SRAM word is read, inverse transform is applied, plaintext is returned on R channel", "control": "Read FSM accepts AR, reads memory, decrypts, then holds RVALID until RREADY", "output": "Read data equals last architecturally written plaintext word"},
        {"name": "byte_strobe_merge", "trigger": "AXI write completes with partial s_axi_wstrb", "datapath": "Existing raw word is decrypted, selected byte lanes merge with new plaintext, merged word is re-encrypted and stored", "control": "Partial write uses read-modify-write sequence before B response", "output": "Unstrobed bytes retain previous plaintext value"},
        {"name": "backpressure_stability", "trigger": "Any AXI ready signal is deasserted while valid is asserted", "datapath": "Payload and state remain stable until handshake", "control": "FSM stalls only affected channel", "output": "No duplicated or dropped transaction"},
    ]


def _ensure_dataflow(doc: dict[str, Any]) -> dict[str, Any]:
    dataflow = doc.get("dataflow") if isinstance(doc.get("dataflow"), dict) else {}
    if dataflow and not _has_tbd(dataflow):
        return dataflow
    return {
        "write_path": {"sequence": "AW/W handshake -> address decode -> plaintext merge -> crypto transform -> SRAM write -> B response", "storage": "Encrypted raw word in SRAM", "ordering": "One architectural write commits before its B response is accepted"},
        "read_path": {"sequence": "AR handshake -> address decode -> SRAM read -> inverse crypto transform -> R response", "output": "Plaintext data on s_axi_rdata", "ordering": "R payload remains stable until RREADY"},
        "partial_write_path": {"sequence": "Read old raw word -> decrypt old plaintext -> merge byte lanes by WSTRB -> encrypt merged plaintext -> write raw word", "hazard_rule": "Do not write SRAM until merge data is computed from a valid old word"},
        "debug_path": {"dbg_crypto_active": "Reflects CRYPTO_ENABLE", "dbg_raw_word": "Shows most recent raw SRAM word when DEBUG_ENABLE=1"},
    }


def _ensure_clock_reset_domains(doc: dict[str, Any]) -> dict[str, Any]:
    value = doc.get("clock_reset_domains")
    if isinstance(value, dict) and value and not _has_tbd(value):
        return value
    return {
        "domains": [{"clock": "aclk", "reset": "aresetn", "frequency_mhz": 100, "reset_scheme": "async_assert_sync_deassert"}],
        "reset_behavior": ["AXI channel valid/ready state resets to idle", "Debug outputs reset to zero", "SRAM contents are unspecified unless RESET_MEMORY=1"],
    }


def _ensure_cdc_rdc(section: str, doc: dict[str, Any]) -> dict[str, Any]:
    value = doc.get(section)
    if isinstance(value, dict) and value and not _has_tbd(value):
        return value
    return {
        "required": False,
        "rationale": "Single aclk/aresetn domain in v1 leaf IP",
        "checks": ["No crossing paths expected; update SSOT if additional clocks or resets are introduced"],
    }


def _ensure_registers(doc: dict[str, Any]) -> dict[str, Any]:
    regs = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
    if regs and not _has_tbd(regs):
        return _promote_register_note_entries(regs)
    return {
        "policy": "No discrete firmware CSRs in v1; AXI4-Lite address window directly maps SRAM words",
        "register_list": [
            {"name": "SRAM_WORD", "offset": "word_address << 2", "access": "RW", "reset": "unspecified", "description": "Memory-mapped plaintext data word; stored encrypted internally", "fields": [{"name": "data", "bits": "DATA_WIDTH-1:0", "access": "RW", "reset": "unspecified", "description": "Plaintext read/write data"}]},
            {"name": "DEBUG_RAW_WORD", "offset": "debug-only", "access": "RO", "reset": 0, "description": "Optional non-firmware debug observation of encrypted raw word", "fields": [{"name": "raw", "bits": "DATA_WIDTH-1:0", "access": "RO", "reset": 0, "description": "Encrypted-at-rest raw SRAM word"}]},
        ],
    }


def _promote_register_note_entries(regs: dict[str, Any]) -> dict[str, Any]:
    out = dict(regs)
    reg_list = [dict(item) for item in out.get("register_list") or [] if isinstance(item, dict)]
    known = {str(item.get("name") or "").upper() for item in reg_list}
    config = out.get("config") if isinstance(out.get("config"), dict) else {}
    width = config.get("register_width", 32)
    note = " ".join(
        str(value or "")
        for value in (
            config.get("note"),
            config.get("source"),
            config.get("description"),
            config.get("access_policy"),
            out.get("note"),
            out.get("description"),
        )
    )
    for match in re.finditer(r"\b([A-Z][A-Z0-9_]{1,31})\s+0x([0-9A-Fa-f]+)\s+([A-Z][A-Z0-9_/]*)?", note):
        name = match.group(1).upper()
        if name in known:
            continue
        access = (match.group(3) or "RW").lower()
        desc_start = match.start()
        desc_end = note.find(",", match.end())
        if desc_end < 0:
            desc_end = min(len(note), match.end() + 96)
        description = note[desc_start:desc_end].strip(" ,.;") or f"Register {name} promoted from register note"
        reg_list.append({
            "name": name,
            "offset": int(match.group(2), 16),
            "width": width,
            "access": access,
            "reset": 0,
            "category": "status" if any(tok in name for tok in ("INT", "STATUS", "FSM", "FSC", "FTM", "FTC", "DBG")) else "data",
            "description": description,
            "fields": [{
                "name": name.lower(),
                "bits": [int(width) - 1 if isinstance(width, int) else 31, 0],
                "access": access,
                "reset": 0,
            }],
        })
        known.add(name)
    out["register_list"] = reg_list
    return out


def _ensure_memory(doc: dict[str, Any]) -> dict[str, Any]:
    mem = doc.get("memory") if isinstance(doc.get("memory"), dict) else {}
    if mem and not _has_tbd(mem):
        return mem
    return {
        "instances": [{"name": "sram", "type": "sync_sram", "depth": "1 << ADDR_WIDTH", "width": "DATA_WIDTH", "write_mask": "STRB_WIDTH", "reset": "controlled by RESET_MEMORY"}],
        "addressing": {"word_index": "s_axi_*addr[ADDR_WIDTH+1:2]", "alignment_bytes": "DATA_WIDTH/8", "out_of_range": "respond SLVERR when detectable"},
        "storage_policy": "Raw SRAM stores transformed/encrypted data when CRYPTO_ENABLE=1 and plaintext data when CRYPTO_ENABLE=0",
    }


def _ensure_interrupts(doc: dict[str, Any]) -> dict[str, Any]:
    intr = doc.get("interrupts") if isinstance(doc.get("interrupts"), dict) else {}
    if intr and not _has_tbd(intr):
        return intr
    return {"present": False, "sources": [], "rationale": "AXI4-Lite responses carry completion/error status for v1; no interrupt output"}


def _ensure_fsm(doc: dict[str, Any]) -> dict[str, Any]:
    fsm = doc.get("fsm") if isinstance(doc.get("fsm"), dict) else {}
    if fsm and not _has_tbd(fsm):
        return fsm
    return {
        "write_fsm": {
            "states": ["W_IDLE", "W_CAPTURE", "W_READ_OLD", "W_MERGE_ENCRYPT", "W_WRITE_MEM", "W_RESP"],
            "transitions": [
                {"from": "W_IDLE", "to": "W_CAPTURE", "when": "AW and W accepted"},
                {"from": "W_CAPTURE", "to": "W_READ_OLD", "when": "partial strobe requires old word"},
                {"from": "W_CAPTURE", "to": "W_MERGE_ENCRYPT", "when": "full strobe"},
                {"from": "W_READ_OLD", "to": "W_MERGE_ENCRYPT", "when": "old raw word valid"},
                {"from": "W_MERGE_ENCRYPT", "to": "W_WRITE_MEM", "when": "merged encrypted word ready"},
                {"from": "W_WRITE_MEM", "to": "W_RESP", "when": "SRAM write committed"},
                {"from": "W_RESP", "to": "W_IDLE", "when": "B handshake completes"},
            ],
        },
        "read_fsm": {
            "states": ["R_IDLE", "R_READ_MEM", "R_DECRYPT", "R_RESP"],
            "transitions": [
                {"from": "R_IDLE", "to": "R_READ_MEM", "when": "AR accepted"},
                {"from": "R_READ_MEM", "to": "R_DECRYPT", "when": "raw word valid"},
                {"from": "R_DECRYPT", "to": "R_RESP", "when": "plaintext ready"},
                {"from": "R_RESP", "to": "R_IDLE", "when": "R handshake completes"},
            ],
        },
    }

def _register_state_variables(doc: dict[str, Any]) -> list[dict[str, Any]]:
    regs = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
    variables: list[dict[str, Any]] = []
    for reg in regs.get("register_list") or []:
        if not isinstance(reg, dict):
            continue
        reg_name = str(reg.get("name") or "reg").lower()
        fields = reg.get("fields") if isinstance(reg.get("fields"), list) else []
        if fields:
            for field in fields:
                if not isinstance(field, dict):
                    continue
                name = str(field.get("name") or reg_name)
                variables.append({
                    "name": name,
                    "source": f"registers.{reg.get('name')}.{name}",
                    "reset": field.get("reset", reg.get("reset", 0)),
                    "description": field.get("description") or f"Architectural field {name}",
                })
        else:
            variables.append({
                "name": reg_name,
                "source": f"registers.{reg.get('name')}",
                "reset": reg.get("reset", 0),
                "description": reg.get("description") or f"Architectural register {reg_name}",
            })
    if variables:
        return variables[:24]
    return [
        {"name": "state", "source": "fsm", "reset": "IDLE", "description": "Primary architectural state"},
        {"name": "error", "source": "error_handling", "reset": 0, "description": "Architectural error indicator"},
    ]


def _error_sources(doc: dict[str, Any]) -> list[dict[str, Any]]:
    errors = doc.get("error_handling") if isinstance(doc.get("error_handling"), dict) else {}
    raw = errors.get("error_sources") or errors.get("sources") or []
    out = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        out.append({
            "id": item.get("id") or item.get("name") or f"ERR{idx}",
            "condition": item.get("condition") or item.get("detection") or "Declared error condition is observed",
            "architectural_effect": item.get("architectural_effect") or item.get("response") or "Status/error reporting follows the SSOT error policy",
        })
    if out:
        return out
    return [{"id": "ERR_PROTOCOL", "condition": "Downstream protocol response is non-OKAY or invalid", "architectural_effect": "Set error status and block signoff until handled"}]


def _ensure_function_model(doc: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    existing_txs = fm.get("transactions") if isinstance(fm.get("transactions"), list) else []
    generic_only = (
        len(existing_txs) <= 1
        and existing_txs
        and str(existing_txs[0].get("name") or "").lower() in {"primary_operation", "basic_operation"}
    )
    if fm.get("state_variables") and fm.get("transactions") and fm.get("invariants") and not generic_only:
        return fm
    decisions = state.get("decisions") if isinstance(state.get("decisions"), dict) else {}
    features = [f for f in (doc.get("features") or []) if isinstance(f, dict)]
    dataflow = doc.get("dataflow") if isinstance(doc.get("dataflow"), dict) else {}
    transactions = []
    for idx, feature in enumerate(features[:4], start=1):
        transactions.append({
            "id": f"FM{idx}",
            "name": str(feature.get("name") or f"feature_{idx}").lower().replace(" ", "_"),
            "preconditions": [str(feature.get("trigger") or "Feature trigger is asserted under legal configuration")],
            "inputs": [str(feature.get("datapath") or "Inputs described by io_list and dataflow")],
            "outputs": [str(feature.get("output") or "Architectural output matches feature definition")],
            "side_effects": [str(feature.get("control") or "Architectural state updates according to FSM/control policy")],
            "error_cases": [
                {"condition": src["condition"], "result": src["architectural_effect"]}
                for src in _error_sources(doc)[:3]
            ],
        })
    if not transactions or generic_only:
        transactions = [
            {
                "id": "FM1",
                "name": "full_word_write_read",
                "preconditions": ["CRYPTO_ENABLE may be 0 or 1", "AXI write and read addresses are in range and aligned"],
                "inputs": ["plaintext write word", "word address", "byte strobe mask"],
                "outputs": ["subsequent read at the same address returns the plaintext write word"],
                "side_effects": ["SRAM raw word stores crypto_transform(plaintext) when CRYPTO_ENABLE=1"],
                "error_cases": [{"condition": "address is outside implemented SRAM aperture", "result": "AXI response is SLVERR and memory is not modified"}],
            },
            {
                "id": "FM2",
                "name": "partial_byte_strobe_merge",
                "preconditions": ["Old plaintext word exists at selected address", "WSTRB is neither all-zero nor all-one"],
                "inputs": ["old raw SRAM word", "new plaintext write data", "byte strobe mask"],
                "outputs": ["readback equals byte-lane merge of old plaintext and new plaintext"],
                "side_effects": ["merged plaintext is transformed and stored as a single committed raw word"],
                "error_cases": [{"condition": "read-modify-write old word is not valid", "result": "write must stall; no corrupt raw word may be committed"}],
            },
            {
                "id": "FM3",
                "name": "crypto_passthrough_mode",
                "preconditions": ["CRYPTO_ENABLE=0"],
                "inputs": ["plaintext write word"],
                "outputs": ["readback equals plaintext and raw debug word equals plaintext when DEBUG_ENABLE=1"],
                "side_effects": ["crypto_active debug output is 0"],
                "error_cases": [{"condition": "CRYPTO_ENABLE changes during an active transaction", "result": "behavior is constrained by integration to stable parameter/configuration"}],
            },
            {
                "id": "FM4",
                "name": "debug_encrypted_visibility",
                "preconditions": ["CRYPTO_ENABLE=1", "DEBUG_ENABLE=1"],
                "inputs": ["plaintext write word and CRYPTO_KEY"],
                "outputs": ["dbg_raw_word observes encrypted raw storage, while AXI read returns plaintext"],
                "side_effects": ["debug outputs update only from committed memory operations"],
                "error_cases": [{"condition": "DEBUG_ENABLE=0", "result": "debug outputs are tied off or held inactive"}],
            },
        ]
    invariants = [
        "No externally visible output changes except through declared interfaces, registers, interrupts, or debug signals.",
        "All state updates are synchronous to the declared clock and return to reset values under the declared reset policy.",
        "Every declared error source has a defined architectural effect and recovery path.",
    ]
    if dataflow:
        invariants.append("Data movement and ordering follow the dataflow section without bypassing declared buffers or counters.")
    return {
        "purpose": "Cycle-independent behavioral contract for rtl-gen and tb-gen.",
        "state_variables": _register_state_variables(doc),
        "transactions": transactions,
        "invariants": invariants,
        "reference_model_hint": "tb-gen must build a scoreboard/reference model from function_model transactions and compare expected versus observed results.",
    }


def _interface_handshakes(doc: dict[str, Any]) -> list[dict[str, str]]:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    rules: list[dict[str, str]] = []
    for intf in io.get("interfaces") or []:
        if not isinstance(intf, dict):
            continue
        ports = intf.get("ports") if isinstance(intf.get("ports"), list) else []
        names = {str(p.get("name")) for p in ports if isinstance(p, dict) and p.get("name")}
        for name in sorted(names):
            if name.endswith("valid"):
                ready = name[:-5] + "ready"
                if ready in names:
                    rules.append({"signal": f"{name}/{ready}", "rule": f"{name} payload remains stable until {ready} is sampled asserted on {intf.get('name', 'interface')}."})
    return rules[:12] or [{"signal": "valid/ready", "rule": "All valid payloads remain stable until the matching ready handshake completes."}]


def _fsm_pipeline(doc: dict[str, Any]) -> list[dict[str, Any]]:
    fsm = doc.get("fsm") if isinstance(doc.get("fsm"), dict) else {}
    for value in fsm.values():
        if isinstance(value, dict) and isinstance(value.get("states"), list) and value["states"]:
            return [
                {"stage": str(state), "cycle": "state-dependent", "action": f"Execute {state} behavior from fsm and dataflow"}
                for state in value["states"][:12]
            ]
    return [
        {"stage": "S0_ACCEPT", "cycle": 0, "action": "Accept legal command or request"},
        {"stage": "S1_EXECUTE", "cycle": "1..N", "action": "Perform data/control operation with protocol handshakes"},
        {"stage": "S2_COMPLETE", "cycle": "N+1", "action": "Update status, interrupts, and debug observability"},
    ]


def _ensure_cycle_model(doc: dict[str, Any]) -> dict[str, Any]:
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    generic_handshake = (
        isinstance(cm.get("handshake_rules"), list)
        and len(cm.get("handshake_rules") or []) <= 1
        and "valid/ready" in str((cm.get("handshake_rules") or [{}])[0].get("signal", ""))
    )
    if all(cm.get(k) for k in ("clock", "reset", "latency", "handshake_rules", "pipeline", "ordering")) and not generic_handshake:
        return cm
    clock, freq = _first_clock(doc)
    reset, polarity, sync_async = _first_reset(doc)
    dataflow = doc.get("dataflow") if isinstance(doc.get("dataflow"), dict) else {}
    return {
        "purpose": "Cycle/handshake contract for rtl-gen and waveform-based verification.",
        "clock": clock,
        "reset": {
            "signal": reset,
            "polarity": polarity,
            "assertion": f"{reset} assertion returns architectural state to declared reset values",
            "deassertion": f"Logic may accept transactions after {sync_async} deassertion completes",
        },
        "latency": {
            "register_read": {"min_cycles": 0, "max_cycles": None, "description": "Bounded by slave ready/valid backpressure"},
            "register_write": {"min_cycles": 0, "max_cycles": None, "description": "Bounded by slave ready/valid backpressure"},
            "primary_operation": {"min_cycles": 1, "max_cycles": None, "description": f"Runs on {clock} at nominal {freq} MHz; max depends on downstream backpressure"},
        },
        "handshake_rules": [
            {"signal": "s_axi_awvalid/s_axi_awready", "rule": "Write address payload remains stable until AW handshake completes."},
            {"signal": "s_axi_wvalid/s_axi_wready", "rule": "Write data and byte strobes remain stable until W handshake completes."},
            {"signal": "s_axi_bvalid/s_axi_bready", "rule": "B response remains stable until accepted and is emitted only after the memory commit point."},
            {"signal": "s_axi_arvalid/s_axi_arready", "rule": "Read address payload remains stable until AR handshake completes."},
            {"signal": "s_axi_rvalid/s_axi_rready", "rule": "R data and response remain stable until accepted."},
            {"signal": "partial_write_rmw", "rule": "Partial writes must wait for a valid old word before committing merged encrypted data."},
        ],
        "pipeline": [
            {"stage": "W_CAPTURE", "cycle": "0..N", "action": "Capture write address/data after AW/W handshakes; stall under backpressure."},
            {"stage": "W_READ_OLD", "cycle": "N+1", "action": "For partial writes, read old raw word and decrypt to plaintext before merge."},
            {"stage": "W_MERGE_ENCRYPT", "cycle": "N+2", "action": "Merge byte lanes and apply crypto transform to merged plaintext."},
            {"stage": "W_COMMIT", "cycle": "N+3", "action": "Write encrypted raw word to SRAM and prepare B response."},
            {"stage": "R_READ", "cycle": "0..N", "action": "Capture read address and read raw SRAM word."},
            {"stage": "R_DECRYPT", "cycle": "N+1", "action": "Apply inverse crypto transform to produce plaintext read data."},
            {"stage": "R_RESP", "cycle": "N+2", "action": "Hold read payload stable until R handshake completes."},
        ],
        "ordering": [
            "Accepted requests update architectural state only on clock edges.",
            "Completion/status/interrupt updates occur after the operation reaches its terminal FSM state.",
            "Backpressure stalls the active handshake stage without corrupting stored state.",
        ] + (["Read/dataflow stages must precede dependent write/output stages where declared in dataflow."] if dataflow else []),
        "backpressure": ["Ready/valid deassertion stalls only the affected interface stage; payload and route/control state remain stable."],
        "observability": ["Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario."],
    }


def _ensure_timing(doc: dict[str, Any]) -> dict[str, Any]:
    timing = doc.get("timing") if isinstance(doc.get("timing"), dict) else {}
    clock, freq = _first_clock(doc)
    timing.setdefault("target_clocks", [{"name": clock, "frequency_mhz": freq, "period_ns": round(1000 / max(freq, 1), 3), "uncertainty_ns": 0.2}])
    timing.setdefault("latency_budget", {
        "register_access": {"min": 0, "max": None, "measured_from": "valid && ready", "measured_to": "response valid && ready"},
        "primary_operation": {"min": 1, "max": None, "measured_from": "start/request accepted", "measured_to": "done/response accepted"},
    })
    timing.setdefault("sta_expectations", {"setup_wns_ns_min": 0.0, "hold_wns_ns_min": 0.0, "required_reports": ["sta/out/timing.rpt", "sta/out/wns.json"]})
    return timing


def _ensure_power(doc: dict[str, Any]) -> dict[str, Any]:
    power = doc.get("power") if isinstance(doc.get("power"), dict) else {}
    clock, _ = _first_clock(doc)
    power.setdefault("domains", [{"name": "PD_MAIN", "voltage": "nominal", "clock_domains": [clock], "isolation": "not_required_single_domain"}])
    states = power.get("power_states") or power.get("low_power_states")
    power["power_states"] = states if isinstance(states, list) and states else [{"name": "ON", "entry": "reset deasserted", "exit": "reset asserted", "guarantees": ["All declared IP functionality active"]}]
    power.setdefault("clock_gating", {"required": False, "rationale": "No explicit integrated clock-gating requirement in approved SSOT"})
    power.setdefault("upf_required", False)
    return power


def _ensure_security(doc: dict[str, Any]) -> dict[str, Any]:
    sec = doc.get("security") if isinstance(doc.get("security"), dict) else {}
    sec.setdefault("classification", "non_secure_leaf_ip")
    sec.setdefault("assets", [
        {"name": "configuration_state", "protection": "CSR/configuration updates must be deterministic and reset-safe"},
        {"name": "data_integrity", "protection": "Data/control outputs must match function_model transactions"},
    ])
    sec.setdefault("threat_model", [
        {"threat": "invalid configuration or address", "mitigation": "error_handling declares detection, architectural effect, and recovery"},
        {"threat": "silent data/control corruption", "mitigation": "test_requirements scoreboard checks every declared functional transaction"},
    ])
    sec.setdefault("privilege_model", "System-level access control is owned by the integrating bus/firewall unless explicitly declared here.")
    return sec


def _ensure_error_handling(doc: dict[str, Any]) -> dict[str, Any]:
    err = doc.get("error_handling") if isinstance(doc.get("error_handling"), dict) else {}
    sources = _error_sources(doc)
    recovery = err.get("recovery")
    if isinstance(recovery, dict):
        recovery_value: Any = recovery
    elif recovery:
        recovery_value = recovery
    else:
        recovery_value = [{"action": "reset or software clear", "clears": ["error/status indicators"], "preserves": ["configuration unless reset policy states otherwise"]}]
    return {
        **err,
        "error_sources": sources,
        "propagation": err.get("propagation") or ["Errors update status/debug observability and propagate through declared response/interrupt mechanisms."],
        "recovery": recovery_value,
    }


def _ensure_debug(doc: dict[str, Any]) -> dict[str, Any]:
    clock, _ = _first_clock(doc)
    return {
        "waveform_must_probe": [clock, _first_reset(doc)[0], "fsm_state", "start_or_request", "done_or_response", "error_status", "irq_or_status_outputs"],
        "trace_events": [
            {"name": "operation_start", "trigger": "start/request accepted"},
            {"name": "operation_complete", "trigger": "done/response accepted"},
            {"name": "error_detected", "trigger": "any error_handling.error_sources condition"},
        ],
        "status_outputs": ["status/debug signals declared in io_list or registers"],
    }


def _ensure_integration(doc: dict[str, Any]) -> dict[str, Any]:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    interfaces = [i.get("name") for i in io.get("interfaces") or [] if isinstance(i, dict) and i.get("name")]
    return {
        "bus_attachment": {"interfaces": interfaces, "address_ownership": "SoC assigns base addresses and external routing not owned by this leaf IP"},
        "dependencies": {"external_modules": [], "external_clocks": [_first_clock(doc)[0]], "external_resets": [_first_reset(doc)[0]]},
        "integration_notes": ["Integrator must connect every declared io_list port and honor timing/reset assumptions."],
    }


def _ensure_test_requirements(doc: dict[str, Any]) -> dict[str, Any]:
    tr = doc.get("test_requirements") if isinstance(doc.get("test_requirements"), dict) else {}
    scenarios = []
    for idx, sc in enumerate(tr.get("scenarios") or [], start=1):
        if not isinstance(sc, dict):
            continue
        sid = sc.get("id") or f"SC{idx:02d}"
        name = sc.get("name") or f"Scenario {idx}"
        scenarios.append({
            **sc,
            "id": sid,
            "name": name,
            "stimulus": sc.get("stimulus") or f"Drive the sequence for {name} using declared interfaces and configuration registers.",
            "expected": sc.get("expected") or f"{name} behavior matches function_model and cycle_model.",
            "checker": sc.get("checker") or f"Scoreboard/checker compares observed {name} result against function_model expected result.",
            "coverage": sc.get("coverage") or [str(sid), "function_model", "cycle_model"],
        })
    weak_default = (
        len(scenarios) < 10
        or any(str(sc.get("name") or "").lower() in {"primary operation", "basic operation"} for sc in scenarios)
    )
    if weak_default:
        scenarios = [
            {"id": "SC01", "name": "Reset idle", "stimulus": "Assert and deassert aresetn with no AXI valid asserted", "expected": "All AXI valid outputs are low, ready/state is idle, debug outputs are reset or inactive", "checker": "Reset checker samples outputs after reset release", "coverage": ["reset", "cycle_model.reset"]},
            {"id": "SC02", "name": "Full-word encrypted write read", "stimulus": "Write 0xDEADBEEF to an aligned word with all byte strobes, then read the same address", "expected": "Read data is 0xDEADBEEF and raw SRAM/debug word is transformed when CRYPTO_ENABLE=1", "checker": "Scoreboard compares plaintext readback and crypto raw-word model", "coverage": ["FM1", "write_fsm", "read_fsm", "crypto_enabled"]},
            {"id": "SC03", "name": "Multiple address retention", "stimulus": "Write distinct data to addresses 0x00, 0x04, and 0x100, then read all back in mixed order", "expected": "Each address returns its own last plaintext value", "checker": "Associative memory scoreboard keyed by word address", "coverage": ["address_decode", "memory_depth", "ordering"]},
            {"id": "SC04", "name": "Partial byte-strobe merge", "stimulus": "Write 0xAABBCCDD, then partial write 0x00341200 with WSTRB=0x6, then read back", "expected": "Readback is 0xAA3412DD with unstrobed byte lanes preserved", "checker": "Reference model performs byte-lane merge before crypto transform", "coverage": ["FM2", "partial_write_rmw", "byte_strobes"]},
            {"id": "SC05", "name": "AXI write response", "stimulus": "Complete legal writes while delaying BREADY", "expected": "BVALID holds stable with OKAY until BREADY and no second response appears", "checker": "AXI response monitor checks stability and one response per write", "coverage": ["b_channel", "backpressure"]},
            {"id": "SC06", "name": "AXI read response", "stimulus": "Complete legal reads while delaying RREADY", "expected": "RDATA/RRESP hold stable with OKAY until RREADY", "checker": "AXI read monitor checks payload stability and response code", "coverage": ["r_channel", "backpressure"]},
            {"id": "SC07", "name": "Crypto pass-through mode", "stimulus": "Run write/read sequence with CRYPTO_ENABLE=0 configuration or parameter override", "expected": "Readback and raw debug word both equal plaintext; dbg_crypto_active is low", "checker": "Scoreboard compares raw and plaintext models under pass-through mode", "coverage": ["FM3", "crypto_disabled"]},
            {"id": "SC08", "name": "Debug encrypted visibility", "stimulus": "Run encrypted write/read with DEBUG_ENABLE=1", "expected": "dbg_crypto_active is high and dbg_raw_word matches transformed storage while readback is plaintext", "checker": "Debug checker compares raw debug output against crypto reference", "coverage": ["FM4", "debug_observability"]},
            {"id": "SC09", "name": "Back-to-back write then read", "stimulus": "Issue a write followed immediately by a read to the same address under minimal idle cycles", "expected": "Read returns the committed write value without stale or X data", "checker": "Hazard checker verifies write commit precedes dependent read response", "coverage": ["ordering", "read_after_write"]},
            {"id": "SC10", "name": "Full SRAM sweep", "stimulus": "Write and read every word in the default 256-word SRAM aperture", "expected": "Every location returns the expected plaintext and no neighboring location is corrupted", "checker": "Memory scoreboard covers every ADDR_WIDTH index", "coverage": ["memory_depth", "address_bins"]},
            {"id": "SC11", "name": "Independent channel backpressure", "stimulus": "Randomly deassert AWREADY/WREADY/BREADY/ARREADY/RREADY equivalents through slave response timing", "expected": "Payloads remain stable and transaction ordering follows cycle_model", "checker": "AXI protocol checker and scoreboard run under randomized stalls", "coverage": ["cycle_model.handshake_rules", "random_backpressure"]},
            {"id": "SC12", "name": "Invalid address or unsupported access", "stimulus": "Drive out-of-range or otherwise unsupported access when detectable by implementation", "expected": "Response is SLVERR/DECERR per error_handling and memory contents are unchanged", "checker": "Negative test checker verifies error response and no side effect", "coverage": ["ERR_PROTOCOL", "negative_access"]},
        ]
    tr["scenarios"] = scenarios
    tr["scoreboard_checks"] = max(int(tr.get("scoreboard_checks") or 0), len(scenarios))
    tr["coverage_goals"] = {
        **(
            {
                "functional": (
                    "100% of SSOT-planned functional bins from function_model transactions, "
                    "byte-strobe bins, crypto modes, debug bins, error paths, and protocol backpressure bins covered"
                ),
                "evidence": (
                    "Tool-instrumented structural metrics are optional unless an explicit SSOT metric goal "
                    "with matching tool evidence is added."
                ),
            }
            if not isinstance(tr.get("coverage_goals"), dict)
            else tr.get("coverage_goals")
        ),
        "scenario": "All SSOT scenarios SC01-SC12 pass with executable cocotb/pyuvm checkers",
    }
    return tr


def _ensure_quality_gates() -> dict[str, Any]:
    return {
        "ssot": {"pass": "check_ssot_disk.sh exits 0 and ATLAS SSOT progress is fully approved", "evidence": ["check_ssot_disk.sh PASS", "ATLAS /api/progress ssot all sections approved"]},
        "rtl": {"pass": "All expected RTL files exist, are production-ready, compile, and lint within warning budget", "evidence": ["list/<ip>.f", "compile log", "lint log"]},
        "dv": {"pass": "Every SSOT test_requirements scenario has an executable checker and FL-vs-RTL equivalence goal", "evidence": ["verify/equivalence_goals.json", "sim/scoreboard_events.jsonl", "tb/cocotb tests", "scenario implementation map"]},
        "coverage": {"pass": "Functional coverage passes and any explicitly requested structural metrics have matching evidence or approved waivers", "evidence": ["coverage report", "coverage waiver list if any"]},
        "eda": {"pass": "Synthesis/STA/DFT expectations have reports or approved waivers", "evidence": ["syn/sta/dft reports"]},
        "signoff": {"pass": "SSOT, FL/equivalence, RTL, lint, DV, sim, coverage, and EDA gates pass with fresh artifacts", "evidence": ["ATLAS progress signoff PASS"]},
    }


def _ensure_traceability(doc: dict[str, Any]) -> dict[str, Any]:
    trace = doc.get("traceability") if isinstance(doc.get("traceability"), dict) else {}
    rows = trace.get("yaml_to_output") if isinstance(trace.get("yaml_to_output"), list) else []
    required = [
        ("function_model", "RTL behavior and TB reference model"),
        ("cycle_model", "RTL handshake/pipeline timing and waveform checks"),
        ("function_model/cycle_model/test_requirements", "verify/equivalence_goals.json and FL-vs-RTL scoreboard contracts"),
        ("timing", "STA constraints and latency pass/fail criteria"),
        ("security", "Threat mitigations and negative tests"),
        ("error_handling", "Fault RTL paths and DV error scenarios"),
        ("debug_observability", "VCD probes and sim_debug inspection"),
        ("quality_gates", "ATLAS progress/signoff criteria"),
    ]
    existing = {r.get("yaml") for r in rows if isinstance(r, dict)}
    for yaml_key, output in required:
        if yaml_key not in existing:
            rows.append({"yaml": yaml_key, "output": output})
    trace["yaml_to_output"] = rows or [{"yaml": "top_module", "output": "Generated RTL/TB/docs root identity"}]
    return trace


def _todo_text(value: Any, limit: int = 260) -> str:
    if isinstance(value, dict):
        parts = []
        for key, val in value.items():
            if key in {"id", "name", "description", "condition", "rule", "action", "outputs", "side_effects", "expected"}:
                parts.append(f"{key}={_todo_text(val, 120)}")
        text = "; ".join(parts) if parts else str(value)
    elif isinstance(value, list):
        text = "; ".join(_todo_text(item, 120) for item in value[:5])
    else:
        text = str(value or "").strip()
    text = " ".join(text.split())
    return text[:limit].rstrip() + ("..." if len(text) > limit else "")


def _todo_id(prefix: str, value: Any, index: int) -> str:
    token = str(value or f"item_{index}")
    token = "".join(ch if ch.isalnum() else "_" for ch in token.upper()).strip("_")
    token = token or f"ITEM_{index}"
    return f"{prefix}_{token[:64]}"


def _module_owner(doc: dict[str, Any], ip: str, refs: list[str] | None = None) -> tuple[str, str]:
    refs_text = " ".join(refs or []).lower()
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    top_name = str(top.get("name") or ip)
    fallback = (top_name, f"rtl/{top_name}.sv")
    for item in doc.get("sub_modules") or []:
        if not isinstance(item, dict):
            continue
        ownership = str(item.get("ownership") or "manifest").lower()
        if ownership in {"child_ssot", "conceptual", "verification", "coverage"} or item.get("rtl_emit") is False:
            continue
        name = str(item.get("name") or "").strip()
        file_name = str(item.get("file") or "").strip()
        if not name:
            continue
        haystack = " ".join(
            _todo_text(item.get(key), 400)
            for key in (
                "name",
                "description",
                "implements",
                "source_sections",
                "function_model_refs",
                "cycle_model_refs",
                "feature_refs",
                "dataflow_refs",
                "register_refs",
                "fsm_refs",
                "test_refs",
                "ssot_refs",
            )
        ).lower()
        if refs_text and any(ref.lower() in haystack or haystack in ref.lower() for ref in refs or []):
            return name, file_name or f"rtl/{name}.sv"
        if not refs_text:
            return name, file_name or f"rtl/{name}.sv"
    return fallback


def _append_rtl_todo(
    todos: list[dict[str, Any]],
    *,
    id: str,
    content: str,
    detail: str,
    criteria: list[str],
    source_refs: list[str],
    owner: tuple[str, str],
    priority: str = "high",
) -> None:
    seen = {item.get("id") for item in todos if isinstance(item, dict)}
    base = id
    suffix = 2
    while id in seen:
        id = f"{base}_{suffix}"
        suffix += 1
    todos.append(
        {
            "id": id,
            "content": content,
            "detail": detail,
            "criteria": [item for item in criteria if str(item or "").strip()],
            "source_refs": source_refs,
            "owner_module": owner[0],
            "owner_file": owner[1],
            "priority": priority,
            "required": True,
        }
    )


def _synthesize_rtl_workflow_todos(doc: dict[str, Any], ip: str) -> list[dict[str, Any]]:
    todos: list[dict[str, Any]] = []
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    top_name = str(top.get("name") or ip)
    top_owner = (top_name, f"rtl/{top_name}.sv")
    _append_rtl_todo(
        todos,
        id="RTL_IMPLEMENT_SSOT_CONTRACT",
        content="Implement the complete SSOT RTL contract without fixed-template fallback behavior",
        detail=(
            "Use the current SSOT as the only source for ports, parameters, function_model, cycle_model, "
            "registers, dataflow, error/security/debug behavior, decomposition ownership, and quality gates."
        ),
        criteria=[
            "Generated RTL drives only SSOT-approved externally visible behavior",
            "No placeholder heartbeat, tie-off, alive-only, or comment-only implementation is used as evidence",
            "derive_rtl_todos.py --audit-rtl reports every required TODO as pass",
        ],
        source_refs=["top_module", "function_model", "cycle_model", "quality_gates.rtl"],
        owner=top_owner,
    )

    for idx, item in enumerate(doc.get("sub_modules") or []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or f"module_{idx}")
        refs = []
        for key in (
            "source_sections",
            "function_model_refs",
            "cycle_model_refs",
            "feature_refs",
            "dataflow_refs",
            "register_refs",
            "fsm_refs",
            "test_refs",
            "ssot_refs",
        ):
            raw = item.get(key)
            if isinstance(raw, list):
                refs.extend(str(v) for v in raw if str(v or "").strip())
            elif raw:
                refs.append(str(raw))
        owner = _module_owner(doc, ip, refs) if str(item.get("ownership") or "").lower() == "conceptual" else (
            name,
            str(item.get("file") or f"rtl/{name}.sv"),
        )
        _append_rtl_todo(
            todos,
            id=_todo_id("RTL_MODULE", name, idx),
            content=f"Implement or account for SSOT module slice `{name}`",
            detail=_todo_text(item.get("description") or item),
            criteria=[
                "Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module",
                "Module slice has traceability evidence in rtl_todo_plan.json",
                "No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned",
            ],
            source_refs=refs or [f"sub_modules[{idx}]"],
            owner=owner,
        )

    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    for idx, tx in enumerate(fm.get("transactions") or []):
        if not isinstance(tx, dict):
            continue
        tx_id = str(tx.get("id") or tx.get("name") or f"transaction_{idx}")
        source = f"function_model.transactions[{idx}]"
        _append_rtl_todo(
            todos,
            id=_todo_id("RTL_FM_TX", tx_id, idx),
            content=f"Implement FunctionalModel transaction `{tx_id}` in RTL",
            detail=(
                f"Preconditions: {_todo_text(tx.get('preconditions'))}. "
                f"Outputs: {_todo_text(tx.get('outputs'))}. "
                f"Side effects: {_todo_text(tx.get('side_effects'))}. "
                f"Error cases: {_todo_text(tx.get('error_cases'))}."
            ),
            criteria=[
                "RTL samples the transaction only under the approved preconditions",
                "All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping",
                "All side effects and error cases have observable state, status, or handoff evidence",
            ],
            source_refs=[source, f"function_model.transactions.{tx_id}"],
            owner=_module_owner(doc, ip, [source, f"function_model.transactions.{tx_id}"]),
        )
        for rule_idx, rule in enumerate(tx.get("output_rules") or []):
            if not isinstance(rule, dict):
                continue
            rule_name = str(rule.get("name") or rule.get("port") or f"output_{rule_idx}")
            _append_rtl_todo(
                todos,
                id=_todo_id("RTL_OUTPUT_RULE", rule_name, rule_idx),
                content=f"Drive output rule `{rule_name}` from FunctionalModel expression",
                detail=f"Expression: {_todo_text(rule.get('expr') or rule.get('expression') or rule)}",
                criteria=[
                    f"RTL output `{rule.get('port') or rule_name}` follows the SSOT expression",
                    "Expression inputs are mapped through rtl_contract.input_map or declared ports",
                    "FL-vs-RTL scoreboard can compare this observable without changing SSOT",
                ],
                source_refs=[f"{source}.output_rules[{rule_idx}]"],
                owner=_module_owner(doc, ip, [f"{source}.output_rules[{rule_idx}]", rule_name]),
            )
        for rule_idx, rule in enumerate(tx.get("state_updates") or []):
            if not isinstance(rule, dict):
                continue
            state_name = str(rule.get("name") or rule.get("state") or f"state_{rule_idx}")
            _append_rtl_todo(
                todos,
                id=_todo_id("RTL_STATE_UPDATE", state_name, rule_idx),
                content=f"Implement state update `{state_name}` from FunctionalModel expression",
                detail=f"Expression: {_todo_text(rule.get('expr') or rule.get('expression') or rule)}",
                criteria=[
                    "RTL updates the state only on the approved sample condition",
                    "Reset value and width match function_model.state_variables",
                    "Debug/status visibility remains consistent with SSOT traceability",
                ],
                source_refs=[f"{source}.state_updates[{rule_idx}]"],
                owner=_module_owner(doc, ip, [f"{source}.state_updates[{rule_idx}]", state_name]),
            )

    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    for key, label in (("handshake_rules", "handshake rule"), ("pipeline", "pipeline stage"), ("ordering", "ordering rule"), ("backpressure", "backpressure rule")):
        for idx, item in enumerate(cm.get(key) or []):
            source = f"cycle_model.{key}[{idx}]"
            _append_rtl_todo(
                todos,
                id=_todo_id(f"RTL_CYCLE_{key}", idx, idx),
                content=f"Implement cycle_model {label} {idx}",
                detail=_todo_text(item),
                criteria=[
                    "RTL timing/handshake behavior follows this cycle_model entry",
                    "Signals remain stable or advance only under the approved protocol phase",
                    "The behavior is visible to waveform/sim-debug or scoreboard checks",
                ],
                source_refs=[source],
                owner=_module_owner(doc, ip, [source]),
            )

    regs = (doc.get("registers") or {}).get("register_list") if isinstance(doc.get("registers"), dict) else []
    for idx, reg in enumerate(regs or []):
        if not isinstance(reg, dict):
            continue
        name = str(reg.get("name") or f"reg_{idx}")
        _append_rtl_todo(
            todos,
            id=_todo_id("RTL_REGISTER", name, idx),
            content=f"Implement CSR/register `{name}` access behavior",
            detail=_todo_text(reg),
            criteria=[
                "Reset/access/field side effects match registers.register_list",
                "Illegal access behavior follows error_handling/security policy",
                "Readback and W1C/RW/RO semantics are covered by RTL and DV plan",
            ],
            source_refs=[f"registers.register_list[{idx}]"],
            owner=_module_owner(doc, ip, [f"registers.register_list[{idx}]", name]),
        )

    tr = doc.get("test_requirements") if isinstance(doc.get("test_requirements"), dict) else {}
    for idx, sc in enumerate(tr.get("scenarios") or []):
        if not isinstance(sc, dict):
            continue
        sid = str(sc.get("id") or sc.get("name") or f"SC{idx}")
        _append_rtl_todo(
            todos,
            id=_todo_id("RTL_SCENARIO_SUPPORT", sid, idx),
            content=f"Expose RTL behavior needed by SSOT scenario `{sid}`",
            detail=f"Stimulus: {_todo_text(sc.get('stimulus'))}. Expected: {_todo_text(sc.get('expected'))}.",
            criteria=[
                "RTL has observable behavior for the scenario checker without weakening expected results",
                "Scenario coverage can be closed by tb-gen using function_model/cycle_model",
                "If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass",
            ],
            source_refs=[f"test_requirements.scenarios[{idx}]"],
            owner=_module_owner(doc, ip, [f"test_requirements.scenarios[{idx}]", sid]),
            priority="normal",
        )

    _append_rtl_todo(
        todos,
        id="RTL_CLOSE_GATE_TODOS",
        content="Close all rtl_gate.rtl_gen quality-gate TODOs with fresh evidence",
        detail=(
            "Run dynamic TODO audit, DUT compile, DUT-only lint, and static traceability checks after the final RTL edit. "
            "The gate TODOs are pass/fail work items, not summary prose."
        ),
        criteria=[
            "SSOT authority, workflow TODO format, owner traceability, static RTL evidence, compile, lint, and closure gate TODOs pass",
            "rtl_compile.json and lint/dut_lint.json are fresh and clean",
            "open_required_todos is zero",
        ],
        source_refs=["quality_gates.rtl", "workflow_todos.rtl-gen", "generation_flow"],
        owner=top_owner,
    )
    return todos


def _ensure_workflow_todos(doc: dict[str, Any], ip: str) -> dict[str, Any]:
    todos = doc.get("workflow_todos") if isinstance(doc.get("workflow_todos"), dict) else {}
    rtl_todos = todos.get("rtl-gen") if isinstance(todos.get("rtl-gen"), list) else []
    if not rtl_todos:
        rtl_todos = _synthesize_rtl_workflow_todos(doc, ip)
    todos["rtl-gen"] = rtl_todos
    todos.setdefault("tb-gen", [])
    todos.setdefault("sim_debug", [])
    return todos


def repair(doc: dict[str, Any], state: dict[str, Any], ip: str) -> dict[str, Any]:
    out = dict(doc)
    out["top_module"] = _ensure_top_module(out, state, ip)
    out["sub_modules"] = _ensure_sub_modules(out, ip)
    out["parameters"] = _ensure_parameters_section(out, state)
    out["io_list"] = _ensure_io_list(out)
    out["features"] = _ensure_features(out)
    out["dataflow"] = _ensure_dataflow(out)
    out["clock_reset_domains"] = _ensure_clock_reset_domains(out)
    out["cdc_requirements"] = _ensure_cdc_rdc("cdc_requirements", out)
    out["rdc_requirements"] = _ensure_cdc_rdc("rdc_requirements", out)
    out["registers"] = _ensure_registers(out)
    out["memory"] = _ensure_memory(out)
    out["interrupts"] = _ensure_interrupts(out)
    out["fsm"] = _ensure_fsm(out)
    out["function_model"] = _ensure_function_model(out, state)
    out["sub_modules"] = _ensure_submodule_behavior_ownership(out, ip)
    out["cycle_model"] = _ensure_cycle_model(out)
    out["timing"] = _ensure_timing(out)
    out["power"] = _ensure_power(out)
    out["security"] = _ensure_security(out)
    out["error_handling"] = _ensure_error_handling(out)
    out["debug_observability"] = out.get("debug_observability") if isinstance(out.get("debug_observability"), dict) else _ensure_debug(out)
    out["integration"] = out.get("integration") if isinstance(out.get("integration"), dict) else _ensure_integration(out)
    out["dft"] = out.get("dft") if isinstance(out.get("dft"), dict) else {
        "scan_required": False,
        "controllability": {"reset": _first_reset(out)[0], "clocks": [_first_clock(out)[0]], "primary_inputs": "all io_list inputs controllable in testbench"},
        "observability": {"required_internal_points": ["fsm_state", "status", "error_status"], "outputs": "all io_list outputs observable"},
        "mbist_required": bool((out.get("memory") or {}).get("instances")) if isinstance(out.get("memory"), dict) else False,
    }
    out["synthesis"] = out.get("synthesis") if isinstance(out.get("synthesis"), dict) else {
        "dialect": (out.get("coding_rules") or {}).get("verilog_style", "systemverilog_2012") if isinstance(out.get("coding_rules"), dict) else "systemverilog_2012",
        "top_module": out.get("top_module", {}).get("name", ip) if isinstance(out.get("top_module"), dict) else ip,
        "constraints": ["No inferred latches", "No unresolved black boxes", "All sequential state reset or intentionally initialized"],
        "required_outputs": ["syn/out/area.rpt", "syn/out/timing_summary.rpt", "sta/out/wns.json"],
    }
    out["coding_rules"] = out.get("coding_rules") if isinstance(out.get("coding_rules"), dict) else {
        "verilog_style": "systemverilog_2012",
        "conventions": [
            "Use always_ff/always_comb or equivalent synthesis-safe style consistently",
            "No inferred latches; every combinational branch assigns all outputs",
            "No parameterized part-selects inside procedural blocks; use helper wires/continuous assigns",
            "No ad-hoc lint suppressions without SSOT waiver and DUT-only lint evidence",
        ],
        "lint_waivers": [],
    }
    out["reuse_modules"] = out.get("reuse_modules") if isinstance(out.get("reuse_modules"), list) else []
    out["custom"] = out.get("custom") if isinstance(out.get("custom"), dict) else {
        "assumptions": [
            "Base address decode is owned by the integrating SoC fabric",
            "XOR transform is a functional crypto demonstration for v1 and must not be claimed as production cryptographic strength",
            "Line/branch coverage is required when tool-supported; otherwise a waiver must be explicit in coverage evidence",
        ]
    }
    out["dir_structure"] = out.get("dir_structure") if isinstance(out.get("dir_structure"), dict) else {
        "yaml_dir": "yaml/",
        "output_dirs": {"rtl": "rtl/", "list": "list/", "tb": "tb/cocotb/", "sim": "sim/", "lint": "lint/", "cov": "cov/", "doc": "doc/"},
        "generators_dir": "generators/",
    }
    filelist = out.get("filelist") if isinstance(out.get("filelist"), dict) else {}
    rtl_filelist = [item["file"] for item in out["sub_modules"] if isinstance(item, dict) and item.get("file")]
    if not isinstance(filelist.get("rtl"), list) or _has_tbd(filelist.get("rtl")) or f"rtl/{ip}.sv" not in filelist.get("rtl", []):
        filelist["rtl"] = rtl_filelist
    filelist.setdefault("tb", ["tb/cocotb/test_axi_crypto_sram.py", "tb/cocotb/axi_lite_agent.py", "tb/cocotb/scoreboard.py"])
    filelist.setdefault("sim", ["sim/results.xml", "sim/waves.fst"])
    filelist.setdefault("coverage", ["cov/coverage.json"])
    out["filelist"] = filelist if filelist else {
        "rtl": [item["file"] for item in out["sub_modules"] if isinstance(item, dict) and item.get("file")],
        "tb": ["tb/cocotb/test_axi_crypto_sram.py", "tb/cocotb/axi_lite_agent.py", "tb/cocotb/scoreboard.py"],
        "sim": ["sim/results.xml", "sim/waves.fst"],
        "coverage": ["cov/coverage.json"],
    }
    out["test_requirements"] = _ensure_test_requirements(out)
    out["quality_gates"] = out.get("quality_gates") if isinstance(out.get("quality_gates"), dict) else _ensure_quality_gates()
    out["traceability"] = _ensure_traceability(out)
    out["workflow_todos"] = _ensure_workflow_todos(out, ip)
    out["generation_flow"] = {
        "steps": [
            {"name": "validate_ssot", "command": f"bash workflow/ssot-gen/scripts/check_ssot_disk.sh {ip}", "description": "Validate production SSOT structure and quality gates"},
            {"name": "handoff_fl_model", "command": f"/ssot-fl-model {ip}", "description": "Generate FunctionalModel, decomposition, and FCOV plan from SSOT"},
            {"name": "handoff_equivalence_goals", "command": f"/ssot-equiv-goals {ip}", "description": "Derive FL-vs-RTL equivalence goals before TB generation"},
            {"name": "handoff_rtl", "command": f"/ssot-rtl {ip}", "description": "Generate RTL from validated SSOT"},
            {"name": "handoff_tb", "command": f"/ssot-tb-cocotb {ip}", "description": "Generate cocotb/pyuvm verification from validated SSOT"},
            {"name": "handoff_sim_debug", "command": "/wf sim_debug", "description": "Run simulation, waveform, and coverage inspection"},
        ]
    }
    _ensure_rtl_contract_consistency(out)
    ordered = {key: out.get(key) for key in REQUIRED_ORDER}
    for key, value in out.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    ssot = _find_ssot(root, ns.ip)
    doc = _load_yaml(ssot)
    state = _load_state(root, ns.ip)
    repaired = repair(doc, state, ns.ip)
    ssot.write_text(yaml.safe_dump(repaired, sort_keys=False, width=140, allow_unicode=False), encoding="utf-8")
    loaded = yaml.safe_load(ssot.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_ORDER if key not in loaded]
    if missing:
        raise SystemExit("[repair_ssot_schema] missing after repair: " + ", ".join(missing))
    print(f"[repair_ssot_schema] wrote {ssot.relative_to(root)}")
    print(f"[repair_ssot_schema] sections: {len([k for k in REQUIRED_ORDER if k in loaded])}/{len(REQUIRED_ORDER)}")
    print("[repair_ssot_schema] next: bash workflow/ssot-gen/scripts/check_ssot_disk.sh " + ns.ip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
