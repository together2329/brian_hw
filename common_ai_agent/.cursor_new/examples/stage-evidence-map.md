# Stage Evidence Map

This is a compact reference for explaining evidence during the seminar.

Source references:

- `.cursor/workflow/COMMON_ENGINE_FLOW.md`
- `.cursor/workflow/wiki/ip_knowledge/sim.md`
- `.cursor/workflow/wiki/ip_knowledge/coverage.md`
- `doc/wiki/req-obligation-contract-evidence-validation.md`
- `doc/wiki/evidence-contract-obligation-traceability.md`
- `doc/wiki/formal-verification-evidence.md`

## The Short Version

```text
Requirement says what we want.
Obligation makes it checkable.
Contract says how to judge it.
Evidence is the artifact.
Validation is the decision.
```

## Stage Map

| Stage | Owns | Typical evidence | Validation question |
|---|---|---|---|
| req | requirement and obligation authority | `req/requirements_index.json`, `req/obligations.json`, `req/evidence_plan.json`, `req/locked_truth.md` | Is the requirement decomposed into checkable obligations? |
| rtl | implementation and DUT-only quality | `rtl/*.sv`, `rtl/rtl_compile.json`, `rtl/rtl_traceability.json` | Does RTL implement the contract and compile? |
| lint | structural cleanliness | `lint/dut_lint.json`, lint log | Are blocking lint/style issues absent? |
| tb | observation and stimulus | `tb/cocotb/*`, scoreboard, scenario list, TB manifest | Does the TB observe each obligation? |
| sim | executed behavior | `sim/results.xml`, `sim/sim_report.txt` | Did the simulation run and avoid failures? |
| scoreboard | expected vs observed | `sim/scoreboard_events.jsonl` | Did RTL observed values match expected values? |
| coverage | exercised cases | `cov/coverage.json`, coverage reports | Were required bins/goals actually hit by passing evidence? |
| waveform | debug trace | `sim/*.vcd`, `.fst`, waveform manifest | Can we inspect the cycle-level cause? |
| formal | all-state property proof | `.sva`, proof log, `verify/formal_status.json` | Was the specific property proven without vacuity? |
| signoff | bundle closure | `signoff/truth_coverage.json`, signoff report | Is the whole evidence bundle complete and fresh? |

## PASS Is Not One Thing

Use this when explaining why a single "PASS" is weak:

```text
RTL compile PASS
  The RTL parses/elaborates under the configured tool.

Lint PASS
  The RTL has no blocking style/structural diagnostics.

Simulation PASS
  The test that ran did not fail.

Scoreboard PASS
  RTL observed values matched expected/model values for that row.

Coverage PASS
  Required cases/bins were exercised by passing evidence.

Formal PASS
  A specific property was proven under recorded assumptions.

Signoff PASS
  The required evidence bundle is complete and fresh.
```

## Completion Report Template

```text
Requirement:

Obligation:

Contract:

Evidence:
  - path:
    verdict:
    what it proves:

Validation:
  closed | not closed | needs more evidence

Gap:
  if not closed, name the missing evidence or weak contract
```

