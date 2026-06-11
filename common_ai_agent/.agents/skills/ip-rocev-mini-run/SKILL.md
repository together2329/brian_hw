---
name: ip-rocev-mini-run
description: Walk one hardware IP through Requirement, Obligation, Contract, Evidence, and Validation. Use for concise IP evidence demos and seminar examples.
---

# IP ROCEV Mini Run

Use this skill for one IP directory.

## Procedure

1. Read the requirement files under `<ip>/req/`.
2. Identify one requirement and split it into one or two obligations.
3. Name the contract that judges each obligation.
4. Inspect evidence on disk.
5. State validation as closed, not closed, or needs more evidence.

## Evidence To Check

```bash
IP=<ip>
ls -lh "$IP/req/locked_truth.md" "$IP/req/obligations.json" "$IP/req/evidence_plan.json"
ls -lh "$IP/verify/equivalence_goals.json"
ls -lh "$IP/rtl/rtl_compile.json" "$IP/lint/dut_lint.json"
ls -lh "$IP/sim/results.xml" "$IP/sim/scoreboard_events.jsonl"
ls -lh "$IP/cov/coverage.json" "$IP/sim/"*.vcd
ls -lh "$IP/verify/formal_status.json"
```

Missing files are evidence gaps, not failures by themselves.

## Report Shape

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
```

## Local Example

For `pwm_gen_cx1`, do not stop at `sim/results.xml`.

Useful evidence:

- `pwm_gen_cx1/req/locked_truth.md`
- `pwm_gen_cx1/req/obligations.json`
- `pwm_gen_cx1/req/evidence_plan.json`
- `pwm_gen_cx1/verify/equivalence_goals.json`
- `pwm_gen_cx1/rtl/rtl_compile.json`
- `pwm_gen_cx1/lint/dut_lint.json`
- `pwm_gen_cx1/sim/results.xml`
- `pwm_gen_cx1/sim/scoreboard_events.jsonl`
- `pwm_gen_cx1/cov/coverage.json`
- `pwm_gen_cx1/sim/pwm_gen_cx1.vcd`

The important teaching point: compile, lint, sim, and scoreboard evidence can
exist while validation remains open because coverage is blocked.

