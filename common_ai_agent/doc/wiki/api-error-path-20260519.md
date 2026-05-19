# API Error Path Negative-Test Matrix — 2026-05-19

Cross-link: [[atlas-pipeline-screen]]

Tested against `http://127.0.0.1:62196`. Auth cookie: `/tmp/atlas_cookies_v2.txt`.

## Results

| # | Endpoint | Input | Expected | Actual | Status |
|---|----------|-------|----------|--------|--------|
| 1 | `POST /api/pipeline/dispatch` | No auth, `{}` | 401 `login required` | `{"detail":"login required"}` 401 | PASS |
| 2 | `POST /api/pipeline/dispatch` | Auth, `{"ip":"../etc/passwd","stages":["ssot"]}` | 400 | `{"error":"invalid ip '../etc/passwd'"}` 400 | PASS |
| 3 | `POST /api/pipeline/orchestrator/chat` | Auth, `{"ip":"x","message":""}` | 400 | `{"error":"message required"}` 400 | PASS |
| 4 | `POST /api/pipeline/dispatch` | Auth, `prompt` = 200 KB base64 (~267 K chars) | 413 or 400 | 200 `ok:true` (pipeline dispatched) | **FAIL — BUG** |
| 5 | `POST /api/pipeline/dispatch` | Auth, `{"ip":"x","stages":["not-a-real-workflow"]}` | 400 | `{"error":"unknown pipeline stage 'not-a-real-workflow'"}` 400 | PASS |
| 6 | `GET /api/orchestrator/chat/messages` | Auth, no `ip` param | 400 | `{"error":"ip param missing or invalid"}` 400 | PASS |
| 7 | `GET /api/orchestrator/active_run?ip=` | Auth, empty `ip` | 400 | `{"error":"ip query param required"}` 400 | PASS |

**Score: 6/7 PASS**

## Bug Report — Test 4: No prompt size limit on `/api/pipeline/dispatch`

**Symptom:** A 267 K-character base64 prompt was accepted and dispatched as a real pipeline job (HTTP 200, `pipeline_id` assigned, worker started). No size guard existed.

**Root cause:** `api_pipeline_dispatch` in `src/atlas_api_jobs.py` validates `ip`, `schedule`, `rtl_version_id`, `run_mode`, `exec_mode`, and `stages`, but had no upper bound on `prompt` length.

**Fix applied** (`src/atlas_api_jobs.py:3332`):
```python
if len(user_prompt) > 100_000:
    return JSONResponse({"error": "prompt too large (max 100 000 chars)"}, status_code=400)
```

Inserted after the `exec_mode` guard, before the `stages` resolution block. The fix is written to disk; the server requires a restart to activate it (no auto-reload).

**Note on test 3:** The task brief referenced `/api/orchestrator/chat` which returns 405 (route does not exist as POST). The correct endpoint is `/api/pipeline/orchestrator/chat`. Test re-run against correct URL returned 400 as expected.
