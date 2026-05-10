// data.jsx — live data bindings for the Atlas frontend.
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

(function () {
  'use strict';

  // ── localStorage gate (per user request) ─────────────────────────
  // Session/IP/scope state must NOT survive a page reload — every
  // boot is anchored to the backend's PROJECT_ROOT scan instead. This
  // monkey-patch on Storage.prototype intercepts every call site
  // (workspace.jsx, app.jsx, data.jsx) at once so we don't have to
  // chase down every getItem/setItem individually. UI prefs (font,
  // language, theme) still persist normally.
  try {
    const _BLOCKED_LS_KEYS = new Set([
      'atlasActiveSession', 'atlasUserSessionId', 'atlasScopePath',
    ]);
    const _origGet = Storage.prototype.getItem;
    const _origSet = Storage.prototype.setItem;
    Storage.prototype.getItem = function (k) {
      if (_BLOCKED_LS_KEYS.has(k)) return null;
      return _origGet.call(this, k);
    };
    Storage.prototype.setItem = function (k, v) {
      if (_BLOCKED_LS_KEYS.has(k)) return;
      _origSet.call(this, k, v);
    };
    // Clear any pre-existing stale entries so a one-time migration
    // happens on the very first reload after this lands.
    for (const k of _BLOCKED_LS_KEYS) {
      try { _origSet.call(localStorage, k, null); localStorage.removeItem(k); } catch (_) {}
    }
  } catch (_) {}

  // ── Static defaults ─────────────────────────────────────────────
  // All of these are deliberately small/empty. workspace.jsx panels
  // that used to render mock content now render whatever the live
  // backend has, or nothing.

  // Slash commands — populated from /api/commands at boot. Until the
  // first fetch lands, seed with built-ins the agent always supports
  // plus the client-side ones (/scope, /cd, /session) workspace.jsx handles
  // locally without round-tripping to the backend.
  window.SLASH_COMMANDS = [
    { cmd: '/help',    alias: 'h',  hint: 'show available commands' },
    { cmd: '/clear',   alias: 'cl', hint: 'reset conversation' },
    { cmd: '/compact', alias: 'co', hint: 'compress history' },
    { cmd: '/exit',    alias: 'q',  hint: 'leave the session' },
    { cmd: '/todo',    alias: 't',  hint: 'show / manage todos' },
    { cmd: '/scope',   alias: 'sc', hint: '(client) confine agent to a directory: /scope <path>' },
    { cmd: '/cd',      alias: 'cd', hint: '(client) alias for /scope' },
    { cmd: '/session', alias: 'ss', hint: '(client) show or switch session: /session default' },
  ];

  const DEFAULT_FLOW_STAGES = [
    { id: 'ssot-gen',     label: 'ssot-gen',     cmd: '/wf ssot-gen',     color: 'var(--mag)',    glyph: 'SS' },
    { id: 'fl-model-gen', label: 'fl-model-gen', cmd: '/wf fl-model-gen', color: 'var(--cyan)',   glyph: 'FL' },
    { id: 'rtl-gen',      label: 'rtl-gen',      cmd: '/wf rtl-gen',      color: 'var(--accent)', glyph: 'RT' },
    { id: 'tb-gen',       label: 'tb-gen',       cmd: '/wf tb-gen',       color: 'var(--ok)',     glyph: 'TB' },
    { id: 'sim_debug',    label: 'sim_debug',    cmd: '/wf sim_debug',    color: 'var(--warn)',   glyph: 'DB' },
    { id: 'lint',         label: 'lint',         cmd: '/wf lint',         color: 'var(--err)',    glyph: 'LT' },
    { id: 'coverage',     label: 'coverage',     cmd: '/wf coverage',     color: 'var(--cyan)',   glyph: 'CV' },
    { id: 'syn',          label: 'syn',          cmd: '/wf syn',          color: 'var(--accent)', glyph: 'SY' },
    { id: 'sta',          label: 'sta',          cmd: '/wf sta',          color: 'var(--mag)',    glyph: 'ST' },
    { id: 'pnr',          label: 'pnr',          cmd: '/wf pnr',          color: 'var(--ok)',     glyph: 'PR' },
  ];

  // Workflow stage badges. Seed the canonical IP flow immediately so the
  // left workflow rail is visible even before /api/workspaces returns.
  window.FLOW_STAGES = DEFAULT_FLOW_STAGES.slice();

  // Question flows for ask_user. Dynamic flows are pushed in by
  // workspace.jsx's `ask_user` WS subscription, so we only need an
  // empty seed here.
  window.QA_FLOWS = {};

  // Live-fetched data — initialized empty, refreshed on connect /
  // periodically thereafter. Each is a plain array/object; consumers
  // re-read it on every render so updates are picked up.
  window.FILE_TREE = [];
  window.TODOS = [];
  window.SSOT_FILES = [];
  window.ATLAS_PROGRESS = null;
  try {
    const savedLang = localStorage.getItem('atlasUiLang');
    const explicitLang = localStorage.getItem('atlasUiLangUserSet') === '1';
    window.ATLAS_UI_LANG = explicitLang && savedLang === 'ko' ? 'ko' : 'en';
  } catch (_) {
    window.ATLAS_UI_LANG = window.ATLAS_UI_LANG || 'en';
  }

  // Scope path: agent is asked (via prompt prefix) to keep all reads,
  // writes, and tool calls confined to this directory. Empty string =
  // whole project root. Persists across reloads via localStorage.
  function normalizeScopePath(raw) {
    const src = String(raw ?? '').trim().replace(/\\/g, '/');
    if (!src || src === '/') return '';
    const out = [];
    src.split('/').forEach((part) => {
      const seg = String(part || '').trim();
      if (!seg || seg === '.') return;
      if (seg === '..') {
        out.pop();
        return;
      }
      out.push(seg);
    });
    return out.join('/');
  }

  function createUserSessionId() {
    const stamp = Date.now().toString(36);
    const rand = Math.random().toString(36).slice(2, 8);
    return `u-${stamp}-${rand}`;
  }

  try {
    window.SCOPE_PATH = normalizeScopePath(localStorage.getItem('atlasScopePath') || '');
  } catch (_) {
    window.SCOPE_PATH = '';
  }
  try {
    window.ACTIVE_SESSION = normalizeSessionName(localStorage.getItem('atlasActiveSession')) || 'default';
  } catch (_) {
    window.ACTIVE_SESSION = 'default';
  }

  // Status-bar metadata. Filled in by the /healthz response and the
  // first `cost`/`context` WS event.
  window.CONTEXT = {
    model: '—',
    iterMax: '—',
    rate: '—',
    tokens: 0,
    maxTokens: 0,
  };
  window.ATLAS_CHAT_FEED_SUMMARY = true;

  // Legacy globals retained as empty stubs so workspace.jsx never
  // crashes when it reads them. (Only used by mock-only panels.)
  window.WORKSPACES = [];
  window.ACTIVE_IP = null;
  window.RECENT_IPS = [];
  window.REACT_LOG = [];
  window.DIFF_LINES = [];
  window.LINT_FINDINGS = [];

  // ── Live loaders ────────────────────────────────────────────────
  // FILE_TREE entry shape (matches what workspace.jsx renders):
  //   { type: 'dir'|'file', name, size, depth, expanded, dim, active }
  function fmtSize(bytes) {
    if (!bytes) return '';
    if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    if (bytes >= 1024)        return (bytes / 1024).toFixed(1) + ' KB';
    return bytes + ' B';
  }

  function normalizeTodoListField(value) {
    if (Array.isArray(value)) {
      return value.map(v => String(v ?? '').trim()).filter(Boolean);
    }
    const s = String(value ?? '').trim();
    if (!s) return [];
    return s.split(/\r?\n+/).map(line => line.trim()).filter(Boolean);
  }

  function normalizeTodos(rawTodos) {
    return (Array.isArray(rawTodos) ? rawTodos : []).map((t, i) => ({
      id:      t.id ? String(t.id) : `t${i + 1}`,
      state:   t.status || 'pending',
      section: t.priority ? String(t.priority).toUpperCase() : '',
      title:   t.content || '',
      detail:  t.detail || '',
      criteria: normalizeTodoListField(t.criteria || t.acceptance_criteria),
      sourceRefs: normalizeTodoListField(t.source_refs || t.sourceRefs || t.references),
      ownerModule: String(t.owner_module || t.ownerModule || '').trim(),
      ownerFile: String(t.owner_file || t.ownerFile || '').trim(),
      required: t.required,
      approvedReason: t.approved_reason || '',
      rejectionReason: t.rejection_reason || '',
      notes:   Array.isArray(t.notes) ? t.notes : [],
      deps:    Array.isArray(t.deps) ? t.deps : [],
    }));
  }

  const KNOWN_WORKFLOWS = new Set([
    'architect',
    'coverage',
    'fl-model-gen',
    'goal-audit',
    'lint',
    'mas-gen',
    'rtl-gen',
    'signoff',
    'sim',
    'sim_debug',
    'ssot-gen',
    'tb-gen',
  ]);

  const KNOWN_SESSION_FILES = new Set([
    'conversation.json',
    'full_conversation.json',
    'todo.json',
    'todo_error.json',
    'cost.json',
    'state.json',
    'qa.json',
    'result.json',
  ]);

  function normalizeSessionName(value) {
    const raw = String(value || '').trim().replace(/^["']|["']$/g, '');
    if (!raw) return '';
    const pathish = raw.includes('\\') || raw.includes(':') || raw.startsWith('/') ||
      raw.startsWith('~') || raw.startsWith('.session');
    let parts = raw.replace(/\\/g, '/').replace(/^\/+|\/+$/g, '')
      .split('/')
      .filter(p => p && p !== '.');
    if (!parts.length) return '';
    const lower = parts.map(p => p.toLowerCase());
    const idx = lower.lastIndexOf('.session');
    const hadSessionMarker = idx >= 0;
    if (idx >= 0) parts = parts.slice(idx + 1);
    else if (/^[A-Za-z]:$/.test(parts[0])) {
      parts = parts.slice(1);
      if (parts.length > 2) parts = parts.slice(-2);
    }
    if (parts.length && KNOWN_SESSION_FILES.has(String(parts[parts.length - 1]).toLowerCase())) {
      parts = parts.slice(0, -1);
    }
    if (!parts.length) return '';
    if (
      parts.length > 2 &&
      KNOWN_WORKFLOWS.has(String(parts[parts.length - 1]).toLowerCase()) &&
      ((pathish && !hadSessionMarker) || parts.length > 3)
    ) {
      parts = parts.slice(-2);
    }
    for (const part of parts) {
      if (part === '..' || part.includes(':') || !/^[A-Za-z0-9_.-]+$/.test(part)) return '';
    }
    return parts.join('/');
  }
  window.normalizeAtlasSessionName = normalizeSessionName;

  function readUrlNamespace() {
    let params;
    try { params = new URLSearchParams(window.location.search || ''); }
    catch (_) { return ''; }
    const direct = normalizeSessionName(
      params.get('session') || params.get('sid') || params.get('namespace') || ''
    );
    if (direct && direct.includes('/')) return direct;
    const owner = normalizeSessionName(
      params.get('session_id') || params.get('user_session') || params.get('owner') || direct || ''
    );
    const ip = normalizeSessionName(params.get('ip') || params.get('ip_id') || '');
    const wf = normalizeSessionName(params.get('workflow') || params.get('wf') || '');
    const storedOwner = (() => {
      try { return normalizeSessionName(localStorage.getItem('atlasUserSessionId')); }
      catch (_) { return ''; }
    })();
    const baseOwner = owner || storedOwner || normalizeSessionName(window.ATLAS_USER_SESSION_ID || '') || 'default';
    if (ip && wf) return `${baseOwner}/${ip}/${wf}`;
    if (ip) return `${baseOwner}/${ip}/default`;
    if (wf) return `${baseOwner}/${wf}`;
    if (owner) return `${owner}/default`;
    return '';
  }

  const URL_ACTIVE_SESSION = readUrlNamespace();

  function sessionPartsEndWithWorkflow(parts) {
    const last = String(parts[parts.length - 1] || '').toLowerCase();
    return KNOWN_WORKFLOWS.has(last);
  }

  function setActiveSessionName(session) {
    const sid = normalizeSessionName(session) || 'default';
    window.ACTIVE_SESSION = sid;
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    return sid;
  }

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
    window.ATLAS_USER_SESSION_ID = sid;
  } catch (_) {
    window.ATLAS_USER_SESSION_ID = createUserSessionId();
  }
  try {
    const storedActive = URL_ACTIVE_SESSION || normalizeSessionName(localStorage.getItem('atlasActiveSession'));
    if (!storedActive || storedActive === 'default') {
      setActiveSessionName(`${window.ATLAS_USER_SESSION_ID}/default`);
    } else {
      const parts = storedActive.split('/').filter(Boolean);
      const legacyIpWorkflow = parts.length === 2 && KNOWN_WORKFLOWS.has(String(parts[1] || '').toLowerCase());
      const legacyWorkflow = parts.length === 1 && KNOWN_WORKFLOWS.has(String(parts[0] || '').toLowerCase());
      if (legacyIpWorkflow) {
        setActiveSessionName(`${window.ATLAS_USER_SESSION_ID}/${storedActive}`);
      } else if (legacyWorkflow) {
        setActiveSessionName(`${window.ATLAS_USER_SESSION_ID}/soc/${storedActive}`);
      } else {
        setActiveSessionName(storedActive);
      }
    }
    const urlParts = (URL_ACTIVE_SESSION || '').split('/').filter(Boolean);
    if (urlParts.length >= 3 && sessionPartsEndWithWorkflow(urlParts)) {
      window.SCOPE_PATH = urlParts[urlParts.length - 2];
      try { localStorage.setItem('atlasScopePath', window.SCOPE_PATH); } catch (_) {}
    }
  } catch (_) {
    if (!window.ACTIVE_SESSION || window.ACTIVE_SESSION === 'default') {
      setActiveSessionName(`${window.ATLAS_USER_SESSION_ID}/default`);
    }
  }

  function sessionFor(scopePath, workflow) {
    let scope = normalizeSessionName(scopePath || '');
    const wf = normalizeSessionName(String(workflow || '').replace(/^\/+|\/+$/g, ''));
    const userSession = normalizeSessionName(window.ATLAS_USER_SESSION_ID || '') || '';
    if (scope === 'default') scope = '';
    const scopeParts = scope.split('/').filter(Boolean);
    const joinSessionParts = (parts) => parts.filter(Boolean).join('/');
    const scopeHasOwner = /^u-[A-Za-z0-9_-]+$/.test(scopeParts[0] || '');
    const scopeEndsWithWorkflow = sessionPartsEndWithWorkflow(scopeParts);
    if (scopeHasOwner) {
      if (wf) {
        if (scopeEndsWithWorkflow || scopeParts[scopeParts.length - 1] === 'user') {
          return joinSessionParts([...scopeParts.slice(0, -1), wf]);
        }
        if (scopeParts.length === 1 || scopeParts[1] === 'default') {
          return joinSessionParts([scopeParts[0], 'soc', wf]);
        }
        return joinSessionParts([...scopeParts, wf]);
      }
      if (scopeEndsWithWorkflow || scopeParts[1] === 'default') return scope;
      if (scopeParts.length === 1) return `${scopeParts[0]}/default`;
      return joinSessionParts([...scopeParts, 'user']);
    }
    if (wf && scope && scopeEndsWithWorkflow) {
      scope = scopeParts.slice(0, -1).join('/');
    } else if (!wf && userSession && scope && scopeEndsWithWorkflow) {
      return joinSessionParts([userSession, scope]);
    }
    // 'user' / 'soc' synthetic segments removed — they planted
    // confusing `.session/<owner>/user/...` and `.session/<owner>/soc/<wf>/...`
    // trees for ip-less / wf-less runs that aren't actually SoC or user-
    // owned. Use 'default' for ip-less and just the workflow segment
    // otherwise so the disk layout reads as the user expects.
    // Always at least 2 segments (owner + something) so the .session
    // tree never has a bare top-level workflow / IP dir like
    // .session/ssot-gen/ or .session/to/ that the user can't ratoionally
    // navigate. owner defaults to 'default' when no per-user session
    // is set (multi-user mode is opt-in via ATLAS_MULTI_USER).
    const owner = userSession || 'default';
    if (scope && wf) return `${owner}/${scope}/${wf}`;
    if (scope)      return `${owner}/${scope}/default`;
    if (wf)         return `${owner}/${wf}`;
    return `${owner}/default`;
  }

  async function refreshSessionState(session, hydrateConversation = true, opts = {}) {
    const sid = normalizeSessionName(session || window.ACTIVE_SESSION || 'default');
    if (!sid) return null;
    // mode: conversation (default) | full | recent
    const mode = (opts && opts.mode) || (() => {
      try { return localStorage.getItem('atlasConversationMode') || 'conversation'; }
      catch (_) { return 'conversation'; }
    })();
    const limit = (opts && Number(opts.limit)) || (mode === 'recent' ? 50 : 200);
    try {
      const url = '/api/session/state'
        + '?session=' + encodeURIComponent(sid)
        + '&limit=' + encodeURIComponent(String(limit))
        + '&mode='  + encodeURIComponent(mode);
      const r = await fetch(url);
      if (!r.ok) return null;
      const d = await r.json();
      const responseSession = normalizeSessionName(d.session || sid) || sid;
      const currentSession = normalizeSessionName(window.ACTIVE_SESSION || '') || sid;
      if (currentSession !== sid && currentSession !== responseSession) {
        return d;
      }
      const appliedSession = responseSession === sid ? responseSession : sid;
      setActiveSessionName(appliedSession);
      const todos = d.todos && Array.isArray(d.todos.todos) ? d.todos.todos : [];
      window.TODOS = normalizeTodos(todos);
      if (hydrateConversation) {
        const sessionDetail = { ...d, session: appliedSession };
        const conversationDetail = {
          messages: (d.conversation && d.conversation.messages) || [],
          session: appliedSession,
        };
        window.ATLAS_LAST_SESSION_STATE = sessionDetail;
        window.ATLAS_LAST_CONVERSATION = conversationDetail;
        window.dispatchEvent(new CustomEvent('atlas-session-loaded', { detail: sessionDetail }));
        window.dispatchEvent(new CustomEvent('atlas-conversation-loaded', {
          detail: conversationDetail,
        }));
      }
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SESSION_STATE' }));
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'TODOS' }));
      return d;
    } catch (e) {
      return null;
    }
  }
  function asTreeNode(entry, depth) {
    return {
      type: entry.type === 'dir' ? 'dir' : 'file',
      name: entry.name,
      size: fmtSize(entry.size),
      // Preserve mtime so the workspace panel can sort by 'recent'
      // (most recently modified first). Backend ships it per entry
      // — see atlas_ui.py:367.
      mtime: entry.mtime || 0,
      depth: depth || 0,
      expanded: false,
      dim: false,
      active: false,
    };
  }

  async function refreshFileTree(path, opts) {
    const reqPath = normalizeScopePath(path || '');
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
      const r = await fetch('/api/files?path=' + encodeURIComponent(reqPath) + recursive);
      if (!r.ok) return;
      const d = await r.json();
      if (Array.isArray(d.entries)) {
        // Trust backend canonical path (resolved + project-relative) so
        // UI scope cannot drift as "spi/spi/spi/..." from alias/symlink
        // clicks that still resolve to the same real directory.
        const canonicalScope = normalizeScopePath(d.path || reqPath);
        if (canonicalScope !== window.SCOPE_PATH) {
          window.SCOPE_PATH = canonicalScope;
          try { localStorage.setItem('atlasScopePath', window.SCOPE_PATH); } catch (_) {}
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
        }
        window.FILE_TREE = d.entries.map(e => asTreeNode(e, e.depth || 0));
        window.FILE_TREE_LAST_REFRESH = Date.now();
        window.FILE_TREE_TRUNCATED = !!d.truncated;
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
      }
    } catch (e) { /* server not reachable yet */ }
  }

  async function refreshTodos() {
    try {
      if (window.ACTIVE_SESSION) {
        const d = await refreshSessionState(window.ACTIVE_SESSION, false);
        if (d) return;
      }
      const r = await fetch('/api/todos');
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
      window.TODOS = normalizeTodos(d.todos);
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'TODOS' }));
    } catch (e) { /* ignore */ }
  }

  async function refreshSlashCommands() {
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
        const live = cmds.map(c => ({
          cmd:   c.cmd,
          alias: (c.aliases && c.aliases[0]) || c.name.slice(0, 2),
          hint:  c.hint || '',
          desc:  c.hint || '',
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
        ];
        const present = new Set(live.map(c => c.cmd));
        for (const c of clientOnly) {
          if (!present.has(c.cmd)) live.push(c);
        }
        live.sort((a, b) => a.cmd.localeCompare(b.cmd));
        window.SLASH_COMMANDS = live;
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SLASH_COMMANDS' }));
      }
    } catch (e) { /* keep built-in fallbacks */ }
  }

  async function refreshSsotList() {
    try {
      const r = await fetch('/api/ssot');
      if (!r.ok) return;
      const d = await r.json();
      window.SSOT_FILES = Array.isArray(d.files) ? d.files : [];
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SSOT_FILES' }));
    } catch (e) { /* ignore */ }
  }

  async function refreshProgress() {
    try {
      const scope = window.SCOPE_PATH || '';
      const r = await fetch('/api/progress?scope=' + encodeURIComponent(scope));
      if (!r.ok) return;
      const d = await r.json();
      window.ATLAS_PROGRESS = d || null;
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'PROGRESS' }));
      return d;
    } catch (e) {
      return null;
    }
  }

  function activeWorkflowFromSession(session) {
    const parts = normalizeSessionName(session || window.ACTIVE_SESSION || '').split('/').filter(Boolean);
    const last = parts[parts.length - 1] || '';
    return KNOWN_WORKFLOWS.has(last) ? last : '';
  }

  async function refreshHealth() {
    try {
      const r = await fetch('/healthz');
      if (!r.ok) return;
      const d = await r.json();
      // First-visit seed of the per-user session id. /healthz now
      // carries the IPv4-derived user_session, so we don't need a
      // separate /api/whoami round-trip on boot. Also seed
      // atlasActiveSession + window.ACTIVE_SESSION so the App
      // shell updates from "default" → "u-<ipv4>/default" on the
      // first render (the existing atlas-session-loaded listener
      // re-derives activeSessionId from the namespace).
      try {
        const stored = (localStorage.getItem('atlasUserSessionId') || '').trim();
        // Migrate stale auto-generated `u-<base36>-<rand>` ids to the
        // server-supplied default ("default" in single-user mode).
        // Don't override deliberate user-named sessions (anything that
        // doesn't match the random stamp pattern).
        const isLegacyRandom = /^u-[a-z0-9]{6,12}-[a-z0-9]{4,8}$/i.test(stored);
        const shouldSeed = (!stored || isLegacyRandom) && d.user_session;
        if (shouldSeed) {
          localStorage.setItem('atlasUserSessionId', d.user_session);
          window.ATLAS_USER_SESSION_ID = d.user_session;
          const storedNs = (localStorage.getItem('atlasActiveSession') || '').trim();
          if (!storedNs || /^u-[a-z0-9]{6,12}-[a-z0-9]{4,8}\//i.test(storedNs)) {
            const seedNs = `${d.user_session}/default`;
            localStorage.setItem('atlasActiveSession', seedNs);
            window.ACTIVE_SESSION = seedNs;
            window.dispatchEvent(new CustomEvent('atlas-session-loaded', {
              detail: { session: seedNs },
            }));
          }
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'USER_SESSION_ID' }));
        }
      } catch (_) {}
      const _prev = window.CONTEXT || {};
      const activeWorkflow = activeWorkflowFromSession();
      const backendWorkspace = normalizeSessionName(d.workspace || '');
      if (typeof d.chat_feed_summary === 'boolean') {
        window.ATLAS_CHAT_FEED_SUMMARY = d.chat_feed_summary;
      }
      window.CONTEXT = Object.assign({}, _prev, {
        frontend:    d.frontend  || '',
        model:       d.model     || _prev.model || '—',
        baseModel:   d.base_model || '',
        baseUrl:     d.base_url   || '',
        provider:    d.provider   || '',
        reasoningEffort: d.reasoning_effort || '',
        activeSession: d.active_session || '',
        activeIp:      d.active_ip      || '',
        activeWorkflow: d.active_workflow || '',
        maxTokens:   d.max_context    || _prev.maxTokens || 0,
        iterMax:     d.max_iterations || _prev.iterMax    || 0,
        workspace:   (backendWorkspace && backendWorkspace !== 'default') ? backendWorkspace : (activeWorkflow || backendWorkspace || ''),
        projectRoot: d.project_root || '',
        cwd:         d.cwd || '',
        pricing:     d.pricing || null,    // {input, cache, output} USD/1M
        chatFeedSummary: window.ATLAS_CHAT_FEED_SUMMARY !== false,
        // Token counts: only seed from /healthz when cost.json is on
        // disk (d.tokens_* is non-null). Otherwise PRESERVE whatever
        // the live WS 'cost' subscription has accumulated this session
        // — the 5s healthz poll used to wipe these to 0 every cycle.
        tokensIn:    (d.tokens_in    != null) ? d.tokens_in    : (_prev.tokensIn    || 0),
        tokensCache: (d.tokens_cache != null) ? d.tokens_cache : (_prev.tokensCache || 0),
        tokensOut:   (d.tokens_out   != null) ? d.tokens_out   : (_prev.tokensOut   || 0),
        costUsd:     (d.cost_usd     != null) ? d.cost_usd     : (_prev.costUsd     || 0),
      });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    } catch (e) { /* ignore */ }
  }

  async function refreshWorkflows() {
    try {
      const r = await fetch('/api/workspaces');
      if (!r.ok) return;
      const d = await r.json();
      const items = Array.isArray(d.items) ? d.items : [];
      const byId = new Map(items.map(w => [w.id, w]));
      const live = DEFAULT_FLOW_STAGES
        .filter(p => byId.has(p.id))
        .map(p => {
          const w = byId.get(p.id);
          return {
            id:    w.id,
            label: w.label || w.name,
            cmd:   p.cmd,
            color: p.color,
            glyph: p.glyph,
          };
        });
      window.FLOW_STAGES = live.length ? live : DEFAULT_FLOW_STAGES.slice();
      const activeWorkflow = activeWorkflowFromSession();
      const backendActive = normalizeSessionName(d.active || '');
      window.CONTEXT.workspace = (backendActive && backendActive !== 'default') ? backendActive : (activeWorkflow || backendActive || '');
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FLOW_STAGES' }));
    } catch (e) { /* ignore */ }
  }

  // Public API for workspace.jsx so it can pull a fresh slice on demand.
  window.atlasData = {
    refreshFileTree, refreshTodos, refreshSsotList, refreshHealth,
    refreshSlashCommands, refreshWorkflows, refreshSessionState, sessionFor,
    refreshProgress, normalizeSessionName,
    setUserSessionId: (sessionId) => {
      const sid = normalizeSessionName(sessionId);
      if (!sid || sid.includes('/')) return window.ATLAS_USER_SESSION_ID || '';
      window.ATLAS_USER_SESSION_ID = sid;
      try { localStorage.setItem('atlasUserSessionId', sid); } catch (_) {}
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'USER_SESSION_ID' }));
      return sid;
    },
    clearTodos: () => fetch('/api/todos/clear', { method: 'POST' }).then(refreshTodos),
    fetchFile: (path) =>
      fetch('/api/file?path=' + encodeURIComponent(path)).then(r => r.json()),
    fetchSsot: (path) =>
      fetch('/api/ssot?file=' + encodeURIComponent(path)).then(r => r.json()),
    setScopePath: (p) => {
      let next = normalizeScopePath(p || '');
      // Scope is bound to the active IP. The IP_ID dropdown is the only
      // control that should change which IP is active; anything that
      // tries to set scope to a path outside the active IP gets clamped
      // back to the IP root so the file tree never leaks cross-IP
      // siblings (the bug where scope = "gpio" still showed
      // simple_gpio_lite/ entries).
      const sess = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
      const activeIp = sess.length >= 2 ? sess[1] : '';
      if (activeIp) {
        const segs = next.split('/').filter(Boolean);
        if (segs.length === 0 || segs[0] !== activeIp) {
          next = activeIp;
        }
      }
      if (next === window.SCOPE_PATH) return;
      window.SCOPE_PATH = next;
      try { localStorage.setItem('atlasScopePath', window.SCOPE_PATH); } catch (_) {}
      // Re-fetch the tree at the new scope so the panel updates.
      refreshFileTree(window.SCOPE_PATH);
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
    },
    setActiveSession: (session) => {
      const sid = setActiveSessionName(session);
      return refreshSessionState(sid);
    },
  };

  // ── Bootstrap ───────────────────────────────────────────────────
  // Coalesce a burst of WS events into a single API hit per resource.
  // Without this, a single agent turn that fires 5 tool_result frames
  // in 200 ms triggers 5 file-tree + 5 ssot + 5 todo fetches and the
  // UI feels sluggish.
  function debounce(fn, wait) {
    let t;
    return function () {
      clearTimeout(t);
      t = setTimeout(fn, wait);
    };
  }
  const _refFiles = debounce(() => refreshFileTree(window.SCOPE_PATH || ''), 250);
  const _refSsot  = debounce(refreshSsotList, 250);
  const _refTodos = debounce(refreshTodos, 250);

  async function boot() {
    // /healthz carries `user_session` derived from the requesting
    // IPv4. Awaiting it first guarantees ATLAS_USER_SESSION_ID is
    // populated before any other fetch fires off, so downstream
    // session-aware calls don't race the seed.
    await refreshHealth();
    refreshFileTree(window.SCOPE_PATH || '');
    refreshTodos();
    refreshSsotList();
    refreshProgress();
    refreshSlashCommands();
    refreshWorkflows();
    // Hook the WS pubsub once it's available so todo_line events trigger
    // a fresh /api/todos fetch (the lines are ANSI-formatted strings; the
    // structured todo state lives behind the API).
    function attach() {
      if (!window.backend || typeof window.backend.subscribe !== 'function') {
        setTimeout(attach, 200);
        return;
      }
      // 'hello' fires on every WS connect (initial + every reconnect
      // after a transient drop). Re-run /healthz so the UI's session/
      // ip/workflow chips and URL params re-sync to whatever the
      // server now reports — without this, a brief WS drop left the
      // browser cached on the OLD triple while the backend may have
      // pivoted to a new IP via /ip / /session / /wf during the gap.
      window.backend.subscribe('hello', () => {
        refreshHealth().then(() => {
          // /healthz lands → CONTEXT.active_session is fresh →
          // syncCurrent in app.jsx will pull the URL into line via
          // its atlas-data-changed listener.
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
        }).catch(() => {});
        refreshSlashCommands();
        refreshWorkflows();
      });
      window.backend.subscribe('todo_line', (m) => {
        const raw = Array.isArray(m && m.todos)
          ? m.todos
          : (m && m.todo_state && Array.isArray(m.todo_state.todos) ? m.todo_state.todos : null);
        if (raw) {
          window.TODOS = normalizeTodos(raw);
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'TODOS' }));
        }
        setTimeout(refreshTodos, 300);
      });
      window.backend.subscribe('tool_result', () => {
        // Coalesce into one fetch per ~250 ms — see _refFiles etc.
        _refFiles(); _refSsot(); _refTodos();
        refreshProgress();
      });
      window.backend.subscribe('context', (m) => {
        if (typeof m.used === 'number') {
          window.CONTEXT.tokens = m.used;
          window.CONTEXT.maxTokens = m.max || window.CONTEXT.maxTokens;
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
        }
      });
      // Live cost — agent fires per-LLM-call. We accumulate into CONTEXT
      // so the sidebar reflects spend without waiting for the 5 s poll.
      window.backend.subscribe('cost', (m) => {
        const ctx = window.CONTEXT;
        ctx.tokensIn    = (ctx.tokensIn    || 0) + (m.input  || 0);
        ctx.tokensCache = (ctx.tokensCache || 0) + (m.cached || 0);
        ctx.tokensOut   = (ctx.tokensOut   || 0) + (m.output || 0);
        // Backend now resolves pricing at LLM-call time (honors
        // LLM_BASE_MODEL env) and ships both the USD delta and the pricing
        // it used. Prefer those over the page-load pricing snapshot so the
        // sidebar reflects the actual model in use right now.
        if (m.pricing) ctx.pricing = m.pricing;
        if (m.model)   ctx.model   = m.model;
        if (typeof m.cost_usd_delta === 'number' && !isNaN(m.cost_usd_delta)) {
          ctx.costUsd = (ctx.costUsd || 0) + m.cost_usd_delta;
        } else if (ctx.pricing) {
          // Fallback for older backends that don't ship cost_usd_delta:
          // recompute from cumulative tokens.
          ctx.costUsd =
            (ctx.tokensIn    * ctx.pricing.input  +
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
      let _lastWs = null;
      // Single hydrate path: dedup on workspace name so we don't
      // clobber the live feed every flush, but DO fire on initial
      // attach (the server's `commands_changed` only emits on flush
      // — without an explicit kickoff, a fresh page load shows an
      // empty chat until the user sends something).
      const _maybeHydrateConversation = () => {
        return refreshHealth().then(() => {
          const ws = (window.CONTEXT && window.CONTEXT.workspace) || '';
          const sid = normalizeSessionName(window.ACTIVE_SESSION || '') || sessionFor(window.SCOPE_PATH || '', ws);
          if (sid === _lastWs) return;
          _lastWs = sid;
          return refreshSessionState(sid, true);
        });
      };
      window.backend.subscribe('commands_changed', () => {
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
      window.backend.subscribe('flush', () => {
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
      refreshFileTree(window.SCOPE_PATH || '');
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
