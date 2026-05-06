# Golden FL/CL Flow Guide

> Human이 정답을 확정하고, LLM이 그 정답에 수렴하도록 9개 loop을 도는 시스템.
> 한 줄: **사람은 `yaml/<ip>.ssot.yaml`만 짠다 → `/golden-all <ip>` 친다 → 9 loop이 9 gate를 채워가는 걸 본다.**

이 문서는 fl-model-gen 워크플로의 Golden 모델 augment 산출물을 다음 사람(또는 다음 세션)이 이어받기 위한 단일 진실 가이드다.

---

## 0. TL;DR

| 묻는 것 | 답 |
|---|---|
| 시스템 한 명령으로 돌리려면? | `/golden-all <ip>` (alias: `ga`) |
| 사람이 손보는 유일한 입력? | `<ip>/yaml/<ip>.ssot.yaml` |
| 사람이 절대 LLM에게 안 맡기는 것? | spec / FL 모델 / coverage goal / perf target / interface 계약 / signoff |
| LLM이 자동으로 도는 loop 개수? | 9개 (L1~L9) |
| 사람 게이트 개수? | 9개 (G1~G9) |
| Cardinal rule? | "RTL이 FL과 안 맞을 때 FL을 바꿔서 PASS시키는 것은 금지" |
| 어디 검증부터 보면 됨? | `<ip>/governance/authority.md` (체크박스로 게이트 진척률) |

---

## 1. 철학 (변경하지 말 것)

```
HUMAN = 정답/목표/판단 기준 확정
LLM   = 그 기준에 수렴하도록 생성·실행·수정 loop 수행
```

**Operating Rules (R1~R6, 머신 레벨에서 강제)**:
1. LLM은 RTL을 고칠 수 있다
2. LLM은 test를 추가할 수 있다
3. LLM은 coverage gap을 채울 수 있다
4. LLM은 spec/FL/coverage/perf target을 바꾸려면 change request 필수
5. 사람 승인 전에는 golden artifact 변경 금지
6. PASS의 의미는 항상 locked truth(FL+SSOT) 기준으로만 판단

**Cardinal rule (위반 시 시스템이 멈춤)**:
> RTL이 FL과 어긋났을 때 FL을 바꿔서 PASS시키는 것은 금지된다.
> `model_signature.json` drift가 감지되면 downstream worker는 `[SSOT HANDOFF] golden_changed`를 발행하고 멈춘다.

---

## 2. Repo 레이아웃 (per-IP)

```
<ip>/
├── yaml/<ip>.ssot.yaml          # ◆ HUMAN locked — 유일한 진실
├── req/                         # ◆ HUMAN locked — requirement
├── model/                       # ◆ HUMAN-approved generated
│   ├── functional_model.py      # FL = oracle
│   ├── cycle_model.py           # CL (조건부) — FL을 import만 함
│   ├── fl_model_check.json      # FL self-check report
│   ├── cl_model_check.json      # CL self-check report
│   ├── decomposition.json       # SSOT 섹션 → unit 매핑
│   ├── model_signature.json     # ◆ drift gate (SHA-256 SSOT/tx/inv/expr)
│   └── manifest.json            # timestamps/host (payload와 분리)
├── cov/                         # ◆ HUMAN-approved generated
│   ├── fl_fcov_plan.json        # FL bins (transaction/state/error)
│   ├── cl_fcov_plan.json        # CL bins (handshake/timing/ordering)
│   └── fcov_plan.json           # union view (backward compat)
├── verify/                      # ◆ HUMAN-approved generated
│   ├── equivalence_goals.json   # FL-vs-RTL goal manifest (인 plenty)
│   ├── cocotb_harness.py        # FL/CL을 oracle로 호출하는 scoreboard
│   ├── Makefile.sim             # fl_only / cl_only / fl_cl_rtl
│   └── scoreboard_bindings.sv   # 조건부 module-bind 스텁
├── golden/                      # ⚙ TodoTracker가 자동 로드
│   ├── golden_todos.json        # audit ledger (full metadata)
│   └── golden_todos_tracker.json # TodoTracker shape (validator-gated)
├── governance/                  # ⚙ 9 gates / 9 loops / 6 rules
│   ├── authority.json
│   └── authority.md
├── rtl/                         # ✎ LLM editable
├── tb/                          # ✎ LLM editable
├── sim/                         # ✎ LLM editable
├── vectors/                     # ✎ LLM editable
├── lint/                        # ⚙ tool output (LLM read, edits via rtl/)
├── reports/                     # ✎ LLM editable
└── synthesis/, dft/, pnr/, ...  # ⚙ EDA workflow output
```

