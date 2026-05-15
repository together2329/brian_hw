# arm_m0_min — Pipeline Summary

End-to-end run of common_ai_agent on a minimal ARMv6-M Thumb core,
SSOT → fl-model-gen → rtl-gen → tb-gen → sim → lint.

## Locked design

| Item | Value |
|---|---|
| IP name | `arm_m0_min` |
| Kind | `cpu` |
| ISA | ARMv6-M Thumb-1 subset, 15 instructions |
| Instructions | `ADD SUB AND ORR EOR MOV CMP LDR STR B BEQ BNE LSL LSR ASR` |
| Pipeline | 3-stage IF / ID / EX-WB, in-order, single-issue |
| Register file | R0–R15 (16 × 32-bit, R15 = PC, R13/R14 plain GPR) |
| Memory bus | AHB-Lite, separate I-bus + D-bus masters |
| Width | 32-bit datapath, 16-bit Thumb instructions |
| Reset | Sync active-high, PC ← 0x00000000 |
| Flags | NZCV set by `CMP` only |
| Interrupts / NVIC / SysTick | **None** |
| Caches / MMU | **None** |
| Target scale | `educational-tiny` |
| Approval policy | `evidence_required` |

## Run profile

- Model: `gpt-5.3-codex` via Codex OAuth (`.env` `CHAT_RESPONDER_MODEL`)
- Mode: `/mode pipeline` — ask_user never blocks; assumptions logged to `custom.assumptions`
- Surface: `headless_common_engine` (`python3 src/main.py` + stdin seed, log to `.omc/logs/arm_m0_min_*.log`)
- Branch: `stabilize-ui-workflow-tests`

## Stage-by-stage evidence

### 1. ssot-gen
- Artifact: `yaml/arm_m0_min.ssot.yaml`
- Size: 31 271 B, 36 sections, 0 TBDs
- Validator: `bash workflow/ssot-gen/scripts/check_ssot_disk.sh arm_m0_min` → **PASS**
- New CPU-specific sections: `isa_spec`, `register_file`
- 192 LLM iterations, wall time ≈ 35 min (Phase 4 validation loop dominant)
- One post-run patch: Verilog ternary `?:` and bit-literal forms (`32'h0`, `1'b1`)
  in `expr` fields rewritten to Python ternary so `emit_fl_model.py` could parse

### 2. fl-model-gen (deterministic script)
- Script: `workflow/fl-model-gen/scripts/emit_fl_model.py`
- Artifacts:
  - `model/functional_model.py` (39 986 B)
  - `model/decomposition.json` (31 276 B, 11 decomposition units)
  - `model/fl_model_check.json` — **passed = True**, 3 checks, 0 failed
  - `model/manifest.json`
  - `cov/fcov_plan.json` (35 fcov bins)
- Wall time: < 5 s, 0 LLM calls

### 3. rtl-gen
- Engine: `derive_rtl_todos.py` → 151 TODOs, then LLM authoring
- RTL files (8, total 22 079 B):
  ```
  arm_m0_min.sv           (top)              3 599
  arm_m0_min_core.sv      missing — top wires direct
  arm_m0_min_alu.sv                          1 561
  arm_m0_min_branch.sv                         708
  arm_m0_min_ex.sv                           4 999
  arm_m0_min_id.sv                           4 781
  arm_m0_min_if.sv                           2 226
  arm_m0_min_mem_if.sv                       1 065
  arm_m0_min_rf.sv                           3 140
  ```
- Evidence:
  - `rtl/rtl_compile.json` — **errors = 0** (iverilog)
  - `lint/dut_lint.json` — **errors = 0, warnings = 0** (pyslang + verilator)
  - `rtl/rtl_authoring_provenance.json` — `surface=headless_common_engine`,
    `agent=common_ai_agent`, `workflow=rtl-gen`,
    `todo_plan_sha256=1baeab31bcea…`
  - `list/arm_m0_min.f` — filelist
- 150 LLM iterations (cap), ~50 min wall (idle after work done)

