#!/usr/bin/env python3
# noqa: SIZE_OK - single-purpose external RTL DB generator script.
"""Generate an LLM knowledge-graph wiki for the Andes peripheral RTL database.

The Andes drop (`~/Desktop/andes`) is a corpus of real, silicon-proven IP cores
(UART, SPI, I2C, GPIO, timers, DMA, AHB bus matrix, bridges) plus the AE210P SoC
platform. This script turns it into a wiki that ATLAS can consult as its external
"previous-project RTL DB" via `ATLAS_RTL_DB_WIKI` and `wiki_query(ip="rtl-db")`.

For each top-level block with an `hdl/` directory it parses module declarations,
the top module's port list (classified into APB / AHB / SPI / I2C / DMA / interrupt
groups), counts RTL, and matches AndeShape datasheets/release-notes PDFs. It then
wires a cross-link topology — APB peripherals → the APB bridge/decoder, AHB blocks →
the bus matrix, DMA-capable blocks → the DMA controller, plus an AE210P platform hub
— so the canonical `workflow/wiki/build_graph.py` produces a connected graph (real
`outgoing`/`incoming` edges) rather than a flat list.

Pages are emitted with YAML frontmatter (`id/title/type/tags/related/updated`) and
inline `[[wiki-link]]`s, matching the format `build_graph.py` consumes.

Usage:
    python3 scripts/build_andes_rtl_db_wiki.py                 # ~/Desktop/andes
    python3 scripts/build_andes_rtl_db_wiki.py --andes-root <dir> [--build-graph]

Then point ATLAS at it:
    export ATLAS_RTL_DB_WIKI=<andes>/wiki        # or set in .env / .config
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterator
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, cast

JsonObject = dict[str, Any]
FactMap = dict[str, Any]
BlockMap = dict[str, Any]

# ── Bus / signal classification by port name ───────────────────────────────
BUS_SIGNALS = {
    "APB": ("psel", "penable", "paddr", "pwrite", "pwdata", "prdata", "pready", "pslverr", "pprot", "pstrb"),
    "AHB": ("haddr", "htrans", "hwrite", "hwdata", "hrdata", "hready", "hresp", "hsel",
            "hburst", "hsize", "hprot", "hmastlock", "hgrant", "hbusreq", "hlock", "hreadyout"),
    "SPI": ("spi_", "sclk", "mosi", "miso", "_clk_o", "_cs_n", "ss_n", "spiclk", "dq"),
    "I2C": ("scl", "sda"),
}
DMA_SIGNALS = ("dma_req", "dma_ack", "dma_rx_req", "dma_tx_req", "dma_rx_ack", "dma_tx_ack",
               "dma_tc", "dma_ten", "tdmaack", "rdmaack")
IRQ_SIGNALS = ("intr", "_int", "irq", "interrupt")

# ── Curated per-block role + category (RTL alone can't express SoC intent) ──
# Keeps summaries useful for an LLM and drives the cross-link topology.
ROLES = {
    "atcbmc200":     ("interconnect", "AHB bus matrix / multi-layer interconnect — the fabric that connects masters (CPU, DMA) to slaves (memory, bridges)."),
    "atcapbbrg100":  ("bridge",       "AHB-to-APB bridge — adapts the AHB system bus down to the low-power APB peripheral bus."),
    "atcapbdec100":  ("bridge",       "APB decoder — address-decodes the APB bus and selects among the attached APB peripherals."),
    "atceilmbrg100": ("bridge",       "External Instruction Local-Memory (EILM) bridge — connects the I-LM port to the system bus."),
    "atcexlmbrg100": ("bridge",       "External Data Local-Memory (EXLM) bridge — connects the D-LM port to the system bus."),
    "atcahb2spi200": ("bridge",       "AHB-to-SPI bridge — exposes SPI flash as memory-mapped AHB reads (XIP-style boot/code fetch)."),
    "atcdmac100":    ("dma",          "DMA controller — multi-channel AHB master that offloads memory/peripheral transfers from the CPU."),
    "atcuart100":    ("comm",         "16550-style UART — serial console / data link with FIFOs, modem control, and optional DMA."),
    "atciic100":     ("comm",         "I2C controller — two-wire master/slave serial interface with FIFO and optional DMA."),
    "atcspi200":     ("comm",         "SPI controller — full-duplex serial master/slave with FIFO, local-memory path, and DMA."),
    "atcgpio100":    ("gpio",         "General-purpose I/O — programmable input/output pins with edge/level interrupt support."),
    "atcpit100":     ("timer",        "Programmable interval timer (PIT) — multi-channel timers/counters with interrupts."),
    "atcwdt200":     ("timer",        "Watchdog timer — resets/interrupts the system if not serviced within a window."),
    "atcrtc100":     ("timer",        "Real-time clock — calendar/alarm timekeeping with periodic interrupts."),
}
CATEGORY_TITLES = [
    ("interconnect", "Interconnect"),
    ("bridge", "Bridges & decoders"),
    ("dma", "DMA"),
    ("comm", "Communication peripherals"),
    ("gpio", "GPIO"),
    ("timer", "Timers & RTC"),
    ("other", "Other"),
]

MODULE_RE = re.compile(r"^\s*module\s+([A-Za-z_]\w*)", re.MULTILINE)
PARAM_RE = re.compile(
    r"\b(?P<kind>localparam|parameter)\b\s+"
    r"(?:(?:logic|reg|wire|bit|integer|signed|unsigned)\s+)*"
    r"(?:\[[^\]]+\]\s*)?"
    r"(?P<name>[A-Za-z_]\w*)"
    r"(?:\s*=\s*(?P<value>[^,;\n)]+))?",
    re.MULTILINE,
)
ANSIPORT_RE = re.compile(
    r"\b(?P<dir>input|output|inout)\b\s+"
    r"(?:(?:wire|reg|logic|bit|signed|unsigned)\s+)*"
    r"(?P<width>\[[^\]]+\]\s*)?"
    r"(?P<name>[A-Za-z_]\w*)",
    re.MULTILINE,
)
# old-style declaration: `input [31:0] paddr;` / `output reg foo;`
PORTDECL_RE = re.compile(
    r"^\s*(input|output|inout)\s+(?:(?:wire|reg|logic|bit|signed|unsigned)\s+)?(\[[^\]]*\]\s*)?([A-Za-z_]\w*)\s*;",
    re.MULTILINE,
)
DECL_RE = re.compile(
    r"^\s*(?:reg|logic)\s+(?P<packed>\[[^\]]+\]\s*)?(?P<decls>[^;]+);",
    re.MULTILINE,
)
ASSIGN_RE = re.compile(
    r"(?P<lhs>[A-Za-z_]\w*(?:\s*\[[^\]]+\])?)\s*(?P<op><=|=)\s*(?P<rhs>[^;]+);",
    re.MULTILINE,
)
CASE_RE = re.compile(r"\bcase\s*\((?P<expr>[^)]+)\)(?P<body>.*?)\bendcase\b", re.DOTALL)
DOC_EXTS = {".md", ".txt", ".pdf", ".rst", ".html", ".doc", ".docx"}


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def discover_ips(andes: Path) -> list[str]:
    out: list[str] = []
    for child in sorted(andes.iterdir()):
        if child.is_dir() and (child / "hdl").is_dir() and not child.name.startswith("."):
            out.append(child.name)
    return out


def slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "document"


def _walk_json(node: Any) -> Iterator[JsonObject]:
    if isinstance(node, dict):
        obj = cast(JsonObject, node)
        yield obj
        for value in obj.values():
            yield from _walk_json(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_json(value)


def _text_from_json(node: Any) -> str:
    parts: list[str] = []
    for item in _walk_json(node):
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return " ".join(parts)


def _empty_extracted_facts() -> FactMap:
    return {
        "modules": [],
        "parameters": [],
        "ports": [],
        "clocks": [],
        "resets": [],
        "registers": [],
        "memories": [],
        "fsm_candidates": [],
        "datapaths": [],
        "assignments": [],
    }


def _expr_text(node: Any) -> str:
    text = _text_from_json(node)
    text = re.sub(r"\s*([\[\]\(\),:;])\s*", r"\1", text)
    text = re.sub(r"\s*'\s*", "'", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\d+)'([A-Za-z])\s+([0-9A-Fa-f_xXzZ?]+)", r"\1'\2\3", text)
    return text.strip()


def _identifier_name(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    if node.get("kind") == "Identifier":
        text = node.get("text")
        return text if isinstance(text, str) else ""
    for key in ("name", "identifier"):
        value = node.get(key)
        if isinstance(value, dict):
            name = _identifier_name(value)
            if name:
                return name
    return ""


def _direction_text(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    direction = node.get("direction")
    if not isinstance(direction, dict):
        return ""
    text = direction.get("text")
    if isinstance(text, str) and text:
        return text
    return {
        "InputKeyword": "input",
        "OutputKeyword": "output",
        "InOutKeyword": "inout",
    }.get(str(direction.get("kind")), "")


def _type_width(header: Any) -> str:
    if not isinstance(header, dict):
        return "1"
    data_type = header.get("dataType") or header.get("type")
    if not isinstance(data_type, dict):
        return "1"
    dimensions = data_type.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        return "1"
    width = "".join(_expr_text(dimension) for dimension in dimensions if isinstance(dimension, dict))
    return width or "1"


def _extract_ast_module(item: JsonObject, facts: FactMap) -> None:
    header = item.get("header")
    if not isinstance(header, dict):
        return
    name = _identifier_name(header.get("name"))
    _merge_name(facts["modules"], name)


def _extract_ast_parameter(item: JsonObject, facts: FactMap) -> None:
    keyword = item.get("keyword")
    local = isinstance(keyword, dict) and keyword.get("kind") == "LocalParamKeyword"
    declarators = item.get("declarators")
    if not isinstance(declarators, list):
        return
    for declarator in declarators:
        if not isinstance(declarator, dict) or declarator.get("kind") != "Declarator":
            continue
        name = _identifier_name(declarator.get("name"))
        if not name:
            continue
        parameter: JsonObject = {"name": name, "local": local}
        initializer = declarator.get("initializer")
        if isinstance(initializer, dict):
            value = _expr_text(initializer.get("expr"))
            if value:
                parameter["value"] = value
        _append_unique_named(facts["parameters"], parameter)


def _extract_ast_port(item: JsonObject, facts: FactMap) -> None:
    header = item.get("header")
    if not isinstance(header, dict):
        return
    direction = _direction_text(header)
    width = _type_width(header)
    declarators = item.get("declarators")
    if not isinstance(declarators, list):
        declarator = item.get("declarator")
        declarators = [declarator] if isinstance(declarator, dict) else []
    for declarator in declarators:
        if not isinstance(declarator, dict) or declarator.get("kind") != "Declarator":
            continue
        name = _identifier_name(declarator.get("name"))
        if not name or not direction:
            continue
        _append_unique_named(facts["ports"], {"name": name, "direction": direction, "width": width})


def _extract_ast_data_declaration(item: JsonObject, facts: FactMap) -> None:
    declarators = item.get("declarators")
    if not isinstance(declarators, list):
        return
    for declarator in declarators:
        if not isinstance(declarator, dict) or declarator.get("kind") != "Declarator":
            continue
        name = _identifier_name(declarator.get("name"))
        if not name:
            continue
        _merge_name(facts["registers"], name)
        dimensions = declarator.get("dimensions")
        has_unpacked_dimensions = isinstance(dimensions, list) and bool(dimensions)
        if has_unpacked_dimensions or any(token in name.lower() for token in ("mem", "ram", "fifo")):
            _merge_name(facts["memories"], name)


def _base_signal_name(node: Any) -> str:
    name = _identifier_name(node)
    if name:
        return name
    text = _expr_text(node)
    match = re.match(r"([A-Za-z_]\w*)", text)
    return match.group(1) if match else ""


def _assignment_entry(item: JsonObject) -> JsonObject | None:
    left = item.get("left")
    right = item.get("right")
    left_text = _expr_text(left)
    right_text = _expr_text(right)
    if not left_text:
        return None
    operator = item.get("operatorToken")
    op = _expr_text(operator) if isinstance(operator, dict) else ""
    return {"left": left_text, "op": op or "=", "right": right_text}


def _extract_ast_case(item: JsonObject, facts: FactMap) -> None:
    state = _expr_text(item.get("expr"))
    states: list[str] = []
    items = item.get("items")
    if isinstance(items, list):
        for case_item in items:
            if not isinstance(case_item, dict):
                continue
            if case_item.get("kind") == "DefaultCaseItem":
                _merge_name(states, "default")
            expressions = case_item.get("expressions")
            if not isinstance(expressions, list):
                continue
            for expression in expressions:
                label = _expr_text(expression)
                _merge_name(states, label)
    if state or states:
        _append_unique(
            facts["fsm_candidates"],
            {
                "kind": "case",
                "state": state,
                "states": states,
                "text": f"case ({state})" if state else "case",
            },
        )


def _extract_ast_facts(ast: Any) -> tuple[FactMap, Counter[str]]:
    facts = _empty_extracted_facts()
    counts: Counter[str] = Counter()
    for item in _walk_json(ast):
        kind = item.get("kind")
        if not isinstance(kind, str):
            continue
        counts[kind] += 1
        if kind == "ModuleDeclaration":
            _extract_ast_module(item, facts)
        elif kind == "ParameterDeclaration":
            _extract_ast_parameter(item, facts)
        elif kind in ("ImplicitAnsiPort", "PortDeclaration"):
            _extract_ast_port(item, facts)
        elif kind == "DataDeclaration":
            _extract_ast_data_declaration(item, facts)
        elif kind == "NonblockingAssignmentExpression":
            entry = _assignment_entry(item)
            if entry is not None:
                _append_unique(facts["assignments"], entry)
                _merge_name(facts["registers"], _base_signal_name(item.get("left")))
        elif kind == "AssignmentExpression":
            entry = _assignment_entry(item)
            if entry is not None:
                _append_unique(facts["datapaths"], entry)
                _append_unique(facts["assignments"], entry)
        elif kind == "CaseStatement":
            _extract_ast_case(item, facts)
    port_names = [str(port["name"]) for port in facts["ports"]]
    facts["clocks"] = list(dict.fromkeys(name for name in port_names if any(token in name.lower() for token in ("clk", "clock"))))
    facts["resets"] = list(dict.fromkeys(name for name in port_names if any(token in name.lower() for token in ("rst", "reset"))))
    return facts, counts


def _ast_facts(path: Path) -> tuple[FactMap, Counter[str], list[str]]:
    diagnostics: list[str] = []
    try:
        import pyslang
    except ImportError:
        return _empty_extracted_facts(), Counter[str](), [f"{path.name}: pyslang unavailable; used regex fallback"]

    try:
        tree = pyslang.SyntaxTree.fromFile(str(path))
        raw = tree.root.to_json()
        ast = json.loads(raw) if isinstance(raw, str) else raw
        extracted, counts = _extract_ast_facts(ast)
        for diag in tree.diagnostics:
            code = getattr(diag, "code", "diagnostic")
            loc = getattr(diag, "location", "")
            args = getattr(diag, "args", [])
            diagnostics.append(f"{path.name}: {code} at {loc} args={list(args)}")
    except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        diagnostics.append(f"{path.name}: pyslang parse failed: {type(exc).__name__}: {exc}")
        return _empty_extracted_facts(), Counter[str](), diagnostics
    return extracted, counts, diagnostics


def _append_unique(items: list[Any], value: Any) -> None:
    if value not in items:
        items.append(value)


def _append_unique_named(items: list[JsonObject], value: JsonObject) -> None:
    name = value.get("name")
    if isinstance(name, str) and any(isinstance(item, dict) and item.get("name") == name for item in items):
        return
    _append_unique(items, value)


def _merge_name(items: list[str], name: str) -> None:
    if name and name not in items:
        items.append(name)


def _port_width(width: str) -> str:
    return width.strip() if width and width.strip() else "1"


def _declared_names(decls: str) -> list[tuple[str, bool]]:
    names: list[tuple[str, bool]] = []
    for raw in decls.split(","):
        item = raw.strip()
        if not item:
            continue
        item = item.split("=", 1)[0].strip()
        match = re.match(r"(?P<name>[A-Za-z_]\w*)\s*(?P<dims>(?:\[[^\]]+\]\s*)*)$", item)
        if not match:
            continue
        dims = match.group("dims") or ""
        names.append((match.group("name"), bool(dims.strip())))
    return names


def _extract_regex_facts(text: str) -> FactMap:
    modules: list[str] = []
    parameters: list[JsonObject] = []
    ports: list[JsonObject] = []
    registers: list[str] = []
    memories: list[str] = []
    assignments: list[JsonObject] = []
    fsm_candidates: list[JsonObject] = []

    for match in MODULE_RE.finditer(text):
        _merge_name(modules, match.group(1))
    for match in PARAM_RE.finditer(text):
        item: JsonObject = {"name": match.group("name"), "local": match.group("kind") == "localparam"}
        value = (match.group("value") or "").strip()
        if value:
            item["value"] = value
        _append_unique(parameters, item)
    for match in ANSIPORT_RE.finditer(text):
        _append_unique(
            ports,
            {
                "name": match.group("name"),
                "direction": match.group("dir"),
                "width": _port_width(match.group("width") or ""),
            },
        )
    for match in PORTDECL_RE.finditer(text):
        _append_unique(
            ports,
            {
                "name": match.group(3),
                "direction": match.group(1),
                "width": _port_width(match.group(2) or ""),
            },
        )
    for match in DECL_RE.finditer(text):
        for name, has_unpacked in _declared_names(match.group("decls")):
            _merge_name(registers, name)
            if has_unpacked or any(token in name.lower() for token in ("mem", "ram", "fifo")):
                _merge_name(memories, name)
    for match in ASSIGN_RE.finditer(text):
        lhs = re.sub(r"\s+", "", match.group("lhs"))
        rhs = match.group("rhs").strip()
        base_lhs = lhs.split("[", 1)[0]
        _append_unique(assignments, {"left": lhs, "op": match.group("op"), "right": rhs})
        if match.group("op") == "<=":
            _merge_name(registers, base_lhs)
    for match in CASE_RE.finditer(text):
        body = match.group("body")
        labels = re.findall(r"^\s*([A-Za-z_]\w*)\s*:", body, flags=re.MULTILINE)
        fsm_candidates.append(
            {
                "kind": "case",
                "state": match.group("expr").strip(),
                "states": list(dict.fromkeys(labels)),
                "text": f"case ({match.group('expr').strip()})",
            }
        )

    port_names = [str(port["name"]) for port in ports]
    clocks = [name for name in port_names if any(token in name.lower() for token in ("clk", "clock"))]
    resets = [name for name in port_names if any(token in name.lower() for token in ("rst", "reset"))]
    return {
        "modules": modules,
        "parameters": parameters,
        "ports": ports,
        "clocks": list(dict.fromkeys(clocks)),
        "resets": list(dict.fromkeys(resets)),
        "registers": registers,
        "memories": memories,
        "fsm_candidates": fsm_candidates,
        "datapaths": assignments,
        "assignments": assignments,
    }


def _merge_extracted_facts(target: FactMap, extracted: FactMap, *, fallback: bool = False) -> None:
    for key in ("modules", "clocks", "resets", "registers", "memories"):
        target_names = cast(list[str], target[key])
        for value in cast(list[str], extracted[key]):
            _merge_name(target_names, value)
    for key in ("parameters", "ports"):
        target_items = cast(list[JsonObject], target[key])
        for value in cast(list[JsonObject], extracted[key]):
            _append_unique_named(target_items, value)
    for key in ("fsm_candidates", "datapaths", "assignments"):
        if fallback and target[key]:
            continue
        target_items = cast(list[Any], target[key])
        for value in cast(list[Any], extracted[key]):
            _append_unique(target_items, value)


def build_rtl_facts(andes: Path, name: str, rtl_files: list[Path]) -> FactMap:
    facts: FactMap = {
        "schema_version": "andes_rtl_facts.v1",
        "block": name,
        "modules": [],
        "parameters": [],
        "ports": [],
        "clocks": [],
        "resets": [],
        "registers": [],
        "memories": [],
        "fsm_candidates": [],
        "datapaths": [],
        "assignments": [],
        "diagnostics": [],
        "source_files": [path.relative_to(andes).as_posix() for path in rtl_files],
        "ast_extracted_files": [],
        "features": [],
        "ast_kind_counts": {},
    }
    kind_counts: Counter[str] = Counter()
    diagnostics = cast(list[str], facts["diagnostics"])
    ast_extracted_files = cast(list[str], facts["ast_extracted_files"])
    if not rtl_files:
        diagnostics.append(f"{name}: no .v/.sv RTL files found under hdl/")
    for path in rtl_files:
        text = _read(path)
        ast_extracted, counts, path_diagnostics = _ast_facts(path)
        kind_counts.update(counts)
        diagnostics.extend(path_diagnostics)
        if counts:
            ast_extracted_files.append(path.relative_to(andes).as_posix())
        _merge_extracted_facts(facts, ast_extracted)
        _merge_extracted_facts(facts, _extract_regex_facts(text), fallback=True)
    features: list[str] = []
    if facts["fsm_candidates"]:
        features.append("fsm")
    if facts["registers"]:
        features.append("register")
    if facts["memories"]:
        features.append("memory")
    if facts["clocks"]:
        features.append("clock")
    if facts["resets"]:
        features.append("reset")
    if facts["datapaths"]:
        features.append("datapath")
    facts["features"] = features
    facts["ast_kind_counts"] = dict(sorted(kind_counts.items()))
    return facts


def discover_docs(andes: Path, name: str) -> list[JsonObject]:
    docs: list[JsonObject] = []
    seen: set[str] = set()
    ip_root = andes / name
    candidates = [path for path in ip_root.rglob("*") if path.is_file() and path.suffix.lower() in DOC_EXTS]
    up = name.upper()
    candidates += [path for path in andes.rglob(f"*{up}*") if path.is_file() and path.suffix.lower() in DOC_EXTS]
    for path in sorted(candidates):
        rel = path.relative_to(andes).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        docs.append({"path": rel, "title": path.stem.replace("_", " "), "slug": slugify(path.stem)})
    return docs


def parse_block(andes: Path, name: str) -> BlockMap:
    hdl = andes / name / "hdl"
    v_files = sorted(hdl.rglob("*.v")) + sorted(hdl.rglob("*.sv"))
    vh_files = sorted(hdl.rglob("*.vh")) + sorted(hdl.rglob("*.svh"))
    modules: list[str] = []
    total_lines = 0
    for f in v_files:
        text = _read(f)
        total_lines += text.count("\n") + 1
        for m in MODULE_RE.finditer(text):
            if m.group(1) not in modules:
                modules.append(m.group(1))

    top = name if name in modules else (modules[0] if modules else name)
    top_file = hdl / f"{top}.v"
    if not top_file.is_file():
        top_file = hdl / f"{top}.sv"
    if not top_file.is_file():
        # fall back to whichever file declares `module <top>`
        for f in v_files:
            if re.search(rf"^\s*module\s+{re.escape(top)}\b", _read(f), re.MULTILINE):
                top_file = f
                break

    # Top-module ports (old-style input/output/inout declarations in the top file).
    ports: list[tuple[str, str, str]] = []  # (dir, width, signal)
    top_text = _read(top_file)
    for m in ANSIPORT_RE.finditer(top_text):
        direction, width, sig = m.group("dir"), (m.group("width") or "").strip(), m.group("name")
        if (direction, width, sig) not in ports:
            ports.append((direction, width, sig))
    for m in PORTDECL_RE.finditer(top_text):
        direction, width, sig = m.group(1), (m.group(2) or "").strip(), m.group(3)
        if (direction, width, sig) not in ports:
            ports.append((direction, width, sig))

    names = [p[2].lower() for p in ports]
    buses: list[str] = []
    for bus, sigs in BUS_SIGNALS.items():
        if any(any(s in n for s in sigs) for n in names):
            buses.append(bus)
    has_dma = any(any(s in n for s in DMA_SIGNALS) for n in names)
    has_irq = any(any(n.endswith(s) or s in n for s in IRQ_SIGNALS) for n in names)

    docs_meta = discover_docs(andes, name)
    docs = [doc["path"] for doc in docs_meta]

    category, role = ROLES.get(name, ("other", f"Andes `{name}` RTL block."))

    # Tags: category + buses + features.
    tags = ["rtl-db", "andes", category]
    tags += [b.lower() for b in buses]
    if has_dma:
        tags.append("dma")
    if has_irq:
        tags.append("interrupt")
    if any("fifo" in mod.lower() for mod in modules):
        tags.append("fifo")
    tags = list(dict.fromkeys(tags))

    return {
        "name": name, "top": top, "category": category, "role": role,
        "modules": modules, "ports": ports, "buses": buses,
        "has_dma": has_dma, "has_irq": has_irq,
        "lines": total_lines,
        "rtl_files": [f.relative_to(andes).as_posix() for f in v_files],
        "inc_files": [f.relative_to(andes).as_posix() for f in vh_files],
        "docs": docs, "doc_pages": docs_meta, "tags": tags,
        "rtl_facts": build_rtl_facts(andes, name, v_files),
    }


PLATFORM_ID = "ae210p"


def related_for(b: BlockMap, all_names: set[str]) -> list[str]:
    """Cross-link topology, derived from bus tags + curated roles."""
    rel: list[str] = []

    def add(x: str) -> None:
        if x in all_names and x != b["name"] and x not in rel:
            rel.append(x)

    if "APB" in b["buses"] and b["category"] not in ("bridge",):
        add("atcapbbrg100")
        add("atcapbdec100")
    if "AHB" in b["buses"]:
        add("atcbmc200")
    if b["has_dma"] and b["category"] != "dma":
        add("atcdmac100")
    if b["name"] == "atcahb2spi200":
        add("atcspi200")
    if b["name"] == "atcspi200":
        add("atcahb2spi200")
    if b["name"] in ("atceilmbrg100", "atcexlmbrg100"):
        add("atceilmbrg100")
        add("atcexlmbrg100")
        add("atcbmc200")
    if b["name"] == "atcbmc200":
        # the matrix points back at the principal masters/bridges
        for x in ("atcdmac100", "atcapbbrg100", "atceilmbrg100", "atcexlmbrg100", "atcahb2spi200"):
            add(x)
    # everything sits on the AE210P platform + the inventory
    rel = [PLATFORM_ID, "rtl-inventory"] + rel
    return rel


def fence(rows: list[str]) -> str:
    return "\n".join(rows)


def write_block_page(wiki: Path, b: BlockMap, all_names: set[str], today: str) -> None:
    rel = related_for(b, all_names)
    tags = ", ".join(b["tags"])
    related_fm = ", ".join(rel)
    iface = " + ".join(b["buses"]) if b["buses"] else "internal / custom"
    feats: list[str] = []
    if b["has_dma"]:
        feats.append("DMA handshake")
    if b["has_irq"]:
        feats.append("interrupt")
    feat_str = (", ".join(feats)) if feats else "—"

    # group ports by bus for a compact interface table
    def grp(sig: str) -> str:
        s = sig.lower()
        for bus, sigs in BUS_SIGNALS.items():
            if any(x in s for x in sigs):
                return bus
        if any(x in s for x in DMA_SIGNALS):
            return "DMA"
        if any(s.endswith(x) or x in s for x in IRQ_SIGNALS):
            return "IRQ"
        if any(x in s for x in ("clk", "rst", "reset", "resetn", "clock")):
            return "clk/rst"
        return "other"

    port_rows = ["| Group | Dir | Width | Signal |", "| --- | --- | --- | --- |"]
    for direction, width, sig in b["ports"]:
        port_rows.append(f"| {grp(sig)} | {direction} | {width or '1'} | `{sig}` |")
    port_table = "\n".join(port_rows) if b["ports"] else "_No top-level port declarations parsed._"

    submods = [m for m in b["modules"] if m != b["top"]]
    submod_lines = "\n".join(f"- `{m}`" for m in submods) or "_(single-module block)_"
    rtl_lines = "\n".join(f"- `{f}`" for f in (b["rtl_files"] + b["inc_files"]))
    doc_lines = "\n".join(f"- [[doc-{b['name']}-{d['slug']}]] — `{d['path']}`" for d in b["doc_pages"]) or "_No matching local document found._"
    related_links = " · ".join(f"[[{r}]]" for r in rel)
    facts = cast(FactMap, b["rtl_facts"])
    fact_path = f"_rtl_facts/{b['name']}.json"
    fact_terms = " ".join(facts["features"]) or "module port parameter"
    ast_summary = (
        f"AST RTL facts for module/port/parameter/fsm/datapath/register/memory/clock/reset queries: "
        f"{fact_terms}; clocks {', '.join(facts['clocks']) or '-'}; resets {', '.join(facts['resets']) or '-'}; "
        f"registers {', '.join(facts['registers'][:8]) or '-'}; memories {', '.join(facts['memories'][:8]) or '-'}."
    )

    body = f"""---
