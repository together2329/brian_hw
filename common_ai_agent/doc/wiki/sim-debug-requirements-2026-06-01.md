---
title: Sim Debug Requirements Ledger
type: reference
tags:
  - atlas
  - sim-debug
  - requirements
  - deep-test
  - waveform
  - rtl
  - vcd
  - pyslang
updated: 2026-06-01 KST
related:
  - sim-debug-feature-review-2026-05-31
  - sim-debug-module-signals-2026-05-30
  - sim-debug-agent-tool-2026-05-31
  - sim-debug-waveform-renderer-2026-05-31
---

# Sim Debug Requirements Ledger 2026-06-01

This page consolidates the user-raised Sim Debug requirements from the
2026-05-30 to 2026-06-01 iteration. It is the product/UX ledger; implementation
details remain in [[sim-debug-feature-review-2026-05-31]],
[[sim-debug-module-signals-2026-05-30]],
[[sim-debug-agent-tool-2026-05-31]], and
[[sim-debug-waveform-renderer-2026-05-31]].

## Product Surface

Sim Debug is expected to feel like one debugger with four coordinated panes:

1. RTL instance hierarchy.
2. RTL source.
3. RTL/VCD signal list.
4. Waveform viewer.

The user expectation is that these panes load as a coherent debugging surface,
not as disconnected widgets that partially populate and force repeated waiting.

## Requirement Ledger

| ID | Area | Requirement | Acceptance criteria | Status |
|---|---|---|---|---|
| SDR-001 | Loading | First Debug loading should be clear and non-fragmented. | Show a centered loading state while hierarchy/source/VCD/signal metadata prepare, then reveal the ready surface together. Avoid leaving a mostly blank waveform/source pane as the main visual state. | Open |
| SDR-002 | Loading | Once Sim Debug has loaded, keep it warm. | Switching away and back to Debug should reuse mounted/cached state instead of redoing expensive VCD/hierarchy/source loading. | Implemented/verify |
| SDR-003 | Loading | Preload when the sim-debug workflow is active. | When the workflow or Debug tab becomes relevant, run safe background preparation so the first visible click is faster. Hidden preloading must not trigger keyboard shortcuts or UI intents. | Implemented/verify |
| SDR-004 | Signal list | The signal pane should show useful signals by default. | On first Debug view, default to available VCD signals; selecting a hierarchy module can switch to RTL module signals. | Implemented/verify |
| SDR-005 | Signal list | Signal rows should display Verilog-style ranges. | Buses appear as `name[31:0]`, `name[5:0]`, etc., with direction and width visible where available. | Implemented/verify |
| SDR-006 | Source | Clicking a signal in RTL source should highlight exactly that signal. | A selected source signal is visibly highlighted and threaded into the same selection model used by Ctrl+W/add-to-wave. | Implemented/verify |
| SDR-007 | Source | Source selection must preserve bit slices. | Selecting `irq_status_o[5:0]` adds/highlights that slice, not only the full `irq_status_o[31:0]` bus. | Implemented/verify |
| SDR-008 | Source | Source multi-select should be semantic, not arbitrary text dimming. | Drag selection selects Verilog identifiers/ranges only. Native-looking large dim rectangles are avoided in normal source-drag selection. | Implemented/verify |
| SDR-009 | Source | Ignore comments and numeric literals during source selection. | Comment words such as `payload` and numeric literal suffixes such as `4'd0` / `4'hf` are not highlighted or added as signals. | Implemented/verify |
| SDR-010 | Source | Source context menu must include waveform loading. | Right-click on a source signal offers Add/Load to waveform plus trace/navigation actions. | Implemented/verify |
| SDR-011 | Source/signals | Multi-select should work consistently. | Ctrl/Cmd click toggles, Shift click range-selects, and Ctrl+W adds all selected source or signal rows to waveform. | Implemented/verify |
| SDR-012 | Waveform | Waveform row multi-select delete should be bulk. | Selecting multiple waveform rows and pressing Delete/Backspace or header `delete` removes all selected rows at once. | Implemented/verify |
| SDR-013 | Waveform | Waveform rows and groups should reorder by drag/drop. | Dragging a signal row in the label/value zone reorders that row; dragging a group header moves the group block; plot-zone drag remains cursor/zoom. | Needs browser E2E |
| SDR-014 | Waveform | Bus slices must be true sliced traces. | `irq_status_o[5:0]`, `irq_status_o[31:6]`, and `irq_status_o[31:0]` render distinct sliced values. Upper slices do not show a change only because lower bits changed. | Implemented/verify |
| SDR-015 | Waveform | Radix selection should match color selection ergonomics. | Each row can choose HEX/DEC/BIN/PARAM from the row menu, and display updates without changing signal identity. | Implemented/verify |
| SDR-016 | Waveform | FSM-like signals should display parameter names by default when possible. | If a `parameter` or `localparam` value map is available for a state/FSM-like bus, waveform display can show labels such as `IDLE` or `ERROR` instead of raw numbers. | Implemented/verify |
| SDR-017 | Waveform | RC save/restore should persist the debugging layout. | Save and restore files such as `signal.rc` or `feature.rc` under `<ip>/sim/`. Persist selected signals, order, slices, groups, colors, radix, cursors, time unit, and view range. | Implemented/verify |
| SDR-018 | Waveform | Time resolution should be user-selectable. | Viewer supports auto/fs/ps/ns/us/ms/s display resolution for ruler, cursors, and view controls. | Implemented/verify |
| SDR-019 | Waveform | Cursor A/B delta should be useful. | Show A-B interval in the selected time unit and convert it to frequency when valid. | Implemented/verify |
| SDR-020 | Waveform | Missing dumped signals must be explicit. | If an RTL signal exists but is not dumped into the selected VCD, keep a visible `not in VCD` row instead of silently dropping or remapping it. | Implemented/verify |
| SDR-021 | Tool call | Tool-call signal lookup should be stricter than leaf-name guessing. | Check VCD signals and pyslang-elaborated RTL pins before returning `not in VCD`; resolve unique scoped/leaf matches, but fail visibly on ambiguity. | Implemented/verify |
| SDR-022 | Tool call | Common names such as `clk`, `rst`, and `irq` must resolve in the current instance scope. | Source/signal/tool paths preserve instance scope so common leaf names add the correct VCD row. | Implemented/verify |
| SDR-023 | Tool call | Single-bit signals must add from source and signal list. | A unique single-bit leaf such as `parse_done` can resolve even when the RTL module scope and VCD instance path differ by parent prefixes. | Implemented/verify |
| SDR-024 | Trace | Trace must support multiple drivers and multiple loads/sinks. | Trace popover and tool result show all drivers and loads/sinks with file/line context; UI must not collapse drivers to one item. | Implemented/verify |
| SDR-025 | Trace | pyslang is the semantic authority. | Use pyslang/elaboration for hierarchy, ports, internals, driver/load trace, and pin-existence checks; static text fallback is allowed only as degraded continuity. | Implemented/verify |
| SDR-026 | Waveform | The left value column should follow cursor A. | Each waveform row's value cell samples the trace at cursor A, not at the final VCD sample, so moving A updates the visible value column in lockstep. | Implemented/verify |
| SDR-026 | Renderer | The waveform renderer should stay simple until profiling proves otherwise. | Current React DOM plus per-row SVG is acceptable. Do not migrate to React Flow. Consider hybrid Canvas only with row virtualization and time-window sample clipping. | Decision recorded |
| SDR-027 | Verification | Validate the whole IP flow, not only isolated widgets. | For broad regressions, exercise one IP through SSOT, FL model, RTL, TB generation, Sim Debug, and lint, then record evidence. | Evidence recorded |

