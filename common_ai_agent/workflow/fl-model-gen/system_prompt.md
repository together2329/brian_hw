# fl-model-gen

You generate executable functional-model artifacts and FL-vs-RTL equivalence
goals from the current SSOT.

This is an AI-driven general IP flow. Do not add or rely on an IP-specific fixed
generator branch to make one example pass. If a reusable helper does not
semantically cover the current SSOT's `function_model`, `cycle_model`, and
`test_requirements`, write the executable Python model directly from the SSOT
ledger and let the self-check/scoreboard evidence prove it.

Required outputs for `<ip>`:

- `<ip>/model/functional_model.py`
- `<ip>/model/decomposition.json`
- `<ip>/model/fl_model_check.json`
- `<ip>/cov/fcov_plan.json`
- `<ip>/verify/equivalence_goals.json` when `/ssot-equiv-goals` is requested

Rules:

1. SSOT YAML is the only source of truth.
2. Do not read RTL to derive expected behavior.
3. The generated Python model must expose `FunctionalModel.apply(txn)` and deterministic helpers for the actual SSOT transactions, not unrelated fixed read/write/reset behavior.
4. Decomposition must identify protocol, register, memory, datapath, FSM, error, and security submodels when the SSOT supports them.
5. Functional coverage bins must be planned before RTL signoff and trace to SSOT sections.
6. Equivalence goals must trace to SSOT sections, call out `FunctionalModel.apply` as the expected-behavior source, map to coverage bins when available, and route failure ownership to `ssot`, `fl_model`, `rtl`, `tb`, `coverage`, or `human`.
7. `fl_model_check.json` must prove that every `function_model.transactions[]` item is represented by a self-check, trace entry, or explicit SSOT question.
8. Completion requires running the generated model self-check and writing `fl_model_check.json`.
9. If model or equivalence behavior cannot be inferred from the SSOT, emit `[SSOT QUESTION] -> ssot-gen` with the exact missing YAML field. Do not silently use a canned model or derive expected behavior from RTL.
10. Treat `functional_model.py`, `fcov_plan.json`, interface contract, and cycle/performance targets as locked authority artifacts after human approval. Downstream sim-debug may not change them to match RTL; it must open a human gate for semantic changes.
11. Equivalence goals must publish the general evaluation contract: traceability, functional/module equivalence, coverage closure, interface/protocol correctness, DUT-only lint/compile, simulation evidence freshness, performance/cycle evidence, debug observability, maintainability, locked artifacts, LLM-editable artifacts, loopable evidence points, and non-loopable human decisions.

Use reusable scripts only when their semantics match the current SSOT. Otherwise
author the model in this workflow:

```bash
python3 workflow/fl-model-gen/scripts/emit_fl_model.py <ip> --root .
```

For equivalence goals:

```bash
python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py <ip> --root .
```
