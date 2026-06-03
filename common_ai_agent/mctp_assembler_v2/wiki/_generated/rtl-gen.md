---
title: RTL Generation
type: reference
tags: [workflow, rtl-gen, rtl]
status: stable
---

# RTL Generation

`rtl-gen` translates the validated SSOT into synthesizable SystemVerilog, driving every SSOT-derived TODO and quality gate to `pass` with fresh compile/lint evidence. It is a contract-first SSOT→RTL translation workflow: existing RTL is reuse evidence only, and any disagreement with SSOT ports/names/hierarchy is repaired, not accepted. See [[ssot-gen]] for the contract and [[workflow-stages]] for the pipeline.

## Purpose

Produce `rtl/*.sv` plus `list/<ip>.f` that implement the SSOT `function_model`/`cycle_model`/`registers`/`fsm`/`io_list` behavior, then prove DUT-only compile and lint cleanliness — the mandatory gate before [[tb-gen]] and [[sim]].

## How to run

The `/ssot-rtl <ip>` stage engine runs `derive_rtl_todos.py` before the agent's turn (writing the TODO ledger), then the LLM writes the RTL files. From the project root / active IP root:

```bash
# derive (or refresh + audit) the SSOT-derived RTL TODO ledger
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py <ip> --root . --audit-rtl
# canonical DUT compile evidence
python3 workflow/rtl-gen/scripts/rtl_compile_report.py <ip> --top <top_module> --project-root .
# DUT-only lint evidence (see [[lint]])
python3 workflow/lint/scripts/dut_lint_report.py <ip> --top <top_module>
```

`/ssot-rtl` is an internal slash command (`handler: stage:ssot-rtl`), not a shell command. Use `$ATLAS_WORKFLOW_ROOT`/`$ATLAS_PROJECT_ROOT`/`$ATLAS_IP_ROOT` in split workspaces.

## Scripts

| script | does |
| --- | --- |
| `derive_rtl_todos.py` | Convert SSOT into the active RTL TODO ledger (`rtl/rtl_todo_plan.json`, `rtl/rtl_todo_tracker.json`, `todo/rtl_todo_tracker.json`); imports every `workflow_todos.rtl-gen[]` and `rtl_gate.rtl_gen` gate; `--audit-rtl` checks owner-logic/placeholder-free/IO-contract/hierarchy/integration/freshness gates. |
| `rtl_compile_report.py` | Run the canonical DUT RTL compile check and write machine-readable `rtl/rtl_compile.json`. |
| `ssot_to_rtl.py` | SSOT→RTL preflight bridge: blocks on missing semantics, stale artifacts, missing manifest files / filelist / provenance. Does not author production RTL. |
| `ssot_to_rtl.sh` | Shell wrapper for the SSOT→RTL preflight/handoff. |
| `check_register_contract.py` | Verify RTL register bit layout matches `SSOT.registers.register_list[]` exactly. |
| `check_single_driver.py` | Check every sequential signal/output is driven by exactly one always block (catches multi-driver races). |
| `prepare_rtl_human_review.py` | Build human-review packets for gates that must not auto-approve; writes `draft_rtl_blocker_answers` for later locking via `resolve_rtl_blockers.py`. |
| `profile_rtl_reference.py` | Profile an external reference RTL tree for scale calibration only (`reports/rtl_reference_profile.json`); never copies/transforms reference RTL. |
| `refresh_rtl_provenance.py` | Refresh filelist/provenance after SSOT metadata-only gate updates (does not bless manual RTL). |
| `build_gate.sh` | RTL build-time gate orchestrator: run SSOT-driven contract checks before the simulator touches the design. |
| `lint.sh` / `syn_check.sh` | Quick RTL lint of a file / synthesis feasibility check (hook helpers). |
| `check_rtl_disk.sh` | Disk-truth validator: reads filelist + each file size + iverilog compile. |
| `derive… / post_write.sh / error_capture.sh / disk_diff.sh / find-mas.sh` | Hook helpers: post-write logging, error capture, disk-diff injection, MAS file discovery (legacy). |

