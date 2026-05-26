"""Per-IP workflow scaffold + configurable wiki pointers.

Covers the .config-driven wiki pointing (ATLAS_WIKI_ROOT / ATLAS_RTL_DB_WIKI)
and scaffold_ip's per-IP workflow-script copy + execution runbook.
"""

from pathlib import Path

import pytest

import core.tools as tools
from core.tools import (
    resolve_project_wiki_root,
    resolve_rtl_db_wiki,
    scaffold_ip,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_resolve_project_wiki_root_derives_from_workflow_root(tmp_path, monkeypatch):
    # The dev wiki is the sibling of the workflow tree (--workflow-root) — no
    # dedicated env var.
    monkeypatch.delenv("COMMON_AI_AGENT_HOME", raising=False)
    src = tmp_path / "src"
    (src / "workflow").mkdir(parents=True)
    (src / "doc" / "wiki").mkdir(parents=True)
    monkeypatch.setenv("ATLAS_WORKFLOW_ROOT", str(src / "workflow"))
    assert resolve_project_wiki_root(tmp_path / "elsewhere") == (src / "doc" / "wiki").resolve()

    # Fallback: when no doc/wiki sits beside the workflow root, use
    # <project_root>/doc/wiki.
    src2 = tmp_path / "src2"
    (src2 / "workflow").mkdir(parents=True)
    monkeypatch.setenv("ATLAS_WORKFLOW_ROOT", str(src2 / "workflow"))
    proj = tmp_path / "proj"
    (proj / "doc" / "wiki").mkdir(parents=True)
    assert resolve_project_wiki_root(proj) == (proj / "doc" / "wiki").resolve()


def test_resolve_rtl_db_wiki_pointer(tmp_path, monkeypatch):
    monkeypatch.delenv("ATLAS_RTL_DB_WIKI", raising=False)
    assert resolve_rtl_db_wiki() is None

    # Non-existent path → None (no dangling link).
    monkeypatch.setenv("ATLAS_RTL_DB_WIKI", str(tmp_path / "nope.md"))
    assert resolve_rtl_db_wiki() is None

    # Existing path → returned.
    wiki = tmp_path / "legacy_rtl.md"
    wiki.write_text("# prior project RTL\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_RTL_DB_WIKI", str(wiki))
    assert resolve_rtl_db_wiki() == wiki


def test_scaffold_ip_writes_per_ip_workflow_and_runbook(tmp_path, monkeypatch):
    # Point the central workflow tree at the real repo so stages copy.
    monkeypatch.setenv("COMMON_AI_AGENT_HOME", str(REPO_ROOT))
    monkeypatch.delenv("ATLAS_WORKFLOW_ROOT", raising=False)
    rtl_db = tmp_path / "prev_rtl.md"
    rtl_db.write_text("# previous project RTL DB\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_RTL_DB_WIKI", str(rtl_db))

    out = scaffold_ip("widget", root=str(tmp_path))
    assert "Scaffolded IP 'widget'" in out

    ip = tmp_path / "widget"
    # The WHOLE workflow tree is copied so the IP runs on its own: stages,
    # the shared scripts/+prompts/, and the flow guides.
    for stage in ("ssot-gen", "fl-model-gen", "rtl-gen", "tb-gen", "sim", "lint"):
        assert (ip / "workflow" / stage).is_dir(), stage
    assert (ip / "workflow" / "GUIDE.md").is_file()
    assert (ip / "workflow" / "scripts").is_dir()
    # Prompts / system prompts come along (usable standalone).
    assert (ip / "workflow" / "tb-gen" / "system_prompt.md").is_file()
    # __pycache__ is not copied.
    assert not list((ip / "workflow").rglob("__pycache__"))

    runbook = ip / "wiki" / "workflow-runbook.md"
    assert runbook.is_file()
    text = runbook.read_text(encoding="utf-8")
    assert "widget — Workflow Runbook" in text
    assert "SSOT → FL-Model → RTL → TB → SIM → LINT" in text
    # Self-contained: the runbook must NOT depend on the central doc/wiki.
    assert "doc/wiki" not in text
    # The only external link is the previous-project RTL DB.
    assert str(rtl_db) in text
    # The runbook points into the per-IP knowledge graph.
    assert "[[workflow-stages]]" in text

    # Knowledge-graph pages are copied FLAT into <ip>/wiki/ (build_graph globs
    # non-recursively) so wiki_query(ip) surfaces them.
    assert (ip / "wiki" / "workflow-stages.md").is_file()   # knowledge index
    for stage in ("ssot-gen", "rtl-gen", "lint", "sim"):
        assert (ip / "wiki" / f"{stage}.md").is_file(), stage
    # The knowledge index is workflow-stages.md, NOT index.md — so it can't
    # collide with the ssot-gen-seeded <ip>/wiki/index.md.
    assert not (ip / "wiki" / "index.md").exists()
    # ip_knowledge is NOT duplicated inside the wholesale <ip>/workflow/ copy.
    assert not (ip / "workflow" / "wiki" / "ip_knowledge").exists()


def test_scaffold_ip_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("COMMON_AI_AGENT_HOME", str(REPO_ROOT))
    scaffold_ip("again", root=str(tmp_path))
    out2 = scaffold_ip("again", root=str(tmp_path))
    # Second run preserves everything (nothing created, runbook kept).
    assert "kept (already existed)" in out2
    assert "workflow-runbook.md" in out2
