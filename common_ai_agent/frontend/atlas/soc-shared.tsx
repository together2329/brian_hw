// soc-shared.tsx — TypeScript migration of soc-shared.jsx.
//
// Shared primitives for the 5 SoC Architect variations.
//
// All variations share: ModuleCard, ClusterGroup, BusLine (orthogonal,
// auto-routed), BusBundle (signal lane expansion), StatusPill, RunBar,
// ProtocolLegend, AddrMapTable, IpxactPanel, PerModuleArtifacts.
//
// Visual language: traditional SoC-Designer look.
// - Sharp 1px borders, monospace labels, orthogonal routes
// - ATLAS dark palette already provided by styles.css tokens
// - Bus colors keyed off protocol name → CSS var
//
// What changed vs soc-shared.jsx:
//   - Proper ES module: typed exports + `import { Fragment } from 'react'`
//     instead of ambient global `React` + in-browser-babel compile.
//   - Transitional: still bridges to `window.*` at the bottom so not-yet-
//     migrated .jsx files keep resolving `window.ModuleCard`, etc.
//   - Cross-file globals `window.SOC` / `window.pinAt` are owned by the
//     still-legacy soc-data.jsx; they are read via a locally-typed view of
//     window (those entries are not yet in types/atlas-window.d.ts).
import { Fragment, type CSSProperties, type ReactNode } from 'react';

// ──────────────────────────────────────────────────────────────
// Local typed views of cross-file globals owned by soc-data.jsx
// (window.SOC / window.pinAt). These are not yet declared in
// types/atlas-window.d.ts, so we model their shape here and read
// them through a narrow cast — behavior is identical to window.X.
// ──────────────────────────────────────────────────────────────
interface SocProtocol {
  color: string;
  label: string;
  signals: string[];
}
interface SocPin {
  x: number;
  y: number;
  side: string;
  proto: string;
  role: string;
  label: string;
  width?: number;
}
interface SocModule {
  id: string;
  name: string;
  kind: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  addr?: string;
  params?: Array<{ k: string; v: string }>;
  status: Record<string, string>;
  interfaces?: Array<{
    side: string;
    name: string;
    proto: string;
    role: string;
    width?: number;
    lanes?: string;
    x?: number;
    y?: number;
  }>;
}
interface SocCluster {
  id: string;
  name: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  status: Record<string, string>;
  modules: SocModule[];
}
interface SocBus {
  id: string;
  proto: string;
  width?: number;
  from: string;
  to: string;
  label?: string;
  addr?: string | null;
  active?: boolean;
  status?: string;
}
interface SocAddrRegion {
  base: string;
  size: string;
  region: string;
  target: string;
}
interface SocModel {
  name: string;
  version: string;
  protocols: Record<string, SocProtocol>;
  clusters: SocCluster[];
  busses: SocBus[];
  addrMap: SocAddrRegion[];
}

// Narrow accessors for the soc-data.jsx-owned globals.
const socWin = window as unknown as {
  SOC: SocModel;
  pinAt: (qualifiedRef: string) => SocPin | null;
};

