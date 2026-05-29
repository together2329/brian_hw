# React Flow adoption decision (2026-05-29)

**Verdict: ADOPT `@xyflow/react` v12 — narrowly (SoC Architect first), and in the
NEXT cycle (not now). Decision committed; execution scheduled.**

Now possible because the Vite cutover landed (babel-free ESM, `.tsx`-first resolve)
— in-browser babel previously blocked npm graph libs. Related:
[[frontend-modernization-2026-05-29]] · [[tech-direction-recommendation-20260529]].

## Why adopt (the real win)
Every ATLAS diagram is hand-rolled inline `<svg>` + manual layout math today (no
graph-lib deps). The **SoC Architect** view is the only genuinely interactive
node-edge graph and re-implements an entire mini graph-editor by hand:
- pan (`panDragRef` + 4 mouse handlers), zoom (wheel + buttons + manual `scale` transform),
  node-drag (delta/scale math + dead-zone + clamp + persist to localStorage & `POST /api/soc/layout`),
  a **hand-built minimap that recomputes the auto-grid layout a 2nd time** to stay in sync,
  click-port→click-port connect (`POST /api/soc/connect`), and **auto-grid layout math
  duplicated 3×** (renderSocView / renderClusterView / minimap).
- Files: `soc-architect-canvas.tsx` (272 LOC pan/zoom/minimap shell) +
  `soc-architect-diagrams.tsx` (799) + `soc-architect-tree.tsx` (229).

React Flow's `<Controls>` / `<MiniMap>` / `<Background>` + built-in node dragging +
viewport state **delete most of `soc-architect-canvas.tsx` and the triplicated layout
math**, and `soc.busses`→edges / ports→`<Handle>` / connect→`onConnect` map ~1:1.

## Targets
| Diagram | Decision |
|---|---|
| **SoC Architect** (`renderSocView` + cluster + module, `soc-architect-*.tsx`) | ✅ **1st** — highest interactivity+pain payoff |
| **Pipeline `EnhancedFlowCanvas`** (`pipeline-trace-canvas.tsx` + `pipeline-cards.tsx`) | ✅ 2nd — removes **13 frozen magic-number SVG path strings** (`ENH_ROUTE_EDGES`, copied from a mockup) + the `ENH_EDGE_BADGE_POS` table via auto edge-routing. Static, so interactivity gain is small. |
| FSM (`workspace-ssot-fsm.tsx`) | ⚪ Leave — mermaid stateDiagram is the right tool (declarative, layout-only). Cleanup only: delete the duplicate legacy FSM in `workspace.jsx` (~10787-11173). |
| `BlockDiagram` (`block-diagram.tsx`) | ⚪ Leave — not a node-edge graph (framed box + CSS-grid cells + decorative pin lines). RF would regress simplicity. |
| `PipelineFlowMap` (`pipeline-flow-stage.tsx`) | ⚪ Leave — layout already data-driven (`PIPELINE_NODE_LAYOUT`), interactivity is click-only. Modest payoff; revisit only when unifying with EnhancedFlowCanvas on the proven RF component. |
| VCD waveform | ⚪ Leave — Canvas territory (10k+ nodes), not React Flow. |

## Cost & hard rules
- **~60-70 KB gzip net**: `@xyflow/react` v12 (~45-55) + `dagre@0.8.5` (~12-15). zustand (~4) likely already pulled.
- **MUST `React.lazy`/dynamic-import behind the architect route** so it never loads on login/lobby — directly contains the WKWebView/bundle-size perf concern (see the Tauri-perf finding: WKWebView/JSC + the ~900KB bundle). Measure on-device WKWebView impact before migrating a 2nd diagram.
- **Do NOT add `elkjs`** (8 MB unpacked) unless hierarchical-orthogonal routing becomes a firm need. Pin `@xyflow/react` + `zustand@^4.4.0` + `@xyflow/system`; re-run the vitest smoke after install (note the pre-existing vitest vite@5 ↔ vite@7 plugin-type skew).

## Effort
First slice (SoC overview + cluster + module in one pass): **~3-5 dev-days.**
- Highest risk/effort: the **3-source layout-persistence parity** (localStorage `layout[ref]` → `module.savedX/savedY` → fallback) in controlled mode (`applyNodeChanges` → existing `persistLayout`) — must be tested against real saved `<ip>.ssot.yaml` layouts so existing user drags aren't clobbered.
- Medium: `onConnect` → `/api/soc/connect` with master/slave + proto-family validators; CSS-variable theming of the RF container/edges/minimap.
- Low: custom `ipBlock` node (existing `.bd-block` markup ~verbatim, port spans → `<Handle>`); dagre fallback layout.
- Subsequent diagrams: ~0.5-1 day each once `nodeTypes` + the pattern exist.

## Timing — NEXT cycle, gated
Not now, because: (a) Vite **just stabilized** — let it bake before stacking a graph runtime + zustand store (duplicate-React-instance risk); (b) `soc-architect-*.tsx` is **actively being refactored** (979/799/272 LOC files touched 2026-05-29) — a big-bang RF rewrite collides; (c) the WKWebView/bundle perf concern needs the lazy-route isolation + a real measurement first.

→ **Schedule the SoC-overview first slice for next cycle, gated on the SoC refactor settling; ship it lazy-loaded behind the architect route with dagre (never elkjs); measure WKWebView impact before the 2nd diagram.**

## First-slice plan (when it starts)
SoC Architect overview behind `React.lazy` on the architect route. `{cluster,module,ref}` → `Node{id:ref, type:'ipBlock', position:{x,y}, data:{module}}`; the `.bd-block` with-ports markup becomes the `ipBlock` custom node ~verbatim; port spans → `<Handle>` source/target; each `soc.busses{from,to,proto}` → `Edge{source,target,data:{proto}}`. **Controlled mode** (nodes/edges as state, `onNodesChange`→`applyNodeChanges`, deltas persisted via the EXISTING `persistLayout`, preserving the 3-source precedence). dagre as the fallback auto-layout (replacing the triplicated grid math).
