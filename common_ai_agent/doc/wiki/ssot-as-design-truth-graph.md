---
title: SSOT As Design Truth Graph
type: proposal
tags: [ssot, truth-graph, requirement, obligation, contract, decision-table, oracle, namespace, gates, fingerprint, mctp, direction]
updated: 2026-06-07
related: [req-obligation-contract-evidence-validation, verification-contract-model, locked-truth-concept, locked-truth-design-spec-workflow, contract-reflection-workflow, evidence-contract-obligation-traceability, llm-contract-repair-loop, formal-verification-evidence, spec-loop-and-equivalence-check, mctp-contract-slice-trial-and-error-20260606, karpathy-llm-wiki-pattern, llm-wiki-knowledge-graph-discussion-20260602]
---

# SSOT As Design Truth Graph

방향 결정 기록(2026-06-07 토론): **SSOT를 "개념"으로 없애지 말고, "거대한 저작 YAML 파일"로는 없앤다.**
SSOT 원칙은 유지·강화하되, `yaml/<ip>.ssot.yaml`이라는 authored monolith는 죽이고
SSOT를 **req / obligation / contract / structure / oracle 로 이루어진 typed Design Truth Graph**로
재정의한다. 이 페이지는 그 합의와, 합의가 *서느냐 무너지느냐*를 가르는 게이트들을 적는다.

이 페이지는 [[req-obligation-contract-evidence-validation]] (척추 정의)와
[[verification-contract-model]] (VCM 구현)을 전제로, 그 위에서 SSOT의 위치를 못 박는다.

## 0. 핵심 한 줄

```text
single source ≠ single file.
파일 하나가 있다고 SSOT가 되는 게 아니고,
여러 파일이어도 "권위 있는 진실 그래프가 하나"면 SSOT다.
SSOT = a file  →  SSOT = a resolved truth graph.
```

지금 헷갈리는 이유는 "single source"와 "single file"을 같은 것으로 봤기 때문이다.

## 1. 진단 — 현 구조는 이름만 SSOT (코드로 검증, 2026-06-06)

코드베이스 리뷰(생산/소비/검증 3면)로 확인된 사실:

- **진실 후보가 3개 평행 존재한다.**
  - `req/*.json` 번들 — `to-ssot` SKILL이 *"req/*.json is the authority; yaml ssot is **not** the authority, it is a projection"* 라고 스스로 선언.
  - `yaml/<ip>.ssot.yaml` — "SSOT"라 불리고 `truth_coverage`·모든 생성기가 읽음.
  - `verify/semantic_contracts.json` — 정작 contract 스파인(`semantic_overlay.py`)이 읽고 fingerprint하는 것.
  → 사용자가 "root가 SSOT인가 req인가 contract인가"를 헷갈리는 게 당연하다.
- **SSOT.yaml이 6역할을 겸한다**: 요구사항 산문 + 포트/레지스터/클럭 구조 + function_model(오라클) + error/test + synthesis/pnr/dft 빌드설정 + traceability/workflow_todos/죽은 placeholder. → 설계 위키 + 생성기 입력 + 오라클 + 빌드 설정 + 체크리스트가 한 파일에. 이게 애매함의 근원.
- **spine↔SSOT 연결이 load-bearing이 아니라 장식이다.**
  - obligation은 `ssot_anchor`를 안 들고 다닌다 (실측 0/106). 앵커는 `requirement → source_refs` 로 **간접**.
  - `source_refs`("yaml/...ssot.yaml:function_model.X")는 **resolve 검증 없는 freeform 문자열**.
  - freshness fingerprint는 SSOT가 아니라 `semantic_contracts.json`을 해시 → **SSOT를 고쳐도 contract는 fresh로 통과**(stealth drift).

## 2. 결정

```text
SSOT.yaml (authored monolith)  → 제거 / generated projection으로 강등
SSOT 원칙                      → 유지·강화: requirements + obligations + contracts 로
                                 구성된 Design Truth Graph 가 담당
```

버리면 안 되는 것은 SSOT가 *대리하던* 환원 불가능한 셋이다:

