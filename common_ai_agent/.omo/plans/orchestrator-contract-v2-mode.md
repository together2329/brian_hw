# Orchestrator Contract V2 Mode Implementation And Test Plan

## Goal

Promote the current MCTP Contract V2 pilot into an orchestrator-visible
common-engine path:

```text
locked truth
-> requirement
-> obligation
-> contract_ref
-> FL / CL / RTL / TB / SIM reflection
-> executable evidence
-> deterministic validator closure
-> owner-routed repair
```

This must work in two modes:

- Default mode: one serialized worker runs the same contract stages manually.
- Orchestrator mode: the orchestrator dispatches stages, reads deterministic
  reports, and routes failures to the owning workflow worker.

## Key Decisions

- Add three real engine stages: `contract-overlay`, `evidence-contract`, and
  `contract-reflection`.
- Add `contract-v2` as a dispatch macro only. It expands to
  `contract-overlay -> evidence-contract + contract-reflection`; it is not a
  fourth engine stage.
- Owner workflow for the three contract stages is `contract-reflection`.
- CL repair routes to `workflow="fl-model-gen", stages=["cl-model"]`; do not
  introduce `cl-model-gen`.
- Missing upstream inputs are `blocked`; evaluated predicates that fail are
  `fail`.
- Contract scripts must write machine-readable status reports. Stage engine
  reads the report status instead of inferring success from prose.
- `contract_owner_routing.json` must include the full rerun list after repair.
- Initial rollout is opt-in for default/full pipeline. Engineering mode can ask
  for `contract-v2`; Signoff-required promotion waits until MCTP and one
  non-MCTP fixture pass.
- Current MCTP reference expectation:
  - `evidence_contract_coverage`: `pass`, `91/91`
  - `contract_reflection_coverage`: `pass`, `7/7`

## Core User Flow

User gives a requirement or approves existing requirements.

```text
ssot-gen:
  lock truth in req/ and SSOT

fl-model-gen:
  generate FL meaning model
  generate CL cycle/order/protocol model
  generate equivalence goals

rtl-gen:
  implement owner modules and observable paths

tb-gen:
  implement cocotb/pyuvm scenarios, monitors, and scoreboard fields

sim:
  run simulation, scoreboard, and VCD/FST capture

contract-reflection:
  derive/check Contract V2 artifacts
  close or fail obligations
  route failures to the owner workflow
```

The LLM may author, review, and explain. It must not approve Contract V2
closure. Validator reports are the pass/fail authority.

## Stage DAG

Explicit stage sequence for orchestrator mode:

```text
ssot
-> fl-model
-> cl-model
-> equivalence
-> rtl
-> lint + tb
-> sim
-> contract-overlay
-> evidence-contract + contract-reflection
```

`dispatch_workflow(stages=["contract-v2"], schedule="dag")` must expand to:

```text
["contract-overlay", "evidence-contract", "contract-reflection"]
```

The stage engine itself only sees the three concrete stage IDs.

## Owner Routing

Add `signoff/contract_owner_routing.json`.

Required fields:

```json
{
  "type": "contract_owner_routing",
  "status": "blocked",
  "owner": "tb-gen",
  "workflow": "tb-gen",
  "stages": ["tb"],
  "reason": "scoreboard row missing required observable",
  "failed_obligation_ids": ["OBL_MCTP_APB_VIS_001"],
  "failed_contract_refs": ["APB_Q_PAYLOAD_COUNT_VISIBILITY"],
  "forbidden_edits": [
    "do not hand-edit sim/scoreboard_events.jsonl",
    "do not lower SSOT requirements"
  ],
  "rerun_after_repair": ["tb", "sim", "contract-overlay", "evidence-contract", "contract-reflection"]
}
```

Routing precedence:

```text
missing/ambiguous locked truth:
  human or ssot-gen

missing requirement_id / obligation_id / contract_ref schema:
  contract-reflection

FL expected missing/wrong:
  fl-model-gen, stages=["fl-model"]

CL latency/order/hold/backpressure missing/wrong:
  fl-model-gen, stages=["cl-model"]

RTL observable missing:
  rtl-gen

RTL observed value violates predicate:
  rtl-gen

TB monitor/scoreboard field missing while RTL/VCD signal exists:
  tb-gen

VCD artifact missing:
  sim

VCD exists but dumped signal missing and tb_manifest lacks observable:
  tb-gen

VCD exists but RTL observable path is absent:
  rtl-gen

stale sim/scoreboard/VCD against upstream hashes:
  sim

ambiguous mismatch classification:
  sim_debug

waiver/spec sufficiency:
  human
```

Every route must include `rerun_after_repair`; orchestrator does not guess the
downstream rerun scope.

## Implementation TODOs

### 1. Register Contract Stages In The Pipeline

Files:

- `workflow/STAGE_MANIFEST.json`
- `src/atlas_api_jobs.py`
- `tests/test_atlas_pipeline_contract.py`
- `tests/test_db_frontend_phase3_integration.py`

Work:

- Add `contract-overlay`, `evidence-contract`, and `contract-reflection` stage
  definitions.
- Add deps:
  - `contract-overlay`: depends on `sim`
  - `evidence-contract`: depends on `contract-overlay`
  - `contract-reflection`: depends on `contract-overlay`
- Add dispatch macro expansion for `contract-v2`.
- Keep default full pipeline opt-in at first; do not silently change all
  existing full-pipeline tests unless the test is explicitly for Contract V2.
- Update duplicated pipeline artifact maps:
  - `_job_artifact_recovery`
  - `_job_artifact_failure`
  - in-process pipeline state artifact map
  - any stage failure/recovery summary paths
- Fix stale frontend parity references from `pipeline.jsx` to `pipeline.tsx`
  where the touched tests still mention the old filename.

Acceptance:

- Pipeline resolver accepts all three concrete stages.
- `contract-v2` expands only in stage-list dispatch and never appears as a job
  stage ID.
- Existing full-pipeline tests either remain unchanged or explicitly assert the
  opt-in Contract V2 variant.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_pipeline_contract.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_db_frontend_phase3_integration.py -q
```

### 2. Register Stage Engine And Surface Support

Files:

- `src/workflow_stage_engine.py`
- `src/workflow_stage_surface.py`
- `tests/test_workflow_stage_engine.py`
- `tests/test_workflow_stage_surface.py`

Work:

- Add aliases in `STAGE_ALIASES`.
- Add `STAGE_WORKFLOW` mapping to `contract-reflection`.
- Add the stages to `COMMON_ENGINE_STAGES`.
- Implement:
  - `_run_contract_overlay`
  - `_run_evidence_contract`
  - `_run_contract_reflection`
- Use `_run_tool` and write logs:
  - `logs/stage_engine/contract-overlay.json`
  - `logs/stage_engine/evidence-contract.json`
  - `logs/stage_engine/contract-reflection.json`
- Stage status translation:
  - report `status=pass` -> stage `pass`
  - report `status=fail` -> stage `fail`
  - report `status=blocked` -> stage `blocked`
  - script fails without report -> stage `fail`
  - missing SSOT before non-sim diagnostic stage -> stage `blocked`

Acceptance:

- Stage engine reports deterministic status and artifacts.
- Failed contract evidence never becomes pass.
- Surface sessions use `<ip>/contract-reflection`.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_workflow_stage_engine.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_workflow_stage_surface.py -q
```

### 3. Create The Contract-Reflection Workflow Workspace

Files:

- `workflow/contract-reflection/workspace.json`
- `workflow/contract-reflection/commands/contract-overlay.json`
- `workflow/contract-reflection/commands/evidence-contract.json`
- `workflow/contract-reflection/commands/contract-reflection.json`
- `workflow/loader.py`
- `tests/test_workflow_tool_inventory.py`

Work:

- Add minimal workspace JSON following existing worker workspaces.
- Set:
  - `WORKFLOW_DISABLED_TOOLS=ask_user,record_ssot_qa,dispatch_workflow`
  - `execution_mode=sequential`
- Add command JSON with `handler: "stage:<stage-id>"`.
- Do not change `workflow/loader.py` unless a discovery test fails.

