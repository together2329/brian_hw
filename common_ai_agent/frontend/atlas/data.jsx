// data.jsx — live data bindings for the Atlas frontend.
//
// Replaces the original mock-data file. Every `window.*` global below is
// either an empty/safe default or is populated asynchronously from the
// real HTTP API exposed by src/atlas_ui.py:
//
//   GET /api/files?path=…   → real project file tree
//   GET /api/todos          → real TodoTracker state
//   GET /api/ssot           → list of *.ssot.yaml files (with ?file=… for content)
//
// Plus live updates pushed over the WS:
//   todo_line event → re-fetch /api/todos
//
// The `FLOW_STAGES` / `SLASH_COMMANDS` lists are real, agent-supported
// values (subset of the actual slash commands main.py recognizes).

(function () {
  'use strict';

  // ── Static defaults ─────────────────────────────────────────────
  // All of these are deliberately small/empty. workspace.jsx panels
  // that used to render mock content now render whatever the live
  // backend has, or nothing.

  // Slash commands — populated from /api/commands at boot. Until the
  // first fetch lands, seed with built-ins the agent always supports
  // so the dropdown is never empty if the API is briefly unreachable.
  window.SLASH_COMMANDS = [
    { cmd: '/help',    alias: 'h',  hint: 'show available commands' },
    { cmd: '/clear',   alias: 'cl', hint: 'reset conversation' },
    { cmd: '/compact', alias: 'co', hint: 'compress history' },
    { cmd: '/exit',    alias: 'q',  hint: 'leave the session' },
    { cmd: '/todo',    alias: 't',  hint: 'show / manage todos' },
  ];

  // Workflow stage badges. Empty by default — populated only if a future
  // /api/workflows endpoint exists. Workspace tolerates an empty list.
  window.FLOW_STAGES = [];

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

  // Scope path: agent is asked (via prompt prefix) to keep all reads,
  // writes, and tool calls confined to this directory. Empty string =
  // whole project root. Persists across reloads via localStorage.
  try {
    window.SCOPE_PATH = localStorage.getItem('atlasScopePath') || '';
  } catch (_) {
    window.SCOPE_PATH = '';
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
  function asTreeNode(entry, depth) {
    return {
      type: entry.type === 'dir' ? 'dir' : 'file',
      name: entry.name,
      size: fmtSize(entry.size),
      depth: depth || 0,
      expanded: false,
      dim: false,
      active: false,
    };
  }

  async function refreshFileTree(path) {
    try {
      const r = await fetch('/api/files?path=' + encodeURIComponent(path || ''));
      if (!r.ok) return;
      const d = await r.json();
      if (Array.isArray(d.entries)) {
        window.FILE_TREE = d.entries.map(e => asTreeNode(e, 0));
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
      }
    } catch (e) { /* server not reachable yet */ }
  }

  async function refreshTodos() {
    try {
      const r = await fetch('/api/todos');
      if (!r.ok) return;
      const d = await r.json();
      // TodoTracker.to_dict() shape:
      //   {todos: [{content, activeForm, status, priority, detail, ...}]}
      // The TodoPanel UI expects {id, state, section, title, detail, deps}.
      const status2state = { completed: 'done', in_progress: 'active' };
      window.TODOS = (Array.isArray(d.todos) ? d.todos : []).map((t, i) => ({
        id:      `t${i + 1}`,
        state:   status2state[t.status] || 'pending',
        section: t.priority ? String(t.priority).toUpperCase() : '',
        title:   t.content || '',
        detail:  t.detail || '',
        deps:    [],
      }));
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
        // shape workspace.jsx expects ({cmd, alias, hint}).
        window.SLASH_COMMANDS = cmds.map(c => ({
          cmd:   c.cmd,
          alias: (c.aliases && c.aliases[0]) || c.name.slice(0, 2),
          hint:  c.hint || '',
        }));
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

  async function refreshHealth() {
    try {
      const r = await fetch('/healthz');
      if (!r.ok) return;
      const d = await r.json();
      // healthz currently returns {ok, frontend}; keep room to expand later.
      window.CONTEXT = Object.assign({}, window.CONTEXT, {
        frontend: d.frontend || '',
      });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    } catch (e) { /* ignore */ }
  }

  // Public API for workspace.jsx so it can pull a fresh slice on demand.
  window.atlasData = {
    refreshFileTree, refreshTodos, refreshSsotList, refreshHealth,
    refreshSlashCommands,
    fetchFile: (path) =>
      fetch('/api/file?path=' + encodeURIComponent(path)).then(r => r.json()),
    fetchSsot: (path) =>
      fetch('/api/ssot?file=' + encodeURIComponent(path)).then(r => r.json()),
    setScopePath: (p) => {
      window.SCOPE_PATH = p || '';
      try { localStorage.setItem('atlasScopePath', window.SCOPE_PATH); } catch (_) {}
      // Re-fetch the tree at the new scope so the panel updates.
      refreshFileTree(window.SCOPE_PATH);
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
    },
  };

  // ── Bootstrap ───────────────────────────────────────────────────
  function boot() {
    refreshHealth();
    refreshFileTree(window.SCOPE_PATH || '');
    refreshTodos();
    refreshSsotList();
    refreshSlashCommands();
    // Hook the WS pubsub once it's available so todo_line events trigger
    // a fresh /api/todos fetch (the lines are ANSI-formatted strings; the
    // structured todo state lives behind the API).
    function attach() {
      if (!window.backend || typeof window.backend.subscribe !== 'function') {
        setTimeout(attach, 200);
        return;
      }
      window.backend.subscribe('todo_line', () => refreshTodos());
      window.backend.subscribe('tool_result', (m) => {
        // Refresh on every tool_result — file tree + ssot list are cheap
        // to recompute (~ms each) and any tool can mutate the FS through
        // run_command. Always bump TODOS too in case the agent updated
        // them as a side-effect.
        const path = window.SCOPE_PATH || '';
        refreshFileTree(path);
        refreshSsotList();
        refreshTodos();
      });
      window.backend.subscribe('context', (m) => {
        if (typeof m.used === 'number') {
          window.CONTEXT.tokens = m.used;
          window.CONTEXT.maxTokens = m.max || window.CONTEXT.maxTokens;
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
        }
      });
    }
    attach();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
