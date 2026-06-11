---
name: rocev-evidence-review
description: Review a hardware completion claim against real artifacts. Use when the user asks whether RTL, TB, sim, coverage, VCD, formal, or signoff evidence is enough.
---

# ROCEV Evidence Review

Use this when a claim sounds like "done", "passed", or "good" but the evidence
needs to be checked.

## Review Steps

1. State the Requirement in one sentence.
2. Split it into checkable Obligations.
3. For each Obligation, name the Contract.
4. List fresh Evidence paths and the verdict of each.
5. Make the Validation call.

## Evidence Vocabulary

| Stage | Evidence | What it can close |
|---|---|---|
| req | `req/locked_truth.md`, `req/obligations.json` | Requirement and obligation clarity |
| contract | `req/evidence_plan.json`, `verify/equivalence_goals.json` | How behavior is judged |
| rtl | `rtl/rtl_compile.json`, compile log | RTL exists and compiles |
| lint | `lint/dut_lint.json`, lint log | Structural/style checks |
| tb | TB source, scenario list | Observation exists |
| sim | `sim/results.xml`, sim log | A run executed and passed/failed |
| scoreboard | `sim/scoreboard_events.jsonl` | RTL observed vs expected |
| coverage | `cov/coverage.json`, coverage report | Required cases were exercised |
| waveform | `.vcd`, `.fst`, wave manifest | Debug trace exists |
| formal | `.sva`, proof log, `verify/formal_status.json` | A property was proven |
| signoff | `signoff/truth_coverage.json` | Required bundle is complete |

## Output Rule

Do not write "tests passed" alone. Write:

```text
Simulation evidence exists, scoreboard rows pass, coverage is blocked, so
validation is not closed for the full requirement.
```

