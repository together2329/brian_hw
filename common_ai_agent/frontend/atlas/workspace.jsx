// workspace.jsx — Chat-centric: ReAct + inline Q&A cards + SSOT/Todo sidebar + file viewer

// ── Tool-call visual theme ────────────────────────────────────────
// Each tool gets a glyph + accent color so a long chat can be
// visually scanned ("the agent just did 4 writes and a grep") at a
// glance. Used by ToolCard's left border + header glyph.
const TOOL_THEME = {
  write_file:        { glyph: '✏️',  color: '#3fb950' },  // green
  replace_in_file:   { glyph: '✏️',  color: '#3fb950' },
  replace_lines:     { glyph: '✏️',  color: '#3fb950' },
  read_file:         { glyph: '📄',  color: '#58a6ff' },  // blue
  read_lines:        { glyph: '📄',  color: '#58a6ff' },
  grep_file:         { glyph: '🔍',  color: '#d29922' },  // amber
  find_files:        { glyph: '🔍',  color: '#d29922' },
  list_dir:          { glyph: '🔍',  color: '#d29922' },
  run_command:       { glyph: '⚡',  color: '#a371f7' },  // purple
  todo_update:       { glyph: '☑',  color: '#39c5cf' },  // cyan
  todo_write:        { glyph: '☑',  color: '#39c5cf' },
  todo_add:          { glyph: '☑',  color: '#39c5cf' },
  todo_remove:       { glyph: '☑',  color: '#39c5cf' },
  todo_status:       { glyph: '☑',  color: '#39c5cf' },
  todo_note:         { glyph: '☑',  color: '#39c5cf' },
  scaffold_ip:       { glyph: '🛠️', color: '#f0883e' },  // orange
  ask_user:          { glyph: '⏸',  color: '#d29922' },
  read_doc:          { glyph: '📄',  color: '#58a6ff' },
  git_diff:          { glyph: '⚙',  color: '#a371f7' },
  git_status:        { glyph: '⚙',  color: '#a371f7' },
  __default:         { glyph: '▶',  color: 'var(--fg-mute)' },
};
const _toolTheme = (name) => TOOL_THEME[name] || TOOL_THEME.__default;

// Direct workflow/slash results also arrive as `slash_output`, which is the
// user-facing Markdown surface. Keep their mirrored `tool_result` event for
// data refresh subscribers, but do not render it again as a plain obs block.
const WORKFLOW_RESULT_TOOLS = new Set([
  'slash',
  'workflow',
  'import',
  'new-ip',
  'grill-me',
  'approve',
  'to-ssot',
  'resolve-rtl-blockers',
  'sim-debug',
  'repair-ssot',
  'repair-rtl',
  'repair-equiv',
  'validate-yaml',
  'ssot-fl-model',
  'ssot-equiv-goals',
  'ssot-rtl',
  'ssot-tb-cocotb',
  'ssot-tb',
  'ssot-tb-uvm',
  'ssot-tb-verilog',
  'ssot-tb-sv',
  'tb',
  'sim',
  'lint',
  'syn',
  'sta',
  'coverage',
  'goal-audit',
  'signoff',
]);
const _isWorkflowResultTool = (tool) => WORKFLOW_RESULT_TOOLS.has(String(tool || '').toLowerCase());
const INPUT_HISTORY_LIMIT = 200;

// Detect success/error in a tool result body. Used by ObsCard to
// stamp a leading ✓/✗ badge + override border color on errors.
const _obsStatus = (txt) => {
  const t = (txt || '').toLowerCase();
  if (/^\s*(error[:!]|\[error\]|✗|❌|\[plan mode\] .* blocked|exit code [1-9]|traceback|^exception:|fatal:)/m.test(t)) return 'err';
  if (/✓|^\s*ok\b|successfully|approved|wrote to|completed|matched|^✅|file does not exist/m.test(t)) {
    // "file does not exist" comes from read_file on a missing path —
    // ambiguous; lean neutral rather than green.
    if (/file does not exist|not found/m.test(t)) return 'neutral';
    return 'ok';
  }
  return 'neutral';
};

// Relative timestamp helper for hover-revealed "5m ago" labels.
const _relTime = (ts) => {
  if (!ts) return '';
  const d = Math.max(0, (Date.now() - ts) / 1000);
  if (d < 5) return 'just now';
  if (d < 60) return `${Math.floor(d)}s ago`;
  if (d < 3600) return `${Math.floor(d / 60)}m ago`;
  if (d < 86400) return `${Math.floor(d / 3600)}h ago`;
  return `${Math.floor(d / 86400)}d ago`;
};

