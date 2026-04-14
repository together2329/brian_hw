# EDA Self-Converging Loop — Implementation Specification

> **한 줄**: 실행 → 평가(점수) → 분류 → 수정 → 반복. 점수가 나빠지면 rollback, 좋아질 때만 진행.

---

## 0. 현실 점검: 이미 있는 것 vs 만들 것

### 이미 구축됨 (재사용)

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| Sub-agent 실행 | `core/agent_runner.py` (778줄) | `run_agent_session()` → 미니 ReAct 루프 |
| Job persistence | 동일 | `_persist_job_result()` → `jobs/job<N>/` 4파일 |
| Pipeline engine | `core/workflow_orchestrator.py` (402줄) | sequential/parallel/auto |
| Multi-backend | `core/delegate_runner.py` (302줄) | sub-agent, cursor-agent, codex... |
| req-gen workspace | `workflow/req-gen/` | 요구사항 정리 |
| mas-gen workspace | `workflow/mas-gen/` | MAS 문서 생성 + orchestration |
| rtl-gen workspace | `workflow/rtl-gen/` | RTL 생성 (123줄 프롬프트) |
| tb-gen workspace | `workflow/tb-gen/` | TB 생성 |
| sim workspace | `workflow/sim/` | 시뮬레이션 실행 |
| lint workspace | `workflow/lint/` | Lint 검증 |
| 시각화 | `/session tree`, `/job context` | 디버깅 |

### 새로 만들 것

| # | 파일 | 내용 | 라인 |
|---|------|------|------|
| 1 | `core/eda_loop.py` | **핵심**: 상태머신 + score + classifier + loop controller | ~350 |
| 2 | `slash_commands.py` | `/eda-loop` 커맨드 추가 | ~50 |
| 3 | `workflow/synth/` | Synthesis workspace (Phase 2) | ~150 |
| 4 | `workflow/sta/` | STA workspace (Phase 2) | ~120 |

---

## 1. 아키텍처

```
┌───────────────────────────────────────────────────────────────────┐
│  Human                                                            │
│  └── /eda-loop counter --phase fast                              │
│                                                                   │
│  Main Agent (Decision Layer)                                      │
│  └── core/eda_loop.py                                             │
│      ├── LoopController                                           │
│      │   ├── run_phase_fast()   ← Phase 1: RTL↔Lint↔Sim         │
│      │   ├── run_phase_mid()    ← Phase 2: Synth↔STA             │
│      │   └── run_phase_slow()   ← Phase 3: PnR                   │
│      ├── Score                                                    │
│      │   └── evaluate(state) → float                              │
│      ├── Classifier                                               │
│      │   └── classify_fail(output) → "rtl" | "tb" | "constraint" │
│      └── State                                                    │
│          └── loop_state.json (iteration 추적)                     │
│                                                                   │
│  Execution (이미 구축됨)                                          │
│  └── run_agent_session() → jobs/job<N>/                          │
│      ├── 각 단계마다 1개 job 생성                                 │
│      ├── result.json에 실행 결과 저장                             │
│      └── conversation.json에 전체 컨텍스트 저장                   │
│                                                                   │
│  Workspaces (이미 구축됨)                                         │
│  ├── req-gen → mas-gen → rtl-gen → lint → tb-gen → sim           │
│  └── (신규) synth → sta                                          │
└───────────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

```
run_agent_session() 호출
       │
       ▼
┌─ agent_runner.py ───────────────────────────────────┐
│  1. _next_job_counter() → job<N>/ 할당              │
│  2. TODO_FILE → job<N>/todo.json 리다이렉트         │
│  3. Mini ReAct 루프 실행 (tool 호출 반복)           │
│  4. 결과 압축 (≤8000 chars)                         │
│  5. _persist_job_result() → 4파일 저장              │
│     ├── conversation.json  ← 대화 내역              │
│     ├── full_conversation.json ← append-only        │
│     ├── todo.json          ← sub-agent todo         │
│     └── result.json        ← {status, output, ...}  │
│  6. AgentResult 반환                                 │
└──────────────────────────────────────────────────────┘
       │
       ▼
