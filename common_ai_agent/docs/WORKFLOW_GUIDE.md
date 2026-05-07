# Common AI Agent: Hardware IP Development Workflow Guide

## 1. Overview

This workflow implements an **AI-driven, SSOT-based hardware IP generation pipeline** that spans from requirements capture to silicon signoff. It is designed to leverage LLM automation while maintaining strict human oversight at critical decision points.

### Core Philosophy
- **SSOT (Single Source of Truth)**: The `*.ssot.yaml` file is the only authority for function model, cycle model, RTL contract, DV plan, and coverage.
- **Executable Specifications**: Every abstract model (FL/CL) must be executable Python code that can serve as a golden reference.
- **Human-in-the-Loop**: LLM handles repetitive generation and validation loops; humans own intent, approval, and ambiguity resolution.
- **Traceability**: Every RTL line, test vector, and coverage bin must trace back to an SSOT section.

---

## 2. The 9-Stage Canonical Flow

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  1. req-gen │ → │ 2. ssot-gen │ → │3. fl-model  │ → │4. equiv-goals│
│             │   │             │   │   -gen      │   │    -gen     │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
                                                           ↓
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ 9. goal-    │ ← │ 8. sim-debug│ ← │  7. sim     │ ← │  6. tb-gen  │
│    audit    │   │             │   │             │   │             │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
       ↑