1. **이름의 기준 (structural namespace)** — port/register/clock/reset/interface/field/derived-signal 이름이 하나로 resolve.
2. **의미의 기준 (executable oracle)** — 입력 시퀀스 → expected output/state 를 계산 가능.
3. **trace의 기준 (fingerprint authority)** — 이 evidence가 어떤 req/obligation/contract를 닫는지 추적.

이 셋은 SSOT 파일이 *암묵적으로* 줘서 편했지만, 그 암묵성이 곧 애매함이었다. 이제 명시적으로 둔다.

## 3. 새 모델 — typed Design Truth Graph

"req + obligation + contract" 3계층은 슬로건이고, 실제는 **노드 타입이 6~8개인 typed graph**다.
contract는 한 개념이 아니라 *family*다.

```text
requirement   왜/무엇을 원하는가 (사람 의도, 아직 모호할 수 있음)
  └ decision  모호함을 사람이 결정 (선택 + 승인 + 기각 대안 = provenance, 행위 복사본 아님)
obligation    반드시 참이어야 하는 atomic design truth (= locked truth claim; prose)
contract      그 truth를 구현·관측·검증 가능하게 만드는 형식 (typed family):
                structural_contract  포트/상태/이벤트 이름·폭 (참조, 재선언 금지)
                behavioral_contract  condition → next_state/output (★ decision-table)
                timing_contract      latency/handshake/ordering
                error_contract       malformed/overflow/timeout/seq mismatch
                verification_contract assertion/test/formal target + required evidence
evidence      contract를 만족했다는 산출물
validation    graph closure 판정
```

핵심 규약: **행위는 단 한 곳(behavioral_contract)에만 저작한다.** obligation은 prose claim,
oracle/FL/SVA는 behavioral_contract에서 *컴파일*한다. (지난 논의의 오라클 포크는
"contract가 곧 전이명세, FL은 그 컴파일"로 닫혔다 — oracle_rules를 별도 계층으로 두지 않는다.)
locked truth도 별도 4번째 계층이 아니라 **obligation의 status로** 둔다: `locked obligation = 검증 가능한 truth`.

## 4. 가장 큰 매듭 — behavioral contract는 decision-table 여야 한다 (make-or-break)

자유 boolean `condition:` 으로 쓰면 totality/determinism/oracle-compilability 게이트가 **vacuous**가 된다:
- 두 조건이 겹치면 오라클 비결정적, 어떤 state×input이 어느 조건에도 안 걸리면 비전역.
- 임의 술어의 exhaustive/disjoint 검사는 무한 상태공간 위 SMT 문제 → "important 조합"을 정의 못 하면 #5는 돌려도 vacuous.

**유일한 해법: FSM/transaction 단위로 behavioral contract를 decision-table로 강제.**
선언된 guard 차원 집합 위에서 각 행 = 한 조합 → 정확히 하나의 effect.

- determinism = 같은 조합 두 행 없음 (구문적, 자명)
- totality = 모든 조합에 행(또는 명시 default) (기계적 enumerate)
- 자유 `condition:`은 *저작*이 아니라 decision-table에서 *컴파일/검증*

예 (MCTP continuation 결정의 guard 차원):
`{hdr_ok, som, eom, context_active, key_match, seq_match, len==DEPTH}`.

**이건 슬라이스에서 이미 실증됐다.** [[mctp-contract-slice-trial-and-error-20260606]] 의
`mctp_rx_assembler`에서 per-arc 계약(a_key/a_seq/a_ovf…)을 다 넣었는데도 blanket mutation + SEC가
**구멍을 찾아냈고**, 그걸 닫은 게 `C-ASM-DECODE`(`exp_drop = a_gate|a_unexp|a_key|a_seq|a_ovf|… `
— 모든 drop을, 오직 drop만)였다. 즉 **"per-arc 계약은 total이 아니다 → partition/decode 계약으로
total을 *구성*해야 한다 → mutation+SEC가 안-total임을 들킨다"** 가 totality 게이트의 miniature 증명이다.
([[formal-verification-evidence]] `## Mutation` 의 SEC 백스톱과 같은 맥락.)

## 5. structure는 *참조*여야지 contract마다 *재선언* 금지

