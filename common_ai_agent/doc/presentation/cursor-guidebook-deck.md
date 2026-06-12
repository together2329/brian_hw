---
marp: true
paginate: true
size: 16:9
title: .cursor 가이드북 — rules · skills · hooks · agents
description: 슬림 .cursor 팩의 실제 규율 컴팩트 레퍼런스
style: |
  :root {
    --ink:#16213e; --accent:#e94560; --ok:#22a06b; --blue:#3b5bdb;
    --muted:#8d99ae; --bg:#fbfbfd; --line:#cdd3df; --soft:#eef1f7;
  }
  section {
    background: var(--bg); color: var(--ink);
    font-family: "Pretendard","Helvetica Neue",-apple-system,sans-serif;
    font-size: 24px; padding: 48px 60px; line-height: 1.4;
  }
  h1 { font-size: 46px; color: var(--ink); margin: 0 0 .15em; letter-spacing:-.5px; }
  h2 { font-size: 30px; color: var(--ink); border-bottom: 3px solid var(--soft);
       padding-bottom:.2em; margin:0 0 .35em; }
  strong { color: var(--accent); }
  code { background: var(--soft); padding: .06em .3em; border-radius: 5px; font-size: .86em; }
  ul { margin:.2em 0; } li { margin:.15em 0; }
  table { font-size: 18px; border-collapse: collapse; margin:.15em 0; width:100%; }
  th { background: var(--ink); color:#fff; padding:.4em .6em; text-align:left; }
  td { border:1px solid var(--line); padding:.32em .6em; vertical-align:top; }
  td code { font-size:.82em; }
  .muted{ color:var(--muted); } .note{ color:var(--muted); font-size:18px; }
  .center{ text-align:center; }
  .kicker{ color:var(--accent); font-weight:800; letter-spacing:1px; font-size:18px; text-transform:uppercase; }
  .flow{ display:flex; align-items:center; justify-content:center; gap:.45rem; flex-wrap:wrap; margin:.4em 0; }
  .col{ display:flex; flex-direction:column; align-items:center; gap:.2rem; }
  .box{ padding:.4rem .7rem; border-radius:11px; background:#fff; border:2.5px solid var(--ink);
        font-weight:700; box-shadow:0 2px 0 var(--line); white-space:nowrap; }
  .box.blue{ border-color:var(--blue); color:var(--blue); }
  .box.ok{ border-color:var(--ok); color:var(--ok); }
  .box.bad{ border-color:var(--accent); color:var(--accent); }
  .sub{ font-size:16px; color:var(--muted); }
  .arr{ font-size:1.4rem; color:var(--muted); font-weight:700; }
  .cols{ display:flex; gap:1rem; }
  .card{ flex:1; border:2px solid var(--line); border-radius:13px; padding:.7rem .9rem; background:#fff; }
  .card .t{ font-weight:800; font-size:21px; } .card .d{ color:var(--muted); font-size:18px; }
  .pill{ display:inline-block; font-size:15px; font-weight:700; padding:.05em .5em; border-radius:20px; }
  .always{ background:#e7efff; color:var(--blue); } .auto{ background:#eafbf2; color:var(--ok); }
  .lead{ display:flex; flex-direction:column; justify-content:center; height:100%; }
  .big{ font-size:36px; font-weight:800; line-height:1.3; }
---

<!-- _paginate: false -->
<div class="lead center">

<span class="kicker">slim pack reference</span>

# `.cursor` 가이드북

### rules · skills · hooks · agents — 컴팩트 레퍼런스

<p class="note">req → rtl → tb → sim · 증거 없이 완료 없음</p>

</div>

<!--
슬림 .cursor 팩의 실제 규율을 한 권으로. 개념이 아니라 "무엇이 들어있고 각각 뭘 하나".
-->

---

## 4기둥 — 한 장 개관

<div class="cols">
  <div class="card"><div class="t">rules</div><div class="d">모델을 미리 정렬 (prime)</div><div class="note">6개 · .mdc</div></div>
  <div class="card"><div class="t">hooks</div><div class="d">결정론적 차단 (block)</div><div class="note">5개 · .py</div></div>
  <div class="card"><div class="t">agents</div><div class="d">스테이지 소유 (own)</div><div class="note">6개 · .md</div></div>
  <div class="card"><div class="t">skills</div><div class="d">실행 절차 (procedure)</div><div class="note">3개</div></div>
</div>

<p class="center" style="margin-top:.5em">
<span class="box ok" style="display:inline-block">모두 한 목적 → "초록불 = 진짜 게이트 통과"</span>
</p>

<!--
rules는 유도, hooks는 강제, agents는 오너, skills는 절차. 네 축이 한 목적에 봉사한다.
-->

---

## rules (6) — 가드레일

| 룰 | 적용 | 강제하는 것 |
|---|---|---|
| `00-project-core` | <span class="pill always">Always</span> | 레포 정체성·디렉토리 맵·scope 규율 |
| `80-todo-evidence` | <span class="pill always">Always</span> | todo=증거계약, **증거로만 완료** |
| `85-rocev-todo-loop` | <span class="pill always">Always</span> | ROCEV 척추 + `cursor_todo→current_todos.json` |
| `30-hardware-workflow` | <span class="pill auto">Auto</span> | SSOT=권위·가짜PASS금지·Verilog-2001(`always_ff/logic/for` 금지)·HDL출력 truncate 금지 |
| `50-generated-artifacts` | <span class="pill auto">Auto</span> | 산출물=증거, **손편집 금지**, 신선도 |
| `90-rtl-to-signoff` | <span class="pill auto">Auto</span> | `STAGE_MANIFEST` 라우팅, 게이트 우회 금지 |

<p class="note"><b>Always 3</b>(항상 ≈baseline) · <b>Auto 3</b>(glob 매치 파일 만질 때만)</p>

<!--
항상 켜지는 건 정체성·증거·ROCEV 3개. 하드웨어/산출물/signoff 세부는 해당 파일 건드릴 때만.
-->

---

## hooks (5) — 강제의 이빨

| 훅 | 이벤트 | 막는 것 (loop_limit) |
|---|---|---|
| `guard-shell` | beforeShell | HDL출력 `\| head/tail/grep` **deny** · live LLM·위험 git **ask** |
| `protect-generated-artifacts` | preToolUse | `sim/ verify/ cov/ .session/ current_todos` 편집 **ask** |
| `subagent-evidence-check` | subagentStop (×2) | 증거 없는 subagent "완료" **차단** |
| `stop-todo-loop` | stop (×20) | open todo 남으면 **재투입** |
| `stop-loop-check` | stop (×1) | 변경 파일 기반 테스트/재생성 **리마인드** |

<p class="note">룰을 다 꺼도 작동하는 <b>결정론적 강제</b> — silent-PASS의 모든 판본을 차단.</p>

<!--
hooks가 진짜 강제다. 증거 흔적(PASS/FAIL/rc/results.xml) 없으면 subagent도 멈출 수 없고,
HDL 출력을 truncate하는 파이프는 아예 deny.
-->

---

## agents (6) — 소유 지도

<div class="flow">
  <div class="box ok">/rocev-chain</div><div class="arr">⟶</div>
  <div class="box blue">/req-gen</div><div class="arr">→</div>
  <div class="box blue">/fl-model-gen</div><div class="arr">→</div>
  <div class="box blue">/rtl-gen</div><div class="arr">→</div>
  <div class="box blue">/tb-gen</div><div class="arr">→</div>
  <div class="box blue">/sim</div>
</div>

| 에이전트 | 소유 | 핵심 규율 |
|---|---|---|
| `rocev-chain` | 지휘 | 위임만 · 3연속 실패 멈춤·보고 |
| `req-gen` | `req/` | **SSOT anchor 필수** · gate FAIL이 산출물 |
| `fl-model-gen` | `model/`+equiv | RTL에 맞춰 **모델 수정 금지** |
| `rtl-gen` | `rtl/ list/` | `rtl_blocked`→ssot-gen/human |
| `tb-gen` | `tb/`+scoreboard | **FunctionalModel과 비교** · mock PASS 금지 |
| `sim` | `sim/` 증거 | 출력 truncate·PASS 조작 금지 |

<p class="note">전부 <code>readonly:false</code> → subagent-evidence-check 강제 대상.</p>

<!--
각 단계 오너가 자기 폴더를 소유하고, 모두 증거 의무를 진다.
-->

---

## skills (3) — 실행 절차

<div class="cols">
  <div class="card">
    <div class="t">rocev-chain</div>
    <div class="d">req→rtl→tb→sim 4단계 ROCEV. 단계별 명령 + <code>KNOWN_TRAPS.md</code></div>
  </div>
  <div class="card">
    <div class="t">rtl-to-signoff</div>
    <div class="d">DV+EDA 전체 signoff 러너. profiles·<code>WorkflowStageEngine</code></div>
  </div>
  <div class="card">
    <div class="t">ip-wiki</div>
    <div class="d">IP별 wiki <code>init/log/page/check</code>. append-only 히스토리</div>
  </div>
</div>

- **rocev-chain** = 데모의 주경로 · **rtl-to-signoff** = 풀 클로저 · **ip-wiki** = 매 스테이지 기록
- 셋 다 "정본을 실행, 재구현 금지" 원칙

<!--
skills는 따라 읽는 레시피. rocev-chain이 req→rtl→tb→sim의 운영 매뉴얼.
-->

---

## 이 모든 걸 묶는 척추

<div class="flow">
  <div class="col"><div class="box blue">Requirement→Obligation</div><div class="sub">req-gen</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box blue">Contract</div><div class="sub">SSOT/fl-model-gen</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box blue">Evidence</div><div class="sub">rtl/tb/sim</div></div>
  <div class="arr">→</div>
  <div class="col"><div class="box ok">Validation</div><div class="sub">gates</div></div>
</div>

```text
rules(가드) + skills(절차) + agents(오너)  →  게이트 통과해야 다음
                                           ↓
hooks: open todo 멈춤 금지 / 증거 없는 완료 차단 / 산출물 편집 ask
```

<p class="center note">네 축의 교차점 = "가짜로는 초록불에 못 간다".</p>

<!--
rules/skills/agents/hooks가 ROCEV 척추 위에서 어떻게 맞물리는지.
-->

---

<!-- _class: lead -->
<div class="center lead">

<span class="kicker">공통 계율</span>

<div class="big">증거 없이 완료 없음</div>

<div style="margin-top:.5em; text-align:left; display:inline-block">

- 모델 확신 ≠ 증거 — verdict 라인을 인용
- 산출물 손편집 금지 → **소유 명령 재생성**
- 옛 초록 JSON은 **stale** (RTL/TB/SSOT 변경 후)
- gate FAIL 출력이 곧 산출물 — **verbatim**

</div>
</div>

<!--
네 축을 관통하는 한 줄. 모든 rule·hook·agent가 이걸 강제한다.
-->

---

## 치트시트

| 용도 | 명령 |
|---|---|
| todo | `cursor_todo.py {add\|start\|done}` → `current_todos.json` |
| req 게이트 | `check_locked_truth_bundle.py` · `stage_gate.py` |
| sim 실행 | `<ip>/tb/cocotb/test_runner.py` 직접 *(stage_gate sim 버그)* |
| sim 게이트 | `check_sim_disk.py` · `check_truth_coverage.py` |
| wiki | `ip_wiki.py log/check` (매 스테이지) |

- 모든 체커 **repo 루트**에서 실행 · 신규 IP `ATLAS_COV_BLOCK_IS_FAIL=0`
- req 번들 **수동 저작** (생성기 없음 — `*_cx1/req/` 템플릿)

<!--
실전에서 바로 쓰는 명령 모음. KNOWN_TRAPS 보정 반영.
-->

---

## 부록 — KNOWN_TRAPS 5

1. **체커는 repo 루트에서** — IP 디렉토리서 돌리면 경로 이중첩
2. **sim은 `test_runner.py` 직접** — `stage_gate sim`은 IP명을 소스로 넘기는 버그(전 IP FAIL)
3. **신규 IP coverage** — `ATLAS_COV_BLOCK_IS_FAIL=0` 없으면 rc=3로 sim 막힘
4. **req 번들 수동 저작** — scaffold 생성기 없음, 기존 `*_cx1/req/`가 템플릿
5. **FL=pre-state, RTL=post-state** — registered flag는 `output_rules`에서 `count±1`로

<p class="note">전부 10-IP 실전에서 수확. 안 읽으면 같은 함정 반복.</p>

<!--
Q&A 백업: 실전 함정. rocev-chain/KNOWN_TRAPS.md 전체 참조.
-->
