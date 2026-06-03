// app-helpers.tsx — TypeScript migration of the module-level helpers and
// standalone sub-components that lived at the top of app.jsx (strangler-fig).
//
// Extracted from app.jsx so the main app.tsx (which holds the irreducibly
// large `App` root component) stays as small as possible. These are the
// least-coupled seams: pure constants + normalizers + two self-contained
// status components (PipelineRunningChip, OrchInlineStatus) + ErrorBoundary.
//
// Load order: in the eventual Vite cutover this file is imported by app.tsx
// BEFORE App is defined, so the exports resolve at module-eval time. We also
// bridge the values app.tsx consumes onto window so ordering never bites.
//
// Behavior is identical to the original app.jsx: same constants, same
// normalizers, same component markup, same window reads/writes.
import { Component, useState, useEffect } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

// ── ErrorBoundary ─────────────────────────────────────────────────
// Without this, any throw inside Workspace / SocArchitect / a deep
// child component unmounts the *whole* app and shows a blank black
// page. The Atlas test agent caught one of these (a TDZ ReferenceError
// in soc-architect.jsx). Catching at the shell level keeps the user
// in business + surfaces the error inline so we get a screenshot we
// can act on instead of a silent blank.
interface ErrorBoundaryProps {
  label?: string;
  children?: ReactNode;
}
interface ErrorBoundaryState {
  error: unknown;
  info: ErrorInfo | null;
}
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(p: ErrorBoundaryProps) { super(p); this.state = { error: null, info: null }; }
  static getDerivedStateFromError(error: unknown) { return { error }; }
  componentDidCatch(error: unknown, info: ErrorInfo) { this.setState({ info }); console.error('[atlas] component crashed:', error, info); }
  reset = () => this.setState({ error: null, info: null });
  render() {
    if (!this.state.error) return this.props.children;
    const err = this.state.error as { message?: string } | null;
    return (
      <div style={{ padding: 24, fontFamily: 'var(--mono)', color: 'var(--fg)',
                    background: 'var(--bg)', height: '100%', overflow: 'auto' }}>
        <div style={{ color: 'var(--err)', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
          ✗ {this.props.label || 'Component'} crashed
        </div>
        <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginBottom: 12, lineHeight: 1.6 }}>
          The shell stays alive — pick a different screen, or hit Reset to try mounting again.
        </div>
        <pre style={{ background: 'var(--bg-2)', border: '1px solid var(--line)',
                      padding: 12, fontSize: 'var(--ui-control-font-size)', color: 'var(--err)',
                      maxHeight: 200, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
          {String(err && err.message || this.state.error)}
        </pre>
        {this.state.info && this.state.info.componentStack && (
          <pre style={{ background: 'var(--bg-2)', border: '1px solid var(--line)',
                        padding: 12, fontSize: 10.5, color: 'var(--fg-dim)',
                        maxHeight: 280, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
            {this.state.info.componentStack}
          </pre>
        )}
        <button onClick={this.reset}
                style={{ marginTop: 12, padding: '6px 14px',
                         background: 'var(--accent)', color: 'var(--bg)',
                         border: 0, fontFamily: 'var(--mono)', fontSize: 12,
                         cursor: 'pointer' }}>
          Reset
        </button>
      </div>
    );
  }
}

export interface AtlasUiResolutionPreset {
  key: string;
  label: string;
  width: number;
  height: number;
}
const viewportResolutionPreset = (): AtlasUiResolutionPreset => {
  const width = typeof window !== 'undefined' ? Math.max(1, Math.round(window.innerWidth || 0)) : 1920;
  const height = typeof window !== 'undefined' ? Math.max(1, Math.round(window.innerHeight || 0)) : 1080;
  return { key: 'auto', label: 'Auto', width, height };
};
export const ATLAS_UI_RESOLUTION_PRESETS: AtlasUiResolutionPreset[] = [
  { key: 'auto', label: 'Auto', width: 0, height: 0 },
  { key: '1366x768', label: '1366x768', width: 1366, height: 768 },
  { key: '1600x900', label: '1600x900', width: 1600, height: 900 },
  { key: '1920x1080', label: '1920x1080', width: 1920, height: 1080 },
  { key: '2560x1440', label: '2560x1440', width: 2560, height: 1440 },
  { key: '3840x2160', label: '3840x2160', width: 3840, height: 2160 },
];
export const DEFAULT_ATLAS_RESOLUTION = 'auto';
export const atlasResolutionPreset = (key: string): AtlasUiResolutionPreset => {
  if (key === 'auto' || !key) return viewportResolutionPreset();
  const preset = ATLAS_UI_RESOLUTION_PRESETS.find(p => p.key === key);
  if (preset && preset.key !== 'auto') return preset;
  return DEFAULT_ATLAS_RESOLUTION === 'auto'
    ? viewportResolutionPreset()
    : ATLAS_UI_RESOLUTION_PRESETS.find(p => p.key === DEFAULT_ATLAS_RESOLUTION) || viewportResolutionPreset();
};
export const ATLAS_RUN_MODE_OPTIONS = [
  { key: 'starter', label: 'Starter' },
  { key: 'engineering', label: 'Engineering' },
  { key: 'signoff', label: 'Signoff' },
];
export const ATLAS_EXEC_MODE_OPTIONS = [
  { key: 'single-worker', label: 'Single Worker' },
  { key: 'orchestrator', label: 'Orchestrator' },
];
export const DEFAULT_ATLAS_EXEC_MODE = 'single-worker';
export const ATLAS_EXEC_MODE_LOCKED = false;
export const ATLAS_FONT_MODE_OPTIONS = [
  { key: 'windows', label: 'Windows' },
  { key: 'sans', label: 'Sans' },
  { key: 'system', label: 'System' },
  { key: 'mono', label: 'Mono' },
];
export const normalizeAtlasFontMode = (value: unknown): string => {
  const v = String(value || '').trim().toLowerCase();
  return ATLAS_FONT_MODE_OPTIONS.some(o => o.key === v) ? v : '';
};
export const normalizeAtlasRunMode = (value: unknown): string => {
  const v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
  if (v === 'eng') return 'engineering';
  if (v === 'sign-off') return 'signoff';
  return ATLAS_RUN_MODE_OPTIONS.some(o => o.key === v) ? v : 'engineering';
};
export const normalizeAtlasExecMode = (value: unknown): string => {
  if (window.AtlasExecPolicy && window.AtlasExecPolicy.normalizeExecMode) {
    return window.AtlasExecPolicy.normalizeExecMode(value, DEFAULT_ATLAS_EXEC_MODE);
  }
  const v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
  if (v === 'single' || v === 'worker' || v === 'serial') return 'single-worker';
  if (v === 's' || v === 'sw' || v === 'main' || v === 'single worker') return 'single-worker';
  if (v === 'orch' || v === 'o' || v === 'multi-worker' || v === 'multi worker' || v === 'orchestrator-mode') return 'orchestrator';
  return ATLAS_EXEC_MODE_OPTIONS.some(o => o.key === v) ? v : DEFAULT_ATLAS_EXEC_MODE;
};
export const atlasBootConfig = (): Record<string, any> => {
  try { return window.ATLAS_BOOT_CONFIG || {}; }
  catch (_) { return {}; }
};
export const atlasPolicyConfig = (): Record<string, any> => {
  const cfg = atlasBootConfig();
  try {
    if (window.AtlasExecPolicy && window.AtlasExecPolicy.policyFromBootConfig) {
      return window.AtlasExecPolicy.policyFromBootConfig(cfg);
    }
  } catch (_) {}
  const mode = normalizeAtlasExecMode(cfg.exec_mode || window.ATLAS_EXEC_MODE || window.ATLAS_DEFAULT_EXEC_MODE);
  const policy = cfg.exec_policy || cfg.policy || {};
  return {
    exec_mode: mode,
    initial_workflow: policy.initial_workflow || (mode === 'orchestrator' ? 'orchestrator' : 'default'),
    preserve_running_on_workflow_switch:
      typeof policy.preserve_running_on_workflow_switch === 'boolean'
        ? policy.preserve_running_on_workflow_switch
        : mode === 'orchestrator',
  };
};
export const mergeAtlasPolicyResponse = (response: any): void => {
  try {
    window.ATLAS_BOOT_CONFIG = window.ATLAS_BOOT_CONFIG || {};
    if (window.AtlasExecPolicy && window.AtlasExecPolicy.mergePolicyResponse) {
      window.AtlasExecPolicy.mergePolicyResponse(window.ATLAS_BOOT_CONFIG, response || {});
    } else {
      if (response && response.exec_mode) window.ATLAS_BOOT_CONFIG.exec_mode = response.exec_mode;
      if (response && response.policy) window.ATLAS_BOOT_CONFIG.exec_policy = response.policy;
    }
    window.ATLAS_DEFAULT_EXEC_MODE = window.ATLAS_BOOT_CONFIG.exec_mode || window.ATLAS_DEFAULT_EXEC_MODE;
  } catch (_) {}
};
export const atlasNavigationIntent = (): { view: string; hasContext: boolean } => {
  try {
    const params = new URLSearchParams(window.location.search || '');
    const view = String(params.get('view') || '').trim().toLowerCase();
    const hasContext = !!(
      params.get('session') ||
      params.get('session_id') ||
      params.get('ip') ||
      params.get('ip_id') ||
      params.get('workflow') ||
      params.get('wf')
    );
    return { view, hasContext };
  } catch (_) {
    return { view: '', hasContext: false };
  }
};
export const atlasShouldHoldDashboardActivation = (): boolean => {
  const intent = atlasNavigationIntent();
  return intent.view === 'dashboard' && !intent.hasContext;
};

// ── PipelineRunningChip ───────────────────────────────────────────
// Top-bar "[▶ N running]" chip. Reads window.ATLAS_PIPELINE_RUNNING
// (set by AtlasPipeline's poll loop) and listens to the corresponding
// custom event so the chip stays accurate even when the user is on
// the Workspace screen. Visible only when count > 0.
export interface PipelineRunningChipProps {
  onClick: () => void;
}
export const PipelineRunningChip = ({ onClick }: PipelineRunningChipProps) => {
  const [count, setCount] = useState(
    typeof window.ATLAS_PIPELINE_RUNNING === 'number' ? window.ATLAS_PIPELINE_RUNNING : 0
  );
  useEffect(() => {
    const onChange = (ev: any) => {
      setCount((ev && ev.detail && typeof ev.detail.count === 'number') ? ev.detail.count : 0);
    };
    window.addEventListener('atlas:pipeline-running-changed', onChange);
    return () => window.removeEventListener('atlas:pipeline-running-changed', onChange);
  }, []);
  if (!count) return null;
  return (
    <button className="dir-btn pipe-running-chip"
            title={`${count} pipeline stage(s) running — click to open Pipeline`}
            onClick={onClick}>
      ▶ {count} running
    </button>
  );
};

export interface OrchInlineStatusProps {
  activeIp: string;
}
export const OrchInlineStatus = ({ activeIp }: OrchInlineStatusProps) => {
  const [status, setStatus] = useState<any>(null);

  const execMode = normalizeAtlasExecMode(
    (atlasBootConfig().exec_policy && atlasBootConfig().exec_policy.exec_mode)
    || (atlasBootConfig().policy && atlasBootConfig().policy.exec_mode)
    || atlasBootConfig().exec_mode
    || window.ATLAS_EXEC_MODE
    || window.ATLAS_DEFAULT_EXEC_MODE
    || 'single'
  );
  const isOrch = execMode === 'orchestrator';

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      if (!isOrch || !activeIp || activeIp === 'default') { setStatus(null); return; }
      try {
        const [runRes, traceRes] = await Promise.all([
          fetch(`/api/orchestrator/active_run?ip=${encodeURIComponent(activeIp)}`),
          fetch(`/api/orchestrator/trace?ip=${encodeURIComponent(activeIp)}&limit=1`),
        ]);
        if (cancelled) return;
        const runData = runRes.ok ? await runRes.json() : null;
        const traceData = traceRes.ok ? await traceRes.json() : null;
        if (cancelled) return;
        const lastEvent = traceData && Array.isArray(traceData.events) && traceData.events.length
          ? traceData.events[0] : null;
        setStatus({ run: runData, lastEvent });
      } catch (_) {
        if (!cancelled) setStatus(null);
      }
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, [activeIp, isOrch]);
  const workerCount = status && status.run && typeof status.run.running_count === 'number'
    ? status.run.running_count : 0;
  const lastKind = status && status.lastEvent
    ? (status.lastEvent.kind || status.lastEvent.type || '') : '';

  return (
    <span className="orch-inline">
      <span className="osk">orch:</span>
      <span className={`osv ${isOrch ? 'on' : 'off'}`}>{isOrch ? 'on' : 'off'}</span>
      <span className="os-sep"> │ </span>
      <span className="osk">workers:</span>
      <span className="osv">{workerCount}</span>
      {lastKind ? (
        <>
          <span className="os-sep"> │ </span>
          <span className="osk">last:</span>
          <span className="osv">{lastKind}</span>
        </>
      ) : null}
    </span>
  );
};