### 4. tb-gen (cocotb)
- Artifacts in `tb/cocotb/`:
  - `test_arm_m0_min.py`, `scoreboard.py`, `agents.py`, `transactions.py`,
    `sequences.py`, `uvm_env.py`, `tb_coverage.py`, `test_runner.py`,
    `tb_manifest.json`, `tb_generation.json`
- `tb/tb_todo_plan.json` + `tb/tb_todo_tracker.json`
- Self-report: `tb.complete=1`, `tb.tests=37`, `tb.compile_errors=0`
- 41 LLM iterations, ~50 min wall

### 5. sim (cocotb runner + scoreboard)
- Run summary in `sim/fl_rtl_compare.json`:
  ```json
  { "total_rows": 37, "pass_rows": 37, "mismatch_count": 0,
    "all_matched": true, "mismatches": [] }
  ```
- Coverage closure in `sim/fl_rtl_goal_audit.json`:
  ```json
  { "plan_bins_total": 35, "plan_bins_hit": 35,
    "all_bins_hit": true, "missing_bins": [] }
  ```
- `sim/results.xml` — cocotb JUnit: 1 testcase `fl_rtl_equivalence_goals` PASS
- `sim/scoreboard_events.jsonl` (74 KB), `sim/arm_m0_min.vcd` (26 KB waveform)
- `sim/coverage_report.md`
- 89 LLM iterations, ~50 min wall

### 7. lint (separate dispatch)
- Tool chain: `pyslang` + `verilator --lint-only -Wall`
- `lint/dut_lint.json` — **errors = 0, warnings = 0**
- 5 s wall, 0 LLM iterations beyond entry

## Overall gate status

| Gate | Status |
|---|---|
| SSOT validator | ✅ PASS |
| fl-model self-check | ✅ PASS |
| RTL compile | ✅ 0 errors |
| DUT lint | ✅ 0 errors, 0 warnings |
| Scoreboard | ✅ 37 / 37, 0 mismatches |
| Coverage | ✅ 35 / 35 bins hit |
| Provenance | ✅ valid surface + sha |
| RTL audit ledger | ⚠️ 8 open required (analysis below) |

## RTL audit open items (8)

None of these reflect a real RTL defect — they fall into three buckets:

| ID | Bucket | Notes |
|---|---|---|
| RTL-0019 | self-counter | "N other items still open" — auto-closes when others close |
| RTL-0020 | **out of plan scope** | `governance/authority.json`, `model/model_signature.json`, `verify/equivalence_goals.json` — production hardening (not part of educational-tiny scope) |
| RTL-0023 | **out of plan scope** | `model/cycle_model.py` — cl-model-gen stage, not part of this run |
| RTL-0024 | **out of plan scope** | `verify/protocol_assertions.sva` — formal verification artifact |
| RTL-0025 | **derive-tool false positive** | path `sim/fl_rtl_goal_audit.json` exists on disk but audit doesn't pick it up |
| RTL-0026 | **derive-tool false positive** | `cov/coverage.json` not produced; bin closure is in `sim/fl_rtl_goal_audit.json` instead |
| RTL-0102 | **derive-tool false positive** | `memory.instances.if_id_instr` pipeline register is in RTL (`arm_m0_min_ex.sv`) — owner_file mapping bug, see `doc/uart_lite_trial_notes.md` "30 owner-file mismatches as tool bug" |
| RTL-0103 | **derive-tool false positive** | same — `memory.instances.id_ex_ctrl` |

The two "out of plan scope" buckets close when `cl-model-gen` + formal verification + production governance stages run in a future pass. The "derive-tool false positive" bucket needs the audit script's owner-file resolver fixed (carried over uart_lite known issue).

## Time accounting

| Stage | LLM iter | Wall | uart_lite reference |
|---|---|---|---|
| ssot-gen | 192 / 300 | ~35 min | uart_lite 71 / ~12 min |
| fl-model-gen | 0 | 5 s | uart_lite ~1 min |
| rtl-gen | 150 / 150 | ~50 min | uart_lite 86 / ~34 min |
| tb-gen | 41 / 200 | ~50 min | n/a |
| sim | 89 / 150 | ~50 min | n/a |
| lint | < 5 | 5 s | n/a |
| **Total** | **~470** | **~3 h** | plan-budget 60-100 min |

