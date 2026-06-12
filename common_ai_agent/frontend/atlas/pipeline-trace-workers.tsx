// pipeline-trace-workers.tsx — WorkerOrchestraBar + OrchestratorTraceStrip
// extracted from pipeline-trace.tsx (Phase: sub-1000 split). Both render live
// orchestrator/worker telemetry polled from /api/orchestrator/trace and the
// worker snapshot helper. They own their own window bridges.
import { useState, useEffect, useMemo } from 'react';
import {
  type OrchestratorDecisionTrace,
  type TraceEvent,
  type WorkerInfo,
  type WorkerSnapshot,
  type WorkerOrchestraBarProps,
  type OrchestratorTraceStripProps,
} from './pipeline-trace-shared';
import { win } from './pipeline-trace-shared';

const workerIdentityLabel = (worker: WorkerInfo): string => {
  const owner = String(worker.worker_owner || '').trim();
  const workspace = String(worker.workspace_session || '').trim();
  if (owner && workspace && workspace !== 'default') return `${owner}/${workspace}`;
  if (owner) return owner;
  return '';
};

const activeWorkspaceSession = (): string => {
  const explicit = String(win.ATLAS_WORKSPACE_SESSION_ID || '').trim();
  if (explicit) return explicit;
  const parts = String(win.ACTIVE_SESSION || '').split('/').filter(Boolean);
  return parts.length >= 4 ? parts[1] || '' : '';
};

const orchestratorTraceUrl = (ip: string, limit: number): string => {
  const params = new URLSearchParams({ ip, limit: String(limit) });
  const workspaceSession = activeWorkspaceSession();
  if (workspaceSession) params.set('workspace_session', workspaceSession);
  return `/api/orchestrator/trace?${params.toString()}`;
};

const orchestratorRunTraceUrl = (ip: string, limit: number): string => {
  const params = new URLSearchParams({ ip, limit: String(limit) });
  const workspaceSession = activeWorkspaceSession();
  if (workspaceSession) params.set('workspace_session', workspaceSession);
  return `/api/orchestrator/runs/latest/trace?${params.toString()}`;
};

