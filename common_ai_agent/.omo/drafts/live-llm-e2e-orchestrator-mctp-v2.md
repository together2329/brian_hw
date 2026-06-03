# Draft: Live LLM E2E Orchestrator MCTP V2

## Requirements (confirmed)
- Plan a live LLM-based E2E test for the orchestrator path.
- Use the contract-v2 idea we discussed: locked truth -> requirement -> obligation -> contract_ref -> FL/CL/RTL/TB/SIM evidence -> validator closure.
- Validate whether a real requirement can be closed through orchestrator mode, not only mocks.

## Technical Decisions
- Scope the first live test to the existing `mctp_assembler_scratch` contract-v2 reference closure, because it already has deterministic closed evidence: `contract_check=pass`, reflection `7/7`, evidence `91/91`.
- Treat the LLM/orchestrator as the dispatcher and analyst, not the final judge. Pass/fail must come from `workflow/contract-reflection/scripts/run_contract_check.py`.
- Use a phased ladder: deterministic preflight, real worker/UI process smoke, live LLM headless orchestrator dispatch, UI Playwright verification, then negative owner-routing.
- Keep this out of default CI. Gate it behind an explicit live flag because it uses real LLM calls and long-running local processes.

## Research Findings
- `src/main.py` supports `--serve`, `--workflow`, and `--all-workflows` for worker/server execution.
- `src/atlas_runtime_run.py` supports `--exec orchestrator` and configures lazy worker behavior for orchestrator mode.
- `workflow/STAGE_MANIFEST.json` defines `contract_check` and stage `contract-check`.
- `src/workflow_stage_engine.py` runs `contract-check` via `run_contract_check.py` and expects `contract_check.json`, `contract_reflection_coverage.json`, `evidence_contract_coverage.json`, and `contract_owner_routing.json`.
- `mctp_assembler_scratch/signoff/contract_check.json` currently reports `pass` with evidence `91/91` and reflection `7/7`.

## Open Questions
- None blocking. Default: use existing `.env`/`.config` model settings without printing secret values.

## Scope Boundaries
- INCLUDE: live local processes, real LLM calls, orchestrator dispatch, worker execution, MCTP contract-v2 check, UI visibility, owner-route negative test.
- EXCLUDE: full production signoff, PNR/STA/DFT/CDC/PPA/formal closure, exhaustive full-IP regeneration, default CI enablement.
