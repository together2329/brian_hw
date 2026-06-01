# Expand MCTP Verification Cases

## TL;DR
> Summary:      Expand `mctp_assembler_scratch` directed verification so the existing single-packet, multi-fragment, max-TU, interleaved, SRAM-pack, readback, APB, and drop scenarios drive distinct executable behavior instead of shallow one-shot rows. Then use the stronger scenarios, scoreboard checks, and quality/mutation gates to reduce meaningful mutation survivors without chasing instrumentation-only no-ops.
> Deliverables:
> - Executable scenario vector/timeline contract for the existing `mctp_assembler_scratch` scenario catalog.
> - Cocotb integration that drives multi-step MCTP packet, fragment, interleave, readback, APB, and drop cases.
> - Stricter scoreboard and simulation-quality checks that fail hollow scenario coverage.
> - Mutation guard improvements that separate instrumentation-only candidates from meaningful survivors.
> - Fresh simulation, quality, mutation, and evidence artifacts.
> Effort:       Large
> Risk:         High - multi-cycle cocotb behavior, generated artifacts, scoreboard semantics, and mutation triage all interact with a dirty worktree.

## Scope
### Must have
- Preserve unrelated dirty worktree changes. Current exploration found unrelated edits under `mctp_assembler/`, many generated `mctp_assembler_scratch/` artifacts, and untracked sim outputs; downstream executors must stage and commit only the files they intentionally change.
- Make the existing valid scenarios executable and observably distinct: `SC_VALID_SINGLE_PACKET`, `SC_MULTI_FRAGMENT_TU64`, `SC_MAX_TU_4096_129_BEATS`, `SC_INTERLEAVE_TWO_KEYS`, `SC_UNALIGNED_SRAM_PACK_NO_HOLES`, `SC_FIRST_LAST_TLP_HEADERS`, `SC_AXI_READBACK_TRIM`, and `SC_APB_REGS_PER_Q`.
- Keep the existing packet-drop and assembly-drop scenarios in the regression and ensure they still suppress SRAM/context mutation except allowed counters.
- Use TDD: capture a RED or expected-failure transcript before each behavior change, then capture GREEN evidence after the implementation.
- Prefer a focused helper module for scenario vectors/timelines instead of expanding the already-large cocotb harness.
- Strengthen `scoreboard.py` and `check_simulation_quality.py` so scenario rows must prove payload byte counts, sequence/key behavior, SRAM strobes/addresses, readback trimming, APB visibility, and drop suppression.
- Run mutation guard with threshold enforcement and reduce meaningful survivors; explicitly classify instrumentation-only `unused_inputs` reducers as excluded/no-op instead of adding fake tests for them.
- Capture every task's evidence under `evidence/task-<N>-<slug>.<ext>`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not weaken the scoreboard, set `cl_passed` to bypass assertions, or lower mutation thresholds to get green.
- Do not manually edit generated reports such as `mctp_assembler_scratch/sim/scoreboard_events.jsonl`, `mctp_assembler_scratch/sim/simulation_quality.*`, or `mctp_assembler_scratch/mutation/mutation_report.*`; regenerate them with the repo scripts.
- Do not broadly rewrite `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py`; keep integration thin and push new behavior into focused helper/tests.
- Do not count instrumentation-only `unused_inputs` mutation candidates as meaningful verification failures after they are mechanically proven no-op.
- Do not touch the unrelated `mctp_assembler/` IP changes reported by the external research agent unless the user separately asks for that IP.
- Do not add manual/user testing as acceptance. Every check must be agent-executed.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD + `pytest`, cocotb/icarus via `test_runner.py`, scoreboard schema validator, simulation-quality gate, RTL compile/lint/audit when RTL changes, and mutation guard with threshold enforcement.
- QA policy: every task has agent-executed scenarios
- Evidence: `evidence/task-<N>-<slug>.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Add baseline diversity RED/xfail tests and evidence for shallow scenario coverage.
- Task 2: Define scenario vector/timeline contract and unit tests.
- Task 3: Add goal-propagation tests for executable scenario machine specs.
- Task 4: Add simulation-quality scenario-diversity tests.
- Task 5: Exclude instrumentation-only mutation candidates from meaningful survivor accounting.

Wave 2 (after Wave 1):
- Task 6: depends [2, 3] - author executable scenario timelines and preserve them through goal generation.
- Task 7: depends [2, 6] - integrate timeline driving into cocotb with thin harness changes.
- Task 8: depends [1, 2, 7] - enforce scenario-specific scoreboard contracts.
- Task 9: depends [4, 7, 8] - enforce scenario-diversity semantics in simulation quality.
- Task 10: depends [6, 7, 8, 9] - regenerate verification artifacts and close the full sim gate.

Wave 3 (after Wave 2):
- Task 11: depends [10] - target meaningful parser, context, and byte-count mutation survivors.
- Task 12: depends [10] - add adversarial backpressure, readback, and descriptor queue scenarios.
- Task 13: depends [10] - add reset/control/APB state coverage for meaningful reset/control survivors.
- Task 14: depends [5, 11, 12, 13] - enforce mutation threshold and record closure evidence.

Critical path: Task 2 -> Task 6 -> Task 7 -> Task 8 -> Task 10 -> Task 11 -> Task 14

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 8      | 2, 3, 4, 5           |
| 2    | none       | 6, 7, 8 | 1, 3, 4, 5          |
| 3    | none       | 6      | 1, 2, 4, 5           |
| 4    | none       | 9      | 1, 2, 3, 5           |
| 5    | none       | 14     | 1, 2, 3, 4           |
| 6    | 2, 3       | 7, 10  | 8 only after 7       |
| 7    | 2, 6       | 8, 9, 10 | none               |
| 8    | 1, 2, 7    | 9, 10  | none                 |
| 9    | 4, 7, 8    | 10     | none                 |
| 10   | 6, 7, 8, 9 | 11, 12, 13 | none             |
| 11   | 10         | 14     | 12, 13               |
| 12   | 10         | 14     | 11, 13               |
| 13   | 10         | 14     | 11, 12               |
| 14   | 5, 11, 12, 13 | final verification | none      |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Baseline scenario-diversity RED tests

  What to do: Add focused tests that parse current or freshly generated scenario rows and prove the desired diversity contract is not yet met. Use `pytest.mark.xfail(strict=True, reason=...)` for RED expectations so the branch remains runnable until Tasks 6-10 make them green. Include at least these desired assertions: valid scenarios do not all share `(m_axi_awlen=0, m_axi_wlast=1, payload_byte_count=16, sram_write_strb=4095)`, `SC_MULTI_FRAGMENT_TU64` emits multiple fragments/sequences, `SC_MAX_TU_4096_129_BEATS` emits a max-TU signature, and `SC_INTERLEAVE_TWO_KEYS` emits two nonzero/distinct context keys.
  Must NOT do: Do not change cocotb behavior yet. Do not hand-edit `scoreboard_events.jsonl`.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `mctp_assembler_scratch/sim/scoreboard_events.jsonl:11` - current `SC_VALID_SINGLE_PACKET` row is one-shot with `m_axi_awlen=0`, `m_axi_wlast=1`, `payload_byte_count=16`, and `sram_wr_strb=4095`.
  - Pattern:  `mctp_assembler_scratch/sim/scoreboard_events.jsonl:12` - current `SC_MULTI_FRAGMENT_TU64` row has the same one-shot signature as the single-packet row.
  - Pattern:  `mctp_assembler_scratch/sim/scoreboard_events.jsonl:17` - current readback row is separate but not tied to an assembled descriptor sequence.
  - Pattern:  `tests/test_simulation_quality_gate.py:29` - helper pattern for building scoreboard-style rows in unit tests.
  - API/Type: `mctp_assembler_scratch/tc/mctp_assembler_scratch_scenarios.py:131` - valid scenario names begin here.
  - Test:     `tests/test_simulation_quality_gate.py:131` - existing happy-path quality test shape.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_diversity.py -q -rx` reports the new diversity expectations as `XFAIL` and no unexpected pass.
  - [ ] `python3 - <<'PY'\nfrom pathlib import Path\ntext = Path('tests/test_mctp_scenario_diversity.py').read_text()\nfor token in ['SC_VALID_SINGLE_PACKET','SC_MULTI_FRAGMENT_TU64','SC_MAX_TU_4096_129_BEATS','SC_INTERLEAVE_TWO_KEYS']:\n    assert token in text\nassert 'xfail' in text\nPY` succeeds.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: RED diversity expectations are recorded
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-1-red "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_diversity.py -q -rx; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-1-red -S - > evidence/task-1-baseline-red.txt && tmux kill-session -t task-1-red
    Expected: evidence/task-1-baseline-red.txt contains `XFAIL` for the scenario-diversity expectations and contains no `XPASS`.
    Evidence: evidence/task-1-baseline-red.txt

  Scenario: Missing scoreboard artifact fails clearly
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-1-missing "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && SCOREBOARD_EVENTS=/tmp/missing-scoreboard-events.jsonl PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_diversity.py -q -rx; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-1-missing -S - > evidence/task-1-baseline-missing.txt && tmux kill-session -t task-1-missing
    Expected: evidence/task-1-baseline-missing.txt contains a clear missing-file failure or skip reason naming `/tmp/missing-scoreboard-events.jsonl`, not a traceback from unrelated code.
    Evidence: evidence/task-1-baseline-missing.txt
  ```

  Commit: YES | Message: `test(mctp): characterize shallow scenario coverage` | Files: [`tests/test_mctp_scenario_diversity.py`]

- [ ] 2. Scenario vector and timeline contract

  What to do: Create a focused scenario-vector contract module and tests. The contract must describe the concrete sequence for every valid scenario and representative PD/AD cases: fields per step, expected fragments/beats, SOM/EOM/packet sequence, source/destination EID, tag owner, message tag, payload byte count, WSTRB, SRAM write expectations, readback expectations, APB expectations, and expected debug/context keys. Prefer a new `mctp_assembler_scratch/tb/cocotb/mctp_scenario_vectors.py` with pure functions that can be unit-tested without a simulator.
  Must NOT do: Do not duplicate large chunks of the cocotb harness. Do not invent scenario names outside the existing catalog unless the SSOT is updated consistently.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [6, 7, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `mctp_assembler_scratch/tc/mctp_assembler_scratch_scenarios.py:32` - `DirectedScenario` fields and manifest shape.
  - Pattern:  `mctp_assembler_scratch/tc/mctp_assembler_scratch_scenarios.py:73` - required scenario fields currently emitted into goals.
  - Pattern:  `mctp_assembler_scratch/tc/mctp_assembler_scratch_scenarios.py:93` - current machine spec is only a shallow `assign`, not a timeline.
  - API/Type: `mctp_assembler_scratch/tb/cocotb/mctp_contract_stimulus.py:188` - `_encode_mctp_word()` encodes source EID, destination EID, tag owner, message tag, packet sequence, SOM/EOM, message type, payload, and byte strobe.
  - API/Type: `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:1245` - `_apply_machine_spec()` already supports `timeline[]`, `assign`, `csr_write`, `wait_cycles`, and `wait_until`.
  - External: `https://www.dmtf.org/dsp/DSP0236` - MCTP base specification landing page for packet sequencing and SOM/EOM semantics.
  - External: `https://www.dmtf.org/dsp/DSP0238` - MCTP PCIe VDM binding landing page for PCIe VDM transport context.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_vectors.py -q` passes.
  - [ ] `python3 - <<'PY'\nfrom mctp_assembler_scratch.tb.cocotb.mctp_scenario_vectors import scenario_vector\ncases = ['SC_VALID_SINGLE_PACKET','SC_MULTI_FRAGMENT_TU64','SC_MAX_TU_4096_129_BEATS','SC_INTERLEAVE_TWO_KEYS','SC_UNALIGNED_SRAM_PACK_NO_HOLES','SC_FIRST_LAST_TLP_HEADERS','SC_AXI_READBACK_TRIM','SC_APB_REGS_PER_Q']\nfor case in cases:\n    vector = scenario_vector(case)\n    assert vector.steps, case\n    assert vector.expected, case\nassert len({tuple(step.get('context_key', 0) for step in scenario_vector('SC_INTERLEAVE_TWO_KEYS').steps)}) >= 2\nassert len(scenario_vector('SC_MULTI_FRAGMENT_TU64').steps) >= 2\nPY` succeeds.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Vector contract covers every valid scenario
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-2-vectors "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_vectors.py -q; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-2-vectors -S - > evidence/task-2-vector-contract.txt && tmux kill-session -t task-2-vectors
    Expected: evidence/task-2-vector-contract.txt contains `passed` and no failures.
    Evidence: evidence/task-2-vector-contract.txt

  Scenario: Unknown scenario is rejected
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-2-unknown "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 - <<'PY'\nfrom mctp_assembler_scratch.tb.cocotb.mctp_scenario_vectors import scenario_vector\ntry:\n    scenario_vector('SC_DOES_NOT_EXIST')\nexcept KeyError as exc:\n    print(str(exc))\nelse:\n    raise SystemExit('missing KeyError')\nPY\nprintf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-2-unknown -S - > evidence/task-2-vector-unknown.txt && tmux kill-session -t task-2-unknown
    Expected: evidence/task-2-vector-unknown.txt contains `SC_DOES_NOT_EXIST` and `exit=0`.
    Evidence: evidence/task-2-vector-unknown.txt
  ```

  Commit: YES | Message: `test(mctp): define directed scenario vector contracts` | Files: [`mctp_assembler_scratch/tb/cocotb/mctp_scenario_vectors.py`, `tests/test_mctp_scenario_vectors.py`]