export function WorkerOrchestraBar({ ip, onSelectTarget, currentTarget }: WorkerOrchestraBarProps) {
  const [data, setData] = useState<WorkerSnapshot>({ orchestrator: {}, workers: [] });
  const [traceMap, setTraceMap] = useState<Record<string, TraceEvent>>({}); // worker -> latest event
  useEffect(() => {
    let dead = false;
    const fetchAll = async () => {
      try {
        const j = await win.pipelineFetchWorkerSnapshot!({ ip, activeOnly: true });
        if (!dead) setData(j || { workers: [] });
      } catch (_) {}
      try {
        if (!ip) return;
        const r2 = await fetch(orchestratorTraceUrl(ip, 30));
        if (!r2.ok) return;
        const j2 = await r2.json();
        if (dead) return;
        const m: Record<string, TraceEvent> = {};
        const evs: TraceEvent[] = (j2 && j2.events) || [];
        for (const e of evs) {
          const a = e.actor || '';
          if (!a.endsWith('-worker')) continue;
          const wf = a.replace(/-worker$/, '');
          if (!m[wf] || (m[wf].step as number) < (e.step as number)) m[wf] = e;
        }
        setTraceMap(m);
      } catch (_) {}
    };
    fetchAll();
    const t = setInterval(fetchAll, 3000);
    return () => { dead = true; clearInterval(t); };
  }, [ip]);
  const orch = data.orchestrator || {};
  const workers = data.workers || [];
  const activeTarget = orch.active_target || null;
  const kindArrow = (k?: string) => {
    if (!k) return { dir: 'none', color: 'muted', label: '' };
    if (k === 'http_send' || k === 'http_recv') return { dir: 'down', color: 'amber', label: 'dispatch' };
    if (k === 'http_accepted') return { dir: 'down', color: 'green', label: 'accepted' };
    if (k === 'http_rejected') return { dir: 'down', color: 'red', label: 'rejected' };
    if (k === 'run_completed') return { dir: 'up', color: 'cyan', label: 'completed' };
    if (k === 'gate_verdict') return { dir: 'up', color: 'purple', label: 'gate' };
    return { dir: 'none', color: 'muted', label: k };
  };
  const dataFlow = (w: WorkerInfo, ev?: TraceEvent) => {
    if (w.status === 'mismatch') return 'down';
    if (w.status !== 'ok') return 'down';
    if ((w.running_count as number) > 0) return 'dispatch';
    if (ev && ev.kind === 'run_completed') return 'return';
    return 'idle';
  };
  const flowArrow = (flow: string) => {
    if (flow === 'dispatch') return '↓';
    if (flow === 'return') return '↑';
    if (flow === 'down') return '✗';
    return '·';
  };
  const stateLabel = (w: WorkerInfo) => {
    if (w.status === 'mismatch') return 'mismatch';
    if (w.status !== 'ok') return 'unreachable';
    if ((w.running_count as number) > 0) return `run #${w.running && w.running[0] && w.running[0].run_id ? w.running[0].run_id.slice(-6) : '?'}`;
    return 'idle';
  };
  const runningTotal = workers.filter(w => (w.running_count as number) > 0).length;
  return (
    <div className="pipe-orchestra worker-bar" data-on={orch.enabled ? 'yes' : 'no'}>
      <div className="pipe-orchestra-conductor">
        <div className="worker-bar-head">
          <span className="worker-bar-title pipe-orchestra-conductor-name">WORKERS</span>
          <span className="worker-bar-sub pipe-orchestra-conductor-activity">
            {activeTarget
              ? <><b>{runningTotal}</b> dispatched · target <b>{activeTarget}</b></>
              : <><b>{runningTotal}</b> running · orchestrator {orch.enabled ? 'ON' : 'OFF'}</>}
          </span>
          <span className="worker-bar-legend">
            <span className="leg-disp"><i>↓</i> dispatch</span>
            <span className="leg-ret"><i>↑</i> return</span>
            <span className="leg-idle"><i>·</i> idle</span>
            <span className="leg-down"><i>✗</i> down</span>
          </span>
        </div>
      </div>
      <div className="pipe-orchestra-workers worker-grid">
        {workers.map(w => {
          const ev = traceMap[w.workflow];
          const arrow = kindArrow(ev && ev.kind);
          const live = (w.running_count as number) > 0;
          const reachable = w.status === 'ok';
          const mismatch = w.status === 'mismatch';
          const sel = currentTarget === w.workflow;
          const flow = dataFlow(w, ev);
          const identity = workerIdentityLabel(w);
          const opensWorkspace = win.PIPELINE_WORKSPACE_WORKFLOWS
            && win.PIPELINE_WORKSPACE_WORKFLOWS.has(w.workflow);
          const baseTitle = opensWorkspace
            ? `Open ${w.workflow} workspace and history`
            : (mismatch && w.mismatch_reasons && w.mismatch_reasons.length
                ? w.mismatch_reasons.join('\n')
                : `Click to set chat target to ${w.workflow}`);
          const cardTitle = identity ? `${baseTitle}\nscope: ${identity}` : baseTitle;
          return (
            <button key={w.workflow}
                    className="pipe-orchestra-worker worker-card"
                    data-flow={flow}
                    data-state={mismatch ? 'mismatch' : (reachable ? (live ? 'running' : 'idle') : 'down')}
                    data-selected={sel ? 'yes' : 'no'}
                    onClick={() => {
                      if (opensWorkspace && win.openPipelineWorkflowWorkspace) {
                        win.openPipelineWorkflowWorkspace({ ip, workflow: w.workflow });
                        return;
                      }
                      if (onSelectTarget) onSelectTarget(w.workflow);
                    }}
                    title={cardTitle}>
              <span className="worker-card-arrow pipe-orchestra-arrow">
                {flowArrow(flow)}
              </span>
              <span className="worker-card-name pipe-orchestra-worker-head">
                <span className="pipe-orchestra-worker-dot" data-live={live ? 'yes' : 'no'} />
                <span className="pipe-orchestra-worker-name">{w.workflow}</span>
                {sel && <span className="to-badge pipe-orchestra-worker-sel">TO</span>}
              </span>
              {identity && (
                <span className="worker-card-owner pipe-orchestra-worker-owner">{identity}</span>
              )}
              <span className="worker-card-state pipe-orchestra-worker-state">
                {stateLabel(w)}
              </span>
              <span className="worker-card-model pipe-orchestra-worker-model">
                {w.model || w.profile || '?'}
                {w.reasoning_effort && (
                  <span className="pipe-orchestra-worker-effort"> {w.reasoning_effort}</span>
                )}
                {w.toolchain && (
                  <span className="pipe-orchestra-worker-toolchain"> {w.toolchain}</span>
                )}
              </span>
              <span className="worker-card-trace pipe-orchestra-worker-trace" data-color={arrow.color}>
                {ev ? `${arrow.label} · step #${ev.step}` : '— no recent trace'}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function OrchestratorTraceStrip({ ip }: OrchestratorTraceStripProps) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [decisionTrace, setDecisionTrace] = useState<OrchestratorDecisionTrace | null>(null);
  const [open, setOpen] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  useEffect(() => {
    if (!ip) { setEvents([]); setDecisionTrace(null); return; }
    let dead = false;
    const fetchOnce = async () => {
      let hasDecisionTrace = false;
      try {
        const r = await fetch(orchestratorRunTraceUrl(ip, 50));
        if (r.ok) {
          const j = await r.json();
          if (!dead && j && j.run_id && Array.isArray(j.steps)) {
            setDecisionTrace(j);
            setEvents([]);
            hasDecisionTrace = true;
          } else if (!dead) {
            setDecisionTrace(null);
          }
        }
      } catch (_) {
        if (!dead) setDecisionTrace(null);
      }
      if (hasDecisionTrace) return;
      try {
        const r = await fetch(orchestratorTraceUrl(ip, 20));
        if (!r.ok) return;
        const j = await r.json();
        if (!dead) setEvents(Array.isArray(j.events) ? j.events.slice().reverse() : []);
      } catch (_) {}
    };
    fetchOnce();
    if (!autoRefresh) return () => { dead = true; };
    const t = setInterval(fetchOnce, 3000);
    return () => { dead = true; clearInterval(t); };
  }, [ip, autoRefresh]);
  const corrGroups = useMemo(() => {
    const grouped = new Map<string, TraceEvent[]>();
    for (const e of events) {
      const c = e.corr || 'no_corr';
      if (!grouped.has(c)) grouped.set(c, []);
      grouped.get(c)!.push(e);
    }
    return [...grouped.entries()].slice(0, 6);
  }, [events]);
  const lensGlyph: Record<string, string> = { interaction: '⇄', intermediate: '◐', result: '✓' };
  const decisionSteps = Array.isArray(decisionTrace?.steps) ? decisionTrace!.steps! : [];
  const run = decisionTrace?.run || null;
  const runStatus = run?.effective_final_state || run?.final_state || run?.effective_status || run?.status || '';
  const countText = decisionTrace && decisionTrace.run_id
    ? `${decisionSteps.length} decisions`
    : `${events.length} events`;
  return (
    <div className="pipe-trace-strip" data-open={open ? 'yes' : 'no'}>
      <div className="pipe-trace-head">
        <button className="pipe-trace-toggle" onClick={() => setOpen(v => !v)} aria-expanded={open}>
          <span>ORCHESTRATOR TRACE</span>
          <span className="pipe-trace-count">{countText}{runStatus ? ` · ${runStatus}` : ''}</span>
          <span className="pipe-trace-chev">{open ? '▾' : '▸'}</span>
        </button>
        {open && (
          <label className="pipe-trace-auto">
            <input type="checkbox" checked={autoRefresh}
                   onChange={e => setAutoRefresh(e.currentTarget.checked)} />
            auto-refresh 3s
          </label>
        )}
      </div>
      {open && (
        <div className="pipe-trace-body">
          {decisionTrace && decisionTrace.run_id ? (
            <div className="pipe-trace-group">
              <div className="pipe-trace-corr">
                run #{String(decisionTrace.run_id).slice(-8)}
                {run?.model ? ` · ${run.model}` : ''}
              </div>
              {run?.terminal_anomaly && (
                <div className="pipe-trace-row" data-status="failed" data-lens="result">
                  <span className="pipe-trace-glyph">!</span>
                  <span className="pipe-trace-step">!</span>
                  <span className="pipe-trace-kind">terminal</span>
                  <span className="pipe-trace-actor">orchestrator</span>
                  <span className="pipe-trace-extra">{run.terminal_anomaly}</span>
                </div>
              )}
              {decisionSteps.map((s, i) => {
                const status = String(s.status || '');
                const glyph = status === 'failed' ? '!' : (status === 'waiting' ? '◐' : '✓');
                return (
                  <div key={`${decisionTrace.run_id}-${s.step ?? i}`} className="pipe-trace-row" data-status={status} data-lens={status === 'waiting' ? 'intermediate' : 'result'}>
                    <span className="pipe-trace-glyph">{glyph}</span>
                    <span className="pipe-trace-step">#{s.step ?? i}</span>
                    <span className="pipe-trace-kind">{s.tool || '?'}</span>
                    <span className="pipe-trace-actor">{s.time || ''}</span>
                    <span className="pipe-trace-extra">
                      {s.detail || s.verdict || ''}
                      {s.error ? ` · ${s.error}` : ''}
                      {!s.error && s.why ? ` · ${s.why}` : ''}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : events.length === 0 ? (
            <div className="pipe-trace-empty">No trace events yet for <b>{ip}</b>. Dispatch a worker to populate.</div>
          ) : corrGroups.map(([corr, group]) => (
            <div className="pipe-trace-group" key={corr}>
              <div className="pipe-trace-corr">{corr}</div>
              {group.map((e, i) => (
                <div key={`${corr}-${i}`} className="pipe-trace-row" data-lens={e.lens}>
                  <span className="pipe-trace-glyph">{lensGlyph[e.lens as string] || '·'}</span>
                  <span className="pipe-trace-step">#{e.step}</span>
                  <span className="pipe-trace-kind">{e.kind}</span>
                  <span className="pipe-trace-actor">{e.actor}{e.peer ? ` → ${e.peer}` : ''}</span>
                  <span className="pipe-trace-extra">
                    {e.status ? `${e.status} ` : ''}
                    {e.requested_workflow || e.run_id || e.detail || e.gate || e.reason || ''}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Phase 20 window exports — pipeline.jsx aliases these back via forward-ref lambdas.
win.WorkerOrchestraBar = WorkerOrchestraBar;
win.OrchestratorTraceStrip = OrchestratorTraceStrip;