## Method / key rules

- **Strict SSOT authority.** Implement only behavior present in SSOT fields and `rtl_todo_plan.json`. No canonical SSOT → `[SSOT REQUIRED] -> ssot-gen`. Missing behavior stays `TBD (missing in SSOT)` + `[SSOT TBD REPORT]`; DONE states `SSOT TBD REPORT: none`. `ask_user`/`record_ssot_qa` are disabled here — the contract is on disk.
- **Syntax policy (synthesizable `.sv` subset).** ANSI `input logic`/`output logic`/`inout wire`; portable `always @(posedge clk …)` / `always @(*)`; shared params in `rtl/<ip>_param.vh` (included, never listed as compile source). **Banned:** `typedef`, `enum`, `always_ff/comb/latch`, `package`/`import`, `interface`/`modport`, `function`/`task`, `for`/`while`, `initial`, `#delay`, `'0`/`'1` literals, `*_pkg`.
- **Anti-hallucination.** No "RTL written" without `write_file`; no "lint clean / compile OK" without the canonical `run_command` whose output is cited. Filelist must list every written file; one module per file (filename = module name, top is `rtl/<ip>.sv`).
- **Coding discipline.** Single-driver sequential signals; default assignments to avoid latches; correct-width constants; no procedural parameterized part-selects (precompute via assigns); prefer shift-based arithmetic; parameterize tunable widths and use every declared parameter; honor `cycle_model.latency` exactly (latency-1 = registered result on the accepting edge, not two-edge).
- **Large-file chunking.** Split >800-line writes into many small files or skeleton+`replace_in_file` to avoid `max_tokens` truncation.
- **Gate closure.** Continue until every required `rtl/rtl_todo_plan.json` task (including `rtl_gate.rtl_gen` gates) is `todo_completion.status=pass` after `--audit-rtl`. Production profile adds locked authority manifest/signature, target-scale depth, protocol-assertion sim, FL-vs-RTL goal audit, and coverage-closure gates. The engine writes `rtl/rtl_authoring_provenance.json` — the LLM must not.
- **Approval repair mode.** On fresh sim/sim-debug DUT failures, build a failure→RTL ledger, patch the owning manifest module minimally (never edit TB/sim to hide failures), recompile, and hand off.

## Inputs → Outputs

- **Inputs:** `<ip>/yaml/<ip>.ssot.yaml`, `<ip>/rtl/rtl_todo_plan.json`, `<ip>/model/decomposition.json` (production), `<ip>/verify/equivalence_goals.json` (for module-level fixes).
- **Outputs:** `<ip>/rtl/*.sv`, `<ip>/rtl/<ip>_param.vh` (optional), `<ip>/list/<ip>.f`, `<ip>/rtl/rtl_compile.json`, `<ip>/rtl/rtl_traceability.json`, `<ip>/rtl/rtl_contract.json`, `<ip>/rtl/rtl_authoring_provenance.json` (engine-written), and `<ip>/lint/dut_lint.json` (via [[lint]]).

## Structure — SSOT → RTL mapping

Files come from `sub_modules[]` + `filelist.rtl[]` (no fixed submodule set). `ownership: manifest` → this session writes the file; `ownership: child_ssot` → instantiate only, child workflow owns it. Section processing order: `top_module` → `parameters` → `io_list.interfaces`/`clock_domains` → `registers` → `function_model` → `cycle_model` → `fsm` → `features`+`dataflow` → `memory` → `interrupts` → `workflow_todos.rtl-gen[]` → `filelist`. Default FSM style: `localparam` state encodings + one sequential state-register block + one combinational next-state/output-decode block.

## Related

Upstream: [[ssot-gen]], [[fl-model-gen]]. Gated by [[lint]]. Downstream: [[tb-gen]], [[sim]], [[coverage]], [[syn]]. Back to [[workflow-stages]].