- [ ] 3. Executable machine-spec propagation tests

  What to do: Add tests that assert executable scenario timelines survive from scenario/SSOT authoring into `verify/equivalence_goals.json`. Start with expected failures if current generator drops timeline fields, then make Task 6 responsible for turning them green.
  Must NOT do: Do not patch generated JSON by hand. Do not create a second source of truth for scenario definitions.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [6] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `workflow/fl-model-gen/scripts/emit_equivalence_goals.py:504` - `_scenario_goals()` is where SSOT scenarios become equivalence goals.
  - Pattern:  `workflow/fl-model-gen/scripts/emit_equivalence_goals.py:525` - current generated required fields are assembled here.
  - Pattern:  `workflow/fl-model-gen/scripts/emit_equivalence_goals.py:537` - pass criteria generation for scenarios.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:1377` - main cocotb loop applies `machine_spec` only if present on the goal.
  - Test:     `tests/test_fl_rtl_equivalence_loop.py` - existing test file for FL/RTL goal-generation and loop expectations.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_goal_machine_spec.py -q -rx` reports expected failures before Task 6 or passes after Task 6.
  - [ ] `python3 - <<'PY'\nfrom pathlib import Path\ntext = Path('tests/test_mctp_goal_machine_spec.py').read_text()\nassert 'EQ_SCENARIO_SC_MULTI_FRAGMENT_TU64' in text\nassert 'machine_spec' in text\nassert 'timeline' in text\nPY` succeeds.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Goal machine-spec propagation expectation is executable
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-3-prop "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_goal_machine_spec.py -q -rx; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-3-prop -S - > evidence/task-3-machine-spec-propagation.txt && tmux kill-session -t task-3-prop
    Expected: evidence/task-3-machine-spec-propagation.txt contains either `XFAIL` for the known missing propagation or `passed` after Task 6; it must not contain import errors.
    Evidence: evidence/task-3-machine-spec-propagation.txt

  Scenario: Generated-goal fixture without timeline fails the targeted assertion
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-3-negative "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_goal_machine_spec.py -q -k missing_timeline_fixture -rx; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-3-negative -S - > evidence/task-3-machine-spec-negative.txt && tmux kill-session -t task-3-negative
    Expected: evidence/task-3-machine-spec-negative.txt names `machine_spec.timeline` as the missing field.
    Evidence: evidence/task-3-machine-spec-negative.txt
  ```

  Commit: YES | Message: `test(mctp): require executable scenario machine specs` | Files: [`tests/test_mctp_goal_machine_spec.py`]

- [ ] 4. Simulation-quality scenario-diversity tests

  What to do: Extend unit tests for `workflow/sim_debug/scripts/check_simulation_quality.py` so the quality gate can reject hollow scenario rows even when all rows pass. Test for duplicate valid scenario signatures, missing multi-fragment sequence evidence, missing interleave context-key evidence, missing max-TU byte-count evidence, missing final WSTRB/trim evidence, and drop rows that mutate SRAM/context.
  Must NOT do: Do not make the quality gate depend on current generated reports only; use small synthetic fixtures in tests.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `workflow/sim_debug/scripts/check_simulation_quality.py:16` - class token mapping used by the gate.
  - API/Type: `workflow/sim_debug/scripts/check_simulation_quality.py:144` - semantic issue checks begin here.
  - API/Type: `workflow/sim_debug/scripts/check_simulation_quality.py:172` - current interleave check only requires a context key or message tag.
  - Test:     `tests/test_simulation_quality_gate.py:61` - drop suppression test pattern.
  - Test:     `tests/test_simulation_quality_gate.py:131` - synthetic happy-path report test.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_simulation_quality_gate.py -q` passes.
  - [ ] `python3 - <<'PY'\nfrom pathlib import Path\ntext = Path('workflow/sim_debug/scripts/check_simulation_quality.py').read_text()\nfor token in ['SC_MULTI_FRAGMENT_TU64','SC_MAX_TU_4096_129_BEATS','SC_INTERLEAVE_TWO_KEYS','scenario_diversity']:\n    assert token in text\nPY` succeeds.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Synthetic hollow rows fail quality
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-4-hollow "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_simulation_quality_gate.py -q -k scenario_diversity; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-4-hollow -S - > evidence/task-4-sim-quality-diversity.txt && tmux kill-session -t task-4-hollow
    Expected: evidence/task-4-sim-quality-diversity.txt contains `passed` and proves hollow synthetic rows are rejected by assertion.
    Evidence: evidence/task-4-sim-quality-diversity.txt

  Scenario: Synthetic rich rows pass quality
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-4-rich "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_simulation_quality_gate.py -q -k rich_scenario_diversity; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-4-rich -S - > evidence/task-4-sim-quality-rich.txt && tmux kill-session -t task-4-rich
    Expected: evidence/task-4-sim-quality-rich.txt contains `passed` and no failure.
    Evidence: evidence/task-4-sim-quality-rich.txt
  ```

  Commit: YES | Message: `test(sim-quality): require scenario diversity observables` | Files: [`workflow/sim_debug/scripts/check_simulation_quality.py`, `tests/test_simulation_quality_gate.py`]

- [ ] 5. Instrumentation-only mutation candidate exclusion

  What to do: Teach mutation guard to identify mechanically no-op instrumentation reducers such as `assign unused_inputs = ^...;` and exclude them from meaningful survivor accounting while reporting them separately. Add unit tests proving these candidates are excluded and that functional operator/comparator/handshake/state candidates are still counted.
  Must NOT do: Do not skip meaningful candidates such as `context_accept`, `context_assembly`, `next_seq`, byte-count updates, SRAM handshakes, descriptor queue handshakes, or readback descriptor state.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [14] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `workflow/mutation/scripts/mutation_guard.py:54` - supported mutation categories and priorities.
  - Pattern:  `workflow/mutation/scripts/mutation_guard.py:403` - current structural mutation skip logic.
  - Pattern:  `workflow/mutation/scripts/mutation_guard.py:463` - category summary accounting.
  - Pattern:  `mctp_assembler_scratch/mutation/mutation_report.json:15` - example survived `unused_inputs` preview.
  - Pattern:  `mctp_assembler_scratch/mutation/mutation_report.json:268` - example `unused_inputs` preview containing real signals but still only a reduction sink.
  - Test:     `tests/test_mutation_guard.py:232` - category kill-rate test pattern.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mutation_guard.py -q` passes.
  - [ ] `python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --list-only --max-mutants 32 > evidence/task-5-mutation-list.txt` writes a list that reports instrumentation/no-op exclusions separately from meaningful candidates.
  - [ ] `python3 - <<'PY'\nfrom pathlib import Path\ntext = Path('workflow/mutation/scripts/mutation_guard.py').read_text()\nassert 'unused_inputs' in text\nassert 'instrumentation' in text or 'noop' in text\nPY` succeeds.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Mutation guard unit tests cover no-op exclusion
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-5-tests "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mutation_guard.py -q; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-5-tests -S - > evidence/task-5-mutation-noop-tests.txt && tmux kill-session -t task-5-tests
    Expected: evidence/task-5-mutation-noop-tests.txt contains `passed` and no failure.
    Evidence: evidence/task-5-mutation-noop-tests.txt

  Scenario: Functional candidate remains meaningful
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-5-list "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --list-only --max-mutants 32; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-5-list -S - > evidence/task-5-mutation-list.txt && tmux kill-session -t task-5-list
    Expected: evidence/task-5-mutation-list.txt includes meaningful candidates from `context_assembly`, `context_accept`, or handshake/state updates and marks `unused_inputs` candidates as excluded/no-op.
    Evidence: evidence/task-5-mutation-list.txt
  ```

  Commit: YES | Message: `fix(mutation): exclude instrumentation-only mutants` | Files: [`workflow/mutation/scripts/mutation_guard.py`, `tests/test_mutation_guard.py`]

- [ ] 6. Author executable scenario timelines and preserve them through goal generation

  What to do: Replace shallow scenario machine specs with executable timelines for the valid and representative drop scenarios, then update generator plumbing so those timelines appear in `verify/equivalence_goals.json`. Keep `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml`, `mctp_assembler_scratch/tc/mctp_assembler_scratch_scenarios.py`, scenario manifest output, and generated equivalence goals consistent. Resolve the current ambiguity where `SC_MULTI_FRAGMENT_TU64` is described as SOM/middle/EOM in SSOT but has a different packet-count hint in the Python catalog by making the executable contract explicit in both places.
  Must NOT do: Do not hand-edit generated equivalence goals without updating the source generator/input. Do not silently drop fields not understood by the harness.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [7, 10] | Blocked by: [2, 3]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml:1060` - dataflow requirements for AXI W concatenation, drop suppression, SOM allocation, middle/EOM sequence order, SRAM packing, descriptor readback, and final trim.
  - Pattern:  `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml:2979` - valid scenario definitions begin here.
  - Pattern:  `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml:3045` - packet-drop and assembly-drop scenario definitions continue here.
  - Pattern:  `mctp_assembler_scratch/tc/mctp_assembler_scratch_scenarios.py:129` - valid scenario definitions in Python catalog.
  - Pattern:  `workflow/fl-model-gen/scripts/emit_equivalence_goals.py:504` - scenario goal generation.
  - Test:     `tests/test_mctp_goal_machine_spec.py` - Task 3 propagation tests.
  - Test:     `tests/test_mctp_scenario_vectors.py` - Task 2 vector contract tests.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_vectors.py tests/test_mctp_goal_machine_spec.py -q` passes with no `XFAIL` for machine-spec propagation.
  - [ ] `python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py mctp_assembler_scratch --root .` regenerates goals successfully, or the repo-equivalent documented generation command succeeds if this script has a different CLI.
  - [ ] `python3 - <<'PY'\nimport json\nfrom pathlib import Path\ngoals = json.loads(Path('mctp_assembler_scratch/verify/equivalence_goals.json').read_text())\nby_id = {g['goal_id']: g for g in goals}\nfor goal_id in ['EQ_SCENARIO_SC_MULTI_FRAGMENT_TU64','EQ_SCENARIO_SC_MAX_TU_4096_129_BEATS','EQ_SCENARIO_SC_INTERLEAVE_TWO_KEYS']:\n    timeline = by_id[goal_id].get('machine_spec', {}).get('timeline')\n    assert timeline and len(timeline) >= 2, goal_id\nPY` succeeds.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Executable timelines are present in generated goals
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-6-goals "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_goal_machine_spec.py -q && python3 - <<'PY'\nimport json\nfrom pathlib import Path\ngoals = json.loads(Path('mctp_assembler_scratch/verify/equivalence_goals.json').read_text())\nfor g in goals:\n    if g['goal_id'] in {'EQ_SCENARIO_SC_MULTI_FRAGMENT_TU64','EQ_SCENARIO_SC_MAX_TU_4096_129_BEATS','EQ_SCENARIO_SC_INTERLEAVE_TWO_KEYS'}:\n        print(g['goal_id'], len(g.get('machine_spec', {}).get('timeline', [])))\nPY\nprintf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-6-goals -S - > evidence/task-6-machine-spec-goals.txt && tmux kill-session -t task-6-goals
    Expected: evidence/task-6-machine-spec-goals.txt shows nonzero timeline lengths for the multi-fragment, max-TU, and interleave goals and exits 0.
    Evidence: evidence/task-6-machine-spec-goals.txt

  Scenario: Drop scenario timeline still suppresses writes
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-6-drop "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 - <<'PY'\nfrom mctp_assembler_scratch.tb.cocotb.mctp_scenario_vectors import scenario_vector\nfor case in ['PD_MALFORMED_TLP','AD_SEQUENCE_MISMATCH']:\n    vector = scenario_vector(case)\n    assert vector.expected.get('sram_writes', 0) == 0, case\n    print(case, vector.expected)\nPY\nprintf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-6-drop -S - > evidence/task-6-drop-suppression-contract.txt && tmux kill-session -t task-6-drop
    Expected: evidence/task-6-drop-suppression-contract.txt prints both drop cases with zero expected SRAM writes and exits 0.
    Evidence: evidence/task-6-drop-suppression-contract.txt
  ```

  Commit: YES | Message: `feat(mctp): preserve executable scenario machine specs` | Files: [`mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml`, `mctp_assembler_scratch/tc/mctp_assembler_scratch_scenarios.py`, `mctp_assembler_scratch/tc/scenario_manifest.json`, `workflow/fl-model-gen/scripts/emit_equivalence_goals.py`, `mctp_assembler_scratch/verify/equivalence_goals.json`, `tests/test_mctp_goal_machine_spec.py`]

