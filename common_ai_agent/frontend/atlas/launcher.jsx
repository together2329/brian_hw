// launcher.jsx — Workspace launcher / dashboard

const Launcher = ({ dir, onScreen, onPickIp }) => {
  const stages = window.FLOW_STAGES;
  const ips = window.RECENT_IPS;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 16, padding: 16, height: '100%', overflow: 'hidden' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, overflow: 'hidden' }}>
        {/* Hero / flow overview */}
        <div className="box" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 6 }}>
            <div style={{ fontSize: 11, letterSpacing: '0.18em', color: 'var(--fg-mute)', textTransform: 'uppercase' }}>common_ai_agent · v0.4.2</div>
            <div style={{ fontSize: 11, color: 'var(--fg-mute)' }}>·</div>
            <div style={{ fontSize: 11, color: 'var(--fg-dim)' }}>Hardware design workflow for RTL/verification engineers</div>
          </div>
          <div style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.01em', marginBottom: 16, color: 'var(--fg)' }}>
            Pick a stage <span className="mute">·</span> the agent runs the loop.
          </div>

          {/* schematic flow strip */}
          <FlowStrip stages={stages} dir={dir} onScreen={onScreen} />
        </div>

        {/* Recent IPs table */}
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div className="box-h">
            <span>▸ Recent IPs</span>
            <span className="mute" style={{ fontSize: 10, letterSpacing: 0, textTransform: 'none' }}>{ips.length} projects · sorted by activity</span>
            <span style={{ flex: 1 }} />
            <span className="mute" style={{ textTransform: 'none', fontSize: 10, letterSpacing: 0 }}>
              <Kbd>↑↓</Kbd> select <span style={{ margin: '0 6px' }} /> <Kbd>↵</Kbd> open <span style={{ margin: '0 6px' }} /> <Kbd>n</Kbd> new
            </span>
          </div>
          <div style={{ flex: 1, overflow: 'auto' }}>
            <div style={{
              display: 'grid', gridTemplateColumns: '24px 1.4fr 90px 1fr 1fr 90px',
              padding: '6px 12px', fontSize: 10, letterSpacing: '0.08em', color: 'var(--fg-mute)',
              textTransform: 'uppercase', borderBottom: '1px solid var(--line)',
            }}>
              <span></span><span>IP Name</span><span>Status</span><span>Stage</span><span>Last Activity</span><span style={{ textAlign: 'right' }}>Findings</span>
            </div>
            {ips.map((ip, i) => (
              <div key={ip.name}
                onClick={() => { onPickIp(ip.name); onScreen('pipeline'); }}
                style={{
                  display: 'grid', gridTemplateColumns: '24px 1.4fr 90px 1fr 1fr 90px',
                  padding: '8px 12px', fontSize: 13, alignItems: 'center', cursor: 'pointer',
                  borderBottom: '1px solid var(--line)',
                  background: i === 0 ? 'var(--select)' : 'transparent',
                }}
                onMouseEnter={(e) => { if (i !== 0) e.currentTarget.style.background = 'var(--bg-2)'; }}
                onMouseLeave={(e) => { if (i !== 0) e.currentTarget.style.background = 'transparent'; }}
              >
                <span className="mute">{i === 0 ? '▸' : ' '}</span>
                <span style={{ fontWeight: 500 }}>{ip.name}</span>
                <span><StateLabel state={ip.status} /></span>
                <span className="dim">{ip.phase}</span>
                <span className="dim">{ip.date}</span>
                <span style={{ textAlign: 'right', fontSize: 12 }}>
                  {ip.warn > 0 && <span className="warn">{ip.warn}W </span>}
                  {ip.err > 0 && <span className="err">{ip.err}E</span>}
                  {ip.warn === 0 && ip.err === 0 && <span className="mute">—</span>}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right column: command quick start + system */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, overflow: 'hidden' }}>
        <div className="box">
          <div className="box-h"><span>▸ Quick start</span></div>
          <div style={{ padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
            {stages.map(s => (
              <div key={s.id}
                onClick={() => { onPickIp('spi_master'); onScreen('qa'); window.__qaStage = s.id === 'lint' ? 'rtl_gen' : s.id; window.dispatchEvent(new Event('qa-stage-change')); }}
                style={{
                  display: 'grid', gridTemplateColumns: '46px 1fr auto', alignItems: 'center', gap: 10,
                  padding: '10px 8px', cursor: 'pointer', borderRadius: 2,
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-2)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{
                  fontSize: 11, fontWeight: 700, letterSpacing: '0.08em',
                  textAlign: 'center', padding: '4px 0', color: s.color,
                  border: `1px solid ${s.color}`, borderRadius: 2,
                }}>{s.glyph}</div>
                <div>
                  <div style={{ fontWeight: 500 }}>{s.label}</div>
                  <div className="mute" style={{ fontSize: 11 }}>{s.detail}</div>
                </div>
                <code className="acc" style={{ fontSize: 11 }}>{s.cmd}</code>
              </div>
            ))}
          </div>
        </div>

        <div className="box">
          <div className="box-h"><span>▸ System</span></div>
          <div style={{ padding: '12px 14px', fontSize: 12, lineHeight: 1.9 }}>
            <Row k="model"        v={<><b style={{ color: 'var(--fg)' }}>{window.CONTEXT.model}</b> <span className="mute">primary</span></>} />
            <Row k="subagent.lo"  v={<>haiku-4.5 <span className="mute">explore/review</span></>} />
            <Row k="subagent.hi"  v={<>opus-4.1 <span className="mute">plan/execute</span></>} />
            <Row k="rate.limit"   v={<>{window.CONTEXT.rate} <span className="mute">between calls</span></>} />
            <Row k="safe.mode"    v={<span className="ok">true</span>} />
            <Row k="iter.max"     v={<>{window.CONTEXT.iterMax}</>} />
          </div>
        </div>

        <div className="box" style={{ padding: '12px 14px' }}>
          <div className="mute" style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 8 }}>tip</div>
          <div style={{ fontSize: 12, lineHeight: 1.55, color: 'var(--fg-dim)' }}>
            Every IP lives under one folder: <span className="acc">req/ rtl/ list/ tb/ sim/ lint/</span>.
            Type <span className="acc">/</span> anywhere to invoke a slash command, <span className="acc">@</span> to complete a file path.
          </div>
        </div>
      </div>
    </div>
  );
};

