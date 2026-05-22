---
title: Single main-loop restoration verify (2026-05-19)
date: 2026-05-19
status: PASS (with one fix landed mid-verify)
related:
  - flow-fixes-r3-verify-20260519
  - orchestrator-llm-loop-phase3
---

# Single main-loop restoration — cmux verify (May-12-style)

검증 목표: ATLAS_SINGLE_MAIN_LOOP=1 로 atlas_ui를 띄우면 단일 main-loop worker
(port 5601, --all-workflows) 가 자동 spawn되어 모든 워크플로우(SSOT, RTL, …) 를
순차적으로 받아 처리한다는 것을 cmux Chrome 으로 end-to-end 확인.

## 실행 환경

- atlas_ui: `http://127.0.0.1:62196`, env `ATLAS_SINGLE_MAIN_LOOP=1`, model `gpt-5.5`, effort `xhigh`.
- spawned main-loop worker: `pid=20616`, port `5601`, `--all-workflows`.
- cmux browser surface: `surface:9` (workspace:1, pane:7).
- 검증 시작: atlas_ui pid=13223 (재시작 이후 안정).
- DB: `~/.common_ai_agent/atlas.db`.

12-worker fleet (5621–5632) 은 사용자 환경에 별도로 떠 있었으나 atlas_ui spawn
로그에는 **5601만 spawn** 됐고, single-worker 모드에서 dispatch가 외부 fleet로
가지 않음을 cmux Chrome trace로 검증.

## 검증 절차

1. atlas_ui kill → single-worker env 로 재기동.
2. cookie `atlas_ip=cmux_singlewf` 세팅 후 `?ip=cmux_singlewf` 로 hard reload.
3. Pipeline mount + textarea 존재 확인.
4. 첫 dispatch: "A simple 8-bit counter with sync reset and enable, top module name: cnt8." → Enter.
5. ssot-gen 완료 (`status=completed`) 까지 대기. Worker PID 비교.
6. 두 번째 dispatch: "run rtl for cmux_singlewf" → Enter.
7. rtl-gen 시작/실행 확인. Worker PID 동일 유지 확인.
8. DB workflow_runs 확인 + LLM cost accounting 확인.

## 핵심 발견 — atlas_ui spawn 경로 버그 (별도 commit에서 수정됨)

처음 재기동 시 워커가 안 떠서 5601이 비어 있었음. atlas_ui 로그에는:

```
[single-worker] spawned main-loop worker on port 5601 (pid=13249)
/Library/.../python3: can't open file '/Users/.../common_ai_agent/main.py': [Errno 2] No such file or directory
[single-worker] WARNING: worker on port 5601 did not respond within 10.0s
```

원인: `src/atlas_ui.py:13528` 에서 `_main_py = str(SOURCE_ROOT / "main.py")` 로
경로 조립. `SOURCE_ROOT = HERE.parent` 이므로 repo 루트인 `common_ai_agent/`
아래에서 `main.py` 를 찾지만, 실제 파일은 `common_ai_agent/src/main.py` (= `HERE/main.py`).

해결: commit `52ed4e538` (`fix(api): cap dispatch prompt at 100k chars + correct
single-worker main.py path`) 에서 동일 root cause 가 v-error-path 매트릭스 작업
도중 발견되어 `_main_py = str(HERE / "main.py")` 로 수정됨. 본 verifier 가
working tree 에 동일한 패치를 적용했지만, head 가 이미 같은 값이라 git diff 0.

이 fix 적용 후 재기동에서 worker 정상 spawn — `pid=20616`, `/health` 200 응답.

## PASS / FAIL 체크리스트

