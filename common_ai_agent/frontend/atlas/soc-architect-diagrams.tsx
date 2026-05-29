// soc-architect-diagrams.tsx — the V7 diagram render closures.
// TypeScript migration of soc-architect.jsx (strangler-fig split).
//
// SPLIT NOTE: soc-architect.tsx's three diagram render closures
// (renderSocView / renderClusterView / renderModuleView) each read a fixed,
// enumerable set of in-scope SocArchitect values (soc, layout, layers, selMod,
// the drag refs, a few setters/helpers). They were hoisted out here UNCHANGED
// except for a single leading destructure of those values from a `ctx` bag the
// component passes in at call time. Behavior is identical — this is a pure
// mechanical lift to keep every file under 1000 lines.
//
// Cross-file components (PipelineStrip) are resolved through window at render
// time exactly as the legacy `window.X` JSX did, via the local `g`.
import { Fragment } from 'react';

const g = window as unknown as Record<string, any>;

// PipelineStrip is owned by soc-architect-pipeline.tsx and registered on
// window; resolve it at render time (matches the legacy window lookup).
const PipelineStrip = (props: any): any => g.PipelineStrip(props);

// ── renderSocView — top-level SoC overview (live IP instances + busses) ──
export function renderSocView(ctx: any): any {
  const {
    soc, socTopMode, layout, layers, selMod, pendingPort,
    setPendingPort, setSelMod, setView, getStageScale, blockDragRef,
    refreshSoc, isTouched,
  } = ctx;
    const W = 1180, H = 720;
    const modules: any[] = [];
    for (const c of soc.clusters || []) {
      for (const m of c.modules || []) modules.push({ cluster: c, module: m, ref: `${c.id}/${m.id}` });
    }
    const findRow = (id: any) => modules.find(r => r.module.id === id);
    const isAux = (it: any) => {
      const p = (it.proto || '').toUpperCase();
      return p === 'CLK' || p === 'RST';
    };
    const sizeOf = (m: any) => {
      const visible = (m.interfaces || []).filter((it: any) => socTopMode === 'detail' || !isAux(it));
      const n = Math.max(2, Math.min(5, visible.length));
      return { w: 236, h: Math.max(112, 50 + n * 20) };
    };
    const positions: Record<string, any> = {};
    const put = (id: any, x: any, y: any) => {
      const row = findRow(id); if (!row) return;
      const s = sizeOf(row.module);
      // Top SoC has its own layout namespace. Cluster-local saved
      // positions can be useful inside a cluster view but make the
      // full-chip diagram collapse when the same x/y are reused here.
      const ov = layout && (layout as any)[`top:${row.ref}`];
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
    const ifaceSide = (iface: any) => {
      const side = (iface.side || '').toLowerCase();
      const role = (iface.role || 'slave').toLowerCase();
      const proto = (iface.proto || '').toUpperCase();
      if (proto === 'CLK' || proto === 'RST') return 'left';
      if (side === 'top' || side === 'bottom' || side === 'left' || side === 'right') return side;
      return role === 'master' ? 'right' : 'left';
    };
    const sideList = (m: any, side: any) => (m.interfaces || [])
      .filter((it: any) => socTopMode === 'detail' || !isAux(it))
      .filter((it: any) => ifaceSide(it) === side)
      .slice(0, 5);
    const pinPoint = (m: any, ifaceName: any, preferSide: any) => {
      const p = positions[m.id]; if (!p) return null;
      const iface = (m.interfaces || []).find((it: any) => it.name === ifaceName) || {};
      const side = preferSide || ifaceSide(iface);
      const list = sideList(m, side);
      const idx = Math.max(0, list.findIndex((it: any) => it.name === ifaceName));
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
    const protoColor = (proto: any) => {
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
    const familyClass = (proto: any) => {
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
    const arrowFor = (iface: any) => {
      const role = (iface.role || 'slave').toLowerCase();
      const proto = (iface.proto || '').toUpperCase();
      if (proto === 'IRQ') return '↯';
      if (proto === 'CLK' || proto === 'RST') return '►';
      return role === 'master' ? '►' : '◄';
    };
    const connectPort = async (row: any, iface: any, e: any) => {
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
      } catch (err: any) {
        alert(`connect failed: ${err.message || err}`);
      }
    };
    const beginBlockDrag = (ref: any, layoutKey: any, p: any, e: any, maxX: any, maxY: any) => {
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
    const portClass = (m: any, it: any, side: any) => {
      const active = pendingPort && pendingPort.ip === m.id && pendingPort.iface === it.name;
      return `bd-port ${side}-side ${familyClass(it.proto)} ${active ? 'connecting' : ''}`;
    };
    const protoBadge = (it: any) => {
      const p = (it.proto || '').toUpperCase();
      if (!p || p === 'CLK' || p === 'RST') return null;
      return <span className="proto-badge">{p}</span>;
    };
    return (
      <Fragment>
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
              {top.length > 0 && <div className="bd-ports-edge top">{top.map((it: any, i: any) => (
                <span key={i} className={portClass(m, it, 'top')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}><span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}</span>
              ))}</div>}
              <div className="bd-ports">
                <div className="bd-ports-col left">
                  {left.map((it: any, i: any) => (
                    <span key={i} className={portClass(m, it, 'left')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}>
                      <span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}
                    </span>
                  ))}
                </div>
                <div className="bd-center-icon" aria-hidden="true" />
                <div className="bd-ports-col right">
                  {right.map((it: any, i: any) => (
                    <span key={i} className={portClass(m, it, 'right')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}>
                      {protoBadge(it)}<span className="nm">{it.name}</span><span className="arr">{arrowFor(it)}</span>
                    </span>
                  ))}
                </div>
              </div>
              {bottom.length > 0 && <div className="bd-ports-edge bottom">{bottom.map((it: any, i: any) => (
                <span key={i} className={portClass(m, it, 'bottom')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}><span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}</span>
              ))}</div>}
            </div>
          );
        })}
      </Fragment>
    );
}