id: {b['name']}
title: {b['name']} RTL reference
type: reference
tags: [{tags}]
related: [{related_fm}]
updated: {today}
---
# {b['name']} — {b['category']} block

{b['role']} {ast_summary}

Part of the [[{PLATFORM_ID}]] platform; indexed in [[rtl-inventory]]. External Andes
RTL reference — read-only design knowledge for reuse and RTL generation.

## At a glance

- **Top module:** `{b['top']}`
- **Bus interface:** {iface}
- **Features:** {feat_str}
- **Modules:** {len(b['modules'])}  ·  **RTL/include files:** {len(b['rtl_files']) + len(b['inc_files'])}  ·  **RTL lines:** {b['lines']}
- **HDL root:** `{b['name']}/hdl`

## Top-level interface

{port_table}

## Submodules

{submod_lines}

## RTL & include files

{rtl_lines}

## Datasheets / release notes

{doc_lines}

## AST RTL facts

Detailed pyslang-backed RTL facts are stored in `{fact_path}`. Search terms: module port parameter fsm datapath register memory clock reset clk rst.

## Related blocks

{related_links}

## Query

```sh
wiki_query(ip="rtl-db", topic="{b['name']} {' '.join(b['buses']).lower()}", depth=3)
```
"""
    (wiki / f"{b['name']}.md").write_text(body, encoding="utf-8")


def write_rtl_facts(wiki: Path, blocks: list[BlockMap]) -> None:
    facts_dir = wiki / "_rtl_facts"
    facts_dir.mkdir(parents=True, exist_ok=True)
    for b in blocks:
        path = facts_dir / f"{b['name']}.json"
        path.write_text(json.dumps(b["rtl_facts"], indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_doc_pages(wiki: Path, blocks: list[BlockMap], today: str) -> None:
    rows: list[str] = []
    seen: set[str] = set()
    for b in blocks:
        for doc in b["doc_pages"]:
            doc_id = f"doc-{b['name']}-{doc['slug']}"
            if doc_id in seen:
                continue
            seen.add(doc_id)
            rows.append(f"- [[{doc_id}]] — [[{b['name']}]] `{doc['path']}`")
            body = f"""---
