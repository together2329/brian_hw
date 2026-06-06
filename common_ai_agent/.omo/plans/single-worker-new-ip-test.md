# Single Worker New IP Test

## TL;DR
> Summary:      Test exactly one fresh IP through the product single-active session-worker path with `exec_mode=single-worker` and `workflow=default`, using an isolated ATLAS root and captured HTTP/UI/WS/signoff evidence. If the live worker or signoff path blocks, classify the first blocker instead of editing generated artifacts.
> Deliverables:
> - Isolated runtime evidence for single-active `single-worker/default` mode
> - UI plus HTTP evidence for session creation, activation, and one fresh IP scaffold
> - Default-workflow WebSocket prompt evidence, or first request blocker classification
> - Contract/signoff evidence, or first contract/signoff blocker classification
> Effort:       Short
> Risk:         Medium - live worker response can depend on local model/API/runtime availability

## Scope
### Must have
- Use a temp ATLAS root so the fresh IP scaffold is isolated from the checked-out repo.
- Force product mode to `ATLAS_EXEC_MODE=single-worker`, `ATLAS_DEFAULT_EXEC_MODE=single-worker`, `ATLAS_SESSION_WORKER_POLICY=single-active-owner`, and `workflow=default`.
- Prove new session and activation through HTTP endpoints.
- Prove new IP creation through the UI `+ IP` modal and the backing `/api/ip/create` response.
- Prove request submission through `/ws/agent` using the same fresh IP and `workflow=default`.
- Run contract/signoff validators against the fresh IP and record pass or first blocker.
- Keep all evidence under `.omo/evidence/`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not use orchestrator mode for the tested request.
- Do not use `/api/job/dispatch`, `/api/jobs/dispatch_many`, or orchestrator chat as the request path.
- Do not manually edit generated IP artifacts such as `.session/`, `sim/`, `verify/`, `cov/`, or `lint/*.json|log`; `.cursor/hooks/protect-generated-artifacts.py:9-20` defines these as generated/runtime paths.
- Do not edit product source code or add persistent test harness files.
- Do not treat `worker_warmup` as proof of request execution; use WS frames (`agent_received`, `agent_accepted`, and output/running) for request evidence.
- Do not require final signoff to pass on a scaffold-only IP; classify the first blocker when validators fail.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + pytest, curl/Python HTTP, Playwright real Chrome, and Node WebSocket checks
- QA policy: every task has agent-executed scenarios
- Evidence: `.omo/evidence/task-<N>-single-worker-new-ip-test.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Create isolated runtime fixture and evidence env
- Task 2: Preflight dependencies and guardrail references
- Task 3: Run focused existing regressions

Wave 2 (after Wave 1):
- Task 4: depends [1, 2]

Wave 3 (after Wave 2):
- Task 5: depends [4]

Wave 4 (after Wave 3):
- Task 6: depends [5]

Wave 5 (after Wave 4):
- Task 7: depends [6]
- Task 8: depends [6]

Critical path: Task 1 -> Task 4 -> Task 5 -> Task 6 -> Task 7

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 4      | 2, 3                 |
| 2    | none       | 4      | 1, 3                 |
| 3    | none       | F2     | 1, 2                 |
| 4    | 1, 2       | 5      | none                 |
| 5    | 4          | 6      | none                 |
| 6    | 5          | 7, 8   | none                 |
| 7    | 6          | F3     | 8                    |
| 8    | 6          | F3     | 7                    |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Create isolated runtime fixture and evidence env

  What to do: Create `.omo/evidence/`, generate a unique tag/user/IP, allocate a free local port, create a temp ATLAS root, and write `.omo/evidence/task-1-single-worker-new-ip-test.env` for later tasks.
  Must NOT do: Do not create the fresh IP under the repository root. Do not start the server in this task.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `src/atlas_runtime_run.py:1008-1011` - `--root` controls the backend project root.
  - Pattern:  `src/atlas_runtime_run.py:1126-1128` - runtime exports `ATLAS_ROOT`, `ATLAS_PROJECT_ROOT`, and `ATLAS_WORKFLOW_ROOT`.
  - Pattern:  `src/atlas_runtime_run.py:1135-1156` - canonical launch session is `<owner>/<workspace_session>/<ip>/<workflow>`.
  - Test:     `tests/test_atlas_multiuser_session_scope.py:1765` - IP create tests use temp roots to avoid persistent repo pollution.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f .omo/evidence/task-1-single-worker-new-ip-test.env`
  - [ ] `source .omo/evidence/task-1-single-worker-new-ip-test.env && test -d "$ATLAS_E2E_ROOT" && test "$ATLAS_E2E_WORKFLOW" = "default" && test "$ATLAS_E2E_EXEC_MODE" = "single-worker"`
  - [ ] `source .omo/evidence/task-1-single-worker-new-ip-test.env && test ! -e "$REPO/$ATLAS_E2E_IP"`

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: fixture env exists and points to temp root
    Tool:     bash
    Steps:    mkdir -p .omo/evidence && TAG="swnewip$(date +%s)" && PORT="$(python3 - <<'PY'
