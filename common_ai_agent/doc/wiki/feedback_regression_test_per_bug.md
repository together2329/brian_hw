---
type: rule
tags: [testing, regression]
updated: 2026-05-31
related: [testing-methodology]
---

# Feedback Regression Test Per Bug

Every confirmed bug class should leave behind the smallest regression test that would have failed before the fix. Pick the layer that owns the failure: unit, workflow script, API, UI/E2E, or real worker smoke.

