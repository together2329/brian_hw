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