eda_loop.py에서 output 파싱 → state 업데이트 → 다음 단계 결정
```

---

## 2. 상태 정의 (LoopState)

```python
@dataclass
class LoopState:
    # ── Identity ──────────────────────────────
    module: str                          # "counter"
    mas_path: str                        # "counter/mas/counter_mas.md"

    # ── Phase Control ─────────────────────────
    phase: str = "idle"                  # idle → fast → mid → slow → done | failed
    status: str = "pending"              # pending | running | converged | failed | timeout

    # ── Iteration Tracking ────────────────────
    iteration: int = 0                   # 전체 iteration
    max_iterations: int = 15             # 전체 최대
    rtl_iterations: int = 0             # Fast loop 내 RTL 수정 횟수
    sim_iterations: int = 0             # Fast loop 내 Sim 반복 횟수
    synth_iterations: int = 0           # Mid loop 내 반복 횟수

    # ── Per-phase Limits ──────────────────────
    max_rtl_iterations: int = 3
    max_sim_iterations: int = 5
    max_synth_iterations: int = 3

    # ── Metrics ───────────────────────────────
    lint: dict = field(default_factory=lambda: {"errors": -1, "warnings": -1})
    sim: dict = field(default_factory=lambda: {"pass": 0, "fail": 0, "tests": 0, "fail_tests": []})
    synth: dict = field(default_factory=lambda: {"wns": 0.0, "tns": 0.0, "area": 0, "power": 0.0})
    coverage: float = 0.0

    # ── Score ─────────────────────────────────
    score: float = -999.0
    best_score: float = -999.0

    # ── Convergence ───────────────────────────
    no_improve_count: int = 0
    no_improve_limit: int = 3            # N회 연속 개선 없으면 soft stop

    # ── Job Tracking ──────────────────────────
    jobs: list = field(default_factory=list)  # ["job5", "job6", ...]
    history: list = field(default_factory=list)  # [{iter, action, score, ...}]

    # ── Convergence Criteria ──────────────────
    # Phase 1 (Fast): lint 0E/0W + sim ALL PASS
    # Phase 2 (Mid):  TNS ≥ 0 and WNS ≥ 0
    # Phase 3 (Slow): DRC = 0 (future)
```

### State Persistence: `loop_state.json`

```
.session/<project>/loop_state.json
```

모든 iteration 끝에 저장. 크래시 후 `/eda-loop retry`로 복구 가능.

---

## 3. Score 함수

### Phase별 가중치

```python
def evaluate(state: LoopState) -> float:
    """
    Phase 1 (Fast Loop):
      Score = -10.0 * lint_errors
              -  5.0 * lint_warnings
              + 10.0 * (sim_pass / max(sim_tests, 1))
              - 20.0  (if sim has failures)

    Phase 2 (Mid Loop):
      Phase 1 score
              -  5.0 * max(0, -wns)       # WNS penalty (negative = violation)
              -  3.0 * max(0, -tns)       # TNS penalty
              +  2.0 * coverage_pct / 100  # coverage bonus
    """
    if state.phase == "fast":
        return _score_fast(state)
    elif state.phase == "mid":
        return _score_fast(state) + _score_mid(state)
    return 0.0

def _score_fast(state):
    s = 0.0
    s -= 10.0 * max(0, state.lint.get("errors", 0))
    s -=  5.0 * max(0, state.lint.get("warnings", 0))
    total = max(state.sim.get("tests", 0), 1)
    s += 10.0 * state.sim.get("pass", 0) / total
    if state.sim.get("fail", 0) > 0:
        s -= 20.0
    return s