- [ ] 7. Cocotb timeline-driver integration

  What to do: Integrate the scenario-vector/timeline contract into cocotb execution with minimal changes to the main harness. The driver must apply each timeline step, wait according to the step contract, collect per-step and aggregate observations, and pass enough evidence into `scoreboard.check_goal()` for scenario-specific checks. Preserve existing one-shot generic goal behavior.
  Must NOT do: Do not reset between fragments of the same scenario. Do not expand `test_mctp_assembler_scratch.py` with large duplicated case logic.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [8, 9, 10] | Blocked by: [2, 6]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:747` - `_stimulus_for_goal()` currently creates one stimulus dict per goal.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:837` - wait-cycle heuristic for MCTP-like goals.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:1160` - `_merge_observation_window()` aggregates pulse and data observations.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:1245` - `_apply_machine_spec()` can already execute timeline entries.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:1457` - `scoreboard.check_goal()` call site.
  - API/Type: `mctp_assembler_scratch/tb/cocotb/mctp_contract_stimulus.py:140` - write defaults currently clamp payload length and default to one beat.
  - External: `https://docs.cocotb.org/en/stable/writing_testbenches.html` - cocotb testbench structure and coroutine guidance.
  - External: `https://docs.cocotb.org/en/stable/triggers.html` - cocotb trigger/wait primitives.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_vectors.py -q` passes.
  - [ ] `python3 workflow/tb-gen/runtime/equivalence_scoreboard.py mctp_assembler_scratch --root . --self-check` passes.
  - [ ] `python3 mctp_assembler_scratch/tb/cocotb/test_runner.py` completes with simulator return code 0 before Task 8 strict scoreboard changes are enabled, or produces only the known Task 8 scenario-contract RED mismatches captured as evidence.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Cocotb runner accepts timeline-driven scenarios
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-7-runner "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 mctp_assembler_scratch/tb/cocotb/test_runner.py; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 5 && tmux capture-pane -pt task-7-runner -S - > evidence/task-7-cocotb-timeline-runner.txt && tmux kill-session -t task-7-runner
    Expected: evidence/task-7-cocotb-timeline-runner.txt contains the test-runner summary and either `exit=0` or targeted scenario-contract mismatches that Task 8 will close; no Python import errors.
    Evidence: evidence/task-7-cocotb-timeline-runner.txt

  Scenario: One-shot non-scenario goal still runs
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-7-selfcheck "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 workflow/tb-gen/runtime/equivalence_scoreboard.py mctp_assembler_scratch --root . --self-check; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-7-selfcheck -S - > evidence/task-7-scoreboard-selfcheck.txt && tmux kill-session -t task-7-selfcheck
    Expected: evidence/task-7-scoreboard-selfcheck.txt contains `exit=0`.
    Evidence: evidence/task-7-scoreboard-selfcheck.txt
  ```

  Commit: YES | Message: `feat(mctp): drive directed scenario timelines` | Files: [`mctp_assembler_scratch/tb/cocotb/mctp_scenario_vectors.py`, `mctp_assembler_scratch/tb/cocotb/mctp_contract_stimulus.py`, `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py`, `tests/test_mctp_scenario_vectors.py`]

