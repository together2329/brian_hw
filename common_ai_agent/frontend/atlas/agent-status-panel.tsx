// agent-status-panel.tsx — TypeScript migration of agent-status-panel.jsx
// (Phase 19 refactor: AgentStatusPanel, 614L) — extracted from
// workspace-panels.jsx so the latter drops under the 2000-line target.
//
// TS migration: converted from ambient global React + IIFE + lambda forward-ref
// pattern to a typed ES module. Still bridges `window.AgentStatusPanel` at the
// bottom for not-yet-migrated .jsx consumers (workspace.jsx mounts it).
// Cross-file globals (window.workspaceFetchWorkerSnapshot, window.CONTEXT,
// window.SCOPE_PATH, window.ACTIVE_SESSION, window.FLOW_STAGES,
// window.AtlasWorkersLogic, window.openPipelineWorkflowWorkspace, and the
// workspace.jsx health helpers) are read through a narrow cast since their
// owners are still .jsx and they are not yet declared in
// types/atlas-window.d.ts.
import {
  useState,
  useEffect,
  type ChangeEvent,
  type MouseEvent,
} from 'react';
import {
  AgentWorkerStatus,
  type AtlasWorkersLogicApi,
  type InteractiveWorkerState,
  type InteractiveWorkerStatus,
  type WorkerSnapshot,
} from './agent-worker-status';

// ── Data shapes flowing through this panel. Loose where the .jsx was loose. ──
interface ModelOption {
  key?: string;
  model?: string;
  label?: string;
}

interface PricingInfo {
  // Typed as required numbers so the cost-ledger arithmetic below matches the
  // original .jsx exactly (which read `_ctx.pricing.input` with no fallback —
  // an undefined value there yields NaN, preserved here on purpose).
  input: number;
  cache: number;
  output: number;
}

interface LiveContext {
  modelOptions?: ModelOption[];
  selectedModelKey?: string;
  model?: string;
  baseModel?: string;
  baseUrl?: string;
  provider?: string;
  reasoningEffort?: string;
  maxTokens?: number;
  tokens?: number;
  tokensIn?: number;
  tokensCache?: number;
  tokensOut?: number;
  costUsd?: number;
  costScope?: string;
  costUser?: string;
  costIp?: string;
  costCalls?: number;
  pricing?: PricingInfo | null;
  activeSession?: string;
  [key: string]: unknown;
}

interface HealthzResponse {
  model?: string;
  base_model?: string;
  base_url?: string;
  provider?: string;
  reasoning_effort?: string;
  model_options?: ModelOption[];
  selected_model_key?: string;
  max_context?: number;
  tokens?: number;
  tokens_in?: number;
  tokens_cache?: number;
  tokens_out?: number;
  cost_usd?: number;
  cost_scope?: string;
  cost_user?: string;
  cost_ip?: string;
  cost_calls?: number | null;
  pricing?: PricingInfo | null;
  [key: string]: unknown;
}

interface SessionRoute {
  owner?: string;
  ip?: string;
}

interface FlowStage {
  id?: string;
  label?: string;
}

interface SocModule {
  id?: string;
  ip_dir?: string;
  status?: string;
}

// ── Cross-file window globals owned by unmigrated .jsx, reached via a narrow
// typed view of `window` (not yet in types/atlas-window.d.ts). ──
const w = window as unknown as {
  workspaceFetchWorkerSnapshot: (opts: { ip?: string; activeOnly?: boolean }) => Promise<{ workers?: WorkerSnapshot[] } | null | undefined>;
  healthMatchesCurrentUser: (j: HealthzResponse) => boolean;
  uiEffectiveHealthSession: (j: HealthzResponse) => string;
  uiHealthCountersMatchBrowserRoute: (j: HealthzResponse) => boolean;
  uiSessionRoute: (session: string) => SessionRoute;
  atlasUiExecMode: () => string;
  atlasStatusMeta: (...a: unknown[]) => unknown;
  AtlasStatusBadge: (...a: unknown[]) => unknown;
  normalizeUiSession: (session: string) => string;
  CONTEXT?: LiveContext;
  ACTIVE_SESSION?: string;
  SCOPE_PATH?: string;
  FLOW_STAGES?: FlowStage[];
  AtlasWorkersLogic?: AtlasWorkersLogicApi;
  openPipelineWorkflowWorkspace?: (opts: { ip?: string; workflow?: string }) => void;
};