범례: ◆ locked / ⚙ machine-managed / ✎ LLM-editable

---

## 3. 한 방 명령

```bash
/golden-all <ip>          # 별칭: /ga <ip>
```

내부 chain (`commands/golden-all.json::chain[]`):
```
ssot-fl-model        # 기존 — FL emit
ssot-cycle-model     # 신규 — CL emit (트리거 만족 시)
ssot-dual-fcov       # 신규 — FL/CL 분리 coverage
ssot-equiv-goals     # 기존 — equivalence goals
ssot-verification-rtl # 신규 — cocotb harness + Makefile.sim
ssot-golden-todos    # 신규 — TodoTracker JSON 떨굼
ssot-authority       # 신규 — 9 gates / 9 loops manifest
```

각 단계는 단독으로도 호출 가능:
```bash
/ssot-fl-model <ip>      # 별칭: sfm
/ssot-cycle-model <ip>   # 별칭: scm
/ssot-dual-fcov <ip>     # 별칭: sdf
/ssot-equiv-goals <ip>   # 별칭: seg, equiv-goals
/ssot-verification-rtl <ip>  # 별칭: svr
/ssot-golden-todos <ip>  # 별칭: sgt, golden-todos
/ssot-authority <ip>     # 별칭: sa
```

CLI 직접 호출 (워크스페이스 외부):
```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
python3 workflow/fl-model-gen/scripts/emit_model_signature.py <ip> --root .
python3 workflow/fl-model-gen/scripts/emit_cycle_model.py <ip> --root .
python3 workflow/fl-model-gen/scripts/emit_dual_fcov.py <ip> --root .
python3 workflow/fl-model-gen/scripts/emit_verification_rtl.py <ip> --root .
python3 workflow/fl-model-gen/scripts/emit_golden_todos.py <ip> --root .
python3 workflow/fl-model-gen/scripts/emit_authority_manifest.py <ip> --root .

# Drift 감지만 하고 싶을 때:
python3 workflow/fl-model-gen/scripts/emit_model_signature.py <ip> --root . --check
```

---

## 4. CL 트리거 매트릭스

`emit_cycle_model.py`는 SSOT가 아래 조건 중 하나 이상 만족할 때만 `<ip>/model/cycle_model.py`를 emit한다.

| 조건 | 이유 |
|---|---|
| `cycle_model.handshake_rules` non-empty | ready/valid timing 기계 검증 필요 |
| `cycle_model.ordering` non-empty | 트랜잭션 순서 stepper 필요 |
| `cycle_model.arbitration` defined | fairness/starvation declarative 불가 |
| `cycle_model.outstanding > 1` | 다중 outstanding emergent behavior |
| `cycle_model.latency.*.max_cycles == null` | unbounded → 측정 필요 |
| `synthesis.ppa_targets.frequency_mhz_min` set | fmax sweep 위해 CL 실행 필요 |

조건 모두 미충족 → `[emit_cycle_model] <ip> CL not required`로 종료, CL 산출물 안 만듦. 다음 단계는 declarative cycle_model + cocotb assertion으로 충분.

---

## 5. TodoTracker 통합

`workflow/loader.py::load_dynamic_todo_template()` (lines 536-567)이 자동으로 `<ip>/<area>/<area>_todo_tracker.json`을 발견한다. `area="golden"` 등록만 되면 추가 코드 불필요.

```
emit_golden_todos.py
  → <ip>/golden/golden_todos_tracker.json
       │
       ▼ loader 자동 감지
  TodoTracker.add_todos(tasks)  (lib/todo_tracker.py:291)
       │
       ▼ persist
  ~/.common_ai_agent/current_todos.json
       │
       ▼ Textual TUI 자동 로드
  src/textual_main.py::AgentTUI
```

### Todo 분류 (smbus 파일럿 기준 13개)