id: {doc_id}
title: {doc['title']}
type: reference
tags: [rtl-db, andes, doc]
related: [{b['name']}, doc-inventory]
updated: {today}
---
# {doc['title']}

Document metadata for [[{b['name']}]] in the external Andes RTL DB. Use this page to find the local datasheet, guide, release note, or spec without embedding source document contents.

- **Owner block:** [[{b['name']}]]
- **Path:** `{doc['path']}`
- **Kind:** `{Path(doc['path']).suffix.lower() or 'document'}`

Related inventory: [[doc-inventory]].
"""
            (wiki / f"{doc_id}.md").write_text(body, encoding="utf-8")

    body = f"""---
id: doc-inventory
title: Andes RTL DB document inventory
type: reference
tags: [rtl-db, andes, doc, inventory]
related: [index, rtl-inventory]
updated: {today}
---
# Andes RTL DB document inventory

Local document pages for Andes RTL DB blocks. These pages record path and ownership metadata only; source document contents are not embedded.

{chr(10).join(rows) if rows else '_No local documents found._'}
"""
    (wiki / "doc-inventory.md").write_text(body, encoding="utf-8")


def write_platform_page(wiki: Path, blocks: list[BlockMap], today: str) -> None:
    names = [b["name"] for b in blocks]
    links = "\n".join(
        f"- [[{b['name']}]] — {b['role']}" for b in blocks
    )
    related_fm = ", ".join(names + ["rtl-inventory"])
    body = f"""---
