// data.tsx — TypeScript migration of data.jsx (strangler-fig). Live data
// bindings for the Atlas frontend.
//
// data.jsx was ONE IIFE of ORDERED side-effects:
//   - installs window.* seeds/defaults (SLASH_COMMANDS, FLOW_STAGES, FILE_TREE…),
//   - runs the lang/scope/user-session bootstrap off localStorage + the URL,
//   - defines the async API loaders + WS wiring,
//   - finally publishes window.atlasData and kicks off boot().
// Correctness of that execution ORDER beats aggressive splitting, so this
// migration keeps the SINGLE IIFE intact here and only pulls the
// side-effect-FREE clusters into siblings:
//   - data-helpers.tsx : pure helpers + constants (no closure state).
//   - data-loaders.tsx : the async loaders, packaged as a factory that
//                         closes over the SAME shared caches + URL const this
//                         file creates, then returns them. They are
//                         constructed at the exact point the originals were
//                         defined, so every window.* read/write still happens
//                         at call time in the original order.
//
// Replaces the original mock-data file. Every `window.*` global below is
// either an empty/safe default or is populated asynchronously from the
// real HTTP API exposed by src/atlas_ui.py:
//
//   GET /api/files?path=…   → real project file tree
//   GET /api/todos          → real TodoTracker state
//   GET /api/session/state  → scoped conversation/todo/cost/job state
//   GET /api/ssot           → list of *.ssot.yaml files (with ?file=… for content)
//
// Plus live updates pushed over the WS:
//   todo_line event → re-fetch /api/todos
//
// The `FLOW_STAGES` / `SLASH_COMMANDS` lists are real, agent-supported
// values (subset of the actual slash commands main.py recognizes).
//
// Transitional: still bridges to `window.*` so not-yet-migrated .jsx files
// (workspace.jsx, app.jsx) keep resolving window.atlasData /
// window.normalizeAtlasSessionName / window.SLASH_COMMANDS / … exactly as before.

import {
  DEFAULT_WORKFLOW,
  DEFAULT_FLOW_STAGES,
  flowStagesForExecMode,
  normalizeScopePath,
  createUserSessionId,
  normalizeSessionName,
  activeIpFromSession,
  sessionPartsEndWithWorkflow,
  KNOWN_WORKFLOWS,
  normalizeTodos,
  changedPathsFromToolResult,
  dispatchAtlasFileChanged,
  debounce,
} from './data-helpers';
import { createDataLoaders } from './data-loaders';

// Loosely-typed view of the window-global surface this file reads/writes that
// is NOT (yet) in types/atlas-window.d.ts. Mirrors preview-pane.tsx's pattern
// (`const g = window as unknown as …`). Keeps NAME-level safety where the
// shared ambient d.ts already covers a global, and avoids `(window as any)`
// sprinkled everywhere for the rest.
const w = window as any;