| Source | 개수 | 패턴 |
|---|---|---|
| A. equivalence_goals.json | 9 | `GLD_GOAL_<goal_id> — <title>` |
| A. blocked goal | 0 | `[BLOCKED] GLD_GOAL_<id>` + `rejection_reason` |
| B. fl_model_check fail | 0 | `GLD_FL_FAIL_<tx_id>` + `validator` |
| B. cl_model_check fail | 0 | `GLD_CL_FAIL_<tx_id>` + `validator` |
| C. SSOT-TBD escalation | 0 | `[SSOT-TBD] GLD_SSOT_*` (ssot-gen에 escalate) |
| D. 항상 augmentation | 3 | GLD_AUG_SIGNATURE / COCOTB_RUN / LOOP_MAP |
| D. 조건부 augmentation | 1 | GLD_AUG_CL_EMIT (handshake/ordering 있을 때) |

### TodoItem 스키마 정합 (절대 안 깸)

`emit_golden_todos.py`는 `lib/todo_tracker.py:115-194`의 TodoItem 필드만 emit한다:

```
content, activeForm, status, priority, detail, criteria,
rejection_reason, approved_reason, validator, delegate, workflow,
notes, loop, max_loop_iterations, exit_condition, command, ...
```

`status` ∈ {pending, in_progress, completed, approved, rejected} — **`blocked`는 valid가 아니다**. blocked goal은 `status="pending"` + `rejection_reason="<blocker>"` + `priority="high"` + content prefix `[BLOCKED]`로 인코딩된다.

`priority` ∈ {high, medium, low}. 워크플로 필터용 `workflow="fl-model-gen"` 모든 todo에 박힘.

### Validator-driven auto-reject loop

`GLD_AUG_*` 와 `GLD_*_FAIL_*` todo는 `validator` 필드에 shell command를 가진다:

```
"validator": "test -f smbus/model/cycle_model.py && ! grep -E 'output_rules|state_updates|_eval_rule_expr' smbus/model/cycle_model.py"
```

LLM이 todo를 `mark_completed` 시도하면 TodoTracker가 validator를 실행하고, returncode≠0면 자동으로 `rejected` 상태로 돌리고 stderr를 `rejection_reason`에 박는다 (`lib/todo_tracker.py:215`). **fake completion 차단**.

---

## 6. 9 Gates × 9 Loops × 6 Rules

`<ip>/governance/authority.json` + `authority.md`에 박힘. 둘 다 deterministic (timestamp 없음).

### 9 Human Gates — artifact 존재로 자동 status 갱신

| ID | Title | approved 조건 |
|---|---|---|
| G1 | Requirement 승인 | `<ip>/req/` non-empty |
| G2 | Spec 승인 | `<ip>/yaml/<ip>.ssot.yaml` 파싱 가능 |
| G3 | Interface 승인 | `io_list` section non-empty |
| G4 | FL golden model 승인 | `model/functional_model.py` + `fl_model_check.passed=true` + `model_signature.json` |
| G5 | Coverage goal 승인 | `cov/fl_fcov_plan.json` (+ CL 트리거 시 `cl_fcov_plan.json`) |
| G6 | CL/performance target 승인 | `cycle_model` section + (조건부) `model/cycle_model.py` |
| G7 | RTL architecture 방향 승인 | `model/decomposition.json` complete=true; behavior modules have function/cycle ownership, structural modules have memory/dataflow/register/parameter/feature traceability |
| G8 | PPA/DFT trade-off 승인 | `synthesis.ppa_targets` populated |
| G9 | Final sign-off | `<ip>/golden/sign_off.json` signed |

### 9 LLM Loops

| ID | Title | Validator path | Owner-on-fail |
|---|---|---|---|
| L1 | RTL correctness | `<ip>/sim/scoreboard_events.jsonl` | rtl |
| L2 | Module-level | `<ip>/sim/module_scoreboard_*.jsonl` | rtl |
| L3 | Coverage closure | `<ip>/cov/coverage.json` | tb |
| L4 | Lint/compile | `<ip>/lint/dut_lint.json` | rtl |
| L5 | Assertion/protocol | `<ip>/sim/assertion_failures.jsonl` | rtl\|tb |
| L6 | CL performance | `<ip>/reports/perf_sweep.json` | rtl\|architect |
| L7 | PPA chain (synth/dft/pnr/sta/power/area) | `<ip>/reports/ppa_sweep.json` + 6 sub-stage reports | architect\|human |
| L8 | Regression minimization | `<ip>/sim/min_repro_*.jsonl` | tb\|rtl |
| L9 | Report/root-cause | `<ip>/reports/fail_analysis.md` | tb\|rtl\|architect |

