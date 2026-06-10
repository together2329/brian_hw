# Stage Validation Run — pulse_counter_v1 (2026-06-10)

Phase-1 manual walk of req → ssot → fl/cl → rtl → tb → sim on a fresh small IP
(APB pulse counter), with the agent playing each stage's LLM role and every
gate run for real. Scratch root: `.tmp/pc1/project` (worktree off main
67840407+). Goal: prove each stage's machinery/gates work and locate gaps
before building the phase-2 headless worker.

## Verdict per stage

| Stage | Machinery | Gates | Result |
| --- | --- | --- | --- |
| req (lock + bundle) | lock_requirement_set --from-candidate | check_contract_bundle | PASS (3 req / 5 obl / 9 evidence, closure 9/9) |
| ssot | repair_ssot_schema scaffold + LLM semantic core | verify_ssot + check_ssot_disk + check_design_spec_trace | PASS (34 sections, 0 TBD) |
| fl/cl model | emit_fl_model / emit_cycle_model / emit_model_signature / emit_equivalence_goals | check_fl_model_artifacts + check_model_contract_trace | PASS |
| rtl | LLM-authored 3 modules + ssot_to_rtl preflight + refresh_rtl_provenance | derive_rtl_todos --audit-rtl + dut_lint_report + check_single_driver + rtl_compile_report | PASS (189 todos, gate=pass, lint 0/0) |
| tb | emit_goal_scoreboard_cocotb (8 files) + emit_timing_header + LLM patches | check_pyuvm_structure + check_tb_magic_numbers + check_no_ip_coverage_workarounds + check_tb_python_compile | PASS |
| sim | cocotb+iverilog runner, VCD, scoreboard_events.jsonl, SIM ESCALATE | check_sim_pass / check_scoreboard_events / check_tb_sim_evidence | machinery PASS; goal closure OPEN (24) — gates correctly FAIL (exit 1), escalation routed owner=sim_debug |

Key positive: **no silent pass anywhere**. Every fake/incomplete state I
produced was rejected with an actionable message, including my own direct-edit
RTL being caught by the provenance gate.

## Findings (machinery gaps / authoring contracts learned)

1. **behavioral_contracts entries need `stage_contracts[]`** (and obligations
   need structural/behavioral refs; evidence must close EVERY contract id —
   central + structural + behavioral).
2. **fl/cl per-contract evidence is worker-authored**: emit_fl_model/_cycle_model
   do NOT propagate SSOT `contract_refs` into self-check rows, while
   check_model_contract_trace requires per-contract rows. The worker must join
   the SSOT-declared linkage onto passing rows (see `.tmp/pc1/augment_model_checks.py`).
3. **repair_ssot_schema merges `rtl_contract`** — stale scaffold ports survive
   an io_list replacement. Fix: drop the section and re-run repair.
4. **check_register_contract is AXI-only** (`{ip}_regs.sv` + `s_axi_rdata`
   hardcoded) — APB IPs cannot use this gate at all.
5. **SSOT expr fields are ast-parsed Python** (`&&`/prose rejected) and
   `emit_cycle_model` blocks undeclared symbols (`count_next`).
6. **Scaffold sections are todo-generative**: an unreplaced template `fsm`
   section produced 15 phantom "Implement FSM state/transition" RTL todos.
   Authoring the truth (`no_fsm`) removed them.
7. **`implements` is mandatory per manifest submodule** (refs alone don't
   satisfy `_module_contract_ready`) — ssot_to_rtl blocks with RTL_MODULE_CONTRACTS.
8. **emit_timing_header silently skips** entries without
   `min_ns/max_ns/max_cycles/min_cycles/value` keys (bare `cycles:` ignored, no
   warning), and emit_goal_scoreboard_cocotb still emits literal 3/4 waits that
   check_tb_magic_numbers then flags — the worker must regenerate-then-patch
   with `<ip>_timing.py` constants after every TB regen.
9. **Gate CLI conventions are inconsistent**: most take `--root`, but
   check_pyuvm_structure.sh / check_no_ip_coverage_workarounds.sh /
   check_sim_pass.sh are cwd-relative (must run from the IP parent).
