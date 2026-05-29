// soc-architect-tree.tsx — the LEFT hierarchy / catalog / workspace panel.
// TypeScript migration of soc-architect.jsx (strangler-fig split).
//
// SPLIT NOTE: this is the `{/* LEFT — hierarchy tree */}` panel sub-tree of the
// SocArchitect render, lifted out UNCHANGED except for a single leading
// destructure from a `ctx` bag the component passes at call time. The
// renderWorkspaceNode recursion (which had empty useCallback deps and reads no
// component state) moved here too, as a plain module-level helper.
//
// _matchesQuery / _highlightMatch / normalizeArchitectSession come from
// soc-architect-shared; PipelineStrip is resolved through window at render time
// exactly as the legacy `window.X` JSX did.
import { Fragment } from 'react';
import {
  _matchesQuery,
  _highlightMatch,
  normalizeArchitectSession,
} from './soc-architect-shared';

const g = window as unknown as Record<string, any>;

const PipelineStrip = (props: any): any => g.PipelineStrip(props);

// Recursive workspace-directory row. Pure (reads only its args); was an
// empty-deps useCallback in the component.
function renderWorkspaceNode(node: any, depth = 0): any {
    if (!node) return null;
    const kids = Array.isArray(node.children) ? node.children : [];
    const artifacts = Array.isArray(node.artifacts) ? node.artifacts : [];
    const isIp = !!node.is_ip;
    return (
      <Fragment key={node.path || node.name}>
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
        {kids.slice(0, depth === 0 ? 80 : 24).map((k: any) => renderWorkspaceNode(k, depth + 1))}
      </Fragment>
    );
}

export function renderHierarchyPanel(ctx: any): any {
  const {
    diagramFocus, beginPanelResize, treeQuery, setTreeQuery, treeMatches,
    setSelMod, setView, soc, isTouched, view, deleteInstance, catalog,
    addCatalogInstance, dispatchJob, workspaceTree, selMod,
  } = ctx;
  return (
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
                if (e.key === 'Escape') { setTreeQuery(''); (e.target as HTMLInputElement).blur(); }
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
            {soc.clusters.map((c: any) => {
              // When a query is active, only emit clusters that have
              // at least one matching module. Empty clusters are hidden.
              const visibleModules = treeQuery
                ? c.modules.filter((m: any) => _matchesQuery(m, c.id, treeQuery))
                : c.modules;
              if (treeQuery && visibleModules.length === 0) return null;
              return (
              <Fragment key={c.id}>
                <div className={`bd-tree-row cluster ${view === `cluster:${c.id}` ? 'sel' : ''}`}
                     onClick={() => setView(`cluster:${c.id}`)} style={{ paddingLeft: 18 }}>
                  <span className="tw">▼</span>
                  <span className="ico">{c.id === 'cpu_ss' ? '◆' : c.id === 'mem_ss' ? '▦' : c.id === 'periph_ss' ? '⊟' : c.id === 'noc' ? '╫' : '∿'}</span>
                  <span style={{ flex: 1 }}>{c.id}</span>
                  <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{visibleModules.length}{treeQuery ? `/${c.modules.length}` : ''}</span>
                </div>
                {visibleModules.map((m: any) => {
                  const ref = `${c.id}/${m.id}`;
                  const touched = isTouched(ref);
                  return (
                    <div key={ref} className={`bd-tree-row ${selMod === ref ? 'sel' : ''} ${touched ? 'touched' : ''}`}
                         onClick={() => { setSelMod(ref); if (view === 'soc') setView(`cluster:${c.id}`); }}
                         onDoubleClick={() => setView(`module:${ref}`)}
                         style={{ paddingLeft: 38 }}>
                      <span className="tw">·</span>
                      <span className="ico">{g.MOD_ICON[m.kind]}</span>
                      <span style={{ flex: 1, fontSize: 11.5, color: m.status.sim === 'err' ? 'var(--err)' : undefined }}
                            dangerouslySetInnerHTML={{ __html: _highlightMatch(m.name, treeQuery) }} />
                      {touched && <span style={{ background: 'var(--accent)', color: 'var(--bg)', fontSize: 8, padding: '1px 4px', fontWeight: 700 }}>+</span>}
                      <PipelineStrip status={m.status} modId={m.id} />
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
              </Fragment>
              );
            })}
            {treeQuery && treeMatches.length === 0 && (
              <div style={{ padding: '12px 14px', fontSize: 'var(--ui-control-font-size)',
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
            {catalog.map((model: any) => {
              const ports: any[] = Array.isArray(model.ports) ? model.ports : [];
              const protoList = [...new Set(ports.map((p: any) => p && p.proto).filter(Boolean))].slice(0, 4);
              return (
                <div key={`${model.source}:${model.name}`} className="bd-tree-row"
                     title={`${model.ssot_path || ''}\n${ports.map((p: any) => `${p.name}:${p.proto}/${p.role}`).join(' · ')}`}
                     onDoubleClick={() => addCatalogInstance(model)}
                     style={{ paddingLeft: 12, alignItems: 'flex-start' }}>
                  <span className="ico">{g.MOD_ICON[model.kind] || '◇'}</span>
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
            {workspaceTree && (workspaceTree.children || []).map((n: any) => renderWorkspaceNode(n, 0))}
          </div>
          <div style={{ padding: 8, borderTop: '1px solid var(--line)', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.05em' }}>
            click → drill cluster · dbl-click → drill module
          </div>
        </div>
  );
}
