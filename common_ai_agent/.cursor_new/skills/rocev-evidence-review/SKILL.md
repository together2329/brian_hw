---
name: rocev-evidence-review
description: Review one hardware task using Requirement -> Obligation -> Contract -> Evidence -> Validation. Use when the user asks whether RTL/TB/sim/formal evidence is enough, or asks why a PASS is trustworthy.
---

# ROCEV Evidence Review

Use this skill to turn a vague "passed" claim into a concrete evidence review.

## Procedure

1. State the Requirement in one sentence.
2. Split it into one or more Obligations.
3. For each Obligation, name the Contract that can judge it.
4. Find fresh Evidence on disk.
5. Decide Validation: closed, not closed, or needs more evidence.

## Evidence checklist

Look for the evidence type that matches the obligation:

| Obligation type | Useful evidence |
|---|---|
| RTL exists / compiles | `rtl/rtl_compile.json`, filelist, compile log |
| RTL style / structure | `lint/dut_lint.json`, lint log |
| TB observes behavior | TB source, scenario list, scoreboard code |
| Simulation ran | `sim/results.xml`, simulator log |
| Expected vs observed | `sim/scoreboard_events.jsonl` |
| Case was exercised | `cov/coverage.json`, coverage report |
| Debug trace exists | `.vcd` / `.fst`, wave manifest |
| Property holds | `.sva`, formal report, `verify/formal_status.json` |
| Signoff bundle closed | `signoff/truth_coverage.json`, signoff report |

## Report template

```text
Requirement:

Obligation:

Contract:

Evidence:
  - path:
    verdict:

Validation:
  closed | not closed | needs more evidence

Gap:
  if not closed, name the missing evidence or weak contract
```

## Agent delegation

For larger work, delegate by role:

- requirement/obligation shape -> `rocev-requirement-agent`
- RTL/lint evidence -> `rocev-rtl-agent`
- TB/sim/coverage/formal evidence -> `rocev-verification-agent`
- final decision -> `rocev-validator-agent`

