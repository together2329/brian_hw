// agent-status-panel.jsx — Phase 19 refactor: AgentStatusPanel (614L)
// extracted from workspace-panels.jsx so the latter drops under the
// 2000-line target. Same IIFE + lambda forward-ref pattern.

(() => {

// Forward-ref to workspace.jsx helpers (resolved at call time):
const workspaceFetchWorkerSnapshot = (...a) => window.workspaceFetchWorkerSnapshot(...a);
const healthMatchesCurrentUser = (...a) => window.healthMatchesCurrentUser(...a);
const uiEffectiveHealthSession = (...a) => window.uiEffectiveHealthSession(...a);
const uiHealthCountersMatchBrowserRoute = (...a) => window.uiHealthCountersMatchBrowserRoute(...a);
const uiSessionRoute = (...a) => window.uiSessionRoute(...a);
const atlasUiExecMode = (...a) => window.atlasUiExecMode(...a);
const atlasStatusMeta = (...a) => window.atlasStatusMeta(...a);
const AtlasStatusBadge = (...a) => window.AtlasStatusBadge(...a);
const normalizeUiSession = (...a) => window.normalizeUiSession(...a);


const AgentStatusPanel = ({ intent, workflow, activeIp = '', agentAlive = false, agentRunning = false, onCollapse }) => {
  // Live context — populated by /healthz + WS 'context' events.
  const [liveContext, setLiveContext] = React.useState(() => Object.assign({}, window.CONTEXT || {}));
  const _ctx = liveContext;
  const [liveStageStatus, setLiveStageStatus] = React.useState(null);
  const [liveWorkers, setLiveWorkers] = React.useState([]);
  const [workersError, setWorkersError] = React.useState('');
  const effortOptions = ['none', 'low', 'medium', 'high', 'xhigh'];
  const normalizeEffortValue = (value) => (
    effortOptions.includes(String(value || '').toLowerCase())
      ? String(value || '').toLowerCase()
      : 'medium'
  );
  const modelOptions = Array.isArray(_ctx.modelOptions) ? _ctx.modelOptions : [];
  const modelKey =
    _ctx.selectedModelKey
    || ((modelOptions.find(m => m.model === _ctx.model) || modelOptions[0] || {}).key || '');
  const [effortValue, setEffortValue] = React.useState(normalizeEffortValue(_ctx.reasoningEffort));
  const [savingEffort, setSavingEffort] = React.useState(false);
  const [savingModel, setSavingModel] = React.useState(false);
  const [settingsError, setSettingsError] = React.useState('');
  const numericValue = (value, fallback = 0) => {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  };
  const sessionPartsFor = (session) => normalizeUiSession(session).split('/').filter(Boolean);
  const shouldPreserveBrowserCounters = (incomingSession) => {
    const incoming = sessionPartsFor(incomingSession);
    const browserSession = normalizeUiSession(window.ACTIVE_SESSION || '');
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
  const mergeStableContext = (prev, extra) => {
    const prevCtx = prev || {};
    const clean = {};
    Object.entries(extra || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null) clean[key] = value;
    });
    const globalCtx = window.CONTEXT || {};
    const merged = Object.assign({}, prevCtx, globalCtx, clean);
    const prevSession = normalizeUiSession(prevCtx.activeSession || '');
    const incomingSession = normalizeUiSession(clean.activeSession || globalCtx.activeSession || merged.activeSession || '');
    const browserSession = normalizeUiSession(window.ACTIVE_SESSION || '');
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
    const _sessTail = (s) => String(s || '').split('/').filter(Boolean).slice(-2).join('/');
    const sameSession = !prevSession || !effectiveSession
      || prevSession === effectiveSession
      || (_sessTail(prevSession) && _sessTail(prevSession) === _sessTail(effectiveSession));
	    if (effectiveSession) merged.activeSession = effectiveSession;

	    const counters = ['tokensIn', 'tokensCache', 'tokensOut', 'costUsd']; // 'tokens' = live context size, DROPS on compression → must not be Math.max-clamped
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
  React.useEffect(() => {
    let alive = true;
    const syncContext = (extra) => {
      if (!alive) return;
      setLiveContext(prev => mergeStableContext(prev, extra));
    };
    const poll = () => {
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
      fetch('/healthz', { cache: 'no-store' })
        .then(r => r.ok ? r.json() : null)
	        .then(j => {
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
  React.useEffect(() => {
    setEffortValue(normalizeEffortValue(_ctx.reasoningEffort));
  }, [_ctx.reasoningEffort]);
  // Live orchestrator worker list. Server caches /api/orchestrator/workers
  // per URL for 1.5s, so this 3s poll is one HTTP round-trip per tab, not
  // per worker. Pauses while the tab is hidden.
  React.useEffect(() => {
    let dead = false;
    const workerIp = (() => {
      const direct = String(activeIp || '').trim();
      if (direct && direct !== 'default') return direct;
      const scoped = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
      const leaf = scoped.split('/').filter(Boolean).pop() || '';
      return leaf && leaf !== 'default' ? leaf : '';
    })();
    const poll = async () => {
      if (dead) return;
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
      try {
        const j = await workspaceFetchWorkerSnapshot({ ip: workerIp, activeOnly: true });
        const list = Array.isArray(j && j.workers) ? j.workers : [];
        if (!dead) {
          setLiveWorkers(list);
          setWorkersError('');
        }
      } catch (e) {
        if (!dead) setWorkersError(String((e && e.message) || e));
      }
    };
    poll();
    const id = setInterval(poll, 3000);
    return () => { dead = true; clearInterval(id); };
  }, [activeIp]);
  React.useEffect(() => {
    let alive = true;
    const refresh = () => {
      const scoped = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
      const url = scoped ? `/api/soc?scope=${encodeURIComponent(scoped)}` : '/api/soc';
      fetch(url)
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          if (!alive || !d) return;
          const mods = (d.clusters || []).flatMap(c => Array.isArray(c.modules) ? c.modules : []);
          const preferred = mods.find(m => scoped && (m.id === scoped || m.ip_dir === scoped)) || mods[0];
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
  const updateEffort = async (value) => {
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
      window.CONTEXT = Object.assign({}, window.CONTEXT || {}, {
        reasoningEffort: data.reasoning_effort || value,
      });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    } catch (err) {
      setSettingsError(String(err).replace(/^Error:\s*/, ''));
      setEffortValue((window.CONTEXT && window.CONTEXT.reasoningEffort) || _ctx.reasoningEffort || 'medium');
    } finally {
      setSavingEffort(false);
    }
  };
  const updateModel = async (key) => {
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
      window.CONTEXT = Object.assign({}, window.CONTEXT || {}, {
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
            <span className="mute"> · {workflow ? window.FLOW_STAGES.find(s => s.id === workflow)?.label : 'free chat'}</span>
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
              onChange={(ev) => updateModel(ev.currentTarget.value)}>
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
            onChange={(ev) => updateEffort(ev.currentTarget.value)}>
            {effortOptions.map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        {settingsError && (
          <div style={{ marginLeft: 72, marginBottom: 6, color: 'var(--err)', fontSize: 10 }}>
            {settingsError}
          </div>
        )}
        {(_ctx.provider || _ctx.baseUrl) && (
          <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4, fontSize: 10 }}>
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
            <span className="mute" style={{ fontSize: 9, marginLeft: 4 }}>worker</span>
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
          const fmt = (n) => {
            if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
            if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
            return n.toFixed(0);
          };
          const usd = (n) => '$' + (n || 0).toFixed(4);
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
              <div className="mute" style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
                Cost
                <span className="mute" style={{ fontSize: 9, fontWeight: 400, letterSpacing: 0, textTransform: 'none', marginLeft: 4 }}>
                  · {(_ctx.costScope === 'user_ip' ? `user/IP${_ctx.costIp ? ` ${_ctx.costIp}` : ''}` : 'worker session')}
                  {_ctx.costCalls ? ` · ${_ctx.costCalls} calls` : ''}
                </span>
                {_ctx.pricing && (
                  <span className="mute" style={{ fontSize: 9, fontWeight: 400, letterSpacing: 0, textTransform: 'none', marginLeft: 4 }}>
                    @ ${pi}/${pc}/${po} per 1M
                  </span>
                )}
              </div>
              <div data-role="cost" style={{ display: 'grid', gridTemplateColumns: '64px minmax(56px, 1fr) 76px', gap: 4, fontSize: 'var(--ui-control-font-size)', lineHeight: 1.55, fontVariantNumeric: 'tabular-nums' }}>
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

        {/* ── orchestrator workers (live lazy-spawn state) ──────── */}
        {(() => {
          const _wl = window.AtlasWorkersLogic;
          const singleWorkerMode = atlasUiExecMode() === 'single-worker';
          const sessionWorkerAlive = !!agentAlive;
          const sessionWorkerLabel = agentRunning ? 'running' : (sessionWorkerAlive ? 'hot' : 'cold');
          const { total, upCount } = _wl
            ? _wl.summarizeWorkers(liveWorkers)
            : { total: liveWorkers.length, upCount: liveWorkers.filter(w => String(w.status || '') === 'ok').length };
          const _portFromUrl = _wl ? _wl.portFromUrl : (u) => {
            const m = String(u || '').match(/:(\d+)(?:\/|$)/);
            return m ? m[1] : '';
          };
          const portShort = (w) => _portFromUrl(w.url) || (String(w.workflow || '').slice(0, 4));
          const tone = (w) => {
            if (_wl) {
              // workerTone covers ok/mismatch/pending; extend locally for queued/pending counts
              const s = String(w.status || '');
              if (s === 'ok' && Number(w.running_count || 0) > 0) return 'active';
              if (s === 'ok' && Number(w.pending_count || 0) > 0) return 'pending';
              if (s === 'ok' && Number(w.queued_count || 0) > 0) return 'queued';
              return _wl.workerTone(w);
            }
            const s = String(w.status || '');
            if (s === 'ok' && Number(w.running_count || 0) > 0) return 'active';
            if (s === 'ok' && Number(w.pending_count || 0) > 0) return 'pending';
            if (s === 'ok' && Number(w.queued_count || 0) > 0) return 'queued';
            if (s === 'ok') return 'done';
            if (s === 'mismatch') return 'err';
            return 'pending';
          };
          const cfgFor = (t) => (
            t === 'active'  ? { color: 'var(--accent)', glyph: '●', bg: 'color-mix(in oklch, var(--accent) 14%, transparent)', border: 'var(--accent)' } :
            t === 'done'    ? { color: 'var(--ok)',     glyph: '✓', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)',     border: 'var(--ok)' } :
            t === 'err'     ? { color: 'var(--err)',    glyph: '✗', bg: 'color-mix(in oklch, var(--err) 14%, transparent)',    border: 'var(--err)' } :
            t === 'queued'  ? { color: 'var(--fg-mute)',glyph: '◌', bg: 'color-mix(in oklch, var(--fg-mute) 9%, transparent)', border: 'var(--line)' } :
                              { color: 'var(--fg-mute)',glyph: '○', bg: 'transparent',                                          border: 'var(--line)' }
          );
          const activeJobs = liveWorkers.flatMap(w => (
            Array.isArray(w.active_jobs)
              ? w.active_jobs.map(j => Object.assign({ worker_workflow: w.workflow }, j))
              : []
          ));
          const jobLine = (job) => {
            const bits = [
              job.status || 'running',
              job.queue_reason || '',
              job.attempt && job.max_attempts && Number(job.max_attempts) > 1
                ? `try ${job.attempt}/${job.max_attempts}`
                : '',
              job.worker_log_entries ? `${job.worker_log_entries} log` : '',
              job.worker_pid ? `pid ${job.worker_pid}` : '',
            ].filter(Boolean);
            return bits.join(' · ');
          };
          return (
            <>
              <div className="mute" style={{
                fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase',
                marginTop: 14, marginBottom: 6,
                display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap',
              }}
                title={singleWorkerMode
                  ? 'Live state of the single session worker process.'
                  : 'Live state of orchestrator workers (port + status). Lazy-spawned on first dispatch.'}
              >
                <span style={{ color: 'var(--accent)', fontWeight: 700 }}>▸ {singleWorkerMode ? 'agent' : 'workers'}</span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>· {singleWorkerMode ? 'single' : 'orch'}</span>
                <span style={{ flex: 1 }} />
                <span className={upCount > 0 ? 'ok' : 'mute'} style={{ fontSize: 9 }}>
                  {workersError ? '!' : (singleWorkerMode ? sessionWorkerLabel : `${upCount}/${total} up`)}
                </span>
              </div>
              {total === 0 ? (
                <div className="mute" style={{ fontSize: 10, padding: '4px 0 10px', textAlign: 'center' }}>
                  {workersError || (
                    singleWorkerMode
                      ? (agentRunning ? 'session worker running' : (sessionWorkerAlive ? 'session worker hot — no workflow workers needed' : 'warming session worker'))
                      : 'no workers yet — dispatch a workflow to spawn'
                  )}
                </div>
              ) : (
                <div style={{
                  display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4,
                  fontSize: 10, marginBottom: 12,
                }}>
                  {liveWorkers.map((w) => {
                    const cfg = cfgFor(tone(w));
                    const label = String(w.workflow || '').slice(0, 6) || portShort(w);
                    const running = Number(w.running_count || 0);
                    const pending = Number(w.pending_count || 0);
                    const queued = Number(w.queued_count || 0);
                    const active = running || pending || queued;
                    return (
                      <div key={w.url || w.workflow} style={{
                        border: `1px solid ${cfg.border}`, borderRadius: 2,
                        padding: '4px 6px', textAlign: 'center', background: cfg.bg,
                        fontFamily: 'var(--mono)',
                      }}
                        title={
                          `${w.workflow || '?'}\n` +
                          `${w.url || ''}\n` +
                          `status: ${w.status || '-'}` +
                          (running ? `\nrunning jobs: ${running}` : '') +
                          (pending ? `\nstarting jobs: ${pending}` : '') +
                          (queued ? `\nqueued jobs: ${queued}` : '') +
                          (w.bound_workflow ? `\nbound: ${w.bound_workflow}` : '')
                        }
                      >
                        <div style={{ color: cfg.color, fontWeight: 700, fontSize: 10 }}>
                          {cfg.glyph} {label}
                        </div>
                        <div className="mute" style={{ fontSize: 9, marginTop: 1 }}>
                          {portShort(w)}{active ? ` · ${running ? running : pending ? 's' + pending : 'q' + queued}` : ''}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              {activeJobs.length > 0 ? (
                <div style={{
                  borderTop: '1px solid var(--line)',
                  paddingTop: 8,
                  marginBottom: 12,
                  fontSize: 10,
                  fontFamily: 'var(--mono)',
                }}>
                  <div className="mute" style={{
                    fontSize: 9,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    marginBottom: 5,
                  }}>now</div>
                  {activeJobs.slice(0, 4).map(job => (
                    <button
                      key={job.job_id || `${job.worker_workflow}-${job.run_id}`}
                      type="button"
                      onClick={() => {
                        try {
                          window.openPipelineWorkflowWorkspace?.({
                            ip: String(job.ip || activeIp || '').trim(),
                            workflow: job.workflow || job.worker_workflow,
                          });
                        } catch (_) {}
                      }}
                      title={[
                        job.session || '',
                        job.worker || '',
                        job.worker_log_path ? `log: ${job.worker_log_path}` : '',
                        job.result_summary || job.error || '',
                      ].filter(Boolean).join('\n')}
                      style={{
                        width: '100%',
                        display: 'grid',
                        gridTemplateColumns: '12px minmax(0, 1fr)',
                        gap: 6,
                        alignItems: 'start',
                        textAlign: 'left',
                        padding: '4px 0',
                        border: 0,
                        borderBottom: '1px solid color-mix(in oklch, var(--line) 70%, transparent)',
                        background: 'transparent',
                        color: 'var(--fg)',
                        cursor: 'pointer',
                        fontFamily: 'var(--mono)',
                      }}
                    >
                      <span style={{ color: job.status === 'queued' ? 'var(--fg-mute)' : 'var(--accent)' }}>
                        {job.status === 'queued' ? '◌' : '▶'}
                      </span>
                      <span style={{ minWidth: 0 }}>
                        <span style={{ display: 'block', fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {job.workflow || job.worker_workflow || 'worker'}
                        </span>
                        <span className="mute" style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {jobLine(job)}
                        </span>
                      </span>
                    </button>
                  ))}
                </div>
              ) : null}
            </>
          );
        })()}
      </div>
    </div>
  );
};

window.AgentStatusPanel = AgentStatusPanel;

})();