- [ ] 8. Scenario-specific scoreboard contracts

  What to do: Strengthen `GoalScoreboard` verdicts so each valid scenario must match its expected semantic signature. Check at minimum: single-packet descriptor and payload count; multi-fragment ordered sequence and total payload count; max-TU multi-beat/4096-byte behavior; interleave with two distinct context keys/FSMs; unaligned SRAM packing with non-default final strobe and no holes; first/last header retention; readback trim with descriptor-backed final `readback_last`; APB per-Q visibility. Convert Task 1 xfails into passing tests.
  Must NOT do: Do not make the scoreboard accept generic `debug_vdm_valid` as enough proof for all valid scenarios.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [9, 10] | Blocked by: [1, 2, 7]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/scoreboard.py:79` - `_mctp_contract_verdict()` dispatches MCTP contract checks.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/scoreboard.py:108` - current valid scenario logic groups many scenarios behind a shallow check.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/scoreboard.py:127` - current readback check.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/scoreboard.py:158` - current SRAM pack check.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/scoreboard.py:212` - `GoalScoreboard.check_goal()` entry point.
  - Test:     `tests/test_mctp_scenario_diversity.py` - Task 1 xfail tests to convert to green.
  - Test:     `tests/test_mctp_scenario_vectors.py` - expected signature source.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_diversity.py tests/test_mctp_scoreboard_contracts.py -q` passes with zero `XFAIL` and zero `XPASS`.
  - [ ] `python3 - <<'PY'\nfrom pathlib import Path\ntext = Path('mctp_assembler_scratch/tb/cocotb/scoreboard.py').read_text()\nfor token in ['SC_MULTI_FRAGMENT_TU64','SC_MAX_TU_4096_129_BEATS','SC_INTERLEAVE_TWO_KEYS','SC_UNALIGNED_SRAM_PACK_NO_HOLES','SC_AXI_READBACK_TRIM']:\n    assert token in text\nPY` succeeds.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Scoreboard rejects hollow valid scenario rows
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-8-hollow "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scoreboard_contracts.py -q -k hollow; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-8-hollow -S - > evidence/task-8-scoreboard-hollow.txt && tmux kill-session -t task-8-hollow
    Expected: evidence/task-8-scoreboard-hollow.txt contains `passed`; the tests assert hollow rows are rejected by mismatch messages naming the missing scenario proof.
    Evidence: evidence/task-8-scoreboard-hollow.txt

  Scenario: Scoreboard accepts rich scenario rows
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-8-rich "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scoreboard_contracts.py -q -k rich; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-8-rich -S - > evidence/task-8-scoreboard-rich.txt && tmux kill-session -t task-8-rich
    Expected: evidence/task-8-scoreboard-rich.txt contains `passed` and no failures.
    Evidence: evidence/task-8-scoreboard-rich.txt
  ```

  Commit: YES | Message: `test(mctp): enforce scenario-specific scoreboard contracts` | Files: [`mctp_assembler_scratch/tb/cocotb/scoreboard.py`, `tests/test_mctp_scoreboard_contracts.py`, `tests/test_mctp_scenario_diversity.py`]

- [ ] 9. Simulation-quality diversity gate implementation

  What to do: Implement the scenario-diversity semantic checks introduced in Task 4 against real scoreboard rows. The gate must fail if all valid scenarios collapse to the same signature, if multi-fragment/interleave/max-TU/readback/APB scenarios lack their required observations, or if drop scenarios mutate SRAM/context. It must write actionable issue messages into `simulation_quality.json` and `.md`.
  Must NOT do: Do not encode brittle exact cycle numbers. Use scenario IDs, observed fields, and expected semantic signatures.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [10] | Blocked by: [4, 7, 8]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `workflow/sim_debug/scripts/check_simulation_quality.py:119` - required observable loading from `ip_contract.json`.
  - Pattern:  `workflow/sim_debug/scripts/check_simulation_quality.py:144` - semantic issues are collected here.
  - Pattern:  `workflow/sim_debug/scripts/check_simulation_quality.py:205` - report writing.
  - API/Type: `mctp_assembler_scratch/verify/ip_contract.json` - required observable list consumed by the quality gate.
  - Test:     `tests/test_simulation_quality_gate.py` - Task 4 tests.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_simulation_quality_gate.py -q` passes.
  - [ ] `python3 workflow/sim_debug/scripts/check_simulation_quality.py mctp_assembler_scratch --root . --require-class write --require-class memory_pack --require-class interleave --require-class readback --require-class register --require-class drop --require-class boundary --require-class protocol --require-class fsm` exits 0 after Task 10 regenerated rows exist.
  - [ ] `python3 - <<'PY'\nimport json\nfrom pathlib import Path\nreport = json.loads(Path('mctp_assembler_scratch/sim/simulation_quality.json').read_text())\nassert report['status'] == 'pass'\nassert not report.get('issues')\nassert report.get('scenario_diversity', {}).get('status') == 'pass'\nPY` succeeds after Task 10.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Quality gate reports scenario-diversity pass on current generated rows
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-9-quality "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 workflow/sim_debug/scripts/check_simulation_quality.py mctp_assembler_scratch --root . --require-class write --require-class memory_pack --require-class interleave --require-class readback --require-class register --require-class drop --require-class boundary --require-class protocol --require-class fsm; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-9-quality -S - > evidence/task-9-simulation-quality.txt && tmux kill-session -t task-9-quality
    Expected: evidence/task-9-simulation-quality.txt contains `exit=0`; `mctp_assembler_scratch/sim/simulation_quality.json` has `scenario_diversity.status == "pass"`.
    Evidence: evidence/task-9-simulation-quality.txt

  Scenario: Quality gate rejects a duplicate-signature fixture
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-9-duplicate "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_simulation_quality_gate.py -q -k duplicate_signature; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-9-duplicate -S - > evidence/task-9-quality-duplicate.txt && tmux kill-session -t task-9-duplicate
    Expected: evidence/task-9-quality-duplicate.txt contains `passed` and no failure.
    Evidence: evidence/task-9-quality-duplicate.txt
  ```

  Commit: YES | Message: `fix(sim-quality): reject hollow mctp scenario coverage` | Files: [`workflow/sim_debug/scripts/check_simulation_quality.py`, `tests/test_simulation_quality_gate.py`, `mctp_assembler_scratch/sim/simulation_quality.json`, `mctp_assembler_scratch/sim/simulation_quality.md`]

- [ ] 10. Regenerate artifacts and close full simulation gate

  What to do: Run the canonical scoreboard, cocotb, scoreboard schema, and simulation-quality commands to refresh generated artifacts. Inspect scenario signatures with a deterministic script and fix any mismatch in scenario vectors, timeline driving, or scoreboard semantics before committing.
  Must NOT do: Do not commit stale reports from before Tasks 6-9. Do not ignore simulator failures.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [11, 12, 13] | Blocked by: [6, 7, 8, 9]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `workflow/STAGE_MANIFEST.json:108` - canonical sim stage command is `python3 <ip-parent>/<ip>/tb/cocotb/test_runner.py`.
  - Pattern:  `workflow/STAGE_MANIFEST.json:111` - sim outputs include `results.xml`, `sim_report.txt`, and `scoreboard_events.jsonl`.
  - Pattern:  `workflow/STAGE_MANIFEST.json:118` - scoreboard schema command.
  - Pattern:  `workflow/wiki/ip_knowledge/tb-gen.md:20` - TB-gen run instructions.
  - Pattern:  `workflow/wiki/ip_knowledge/tb-gen.md:52` - scoreboard row schema.
  - API/Type: `mctp_assembler_scratch/tb/cocotb/test_runner.py:107` - runner main entry point.
  - API/Type: `mctp_assembler_scratch/tb/cocotb/test_runner.py:165` - run report and artifact copy behavior.

  Acceptance criteria (agent-executable only):
  - [ ] `python3 workflow/tb-gen/runtime/equivalence_scoreboard.py mctp_assembler_scratch --root . --self-check` exits 0.
  - [ ] `python3 mctp_assembler_scratch/tb/cocotb/test_runner.py` exits 0.
  - [ ] `python3 workflow/tb-gen/scripts/check_scoreboard_events.py mctp_assembler_scratch --root . --source-check --require-events` exits 0.
  - [ ] `python3 workflow/sim_debug/scripts/check_simulation_quality.py mctp_assembler_scratch --root . --require-class write --require-class memory_pack --require-class interleave --require-class readback --require-class register --require-class drop --require-class boundary --require-class protocol --require-class fsm` exits 0.
  - [ ] `python3 - <<'PY'\nimport json\nfrom pathlib import Path\nrows = [json.loads(line) for line in Path('mctp_assembler_scratch/sim/scoreboard_events.jsonl').read_text().splitlines() if line.strip()]\nwanted = {r['goal_id']: r for r in rows if r['goal_id'].startswith('EQ_SCENARIO_SC_')}\nassert wanted['EQ_SCENARIO_SC_VALID_SINGLE_PACKET']['rtl_observed']['payload_byte_count'] != wanted['EQ_SCENARIO_SC_MULTI_FRAGMENT_TU64']['rtl_observed']['payload_byte_count']\nassert wanted['EQ_SCENARIO_SC_MAX_TU_4096_129_BEATS']['rtl_observed']['payload_byte_count'] >= 4096\nassert wanted['EQ_SCENARIO_SC_INTERLEAVE_TWO_KEYS']['rtl_observed'].get('debug_context_key') not in (None, 0)\nassert wanted['EQ_SCENARIO_SC_AXI_READBACK_TRIM']['rtl_observed']['readback_last'] == 1\nPY` succeeds.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Full cocotb and quality gate pass
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-10-full "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 workflow/tb-gen/runtime/equivalence_scoreboard.py mctp_assembler_scratch --root . --self-check && python3 mctp_assembler_scratch/tb/cocotb/test_runner.py && python3 workflow/tb-gen/scripts/check_scoreboard_events.py mctp_assembler_scratch --root . --source-check --require-events && python3 workflow/sim_debug/scripts/check_simulation_quality.py mctp_assembler_scratch --root . --require-class write --require-class memory_pack --require-class interleave --require-class readback --require-class register --require-class drop --require-class boundary --require-class protocol --require-class fsm; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 10 && tmux capture-pane -pt task-10-full -S - > evidence/task-10-full-sim-quality.txt && tmux kill-session -t task-10-full
    Expected: evidence/task-10-full-sim-quality.txt contains `exit=0`; generated `sim_report.txt`, `scoreboard_events.jsonl`, and `simulation_quality.json` are fresh.
    Evidence: evidence/task-10-full-sim-quality.txt

  Scenario: Scenario signatures are distinct
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-10-signatures "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 - <<'PY'\nimport json\nfrom pathlib import Path\nrows = [json.loads(line) for line in Path('mctp_assembler_scratch/sim/scoreboard_events.jsonl').read_text().splitlines() if line.strip()]\nfor row in rows:\n    if row['goal_id'].startswith('EQ_SCENARIO_SC_'):\n        obs = row['rtl_observed']\n        print(row['goal_id'], obs.get('payload_byte_count'), obs.get('descriptor_count'), obs.get('sram_write_strb'), obs.get('debug_context_key'), obs.get('readback_last'))\nPY\nprintf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-10-signatures -S - > evidence/task-10-scenario-signatures.txt && tmux kill-session -t task-10-signatures
    Expected: evidence/task-10-scenario-signatures.txt shows different signatures for single, multi-fragment, max-TU, interleave, SRAM-pack, readback, and APB rows.
    Evidence: evidence/task-10-scenario-signatures.txt
  ```

  Commit: YES | Message: `test(mctp): close scenario simulation quality` | Files: [`mctp_assembler_scratch/verify/equivalence_goals.json`, `mctp_assembler_scratch/sim/results.xml`, `mctp_assembler_scratch/sim/sim_report.txt`, `mctp_assembler_scratch/sim/scoreboard_events.jsonl`, `mctp_assembler_scratch/sim/simulation_quality.json`, `mctp_assembler_scratch/sim/simulation_quality.md`, `mctp_assembler_scratch/cov/coverage*.json`, `mctp_assembler_scratch/sim/coverage_report.md`]