L7 sub_stages (가장 표 깊음):
```
synthesis → reports/synth/qor.json    {WNS, TNS, cell_area, register_count, est_power}
dft       → reports/dft/atpg.json     {fault_coverage, pattern_count, scan_chains, scan_shift_power, dft_area_overhead}
pnr       → reports/pnr/route.json    {post_route_WNS, clock_skew, wirelength, cell_density, congestion_overflow, ir_drop_risk}
sta       → reports/sta/timing.json   {setup_slack, hold_slack, fmax_mhz}
power     → reports/power/power.json  {dynamic_mw, leakage_mw, toggle_hotspot}
area      → reports/pnr/area.json     {total_um2, utilization_pct, macro_area}
```

PPA feedback 공식:
```
latency_ns       = cycles × clock_period
throughput       = transactions_per_cycle × Fmax
energy/op        = power / ops_per_second
area_efficiency  = throughput / area
```

---

## 7. Cardinal rule 강제 메커니즘

| 위협 | 차단 메커니즘 | 위치 |
|---|---|---|
| LLM이 FL을 바꿔 PASS | `model_signature.json` drift gate | `emit_model_signature.py --check` |
| LLM이 CL에서 functional 결정 | forbidden-substring guard | `emit_cycle_model.py:186-194` (output_rules/state_updates/_eval_rule_expr) |
| LLM이 coverage goal 약화 | locked_artifacts 명시 | `_authority_contract` + `repo_layout.locked` |
| LLM이 spec/io_list 변경 | locked_artifacts 명시 | 동일 |
| LLM이 todo만 마킹하고 실제 작업 안 함 | `validator` 필드 자동 실행 | `lib/todo_tracker.py:215` |
| Silent overwrite of golden | downstream worker가 진입 시 signature 비교 | follow-up T2 patch (golden-workflow-augment.json item 7) |

---

## 8. 결정성 보장 (golden artifact 모두)

다음 파일들은 같은 SSOT 입력에 대해 **byte-identical** 출력을 보장한다:

```
model/model_signature.json
model/cycle_model.py
cov/fl_fcov_plan.json
cov/cl_fcov_plan.json
cov/fcov_plan.json (union view)
golden/golden_todos.json
golden/golden_todos_tracker.json
governance/authority.json
governance/authority.md
```

확인 방법:
```bash
for f in model/model_signature.json cov/fl_fcov_plan.json governance/authority.json golden/golden_todos_tracker.json; do
  m1=$(md5 -q smbus/$f)
  python3 workflow/fl-model-gen/scripts/emit_<해당-스크립트>.py smbus --root . > /dev/null
  m2=$(md5 -q smbus/$f)
  [ "$m1" = "$m2" ] && echo "OK $f" || echo "FAIL $f"
done
```

`generated_at` / `host` / `run_id`는 향후 `<ip>/model/manifest.json`으로 분리 예정 (T1 patch — 아직 미적용; 현재 `decomposition.json` / `equivalence_goals.json` / `fl_model_check.json`은 timestamp 포함되어 있음).

---

## 9. 신규 파일 인벤토리 (이 augment에서 추가됨)

### Workflow scripts (6개)
```
workflow/fl-model-gen/scripts/
├── emit_model_signature.py
├── emit_cycle_model.py
├── emit_dual_fcov.py
├── emit_verification_rtl.py
├── emit_golden_todos.py
└── emit_authority_manifest.py
```

### Slash commands (6개)
```
workflow/fl-model-gen/commands/
├── ssot-cycle-model.json     (기존 ssot-fl-model.json/ssot-equiv-goals.json 옆)
├── ssot-dual-fcov.json
├── ssot-verification-rtl.json
├── ssot-golden-todos.json
├── ssot-authority.json
└── golden-all.json           (composite chain)
```

