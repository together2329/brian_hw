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
  display: flex; align-items: flex-start; gap: 10px;
}
.arch-screen .run-bar .grp { display: flex; flex-wrap: wrap; gap: 1px; min-width: 0; }
.arch-screen .run-bar .rb-btn {
  background: var(--bg-2); border: 1px solid var(--line);
  color: var(--fg-dim); padding: 4px 10px;
  font-family: var(--mono); font-size: 11px;
  cursor: pointer; display: inline-flex; align-items: center; gap: 5px;
  white-space: nowrap;
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
.arch-splitter {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 9px;
  z-index: 20;
  cursor: col-resize;
  background: transparent;
}
.arch-splitter::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 4px;
  width: 1px;
  background: transparent;
}
.arch-splitter:hover::after {
  background: var(--accent);
  box-shadow: 0 0 0 1px color-mix(in oklch, var(--accent) 20%, transparent);
}
.arch-splitter.left { right: -5px; }
.arch-splitter.right { left: -5px; }

/* ── Block-diagram canvas (V7) ───────────────────────────────── */
.bd-canvas {
  position: relative; flex: 1; overflow: hidden;
  background:
    radial-gradient(circle at 1px 1px, color-mix(in oklch, var(--line) 80%, transparent) 1px, transparent 0) 0 0/24px 24px,
    var(--bg);
}
[data-theme="light"] .bd-canvas.soc-carbon {
  background:
    linear-gradient(#e7ebf0 1px, transparent 1px) 0 0/18px 18px,
    linear-gradient(90deg, #e7ebf0 1px, transparent 1px) 0 0/18px 18px,
    linear-gradient(#d7dde5 1px, transparent 1px) 0 0/90px 90px,
    linear-gradient(90deg, #d7dde5 1px, transparent 1px) 0 0/90px 90px,
    #fbfcfe;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-layers,
[data-theme="light"] .bd-canvas.soc-carbon .bd-legend {
  background: rgba(255,255,255,0.86);
  border-color: #d6dbe2;
  color: #4a5568;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-zoom {
  background: rgba(255,255,255,0.9);
  border-color: #d6dbe2;
  color: #2d3748;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-zoom button {
  color: #2d3748;
  border-color: #d6dbe2;
}
[data-theme="light"] .bd-canvas.soc-carbon .soc-wire-label {
  fill: #fbfcfe;
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
/* Cluster card tinted per kind so the SoC overview reads CPU vs BUS
   vs MEM at a glance. Same palette as bd-block.with-ports kind colors
   used inside cluster view. */
.bd-block.cluster.cpu {
  background: color-mix(in oklch, var(--accent) 8%, var(--panel));
  border-color: color-mix(in oklch, var(--accent) 50%, var(--line-2));
}
.bd-block.cluster.cpu .ico { color: var(--accent); }
.bd-block.cluster.bus {
  background: color-mix(in oklch, var(--magenta) 10%, var(--panel));
  border-color: color-mix(in oklch, var(--magenta) 50%, var(--line-2));
}
.bd-block.cluster.bus .ico { color: var(--magenta); }
.bd-block.cluster.mem {
  background: color-mix(in oklch, var(--cyan) 8%, var(--panel));
  border-color: color-mix(in oklch, var(--cyan) 50%, var(--line-2));
}
.bd-block.cluster.mem .ico { color: var(--cyan); }
.bd-block.cluster.periph {
  background: color-mix(in oklch, var(--ok) 8%, var(--panel));
  border-color: color-mix(in oklch, var(--ok) 50%, var(--line-2));
}
.bd-block.cluster.periph .ico { color: var(--ok); }
.bd-block.cluster.analog {
  background: color-mix(in oklch, var(--warn) 10%, var(--panel));
  border-color: color-mix(in oklch, var(--warn) 50%, var(--line-2));
}
.bd-block.cluster.analog .ico { color: var(--warn); }
/* Legacy .bd-block.noc — kept for backwards-compat; cluster.bus
   class above wins for new code paths but this still applies when
   the kind isn't recognised. */
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
.bd-block.with-ports.soc-top { cursor: grab; }
.bd-block.with-ports.soc-top:active { cursor: grabbing; }
.bd-block.with-ports {
  user-select: none;
}
.bd-block.with-ports.soc-top .bd-ports {
  grid-template-columns: 1fr 18px 1fr;
  padding: 9px 0 10px;
}
.bd-block.with-ports.soc-top .bd-ports-col {
  font-size: 10px;
  gap: 3px;
}
.bd-block.with-ports.soc-top .bd-port {
  padding: 1px 6px;
  font-weight: 500;
}
.bd-block.with-ports.soc-top .bd-port .proto-badge {
  margin-left: 4px;
  padding: 0 3px;
  border: 1px solid currentColor;
  font-size: 8px;
  line-height: 1.15;
  opacity: 0.92;
}
.bd-block.with-ports.soc-top .bd-port.right-side .proto-badge {
  margin-left: 0;
  margin-right: 4px;
}
.bd-block.with-ports.soc-top .bd-center-icon {
  width: 18px; height: 24px;
  font-size: 0;
  opacity: 0;
  border-color: transparent;
  background: transparent;
}
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
.bd-block.with-ports.soc-top .bd-port.proto-axi,
.bd-block.with-ports.soc-top .bd-port.proto-axil,
.bd-block.with-ports.soc-top .bd-port.proto-ace {
  color: var(--accent);
}
.bd-block.with-ports.soc-top .bd-port.proto-apb,
.bd-block.with-ports.soc-top .bd-port.proto-ahb {
  color: var(--magenta);
}
.bd-block.with-ports.soc-top .bd-port.proto-irq {
  color: var(--warn);
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
  cursor: crosshair;
}
.bd-block.with-ports .bd-port:hover { color: var(--fg); }
.bd-block.with-ports .bd-port.connecting {
  outline: 1px solid var(--accent);
  background: color-mix(in oklch, var(--accent) 22%, transparent);
  color: var(--fg);
}
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
  width: 6px; height: 2px; background: currentColor;
}
.bd-block.with-ports .bd-port.right-side::after {
  content: ''; position: absolute; right: -3px; top: 50%;
  width: 6px; height: 2px; background: currentColor;
}

/* Top SoC diagram in a Carbon/EDA-document style: bright paper,
   square white components, black orthogonal wires, minimal chrome. */
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top {
  background: #fff;
  border: 1px solid #8b96a3;
  box-shadow: 0 1px 0 rgba(15,23,42,0.08);
  color: #1f2933;
  border-radius: 0;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top.cpu {
  border-color: #2f6fd0;
  box-shadow: inset 3px 0 0 #2f6fd0, 0 1px 0 rgba(15,23,42,0.08);
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top.bus,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top.noc {
  border-color: #8b4bb3;
  box-shadow: inset 3px 0 0 #8b4bb3, 0 1px 0 rgba(15,23,42,0.08);
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top.mem {
  border-color: #168395;
  box-shadow: inset 3px 0 0 #168395, 0 1px 0 rgba(15,23,42,0.08);
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top.periph {
  border-color: #2f8a5b;
  box-shadow: inset 3px 0 0 #2f8a5b, 0 1px 0 rgba(15,23,42,0.08);
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top:hover,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top.sel {
  border-color: #1d4ed8;
  box-shadow: inset 3px 0 0 #1d4ed8, 0 0 0 1px #1d4ed8, 0 4px 14px rgba(29,78,216,0.13);
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-block-head {
  background: #f6f8fb;
  border-bottom: 1px solid #9aa4b0;
  color: #111827;
  min-height: 22px;
  font-size: 11px;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .nm-instance {
  color: #111827;
  font-weight: 700;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .nm-type {
  color: #273244;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-axi,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-axil,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-ace {
  color: #1f5fcc;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-apb,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-ahb {
  color: #8a3ea0;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-irq {
  color: #a87212;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port:hover,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.connecting {
  color: #111827;
  background: #e8f0ff;
  outline-color: #1d4ed8;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-axi .proto-badge,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-axil .proto-badge,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-ace .proto-badge {
  color: #1f5fcc;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-apb .proto-badge,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-ahb .proto-badge {
  color: #8a3ea0;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.proto-irq .proto-badge {
  color: #a87212;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-center-icon {
  border-color: transparent;
  background: transparent;
  opacity: 0;
}
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.left-side::before,
[data-theme="light"] .bd-canvas.soc-carbon .bd-block.soc-top .bd-port.right-side::after {
  background: currentColor;
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
.seg-tabs {
  display: inline-flex; align-items: center; gap: 1px;
  border: 1px solid var(--line);
  background: var(--bg-2);
  font-family: var(--mono); font-size: 10px;
}
.seg-tabs button {
  border: 0; background: transparent; color: var(--fg-dim);
  padding: 3px 8px; cursor: pointer;
  font-family: inherit; font-size: inherit; text-transform: uppercase;
}
.seg-tabs button:hover { color: var(--fg); background: var(--bg-3); }
.seg-tabs button.sel { color: var(--accent); background: var(--select); }

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
.pl-dot.planned { background: color-mix(in oklch, var(--accent) 45%, var(--line-2)); }
.pl-dot.approved { background: color-mix(in oklch, var(--ok) 70%, var(--warn)); }
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

/* ── Block ⚡ dispatch button + running pill ───────────────────── */
.bd-dispatch-btn {
  background: transparent; border: 0; cursor: pointer;
  color: var(--fg-mute); font-size: 11px;
  padding: 0 4px; line-height: 1;
  transition: color .12s, transform .12s;
}
.bd-dispatch-btn:hover { color: var(--warn); transform: scale(1.2); }
.bd-running-pill {
  font-size: 9px; color: var(--cyan); font-family: var(--mono);
  letter-spacing: 0.04em;
  padding: 1px 5px;
  background: color-mix(in oklch, var(--cyan) 12%, transparent);
  border: 1px solid color-mix(in oklch, var(--cyan) 50%, var(--line));
  border-radius: 1px;
  animation: plBlink 1.2s ease-in-out infinite;
}
.bd-block.with-ports.job-running {
  box-shadow: 0 0 0 1px var(--cyan), 0 0 22px color-mix(in oklch, var(--cyan) 35%, transparent);
  border-color: var(--cyan);
}
.bd-dispatch-item {
  padding: 5px 10px; cursor: pointer;
  display: flex; align-items: center; gap: 8px;
  color: var(--fg-dim);
  border-bottom: 1px solid var(--line);
}
.bd-dispatch-item:last-child { border-bottom: 0; }
.bd-dispatch-item:hover { background: var(--bg-2); color: var(--accent); }

/* ── JobTracker panel ───────────────────────────────────────── */
.job-tracker {
  border-bottom: 1px solid var(--line);
  background: var(--bg-2);
  font-family: var(--mono);
  display: flex; flex-direction: column;
  flex: 0 0 auto;
  max-height: 220px; overflow: hidden;
}
.job-tracker-head {
  padding: 4px 10px; background: var(--bg-3);
  font-size: 10px; color: var(--fg-mute);
  letter-spacing: 0.08em; text-transform: uppercase;
  display: flex; align-items: center; gap: 8px;
  cursor: pointer;
  border-bottom: 1px solid var(--line);
}
.job-tracker-head:hover { color: var(--fg); }
.job-tracker-head .badge {
  font-size: 9px; padding: 0 5px; border-radius: 1px;
  background: var(--accent); color: var(--bg); font-weight: 700;
}
.job-tracker-list {
  flex: 1; overflow: auto; padding: 4px 0;
}
.job-row {
  display: grid;
  grid-template-columns: 18px 1fr 80px 60px 16px;
  gap: 6px; align-items: center;
  padding: 4px 10px; font-size: 10.5px; color: var(--fg-dim);
  cursor: pointer; border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
.job-row:last-child { border-bottom: 0; }
.job-row:hover { background: color-mix(in oklch, var(--accent) 6%, transparent); }
.job-row .icn { text-align: center; font-size: 11px; }
.job-row.running .icn { color: var(--cyan); animation: plBlink 1s infinite; }
.job-row.completed .icn { color: var(--ok); }
.job-row.error .icn { color: var(--err); }
.job-row.cancelled .icn { color: var(--fg-mute); }
.job-row.queued .icn { color: var(--fg-mute); }
.job-row.blocked .icn { color: var(--warn); }
.job-row .ip { color: var(--fg); font-weight: 500; }
.job-row .wf { color: var(--accent); font-size: 10px; padding: 0 4px;
               background: color-mix(in oklch, var(--accent) 10%, transparent);
               border: 1px solid color-mix(in oklch, var(--accent) 30%, var(--line));
               border-radius: 1px; }
.job-row .meta { color: var(--fg-mute); font-size: 9.5px; text-align: right; }
.job-row .x {
  color: var(--fg-mute); cursor: pointer; opacity: 0;
  transition: opacity .12s;
}
.job-row:hover .x { opacity: 1; }
.job-row .x:hover { color: var(--err); }
`;
  document.head.appendChild(s);
})();

const normalizeArchitectSession = (session) => {
  const norm = (window.atlasData && window.atlasData.normalizeSessionName) || window.normalizeAtlasSessionName;
  try { return norm ? norm(session || '') : ''; }
  catch (_) { return ''; }
};

// Pipeline strip shared by V6 grid + V7 diagram. Same logic as the
// upstream zip; lives here because soc-shared.jsx doesn't ship it.
window.PIPELINE_STAGES = [
  'ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb',
  'sim', 'coverage', 'sim-debug', 'syn', 'sta', 'pnr', 'sta-post', 'goal-audit',
];
window.PIPELINE_LABEL = {
  ssot: 'SSOT',
  'fl-model': 'FL',
  'cl-model': 'CL',
  equivalence: 'EQUIV',
  rtl: 'RTL',
  lint: 'LINT',
  tb: 'TB',
  sim: 'SIM',
  coverage: 'COV',
  'sim-debug': 'DBG',
  syn: 'SYN',
  sta: 'STA',
  pnr: 'PNR',
  'sta-post': 'PSTA',
  'goal-audit': 'AUDIT',
};
window.fullPipeline = function fullPipeline(status, modId) {
  const s = status || {};
  const full = {
    ssot: s.ssot || 'pending',
    'fl-model': s.fl_model || s.functional_model || 'pending',
    'cl-model': s.cl_model || s.cycle_model || 'pending',
    equivalence: s.equivalence_goals || 'pending',
    rtl: s.rtl || 'pending',
    lint: s.lint || 'pending',
    tb: s.tb || 'pending',
    sim: s.sim || 'pending',
    coverage: s.coverage || 'pending',
    'sim-debug': s['sim-debug'] || s.sim_debug || (s.sim === 'ok' ? 'ok' : 'pending'),
    syn: s.syn || 'pending',
    sta: s.sta || 'pending',
    pnr: s.pnr || 'pending',
    'sta-post': s['sta-post'] || s.sta_post || s.signoff || 'pending',
    'goal-audit': s.goal_audit || 'pending',
  };
  const jobs = Array.isArray(window.ATLAS_JOBS) ? window.ATLAS_JOBS : [];
  const stageForWorkflow = {
    'ssot-gen': 'ssot',
    'fl-model-gen': 'fl-model',
    'rtl-gen': 'rtl',
    lint: 'lint',
    'tb-gen': 'tb',
    sim: 'sim',
    coverage: 'coverage',
    sim_debug: 'sim-debug',
    syn: 'syn',
    sta: 'sta',
    pnr: 'pnr',
    'sta-post': 'sta-post',
  };
  for (const j of jobs) {
    if (!j || j.ip !== modId) continue;
    const stage = j.stage_id || stageForWorkflow[j.workflow];
    if (!stage || !(stage in full)) continue;
    if (j.status === 'running' || j.status === 'pending') full[stage] = 'run';
    else if (j.status === 'queued') full[stage] = full[stage] === 'pending' ? 'partial' : full[stage];
    else if (j.status === 'completed') full[stage] = 'ok';
    else if (j.status === 'error' || j.status === 'blocked' || j.status === 'cancelled') full[stage] = 'err';
  }
  return full;
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

window.ModuleProgressPanel = function ModuleProgressPanel({ module }) {
  const p = module?.progress || {};
  const ssot = p.ssot || {};
  const rtl = p.rtl || {};
  const equiv = p.equivalence_goals || {};
  const goalAudit = p.goal_audit || {};
  const lint = p.lint || {};
  const sim = p.sim || {};
  const chipColor = (state) => {
    if (state === 'approved' || state === 'pass') return 'var(--ok)';
    if (state === 'missing' || state === 'fail') return 'var(--err)';
    if (state === 'partial' || state === 'incomplete' || state === 'unknown' || state === 'blocked' || state === 'escalated' || state === 'stale') return 'var(--warn)';
    return 'var(--fg-mute)';
  };
  const Bar = ({ value }) => (
    <span style={{
      display: 'inline-block', width: 78, height: 5, border: '1px solid var(--line)',
      background: 'var(--bg-2)', verticalAlign: 'middle', marginLeft: 6,
    }}>
      <span style={{
        display: 'block', height: '100%', width: `${Math.max(0, Math.min(100, value || 0))}%`,
        background: value >= 100 ? 'var(--ok)' : 'var(--warn)',
      }} />
    </span>
  );
  const Section = ({ title, right, children }) => (
    <div style={{ borderBottom: '1px solid var(--line)', padding: '8px 10px' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6,
        fontFamily: 'var(--mono)', fontSize: 10, letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}>
        <b>{title}</b>
        <span style={{ flex: 1 }} />
        <span className="mute">{right}</span>
      </div>
      {children}
    </div>
  );
  const ssotSections = Array.isArray(ssot.sections) ? ssot.sections : [];
  const ssotMetrics = ssot.metrics || {};
  const rtlModules = Array.isArray(rtl.modules) ? rtl.modules : [];
  const dv = sim.dv_plan || {};
  const res = sim.results || {};
  const cov = sim.coverage || {};
  const covStatic = cov.static && typeof cov.static === 'object' ? cov.static : {};
  const metricLabel = (m) => {
    if (!m || typeof m !== 'object') return '—';
    const pct = m.pct ?? m.percent;
    const hit = m.hit ?? m.covered;
    const total = m.total ?? m.found;
    if (pct != null) return `${pct}%`;
    if (hit != null && total != null) return `${hit}/${total}`;
    return '—';
  };
  const scenarioRows = Array.isArray(dv.scenario_rows) ? dv.scenario_rows : [];
  const escalations = Array.isArray(sim.escalations) ? sim.escalations : [];
  const covCriteria = cov.criteria && typeof cov.criteria === 'object' ? Object.entries(cov.criteria) : [];
  const covLimitations = cov.limitations && typeof cov.limitations === 'object' ? Object.entries(cov.limitations) : [];
  const resultRight = res.check_total != null
    ? `${res.check_pass ?? 0}/${res.check_total} checks · ${res.check_fail ?? 0} fail`
    : `${res.pass || 0}/${res.total || 0} pass · ${res.fail || 0} fail`;
  return (
    <div style={{ background: 'var(--panel)', borderBottom: '1px solid var(--line)' }}>
      <Section title="SSOT" right={`${ssot.approved || 0}/${ssot.total || 0} approved`}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 5 }}>
          {ssot.pct || 0}%<Bar value={ssot.pct || 0} />
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, fontFamily: 'var(--mono)', fontSize: 10, marginBottom: 6 }}>
          <span className="pill">submods {ssotMetrics.submodules ?? 0}</span>
          <span className="pill">params {ssotMetrics.parameters ?? 0}</span>
          <span className="pill">if {ssotMetrics.interfaces ?? 0}</span>
          <span className="pill">ports {ssotMetrics.ports ?? 0}</span>
          <span className="pill">regs {ssotMetrics.registers ?? 0}</span>
          <span className="pill">fsm {ssotMetrics.fsm_states ?? 0}/{ssotMetrics.fsm_transitions ?? 0}</span>
          <span className="pill">dv {ssotMetrics.dv_scenarios ?? 0}</span>
          <span className="pill">cov {ssotMetrics.coverage_goals ?? 0}</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {ssotSections.map(s => (
            <span key={s.key} title={`${s.key} · ${s.status}`} style={{
              border: `1px solid ${chipColor(s.status)}`, color: chipColor(s.status),
              padding: '1px 5px', fontSize: 9, fontFamily: 'var(--mono)', borderRadius: 2,
            }}>{s.label}</span>
          ))}
        </div>
      </Section>
      <Section title="FL-vs-RTL Goals" right={`${equiv.passed || 0}/${equiv.total || 0} pass`}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, fontFamily: 'var(--mono)', fontSize: 10 }}>
          <span style={{ color: chipColor(equiv.status), border: `1px solid ${chipColor(equiv.status)}`, padding: '1px 6px' }}>{equiv.status || 'pending'}</span>
          <span className="pill">generated {equiv.generated || 0}</span>
          <span className="pill">checked {equiv.checked || 0}</span>
          <span className="pill">failed {equiv.failed || 0}</span>
          <span className="pill">blocked {equiv.blocked || 0}</span>
          <span className="pill">untested {equiv.untested || 0}</span>
        </div>
        <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {equiv.compare_evidence || equiv.evidence || 'no equivalence goal evidence'}
        </div>
        {equiv.classification_counts && Object.keys(equiv.classification_counts).length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            class: {Object.entries(equiv.classification_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
          </div>
        )}
        {equiv.owner_counts && Object.keys(equiv.owner_counts).length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            owner: {Object.entries(equiv.owner_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
          </div>
        )}
        {Array.isArray(equiv.missing_evidence) && equiv.missing_evidence.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            missing: {equiv.missing_evidence.slice(0, 3).join(', ')}
          </div>
        )}
        {Array.isArray(equiv.stale_evidence) && equiv.stale_evidence.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            stale: {equiv.stale_evidence.slice(0, 3).join(', ')}
          </div>
        )}
        {Array.isArray(equiv.failed_goal_ids) && equiv.failed_goal_ids.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            failed: {equiv.failed_goal_ids.join(', ')}
          </div>
        )}
        {Array.isArray(equiv.blocked_goal_ids) && equiv.blocked_goal_ids.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            blocked: {equiv.blocked_goal_ids.join(', ')}
          </div>
        )}
        {Array.isArray(equiv.untested_goal_ids) && equiv.untested_goal_ids.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            untested: {equiv.untested_goal_ids.join(', ')}
          </div>
        )}
        <div className="mute" style={{ marginTop: 7, fontFamily: 'var(--mono)', fontSize: 10 }}>
          audit <span style={{ color: chipColor(goalAudit.status) }}>{goalAudit.status || 'pending'}</span>
          {' '}· {goalAudit.passed_checks || 0}/{goalAudit.total_checks || 0} checks
          {goalAudit.source ? ` · ${goalAudit.source}` : ' · run /goal-audit'}
        </div>
        {Array.isArray(goalAudit.blockers) && goalAudit.blockers.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            audit blockers: {goalAudit.blockers.slice(0, 8).join(', ')}
          </div>
        )}
        {Array.isArray(goalAudit.stale_evidence) && goalAudit.stale_evidence.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            audit stale: {goalAudit.stale_evidence.slice(0, 3).join(', ')}
          </div>
        )}
      </Section>
      <Section title="RTL" right={`${rtl.approved || 0}/${rtl.total || 0} modules`}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 5 }}>
          {rtl.pct || 0}% · {rtl.filelist || 'no filelist'}<Bar value={rtl.pct || 0} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 4 }}>
          {rtlModules.map(m => (
            <span key={m.file} title={`${m.file}\nlisted=${m.listed} bytes=${m.bytes} placeholder=${m.placeholder}`} style={{
              borderLeft: `2px solid ${chipColor(m.status)}`, background: 'var(--bg-2)',
              padding: '3px 5px', fontSize: 10, fontFamily: 'var(--mono)',
              color: m.status === 'approved' ? 'var(--fg)' : chipColor(m.status),
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>{m.status === 'approved' ? '✓' : m.status === 'missing' ? '✕' : '◐'} {m.name}</span>
          ))}
        </div>
      </Section>
      <Section title="Lint" right={`${lint.errors ?? 0} errors · ${lint.warnings ?? 0} warnings`}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontFamily: 'var(--mono)', fontSize: 11 }}>
          <span style={{ color: chipColor(lint.status), border: `1px solid ${chipColor(lint.status)}`, padding: '1px 6px' }}>{lint.status || 'unknown'}</span>
          <span className="err">E {lint.errors ?? 0}</span>
          <span className="warn">W {lint.warnings ?? 0}</span>
          <span className="mute">waive {lint.warning_budget ?? 0}</span>
          <span className="mute" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{lint.source || 'no lint log'}</span>
        </div>
      </Section>
      <Section title="SIM · DV" right={resultRight}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, fontFamily: 'var(--mono)', fontSize: 10 }}>
          <span className="pill">SSOT scenarios {dv.scenarios || 0}</span>
          <span className="pill">scoreboard {dv.scoreboard_checks ?? '—'}</span>
          <span className="pill">coverage goals {dv.coverage_goals || 0}</span>
          <span className="pill">TB tests {sim.implemented_tests || 0}</span>
          <span className="pill">xunit {res.pass || 0}/{res.total || 0}</span>
          <span style={{ color: chipColor(cov.status), border: `1px solid ${chipColor(cov.status)}`, padding: '1px 6px' }}>coverage {cov.status || 'unknown'}</span>
          <span className="pill">functional cov {cov.functional_pct ?? '—'}%</span>
          <span className="pill">line {metricLabel(covStatic.lines)}</span>
          <span className="pill">branch {metricLabel(covStatic.branches)}</span>
          <span className="pill">fsm {metricLabel(covStatic.fsm_state)}</span>
        </div>
        {scenarioRows.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
            {scenarioRows.map((r) => {
              const esc = r.escalation && typeof r.escalation === 'object' ? r.escalation : null;
              const title = [
                `${r.id || ''} ${r.name || ''}`.trim(),
                `status=${r.status || 'pending'}`,
                r.expected ? `expected=${r.expected}` : '',
                esc ? `escalation=${esc.file || esc.module || ''} ${esc.hypothesis || esc.fix || esc.expected || ''}` : '',
              ].filter(Boolean).join('\n');
              return (
                <span key={r.id || r.name} title={title} style={{
                  border: `1px solid ${chipColor(r.status)}`, color: chipColor(r.status),
                  padding: '1px 5px', fontSize: 9, fontFamily: 'var(--mono)', borderRadius: 2,
                }}>{r.id || r.name}: {r.status || 'pending'}</span>
              );
            })}
          </div>
        )}
        {escalations.length > 0 && (
          <div style={{ marginTop: 6, fontSize: 10, color: 'var(--warn)', lineHeight: 1.4 }}>
            {escalations.slice(0, 3).map((e, idx) => (
              <div key={`${e.test_id || e.scenario || idx}`}>[{e.test_id || e.scenario || `E${idx + 1}`}] {e.module || e.file || 'escalated'}: {e.expected || e.fix || e.hypothesis || 'see coverage.json'}</div>
            ))}
            {escalations.length > 3 && <div className="mute">+{escalations.length - 3} more escalations</div>}
          </div>
        )}
        {covCriteria.length > 0 && (
          <div style={{ marginTop: 5, fontSize: 10, color: 'var(--fg-mute)', lineHeight: 1.4 }}>
            {covCriteria.map(([k, v]) => <div key={k}><b>{k}</b>: {String(v)}</div>)}
          </div>
        )}
        {covLimitations.length > 0 && (
          <div style={{ marginTop: 5, fontSize: 10, color: 'var(--warn)', lineHeight: 1.4 }}>
            {covLimitations.map(([k, v]) => <div key={k}><b>{k}</b>: {String(v)}</div>)}
          </div>
        )}
      </Section>
    </div>
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
  const [socTopMode, setSocTopMode] = React.useState('if'); // 'if' = I/F only, 'detail' = show aux pins/addr
  const [diagramFocus, setDiagramFocus] = React.useState(false);
  const [leftPanelW, setLeftPanelW] = React.useState(() => Number(localStorage.getItem('atlas.arch.leftPanelW')) || 240);
  const [rightPanelW, setRightPanelW] = React.useState(() => Number(localStorage.getItem('atlas.arch.rightPanelW')) || 480);
  const panelResizeRef = React.useRef(null);
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
  // Active worker jobs (HTTP-worker dispatched). Polled from /api/jobs
  // every 2s; used by the JobTracker panel + the per-block "running"
  // ring + the block ⚡ menu.
  const [jobs, setJobs] = React.useState([]);
  const beginPanelResize = React.useCallback((side, e) => {
    e.preventDefault();
    e.stopPropagation();
    panelResizeRef.current = {
      side,
      startX: e.clientX,
      left0: leftPanelW,
      right0: rightPanelW,
      viewportW: window.innerWidth || 1440,
    };
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [leftPanelW, rightPanelW]);
  React.useEffect(() => {
    const onMove = (e) => {
      const drag = panelResizeRef.current;
      if (!drag) return;
      const dx = e.clientX - drag.startX;
      if (drag.side === 'left') {
        const next = Math.max(170, Math.min(420, drag.left0 + dx));
        setLeftPanelW(next);
      } else {
        const next = Math.max(320, Math.min(Math.max(360, drag.viewportW - 420), drag.right0 - dx));
        setRightPanelW(next);
      }
    };
    const onUp = () => {
      if (!panelResizeRef.current) return;
      panelResizeRef.current = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      setLeftPanelW(v => {
        localStorage.setItem('atlas.arch.leftPanelW', String(Math.round(v)));
        return v;
      });
      setRightPanelW(v => {
        localStorage.setItem('atlas.arch.rightPanelW', String(Math.round(v)));
        return v;
      });
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, []);
  React.useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const r = await fetch('/api/jobs');
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const d = await r.json();
        if (!cancelled) setJobs(Array.isArray(d.jobs) ? d.jobs : []);
      } catch (_) { /* keep last good */ }
    };
    tick();
    const id = setInterval(tick, 2000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);
  React.useEffect(() => {
    window.ATLAS_JOBS = jobs || [];
  }, [jobs]);
  // Map ip → most recent running job (used for diagram ring).
  const runningByIp = React.useMemo(() => {
    const m = {};
    for (const j of jobs) {
      if (j.status === 'running' && j.ip) {
        if (!m[j.ip] || (j.started_at || 0) > (m[j.ip].started_at || 0)) m[j.ip] = j;
      }
    }
    return m;
  }, [jobs]);
  const jobsByIp = React.useMemo(() => {
    const m = {};
    for (const j of jobs) {
      if (!j.ip) continue;
      if (!m[j.ip]) m[j.ip] = [];
      m[j.ip].push(j);
    }
    for (const ip of Object.keys(m)) {
      m[ip].sort((a, b) => (b.started_at || 0) - (a.started_at || 0));
    }
    return m;
  }, [jobs]);
  // Per-block dispatch menu state — anchored to the ⚡ button.
  // {ipRef, x, y} or null.
  const [dispatchMenu, setDispatchMenu] = React.useState(null);
  const dispatchJob = React.useCallback(async (workflow, ip, stageId = '') => {
    setDispatchMenu(null);
    const stageName = stageId || workflow;
    const session = normalizeArchitectSession(ip ? `${ip}/${stageName}` : stageName);
    try {
      const r = await fetch('/api/job/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow,
          ip,
          stage_id: stageId,
          session,
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
      // Force a job poll soon so the ring + tracker update fast.
      setTimeout(() => fetch('/api/jobs').then(r => r.json())
        .then(dd => setJobs(dd.jobs || [])).catch(() => {}), 200);
    } catch (e) {
      alert(`dispatch failed: ${e.message || e}\n\n` +
            `Check the worker for ${workflow} is running:\n` +
            `  python src/main.py --serve --port 8001 --worker-name ${workflow}\n` +
            `Or set WORKER_URL_${workflow.toUpperCase().replace(/-/g, '_')} env var.`);
    }
  }, []);
  const dispatchPipeline = React.useCallback(async (ip) => {
    setDispatchMenu(null);
    if (!ip) {
      alert('Select an IP/module first, then run the full pipeline.');
      return;
    }
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
      setTimeout(() => fetch('/api/jobs').then(r => r.json())
        .then(dd => setJobs(dd.jobs || [])).catch(() => {}), 200);
    } catch (e) {
      alert(`pipeline dispatch failed: ${e.message || e}`);
    }
  }, []);
  // Sparkline hover popover state — which row is hovered, for the
  // status grid TREND column. {ref, x, y} or null.
  const [sparkPop, setSparkPop] = React.useState(null);
  // Port-to-port connect state for the top SoC diagram. First click
  // arms a source port; second click writes connections[] through
  // /api/soc/connect and refreshes live data.
  const [pendingPort, setPendingPort] = React.useState(null);
  const [catalog, setCatalog] = React.useState([]);
  const [workspaceTree, setWorkspaceTree] = React.useState(null);
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
  React.useEffect(() => {
    let cancelled = false;
    fetch('/api/catalog/models')
      .then(r => r.json())
      .then(d => { if (!cancelled) setCatalog(Array.isArray(d.models) ? d.models : []); })
      .catch(() => { if (!cancelled) setCatalog([]); });
    return () => { cancelled = true; };
  }, [isLive]);
  React.useEffect(() => {
    let cancelled = false;
    fetch('/api/workspace/tree?depth=2')
      .then(r => r.json())
      .then(d => { if (!cancelled) setWorkspaceTree(d.root || null); })
      .catch(() => { if (!cancelled) setWorkspaceTree(null); });
    return () => { cancelled = true; };
  }, [isLive]);

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
  const getStageScale = React.useCallback((e, stageW = 1180) => {
    const stage = e?.currentTarget?.closest?.('.bd-stage') ||
                  bdCanvasRef.current?.querySelector?.('.bd-stage');
    const rect = stage?.getBoundingClientRect?.();
    if (rect && rect.width > 0) return rect.width / stageW;
    return zoom / 100;
  }, [zoom]);
  React.useEffect(() => {
    const onMove = (e) => {
      const d = blockDragRef.current;
      if (!d || !d.globalDrag) return;
      const dx = (e.clientX - d.startX) / d.scale;
      const dy = (e.clientY - d.startY) / d.scale;
      if (Math.abs(dx) + Math.abs(dy) < 2) return;
      d.dragged = true;
      const nextPos = {
        x: Math.max(0, Math.min(d.maxX, d.baseX + dx)),
        y: Math.max(0, Math.min(d.maxY, d.baseY + dy)),
      };
      setLayout(prev => {
        const next = { ...prev, [d.layoutKey]: nextPos };
        d.latestLayout = next;
        return next;
      });
    };
    const onUp = () => {
      const d = blockDragRef.current;
      if (!d || !d.globalDrag) return;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      if (d.dragged && d.latestLayout) persistLayout(d.latestLayout);
      setTimeout(() => { blockDragRef.current = null; }, 0);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [persistLayout]);

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
    // selection doesn't exist there. Keep the top-level SoC overview
    // visible: it now renders live IP instances and real interconnects
    // instead of a mock-only cluster card layout.
    if (isLive) {
      if (!lookup[selMod]) setSelMod(firstRef);
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

  // Run metadata for the status grid. Use only real sim_history from
  // /api/soc; missing data stays blank so the UI does not imply a
  // verification run that never happened.
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
    return { t: '—', cov: '—', tests: '—', dur: '—' };
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
    return [];
  };

  // ── V7 diagram renderers ──────────────────────────────────────
  const renderSocView = () => {
    const W = 1180, H = 720;
    const modules = [];
    for (const c of soc.clusters || []) {
      for (const m of c.modules || []) modules.push({ cluster: c, module: m, ref: `${c.id}/${m.id}` });
    }
    const findRow = (id) => modules.find(r => r.module.id === id);
    const isAux = (it) => {
      const p = (it.proto || '').toUpperCase();
      return p === 'CLK' || p === 'RST';
    };
    const sizeOf = (m) => {
      const visible = (m.interfaces || []).filter(it => socTopMode === 'detail' || !isAux(it));
      const n = Math.max(2, Math.min(5, visible.length));
      return { w: 236, h: Math.max(112, 50 + n * 20) };
    };
    const positions = {};
    const put = (id, x, y) => {
      const row = findRow(id); if (!row) return;
      const s = sizeOf(row.module);
      // Top SoC has its own layout namespace. Cluster-local saved
      // positions can be useful inside a cluster view but make the
      // full-chip diagram collapse when the same x/y are reused here.
      const ov = layout && layout[`top:${row.ref}`];
      const hasOv = ov && typeof ov.x === 'number' && typeof ov.y === 'number';
      const hasSaved = typeof row.module.savedTopX === 'number' && typeof row.module.savedTopY === 'number';
      positions[id] = {
        x: hasOv ? ov.x : hasSaved ? row.module.savedTopX : x,
        y: hasOv ? ov.y : hasSaved ? row.module.savedTopY : y,
        w: s.w, h: s.h,
      };
    };
    // Prefer the familiar Carbon-style SoC placement when these IPs
    // exist; fall back to kind/role based columns for other projects.
    put('cortexa15_0', 74, 92);
    put('cci550',      468, 210);
    put('ddr_phy',     846, 92);
    put('spi_master',  170, 468);
    put('gic_400',     846, 438);
    put('uart_lite',   846, 592);
    let yCpu = 80, yBus = 220, yMem = 88, yPer = 430, yMisc = 560;
    for (const r of modules) {
      if (positions[r.module.id]) continue;
      const role = (r.cluster.role || '').toUpperCase();
      const kind = r.module.kind || '';
      if (role === 'CPU' || kind === 'cpu') { put(r.module.id, 72, yCpu); yCpu += 164; }
      else if (role === 'BUS' || kind === 'bus') { put(r.module.id, 470, yBus); yBus += 168; }
      else if (role === 'MEM' || kind === 'mem') { put(r.module.id, 850, yMem); yMem += 164; }
      else if (role === 'PERIPH' || kind === 'periph') { put(r.module.id, 164, yPer); yPer += 150; }
      else { put(r.module.id, 850, yMisc); yMisc += 140; }
    }
    const ifaceSide = (iface) => {
      const side = (iface.side || '').toLowerCase();
      const role = (iface.role || 'slave').toLowerCase();
      const proto = (iface.proto || '').toUpperCase();
      if (proto === 'CLK' || proto === 'RST') return 'left';
      if (side === 'top' || side === 'bottom' || side === 'left' || side === 'right') return side;
      return role === 'master' ? 'right' : 'left';
    };
    const sideList = (m, side) => (m.interfaces || [])
      .filter(it => socTopMode === 'detail' || !isAux(it))
      .filter(it => ifaceSide(it) === side)
      .slice(0, 5);
    const pinPoint = (m, ifaceName, preferSide) => {
      const p = positions[m.id]; if (!p) return null;
      const iface = (m.interfaces || []).find(it => it.name === ifaceName) || {};
      const side = preferSide || ifaceSide(iface);
      const list = sideList(m, side);
      const idx = Math.max(0, list.findIndex(it => it.name === ifaceName));
      const t = (idx + 1) / (Math.max(1, list.length) + 1);
      const topPorts = sideList(m, 'top');
      const bottomPorts = sideList(m, 'bottom');
      const headerH = 24;
      const topH = topPorts.length ? 18 : 0;
      const bottomH = bottomPorts.length ? 18 : 0;
      if (side === 'top') return { x: p.x + p.w * t, y: p.y + headerH + 1, side };
      if (side === 'bottom') return { x: p.x + p.w * t, y: p.y + p.h - bottomH - 1, side };

      // The visible left/right port rows are not distributed across the
      // whole block: CSS centers the port column inside the body area.
      // Mirror that geometry so wires terminate at the row, not above or
      // below the label.
      const bodyY = p.y + headerH + topH;
      const bodyH = Math.max(1, p.h - headerH - topH - bottomH);
      const rowH = 13;
      const gap = 3;
      const n = Math.max(1, list.length);
      const stackH = n * rowH + (n - 1) * gap;
      const firstY = bodyY + (bodyH - stackH) / 2 + rowH / 2;
      const y = firstY + Math.max(0, idx) * (rowH + gap);
      if (side === 'right') return { x: p.x + p.w + 3, y, side };
      return { x: p.x - 3, y, side: 'left' };
    };
    const protoColor = (proto) => {
      const p = (proto || '').toUpperCase();
      if (p === 'ACE' || p === 'AXI' || p === 'AXI4' || p === 'AXI4L') return 'var(--accent)';
      if (p === 'APB' || p === 'AHB') return 'var(--magenta)';
      if (p === 'IRQ') return 'var(--warn)';
      return 'var(--cyan)';
    };
    const connections = [];
    if (layers.busses) {
      for (const bus of (soc.busses || soc.connections || [])) {
        if (!bus.from || !bus.to) continue;
        const [aId, aIf] = String(bus.from).split('/');
        const [bId, bIf] = String(bus.to).split('/');
        const a = findRow(aId)?.module, b = findRow(bId)?.module;
        if (!a || !b) continue;
        const p1 = pinPoint(a, aIf, 'right');
        const p2 = pinPoint(b, bIf, 'left');
        if (!p1 || !p2) continue;
        connections.push({ id: `${bus.from}->${bus.to}`, from: bus.from, to: bus.to,
                           proto: bus.proto || '', color: protoColor(bus.proto), p1, p2 });
      }
    }
    const familyClass = (proto) => {
      const x = (proto || '').toUpperCase();
      if (x === 'AXI' || x === 'AXI4') return 'proto-axi';
      if (x === 'AXI4L') return 'proto-axil';
      if (x === 'ACE') return 'proto-ace';
      if (x === 'APB') return 'proto-apb';
      if (x === 'IRQ') return 'proto-irq';
      if (x === 'CLK') return 'proto-clk';
      if (x === 'RST') return 'proto-rst';
      return '';
    };
    const arrowFor = (iface) => {
      const role = (iface.role || 'slave').toLowerCase();
      const proto = (iface.proto || '').toUpperCase();
      if (proto === 'IRQ') return '↯';
      if (proto === 'CLK' || proto === 'RST') return '►';
      return role === 'master' ? '►' : '◄';
    };
    const connectPort = async (row, iface, e) => {
      e.stopPropagation();
      const port = {
        ip: row.module.id,
        iface: iface.name,
        proto: (iface.proto || '').toUpperCase(),
        role: (iface.role || '').toLowerCase(),
      };
      if (!pendingPort) {
        setPendingPort(port);
        return;
      }
      if (pendingPort.ip === port.ip && pendingPort.iface === port.iface) {
        setPendingPort(null);
        return;
      }
      const pendingIsMaster = pendingPort.role === 'master';
      const thisIsMaster = port.role === 'master';
      const src = pendingIsMaster || !thisIsMaster ? pendingPort : port;
      const dst = src === pendingPort ? port : pendingPort;
      try {
        const r = await fetch('/api/soc/connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: `${src.ip}/${src.iface}`,
            to: `${dst.ip}/${dst.iface}`,
            proto: src.proto || dst.proto,
          }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
        setPendingPort(null);
        refreshSoc();
      } catch (err) {
        alert(`connect failed: ${err.message || err}`);
      }
    };
    const beginBlockDrag = (ref, layoutKey, p, e, maxX, maxY) => {
      if (e.button !== 0) return;
      if (e.target.closest && e.target.closest('.bd-port')) return;
      e.stopPropagation();
      document.body.style.cursor = 'grabbing';
      document.body.style.userSelect = 'none';
      blockDragRef.current = {
        ref,
        layoutKey,
        scale: getStageScale(e, W),
        dragged: false,
        startX: e.clientX,
        startY: e.clientY,
        baseX: p.x,
        baseY: p.y,
        maxX,
        maxY,
        latestLayout: null,
        globalDrag: true,
      };
    };
    const portClass = (m, it, side) => {
      const active = pendingPort && pendingPort.ip === m.id && pendingPort.iface === it.name;
      return `bd-port ${side}-side ${familyClass(it.proto)} ${active ? 'connecting' : ''}`;
    };
    const protoBadge = (it) => {
      const p = (it.proto || '').toUpperCase();
      if (!p || p === 'CLK' || p === 'RST') return null;
      return <span className="proto-badge">{p}</span>;
    };
    return (
      <React.Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          <defs>
            <marker id="soc-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M0,0 L8,4 L0,8 z" fill="currentColor" />
            </marker>
          </defs>
          {connections.map(co => {
            const midX = (co.p1.x + co.p2.x) / 2;
            const points = `${co.p1.x},${co.p1.y} ${midX},${co.p1.y} ${midX},${co.p2.y} ${co.p2.x},${co.p2.y}`;
            return (
              <g key={co.id} style={{ color: co.color }}>
                <polyline points={points} stroke={co.color} strokeWidth="3.2" fill="none"
                          strokeLinejoin="round" strokeLinecap="square" markerEnd="url(#soc-arrow)" />
                <circle cx={co.p1.x} cy={co.p1.y} r="3.2" fill={co.color} />
                <circle cx={co.p2.x} cy={co.p2.y} r="3.2" fill={co.color} />
                {layers.labels && (
                  <g>
                    <rect x={midX - 20} y={(co.p1.y + co.p2.y)/2 - 8} width="40" height="15"
                          className="soc-wire-label" fill="var(--bg)" stroke={co.color} strokeWidth="0.8" />
                    <text x={midX} y={(co.p1.y + co.p2.y)/2} textAnchor="middle"
                          dominantBaseline="middle" fill={co.color} fontSize="10"
                          fontFamily="var(--mono)">{co.proto}</text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
        {modules.map(({ cluster: c, module: m, ref }) => {
          const p = positions[m.id]; if (!p) return null;
          const sel = selMod === ref;
          const touched = isTouched(ref);
          const left = sideList(m, 'left');
          const right = sideList(m, 'right');
          const top = sideList(m, 'top');
          const bottom = sideList(m, 'bottom');
          return (
            <div key={ref} className={`bd-block with-ports soc-top ${m.kind || ''} ${sel ? 'sel' : ''} ${touched ? 'touched' : ''}`}
                 style={{ left: p.x, top: p.y, width: p.w, height: p.h }}
                 onClick={(e) => {
                   if (blockDragRef.current && blockDragRef.current.ref === ref && blockDragRef.current.dragged) return;
                   e.stopPropagation(); setSelMod(ref);
                 }}
                 onDoubleClick={() => {
                   if (blockDragRef.current && blockDragRef.current.ref === ref && blockDragRef.current.dragged) return;
                   setView(`module:${ref}`);
                 }}
                 onMouseDown={(e) => beginBlockDrag(ref, `top:${ref}`, p, e, W - p.w, H - p.h)}>
              <div className="bd-block-head"
                   title="drag block · click ports to connect · double-click to inspect"
                   style={{ cursor: 'grab' }}
                   onMouseDown={(e) => beginBlockDrag(ref, `top:${ref}`, p, e, W - p.w, H - p.h)}>
                <span className="nm-instance">{m.name || m.id}</span>
                <span className="nm-type">({c.id})</span>
                <span style={{ flex: 1 }} />
                {socTopMode === 'detail' && m.addr && <span style={{ fontSize: 9, color: 'var(--cyan)', fontFamily: 'var(--mono)' }}>{m.addr}</span>}
              </div>
              {top.length > 0 && <div className="bd-ports-edge top">{top.map((it, i) => (
                <span key={i} className={portClass(m, it, 'top')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}><span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}</span>
              ))}</div>}
              <div className="bd-ports">
                <div className="bd-ports-col left">
                  {left.map((it, i) => (
                    <span key={i} className={portClass(m, it, 'left')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}>
                      <span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}
                    </span>
                  ))}
                </div>
                <div className="bd-center-icon" aria-hidden="true" />
                <div className="bd-ports-col right">
                  {right.map((it, i) => (
                    <span key={i} className={portClass(m, it, 'right')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}>
                      {protoBadge(it)}<span className="nm">{it.name}</span><span className="arr">{arrowFor(it)}</span>
                    </span>
                  ))}
                </div>
              </div>
              {bottom.length > 0 && <div className="bd-ports-edge bottom">{bottom.map((it, i) => (
                <span key={i} className={portClass(m, it, 'bottom')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}><span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}</span>
              ))}</div>}
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

        {c.modules.map((m) => {
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
            <div key={m.id} className={`bd-block with-ports ${m.kind || ''} ${sel ? 'sel' : ''} ${touched ? 'touched' : ''} ${runningByIp[m.id] ? 'job-running' : ''}`}
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
                     const scale = getStageScale(e, W);
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
                {/* Running-job ring marker */}
                {runningByIp[m.id] && (
                  <span className="bd-running-pill"
                        title={`${runningByIp[m.id].workflow} · iter ${runningByIp[m.id].iterations}`}>
                    ◌ {runningByIp[m.id].workflow}
                  </span>
                )}
                {m.addr && <span style={{ fontSize: 9, color: 'var(--cyan)', fontFamily: 'var(--mono)' }}>{m.addr.split(' ')[0] || ''}</span>}
                {/* ⚡ dispatch button — opens menu to run workflows on
                    this IP via an HTTP worker. */}
                <button className="bd-dispatch-btn"
                        title="dispatch a workflow on this IP"
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={(e) => {
                          e.stopPropagation();
                          const r = e.currentTarget.getBoundingClientRect();
                          setDispatchMenu({
                            ip: m.id,
                            x: r.right + 4, y: r.top,
                          });
                        }}>⚡</button>
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

  const applyDiagramPlan = React.useCallback(async (promptText) => {
    const r = await fetch('/api/diagram/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: promptText, layout }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
    const plan = d.plan || {};
    const actions = Array.isArray(plan.actions) ? plan.actions : [];
    const refById = {};
    for (const c of soc.clusters || []) {
      for (const m of c.modules || []) refById[m.id] = `${c.id}/${m.id}`;
    }
    let nextLayout = { ...layout };
    let touchedLayout = false;
    const notes = [];
    for (const a of actions) {
      if (!a || typeof a !== 'object') continue;
      if (a.type === 'auto_layout') {
        nextLayout = Object.fromEntries(Object.entries(nextLayout).filter(([k]) => !k.startsWith('top:')));
        touchedLayout = true;
        notes.push('auto layout');
      } else if (a.type === 'move_block') {
        const id = String(a.id || a.ref || '').split('/').pop();
        const ref = refById[id];
        const x = Number(a.x), y = Number(a.y);
        if (ref && Number.isFinite(x) && Number.isFinite(y)) {
          nextLayout[`top:${ref}`] = {
            x: Math.max(0, Math.min(1080, x)),
            y: Math.max(0, Math.min(650, y)),
          };
          touchedLayout = true;
          notes.push(`move ${id}`);
        }
      } else if (a.type === 'connect_ports') {
        const rr = await fetch('/api/soc/connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ from: a.from, to: a.to, proto: a.proto || '' }),
        });
        const dd = await rr.json().catch(() => ({}));
        if (!rr.ok || dd.error) throw new Error(dd.error || `connect HTTP ${rr.status}`);
        notes.push(`connect ${a.from} -> ${a.to}`);
      } else if (a.type === 'add_instance') {
        const rr = await fetch('/api/soc/instance/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: a.model || a.name,
            id: a.id,
            cluster: a.cluster,
            x: a.x,
            y: a.y,
            addr: a.addr,
          }),
        });
        const dd = await rr.json().catch(() => ({}));
        if (!rr.ok || dd.error) throw new Error(dd.error || `add instance HTTP ${rr.status}`);
        notes.push(`add ${dd.instance?.id || a.id || a.model}`);
      } else if (a.type === 'delete_instance') {
        const id = String(a.id || a.instance || '').trim();
        if (!id) continue;
        if (!confirm(`Remove instance "${id}" from this SoC?\n\nModel files will stay in the available model catalog.`)) {
          notes.push(`skip delete ${id}`);
          continue;
        }
        const rr = await fetch('/api/soc/instance/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id }),
        });
        const dd = await rr.json().catch(() => ({}));
        if (!rr.ok || dd.error) throw new Error(dd.error || `delete instance HTTP ${rr.status}`);
        nextLayout = Object.fromEntries(Object.entries(nextLayout).filter(([k]) => !k.endsWith(`/${id}`)));
        touchedLayout = true;
        notes.push(`delete ${id}`);
      }
    }
    if (touchedLayout) {
      setLayout(nextLayout);
      persistLayout(nextLayout);
    }
    if (actions.some(a => a && (a.type === 'connect_ports' || a.type === 'add_instance' || a.type === 'delete_instance'))) await refreshSoc();
    return {
      summary: plan.summary || 'diagram plan applied',
      count: actions.length,
      notes,
    };
  }, [layout, persistLayout, refreshSoc, soc]);

  const addCatalogInstance = React.useCallback(async (model) => {
    const roleCluster = model.kind === 'cpu' ? 'cpu_ss'
      : model.kind === 'bus' ? 'noc'
      : model.kind === 'mem' ? 'mem_ss'
      : 'periph_ss';
    const r = await fetch('/api/soc/instance/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model.name || model.id,
        cluster: roleCluster,
        x: model.kind === 'mem' ? 850 : model.kind === 'bus' ? 470 : 170,
        y: 560,
      }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || d.error) {
      alert(`add instance failed: ${d.error || `HTTP ${r.status}`}`);
      return;
    }
    await refreshSoc();
    setView('soc');
    if (d.instance && d.instance.id) {
      setSelMod(`${d.cluster}/${d.instance.id}`);
    }
  }, [refreshSoc]);

  const deleteInstance = React.useCallback(async (id) => {
    if (!id) return;
    if (!confirm(`Remove instance "${id}" from this SoC?\n\nModel files will be kept; only soc.ssot.yaml instance/members/connections are changed.`)) return;
    const r = await fetch('/api/soc/instance/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || d.error) {
      alert(`delete instance failed: ${d.error || `HTTP ${r.status}`}`);
      return;
    }
    const nextLayout = Object.fromEntries(Object.entries(layout).filter(([k]) => !k.endsWith(`/${id}`)));
    setLayout(nextLayout);
    persistLayout(nextLayout);
    await refreshSoc();
    setView('soc');
  }, [layout, persistLayout, refreshSoc]);

  const renderWorkspaceNode = React.useCallback((node, depth = 0) => {
    if (!node) return null;
    const kids = Array.isArray(node.children) ? node.children : [];
    const artifacts = Array.isArray(node.artifacts) ? node.artifacts : [];
    const isIp = !!node.is_ip;
    return (
      <React.Fragment key={node.path || node.name}>
        <div className="bd-tree-row"
             title={node.path || node.name}
             style={{ paddingLeft: 10 + depth * 14, alignItems: 'flex-start' }}>
          <span className="tw">{kids.length ? '▾' : '·'}</span>
          <span className="ico">{isIp ? '◇' : '▸'}</span>
          <span style={{ flex: 1, minWidth: 0 }}>
            <span style={{ display: 'block', color: isIp ? 'var(--fg)' : 'var(--fg-dim)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {node.name}
            </span>
            {isIp && (
              <span style={{ display: 'block', fontSize: 8.5, color: 'var(--fg-mute)', marginTop: 2 }}>
                {node.ssot_count || 1} ssot · {artifacts.slice(0, 5).join(' · ')}
              </span>
            )}
          </span>
          {isIp && <span className="pill acc" style={{ fontSize: 8 }}>ip</span>}
        </div>
        {kids.slice(0, depth === 0 ? 80 : 24).map(k => renderWorkspaceNode(k, depth + 1))}
      </React.Fragment>
    );
  }, []);

  return (
    <div className="arch-screen">
      {/* Run bar (scope · stage triggers · totals). Each stage button
          dispatches the matching backend workflow immediately. */}
      <div className="run-bar">
        <div className="grp">
          <button className="rb-btn primary"
                  disabled={!selModule}
                  title={selModule ? `run architect → post-STA pipeline on ${selModule.id}` : 'select a module first'}
                  onClick={() => dispatchPipeline(selModule && selModule.id)}>
            <span className="icn">▶</span> full pipeline
          </button>
          {window.PIPELINE_STAGES.map((s) => {
            const wfMap = {
              ssot: { wf: 'ssot-gen' },
              'fl-model': { wf: 'fl-model-gen', stage: 'fl-model' },
              'cl-model': { wf: 'fl-model-gen', stage: 'cl-model' },
              equivalence: { wf: 'fl-model-gen', stage: 'equivalence' },
              rtl: { wf: 'rtl-gen' },
              lint: { wf: 'lint' },
              tb: { wf: 'tb-gen' },
              sim: { wf: 'sim' },
              coverage: { wf: 'coverage' },
              'sim-debug': { wf: 'sim_debug' },
              syn: { wf: 'syn' },
              sta: { wf: 'sta' },
              pnr: { wf: 'pnr' },
              'sta-post': { wf: 'sta-post' },
              'goal-audit': { wf: 'sim_debug', stage: 'goal-audit' },
            };
            const cfg = wfMap[s] || {};
            const wf = cfg.wf || '';
            const onPipeClick = () => {
              if (!wf || !selModule) return;
              setRunning(s);
              setTimeout(() => setRunning(null), 1100);
              dispatchJob(wf, selModule.id, cfg.stage || s);
            };
            return (
              <button key={s}
                      className={`rb-btn ${s === 'sim' ? 'primary' : ''}`}
                      disabled={!wf || !selModule}
                      title={wf && selModule ? `dispatch ${wf} on ${selModule.id}` : 'select a module first'}
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

      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: diagramFocus ? '0 minmax(0,1fr) 0' : `${leftPanelW}px minmax(360px,1fr) ${rightPanelW}px`,
        overflow: 'hidden',
      }}>
        {/* LEFT — hierarchy tree */}
        <div style={{
          background: 'var(--panel)', borderRight: '1px solid var(--line)',
          overflow: 'auto', display: 'flex', flexDirection: 'column', position: 'relative',
          visibility: diagramFocus ? 'hidden' : 'visible',
          pointerEvents: diagramFocus ? 'none' : 'auto',
        }}>
          <div className="arch-splitter left"
               title="resize hierarchy"
               onMouseDown={(e) => beginPanelResize('left', e)} />
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
          <div className="bd-tree" style={{ padding: '6px 0', flex: '1 1 52%', minHeight: 160, overflow: 'auto' }}>
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
                      <button title="remove this instance from the SoC"
                              onClick={(e) => { e.stopPropagation(); deleteInstance(m.id); }}
                              style={{
                                border: '1px solid var(--line)',
                                background: 'var(--bg-2)',
                                color: 'var(--fg-mute)',
                                width: 18,
                                height: 18,
                                lineHeight: '14px',
                                padding: 0,
                                fontSize: 13,
                                cursor: 'pointer',
                                marginLeft: 4,
                              }}>×</button>
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
          <div className="box-h" style={{ borderTop: '1px solid var(--line)' }}>
            <b>available models</b>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{catalog.length}</span>
          </div>
          <div className="bd-tree" style={{ padding: '5px 0', flex: '0 1 34%', minHeight: 110, overflow: 'auto' }}>
            {catalog.length === 0 && (
              <div style={{ padding: '10px 12px', fontSize: 10.5, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                no catalog models found
              </div>
            )}
            {catalog.map(model => {
              const ports = Array.isArray(model.ports) ? model.ports : [];
              const protoList = [...new Set(ports.map(p => p && p.proto).filter(Boolean))].slice(0, 4);
              return (
                <div key={`${model.source}:${model.name}`} className="bd-tree-row"
                     title={`${model.ssot_path || ''}\n${ports.map(p => `${p.name}:${p.proto}/${p.role}`).join(' · ')}`}
                     onDoubleClick={() => addCatalogInstance(model)}
                     style={{ paddingLeft: 12, alignItems: 'flex-start' }}>
                  <span className="ico">{window.MOD_ICON[model.kind] || '◇'}</span>
                  <span style={{ flex: 1 }}>
                    <span style={{ display: 'block', color: 'var(--fg)' }}>{model.name}</span>
                    <span style={{ display: 'block', fontSize: 9, color: 'var(--fg-mute)', marginTop: 2 }}>
                      {model.kind || 'ip'} · {ports.length} ports
                    </span>
                  </span>
                  <span style={{ display: 'flex', gap: 3, flexWrap: 'wrap', justifyContent: 'flex-end', maxWidth: 76 }}>
                    {protoList.map(p => (
                      <span key={p} style={{
                        fontSize: 8, border: '1px solid var(--line)', padding: '0 3px',
                        color: p === 'APB' ? 'var(--magenta)' : p === 'IRQ' ? 'var(--warn)' : 'var(--accent)',
                      }}>{p}</span>
                    ))}
                    {['ssot-gen', 'rtl-gen', 'tb-gen', 'sim'].map(wf => (
                      <button key={wf}
                              title={`${wf} · .session/${normalizeArchitectSession(`${model.id || model.name}/${wf}`) || wf}`}
                              onClick={(e) => { e.stopPropagation(); dispatchJob(wf, model.id || model.name); }}
                              style={{
                                border: '1px solid var(--line)',
                                background: 'var(--bg-2)',
                                color: 'var(--fg-mute)',
                                font: '8px var(--mono)',
                                padding: '0 3px',
                                cursor: 'pointer',
                              }}>{wf.split('-')[0]}</button>
                    ))}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="box-h" style={{ borderTop: '1px solid var(--line)' }}>
            <b>workspace directory</b>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{workspaceTree?.children?.length || 0}</span>
          </div>
          <div className="bd-tree" style={{ padding: '5px 0', flex: '0 1 28%', minHeight: 100, overflow: 'auto' }}>
            {!workspaceTree && (
              <div style={{ padding: '10px 12px', fontSize: 10.5, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                workspace tree unavailable
              </div>
            )}
            {workspaceTree && (workspaceTree.children || []).map(n => renderWorkspaceNode(n, 0))}
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
              {view === 'soc' && tab === 'diagram' && (
                <div className="seg-tabs" title="top diagram density">
                  <button className={socTopMode === 'if' ? 'sel' : ''}
                          onClick={() => setSocTopMode('if')}>I/F</button>
                  <button className={socTopMode === 'detail' ? 'sel' : ''}
                          onClick={() => setSocTopMode('detail')}>detail</button>
                </div>
              )}
              {tab === 'diagram' && (
                <button className="btn"
                        style={{ fontSize: 10.5, padding: '3px 9px' }}
                        title="toggle block-diagram focus view"
                        onClick={() => {
                          setDiagramFocus(v => !v);
                          setTimeout(fitZoom, 40);
                        }}>
                  {diagramFocus ? 'show panels' : 'focus diagram'}
                </button>
              )}
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
            <div className={`bd-canvas ${view === 'soc' ? 'soc-carbon' : ''}`} style={{ flex: 1 }} ref={bdCanvasRef}
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
                      <th style={{ width: 180 }}>LIVE JOBS</th>
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
                      const rowJobs = (jobsByIp[r.module.id] || []).slice(0, 4);
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
                          <td><window.StatusTrio status={r.module.status}
                                                 detail={r.module.status_detail}
                                                 source={r.module.status_source}
                                                 big /></td>
                          <td>
                            {rowJobs.length === 0 ? (
                              <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>idle</span>
                            ) : (
                              <span style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                                {rowJobs.map(j => (
                                  <button key={j.job_id || j.run_id}
                                          className={`pill ${j.status === 'running' ? 'run' : j.status === 'completed' ? 'ok' : j.status === 'error' ? 'err' : ''}`}
                                          title={`${j.workflow} · ${j.status}\n${normalizeArchitectSession(j.session || '') || ''}\nclick to show worker log in chat`}
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            window.dispatchEvent(new CustomEvent('atlas:load-job-log', {
                                              detail: { jobId: j.job_id, live: j.status === 'running' },
                                            }));
                                          }}
                                          style={{ border: 0, cursor: 'pointer', fontSize: 9 }}>
                                    {j.status === 'running' ? '◌' : j.status === 'completed' ? '✓' : j.status === 'error' ? '✗' : j.status === 'queued' ? '…' : j.status === 'blocked' ? '⊘' : '○'} {j.workflow}
                                  </button>
                                ))}
                              </span>
                            )}
                          </td>
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
                            {rowJobs.length ? <span className="acc">worker · {rowJobs[0].workflow} · {rowJobs[0].status} · {rowJobs[0].run_id || rowJobs[0].job_id}</span>
                              : isErr ? <span className="err">✗ sim error · see sim log</span>
                              : r.module.status.sim === 'partial' ? <span className="warn">◐ partial sim artifacts</span>
                              : r.module.status.sim === 'pending' ? <span style={{ color: 'var(--fg-mute)' }}>○ no sim run data</span>
                              : touched ? <span className="acc">layout changed locally</span>
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
                    <window.StatusTrio status={selModule.status}
                                       detail={selModule.status_detail}
                                       source={selModule.status_source}
                                       big />
                    <span className="pill ok" style={{ fontSize: 9, marginLeft: 8 }}>synced</span>
                  </div>
                  <div style={{ flex: 1, overflow: 'auto' }}>
                    <window.ModuleProgressPanel module={selModule} />
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

        {/* RIGHT — vertical stack: JobTracker (collapsible) + chat. */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden',
                      borderLeft: '1px solid var(--line)', background: 'var(--panel)',
                      position: 'relative',
                      visibility: diagramFocus ? 'hidden' : 'visible' }}>
          <div className="arch-splitter right"
               title="resize chat"
               onMouseDown={(e) => beginPanelResize('right', e)} />
          <window.JobTracker jobs={jobs}
                             onLoadSession={(session) => {
                               const sid = normalizeArchitectSession(session);
                               if (!sid) return;
                               window.dispatchEvent(new CustomEvent('atlas:load-session-history', {
                                 detail: { session: sid },
                               }));
                             }}
                             onLoadJobLog={(jobId, live) => {
                               if (!jobId) return;
                               window.dispatchEvent(new CustomEvent('atlas:load-job-log', {
                                 detail: { jobId, live: !!live },
                               }));
                             }}
                             onSelectIp={(ip) => {
                               const lk = lookup[Object.keys(lookup).find(k => lookup[k].module.id === ip)];
                               if (lk) {
                                 setSelMod(`${lk.cluster.id}/${ip}`);
                                 setView(`cluster:${lk.cluster.id}`);
                               }
                             }} />
          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <window.ArchitectChat view={view} selModule={selModule} selCluster={selCluster}
                                  onDiagramPlan={applyDiagramPlan} />
          </div>
        </div>
      </div>

      {/* Block ⚡ dispatch menu — popover anchored to the button. */}
      {dispatchMenu && (
        <>
          <div onClick={() => setDispatchMenu(null)}
               style={{ position: 'fixed', inset: 0, zIndex: 999 }} />
          <div style={{
            position: 'fixed', left: dispatchMenu.x, top: dispatchMenu.y,
            zIndex: 1000, minWidth: 180,
            background: 'var(--panel)', border: '1px solid var(--line-2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
            font: '11px var(--mono)',
          }}>
            <div style={{ padding: '4px 10px', background: 'var(--bg-2)',
                          borderBottom: '1px solid var(--line)',
                          fontSize: 10, color: 'var(--fg-mute)',
                          letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              dispatch on <b style={{ color: 'var(--accent)' }}>{dispatchMenu.ip}</b>
            </div>
            <div className="bd-dispatch-item"
                 onClick={() => dispatchPipeline(dispatchMenu.ip)}>
              <span style={{ width: 14, textAlign: 'center', color: 'var(--accent)' }}>▶</span>
              <span style={{ flex: 1 }}>full — architect → post-STA</span>
            </div>
            <div style={{ height: 1, background: 'var(--line)', margin: '2px 0' }} />
            {[
              { wf: 'architect', icon: '◇', label: 'architect — SoC contract' },
              { wf: 'ssot-gen', icon: '◐', label: 'ssot-gen — refresh SSOT' },
              { wf: 'fl-model-gen', stage: 'fl-model', icon: 'ƒ', label: 'fl-model — functional model' },
              { wf: 'fl-model-gen', stage: 'cl-model', icon: 'λ', label: 'cl-model — cycle model' },
              { wf: 'fl-model-gen', stage: 'equivalence', icon: '≡', label: 'equivalence — FL vs RTL goals' },
              { wf: 'rtl-gen',  stage: 'rtl', icon: '⚙', label: 'rtl-gen — generate RTL' },
              { wf: 'lint',     stage: 'lint', icon: '✓', label: 'lint' },
              { wf: 'tb-gen',   stage: 'tb', icon: '⌬', label: 'tb-gen — testbench' },
              { wf: 'sim',      stage: 'sim', icon: '▶', label: 'sim' },
              { wf: 'coverage', stage: 'coverage', icon: '▤', label: 'coverage — function/cycle' },
              { wf: 'sim_debug', stage: 'sim-debug', icon: '◎', label: 'sim-debug' },
              { wf: 'syn',      stage: 'syn', icon: '⊕', label: 'syn' },
              { wf: 'dft',      stage: 'dft', icon: '⊗', label: 'dft' },
              { wf: 'sta',      stage: 'sta', icon: '⊞', label: 'sta' },
              { wf: 'pnr',      stage: 'pnr', icon: '▣', label: 'pnr' },
              { wf: 'sta-post', stage: 'sta-post', icon: '◆', label: 'post-sta' },
              { wf: 'sim_debug', stage: 'goal-audit', icon: '□', label: 'goal-audit' },
            ].map(o => (
              <div key={`${o.wf}:${o.stage || ''}`}
                   className="bd-dispatch-item"
                   onClick={() => dispatchJob(o.wf, dispatchMenu.ip, o.stage || '')}>
                <span style={{ width: 14, textAlign: 'center', color: 'var(--fg-mute)' }}>{o.icon}</span>
                <span style={{ flex: 1 }}>{o.label}</span>
              </div>
            ))}
          </div>
        </>
      )}

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
window.ArchitectChat = function ArchitectChat({ view, selModule, selCluster, onDiagramPlan }) {
  const normalizedView = String(view || 'architect').toLowerCase();
  const isPipelineChat = normalizedView === 'pipeline' || normalizedView === 'orchestrator';
  const [feed, setFeed] = React.useState([]);
  const [streaming, setStreaming] = React.useState(false);
  const [input, setInput] = React.useState('');
  const bufRef = React.useRef('');
  const feedRef = React.useRef(null);
  const jobLogPollRef = React.useRef(null);

  const replayMessages = React.useCallback((messages, session, path) => {
    const displaySession = normalizeArchitectSession(session) || 'default';
    const rows = [];
    rows.push({
      kind: 'agent',
      text: `[session] loaded .session/${displaySession}${path ? `\n${path}` : ''}`,
    });
    for (const m of messages || []) {
      const role = m.role || '';
      const content = typeof m.content === 'string'
        ? m.content
        : Array.isArray(m.content)
          ? m.content.map(x => typeof x === 'string' ? x : (x && x.text) || '').join('\n')
          : '';
      const text = String(content || '').trim();
      if (!text) continue;
      if (role === 'user') rows.push({ kind: 'user', text });
      else if (role === 'assistant') rows.push({ kind: 'agent', text: text.slice(0, 2400) });
      else if (role === 'tool') rows.push({ kind: 'obs', text: text.slice(0, 1600), tool: m.name || m.tool_call_id || '' });
    }
    setFeed(rows);
  }, []);

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

  React.useEffect(() => {
    const onLoadSession = async (ev) => {
      const session = normalizeArchitectSession(ev.detail && ev.detail.session);
      if (!session) return;
      setStreaming(true);
      try {
        const r = await fetch(`/api/session/history?session=${encodeURIComponent(session)}&limit=160`);
        const d = await r.json().catch(() => ({}));
        if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
        if (!d.exists) {
          setFeed([{ kind: 'agent', text: `[session] .session/${session}/conversation.json not found yet` }]);
        } else {
          replayMessages(d.messages || [], session, d.path);
        }
      } catch (e) {
        setFeed(l => [...l, { kind: 'agent', text: `[session error] ${e.message || e}` }]);
      } finally {
        setStreaming(false);
      }
    };
    window.addEventListener('atlas:load-session-history', onLoadSession);
    return () => window.removeEventListener('atlas:load-session-history', onLoadSession);
  }, [replayMessages]);

  const replayWorkerLog = React.useCallback((data) => {
    const job = data.job || {};
    const session = normalizeArchitectSession(job.session || '');
    const rows = [{
      kind: 'agent',
      text: `[worker] ${job.ip || '(soc)'} · ${job.workflow || '-'} · ${job.status || data.status || '-'}\n` +
            `job_id: ${job.job_id || '-'}\nrun_id: ${data.run_id || job.run_id || '-'}\n` +
            `session: .session/${session || '-'}`
    }];
    for (const e of data.entries || []) {
      const typ = e.type || '';
      const text = String(e.content || '').trim();
      if (!text) continue;
      if (typ === 'task') rows.push({ kind: 'user', text });
      else if (typ === 'action' || typ === 'tool_call') rows.push({ kind: 'action', text });
      else if (typ === 'observation' || typ === 'tool_result') rows.push({ kind: 'obs', text: text.slice(0, 2200), tool: typ });
      else if (typ === 'error') rows.push({ kind: 'agent', text: `[error] ${text}` });
      else if (typ === 'done' || typ === 'completion') rows.push({ kind: 'agent', text: `[done] ${text}` });
      else if (typ === 'response') rows.push({ kind: 'agent', text: text.slice(0, 2400) });
      else if (typ === 'iteration' || typ === 'system' || typ === 'context') rows.push({ kind: 'thought', text: `[${typ}] ${text}` });
    }
    setFeed(rows);
  }, []);

  React.useEffect(() => {
    const clearPoll = () => {
      if (jobLogPollRef.current) {
        clearInterval(jobLogPollRef.current);
        jobLogPollRef.current = null;
      }
    };
    const onLoadJobLog = async (ev) => {
      const jobId = ev.detail && ev.detail.jobId;
      const live = !!(ev.detail && ev.detail.live);
      if (!jobId) return;
      clearPoll();
      setStreaming(true);
      const loadOnce = async () => {
        try {
          const r = await fetch(`/api/job/${encodeURIComponent(jobId)}/log`);
          const d = await r.json().catch(() => ({}));
          if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
          replayWorkerLog(d);
          if ((d.job || {}).status && (d.job || {}).status !== 'running') {
            clearPoll();
            setStreaming(false);
          }
        } catch (e) {
          clearPoll();
          setFeed(l => [...l, { kind: 'agent', text: `[worker log error] ${e.message || e}` }]);
          setStreaming(false);
        }
      };
      await loadOnce();
      if (live) jobLogPollRef.current = setInterval(loadOnce, 2000);
      else setStreaming(false);
    };
    window.addEventListener('atlas:load-job-log', onLoadJobLog);
    return () => {
      clearPoll();
      window.removeEventListener('atlas:load-job-log', onLoadJobLog);
    };
  }, [replayWorkerLog]);

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
    const wantsDiagramPlan =
      /^\/diagram\b/i.test(text) ||
      /^\/(arch|move|mv|connect|cn|add|add-instance|instantiate|delete|del|remove|rm|layout|auto-?layout)\b/i.test(text) ||
      /(diagram|block|connect|move|layout|align|delete|remove|add|배치|정렬|옮겨|움직|연결|추가|삭제|제거|블록|다이어그램)/i.test(text);
    if (wantsDiagramPlan && typeof onDiagramPlan === 'function') {
      setStreaming(true);
      onDiagramPlan(text.replace(/^\/diagram\s*/i, ''))
        .then(res => {
          const notes = (res.notes || []).map(x => `- ${x}`).join('\n');
          setFeed(l => [...l, {
            kind: 'agent',
            text: `[diagram] ${res.summary || 'applied'}\n${notes}`.trim(),
          }]);
        })
        .catch(err => {
          setFeed(l => [...l, { kind: 'agent', text: `[diagram error] ${err.message || err}` }]);
        })
        .finally(() => setStreaming(false));
      return;
    }
    if (isPipelineChat && window.ATLAS_PIPELINE_CHAT_MODE === 'websocket') {
      setStreaming(true);
      const ipName = ((selModule && (selModule.name || selModule.id)) || activeSessionIp || '').trim();
      const policy = (typeof window.pipelinePolicyPayload === 'function')
        ? window.pipelinePolicyPayload()
        : {};
      const outbound = [
        '[ATLAS PIPELINE ORCHESTRATOR CHAT]',
        `- ip: ${ipName || 'active IP'}`,
        `- run_mode: ${policy.run_mode || 'engineering'}`,
        `- exec_mode: ${policy.exec_mode || 'orchestrator'}`,
        `- atlas_api_origin: ${window.location.origin}`,
        '',
        '[DIRECT EXECUTION RULES]',
        '- This right-side Pipeline chat is the real orchestrator control surface.',
        '- Treat /goal as a pipeline goal, not generic todo/plan mode.',
        '- Use read_pipeline_state(ip) for status/evidence reads; do not curl protected /api endpoints.',
        '- For worker/stage/run-to-green requests, call dispatch_workflow directly.',
        '- Do not call todo_add/todo_update/todo_write unless the user explicitly asks for a plan.',
        '- Do not fake pass status; require fresh artifact evidence before reporting success.',
        '',
        text,
      ].join('\n');
      if (window.backend) {
        window.backend.send({
          type: 'prompt',
          text: outbound,
          session: window.ACTIVE_SESSION || '',
          ui_lang: window.ATLAS_UI_LANG || 'en',
        });
      } else {
        setFeed(l => [...l, { kind: 'agent', text: '[error] backend websocket is not connected' }]);
        setStreaming(false);
      }
      return;
    }
    if (isPipelineChat) {
      setStreaming(true);
      const ipName = ((selModule && (selModule.name || selModule.id)) || activeSessionIp || '').trim();
      const policy = (typeof window.pipelinePolicyPayload === 'function')
        ? window.pipelinePolicyPayload()
        : {};
      fetch('/api/pipeline/orchestrator/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          ip: ipName,
          session: window.ACTIVE_SESSION || '',
          session_id: window.ATLAS_USER_SESSION_ID || window.ACTIVE_SESSION || '',
          ...policy,
        }),
      })
        .then(async r => {
          const d = await r.json().catch(() => ({}));
          if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
          const statusLine = d.reply || [
            `orchestrator ${d.status || 'updated'}`,
            d.run_id ? `run_id: ${d.run_id}` : '',
            d.ip ? `ip: ${d.ip}` : '',
          ].filter(Boolean).join('\n');
          setFeed(l => [...l, { kind: 'agent', text: statusLine }]);
          window.dispatchEvent(new CustomEvent('atlas:pipeline-poll', { detail: d }));
          if (d.action === 'dispatch') {
            window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', { detail: d }));
          }
        })
        .catch(err => {
          setFeed(l => [...l, { kind: 'agent', text: `[orchestrator error] ${err.message || err}` }]);
        })
        .finally(() => setStreaming(false));
      return;
    }
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
    if (window.backend) {
      window.backend.send({
        type: 'prompt',
        text: outbound,
        session: window.ACTIVE_SESSION || '',
        ui_lang: window.ATLAS_UI_LANG || 'en',
      });
    }
  };
  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const activeSessionIp = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean).slice(-2, -1)[0] || '';
  const scopeLabel = isPipelineChat ? `${(selModule && selModule.name) || activeSessionIp || 'active IP'} · orchestrator`
                   : view === 'soc' ? 'soc · architect'
                   : selModule ? `${selModule.name} · module`
                   : selCluster ? `${selCluster.id} · cluster`
                   : view.replace(':', ' · ');

  return (
    <div style={{ background: 'var(--panel)', borderLeft: '1px solid var(--line)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="box-h">
        <b>{isPipelineChat ? 'orchestrator chat' : `chat · ${normalizedView}`}</b>
        <span style={{ flex: 1 }} />
        <span className={`pill ${streaming ? 'run' : 'acc'}`} style={{ fontSize: 9 }}>
          {streaming ? 'react-loop · streaming' : 'react-loop · idle'}
        </span>
      </div>

      <div ref={feedRef} style={{ flex: 1, overflow: 'auto', padding: 14, fontSize: 12.5 }}>
        {feed.length === 0 && (
          <div style={{ color: 'var(--fg-mute)', fontSize: 11, fontStyle: 'italic', lineHeight: 1.6 }}>
            {isPipelineChat
              ? 'Orchestrator ready. Ask for status, run to green, retry a stage, or create an IP.'
              : 'architect commands: /move cortexa15_0 left, /connect cortexa15_0/M_ACE cci550/S0_ACE ACE, /add counter, /delete counter, /layout.'}
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
                 placeholder={isPipelineChat ? "Ask orchestrator…" : "/move · /connect · /add · /delete · /layout"} />
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


// ── JobTracker — collapsible list of dispatched HTTP-worker jobs ──
// Lives above ArchitectChat in the right column. Rows show:
//   <icon> <ip> <workflow> <runtime/iter> <cancel-x>
// Click a row → drill the architect view to that IP's cluster.
// Click cancel × → POST /api/job/<id>/cancel.
window.JobTracker = function JobTracker({ jobs, onSelectIp, onLoadSession, onLoadJobLog }) {
  const [open, setOpen] = React.useState(true);
  const live = (jobs || []).filter(j => j.status === 'running');
  const recent = (jobs || []).filter(j => j.status !== 'running');

  if ((jobs || []).length === 0) {
    // Compact "no active jobs" header so the user sees the slot exists.
    return (
      <div className="job-tracker" style={{ maxHeight: 32 }}>
        <div className="job-tracker-head" style={{ cursor: 'default', opacity: 0.6 }}>
          <span>jobs</span>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 9, fontStyle: 'italic' }}>no active dispatch — click ⚡ on a block</span>
        </div>
      </div>
    );
  }

  const fmtElapsed = (j) => {
    const t = j.duration_ms ? Math.round(j.duration_ms / 1000)
            : Math.round((Date.now() / 1000) - (j.started_at || 0));
    if (t < 60) return `${t}s`;
    return `${Math.floor(t / 60)}m${(t % 60).toString().padStart(2, '0')}s`;
  };

  const cancel = async (e, jobId) => {
    e.stopPropagation();
    try {
      await fetch(`/api/job/${jobId}/cancel`, { method: 'POST' });
    } catch (_) {}
  };

  const clearDone = async () => {
    try { await fetch('/api/jobs/clear', { method: 'POST' }); } catch (_) {}
  };

  return (
    <div className="job-tracker" style={!open ? { maxHeight: 28 } : null}>
      <div className="job-tracker-head" onClick={() => setOpen(o => !o)}>
        <span>{open ? '▾' : '▸'} jobs</span>
        {live.length > 0 && <span className="badge">{live.length}</span>}
        <span style={{ flex: 1 }} />
        {recent.length > 0 && (
          <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>
            {recent.length} done
            <span onClick={(e) => { e.stopPropagation(); clearDone(); }}
                  style={{ marginLeft: 8, cursor: 'pointer', color: 'var(--fg-mute)' }}
                  title="clear completed jobs">×</span>
          </span>
        )}
      </div>
      {open && (
        <div className="job-tracker-list">
          {[...live, ...recent].map(j => {
            const sym = j.status === 'running' ? '◌'
                      : j.status === 'completed' ? '✓'
                      : j.status === 'error' ? '✗'
                      : j.status === 'cancelled' ? '○'
                      : j.status === 'queued' ? '…'
                      : j.status === 'blocked' ? '⊘' : '·';
            const subtitle = j.status === 'running'
              ? `iter ${j.iterations || 0}`
              : j.status === 'error' ? (j.error || '').slice(0, 40)
              : j.status === 'completed' ? `+${(j.files_modified || []).length} files`
              : j.status === 'queued' ? `after ${j.depends_on || 'previous'}`
              : j.status === 'blocked' ? (j.error || 'blocked').slice(0, 40)
              : j.status;
            return (
              <div key={j.job_id || j.run_id}
                   className={`job-row ${j.status || ''}`}
                   title={`${j.workflow} on ${j.ip || '-'} · ${j.prompt || ''}\nworker: ${j.worker || '-'}\nrun_id: ${j.run_id || '-'}`}
                   onClick={() => j.ip && typeof onSelectIp === 'function' && onSelectIp(j.ip)}>
                <span className="icn">{sym}</span>
                <span className="ip">{j.ip || '(no ip)'}{' '}
                  <span style={{ color: 'var(--fg-mute)', fontSize: 9.5, fontWeight: 400 }}>· {subtitle}</span>
                </span>
                <span className="wf">{j.workflow}</span>
                <span className="meta">{fmtElapsed(j)}</span>
                {j.session && (
                  <span className="x"
                        onClick={(e) => {
                          e.stopPropagation();
                          const session = normalizeArchitectSession(j.session);
                          if (session) onLoadSession && onLoadSession(session);
                        }}
                        title={`reload session history: .session/${normalizeArchitectSession(j.session) || '-'}`}>↻</span>
                )}
                <span className="x"
                      onClick={(e) => {
                        e.stopPropagation();
                        onLoadJobLog && onLoadJobLog(j.job_id, j.status === 'running');
                      }}
                      title="show worker log in chat">▤</span>
                {j.status === 'running' ? (
                  <span className="x" onClick={(e) => cancel(e, j.job_id)}
                        title="cancel job">✕</span>
                ) : <span />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