def _score_mid(state):
    s = 0.0
    wns = state.synth.get("wns", 0.0)
    tns = state.synth.get("tns", 0.0)
    if wns < 0:
        s -= 5.0 * abs(wns)
    if tns < 0:
        s -= 3.0 * abs(tns)
    s += 2.0 * state.coverage / 100.0
    return s
```

### 점수 예시

| 상황 | lint | sim | score |
|------|------|-----|-------|
| 초기 RTL (lint 5E) | E=5 | — | -50.0 |
| Lint 통과, sim 3/7 pass | E=0 | 3/7 | -10.7 |
| Lint 통과, sim ALL PASS | E=0 | 7/7 | **+10.0** |
| Synth WNS=-0.2, TNS=-1.5 | 0 | 7/7 | 10.0 - 1.0 - 4.5 = **+4.5** |
| Timing closure | 0 | 7/7 | 10.0 + 0 = **+10.0** |

---

## 4. Feedback Graph (Targeted Fix)

```
                 ┌──────────────────────────────────────────┐
                 │                                          │
   req → mas → rtl ──► lint ──┐                             │
                  │           │ errors                      │
                  │◄──────────┘ (max 3회)                   │
                  │                                        │
                  ├──► tb-gen ──► sim ──┐                   │
                  │              │     │ failures           │
                  │              │◄────┘                    │
                  │              │                          │
                  │        ┌─────┴──────┐                   │
                  │        │ Classifier │                   │
                  │        └──┬───┬───┬──┘                   │
                  │           │   │   │                     │
                  │     TB bug  RTL bug  Timeout            │
                  │        │      │      │                  │
                  │   tb-fix  rtl-fix  rtl-fix             │
                  │        │      │      │                  │
                  │        └──┬───┘      │                  │
                  │           │◄─────────┘                  │
                  │           │ (max 5회 sim loop)           │
                  │           ▼                              │
                  ├──► synth ──► sta ──┐                    │
                  │              │     │ violations          │
                  │              │◄────┘                     │
                  │         rtl-fix |                       │
                  │         constraint-fix                   │
                  │              │ (max 3회)                 │
                  │              ▼                           │
                  └──► [CONVERGED] ✅                       │
                             │                              │
                             ▼                              │
                       loop_state.json                      │
                       eda_loop_report.json                  │
                                                       RESTART ┘
```

### 핵심: Fail → Fix 매핑

| Fail 위치 | 분류 | 수정 대상 | 재시작 지점 |
|-----------|------|----------|-------------|
| lint error | — | RTL 코드 | `rtl → lint` (Fast loop 내) |
| sim compile error | TB bug | TB 코드 | `tb → sim` |
| sim [FAIL] tc_ (초기) | TB bug 가능성 | TB 코드 먼저 | `tb → sim` |
| sim [FAIL] tc_ (3회+ 지속) | RTL bug | RTL 코드 | `rtl → lint → sim` |
| sim timeout/hang | RTL bug | RTL 코드 | `rtl → lint → sim` |
| STA WNS < 0 | Timing | RTL pipeline or constraint | `synth → sta` |
| STA TNS < 0 | Timing | Constraint or architecture | `synth → sta` |

---

## 5. Bug Classifier

```python
def classify_sim_failure(sim_output: str, sim_iterations: int) -> str:
    """
    sim 실행 결과를 분석하여 수정 대상 분류.

    Returns:
        "tb"   → TB 코드 수정 필요
        "rtl"  → RTL 코드 수정 필요
        "sim"  → sim 스크립트/환경 문제
    """
    output_lower = sim_output.lower()

    # 1. Compile error → 항상 TB bug (port mismatch, undeclared 등)
    if any(kw in output_lower for kw in [
        "compile error", "port mismatch", "undeclared",
        "syntax error", "cannot find", "no such file"
    ]):
        return "tb"

    # 2. Timeout / hang → RTL bug (DUT가 응답 안 함)
    if any(kw in output_lower for kw in [
        "timeout", "simulation hang", "no $finish"
    ]):
        return "rtl"

    # 3. [FAIL] 테스트 케이스 — iteration에 따라 분류
    if "[fail]" in output_lower or "fail:" in output_lower:
        # 여러 번 고쳐도 같은 테스트가 계속 실패 → RTL 문제
        if sim_iterations >= 3:
            return "rtl"
        return "tb"

    # 4. X propagation → reset/initialization 문제
    if any(kw in output_lower for kw in ["xxxx", "x-prop", "unknown"]):
        return "rtl"

    # 5. 기본: TB 수정 먼저 시도
    return "tb"