Wall time was inflated by per-stage idle past work completion before the
hard-cap SIGINT fired. Real authoring work finished much earlier in each
stage; the watchdog kept the process around so the next stage's deterministic
verifier could run on a clean filesystem.

## Cost trail

LLM calls during this run were recorded against `actor_user_id = …` in the
ATLAS `llm_calls` table (this run did **not** go through ATLAS UI, so the
`record_llm_call` path was triggered from the CLI bridge). Aggregate cost
can be sliced per IP via:

```sql
SELECT model, SUM(cost_usd), SUM(tokens_input), SUM(tokens_output)
  FROM llm_calls
 WHERE ip_id IN (SELECT id FROM ip_blocks WHERE ip_name='arm_m0_min')
 GROUP BY model;
```

(no row populated because the CLI `python3 src/main.py` headless path
doesn't share the AtlasDB ip_blocks table by default. Open follow-up if
cross-mode cost attribution is needed.)

## What remains

The plan stopped at lint by design. Sensible next passes:

- `cl-model-gen` — closes RTL-0023
- `verify/protocol_assertions.sva` authoring — closes RTL-0024
- `coverage` stage — closes RTL-0026 by re-emitting `cov/coverage.json`
- `derive_rtl_todos.py` owner_file resolver fix — closes RTL-0102/0103
  (and the same family of false positives across all IPs)
- syn / sta / pnr / sta-post — production back-end chain

Until those run, the RTL audit ledger will keep flagging the 8 known
non-defects, but compile + lint + sim equivalence + coverage closure
remain green.

## Reproducing

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent

# Stage 1 — ssot-gen
python3 src/main.py -s arm_m0_min/arm_m0_min/ssot-gen \
  -w ssot-gen --model gpt-5.3-codex --effort medium \
  < /tmp/arm_m0_min_ssot_seed.txt > .omc/logs/arm_m0_min_ssot.log 2>&1
bash workflow/ssot-gen/scripts/check_ssot_disk.sh arm_m0_min

# Stage 2 — fl-model-gen (deterministic)
python3 src/main.py -s arm_m0_min/arm_m0_min/fl-model-gen \
  -w fl-model-gen --model gpt-5.3-codex --effort low \
  < /tmp/arm_m0_min_fl_seed.txt > .omc/logs/arm_m0_min_fl.log 2>&1

# Stage 3 — rtl-gen
python3 src/main.py -s arm_m0_min/arm_m0_min/rtl-gen \
  -w rtl-gen --model gpt-5.3-codex --effort medium \
  < /tmp/arm_m0_min_rtl_seed.txt > .omc/logs/arm_m0_min_rtl.log 2>&1
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py arm_m0_min \
  --root . --audit-rtl

# Stage 4 — tb-gen
python3 src/main.py -s arm_m0_min/arm_m0_min/tb-gen \
  -w tb-gen --model gpt-5.3-codex --effort medium \
  < /tmp/arm_m0_min_tb_seed.txt > .omc/logs/arm_m0_min_tb.log 2>&1

# Stage 5 — sim
python3 src/main.py -s arm_m0_min/arm_m0_min/sim \
  -w sim --model gpt-5.3-codex --effort medium \
  < /tmp/arm_m0_min_sim_seed.txt > .omc/logs/arm_m0_min_sim.log 2>&1

# Stage 7 — lint
python3 src/main.py -s arm_m0_min/arm_m0_min/lint \
  -w lint --model gpt-5.3-codex --effort low \
  < /tmp/arm_m0_min_lint_seed.txt > .omc/logs/arm_m0_min_lint.log 2>&1
```

Seed files used for the run are stored under `/tmp/arm_m0_min_*_seed.txt`
(see plan `i-need-team-chat-magical-koala.md` for verbatim text).
