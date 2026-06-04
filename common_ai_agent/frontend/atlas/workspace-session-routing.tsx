// workspace-session-routing.tsx — session-name normalization, health-counter /
// browser-route matching, exec-mode (orchestrator vs default) resolution,
// workflow<->session mapping, and IP-route extraction.
//
// Extracted from workspace.jsx (the live source of truth) as part of the
// strangler-fig TypeScript migration. This module is an INERT mirror: the
// legacy workspace.jsx still serves the live app. This file owns the pure
// routing helpers that read window.AtlasSessionRouting / ATLAS_USER /
// ACTIVE_SESSION / SCOPE_PATH / ATLAS_EXEC_MODE / ATLAS_BOOT_CONFIG /
// atlasData and performs the runtime window.atlasResolveActiveSession
// assignment inside resolveActiveSession.
//
// Typed in the permissive house style — window-sourced values and
// dynamically-shaped payloads are typed `any` on purpose; do NOT tighten them.

// Narrow `any` cast over `window` for the cross-file globals owned by
// unmigrated .jsx (window.AtlasSessionRouting, window.ATLAS_USER,
// window.atlasData, window.FLOW_STAGES, etc.). Read everything through this so
// the inert mirror stays decoupled from types/atlas-window.d.ts.
const w = window as any;

export const normalizeUiSession = (session: any): string => {
  const norm = (w.atlasData && w.atlasData.normalizeSessionName) || w.normalizeAtlasSessionName;
  try { return norm ? norm(session || '') : ''; }
  catch (_) { return ''; }
};

export const healthMatchesCurrentUser = (payload: any): boolean => {
  const current = normalizeUiSession((w.ATLAS_USER && w.ATLAS_USER.username) || '');
  const response = normalizeUiSession((payload && payload.user_session) || '');
  return !(current && response && current !== response);
};

export const uiSessionRoute = (session: any): { owner: string; ip: string; workflow: string } => {
  const route = w.AtlasSessionRouting || {};
  if (typeof route.sessionRoute === 'function') {
    try { return route.sessionRoute(session); } catch (_) {}
  }
  const parts = normalizeUiSession(session).split('/').filter(Boolean);
  const ip = parts.length >= 3 ? parts[parts.length - 2] : '';
  const owner = parts.length >= 4 ? `${parts[0]}/${parts[1]}` : (parts[0] || '');
  return {
    owner,
    ip: ip && ip !== 'default' && ip !== 'soc' ? ip : '',
    workflow: parts.length >= 3 ? (parts[parts.length - 1] || '') : '',
  };
};

export const uiHealthCountersMatchBrowserRoute = (payload: any): boolean => {
  const route = w.AtlasSessionRouting || {};
  const browserSession = normalizeUiSession(w.ACTIVE_SESSION || '');
  const payloadSession = normalizeUiSession((payload && payload.active_session) || '');
  if (typeof route.healthCountersMatchRoute === 'function') {
    try { return route.healthCountersMatchRoute({ browserSession, payloadSession }); } catch (_) {}
  }
  if (!browserSession || !payloadSession || browserSession === payloadSession) return true;
  const browser = uiSessionRoute(browserSession);
  const incoming = uiSessionRoute(payloadSession);
  const sameOwner = !browser.owner || !incoming.owner || browser.owner === incoming.owner || incoming.owner === 'local-admin';
  return !browser.ip || (!!incoming.ip && incoming.ip === browser.ip && sameOwner);
};

export const uiEffectiveHealthSession = (payload: any): string => {
  const route = w.AtlasSessionRouting || {};
  const browserSession = normalizeUiSession(w.ACTIVE_SESSION || '');
  const payloadSession = normalizeUiSession((payload && payload.active_session) || '');
  if (typeof route.shouldUseBrowserSession === 'function') {
    try {
      return route.shouldUseBrowserSession({ browserSession, payloadSession })
        ? browserSession
        : (payloadSession || browserSession);
    } catch (_) {}
  }
  if (!browserSession || !payloadSession || browserSession === payloadSession) return payloadSession || browserSession;
  return uiHealthCountersMatchBrowserRoute(payload) ? payloadSession : browserSession;
};

export const atlasUiExecMode = (): string => String(
  w.ATLAS_EXEC_MODE
  || w.ATLAS_DEFAULT_EXEC_MODE
  || (w.ATLAS_BOOT_CONFIG && w.ATLAS_BOOT_CONFIG.exec_mode)
  || ''
).trim().toLowerCase();

