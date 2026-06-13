---
title: SSOT Generation
type: reference
tags: [workflow, ssot-gen, ssot]
status: stable
---

# SSOT Generation

`ssot-gen` authors and validates `<ip>/yaml/<ip>.ssot.yaml`, the Single Source of Truth that every downstream stage treats as binding contract. It owns the SSOT contract only — it writes no RTL, TB, sim, firmware, or docs — and finishes with a `[SSOT HANDOFF] -> rtl-gen` block once validation passes. See [[workflow-stages]] for the full pipeline.

## Purpose

Transform requirements (or imported docs/RTL) into a complete, machine-parsable YAML SSOT that captures top-module identity, hierarchy ownership, interfaces, registers, function/cycle behavioral models, DV plan, coverage goals, EDA targets, and downstream workflow TODOs — so [[fl-model-gen]], [[rtl-gen]], [[tb-gen]], and the EDA stages can implement with traceability from spec to silicon.

## How to run

Run from the project root (the directory containing `<ip>/`). SSOT authoring is LLM-driven via `/new-ip <ip>`, `/import`, `/grill-me`, and `/to-ssot`; deterministic scripts are contract checkers by default:

```bash
# validate shape + ATLAS Preview anchors + run check_ssot_disk.sh (writes req/ssot_validation.json)
python3 workflow/ssot-gen/scripts/verify_ssot.py <ip> --root . --mode engineering
# disk-truth pass/fail authority
bash workflow/ssot-gen/scripts/check_ssot_disk.sh <ip> --root . --mode engineering
# explicit rescue only: canonicalize an existing SSOT and write downstream blockers/provenance
python3 workflow/ssot-gen/scripts/repair_ssot_schema.py <ip> --root . --mode engineering
```

Modes are `starter` (3 sections), `engineering` (all except `dft`/`pnr`), and `signoff` (all 36). Keep `verify_ssot` blockers at zero before advancing to `/to-ssot` signoff or [[fl-model-gen]]. When `/repair-ssot` is used explicitly, also inspect and clear `ssot_downstream_blockers.json`; do not treat repair output as a substitute for LLM-owned YAML semantics.

## Scripts

| script | does |
| --- | --- |
| `repair_ssot_schema.py` | Explicit rescue tool: upgrade an existing SSOT to canonical section order; derive missing model/sign-off sections from existing facts + approved Q&A; quote expression scalars; expand bracketed flow-mappings; write `req/ssot_downstream_blockers.json` and `<ip>.ssot.provenance.json`. Structure repair, not the default authoring loop and not an IP generator. |
| `verify_ssot.py` | Read-mostly validator: checks top-level shape (no `ssot:`/`sections:` wrapper, no legacy aliases), required-by-mode sections, ATLAS Preview anchors, and runs `check_ssot_disk.sh` internally; writes `req/ssot_validation.json` with `blockers`/`warnings`. |
| `check_ssot_disk.sh` | Disk-truth pass/fail authority (file ≥ size threshold, all required section keys, parses as YAML, substantive function/cycle models, ≤5 live `<TBD>` markers). |
| `validate_yaml.sh` | Cerberus schema validation across YAML SSOT files. |
| `approved_to_ssot.py` | Bridge: convert ATLAS Web Q&A/import/wiki ledger into the canonical SSOT shape so downstream works from disk truth, not a chat transcript. |
| `resolve_rtl_blockers.py` | Apply rtl-gen semantic blocker answers back into the SSOT (function_model, cycle_model, registers, error_handling, …) under `custom.rtl_blocker_resolutions`. |
| `new_ip_emit_chain.sh` | After `/to-ssot`, run the proven 4-step emit chain: FL model → equivalence goals → cocotb scoreboard → simulation. |
| `disk_diff.sh` | Hook: inject ground-truth disk diff into agent context after each write/run. |
| `gen_rtl.sh` | Legacy alias for the SSOT→RTL handoff. |

## Method / key rules

- **SSOT-only contract.** Write/validate the YAML; never run rtl-gen/tb-gen/lint/sim or generate downstream artifacts from this workspace.
- **Anti-hallucination.** No "SSOT written" without a real `write_file`; no "validation passed" without a real validator `run_command` whose output contains `PASS`. `todo_write` is plan-mode only.
- **Import-first.** Use `/import` before `/grill-me`/`/to-ssot` when given docs/legacy YAML/RTL; imports are evidence only — SSOT remains authority.
- **Evidence-derived human gates.** Sweep the draft for every TBD/null/placeholder/contradiction; record each human-owned decision with `record_ssot_qa` (deferred) or `ask_user` (immediate blocker). Plain-prose questions are forbidden.
- **Downstream readiness (author once, pass deterministically).** Expression DSL only (`&&→and`, etc., Python-evaluable); every non-reset transaction needs machine-readable `output_rules`/`state_updates`; numeric `state_variables[*].reset`; state-var names must not collide with register names; `cycle_model.cosim: true` for any multi-cycle state; `stimulus_machine_spec` for every scenario; specific transaction preconditions first, catch-all `FM_IDLE` last.
- **Downstream feedback intake.** Patch `[SSOT TBD REPORT]` rows from [[rtl-gen]] and `rtl/rtl_blocked.json` items; preserve approved facts; never answer a TBD with a template default.
- **RTL gate profile.** Smoke/tiny IPs → `quality_gates.rtl_gen.profile: standard`; DMA/CPU/bus/accelerator → `production` (adds locked FL/CL/equivalence/coverage gates in [[rtl-gen]]).

