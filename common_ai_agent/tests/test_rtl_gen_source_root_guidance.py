from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rtl_gen_prompt_allows_source_root_tooling_from_split_workspace():
    prompt = (ROOT / "workflow" / "rtl-gen" / "system_prompt.md").read_text(encoding="utf-8")

    assert "$ATLAS_SOURCE_ROOT/workflow/rtl-gen/scripts/derive_rtl_todos.py" in prompt
    assert "Do not ask the user to mount or copy `workflow/`" in prompt
    assert "ALLOWED TOOLING" in prompt
    assert "write IP artifacts only within the current working directory".lower() in prompt.lower()


def test_atlas_runtime_note_explains_workflow_source_root_exception():
    atlas_ui = (ROOT / "src" / "atlas_ui.py").read_text(encoding="utf-8")

    assert "$ATLAS_SOURCE_ROOT/workflow/..." in atlas_ui
    assert "do not ask the user to mount or copy workflow/" in atlas_ui
    assert "keep generated IP artifacts" in atlas_ui