`context_active`/`expected_seq`/`drop_pulse` 같은 신호는 START/END/KEY/OOS 계약이 다 건드린다.
계약마다 `structure:` 블록에 재선언하면 → 한 곳 2-bit, 다른 곳 3-bit 식 drift = io_list 중복문제가
contract 단위로 부활. → **structure는 단일 네임스페이스에서 한 번 선언**, behavioral contract는
**id로 참조만**. derived-signal(`pkt_accept = pkt_valid && pkt_ready`)·glossary도 structure에 한 번.
namespace-resolve 게이트가 "모든 참조가 노드로 resolve"를 강제한다.

## 6. 저작본 vs 생성물 — compiled IR이 기계가 읽는 SSOT

monolithic function_model은 한 파일을 위→아래로 읽으면 FSM이 보였다. 30개 contract로 쪼개면
**전역 상태기계가 암묵(emergent)**이 된다. 검사엔 문제없지만 사람·RTL 생성기는 "state X에서 뭘 하나"를
못 읽는다. → composed-FSM 뷰 + compiled IR은 **선택이 아니라 필수 생성물**.

```text
truth/                         ← AUTHORITY (사람 저작, 리뷰, diff)
  requirements.yaml
  decisions.yaml
  structure.yaml               (ports/state/events/derived-signal namespace)
  obligations.yaml
  contracts/  (structure/behavior/timing/error/verification.yaml)
generated/                     ← DERIVED (저작 금지; do_not_edit + source_graph_fingerprint 헤더)
  design_truth_graph.json      ← 기계가 읽는 진짜 "SSOT" (resolved graph = compiled IR)
  design_spec.html             ← 사람용 뷰 (closure browser, freshness 표시)
  fl_model.py                  ← 오라클 (behavioral contract에서 컴파일)
  sva/  tb/  evidence_plan.json  validation_report.html
evidence/   sim/ formal/ lint/ coverage/ repair/
```

규칙: **HTML도, compiled IR도, fl_model.py도, semantic_contracts.json도 source가 아니다.
source는 canonical truth graph(`truth/*`)다.** `semantic_contracts.json`은 삭제하거나
`generated/semantic_contracts.generated.json`(do_not_edit + fingerprint + generated_from)으로 강등해
평행 authority를 제거한다.

HTML 뷰의 가치는 trace closure 브라우저:
`REQ-…→OBIL-…→C-…→property→E-…(proven)→V-…(closed)`. 단 **stale 노드를 표시**해야 한다 —
green HTML over stale evidence는 같은 함정.

## 6.5 그래프의 형태 — Karpathy LLM-wiki form + typed edges

질문: truth graph를 [[karpathy-llm-wiki-pattern]] 처럼 만들면 되나? **형태(머신)는 yes, 엣지의
계약은 다르다.** [[llm-wiki-knowledge-graph-discussion-20260602]] 이 이미 갈라놨다:

- **LLM Wiki** = 사람/에이전트가 읽는 markdown 지식층, 엣지 = `[[link]]` (**연관적·advisory**, 깨져도 경고)
- **Knowledge Graph** = node–predicate–node **triple** (`uses_bus`/`has_register` 같은 *타입된* 관계)

그 페이지의 risk boundary가 핵심: *"LLM이 그래프 만듦 → 팀이 truth로 취급 → stale/날조 엣지가
ship된다."* → **truth graph의 엣지는 wiki의 느슨한 `[[link]]`가 아니라 KG의 strict triple이어야 한다.**
사람/리뷰/네비 층은 카파시식 그대로(우리 `doc/wiki` build_graph 머신 재사용), 진실 엣지는 strict.

| | 카파시 wiki 엣지 | truth graph 엣지 |
|---|---|---|
| 의미 | "관련 있음"(연관) | `closes`/`references_signal`(정밀 관계) |
| 깨진 참조 | 경고 | **HARD FAIL** (resolve 게이트, §7-1) |
| 저작 | LLM 산문 | resolve+fingerprint된 기계 엣지 |

### 엣지를 2종으로 분리 (이게 복잡함을 막는 핵심)

```text
load-bearing (게이트가 검증, 반드시 resolve, 깨지면 fail):
  derived_from      obligation→requirement, requirement→decision
  closes            contract→obligation, evidence→contract, validation→obligation
  references_signal  behavioral_contract→structure signal   ← IO 허브로 연결
  anchors_to        →oracle/ssot 노드
  proves            evidence→property
organizational (nav/grouping, 깨져도 경고):
  belongs_to_theme  requirement→theme   ← 여러 req → 한 주제 (many-to-many)
  part_of           signal→interface, module→top   ← IO 관리 노드
  related           자유 연관 (카파시식 [[link]])
```