export const atlasUiOrchestratorMode = (): boolean => atlasUiExecMode() === 'orchestrator';

export const defaultWorkflowForExecMode = (): string => atlasUiOrchestratorMode() ? 'orchestrator' : 'default';

export const workflowForExecMode = (wf: any): string => {
  const normalized = normalizeUiSession(wf || '');
  if (atlasUiOrchestratorMode()) {
    return (!normalized || normalized === 'default') ? 'orchestrator' : normalized;
  }
  return (!normalized || normalized === 'orchestrator') ? 'default' : normalized;
};

export const initialInputRouteForExecMode = (): { type: string; workflow: string; session: string } => {
  const wf = defaultWorkflowForExecMode();
  return {
    type: atlasUiOrchestratorMode() ? 'orchestrator-chat' : 'workflow-chat',
    workflow: wf,
    session: '',
  };
};

// Legacy histories may contain an old "[scope] ...\n\n" user-message prefix.
// Keep stripping it for display; new sends put scope/path rules in the
// workflow system prompt instead of repeating them in every user turn.
export const stripScopeDirective = (t: any): any => {
  if (typeof t === 'string' && t.startsWith('[scope] ')) {
    const i = t.indexOf('\n\n');
    if (i >= 0) return t.slice(i + 2);
  }
  return t;
};

// URL `?ip=` wins over localStorage on the READ direction so deep links
// like /?ip=cmux_url_test pick up the requested IP even when a previous
// session left `validator/default/default` in localStorage.
export function resolveActiveSession(): string {
  try {
    const url = new URLSearchParams(window.location.search);
    const rawUrlSession = String(url.get('session') || url.get('sid') || url.get('namespace') || '')
      .trim()
      .replace(/^\/+|\/+$/g, '');
    const urlSession = normalizeUiSession(rawUrlSession) || rawUrlSession;
    const urlSessionParts = urlSession.split('/').filter(Boolean);
    const urlIp = String(url.get('ip') || url.get('ip_id') || '').trim();
    const urlWf = String(url.get('workflow') || url.get('wf') || '').trim()
      || defaultWorkflowForExecMode()
      || 'default';
    const username = (w.ATLAS_USER && w.ATLAS_USER.username)
      || w.ATLAS_USER_SESSION_ID
      || 'validator';
    const rawWorkspaceSession = String(
      url.get('workspace_session')
        || url.get('workspace')
        || w.ATLAS_WORKSPACE_SESSION_ID
        || (() => {
          try { return localStorage.getItem('atlasWorkspaceSessionId') || ''; }
          catch (_) { return ''; }
        })()
        || ''
    ).trim().replace(/^\/+|\/+$/g, '');
    const workspaceSession = normalizeUiSession(rawWorkspaceSession) || rawWorkspaceSession || 'default';
    if (urlSessionParts.length >= 4) {
      return urlSession;
    }
    if (urlSessionParts.length === 3) {
      return normalizeUiSession(`${urlSessionParts[0]}/${workspaceSession}/${urlSessionParts[1]}/${urlSessionParts[2]}`)
        || `${urlSessionParts[0]}/${workspaceSession}/${urlSessionParts[1]}/${urlSessionParts[2]}`;
    }
    if (urlSessionParts.length === 2) {
      return normalizeUiSession(`${username}/${workspaceSession}/${urlSessionParts[0]}/${urlSessionParts[1]}`)
        || `${username}/${workspaceSession}/${urlSessionParts[0]}/${urlSessionParts[1]}`;
    }
    if (urlIp && urlIp !== 'default') {
      return normalizeUiSession(`${username}/${workspaceSession}/${urlIp}/${urlWf}`) || `${username}/${workspaceSession}/${urlIp}/${urlWf}`;
    }
    try {
      const stored = localStorage.getItem('atlasActiveSession') || '';
      const normalizedStored = normalizeUiSession(stored) || stored;
      const storedOwner = (normalizedStored.split('/').filter(Boolean)[0] || '');
      if (normalizedStored && (!username || storedOwner === username)) return normalizedStored;
    } catch (_) {}
    return normalizeUiSession(`${username}/default/default/${urlWf}`) || `${username}/default/default/${urlWf}`;
  } catch (_) {
    return 'default';
  }
}
try { w.atlasResolveActiveSession = resolveActiveSession; } catch (_) {}

