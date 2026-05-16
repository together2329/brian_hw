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


def _markdown_nodes(wiki_root: Path, path_root: Path) -> dict[str, dict[str, Any]]:
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
        try:
            rel_path = path.relative_to(path_root)
        except ValueError:
            rel_path = path
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
            "path": str(rel_path),
            "size_bytes": path.stat().st_size,
        }
    return nodes


def _wire_edges(nodes: dict[str, dict[str, Any]]) -> int:
    edge_count = 0
    for node in nodes.values():
        for target in node["outgoing"]:
            if target in nodes:
                if node["id"] not in nodes[target]["incoming"]:
                    nodes[target]["incoming"].append(node["id"])
                edge_count += 1
            else:
                if target not in node["broken_refs"]:
                    node["broken_refs"].append(target)
    return edge_count


def _graph_envelope(
    schema: str,
    root_label: str,
    nodes: dict[str, dict[str, Any]],
    edge_count: int,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tags_index: dict[str, list[str]] = defaultdict(list)
    types_index: dict[str, list[str]] = defaultdict(list)
    for node in nodes.values():
        for tag in node["tags"]:
            tags_index[tag].append(node["id"])
        types_index[node["type"]].append(node["id"])
    envelope: dict[str, Any] = {
        "schema_version": schema,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": root_label,
        "node_count": len(nodes),
        "edge_count": edge_count,
        "tags": {key: sorted(value) for key, value in sorted(tags_index.items())},
        "types": {key: sorted(value) for key, value in sorted(types_index.items())},
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
    }
    if extra:
        envelope.update(extra)
    return envelope


def build(wiki_root: Path) -> dict[str, Any]:
    path_root = wiki_root.parent.parent
    nodes = _markdown_nodes(wiki_root, path_root)
    edge_count = _wire_edges(nodes)
    return _graph_envelope(
        "wiki_graph.v1",
        str(wiki_root.relative_to(path_root)),
        nodes,
        edge_count,
    )


def _json_or_none(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _file_updated(path: Path, override: str = "") -> str:
    if override:
        return str(override)
    if not path.exists():
        return ""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime))


def _status_pf(passed: bool | None) -> str:
    if passed is True:
        return "pass"
    if passed is False:
        return "fail"
    return "unknown"


def _make_artifact_node(
    *,
    node_id: str,
    title: str,
    node_type: str,
    status: str,
    digest: str,
    path: Path | str,
    updated: str,
    project_root: Path,
    extra_tags: list[str] | None = None,
    related: list[str] | None = None,
) -> dict[str, Any]:
    try:
        rel_path = str(Path(path).resolve().relative_to(project_root))
    except (ValueError, OSError):
        rel_path = str(path)
    size = 0
    p = Path(path)
    if p.exists():
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
    summary = digest if digest else f"{title}"
    tags = ["artifact"] + (extra_tags or [])
    return {
        "id": node_id,
        "title": title,
        "type": node_type,
        "tags": tags,
        "related": [item.lower() for item in (related or [])],
        "outgoing": [item.lower() for item in (related or [])],
        "incoming": [],
        "broken_refs": [],
        "updated": updated,
        "summary": summary,
        "status": status,
        "digest": digest,
        "path": rel_path,
        "size_bytes": size,
    }