### Static todo templates (2개)
```
workflow/fl-model-gen/todo_templates/
├── golden-workflow-augment.json   (10 IP-agnostic T1/T2/T4 패치)
└── golden-ip-augment.template.json (8 conditional 템플릿 카탈로그)
```

### 건드리지 않은 핵심 파일 (수정 금지)
```
workflow/fl-model-gen/scripts/emit_fl_model.py        ← T1 패치는 follow-up
workflow/fl-model-gen/scripts/emit_equivalence_goals.py
workflow/loader.py                                     ← chain 디렉티브는 follow-up
lib/todo_tracker.py                                    ← TodoItem 스키마 단일 진실
```

---

## 10. 9 Loop별 구현 상태 (정직)

| Loop | Contract | Harness/Validator | 실행 워커 (loop 자동 패치) |
|---|---|---|---|
| L1 RTL correctness | ✅ EQ_TRANSACTION_* + expected_contract | ✅ cocotb_harness.py + Makefile.sim | ⚠ 외부 — `rtl-gen` 워크플로 |
| L2 Module-level | ✅ EQ_MODULE_* + decomposition.module_contracts | ✅ scoreboard_bindings.sv (stub) | ⚠ 외부 — module별 cocotb는 tb-gen |
| L3 Coverage closure | ✅ fl/cl_fcov_plan + EQ_COVERAGE_* | ✅ todo validator | ⚠ 외부 — stimulus 자동 생성은 tb-gen |
| L4 Lint/compile | ✅ manifest path | ⚠ 경로만 | ⚠ 외부 — `lint` 워크플로 |
| L5 Assertion/protocol | ✅ cycle_model.handshake_rules + EQ_PROTOCOL_*/EQ_TIMING_* | ⚠ CL이 룰 카운트만, SVA emit ❌ | ⚠ 외부 |
| L6 CL performance | ✅ cycle_model.py 실행 + EQ_TIMING_* | ✅ CycleModel.observe()/tick() | ❌ perf sweep 자동화 미구현 |
| L7 PPA chain | ✅ sub_stages + metrics | ⚠ 경로만, parser ❌ | ⚠ 외부 — `syn`/`sta-post`/`pnr`/`dft` |
| L8 Regression-min | ✅ manifest path | ❌ bisect 미구현 | ❌ 미구현 |
| L9 Report/root-cause | ✅ manifest path | ❌ 자동 생성 미구현 | ❌ 미구현 |

---

## 11. Follow-up 로드맵 (다음 사람이 이어받을 항목)

### T1 (correctness lock — emit_fl_model.py 직접 패치 필요)
1. `_apply_primary` 의 이름 휴리스틱 (`count`/`bad`/`good` auto-increment) 제거 — line 884-892
2. `_active_rtl_modules` 의 4-ref auto-fill 제거 — line 208-209 → blocked 처리
3. `_coverage_closure_goals` 의 transactions[0] 강제 default 제거 → 매칭 못 하면 blocked
4. `generated_at` / `timestamp` 를 `manifest.json`으로 분리 — payload byte-stable 보장
5. `run_self_check`에 invariants/reset/error_case 단정 추가
6. `golden_vectors.jsonl` 회귀 playback 통합

→ `golden-workflow-augment.json` 의 10개 항목이 이미 todo로 박혀있음. TodoTracker UI에서 받아 작업.

### T3 (vision 완성 — 신규 emitter 필요)
7. `emit_protocol_assertions.py` — `cycle_model.handshake_rules` → SVA 자동 변환 (L5 자동화)
8. `emit_regression_min.py` — bisect/shrink 알고리즘 (L8 자동화)
9. `emit_fail_analysis.py` — sim 로그 + scoreboard diff → `reports/fail_analysis.md` (L9 자동화)
10. `emit_ppa_dashboard.py` — synth/dft/pnr/sta report parser → CL 예측 vs 실측 (L7 자동화)
11. `emit_loop_map.py` — `authority.json` → mermaid `loop_map.mmd` + SVG (시각화)

### T2 (signature gate 머신 강제)
12. tb-gen / sim-debug / rtl-gen 워커 진입 시 `model_signature.json` 비교 → mismatch 시 `[SSOT HANDOFF] golden_changed` 발행 후 정지
   → 각 워커의 system_prompt.md에 헤더 가드 추가

