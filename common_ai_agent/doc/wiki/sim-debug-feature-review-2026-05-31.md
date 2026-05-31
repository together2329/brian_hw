---
title: Sim Debug Feature Review
type: reference
tags:
  - atlas
  - sim-debug
  - rtl
  - waveform
  - vcd
  - pyslang
updated: 2026-05-31 KST
related:
  - sim-debug-module-signals-2026-05-30
  - sim-debug-agent-tool-2026-05-31
  - sim-debug-waveform-renderer-2026-05-31
---

# Sim Debug Feature Review 2026-05-31

Consolidated review of the Sim Debug feature as implemented across the Atlas
frontend, backend API, pyslang elaboration layer, VCD tooling, agent tool bridge,
and tests. This page is the current high-level operating map; the narrower
implementation notes remain in [[sim-debug-module-signals-2026-05-30]],
[[sim-debug-agent-tool-2026-05-31]], and
[[sim-debug-waveform-renderer-2026-05-31]].

## Review Findings

- **No release-blocking issue was found in the reviewed Sim Debug surfaces.**
  The recent regressions around source selection, Ctrl+W add, scoped common
  pins (`clk`, `rst`, `irq`), bus slicing, row delete, and waveform row reorder
  have targeted frontend tests.
- **Signal identity is the main hard contract.** A selected signal is not just
  `name`; it is `scope + name + optional bit/range`. Any code path that drops
  `scope` will regress module ports with common leaf names and will cause
  `not in VCD`, ambiguous leaf resolution, or wrong-instance waveform rows.
- **Ambiguous tool calls should fail visibly rather than guess.** Leaf-only
  `sim_debug(show/add)` requests are resolved only when unique. If the same leaf
  exists in multiple VCD scopes, the tool/UI should require `scope` or a full VCD
  path. This is correct behavior, not a bug.
- **The waveform renderer is still React DOM plus per-row SVG.** It is not
  React Flow and not Canvas. It is acceptable for the current UI, but it does not
  yet implement row virtualization or time-window sample clipping.
- **The loading path is improved by background preload and lazy signal
  elaboration, but not eliminated.** VCD parsing and hierarchy fetches still
  cost real time. Module signal elaboration stays lazy so opening the tab does
  not immediately elaborate every signal list.
- **The agent-to-UI intent channel is latest-only and per IP.** It is simple and
  robust for one active user/session, but not strictly browser-session scoped.
  Multi-tab or multi-user flows can race if they operate on the same IP.
- **RC save/restore is per IP, not per VCD.** Restoring an RC made for a
  different VCD can intentionally produce `not in VCD` rows. That is safer than
  silently remapping to the wrong signal, but the UI contract should stay clear.
- **pyslang is the semantic authority, static fallback is a degraded mode.**
  Fallback keeps the UI populated when pyslang APIs drift or fail, but it is not
  equivalent to elaborated symbol resolution.
- **Browser gesture coverage still has one gap.** Pure reorder logic and source
  selection logic are unit-tested, but full browser drag/drop gesture E2E is not
  yet covered.

## Feature Surface Inventory

Sim Debug is a four-surface debugger:

1. **RTL instance hierarchy** - left upper pane. Shows elaborated instance tree,
   top resolution, and module/file mapping.
2. **RTL source** - center upper band. Shows selected module source, source-line
   annotations, signal highlighting, driver/load jumps, and source-origin signal
   selection.
3. **RTL/VCD signal list** - left lower pane. Lists module ports/internal nets
   from pyslang or VCD signals, supports filtering/search/multi-select, and adds
   signals to the waveform.
4. **Waveform viewer** - bottom band. Shows VCD traces, pinned RTL signals,
   groups, colors, radix/FSM display, cursors, zoom/pan, RC save/restore, and
   row reorder/delete.

The main frontend entrypoint is `frontend/atlas/sim-debug.tsx`. Supporting
surface files:

- `frontend/atlas/sim-debug-panels-side.tsx` - hierarchy panel and RTL/VCD
  signal list.
- `frontend/atlas/sim-debug-panels.tsx` - source viewer and source interaction.
- `frontend/atlas/sim-debug-wave.tsx` - waveform UI, row selection, reorder,
  groups, context menu, RC/time controls.
