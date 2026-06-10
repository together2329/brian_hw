# debounce_cx1 — Locked Truth

**Status**: requirements_locked
**IP**: debounce_cx1
**Description**: Button debouncer with configurable counter threshold (THRESH=4)

## Locked Requirements

| ID | Title | Status |
|----|-------|--------|
| REQ_DEB_STABLE_001 | Stability counter increments on stable input | locked |
| REQ_DEB_BOUNCE_001 | Counter resets on input change | locked |
| REQ_DEB_OUTPUT_001 | db_out updates after THRESH stable cycles | locked |
| REQ_DEB_RESET_001 | Reset clears all state | locked |

## Behavioral Summary

- `db_out` is registered and updates to `btn_in` only after `THRESH=4` consecutive stable cycles.
- The stability counter increments each clock when `btn_in == last_sample`; resets when `btn_in` changes.
- `last_sample` always tracks the most recent `btn_in` value.
- Active-low async reset clears all state (counter, last_sample, db_out) to 0.

## Interface

- Inputs: `clk`, `rst_n`, `btn_in`
- Outputs: `db_out`

## Locked by

Cursor agent simulation exercise. Locked 2026-06-10.