const _unwrapAtlasOutputFence = (text) => {
  const raw = String(text || '');
  const trimmed = raw.trim();
  const m = trimmed.match(/^```(?:text|markdown|md)?\s*\n([\s\S]*?)\n```$/i);
  if (!m) return raw;
  const body = m[1].trim();
  if (/^\[(SSOT|MAS|SIM|ATLAS|APPROVED|Plan Mode|to-ssot|ssot-|repair-|resolve-|workflow|import|new-ip|grill|lint|syn|sta|coverage)\b/i.test(body)) {
    return body;
  }
  return raw;
};

const _markdownHtml = (text) => {
  const body = _unwrapAtlasOutputFence(text);
  const rawHtml = (typeof window.marked !== 'undefined' && window.marked.parse)
    ? window.marked.parse(body || '', { breaks: true, gfm: true })
    : renderInline(body || '');
  return (typeof window.DOMPurify !== 'undefined' && window.DOMPurify.sanitize)
    ? window.DOMPurify.sanitize(rawHtml, { ADD_ATTR: ['target', 'rel'] })
    : rawHtml;
};

const _postProcessMarkdownNode = (node) => {
  if (!node) return;
  node.querySelectorAll('a[href]').forEach(a => {
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener noreferrer');
  });
  if (window.Prism) {
    node.querySelectorAll('pre > code').forEach(c => {
      const has = (c.className || '').match(/\blanguage-/);
      if (!has) c.classList.add('language-none');
    });
    try { window.Prism.highlightAllUnder(node); } catch (_) {}
  }
};

// Hover-revealed copy button (positioned absolute; parent must be
// position:relative and apply CSS `:hover .copy-btn{opacity:1}`).
const CopyBtn = ({ text, label = 'copy' }) => {
  const [copied, setCopied] = React.useState(false);
  const onClick = (e) => {
    e.stopPropagation();
    try { navigator.clipboard.writeText(text || ''); setCopied(true); setTimeout(() => setCopied(false), 1200); }
    catch (_) {}
  };
  return (
    <button onClick={onClick} className="copy-btn" type="button"
      style={{
        position: 'absolute', top: 6, right: 6,
        opacity: 0, transition: 'opacity .15s',
        background: 'var(--bg-2)', border: '1px solid var(--line)',
        color: copied ? 'var(--ok)' : 'var(--fg-mute)',
        fontSize: 10, padding: '1px 6px', borderRadius: 2,
        cursor: 'pointer', fontFamily: 'var(--mono)',
      }}>
      {copied ? '✓ copied' : label}
    </button>
  );
};

// ── Column-resize helpers ─────────────────────────────────────────
// useResizable: state + localStorage persistence + clamp.
// `0` is the special "collapsed" value; any positive width is clamped
// to [minW, maxW]. A separate "lastNonZero" remembers the user's last
// open width so collapse → expand restores cleanly.
const useResizable = (initial, storageKey, minW, maxW, restoreCollapsed = true) => {
  const [w, setW] = React.useState(() => {
    try {
      const raw = parseInt(localStorage.getItem(storageKey), 10);
      if (Number.isFinite(raw) && raw === 0 && restoreCollapsed) {
        return 0;
      }
      if (Number.isFinite(raw) && raw >= minW) {
        return Math.min(maxW, raw);
      }
    } catch (_) {}
    return initial;
  });
  const lastOpenRef = React.useRef(w > 0 ? w : initial);
  React.useEffect(() => {
    if (w > 0) lastOpenRef.current = w;
    try { localStorage.setItem(storageKey, String(w)); } catch (_) {}
  }, [w, storageKey]);
  const set = React.useCallback((next) => {
    if (next === 0) { setW(0); return; }
    setW(Math.max(minW, Math.min(maxW, next)));
  }, [minW, maxW]);
  const toggle = React.useCallback(() => {
    setW(prev => prev === 0 ? lastOpenRef.current : 0);
  }, []);
  return [w, set, toggle];
};

// Splitter: 4px-wide drag handle. drag → resize via onResize(width).
// Double-click → onToggle(). Side='left' resizes the LEFT column
// (drag right widens), side='right' resizes the RIGHT column (drag
// left widens — direction inverted).
const Splitter = ({ width, side, onResize, onToggle }) => {
  const drag = React.useRef(null);
  const onMouseDown = (e) => {
    e.preventDefault();
    drag.current = { x: e.clientX, w0: width };
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
    const onMove = (ev) => {
      if (!drag.current) return;
      const dx = ev.clientX - drag.current.x;
      const next = side === 'left' ? drag.current.w0 + dx : drag.current.w0 - dx;
      onResize(next);
    };
    const onUp = () => {
      drag.current = null;
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };
  return (
    <div
      onMouseDown={onMouseDown}
      onDoubleClick={onToggle}
      title={'drag to resize · double-click to ' + (width === 0 ? 'expand' : 'collapse')}
      style={{
        cursor: 'col-resize',
        background: 'transparent',
        borderLeft: '1px solid var(--line)',
        borderRight: '1px solid var(--line)',
        height: '100%',
        transition: 'background 120ms',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'color-mix(in oklch, var(--accent) 30%, transparent)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    />
  );
};

const normalizeUiSession = (session) => {
  const norm = (window.atlasData && window.atlasData.normalizeSessionName) || window.normalizeAtlasSessionName;
  try { return norm ? norm(session || '') : ''; }
  catch (_) { return ''; }
};

const ssotIpFromSession = (session) => {
  const parts = normalizeUiSession(session).split('/').filter(Boolean);
  const idx = parts.lastIndexOf('ssot-gen');
  return idx > 0 ? parts[idx - 1] : '';
};

const Workspace = ({ dir, onScreen, uiLang = 'ko' }) => {
  // Two-axis mode model:
  //   intent: 'normal' | 'plan'   (top-level — shift+tab to swap)
  //   workflow: null | 'ssot' | 'rtl_gen' | 'lint' | 'tb_gen'
  const [intent, setIntent] = React.useState('normal');
  const [workflow, setWorkflow] = React.useState(null);

  // Column widths (drag-resizable, persisted in localStorage).
  // 0 = collapsed; any positive width is clamped to [min, max].
  const [leftW,  setLeftW,  toggleLeft]  = useResizable(230, 'atlasLeftW',  160, 480, false);
  const [rightW, setRightW, toggleRight] = useResizable(360, 'atlasRightW', 260, 600);

  // File-tree sort mode — 'name' (alphabetical, dirs first; default) or
  // 'recent' (most recently modified first, regardless of dir/file).
  // Persisted across reloads.
  const [fileSort, setFileSort] = React.useState(() => {
    try { return localStorage.getItem('atlasFileSort') === 'recent' ? 'recent' : 'name'; }
    catch (_) { return 'name'; }
  });
  React.useEffect(() => {
    try { localStorage.setItem('atlasFileSort', fileSort); } catch (_) {}
  }, [fileSort]);

  const NORMAL_FEED = [
    { kind: 'agent', text: 'Connected. Type a message and press Enter to talk to the agent.' },
  ];
  const PLAN_FEED = [
    { kind: 'agent', text: '**Plan mode** · read-only. The agent will analyze and propose without executing mutating tools. Use `apply` (or switch back to Normal) to run the plan.' },
  ];

  const resolveSession = React.useCallback((...candidates) => {
    for (const candidate of candidates) {
      try {
        const sid = normalizeUiSession(candidate || '');
        if (sid) return sid;
      } catch (_) {}
    }
    return 'default';
  }, []);

  const [feed, setFeed] = React.useState(NORMAL_FEED);
  const [activeSession, setActiveSession] = React.useState(() => {
    try {
      const sid = normalizeUiSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession')) || 'default';
      window.ACTIVE_SESSION = sid;
      try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
      return sid;
    } catch (_) {
      window.ACTIVE_SESSION = 'default';
      return 'default';
    }
  });

  const refreshFeed = (newIntent /*, newWorkflow */) => {
    // Do not reset the conversation on mode/workflow switches. The
    // authoritative history lives in .session/<workflow>/conversation.json
    // and is hydrated asynchronously; wiping the browser feed here makes
    // reloads and /wf transitions look like the session was lost.
    setFeed(f => (f && f.length ? f : (newIntent === 'plan' ? PLAN_FEED : NORMAL_FEED)));
  };

  const activateSession = React.useCallback((scopePath, wf) => {
    const rawSid = (window.atlasData && window.atlasData.sessionFor)
      ? window.atlasData.sessionFor(scopePath || window.SCOPE_PATH || '', wf || '')
      : 'default';
    const sid = resolveSession(rawSid);
    window.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (window.atlasData && window.atlasData.refreshSessionState) {
      window.atlasData.refreshSessionState(sid);
    }
    return sid;
  }, []);

  const sendPrompt = React.useCallback((text, sessionOverride) => {
    if (window.backend) {
      const session = resolveSession(sessionOverride, activeSession, window.ACTIVE_SESSION);
      window.backend.send({
        type: 'prompt',
        text,
        session,
        ui_lang: window.ATLAS_UI_LANG || uiLang,
      });
    }
  }, [activeSession, resolveSession, uiLang]);

  const switchToDefaultSession = React.useCallback(() => {
    const sid = (window.atlasData && window.atlasData.sessionFor)
      ? (window.atlasData.sessionFor('', '') || 'default')
      : 'default';
    window.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (window.atlasData && window.atlasData.refreshSessionState) {
      window.atlasData.refreshSessionState(sid);
    }
    return sid;
  }, []);

  const switchIntent = (i) => {
    setIntent(i);
    refreshFeed(i, workflow);
    // Tell the BACKEND about the mode swap — local React state alone
    // doesn't change the agent's behaviour. /plan flips agent_mode to
    // 'plan' (no mutating tools); /mode normal flips it back.
    if (window.backend) {
      const cmd = i === 'plan' ? '/plan' : '/mode normal';
      sendPrompt(cmd);
    }
  };
  const switchWorkflow = (w) => {
    // Click a workflow chip → fire `/wf <name>` to actually swap the
    // agent's workspace on the server. The slash command is processed
    // locally by the dispatcher (no LLM call) and re-registers the
    // workspace's slash commands. Clicking the active chip exits back
    // to default on both the UI and backend; otherwise CONTEXT refresh
    // can re-enter the old workflow after local React state cleared.
    const next = workflow === w ? null : w;
    setWorkflow(next);
    refreshFeed(intent, next);
    const sid = activateSession(window.SCOPE_PATH || '', next || '');
    if (window.backend) {
      sendPrompt(next ? `/wf ${next}` : '/workflow default', sid);
    }
  };
  const [input, setInput] = React.useState('');
  const [inputHistory, setInputHistory] = React.useState(() => {
    try {
      const raw = localStorage.getItem('atlasInputHistory');
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed)
        ? parsed.filter(x => typeof x === 'string' && x.trim()).slice(-INPUT_HISTORY_LIMIT)
        : [];
    } catch (_) {
      return [];
    }
  });
  const inputHistoryIndexRef = React.useRef(null);
  const inputHistoryDraftRef = React.useRef('');
  const [showSlash, setShowSlash] = React.useState(false);
  const [slashSel, setSlashSel] = React.useState(0);
  const [streaming, setStreaming] = React.useState(false);
  const streamingRef = React.useRef(false);
  const streamBufferRef = React.useRef('');
  React.useEffect(() => { streamingRef.current = streaming; }, [streaming]);
  const [backendState, setBackendState] = React.useState(() => {
    if (!window.backend) return 'missing';
    return window.backend.getConnectionState ? window.backend.getConnectionState() : 'connecting';
  });
  const [streamText, setStreamText] = React.useState('');
  const [openFile, setOpenFile] = React.useState(null);
  const [rightTab, setRightTab] = React.useState('progress'); // progress | todo | git
  // Main column tab: 'chat' shows the conversation feed; 'preview' shows
  // the contents of the file at previewPath with syntax highlighting;
  // 'split' keeps chat and preview visible side-by-side.
  // 'qa' is only available when centerLayout === 'tabbed' — it surfaces
  // the dedicated ask_user pane with breadcrumb-tabbed batched questions.
  // Double-clicking a file in the left tree sets previewPath + flips tab.
  const [mainTab, setMainTab] = React.useState('chat');     // chat | preview | split | qa
  const [previewPath, setPreviewPath] = React.useState(null);
  // Center layout: 'classic' (chat with inline ask_user) or 'tabbed'
  // (Chat / Preview / Q&A tab strip with auto-switch). Comes from the
  // server hello payload (driven by ATLAS_CENTER_LAYOUT in .config).
  const [centerLayout, setCenterLayout] = React.useState('classic');
  // qaState is keyed by flow_id. Dynamic flows are added on-the-fly
  // when the agent emits an ask_user event over the WS.
  const [qaState, setQaState] = React.useState({});
  // qaHistory: every submitted ask_user round-trip, newest first.
  // Each entry is {flowId, ts, ip, workflow, source, items: [{
  //   question, kind, selected: [{id,label}], custom
  // }, ...]}. Persisted in localStorage so refreshing the tab keeps
  // the trail visible. The Q&A tab renders this above the SSOT board.
  const [qaHistory, setQaHistory] = React.useState(() => {
    try {
      const raw = localStorage.getItem('atlasQaHistory');
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed.slice(0, 50) : [];
    } catch (_) { return []; }
  });
  React.useEffect(() => {
    try { localStorage.setItem('atlasQaHistory', JSON.stringify(qaHistory.slice(0, 50))); } catch (_) {}
  }, [qaHistory]);
  const [ssotApproval, setSsotApproval] = React.useState(null);
  const [ssotQa, setSsotQa] = React.useState(null);
  const [ssotQaSessions, setSsotQaSessions] = React.useState([]);

  const replaceInputHistory = React.useCallback((items) => {
    const cleaned = (Array.isArray(items) ? items : [])
      .filter(x => typeof x === 'string' && x.trim())
      .slice(-INPUT_HISTORY_LIMIT);
    setInputHistory(cleaned);
    try { localStorage.setItem('atlasInputHistory', JSON.stringify(cleaned)); } catch (_) {}
  }, []);

  React.useEffect(() => {
    let alive = true;
    fetch('/api/input-history?limit=' + INPUT_HISTORY_LIMIT, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!alive || !d || !Array.isArray(d.history)) return;
        replaceInputHistory(d.history);
      })
      .catch(() => {});
    return () => { alive = false; };
  }, [replaceInputHistory]);

  const recordInputHistory = React.useCallback((raw) => {
    const text = String(raw || '').trim();
    if (!text) return;
    inputHistoryIndexRef.current = null;
    inputHistoryDraftRef.current = '';
    setInputHistory(prev => {
      const next = [...prev, text].slice(-INPUT_HISTORY_LIMIT);
      try { localStorage.setItem('atlasInputHistory', JSON.stringify(next)); } catch (_) {}
      return next;
    });
    fetch('/api/input-history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }).catch(() => {});
  }, []);

  const currentSession = React.useMemo(
    () => resolveSession(activeSession, window.ACTIVE_SESSION),
    [activeSession, resolveSession],
  );

  const activeSsotIp = React.useCallback(() => {
    const fromSession = ssotIpFromSession(currentSession || window.ACTIVE_SESSION);
    if (fromSession) return fromSession;
    const scoped = String(window.SCOPE_PATH || '').split('/').filter(Boolean).pop() || '';
    return /^[A-Za-z][A-Za-z0-9_]*$/.test(scoped) ? scoped : '';
  }, [currentSession]);

  const refreshSsotQa = React.useCallback(async (sessionOverride) => {
    const session = normalizeUiSession(sessionOverride || currentSession || window.ACTIVE_SESSION || '');
    const ip = ssotIpFromSession(session) || activeSsotIp();
    if (!ip) {
      setSsotQa({ ip: '', toc: [], sections: [], summary: { total: 0, approved: 0, pending: 0 } });
      return null;
    }
    try {
      const qs = new URLSearchParams({ ip });
      if (session) qs.set('session', session);
      const r = await fetch('/api/ssot/qa?' + qs.toString());
      if (!r.ok) return null;
      const d = await r.json();
      setSsotQa(d);
      return d;
    } catch (_) {
      return null;
    }
  }, [activeSsotIp, currentSession]);

  const refreshSsotQaSessions = React.useCallback(async () => {
    try {
      const r = await fetch('/api/ssot/qa/sessions', { cache: 'no-store' });
      if (!r.ok) return null;
      const d = await r.json();
      const rows = Array.isArray(d.sessions) ? d.sessions : [];
      setSsotQaSessions(rows);
      return rows;
    } catch (_) {
      return null;
    }
  }, []);

  const activateSsotQaSession = React.useCallback((row) => {
    const sid = normalizeUiSession(row?.session || '');
    if (!sid) return;
    window.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (row?.ip && window.atlasData?.setScopePath) {
      window.atlasData.setScopePath(row.ip);
    }
    if (window.atlasData?.refreshSessionState) {
      window.atlasData.refreshSessionState(sid);
    }
    setWorkflow('ssot-gen');
    refreshSsotQa(sid);
  }, [refreshSsotQa]);

  const flowMatchesCurrentSession = React.useCallback((flowId, eventSession) => {
    const flow = window.QA_FLOWS && window.QA_FLOWS[flowId];
    const flowSession = normalizeUiSession(eventSession || (flow && flow.session) || '');
    const active = normalizeUiSession(currentSession || window.ACTIVE_SESSION || '');
    if (!flowSession || !active || flowSession === active) return true;
    const flowParts = flowSession.split('/').filter(Boolean);
    const activeParts = active.split('/').filter(Boolean);
    const minLen = Math.min(flowParts.length, activeParts.length);
    if (minLen < 2) return false;
    return flowParts.slice(-minLen).join('/') === activeParts.slice(-minLen).join('/');
  }, [currentSession]);

  const activateAskUserSession = React.useCallback((session, ip, eventWorkflow) => {
    const sid = normalizeUiSession(session || '');
    if (!sid) return;
    if (flowMatchesCurrentSession('', sid)) return;
    window.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (ip && window.atlasData?.setScopePath) {
      window.atlasData.setScopePath(ip);
    }
    if (eventWorkflow) {
      setWorkflow(eventWorkflow);
    }
    if (window.atlasData?.refreshSessionState) {
      window.atlasData.refreshSessionState(sid, false);
    }
  }, [flowMatchesCurrentSession]);

  // Force a re-render when the live data layer (data.jsx) refreshes
  // FILE_TREE / TODOS / SSOT_FILES so dependent panels show fresh data.
  const [, bumpRender] = React.useReducer(x => x + 1, 0);
  React.useEffect(() => {
    const h = () => bumpRender();
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  React.useEffect(() => {
    refreshSsotQa();
    refreshSsotQaSessions();
    const h = (ev) => {
      if (!ev.detail || ['SESSION_STATE', 'SCOPE_PATH', 'SSOT_QA', 'SSOT_FILES'].includes(ev.detail)) {
        refreshSsotQa();
        refreshSsotQaSessions();
      }
    };
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, [refreshSsotQa, refreshSsotQaSessions]);

  React.useEffect(() => {
    const onData = (ev) => {
      if (ev.detail === 'CONTEXT' || ev.detail === 'FLOW_STAGES') {
        const backendWorkflow = (window.CONTEXT && window.CONTEXT.workspace) || '';
        const known = (window.FLOW_STAGES || []).some(s => s.id === backendWorkflow);
        if (!backendWorkflow || backendWorkflow === 'default') {
          setWorkflow(null);
        } else if (known) {
          setWorkflow(backendWorkflow);
        }
      }
      if (ev.detail === 'SCOPE_PATH') {
        const activeParts = normalizeUiSession(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
        const activeWorkflow = (window.FLOW_STAGES || []).some(s => s.id === activeParts[activeParts.length - 1])
          ? activeParts[activeParts.length - 1]
          : '';
        activateSession(window.SCOPE_PATH || '', activeWorkflow || workflow || (window.CONTEXT && window.CONTEXT.workspace) || '');
      }
    };
    onData({ detail: 'CONTEXT' });
    window.addEventListener('atlas-data-changed', onData);
    return () => window.removeEventListener('atlas-data-changed', onData);
  }, [activateSession, workflow]);

  // Hydrate the chat feed from the active .session/<scope>/<workflow>
  // conversation.json. data.jsx fires 'atlas-conversation-loaded' after
  // active session changes so screen switches do not erase chat history.
  React.useEffect(() => {
    const onConvLoaded = (ev) => {
      const msgs = (ev.detail && ev.detail.messages) || [];
      const session = ev.detail && ev.detail.session;
      if (session) setActiveSession(session);
      if (streamingRef.current || (streamBufferRef.current || '').trim()) {
        return;
      }
      const newFeed = [];
      for (const m of msgs) {
        const role = m.role;
        const content = typeof m.content === 'string' ? m.content
          : Array.isArray(m.content) ? m.content.map(c => c.text || '').join('')
          : '';
        if (role === 'user' && content) {
          newFeed.push({ kind: 'user', text: content });
        } else if (role === 'assistant') {
          // assistant message may have content + tool_calls
          if (content && content.trim()) {
            newFeed.push({ kind: 'agent', text: content });
          }
          if (Array.isArray(m.tool_calls)) {
            for (const tc of m.tool_calls) {
              const fn = (tc.function && tc.function.name) || tc.name || '?';
              const args = (tc.function && tc.function.arguments) || tc.arguments || '';
              const argsShort = typeof args === 'string'
                ? args.slice(0, 120)
                : JSON.stringify(args).slice(0, 120);
              // Stamp `tool` so the render-time pre-pass can pair this
              // hydrated action with the next 'tool'-role obs into a
              // single ToolCard (matching the live shape).
              newFeed.push({ kind: 'action', text: `▶ ${fn} ${argsShort}`, tool: fn, args: argsShort });
            }
          }
        } else if (role === 'tool' && content) {
          newFeed.push({
            kind: 'obs',
            text: content.slice(0, 8000),
            tool: m.name || '',
            truncated: content.length > 8000,
          });
        }
      }
      // Drop a turn-end divider so the user can tell where the
      // hydrated history ends and live tokens begin.
      if (newFeed.length) {
        newFeed.push({
          kind: 'turn_end',
          text: `↓ live (${session ? `.session/${session}` : 'session history'} above) ↓`,
        });
      }
      // Always replace the feed on namespace change — even when the
      // new namespace has zero messages on disk yet. Previously we
      // only replaced on non-empty results, which left the OLD feed
      // visible when switching to a fresh ssot-gen / rtl-gen workflow
      // and made it look like "session, ip, workflow별 conversation
      // 분리"가 무시된 것처럼 보였다. Empty new namespace → empty
      // feed (no fake "Agent: .session/..." placeholder; the path
      // leaked internal info and the message was misleadingly
      // attributed to the agent).
      setFeed(newFeed);
    };
    window.addEventListener('atlas-conversation-loaded', onConvLoaded);
    return () => window.removeEventListener('atlas-conversation-loaded', onConvLoaded);
  }, []);

  const inputRef = React.useRef(null);
  const feedRef = React.useRef(null);

  // Derived: the latest unsubmitted qcard. Live ask_user normally appends
  // a qcard to the chat feed, but session-history hydration can replace
  // the feed after a reconnect. Keep Q&A visible from qaState as the
  // authoritative pending-flow state.
  const pendingQcard = React.useMemo(() => {
    for (let i = feed.length - 1; i >= 0; i--) {
      const e = feed[i];
      if (e.kind === 'qcard' && !qaState[e.flowId]?.submitted && flowMatchesCurrentSession(e.flowId)) return e;
    }
    const flowIds = Object.keys(qaState || {});
    for (let i = flowIds.length - 1; i >= 0; i--) {
      const flowId = flowIds[i];
      if (!qaState[flowId]?.submitted && window.QA_FLOWS && window.QA_FLOWS[flowId] && flowMatchesCurrentSession(flowId)) {
        return { kind: 'qcard', flowId, dynamic: true };
      }
    }
    return null;
  }, [feed, qaState, flowMatchesCurrentSession]);

  // Tabbed center layout — auto-switch to Q&A tab when ask_user fires,
  // and back to chat after the user submits.  Classic layout ignores
  // mainTab='qa' entirely (still routes ask_user inline below the feed).
  const _qcardActiveFlow = pendingQcard?.flowId || null;
  const _qcardSubmitted = !!(pendingQcard && qaState[pendingQcard.flowId]?.submitted);
  React.useEffect(() => {
    if (centerLayout !== 'tabbed') return;
    if (_qcardActiveFlow && !_qcardSubmitted && mainTab !== 'qa') {
      setMainTab('qa');
    } else if (!_qcardActiveFlow && mainTab === 'qa') {
      setMainTab('chat');
    }
  }, [centerLayout, _qcardActiveFlow, _qcardSubmitted]);

  // Keyboard navigation cursor for the ask_user inline form.
  // Index space: 0..opts.length-1 = option rows, opts.length = custom-text row,
  // opts.length+1 = Submit, opts.length+2 = "Chat about this".
  const [askSel, setAskSel] = React.useState(0);
  const pendingQcardActiveTab = pendingQcard
    ? (qaState[pendingQcard.flowId]?.active || 0)
    : 0;
  React.useEffect(() => { setAskSel(0); }, [pendingQcard?.flowId, pendingQcardActiveTab]);

  // Auto-focus the ask_user prompt area when one opens
  React.useEffect(() => {
    if (pendingQcard) {
      setTimeout(() => {
        const el = document.querySelector('.ask-prompt');
        el?.focus();
      }, 30);
    }
  }, [pendingQcard?.flowId]);

  // ── @ file completion (Python-style, one path segment at a time) ──
  // Find a trailing "@<query>" token (anywhere in the input). The
  // query is everything after the LAST `@` to the end of the line.
  // We split the query into (parentDir, filter): everything up to the
  // last '/' is the directory the user is browsing; everything after
  // is the prefix to match against entries in that directory.
  //
  //   "@"               → parent='',         filter=''       → list project root
  //   "@workflow/"      → parent='workflow', filter=''       → list workflow/
  //   "@workflow/ssot"  → parent='workflow', filter='ssot'   → workflow/ filtered by 'ssot'
  //   "@a/b/c"          → parent='a/b',      filter='c'      → a/b/ filtered by 'c'
  const atQuery = React.useMemo(() => {
    const m = input.match(/(^|\s)@([^\s]*)$/);
    if (!m) return null;
    const raw = m[2];
    const slash = raw.lastIndexOf('/');
    const parentRel = slash >= 0 ? raw.slice(0, slash) : '';
    const filter    = slash >= 0 ? raw.slice(slash + 1) : raw;
    // @-completion is always project-root-relative — independent of
    // SCOPE_PATH, which only narrows the file-tree panel. The token
    // that ends up in the chat must be a full project-root-relative
    // path so the agent can resolve it without knowing about scope.
    return {
      token: '@' + raw,
      pos: m.index + m[1].length,
      raw,
      parentRel,
      parentAbs: parentRel,  // project-root-relative
      filter: filter.toLowerCase(),
    };
  }, [input]);

  // Cache directory listings keyed by absolute path so chaining
  // ("@a/" → "@a/b/" → "@a/b/c/") doesn't refetch each segment.
  const [atDirCache, setAtDirCache] = React.useState({});
  const [atDirEntries, setAtDirEntries] = React.useState([]);

  React.useEffect(() => {
    if (!atQuery) { setAtDirEntries([]); return; }
    const key = atQuery.parentAbs;
    if (atDirCache[key]) { setAtDirEntries(atDirCache[key]); return; }
    let cancelled = false;
    fetch('/api/files?path=' + encodeURIComponent(key))
      .then(r => r.json())
      .then(d => {
        if (cancelled) return;
        const entries = (d && d.entries) || [];
        setAtDirCache(c => ({ ...c, [key]: entries }));
        setAtDirEntries(entries);
      })
      .catch(() => { if (!cancelled) setAtDirEntries([]); });
    return () => { cancelled = true; };
  }, [atQuery && atQuery.parentAbs]);

  const fileMatches = React.useMemo(() => {
    if (!atQuery) return [];
    const f = atQuery.filter;
    const list = !f
      ? atDirEntries
      : atDirEntries.filter(e => e.name.toLowerCase().startsWith(f));
    return list.slice(0, 30);
  }, [atQuery && atQuery.filter, atDirEntries]);

  const filtered = React.useMemo(() => {
    if (!input.startsWith('/')) return [];
    const q = input.slice(1).toLowerCase();
    return window.SLASH_COMMANDS.filter(c =>
      c.cmd.slice(1).toLowerCase().startsWith(q) || c.alias.startsWith(q)
    );
  }, [input]);

  const [showAt, setShowAt] = React.useState(false);
  const [atSel, setAtSel] = React.useState(0);

  React.useEffect(() => {
    if (input.startsWith('/')) { setShowSlash(true); setSlashSel(0); setShowAt(false); }
    else setShowSlash(false);
    // Keep the @ popup open as long as the user is in an @-token —
    // even when matches are momentarily empty (chaining into a new
    // dir takes one fetch round-trip). Closing on empty would flicker.
    if (atQuery) { setShowAt(true); setAtSel(0); }
    else setShowAt(false);
  }, [input, atQuery && atQuery.parentAbs, atQuery && atQuery.filter]);

  const acceptAtCompletion = (entry) => {
    if (!atQuery) return;
    const before = input.slice(0, atQuery.pos);
    const after  = input.slice(atQuery.pos + atQuery.token.length);
    // Replace only the filter portion of the @-token, keeping the
    // parent path the user already typed. So "@workflow/s" + selecting
    // "ssot-gen/" becomes "@workflow/ssot-gen/" (popup stays open and
    // shows ssot-gen's contents next), while selecting a file appends
    // a trailing space and closes the popup.
    const parent = atQuery.parentRel ? atQuery.parentRel + '/' : '';
    if (entry.type === 'dir') {
      // Chain into the directory — popup re-opens with its contents
      // because the new query ends in '/'.
      setInput(before + '@' + parent + entry.name + '/' + after);
      // Keep showAt true; the effect that listens to atQuery will
      // refetch the new directory's entries automatically.
    } else {
      setInput(before + '@' + parent + entry.name + ' ' + after);
      setShowAt(false);
    }
  };

  React.useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [feed, streamText, mainTab]);

  // shift+tab swaps Normal ↔ Plan. Fire even when the chat input is
  // focused — the input is auto-focused, so the old "tagName !== INPUT"
  // guard meant the shortcut never triggered. e.preventDefault stops
  // the browser's native focus-walk regardless.
  React.useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Tab' && e.shiftKey) {
        e.preventDefault();
        switchIntent(intent === 'normal' ? 'plan' : 'normal');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [intent, workflow]);

  // ── chat actions ───────────────────────────────────────────────
  const submitMsg = (cmd) => {
    const raw = (cmd ?? input).trim();
    if (!raw) return;
    recordInputHistory(raw);
    setInput('');
    setShowSlash(false);

    // ── Client-side slash commands ──────────────────────────────
    // Some commands operate on browser state (SCOPE_PATH lives in
    // localStorage / window) and don't need an agent round-trip.
    // Handle them here BEFORE sending anything to the backend.
    const sessionMatch = raw.match(/^\/(session|sess)(\s+(.*))?$/);
    if (sessionMatch) {
      const arg = (sessionMatch[3] || '').trim();
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      const _clearStreaming = () => {
        setStreaming(false);
        streamBufferRef.current = '';
        setStreamText('');
      };
      if (!arg) {
        setFeed(f => [...f, {
          kind: 'agent',
          text: `Current session: \`${activeSession || window.ACTIVE_SESSION || 'default'}\`\nUse \`/session default\` to return to the default session.`,
        }]);
        _clearStreaming();
        return;
      }
      if (arg.toLowerCase() === 'default') {
        const sid = switchToDefaultSession();
        setFeed(f => [...f, { kind: 'agent', text: `Session set to \`${sid}\`.` }]);
        _clearStreaming();
        return;
      }
      const sid = resolveSession(arg, activeSession, window.ACTIVE_SESSION);
      window.ACTIVE_SESSION = sid;
      setActiveSession(sid);
      try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
      if (window.atlasData && window.atlasData.refreshSessionState) {
        window.atlasData.refreshSessionState(sid);
      }
      setFeed(f => [...f, { kind: 'agent', text: `Session set to \`${sid}\`.` }]);
      _clearStreaming();
      return;
    }

    const m = raw.match(/^\/(scope|cd)(\s+(.*))?$/);
    if (m) {
      const arg = (m[3] || '').trim();
      const cur = window.SCOPE_PATH || '';
      // Same defensive cleanup as the /plan branch — these commands
      // are purely client-side and shouldn't inherit a stale
      // streaming state from a prior unclean turn.
      const _clearStreaming = () => {
        setStreaming(false);
        streamBufferRef.current = '';
        setStreamText('');
      };
      if (!arg) {
        setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
        setFeed(f => [...f, {
          kind: 'agent',
          text: cur
            ? `Current scope: \`${cur}\`\nUse \`/scope <path>\` to change, \`/scope /\` to reset.`
            : 'No scope set — agent works on the whole project.\nUse `/scope <path>` to confine it.',
        }]);
        _clearStreaming();
        return;
      }
      const next = (arg === '/' || arg === '~' || arg === '-') ? '' : arg.replace(/^\/+|\/+$/g, '');
      window.atlasData.setScopePath(next);
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      setFeed(f => [...f, {
        kind: 'agent',
        text: next
          ? `✓ Scope set to \`${next}\`. Future prompts will tell the agent to stay inside this directory.`
          : '✓ Scope cleared. Agent operates on the whole project again.',
      }]);
      _clearStreaming();
      return;
    }

    // /plan, /normal, /mode plan, /mode normal — flip UI intent locally
    // AND forward to backend so agent_mode flips. Mirrors the /scope
    // pattern. Without this, /plan only updated the backend and the
    // sidebar pill stayed on "normal" until shift+tab (also broken).
    //
    // Backend slash registry: '/plan' and '/mode <x>' are registered.
    // '/normal' (without /mode prefix) is NOT registered → would land
    // as "Unknown command" and leave agent_mode in plan_q while the
    // UI happily flipped to normal. Normalize the WIRE form to the
    // canonical command the backend actually handles.
    const modeMatch = raw.match(/^\/(plan|mode\s+plan|mode\s+normal|normal)$/i);
    if (modeMatch) {
      const target = /^\/(plan|mode\s+plan)$/i.test(raw) ? 'plan' : 'normal';
      const wire = target === 'plan' ? '/plan' : '/mode normal';
      setIntent(target);
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      sendPrompt(wire);
      // Slash commands don't run the agent — clear any stale streaming
      // state inherited from a prior turn that didn't close out cleanly
      // (agent crash, dropped WS, etc.). Without this, the banner
      // leaves the running status stuck after the user types /plan.
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    setFeed(f => [...f, { kind: 'user', text: raw }]);
    setStreaming(true);
    setStreamText('');
    // Prepend a scope-restriction directive so the agent is forced to
    // operate inside the user's selected directory. Slash commands
    // bypass the prefix because they hit the local dispatcher first.
    // Confirmation tokens (y / yc / yes / n / cancel / ok …) ALSO
    // bypass — chat_loop's plan-confirmation handler does an exact
    // `inp.lower().strip() in ("y", "yes", ...)` match, and the
    // "[scope] You MUST..." prefix breaks that comparison so plan
    // mode never exits even after the user types `y`. Keep these
    // short tokens unprefixed.
    const isConfirmation = /^(y|yc|yes|n|no|confirm|cancel|ok|proceed|ㅇㅇ|ㄴㄴ|확인|진행|취소|네|예|아니오)$/i.test(raw);
    const scope = (window.SCOPE_PATH || '').trim();
    let outbound = raw;
    if (scope && !raw.startsWith('/') && !isConfirmation) {
      outbound = (
        `[scope] You MUST confine every file read, write, edit, grep, ` +
        `find, and run_command to paths inside "${scope}". Do not touch ` +
        `files outside this directory unless I explicitly say so.\n\n` +
        raw
      );
    }
    sendPrompt(outbound);
  };

  // Subscribe to backend events and translate them into feed entries.
  React.useEffect(() => {
    if (!window.backend) {
      setBackendState('missing');
      setStreaming(false);
      return;
    }
    if (window.backend.getConnectionState) {
      setBackendState(window.backend.getConnectionState());
    }
    const subs = [];
    // Hello payload — server tells us which center-column layout the
    // user has configured (.config: ATLAS_CENTER_LAYOUT=classic|tabbed).
    subs.push(window.backend.subscribe('hello', (m) => {
      if (m && (m.center_layout === 'tabbed' || m.center_layout === 'classic')) {
        setCenterLayout(m.center_layout);
      }
      if (m && typeof m.running === 'boolean') {
        setStreaming(!!m.running);
      }
    }));
    subs.push(window.backend.subscribe('connection', (m) => {
      const state = (m && m.state) || '';
      setBackendState(state || 'unknown');
      if (state === 'closed' || state === 'error') {
        streamBufferRef.current = '';
        setStreamText('');
        setStreaming(false);
      }
    }));
    subs.push(window.backend.subscribe('token', (m) => {
      const t = m.text || '';
      if (!t || t === '\x00') return;  // skip sentinel
      streamBufferRef.current += t;
      setStreamText(streamBufferRef.current);
    }));
    subs.push(window.backend.subscribe('reasoning', (m) => {
      const t = (m.text || '').trim();
      if (!t) return;
      // Coalesce consecutive reasoning lines into ONE thought block —
      // the agent emits one chunk per sentence, which floods the chat
      // with 10+ THOUGHT entries per turn. We append to the last
      // entry if it's still a thought, otherwise create a new one.
      setFeed(l => {
        const last = l[l.length - 1];
        if (last && last.kind === 'thought') {
          return [...l.slice(0, -1),
                  { kind: 'thought', text: last.text + '\n' + t, createdAt: last.createdAt || Date.now() }];
        }
        return [...l, { kind: 'thought', text: t, createdAt: Date.now() }];
      });
    }));
    // todo_line: react_loop emits a full TodoTracker.format_simple() dump
    // on every iteration and after every tool call (see react_loop.py),
    // which previously flooded the chat feed with redundant "OBS TODO"
    // status blocks. The right-sidebar <TodoPanel/> already renders the
    // authoritative live state via /api/todos (data.jsx subscribes to
    // todo_line for refresh), so swallow the event here and keep the
    // chat for messages/tool_result only.
    // Tool call header: agent is about to invoke a tool.
    subs.push(window.backend.subscribe('tool', (m) => {
      const t = (m.text || '').trim();
      if (!t) return;
      // Detect the per-iteration banner (── Iter N / M  [model]) and
      // route to a thinner iter_marker kind so the feed doesn't break
      // tool action+obs cards with a full-width separator.
      const iterMatch = t.match(/^──\s*Iter\s+(\d+)\s*\/\s*(\d+)\s*\[([^\]]+)\]/);
      if (iterMatch) {
        setFeed(l => [...l, {
          kind: 'iter_marker',
          n: parseInt(iterMatch[1], 10),
          max: parseInt(iterMatch[2], 10),
          model: iterMatch[3].trim(),
          createdAt: Date.now(),
        }]);
        return;
      }
      // Finalize any pending streaming text first so the tool-call entry
      // sits AFTER the pre-tool reasoning/agent text in the feed.
      const buf = streamBufferRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf, createdAt: Date.now() }]);
      streamBufferRef.current = '';
      setStreamText('');
      // Parse "▶ tool_name  args…" → capture tool name so ToolCard can
      // pair this with its tool_result obs and pick a theme color.
      const am = t.match(/^▶\s*(\S+)\s*(.*)$/);
      const toolName = am ? am[1] : '';
      const argsText = am ? (am[2] || '').trim() : '';
      setFeed(l => [...l, {
        kind: 'action',
        text: t,
        tool: toolName,
        args: argsText,
        createdAt: Date.now(),
      }]);
    }));
    // Tool observation: the result the agent just received from the tool.
    subs.push(window.backend.subscribe('tool_result', (m) => {
      const t = (m.text || '').trim();
      if (!t) return;
      if (_isWorkflowResultTool(m.tool || '')) return;
      setFeed(l => [...l, {
        kind: 'obs',
        text: t,
        tool: m.tool || '',
        truncated: !!m.truncated,
        createdAt: Date.now(),
      }]);
    }));
    // Park the in-progress streaming buffer into the feed without
    // touching the streaming flag — flush fires AFTER EACH iteration,
    // not just at turn end, so the spinner must keep going until
    // agent_state(running:false) explicitly says we're done.
    const parkBuffer = () => {
      const buf = streamBufferRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf, createdAt: Date.now() }]);
      streamBufferRef.current = '';
      setStreamText('');
    };
    const turnEnd = () => {
      parkBuffer();
      setStreaming(false);
      // Drop a visible divider in the feed so the user can scroll back
      // and see exactly where each turn ended. Skip if the previous
      // entry is already a turn_end (defensive — flush + done can both
      // call this in close succession).
      setFeed(l => {
        const last = l[l.length - 1];
        if (last && last.kind === 'turn_end') return l;
        return [...l, { kind: 'turn_end', text: '✓ end of loop', createdAt: Date.now() }];
      });
    };
    // Mode flip from backend (chat_loop auto-promotes plan_q→normal when
    // the user types "y" to confirm). Sync the UI pill so it doesn't
    // stay stuck on PLAN while the agent is already executing writes.
    subs.push(window.backend.subscribe('mode_change', (m) => {
      const target = (m.mode || '').toLowerCase();
      if (target === 'normal' || target === 'plan') {
        setIntent(target);
      }
    }));

    // Safety-net feed entry for slash command output. Backend mirrors the
    // fenced output via both the token+flush pipeline and this event; we
    // dedupe by checking streamBufferRef (normal case: token fired first)
    // AND the feed's last agent entry (edge case: flush already parked the
    // buffer and cleared it before this event arrived).
    subs.push(window.backend.subscribe('slash_output', (m) => {
      const t = m.text || '';
      if (!t) return;
      const shown = _unwrapAtlasOutputFence(t);
      // Fast path — token landed in the buffer before us (new emit order).
      const buf = streamBufferRef.current;
      if (buf && (buf.indexOf(t) >= 0 || buf.indexOf(shown) >= 0)) return;
      // Slow path — flush may have already parked the buffer. Check if the
      // last agent entry in the feed is a duplicate.
      let dup = false;
      setFeed(l => {
        const last = l[l.length - 1];
        if (last && last.kind === 'agent' && (last.text === t || last.text === shown)) {
          dup = true;
          return l;
        }
        return [...l, { kind: 'agent', text: shown, createdAt: Date.now(), fromSlash: true }];
      });
      if (dup) return;
      streamBufferRef.current = '';
      setStreamText('');
    }));
    subs.push(window.backend.subscribe('flush', parkBuffer));
    subs.push(window.backend.subscribe('done', turnEnd));
    subs.push(window.backend.subscribe('agent_state', (m) => {
      if (m.running === false) turnEnd();
      else if (m.running === true) setStreaming(true);
    }));
    subs.push(window.backend.subscribe('error', (m) => {
      setFeed(l => [...l, { kind: 'agent', text: `[error] ${m.message || ''}`, createdAt: Date.now() }]);
      streamBufferRef.current = '';
      setStreamText('');
      setStreaming(false);
    }));
    // ask_user → register a dynamic flow and append a qcard to the feed.
    // Two payload shapes:
    //   • Single  : {question, kind, options, subtitle}
    //   • Batched : {questions: [{question, kind, options, subtitle}, ...]}
    // Batched mirrors the textual UI's ask_user breadcrumb-tab flow:
    // the user sees N tabs (☐/☒ marker per tab + a final ✔ Submit tab),
    // fills each, then submits all answers in one round-trip.
    subs.push(window.backend.subscribe('ask_user', (m) => {
      const flowId = m.flow_id;
      if (!flowId) return;
      activateAskUserSession(m.session, m.ip, m.workflow);
      streamBufferRef.current = '';
      setStreamText('');
      setStreaming(false);
      const isBatched = Array.isArray(m.questions) && m.questions.length > 0;
      // Multi-question (batched) ask_user is awkward to answer in the
      // classic-layout inline-bottom slot — N stacked questions with
      // option lists overflow the input area. Promote to the tabbed
      // Q&A pane so the user gets the full center column for the
      // batch. Single-question flows stay inline (fits fine there).
      if (isBatched) {
        setCenterLayout('tabbed');
        setMainTab('qa');
      }
      if (isBatched) {
        const qs = m.questions.map(q => ({
          question: q.question || '',
          kind: q.kind === 'multi' ? 'multi'
              : q.kind === 'input' ? 'input' : 'single',
          subtitle: q.subtitle || '',
          placeholder: q.placeholder || '',
          multiline: !!q.multiline || String(q.placeholder || '').includes('\n'),
          options: (q.options || []).map(o => ({
            id: o.id, label: o.label, detail: o.detail || '', selected: false,
          })),
        }));
        window.QA_FLOWS[flowId] = {
          stage: 'Agent', stageDetail: 'ask_user',
          title: qs[0].question || 'Questions',
          step: 1, total: qs.length,
          breadcrumbs: [], activeBreadcrumb: 0,
          // legacy single fields point to first question (so any
          // existing single-question render fallback still works)
          question: qs[0].question, subtitle: qs[0].subtitle,
          kind: qs[0].kind, options: qs[0].options,
          // batched extras
          batched: true,
          questions: qs,
          history: [], upcoming: [],
          session: normalizeUiSession(m.session || ''),
          ip: m.ip || '',
          workflow: m.workflow || '',
          source: m.source || '',
          dynamic: true,
        };
        setQaState(s => ({
          ...s,
          [flowId]: {
            batched: true,
            active: 0,
            states: qs.map(q => ({
              opts: q.options.map(o => ({ ...o })),
              custom: '',
            })),
            submitted: false,
          },
        }));
      } else {
        // Single-question path — unchanged
        const opts = (m.options || []).map(o => ({
          id: o.id, label: o.label, detail: o.detail || '', selected: false,
        }));
        window.QA_FLOWS[flowId] = {
          stage: 'Agent', stageDetail: 'ask_user',
          title: m.question || 'Question',
          step: 1, total: 1,
          breadcrumbs: [], activeBreadcrumb: 0,
          question: m.question || '',
          subtitle: m.subtitle || '',
          placeholder: m.placeholder || '',
          multiline: !!m.multiline || String(m.placeholder || '').includes('\n'),
          kind: m.kind === 'multi' ? 'multi' : m.kind === 'input' ? 'input' : 'single',
          options: opts,
          history: [], upcoming: [],
          session: normalizeUiSession(m.session || ''),
          ip: m.ip || '',
          workflow: m.workflow || '',
          source: m.source || '',
          dynamic: true,
        };
        setQaState(s => ({
          ...s,
          [flowId]: { opts: opts.map(o => ({ ...o })), custom: '', submitted: false }
        }));
      }
      setFeed(f => (
        f.some(e => e && e.kind === 'qcard' && e.flowId === flowId)
          ? f
          : [...f, { kind: 'qcard', flowId, dynamic: true, session: normalizeUiSession(m.session || '') }]
      ));
      if (m.workflow === 'ssot-gen' || m.source === 'ssot-qna') {
        setTimeout(refreshSsotQa, 150);
      }
    }));
    subs.push(window.backend.subscribe('ssot_approval_ready', (m) => {
      if (!m || !m.ip) return;
      const payload = { ...m, createdAt: Date.now() };
      setSsotApproval(payload);
      setFeed(f => {
        const deduped = f.filter(e => !(e.kind === 'ssot_approval' && e.ip === m.ip));
        return [...deduped, {
          kind: 'ssot_approval',
          ip: m.ip,
          payload,
          createdAt: Date.now(),
        }];
      });
      setStreaming(false);
    }));
    const closeAskUser = (m) => {
      const flowId = m && m.flow_id;
      if (!flowId) return;
      setQaState(s => {
        const cur = s[flowId];
        if (!cur || cur.submitted) return s;
        return { ...s, [flowId]: { ...cur, submitted: true } };
      });
      setTimeout(refreshSsotQa, 250);
    };
    subs.push(window.backend.subscribe('ask_user_answered', closeAskUser));
    subs.push(window.backend.subscribe('ask_user_closed', closeAskUser));
    subs.push(window.backend.subscribe('ssot_qa_updated', (m) => refreshSsotQa(m && m.session)));
    return () => subs.forEach(u => u && u());
  }, [activateAskUserSession, refreshSsotQa]);

  const navigateInputHistory = (delta) => {
    if (!inputHistory.length) return false;
    let idx = inputHistoryIndexRef.current;
    if (idx === null || idx === undefined) {
      if (delta > 0) return false;
      inputHistoryDraftRef.current = input;
      idx = inputHistory.length - 1;
    } else {
      idx += delta;
    }
    if (idx < 0) idx = 0;
    if (idx >= inputHistory.length) {
      inputHistoryIndexRef.current = null;
      setInput(inputHistoryDraftRef.current || '');
      return true;
    }
    inputHistoryIndexRef.current = idx;
    setInput(inputHistory[idx] || '');
    setShowSlash(false);
    setShowAt(false);
    return true;
  };

  const onKey = (e) => {
    if (showSlash) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setSlashSel(s => Math.min(s + 1, filtered.length - 1)); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setSlashSel(s => Math.max(s - 1, 0)); return; }
      if (e.key === 'Tab' || e.key === 'Enter') {
        if (filtered[slashSel]) {
          e.preventDefault();
          if (e.key === 'Enter') submitMsg(filtered[slashSel].cmd);
          else setInput(filtered[slashSel].cmd + ' ');
          return;
        }
      }
      if (e.key === 'Escape') { e.preventDefault(); setShowSlash(false); return; }
    }
    if (showAt) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setAtSel(s => Math.min(s + 1, fileMatches.length - 1)); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setAtSel(s => Math.max(s - 1, 0)); return; }
      if (e.key === 'Tab' || e.key === 'Enter') {
        if (fileMatches[atSel]) {
          e.preventDefault();
          acceptAtCompletion(fileMatches[atSel]);
          return;
        }
      }
      if (e.key === 'Escape') { e.preventDefault(); setShowAt(false); return; }
    }
    if (e.key === 'ArrowUp') {
      if (navigateInputHistory(-1)) {
        e.preventDefault();
        requestAnimationFrame(() => {
          const el = inputRef.current;
          if (el) el.setSelectionRange(el.value.length, el.value.length);
        });
      }
      return;
    }
    if (e.key === 'ArrowDown') {
      if (navigateInputHistory(1)) {
        e.preventDefault();
        requestAnimationFrame(() => {
          const el = inputRef.current;
          if (el) el.setSelectionRange(el.value.length, el.value.length);
        });
      }
      return;
    }
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitMsg(); }
  };

  // ── question card handlers ─────────────────────────────────────
  // Both single-question and batched (tabbed) flows share these
  // helpers; in batched mode they operate on the active tab's slice
  // (states[active]) instead of the top-level opts/custom.
  const toggleOpt = (flowId, optId) => {
    const flow = window.QA_FLOWS[flowId];
    setQaState(s => {
      const cur = s[flowId];
      if (cur.submitted) return s;
      if (cur.batched) {
        const idx = cur.active || 0;
        const q = flow.questions[idx];
        const tabState = cur.states[idx];
        let opts;
        if (q.kind === 'multi') {
          opts = tabState.opts.map(o =>
            o.id === optId ? (o.locked ? o : { ...o, selected: !o.selected }) : o
          );
        } else {
          opts = tabState.opts.map(o => ({ ...o, selected: o.id === optId }));
        }
        const states = cur.states.map((st, i) =>
          i === idx ? { ...st, opts } : st
        );
        return { ...s, [flowId]: { ...cur, states } };
      }
      let opts;
      if (flow.kind === 'multi') {
        opts = cur.opts.map(o => o.id === optId ? (o.locked ? o : { ...o, selected: !o.selected }) : o);
      } else {
        opts = cur.opts.map(o => ({ ...o, selected: o.id === optId }));
      }
      return { ...s, [flowId]: { ...cur, opts } };
    });
  };

  const setCustom = (flowId, val) => {
    setQaState(s => {
      const cur = s[flowId];
      if (!cur) return s;
      if (cur.batched) {
        const idx = cur.active || 0;
        const states = cur.states.map((st, i) =>
          i === idx ? { ...st, custom: val } : st
        );
        return { ...s, [flowId]: { ...cur, states } };
      }
      return { ...s, [flowId]: { ...cur, custom: val } };
    });
  };

  // Switch active tab in a batched ask_user flow. `idx` may equal
  // questions.length to land on the synthetic 'Submit' tab (review).
  const setActiveTab = (flowId, idx) => {
    setQaState(s => {
      const cur = s[flowId];
      if (!cur || !cur.batched) return s;
      const flow = window.QA_FLOWS[flowId];
      const max = (flow.questions || []).length; // .length = Submit tab
      const next = Math.max(0, Math.min(max, idx));
      return { ...s, [flowId]: { ...cur, active: next } };
    });
  };

  const advanceBatchedQuestion = (flowId) => {
    setQaState(s => {
      const cur = s[flowId];
      if (!cur || !cur.batched) return s;
      const flow = window.QA_FLOWS[flowId];
      const tabCount = (flow.questions || []).length;
      const active = cur.active || 0;
      const next = Math.max(0, Math.min(tabCount, active + 1));
      return { ...s, [flowId]: { ...cur, active: next } };
    });
  };

  // submitCard ships an ask_user answer back to the agent over the WS.
  // Batched flows package every per-tab answer into a single
  // {answers: [...]} payload so the backend resolves all of them in
  // one round-trip — matches the textual UI's batched ask_user.
  const submitCard = (flowId) => {
    // Functional updater so we always read the latest qaState — this
    // matters when a toggle was just queued (e.g. single-kind Enter
    // = toggle+submit) and we'd otherwise see pre-toggle state.
    let snapshot = null;
    setQaState(s => {
      const st = s[flowId];
      if (!st || st.submitted) return s;
      if (window.backend) {
        if (st.batched) {
          const answers = (st.states || []).map(tab => ({
            selected: tab.opts.filter(o => o.selected).map(o => o.id),
            custom: tab.custom || '',
          }));
          window.backend.send({ type: 'answer', flow_id: flowId, answers });
        } else {
          const selectedIds = st.opts.filter(o => o.selected).map(o => o.id);
          window.backend.send({
            type: 'answer',
            flow_id: flowId,
            selected: selectedIds,
            custom: st.custom || '',
          });
        }
      }
      // Build a serializable history snapshot of THIS submit so we
      // can prepend it to qaHistory after the state update flushes.
      try {
        const flow = window.QA_FLOWS && window.QA_FLOWS[flowId];
        if (flow) {
          const items = flow.batched
            ? (flow.questions || []).map((q, i) => {
                const tab = (st.states || [])[i] || { opts: [], custom: '' };
                return {
                  question: q.question || '',
                  kind: q.kind || 'single',
                  selected: tab.opts.filter(o => o.selected)
                    .map(o => ({ id: o.id, label: o.label })),
                  custom: tab.custom || '',
                };
              })
            : [{
                question: flow.question || '',
                kind: flow.kind || 'single',
                selected: (st.opts || []).filter(o => o.selected)
                  .map(o => ({ id: o.id, label: o.label })),
                custom: st.custom || '',
              }];
          snapshot = {
            flowId,
            ts: Date.now(),
            ip: flow.ip || '',
            workflow: flow.workflow || '',
            source: flow.source || '',
            items,
          };
        }
      } catch (_) {}
      return { ...s, [flowId]: { ...st, submitted: true } };
    });
    if (snapshot) {
      setQaHistory(h => {
        if (h.length && h[0].flowId === snapshot.flowId) return h; // dedupe re-submits
        return [snapshot, ...h].slice(0, 50);
      });
    }
    setStreaming(true);  // agent resumes after receiving answer
  };

  // ── layout ─────────────────────────────────────────────────────
  // sim_debug owns its own hierarchy / source / wave / chat panels —
  // hide the outer ATLAS sidebars (mode/workflow/files on the left,
  // ATLAS + SSOT/Todo/Diff on the right) so the inner 3-zone
  // debug surface gets the full viewport. Width state is preserved so
  // switching back to another workflow restores the original layout.
  const isSimDebug = workflow === 'sim_debug';
  const effLeftW  = isSimDebug ? 0 : leftW;
  const effRightW = isSimDebug ? 0 : rightW;
  const renderFeedEntries = () => {
    // Pairing pre-pass: when an action entry is immediately followed by
    // an obs entry whose tool matches, fuse them into one ToolCard.
    const out = [];
    for (let i = 0; i < feed.length; i++) {
      const cur = feed[i];
      const nxt = feed[i + 1];
      if (cur && cur.kind === 'action' && nxt && nxt.kind === 'obs'
          && cur.tool && nxt.tool && cur.tool === nxt.tool) {
        out.push(<ToolCard key={i} action={cur} obs={nxt} />);
        i++;
        continue;
      }
      if (cur && cur.kind === 'action' && cur.tool) {
        out.push(<ToolCard key={i} action={cur} obs={null} />);
        continue;
      }
      out.push(
        <FeedEntry
          key={i}
          entry={cur}
          qaState={qaState}
          onToggle={toggleOpt}
          onCustom={setCustom}
          onSubmit={submitCard}
          dir={dir}
        />
      );
    }
    return out;
  };
  const renderChatPane = (style = {}) => (
    <div ref={feedRef} style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '14px 18px', ...style }}>
      {renderFeedEntries()}
      {/* Streaming preview removed — used to render the in-progress
          buffer as plain text, then the same text reappeared as a
          markdown-rendered 'agent' entry on flush, with very different
          line spacing. The status strip already signals work-in-progress;
          the final clean markdown lands once when the buffer parks. */}
    </div>
  );

  // Toggle a body-level class so the App-level TitleBar / StatusBar
  // can self-collapse when sim_debug owns the screen — gives the
  // waveform / hierarchy / chat panels true full-viewport real estate.
  React.useEffect(() => {
    if (isSimDebug) document.body.classList.add('atlas-sim-debug-fullscreen');
    else            document.body.classList.remove('atlas-sim-debug-fullscreen');
    return () => document.body.classList.remove('atlas-sim-debug-fullscreen');
  }, [isSimDebug]);
  return (
    <div style={{
      display: 'grid',
      // When sim_debug owns the surface there's exactly one child
      // (the SimDebug wrapper); collapsing the grid to a single 1fr
      // column keeps that child from auto-placing into a 0px slot.
      gridTemplateColumns: isSimDebug
        ? '1fr'
        : `${leftW}px 4px 1fr 4px ${rightW}px`,
      gap: isSimDebug ? 0 : 12,
      padding: isSimDebug ? 0 : 16,
      height: '100%', overflow: 'hidden',
    }}>
      {/* LEFT — Mode/Workflow + Files (collapsed when leftW===0 OR sim_debug) */}
      {effLeftW > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        <div className="box">
          <div className="box-h">
            <span>▸ mode</span>
            <span style={{ flex: 1 }} />
            <span
              onClick={toggleLeft}
              title="collapse left panel (double-click splitter to restore)"
              className="mute"
              style={{ cursor: 'pointer', fontSize: 12, padding: '0 6px',
                       userSelect: 'none' }}
            >‹</span>
            <span className="mute" style={{ fontSize: 10, textTransform: 'none', letterSpacing: 0 }}>shift+tab</span>
          </div>
          {/* Intent toggle: Normal | Plan */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--line)' }}>
            <div
              onClick={() => switchIntent('normal')}
              style={{
                padding: '8px 10px', textAlign: 'center', cursor: 'pointer', fontSize: 11,
                letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600,
                color: intent === 'normal' ? 'var(--bg)' : 'var(--fg-mute)',
                background: intent === 'normal' ? 'var(--cyan)' : 'transparent',
                borderRight: '1px solid var(--line)',
              }}
            >● Normal</div>
            <div
              onClick={() => switchIntent('plan')}
              style={{
                padding: '8px 10px', textAlign: 'center', cursor: 'pointer', fontSize: 11,
                letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600,
                color: intent === 'plan' ? 'var(--bg)' : 'var(--fg-mute)',
                background: intent === 'plan' ? 'var(--warn)' : 'transparent',
              }}
            >◐ Plan</div>
          </div>
          <div style={{ padding: '6px 12px 4px', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--fg-mute)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>workflow</span>
            <span className="mute" style={{ fontSize: 9, textTransform: 'none', letterSpacing: 0 }}>· optional · click to toggle</span>
          </div>
          <div style={{ paddingBottom: 4 }}>
            {window.FLOW_STAGES.map((s, i) => {
              const active = workflow === s.id;
              return (
                <div key={s.id}
                  onClick={() => switchWorkflow(s.id)}
                  style={{
                    display: 'grid', gridTemplateColumns: '14px 38px 1fr 14px',
                    gap: 8, padding: '6px 12px', alignItems: 'center', fontSize: 12, cursor: 'pointer',
                    background: active ? 'var(--select)' : 'transparent',
                    borderLeft: active ? `2px solid ${s.color}` : '2px solid transparent',
                  }}
                  onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--bg-2)'; }}
                  onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
                >
                  <span className="mute">{i + 1}</span>
                  <span style={{ color: s.color, fontWeight: 700, letterSpacing: '0.06em', fontSize: 10 }}>{s.glyph}</span>
                  <span style={{ fontWeight: active ? 500 : 400 }}>{s.label}</span>
                  <span className="mute" style={{ fontSize: 10 }}>{active ? '◉' : '○'}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div className="box-h">
            <span>▸ workspace</span>
            <span style={{ flex: 1 }} />
            <span className="acc" style={{ textTransform: 'none', fontSize: 11, letterSpacing: 0 }}>
              {(window.SCOPE_PATH || '').split('/').pop() || 'project root'}
            </span>
          </div>
          {/* scope path bar — editable; constrains the agent to this dir.
              When empty, the input shows the project's root dir as a
              placeholder so the user knows what "no scope" means. */}
          <div style={{
            padding: '6px 10px', borderBottom: '1px solid var(--line)',
            display: 'flex', alignItems: 'center', gap: 6, fontSize: 11,
            background: 'var(--bg-2)',
          }}>
            <span className="mute" style={{ fontSize: 10 }}>scope</span>
            <span className="mute">›</span>
            <input
              type="text"
              // key forces a remount whenever SCOPE_PATH changes
              // externally (e.g. selecting a different ip_id from the
              // top dir-switcher), so the uncontrolled input picks up
              // the new defaultValue. Without this, picking IP=spi
              // would leave the input still showing the previous IP's
              // dir, even though window.SCOPE_PATH already updated.
              key={window.SCOPE_PATH || '__root__'}
              defaultValue={window.SCOPE_PATH || ''}
              placeholder={
                window.CONTEXT && window.CONTEXT.projectRoot
                  ? '(root: ' + window.CONTEXT.projectRoot.split('/').slice(-2).join('/') + ') — type sub-dir, ↵ to set'
                  : '(project root) — type a sub-dir, ↵ to set'
              }
              title={'Agent will be asked to confine all reads/writes to this path. Empty = whole project root ('
                     + (window.CONTEXT?.projectRoot || '?') + ')'}
              style={{
                flex: 1, fontFamily: 'var(--mono)', fontSize: 11,
                background: 'transparent', border: 'none', outline: 'none',
                color: 'var(--fg)',
              }}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  window.atlasData.setScopePath(e.currentTarget.value.trim());
                }
              }}
              onBlur={e => window.atlasData.setScopePath(e.currentTarget.value.trim())}
            />
            {window.SCOPE_PATH ? (
              <span
                title={'clear scope (back to project root)\nWas: ' + window.SCOPE_PATH}
                style={{ cursor: 'pointer', color: 'var(--warn)', fontSize: 12,
                         padding: '0 4px', userSelect: 'none' }}
                onClick={() => window.atlasData.setScopePath('')}
              >✕</span>
            ) : null}
            {/* Sort toggle: name (A-Z, dirs first) ↔ recent (mtime DESC).
                Click cycles between the two; the active one is accent-color. */}
            <span
              title={'sort: ' + (fileSort === 'recent'
                ? 'recent (most recently modified first) — click for A→Z'
                : 'A→Z (dirs first) — click for recent')}
              onClick={() => {
                setFileSort(s => s === 'recent' ? 'name' : 'recent');
                window.atlasData.refreshFileTree(window.SCOPE_PATH || '');
              }}
              style={{
                cursor: 'pointer',
                fontSize: 10,
                padding: '1px 6px',
                borderRadius: 2,
                userSelect: 'none',
                color: fileSort === 'recent' ? 'var(--accent)' : 'var(--fg-mute)',
                border: '1px solid ' + (fileSort === 'recent' ? 'var(--accent)' : 'var(--line)'),
                fontFamily: 'var(--mono)',
              }}
            >{fileSort === 'recent' ? '⏱ recent' : 'A→Z'}</span>
            <span
              title="refresh — pull the latest file list now"
              style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 13,
                       padding: '0 6px', fontWeight: 600, userSelect: 'none' }}
              onClick={() => window.atlasData.refreshFileTree(window.SCOPE_PATH || '')}
            >↻</span>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
            {/* Parent-dir shortcut: click → pop one segment off scope.
                Only shown when scope is non-empty so users have a
                one-click way out without retyping into the input. */}
            {window.SCOPE_PATH ? (
              <div
                className="frow"
                style={{ paddingLeft: 8, cursor: 'pointer' }}
                title={'go up one level\nfrom: ' + window.SCOPE_PATH}
                onClick={() => {
                  const segs = (window.SCOPE_PATH || '').split('/').filter(Boolean);
                  segs.pop();
                  window.atlasData.setScopePath(segs.join('/'));
                }}
              >
                <span className="fr-icon">▲</span>
                <span className="trunc"><span className="dim">.. (up)</span></span>
                <span className="mute" style={{ fontSize: 10 }} />
              </div>
            ) : null}
            {window.FILE_TREE.length === 0 && (
              <div className="mute" style={{ padding: '8px 10px', fontSize: 11 }}>
                (empty — try a different scope or refresh)
              </div>
            )}
            {/* Sort: 'recent' = mtime DESC (most recent first, ignoring
                dir/file distinction so just-touched files always float
                to the top). 'name' keeps the API's default A→Z, dirs
                first ordering. /api/files already returns mtime per
                entry — sort happens client-side, no backend change. */}
            {(fileSort === 'recent'
              ? [...window.FILE_TREE].sort((a, b) => (b.mtime || 0) - (a.mtime || 0))
              : window.FILE_TREE
            ).map((n, i) => {
              const fullPath = (window.SCOPE_PATH ? window.SCOPE_PATH + '/' : '') + n.name;
              const isSelected = n.type === 'file' && previewPath === fullPath;
              return (
                <div key={i}
                  className={(isSelected ? 'frow active' : (n.active ? 'frow active' : 'frow'))}
                  style={{ paddingLeft: 8 + (n.depth || 0) * 14, cursor: 'pointer' }}
                  onClick={() => {
                    if (n.type === 'file') {
                      setPreviewPath(fullPath);
                      setMainTab(tab => tab === 'split' ? 'split' : 'preview');
                    } else {
                      window.atlasData.setScopePath(fullPath);
                    }
                  }}
                  title={fullPath + (n.type === 'file' ? ' (click to preview)' : '')}
                >
                  <span className="fr-icon">{n.type === 'dir' ? '▸' : '◆'}</span>
                  <span className="trunc">{n.type === 'dir' ? <span className="dim">{n.name}/</span> : n.name}</span>
                  <span className="mute" style={{ fontSize: 10 }}>{n.size}</span>
                </div>
              );
            })}
          </div>
          {/* file tree footer */}
          <div style={{ borderTop: '1px solid var(--line)', padding: '6px 10px', fontSize: 10, color: 'var(--fg-mute)', display: 'flex', gap: 10 }}>
            <span>{window.FILE_TREE.length} entries</span>
            <span className="mute">·</span>
            <span className="mute" title="Auto-refreshes on tool_result + every 5s">
              {window.FILE_TREE_LAST_REFRESH
                ? new Date(window.FILE_TREE_LAST_REFRESH).toLocaleTimeString()
                : 'loading…'}
            </span>
            <span style={{ flex: 1 }} />
            <span className="mute"
              title={window.CONTEXT?.projectRoot || ''}>
              {window.SCOPE_PATH
                ? window.SCOPE_PATH
                : (window.CONTEXT && window.CONTEXT.projectRoot
                    ? window.CONTEXT.projectRoot.split('/').pop()
                    : 'project root')}
            </span>
          </div>
        </div>
        {/* Conversation hydration mode selector — sits below the file
            tree, left of the chat input. Picks which on-disk source
            populates the chat feed on (re)load:
              • conversation — recent rolling window from conversation.json
              • full         — every message from full_conversation.json
              • recent 50    — last 50 messages of full_conversation.json
            Default 'conversation'. Saved in localStorage. */}
        <ConvModeSelector />
      </div>
      ) : (
        <div /> /* collapsed — empty grid cell so the 5-track grid stays aligned */
      )}

      {/* LEFT ↔ CENTER splitter — keep visible at 0px so collapsed panels can reopen. */}
      {!isSimDebug && (
        <Splitter width={leftW} side="left" onResize={setLeftW} onToggle={toggleLeft} />
      )}

      {/* CENTER — sim_debug / coverage workflows swap the chat panel for
          their domain-specific UI (waveform debug center / coverage stats
          + annotated source viewer); every other workflow keeps the chat. */}
      {workflow === 'sim_debug' && window.SimDebug ? (
        <div style={{
          width: '100%', height: '100%',
          minWidth: 0, overflow: 'hidden', position: 'relative',
          display: 'flex', flexDirection: 'column',
        }}>
          <window.SimDebug />
          <button
            onClick={() => switchWorkflow('sim_debug')}
            title="Exit sim_debug → restore default ATLAS layout"
            style={{
              position: 'absolute', top: 8, right: 8, zIndex: 100,
              background: 'rgba(20,24,30,0.85)', color: 'var(--fg)',
              border: '1px solid var(--line)', borderRadius: 4,
              padding: '4px 10px', fontSize: 11,
              fontFamily: 'var(--mono)', cursor: 'pointer',
              backdropFilter: 'blur(2px)',
            }}
          >← exit sim_debug</button>
        </div>
      ) : workflow === 'coverage' && window.Coverage ? (
        <div style={{
          width: '100%', height: '100%',
          minWidth: 0, overflow: 'hidden', position: 'relative',
          display: 'flex', flexDirection: 'column',
        }}>
          <window.Coverage />
          <button
            onClick={() => switchWorkflow('coverage')}
            title="Exit coverage → restore default ATLAS layout"
            style={{
              position: 'absolute', top: 8, right: 8, zIndex: 100,
              background: 'rgba(20,24,30,0.85)', color: 'var(--fg)',
              border: '1px solid var(--line)', borderRadius: 4,
              padding: '4px 10px', fontSize: 11,
              fontFamily: 'var(--mono)', cursor: 'pointer',
              backdropFilter: 'blur(2px)',
            }}
          >← exit coverage</button>
        </div>
      ) : (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        {intent === 'plan' && (
          <div style={{
            padding: '6px 14px', border: '1px solid var(--warn)',
            background: 'color-mix(in oklch, var(--warn) 12%, transparent)',
            color: 'var(--warn)', fontSize: 11, letterSpacing: '0.06em',
            display: 'flex', alignItems: 'center', gap: 10, borderRadius: 2,
          }}>
            <span style={{ fontWeight: 700, textTransform: 'uppercase' }}>◐ Plan mode</span>
            <span style={{ flex: 1 }}>Read-only · agent will analyze and propose, but will not write or run any tools.</span>
            <button className="btn" onClick={() => switchIntent('normal')}
              style={{ borderColor: 'var(--warn)', color: 'var(--warn)', fontSize: 10 }}>
              Apply &amp; switch to Normal <Kbd>⌘ ↵</Kbd>
            </button>
          </div>
        )}
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div className="box-h">
            {/* Tab strip: chat ↔ preview. Preview stays reachable even
                before a file is selected so the empty-state is visible. */}
            <span
              onClick={() => setMainTab('chat')}
              style={{
                cursor: 'pointer', padding: '2px 8px', borderRadius: 2,
                color: mainTab === 'chat' ? 'var(--accent)' : 'var(--fg-mute)',
                background: mainTab === 'chat' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                border: '1px solid ' + (mainTab === 'chat' ? 'var(--accent)' : 'transparent'),
                fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
              }}
            >chat</span>
            <span
              onClick={() => setMainTab('preview')}
              title={previewPath ? 'View ' + previewPath : 'Open preview pane'}
              style={{
                cursor: 'pointer',
                padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                color: mainTab === 'preview' ? 'var(--accent)' : 'var(--fg-mute)',
                background: mainTab === 'preview' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                border: '1px solid ' + (mainTab === 'preview' ? 'var(--accent)' : 'transparent'),
                fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
              }}
            >preview</span>
            <span
              onClick={() => setMainTab('split')}
              title="Show chat and preview side by side"
              style={{
                cursor: 'pointer',
                padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                color: mainTab === 'split' ? 'var(--accent)' : 'var(--fg-mute)',
                background: mainTab === 'split' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                border: '1px solid ' + (mainTab === 'split' ? 'var(--accent)' : 'transparent'),
                fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
              }}
            >split</span>
            {centerLayout === 'tabbed' && (
              <span
                onClick={() => setMainTab('qa')}
                title={pendingQcard ? 'Answer the agent\'s questions' : 'No pending questions'}
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                  position: 'relative',
                  color: mainTab === 'qa' ? 'var(--warn)' : (pendingQcard ? 'var(--warn)' : 'var(--fg-mute)'),
                  background: mainTab === 'qa' ? 'color-mix(in oklch, var(--warn) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'qa' ? 'var(--warn)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >
                Q&amp;A
                {pendingQcard && mainTab !== 'qa' && (
                  <span style={{
                    position: 'absolute', top: 1, right: 1,
                    width: 6, height: 6, borderRadius: '50%',
                    background: 'var(--warn)',
                    animation: 'pulse 1.5s infinite',
                  }} />
                )}
              </span>
            )}
            <span className="mute" style={{ margin: '0 6px' }}>·</span>
            {mainTab === 'chat' ? (
              <>
                <span style={{ color: intent === 'plan' ? 'var(--warn)' : 'var(--cyan)', fontWeight: 600, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                  {intent === 'plan' ? '◐ plan' : '● normal'}
                </span>
                {workflow && (
                  <>
                    <span className="mute" style={{ margin: '0 6px' }}>›</span>
                    <span style={{ color: window.FLOW_STAGES.find(s => s.id === workflow)?.color, fontSize: 11, fontWeight: 600 }}>
                      {window.FLOW_STAGES.find(s => s.id === workflow)?.label}
                    </span>
                  </>
                )}
                <span className="mute" style={{ margin: '0 6px' }}>›</span>
                <span className="trunc"
                      title={`.session/${activeSession || 'default'}\nclick to switch to .session/default`}
                      onClick={switchToDefaultSession}
                      style={{ color: 'var(--fg-mute)', fontSize: 11, maxWidth: 220, cursor: 'pointer' }}>
                  session: {activeSession || 'default'}
                </span>
              </>
            ) : mainTab === 'split' ? (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}
                    title={previewPath || ''}>
                chat + preview · {previewPath || '(no file selected)'}
              </span>
            ) : (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}
                    title={previewPath || ''}>
                {previewPath || '(no file selected)'}
              </span>
            )}
            <span style={{ flex: 1 }} />
            {/* top-right streaming/ready indicator removed — the
                "Running / End of loop / Waiting on you" pill above the
                input row already conveys this state, and louder, so two
                redundant indicators just add noise to the tab header. */}
            {(mainTab === 'preview' || mainTab === 'split') && (
              <span style={{ fontSize: 10 }}>
                <span className="mute" style={{ marginRight: 8 }}>{mainTab === 'split' ? 'chat only' : 'back to chat'}</span>
                <span onClick={() => setMainTab('chat')} className="acc"
                      style={{ cursor: 'pointer', padding: '2px 6px',
                               border: '1px solid var(--accent)', borderRadius: 2 }}>↵</span>
              </span>
            )}
          </div>
          {mainTab === 'chat' ? (
            renderChatPane()
          ) : mainTab === 'preview' ? (
            <PreviewPane path={previewPath} onClose={() => setMainTab('chat')} />
          ) : mainTab === 'split' ? (
            <div style={{
              flex: 1, minHeight: 0, display: 'grid',
              gridTemplateColumns: 'minmax(0, 1fr) minmax(300px, 42%)',
              overflow: 'hidden',
            }}>
              <div style={{ minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--line)' }}>
                <div style={{
                  padding: '4px 10px', borderBottom: '1px solid var(--line)',
                  color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10,
                  letterSpacing: '0.06em', textTransform: 'uppercase',
                }}>
                  chat stream
                </div>
                {renderChatPane({ padding: '10px 12px' })}
              </div>
              <div style={{ minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <PreviewPane path={previewPath} onClose={() => setMainTab('chat')} />
              </div>
            </div>
          ) : (
            /* mainTab === 'qa' — only reachable when centerLayout==='tabbed' */
            <div style={{ flex: 1, overflow: 'auto', padding: '14px 18px' }}>
              {pendingQcard ? (
                <AskUserPrompt
                  flowId={pendingQcard.flowId}
                  state={qaState[pendingQcard.flowId]}
                  sel={askSel}
                  intent={intent}
                  onSel={setAskSel}
                  onToggle={toggleOpt}
                  onCustom={setCustom}
                  onSubmit={submitCard}
                  onChat={() => { setMainTab('chat'); setAskSel(0); inputRef.current?.focus(); }}
                  onSetTab={setActiveTab}
                  onAdvance={advanceBatchedQuestion}
                />
              ) : (
                <SsotQaBoard
                  data={ssotQa}
                  sessions={ssotQaSessions}
                  activeSession={currentSession}
                  uiLang={uiLang}
                  onSelectSession={activateSsotQaSession}
                  onBack={() => setMainTab('chat')}
                  onRefresh={() => { refreshSsotQa(); refreshSsotQaSessions(); }}
                />
              )}
              {qaHistory.length > 0 && (
                <QaHistoryPanel history={qaHistory} onClear={() => setQaHistory([])} />
              )}
            </div>
          )}
        </div>

        {/* prompt — breathing room below so the input row isn't flush
            with the bottom edge of the viewport */}
        <div style={{ position: 'relative', paddingBottom: 24 }}>
          {showAt && atQuery && (
            <div className="slash-menu fade-in" style={{ maxHeight: 280, overflowY: 'auto' }}>
              <div style={{ padding: '6px 12px', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: 'var(--cyan)' }}>
                  {atQuery.parentAbs ? atQuery.parentAbs + '/' : '(project root)'}
                </span>
                <span style={{ flex: 1 }} />
                <span>{fileMatches.length} match{fileMatches.length === 1 ? '' : 'es'}</span>
                <span className="mute">·</span>
                <span><Kbd>↑↓</Kbd> nav · <Kbd>↵</Kbd> select · <Kbd>Esc</Kbd> close</span>
              </div>
              {fileMatches.length === 0 ? (
                <div style={{ padding: '10px 12px', fontSize: 11, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                  {atDirEntries.length === 0 ? 'loading…' : `no entries match "${atQuery.filter}"`}
                </div>
              ) : fileMatches.map((f, i) => (
                <div key={i} className={`slash-item ${i === atSel ? 'sel' : ''}`}
                  onClick={() => acceptAtCompletion(f)}
                  onMouseEnter={() => setAtSel(i)}
                  style={{
                    display: 'grid', gridTemplateColumns: '20px 1fr auto',
                    gap: 8, padding: '5px 12px',
                    background: i === atSel ? 'color-mix(in oklch, var(--accent) 18%, transparent)' : 'transparent',
                    borderLeft: i === atSel ? '2px solid var(--accent)' : '2px solid transparent',
                    cursor: 'pointer',
                  }}>
                  <span style={{ color: f.type === 'dir' ? 'var(--cyan)' : 'var(--accent)' }}>
                    {f.type === 'dir' ? '▸' : '◆'}
                  </span>
                  <span style={{ fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 12 }}>
                    {f.name}{f.type === 'dir' ? '/' : ''}
                  </span>
                  <span className="mute" style={{ fontSize: 10 }}>
                    {f.type === 'dir' ? 'dir' : (f.size != null ? (f.size < 1024 ? f.size + 'B' : (f.size/1024).toFixed(1) + 'K') : '')}
                  </span>
                </div>
              ))}
            </div>
          )}
          {showSlash && filtered.length > 0 && (
            <div className="slash-menu fade-in">
              <div style={{ padding: '6px 12px', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)' }}>
                {filtered.length} command{filtered.length === 1 ? '' : 's'} · <Kbd>↑↓</Kbd> nav · <Kbd>Tab</Kbd> complete · <Kbd>↵</Kbd> run
              </div>
              {filtered.map((c, i) => (
                <div key={c.cmd} className={`slash-item ${i === slashSel ? 'sel' : ''}`}
                  onClick={() => { submitMsg(c.cmd); }}
                  onMouseEnter={() => setSlashSel(i)}>
                  <span className="si-cmd">{c.cmd}</span>
                  <span className="si-alias">{c.alias}</span>
                  <span className="si-desc">{c.desc}</span>
                </div>
              ))}
            </div>
          )}
          {/* Status strip directly above the input — at-a-glance state
              the user doesn't have to look up at the chat header for. */}
          {(() => {
            const backendDown = !window.backend || backendState === 'missing' ||
              backendState === 'closed' || backendState === 'error';
            const s = backendDown
              ? { icon: '!', text: backendState === 'missing' ? 'Backend adapter missing' : 'Backend disconnected', color: 'var(--err)', bg: 'color-mix(in oklch, var(--err) 12%, transparent)' }
              : backendState === 'connecting'
                ? { icon: '·', text: 'Backend connecting', color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 10%, transparent)' }
                : pendingQcard
              ? { icon: '⏸', text: 'Waiting on you · answer the ask_user above', color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)' }
              : streaming
                ? { icon: '◉', text: 'Agent running', color: 'var(--accent)', bg: 'color-mix(in oklch, var(--accent) 16%, transparent)', spin: true }
                : ssotApproval && ssotApproval.approved
                  ? { icon: '◆', text: `SSOT approved · run ${ssotApproval.generate_cmd || `/to-ssot ${ssotApproval.ip}`}`, color: 'var(--ok)', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)' }
                  : ssotApproval
                    ? { icon: '◆', text: `SSOT plan ready · approve ${ssotApproval.ip} before YAML write`, color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)' }
                : { icon: '✓', text: 'End of loop · agent ready', color: 'var(--ok)', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)' };
            return (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '4px 12px', marginBottom: 4,
                fontSize: 11, fontFamily: 'var(--mono)',
                color: s.color, background: s.bg,
                border: `1px solid ${s.color}`, borderRadius: 2,
                letterSpacing: '0.04em',
              }}>
                <span style={{ fontWeight: 700 }}>
                  {s.icon}{s.spin ? <span className="ascii-spin" style={{ marginLeft: 2 }} /> : null}
                </span>
                <span>{s.text}</span>
              </div>
            );
          })()}
          {/* Bottom prompt area — three rendering modes:
              1. classic + pending qcard      → inline AskUserPrompt (legacy)
              2. tabbed   + on Q&A tab        → hidden (AskUserPrompt lives in tab body)
              3. tabbed   + chat/preview tab  → hint to switch to Q&A tab (not input)
              4. anything + no pending qcard  → normal input row */}
          {pendingQcard && centerLayout === 'classic' ? (
            <AskUserPrompt
              flowId={pendingQcard.flowId}
              state={qaState[pendingQcard.flowId]}
              sel={askSel}
              intent={intent}
              onSel={setAskSel}
              onToggle={toggleOpt}
              onCustom={setCustom}
              onSubmit={submitCard}
              onChat={() => { setAskSel(0); inputRef.current?.focus(); }}
              onSetTab={setActiveTab}
              onAdvance={advanceBatchedQuestion}
            />
          ) : pendingQcard && centerLayout === 'tabbed' && mainTab !== 'qa' ? (
            <div
              onClick={() => setMainTab('qa')}
              className="ask-feed-placeholder"
              style={{
                padding: '8px 12px',
                border: '1px dashed var(--warn)',
                borderRadius: 2,
                background: 'color-mix(in oklch, var(--warn) 10%, transparent)',
                color: 'var(--warn)',
                fontSize: 12,
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8,
              }}
              title="Click to open the Q&A tab"
            >
              <span>⏸</span>
              <span>Agent is waiting on you · click here or open the <b>Q&amp;A</b> tab to answer</span>
              <span style={{ flex: 1 }} />
              <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>→ Q&amp;A</span>
            </div>
          ) : pendingQcard && centerLayout === 'tabbed' && mainTab === 'qa' ? (
            null /* AskUserPrompt is rendered inside the tab body above */
          ) : (
            <div className="prompt-row">
              <span className="ps" style={{ color: 'var(--fg-mute)' }}>❯</span>
              <input ref={inputRef} value={input}
                onChange={e => {
                  inputHistoryIndexRef.current = null;
                  inputHistoryDraftRef.current = '';
                  setInput(e.target.value);
                }}
                onKeyDown={onKey}
                placeholder='Type a message · "/" for commands · "@" for files'
                autoFocus
              />
              <span className="mute" style={{ fontSize: 11 }}>
                <Kbd>/</Kbd> cmd · <Kbd>@</Kbd> file · <Kbd>↑</Kbd><Kbd>↓</Kbd> history · <Kbd>↵</Kbd> send
              </span>
            </div>
          )}
        </div>

        {/* hotkey footer removed — chips were rendered in --fg-mute on
            --bg-2 so most users couldn't read them, and the App-level
            <StatusBar/> below already exposes the model + the same
            shift+tab/⌘+/ hints. */}
      </div>
      )}

      {/* CENTER ↔ RIGHT splitter — keep visible at 0px so collapsed panels can reopen. */}
      {!isSimDebug && (
        <Splitter width={rightW} side="right" onResize={setRightW} onToggle={toggleRight} />
      )}

      {/* RIGHT — ATLAS status + SSOT/Todo/Diff (hidden when sim_debug or collapsed) */}
      {effRightW > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        <AgentStatusPanel intent={intent} workflow={workflow}
                          onCollapse={toggleRight} />
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="box-h" style={{ padding: 0 }}>
            <RightTab id="progress" cur={rightTab} onTab={setRightTab}>Progress</RightTab>
            <RightTab id="todo" cur={rightTab} onTab={setRightTab}>Todo</RightTab>
            <RightTab id="git"  cur={rightTab} onTab={setRightTab}>Git</RightTab>
          </div>
          {rightTab === 'progress' && <ProgressPanel />}
          {rightTab === 'todo' && <TodoPanel />}
          {rightTab === 'git'  && <GitPanel />}
        </div>
      </div>
      ) : (
        <div /> /* collapsed — empty grid cell to keep the 5-track grid aligned */
      )}

      {openFile && <FileViewer name={openFile} onClose={() => setOpenFile(null)} />}
    </div>
  );
};

const RightTab = ({ id, cur, onTab, children }) => (
  <span onClick={() => onTab(id)} style={{
    cursor: 'pointer', padding: '10px 14px', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
    color: cur === id ? 'var(--fg)' : 'var(--fg-mute)',
    borderBottom: cur === id ? `2px solid var(--accent)` : '2px solid transparent',
    background: cur === id ? 'var(--bg-2)' : 'transparent',
    flex: 1, textAlign: 'center',
  }}>{children}</span>
);

// ── Feed entry: dispatcher ─────────────────────────────────────────
const CollapsibleThought = ({ text }) => {
  // Default state: show only the LAST ~5 lines, dimmed. Reasoning is
  // valuable as a tail (what the agent just decided), but the early
  // chain-of-thought lines are usually scaffolding the user doesn't
  // need to read. Click to expand for the full text.
  const TAIL_LINES = 5;
  const [open, setOpen] = React.useState(false);
  const lines = text.split('\n').filter(l => l.trim());
  const tail = lines.slice(-TAIL_LINES);
  const hidden = Math.max(0, lines.length - TAIL_LINES);
  return (
    <div
      className="react-block thought"
      style={{ cursor: 'pointer', opacity: 0.62 /* dim */ }}
      onClick={() => setOpen(o => !o)}
      title={open ? 'click to collapse' : 'click to expand full reasoning'}
    >
      <span className="rb-tag">
        thought{lines.length > 1 && ` (${lines.length})`}
        {!open && hidden > 0 && (
          <span className="mute" style={{ marginLeft: 6, fontSize: 10, fontWeight: 400 }}>
            · +{hidden} earlier · click to expand
          </span>
        )}
      </span>
      <span style={{ whiteSpace: 'pre-wrap' }}>
        {open ? text : tail.join('\n')}
      </span>
    </div>
  );
};

// Tool-call observation card — collapsible by default, click to expand.
// Replaces the previous always-expanded <pre> block that drowned the
// chat in tool output. Header shows tool name + first line summary +
// expand chevron; body (full text + diff coloring) stays hidden until
// the user clicks. Inline (single-line) results are shown in full as
// they're already brief.
//
// Optional `embedded` prop: when true, render WITHOUT the outer
// react-block wrapper (used by ToolCard which provides its own
// outer container).
const ObsCard = ({ entry, embedded }) => {
  // Expanded by default — chat log was losing too much info when
  // collapsed (Read results, command output, etc. were hidden behind
  // a one-line header so the user couldn't follow what the agent did
  // without clicking each row). Click the header to collapse if a
  // particular result is too long. Single-line obs always renders
  // inline regardless of this state.
  const [open, setOpen] = React.useState(true);
  let txt = entry.text || '';

  // Condense todo_* tool results — strip the redundant ── TODO ──
  // list block from chat. Right-sidebar TodoPanel has the live full
  // state; reprinting per iteration drowns the chat.
  if (entry.tool && /^todo_(write|update|add|remove|status|note)$/i.test(entry.tool)) {
    const m = txt.match(/^([\s\S]*?)\n\s*── TODO ──[\s\S]*$/);
    if (m) {
      const head = m[1].trim();
      const tally = {};
      const todoBlock = txt.slice(m[1].length);
      const statusRe = /^\s*(⏸|▶|👀|✅|❌)\s/gm;
      let mm;
      while ((mm = statusRe.exec(todoBlock)) !== null) {
        const k = ({'⏸':'pending','▶':'in-progress','👀':'completed','✅':'approved','❌':'rejected'})[mm[1]];
        if (k) tally[k] = (tally[k] || 0) + 1;
      }
      const tallyStr = ['in-progress','pending','completed','approved','rejected']
        .filter(k => tally[k]).map(k => `${tally[k]} ${k}`).join(' · ');
      txt = head + (tallyStr ? `\n— ${tallyStr} (full list in sidebar →)` : '');
    }
  }

  const lines = txt.split('\n');
  const isMulti = lines.length > 1;
  const firstLine = lines[0] || '(empty)';
  const lineCount = lines.length;

  // Diff coloring — opt in by tool name or "Added N, removed M" header.
  const looksLikeDiff = /(^|\n)\s*⎿?\s*Added \d+ lines?,? removed \d+ lines?/.test(txt)
                     || (entry.tool && /^(replace_in_file|write_file|edit|patch)/i.test(entry.tool));

  const renderBody = () => looksLikeDiff
    ? txt.split('\n').map((line, i) => {
        const m = line.match(/^(\s*\d+ )([+\-])(.*)$/);
        if (!m) return <div key={i} style={{ color: 'var(--fg-mute)' }}>{line || ' '}</div>;
        const [, prefix, marker, rest] = m;
        const add = marker === '+';
        return (
          <div key={i} style={{
            background: add ? 'color-mix(in oklch, #3fb950 18%, transparent)'
                            : 'color-mix(in oklch, #f85149 18%, transparent)',
            color: add ? '#7ee787' : '#ffa198',
            borderLeft: `2px solid ${add ? '#3fb950' : '#f85149'}`,
            paddingLeft: 6,
          }}>
            <span style={{ color: 'var(--fg-mute)' }}>{prefix}</span>
            <b>{marker}</b><span>{rest}</span>
          </div>
        );
      })
    : txt;
  const renderMarkdownBody = () => (
    <div
      className="md-agent md-tool-result"
      dangerouslySetInnerHTML={{ __html: _markdownHtml(txt) }}
      ref={_postProcessMarkdownNode}
    />
  );

  // Status detection — leading ✓/✗ badge so errors stand out
  const status = _obsStatus(txt);
  const statusBadge = status === 'err' ? <span style={{ color: '#f85149' }}>✗</span>
                    : status === 'ok'  ? <span style={{ color: '#3fb950' }}>✓</span>
                    : null;

  // Wrapper element: `embedded=true` → no outer react-block (used inside ToolCard).
  const Wrapper = embedded ? React.Fragment : 'div';
  const wrapperProps = embedded ? {} : { className: 'react-block obs has-hover-affordance', style: { position: 'relative' } };

  // Single-line results: show inline (no toggle, already compact).
  if (!isMulti) {
    return (
      <Wrapper {...wrapperProps}>
        {!embedded && <CopyBtn text={txt} />}
        <span className="rb-tag">{embedded ? '' : 'obs'}{entry.tool && !embedded ? ` · ${entry.tool}` : ''}</span>
        {statusBadge && <span style={{ marginRight: 6 }}>{statusBadge}</span>}
        <span>{txt}{entry.truncated ? ' …[truncated]' : ''}</span>
      </Wrapper>
    );
  }

  // Multi-line: collapsible header + hidden body.
  return (
    <Wrapper {...wrapperProps}>
      {!embedded && <CopyBtn text={txt} />}
      <div
        onClick={() => setOpen(o => !o)}
        title={open ? 'click to collapse' : 'click to expand full result'}
        style={{
          display: 'flex', alignItems: 'baseline', gap: 8,
          cursor: 'pointer', userSelect: 'none',
        }}
      >
        {!embedded && <span className="rb-tag">obs{entry.tool ? ` · ${entry.tool}` : ''}</span>}
        {statusBadge && <span style={{ fontSize: 12 }}>{statusBadge}</span>}
        <span className="mute trunc" style={{ flex: 1, fontSize: 12 }}>
          {firstLine}
        </span>
        <span className="mute" style={{ fontSize: 10 }}>
          {lineCount} line{lineCount === 1 ? '' : 's'}
          {entry.truncated ? ' · truncated' : ''}
        </span>
        <span className="mute" style={{ fontSize: 11 }}>{open ? '▾' : '▸'}</span>
      </div>
      {open && (
        looksLikeDiff || !_isWorkflowResultTool(entry.tool) ? (
          <pre style={{
            margin: '4px 0 0', maxHeight: 280, overflow: 'auto',
            background: 'var(--bg-3)', padding: '6px 10px',
            borderRadius: 4, fontSize: 11, lineHeight: 1.45,
            whiteSpace: 'pre', wordBreak: 'normal',
          }}>
            {renderBody()}
            {entry.truncated ? '\n…[truncated]' : ''}
          </pre>
        ) : (
          <>
            {renderMarkdownBody()}
            {entry.truncated ? <div className="mute" style={{ fontSize: 10 }}>…[truncated]</div> : null}
          </>
        )
      )}
    </Wrapper>
  );
};

// ToolCard: pairs an action entry with its obs entry into a single
// connected card with tool-themed left border + glyph + status badge.
// Either half can be missing (action-only when blocked, obs-only is
// uncommon but handled).
const ToolCard = ({ action, obs }) => {
  const tool = (action && action.tool) || (obs && obs.tool) || '';
  const theme = _toolTheme(tool);
  // If the obs indicates an error, override the border to red so the
  // eye finds it. Otherwise use the tool theme color.
  const status = obs ? _obsStatus(obs.text || '') : 'neutral';
  const borderColor = status === 'err' ? '#f85149' : theme.color;
  const argsText = action && action.text ? action.text.replace(/^▶\s*/, '').replace(new RegExp('^' + tool + '\\s*'), '') : '';
  const ts = (action && action.createdAt) || (obs && obs.createdAt) || 0;
  return (
    <div className="tool-card has-hover-affordance"
         style={{ borderLeftColor: borderColor }}>
      <span className="tool-card-ts">{_relTime(ts)}</span>
      <div className="tool-card-head">
        <span className="tool-card-glyph" style={{ color: borderColor }}>{theme.glyph}</span>
        <span className="tool-card-tool" style={{ color: borderColor }}>{tool || '?'}</span>
        {argsText && <span className="tool-card-args trunc">{argsText}</span>}
        {status === 'err' && <span className="tool-card-status" style={{ color: '#f85149' }}>✗</span>}
        {status === 'ok'  && <span className="tool-card-status" style={{ color: '#3fb950' }}>✓</span>}
      </div>
      {obs && <div className="tool-card-sep" />}
      {obs && <ObsCard entry={obs} embedded={true} />}
    </div>
  );
};

const FeedEntry = ({ entry, qaState, onToggle, onCustom, onSubmit, dir }) => {
  if (entry.kind === 'user') {
    return (
      <div style={{ padding: '10px 14px', marginBottom: 12, borderLeft: '2px solid var(--accent)', background: 'var(--bg-2)', borderRadius: 2 }}>
        <span className="acc" style={{ fontWeight: 600, marginRight: 8, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase' }}>You</span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{entry.text}</span>
      </div>
    );
  }
  if (entry.kind === 'agent') {
    const html = _markdownHtml(entry.text || '');
    return (
      <div className="has-hover-affordance" style={{ padding: '8px 0 12px', marginBottom: 4, position: 'relative' }}>
        <span className="ok" style={{ fontWeight: 600, marginRight: 8,
          fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Agent</span>
        {entry.createdAt ? (
          <span className="ts-pill">{_relTime(entry.createdAt)}</span>
        ) : null}
        <CopyBtn text={entry.text || ''} />
        <div className="md-agent" style={{ fontSize: 14, lineHeight: 1.65,
          marginTop: 4 }} dangerouslySetInnerHTML={{ __html: html }}
          ref={_postProcessMarkdownNode}
        />
      </div>
    );
  }
  if (entry.kind === 'thought') {
    return <CollapsibleThought text={entry.text || ''} />;
  }
  if (entry.kind === 'iter_marker') {
    // Thin right-aligned label for the per-iteration banner. Replaces
    // the loud full-width "── Iter N / M  [model]" separator that used
    // to break the visual flow between an action and its obs.
    return (
      <div className="iter-marker">
        <span className="iter-marker-line" />
        <span className="iter-marker-label">
          iter {entry.n}{entry.max ? ` / ${entry.max}` : ''}
          {entry.model ? <span className="iter-marker-model"> · {entry.model}</span> : null}
        </span>
      </div>
    );
  }
  if (entry.kind === 'action') {
    const planned = entry.planned;
    // Live mode emits {kind:'action', text:'▶ tool args…'}; the old mock
    // shape was {kind:'action', tool, args, planned?}. Prefer .text when
    // present so we don't crash on missing args.
    if (entry.text) {
      return (
        <div className="react-block action">
          <span className="rb-tag">action</span>
          <span className="mute" style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</span>
        </div>
      );
    }
    return (
      <div className="react-block action" style={planned ? { opacity: 0.6, borderLeftColor: 'var(--warn)' } : {}}>
        <span className="rb-tag" style={planned ? { color: 'var(--warn)' } : {}}>{planned ? 'plan·action' : 'action'}</span>
        <span>{planned && <span className="warn" style={{ marginRight: 6, fontStyle: 'italic' }}>[would]</span>}<b className="cyan">{entry.tool}</b>(<span className="mute">{Object.entries(entry.args || {}).filter(([k]) => k !== 'planned').map(([k, v]) => (
          <span key={k}>{k}=<span style={{ color: 'var(--fg)' }}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span> </span>
        ))}</span>)</span>
      </div>
    );
  }
  if (entry.kind === 'obs') {
    return <ObsCard entry={entry} />;
  }
  // legacy inline (unused — kept so the surrounding block compiles
  // until I fully extract; never reached because of return above)
  if (false) {
    let txt = entry.text || '';
    // Plan A: condense todo_* tool results — strip the redundant
    // ── TODO ── list block from the chat OBS. The right-sidebar
    // TodoPanel already shows the full live state via /api/todos;
    // re-printing the 7-line list per iteration drowns the chat in
    // duplicates. Keep the agent's actual response (e.g. "✅ Task 2
    // approved" / "Task 3 marked completed. Now perform a CRITICAL
    // ADVERSARIAL review...") because that's the actionable content.
    if (entry.tool && /^todo_(write|update|add|remove|status|note)$/i.test(entry.tool)) {
      const m = txt.match(/^([\s\S]*?)\n\s*── TODO ──[\s\S]*$/);
      if (m) {
        const head = m[1].trim();
        // Count statuses to put a one-line tally where the list was.
        const tally = {};
        const todoBlock = txt.slice(m[1].length);
        const statusRe = /^\s*(⏸|▶|👀|✅|❌)\s/gm;
        let mm;
        while ((mm = statusRe.exec(todoBlock)) !== null) {
          const k = ({'⏸':'pending','▶':'in-progress','👀':'completed','✅':'approved','❌':'rejected'})[mm[1]];
          if (k) tally[k] = (tally[k] || 0) + 1;
        }
        const tallyStr = ['in-progress','pending','completed','approved','rejected']
          .filter(k => tally[k]).map(k => `${tally[k]} ${k}`).join(' · ');
        txt = head + (tallyStr ? `\n— ${tallyStr} (full list in sidebar →)` : '');
      }
    }
    const isMulti = txt.includes('\n');
    // Diff colorizing — replace_in_file / write_file emit a body where
    // each line is "<lineno> [+|-| ] <content>". Mark + lines green and
    // - lines red. Detect by tool name OR by presence of the "Added N
    // lines, removed M lines" header (which is the canonical signature
    // of a diff-style result).
    const looksLikeDiff = /(^|\n)\s*⎿?\s*Added \d+ lines?,? removed \d+ lines?/.test(txt)
                       || (entry.tool && /^(replace_in_file|write_file|edit|patch)/i.test(entry.tool));
    return (
      <div className="react-block obs">
        <span className="rb-tag">obs{entry.tool ? ` · ${entry.tool}` : ''}</span>
        {isMulti ? (
          <pre style={{
            margin: '4px 0 0', maxHeight: 280, overflow: 'auto',
            background: 'var(--bg-3)', padding: '6px 10px',
            borderRadius: 4, fontSize: 11, lineHeight: 1.45,
            whiteSpace: 'pre', wordBreak: 'normal',
          }}>
            {looksLikeDiff
              ? txt.split('\n').map((line, i) => {
                  // Match "  82 + content" / "  82 - content" / "  82 -//comment".
                  // Require exactly ONE space between line number and
                  // marker — context lines like "  79      - { ... }"
                  // (YAML list inside a diff) have extra spaces, and we
                  // shouldn't colorize those as deletions. Marker can
                  // abut content with no space (e.g. "-//").
                  const m = line.match(/^(\s*\d+ )([+\-])(.*)$/);
                  if (!m) {
                    return <div key={i} style={{ color: 'var(--fg-mute)' }}>{line || ' '}</div>;
                  }
                  const [, prefix, marker, rest] = m;
                  const add = marker === '+';
                  return (
                    <div key={i} style={{
                      background: add
                        ? 'color-mix(in oklch, #3fb950 18%, transparent)'
                        : 'color-mix(in oklch, #f85149 18%, transparent)',
                      color: add ? '#7ee787' : '#ffa198',
                      borderLeft: `2px solid ${add ? '#3fb950' : '#f85149'}`,
                      paddingLeft: 6,
                    }}>
                      <span style={{ color: 'var(--fg-mute)' }}>{prefix}</span>
                      <b>{marker}</b>
                      <span>{rest}</span>
                    </div>
                  );
                })
              : txt}
            {entry.truncated ? '\n…[truncated]' : ''}
          </pre>
        ) : (
          <span>{txt}{entry.truncated ? ' …[truncated]' : ''}</span>
        )}
      </div>
    );
  }
  if (entry.kind === 'qcard') {
    return <AskUserCall flowId={entry.flowId} state={qaState[entry.flowId]} dir={dir} />;
  }
  if (entry.kind === 'ssot_approval') {
    return <SsotApprovalCard payload={entry.payload || entry} />;
  }
  if (entry.kind === 'turn_end') {
    // Visible boundary so users can scroll back and see exactly where
    // each turn ended. Distinct from "waiting on ask_user" — that state
    // shows the AskUserPrompt and never reaches this branch.
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        margin: '14px 0 18px', userSelect: 'none',
      }}>
        <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
        <span className="ok" style={{
          fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase',
          fontFamily: 'var(--mono)', fontWeight: 600,
        }}>{entry.text || '✓ end of loop'}</span>
        <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
      </div>
    );
  }
  return null;
};

// HTML-escape before any interpolation. Without this, the fallback
// renderer was happy to drop user-controlled text (e.g. file contents
// the agent quoted) straight into HTML — `</code><img src=x onerror=…>`
// inside a backtick span would have escaped the <code> tag and
// injected a payload. DOMPurify catches it downstream now too, but
// belt-and-suspenders.
const _escHtml = (s) => String(s)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');
const renderInline = (s) => _escHtml(s)
  .replace(/`([^`]+)`/g, '<code class="acc" style="background:var(--bg-2);padding:1px 4px;border-radius:2px;">$1</code>')
  .replace(/\*\*([^*]+)\*\*/g, '<b style="color:var(--fg);">$1</b>');

const SsotApprovalCard = ({ payload }) => {
  const ip = payload?.ip || '';
  const decisions = payload?.decisions || {};
  const missing = Array.isArray(payload?.missing) ? payload.missing : [];
  const approved = !!payload?.approved;
  const send = (text) => {
    if (!text || !window.backend?.send) return;
    let session = 'default';
    try {
      session = normalizeUiSession(window.ACTIVE_SESSION || '') || 'default';
    } catch (_) {
      session = 'default';
    }
    window.backend.send({
      type: 'prompt',
      text,
      session,
      ui_lang: window.ATLAS_UI_LANG || 'ko',
    });
  };
  const rows = [
    ['purpose', 'Purpose'],
    ['bus_interface', 'Bus'],
    ['register_map', 'Registers'],
    ['clock_reset', 'Clock/reset'],
    ['interrupt', 'Interrupt'],
    ['memory_map', 'Memory map'],
    ['parameters', 'Parameters'],
    ['submodule_structure', 'Submodules'],
    ['test_expectation', 'Tests'],
  ];
  const statusText = missing.length
    ? `Missing ${missing.length} decision${missing.length === 1 ? '' : 's'}`
    : approved ? 'Approved · YAML write enabled' : 'Answered · waiting for approval';
  return (
    <div className="react-block obs" style={{
      borderLeftColor: approved ? 'var(--ok)' : 'var(--warn)',
      background: approved
        ? 'color-mix(in oklch, var(--ok) 8%, var(--bg-2))'
        : 'color-mix(in oklch, var(--warn) 8%, var(--bg-2))',
      padding: '10px 12px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
        <div>
          <span className="rb-tag" style={{ color: approved ? 'var(--ok)' : 'var(--warn)' }}>ssot approval</span>
          <b style={{ marginLeft: 8 }}>{ip}</b>
        </div>
        <span style={{
          fontSize: 10,
          color: approved ? 'var(--ok)' : 'var(--warn)',
          border: `1px solid ${approved ? 'var(--ok)' : 'var(--warn)'}`,
          padding: '2px 6px',
          borderRadius: 2,
          whiteSpace: 'nowrap',
        }}>{statusText}</span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--fg-mute)', marginBottom: 10 }}>
        Q&A is complete. Review the plan, approve it, then generate the SSOT YAML from the same Web UI session.
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(92px, 0.28fr) minmax(0, 1fr)',
        gap: '4px 10px',
        marginBottom: 10,
        fontSize: 11,
      }}>
        {rows.map(([key, label]) => (
          <React.Fragment key={key}>
            <span style={{ color: missing.includes(key) ? 'var(--warn)' : 'var(--fg-mute)' }}>{label}</span>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {decisions[key] || <span className="warn">missing</span>}
            </span>
          </React.Fragment>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <button
          className="mini-btn"
          disabled={approved || missing.length > 0}
          onClick={() => send(payload?.approve_cmd || `approve ${ip}`)}
          title={missing.length ? 'Answer missing Q&A fields first' : 'Approve this SSOT plan'}
        >
          approve
        </button>
        <button
          className="mini-btn"
          disabled={!approved}
          onClick={() => send(payload?.generate_cmd || `/to-ssot ${ip}`)}
          title={approved ? 'Generate SSOT YAML' : 'Approve before writing YAML'}
        >
          generate SSOT
        </button>
        <button
          className="mini-btn"
          onClick={() => send(`/new-ip ${ip} ${payload?.kind || ''}`.trim())}
          title="Reopen the Q&A cards for this IP"
        >
          revise Q&A
        </button>
        <code className="acc">{approved ? (payload?.generate_cmd || `/to-ssot ${ip}`) : (payload?.approve_cmd || `approve ${ip}`)}</code>
      </div>
    </div>
  );
};

const SsotQaBoard = ({ data, sessions, activeSession, uiLang = 'ko', onSelectSession, onBack, onRefresh }) => {
  const sections = Array.isArray(data?.sections) ? data.sections : [];
  const toc = Array.isArray(data?.toc) ? data.toc : [];
  const sessionRows = Array.isArray(sessions) ? sessions : [];
  const summary = data?.summary || { total: 0, approved: 0, pending: 0 };
  const hasIp = !!data?.ip;
  const t = uiLang === 'en'
    ? {
        noSession: 'No SSOT QA session selected.',
        selectSession: 'Select an IP/session that uses',
        back: 'back to chat',
        title: 'SSOT QA Preview',
        refresh: 'refresh',
        chat: 'chat',
        total: 'total',
        approved: 'approved',
        pending: 'pending',
        ssot: 'ssot',
        draft: 'draft',
        sessions: 'Sessions',
        toc: 'Table of contents',
        none: 'No QA records yet.',
        noSaved: 'No saved SSOT sessions yet.',
        noCards: 'No section QA cards yet. Start',
        noAnswer: 'No answer captured yet.',
      }
    : {
        noSession: '선택된 SSOT QA 세션이 없습니다.',
        selectSession: 'IP/session을 선택하세요:',
        back: '채팅으로',
        title: 'SSOT QA 미리보기',
        refresh: '새로고침',
        chat: '채팅',
        total: '전체',
        approved: '승인',
        pending: '대기',
        ssot: 'SSOT',
        draft: '작성중',
        sessions: '세션',
        toc: '목차',
        none: '아직 QA 기록이 없습니다.',
        noSaved: '저장된 SSOT 세션이 없습니다.',
        noCards: '아직 section QA 카드가 없습니다. 시작:',
        noAnswer: '아직 답변이 저장되지 않았습니다.',
      };
  const scrollTo = (id) => {
    try {
      document.getElementById('ssot-qa-' + id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (_) {}
  };
  const renderQa = (item, status) => (
    <div
      key={`${item.flow_id || ''}:${item.decision_key || item.question}`}
      style={{
        padding: '8px 10px',
        border: '1px solid var(--line)',
        borderLeft: `3px solid ${status === 'approved' ? 'var(--ok)' : 'var(--warn)'}`,
        background: status === 'approved'
          ? 'color-mix(in oklch, var(--ok) 7%, transparent)'
          : 'color-mix(in oklch, var(--warn) 8%, transparent)',
        marginBottom: 8,
        fontFamily: 'var(--mono)',
      }}
    >
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
        <span style={{
          color: status === 'approved' ? 'var(--ok)' : 'var(--warn)',
          fontSize: 10,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}>
          {status}
        </span>
        <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
          {item.decision_key || item.source || 'qa'}
        </span>
      </div>
      <div style={{ color: 'var(--fg)', fontSize: 12, lineHeight: 1.45 }}>
        {item.question || item.decision_label || 'Untitled question'}
      </div>
      {item.subtitle ? (
        <div style={{ color: 'var(--fg-mute)', fontSize: 11, marginTop: 3 }}>
          {item.subtitle}
        </div>
      ) : null}
      <div style={{ color: item.answer ? 'var(--fg)' : 'var(--fg-mute)', fontSize: 12, marginTop: 7, lineHeight: 1.45 }}>
        {item.answer || t.noAnswer}
      </div>
    </div>
  );

  if (!hasIp) {
    return (
      <div style={{ padding: 20, color: 'var(--fg-mute)', fontSize: 12, fontFamily: 'var(--mono)' }}>
        <div style={{ marginBottom: 8, color: 'var(--fg)' }}>{t.noSession}</div>
        <div>{t.selectSession} <code style={{ color: 'var(--cyan)' }}>ssot-gen</code>.</div>
        <div style={{ marginTop: 12 }}>
          <button className="mini-btn" type="button" onClick={onBack}>{t.back}</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontFamily: 'var(--mono)' }}>
      <div style={{
        border: '1px solid var(--line)',
        background: 'var(--bg-1)',
        padding: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <div style={{ color: 'var(--fg)', fontSize: 15, fontWeight: 700 }}>{t.title}</div>
          <code className="acc">{data.ip}</code>
          <span style={{ flex: 1 }} />
          <button className="mini-btn" type="button" onClick={onRefresh}>{t.refresh}</button>
          <button className="mini-btn" type="button" onClick={onBack}>{t.chat}</button>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10, fontSize: 11 }}>
          <span style={{ color: 'var(--fg-mute)' }}>{t.total} {summary.total || 0}</span>
          <span style={{ color: 'var(--ok)' }}>{t.approved} {summary.approved || 0}</span>
          <span style={{ color: 'var(--warn)' }}>{t.pending} {summary.pending || 0}</span>
          <span style={{ color: data.approved ? 'var(--ok)' : 'var(--fg-mute)' }}>
            {t.ssot} {data.approved ? t.approved : (data.state_status || t.draft)}
          </span>
        </div>
      </div>

      <div style={{
        border: '1px solid var(--line)',
        padding: 10,
        background: 'color-mix(in oklch, var(--bg-1) 75%, transparent)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <div style={{ fontSize: 11, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            {t.sessions}
          </div>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>{sessionRows.length} ssot-gen</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 8 }}>
          {sessionRows.length ? sessionRows.slice(0, 12).map(row => {
            const active = normalizeUiSession(row.session) === normalizeUiSession(activeSession || data.session || '');
            const rowSummary = row.summary || {};
            return (
              <button
                key={row.session}
                type="button"
                onClick={() => onSelectSession && onSelectSession(row)}
                style={{
                  textAlign: 'left',
                  border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
                  background: active ? 'color-mix(in oklch, var(--accent) 12%, transparent)' : 'transparent',
                  color: 'var(--fg)',
                  padding: '8px 9px',
                  cursor: 'pointer',
                  fontFamily: 'var(--mono)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ color: row.approved ? 'var(--ok)' : 'var(--warn)' }}>
                    {row.approved ? 'approved' : row.status || 'draft'}
                  </span>
                  <span style={{ flex: 1 }} />
                  <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>{row.workflow || 'ssot-gen'}</span>
                </div>
                <div style={{ marginTop: 5, fontSize: 12, color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {row.ip || '(no ip)'}
                </div>
                <div style={{ marginTop: 3, fontSize: 10, color: 'var(--fg-mute)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {row.session}
                </div>
                <div style={{ marginTop: 6, fontSize: 10 }}>
                  <span style={{ color: 'var(--ok)' }}>{rowSummary.approved || 0} {t.approved}</span>
                  <span style={{ color: 'var(--fg-mute)' }}> / </span>
                  <span style={{ color: 'var(--warn)' }}>{rowSummary.pending || 0} {t.pending}</span>
                </div>
              </button>
            );
          }) : (
            <div style={{ color: 'var(--fg-mute)', fontSize: 12 }}>{t.noSaved}</div>
          )}
        </div>
      </div>

      <div style={{
        border: '1px solid var(--line)',
        padding: 10,
        background: 'color-mix(in oklch, var(--bg-1) 75%, transparent)',
      }}>
        <div style={{ fontSize: 11, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
          {t.toc}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 6 }}>
          {toc.length ? toc.map(section => (
            <button
              key={section.id}
              type="button"
              onClick={() => scrollTo(section.id)}
              style={{
                textAlign: 'left',
                border: '1px solid var(--line)',
                background: 'transparent',
                color: 'var(--fg)',
                padding: '6px 8px',
                cursor: 'pointer',
                fontFamily: 'var(--mono)',
              }}
            >
              <div style={{ fontSize: 11, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {section.title}
              </div>
              <div style={{ fontSize: 10, color: 'var(--fg-mute)', marginTop: 3 }}>
                {section.approved || 0} {t.approved} / {section.pending || 0} {t.pending}
              </div>
            </button>
          )) : (
            <div style={{ color: 'var(--fg-mute)', fontSize: 12 }}>{t.none}</div>
          )}
        </div>
      </div>

      {sections.length ? sections.map(section => (
        <section
          key={section.id}
          id={'ssot-qa-' + section.id}
          style={{ border: '1px solid var(--line)', background: 'var(--bg-1)', padding: 12 }}
        >
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 10 }}>
            <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 700 }}>{section.title}</div>
            <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
              {(section.approved || []).length} {t.approved} / {(section.pending || []).length} {t.pending}
            </span>
          </div>
          {(section.pending || []).length ? (
            <div style={{ marginBottom: 10 }}>
              <div style={{ color: 'var(--warn)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{t.pending}</div>
              {(section.pending || []).map(item => renderQa(item, 'pending'))}
            </div>
          ) : null}
          {(section.approved || []).length ? (
            <div>
              <div style={{ color: 'var(--ok)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{t.approved}</div>
              {(section.approved || []).map(item => renderQa(item, 'approved'))}
            </div>
          ) : null}
        </section>
      )) : (
        <div style={{ padding: 20, color: 'var(--fg-mute)', fontSize: 12 }}>
          {t.noCards} <code style={{ color: 'var(--cyan)' }}>/new-ip</code> / <code style={{ color: 'var(--cyan)' }}>/grill-me</code>.
        </div>
      )}
    </div>
  );
};

// ── ask_user — compact in-feed tool-call line ─────────────────────
// Renders as `action: ask_user(...)` matching the other tool calls,
// then (when submitted) appends an `obs:` line with the user's reply.
const AskUserCall = ({ flowId, state, dir }) => {
  const flow = window.QA_FLOWS[flowId];
  if (!flow || !state) return null;
  const submitted = state.submitted;
  const isBatched = !!state.batched;
  let sel = [];
  let replySummary = '';
  let argSummary;
  if (isBatched) {
    const tabCount = (flow.questions || []).length;
    const allSel = (state.states || []).map((ts, i) => {
      const ss = (ts.opts || []).filter(o => o.selected).map(o => o.label).join(', ');
      const c = (ts.custom || '').trim();
      return `Q${i + 1}: ${ss}${c ? (ss ? ' · ' : '') + 'note=' + c : ''}`;
    });
    replySummary = allSel.join(' | ');
    argSummary = `flow="${flowId}", batched=${tabCount} questions`;
  } else {
    sel = state.opts.filter(o => o.selected);
    replySummary = sel.map(o => o.label).join(', ') + (state.custom ? `, +"${state.custom}"` : '');
    argSummary = `flow="${flowId}", question="${flow.question.length > 48 ? flow.question.slice(0, 48) + '…' : flow.question}", kind=${flow.kind}, options=${flow.options.length}`;
  }

  return (
    <>
      <div className="react-block action" style={{ borderLeftColor: submitted ? 'var(--ok)' : 'var(--warn)' }}>
        <span className="rb-tag" style={{ color: submitted ? 'var(--ok)' : 'var(--warn)' }}>action</span>
        <span>
          <b className="cyan">ask_user</b>
          <span className="mute">(</span>
          <span style={{ color: 'var(--fg-mute)' }}>{argSummary}</span>
          <span className="mute">)</span>
          {!submitted && (
            <span className="warn" style={{
              marginLeft: 10, fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase',
              padding: '1px 6px', border: '1px solid var(--warn)', borderRadius: 2,
              background: 'color-mix(in oklch, var(--warn) 12%, transparent)',
            }}>
              ⌨ input pending · reply below
            </span>
          )}
        </span>
      </div>
      {submitted && (
        <div className="react-block obs">
          <span className="rb-tag">obs</span>
          <span><span className="ok">✓</span> user replied · <span style={{ color: 'var(--fg)' }}>{replySummary || '(no selection)'}</span></span>
        </div>
      )}
    </>
  );
};

// ── ask_user — past Q&A round-trips, newest first ────────────────
// Persisted to localStorage in workspace.jsx so the trail survives a
// page reload. Renders below the active SSOT board on the Q&A tab.
const QaHistoryPanel = ({ history, onClear }) => {
  if (!history || history.length === 0) return null;
  const fmtTs = (ts) => {
    try {
      const d = new Date(ts);
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      const mo = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      return `${mo}-${dd} ${hh}:${mm}`;
    } catch (_) { return ''; }
  };
  return (
    <div style={{ marginTop: 18 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8,
        paddingBottom: 6, borderBottom: '1px dashed var(--line)',
        fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
      }}>
        <span className="acc" style={{ fontWeight: 700 }}>▸ Q&amp;A history</span>
        <span className="mute">·</span>
        <span>{history.length} answered</span>
        <span style={{ flex: 1 }} />
        <span
          onClick={onClear}
          style={{ cursor: 'pointer', color: 'var(--fg-mute)', fontSize: 10 }}
          title="Clear local Q&A history (does not affect the agent's session)"
        >clear</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {history.map((entry, i) => (
          <details
            key={entry.flowId + ':' + entry.ts + ':' + i}
            open={i === 0}
            style={{
              border: '1px solid var(--line)',
              borderLeft: '2px solid var(--ok)',
              borderRadius: 2, padding: '6px 10px',
              background: 'color-mix(in oklch, var(--ok) 4%, transparent)',
            }}
          >
            <summary style={{
              cursor: 'pointer', fontSize: 12, fontFamily: 'var(--mono)',
              listStyle: 'none', display: 'flex', gap: 8, alignItems: 'center',
            }}>
              <span style={{ color: 'var(--ok)', fontWeight: 700 }}>☑</span>
              <span style={{ color: 'var(--fg)' }}>
                {entry.items.length} question{entry.items.length === 1 ? '' : 's'}
                {entry.ip ? ` · ${entry.ip}` : ''}
                {entry.workflow ? ` · ${entry.workflow}` : ''}
              </span>
              <span style={{ flex: 1 }} />
              <span className="mute" style={{ fontSize: 10 }}>{fmtTs(entry.ts)}</span>
            </summary>
            <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {entry.items.map((q, qi) => {
                const sels = (q.selected || []).map(s => s.label).join(', ');
                const ans = sels
                  ? sels + (q.custom ? ` · note: "${q.custom}"` : '')
                  : (q.custom ? `note: "${q.custom}"` : '(no answer)');
                return (
                  <div key={qi} style={{
                    fontSize: 12, fontFamily: 'var(--mono)',
                    paddingLeft: 6, borderLeft: '1px solid var(--line-2)',
                  }}>
                    <div style={{ color: 'var(--fg-dim)' }}>
                      Q{qi + 1}. {q.question}
                    </div>
                    <div style={{ color: 'var(--fg)', marginTop: 1 }}>
                      <span className="mute">→ </span>{ans}
                    </div>
                  </div>
                );
              })}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
};

// ── ask_user — inline bottom prompt (replaces the regular input row) ──
// Mirrors the screenshot: numbered options, inline `[ ]`/`[✓]`, single
// custom-text line, Submit + "Chat about this" affordances, hint footer.
//
// Batched mode (mirror of textual UI's breadcrumb tabs): when the flow
// carries `flow.batched === true` and `flow.questions: [...]`, a tab
// strip renders above the question — one tab per question with a
// ☐/☒ "answered" marker, plus a final ✔ Submit tab. Active tab
// content is shown using the same option/custom widgets; state lives
// in `state.states[active]` instead of the flat `state.opts/state.custom`.
const AskUserPrompt = ({ flowId, state, sel, intent, onToggle, onCustom, onSubmit, onChat, onSel, onSetTab, onAdvance }) => {
  const flow = window.QA_FLOWS[flowId];
  if (!flow || !state) return null;

  // Batched flow virtualization — derive the "view" for the active tab
  // and reuse all the existing single-question rendering below.
  const isBatched = !!state.batched;
  const tabCount = isBatched ? (flow.questions || []).length : 0;
  const active = isBatched ? (state.active || 0) : 0;
  const isSubmitTab = isBatched && active === tabCount;
  // Active tab view (used by the option/custom widgets below)
  const tabState = isBatched
    ? (state.states && state.states[active]) || { opts: [], custom: '' }
    : state;
  const tabFlowKind = isBatched && !isSubmitTab ? flow.questions[active].kind : flow.kind;
  const tabFlowMultiline = !!(isBatched && !isSubmitTab ? flow.questions[active].multiline : flow.multiline);
  const tabAnswered = (i) => {
    const ts = state.states && state.states[i];
    if (!ts) return false;
    return (ts.opts || []).some(o => o.selected) || (ts.custom || '').trim().length > 0;
  };
  const allAnswered = isBatched
    ? (state.states || []).every((_, i) => tabAnswered(i))
    : true;

  const goNextBatchedStep = () => {
    if (!isBatched) return false;
    if (isSubmitTab) {
      if (allAnswered) onSubmit(flowId);
      return true;
    }
    if (active < tabCount - 1) {
      onAdvance ? onAdvance(flowId) : onSetTab && onSetTab(flowId, active + 1);
      return true;
    }
    if (allAnswered) {
      onSubmit(flowId);
    } else {
      onSetTab && onSetTab(flowId, tabCount);
    }
    return true;
  };

  const opts = tabState.opts || [];
  const customIdx = opts.length;       // row index for custom-text line
  const submitIdx = opts.length + 1;   // Submit menu line
  const chatIdx   = opts.length + 2;   // "Chat about this" menu line
  const lastIdx   = chatIdx;

  const onKey = (e) => {
    // Batched flow: ⌘/⌃ + ←/→ moves the keyboard cursor between
    // question blocks (each Q renders its own block; the active block
    // is highlighted and owns the option/custom cursor).
    if (isBatched) {
      if (e.key === 'ArrowLeft' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.max(0, active - 1)); return;
      }
      if (e.key === 'ArrowRight' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.min(tabCount - 1, active + 1)); return;
      }
    }
    if (e.key === 'ArrowDown' || (e.key === 'j' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.min(sel + 1, lastIdx)); return;
    }
    if (e.key === 'ArrowUp' || (e.key === 'k' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.max(sel - 1, 0)); return;
    }
    if (e.key === ' ' && sel < opts.length) {
      e.preventDefault(); onToggle(flowId, opts[sel].id); return;
    }
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      const activeEl = document.activeElement;
      const isCustomInput = activeEl && activeEl.classList && activeEl.classList.contains('askcustom');
      if (isCustomInput && tabFlowMultiline && !e.metaKey && !e.ctrlKey) return;
      e.preventDefault();
      // Custom-input Enter: in batched, advance to next question (or
      // submit-all on the last); in single, submit immediately when the
      // text isn't empty so a one-shot QA can be answered with Enter.
      if (isCustomInput) {
        if (isBatched) { goNextBatchedStep(); return; }
        if ((tabState.custom || '').trim() || opts.some(o => o.selected)) {
          onSubmit(flowId);
        }
        return;
      }
      if (sel < opts.length) {
        onToggle(flowId, opts[sel].id);
        // Batched + single-kind: advance to next question (or submit
        // when on the last one and everything else is answered).
        if (isBatched && tabFlowKind !== 'multi') { goNextBatchedStep(); return; }
        // Non-batched + single-kind (one-question flow): Enter
        // immediately submits — the user just picked their answer.
        if (!isBatched && tabFlowKind === 'single') { onSubmit(flowId); return; }
        return;
      }
      if (sel === customIdx) {
        if (isBatched && (tabState.custom || '').trim()) { goNextBatchedStep(); return; }
        const el = e.currentTarget.querySelector('input.askcustom, textarea.askcustom'); el?.focus(); return;
      }
      if (sel === submitIdx) {
        if (isBatched) { if (allAnswered) onSubmit(flowId); return; }
        onSubmit(flowId);
        return;
      }
      if (sel === chatIdx)   { onChat(flowId); return; }
    }
    if (e.key === 'Escape') { e.preventDefault(); onSel(0); }
  };

  // ── per-question block — used both for the single-question case
  // (rendered once) and for each entry of a batched flow (rendered as
  // a vertical stack so the user can see and answer all questions at
  // once instead of paging through tabs). The active block owns the
  // keyboard cursor (`sel`); inactive blocks are still fully clickable.
  const renderQuestionBlock = (i, block, bs, kind) => {
    const blockOpts = bs.opts || [];
    const blockMultiline = !!(block.multiline || String(block.placeholder || '').includes('\n'));
    const blockPlaceholder = block.placeholder || '';
    const blockSubtitle = block.subtitle || '';
    const blockQuestion = block.question || '';
    const isThisActive = !isBatched || i === active;
    const ensureActive = () => {
      if (isBatched && i !== active && onSetTab) onSetTab(flowId, i);
    };
    return (
      <div
        key={i}
        onClick={() => { if (isBatched && i !== active) ensureActive(); }}
        style={{
          marginBottom: isBatched ? 12 : 0,
          padding: isBatched ? '10px 12px' : 0,
          border: isBatched
            ? `1px solid ${isThisActive ? 'var(--accent)' : 'var(--line)'}`
            : 'none',
          background: isBatched && isThisActive
            ? 'color-mix(in oklch, var(--accent) 5%, transparent)'
            : 'transparent',
          borderRadius: 2,
          cursor: isBatched && !isThisActive ? 'pointer' : 'default',
        }}
      >
        {/* question */}
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 10, color: 'var(--fg)' }}>
          {isBatched && (
            <span
              className={tabAnswered(i) ? 'ok' : 'mute'}
              style={{ marginRight: 8, fontSize: 12, fontWeight: 700, fontFamily: 'var(--mono)' }}
            >
              {tabAnswered(i) ? '☒' : '☐'} Q{i + 1}.
            </span>
          )}
          {blockQuestion}
          {blockSubtitle && (
            <div className="mute" style={{ fontSize: 11, fontWeight: 400, marginTop: 2 }}>
              {blockSubtitle}
            </div>
          )}
        </div>

        {/* multi-mode bulk select / clear */}
        {kind === 'multi' && blockOpts.length > 1 && (
          <div style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 11 }}>
            <span
              onClick={(ev) => {
                ev.stopPropagation();
                ensureActive();
                blockOpts.forEach(o => { if (!o.selected && !o.locked) onToggle(flowId, o.id); });
              }}
              style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--accent)', color: 'var(--accent)', borderRadius: 2 }}
              title="Select every option">
              ☑ Select all
            </span>
            <span
              onClick={(ev) => {
                ev.stopPropagation();
                ensureActive();
                blockOpts.forEach(o => { if (o.selected && !o.locked) onToggle(flowId, o.id); });
              }}
              style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--line)', color: 'var(--fg-mute)', borderRadius: 2 }}
              title="Deselect every option">
              ☐ Clear
            </span>
            <span className="mute" style={{ alignSelf: 'center', fontSize: 10 }}>
              · click rows to toggle individually
            </span>
          </div>
        )}

        {/* numbered options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {blockOpts.map((o, oi) => {
            const isSel = o.selected;
            const focused = isThisActive && sel === oi;
            return (
              <div
                key={o.id}
                onClick={(ev) => { ev.stopPropagation(); ensureActive(); onSel(oi); onToggle(flowId, o.id); }}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '24px 28px 1fr',
                  alignItems: 'baseline',
                  gap: 6,
                  padding: '4px 8px',
                  background: focused ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                  borderLeft: `2px solid ${focused ? 'var(--accent)' : 'transparent'}`,
                  cursor: 'pointer',
                  fontFamily: 'var(--mono)',
                  fontSize: 13,
                  lineHeight: 1.4,
                }}
              >
                <span className="mute" style={{ textAlign: 'right' }}>{oi + 1}.</span>
                <span style={{ color: isSel ? 'var(--accent)' : 'var(--fg-mute)', fontWeight: 700 }}>
                  {kind === 'multi' ? (isSel ? '[✓]' : '[ ]') : (isSel ? '(•)' : '( )')}
                </span>
                <div>
                  <span style={{ color: focused ? 'var(--fg)' : (isSel ? 'var(--fg)' : 'var(--fg-dim, var(--fg))') }}>
                    {o.label}
                    {o.locked && <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>(required)</span>}
                  </span>
                  <div className="mute" style={{ fontSize: 11, fontFamily: 'var(--mono)', marginTop: 1 }}>
                    {o.detail}
                  </div>
                </div>
              </div>
            );
          })}

          {/* custom text line — number continues, has [✓] when non-empty */}
          <div
            onClick={(ev) => { ev.stopPropagation(); ensureActive(); onSel(customIdx); }}
            style={{
              display: 'grid',
              gridTemplateColumns: '24px 28px 1fr',
              alignItems: 'baseline',
              gap: 6,
              padding: '4px 8px',
              background: isThisActive && sel === customIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
              borderLeft: `2px solid ${isThisActive && sel === customIdx ? 'var(--accent)' : 'transparent'}`,
              cursor: 'text',
              fontFamily: 'var(--mono)',
              fontSize: 13,
            }}
          >
            <span className="mute" style={{ textAlign: 'right' }}>{blockOpts.length + 1}.</span>
            <span style={{ color: bs.custom ? 'var(--warn)' : 'var(--fg-mute)', fontWeight: 700 }}>
              {bs.custom ? '[✓]' : '[ ]'}
            </span>
            <div style={{ display: 'flex', alignItems: 'stretch', gap: 6 }}>
              {blockMultiline ? (
                <textarea
                  className="askcustom"
                  value={bs.custom || ''}
                  onChange={(e) => { ensureActive(); onCustom(flowId, e.target.value); }}
                  onFocus={() => { ensureActive(); onSel(customIdx); }}
                  placeholder={blockPlaceholder || 'custom answer / free-form note…'}
                  spellCheck={false}
                  style={{
                    background: 'transparent', border: '1px solid var(--line)', outline: 'none',
                    fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 12, flex: 1,
                    padding: '6px 8px', minHeight: 160, lineHeight: 1.45, resize: 'vertical',
                    whiteSpace: 'pre-wrap',
                  }}
                />
              ) : (
                <input
                  className="askcustom"
                  value={bs.custom || ''}
                  onChange={(e) => { ensureActive(); onCustom(flowId, e.target.value); }}
                  onFocus={() => { ensureActive(); onSel(customIdx); }}
                  placeholder={blockPlaceholder || 'custom answer / free-form note…'}
                  style={{
                    background: 'transparent', border: 'none', outline: 'none',
                    fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 13, flex: 1, padding: 0,
                  }}
                />
              )}
              {isThisActive && sel === customIdx && <span className="cursor-thin" />}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div
      className="ask-prompt fade-in"
      tabIndex={0}
      onKeyDown={onKey}
      style={{
        border: `1px solid var(--accent)`,
        borderLeftWidth: 3,
        background: 'var(--bg-2)',
        padding: '10px 14px 8px',
        outline: 'none',
        boxShadow: '0 -2px 0 0 color-mix(in oklch, var(--accent) 25%, transparent)',
      }}
    >
      {/* header — mimics the screenshot: "▸ ask_user · ✓ Submit" */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8,
        fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
      }}>
        <span className="acc" style={{ fontWeight: 700 }}>▸ ask_user</span>
        <span className="mute">·</span>
        <span className="ok" style={{ fontWeight: 600, opacity: sel === submitIdx ? 1 : 0.6 }}>✓ Submit</span>
        <span className="mute">·</span>
        <span className="mute">{flow.stage} · step {flow.step}/{flow.total}</span>
        <span style={{ flex: 1 }} />
        {intent === 'plan' && (
          <span className="warn" style={{ fontSize: 10, fontWeight: 700 }}>◐ plan mode · still asks</span>
        )}
        <span className="mute" style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10 }}>
          {tabFlowKind === 'multi' ? 'multi-select' : tabFlowKind === 'input' ? 'text' : 'single-select'}
        </span>
        {isBatched && (
          <span
            className={allAnswered ? 'ok' : 'mute'}
            style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10, marginLeft: 6, fontWeight: 600 }}
          >
            · {(state.states || []).filter((_, i) => tabAnswered(i)).length}/{tabCount} answered
          </span>
        )}
      </div>

      {/* questions — single block when not batched, stacked blocks when batched */}
      {isBatched
        ? (flow.questions || []).map((q, i) => {
            const ts = (state.states || [])[i] || { opts: [], custom: '' };
            const k = q.kind === 'multi' ? 'multi' : q.kind === 'input' ? 'input' : 'single';
            return renderQuestionBlock(i, q, ts, k);
          })
        : renderQuestionBlock(0, flow, state, tabFlowKind)}

      {/* submit row — for batched, gates on allAnswered and submits all */}
      <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 0 }}>
        <div
          onClick={() => {
            if (isBatched) { if (allAnswered) onSubmit(flowId); }
            else onSubmit(flowId);
          }}
          style={{
            padding: '4px 8px',
            background: sel === submitIdx ? 'color-mix(in oklch, var(--ok) 18%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === submitIdx ? 'var(--ok)' : 'transparent'}`,
            cursor: (isBatched && !allAnswered) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
            color: sel === submitIdx ? 'var(--ok)' : 'var(--fg)',
            fontWeight: sel === submitIdx ? 600 : 400,
            opacity: (isBatched && !allAnswered) ? 0.6 : 1,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>
          {isBatched ? `Submit all (${(state.states || []).filter((_, i) => tabAnswered(i)).length}/${tabCount})` : 'Submit'}
          {!isBatched && (
            <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>
              ({(opts.filter(o => o.selected) || []).length}{tabState.custom ? '+1' : ''} reply)
            </span>
          )}
        </div>
        <div
          onClick={() => { onSel(chatIdx); onChat(flowId); }}
          style={{
            padding: '4px 8px',
            background: sel === chatIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === chatIdx ? 'var(--accent)' : 'transparent'}`,
            cursor: 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>Chat about this
          <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>(send a free-form message instead)</span>
        </div>
      </div>

      {/* hint footer — terminal-style */}
      <div className="mute" style={{
        marginTop: 8, paddingTop: 6, borderTop: '1px dashed var(--line)',
        fontSize: 11, display: 'flex', gap: 14, flexWrap: 'wrap',
      }}>
        <span><Kbd>↵</Kbd> {isBatched ? 'select & next' : 'select & submit'}</span>
        <span><Kbd>↑↓</Kbd>/<Kbd>j k</Kbd> navigate</span>
        <span><Kbd>Space</Kbd> toggle</span>
        <span><Kbd>Tab</Kbd> next field</span>
        {isBatched && <span><Kbd>⌘/⌃ ←→</Kbd> switch question</span>}
        <span><Kbd>Esc</Kbd> top</span>
      </div>
    </div>
  );
};

// ── Right panels ──────────────────────────────────────────────────
// Live SSOT panel — lists every *.ssot.yaml under the project (or the
// current scope path, if /api/ssot ever filters by it) and shows the
// content of whichever one the user clicks on. Auto-refreshes when the
// agent writes a new SSOT (data.jsx subscribes to tool_result).
const SsotPanel = () => {
  const files = window.SSOT_FILES || [];
  const [selected, setSelected] = React.useState(null);
  const [content, setContent] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  // Default to the first file once the list is populated.
  React.useEffect(() => {
    if (!selected && files.length > 0) setSelected(files[0].path);
  }, [files.length, selected]);

  // Fetch content whenever the selected file changes (or the file list
  // refreshes — the user may want to see updated content for an SSOT
  // the agent just wrote).
  React.useEffect(() => {
    if (!selected) { setContent(''); return; }
    let cancelled = false;
    setLoading(true);
    window.atlasData.fetchSsot(selected).then(d => {
      if (cancelled) return;
      setContent(d?.content || `# (could not read ${selected})`);
      setLoading(false);
    }).catch(() => { if (!cancelled) { setContent(''); setLoading(false); } });
    return () => { cancelled = true; };
  }, [selected, files.length]);

  if (files.length === 0) {
    return (
      <div className="code" style={{ flex: 1, overflow: 'auto',
        padding: '14px 16px', fontSize: 12, color: 'var(--fg-mute)' }}>
        # No *.ssot.yaml files in the project yet.<br />
        # Use <span className="acc">/grill-me</span> to gather the spec
        and <span className="acc">/to-ssot &lt;ip&gt;</span> to write the YAML.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* file picker */}
      <div style={{
        borderBottom: '1px solid var(--line)', padding: '4px 6px',
        display: 'flex', flexWrap: 'wrap', gap: 4,
        background: 'var(--bg-2)',
      }}>
        {files.map(f => (
          <span key={f.path}
            onClick={() => setSelected(f.path)}
            title={f.path}
            style={{
              cursor: 'pointer',
              padding: '2px 8px', fontSize: 10,
              fontFamily: 'var(--mono)',
              border: `1px solid ${selected === f.path ? 'var(--accent)' : 'var(--line)'}`,
              color: selected === f.path ? 'var(--accent)' : 'var(--fg-mute)',
              background: selected === f.path ? 'var(--bg-3, var(--bg-2))' : 'transparent',
              borderRadius: 2,
            }}>
            {f.path.split('/').pop()}
          </span>
        ))}
      </div>
      {/* content viewer */}
      <pre className="code" style={{
        flex: 1, overflow: 'auto', margin: 0,
        padding: '12px 14px', fontSize: 12, lineHeight: 1.55,
        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {loading ? '# loading…' : content}
      </pre>
    </div>
  );
};

const ProgressPanel = () => {
  const [, bump] = React.useReducer(x => x + 1, 0);
  const [moduleId, setModuleId] = React.useState('');

  React.useEffect(() => {
    const h = (ev) => {
      if (!ev.detail || ['PROGRESS', 'SCOPE_PATH', 'SSOT_FILES', 'TODOS'].includes(ev.detail)) bump();
    };
    window.addEventListener('atlas-data-changed', h);
    if (window.atlasData && window.atlasData.refreshProgress) window.atlasData.refreshProgress();
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  const data = window.ATLAS_PROGRESS || {};
  const modules = Array.isArray(data.modules) ? data.modules : [];
  const selected = modules.find(m => m.id === moduleId)
    || data.selected
    || modules[0]
    || null;

  React.useEffect(() => {
    if (selected && selected.id && selected.id !== moduleId) setModuleId(selected.id);
  }, [selected && selected.id]);

  const progress = (selected && selected.progress) || {};
  const status = (selected && selected.status) || {};
  const details = (selected && selected.status_detail) || {};
  const signoff = (selected && selected.signoff) || {};
  const blockers = Array.isArray(signoff.blockers) ? signoff.blockers : [];
  const ownership = signoff.ownership || {};
  const artifact = (selected && selected.artifact_status) || {};
  const artifactDetails = (selected && selected.artifact_detail) || {};
  const req = progress.req || {};
  const ssot = progress.ssot || {};
  const flModel = progress.fl_model || {};
  const flDecomp = progress.fl_decomp || {};
  const fcovPlan = progress.fcov_plan || {};
  const equiv = progress.equivalence_goals || {};
  const goalAudit = progress.goal_audit || {};
  const rtl = progress.rtl || {};
  const compile = progress.compile || {};
  const lint = progress.lint || {};
  const sim = progress.sim || {};
  const dv = sim.dv_plan || {};
  const results = sim.results || {};
  const coverage = sim.coverage || {};

  const pct = (obj) => Math.max(0, Math.min(100, Number(obj && obj.pct) || 0));
  const stateColor = (s) => {
    const v = String(s || '').toLowerCase();
    if (['ok', 'pass', 'approved', 'done'].includes(v)) return 'var(--ok)';
    if (['fail', 'err', 'error', 'rejected'].includes(v)) return 'var(--err)';
    if (['partial', 'planned', 'active', 'blocked', 'stale'].includes(v)) return 'var(--warn)';
    return 'var(--fg-mute)';
  };
  const pill = (label, value) => (
    <span style={{
      border: `1px solid ${stateColor(value)}`,
      color: stateColor(value),
      borderRadius: 2,
      padding: '1px 6px',
      fontSize: 10,
      fontFamily: 'var(--mono)',
      whiteSpace: 'nowrap',
    }}>{label}: {value || 'pending'}</span>
  );
  const Bar = ({ label, done, total, value, color = 'var(--ok)' }) => {
    const p = value != null ? Math.max(0, Math.min(100, Number(value) || 0))
      : (total ? Math.round(100 * (done || 0) / total) : 0);
    return (
      <div style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--fg-mute)', marginBottom: 3 }}>
          <span>{label}</span>
          <span>{done != null && total != null ? `${done}/${total}` : `${p}%`}</span>
        </div>
        <div style={{ height: 5, background: 'var(--bg-3)', border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${p}%`, background: color }} />
        </div>
      </div>
    );
  };
  const Section = ({ title, right, children }) => (
    <div style={{ borderBottom: '1px solid var(--line)', padding: '10px 12px' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8,
        fontSize: 10, fontFamily: 'var(--mono)', letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}>
        <span style={{ color: 'var(--fg)', fontWeight: 700 }}>{title}</span>
        <span style={{ flex: 1 }} />
        {right && <span className="mute" style={{ letterSpacing: 0, textTransform: 'none' }}>{right}</span>}
      </div>
      {children}
    </div>
  );
  const repairRtl = () => {
    const ip = selected && (selected.id || selected.name || selected.ip_dir || '');
    if (!ip || !window.backend) return;
    window.backend.send({ type: 'prompt', text: `/repair-rtl ${ip}` });
  };

  if (!selected) {
    return (
      <div className="code" style={{ flex: 1, padding: '14px 16px', overflow: 'auto', color: 'var(--fg-mute)', fontSize: 12 }}>
        # No SSOT-backed IP progress found.<br />
        # Create or select a leaf SSOT YAML, then run the ATLAS SSOT → RTL → TB → sim_debug flow.
      </div>
    );
  }

  const sections = Array.isArray(ssot.sections) ? ssot.sections : [];
  const rtlModules = Array.isArray(rtl.modules) ? rtl.modules : [];
  const scenarios = Array.isArray(dv.scenario_rows) ? dv.scenario_rows : [];
  const criteria = coverage.criteria && typeof coverage.criteria === 'object' ? coverage.criteria : {};
  const limitations = coverage.limitations && typeof coverage.limitations === 'object' ? coverage.limitations : {};
  const staticCov = coverage.static && typeof coverage.static === 'object' ? coverage.static : {};
  const ownershipRows = [
    'req', 'ssot', 'fl_model', 'fl_decomp', 'fcov_plan', 'equivalence_goals',
    'goal_audit', 'rtl', 'lint', 'tb', 'sim_debug', 'coverage', 'signoff',
  ].map(k => ownership[k]).filter(Boolean);

  return (
    <div style={{ flex: 1, overflow: 'auto', fontSize: 11 }}>
      <div style={{ padding: '9px 12px', borderBottom: '1px solid var(--line)', background: 'var(--bg-2)' }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 8 }}>
          <select
            value={selected.id || ''}
            onChange={(e) => setModuleId(e.target.value)}
            style={{
              flex: 1, minWidth: 0, background: 'var(--bg-3)',
              color: 'var(--fg)', border: '1px solid var(--line)',
              borderRadius: 2, padding: '4px 6px', fontFamily: 'var(--mono)', fontSize: 11,
            }}
          >
            {modules.map(m => <option key={m.id || m.name} value={m.id || m.name}>{m.label || m.name || m.id}</option>)}
          </select>
          <span className="mute" title={selected.ssot_path || ''}>{selected.kind || 'ip'}</span>
        </div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {pill('signoff', status.signoff)}
          {pill('req', status.req)}
          {pill('ssot', status.ssot)}
          {pill('fl', status.fl_model)}
          {pill('decomp', status.fl_decomp)}
          {pill('fcov plan', status.fcov_plan)}
          {pill('equiv', status.equivalence_goals)}
          {pill('audit', status.goal_audit)}
          {pill('rtl', status.rtl)}
          {pill('lint', status.lint)}
          {pill('tb', status.tb)}
          {pill('simdbg', status.sim_debug || status.sim)}
          {pill('cov', status.coverage)}
        </div>
        <div className="mute" style={{ marginTop: 6, fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.4 }}>
          strict gate: REQ + SSOT + executable FL model + decomposition + FCOV plan + RTL + lint + FL-vs-RTL sim + coverage + goal audit
        </div>
        {blockers.length > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>
            blocked by: {blockers.slice(0, 4).join(' · ')}
          </div>
        )}
        <div style={{ marginTop: 8, display: 'flex', gap: 6, alignItems: 'center' }}>
          <button
            onClick={repairRtl}
            disabled={!selected || !selected.id}
            title="Queue rtl-gen repair from current compile/lint/SSOT evidence"
            style={{
              background: 'var(--bg-3)',
              color: 'var(--accent)',
              border: '1px solid var(--accent)',
              borderRadius: 2,
              padding: '3px 7px',
              fontFamily: 'var(--mono)',
              fontSize: 10,
              cursor: 'pointer',
            }}
          >
            repair rtl-gen
          </button>
          <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            uses SSOT + rtl_compile.json + dut_lint.json
          </span>
        </div>
      </div>

      <Section title="Artifact Evidence" right="not signoff">
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
          {pill('req', artifact.req)}
          {pill('ssot', artifact.ssot)}
          {pill('fl', artifact.fl_model)}
          {pill('decomp', artifact.fl_decomp)}
          {pill('fcov plan', artifact.fcov_plan)}
          {pill('equiv', artifact.equivalence_goals)}
          {pill('audit', artifact.goal_audit)}
          {pill('rtl', artifact.rtl)}
          {pill('tb', artifact.tb)}
          {pill('simdbg', artifact.sim_debug)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '62px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">req</span><span className="trunc" title={artifactDetails.req || ''}>{artifactDetails.req || 'no requirement evidence'}</span>
          <span className="mute">ssot</span><span className="trunc" title={artifactDetails.ssot || ''}>{artifactDetails.ssot || 'no artifact evidence'}</span>
          <span className="mute">fl</span><span className="trunc" title={artifactDetails.fl_model || ''}>{artifactDetails.fl_model || 'no executable FL model'}</span>
          <span className="mute">decomp</span><span className="trunc" title={artifactDetails.fl_decomp || ''}>{artifactDetails.fl_decomp || 'no FL decomposition'}</span>
          <span className="mute">fcov</span><span className="trunc" title={artifactDetails.fcov_plan || ''}>{artifactDetails.fcov_plan || 'no FCOV plan'}</span>
          <span className="mute">equiv</span><span className="trunc" title={artifactDetails.equivalence_goals || ''}>{artifactDetails.equivalence_goals || 'no equivalence goals'}</span>
          <span className="mute">audit</span><span className="trunc" title={artifactDetails.goal_audit || ''}>{artifactDetails.goal_audit || 'no goal audit'}</span>
          <span className="mute">rtl</span><span className="trunc" title={artifactDetails.rtl || ''}>{artifactDetails.rtl || 'no artifact evidence'}</span>
          <span className="mute">tb</span><span className="trunc" title={artifactDetails.tb || ''}>{artifactDetails.tb || 'no artifact evidence'}</span>
          <span className="mute">simdbg</span><span className="trunc" title={artifactDetails.sim_debug || ''}>{artifactDetails.sim_debug || 'no artifact evidence'}</span>
        </div>
      </Section>

      <Section title="Loop Owner & Next Action" right="LLM loop / human gate">
        {ownershipRows.length ? (
          <div style={{ display: 'grid', gridTemplateColumns: '58px 68px 1fr', rowGap: 5, columnGap: 8, fontFamily: 'var(--mono)', fontSize: 10 }}>
            {ownershipRows.map(row => (
              <React.Fragment key={row.stage}>
                <span className="mute">{String(row.stage || '').replace('_', ' ')}</span>
                <span style={{ color: row.owner === 'human gate' ? 'var(--warn)' : stateColor(row.status) }}>
                  {row.owner || 'LLM loop'}
                </span>
                <span
                  className="trunc"
                  title={[
                    `status: ${row.status || 'pending'}`,
                    `validator: ${row.validator || ''}`,
                    `evidence: ${row.evidence || ''}`,
                    `blocker: ${row.blocker || ''}`,
                    `next: ${row.next_action || ''}`,
                  ].join('\n')}
                >
                  {row.next_action || 'inspect stage evidence'}
                </span>
              </React.Fragment>
            ))}
          </div>
        ) : (
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            ownership data missing from ATLAS progress response
          </div>
        )}
      </Section>

      <Section title="SSOT Sections" right={selected.ssot_path}>
        <Bar label="approved sections" done={ssot.approved || 0} total={ssot.total || 0} value={pct(ssot)} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {sections.map(s => (
            <div key={s.key} title={s.key} style={{
              display: 'flex', alignItems: 'center', gap: 5, minWidth: 0,
              color: s.status === 'approved' ? 'var(--fg)' : 'var(--fg-mute)',
              fontFamily: 'var(--mono)', fontSize: 10,
            }}>
              <span style={{ color: stateColor(s.status), width: 10 }}>{s.status === 'approved' ? '✓' : '○'}</span>
              <span className="trunc">{s.label || s.key}</span>
            </div>
          ))}
        </div>
        {ssot.metrics && (
          <div className="mute" style={{ marginTop: 8, lineHeight: 1.5, fontFamily: 'var(--mono)' }}>
            submods {ssot.metrics.submodules || 0} · ports {ssot.metrics.ports || 0} · regs {ssot.metrics.registers || 0} · scenarios {ssot.metrics.dv_scenarios || 0}
          </div>
        )}
      </Section>

      <Section title="FL Model & Coverage Plan" right={flModel.source || details.fl_model}>
        <div style={{ display: 'grid', gridTemplateColumns: '86px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">req</span><span style={{ color: stateColor(req.status) }}>{req.status || 'pending'} · {(req.files || []).length || 0} file(s)</span>
          <span className="mute">model</span><span style={{ color: stateColor(flModel.status) }}>{flModel.status || 'pending'} · {flModel.bytes || 0}B</span>
          <span className="mute">self-check</span><span style={{ color: flModel.self_check && flModel.self_check.passed ? 'var(--ok)' : 'var(--fg-mute)' }}>{flModel.self_check && flModel.self_check.passed ? 'pass' : 'missing'}</span>
          <span className="mute">decomp</span><span style={{ color: stateColor(flDecomp.status) }}>{flDecomp.status || 'pending'} · {flDecomp.units || 0} unit(s)</span>
          <span className="mute">fcov plan</span><span style={{ color: stateColor(fcovPlan.status) }}>{fcovPlan.status || 'pending'} · {fcovPlan.bins || 0} bin(s)</span>
          <span className="mute">equiv</span><span style={{ color: stateColor(equiv.status) }}>{equiv.status || 'pending'} · {equiv.passed || 0}/{equiv.total || 0} pass · {equiv.blocked || 0} blocked · {equiv.untested || 0} untested</span>
        </div>
        {Array.isArray(flDecomp.kinds) && flDecomp.kinds.length > 0 && (
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            model slices: {flDecomp.kinds.join(', ')}
          </div>
        )}
        {fcovPlan.summary && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            bins: scenario {fcovPlan.summary.scenario_bins || 0} · transaction {fcovPlan.summary.transaction_bins || 0} · protocol {fcovPlan.summary.protocol_bins || 0} · state {fcovPlan.summary.state_transition_bins || 0} · error {fcovPlan.summary.error_bins || 0}
          </div>
        )}
        <div style={{ marginTop: 8 }}>
          <Bar
            label="equivalence goals"
            done={equiv.passed || 0}
            total={equiv.total || 0}
            color={stateColor(equiv.status)}
          />
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.45 }}>
            checked {equiv.checked || 0} · failed {equiv.failed || 0} · classifications {equiv.classifications || 0}
            {equiv.compare_evidence ? ` · ${equiv.compare_evidence}` : (equiv.evidence ? ` · ${equiv.evidence}` : '')}
          </div>
          {equiv.classification_counts && Object.keys(equiv.classification_counts).length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              class: {Object.entries(equiv.classification_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
            </div>
          )}
          {equiv.owner_counts && Object.keys(equiv.owner_counts).length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              owner: {Object.entries(equiv.owner_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
            </div>
          )}
          {Array.isArray(equiv.missing_evidence) && equiv.missing_evidence.length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              missing: {equiv.missing_evidence.slice(0, 3).join(', ')}
            </div>
          )}
          {Array.isArray(equiv.stale_evidence) && equiv.stale_evidence.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              stale: {equiv.stale_evidence.slice(0, 3).join(', ')}
            </div>
          )}
          {Array.isArray(equiv.failed_goal_ids) && equiv.failed_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              failed: {equiv.failed_goal_ids.join(', ')}
            </div>
          )}
          {Array.isArray(equiv.blocked_goal_ids) && equiv.blocked_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              blocked: {equiv.blocked_goal_ids.join(', ')}
            </div>
          )}
          {Array.isArray(equiv.untested_goal_ids) && equiv.untested_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              untested: {equiv.untested_goal_ids.join(', ')}
            </div>
          )}
          <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '86px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', fontSize: 10 }}>
            <span className="mute">goal audit</span>
            <span style={{ color: stateColor(goalAudit.status) }}>
              {goalAudit.status || 'pending'} · {goalAudit.passed_checks || 0}/{goalAudit.total_checks || 0} checks · {goalAudit.failed_checks || 0} failed
            </span>
            <span className="mute">evidence</span>
            <span className="trunc" title={goalAudit.source || ''}>{goalAudit.source || 'run /goal-audit <ip>'}</span>
          </div>
          {Array.isArray(goalAudit.blockers) && goalAudit.blockers.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              audit blockers: {goalAudit.blockers.slice(0, 8).join(', ')}
            </div>
          )}
          {Array.isArray(goalAudit.stale_evidence) && goalAudit.stale_evidence.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              audit stale: {goalAudit.stale_evidence.slice(0, 3).join(', ')}
            </div>
          )}
        </div>
      </Section>

      <Section title="RTL Modules" right={rtl.filelist || details.rtl}>
        <Bar label="approved RTL files" done={rtl.approved || 0} total={rtl.total || 0} value={pct(rtl)} color="var(--accent)" />
        {rtlModules.length ? rtlModules.map(m => (
          <div key={m.file || m.name} style={{
            display: 'grid', gridTemplateColumns: '14px 1fr auto', gap: 6,
            alignItems: 'baseline', padding: '3px 0', fontFamily: 'var(--mono)', fontSize: 10,
          }}>
            <span style={{ color: stateColor(m.status) }}>{m.status === 'approved' ? '✓' : m.status === 'partial' ? '◐' : '○'}</span>
            <span className="trunc" title={m.resolved_file && m.resolved_file !== m.file ? `${m.file} -> ${m.resolved_file}` : m.file}>
              {m.name || m.file}
              {m.manifest_mismatch ? <span style={{ color: 'var(--warn)' }}> · manifest</span> : null}
            </span>
            <span className="mute">{m.listed ? 'listed' : 'unlisted'} · {m.bytes || 0}B</span>
          </div>
        )) : <div className="mute">No expected RTL modules found in SSOT/filelist yet.</div>}
        {(rtl.manifest_mismatches || 0) > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
            SSOT/RTL manifest mismatch: {rtl.manifest_mismatches}
          </div>
        )}
      </Section>

      <Section title="Compile Gate" right={compile.source || ''}>
        <div style={{ display: 'grid', gridTemplateColumns: '82px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">status</span><span style={{ color: stateColor(compile.status) }}>{compile.status || 'unknown'}</span>
          <span className="mute">errors</span><span style={{ color: (compile.errors || 0) ? 'var(--err)' : 'var(--ok)' }}>{compile.errors ?? 0}</span>
          <span className="mute">diagnostics</span><span style={{ color: (compile.diagnostics || 0) ? 'var(--warn)' : 'var(--ok)' }}>{compile.diagnostics ?? 0}</span>
          <span className="mute">style</span><span style={{ color: (compile.style_violations || 0) ? 'var(--warn)' : 'var(--ok)' }}>{compile.style_violations ?? 0}</span>
        </div>
        {Array.isArray(compile.style_violation_details) && compile.style_violation_details.slice(0, 4).map((v, idx) => (
          <div key={idx} className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>
            <span style={{ color: 'var(--warn)' }}>{v.file}:{v.line}</span> {v.rule}
          </div>
        ))}
      </Section>

      <Section title="Lint Gate" right={lint.source || ''}>
        <div style={{ display: 'grid', gridTemplateColumns: '70px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">status</span><span style={{ color: stateColor(lint.status) }}>{lint.status || 'unknown'}</span>
          <span className="mute">errors</span><span style={{ color: (lint.errors || 0) ? 'var(--err)' : 'var(--ok)' }}>{lint.errors ?? 0}</span>
          <span className="mute">warnings</span><span style={{ color: (lint.warnings || 0) > (lint.warning_budget || 0) ? 'var(--warn)' : 'var(--ok)' }}>{lint.warnings ?? 0} / budget {lint.warning_budget || 0}</span>
        </div>
      </Section>

      <Section title="Simulation & DV Plan" right={(results.sources || []).join(', ')}>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">scenarios</span><span>{dv.scenarios || 0}</span>
          <span className="mute">scoreboard</span><span>{dv.scoreboard_checks ?? 'derive from SSOT'}</span>
          <span className="mute">tests</span><span>{results.pass || 0} pass / {results.fail || 0} fail / {results.total || 0} total</span>
          <span className="mute">checks</span><span>{results.check_pass ?? 0} pass / {results.check_fail ?? 0} fail / {results.check_total ?? 0} total</span>
        </div>
        {scenarios.slice(0, 12).map(sc => (
          <div key={sc.id || sc.name} style={{
            display: 'grid', gridTemplateColumns: '42px 1fr 70px', gap: 6,
            fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0',
          }}>
            <span className="mute">{sc.id || '-'}</span>
            <span className="trunc" title={sc.expected || sc.name}>{sc.name || sc.expected || 'scenario'}</span>
            <span style={{ color: stateColor(sc.status), textAlign: 'right' }}>{sc.status || 'pending'}</span>
          </div>
        ))}
      </Section>

      <Section title="Coverage Criteria" right={coverage.status || 'unknown'}>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">functional</span><span style={{ color: coverage.functional_pct == null ? 'var(--fg-mute)' : 'var(--ok)' }}>{coverage.functional_pct == null ? 'unknown' : coverage.functional_pct + '%'}</span>
          <span className="mute">goals</span><span>{Object.keys(criteria).length}</span>
          <span className="mute">limits</span><span style={{ color: Object.keys(limitations).length ? 'var(--warn)' : 'var(--fg-mute)' }}>{Object.keys(limitations).length || 0}</span>
        </div>
        {Object.entries(criteria).slice(0, 6).map(([k, v]) => (
          <div key={k} className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0' }}>
            <span style={{ color: 'var(--fg)' }}>{k}</span>: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
          </div>
        ))}
        {Object.entries(staticCov).slice(0, 4).map(([k, v]) => (
          <div key={k} className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0' }}>
            static {k}: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
          </div>
        ))}
        {Object.keys(limitations).length > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
            coverage capability gap: {Object.keys(limitations).join(', ')}
          </div>
        )}
      </Section>
    </div>
  );
};

const TodoPanel = () => {
  const [view, setView] = React.useState('compact'); // compact | detail | graph
  const [openId, setOpenId] = React.useState(null);
  // Per-group collapse state in compact view: {approved: true, ...}
  // means that group is collapsed. Defaults set via collapsedDefault
  // inside the render so they're not duplicated.
  const [collapsedTodoGroups, setCollapsedTodoGroups] = React.useState({});
  const todos = window.TODOS;
  // "Done" counter spans every terminal state (done/approved/completed)
  // — without this, the counter showed 0/7 for tasks the agent had
  // explicitly approved because raw 'approved' status now flows
  // through unchanged from data.jsx.
  const done = todos.filter(t => ['done', 'approved', 'completed'].includes(t.state)).length;

  // Map every status to a glyph + color so the right panel reads at a
  // glance. data.jsx normalizes TodoTracker statuses
  // (pending/in_progress/completed/approved/rejected) into the simpler
  // pending/active/done used by this UI; the renderer below also keeps
  // explicit cases for the raw statuses so live updates render right.
  const stateCfg = (s) => {
    switch (s) {
      // Auto-finished by the agent (no explicit human nod)
      case 'done':        return { glyph: '☑', color: '#3fb950', label: 'done' };
      case 'completed':   return { glyph: '✓', color: '#3fb950', label: 'completed' };
      // Explicitly approved by a human — distinct glyph + accent
      // colour so the pending/approved distinction reads at a glance
      case 'approved':    return { glyph: '★', color: 'var(--accent, #58a6ff)', label: 'approved' };
      case 'active':      return { glyph: '◉', color: '#58a6ff', label: 'in-progress' };
      case 'in_progress': return { glyph: '◉', color: '#58a6ff', label: 'in-progress' };
      case 'rejected':    return { glyph: '✕', color: '#f85149', label: 'rejected' };
      // Hollow square + warm warn-yellow so it never reads as "done"
      case 'pending':     return { glyph: '☐', color: '#e8a82a', label: 'pending' };
      default:            return { glyph: '☐', color: 'var(--fg-mute)', label: s || '?' };
    }
  };

  // Counts per state for the header summary
  const counts = todos.reduce((acc, t) => {
    const cfg = stateCfg(t.state);
    acc[cfg.label] = (acc[cfg.label] || 0) + 1;
    return acc;
  }, {});

  // ── header tab strip
  const Tab = ({ id, label }) => (
    <span onClick={() => setView(id)} style={{
      cursor: 'pointer', padding: '4px 10px', fontSize: 10, letterSpacing: '0.06em',
      textTransform: 'uppercase', fontFamily: 'var(--mono)',
      color: view === id ? 'var(--fg)' : 'var(--fg-mute)',
      background: view === id ? 'var(--bg-2)' : 'transparent',
      border: `1px solid ${view === id ? 'var(--accent)' : 'var(--line)'}`,
      borderRadius: 2,
    }}>{label}</span>
  );

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{
        padding: '8px 12px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, flexWrap: 'wrap',
      }}>
        <span className="mute" style={{ fontFamily: 'var(--mono)' }}>{done}/{todos.length}</span>
        {/* color-coded count chips per state */}
        {['in-progress','pending','done','approved','completed','rejected'].filter(k => counts[k]).map(k => {
          const c = stateCfg(k === 'done' ? 'done' : k.replace('-', '_'));
          return (
            <span key={k} style={{
              fontSize: 10, padding: '1px 6px', borderRadius: 8,
              border: `1px solid ${c.color}`, color: c.color,
            }}>{counts[k]} {k}</span>
          );
        })}
        <span style={{ flex: 1 }} />
        <span title="Clear all todos"
          onClick={() => { if (confirm('Clear all todos?')) window.atlasData.clearTodos(); }}
          style={{
            cursor: 'pointer', fontSize: 10, padding: '2px 8px',
            border: '1px solid var(--line)', color: 'var(--fg-mute)',
            borderRadius: 2,
          }}>✕ clear</span>
        <span className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>view</span>
        <Tab id="compact" label="list" />
        <Tab id="detail" label="detail" />
        <Tab id="graph" label="graph" />
      </div>

      {/* Progress bar — at-a-glance "X / Y approved" with green fill */}
      {todos.length > 0 && (
        <div style={{ padding: '6px 12px 4px', borderBottom: '1px solid var(--line)',
                       background: 'var(--bg-2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
                         fontSize: 10, fontFamily: 'var(--mono)',
                         color: 'var(--fg-mute)', marginBottom: 3 }}>
            <span>progress</span>
            <span><b style={{ color: 'var(--ok)' }}>{done}</b> / {todos.length} approved</span>
          </div>
          <div style={{ height: 4, background: 'var(--bg-3)',
                         border: '1px solid var(--line)', borderRadius: 2,
                         overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${todos.length ? Math.round(100 * done / todos.length) : 0}%`,
              background: '#3fb950',
              transition: 'width 240ms ease-out',
            }} />
          </div>
        </div>
      )}

      <div style={{ flex: 1, overflow: 'auto' }}>
        {view === 'compact' && (() => {
          // Group by status order: in_progress → pending → completed →
          // rejected → approved (approved collapsed by default since it's
          // usually the long tail of "done" todos that the user no longer
          // needs to scan).
          const groupOf = (t) => {
            const s = t.state;
            if (s === 'active' || s === 'in_progress') return 'in_progress';
            if (s === 'completed') return 'completed';
            if (s === 'approved' || s === 'done') return 'approved';
            if (s === 'rejected') return 'rejected';
            return 'pending';
          };
          const groups = { in_progress: [], pending: [], completed: [], rejected: [], approved: [] };
          todos.forEach(t => groups[groupOf(t)].push(t));
          const order = ['in_progress', 'pending', 'completed', 'rejected', 'approved'];
          const labels = {
            in_progress: 'IN PROGRESS', pending: 'PENDING',
            completed: 'COMPLETED',     rejected: 'REJECTED', approved: 'APPROVED',
          };
          // approved + rejected default-collapsed; in-progress/pending/completed default-open
          const collapsedDefault = { approved: true, rejected: true };
          const isCollapsed = (g) => collapsedTodoGroups[g] !== undefined
            ? collapsedTodoGroups[g] : (collapsedDefault[g] || false);
          const toggleGroup = (g) => setCollapsedTodoGroups(prev =>
            ({ ...prev, [g]: !isCollapsed(g) }));
          return (
            <div style={{ padding: '4px 0' }}>
              {order.map(g => {
                const items = groups[g];
                if (!items.length) return null;
                const collapsed = isCollapsed(g);
                const cfg = stateCfg(g === 'in_progress' ? 'in_progress' : g);
                return (
                  <div key={g}>
                    {/* Group divider — uppercase label, click to toggle */}
                    <div
                      onClick={() => toggleGroup(g)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '4px 12px 2px', cursor: 'pointer',
                        fontFamily: 'var(--mono)', fontSize: 9,
                        letterSpacing: '0.1em', textTransform: 'uppercase',
                        color: cfg.color, userSelect: 'none',
                      }}
                    >
                      <span>{collapsed ? '▸' : '▾'}</span>
                      <span>{labels[g]}</span>
                      <span style={{ flex: 1, height: 1, background: 'var(--line)',
                                       opacity: 0.5, marginLeft: 6 }} />
                      <span className="mute">{items.length}</span>
                    </div>
                    {!collapsed && items.map(t => {
                      const tcfg = stateCfg(t.state);
                      const open = openId === t.id;
                      return (
                        <div key={t.id}>
                          <div
                            onClick={() => setOpenId(open ? null : t.id)}
                            style={{
                              display: 'grid', gridTemplateColumns: '24px 36px 1fr 16px',
                              alignItems: 'baseline', gap: 6, padding: '4px 12px',
                              cursor: 'pointer', fontFamily: 'var(--mono)', fontSize: 12,
                              background: t.state === 'active' || t.state === 'in_progress'
                                ? 'color-mix(in oklch, var(--accent) 8%, transparent)'
                                : 'transparent',
                              borderLeft: (t.state === 'active' || t.state === 'in_progress')
                                ? '2px solid var(--accent)' : '2px solid transparent',
                            }}
                          >
                            <span style={{ color: tcfg.color, fontSize: 13 }}>{tcfg.glyph}</span>
                            <span className="mute" style={{ fontSize: 11 }}>{t.section}</span>
                            <span style={{ color: t.state === 'pending' ? 'var(--fg-mute)' : 'var(--fg)' }}>{t.title}</span>
                            <span className="mute" style={{ fontSize: 10 }}>{open ? '▾' : '▸'}</span>
                          </div>
                          {open && (
                            <div className="mute fade-in" style={{
                              padding: '6px 12px 10px 64px', fontSize: 11, lineHeight: 1.5,
                              borderLeft: '2px solid var(--line)', marginLeft: 12, marginRight: 12,
                              background: 'var(--bg-2)',
                            }}>
                              {t.detail}
                              {t.deps && t.deps.length > 0 && (
                                <div style={{ marginTop: 4, fontSize: 10 }}>
                                  <span className="mute">deps:</span>{' '}
                                  {t.deps.map(d => <span key={d} className="acc">§{d} </span>)}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          );
        })()}

        {view === 'detail' && (
          <div>
            {todos.map(t => {
              const cfg = stateCfg(t.state);
              return (
                <div key={t.id} style={{
                  padding: '10px 14px', borderBottom: '1px solid var(--line)',
                  background: t.state === 'active' ? 'var(--bg-2)' : 'transparent',
                  borderLeft: t.state === 'active' ? '2px solid var(--accent)' : '2px solid transparent',
                }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: 14, color: cfg.color }}>{cfg.glyph}</span>
                    <span className="mute" style={{ fontSize: 11 }}>{t.section}</span>
                    <span style={{ fontWeight: t.state === 'active' ? 500 : 400, flex: 1, fontSize: 12 }}>{t.title}</span>
                  </div>
                  <div className="mute" style={{ fontSize: 11, marginTop: 4, marginLeft: 22, lineHeight: 1.4 }}>{t.detail}</div>
                </div>
              );
            })}
          </div>
        )}

        {view === 'graph' && <TodoGraph todos={todos} openId={openId} setOpenId={setOpenId} />}
      </div>
    </div>
  );
};

// ── Graph view: SVG DAG laid out by topological level ─────────────
const TodoGraph = ({ todos, openId, setOpenId }) => {
  // assign each node a level = max(level of deps) + 1
  const levelOf = {};
  todos.forEach(t => {
    levelOf[t.id] = (t.deps || []).reduce((m, d) => Math.max(m, (levelOf[d] ?? 0) + 1), 0);
  });
  const levels = {};
  todos.forEach(t => { (levels[levelOf[t.id]] = levels[levelOf[t.id]] || []).push(t); });
  const levelKeys = Object.keys(levels).map(Number).sort((a, b) => a - b);

  const W = 320, NODE_W = 80, NODE_H = 32, gapY = 10, gapX = 22, padX = 10, padY = 10;
  const colW = NODE_W + gapX;
  const totalW = padX * 2 + colW * levelKeys.length - gapX;
  const maxRow = Math.max(...levelKeys.map(k => levels[k].length));
  const totalH = padY * 2 + maxRow * (NODE_H + gapY) - gapY;

  const pos = {};
  levelKeys.forEach((lvl, ci) => {
    const col = levels[lvl];
    const colH = col.length * (NODE_H + gapY) - gapY;
    const yStart = padY + (totalH - padY * 2 - colH) / 2;
    col.forEach((t, ri) => {
      pos[t.id] = {
        x: padX + ci * colW,
        y: yStart + ri * (NODE_H + gapY),
      };
    });
  });

  const stateCfg = (s) =>
    s === 'done'   ? { fill: 'color-mix(in oklch, var(--ok) 14%, transparent)',     stroke: 'var(--ok)',     glyph: '✓', color: 'var(--ok)' } :
    s === 'active' ? { fill: 'color-mix(in oklch, var(--accent) 14%, transparent)', stroke: 'var(--accent)', glyph: '●', color: 'var(--accent)' } :
                     { fill: 'transparent',                                          stroke: 'var(--line)',   glyph: '○', color: 'var(--fg-mute)' };

  return (
    <div style={{ padding: 12 }}>
      <div className="mute" style={{ fontSize: 10, marginBottom: 8, fontFamily: 'var(--mono)' }}>
        ── DAG · {levelKeys.length} levels · click a node · ↔ scroll
      </div>
      <div style={{ overflowX: 'auto', overflowY: 'hidden', border: '1px solid var(--line)', borderRadius: 2, background: 'var(--bg-2)' }}>
      <svg width={totalW} height={totalH} style={{ display: 'block' }}>
        {/* edges */}
        <defs>
          <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--fg-mute)" />
          </marker>
        </defs>
        {todos.flatMap(t => (t.deps || []).map(d => {
          const a = pos[d], b = pos[t.id];
          if (!a || !b) return null;
          const x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2;
          const x2 = b.x,           y2 = b.y + NODE_H / 2;
          const mx = (x1 + x2) / 2;
          return (
            <path key={`${d}->${t.id}`}
              d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
              fill="none" stroke="var(--line)" strokeWidth="1"
              markerEnd="url(#arr)"
            />
          );
        }))}
        {/* nodes */}
        {todos.map(t => {
          const p = pos[t.id], cfg = stateCfg(t.state);
          const sel = openId === t.id;
          return (
            <g key={t.id}
              onClick={() => setOpenId(sel ? null : t.id)}
              style={{ cursor: 'pointer' }}
            >
              <rect x={p.x} y={p.y} width={NODE_W} height={NODE_H} rx="2"
                fill={cfg.fill} stroke={sel ? 'var(--fg)' : cfg.stroke}
                strokeWidth={sel ? 2 : 1}
              />
              <text x={p.x + 6} y={p.y + 12} fontSize="8" fill="var(--fg-mute)"
                fontFamily="var(--mono)" letterSpacing="0.04em">{t.section}</text>
              <text x={p.x + NODE_W - 6} y={p.y + 12} fontSize="9" textAnchor="end"
                fill={cfg.color} fontFamily="var(--mono)" fontWeight="700">{cfg.glyph}</text>
              <text x={p.x + 6} y={p.y + 24} fontSize="9" fill="var(--fg)"
                fontFamily="var(--mono)">
                {t.title.length > 11 ? t.title.slice(0, 10) + '…' : t.title}
              </text>
            </g>
          );
        })}
      </svg>
      </div>
      {openId && (
        <div className="fade-in" style={{
          marginTop: 12, padding: '8px 10px', borderLeft: '2px solid var(--accent)',
          background: 'var(--bg-2)', fontFamily: 'var(--mono)', fontSize: 11, lineHeight: 1.5,
        }}>
          {(() => {
            const t = todos.find(x => x.id === openId);
            if (!t) return null;
            const cfg = stateCfg(t.state);
            return (
              <>
                <div>
                  <span style={{ color: cfg.color, fontWeight: 700 }}>{cfg.glyph}</span>{' '}
                  <span className="mute">{t.section}</span>{' '}
                  <span style={{ color: 'var(--fg)' }}>{t.title}</span>
                </div>
                <div className="mute" style={{ marginTop: 4 }}>{t.detail}</div>
                <div style={{ marginTop: 4, fontSize: 10 }}>
                  <span className="mute">deps:</span>{' '}
                  {(t.deps && t.deps.length) ? t.deps.map(d => <span key={d} className="acc">§{d} </span>) : <span className="mute">(none)</span>}
                </div>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

// ── Git panel — branch / changes / diff / commit / push ──────────
// Hits /api/git/{status,diff,commit,push}. Read-only by default;
// commit + push require the user to fill the message and click the
// big buttons. Status mark mapping (XY from `git status --porcelain`):
//   M = modified   A = added   D = deleted   R = renamed
//   ? = untracked  !  = ignored (we don't show those)
const GIT_STATUS_GLYPH = {
  M: { ch: 'M', color: '#d29922' },   // yellow
  A: { ch: 'A', color: '#3fb950' },   // green
  D: { ch: 'D', color: '#f85149' },   // red
  R: { ch: 'R', color: '#a371f7' },   // purple
  '?': { ch: '?', color: 'var(--fg-mute)' },
  ' ': { ch: ' ', color: 'var(--fg-mute)' },
};
const _statusGlyph = (xy) => {
  const a = GIT_STATUS_GLYPH[xy[0]] || GIT_STATUS_GLYPH[' '];
  const b = GIT_STATUS_GLYPH[xy[1]] || GIT_STATUS_GLYPH[' '];
  return { staged: a, work: b };
};

const GitPanel = () => {
  const [branch, setBranch] = React.useState('');
  const [ahead, setAhead]   = React.useState(0);
  const [behind, setBehind] = React.useState(0);
  const [files, setFiles]   = React.useState([]);
  const [error, setError]   = React.useState('');
  const [selected, setSelected] = React.useState(null);
  const [diff, setDiff]     = React.useState('');
  const [diffLoading, setDiffLoading] = React.useState(false);
  const [message, setMessage] = React.useState('');
  const [busy, setBusy]     = React.useState('');   // '' | 'commit' | 'push'
  const [lastResult, setLastResult] = React.useState(null);

  const refresh = React.useCallback(async () => {
    try {
      const r = await fetch('/api/git/status');
      const d = await r.json();
      setBranch(d.branch || ''); setAhead(d.ahead || 0); setBehind(d.behind || 0);
      setFiles(d.files || []); setError(d.error || '');
    } catch (e) { setError(String(e)); }
  }, []);

  React.useEffect(() => { refresh(); const id = setInterval(refresh, 5000); return () => clearInterval(id); }, [refresh]);

  // When user clicks a file, fetch its diff (cached as `selected`)
  React.useEffect(() => {
    if (!selected) { setDiff(''); return; }
    let cancelled = false;
    setDiffLoading(true);
    fetch('/api/git/diff?path=' + encodeURIComponent(selected))
      .then(r => r.json())
      .then(d => { if (!cancelled) { setDiff(d.diff || d.error || ''); setDiffLoading(false); } })
      .catch(e => { if (!cancelled) { setDiff(String(e)); setDiffLoading(false); } });
    return () => { cancelled = true; };
  }, [selected, files.length]);

  const doCommit = async () => {
    if (!message.trim()) { alert('Commit message required.'); return; }
    setBusy('commit');
    try {
      const r = await fetch('/api/git/commit', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, add_all: true }),
      });
      const d = await r.json();
      setLastResult({ kind: 'commit', ...d });
      if (d.ok) setMessage('');
      refresh();
    } finally { setBusy(''); }
  };

  const doPush = async () => {
    if (!confirm('Push branch "' + (branch || '?') + '" to origin?')) return;
    setBusy('push');
    try {
      const r = await fetch('/api/git/push', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
      });
      const d = await r.json();
      setLastResult({ kind: 'push', ...d });
      refresh();
    } finally { setBusy(''); }
  };

  const stagedCount   = files.filter(f => f.staged).length;
  const unstagedCount = files.filter(f => f.unstaged).length;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, fontSize: 12 }}>
      {/* Branch / ahead-behind / refresh */}
      <div style={{
        padding: '6px 10px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--mono)',
      }}>
        <span className="mute" style={{ fontSize: 10 }}>branch</span>
        <span className="acc" style={{ fontWeight: 600 }}>{branch || '(none)'}</span>
        {ahead  > 0 && <span className="ok"  style={{ fontSize: 10 }}>↑{ahead}</span>}
        {behind > 0 && <span className="warn" style={{ fontSize: 10 }}>↓{behind}</span>}
        <span style={{ flex: 1 }} />
        <span onClick={refresh} title="refresh git status"
              style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 13, padding: '0 6px' }}>↻</span>
      </div>

      {/* File list */}
      <div style={{ borderBottom: '1px solid var(--line)', maxHeight: 200, overflow: 'auto' }}>
        {error && <div className="warn" style={{ padding: '8px 10px', fontSize: 11 }}>{error}</div>}
        {!error && files.length === 0 && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            (working tree clean)
          </div>
        )}
        {files.map((f, i) => {
          const sg = _statusGlyph(f.status || '  ');
          const isSel = selected === f.path;
          return (
            <div key={i}
              onClick={() => setSelected(f.path)}
              title={f.path + ' · ' + (f.status || '')}
              style={{
                display: 'grid', gridTemplateColumns: '20px 1fr auto', gap: 6,
                padding: '3px 10px', cursor: 'pointer', fontFamily: 'var(--mono)',
                background: isSel ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                borderLeft: isSel ? '2px solid var(--accent)' : '2px solid transparent',
              }}>
              <span style={{ color: sg.staged.color, fontWeight: 700 }}>{sg.staged.ch}{sg.work.ch}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{f.path}</span>
              <span style={{ fontSize: 10 }}>
                {f.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{f.added}</span>}
                {f.removed != null && <span className="err">−{f.removed}</span>}
              </span>
            </div>
          );
        })}
      </div>

      {/* Diff viewer for selected file */}
      <div style={{ flex: 1, overflow: 'auto', borderBottom: '1px solid var(--line)' }}>
        {!selected && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            Click a file above to view its diff.
          </div>
        )}
        {selected && (
          <pre className="code" style={{
            margin: 0, padding: '8px 10px', fontSize: 11, lineHeight: 1.5,
            whiteSpace: 'pre', fontFamily: 'var(--mono)',
          }}>
            {diffLoading ? 'loading…' :
              (diff || '').split('\n').map((line, i) => {
                let color = 'var(--fg)';
                let bg = 'transparent';
                if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff ') || line.startsWith('@@') || line.startsWith('index ')) {
                  color = 'var(--accent)';
                } else if (line.startsWith('+')) {
                  color = '#7ee787'; bg = 'color-mix(in oklch, #3fb950 12%, transparent)';
                } else if (line.startsWith('-')) {
                  color = '#ffa198'; bg = 'color-mix(in oklch, #f85149 12%, transparent)';
                }
                return <div key={i} style={{ color, background: bg }}>{line || ' '}</div>;
              })
            }
          </pre>
        )}
      </div>

      {/* Commit composer */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          {files.length} change{files.length === 1 ? '' : 's'}
          {stagedCount   > 0 && <span className="ok"   style={{ marginLeft: 6 }}>{stagedCount} staged</span>}
          {unstagedCount > 0 && <span className="warn" style={{ marginLeft: 6 }}>{unstagedCount} unstaged</span>}
        </div>
        <textarea
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder="Commit message — first line = summary, blank line + body for details"
          rows={3}
          style={{
            background: 'var(--bg-3)', border: '1px solid var(--line)',
            borderRadius: 2, padding: '6px 8px', fontSize: 12,
            fontFamily: 'var(--mono)', color: 'var(--fg)', resize: 'vertical',
            outline: 'none', minHeight: 50,
          }}
        />
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className="btn primary"
            disabled={busy !== '' || !message.trim() || files.length === 0}
            onClick={doCommit}
            style={{ flex: 1 }}>
            {busy === 'commit' ? 'committing…' : 'commit ↵'}
          </button>
          <button
            className="btn"
            disabled={busy !== '' || !branch}
            onClick={doPush}>
            {busy === 'push' ? 'pushing…' : ('push ↑' + (ahead ? ahead : ''))}
          </button>
        </div>
        {lastResult && (
          <div style={{
            fontSize: 10, padding: '4px 6px', borderRadius: 2,
            background: lastResult.ok ? 'color-mix(in oklch, var(--ok) 12%, transparent)'
                                       : 'color-mix(in oklch, var(--warn) 12%, transparent)',
            color: lastResult.ok ? 'var(--ok)' : 'var(--warn)',
            fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            maxHeight: 80, overflow: 'auto',
          }}>
            <b>{lastResult.kind}{lastResult.ok ? ' ✓' : ' ✗'}</b>
            {lastResult.stdout && '\n' + lastResult.stdout.trim()}
            {lastResult.stderr && '\n' + lastResult.stderr.trim()}
            {lastResult.error && '\n' + lastResult.error}
          </div>
        )}
      </div>
    </div>
  );
};

const DiffPanel = () => (
  <div className="code" style={{ flex: 1, overflow: 'auto', padding: '12px 14px', fontSize: 12 }}>
    <div className="mute" style={{ marginBottom: 8, fontSize: 11 }}>
      <span className="acc">replace_in_file</span> spi_master/rtl/spi_master.sv
      <span style={{ marginLeft: 12 }} className="ok">+5</span>
      <span style={{ marginLeft: 6 }} className="err">−2</span>
    </div>
    <div style={{ border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
      {window.DIFF_LINES.map((l, i) => (
        <div key={i} style={{
          display: 'grid', gridTemplateColumns: '36px 14px 1fr', gap: 0, padding: '2px 0',
          background: l.kind === 'add' ? 'rgba(89, 192, 138, 0.10)' :
                       l.kind === 'del' ? 'rgba(232, 112, 112, 0.10)' : 'transparent',
          color: l.kind === 'add' ? 'var(--ok)' : l.kind === 'del' ? 'var(--err)' : 'var(--fg)',
          borderLeft: `2px solid ${l.kind === 'add' ? 'var(--ok)' : l.kind === 'del' ? 'var(--err)' : 'transparent'}`,
        }}>
          <span className="mute" style={{ paddingLeft: 8, fontSize: 10 }}>{l.n}</span>
          <span style={{ fontWeight: 700 }}>{l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' '}</span>
          <span style={{ whiteSpace: 'pre' }}>{l.t}</span>
        </div>
      ))}
    </div>
    <div style={{ marginTop: 12, display: 'flex', gap: 6 }}>
      <button className="btn primary">Accept <Kbd>A</Kbd></button>
      <button className="btn">Reject</button>
    </div>
  </div>
);

// ── PreviewPane: in-tab file viewer with Prism syntax highlighting ──
// Inline replacement for the FileViewer modal when the user wants the
// preview alongside (well, replacing) the chat feed via the main tab
// strip. Same /api/file backend; Prism.js handles language detection
// per the PRISM_LANG_MAP set up in index.html.
const PreviewPane = ({ path, onClose }) => {
  const [body, setBody] = React.useState('');
  const [size, setSize] = React.useState(0);
  const [truncated, setTruncated] = React.useState(false);
  const [err, setErr] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const codeRef = React.useRef(null);

  const ext = (path ? (path.split('.').pop() || '') : '').toLowerCase();
  const lang = (window.PRISM_LANG_MAP && window.PRISM_LANG_MAP[ext]) || 'none';
  const isMarkdown = ['md', 'markdown', 'mdown', 'mkdn'].includes(ext);
  const hasGlobPath = !!path && /[*?[\]{}]/.test(path);
  const highlightTooLarge = !isMarkdown && body.length > 60000;
  const canHighlight = !highlightTooLarge && lang !== 'none';

  React.useEffect(() => {
    if (!path) {
      setBody('');
      setErr(null);
      setSize(0);
      setTruncated(false);
      setLoading(false);
      return;
    }
    if (/[*?[\]{}]/.test(path)) {
      setLoading(false);
      setSize(0);
      setTruncated(false);
      setErr('Preview needs one concrete file path; glob patterns are not previewable.');
      setBody(`// ${path}\n// Preview needs one concrete file path, not a glob pattern.\n// Select an exact file from the tree, for example rtl/<module>.sv.`);
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    setLoading(true); setErr(null);
    fetch('/api/file?path=' + encodeURIComponent(path), { signal: controller.signal }).then(async r => {
      let d = {};
      try { d = await r.json(); }
      catch (_) { d = { error: r.statusText || `HTTP ${r.status}` }; }
      if (!r.ok && !d.error) d.error = r.statusText || `HTTP ${r.status}`;
      return d;
    }).then(d => {
      if (cancelled) return;
      clearTimeout(timeout);
      setLoading(false);
      if (d.error) {
        setErr(d.error); setBody(`// ${path}\n// (could not read: ${d.error})`); return;
      }
      setBody(d.content || '');
      setSize(d.size || 0);
      setTruncated(!!d.truncated);
    }).catch(e => {
      if (!cancelled) {
        clearTimeout(timeout);
        const msg = e && e.name === 'AbortError'
          ? 'preview timed out after 8s'
          : String(e);
        setLoading(false);
        setErr(msg);
        setBody(`// ${path}\n// fetch failed: ${msg}`);
      }
    });
    return () => {
      cancelled = true;
      clearTimeout(timeout);
      controller.abort();
    };
  }, [path]);

  // Re-highlight whenever body/lang changes. Prism replaces the
  // <code> contents in place; we set the language class first.
  React.useEffect(() => {
    if (!codeRef.current || !window.Prism) return;
    if (!canHighlight) return;       // skip for plain text or large files
    codeRef.current.className = 'language-' + lang;
    try { window.Prism.highlightElement(codeRef.current); } catch (_) { /* ignore */ }
  }, [body, lang, canHighlight]);

  if (!path) {
    return (
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexDirection: 'column', gap: 12, color: 'var(--fg-mute)', padding: 40,
      }}>
        <div style={{ fontSize: 32, opacity: 0.4 }}>◆</div>
        <div style={{ fontSize: 13 }}>No file selected.</div>
        <div style={{ fontSize: 11 }}>Click any file in the tree on the left to preview it here.</div>
      </div>
    );
  }

  const lineCount = body.split('\n').length;
  const sizeKb = size > 0 ? (size / 1024).toFixed(1) + ' KB' : '';
  const copyPath = () => { try { navigator.clipboard.writeText(path); } catch (_) {} };
  const copyAll  = () => { try { navigator.clipboard.writeText(body);  } catch (_) {} };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* meta strip */}
      <div style={{
        padding: '4px 14px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 10, fontSize: 10,
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
      }}>
        <span>lang <span style={{ color: 'var(--accent)' }}>{isMarkdown ? 'rendered markdown' : (lang === 'none' ? 'plain' : lang)}</span></span>
        <span className="mute">·</span>
        <span>{lineCount} lines</span>
        {sizeKb && <><span className="mute">·</span><span>{sizeKb}</span></>}
        {truncated && <><span className="mute">·</span><span className="warn">truncated at {Math.round((body.length || 0) / 1024)}KB</span></>}
        {highlightTooLarge && <><span className="mute">·</span><span className="warn">syntax highlight skipped for speed</span></>}
        {hasGlobPath && <><span className="mute">·</span><span className="warn">glob path</span></>}
        <span style={{ flex: 1 }} />
        <span onClick={copyAll}  style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>copy</span>
        <span onClick={copyPath} style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>copy path</span>
      </div>
      {err && (
        <div style={{
          padding: '6px 14px',
          borderBottom: '1px solid var(--err)',
          background: 'color-mix(in oklch, var(--err) 12%, transparent)',
          color: 'var(--err)',
          fontFamily: 'var(--mono)',
          fontSize: 10,
        }}>
          preview error: {err}
        </div>
      )}
      {/* code body — theme-aware background so light mode stays light.
          Markdown files (.md) get full marked → DOMPurify → md-agent
          rendering instead of raw text + Prism, so the same headings/
          code-fence/table styling used for the agent's chat replies
          applies to README/guide files in the preview tab. */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto', background: isMarkdown ? 'var(--bg)' : 'var(--bg-3)' }}>
        {loading ? (
          <div style={{ padding: 16, color: 'var(--fg-mute)', fontFamily: 'var(--code-font, var(--mono))', fontSize: 12 }}>
            loading {path}…
          </div>
        ) : isMarkdown ? (
          body.trim() ? (
            <div
              className="md-agent md-preview"
              dangerouslySetInnerHTML={{ __html: _markdownHtml(body) }}
              ref={_postProcessMarkdownNode}
            />
          ) : (
            <div className="md-preview-empty">empty markdown file</div>
          )
        ) : (
          <pre style={{
            margin: 0, padding: '12px 16px',
            fontFamily: 'var(--code-font, var(--mono))', fontSize: 12, lineHeight: 1.55,
            whiteSpace: 'pre', tabSize: 4,
            background: 'transparent',
            color: 'var(--fg)',
          }}>
            <code ref={codeRef} className={canHighlight ? ('language-' + lang) : ''}>
              {body}
            </code>
          </pre>
        )}
      </div>
    </div>
  );
};

// ── File viewer modal — fetches real content from /api/file ────────
const FileViewer = ({ name, onClose }) => {
  const [body, setBody] = React.useState('# loading…');
  const [size, setSize] = React.useState(0);
  const [truncated, setTruncated] = React.useState(false);
  const [err, setErr] = React.useState(null);
  const ext = (name.split('.').pop() || '').toLowerCase();

  React.useEffect(() => {
    const onEsc = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onEsc);
    return () => window.removeEventListener('keydown', onEsc);
  }, [onClose]);

  React.useEffect(() => {
    let cancelled = false;
    setBody('# loading…'); setErr(null);
    window.atlasData.fetchFile(name).then(d => {
      if (cancelled) return;
      if (d.error) {
        setErr(d.error);
        setBody(`// ${name}\n// (could not read: ${d.error})`);
        return;
      }
      setBody(d.content || '');
      setSize(d.size || 0);
      setTruncated(!!d.truncated);
    }).catch(e => {
      if (!cancelled) {
        setErr(String(e));
        setBody(`// ${name}\n// (fetch failed: ${e})`);
      }
    });
    return () => { cancelled = true; };
  }, [name]);

  const lineCount = body.split('\n').length;
  const sizeKb = size > 0 ? (size / 1024).toFixed(1) + ' KB' : '';

  const copyPath = () => {
    try { navigator.clipboard.writeText(name); } catch (_) {}
  };

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 40,
    }}>
      <div onClick={(e) => e.stopPropagation()} className="box" style={{
        width: 'min(900px, 100%)', height: 'min(680px, 100%)',
        display: 'flex', flexDirection: 'column', background: 'var(--bg)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.45)',
      }}>
        <div className="box-h" style={{ padding: '8px 14px' }}>
          <span style={{ color: 'var(--fg-mute)', marginRight: 6 }}>◆</span>
          <span style={{ color: 'var(--fg)' }}>{name}</span>
          <span className="mute" style={{ marginLeft: 10, textTransform: 'none', letterSpacing: 0, fontSize: 11 }}>
            · {ext || 'file'} · read-only{sizeKb ? ` · ${sizeKb}` : ''}{truncated ? ' · truncated' : ''}
          </span>
          <span style={{ flex: 1 }} />
          <button className="btn" onClick={onClose} style={{ fontSize: 11 }}>Close <Kbd>Esc</Kbd></button>
        </div>
        <pre className="code" style={{
          flex: 1, overflow: 'auto', padding: 16, margin: 0, fontSize: 12, lineHeight: 1.55,
          whiteSpace: 'pre', color: err ? 'var(--warn)' : 'var(--fg)',
        }}>{body}</pre>
        <div style={{ borderTop: '1px solid var(--line)', padding: '8px 14px', display: 'flex', gap: 8, fontSize: 11 }}>
          <span className="mute">{lineCount} lines{truncated ? ' (truncated)' : ''}</span>
          <span style={{ flex: 1 }} />
          <button className="btn" onClick={copyPath}>Copy path</button>
        </div>
      </div>
    </div>
  );
};

// ── conversation hydration mode (left column footer) ───────────────
// Picks which on-disk source the chat feed is rebuilt from on a
// session refresh / page reload. The mode is persisted in
// localStorage and read by data.jsx's refreshSessionState which
// passes it through as a `mode` query param to /api/session/state.
//   • conversation  — recent rolling window (conversation.json). Default.
//   • full          — every message ever (full_conversation.json).
//   • recent        — last 50 messages of full_conversation.json.
const ConvModeSelector = () => {
  const initial = (() => {
    try { return localStorage.getItem('atlasConversationMode') || 'conversation'; }
    catch (_) { return 'conversation'; }
  })();
  const [mode, setMode] = React.useState(initial);
  const apply = (next) => {
    setMode(next);
    try { localStorage.setItem('atlasConversationMode', next); } catch (_) {}
    if (window.atlasData && window.atlasData.refreshSessionState) {
      window.atlasData.refreshSessionState(window.ACTIVE_SESSION || '', true, { mode: next });
    }
  };
  const Pill = ({ id, label, title }) => (
    <span
      onClick={() => apply(id)}
      title={title}
      style={{
        cursor: 'pointer',
        padding: '2px 6px',
        fontSize: 10,
        fontFamily: 'var(--mono)',
        letterSpacing: '0.02em',
        textTransform: 'uppercase',
        color: mode === id ? 'var(--bg)' : 'var(--fg-mute)',
        background: mode === id ? 'var(--accent)' : 'transparent',
        border: '1px solid ' + (mode === id ? 'var(--accent)' : 'var(--line)'),
        borderRadius: 2,
        whiteSpace: 'nowrap',
        flex: '0 0 auto',
      }}
    >{label}</span>
  );
  return (
    <div style={{
      // Sit a little above the bottom edge of the left column so the
      // pills don't visually merge with the splitter line.
      marginBottom: 24,
      border: '1px solid var(--line)',
      borderRadius: 2,
      padding: '6px 8px',
      fontSize: 10, color: 'var(--fg-mute)',
      display: 'flex', alignItems: 'center', gap: 4,
      // No flexWrap — keep all three pills on one row even in a narrow
      // left column. Drop the "history" label text so the pills get
      // every available pixel without wrapping `full` to a new line.
      flexWrap: 'nowrap',
      overflow: 'hidden',
    }}
    title="Conversation hydration source on session reload">
      <Pill id="conversation" label="recent" title="conversation.json — recent rolling window (default)" />
      <Pill id="full"         label="full"   title="every message from full_conversation.json" />
    </div>
  );
};

// ── ATLAS status panel ─────────────────────────────────────────────
const AgentStatusPanel = ({ intent, workflow, onCollapse }) => {
  // Live context — populated by /healthz + WS 'context' events.
  const _ctx = window.CONTEXT || {};
  const [liveStageStatus, setLiveStageStatus] = React.useState(null);
  React.useEffect(() => {
    let alive = true;
    const refresh = () => {
      fetch('/api/soc')
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          if (!alive || !d) return;
          const mods = (d.clusters || []).flatMap(c => Array.isArray(c.modules) ? c.modules : []);
          const scoped = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
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
  const ctxUsed = (_ctx.tokens || 0) / 1000;             // → K tokens
  const ctxMax  = Math.max(1, (_ctx.maxTokens || 1000000) / 1000);  // → K
  const pct = Math.min(100, Math.round((ctxUsed / ctxMax) * 100));
  return (
    <div className="box" style={{ flexShrink: 0 }}>
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
      <div style={{ padding: '10px 14px', fontSize: 11, fontFamily: 'var(--mono)' }}>
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
          <span style={{ color: 'var(--fg)' }} title={_ctx.baseUrl}>
            {_ctx.model || '—'}
          </span>
        </div>
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
          <span className="mute">Context</span>
          <span>
            <span style={{ color: 'var(--fg)' }}>
              {ctxUsed >= 1000 ? (ctxUsed/1000).toFixed(2) + 'M' : ctxUsed.toFixed(1) + 'K'}
            </span>
            <span className="mute"> / {ctxMax >= 1000 ? (ctxMax/1000) + 'M' : ctxMax + 'K'} · </span>
            <span className={pct > 70 ? 'warn' : 'ok'}>{pct}%</span>
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
          const ti = _ctx.tokensIn    || 0;
          const tc = _ctx.tokensCache || 0;
          const to = _ctx.tokensOut   || 0;
          const cIn   = ti * pi / 1e6;
          const cCach = tc * pc / 1e6;
          const cOut  = to * po / 1e6;
          const cTot  = cIn + cCach + cOut;
          return (
            <>
              <div className="mute" style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
                Cost {_ctx.pricing && (
                  <span className="mute" style={{ fontSize: 9, fontWeight: 400, letterSpacing: 0, textTransform: 'none', marginLeft: 4 }}>
                    @ ${pi}/${pc}/${po} per 1M
                  </span>
                )}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr 70px', gap: 4, fontSize: 11, lineHeight: 1.55 }}>
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

        {/* ── pipeline · ATLAS (this session) ─────────────────────── */}
        <div className="mute" style={{
          fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase',
          marginTop: 14, marginBottom: 6,
          display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap',
        }}>
          <span style={{ color: 'var(--accent)', fontWeight: 700 }}>▸ atlas</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>· session</span>
          <span style={{ flex: 1 }} />
          <span className="ok" style={{ fontSize: 9 }}>● live</span>
        </div>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4,
          fontSize: 10, marginBottom: 12,
        }}>
          {(() => {
            const st = liveStageStatus || {};
            const normalize = (v) => v === 'ok' || v === 'pass' ? 'done'
              : v === 'partial' || v === 'approved' || v === 'planned' || v === 'blocked' ? 'active'
              : v === 'err' || v === 'error' || v === 'fail' || v === 'rejected' ? 'err'
              : 'pending';
            const simDebugReady = st.sim_debug === 'ok' || (st.sim === 'ok' && (st.tb === 'ok' || st.tb === 'partial'));
            return [
              { id: 'ssot', label: 'SSOT', state: normalize(st.ssot) },
              { id: 'rtl',  label: 'RTL',  state: normalize(st.rtl) },
              { id: 'tb',   label: 'TB',   state: normalize(st.tb) },
              { id: 'dbg',  label: 'SIMDBG',  state: simDebugReady ? 'done' : normalize(st.sim_debug) },
            ];
          })().map(s => {
            const cfg = s.state === 'done'    ? { color: 'var(--ok)',     glyph: '✓', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)',     border: 'var(--ok)' }
                      : s.state === 'active'  ? { color: 'var(--accent)', glyph: '●', bg: 'color-mix(in oklch, var(--accent) 14%, transparent)', border: 'var(--accent)' }
                      : s.state === 'err'     ? { color: 'var(--err)',    glyph: '✗', bg: 'color-mix(in oklch, var(--err) 14%, transparent)',    border: 'var(--err)' }
                      :                         { color: 'var(--fg-mute)',glyph: '○', bg: 'transparent',                                          border: 'var(--line)' };
            return (
              <div key={s.id} style={{
                border: `1px solid ${cfg.border}`, borderRadius: 2,
                padding: '4px 6px', textAlign: 'center', background: cfg.bg,
                fontFamily: 'var(--mono)',
              }}>
                <div style={{ color: cfg.color, fontWeight: 700, fontSize: 10 }}>
                  {cfg.glyph} {s.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ── Hotkey footer (terminal-style) ─────────────────────────────────
const HotkeyFooter = ({ intent, streaming }) => (
  <div style={{
    display: 'flex', gap: 14, padding: '6px 12px', fontSize: 10,
    color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
    background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 2,
    alignItems: 'center', flexWrap: 'wrap',
  }}>
    <span style={{ color: 'var(--accent)', fontWeight: 600 }}>↑</span>
    <span>{(window.CONTEXT && window.CONTEXT.model) || '—'}</span>
    <span style={{ width: 1, height: 12, background: 'var(--line)' }} />
    <span><Kbd>shift+tab</Kbd> {intent === 'plan' ? 'normal' : 'plan'}</span>
    <span><Kbd>⌫⌫</Kbd> {streaming ? 'interrupt' : 'clear'}</span>
    <span><Kbd>ctrl+c</Kbd> quit</span>
    <span><Kbd>ctrl+j</Kbd> newline</span>
    <span><Kbd>shift+drag</Kbd> copy</span>
    <span><Kbd>shift+insert</Kbd> paste</span>
    <span style={{ flex: 1 }} />
    <span className={streaming ? 'acc' : 'ok'}>{streaming ? 'streaming…' : 'ready'}</span>
  </div>
);

window.Workspace = Workspace;
