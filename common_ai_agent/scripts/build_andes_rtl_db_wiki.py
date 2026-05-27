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
# old-style declaration: `input [31:0] paddr;` / `output reg foo;`
PORTDECL_RE = re.compile(
    r"^\s*(input|output|inout)\s+(?:wire\s+|reg\s+)?(\[[^\]]*\]\s*)?([A-Za-z_]\w*)\s*;",
    re.MULTILINE,
)


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


def parse_block(andes: Path, name: str) -> dict:
    hdl = andes / name / "hdl"
    v_files = sorted(hdl.rglob("*.v"))
    vh_files = sorted(hdl.rglob("*.vh")) + sorted(hdl.rglob("*.svh"))
    modules: list[str] = []
    total_lines = 0
    for f in v_files:
        text = _read(f)
        total_lines += text.count("\n") + 1
        for m in MODULE_RE.finditer(text):
            if m.group(1) not in modules:
                modules.append(m.group(1))

    # Top module: prefer the file named exactly <name>.v, else a module == name.
    top = name if name in modules else (modules[0] if modules else name)
    top_file = hdl / f"{top}.v"
    if not top_file.is_file():
        # fall back to whichever file declares `module <top>`
        for f in v_files:
            if re.search(rf"^\s*module\s+{re.escape(top)}\b", _read(f), re.MULTILINE):
                top_file = f
                break

    # Top-module ports (old-style input/output/inout declarations in the top file).
    ports: list[tuple[str, str, str]] = []  # (dir, width, signal)
    for m in PORTDECL_RE.finditer(_read(top_file)):
        direction, width, sig = m.group(1), (m.group(2) or "").strip(), m.group(3)
        ports.append((direction, width, sig))

    names = [p[2].lower() for p in ports]
    buses: list[str] = []
    for bus, sigs in BUS_SIGNALS.items():
        if any(any(s in n for s in sigs) for n in names):
            buses.append(bus)
    has_dma = any(any(s in n for s in DMA_SIGNALS) for n in names)
    has_irq = any(any(n.endswith(s) or s in n for s in IRQ_SIGNALS) for n in names)

    # Datasheet / release-note PDFs (under the IP dir and the platform DOCS).
    up = name.upper()
    docs = []
    for pdf in list((andes / name).rglob("*.pdf")) + list(andes.rglob(f"*{up}*.pdf")):
        rel = pdf.relative_to(andes).as_posix()
        if rel not in docs:
            docs.append(rel)
    docs.sort()

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
        "docs": docs, "tags": tags,
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
    doc_lines = "\n".join(f"- `{d}`" for d in b["docs"]) or "_No matching PDF found._"
    related_links = " · ".join(f"[[{r}]]" for r in rel)

    body = f"""---
id: {b['name']}
title: {b['name']} RTL reference
type: reference
tags: [{tags}]
related: [{related_fm}]
updated: {today}
---
# {b['name']} — {b['category']} block

{b['role']}

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

## Related blocks

{related_links}

## Query

```sh
wiki_query(ip="rtl-db", topic="{b['name']} {' '.join(b['buses']).lower()}", depth=3)
```
"""
    (wiki / f"{b['name']}.md").write_text(body, encoding="utf-8")


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
    ap.add_argument("--andes-root", default=str(Path.home() / "Desktop" / "andes"),
                    help="Path to the Andes RTL corpus (default ~/Desktop/andes).")
    ap.add_argument("--build-graph", action="store_true",
                    help="Also run workflow/wiki/build_graph.py on the generated wiki.")
    args = ap.parse_args(argv)

    andes = Path(args.andes_root).expanduser().resolve()
    if not andes.is_dir():
        print(f"[andes-wiki] not found: {andes}", file=sys.stderr)
        return 2
    wiki = andes / "wiki"
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
    write_platform_page(wiki, blocks, today)
    write_index(wiki, blocks, andes, today)
    write_inventory(wiki, blocks, andes, today)

    print(f"[andes-wiki] wrote {len(blocks)} block pages + index + rtl-inventory + {PLATFORM_ID} to {wiki}")

    if args.build_graph:
        builder = Path(__file__).resolve().parents[1] / "workflow" / "wiki" / "build_graph.py"
        if builder.is_file():
            subprocess.run(["python3", str(builder), "--wiki", str(wiki)], check=False)
        else:
            print(f"[andes-wiki] build_graph.py not found at {builder}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