id: {PLATFORM_ID}
title: AE210P platform (Andes SoC)
type: index
tags: [rtl-db, andes, platform, soc, ae210p]
related: [{related_fm}]
updated: {today}
---
# AE210P — Andes SoC platform

`AE210P` is the Andes reference SoC platform that integrates the peripheral RTL
blocks in this database around an AHB system bus ([[atcbmc200]]) with an AHB-to-APB
bridge ([[atcapbbrg100]]) feeding the low-speed peripherals. Use it as the
integration hub when reusing any block below.

## Integrated blocks

{links}

## Topology (summary)

- **System bus:** [[atcbmc200]] (AHB matrix) ties CPU, [[atcdmac100]] (DMA), and the
  local-memory bridges ([[atceilmbrg100]], [[atcexlmbrg100]]) to memory and slaves.
- **Peripheral bus:** [[atcapbbrg100]] bridges AHB→APB; [[atcapbdec100]] decodes APB to
  [[atcuart100]], [[atciic100]], [[atcgpio100]], [[atcpit100]], [[atcrtc100]], [[atcwdt200]].
- **Storage/serial:** [[atcspi200]] / [[atcahb2spi200]] provide SPI + memory-mapped SPI flash.

See [[rtl-inventory]] for the machine-generated block table.
"""
    (wiki / f"{PLATFORM_ID}.md").write_text(body, encoding="utf-8")


def write_index(wiki: Path, blocks: list[BlockMap], andes: Path, today: str) -> None:
    by_cat: dict[str, list[BlockMap]] = {}
    for b in blocks:
        by_cat.setdefault(b["category"], []).append(b)
    sections = []
    for cat, title in CATEGORY_TITLES:
        items = by_cat.get(cat)
        if not items:
            continue
        rows = "\n".join(
            f"- [[{b['name']}]] — top `{b['top']}`, "
            f"{'+'.join(b['buses']) or 'internal'} bus, "
            f"{len(b['modules'])} modules, {b['lines']} lines"
            for b in items
        )
        sections.append(f"### {title}\n\n{rows}")
    grouped = "\n\n".join(sections)
    body = f"""---