게이트(§7)는 **load-bearing 엣지 위에서만** 돈다. organizational은 뷰·묶음용.

### 허브 노드 — 많이 연결해도 됨, 단 connector지 content 아님

many-to-many와 묶음은 그래프의 정석이다(트리면 못 함). 두 허브가 유용:

- **Theme 노드** — 여러 requirement를 한 주제로: `REQ-ASM-SEQ-001 ─belongs_to_theme→ THEME-SEQ-ORDERING`. 주제별 리뷰/HTML 뷰.
- **IO/Interface 노드 (= structure namespace 허브)** — IO 관련을 한 곳에 (§5 "structure 참조-only"의 구체형):
  ```text
  STRUCT-IO ─part_of← STRUCT-IF-AXI-WR ─owns→ SIG-S-AXI-WDATA, SIG-S-AXI-WSTRB, ...
  C-ASM-INGEST ─references_signal→ SIG-S-AXI-WDATA
  ```
  포트/폭/프로토콜은 IO 허브에 **한 번 선언**, behavioral contract는 **참조만**.

**철칙: 허브는 connector지 content owner가 아니다.** IO 노드는 이름/폭/프로토콜만(행위 금지),
Theme은 묶음만(요구사항 내용 복사 금지). 안 그러면 노드 안에 monolith가 재생성된다.

### "너무 복잡한가?" — 아니다. 복잡함의 진짜 원인 3가지

many-to-many·허브 *때문이 아니라* 이 셋 때문에 복잡해진다 → 규율로 막는다:

1. **엣지 타입 남발** → predicate 어휘를 작게(~10) 고정 (위 목록이 전부).
2. **미해결/날조 엣지** → resolve 게이트. load-bearing은 HARD FAIL.
3. **허브가 내용 보관소가 됨** → 허브는 내용 안 가짐.

원칙: **ontology(타입 종류)는 작게, instance(실제 노드)는 많게.**

## 7. 게이트 — 한 파일의 "암묵 일관성"을 명시 게이트로 되산다

쪼개면 공짜로 얻던 "한 파일에 있으니 대충 일관돼 보임"이 사라진다. 대신:

1. **namespace resolve** — 모든 signal/register/interface/derived 참조가 `structure`에 실존 (freeform 문자열 금지). #8(fingerprint)를 가능케 하는 선행 게이트.
2. **obligation closure** — 모든 requirement가 ≥1 locked obligation으로 내려감.
3. **contract closure** — 모든 locked obligation이 ≥1 contract로 닫힘 (고아 obligation/contract/evidence = fail).
4. **behavior determinism** — decision-table에 같은 guard 조합 두 행 없음.
5. **totality** — 중요한 guard 조합이 정의되지 않은 채 남지 않음 (decision-table enumerate). ★슬라이스 C-ASM-DECODE가 증명.
6. **oracle compilability** — behavioral contract에서 FL/Python golden을 만들 수 있음 (= 오라클이 total·deterministic).
7. **RTL compilability** — structural/behavioral contract에서 module skeleton + state/update logic을 만들 수 있음.
8. **evidence readiness / freshness** — 각 contract를 닫을 assertion/test/formal target 존재 + **fingerprint는 손나열이 아니라 그래프 전이폐쇄로 *계산*** (그 subgraph 중 하나라도 바뀌면 해당 evidence stale).
9. **locked-node guard** — `status: locked` 는 단어가 아니라 *메커니즘*: 잠긴 obligation의 statement/condition/expected는 재승인 서명 없이 못 바뀜 (현 `locked_truth_guard`를 파일→노드 단위로 이동).