- [ ] 11. Target parser, context, and byte-count meaningful mutation survivors

  What to do: Run mutation guard after Task 10, identify remaining meaningful survivors in parser/context/byte-count behavior, and close them with either stronger scenario observations or minimal RTL fixes when the RTL is wrong. Known current survivor examples include `context_accept`, `context_assembly`, `next_seq`, `byte_count_q`, and context-table state updates. Use TDD: capture the survivor, add/fix scenario or RTL, rerun the targeted mutation.
  Must NOT do: Do not chase `unused_inputs` reducers here. Do not make scoreboard expectations match incorrect RTL if the SSOT/vector contract says otherwise.

  Parallelization: Can parallel: YES | Wave 3 | Blocks: [14] | Blocked by: [10]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `mctp_assembler_scratch/mutation/mutation_report.json:200` - current `context_assembly` comparator survivor example.
  - Pattern:  `mctp_assembler_scratch/mutation/mutation_report.json:711` - current `MUT_0056` survivor location in generated report.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_axi_write_ingress.sv:56` - `context_assembly` assignment.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_axi_write_ingress.sv:104` - byte-count update target.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:30` - `context_accept` survivor target.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:34` - `next_seq` survivor target.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_context_table.sv` - context state survivor targets around IDLE/ERROR updates.
  - Test:     `tests/test_mutation_guard.py:43` - contract obligation test pattern.

  Acceptance criteria (agent-executable only):
  - [ ] `python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32 --timeout-sec 60 --threshold 0.70 --enforce-threshold` exits 0 or records only non-meaningful excluded/no-op survivors after Task 14.
  - [ ] If RTL files change, `python3 workflow/rtl-gen/scripts/rtl_compile_report.py mctp_assembler_scratch --project-root .`, `python3 workflow/lint/scripts/dut_lint_report.py mctp_assembler_scratch`, and `python3 workflow/rtl-gen/scripts/derive_rtl_todos.py mctp_assembler_scratch --root . --audit-rtl` all exit 0.
  - [ ] `python3 - <<'PY'\nimport json\nfrom pathlib import Path\nreport = json.loads(Path('mctp_assembler_scratch/mutation/mutation_report.json').read_text())\nremaining = [r for r in report.get('results', []) if r.get('status') == 'survived' and not r.get('excluded')]\nfor row in remaining:\n    assert 'unused_inputs' in row.get('preview', '') or row.get('classification') in {'instrumentation_noop','unsupported'}, row\nPY` succeeds after Task 14.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Meaningful parser/context/byte-count mutants are killed
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-11-mutation "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32 --timeout-sec 60 --threshold 0.70 --enforce-threshold; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 20 && tmux capture-pane -pt task-11-mutation -S - > evidence/task-11-parser-context-mutants.txt && tmux kill-session -t task-11-mutation
    Expected: evidence/task-11-parser-context-mutants.txt shows killed mutants for parser/context/byte-count targets or lists only excluded/no-op survivors after Task 14.
    Evidence: evidence/task-11-parser-context-mutants.txt

  Scenario: RTL gates pass if RTL changed
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-11-rtl "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 workflow/rtl-gen/scripts/rtl_compile_report.py mctp_assembler_scratch --project-root . && python3 workflow/lint/scripts/dut_lint_report.py mctp_assembler_scratch && python3 workflow/rtl-gen/scripts/derive_rtl_todos.py mctp_assembler_scratch --root . --audit-rtl; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 5 && tmux capture-pane -pt task-11-rtl -S - > evidence/task-11-rtl-gates.txt && tmux kill-session -t task-11-rtl
    Expected: evidence/task-11-rtl-gates.txt contains `exit=0` if RTL files changed; if no RTL changed, record `not applicable - no RTL changes` in the evidence file.
    Evidence: evidence/task-11-rtl-gates.txt
  ```

  Commit: YES | Message: `fix(mctp): kill parser context and byte-count mutants` | Files: [`mctp_assembler_scratch/tb/cocotb/mctp_scenario_vectors.py`, `mctp_assembler_scratch/tb/cocotb/scoreboard.py`, `mctp_assembler_scratch/rtl/*.sv`, `mctp_assembler_scratch/sim/*`, `mctp_assembler_scratch/mutation/*`]

