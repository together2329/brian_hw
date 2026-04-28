// qa.jsx — Q&A flow for SSOT / RTL / TB detail authoring

const QAFlow = ({ dir, onScreen, stage, setStage }) => {
  const flow = window.QA_FLOWS[stage] || window.QA_FLOWS.ssot;
  const [opts, setOpts] = React.useState(flow.options);
  const [sel, setSel] = React.useState(0); // index of focused option (or option.length = submit row)
  const [textVal, setTextVal] = React.useState('');
  const [editing, setEditing] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  // reset when stage changes
  React.useEffect(() => {
    setOpts(flow.options);
    setSel(0);
    setTextVal('');
    setEditing(false);
    setSubmitted(false);
  }, [stage]);

  const totalRows = opts.length + 2; // options + free-input row + submit
  const TEXT_ROW = opts.length;
  const SUBMIT_ROW = opts.length + 1;

  const toggle = (i) => {
    if (opts[i].locked) return;
    if (flow.kind === 'multi') {
      setOpts(o => o.map((x, idx) => idx === i ? { ...x, selected: !x.selected } : x));
    } else {
      setOpts(o => o.map((x, idx) => ({ ...x, selected: idx === i })));
    }
  };

  const onKey = React.useCallback((e) => {
    if (editing) return; // text field captures keys
    if (e.key === 'ArrowDown' || e.key === 'j') { e.preventDefault(); setSel(s => Math.min(s + 1, totalRows - 1)); }
    else if (e.key === 'ArrowUp' || e.key === 'k') { e.preventDefault(); setSel(s => Math.max(s - 1, 0)); }
    else if (e.key === ' ' || e.key === 'x') {
      if (sel < opts.length) { e.preventDefault(); toggle(sel); }
    }
    else if (e.key === 'Enter') {
      if (sel === SUBMIT_ROW) { e.preventDefault(); doSubmit(); }
      else if (sel === TEXT_ROW) { e.preventDefault(); setEditing(true); }
      else { e.preventDefault(); toggle(sel); }
    }
    else if (e.key === 'Tab') { e.preventDefault(); setSel(s => (s + 1) % totalRows); }
    else if (e.key === 'Escape') { e.preventDefault(); onScreen('pipeline'); }
  }, [sel, editing, opts]);

  React.useEffect(() => {
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onKey]);

  const doSubmit = () => {
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 2200);
  };

  const selectedCount = opts.filter(o => o.selected).length;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr 320px', gap: 16, padding: 16, height: '100%', overflow: 'hidden' }}>
      {/* LEFT — stage detail switcher */}
      <div className="box" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="box-h"><span>▸ stage detail</span></div>
        <div style={{ padding: '8px 0' }}>
          {[
            { id: 'ssot',    name: 'SSOT Spec Detail',          color: 'var(--magenta)', glyph: 'SSOT' },
            { id: 'rtl_gen', name: 'RTL Implementation Style',  color: 'var(--accent)',  glyph: 'RTL'  },
            { id: 'tb_gen',  name: 'TB Detail',                  color: 'var(--ok)',     glyph: 'TB'   },
          ].map(s => (
            <div key={s.id}
              onClick={() => setStage(s.id)}
              style={{
                padding: '12px 14px',
                cursor: 'pointer',
                borderLeft: stage === s.id ? `2px solid ${s.color}` : '2px solid transparent',
                background: stage === s.id ? 'var(--select)' : 'transparent',
              }}
              onMouseEnter={(e) => { if (stage !== s.id) e.currentTarget.style.background = 'var(--bg-2)'; }}
              onMouseLeave={(e) => { if (stage !== s.id) e.currentTarget.style.background = 'transparent'; }}
            >
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
                <span style={{ color: s.color, fontSize: 10, fontWeight: 700, letterSpacing: '0.1em' }}>{s.glyph}</span>
                {stage === s.id && <span className="acc" style={{ fontSize: 10 }}>● ACTIVE</span>}
              </div>
              <div style={{ fontWeight: stage === s.id ? 500 : 400, fontSize: 13 }}>{s.name}</div>
            </div>
          ))}
        </div>
        <div style={{ borderTop: '1px solid var(--line)', padding: '12px 14px' }}>
          <div className="mute" style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>history</div>
          {flow.history.length === 0 && <div className="mute" style={{ fontSize: 11 }}>— no answers yet —</div>}
          {flow.history.map(h => (
            <div key={h.step} style={{ marginBottom: 8 }}>
              <div className="mute" style={{ fontSize: 10 }}>step {h.step} · {h.title}</div>
              <div style={{ fontSize: 12, color: 'var(--fg)', marginTop: 2 }}>✓ {h.answer}</div>
            </div>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ borderTop: '1px solid var(--line)', padding: '12px 14px' }}>
          <div className="mute" style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>upcoming</div>
          {flow.upcoming.map(u => (
            <div key={u.step} style={{ fontSize: 11, color: 'var(--fg-mute)', marginBottom: 4 }}>
              step {u.step} · {u.title}
            </div>
          ))}
        </div>
      </div>

      {/* CENTER — the big Q&A */}
      <div className="box" style={{ display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
        <div className="box-h">
          <span style={{ color: 'var(--accent)' }}>▸ {flow.title}</span>
          <span style={{ flex: 1 }} />
          <Pill kind="acc">{flow.stageDetail}</Pill>
        </div>

        {/* Breadcrumbs */}
        <div style={{ padding: '12px 24px 8px', borderBottom: '1px solid var(--line)', display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          {flow.breadcrumbs.map((b, i) => (
            <React.Fragment key={i}>
              <span style={{
                fontSize: 11,
                padding: '3px 8px',
                color: i === flow.activeBreadcrumb ? 'var(--bg)' : i < flow.activeBreadcrumb ? 'var(--ok)' : 'var(--fg-mute)',
                background: i === flow.activeBreadcrumb ? 'var(--accent)' : 'transparent',
                border: i === flow.activeBreadcrumb ? '1px solid var(--accent)' : `1px solid ${i < flow.activeBreadcrumb ? 'color-mix(in oklch, var(--ok) 40%, var(--line-2))' : 'var(--line)'}`,
                borderRadius: 2,
                letterSpacing: '0.02em',
              }}>
                {i < flow.activeBreadcrumb && '✓ '}
                {String(i + 1).padStart(2, '0')} {b}
              </span>
              {i < flow.breadcrumbs.length - 1 && <span className="mute" style={{ fontSize: 11 }}>›</span>}
            </React.Fragment>
          ))}
        </div>

        {/* Question + body */}
        <div style={{ flex: 1, overflow: 'auto', padding: '24px 32px' }}>
          <div style={{ marginBottom: 24 }}>
            <div className="mute" style={{ fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 6 }}>
              ?  Step {flow.step} of {flow.total} · {flow.kind === 'multi' ? 'multi-select' : flow.kind === 'single' ? 'single-select' : 'input'}
            </div>
            <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.01em', lineHeight: 1.3, marginBottom: 8 }}>
              {flow.question}
            </div>
            <div className="dim" style={{ fontSize: 13, lineHeight: 1.55, maxWidth: 760 }}>{flow.subtitle}</div>
          </div>

          {/* Options */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {opts.map((o, i) => (
              <OptionRow key={o.id}
                idx={i}
                opt={o}
                kind={flow.kind}
                focused={sel === i}
                onFocus={() => setSel(i)}
                onToggle={() => toggle(i)}
                dir={dir}
              />
            ))}

            {/* Free-input row */}
            <div
              onClick={() => { setSel(TEXT_ROW); setEditing(true); }}
              style={{
                marginTop: 4,
                display: 'grid', gridTemplateColumns: '40px 22px 1fr', gap: 12, alignItems: 'center',
                padding: '14px 14px',
                border: `1px solid ${sel === TEXT_ROW ? 'var(--accent)' : 'var(--line)'}`,
                background: sel === TEXT_ROW ? 'var(--bg-2)' : 'transparent',
                borderLeft: sel === TEXT_ROW ? '3px solid var(--accent)' : '3px solid var(--line)',
                cursor: 'text',
                borderRadius: 2,
              }}
            >
              <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{String(opts.length + 1).padStart(2, '0')}.</span>
              <span style={{ color: sel === TEXT_ROW ? 'var(--accent)' : 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>›</span>
              <div>
                <div style={{ fontSize: 13, marginBottom: 2 }}>
                  <span className="mute">Add custom · </span>
                  {editing ? (
                    <input autoFocus value={textVal}
                      onChange={e => setTextVal(e.target.value)}
                      onBlur={() => setEditing(false)}
                      onKeyDown={(e) => {
                        if (e.key === 'Escape') { e.preventDefault(); setEditing(false); }
                        if (e.key === 'Enter') { e.preventDefault(); setEditing(false); }
                      }}
                      placeholder="e.g. wishbone slave, custom protocol…"
                      style={{
                        background: 'transparent', border: 'none', outline: 'none',
                        color: 'var(--fg)', fontFamily: 'var(--mono)', fontSize: 13, width: 360,
                        borderBottom: '1px solid var(--accent)',
                      }}
                    />
                  ) : (
                    <span style={{ color: textVal ? 'var(--fg)' : 'var(--fg-mute)' }}>
                      {textVal || 'press ↵ or click to type your own…'}
                      {sel === TEXT_ROW && !editing && <span className="cursor-thin" style={{ marginLeft: 4 }} />}
                    </span>
                  )}
                </div>
                <div className="mute" style={{ fontSize: 11 }}>Free-form input is appended verbatim to the SSOT and reviewed in the next step.</div>
              </div>
            </div>

            {/* Submit row */}
            <div
              onClick={() => { setSel(SUBMIT_ROW); doSubmit(); }}
              style={{
                marginTop: 8,
                display: 'flex', alignItems: 'center', gap: 14,
                padding: '14px 18px',
                border: `1px solid ${sel === SUBMIT_ROW ? 'var(--accent)' : 'var(--line-2)'}`,
                background: sel === SUBMIT_ROW ? 'var(--accent)' : 'var(--bg-2)',
                color: sel === SUBMIT_ROW ? 'var(--bg)' : 'var(--fg)',
                cursor: 'pointer',
                borderRadius: 2,
              }}
            >
              <span style={{ fontWeight: 700, fontFamily: 'var(--mono)', letterSpacing: '0.06em' }}>
                {sel === SUBMIT_ROW ? '▸' : '·'} SUBMIT &amp; CONTINUE
              </span>
              <span style={{ flex: 1 }} />
              <span style={{ fontSize: 11, opacity: 0.85 }}>
                {selectedCount}{flow.kind === 'multi' ? ` selected` : flow.kind === 'single' ? ' chosen' : ''}
                {textVal && ` · 1 custom`}
              </span>
              <span style={{ fontSize: 11, opacity: 0.85 }}>→ next: {flow.upcoming[0]?.title || 'generate'}</span>
              <span className="kbd" style={{
                color: sel === SUBMIT_ROW ? 'var(--bg)' : 'var(--fg-dim)',
                borderColor: sel === SUBMIT_ROW ? 'var(--bg)' : 'var(--line)',
                background: 'transparent',
              }}>↵</span>
            </div>
          </div>

          {submitted && (
            <div className="fade-in" style={{
              marginTop: 16, padding: '12px 16px', border: '1px solid var(--ok)',
              background: 'color-mix(in oklch, var(--ok) 10%, transparent)',
              color: 'var(--ok)', fontSize: 13, borderRadius: 2,
              display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <span style={{ fontSize: 16 }}>✓</span>
              Step {flow.step} locked. Advancing to step {flow.step + 1}: <b>{flow.upcoming[0]?.title}</b>…
              <span style={{ flex: 1 }} />
              <button className="btn" onClick={() => onScreen('workspace')} style={{ borderColor: 'var(--ok)', color: 'var(--ok)' }}>Open Chat →</button>
            </div>
          )}

          {/* Inline chat shortcut */}
          <div style={{ marginTop: 24, padding: '12px 16px', border: '1px dashed var(--line-2)', borderRadius: 2, display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="mute" style={{ fontSize: 11, letterSpacing: '0.1em', textTransform: 'uppercase' }}>or chat freely</span>
            <span className="acc" style={{ fontSize: 13 }}>›</span>
            <span className="dim" style={{ fontSize: 12, flex: 1 }}>Skip the form and ask the agent anything — describe interfaces in plain English, paste a snippet, or run a slash command.</span>
            <button className="btn" onClick={() => onScreen('workspace')}>Open Chat <Kbd>⌘ ↵</Kbd></button>
          </div>
        </div>

        {/* Bottom keyhint bar */}
        <div style={{ borderTop: '1px solid var(--line)', padding: '8px 18px', display: 'flex', gap: 16, fontSize: 11, color: 'var(--fg-mute)', alignItems: 'center', background: 'var(--bg-2)' }}>
          <span><Kbd>↑↓</Kbd> navigate</span>
          <span><Kbd>Space</Kbd> {flow.kind === 'multi' ? 'toggle' : 'select'}</span>
          <span><Kbd>↵</Kbd> {sel === SUBMIT_ROW ? 'submit' : sel === TEXT_ROW ? 'edit input' : 'select & continue'}</span>
          <span><Kbd>Tab</Kbd> next field</span>
          <span><Kbd>Esc</Kbd> back</span>
          <span style={{ flex: 1 }} />
          <span className="acc">› Focus: {sel < opts.length ? `option ${sel + 1}` : sel === TEXT_ROW ? 'custom input' : 'submit'}</span>
        </div>
      </div>

      {/* RIGHT — preview / SSOT being built */}
      <div className="box" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="box-h"><span>▸ live preview</span><span style={{ flex: 1 }} /><span className="mute" style={{ textTransform: 'none', fontSize: 10, letterSpacing: 0 }}>spi_master · {stage === 'ssot' ? 'ssot' : stage === 'rtl_gen' ? 'rtl_style' : 'tb_plan'}.yaml</span></div>
        <div style={{ flex: 1, overflow: 'auto', padding: '14px 16px', fontFamily: 'var(--mono)', fontSize: 11.5, lineHeight: 1.65 }}>
          <PreviewMD stage={stage} flow={flow} opts={opts} textVal={textVal} />
        </div>
        <div style={{ borderTop: '1px solid var(--line)', padding: '10px 14px', fontSize: 10, color: 'var(--fg-mute)', display: 'flex', justifyContent: 'space-between' }}>
          <span>auto-saved · {new Date().toLocaleTimeString().slice(0, 5)}</span>
          <span>v3 · 47 specs</span>
        </div>
      </div>
    </div>
  );
};

const OptionRow = ({ idx, opt, kind, focused, onFocus, onToggle, dir }) => {
  const checked = opt.selected;
  return (
    <div
      onClick={() => { onFocus(); onToggle(); }}
      onMouseEnter={onFocus}
      style={{
        display: 'grid', gridTemplateColumns: '40px 22px 1fr auto', gap: 12, alignItems: 'center',
        padding: '14px 14px',
        border: `1px solid ${focused ? 'var(--accent)' : 'var(--line)'}`,
        background: focused ? 'var(--bg-2)' : 'transparent',
        borderLeft: focused ? '3px solid var(--accent)' : '3px solid transparent',
        cursor: opt.locked ? 'not-allowed' : 'pointer',
        opacity: opt.locked ? 0.75 : 1,
        borderRadius: 2,
      }}
    >
      <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{String(idx + 1).padStart(2, '0')}.</span>

      {/* checkbox / radio glyph */}
      <span style={{ fontFamily: 'var(--mono)', fontSize: 14, color: checked ? 'var(--accent)' : 'var(--fg-mute)' }}>
        {kind === 'single'
          ? (checked ? '◉' : '○')
          : (checked ? '[✓]' : '[ ]')}
      </span>

      <div>
        <div style={{ fontSize: 14, fontWeight: focused || checked ? 500 : 400, marginBottom: 2 }}>
          {opt.label}
          {opt.locked && <span className="mute" style={{ marginLeft: 8, fontSize: 10, letterSpacing: '0.08em' }}>· REQUIRED</span>}
        </div>
        <div className="dim" style={{ fontSize: 12, lineHeight: 1.45, fontFamily: 'var(--mono)' }}>{opt.detail}</div>
      </div>

      {checked && !opt.locked && <span className="ok" style={{ fontSize: 11 }}>✓ in spec</span>}
    </div>
  );
};

const PreviewMD = ({ stage, flow, opts, textVal }) => {
  const sel = opts.filter(o => o.selected);
  const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  return (
    <>
      <div className="mute"># spi_master · {flow.stageDetail}</div>
      <div className="mute">{'# generated by common_ai_agent'}</div>
      <div style={{ height: 8 }} />
      <div><span className="mag">ip:</span> <span style={{ color: 'var(--fg)' }}>spi_master</span></div>
      <div><span className="mag">version:</span> <span style={{ color: 'var(--fg)' }}>3</span></div>
      <div><span className="mag">stage:</span> <span style={{ color: 'var(--fg)' }}>{stage}</span></div>
      <div style={{ height: 8 }} />
      <div className="acc">overview:</div>
      <div>  <span className="mag">role:</span> <span style={{ color: 'var(--fg)' }}>spi_master_controller</span></div>
      <div>  <span className="mag">topology:</span> <span style={{ color: 'var(--fg)' }}>single_master</span></div>
      <div>  <span className="mag">cs_count:</span> <span style={{ color: 'var(--fg)' }}>4</span></div>
      <div style={{ height: 8 }} />
      <div className="acc">use_case:</div>
      <div>  <span className="ok">- </span>sensor_polling</div>
      <div>  <span className="ok">- </span>flash_config</div>
      <div>  <span className="ok">- </span>low_latency_burst</div>
      <div style={{ height: 8 }} />
      <div className="acc">interfaces:</div>
      {sel.length === 0 && <div className="mute">  []  # no selections yet</div>}
      {sel.map(o => (
        <div key={o.id}>
          <span className="ok">  - </span>
          <span style={{ color: 'var(--fg)' }}>{slug(o.label)}</span>
          <span className="mute"> {'  # ' + o.detail.split('·')[0].trim()}</span>
        </div>
      ))}
      {textVal && (
        <div>
          <span className="warn">  - </span>
          <span style={{ color: 'var(--fg)' }}>{slug(textVal)}</span>
          <span className="warn" style={{ marginLeft: 6 }}>  # custom</span>
        </div>
      )}
      <div style={{ height: 8 }} />
      <div className="mute">clocking:        ~  # pending</div>
      <div className="mute">register_map:    ~  # pending</div>
      <div className="mute">fsm:             ~  # pending</div>
      <div className="mute">acceptance:      ~  # pending</div>
    </>
  );
};

window.QAFlow = QAFlow;