import socket
s=socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
)" && ROOT="$(mktemp -d "${TMPDIR:-/tmp}/atlas-single-worker-root.XXXXXX")" && REPO="$(pwd)" && USER_NAME="swuser_${TAG}" && IP_NAME="ip_${TAG}" && PASS_VALUE="${USER_NAME}_pw123456" && mkdir -p "$ROOT/.atlas" && cat > .omo/evidence/task-1-single-worker-new-ip-test.env <<EOF
REPO=$REPO
ATLAS_E2E_ROOT=$ROOT
ATLAS_E2E_PORT=$PORT
ATLAS_E2E_BASE=http://127.0.0.1:$PORT
ATLAS_E2E_TAG=$TAG
ATLAS_E2E_USER=$USER_NAME
ATLAS_E2E_PASS=$PASS_VALUE
ATLAS_E2E_IP=$IP_NAME
ATLAS_E2E_WORKFLOW=default
ATLAS_E2E_EXEC_MODE=single-worker
ATLAS_E2E_COOKIE=.omo/evidence/task-5-single-worker-new-ip-test.cookie
EOF
    Expected: `.omo/evidence/task-1-single-worker-new-ip-test.env` exists, `$ATLAS_E2E_ROOT` is a temp directory, and `$REPO/$ATLAS_E2E_IP` does not exist.
    Evidence: .omo/evidence/task-1-single-worker-new-ip-test.env

  Scenario: fixture rejects accidental repo-root scaffold target
    Tool:     bash
    Steps:    source .omo/evidence/task-1-single-worker-new-ip-test.env && if [ -e "$REPO/$ATLAS_E2E_IP" ]; then echo "repo IP already exists"; exit 1; fi
    Expected: Command exits 0 and prints nothing.
    Evidence: .omo/evidence/task-1-single-worker-new-ip-test-root-check.txt
  ```

  Commit: NO | Message: `test(single-worker): prepare isolated new-ip fixture` | Files: [.omo/evidence/task-1-single-worker-new-ip-test.env]

- [ ] 2. Preflight dependencies and generated-artifact guardrails

  What to do: Verify required scripts, route modules, Node dependencies, frontend bundle, and generated-artifact guardrail files exist before the live flow runs.
  Must NOT do: Do not run the product flow or create the IP. Do not edit generated artifacts.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.cursor/hooks/protect-generated-artifacts.py:9-20` - generated/runtime artifacts protected from manual edits.
  - Pattern:  `frontend/atlas/app.tsx:166-171` - new IP initial workflow is `default` unless exec mode is orchestrator.
  - Pattern:  `frontend/atlas/app.tsx:815-826` - UI sends `name`, `kind`, `exec_mode`, `workflow`, `workspace_session`, and `session_id` to `/api/ip/create`.
  - Pattern:  `frontend/atlas/data-helpers.tsx:18-24` - `DEFAULT_WORKFLOW` and default flow stage.
  - Pattern:  `frontend/atlas/data-helpers.tsx:64-73` - single-worker mode leads with the general-purpose `default` workflow.
  - Test:     `scripts/run_tests.sh:4-18` - repo test wrapper modes.
  - Test:     `scripts/atlas_vite_e2e_realuser.mjs:108-149` - existing UI `+ IP` selector pattern.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f .cursor/hooks/protect-generated-artifacts.py`
  - [ ] `test -f frontend/atlas/dist/index.html || (cd frontend/atlas && npm run build)`
  - [ ] `node -e "require.resolve('playwright')"`
  - [ ] `node -e "const path=require('node:path'); require(path.resolve('frontend/atlas/node_modules/ws'))"`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: required local dependencies and files exist
    Tool:     bash
    Steps:    set -euo pipefail; mkdir -p .omo/evidence; for f in src/atlas_ui.py src/atlas_api_sessions.py src/atlas_api_chat.py src/atlas_api_jobs.py workflow/ssot-gen/scripts/check_ssot_disk.sh workflow/ssot-gen/scripts/verify_ssot.py workflow/ip-contract/scripts/derive_ip_contract.py workflow/signoff/scripts/check_ip_signoff.py .cursor/hooks/protect-generated-artifacts.py; do test -f "$f"; done; test -f frontend/atlas/dist/index.html || (cd frontend/atlas && npm run build); node -e "require.resolve('playwright')"; node -e "const path=require('node:path'); require(path.resolve('frontend/atlas/node_modules/ws'))"; echo "preflight ok" | tee .omo/evidence/task-2-single-worker-new-ip-test.txt
    Expected: Command exits 0 and evidence contains `preflight ok`.
    Evidence: .omo/evidence/task-2-single-worker-new-ip-test.txt

  Scenario: guardrail patterns include generated IP artifact paths
    Tool:     bash
    Steps:    python3 - <<'PY' | tee .omo/evidence/task-2-single-worker-new-ip-test-guardrail.json
import json
from pathlib import Path
text = Path(".cursor/hooks/protect-generated-artifacts.py").read_text(encoding="utf-8")
required = [r"(^|/)\\.session/", r"(^|/)sim/.*", r"(^|/)verify/", r"(^|/)cov/", r"(^|/)lint/.*"]
missing = [item for item in required if item not in text]
print(json.dumps({"missing": missing, "ok": not missing}, indent=2))
raise SystemExit(0 if not missing else 1)
PY
    Expected: JSON has `"ok": true`.
    Evidence: .omo/evidence/task-2-single-worker-new-ip-test-guardrail.json
  ```

  Commit: NO | Message: `test(single-worker): verify preflight guardrails` | Files: [.omo/evidence/task-2-single-worker-new-ip-test.txt]

