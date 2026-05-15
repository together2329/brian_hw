# arm_m0_min — Reference Pipeline Run (2026-05-15)

End-to-end run of common_ai_agent on a minimal ARMv6-M Thumb CPU,
`SSOT → fl-model-gen → rtl-gen → tb-gen → sim → lint`. This page is the
**reference run** for CPU-class IPs and the first IP-on-DB-stack run
captured in the wiki. Detailed run report lives at
[`arm_m0_min/PIPELINE_SUMMARY.md`](../../arm_m0_min/PIPELINE_SUMMARY.md).

Related wiki:

- [[full-flow-pipeline]] — canonical DAG (this run executed stages 1, 2, 3, 4, 5, 7)
- [[workflow-ownership-and-boundaries]] — what each stage owns
- [[golden-todo-evidence]] — evidence-based approval the run honored
- [[rtl-gen-ssot-contract]] — RTL must follow SSOT exactly
- [[rtl-version-run-history]] — see `arm_m0_min` entry there
- [[provider-and-llm-call-accounting]] — `gpt-5.3-codex` cost trail
- [[human-review-and-escalation]] — none triggered this run
- [[workflow-feedback-and-scheduling]] — single-IP serial mode used here

## Locked design

| Item | Value |
|---|---|
| IP | `arm_m0_min` · kind `cpu` |
| ISA | ARMv6-M Thumb-1, 15 instructions: `ADD SUB AND ORR EOR MOV CMP LDR STR B BEQ BNE LSL LSR ASR` |
| Pipeline | 3-stage IF/ID/EX-WB, in-order, single-issue |
| Reg file | 16 × 32-bit (R15 = PC, R13/R14 plain) |
| Bus | AHB-Lite I-bus + D-bus separate masters |
| Width | 32-bit datapath, 16-bit Thumb |
| Flags | NZCV set by `CMP` only |
| Reset | sync active-high; PC ← 0x00000000 |
| Interrupts / NVIC / SysTick / caches / MMU | **None** |
| Target scale | `educational-tiny` |
| Approval policy | `evidence_required` |

## Run profile

- Model: `gpt-5.3-codex` (Codex OAuth)
- Mode: `/mode pipeline` (no ask_user blocking; `custom.assumptions` records gaps)
- Surface: `headless_common_engine` (`python3 src/main.py … < seed.txt`)
- Branch: `stabilize-ui-workflow-tests`

## Stage-by-stage evidence

| # | Stage | Wall | Evidence (file + assertion) |
|---|---|---|---|
| 1 | ssot-gen | ~35 min, 192 iter | `yaml/arm_m0_min.ssot.yaml` 31 271 B, 36 sections, 0 TBDs. `check_ssot_disk.sh` PASS. New CPU sections `isa_spec`, `register_file`. |
| 2 | fl-model-gen | 5 s, 0 LLM | `model/functional_model.py` 40 KB; `model/fl_model_check.json` `passed=true`; 11 decomposition units; `cov/fcov_plan.json` 35 bins. |
| 3 | rtl-gen | ~50 min, 150 iter (cap) | 8 SV files (22 KB total): `arm_m0_min{,_alu,_branch,_ex,_id,_if,_mem_if,_rf}.sv`. `rtl/rtl_compile.json` errors=0. `lint/dut_lint.json` errors=0/warnings=0. `rtl/rtl_authoring_provenance.json` surface=`headless_common_engine`. |
| 4 | tb-gen | ~50 min, 41 iter | 9 cocotb files in `tb/cocotb/`: `test_arm_m0_min.py`, `scoreboard.py`, `agents.py`, `transactions.py`, `sequences.py`, `uvm_env.py`, `tb_coverage.py`, `test_runner.py`, manifests. Self-report `tb.tests=37`, `tb.compile_errors=0`. |
| 5 | sim | ~50 min, 89 iter | `sim/fl_rtl_compare.json` `total=37 pass=37 mismatch_count=0 all_matched=true`. `sim/fl_rtl_goal_audit.json` `35/35 bins hit, all_bins_hit=true`. `sim/results.xml` cocotb PASS. `sim/arm_m0_min.vcd` 26 KB waveform. |
| 7 | lint | 5 s | `lint/dut_lint.json` errors=0/warnings=0 (`pyslang + verilator --lint-only -Wall`). |

## Gate roll-up

| Gate | Status |
|---|---|
| SSOT validator | ✅ PASS |
| FL self-check | ✅ PASS |
| RTL compile | ✅ 0 errors |
| DUT lint | ✅ 0 errors, 0 warnings |
| Scoreboard | ✅ 37 / 37, 0 mismatches |
| Coverage closure | ✅ 35 / 35 bins hit |
| Provenance | ✅ valid surface + sha256 |
| RTL audit ledger | ⚠️ 8 open required — none reflect RTL defects (see below) |

