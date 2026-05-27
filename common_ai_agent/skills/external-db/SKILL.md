---
name: external-db
description: >
  External reference-database expert. Before authoring new RTL — or answering from
  assumed knowledge — consult the configured external DB for proven, authoritative
  references instead of reinventing. The DB is typically a prior-project / vendor RTL
  corpus (e.g. Andes peripherals: UART, SPI, I2C, GPIO, DMA, AHB bus matrix, bridges,
  timers), but it is NOT limited to RTL: it can hold spec excerpts, reference designs,
  datasheets, or any prior-art knowledge wired in by the deployment.
  Trigger on: external db, reference db, reference design, prior art, reuse, existing
  rtl, previous project, knowledge base, and common peripheral/bus families
  (uart, spi, i2c, gpio, dma, apb, ahb, bus matrix, bridge, timer, watchdog, rtc, fifo).
priority: 80
activation:
  keywords: ["external db", "external database", "reference db", "reference design",
             "knowledge base", reuse, "rtl reuse", "prior art", "existing rtl",
             "previous project", "previous-project", "reference rtl", "proven design",
             andes, "ip reuse",
             uart, spi, i2c, iic, gpio, dma, dmac, "bus matrix", apb, ahb,
             bridge, timer, watchdog, wdt, rtc, pit, fifo, "local memory", lmbrg,
             peripheral, "soc integration"]
  file_patterns: ["*.md", "*.yaml", "*.yml", "*.sv", "*.v", "*.txt"]
  auto_detect: true
requires_tools: [wiki_query]
related_skills: [verilog-expert, testbench-expert]
---

# ⚠️ MANDATORY: Check the external DB before reinventing

**Before generating/hand-writing RTL for a peripheral or bus block — or stating a
"reference" design or convention — FIRST query the external reference database for an
existing, proven source. Reuse interface conventions, module decomposition, register
layouts, and cited facts rather than inventing them.**

The external DB is, by design, *external* and **data-source-agnostic** — this skill
does not assume any structure. The deployment wires the source via any one of (newer
`ATLAS_EXTERNAL_DB_*` names are preferred; legacy `ATLAS_RTL_DB_*` still work):

- `…_WIKI` — a wiki directory (markdown + `_graph.json`).
- `…_BUILDER` — an external converter that builds `_graph.json` from a foreign corpus.
- `…_QUERY` — an external executable that owns the *entire* query (its own structure /
  search / transport: files, DB, HTTP, vector store…).

You never need to know which is configured — always go through `wiki_query`.

## How to query

```
wiki_query(ip="external-db", topic="<block / interface / topic>", depth=3)
```
(`ip="rtl-db"` / `"andes"` are accepted aliases for the same source.)

Examples:
```
wiki_query(ip="external-db", topic="uart apb dma fifo", depth=3)
wiki_query(ip="external-db", topic="ahb bus matrix interconnect", depth=2)
wiki_query(ip="external-db", topic="spi flash bridge", depth=3)
```

`depth`: 1 = id+title, 2 = +status/meta, 3 = +summary. Start broad (a family keyword
or `topic=""`), then drill into the specific id the first query surfaces.

## Workflow

1. **Identify the block/interface/topic** from the SSOT or the user's request.
2. **Query the external DB** with the relevant family + interface keywords.
3. **If a match is found**, cite it (id + path) and reuse its conventions:
   bus signal set + naming (APB `psel/penable/paddr/…`, AHB `haddr/htrans/…`),
   module decomposition, register map, reset/clock conventions.
4. **If nothing matches**, say so explicitly and proceed cleanly — never fabricate a citation.

## Rules

- Never claim something exists in the external DB without a `wiki_query` result backing it.
- Reuse *conventions and structure*; the active IP's SSOT remains authoritative on conflict.
- Complements the protocol spec experts ([[verilog-expert]], `pcie-expert`, …): use those
  for spec semantics, use this for "has someone already built / documented this?".