// ── renderClusterView — Carbon SoC-Designer-style per-cluster view ──
export function renderClusterView(cid: any, ctx: any): any {
  const {
    soc, layout, layers, selMod, setSelMod, setView, setLayout,
    getStageScale, blockDragRef, persistLayout, isTouched,
    runningByIp, setDispatchMenu,
  } = ctx;
    const c = soc.clusters.find((c: any) => c.id === cid); if (!c) return null;
    const W = 1180, H = 720;

    // Per-module port partition: left side = slave + clk + rst,
    // right side = master, top/bottom honoured when explicitly set
    // (typical for IRQ in/out which Carbon-style diagrams place on
    // the top edge). Cap at 5 ports per side so the block doesn't
    // grow taller than its column gap.
    const partition = (m: any) => {
      const ifs = (m.interfaces || []);
      const left: any[] = []; const right: any[] = []; const top: any[] = []; const bottom: any[] = [];
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
    const sizeOf = (m: any) => {
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
    const maxBlockH = Math.max(140, ...sizes.map((s: any) => s.h));
    const gapX = Math.max(40, (W - cols * blockW) / (cols + 1));
    const gapY = Math.max(40, (H - rowsN * maxBlockH - 60) / (rowsN + 1));
    const positions: Record<string, any> = {};
    c.modules.forEach((m: any, i: any) => {
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
    const protoFamily = (p: any) => {
      const x = (p || '').toUpperCase();
      if (x === 'AXI' || x === 'AXI4' || x === 'AXI4L' || x === 'ACE' || x === 'AXIS') return 'axi';
      if (x === 'APB' || x === 'AHB') return 'apb';
      if (x === 'IRQ') return 'irq';
      return null;
    };
    const connections: any[] = [];
    if (layers.busses) {
      for (const m of c.modules) {
        const partA = partition(m);
        const headerH = 24;
        // For each master (right) on this module, try to find a
        // matching slave (left) on any other module with same family.
        partA.right.forEach((iface: any, i: any) => {
          const fam = protoFamily(iface.proto);
          if (!fam) return;
          for (const n of c.modules) {
            if (n.id === m.id) continue;
            const partB = partition(n);
            const j = partB.left.findIndex((x: any) => protoFamily(x.proto) === fam);
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
    const stubs: any[] = [];
    const ipToCluster: Record<string, any> = {};
    for (const cc of soc.clusters) for (const mm of cc.modules) ipToCluster[mm.id] = cc.id;
    const localIds = new Set(c.modules.map((x: any) => x.id));
    const allBusses = (soc && Array.isArray(soc.busses)) ? soc.busses : [];
    const stubColorClass = (proto: any) => {
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
      const part = partition(c.modules.find((x: any) => x.id === localInst) || {});
      const pos = positions[localInst]; if (!pos) continue;
      const headerH = 24;
      // Try to find the matching iface row inside left/right partition
      const idxR = part.right.findIndex((x: any) => x.name === localIface);
      const idxL = part.left.findIndex((x: any) => x.name === localIface);
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
      <Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {connections.length === 0 && layers.busses && (
            <>
              <line x1={60} y1={H/2} x2={W-60} y2={H/2} stroke={railColor} strokeWidth="3" opacity="0.4" />
              {c.modules.map((m: any) => {
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

        {c.modules.map((m: any) => {
          const p = positions[m.id];
          const ref = `${c.id}/${m.id}`;
          const sel = selMod === ref;
          const touched = isTouched(ref);
          const { left, right, top, bottom } = partition(m);
          const familyClass = (proto: any) => {
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
          const arrowFor = (iface: any) => {
            const role = (iface.role || 'slave').toLowerCase();
            const proto = (iface.proto || '').toUpperCase();
            if (proto === 'CLK' || proto === 'RST') return '►'; // input
            if (proto === 'IRQ') return role === 'master' ? '↯' : '↯';
            return role === 'master' ? '►' : '◄';
          };
          // Carbon-style instance name: "<name>[0]"  with type in parens.
          const instLabel = `${m.name || m.id}[0]`;
          const typeLabel = m.label && m.label !== m.name ? `(${m.label})` :
                            m.kind ? `(${(g.MOD_KIND_LABEL || {})[m.kind] || m.kind})` : '';
          const centerGlyph = (g.MOD_ICON || {})[m.kind] || 'C';
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
                     setLayout((prev: any) => ({ ...prev, [ref]: {
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
                       setLayout((prev: any) => { persistLayout(prev); return prev; });
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
      </Fragment>
    );
}

// ── renderModuleView — single-module inspector block ──
export function renderModuleView(ref: any, ctx: any): any {
  const { lookup, layers } = ctx;
    const lkm = lookup[ref]; if (!lkm) return null;
    const m = lkm.module;
    const W = 1180, H = 720;
    const blockW = 480, blockH = 320;
    const bx = (W - blockW) / 2, by = (H - blockH) / 2;
    const ifaces = m.interfaces || [];
    return (
      <Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {layers.busses && ifaces.map((iface: any) => {
            const sameSide = ifaces.filter((x: any) => x.side === iface.side);
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
            <span className="ico" style={{ fontSize: 16 }}>{g.MOD_ICON[m.kind]}</span>
            <span className="nm" style={{ fontSize: 16, color: 'var(--accent)' }}>{m.name}</span>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{g.MOD_KIND_LABEL[m.kind]}</span>
          </div>
          <div className="bd-block-body" style={{ padding: '12px 14px', justifyContent: 'flex-start', flexDirection: 'column', alignItems: 'stretch', gap: 10 }}>
            <div className="lbl" style={{ fontSize: 12, color: 'var(--fg-dim)' }}>{m.label}</div>
            {m.addr && <div className="addr" style={{ fontSize: 12 }}>addr · {m.addr}</div>}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
              {(m.params || []).map((p: any) => (
                <span key={p.k} style={{ fontSize: 10, fontFamily: 'var(--mono)', padding: '2px 7px', background: 'var(--bg-3)', border: '1px solid var(--line)', color: 'var(--fg-dim)' }}>
                  {p.k}=<b style={{ color: 'var(--fg)' }}>{p.v}</b>
                </span>
              ))}
            </div>
            <div style={{ marginTop: 6, fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>pipeline</div>
            <PipelineStrip status={m.status} modId={m.id} big />
          </div>
        </div>
      </Fragment>
    );
}
