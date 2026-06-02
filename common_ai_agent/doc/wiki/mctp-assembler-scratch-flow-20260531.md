---
type: run
tags: [ip-flow, mctp, signoff, mutation, owner-routing]
updated: 2026-06-01
related: [common-ai-agent-map, workflow-ownership-and-boundaries, rtl-gen-ssot-contract, mutation-baseline-2026-05-23, human-review-and-escalation, truth-coverage-gate]
---

# MCTP Assembler Scratch Flow - 2026-05-31

This page records the fresh `mctp_assembler_scratch` req-to-audit run. It is a handoff map, not a production conformance claim. The original local evidence bundle passed the pre-truth-coverage signoff. After the 2026-06-01 `truth_coverage` gate was added, final signoff became stricter; the refresh now maps all locked-truth obligations to executable evidence and passes local signoff.

## Scope

The IP was built from the current user requirements, not by reusing prior `mctp_assembler/` proof artifacts.

- AXI4 write ingress, 256-bit `WDATA`, one PCIe VDM TLP per AXI write transaction.
- Multi-beat AXI write bursts; `WLAST` ends the TLP.
- SRAM interface is 256-bit and stores only packed MCTP payload bytes with no alignment holes.
- Assembler contexts are keyed for interleaving by source EID, tag owner, message tag, and related MCTP fields.
- Per-Q state, base address, counters, debug/control/status/interrupt registers are visible through APB.
- AXI4 read egress lets firmware read assembled payload from SRAM-backed descriptors.
- Packet drop and assembly drop reasons are counted and exposed.

Out of scope for this run: formal proof, PnR/PPA signoff, DMTF certification, PCIe endpoint behavior, ECRC checking, and Flit Mode.

## Evidence Bundle

Primary artifacts:

- Requirements: `mctp_assembler_scratch/req/`
- SSOT: `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml`
- FL/CL: `mctp_assembler_scratch/model/functional_model.py`, `mctp_assembler_scratch/model/cycle_model.py`
- Goals/contract: `mctp_assembler_scratch/verify/equivalence_goals.json`, `mctp_assembler_scratch/verify/ip_contract.json`
- RTL/TB: `mctp_assembler_scratch/rtl/`, `mctp_assembler_scratch/tb/cocotb/`
- Sim/debug: `mctp_assembler_scratch/sim/`
- Simulation quality: `mctp_assembler_scratch/sim/simulation_quality.json`
- Coverage: `mctp_assembler_scratch/cov/`
- Mutation: `mctp_assembler_scratch/mutation/mutation_report.json`
- Signoff: `mctp_assembler_scratch/signoff/ip_signoff.json`
- Truth coverage: `mctp_assembler_scratch/signoff/truth_coverage.json`
- Owner routes: `mctp_assembler_scratch/signoff/signoff_owner_routes.json`
- Evidence authority: `mctp_assembler_scratch/signoff/evidence_authority_manifest.json`

Useful commands:

```bash
python3 workflow/ssot-gen/scripts/verify_ssot.py mctp_assembler_scratch --root . --mode signoff
python3 workflow/fl-model-gen/scripts/emit_fl_model.py mctp_assembler_scratch --root .
python3 workflow/fl-model-gen/scripts/emit_cycle_model.py mctp_assembler_scratch --root .
python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py mctp_assembler_scratch --root .
python3 workflow/ip-contract/scripts/derive_ip_contract.py mctp_assembler_scratch --root .
python3 workflow/rtl-gen/scripts/derive_rtl_todos.py mctp_assembler_scratch --root . --audit-rtl
python3 workflow/rtl-gen/scripts/rtl_compile_report.py mctp_assembler_scratch --root .
python3 workflow/lint/scripts/dut_lint_report.py mctp_assembler_scratch --root .
python3 mctp_assembler_scratch/tb/cocotb/test_runner.py
python3 workflow/tb-gen/scripts/check_scoreboard_events.py mctp_assembler_scratch --root . --source-check --require-events
python3 workflow/sim_debug/scripts/check_simulation_quality.py mctp_assembler_scratch --root . --require-class write --require-class readback --require-class drop --require-class memory_pack --require-class register --require-class boundary --require-class interleave --require-class protocol --require-class fsm --require-class module --require-class coverage
python3 workflow/coverage/scripts/ssot_coverage_summary.py mctp_assembler_scratch --root .
python3 workflow/reqcov/scripts/check_truth_coverage.py mctp_assembler_scratch --root .
python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32
python3 workflow/signoff/scripts/check_ip_signoff.py mctp_assembler_scratch --root .
```

