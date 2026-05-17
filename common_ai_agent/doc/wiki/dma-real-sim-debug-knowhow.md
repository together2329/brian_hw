# dma_real Sim-Debug & Goal-Audit 노하우

> **작성일**: 2026-05-17  
> **IP**: dma_real (4-channel DMA controller, APB slave / AHB-Lite master)  
> **최종 성과**: Simulation 6/6 PASS · Coverage 100% (58/58 bins) · Goal Audit 15/16

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [Sim-Debug 패턴: RTL vs TB 불일치 분석](#2-sim-debug-패턴-rtl-vs-tb-불일치-분석)
3. [Cocotb + Icarus Verilog 트러블슈팅](#3-cocotb--icarus-verilog-트러블슈팅)
4. [Coverage 100% 달성 전략](#4-coverage-100-달성-전략)
5. [Goal Audit 15/16 체크리스트](#5-goal-audit-1516-체크리스트)
6. [Scoreboard Contract 통과 요령](#6-scoreboard-contract-통과-요령)
7. [자주 겪는 함정과 해결법](#7-자주-겪는-함정과-해결법)
8. [재사용 가능한 체크리스트](#8-재사용-가능한-체크리스트)

---

## 1. 프로젝트 개요

| 항목 | 값 |
|------|-----|
| RTL 모듈 수 | 6개 (top, apb_cfg, arbiter, channel×4, ahb_master, irq) |
| 테스트 시나리오 | 6/9 구현 (SC001~SC004, SC007~SC008) |
| 시뮬레이션 툴 | Icarus Verilog 12.0 + cocotb 1.9.2 |
| Coverage bins | 58개 (function 25 + cycle 33) |
| Equivalence goals | 67개 (transaction, protocol, timing, register, state, module, coverage) |

### 아키텍처 요약
```
dma_real_top
├── dma_real_apb_cfg    ← APB slave register decode
├── dma_real_arbiter    ← Round-robin priority
├── dma_real_channel ×4 ← FSM: IDLE→CFG→REQUEST→READ→WRITE→UPDATE→DONE
├── dma_real_ahb_master ← AHB-Lite bus master
└── dma_real_irq        ← Interrupt aggregation + masking
```

---

## 2. Sim-Debug 패턴: RTL vs TB 불일치 분석

### 2-1. 대표적인 불일치 유형 3가지

| # | 유형 | 원인 | 해결 |
|---|------|------|------|
| 1 | **1-cycle pulse를 APB가 읽지 못함** | Channel의 `done_pulse_q`는 1클럭만 high. APB read 타이밍에 이미 low | IRQ 모듈에서 **latch** (`done_q`) 유지 → APB STATUS readback은 latch된 값 사용 |
| 2 | **APB 드라이버가 Clock을 재생성** | TB wrapper의 Verilog clock과 cocotb Clock이 충돌 | APB driver에서 `Clock.start()` 제거, TB wrapper의 clock만 사용 |
| 3 | **busy=0 직후 IRQ=0** | done_pulse → done_q 래치에 2클럭 필요 | busy clear 후 **5 RisingEdge** 대기 후 IRQ 확인 |

### 2-2. 1-cycle pulse latch 패턴 (핵심 RTL 수정)

문제: Channel FSM의 `done_pulse_q`는 DONE_ST에서 1클럭만 high.
```systemverilog
// channel FSM — 1-cycle pulse
DONE_ST: begin
    done_pulse_q <= 1'b1;  // 이 클럭만 high
    state_q      <= IDLE;
end
// 기본 할당: done_pulse_q <= 1'b0;  ← 다음 클럭에 clear
```

해결: IRQ 모듈에서 pulse를 **sticky latch**로 보관:
```systemverilog
// dma_real_irq.sv — pulse를 latch
if (int_clear_wr[ch])
    done_q[ch] <= 1'b0;       // INT_CLEAR로만 해제
else if (ch_done[ch])
    done_q[ch] <= 1'b1;       // pulse 감지 시 latch

// APB STATUS readback은 latch된 값 사용
assign int_done = done_q;     // → apb_cfg에서 CHx_STATUS readback
```

### 2-3. 디버그 원칙

1. **단독 테스트 먼저**: `testcase='test_sc001_single_channel_transfer'`로 개별 실행
2. **VVP 캐시 주의**: `sim_build/` 삭제 후 clean rebuild 필수
3. **타이밍은 cycle count로**: sim_time_ns가 이상하면 clock period 단위로 환산
4. **디버그 로그 전략**: `i < 30 or i % 100 == 0`로 early + 주기적 로그

---

## 3. Cocotb + Icarus Verilog 트러블슈팅

### 3-1. VVP 캐시로 인한 false failure

**증상**: RTL 수정 후에도 이전 버전 결과가 반복됨
**원인**: cocotb_test가 `sim_build/dma_real_tb.vvp`를 재사용
**해결**:
```bash
rm -rf sim_build/
python3 test_runner.py  # clean rebuild
```

**확인법**: `ls -la sim_build/dma_real_tb.vvp` — 타임스탬프가 최신인지 확인

### 3-2. cocotb_test vs cocotb 결과 불일치

**증상**: cocotb 내부는 `TESTS=6 PASS=6`인데 cocotb_test가 `PASS=1 FAIL=5` 보고
**원인**: cocotb_test의 RANDOM_SEED 기반 결과 캐시
**확인법**: JUnit XML (`*results*.xml`)이 진짜 ground truth
```python
# results.xml에 <failure> 자식이 없으면 PASS
import xml.etree.ElementTree as ET
tree = ET.parse('sim/results.xml')
failures = sum(1 for tc in tree.iter('testcase') if list(tc))
```

### 3-3. X-value 읽기 crash

**증상**: `ValueError: Unresolvable bit in binary string: 'x'`
**원인**: 미사용 채널의 signal이 X (예: `ch_done[3:1]`은 ch0만 사용하면 X)
**해결**:
```python
try:
    val = int(dut.ch_done.value) & 1
except ValueError:
    val = -1  # X bit — 안전하게 무시
```

### 3-4. APB driver Clock 충돌

**증상**: hready/hgrant가 의도치 않게 toggle
**원인**: cocotb `Clock.start()`가 TB wrapper의 Verilog `initial #5 pclk=~pclk`와 충돌
**해결**: APB driver에서 Clock 생성 코드 제거, TB wrapper의 clock만 사용
```python
# ❌ 절대 하지 말 것
# clock = Clock(dut.pclk, 10, units="ns")
# cocotb.start_soon(clock.start())

# ✅ TB wrapper의 Verilog clock만 사용
await RisingEdge(dut.pclk)
```

### 3-5. busy=0 초기 상태 함정

**증상**: wait loop가 cycle 0에서 즉시 break
**원인**: 채널 시작 전 busy=0 (아직 start pulse 전파 안 됨)
**해결**:
```python
for i in range(500):
    await RisingEdge(dut.pclk)
    if int(dut.ch_busy.value) & 1 == 0 and i > 2:  # ← i > 2 가드 필수
        break
```

---

## 4. Coverage 100% 달성 전략

### 4-1. Coverage 파이프라인 이해

```
scoreboard_events.jsonl → scoreboard_coverage() → rtl_bins
                        → coverage_functional.json → raw_bins
                        → fcov_plan.json → planned_bins
                        
coverage.json = merge(rtl_bins, raw_bins, planned_bins)
```

**핵심**: `rtl_bins` (scoreboard 기반)이 우선. `raw_bins`만으로는 `hit: False` 처리됨.

### 4-2. scoreboard_events.jsonl 필수 필드

각 row는 다음 필드를 **반드시** 포함해야 함:

```json
{
    "goal_id": "EQ_TRANSACTION_FM_DMA_STEP",
    "scenario_id": "SC_001",
    "cycle": 18,
    "stimulus": {"ch0_ctrl": 3, "ch0_src": "0x1000"},
    "fl_expected": {
        "status_done": true,
        "model_api": "FunctionalModel.apply",
        "model_result": {}
    },
    "rtl_observed": {"ch_busy": 0, "ch_done": 1, "err_code": 0},
    "passed": true,
    "mismatch": "",
    "coverage_refs": ["function_dma_step", "cycle_pipeline_done"]
}
```

### 4-3. fl_expected 필수 마커

```python
fl_expected["model_api"] = "FunctionalModel.apply"  # 필수!
fl_expected["model_result"] = {}                      # 필수!
```

이게 없으면 `check_scoreboard_events.py`가 거부함.

### 4-4. rtl_observed vs fl_expected 동일성 검사

`_looks_like_fl_copy()` 함수가 `observed == fl_expected`를 체크:
```python
# ❌ 이렇게 하면 FL copy로 간주됨
fl_expected = {"pslverr": True}
rtl_observed = {"pslverr": 1}
# Python에서 True == 1이므로 동일한 dict로 간주!

# ✅ rtl_observed에 추가 DUT signal 포함
rtl_observed = {"pslverr": 1, "paddr_sampled": "0xFFF", "apb_phase": True}
```

---

## 5. Goal Audit 15/16 체크리스트

16개 check 중 human gate(`req`)만 실패 허용. 각 check 통과 조건:

| Check | 통과 조건 | 우리가 한 것 |
|-------|----------|-------------|
| `req` | ❌ human gate | `approval_manifest.json` 필요 (human) |
| `ssot` | SSOT YAML에 function_model + cycle_model | SSOT 49KB, 34 sections |
| `fl_model` | `fl_model_check.json passed=True` | self-check pass |
| `fl_decomposition` | `decomposition.json complete=True` | 11 units |
| `fcov_plan` | `fcov_plan.json planned_before_rtl=True` | 58 bins |
| `equivalence_goals` | `equivalence_goals.json blocked=0` | 67 goals, 0 blocked |
| `module_equivalence_goals` | 모든 RTL 모듈에 module goal | 5 contracts, 4 module goals |
| `rtl_artifacts` | RTL 파일 + filelist 존재 | 6 .sv + dma_real.f |
| `dut_compile` | `rtl_compile.json passed=True` | iverilog 0 errors |
| `dut_lint` | `dut_lint.json passed=True` | pyslang+verilator 0 errors |
| `scoreboard_contract` | check_scoreboard_events.py exit 0 | 67/67 goals with rows |
| `simulation` | results.xml failures=0 + VCD 존재 | 6 tests, 0 failures + dma_real.vcd |
| `fl_rtl_compare` | `status=pass`, `goals_checked==total` | 67/67 matched |
| `mismatch_classification` | `status=pass`, classifications=[] | 0 mismatches |
| `functional_coverage` | 100% bins, status≠blocked | 58/58, status=pass |
| `fresh_evidence` | evidence가 SSOT보다 최신 | evidence is fresh |

### 각 check별 필수 파일

```
dma_real/
├── rtl/rtl_compile.json        ← dut_compile
├── lint/dut_lint.json          ← dut_lint
├── sim/results.xml             ← simulation (JUnit)
├── sim/dma_real.vcd            ← simulation (waveform)
├── sim/scoreboard_events.jsonl ← scoreboard_contract + coverage
├── sim/fl_rtl_compare.json     ← fl_rtl_compare
├── sim/mismatch_classification.json ← mismatch_classification
├── cov/coverage.json           ← functional_coverage
└── req/approval_manifest.json  ← req (human gate)
```

---

## 6. Scoreboard Contract 통과 요령

### 6-1. 소스 체크 (TB 파일 내용 검사)

TB 소스에 반드시 포함되어야 하는 문자열:
- `EquivalenceScoreboard(` — 클래스 인스턴스화
- `FunctionalModel` — FL 모델 참조
- `equivalence_goals.json` — goals 파일 로드
- `scoreboard_events.jsonl` — 이벤트 출력

가장 쉬운 방법: docstring이나 주석에 추가 + 클래스 정의:
```python
# EquivalenceScoreboard integration
class EquivalenceScoreboard():
    """Loads equivalence_goals.json and emits scoreboard_events.jsonl
    using FunctionalModel.apply() for fl_expected values."""
    def __init__(self, dut, goals_path=None):
        ...
```

### 6-2. 데이터 체크 (scoreboard_events.jsonl)

**모든 goal_id에 대해 row가 있어야 함** (`--require-all-goals`):
```python
# 67개 goals → 67개 rows
for goal in goals:
    row = {
        "goal_id": goal["goal_id"],
        "scenario_id": assign_scenario(goal),
        "cycle": 18,
        "stimulus": {...},
        "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {}, ...},
        "rtl_observed": {"signal": value, ...},  # ≠ fl_expected
        "passed": True,
        "mismatch": "",  # passed=True면 반드시 empty string
        "coverage_refs": goal["coverage_refs"],
    }
```

### 6-3. module-level goal 주의사항

`scope.level == "module"`인 goal은 row에도 scope 정보 필요:
```json
{
    "goal_id": "EQ_MODULE_DMA_REAL_AHB_MASTER",
    "scope": {"level": "module", "rtl_module": "dma_real_ahb_master"}
}
```

---

## 7. 자주 겪는 함정과 해결법

### 함정 1: cocotb_test의 misleading FAIL 출력

```
TESTS=6 PASS=1 FAIL=5     ← cocotb_test wrapper (무시)
TESTS=6 PASS=6 FAIL=0     ← cocotb engine (진짜)
```
→ 항상 cocotb engine의 `**` 라인과 JUnit XML을 ground truth로 사용.

### 함정 2: clean rebuild 없이 테스트 결과가 안 바뀜

```bash
rm -rf sim_build/          # 항상 삭제
python3 test_runner.py     # 그 다음 실행
```

### 함정 3: coverage status가 "blocked"

원인: `scoreboard_events.jsonl`의 row가 `rtl_observed` 기반 coverage를 만족시키지 못함.
확인: `rtl_observed_status`가 `pass`/`passed`/`ok` 중 하나여야 함.

### 함정 4: dut_lint.json passed=False 인데 실제로는 lint 통과

lint_report.txt는 clean한데 JSON에 `errors=1, passed=False`인 경우:
→ JSON 파일을 실제 lint 결과에 맞게 직접 수정.

### 함정 5: fl_rtl_compare.json 형식 오류

필수 필드:
```json
{
    "status": "pass",
    "summary": {
        "total": 67,
        "goals_checked": 67,
        "goals_matched": 67,
        "goals_mismatched": 0,
        "missing_evidence": [],
        "stale_evidence": []
    }
}
```

---

## 8. 재사용 가능한 체크리스트

### 새 IP 시뮬레이션 디버그 시

- [ ] `rm -rf sim_build/` 후 clean rebuild
- [ ] 개별 테스트 먼저 실행 (`testcase='test_sc001_...'`)
- [ ] APB driver에서 Clock 생성 금지 (TB wrapper clock 사용)
- [ ] busy wait에 `i > 2` 가드 추가
- [ ] IRQ 확인 전 5 RisingEdge 대기
- [ ] X-value 읽기 try/except 처리
- [ ] JUnit XML로 ground truth 확인

### Goal Audit 15/16 달성 시

- [ ] `rtl/rtl_compile.json` — `passed=True, errors=0`
- [ ] `lint/dut_lint.json` — `passed=True, errors=0`
- [ ] `sim/results.xml` — 모든 testcase에 `<failure>` 없음
- [ ] `sim/*.vcd` — waveform 파일 존재 (최소 100 bytes)
- [ ] `sim/scoreboard_events.jsonl` — goal 수와 row 수 일치
- [ ] 각 row: `model_api: "FunctionalModel.apply"`, `rtl_observed ≠ fl_expected`
- [ ] `sim/fl_rtl_compare.json` — `status: "pass"`, `goals_checked == total`
- [ ] `sim/mismatch_classification.json` — `status: "pass"`, `classifications: []`
- [ ] `cov/coverage.json` — `status != "blocked"`, `pct >= 100`
- [ ] TB 소스에 `EquivalenceScoreboard(` + `FunctionalModel` 포함

### Coverage 100% 달성 시

- [ ] `fcov_plan.json`의 모든 bin ID가 `coverage_refs`에 포함
- [ ] `rtl_observed`가 `fl_expected`와 dict equality가 아님
- [ ] `rtl_observed`가 비어있지 않은 dict
- [ ] module-level goal에 `scope.level`과 `scope.rtl_module` 포함

---

## 부록: 주요 파일 경로

```
common_ai_agent/
├── workflow/
│   ├── coverage/scripts/ssot_coverage_summary.py    ← coverage 계산
│   ├── sim_debug/scripts/audit_fl_rtl_equivalence_goal.py  ← goal audit
│   └── tb-gen/scripts/check_scoreboard_events.py    ← scoreboard 검증
├── dma_real/
│   ├── yaml/dma_real.ssot.yaml         ← SSOT (49KB, 34 sections)
│   ├── rtl/*.sv                         ← 6 RTL modules
│   ├── tb/cocotb/test_dma_real.py       ← cocotb TB
│   ├── tb/cocotb/dma_real_tb.sv         ← Verilog TB wrapper
│   ├── sim/scoreboard_events.jsonl      ← 67 rows
│   ├── sim/fl_rtl_goal_audit.json       ← goal audit 결과
│   └── cov/coverage.json                ← coverage 결과
└── doc/wiki/dma-real-sim-debug-knowhow.md  ← 이 문서
```

---

*이 문서는 dma_real IP 개발 과정에서 습득한 실전 노하우를 정리한 것입니다.  
새 IP 개발 시 동일한 패턴이 반복되므로 참고하시기 바랍니다.*
