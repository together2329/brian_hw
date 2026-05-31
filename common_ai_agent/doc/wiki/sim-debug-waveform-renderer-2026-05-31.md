---
title: Sim Debug Waveform Renderer
category: decision
tags:
  - atlas
  - sim-debug
  - waveform
  - frontend
  - performance
updated: 2026-05-31 KST
---

# Sim Debug Waveform Renderer

Decision: keep the current React DOM plus per-row SVG renderer for now. The
current perceived speed is acceptable, and the UI still benefits from simple
React-controlled rows, context menus, selection, grouping, and source/wave
cross-highlighting.

## Current Renderer

The waveform viewer is not React Flow and not Canvas.

Current shape:

```text
React UI
  WaveBand
    row containers and context menu in DOM
    TimeRuler / cursors as DOM overlays
    WaveRow per signal
      SVG path for scalar signals
      SVG polygon + text for bus segments
```

The renderer maps time to pixels directly:

```text
x = ((time - visibleStart) / visibleSpan) * plotWidth
```

That same mapping drives scalar paths, bus segment polygons, cursor positions,
drag-to-zoom, and click-to-time behavior.

## Why Not React Flow

React Flow is a graph node/edge engine. The waveform viewer is not a graph:
it is an ordered signal table with a time-domain plot. Using React Flow would
add graph viewport and node abstractions that do not match waveform-specific
hit testing, radix display, grouped rows, or VCD time clipping.

## Future Canvas Path

If waveform performance becomes a real issue with larger VCDs, the preferred
next architecture is a hybrid renderer, not an all-Canvas UI:

```text
DOM / React
  signal name column
  value column
  selection state
  context menu
  keyboard and resize interactions

Canvas
  grid
  scalar wave lines
  bus segment flags and text
```

The important performance features are:

- Row virtualization: render only visible rows plus overscan.
- Time-window clipping: binary-search each trace and draw only samples around
  the current visible time range.

Canvas only pays off when paired with those two constraints. Without them, it
can still waste time drawing off-screen rows or off-window samples.

## Migration Trigger

Do not rewrite the renderer just because Canvas is theoretically faster.
Consider a Canvas/hybrid migration when one of these becomes true:

- The viewer needs hundreds or thousands of visible/pinned signals.
- Bus segment counts create too many SVG nodes.
- Zoom/pan interaction stutters on realistic project VCDs.
- Context menu, selection, or cursor updates become visibly delayed.

Until then, the current SVG renderer is acceptable and easier to evolve.

## Slice Handling Note

Pinned bit slices such as `irq_status_o[5:0]` and `irq_status_o[31:6]` must be
separate waveform rows and must render sliced values, not the original
`[31:0]` value. VCD bus values may arrive as short binary strings, so slice
logic must zero-extend to the declared bus width before extracting upper bits.
