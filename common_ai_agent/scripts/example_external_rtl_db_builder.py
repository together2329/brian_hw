#!/usr/bin/env python3
"""Reference *external* RTL-DB wiki builder (override adapter).

ATLAS reads an external "previous-project RTL DB" through `wiki_query(ip="rtl-db")`,
which expects a `<wiki_root>/_graph.json` in the `wiki_graph.v1` node schema. When a
foreign wiki has a *different structure* (not ATLAS's markdown + YAML-frontmatter +
`[[links]]` convention), you don't convert it by hand — you point ATLAS at an adapter:

    export ATLAS_RTL_DB_WIKI=/path/to/foreign/wiki
    export ATLAS_RTL_DB_BUILDER=/abs/path/to/your_builder.py   # this contract

ATLAS then runs `your_builder.py --wiki <wiki_root>` instead of the built-in
`workflow/wiki/build_graph.py`, and reads the `_graph.json` you write. Your builder
owns all knowledge of the foreign structure; ATLAS only ever sees the normalized graph.

----------------------------------------------------------------------------------
THE CONTRACT (what any external builder must satisfy)
----------------------------------------------------------------------------------
Invocation : `<builder> --wiki <wiki_root>`     (python files are run with python3)
Output     : write `<wiki_root>/_graph.json`, a JSON object:
             {
               "schema_version": "wiki_graph.v1",
               "node_count": <int>, "edge_count": <int>,
               "nodes": [
                 { "id": "<slug>",            # required, unique, lowercase
                   "title": "<human title>",  # shown in results
                   "type": "reference",       # any of build_graph's KNOWN_TYPES
                   "tags": ["rtl-db", ...],   # searchable
                   "summary": "<one paragraph>",
                   "path": "<source path>",   # shown so the agent can open it
                   "outgoing": ["<other-id>", ...]   # optional cross-links
                 }, ...
               ]
             }
Only `id` is strictly required; the rest improve search/render. `wiki_query`
matches topics against id/title/tags/type/path/status/digest/summary.

If instead the foreign system produces its OWN `_graph.json` by some other pipeline,
skip the builder and set `ATLAS_RTL_DB_NO_REBUILD=1` so ATLAS reads it as-is and never
rebuilds/clobbers it.

----------------------------------------------------------------------------------
THIS EXAMPLE
----------------------------------------------------------------------------------
Demonstrates a deliberately *non-ATLAS* structure: a directory of `*.txt` reference
files, each with a tiny header:

    title: ATCUART100 UART
    tags: uart, apb, dma
    related: atcdmac100

    <free-text summary / notes ...>

Replace the `parse_entry` / discovery logic with whatever your real DB uses
(SystemVerilog headers, a CSV/JSON manifest, an HTTP export, a database query, …).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def parse_entry(path: Path) -> dict:
    """Parse one foreign `*.txt` reference file into a graph node."""
    text = path.read_text(encoding="utf-8", errors="replace")
    title = path.stem
    tags: list[str] = ["rtl-db", "external"]
    related: list[str] = []
    body_lines: list[str] = []
    in_body = False
    for line in text.splitlines():
        if not in_body and line.strip() == "":
            in_body = True
            continue
        if not in_body and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()
            if key == "title":
                title = val or title
            elif key == "tags":
                tags += [t.strip().lower() for t in val.split(",") if t.strip()]
            elif key == "related":
                related += [t.strip().lower() for t in val.split(",") if t.strip()]
            else:
                in_body = True
                body_lines.append(line)
        else:
            in_body = True
            body_lines.append(line)
    summary = " ".join(l.strip() for l in body_lines if l.strip())[:360]
    return {
        "id": path.stem.lower(),
        "title": title,
        "type": "reference",
        "tags": list(dict.fromkeys(tags)),
        "related": related,
        "outgoing": related,
        "incoming": [],
        "broken_refs": [],
        "summary": summary,
        "path": str(path),
        "size_bytes": path.stat().st_size,
    }


def build(wiki_root: Path) -> dict:
    nodes = {}
    for txt in sorted(wiki_root.glob("*.txt")):
        node = parse_entry(txt)
        nodes[node["id"]] = node
    # wire incoming edges from outgoing
    edge_count = 0
    for n in nodes.values():
        for t in n["outgoing"]:
            if t in nodes:
                if n["id"] not in nodes[t]["incoming"]:
                    nodes[t]["incoming"].append(n["id"])
                edge_count += 1
            elif t not in n["broken_refs"]:
                n["broken_refs"].append(t)
    return {
        "schema_version": "wiki_graph.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(wiki_root),
        "node_count": len(nodes),
        "edge_count": edge_count,
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Example external RTL-DB wiki builder (ATLAS_RTL_DB_BUILDER contract).")
    ap.add_argument("--wiki", required=True, help="Wiki root ATLAS points at (ATLAS_RTL_DB_WIKI).")
    ap.add_argument("--output", default="", help="Output _graph.json (default <wiki>/_graph.json).")
    args = ap.parse_args(argv)
    wiki_root = Path(args.wiki).expanduser().resolve()
    wiki_root.mkdir(parents=True, exist_ok=True)
    graph = build(wiki_root)
    out = Path(args.output).resolve() if args.output else wiki_root / "_graph.json"
    out.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[example-external-builder] wrote {out}: nodes={graph['node_count']} edges={graph['edge_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
