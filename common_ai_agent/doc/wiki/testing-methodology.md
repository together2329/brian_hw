# ATLAS 테스트 방법론 — "green-while-broken"을 막는 4층 구조

> 핵심 교훈(2026-05-30, 비싸게 배움): **빌드/타입/유닛이 전부 green이어도 실제 앱은 흰화면·무응답일 수 있다.** 조각 테스트는 "부품 OK"만 보장하지, "사용자가 실제로 쓸 수 있다"를 보장하지 않는다. 그래서 **최상층(실브라우저 E2E)** 이 반드시 필요하다.

## 테스트 4층 (피라미드)

| 층 | 도구 | 무엇을 검사 | 어디서 실행 | 구조적으로 **못 잡는** 것 |
|---|---|---|---|---|
| 1. 타입 | `npx tsc --noEmit` | 타입 정합성 | **코드 실행 안 함** | 런타임·렌더·배선·값 |
| 2. 유닛/스모크 | `npx vitest run` | 컴포넌트 로직·마운트 | **jsdom (가짜 DOM)** | 실브라우저·실WS·실번들·CSS레이아웃·인증·Tauri |
| 3. 빌드 | `npm run build` | 번들이 만들어지나 | **컴파일만** | 번들이 **실제로 렌더되는지** |
| 4. **E2E** | **Playwright (headless Chromium) + 진짜 백엔드** | **전체 흐름**: 로드→로그인→화면 렌더→입력→응답 | **진짜 브라우저 + 진짜 서버** | (1~3이 놓친 그 층을 메움) |

**1~3은 전부 green이어도 4가 빨강일 수 있다** = green-while-broken. 실제로 이번에 그랬다:
- 흰화면 = dist 미빌드/캐시 (번들 서빙) → tsc/vitest/build는 통과, **실브라우저만 잡음**.
- "무응답" = `/ws/agent` IPC 전달 깨짐 → 유닛은 통과(jsdom엔 실 WS 없음), **실브라우저 WS 프레임만 잡음**.
- 왼쪽레일 사라짐 = `effLeftW` 게이트(레이아웃) → render-smoke(mount-only)는 통과, **실 DOM만 잡음**.

## 각 층이 잡는 버그 클래스
- **tsc**: 타입 불일치, 시그니처 깨짐. (예: `as any` 제거로 드러난 `activeNamespace` 누락 — cast가 가린 런타임 undefined.)
- **vitest**: 순수 로직, 디스패치 배선(단 **실제로 dispatch를 exercise**하는 테스트여야 함; mount-only 스모크는 stub도 통과시켜 위험 → submitMsg stub 사고).
- **build**: import/번들 에러, 절대경로 이식성.
- **E2E**: 흰화면, 무응답, 레이아웃, 인증, 자산 404, Tauri parity — **사용자가 실제로 겪는 것**.

## 비유
tsc/vitest/build = 재료·레시피·플레이팅 점검. **E2E = 손님이 실제로 주문해서 먹고 맛있다고 확인.** 앞쪽만 믿으면 "다 됐는데 손님은 못 먹는" 상태가 나온다.

## 규칙 (이걸로 사고 재발 차단)
1. **프론트 컷오버/서빙 기본값 flip 전에는 반드시 E2E green 확인.** "build 됐으니 된다" 금지.
2. **버그마다 회귀 테스트 추가** ([[feedback_regression_test_per_bug]]). 버그 클래스에 맞는 층 선택:
   - undefined-name/런타임 NameError류 → bytecode `co_names` 스캔 또는 소스 가드 (예: `tests/test_slash_handlers_emit_scope.py`).
   - 입력/응답/렌더류 → **E2E** (실브라우저).
3. **mount-only 스모크를 "동작 검증"으로 착각하지 말 것** — 반드시 동작을 exercise(dispatch 실행, 입력 전송)하는 테스트로.
4. 백엔드 IPC/입력경로 변경(특히 병행-에이전트 merge)은 **라이브 "hi" 응답 스모크** 후에만 신뢰 ([[project_merge_broke_prompt_delivery]]).
5. **TODO/worker loop 변경은 state만 보지 말고 prompt delivery까지 본다.** `get_continuation_prompt()`가 문자열을 만드는 테스트와,
   그 문자열이 실제 다음 LLM input에 들어가는 `react_loop` 테스트는 별개다. Atlas/web chat mode와 Textual TUI가 같은
   상태 전이를 같은 방식으로 이어가는지도 확인한다. 상세 매트릭스: [[todo-loop-verification-hardening-20260608]].

## 자동화 (한 줄)
```bash
scripts/atlas_vite_e2e_verify.sh      # tsc → vitest → build → 서버(:3019) → 실브라우저 e2e; exit 0 = ✅ VERIFIED
```
- 실브라우저로: 렌더(#root 채움·자산404 0·에러배너 없음) → 로그인 → workspace → "hi" → `/ws/agent` `agent_received`+`agent_accepted{ok:true}`(+워커 `gpt-5.5` 실행/토큰) 핸드셰이크.
- 테스트 포트라 실행 중인 `:3000`을 안 건드림. 스크린샷 `/tmp/atlas_e2e_shots/`.
- 상세 런북: [[atlas-vite-e2e-verification]].

관련: [[project_ts_vite_tauri_cutover]] · [[project_vite_env_stale_build]] · [[project_silent_pass_exposure]](백엔드판 green-while-broken).
