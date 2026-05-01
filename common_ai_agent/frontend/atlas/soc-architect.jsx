// soc-architect.jsx — Combined V6 + V7 Architect screen.
//
// Shared 3-column layout (hierarchy tree · center · chat). Center is
// a [Diagram | Status] tab toggle:
//   diagram → V7 drill-in canvas (SoC ▸ cluster ▸ module + bus routing)
//   status  → V6 orch grid + ssot.yaml editor on the selected module
//
// Mock data only — pulls from window.SOC / window.SOC_LOOKUP that
// soc-data.jsx loads. No live backend wiring yet.
(function injectStyles() {
  if (typeof document === 'undefined' || document.getElementById('arch-styles')) return;
  const s = document.createElement('style');
  s.id = 'arch-styles';
  s.textContent = `
/* ── V8 tab toggle ───────────────────────────────────────────── */
.v8-tab {
  background: transparent; border: 0;
  padding: 8px 18px; cursor: pointer;
  font-family: var(--mono); font-size: 11.5px; letter-spacing: 0.06em;
  color: var(--fg-mute); border-right: 1px solid var(--line);
  display: inline-flex; align-items: center; gap: 6px;
  text-transform: uppercase; transition: color .12s, background .12s;
}
.v8-tab:hover { color: var(--fg); background: var(--bg-2); }
.v8-tab.sel { color: var(--accent); background: var(--bg);
  box-shadow: inset 0 -2px 0 var(--accent); }
.v8-tab .ic { font-size: 12px; }

/* ── Architect shell ─────────────────────────────────────────── */
.arch-screen { display: flex; flex-direction: column; height: 100%;
  background: var(--bg); color: var(--fg); }
.arch-screen .run-bar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--line);
  background: var(--panel);
  display: flex; align-items: center; gap: 10px;
}
.arch-screen .run-bar .grp { display: flex; gap: 1px; }
.arch-screen .run-bar .rb-btn {
  background: var(--bg-2); border: 1px solid var(--line);
  color: var(--fg-dim); padding: 4px 10px;
  font-family: var(--mono); font-size: 11px;
  cursor: pointer; display: inline-flex; align-items: center; gap: 5px;
  transition: border-color .12s, color .12s, background .12s;
}
.arch-screen .run-bar .rb-btn:hover { border-color: var(--accent); color: var(--accent); }
.arch-screen .run-bar .rb-btn.primary {
  background: color-mix(in oklch, var(--accent) 22%, var(--bg-2));
  border-color: var(--accent); color: var(--accent);
}
.arch-screen .run-bar .rb-btn:disabled { cursor: not-allowed; opacity: 0.4; }
.arch-screen .run-bar .rb-spacer { flex: 1; }
.arch-screen .run-bar .rb-meta {
  display: inline-flex; gap: 14px;
  font-family: var(--mono); font-size: 11px; color: var(--fg-mute);
}
.arch-screen .run-bar .rb-meta b { color: var(--fg); }

/* ── Block-diagram canvas (V7) ───────────────────────────────── */
.bd-canvas {
  position: relative; flex: 1; overflow: hidden;
  background:
    radial-gradient(circle at 1px 1px, color-mix(in oklch, var(--line) 80%, transparent) 1px, transparent 0) 0 0/24px 24px,
    var(--bg);
}
.bd-svg-layer { position: absolute; inset: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 1; }

/* The block itself — base style. .with-ports overrides body layout. */
.bd-block {
  position: absolute; box-sizing: border-box;
  background: color-mix(in oklch, var(--panel) 92%, var(--accent));
  border: 1px solid var(--line-2);
  font-family: var(--mono);
  cursor: pointer;
  display: flex; flex-direction: column;
  z-index: 2;
  transition: border-color .12s, box-shadow .12s, transform .15s;
  border-radius: 2px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.35);
}
.bd-block:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), 0 4px 16px rgba(0,0,0,0.5);
}
.bd-block.sel {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), 0 0 22px color-mix(in oklch, var(--accent) 35%, transparent);
}
.bd-block.cluster {
  background: color-mix(in oklch, var(--bg-2) 95%, var(--accent));
  border-style: dashed;
}
.bd-block.noc {
  background: color-mix(in oklch, var(--magenta) 10%, var(--panel));
  border-color: color-mix(in oklch, var(--magenta) 50%, var(--line-2));
}
.bd-block.touched {
  animation: bdAppear 1.6s ease-out;
}
@keyframes bdAppear {
  0%   { opacity: 0; transform: scale(0.85); }
  60%  { opacity: 1; transform: scale(1.04); border-color: var(--accent);
         box-shadow: 0 0 0 2px var(--accent), 0 0 32px var(--accent); }
  100% { opacity: 1; transform: scale(1); }
}
.bd-block-head {
  padding: 6px 10px;
  border-bottom: 1px solid var(--line);
  background: color-mix(in oklch, var(--bg-2) 70%, var(--panel));
  display: flex; align-items: center; gap: 8px;
  font-size: 11.5px; color: var(--fg);
}
.bd-block-head .ico { color: var(--fg-mute); font-size: 12px; width: 14px; text-align: center; }
.bd-block-head .nm { font-weight: 600; flex: 1; letter-spacing: 0.02em;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bd-block-head .add-badge {
  background: var(--accent); color: var(--bg);
  font-size: 9px; font-weight: 700;
  padding: 1px 5px; letter-spacing: 0.06em;
  border-radius: 1px;
}
.bd-block-body {
  padding: 6px 10px 8px; flex: 1;
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px;
}
.bd-block-body .lbl { font-size: 10.5px; color: var(--fg-dim); font-family: var(--mono); }
.bd-block-body .addr { font-size: 10px; color: var(--cyan); font-family: var(--mono); margin-top: 2px; }

/* ── Carbon-style block (named ports + center icon) ──────────── */
.bd-block.with-ports { padding: 0; box-sizing: border-box; }
.bd-block.with-ports .bd-block-head {
  padding: 4px 8px; font-size: 10.5px;
  background: var(--bg-2);
  border-bottom: 1px solid var(--line);
  display: flex; align-items: center; gap: 6px;
}
.bd-block.with-ports .bd-block-head .nm-instance {
  color: var(--fg); font-weight: 600;
}
.bd-block.with-ports .bd-block-head .nm-type {
  color: var(--fg-mute); font-size: 9.5px; font-weight: 400;
}
.bd-block.with-ports .bd-ports {
  display: grid;
  grid-template-columns: 1fr 44px 1fr;
  flex: 1; gap: 4px;
  padding: 6px 0; align-items: center;
  position: relative;
}
.bd-block.with-ports .bd-ports-col {
  display: flex; flex-direction: column; gap: 1px;
  font-family: var(--mono); font-size: 9px;
}
.bd-block.with-ports .bd-ports-col.left  { padding-left: 0;  align-items: flex-start; }
.bd-block.with-ports .bd-ports-col.right { padding-right: 0; align-items: flex-end; }
.bd-block.with-ports .bd-port {
  display: flex; align-items: center; gap: 3px;
  padding: 1px 4px;
  color: var(--fg-dim); white-space: nowrap;
  line-height: 1.3;
  position: relative;
}
.bd-block.with-ports .bd-port:hover { color: var(--fg); }
.bd-block.with-ports .bd-port .nm { letter-spacing: 0.02em; }
.bd-block.with-ports .bd-port .arr {
  font-size: 10px; line-height: 1; width: 6px; text-align: center;
}
.bd-block.with-ports .bd-port.proto-axi  .arr,
.bd-block.with-ports .bd-port.proto-axil .arr,
.bd-block.with-ports .bd-port.proto-ace  .arr  { color: var(--accent); }
.bd-block.with-ports .bd-port.proto-apb  .arr,
.bd-block.with-ports .bd-port.proto-ahb  .arr  { color: var(--magenta); }
.bd-block.with-ports .bd-port.proto-axis .arr  { color: var(--cyan); }
.bd-block.with-ports .bd-port.proto-irq  .arr  { color: var(--warn); }
.bd-block.with-ports .bd-port.proto-clk  .arr,
.bd-block.with-ports .bd-port.proto-rst  .arr  { color: var(--ok); }

/* hexagonal center icon */
.bd-block.with-ports .bd-center-icon {
  width: 36px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--mono); font-size: 14px; font-weight: 700;
  color: var(--accent);
  background: color-mix(in oklch, var(--accent) 12%, var(--bg-2));
  border: 1px solid color-mix(in oklch, var(--accent) 60%, var(--line));
  clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
  margin: 0 auto;
}
/* Distinct hex-icon colour per category so a glance tells you what
   class of IP each block is. CPU=blue (primary), BUS=magenta
   (interconnect), MEM=cyan (storage), PERIPH=green (external),
   ANALOG=amber (physical). */
.bd-block.with-ports.cpu    .bd-center-icon { color: var(--accent);  border-color: var(--accent); }
.bd-block.with-ports.mem    .bd-center-icon { color: var(--cyan);    border-color: var(--cyan); }
.bd-block.with-ports.bus    .bd-center-icon { color: var(--magenta); border-color: var(--magenta); }
.bd-block.with-ports.periph .bd-center-icon { color: var(--ok);      border-color: var(--ok); }
.bd-block.with-ports.analog .bd-center-icon { color: var(--warn);    border-color: var(--warn); }
/* Subtle border-tint on the whole block matching its category, so
   the kind reads even when the canvas is zoomed out. */
.bd-block.with-ports.cpu    { border-color: color-mix(in oklch, var(--accent)  60%, var(--line-2)); }
.bd-block.with-ports.bus    { border-color: color-mix(in oklch, var(--magenta) 60%, var(--line-2)); }
.bd-block.with-ports.mem    { border-color: color-mix(in oklch, var(--cyan)    60%, var(--line-2)); }
.bd-block.with-ports.periph { border-color: color-mix(in oklch, var(--ok)      60%, var(--line-2)); }
.bd-block.with-ports.analog { border-color: color-mix(in oklch, var(--warn)    60%, var(--line-2)); }

.bd-block.with-ports .clk-in-marker {
  position: absolute; bottom: 3px; left: 4px;
  font-size: 8.5px; color: var(--fg-mute); font-family: var(--mono);
  letter-spacing: 0.04em;
}
.bd-block.with-ports .bd-port.left-side::before {
  content: ''; position: absolute; left: -3px; top: 50%;
  width: 6px; height: 1px; background: var(--line-2);
}
.bd-block.with-ports .bd-port.right-side::after {
  content: ''; position: absolute; right: -3px; top: 50%;
  width: 6px; height: 1px; background: var(--line-2);
}

/* ── Hierarchy tree (left rail) ──────────────────────────────── */
.bd-tree { font-family: var(--mono); font-size: 12px; }
.bd-tree-row {
  padding: 4px 10px 4px 6px; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  border-left: 2px solid transparent;
  color: var(--fg-dim);
}
.bd-tree-row:hover { background: var(--bg-2); color: var(--fg); }
.bd-tree-row.sel   { background: color-mix(in oklch, var(--accent) 14%, transparent);
                     color: var(--accent); border-left-color: var(--accent); }
.bd-tree-row.cluster { color: var(--fg); font-weight: 500; }
.bd-tree-row.touched { color: var(--accent); animation: bdRowPulse 1.4s ease-out 2; }
@keyframes bdRowPulse {
  0%,100% { background: color-mix(in oklch, var(--accent) 12%, transparent); }
  50%     { background: color-mix(in oklch, var(--accent) 26%, transparent); }
}
.bd-tree-row .tw  { color: var(--fg-mute); font-size: 9px; width: 10px; }
.bd-tree-row .ico { color: var(--fg-mute); width: 14px; }
.bd-sync { font-size: 9px; color: var(--ok); letter-spacing: 0.1em; text-transform: uppercase;
  padding: 1px 6px; border: 1px solid color-mix(in oklch, var(--ok) 50%, var(--line)); }

/* ── Breadcrumb ──────────────────────────────────────────────── */
.bd-crumb { display: flex; align-items: center; gap: 6px;
            font-family: var(--mono); font-size: 11.5px; color: var(--fg-dim); }
.bd-crumb .seg { cursor: pointer; padding: 2px 6px; }
.bd-crumb .seg:hover { color: var(--accent); }
.bd-crumb .seg.last { color: var(--accent); cursor: default;
                      background: color-mix(in oklch, var(--accent) 12%, transparent); }
.bd-crumb .sep { color: var(--fg-mute); font-size: 10px; }

/* ── Layers / zoom / legend overlays on canvas ───────────────── */
.bd-layers {
  position: absolute; top: 12px; left: 12px; z-index: 5;
  background: color-mix(in oklch, var(--panel) 92%, transparent);
  border: 1px solid var(--line);
  padding: 8px 10px; font-family: var(--mono); font-size: 10.5px;
  backdrop-filter: blur(6px);
  display: flex; flex-direction: column; gap: 4px;
}
.bd-layers .ttl { font-size: 9px; color: var(--fg-mute);
                  letter-spacing: 0.12em; text-transform: uppercase;
                  margin-bottom: 4px; }
.bd-layers label { display: flex; align-items: center; gap: 6px;
                   color: var(--fg-dim); cursor: pointer; }
.bd-layers label:hover { color: var(--fg); }
.bd-layers input[type=checkbox] { accent-color: var(--accent); width: 11px; height: 11px; }

.bd-zoom {
  position: absolute; bottom: 12px; left: 12px; z-index: 5;
  display: flex; align-items: center; gap: 1px;
  background: color-mix(in oklch, var(--panel) 92%, transparent);
  border: 1px solid var(--line); font-family: var(--mono);
  backdrop-filter: blur(6px);
}
.bd-zoom button {
  background: transparent; border: 0; color: var(--fg-dim);
  font-family: inherit; font-size: 12px; padding: 4px 10px; cursor: pointer;
}
.bd-zoom button:hover { background: var(--bg-3); color: var(--accent); }
.bd-zoom .pct { padding: 4px 8px; font-size: 11px; color: var(--fg);
                border-left: 1px solid var(--line); border-right: 1px solid var(--line);
                min-width: 42px; text-align: center; }

.bd-legend {
  position: absolute; bottom: 12px; right: 12px; z-index: 5;
  display: flex; gap: 12px;
  background: color-mix(in oklch, var(--panel) 92%, transparent);
  border: 1px solid var(--line);
  padding: 6px 10px; font-family: var(--mono); font-size: 10px;
  backdrop-filter: blur(6px);
}
.bd-legend .swatch { display: inline-flex; align-items: center; gap: 5px; color: var(--fg-dim); }
.bd-legend .swatch::before { content: ''; display: inline-block; width: 12px; height: 2px;
                             background: currentColor; }
.bd-legend .swatch.acc { color: var(--accent); }
.bd-legend .swatch.magenta { color: var(--magenta); }
.bd-legend .swatch.cyan { color: var(--cyan); }
.bd-legend .swatch.warn { color: var(--warn); }

/* ── Pipeline strip dots ─────────────────────────────────────── */
.pl-strip { display: inline-flex; gap: 3px; align-items: center; }
.pl-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--line-2); position: relative;
}
.pl-dot.ok      { background: var(--ok); }
.pl-dot.partial { background: var(--warn); }
.pl-dot.err     { background: var(--err); }
.pl-dot.run     { background: var(--cyan); animation: plBlink 1s infinite; }
.pl-dot.pending { background: var(--line-2); }
@keyframes plBlink { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
.pl-strip-lg .pl-dot { width: 9px; height: 9px; }
.pl-legend {
  display: inline-flex; gap: 8px; font-size: 9.5px; color: var(--fg-mute);
  letter-spacing: 0.08em; text-transform: uppercase;
}
.pl-legend .cell { display: inline-flex; align-items: center; gap: 4px; }

/* ── Status grid (V6 status tab) ─────────────────────────────── */
.orch-grid { width: 100%; border-collapse: collapse;
             font-family: var(--mono); font-size: 11.5px; }
.orch-grid thead th {
  position: sticky; top: 0; z-index: 2;
  background: var(--panel); color: var(--fg-mute);
  font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase;
  font-weight: 500; text-align: left; padding: 8px;
  border-bottom: 1px solid var(--line-2);
}
.orch-grid tbody tr.orch-row {
  border-bottom: 1px solid var(--line); cursor: pointer;
  transition: background .08s;
}
.orch-grid tbody tr.orch-row:hover { background: var(--bg-2); }
.orch-grid tbody tr.orch-row.sel { background: color-mix(in oklch, var(--accent) 10%, var(--bg)); }
.orch-grid tbody tr.orch-row.sel td { color: var(--fg); }
.orch-grid tbody tr.orch-row.errrow {
  background: color-mix(in oklch, var(--err) 6%, transparent);
}
.orch-grid tbody tr.orch-row.touched {
  animation: orchPulse 1.4s ease-out infinite;
  box-shadow: inset 3px 0 0 var(--accent);
}
@keyframes orchPulse {
  0%, 100% { background: color-mix(in oklch, var(--accent) 8%, transparent); }
  50%      { background: color-mix(in oklch, var(--accent) 18%, transparent); }
}
.orch-grid tbody td { padding: 5px 8px; vertical-align: middle; color: var(--fg-dim); }
.orch-grid .g-mark { text-align: center; }
.orch-grid .g-add {
  display: inline-block; width: 16px; height: 16px; line-height: 16px;
  text-align: center; background: var(--accent); color: var(--bg);
  font-weight: 700; font-size: 11px;
}
.orch-grid .g-mod-ico { color: var(--fg-mute); margin-right: 6px; }
.orch-grid .g-mod-nm  { color: var(--fg); font-weight: 500; }
.orch-grid tr.sel .g-mod-nm { color: var(--accent); }
.orch-grid .g-clu  { color: var(--fg-mute); font-size: 11px; }
.orch-grid .g-kind {
  font-size: 9.5px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--fg-mute); padding: 2px 6px;
  background: var(--bg-3); border: 1px solid var(--line);
}
.orch-grid .g-addr { color: var(--cyan); font-size: 11px; }
.orch-grid .g-tnum { font-size: 11px; color: var(--fg-dim); }
.orch-grid .g-note { font-size: 11px; }
.orch-grid .g-note .err  { color: var(--err); }
.orch-grid .g-note .warn { color: var(--warn); }
.orch-grid .g-note .acc  { color: var(--accent); }

/* ── Code/yaml inline editor ─────────────────────────────────── */
.code-pane {
  background: var(--bg); padding: 10px 14px;
  font-family: var(--mono); font-size: 11.5px;
  white-space: pre; color: var(--fg);
  border-top: 1px solid var(--line);
  overflow: auto; line-height: 1.6;
}

/* ── Box header (panel title) ────────────────────────────────── */
.arch-screen .box-h {
  border-bottom: 1px solid var(--line); padding: 6px 10px;
  background: var(--bg-2);
  font-size: 11px; color: var(--fg-dim);
  letter-spacing: 0.06em; text-transform: uppercase;
  display: flex; align-items: center; gap: 8px;
}
.arch-screen .box-h b { color: var(--fg); font-weight: 600; letter-spacing: 0.04em; }

/* ── Suggestion chip ────────────────────────────────────────── */
.sug-chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--bg-3); border: 1px solid var(--line);
  padding: 4px 10px; font-size: 11px; cursor: pointer;
  color: var(--fg-dim); border-radius: 2px; font-family: var(--mono);
}
.sug-chip:hover { border-color: var(--accent); color: var(--accent); }
.sug-chip .arrow { color: var(--fg-mute); }

/* ── Top + bottom edge port rows (Carbon-style IRQ-on-top etc.) ─── */
.bd-block.with-ports .bd-ports-edge {
  display: flex; justify-content: space-around; gap: 4px;
  padding: 2px 8px;
  font-family: var(--mono); font-size: 9px;
}
.bd-block.with-ports .bd-ports-edge.top {
  border-bottom: 1px solid var(--line);
  background: color-mix(in oklch, var(--bg-2) 60%, transparent);
}
.bd-block.with-ports .bd-ports-edge.bottom {
  border-top: 1px solid var(--line);
  background: color-mix(in oklch, var(--bg-2) 60%, transparent);
}
.bd-block.with-ports .bd-port.top-side,
.bd-block.with-ports .bd-port.bottom-side {
  flex-direction: column; align-items: center; gap: 0;
  color: var(--fg-dim); white-space: nowrap; padding: 0 2px;
}
.bd-block.with-ports .bd-port.top-side::before {
  content: ''; position: absolute; top: -3px; left: 50%;
  width: 1px; height: 6px; background: var(--line-2);
}
.bd-block.with-ports .bd-port.bottom-side::after {
  content: ''; position: absolute; bottom: -3px; left: 50%;
  width: 1px; height: 6px; background: var(--line-2);
}

/* ── Cross-cluster stub markers ──────────────────────────────────
   When a connection in soc.ssot.yaml exits the current cluster's
   view (target IP lives in a different cluster), draw a small dashed
   chip on the block's edge with "→ <cluster>/<inst>/<iface>" so the
   user sees that the IP isn't actually isolated. */
.bd-stub {
  position: absolute; z-index: 3;
  font-family: var(--mono); font-size: 9px;
  color: var(--fg-mute); pointer-events: none;
  display: inline-flex; align-items: center; gap: 4px;
  background: color-mix(in oklch, var(--panel) 70%, transparent);
  padding: 1px 5px;
  border: 1px dashed var(--line-2);
  border-radius: 2px;
  white-space: nowrap;
}
.bd-stub.acc     { color: var(--accent);  border-color: color-mix(in oklch, var(--accent)  50%, var(--line-2)); }
.bd-stub.magenta { color: var(--magenta); border-color: color-mix(in oklch, var(--magenta) 50%, var(--line-2)); }
.bd-stub.cyan    { color: var(--cyan);    border-color: color-mix(in oklch, var(--cyan)    50%, var(--line-2)); }
.bd-stub.warn    { color: var(--warn);    border-color: color-mix(in oklch, var(--warn)    50%, var(--line-2)); }

/* ── Mini-map (cluster view, top-right corner) ─────────────────── */
.bd-minimap {
  position: absolute; top: 12px; right: 12px; z-index: 6;
  background: color-mix(in oklch, var(--panel) 92%, transparent);
  border: 1px solid var(--line-2);
  font-family: var(--mono);
  cursor: crosshair;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
}
.bd-minimap-head {
  padding: 2px 6px; font-size: 9px; color: var(--fg-mute);
  letter-spacing: 0.12em; text-transform: uppercase;
  border-bottom: 1px solid var(--line);
  display: flex; align-items: center; gap: 4px;
}
.bd-minimap-head > span:last-child { padding: 0 4px; }
.bd-minimap-head > span:last-child:hover { color: var(--err); }
.bd-minimap-body {
  position: relative;
  background:
    radial-gradient(circle at 1px 1px, color-mix(in oklch, var(--line) 70%, transparent) 1px, transparent 0) 0 0/6px 6px,
    var(--bg);
}
.bd-minimap-toggle {
  position: absolute; top: 12px; right: 12px; z-index: 6;
  background: color-mix(in oklch, var(--panel) 92%, transparent);
  border: 1px solid var(--line);
  color: var(--fg-mute); font-family: var(--mono); font-size: 10px;
  padding: 4px 10px; cursor: pointer;
  letter-spacing: 0.08em; text-transform: uppercase;
  backdrop-filter: blur(8px);
}
.bd-minimap-toggle:hover { color: var(--accent); border-color: var(--accent); }
`;
  document.head.appendChild(s);
})();

