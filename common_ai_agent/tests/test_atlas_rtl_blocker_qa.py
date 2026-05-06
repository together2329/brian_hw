import json
import os
import sys
from pathlib import Path


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_auto_rtl_blocker_records_deferred_ssot_qa_without_opening_question(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    ip = "dma330"
    rtl_dir = tmp_path / ip / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "rtl_blocked.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_blocker",
                "status": "blocked",
                "reason": "SSOT-derived dynamic RTL TODO gate is blocked.",
                "questions": [
                    {
                        "id": "RTL_DYNAMIC_TODO_OWNERSHIP",
                        "decision_needed": "Assign every SSOT-derived task to an RTL module owner.",
                        "evidence": "rtl/rtl_todo_plan.json orphans",
                        "orphan_refs": ["function_model.transactions.FM_DMAGO"],
                        "candidate_modules": [
                            {
                                "name": "dma330_engine",
                                "file": "rtl/dma330_engine.sv",
                                "refs": ["function_model.transactions.FM_DMAGO"],
                            }
                        ],
                        "required_fields": ["sub_modules[].function_model_refs"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    app = atlas_ui.create_app()

    handled = app.state.start_rtl_blocker_qna(
        ip,
        reason="automatic /ssot-rtl preflight",
        interactive=False,
    )

    assert handled is True
    assert app.state.atlas_bridge._pending_ask_user == {}
    qa_path = tmp_path / ".session" / ip / "ssot-gen" / "qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    assert len(qa["items"]) == 1
    item = qa["items"][0]
    assert item["source"] == "rtl-blocker"
    assert item["qa_type"] == "rtl_blocker"
    assert item["status_group"] == "pending"
    assert item["section_id"] == "04_architecture"
    assert item["decision_key"] == "rtl_dynamic_todo_ownership"
    assert item["field_path"] == "sub_modules"
    assert "function_model.transactions.FM_DMAGO" in item["source_refs"]
    assert any("orphan source_ref" in criterion for criterion in item["criteria"])


def test_rtl_blocker_qa_sections_target_scale_and_connection_contracts(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    ip = "dma330"
    rtl_dir = tmp_path / ip / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "rtl_blocked.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_blocker",
                "status": "blocked",
                "questions": [
                    {
                        "id": "RTL_TARGET_SCALE_POLICY",
                        "decision_needed": "Lock or waive RTL target-scale policy.",
                        "evidence": "rtl/rtl_todo_plan.json target_scale_policy gate",
                        "required_fields": ["quality_gates.rtl_gen.target_scale"],
                    },
                    {
                        "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
                        "decision_needed": "Resolve production multi-module connection contracts.",
                        "evidence": "integration.connections missing",
                        "required_fields": ["integration.connections"],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    app = atlas_ui.create_app()

    handled = app.state.start_rtl_blocker_qna(
        ip,
        reason="automatic /ssot-rtl preflight",
        interactive=False,
    )

    assert handled is True
    qa_path = tmp_path / ".session" / ip / "ssot-gen" / "qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    by_key = {item["decision_key"]: item for item in qa["items"]}
    assert by_key["rtl_target_scale_policy"]["section_id"] == "19_workflow_todos"
    assert by_key["rtl_target_scale_policy"]["field_path"] == "quality_gates.rtl_gen.target_scale"
    assert by_key["rtl_resolve_connection_contracts"]["section_id"] == "17_integration"
    assert by_key["rtl_resolve_connection_contracts"]["field_path"] == "integration.connections"


def test_rtl_impl_blocker_is_not_saved_as_ssot_qa_card(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    ip = "dma330"
    rtl_dir = tmp_path / ip / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "rtl_blocked.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "rtl_blocker",
                "status": "blocked",
                "questions": [
                    {
                        "id": "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
                        "decision_needed": "Prove common_ai_agent authored RTL.",
                        "evidence": "rtl/rtl_authoring_provenance.json missing",
                    },
                    {
                        "id": "RTL_TARGET_SCALE_POLICY",
                        "decision_needed": "Lock or waive RTL target-scale policy.",
                        "evidence": "rtl/rtl_todo_plan.json target_scale_policy gate",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    app = atlas_ui.create_app()

    handled = app.state.start_rtl_blocker_qna(
        ip,
        reason="automatic /ssot-rtl preflight",
        interactive=False,
    )

    assert handled is True
    qa_path = tmp_path / ".session" / ip / "ssot-gen" / "qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    keys = {item["decision_key"] for item in qa["items"]}
    assert keys == {"rtl_target_scale_policy"}
