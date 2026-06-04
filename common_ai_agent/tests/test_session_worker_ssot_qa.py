import json
import os
import sys
import threading
import time

import pytest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _qa_items(root, session):
    path = root / ".session" / session / "qa.json"
    return json.loads(path.read_text(encoding="utf-8"))["items"]


def _payload(row):
    raw = row.get("payload")
    if isinstance(raw, str):
        return json.loads(raw)
    return raw or {}


def test_session_worker_emits_tool_and_cost_events(tmp_path, monkeypatch):
    from core.session_worker import SessionWorker

    session = "brian/soc_ip/rtl-gen"
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("LLM_ACTIVE_MODEL_NAME", "soc-sol-gpt-5.4")
    monkeypatch.setenv("MODEL_NAME", "soc-sol-gpt-5.4")
    monkeypatch.setenv("LLM_ACTIVE_BASE_NAME", "glm-5.1")
    import config as config_module
    monkeypatch.setattr(config_module, "MODEL_NAME", "soc-sol-gpt-5.4", raising=False)
    worker = SessionWorker(session, str(tmp_path / "atlas.db"))
    try:
        worker.emit_tool("▶ read_file  soc_ip/rtl/top.sv")
        worker.emit_tool_result("read soc_ip/rtl/top.sv", "read_file")
        worker.emit_token_usage(1000, 100, 200)

        rows = worker.db.poll_messages(session, "out")
        by_type = {row.get("msg_type"): _payload(row) for row in rows}

        assert by_type["tool"]["text"].startswith("▶ read_file")
        assert by_type["tool_result"]["tool"] == "read_file"
        assert by_type["cost"]["model"] == "soc-sol-gpt-5.4"
        assert by_type["cost"]["pricing"]["input"] == 2.5
        assert by_type["cost"]["cost_usd_delta"] > 0
        assert by_type["token_usage"]["cost_usd_delta"] == by_type["cost"]["cost_usd_delta"]

        cost_file = tmp_path / ".session" / session / "cost.json"
        ledger = json.loads(cost_file.read_text(encoding="utf-8"))
        assert ledger["in_tok"] == 1000
        assert ledger["cache_tok"] == 100
        assert ledger["out_tok"] == 200
        assert ledger["cost_usd"] == by_type["cost"]["cost_usd_delta"]
    finally:
        worker.close()


def test_session_worker_rejects_path_traversal_session_id(tmp_path, monkeypatch):
    from core.session_worker import SessionWorker

    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))

    with pytest.raises(ValueError, match="invalid session path segment"):
        SessionWorker("alice/../bob/ip/ssot-gen", str(tmp_path / "atlas.db"))

    assert not (tmp_path / ".session" / "bob").exists()


def test_session_worker_idle_stop_does_not_cancel_next_prompt(tmp_path):
    from core.session_worker import SessionWorker

    session = "brian/dma/default"
    worker = SessionWorker(session, str(tmp_path / "atlas.db"))
    try:
        stale_stop = worker.db.enqueue_message(session, "in", "stop", {})
        worker.db.enqueue_message(session, "in", "prompt", {"text": "I need dma"})

        assert worker.input("> ") == "I need dma"
        assert worker.check_stop() is False

        rows = worker.db._fetchall(
            "SELECT delivered_at FROM session_queue WHERE id = ?",
            (stale_stop,),
        )
        assert rows[0]["delivered_at"] is not None
    finally:
        worker.close()


def test_session_worker_consumed_stop_marks_execution_paused(tmp_path, monkeypatch):
    from core.session_worker import SessionWorker

    session = "brian/dma/default"
    monkeypatch.delenv("ATLAS_EXECUTION_PAUSED_AFTER_STOP", raising=False)
    monkeypatch.delenv("ATLAS_EXECUTION_PAUSED_SESSION", raising=False)
    worker = SessionWorker(session, str(tmp_path / "atlas.db"))
    try:
        worker.db.enqueue_message(session, "in", "stop", {})

        assert worker.check_stop() is True
        assert os.environ["ATLAS_EXECUTION_PAUSED_AFTER_STOP"] == "1"
        assert os.environ["ATLAS_EXECUTION_PAUSED_SESSION"] == session
    finally:
        worker.close()