id: index
title: Andes Peripheral RTL DB
type: index
tags: [rtl-db, andes, peripheral, external, soc]
related: [{PLATFORM_ID}, rtl-inventory]
updated: {today}
---
# Andes Peripheral RTL DB

Local LLM knowledge-graph wiki generated from `{andes}` by
`scripts/build_andes_rtl_db_wiki.py`. It indexes the Andes peripheral RTL blocks
(module hierarchy, top-level bus interface, RTL paths, datasheets) and cross-links
them through the [[{PLATFORM_ID}]] platform so ATLAS can reuse proven designs.

Point ATLAS at this wiki as the external **previous-project RTL DB**:

```sh
export ATLAS_RTL_DB_WIKI={andes}/wiki        # or set in .env / .config
```

Then query it from ATLAS:

```sh
wiki_query(ip="rtl-db", topic="uart apb dma", depth=3)
wiki_query(ip="andes",  topic="atcspi200",    depth=3)
```

## Platform

- [[{PLATFORM_ID}]] — AE210P SoC integration hub

## Blocks by category

{grouped}

See also: [[rtl-inventory]] (full table).
"""
    (wiki / "index.md").write_text(body, encoding="utf-8")


def write_inventory(wiki: Path, blocks: list[BlockMap], andes: Path, today: str) -> None:
    rows = [
        "| Block | Category | Top module | Bus | Modules | Files | Lines | Tags | Docs |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for b in blocks:
        rows.append(
            f"| [[{b['name']}]] | {b['category']} | `{b['top']}` | "
            f"{'+'.join(b['buses']) or '-'} | {len(b['modules'])} | "
            f"{len(b['rtl_files']) + len(b['inc_files'])} | {b['lines']} | "
            f"{', '.join(b['tags'])} | {len(b['docs'])} |"
        )
    table = "\n".join(rows)
    body = f"""---