// --- One-time CSS injection for SoC-Architect-specific atoms ---------
(function () {
  if (typeof document === 'undefined' || document.getElementById('soc-styles')) return;
  const s = document.createElement('style');
  s.id = 'soc-styles';
  s.textContent = `
/* SoC Architect canvas */
.soc-canvas {
  position: relative;
  background: var(--bg);
  background-image:
    linear-gradient(rgba(120,150,180,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(120,150,180,0.04) 1px, transparent 1px);
  background-size: 8px 8px, 8px 8px;
  font-family: var(--mono);
  color: var(--fg);
  overflow: hidden;
}
.soc-canvas .cluster {
  position: absolute;
  border: 1px dashed var(--line-2);
  background: color-mix(in oklch, var(--panel) 75%, transparent);
  border-radius: 2px;
}
.soc-canvas .cluster .clu-h {
  position: absolute; top: -10px; left: 12px;
  background: var(--bg); padding: 0 8px;
  font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--fg-dim); display: flex; align-items: center; gap: 8px;
}
.soc-canvas .cluster .clu-h b { color: var(--accent); font-weight: 600; }
.soc-canvas .cluster .clu-h .ssize { color: var(--fg-mute); font-size: 10px; }

.soc-canvas .module {
  position: absolute;
  background: var(--panel);
  border: 1px solid var(--line-2);
  border-radius: 2px;
  cursor: pointer;
  transition: border-color 0.12s, box-shadow 0.12s;
  display: flex; flex-direction: column;
  font-family: var(--mono);
}
.soc-canvas .module:hover { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.soc-canvas .module.sel { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent), 0 0 18px color-mix(in oklch, var(--accent) 30%, transparent); }
.soc-canvas .module.sim-err { border-color: var(--err); }
.soc-canvas .module.sim-err::after {
  content: ''; position: absolute; top: -4px; right: -4px; width: 8px; height: 8px; border-radius: 50%;
  background: var(--err); box-shadow: 0 0 8px var(--err);
}

.soc-canvas .module .mod-h {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 8px; border-bottom: 1px solid var(--line);
  background: var(--bg-2);
  font-size: 11px;
}
.soc-canvas .module .mod-h .ico { font-size: 12px; opacity: 0.75; width: 14px; text-align: center; }
.soc-canvas .module .mod-h .nm { color: var(--fg); font-weight: 600; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.soc-canvas .module .mod-h .stat { display: flex; gap: 4px; font-size: 10px; }
.soc-canvas .module .mod-b {
  padding: 5px 8px; flex: 1;
  display: flex; flex-direction: column; gap: 3px;
  font-size: 10.5px; color: var(--fg-dim);
}
.soc-canvas .module .lbl { color: var(--fg); font-size: 11px; line-height: 1.2; }
.soc-canvas .module .pchips { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 2px; }
.soc-canvas .module .pchip {
  font-size: 9.5px; background: var(--tag-bg); border: 1px solid var(--line);
  padding: 0 5px; color: var(--fg-dim); white-space: nowrap; line-height: 14px; border-radius: 1px;
}
.soc-canvas .module .pchip b { color: var(--fg); font-weight: 500; }
.soc-canvas .module .addr {
  font-size: 10px; color: var(--cyan);
  font-family: var(--mono); letter-spacing: 0.02em;
}

/* status dots — ssot/rtl/sim per module */
.s-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; vertical-align: middle; }
.s-dot.ok      { background: var(--ok);      }
.s-dot.partial { background: var(--warn);    }
.s-dot.pending { background: var(--fg-mute); }
.s-dot.err     { background: var(--err); box-shadow: 0 0 6px var(--err); }
.s-dot.run     { background: var(--cyan); animation: blink 1s step-end infinite; }
.s-trio { display: inline-flex; align-items: center; gap: 4px; font-size: 9px; color: var(--fg-mute); letter-spacing: 0.04em; flex-wrap: wrap; }
.s-trio .chip { display: inline-flex; align-items: center; gap: 3px; padding: 1px 4px; border: 1px solid var(--line); background: color-mix(in oklch, var(--panel) 80%, transparent); }
.s-trio .lab { color: var(--fg-mute); font-size: 9px; text-transform: uppercase; }
.s-trio .val { color: var(--fg-dim); font-size: 9px; text-transform: uppercase; }
.s-row { display: flex; align-items: center; gap: 5px; font-size: 10px; }
.s-row .k { width: 28px; color: var(--fg-mute); text-transform: uppercase; letter-spacing: 0.08em; font-size: 9px; }

/* interface stub on edges (IP-XACT triangle/pin look) */
.iface {
  position: absolute;
  font-family: var(--mono); font-size: 9px;
  color: var(--fg-dim); pointer-events: auto;
  display: flex; align-items: center; gap: 3px;
  white-space: nowrap;
}
.iface .pin {
  width: 7px; height: 7px;
  background: var(--proto-color, var(--accent));
  border: 1px solid var(--bg);
  box-shadow: 0 0 0 1px var(--proto-color, var(--accent));
}
.iface.left   { transform: translate(-100%, -50%); }
.iface.right  { transform: translate(0, -50%); flex-direction: row; }
.iface.top    { transform: translate(-50%, -100%); flex-direction: column; }
.iface.bottom { transform: translate(-50%, 0); flex-direction: column; }
.iface .lbl { font-size: 9px; }

/* bus line layer — sits on top */
.bus-layer {
  position: absolute; inset: 0;
  pointer-events: none;
}
.bus-layer svg { width: 100%; height: 100%; overflow: visible; }
.bus-layer .bus-line {
  fill: none; stroke-width: 3;
  pointer-events: stroke; cursor: pointer;
  transition: stroke-width 0.12s;
}
.bus-layer .bus-line:hover { stroke-width: 5; }
.bus-layer .bus-line.sel  { stroke-width: 5; filter: drop-shadow(0 0 4px currentColor); }
.bus-layer .bus-label {
  pointer-events: auto; cursor: pointer;
  font-family: var(--mono); font-size: 10px;
}
.bus-layer .bus-label rect { fill: var(--bg); stroke: currentColor; stroke-width: 1; }
.bus-layer .bus-label text { fill: var(--fg); }
.bus-layer .bus-label .pproto { font-weight: 600; }

/* protocol → color mapping (consumed via inline style var --proto-color) */
.bus-cyan    { color: var(--cyan); }
.bus-magenta { color: var(--magenta); }
.bus-accent  { color: var(--accent); }
.bus-warn    { color: var(--warn); }
.bus-err     { color: var(--err); }
.bus-fg-dim  { color: var(--fg-dim); }

/* legend / chip */
.legend {
  display: flex; gap: 14px; font-size: 10px; color: var(--fg-dim);
  letter-spacing: 0.06em; text-transform: uppercase;
}
.legend .leg-item { display: flex; align-items: center; gap: 6px; }
.legend .leg-item .swatch {
  width: 14px; height: 3px; background: currentColor;
}

/* run-bar */
.run-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 0 12px; height: 40px;
  background: var(--panel); border-bottom: 1px solid var(--line);
}
.run-bar .grp { display: flex; gap: 1px; }
.run-bar .rb-btn {
  background: var(--bg-3); border: 1px solid var(--line);
  font-family: var(--mono); font-size: 11.5px;
  color: var(--fg); padding: 5px 12px; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px;
  border-radius: 0; letter-spacing: 0.04em;
}
.run-bar .rb-btn:hover { border-color: var(--accent); color: var(--accent); }
.run-bar .rb-btn.primary { background: var(--accent); color: var(--bg); border-color: var(--accent); }
.run-bar .rb-btn.primary:hover { background: var(--accent-2); color: var(--bg); }
.run-bar .rb-btn .icn { font-size: 10px; opacity: 0.85; }
.run-bar .rb-spacer { flex: 1; }
.run-bar .rb-meta {
  display: flex; gap: 14px; font-size: 11px; color: var(--fg-dim);
}
.run-bar .rb-meta b { color: var(--fg); font-weight: 500; }

/* lane expansion popover */
.bus-pop {
  position: absolute; z-index: 20;
  background: var(--panel); border: 1px solid var(--line-2);
  font-family: var(--mono); font-size: 11px;
  min-width: 280px; max-width: 360px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.bus-pop .bp-h {
  padding: 6px 10px; background: var(--bg-2); border-bottom: 1px solid var(--line);
  display: flex; align-items: center; gap: 8px;
  font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--fg-dim);
}
.bus-pop .bp-h b { color: var(--accent); font-weight: 600; }
.bus-pop .bp-h .pp {
  background: var(--tag-bg); border: 1px solid currentColor;
  padding: 0 5px; line-height: 14px; font-size: 9px;
}
.bus-pop .bp-body { padding: 6px 0; max-height: 320px; overflow-y: auto; }
.bus-pop .bp-row {
  padding: 2px 12px; display: grid;
  grid-template-columns: 14px 1fr 60px 28px;
  gap: 8px; font-size: 10.5px; color: var(--fg-dim);
}
.bus-pop .bp-row:hover { background: var(--bg-2); color: var(--fg); }
.bus-pop .bp-row .dr { font-family: var(--mono); color: var(--fg-mute); }
.bus-pop .bp-row .nm { color: var(--fg); font-family: var(--mono); }
.bus-pop .bp-foot {
  padding: 6px 10px; border-top: 1px solid var(--line); background: var(--bg-2);
  display: flex; align-items: center; gap: 8px; font-size: 10px;
}

/* drill-in tabs */
.dtabs {
  display: flex; gap: 0; background: var(--panel);
  border-bottom: 1px solid var(--line);
}
.dtab {
  padding: 7px 16px; font-size: 11.5px; cursor: pointer;
  font-family: var(--mono); letter-spacing: 0.06em;
  color: var(--fg-dim); border-right: 1px solid var(--line);
  display: flex; align-items: center; gap: 6px;
  text-transform: uppercase;
}
.dtab:hover { color: var(--fg); background: var(--bg-2); }
.dtab.active { color: var(--accent); background: var(--bg); border-bottom: 2px solid var(--accent); margin-bottom: -1px; }
.dtab .num { font-size: 9px; color: var(--fg-mute); }

/* address-map table */
.amap { font-family: var(--mono); font-size: 11px; width: 100%; border-collapse: collapse; }
.amap th, .amap td { padding: 4px 10px; border-bottom: 1px solid var(--line); text-align: left; }
.amap th { background: var(--bg-2); color: var(--fg-dim); font-weight: 500; font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; }
.amap tr:hover { background: var(--bg-2); }
.amap .base { color: var(--cyan); }
.amap .reg { color: var(--accent); font-weight: 500; }

/* code/yaml/xml view */
.code-pane {
  background: var(--bg); padding: 10px 14px;
  font-family: var(--mono); font-size: 11.5px;
  white-space: pre; color: var(--fg);
  border-top: 1px solid var(--line);
  overflow: auto; line-height: 1.6;
}

/* tiny prompt suggestion chip */
.sug-chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--bg-3); border: 1px solid var(--line);
  padding: 4px 10px; font-size: 11px; cursor: pointer;
  color: var(--fg-dim); border-radius: 2px;
  font-family: var(--mono);
}
.sug-chip:hover { border-color: var(--accent); color: var(--accent); }
.sug-chip .arrow { color: var(--fg-mute); }

/* tooltip */
.toolt {
  position: absolute; z-index: 30;
  background: var(--bg-3); border: 1px solid var(--line-2);
  font-family: var(--mono); font-size: 10.5px;
  color: var(--fg); padding: 4px 8px; pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}
  `;
  document.head.appendChild(s);
})();