```

---

## 6. Loop Controller — Phase별 상세

### Phase 1: Fast Loop (RTL ↔ Lint ↔ Sim)

```python
def run_phase_fast(self) -> LoopState:
    """
    수렴 조건: lint.errors == 0 AND sim.fail == 0
    최대: rtl 수정 3회 + sim 재시도 5회
    """

    # ── Step 1: RTL Gen ─────────────────────────────────
    result = self._run_subagent(
        agent="execute",
        prompt=f"[MAS HANDOFF] → rtl-gen\n"
               f"Module: {self.state.module}\n"
               f"MAS: {self.state.mas_path}\n"
               f"Implement RTL from MAS §2-§8\n"
               f"Output: {self.state.module}/rtl/{self.state.module}.sv",
        workflow="rtl-gen",
    )
    self._record("rtl-gen", result)

    # ── Step 2: Lint Loop (max 3) ──────────────────────
    lint_context = ""
    for i in range(self.state.max_rtl_iterations):
        result = self._run_subagent(
            agent="execute",
            prompt=f"Run verilator --lint-only -Wall on "
                   f"{self.state.module}/rtl/{self.state.module}.sv\n"
                   f"Fix all errors and warnings.\n"
                   f"{f'Previous lint errors: {lint_context}' if lint_context else ''}",
            workflow="lint",
        )
        lint = self._parse_lint(result.output)
        self.state.lint = lint
        self._record(f"lint-iter{i+1}", result)

        if lint["errors"] == 0:
            break
        lint_context = result.output

    if self.state.lint["errors"] > 0:
        self.state.status = "FAILED_LINT"
        return self.state

    # ── Step 3: TB Gen ─────────────────────────────────
    result = self._run_subagent(
        agent="execute",
        prompt=f"[MAS HANDOFF] → tb-gen\n"
               f"Module: {self.state.module}\n"
               f"MAS: {self.state.mas_path}\n"
               f"RTL: {self.state.module}/rtl/{self.state.module}.sv\n"
               f"Generate testbench from MAS §9 DV Plan",
        workflow="tb-gen",
    )
    self._record("tb-gen", result)

    # ── Step 4: Sim Loop (max 5) ───────────────────────
    for i in range(self.state.max_sim_iterations):
        result = self._run_subagent(
            agent="execute",
            prompt=f"Compile and simulate {self.state.module}\n"
                   f"Filelist: {self.state.module}/list/{self.state.module}.f\n"
                   f"TB: {self.state.module}/tb/tb_{self.state.module}.sv\n"
                   f"Run until 0 errors, 0 warnings, all [PASS]",
            workflow="sim",
        )
        sim = self._parse_sim(result.output)
        self.state.sim = sim
        self._record(f"sim-iter{i+1}", result)

        if sim["fail"] == 0:
            break  # ✅ ALL PASS

        # ── Classify & Fix ────────────────────────────
        bug_type = classify_sim_failure(result.output, i + 1)

        if bug_type == "tb":
            result = self._run_subagent(
                agent="execute",
                prompt=f"[SIM FIX - TB BUG]\n"
                       f"Sim output shows failures:\n{result.output[:3000]}\n"
                       f"Fix the testbench: {self.state.module}/tb/",
                workflow="sim",
            )
            self._record(f"tb-fix-iter{i+1}", result)

        elif bug_type == "rtl":
            result = self._run_subagent(
                agent="execute",
                prompt=f"[SIM FIX - RTL BUG]\n"
                       f"Sim output shows RTL failures:\n{result.output[:3000]}\n"
                       f"Fix RTL: {self.state.module}/rtl/{self.state.module}.sv\n"
                       f"Preserve interface. Only fix logic.",
                workflow="rtl-gen",
            )
            self._record(f"rtl-fix-iter{i+1}", result)

            # Re-lint after RTL fix
            result = self._run_subagent(
                agent="execute",
                prompt=f"Run verilator --lint-only -Wall on "
                       f"{self.state.module}/rtl/{self.state.module}.sv",
                workflow="lint",
            )
            self.state.lint = self._parse_lint(result.output)
            self._record(f"lint-recheck-iter{i+1}", result)

        self.state.sim_iterations += 1

    # ── Evaluate ────────────────────────────────────────
    self.state.score = evaluate(self.state)

    if self.state.sim.get("fail", 0) == 0:
        self.state.status = "FAST_PASS"
        self.state.phase = "mid"  # 다음 phase로
    else:
        self.state.status = "FAILED_SIM"

    return self.state