Acceptance:

- Commands are discovered by loader.
- Worker tool schema does not expose `dispatch_workflow`.
- The workspace does not permit worker-to-worker dispatch.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_workflow_tool_inventory.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_workflow_stage_surface.py -q
```

### 4. Register Worker Routing And Toolchain Defaults

Files:

- `src/atlas_api_jobs.py`
- `tests/test_workflow_tool_inventory.py`
- `tests/test_pipeline_orchestrator_worker_integration.py`

Work:

- Add `contract-reflection` to `_DEFAULT_WORKER_PORTS`.
- Add env suffix support via existing worker URL convention:
  - `WORKER_URL_CONTRACT_REFLECTION`
  - `ATLAS_WORKER_URL_CONTRACT_REFLECTION`
- Add model/toolchain metadata used by worker status payloads.
- Ensure `_PIPELINE_BY_WORKFLOW` ambiguity is handled because three stages share
  one workflow. A workflow-only lookup for `contract-reflection` should map to
  `contract-overlay` only if explicitly documented; stage-list dispatch must use
  stage IDs.

Acceptance:

- Orchestrator can dispatch a fake `contract-reflection` worker in tests.
- Tool inventory remains in sync with `_DEFAULT_WORKER_PORTS`.
- Shared-workflow stages do not dedupe each other incorrectly.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_workflow_tool_inventory.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py -q
```

### 5. Harden Contract Overlay Generation

Files:

- `workflow/contract-reflection/scripts/emit_goal_contract_overlay.py`
- `workflow/contract_reflection/*.py`
- `tests/test_goal_contract_overlay.py`
- `tests/test_contract_reflection_stage_gate.py`

Work:

- Support two modes:
  - Seed mode: create Contract V2 skeleton from approved req/SSOT/equivalence
    artifacts when Contract V2 files are absent.
  - Overlay mode: preserve existing stable IDs and add goal-derived obligations
    without claiming closure.
- If no locked requirement or approval source exists, write a blocked report
  instead of inventing truth.
- Preserve byte-idempotence when inputs are unchanged.

Acceptance:

- Requirements are not fabricated from LLM confidence.
- Overlay can run on MCTP and preserve `91/91` evidence-contract expectation.
- Missing locked truth becomes blocked/human, not pass.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_goal_contract_overlay.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_contract_reflection_stage_gate.py -q
```

### 6. Standardize Contract Checker Reports

Files:

- `workflow/contract-reflection/scripts/check_evidence_contract.py`
- `workflow/contract-reflection/scripts/check_contract_reflection.py`
- `tests/test_contract_reflection_gate.py`
- `tests/test_evidence_contract_artifact_rows.py`

Work:

- Always write status JSON when possible.
- Use `blocked` for missing required upstream artifacts:
  - SSOT
  - scoreboard
  - VCD/FST
  - required Contract V2 artifact
- Use `fail` for malformed contract schema or evaluated predicate failures.
- Include hashes/mtimes for:
  - SSOT
  - FL/CL
  - RTL
  - TB
  - scoreboard
  - VCD/FST
- Include failed obligation IDs, failed contract refs, and observed predicate
  details in reports.

Acceptance:

- Stage engine can trust `status`.
- Stale evidence is visible.
- Forged rows without required observables still fail.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_contract_reflection_gate.py tests/test_evidence_contract_artifact_rows.py -q
```

### 7. Add Deterministic Owner Router

Files:

- `workflow/contract-reflection/scripts/classify_contract_owner.py`
- `src/workflow_stage_engine.py`
- `src/orchestrator/classify.py`
- `src/orchestrator/tools.py`
- `tests/test_contract_reflection_gate.py`
- `tests/test_orchestrator_tools.py`

Work:

- Add path-safe router script that reads Contract V2 reports and writes
  `signoff/contract_owner_routing.json`.
- Integrate it into failed or blocked `evidence-contract` and
  `contract-reflection` stage runs.
- Decide integration boundary:
  - `classify_contract_owner.py` is the deterministic authority.
  - `classify_failure_tool` may preview/relay its result but does not override
    owner routing.
