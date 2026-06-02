# IP Signoff Contract

## Purpose

`AGENTS.md` is for the agent.  It tells Codex and other automation how to behave: autonomy, routing, tool use, progress updates, commit style, and verification discipline.

`IP_SIGNOFF.md` is for the IP.  It defines what counts as truth, what artifacts are editable, which evidence gates must pass, and where human approval is required.

In short:

```text
AGENTS.md
  governs the worker.

IP_SIGNOFF.md
  governs the work product.
```

## Locked Truth

The agent may draft or propose changes to these artifacts, but it must not silently change them to make RTL pass:

- requirement intent and scope
- SSOT behavior, register map, interface contract, and cycle contract
- approved Functional Level golden model semantics
- coverage goals and equivalence goals
- performance, PPA, DFT, timing, and waiver targets
- final signoff policy

Any change to locked truth requires a change request or explicit human approval.

## Agent-Editable Artifacts

The agent may iterate on these artifacts when trying to satisfy locked truth:

- RTL implementation
- cocotb/pyuvm testbench
- simulation harness
- generated reports and local evidence
- provenance refresh artifacts
- localized workflow fixes when a validator exposes a systemic tool/template bug

## Required Local Evidence

For local evidence signoff, all required gates must pass:

```text
SSOT exists and parses.
Per-IP evidence contract exists and was derived from SSOT/IO/goals, not a static profile.
FL artifact check passes.
CL self-check passes.
Equivalence goals exist and have zero blocked goals.
RTL todo/static audit gate passes.
RTL authoring provenance matches the current RTL todo plan.
DUT-only RTL compile passes with zero diagnostics/style violations.
DUT-only lint passes with zero errors, warnings, suppressions, and style violations.
TB Python compile gate passes before simulation.
Simulation passes with at least one executed test.
Scoreboard events exist and compare FL expected values to RTL observed values.
Coverage summary reports pass.
Truth coverage reports pass: every required locked-truth obligation has executable evidence.
Waivers are explicit, sourced, and reviewable.
```

The per-IP evidence contract is:

```text
<ip>/verify/ip_contract.json
```

It records capabilities, required monitors, required mutations, required
observables, and evidence obligations derived from that IP's own artifacts.
The flow must not claim general-IP coverage by selecting a fixed profile such
as "APB", "FIFO", or "AXI"; those are only facts if the IP artifacts imply
them.

The canonical executable gate is:

```text
python3 workflow/reqcov/scripts/check_truth_coverage.py <ip> --root <ip-parent>
python3 workflow/signoff/scripts/check_ip_signoff.py <ip> --root <ip-parent>
```

It writes:

```text
<ip>/signoff/ip_signoff.json
<ip>/signoff/ip_signoff.md
```

## Human-Owned Gates

The agent must ask for human approval, or leave signoff blocked, for:

- requirement or architectural intent changes
- SSOT behavior changes
- FunctionalModel golden semantic changes
- coverage goal changes
- interface contract changes
- timing exception, false path, multicycle path, or clock/reset policy changes
- performance/PPA tradeoffs
- DFT policy changes
- waiver approval for production signoff
- final production signoff

## Waiver Policy

A waiver is valid only when it records:

- stable waiver id
- reason
- source or gate being waived
- approval owner for production signoff

Local experiments may carry explicit waivers without production approval, but production signoff must either approve or remove them.

## Result Language

`pass` means every required local evidence gate passed against locked truth.

`fail` means a machine-checkable artifact is missing, stale, malformed, or failing.

`blocked` means the remaining issue is human-owned, such as an unapproved waiver or missing locked-truth decision.

No agent may claim IP signoff from prose alone.