// ──────────────────────────────────────────────────────────────
// Module type icons (ASCII-ish for the traditional look)
// ──────────────────────────────────────────────────────────────
export const MOD_ICON: Record<string, string> = {
  cpu:    '◆',
  bus:    '╫',
  mem:    '▤',
  periph: '◇',
  analog: '∿',
};
export const MOD_KIND_LABEL: Record<string, string> = {
  cpu: 'CPU', bus: 'BUS', mem: 'MEM', periph: 'PERIPH', analog: 'ANALOG',
};

// ──────────────────────────────────────────────────────────────
// Status helpers
// ──────────────────────────────────────────────────────────────
interface StatusTrioProps {
  status: Record<string, string>;
  detail?: Record<string, string>;
  source?: Record<string, string>;
  big?: boolean;
}
export function StatusTrio({ status, detail = {}, source = {}, big = false }: StatusTrioProps): ReactNode {
  const order = ['ssot', 'rtl', 'sim'];
  return (
    <span className="s-trio" style={big ? { fontSize: 11 } : (null as unknown as CSSProperties)}>
      {order.map(k => {
        const v = status[k] || 'pending';
        const d = detail[k] ? `\n${detail[k]}` : '';
        const src = source[k] ? `\nsource: ${source[k]}` : '';
        return (
        <span key={k} className={big ? 'chip' : ''}
              title={`${k}: ${v}${d}${src}`}
              style={!big ? { display: 'inline-flex', alignItems: 'center', gap: 3 } : (null as unknown as CSSProperties)}>
          <span className={`s-dot ${status[k] || 'pending'}`} />
          {big && <span className="lab">{k}</span>}
          {big && <span className="val">{v}</span>}
        </span>
      );})}
    </span>
  );
}

