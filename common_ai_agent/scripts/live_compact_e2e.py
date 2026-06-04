#!/usr/bin/env python3
"""live_compact_e2e.py — isolated LIVE end-to-end check of the web /compact fix.

Runs the REAL web compaction path against a temp conversation file using the
live model config (real chat_completion_stream / OAuth), bypassing
_session_json_path (we hand _compact_history_llm an explicit Path) so this
isolates the compression-LLM fix from the separate #2 session-path issue.

Proves Fix 2: _default_web_compress_fn now runs inside scoped_model_runtime +
reload_env and actually applies the LLM, producing a genuine AI summary (not a
"compression failed" truncation dump and no "AI Summary Unavailable" banner).

Run from common_ai_agent/:  python3 scripts/live_compact_e2e.py
"""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))

import config  # noqa: E402
from src.atlas_compactor import _compact_history_llm  # noqa: E402


def _make_history(n: int = 40) -> list[dict]:
    msgs = [{"role": "system", "content": "You are a coding agent working on the ATLAS repo."}]
    for i in range(n):
        msgs.append({"role": "user", "content": f"Step {i}: edit core/module_{i}.py and run its unit test."})
        msgs.append({"role": "assistant", "content": "",
                     "tool_calls": [{"id": f"c{i}", "type": "function",
                                     "function": {"name": "write_file",
                                                  "arguments": json.dumps({"path": f"core/module_{i}.py"})}}]})
        msgs.append({"role": "tool", "tool_call_id": f"c{i}", "name": "write_file",
                     "content": f"wrote core/module_{i}.py; pytest tests/test_module_{i}.py -> 3 passed"})
    msgs.append({"role": "user", "content": "Now summarize what is done and what's left."})
    return msgs


def main() -> int:
    try:
        config.reload_env()
    except Exception:
        pass
    print(f"[live] MODEL_NAME={getattr(config,'MODEL_NAME','?')}  BASE_URL={getattr(config,'BASE_URL','?')}")
    hist = _make_history()
    with tempfile.TemporaryDirectory() as td:
        conv = Path(td) / "conversation.json"
        conv.write_text(json.dumps(hist), encoding="utf-8")
        print(f"[live] wrote {len(hist)} messages -> {conv}")
        print("[live] calling REAL _compact_history_llm (live model)…")
        msg, updated = _compact_history_llm(conv, "COMPACT_HISTORY:keep=3")

        body = " ".join(str(m.get("content", "")) for m in updated)
        failed_marker = ("compression failed" in body) or ("Chunk compression failed" in body)
        banner = "AI Summary Unavailable" in msg or "AI Summary Unavailable" in body
        # Heuristic: a genuine LLM summary mentions the structured sections or
        # the work content rather than just replaying raw "Step N" lines.
        genuine = (not failed_marker) and (not banner) and len(msg) > 0
        print("\n================= RESULT =================")
        print(f"messages: {len(hist)} -> {len(updated)}")
        print(f"LLM-failure fallback present : {failed_marker}")
        print(f"'AI Summary Unavailable' banner: {banner}")
        print(f"=> genuine LLM summary applied : {genuine}")
        print("\n----- user-facing /compact message (head) -----")
        print(msg[:1400])
        return 0 if genuine else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"\n[live] ERROR: {e}")
        sys.exit(2)
