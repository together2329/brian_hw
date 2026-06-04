// data-loaders.tsx — async API loaders + session/health helpers extracted
// from data.jsx (strangler-fig).
//
// data.jsx is ONE IIFE of ORDERED side-effects. The loaders below are defined
// AFTER the top-level window.* seeds and BEFORE window.atlasData is published,
// and they close over shared, mutable state (the two request caches and the
// URL_ACTIVE_SESSION const) plus a couple of sibling functions. To keep the
// main file <1000 lines without disturbing the IIFE's execution order, these
// functions are packaged as a FACTORY: data.tsx calls createDataLoaders(deps)
// at exactly the point the originals were defined, passing in the same shared
// cache instances + URL_ACTIVE_SESSION. The returned closures are byte-for-byte
// equivalent to the originals (same captured references, same call order).
//
// This module performs NO window.* writes at import time. Every window.* read /
// write inside these functions happens at CALL time, exactly as before, so the
// ordered side-effect contract of data.jsx is preserved.

import {
  DEFAULT_WORKFLOW,
  KNOWN_WORKFLOWS,
  normalizeSessionName,
  normalizeScopePath,
  normalizeTodos,
  asTreeNode,
  activeIpFromSession,
  activeWorkflowFromSession,
  sessionPartsEndWithWorkflow,
  flowStagesForExecMode,
  DEFAULT_FLOW_STAGES,
} from './data-helpers';

export interface DataLoaderDeps {
  // Shared, mutable request-coalescing caches (same instances the bootstrap
  // and atlasData mutations rely on). Passed in so the closures capture the
  // identical Map objects the original IIFE created.
  sessionStateCache: Map<string, any>;
  workerSnapshotCache: Map<string, any>;
  // Module-level const computed once at boot from the URL.
  URL_ACTIVE_SESSION: string;
  // Tuning constants (kept as deps so the main file owns the canonical values).
  SESSION_STATE_CACHE_MS: number;
  CHAT_RECENT_LIMIT: number;
  CHAT_SWITCH_LIMIT: number;
  WORKER_SNAPSHOT_CACHE_MS: number;
}

export interface DataLoaders {
  setActiveSessionName: (session: unknown) => string;
  refreshSessionState: (
    session?: unknown,
    hydrateConversation?: boolean,
    opts?: any,
  ) => Promise<any>;
  refreshActiveConversation: (session?: unknown, opts?: any) => Promise<any>;
  fetchWorkerSnapshot: (opts?: any) => Promise<any>;
  refreshFileTree: (path?: unknown, opts?: any) => Promise<void>;
  invalidateSessionState: (session?: unknown) => void;
  applyTodoPayload: (payload: any) => void;
  refreshTodosAfterMutation: (session: unknown, payload: any) => Promise<any>;
  refreshTodos: (opts?: any) => Promise<void>;
  refreshSlashCommands: () => Promise<void>;
  refreshSsotList: () => Promise<void>;
  refreshProgress: () => Promise<any>;
  refreshHealth: () => Promise<void>;
  refreshWorkflows: () => Promise<void>;
  todoJsonRequest: (url: string, opts?: any) => Promise<any>;
}

const w = window as any;

