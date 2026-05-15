#!/usr/bin/env python3
"""Build a knowledge-graph index for common_ai_agent's project wiki.

Reads every `*.md` under `doc/wiki/`, parses optional YAML frontmatter
and `[[wiki-link]]` cross-references, and emits a single JSON index
that downstream tooling (LLM agents, CLI search, CI lint) can query
without re-grepping the wiki tree on every call.

Output schema (`doc/wiki/_graph.json`):

```
{
  "schema_version": "wiki_graph.v1",
  "generated_at": "<ISO8601>",
  "root": "doc/wiki",
  "node_count": <int>,
  "edge_count": <int>,
  "tags": {"<tag>": ["<node_id>", ...]},
  "types": {"<type>": ["<node_id>", ...]},
  "nodes": [
    {
      "id": "<slug>",
      "title": "<H1 or slug>",
      "type": "process|concept|rule|log|runbook|reference|run",
      "tags": ["..."],
      "related": ["<node_id>", ...],
      "outgoing": ["<node_id>", ...],
      "incoming": ["<node_id>", ...],
      "broken_refs": ["<missing_id>", ...],
      "updated": "YYYY-MM-DD",
      "summary": "<first non-empty paragraph after frontmatter, stripped>",
      "path": "doc/wiki/<file>.md",
      "size_bytes": <int>
    }
  ]
}
```

Run from the repo root or `common_ai_agent/`:

    python3 workflow/wiki/build_graph.py
    python3 workflow/wiki/build_graph.py --check    # exit 1 on broken refs
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

WIKI_LINK_RE = re.compile(r"\[\[([^\[\]\|#]+?)(?:[#|][^\[\]]*)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
KNOWN_TYPES = {
    "process",
    "concept",
    "rule",
    "log",
    "runbook",
    "reference",
    "run",
    "index",
}


def _read_yaml_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse a simple YAML frontmatter block. Falls back to a tiny scalar/list parser when PyYAML is unavailable."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    body = text[match.end():]
    raw = match.group(1)
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            data = {}
        return data, body
    except Exception:
        pass
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip("'\"") for item in value[1:-1].split(",")]
            data[key] = [item for item in items if item]
        else:
            data[key] = value.strip("'\"")
    return data, body


def _slug_from_path(path: Path) -> str:
    return path.stem


def _h1_title(body: str, fallback: str) -> str:
    match = H1_RE.search(body)
    return match.group(1).strip() if match else fallback


def _first_paragraph(body: str, max_chars: int = 360) -> str:
    text = H1_RE.sub("", body, count=1).strip()
    parts: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            if parts:
                break
            continue
        if line.startswith("#"):
            if parts:
                break
            continue
        if line.startswith(("|", "```", "    ")):
            if parts:
                break
            continue
        parts.append(line.strip())
    summary = " ".join(parts)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return summary


def _strip_code(body: str) -> str:
    """Drop fenced code blocks and inline backtick spans before harvesting wiki links.

    Wiki pages legitimately use `[[slug]]` inside example snippets and inline
    code to teach the syntax; those occurrences are not real edges and would
    otherwise show up as broken refs (e.g. `[[refs]]`, `[[page-slug]]`).
    """
    no_fences = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", no_fences)


def _wiki_links(body: str) -> list[str]:
    cleaned = _strip_code(body)
    seen: list[str] = []
    for match in WIKI_LINK_RE.finditer(cleaned):
        target = match.group(1).strip().lower()
        if not target or target.endswith(".md"):
            target = target.rsplit(".", 1)[0]
        if target and target not in seen:
            seen.append(target)
    return seen


def _normalize_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in KNOWN_TYPES else "reference"


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [token.strip() for token in re.split(r"[,\s]+", value) if token.strip()]
    return []


def build(wiki_root: Path) -> dict[str, Any]:
    files = sorted(p for p in wiki_root.glob("*.md") if p.is_file())
    nodes: dict[str, dict[str, Any]] = {}
    for path in files:
        raw = path.read_text(encoding="utf-8")
        fm, body = _read_yaml_frontmatter(raw)
        slug = str(fm.get("id") or _slug_from_path(path)).lower()
        title = str(fm.get("title") or _h1_title(body, slug))
        node_type = _normalize_type(fm.get("type"))
        tags = _normalize_list(fm.get("tags"))
        related = [item.lower() for item in _normalize_list(fm.get("related"))]
        outgoing = _wiki_links(body)
        merged_out = list(dict.fromkeys(related + outgoing))
        nodes[slug] = {
            "id": slug,
            "title": title,
            "type": node_type,
            "tags": tags,
            "related": related,
            "outgoing": merged_out,
            "incoming": [],
            "broken_refs": [],
            "updated": str(fm.get("updated") or ""),
            "summary": _first_paragraph(body),
            "path": str(path.relative_to(wiki_root.parent.parent)),
            "size_bytes": path.stat().st_size,
        }

    for node in nodes.values():
        for target in node["outgoing"]:
            if target in nodes:
                if node["id"] not in nodes[target]["incoming"]:
                    nodes[target]["incoming"].append(node["id"])
            else:
                if target not in node["broken_refs"]:
                    node["broken_refs"].append(target)

    tags_index: dict[str, list[str]] = defaultdict(list)
    types_index: dict[str, list[str]] = defaultdict(list)
    edge_count = 0
    for node in nodes.values():
        for tag in node["tags"]:
            tags_index[tag].append(node["id"])
        types_index[node["type"]].append(node["id"])
        edge_count += sum(1 for target in node["outgoing"] if target in nodes)

    return {
        "schema_version": "wiki_graph.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(wiki_root.relative_to(wiki_root.parent.parent)),
        "node_count": len(nodes),
        "edge_count": edge_count,
        "tags": {key: sorted(value) for key, value in sorted(tags_index.items())},
        "types": {key: sorted(value) for key, value in sorted(types_index.items())},
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--wiki",
        default=str(Path(__file__).resolve().parents[2] / "doc" / "wiki"),
        help="Path to the wiki root (defaults to common_ai_agent/doc/wiki).",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output JSON path (defaults to <wiki>/_graph.json).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when any wiki link points to a missing node.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational output.",
    )
    args = parser.parse_args(argv)

    wiki_root = Path(args.wiki).resolve()
    if not wiki_root.is_dir():
        print(f"[wiki/build_graph] missing wiki dir: {wiki_root}", file=sys.stderr)
        return 2

    output_path = Path(args.output).resolve() if args.output else wiki_root / "_graph.json"
    graph = build(wiki_root)
    output_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    broken: list[tuple[str, str]] = []
    for node in graph["nodes"]:
        for target in node["broken_refs"]:
            broken.append((node["id"], target))

    if not args.quiet:
        print(
            f"[wiki/build_graph] wrote {output_path}: "
            f"nodes={graph['node_count']} edges={graph['edge_count']} "
            f"types={len(graph['types'])} tags={len(graph['tags'])} broken_refs={len(broken)}"
        )
        if broken:
            for src, missing in broken[:12]:
                print(f"  broken: {src} → [[{missing}]]")
            if len(broken) > 12:
                print(f"  … and {len(broken) - 12} more broken links")

    if args.check and broken:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