(function () {
  'use strict';

  // The AXI DMA screenshot-test fetch interceptor is loaded from
  // axi-dma-mock.jsx before these live data defaults.

  // ── Static defaults ─────────────────────────────────────────────
  // All of these are deliberately small/empty. workspace.jsx panels
  // that used to render mock content now render whatever the live
  // backend has, or nothing.

  // Slash commands — populated from /api/commands at boot. Until the
  // first fetch lands, seed with built-ins the agent always supports
  // plus the client-side ones (/scope, /cd, /session) workspace.jsx handles
  // locally without round-tripping to the backend.
  w.SLASH_COMMANDS = [
    { cmd: '/help',    alias: 'h',  hint: 'show available commands' },
    { cmd: '/clear',   alias: 'cl', hint: 'reset conversation' },
    { cmd: '/compact', alias: 'co', hint: 'compress history' },
    { cmd: '/exit',    alias: 'q',  hint: 'leave the session' },
    { cmd: '/todo',    alias: 't',  hint: 'show / manage todos' },
    { cmd: '/pipeline', alias: 'pl', hint: '(client) dispatch full SSOT pipeline: /pipeline <ip>' },
    { cmd: '/scope',   alias: 'sc', hint: '(client) confine agent to a directory: /scope <path>' },
    { cmd: '/cd',      alias: 'cd', hint: '(client) alias for /scope' },
    { cmd: '/session', alias: 'ss', hint: '(client) show or switch session: /session default' },
    { cmd: '/memory', alias: 'mem', hint: "show or edit this user's prompt memory rules" },
    { cmd: '/feedback', alias: 'fb', hint: '(client) send admin-visible feedback: /feedback <message>' },
  ];
  w.SLASH_COMMANDS_LOADING = false;
  w.SLASH_COMMANDS_ERROR = '';

  // Workflow stage badges. Seed the canonical IP flow immediately so the
  // left workflow rail is visible even before /api/workspaces returns.
  w.FLOW_STAGES = flowStagesForExecMode(DEFAULT_FLOW_STAGES);

  // Question flows for ask_user. Dynamic flows are pushed in by
  // workspace.jsx's `ask_user` WS subscription, so we only need an
  // empty seed here.
  w.QA_FLOWS = {};

  // Live-fetched data — initialized empty, refreshed on connect /
  // periodically thereafter. Each is a plain array/object; consumers
  // re-read it on every render so updates are picked up.
  w.FILE_TREE = [];
  w.FILE_TREE_LOADING = false;
  w.FILE_TREE_ERROR = '';
  w.FILE_TREE_EMPTY_REASON = 'select_ip';
  w.TODOS = [];
  w.SSOT_FILES = [];
  w.ATLAS_PROGRESS = null;
  try {
    const savedLang = localStorage.getItem('atlasUiLang');
    const explicitLang = localStorage.getItem('atlasUiLangUserSet') === '1';
    w.ATLAS_UI_LANG = explicitLang && savedLang === 'ko' ? 'ko' : 'en';
  } catch (_) {
    w.ATLAS_UI_LANG = w.ATLAS_UI_LANG || 'en';
  }

  try {
    w.SCOPE_PATH = normalizeScopePath(localStorage.getItem('atlasScopePath') || '');
  } catch (_) {
    w.SCOPE_PATH = '';
  }
  try {
    const params = new URLSearchParams(window.location.search || '');
    const urlSession = normalizeSessionName(params.get('session') || '');
    const urlParts = urlSession.split('/').filter(Boolean);
    const urlOwner = normalizeSessionName(
      (urlParts.length >= 3 ? urlParts[0] : '') || params.get('session_id') || ''
    );
    const urlWorkspace = normalizeSessionName(
      (urlParts.length >= 4 ? urlParts[1] : '') ||
      params.get('workspace_session') ||
      params.get('workspace') ||
      localStorage.getItem('atlasWorkspaceSessionId') ||
      ''
    );
    const urlIp = normalizeSessionName(
      (urlParts.length >= 3 ? urlParts[urlParts.length - 2] : '') ||
      params.get('ip') ||
      params.get('ip_id') ||
      ''
    );
    const urlWorkflow = normalizeSessionName(
      (urlParts.length >= 3 ? urlParts[urlParts.length - 1] : '') ||
      params.get('workflow') ||
      params.get('wf') ||
      ''
    );
    const urlNamespace = (urlSession && urlParts.length >= 4 ? urlSession : '') || (
      (urlIp || urlWorkflow)
        ? `${urlOwner || 'default'}/${urlWorkspace || 'default'}/${urlIp || 'default'}/${urlWorkflow || 'default'}`
        : ''
    );
    w.ACTIVE_SESSION = urlNamespace || normalizeSessionName(localStorage.getItem('atlasActiveSession')) || 'default';
    if (urlNamespace) {
      localStorage.setItem('atlasActiveSession', urlNamespace);
      localStorage.setItem('atlasWorkspaceSessionId', urlWorkspace || 'default');
      w.ATLAS_WORKSPACE_SESSION_ID = urlWorkspace || 'default';
    }
  } catch (_) {
    w.ACTIVE_SESSION = 'default';
  }

  // Status-bar metadata. Filled in by the /healthz response and the
  // first `cost`/`context` WS event.
  w.CONTEXT = {
    model: '—',
    iterMax: '—',
    rate: '—',
    tokens: 0,
    maxTokens: 0,
  };
  w.ATLAS_CHAT_FEED_SUMMARY = true;

  // Legacy globals retained as empty stubs so workspace.jsx never
  // crashes when it reads them. (Only used by mock-only panels.)
  w.WORKSPACES = [];
  w.ACTIVE_IP = null;
  w.RECENT_IPS = [];
  w.REACT_LOG = [];
  w.DIFF_LINES = [];
  w.LINT_FINDINGS = [];

  // normalizeSessionName is published for app.jsx / workspace.jsx. Keep this
  // bridge here (same position as the original) so consumers resolve it before
  // any of them run their own session bootstrap.
  w.normalizeAtlasSessionName = normalizeSessionName;

  function readUrlNamespace(): string {
    let params: URLSearchParams;
    try { params = new URLSearchParams(window.location.search || ''); }
    catch (_) { return ''; }
    const direct = normalizeSessionName(
      params.get('session') || params.get('sid') || params.get('namespace') || ''
    );
    if (direct && direct.includes('/')) {
      const directParts = direct.split('/').filter(Boolean);
      const directStoredOwner = (() => {
        try { return normalizeSessionName(localStorage.getItem('atlasUserSessionId')); }
        catch (_) { return ''; }
      })();
      const directStoredWorkspace = (() => {
        try { return normalizeSessionName(localStorage.getItem('atlasWorkspaceSessionId')); }
        catch (_) { return ''; }
      })();
      const directOwner = normalizeSessionName(
        params.get('session_id') || params.get('user_session') || params.get('owner') || directStoredOwner || w.ATLAS_USER_SESSION_ID || ''
      ) || 'default';
      const directWorkspace = normalizeSessionName(
        params.get('workspace_session') || params.get('workspace') || directStoredWorkspace || ''
      ) || 'default';
      if (directParts.length >= 4) return direct;
      if (directParts.length === 3) return `${directParts[0]}/${directWorkspace}/${directParts[1]}/${directParts[2]}`;
      if (directParts.length === 2) {
        const first = directParts[0] || DEFAULT_WORKFLOW;
        const second = directParts[1] || DEFAULT_WORKFLOW;
        if (KNOWN_WORKFLOWS.has(String(second).toLowerCase())) {
          return `${directOwner}/${directWorkspace}/${first}/${second}`;
        }
        return `${directOwner}/${directWorkspace}/${first}/${DEFAULT_WORKFLOW}`;
      }
    }
    const owner = normalizeSessionName(
      params.get('session_id') || params.get('user_session') || params.get('owner') || direct || ''
    );
    const ip = normalizeSessionName(params.get('ip') || params.get('ip_id') || '');
    const wf = normalizeSessionName(params.get('workflow') || params.get('wf') || '');
    const storedOwner = (() => {
      try { return normalizeSessionName(localStorage.getItem('atlasUserSessionId')); }
      catch (_) { return ''; }
    })();
    const storedWorkspace = (() => {
      try { return normalizeSessionName(localStorage.getItem('atlasWorkspaceSessionId')); }
      catch (_) { return ''; }
    })();
    const baseOwner = owner || storedOwner || normalizeSessionName(w.ATLAS_USER_SESSION_ID || '') || 'default';
    const baseWorkspace = normalizeSessionName(params.get('workspace_session') || params.get('workspace') || storedWorkspace) || 'default';
    if (ip && wf) return `${baseOwner}/${baseWorkspace}/${ip}/${wf}`;
    if (ip) return `${baseOwner}/${baseWorkspace}/${ip}/${DEFAULT_WORKFLOW}`;
    if (wf) return `${baseOwner}/${baseWorkspace}/${DEFAULT_WORKFLOW}/${wf}`;
    if (owner) return `${owner}/${baseWorkspace}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`;
    return '';
  }

  const URL_ACTIVE_SESSION = readUrlNamespace();

  // ── Shared request-coalescing caches + tuning constants ──────────
  // Created here (before the loader factory) so the async loaders capture the
  // exact same Map instances. Nothing reads them between this point and the
  // bootstrap below, so moving their creation a few lines earlier than the
  // original is behavior-neutral (they start empty either way).
  const SESSION_STATE_CACHE_MS = 1200;
  const CHAT_RECENT_LIMIT = 30;
  const CHAT_SWITCH_LIMIT = 80;
  const WORKER_SNAPSHOT_CACHE_MS = 1500;
  const sessionStateCache = new Map<string, any>();
  const workerSnapshotCache = new Map<string, any>();

  // Build the async loader layer. The returned closures are byte-for-byte
  // equivalent to the originals (same captured caches + URL const), and define
  // NO new window.* state until called — so the IIFE's ordered side-effects
  // are unchanged.
  const loaders = createDataLoaders({
    sessionStateCache,
    workerSnapshotCache,
    URL_ACTIVE_SESSION,
    SESSION_STATE_CACHE_MS,
    CHAT_RECENT_LIMIT,
    CHAT_SWITCH_LIMIT,
    WORKER_SNAPSHOT_CACHE_MS,
  });
  const {
    setActiveSessionName,
    refreshSessionState,
    refreshActiveConversation,
    fetchWorkerSnapshot,
    refreshFileTree,
    invalidateSessionState,
    refreshTodosAfterMutation,
    refreshTodos,
    refreshSlashCommands,
    refreshSsotList,
    refreshProgress,
    refreshHealth,
    refreshWorkflows,
    todoJsonRequest,
  } = loaders;

  // ── User-session id + active-session bootstrap ───────────────────
  try {
    let sid = normalizeSessionName(localStorage.getItem('atlasUserSessionId'));
    const urlOwner = (URL_ACTIVE_SESSION.split('/').filter(Boolean)[0] || '');
    if (urlOwner) {
      sid = urlOwner;
      localStorage.setItem('atlasUserSessionId', sid);
    }
    if (!sid || sid.includes('/')) {
      sid = createUserSessionId();
      localStorage.setItem('atlasUserSessionId', sid);
    }
    w.ATLAS_USER_SESSION_ID = sid;
  } catch (_) {
    w.ATLAS_USER_SESSION_ID = createUserSessionId();
  }
  try {
    const storedActive = URL_ACTIVE_SESSION || normalizeSessionName(localStorage.getItem('atlasActiveSession'));
    if (!storedActive || storedActive === 'default') {
      setActiveSessionName(`${w.ATLAS_USER_SESSION_ID}/default/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`);
    } else {
      const parts = storedActive.split('/').filter(Boolean);
      if (parts.length === 2 && String(parts[1] || '').toLowerCase() === DEFAULT_WORKFLOW) {
        setActiveSessionName(`${parts[0]}/default/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`);
      } else {
        const legacyIpWorkflow = parts.length === 2
          && String(parts[1] || '').toLowerCase() !== DEFAULT_WORKFLOW
          && KNOWN_WORKFLOWS.has(String(parts[1] || '').toLowerCase());
        const legacyWorkflow = parts.length === 1 && KNOWN_WORKFLOWS.has(String(parts[0] || '').toLowerCase());
        if (legacyIpWorkflow) {
          setActiveSessionName(`${w.ATLAS_USER_SESSION_ID}/default/${storedActive}`);
        } else if (legacyWorkflow) {
          setActiveSessionName(`${w.ATLAS_USER_SESSION_ID}/default/${DEFAULT_WORKFLOW}/${storedActive}`);
        } else {
          setActiveSessionName(storedActive);
        }
      }
    }
    const urlParts = (URL_ACTIVE_SESSION || '').split('/').filter(Boolean);
    if (urlParts.length >= 3 && sessionPartsEndWithWorkflow(urlParts)) {
      w.SCOPE_PATH = urlParts[urlParts.length - 2];
      try { localStorage.setItem('atlasScopePath', w.SCOPE_PATH); } catch (_) {}
    }
  } catch (_) {
    if (!w.ACTIVE_SESSION || w.ACTIVE_SESSION === 'default') {
      setActiveSessionName(`${w.ATLAS_USER_SESSION_ID}/default/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`);
    }
  }

  // sessionFor: pure namespace builder. Published via atlasData below. Kept in
  // this file because it depends only on pure helpers (no loader/cache state).
  function sessionFor(scopePath: unknown, workflow: unknown): string {
    let scope = normalizeSessionName(scopePath || '');
    const wf = normalizeSessionName(String(workflow || '').replace(/^\/+|\/+$/g, ''));
    const userSession = normalizeSessionName(w.ATLAS_USER_SESSION_ID || '') || '';
    const workspaceSession = normalizeSessionName((w as any).ATLAS_WORKSPACE_SESSION_ID || (() => {
      try { return localStorage.getItem('atlasWorkspaceSessionId') || ''; }
      catch (_) { return ''; }
    })()) || 'default';
    if (scope === 'default') scope = '';
    const scopeParts = scope.split('/').filter(Boolean);
    const joinSessionParts = (parts: string[]) => parts.filter(Boolean).join('/');
    const scopeEndsWithWorkflow = sessionPartsEndWithWorkflow(scopeParts);
    const scopeIsV2Namespace = scopeParts.length >= 4 && scopeEndsWithWorkflow;
    const scopeIsLegacyNamespace = scopeParts.length === 3 && scopeEndsWithWorkflow;
    const firstScopePart = scopeParts[0] || '';
    const scopeHasOwner = !!firstScopePart && (
      firstScopePart === userSession
      || /^u-[A-Za-z0-9_-]+$/.test(firstScopePart)
      || scopeIsV2Namespace
      || scopeIsLegacyNamespace
    );
    if (scopeHasOwner) {
      const owner = scopeParts[0] || userSession || 'default';
      if (wf) {
        if (scopeIsV2Namespace) {
          return joinSessionParts([...scopeParts.slice(0, -1), wf]);
        }
        if (scopeIsLegacyNamespace) {
          return joinSessionParts([owner, workspaceSession, scopeParts[1], wf]);
        }
        if (scopeParts.length <= 1 || scopeParts[1] === DEFAULT_WORKFLOW) {
          return joinSessionParts([owner, workspaceSession, DEFAULT_WORKFLOW, wf]);
        }
        return joinSessionParts([owner, workspaceSession, scopeParts[1], wf]);
      }
      if (scopeIsV2Namespace) return scope;
      if (scopeIsLegacyNamespace) return joinSessionParts([owner, workspaceSession, scopeParts[1], scopeParts[2]]);
      if (scopeParts[1] === DEFAULT_WORKFLOW) {
        return joinSessionParts([owner, workspaceSession, DEFAULT_WORKFLOW, DEFAULT_WORKFLOW]);
      }
      if (scopeParts.length === 1) return `${owner}/${workspaceSession}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`;
      return joinSessionParts([owner, workspaceSession, scopeParts[1], DEFAULT_WORKFLOW]);
    }
    if (wf && scope && scopeEndsWithWorkflow) {
      scope = scopeParts.slice(0, -1).join('/');
    } else if (!wf && userSession && scope && scopeEndsWithWorkflow) {
      return joinSessionParts([userSession, workspaceSession, DEFAULT_WORKFLOW, scope]);
    }
    // 'user' / 'soc' synthetic segments removed — they planted
    // confusing `.session/<owner>/user/...` and `.session/<owner>/soc/<wf>/...`
    // trees for ip-less / wf-less runs that aren't actually SoC or user-
    // owned. Use an explicit default IP/workflow segment for ip-less
    // or wf-less runs so the disk layout reads as the user expects.
    // Always at least 2 segments (owner + something) so the .session
    // tree never has a bare top-level workflow / IP dir like
    // .session/ssot-gen/ or .session/to/ that the user can't ratoionally
    // navigate. owner defaults to 'default' when no per-user session
    // is set (multi-user mode is opt-in via ATLAS_MULTI_USER).
    const owner = userSession || 'default';
    if (scope && wf) return `${owner}/${workspaceSession}/${scope}/${wf}`;
    if (scope)      return `${owner}/${workspaceSession}/${scope}/${DEFAULT_WORKFLOW}`;
    if (wf)         return `${owner}/${workspaceSession}/${DEFAULT_WORKFLOW}/${wf}`;
    return `${owner}/${workspaceSession}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`;
  }

  // Public API for workspace.jsx so it can pull a fresh slice on demand.
  w.atlasData = {
    refreshFileTree, refreshTodos, refreshSsotList, refreshHealth,
    refreshSlashCommands, refreshWorkflows, refreshSessionState, refreshActiveConversation,
    fetchWorkerSnapshot, sessionFor, refreshProgress, normalizeSessionName,
    refreshWorkflowStagesForPolicy: () => {
      w.FLOW_STAGES = flowStagesForExecMode(w.FLOW_STAGES || DEFAULT_FLOW_STAGES);
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FLOW_STAGES' }));
    },
    setUserSessionId: (sessionId: unknown) => {
      const sid = normalizeSessionName(sessionId);
      if (!sid || sid.includes('/')) return w.ATLAS_USER_SESSION_ID || '';
      w.ATLAS_USER_SESSION_ID = sid;
      try { localStorage.setItem('atlasUserSessionId', sid); } catch (_) {}
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'USER_SESSION_ID' }));
      return sid;
    },
    clearTodos: () => {
      const session = normalizeSessionName(w.ACTIVE_SESSION || '');
      return todoJsonRequest('/api/todos/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session }),
      }).then((payload: any) => refreshTodosAfterMutation(session, payload));
    },
    addTodo: (fields: any) => {
      const session = normalizeSessionName(w.ACTIVE_SESSION || '');
      return todoJsonRequest('/api/todos/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session, ...(fields || {}) }),
      }).then((payload: any) => refreshTodosAfterMutation(session, payload));
    },
    updateTodo: (index: any, fields: any) => {
      const session = normalizeSessionName(w.ACTIVE_SESSION || '');
      return todoJsonRequest('/api/todos/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session, index, ...(fields || {}) }),
      }).then((payload: any) => refreshTodosAfterMutation(session, payload));
    },
    removeTodo: (index: any) => {
      const session = normalizeSessionName(w.ACTIVE_SESSION || '');
      return todoJsonRequest('/api/todos/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session, index }),
      }).then((payload: any) => refreshTodosAfterMutation(session, payload));
    },
    fetchFile: (path: string) => {
      const params = new URLSearchParams({ path });
      const session = normalizeSessionName(w.ACTIVE_SESSION || '');
      if (session) params.set('session_id', session);
      return fetch('/api/file?' + params.toString(), { credentials: 'include' }).then(r => r.json());
    },
    fetchSsot: (path: string) => {
      const params = new URLSearchParams({ file: path });
      const session = normalizeSessionName(w.ACTIVE_SESSION || '');
      if (session) params.set('session_id', session);
      return fetch('/api/ssot?' + params.toString(), { credentials: 'include' }).then(r => r.json());
    },
    setScopePath: (p: unknown) => {
      let next = normalizeScopePath(p || '');
      if (next === DEFAULT_WORKFLOW) next = '';
      // Scope is no longer user-browsable: the left file tree is always
      // rooted at the active IP. The IP_ID dropdown is the only control
      // that changes this root; folder clicks only fold/unfold locally.
      const activeIp = activeIpFromSession(w.ACTIVE_SESSION || '');
      if (activeIp) {
        next = activeIp;
      } else {
        next = '';
      }
      if (next === w.SCOPE_PATH) {
        if (!activeIp) refreshFileTree('', { recursive: true });
        return;
      }
      w.SCOPE_PATH = next;
      try {
        if (w.SCOPE_PATH) localStorage.setItem('atlasScopePath', w.SCOPE_PATH);
        else localStorage.removeItem('atlasScopePath');
      } catch (_) {}
      // Re-fetch the IP-rooted tree so folder clicks can fold/unfold locally.
      refreshFileTree(w.SCOPE_PATH, { recursive: true });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
    },
    setActiveSession: (session: unknown) => {
      const sid = setActiveSessionName(session);
      return refreshActiveConversation(sid);
    },
  };

  window.addEventListener('atlas-run-policy-changed', () => {
    w.FLOW_STAGES = flowStagesForExecMode(w.FLOW_STAGES || DEFAULT_FLOW_STAGES);
    window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FLOW_STAGES' }));
  });

  // ── Bootstrap ───────────────────────────────────────────────────
  const _refFiles = debounce(() => refreshFileTree(w.SCOPE_PATH || '', { quiet: true }), 250);
  const _refSsot  = debounce(refreshSsotList, 250);
  const _refTodos = debounce(refreshTodos, 250);

  async function boot() {
    // /healthz carries `user_session` derived from the requesting
    // IPv4. Awaiting it first guarantees ATLAS_USER_SESSION_ID is
    // populated before any other fetch fires off, so downstream
    // session-aware calls don't race the seed.
    await refreshHealth();
    refreshFileTree(w.SCOPE_PATH || '');
    refreshTodos();
    refreshSsotList();
    refreshProgress();
    refreshSlashCommands();
    refreshWorkflows();
    // Hook the WS pubsub once it's available so todo_line events trigger
    // a fresh /api/todos fetch (the lines are ANSI-formatted strings; the
    // structured todo state lives behind the API).
    function attach() {
      if (!w.backend || typeof w.backend.subscribe !== 'function') {
        setTimeout(attach, 200);
        return;
      }
      const eventMatchesActiveSession = (m: any, opts: any = {}) => {
        const eventSession = normalizeSessionName(
          (m && (m.session_id || m.session || m.namespace)) || ''
        );
        const activeSession = normalizeSessionName(
          w.ACTIVE_SESSION
          || (w.CONTEXT && (w.CONTEXT.activeSession || w.CONTEXT.active_session))
          || ''
        );
        if (!activeSession) return !opts.requireSession;
        if (!eventSession) return !opts.requireSession;
        return eventSession === activeSession;
      };
      const eventMatchesActiveCostScope = (m: any) => {
        if (eventMatchesActiveSession(m, { requireSession: true })) return true;
        const ctx = w.CONTEXT || {};
        if (ctx.costScope !== 'user_ip') return false;
        const eventSession = normalizeSessionName(
          (m && (m.session_id || m.session || m.namespace)) || ''
        );
        const parts = eventSession.split('/').filter(Boolean);
        if (parts.length < 3) return false;
        const owner = parts[0] || '';
        const ip = parts[parts.length - 2] || '';
        return !!(
          ip
          && ip === String(ctx.costIp || ctx.activeIp || '').trim()
          && (!ctx.costUser || owner === ctx.costUser)
        );
      };
      // 'hello' fires on every WS connect (initial + every reconnect
      // after a transient drop). Re-run /healthz so the UI's session/
      // ip/workflow chips and URL params re-sync to whatever the
      // server now reports — without this, a brief WS drop left the
      // browser cached on the OLD triple while the backend may have
      // pivoted to a new IP via /ip / /session / /wf during the gap.
      w.backend.subscribe('hello', () => {
        refreshHealth().then(() => {
          // /healthz lands → CONTEXT.active_session is fresh →
          // syncCurrent in app.jsx will pull the URL into line via
          // its atlas-data-changed listener.
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
        }).catch(() => {});
        refreshSlashCommands();
        refreshWorkflows();
      });
      w.backend.subscribe('todo_line', (m: any) => {
        if (!eventMatchesActiveSession(m, { requireSession: true })) return;
        const raw = Array.isArray(m && m.todos)
          ? m.todos
          : (m && m.todo_state && Array.isArray(m.todo_state.todos) ? m.todo_state.todos : null);
        if (raw) {
          w.TODOS = normalizeTodos(raw);
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'TODOS' }));
        }
        setTimeout(refreshTodos, 300);
      });
      w.backend.subscribe('tool_result', (m: any) => {
        if (!eventMatchesActiveSession(m, { requireSession: true })) return;
        // Coalesce into one fetch per ~250 ms — see _refFiles etc.
        _refFiles(); _refSsot(); _refTodos();
        refreshProgress();
        // Some runtimes only emit tool_result for write/replace tools,
        // without the richer file_changed event. Derive the touched path
        // here as a backup so open previews reload immediately.
        const tool = (m && m.tool) || '';
        const text = (m && (m.text || m.content)) || '';
        changedPathsFromToolResult(tool, text)
          .forEach(path => dispatchAtlasFileChanged(path, tool));
      });
      // file_changed — backend fires this immediately after a
      // write/replace/edit tool call. Refresh file-tree + ssot list
      // and broadcast a window event so the open preview pane /
      // full SSOT view can self-reload if they were viewing this path.
      w.backend.subscribe('file_changed', (m: any) => {
        if (!eventMatchesActiveSession(m, { requireSession: true })) return;
        _refFiles(); _refSsot();
        const paths = Array.isArray(m && m.paths)
          ? m.paths
          : ((m && m.path) ? [m.path] : []);
        paths.forEach((path: any) => dispatchAtlasFileChanged(String(path || ''), (m && m.tool) || ''));
      });
      w.backend.subscribe('context', (m: any) => {
        if (!eventMatchesActiveSession(m, { requireSession: true })) return;
        let changed = false;
        if (typeof m.used === 'number') {
          const used = Number(m.used);
          const maxTokens = Number(m.max || 0);
          if (Number.isFinite(used) && (used > 0 || m.reset === true || m.clear === true)) {
            w.CONTEXT.tokens = Math.max(0, used);
            changed = true;
          }
          if (Number.isFinite(maxTokens) && maxTokens > 0) {
            w.CONTEXT.maxTokens = maxTokens;
            changed = true;
          }
        }
        const reasoningEffort = m.reasoning_effort || m.reasoningEffort || m.effort;
        const model = m.model || m.active_model || m.activeModel || m.runtime_model;
        if (reasoningEffort) {
          w.CONTEXT.reasoningEffort = reasoningEffort;
          changed = true;
        }
        if (model) {
          w.CONTEXT.model = model;
          changed = true;
        }
        if (Array.isArray(m.model_options)) {
          w.CONTEXT.modelOptions = m.model_options;
          changed = true;
        }
        if (m.selected_model_key) {
          w.CONTEXT.selectedModelKey = m.selected_model_key;
          changed = true;
        }
        if (changed) window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
      });
      // Live cost — agent fires per-LLM-call. We accumulate into CONTEXT
      // so the sidebar reflects spend without waiting for the 5 s poll.
      w.backend.subscribe('cost', (m: any) => {
        if (!eventMatchesActiveCostScope(m)) return;
        const ctx = w.CONTEXT;
        ctx.tokensIn    = (ctx.tokensIn    || 0) + (m.input  || 0);
        ctx.tokensCache = (ctx.tokensCache || 0) + (m.cached || 0);
        ctx.tokensOut   = (ctx.tokensOut   || 0) + (m.output || 0);
        const promptTokens = Number(m.context_used ?? m.used ?? m.input ?? 0);
        if (promptTokens > 0) ctx.tokens = promptTokens;
        const maxTokens = Number(m.max || m.max_context || m.maxTokens || 0);
        if (maxTokens > 0) ctx.maxTokens = maxTokens;
        // Backend now resolves pricing at LLM-call time (honors
        // LLM_BASE_NAME env) and ships both the USD delta and the pricing
        // it used. Prefer those over the page-load pricing snapshot so the
        // sidebar reflects the actual model in use right now.
        if (m.pricing) ctx.pricing = m.pricing;
        if (m.model)   ctx.model   = m.model;
        if (typeof m.cost_usd_delta === 'number' && !isNaN(m.cost_usd_delta)) {
          ctx.costUsd = (ctx.costUsd || 0) + m.cost_usd_delta;
        } else if (ctx.pricing) {
          // Fallback for older backends that don't ship cost_usd_delta:
          // recompute from cumulative tokens. m.input is total prompt
          // tokens and includes the cached subset, so charge only the
          // uncached slice at the input rate.
          const billableInput = Math.max(0, (ctx.tokensIn || 0) - (ctx.tokensCache || 0));
          ctx.costUsd =
            (billableInput   * ctx.pricing.input  +
             ctx.tokensCache * ctx.pricing.cache  +
             ctx.tokensOut   * ctx.pricing.output) / 1_000_000;
        }
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'COST' }));
      });
      // /wf <name> swaps the slash registry on the server — re-fetch.
      // NOTE: backend currently emits 'commands_changed' on EVERY flush
      // (per-iteration), not just on workspace switch. We dedupe at this
      // layer by tracking the last-seen workspace name and only running
      // the heavy hydrate (conversation replay) when it actually
      // changed. Re-firing the conversation fetch per-iteration was
      // wiping the live feed under the hydrated snapshot — the chat
      // appeared to lose messages.
      let _lastWs: string | null = null;
      // Single hydrate path: dedup on workspace name so we don't
      // clobber the live feed every flush, but DO fire on initial
      // attach (the server's `commands_changed` only emits on flush
      // — without an explicit kickoff, a fresh page load shows an
      // empty chat until the user sends something).
      const _maybeHydrateConversation = () => {
        return refreshHealth().then(() => {
          const ws = (w.CONTEXT && w.CONTEXT.workspace) || '';
          const sid = normalizeSessionName(w.ACTIVE_SESSION || '') || sessionFor(w.SCOPE_PATH || '', ws);
          if (sid === _lastWs) return;
          _lastWs = sid;
          return refreshActiveConversation(sid);
        });
      };
      w.backend.subscribe('commands_changed', () => {
        refreshSlashCommands();
        refreshTodos();
        refreshSsotList();
        refreshWorkflows();
        refreshProgress();
        _maybeHydrateConversation();
      });
      // Initial-load hydrate: kick off once now so a fresh page open
      // already shows the previous conversation instead of waiting for
      // the first agent turn to fire `commands_changed`.
      _maybeHydrateConversation();
      // Every flush (end of a slash result, end of an iteration's tokens)
      // is a cheap excuse to resync state so /todo clear, /clear, etc.
      // reflect immediately instead of waiting for the next 5 s poll.
      w.backend.subscribe('flush', (m: any) => {
        if (!eventMatchesActiveSession(m, { requireSession: true })) return;
        refreshTodos();
        refreshProgress();
      });
    }
    attach();
    // Belt-and-suspenders polling: every 5 s, refresh the file tree,
    // todo state, and SSOT list at the current scope. Catches any case where a
    // tool_result event was missed (UI was loading, WS dropped, etc.)
    // and keeps the timestamp footer ticking.
    // Belt-and-suspenders polling. WS events drive the panels in
    // realtime, so this loop only catches the rare missed event. The
    // old 5-second tick fired four fetches per cycle on every tab,
    // contributing meaningfully to the "frontend feels slow" symptom
    // because each fetch races against the WS-driven refresh and
    // re-runs the same React render cycle. Pull it out to 30 s and
    // skip when the tab is hidden — there's nothing to update on a
    // backgrounded tab anyway.
    setInterval(() => {
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
      refreshFileTree(w.SCOPE_PATH || '', { quiet: true });
      refreshTodos();
      refreshSsotList();
      refreshProgress();
    }, 30000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