- [ ] 3. Run focused existing regressions

  What to do: Run focused existing pytest coverage for IP creation and strict single-active worker status. These are not a replacement for the live product test; they are a fast regression backstop.
  Must NOT do: Do not run live LLM suites or broad full-suite tests unless the focused tests fail in a way that requires deeper diagnosis.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [F2] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Test:     `tests/test_atlas_multiuser_session_scope.py:1765` - creates a workspace-scoped IP, asserts session `alice/default/gpio/default`, scaffold YAML, catalog row, and duplicate 409.
  - Test:     `tests/test_session_worker_e2e.py:1-7` - tests real HTTP path for auth, activation, and worker status with only the leaf process manager faked.
  - Test:     `tests/test_session_worker_e2e.py:75-107` - strict switch isolation and user-scoped status assertions.
  - Test:     `scripts/run_tests.sh:48-73` - quick mode excludes live LLM suites.

  Acceptance criteria (agent-executable only):
  - [ ] `python3 -m pytest tests/test_atlas_multiuser_session_scope.py::test_ip_create_endpoint_scaffolds_once_and_rejects_duplicate tests/test_session_worker_e2e.py::test_e2e_strict_switch_isolation_and_status -q --tb=short` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: focused happy-path regressions pass
    Tool:     bash
    Steps:    set -o pipefail; python3 -m pytest tests/test_atlas_multiuser_session_scope.py::test_ip_create_endpoint_scaffolds_once_and_rejects_duplicate tests/test_session_worker_e2e.py::test_e2e_strict_switch_isolation_and_status -q --tb=short | tee .omo/evidence/task-3-single-worker-new-ip-test.txt
    Expected: Pytest exits 0.
    Evidence: .omo/evidence/task-3-single-worker-new-ip-test.txt

  Scenario: focused edge regression for symlink workspace rejection passes
    Tool:     bash
    Steps:    set -o pipefail; python3 -m pytest tests/test_atlas_multiuser_session_scope.py::test_ip_create_rejects_workspace_session_symlink_in_multiuser_mode -q --tb=short | tee .omo/evidence/task-3-single-worker-new-ip-test-error.txt
    Expected: Pytest exits 0.
    Evidence: .omo/evidence/task-3-single-worker-new-ip-test-error.txt
  ```

  Commit: NO | Message: `test(single-worker): run focused strict-worker regressions` | Files: [.omo/evidence/task-3-single-worker-new-ip-test.txt]

- [ ] 4. Start isolated single-active single-worker server

  What to do: Start `src/atlas_ui.py` on the allocated port using the isolated root, single-worker exec mode, strict single-active policy, and default workflow. Capture `/healthz` and `/api/pipeline/run_policy`.
  Must NOT do: Do not set orchestrator mode. Do not use a repo-root `--root`.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [5] | Blocked by: [1, 2]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `src/atlas_runtime_run.py:999-1049` - CLI flags for port, root, workflow root, session, workspace session, IP, workflow, and exec mode.
  - Pattern:  `src/atlas_runtime_run.py:1051-1060` - `--exec` normalizes and pins `ATLAS_EXEC_MODE`.
  - Pattern:  `src/atlas_runtime_run.py:1097-1128` - `--root` mutates the runtime project root and exports it.
  - Pattern:  `src/atlas_runtime_run.py:1157-1183` - orchestrator-specific runtime is only configured when current exec mode is orchestrator.
  - API/Type: `src/atlas_ui.py:1947-1964` - `/healthz` returns server readiness and user/session fields.
  - API/Type: `src/atlas_api_jobs.py:8024-8044` - `/api/pipeline/run_policy` returns `exec_mode`, `initial_workflow`, and worker policy fields.
  - Pattern:  `doc/wiki/atlas-single-active-orchestrator-subworkers-20260603.md:41-66` - strict policy variables and compatibility flags.
  - Pattern:  `doc/wiki/atlas-single-active-orchestrator-subworkers-20260603.md:74-77` - interactive session workers are separate from orchestrator workflow/job workers.

  Acceptance criteria (agent-executable only):
  - [ ] `.omo/evidence/task-4-single-worker-new-ip-test-healthz.json` has `"ok": true`.
  - [ ] `.omo/evidence/task-4-single-worker-new-ip-test-run-policy.json` has `"exec_mode": "single-worker"`, `"orchestrator_enabled": false`, and `"initial_workflow": "default"`.
  - [ ] `.omo/evidence/task-4-single-worker-new-ip-test-server.pid` contains a live PID after startup.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: server starts in single-worker/default mode
    Tool:     bash
    Steps:    set -euo pipefail; set -a; source .omo/evidence/task-1-single-worker-new-ip-test.env; set +a; ATLAS_DB_PATH="$ATLAS_E2E_ROOT/.atlas/atlas.db" ATLAS_ROOT="$ATLAS_E2E_ROOT" ATLAS_PROJECT_ROOT="$ATLAS_E2E_ROOT" ATLAS_WORKFLOW_ROOT="$REPO/workflow" ATLAS_FRONTEND_MODE=vite ATLAS_MULTI_USER=1 ATLAS_MULTI_USER_PROC=1 ATLAS_EXEC_MODE=single-worker ATLAS_DEFAULT_EXEC_MODE=single-worker ATLAS_SESSION_WORKER_POLICY=single-active-owner ATLAS_SESSION_WORKER_KEEPALIVE=1 ATLAS_DEFAULT_WORKFLOW=default python3 src/atlas_ui.py --port "$ATLAS_E2E_PORT" --host 127.0.0.1 --root "$ATLAS_E2E_ROOT" --workflow-root "$REPO/workflow" --exec single-worker --session "$ATLAS_E2E_USER" --workspace-session default --ip default --workflow default > .omo/evidence/task-4-single-worker-new-ip-test-server.log 2>&1 & echo $! > .omo/evidence/task-4-single-worker-new-ip-test-server.pid; for i in $(seq 1 60); do curl -fsS "$ATLAS_E2E_BASE/healthz" > .omo/evidence/task-4-single-worker-new-ip-test-healthz.json && break || sleep 1; done; curl -fsS "$ATLAS_E2E_BASE/api/pipeline/run_policy" > .omo/evidence/task-4-single-worker-new-ip-test-run-policy.json; python3 - <<'PY'
import json
from pathlib import Path
health = json.loads(Path(".omo/evidence/task-4-single-worker-new-ip-test-healthz.json").read_text())
policy = json.loads(Path(".omo/evidence/task-4-single-worker-new-ip-test-run-policy.json").read_text())
assert health["ok"] is True, health
assert policy["exec_mode"] == "single-worker", policy
assert policy["orchestrator_enabled"] is False, policy
assert policy["initial_workflow"] == "default", policy
PY
    Expected: Server responds to health and run policy is single-worker/default with orchestrator disabled.
    Evidence: .omo/evidence/task-4-single-worker-new-ip-test-run-policy.json

  Scenario: bad exec mode is rejected before startup
    Tool:     bash
    Steps:    set -euo pipefail; source .omo/evidence/task-1-single-worker-new-ip-test.env; BAD_PORT=$((ATLAS_E2E_PORT + 1000)); set +e; ATLAS_ROOT="$ATLAS_E2E_ROOT" python3 src/atlas_ui.py --port "$BAD_PORT" --root "$ATLAS_E2E_ROOT" --workflow-root "$REPO/workflow" --exec definitely-bad > .omo/evidence/task-4-single-worker-new-ip-test-error.txt 2>&1; RC=$?; set -e; test "$RC" -ne 0; grep -q -- "--exec: unknown value" .omo/evidence/task-4-single-worker-new-ip-test-error.txt
    Expected: Command exits nonzero and evidence contains `--exec: unknown value`.
    Evidence: .omo/evidence/task-4-single-worker-new-ip-test-error.txt
  ```

  Commit: NO | Message: `test(single-worker): start isolated strict default server` | Files: [.omo/evidence/task-4-single-worker-new-ip-test-run-policy.json]