## Signal Identity Contract

A Sim Debug signal is identified by all of these fields:

```text
scope + name + optional range/slice
```

Dropping any part of that identity causes the regressions the user called out:

- `clk`, `rst`, or `irq` can bind to the wrong instance.
- `parse_done` can be reported as `not in VCD` even when a unique VCD leaf
  exists under a prefixed instance path.
- `irq_status_o[31:6]` can appear to change when only `irq_status_o[5:0]`
  changed.
- RC restore can silently remap a row to a same-name signal from another scope.

Therefore all add paths must preserve signal identity: hierarchy row, RTL signal
list, VCD signal list, source click, source drag, Ctrl+W, context menu, agent
tool call, RC restore, reorder, group, and delete.

## Source Interaction Contract

Normal source interaction is semantic:

- single click focuses one identifier or exact bus slice;
- drag selection collects Verilog signal identifiers/ranges only;
- Ctrl/Cmd and Shift compose multi-selection;
- Ctrl+W adds the selected source/signal set to waveform;
- right click offers Add/Load to waveform, Trace, Go driver, and Go first load;
- comments and numeric literal fragments are not selectable signal tokens.

Native text selection can exist as an escape hatch, but it should not be the
default debugging gesture.

## Waveform Interaction Contract

Waveform row selection is separate from source/signal selection. Selecting rows
already in the waveform is for waveform operations: delete, reorder, group,
color, radix, collapse, and restore. Selecting source or signal-list rows is for
adding signals to the waveform.

The expected waveform controls are:

- bulk delete for selected rows;
- row and group drag/drop reorder;
- per-row color and radix;
- parameter/FSM label display when maps are available;
- exact bus slices as independent rows;
- A/B cursor delta and frequency;
- time resolution selector;
- RC save/restore for reusable debug setups.

## Tool Call Contract

The `sim_debug` tool should behave like a careful debugger assistant:

- Use VCD as the authority for dumped waveform data.
- Use pyslang/elaboration as the authority for RTL pin existence, hierarchy,
  ports, internals, and driver/load trace.
