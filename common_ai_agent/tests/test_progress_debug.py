from __future__ import annotations

import json
from pathlib import Path

from src.progress_debug import summarize_headless_progress


def _append_jsonl(path: Path, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, sort_keys=True) + "\n")


def test_progress_debug_reports_stuck_llm_call(tmp_path: Path) -> None:
    ip = "mini_cpu"
    root = tmp_path / "work"
    logs = root / ip / "logs"
    logs.mkdir(parents=True)
    (logs / "heartbeat.json").write_text(
        json.dumps(
            {
                "ts": "1970-01-01T00:00:01Z",
                "state": "running",
                "phase": "llm_call",
                "stage": "ssot-gen",
                "model": "deepseek",
                "pid": 123,
            }
        ),
        encoding="utf-8",
    )
    _append_jsonl(
        logs / "run_progress.jsonl",
        {"ts": "1970-01-01T00:00:00Z", "event": "stage_start", "stage": "ssot-gen"},
    )
    _append_jsonl(
        logs / "run_progress.jsonl",
        {
            "ts": "1970-01-01T00:00:01Z",
            "event": "llm_call_start",
            "stage": "ssot-gen",
            "log_stage": "ssot-gen",
            "model": "deepseek",
            "prompt_chars": 900,
            "system_prompt_chars": 100,
        },
    )

    summary = summarize_headless_progress(root, ip, now=301.0, stale_after_sec=120)

    assert summary["diagnosis"]["state"] == "stuck_llm_call"
    assert summary["diagnosis"]["severity"] == "warning"
    assert summary["current"]["stage"] == "ssot-gen"
    assert summary["current"]["pid"] == 123
    assert summary["llm"]["active"] is True
    assert summary["llm"]["elapsed_sec"] == 300.0
    assert summary["llm"]["open"] == 1
    assert summary["artifacts"]["ssot_yaml"]["exists"] is False
    assert len(summary["events_tail"]) == 2


def test_progress_debug_reports_finished_run(tmp_path: Path) -> None:
    ip = "timer_ip"
    root = tmp_path / "work"
    logs = root / ip / "logs"
    logs.mkdir(parents=True)
    (logs / "headless_run.json").write_text(
        json.dumps({"status": "pass", "stages": []}),
        encoding="utf-8",
    )
    (logs / "heartbeat.json").write_text(
        json.dumps({"ts": "1970-01-01T00:00:04Z", "state": "done", "status": "pass"}),
        encoding="utf-8",
    )
    _append_jsonl(
        logs / "run_progress.jsonl",
        {"ts": "1970-01-01T00:00:01Z", "event": "llm_call_start", "stage": "ssot-gen"},
    )
    _append_jsonl(
        logs / "run_progress.jsonl",
        {"ts": "1970-01-01T00:00:03Z", "event": "llm_call_end", "stage": "ssot-gen", "status": "pass"},
    )

    summary = summarize_headless_progress(root, ip, now=10.0, stale_after_sec=1)

    assert summary["diagnosis"]["state"] == "finished"
    assert summary["current"]["status"] == "pass"
    assert summary["llm"]["active"] is False
    assert summary["llm"]["started"] == 1
    assert summary["llm"]["finished"] == 1
    assert summary["artifacts"]["headless_run"]["exists"] is True