- [ ] 12. Backpressure, readback, and descriptor adversarial scenarios

  What to do: Add adversarial timeline steps that hold/deassert ready signals and force descriptor queue/readback edge behavior. Target known meaningful survivors around SRAM packer full/pop ready, AXI read egress ready/valid hold, descriptor push/pop, and read descriptor state. Update scenario vectors, scoreboard expectations, and artifacts.
  Must NOT do: Do not create unrealistic protocol sequences that violate AXI/cocotb handshake rules.

  Parallelization: Can parallel: YES | Wave 3 | Blocks: [14] | Blocked by: [10]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `mctp_assembler_scratch/mutation/mutation_report.json:46` - current AXI read egress ready/valid survivor ID.
  - Pattern:  `mctp_assembler_scratch/mutation/mutation_report.json:487` - current `MUT_0030` result line in report.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_axi_read_egress.sv:37` - read response ready/valid survivor target.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_axi_read_egress.sv:76` - `read_has_descriptor_q` update survivor target.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_sram_packer.sv:39` - SRAM packer ready/valid survivor target.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_descriptor_queue.sv:55` - descriptor queue push/pop survivor target.
  - API/Type: `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:1248` - timeline operations available to drive waits and assignments.
  - External: `https://docs.cocotb.org/en/stable/triggers.html` - wait/edge primitives for deterministic backpressure.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_vectors.py tests/test_mctp_scoreboard_contracts.py -q` passes.
  - [ ] `python3 mctp_assembler_scratch/tb/cocotb/test_runner.py` exits 0 with adversarial scenarios included.
  - [ ] Mutation report after Task 14 shows the readback/descriptor/SRAM handshake candidates killed or classified with line-specific rationale.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Backpressure scenarios pass simulation
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-12-backpressure "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 mctp_assembler_scratch/tb/cocotb/test_runner.py; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 10 && tmux capture-pane -pt task-12-backpressure -S - > evidence/task-12-backpressure-sim.txt && tmux kill-session -t task-12-backpressure
    Expected: evidence/task-12-backpressure-sim.txt contains `exit=0`; scoreboard rows include backpressure/readback/descriptor coverage refs.
    Evidence: evidence/task-12-backpressure-sim.txt

  Scenario: Descriptor/readback row contains held-ready evidence
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-12-readback "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 - <<'PY'\nimport json\nfrom pathlib import Path\nrows = [json.loads(line) for line in Path('mctp_assembler_scratch/sim/scoreboard_events.jsonl').read_text().splitlines() if line.strip()]\nmatched = [r for r in rows if 'READBACK' in r['goal_id'] or 'DESCRIPTOR' in r['goal_id'] or 'BACKPRESSURE' in r['goal_id']]\nassert matched, 'missing readback/descriptor/backpressure rows'\nfor row in matched:\n    print(row['goal_id'], row['rtl_observed'])\nPY\nprintf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-12-readback -S - > evidence/task-12-readback-descriptor-evidence.txt && tmux kill-session -t task-12-readback
    Expected: evidence/task-12-readback-descriptor-evidence.txt contains at least one readback/descriptor/backpressure row and `exit=0`.
    Evidence: evidence/task-12-readback-descriptor-evidence.txt
  ```

  Commit: YES | Message: `test(mctp): cover backpressure and descriptor handshakes` | Files: [`mctp_assembler_scratch/tb/cocotb/mctp_scenario_vectors.py`, `mctp_assembler_scratch/tb/cocotb/scoreboard.py`, `mctp_assembler_scratch/rtl/*.sv`, `mctp_assembler_scratch/sim/*`, `mctp_assembler_scratch/mutation/*`]