## Inputs → Outputs

- **Inputs:** `<ip>/req/<ip>_requirements.md`, `<ip>/req/import_manifest.json`, `<ip>/req/extracted_decisions.json`, `<ip>/wiki/import-evidence.md`, approved SSOT Q&A; the canonical template `workflow/ssot-gen/rules/ssot-template.yaml`.
- **Outputs:** `<ip>/yaml/<ip>.ssot.yaml` (+ `.provenance.json`), `<ip>/req/ssot_validation.json`, `<ip>/req/ssot_downstream_blockers.json`, and the `[SSOT HANDOFF]` block.

## Structure — SSOT YAML schema

Top-level YAML is one mapping (no `ssot:`/`sections:`/`spec:` wrapper, no legacy aliases like `interface`/`register_map`/`dv_plan`). Canonical section order (36 keys; `engineering` mode requires all except `dft`/`pnr`):

`top_module` · `sub_modules` · `decomposition` · `rtl_contract` · `parameters` · `io_list` · `features` · `dataflow` · `function_model` · `cycle_model` · `clock_reset_domains` · `cdc_requirements` · `rdc_requirements` · `registers` · `memory` · `interrupts` · `fsm` · `timing` · `power` · `security` · `error_handling` · `debug_observability` · `integration` · `dft` · `synthesis` · `pnr` · `coding_rules` · `reuse_modules` · `custom` · `dir_structure` · `filelist` · `test_requirements` · `quality_gates` · `traceability` · `workflow_todos` · `generation_flow`.

Key sections in detail:

- **`top_module`** — `name`, `file` (REQUIRED, must be `rtl/<ip>.sv`), `version`, `type` (dma|cpu|accelerator|bus|peripheral|memory), `description` (Preview anchor), `reference_spec`, `target{technology, clock_freq_mhz, area_um2, power_mw}`.
- **`sub_modules[]`** — each: `name`, `file`, `ownership` (`manifest` = internal block in this leaf YAML; `child_ssot` = independent reusable child IP with its own YAML), `ssot_gen` (downstream hint), and ownership refs (`implements`/`source_sections` plus typed `function_model_refs`/`cycle_model_refs`/`register_refs`/`dataflow_refs`/`fsm_refs`). Wiring-only wrappers set `wiring_only: true`.
- **`function_model`** — the cycle-independent oracle: `state_variables[]` (`name`, `source: registers.<R>.<field>`, numeric `reset`), `transactions[]` (`id`, `name`, `preconditions`, `output_rules[]{name,port,expr,width}`, `state_updates[]{name,expr,width}`, `error_cases`), `invariants`. Expressions are the Python DSL.
- **`cycle_model`** — `clock`, `reset`, `latency`, `handshake_rules[]`, `pipeline[]{stage,cycle,action,output_rules}`, `ordering`, `backpressure`; opt-in flags `cosim: true`, `use_per_cycle_expected: true`, `state_accumulating: true`.
- **`registers`** — `config{register_width,addr_width,...}` + `register_list[]{name,offset,width,access,reset,fields[]{name,bits,access,reset,description}}`, or an explicit no-register policy.
- **`test_requirements`** — `scenarios[]` (each needs `stimulus_machine_spec`: `assign`/`csr_writes`/`timeline`), `scoreboard_checks`, `coverage_goals.function` and `coverage_goals.cycle` (bins traceable to function_model/cycle_model).
- **`quality_gates`** — `rtl_gen.profile` (standard|production), `target_scale` minima, pass/evidence for rtl/coverage/eda.
- **`workflow_todos.<stage>[]`** — the executable handoff ledger; each item carries `content`, `detail`, `command`, `script`, `instructions`, `criteria`, `source_refs` (rtl-gen items also `owner_module`/`owner_file`).

## Related

Upstream: requirements (`req/`). Downstream: [[fl-model-gen]], [[rtl-gen]], [[tb-gen]], [[coverage]], [[syn]], [[sta]], [[pnr]], [[sta-post]]. Back to [[workflow-stages]].
