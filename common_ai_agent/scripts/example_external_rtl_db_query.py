#!/usr/bin/env python3
"""Reference *external query adapter* for the RTL DB (ATLAS_RTL_DB_QUERY contract).

This is the freest external integration point: the adapter OWNS the entire lookup —
its own structure, search, and transport. ATLAS does not parse a `_graph.json` or
impose any schema; it just hands the query to this command and returns its output.

    export ATLAS_RTL_DB_QUERY=/abs/path/to/your_query_adapter        # or .py
    # wiki_query(ip="rtl-db", topic="uart apb", depth=3) now calls THIS

----------------------------------------------------------------------------------
THE CONTRACT
----------------------------------------------------------------------------------
Invocation : ATLAS runs `<cmd>` (a `.py` via python3, anything else directly) and
             writes the query to STDIN as one JSON object:
               {"ip": "rtl-db", "topic": "<keywords>", "depth": 1|2|3, "max_nodes": N}
Output     : write the answer to STDOUT (markdown/plain text). ATLAS returns it
             verbatim under a "scope=rtl-db · external query" header. Non-zero exit
             with empty stdout is surfaced as an error.

Your adapter can do ANYTHING to produce that answer: read a foreign-format corpus,
query a database, call an HTTP/vector service, etc. A 3-line shell+curl wrapper that
POSTs the JSON to a service and echoes the response is a perfectly valid adapter.

----------------------------------------------------------------------------------
THIS EXAMPLE
----------------------------------------------------------------------------------
Searches a tiny in-script catalog (no files needed — proves the external side owns
the structure) and renders matching entries as markdown. Replace `CATALOG` + `search`
with your real source (SystemVerilog headers, a JSON manifest, an HTTP API, …).
"""

from __future__ import annotations

import json
import sys

# Foreign "structure": a flat catalog. Could equally be rows from a DB / API.
CATALOG = [
    {"id": "ext_uart", "title": "Vendor UART (APB, FIFO, DMA)",
     "tags": ["uart", "apb", "dma", "fifo"],
     "summary": "16550-style UART: APB regs, TX/RX FIFOs, modem control, DMA handshake."},
    {"id": "ext_spi", "title": "Vendor SPI master/slave",
     "tags": ["spi", "apb", "ahb", "dma", "fifo"],
     "summary": "Full-duplex SPI with FIFO, local-memory path, and DMA."},
    {"id": "ext_dma", "title": "Vendor DMA controller",
     "tags": ["dma", "ahb"],
     "summary": "Multi-channel AHB master offloading memory/peripheral transfers."},
    {"id": "ext_busmatrix", "title": "Vendor AHB bus matrix",
     "tags": ["ahb", "bus matrix", "interconnect"],
     "summary": "Multi-layer AHB interconnect tying masters to slaves."},
]


def search(topic: str, depth: int, max_nodes: int) -> str:
    terms = [t for t in topic.lower().replace("/", " ").replace("_", " ").split() if t]

    def score(e):
        hay = (e["id"] + " " + e["title"] + " " + " ".join(e["tags"]) + " " + e["summary"]).lower()
        return sum(1 for t in terms if t in hay)

    hits = CATALOG if not terms else [e for e in CATALOG if score(e) > 0]
    hits = sorted(hits, key=score, reverse=True)[:max_nodes]
    if not hits:
        return f"No RTL DB match for: {topic!r}"

    lines = [f"matches={len(hits)} (external adapter)"]
    for e in hits:
        lines.append(f"## {e['id']} — {e['title']}")
        lines.append(f"tags: {', '.join(e['tags'])}")
        if depth >= 3:
            lines.append(e["summary"])
        lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    try:
        q = json.load(sys.stdin)
    except Exception:
        q = {}
    topic = str(q.get("topic") or "")
    depth = int(q.get("depth") or 2)
    max_nodes = int(q.get("max_nodes") or 12)
    sys.stdout.write(search(topic, depth, max_nodes) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