```

### Phase 2: Mid Loop (Synth ↔ STA)

```python
def run_phase_mid(self) -> LoopState:
    """
    전제: Phase 1 통과 (lint clean, sim all pass)
    수렴 조건: tns >= 0 and wns >= 0
    최대: synth 반복 3회
    """
    for i in range(self.state.max_synth_iterations):
        # ── Synthesis ──────────────────────────────────
        result = self._run_subagent(
            agent="execute",
            prompt=f"Synthesize {self.state.module}\n"
                   f"RTL: {self.state.module}/rtl/{self.state.module}.sv\n"
                   f"Filelist: {self.state.module}/list/{self.state.module}.f\n"
                   f"Generate QoR report: area, power, timing",
            workflow="synth",
        )
        synth = self._parse_synth(result.output)
        self.state.synth = synth
        self._record(f"synth-iter{i+1}", result)

        # ── STA ────────────────────────────────────────
        result = self._run_subagent(
            agent="execute",
            prompt=f"Run STA on {self.state.module}\n"
                   f"Check setup/hold violations\n"
                   f"Report WNS, TNS",
            workflow="sta",
        )
        sta = self._parse_sta(result.output)
        self.state.synth.update(sta)
        self._record(f"sta-iter{i+1}", result)

        # ── Check ──────────────────────────────────────
        self.state.score = evaluate(self.state)

        if self.state.synth.get("tns", -1) >= 0 and self.state.synth.get("wns", -1) >= 0:
            self.state.status = "CONVERGED"
            return self.state

        # ── Fix Timing ─────────────────────────────────
        result = self._run_subagent(
            agent="execute",
            prompt=f"[TIMING FIX]\n"
                   f"WNS={self.state.synth.get('wns')}, TNS={self.state.synth.get('tns')}\n"
                   f"Options:\n"
                   f"1. Insert pipeline stages in critical path\n"
                   f"2. Retiming\n"
                   f"3. Constraint relaxation if safe\n"
                   f"Fix RTL: {self.state.module}/rtl/{self.state.module}.sv",
            workflow="rtl-gen",
        )
        self._record(f"timing-fix-iter{i+1}", result)
        self.state.synth_iterations += 1

    self.state.status = "FAILED_TIMING"
    return self.state
```

### Convergence Check

```python
def check_convergence(self) -> str:
    """
    Returns: "converged" | "improving" | "stalled" | "regressed"
    """
    # ── Hard Stop ────────────────────────────────────
    if (self.state.lint.get("errors", 1) == 0
        and self.state.sim.get("fail", 1) == 0
        and self.state.synth.get("tns", 0) >= 0
        and self.state.synth.get("wns", 0) >= 0):
        return "converged"

    # ── Score Trend ──────────────────────────────────
    if self.state.score > self.state.best_score:
        self.state.best_score = self.state.score
        self.state.no_improve_count = 0
        return "improving"

    if self.state.score == self.state.best_score:
        self.state.no_improve_count += 1
        if self.state.no_improve_count >= self.state.no_improve_limit:
            return "stalled"
        return "improving"  # same score, still trying

    # score < best_score → regression
    return "regressed"
