// soc-architect-views.tsx — large self-contained JSX sub-trees of SocArchitect.
// TypeScript migration of soc-architect.jsx (strangler-fig split).
//
// SPLIT NOTE: these three pieces are JSX sub-trees of the SocArchitect render
// that each read a fixed, enumerable set of in-scope values. They were hoisted
// out UNCHANGED except for a single leading destructure from a `ctx` bag the
// component passes at call time, and a trivial guard around the popovers (which
// the parent previously expressed as `{dispatchMenu && (...)}` /
// `{sparkPop && (() => ...)()}`). Behavior is identical.
//
//   renderStatusGrid    — the [status grid] tab table + ssot.yaml editor pane
//   renderDispatchMenu  — the per-block ⚡ workflow dispatch popover
//   renderSparkPopover  — the sim-history sparkline hover popover
//
// StatusTrio / ModuleProgressPanel are resolved through window at render time
// (StatusTrio is owned by a still-legacy file; ModuleProgressPanel by
// soc-architect-pipeline.tsx) exactly as the legacy `window.X` JSX did.
import { normalizeArchitectSession } from './soc-architect-shared';

const g = window as unknown as Record<string, any>;

const StatusTrio = (props: any): any => g.StatusTrio(props);
const ModuleProgressPanel = (props: any): any => g.ModuleProgressPanel(props);

export function renderStatusGrid(ctx: any): any {
  const {
    filteredRows, selMod, setSelMod, setView, isTouched, runMeta, sparkBars,
    jobsByIp, setSparkPop, selModule, selCluster, soc,
  } = ctx;
  return (
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
                    {filteredRows.map((r: any) => {
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
                            <span className="g-mod-ico">{g.MOD_ICON[r.module.kind]}</span>
                            <b className="g-mod-nm">{r.module.name}</b>
                          </td>
                          <td className="g-clu">{r.cluster.id}</td>
                          <td><span className="g-kind">{g.MOD_KIND_LABEL[r.module.kind]}</span></td>
                          <td className="g-addr">{r.module.addr || <span style={{ color: 'var(--fg-mute)' }}>—</span>}</td>
                          <td><StatusTrio status={r.module.status}
                                                 detail={r.module.status_detail}
                                                 source={r.module.status_source}
                                                 big /></td>
                          <td>
                            {rowJobs.length === 0 ? (
                              <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>idle</span>
                            ) : (
                              <span style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                                {rowJobs.map((j: any) => (
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
                               onMouseLeave={() => setSparkPop((prev: any) => prev && prev.ref === r.ref ? null : prev)}>
                            {bars.length === 0 ? (
                              <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>—</span>
                            ) : (
                              <svg width={Math.max(40, bars.length * 11)} height="18" style={{ display: 'block' }}>
                                {bars.map((h: any, i: any) => (
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
                    <StatusTrio status={selModule.status}
                                       detail={selModule.status_detail}
                                       source={selModule.status_source}
                                       big />
                    <span className="pill ok" style={{ fontSize: 9, marginLeft: 8 }}>synced</span>
                  </div>
                  <div style={{ flex: 1, overflow: 'auto' }}>
                    <ModuleProgressPanel module={selModule} />
                    <pre className="code-pane" style={{ margin: 0, height: '100%', fontSize: 11.5 }}>
{selModule.id === 'spi' && soc.ssotYamlSpi ? soc.ssotYamlSpi : `# ${selModule.name}.ssot.yaml — generated
component:
  vendor:  atlas.io
  library: ${selCluster.id}
  name:    ${selModule.name}
  version: 0.1.0

parameters:
${(selModule.params || []).map((p: any) => `  - { name: ${p.k.toUpperCase().padEnd(8)}, value: ${p.v} }`).join('\n')}

busInterfaces:
${(selModule.interfaces || []).map((i: any) => `  - { name: ${i.name}, proto: ${i.proto}, role: ${i.role}, side: ${i.side} }`).join('\n')}
${selModule.addr ? `
memoryMap:
  - { name: regs, base: ${selModule.addr.split(' ')[0]}, range: 0x1000 }
` : ''}`}</pre>
                  </div>
                </div>
              )}
            </div>
  );
}

export function renderDispatchMenu(ctx: any): any {
  const { dispatchMenu, setDispatchMenu, dispatchPipeline, dispatchJob } = ctx;
  if (!dispatchMenu) return null;
  return (
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
  );
}

export function renderSparkPopover(ctx: any): any {
  const { sparkPop, lookup } = ctx;
  if (!sparkPop) return null;
  return (() => {
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
                  {hist.slice().reverse().map((r: any, i: any) => {
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
  })();
}
