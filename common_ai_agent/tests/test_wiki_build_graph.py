from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BUILD_GRAPH_PATH = REPO / "workflow" / "wiki" / "build_graph.py"


def _load_build_graph():
    spec = importlib.util.spec_from_file_location("wiki_build_graph_under_test", BUILD_GRAPH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ip_graph_keeps_sim_node_when_compare_json_is_missing(tmp_path: Path):
    ip = "partial_sim_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "sim").mkdir(parents=True)
    (ip_dir / "cov").mkdir(parents=True)
    (ip_dir / "sim" / "results.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0"><testcase name="smoke"/></testsuite>\n',
        encoding="utf-8",
    )
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text("{}\n", encoding="utf-8")
    (ip_dir / "cov" / "coverage.json").write_text('{"status": "blocked"}\n', encoding="utf-8")
    build_graph = _load_build_graph()

    graph = build_graph.build_ip(ip, tmp_path)

    nodes = {node["id"]: node for node in graph["nodes"]}
    assert "sim" in nodes
    assert nodes["sim"]["status"] == "present"
    assert "scoreboard_events=present" in nodes["sim"]["digest"]
    assert nodes["coverage"]["broken_refs"] == []


def test_ip_graph_reads_generated_and_user_wiki_dirs(tmp_path: Path):
    ip = "wiki_split_ip"
    wiki = tmp_path / ip / "wiki"
    (wiki / "_generated").mkdir(parents=True)
    (wiki / "user").mkdir()
    (wiki / "_generated" / "workflow-stages.md").write_text(
        "---\ntitle: Generated Workflow\n---\n# Generated Workflow\n\nrefresh-owned page\n",
        encoding="utf-8",
    )
    (wiki / "user" / "bringup-note.md").write_text(
        "---\ntitle: Bringup Note\ntags: [local]\n---\n# Bringup Note\n\nuser-authored page\n",
        encoding="utf-8",
    )
    build_graph = _load_build_graph()

    graph = build_graph.build_ip(ip, tmp_path)

    nodes = {node["id"]: node for node in graph["nodes"]}
    assert "workflow-stages" in nodes
    assert nodes["workflow-stages"]["path"] == f"{ip}/wiki/_generated/workflow-stages.md"
    assert "bringup-note" in nodes
    assert nodes["bringup-note"]["path"] == f"{ip}/wiki/user/bringup-note.md"


def test_project_graph_indexes_sim_debug_requirements_ledger():
    build_graph = _load_build_graph()

    wiki_root = REPO / "doc" / "wiki"
    page_path = wiki_root / "sim-debug-requirements-2026-06-01.md"
    graph = build_graph.build(wiki_root)

    nodes = {node["id"]: node for node in graph["nodes"]}
    assert "sim-debug-requirements-2026-06-01" in nodes
    node = nodes["sim-debug-requirements-2026-06-01"]
    assert "requirements" in node["tags"]
    assert "deep-test" in node["tags"]
    assert node["path"] == "doc/wiki/sim-debug-requirements-2026-06-01.md"
    assert node["summary"].startswith("This page consolidates the user-raised Sim Debug requirements")

    body = page_path.read_text(encoding="utf-8")
    assert "Deep Test Coverage Matrix" in body
    assert "Requirement-Level Deep Evidence" in body
    assert "SDR-007, SDR-014" in body
    assert "SDR-020, SDR-021, SDR-022, SDR-023" in body
    assert "frontend/atlas/__tests__/sim-debug-requirements-deep.test.tsx" in body
    assert "frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx" in body
    assert "frontend/atlas/__tests__/sim-debug-requirements-waveband.test.tsx" in body
    assert "tests/test_simulation_quality_gate.py" in body


def test_check_fails_when_existing_graph_markdown_inventory_is_stale(tmp_path: Path):
    wiki = tmp_path / "doc" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "fresh-page.md").write_text(
        "---\ntitle: Fresh Page\ntags: [rtl-gen]\n---\n# Fresh Page\n\nfresh summary\n",
        encoding="utf-8",
    )
    graph_path = wiki / "_graph.json"
    graph_path.write_text(
        '{\n'
        '  "schema_version": "wiki_graph.v1",\n'
        '  "node_count": 1,\n'
        '  "edge_count": 0,\n'
        '  "nodes": [\n'
        '    {"id": "old-page", "path": "doc/wiki/old-page.md", "type": "reference"}\n'
        '  ]\n'
        '}\n',
        encoding="utf-8",
    )
    build_graph = _load_build_graph()

    first_rc = build_graph.main(["--wiki", str(wiki), "--check", "--quiet"])
    rebuilt = graph_path.read_text(encoding="utf-8")
    second_rc = build_graph.main(["--wiki", str(wiki), "--check", "--quiet"])

    assert first_rc == 1
    assert '"id": "fresh-page"' in rebuilt
    assert '"old-page"' not in rebuilt
    assert second_rc == 0