- Add a human-gate route shape for spec/waiver decisions:
  - `owner: "human"`
  - `workflow: ""`
  - `stages: []`
  - `status: "human_gate"`
  - `questions` or `review_required` payload.

Acceptance:

- A contract failure produces one primary owner route or human gate.
- The route includes a complete `rerun_after_repair`.
- The route forbids editing generated sim evidence to force green.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_contract_reflection_gate.py tests/test_orchestrator_tools.py -q
```

### 8. Surface Contract Artifacts To Orchestrator

Files:

- `src/orchestrator/tools.py`
- `src/atlas_api_jobs.py`
- `tests/test_orchestrator_tools.py`
- `tests/test_pipeline_orchestrator_worker_integration.py`

Work:

- Add `read_artifact` mappings for:
  - `contract-overlay`
  - `evidence-contract`
  - `contract-reflection`
  - `contract-owner-routing`
- Add previews for:
  - `summary`
  - `failed_obligation_ids`
  - `failed_contract_refs`
  - `owner`
  - `workflow`
  - `rerun_after_repair`
- Update pipeline-state artifact rendering and job recovery/failure logic.

Acceptance:

- Orchestrator can answer “why did Contract V2 fail?” from artifacts.
- Pipeline state shows contract stage pass/fail/blocked without raw path guessing.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_orchestrator_tools.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py -q
```

### 9. Update Orchestrator Prompt, Budgets, And Active-Job Policy

Files:

- `src/orchestrator/prompts.py`
- `src/orchestrator/budgets.py`
- `src/orchestrator/react_bridge.py`
- `tests/test_orchestrator_budgets.py`
- `tests/test_orchestrator_react_loop_parity.py`

Work:

- Add stage vocabulary and examples for Contract V2.
- Add dispatch macro instructions for `contract-v2`.
- Add budgets for:
  - `contract-overlay`
  - `evidence-contract`
  - `contract-reflection`
  - `contract-reflection` workflow
- Prompt rules:
  - read validator reports before finalizing
  - read owner routing before repair dispatch
  - dispatch exactly one owner repair on fail/blocked
  - yield while owner repair worker is active
  - do not claim pass from LLM reasoning
- Grep and fix docs/prompts that still imply `cl-model-gen`.

Acceptance:

- Contract pass path finalizes only with validator evidence.
- Contract fail path dispatches the routed owner and yields.
- Budget exhaustion blocks repeated blind dispatch.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_orchestrator_budgets.py tests/test_orchestrator_react_loop_parity.py -q
rg -n "cl-model-gen" src doc workflow
```

### 10. Test MCTP As The Reference Fixture

Files:

- `mctp_assembler_scratch/verify/requirements_index.json`
- `mctp_assembler_scratch/verify/evidence_contract.json`
- `mctp_assembler_scratch/verify/contract_reflection.json`
- `mctp_assembler_scratch/signoff/evidence_contract_coverage.json`
- `mctp_assembler_scratch/signoff/contract_reflection_coverage.json`
- `mctp_assembler_scratch/signoff/contract_owner_routing.json`

Work:

- Use MCTP as the acceptance fixture.
- Do not hand-edit generated sim outputs.
- Assert the current green Contract V2 summaries:
  - evidence contract `pass`, total `91`, failed `0`
  - contract reflection `pass`, total `7`, failed `0`
- Add a negative fixture or temp copy where one scoreboard observable is missing;
  assert owner route instead of changing MCTP evidence.

Acceptance:

- Real MCTP runs close Contract V2.
- Negative fixture proves the new gate catches a missing obligation path.

QA:

```bash
python3 workflow/contract-reflection/scripts/emit_goal_contract_overlay.py mctp_assembler_scratch --root .
python3 workflow/contract-reflection/scripts/check_contract_reflection.py mctp_assembler_scratch --root .
python3 workflow/contract-reflection/scripts/check_evidence_contract.py mctp_assembler_scratch --root .
jq '{status, summary}' mctp_assembler_scratch/signoff/evidence_contract_coverage.json
jq '{status, summary}' mctp_assembler_scratch/signoff/contract_reflection_coverage.json
```

### 11. Add End-To-End Orchestrator Tests

Files:

- `tests/test_pipeline_orchestrator_worker_integration.py`
- `tests/test_workflow_tool_inventory.py`
- `tests/test_orchestrator_tools.py`

Work:

- Add fake worker tests for the new workflow URL.
- Test `dispatch_workflow(stages=["contract-v2"], schedule="dag")`.
- Test explicit stage dispatch with the three concrete stages.
- Test contract failure:
  - pipeline job fails/blocks
  - owner route is written
  - orchestrator dispatches routed owner
  - orchestrator yields while active owner job runs
- Test dedupe:
  - active `contract-overlay` does not suppress a later
    `evidence-contract` job
  - duplicate same stage/IP does dedupe.

Acceptance:

- Multi-stage orchestrator path is covered from dispatch through pipeline state.
- Worker completion without contract evidence is not marked green.
- Shared `contract-reflection` workflow does not collapse all three stages into
  one job.

QA:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_workflow_tool_inventory.py -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_orchestrator_tools.py -q
```

