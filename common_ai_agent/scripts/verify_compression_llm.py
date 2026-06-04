#!/usr/bin/env python3
"""verify_compression_llm.py — empirical check of compression LLM application.

Hypothesis under test (user report): "compression 시 LLM 이 잘 적용이 안 되는 것
같다 / session 을 잘 못찾나?" — during /compact the LLM summary does not seem to
be applied, possibly because the session is not resolved.

This harness exercises the *web* compaction path (the one ATLAS users hit) WITHOUT
network, by injecting controlled llm_call_fn / compress_fn stubs, and reports
exactly where the LLM summary is or is not applied.

Run from common_ai_agent/:  python3 scripts/verify_compression_llm.py
"""
from __future__ import annotations
import json, sys, tempfile, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import config  # noqa: E402
from core import compressor  # noqa: E402

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
INFO = "\033[36mINFO\033[0m"


def _make_history(n_pairs: int = 40) -> list[dict]:
    """A realistic ReAct-ish conversation big enough to cross the threshold."""
    msgs = [{"role": "system", "content": "You are a coding agent."}]
    for i in range(n_pairs):
        msgs.append({"role": "user", "content": f"Task {i}: edit core/file_{i}.py and run tests. " * 8})
        msgs.append({
            "role": "assistant", "content": "",
            "tool_calls": [{"id": f"c{i}", "type": "function",
                            "function": {"name": "write_file",
                                         "arguments": json.dumps({"path": f"core/file_{i}.py", "content": "x" * 50})}}],
        })
        msgs.append({"role": "tool", "tool_call_id": f"c{i}", "name": "write_file",
                     "content": f"wrote core/file_{i}.py ok; pytest: 3 passed " * 6})
    return msgs


def working_llm(messages, **kw):
    """A stub that behaves like a healthy summarizer LLM."""
    yield "## Working Context\n- CWD: /repo\n## Completed Work\n- edited core/file_0.py..file_39.py\n"


def failing_llm(messages, **kw):
    """A stub that simulates a broken/misconfigured LLM (bad key, wrong model)."""
    raise RuntimeError("HTTP 401 invalid api key (simulated)")
    yield ""  # pragma: no cover


def _summary_text(result: list[dict]) -> str:
    for m in result:
        c = str(m.get("content", ""))
        if "Summary" in c or "summary" in c:
            return c
    return ""