const explicitRouteSession = (): string => {
  try {
    const url = new URLSearchParams(window.location.search);
    const hasExplicitRoute = !!(
      url.get('session')
      || url.get('sid')
      || url.get('namespace')
      || url.get('ip')
      || url.get('ip_id')
      || url.get('workflow')
      || url.get('wf')
    );
    const resolved = resolveActiveSession() || '';
    return hasExplicitRoute ? (normalizeUiSession(resolved) || String(resolved).trim()) : '';
  } catch (_) {
    return '';
  }
};

export const activeUiSession = (): string => {
  const routeSession = explicitRouteSession();
  const activeSession = normalizeUiSession(w.ACTIVE_SESSION || '') || String(w.ACTIVE_SESSION || '').trim();
  const resolved = resolveActiveSession() || '';
  const resolvedSession = normalizeUiSession(resolved) || String(resolved).trim();
  return routeSession || activeSession || resolvedSession || 'default';
};

export const appendActiveSessionParam = (params: URLSearchParams): URLSearchParams => {
  const sid = activeUiSession();
  if (sid) params.set('session_id', sid);
  return params;
};

export const ssotIpFromSession = (session: any): string => {
  const parts = normalizeUiSession(session).split('/').filter(Boolean);
  const idx = parts.lastIndexOf('ssot-gen');
  if (idx > 0) return parts[idx - 1];
  return routeSessionIp(session);
};
w.ssotIpFromSession = ssotIpFromSession;  // Phase 13a: consumed by ssot-doc.jsx

export const isSsotYamlPath = (path: any): boolean => /\.ssot\.ya?ml$/i.test(String(path || ''));

export const KNOWN_WORKFLOW_PATH_SEGMENTS = new Set<string>([
  'default',
  'orchestrator',
  'ssot-gen',
  'fl-model-gen',
  'rtl-gen',
  'lint',
  'tb-gen',
  'sim',
  'sim_debug',
  'coverage',
  'contract-reflection',
  'syn',
  'sta',
  'pnr',
  'sta-post',
  'goal-audit',
]);

export const atlasRoutingApi = (): any => w.AtlasSessionRouting || {};

export const routeSessionIp = (session: any): string => {
  const api = atlasRoutingApi();
  if (typeof api.sessionIpFromSession === 'function') {
    return api.sessionIpFromSession(session);
  }
  const parts = normalizeUiSession(session).split('/').filter(Boolean);
  const ip = parts.length >= 3 ? parts[parts.length - 2] : '';
  const lowered = ip.toLowerCase();
  return ip && /^[A-Za-z][A-Za-z0-9_.-]*$/.test(ip) && !KNOWN_WORKFLOW_PATH_SEGMENTS.has(lowered) && lowered !== 'soc' && lowered !== 'user' ? ip : '';
};

export const routeScopeIp = (scope: any): string => {
  const api = atlasRoutingApi();
  if (typeof api.scopeIp === 'function') return api.scopeIp(scope);
  const parts = normalizeUiSession(scope).split('/').filter(Boolean);
  const ip = parts[parts.length - 1] || '';
  const lowered = ip.toLowerCase();
  return ip && /^[A-Za-z][A-Za-z0-9_.-]*$/.test(ip) && !KNOWN_WORKFLOW_PATH_SEGMENTS.has(lowered) && lowered !== 'soc' && lowered !== 'user' ? ip : '';
};

export const activeIpForRoute = (sessions: any[] = []): string => {
  const api = atlasRoutingApi();
  if (typeof api.activeIpForRouting === 'function') {
    return api.activeIpForRouting({
      sessions,
      activeIp: w.ACTIVE_IP || '',
      scopePath: w.SCOPE_PATH || '',
    });
  }
  for (const session of sessions) {
    const ip = routeSessionIp(session);
    if (ip) return ip;
  }
  return routeScopeIp(w.ACTIVE_IP || '') || routeScopeIp(w.SCOPE_PATH || '');
};

export const workflowFromSession = (session: any): string => {
  const parts = normalizeUiSession(session).split('/').filter(Boolean);
  const last = parts[parts.length - 1] || '';
  return (w.FLOW_STAGES || []).some((s: any) => s.id === last) ? last : '';
};

export const sessionForExecMode = (session: any): string => {
  const sid = normalizeUiSession(session || '');
  const parts = sid.split('/').filter(Boolean);
  if (parts.length >= 3) {
    const workflow = workflowForExecMode(parts[parts.length - 1] || '');
    if (workflow && workflow !== parts[parts.length - 1]) {
      const nextParts = parts.slice();
      nextParts[nextParts.length - 1] = workflow;
      return normalizeUiSession(nextParts.join('/'));
    }
  }
  return sid;
};