## Current Result

Current stricter signoff result:

```text
status=pass
gates=18
passed=18
failed=0
blocked=0
```

The refreshed `truth_coverage` gate reports 95 locked-truth obligations, 95 covered, and 0 required obligations uncovered. The closure came from mapping existing executable evidence, not from reducing SSOT scope: cycle coverage bins, `EQ_REGISTER_*` scoreboard goals, interrupt cause evidence, static RTL todo gates, and signoff artifact gates are now credited by the checker.

The local evidence replay produced:

```text
rtl_todo: gate=pass, open_required_todos=0, static_missing=0
simulation: TESTS=3 PASS=3 FAIL=0
scoreboard: goals=86 required=86 scoreboard_rows=86 goals_with_rows=86
simulation_quality: status=pass, rows=86, issues=0, classes=13
coverage: status=pass
mutation: status=pass, executed=32, killed=16, survived=16, kill_rate=0.5
truth_coverage: status=pass, obligations=95, covered=95, uncovered_required=0
signoff: status=pass, gates=18/18 pass
```

Some adversarial evidence transcripts intentionally include dirty-worktree scans that mention the earlier `mctp_assembler/` directory. Those files are diagnostic logs only, not proof sources. The authoritative scratch evidence roots and diagnostic-only legacy-reference files are listed in `signoff/evidence_authority_manifest.json`.

## Mutation Interpretation

Mutation now runs on a green baseline and produces category kill-rate evidence. `mutation_report.json` is:

```text
status=pass
mode=advisory
executed=32
killed=16
survived=16
kill_rate=0.5
```

Interpretation: the workflow signoff treats mutation as advisory unless threshold enforcement is requested. The 0.5 kill-rate is not a formal correctness proof, but it is useful pressure on monitor quality. Surviving mutants should continue to drive reusable monitor improvements rather than weakening the locked truth.

## Lessons

- For a broad "General IP" flow, static profiles are the wrong abstraction. Obligations must derive from `io_list`, SSOT goals, and `ip_contract.json`.
- Owner routing is more important than a single green headline. Earlier runs had 1 cocotb pass but many scoreboard mismatches; the final signoff only passed after scoreboard rows, coverage, goal audit, and RTL TODO evidence were all clean.
- `rtl_authoring_provenance.json` and `signoff/goal_ledger.json` are not optional paperwork. Missing provenance made signoff fail even though compile/lint passed.
- `rtl_todo_plan.json --audit-rtl` is the canonical RTL evidence gate. Compile/lint clean is necessary but not enough for a generated IP.
- `simulation_quality.json` is the stronger simulation evidence gate. It catches shallow green runs by enforcing required observable presence, scenario-class coverage, no-SRAM-write drop behavior, contiguous SRAM write strobes, readback observability, APB readiness, and interleave context-key observability.
- Mutation should be baseline-gated and interpreted by class. A green mutation status without threshold enforcement is a measurement, not a proof.
- `truth_coverage` must understand general evidence forms instead of IP-specific profiles. The refresh closed MCTP by crediting `cycle_coverage`, register/interrupt scoreboard aliases, real workflow artifacts, and passing static/signoff gates.
- Formal proof remains an optional future workflow. It should be added for small safety invariants after simulation ownership is clean, not used as a substitute for missing stimulus or broken RTL.

## Next Repair Order

1. Raise mutation kill-rate with stronger reusable monitors for handshake-hold, operator, and constant-change classes.
2. Add optional formal checks for small safety invariants such as no descriptor before EOM, no SRAM write on packet drop, and AXI valid/ready hold stability.
3. Keep production claims blocked until external standard conformance, CDC strategy review, synthesis/PnR/PPA, and formal/STA signoff are explicitly added.

Related pages: [[common-ai-agent-map]], [[workflow-ownership-and-boundaries]], [[rtl-gen-ssot-contract]], [[human-review-and-escalation]].
