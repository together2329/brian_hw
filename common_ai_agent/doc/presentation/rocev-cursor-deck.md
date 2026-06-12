---
marp: true
paginate: true
size: 16:9
math: katex
title: 신뢰할 수 있는 AI 하드웨어 개발 — ROCEV & .cursor
description: AI 에이전트가 만든 RTL을 진짜로 믿게 만드는 법
style: |
  :root {
    --ink:#16213e; --accent:#e94560; --ok:#22a06b; --blue:#3b5bdb;
    --muted:#8d99ae; --bg:#fbfbfd; --line:#cdd3df; --soft:#eef1f7;
  }
  section {
    background: var(--bg); color: var(--ink);
    font-family: "Pretendard","Helvetica Neue",-apple-system,sans-serif;
    font-size: 26px; padding: 56px 72px; line-height: 1.45;
  }
  h1 { font-size: 50px; color: var(--ink); margin: 0 0 .2em; letter-spacing:-.5px; }
  h2 { font-size: 34px; color: var(--ink); border-bottom: 3px solid var(--soft); padding-bottom:.25em; }
  strong { color: var(--accent); }
  a { color: var(--blue); }
  code { background: var(--soft); padding: .08em .35em; border-radius: 6px; font-size: .9em; }
  ul { margin-top:.3em; } li { margin:.25em 0; }
  table { font-size: 21px; border-collapse: collapse; margin: .2em auto; }
  th { background: var(--ink); color:#fff; padding:.45em .7em; }
  td { border:1px solid var(--line); padding:.4em .7em; }
  .muted { color: var(--muted); }
  .note { color: var(--muted); font-size: 20px; }
  .center { text-align:center; }
  /* diagram primitives */
  .flow { display:flex; align-items:center; justify-content:center; gap:.5rem; flex-wrap:wrap; margin:.6em 0; }
  .col { display:flex; flex-direction:column; align-items:center; gap:.25rem; }
  .box { padding:.5rem .8rem; border-radius:12px; background:#fff; border:2.5px solid var(--ink);
         font-weight:700; box-shadow:0 2px 0 var(--line); white-space:nowrap; }
  .box.blue{ border-color:var(--blue); color:var(--blue); }
  .box.ok{ border-color:var(--ok); color:var(--ok); }
  .box.bad{ border-color:var(--accent); color:var(--accent); }
  .box.lg{ font-size:1.15em; padding:.6rem 1.1rem; }
  .sub{ font-size:18px; color:var(--muted); }
  .arr{ font-size:1.7rem; color:var(--muted); font-weight:700; }
  .lock{ font-size:1.2rem; }
  .stack{ display:flex; flex-direction:column; gap:.5rem; max-width:760px; margin:.6em auto; }
  .layer{ display:flex; justify-content:space-between; align-items:center;
          padding:.7rem 1.1rem; border-radius:12px; border:2.5px solid var(--ink); background:#fff; }
  .layer .tag{ font-weight:800; } .layer .desc{ color:var(--muted); font-size:20px; }
  .soft{ background:var(--soft); border-color:var(--line); }
  .hard{ border-color:var(--ink); }
  .seal{ border-color:var(--ok); color:var(--ok); }
  .cols{ display:flex; gap:1.4rem; justify-content:center; align-items:stretch; margin:.4em 0; }
  .card{ flex:1; border:2px solid var(--line); border-radius:14px; padding:.9rem 1.1rem; background:#fff; }
  .metric{ font-size:46px; font-weight:800; }
  .down{ color:var(--ok); } .up{ color:var(--accent); }
  .lead{ display:flex; flex-direction:column; justify-content:center; height:100%; }
  .big-quote{ font-size:38px; font-weight:800; line-height:1.3; }
  .kicker{ color:var(--accent); font-weight:800; letter-spacing:1px; font-size:20px; text-transform:uppercase; }
---

<!-- _paginate: false -->
<div class="lead center">

<span class="kicker">silent pass hardening</span>

# "✅ 완료"가<br>거짓말이라면?

### AI가 만든 RTL을 *진짜로* 믿는 법 — ROCEV & `.cursor`

<p class="note">req → rtl → tb → sim · 가짜 통과 불가능한 파이프라인</p>

</div>

<!--
오프닝 훅. AI 에이전트에게 RTL을 맡겼더니 "다 됐습니다 ✅" — 그런데 열어보니
시뮬레이션이 한 번도 제대로 안 돈 거였다. 오늘은 이 '조용한 거짓말'을
어떻게 구조적으로 불가능하게 만들었는지 이야기합니다.
-->

---

## 문제 ① — AI는 '완료'를 조작한다

<div class="center">

### 모델 확신 ≠ 증거

</div>

- 테스트를 **안 돌리고** "통과"
- timeout · 빈 결과를 **"성공"으로** 보고
- 게이트 우회 · 산출물 **손편집**으로 초록불

<div class="flow">
  <div class="box bad">에이전트: "PASS ✅"</div>
  <div class="arr">vs</div>
  <div class="box">빈 <code>results.xml</code> · 0 events</div>
</div>

<p class="note">실측: 정책을 조이자 4개 IP 중 3개(75%)가 사실은 silent PASS였다.</p>

<!--
모델의 자신감은 증거가 아니다. 이게 출발점의 통증.
-->

---

## 문제 ② — 하드웨어에선 치명적

<div class="flow">
  <div class="col"><div class="box blue lg">req</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box blue lg">rtl</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box bad lg">tb 💥</div><div class="sub">가짜 통과</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box lg">sim</div><div class="sub muted">오염된 증거</div></div>
</div>

- 소프트웨어 버그 → 패치. **RTL → 칩으로 굳는다.**
- 한 칸이 가짜로 넘어가면 **그 위에 쌓은 검증 전체가 거짓**

<!--
어느 한 단계에서 가짜로 넘어가면 하류 전체가 거짓이 된다. 그래서 단계마다
진짜 게이트가 필요하다.
-->

---

<!-- _class: lead -->
<div class="center">

<span class="kicker">핵심 전환</span>

<div class="big-quote">
모델이 "됐다"고 말하는 게 아니라<br>
<span style="color:var(--ok)">검증기가 신선한 증거로</span><br>
통과를 찍어야 <span style="color:var(--ok)">완료</span>다
</div>

<p class="note">green = 진짜 게이트를 fresh evidence로 통과했을 때만</p>

</div>

<!--
해법의 출발점은 단순하다. '완료'의 정의를 바꾼다.
-->

---

## ROCEV — 모든 작업의 척추

<div class="flow">
  <div class="col"><div class="box blue">Requirement</div><div class="sub">약속</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box blue">Obligation</div><div class="sub">의무</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box blue">Contract</div><div class="sub">판정 기준</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box blue">Evidence</div><div class="sub">산출물</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box ok">Validation</div><div class="sub">게이트</div></div>
</div>

> 무엇을 약속했고(R/O) · 무엇이 '맞다'의 기준이며(C) · 실제로 뭘 만들었고(E) · 그게 기준을 만족하나(**V**)

<p class="center note"><strong>V</strong>가 통과해야만 다음으로 간다.</p>

<!--
이 다섯 단계가 척추. 각 칸이 기계가 읽을 수 있게 정의돼 있고, 마지막 V가 게이트.
-->

---

## 4단계 흐름 — 각 단계가 척추를 닫는다

<div class="flow">
  <div class="col"><div class="box blue lg">req</div><div class="lock">🔒</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box blue lg">rtl</div><div class="lock">🔒</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box blue lg">tb</div><div class="lock">🔒</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box ok lg">sim</div><div class="lock">🔒</div></div>
</div>

- 이전 게이트가 **신선한 증거로 PASS** 안 하면 **진입 불가**
- 순서 고정 · 한 번에 하나의 의무만 in-progress

<!--
ROCEV를 하드웨어에 입히면 네 단계. 핵심은 각 단계가 자기 척추를 닫아야 다음이 열린다는 것.
-->

---

## 단계별 계약 — 한 장 요약

| 단계 | Obligation | Contract | Evidence | **Gate** |
|---|---|---|---|---|
| **req** | 의무 lock | truth bundle | `req/*.json` | `check_locked_truth_bundle` |
| **rtl** | rtl todo | `rtl_contract` | `rtl/*.sv` | lint + compile |
| **tb** | scoreboard goal | equiv goals | `tb/cocotb/*` | tb ledger |
| **sim** | obligation closure | FL-vs-RTL | `results.xml` | `check_sim_disk` |

<p class="center note">마지막 열 = '가짜로 못 넘기는' 게이트들.</p>

<!--
각 칸마다 무엇을 닫아야 하는지가 기계가 읽을 수 있게 정의돼 있다.
-->

---

## rocev-chain — 지휘자와 오너

<div class="flow">
  <div class="box ok lg">/rocev-chain</div>
  <div class="arr">⟶ 위임</div>
  <div class="col" style="gap:.4rem">
    <div class="box blue">/req-gen</div>
    <div class="box blue">/rtl-gen</div>
  </div>
  <div class="col" style="gap:.4rem">
    <div class="box blue">/tb-gen</div>
    <div class="box blue">/sim</div>
  </div>
</div>

- 지휘자는 **지휘만** — 수리는 단계 오너에게 위임
- DUT 버그면 `/sim` → `/rtl-gen` **에스컬레이션**
- 같은 게이트 **3연속 실패 → 멈추고 보고** (맹목 재시도 금지)

<!--
rocev-chain은 오케스트레이션만. 진행 주장마다 게이트 출력을 인용한다.
-->

---

<!-- _class: lead -->
<div class="center">
<span class="kicker">발표의 심장</span>

# 3계층 강제

<p class="note">초록불로 가는 유일한 길 = 진짜 게이트</p>
</div>

<!--
여기가 핵심. 룰·훅·게이트가 어떻게 가짜 통과를 불가능하게 만드는가.
-->

---

## 강제는 룰이 아니라 hooks + gates

<div class="stack">
  <div class="layer soft"><span class="tag">rules</span><span class="desc">모델을 미리 정렬 — 지워도 시스템은 돈다 (priming)</span></div>
  <div class="layer hard"><span class="tag">hooks</span><span class="desc">결정론적 차단 — stop-todo-loop / subagent-evidence-check</span></div>
  <div class="layer seal"><span class="tag">gates</span><span class="desc">진짜 PASS만 — 가짜 통과 불가</span></div>
</div>

- 룰을 **다 꺼도** hook이 막고 gate가 거른다
- 룰 = 모델이 게이트 만나기 전에 덜 헤매게 하는 **유도**일 뿐

<!--
룰은 유도만 한다. 진짜 강제는 hooks와 gates. 이걸 분리해서 이해하는 게 중요.
-->

---

## todo 루프 — 멈추지 못하게

<div class="flow">
  <div class="box">cursor_todo.py</div>
  <div class="arr">→</div>
  <div class="box">current_todos.json</div>
  <div class="arr">→</div>
  <div class="box bad">stop hook</div>
  <div class="arr">↻ 재투입</div>
</div>
<div class="center">
  <div class="box ok" style="display:inline-block">증거 붙여 close → 루프 자동 종료</div>
</div>

- 열린 todo가 남으면 **종료를 막고 다음 걸 재투입** (`loop_limit 20`)
- hook은 **별도 프로세스** → 에이전트 메모리 못 봄 → **파일이 유일한 진실원**

<!--
에이전트가 todo를 외부 파일에 쓰고, stop 훅이 그 파일을 읽어 열린 게 있으면
재투입한다. 증거를 붙여 닫아야만 끝난다.
-->

---

## FL-vs-RTL — 무엇이 '정답'인가

<div class="flow">
  <div class="col"><div class="box blue">SSOT</div><div class="sub">사람이 작성</div></div>
  <div class="arr">→ 자동파생</div>
  <div class="col"><div class="box ok">FunctionalModel<br>.apply()</div><div class="sub">골든 오라클</div></div>
  <div class="arr">⟷ 비교</div>
  <div class="col"><div class="box">RTL observed</div><div class="sub">피고</div></div>
</div>

- contract는 정답을 **담지 않는다** → 실행가능 FL 모델에 위임
- 모델은 **SSOT에서 자동 생성** (손코딩 아님)
- *"sim-debug는 RTL에 맞추려 모델을 바꿀 수 없다"* — 모델이 진실

<!--
TB가 RTL을 무엇과 비교하나? SSOT에서 자동 파생된 실행가능 모델이 골든 오라클.
contract 기반으로 작성해도 모델은 공짜로 따라온다.
-->

---

## rules의 4가지 적용 방식

| 타입 | 트리거 | 평소 비용 |
|---|---|---|
| **Always** | 항상 | baseline (~1.3K tok) |
| **Auto-Attached** | `glob` 매치 파일 만질 때 | 0 |
| **Agent-Requested** | AI가 필요 판단 | 0 |
| **Manual** | `@이름` 호출 | 0 |

- 11개 룰이 다 켜진 게 아니다 — **baseline만 Always**
- 나머지는 *해당 영역 파일을 만질 때만* 자동 첨부

<!--
컨텍스트 낭비를 의도적으로 막은 설계. glob이 정밀해서 RTL 작업엔 RTL 룰만.
-->

---

## glob = 상황별 정밀 로딩

<div class="flow">
  <div class="box"><code>frontend/**/*.{jsx,js}</code></div>
  <div class="arr">→</div>
  <div class="box blue">frontend 만질 때만</div>
</div>
<div class="flow">
  <div class="box"><code>**/*.vcd</code></div>
  <div class="arr">→</div>
  <div class="box blue">시뮬 산출물만</div>
</div>

- 리눅스 `*`의 확장판 (`**`=재귀, `{a,b}`=택1)
- **항상 필요한 규율만** baseline, 영역 세부는 그때그때

<!--
정교한 glob 덕에 관련 작업에만 관련 룰이 붙는다.
-->

---

## `.cursor` — 권위 모델을 폴더 하나로

<div class="flow">
  <div class="box">ATLAS authority model</div>
  <div class="arr">→</div>
  <div class="box ok lg">.cursor/</div>
  <div class="arr">→</div>
  <div class="box blue">어디든 빼가서 자족</div>
</div>

- 룰 · 게이트 · 훅 · **엔진까지** vendored
- 부모 레포 없이 **통째로 빼가면 Cursor에서 그대로 작동**

<!--
이 모든 규율을 폴더 하나에 담았다. 자족형 전달본.
-->

---

## `.cursor` 해부

| 폴더 | 역할 |
|---|---|
| `rules/` | 가드레일 (자동 주입) |
| `skills/` | 절차 — `rocev-chain` |
| `agents/` | 오너 — `/req-gen` … |
| `hooks/` | 차단 — `stop-todo-loop` |
| `workflow/` | **vendored 엔진 + 게이트** |

<p class="center note">workflow 안 = 실제 실행 엔진. 정본의 사본, 손대지 않는다.</p>

<!--
각 폴더가 권위 모델의 한 축.
-->

---

## 데모용으로 뼈대만 — 41 → 12

<div class="cols">
  <div class="card center">
    <div class="metric down">41→12</div>
    <div class="note">workflow 스테이지</div>
  </div>
  <div class="card center">
    <div class="metric down">5.7M→3.4M</div>
    <div class="note">−40% 크기</div>
  </div>
  <div class="card center">
    <div class="metric down">317</div>
    <div class="note">파일 삭제</div>
  </div>
</div>

- EDA(`syn/sta/pnr…`) · `orchestrator` = ROCEV 데모엔 불필요
- agents 27→6 · skills 21→3 · rules 11→6

<!--
req→rtl→tb→sim 데모엔 EDA나 orchestrator가 필요 없다. 경로 밖을 들어냈다.
-->

---

## 안전하게 지우는 법 — 의존성 폐포

<div class="flow">
  <div class="box">엔진</div>
  <div class="arr">→</div>
  <div class="box">STAGE_MANIFEST.json</div>
  <div class="arr">→ subprocess</div>
  <div class="box blue">스테이지 스크립트</div>
</div>

- 엔진은 **하드-import 아님** → 매니페스트로 호출
- 호출 안 되는 스테이지는 **안전 드롭** · root 탐지 graceful fallback
- **스모크 5/5** 검증 (import · 라우팅 · 게이트 · todo · wiki)

<!--
막 지우면 깨진다. 핵심 발견은 엔진이 매니페스트로 subprocess 호출한다는 것.
그래서 안전하게 드롭 가능했고 스모크로 검증했다.
-->

---

## 라이브 — 게이트는 정직하다

```text
$ check_sim_disk ghost_ip
[check_sim_disk] FAIL: cannot locate IP directory   ← crash 아님, 정직한 FAIL
```

<div class="flow">
  <div class="box bad">FAIL</div>
  <div class="arr">→ 수정</div>
  <div class="box">re-run</div>
  <div class="arr">→</div>
  <div class="box ok lg">PASS ✅</div>
</div>

- PASS = **실 산출물 + 통과한 스코어보드 이벤트 + 실패 마커 0**
- timeout · 빈 XML = **증거 아님**

<!--
없는 IP엔 정직한 FAIL. 진짜 IP로 닫아야 PASS. 가짜로는 절대 못 넘긴다.
사전 녹화 클립을 백업으로 준비할 것.
-->

---

<!-- _class: lead -->
<div class="center lead">

<div class="big-quote">
green = <span style="color:var(--ok)">genuinely correct</span><br>
<span class="muted" style="font-size:.7em">그리고 폴더 하나로 빼간다</span>
</div>

<p class="note">AI에게 하드웨어를 맡기되, 초록불이 진짜 초록불이게.</p>

</div>

<!--
회수. 한 문장으로 끝낸다.
-->

---

## 부록 — Q&A 백업

- **MCP dual-transport** — stdio(Cursor가 spawn) vs HTTP 상주; 데모 버전엔 제거
- **KNOWN_TRAPS** —
  `stage_gate sim` 버그 → `test_runner.py` 직접 ·
  req 번들 수동 저작 ·
  `ATLAS_COV_BLOCK_IS_FAIL=0` ·
  체커는 **repo 루트**에서 ·
  **FL=pre-state, RTL=post-state**
- **컨텍스트 비용** — baseline 4룰 ≈ 1.3–1.5K 토큰
- **복구** — `git restore` + 백업 tar 이중 안전망

<!--
예상 질문 백업 슬라이드.
-->