- `frontend/atlas/sim-debug-helpers.tsx` - pure signal matching, slicing, time,
  command, group/order, search, and formatting helpers.
- `frontend/atlas/debug-shared.tsx` - waveform drawing primitives.
- `frontend/atlas/vcd-parser.js` - browser-side VCD parser used by the wave UI.

## Loading And Preload Contract

`SimDebug` accepts `active` and `preload`. Internally:

```text
dataActive = active || preload
```

Data fetches use `dataActive`, while keyboard shortcuts and file-intent polling
remain tied to `active`. This allows the Debug tab to start preparing in the
background when the sim-debug workflow is selected, while avoiding hidden-tab
shortcuts or hidden-tab intent side effects.

The workspace keeps Sim Debug mounted after the user visits Debug or when
`showDebugTab` is true:

```text
workspace-root.tsx
  mount SimDebug persistently after debugVisitedRef or showDebugTab
  hide inactive instance with display:none
  pass preload={showDebugTab}
```

Important loading choices:

- VCD list is fetched from `/api/vcd/list?ip=<ip>`.
- VCD raw content is fetched from `/api/vcd/raw?path=...` and parsed in the
  browser by `window.parseVCD`.
- Hierarchy is fetched from `/api/hierarchy?top=&ip=`.
- Source auto-load selects the top module, but passes `{ loadSignals: false }`
  so the first tab open does not also trigger module signal elaboration.
- Module signals are fetched only when the user selects a module or needs that
  module signal list.

This is why background preload improves perceived speed but does not make first
loading free: raw VCD read/parse and hierarchy construction remain real work.

## Data Flow

High-level flow:

```text
IP selection
  -> VCD list
  -> active VCD raw
  -> browser VCD parse
  -> infer VCD scope / time range / default traces
  -> resolve RTL top
  -> hierarchy API
  -> module source load
  -> optional module signal API
  -> user or tool pins signals
  -> resolve pinned signal against VCD
  -> render waveform row
```

Backend routes:

- `src/atlas_api_vcd.py`
  - `/api/vcd/list` - recursively finds `.vcd` under the active IP, sorted by
    mtime.
  - `/api/vcd/raw` - safe VCD read, byte-capped, UTF-8 replace mode.
  - `/api/vcd/rc/list`, `/api/vcd/rc/load`, `/api/vcd/rc/save` - per-IP
    waveform layout RC files under `<ip>/sim/*.rc`.
- `src/atlas_api_sim_debug.py`
  - `/api/debug/scenarios` - SSOT scenarios plus scoreboard rollup.
  - `/api/elab/status` - pyslang/verilator/slang availability.
  - `/api/hierarchy` - elaborated instance tree and module file mapping.
  - `/api/trace` - driver/load tracing for a signal.
  - `/api/module/signals` - module ports/internal signals with direction, type,
    width, line, and `instance_path`.
  - `/api/sim_debug/intent` - latest agent-pushed UI intent.
  - `/api/cocotb` - TB/cocotb tree and results summary.

Shared source and top resolution:

- `src/sim_debug_sources.py` resolves source lists. It prefers
  `<ip>/list/*.f`, then `<ip>/rtl/*`, follows nested `-f` includes, clips to the
  project root, and skips build/vendor-like directories.
- `src/atlas_sim_debug_top.py` resolves the real top. Precedence is explicit
  non-IP top, TB manifest, SSOT `top_module`, first non-dump VCD scope, then
  requested/IP fallback. Dump helper scopes such as `atlas_iverilog_vcd_dump`
  are ignored as design tops.

## Signal Identity And Resolution

The UI uses these concepts:

- `name`: leaf or range-bearing signal name, for example `irq_status_o[5:0]`.
- `scope`: RTL/VCD instance path, for example
  `NEWIP_MCTP.u_packet_engine`.
- `range`: optional bus slice from the requested name.
- `selKey`: UI selection key, typically `scope::range-stripped-name`.
- `waveSignalKey`: waveform row identity, preserving scope and slice.

