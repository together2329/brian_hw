// workspace.jsx — Chat-centric: ReAct + inline Q&A cards + SSOT/Todo sidebar + file viewer

const Workspace = ({ dir, onScreen }) => {
  // Two-axis mode model:
  //   intent: 'normal' | 'plan'   (top-level — shift+tab to swap)
  //   workflow: null | 'ssot' | 'rtl_gen' | 'lint' | 'tb_gen'
  const [intent, setIntent] = React.useState('normal');
  const [workflow, setWorkflow] = React.useState(null);

  const NORMAL_FEED = [
    { kind: 'agent', text: 'Normal mode · ask anything about `spi_master` — explain code, propose improvements, debug issues, or just chat. Pick a **Workflow** below to enter a guided generation flow.' },
    { kind: 'agent', text: 'Suggested follow-ups:\n  · `Review §5 FSM for hazards`\n  · `Compare CPOL/CPHA timing across all 4 modes`\n  · `What changed since v2 of the SSOT?`\n  · `Find dead code in spi_master.sv`' },
  ];
  const PLAN_FEED = [
    { kind: 'agent', text: '**Plan mode** · read-only. I will analyze, propose, and write a plan — but **will not execute** any tools that mutate files. Use `apply` (or switch back to Normal) to run the plan.' },
    { kind: 'agent', text: 'Try: `Plan a refactor of §5 FSM to add LOAD state`, or pick a Workflow to plan its outputs without writing them.' },
  ];
  const buildWorkflowFeed = (wfId, intent) => {
    const stage = window.FLOW_STAGES.find(s => s.id === wfId);
    const planPrefix = intent === 'plan' ? '[plan] ' : '';
    return [
      { kind: 'agent', text: `Workflow · \`${stage.cmd} spi_master\` ${intent === 'plan' ? '· **PLAN mode** (no writes)' : ''}` },
      { kind: 'thought', text: `${planPrefix}Loading prior stage outputs and slash-command catalog…` },
      { kind: 'action', tool: 'read_file', args: { path: 'spi_master/mas/spi_master_mas.md' }, planned: intent === 'plan' },
      { kind: 'obs', text: 'OK · prior stage context loaded.' },
      ...(window.QA_FLOWS[wfId] ? [
        { kind: 'agent', text: 'First decision needs your input — see card below.' },
        { kind: 'qcard', flowId: wfId },
      ] : [
        { kind: 'agent', text: 'No interactive questions — outputs will stream as I work.' },
      ]),
    ];
  };

  const [feed, setFeed] = React.useState(NORMAL_FEED);

  const refreshFeed = (newIntent, newWorkflow) => {
    if (newWorkflow) setFeed(buildWorkflowFeed(newWorkflow, newIntent));
    else setFeed(newIntent === 'plan' ? PLAN_FEED : NORMAL_FEED);
  };

  const switchIntent = (i) => {
    setIntent(i);
    refreshFeed(i, workflow);
  };
  const switchWorkflow = (w) => {
    // Clicking the active workflow toggles it off → free chat in current intent
    const next = workflow === w ? null : w;
    setWorkflow(next);
    refreshFeed(intent, next);
  };
  const [input, setInput] = React.useState('');
  const [showSlash, setShowSlash] = React.useState(false);
  const [slashSel, setSlashSel] = React.useState(0);
  const [streaming, setStreaming] = React.useState(false);
  const [streamText, setStreamText] = React.useState('');
  const [openFile, setOpenFile] = React.useState(null);
  const [rightTab, setRightTab] = React.useState('ssot'); // ssot | todo | files
  const [qaState, setQaState] = React.useState(() => {
    const m = {};
    Object.keys(window.QA_FLOWS).forEach(k => {
      m[k] = {
        opts: window.QA_FLOWS[k].options.map(o => ({ ...o })),
        custom: '',
        submitted: false,
      };
    });
    return m;
  });

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

  const filtered = React.useMemo(() => {
    if (!input.startsWith('/')) return [];
    const q = input.slice(1).toLowerCase();
    return window.SLASH_COMMANDS.filter(c =>
      c.cmd.slice(1).toLowerCase().startsWith(q) || c.alias.startsWith(q)
    );
  }, [input]);

  React.useEffect(() => {
    if (input.startsWith('/')) { setShowSlash(true); setSlashSel(0); }
    else setShowSlash(false);
  }, [input]);

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
    const txt = (cmd ?? input).trim();
    if (!txt) return;
    setInput('');
    setShowSlash(false);
    setFeed(f => [...f, { kind: 'user', text: txt }]);
    if (window.backend && window.backend.mode === 'live') {
      sendToBackend(txt);
    } else {
      streamAgentReply(txt);
    }
  };

  // ── live backend ───────────────────────────────────────────────
  const sendToBackend = (txt) => {
    setStreaming(true);
    setStreamText('');
    window.backend.send({ type: 'prompt', text: txt });
  };

  // Subscribe to backend events and translate them into feed entries.
  const streamBufferRef = React.useRef('');
  React.useEffect(() => {
    if (!window.backend || window.backend.mode !== 'live') return;
    const subs = [];
    subs.push(window.backend.subscribe('token', (m) => {
      const t = m.text || '';
      if (!t || t === '\x00') return;  // skip sentinel
      streamBufferRef.current += t;
      setStreamText(streamBufferRef.current);
    }));
    subs.push(window.backend.subscribe('reasoning', (m) => {
      const t = (m.text || '').trim();
      if (t) setFeed(l => [...l, { kind: 'thought', text: t }]);
    }));
    subs.push(window.backend.subscribe('todo_line', (m) => {
      const t = (m.text || '').trim();
      if (t) setFeed(l => [...l, { kind: 'obs', text: t }]);
    }));
    const finalize = () => {
      const buf = streamBufferRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf }]);
      streamBufferRef.current = '';
      setStreamText('');
      setStreaming(false);
    };
    subs.push(window.backend.subscribe('flush', finalize));
    subs.push(window.backend.subscribe('done', finalize));
    subs.push(window.backend.subscribe('agent_state', (m) => {
      if (m.running === false) finalize();
      else if (m.running === true) setStreaming(true);
    }));
    subs.push(window.backend.subscribe('error', (m) => {
      setFeed(l => [...l, { kind: 'agent', text: `[error] ${m.message || ''}` }]);
      streamBufferRef.current = '';
      setStreamText('');
      setStreaming(false);
    }));
    return () => subs.forEach(u => u && u());
  }, []);

  const streamAgentReply = (cmd) => {
    setStreaming(true);
    const isCmd = cmd.startsWith('/');
    const seq = isCmd
      ? [
          { kind: 'thought', text: `Routing "${cmd}". Loading workspace and tool catalog…` },
          { kind: 'action',  tool: 'read_file', args: { path: 'spi_master/mas/spi_master_mas.md' } },
          { kind: 'obs',     text: 'OK · 312 lines · context loaded' },
          { kind: 'agent',   text: 'Ready. Next decision needs your input — see the question card below.' },
          { kind: 'qcard',   flowId: 'tb_gen' },
        ]
      : [
          { kind: 'thought', text: `Interpreting your reply: "${cmd}". I\'ll fold this into the current SSOT step.` },
          { kind: 'agent',   text: 'Got it — I\'ve added a `# note` to the SSOT preview on the right. Continue with the question card or type another command.' },
        ];
    let i = 0;
    const next = () => {
      if (i >= seq.length) { setStreaming(false); setStreamText(''); return; }
      const r = seq[i];
      if (r.kind === 'thought' || r.kind === 'agent') {
        let pos = 0;
        setStreamText('');
        const tw = setInterval(() => {
          pos += 8;
          setStreamText(r.text.slice(0, pos));
          if (pos >= r.text.length) {
            clearInterval(tw);
            setFeed(l => [...l, r]);
            setStreamText('');
            i++;
            setTimeout(next, 180);
          }
        }, 18);
      } else {
        setFeed(l => [...l, r]);
        i++;
        setTimeout(next, 280);
      }
    };
    next();
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

  const submitCard = (flowId) => {
    const flow = window.QA_FLOWS[flowId];
    const st = qaState[flowId];
    const sel = st.opts.filter(o => o.selected).map(o => o.label);
    setQaState(s => ({ ...s, [flowId]: { ...s[flowId], submitted: true } }));
    // No user-message echo — the qcard becomes an `action: ask_user` line
    // in the feed and an `obs: user replied · …` line is appended automatically
    // (rendered inside <AskUserCall> when state.submitted flips to true).
    // agent advances
    setTimeout(() => {
      const advance = [
        { kind: 'thought', text: `Locked step ${flow.step} of ${flow.stage}: ${sel.length} option(s)${st.custom ? ' + 1 custom' : ''}. Updating SSOT YAML and queuing next question…` },
        { kind: 'action',  tool: 'write_file', args: { path: 'spi_master/ssot/spi_master.ssot.yaml', section: flow.stageDetail } },
        { kind: 'obs',     text: 'OK · ssot.yaml updated · advancing to step ' + (flow.step + 1) },
        { kind: 'agent',   text: `Step ${flow.step + 1}: **${flow.upcoming[0]?.title || 'Confirm'}** — pick an option below.` },
        { kind: 'qcard',   flowId: flow.step >= 3 ? 'rtl_gen' : flowId, locked: true },
      ];
      streamSeq(advance);
    }, 400);
  };

  const streamSeq = (seq) => {
    setStreaming(true);
    let i = 0;
    const next = () => {
      if (i >= seq.length) { setStreaming(false); setStreamText(''); return; }
      const r = seq[i];
      if (r.kind === 'thought' || r.kind === 'agent') {
        let pos = 0;
        setStreamText('');
        const tw = setInterval(() => {
          pos += 8;
          setStreamText(r.text.slice(0, pos));
          if (pos >= r.text.length) {
            clearInterval(tw);
            setFeed(l => [...l, r]);
            setStreamText('');
            i++;
            setTimeout(next, 160);
          }
        }, 16);
      } else {
        setFeed(l => [...l, r]);
        i++;
        setTimeout(next, 240);
      }
    };
    next();
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
            <span className="acc" style={{ textTransform: 'none', fontSize: 11, letterSpacing: 0 }}>spi_master</span>
          </div>
          {/* cwd path bar */}
          <div style={{
            padding: '6px 10px', borderBottom: '1px solid var(--line)',
            display: 'flex', alignItems: 'center', gap: 6, fontSize: 11,
            background: 'var(--bg-2)',
          }}>
            <span className="mute" style={{ fontSize: 10 }}>cwd</span>
            <span className="mute">›</span>
            <span style={{
              flex: 1, fontFamily: 'var(--mono)',
              color: 'var(--fg)', fontSize: 11,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              direction: 'rtl', textAlign: 'left',
            }} title="/Users/sk/work/ip_dev/spi_master">
              ~/work/ip_dev/spi_master
            </span>
            <span
              title="refresh tree"
              style={{ cursor: 'pointer', color: 'var(--fg-mute)', fontSize: 12, padding: '0 4px' }}
              onMouseEnter={(e) => e.currentTarget.style.color = 'var(--accent)'}
              onMouseLeave={(e) => e.currentTarget.style.color = 'var(--fg-mute)'}
            >↻</span>
            <span
              title="reveal in finder"
              style={{ cursor: 'pointer', color: 'var(--fg-mute)', fontSize: 12, padding: '0 4px' }}
              onMouseEnter={(e) => e.currentTarget.style.color = 'var(--accent)'}
              onMouseLeave={(e) => e.currentTarget.style.color = 'var(--fg-mute)'}
            >⤢</span>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
            {window.FILE_TREE.map((n, i) => (
              <div key={i}
                className={n.active ? 'frow active' : 'frow'}
                style={{ paddingLeft: 8 + n.depth * 14, opacity: n.dim ? 0.55 : 1, cursor: n.type === 'file' ? 'pointer' : 'default' }}
                onClick={() => n.type === 'file' && setOpenFile(n.name)}
              >
                <span className="fr-icon">{n.type === 'dir' ? (n.expanded ? '▾' : '▸') : '◆'}</span>
                <span className="trunc">{n.type === 'dir' ? <span className="dim">{n.name}</span> : n.name}</span>
                <span className="mute" style={{ fontSize: 10 }}>{n.size}</span>
              </div>
            ))}
          </div>
          {/* file tree footer w/ stats */}
          <div style={{ borderTop: '1px solid var(--line)', padding: '6px 10px', fontSize: 10, color: 'var(--fg-mute)', display: 'flex', gap: 10 }}>
            <span>7 files</span>
            <span>·</span>
            <span>40.4 KB</span>
            <span style={{ flex: 1 }} />
            <span className="ok">git: clean</span>
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
              <span className="ps">›</span>
              <input ref={inputRef} value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder='Reply to the agent, type "/" for commands, "@" for files…'
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
          {rightTab === 'ssot' && <SsotPanel qaState={qaState} />}
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
    return (
      <div style={{ padding: '8px 0 12px', marginBottom: 4 }}>
        <span className="ok" style={{ fontWeight: 600, marginRight: 8, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Agent</span>
        <span style={{ fontSize: 13, lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: renderInline(entry.text) }} />
      </div>
    );
  }
  if (entry.kind === 'thought') {
    return (
      <div className="react-block thought">
        <span className="rb-tag">thought</span>
        <span>{entry.text}</span>
      </div>
    );
  }
  if (entry.kind === 'action') {
    const planned = entry.planned;
    return (
      <div className="react-block action" style={planned ? { opacity: 0.6, borderLeftColor: 'var(--warn)' } : {}}>
        <span className="rb-tag" style={planned ? { color: 'var(--warn)' } : {}}>{planned ? 'plan·action' : 'action'}</span>
        <span>{planned && <span className="warn" style={{ marginRight: 6, fontStyle: 'italic' }}>[would]</span>}<b className="cyan">{entry.tool}</b>(<span className="mute">{Object.entries(entry.args).filter(([k]) => k !== 'planned').map(([k, v]) => (
          <span key={k}>{k}=<span style={{ color: 'var(--fg)' }}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span> </span>
        ))}</span>)</span>
      </div>
    );
  }
  if (entry.kind === 'obs') {
    return (
      <div className="react-block obs">
        <span className="rb-tag">obs</span>
        <span>{entry.text}</span>
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
const SsotPanel = ({ qaState }) => {
  const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  const ssotSel = qaState.ssot?.opts.filter(o => o.selected) || [];
  const ssotCustom = qaState.ssot?.custom;
  const rtlSel = qaState.rtl_gen?.opts.filter(o => o.selected)[0];
  const tbSel = qaState.tb_gen?.opts.filter(o => o.selected) || [];
  const tbCustom = qaState.tb_gen?.custom;

  return (
    <div className="code" style={{ flex: 1, overflow: 'auto', padding: '12px 14px', fontSize: 12, lineHeight: 1.55 }}>
      <div className="mute"># spi_master.ssot.yaml</div>
      <div className="mute">{'# generated by /new-ssot, locked-as-you-go'}</div>
      <div style={{ height: 8 }} />
      <div><span className="mag">ip:</span> <span style={{ color: 'var(--fg)' }}>spi_master</span></div>
      <div><span className="mag">version:</span> <span style={{ color: 'var(--fg)' }}>3</span></div>
      <div style={{ height: 8 }} />
      <div className="acc">overview:</div>
      <div>  <span className="mag">role:</span> spi_master_controller</div>
      <div>  <span className="mag">topology:</span> single_master</div>
      <div>  <span className="mag">cs_count:</span> 4</div>
      <div style={{ height: 8 }} />
      <div className="acc">use_case:</div>
      <div><span className="ok">  - </span>sensor_polling</div>
      <div><span className="ok">  - </span>flash_config</div>
      <div><span className="ok">  - </span>low_latency_burst</div>
      <div style={{ height: 8 }} />
      <div className="acc">interfaces:</div>
      {ssotSel.length === 0 && <div className="mute">  []  # awaiting step 3</div>}
      {ssotSel.map(o => (
        <div key={o.id}>
          <span className="ok">  - </span>
          <span style={{ color: 'var(--fg)' }}>{slug(o.label)}</span>
          <span className="mute">  # {o.detail.split('·')[0].trim()}</span>
        </div>
      ))}
      {ssotCustom && (
        <div>
          <span className="warn">  - </span>
          <span style={{ color: 'var(--fg)' }}>{slug(ssotCustom)}</span>
          <span className="warn">  # custom</span>
        </div>
      )}
      <div style={{ height: 8 }} />
      <div className="acc">rtl:</div>
      {rtlSel ? (
        <div>  <span className="mag">style:</span> <span style={{ color: 'var(--fg)' }}>{slug(rtlSel.label)}</span></div>
      ) : (
        <div className="mute">  style: ~  # pending</div>
      )}
      <div style={{ height: 8 }} />
      <div className="acc">testbench:</div>
      <div>  <span className="mag">scenarios:</span></div>
      {tbSel.length === 0 && <div className="mute">    []  # pending</div>}
      {tbSel.map(o => (
        <div key={o.id}>
          <span className="ok">    - </span>
          <span style={{ color: 'var(--fg)' }}>{slug(o.label)}</span>
        </div>
      ))}
      {tbCustom && (
        <div>
          <span className="warn">    - </span>
          <span style={{ color: 'var(--fg)' }}>{slug(tbCustom)}</span>
        </div>
      )}
      <div style={{ height: 8 }} />
      <div className="mute">clocking:        ~  # pending</div>
      <div className="mute">register_map:    ~  # pending</div>
      <div className="mute">fsm:             ~  # pending</div>
      <div className="mute">acceptance:      ~  # pending</div>
    </div>
  );
};

const TodoPanel = () => {
  const [view, setView] = React.useState('compact'); // compact | detail | graph
  const [openId, setOpenId] = React.useState(null);
  const todos = window.TODOS;
  const done = todos.filter(t => t.state === 'done').length;

  const stateCfg = (s) =>
    s === 'done'   ? { glyph: '☒', color: 'var(--ok)' } :
    s === 'active' ? { glyph: '◉', color: 'var(--accent)' } :
                     { glyph: '☐', color: 'var(--fg-mute)' };

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
        display: 'flex', alignItems: 'center', gap: 6, fontSize: 11,
      }}>
        <span className="mute" style={{ fontFamily: 'var(--mono)' }}>{done}/{todos.length}</span>
        <span className="mute">·</span>
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
          <span style={{ color: 'var(--fg)' }}>claude-sonnet-4</span>
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
    <span>claude-sonnet-4</span>
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