- Resolve unique matches across common RTL/VCD scope-prefix differences.
- Return ambiguity with candidates instead of guessing.
- Return `rtl_not_dumped` / visible `not in VCD` only after proving the RTL
  signal exists but is absent from the VCD.
- Push UI intent for show/add/goto/cursor/trace/find/value so the visible viewer
  follows the tool result.

## Performance Direction

Current speed is acceptable, but the loading UX should not feel unstable. The
priority order is:

1. keep the mounted state warm after first load;
2. background-preload safe data when Sim Debug is likely to be used;
3. avoid eager full-module signal elaboration on initial load;
4. profile before renderer rewrites;
5. if large VCDs become slow, add row virtualization and time-window clipping;
6. consider hybrid Canvas only after those two constraints are part of the
   renderer plan.

React Flow remains the wrong abstraction because waveform viewing is an ordered
signal table plus time-domain plot, not a node/edge graph.

## Validation Snapshot

## Deep Test Coverage Matrix

| Requirement focus | Deep test evidence |
|---|---|
| Source selection, scoped VCD lookup, exact slices, PARAM radix, reorder/group, time controls | `frontend/atlas/__tests__/sim-debug-requirements-deep.test.tsx` |
| Requirement-class simulation quality gate (`memory_pack`, `drop`, `readback`, `register`, `multi_assemble`) | `tests/test_simulation_quality_gate.py` |

The matrix above is the requirements-to-tests contract for this ledger page.

## Requirement-Level Deep Evidence

| Requirement IDs | Deep assertion | Evidence |
|---|---|---|
| SDR-007, SDR-014 | Exact selected bit slices remain independent from the full VCD bus and from other slices; single-bit slices stay scalar. | `frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx` |
| SDR-020, SDR-021, SDR-022, SDR-023 | VCD lookup preserves scope, resolves unique RTL/VCD prefix differences, and marks missing or ambiguous rows visibly, including ranged missing-bus placeholders. | `frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx` |
| SDR-008, SDR-009 | Source drag/token selection collects Verilog identifiers/ranges and ignores comments, numeric literal fragments, and declaration-width syntax. | `frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx` |
| SDR-015, SDR-016 | Parameter/localparam maps drive PARAM radix display for FSM-like waveform rows. | `frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx` |
| SDR-013 | Grouped waveform rows remain contiguous, group-block reorder preserves membership, drag preview anchors near the pointer, and plot-zone drag does not reorder rows. Browser drag/drop still needs visible E2E. | `frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx`, `frontend/atlas/__tests__/sim-debug-requirements-waveband.test.tsx` |
| SDR-018, SDR-019 | Time-unit selection, cursor A/B delta, derived frequency, and command-driven cursor/zoom input are stable. | `frontend/atlas/__tests__/sim-debug-requirements-signals.test.tsx` |
| SDR-011, SDR-012 | Waveform row selection stays below the sticky header and bulk delete passes all selected rows. | `frontend/atlas/__tests__/sim-debug-requirements-waveband.test.tsx` |
| SDR-017 | RC save/restore controls preserve user-facing rc filenames and invoke the save/restore hooks. | `frontend/atlas/__tests__/sim-debug-requirements-waveband.test.tsx` |
| SDR-027 | Simulation quality rejects shallow rows and requires requirement-class evidence for memory pack, drop, readback, register, and multi-assemble flows. | `tests/test_simulation_quality_gate.py` |

Requirements not listed in this table are either product-loading/browser-flow
items, already covered by earlier focused tests referenced in the validation
snapshot, or recorded as follow-up where browser E2E is still required.

Recent Sim Debug-focused verification evidence:

```text
cd frontend/atlas
npm test -- \
  __tests__/sim-debug-source-viewer.test.tsx \
  __tests__/sim-debug-ctrlw-add.test.tsx \
  __tests__/sim-debug-vcd-scope-annotation.test.jsx \
  __tests__/wave-edge-click.test.jsx
npm run build
git diff --check
```

Latest local result for the focused frontend set: 4 files, 33 tests passed;
Vite build passed with existing bundle-size/vendor-script warnings.

Recent broad product-flow evidence from the same iteration used a scratch IP
through SSOT, FL model, RTL, TB generation, Sim Debug, and lint. Keep using this
style of real flow validation for high-risk Sim Debug regressions, because the
user-facing contract spans UI, API, worker intent, VCD data, and pyslang.

## Open Follow-Up

- Add real browser/Computer Use coverage for waveform row and group drag/drop.
- Add a small performance probe for VCD size, parse time, signal count, sample
  segment count, and render/update time.
- Make RC restore summarize unresolved rows against the currently selected VCD.
- Consider browser-session scoping for the latest-intent file channel before
  multi-user or multi-tab Sim Debug becomes a product target.
- Keep future Sim Debug wiki updates in `doc/wiki`, not `.omx` or `omx/wiki`.
