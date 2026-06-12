---
marp: true
paginate: true
size: 16:9
title: Cursor 활용법 — AI가 쓴 RTL을 믿게 만드는 워크플로
description: 신뢰 질문 → ROCEV → 실질 workflow → Cursor 구현 → Codex/Claude Code 일반화
style: |
  :root {
    --ink:#16213e; --accent:#e94560; --ok:#22a06b; --blue:#3b5bdb;
    --muted:#8d99ae; --bg:#fbfbfd; --line:#cdd3df; --soft:#eef1f7; --codebg:#0f1530;
  }
  section {
    background: var(--bg); color: var(--ink);
    font-family: "Pretendard","Helvetica Neue",-apple-system,sans-serif;
    font-size: 24px; padding: 46px 58px; line-height: 1.4;
  }
  h1 { font-size: 44px; color: var(--ink); margin: 0 0 .15em; letter-spacing:-.5px; }
  h2 { font-size: 30px; color: var(--ink); border-bottom: 3px solid var(--soft);
       padding-bottom:.2em; margin:0 0 .35em; }
  h3 { font-size: 27px; margin:.2em 0; }
  strong { color: var(--accent); }
  code { background: var(--soft); padding:.05em .3em; border-radius:5px; font-size:.84em; }
  pre { background: var(--codebg); color:#e8ecf7; padding:.65em .95em; border-radius:10px;
        font-size:16px; line-height:1.4; overflow:auto; margin:.35em 0; }
  pre code { background:none; color:inherit; padding:0; font-size:16px; }
  ul{ margin:.2em 0; } li{ margin:.16em 0; }
  table{ font-size:18px; border-collapse:collapse; width:100%; margin:.15em 0; }
  th{ background:var(--ink); color:#fff; padding:.38em .6em; text-align:left; }
  td{ border:1px solid var(--line); padding:.32em .6em; vertical-align:top; }
  td code{ font-size:.82em; }
  .muted{ color:var(--muted); } .note{ color:var(--muted); font-size:18px; }
  .center{ text-align:center; }
  .kicker{ color:var(--accent); font-weight:800; letter-spacing:1px; font-size:18px; text-transform:uppercase; }
  .flow{ display:flex; align-items:center; justify-content:center; gap:.4rem; flex-wrap:wrap; margin:.4em 0; }
  .box{ padding:.38rem .7rem; border-radius:11px; background:#fff; border:2.5px solid var(--ink);
        font-weight:700; box-shadow:0 2px 0 var(--line); white-space:nowrap; }
  .box.blue{ border-color:var(--blue); color:var(--blue); }
  .box.ok{ border-color:var(--ok); color:var(--ok); }
  .box.bad{ border-color:var(--accent); color:var(--accent); }
  .arr{ font-size:1.4rem; color:var(--muted); font-weight:700; }
  .lead{ display:flex; flex-direction:column; justify-content:center; height:100%; }
  .big{ font-size:36px; font-weight:800; line-height:1.3; }
  .tag{ display:inline-block; font-size:15px; font-weight:700; padding:.05em .55em; border-radius:20px; background:var(--soft); color:var(--blue); }
---

<!-- _paginate: false -->
<div class="lead center">

<span class="kicker">cursor 활용법 세미나</span>

# AI가 쓴 RTL을<br>믿게 만드는 워크플로

### 신뢰 질문 → ROCEV → 실질 workflow → Cursor 구현 → 어디서나

<p class="note">requirement · obligation · contract · evidence · validation</p>

</div>

<!--
세미나의 진짜 주제는 Cursor 사용법이지만, 그 전에 "왜 이렇게 써야 하나"를 먼저.
-->

---

## 질문 하나로 시작

<div class="center">

### "AI로 작성한 RTL을 믿을 수 있을까?"

</div>

<div class="flow">
  <div class="box bad">에이전트: "테스트 통과 ✅"</div>
  <div class="arr">vs</div>
  <div class="box">실제 <code>results.xml</code> — 비어 있음</div>
</div>

- 실측: 정책을 조이자 **4 IP 중 3개(75%)가 silent PASS**였다
- 오늘의 진짜 주제 → **어떻게 *믿게* 만드는가**

<!--
AI에게 RTL을 맡기면 "다 됐다"고 한다. 그런데 시뮬이 한 번도 제대로 안 돈 경우가 태반.
-->

---

## 신뢰의 빈틈

<div class="center big" style="margin:.3em 0">모델 확신 ≠ 증거</div>

- "다 됐다"는 모델의 **말** — 우리가 믿을 건 **검증기의 출력**
- 가짜 통과의 3가지 얼굴:
  - 테스트 안 돌리고 "통과"
  - timeout · 빈 결과를 "성공"으로 보고
  - 게이트 우회 · 산출물 손편집

<p class="note">소프트웨어는 패치, RTL은 칩으로 굳는다 → 가짜 통과 비용이 비대칭.</p>

<!--
신뢰의 단위를 '모델의 말'에서 '검증기 출력'으로 옮겨야 한다.
-->

---

## 그래서 이 순서가 필요하다

<div class="flow">
  <div class="box blue">Requirement</div><div class="arr">→</div>
  <div class="box blue">Obligation</div><div class="arr">→</div>
  <div class="box blue">Contract</div><div class="arr">→</div>
  <div class="box blue">Evidence</div><div class="arr">→</div>
  <div class="box ok">Validation</div>
</div>

| 단계 | 하는 일 | 왜 |
|---|---|---|
| Requirement | 자연어 약속 | 사람의 의도 |
| Obligation | 원자·기계검증 의무 | 모호함 제거 → 채점 가능 |
| Contract | 판정 기준 | "맞다"의 정의 |
| Evidence | 산출물 | 실제로 만든 것 |
| Validation | 게이트 | 기준 만족 여부 |

<p class="note">왜 요구→RTL 직행이 아닌가: 자연어는 기계가 채점 못 한다. 각 단계가 다음을 채점 가능하게 정규화.</p>

<!--
ROCEV는 "요구를 기계검증 가능한 약속으로 정규화한 뒤 증거를 닫는" 척추.
-->

---

## ROCEV 구체 예시 — `pulse_counter`

| 요소 | 실제 값 |
|---|---|
| **Requirement** | "`pulse_in` rising마다 `count`+1; MAX 도달 시 다음 펄스에 0 wrap + `ovf` 1-cycle" |
| **Obligation** | `OBL_COUNT_INCR` (temporal): rising(pulse)⇒count[t]=count[t-1]+1 (mod 2ᴺ)<br>`OBL_OVF_PULSE`: MAX→0 전이 시 ovf 정확히 1-cycle |
| **Contract** | `model_api: FunctionalModel.apply` — FL이 (pulse,rst)→(count,ovf) 계산<br>pass: "RTL observed == FL expected, 매 cycle" · `ssot_anchor: counter.width` |
| **Evidence** | `tb/cocotb/test_pulse_counter.py` 스코어보드 · `sim/results.xml`<br>`sim/scoreboard_events.jsonl` (fl_expected vs rtl_observed) |
| **Validation** | `check_sim_disk.py` PASS (실산출물+≥1 passing+0 fail)<br>`check_truth_coverage.py` (두 OBL이 coverage_refs에 커버) |

<p class="note">요구 한 줄 → 기계검증 가능한 의무 2개 → FL이 정답 계산 → 스코어보드 증거 → 게이트 잠금. 이 사슬이 신뢰.</p>

<!--
이 표가 발표의 핵심 구체화. 추상 ROCEV가 실제 IP에서 어떤 값이 되는지 한 장에.
-->

---

## 실질 workflow — 각 단계가 ROCEV를 닫는다

<div class="flow">
  <div class="box blue">req 🔒</div><div class="arr">→</div>
  <div class="box blue">rtl 🔒</div><div class="arr">→</div>
  <div class="box blue">tb 🔒</div><div class="arr">→</div>
  <div class="box ok">sim 🔒</div>
</div>

| 단계 | 닫는 것 | 게이트 |
|---|---|---|
| req | OBL lock + SSOT anchor | `check_locked_truth_bundle` |
| rtl | 컴파일 / lint | `iverilog` + `dut_lint_report` |
| tb | scoreboard가 OBL observable 관측 | tb ledger |
| sim | `OBL_COUNT_INCR/OVF` 증거 | `check_sim_disk` + `check_truth_coverage` |

<p class="center note">이전 게이트가 fresh evidence로 PASS 안 하면 다음 진입 불가.</p>

<!--
S5의 추상 OBL이 어느 단계에서 어떤 게이트로 닫히는지.
-->

---

<!-- _class: lead -->
<div class="center">
<span class="kicker">이걸 cursor로 구현한다면?</span>

# rules · skills · hooks · agents

<p class="note">ROCEV를 구동하는 네 표면</p>
</div>

<!--
여기서부터 세미나 본체 — Cursor 활용법.
-->

---

## Cursor 4표면 = ROCEV 구동 축

<div class="flow">
  <div class="box">rules<br><span class="note">유도</span></div>
  <div class="box bad">hooks<br><span class="note">강제</span></div>
  <div class="box blue">agents<br><span class="note">오너</span></div>
  <div class="box ok">skills<br><span class="note">절차</span></div>
</div>

- **rules** — 모델을 미리 정렬 · **hooks** — 결정론적 차단
- **agents** — 단계 소유 · **skills** — 실행 절차
- 모두 한 목적 → **"초록불 = 진짜 게이트"**

<p class="note">각 표면을 공식 스펙 기준으로 하나씩 — 실제 .cursor 예시와 함께.</p>

<!--
네 축의 역할 분담. 다음 4면이 각각의 구체 예시.
-->

---

## ① Rules — `.cursor/rules/*.mdc`

```markdown
---
description: Hardware RTL conventions + no-fake-pass discipline
globs: "**/rtl/**, **/tb/**, **/sim/**"
alwaysApply: false
---
- SSOT가 권위. 생성 산출물 손편집해 PASS 만들기 금지.
- Verilog-2001 방언: always_ff / logic / typedef / for 금지.
- HDL 시뮬 출력을 head/tail/grep 로 자르지 말 것.
```

| 적용 방식 | frontmatter | 트리거 |
|---|---|---|
| Always | `alwaysApply: true` | 모든 세션 |
| Auto-Attached | `globs` | 매치 파일이 context에 |
| Agent-Requested | `description` | 에이전트가 판단 |
| Manual | (둘 다 없음) | `@rule` 호출 |

<!--
.mdc = 마크다운+frontmatter. globs로 RTL 만질 때만 자동 첨부.
-->

---

## ② Skills — `.cursor/skills/<name>/SKILL.md`

```markdown
---
name: rocev-chain
description: Drive one IP req→rtl→tb→sim, closing ROCEV at each stage.
                Use when taking requirements to simulated RTL.
---
## Stage 1 — req
python3 .cursor/workflow/req-gen/scripts/lock_requirement_set.py <ip> --root .
python3 .cursor/workflow/req-gen/scripts/check_locked_truth_bundle.py <ip> --root .
```

- 폴더명 = skill명 · `name`+`description`만 카탈로그 로드, 매칭 시 본문 로드
- `description`으로 **자동 트리거** · `disable-model-invocation: true` → `/rocev-chain`만
- skills = "따라 읽는 레시피" (정본 실행, 재구현 금지)

<!--
rocev-chain이 req→rtl→tb→sim 운영 매뉴얼. 단계별 정확한 명령.
-->

---

## ③ Hooks — `.cursor/hooks.json` + script

```json
{ "version": 1, "hooks": {
  "stop":                 [{ "command": ".cursor/hooks/stop-todo-loop.py" }],
  "beforeShellExecution": [{ "command": ".cursor/hooks/guard-shell.py" }] }}
```

- `stop-todo-loop` → open todo 남으면 `{"followup_message":"…"}` → **재투입(멈출 수 없음)**
- `guard-shell` → HDL 출력 `| head/tail/grep` → `{"permission":"deny"}` → **정직 차단**

```text
입력(stdin JSON) → 출력: {"permission":"allow|deny|ask"}  또는  {"followup_message":"…"}
이벤트: sessionStart · preToolUse · subagentStop · beforeShellExecution · stop …
```

<p class="note">룰을 다 꺼도 작동하는 결정론적 강제 — silent-PASS의 모든 판본 차단.</p>

<!--
hooks가 진짜 이빨. 공식 이벤트 목록 + permission/followup 계약.
-->

---

## ④ Agents — `.cursor/agents/*.md`

```markdown
---
name: req-gen
description: req stage owner — emit/lock requirements,
                project VCM todos, pass the locked-truth gates.
readonly: false
---
Owns `req/`. Rules:
- SSOT anchor 필수 — 없는 requirement는 무효.
- gate FAIL 출력이 곧 산출물 — verbatim, 완화 금지.
```

<div class="flow" style="margin-top:.3em">
  <div class="box ok">/rocev-chain</div><div class="arr">⟶</div>
  <div class="box blue">/req-gen</div><div class="arr">→</div>
  <div class="box blue">/rtl-gen</div><div class="arr">→</div>
  <div class="box blue">/tb-gen</div><div class="arr">→</div>
  <div class="box blue">/sim</div>
</div>

<p class="note"><code>readonly:false</code> → subagent-evidence-check 훅이 증거 없는 "완료" 차단.</p>

<!--
agents = 단계 오너. 지휘자(rocev-chain)가 위임, 각자 자기 폴더 소유 + 증거 의무.
-->

---

## 이게 Cursor만의 얘기가 아니다

<div class="big center" style="margin:.2em 0">같은 패턴, 다른 에이전트</div>

| 표면 | Cursor | Claude Code | Codex |
|---|---|---|---|
| 규칙 | `.cursor/rules/*.mdc` | `CLAUDE.md` / output style | `AGENTS.md` |
| 절차 | `.cursor/skills/*/SKILL.md` | Skills · `.claude/commands/*.md` | prompt 파일 |
| 훅 | `.cursor/hooks.json` | `.claude/settings.json` (PreToolUse/Stop/SubagentStop) | wrapper / MCP |
| 서브에이전트 | `.cursor/agents/*.md` | `.claude/agents/*.md` | profiles |
| 공통 권위 | `AGENTS.md` | `AGENTS.md` (+`CLAUDE.md`) | `AGENTS.md` |

<!--
세 도구 모두 rules/skills/hooks/subagents 대응물이 있다. 표면만 다르다.
-->

---

## 왜 일반화되나 — 핵심 메시지

<div class="lead center">

<div class="big">
게이트(<code>*.py</code>) · todo(<code>current_todos.json</code>) · 증거(<code>results.xml</code>)<br>
= <span style="color:var(--blue)">에이전트 바깥의 plain 파일</span>
</div>

<p style="margin-top:.5em">→ 어느 에이전트든 <b>같은 ROCEV 워크플로</b>를 구동<br>
표면만 다르고 <b style="color:var(--ok)">권위 모델은 공유</b></p>

</div>

<!--
핵심: 강제 장치가 에이전트 밖 파일/스크립트라 에이전트 교체에 불변.
Cursor로 배우면 Claude Code/Codex로 그대로 옮겨간다.
-->

---

<!-- _class: lead -->
<div class="center lead">

<div class="big">
green = <span style="color:var(--ok)">genuinely correct</span><br>
<span class="muted" style="font-size:.62em">에이전트는 갈아끼워도 워크플로는 그대로</span>
</div>

<p class="note">데모: <code>check_sim_disk ghost_ip</code> → 정직한 FAIL (가짜로는 못 넘긴다)</p>

</div>

<!--
회수. AI에게 RTL을 맡기되 초록불이 진짜이게. 그 규율은 어느 에이전트에서도 동일.
-->
