from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.andes_rtl_db_search import write_top_level_search_artifacts

RTL_SUFFIXES = {".v", ".sv"}
MODULE_RE = re.compile(r"^\s*module\s+([A-Za-z_]\w*)", re.MULTILINE)
IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")


@dataclass(frozen=True)
class HdlRoot:
    __slots__ = ("hdl", "rel", "page_id", "title", "kind", "top_level", "rtl_files")

    hdl: Path
    rel: str
    page_id: str
    title: str
    kind: str
    top_level: bool
    rtl_files: tuple[Path, ...]


def write_quality_artifacts(andes: Path, wiki: Path, today: str) -> None:
    roots = _discover_hdl_roots(andes)
    facts_dir = wiki / "_rtl_facts"
    facts_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for root in roots:
        facts = _root_facts(andes, root)
        if root.top_level:
            write_top_level_search_artifacts(wiki, root.page_id, facts)
        else:
            _write_root_page(wiki, root, facts, today)
            (facts_dir / f"{root.page_id}.json").write_text(
                json.dumps(facts, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        entries.append(_coverage_entry(wiki, root, facts))
    _write_coverage_page(wiki, andes, entries, today)
    _write_query_cookbook(wiki, roots, today)
    manifest = _coverage_manifest(entries)
    (wiki / "_coverage.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _discover_hdl_roots(andes: Path) -> list[HdlRoot]:
    candidates: list[tuple[Path, tuple[str, ...], str, bool, str]] = []
    base_counts: dict[str, int] = {}
    for hdl in sorted(path for path in andes.rglob("hdl") if path.is_dir()):
        try:
            rel_parts = hdl.relative_to(andes).parts
        except ValueError:
            continue
        if not rel_parts or rel_parts[0].startswith(".") or rel_parts[0] == "wiki":
            continue
        rel = "/".join(rel_parts)
        top_level = len(rel_parts) == 2 and rel_parts[-1] == "hdl"
        base_id = rel_parts[0] if top_level else f"rtlroot-{_slug('/'.join(rel_parts[:-1]))}"
        base_counts[base_id] = base_counts.get(base_id, 0) + 1
        candidates.append((hdl, rel_parts, rel, top_level, base_id))
    roots: list[HdlRoot] = []
    for hdl, rel_parts, rel, top_level, base_id in candidates:
        page_id = base_id if base_counts[base_id] == 1 else f"{base_id}-{_hash(rel)}"
        roots.append(
            HdlRoot(
                hdl=hdl,
                rel=rel,
                page_id=page_id,
                title=_title_for(rel_parts),
                kind=_kind_for(rel_parts, top_level),
                top_level=top_level,
                rtl_files=tuple(_rtl_files(hdl)),
            )
        )
    return roots


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text.lower()).strip("-") or "hdl-root"


def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def _title_for(parts: tuple[str, ...]) -> str:
    stem = parts[-2] if len(parts) > 1 else "hdl"
    if stem in {"hdl", "top", "rtl", "src"} and len(parts) > 2:
        stem = parts[-3]
    return f"{stem} HDL root"


def _kind_for(parts: tuple[str, ...], top_level: bool) -> str:
    lowered = {part.lower() for part in parts}
    if top_level:
        return "canonical"
    if "andes_vip" in lowered:
        return "verification"
    if "models" in lowered:
        return "model"
    if "macro" in lowered:
        return "macro"
    if "andes_ip" in lowered:
        return "design"
    return "nested"


def _rtl_files(hdl: Path) -> list[Path]:
    return sorted(path for path in hdl.rglob("*") if path.is_file() and path.suffix.lower() in RTL_SUFFIXES)


def _root_facts(andes: Path, root: HdlRoot) -> dict[str, Any]:
    modules: list[str] = []
    clocks: list[str] = []
    resets: list[str] = []
    line_count = 0
    for path in root.rtl_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        line_count += text.count("\n") + 1
        modules.extend(name for name in MODULE_RE.findall(text) if name not in modules)
        for ident in IDENT_RE.findall(text):
            low = ident.lower()
            if ("clk" in low or "clock" in low) and ident not in clocks:
                clocks.append(ident)
            if ("rst" in low or "reset" in low) and ident not in resets:
                resets.append(ident)
    diagnostics = [] if root.rtl_files else [f"{root.rel}: no .v/.sv RTL files found under hdl/"]
    features = _features(modules, clocks, resets, root.rtl_files)
    return {
        "schema_version": "andes_rtl_root_coverage.v1",
        "block": root.page_id,
        "hdl_root": root.rel,
        "root_kind": root.kind,
        "status": "indexed" if root.rtl_files else "empty",
        "source_files": [path.relative_to(andes).as_posix() for path in root.rtl_files],
        "rtl_file_count": len(root.rtl_files),
        "line_count": line_count,
        "modules": modules,
        "clocks": clocks[:16],
        "resets": resets[:16],
        "features": features,
        "diagnostics": diagnostics,
    }


def _features(modules: list[str], clocks: list[str], resets: list[str], files: tuple[Path, ...]) -> list[str]:
    features: list[str] = []
    if modules:
        features.append("module")
    if clocks:
        features.append("clock")
    if resets:
        features.append("reset")
    text = " ".join(path.read_text(encoding="utf-8", errors="replace") for path in files[:8])
    if "always_ff" in text:
        features.append("register")
    if re.search(r"\bcase\s*\(", text):
        features.append("fsm")
    if re.search(r"\bassign\b|<=|=", text):
        features.append("datapath")
    return features


def _write_root_page(wiki: Path, root: HdlRoot, facts: dict[str, Any], today: str) -> None:
    tag_items = ["rtl-db", "andes", "hdl-root", "coverage", root.kind]
    tag_items.extend(str(item) for item in facts["features"])
    tags = ", ".join(dict.fromkeys(tag_items))
    modules = ", ".join(str(item) for item in facts["modules"]) or "-"
    features = ", ".join(str(item) for item in facts["features"]) or "empty"
    diagnostics = "\n".join(f"- {item}" for item in facts["diagnostics"]) or "- none"
    sources = "\n".join(f"- `{item}`" for item in facts["source_files"]) or "- no RTL source files"
    body = f"""---
id: {root.page_id}
title: {root.title}
type: reference
tags: [{tags}]
related: [coverage, rtl-inventory, rtl-query-cookbook, index]
updated: {today}
---
# {root.title}

Nested Andes HDL root indexed for the external RTL DB LLM Wiki. It exists so agents can discover platform, VIP, model, macro, and copied IP RTL that is not a canonical top-level block.

- **HDL root:** `{root.rel}`
- **Root kind:** `{root.kind}`
- **Status:** `{facts['status']}`
- **RTL files:** {facts['rtl_file_count']}
- **Lines:** {facts['line_count']}
- **Modules:** {modules}
- **Features:** {features}
- **Fact sidecar:** `_rtl_facts/{root.page_id}.json`

Search terms: module port parameter fsm datapath register memory clock reset clk rst coverage hdl root.

## RTL files

{sources}

## Diagnostics

{diagnostics}

See [[coverage]], [[rtl-inventory]], and [[rtl-query-cookbook]].
"""
    (wiki / f"{root.page_id}.md").write_text(body, encoding="utf-8")


def _coverage_entry(wiki: Path, root: HdlRoot, facts: dict[str, Any]) -> dict[str, Any]:
    page = f"{root.page_id}.md"
    fact = f"_rtl_facts/{root.page_id}.json"
    return {
        "id": root.page_id,
        "hdl_root": root.rel,
        "kind": root.kind,
        "status": facts["status"],
        "page": page,
        "fact": fact,
        "rtl_file_count": facts["rtl_file_count"],
        "module_count": len(facts["modules"]),
        "diagnostics": facts["diagnostics"],
        "page_exists": (wiki / page).is_file(),
        "fact_exists": (wiki / fact).is_file(),
    }


def _coverage_manifest(entries: list[dict[str, Any]]) -> dict[str, Any]:
    missing_pages = [str(entry["id"]) for entry in entries if not entry["page_exists"]]
    missing_facts = [str(entry["id"]) for entry in entries if not entry["fact_exists"]]
    empty_roots = [entry for entry in entries if entry["status"] == "empty"]
    return {
        "schema_version": "andes_rtl_db_coverage.v1",
        "summary": {
            "total_hdl_roots": len(entries),
            "nonempty_hdl_roots": len(entries) - len(empty_roots),
            "empty_hdl_roots": len(empty_roots),
            "missing_pages": missing_pages,
            "missing_facts": missing_facts,
        },
        "entries": entries,
    }


def _write_coverage_page(wiki: Path, andes: Path, entries: list[dict[str, Any]], today: str) -> None:
    rows = ["| HDL root | Kind | Status | RTL files | Modules | Fact |", "| --- | --- | --- | ---: | ---: | --- |"]
    for entry in entries:
        rows.append(
            f"| [[{entry['id']}]] `{entry['hdl_root']}` | {entry['kind']} | {entry['status']} | "
            f"{entry['rtl_file_count']} | {entry['module_count']} | `{entry['fact']}` |"
        )
    body = f"""---
id: coverage
title: Andes RTL DB wiki coverage
type: reference
tags: [rtl-db, andes, coverage, inventory]
related: [index, rtl-inventory, rtl-query-cookbook]
updated: {today}
---
# Andes RTL DB wiki coverage

Coverage manifest for every discovered `hdl/` root under `{andes}`. Use this page to confirm that canonical IP, nested platform IP, VIP models, macros, and empty HDL roots are all represented in the LLM Wiki graph.

{chr(10).join(rows)}

Machine-readable manifest: `_coverage.json`.
"""
    (wiki / "coverage.md").write_text(body, encoding="utf-8")


def _write_query_cookbook(wiki: Path, roots: list[HdlRoot], today: str) -> None:
    samples = roots[:3] + [root for root in roots if not root.top_level][:5]
    sample_lines = "\n".join(f"- [[{root.page_id}]] - `{root.rel}`" for root in dict.fromkeys(samples))
    body = f"""---
id: rtl-query-cookbook
title: Andes RTL DB query cookbook
type: runbook
tags: [rtl-db, andes, query, cookbook]
related: [index, coverage, rtl-inventory]
updated: {today}
---
# Andes RTL DB query cookbook

Practical query patterns for using the generated Andes RTL DB LLM Wiki from an agent.

```sh
wiki_query(ip="rtl-db", topic="uart apb dma", depth=3)
wiki_query(ip="rtl-db", topic="coverage nested hdl root", depth=3)
wiki_query(ip="andes", topic="ae210 platform module clock reset", depth=3)
```

Useful terms: module, port, parameter, fsm, datapath, register, memory, clock, reset, clk, rst, coverage, platform, vip, model, macro.

## Sample indexed roots

{sample_lines or '- none'}

See [[coverage]] for the complete root table and [[rtl-inventory]] for canonical top-level IP blocks.
"""
    (wiki / "rtl-query-cookbook.md").write_text(body, encoding="utf-8")