```

---

## 7. Rollback 전략

```python
def _save_snapshot(self):
    """현재 상태 + RTL 파일 스냅샷 저장"""
    snap_dir = Path(self.session_dir) / "snapshots" / f"iter_{self.state.iteration}"
    snap_dir.mkdir(parents=True, exist_ok=True)

    # Save state
    (snap_dir / "loop_state.json").write_text(
        json.dumps(asdict(self.state), indent=2, default=str)
    )

    # Save RTL files
    rtl_dir = Path(f"{self.state.module}/rtl")
    if rtl_dir.exists():
        import shutil
        shutil.copytree(rtl_dir, snap_dir / "rtl", dirs_exist_ok=True)

def _rollback(self):
    """best_score 시점으로 RTL 복원"""
    # Find best snapshot
    best_iter = max(
        (h for h in self.state.history if h.get("is_best")),
        key=lambda h: h["score"],
        default=None,
    )
    if not best_iter:
        return  # nowhere to rollback to

    snap_dir = Path(self.session_dir) / "snapshots" / f"iter_{best_iter['iteration']}"
    if not snap_dir.exists():
        return

    # Restore RTL
    import shutil
    rtl_src = snap_dir / "rtl"
    rtl_dst = Path(f"{self.state.module}/rtl")
    if rtl_src.exists():
        shutil.copytree(rtl_src, rtl_dst, dirs_exist_ok=True)
```

---

## 8. Result Parsing

### Lint Output Parser

```python
def _parse_lint(self, output: str) -> dict:
    """
    Parse verilator or iverilog lint output.

    Input: "%Error: counter.sv:42: ..."
    Output: {"errors": 3, "warnings": 1}
    """
    errors = 0
    warnings = 0
    for line in output.splitlines():
        line_lower = line.lower()
        if "%error" in line_lower or "error:" in line_lower:
            errors += 1
        elif "%warning" in line_lower or "warning:" in line_lower:
            warnings += 1
    return {"errors": errors, "warnings": warnings}
```

### Sim Output Parser

```python
def _parse_sim(self, output: str) -> dict:
    """
    Parse simulation output.

    Input: "[PASS] tc_S1_reset\n[FAIL] tc_S3_interrupt: got=X expected=1"
    Output: {"pass": 5, "fail": 2, "tests": 7, "fail_tests": ["tc_S3_interrupt", ...]}
    """
    pass_count = output.lower().count("[pass]")
    fail_count = output.lower().count("[fail]")

    fail_tests = []
    for line in output.splitlines():
        if "[fail]" in line.lower():
            # Extract test name
            parts = line.split("]")
            if len(parts) >= 2:
                test_name = parts[0].split("[")[-1] + "]"
                fail_tests.append(test_name.strip())

    return {
        "pass": pass_count,
        "fail": fail_count,
        "tests": pass_count + fail_count,
        "fail_tests": fail_tests,
    }