> **각주 — tamper-evident provenance ≠ blockchain.** 게이트 8/9(fingerprint·locked-node)는 "변조가
> *들키는*(tamper-evident)" 속성을 원하는 거지, "변조 *불가능*(tamper-proof)/합의"를 원하는 게 아니다.
> evident는 이미 공짜: **git(Merkle DAG) + sha256 + 서명 커밋/태그 + 승인 manifest**. 필요해지면
> (audit·IP 우선권·다자) **transparency log(sigstore Rekor) / RFC3161 타임스탬프**를 붙이면 90%.
> 블록체인*만*의 순증분은 "중앙 권위 없는 무신뢰 다자 합의"인데, 우리는 repo+사람 승인자라는 *중앙이
> 있어* 그 가정이 성립 안 함 → 오바. 단 truth graph를 **ledger-ready**(모든 노드 content-addressed +
> 모든 lock 서명)로 설계만 해두면, 나중에 transparency log를 붙이는 건 재설계가 아니라 하루짜리 add.

## 8. 기존 SSOT 섹션 → 재배치 매핑

| 행선지 | SSOT 섹션 |
|---|---|
| requirements / intent | features, top_module.description, dataflow, test_requirements.scenarios |
| oracle / obligation (behavioral) | function_model(transactions/state_variables/invariants), cycle_model, fsm 일부 |
| structure contract / namespace | io_list, rtl_contract, parameters, clock_reset_domains, memory, registers.bits, interrupts, sub_modules, decomposition |
| obligation + contract | error_handling, registers.write_side_effects, security.safety_goals, debug_observability, quality_gates(검증부) |
| stage config (truth graph 밖) | timing, synthesis, pnr, dft, power, coding_rules, filelist, dir_structure, cdc/rdc |
| generated metadata / view | traceability, workflow_todos, generation_flow, quality_gates 일부 |

가장 중요한 수술 세 가지: **(a) SSOT에서 truth가 아닌 걸 빼라. (b) truth에서 파생 가능한 걸 저작하지 마라.
(c) 생성기 편의용 IR을 authority로 만들지 마라.**

## 9. 이행 — consumer-first (살아있는 시스템 보호)

`mctp_assembler_v3`가 18/18 signoff로 도는 상태에서 flag-day 재작성은 금물.

1. truth graph + 9 게이트를 **오늘의 산출물(ssot.yaml/semantic_contracts)을 컴파일해 읽는 *소비자*로** 먼저 만들고 v3에서 green 띄움(그래프·게이트가 실제로 닫히는지 증명).
2. 그다음 저작권을 뒤집음: `truth/`가 저작본, `ssot.yaml`은 generated/legacy로 강등.

## 9.5 운영 플로우 — commands · gates · 1-TODO/stage (현실성)

그래프를 *운영*하는 명령/게이트 흐름. **결론: 현실적이다 — 80%가 이미 레포에 있고 깔끔히 재정리한 것.**
새 게이트 몇 개 + hard part 2개만 진짜 신규.

### Top flow
`draft-req → finalize-req → lock-req → to-ssot → gen-rtl → gen-tb → sim → (sim-debug / coverage / signoff)`

### Truth flow (단계별 역할)
- `req/obligation/contract/evidence_plan` = **진짜 Locked Truth** (lock-req가 생성)
- `/to-ssot` = Locked Truth → Design Spec SSOT YAML *투영* ([[locked-truth-design-spec-workflow]])
- `/gen-rtl` (현 `/ssot-rtl`) = structural+behavioral contract 기반 RTL 구현 + gate
- `/gen-tb` (현 `/ssot-tb`) = SSOT/RTL/equivalence contract 기반 TB 구현 + gate
- `/sim` = command-only simulation evidence gate
- `/sim-debug` = fail 원인 분류 (RTL bug / TB bug / SSOT ambiguity / tool issue)

### TODO 구조 — UI 1개 / 내부 N개
- UI visible: stage당 대표 TODO 1개 (예: `[gen-tb] Generate TB from SSOT contract ledger`)
- 내부 ledger: `rtl/rtl_todo_plan.json`(존재) · `tb/tb_todo_plan.json` · `sim/sim_todo_plan.json` — contract별/gate별 task 다수
- **규칙: 대표 TODO = 내부 task의 보수적 rollup(AND)** — 내부 1개라도 FAIL이면 stage FAIL. FAIL 시 대표 TODO에서 실패 내부 task로 **drill-down** 가능해야(안 그러면 1-TODO가 actionable 정보를 숨김).

