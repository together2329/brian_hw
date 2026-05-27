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
