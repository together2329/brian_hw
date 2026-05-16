from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from atlas_ui import _atlas_todo_payload_from_raw  # noqa: E402


def test_atlas_todo_payload_accepts_dynamic_tasks_shape():
    payload = _atlas_todo_payload_from_raw(
        {
            "name": "Simple_Timer-rtl",
            "source_task_count": 1,
            "tasks": [
                {
                    "content": "RTL-0001: Read SSOT and build dynamic RTL implementation ledger",
                    "activeForm": "Reading SSOT ledger",
                    "status": "pending",
                    "priority": "critical",
                    "detail": "Use rtl_todo_plan.json.",
                    "criteria": "Ledger exists",
                }
            ],
        },
        {"todos": []},
    )

    assert payload["name"] == "Simple_Timer-rtl"
    assert payload["source_task_count"] == 1
    assert len(payload["todos"]) == 1
    assert payload["todos"][0]["activeForm"] == "Reading SSOT ledger"
    assert payload["todos"][0]["priority"] == "critical"


def test_atlas_todo_payload_accepts_legacy_list_shape():
    payload = _atlas_todo_payload_from_raw(
        [{"content": "Run lint", "status": "pending"}],
        {"todos": []},
    )

    assert payload["todos"] == [
        {
            "content": "Run lint",
            "activeForm": "Run lint",
            "status": "pending",
            "priority": "medium",
            "detail": "",
            "criteria": "",
        }
    ]