```

### Synthesis Output Parser

```python
def _parse_synth(self, output: str) -> dict:
    """
    Parse synthesis QoR report.

    Input: "WNS: -0.15  TNS: -1.20  Area: 12450  Power: 0.45mW"
    Output: {"wns": -0.15, "tns": -1.20, "area": 12450, "power": 0.45}
    """
    import re
    result = {"wns": 0.0, "tns": 0.0, "area": 0, "power": 0.0}

    wns_match = re.search(r'wns[:\s]+(-?\d+\.?\d*)', output, re.IGNORECASE)
    tns_match = re.search(r'tns[:\s]+(-?\d+\.?\d*)', output, re.IGNORECASE)
    area_match = re.search(r'area[:\s]+(\d+)', output, re.IGNORECASE)
    power_match = re.search(r'power[:\s]+(\d+\.?\d*)', output, re.IGNORECASE)

    if wns_match: result["wns"] = float(wns_match.group(1))
    if tns_match: result["tns"] = float(tns_match.group(1))
    if area_match: result["area"] = int(area_match.group(1))
    if power_match: result["power"] = float(power_match.group(1))

    return result
```

---

## 9. `/eda-loop` Slash Command

```
/eda-loop <module>                     → 전체 flow (Phase 1 → 2 → 3)
/eda-loop <module> --phase fast        → Phase 1만 (rtl↔lint↔sim)
/eda-loop <module> --phase mid         → Phase 2만 (synth↔sta)
/eda-loop status                       → loop_state.json 조회
/eda-loop history                      → iteration 히스토리 + 점수 추이
/eda-loop retry                        → 마지막 실패 지점부터 재시도
/eda-loop report                       → 최종 리포트
```

### History 출력 예시

```
=== EDA Loop: counter ===
Phase: fast → mid → CONVERGED ✅
Total iterations: 12 | Total jobs: 14

Iter  Action            Score   Lint    Sim         Synth
  1   rtl-gen          -999.0   —       —           —
  2   lint (3E)          -30.0   E=3     —           —
  3   rtl-fix            -30.0   E=0     —           —
  4   lint (clean)        +0.0   E=0     —           —
  5   tb-gen              +0.0   —       —           —
  6   sim (3/7 pass)     -15.7   —       3P/4F       —
  7   tb-fix             -15.7   —       5P/2F       —
  8   sim (5/7 pass)     -11.4   —       5P/2F       —
  9   rtl-fix (RTL bug)  -11.4   E=0     —           —
 10   sim (ALL PASS) ✅   +10.0   E=0     7P/0F       —
 11   synth (WNS=-0.15)   +4.5   —       —           WNS=-0.15
 12   timing-fix          +4.5   —       —           —
 13   synth (clean) ✅   +10.0   E=0     7P/0F       WNS=+0.02