- [ ] 13. Reset, control, and APB state scenarios

  What to do: Add or strengthen scenarios that prove reset values, APB control setup, per-Q APB visibility, parser enable behavior, CDC enable/drop state, and interrupt/debug state transitions. Use these to kill meaningful reset/control survivors while keeping unsupported reset categories reported accurately.
  Must NOT do: Do not rely only on reset compile/lint success; observe reset/control values in scoreboard or quality artifacts.

  Parallelization: Can parallel: YES | Wave 3 | Blocks: [14] | Blocked by: [10]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:930` - `_apply_goal_preconditions()` writes APB control and IRQ enable registers.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:1001` - CSR/APB drive special handling.
  - Pattern:  `mctp_assembler_scratch/tb/cocotb/test_mctp_assembler_scratch.py:1199` - `debug_context_key` observation retained.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_sram_packer.sv:29` - `sram_wr_valid` reset target.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_sram_packer.sv:34` - `pack_partial_valid` reset target.
  - Pattern:  `mctp_assembler_scratch/rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:31` - `enable_reg` constant/control survivor target.
  - Pattern:  `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml:3032` - `SC_APB_REGS_PER_Q` scenario definition.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scenario_vectors.py tests/test_mctp_scoreboard_contracts.py -q` passes.
  - [ ] `python3 mctp_assembler_scratch/tb/cocotb/test_runner.py` exits 0 and emits APB/reset/control scenario rows.
  - [ ] `python3 workflow/tb-gen/scripts/check_scoreboard_events.py mctp_assembler_scratch --root . --source-check --require-events` exits 0.
  - [ ] If RTL changes, compile/lint/audit commands from Task 11 pass.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: APB/reset/control scenario rows are emitted
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-13-apb "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 mctp_assembler_scratch/tb/cocotb/test_runner.py && python3 - <<'PY'\nimport json\nfrom pathlib import Path\nrows = [json.loads(line) for line in Path('mctp_assembler_scratch/sim/scoreboard_events.jsonl').read_text().splitlines() if line.strip()]\nmatched = [r for r in rows if 'APB' in r['goal_id'] or 'RESET' in r['goal_id'] or 'CONTROL' in r['goal_id']]\nassert matched, 'missing APB/reset/control rows'\nfor row in matched:\n    print(row['goal_id'], row['rtl_observed'].get('apb_ready'), row['rtl_observed'].get('apb_read_data'), row['rtl_observed'].get('debug_context_key'))\nPY\nprintf '\nexit=%s\n' \$?; sleep 3600" && sleep 10 && tmux capture-pane -pt task-13-apb -S - > evidence/task-13-apb-reset-control.txt && tmux kill-session -t task-13-apb
    Expected: evidence/task-13-apb-reset-control.txt contains `exit=0` and prints APB/reset/control rows.
    Evidence: evidence/task-13-apb-reset-control.txt

  Scenario: Disabled parser/control path fails closed
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-13-disabled "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_mctp_scoreboard_contracts.py -q -k disabled_control; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-13-disabled -S - > evidence/task-13-disabled-control.txt && tmux kill-session -t task-13-disabled
    Expected: evidence/task-13-disabled-control.txt contains `passed` and proves disabled control suppresses VDM/context behavior.
    Evidence: evidence/task-13-disabled-control.txt
  ```

  Commit: YES | Message: `test(mctp): cover reset control and apb state` | Files: [`mctp_assembler_scratch/tb/cocotb/mctp_scenario_vectors.py`, `mctp_assembler_scratch/tb/cocotb/scoreboard.py`, `mctp_assembler_scratch/rtl/*.sv`, `mctp_assembler_scratch/sim/*`, `mctp_assembler_scratch/mutation/*`]