export function createDataLoaders(deps: DataLoaderDeps): DataLoaders {
  const {
    sessionStateCache,
    workerSnapshotCache,
    URL_ACTIVE_SESSION,
    SESSION_STATE_CACHE_MS,
    CHAT_RECENT_LIMIT,
    CHAT_SWITCH_LIMIT,
    WORKER_SNAPSHOT_CACHE_MS,
  } = deps;

  function healthMatchesCurrentUser(payload: any): boolean {
    const current = normalizeSessionName((w.ATLAS_USER && w.ATLAS_USER.username) || '');
    const response = normalizeSessionName((payload && payload.user_session) || '');
    return !(current && response && current !== response);
  }

  function routeSessionInfo(session: unknown): { owner: string; ip: string; workflow: string } {
    const route = w.AtlasSessionRouting || {};
    if (typeof route.sessionRoute === 'function') {
      try { return route.sessionRoute(session); } catch (_) {}
    }
    const parts = normalizeSessionName(session).split('/').filter(Boolean);
    const ip = parts.length >= 3 ? parts[parts.length - 2] : '';
    return {
      owner: parts[0] || '',
      ip: activeIpFromSession(session) || ip,
      workflow: parts.length >= 3 ? (parts[parts.length - 1] || '') : '',
    };
  }

  function browserSessionOverridesHealth(payload: any): boolean {
    const route = w.AtlasSessionRouting || {};
    const browserSession = normalizeSessionName(w.ACTIVE_SESSION || '');
    const payloadSession = normalizeSessionName((payload && payload.active_session) || '');
    if (typeof route.shouldUseBrowserSession === 'function') {
      try {
        return route.shouldUseBrowserSession({ browserSession, payloadSession });
      } catch (_) {}
    }
    if (!browserSession || !payloadSession || browserSession === payloadSession) return false;
    const browser = routeSessionInfo(browserSession);
    const incoming = routeSessionInfo(payloadSession);
    const sameOwner = !browser.owner || !incoming.owner || browser.owner === incoming.owner || incoming.owner === 'local-admin';
    return !!browser.ip && (!incoming.ip || browser.ip !== incoming.ip || !sameOwner);
  }

  function healthCountersMatchBrowserRoute(payload: any): boolean {
    const route = w.AtlasSessionRouting || {};
    const browserSession = normalizeSessionName(w.ACTIVE_SESSION || '');
    const payloadSession = normalizeSessionName((payload && payload.active_session) || '');
    if (typeof route.healthCountersMatchRoute === 'function') {
      try {
        return route.healthCountersMatchRoute({ browserSession, payloadSession });
      } catch (_) {}
    }
    if (!browserSession || !payloadSession || browserSession === payloadSession) return true;
    const browser = routeSessionInfo(browserSession);
    const incoming = routeSessionInfo(payloadSession);
    const sameOwner = !browser.owner || !incoming.owner || browser.owner === incoming.owner || incoming.owner === 'local-admin';
    return !browser.ip || (!!incoming.ip && incoming.ip === browser.ip && sameOwner);
  }

  function setActiveSessionName(session: unknown): string {
    const sid = normalizeSessionName(session) || 'default';
    w.ACTIVE_SESSION = sid;
    try {
      const route = w.AtlasSessionRouting || {};
      const ip = typeof route.sessionIpFromSession === 'function'
        ? route.sessionIpFromSession(sid)
        : activeIpFromSession(sid);
      w.ACTIVE_IP = ip || '';
    } catch (_) {}
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    return sid;
  }

  function explicitBrowserRouteSession(): string {
    let params: URLSearchParams;
    try { params = new URLSearchParams(window.location.search || ''); }
    catch (_) { return ''; }
    const hasRoute = !!(
      params.get('session')
      || params.get('sid')
      || params.get('namespace')
      || params.get('ip')
      || params.get('ip_id')
      || params.get('workflow')
      || params.get('wf')
    );
    if (!hasRoute) return '';
    const direct = normalizeSessionName(
      params.get('session') || params.get('sid') || params.get('namespace') || '',
    );
    const directParts = direct.split('/').filter(Boolean);
    const storedOwner = (() => {
      try { return normalizeSessionName(localStorage.getItem('atlasUserSessionId')); }
      catch (_) { return ''; }
    })();
    const storedWorkspace = (() => {
      try { return normalizeSessionName(localStorage.getItem('atlasWorkspaceSessionId')); }
      catch (_) { return ''; }
    })();
    const owner = normalizeSessionName(
      params.get('session_id')
      || params.get('user_session')
      || params.get('owner')
      || storedOwner
      || w.ATLAS_USER_SESSION_ID
      || '',
    ) || 'default';
    const workspace = normalizeSessionName(
      params.get('workspace_session')
      || params.get('workspace')
      || storedWorkspace
      || w.ATLAS_WORKSPACE_SESSION_ID
      || '',
    ) || 'default';
    if (directParts.length >= 4) return direct;
    if (directParts.length === 3) {
      return normalizeSessionName(`${directParts[0]}/${workspace}/${directParts[1]}/${directParts[2]}`);
    }
    if (directParts.length === 2) {
      const ip = directParts[0] || DEFAULT_WORKFLOW;
      const workflow = directParts[1] || DEFAULT_WORKFLOW;
      return normalizeSessionName(`${owner}/${workspace}/${ip}/${workflow}`);
    }
    const ip = normalizeSessionName(params.get('ip') || params.get('ip_id') || '');
    const workflow = normalizeSessionName(params.get('workflow') || params.get('wf') || '') || DEFAULT_WORKFLOW;
    return ip ? normalizeSessionName(`${owner}/${workspace}/${ip}/${workflow}`) : '';
  }

  function activeFileTreeSession(): string {
    return (
      explicitBrowserRouteSession()
      || normalizeSessionName(URL_ACTIVE_SESSION || '')
      || normalizeSessionName(w.ACTIVE_SESSION || '')
      || 'default'
    );
  }

  async function refreshSessionState(
    session?: unknown,
    hydrateConversation: boolean = true,
    opts: any = {},
  ): Promise<any> {
    const sid = normalizeSessionName(session || w.ACTIVE_SESSION || 'default');
    if (!sid) return null;
    // mode: conversation (default) | full | recent
    const mode = (opts && opts.mode) || (() => {
      try { return localStorage.getItem('atlasConversationMode') || 'conversation'; }
      catch (_) { return 'conversation'; }
    })();
    const requestedLimit = opts && opts.limit !== undefined ? Number(opts.limit) : NaN;
    const limit = Number.isFinite(requestedLimit)
      ? requestedLimit
      : (mode === 'full' ? 200 : CHAT_RECENT_LIMIT);
    const force = !!(opts && opts.force);
    const url = '/api/session/state'
      + '?session=' + encodeURIComponent(sid)
      + '&limit=' + encodeURIComponent(String(limit))
      + '&mode='  + encodeURIComponent(mode);
    try {
      const now = Date.now();
      const cached = sessionStateCache.get(url);
      let d = null;
      if (!force && cached && cached.promise) {
        d = await cached.promise;
      } else if (!force && cached && cached.data && (now - cached.at) < SESSION_STATE_CACHE_MS) {
        d = cached.data;
      } else {
        const promise = fetch(url).then(async (r) => {
          if (!r.ok) return null;
          return r.json();
        });
        sessionStateCache.set(url, { promise, data: cached && cached.data, at: (cached && cached.at) || 0 });
        d = await promise;
        if (d) sessionStateCache.set(url, { data: d, at: Date.now(), promise: null });
        else sessionStateCache.delete(url);
      }
      if (!d) return null;
      const responseSession = normalizeSessionName(d.session || sid) || sid;
      const currentSession = normalizeSessionName(w.ACTIVE_SESSION || '') || sid;
      const allowInactiveConversation = !!(
        opts && (opts.viewOnly || opts.allowInactiveConversation || opts.allow_inactive_conversation)
      );
      if (!allowInactiveConversation && currentSession !== sid && currentSession !== responseSession) {
        return d;
      }
      const appliedSession = responseSession === sid ? responseSession : sid;
      const todos = d.todos && Array.isArray(d.todos.todos) ? d.todos.todos : [];
      if (!allowInactiveConversation) {
        setActiveSessionName(appliedSession);
        w.TODOS = normalizeTodos(todos);
      }
      if (hydrateConversation) {
        const sessionDetail = { ...d, session: appliedSession };
        const conversationDetail = {
          messages: (d.conversation && d.conversation.messages) || [],
          session: appliedSession,
        };
        if (!allowInactiveConversation) {
          w.ATLAS_LAST_SESSION_STATE = sessionDetail;
          w.ATLAS_LAST_CONVERSATION = conversationDetail;
          window.dispatchEvent(new CustomEvent('atlas-session-loaded', { detail: sessionDetail }));
        }
        window.dispatchEvent(new CustomEvent('atlas-conversation-loaded', {
          detail: conversationDetail,
        }));
      }
      if (!allowInactiveConversation) {
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SESSION_STATE' }));
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'TODOS' }));
      }
      return d;
    } catch (e) {
      return null;
    }
  }

  function refreshActiveConversation(session?: unknown, opts: any = {}): Promise<any> {
    return refreshSessionState(session, true, {
      mode: 'conversation',
      limit: CHAT_SWITCH_LIMIT,
      ...(opts || {}),
    });
  }

  function activeWorkspaceSessionParam(): string {
    const explicit = normalizeSessionName(w.ATLAS_WORKSPACE_SESSION_ID || '');
    if (explicit) return explicit;
    const parts = normalizeSessionName(w.ACTIVE_SESSION || URL_ACTIVE_SESSION || '').split('/').filter(Boolean);
    return parts.length >= 4 ? parts[1] || '' : '';
  }

  function activeSessionParams(params: URLSearchParams): URLSearchParams {
    const activeSession = normalizeSessionName(w.ACTIVE_SESSION || URL_ACTIVE_SESSION || '');
    if (activeSession) params.set('session_id', activeSession);
    return params;
  }

  function workerSnapshotUrl(opts: any = {}): string {
    const params = new URLSearchParams();
    const activeOnly = opts.activeOnly !== false && opts.active_only !== false;
    if (activeOnly) params.set('active_only', '1');
    const ip = String(opts.ip || '').trim();
    if (ip && ip !== 'default') params.set('ip', ip);
    const workspaceSession = activeWorkspaceSessionParam();
    if (workspaceSession) params.set('workspace_session', workspaceSession);
    const query = params.toString();
    return `/api/orchestrator/workers${query ? `?${query}` : ''}`;
  }

  async function fetchWorkerSnapshot(opts: any = {}): Promise<any> {
    const url = workerSnapshotUrl(opts);
    const force = !!opts.force;
    const ttl = Number(opts.ttlMs || opts.ttl_ms || WORKER_SNAPSHOT_CACHE_MS);
    const now = Date.now();
    const cached = workerSnapshotCache.get(url);
    if (!force && cached && cached.promise) return cached.promise;
    if (!force && cached && cached.data && (now - cached.at) < ttl) return cached.data;
    const promise = fetch(url, { cache: 'no-store' }).then(async (r) => {
      if (!r.ok) throw new Error(`workers ${r.status}`);
      return r.json();
    });
    workerSnapshotCache.set(url, { promise, data: cached && cached.data, at: (cached && cached.at) || 0 });
    try {
      const data = await promise;
      workerSnapshotCache.set(url, { data, at: Date.now(), promise: null });
      return data;
    } catch (e) {
      workerSnapshotCache.delete(url);
      throw e;
    }
  }

  async function refreshFileTree(path?: unknown, opts?: any): Promise<void> {
    const activeSession = activeFileTreeSession();
    const activeIp = activeIpFromSession(activeSession) || activeIpFromSession();
    const reqPath = activeIp;
    if (!reqPath) {
      w.FILE_TREE = [];
      w.FILE_TREE_LOADING = false;
      w.FILE_TREE_ERROR = '';
      w.FILE_TREE_EMPTY_REASON = 'select_ip';
      w.FILE_TREE_TRUNCATED = false;
      w.FILE_TREE_LAST_REFRESH = 0;
      if (w.SCOPE_PATH) {
        w.SCOPE_PATH = '';
        try { localStorage.removeItem('atlasScopePath'); } catch (_) {}
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
      }
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
      return;
    }
    const quiet = !!(opts && opts.quiet && Array.isArray(w.FILE_TREE) && w.FILE_TREE.length);
    if (!quiet) {
      w.FILE_TREE_LOADING = true;
      w.FILE_TREE_ERROR = '';
      w.FILE_TREE_EMPTY_REASON = '';
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
    } else {
      w.FILE_TREE_ERROR = '';
      w.FILE_TREE_EMPTY_REASON = '';
    }
    // When the user has narrowed to a sub-scope we go recursive so the
    // panel shows every file inside, not just the top level. At the
    // project root we keep it shallow (94 top-level entries already
    // crowd the panel — sub-dirs are reachable by clicking in).
    // `opts.recursive=true` overrides this — used by the "expand all"
    // button to force a deep refresh even at root scope. opts.recursive
    // false keeps the auto behavior (avoids fighting against scope-narrowed
    // recursive defaults).
    let recursive = (reqPath && reqPath.length > 0) ? '&recursive=1' : '';
    if (opts && opts.recursive === true) recursive = '&recursive=1';
    try {
      const qs = new URLSearchParams({ path: reqPath });
      if (activeSession) qs.set('session_id', activeSession);
      if (recursive) qs.set('recursive', '1');
      const r = await fetch('/api/files?' + qs.toString(), {
        cache: 'no-store',
        credentials: 'include',
      });
      if (!r.ok) {
        let message = r.statusText || `HTTP ${r.status}`;
        try {
          const d = await r.json();
          message = d.error || d.detail || message;
        } catch (_) {}
        if (!quiet) w.FILE_TREE = [];
        w.FILE_TREE_ERROR = message;
        w.FILE_TREE_EMPTY_REASON = '';
        w.FILE_TREE_LOADING = false;
        w.FILE_TREE_LAST_REFRESH = Date.now();
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
        return;
      }
      const d = await r.json();
      if (Array.isArray(d.entries)) {
        // Trust backend canonical path (resolved + project-relative) so
        // UI scope cannot drift as "spi/spi/spi/..." from alias/symlink
        // clicks that still resolve to the same real directory.
        const canonicalScope = activeIp || normalizeScopePath(d.path || reqPath);
        if (canonicalScope !== w.SCOPE_PATH) {
          w.SCOPE_PATH = canonicalScope;
          try { localStorage.setItem('atlasScopePath', w.SCOPE_PATH); } catch (_) {}
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
        }
        w.FILE_TREE = d.entries.map((e: any) => asTreeNode(e, e.depth || 0));
        w.FILE_TREE_LAST_REFRESH = Date.now();
        w.FILE_TREE_TRUNCATED = !!d.truncated;
        w.FILE_TREE_ERROR = '';
        w.FILE_TREE_EMPTY_REASON = '';
        w.FILE_TREE_LOADING = false;
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
      }
    } catch (e: any) {
      if (!quiet) w.FILE_TREE = [];
      w.FILE_TREE_ERROR = String(e && e.message || e || 'file tree request failed');
      w.FILE_TREE_EMPTY_REASON = '';
      w.FILE_TREE_LOADING = false;
      w.FILE_TREE_LAST_REFRESH = Date.now();
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
    }
  }

  function invalidateSessionState(session?: unknown): void {
    const sid = normalizeSessionName(session || w.ACTIVE_SESSION || '');
    if (!sid) {
      sessionStateCache.clear();
      return;
    }
    const needle = 'session=' + encodeURIComponent(sid);
    for (const key of Array.from(sessionStateCache.keys())) {
      if (key.indexOf(needle) >= 0) sessionStateCache.delete(key);
    }
  }

  async function todoJsonRequest(url: string, opts: any = {}): Promise<any> {
    const r = await fetch(url, {
      ...(opts || {}),
      credentials: 'include',
    });
    let payload = null;
    let text = '';
    try {
      text = await r.text();
      payload = text ? JSON.parse(text) : {};
    } catch (_) {
      payload = null;
    }
    if (!r.ok || (payload && payload.error)) {
      const message = (payload && (payload.error || payload.detail))
        || text
        || r.statusText
        || `HTTP ${r.status}`;
      throw new Error(message);
    }
    return payload || {};
  }

  function applyTodoPayload(payload: any): void {
    if (payload && Array.isArray(payload.todos)) {
      w.TODOS = normalizeTodos(payload.todos);
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'TODOS' }));
    }
  }

  async function refreshTodosAfterMutation(session: unknown, payload: any): Promise<any> {
    applyTodoPayload(payload);
    invalidateSessionState(session);
    await refreshTodos({ force: true });
    return payload;
  }

  async function refreshTodos(opts: any = {}): Promise<void> {
    try {
      if (w.ACTIVE_SESSION) {
        const d = await refreshSessionState(w.ACTIVE_SESSION, false, { force: !!opts.force });
        if (d) return;
      }
      const query = w.ACTIVE_SESSION
        ? ('?session=' + encodeURIComponent(normalizeSessionName(w.ACTIVE_SESSION)))
        : '';
      const r = await fetch('/api/todos' + query, { cache: 'no-store' });
      if (!r.ok) return;
      const d = await r.json();
      // TodoTracker.to_dict() shape:
      //   {todos: [{content, activeForm, status, priority, detail, ...}]}
      // The TodoPanel UI expects {id, state, section, title, detail, deps}.
      // Pass the raw status through — workspace.jsx's stateCfg() already
      // handles all five (pending / in_progress / completed / approved /
      // rejected) plus the legacy 'done' / 'active' aliases. The previous
      // status2state map only covered completed→done and in_progress→
      // active, so 'approved' fell through `||` to 'pending' and the
      // sidebar showed ☐ for tasks the agent had already approved.
      w.TODOS = normalizeTodos(d.todos);
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'TODOS' }));
    } catch (e) { /* ignore */ }
  }

  async function refreshSlashCommands(): Promise<void> {
    try {
      const r = await fetch('/api/commands');
      if (!r.ok) return;
      const d = await r.json();
      const cmds = Array.isArray(d.commands) ? d.commands : [];
      if (cmds.length) {
        // Map the API shape ({cmd, name, aliases, hint, usage}) to the
        // shape workspace.jsx's slash dropdown expects. The renderer
        // reads BOTH .hint (mute footer) and .desc (in-line right
        // column), so populate both.
        const live = cmds.map((c: any) => ({
          cmd:   c.cmd,
          alias: (c.aliases && c.aliases[0]) || c.name.slice(0, 2),
          aliases: c.aliases || [],
          hint:  c.hint || '',
          desc:  c.hint || '',
          usage: c.usage || c.cmd,
        }));
        // Merge in the client-side commands (handled by workspace.jsx
        // before sending to the backend, so they never appear in
        // /api/commands but still need to show in autocomplete).
        const clientOnly = [
          { cmd: '/scope', alias: 'sc',
            hint: '(client) confine agent to a directory: /scope <path> | /scope / to clear',
            desc: '(client) confine agent to a directory: /scope <path> | /scope / to clear' },
          { cmd: '/cd',    alias: 'cd',
            hint: '(client) alias for /scope',
            desc: '(client) alias for /scope' },
          { cmd: '/session', alias: 'ss',
            hint: '(client) show or switch session: /session default',
            desc: '(client) show or switch session: /session default' },
          { cmd: '/pipeline', alias: 'pl',
            hint: '(client) dispatch full SSOT pipeline: /pipeline <ip>',
            desc: '(client) dispatch full SSOT pipeline: /pipeline <ip>' },
          { cmd: '/feedback', alias: 'fb',
            hint: '(client) send admin-visible feedback: /feedback <message>',
            desc: '(client) send admin-visible feedback: /feedback <message>',
            usage: '/feedback <message>' },
          { cmd: '/memory', alias: 'mem',
            hint: "show or edit this user's prompt memory rules",
            desc: "show or edit this user's prompt memory rules",
            usage: '/memory add <rule>' },
        ];
        const present = new Set(live.map((c: any) => c.cmd));
        for (const c of clientOnly) {
          if (!present.has(c.cmd)) live.push(c);
        }
        live.sort((a: any, b: any) => a.cmd.localeCompare(b.cmd));
        w.SLASH_COMMANDS = live;
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SLASH_COMMANDS' }));
      }
    } catch (e) { /* keep built-in fallbacks */ }
  }

  async function refreshSsotList(): Promise<void> {
    try {
      const qs = activeSessionParams(new URLSearchParams());
      const url = qs.toString() ? `/api/ssot?${qs.toString()}` : '/api/ssot';
      const r = await fetch(url, { cache: 'no-store', credentials: 'include' });
      if (!r.ok) return;
      const d = await r.json();
      w.SSOT_FILES = Array.isArray(d.files) ? d.files : [];
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SSOT_FILES' }));
    } catch (e) { /* ignore */ }
  }

  async function refreshProgress(): Promise<any> {
    try {
      const scope = w.SCOPE_PATH || '';
      const r = await fetch('/api/progress?scope=' + encodeURIComponent(scope));
      if (!r.ok) return;
      const d = await r.json();
      w.ATLAS_PROGRESS = d || null;
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'PROGRESS' }));
      return d;
    } catch (e) {
      return null;
    }
  }

  async function refreshHealth(): Promise<void> {
    try {
      const activeSession = normalizeSessionName(w.ACTIVE_SESSION || URL_ACTIVE_SESSION || '');
      const activeParts = activeSession.split('/').filter(Boolean);
      const activeWorkspaceSession = activeParts.length >= 4 ? activeParts[1] : '';
      const healthParams = new URLSearchParams();
      if (activeSession) healthParams.set('session_id', activeSession);
      if (activeWorkspaceSession) healthParams.set('workspace_session', activeWorkspaceSession);
      const healthQuery = healthParams.toString();
      const healthUrl = healthQuery ? `/healthz?${healthQuery}` : '/healthz';
      const r = await fetch(healthUrl);
      if (!r.ok) return;
      const d = await r.json();
      if (!healthMatchesCurrentUser(d)) return;
      // First-visit seed of the per-user session id. /healthz now
      // carries the IPv4-derived user_session, so we don't need a
      // separate /api/whoami round-trip on boot. Also seed
      // atlasActiveSession + window.ACTIVE_SESSION so the App
      // shell updates from "default" → "u-<ipv4>/default" on the
      // first render (the existing atlas-session-loaded listener
      // re-derives activeSessionId from the namespace).
      try {
        const stored = (localStorage.getItem('atlasUserSessionId') || '').trim();
        const serverUser = normalizeSessionName(d.user_session || '');
        const storedUser = normalizeSessionName(stored);
        // Migrate stale auto-generated `u-<base36>-<rand>` ids, and keep
        // browser-local owner state aligned with the authenticated user.
        const isLegacyRandom = /^u-[a-z0-9]{6,12}-[a-z0-9]{4,8}$/i.test(stored);
        const userChanged = !!(serverUser && storedUser && storedUser !== serverUser);
        const shouldSeed = !!(serverUser && (!storedUser || isLegacyRandom || userChanged));
        if (shouldSeed) {
          localStorage.setItem('atlasUserSessionId', serverUser);
          w.ATLAS_USER_SESSION_ID = serverUser;
          const storedNs = normalizeSessionName(localStorage.getItem('atlasActiveSession') || '');
          const liveNs = normalizeSessionName(w.ACTIVE_SESSION || '');
          const activeNs = normalizeSessionName(URL_ACTIVE_SESSION || liveNs || storedNs);
          const activeParts = activeNs.split('/').filter(Boolean);
          const activeOwner = activeParts[0] || '';
          const legacyNs = /^u-[a-z0-9]{6,12}-[a-z0-9]{4,8}(?:\/|$)/i.test(activeNs);
          const ownerMismatch = !!(activeOwner && activeOwner !== serverUser);
          if (!activeNs || activeNs === 'default' || legacyNs || ownerMismatch) {
            const serverNs = normalizeSessionName(d.active_session || '');
            const serverParts = serverNs.split('/').filter(Boolean);
            let tail: string[] = [];
            if ((legacyNs || ownerMismatch) && URL_ACTIVE_SESSION) {
              tail = activeParts.slice(1);
            } else if (serverParts[0] === serverUser) {
              tail = serverParts.slice(1);
            }
            if (tail.length < 3) tail = ['default', 'default', 'default'];
            const seedNs = [serverUser, ...tail.slice(0, 3)].join('/');
            localStorage.setItem('atlasActiveSession', seedNs);
            w.ACTIVE_SESSION = seedNs;
            window.dispatchEvent(new CustomEvent('atlas-session-loaded', {
              detail: { session: seedNs },
            }));
          } else if (storedNs !== activeNs) {
            localStorage.setItem('atlasActiveSession', activeNs);
          }
          if (userChanged && !URL_ACTIVE_SESSION) {
            w.SCOPE_PATH = '';
            localStorage.removeItem('atlasScopePath');
            window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
          }
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'USER_SESSION_ID' }));
        }
      } catch (_) {}
      const _prev = w.CONTEXT || {};
      const browserSession = normalizeSessionName(w.ACTIVE_SESSION || '');
      const healthSession = normalizeSessionName(d.active_session || '');
      const healthOverride = browserSessionOverridesHealth(d);
      const effectiveSession = healthOverride ? browserSession : (healthSession || browserSession);
      const acceptHealthCounters = healthCountersMatchBrowserRoute(d);
      const effectiveRoute = routeSessionInfo(effectiveSession);
      const effectiveParts = effectiveSession.split('/').filter(Boolean);
      const workspaceSession = normalizeSessionName(
        (effectiveParts.length >= 4 ? effectiveParts[1] : '') || d.workspace_session || ''
      );
      if (workspaceSession) {
        (w as any).ATLAS_WORKSPACE_SESSION_ID = workspaceSession;
        try { localStorage.setItem('atlasWorkspaceSessionId', workspaceSession); } catch (_) {}
      }
      const activeWorkflow = activeWorkflowFromSession(effectiveSession);
      const backendWorkspace = normalizeSessionName(d.workspace || '');
      if (typeof d.chat_feed_summary === 'boolean') {
        w.ATLAS_CHAT_FEED_SUMMARY = d.chat_feed_summary;
      }
      // Keep SCOPE_PATH aligned with the active namespace IP. During a fast
      // new-IP switch the browser namespace can be newer than /healthz for a
      // few ticks, so prefer the IP embedded in ACTIVE_SESSION and only fall
      // back to the backend IP when the browser has no real IP yet.
      const backendActiveIp = String(d.active_ip || '').trim();
      const browserActiveIp = activeIpFromSession();
      const routeActiveIp = effectiveRoute.ip || browserActiveIp || backendActiveIp;
      if (routeActiveIp && routeActiveIp !== 'default') {
        w.ACTIVE_IP = routeActiveIp;
      }
      if (routeActiveIp && routeActiveIp !== 'default' && routeActiveIp !== w.SCOPE_PATH) {
        w.SCOPE_PATH = routeActiveIp;
        try { localStorage.setItem('atlasScopePath', routeActiveIp); } catch (_) {}
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
      }
      const healthMetaApplies = !healthSession || !effectiveSession || healthSession === effectiveSession;
      if (healthMetaApplies) {
        w.ATLAS_DB_SESSION_ID = String(d.db_session_id || '').trim();
        w.ATLAS_SESSION_UID = String(d.session_uid || '').trim();
        w.ATLAS_SESSION_LABEL = String(d.session_label || '').trim();
      }
      const effectiveWorkspace = activeWorkflow || (healthOverride ? (_prev.workspace || '') : (backendWorkspace || ''));
      w.CONTEXT = Object.assign({}, _prev, {
        ...(() => {
          const nextActiveSession = String(effectiveSession || '').trim();
          const prevActiveSession = String(_prev.activeSession || '').trim();
          const prevRoute = routeSessionInfo(prevActiveSession);
          const prevIp = prevRoute.ip || String(_prev.costIp || '').trim();
          const scopeChanged = !!(nextActiveSession && prevActiveSession && nextActiveSession !== prevActiveSession);
          const rejectedDifferentIp = !!(
            !acceptHealthCounters
            && routeActiveIp
            && prevIp
            && prevIp !== routeActiveIp
          );
          const resetCounters = scopeChanged || rejectedDifferentIp;
          const keep = (value: any) => (resetCounters ? 0 : value);
          const stable = (key: string, value: any) => {
            if (!acceptHealthCounters) return keep(Number(_prev[key] || 0));
            const next = Number(value || 0);
            if (resetCounters) return next;
            const prev = Number(_prev[key] || 0);
            return Number.isFinite(next) ? Math.max(prev, next) : prev;
          };
          const live = (key: string, value: any) => {
            if (!acceptHealthCounters) return keep(Number(_prev[key] || 0));
            const next = Number(value || 0);
            return Number.isFinite(next) ? next : Number(_prev[key] || 0);
          };
          const routeCostScope = routeActiveIp ? 'user_ip' : '';
          const routeCostUser = effectiveRoute.owner || String(_prev.costUser || '').trim();
          const routeCostIp = routeActiveIp || '';
          return {
            tokens: (d.tokens != null) ? live('tokens', d.tokens) : keep(Number(_prev.tokens || 0)),
            tokensIn: (d.tokens_in != null) ? stable('tokensIn', d.tokens_in) : keep(Number(_prev.tokensIn || 0)),
            tokensCache: (d.tokens_cache != null) ? stable('tokensCache', d.tokens_cache) : keep(Number(_prev.tokensCache || 0)),
            tokensOut: (d.tokens_out != null) ? stable('tokensOut', d.tokens_out) : keep(Number(_prev.tokensOut || 0)),
            costUsd: (d.cost_usd != null) ? stable('costUsd', d.cost_usd) : keep(Number(_prev.costUsd || 0)),
            costScope: acceptHealthCounters ? (routeCostScope || d.cost_scope || _prev.costScope || '') : (routeCostScope || ''),
            costUser: acceptHealthCounters ? (routeCostUser || d.cost_user || _prev.costUser || '') : routeCostUser,
            costIp: acceptHealthCounters ? (routeCostIp || d.cost_ip || _prev.costIp || '') : routeCostIp,
            costCalls: acceptHealthCounters && d.cost_calls != null ? Number(d.cost_calls || 0) : keep(Number(_prev.costCalls || 0)),
          };
        })(),
        frontend:    d.frontend  || '',
        model:       d.model     || _prev.model || '—',
        baseModel:   d.base_model || '',
        baseUrl:     d.base_url   || '',
        provider:    d.provider   || '',
        reasoningEffort: d.reasoning_effort || '',
        modelOptions: Array.isArray(d.model_options) ? d.model_options : [],
        selectedModelKey: d.selected_model_key || '',
        activeSession: effectiveSession || '',
        dbSessionId: healthMetaApplies ? (d.db_session_id || '') : (_prev.dbSessionId || ''),
        sessionUid: healthMetaApplies ? (d.session_uid || '') : (_prev.sessionUid || ''),
        sessionLabel: healthMetaApplies ? (d.session_label || '') : (_prev.sessionLabel || ''),
        activeIp:      routeActiveIp || '',
        activeWorkflow: activeWorkflow || d.active_workflow || '',
        maxTokens:   d.max_context    || _prev.maxTokens || 0,
        iterMax:     d.max_iterations || _prev.iterMax    || 0,
        workspace:   effectiveWorkspace,
        projectRoot: d.project_root || '',
        cwd:         d.cwd || '',
        pricing:     d.pricing || null,    // {input, cache, output} USD/1M
        chatFeedSummary: w.ATLAS_CHAT_FEED_SUMMARY !== false,
      });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    } catch (e) { /* ignore */ }
  }

  async function refreshWorkflows(): Promise<void> {
    try {
      const r = await fetch('/api/workspaces');
      if (!r.ok) return;
      const d = await r.json();
      const items = Array.isArray(d.items) ? d.items : [];
      const byId = new Map(items.map((wsItem: any) => [wsItem.id, wsItem]));
      const live = DEFAULT_FLOW_STAGES
        .filter((p) => byId.has(p.id))
        .map((p) => {
          const wsItem: any = byId.get(p.id);
          return {
            id:    wsItem.id,
            label: wsItem.label || wsItem.name,
            cmd:   p.cmd,
            color: p.color,
            glyph: p.glyph,
          };
        });
      w.FLOW_STAGES = flowStagesForExecMode(live.length ? live : DEFAULT_FLOW_STAGES);
      const activeWorkflow = activeWorkflowFromSession();
      const backendActive = normalizeSessionName(d.active || '');
      w.CONTEXT.workspace = activeWorkflow || backendActive || '';
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FLOW_STAGES' }));
    } catch (e) { /* ignore */ }
  }

  return {
    setActiveSessionName,
    refreshSessionState,
    refreshActiveConversation,
    fetchWorkerSnapshot,
    refreshFileTree,
    invalidateSessionState,
    applyTodoPayload,
    refreshTodosAfterMutation,
    refreshTodos,
    refreshSlashCommands,
    refreshSsotList,
    refreshProgress,
    refreshHealth,
    refreshWorkflows,
    todoJsonRequest,
  };
}

// Re-export the helper used by data.tsx's session bootstrap so the main file
// has a single import surface for the loader layer's collaborators. (Pure
// re-export — no side effects.)
export { sessionPartsEndWithWorkflow, DEFAULT_WORKFLOW, KNOWN_WORKFLOWS };