def test_session_worker_record_ssot_qa_writes_pending_review_card(tmp_path, monkeypatch):
    from core.session_worker import SessionWorker

    session = "brian/dma330/ssot-gen"
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    worker = SessionWorker(session, str(tmp_path / "atlas.db"))
    try:
        result = worker.record_ssot_qa(
            questions=[{
                "id": "burst_policy",
                "section_id": "03_interface",
                "decision_key": "burst_policy",
                "decision_label": "DMA burst policy",
                "question": "Which burst policy should DMA330 use?",
                "kind": "single",
                "options": [{"id": "fixed", "label": "Fixed"}],
            }],
            source="llm-ssot-qna",
        )

        assert "recorded 1 pending SSOT QA item" in result
        items = _qa_items(tmp_path, session)
        assert len(items) == 1
        assert items[0]["decision_key"] == "burst_policy"
        assert items[0]["status_group"] == "pending"
        assert items[0]["source"] == "llm-ssot-qna"
    finally:
        worker.close()


def test_session_worker_ask_user_moves_review_card_pending_to_approved(tmp_path, monkeypatch):
    from core.session_worker import SessionWorker

    session = "brian/dma330/ssot-gen"
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    worker = SessionWorker(session, str(tmp_path / "atlas.db"))
    try:
        result = {}

        def run_ask():
            result["text"] = worker.ask_user(
                "Which reset policy should DMA330 use?",
                [{"id": "sync", "label": "Synchronous"}],
                "single",
                "§2 reset policy",
                questions=[{
                    "id": "reset_policy",
                    "section_id": "02_clock_reset",
                    "decision_key": "reset_policy",
                    "decision_label": "Reset policy",
                    "question": "Which reset policy should DMA330 use?",
                    "kind": "single",
                    "options": [{"id": "sync", "label": "Synchronous"}],
                }],
            )

        thread = threading.Thread(target=run_ask)
        thread.start()
        flow_id = ""
        deadline = time.time() + 3
        while time.time() < deadline and not flow_id:
            rows = worker.db.poll_messages(session, "out")
            for row in rows:
                if row.get("msg_type") == "ask_user":
                    flow_id = _payload(row).get("flow_id") or ""
                    break
            if not flow_id:
                time.sleep(0.05)
        assert flow_id
        assert _qa_items(tmp_path, session)[0]["status_group"] == "pending"

        worker.db.enqueue_message(
            session,
            "in",
            "answer",
            {"flow_id": flow_id, "selected": ["sync"], "custom": ""},
        )
        thread.join(timeout=3)
        assert not thread.is_alive()

        item = _qa_items(tmp_path, session)[0]
        assert item["status_group"] == "approved"
        assert item["answer"] == "Synchronous"
        assert "selected: Synchronous" in result["text"]
    finally:
        worker.close()


def test_session_worker_auto_select_approves_review_card_without_modal(tmp_path, monkeypatch):
    from core.session_worker import SessionWorker

    session = "brian/timer_auto/ssot-gen"
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ASK_USER_EXEC_MODE", "auto-select")
    worker = SessionWorker(session, str(tmp_path / "atlas.db"))
    try:
        text = worker.ask_user(
            "Which reset policy should timer_auto use?",
            [
                {"id": "async_sync", "label": "Async assert, sync deassert (Recommended)"},
                {"id": "sync", "label": "Fully synchronous"},
            ],
            "single",
            "§2 reset policy. Suggest: Async assert, sync deassert",
            questions=[{
                "id": "reset_policy",
                "section_id": "02_clock_reset",
                "decision_key": "reset_policy",
                "decision_label": "Reset policy",
                "question": "Which reset policy should timer_auto use?",
                "kind": "single",
                "subtitle": "§2 reset policy. Suggest: Async assert, sync deassert",
                "options": [
                    {"id": "async_sync", "label": "Async assert, sync deassert (Recommended)"},
                    {"id": "sync", "label": "Fully synchronous"},
                ],
            }],
        )

        assert "Auto" not in text  # SessionWorker returns the normal answer format.
        assert "selected: Async assert, sync deassert" in text
        items = _qa_items(tmp_path, session)
        assert len(items) == 1
        assert items[0]["status_group"] == "approved"
        assert items[0]["source"] == "llm-ssot-qna.auto_select"
        assert items[0]["answer"] == "Async assert, sync deassert (Recommended)"
        out_rows = worker.db.poll_messages(session, "out")
        assert any(row.get("msg_type") == "ask_user_auto_selected" for row in out_rows)
        assert not any(row.get("msg_type") == "ask_user" for row in out_rows)
    finally:
        worker.close()
