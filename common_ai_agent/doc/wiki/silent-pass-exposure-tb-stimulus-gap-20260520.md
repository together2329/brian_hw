---
title: Silent Pass Exposure TB Stimulus Gap 2026-05-20
date: 2026-05-20
type: reference
tags: [testbench, scoreboard, stimulus, silent-green, verification]
related: [atlas-new-ip-recipe, atlas-ssot-flag-reference, systematic-quality-gates-20260521]
---

# Silent Pass Exposure TB Stimulus Gap 2026-05-20

Historical context page for the testbench and stimulus gaps that could produce
silent-green results.

## Contract

- A scenario without concrete `stimulus_machine_spec` is not enough evidence for
  cycle-accurate signoff.
- Transactions need explicit `output_rules`; an empty output comparison can make
  a run look green without proving behavior.
- Scoreboard policy should fail hard or produce a visible blocker when required
  comparisons are absent.

## Why It Matters

The May 21 systematic quality gates found cases where missing output rules or
weak stimulus shape made a result ambiguous. The fix is to block early in SSOT
validation and manifest hygiene, then let TB generation consume explicit
stimulus and expected-output structure.

## Related

- [[atlas-new-ip-recipe]]
- [[atlas-ssot-flag-reference]]
- [[systematic-quality-gates-20260521]]
