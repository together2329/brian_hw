# Sim Debug — RTL module signal panel (2026-05-30)

Adds a per-module signal browser to the Sim Debug left panel: click a module in
the RTL hierarchy tree and the bottom panel lists **that module's signals** —
ports (with `in` / `out` / `inout` direction) plus internal nets/variables —
filterable by direction, searchable by regex, and addable to the waveform.

## What was built

### Backend — pyslang signal extraction
- `workflow/sim_debug/elab.py`
  - `PyslangElab.module_signals(top, module, sources)` — walks the elaborated
    symbol table, finds the first instance of `module` (most-members wins, same
    duplicate-module handling as `build_hierarchy`), and classifies each body
    member:
    - `PortSymbol` → `in` / `out` / `inout` from `ArgumentDirection`
    - `VariableSymbol` / `NetSymbol` → `internal`
    - captures `type` (e.g. `logic[15:0]`), bit `width`, and `file:line`.
  - **Dedup is mandatory**: every port re-appears as a backing `VariableSymbol`
    (verified — all 33 ports of `mctp_assembler` also show as Variables), so
    port names are removed from the internal list (port wins).
  - `_static_module_signals(...)` — regex fallback (ANSI port header + internal
    `reg/wire/logic` decls) for when pyslang cannot import, mirroring the
    existing `_static_hierarchy` / `_static_trace_driver` pattern.
  - `module_signals_cached(prefer, top, module, sources)` — always routes
    through pyslang (only backend with port directions); same disk cache as the
    other elab helpers.
- `src/atlas_api_sim_debug.py` — `GET /api/module/signals?module=&top=&ip=`
  returns `{module, instance_path, signals[], counts{in,out,inout,internal,total}}`.
  Same source resolution + top resolution as `/api/hierarchy`; runs the elab off
  the event loop via `asyncio.to_thread`.

### Frontend
- `frontend/atlas/sim-debug-module-signals.tsx` — **new** `useModuleSignals`
  hook (feature-split out of the root to keep `sim-debug.tsx` lean: 816→767 LOC).
  Owns the signal list, the `in/out/internal` filter, the `rtl/vcd` source
  toggle, and the click→focus + source-jump handler.
- `frontend/atlas/sim-debug-panels-side.tsx` — bottom `HierarchyPanel` pane
  rewritten:
  - RTL/VCD source toggle; regex **search box** (`buildSignalSearchMatcher`,
    invalid pattern falls back to substring + red flag).
  - direction **filter chips** `all / in / out / int` with live counts.
  - per-row direction glyph + width badge; `◆` pinned / `◇` present-in-VCD / `·`.
  - **add to waveform** three ways: select + `Ctrl+W`, double-click, or
    right-click → context menu.
  - default hierarchy/signals split is now **50/50** (`hierFrac` 0.62→0.5),
    matching the source/waveform split.
- `frontend/atlas/sim-debug-helpers.tsx` — pure helpers `filterModuleSignals`,
  `moduleSignalCounts`, `moduleSignalWidthLabel`, `buildSignalSearchMatcher`.
- `frontend/atlas/sim-debug.tsx` — `pinSignalToWave(name, scope)` extracted so
  both `Ctrl+W` and the right-click menu share one pin path.

### Bug fix — waveform scroll
`frontend/atlas/sim-debug-wave.tsx`: the cursor strip was `position:sticky;
top:22` while the `TimeRuler` scrolled away, leaving a 22px gap that let trace
rows bleed through on scroll-down ("화면 깨짐"). Ruler + cursor strip are now
wrapped in **one** `sticky; top:0` header so the rows scroll cleanly beneath.

## Existing behavior reused
- `h` toggles full-hierarchy (`scope.name`) ↔ name-only — already wired via
  `showSignalHierarchy`; now also drives the RTL signal list display.
- Pinned RTL signals match VCD signals **by name** (empty scope) so a pin
  resolves regardless of VCD scope nesting.

## Verification
- `tests/test_sim_debug_elab.py` — +3 tests (pyslang classify+dedup+width,
  text fallback, cached helper). 7 passed.
- `tsc --noEmit` on `frontend/atlas` — 0 errors.
- `/api/module/signals` route registration smoke — OK.
- Probe on `mctp_assembler`: in=21, out=12, internal=138, no duplicates;
  child `u_context` resolved at instance path `mctp_assembler.u_context`.

## Multi-select + signal trace (same session)
- **Multi-select** in the signal pane: `Ctrl/⌘+click` toggles, `Shift+click`
  range-selects. Action bar shows `N selected · ＋ add to wave · clear`. Bulk
  add via the button, `Ctrl+W`, or right-click "Add N to waveform". Root owns
  `waveSel` + `pinSignalsToWave([...])`; `pinSignalToWave` delegates to it.
- **Right-click signal trace** (pyslang `/api/trace`, already existed):
  - context menu "↳ Trace driver / loads" → `runSignalTrace` populates a
    `TraceFanoutPopover` (bottom-left) listing the **driver (drive)** and each
    **load/sink (RD/RW)**; click any row → source viewer jumps there (follow).
  - "→ Go to driver" jumps straight to the driver (existing `onSelectWaveSignal`).
  - `trace_driver` classifies LHS=driver / read=load via the elaborated
    symbol walk.

