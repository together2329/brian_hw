from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_wiki_query_matches_handoff_approval_terms(tmp_path: Path, monkeypatch) -> None:
    """Agent wiki lookup should find approval handoff pages from natural terms,
    not only exact title substrings."""
    ip = "arm_m0_min"
    wiki_dir = tmp_path / ip / "wiki"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "_graph.json").write_text(
        json.dumps(
            {
                "schema_version": "ip_wiki_graph.v1",
                "node_count": 1,
                "edge_count": 0,
                "nodes": [
                    {
                        "id": "index",
                        "title": "arm_m0_min Wiki Index",
                        "type": "reference",
                        "tags": [],
                        "path": "arm_m0_min/wiki/index.md",
                        "status": "blocked",
                        "digest": "final signoff blocked on req",
                        "summary": (
                            "CPU handoff links approval request and "
                            "approve_locked_scope promotion boundary."
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("COMMON_AI_AGENT_HOME", raising=False)

    from core.tools import wiki_query

    result = wiki_query(ip=ip, topic="CPU handoff approval req", depth=3)

    assert "matches=1/1" in result
    assert "path: arm_m0_min/wiki/index.md" in result
    assert "approve_locked_scope" in result


def test_wiki_query_splits_path_like_terms(tmp_path: Path, monkeypatch) -> None:
    ip = "arm_m0_min"
    wiki_dir = tmp_path / ip / "wiki"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "_graph.json").write_text(
        json.dumps(
            {
                "schema_version": "ip_wiki_graph.v1",
                "node_count": 1,
                "edge_count": 0,
                "nodes": [
                    {
                        "id": "user_handoff",
                        "title": "User Handoff",
                        "type": "reference",
                        "tags": [],
                        "path": "arm_m0_min/doc/arm_m0_min_user_handoff.md",
                        "summary": "Verification commands for req approval.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("COMMON_AI_AGENT_HOME", raising=False)

    from core.tools import wiki_query

    result = wiki_query(ip=ip, topic="user handoff", depth=2)

    assert "matches=1/1" in result
    assert "arm_m0_min_user_handoff.md" in result


def test_wiki_query_reads_external_rtl_db_wiki_without_ip_scope(tmp_path: Path, monkeypatch) -> None:
    rtl_root = tmp_path / "andes"
    wiki_dir = rtl_root / "wiki"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "atcuart100.md").write_text(
        """---
id: atcuart100
title: ATCUART100 UART RTL
type: reference
tags: [rtl-db, andes, uart, apb]
---
# ATCUART100 UART RTL

External Andes peripheral RTL reference. APB register interface, UART TX/RX,
interrupt, baud-rate divider, and FIFO control are available in hdl/*.v.
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("COMMON_AI_AGENT_HOME", str(PROJECT_ROOT))
    monkeypatch.setenv("ATLAS_RTL_DB_WIKI", str(rtl_root))
    monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)

    from core.tools import wiki_query

    result = wiki_query(ip="rtl-db", topic="andes uart apb", depth=3)

    assert "scope=rtl-db" in result
    assert "matches=1/1" in result
    assert "ATCUART100 UART RTL" in result
    assert "IP directory not found" not in result
    assert (wiki_dir / "_graph.json").is_file()


def test_wiki_query_reports_missing_external_rtl_db_config(monkeypatch) -> None:
    monkeypatch.delenv("ATLAS_RTL_DB_WIKI", raising=False)
    monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)

    from core.tools import wiki_query

    result = wiki_query(ip="rtl-db", topic="uart")

    assert "ATLAS_RTL_DB_WIKI is not configured" in result


def test_real_arm_m0_min_wiki_query_finds_cpu_handoff(monkeypatch) -> None:
    """The real CPU IP wiki should be discoverable through the same tool path
    agents use during handoff or review."""
    if not (PROJECT_ROOT / "arm_m0_min").is_dir():
        pytest.skip("arm_m0_min fixture IP is not present in this checkout")
    subprocess.run(
        [
            "python3",
            "workflow/wiki/build_graph.py",
            "--ip",
            "arm_m0_min",
            "--quiet",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("COMMON_AI_AGENT_HOME", raising=False)

    from core.tools import wiki_query

    result = wiki_query(ip="arm_m0_min", topic="CPU handoff approval req", depth=3)

    assert "matches=2/14" in result
    assert "arm_m0_min/wiki/index.md" in result
    assert "approve_locked_scope" in result
    assert "final signoff is blocked" in result
    assert result.index("## index [reference]") < result.index("## log [reference]")


def test_real_arm_m0_min_wiki_query_finds_root_readme(monkeypatch) -> None:
    if not (PROJECT_ROOT / "arm_m0_min").is_dir():
        pytest.skip("arm_m0_min fixture IP is not present in this checkout")
    subprocess.run(
        [
            "python3",
            "workflow/wiki/build_graph.py",
            "--ip",
            "arm_m0_min",
            "--quiet",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("COMMON_AI_AGENT_HOME", raising=False)

    from core.tools import wiki_query

    result = wiki_query(ip="arm_m0_min", topic="readme cpu", depth=3)

    assert "matches=" in result
    assert "arm_m0_min/README.md" in result
    assert "root README entry point" in result


def test_project_wiki_query_finds_arm_m0_min_current_status(monkeypatch) -> None:
    subprocess.run(
        [
            "python3",
            "workflow/wiki/build_graph.py",
            "--quiet",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("COMMON_AI_AGENT_HOME", raising=False)

    from core.tools import wiki_query

    approval = wiki_query(topic="cpu approval req", depth=3, max_nodes=3)
    handoff = wiki_query(topic="arm m0 handoff", depth=3, max_nodes=3)
    readme = wiki_query(topic="readme cpu", depth=3, max_nodes=3)

    for result in (approval, handoff, readme):
        assert "arm-m0-min-current-status" in result
        assert "arm_m0_min/README.md" in result
        assert "approve_locked_scope" in result


def test_wiki_query_rebuilds_ip_graph_when_wiki_markdown_is_newer(
    tmp_path: Path, monkeypatch
) -> None:
    """A stale IP graph must refresh when an existing wiki markdown file changes."""
    ip = "demo_ip"
    wiki_dir = tmp_path / ip / "wiki"
    workflow_dir = tmp_path / "workflow" / "wiki"
    wiki_dir.mkdir(parents=True)
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "build_graph.py").symlink_to(PROJECT_ROOT / "workflow" / "wiki" / "build_graph.py")
    index_path = wiki_dir / "index.md"
    index_path.write_text("# Fresh Title\n\nfresh summary\n", encoding="utf-8")
    graph = {
        "schema_version": "ip_wiki_graph.v1",
        "node_count": 1,
        "edge_count": 0,
        "nodes": [
            {
                "id": "index",
                "title": "Old Title",
                "type": "reference",
                "path": "demo_ip/wiki/index.md",
                "summary": "old summary",
            }
        ],
    }
    graph_path = wiki_dir / "_graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    old_time = 1_700_000_000
    new_time = old_time + 100
    os.utime(graph_path, (old_time, old_time))
    os.utime(index_path, (new_time, new_time))
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("COMMON_AI_AGENT_HOME", raising=False)

    from core.tools import wiki_query

    result = wiki_query(ip=ip, topic="old", depth=3)

    assert "matches=0/" in result
    rebuilt = json.loads(graph_path.read_text(encoding="utf-8"))
    assert rebuilt["node_count"] >= 1