- [ ] 14. Mutation threshold enforcement and closure artifacts

  What to do: Run the final mutation guard with threshold enforcement after Tasks 11-13. Commit fresh mutation reports, simulation-quality reports, and any signoff/ledger updates required by the repo workflow. The final report must distinguish killed mutants, meaningful survivors, excluded instrumentation-only candidates, invalid mutants, and unsupported categories.
  Must NOT do: Do not mark the task done if meaningful kill rate is below threshold. Do not hide survivors in markdown without corresponding JSON fields.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [final verification] | Blocked by: [5, 11, 12, 13]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `workflow/mutation/scripts/mutation_guard.py:629` - mutation guard CLI options.
  - Pattern:  `workflow/mutation/scripts/mutation_guard.py:670` - threshold enforcement.
  - Pattern:  `workflow/mutation/scripts/mutation_guard.py:701` - mutation report output paths.
  - Pattern:  `mctp_assembler_scratch/mutation/mutation_report.json:965` - current baseline summary is `kill_rate=0.2812`, `killed=9`, `survived=23`.
  - Pattern:  `doc/golden_todo_evidence_flow.md:55` - evidence-required policy.
  - Pattern:  `doc/ip_workflow_guide.md:319` - stage stop-condition guidance and monitored artifacts.

  Acceptance criteria (agent-executable only):
  - [ ] `python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32 --timeout-sec 60 --threshold 0.70 --enforce-threshold` exits 0.
  - [ ] `python3 - <<'PY'\nimport json\nfrom pathlib import Path\nreport = json.loads(Path('mctp_assembler_scratch/mutation/mutation_report.json').read_text())\nsummary = report['summary']\nassert summary['executed'] >= 32\nassert summary['kill_rate'] >= 0.70, summary\nmeaningful_survivors = [r for r in report.get('results', []) if r.get('status') == 'survived' and not r.get('excluded')]\nassert not meaningful_survivors, meaningful_survivors[:3]\nassert report.get('excluded_summary') or report.get('instrumentation_noop_summary')\nPY` succeeds.
  - [ ] `python3 workflow/sim_debug/scripts/check_simulation_quality.py mctp_assembler_scratch --root . --require-class write --require-class memory_pack --require-class interleave --require-class readback --require-class register --require-class drop --require-class boundary --require-class protocol --require-class fsm` exits 0 after mutation reports are fresh.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Mutation threshold is enforced
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-14-mutation "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32 --timeout-sec 60 --threshold 0.70 --enforce-threshold; printf '\nexit=%s\n' \$?; sleep 3600" && sleep 20 && tmux capture-pane -pt task-14-mutation -S - > evidence/task-14-mutation-threshold.txt && tmux kill-session -t task-14-mutation
    Expected: evidence/task-14-mutation-threshold.txt contains `exit=0`; JSON summary has `kill_rate >= 0.70`.
    Evidence: evidence/task-14-mutation-threshold.txt

  Scenario: Reports separate no-op exclusions from meaningful survivors
    Tool:     tmux
    Steps:    mkdir -p evidence && tmux new-session -d -s task-14-report "cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 - <<'PY'\nimport json\nfrom pathlib import Path\nreport = json.loads(Path('mctp_assembler_scratch/mutation/mutation_report.json').read_text())\nprint(json.dumps({k: report.get(k) for k in ['summary','category_summary','excluded_summary','instrumentation_noop_summary']}, indent=2, sort_keys=True))\nremaining = [r for r in report.get('results', []) if r.get('status') == 'survived' and not r.get('excluded')]\nprint('meaningful_survivors', len(remaining))\nassert not remaining\nPY\nprintf '\nexit=%s\n' \$?; sleep 3600" && sleep 2 && tmux capture-pane -pt task-14-report -S - > evidence/task-14-mutation-report-audit.txt && tmux kill-session -t task-14-report
    Expected: evidence/task-14-mutation-report-audit.txt contains `meaningful_survivors 0` and `exit=0`.
    Evidence: evidence/task-14-mutation-report-audit.txt
  ```

  Commit: YES | Message: `test(mutation): enforce meaningful mctp mutation threshold` | Files: [`workflow/mutation/scripts/mutation_guard.py`, `tests/test_mutation_guard.py`, `mctp_assembler_scratch/mutation/mutation_report.json`, `mctp_assembler_scratch/mutation/mutation_report.md`, `mctp_assembler_scratch/sim/simulation_quality.json`, `mctp_assembler_scratch/sim/simulation_quality.md`, `mctp_assembler_scratch/signoff/*`, `evidence/task-14-mutation-threshold.txt`, `evidence/task-14-mutation-report-audit.txt`]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: plans/expand_mctp_verification_cases.md`.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