// Forward-ref to workspace.jsx helpers (resolved at call time):
const workspaceFetchWorkerSnapshot = (opts: { ip?: string; activeOnly?: boolean }) => w.workspaceFetchWorkerSnapshot(opts);
const healthMatchesCurrentUser = (j: HealthzResponse) => w.healthMatchesCurrentUser(j);
const uiEffectiveHealthSession = (j: HealthzResponse) => w.uiEffectiveHealthSession(j);
const uiHealthCountersMatchBrowserRoute = (j: HealthzResponse) => w.uiHealthCountersMatchBrowserRoute(j);
const uiSessionRoute = (session: string) => w.uiSessionRoute(session);
const atlasUiExecMode = () => w.atlasUiExecMode();
const atlasStatusMeta = (...a: unknown[]) => w.atlasStatusMeta(...a);
const AtlasStatusBadge = (...a: unknown[]) => w.AtlasStatusBadge(...a);
const normalizeUiSession = (session: string) => w.normalizeUiSession(session);


interface AgentStatusPanelProps {
  intent?: string;
  workflow?: string;
  activeIp?: string;
  agentAlive?: boolean;
  agentRunning?: boolean;
  onCollapse?: () => void;
}

const AgentStatusPanel = ({ intent, workflow, activeIp = '', agentAlive = false, agentRunning = false, onCollapse }: AgentStatusPanelProps) => {
  // Live context — populated by /healthz + WS 'context' events.
  const [liveContext, setLiveContext] = useState<LiveContext>(() => Object.assign({}, w.CONTEXT || {}));
  const _ctx = liveContext;
  const [liveStageStatus, setLiveStageStatus] = useState<string | null>(null);
  const [liveWorkers, setLiveWorkers] = useState<WorkerSnapshot[]>([]);
  const [workersError, setWorkersError] = useState('');
  const [interactiveWorker, setInteractiveWorker] = useState<InteractiveWorkerStatus | null>(null);
  const [interactiveWorkerError, setInteractiveWorkerError] = useState('');
  const effortOptions = ['none', 'low', 'medium', 'high', 'xhigh'];
  const normalizeEffortValue = (value: unknown): string => (
    effortOptions.includes(String(value || '').toLowerCase())
      ? String(value || '').toLowerCase()
      : 'medium'
  );
  const modelOptions = Array.isArray(_ctx.modelOptions) ? _ctx.modelOptions : [];
  const modelKey =
    _ctx.selectedModelKey
    || ((modelOptions.find(m => m.model === _ctx.model) || modelOptions[0] || {}).key || '');
  const [effortValue, setEffortValue] = useState(normalizeEffortValue(_ctx.reasoningEffort));
  const [savingEffort, setSavingEffort] = useState(false);
  const [savingModel, setSavingModel] = useState(false);
  const [settingsError, setSettingsError] = useState('');
  const numericValue = (value: unknown, fallback = 0): number => {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  };
  const sessionPartsFor = (session: string): string[] => normalizeUiSession(session).split('/').filter(Boolean);
  const shouldPreserveBrowserCounters = (incomingSession: string): boolean => {
    const incoming = sessionPartsFor(incomingSession);
    const browserSession = normalizeUiSession(w.ACTIVE_SESSION || '');
    const browser = sessionPartsFor(browserSession);
    const incomingOwner = incoming[0] || '';
    const browserOwner = browser[0] || '';
    const incomingIp = incoming.length >= 3 ? incoming[incoming.length - 2] : '';
    const incomingWf = incoming[incoming.length - 1] || '';
    const browserIp = browser.length >= 3 ? browser[browser.length - 2] : '';
    const incomingIsDefault = !!incomingOwner
      && (!incomingIp || incomingIp === 'default')
      && (!incomingWf || incomingWf === 'default');
    const browserHasIp = !!browserOwner && !!browserIp && browserIp !== 'default' && browserIp !== 'soc';
    return incomingIsDefault && browserHasIp && (!incomingOwner || !browserOwner || incomingOwner === browserOwner);
  };
  const mergeStableContext = (prev: LiveContext | null, extra?: Partial<LiveContext>): LiveContext => {
    const prevCtx = prev || {};
    const clean: Record<string, unknown> = {};
    Object.entries(extra || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null) clean[key] = value;
    });
    const globalCtx = w.CONTEXT || {};
    const merged: LiveContext = Object.assign({}, prevCtx, globalCtx, clean);
    const prevSession = normalizeUiSession(String(prevCtx.activeSession || ''));
    const incomingSession = normalizeUiSession(String(clean.activeSession || globalCtx.activeSession || merged.activeSession || ''));
    const browserSession = normalizeUiSession(w.ACTIVE_SESSION || '');
    const preserveBrowser = shouldPreserveBrowserCounters(incomingSession);
    const effectiveSession = preserveBrowser
      ? (browserSession || prevSession || incomingSession)
      : (incomingSession || browserSession || prevSession);
    // Tail match (ip/workflow) so an owner-prefix difference between the
    // orchestrator run session (e.g. `admin/new_axi/orchestrator`) and the
    // workspace session does NOT flip sameSession to false. When it flips,
    // the monotonic Math.max clamp below is skipped and the token/cost
    // counters jump up and down between two sources — the visible
    // "흔들림" the user reported during an active orchestrator run.
    const _sessTail = (s: string) => String(s || '').split('/').filter(Boolean).slice(-2).join('/');
    const sameSession = !prevSession || !effectiveSession
      || prevSession === effectiveSession
      || (_sessTail(prevSession) && _sessTail(prevSession) === _sessTail(effectiveSession));
	    if (effectiveSession) merged.activeSession = effectiveSession;

	    // 'tokens' = the LIVE context size; it legitimately DROPS after history
	    // compression, so it must NOT be monotonically clamped (Math.max froze the
	    // Context meter post-compression). Only the genuinely-cumulative usage/cost
	    // counters below are clamped against per-tick jitter.
    const counters = ['tokensIn', 'tokensCache', 'tokensOut', 'costUsd'];
	    const incomingCostIp = String(clean.costIp || globalCtx.costIp || '').trim();
	    const prevCostIp = String(prevCtx.costIp || '').trim();
	    const costIpChanged = !!(incomingCostIp && prevCostIp && incomingCostIp !== prevCostIp);
	    if (preserveBrowser && prevSession) {
	      counters.forEach(key => {
	        if (prevCtx[key] !== undefined && prevCtx[key] !== null) merged[key] = numericValue(prevCtx[key], 0);
	      });
	    } else if (costIpChanged) {
	      counters.forEach(key => {
	        merged[key] = numericValue(clean[key], 0);
	      });
	    } else if (sameSession) {
	      counters.forEach(key => {
	        const next = numericValue(merged[key], NaN);
        const prevVal = numericValue(prevCtx[key], 0);
        merged[key] = Number.isFinite(next) ? Math.max(prevVal, next) : prevVal;
      });
    }
    return merged;
  };
  useEffect(() => {
    let alive = true;
    const syncContext = (extra?: Partial<LiveContext>) => {
      if (!alive) return;
      setLiveContext(prev => mergeStableContext(prev, extra));
    };
    const poll = () => {
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
      fetch('/healthz', { cache: 'no-store' })
        .then(r => r.ok ? r.json() : null)
	        .then((j: HealthzResponse | null) => {
	          if (!j || !healthMatchesCurrentUser(j)) return;
	          const effectiveSession = uiEffectiveHealthSession(j);
	          const acceptCounters = uiHealthCountersMatchBrowserRoute(j);
	          const effectiveRoute = uiSessionRoute(effectiveSession);
	          const counterPatch = acceptCounters ? {
	            tokens: j.tokens,
	            tokensIn: j.tokens_in,
	            tokensCache: j.tokens_cache,
	            tokensOut: j.tokens_out,
	            costUsd: j.cost_usd,
	            costScope: j.cost_scope || '',
	            costUser: j.cost_user || '',
	            costIp: j.cost_ip || '',
	            costCalls: j.cost_calls != null ? Number(j.cost_calls || 0) : 0,
	          } : {
	            tokens: 0,
	            tokensIn: 0,
	            tokensCache: 0,
	            tokensOut: 0,
	            costUsd: 0,
	            costScope: effectiveRoute.ip ? 'user_ip' : '',
	            costUser: effectiveRoute.owner || '',
	            costIp: effectiveRoute.ip || '',
	            costCalls: 0,
	          };
	          syncContext({
	            model: j.model || j.base_model || '',
	            baseModel: j.base_model || '',
	            baseUrl: j.base_url || '',
	            provider: j.provider || '',
	            reasoningEffort: j.reasoning_effort || '',
	            modelOptions: Array.isArray(j.model_options) ? j.model_options : [],
	            selectedModelKey: j.selected_model_key || '',
	            maxTokens: j.max_context,
	            ...counterPatch,
	            pricing: j.pricing || null,
	            activeSession: effectiveSession || '',
	          });
	        })
        .catch(() => {});
    };
    const onDataChanged = () => syncContext();
    syncContext();
    poll();
    const timer = setInterval(poll, 30000);
    window.addEventListener('atlas-data-changed', onDataChanged);
    window.addEventListener('atlas-session-loaded', onDataChanged);
    return () => {
      alive = false;
      clearInterval(timer);
      window.removeEventListener('atlas-data-changed', onDataChanged);
      window.removeEventListener('atlas-session-loaded', onDataChanged);
    };
  }, []);
  useEffect(() => {
    setEffortValue(normalizeEffortValue(_ctx.reasoningEffort));
  }, [_ctx.reasoningEffort]);
  // Live orchestrator worker list. Server caches /api/orchestrator/workers
  // per URL for 1.5s, so this 3s poll is one HTTP round-trip per tab, not
  // per worker. Pauses while the tab is hidden.
  useEffect(() => {
    let dead = false;
    const workerIp = (() => {
      const direct = String(activeIp || '').trim();
      if (direct && direct !== 'default') return direct;
      const scoped = String(w.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
      const leaf = scoped.split('/').filter(Boolean).pop() || '';
      return leaf && leaf !== 'default' ? leaf : '';
    })();
    const poll = async () => {
      if (dead) return;
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
      try {
        const j = await workspaceFetchWorkerSnapshot({ ip: workerIp, activeOnly: true });
        const list = Array.isArray(j && j.workers) ? j!.workers! : [];
        if (!dead) {
          setLiveWorkers(list);
          setWorkersError('');
        }
      } catch (e) {
        if (!dead) setWorkersError(String((e && (e as Error).message) || e));
      }
    };
    poll();
    const id = setInterval(poll, 3000);
    return () => { dead = true; clearInterval(id); };
  }, [activeIp]);
  // Interactive session worker ('agent') status — DISTINCT from the
  // orchestrator worker list above. Same 3s cadence, paused while hidden,
  // with its own error channel so an agent-status fetch failure never blanks
  // the orchestrator worker cards (and vice-versa). Backed by Task 7's
  // GET /api/session/worker/status (user-scoped: only the caller's slot).
  useEffect(() => {
    let dead = false;
    const poll = async () => {
      if (dead) return;
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
      try {
        const r = await fetch('/api/session/worker/status', { cache: 'no-store' });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = (await r.json()) as Record<string, unknown>;
        const w0 = (j && (j as { worker?: Record<string, unknown> }).worker) || {};
        if (!dead) {
          setInteractiveWorker({
            policy: String(j.policy || ''),
            single_active_owner: !!j.single_active_owner,
            max_active: Number(j.max_active || 0),
            active_count: Number(j.active_count || 0),
            owner: j.owner != null ? String(j.owner) : undefined,
            owner_slot: j.owner_slot != null ? String(j.owner_slot) : undefined,
            authenticated_owner: j.authenticated_owner != null ? String(j.authenticated_owner) : undefined,
            owner_active_session: j.owner_active_session != null ? String(j.owner_active_session) : undefined,
            state: (String((w0 as { state?: string }).state || (j.active_count ? 'ready' : 'failed')) as InteractiveWorkerState),
            alive: !!(w0 as { alive?: boolean }).alive,
            running: !!(w0 as { running?: boolean }).running,
            pid: (w0 as { pid?: number }).pid,
            idle_age_sec: (w0 as { idle_age_sec?: number }).idle_age_sec,
          });
          setInteractiveWorkerError('');
        }
      } catch (e) {
        if (!dead) setInteractiveWorkerError(String((e && (e as Error).message) || e));
      }
    };
    poll();
    const id = setInterval(poll, 3000);
    return () => { dead = true; clearInterval(id); };
  }, []);
  useEffect(() => {
    let alive = true;
    const refresh = () => {
      const scoped = String(w.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
      const url = scoped ? `/api/soc?scope=${encodeURIComponent(scoped)}` : '/api/soc';
      fetch(url)
        .then(r => r.ok ? r.json() : null)
        .then((d: { clusters?: Array<{ modules?: SocModule[] }> } | null) => {
          if (!alive || !d) return;
          const mods = (d.clusters || []).flatMap((c) => Array.isArray(c.modules) ? c.modules : []);
          const preferred = mods.find((m) => scoped && (m.id === scoped || m.ip_dir === scoped)) || mods[0];
          setLiveStageStatus((preferred && preferred.status) || null);
        })
        .catch(() => {});
    };
    refresh();
    const timer = setInterval(refresh, 5000);
    window.addEventListener('atlas-data-changed', refresh);
    return () => {
      alive = false;
      clearInterval(timer);
      window.removeEventListener('atlas-data-changed', refresh);
    };
  }, []);
  const updateEffort = async (value: string) => {
    setEffortValue(value);
    setSavingEffort(true);
    setSettingsError('');
    try {
      const resp = await fetch('/api/settings/reasoning-effort', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ effort: value }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || data.ok === false) throw new Error(data.error || `HTTP ${resp.status}`);
      w.CONTEXT = Object.assign({}, w.CONTEXT || {}, {
        reasoningEffort: data.reasoning_effort || value,
      });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    } catch (err) {
      setSettingsError(String(err).replace(/^Error:\s*/, ''));
      setEffortValue((w.CONTEXT && w.CONTEXT.reasoningEffort) || _ctx.reasoningEffort || 'medium');
    } finally {
      setSavingEffort(false);
    }
  };
  const updateModel = async (key: string) => {
    if (!key) return;
    setSavingModel(true);
    setSettingsError('');
    try {
      const resp = await fetch('/api/settings/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || data.ok === false) throw new Error(data.error || `HTTP ${resp.status}`);
      w.CONTEXT = Object.assign({}, w.CONTEXT || {}, {
        model: data.model || _ctx.model,
        modelOptions: Array.isArray(data.model_options) ? data.model_options : modelOptions,
        selectedModelKey: data.selected_model_key || key,
      });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    } catch (err) {
      setSettingsError(String(err).replace(/^Error:\s*/, ''));
    } finally {
      setSavingModel(false);
    }
  };
  const ctxUsed = numericValue(_ctx.tokens, 0) / 1000;             // K tokens
  const ctxMax  = Math.max(1, numericValue(_ctx.maxTokens, 1000000) / 1000);  // K
  const pct = Math.min(100, Math.round((ctxUsed / ctxMax) * 100));
  const ctxUsedLabel = ctxUsed >= 1000 ? (ctxUsed / 1000).toFixed(2) + 'M' : ctxUsed.toFixed(1) + 'K';
  const ctxMaxLabel = ctxMax >= 1000 ? (ctxMax / 1000) + 'M' : ctxMax + 'K';
  const selectStyle = {
    width: '100%',
    minWidth: 0,
    maxWidth: '100%',
    height: 22,
    fontSize: 10,
  };
  return (
    <div className="box tab-nums" style={{ flexShrink: 0, fontVariantNumeric: 'tabular-nums' }}>
      <div className="box-h" style={{ padding: '6px 12px' }}>
        <span style={{ color: 'var(--accent)', fontWeight: 700 }}>ATLAS</span>
        <span style={{ flex: 1 }} />
        <span style={{
          fontSize: 9, padding: '1px 6px', borderRadius: 2,
          background: intent === 'plan' ? 'color-mix(in oklch, var(--warn) 25%, transparent)' : 'color-mix(in oklch, var(--cyan) 25%, transparent)',
          color: intent === 'plan' ? 'var(--warn)' : 'var(--cyan)',
          fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase',
        }}>{intent === 'plan' ? '◐ plan' : '● normal'}</span>
        {onCollapse && (
          <span
            onClick={onCollapse}
            title="collapse right panel (double-click splitter to restore)"
            className="mute"
            style={{ cursor: 'pointer', fontSize: 12, padding: '0 6px',
                     marginLeft: 6, userSelect: 'none' }}
          >›</span>
        )}
      </div>
      <div style={{ padding: '10px 14px', fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)' }}>
        {/* Mode line */}
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 8 }}>
          <span className="mute">Mode</span>
          <span style={{ color: 'var(--fg)' }}>
            {intent === 'plan' ? 'Plan' : 'Normal'}
            <span className="mute"> · {workflow ? (w.FLOW_STAGES || []).find(s => s.id === workflow)?.label : 'free chat'}</span>
          </span>
        </div>
        {/* Model */}
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4 }}>
          <span className="mute">Model</span>
          {modelOptions.length ? (
            <select
              className="dir-select"
              style={selectStyle}
              value={modelKey}
              disabled={savingModel}
              title={_ctx.model || ''}
              onChange={(ev: ChangeEvent<HTMLSelectElement>) => updateModel(ev.currentTarget.value)}>
              {modelOptions.filter(opt => opt.model && !opt.model.toLowerCase().startsWith('default')).map(opt => (
                <option key={opt.key} value={opt.key}>
                  {opt.label ? `${opt.label} · ${opt.model}` : opt.model}
                </option>
              ))}
            </select>
          ) : (
            <span style={{ color: 'var(--fg)' }} title={_ctx.baseUrl}>{_ctx.model || '—'}</span>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4 }}>
          <span className="mute">Effort</span>
          <select
            className="dir-select"
            style={selectStyle}
            value={effortValue}
            disabled={savingEffort}
            title={`reasoning_effort = ${effortValue}`}
            onChange={(ev: ChangeEvent<HTMLSelectElement>) => updateEffort(ev.currentTarget.value)}>
            {effortOptions.map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        {settingsError && (
          <div style={{ marginLeft: 72, marginBottom: 6, color: 'var(--err)', fontSize: 10 }}>
            {settingsError}
          </div>
        )}
        {(_ctx.provider || _ctx.baseUrl) && (
          <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4, fontSize: 'var(--ui-font-size)' }}>
            <span className="mute">via</span>
            <span className="mute trunc" title={_ctx.baseUrl}>
              {_ctx.provider || ''}{_ctx.baseUrl ? ' · ' + _ctx.baseUrl.replace(/^https?:\/\//, '') : ''}
            </span>
          </div>
        )}
        {/* Context with bar */}
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4, marginTop: 6 }}>
          <span className="mute" title="Current context window of the selected/live worker session">Context</span>
          <span>
            <span style={{ color: 'var(--fg)', display: 'inline-block', minWidth: 48, textAlign: 'right' }}>
              {ctxUsedLabel}
            </span>
            <span className="mute"> / {ctxMaxLabel} · </span>
            <span className={pct > 70 ? 'warn' : 'ok'} style={{ display: 'inline-block', minWidth: 30, textAlign: 'right' }}>{pct}%</span>
            <span className="mute" style={{ fontSize: 'var(--ui-control-font-size)', marginLeft: 4 }}>worker</span>
          </span>
        </div>
        <div style={{ marginLeft: 72, marginBottom: 10, height: 4, background: 'var(--bg-2)', borderRadius: 1, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${pct}%`,
            background: pct > 70 ? 'var(--warn)' : 'var(--accent)',
          }} />
        </div>
        {/* Cost ledger — live from /healthz + 'cost' WS events */}
        {(() => {
          const fmt = (n: number) => {
            if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
            if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
            return n.toFixed(0);
          };
          const usd = (n: number) => '$' + (n || 0).toFixed(4);
          const pi = _ctx.pricing ? _ctx.pricing.input  : 0;
          const pc = _ctx.pricing ? _ctx.pricing.cache  : 0;
          const po = _ctx.pricing ? _ctx.pricing.output : 0;
          const tiRaw = numericValue(_ctx.tokensIn, 0);
          const tc = numericValue(_ctx.tokensCache, 0);
          const to = numericValue(_ctx.tokensOut, 0);
          // tokensIn is raw prompt tokens from provider usage and includes
          // the cached subset. The ledger's Input row should show/bill only
          // uncached input; Cached is displayed and charged separately.
          const ti = Math.max(0, tiRaw - tc);
          const cIn   = ti * pi / 1e6;
          const cCach = tc * pc / 1e6;
          const cOut  = to * po / 1e6;
          const cCalc = cIn + cCach + cOut;
          const cTot = numericValue(_ctx.costUsd, 0) > 0 ? numericValue(_ctx.costUsd, 0) : cCalc;
          return (
            <>
              <div className="mute" style={{ fontSize: 'var(--ui-font-size)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
                Cost
                <span className="mute" style={{ fontSize: 'var(--ui-control-font-size)', fontWeight: 400, letterSpacing: 0, textTransform: 'none', marginLeft: 4 }}>
                  · {(_ctx.costScope === 'user_ip' ? `user/IP${_ctx.costIp ? ` ${_ctx.costIp}` : ''}` : 'worker session')}
                  {_ctx.costCalls ? ` · ${_ctx.costCalls} calls` : ''}
                </span>
                {_ctx.pricing && (
                  <span className="mute" style={{ fontSize: 'var(--ui-control-font-size)', fontWeight: 400, letterSpacing: 0, textTransform: 'none', marginLeft: 4 }}>
                    @ ${pi}/${pc}/${po} per 1M
                  </span>
                )}
              </div>
              <div data-role="cost" style={{ display: 'grid', gridTemplateColumns: '64px minmax(56px, 1fr) 76px', gap: 4, fontSize: 'var(--ui-font-size)', lineHeight: 1.55, fontVariantNumeric: 'tabular-nums' }}>
                <span className="mute">Input</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{fmt(ti)}</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{usd(cIn)}</span>

                <span className="mute">Cached</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{fmt(tc)}</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{usd(cCach)}</span>

                <span className="mute">Output</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{fmt(to)}</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{usd(cOut)}</span>

                <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--fg)', fontWeight: 600 }}>Total</span>
                <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--fg)', textAlign: 'right' }}>{fmt(ti + tc + to)}</span>
                <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--ok)', textAlign: 'right', fontWeight: 600 }}>{usd(cTot)}</span>
              </div>
            </>
          );
        })()}

        <AgentWorkerStatus
          workers={liveWorkers}
          workersError={workersError}
          activeIp={activeIp}
          agentAlive={agentAlive}
          agentRunning={agentRunning}
          execMode={atlasUiExecMode()}
          interactiveWorker={interactiveWorker}
          interactiveWorkerError={interactiveWorkerError}
          logic={w.AtlasWorkersLogic}
          onOpenWorkflow={w.openPipelineWorkflowWorkspace}
        />
      </div>
    </div>
  );
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// workspace-panels.jsx / workspace.jsx mount <window.AgentStatusPanel … />.
// Not yet in types/atlas-window.d.ts, so the assignment goes through a narrow
// cast. Remove once all consumers import { AgentStatusPanel } directly.
(window as unknown as { AgentStatusPanel: typeof AgentStatusPanel }).AgentStatusPanel = AgentStatusPanel;
