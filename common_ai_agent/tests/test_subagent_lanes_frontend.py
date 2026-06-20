"""Content gate for the codex `/subagent` left-rail lanes frontend.

Reads the workspace frontend sources (no DOM) and asserts the structural wiring
that surfaces codex subagents as a left workflow-panel picker: the presentational
component, the data-hook `subagent` subscription + Main-on-top lane model, and
the left-rail mount. The behavioral DOM assertions live in the vitest sibling
``frontend/atlas/__tests__/workspace-subagent-lanes.test.tsx``.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FE = PROJECT_ROOT / "frontend" / "atlas"


def _read(rel: str) -> str:
    return (FE / rel).read_text(encoding="utf-8")


def test_subagent_lanes_component_renders_picker():
    src = _read("workspace-subagent-lanes.tsx")
    assert "export const SubagentLanes" in src
    # Main-on-top + default marker + click-to-select contract (mirrors codex CLI).
    assert "isMain" in src
    assert "[default]" in src
    assert "onSelect" in src
    # each row shows the codex thread id (uuid).
    assert "lane.agentId" in src
    # only surfaces once a subagent exists (Main-only -> null).
    assert "subCount" in src
    assert "return null" in src


def test_data_hook_subscribes_subagent_and_builds_main_first_lanes():
    src = _read("workspace-root-data-hook.tsx")
    assert "subscribe('subagent'" in src
    assert "setSubagentLanes" in src
    # Main row synthesized from the parent thread id, ordered main-first.
    assert "isMain: true" in src
    assert "subagentLanes: subagentLanesArr" in src
    assert "selectedSubagentId" in src


def test_left_rail_mounts_subagent_lanes():
    src = _read("workspace-rootui-rail-tabs.tsx")
    assert "import { SubagentLanes }" in src
    assert "<SubagentLanes" in src
    assert "selectedId={selectedSubagentId}" in src
    assert "onSelect={setSelectedSubagentId}" in src