### PyMTL3 backend (선택)
13. `emit_fl_pymtl.py` — `cycle_model.executable: pymtl3` 옵트인 시 PyMTL3 FL 생성 (pure-Python FL을 delegate)
14. `emit_cycle_model_pymtl.py` — PyMTL3 CL with @update_ff
15. Verilator co-sim path

### 디렉토리 분리 (선택, 큰 작업)
16. `<ip>/locked/` vs `<ip>/generated_or_editable/` 디렉토리 split — 모든 path reference 재작성 필요

---

## 12. 다음 사람이 이어받기 위한 체크리스트

### 1단계 — 환경 확인
```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
ls workflow/fl-model-gen/scripts/        # 6개 신규 + 기존 2개 = 8개
ls workflow/fl-model-gen/commands/        # 8개 (기존 2 + 신규 6)
ls workflow/fl-model-gen/todo_templates/  # 4개 (기존 2 + 신규 2)
```

### 2단계 — smbus 파일럿 재현
```bash
python3 workflow/fl-model-gen/scripts/emit_model_signature.py smbus --root .
python3 workflow/fl-model-gen/scripts/emit_cycle_model.py smbus --root .
python3 workflow/fl-model-gen/scripts/emit_dual_fcov.py smbus --root .
python3 workflow/fl-model-gen/scripts/emit_verification_rtl.py smbus --root .
python3 workflow/fl-model-gen/scripts/emit_golden_todos.py smbus --root .
python3 workflow/fl-model-gen/scripts/emit_authority_manifest.py smbus --root .

# Verify
make -C smbus/verify -f Makefile.sim fl_only
cat smbus/governance/authority.md
```

### 3단계 — 새 IP에 적용
```bash
# (1) SSOT 작성
vim <new_ip>/yaml/<new_ip>.ssot.yaml

# (2) 한 방
/golden-all <new_ip>

# (3) Tracker UI에서 todo 확인
# golden_todos_tracker.json이 자동 로드되어 TUI에 뜸

# (4) authority.md에서 9 gate 진척률 확인
cat <new_ip>/governance/authority.md
```

### 4단계 — Follow-up 작업 picking up
```bash
# PRD + progress 확인
cat .omc/prd.json
cat .omc/progress.txt

# 워크플로 augment todo 확인 (T1 patches)
cat workflow/fl-model-gen/todo_templates/golden-workflow-augment.json

# 다음으로 만들 emitter 우선순위 (이 가이드 §11)
# 1. T1 patches (emit_fl_model.py 패치)
# 2. emit_regression_min.py (L8 자동화)
# 3. emit_fail_analysis.py (L9 자동화)
# 4. T2 signature gate (downstream 워커 헤더 가드)
```

### 5단계 — 회귀 안전망
새 작업 후 항상 smbus 9-step 검증 재실행:

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent

# 1. emit scripts 모두 존재
ls workflow/fl-model-gen/scripts/emit_*.py

# 2. smbus 산출물 모두 존재
ls smbus/{model,cov,verify,golden,governance}/

# 3. CL single-oracle guard
! grep -E 'output_rules|state_updates|_eval_rule_expr' smbus/model/cycle_model.py

# 4. TodoTracker round-trip
python3 - <<'PY'
import sys, json, tempfile, pathlib
sys.path.insert(0, '.')
from lib.todo_tracker import TodoTracker
tasks = json.load(open('smbus/golden/golden_todos_tracker.json'))['todos']
with tempfile.TemporaryDirectory() as d:
    tt = TodoTracker(persist_path=pathlib.Path(d)/'r.json')
    tt.add_todos(tasks)
    assert len(tt.todos) == len(tasks)
print(f'OK {len(tasks)} todos')
PY

# 5. per-goal coverage
python3 - <<'PY'
import json
g = json.load(open('smbus/verify/equivalence_goals.json'))
t = json.load(open('smbus/golden/golden_todos_tracker.json'))
ids = {x['goal_id'] for x in g['goals']}
content = ' '.join(x['content'] for x in t['todos'])
missing = [i for i in ids if f'GLD_GOAL_{i}' not in content]
assert not missing, missing
print(f'OK {len(ids)} goals -> todos')
PY

