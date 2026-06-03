---
title: Truth Coverage Gate
tags: [ip-flow, ssot, signoff, requirements]
related: [evidence-contract-obligation-traceability, general-ip-flow-trial-and-error-20260601, mctp-assembler-scratch-flow-20260531]
---

# Truth Coverage Gate

`truth_coverage` closes the workflow gap where signoff could pass even though the full locked intent was not proven by executable evidence.

The rule is:

```text
Locked truth can come from req -> SSOT, or directly from SSOT.
Signoff only passes when every required locked-truth obligation has evidence.
```

## Sources

The primary source is always:

```text
<ip>/yaml/<ip>.ssot.yaml
```

A separate requirement document is optional. If a project has a human-authored requirement ledger, it can add:

```text
<ip>/req/requirement_coverage.json
```

Direct SSOT authoring is valid. In that flow, the SSOT itself must carry the obligations through `function_model`, `error_handling`, `registers`, `interrupts`, `test_requirements`, and `workflow_todos`.

## Evidence

The gate reads executable local evidence:

```text
<ip>/sim/scoreboard_events.jsonl
<ip>/cov/coverage.json
<ip>/rtl/rtl_todo_plan.json
<ip>/signoff/ip_signoff.json
```

It does not accept prose-only claims. A scenario, register, interrupt, error condition, function transaction, coverage bin, or acceptance criterion is covered only when matching evidence appears in passing scoreboard rows, hit coverage bins, or passing static/todo gates.

The MCTP signoff refresh added three practical matching rules:

- `function_coverage` and `cycle_coverage` hit bins are both executable coverage evidence.
- Passing scoreboard goals such as `EQ_REGISTER_*` and `EQ_INTERRUPT_*` can satisfy SSOT register/interrupt obligations after normal alias stripping.
- Workflow acceptance criteria are credited only from real artifact or gate evidence, such as `fl_model_check.json`, `fcov_plan.json`, `approval_manifest.json`, passing `rtl_todo_plan.json`, or passing signoff gates. A failing gate does not create its own pass token.

## Commands

Run it before final signoff:

```bash
python3 workflow/reqcov/scripts/check_truth_coverage.py <ip> --root <ip-parent>
python3 workflow/signoff/scripts/check_ip_signoff.py <ip> --root <ip-parent>
```

The output is:

```text
<ip>/signoff/truth_coverage.json
```

Final signoff now requires this report to be present and passing.

## Why This Exists

The MCTP assembler scratch run exposed a workflow failure mode:

```text
requirements/SSOT contained broad intent
generated sim and coverage proved only a subset
signoff aggregated green local artifacts
full requirement satisfaction was still not guaranteed
```

`truth_coverage` makes that gap visible. If a requirement is intentionally out of scope, mark it `optional`, `deferred`, `status: deferred`, or move it behind an explicit human waiver. Otherwise it remains a failing obligation.

## Next Traceability Layer

The current `truth_coverage` implementation is intentionally general. It links
SSOT obligations to evidence through normalized goal, scenario, coverage, and
artifact tokens. That made the MCTP scratch signoff stricter, but it still does
not fully answer this harder question:

```text
Which exact observable and pass condition proves this specific requirement?
```

The proposed next artifact is:

```text
<ip>/verify/evidence_contract.json
```

It should split broad requirements into atomic obligations and connect each one
to required scenarios, required observables, pass conditions, and passing
scoreboard rows.

Future direction:

```text
SSOT
-> ip_contract
-> evidence_contract
-> cocotb monitors / scoreboard rows
-> evidence_contract_coverage
-> truth_coverage
-> signoff
```

See [[evidence-contract-obligation-traceability]] for the proposed schema,
MCTP examples, and staged adoption plan.

## MCTP Refresh Result

The 2026-06-01 `mctp_assembler_scratch` refresh closed the gate without weakening the locked SSOT:

```text
truth_coverage: status=pass, obligations=95, covered=95, uncovered_required=0
ip_signoff: status=pass, gates=18/18
```

The useful lesson is that truth coverage should not demand a special profile per IP. It should map general evidence forms back to SSOT obligations: scoreboard goals, observed RTL keys, function/cycle coverage bins, static RTL gates, and signoff artifacts.