// Pipeline strip shared by V6 grid + V7 diagram. Same logic as the
// upstream zip; lives here because soc-shared.jsx doesn't ship it.
window.PIPELINE_STAGES = ['ssot', 'rtl', 'lint', 'sim', 'syn', 'sta', 'pnr'];
window.PIPELINE_LABEL = {
  ssot: 'SSOT', rtl: 'RTL', lint: 'LINT', sim: 'SIM',
  syn: 'SYN', sta: 'STA', pnr: 'PNR',
};
window.fullPipeline = function fullPipeline(status, modId) {
  const seed = (modId || '').charCodeAt(0) || 7;
  return {
    ssot: status.ssot,
    rtl:  status.rtl,
    lint: status.rtl === 'pending' ? 'pending'
        : status.rtl === 'partial' ? 'partial'
        : (seed % 5 === 0 ? 'partial' : 'ok'),
    sim:  status.sim,
    syn:  status.rtl === 'ok' && status.sim === 'ok' ? (seed % 4 === 0 ? 'partial' : 'ok') : 'pending',
    sta:  status.rtl === 'ok' && status.sim === 'ok' ? (seed % 6 === 0 ? 'partial' : 'pending') : 'pending',
    pnr:  'pending',
  };
};
window.PipelineStrip = function PipelineStrip({ status, modId, big = false }) {
  const full = window.fullPipeline(status, modId || '');
  return (
    <span className={`pl-strip ${big ? 'pl-strip-lg' : ''}`}>
      {window.PIPELINE_STAGES.map((s) => (
        <span key={s} className={`pl-dot ${full[s]}`}
              title={`${window.PIPELINE_LABEL[s]} · ${full[s]}`} />
      ))}
    </span>
  );
};

// ── Live SoC fetch ─────────────────────────────────────────────
// Pulls `/api/soc` and folds the response into a SOC-shaped object
// the renderers expect. Falls back to the bundled mock if the
// endpoint is unavailable or returns no clusters.
function _fetchLiveSoc() {
  return fetch('/api/soc').then(r => {
    if (!r.ok) throw new Error('soc fetch failed');
    return r.json();
  }).then(d => {
    if (!d || !Array.isArray(d.clusters) || d.clusters.length === 0) return null;
    // Position any cluster that lacks x/y so the diagram doesn't
    // collapse all blocks onto (0,0). Tile horizontally.
    d.clusters.forEach((c, i) => {
      if (typeof c.x !== 'number') c.x = 80 + i * 540;
      if (typeof c.y !== 'number') c.y = 90;
      if (typeof c.w !== 'number') c.w = 480;
      if (typeof c.h !== 'number') c.h = 460;
      (c.modules || []).forEach((m, j) => {
        if (typeof m.x !== 'number') m.x = 24 + (j % 3) * 150;
        if (typeof m.y !== 'number') m.y = 56 + Math.floor(j / 3) * 110;
        if (typeof m.w !== 'number') m.w = 140;
        if (typeof m.h !== 'number') m.h = 90;
        if (!Array.isArray(m.interfaces)) m.interfaces = [];
        if (!Array.isArray(m.params)) m.params = [];
      });
    });
    if (!Array.isArray(d.busses)) d.busses = [];
    if (!Array.isArray(d.addrMap)) d.addrMap = [];
    return d;
  }).catch(() => null);
}

