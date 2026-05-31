---
type: run
tags: [ip-flow, mctp, signoff, mutation, owner-routing]
updated: 2026-05-31
related: [common-ai-agent-map, workflow-ownership-and-boundaries, rtl-gen-ssot-contract, mutation-baseline-2026-05-23, human-review-and-escalation]
---

# MCTP Assembler Scratch Flow - 2026-05-31

This page records the fresh `mctp_assembler_scratch` req-to-audit run. It is a handoff map, not a production conformance claim. The scratch IP reached a complete local evidence bundle, but final local signoff remains `fail` with explicit owner-routed blockers.

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
- Coverage: `mctp_assembler_scratch/cov/`
- Mutation: `mctp_assembler_scratch/mutation/mutation_report.json`
- Signoff: `mctp_assembler_scratch/signoff/ip_signoff.json`
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
python3 workflow/coverage/scripts/ssot_coverage_summary.py mctp_assembler_scratch --root .
python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32
python3 workflow/signoff/scripts/check_ip_signoff.py mctp_assembler_scratch --root .
```

## Current Result

Local signoff result:

```text
status=fail
gates=15
passed=12
failed=3
blocked=0
```

Passing gates include SSOT, IP contract, FL, CL, equivalence goals, RTL provenance, RTL compile, lint, TB Python compile, simulation, mutation guard, and waiver ledger.

Remaining failed gates are owner-routed:

| Gate | Owner | Summary |
| --- | --- | --- |
| `rtl_todo` | `rtl-gen` | 23 open required RTL TODOs, including 19 static-evidence gaps. |
| `scoreboard` | `tb-gen` + `rtl-gen` | 65 FL-vs-RTL mismatches classified: 33 TB stimulus/encoder gaps, 32 RTL bugs. |
| `coverage` | `sim_debug` | Coverage status is `owner_routed`; 57 missing bins are routed to `sim_debug`. |

The important point is not that the IP is green. It is that failure is now explicit, machine-readable, and routed to the right owner workflow instead of being hidden behind a passing cocotb test.

Some adversarial evidence transcripts intentionally include dirty-worktree scans that mention the earlier `mctp_assembler/` directory. Those files are diagnostic logs only, not proof sources. The authoritative scratch evidence roots and diagnostic-only legacy-reference files are listed in `signoff/evidence_authority_manifest.json`.

## Mutation Interpretation

Mutation did not produce a kill-rate for this IP, by design. `mutation_report.json` is:

```text
status=blocked_baseline
mode=baseline_blocked
executed=0
```

Reason: baseline FL-vs-RTL comparison is not green. Running mutation before the scoreboard baseline is correct would create a misleading quality number. This matches [[mutation-baseline-2026-05-23]]: mutation is useful only after the baseline can fail for the right reason and pass for the right implementation.

The report still lists candidate categories and unsupported follow-up categories, so the next green baseline run can immediately convert this into category kill-rate evidence.

## Lessons

- For a broad "General IP" flow, static profiles are the wrong abstraction. Obligations must derive from `io_list`, SSOT goals, and `ip_contract.json`.
- Owner routing is more important than a single green headline. This run has 1 cocotb pass but 65 scoreboard mismatches, proving why signoff must read scoreboard rows, coverage ownership, and goal audit artifacts.
- `rtl_authoring_provenance.json` and `signoff/goal_ledger.json` are not optional paperwork. Missing provenance made signoff fail even though compile/lint passed.
- `rtl_todo_plan.json --audit-rtl` is the canonical RTL evidence gate. Compile/lint clean is necessary but not enough for a generated IP.
- Mutation should be baseline-gated. A blocked mutation report is better than a fake kill-rate when FL-vs-RTL is still red.
- Formal proof remains an optional future workflow. It should be added for small safety invariants after simulation ownership is clean, not used as a substitute for missing stimulus or broken RTL.

## Next Repair Order

1. Run `rtl-gen` on `rtl/rtl_todo_plan.json` until the static audit gate passes.
2. Run `tb-gen` on the 33 TB-owned mismatch routes, then replay sim and scoreboard.
3. Run `rtl-gen` on the 32 RTL-owned mismatch routes, then replay sim and scoreboard.
4. Recompute coverage after scoreboard rows are all green.
5. Run mutation again only after baseline FL-vs-RTL is green.
6. Re-run signoff and keep production claims blocked until the report is `pass`.

Related pages: [[common-ai-agent-map]], [[workflow-ownership-and-boundaries]], [[rtl-gen-ssot-contract]], [[human-review-and-escalation]].
