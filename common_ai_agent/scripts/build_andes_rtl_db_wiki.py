#!/usr/bin/env python3
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
import json
import re
import subprocess
import sys
import time
from pathlib import Path

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
    out = []
    for child in sorted(andes.iterdir()):
        if child.is_dir() and (child / "hdl").is_dir() and not child.name.startswith("."):
            out.append(child.name)
    return out


def slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "document"


def _walk_json(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_json(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_json(value)


def _text_from_json(node) -> str:
    parts: list[str] = []
    for item in _walk_json(node):
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return " ".join(parts)


def _ast_facts(path: Path) -> tuple[Counter, list[str]]:
    diagnostics: list[str] = []
    counts: Counter = Counter()
    try:
        import pyslang  # type: ignore
    except ImportError:
        return counts, [f"{path.name}: pyslang unavailable; used regex fallback"]

    try:
        tree = pyslang.SyntaxTree.fromFile(str(path))
        raw = tree.root.to_json()
        ast = json.loads(raw) if isinstance(raw, str) else raw
        for item in _walk_json(ast):
            kind = item.get("kind")
            if isinstance(kind, str):
                counts[kind] += 1
        for diag in tree.diagnostics:
            code = getattr(diag, "code", "diagnostic")
            loc = getattr(diag, "location", "")
            args = getattr(diag, "args", [])
            diagnostics.append(f"{path.name}: {code} at {loc} args={list(args)}")
    except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        diagnostics.append(f"{path.name}: pyslang parse failed: {type(exc).__name__}: {exc}")
    return counts, diagnostics


def _append_unique(items: list, value) -> None:
    if value not in items:
        items.append(value)


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


def _extract_regex_facts(text: str) -> dict:
    modules: list[str] = []
    parameters: list[dict] = []
    ports: list[dict] = []
    registers: list[str] = []
    memories: list[str] = []
    assignments: list[dict] = []
    fsm_candidates: list[dict] = []

    for match in MODULE_RE.finditer(text):
        _merge_name(modules, match.group(1))
    for match in PARAM_RE.finditer(text):
        item = {"name": match.group("name"), "local": match.group("kind") == "localparam"}
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


def build_rtl_facts(andes: Path, name: str, rtl_files: list[Path]) -> dict:
    facts = {
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
        "features": [],
        "ast_kind_counts": {},
    }
    kind_counts: Counter = Counter()
    if not rtl_files:
        facts["diagnostics"].append(f"{name}: no .v/.sv RTL files found under hdl/")
    for path in rtl_files:
        text = _read(path)
        counts, diagnostics = _ast_facts(path)
        kind_counts.update(counts)
        facts["diagnostics"].extend(diagnostics)
        extracted = _extract_regex_facts(text)
        for key in ("modules", "clocks", "resets", "registers", "memories"):
            for value in extracted[key]:
                _merge_name(facts[key], value)
        for key in ("parameters", "ports", "fsm_candidates", "datapaths", "assignments"):
            for value in extracted[key]:
                _append_unique(facts[key], value)
    features = []
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


def discover_docs(andes: Path, name: str) -> list[dict]:
    docs: list[dict] = []
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


def parse_block(andes: Path, name: str) -> dict:
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


def related_for(b: dict, all_names: set[str]) -> list[str]:
    """Cross-link topology, derived from bus tags + curated roles."""
    rel: list[str] = []

    def add(x):
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


def write_block_page(wiki: Path, b: dict, all_names: set[str], today: str) -> None:
    rel = related_for(b, all_names)
    tags = ", ".join(b["tags"])
    related_fm = ", ".join(rel)
    iface = " + ".join(b["buses"]) if b["buses"] else "internal / custom"
    feats = []
    if b["has_dma"]:
        feats.append("DMA handshake")
    if b["has_irq"]:
        feats.append("interrupt")
    feat_str = (", ".join(feats)) if feats else "—"

    # group ports by bus for a compact interface table
    def grp(sig):
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
    facts = b["rtl_facts"]
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


def write_rtl_facts(wiki: Path, blocks: list[dict]) -> None:
    facts_dir = wiki / "_rtl_facts"
    facts_dir.mkdir(parents=True, exist_ok=True)
    for b in blocks:
        path = facts_dir / f"{b['name']}.json"
        path.write_text(json.dumps(b["rtl_facts"], indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_doc_pages(wiki: Path, blocks: list[dict], today: str) -> None:
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


def write_platform_page(wiki: Path, blocks: list[dict], today: str) -> None:
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


def write_index(wiki: Path, blocks: list[dict], andes: Path, today: str) -> None:
    by_cat: dict[str, list[dict]] = {}
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


def write_inventory(wiki: Path, blocks: list[dict], andes: Path, today: str) -> None:
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