def _ip_artifact_nodes(ip: str, ip_dir: Path, project_root: Path) -> dict[str, dict[str, Any]]:
    """Build synthetic artifact nodes for an IP's canonical directory layout."""
    nodes: dict[str, dict[str, Any]] = {}

    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if ssot_path.is_file():
        text = ssot_path.read_text(encoding="utf-8", errors="replace")
        section_count = sum(1 for line in text.splitlines() if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:", line))
        nodes["ssot"] = _make_artifact_node(
            node_id="ssot",
            title=f"{ip} SSOT",
            node_type="reference",
            status="present",
            digest=f"sections={section_count} size={ssot_path.stat().st_size}B",
            path=ssot_path,
            updated=_file_updated(ssot_path),
            project_root=project_root,
            extra_tags=["ssot"],
        )

    fl_check = _json_or_none(ip_dir / "model" / "fl_model_check.json")
    manifest = _json_or_none(ip_dir / "model" / "manifest.json")
    fl_path = ip_dir / "model" / "functional_model.py"
    if fl_check or manifest or fl_path.exists():
        passed = bool(fl_check.get("passed")) if isinstance(fl_check, dict) else None
        units = manifest.get("decomposition_units") if isinstance(manifest, dict) else None
        bins = manifest.get("fcov_bins") if isinstance(manifest, dict) else None
        digest = ""
        if units is not None or bins is not None:
            digest = f"decomposition_units={units} fcov_bins={bins}"
        if isinstance(fl_check, dict):
            digest = (digest + " " if digest else "") + f"check={'pass' if passed else 'fail'}"
        nodes["fl_model"] = _make_artifact_node(
            node_id="fl_model",
            title=f"{ip} FunctionalModel",
            node_type="reference",
            status=_status_pf(passed) if fl_check else "present",
            digest=digest.strip() or "functional_model.py present",
            path=fl_path if fl_path.exists() else (ip_dir / "model"),
            updated=_file_updated(fl_path) or _file_updated(ip_dir / "model" / "fl_model_check.json"),
            project_root=project_root,
            extra_tags=["fl-model-gen"],
            related=["ssot"],
        )

    cl_path = ip_dir / "model" / "cycle_model.py"
    if cl_path.is_file():
        nodes["cl_model"] = _make_artifact_node(
            node_id="cl_model",
            title=f"{ip} CycleModel",
            node_type="reference",
            status="present",
            digest=f"cycle_model.py size={cl_path.stat().st_size}B",
            path=cl_path,
            updated=_file_updated(cl_path),
            project_root=project_root,
            extra_tags=["cl-model-gen"],
            related=["ssot"],
        )

    rtl_compile = _json_or_none(ip_dir / "rtl" / "rtl_compile.json")
    provenance = _json_or_none(ip_dir / "rtl" / "rtl_authoring_provenance.json")
    filelist_path = ip_dir / "list" / f"{ip}.f"
    rtl_dir = ip_dir / "rtl"
    rtl_files = sorted(p.name for p in rtl_dir.glob("*.sv")) if rtl_dir.is_dir() else []
    if rtl_compile or provenance or rtl_files:
        errors = rtl_compile.get("errors") if isinstance(rtl_compile, dict) else None
        warnings = rtl_compile.get("warnings") if isinstance(rtl_compile, dict) else None
        status = "unknown"
        if isinstance(errors, int):
            status = "pass" if errors == 0 else "fail"
        digest_parts = []
        if rtl_files:
            digest_parts.append(f"files={len(rtl_files)}")
        if errors is not None:
            digest_parts.append(f"compile_errors={errors}")
        if warnings is not None:
            digest_parts.append(f"compile_warnings={warnings}")
        if isinstance(provenance, dict):
            digest_parts.append(f"surface={provenance.get('surface', '?')}")
        nodes["rtl"] = _make_artifact_node(
            node_id="rtl",
            title=f"{ip} RTL",
            node_type="reference",
            status=status,
            digest=" ".join(digest_parts) or "rtl present",
            path=rtl_dir,
            updated=_file_updated(ip_dir / "rtl" / "rtl_compile.json") or _file_updated(rtl_dir),
            project_root=project_root,
            extra_tags=["rtl-gen"],
            related=["ssot", "fl_model"],
        )
    if filelist_path.is_file():
        nodes["filelist"] = _make_artifact_node(
            node_id="filelist",
            title=f"{ip} filelist",
            node_type="reference",
            status="present",
            digest=f"{filelist_path.name} size={filelist_path.stat().st_size}B",
            path=filelist_path,
            updated=_file_updated(filelist_path),
            project_root=project_root,
            extra_tags=["rtl-gen"],
            related=["rtl"],
        )

    lint = _json_or_none(ip_dir / "lint" / "dut_lint.json")
    if isinstance(lint, dict):
        errors = lint.get("errors")
        warnings = lint.get("warnings")
        status = "pass" if errors == 0 and warnings == 0 else "fail"
        nodes["lint"] = _make_artifact_node(
            node_id="lint",
            title=f"{ip} Lint",
            node_type="reference",
            status=status,
            digest=f"errors={errors} warnings={warnings}",
            path=ip_dir / "lint" / "dut_lint.json",
            updated=_file_updated(ip_dir / "lint" / "dut_lint.json"),
            project_root=project_root,
            extra_tags=["lint"],
            related=["rtl"],
        )

    tb_dir = ip_dir / "tb"
    tb_manifest = _json_or_none(tb_dir / "cocotb" / "tb_manifest.json")
    if tb_dir.is_dir() or tb_manifest:
        nodes["tb"] = _make_artifact_node(
            node_id="tb",
            title=f"{ip} Testbench",
            node_type="reference",
            status="present",
            digest=f"manifest={'yes' if tb_manifest else 'missing'}",
            path=tb_dir,
            updated=_file_updated(tb_dir / "cocotb" / "tb_manifest.json") or _file_updated(tb_dir),
            project_root=project_root,
            extra_tags=["tb-gen"],
            related=["rtl", "fl_model"],
        )

    sim_dir = ip_dir / "sim"
    sim_compare_path = sim_dir / "fl_rtl_compare.json"
    sim_audit_path = sim_dir / "fl_rtl_goal_audit.json"
    sim_result_path = sim_dir / "results.xml"
    sim_scoreboard_path = sim_dir / "scoreboard_events.jsonl"
    sim_report_path = sim_dir / "sim_report.txt"
    sim_compare = _json_or_none(sim_compare_path)
    sim_audit = _json_or_none(sim_audit_path)
    sim_evidence_present = sim_result_path.is_file() or sim_scoreboard_path.is_file() or sim_report_path.is_file()
    if sim_compare or sim_audit or sim_evidence_present:
        total = None
        passed = None
        mismatches = None
        if isinstance(sim_compare, dict):
            total = sim_compare.get("total_rows", sim_compare.get("total"))
            passed = sim_compare.get("pass_rows", sim_compare.get("pass"))
            mismatches = sim_compare.get("mismatch_count")
            if mismatches is None and isinstance(sim_compare.get("mismatches"), list):
                mismatches = len(sim_compare["mismatches"])
        bins_hit = None
        bins_total = None
        if isinstance(sim_audit, dict):
            bins_hit = sim_audit.get("bins_hit") or sim_audit.get("hit") or sim_audit.get("covered")
            bins_total = sim_audit.get("bins_total") or sim_audit.get("total")
            if bins_hit is None and isinstance(sim_audit.get("bins"), dict):
                bins_doc = sim_audit["bins"]
                bins_hit = bins_doc.get("hit") or bins_doc.get("hit_count")
                bins_total = bins_doc.get("total")
        status = "present" if sim_evidence_present else "unknown"
        if isinstance(mismatches, int) and mismatches == 0 and (
            isinstance(sim_compare, dict)
            and (
                sim_compare.get("all_matched") is True
                or (isinstance(passed, int) and isinstance(total, int) and passed == total)
            )
        ):
            status = "pass"
        elif isinstance(mismatches, int) and mismatches > 0:
            status = "fail"
        digest_parts = []
        if total is not None:
            digest_parts.append(f"goals={passed}/{total}")
        if mismatches is not None:
            digest_parts.append(f"mismatches={mismatches}")
        if bins_hit is not None:
            digest_parts.append(f"bins={bins_hit}/{bins_total}")
        if sim_result_path.is_file():
            digest_parts.append("results.xml=present")
        if sim_scoreboard_path.is_file():
            digest_parts.append("scoreboard_events=present")
        nodes["sim"] = _make_artifact_node(
            node_id="sim",
            title=f"{ip} Simulation",
            node_type="reference",
            status=status,
            digest=" ".join(digest_parts) or "sim evidence present",
            path=sim_dir,
            updated=_file_updated(sim_compare_path)
            or _file_updated(sim_audit_path)
            or _file_updated(sim_result_path)
            or _file_updated(sim_scoreboard_path)
            or _file_updated(sim_report_path),
            project_root=project_root,
            extra_tags=["sim"],
            related=["rtl", "tb", "fl_model"],
        )

    cov_dir = ip_dir / "cov"
    cov_files = sorted(cov_dir.glob("coverage*.json")) if cov_dir.is_dir() else []
    if cov_files:
        cov_doc = _json_or_none(cov_files[0])
        digest = ""
        if isinstance(cov_doc, dict):
            for key in ("coverage", "hit_ratio", "percent", "summary"):
                if key in cov_doc:
                    digest = f"{key}={cov_doc[key]}"
                    break
        nodes["coverage"] = _make_artifact_node(
            node_id="coverage",
            title=f"{ip} Coverage",
            node_type="reference",
            status="present",
            digest=digest or f"reports={len(cov_files)}",
            path=cov_files[0],
            updated=_file_updated(cov_files[0]),
            project_root=project_root,
            extra_tags=["coverage"],
            related=["sim"],
        )

    audit_path = ip_dir / "verify" / "equivalence_goals.json"
    audit_doc = _json_or_none(audit_path)
    if isinstance(audit_doc, dict):
        goals = audit_doc.get("goals") or []
        total = audit_doc.get("required") or audit_doc.get("required_count") or len(goals) if isinstance(goals, list) else None
        blocked = audit_doc.get("blocked")
        if blocked is None and isinstance(goals, list):
            blocked = sum(1 for g in goals if isinstance(g, dict) and g.get("blocked"))
        status = "pass" if (blocked == 0) else ("blocked" if blocked else "present")
        digest_parts = []
        if total is not None:
            digest_parts.append(f"goals={total}")
        if blocked is not None:
            digest_parts.append(f"blocked={blocked}")
        nodes["audit"] = _make_artifact_node(
            node_id="audit",
            title=f"{ip} Equivalence Goals",
            node_type="reference",
            status=status,
            digest=" ".join(digest_parts) or "equivalence_goals present",
            path=audit_path,
            updated=_file_updated(audit_path),
            project_root=project_root,
            extra_tags=["equiv-goals"],
            related=["fl_model", "rtl"],
        )

    run_log = _json_or_none(ip_dir / "logs" / "headless_run.json")
    if isinstance(run_log, dict):
        stages = run_log.get("stages") or []
        last_stage = stages[-1] if isinstance(stages, list) and stages else {}
        status = last_stage.get("status") if isinstance(last_stage, dict) else "unknown"
        digest = f"stages={len(stages)} last={last_stage.get('stage', '?')}:{status}" if stages else f"status={run_log.get('status', '?')}"
        nodes["last_run"] = _make_artifact_node(
            node_id="last_run",
            title=f"{ip} last run",
            node_type="log",
            status=str(status or "unknown"),
            digest=digest,
            path=ip_dir / "logs" / "headless_run.json",
            updated=_file_updated(ip_dir / "logs" / "headless_run.json"),
            project_root=project_root,
            extra_tags=["run-log"],
        )

    return nodes


def build_ip(ip: str, project_root: Path) -> dict[str, Any]:
    """Build a per-IP knowledge graph: <ip>/wiki/*.md + synthetic artifact nodes."""
    ip_dir = (project_root / ip).resolve()
    if not ip_dir.is_dir():
        raise SystemExit(f"[wiki/build_graph] IP directory not found: {ip_dir}")
    wiki_dir = ip_dir / "wiki"
    if wiki_dir.is_dir():
        md_nodes = _markdown_nodes(wiki_dir, project_root)
    else:
        md_nodes = {}
    artifact_nodes = _ip_artifact_nodes(ip, ip_dir, project_root)
    nodes: dict[str, dict[str, Any]] = {}
    nodes.update(md_nodes)
    for slug, node in artifact_nodes.items():
        if slug in nodes:
            existing = nodes[slug]
            existing.setdefault("status", node.get("status"))
            existing.setdefault("digest", node.get("digest"))
            for tag in node.get("tags") or []:
                if tag not in existing["tags"]:
                    existing["tags"].append(tag)
            for ref in node.get("outgoing") or []:
                if ref not in existing["outgoing"]:
                    existing["outgoing"].append(ref)
        else:
            nodes[slug] = node
    edge_count = _wire_edges(nodes)
    return _graph_envelope(
        "ip_wiki_graph.v1",
        f"{ip}/wiki",
        nodes,
        edge_count,
        extra={"ip": ip},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--wiki",
        default=str(Path(__file__).resolve().parents[2] / "doc" / "wiki"),
        help="Path to the wiki root (defaults to common_ai_agent/doc/wiki). Ignored when --ip is set.",
    )
    parser.add_argument(
        "--ip",
        default="",
        help="IP name. When set, builds <project-root>/<ip>/wiki/_graph.json with synthetic artifact nodes.",
    )
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Project root used to resolve <ip>/ when --ip is set.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output JSON path (defaults to <wiki>/_graph.json or <ip>/wiki/_graph.json).",
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

    if args.ip:
        project_root = Path(args.project_root).resolve()
        graph = build_ip(args.ip, project_root)
        ip_wiki_dir = project_root / args.ip / "wiki"
        ip_wiki_dir.mkdir(parents=True, exist_ok=True)
        output_path = Path(args.output).resolve() if args.output else ip_wiki_dir / "_graph.json"
    else:
        wiki_root = Path(args.wiki).resolve()
        if not wiki_root.is_dir():
            print(f"[wiki/build_graph] missing wiki dir: {wiki_root}", file=sys.stderr)
            return 2
        graph = build(wiki_root)
        output_path = Path(args.output).resolve() if args.output else wiki_root / "_graph.json"
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