const Row = ({ k, v }) => (
  <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', gap: 8, fontFamily: 'var(--mono)' }}>
    <span className="mute">{k}</span>
    <span>{v}</span>
  </div>
);

// ── FlowStrip — schematic-style stage chain ──
const FlowStrip = ({ stages, dir, onScreen }) => {
  if (dir === 'A') {
    // ASCII: [ SSOT ] ──▶ [ RTL ] ──▶ [ LINT ] ──▶ [ TB ]
    return (
      <div style={{ fontFamily: 'var(--mono)', display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, marginTop: 8, flexWrap: 'wrap' }}>
        {stages.map((s, i) => (
          <React.Fragment key={s.id}>
            <span
              onClick={() => onScreen('pipeline')}
              style={{
                cursor: 'pointer',
                padding: '8px 14px',
                border: `1px solid ${s.color}`,
                color: s.color,
                fontWeight: 600,
                letterSpacing: '0.06em',
                background: 'var(--bg-2)',
              }}
            >{`[ ${s.glyph} · ${s.label} ]`}</span>
            {i < stages.length - 1 && <span className="mute" style={{ fontSize: 18 }}>──▶</span>}
          </React.Fragment>
        ))}
      </div>
    );
  }
  // B: SVG schematic blocks with connectors
  return (
    <div style={{ position: 'relative', height: 88, marginTop: 8 }}>
      <svg width="100%" height="88" style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        {stages.map((s, i) => {
          if (i === stages.length - 1) return null;
          const x1 = (i + 1) * (100 / stages.length) - (100 / stages.length) * 0.13;
          const x2 = (i + 1) * (100 / stages.length) + (100 / stages.length) * 0.13;
          return (
            <g key={i}>
              <line className="wire active" x1={`${x1}%`} y1="44" x2={`${x2}%`} y2="44" />
              <polygon points={`${x2 - 0.4},42 ${x2 - 0.4},46 ${x2},44`}
                transform={`translate(0 0)`} fill="var(--accent)" />
            </g>
          );
        })}
      </svg>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${stages.length}, 1fr)`, gap: 0, height: 88, position: 'relative', zIndex: 1 }}>
        {stages.map(s => (
          <div key={s.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div
              onClick={() => onScreen('pipeline')}
              style={{
                cursor: 'pointer',
                width: 152, height: 64,
                border: `1px solid var(--line-2)`,
                background: 'var(--panel)',
                borderRadius: 2,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                padding: '0 12px',
                position: 'relative',
              }}
            >
              <div style={{ fontSize: 10, letterSpacing: '0.12em', color: s.color, fontWeight: 700 }}>{s.glyph}</div>
              <div style={{ fontWeight: 500, marginTop: 2 }}>{s.label}</div>
              <div className="mute" style={{ fontSize: 10, marginTop: 2 }}>{s.cmd}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

window.Launcher = Launcher;