### Loop
`implementation TODO → command gate → PASS: next stage / FAIL: same-stage repair or owner route`
RTL→`/gen-rtl` · TB→`/gen-tb` · sim evidence→`/sim` · waveform·root-cause→`/sim-debug` · spec ambiguity→`/to-ssot`/req repair

### 핵심 원칙
다수 contract/gate는 내부 ledger, 사람 TODO는 stage당 1개 · PASS/FAIL은 command/script evidence(자기보고 status 금지) · LLM=구현/수리, script=gate/판정.

### 현실성 — 이미 있는 것 vs 진짜 신규
| 요소 | 상태 |
|---|---|
| draft/finalize/lock-req · to-ssot · ssot-rtl · ssot-tb · sim_debug · coverage · signoff 명령 | ✅ 존재 |
| lock-req가 req bundle(obligations/contract_refs/evidence_plan) 생성 | ✅ 존재 |
| 내부 ledger `rtl_todo_plan.json` + script gate(check_ip_signoff·rtl_compile·dut_lint·results.xml) | ✅ 존재 |
| owner routing on fail (orchestrator run-to-green + retry_budget + routing_policy) | ✅ 존재 |
| **thick contract**(decision-table behavioral + structural)로 gen-rtl/gen-tb 실제 구동 | ⚠️ 신규 — make-or-break(§4) |
| **fail-classifier**(sim-debug)가 RTL/TB/SSOT/tool을 *증거로* 판정 | ⚠️ hard — 오판=loop 미수렴 |
| gate=재실행 evidence(자기보고 금지) | ⚠️ 일부 — 이번 contract_mutation/formal silent-PASS가 그 사례 |
| 1-TODO 보수적 rollup + drill-down | ⚠️ 소규모 신규 |
| spec-ambiguity→to-ssot/req 재경로 시 **locked-truth 개정(unlock→재결정→재승인)** 경로 | ⚠️ 정의 필요 — 안 그러면 `locked_truth_guard`가 막거나 우회됨 |

### 성패를 가르는 리스크 2개
1. **contract가 충분히 두꺼운가** — "SSOT contract 기반 gen-rtl/gen-tb"가 성립하려면 behavioral=decision-table, structural=namespace여야. 얇으면 LLM 재해석=drift (§4).
2. **fail-classifier가 증거 기반인가** — RTL/TB/SSOT/tool을 *label*만 내면 오판→엉뚱한 owner 수리→무한루프. verdict에 증거(FL=X, RTL=Y@cycle N, waveform cite) 첨부 + 모호하면 사람 escalate(추측 금지). 우리 SEC/mutation 테마와 동일: **verdict엔 evidence.**

## 10. 이름

SSOT는 **원칙**으로 유지한다(`The Design Truth Graph is the SSOT`). 새 *아티팩트*만 `truth/`로 부른다.
용어를 코드에서 하드 리네임하는 건 churn 대비 이득이 작으므로 신중히 — 혼란의 원인은 "SSOT"라는 단어가
아니라 *한 파일이 6역할*이었던 것. `Design Truth Graph`는 문서용 별명으로만.

## 11. 다음 (열린 항목)

- **PoC (권장)**: 슬라이스의 `mctp_rx_assembler` continuation 결정을 **decision-table 한 장**(guard 7차원)으로 적고, 거기서 (a) totality/determinism 게이트, (b) FL golden, (c) SVA를 *컴파일*해 우리가 손으로 넣은 C-ASM-*/C-ASM-DECODE와 **동치**임을 보인다 → "req→obligation→(decision-table)contract만으로 RTL+오라클+검증이 선다"를 슬라이스로 증명.
- truth/ 스키마 확정 (특히 decision-table 행 포맷 + structure 노드 id 규약).
- `design_truth_graph.json` 컴파일러 + 9 게이트를 consumer-first로.

## 한 줄 요약

```text
RTL IP 설계에는 SSOT "파일"이 필요한 게 아니라 resolved truth graph가 필요하다.
그 graph는 requirement → obligation → (typed) contract 로 만들 수 있고,
behavioral contract를 decision-table로 쓸 때만 totality/oracle 게이트가 진짜가 된다.
SSOT.yaml은 authority에서 generated projection으로 강등, SSOT 원칙은 그래프가 승계.
```