// Tree-search helpers — case-insensitive substring match against the
// module's id and name + the cluster id. Returns true when query is
// empty (so the tree is unfiltered by default).
function _matchesQuery(m, clusterId, q) {
  if (!q) return true;
  const needle = q.toLowerCase();
  const hay = `${m.id || ''} ${m.name || ''} ${m.label || ''} ${clusterId || ''}`.toLowerCase();
  return hay.includes(needle);
}
// Wrap matched substrings in <mark>; safe-escape the rest so we can
// drop into dangerouslySetInnerHTML without an XSS hole.
function _highlightMatch(text, q) {
  const t = String(text || '');
  if (!q) return t.replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
  const esc = t.replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
  const re = new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
  return esc.replace(re, '<mark style="background:color-mix(in oklch, var(--accent) 35%, transparent);color:var(--fg);padding:0 1px;">$1</mark>');
}

function _buildLookup(soc) {
  const lk = {};
  for (const c of soc.clusters) {
    for (const m of c.modules) lk[`${c.id}/${m.id}`] = { cluster: c, module: m };
  }
  return lk;
}

// ── SocArchitect — the combined screen ──────────────────────────
window.SocArchitect = function SocArchitect() {
  const [tab, setTab] = React.useState('diagram');
  const [view, setView] = React.useState('soc');           // 'soc' | 'cluster:<id>' | 'module:<ref>'
  const [running, setRunning] = React.useState(null);
  const [layers, setLayers] = React.useState({
    modules: true, busses: true, clk: false, rst: false, labels: true,
  });
  // Default to fit-to-canvas-ish (70% works for most viewports);
  // bdCanvasRef + the fit() handler below recompute precisely.
  const [zoom, setZoom] = React.useState(70);
  const [pan, setPan] = React.useState({ x: 0, y: 0 });
  const bdCanvasRef = React.useRef(null);
  const panDragRef = React.useRef(null);
  // Per-block manual position overrides + persistence. The actual
  // localStorage key depends on `soc.name`, but `soc` is declared later
  // in this function — so we initialise the state to {} here and the
  // useEffect below (after soc is in scope) loads the right slot.
  const [layout, setLayout] = React.useState({});
  const blockDragRef = React.useRef(null);
  // Mini-map toggle
  const [miniOpen, setMiniOpen] = React.useState(true);
  // Sparkline hover popover state — which row is hovered, for the
  // status grid TREND column. {ref, x, y} or null.
  const [sparkPop, setSparkPop] = React.useState(null);
  const fitZoom = React.useCallback(() => {
    const el = bdCanvasRef.current; if (!el) return;
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    // Stage is 1180×720; pick the smaller axis ratio with a small
    // margin so the diagram doesn't kiss the edges.
    const r = Math.min(w / 1180, h / 720) * 0.94;
    setZoom(Math.max(20, Math.min(200, Math.round(r * 100))));
    setPan({ x: 0, y: 0 });          // recenter on fit
  }, []);
  React.useEffect(() => {
    fitZoom();
    if (typeof ResizeObserver === 'undefined') return;
    const el = bdCanvasRef.current; if (!el) return;
    const ro = new ResizeObserver(() => fitZoom());
    ro.observe(el);
    return () => { try { ro.disconnect(); } catch (_) {} };
  }, [fitZoom, view]);

  // Live data: try `/api/soc` first, fall back to the bundled mock.
  // `live=null` = still loading, `live=false` = fetch failed/empty
  // (use mock), `live=<soc>` = use live data.
  const [live, setLive] = React.useState(null);
  // Module refs that the agent just touched (mutated SSOT, regen'd RTL,
  // ran sim). Pulses on the diagram + grid until the user clicks
  // somewhere or the next refresh clears them.
  const [touchedSet, setTouchedSet] = React.useState(() => new Set());
  // Bumped on tool_result events so SocArchitect knows to re-fetch
  // /api/soc (pre-pass debounces multiple events into one fetch).
  const refreshTimerRef = React.useRef(null);
  const prevModuleRefsRef = React.useRef(new Set());
  const prevMtimeRef = React.useRef(new Map());

  // ── Derived data (computed every render, must come BEFORE any
  // useEffect/useMemo that references them — otherwise the deps
  // array hits a TDZ ReferenceError on the first call, the whole
  // component throws, and the screen unmounts.)
  const soc = (live && live.clusters && live.clusters.length) ? live : window.SOC;
  const lookup = (live && live.clusters && live.clusters.length) ? _buildLookup(live) : window.SOC_LOOKUP;
  const isLive = !!(live && live.clusters && live.clusters.length);

  // Hierarchy tree search query — case-insensitive substring match
  // against module id + name. Empty string means "show everything".
  // (Declared after `soc` so the useMemo deps array doesn't hit TDZ.)
  const [treeQuery, setTreeQuery] = React.useState('');
  const treeMatches = React.useMemo(() => {
    if (!treeQuery) return [];
    const out = [];
    for (const c of soc.clusters || [])
      for (const m of c.modules || [])
        if (_matchesQuery(m, c.id, treeQuery)) out.push({ ref: `${c.id}/${m.id}`, m, c });
    return out;
  }, [treeQuery, soc]);

  // Layout-persistence key depends on the SoC name so different SoCs
  // keep independent block-position layouts. Reload the layout slot
  // whenever the SoC name changes (Tier-1 ↔ Tier-2 swap, /wf switch).
  const _layoutKey = `architectLayout:${(soc && soc.name) || 'default'}`;
  React.useEffect(() => {
    try { setLayout(JSON.parse(localStorage.getItem(_layoutKey) || '{}') || {}); }
    catch (_) { setLayout({}); }
  }, [_layoutKey]);
  const persistLayout = React.useCallback((next) => {
    try { localStorage.setItem(_layoutKey, JSON.stringify(next)); } catch (_) {}
  }, [_layoutKey]);

  // Default selection: first module of first cluster (so we don't
  // hold a stale 'periph_ss/spi' ref on a live project that has
  // entirely different IP names).
  const firstRef = (soc && soc.clusters && soc.clusters[0] && soc.clusters[0].modules[0])
    ? `${soc.clusters[0].id}/${soc.clusters[0].modules[0].id}` : '';
  const [selMod, setSelMod] = React.useState(firstRef);

  const refreshSoc = React.useCallback(() => {
    return _fetchLiveSoc().then(d => {
      setLive(prev => {
        const next = d || prev || false;
        // Diff module refs: anything new gets marked touched. Also flag
        // a module whose ssot.yaml mtime moved forward (in-place edits
        // without a new module).
        if (next && next.clusters) {
          const nowRefs = new Set();
          const nowMtime = new Map();
          for (const c of next.clusters) for (const m of c.modules) {
            const ref = `${c.id}/${m.id}`;
            nowRefs.add(ref);
            if (m.ssot_mtime) nowMtime.set(ref, m.ssot_mtime);
          }
          const prevRefs = prevModuleRefsRef.current;
          const prevMtime = prevMtimeRef.current;
          const touched = [];
          for (const r of nowRefs) {
            if (!prevRefs.has(r)) touched.push(r);
            else if (prevMtime.get(r) && nowMtime.get(r) > prevMtime.get(r) + 0.5) touched.push(r);
          }
          if (touched.length && prevRefs.size > 0) {
            setTouchedSet(s => {
              const ns = new Set(s);
              for (const r of touched) ns.add(r);
              return ns;
            });
            // Auto-clear after 10s — the user's eye has caught the pulse
            // by then, and we don't want it animating forever.
            for (const r of touched) {
              setTimeout(() => {
                setTouchedSet(s => {
                  if (!s.has(r)) return s;
                  const ns = new Set(s); ns.delete(r); return ns;
                });
              }, 10000);
            }
          }
          prevModuleRefsRef.current = nowRefs;
          prevMtimeRef.current = nowMtime;
        }
        return next;
      });
    });
  }, []);

  React.useEffect(() => { refreshSoc(); }, [refreshSoc]);

  // Scope-follow: when the user drills into a cluster or module on
  // the diagram, set the global agent scope to that IP's directory so
  // subsequent prompts in the chat panel are confined. Drilling back
  // to the SoC overview clears the scope.
  React.useEffect(() => {
    if (!isLive || !window.atlasData || typeof window.atlasData.setScopePath !== 'function') return;
    let scope = '';
    if (view.startsWith('cluster:')) {
      // Single-cluster live mode: cluster scope = whole project (no
      // narrowing). Skip setting scope so user gets full project access.
      scope = '';
    } else if (view.startsWith('module:')) {
      const ref = view.split(':')[1];
      const lkv = lookup[ref];
      if (lkv && lkv.module && lkv.module.ip_dir) scope = lkv.module.ip_dir;
    }
    // Avoid clobbering an unrelated scope set by the Workspace screen.
    // Only override when we're presenting an IP-specific view.
    if (scope && window.SCOPE_PATH !== scope) {
      window.atlasData.setScopePath(scope);
    } else if (!scope && view === 'soc' && window.SCOPE_PATH) {
      // Drilled back to overview → release the scope so subsequent
      // prompts can roam.
      window.atlasData.setScopePath('');
    }
  }, [view, isLive, lookup]);

  // Watch tool_result events on the live WS bridge. Anything that
  // touches a yaml/rtl/sim path under <ip>/ → schedule a debounced
  // /api/soc refresh so the diagram + grid pick up the change.
  React.useEffect(() => {
    if (!window.backend || typeof window.backend.subscribe !== 'function') return;
    const schedule = () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = setTimeout(() => { refreshSoc(); }, 500);
    };
    const unsubA = window.backend.subscribe('tool_result', (m) => {
      const t = (m.text || '');
      // Only refresh when the tool result mentions a path that looks
      // like an SSOT mutation. Keeps unrelated tool calls (Read, grep)
      // from spamming the endpoint.
      if (/\.ssot\.yaml|\.sv\b|\bsim\/|\brtl\//.test(t)) schedule();
    });
    const unsubB = window.backend.subscribe('flush', schedule);
    return () => {
      try { unsubA(); } catch (_) {}
      try { unsubB(); } catch (_) {}
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, [refreshSoc]);

  React.useEffect(() => {
    // When live data lands, jump to its first module if our current
    // selection doesn't exist there. Also drill straight into the
    // first cluster — the SoC overview is hardcoded for the aurora
    // 4-cluster mock layout, which doesn't match live IPs.
    if (isLive) {
      if (!lookup[selMod]) setSelMod(firstRef);
      if (view === 'soc' && soc.clusters[0]) setView(`cluster:${soc.clusters[0].id}`);
    }
  }, [isLive, firstRef]); // eslint-disable-line

  // In live mode, `touchedSet` is populated by the tool_result watcher
  // above (modules that appear in /api/soc after they were absent before).
  // In mock mode, fall back to the bundled "agent just added periph_ss/spi"
  // demo selection so the design preview still shows the pulse animation.
  const agentTouched = isLive ? touchedSet : new Set(['periph_ss/spi']);
  const isTouched = (ref) => agentTouched.has(ref);
  const toggleLayer = (k) => setLayers(l => ({ ...l, [k]: !l[k] }));

  const allRows = [];
  for (const c of soc.clusters) {
    for (const m of c.modules) allRows.push({ ref: `${c.id}/${m.id}`, cluster: c, module: m });
  }
  const lk = lookup[selMod];
  const selModule = lk?.module;
  const selCluster = lk?.cluster;

  const crumb = (() => {
    const parts = [{ id: 'soc', label: soc.name || 'aurora_soc', target: 'soc' }];
    if (view.startsWith('cluster:')) {
      parts.push({ id: view.split(':')[1], label: view.split(':')[1], target: view, last: true });
    } else if (view.startsWith('module:')) {
      const ref = view.split(':')[1];
      const lkv = lookup[ref];
      if (lkv) {
        parts.push({ id: lkv.cluster.id, label: lkv.cluster.id, target: `cluster:${lkv.cluster.id}` });
        parts.push({ id: lkv.module.id, label: lkv.module.name, target: view, last: true });
      }
    } else { parts[0].last = true; }
    return parts;
  })();

  const filteredRows = (() => {
    if (view === 'soc') return allRows;
    if (view.startsWith('cluster:')) {
      const cid = view.split(':')[1];
      return allRows.filter(r => r.cluster.id === cid);
    }
    if (view.startsWith('module:')) {
      const ref = view.split(':')[1];
      return allRows.filter(r => r.ref === ref);
    }
    return allRows;
  })();

  // Run metadata for the status grid. Prefer real sim_history from
  // /api/soc; fall back to deterministic-pseudo-random demo values so
  // the mock mode still shows non-empty cells.
  const runMeta = (mod) => {
    const hist = Array.isArray(mod.sim_history) ? mod.sim_history : [];
    const last = hist[hist.length - 1];
    if (last) {
      return {
        t: last.t || '—',
        cov: last.cov || '—',
        tests: last.tests || '—',
        dur: last.dur || '—',
      };
    }
    return {
      t: mod.id === 'spi' ? '12:04:28' : mod.id === 'cpu1' ? '12:01:14' : mod.id === 'gic' ? '—' : '11:58:41',
      cov:   mod.status.sim === 'ok' ? '91%' : mod.status.sim === 'partial' ? '84%' : mod.status.sim === 'err' ? '87%' : '—',
      tests: mod.status.sim === 'ok' ? '24/24' : mod.status.sim === 'partial' ? '22/24' : mod.status.sim === 'err' ? '21/24' : '—',
      dur:   mod.status.sim === 'ok' ? '4.2s' : mod.status.sim === 'partial' ? '3.8s' : mod.status.sim === 'err' ? '5.1s' : '—',
    };
  };
  const sparkBars = (mod) => {
    const hist = Array.isArray(mod.sim_history) ? mod.sim_history : [];
    if (hist.length) {
      // Map each run's duration (seconds, parsed from "4.2s") onto a 2-11
      // bar height. If duration is missing, derive height from status:
      // ok = tall, partial = mid, err = short, pending = stub.
      const dursS = hist.map(r => {
        const v = parseFloat((r.dur || '').replace(/[^\d.]/g, ''));
        return isFinite(v) && v > 0 ? v : null;
      });
      const valid = dursS.filter(v => v != null);
      const max = valid.length ? Math.max(...valid) : 1;
      return hist.map((r, i) => {
        if (dursS[i] != null) {
          return Math.round(2 + (dursS[i] / max) * 9);
        }
        return r.status === 'ok' ? 9 : r.status === 'partial' ? 6 : r.status === 'err' ? 3 : 2;
      });
    }
    // Fallback (mock mode): deterministic-pseudo-random.
    const id = mod.id || '';
    if (!id) return [];
    const seed = id.charCodeAt(0) + id.charCodeAt(id.length - 1);
    return Array.from({ length: 10 }, (_, i) => ((seed * (i + 7)) % 9) + 2);
  };

  // ── V7 diagram renderers ──────────────────────────────────────
  const renderSocView = () => {
    const W = 1180, H = 720;
    const cx = W/2, cy = H/2;
    const positions = {
      cpu_ss:    { x: 80,    y: 90,  w: 280, h: 170 },
      mem_ss:    { x: W-360, y: 90,  w: 280, h: 170 },
      periph_ss: { x: 80,    y: H-260, w: 280, h: 170 },
      analog_ss: { x: W-360, y: H-260, w: 280, h: 170 },
      noc:       { x: cx-130,y: cy-85, w: 260, h: 170 },
    };
    const lines = [];
    if (layers.busses) {
      for (const cid of ['cpu_ss','mem_ss','periph_ss','analog_ss']) {
        const c = positions[cid];
        const cMidX = c.x + c.w/2, cMidY = c.y + c.h/2;
        const nMidX = positions.noc.x + positions.noc.w/2, nMidY = positions.noc.y + positions.noc.h/2;
        const dx = nMidX - cMidX, dy = nMidY - cMidY;
        const t1 = 1 - 130 / Math.sqrt(dx*dx + dy*dy);
        const x2 = cMidX + dx * t1, y2 = cMidY + dy * t1;
        const color = cid === 'cpu_ss' ? 'var(--accent)'
                    : cid === 'mem_ss' ? 'var(--cyan)'
                    : cid === 'periph_ss' ? 'var(--magenta)'
                    : 'var(--warn)';
        lines.push({ id: `${cid}-noc`, x1: cMidX, y1: cMidY, x2, y2, color });
      }
    }
    return (
      <React.Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {lines.map(l => (
            <g key={l.id}>
              <line x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke={l.color} strokeWidth="2" opacity="0.7" />
              <circle cx={l.x2} cy={l.y2} r="3" fill={l.color} opacity="0.9" />
            </g>
          ))}
        </svg>
        {(() => {
          const c = soc.clusters.find(c => c.id === 'noc'); if (!c) return null;
          const p = positions.noc;
          const sel = view === 'cluster:noc';
          return (
            <div className={`bd-block noc cluster ${sel ? 'sel' : ''}`}
                 style={{ left: p.x, top: p.y, width: p.w, height: p.h }}
                 onClick={() => setView('cluster:noc')}>
              <div className="bd-block-head">
                <span className="ico" style={{ color: 'var(--magenta)' }}>╫</span>
                <span className="nm">noc</span>
                {layers.labels && <span style={{ fontSize: 9, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>interconnect</span>}
              </div>
              <div className="bd-block-body">
                <div>
                  <div className="lbl">cci_550 · apb_bridge · dmac_330</div>
                  <div className="lbl" style={{ marginTop: 2 }}>{c.modules.length} modules</div>
                </div>
                <window.PipelineStrip status={c.status} modId={c.id} big />
              </div>
            </div>
          );
        })()}
        {soc.clusters.filter(c => c.id !== 'noc').map(c => {
          const p = positions[c.id]; if (!p) return null;
          const sel = view === `cluster:${c.id}`;
          const hasTouched = c.modules.some(m => isTouched(`${c.id}/${m.id}`));
          const errCount = c.modules.filter(m => m.status.sim === 'err').length;
          const role = c.id === 'cpu_ss' ? 'CPU'
                     : c.id === 'mem_ss' ? 'MEM'
                     : c.id === 'periph_ss' ? 'PERIPH'
                     : 'ANALOG';
          return (
            <div key={c.id} className={`bd-block cluster ${sel ? 'sel' : ''} ${hasTouched ? 'touched' : ''}`}
                 style={{ left: p.x, top: p.y, width: p.w, height: p.h }}
                 onClick={() => setView(`cluster:${c.id}`)}>
              <div className="bd-block-head">
                <span className="ico">{c.id === 'cpu_ss' ? '◆' : c.id === 'mem_ss' ? '▦' : c.id === 'periph_ss' ? '⊟' : '∿'}</span>
                <span className="nm">{c.id}</span>
                {hasTouched && <span className="add-badge">+1</span>}
                {layers.labels && <span style={{ fontSize: 9, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{role}</span>}
              </div>
              <div className="bd-block-body">
                <div>
                  <div className="lbl">{c.modules.slice(0, 3).map(m => m.name).join(' · ')}{c.modules.length > 3 && ' · …'}</div>
                  <div className="lbl" style={{ marginTop: 2 }}>
                    {c.modules.length} modules
                    {errCount > 0 && <span style={{ color: 'var(--err)' }}> · {errCount} sim ✗</span>}
                  </div>
                </div>
                <window.PipelineStrip status={c.status} modId={c.id} big />
              </div>
            </div>
          );
        })}
      </React.Fragment>
    );
  };

  // Carbon SoC-Designer-style cluster view: each module shows its
  // ports as labeled rows on the left + right edges with a center
  // type icon. Connections route pin-to-pin when the cluster has bus
  // info; otherwise we just show the blocks with their interfaces.
  const renderClusterView = (cid) => {
    const c = soc.clusters.find(c => c.id === cid); if (!c) return null;
    const W = 1180, H = 720;

    // Per-module port partition: left side = slave + clk + rst,
    // right side = master, top/bottom honoured when explicitly set
    // (typical for IRQ in/out which Carbon-style diagrams place on
    // the top edge). Cap at 5 ports per side so the block doesn't
    // grow taller than its column gap.
    const partition = (m) => {
      const ifs = (m.interfaces || []);
      const left = []; const right = []; const top = []; const bottom = [];
      for (const it of ifs) {
        const side = (it.side || '').toLowerCase();
        const role = (it.role || 'slave').toLowerCase();
        const proto = (it.proto || '').toUpperCase();
        // CLK/RST always go on the left (input pins).
        if (proto === 'CLK' || proto === 'RST') { left.push(it); continue; }
        // Honour explicit `side` first.
        if (side === 'top')         top.push(it);
        else if (side === 'bottom') bottom.push(it);
        else if (side === 'left')   left.push(it);
        else if (side === 'right')  right.push(it);
        // No explicit side: role-based.
        else if (role === 'master') right.push(it);
        else                        left.push(it);
      }
      return {
        left:   left.slice(0, 5),
        right:  right.slice(0, 5),
        top:    top.slice(0, 4),
        bottom: bottom.slice(0, 4),
      };
    };

    // Block size: header (24) + body padded for max(left,right) rows
    // at ~14px each + safe minimum. Top/bottom ports add fixed margins.
    const sizeOf = (m) => {
      const { left, right, top, bottom } = partition(m);
      const rows = Math.max(left.length, right.length, 2);
      const headerH = 24;
      const bodyH   = Math.max(76, rows * 14 + 24);
      const topPad    = top.length    ? 18 : 0;
      const bottomPad = bottom.length ? 18 : 0;
      return { w: 220, h: headerH + bodyH + topPad + bottomPad,
               topPad, bottomPad };
    };

    const cols = Math.min(3, c.modules.length);
    const rowsN = Math.ceil(c.modules.length / cols);
    const sizes = c.modules.map(sizeOf);
    const blockW = 220;
    const maxBlockH = Math.max(140, ...sizes.map(s => s.h));
    const gapX = Math.max(40, (W - cols * blockW) / (cols + 1));
    const gapY = Math.max(40, (H - rowsN * maxBlockH - 60) / (rowsN + 1));
    const positions = {};
    c.modules.forEach((m, i) => {
      const ref = `${c.id}/${m.id}`;
      const col = i % cols, rIdx = Math.floor(i / cols);
      // Position precedence (most-local first):
      //   1. layout[ref] from localStorage (user-dragged, not yet saved)
      //   2. m.savedX/savedY from soc.ssot.yaml (saved layout)
      //   3. auto-grid fallback
      const ov = layout && layout[ref];
      const hasOv = ov && typeof ov.x === 'number';
      const hasSaved = typeof m.savedX === 'number';
      positions[m.id] = {
        x: hasOv  ? ov.x
          : hasSaved ? m.savedX
          : gapX + col * (blockW + gapX),
        y: hasOv  ? ov.y
          : hasSaved ? m.savedY
          : 40 + gapY + rIdx * (maxBlockH + gapY),
        w: blockW,
        h: sizes[i].h,
      };
    });

    // Cluster colour cue — drives the optional rail when no per-bus
    // data is available.
    const railColor = c.id === 'cpu_ss' ? 'var(--accent)'
                    : c.id === 'mem_ss' ? 'var(--cyan)'
                    : c.id === 'periph_ss' ? 'var(--magenta)'
                    : c.id === 'noc' ? 'var(--magenta)'
                    : c.id === 'ips' ? 'var(--accent)'
                    : 'var(--warn)';

    // Pin-to-pin connection lines. For each module, walk left ports
    // and try to find a matching right-side port on another module
    // with the same proto family — heuristic, but enough to draw
    // realistic lines until proper bus info lands.
    const protoFamily = (p) => {
      const x = (p || '').toUpperCase();
      if (x === 'AXI' || x === 'AXI4' || x === 'AXI4L' || x === 'ACE' || x === 'AXIS') return 'axi';
      if (x === 'APB' || x === 'AHB') return 'apb';
      if (x === 'IRQ') return 'irq';
      return null;
    };
    const connections = [];
    if (layers.busses) {
      for (const m of c.modules) {
        const partA = partition(m);
        const headerH = 24;
        // For each master (right) on this module, try to find a
        // matching slave (left) on any other module with same family.
        partA.right.forEach((iface, i) => {
          const fam = protoFamily(iface.proto);
          if (!fam) return;
          for (const n of c.modules) {
            if (n.id === m.id) continue;
            const partB = partition(n);
            const j = partB.left.findIndex(x => protoFamily(x.proto) === fam);
            if (j === -1) continue;
            const pa = positions[m.id], pb = positions[n.id];
            const rowsA = Math.max(partA.left.length, partA.right.length, 2);
            const rowsB = Math.max(partB.left.length, partB.right.length, 2);
            const stepA = (pa.h - headerH - 12) / Math.max(rowsA, 1);
            const stepB = (pb.h - headerH - 12) / Math.max(rowsB, 1);
            const x1 = pa.x + pa.w + 3, y1 = pa.y + headerH + 6 + stepA * (i + 0.5);
            const x2 = pb.x - 3,        y2 = pb.y + headerH + 6 + stepB * (j + 0.5);
            const color = fam === 'axi' ? 'var(--accent)'
                        : fam === 'apb' ? 'var(--magenta)'
                        : fam === 'irq' ? 'var(--warn)'
                        : 'var(--cyan)';
              connections.push({ id: `${m.id}-${iface.name}-${n.id}`, x1, y1, x2, y2, color,
                                proto: iface.proto || '' });
            break; // 1 master ↔ 1 slave per family per module pair
          }
        });
      }
    }

    // Cross-cluster stubs — when soc.busses (from /api/soc) names a
    // connection whose ONE end is inside this cluster but the other is
    // in a different cluster, emit a small chip on the local block's
    // matching edge: "→ <other_cluster>/<other_inst>/<other_iface>".
    const stubs = [];
    const ipToCluster = {};
    for (const cc of soc.clusters) for (const mm of cc.modules) ipToCluster[mm.id] = cc.id;
    const localIds = new Set(c.modules.map(x => x.id));
    const allBusses = (soc && Array.isArray(soc.busses)) ? soc.busses : [];
    const stubColorClass = (proto) => {
      const x = (proto || '').toUpperCase();
      if (x === 'AXI' || x === 'AXI4' || x === 'AXI4L' || x === 'ACE') return 'acc';
      if (x === 'APB' || x === 'AHB') return 'magenta';
      if (x === 'IRQ') return 'warn';
      if (x === 'AXIS') return 'cyan';
      return '';
    };
    for (const cn of allBusses) {
      if (!cn || !cn.from || !cn.to) continue;
      const [aInst, aIface] = String(cn.from).split('/');
      const [bInst, bIface] = String(cn.to).split('/');
      const aLocal = localIds.has(aInst);
      const bLocal = localIds.has(bInst);
      if (aLocal === bLocal) continue; // both local → real wire above; both remote → not our problem
      const localInst  = aLocal ? aInst  : bInst;
      const localIface = aLocal ? aIface : bIface;
      const remoteInst = aLocal ? bInst  : aInst;
      const remoteIface= aLocal ? bIface : aIface;
      const remoteCluster = ipToCluster[remoteInst] || '?';
      const isOutgoing = aLocal; // local end is the master/from
      const part = partition(c.modules.find(x => x.id === localInst) || {});
      const pos = positions[localInst]; if (!pos) continue;
      const headerH = 24;
      // Try to find the matching iface row inside left/right partition
      const idxR = part.right.findIndex(x => x.name === localIface);
      const idxL = part.left.findIndex(x => x.name === localIface);
      const onRight = idxR >= 0 || (idxL < 0 && isOutgoing);
      const rows = Math.max(part.left.length, part.right.length, 2);
      const step = (pos.h - headerH - 12) / Math.max(rows, 1);
      const idx = onRight ? Math.max(idxR, 0) : Math.max(idxL, 0);
      const yPin = pos.y + headerH + 6 + step * (idx + 0.5);
      stubs.push({
        id: `stub-${localInst}-${localIface}-${remoteInst}-${remoteIface}`,
        x: onRight ? pos.x + pos.w + 6 : pos.x - 6,
        y: yPin,
        anchor: onRight ? 'left' : 'right',     // CSS positioning
        label: `${isOutgoing ? '→' : '←'} ${remoteCluster}/${remoteInst}/${remoteIface}`,
        proto: cn.proto || '',
      });
    }

    return (
      <React.Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {connections.length === 0 && layers.busses && (
            <>
              <line x1={60} y1={H/2} x2={W-60} y2={H/2} stroke={railColor} strokeWidth="3" opacity="0.4" />
              {c.modules.map(m => {
                const p = positions[m.id];
                return <line key={m.id} x1={p.x + p.w/2} y1={p.y + p.h/2} x2={p.x + p.w/2} y2={H/2} stroke={railColor} strokeWidth="1" opacity="0.3" strokeDasharray="3,3" />;
              })}
              {layers.labels && (
                <text x={70} y={H/2 - 6} fill="var(--fg-mute)" fontSize="10" fontFamily="var(--mono)" letterSpacing="0.1em">
                  no bus info — heuristic fallback
                </text>
              )}
            </>
          )}
          {/* Pin-to-pin orthogonal lines: H — V — H, with a small
              proto label hovering at the midpoint. */}
          {connections.map(co => {
            const midX = (co.x1 + co.x2) / 2;
            const midY = (co.y1 + co.y2) / 2;
            return (
              <g key={co.id}>
                <polyline
                  points={`${co.x1},${co.y1} ${midX},${co.y1} ${midX},${co.y2} ${co.x2},${co.y2}`}
                  stroke={co.color} strokeWidth="1.6" fill="none" opacity="0.85" />
                <circle cx={co.x1} cy={co.y1} r="2.5" fill={co.color} />
                <circle cx={co.x2} cy={co.y2} r="2.5" fill={co.color} />
                {layers.labels && co.proto && (
                  <g>
                    <rect x={midX - 14} y={midY - 7} width={28} height={12}
                          fill="var(--bg-2)" stroke={co.color} strokeWidth="0.5" opacity="0.9" />
                    <text x={midX} y={midY + 1} textAnchor="middle"
                          fill={co.color} fontSize="9" fontFamily="var(--mono)"
                          dominantBaseline="middle">{co.proto}</text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>

        {c.modules.map((m, i) => {
          const p = positions[m.id];
          const ref = `${c.id}/${m.id}`;
          const sel = selMod === ref;
          const touched = isTouched(ref);
          const { left, right, top, bottom } = partition(m);
          const familyClass = (proto) => {
            const x = (proto || '').toUpperCase();
            if (x === 'AXI' || x === 'AXI4') return 'proto-axi';
            if (x === 'AXI4L') return 'proto-axil';
            if (x === 'ACE') return 'proto-ace';
            if (x === 'AXIS') return 'proto-axis';
            if (x === 'APB') return 'proto-apb';
            if (x === 'AHB') return 'proto-ahb';
            if (x === 'IRQ') return 'proto-irq';
            if (x === 'CLK') return 'proto-clk';
            if (x === 'RST') return 'proto-rst';
            return '';
          };
          const arrowFor = (iface) => {
            const role = (iface.role || 'slave').toLowerCase();
            const proto = (iface.proto || '').toUpperCase();
            if (proto === 'CLK' || proto === 'RST') return '►'; // input
            if (proto === 'IRQ') return role === 'master' ? '↯' : '↯';
            return role === 'master' ? '►' : '◄';
          };
          // Carbon-style instance name: "<name>[0]"  with type in parens.
          const instLabel = `${m.name || m.id}[0]`;
          const typeLabel = m.label && m.label !== m.name ? `(${m.label})` :
                            m.kind ? `(${(window.MOD_KIND_LABEL || {})[m.kind] || m.kind})` : '';
          const centerGlyph = (window.MOD_ICON || {})[m.kind] || 'C';
          return (
            <div key={m.id} className={`bd-block with-ports ${m.kind || ''} ${sel ? 'sel' : ''} ${touched ? 'touched' : ''}`}
                 style={{ left: p.x, top: p.y, width: p.w, height: p.h }}
                 onClick={(e) => {
                   // Skip if this was the end of a drag — block-head's
                   // mouseup already handles the drag-stop, but a click
                   // on body still selects.
                   if (blockDragRef.current && blockDragRef.current.dragged) return;
                   e.stopPropagation(); setSelMod(ref);
                 }}
                 onDoubleClick={() => setView(`module:${ref}`)}>
              <div className="bd-block-head"
                   title="drag to move · double-click to drill in"
                   style={{ cursor: 'grab' }}
                   onMouseDown={(e) => {
                     // Start a block drag. We store the screen-space start
                     // and the block's stage-space base so mousemove can
                     // compute a delta divided by the current zoom scale.
                     // (Pan doesn't enter the math because pan is a
                     // sibling translate that affects screen coords by
                     // the same amount on both endpoints.)
                     e.stopPropagation();
                     const scale = zoom / 100;
                     blockDragRef.current = {
                       ref, scale, dragged: false,
                       startX: e.clientX, startY: e.clientY,
                       baseX: p.x, baseY: p.y,
                     };
                     e.currentTarget.style.cursor = 'grabbing';
                   }}
                   onMouseMove={(e) => {
                     const d = blockDragRef.current;
                     if (!d || d.ref !== ref) return;
                     const dx = (e.clientX - d.startX) / d.scale;
                     const dy = (e.clientY - d.startY) / d.scale;
                     if (Math.abs(dx) + Math.abs(dy) < 2) return; // dead zone
                     d.dragged = true;
                     setLayout(prev => ({ ...prev, [ref]: {
                       x: Math.max(0, Math.min(W - 60, d.baseX + dx)),
                       y: Math.max(0, Math.min(H - 30, d.baseY + dy)),
                     }}));
                   }}
                   onMouseUp={(e) => {
                     const d = blockDragRef.current;
                     if (!d || d.ref !== ref) return;
                     e.currentTarget.style.cursor = 'grab';
                     // Persist the new layout (only if user actually
                     // moved — pure click stays a click).
                     if (d.dragged) {
                       setLayout(prev => { persistLayout(prev); return prev; });
                     }
                     // Clear after the click handler sees `dragged`.
                     setTimeout(() => { blockDragRef.current = null; }, 0);
                   }}
                   onMouseLeave={(e) => {
                     // If the mouse leaves the head while dragging, stop
                     // — the canvas-level mouseup would clear it anyway,
                     // but this avoids a stuck grabbing cursor.
                     e.currentTarget.style.cursor = 'grab';
                   }}>
                <span className="nm-instance">{instLabel}</span>
                <span className="nm-type">{typeLabel}</span>
                <span style={{ flex: 1 }} />
                {touched && <span className="add-badge">+</span>}
                {m.status.sim === 'err' && <span style={{ color: 'var(--err)', fontSize: 11 }}>✗</span>}
                {m.addr && <span style={{ fontSize: 9, color: 'var(--cyan)', fontFamily: 'var(--mono)' }}>{(m.addr.split(' ')[0] || '').replace(/^0x/, '')}</span>}
              </div>
              {top.length > 0 && (
                <div className="bd-ports-edge top">
                  {top.map((iface, k) => (
                    <span key={`T${k}`} className={`bd-port top-side ${familyClass(iface.proto)}`}
                          title={`${iface.name} · ${iface.proto || ''} ${iface.role || ''}`}>
                      <span className="arr">{arrowFor(iface)}</span>
                      <span className="nm">{iface.name}</span>
                    </span>
                  ))}
                </div>
              )}
              <div className="bd-ports">
                <div className="bd-ports-col left">
                  {left.map((iface, k) => (
                    <span key={`L${k}`} className={`bd-port left-side ${familyClass(iface.proto)}`}>
                      <span className="arr">{arrowFor(iface)}</span>
                      <span className="nm">{iface.name}{iface.proto && iface.proto !== 'CLK' && iface.proto !== 'RST' ? ` ${(iface.role || '').slice(0,1).toUpperCase()}` : ''}</span>
                    </span>
                  ))}
                </div>
                <div className="bd-center-icon">{centerGlyph}</div>
                <div className="bd-ports-col right">
                  {right.map((iface, k) => (
                    <span key={`R${k}`} className={`bd-port right-side ${familyClass(iface.proto)}`}>
                      <span className="nm">{iface.name}{iface.proto ? ` ${(iface.role || '').slice(0,1).toUpperCase()}` : ''}</span>
                      <span className="arr">{arrowFor(iface)}</span>
                    </span>
                  ))}
                </div>
              </div>
              {bottom.length > 0 && (
                <div className="bd-ports-edge bottom">
                  {bottom.map((iface, k) => (
                    <span key={`B${k}`} className={`bd-port bottom-side ${familyClass(iface.proto)}`}
                          title={`${iface.name} · ${iface.proto || ''} ${iface.role || ''}`}>
                      <span className="arr">{arrowFor(iface)}</span>
                      <span className="nm">{iface.name}</span>
                    </span>
                  ))}
                </div>
              )}
              {layers.clk && <span className="clk-in-marker">▶ clk-in</span>}
            </div>
          );
        })}
        {stubs.map(st => (
          <div key={st.id} className={`bd-stub ${stubColorClass(st.proto)}`}
               style={{
                 left: st.anchor === 'left' ? st.x : undefined,
                 right: st.anchor === 'right' ? (W - st.x) : undefined,
                 top: st.y - 8,
                 transform: st.anchor === 'right' ? 'translateX(0)' : undefined,
               }}>
            {st.label}{st.proto && <span style={{ opacity: 0.7 }}> · {st.proto}</span>}
          </div>
        ))}
      </React.Fragment>
    );
  };

  const renderModuleView = (ref) => {
    const lkm = lookup[ref]; if (!lkm) return null;
    const m = lkm.module;
    const W = 1180, H = 720;
    const blockW = 480, blockH = 320;
    const bx = (W - blockW) / 2, by = (H - blockH) / 2;
    const ifaces = m.interfaces || [];
    return (
      <React.Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {layers.busses && ifaces.map((iface) => {
            const sameSide = ifaces.filter(x => x.side === iface.side);
            const idx = sameSide.indexOf(iface);
            const t = (idx + 1) / (sameSide.length + 1);
            let x1, y1, x2, y2;
            if (iface.side === 'left')         { x1 = bx - 80;        y1 = by + blockH * t; x2 = bx;             y2 = y1; }
            else if (iface.side === 'right')   { x1 = bx + blockW + 80; y1 = by + blockH * t; x2 = bx + blockW; y2 = y1; }
            else if (iface.side === 'top')     { x1 = bx + blockW * t; y1 = by - 80;          x2 = x1;          y2 = by; }
            else                                { x1 = bx + blockW * t; y1 = by + blockH + 80; x2 = x1;          y2 = by + blockH; }
            // Stroke color matches the cluster-view port-arrow palette:
            // AXI/ACE/AXI4L → blue accent, APB/AHB → magenta,
            // AXIS → cyan, IRQ → amber, CLK/RST → green.
            const _p = (iface.proto || '').toUpperCase();
            const color =
              (_p === 'AXI' || _p === 'AXI4' || _p === 'AXI4L' || _p === 'ACE') ? 'var(--accent)'
              : (_p === 'APB' || _p === 'AHB') ? 'var(--magenta)'
              : (_p === 'AXIS') ? 'var(--cyan)'
              : (_p === 'IRQ') ? 'var(--warn)'
              : (_p === 'CLK' || _p === 'RST') ? 'var(--ok)'
              : 'var(--fg-mute)';
            return (
              <g key={iface.name}>
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth="2" />
                <circle cx={x1} cy={y1} r="4" fill={color} />
                {layers.labels && (
                  <text x={iface.side === 'left' ? x1 - 6 : iface.side === 'right' ? x1 + 6 : x1}
                        y={iface.side === 'top' ? y1 - 6 : iface.side === 'bottom' ? y1 + 16 : y1 - 6}
                        fill="var(--fg-dim)" fontSize="10" fontFamily="var(--mono)"
                        textAnchor={iface.side === 'left' ? 'end' : iface.side === 'right' ? 'start' : 'middle'}>
                    {iface.name} · {iface.proto}{iface.role === 'master' ? ' M' : ' S'}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
        <div className="bd-block sel" style={{ left: bx, top: by, width: blockW, height: blockH }}>
          <div className="bd-block-head" style={{ padding: '10px 14px', fontSize: 14 }}>
            <span className="ico" style={{ fontSize: 16 }}>{window.MOD_ICON[m.kind]}</span>
            <span className="nm" style={{ fontSize: 16, color: 'var(--accent)' }}>{m.name}</span>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{window.MOD_KIND_LABEL[m.kind]}</span>
          </div>
          <div className="bd-block-body" style={{ padding: '12px 14px', justifyContent: 'flex-start', flexDirection: 'column', alignItems: 'stretch', gap: 10 }}>
            <div className="lbl" style={{ fontSize: 12, color: 'var(--fg-dim)' }}>{m.label}</div>
            {m.addr && <div className="addr" style={{ fontSize: 12 }}>addr · {m.addr}</div>}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
              {(m.params || []).map(p => (
                <span key={p.k} style={{ fontSize: 10, fontFamily: 'var(--mono)', padding: '2px 7px', background: 'var(--bg-3)', border: '1px solid var(--line)', color: 'var(--fg-dim)' }}>
                  {p.k}=<b style={{ color: 'var(--fg)' }}>{p.v}</b>
                </span>
              ))}
            </div>
            <div style={{ marginTop: 6, fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>pipeline</div>
            <window.PipelineStrip status={m.status} modId={m.id} big />
          </div>
        </div>
      </React.Fragment>
    );
  };

  return (
    <div className="arch-screen" data-dir="A" data-theme="dark">
      {/* Run bar (scope · stage triggers · totals).
          Each pipeline button switches the agent into the matching
          workflow via /workflow <name>. The user can then chat-prompt
          to actually execute the stage. pnr has no workflow yet, so
          its button is disabled. */}
      <div className="run-bar">
        <div className="grp">
          {window.PIPELINE_STAGES.map((s) => {
            const wfMap = { ssot: 'ssot-gen', rtl: 'rtl-gen', lint: 'lint',
                            sim: 'sim', syn: 'syn', sta: 'sta', pnr: '' };
            const wf = wfMap[s] || '';
            const onPipeClick = () => {
              if (!wf) return; // pnr (no workflow yet)
              setRunning(s);
              setTimeout(() => setRunning(null), 1100);
              if (window.backend) {
                // Switch workflow first; the slash dispatcher returns
                // immediately. The user follows up in chat to actually
                // execute the stage on the current scope.
                window.backend.send({ type: 'prompt', text: `/workflow ${wf}` });
              }
            };
            return (
              <button key={s}
                      className={`rb-btn ${s === 'sim' ? 'primary' : ''}`}
                      disabled={!wf}
                      title={wf ? `switch to /workflow ${wf}` : 'no workflow registered'}
                      onClick={onPipeClick}
                      style={!wf ? { opacity: 0.4, cursor: 'not-allowed' } : null}>
                <span className="icn">{running === s ? '◌' : '▶'}</span>{s}
              </button>
            );
          })}
        </div>
        <span className="rb-spacer" />
        <window.IpxactImportBtn onImported={() => refreshSoc()} />
        <span className="rb-meta">
          <span>modules · <b>{filteredRows.length}</b>{view !== 'soc' && <span style={{ color: 'var(--fg-mute)' }}> / {allRows.length}</span>}</span>
          <span>busses · <b>{(soc.busses || []).length}</b></span>
          <span style={{ color: 'var(--err)' }}>sim err · <b style={{ color: 'var(--err)' }}>{filteredRows.filter(r => r.module.status.sim === 'err').length}</b></span>
          <span style={{ color: 'var(--warn)' }}>partial · <b style={{ color: 'var(--warn)' }}>{filteredRows.filter(r => r.module.status.sim === 'partial').length}</b></span>
        </span>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '240px 1fr 480px', overflow: 'hidden' }}>
        {/* LEFT — hierarchy tree */}
        <div style={{ background: 'var(--panel)', borderRight: '1px solid var(--line)', overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
          <div className="box-h"><b>hierarchy</b><span style={{ flex: 1 }} /><span className="bd-sync">synced</span></div>
          {/* Search box: filters tree to clusters/modules whose id or
              name contains the query (case-insensitive). When a query
              is active, only matching modules are shown plus their
              parent clusters; matched substrings are highlighted. */}
          <div style={{ padding: '6px 8px', borderBottom: '1px solid var(--line)' }}>
            <input
              value={treeQuery}
              onChange={(e) => setTreeQuery(e.target.value)}
              placeholder="search IPs · ⌃F"
              style={{
                width: '100%', boxSizing: 'border-box',
                background: 'var(--bg-2)', border: '1px solid var(--line)',
                color: 'var(--fg)', font: '11px var(--mono)',
                padding: '4px 8px', outline: 'none', borderRadius: 2,
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape') { setTreeQuery(''); e.target.blur(); }
                else if (e.key === 'Enter' && treeMatches.length > 0) {
                  // Jump straight to first match.
                  const first = treeMatches[0];
                  setSelMod(first.ref); setView(`module:${first.ref}`);
                }
              }}
            />
          </div>
          <div className="bd-tree" style={{ padding: '6px 0', flex: 1 }}>
            <div className={`bd-tree-row ${view === 'soc' ? 'sel' : ''}`} onClick={() => setView('soc')}>
              <span className="tw">▼</span><span className="ico">⊞</span>
              <span style={{ flex: 1 }}>{soc.name || 'aurora_soc'}</span>
              <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{soc.version ? (soc.version.startsWith('v') ? soc.version : `v${soc.version}`) : 'v0.4.2'}</span>
            </div>
            {soc.clusters.map(c => {
              // When a query is active, only emit clusters that have
              // at least one matching module. Empty clusters are hidden.
              const visibleModules = treeQuery
                ? c.modules.filter(m => _matchesQuery(m, c.id, treeQuery))
                : c.modules;
              if (treeQuery && visibleModules.length === 0) return null;
              return (
              <React.Fragment key={c.id}>
                <div className={`bd-tree-row cluster ${view === `cluster:${c.id}` ? 'sel' : ''}`}
                     onClick={() => setView(`cluster:${c.id}`)} style={{ paddingLeft: 18 }}>
                  <span className="tw">▼</span>
                  <span className="ico">{c.id === 'cpu_ss' ? '◆' : c.id === 'mem_ss' ? '▦' : c.id === 'periph_ss' ? '⊟' : c.id === 'noc' ? '╫' : '∿'}</span>
                  <span style={{ flex: 1 }}>{c.id}</span>
                  <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{visibleModules.length}{treeQuery ? `/${c.modules.length}` : ''}</span>
                </div>
                {visibleModules.map(m => {
                  const ref = `${c.id}/${m.id}`;
                  const touched = isTouched(ref);
                  return (
                    <div key={ref} className={`bd-tree-row ${selMod === ref ? 'sel' : ''} ${touched ? 'touched' : ''}`}
                         onClick={() => { setSelMod(ref); if (view === 'soc') setView(`cluster:${c.id}`); }}
                         onDoubleClick={() => setView(`module:${ref}`)}
                         style={{ paddingLeft: 38 }}>
                      <span className="tw">·</span>
                      <span className="ico">{window.MOD_ICON[m.kind]}</span>
                      <span style={{ flex: 1, fontSize: 11.5, color: m.status.sim === 'err' ? 'var(--err)' : undefined }}
                            dangerouslySetInnerHTML={{ __html: _highlightMatch(m.name, treeQuery) }} />
                      {touched && <span style={{ background: 'var(--accent)', color: 'var(--bg)', fontSize: 8, padding: '1px 4px', fontWeight: 700 }}>+</span>}
                      <window.PipelineStrip status={m.status} modId={m.id} />
                    </div>
                  );
                })}
              </React.Fragment>
              );
            })}
            {treeQuery && treeMatches.length === 0 && (
              <div style={{ padding: '12px 14px', fontSize: 11,
                            color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                no IPs match "{treeQuery}"
              </div>
            )}
          </div>
          <div style={{ padding: 8, borderTop: '1px solid var(--line)', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.05em' }}>
            click → drill cluster · dbl-click → drill module
          </div>
        </div>

        {/* CENTER — tab bar + diagram or status */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'stretch', borderBottom: '1px solid var(--line)', background: 'var(--bg-2)' }}>
            <div style={{ display: 'flex' }}>
              {[
                { id: 'diagram', label: 'block diagram', icon: '◫' },
                { id: 'status',  label: 'status grid',  icon: '⊞' },
              ].map(t => (
                <button key={t.id}
                        onClick={() => setTab(t.id)}
                        className={`v8-tab ${tab === t.id ? 'sel' : ''}`}>
                  <span className="ic">{t.icon}</span>{t.label}
                </button>
              ))}
            </div>
            <div style={{ flex: 1, padding: '0 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="bd-crumb">
                {crumb.map((p, i) => (
                  <React.Fragment key={p.id}>
                    {i > 0 && <span className="sep">▸</span>}
                    <span className={`seg ${p.last ? 'last' : ''}`} onClick={() => !p.last && setView(p.target)}>{p.label}</span>
                  </React.Fragment>
                ))}
              </div>
              <span style={{ flex: 1 }} />
              {view !== 'soc' && (
                <button className="btn" style={{ fontSize: 10.5, padding: '3px 9px' }}
                        title="step up one level (module → cluster → soc)"
                        onClick={() => {
                          // Step up one level instead of jumping straight
                          // to soc, matching the breadcrumb depth.
                          if (view.startsWith('module:')) {
                            const ref = view.split(':')[1];
                            const lkv = lookup[ref];
                            if (lkv && lkv.cluster) setView(`cluster:${lkv.cluster.id}`);
                            else setView('soc');
                          } else {
                            setView('soc');
                          }
                        }}>↑ up</button>
              )}
            </div>
          </div>

          {tab === 'diagram' && (
            <div className="bd-canvas" style={{ flex: 1 }} ref={bdCanvasRef}
                 onWheel={(e) => {
                   // Cmd/Ctrl + wheel → zoom. Plain wheel → bubble up
                   // (for outer scroll if any). preventDefault on the
                   // zoom path so the page itself doesn't scroll.
                   if (!(e.ctrlKey || e.metaKey)) return;
                   e.preventDefault();
                   const delta = e.deltaY > 0 ? -8 : 8;
                   setZoom(z => Math.max(20, Math.min(200, z + delta)));
                 }}
                 onMouseDown={(e) => {
                   // Pan the stage by dragging on empty canvas. Skip
                   // when the click hit a block — those have their own
                   // click/drag semantics. Right-click also pans.
                   const onBlock = e.target.closest && e.target.closest('.bd-block');
                   if (onBlock && e.button === 0) return;
                   panDragRef.current = {
                     startX: e.clientX, startY: e.clientY,
                     baseX: pan.x, baseY: pan.y,
                   };
                   e.currentTarget.style.cursor = 'grabbing';
                 }}
                 onMouseMove={(e) => {
                   if (!panDragRef.current) return;
                   const d = panDragRef.current;
                   setPan({ x: d.baseX + (e.clientX - d.startX),
                            y: d.baseY + (e.clientY - d.startY) });
                 }}
                 onMouseUp={(e) => {
                   panDragRef.current = null;
                   e.currentTarget.style.cursor = '';
                 }}
                 onMouseLeave={(e) => {
                   panDragRef.current = null;
                   e.currentTarget.style.cursor = '';
                 }}
                 onDoubleClick={(e) => {
                   // Empty-canvas dblclick → reset pan. Block dblclick
                   // already drills into module-view (see bd-block).
                   const onBlock = e.target.closest && e.target.closest('.bd-block');
                   if (!onBlock) setPan({ x: 0, y: 0 });
                 }}>
              <div className="bd-layers">
                <div className="ttl">layers</div>
                {Object.keys(layers).map(k => (
                  <label key={k}>
                    <input type="checkbox" checked={layers[k]} onChange={() => toggleLayer(k)} /><span>{k}</span>
                  </label>
                ))}
              </div>
              <div className="bd-zoom">
                <button onClick={() => setZoom(z => Math.max(50, z - 10))}>−</button>
                <span className="pct">{zoom}%</span>
                <button onClick={() => setZoom(z => Math.min(200, z + 10))}>+</button>
                <button onClick={fitZoom} title="fit diagram to canvas">fit</button>
                <button onClick={async () => {
                          // Save current localStorage layout into
                          // soc.ssot.yaml's instances[].x/y. After save
                          // we keep the localStorage cache so reload
                          // fingerprints match; subsequent /api/soc
                          // fetches will pick up savedX/Y too.
                          if (!isLive) {
                            alert('Save needs a live soc.ssot.yaml — currently in mock mode.');
                            return;
                          }
                          try {
                            const r = await fetch('/api/soc/layout', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ layout }),
                            });
                            const d = await r.json().catch(() => ({}));
                            if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
                            // Re-fetch /api/soc so savedX/Y land on the
                            // module dicts (and the layout is now the
                            // canonical source of truth).
                            refreshSoc();
                            // brief visual confirm via the run-bar text
                            // or just a console hint — keep noise low.
                            console.info('[architect] layout saved →', d.path,
                                         '· touched:', d.touched, 'cleared:', d.cleared);
                          } catch (err) {
                            alert('Save failed: ' + (err.message || err));
                          }
                        }}
                        title="save dragged block positions into soc.ssot.yaml (instances[].x/y)"
                        style={{ borderLeft: '1px solid var(--line)',
                                 color: Object.keys(layout).length ? 'var(--accent)' : 'inherit',
                                 opacity: Object.keys(layout).length ? 1 : 0.4 }}>
                  save
                </button>
                <button onClick={() => {
                          if (Object.keys(layout).length === 0) return;
                          if (!confirm('Reset all dragged block positions to the auto-grid layout?')) return;
                          setLayout({}); persistLayout({});
                        }}
                        title="discard user-dragged block positions and revert to auto-grid"
                        style={{ borderLeft: '1px solid var(--line)',
                                 opacity: Object.keys(layout).length ? 1 : 0.4 }}>
                  reset
                </button>
              </div>
              <div className="bd-legend">
                <span className="swatch acc">AXI/ACE</span>
                <span className="swatch magenta">APB</span>
                <span className="swatch cyan">AXI4</span>
                <span className="swatch warn">analog/IRQ</span>
              </div>
              {/* Fixed virtual stage 1180×720. Both the SVG (viewBox
                  0 0 1180 720) and the block divs (raw px coordinates)
                  live in this stage so their coordinate frames agree.
                  The stage is centered + scaled to fit the available
                  bd-canvas area, then user zoom is multiplied on top. */}
              <div style={{ position: 'absolute', inset: 0, display: 'flex',
                            alignItems: 'center', justifyContent: 'center',
                            overflow: 'hidden' }}>
                <div className="bd-stage" style={{
                  position: 'relative',
                  width: 1180, height: 720,
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom/100})`,
                  transformOrigin: 'center center',
                  flex: '0 0 auto',
                  willChange: 'transform',
                }}>
                  {view === 'soc' && renderSocView()}
                  {view.startsWith('cluster:') && renderClusterView(view.split(':')[1])}
                  {view.startsWith('module:') && renderModuleView(view.split(':')[1])}
                </div>
              </div>
              {/* Mini-map (cluster view only — soc/module views don't
                  benefit since they're either a fixed 4-cluster layout
                  or a single big block). */}
              {miniOpen && view.startsWith('cluster:') && (() => {
                const cid = view.split(':')[1];
                const cc = soc.clusters.find(x => x.id === cid);
                if (!cc) return null;
                const W = 1180, H = 720;
                const mw = 180, mh = Math.round(mw * H / W);
                // Recompute positions the same way renderClusterView
                // does (auto-grid + layout overrides) so the mini-map
                // matches exactly.
                const cols = Math.min(3, cc.modules.length);
                const blockW = 220;
                const partition = (m) => {
                  const ifs = (m.interfaces || []);
                  let lc = 0, rc = 0;
                  for (const it of ifs) {
                    const r = (it.role || 'slave').toLowerCase();
                    const p = (it.proto || '').toUpperCase();
                    if (p === 'CLK' || p === 'RST') lc++;
                    else if (r === 'master') rc++;
                    else lc++;
                  }
                  return Math.max(lc, rc, 2);
                };
                const sizes = cc.modules.map(m => ({ h: 24 + Math.max(76, partition(m) * 14 + 24) }));
                const maxBlockH = Math.max(140, ...sizes.map(s => s.h));
                const rowsN = Math.ceil(cc.modules.length / cols);
                const gapX = Math.max(40, (W - cols * blockW) / (cols + 1));
                const gapY = Math.max(40, (H - rowsN * maxBlockH - 60) / (rowsN + 1));
                const sx = mw / W, sy = mh / H;
                return (
                  <div className="bd-minimap"
                       onMouseDown={(e) => {
                         // Click on minimap → pan stage so the click
                         // location maps to the canvas center.
                         const rect = e.currentTarget.getBoundingClientRect();
                         const xWorld = (e.clientX - rect.left) / sx;
                         const yWorld = (e.clientY - rect.top)  / sy;
                         const scale = zoom / 100;
                         setPan({
                           x: ((W / 2) - xWorld) * scale,
                           y: ((H / 2) - yWorld) * scale,
                         });
                         e.stopPropagation();
                       }}>
                    <div className="bd-minimap-head">
                      <span>map</span>
                      <span style={{ flex: 1 }} />
                      <span style={{ cursor: 'pointer' }}
                            onClick={(e) => { e.stopPropagation(); setMiniOpen(false); }}>×</span>
                    </div>
                    <div className="bd-minimap-body" style={{ width: mw, height: mh }}>
                      {cc.modules.map((m, i) => {
                        const ref = `${cc.id}/${m.id}`;
                        const ov = layout && layout[ref];
                        const col = i % cols, rIdx = Math.floor(i / cols);
                        const x = (ov && typeof ov.x === 'number') ? ov.x : gapX + col * (blockW + gapX);
                        const y = (ov && typeof ov.y === 'number') ? ov.y : 40 + gapY + rIdx * (maxBlockH + gapY);
                        const h = sizes[i].h;
                        const isSel = selMod === ref;
                        const tint = m.kind === 'cpu' ? 'var(--accent)'
                                   : m.kind === 'bus' ? 'var(--magenta)'
                                   : m.kind === 'mem' ? 'var(--cyan)'
                                   : m.kind === 'analog' ? 'var(--warn)'
                                   : 'var(--ok)';
                        return (
                          <div key={m.id}
                               title={m.name}
                               onClick={(ev) => { ev.stopPropagation(); setSelMod(ref); }}
                               onDoubleClick={(ev) => { ev.stopPropagation(); setView(`module:${ref}`); }}
                               style={{
                                 position: 'absolute',
                                 left: x * sx, top: y * sy,
                                 width: blockW * sx, height: h * sy,
                                 background: isSel ? tint : 'color-mix(in oklch, ' + tint + ' 30%, var(--bg-2))',
                                 border: '1px solid ' + (isSel ? 'var(--fg)' : tint),
                                 cursor: 'pointer',
                                 borderRadius: 1,
                               }} />
                        );
                      })}
                      {/* Viewport rectangle: shows what's currently
                          visible given pan + zoom. The visible region in
                          stage coords is centered at (W/2 - pan/scale,
                          H/2 - pan/scale) with size = canvas / scale. */}
                      {(() => {
                        const el = bdCanvasRef.current;
                        if (!el) return null;
                        const scale = zoom / 100;
                        const vw = (el.clientWidth || W) / scale;
                        const vh = (el.clientHeight || H) / scale;
                        const cx = W / 2 - pan.x / scale;
                        const cy = H / 2 - pan.y / scale;
                        const x = Math.max(0, cx - vw / 2);
                        const y = Math.max(0, cy - vh / 2);
                        const w = Math.min(W - x, vw);
                        const h = Math.min(H - y, vh);
                        return (
                          <div style={{
                            position: 'absolute',
                            left: x * sx, top: y * sy,
                            width: w * sx, height: h * sy,
                            border: '1.5px solid var(--accent)',
                            background: 'color-mix(in oklch, var(--accent) 8%, transparent)',
                            pointerEvents: 'none',
                            borderRadius: 1,
                          }} />
                        );
                      })()}
                    </div>
                  </div>
                );
              })()}
              {!miniOpen && view.startsWith('cluster:') && (
                <button className="bd-minimap-toggle"
                        onClick={(e) => { e.stopPropagation(); setMiniOpen(true); }}
                        title="show mini-map">map</button>
              )}
            </div>
          )}

          {tab === 'status' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ flex: 1, overflow: 'auto' }}>
                <table className="orch-grid">
                  <thead>
                    <tr>
                      <th style={{ width: 28 }}></th>
                      <th style={{ width: 180 }}>MODULE</th>
                      <th style={{ width: 120 }}>CLUSTER</th>
                      <th style={{ width: 80 }}>TYPE</th>
                      <th style={{ width: 140 }}>ADDR</th>
                      <th style={{ width: 200 }}>SSOT · RTL · SIM</th>
                      <th style={{ width: 96 }}>LAST RUN</th>
                      <th style={{ width: 80 }}>TESTS</th>
                      <th style={{ width: 56 }}>COV</th>
                      <th style={{ width: 56 }}>DUR</th>
                      <th style={{ width: 120 }}>TREND</th>
                      <th>NOTE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRows.map(r => {
                      const sel = selMod === r.ref;
                      const isErr = r.module.status.sim === 'err';
                      const touched = isTouched(r.ref);
                      const meta = runMeta(r.module);
                      const bars = sparkBars(r.module);
                      return (
                        <tr key={r.ref}
                            className={`orch-row ${sel ? 'sel' : ''} ${isErr ? 'errrow' : ''} ${touched ? 'touched' : ''}`}
                            onClick={() => setSelMod(r.ref)}
                            onDoubleClick={() => setView(`module:${r.ref}`)}>
                          <td className="g-mark">
                            {touched ? <span className="g-add">+</span> : sel ? <span style={{ color: 'var(--accent)' }}>▸</span> : ''}
                          </td>
                          <td>
                            <span className="g-mod-ico">{window.MOD_ICON[r.module.kind]}</span>
                            <b className="g-mod-nm">{r.module.name}</b>
                          </td>
                          <td className="g-clu">{r.cluster.id}</td>
                          <td><span className="g-kind">{window.MOD_KIND_LABEL[r.module.kind]}</span></td>
                          <td className="g-addr">{r.module.addr || <span style={{ color: 'var(--fg-mute)' }}>—</span>}</td>
                          <td><window.StatusTrio status={r.module.status} big /></td>
                          <td className="g-tnum">{meta.t}</td>
                          <td className="g-tnum" style={{ color: isErr ? 'var(--err)' : meta.tests === '—' ? 'var(--fg-mute)' : 'var(--fg-dim)' }}>{meta.tests}</td>
                          <td className="g-tnum" style={{ color: meta.cov === '—' ? 'var(--fg-mute)' : isErr ? 'var(--warn)' : 'var(--ok)' }}>{meta.cov}</td>
                          <td className="g-tnum" style={{ color: 'var(--fg-mute)' }}>{meta.dur}</td>
                          <td onMouseEnter={(e) => {
                                 // Anchor popover to the cell so it
                                 // tracks horizontal scroll inside the
                                 // grid container.
                                 const rect = e.currentTarget.getBoundingClientRect();
                                 setSparkPop({ ref: r.ref, x: rect.right + 4, y: rect.top });
                               }}
                               onMouseLeave={() => setSparkPop(prev => prev && prev.ref === r.ref ? null : prev)}>
                            {bars.length === 0 ? (
                              <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>—</span>
                            ) : (
                              <svg width={Math.max(40, bars.length * 11)} height="18" style={{ display: 'block' }}>
                                {bars.map((h, i) => (
                                  <rect key={i} x={i * 11} y={18 - h} width={8} height={h}
                                        fill={isErr && i === bars.length - 1 ? 'var(--err)'
                                            : i === bars.length - 1 ? (r.module.status.sim === 'ok' ? 'var(--ok)' : r.module.status.sim === 'partial' ? 'var(--warn)' : 'var(--fg-mute)')
                                            : 'var(--line-2)'} />
                                ))}
                              </svg>
                            )}
                          </td>
                          <td className="g-note">
                            {isErr ? <span className="err">✗ test_back_to_back · mosi=X at t=110ns</span>
                              : r.module.status.sim === 'partial' ? <span className="warn">◐ 2 tests skipped</span>
                              : r.module.status.sim === 'pending' ? <span style={{ color: 'var(--fg-mute)' }}>○ never run</span>
                              : touched ? <span className="acc">+ added by agent · 12:04:21</span>
                              : <span style={{ color: 'var(--fg-mute)' }}>—</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {selModule && (
                <div style={{ flex: '0 0 320px', borderTop: '1px solid var(--line)', background: 'var(--panel)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                  <div className="box-h">
                    <span style={{ color: 'var(--fg-mute)' }}>{(soc.name || 'aurora_soc') + '/'}</span>
                    <b>{selModule.name}.ssot.yaml</b>
                    <span style={{ flex: 1 }} />
                    <window.StatusTrio status={selModule.status} />
                    <span className="pill ok" style={{ fontSize: 9, marginLeft: 8 }}>synced</span>
                  </div>
                  <div style={{ flex: 1, overflow: 'auto' }}>
                    <pre className="code-pane" style={{ margin: 0, height: '100%', fontSize: 11.5 }}>
{selModule.id === 'spi' && soc.ssotYamlSpi ? soc.ssotYamlSpi : `# ${selModule.name}.ssot.yaml — generated
component:
  vendor:  atlas.io
  library: ${selCluster.id}
  name:    ${selModule.name}
  version: 0.1.0

parameters:
${(selModule.params || []).map(p => `  - { name: ${p.k.toUpperCase().padEnd(8)}, value: ${p.v} }`).join('\n')}

busInterfaces:
${(selModule.interfaces || []).map(i => `  - { name: ${i.name}, proto: ${i.proto}, role: ${i.role}, side: ${i.side} }`).join('\n')}
${selModule.addr ? `
memoryMap:
  - { name: regs, base: ${selModule.addr.split(' ')[0]}, range: 0x1000 }
` : ''}`}</pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT — chat (live · routes prompts to the same WS bridge
            the Workspace screen uses). */}
        <window.ArchitectChat view={view} selModule={selModule} selCluster={selCluster} />
      </div>

      {/* Sparkline hover popover — full sim_history of the hovered IP.
          Position-fixed so it can spill out of the grid container. */}
      {sparkPop && (() => {
        const lk = lookup[sparkPop.ref]; if (!lk) return null;
        const m = lk.module;
        const hist = Array.isArray(m.sim_history) ? m.sim_history : [];
        return (
          <div style={{
            position: 'fixed', left: sparkPop.x, top: sparkPop.y,
            zIndex: 1000, pointerEvents: 'none',
            background: 'var(--panel)', border: '1px solid var(--line-2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
            font: '11px var(--mono)', minWidth: 280, maxWidth: 380,
          }}>
            <div style={{ padding: '6px 10px', background: 'var(--bg-2)',
                          borderBottom: '1px solid var(--line)',
                          fontSize: 10, color: 'var(--fg-mute)',
                          letterSpacing: '0.08em', textTransform: 'uppercase',
                          display: 'flex', gap: 8 }}>
              <b style={{ color: 'var(--accent)' }}>{m.name}</b>
              <span style={{ flex: 1 }} />
              <span>sim · {hist.length} run{hist.length === 1 ? '' : 's'}</span>
            </div>
            {hist.length === 0 ? (
              <div style={{ padding: '12px 10px', color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                no sim history yet ·{' '}
                <span style={{ color: 'var(--fg-dim)' }}>
                  populated when {'<'}ip{'>'}/sim/history.json exists
                </span>
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10.5 }}>
                <thead>
                  <tr style={{ color: 'var(--fg-mute)' }}>
                    <th style={{ textAlign: 'left', padding: '4px 8px', fontWeight: 500 }}>WHEN</th>
                    <th style={{ textAlign: 'right', padding: '4px 8px', fontWeight: 500 }}>TESTS</th>
                    <th style={{ textAlign: 'right', padding: '4px 8px', fontWeight: 500 }}>COV</th>
                    <th style={{ textAlign: 'right', padding: '4px 8px', fontWeight: 500 }}>DUR</th>
                    <th style={{ textAlign: 'right', padding: '4px 8px', fontWeight: 500 }}>RES</th>
                  </tr>
                </thead>
                <tbody>
                  {hist.slice().reverse().map((r, i) => {
                    const sc = r.status === 'ok' ? 'var(--ok)'
                             : r.status === 'partial' ? 'var(--warn)'
                             : r.status === 'err' ? 'var(--err)' : 'var(--fg-mute)';
                    const sym = r.status === 'ok' ? '✓'
                              : r.status === 'partial' ? '◐'
                              : r.status === 'err' ? '✗' : '○';
                    return (
                      <tr key={i} style={{ borderTop: i ? '1px solid var(--line)' : 'none' }}>
                        <td style={{ padding: '3px 8px', color: 'var(--fg-dim)' }}>{r.t || '—'}</td>
                        <td style={{ padding: '3px 8px', textAlign: 'right' }}>{r.tests || '—'}</td>
                        <td style={{ padding: '3px 8px', textAlign: 'right' }}>{r.cov || '—'}</td>
                        <td style={{ padding: '3px 8px', textAlign: 'right', color: 'var(--fg-mute)' }}>{r.dur || '—'}</td>
                        <td style={{ padding: '3px 8px', textAlign: 'right', color: sc }}>{sym}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        );
      })()}
    </div>
  );
};

// ── ArchitectChat — minimal live chat panel ────────────────────
// Shares the same WebSocket bridge (`window.backend`) as Workspace,
// so prompts go through the same react-loop and tokens stream back.
// Renders only token / reasoning / tool / tool_result events; the
// full feed (with collapsible cards, qcards, slash menu, scope etc.)
// stays on the Workspace screen.
window.ArchitectChat = function ArchitectChat({ view, selModule, selCluster }) {
  const [feed, setFeed] = React.useState([]);
  const [streaming, setStreaming] = React.useState(false);
  const [input, setInput] = React.useState('');
  const bufRef = React.useRef('');
  const feedRef = React.useRef(null);

  // Subscribe to the live WS once on mount.
  React.useEffect(() => {
    if (!window.backend || typeof window.backend.subscribe !== 'function') return;
    const subs = [];
    subs.push(window.backend.subscribe('token', (m) => {
      bufRef.current += (m.text || '');
    }));
    subs.push(window.backend.subscribe('reasoning', (m) => {
      const t = (m.text || '').trim(); if (!t) return;
      setFeed(l => {
        const last = l[l.length - 1];
        if (last && last.kind === 'thought') {
          return [...l.slice(0, -1), { kind: 'thought', text: last.text + '\n' + t }];
        }
        return [...l, { kind: 'thought', text: t }];
      });
    }));
    subs.push(window.backend.subscribe('tool', (m) => {
      const t = (m.text || '').trim(); if (!t) return;
      // Park any pending tokens before the tool entry.
      const buf = bufRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf }]);
      bufRef.current = '';
      setFeed(l => [...l, { kind: 'action', text: t }]);
    }));
    subs.push(window.backend.subscribe('tool_result', (m) => {
      const t = (m.text || '').trim(); if (!t) return;
      setFeed(l => [...l, { kind: 'obs', text: t.slice(0, 1200), tool: m.tool || '' }]);
    }));
    const park = () => {
      const buf = bufRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf }]);
      bufRef.current = '';
    };
    subs.push(window.backend.subscribe('flush', park));
    subs.push(window.backend.subscribe('done', () => { park(); setStreaming(false); }));
    subs.push(window.backend.subscribe('agent_state', (m) => {
      if (m.running === false) { park(); setStreaming(false); }
      else if (m.running === true) setStreaming(true);
    }));
    subs.push(window.backend.subscribe('error', (m) => {
      setFeed(l => [...l, { kind: 'agent', text: `[error] ${m.message || ''}` }]);
      setStreaming(false);
    }));
    return () => subs.forEach(u => { try { u(); } catch (_) {} });
  }, []);

  // Auto-scroll to bottom on new entries.
  React.useEffect(() => {
    const el = feedRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [feed.length]);

  const send = () => {
    const text = input.trim();
    if (!text) return;
    setFeed(l => [...l, { kind: 'user', text }]);
    setInput('');
    setStreaming(true);
    // Mirror Workspace's scope-prefix behaviour: when an IP scope is
    // active (set automatically by drilling into a module on the
    // diagram), prepend a directive so the agent confines its tools
    // to that directory. Slash commands and short confirmations
    // bypass the prefix.
    const isConfirmation = /^(y|yc|yes|n|no|confirm|cancel|ok|proceed)$/i.test(text);
    const scope = (window.SCOPE_PATH || '').trim();
    let outbound = text;
    if (scope && !text.startsWith('/') && !isConfirmation) {
      outbound = (
        `[scope] You MUST confine every file read, write, edit, grep, ` +
        `find, and run_command to paths inside "${scope}". Do not touch ` +
        `files outside this directory unless I explicitly say so.\n\n` +
        text
      );
    }
    if (window.backend) window.backend.send({ type: 'prompt', text: outbound });
  };
  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const scopeLabel = view === 'soc' ? 'soc · architect'
                   : selModule ? `${selModule.name} · module`
                   : selCluster ? `${selCluster.id} · cluster`
                   : view.replace(':', ' · ');

  return (
    <div style={{ background: 'var(--panel)', borderLeft: '1px solid var(--line)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="box-h">
        <b>chat · architect</b>
        <span style={{ flex: 1 }} />
        <span className={`pill ${streaming ? 'run' : 'acc'}`} style={{ fontSize: 9 }}>
          {streaming ? 'react-loop · streaming' : 'react-loop · idle'}
        </span>
      </div>

      <div ref={feedRef} style={{ flex: 1, overflow: 'auto', padding: 14, fontSize: 12.5 }}>
        {feed.length === 0 && (
          <div style={{ color: 'var(--fg-mute)', fontSize: 11, fontStyle: 'italic', lineHeight: 1.6 }}>
            ask the agent to inspect the SoC, validate addresses, or scaffold a new IP.
            prompts go through the same react-loop as the Workspace screen.
          </div>
        )}
        {feed.map((entry, i) => {
          if (entry.kind === 'user') {
            return (
              <div key={i} style={{ background: 'var(--bg-2)', border: '1px solid var(--line)', padding: '6px 10px', margin: '4px 0 10px', whiteSpace: 'pre-wrap' }}>
                <span className="acc" style={{ fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', marginRight: 6 }}>you</span>
                {entry.text}
              </div>
            );
          }
          if (entry.kind === 'agent') {
            return (
              <div key={i} style={{ padding: '4px 0 10px', whiteSpace: 'pre-wrap', lineHeight: 1.55 }}>
                <span className="ok" style={{ fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', marginRight: 6 }}>agent</span>
                {entry.text}
              </div>
            );
          }
          if (entry.kind === 'thought') {
            return (
              <div key={i} className="react-block thought" style={{ opacity: 0.75 }}>
                <span className="rb-tag">thought</span>
                <span style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</span>
              </div>
            );
          }
          if (entry.kind === 'action') {
            return (
              <div key={i} className="react-block action">
                <span className="rb-tag">tool</span>
                <span style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</span>
              </div>
            );
          }
          if (entry.kind === 'obs') {
            return (
              <div key={i} className="react-block obs">
                <span className="rb-tag">obs{entry.tool ? ` · ${entry.tool}` : ''}</span>
                <span style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</span>
              </div>
            );
          }
          return null;
        })}
      </div>

      <div style={{ padding: 10, borderTop: '1px solid var(--line)', background: 'var(--panel)' }}>
        <div className="prompt-row">
          <span className="ps">›</span>
          <input value={input}
                 onChange={e => setInput(e.target.value)}
                 onKeyDown={onKey}
                 placeholder="ask the agent · scope follows the diagram drill" />
          <span className="kbd" onClick={send} style={{ cursor: 'pointer' }}>↵</span>
        </div>
        <div style={{ marginTop: 6, display: 'flex', gap: 6, fontSize: 10, color: 'var(--fg-mute)', alignItems: 'center' }}>
          <span>scope</span>
          <span className="pill acc" style={{ fontSize: 9 }}>{scopeLabel}</span>
          <span style={{ flex: 1 }} />
          <span><span className="kbd">↵</span> send</span>
        </div>
      </div>
    </div>
  );
};

// ── IpxactImportBtn — IP-XACT XML uploader ────────────────────
// Opens a hidden file input, uploads the XML to /api/ipxact/import,
// then triggers a refresh on the parent so the new IP appears in
// the architect tree + diagram + grid immediately.
window.IpxactImportBtn = function IpxactImportBtn({ onImported }) {
  const fileRef = React.useRef(null);
  const [busy, setBusy] = React.useState(false);
  const [msg, setMsg] = React.useState("");
  const onClick = () => { if (fileRef.current && !busy) fileRef.current.click(); };
  const onPick = async (e) => {
    const f = e.target.files && e.target.files[0];
    e.target.value = ""; // allow re-picking the same file
    if (!f) return;
    setBusy(true); setMsg("uploading…");
    try {
      // architect-aware: ensure the supervisor workflow is active
      // before importing so the agent can react (suggest scaffold,
      // run addrmap_check, etc.). app.jsx auto-switches when entering
      // the Architect screen, but if the user is here mid-session
      // and the workflow drifted (e.g. via /workflow rtl-gen) we
      // nudge it back. No-op when already on architect.
      if (window.backend && typeof window.backend.send === 'function') {
        window.backend.send({ type: 'prompt', text: '/workflow architect' });
      }
      const fd = new FormData();
      fd.append("xml", f, f.name);
      const r = await fetch("/api/ipxact/import", { method: "POST", body: fd });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
      setMsg(`✓ imported ${d.name} → ${d.path}`);
      // Tell the architect agent so it can suggest next steps
      // (add to soc.ssot.yaml, addr conflict check, scaffold).
      if (window.backend && typeof window.backend.send === 'function') {
        window.backend.send({
          type: 'prompt',
          text: `IP-XACT just imported: ${d.name} → ${d.path}. ` +
                `Add it to soc.ssot.yaml under an appropriate cluster, ` +
                `then run addrmap_check.`,
        });
      }
      if (typeof onImported === "function") onImported();
    } catch (err) {
      setMsg(`✗ ${err.message || err}`);
    } finally {
      setBusy(false);
      setTimeout(() => setMsg(""), 4000);
    }
  };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, marginRight: 12 }}>
      <input ref={fileRef} type="file" accept=".xml" style={{ display: "none" }} onChange={onPick} />
      <button className="rb-btn" onClick={onClick} disabled={busy}
              title="Convert an IP-XACT (IEEE 1685) XML file into our SSOT YAML"
              style={busy ? { opacity: 0.5 } : null}>
        <span className="icn">{busy ? "◌" : "⇪"}</span>import IP-XACT
      </button>
      {msg && (
        <span style={{ fontSize: 10, fontFamily: "var(--mono)",
                       color: msg.startsWith("✓") ? "var(--ok)" : msg.startsWith("✗") ? "var(--err)" : "var(--fg-mute)",
                       maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {msg}
        </span>
      )}
    </span>
  );
};

