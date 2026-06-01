# Goal

Objective: expand `mctp_assembler_scratch` verification so single, multi-fragment, interleaved, readback, and drop scenarios are distinguishable in generated goals/scoreboard evidence, and reduce meaningful survived mutants.

Goal tool note: `create_goal` was attempted for this follow-up but failed because this thread still has a completed legacy aggregate goal. This notepad is the binding local goal record for the follow-up.

## Skills

- `omo:ulw-loop`: user explicitly requested `$omo:ulw-loop`; use evidence-bound criteria, RED/GREEN proof, and tmux command artifacts.
- `omo:programming`: Python test/verification files are in scope; read Python rules before edits.
- `omo:review-work`: final verification gate is required because this touches more than three files and changes verification behavior.

## Scope

- Surfaces: generated scenario manifest, SSOT scenario list, cocotb stimulus normalization, scoreboard verdicts, simulation quality gate, mutation candidate selection/reporting.
- Files likely in scope:
  - `mctp_assembler_scratch/tc/mctp_assembler_scratch_scenarios.py`
  - `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml`
  - `mctp_assembler_scratch/tb/cocotb/mctp_contract_stimulus.py`
  - `mctp_assembler_scratch/tb/cocotb/scoreboard.py`
  - `workflow/sim_debug/scripts/check_simulation_quality.py`
  - `workflow/mutation/scripts/mutation_guard.py`
  - `tests/test_*`

## Success Criteria

### C001 Scenario Expansion

Automated test: `tests/test_mctp_scenario_contract.py::test_scenario_contract_distinguishes_single_multi_interleave`.

RED evidence: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-red-C001.txt`.

GREEN evidence: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-green-C001.txt`.

Manual QA channel: tmux.

Manual QA command: create session `ulw-qa-expand-c001` and run `python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py mctp_assembler_scratch --root . && python3 - <<'PY' ... PY` to assert expanded scenario IDs exist in `verify/equivalence_goals.json`.

PASS observable: transcript contains `C001 PASS`.

Artifact: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-C001-tmux.txt`.

### C002 Stronger Scoreboard And Quality Gate

Automated test: `tests/test_mctp_scenario_contract.py::test_scoreboard_rejects_weak_multi_observation` and `tests/test_simulation_quality_gate.py::test_simulation_quality_rejects_multi_assemble_without_distinct_context`.

RED evidence: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-red-C002.txt`.

GREEN evidence: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-green-C002.txt`.

Manual QA channel: tmux.

Manual QA command: create session `ulw-qa-expand-c002` and run `python3 mctp_assembler_scratch/tb/cocotb/test_runner.py && python3 workflow/sim_debug/scripts/check_simulation_quality.py mctp_assembler_scratch --root . --require-class single --require-class multi_assemble --require-class interleave`.

PASS observable: transcript contains `C002 PASS`.

Artifact: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-C002-tmux.txt`.

### C003 Mutation Survivor Reduction

Automated test: `tests/test_mutation_guard.py::test_mutation_guard_skips_noop_unused_evidence_lines`.

RED evidence: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-red-C003.txt`.

GREEN evidence: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-green-C003.txt`.

Manual QA channel: tmux.

Manual QA command: create session `ulw-qa-expand-c003` and run `python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32 && python3 - <<'PY' ... PY` to assert no executed candidate preview contains `unused_` or `evidence` no-op plumbing.

PASS observable: transcript contains `C003 PASS`.

Artifact: `.omo/ulw-loop/019e78f6-947a-7d00-a244-58cefce570bd/evidence/expand-C003-tmux.txt`.

## Findings

- Current scenario rows show `SC_VALID_SINGLE_PACKET`, `SC_MULTI_FRAGMENT_TU64`, and `SC_INTERLEAVE_TWO_KEYS` all pass with nearly identical one-beat observations.
- `test_mctp_assembler_scratch.py` is already 1319 pure LOC and should not be expanded for this follow-up.
- `scoreboard.py` is 219 pure LOC and `mctp_contract_stimulus.py` is 211 pure LOC; keep edits small or split.
- `mutation_guard.py` is already 621 pure LOC; any touch should be minimal and specifically justified as repairing an existing oversized workflow script.
