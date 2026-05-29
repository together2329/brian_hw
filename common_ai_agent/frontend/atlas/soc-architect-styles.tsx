// soc-architect-styles.tsx — CSS injection for the soc-architect.tsx family
// (TypeScript migration of soc-architect.jsx, strangler-fig split).
//
// This is the verbatim `injectStyles` IIFE from the head of soc-architect.jsx,
// pulled into its own module so the main file stays focused on the component.
// It is a self-contained DOM side-effect (appends a <style id="arch-styles">
// once). The main file imports this module FIRST, for that side-effect, before
// rendering — preserving the original eval-time ordering.
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
