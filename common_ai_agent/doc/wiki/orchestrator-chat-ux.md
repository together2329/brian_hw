# Orchestrator Chat UX Overhaul (2026-05-19)

ATLAS Pipeline 우측 trace 패널이 **외계어 JSON trace event** 만 출력하던 문제를
chat-style natural language 패널로 갈아엎는 라운드. 본 페이지는 변경 의도,
랜딩한 커밋, **worker-4 hardcore E2E 검증 증거**를 모아둔다. 검증 결과는
정직하게 mixed (backend PASS / endpoint contract bug / frontend hydrate
regression) 임을 기록한다.

Related: [[atlas-pipeline-screen]], [[orchestrator-llm-loop-phase3]],
[[atlas-pytest-hygiene]], [[orchestrator-chat-only-product-plan]].

---

## 1. Symptom (before this round)

- Pipeline 우측 패널이 raw orchestrator trace (`{"type":"step","payload":{...}}`)
  를 그대로 노출하던 상태. 사용자가 chat 메시지를 보내도 응답이 JSON 으로 나와
  "외계어" 라고 사용자 피드백.
- 추가로 (a) workers bar 가 9개만 surface (b) DISPATCH 카운터 stuck (c)
  pipeline 첫 진입 시 IP 미선택이면 blank 화면 (d) light theme 에서 canvas 가
  까만 화면 (e) `.jsx`/`.css`/`.png` 정적 리소스의 Content-Type 누락 같은
  파편화 문제들이 동반.

## 2. Architecture change

### 2.1 chat_messages persistence (실제로는 trace_events row)

핸드오프 문서는 "`chat_messages` 테이블에 persist" 라고 표현했지만 실제 DB
스키마는 별도 테이블이 아니라 canonical `trace_events` 위에 얹어 두는
구조다 — `event_type='chat_message'`, payload `{content, display_name, role}`
로 저장된다 (`core/atlas_db.py:2820~2865`). 따라서:

- `core.atlas_db.AtlasDB.record_chat_message(ip_id, user_id, content,
  display_name="", workspace_id="", role="user")` 가 한 row 를 만든다.
- `role` 은 `"user" / "assistant" / "tool"` 셋 중 하나로 payload 안에 들어간다.
- 조회는 `AtlasDB.list_chat_messages(ip_id, limit, since=...)`. **이 함수는
  ip_id 인자로 UUID (`ip_blocks.id`) 를 받지, ip name 을 받지 않는다.**

### 2.2 react_bridge → assistant content + tool labels

`src/orchestrator/react_bridge.py:42-91` 의 `_ChatPersister` 가:

- LLM 응답 stream 한 turn 분량의 content 를 누적해 `flush_assistant_turn` 에서
  role=assistant row 1 개로 commit.
- 매 tool 호출 직전에 `ui_formatter.format_tool_call(name, args)` 로 한국어 + emoji
  status 라인을 만들어 role=tool row 로 persist.
- DB 실패는 silent swallow — chat 은 observability, control-flow 가 아님.