- [ ] 5. Create auth session and activate default namespace through HTTP

  What to do: Register and log in the test user, create a session row through `/api/sessions`, activate `owner/default/default/default`, and capture worker status for the strict interactive worker lane.
  Must NOT do: Do not create the IP in this task. Do not call orchestrator endpoints.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [6] | Blocked by: [4]

  References (executor has NO interview context - be exhaustive):
  - API/Type: `core/atlas_auth.py:773-815` - `/api/auth/register` creates the user and sets the auth cookie.
  - API/Type: `core/atlas_auth.py:817-842` - `/api/auth/login` validates credentials and sets the auth cookie.
  - API/Type: `src/atlas_api_sessions.py:1497-1534` - `/api/sessions` list/create session rows; title is required.
  - API/Type: `src/atlas_api_sessions.py:237-360` - `/api/session/activate` canonicalizes `owner`, `workspace_session`, `ip`, and `workflow`.
  - API/Type: `src/atlas_api_sessions.py:1388-1456` - `/api/session/worker/status` is scoped to the authenticated owner/session.
  - Pattern:  `src/atlas_api_sessions.py:1390-1397` - worker status is independent of `/api/orchestrator/workers`.

  Acceptance criteria (agent-executable only):
  - [ ] `.omo/evidence/task-5-single-worker-new-ip-test.json` has `register.status < 400`, `login.status < 400`, `session.status == 200`, and `activation.workflow == "default"`.
  - [ ] Activation evidence has no fallback to a different owner/IP/workflow.
  - [ ] Worker status evidence has policy `single-active-owner` or `single_active_owner: true`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: HTTP auth, session create, default activation
    Tool:     bash
    Steps:    set -euo pipefail; set -a; source .omo/evidence/task-1-single-worker-new-ip-test.env; set +a; python3 - <<'PY'