The critical helper is `resolvePinnedWaveSignal` in
`frontend/atlas/sim-debug-helpers.tsx`. It resolves in this order:

1. exact name/scope match through `waveSignalMatches`;
2. scoped suffix match when the requested scope omits testbench/top prefixes;
3. unique suffix match for dotted names missing the top prefix;
4. unique leaf-only fallback as the final option.

If a leaf-only request is ambiguous, it stays unresolved and renders as a
visible `not in VCD` row. This avoids showing a real but wrong signal.

The server-side `core/sim_debug_analyze.py::resolve_wave_signal` follows the
same philosophy for tool calls:

- VCD is authoritative when a unique VCD signal exists.
- pyslang hierarchy/module signals are used to prove that an RTL pin exists and
  to map module-style requests to VCD scopes.
- Proven RTL-but-undumped signals return `rtl_not_dumped`.
- Ambiguous signals return `ambiguous` with candidates, not a guessed row.

## Source Viewer Contract

The source viewer supports signal picking directly from RTL:

- single click - focus the exact identifier or bit slice;
- double click - add to waveform;
- right click - Add, Trace driver/loads, Go driver, Go first load;
- plain drag - semantic multi-signal selection for bulk add;
- Alt-drag - native text selection escape hatch.

Important implementation details:

- `signalAtPoint` uses browser caret APIs and preserves bit/range suffixes, so
  clicking `irq_status_o[5:0]` selects that slice instead of only
  `irq_status_o[31:0]`.
- `sourceSignalsBetween` turns a drag range into unique Verilog identifiers.
- Native text selection is cleared after source context-menu capture to prevent
  accidental dimmed source blocks.
- Source selected signals are threaded to root `waveSel`, so `Ctrl+W` adds them
  the same way signal-panel selection does.
- Source scope is applied only when the loaded source belongs to the currently
  selected module signal list. This prevents blindly assigning an unrelated
  scope to generic source text.

## RTL/VCD Signal List Contract

The left-bottom signal pane has two modes:

- `RTL`: module signal list from `/api/module/signals`.
- `VCD`: parsed VCD signal list.

Interaction contract:

- `Ctrl`/`Cmd` click toggles multi-select.
- `Shift` click range-selects.
- macOS `Ctrl+click` is prevented from becoming a native context menu path.
- `Ctrl+W` adds current `waveSel` to the waveform.
- Right-click on one row offers Add, Trace, Go driver, Go first load.
- Right-click on a multi-selected row offers bulk add.
- RTL rows preserve `moduleSignalsScope`, which is why common pins like `clk`,
  `rst`, and `irq` add to the correct VCD instance.
- Buses display as `name[width-1:0]`; VCD rows display the VCD range.

The old unsafe behavior was leaf-only pinning. The current safe behavior is
scope-preserving pinning.

## Waveform Viewer Contract

The waveform viewer owns a separate row-selection state from the signal pane:

- `waveSel`: selected source/RTL/VCD signals ready to add.
- `waveRowSel`: selected waveform rows ready to delete/reorder/group.

This separation is intentional. Selecting rows already in the waveform should
not mutate the source/signal-pane selection.

User features:

- Delete selected waveform rows with the header `delete` button or
  Delete/Backspace.
- Drag signal rows from the label/value zone to reorder.
- Drag group headers to move a whole contiguous group block.
- Dragging the plot zone remains cursor/zoom interaction, not reorder.
- Right-click a row for color, radix, delete, move, and group actions.
- Right-click a group for color, rename, collapse/expand.
- `HEX`, `DEC`, `BIN`, and `PARAM` radix are available from the row menu.
- State-like buses can display parameter/localparam labels when a map is found.
- Cursors A/B show delta and frequency.
- Time display resolution supports auto/fs/ps/ns/us/ms/s.
- The command input handles cursor and zoom phrases such as
  `a 5000 b 15000`, `zoom 1000 8000`, `a..b`, and `fit`.
- RC save/restore stores the current waveform layout envelope as
  `<ip>/sim/<name>.rc`.

## Waveform Rendering

Current renderer:

```text
React DOM
  all rendered rows, labels, value column, controls, menus
SVG per rendered row
  scalar wave path
  bus segment polygons and segment text
DOM overlays
  time ruler, cursor strip, cursor labels, drag zoom box
```

It is not React Flow. React Flow is for node/edge graphs, while this viewer is
an ordered table plus time-domain plot. React Flow would add graph abstractions
without solving VCD sample clipping, signal row selection, radix formatting, or
cursor hit testing.

It is also not Canvas yet. A future Canvas migration should be hybrid:

- React/DOM for controls, name/value columns, row selection, menus, grouping.
- Canvas for grid, scalar traces, bus flags, and text.

Canvas only becomes worth it with both:

- row virtualization - render only visible rows plus overscan;
- time-window clipping - binary-search each trace and draw only samples around
  the current zoom range.

Without those two constraints, Canvas can still waste work drawing off-screen
rows or off-window samples. Current speed is acceptable, so the correct trigger
is measured stutter on real large VCDs, not theoretical renderer preference.

## Bus Slice Contract

Pinned slices such as `irq_status_o[5:0]`, `irq_status_o[31:6]`, and
`irq_status_o[31:0]` must behave as separate rows with separate compacted trace
values.

`applyPinnedRange` handles this:

- parse requested slice from the pinned name;
- zero-extend short VCD bus strings to the declared width;
- extract the requested slice;
- compact only after slicing.

This prevents `[31:6]` from looking changed only because `[5:0]` changed.

## FSM And Parameter Display

`parseVerilogParamValueMap` extracts simple numeric `parameter` and `localparam`
labels from loaded source. The waveform row chooses a parameter label map when:

- the user selects `PARAM` in the row radix menu;
- or the row is state-like (`state`/`fsm`) and a parameter map is available.

This is deliberately lightweight. It is useful for common FSM encodings, but it
does not replace full enum/type elaboration.

## Agent Tool Contract

The agent tool is `sim_debug` in `core/tools.py`, with schema in
`core/tool_schema.py`.

Actions:

- `show` / `add` - resolve and add waveform signals.
- `goto` / `zoom` / `view` - set visible time range.
- `cursor` - set cursor A/B.
- `fit` - full VCD range.
- `reorder` - set row ordering.
- `group` / `ungroup` - tag rows into foldable groups.
- `color` - set row color.
- `fold` / `unfold` - collapse or expand group.
- `trace` - pyslang driver/load trace.
- `find` - find a signal edge and push a goto intent.
- `value` - read value at a time and push cursor/show intent.

Tool-to-UI bridge:

```text
core.tools.sim_debug
  -> core.sim_debug_analyze / core.vcd_timeline / workflow.sim_debug.elab
  -> core.sim_debug_intent.push_intent(...)
  -> .session/sim_debug_intent.json
  -> /api/sim_debug/intent?ip=<ip>
  -> frontend useSimDebugIntent polling while active
  -> SimDebug state mutation
```

The intent file stores only the latest action, with a monotonic `seq`. This is
simple and avoids worker-process memory coupling. Later, a browser-session-scoped
or websocket push channel can reduce races and latency.

## pyslang Elaboration Contract

`workflow/sim_debug/elab.py` provides the semantic RTL layer:

- hierarchy build;
- module signal extraction;
- driver/load tracing;
- dual backend cross-checking when configured;
- static fallback when pyslang import/API compatibility fails.

Cache lives under `.session/elab_cache`, keyed by backend/top/source mtimes and
an explicit cache version. Cache version must be bumped when trace or signal
semantics change.

Trace semantics:

- multiple drivers are represented as a list, not just a single `driver`;
- assignment line location should land on the assignment line, not the `always`
  header;
- reads in conditions and port maps are loads/sinks;
- text fallback is acceptable for continuity but less precise.

## RC Save/Restore Contract

RC endpoints live in `src/atlas_api_vcd.py`:

- names must match a safe filename ending in `.rc`;
- dotfiles and path traversal are rejected;
- files are stored in `<ip>/sim/`;
- new format is JSON envelope:

```json
{
  "version": 1,
  "kind": "sim_debug_wave_rc",
  "payload": {}
}
```