id: rtl-inventory
title: Andes RTL Inventory
type: reference
tags: [rtl-db, andes, inventory]
related: [index, {PLATFORM_ID}]
updated: {today}
---
# Andes RTL Inventory

Machine-generated inventory of Andes peripheral RTL blocks under `{andes}`.
Regenerate with `scripts/build_andes_rtl_db_wiki.py`. Index: [[index]] · Platform: [[{PLATFORM_ID}]].

{table}
"""
    (wiki / "rtl-inventory.md").write_text(body, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--andes-root", default=None,
                    help="Path to the Andes RTL corpus (default ~/Desktop/andes).")
    ap.add_argument("--wiki", default=None,
                    help="Wiki output directory; source root defaults to its parent when --andes-root is omitted.")
    ap.add_argument("--build-graph", action="store_true",
                    help="Also run workflow/wiki/build_graph.py on the generated wiki.")
    args = ap.parse_args(argv)

    wiki_arg = Path(args.wiki).expanduser().resolve() if args.wiki else None
    if args.andes_root:
        andes = Path(args.andes_root).expanduser().resolve()
    elif wiki_arg is not None:
        andes = wiki_arg.parent
    else:
        andes = (Path.home() / "Desktop" / "andes").resolve()
    if not andes.is_dir():
        print(f"[andes-wiki] not found: {andes}", file=sys.stderr)
        return 2
    wiki = wiki_arg or (andes / "wiki")
    wiki.mkdir(parents=True, exist_ok=True)
    today = time.strftime("%Y-%m-%d")

    names = discover_ips(andes)
    if not names:
        print(f"[andes-wiki] no IP dirs with hdl/ under {andes}", file=sys.stderr)
        return 2
    blocks = [parse_block(andes, n) for n in names]
    all_names = set(names)

    for b in blocks:
        write_block_page(wiki, b, all_names, today)
    write_rtl_facts(wiki, blocks)
    write_doc_pages(wiki, blocks, today)
    write_platform_page(wiki, blocks, today)
    write_index(wiki, blocks, andes, today)
    write_inventory(wiki, blocks, andes, today)

    print(f"[andes-wiki] wrote {len(blocks)} block pages + AST facts + docs + index + rtl-inventory + {PLATFORM_ID} to {wiki}")

    if args.build_graph:
        builder = Path(__file__).resolve().parents[1] / "workflow" / "wiki" / "build_graph.py"
        if builder.is_file():
            subprocess.run(["python3", str(builder), "--wiki", str(wiki)], check=False)
        else:
            print(f"[andes-wiki] build_graph.py not found at {builder}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
