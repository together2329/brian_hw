# RTL-Gen SSOT Contract

## Principle

RTL-gen is the SSOT-to-RTL translation workflow. It reads the current canonical
SSOT as the mandatory reference and implements that contract in RTL.

```text
SSOT contract -> derived RTL todo ledger -> RTL files -> compile/lint/audit evidence
```

## What Must Match

- top module name and public ports
- clock/reset domains and reset policy
- bus, interrupt, inout, debug, and status interfaces
- manifest-owned submodule names and files
- register offsets, fields, resets, access rules, and side effects
- FSM states, transitions, and output actions
- function_model and cycle_model observable behavior
- filelist contents and compile order
- timing/synthesis/lint/DFT/quality-gate constraints
- `workflow_todos.rtl-gen[]` content, detail, criteria, and source refs

## Existing RTL Rule

Existing RTL is evidence, not authority. Reuse it only if it already satisfies
the SSOT contract. If it has generic fixture ports, missing manifest files,
stale filelist entries, or a different hierarchy, the owner is rtl-gen unless a
human chooses to change SSOT.

## When To Escalate To SSOT

Escalate to ssot-gen only when SSOT lacks a required fact or contains a real
contradiction. The escalation must cite an exact YAML path.

Do not escalate just because the current RTL is incomplete or stale.

## Related

- [[full-flow-pipeline]]
- [[golden-todo-evidence]]
- [[workflow-ownership-and-boundaries]]
- [workflow/rtl-gen/RTL_GEN_FLOW.md](../../workflow/rtl-gen/RTL_GEN_FLOW.md)
- [workflow/rtl-gen/rules/ssot-rtl-orchestration.md](../../workflow/rtl-gen/rules/ssot-rtl-orchestration.md)