The payload is a UI layout, not a guarantee that every saved signal exists in
every future VCD. Restore should preserve unresolved rows visibly.

## Verification Map

Frontend tests covering current Sim Debug behavior:

- `frontend/atlas/__tests__/sim-debug-vcd-scope-annotation.test.jsx`
  - IP-scoped VCD picker;
  - source-line cursor annotations;
  - pinned rows beyond default slice;
  - bus slices distinct from full buses;
  - zero-extension before slicing upper bits;
  - parameter map extraction;
  - waveform reorder helper;
  - missing-top-prefix and scoped pin resolution;
  - ambiguous leaf-only pins stay unresolved.
- `frontend/atlas/__tests__/sim-debug-ctrlw-add.test.tsx`
  - focused RTL signal adds with instance scope;
  - Ctrl-selected RTL signals add with scope;
  - source-dragged signals add with `Ctrl+W`.
- `frontend/atlas/__tests__/sim-debug-source-viewer.test.tsx`
  - selected source signal highlight;
  - bit-slice exact highlight;
  - native selection clearing;
  - semantic drag selection;
  - exact source bit-slice pick.
- `frontend/atlas/__tests__/sim-debug-intent-hook.test.ts`
  - intent polling ignores other-IP intents;
  - blank-IP intent is global once.
- `frontend/atlas/__tests__/wave-edge-click.test.jsx`
  - edge click behavior;
  - color hints;
  - parameter/FSM value display.

Backend/core tests covering Sim Debug:

- `tests/test_sim_debug_elab.py` - hierarchy, fallback, trace precision,
  multi-driver/loads, cached dual backend label.
- `tests/test_sim_debug_analyze.py` - VCD timeline analysis, find/value, scoped
  resolution, ambiguous elab module pins, trace dispatch.
- `tests/test_sim_debug_intent.py` - tool action guards, schema registration,
  file-channel API route.
- `tests/test_sim_debug_top_resolution.py` - top resolution from manifest,
  explicit top, VCD scope, and dump-helper filtering.

Recent verification evidence from the feature work:

```text
cd frontend/atlas
npx tsc --noEmit
npm test -- \
  __tests__/sim-debug-vcd-scope-annotation.test.jsx \
  __tests__/sim-debug-ctrlw-add.test.tsx \
  __tests__/sim-debug-source-viewer.test.tsx \
  __tests__/wave-edge-click.test.jsx
npm run build
git diff --check
```

Result recorded at review time: TypeScript passed, the 4 targeted frontend test
files passed with 28 tests, Vite build passed with pre-existing bundle warnings,
and whitespace check passed.

## Operational Guardrails

- Preserve `scope` on every path that adds a signal to the waveform:
  hierarchy signal row, source click/drag, tool call, RC restore, and group/order
  mutations.
- Do not "fix" ambiguous leaf-only requests by picking the first VCD match.
  Ask for or infer a real scope; otherwise keep a visible unresolved row.
- Keep source selection semantic by default. Native text selection can exist as
  an explicit escape hatch, but normal drag should select signals, not dim
  arbitrary source blocks.
- Do not eagerly elaborate module signals during first Debug loading. Keep
  source/hierarchy usable first, then fetch signal lists on demand.
- Keep plot dragging and row dragging separated by zone. Plot zone is for
  cursor/zoom; label/value zone is for reorder.
- If renderer performance becomes a problem, profile row count and visible
  sample count before moving to Canvas.
- When changing pyslang trace semantics, bump elab cache version and add a
  targeted test with exact line expectations.
- When changing wiki/docs for Sim Debug, run:

```text
python3 workflow/wiki/build_graph.py --check
```

## Recommended Next Work

Priority recommendations:

- Add a browser E2E test for waveform row and group drag/drop reorder.
- Scope the intent channel by browser session or tab when multi-user Sim Debug
  becomes a product target.
- Make RC restore optionally validate against the selected VCD and summarize
  unresolved rows.
- Add a small performance probe that records row count, sample segment count,
  VCD size, parse time, and render time for realistic large VCDs.
- Keep the Canvas/hybrid renderer as a measured migration path, not a default
  rewrite.