10. **Stimulus contract is the real frontier (P0 confirmed again)**: the
    goal-driven generic TB cannot express IP-specific preconditions (APB CTRL
    write before pulses). `test_requirements.scenarios[].stimulus_machine_spec`
    (timeline: csr_write/assign/wait_cycles/wait_until) is the SSOT-driven path
    and executes, but per-goal reset + the trailing generic `_drive_inputs`
    vector interact badly: VCD shows edge_detect firing 39× while enable
    windows rarely overlap pulse windows, count_fire fired once at a goal
    boundary and was wiped by the next per-goal reset, and generic vectors
    side-wrote CLEAR (clear_trigger toggled 7×). EQ_TRANSACTION_* goals have no
    machine_spec channel at all (emitter only wires scenarios). Closure needs
    either an IP-specific TB layer (mctp pattern) or emitter support for
    transaction-goal machine_specs + cleaner isolation around scenario goals.

## Evidence locations

Scratch IP: `<worktree>/.tmp/pc1/project/pulse_counter_v1/` — req/ (locked
bundle), yaml/ (SSOT), model/, verify/equivalence_goals.json, rtl/ (+provenance),
lint/dut_lint.json, tb/cocotb/, sim/scoreboard_events.jsonl + VCD,
logs/gates/*.json. Helper scripts: `.tmp/pc1/{edit_ssot_core,patch_ssot_projection,augment_model_checks}.py`.

## Phase-2 plan (headless worker)

Sequence the proven loop: author/lock req → scaffold+project SSOT → emit fl/cl
(+contract-evidence join) → preflight ssot_to_rtl → author RTL + provenance →
emit TB + timing patch → sim → on scoreboard escalation enter the sim_debug
loop. Each step = run gate, parse actionable errors, repair owning artifact,
re-run — exactly the iteration this run did manually. Items 2/8 (worker-side
joins/patches) become deterministic post-steps; item 10 is the open design
question to resolve first (transaction-goal stimulus channel).

Related: [[contract-reflection-workflow]], [[locked-truth-design-spec-workflow]],
[[atlas-worker-workflow-ui-sync-20260610]].


## 2026-06-10 follow-up — FULL closure achieved

After the CAND-06/08 machinery batch (commit 8688bbcb) plus a second round,
pulse_counter_v1 reached an honest full pipeline PASS: scoreboard 31/31 goals,
check_scoreboard_events / check_tb_sim_evidence / check_sim_disk all exit 0,
and the complete stage battery (req bundle, ssot, fl/cl trace, rtl audit,
register contract, lint, tb structure/magic) green. mctp register-gate verdict
unchanged (4 honest findings).

Second-round general fixes (all machinery, validated on pc1 + mctp no-change):
- scenario `transaction:` field is authoritative over alias text-matching
  (emit_equivalence_goals).
- runtime stimulus inheritance: a goal without machine_spec runs the spec of
  the FM transaction the FL oracle resolves (donor map keyed by
  stimulus_contract.transaction_id; exact, replaces kind heuristics that were
  wrong in both directions).
- timeline `csr_read` step (APB read-back; case-insensitive ports).
- ssot_to_rtl preflight now ALWAYS refreshes rtl_contract.json (soft-question
  runs used to skip the write — SSOT rule renames never propagated), and
  collects output_rules from EVERY function_model transaction (union by name;
  primary-only collection dropped secondary-transaction observables).
- check_sim_disk accepts the generated runner layout (sim/cocotb_build/*.vvp).

Authoring contract learned: FL output_rules evaluate against PRE-transaction
state — "read-back shows the post-edge count" is authored as `count + 1`, and
timelines end with `csr_read` so the DUT's read-data is fresh at sampling.

Invocation gotchas (CAND-11 additions): check_sim_pass.sh ignores positional
args (IP_NAME env or TOOL_OUTPUT only) and check_sim_disk.sh resolves its
sibling script relative to the repo root.
