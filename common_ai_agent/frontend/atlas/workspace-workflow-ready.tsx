/* workspace-workflow-ready.tsx — slice of the ATLAS workspace migration.
 *
 * Owns the workflow-ready handshake constants + the WorkflowReadyOverlay
 * progress UI, plus the SessionSwitcher dropdown (fetches `/api/sessions`,
 * confirm-on-switch when streaming). Sits between routing and the
 * async-resource helpers in the original workspace.jsx.
 *
 * These .tsx files are INERT mirrors — the legacy workspace.jsx still
 * serves the live app. Behavior here is identical to the legacy source.
 */
import { useState, useEffect, useRef, useCallback } from 'react';

export const WORKFLOW_READY_TIMEOUT_MS = 7000;
export const WORKFLOW_READY_PHASES = ['route', 'session', 'backend', 'worker', 'ready'];
export const WORKFLOW_READY_STEPS = [
  { key: 'route', label: 'Route' },
  { key: 'session', label: 'Session' },
  { key: 'backend', label: 'Backend' },
  { key: 'worker', label: 'Worker' },
  { key: 'ready', label: 'Ready' },
];

export const workflowReadyPhaseIndex = (phase: unknown): number => {
  const idx = WORKFLOW_READY_PHASES.indexOf(String(phase || ''));
  return idx >= 0 ? idx : 0;
};

export const WorkflowReadyOverlay = ({ state }: { state?: any }) => {
  if (!state) return null;
  const phase = String(state.phase || 'route');
  const activeIdx = workflowReadyPhaseIndex(phase);
  const failed = phase === 'error';
  return (
    <div className="workflow-ready-overlay" role="status" aria-live="polite">
      <div className="workflow-ready-card" data-state={failed ? 'error' : phase}>
        <div className="workflow-ready-header">
          <span className="workflow-ready-spinner" aria-hidden="true" />
          <div>
            <div className="workflow-ready-title">
              {failed ? 'Workflow switch failed' : 'Preparing workflow'}
            </div>
            <div className="workflow-ready-target">
              <code>{state.target || 'default'}</code>
              {state.ip ? <span> / ip=<code>{state.ip}</code></span> : null}
            </div>
          </div>
        </div>
        <div className="workflow-ready-message">
          {state.message || (failed ? 'Activation error' : 'Waiting for worker readiness')}
        </div>
        <div className="workflow-ready-steps">
          {WORKFLOW_READY_STEPS.map((step, idx) => {
            const stepState = failed && idx >= activeIdx
              ? 'error'
              : (idx < activeIdx ? 'done' : (idx === activeIdx ? 'active' : 'pending'));
            return (
              <span key={step.key} className="workflow-ready-step" data-state={stepState}>
                <span className="workflow-ready-dot" />
                <span>{step.label}</span>
              </span>
            );
          })}
        </div>
        {state.session ? (
          <div className="workflow-ready-session">{state.session}</div>
        ) : null}
      </div>
    </div>
  );
};

export const SessionSwitcher = ({
  currentSession,
  streaming,
  onSwitch,
}: {
  currentSession?: string;
  streaming?: boolean;
  onSwitch: (id: string) => void;
}) => {
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  const fetchOptions = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/sessions');
      const d = await r.json();
      setOptions(Array.isArray(d.sessions) ? d.sessions : []);
    } catch (_) {
      setOptions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    fetchOptions();
    const onDocClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [open, fetchOptions]);

  const currentLabel = (currentSession || '').split('/')[0] || 'default';

  const handleSelect = (id: string) => {
    setOpen(false);
    if (id === currentLabel) return;
    if (streaming) {
      setConfirmId(id);
      return;
    }
    onSwitch(id);
  };

  return (
    <>
      <div ref={wrapRef} style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          title="Switch session"
          style={{
            background: 'transparent',
            border: '1px solid var(--line)',
            color: 'var(--fg-mute)',
            fontSize: 'var(--ui-control-font-size)',
            fontFamily: 'var(--mono)',
            padding: '2px 8px',
            borderRadius: 2,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <span style={{ color: 'var(--accent)' }}>◈</span>
          <span className="trunc" style={{ maxWidth: 140 }}>{currentLabel}</span>
          <span style={{ fontSize: 9 }}>{open ? '▲' : '▼'}</span>
        </button>
        {open && (
          <div style={{
            position: 'absolute', top: 'calc(100% + 4px)', left: 0, zIndex: 50,
            minWidth: 220, maxWidth: 300, maxHeight: 260, overflow: 'auto',
            background: 'var(--panel)', border: '1px solid var(--line)',
            borderRadius: 2, boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
          }}>
            <div style={{ padding: '6px 10px', borderBottom: '1px solid var(--line)', fontSize: 10, color: 'var(--fg-dim)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Switch session
            </div>
            {loading && (
              <div style={{ padding: '8px 10px', fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)' }}>Loading…</div>
            )}
            {!loading && options.length === 0 && (
              <div style={{ padding: '8px 10px', fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)' }}>No sessions</div>
            )}
            {options.map((s: any) => (
              <div
                key={s.id}
                onClick={() => handleSelect(s.id)}
                style={{
                  padding: '6px 10px', fontSize: 'var(--ui-control-font-size)', cursor: 'pointer',
                  color: s.id === currentLabel ? 'var(--accent)' : 'var(--fg)',
                  background: s.id === currentLabel ? 'color-mix(in oklch, var(--accent) 10%, transparent)' : 'transparent',
                  borderBottom: '1px solid var(--line-2)',
                }}
                onMouseEnter={(e) => { if (s.id !== currentLabel) e.currentTarget.style.background = 'var(--bg-2)'; }}
                onMouseLeave={(e) => { if (s.id !== currentLabel) e.currentTarget.style.background = 'transparent'; }}
              >
                <div style={{ fontWeight: 500 }}>{s.title || s.id}</div>
                <div style={{ fontSize: 10, color: 'var(--fg-mute)', marginTop: 2 }}>{s.project_id || s.id}</div>
              </div>
            ))}
          </div>
        )}
      </div>
      {confirmId && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 100,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
        onClick={(e) => { if (e.target === e.currentTarget) setConfirmId(null); }}
        >
          <div style={{
            background: 'var(--panel)', border: '1px solid var(--line)',
            borderRadius: 4, padding: '20px 24px', maxWidth: 360, width: 'min(90vw, 360px)',
          }}>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: 'var(--fg)' }}>
              Agent is running
            </div>
            <div style={{ fontSize: 12, color: 'var(--fg-mute)', marginBottom: 16, lineHeight: 1.5 }}>
              Switching sessions will interrupt the current agent. Switch anyway?
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn" type="button" onClick={() => setConfirmId(null)} style={{ fontSize: 11 }}>
                Cancel
              </button>
              <button
                className="btn" type="button"
                onClick={() => { const id = confirmId; setConfirmId(null); onSwitch(id); }}
                style={{ fontSize: 'var(--ui-control-font-size)', background: 'var(--warn)', color: 'var(--bg)', borderColor: 'var(--warn)' }}
              >
                Switch
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