### 12. Preserve Default Mode And Document The Boundary

Files:

- `doc/wiki/contract-reflection-workflow.md`
- `doc/wiki/default-agent-ip-flow.md`
- `doc/wiki/orchestrator-worker-handoff.md`
- `doc/wiki/atlas-single-active-orchestrator-subworkers-20260603.md`
- `workflow/COMMON_ENGINE_FLOW.md`
- `doc/wiki/index.md`
- `doc/wiki/log.md`

Work:

- Document:
  - default mode can run Contract V2 serially
  - orchestrator mode owns multi-owner repair dispatch
  - strict single-worker mode is valid but slower and cannot run multiple owner
    repairs concurrently
  - interactive single-worker policy is separate from orchestrator job workers
  - `contract-v2` is a dispatch macro, not a stage
  - deterministic validator is the judge; LLM is author/reviewer
- Update wiki graph.

Acceptance:

- Docs and prompts agree on stage names and workflow owners.
- No broken wiki refs.

QA:

```bash
python3 workflow/wiki/build_graph.py --check
```

## Test Matrix

Unit:

```text
stage alias canonicalization
contract-v2 macro expansion
stage engine status translation
checker pass/fail/blocked reports
owner-router precedence
path traversal rejection
artifact preview summaries
budget exhaustion
```

Integration:

```text
MCTP real Contract V2 pass
negative missing-observable owner route
workflow command discovery
orchestrator dispatch DAG
pipeline state polling
active job yield
downstream stale rerun list
shared workflow multi-stage dedupe
```

Negative:

```text
missing requirement_id
missing obligation_id
missing contract_ref
missing SSOT
missing scoreboard
missing VCD
missing TB observable
forged scoreboard pass
wrong RTL observed value
stale sim against upstream inputs
worker exposing dispatch_workflow
LLM-only approval attempt
```

## Rollout Phases

Phase 1:

- Add stages, workspace, engine runners, artifact previews.
- Keep Contract V2 opt-in.
- MCTP must stay green.

Phase 2:

- Add owner router and orchestrator repair dispatch tests.
- Add negative fixtures.

Phase 3:

- Add one non-MCTP IP fixture.
- Promote Engineering mode to recommend Contract V2 after sim.

Phase 4:

- Make Contract V2 required for Signoff mode.
- Any missing required obligation becomes blocked, not pass.

## Done Definition

The work is done when:

- `contract-overlay`, `evidence-contract`, and `contract-reflection` are
  common-engine stages.
- `dispatch_workflow(stages=["contract-v2"])` expands to the three concrete
  stages.
- Orchestrator can read Contract V2 reports and owner routing.
- Contract failures route to exactly one owner workflow or human gate.
- Default mode can run the same stages serially.
- MCTP Contract V2 reference passes with the expected summaries.
- Negative fixtures prove missing evidence fails or blocks.
- Tests cover stage engine, pipeline, orchestrator tools, budgets, worker
  inventory, and wiki graph.

