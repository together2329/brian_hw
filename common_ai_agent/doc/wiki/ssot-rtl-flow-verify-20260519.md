---
title: SSOT RTL Flow Verify 2026-05-19
date: 2026-05-19
type: reference
tags: [atlas, ssot, rtl-gen, verification, db-sync]
related: [flow-fixes-verify-20260519, flow-fixes-r2-verify-20260519, flow-fixes-r3-verify-20260519, rtl-gen-ssot-contract, workflow-ownership-and-boundaries]
---

# SSOT RTL Flow Verify 2026-05-19

Historical cross-link target for the May 19 SSOT-to-RTL product-flow
verification work. The detailed evidence lives in the three flow-fix verification
pages:

- [[flow-fixes-verify-20260519]] - initial live UI verification, 0/5 fixes green.
- [[flow-fixes-r2-verify-20260519]] - cross-workspace follow-up verification.
- [[flow-fixes-r3-verify-20260519]] - real textarea typing verification, 6/7 green.

## Durable Lessons

- Product-flow claims must be validated through the same ATLAS UI/API/worker path
  that users run, not only by headless scripts.
- SSOT seed text must propagate from visible chat into the worker prompt and the
  emitted `yaml/<ip>.ssot.yaml`.
- RTL handoff should dispatch `/ssot-rtl <ip>` and let `rtl-gen` read dynamic
  ledgers from disk; do not preload stale TODO payloads.
- DB identity must converge on one logical workspace/IP row before downstream
  workflow evidence can be trusted as a single run history.

## Current Known Gap

The remaining data-model gap from the R3 verification is workspace identity
canonicalization: the same filesystem workspace can still get multiple
`workspaces.id` values, which lets `ip_blocks` fork by `(workspace_id, ip_name)`.

See [[flow-fixes-r3-verify-20260519]] and [[rtl-gen-ssot-contract]].
