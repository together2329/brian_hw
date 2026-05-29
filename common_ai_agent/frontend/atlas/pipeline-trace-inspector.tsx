// pipeline-trace-inspector.tsx — FlowInspector + PipelineFlowControl extracted
// from pipeline-trace.tsx (Phase: sub-1000 split). Both are flow-selection
// panels: FlowInspector is the right-side inspector (flows + numbered steps +
// focused stage detail), PipelineFlowControl is the top-center flow selector.
// Both dispatch flows via POST /api/pipeline/dispatch and own their window
// bridges; they remain real named exports for migrated consumers too.
import { useState } from 'react';
import {
  type PipelineState,
  type PipelineFlowDef,
  type FlowInspectorProps,
  type PipelineFlowControlProps,
} from './pipeline-trace-shared';
import { win, StageCard } from './pipeline-trace-shared';

// ─── FlowInspector ────────────────────────────────────────────────
//
// Right-side panel inspired by the reference screenshots: selectable flows on
// top, numbered steps below, and a focused stage detail/action area.
export function FlowInspector({
  ip,
  state,
  selectedFlowId,
  onSelectFlow,
  selectedStage,
  onSelectStage,
  onChain,
}: FlowInspectorProps) {
  const [busyFlow, setBusyFlow] = useState('');
  const flows = win.PIPELINE_FLOW_DEFS || [];
  const labels = win.PIPELINE_LABEL || {};
  const actualSet = new Set(win.PIPELINE_STAGES || []);
  const stagesState = (state && state.stages) || {};
  const flow = flows.find(f => f.id === selectedFlowId) || flows[0] || { stages: [] } as unknown as PipelineFlowDef;
  const selectedInfo = actualSet.has(selectedStage as string) ? stagesState[selectedStage as string] : null;

  const dispatchFlow = async () => {
    const stages = win.pipelineActualStages!(flow.stages || []);
    if (!ip || !stages.length || busyFlow) return;
    setBusyFlow(flow.id);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, stages, schedule: 'auto', prompt: '', ...win.pipelinePolicyPayload!() }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        console.error('[pipeline] flow dispatch failed', j.error || r.status);
      } else {
        try {
          window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', {
            detail: { stage: flow.id, ip, jobs: j.jobs || [] },
          }));
        } catch (_) {}
      }
    } catch (e) {
      console.error('[pipeline] flow dispatch error', e);
    } finally {
      setBusyFlow('');
    }
  };

  const flowCounts = (stages?: string[]) => {
    const real = win.pipelineActualStages!(stages || []);
    const counts = { running: 0, passed: 0, failed: 0, blocked: 0, locked: 0 };
    real.forEach(s => {
      const st = (stagesState[s] && stagesState[s].state) || 'idle';
      if (st === 'running' || st === 'run') counts.running += 1;
      if (st === 'passed' || st === 'ok') counts.passed += 1;
      if (st === 'failed' || st === 'err') counts.failed += 1;
      if (st === 'blocked' || st === 'stale') counts.blocked += 1;
      if (st === 'locked') counts.locked += 1;
    });
    return counts;
  };

  const stepLabel = (id: string) => {
    if ((win.PIPELINE_VIRTUAL_NODES || {})[id]) return win.PIPELINE_VIRTUAL_NODES![id].label;
    return labels[id] || id;
  };
  const stepState = (id: string) => {
    if ((win.PIPELINE_VIRTUAL_NODES || {})[id]) return 'handoff';
    return (stagesState[id] && stagesState[id].state) || 'idle';
  };
  const stepDetail = (id: string) => {
    const virtual = (win.PIPELINE_VIRTUAL_NODES || {})[id];
    if (virtual) return virtual.sub;
    const data = stagesState[id] || {};
    return data.top || data.secondary || data.locked_reason || 'no evidence yet';
  };

  return (
    <div className="pipe-flow-inspector">
      <section className="pipe-inspector-section">
        <div className="pipe-inspector-title">Flows</div>
        <div className="pipe-flow-list">
          {flows.map(f => {
            const counts = flowCounts(f.stages);
            return (
              <button key={f.id}
                      className={`pipe-flow-choice ${f.id === flow.id ? 'sel' : ''}`}
                      onClick={() => {
                        if (typeof onSelectFlow === 'function') onSelectFlow(f.id);
                        const firstActual = win.pipelineActualStages!(f.stages || [])[0];
                        if (firstActual && typeof onSelectStage === 'function') onSelectStage(firstActual);
                      }}>
                <span className="pipe-flow-choice-name">{f.name}</span>
                <span className="pipe-flow-choice-summary">{f.summary}</span>
                <span className="pipe-flow-choice-meta">
                  {counts.running ? `running ${counts.running} · ` : ''}
                  {counts.failed ? `failed ${counts.failed} · ` : ''}
                  {counts.blocked ? `blocked ${counts.blocked} · ` : ''}
                  passed {counts.passed}/{win.pipelineActualStages!(f.stages || []).length}
                </span>
              </button>
            );
          })}
        </div>
        <button className="rb-btn primary pipe-flow-run"
                disabled={!ip || !!busyFlow || !win.pipelineActualStages!(flow.stages || []).length}
                onClick={dispatchFlow}>
          {busyFlow ? 'dispatching…' : `Run ${flow.name}`}
        </button>
      </section>

      <section className="pipe-inspector-section pipe-steps-section">
        <div className="pipe-inspector-title">Steps</div>
        <div className="pipe-step-list">
          {(flow.stages || []).map((id, idx) => {
            const stateName = stepState(id);
            return (
              <button key={`${id}-${idx}`}
                      className={`pipe-step-card ${selectedStage === id ? 'sel' : ''}`}
                      data-state={stateName}
                      onClick={() => typeof onSelectStage === 'function' && onSelectStage(id)}>
                <span className="pipe-step-index">{idx + 1}</span>
                <span className="pipe-step-body">
                  <span className="pipe-step-name">{stepLabel(id)}</span>
                  <span className="pipe-step-detail">{stepDetail(id)}</span>
                </span>
                <span className="pipe-step-state">{stateName}</span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="pipe-inspector-section">
        <div className="pipe-inspector-title">Selected</div>
        {selectedInfo ? (
          // StageCard is owned by pipeline-flow-stage.jsx; resolved off window
          // at render time exactly as the original `<window.StageCard ...>`.
          <StageCard
            stageId={selectedStage as string}
            info={selectedInfo}
            ip={ip}
            onChain={onChain} />
        ) : (
          <div className="pipe-virtual-detail">
            <b>{stepLabel(selectedStage || 'orchestrator')}</b>
            <span>{stepDetail(selectedStage || 'orchestrator')}</span>
            <span className="mute">This is an orchestrator control-plane step, not a workflow artifact owner.</span>
          </div>
        )}
      </section>
    </div>
  );
}

// ─── PipelineFlowControl ──────────────────────────────────────────
//
// Top-center flow selector. The user asked for flow/step controls not to sit
// under the graph; keep them in the center header so the map remains primary.
export function PipelineFlowControl({
  ip,
  state,
  selectedFlowId,
  onSelectFlow,
  selectedStage,
  onSelectStage,
}: PipelineFlowControlProps) {
  const [busyFlow, setBusyFlow] = useState('');
  const flows = win.PIPELINE_FLOW_DEFS || [];
  const labels = win.PIPELINE_LABEL || {};
  const stagesState = (state && state.stages) || {};
  const flow = flows.find(f => f.id === selectedFlowId) || flows[0] || { stages: [] } as unknown as PipelineFlowDef;

  const flowCounts = (stages?: string[]) => {
    const real = win.pipelineActualStages!(stages || []);
    const counts: { running: number; passed: number; failed: number; blocked: number; total?: number } = { running: 0, passed: 0, failed: 0, blocked: 0 };
    real.forEach(s => {
      const st = (stagesState[s] && stagesState[s].state) || 'idle';
      if (st === 'running' || st === 'run') counts.running += 1;
      if (st === 'passed' || st === 'ok') counts.passed += 1;
      if (st === 'failed' || st === 'err') counts.failed += 1;
      if (st === 'blocked' || st === 'stale' || st === 'locked') counts.blocked += 1;
    });
    counts.total = real.length;
    return counts;
  };

  const stepLabel = (id: string) => {
    if ((win.PIPELINE_VIRTUAL_NODES || {})[id]) return win.PIPELINE_VIRTUAL_NODES![id].label;
    return labels[id] || id;
  };
  const stepState = (id: string) => {
    if ((win.PIPELINE_VIRTUAL_NODES || {})[id]) return 'handoff';
    return (stagesState[id] && stagesState[id].state) || 'idle';
  };

  const dispatchFlow = async () => {
    const stages = win.pipelineActualStages!(flow.stages || []);
    if (!ip || !stages.length || busyFlow) return;
    setBusyFlow(flow.id);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, stages, schedule: 'auto', prompt: '', ...win.pipelinePolicyPayload!() }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        console.error('[pipeline] flow dispatch failed', j.error || r.status);
      } else {
        try {
          window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', {
            detail: { stage: flow.id, ip, jobs: j.jobs || [] },
          }));
        } catch (_) {}
      }
    } catch (e) {
      console.error('[pipeline] flow dispatch error', e);
    } finally {
      setBusyFlow('');
    }
  };

  return (
    <div className="pipe-flow-control">
      <div className="pipe-flow-control-top">
        <div>
          <div className="pipe-flow-control-title">Pipeline Flows</div>
          <div className="pipe-flow-control-summary">{flow.summary || ''}</div>
        </div>
        <button className="rb-btn primary pipe-flow-run-inline"
                disabled={!ip || !!busyFlow || !win.pipelineActualStages!(flow.stages || []).length}
                onClick={dispatchFlow}>
          {busyFlow ? 'dispatching...' : `Run ${flow.name || 'flow'}`}
        </button>
      </div>
      <div className="pipe-flow-chip-row">
        {flows.map(f => {
          const counts = flowCounts(f.stages);
          return (
            <button key={f.id}
                    className={`pipe-flow-tab ${f.id === flow.id ? 'sel' : ''}`}
                    onClick={() => {
                      if (typeof onSelectFlow === 'function') onSelectFlow(f.id);
                      const firstActual = win.pipelineActualStages!(f.stages || [])[0];
                      if (firstActual && typeof onSelectStage === 'function') onSelectStage(firstActual);
                    }}>
              <span>{f.name}</span>
              <b>{counts.passed}/{counts.total}</b>
            </button>
          );
        })}
      </div>
      <div className="pipe-flow-step-row">
        {(flow.stages || []).map((id, idx) => (
          <button key={`${id}-${idx}`}
                  className={`pipe-flow-step-pill ${selectedStage === id ? 'sel' : ''}`}
                  data-state={stepState(id)}
                  onClick={() => typeof onSelectStage === 'function' && onSelectStage(id)}>
            <span>{idx + 1}</span>
            {stepLabel(id)}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Transitional bridges for the module-scope window globals ──
// (FlowInspector / PipelineFlowControl were `window.X = function...` definitions
// in the .jsx; keep them resolvable for not-yet-migrated .jsx consumers while
// exposing real exports above.)
win.FlowInspector = FlowInspector;
win.PipelineFlowControl = PipelineFlowControl;
