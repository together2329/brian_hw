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
- [[human-review-and-escalation]] — human req approval is the current final blocker
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

## 2026-05-17 Evidence Refresh

Purpose: re-audit `arm_m0_min` after hidden cocotb soft-mismatch failures were
found. The rule for this refresh was **no pass-for-pass**: cocotb JUnit PASS
alone is insufficient; `scoreboard_events.jsonl`, `fl_rtl_compare.json`,
coverage, compile, lint, and goal audit must agree.

Commands/evidence from the refresh:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_coverage_summary.py \
  tests/test_fl_rtl_equivalence_loop.py::test_scoreboard_uses_goal_specific_comparison_policy_for_reset_debug_and_cycle_goals -q

python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py arm_m0_min --root .
python3 workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py arm_m0_min --root .
COMMON_AI_AGENT_ROOT=/Users/brian/Desktop/Project/brian_hw/common_ai_agent \
  python3 arm_m0_min/tb/cocotb/test_runner.py
python3 workflow/coverage/scripts/ssot_coverage_summary.py arm_m0_min
bash workflow/tb-gen/scripts/check_tb_sim_evidence.sh arm_m0_min
python3 workflow/sim_debug/scripts/compare_fl_rtl_results.py arm_m0_min --root .
python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py arm_m0_min --root .

cd arm_m0_min && iverilog -g2012 -o /tmp/arm_m0_min_fresh_compile.vvp -f list/arm_m0_min.f
cd arm_m0_min && verilator --lint-only -Wall -f list/arm_m0_min.f
```

Refresh result:

| Gate | 2026-05-17 result |
|---|---|
| Targeted regression tests | PASS, 5 tests |
| Cocotb JUnit | PASS, 1 test, 0 failures/errors |
| Scoreboard rows | PASS, 39 required / 39 rows / 39 goals covered |
| FL-vs-RTL compare | PASS, 39 checked / 39 passed / 0 failed / 0 stale |
| Function coverage | PASS, 19 / 19, 100% |
| Cycle coverage | PASS, 17 / 17, 100% |
| RTL compile | PASS, `iverilog -g2012` |
| RTL lint | PASS, `verilator --lint-only -Wall` |
| Goal audit | FAIL only on `req` human gate: 15 / 16 checks pass |

Completion audit:

- [`arm_m0_min/doc/arm_m0_min_completion_audit.md`](../../arm_m0_min/doc/arm_m0_min_completion_audit.md)
  maps the user objective to concrete artifacts and explicitly records the
  stop condition.
- [`arm_m0_min/doc/arm_m0_min_requirement_review.md`](../../arm_m0_min/doc/arm_m0_min_requirement_review.md)
  is the pending human review packet. It is not accepted as a requirement
  artifact until it is promoted into `arm_m0_min/req/` by human approval.
- [`arm_m0_min/review/decision_needed_req_requirement_approval.json`](../../arm_m0_min/review/decision_needed_req_requirement_approval.json)
  is the open UI/orchestrator review decision item for the same blocker.
  `promote_requirement_review.py` resolves this queue item when a human
  approver is supplied and the reviewed packet is promoted into `req/`.
- `/api/pipeline/state?ip=arm_m0_min` now surfaces this honestly:
  `orchestrator.decisions_needed=1`, `stages.goal-audit.state=failed`, and
  `stages.goal-audit.error_summary=blockers=req`. The UI must not treat a
  failed `sim/fl_rtl_goal_audit.json` as a passing stage merely because the
  artifact exists.
- Approval promotion was dry-run on a temporary copy: after promotion, the
  copied final audit passed 16 / 16 with `req_ok=true`, and the copied review
  decision was marked `resolved`. The audit now requires both the approved
  requirement markdown and `req/approval_manifest.json` with a matching
  `target_sha256` and `source_sha256`, and the requirement approval review
  decision must be resolved. The review decision also pins
  `evidence.approval_target.sha256`, and `promote_requirement_review.py`
  rejects stale source path/hash mismatches before writing `req/`. It also
  validates pinned `evidence.machine_evidence_snapshot` hashes for the SSOT,
  FL-vs-RTL compare, coverage, and completion-audit files. A long hand-written
  `req/*.md` file alone cannot satisfy the human gate. The real IP remains
  blocked until a real human approval is applied.

Current interpretation:

- The CPU RTL/TB/sim equivalence path is green at the machine-evidence level:
  39/39 FL-vs-RTL goals pass, no mismatches are classified, and coverage bins
  are backed by passing scoreboard rows with real `rtl_observed` signals.
- The run is **not final signoff green** because
  `arm_m0_min/req/*.md` does not contain a human-approved requirement document.
  This blocker must stay human-owned; auto-generating a 1000-byte requirement
  file would be a pass-for-pass anti-pattern.
- A review packet was prepared at
  `arm_m0_min/doc/arm_m0_min_requirement_review.md`. It captures the locked CPU
  scope and current evidence, but it is deliberately outside `req/` and marked
  pending review so it cannot masquerade as approved requirement evidence.
- `arm_m0_min/cov/coverage.json` still reports `status=blocked` for structural
  line/branch coverage because there is no `coverage.info` instrumentation in
  this refresh. The goal audit's `functional_coverage` check passes because the
  function/cycle domains are fully covered by RTL-observed scoreboard evidence.

Workflow fixes made during the refresh:

- `tb-gen` reset-goal detection now distinguishes actual asserted-reset goals
  from state transitions such as `RESET -> RUN`.
- Generated TB stimulus now uses safe AHB-like defaults:
  `_hready=1`, `_hresp=0`, `_hrdata=0`, and constraint-driven overrides for
  `i_hready==0`, `d_hready==0`, and `hresp==ERROR`.
- Generated TB now resets the DUT between independent non-reset equivalence
  goals, so PC/state accumulation cannot hide or create mismatches.
- The scoreboard has goal-specific compare policies for reset/state/cycle
  goals and treats internal pipeline-latch `memory.instances` as internal
  register memory, not as mandatory external D-bus transfers.
- Coverage summary now maps high-level SSOT bins such as `FCOV_TX_LOAD_STORE`,
  `CCOV_IF_STALL`, `CCOV_MEM_STALL`, and `CCOV_PIPELINE_ORDER` only from
  passing scoreboard rows with real RTL observations.

Remaining non-signoff limitation:

- Internal pipeline latch memory goals currently prove observable top-level
  behavior (`fault_halt=0`, active instruction fetch, PC/address coherence, and
  overlapping model outputs such as `d_haddr/d_hwrite`). They do not yet prove
  the hidden latch contents directly unless hierarchical probes are exposed.
  This is acceptable as non-signoff evidence but should be tightened with
  pyslang/hierarchy-aware probes before claiming deep microarchitectural
  retention proof.

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
   handles (see [[log]] 2026-05-15 SV fill literal normalization entry).

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