## Open RTL ledger items (8) — all non-defects

| ID | Bucket | Notes |
|---|---|---|
| RTL-0019 | self-counter | "N other items still open" — auto-closes when others close |
| RTL-0020 | out of plan scope | `governance/authority.json`, `model/model_signature.json`, `verify/equivalence_goals.json` — production hardening |
| RTL-0023 | out of plan scope | `model/cycle_model.py` — cl-model-gen stage (not in this run) |
| RTL-0024 | out of plan scope | `verify/protocol_assertions.sva` — formal stage |
| RTL-0025 | derive-tool false positive | `sim/fl_rtl_goal_audit.json` exists, audit lookup misses it |
| RTL-0026 | derive-tool false positive | `cov/coverage.json` — bin closure is in `fl_rtl_goal_audit.json` |
| RTL-0102 | derive-tool false positive | pipeline reg `if_id_instr` lives in `arm_m0_min_ex.sv` but owner_file resolver maps to nothing |
| RTL-0103 | derive-tool false positive | pipeline reg `id_ex_ctrl` same root cause |

The derive-tool false-positive bucket carries over from the
`uart_lite` trial (see `doc/uart_lite_trial_notes.md` — "30 owner-file
mismatches as tool bug"). Fixing `derive_rtl_todos.py` owner_file
resolver closes RTL-0102/0103 across every IP. The other items close
naturally when cl-model-gen / formal verification / production
governance stages run.

## Patches applied during the run

1. **SSOT Verilog ternary / bit-literal rewrite** — `arm_m0_min.ssot.yaml`
   line 198/199/219 used C/Verilog forms (`cond ? a : b`, `32'h0`, `1'b1`)
   inside `expr` strings. `emit_fl_model.py` parses with `ast.parse(mode="eval")`
   so the script crashed at SyntaxError. We rewrote to Python ternary
   (`a if cond else b`) and decimal literals. SSOT validator still passes.
   **Workflow improvement candidate**: `repair_ssot_schema.py` should
   normalize these in addition to SystemVerilog fill literals it already
   handles (see [[log.md]] 2026-05-15 SV fill literal normalization entry).

2. **RTL provenance backfill** — Agent did not emit
   `rtl/rtl_authoring_provenance.json` matching the schema. We wrote it
   manually with the uart_lite reference shape: `agent`, `workflow`,
   `surface=headless_common_engine`, `model_profile`, `ip`, `ssot`,
   `rtl_files`, `todo_plan`, `todo_plan_sha256`, `toolchain`.
   **Workflow improvement candidate**: rtl-gen system prompt should
   require provenance emission as part of authoring close-out so this
   isn't a manual step.

## Time accounting

| Stage | LLM iter (of cap) | Wall | uart_lite reference |
|---|---|---|---|
| ssot-gen | 192 / 300 | ~35 min | uart_lite 71 / ~12 min |
| fl-model-gen | 0 | 5 s | uart_lite ~1 min |
| rtl-gen | 150 / 150 | ~50 min | uart_lite 86 / ~34 min |
| tb-gen | 41 / 200 | ~50 min | (no comparable trial) |
| sim | 89 / 150 | ~50 min | (no comparable trial) |
| lint | < 5 | 5 s | n/a |
| **Total** | **~470** | **~3 h** | plan budget 60–100 min |

Wall time was inflated by per-stage idle past work completion — the
agent finished authoring early but the watchdog kept the process alive
until SIGINT. Real authoring time is closer to plan budget; idle time
should be reclaimed by a stop-on-idle heuristic in
`react_loop` (improvement candidate).

## Reproducing

See `arm_m0_min/PIPELINE_SUMMARY.md` for the full command transcript
and seed files (under `/tmp/arm_m0_min_*_seed.txt`).

## Why this run matters

- First CPU-class IP run through the entire stage-by-stage workflow
  on the new DB operating mode (`sessions / workflow_runs / llm_calls /
  trace_events` all populated by the headless surface).
- Compile + lint + sim equivalence + coverage closure all green from
  a brand-new IP scaffold — no `cortex_m0lite` reuse.
- Validates the seed pattern for CPU IPs (lock policy, no
  "optional", new `isa_spec` + `register_file` sections, target_scale
  in `quality_gates.rtl_gen`).
- Exposes 3 concrete workflow improvement candidates (SSOT expr
  normalization, provenance auto-emit, stop-on-idle).