| Step | 항목 | 결과 | 근거 |
|------|------|------|------|
| 0 | atlas_ui=200, main_loop_worker(5601)=200 | PASS | curl probe 200/200 |
| 0 | spawn log 단일 워커만 spawn | PASS | `[single-worker] spawned main-loop worker on port 5601 (pid=20616)` |
| 0 | `/health.all_workflows = true` | PASS | `{"all_workflows":true,"model":"gpt-5.5"}` |
| 1 | worker PID 캡처 | PASS | `WORKER_PID=20616` (`src/main.py --serve ... --all-workflows`) |
| 2 | textarea 렌더 + Pipeline mount | PASS | textarea placeholder `Message orchestrator for cmux_singlewf…` |
| 3 | 첫 dispatch (ssot) 완료 | PASS | workflow_runs `855ae954…` ssot-gen `completed`, started=1779192140.7, ended=1779192258.3 (소요≈117 s) |
| 3 | 첫 dispatch 후 worker PID 불변 | **PASS** | `pid=20616` |
| 4 | 두 번째 dispatch (rtl) 시작 | PASS | workflow_runs `264e8872…` rtl-gen `running`, started=1779192290.7 |
| 4 | 두 번째 dispatch 후 worker PID 불변 | **PASS** | `pid=20616` (after 20+ minutes, still alive, %CPU=3.1) |
| 4 | `/health.runs >= 2` | PASS | runs=3 (외부 3rd dispatch까지 동일 worker가 받음) |
| 5 | workflow_runs 2 행 (ssot + rtl) | PASS | DB 쿼리 결과 ssot-gen completed + rtl-gen running (terminal 도달 못함, 후술) |
| 5 | llm_calls > 0, cost > 0 | PARTIAL | rtl-gen 18 calls $1.01; **ssot-gen 이번 run의 llm_calls는 0** (후술) |
| 6 | 12-worker fleet 자동-spawn 없음 | PASS | atlas_ui 로그에 spawn된 워커는 5601 1개만. 5621–5632 은 사용자가 외부에서 띄운 것이며 atlas_ui가 그쪽으로 dispatch하지 않음 (chat trace #2,#4,#5 모두 5601 run_id) |

## 같은 worker가 두 워크플로우 받았다는 직접 증거

브라우저 ORCHESTRATOR TRACE 패널 (chat dump 발췌):

```
#1 http_recv ssot-gen
#2 http_accepted 200 run_921970da
#3 run_completed run_921970da
#4 http_recv rtl-gen
#5 http_accepted 200 run_66e144e1
```

- run_921970da → ssot-gen, run_66e144e1 → rtl-gen
- 둘 다 같은 HTTP endpoint (5601) 로 accept 됨
- worker process etime: `00:25 → 20:23` (재기동 한 번 없이 양쪽 모두 처리)

## chat body dump

```json
{
  "entryCount": 2,
  "entries": [
    {"cls":"md-bubble md-user md-agent",
     "text":"USERA simple 8-bit counter with sync reset and enable, top module name: cnt8."},
    {"cls":"md-bubble md-user md-agent",
     "text":"USERrun rtl for cmux_singlewf"}
  ],
  "snippet": [
    "cmux_singlewf", "● pipeline", "run", "Engineering", "exec", "Orchestrator",
    "rtl-v001", "▶ 1 running", "orchestrator:", "stages 15",
    "IP", "cmux_singlewf", "GREEN READINESS", "13%", "1 stage running",
    "Waiting for FL to finish.",
    "ORCHESTRATOR TRACE", "5 events",
    "corr_97d29ff6 #5 http_accepted 200 run_66e144e1",
    "corr_8b8a71f4 #4 http_recv rtl-gen",
    "✓ #3 run_completed completed run_921970da",
    "#2 http_accepted 200 run_921970da",
    "#1 http_recv ssot-gen"
  ]
}
```

## 미충족 / 관찰된 변형

1. **session_id 두 dispatch 사이에 다름** (`677c7e23…` vs `2c062565…`).
   Task 설명은 "same session_id" 를 기대했지만 코드 동작은 "reset cleanly per
   workflow change" (설명에 명시된 acceptable 분기). architecturally 문제 없음 —
   같은 process(=20616) 가 두 session 모두 처리.

2. **rtl-gen run 이 budget(300 s + 추가 9 분 + 추가 5 분) 안에 terminal 도달 못함**.
   - LLM call 진행 로그 (sample): `731d… 23 190 ms`, `155f09… 130 488 ms`
   - 전체 30분 이상 hang. worker process alive 유지 (%CPU 0.5–3.1, STAT `SN`).
   - 책임 경계: backend worker (5601) 정상 동작 + 외부 deepseek-v4-pro / glm-5.1
     호출이 매우 느리거나 stalled. atlas_ui / 프론트 / single-worker 라우팅과는 무관.

3. **이번 ssot-gen run (`855ae954…`) 에 매칭되는 llm_calls 0 건**.
   - 동일 시간대 ssot-gen llm_calls 는 다른 ip_id (`84b03a34…`, `68dc97a2…`)
     로만 적힘 — 외부에서 별도 ssot dispatch가 와서 atlas_ui-spawn worker 가
     처리한 것 (runs=3 의 일부).
   - 이번 dispatch 의 ssot-gen llm_calls 에 run_id 가 안 박힘 (workflow tag는
     박힘). Task #20 가 workflow tag 는 고쳤지만 run_id 연결은 별도 이슈로 남음.
     → followup ticket 권장.

## 외부 12-worker fleet 자동 spawn 안 됨 (재확인)

```
$ for p in 5621 5622 5624; do lsof -nP -iTCP:$p -sTCP:LISTEN; done
5621: pid=84335   ← 사용자 외부 fleet (atlas_ui 재기동 전부터 존재)
5622: pid=84336
5624: pid=84338
```

atlas_ui spawn 로그에 5621–5632 spawn 흔적 없음. dispatch 가 5601 로만 갔다는
것은 chat trace `run_921970da`, `run_66e144e1` 양쪽 모두 5601 worker 의 run_id
형식과 일치하고, /health.runs 카운트가 5601 worker 에서만 증가하는 것으로 확인.

## 첨부

- `/tmp/single_main_loop_step3_ssot.png` — ssot 완료 직후 screenshot (458 KB)
- `/tmp/single_main_loop_step4_rtl.png` — rtl 실행 중 screenshot (173 KB)
- atlas_ui log: `.session/canonical_atlas_ui/atlas_ui.log`

## 결론

**아키텍처 PASS**: ATLAS_SINGLE_MAIN_LOOP=1 → atlas_ui 가 단일 main-loop worker
를 spawn → 그 worker(`pid=20616`, --all-workflows) 가 ssot-gen 과 rtl-gen 을
모두 같은 프로세스에서 순차 처리. worker PID 가 두 dispatch 사이 불변임을 확인 (20:23
elapsed, 두 run 모두 처리).

**Followup 권장**:
- ssot-gen run_id → llm_calls.run_id 연결 누락 (Task #20 의 후속).
- rtl-gen end-to-end 완주 확인 (외부 LLM latency 변동성 때문에 별도 budget 가능).

## 관련 commit

- `1b1c3906d` feat(ui): atlas_ui spawns single main-loop worker when exec_mode=single-worker  ← spawn 로직 도입 (원본 bug 포함)
- `52ed4e538` fix(api): cap dispatch prompt at 100k chars + correct single-worker main.py path  ← `SOURCE_ROOT/main.py` → `HERE/main.py` 수정
