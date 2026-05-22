---
title: Multi-Cycle Production Wiring 2026-05-20
date: 2026-05-20
type: reference
tags: [cycle-model, cosim, ssot, production, verification]
related: [atlas-new-ip-recipe, atlas-ssot-flag-reference, systematic-quality-gates-20260521]
---

# Multi-Cycle Production Wiring 2026-05-20

Historical context page for the production wiring that made cycle-accurate
FL/RTL co-simulation practical for stateful IPs.

## Contract

- Stateful IPs opt into cycle co-simulation with `cycle_model.cosim: true`.
- State-accumulating scenarios can preserve DUT/CL state across goals with
  `cycle_model.state_accumulating: true`.
- Per-cycle expected values are described through `cycle_model.pipeline[*]` and
  transaction sample timing when an IP needs stage-specific comparison.

## Why It Matters

Single-shot `FunctionalModel.apply()` can miss bugs in counters, FSMs,
backpressure, and pipeline timing. Multi-cycle wiring lets the scoreboard compare
state evolution over time instead of accepting a final-value-only result.

## Related

- [[atlas-new-ip-recipe]]
- [[atlas-ssot-flag-reference]]
- [[systematic-quality-gates-20260521]]