# 6. 결정성
python3 workflow/fl-model-gen/scripts/emit_model_signature.py smbus --root . > /dev/null
m1=$(md5 -q smbus/model/model_signature.json)
python3 workflow/fl-model-gen/scripts/emit_model_signature.py smbus --root . > /dev/null
m2=$(md5 -q smbus/model/model_signature.json)
[ "$m1" = "$m2" ] && echo "OK determinism: $m1"

# 7. signature --check
python3 workflow/fl-model-gen/scripts/emit_model_signature.py smbus --root . --check

# 8. fl_only sim
make -C smbus/verify -f Makefile.sim fl_only

# 9. authority manifest
python3 - <<'PY'
import json
m = json.load(open('smbus/governance/authority.json'))
assert m['summary']['gates_total'] == 9
assert m['summary']['loops_total'] == 9
assert 'cardinal_rule' in m
assert 'general_flow_guarantee' in m
print(f'OK gates={m["summary"]["gates_approved"]}/9 approved, loops=9')
PY
```

---

## 13. 참고 (이미 박혀있는 invariants — 깨지 마라)

1. **CL은 FL을 import만 한다** — `from .functional_model import FunctionalModel`. CL 안에서 `output_rules`/`state_updates`를 *읽거나 평가하면 emit이 거부됨* (`emit_cycle_model.py` 정적 가드).

2. **`_authority_contract.locked_artifacts`** = SSOT YAML, FL .py, cycle_model .py, fl_fcov_plan, cl_fcov_plan, equivalence_goals. 이 목록 안에 들어간 파일은 **자동 워크플로가 직접 수정하면 안 된다**. 변경하려면 `[SSOT HANDOFF]` 발행 후 사람 승인 필요.

3. **`golden_todos_tracker.json`** 은 TodoTracker 스키마와 1:1로 정합. `lib/todo_tracker.py`의 `TodoItem` 필드만 emit. 새 필드 추가는 **lib/todo_tracker.py 변경 없이 안 됨** (lib 손대지 마라).

4. **결정성 보장 산출물은 timestamp 빼고 sort_keys + 일관 indent로 dump**. 이 규칙 깨면 `emit_model_signature --check`가 false drift를 보고함.

5. **`/golden-all` chain 끝은 항상 `ssot-authority`**. 그래야 governance manifest 가 가장 최신 산출물 상태를 반영함.

6. **새 IP 추가는 SSOT만 짜면 끝**. fl-model-gen workflow가 IP-agnostic이라 어떤 IP의 SSOT도 같은 방식으로 처리. IP-specific 분기/special-case 추가하면 invariant 깨짐.

---

## 14. 변경 이력

| 2026-05-07 | Overnight workflow hardening (OV-001..011): T1 #1/#4/#5 patches, ast.Subscript support, manifest.json split, signature drift gate, SVA emit, regression-min, fail-analysis, loop_map (Mermaid+SVG), submodule FL + module harnesses. 15 scripts / 14 commands / 11-stage golden-all chain. smbus regression GREEN throughout, pl330_target gates 6/9 approved 0 blocked. | Claude (overnight loop) |


| 일자 | 변경 | 작업자 |
|---|---|---|
| 2026-05-06 | 초기 augment (US-001~US-009) — Ralph session 단일 iteration. 15 신규 파일. smbus 파일럿 9/9 통과. Architect Opus 리뷰 APPROVED. | Claude (Ralph) |
| (다음) | 다음 사람이 이어받을 때 여기 추가 | |

---

## 15. 참고 문서

- 기존 워크플로 system prompt: `workflow/fl-model-gen/system_prompt.md`
- 핵심 규칙 (SSOT 단일 진실): 위 system_prompt.md rule 1~11
- TodoItem 스키마: `lib/todo_tracker.py:115-194`
- Loader 자동 발견 로직: `workflow/loader.py:536-567`
- Plan 원본: `~/.claude/plans/title-source-author-linked-hickey.md`
- PRD (이 augment): `.omc/prd.json`
- Progress log: `.omc/progress.txt`

---

**한 줄 다시**:
> 사람은 `yaml/<ip>.ssot.yaml`만 짠다 → `/golden-all <ip>` 친다 → TUI에서 9 loop이 9 gate를 채워가는 걸 본다. FL은 절대 LLM이 못 바꾼다. 끝.