`src/orchestrator/ui_formatter.py` (Task #1 신규) 가 `dispatch_workflow`,
`read_evidence`, `mark_downstream_stale`, `ask_user`, `yield_run` 을 사람이
읽을 수 있는 한 줄로 매핑한다.

### 2.3 Polling endpoint

`src/atlas_api_jobs.py:3961~3997` 의 `GET /api/orchestrator/chat/messages`.

- query: `ip` (필수, 정규식 `^[A-Za-z][A-Za-z0-9_]*$`), `since` (unix
  timestamp float), `limit` (1~500, default 100).
- 응답: `{"ok": true, "messages": [trace_event row…], "next_since": <ts>}`.
- 인증은 `_request_db_user_id` 로 cookie session 기반.

### 2.4 Pipeline chat panel

`frontend/atlas/pipeline.jsx:2498~2571` 의 `OrchestratorChatPanel`. 우측
rail 에 `orch-chat-panel` 컨테이너로 마운트, `pipelineState.orchestrator.active`
가 true 일 때 1500ms 마다 polling. role 별 클래스는:

- `assistant` → `md-bubble md-agent`
- `user` → `md-bubble md-user md-agent`
- `tool` → `md-bubble md-tool`

### 2.5 Static MIME fix

`src/atlas_ui.py` `_NoCacheStatic.get_response` 가 `.js` 외 자산도
`mimetypes.guess_type` 기반으로 Content-Type 을 정확히 부여하도록 확장
(commit `be4008e7e`). `.jsx` 는 `application/javascript` 로 override.

### 2.6 IP 추출 from message body

`src/atlas_api_jobs.py` `_extract_ip_from_orchestrator_message` (commit
`0087dce51`). chat body 의 자유 텍스트에서 `[A-Za-z][A-Za-z0-9_]*` 토큰을
파싱해 IP 우선순위를 (1) body explicit `ip` field (2) message 내 IP 토큰
(3) 기본값 순으로 결정. dropdown 의 ACTIVE_IP 와 다른 IP 도 message
한 줄로 띄울 수 있다.

## 3. Landed commits (E2E 검증 대상)

| Commit | 영향 |
|---|---|
| `4b3fc635e` | workers route surfaces 12 stages, drop goal-audit |
| `0087dce51` | orchestrator chat IP extraction from message body |
| `d94f830c8` | pipeline.jsx DISPATCH counter sync + first-load IP placeholder |
| `e3fb1f433` | pytest collection regression fix |
| `01625f87c` | top-right nav single-line CSS |
| `b5763b668` | pipeline light-mode token overrides |
| `be4008e7e` | static asset MIME fix (.jsx/.css/.png) |
| `0d00c082b` | orchestrator content + tool-call labels → chat_messages |
| `7cf5b0cb7` | pipeline chat panel polls /api/orchestrator/chat/messages |
| `f8e961c17` | atlas.db untracked + root .gitignore |

## 4. Verification evidence (worker-4, 2026-05-19 16:42~16:58 KST)

### 4.1 환경

- Backend: PID 90987, `python3 src/atlas_ui.py --host 127.0.0.1 --port 62196
  --model gpt-5.5 --effort xhigh`, etime 16:50+.
- DB: `/Users/brian/.common_ai_agent/atlas.db` (lsof 로 확인된 atlas_ui FD).
  17:42 baseline `trace_events(chat_message)` row = 7.
- cmux: workspace:1 pane:7 의 `surface:9` ATLAS browser, validator session.
- 검증 모드: read-only. 핸드오프 지시대로 atlas_ui / workers 프로세스는
  재시작하지 않음. 캡쳐 산출물: `/tmp/worker4_verify/`.

### 4.2 Check-by-check

| # | 항목 | 결과 | 증거 |
|---|---|---|---|
| 1 | Cold-load sanity | **PARTIAL PASS** | `/tmp/worker4_verify/01_cold_load.png`. Babel dev warning 외 콘솔 에러 0. 네트워크 실패 0. Root `/` URL 에선 page hydrate (totalCls 417) 정상. |
| 2 | Workers bar count = 12 | **PASS** | `GET /api/orchestrator/workers?ip=pl330` → `"count":12`, workflows 정확히 `ssot-gen/fl-model-gen/rtl-gen/lint/tb-gen/sim/coverage/sim_debug/syn/sta/pnr/sta-post`, goal-audit 없음. 모델 매핑도 plan 사양과 일치 (ssot/fl→glm-5.1, sim_debug→kimi-k2-thinking, 나머지→deepseek-v4-pro). |
| 3 | DISPATCH counter sync | **BLOCKED** | Pipeline view 가 hydrate 실패 (`appendChild` uncaught) 상태라 cmd-click 으로 stage pill 을 선택할 수 없어 시각 검증 불가. backend 자체에 회귀는 없음 (코드 경로 미터칭). |
| 4 | First-load IP placeholder | **BLOCKED (same root cause as #3)** | PIPELINE tab 진입 즉시 화면이 `[오후 4:56:40] uncaught: appendChild@[native code] / SEe@babel.min.js:3:3128405 …` 로 덮여 placeholder 자체가 안 보임. (스크린샷 `05_pipeline_appendchild_err.png`) |
| 5 | Light/Dark 토글 | **BLOCKED (same root cause)** | LIGHT 버튼 클릭은 dispatch 되나, hydrate 가 안 된 상태라 token 적용을 시각 확인 불가. 백엔드 token 정의 (`b5763b668`) 자체엔 영향 없음. (`06_light_attempt.png`) |
| 6 | Orchestrator chat panel — natural-language reply | **MIXED** — 6a backend persist **PASS**, 6b API contract **FAIL**, 6c UI render **BLOCKED** | 아래 6.x 상세 |
| 7 | DB cross-check | **PASS** for orchestrator_runs/workflow_runs/chat rows, **FAIL** for endpoint contract | 아래 7.x 상세 |
| 8 | Image/asset load | **PASS** | 정적 자산 200 OK 응답 (`/styles.css`, `/pipeline.jsx`, `/backend.js`, `/vendor/prism-tomorrow.css`). 각 응답에 `Content-Type: text/css/javascript` 정확히 부여됨. `_NoCacheStatic` MIME fix (`be4008e7e`) 확인. |

### 4.3 Check #6 상세 — chat panel mixed verdict

**시나리오**: `POST /api/pipeline/orchestrator/chat` body `{"message":"run ssot for cmux_orch_ux_20260519"}` → 응답 `{"ok":true,"ip":"cmux_orch_ux_20260519","run_id":"0441cffed5ab425eb97650fbc13f686c","status":"started"}` → 30 초 대기 → DB 와 endpoint 동시 확인.

**6a — Backend persist (PASS)**: `trace_events` 에 4 개 chat row 가 정확한
순서로 들어옴.

```
2026-05-19 16:48:40 | user      | run ssot for cmux_orch_ux_20260519
2026-05-19 16:48:44 | tool      | 🔎 파이프라인 상태 조회: cmux_orch_ux_20260519
2026-05-19 16:48:48 | tool      | 🚀 ssot-gen 실행 중 (ssot-gen / cmux_orch_ux_20260519)
2026-05-19 16:48:54 | tool      | ⏸ 대기 중 (SSOT generation job is running; waiting for completion or user input.)
```

- payload 의 `role` 이 `user/tool` 로 정확히 구분됨.
- 한국어 + emoji tool 라벨이 `format_tool_call` 매핑대로 출력됨.
- 단, **role=assistant row 는 0개**. orchestrator_run 이 첫 ReAct iteration
  에서 `yield_run` 으로 status=yielded 가 되어 LLM 이 자유 텍스트 turn 을
  flush 하기 전에 끝났기 때문. plan-spec 의 "assistant content 도 persist"
  코드 자체는 살아 있지만 본 시나리오에선 미실행 — 더 긴 reasoning
  이 필요한 케이스에서 별도 검증 필요.

**6b — API contract (FAIL — endpoint always empty)**: `GET /api/orchestrator/chat/messages?ip=cmux_orch_ux_20260519` 응답 → `{"ok":true,"messages":[],"next_since":0}`. **DB 에 4 row 있음에도 빈 응답**.

근본 원인: `src/atlas_api_jobs.py:3991`

```python
rows = db.list_chat_messages(ip_id=ip, limit=limit, since=since)
```

여기서 `ip` 는 query param 의 IP **이름** (`cmux_orch_ux_20260519`) 이지만,
`trace_events.ip_id` 컬럼은 `ip_blocks.id` (UUID, 예: `18161f65c1464a92903849c3860a6172`) 로 저장돼 있음. `list_chat_messages` 가 `ip_id = ?` 로 정확히 매칭하므로 영원히 empty.

UUID 를 직접 query 로 넘기면 정규식 `^[A-Za-z][A-Za-z0-9_]*$` 가 첫 글자 `1` (digit) 때문에 reject — `{"error":"ip param missing or invalid"}` 400 응답. 즉 **현재 endpoint 로는 어떤 형태의 IP 식별자로도 chat row 를 받아올 수 없다.**

권장 fix: endpoint 에서 `db.upsert_ip_block(workspace_id, ip)` 또는
`find_ip_by_name` 으로 ip name → ip_id 변환 후 `list_chat_messages(ip_id=ip_row["id"], …)` 호출. user-scoped workspace 확인은 record_orchestrator_chat 과 동일 패턴.

**6c — UI render (BLOCKED — pipeline hydrate failure)**: PIPELINE tab 진입 시
화면이 다음 에러로 덮임 (`/tmp/worker4_verify/05_pipeline_appendchild_err.png`):

```
[오후 4:56:40] uncaught: appendChild@[native code]
SEe@http://127.0.0.1:62196/vendor/babel.min.js:3:3128405
n@http://127.0.0.1:62196/vendor/babel.min.js:3:3128648
PEe@http://127.0.0.1:62196/vendor/babel.min.js:3:3129425
@http://127.0.0.1:62196/vendor/babel.min.js:3:3133083
VEe@http://127.0.0.1:62196/vendor/babel.min.js:3:3133090
WEe@http://127.0.0.1:62196/vendor/babel.min.js:3:3132698
```

`totalCls` 가 33 (rail / stage / worker / chat 관련 class 0개) → React tree
가 마운트 안 됨. 따라서 chat panel 의 시각 확인이 원천적으로 불가능.
worker-9 (in_progress) 가 다루는 Babel appendChild error 와 동일 trace.

### 4.4 Check #7 상세 — DB cross-check

`/Users/brian/.common_ai_agent/atlas.db`:

```
ip_blocks (cmux_orch_ux_20260519)
  18161f65c1464a92903849c3860a6172
  d9c8a8df306d4c0f92ac32f36a4ff384
orchestrator_runs (latest 5)
  0441cffed5ab425eb97650fbc13f686c | 18161f65c1464a92903849c3860a6172 | yielded | 2026-05-19 16:48:40
workflow_runs WHERE ip_id=18161...
  1ddc1bd81db945d89de2ded3ae7504dc | ssot-gen | running | orchestrator_chat | 0441cffed5ab425eb97650fbc13f686c
```

확인 사항 (PASS):

- IP 이름이 chat body 에서 정확히 추출됨 (dropdown ACTIVE_IP=default 와 다른
  IP 가 새로 생성됨 — Bug A `0087dce51` PASS).
- orchestrator_runs row 가 새 IP 로 attach.
- workflow_runs 의 `trigger_source` = `orchestrator_chat` (plan 사양 일치).
- workflow_runs.orchestrator_run_id 가 orchestrator_runs.id 와 매칭.

확인 사항 (NOTE):

- 동일 IP name 으로 ip_blocks row 가 2 개 — workspace 차이 (validator vs.
  default workspace). per-user 격리는 정상 동작이나 row 가 분할되므로
  endpoint 가 ip_id 로 정확히 lookup 해야 user-scoped 결과를 줄 수 있음.

## 5. Verdict per check (final)

```
1  cold-load sanity                       PARTIAL PASS
2  workers bar count = 12                 PASS
3  DISPATCH counter                       BLOCKED (pipeline hydrate fail)
4  first-load IP placeholder              BLOCKED (pipeline hydrate fail)
5  light/dark theme                       BLOCKED (pipeline hydrate fail)
6  chat panel natural-language reply
   6a backend persist                     PASS (user/tool roles)
   6b /api/orchestrator/chat/messages     FAIL (ip name vs ip_id mismatch)
   6c UI render                           BLOCKED (pipeline hydrate fail)
7  DB cross-check                         PASS
8  image/asset load                       PASS
```

## 6. Recommended next-worker tasks

1. **chat/messages endpoint fix** — `src/atlas_api_jobs.py:3961~3997` 에서
   query 의 `ip` (name) 을 `ip_blocks.id` (UUID) 로 변환 후 list_chat_messages
   에 전달. `_request_db_user_id` 로 user-scoped workspace 를 잡아 `upsert_ip_block` 또는 `find_ip_by_name`. 동시에 정규식 매칭은 IP name 형식만
   허용하도록 유지 (UUID 직접 입력은 우회 차단). pytest 보강: post chat →
   30s wait → GET → assistant/tool rows 가 정확한 순서로 와야 한다.
2. **pipeline.jsx Babel appendChild crash** — worker-9 가 in_progress. 본
   검증으로 PIPELINE / WORKSPACE 양 진입 모두에서 hydrate 가 깨지는 것을
   확인. trace 첫 frame 이 babel.min.js 내부 `SEe → n → PEe → VEe → WEe` 인
   걸로 보아 JSX 컴파일 결과의 DOM mutation 단계. 우선 `view=pipeline` query
   를 안 붙인 root URL 만 hydrate 성공, `view=pipeline` 또는 PIPELINE tab
   클릭 시점에서 추가 컴포넌트 (chat panel 포함?) 마운트 중 fail. minified
   stack 으로는 부족하므로 dev build 또는 source map 활성화로 line 추적
   필요.
3. **role=assistant 시나리오 검증** — yield_run 으로 즉시 끝나지 않는
   reasoning-heavy 시나리오 (예: orchestrator 가 ask_user 를 거치는 흐름) 로
   `flush_assistant_turn` 까지 도달하는지 별도 e2e. ssot-gen 1 회 dispatch
   만으론 LLM 이 free-form content 를 안 emit 함.

## 7. 첨부

- 스크린샷: `/tmp/worker4_verify/01_cold_load.png` (root hydrate),
  `02_pipeline_default.png` (workflow=default), `03_workspace_mode.png`,
  `04_pipeline_no_ip.png`, `05_pipeline_appendchild_err.png` (crash),
  `06_light_attempt.png`.
- DB 덤프: `/tmp/worker4_verify/db_after.txt` (chat_messages + orchestrator_runs
  + workflow_runs 30s post-POST 스냅샷).
- 핸드오프 plan 원본: `.omc/handoffs/team-plan-orch-ux-hardcore.md`.