Converged at iteration 13 | Best score: +10.0
```

---

## 10. Jobs 패턴 (실제 생성 예시)

```
.session/default/jobs/
├── .counter ← "14"
│
├── job5/   ← [fast] rtl-gen          → AgentResult(output="RTL written")
├── job6/   ← [fast] lint iter 1      → {"errors": 3, "warnings": 1}
├── job7/   ← [fast] rtl-fix (lint)   → RTL 수정
├── job8/   ← [fast] lint iter 2      → {"errors": 0, "warnings": 0} ✅
├── job9/   ← [fast] tb-gen           → TB + TC 생성
├── job10/  ← [fast] sim iter 1       → 3 PASS / 4 FAIL → classify: TB
├── job11/  ← [fast] tb-fix           → TB 수정
├── job12/  ← [fast] sim iter 2       → 5 PASS / 2 FAIL → classify: TB
├── job13/  ← [fast] tb-fix           → TB 수정
├── job14/  ← [fast] sim iter 3       → 5 PASS / 2 FAIL → classify: RTL (3회+)
├── job15/  ← [fast] rtl-fix (sim)    → RTL 수정
├── job16/  ← [fast] lint recheck     → 0E/0W ✅
├── job17/  ← [fast] sim iter 4       → ALL PASS ✅ → phase → mid
├── job18/  ← [mid] synth iter 1      → WNS=-0.15
├── job19/  ← [mid] sta iter 1        → WNS=-0.15 ❌
├── job20/  ← [mid] timing-fix        → pipeline insert
├── job21/  ← [mid] synth iter 2      → WNS=+0.02
├── job22/  ← [mid] sta iter 2        → WNS=+0.02 ✅ → CONVERGED
│
├── loop_state.json          ← 현재 상태
└── eda_loop_report.json     ← 최종 리포트
```

### eda_loop_report.json

```json
{
  "module": "counter",
  "status": "CONVERGED",
  "total_iterations": 13,
  "total_jobs": 18,
  "phases": {
    "fast": {
      "status": "PASS",
      "iterations": 10,
      "final": {"lint_errors": 0, "lint_warnings": 0, "sim_pass": 7, "sim_fail": 0}
    },
    "mid": {
      "status": "PASS",
      "iterations": 3,
      "final": {"wns": 0.02, "tns": 0.0, "area": 12450, "power": 0.45}
    }
  },
  "score_trajectory": [-999, -30, 0, -15.7, -11.4, 10.0, 4.5, 10.0],
  "best_score": 10.0,
  "jobs": ["job5", "job6", ..., "job22"],
  "convergence_history": [
    {"iter": 1, "action": "rtl-gen",       "score": -999, "is_best": false},
    {"iter": 2, "action": "lint (3E)",     "score": -30,  "is_best": false},
    {"iter": 3, "action": "rtl-fix",       "score": 0,    "is_best": true},
    ...
    {"iter": 13, "action": "synth clean",  "score": 10.0, "is_best": true}
  ]
}
```

---

## 11. 파일 구조 요약

### 신규 파일

```
core/eda_loop.py                  ← LoopController + Score + Classifier + Parsers (~350줄)
workflow/synth/
├── workspace.json                ← {"name": "synth", "description": "Synthesis workspace"}
├── system_prompt.md              ← Synthesis agent 프롬프트 (~100줄)
├── commands/
│   ├── synthesize.json           ← synthesis 실행 커맨드
│   └── report.json               ← QoR 리포트 커맨드
└── todo_templates/
    └── synth-impl.json           ← synthesis task template
workflow/sta/
├── workspace.json                ← {"name": "sta", "description": "STA workspace"}
├── system_prompt.md              ← STA agent 프롬프트 (~80줄)
├── commands/
│   ├── sta-run.json              ← STA 실행 커맨드
│   └── report.json               ← Timing report 커맨드
└── todo_templates/
    └── sta-impl.json             ← STA task template
```

### 수정 파일

```
core/slash_commands.py            ← /eda-loop 커맨드 등록 (~50줄 추가)
```

---

## 12. 구현 순서 (Priority)

```
Step 1: core/eda_loop.py
        ├── LoopState dataclass
        ├── evaluate() score 함수
        ├── classify_sim_failure() classifier
        ├── _parse_lint/_parse_sim/_parse_synth parsers
        └── LoopController.run_phase_fast()

Step 2: core/slash_commands.py
        └── /eda-loop 커맨드

Step 3: 테스트 (counter.v로 Phase 1 전체 루프 검증)

Step 4: workflow/synth/ + workflow/sta/
        └── Phase 2 구현

Step 5: core/eda_loop.py
        └── LoopController.run_phase_mid()
```

---

## 13. 필요 없는 것 (명시적 제외)

| 제외 항목 | 이유 | 언제 필요? |
|-----------|------|-----------|
| LangGraph | `while` 루프 + dict로 충분 | Phase 3: 복잡한 상태 전이 |
| Prefect | `run_agent_session()` 동기 실행으로 충분 | Phase 3: 병렬 DSE |
| RPE/학습 | rule-based로 시작 | 데이터 축적 후 |
| 병렬 Synthesis | 한 버전 수렴부터 | Phase 3 |
| Wiki YAML rule | classifier 안의 if/else | rule이 20개 넘어가면 |
| n8n | Python orchestrator로 충분 | 외부 통합 필요 시 |
| PnR workspace | 물리설계는 Phase 4 | 전체 flow 안정 후 |
| RAG/Memory | 당장은 history로 충분 | iteration 100+ 쌓이면 |