def main() -> int:
    failures = 0
    print(f"{INFO} config.MODEL_NAME = {getattr(config, 'MODEL_NAME', '?')}")
    print(f"{INFO} ENABLE_COMPRESSION = {getattr(config, 'ENABLE_COMPRESSION', '?')}")

    hist = _make_history()
    approx_tokens = sum(compressor._default_estimate(m) for m in hist)
    print(f"{INFO} built {len(hist)} messages (~{approx_tokens:,} est tokens), "
          f"MAX_CONTEXT_TOKENS={getattr(config,'MAX_CONTEXT_TOKENS','?')}")

    # ── Test A: healthy LLM → summary must contain LLM output, not raw dump ──
    res_a = compressor.compress_history(
        hist, force=True, cfg=config, llm_call_fn=working_llm, quiet=True,
    )
    sa = _summary_text(res_a)
    a_ok = "Completed Work" in sa and "compression failed" not in sa
    print(f"\n[A] healthy LLM  -> {'PASS' if a_ok else 'FAIL'}: summary applied={a_ok}")
    print(f"    summary head: {sa[:120]!r}")
    failures += 0 if a_ok else 1

    # ── Test B: broken LLM → does compress_history SWALLOW the failure? ──
    res_b = compressor.compress_history(
        hist, force=True, cfg=config, llm_call_fn=failing_llm, quiet=True,
    )
    sb = _summary_text(res_b)
    swallowed = "compression failed" in sb
    print(f"\n[B] broken LLM   -> {'SWALLOWED' if swallowed else 'raised/other'}")
    print(f"    summary head: {sb[:160]!r}")
    print(f"    {INFO} If SWALLOWED: outer caller sees a 'success' list whose body is")
    print(f"    {INFO} raw char-truncated messages — the LLM was NOT applied.")

    # ── Test C: web /compact wrapper reports success on a swallowed failure ──
    with tempfile.TemporaryDirectory() as td:
        conv = Path(td) / "conversation.json"
        conv.write_text(json.dumps(hist), encoding="utf-8")
        try:
            from src.atlas_compactor import _compact_history_llm
        except Exception:
            from atlas_compactor import _compact_history_llm  # type: ignore

        def broken_compress_fn(messages, **kwargs):
            kwargs.setdefault("quiet", True)
            return compressor.compress_history(
                messages, cfg=config, llm_call_fn=failing_llm, **kwargs,
            )

        msg, updated = _compact_history_llm(conv, "COMPACT_HISTORY", compress_fn=broken_compress_fn)
        body = _summary_text(updated)
        reports_success = "Compacted history with AI summary" in msg or "AI summary" in msg
        actually_llm = "compression failed" not in body and "Completed Work" in body
        print(f"\n[C] web /compact wrapper on broken LLM:")
        print(f"    user-facing message : {msg!r}")
        print(f"    reports AI summary? {reports_success} | body actually LLM? {actually_llm}")
        mismatch = reports_success and not actually_llm
        # NOTE: this stand-in compress_fn does NOT opt into raise_on_llm_failure,
        # so it models the CLI/worker (non-raising) path. Pre-fix that path was
        # silent; it is now covered by the Fix-1 warning banner (Test E). The
        # real web path opts in and raises instead (Test F).
        print(f"    -> {'non-raising path (now banner-covered, see E)' if mismatch else 'ok'}: "
              f"{'body is NON-LLM fallback' if mismatch else 'consistent'}")

    # ── Test D: does the web default fn scope to the session model? ──
    import inspect
    from src import atlas_compactor as _ac
    src_default = inspect.getsource(_ac._default_web_compress_fn)
    uses_global_cfg = "import src.config as _cfg" in src_default or "import config as _cfg" in src_default
    uses_scoped_model = "scoped_model_runtime" in src_default
    print(f"\n[D] _default_web_compress_fn session/model scoping:")
    print(f"    uses GLOBAL src.config       : {uses_global_cfg}")
    print(f"    uses scoped_model_runtime    : {uses_scoped_model}")
    print(f"    -> {INFO} web compaction runs on PROCESS-GLOBAL model/config, NOT the")
    print(f"       per-session/per-workflow model the worker uses (agent_server _llm_call_fn).")

    # ── Test E (FIX 1): non-raising failure now emits a visible warning banner ──
    emitted: list[str] = []
    compressor.compress_history(
        hist, force=True, cfg=config, llm_call_fn=failing_llm, quiet=True,
        emit_fn=lambda t: emitted.append(str(t or "")),
    )
    banner = "AI Summary Unavailable" in "".join(emitted)
    e_ok = banner
    print(f"\n[E] FIX1 warning banner on swallowed failure -> {'PASS' if e_ok else 'FAIL'}")
    failures += 0 if e_ok else 1

    # ── Test F (FIX 1+2): real web fn raises CompressionLLMError + scopes model ──
    import src.llm_client as _llm
    orig_stream = _llm.chat_completion_stream
    seen_scope = {}

    def _raising_stream(messages, **kw):
        seen_scope["thread_model"] = config.current_thread_model_runtime()
        raise RuntimeError("HTTP 401 invalid api key (simulated)")
        yield ""  # pragma: no cover

    _llm.chat_completion_stream = _raising_stream
    try:
        from src.atlas_compactor import _default_web_compress_fn, _compact_history_llm
        raised = False
        try:
            _default_web_compress_fn(hist, force=True, quiet=True)
        except compressor.CompressionLLMError:
            raised = True
        scoped = bool(seen_scope.get("thread_model"))  # scoped_model_runtime pushed an override
        print(f"\n[F] FIX2 web fn: raises CompressionLLMError={raised} | model-scoped during call={scoped}")
        f_ok = raised and scoped
        failures += 0 if f_ok else 1

        # And the web /compact wrapper PROPAGATES (so atlas_ui falls back honestly)
        with tempfile.TemporaryDirectory() as td2:
            conv2 = Path(td2) / "conversation.json"
            conv2.write_text(json.dumps(hist), encoding="utf-8")
            propagated = False
            try:
                _compact_history_llm(conv2, "COMPACT_HISTORY")  # uses real default fn
            except compressor.CompressionLLMError:
                propagated = True
            print(f"    _compact_history_llm propagates failure -> {propagated} "
                  f"(=> atlas_ui falls back to deterministic compactor)")
            failures += 0 if propagated else 1
    finally:
        _llm.chat_completion_stream = orig_stream

    print(f"\n{'='*60}\nSUMMARY")
    print(f"  A healthy-LLM summary applied      : {'yes' if a_ok else 'NO'}")
    print(f"  B broken-LLM failure swallowed     : {'yes' if swallowed else 'no'}")
    print(f"  D web path session-model scoped    : {'yes' if uses_scoped_model else 'NO (pre-fix snapshot)'}")
    print(f"  E FIX1 banner on swallowed failure : {'yes' if e_ok else 'NO'}")
    print(f"  F FIX2 web raises + scopes model   : {'yes' if f_ok else 'NO'}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