┌─────────────┐
│  5. rtl-gen │
│             │
└─────────────┘
```

### Stage 1: req-gen (Requirement Capture)
**Input**: Natural language requirements, block diagrams, performance targets  
**Output**: `req/<ip>_requirements.md`  
**Owner**: Human  
**LLM Role**: Structure, reformat, detect ambiguities (`/grill-me`)

### Stage 2: ssot-gen (SSOT Generation)
**Input**: Requirements document  
**Output**: `<ip>/yaml/<ip>.ssot.yaml`  
**Key Sections**:
- `top_module`, `io_list`, `parameters`
- `function_model` (Section 6): state variables, transactions, output_rules, state_updates, invariants
- `cycle_model` (Section 7): clock, reset, latency, handshake_rules, pipeline, ordering, backpressure
- `registers`, `fsm`, `memory`, `interrupts`, `error_handling`
- `test_requirements`: scenarios, coverage_goals
- `quality_gates`: compile, lint, static, dynamic

**Owner**: Human (with LLM assist)  
**Gate**: Human approval required before downstream stages

### Stage 3: fl-model-gen (Functional Model Generation)
**Input**: SSOT `function_model` section  
**Output**:
- `model/functional_model.py` — executable Python golden reference
- `model/decomposition.json`
- `cov/fcov_plan.json` — functional coverage plan derived from transactions

**LLM Role**: Generate Python class with `apply(txn)` method  
**Self-Check**: `run_self_check()` validates model against SSOT output_rules

### Stage 4: equiv-goals-gen (Equivalence Goal Generation)
**Input**: SSOT + FL model  
**Output**: `verify/equivalence_goals.json`  
**Purpose**: Defines what "correct" means for every signal, register, and transaction.

### Stage 5: rtl-gen (RTL Generation)
**Input**: SSOT + equivalence goals  
**Output**:
- `rtl/*.sv` — SystemVerilog implementation
- `rtl/rtl_todo_plan.json` — TodoTracker-compatible task list
- `rtl/rtl_contract.json` — machine-checkable IO/sampling contract
- `logs/rtl-gen/rtl_todo_plan.json` — internal audit format

**LLM Role**: Generate RTL from SSOT + contract, iterate on lint failures  
**Quality Gates**:
- `function_model` and `cycle_model` must be present
- All derived tasks must have RTL owner modules
- Lint: 0 errors, 0 warnings

### Stage 6: tb-gen (Testbench Generation)
**Input**: RTL contract + equivalence goals + FL model  
**Output**: `tb/cocotb/*.py` (pyuvm environment)  
**Architecture**:
```
Driver → DUT(RTL) → Monitor
              ↑
    Reference: FL Model (Python)
              ↓
         Scoreboard
```

**Key Component**: `equivalence_scoreboard.py` compares `rtl_observed` against `FunctionalModel.apply()` expected values.

### Stage 7: sim (Simulation)
**Input**: TB + DUT  
**Output**:
- `sim/results.xml`
- `sim/scoreboard_events.jsonl`
- `sim/coverage.dat`

### Stage 8: sim-debug (Failure Classification)
**Input**: Scoreboard events + equivalence goals + results  
**Output**:
- `sim/fl_rtl_compare.json`
- `sim/mismatch_classification.json`

**Classification**:
| Type | Action | Owner |
|------|--------|-------|
| `rtl_bug` | LLM fixes RTL | LLM loop |
| `tb_bug` | LLM fixes TB | LLM loop |
| `fl_model_bug` | Human reviews SSOT | **Human gate** |
| `ssot_ambiguity` | Human clarifies spec | **Human gate** |

### Stage 9: goal-audit (Signoff)
**Input**: All evidence artifacts  
**Output**: `sim/fl_rtl_goal_audit.json`  
**Gate**: Human approval required for signoff

---

## 3. Human vs LLM Intervention Matrix

### Red Zones (Human Only)
| Stage | Why Human |
|-------|-----------|
| Requirements | Intent cannot be inferred by LLM |
| SSOT Approval | All downstream truth derives from here |
| FL Model Bug | SSOT itself may be wrong |
| SSOT Ambiguity | Natural language ambiguity resolution |
| Coverage Signoff | Functional completeness judgment |
| Backend Constraints | PPA targets, floorplan, timing budgets |

### Green Zones (LLM Auto-Loop)
| Stage | Validation Criteria |
|-------|---------------------|
| FL Model Generation | Self-check passes against SSOT rules |
| CL Model Generation | Latency matches SSOT spec |
| RTL Generation | Lint 0E0W, compiles successfully |
| Scoreboard Pass | Same input → same output (FL vs RTL) |
| Coverage Closure | All functional + structural targets met |

---

## 4. Coverage Strategy: FL vs CL vs RTL

| Coverage Type | Source | When to Plan | Measured By |
|--------------|--------|--------------|-------------|
| **Functional** | FL model transactions, scenarios, error cases | During SSOT/fl-model-gen | cocotb-coverage, scoreboard events |
| **Cycle** | CL model handshake rules, pipeline stages, latency bins | During cycle_model definition | CL simulation / TB protocol checks |
| **Structural** | RTL line, branch, FSM, toggle | During RTL implementation | LCOV, simulator native |

**Rule**: A coverage bin is ONLY counted when backed by a passing scoreboard row with concrete `rtl_observed` signals — not FL model copies.

---

## 5. PyMTL3 Analysis & Recommendation

### Findings
| Tool | FL/CL/RTL | cocotb Integration | Industry Adoption | LLM Friendly |
|------|-----------|-------------------|-------------------|--------------|
| **PyMTL3** | ✅ Unified | ❌ Opposite philosophy | Academic (450 stars) | ⚠️ Worse than Verilog |
| **Amaranth** | RTL only | ❌ Native Python sim | Hobbyist/Small | Moderate |
| **Chisel** | RTL+Gen | ❌ JVM ecosystem | Industry (SiFive, Google) | ❌ Scala barrier |

### Recommendation: **Do NOT adopt PyMTL3**

Your codebase already has a superior architecture:
- ✅ Python FL model (`emit_fl_model.py`)
- ✅ cocotb/pyuvm TB ecosystem
- ✅ Scoreboard comparison with golden reference
- ✅ LLM generates Verilog best (72% success vs 30% for PyMTL3)

**Better path**: Enhance `emit_fl_model.py` to also generate executable CL models (Python + delay queue), keeping cocotb/pyuvm for verification.

---

## 6. Getting Started

### Create a new IP
```bash
# 1. Start from requirements
/new-ip my_timer
/grill-me          # LLM challenges ambiguities
/to-ssot           # Generate SSOT YAML

# 2. Generate executable models
/ssot-fl-model my_timer
/ssot-equiv-goals my_timer

# 3. Generate RTL
/ssot-rtl my_timer

# 4. Generate TB and run
/ssot-tb my_timer
/sim my_timer

# 5. Debug and audit
/sim-debug my_timer
/goal-audit my_timer
```

### Load RTL TODOs into Tracker
```python
from lib.todo_tracker import TodoTracker
import json

with open("my_timer/rtl/rtl_todo_plan.json") as f:
    plan = json.load(f)

tracker = TodoTracker()
tracker.add_todos(plan["tasks"])
```

---

## 7. Architecture Decisions

### Why Python for FL/CL?
1. **LLM proficiency**: LLMs write Python better than SystemVerilog testbenches
2. **Speed of iteration**: Python simulation is orders of magnitude faster than RTL sim for algorithmic exploration
3. **Ecosystem**: NumPy, cocotb-coverage, PyUVM all integrate natively
4. **Debugging**: Python stack traces and introspection vs VPI complexity

### Why not PyMTL3 specifically?
- cocotb is the industry-standard Python verification framework
- PyMTL3's "embed SV in Python" approach conflicts with cocotb's "embed Python in SV simulator"
- Verilog generation quality from LLMs is highest for plain SV

### When does LLM loop converge?
The LLM auto-loop converges when:
1. FL model self-check passes
2. CL model latency validation passes
3. RTL lint is clean
4. Scoreboard shows 0 mismatches
5. Coverage targets are met

If mismatch classification yields `fl_model_bug` or `ssot_ambiguity`, the loop **must** escalate to human gate.

---

## 8. Backend Integration (Future)

```
RTL Signoff
    ↓
SYN (Yosys/DC) → PPA feedback → SSOT update (if needed)
    ↓
DFT (Scan insertion)
    ↓
PNR (OpenROAD/Innovus) → STA → Physical signoff
```

**Current Status**: Backend flow is human-driven. Future work: LLM-assisted constraint generation and PPA bottleneck analysis.

---

## 9. Key Files Reference

| Purpose | Path |
|---------|------|
| Workflow definition | `workflow/COMMON_ENGINE_FLOW.md` |
| SSOT template schema | `workflow/ssot-gen/rules/ssot-template.yaml` |
| FL model generator | `workflow/fl-model-gen/scripts/emit_fl_model.py` |
| Equivalence goals | `workflow/fl-model-gen/scripts/emit_equivalence_goals.py` |
| RTL TODO generator | `workflow/rtl-gen/scripts/derive_rtl_todos.py` |
| TB generator | `workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py` |
| Scoreboard runtime | `workflow/tb-gen/runtime/equivalence_scoreboard.py` |
| FL vs RTL comparator | `workflow/sim_debug/scripts/compare_fl_rtl_results.py` |
| Coverage aggregator | `workflow/coverage/scripts/ssot_coverage_summary.py` |
| Todo tracker | `lib/todo_tracker.py` |
| Template registry | `workflow/loader.py` |

---

*Generated from comprehensive codebase analysis and PyMTL3/industry verification research.*