### Trace precision fix (driver landed on `always`, loads missing)
`PyslangElab.trace_driver` used the **block** location (`m.location`) for both
driver and sinks, so clicking the driver jumped to the `always` keyword, not the
real assignment; and sinks were only found on an assignment **RHS**, missing
reads inside `if (...)` / `case` / port maps. Rewrote it to be **line-precise**:
- `_classify_line(line)` → `(is_write, is_read)`: write = `bare` is the
  assignment target (identifier just left of `=`/`<=`, paren-depth 0 so an
  `if (a <= b)` comparison isn't a write); read = appears in a condition / RHS /
  port map.
- Each block line maps to its real source line via
  `getLineNumber(syntax.sourceRange.start) + offset`, **minus the count of
  leading `"\n"` trivia** (a leading newline makes `split()[0]` an empty phantom
  and `getLineNumber` reports the line *after* the newline → off-by-one). Verified
  against ground truth: `mctp_assembler.process_active_q` driver → exact `<=`
  line 211 (not `always` @209); loads found at 198/202/235/249 incl. cross-file.
- Loads deduped by `file:line`, driver's own line dropped, cap 20.
- `ELAB_CACHE_VERSION` bumped v8→**v9** to invalidate stale cached traces.
  Backend-only change; `_load_sim_debug_elab` hot-reloads elab.py by mtime, so no
  server restart / frontend rebuild needed.
- Tests: +2 (`...lands_on_exact_assignment_line`, `...load_in_condition_is_found`).

## Source-code signal click (same session)
Click an identifier **in the source viewer** to drive the waveform:
- single-click → focus that signal (then `Ctrl+W` adds it)
- double-click → add straight to the waveform
- right-click → menu: `＋ Add to waveform` / `↳ Trace driver / loads` / `→ Go to driver`

Implementation: `identifierAtPoint(x,y)` in `sim-debug-panels.tsx` uses
`caretRangeFromPoint` (→ `caretPositionFromPoint` fallback) to resolve the word
under the cursor from the click point, expands to `[A-Za-z_]\w*`, and skips
`VERILOG_KEYWORDS`. `SourceViewer` raises `onPickSignal` / `onAddSignal` /
`onSignalContextMenu`; `SourceBand` threads them; the root renders the
fixed-position menu (`srcSigMenu`) and reuses `pinSignalToWave` /
`runSignalTrace` / `onSelectWaveSignal`. Right-click `preventDefault` +
`stopPropagation` only when on an identifier (else the native menu shows).

## Waveform: resizable label column + drag-to-zoom (same session)
Both in `frontend/atlas/sim-debug-wave.tsx` (+ `styles.css`):
- **Resizable middle bar** — the signal-name+value (label) column is now
  draggable vs the plot. A `--wave-name-w` CSS var (default 180px, set on
  `.wave-panel` from `nameW` state) drives `.wave-row` / `.time-ruler`
  `grid-template-columns`; the cursor-strip grid and the cursor-overlay origin
  (`plotLeft = nameW + 100`) follow it. A 6px `col-resize` handle sits at the
  label/plot boundary (`left: nameW+90`, top measured from the scroll
  container's `offsetTop`). Clamp 90–560px.
- **Cursor placement** — on the plot: **left-click = cursor A** (the
  region-selection baseline, snapped to the nearest transition edge via
  `jumpToWaveEdge`, which now sets cursor A not B), **middle-click = cursor B**
  (exact clicked time, handled in `startPlotDrag` `e.button===1` with
  `preventDefault` to kill autoscroll). Left-click also still selects the signal.
- **Drag-to-zoom** — click-drag horizontally across the plot to rubber-band a
  time region; on release `setViewRange([t0,t1])`. `xToTime` maps plot-relative
  px → time via `effRange`/`waveWidth` (same origin as the cursor overlay). A
  plain click still selects / moves cursor B (drag <4px = no zoom); after a real
  drag, `dragJustZoomed` + an `onClickCapture` guard (with a `setTimeout(…,0)`
  reset safety net) swallows the trailing click so it doesn't also fire.

## Waveform command/chat bar (same session)
A command input at the bottom of the wave panel drives the two cursors + zoom by
typing. `parseWaveCommand(input)` (pure, in `sim-debug-helpers.tsx`) → a
`WaveCommand` action, applied in `WaveBand` (`setWaveCursor`/`setWaveCursorB`/
`setViewRange`/`zoomFit`/`zoomToCursors`, clamped to the VCD `timeRange`).
Recognised phrasings: `a 5000 b 15000`, `a=5000 b=15000`, `cursor b 12000`,
`zoom 1000 8000`, `view 1000-5000`, `확대 2000 9000`, `a..b` / `zoom a b`, `fit`
/ `전체`, bare `1000 8000` → zoom, bare `5000` → cursor A. Input `stopPropagation`s
so it doesn't fire the Verdi keyboard shortcuts; an echo line confirms the action.
NOTE: this is client-side command parsing — the **LLM-agent-driven** version
(natural language → the agent computes times from the VCD and drives the UI) is
the still-pending tool→UI bridge (see #9 in the follow-up section).

## Stale-build gotcha (hit this session)
Frontend is served from `frontend/atlas/dist/` (vite build, hashed assets;
`index.vite.html` read fresh each request). `.tsx` edits require `npm run build`
+ browser **hard reload** (Cmd+Shift+R) — no server restart. Symptom was the old
`SIGNALS (373)` panel persisting. See [[project_vite_env_stale_build]].

## Not yet done (follow-up)
- **Waveform region-find agent tool** (`별도 툴콜로 특정 구간 찾아 보여주기`):
  needs a server-side VCD analyzer + a *new* tool→UI navigation bridge (tools do
  not currently push UI events; the sim-debug chat panel is not mounted in this
  variation). Design pending — see session notes.
