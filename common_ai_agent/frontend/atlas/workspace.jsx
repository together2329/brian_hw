// workspace.jsx — Chat-centric: ReAct + inline Q&A cards + SSOT/Todo sidebar + file viewer

// ── Column-resize helpers ─────────────────────────────────────────
// useResizable: state + localStorage persistence + clamp.
// `0` is the special "collapsed" value; any positive width is clamped
// to [minW, maxW]. A separate "lastNonZero" remembers the user's last
// open width so collapse → expand restores cleanly.
const useResizable = (initial, storageKey, minW, maxW) => {
  const [w, setW] = React.useState(() => {
    try {
      const raw = parseInt(localStorage.getItem(storageKey), 10);
      if (Number.isFinite(raw) && (raw === 0 || raw >= minW)) {
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

const Workspace = ({ dir, onScreen }) => {
  // Two-axis mode model:
  //   intent: 'normal' | 'plan'   (top-level — shift+tab to swap)
  //   workflow: null | 'ssot' | 'rtl_gen' | 'lint' | 'tb_gen'
  const [intent, setIntent] = React.useState('normal');
  const [workflow, setWorkflow] = React.useState(null);

  // Column widths (drag-resizable, persisted in localStorage).
  // 0 = collapsed; any positive width is clamped to [min, max].
  const [leftW,  setLeftW,  toggleLeft]  = useResizable(230, 'atlasLeftW',  160, 480);
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

  const [feed, setFeed] = React.useState(NORMAL_FEED);

  const refreshFeed = (newIntent /*, newWorkflow */) => {
    setFeed(newIntent === 'plan' ? PLAN_FEED : NORMAL_FEED);
  };

  const switchIntent = (i) => {
    setIntent(i);
    refreshFeed(i, workflow);
    // Tell the BACKEND about the mode swap — local React state alone
    // doesn't change the agent's behaviour. /plan flips agent_mode to
    // 'plan' (no mutating tools); /mode normal flips it back.
    if (window.backend) {
      const cmd = i === 'plan' ? '/plan' : '/mode normal';
      window.backend.send({ type: 'prompt', text: cmd });
    }
  };
  const switchWorkflow = (w) => {
    // Click a workflow chip → fire `/wf <name>` to actually swap the
    // agent's workspace on the server. The slash command is processed
    // locally by the dispatcher (no LLM call) and re-registers the
    // workspace's slash commands. We also update local state so the
    // chip is highlighted.
    const next = workflow === w ? null : w;
    setWorkflow(next);
    refreshFeed(intent, next);
    if (next && window.backend) {
      window.backend.send({ type: 'prompt', text: `/wf ${next}` });
    }
  };
  const [input, setInput] = React.useState('');
  const [showSlash, setShowSlash] = React.useState(false);
  const [slashSel, setSlashSel] = React.useState(0);
  const [streaming, setStreaming] = React.useState(false);
  const [streamText, setStreamText] = React.useState('');
  const [openFile, setOpenFile] = React.useState(null);
  const [rightTab, setRightTab] = React.useState('todo'); // todo | git
  // Main column tab: 'chat' shows the conversation feed; 'preview' shows
  // the contents of the file at previewPath with syntax highlighting.
  // Double-clicking a file in the left tree sets previewPath + flips tab.
  const [mainTab, setMainTab] = React.useState('chat');     // chat | preview
  const [previewPath, setPreviewPath] = React.useState(null);
  // qaState is keyed by flow_id. Dynamic flows are added on-the-fly
  // when the agent emits an ask_user event over the WS.
  const [qaState, setQaState] = React.useState({});

  // Force a re-render when the live data layer (data.jsx) refreshes
  // FILE_TREE / TODOS / SSOT_FILES so dependent panels show fresh data.
  const [, bumpRender] = React.useReducer(x => x + 1, 0);
  React.useEffect(() => {
    const h = () => bumpRender();
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  const inputRef = React.useRef(null);
  const feedRef = React.useRef(null);

  // Derived: the latest unsubmitted qcard in the feed (the "open ask_user tool call")
  const pendingQcard = React.useMemo(() => {
    for (let i = feed.length - 1; i >= 0; i--) {
      const e = feed[i];
      if (e.kind === 'qcard' && !qaState[e.flowId]?.submitted) return e;
    }
    return null;
  }, [feed, qaState]);

  // Keyboard navigation cursor for the ask_user inline form.
  // Index space: 0..opts.length-1 = option rows, opts.length = custom-text row,
  // opts.length+1 = Submit, opts.length+2 = "Chat about this".
  const [askSel, setAskSel] = React.useState(0);
  React.useEffect(() => { setAskSel(0); }, [pendingQcard?.flowId]);

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
  }, [feed, streamText]);

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
    setInput('');
    setShowSlash(false);

    // ── Client-side slash commands ──────────────────────────────
    // Some commands operate on browser state (SCOPE_PATH lives in
    // localStorage / window) and don't need an agent round-trip.
    // Handle them here BEFORE sending anything to the backend.
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
        setFeed(f => [...f, { kind: 'user', text: raw }]);
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
      setFeed(f => [...f, { kind: 'user', text: raw }]);
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
      setFeed(f => [...f, { kind: 'user', text: raw }]);
      if (window.backend) window.backend.send({ type: 'prompt', text: wire });
      // Slash commands don't run the agent — clear any stale streaming
      // state inherited from a prior turn that didn't close out cleanly
      // (agent crash, dropped WS, etc.). Without this, the banner
      // claims "Agent is working" forever after the user types /plan.
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
    const scope = (window.SCOPE_PATH || '').trim();
    let outbound = raw;
    if (scope && !raw.startsWith('/')) {
      outbound = (
        `[scope] You MUST confine every file read, write, edit, grep, ` +
        `find, and run_command to paths inside "${scope}". Do not touch ` +
        `files outside this directory unless I explicitly say so.\n\n` +
        raw
      );
    }
    if (window.backend) window.backend.send({ type: 'prompt', text: outbound });
  };

  // Subscribe to backend events and translate them into feed entries.
  const streamBufferRef = React.useRef('');
  React.useEffect(() => {
    if (!window.backend) return;
    const subs = [];
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
                  { kind: 'thought', text: last.text + '\n' + t }];
        }
        return [...l, { kind: 'thought', text: t }];
      });
    }));
    subs.push(window.backend.subscribe('todo_line', (m) => {
      const t = (m.text || '').trim();
      if (t) setFeed(l => [...l, { kind: 'obs', text: t }]);
    }));
    // Tool call header: agent is about to invoke a tool.
    subs.push(window.backend.subscribe('tool', (m) => {
      const t = (m.text || '').trim();
      if (!t) return;
      // Finalize any pending streaming text first so the tool-call entry
      // sits AFTER the pre-tool reasoning/agent text in the feed.
      const buf = streamBufferRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf }]);
      streamBufferRef.current = '';
      setStreamText('');
      setFeed(l => [...l, { kind: 'action', text: t }]);
    }));
    // Tool observation: the result the agent just received from the tool.
    subs.push(window.backend.subscribe('tool_result', (m) => {
      const t = (m.text || '').trim();
      if (!t) return;
      setFeed(l => [...l, {
        kind: 'obs',
        text: t,
        tool: m.tool || '',
        truncated: !!m.truncated,
      }]);
    }));
    // Park the in-progress streaming buffer into the feed without
    // touching the streaming flag — flush fires AFTER EACH iteration,
    // not just at turn end, so the spinner must keep going until
    // agent_state(running:false) explicitly says we're done.
    const parkBuffer = () => {
      const buf = streamBufferRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf }]);
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
        return [...l, { kind: 'turn_end', text: '✓ end of loop' }];
      });
    };
    subs.push(window.backend.subscribe('flush', parkBuffer));
    subs.push(window.backend.subscribe('done', turnEnd));
    subs.push(window.backend.subscribe('agent_state', (m) => {
      if (m.running === false) turnEnd();
      else if (m.running === true) setStreaming(true);
    }));
    subs.push(window.backend.subscribe('error', (m) => {
      setFeed(l => [...l, { kind: 'agent', text: `[error] ${m.message || ''}` }]);
      streamBufferRef.current = '';
      setStreamText('');
      setStreaming(false);
    }));
    // ask_user → register a dynamic flow and append a qcard to the feed.
    subs.push(window.backend.subscribe('ask_user', (m) => {
      const flowId = m.flow_id;
      if (!flowId) return;
      // Build a synthetic QA_FLOWS entry so the existing AskUserPrompt renders it.
      const opts = (m.options || []).map(o => ({
        id: o.id,
        label: o.label,
        detail: o.detail || '',
        selected: false,
      }));
      window.QA_FLOWS[flowId] = {
        stage: 'Agent', stageDetail: 'ask_user',
        title: m.question || 'Question',
        step: 1, total: 1,
        breadcrumbs: [], activeBreadcrumb: 0,
        question: m.question || '',
        subtitle: m.subtitle || '',
        kind: m.kind === 'multi' ? 'multi' : 'single',
        options: opts,
        history: [], upcoming: [],
        dynamic: true,
      };
      setQaState(s => ({
        ...s,
        [flowId]: { opts: opts.map(o => ({ ...o })), custom: '', submitted: false }
      }));
      setFeed(f => [...f, { kind: 'qcard', flowId, dynamic: true }]);
    }));
    return () => subs.forEach(u => u && u());
  }, []);

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
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitMsg(); }
  };

  // ── question card handlers ─────────────────────────────────────
  const toggleOpt = (flowId, optId) => {
    const flow = window.QA_FLOWS[flowId];
    setQaState(s => {
      const cur = s[flowId];
      if (cur.submitted) return s;
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
    setQaState(s => ({ ...s, [flowId]: { ...s[flowId], custom: val } }));
  };

  // submitCard ships an ask_user answer back to the agent over the WS.
  // All flows that reach this point are dynamic (registered when an
  // ask_user event arrives); the mock SSOT/RTL advance simulator that
  // used to live here has been removed along with the mock data files.
  const submitCard = (flowId) => {
    const st = qaState[flowId];
    if (!st) return;
    const selectedIds = st.opts.filter(o => o.selected).map(o => o.id);
    setQaState(s => ({ ...s, [flowId]: { ...s[flowId], submitted: true } }));
    if (window.backend) {
      window.backend.send({
        type: 'answer',
        flow_id: flowId,
        selected: selectedIds,
        custom: st.custom || '',
      });
    }
    setStreaming(true);  // agent resumes after receiving answer
  };

  // ── layout ─────────────────────────────────────────────────────
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `${leftW}px 4px 1fr 4px ${rightW}px`,
      gap: 12, padding: 16, height: '100%', overflow: 'hidden',
    }}>
      {/* LEFT — Mode/Workflow + Files (collapsed when leftW===0) */}
      {leftW > 0 ? (
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
                    // Single-click: dirs scope-navigate, files just
                    // select (load preview without switching tab) so
                    // the user can scrub through files while keeping
                    // the chat feed visible.
                    if (n.type === 'file') setPreviewPath(fullPath);
                    else window.atlasData.setScopePath(fullPath);
                  }}
                  onDoubleClick={() => {
                    // Double-click: open in preview tab.
                    if (n.type === 'file') {
                      setPreviewPath(fullPath);
                      setMainTab('preview');
                    }
                  }}
                  title={fullPath + (n.type === 'file' ? ' (double-click to preview)' : '')}
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
      </div>
      ) : (
        <div /> /* collapsed — empty grid cell so the 5-track grid stays aligned */
      )}

      {/* LEFT ↔ CENTER splitter — drag to resize, dbl-click toggles collapse */}
      <Splitter width={leftW} side="left" onResize={setLeftW} onToggle={toggleLeft} />

      {/* CENTER — chat feed */}
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
            {/* Tab strip: chat ↔ preview. Click to switch. Preview is
                disabled (greyed) until a file is loaded by single- or
                double-clicking in the file tree. */}
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
              onClick={() => previewPath && setMainTab('preview')}
              title={previewPath ? 'View ' + previewPath : 'Double-click a file in the tree to preview it here'}
              style={{
                cursor: previewPath ? 'pointer' : 'not-allowed',
                padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                color: mainTab === 'preview' ? 'var(--accent)' : (previewPath ? 'var(--fg-mute)' : 'var(--line)'),
                background: mainTab === 'preview' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                border: '1px solid ' + (mainTab === 'preview' ? 'var(--accent)' : 'transparent'),
                fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
              }}
            >preview</span>
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
              </>
            ) : (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}
                    title={previewPath || ''}>
                {previewPath || '(no file selected)'}
              </span>
            )}
            <span style={{ flex: 1 }} />
            {mainTab === 'chat' && (
              <span className="mute" style={{ fontSize: 10, textTransform: 'none', letterSpacing: 0 }}>
                {streaming
                  ? (pendingQcard
                      ? <span className="warn">⏸ waiting on you (ask_user)</span>
                      : <span className="acc">streaming<span className="ascii-spin"></span></span>)
                  : (pendingQcard
                      ? <span className="warn">⏸ waiting on you (ask_user)</span>
                      : <span className="ok">✓ end of loop · ready</span>)}
              </span>
            )}
            {mainTab === 'preview' && (
              <span style={{ fontSize: 10 }}>
                <span className="mute" style={{ marginRight: 8 }}>back to chat</span>
                <span onClick={() => setMainTab('chat')} className="acc"
                      style={{ cursor: 'pointer', padding: '2px 6px',
                               border: '1px solid var(--accent)', borderRadius: 2 }}>↵</span>
              </span>
            )}
          </div>
          {mainTab === 'chat' ? (
            <div ref={feedRef} style={{ flex: 1, overflow: 'auto', padding: '14px 18px' }}>
              {feed.map((entry, i) => (
                <FeedEntry
                  key={i}
                  entry={entry}
                  qaState={qaState}
                  onToggle={toggleOpt}
                  onCustom={setCustom}
                  onSubmit={submitCard}
                  dir={dir}
                />
              ))}
              {/* Streaming preview removed — used to render the in-progress
                  buffer as plain text, then the same text reappeared as a
                  markdown-rendered 'agent' entry on flush, with very
                  different line spacing. The header spinner ("streaming")
                  already signals work-in-progress; the final clean
                  markdown lands once when the buffer parks. */}
            </div>
          ) : (
            <PreviewPane path={previewPath} onClose={() => setMainTab('chat')} />
          )}
        </div>

        {/* prompt */}
        <div style={{ position: 'relative' }}>
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
            const s = pendingQcard
              ? { icon: '⏸', text: 'Waiting on you · answer the ask_user above', color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)' }
              : streaming
                ? { icon: '⚙', text: 'Agent is working — Esc to stop, or type to interrupt', color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)', spin: true }
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
              onChat={() => { setAskSel(0); inputRef.current?.focus(); }}
            />
          ) : (
            <div className="prompt-row">
              <span className="ps" style={{ color: 'var(--fg-mute)' }}>❯</span>
              <input ref={inputRef} value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder='Type a message · "/" for commands · "@" for files'
                autoFocus
              />
              <span className="mute" style={{ fontSize: 11 }}>
                <Kbd>/</Kbd> cmd · <Kbd>@</Kbd> file · <Kbd>↵</Kbd> send
              </span>
            </div>
          )}
        </div>

        {/* hotkey footer — terminal-style */}
        <HotkeyFooter intent={intent} streaming={streaming} />
      </div>

      {/* CENTER ↔ RIGHT splitter — drag to resize, dbl-click toggles collapse */}
      <Splitter width={rightW} side="right" onResize={setRightW} onToggle={toggleRight} />

      {/* RIGHT — UPD Agent status + SSOT/Todo/Diff (collapsed when rightW===0) */}
      {rightW > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        <AgentStatusPanel intent={intent} workflow={workflow}
                          onCollapse={toggleRight} />
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="box-h" style={{ padding: 0 }}>
            <RightTab id="todo" cur={rightTab} onTab={setRightTab}>Todo</RightTab>
            <RightTab id="git"  cur={rightTab} onTab={setRightTab}>Git</RightTab>
          </div>
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
  const [open, setOpen] = React.useState(false);
  const lines = text.split('\n').filter(l => l.trim());
  const firstLine = lines[0] || '';
  const more = lines.length - 1;
  return (
    <div className="react-block thought" style={{ cursor: 'pointer' }}
         onClick={() => setOpen(o => !o)}>
      <span className="rb-tag">thought {more > 0 && `(${lines.length})`}</span>
      {open ? (
        <span style={{ whiteSpace: 'pre-wrap' }}>{text}</span>
      ) : (
        <span style={{ opacity: 0.7 }}>
          {firstLine}
          {more > 0 && <span className="mute" style={{ marginLeft: 6 }}>· +{more} more · click to expand</span>}
        </span>
      )}
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
    // Use marked.js for full markdown rendering (code fences, lists,
    // headings, tables, links). Falls back to the inline renderer if
    // marked isn't loaded yet.
    const html = (typeof window.marked !== 'undefined' && window.marked.parse)
      ? window.marked.parse(entry.text || '', { breaks: true, gfm: true })
      : renderInline(entry.text || '');
    return (
      <div style={{ padding: '8px 0 12px', marginBottom: 4 }}>
        <span className="ok" style={{ fontWeight: 600, marginRight: 8,
          fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Agent</span>
        <div className="md-agent" style={{ fontSize: 14, lineHeight: 1.65,
          marginTop: 4 }} dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    );
  }
  if (entry.kind === 'thought') {
    return <CollapsibleThought text={entry.text || ''} />;
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
    const txt = entry.text || '';
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
            background: 'var(--bg-input, #1c2128)', padding: '6px 10px',
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

const renderInline = (s) => s.replace(/`([^`]+)`/g, '<code class="acc" style="background:var(--bg-2);padding:1px 4px;border-radius:2px;">$1</code>')
                            .replace(/\*\*([^*]+)\*\*/g, '<b style="color:var(--fg);">$1</b>');

// ── ask_user — compact in-feed tool-call line ─────────────────────
// Renders as `action: ask_user(...)` matching the other tool calls,
// then (when submitted) appends an `obs:` line with the user's reply.
const AskUserCall = ({ flowId, state, dir }) => {
  const flow = window.QA_FLOWS[flowId];
  if (!flow || !state) return null;
  const sel = state.opts.filter(o => o.selected);
  const submitted = state.submitted;
  const argSummary = `flow="${flowId}", question="${flow.question.length > 48 ? flow.question.slice(0, 48) + '…' : flow.question}", kind=${flow.kind}, options=${flow.options.length}`;
  const replySummary = sel.map(o => o.label).join(', ') + (state.custom ? `, +"${state.custom}"` : '');

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

// ── ask_user — inline bottom prompt (replaces the regular input row) ──
// Mirrors the screenshot: numbered options, inline `[ ]`/`[✓]`, single
// custom-text line, Submit + "Chat about this" affordances, hint footer.
const AskUserPrompt = ({ flowId, state, sel, intent, onToggle, onCustom, onSubmit, onChat, onSel }) => {
  const flow = window.QA_FLOWS[flowId];
  if (!flow || !state) return null;
  const opts = state.opts;
  const customIdx = opts.length;       // row index for custom-text line
  const submitIdx = opts.length + 1;   // Submit menu line
  const chatIdx   = opts.length + 2;   // "Chat about this" menu line
  const lastIdx   = chatIdx;

  const onKey = (e) => {
    if (e.key === 'ArrowDown' || (e.key === 'j' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.min(sel + 1, lastIdx)); return;
    }
    if (e.key === 'ArrowUp' || (e.key === 'k' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.max(sel - 1, 0)); return;
    }
    if (e.key === ' ' && sel < opts.length) {
      e.preventDefault(); onToggle(flowId, opts[sel].id); return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      if (sel < opts.length) { onToggle(flowId, opts[sel].id); return; }
      if (sel === customIdx) { /* focus the input */ const el = e.currentTarget.querySelector('input.askcustom'); el?.focus(); return; }
      if (sel === submitIdx) { onSubmit(flowId); return; }
      if (sel === chatIdx)   { onChat(flowId); return; }
    }
    if (e.key === 'Escape') { e.preventDefault(); onSel(0); }
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
          {flow.kind === 'multi' ? 'multi-select' : 'single-select'}
        </span>
      </div>

      {/* question */}
      <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 10, color: 'var(--fg)' }}>
        {flow.question}
      </div>

      {/* multi-mode bulk select / clear */}
      {flow.kind === 'multi' && opts.length > 1 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 11 }}>
          <span
            onClick={() => {
              opts.forEach(o => { if (!o.selected && !o.locked) onToggle(flowId, o.id); });
            }}
            style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--accent)', color: 'var(--accent)', borderRadius: 2 }}
            title="Select every option">
            ☑ Select all
          </span>
          <span
            onClick={() => {
              opts.forEach(o => { if (o.selected && !o.locked) onToggle(flowId, o.id); });
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
        {opts.map((o, i) => {
          const isSel = o.selected;
          const focused = sel === i;
          return (
            <div
              key={o.id}
              onClick={() => { onSel(i); onToggle(flowId, o.id); }}
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
              <span className="mute" style={{ textAlign: 'right' }}>{i + 1}.</span>
              <span style={{ color: isSel ? 'var(--accent)' : 'var(--fg-mute)', fontWeight: 700 }}>
                {flow.kind === 'multi' ? (isSel ? '[✓]' : '[ ]') : (isSel ? '(•)' : '( )')}
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
          onClick={() => onSel(customIdx)}
          style={{
            display: 'grid',
            gridTemplateColumns: '24px 28px 1fr',
            alignItems: 'baseline',
            gap: 6,
            padding: '4px 8px',
            background: sel === customIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === customIdx ? 'var(--accent)' : 'transparent'}`,
            cursor: 'text',
            fontFamily: 'var(--mono)',
            fontSize: 13,
          }}
        >
          <span className="mute" style={{ textAlign: 'right' }}>{opts.length + 1}.</span>
          <span style={{ color: state.custom ? 'var(--warn)' : 'var(--fg-mute)', fontWeight: 700 }}>
            {state.custom ? '[✓]' : '[ ]'}
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <input
              className="askcustom"
              value={state.custom}
              onChange={(e) => onCustom(flowId, e.target.value)}
              onFocus={() => onSel(customIdx)}
              placeholder="custom answer / free-form note…"
              style={{
                background: 'transparent', border: 'none', outline: 'none',
                fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 13, flex: 1, padding: 0,
              }}
            />
            {sel === customIdx && <span className="cursor-thin" />}
          </div>
        </div>
      </div>

      {/* submit row */}
      <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 0 }}>
        <div
          onClick={() => onSubmit(flowId)}
          style={{
            padding: '4px 8px',
            background: sel === submitIdx ? 'color-mix(in oklch, var(--ok) 18%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === submitIdx ? 'var(--ok)' : 'transparent'}`,
            cursor: 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
            color: sel === submitIdx ? 'var(--ok)' : 'var(--fg)',
            fontWeight: sel === submitIdx ? 600 : 400,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>Submit
          <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>
            ({sel.length || 0}{state.custom ? '+1' : ''} reply)
          </span>
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
        <span><Kbd>↵</Kbd> select</span>
        <span><Kbd>↑↓</Kbd>/<Kbd>j k</Kbd> navigate</span>
        <span><Kbd>Space</Kbd> toggle</span>
        <span><Kbd>Tab</Kbd> next field</span>
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

const TodoPanel = () => {
  const [view, setView] = React.useState('compact'); // compact | detail | graph
  const [openId, setOpenId] = React.useState(null);
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
      case 'done':        return { glyph: '☑', color: '#3fb950', label: 'done' };
      case 'approved':    return { glyph: '☑', color: '#3fb950', label: 'approved' };
      case 'completed':   return { glyph: '✓', color: '#3fb950', label: 'completed' };
      case 'active':      return { glyph: '◉', color: '#58a6ff', label: 'in-progress' };
      case 'in_progress': return { glyph: '◉', color: '#58a6ff', label: 'in-progress' };
      case 'rejected':    return { glyph: '✕', color: '#f85149', label: 'rejected' };
      case 'pending':     return { glyph: '☐', color: '#d29922', label: 'pending' };
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

      <div style={{ flex: 1, overflow: 'auto' }}>
        {view === 'compact' && (
          <div style={{ padding: '6px 0' }}>
            {todos.map(t => {
              const cfg = stateCfg(t.state);
              const open = openId === t.id;
              return (
                <div key={t.id}>
                  <div
                    onClick={() => setOpenId(open ? null : t.id)}
                    style={{
                      display: 'grid', gridTemplateColumns: '24px 36px 1fr 16px',
                      alignItems: 'baseline', gap: 6, padding: '4px 12px',
                      cursor: 'pointer', fontFamily: 'var(--mono)', fontSize: 12,
                      background: t.state === 'active' ? 'color-mix(in oklch, var(--accent) 8%, transparent)' : 'transparent',
                      borderLeft: t.state === 'active' ? '2px solid var(--accent)' : '2px solid transparent',
                    }}
                  >
                    <span style={{ color: cfg.color, fontSize: 13 }}>{cfg.glyph}</span>
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
        )}

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
            background: 'var(--bg-input)', border: '1px solid var(--line)',
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

  React.useEffect(() => {
    if (!path) { setBody(''); setErr(null); return; }
    let cancelled = false;
    setLoading(true); setErr(null);
    window.atlasData.fetchFile(path).then(d => {
      if (cancelled) return;
      setLoading(false);
      if (d.error) {
        setErr(d.error); setBody(`// ${path}\n// (could not read: ${d.error})`); return;
      }
      setBody(d.content || '');
      setSize(d.size || 0);
      setTruncated(!!d.truncated);
    }).catch(e => {
      if (!cancelled) { setLoading(false); setErr(String(e)); setBody(`// fetch failed: ${e}`); }
    });
    return () => { cancelled = true; };
  }, [path]);

  // Re-highlight whenever body/lang changes. Prism replaces the
  // <code> contents in place; we set the language class first.
  React.useEffect(() => {
    if (!codeRef.current || !window.Prism) return;
    if (lang === 'none') return;       // skip for plain text
    codeRef.current.className = 'language-' + lang;
    try { window.Prism.highlightElement(codeRef.current); } catch (_) { /* ignore */ }
  }, [body, lang]);

  if (!path) {
    return (
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexDirection: 'column', gap: 12, color: 'var(--fg-mute)', padding: 40,
      }}>
        <div style={{ fontSize: 32, opacity: 0.4 }}>◆</div>
        <div style={{ fontSize: 13 }}>No file selected.</div>
        <div style={{ fontSize: 11 }}>Double-click any file in the tree on the left to preview it here.</div>
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
        <span>lang <span style={{ color: 'var(--accent)' }}>{lang === 'none' ? 'plain' : lang}</span></span>
        <span className="mute">·</span>
        <span>{lineCount} lines</span>
        {sizeKb && <><span className="mute">·</span><span>{sizeKb}</span></>}
        {truncated && <><span className="mute">·</span><span className="warn">truncated at {Math.round((body.length || 0) / 1024)}KB</span></>}
        <span style={{ flex: 1 }} />
        <span onClick={copyAll}  style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>copy</span>
        <span onClick={copyPath} style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>copy path</span>
      </div>
      {/* code body */}
      <div style={{ flex: 1, overflow: 'auto', background: '#1c2128' }}>
        {loading ? (
          <div style={{ padding: 16, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12 }}>
            loading {path}…
          </div>
        ) : (
          <pre style={{
            margin: 0, padding: '12px 16px',
            fontFamily: 'var(--mono)', fontSize: 12, lineHeight: 1.55,
            whiteSpace: 'pre', tabSize: 4,
            background: 'transparent',
          }}>
            <code ref={codeRef} className={lang === 'none' ? '' : ('language-' + lang)}>
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

// ── UPD Agent status panel ─────────────────────────────────────────
const AgentStatusPanel = ({ intent, workflow, onCollapse }) => {
  // Live context — populated by /healthz + WS 'context' events.
  const _ctx = window.CONTEXT || {};
  const ctxUsed = (_ctx.tokens || 0) / 1000;             // → K tokens
  const ctxMax  = Math.max(1, (_ctx.maxTokens || 1000000) / 1000);  // → K
  const pct = Math.min(100, Math.round((ctxUsed / ctxMax) * 100));
  return (
    <div className="box" style={{ flexShrink: 0 }}>
      <div className="box-h" style={{ padding: '6px 12px' }}>
        <span style={{ color: 'var(--accent)', fontWeight: 700 }}>UPD Agent</span>
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
          {[
            { id: 'ssot', label: 'SSOT', state: 'done' },
            { id: 'rtl',  label: 'RTL',  state: 'done' },
            { id: 'lint', label: 'LINT', state: 'active' },
            { id: 'tb',   label: 'TB',   state: 'pending' },
          ].map(s => {
            const cfg = s.state === 'done'    ? { color: 'var(--ok)',     glyph: '✓', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)',     border: 'var(--ok)' }
                      : s.state === 'active'  ? { color: 'var(--accent)', glyph: '●', bg: 'color-mix(in oklch, var(--accent) 14%, transparent)', border: 'var(--accent)' }
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

        {/* ── pipeline · TALOS (backend, TBD) ──────────────────────── */}
        <div className="mute" style={{
          fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase',
          marginBottom: 6,
          display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap',
        }}>
          <span style={{ color: 'var(--mag, #b58aff)', fontWeight: 700 }}>▸ talos</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>· backend</span>
          <span style={{ flex: 1 }} />
          <span className="mute" style={{ fontSize: 9 }}>⊘ tbd</span>
        </div>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4,
          fontSize: 10, marginBottom: 6, opacity: 0.55,
        }}>
          {[
            { id: 'dft', label: 'DFT' },
            { id: 'syn', label: 'SYN' },
            { id: 'sta', label: 'STA' },
            { id: 'pnr', label: 'P&R' },
          ].map(s => (
            <div key={s.id} style={{
              border: '1px dashed var(--line)', borderRadius: 2,
              padding: '4px 6px', textAlign: 'center',
              fontFamily: 'var(--mono)',
              color: 'var(--fg-mute)',
            }}>
              <div style={{ fontWeight: 600, fontSize: 10 }}>
                ⋯ {s.label}
              </div>
            </div>
          ))}
        </div>
        <div className="mute" style={{
          fontSize: 10, fontFamily: 'var(--mono)', lineHeight: 1.5,
          padding: '4px 6px', borderLeft: '2px solid var(--line)',
          background: 'color-mix(in oklch, var(--mag, #b58aff) 6%, transparent)',
        }}>
          <span style={{ color: 'var(--mag, #b58aff)' }}>talos.handshake</span> ›
          heartbeat ok · queue empty<br />
          <span className="mute">awaiting atlas → talos handoff (not yet wired)</span>
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