import http.cookiejar, json, os, urllib.error, urllib.request
from pathlib import Path
base = os.environ["ATLAS_E2E_BASE"]
user = os.environ["ATLAS_E2E_USER"]
password = os.environ["ATLAS_E2E_PASS"]
cookie_path = Path(os.environ["ATLAS_E2E_COOKIE"])
cj = http.cookiejar.MozillaCookieJar(str(cookie_path))
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def req(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"} if body is not None else {}
    r = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with opener.open(r, timeout=20) as resp:
            raw = resp.read().decode()
            return {"status": resp.status, "json": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return {"status": exc.code, "json": parsed}
out = {}
out["register"] = req("POST", "/api/auth/register", {"username": user, "password": password, "display_name": user})
out["login"] = req("POST", "/api/auth/login", {"username": user, "password": password})
cj.save(ignore_discard=True)
out["me"] = req("GET", "/api/users/me")
out["session"] = req("POST", "/api/sessions", {"title": f"single-worker-new-ip-{os.environ['ATLAS_E2E_TAG']}", "project_id": os.environ["ATLAS_E2E_IP"]})
out["activation"] = req("POST", "/api/session/activate", {"owner": user, "workspace_session": "default", "ip": "default", "workflow": "default"})
out["worker_status"] = req("GET", "/api/session/worker/status?session_id=" + urllib.parse.quote(f"{user}/default/default/default", safe=""))
Path(".omo/evidence/task-5-single-worker-new-ip-test.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
assert out["register"]["status"] < 400 or out["register"]["status"] == 409, out
assert out["login"]["status"] < 400, out
assert out["session"]["status"] == 200, out
act = out["activation"]["json"]
assert out["activation"]["status"] == 200, out
assert act.get("workflow") == "default" or str(act.get("namespace") or act.get("active_session") or "").endswith("/default"), out
PY
    Expected: Evidence JSON records successful login, session create, default activation, and worker status.
    Evidence: .omo/evidence/task-5-single-worker-new-ip-test.json

  Scenario: bad session body is rejected
    Tool:     bash
    Steps:    set -euo pipefail; source .omo/evidence/task-1-single-worker-new-ip-test.env; curl -sS -b "$ATLAS_E2E_COOKIE" -H 'Content-Type: application/json' -d '{}' "$ATLAS_E2E_BASE/api/sessions" > .omo/evidence/task-5-single-worker-new-ip-test-error.json; python3 - <<'PY'
import json
from pathlib import Path
body = json.loads(Path(".omo/evidence/task-5-single-worker-new-ip-test-error.json").read_text())
assert body.get("error") == "title required", body
PY
    Expected: Error JSON contains `{"error":"title required"}`.
    Evidence: .omo/evidence/task-5-single-worker-new-ip-test-error.json
  ```

  Commit: NO | Message: `test(single-worker): verify default session activation` | Files: [.omo/evidence/task-5-single-worker-new-ip-test.json]

- [ ] 6. Create one fresh IP through UI modal and backing HTTP API

  What to do: Use Playwright with real Chrome to log in, click the UI `+ IP` control, submit the fresh IP name, capture the `/api/ip/create` request/response, and assert the created session is `user/default/<ip>/default` with `exec_mode=single-worker`.
  Must NOT do: Do not use the API fallback path when the `+ IP` button or modal is unavailable. Do not switch away from `default`.

  Parallelization: Can parallel: NO | Wave 4 | Blocks: [7, 8] | Blocked by: [5]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/app.tsx:783-849` - `createIp()` scaffolds a new IP, posts `/api/ip/create`, then activates the created namespace.
  - Pattern:  `frontend/atlas/app.tsx:815-826` - request payload fields for `/api/ip/create`.
  - Pattern:  `frontend/atlas/app.tsx:840-849` - created namespace and workflow are used for activation.
  - API/Type: `src/atlas_ui.py:3241-3267` - `/api/ip/create` validates name and exec mode.
  - API/Type: `src/atlas_ui.py:3337-3431` - `/api/ip/create` scaffolds files, upserts workspace/IP/session rows, warms worker, and returns session/workflow/exec mode.
  - Test:     `scripts/atlas_vite_e2e_realuser.mjs:108-149` - proven selectors for `+ IP`, `Create IP`, `New IP name`, and response assertions.

  Acceptance criteria (agent-executable only):
  - [ ] `.omo/evidence/task-6-single-worker-new-ip-test.json` has `createdViaUi: true`.
  - [ ] The captured `/api/ip/create` request has `workflow == "default"` and `exec_mode == "single-worker"`.
  - [ ] The captured response has `ok == true`, `ip == $ATLAS_E2E_IP`, `workflow == "default"`, `exec_mode == "single-worker"`, and `session` ending `/$ATLAS_E2E_IP/default`.
  - [ ] `.omo/evidence/task-6-single-worker-new-ip-test.png` exists.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: UI modal creates fresh IP in single-worker/default mode
    Tool:     playwright(real Chrome)
    Steps:    set -euo pipefail; set -a; source .omo/evidence/task-1-single-worker-new-ip-test.env; set +a; node --input-type=module <<'NODE'
import fs from 'node:fs';
import { chromium } from 'playwright';
const base = process.env.ATLAS_E2E_BASE;
const user = process.env.ATLAS_E2E_USER;
const pass = process.env.ATLAS_E2E_PASS;
const ip = process.env.ATLAS_E2E_IP;
const outPath = '.omo/evidence/task-6-single-worker-new-ip-test.json';
const shotPath = '.omo/evidence/task-6-single-worker-new-ip-test.png';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const result = { createdViaUi: false, requests: [], responses: [], state: {} };
try {
  const ctx = await browser.newContext({ baseURL: base, viewport: { width: 1680, height: 1000 }, ignoreHTTPSErrors: true });
  const login = await ctx.request.post(base + '/api/auth/login', { data: { username: user, password: pass } });
  if (!login.ok()) throw new Error(`/api/auth/login -> ${login.status()}`);
  const page = await ctx.newPage();
  page.on('request', (req) => {
    if (req.url().includes('/api/ip/create')) {
      let parsed = {};
      try { parsed = JSON.parse(req.postData() || '{}'); } catch (_) {}
      result.requests.push({ url: req.url().replace(base, ''), method: req.method(), json: parsed });
    }
  });
  page.on('response', async (res) => {
    if (res.url().includes('/api/ip/create')) {
      let parsed = {};
      try { parsed = await res.json(); } catch (_) {}
      result.responses.push({ url: res.url().replace(base, ''), status: res.status(), json: parsed });
    }
  });
  await page.goto(base + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('textarea[placeholder*="message" i], textarea', { timeout: 60000 });
  const plus = page.locator('button', { hasText: /^\+\s*IP$/ }).first();
  if (!(await plus.count())) throw new Error('+ IP button not found; UI fallback is not allowed');
  await plus.click({ timeout: 10000 });
  const modal = page.locator('[role="dialog"][aria-label="Create IP"]');
  await modal.waitFor({ state: 'visible', timeout: 10000 });
  await page.fill('[aria-label="New IP name"]', ip, { timeout: 10000 });
  const responsePromise = page.waitForResponse((res) => res.url().includes('/api/ip/create') && res.request().method() === 'POST', { timeout: 60000 });
  await modal.locator('button:has-text("Create")').click();
  await responsePromise;
  result.createdViaUi = true;
  await page.waitForTimeout(2000);
  await page.screenshot({ path: shotPath, fullPage: true });
  result.state = await page.evaluate(() => ({ activeIp: window.ACTIVE_IP || '', activeSession: window.ACTIVE_SESSION || '', execMode: window.ATLAS_EXEC_MODE || window.ATLAS_DEFAULT_EXEC_MODE || '' }));
} finally {
  await browser.close();
}
fs.writeFileSync(outPath, JSON.stringify(result, null, 2));
const req = result.requests.find((item) => item.method === 'POST');
const resp = result.responses.find((item) => item.status < 400);
if (!result.createdViaUi) throw new Error('not created through UI');
if (!req) throw new Error('missing /api/ip/create request');
if (!resp) throw new Error('missing successful /api/ip/create response');
if (req.json.workflow !== 'default') throw new Error(`request workflow=${req.json.workflow}`);
if (req.json.exec_mode !== 'single-worker') throw new Error(`request exec_mode=${req.json.exec_mode}`);
if (resp.json.ip !== ip || resp.json.workflow !== 'default' || resp.json.exec_mode !== 'single-worker') throw new Error(JSON.stringify(resp.json));
if (!String(resp.json.session || '').endsWith(`/${ip}/default`)) throw new Error(`bad session ${resp.json.session}`);
NODE
    Expected: Evidence JSON proves UI modal path and HTTP create response stayed `single-worker/default`.
    Evidence: .omo/evidence/task-6-single-worker-new-ip-test.json

  Scenario: duplicate IP create returns 409 without creating a second IP
    Tool:     bash
    Steps:    set -euo pipefail; source .omo/evidence/task-1-single-worker-new-ip-test.env; curl -sS -b "$ATLAS_E2E_COOKIE" -H 'Content-Type: application/json' -d "{\"name\":\"$ATLAS_E2E_IP\",\"kind\":\"TBD\",\"exec_mode\":\"single-worker\",\"workflow\":\"default\"}" "$ATLAS_E2E_BASE/api/ip/create" > .omo/evidence/task-6-single-worker-new-ip-test-error.json; python3 - <<'PY'
import json
from pathlib import Path
body = json.loads(Path(".omo/evidence/task-6-single-worker-new-ip-test-error.json").read_text())
assert "already exists" in body.get("error", ""), body
PY
    Expected: Error JSON contains `already exists`.
    Evidence: .omo/evidence/task-6-single-worker-new-ip-test-error.json
  ```

  Commit: NO | Message: `test(single-worker): create fresh ip through ui modal` | Files: [.omo/evidence/task-6-single-worker-new-ip-test.json, .omo/evidence/task-6-single-worker-new-ip-test.png]

- [ ] 7. Submit one request through `/ws/agent` on the default workflow

  What to do: Log in, activate the created IP on `workflow=default`, open `/ws/agent`, send one prompt with the canonical session from Task 6, and capture delivery/acceptance/output frames. If output is blocked, write a first-blocker classification instead of claiming pass.
  Must NOT do: Do not send the prompt on `ssot-gen`, `rtl-gen`, or `orchestrator`. Do not count `worker_warmup` alone as success.

  Parallelization: Can parallel: YES | Wave 5 | Blocks: [F3] | Blocked by: [6]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `src/atlas_ui.py:7-10` - `/ws/agent` is the product bidirectional event stream.
  - Pattern:  `scripts/atlas_ws_nusers.mjs:57-79` - existing WS checker pattern for `agent_received`, `agent_accepted`, and output/running.
  - Pattern:  `scripts/atlas_ws_nusers.mjs:91-95` - existing script creates with `workflow=default` but sends on rotated workflow; do not reuse as sufficient default-workflow evidence.
  - Pattern:  `scripts/atlas_ws_nusers.mjs:151-156` - evidence summary and nonzero exit on failed checks.
  - API/Type: `src/atlas_api_sessions.py:237-360` - activation route keeps owner/IP/workflow in sync.
  - API/Type: `src/atlas_api_sessions.py:1388-1456` - worker status can confirm the requested default session.
  - Pattern:  `doc/wiki/atlas-single-active-orchestrator-subworkers-20260603.md:83-86` - capacity wait is an explicit blocker state, not success.

  Acceptance criteria (agent-executable only):
  - [ ] `.omo/evidence/task-7-single-worker-new-ip-test.json` has `sent.workflow == "default"` and `sent.session` ending `/$ATLAS_E2E_IP/default`.
  - [ ] Evidence has either `status == "pass"` with `received`, `accepted`, and `started` all true, or `status == "blocked"` with `first_blocker.category` in `[ws_delivery, worker_acceptance, worker_output, capacity_wait]`.
  - [ ] Evidence text does not contain `/orchestrator` as the sent workflow/session.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: default-workflow WS prompt is delivered and accepted, or first blocker is classified
    Tool:     bash
    Steps:    set -euo pipefail; set -a; source .omo/evidence/task-1-single-worker-new-ip-test.env; set +a; node --input-type=module <<'NODE'
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const WebSocket = require(path.resolve('frontend/atlas/node_modules/ws'));
const base = process.env.ATLAS_E2E_BASE;
const wsbase = base.replace(/^http/, 'ws');
const user = process.env.ATLAS_E2E_USER;
const pass = process.env.ATLAS_E2E_PASS;
const ip = process.env.ATLAS_E2E_IP;
const createEvidence = JSON.parse(fs.readFileSync('.omo/evidence/task-6-single-worker-new-ip-test.json', 'utf8'));
const createResp = createEvidence.responses.find((item) => item.status < 400)?.json || {};
const session = createResp.session || `${user}/default/${ip}/default`;
const result = { sent: { session, ip, workflow: 'default' }, frames: [], received: false, accepted: false, started: false, workerPid: null, status: 'blocked', first_blocker: null };
function cookieFrom(res) {
  const all = (res.headers.getSetCookie && res.headers.getSetCookie()) || [];
  const raw = all.find((item) => item.startsWith('atlas_session=')) || res.headers.get('set-cookie') || '';
  return raw.split(';')[0];
}
async function post(pathname, body, cookie='') {
  const headers = { 'Content-Type': 'application/json' };
  if (cookie) headers.Cookie = cookie;
  const res = await fetch(base + pathname, { method: 'POST', headers, body: JSON.stringify(body) });
  let json = {};
  try { json = await res.json(); } catch (_) {}
  return { status: res.status, json, res };
}
const login = await post('/api/auth/login', { username: user, password: pass });
const cookie = cookieFrom(login.res);
if (!cookie) throw new Error(`login produced no atlas_session cookie: ${login.status}`);
const activation = await post('/api/session/activate', { owner: user, workspace_session: 'default', ip, workflow: 'default' }, cookie);
result.activation = { status: activation.status, json: activation.json };
const warm = activation.json?.session_worker_warmup || {};
if (warm.status === 'capacity_wait') {
  result.first_blocker = { category: 'capacity_wait', detail: warm };
} else {
  await new Promise((resolve) => {
    let done = false;
    const finish = () => { if (done) return; done = true; try { ws.close(); } catch (_) {}; resolve(); };
    const ws = new WebSocket(`${wsbase}/ws/agent?session_id=${encodeURIComponent(user)}`, { headers: { Cookie: cookie } });
    const timer = setTimeout(finish, 90000);
    ws.on('open', () => {
      ws.send(JSON.stringify({ type: 'prompt', msg_id: `${process.env.ATLAS_E2E_TAG}-default-1`, text: `Reply with READY DEFAULT for ${ip}. Do not edit files.`, session, ip, workflow: 'default', ui_lang: 'en' }));
    });
    ws.on('message', (data) => {
      const text = data.toString();
      result.frames.push(text.slice(0, 1000));
      const blob = result.frames.join('\n');
      result.received = /"type"\s*:\s*"agent_received"/.test(blob);
      result.accepted = /"type"\s*:\s*"agent_accepted"[\s\S]*?"ok"\s*:\s*true/.test(blob);
      result.started = /"type"\s*:\s*"(token|tool)"/.test(blob) || /"type"\s*:\s*"agent_state"[\s\S]*?"running"\s*:\s*true/.test(blob) || /READY DEFAULT/.test(blob);
      const pid = blob.match(/"type"\s*:\s*"worker_started"[\s\S]*?"pid"\s*:\s*(\d+)/) || blob.match(/"pid"\s*:\s*(\d+)[\s\S]*?"type"\s*:\s*"worker_started"/);
      if (pid) result.workerPid = pid[1];
      if (result.received && result.accepted && result.started) { clearTimeout(timer); finish(); }
    });
    ws.on('error', () => { clearTimeout(timer); finish(); });
  });
}
if (result.received && result.accepted && result.started) {
  result.status = 'pass';
} else if (!result.first_blocker) {
  result.first_blocker = !result.received
    ? { category: 'ws_delivery', detail: 'missing agent_received' }
    : !result.accepted
      ? { category: 'worker_acceptance', detail: 'missing agent_accepted ok true' }
      : { category: 'worker_output', detail: 'accepted but missing token/tool/running/READY DEFAULT before timeout' };
}
fs.writeFileSync('.omo/evidence/task-7-single-worker-new-ip-test.json', JSON.stringify(result, null, 2));
if (result.sent.workflow !== 'default' || !result.sent.session.endsWith(`/${ip}/default`)) throw new Error(JSON.stringify(result.sent));
NODE
    Expected: Evidence records pass with received+accepted+started, or blocked with first blocker category.
    Evidence: .omo/evidence/task-7-single-worker-new-ip-test.json

  Scenario: unauthenticated WS does not accept a prompt
    Tool:     bash
    Steps:    set -euo pipefail; set -a; source .omo/evidence/task-1-single-worker-new-ip-test.env; set +a; node --input-type=module <<'NODE'
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const WebSocket = require(path.resolve('frontend/atlas/node_modules/ws'));
const wsbase = process.env.ATLAS_E2E_BASE.replace(/^http/, 'ws');
const result = { opened: false, accepted: false, frames: [] };
await new Promise((resolve) => {
  const ws = new WebSocket(`${wsbase}/ws/agent?session_id=no_cookie`);
  const timer = setTimeout(() => { try { ws.close(); } catch (_) {}; resolve(); }, 5000);
  ws.on('open', () => { result.opened = true; ws.send(JSON.stringify({ type: 'prompt', text: 'should not run', session: 'bad/default/ip/default', ip: 'ip', workflow: 'default' })); });
  ws.on('message', (data) => { const t = data.toString(); result.frames.push(t); if (/"type"\s*:\s*"agent_accepted"[\s\S]*?"ok"\s*:\s*true/.test(t)) result.accepted = true; });
  ws.on('close', () => { clearTimeout(timer); resolve(); });
  ws.on('error', () => { clearTimeout(timer); resolve(); });
});
fs.writeFileSync('.omo/evidence/task-7-single-worker-new-ip-test-error.json', JSON.stringify(result, null, 2));
if (result.accepted) throw new Error('unauthenticated prompt accepted');
NODE
    Expected: Error evidence has `"accepted": false`.
    Evidence: .omo/evidence/task-7-single-worker-new-ip-test-error.json
  ```

  Commit: NO | Message: `test(single-worker): submit default workflow ws request` | Files: [.omo/evidence/task-7-single-worker-new-ip-test.json]

- [ ] 8. Run contract/signoff validation or classify first blocker

  What to do: Run SSOT disk validation, SSOT verifier, IP contract derivation, and signoff checker against the fresh IP. If signoff fails, classify the first blocker using `src.orchestrator.classify.classify_failure` and write a structured result.
  Must NOT do: Do not edit the fresh IP's generated evidence by hand. Do not change SSOT/requirements to make signoff pass.

  Parallelization: Can parallel: YES | Wave 5 | Blocks: [F3] | Blocked by: [6]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `doc/wiki/default-agent-ip-flow.md:85-95` - default-agent mode still needs a contract source.
  - Pattern:  `doc/wiki/default-agent-ip-flow.md:288-309` - static/signoff checks must run or record unavailable/limited checks.
  - Pattern:  `doc/wiki/default-agent-ip-flow.md:310-344` - final signoff bundle/report and adversarial evidence review.
  - Pattern:  `doc/wiki/default-agent-ip-flow.md:367-376` - do not edit SSOT/requirements just to make RTL pass; do not approve stale artifacts.
  - API/Type: `workflow/ssot-gen/scripts/check_ssot_disk.sh:1-17` - disk-truth SSOT validator purpose and exit behavior.
  - API/Type: `workflow/ssot-gen/scripts/check_ssot_disk.sh:21-70` - accepted run modes and CLI parsing.
  - API/Type: `workflow/ssot-gen/scripts/verify_ssot.py:553-645` - verifier CLI writes `req/ssot_validation.json` and exits nonzero on blockers.
  - API/Type: `workflow/ip-contract/scripts/derive_ip_contract.py:433-493` - derives and writes `verify/ip_contract.json`.
  - API/Type: `workflow/signoff/scripts/check_ip_signoff.py:875-909` - signoff checker writes JSON/Markdown and exits 0 only on pass.
  - API/Type: `src/orchestrator/classify.py:15-35` - owner classification routes to repair workflows.
  - API/Type: `src/orchestrator/classify.py:293-319` - `classify_failure` output contract.
  - Pattern:  `.cursor/hooks/protect-generated-artifacts.py:9-20` - generated artifacts are protected from manual edits.

  Acceptance criteria (agent-executable only):
  - [ ] `.omo/evidence/task-8-single-worker-new-ip-test.json` has `ip == $ATLAS_E2E_IP`.
  - [ ] Result has either `status == "pass"` with signoff pass, or `status == "blocked"` with `first_blocker.next_workflow` or `first_blocker.category`.
  - [ ] Generated files, if present, are created by validator commands only: `$ATLAS_E2E_ROOT/$ATLAS_E2E_IP/req/ssot_validation.json`, `verify/ip_contract.json`, and `signoff/ip_signoff.json`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: validate contract/signoff or classify first blocker
    Tool:     bash
    Steps:    set -euo pipefail; set -a; source .omo/evidence/task-1-single-worker-new-ip-test.env; set +a; IP="$ATLAS_E2E_IP"; ROOT="$ATLAS_E2E_ROOT"; set +e; bash workflow/ssot-gen/scripts/check_ssot_disk.sh "$IP" --root "$ROOT" --mode starter > .omo/evidence/task-8-single-worker-new-ip-test-check-ssot.log 2>&1; SSOT_DISK_RC=$?; python3 workflow/ssot-gen/scripts/verify_ssot.py "$IP" --root "$ROOT" --mode signoff --json > .omo/evidence/task-8-single-worker-new-ip-test-verify-ssot.json 2> .omo/evidence/task-8-single-worker-new-ip-test-verify-ssot.err; VERIFY_RC=$?; python3 workflow/ip-contract/scripts/derive_ip_contract.py "$IP" --root "$ROOT" > .omo/evidence/task-8-single-worker-new-ip-test-contract.log 2>&1; CONTRACT_RC=$?; python3 workflow/signoff/scripts/check_ip_signoff.py "$IP" --root "$ROOT" > .omo/evidence/task-8-single-worker-new-ip-test-signoff.log 2>&1; SIGNOFF_RC=$?; set -e; python3 - "$SSOT_DISK_RC" "$VERIFY_RC" "$CONTRACT_RC" "$SIGNOFF_RC" <<'PY'
import json, os, sys
from pathlib import Path
from src.orchestrator.classify import classify_failure
ssot_disk_rc, verify_rc, contract_rc, signoff_rc = [int(x) for x in sys.argv[1:5]]
ip = os.environ["ATLAS_E2E_IP"]
root = Path(os.environ["ATLAS_E2E_ROOT"])
summary = {
    "ip": ip,
    "root": str(root),
    "commands": {
        "check_ssot_disk": ssot_disk_rc,
        "verify_ssot": verify_rc,
        "derive_ip_contract": contract_rc,
        "check_ip_signoff": signoff_rc,
    },
    "status": "blocked",
    "first_blocker": None,
}
verify_path = root / ip / "req" / "ssot_validation.json"
signoff_path = root / ip / "signoff" / "ip_signoff.json"
if signoff_path.is_file():
    signoff = json.loads(signoff_path.read_text(encoding="utf-8"))
    summary["signoff"] = {"status": signoff.get("status"), "summary": signoff.get("summary")}
    if signoff.get("status") == "pass":
        summary["status"] = "pass"
    else:
        gates = signoff.get("gates") or []
        failed = next((gate for gate in gates if str(gate.get("status")) not in ("pass", "skip")), None)
        if failed:
            cls = classify_failure(str(failed.get("name") or "contract-check"), evidence=failed, error_text=json.dumps(failed))
            summary["first_blocker"] = {"category": "signoff", "gate": failed.get("name"), **cls}
if summary["status"] != "pass" and summary["first_blocker"] is None and verify_path.is_file():
    verify = json.loads(verify_path.read_text(encoding="utf-8"))
    blockers = verify.get("blockers") or []
    if blockers:
        first = blockers[0]
        cls = classify_failure("ssot-gen", evidence=first, error_text=json.dumps(first))
        summary["first_blocker"] = {"category": "ssot", "blocker": first, **cls}
if summary["status"] != "pass" and summary["first_blocker"] is None:
    for name, rc in summary["commands"].items():
        if rc != 0:
            summary["first_blocker"] = {"category": name, "returncode": rc}
            break
Path(".omo/evidence/task-8-single-worker-new-ip-test.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
assert summary["status"] == "pass" or summary["first_blocker"], summary
PY
    Expected: Summary JSON records pass or a first blocker with owner/next workflow classification where available.
    Evidence: .omo/evidence/task-8-single-worker-new-ip-test.json

  Scenario: missing IP fails disk validator without manual artifact edits
    Tool:     bash
    Steps:    set -euo pipefail; source .omo/evidence/task-1-single-worker-new-ip-test.env; set +e; bash workflow/ssot-gen/scripts/check_ssot_disk.sh "${ATLAS_E2E_IP}_missing" --root "$ATLAS_E2E_ROOT" --mode starter > .omo/evidence/task-8-single-worker-new-ip-test-error.txt 2>&1; RC=$?; set -e; test "$RC" -ne 0; grep -q "IP dir not found" .omo/evidence/task-8-single-worker-new-ip-test-error.txt
    Expected: Missing-IP validator exits nonzero and reports `IP dir not found`.
    Evidence: .omo/evidence/task-8-single-worker-new-ip-test-error.txt
  ```

  Commit: NO | Message: `test(single-worker): classify fresh ip signoff blocker` | Files: [.omo/evidence/task-8-single-worker-new-ip-test.json]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: .omo/plans/single-worker-new-ip-test.md`.
- Default for this request: no product-code commits. Evidence-only files under `.omo/evidence/` should stay uncommitted unless the caller explicitly asks to version them.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
