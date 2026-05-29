// soc-architect-canvas.tsx — the block-diagram canvas (pan/zoom/mini-map).
// TypeScript migration of soc-architect.jsx (strangler-fig split).
//
// SPLIT NOTE: this is the `{tab === 'diagram' && (...)}` canvas sub-tree of the
// SocArchitect render, lifted out UNCHANGED except for a single leading
// destructure from a `ctx` bag the component passes at call time. It reads a
// fixed, enumerable set of in-scope values (pan/zoom state, refs, the layout
// helpers) plus the three diagram render functions (themselves owned by
// soc-architect-diagrams.tsx and threaded through `ctx`). Behavior is identical.

export function renderDiagramCanvas(ctx: any): any {
  const {
    view, tab, soc, selMod, setSelMod, setView,
    zoom, setZoom, pan, setPan, panDragRef, bdCanvasRef, fitZoom,
    layers, toggleLayer, layout, setLayout, persistLayout, refreshSoc,
    isLive, miniOpen, setMiniOpen,
    renderSocView, renderClusterView, renderModuleView,
  } = ctx;
  if (tab !== 'diagram') return null;
  return (
            <div className={`bd-canvas ${view === 'soc' ? 'soc-carbon' : ''}`} style={{ flex: 1 }} ref={bdCanvasRef}
                 onWheel={(e) => {
                   // Cmd/Ctrl + wheel → zoom. Plain wheel → bubble up
                   // (for outer scroll if any). preventDefault on the
                   // zoom path so the page itself doesn't scroll.
                   if (!(e.ctrlKey || e.metaKey)) return;
                   e.preventDefault();
                   const delta = e.deltaY > 0 ? -8 : 8;
                   setZoom((z: any) => Math.max(20, Math.min(200, z + delta)));
                 }}
                 onMouseDown={(e) => {
                   // Pan the stage by dragging on empty canvas. Skip
                   // when the click hit a block — those have their own
                   // click/drag semantics. Right-click also pans.
                   const onBlock = (e.target as HTMLElement).closest && (e.target as HTMLElement).closest('.bd-block');
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
                   const onBlock = (e.target as HTMLElement).closest && (e.target as HTMLElement).closest('.bd-block');
                   if (!onBlock) setPan({ x: 0, y: 0 });
                 }}>
              <div className="bd-layers">
                <div className="ttl">layers</div>
                {Object.keys(layers).map(k => (
                  <label key={k}>
                    <input type="checkbox" checked={(layers as any)[k]} onChange={() => toggleLayer(k)} /><span>{k}</span>
                  </label>
                ))}
              </div>
              <div className="bd-zoom">
                <button onClick={() => setZoom((z: any) => Math.max(50, z - 10))}>−</button>
                <span className="pct">{zoom}%</span>
                <button onClick={() => setZoom((z: any) => Math.min(200, z + 10))}>+</button>
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
                          } catch (err: any) {
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
                const cc = soc.clusters.find((x: any) => x.id === cid);
                if (!cc) return null;
                const W = 1180, H = 720;
                const mw = 180, mh = Math.round(mw * H / W);
                // Recompute positions the same way renderClusterView
                // does (auto-grid + layout overrides) so the mini-map
                // matches exactly.
                const cols = Math.min(3, cc.modules.length);
                const blockW = 220;
                const partition = (m: any) => {
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
                const sizes = cc.modules.map((m: any) => ({ h: 24 + Math.max(76, partition(m) * 14 + 24) }));
                const maxBlockH = Math.max(140, ...sizes.map((s: any) => s.h));
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
                      {cc.modules.map((m: any, i: any) => {
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
  );
}
