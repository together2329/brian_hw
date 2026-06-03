---
title: Functional Model Generation
type: reference
tags: [workflow, fl-model-gen, ssot]
status: stable
---

# Functional Model Generation

`fl-model-gen` authors the executable FunctionalModel, decomposition, functional-coverage plan, and FL-vs-RTL equivalence goals directly from the validated SSOT. The FunctionalModel is the behavioral oracle that [[tb-gen]]'s scoreboard compares RTL observations against; equivalence goals define what the LLM repair loop may prove versus what stays human-owned. See [[ssot-gen]] for the contract it consumes and [[workflow-stages]] for the pipeline.

## Purpose

Produce a deterministic Python `FunctionalModel.apply(txn)` (and per-cycle `step()` when `cosim` is set) plus the artifacts that bind expected behavior to coverage bins and ownership routing — so every `function_model.transactions[]` item has a checkable golden result before RTL exists.

## How to run

Run from the project root (or active IP root). The production path authors the model in the worker, then runs the gate; emit scripts are SSOT-driven generators usable when their generic semantics exactly match the SSOT:

```bash
# validation gate (does not generate) — writes model/fl_model_check.json
python3 workflow/fl-model-gen/scripts/check_fl_model_artifacts.py <ip> --root .
# SSOT-driven generators
python3 workflow/fl-model-gen/scripts/emit_fl_model.py          <ip> --root .
python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py <ip> --root .
python3 workflow/fl-model-gen/scripts/emit_cycle_model.py       <ip> --root .
```

The proven 3-command new-IP path is `emit_fl_model.py` → `emit_equivalence_goals.py` → then [[tb-gen]]'s `emit_goal_scoreboard_cocotb.py` (see `doc/wiki/atlas-new-ip-recipe.md`).

## Scripts

| script | does |
| --- | --- |
| `check_fl_model_artifacts.py` | Validate worker-authored FL artifacts without generating them; proves every `function_model.transactions[]` item maps to a self-check/trace entry or explicit SSOT question. |
| `emit_fl_model.py` | Generate executable SSOT functional-model artifacts (`functional_model.py`), SSOT-driven and RTL-independent. |
| `emit_equivalence_goals.py` | Emit generic SSOT-traced FL-vs-RTL equivalence goals; the artifact contract between FL-gen, [[tb-gen]], and [[sim]]. |
| `emit_cycle_model.py` | Generate executable `cycle_model.py` wrapping FunctionalModel with latency/handshake/per-cycle behavior. |
| `emit_decomposition.py` | Emit `model/decomposition.json` (protocol/register/memory/datapath/FSM/error/security submodels). |
| `emit_dual_fcov.py` | Split the functional-coverage plan into FL-only and CL-only plans, then regenerate the union. |
| `emit_model_signature.py` | Emit a deterministic SHA-256 signature of the SSOT-derived golden model for drift detection. |
| `check_signature_drift.py` | Detect drift in `model/model_signature.json` vs the last-known lock (T2 enforcement). |
| `emit_authority_manifest.py` | Emit the per-IP Human-LLM authority manifest (`governance/authority.json`: 6 rules, 9 loops, 9 gates). |
| `emit_loop_map.py` | Render the Human-vs-LLM authority diagram as Mermaid/SVG. |
| `emit_formal_properties.py` | Emit SVA from the SSOT negative spec. |
| `emit_protocol_assertions.py` | Emit SVA from `cycle_model.handshake_rules` + ordering into `verify/protocol_assertions.sva`. |
| `emit_submodule_fl.py` | Emit per-sub_module FL stubs delegating to the top FunctionalModel (enables module-level L2 loop). |
| `emit_module_harness.py` | Emit per-sub_module cocotb harnesses for the L2 module-level loop. |
| `emit_verification_rtl.py` | Emit verification scaffolding: `cocotb_harness.py`, `Makefile.sim`, optional scoreboard bindings. |
| `emit_regression_min.py` | Bisect a failing transaction sequence to a minimal reproducer (L8). |
| `emit_fail_analysis.py` | Synthesize a Markdown root-cause report from a scoreboard diff (L9). |
| `emit_golden_todos.py` | Aggregate per-IP TodoItems (one per equivalence goal + self-check failures). |

## Method / key rules

- **Strict SSOT authority.** SSOT YAML is the only semantic source; do not read RTL, MAS, prior examples, or helper defaults to define expected behavior. Vague/missing `function_model`/`cycle_model`/`coverage_goals`/timing → `[SSOT TBD REPORT] -> ssot-gen` with exact `yaml_path` rows, not a guessed model.
- **Author in the worker.** Don't make `emit_fl_model.py`/`/ssot-fl-model` the default authoring path or add IP-specific generator branches; if a reusable helper doesn't semantically cover the SSOT, write the Python model directly and let the self-check prove it.
- `FunctionalModel.apply(txn)` must be exposed with deterministic helpers for the actual SSOT transactions.
- Equivalence goals must trace to SSOT sections, name `FunctionalModel.apply` as expected-behavior source, map to coverage bins, route failure ownership to `ssot`/`fl_model`/`rtl`/`tb`/`coverage`/`human`, and publish the general evaluation + human-gate contract.
- Completion requires running the model self-check and writing `fl_model_check.json`; DONE states `SSOT TBD REPORT: none`.
- After human approval, `functional_model.py`, `fcov_plan.json`, interface contract, and cycle/performance targets are **locked authority** — [[sim]] sim-debug may not change them to match RTL.

## Inputs → Outputs

- **Inputs:** `<ip>/yaml/<ip>.ssot.yaml`.
- **Outputs:** `<ip>/model/functional_model.py`, `<ip>/model/decomposition.json`, `<ip>/model/fl_model_check.json`, `<ip>/cov/fcov_plan.json`, and `<ip>/verify/equivalence_goals.json` (on `/ssot-equiv-goals`). Production-profile IPs also get `governance/authority.json`, `model/model_signature.json`, and `verify/protocol_assertions.sva`.

## Structure — equivalence-goal contract

Each goal traces to an SSOT ref, names the FunctionalModel as oracle, maps to coverage bins, and carries an ownership router. Goals may be `scope.level=module` (checked at a sub_module boundary first) or top-level. `equivalence_goals.json` drives [[tb-gen]]'s scoreboard: every checked goal becomes one `scoreboard_events.jsonl` row keyed by `goal_id`. Blocked goals stay human-owned until the underlying SSOT/FL question is resolved.

## Related

Upstream: [[ssot-gen]]. Downstream: [[rtl-gen]] (implements the model), [[tb-gen]] (scoreboards against it), [[sim]], [[coverage]]. Back to [[workflow-stages]].
