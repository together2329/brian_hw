# Sim Debug agent tool — `sim_debug` (VCD + pyslang, drives the waveform UI)

2026-05-31. The chat agent can now drive AND query the Sim Debug waveform panel
via one tool. It parses the VCD (Python) and the RTL (pyslang) server-side,
returns the analysis as text to the agent, and pushes a UI intent the open panel
applies (navigate / show signals / cursor / trace).

## Channel: file-intent + UI polling
Tools may run in a separate worker process, so an in-memory bridge is unsafe.
The tool writes the **latest** intent to `<ATLAS_PROJECT_ROOT>/.session/sim_debug_intent.json`
(gitignored, atomic temp+`os.replace`, `seq=time.time_ns()`); the panel polls
`GET /api/sim_debug/intent?ip=` every ~1.5 s and applies when `seq` increases and
the intent's `ip` matches the panel's active IP. SimDebug only mounts on the
Debug/Sim Summary tab, so polling is bounded; an immediate fetch on mount gives
catch-up if the agent acted before the tab was open.

Intent schema: `{ seq, ip, action:"show"|"goto"|"cursor"|"trace"|"fit"|"reorder"|
"group"|"ungroup"|"color"|"fold"|"unfold", signals?:[], signal?, t_start?, t_end?,
cursor_a?, cursor_b?, group?, color? }`.

## Tool actions (`core/tools.py: sim_debug`)
- `show`    — add signal(s) to the wave (`signals="a,b"` / `signal="a"`).
- `goto`    — zoom to `[t_start,t_end]` ns (+ optional cursors).
- `cursor`  — place cursor A/B.
- `fit`     — reset to whole VCD.
- `reorder` — set the top-to-bottom row order (`signals=` desired order; listed
  lead, rest follow). UI also reorders by drag or the right-click ↑/↓ menu.
- `group`   — tag signals into a named, foldable group rendered ABOVE them
  (`group="name"`, `signals=`, optional `color="#rrggbb"`). Underlying rows are
  left intact (tag-based); members are pulled together under the header.
- `ungroup` — drop signal(s) from their group (`signals=`).
- `color`   — recolor signal(s) (`color="#rrggbb"`, `signals=`). UI: right-click
  a row → colour swatches.
- `fold`/`unfold` — collapse/expand a group (`group="name"`).
- `trace`   — pyslang driver + load sites (file:line) returned as text + shown in
  the trace popover.
- `find`    — VCD: time of a signal's Nth edge (`edge=rising|falling|any`), then a
  `goto` intent jumps the panel there with the signal shown.
- `value`   — VCD: value of a signal at time `at` ns.

## Decoration model (color / group / order)
Color + group tag are keyed by a NORMALIZED signal name and resolved at render
via `signalAliasKeys` (sim-debug-helpers), so an agent's full path
(`NEWIP_MCTP.u_packet_engine.mctp_som`), a leaf, OR a right-click row ident all
resolve to the same row — incl. VCD id-aliased nets. `buildWaveDisplayRows`
turns the flat `traceList` into `[group header → its members]*` honoring fold.
State lives in `sim-debug.tsx` (`signalColors` / `signalTags` / `groupState`),
flows to `WaveBand` as one `decor` bundle, and is agent-writable through
`useSimDebugIntent` (`reorderByNames`/`assignGroupByNames`/`setSignalColorByNames`/
`ungroupByNames`/`toggleGroupFold`). Right-click menu + group header (rename via
double-click, fold caret, colour dot) live in `sim-debug-wave.tsx`.

Schema registered in `core/tool_schema.py` (`TOOL_SCHEMAS["sim_debug"]`,
required `action`). The LLM maps natural language → these primitives.

## New / changed files
- NEW `core/sim_debug_intent.py` — `push_intent`/`get_intent` (file store).
- NEW `core/vcd_timeline.py` — minimal stdlib VCD reader with a real
  time→value timeline (`load`, `edges`, `value_at`, `match_signals`,
  `time_range`); fills the gap `workflow/coverage/adapters/vcd_toggle.py` leaves
  (it aggregates toggles, drops timestamps).
- NEW `core/sim_debug_analyze.py` — `trace_signal` / `find_event` /
  `signal_value` + `run_sim_debug_analysis` dispatcher.
- NEW `src/sim_debug_sources.py` — `resolve_elab_sources(project_root, glob, ip)`,
  **extracted** from the `_elab_resolve_sources` closure in
  `src/atlas_api_sim_debug.py` (logic-identical) so both the routes and the tool
  reuse it.
- EDIT `core/tools.py` (handler + `AVAILABLE_TOOLS`), `core/tool_schema.py`
  (schema), `src/atlas_api_sim_debug.py` (`/api/sim_debug/intent` route + import
  the extracted resolver), `frontend/atlas/sim-debug.tsx` (poll + apply via the
  existing `pinSignalsToWave`/`setViewRange`/`runSignalTrace`/`setWaveCursor[B]`/
  `zoomFit` handlers).

## Reuse (no reinvention)
- pyslang: `workflow/sim_debug/elab.py` `trace_driver_cached` (loaded by path).
- top resolution: `src/atlas_sim_debug_top.py:resolve_sim_debug_top`.
- VCD location: `<ip>/sim/**/*.vcd` (newest).

## Verification
- `pytest tests/test_sim_debug_intent.py tests/test_sim_debug_analyze.py tests/test_sim_debug_elab.py -q` → 16 passed (elab still green ⇒ source extraction is behavior-preserving).
- `frontend/atlas`: `tsc --noEmit` 0 errors; built (bundle contains `api/sim_debug/intent`).
- Real-VCD probe (`mctp_assembler`): `find_event(s_axi_awvalid, rising, 1)` →
  3250000 ps of 56; `trace_signal(parse_ok)` → driver `mctp_assembler.sv:188` + 3
  loads; route registration includes `/api/sim_debug/intent`.
- Manual end-to-end (file channel, no agent): server running + Debug tab open,
  then `python -c "from core.sim_debug_intent import push_intent; push_intent('NEWIP_MCTP','show',signals=['s_axi_awvalid'])"`
  → wave adds it ≤1.5 s.

## Limits / future
- Per-IP intent (not per-session); UI filters by ip. Key by session for strict
  multi-user later.
- Re-opening the Debug tab re-applies the last intent once (catch-up) — harmless.
- `find`/`value` cover scalar + simple bus edges; no multi-clock/strobe modelling.
- ~1.5 s latency (polling); `bridge.emit` WS-push is a later optimization.
