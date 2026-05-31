# Draft: MCTP Assembler Req-to-Audit Scratch Plan

## Requirements (confirmed)
- User request: "SSOT to Audit $omo:ulw-plan"
- User correction: "req 부터 scratch 구현이야 새로 doc/wiki workflow 참고해."
- Follow-up context: this is for the AXI4 256-bit PCIe VDM MCTP assembler discussed in this thread, not a generic IP exercise.
- The plan must start from requirements and drive a new scratch implementation through SSOT/audit/signoff using the repo workflow stages.
- The plan must not implement code in this planning turn.

## Technical Decisions
- Planning tier: Architecture. This touches SSOT, FL, CL, RTL, cocotb/pyuvm TB, coverage, mutation, and signoff.
- Scratch target: create a new IP directory from requirements rather than repairing the existing `mctp_assembler/` implementation. Existing `mctp_assembler/` artifacts are references and prior evidence only, not authority for the new implementation.
- Source truth priority:
  1. `mctp_assembler/req/mctp_assembler_requirements.md`
  2. `mctp_assembler/req/source_references.md`
  3. `workflow/STAGE_MANIFEST.json`
  4. `doc/wiki/index.md`, `doc/wiki/common-ai-agent-map.md`, `workflow/COMMON_ENGINE_FLOW.md`, `doc/wiki/workflow-ownership-and-boundaries.md`, `doc/wiki/golden-todo-evidence.md`, `doc/wiki/full-flow-pipeline.md`
  5. Existing generated artifacts under `mctp_assembler/` only as patterns or anti-pattern evidence.
- Execution mode for future work: TDD/RED-GREEN where production behavior changes are made; test-first tasks must capture failing evidence before implementation.

## Skill Survey
- Use `omo:ulw-plan`: requested by user; produces decision-complete plan artifacts only.
- Do not use implementation skills in this turn: source/code edits are out of scope for planning.
- Do not use browser/computer-use/document/presentation/spreadsheet/image skills: no matching deliverable.

## Research Findings
- `workflow/STAGE_MANIFEST.json` defines the canonical SSOT-to-signoff route: ssot, emit_fl, emit_cl, emit_equiv_goals, derive_ip_contract, emit_goal_scoreboard, tb_python_compile, rtl_compile, dut_lint, sim, scoreboard_schema, coverage, rtl_provenance_refresh, rtl_final_gate, mutation_guard, signoff.
- `mctp_assembler/req/mctp_assembler_requirements.md` now defines AXI4 write ingress, AXI4 read payload path, 256-bit SRAM read/write, per-Q FSM/register visibility, first/last TLP header snapshots, drop conditions, and MCTP assembly semantics.
- `doc/wiki/full-flow-pipeline.md` defines the canonical DAG: requirement -> ssot-gen -> FL/CL -> equiv-goals -> rtl-gen -> lint/TB/syn -> sim -> coverage/sim-debug -> goal-audit.
- `workflow/COMMON_ENGINE_FLOW.md` requires common-engine ownership and forbids manually patching generated artifacts to fake a pass.
- `doc/wiki/workflow-ownership-and-boundaries.md` maps artifact ownership and repair routing.
- `doc/wiki/golden-todo-evidence.md` requires todos to carry source refs, owner workflow, approval policy, and required evidence.
- Existing `mctp_assembler/yaml`, `rtl`, `tb`, and sim artifacts must not be treated as the starting point for implementation; they only inform naming, gaps, and QA expectations.

## Open Questions
- None blocking for plan generation. Defaults below are applied so execution can start without another interview.

## Defaults Applied
- New scratch IP slug: `mctp_assembler_scratch`. This avoids mutating stale `mctp_assembler/` evidence while still using the same requirement source.
- AXI IDs stay out of first target; no multiple outstanding reads/writes.
- AXI read addresses are 32-byte aligned; firmware trims using descriptor base/length.
- SRAM write traffic has priority over firmware reads unless SSOT later explicitly changes QoS.
- Formal proof is optional wiki/future work, not part of required first audit closure.
- Mutation guard is advisory but required as an audit-depth signal before final signoff claim.

## Scope Boundaries
- INCLUDE: requirement approval artifact, scratch SSOT, FL/CL/equivalence/ip-contract/TB, RTL, sim/coverage/mutation/goal-audit/signoff, evidence records.
- EXCLUDE: PCIe endpoint, PCIe Flit Mode, ECRC checking, full DMTF conformance certification, PnR/PPA signoff, production waiver approval.
