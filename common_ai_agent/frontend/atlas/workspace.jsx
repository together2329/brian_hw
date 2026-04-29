// workspace.jsx — Chat-centric: ReAct + inline Q&A cards + SSOT/Todo sidebar + file viewer

const Workspace = ({ dir, onScreen }) => {
  // Two-axis mode model:
  //   intent: 'normal' | 'plan'   (top-level — shift+tab to swap)
  //   workflow: null | 'ssot' | 'rtl_gen' | 'lint' | 'tb_gen'
  const [intent, setIntent] = React.useState('normal');
  const [workflow, setWorkflow] = React.useState(null);

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
  const [rightTab, setRightTab] = React.useState('ssot'); // ssot | todo | files
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

  // ── @ file completion ────────────────────────────────────────
  // Find a trailing "@<query>" token (anywhere in the input). The
  // query is everything after the LAST `@` to the end of the line.
  const atQuery = React.useMemo(() => {
    const m = input.match(/(^|\s)@([^\s]*)$/);
    return m ? { token: '@' + m[2], q: m[2].toLowerCase(), pos: m.index + m[1].length } : null;
  }, [input]);

  const fileMatches = React.useMemo(() => {
    if (!atQuery) return [];
    const tree = window.FILE_TREE || [];
    if (!atQuery.q) return tree.slice(0, 20);
    return tree
      .filter(e => e.name.toLowerCase().includes(atQuery.q))
      .slice(0, 20);
  }, [atQuery && atQuery.q]);

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
    if (atQuery && fileMatches.length > 0) { setShowAt(true); setAtSel(0); }
    else setShowAt(false);
  }, [input, atQuery, fileMatches.length]);

  const acceptAtCompletion = (entry) => {
    if (!atQuery) return;
    const before = input.slice(0, atQuery.pos);
    const after  = input.slice(atQuery.pos + atQuery.token.length);
    const fullPath = (window.SCOPE_PATH ? window.SCOPE_PATH + '/' : '') + entry.name;
    setInput(before + fullPath + ' ' + after);
    setShowAt(false);
  };

  React.useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [feed, streamText]);

  // shift+tab swaps Normal ↔ Plan
  React.useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Tab' && e.shiftKey && document.activeElement?.tagName !== 'INPUT') {
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
      if (!arg) {
        setFeed(f => [...f, { kind: 'user', text: raw }]);
        setFeed(f => [...f, {
          kind: 'agent',
          text: cur
            ? `Current scope: \`${cur}\`\nUse \`/scope <path>\` to change, \`/scope /\` to reset.`
            : 'No scope set — agent works on the whole project.\nUse `/scope <path>` to confine it.',
        }]);
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
    <div style={{ display: 'grid', gridTemplateColumns: '230px 1fr 360px', gap: 16, padding: 16, height: '100%', overflow: 'hidden' }}>
      {/* LEFT — Mode/Workflow + Files */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden' }}>
        <div className="box">
          <div className="box-h">
            <span>▸ mode</span>
            <span style={{ flex: 1 }} />
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
            <span>▸ ip files</span>
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
            <span
              title="refresh tree"
              style={{ cursor: 'pointer', color: 'var(--fg-mute)', fontSize: 12, padding: '0 4px' }}
              onClick={() => window.atlasData.refreshFileTree(window.SCOPE_PATH || '')}
            >↻</span>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
            {window.FILE_TREE.length === 0 && (
              <div className="mute" style={{ padding: '8px 10px', fontSize: 11 }}>
                (empty — try a different scope or refresh)
              </div>
            )}
            {window.FILE_TREE.map((n, i) => {
              const fullPath = (window.SCOPE_PATH ? window.SCOPE_PATH + '/' : '') + n.name;
              return (
                <div key={i}
                  className={n.active ? 'frow active' : 'frow'}
                  style={{ paddingLeft: 8 + (n.depth || 0) * 14, cursor: 'pointer' }}
                  onClick={() => {
                    if (n.type === 'file') setOpenFile(fullPath);
                    else window.atlasData.setScopePath(fullPath);
                  }}
                  title={fullPath}
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
            <span>▸ chat</span>
            <span className="mute" style={{ margin: '0 6px' }}>·</span>
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
            <span style={{ flex: 1 }} />
            <span className="mute" style={{ fontSize: 10, textTransform: 'none', letterSpacing: 0 }}>
              iter 14 · 47.2k tok · {streaming ? <span className="acc">streaming<span className="ascii-spin"></span></span> : <span className="ok">idle</span>}
            </span>
          </div>
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
            {streaming && streamText && (
              <div className="react-block thought fade-in">
                <span className="rb-tag">…</span>
                <span>{streamText}<span className="cursor-thin" /></span>
              </div>
            )}
          </div>
        </div>

        {/* prompt */}
        <div style={{ position: 'relative' }}>
          {showAt && fileMatches.length > 0 && (
            <div className="slash-menu fade-in" style={{ maxHeight: 280, overflowY: 'auto' }}>
              <div style={{ padding: '6px 12px', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>{fileMatches.length} file{fileMatches.length === 1 ? '' : 's'}</span>
                <span style={{ flex: 1 }} />
                <span><Kbd>↑↓</Kbd> nav · <Kbd>↵</Kbd> insert · <Kbd>Esc</Kbd> close</span>
              </div>
              {fileMatches.map((f, i) => (
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
                  <span className="mute" style={{ fontSize: 10 }}>{f.size || ''}</span>
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
              <span className="ps" title={streaming ? 'Agent is working' : 'Awaiting your input'}
                    style={{ color: streaming ? 'var(--warn)' : 'var(--ok)' }}>
                {streaming ? '⚙' : '›'}
              </span>
              <input ref={inputRef} value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder={streaming
                  ? 'Agent is working — Esc to stop, or type to interrupt with new input'
                  : 'Awaiting your input — type a message, "/" for commands, "@" for files'}
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

      {/* RIGHT — UPD Agent status + SSOT/Todo/Diff */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden' }}>
        <AgentStatusPanel intent={intent} workflow={workflow} />
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="box-h" style={{ padding: 0 }}>
            <RightTab id="ssot" cur={rightTab} onTab={setRightTab}>SSOT.yaml</RightTab>
            <RightTab id="todo" cur={rightTab} onTab={setRightTab}>Todo · 4/9</RightTab>
            <RightTab id="diff" cur={rightTab} onTab={setRightTab}>Diff</RightTab>
          </div>
          {rightTab === 'ssot' && <SsotPanel />}
          {rightTab === 'todo' && <TodoPanel />}
          {rightTab === 'diff' && <DiffPanel />}
        </div>
      </div>

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
    return (
      <div className="react-block obs">
        <span className="rb-tag">obs{entry.tool ? ` · ${entry.tool}` : ''}</span>
        {isMulti ? (
          <pre style={{
            margin: '4px 0 0', maxHeight: 240, overflow: 'auto',
            background: 'var(--bg-input, #1c2128)', padding: '6px 10px',
            borderRadius: 4, fontSize: 11, lineHeight: 1.4,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word'
          }}>{txt}{entry.truncated ? '\n…[truncated]' : ''}</pre>
        ) : (
          <span>{txt}{entry.truncated ? ' …[truncated]' : ''}</span>
        )}
      </div>
    );
  }
  if (entry.kind === 'qcard') {
    return <AskUserCall flowId={entry.flowId} state={qaState[entry.flowId]} dir={dir} />;
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
  const done = todos.filter(t => t.state === 'done').length;

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

// ── File viewer modal ─────────────────────────────────────────────
const FILE_BODIES = {
  'spi_master_requirements.md': `# spi_master · Requirements\n\n## §1 Overview\nSPI master controller, single-master, up to 4 chip-selects.\nHost interface: APB. Frequency target: ≤ 50 MHz sclk.\n\n## §2 Use cases\n  - Sensor polling (LIS3DH, BMP280)\n  - Flash configuration (W25Q series)\n  - Low-latency control bursts\n\n## §3 Functional requirements\n  R-01  Support CPOL/CPHA modes 0..3\n  R-02  Programmable BAUD_DIV (1..255)\n  R-03  TX/RX FIFO depth 8\n  R-04  Interrupt on TX_EMPTY, RX_FULL, DONE\n  R-05  4 independent CS lines, software-selected\n  R-06  Async reset, single posedge clock domain (pclk)`,
  'spi_master_mas.md': `# spi_master · Micro Architecture Spec\n\n## §1 Block diagram\n        ┌──────────┐    ┌──────────┐    ┌────────┐\n  APB → │ reg_file │ →  │ ctrl_fsm │ →  │ shifter│ → SPI\n        └──────────┘    └──────────┘    └────────┘\n\n## §2 Register map\nADDR  NAME      ACCESS  DESCRIPTION\n0x00  CTRL      RW      enable, cpol, cpha, cs_sel\n0x04  STAT      R       tx_empty, rx_full, done\n0x08  DATA_TX   W       tx fifo push\n0x0C  DATA_RX   R       rx fifo pop\n0x10  BAUD_DIV  RW      sclk = pclk / (BAUD_DIV+1)\n0x14  IRQ_EN    RW      mask\n\n## §5 FSM\n  IDLE → LOAD → SHIFT → COMPLETE → IDLE\n\n## §9 DV plan\n  12 scenarios · 4 coverage groups · target 95%`,
  'spi_master.sv': `// spi_master.sv — generated by rtl_gen v3\nmodule spi_master #(\n    parameter int CS_W = 4,\n    parameter int FIFO_D = 8\n) (\n    input  logic        pclk,\n    input  logic        resetn,\n    // APB\n    input  logic [7:0]  paddr,\n    input  logic        psel, penable, pwrite,\n    input  logic [31:0] pwdata,\n    output logic [31:0] prdata,\n    output logic        pready,\n    // SPI\n    output logic        sclk, mosi,\n    input  logic        miso,\n    output logic [CS_W-1:0] ss_n,\n    // IRQ\n    output logic        irq\n);\n  // ── FSM: spi_master transfer cycle ──\n  typedef enum logic [1:0] {\n    IDLE, LOAD, SHIFT, COMPLETE\n  } state_t;\n\n  state_t cur, nxt;\n  logic [3:0] bit_cnt;\n\n  always_ff @(posedge pclk or negedge resetn) begin\n    if (!resetn) begin\n      cur     <= IDLE;\n      bit_cnt <= '0;\n    end\n    else cur <= nxt;\n  end\n\n  // ... 380 more lines ...\nendmodule`,
  'tb_spi_master.sv': `// tb_spi_master.sv — generated by tb_gen\n\`timescale 1ns/1ps\nmodule tb_spi_master;\n  logic pclk = 0; always #5 pclk = ~pclk;\n  logic resetn;\n  spi_master u_dut (.*);\n  initial begin\n    resetn = 0; #20 resetn = 1;\n    run_test();\n    $finish;\n  end\nendmodule`,
  'tc_spi_master.sv': `// tc_spi_master.sv — 12 test cases\nclass tc_cpol0_cpha0 extends tc_base;\n  task body(); /* mode 0 transfer */ endtask\nendclass\nclass tc_b2b_transfer extends tc_base;\n  task body(); /* back-to-back */ endtask\nendclass\n// + 10 more`,
  'lint_report.txt': `verilator 5.024 · spi_master.sv\n──────────────────────────────────────────\n%Warning-WIDTHEXPAND:    spi_master.sv:87   Operator ASSIGN expects 8 bits on RHS, got 4\n%Warning-UNUSED:         spi_master.sv:124  Signal is not used: 'cpha_sync_d2'\n%Warning-CASEINCOMPLETE: spi_master.sv:198  Case values not handled: COMPLETE\n──────────────────────────────────────────\n3 warnings · 0 errors · 412 lines scanned`,
};

const FileViewer = ({ name, onClose }) => {
  const body = FILE_BODIES[name] || `// ${name}\n// (no preview content available)`;
  const ext = name.split('.').pop();
  React.useEffect(() => {
    const onEsc = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onEsc);
    return () => window.removeEventListener('keydown', onEsc);
  }, [onClose]);

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
          <span className="mute" style={{ marginLeft: 10, textTransform: 'none', letterSpacing: 0, fontSize: 11 }}>· {ext} · read-only</span>
          <span style={{ flex: 1 }} />
          <button className="btn" onClick={onClose} style={{ fontSize: 11 }}>Close <Kbd>Esc</Kbd></button>
        </div>
        <pre className="code" style={{
          flex: 1, overflow: 'auto', padding: 16, margin: 0, fontSize: 12, lineHeight: 1.55,
          whiteSpace: 'pre', color: 'var(--fg)',
        }}>{body}</pre>
        <div style={{ borderTop: '1px solid var(--line)', padding: '8px 14px', display: 'flex', gap: 8, fontSize: 11 }}>
          <span className="mute">{body.split('\n').length} lines</span>
          <span style={{ flex: 1 }} />
          <button className="btn">Open in editor</button>
          <button className="btn">Copy path</button>
        </div>
      </div>
    </div>
  );
};

// ── UPD Agent status panel ─────────────────────────────────────────
const AgentStatusPanel = ({ intent, workflow }) => {
  const ctxUsed = 286.4;  // K tokens
  const ctxMax = 1000;    // K tokens
  const pct = Math.round((ctxUsed / ctxMax) * 100);
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
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 8 }}>
          <span className="mute">Model</span>
          <span style={{ color: 'var(--fg)' }}>{(window.CONTEXT && window.CONTEXT.model) || '—'}</span>
        </div>
        {/* Context with bar */}
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4 }}>
          <span className="mute">Context</span>
          <span>
            <span style={{ color: 'var(--fg)' }}>{ctxUsed.toFixed(1)}K</span>
            <span className="mute"> / {ctxMax}K · </span>
            <span className={pct > 70 ? 'warn' : 'ok'}>{pct}%</span>
          </span>
        </div>
        <div style={{ marginLeft: 72, marginBottom: 10, height: 4, background: 'var(--bg-2)', borderRadius: 1, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${pct}%`,
            background: pct > 70 ? 'var(--warn)' : 'var(--accent)',
          }} />
        </div>
        {/* Cost ledger */}
        <div className="mute" style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>Cost</div>
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr 56px', gap: 4, fontSize: 11, lineHeight: 1.55 }}>
          <span className="mute">Input</span>
          <span style={{ color: 'var(--fg)', textAlign: 'right' }}>132.9K</span>
          <span style={{ color: 'var(--fg)', textAlign: 'right' }}>$0.0578</span>

          <span className="mute">Cached</span>
          <span style={{ color: 'var(--fg)', textAlign: 'right' }}>7.4M</span>
          <span style={{ color: 'var(--fg)', textAlign: 'right' }}>$0.2187</span>

          <span className="mute">Output</span>
          <span style={{ color: 'var(--fg)', textAlign: 'right' }}>80.3K</span>
          <span style={{ color: 'var(--fg)', textAlign: 'right' }}>$0.0699</span>

          <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--fg)', fontWeight: 600 }}>Total</span>
          <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--fg)', textAlign: 'right' }}>7.6M</span>
          <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--ok)', textAlign: 'right', fontWeight: 600 }}>$0.3965</span>
        </div>

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