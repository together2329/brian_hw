import json
import os
import sys
import threading
import time


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