interface PrettyStatusProps {
  status: Record<string, string>;
}
export function PrettyStatus({ status }: PrettyStatusProps): ReactNode {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {['ssot', 'rtl', 'sim'].map(k => (
        <div key={k} className="s-row">
          <span className="k">{k}</span>
          <span className={`s-dot ${status[k] || 'pending'}`} />
          <span style={{ color: 'var(--fg-dim)' }}>{status[k] || 'pending'}</span>
        </div>
      ))}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// Module card — drawn at absolute (cluster.x+module.x, +module.y)
// ──────────────────────────────────────────────────────────────
interface ModuleCardProps {
  cluster: SocCluster;
  module: SocModule;
  selected?: boolean;
  onClick?: () => void;
  hideInterfaces?: boolean;
  compact?: boolean;
}
export function ModuleCard({ cluster, module: mod, selected, onClick, hideInterfaces, compact }: ModuleCardProps): ReactNode {
  const x = cluster.x + mod.x;
  const y = cluster.y + mod.y;
  const isErr = mod.status?.sim === 'err';
  return (
    <>
      <div
        className={`module ${selected ? 'sel' : ''} ${isErr ? 'sim-err' : ''}`}
        style={{ left: x, top: y, width: mod.w, height: mod.h }}
        onClick={(e) => { e.stopPropagation(); onClick && onClick(); }}
      >
        <div className="mod-h">
          <span className="ico">{MOD_ICON[mod.kind]}</span>
          <span className="nm">{mod.name}</span>
          <span className="stat"><StatusTrio status={mod.status} /></span>
        </div>
        <div className="mod-b">
          {!compact && <div className="lbl">{mod.label}</div>}
          {mod.addr && <div className="addr">{mod.addr}</div>}
          {!compact && mod.params && (
            <div className="pchips">
              {mod.params.slice(0, 4).map((p,i) => (
                <span key={i} className="pchip"><b>{p.k}</b>={p.v}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {!hideInterfaces && (mod.interfaces || []).map((iface, i) => {
        const px = socWin.pinAt(`${cluster.id}/${mod.id}/${iface.name}`);
        if (!px) return null;
        const proto = socWin.SOC.protocols[iface.proto];
        const colorVar = proto ? `var(--${proto.color === 'fg-dim' ? 'fg-dim' : proto.color})` : 'var(--fg-dim)';
        return (
          <div
            key={i}
            className={`iface ${iface.side}`}
            style={{
              left: px.x,
              top: px.y,
              ['--proto-color' as string]: colorVar,
            } as CSSProperties}
          >
            {iface.side === 'left' && <><span className="lbl">{iface.name}</span><span className="pin" /></>}
            {iface.side === 'right' && <><span className="pin" /><span className="lbl">{iface.name}</span></>}
            {iface.side === 'top' && <><span className="lbl">{iface.name}</span><span className="pin" /></>}
            {iface.side === 'bottom' && <><span className="pin" /><span className="lbl">{iface.name}</span></>}
          </div>
        );
      })}
    </>
  );
}

// ──────────────────────────────────────────────────────────────
// Cluster group — dashed outline + header
// ──────────────────────────────────────────────────────────────
interface ClusterGroupProps {
  cluster: SocCluster;
  children?: ReactNode;
}
export function ClusterGroup({ cluster, children }: ClusterGroupProps): ReactNode {
  const totalMods = cluster.modules.length;
  return (
    <div
      className="cluster"
      style={{ left: cluster.x, top: cluster.y, width: cluster.w, height: cluster.h }}
    >
      <div className="clu-h">
        <b>{cluster.name}</b>
        <span style={{ color: 'var(--fg-dim)' }}>· {cluster.label}</span>
        <span className="ssize">[ {totalMods} modules ]</span>
        <StatusTrio status={cluster.status} />
      </div>
      {children}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// Bus routing — orthogonal Manhattan path between two pins.
// Picks an L-shape based on side combination.
// ──────────────────────────────────────────────────────────────
interface XY { x: number; y: number; }
interface BusPathResult {
  d: string;
  mid: XY;
  fromOut?: XY;
  toOut?: XY;
}
export function computeBusPath(fromPin: SocPin | null, toPin: SocPin | null): BusPathResult {
  if (!fromPin || !toPin) return { d: '', mid: { x: 0, y: 0 } };
  const fx = fromPin.x, fy = fromPin.y, tx = toPin.x, ty = toPin.y;
  // Step out from each pin along its side direction, then connect orthogonally.
  const stepOut = (pin: SocPin, dist: number): XY => {
    if (pin.side === 'left')   return { x: pin.x - dist, y: pin.y };
    if (pin.side === 'right')  return { x: pin.x + dist, y: pin.y };
    if (pin.side === 'top')    return { x: pin.x, y: pin.y - dist };
    if (pin.side === 'bottom') return { x: pin.x, y: pin.y + dist };
    return { x: pin.x, y: pin.y };
  };
  const a = stepOut(fromPin, 18);
  const b = stepOut(toPin, 18);
  // Midpoint: pick a route that avoids zigzagging — split along whichever axis differs more.
  const useX = Math.abs(a.x - b.x) > Math.abs(a.y - b.y);
  const m1 = useX ? { x: (a.x + b.x) / 2, y: a.y } : { x: a.x, y: (a.y + b.y) / 2 };
  const m2 = useX ? { x: (a.x + b.x) / 2, y: b.y } : { x: b.x, y: (a.y + b.y) / 2 };
  const d = `M ${fx} ${fy} L ${a.x} ${a.y} L ${m1.x} ${m1.y} L ${m2.x} ${m2.y} L ${b.x} ${b.y} L ${tx} ${ty}`;
  const mid = { x: (m1.x + m2.x) / 2, y: (m1.y + m2.y) / 2 };
  return { d, mid, fromOut: a, toOut: b };
}

// arrowhead path
export function arrowHeadPath(toPin: SocPin, size = 6): string {
  const { x, y, side } = toPin;
  if (side === 'left')   return `M ${x} ${y} L ${x-size} ${y-size/2} L ${x-size} ${y+size/2} Z`;
  if (side === 'right')  return `M ${x} ${y} L ${x+size} ${y-size/2} L ${x+size} ${y+size/2} Z`;
  if (side === 'top')    return `M ${x} ${y} L ${x-size/2} ${y-size} L ${x+size/2} ${y-size} Z`;
  if (side === 'bottom') return `M ${x} ${y} L ${x-size/2} ${y+size} L ${x+size/2} ${y+size} Z`;
  return '';
}

// ──────────────────────────────────────────────────────────────
// BusLayer — draws all busses as a single SVG overlay
// ──────────────────────────────────────────────────────────────
interface BusLayerProps {
  busses: SocBus[];
  selected?: string | null;
  onSelect?: (id: string) => void;
  hovered?: string | null;
  onHover?: (id: string | null) => void;
  animate?: boolean;
}
export function BusLayer({ busses, selected, onSelect, hovered, onHover, animate = false }: BusLayerProps): ReactNode {
  return (
    <div className="bus-layer">
      <svg>
        <defs>
          {/* dashed pattern for clk/inactive */}
        </defs>

        {busses.map(b => {
          const fromPin = socWin.pinAt(b.from);
          const toPin   = socWin.pinAt(b.to);
          if (!fromPin || !toPin) return null;
          const { d, mid } = computeBusPath(fromPin, toPin);
          const proto = socWin.SOC.protocols[b.proto];
          const colorClass = `bus-${proto?.color || 'fg-dim'}`;
          const isSel = selected === b.id;
          const isErr = b.status === 'err';
          const isInactive = b.active === false;
          const stroke = isErr ? 'var(--err)' : `var(--${proto?.color || 'fg-dim'})`;
          const ah = arrowHeadPath(toPin, 7);
          return (
            <g key={b.id} className={colorClass}
               onMouseEnter={() => onHover && onHover(b.id)}
               onMouseLeave={() => onHover && onHover(null)}>
              <path
                d={d}
                className={`bus-line ${isSel ? 'sel' : ''}`}
                stroke={stroke}
                strokeOpacity={isInactive ? 0.45 : 1}
                strokeDasharray={b.proto === 'CLK' ? '4 4' : isInactive ? '6 4' : 'none'}
                onClick={(e) => { e.stopPropagation(); onSelect && onSelect(b.id); }}
              />
              {animate && b.active && (
                <path d={d} stroke={stroke} strokeWidth={3} fill="none" strokeOpacity={0.55}
                      strokeDasharray="4 16">
                  <animate attributeName="stroke-dashoffset" from="0" to="-40" dur="1.4s" repeatCount="indefinite" />
                </path>
              )}
              {/* arrowhead at destination */}
              <path d={ah} fill={stroke} fillOpacity={isInactive ? 0.4 : 1} />
              {/* label */}
              <g className="bus-label" transform={`translate(${mid.x}, ${mid.y})`}
                 onClick={(e) => { e.stopPropagation(); onSelect && onSelect(b.id); }}>
                <rect x={-46} y={-10} width={92} height={20} rx={1} fill="var(--bg)" stroke={stroke} strokeWidth={1} />
                <text textAnchor="middle" y={-1} style={{ fontSize: 9.5, fill: stroke, fontWeight: 600, letterSpacing: 0.08, textTransform: 'uppercase' }}>
                  {proto?.label || b.proto}
                </text>
                <text textAnchor="middle" y={9} style={{ fontSize: 9, fill: 'var(--fg-dim)' }}>
                  {b.width ? `${b.width}b` : b.label || ''}
                </text>
              </g>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// BusPopover — signal lane list shown when a bus line is clicked
// ──────────────────────────────────────────────────────────────
interface BusPopoverProps {
  bus: SocBus | null;
  x: number;
  y: number;
  onClose?: () => void;
  onJumpDebug?: () => void;
}
export function BusPopover({ bus, x, y, onClose, onJumpDebug }: BusPopoverProps): ReactNode {
  if (!bus) return null;
  const proto = socWin.SOC.protocols[bus.proto];
  const sigs = proto?.signals || [];
  const colorClass = `bus-${proto?.color || 'fg-dim'}`;
  return (
    <div className={`bus-pop ${colorClass}`} style={{ left: x, top: y }}>
      <div className="bp-h">
        <b>{bus.id}</b>
        <span className="pp" style={{ color: 'currentColor' }}>{proto?.label || bus.proto}</span>
        <span style={{ color: 'var(--fg)' }}>{bus.width}b · {bus.label}</span>
        <span style={{ flex: 1 }} />
        <span style={{ cursor: 'pointer', color: 'var(--fg-mute)', fontSize: 14 }} onClick={onClose}>×</span>
      </div>
      <div className="bp-body">
        {sigs.map((s, i) => (
          <div key={i} className="bp-row">
            <span className="dr">{s.startsWith('aw') || s.startsWith('w') || s.startsWith('ar') || s.startsWith('p') && !s.startsWith('pr') ? '→' : s.startsWith('r') || s.startsWith('b') || s.startsWith('pr') ? '←' : '·'}</span>
            <span className="nm">{s}</span>
            <span style={{ color: 'var(--fg-mute)', fontSize: 9.5 }}>{s.includes('valid') || s.includes('ready') ? '1b' : ''}</span>
            <span style={{ color: 'var(--fg-mute)' }}>·</span>
          </div>
        ))}
      </div>
      <div className="bp-foot">
        <span style={{ color: 'var(--fg-dim)' }}>{sigs.length} signals · bundled</span>
        <span style={{ flex: 1 }} />
        <button className="btn" style={{ padding: '2px 8px', fontSize: 10.5 }} onClick={onJumpDebug}>open in sim-debug</button>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// Top run-bar
// ──────────────────────────────────────────────────────────────
interface RunBarProps {
  scope?: string;
  running?: string | null;
  onRun?: (kind: string) => void;
  extraRight?: ReactNode;
}
export function RunBar({ scope = 'all', running = null, onRun, extraRight }: RunBarProps): ReactNode {
  return (
    <div className="run-bar">
      <span style={{ color: 'var(--fg-dim)', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', marginRight: 4 }}>
        scope · <span style={{ color: 'var(--accent)' }}>{scope}</span>
      </span>
      <div className="grp">
        <button className="rb-btn" onClick={() => onRun && onRun('ssot')}>
          <span className="icn">{running === 'ssot' ? <span className="spinner" /> : '▸'}</span>
          generate ssot
        </button>
        <button className="rb-btn" onClick={() => onRun && onRun('rtl')}>
          <span className="icn">{running === 'rtl' ? <span className="spinner" /> : '▸'}</span>
          generate rtl
        </button>
        <button className="rb-btn primary" onClick={() => onRun && onRun('sim')}>
          <span className="icn">{running === 'sim' ? <span className="spinner" /> : '▸'}</span>
          run sim
        </button>
        <button className="rb-btn" onClick={() => onRun && onRun('all')}>
          <span className="icn">⏵</span>
          full pipeline
        </button>
      </div>
      <span className="rb-spacer" />
      <span className="rb-meta">
        <span>modules · <b>{socWin.SOC.clusters.reduce((s,c)=>s+c.modules.length,0)}</b></span>
        <span>busses · <b>{socWin.SOC.busses.length}</b></span>
        <span>addr regions · <b>{socWin.SOC.addrMap.length}</b></span>
      </span>
      {extraRight}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// Protocol legend
// ──────────────────────────────────────────────────────────────
export function ProtocolLegend(): ReactNode {
  const items = [
    { p: 'AXI4', cls: 'bus-cyan' },
    { p: 'AXI4-Lite', cls: 'bus-cyan' },
    { p: 'ACE', cls: 'bus-cyan' },
    { p: 'AHB', cls: 'bus-accent' },
    { p: 'APB', cls: 'bus-magenta' },
    { p: 'IRQ', cls: 'bus-warn' },
    { p: 'CLK', cls: 'bus-fg-dim' },
  ];
  return (
    <div className="legend">
      {items.map(it => (
        <span key={it.p} className={`leg-item ${it.cls}`}>
          <span className="swatch" /> <span>{it.p}</span>
        </span>
      ))}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────
// Address-map table
// ──────────────────────────────────────────────────────────────
interface AddrMapTableProps {
  map: SocAddrRegion[];
  onPick?: (r: SocAddrRegion) => void;
}
export function AddrMapTable({ map, onPick }: AddrMapTableProps): ReactNode {
  return (
    <table className="amap">
      <thead><tr><th>BASE</th><th>SIZE</th><th>REGION</th><th>TARGET</th></tr></thead>
      <tbody>
        {map.map((r, i) => (
          <tr key={i} onClick={() => onPick && onPick(r)} style={{ cursor: onPick ? 'pointer' : 'default' }}>
            <td className="base">{r.base}</td>
            <td>{r.size}</td>
            <td className="reg">{r.region}</td>
            <td style={{ color: 'var(--fg-dim)' }}>{r.target}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ──────────────────────────────────────────────────────────────
// Title / footer reused
// ──────────────────────────────────────────────────────────────
interface SocTitleProps {
  subtitle?: ReactNode;
  right?: ReactNode;
}
export function SocTitle({ subtitle, right }: SocTitleProps): ReactNode {
  return (
    <div className="vt-title titlebar" style={{ background: 'var(--panel)' }}>
      <span className="tb-dot" />
      <span><b>ATLAS</b> · soc-architect</span>
      <span className="tb-pipe">│</span>
      <span><b>{socWin.SOC.name}</b> v{socWin.SOC.version}</span>
      {subtitle && (<>
        <span className="tb-pipe">│</span>
        <span style={{ color: 'var(--accent)' }}>{subtitle}</span>
      </>)}
      <span className="tb-spacer" />
      {right}
    </div>
  );
}

interface SocStatusItem {
  kind?: string;
  text: ReactNode;
  color?: string;
}
interface SocStatusProps {
  items: SocStatusItem[];
}
export function SocStatus({ items }: SocStatusProps): ReactNode {
  return (
    <div className="statusbar">
      {items.map((it, i) => (
        <Fragment key={i}>
          {it.kind === 'tag' ? <span className="sb-tag">{it.text}</span> : <span style={{ color: it.color || 'inherit' }}>{it.text}</span>}
          {i < items.length - 1 && <span style={{ color: 'var(--line-2)' }}>│</span>}
        </Fragment>
      ))}
      <span className="sb-spacer" />
      <span><ProtocolLegend /></span>
    </div>
  );
}

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// Type-checked against types/atlas-window.d.ts (entries to be added as the
// surface migrates). Remove each line once all consumers import directly.
const w = window as unknown as Record<string, unknown>;
w.MOD_ICON = MOD_ICON;
w.MOD_KIND_LABEL = MOD_KIND_LABEL;
w.StatusTrio = StatusTrio;
w.PrettyStatus = PrettyStatus;
w.ModuleCard = ModuleCard;
w.ClusterGroup = ClusterGroup;
w.computeBusPath = computeBusPath;
w.arrowHeadPath = arrowHeadPath;
w.BusLayer = BusLayer;
w.BusPopover = BusPopover;
w.RunBar = RunBar;
w.ProtocolLegend = ProtocolLegend;
w.AddrMapTable = AddrMapTable;
w.SocTitle = SocTitle;
w.SocStatus = SocStatus;
