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

  // ── axi_dma mock pipeline state ─────────────────────────────────
  // Intercept /api/pipeline/state and /api/orchestrator/workers for the
  // axi_dma demo IP only when screenshot-test bypass is explicitly enabled.
  // Live mode must always hit the backend, even for an IP named axi_dma.
  (function installAxiDmaMock() {
    const AXI_DMA_PIPELINE_STATE = {
      ip: 'axi_dma',
      stages: {
        ssot:        { state: 'passed',  iter: 1,  model: 'gpt-4o',         progress: 1.0, live_tail: '', evidence_paths: ['axi_dma/ssot/axi_dma.ssot.yaml'] },
        'fl-model':  { state: 'passed',  iter: 2,  model: 'gpt-4o',         progress: 1.0, live_tail: '', evidence_paths: ['axi_dma/fl-model/fl_model.json'] },
        'cl-model':  { state: 'passed',  iter: 1,  model: 'gpt-4o',         progress: 1.0, live_tail: '', evidence_paths: ['axi_dma/cl-model/cl_model.json'] },
        equivalence: { state: 'passed',  iter: 1,  model: 'gpt-4o',         progress: 1.0, live_tail: '', evidence_paths: ['axi_dma/equivalence/equiv_report.json'] },
        rtl:         { state: 'running', iter: 14, model: 'gpt-5-codex',    progress: 0.6, live_tail: 'wrote axi_dma_ch_arb.sv (164 lines) — running lint pre-check', evidence_paths: [] },
        sim:         { state: 'running', iter: 3,  model: 'gpt-5.3-codex',  progress: 0.3, live_tail: 'sim driver scoreboarding test vector 84/256', evidence_paths: [] },
        lint:        { state: 'ready',   iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [] },
        tb:          { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for rtl' },
        'sim-debug': { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for sim' },
        coverage:    { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for sim' },
        'goal-audit':{ state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for coverage' },
        syn:         { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for rtl' },
        sta:         { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for syn' },
        pnr:         { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for sta' },
        'sta-post':  { state: 'locked',  iter: 0,  model: '',               progress: 0.0, live_tail: '', evidence_paths: [], locked_reason: 'Waiting for pnr' },
      },
      orchestrator: { enabled: true, mode: 'multi-worker', model: 'gpt-4o', pending_handoffs: 0, claimed_handoffs: 0 },
      run_mode: 'engineering',
      exec_mode: 'orchestrator',
    };

    const AXI_DMA_WORKERS_STATE = {
      orchestrator: { enabled: true, mode: 'multi-worker', model: 'gpt-4o', active_target: 'rtl-gen', last_kind: 'http_send' },
      workers: [
        { workflow: 'ssot-gen',      running_count: 0, status: 'ok' },
        { workflow: 'fl-model-gen',  running_count: 0, status: 'ok' },
        { workflow: 'rtl-gen',       running_count: 1, status: 'ok' },
        { workflow: 'sim',           running_count: 1, status: 'ok' },
        { workflow: 'lint',          running_count: 0, status: 'ok' },
        { workflow: 'tb-gen',        running_count: 0, status: 'ok' },
        { workflow: 'coverage',      running_count: 0, status: 'ok' },
        { workflow: 'syn',           running_count: 0, status: 'ok' },
        { workflow: 'sta',           running_count: 0, status: 'ok' },
        { workflow: 'pnr',           running_count: 0, status: 'ok' },
        { workflow: 'sta-post',      running_count: 0, status: 'ok' },
      ],
    };

    function jsonResp(body) {
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      });
    }

    // Screenshot-test bypass: when localStorage.atlasTestBypass === '1' (set by
    // frontend/atlas/_test_axi_dma.html), the interceptor also fakes
    // /api/auth/status and /api/users/me so the screenshot pipeline can render
    // the Pipeline screen without going through the real login UI. Real users
    // never set this flag — the gate is intentional, not a security hole.
    const isTestBypass = (() => {
      try {
        const liveBackend = new URLSearchParams(location.search || '').get('backend') === 'live';
        return !liveBackend && localStorage.getItem('atlasTestBypass') === '1';
      }
      catch (_) { return false; }
    })();
    if (isTestBypass && typeof window !== 'undefined') {
      // Pre-seed the active IP so pipelineInitialIp picks axi_dma instead of
      // falling back to the default IP. Runs before React mounts AtlasPipeline.
      window.ACTIVE_IP = 'axi_dma';
      window.ATLAS_USER_SESSION_ID = 'brian';
      window.ACTIVE_SESSION = 'brian/axi_dma/orchestrator';
    }
    const TEST_USER = { username: 'brian', display_name: 'brian (test)', is_authenticated: true };
    const TEST_ME = { user: TEST_USER };  // app.jsx unwraps j.user
    const TEST_AUTH_STATUS = { authenticated: true, username: 'brian', user: TEST_USER, recovery_enabled: false, email_required: false };

    // In test bypass, hide the boot-progress dialog and force dark theme so
    // screenshots match the Pipeline Image mockup. WebSocket inevitably fails
    // against the static server, and app.jsx defaults theme to 'light' with no
    // localStorage persistence — so we keep-alive 'dark' via setInterval.
    if (isTestBypass && typeof document !== 'undefined') {
      const installHideStyle = () => {
        const s = document.createElement('style');
        s.setAttribute('data-test-bypass', '1');
        s.textContent = '[role="status"][aria-live="polite"]{display:none!important;}';
        if (document.head) document.head.appendChild(s);
      };
      if (document.head) installHideStyle();
      else document.addEventListener('DOMContentLoaded', installHideStyle, { once: true });
      // Override <html> setAttribute and a MutationObserver to force
      // data-theme="dark" on EVERY element that ever gets a data-theme
      // attribute (React sets it via JSX prop on the .app inner div, which
      // bypasses html.setAttribute monkey-patch).
      try {
        const html = document.documentElement;
        const origSetAttr = html.setAttribute.bind(html);
        html.setAttribute = function(name, value) {
          if (name === 'data-theme') return origSetAttr(name, 'dark');
          return origSetAttr(name, value);
        };
        origSetAttr('data-theme', 'dark');
      } catch (_) {}
      // After mount, drive the IP-picker <select> to axi_dma so the pipeline
      // state mock fires with ip=axi_dma instead of the default. Uses React's
      // native value setter + a bubbling change event so the React onChange
      // handler picks up the new value.
      const setAxiDma = () => {
        try {
          const select = document.querySelector('select.pipe-stage-rail-select');
          if (!select) return false;
          if (select.value === 'axi_dma') return true;
          // Ensure the option exists in the dropdown
          let hasOpt = false;
          for (const opt of select.options) { if (opt.value === 'axi_dma') { hasOpt = true; break; } }
          if (!hasOpt) return false;
          const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
          setter.call(select, 'axi_dma');
          select.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        } catch (_) { return false; }
      };
      const startClicker = () => {
        let ticks = 0;
        const id = setInterval(() => {
          if (setAxiDma() || ++ticks > 30) clearInterval(id);
        }, 200);
      };
      if (document.body) startClicker();
      else document.addEventListener('DOMContentLoaded', startClicker, { once: true });

      try {
        const enforceDark = (target) => {
          if (target && target.getAttribute && target.getAttribute('data-theme') === 'light') {
            target.setAttribute('data-theme', 'dark');
          }
        };
        const mo = new MutationObserver((mutations) => {
          mutations.forEach((m) => {
            if (m.type === 'attributes' && m.attributeName === 'data-theme') {
              enforceDark(m.target);
            }
            if (m.type === 'childList') {
              m.addedNodes.forEach((n) => {
                if (n && n.nodeType === 1) {
                  enforceDark(n);
                  if (n.querySelectorAll) {
                    n.querySelectorAll('[data-theme="light"]').forEach(enforceDark);
                  }
                }
              });
            }
          });
        });
        const startObserving = () => {
          if (!document.body) return;
          mo.observe(document.body, { attributes: true, attributeFilter: ['data-theme'], subtree: true, childList: true });
          // Initial sweep
          document.querySelectorAll('[data-theme="light"]').forEach(enforceDark);
        };
        if (document.body) startObserving();
        else document.addEventListener('DOMContentLoaded', startObserving, { once: true });
      } catch (_) {}
    }

    const _origFetch = window.fetch.bind(window);
    window.fetch = function atlasAxiDmaMockFetch(input, init) {
      let path = '';
      try {
        const url = typeof input === 'string' ? input : (input && input.url) || '';
        const parsed = new URL(url, location.href);
        path = parsed.pathname + parsed.search;
      } catch (_) {}
      if (isTestBypass) {
        if (/^\/api\/pipeline\/state/.test(path)) {
          const ipParam = (() => {
            try { return new URL(path, location.href).searchParams.get('ip') || ''; } catch (_) { return ''; }
          })();
          if (ipParam === 'axi_dma') {
            return Promise.resolve(jsonResp(AXI_DMA_PIPELINE_STATE));
          }
        }
        if (/^\/api\/orchestrator\/workers/.test(path)) {
          const ipParam = (() => {
            try { return new URL(path, location.href).searchParams.get('ip') || ''; } catch (_) { return ''; }
          })();
          if (ipParam === 'axi_dma') {
            return Promise.resolve(jsonResp(AXI_DMA_WORKERS_STATE));
          }
        }
        if (/^\/api\/auth\/status/.test(path)) {
          return Promise.resolve(jsonResp(TEST_AUTH_STATUS));
        }
        if (/^\/api\/users\/me/.test(path)) {
          return Promise.resolve(jsonResp(TEST_ME));
        }
        if (/^\/api\/ip\/list/.test(path)) {
          return Promise.resolve(jsonResp({
            items: [
              { ip: 'axi_dma', name: 'axi_dma', has_yaml: true, has_rtl: true, has_tb: true, has_sim: false },
              { ip: 'atcdmac100', name: 'atcdmac100', has_yaml: true, has_rtl: true, has_tb: true, has_sim: true },
              { ip: 'arm_m0_min', name: 'arm_m0_min', has_yaml: true, has_rtl: true, has_tb: true, has_sim: true },
            ],
          }));
        }
      }
      return _origFetch(input, init);
    };
  })();

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
    { cmd: '/pipeline', alias: 'pl', hint: '(client) dispatch full SSOT pipeline: /pipeline <ip>' },
    { cmd: '/scope',   alias: 'sc', hint: '(client) confine agent to a directory: /scope <path>' },
    { cmd: '/cd',      alias: 'cd', hint: '(client) alias for /scope' },
    { cmd: '/session', alias: 'ss', hint: '(client) show or switch session: /session default' },
    { cmd: '/memory', alias: 'mem', hint: "show or edit this user's prompt memory rules" },
    { cmd: '/feedback', alias: 'fb', hint: '(client) send admin-visible feedback: /feedback <message>' },
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
    { id: 'sta-post',     label: 'sta-post',     cmd: '/wf sta-post',     color: 'var(--warn)',   glyph: 'PS' },
  ];

  const ORCHESTRATOR_FLOW_STAGE = {
    id: 'orchestrator',
    label: 'orchestrator',
    cmd: '/workflow orchestrator',
    color: 'var(--cyan)',
    glyph: 'OR',
  };

  // General-purpose chat workflow (workflow/default/). The single-worker
  // counterpart to the orchestrator entry — gives single-worker mode a free
  // conversation window (like the textual UI's general window) instead of
  // only stage workflows.
  const DEFAULT_FLOW_STAGE = {
    id: 'default',
    label: 'default',
    cmd: '/workflow default',
    color: 'var(--fg)',
    glyph: 'GP',
  };

  function atlasExecMode() {
    return String(
      window.ATLAS_EXEC_MODE
      || window.ATLAS_DEFAULT_EXEC_MODE
      || (window.ATLAS_BOOT_CONFIG && window.ATLAS_BOOT_CONFIG.exec_mode)
      || ''
    ).trim().toLowerCase();
  }

  function flowStagesForExecMode(stages) {
    const base = Array.isArray(stages) ? stages : DEFAULT_FLOW_STAGES;
    const deduped = base.filter((s) => s
      && s.id !== ORCHESTRATOR_FLOW_STAGE.id
      && s.id !== DEFAULT_FLOW_STAGE.id);
    if (atlasExecMode() === 'orchestrator') {
      return [ORCHESTRATOR_FLOW_STAGE].concat(deduped);
    }
    // single-worker: lead with the general-purpose 'default' chat workflow.
    return [DEFAULT_FLOW_STAGE].concat(deduped);
  }

  // Workflow stage badges. Seed the canonical IP flow immediately so the
  // left workflow rail is visible even before /api/workspaces returns.
  window.FLOW_STAGES = flowStagesForExecMode(DEFAULT_FLOW_STAGES);

  // Question flows for ask_user. Dynamic flows are pushed in by
  // workspace.jsx's `ask_user` WS subscription, so we only need an
  // empty seed here.
  window.QA_FLOWS = {};

  // Live-fetched data — initialized empty, refreshed on connect /
  // periodically thereafter. Each is a plain array/object; consumers
  // re-read it on every render so updates are picked up.
  window.FILE_TREE = [];
  window.FILE_TREE_LOADING = false;
  window.FILE_TREE_ERROR = '';
  window.FILE_TREE_EMPTY_REASON = 'select_ip';
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
    const params = new URLSearchParams(window.location.search || '');
    const urlSession = normalizeSessionName(params.get('session') || '');
    const urlParts = urlSession.split('/').filter(Boolean);
    const urlOwner = normalizeSessionName(
      (urlParts.length >= 3 ? urlParts[0] : '') || params.get('session_id') || ''
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
    const urlNamespace = urlSession || (
      (urlIp || urlWorkflow)
        ? `${urlOwner || 'default'}/${urlIp || 'default'}/${urlWorkflow || 'default'}`
        : ''
    );
    window.ACTIVE_SESSION = urlNamespace || normalizeSessionName(localStorage.getItem('atlasActiveSession')) || 'default';
    if (urlNamespace) localStorage.setItem('atlasActiveSession', urlNamespace);
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

  const DEFAULT_WORKFLOW = 'default';
  const KNOWN_WORKFLOWS = new Set([
    DEFAULT_WORKFLOW,
    'architect',
    'coverage',
    'fl-model-gen',
    'goal-audit',
    'lint',
    'mas-gen',
    'orchestrator',
    'rtl-gen',
    'signoff',
    'sim',
    'sim_debug',
    'ssot-gen',
    'sta',
    'sta-post',
    'syn',
    'tb-gen',
    'pnr',
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

  function healthMatchesCurrentUser(payload) {
    const current = normalizeSessionName((window.ATLAS_USER && window.ATLAS_USER.username) || '');
    const response = normalizeSessionName((payload && payload.user_session) || '');
    return !(current && response && current !== response);
  }

  function routeSessionInfo(session) {
    const route = window.AtlasSessionRouting || {};
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

  function browserSessionOverridesHealth(payload) {
    const route = window.AtlasSessionRouting || {};
    const browserSession = normalizeSessionName(window.ACTIVE_SESSION || '');
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

  function healthCountersMatchBrowserRoute(payload) {
    const route = window.AtlasSessionRouting || {};
    const browserSession = normalizeSessionName(window.ACTIVE_SESSION || '');
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

  function readUrlNamespace() {
    let params;
    try { params = new URLSearchParams(window.location.search || ''); }
    catch (_) { return ''; }
    const direct = normalizeSessionName(
      params.get('session') || params.get('sid') || params.get('namespace') || ''
    );
    if (direct && direct.includes('/')) {
      const directParts = direct.split('/').filter(Boolean);
      if (directParts.length >= 3) return direct;
      if (directParts.length === 2) {
        const owner = directParts[0] || 'default';
        const second = directParts[1] || DEFAULT_WORKFLOW;
        if (KNOWN_WORKFLOWS.has(String(second).toLowerCase())) {
          return `${owner}/${DEFAULT_WORKFLOW}/${second}`;
        }
        return `${owner}/${second}/${DEFAULT_WORKFLOW}`;
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
    const baseOwner = owner || storedOwner || normalizeSessionName(window.ATLAS_USER_SESSION_ID || '') || 'default';
    if (ip && wf) return `${baseOwner}/${ip}/${wf}`;
    if (ip) return `${baseOwner}/${ip}/${DEFAULT_WORKFLOW}`;
    if (wf) return `${baseOwner}/${DEFAULT_WORKFLOW}/${wf}`;
    if (owner) return `${owner}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`;
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
    try {
      const route = window.AtlasSessionRouting || {};
      const ip = typeof route.sessionIpFromSession === 'function'
        ? route.sessionIpFromSession(sid)
        : activeIpFromSession(sid);
      window.ACTIVE_IP = ip || '';
    } catch (_) {}
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
      setActiveSessionName(`${window.ATLAS_USER_SESSION_ID}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`);
    } else {
      const parts = storedActive.split('/').filter(Boolean);
      if (parts.length === 2 && String(parts[1] || '').toLowerCase() === DEFAULT_WORKFLOW) {
        setActiveSessionName(`${parts[0]}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`);
      } else {
        const legacyIpWorkflow = parts.length === 2
          && String(parts[1] || '').toLowerCase() !== DEFAULT_WORKFLOW
          && KNOWN_WORKFLOWS.has(String(parts[1] || '').toLowerCase());
        const legacyWorkflow = parts.length === 1 && KNOWN_WORKFLOWS.has(String(parts[0] || '').toLowerCase());
        if (legacyIpWorkflow) {
          setActiveSessionName(`${window.ATLAS_USER_SESSION_ID}/${storedActive}`);
        } else if (legacyWorkflow) {
          setActiveSessionName(`${window.ATLAS_USER_SESSION_ID}/${DEFAULT_WORKFLOW}/${storedActive}`);
        } else {
          setActiveSessionName(storedActive);
        }
      }
    }
    const urlParts = (URL_ACTIVE_SESSION || '').split('/').filter(Boolean);
    if (urlParts.length >= 3 && sessionPartsEndWithWorkflow(urlParts)) {
      window.SCOPE_PATH = urlParts[urlParts.length - 2];
      try { localStorage.setItem('atlasScopePath', window.SCOPE_PATH); } catch (_) {}
    }
  } catch (_) {
    if (!window.ACTIVE_SESSION || window.ACTIVE_SESSION === 'default') {
      setActiveSessionName(`${window.ATLAS_USER_SESSION_ID}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`);
    }
  }

  function sessionFor(scopePath, workflow) {
    let scope = normalizeSessionName(scopePath || '');
    const wf = normalizeSessionName(String(workflow || '').replace(/^\/+|\/+$/g, ''));
    const userSession = normalizeSessionName(window.ATLAS_USER_SESSION_ID || '') || '';
    if (scope === 'default') scope = '';
    const scopeParts = scope.split('/').filter(Boolean);
    const joinSessionParts = (parts) => parts.filter(Boolean).join('/');
    const scopeEndsWithWorkflow = sessionPartsEndWithWorkflow(scopeParts);
    const scopeIsCompleteNamespace = scopeParts.length >= 3 && scopeEndsWithWorkflow;
    const firstScopePart = scopeParts[0] || '';
    const scopeHasOwner = !!firstScopePart && (
      firstScopePart === userSession
      || /^u-[A-Za-z0-9_-]+$/.test(firstScopePart)
      || scopeIsCompleteNamespace
    );
    if (scopeHasOwner) {
      if (wf) {
        if (scopeIsCompleteNamespace || scopeParts[scopeParts.length - 1] === 'user') {
          return joinSessionParts([...scopeParts.slice(0, -1), wf]);
        }
        if (scopeParts.length === 1 || scopeParts[1] === DEFAULT_WORKFLOW) {
          return joinSessionParts([scopeParts[0], DEFAULT_WORKFLOW, wf]);
        }
        return joinSessionParts([...scopeParts, wf]);
      }
      if (scopeIsCompleteNamespace) return scope;
      if (scopeParts[1] === DEFAULT_WORKFLOW) {
        return joinSessionParts([scopeParts[0], DEFAULT_WORKFLOW, DEFAULT_WORKFLOW]);
      }
      if (scopeParts.length === 1) return `${scopeParts[0]}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`;
      return joinSessionParts([...scopeParts, DEFAULT_WORKFLOW]);
    }
    if (wf && scope && scopeEndsWithWorkflow) {
      scope = scopeParts.slice(0, -1).join('/');
    } else if (!wf && userSession && scope && scopeEndsWithWorkflow) {
      return joinSessionParts([userSession, DEFAULT_WORKFLOW, scope]);
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
    if (scope && wf) return `${owner}/${scope}/${wf}`;
    if (scope)      return `${owner}/${scope}/${DEFAULT_WORKFLOW}`;
    if (wf)         return `${owner}/${DEFAULT_WORKFLOW}/${wf}`;
    return `${owner}/${DEFAULT_WORKFLOW}/${DEFAULT_WORKFLOW}`;
  }

  const SESSION_STATE_CACHE_MS = 1200;
  const CHAT_SWITCH_LIMIT = 80;
  const WORKER_SNAPSHOT_CACHE_MS = 1500;
  const sessionStateCache = new Map();
  const workerSnapshotCache = new Map();

  async function refreshSessionState(session, hydrateConversation = true, opts = {}) {
    const sid = normalizeSessionName(session || window.ACTIVE_SESSION || 'default');
    if (!sid) return null;
    // mode: conversation (default) | full | recent
    const mode = (opts && opts.mode) || (() => {
      try { return localStorage.getItem('atlasConversationMode') || 'conversation'; }
      catch (_) { return 'conversation'; }
    })();
    const limit = (opts && Number(opts.limit)) || (mode === 'recent' ? 50 : 200);
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
      const currentSession = normalizeSessionName(window.ACTIVE_SESSION || '') || sid;
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
        window.TODOS = normalizeTodos(todos);
      }
      if (hydrateConversation) {
        const sessionDetail = { ...d, session: appliedSession };
        const conversationDetail = {
          messages: (d.conversation && d.conversation.messages) || [],
          session: appliedSession,
        };
        if (!allowInactiveConversation) {
          window.ATLAS_LAST_SESSION_STATE = sessionDetail;
          window.ATLAS_LAST_CONVERSATION = conversationDetail;
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

  function refreshActiveConversation(session, opts = {}) {
    return refreshSessionState(session, true, {
      mode: 'conversation',
      limit: CHAT_SWITCH_LIMIT,
      ...(opts || {}),
    });
  }

  function workerSnapshotUrl(opts = {}) {
    const params = new URLSearchParams();
    const activeOnly = opts.activeOnly !== false && opts.active_only !== false;
    if (activeOnly) params.set('active_only', '1');
    const ip = String(opts.ip || '').trim();
    if (ip && ip !== 'default') params.set('ip', ip);
    const query = params.toString();
    return `/api/orchestrator/workers${query ? `?${query}` : ''}`;
  }

  async function fetchWorkerSnapshot(opts = {}) {
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
    const activeIp = activeIpFromSession();
    const reqPath = activeIp;
    if (!reqPath) {
      window.FILE_TREE = [];
      window.FILE_TREE_LOADING = false;
      window.FILE_TREE_ERROR = '';
      window.FILE_TREE_EMPTY_REASON = 'select_ip';
      window.FILE_TREE_TRUNCATED = false;
      window.FILE_TREE_LAST_REFRESH = 0;
      if (window.SCOPE_PATH) {
        window.SCOPE_PATH = '';
        try { localStorage.removeItem('atlasScopePath'); } catch (_) {}
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
      }
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
      return;
    }
    const quiet = !!(opts && opts.quiet && Array.isArray(window.FILE_TREE) && window.FILE_TREE.length);
    if (!quiet) {
      window.FILE_TREE_LOADING = true;
      window.FILE_TREE_ERROR = '';
      window.FILE_TREE_EMPTY_REASON = '';
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
    } else {
      window.FILE_TREE_ERROR = '';
      window.FILE_TREE_EMPTY_REASON = '';
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
      const r = await fetch('/api/files?path=' + encodeURIComponent(reqPath) + recursive, {
        cache: 'no-store',
        credentials: 'include',
      });
      if (!r.ok) {
        let message = r.statusText || `HTTP ${r.status}`;
        try {
          const d = await r.json();
          message = d.error || d.detail || message;
        } catch (_) {}
        if (!quiet) window.FILE_TREE = [];
        window.FILE_TREE_ERROR = message;
        window.FILE_TREE_EMPTY_REASON = '';
        window.FILE_TREE_LOADING = false;
        window.FILE_TREE_LAST_REFRESH = Date.now();
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
        return;
      }
      const d = await r.json();
      if (Array.isArray(d.entries)) {
        // Trust backend canonical path (resolved + project-relative) so
        // UI scope cannot drift as "spi/spi/spi/..." from alias/symlink
        // clicks that still resolve to the same real directory.
        const canonicalScope = activeIp || normalizeScopePath(d.path || reqPath);
        if (canonicalScope !== window.SCOPE_PATH) {
          window.SCOPE_PATH = canonicalScope;
          try { localStorage.setItem('atlasScopePath', window.SCOPE_PATH); } catch (_) {}
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
        }
        window.FILE_TREE = d.entries.map(e => asTreeNode(e, e.depth || 0));
        window.FILE_TREE_LAST_REFRESH = Date.now();
        window.FILE_TREE_TRUNCATED = !!d.truncated;
        window.FILE_TREE_ERROR = '';
        window.FILE_TREE_EMPTY_REASON = '';
        window.FILE_TREE_LOADING = false;
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
      }
    } catch (e) {
      if (!quiet) window.FILE_TREE = [];
      window.FILE_TREE_ERROR = String(e && e.message || e || 'file tree request failed');
      window.FILE_TREE_EMPTY_REASON = '';
      window.FILE_TREE_LOADING = false;
      window.FILE_TREE_LAST_REFRESH = Date.now();
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FILE_TREE' }));
    }
  }

  function invalidateSessionState(session) {
    const sid = normalizeSessionName(session || window.ACTIVE_SESSION || '');
    if (!sid) {
      sessionStateCache.clear();
      return;
    }
    const needle = 'session=' + encodeURIComponent(sid);
    for (const key of Array.from(sessionStateCache.keys())) {
      if (key.indexOf(needle) >= 0) sessionStateCache.delete(key);
    }
  }

  async function refreshTodos(opts = {}) {
    try {
      if (window.ACTIVE_SESSION) {
        const d = await refreshSessionState(window.ACTIVE_SESSION, false, { force: !!opts.force });
        if (d) return;
      }
      const query = window.ACTIVE_SESSION
        ? ('?session=' + encodeURIComponent(normalizeSessionName(window.ACTIVE_SESSION)))
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
      const r = await fetch('/api/ssot', { cache: 'no-store' });
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

  function activeIpFromSession(session) {
    const parts = normalizeSessionName(session || window.ACTIVE_SESSION || '').split('/').filter(Boolean);
    if (parts.length >= 3) {
      const ip = parts[parts.length - 2] || '';
      return ip === DEFAULT_WORKFLOW ? '' : ip;
    }
    return '';
  }

  async function refreshHealth() {
    try {
      const r = await fetch('/healthz');
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
          window.ATLAS_USER_SESSION_ID = serverUser;
          const storedNs = normalizeSessionName(localStorage.getItem('atlasActiveSession') || '');
          const liveNs = normalizeSessionName(window.ACTIVE_SESSION || '');
          const activeNs = normalizeSessionName(URL_ACTIVE_SESSION || liveNs || storedNs);
          const activeParts = activeNs.split('/').filter(Boolean);
          const activeOwner = activeParts[0] || '';
          const legacyNs = /^u-[a-z0-9]{6,12}-[a-z0-9]{4,8}(?:\/|$)/i.test(activeNs);
          const ownerMismatch = !!(activeOwner && activeOwner !== serverUser);
          if (!activeNs || activeNs === 'default' || legacyNs || ownerMismatch) {
            const serverNs = normalizeSessionName(d.active_session || '');
            const serverParts = serverNs.split('/').filter(Boolean);
            let tail = [];
            if ((legacyNs || ownerMismatch) && URL_ACTIVE_SESSION) {
              tail = activeParts.slice(1);
            } else if (serverParts[0] === serverUser) {
              tail = serverParts.slice(1);
            }
            if (tail.length < 2) tail = ['default', 'default'];
            const seedNs = [serverUser, ...tail.slice(0, 2)].join('/');
            localStorage.setItem('atlasActiveSession', seedNs);
            window.ACTIVE_SESSION = seedNs;
            window.dispatchEvent(new CustomEvent('atlas-session-loaded', {
              detail: { session: seedNs },
            }));
          } else if (storedNs !== activeNs) {
            localStorage.setItem('atlasActiveSession', activeNs);
          }
          if (userChanged && !URL_ACTIVE_SESSION) {
            window.SCOPE_PATH = '';
            localStorage.removeItem('atlasScopePath');
            window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
          }
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'USER_SESSION_ID' }));
        }
      } catch (_) {}
      const _prev = window.CONTEXT || {};
      const browserSession = normalizeSessionName(window.ACTIVE_SESSION || '');
      const healthSession = normalizeSessionName(d.active_session || '');
      const healthOverride = browserSessionOverridesHealth(d);
      const effectiveSession = healthOverride ? browserSession : (healthSession || browserSession);
      const acceptHealthCounters = healthCountersMatchBrowserRoute(d);
      const effectiveRoute = routeSessionInfo(effectiveSession);
      const activeWorkflow = activeWorkflowFromSession(effectiveSession);
      const backendWorkspace = normalizeSessionName(d.workspace || '');
      if (typeof d.chat_feed_summary === 'boolean') {
        window.ATLAS_CHAT_FEED_SUMMARY = d.chat_feed_summary;
      }
      // Keep SCOPE_PATH aligned with the active namespace IP. During a fast
      // new-IP switch the browser namespace can be newer than /healthz for a
      // few ticks, so prefer the IP embedded in ACTIVE_SESSION and only fall
      // back to the backend IP when the browser has no real IP yet.
      const backendActiveIp = String(d.active_ip || '').trim();
      const browserActiveIp = activeIpFromSession();
      const routeActiveIp = effectiveRoute.ip || browserActiveIp || backendActiveIp;
      if (routeActiveIp && routeActiveIp !== 'default') {
        window.ACTIVE_IP = routeActiveIp;
      }
      if (routeActiveIp && routeActiveIp !== 'default' && routeActiveIp !== window.SCOPE_PATH) {
        window.SCOPE_PATH = routeActiveIp;
        try { localStorage.setItem('atlasScopePath', routeActiveIp); } catch (_) {}
        window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
      }
      const healthMetaApplies = !healthSession || !effectiveSession || healthSession === effectiveSession;
      if (healthMetaApplies) {
        window.ATLAS_DB_SESSION_ID = String(d.db_session_id || '').trim();
        window.ATLAS_SESSION_UID = String(d.session_uid || '').trim();
        window.ATLAS_SESSION_LABEL = String(d.session_label || '').trim();
      }
      const effectiveWorkspace = activeWorkflow || (healthOverride ? (_prev.workspace || '') : (backendWorkspace || ''));
      window.CONTEXT = Object.assign({}, _prev, {
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
          const keep = (value) => (resetCounters ? 0 : value);
          const stable = (key, value) => {
            if (!acceptHealthCounters) return keep(Number(_prev[key] || 0));
            const next = Number(value || 0);
            if (resetCounters) return next;
            const prev = Number(_prev[key] || 0);
            return Number.isFinite(next) ? Math.max(prev, next) : prev;
          };
          return {
            tokens: (d.tokens != null) ? stable('tokens', d.tokens) : keep(Number(_prev.tokens || 0)),
            tokensIn: (d.tokens_in != null) ? stable('tokensIn', d.tokens_in) : keep(Number(_prev.tokensIn || 0)),
            tokensCache: (d.tokens_cache != null) ? stable('tokensCache', d.tokens_cache) : keep(Number(_prev.tokensCache || 0)),
            tokensOut: (d.tokens_out != null) ? stable('tokensOut', d.tokens_out) : keep(Number(_prev.tokensOut || 0)),
            costUsd: (d.cost_usd != null) ? stable('costUsd', d.cost_usd) : keep(Number(_prev.costUsd || 0)),
            costScope: acceptHealthCounters ? (d.cost_scope || _prev.costScope || '') : (_prev.costScope || (routeActiveIp ? 'user_ip' : '')),
            costUser: acceptHealthCounters ? (d.cost_user || _prev.costUser || '') : (effectiveRoute.owner || _prev.costUser || ''),
            costIp: acceptHealthCounters ? (d.cost_ip || routeActiveIp || _prev.costIp || '') : (routeActiveIp || ''),
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
        chatFeedSummary: window.ATLAS_CHAT_FEED_SUMMARY !== false,
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
      window.FLOW_STAGES = flowStagesForExecMode(live.length ? live : DEFAULT_FLOW_STAGES);
      const activeWorkflow = activeWorkflowFromSession();
      const backendActive = normalizeSessionName(d.active || '');
      window.CONTEXT.workspace = activeWorkflow || backendActive || '';
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FLOW_STAGES' }));
    } catch (e) { /* ignore */ }
  }

  // Public API for workspace.jsx so it can pull a fresh slice on demand.
  window.atlasData = {
    refreshFileTree, refreshTodos, refreshSsotList, refreshHealth,
    refreshSlashCommands, refreshWorkflows, refreshSessionState, refreshActiveConversation,
    fetchWorkerSnapshot, sessionFor, refreshProgress, normalizeSessionName,
    refreshWorkflowStagesForPolicy: () => {
      window.FLOW_STAGES = flowStagesForExecMode(window.FLOW_STAGES || DEFAULT_FLOW_STAGES);
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FLOW_STAGES' }));
    },
    setUserSessionId: (sessionId) => {
      const sid = normalizeSessionName(sessionId);
      if (!sid || sid.includes('/')) return window.ATLAS_USER_SESSION_ID || '';
      window.ATLAS_USER_SESSION_ID = sid;
      try { localStorage.setItem('atlasUserSessionId', sid); } catch (_) {}
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'USER_SESSION_ID' }));
      return sid;
    },
    clearTodos: () => {
      const session = normalizeSessionName(window.ACTIVE_SESSION || '');
      return fetch('/api/todos/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session }),
      }).then(() => {
        invalidateSessionState(session);
        return refreshTodos({ force: true });
      });
    },
    addTodo: (fields) => {
      const session = normalizeSessionName(window.ACTIVE_SESSION || '');
      return fetch('/api/todos/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session, ...(fields || {}) }),
      }).then(() => {
        invalidateSessionState(session);
        return refreshTodos({ force: true });
      });
    },
    updateTodo: (index, fields) => {
      const session = normalizeSessionName(window.ACTIVE_SESSION || '');
      return fetch('/api/todos/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session, index, ...(fields || {}) }),
      }).then(() => {
        invalidateSessionState(session);
        return refreshTodos({ force: true });
      });
    },
    removeTodo: (index) => {
      const session = normalizeSessionName(window.ACTIVE_SESSION || '');
      return fetch('/api/todos/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session, index }),
      }).then(() => {
        invalidateSessionState(session);
        return refreshTodos({ force: true });
      });
    },
    fetchFile: (path) =>
      fetch('/api/file?path=' + encodeURIComponent(path)).then(r => r.json()),
    fetchSsot: (path) =>
      fetch('/api/ssot?file=' + encodeURIComponent(path)).then(r => r.json()),
    setScopePath: (p) => {
      let next = normalizeScopePath(p || '');
      if (next === DEFAULT_WORKFLOW) next = '';
      // Scope is no longer user-browsable: the left file tree is always
      // rooted at the active IP. The IP_ID dropdown is the only control
      // that changes this root; folder clicks only fold/unfold locally.
      const sess = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
      const activeIp = sess.length >= 2 && sess[1] !== DEFAULT_WORKFLOW ? sess[1] : '';
      if (activeIp) {
        next = activeIp;
      } else {
        next = '';
      }
      if (next === window.SCOPE_PATH) {
        if (!activeIp) refreshFileTree('', { recursive: true });
        return;
      }
      window.SCOPE_PATH = next;
      try {
        if (window.SCOPE_PATH) localStorage.setItem('atlasScopePath', window.SCOPE_PATH);
        else localStorage.removeItem('atlasScopePath');
      } catch (_) {}
      // Re-fetch the IP-rooted tree so folder clicks can fold/unfold locally.
      refreshFileTree(window.SCOPE_PATH, { recursive: true });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SCOPE_PATH' }));
    },
    setActiveSession: (session) => {
      const sid = setActiveSessionName(session);
      return refreshActiveConversation(sid);
    },
  };

  window.addEventListener('atlas-run-policy-changed', () => {
    window.FLOW_STAGES = flowStagesForExecMode(window.FLOW_STAGES || DEFAULT_FLOW_STAGES);
    window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'FLOW_STAGES' }));
  });

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

  const WRITE_TOOL_RE = /^(?:write_file|write_to_file|replace_in_file|replace_lines|replace_file_content|multi_replace_file_content|edit_file|patch_file|apply_patch|patch|update_file)\b/i;
  const CHANGED_PATH_EXT_RE = /^(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl|css|js|jsx|ts|tsx|html)$/i;

  function changedPathsFromToolResult(tool, text) {
    const toolText = String(tool || '');
    const body = String(text || '');
    if (!WRITE_TOOL_RE.test(toolText)) return [];
    const seen = new Set();
    const out = [];
    const add = (value) => {
      let path = String(value || '').trim().replace(/^['"`]+|['"`]+$/g, '');
      path = path.replace(/[\s,;:]+$/g, '');
      if (!path || path === '.' || path === '..' || path.includes('\n')) return;
      const ext = path.split('.').pop() || '';
      if (!CHANGED_PATH_EXT_RE.test(ext)) return;
      if (!seen.has(path)) {
        seen.add(path);
        out.push(path);
      }
    };
    const scan = (rx, source = body) => {
      let m;
      while ((m = rx.exec(source)) !== null) add(m[1]);
    };
    scan(/(?:wrote to|wrote|updated|created|deleted|(?:successfully\s+)?replaced\s+(?:in|to)|replaced\s+\d+\s+occurrence(?:\(s\)|s)?\s+in)\s+['"`]([^'"`]+)['"`]/gi);
    scan(/(?:wrote file|updated file|created file|deleted file|target_file|file_path|path)\s*[:=]\s*['"`]?([^\s,'"`)\]]+)/gi, `${toolText}\n${body}`);
    scan(/^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(.+?)\s*$/gmi);
    scan(/^(?:[MADRCU]|\?\?)\s+(.+?)\s*$/gm);
    scan(/^Update\(([^)]+)\)/gm);
    scan(/(?:in|to)\s+([\w./_-]+\.(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl|css|js|jsx|ts|tsx|html))/gi);
    return out;
  }

  function dispatchAtlasFileChanged(path, tool) {
    if (!path) return;
    try {
      window.dispatchEvent(new CustomEvent('atlas-file-changed', {
        detail: { path, tool: tool || '' },
      }));
    } catch (_) {}
  }

  const _refFiles = debounce(() => refreshFileTree(window.SCOPE_PATH || '', { quiet: true }), 250);
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
      const eventMatchesActiveSession = (m, opts = {}) => {
        const eventSession = normalizeSessionName(
          (m && (m.session_id || m.session || m.namespace)) || ''
        );
        const activeSession = normalizeSessionName(
          window.ACTIVE_SESSION
          || (window.CONTEXT && (window.CONTEXT.activeSession || window.CONTEXT.active_session))
          || ''
        );
        if (!activeSession) return !opts.requireSession;
        if (!eventSession) return !opts.requireSession;
        return eventSession === activeSession;
      };
      const eventMatchesActiveCostScope = (m) => {
        if (eventMatchesActiveSession(m, { requireSession: true })) return true;
        const ctx = window.CONTEXT || {};
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
        if (!eventMatchesActiveSession(m, { requireSession: true })) return;
        const raw = Array.isArray(m && m.todos)
          ? m.todos
          : (m && m.todo_state && Array.isArray(m.todo_state.todos) ? m.todo_state.todos : null);
        if (raw) {
          window.TODOS = normalizeTodos(raw);
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'TODOS' }));
        }
        setTimeout(refreshTodos, 300);
      });
      window.backend.subscribe('tool_result', (m) => {
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
      window.backend.subscribe('file_changed', (m) => {
        if (!eventMatchesActiveSession(m, { requireSession: true })) return;
        _refFiles(); _refSsot();
        const paths = Array.isArray(m && m.paths)
          ? m.paths
          : ((m && m.path) ? [m.path] : []);
        paths.forEach(path => dispatchAtlasFileChanged(String(path || ''), (m && m.tool) || ''));
      });
      window.backend.subscribe('context', (m) => {
        if (!eventMatchesActiveSession(m, { requireSession: true })) return;
        let changed = false;
        if (typeof m.used === 'number') {
          window.CONTEXT.tokens = m.used;
          window.CONTEXT.maxTokens = m.max || window.CONTEXT.maxTokens;
          changed = true;
        }
        if (m.reasoning_effort) {
          window.CONTEXT.reasoningEffort = m.reasoning_effort;
          changed = true;
        }
        if (m.model) {
          window.CONTEXT.model = m.model;
          changed = true;
        }
        if (Array.isArray(m.model_options)) {
          window.CONTEXT.modelOptions = m.model_options;
          changed = true;
        }
        if (m.selected_model_key) {
          window.CONTEXT.selectedModelKey = m.selected_model_key;
          changed = true;
        }
        if (changed) window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
      });
      // Live cost — agent fires per-LLM-call. We accumulate into CONTEXT
      // so the sidebar reflects spend without waiting for the 5 s poll.
      window.backend.subscribe('cost', (m) => {
        if (!eventMatchesActiveCostScope(m)) return;
        const ctx = window.CONTEXT;
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
          return refreshActiveConversation(sid);
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
      window.backend.subscribe('flush', (m) => {
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
      refreshFileTree(window.SCOPE_PATH || '', { quiet: true });
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
