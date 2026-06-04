# Compression LLM application — verification findings

Worktree: `verify/compression-llm-session` · repro: `scripts/verify_compression_llm.py`
Date: 2026-06-04

## User report
"compression 시 LLM 이 잘 적용이 안 되는 것 같아 / session 을 잘 못찾나?"

## Verdict
Confirmed. Two independent defects make compression silently run *without* the
LLM (or with the wrong model), while still reporting success.

---

### Finding 1 — LLM failure is silently swallowed and replaced with a raw truncation dump
`core/compressor.py`

- `_compress_single` (L948-961) and `_compress_chunked` (L1055-1070) wrap the
  `llm_call_fn(...)` in `try/except` and, on **any** exception, return a
  `"[Previous Conversation Summary (N messages, compression failed)]: <raw chars>"`
  built by char-truncating the messages (500 chars each). No re-raise.
- `compress_history` adds a 2nd swallow (L1593-1600, "LLM compression failed entirely").
- The history is still physically reduced (Test C: 121→4 msgs, "96% reduction"),
  and the web emit shows a cheerful `## Compression Summary … 96% reduction`, so it
  *looks* like compaction worked — but the summary body is non-LLM truncated text.

Repro (Test B): a failing LLM → output body =
`[Previous Conversation Summary (117 messages, compression failed)]: user: Task 0 …`
No exception propagates. Test A (healthy LLM) → body contains the real summary.

### Finding 2 — Web `/compact` does NOT use the session/per-workflow model
`src/atlas_compactor.py::_default_web_compress_fn` (used by `src/atlas_ui.py:5178`)

- It imports **process-global** `src.config` and calls raw
  `src.llm_client.chat_completion_stream` directly.
- It does **not** call `config.reload_env()` and does **not** wrap the call in
  `config.scoped_model_runtime(...)`.
- Contrast the worker path `core/agent_server.py::_llm_call_fn` (L1258-1297) which
  the worker's `_compress_fn` (L1300) reuses: it *does* scope model/key/base_url
  per run via `scoped_model_runtime(effective_model)`.

Consequence: web `/compact` summarizes with whatever model the **server process**
booted with (global `MODEL_NAME`), not the session's. If that global model/key is
wrong or unavailable for this process, every web compaction hits Finding 1 and
silently degrades to a truncation dump. The session *conversation file* is found
correctly (`_session_json_path`), but the *LLM config* is not session-derived.

Repro (Test D): `uses GLOBAL src.config = True`, `uses scoped_model_runtime = False`.

---

## Recommended fixes
1. **Stop silent degradation.** In `_compress_single`/`_compress_chunked`, on LLM
   failure either re-raise (let the web wrapper's `_compact_history_file` fallback
   own it, with a clear "AI summary unavailable: <err>" message that is already
   wired at `atlas_ui.py:5184`) or tag the result so callers can detect a
   non-LLM body. At minimum, surface the exception to the user instead of a
   success-looking "96% reduction".
2. **Scope the web compaction to the session model.** Have `_default_web_compress_fn`
   call `config.reload_env()` and wrap the compress call in
   `config.scoped_model_runtime(<session/effective model>)` — mirror the worker's
   `_llm_call_fn` — so `/compact` uses the same model the session runs on.

## How to reproduce
```
cd common_ai_agent
python3 scripts/verify_compression_llm.py
```

---

## Fixes applied (2026-06-04)

### Fix 1 — `core/compressor.py`
- Added `CompressionLLMError`, `_LLM_FAILURE_MARKERS`, `_summary_is_llm_fallback()`.
- `compress_history` gains `raise_on_llm_failure: bool = False`. After
  summarizing it now detects the swallowed-failure marker and: (a) inserts a
  `## ⚠️ AI Summary Unavailable` banner at the top of the emitted output so the
  "N% reduction" stats no longer read as success; (b) raises `CompressionLLMError`
  when the caller opts in. Inner `_compress_single`/`_compress_chunked` keep their
  graceful no-raise contract (CLI/worker loop still survives transient LLM errors;
  existing tests `TestChunkedErrorHandling` unchanged).

### Fix 2 — `src/atlas_compactor.py::_default_web_compress_fn`
- Calls `config.reload_env()` and wraps the compaction in
  `config.scoped_model_runtime(model or config.MODEL_NAME)` — the same thread-local
  switch the worker `_llm_call_fn` uses — so model/base_url/api_key move together.
- Passes `raise_on_llm_failure=True`, so a genuine LLM failure propagates through
  `_compact_history_llm` to `atlas_ui.py:5179`, which falls back to the
  deterministic compactor with an honest "(AI summary unavailable: …)".

## Verification (post-fix)
`python3 scripts/verify_compression_llm.py` →
```
A healthy-LLM summary applied      : yes
E FIX1 banner on swallowed failure : yes
F FIX2 web raises + scopes model   : yes  (CompressionLLMError raised, model scoped, _compact_history_llm propagates)
```
Regression: `pytest tests/test_core/test_compression_improvements.py tests/test_atlas_web_compact.py`
→ 27 passed, same 3 pre-existing failures as on unmodified `main` (verified by
running identical node-ids on the base tree; not introduced by these changes).
The pre-existing `test_websocket_compact_…` failure ("0 non-system messages") is a
separate `_session_json_path` resolution issue under the test's PROJECT_ROOT and is
out of scope here.

