---
title: Hardcoded Strip Honest Baseline 2026-05-20
date: 2026-05-20
type: reference
tags: [verification, baseline, hardcoded, scoreboard, honesty]
related: [atlas-new-ip-recipe, atlas-ssot-flag-reference, systematic-quality-gates-20260521]
---

# Hardcoded Strip Honest Baseline 2026-05-20

Historical context page for removing hardcoded or pass-shaped assumptions from
the SSOT-to-scoreboard baseline.

## Contract

- Generated checks should be derived from SSOT semantics, not from fixed IP names
  or one-off expected values.
- A passing baseline is only honest when the scoreboard compares explicit
  SSOT-authored outputs, state updates, and cycle expectations.
- If an expected value is missing, the flow should surface a validator blocker or
  human gate instead of silently substituting a default.

## Why It Matters

Hardcoded shortcuts can make a demo pass while hiding whether the SSOT, FL, RTL,
and TB actually agree. The follow-up quality gates in
[[systematic-quality-gates-20260521]] make those missing semantics visible before
simulation signoff.

## Related

- [[atlas-new-ip-recipe]]
- [[atlas-ssot-flag-reference]]
- [[systematic-quality-gates-20260521]]
