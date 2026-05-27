// debug-var4.jsx — VARIATION 4: Tri-surface Prompt-first Debug
// Combines V3's prompt-first agent thread (vcd.open → vcd.trace →
// observation → sr.read tool sequence) with persistent V1-style
// waveform AND source panels. Tool calls in the chat drive what's
// shown in the side panels — clicking a tool card scrolls/cursors
// the relevant panel; the user can also drive panels manually.

const normalizeProjectSourcePath = (rawPath) => {
  const raw = String(rawPath || '').replace(/\\/g, '/').replace(/:\d+$/, '');
  const marker = '/common_ai_agent/';
  const idx = raw.indexOf(marker);
  if (idx >= 0) return raw.slice(idx + marker.length);
  return raw.replace(/^\/+/, '');
};

const normalizeAtlasEventSession = (session) => {
  const norm = (window.atlasData && window.atlasData.normalizeSessionName) || window.normalizeAtlasSessionName;
  try { return norm ? norm(session || '') : ''; }
  catch (_) { return ''; }
};

const atlasEventMatchesActiveSession = (m, opts = {}) => {
  const eventSession = normalizeAtlasEventSession((m && (m.session_id || m.session || m.namespace)) || '');
  const activeSession = normalizeAtlasEventSession(
    window.ACTIVE_SESSION
    || (window.CONTEXT && (window.CONTEXT.activeSession || window.CONTEXT.active_session))
    || ''
  );
  if (!activeSession) return !opts.requireSession;
  if (!eventSession) return !opts.requireSession;
  return eventSession === activeSession;
};

const isDumpScopeName = (name) => {
  const n = String(name || '');
  return n === 'iverilog_dump' || n === 'atlas_iverilog_vcd_dump' || /_vcd_dump$/.test(n);
};

const inferRtlTopFromVcd = (parsed, fallback = '') => {
  const signals = Array.isArray(parsed?.signals) ? parsed.signals : [];
  for (const sig of signals) {
    const first = String(sig?.scope || '').split('.').find(Boolean) || '';
    if (first && !isDumpScopeName(first)) return first;
  }
  return fallback || '';
};

const activeIpFromAtlasRuntime = () => {
  if (typeof window === 'undefined') return '';
  const direct = String(window.ACTIVE_IP || '').trim();
  if (direct && direct !== 'default') return direct;
  const ctxIp = String((window.CONTEXT && (window.CONTEXT.active_ip || window.CONTEXT.activeIp)) || '').trim();
  if (ctxIp && ctxIp !== 'default') return ctxIp;
  const parts = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
  const sessionIp = parts.length >= 2 ? String(parts[1] || '').trim() : '';
  return sessionIp && sessionIp !== 'default' ? sessionIp : '';
};

const vcdPathBelongsToIp = (path, ip) => {
  const p = String(path || '').replace(/\\/g, '/').replace(/^\/+/, '');
  const owner = String(ip || '').replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
  return !!owner && (p === owner || p.startsWith(owner + '/'));
};

const stripSignalRange = (name) => String(name || '').replace(/\s*\[[^\]]+\]\s*$/g, '').trim();

const vcdValueAtTrace = (trace, time) => {
  if (!Array.isArray(trace) || trace.length === 0) return '?';
  const target = Number(time);
  if (!Number.isFinite(target)) return '?';
  let value = '?';
  for (const sample of trace) {
    if (!Array.isArray(sample)) continue;
    const t = Number(sample[0]);
    if (!Number.isFinite(t)) continue;
    if (t > target) break;
    value = sample[1];
  }
  return value == null ? '?' : value;
};

const formatVcdValue = (value, isBus) => {
  if (value == null) return '?';
  const s = String(value);
  if (!isBus) return s;
  if (/^[01]+$/.test(s)) {
    try {
      return '0x' + BigInt('0b' + s).toString(16).toUpperCase();
    } catch (_) {
      return s;
    }
  }
  return s;
};

const VERILOG_KEYWORDS = new Set([
  'always', 'always_comb', 'always_ff', 'assign', 'begin', 'case', 'default', 'else',
  'end', 'endcase', 'endmodule', 'for', 'generate', 'if', 'input', 'logic', 'module',
  'negedge', 'or', 'output', 'parameter', 'posedge', 'reg', 'wire',
]);

const sourceLineIdentifiers = (line) => {
  const ids = [];
  const seen = new Set();
  const text = String(line || '');
  const re = /\b[A-Za-z_][A-Za-z0-9_$]*\b/g;
  let m;
  while ((m = re.exec(text))) {
    const id = m[0];
    const key = id.toLowerCase();
    if (VERILOG_KEYWORDS.has(key) || seen.has(key)) continue;
    seen.add(key);
    ids.push(id);
  }
  return ids;
};

const signalAliasKeys = (sig) => {
  const aliases = [
    sig?.signalName,
    sig?.name,
    stripSignalRange(sig?.name),
  ];
  return aliases
    .map(a => String(a || '').trim())
    .filter(Boolean)
    .flatMap(a => [a, a.split('.').pop()])
    .map(a => stripSignalRange(a).toLowerCase())
    .filter(Boolean);
};

const buildVcdLineAnnotations = ({ line, traceList, selectedSig, cursorA, cursorB, limit = 8 }) => {
  if (!Array.isArray(traceList) || traceList.length === 0) return [];
  const byAlias = new Map();
  for (const sig of traceList) {
    for (const alias of signalAliasKeys(sig)) {
      if (!byAlias.has(alias)) byAlias.set(alias, sig);
    }
  }

  const wanted = [];
  const pushWanted = (name) => {
    const key = stripSignalRange(name).toLowerCase();
    if (key && !wanted.includes(key)) wanted.push(key);
  };
  pushWanted(selectedSig);
  sourceLineIdentifiers(line).forEach(pushWanted);

  const rows = [];
  const seen = new Set();
  for (const key of wanted) {
    const sig = byAlias.get(key);
    if (!sig) continue;
    const display = sig.name || sig.signalName || key;
    const dedupe = stripSignalRange(display).toLowerCase();
    if (seen.has(dedupe)) continue;
    seen.add(dedupe);
    rows.push({
      name: display,
      a: formatVcdValue(vcdValueAtTrace(sig.trace, cursorA), sig.isBus),
      b: formatVcdValue(vcdValueAtTrace(sig.trace, cursorB), sig.isBus),
    });
    if (rows.length >= limit) break;
  }
  return rows;
};

if (typeof window !== 'undefined') {
  window.simDebugActiveIpFromAtlasRuntime = activeIpFromAtlasRuntime;
  window.simDebugVcdPathBelongsToIp = vcdPathBelongsToIp;
  window.simDebugVcdValueAtTrace = vcdValueAtTrace;
  window.simDebugBuildVcdLineAnnotations = buildVcdLineAnnotations;
}

// Cocotb (testbench) tree view — categorised file list + parsed
// results.xml summary. Click any file to load it in the source viewer.
const CocotbTreeView = ({ data, ipName, onOpenFile }) => {
  const [openSection, setOpenSection] = React.useState({
    tests: true, sequences: true, env: true, agent: true, other: false, build: false,
  });
  const toggle = (k) => setOpenSection(s => ({ ...s, [k]: !s[k] }));

  if (!data) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                     color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', fontStyle: 'italic' }}>
        loading cocotb env…
      </div>
    );
  }
  if (data.error || !data.exists) {
    return (
      <div style={{ flex: 1, padding: 12, color: 'var(--fg-mute)', fontSize: 11 }}>
        no cocotb env at <code>{ipName}/cocotb/</code><br/>
        {data.error && <span style={{ color: 'var(--err)' }}>{data.error}</span>}
      </div>
    );
  }
  const r = data.results || {};
  const Sec = ({ k, label }) => {
    const items = data[k] || [];
    if (!items.length) return null;
    return (
      <div style={{ marginBottom: 4 }}>
        <div
          onClick={() => toggle(k)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '3px 4px', cursor: 'pointer',
            color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.06em',
            textTransform: 'uppercase', userSelect: 'none',
          }}
        >
          <span style={{ width: 10 }}>{openSection[k] ? '▾' : '▸'}</span>
          <span>{label}</span>
          <span style={{ color: 'var(--fg-dim)' }}>({items.length})</span>
        </div>
        {openSection[k] && items.map(f => (
          <div
            key={f.path}
            onClick={() => onOpenFile && onOpenFile(f.path, 0)}
            style={{
              padding: '1px 4px 1px 22px', cursor: 'pointer',
              color: 'var(--fg)', fontSize: 'var(--ui-control-font-size)',
            }}
            title={f.path}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <span style={{ color: 'var(--fg-mute)' }}>·</span> {f.name}
            <span style={{ color: 'var(--fg-mute)', fontSize: 9, marginLeft: 4 }}>
              {f.size < 1024 ? f.size + 'B' : (f.size/1024).toFixed(1) + 'K'}
            </span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
      {/* Test result summary */}
      {r && r.total != null && (
        <div style={{
          padding: '6px 8px', marginBottom: 8,
          background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 3,
        }}>
          <div style={{
            color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em',
            textTransform: 'uppercase', marginBottom: 4,
          }}>results.xml</div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--ok)', fontWeight: 700 }}>✓ {r.pass}</span>
            <span style={{ color: 'var(--err)', fontWeight: 700 }}>✗ {r.fail}</span>
            <span style={{ color: 'var(--fg-mute)' }}>⊘ {r.skip}</span>
            <span style={{ color: 'var(--fg-mute)' }}>/ {r.total} total</span>
          </div>
          {r.cases && r.cases.length > 0 && (
            <div style={{ marginTop: 6 }}>
              {r.cases.slice(0, 12).map((c, i) => (
                <div
                  key={i}
                  onClick={() => c.file && onOpenFile && onOpenFile(c.file, c.line || 0)}
                  style={{ padding: '2px 0', cursor: c.file ? 'pointer' : 'default', display: 'flex', gap: 6 }}
                  title={c.file ? `${c.file}:${c.line}` : ''}
                >
                  <span style={{
                    color: c.status === 'pass' ? 'var(--ok)' : c.status === 'fail' ? 'var(--err)' : 'var(--fg-mute)',
                    width: 14,
                  }}>{c.status === 'pass' ? '✓' : c.status === 'fail' ? '✗' : '⊘'}</span>
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</span>
                  <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}>
                    {c.sim_time_ns ? `${parseFloat(c.sim_time_ns).toFixed(0)}ns` : `${(c.time_s*1000).toFixed(0)}ms`}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      {r && r.error && (
        <div style={{ color: 'var(--err)', fontSize: 10, marginBottom: 8 }}>
          results.xml: {r.error}
        </div>
      )}
      {/* TB hierarchy — env / agent / scoreboard / sequence / test classes
          extracted via Python AST. Same role as RTL hierarchy from
          pyslang, but for the Pythonic testbench side. */}
      {data.tb_hierarchy && (
        <TBHierarchyView h={data.tb_hierarchy} onOpenFile={onOpenFile} />
      )}

      <Sec k="tests"     label="tests" />
      <Sec k="sequences" label="sequences" />
      <Sec k="env"       label="env" />
      <Sec k="agent"     label="agents" />
      <Sec k="other"     label="other" />
      <Sec k="build"     label="sim_build" />
    </div>
  );
};

const SimResultBadge = ({ status }) => {
  const st = String(status || 'pending').toLowerCase();
  const color = st === 'pass' ? 'var(--ok)' : st === 'fail' ? 'var(--err)' : 'var(--warn)';
  const label = st === 'skip' ? 'pending' : st;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: 64, padding: '2px 8px', borderRadius: 3,
      border: '1px solid color-mix(in oklch, ' + color + ' 34%, var(--line))',
      background: 'color-mix(in oklch, ' + color + ' 12%, transparent)',
      color, fontFamily: 'var(--mono)', fontSize: 10, fontWeight: 800,
      letterSpacing: '0.06em', textTransform: 'uppercase',
    }}>{label}</span>
  );
};

const SimSummaryPanel = ({ ipName, data, loading, error, cocotbData, onOpenFile, onRefresh }) => {
  const scenarioRows = Array.isArray(data?.tests) ? data.tests.map((t, i) => ({
    id: t.scenario_id || `TC${i + 1}`,
    name: t.name || t.scenario_id || `TC${i + 1}`,
    status: t.status || 'pending',
    evidence: `${t.pass_rows || 0} pass / ${t.fail_rows || 0} fail`,
    expected: t.expected || '',
    checker: t.checker || '',
    source: t.source || 'ssot',
    file: '',
    line: 0,
  })) : [];
  const resultCases = Array.isArray(cocotbData?.results?.cases)
    ? cocotbData.results.cases.map((c, i) => ({
      id: c.name || `TC${i + 1}`,
      name: c.classname ? `${c.classname}.${c.name}` : (c.name || `TC${i + 1}`),
      status: c.status === 'skip' ? 'pending' : (c.status || 'pending'),
      evidence: c.sim_time_ns ? `${parseFloat(c.sim_time_ns || '0').toFixed(0)} ns` : `${Math.round((c.time_s || 0) * 1000)} ms`,
      expected: '',
      checker: 'results.xml',
      source: 'results.xml',
      file: c.file || '',
      line: c.line || 0,
    }))
    : [];
  const rows = scenarioRows.length ? scenarioRows : resultCases;
  const counts = rows.reduce((acc, r) => {
    const st = r.status === 'skip' ? 'pending' : (r.status || 'pending');
    acc[st] = (acc[st] || 0) + 1;
    acc.total += 1;
    return acc;
  }, { pass: 0, fail: 0, pending: 0, total: 0 });
  const evidencePaths = [
    data?.ssot_path,
    data?.sb_path,
    ipName ? `${ipName}/sim/results.xml` : '',
    ipName ? `${ipName}/tb/cocotb/results.xml` : '',
  ].filter(Boolean);

  const Stat = ({ label, value, color }) => (
    <div style={{
      minWidth: 118, padding: '10px 12px',
      border: '1px solid var(--line)', borderRadius: 4,
      background: 'var(--bg-2)',
    }}>
      <div style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ color, fontSize: 24, fontWeight: 800, fontFamily: 'var(--mono)', marginTop: 4 }}>{value}</div>
    </div>
  );

  return (
    <div style={{
      flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
      background: 'var(--panel)', color: 'var(--fg)',
    }}>
      <div style={{
        padding: '12px 14px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            Sim Summary
          </div>
          <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginTop: 2, fontFamily: 'var(--mono)' }}>
            {ipName || '(no IP selected)'} · TC pass/fail
          </div>
        </div>
        <span style={{ flex: 1 }} />
        {loading && <span style={{ color: 'var(--accent)', fontSize: 10, fontFamily: 'var(--mono)' }}>loading</span>}
        <button className="btn" onClick={onRefresh} style={{ padding: '2px 8px', fontSize: 10 }}>refresh</button>
      </div>

      <div style={{ padding: 14, display: 'flex', gap: 10, flexWrap: 'wrap', borderBottom: '1px solid var(--line)' }}>
        <Stat label="pass" value={counts.pass || 0} color="var(--ok)" />
        <Stat label="fail" value={counts.fail || 0} color="var(--err)" />
        <Stat label="pending" value={counts.pending || 0} color="var(--warn)" />
        <Stat label="total" value={counts.total || 0} color="var(--fg)" />
      </div>

      {error && (
        <div style={{
          padding: '8px 14px', borderBottom: '1px solid var(--err)',
          background: 'color-mix(in oklch, var(--err) 10%, transparent)',
          color: 'var(--err)', fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)',
        }}>{error}</div>
      )}

      <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--line)', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {evidencePaths.length ? evidencePaths.map(p => (
          <button
            key={p}
            className="btn"
            onClick={() => onOpenFile && onOpenFile(p, 0)}
            title={p}
            style={{ padding: '2px 8px', fontSize: 10, fontFamily: 'var(--mono)' }}
          >{p.split('/').slice(-2).join('/')}</button>
        )) : (
          <span style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)' }}>no sim evidence files resolved</span>
        )}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 14 }}>
        {rows.length ? (
          <div style={{ border: '1px solid var(--line)', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{
              display: 'grid', gridTemplateColumns: 'minmax(120px, 0.9fr) minmax(220px, 1.4fr) 88px minmax(120px, 0.8fr) minmax(220px, 1.2fr)',
              gap: 0, padding: '7px 10px', background: 'var(--bg-2)',
              color: 'var(--fg-mute)', fontSize: 10, fontFamily: 'var(--mono)',
              letterSpacing: '0.07em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)',
            }}>
              <span>TC</span><span>Name</span><span>Status</span><span>Evidence</span><span>Checker / Expected</span>
            </div>
            {rows.map((r, i) => (
              <div
                key={`${r.id}-${i}`}
                onClick={() => r.file && onOpenFile && onOpenFile(r.file, r.line || 0)}
                style={{
                  display: 'grid', gridTemplateColumns: 'minmax(120px, 0.9fr) minmax(220px, 1.4fr) 88px minmax(120px, 0.8fr) minmax(220px, 1.2fr)',
                  gap: 0, padding: '8px 10px', borderBottom: i === rows.length - 1 ? 'none' : '1px solid var(--line)',
                  background: i % 2 ? 'var(--bg)' : 'transparent',
                  cursor: r.file ? 'pointer' : 'default', alignItems: 'center',
                  fontSize: 'var(--ui-control-font-size)',
                }}
                title={r.file ? `${r.file}:${r.line || 0}` : ''}
              >
                <span style={{ fontFamily: 'var(--mono)', color: 'var(--cyan)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.id}</span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.name}</span>
                <SimResultBadge status={r.status} />
                <span style={{ fontFamily: 'var(--mono)', color: 'var(--fg-mute)' }}>{r.evidence || r.source}</span>
                <span style={{ color: 'var(--fg-mute)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {r.checker || r.expected || r.source || '-'}
                  {r.expected && r.checker ? ` · ${r.expected}` : ''}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{
            border: '1px solid var(--line)', borderRadius: 4,
            padding: 20, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12,
            background: 'var(--bg-2)',
          }}>
            {ipName
              ? `No TC rows yet for ${ipName}.`
              : 'Select IP_ID to load sim summary.'}
          </div>
        )}
      </div>
    </div>
  );
};

// TB class hierarchy — env → agents → drivers/monitors → sequencer →
// sequences. Plus tests at the top. Each entry clickable for source jump.
const TBHierarchyView = ({ h, onOpenFile }) => {
  const Group = ({ title, items, color }) => {
    if (!items || !items.length) return null;
    return (
      <div style={{ marginBottom: 6 }}>
        <div style={{
          color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.06em',
          textTransform: 'uppercase', marginBottom: 2,
        }}>{title} ({items.length})</div>
        {items.map((x, i) => (
          <div
            key={i}
            onClick={() => onOpenFile && x.file && onOpenFile(x.file, x.line || 0)}
            style={{
              padding: '1px 4px 1px 12px', cursor: 'pointer',
              fontSize: 'var(--ui-control-font-size)', color: color || 'var(--fg)',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}
            title={`${x.file}:${x.line}` + (x.bases?.length ? ` extends ${x.bases.join(', ')}` : '')}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <span style={{ color: 'var(--fg-mute)' }}>·</span>{' '}
            <span>{x.name}</span>
            {x.bases && x.bases.length > 0 && (
              <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}> ({x.bases.join(',').slice(0, 30)})</span>
            )}
            {x.decorators && x.decorators.length > 0 && (
              <span style={{ color: 'var(--magenta)', fontSize: 9 }}> @{x.decorators.join(',').replace(/cocotb\./g,'').slice(0, 22)}</span>
            )}
          </div>
        ))}
      </div>
    );
  };
  return (
    <div style={{
      marginBottom: 8, padding: '6px 8px',
      background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 3,
    }}>
      <div style={{
        color: 'var(--accent)', fontSize: 10, fontWeight: 700,
        letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6,
        borderBottom: '1px solid var(--line)', paddingBottom: 4,
      }}>TB hierarchy (cocotb / UVM)</div>
      <Group title="environment"  items={h.envs}        color="#7CFC4D" />
      <Group title="scoreboards"  items={h.scoreboards} color="#ffd24d" />
      <Group title="agents / BFM" items={h.agents}      color="#4dd0e1" />
      <Group title="sequences"    items={h.sequences}   color="#ff6bd0" />
      <Group title="@cocotb.test" items={h.tests}       color="#ffb84d" />
    </div>
  );
};

// Editable view-range input pair. User can type the start/end time
// directly to jump there. Blur or Enter commits; Esc reverts. Clamps
// to the VCD's full timeRange.
const RangeInput = ({ effRange, vcdData, setViewRange }) => {
  const ts = vcdData ? vcdData.timescale : 'ns';
  const full = vcdData ? vcdData.timeRange : [0, 0];
  const fullSpan = (full[1] - full[0]) || 1;
  const viewSpan = effRange[1] - effRange[0];
  const zoomPct = (fullSpan / Math.max(1e-9, viewSpan)) * 100;

  const [startTxt, setStartTxt] = React.useState(String(Math.round(effRange[0])));
  const [endTxt,   setEndTxt]   = React.useState(String(Math.round(effRange[1])));
  React.useEffect(() => { setStartTxt(String(Math.round(effRange[0]))); }, [effRange[0]]);
  React.useEffect(() => { setEndTxt  (String(Math.round(effRange[1]))); }, [effRange[1]]);

  const commit = () => {
    if (!vcdData) return;
    const a = Number(startTxt), b = Number(endTxt);
    if (Number.isNaN(a) || Number.isNaN(b)) return;
    const lo = Math.max(full[0], Math.min(a, b));
    const hi = Math.min(full[1], Math.max(a, b));
    if (hi - lo < 1) return;
    setViewRange([lo, hi]);
  };

  const inputStyle = {
    background: '#0d1118',
    color: 'var(--accent)',
    border: '1px solid #2a3140',
    padding: '1px 4px',
    width: 80,
    fontSize: 10,
    fontFamily: 'var(--mono)',
    textAlign: 'right',
  };

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      marginRight: 8, fontFamily: 'var(--mono)', fontSize: 10,
      whiteSpace: 'nowrap',
    }} title={`view ${effRange[0]}–${effRange[1]} ${ts}\nfull ${full[0]}–${full[1]} ${ts}\nzoom ${zoomPct.toFixed(0)}%`}>
      <span style={{ color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>view</span>
      <input
        type="number"
        value={startTxt}
        onChange={e => setStartTxt(e.target.value)}
        onBlur={commit}
        onKeyDown={e => {
          if (e.key === 'Enter') { e.target.blur(); }
          if (e.key === 'Escape') { setStartTxt(String(Math.round(effRange[0]))); e.target.blur(); }
          e.stopPropagation();
        }}
        style={inputStyle}
      />
      <span style={{ color: 'var(--fg-mute)' }}>–</span>
      <input
        type="number"
        value={endTxt}
        onChange={e => setEndTxt(e.target.value)}
        onBlur={commit}
        onKeyDown={e => {
          if (e.key === 'Enter') { e.target.blur(); }
          if (e.key === 'Escape') { setEndTxt(String(Math.round(effRange[1]))); e.target.blur(); }
          e.stopPropagation();
        }}
        style={inputStyle}
      />
      <span style={{ color: 'var(--fg-dim)' }}>{ts}</span>
      <span style={{ color: 'var(--fg-dim)', marginLeft: 4 }}>
        ({viewSpan.toFixed(0)}{ts}) · {zoomPct >= 100 ? `×${(zoomPct/100).toFixed(1)}` : `${zoomPct.toFixed(0)}%`}
      </span>
      <span style={{ color: 'var(--fg-mute)', marginLeft: 4 }}>
        full {full[0]}–{full[1]}
      </span>
    </span>
  );
};

// Lightweight syntax-highlighted source viewer. Uses Prism (loaded
// globally from index.html — language autoloader fetches the grammar
// for the file extension on demand). Renders each line in its own
// row so line numbers + cursor highlight + per-line click work.
const SourceViewer = ({ lines, cursor, path, vcdAnnotations = {} }) => {
  const ref = React.useRef(null);
  // Bump on every Prism load so we re-render once the grammar arrives.
  const [grammarTick, setGrammarTick] = React.useState(0);

  // Resolve language id from extension via window.PRISM_LANG_MAP.
  const ext = (path || '').match(/\.([a-zA-Z0-9]+)$/)?.[1]?.toLowerCase() || '';
  const langId = (window.PRISM_LANG_MAP || {})[ext] || 'none';

  // Highlighted-per-line HTML. If Prism + the grammar are ready we run
  // it; otherwise we fall back to plain escaped text so the panel
  // never goes blank while the autoloader fetches.
  const lineHTMLs = React.useMemo(() => {
    if (!lines || lines.length === 0) return [];
    const fullCode = lines.join('\n');
    const Prism = window.Prism;
    if (Prism && Prism.languages && Prism.languages[langId]) {
      try {
        const html = Prism.highlight(fullCode, Prism.languages[langId], langId);
        return html.split('\n');
      } catch (_) {/* fall through */}
    }
    // No grammar yet — escape and split. Trigger autoloader.
    if (Prism && Prism.plugins && Prism.plugins.autoloader && langId !== 'none') {
      Prism.plugins.autoloader.loadLanguages(langId, () => setGrammarTick(t => t + 1));
    }
    return lines.map(ln =>
      ln.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    );
  }, [lines, langId, grammarTick]);

  React.useEffect(() => {
    if (cursor > 0 && ref.current) {
      const el = ref.current.querySelector(`[data-ln="${cursor}"]`);
      if (el && el.scrollIntoView) el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }, [cursor, lines]);

  if (!lines || lines.length === 0) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                     color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', fontStyle: 'italic' }}>
        no source loaded — click a hierarchy module or a wave signal
      </div>
    );
  }
  return (
    <div ref={ref} className="src-viewer" style={{
      flex: 1, overflow: 'auto', padding: '6px 0',
      fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.45,
      background: 'var(--panel)',
    }}>
      {lineHTMLs.map((html, i) => {
        const lineNo = i + 1;
        const isCur = cursor === lineNo;
        const ann = vcdAnnotations[lineNo] || [];
        return (
          <React.Fragment key={i}>
            <div
              data-ln={lineNo}
              style={{
                display: 'grid',
                gridTemplateColumns: '46px 1fr',
                padding: '0 8px',
                background: isCur ? 'color-mix(in oklch, var(--accent) 18%, transparent)' : 'transparent',
                borderLeft: isCur ? '2px solid var(--accent)' : '2px solid transparent',
              }}
            >
              <span style={{
                color: isCur ? 'var(--accent)' : 'var(--fg-mute)',
                textAlign: 'right', paddingRight: 8, userSelect: 'none',
                fontSize: 10,
              }}>{lineNo}</span>
              <span
                style={{ whiteSpace: 'pre' }}
                dangerouslySetInnerHTML={{ __html: html }}
              />
            </div>
            {ann.length > 0 && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: '46px 1fr',
                padding: '2px 8px 5px',
                borderLeft: '2px solid var(--cyan)',
                background: 'color-mix(in oklch, var(--cyan) 9%, transparent)',
              }}>
                <span style={{
                  color: 'var(--cyan)', textAlign: 'right', paddingRight: 8,
                  fontSize: 9, userSelect: 'none',
                }}>vcd</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {ann.map(item => (
                    <span key={item.name} style={{
                      border: '1px solid color-mix(in oklch, var(--cyan) 40%, var(--line))',
                      borderRadius: 3,
                      padding: '0 5px',
                      color: 'var(--fg)',
                      background: 'var(--bg)',
                      fontSize: 10,
                      whiteSpace: 'nowrap',
                    }}>
                      <b style={{ color: 'var(--cyan)' }}>{item.name}</b>
                      <span style={{ color: 'var(--accent)', marginLeft: 5 }}>A={item.a}</span>
                      <span style={{ color: 'var(--cyan)', marginLeft: 5 }}>B={item.b}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

// Recursive collapsible tree node for the instance hierarchy panel.
// Click on the chevron toggles children; click on the module name fires
// `onSelectModule` so SimDebug can load the matching SV source. The
// instance path stays foreground (accent), module name is cyan.
const HierarchyNode = ({ node, depth, onSelectModule, activeModule }) => {
  const [open, setOpen] = React.useState(depth < 2);
  if (!node) return null;
  const hasKids = (node.children || []).length > 0;
  const indent = depth * 14;
  const last = (node.name || '').split('.').pop();
  const isActive = activeModule === node.module;
  return (
    <div>
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '2px 0 2px ' + indent + 'px',
          color: 'var(--fg)',
          background: isActive ? 'color-mix(in oklch, var(--accent) 18%, transparent)' : 'transparent',
          borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
        }}
      >
        <span
          onClick={() => hasKids && setOpen(o => !o)}
          style={{
            width: 12, color: 'var(--fg-mute)', fontSize: 9,
            cursor: hasKids ? 'pointer' : 'default',
          }}
        >
          {hasKids ? (open ? '▾' : '▸') : '·'}
        </span>
        <span
          onClick={() => onSelectModule && onSelectModule(node.module, node.name)}
          style={{ color: 'var(--accent)', cursor: 'pointer' }}
          title="open module source"
        >{last}</span>
        <span style={{ color: 'var(--fg-mute)' }}>::</span>
        <span
          onClick={() => onSelectModule && onSelectModule(node.module, node.name)}
          style={{ color: 'var(--cyan)', cursor: 'pointer' }}
          title="open module source"
        >{node.module}</span>
        {node.cyclic && (
          <span style={{ color: 'var(--err)', fontSize: 9, marginLeft: 4 }}>cyclic</span>
        )}
      </div>
      {open && hasKids && node.children.map((c, i) => (
        <HierarchyNode key={i} node={c} depth={depth + 1}
          onSelectModule={onSelectModule} activeModule={activeModule} />
      ))}
    </div>
  );
};

window.SimDebug = ({ view = 'debug', initialTab = '' } = {}) => {
  const summaryOnly = view === 'summary';
  const initialTopTab = summaryOnly ? 'summary' : (initialTab || 'wave');
  // Cross-panel state — the agent's "current focus"
  const [activeTool, setActiveTool] = React.useState('vcd.trace'); // last tool the user clicked
  // Cursors default to null until VCD loads — real positions come from
  // 25 % / 75 % of the actual timeRange (no more 110 / 160 mock values).
  const [waveCursor,  setWaveCursor]  = React.useState(0);
  const [waveCursorB, setWaveCursorB] = React.useState(0);
  // View range [start, end] — what slice of the VCD is mapped onto the
  // wave panel width. null = "fit" (whole VCD). Zoom buttons + ctrl+wheel
  // mutate this; "fit" resets it to null.
  const [viewRange, setViewRange] = React.useState(null);
  const [showHelp, setShowHelp] = React.useState(false);
  const [showVcdAnnotations, setShowVcdAnnotations] = React.useState(false);
  // Left panel mode — switch between RTL hierarchy and TB (cocotb) tree.
  const [leftTab, setLeftTab] = React.useState('rtl');  // 'rtl' | 'tb'
  const [cocotbData, setCocotbData] = React.useState(null);
  const [simSummary, setSimSummary] = React.useState(null);
  const [simSummaryLoading, setSimSummaryLoading] = React.useState(false);
  const [simSummaryError, setSimSummaryError] = React.useState('');
  const [simSummaryReload, setSimSummaryReload] = React.useState(0);
  // No mock srcRange — the live SourceViewer drives everything from
  // srcLines / srcCursor. Kept as a stub for any leftover references.
  const [srcRange, setSrcRange] = React.useState({ from: 0, to: 0, hl: [], cur: 0 });
  const [selectedSig, setSelectedSig] = React.useState('mosi');
  const waveWidth = 700;

  // ── Live VCD / hierarchy / trace state ──────────────────────────
  // When a real VCD is loaded via /api/vcd, we replace the mock trace
  // list with the parsed signals. Fall back to MOCK_TRACES when no
  // VCD has been picked yet so the panel never shows blank.
  const [vcdFiles, setVcdFiles] = React.useState([]);
  const [vcdActive, setVcdActive] = React.useState('');
  const [vcdData, setVcdData] = React.useState(null);   // {signals, samples, timeRange}
  const [hierarchy, setHierarchy] = React.useState(null);
  const [hierarchyError, setHierarchyError] = React.useState('');
  const [hierarchyMeta, setHierarchyMeta] = React.useState(null);
  // Top-level tab — full-width view selector. Replaces the old
  // chip-toggle on the right rail; the user picks which DEBUG MODE
  // to focus on and that mode takes the entire center space.
  //   wave      = source (collapsible) + waveform (the rest)
  //   hierarchy = full-width instance tree
  //   trace     = source + driver/sink list (full width)
  //   summary   = TC pass/fail table from SSOT scenarios + scoreboard
  const [topTab, setTopTab] = React.useState(initialTopTab); // summary | wave | hierarchy | trace | tb
  const [rightTab, setRightTab] = React.useState('wave'); // legacy, mirrors topTab
  React.useEffect(() => { setRightTab(topTab); }, [topTab]);
  const [ipName, setIpName] = React.useState('');
  const [rtlTop, setRtlTop] = React.useState('');

  // Auto-detect IP. Two parallel signals are checked:
  //   1) window.ACTIVE_IP / ACTIVE_SESSION — fires immediately on
  //      mount and keeps the panel correctly scoped even when no VCD
  //      has been generated yet (e.g. before /sim runs). Subscribes to
  //      backend session_state events so a workspace switch live-flips
  //      the IP without a manual reload.
  //   2) /api/vcd/list?ip=<ip> — scoped to the active IP only.
  React.useEffect(() => {
    const seedFromActiveSession = () => {
      const activeIp = activeIpFromAtlasRuntime();
      if (activeIp) setIpName(activeIp);
    };
    seedFromActiveSession();
    if (!window.backend?.subscribe) return undefined;
    const subs = [];
    try {
      subs.push(window.backend.subscribe('session_state', seedFromActiveSession));
    } catch (_) {}
    return () => { subs.forEach(u => { try { u && u(); } catch (_) {} }); };
  }, []);

  React.useEffect(() => {
    let cancelled = false;
    const activeIp = String(ipName || activeIpFromAtlasRuntime()).trim();
    if (!activeIp || activeIp === 'default') {
      setVcdFiles([]);
      setVcdActive('');
      setVcdData(null);
      return () => { cancelled = true; };
    }
    (async () => {
      try {
        const r = await fetch('/api/vcd/list?ip=' + encodeURIComponent(activeIp));
        const d = await r.json();
        if (cancelled) return;
        const files = (d.files || []).filter(f => vcdPathBelongsToIp(f.path, activeIp));
        setVcdFiles(files);
        setVcdActive(prev => files.some(f => f.path === prev) ? prev : (files[0]?.path || ''));
        if (!files.length) setVcdData(null);
      } catch (e) { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [ipName]);

  // Load + parse the active VCD whenever it changes.
  React.useEffect(() => {
    if (!vcdActive) return;
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch('/api/vcd/raw?path=' + encodeURIComponent(vcdActive));
        const d = await r.json();
        if (cancelled) return;
        if (d.content && window.parseVCD) {
          const parsed = window.parseVCD(d.content);
          setVcdData(parsed);
          const inferredTop = inferRtlTopFromVcd(parsed, '');
          if (inferredTop) setRtlTop(prev => prev || inferredTop);
          // Reset view to fit the whole VCD on parse.
          setViewRange(null);
          // Position cursors at sensible spots inside the actual VCD
          // span (25 % and 75 %). Avoids the previous hard-coded 110/160
          // ns which was meaningless for VCDs that don't cover that range.
          const [tMin, tMax] = parsed.timeRange;
          const span = tMax - tMin;
          if (span > 0) {
            setWaveCursor (Math.round(tMin + span * 0.25));
            setWaveCursorB(Math.round(tMin + span * 0.75));
          }
        }
      } catch (e) { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [vcdActive]);

  // Fetch cocotb env info whenever IP changes (used by left-panel TB tab).
  React.useEffect(() => {
    if (!ipName) { setCocotbData(null); return; }
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch('/api/cocotb?ip=' + encodeURIComponent(ipName));
        const d = await r.json();
        if (!cancelled) setCocotbData(d);
      } catch (_) { if (!cancelled) setCocotbData(null); }
    })();
    return () => { cancelled = true; };
  }, [ipName]);

  // Fetch TC pass/fail rollup for the Sim Summary tab. The backend
  // merges SSOT scenarios with scoreboard_events.jsonl, and also
  // includes scoreboard-only IDs so failed generated tests are not hidden.
  React.useEffect(() => {
    if (!ipName) {
      setSimSummary(null);
      setSimSummaryError('');
      setSimSummaryLoading(false);
      return;
    }
    let cancelled = false;
    setSimSummaryLoading(true);
    (async () => {
      try {
        const r = await fetch('/api/debug/scenarios?ip=' + encodeURIComponent(ipName), { cache: 'no-store' });
        const d = await r.json();
        if (cancelled) return;
        setSimSummary(d);
        setSimSummaryError(r.ok ? (d.error || '') : (d.error || `HTTP ${r.status}`));
      } catch (e) {
        if (!cancelled) {
          setSimSummary(null);
          setSimSummaryError(String(e));
        }
      } finally {
        if (!cancelled) setSimSummaryLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [ipName, simSummaryReload]);

  React.useEffect(() => {
    setRtlTop('');
  }, [ipName]);

  // Fetch hierarchy when IP is known. The UI is scoped by IP directory, but
  // elaboration must use the real RTL top from tb_manifest/SSOT/VCD scope.
  React.useEffect(() => {
    if (!ipName) return;
    let cancelled = false;
    (async () => {
      try {
        const topForHierarchy = rtlTop || ipName;
        const r = await fetch('/api/hierarchy?top=' + encodeURIComponent(topForHierarchy) +
                              '&ip=' + encodeURIComponent(ipName));
        const d = await r.json();
        if (cancelled) return;
        setHierarchyMeta(d);
        const resolvedTop = d?.resolved_top || d?.tree?.module || '';
        if (resolvedTop && resolvedTop !== rtlTop) setRtlTop(resolvedTop);
        if (d.tree) {
          setHierarchy(d.tree);
          setHierarchyError('');
        } else {
          setHierarchy(null);
          setHierarchyError(d.error || 'no hierarchy tree returned');
        }
      } catch (e) {
        if (!cancelled) {
          setHierarchy(null);
          setHierarchyMeta(null);
          setHierarchyError(String(e));
        }
      }
    })();
    return () => { cancelled = true; };
  }, [ipName, rtlTop]);

  const hierarchyBackendLabel = React.useMemo(() => {
    const backend = String(hierarchyMeta?.backend || '').trim();
    const primary = String(hierarchyMeta?.primary_backend || '').trim();
    const display = (backend === 'dual' || backend === 'pyslang+verilator')
      ? 'pyslang + verilator'
      : (backend || 'pyslang + verilator');
    const primarySuffix = primary ? ` (${primary})` : '';
    const topSuffix = rtlTop && rtlTop !== ipName ? ` · top ${rtlTop}` : '';
    return ipName ? `${display}${primarySuffix} · ${ipName}${topSuffix}` : `${display}${primarySuffix}`;
  }, [hierarchyMeta, ipName, rtlTop]);

  const hierarchyBackendTitle = React.useMemo(() => {
    const results = hierarchyMeta?.backend_results || [];
    if (!Array.isArray(results) || !results.length) return 'RTL hierarchy dual elaboration';
    return results.map(r => {
      const state = r.ok ? 'ok' : (r.error ? `error: ${r.error}` : 'no result');
      return `${r.backend}: ${state}`;
    }).join('\n');
  }, [hierarchyMeta]);

  // Build the traceList — real VCD signals only. Mock SPI traces
  // were dropped here per user request: the wave pane should never
  // show fake data. When no VCD has been parsed yet, return [] and
  // let the empty-state hint below ("no VCD found / run /sim") tell
  // the user how to get real signals on screen.
  const traceList = React.useMemo(() => {
    if (vcdData && vcdData.signals && vcdData.signals.length) {
      return vcdData.signals.slice(0, 24).map(s => ({
        name: s.name + (s.range || ''),
        signalName: s.name,
        scope: s.scope,
        // VCD samples come keyed by ID — re-key by display name for
        // WaveRow which expects [time, value] arrays.
        trace: vcdData.samples[s.id] || [],
        isBus: s.isBus,
        radix: s.isBus ? 'HEX' : undefined,
      }));
    }
    return [];
  }, [vcdData]);

  // Tool-call activations: clicking one in chat re-focuses the side panels.
  const onToolFocus = (toolId, opts) => {
    setActiveTool(toolId);
    if (opts.cursor != null) setWaveCursor(opts.cursor);
    if (opts.range) setSrcRange(opts.range);
    if (opts.sig) setSelectedSig(opts.sig);
  };

  // Compact step block — like V3's but lighter, since panels carry the evidence.
  const Step4 = ({ num, kind, tag, when, title, args, body, done, onClick, active }) => {
    const dotColor = {
      thought: 'var(--magenta)',
      tool:    'var(--cyan)',
      action:  'var(--accent)',
      obs:     'var(--ok)',
    }[kind] || 'var(--fg-mute)';
    return (
      <div
        onClick={onClick}
        style={{
          display: 'grid',
          gridTemplateColumns: '32px 1fr',
          gap: 12,
          marginBottom: 14,
          cursor: onClick ? 'pointer' : 'default',
          padding: '6px 8px',
          borderRadius: 4,
          background: active ? 'color-mix(in oklch, var(--cyan) 8%, transparent)' : 'transparent',
          border: active ? '1px solid color-mix(in oklch, var(--cyan) 30%, var(--line))' : '1px solid transparent',
          transition: 'background 0.15s, border-color 0.15s',
        }}
      >
        <div style={{ position: 'relative', textAlign: 'center' }}>
          <div style={{
            width: 22, height: 22, borderRadius: '50%',
            background: 'var(--panel)',
            border: '1.5px solid ' + dotColor,
            color: dotColor,
            fontFamily: 'var(--mono)', fontSize: 9, fontWeight: 700,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '2px auto 0',
          }}>{num}</div>
          <div style={{
            position: 'absolute', left: '50%', top: 26, bottom: -14,
            width: 1, background: 'var(--line)', transform: 'translateX(-0.5px)',
          }} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
            <span style={{
              color: dotColor,
              fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase',
              fontWeight: 700, fontFamily: 'var(--mono)',
            }}>{tag}</span>
            {done && <span className="pill ok" style={{ fontSize: 8, padding: '0 4px' }}>done</span>}
            <span style={{ flex: 1 }} />
            <span style={{ color: 'var(--fg-mute)', fontSize: 9, fontFamily: 'var(--mono)' }}>{when}</span>
          </div>
          <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 500, marginBottom: 3, lineHeight: 1.35 }}>
            {title}
          </div>
          {args && (
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 4 }}>
              ({args})
            </div>
          )}
          {body}
        </div>
      </div>
    );
  };


  // ── Resizable splitter state ─────────────────────────────────────
  // The user can drag boundaries between hierarchy / source / wave / chat.
  // Double-click each splitter handle to collapse/restore its panel.
  // Expand-mode buttons (only-source / only-wave) hide the other panes
  // entirely.
  const [leftW, setLeftW] = React.useState(220);   // hierarchy column width
  const [rightW, setRightW] = React.useState(320); // chat rail width
  const [topH, setTopH] = React.useState(0.32);    // source band height as fraction of body
  const [expand, setExpand] = React.useState('split'); // split | wave | source | hierarchy

  // ── Zoom helpers ─────────────────────────────────────────────────
  // Effective visible time window. When viewRange is null we fall back
  // to the full VCD timeRange. tToX() in debug-shared.jsx reads from
  // window.WAVE_TIME_START/END so we mirror the effective range there
  // every render.
  const effRange = React.useMemo(() => {
    if (viewRange) return viewRange;
    if (vcdData) return [vcdData.timeRange[0], vcdData.timeRange[1]];
    return [0, 200];
  }, [viewRange, vcdData]);

  // Sync the window-scoped time range BEFORE children render, so
  // tToX() in debug-shared.jsx reads the up-to-date view on every
  // zoom. Doing this in useEffect would be one paint behind.
  if (typeof window !== 'undefined') {
    window.WAVE_TIME_START = effRange[0];
    window.WAVE_TIME_END   = effRange[1];
  }

  const zoomIn  = React.useCallback(() => {
    const [s, e] = effRange;
    const span = e - s;
    const center = (waveCursor != null && waveCursor >= s && waveCursor <= e) ? waveCursor : (s + e) / 2;
    const ns = Math.max(s, center - span * 0.25);
    const ne = Math.min(e, center + span * 0.25);
    if (ne - ns < 1) return;
    setViewRange([ns, ne]);
  }, [effRange, waveCursor]);

  const zoomOut = React.useCallback(() => {
    if (!vcdData) return;
    const [s, e] = effRange;
    const span = e - s;
    const center = (s + e) / 2;
    const [vs, ve] = vcdData.timeRange;
    const ns = Math.max(vs, center - span);
    const ne = Math.min(ve, center + span);
    if (ns === vs && ne === ve) { setViewRange(null); return; }
    setViewRange([ns, ne]);
  }, [effRange, vcdData]);

  const zoomFit = React.useCallback(() => setViewRange(null), []);

  const zoomToCursors = React.useCallback(() => {
    const a = Math.min(waveCursor, waveCursorB);
    const b = Math.max(waveCursor, waveCursorB);
    if (b - a < 1) return;
    const pad = (b - a) * 0.1;
    setViewRange([a - pad, b + pad]);
  }, [waveCursor, waveCursorB]);

  // Pan left/right by 25 % of the current window. Clamped to the full
  // VCD range. Used by Arrow keys and the (future) drag-to-pan handler.
  const panBy = React.useCallback((fraction) => {
    if (!vcdData) return;
    const [s, e] = effRange;
    const span = e - s;
    const delta = span * fraction;
    const [vs, ve] = vcdData.timeRange;
    let ns = s + delta;
    let ne = e + delta;
    if (ns < vs) { ne += vs - ns; ns = vs; }
    if (ne > ve) { ns -= ne - ve; ne = ve; }
    setViewRange([Math.max(vs, ns), Math.min(ve, ne)]);
  }, [effRange, vcdData]);

  const jumpToWaveEdge = React.useCallback((edgeTime) => {
    const t = Math.round(Number(edgeTime));
    if (!Number.isFinite(t)) return;
    setWaveCursorB(t);

    const [s, e] = effRange;
    if (t >= s && t <= e) return;

    const span = Math.max(1, e - s);
    const [vs, ve] = vcdData ? vcdData.timeRange : [s, e];
    let ns = t - span / 2;
    let ne = t + span / 2;
    if (ns < vs) { ne += vs - ns; ns = vs; }
    if (ne > ve) { ns -= ne - ve; ne = ve; }
    ns = Math.max(vs, ns);
    ne = Math.min(ve, ne);
    if (ns <= vs && ne >= ve) setViewRange(null);
    else setViewRange([ns, ne]);
  }, [effRange, vcdData]);

  // ── Keyboard shortcuts (Verdi-ish) ───────────────────────────────
  // Active only while sim_debug has focus AND user isn't typing in
  // an input/textarea/contenteditable.
  React.useEffect(() => {
    const onKey = (e) => {
      if (!vcdData) return;
      const tag = (e.target && e.target.tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || (e.target && e.target.isContentEditable)) return;
      // Don't fight chord shortcuts the IDE may use.
      if (e.metaKey && e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;

      let handled = true;
      switch (e.key) {
        case '+': case '=':
          zoomIn(); break;
        case '-': case '_':
          zoomOut(); break;
        case 'f': case 'F':
          zoomFit(); break;
        case 'a': case 'A':
          zoomToCursors(); break;
        case 'ArrowLeft':
          panBy(e.shiftKey ? -0.5 : -0.25); break;
        case 'ArrowRight':
          panBy(e.shiftKey ? 0.5 : 0.25); break;
        case 'Home':
          if (vcdData) setViewRange([vcdData.timeRange[0], vcdData.timeRange[0] + (effRange[1] - effRange[0])]);
          break;
        case 'End':
          if (vcdData) {
            const span = effRange[1] - effRange[0];
            setViewRange([vcdData.timeRange[1] - span, vcdData.timeRange[1]]);
          }
          break;
        case '?':
          setShowHelp(h => !h); break;
        case 'Escape':
          if (showHelp) setShowHelp(false); else handled = false;
          break;
        default:
          handled = false;
      }
      if (handled) e.preventDefault();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [vcdData, effRange, zoomIn, zoomOut, zoomFit, zoomToCursors, panBy]);

  // ── Source viewer state ──────────────────────────────────────────
  // Replaces the hard-coded mock srcRange. When the user clicks a
  // module in the hierarchy, we fetch <ip>/rtl/<module>.sv via
  // /api/source. When they click a signal in the wave panel, we hit
  // /api/trace first to resolve driver file:line, then fetch that file
  // and scroll to that line.
  const [srcLines, setSrcLines] = React.useState([]);   // string[] (full file)
  const [srcPath, setSrcPath]   = React.useState('');
  const [srcCursor, setSrcCursor] = React.useState(0);  // 1-based line; 0 = none
  const [srcModule, setSrcModule] = React.useState(''); // for hierarchy highlight
  const [srcLoading, setSrcLoading] = React.useState(false);

  const loadSourceFile = React.useCallback(async (path, cursorLine) => {
    if (!path) return;
    setSrcLoading(true);
    try {
      const r = await fetch('/api/source?path=' + encodeURIComponent(path));
      const d = await r.json();
      if (d && Array.isArray(d.lines)) {
        setSrcLines(d.lines);
        setSrcPath(path);
        setSrcCursor(cursorLine || 0);
      } else if (d && d.error) {
        setSrcLines([`// ${d.error}`, `// path: ${path}`]);
        setSrcPath(path);
        setSrcCursor(0);
      }
    } catch (e) {
      setSrcLines([`// fetch failed: ${e}`]);
    } finally {
      setSrcLoading(false);
    }
  }, []);

  // Hierarchy click → load the SV file that ACTUALLY defines the
  // module. Uses ONLY the elaborator's `module_files` map. No filename
  // convention fallback — that picks empty stubs (e.g. `gpio_pad.sv`)
  // when the real implementation lives in `gpio_pad_wrapper.sv`. If
  // elab fails, surface the error rather than guessing.
  const onSelectModule = React.useCallback((moduleName, instancePath) => {
    if (!moduleName || !ipName) return;
    setSrcModule(moduleName);
    (async () => {
      try {
        const r = await fetch('/api/hierarchy?top=' + encodeURIComponent(rtlTop || ipName) +
                              '&ip=' + encodeURIComponent(ipName));
        const d = await r.json();
        if (d?.error) {
          setSrcLines([`// elab error: ${d.error}`,
                       `// backend: ${d.backend || '?'}`]);
          setSrcPath('');
          return;
        }
        const mf = d?.module_files?.[moduleName];
        if (!mf || !mf.file) {
          setSrcLines([`// module '${moduleName}' not found in elab output`,
                       `// known: ${Object.keys(d?.module_files || {}).join(', ') || '(none)'}`,
                       `// backend: ${d?.backend || '?'}`]);
          setSrcPath('');
          return;
        }
        // file may already be relative (including nested trees such as
        // gpio/<ip>/rtl/...). Preserve that exact backend path so
        // /api/source opens the same file the elaborator used.
        const rel = normalizeProjectSourcePath(mf.file);
        await loadSourceFile(rel, mf.line);
      } catch (e) {
        setSrcLines([`// hierarchy fetch failed: ${e}`]);
        setSrcPath('');
      }
    })();
  }, [ipName, rtlTop, loadSourceFile]);

  // Wave signal click → /api/trace returns driver file_line; fetch + scroll.
  const onSelectWaveSignal = React.useCallback(async (signalName, signalScope = '') => {
    setSelectedSig(signalName);
    if (!signalName || !ipName) return;
    try {
      const r = await fetch(
        `/api/trace?signal=${encodeURIComponent(signalName)}` +
        `&top=${encodeURIComponent(rtlTop || ipName)}&ip=${encodeURIComponent(ipName)}` +
        (signalScope ? `&scope=${encodeURIComponent(signalScope)}` : ''));
      const d = await r.json();
      const drv = d && d.driver;
      if (drv && drv.file_line) {
        // file_line is "<path>:<line>" — keep the backend path intact
        // after stripping only a local PROJECT_ROOT prefix.
        const m = String(drv.file_line).match(/^(.*):(\d+)$/);
        if (m) {
          const relPath = normalizeProjectSourcePath(m[1]);
          const lineNo = parseInt(m[2], 10);
          await loadSourceFile(relPath, lineNo);
        }
      }
    } catch (e) { /* trace failed; keep current source */ }
  }, [ipName, rtlTop, loadSourceFile]);

  const sourceVcdAnnotations = React.useMemo(() => {
    if (!showVcdAnnotations || srcCursor <= 0 || !srcLines.length) return {};
    const items = buildVcdLineAnnotations({
      line: srcLines[srcCursor - 1] || '',
      traceList,
      selectedSig,
      cursorA: waveCursor,
      cursorB: waveCursorB,
    });
    return items.length ? { [srcCursor]: items } : {};
  }, [showVcdAnnotations, srcCursor, srcLines, traceList, selectedSig, waveCursor, waveCursorB]);

  // Auto-load top module source the first time hierarchy resolves.
  React.useEffect(() => {
    if (hierarchy && hierarchy.module && !srcPath && !srcLoading) {
      onSelectModule(hierarchy.module, hierarchy.name);
    }
  }, [hierarchy, srcPath, srcLoading, onSelectModule]);

  // ── Live chat (backend WS) state ─────────────────────────────────
  // Hooks the right-rail "chat · trace · debug · ask" panel into the
  // existing ATLAS WS bridge. Send goes to /ws/agent as a 'prompt';
  // streamed tokens append to the in-flight assistant entry; flush /
  // agent_state(false) park the buffer as a finished feed entry.
  const [chatFeed, setChatFeed] = React.useState([]);   // [{kind:'user'|'agent'|'thought'|'sys', text, ts}]
  const [chatInput, setChatInput] = React.useState('');
  const [chatStreaming, setChatStreaming] = React.useState(false);
  const _streamBuf = React.useRef('');
  const _chatScrollRef = React.useRef(null);

  React.useEffect(() => {
    if (!window.backend) return;
    const subs = [];
    subs.push(window.backend.subscribe('token', (m) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      const t = m.text || '';
      if (!t || t === '\x00') return;
      _streamBuf.current += t;
      setChatFeed(f => {
        const last = f[f.length - 1];
        if (last && last.kind === 'agent_stream') {
          return [...f.slice(0, -1), { ...last, text: _streamBuf.current }];
        }
        return [...f, { kind: 'agent_stream', text: _streamBuf.current, ts: Date.now() }];
      });
    }));
    subs.push(window.backend.subscribe('reasoning', (m) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      const t = (m.text || '').trim(); if (!t) return;
      setChatFeed(f => {
        const last = f[f.length - 1];
        if (last && last.kind === 'thought') {
          return [...f.slice(0, -1), { ...last, text: last.text + '\n' + t }];
        }
        return [...f, { kind: 'thought', text: t, ts: Date.now() }];
      });
    }));
    const park = () => {
      const buf = _streamBuf.current;
      if (buf.trim()) {
        setChatFeed(f => {
          // Promote agent_stream → agent (final).
          const last = f[f.length - 1];
          if (last && last.kind === 'agent_stream') {
            return [...f.slice(0, -1), { kind: 'agent', text: buf, ts: Date.now() }];
          }
          return [...f, { kind: 'agent', text: buf, ts: Date.now() }];
        });
      }
      _streamBuf.current = '';
    };
    subs.push(window.backend.subscribe('flush', (m) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      park();
    }));
    subs.push(window.backend.subscribe('done', (m) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      park(); setChatStreaming(false);
    }));
    subs.push(window.backend.subscribe('agent_state', (m) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      if (m.running === false) { park(); setChatStreaming(false); }
      else if (m.running === true) setChatStreaming(true);
    }));
    subs.push(window.backend.subscribe('slash_output', (m) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      const t = m.text || ''; if (!t) return;
      // de-dupe vs streaming buffer
      if (_streamBuf.current && _streamBuf.current.indexOf(t) >= 0) return;
      setChatFeed(f => [...f, { kind: 'agent', text: t, ts: Date.now() }]);
      _streamBuf.current = '';
    }));
    subs.push(window.backend.subscribe('error', (m) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      setChatFeed(f => [...f, { kind: 'sys', text: `[error] ${m.message || ''}`, ts: Date.now() }]);
      setChatStreaming(false);
    }));
    return () => subs.forEach(u => u && u());
  }, []);

  React.useEffect(() => {
    // auto-scroll chat to bottom on new entries
    const el = _chatScrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [chatFeed.length]);

  // Local intent dispatcher — recognizes `/trace <sig>`, `/hier <mod>`,
  // `/wave <path>` etc. and runs them entirely client-side (drives wave
  // panel + source viewer) without paying for an LLM round trip. Only
  // unrecognized input falls through to the backend agent.
  const sendChat = async (text) => {
    const raw = (text != null ? text : chatInput).trim();
    if (!raw) return;
    setChatFeed(f => [...f, { kind: 'user', text: raw, ts: Date.now() }]);
    setChatInput('');

    // ── Intent: trace a signal → focus wave + load driver source ──
    const mTrace = raw.match(/^\/?trace\s+([A-Za-z_][\w.\[\]:]*)\b/i);
    if (mTrace) {
      const sig = mTrace[1];
      setChatFeed(f => [...f, {
        kind: 'sys',
        text: `→ tracing ${sig} (focus wave + driver source)`,
        ts: Date.now(),
      }]);
      // Fire wave focus + /api/trace lookup. onSelectWaveSignal already
      // sets selectedSig, fetches /api/trace, then loads the driver file
      // at the right line.
      try {
        await onSelectWaveSignal(sig);
        // Re-fetch /api/trace to print a summary in the chat.
        const activeTop = rtlTop || ipName || sig.split('.')[0] || '';
        const activeIp = ipName || activeTop;
        const r = await fetch(
          `/api/trace?signal=${encodeURIComponent(sig)}` +
          `&top=${encodeURIComponent(activeTop)}` +
          `&ip=${encodeURIComponent(activeIp)}`);
        const d = await r.json();
        const drv = d?.driver;
        const sinks = d?.sinks || [];
        const lines = [];
        if (drv) lines.push(`driver: ${drv.kind}  @ ${drv.file_line}`);
        else     lines.push(`driver: not found (signal '${sig}' may be a port or constant)`);
        if (sinks.length) {
          lines.push(`sinks (${sinks.length}):`);
          sinks.slice(0, 8).forEach(s => lines.push(`  · ${s.context} ${s.access || ''} @ ${s.file_line}`));
        }
        setChatFeed(f => [...f, { kind: 'agent', text: lines.join('\n'), ts: Date.now() }]);
      } catch (e) {
        setChatFeed(f => [...f, { kind: 'sys', text: `[trace error] ${e}`, ts: Date.now() }]);
      }
      return;
    }

    // ── Intent: hierarchy of a top module ──
    const mHier = raw.match(/^\/?hier\s+([A-Za-z_]\w*)/i);
    if (mHier) {
      const mod = mHier[1];
      setChatFeed(f => [...f, { kind: 'sys', text: `→ loading hierarchy + source for ${mod}`, ts: Date.now() }]);
      onSelectModule(mod, mod);
      try {
        const r = await fetch(
          `/api/hierarchy?top=${encodeURIComponent(mod)}` +
          `&ip=${encodeURIComponent(ipName || mod)}`);
        const d = await r.json();
        const tree = d?.tree;
        const flatten = (n, depth) => {
          if (!n) return [];
          const out = ['  '.repeat(depth) + (n.name || mod) + ' :: ' + (n.module || '')];
          (n.children || []).forEach(c => out.push(...flatten(c, depth + 1)));
          return out;
        };
        setChatFeed(f => [...f, {
          kind: 'agent',
          text: tree ? flatten(tree, 0).join('\n') : (d?.error || 'no tree'),
          ts: Date.now(),
        }]);
      } catch (e) {
        setChatFeed(f => [...f, { kind: 'sys', text: `[hier error] ${e}`, ts: Date.now() }]);
      }
      return;
    }

    // ── Intent: jump to source line ──  /goto <file>:<line>
    const mGoto = raw.match(/^\/?goto\s+([^\s:]+):(\d+)/i);
    if (mGoto) {
      const path = mGoto[1];
      const line = parseInt(mGoto[2], 10);
      setChatFeed(f => [...f, { kind: 'sys', text: `→ source ${path}:${line}`, ts: Date.now() }]);
      loadSourceFile(path, line);
      return;
    }

    // ── Intent: open a VCD ──  /wave <path>
    const mWave = raw.match(/^\/?wave\s+(\S+)/i);
    if (mWave) {
      setChatFeed(f => [...f, { kind: 'sys', text: `→ loading VCD ${mWave[1]}`, ts: Date.now() }]);
      setVcdActive(mWave[1]);
      return;
    }

    // ── Fallback: send to backend agent (natural-language Q&A) ──
    if (!window.backend) return;
    setChatStreaming(true);
    _streamBuf.current = '';
    window.backend.send({ type: 'prompt', text: raw });
  };

  const _drag = React.useRef(null);
  const startDrag = (kind) => (e) => {
    e.preventDefault();
    _drag.current = { kind, startX: e.clientX, startY: e.clientY,
                      leftW, rightW, topH,
                      bodyH: e.currentTarget.parentElement?.parentElement?.clientHeight || 600 };
    const onMove = (ev) => {
      const d = _drag.current; if (!d) return;
      if (d.kind === 'left') {
        const w = Math.max(0, Math.min(560, d.leftW + (ev.clientX - d.startX)));
        setLeftW(w);
      } else if (d.kind === 'right') {
        const w = Math.max(0, Math.min(640, d.rightW - (ev.clientX - d.startX)));
        setRightW(w);
      } else if (d.kind === 'topH') {
        const next = Math.max(0.08, Math.min(0.92, d.topH + (ev.clientY - d.startY) / d.bodyH));
        setTopH(next);
      }
    };
    const onUp = () => {
      _drag.current = null;
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  // Effective dimensions after expand mode.
  const eff = (() => {
    if (expand === 'wave')      return { lw: 0,     rw: 0,      th: 0,    showSource: false, showWave: true,  showHier: false, showChat: false };
    if (expand === 'source')    return { lw: 0,     rw: 0,      th: 1.0,  showSource: true,  showWave: false, showHier: false, showChat: false };
    if (expand === 'hierarchy') return { lw: leftW || 320, rw: 0, th: 0, showSource: false, showWave: false, showHier: true, showChat: false };
    return { lw: leftW, rw: rightW, th: topH, showSource: true, showWave: true, showHier: leftW > 0, showChat: rightW > 0 };
  })();

  const ExpandBtn = ({ id, glyph, title }) => (
    <button
      onClick={() => setExpand(expand === id ? 'split' : id)}
      title={title}
      style={{
        background: expand === id ? 'var(--accent)' : 'transparent',
        color: expand === id ? 'var(--bg)' : 'var(--fg-mute)',
        border: '1px solid var(--line)', borderRadius: 3,
        padding: '1px 6px', fontSize: 'var(--ui-control-font-size)', cursor: 'pointer',
        fontFamily: 'var(--mono)', marginLeft: 4,
      }}
    >{glyph}</button>
  );

  const selectTopTab = (id) => {
    setTopTab(id);
    if (id === 'hierarchy') {
      setLeftTab('rtl');
      setExpand('hierarchy');
    } else if (id === 'tb') {
      setLeftTab('tb');
      setExpand('split');
    } else if (id === 'wave' || id === 'trace') {
      setExpand('split');
    }
  };

  const ModeBtn = ({ id, label, title }) => (
    <button
      onClick={() => selectTopTab(id)}
      title={title || label}
      style={{
        background: topTab === id ? 'var(--accent)' : 'transparent',
        color: topTab === id ? 'var(--bg)' : 'var(--fg-mute)',
        border: '1px solid var(--line)', borderRadius: 3,
        padding: '2px 8px', fontSize: 10, cursor: 'pointer',
        fontFamily: 'var(--mono)', fontWeight: 800,
        letterSpacing: '0.06em', textTransform: 'uppercase',
      }}
    >{label}</button>
  );

  const Splitter = ({ orient, onMouseDown, onDoubleClick }) => (
    <div
      onMouseDown={onMouseDown}
      onDoubleClick={onDoubleClick}
      style={{
        background: 'var(--line)',
        cursor: orient === 'v' ? 'col-resize' : 'row-resize',
        flexShrink: 0,
        ...(orient === 'v' ? { width: 4, height: '100%' } : { height: 4, width: '100%' }),
      }}
    />
  );

  const bodyGridColumns = expand === 'hierarchy'
    ? '1fr 0 0 0 0'
    : `${eff.showHier ? eff.lw + 'px' : '0'} ${eff.showHier && eff.lw > 0 ? '4px' : '0'} 1fr ${eff.showChat && eff.rw > 0 ? '4px' : '0'} ${eff.showChat ? eff.rw + 'px' : '0'}`;

  return (
    <div className="atlas-frame" style={{
      display: 'flex', flexDirection: 'column',
      flex: 1, width: '100%', height: '100%',
      minWidth: 0, minHeight: 0,
    }}>
      <window.AtlasTitle
        // Resolve the active workspace IP — prefer the SimDebug-local
        // ipName (set when a VCD is found), otherwise the live
        // window.ACTIVE_SESSION's middle segment (default/<ip>/<wf>).
        // The hardcoded "spi_master/" fallback inside AtlasTitle is
        // gone now; passing an empty string still falls back to that
        // legacy default for first-paint.
        workspace={
          ipName ||
          (String(window.ACTIVE_SESSION || '').split('/').filter(Boolean)[1]) ||
          ''
        }
        subtitle={'sim_debug · ' + (vcdActive ? vcdActive.split('/').pop() : 'no VCD')}
        right={
          <span className="agent-chip">
            <span className="pulse" /> Atlas · debug session
          </span>
        }
      />

      {/* Single unified header — VCD picker + cursor controls + expand mode */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '6px 14px', borderBottom: '1px solid var(--line)',
        background: 'var(--bg-2)', fontSize: 'var(--ui-control-font-size)', flexShrink: 0,
      }}>
        <span style={{ color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>MODE</span>
        {summaryOnly ? (
          <span className="pill" style={{
            fontSize: 10, padding: '2px 8px',
            background: 'color-mix(in oklch, var(--accent) 14%, transparent)',
            color: 'var(--accent)',
            border: '1px solid color-mix(in oklch, var(--accent) 40%, var(--line))',
            borderRadius: 3,
            fontFamily: 'var(--mono)', fontWeight: 800,
            letterSpacing: '0.06em', textTransform: 'uppercase',
          }}>
            Sim Summary
          </span>
        ) : (
          <>
            <ModeBtn id="wave" label="Wave" title="source + waveform" />
            <ModeBtn id="hierarchy" label="RTL" title="RTL hierarchy" />
            <ModeBtn id="tb" label="TB" title="TB hierarchy and cocotb files" />
          </>
        )}
        <span style={{ color: 'var(--line-2)', margin: '0 4px' }}>│</span>
        <span style={{ color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>VCD</span>
        <select
          value={vcdActive}
          onChange={e => setVcdActive(e.target.value)}
          style={{
            background: 'var(--bg)', color: 'var(--fg)', border: '1px solid var(--line)',
            padding: '3px 6px', fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', minWidth: 280,
          }}
        >
          {!vcdFiles.length && <option value="">(no VCD found — run /sim)</option>}
          {vcdFiles.map(f => (
            <option key={f.path} value={f.path}>{f.path}</option>
          ))}
        </select>
        {vcdData && (
          <span className="pill" style={{
            fontSize: 10, padding: '2px 8px',
            background: 'color-mix(in oklch, var(--ok) 18%, transparent)',
            color: 'var(--ok)',
            border: '1px solid color-mix(in oklch, var(--ok) 30%, var(--line))',
            borderRadius: 3,
          }}>
            ✓ {vcdData.signals.length} sig · t={vcdData.timeRange[0]}–{vcdData.timeRange[1]} {vcdData.timescale}
          </span>
        )}
        {!summaryOnly && (
          <>
            <span style={{ color: 'var(--line-2)', margin: '0 4px' }}>│</span>
            <span style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>cur A</span>
            <span style={{ color: 'var(--accent)', fontWeight: 600, fontFamily: 'var(--mono)' }}>{waveCursor}ns</span>
            <span style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>B</span>
            <span style={{ color: 'var(--cyan)', fontWeight: 600, fontFamily: 'var(--mono)' }}>{waveCursorB}ns</span>
            <span style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Δ</span>
            <span style={{ color: 'var(--magenta)', fontWeight: 600, fontFamily: 'var(--mono)' }}>{waveCursorB - waveCursor}ns</span>
          </>
        )}
        <span style={{ flex: 1 }} />
        {!summaryOnly && (
          <>
            <span style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase' }}>expand</span>
            <ExpandBtn id="hierarchy" glyph="◧"   title="hierarchy only" />
            <ExpandBtn id="source"    glyph="◨"   title="source only"    />
            <ExpandBtn id="wave"      glyph="▣"   title="wave only"      />
            <ExpandBtn id="split"     glyph="⊞"   title="split (default)" />
          </>
        )}
      </div>

      {summaryOnly || topTab === 'summary' ? (
        <SimSummaryPanel
          ipName={ipName}
          data={simSummary}
          loading={simSummaryLoading}
          error={simSummaryError}
          cocotbData={cocotbData}
          onOpenFile={(p, line) => {
            loadSourceFile(p, line || 0);
            if (!summaryOnly) {
              setTopTab('wave');
              setExpand('split');
            }
          }}
          onRefresh={() => setSimSummaryReload(v => v + 1)}
        />
      ) : (
      <div style={{
        display: 'grid',
        gridTemplateColumns: bodyGridColumns,
        flex: 1, minHeight: 0, overflow: 'hidden',
      }}>
        {/* LEFT — hierarchy panel */}
        {eff.showHier && (
          <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--panel)', borderRight: '1px solid var(--line)' }}>
            <div className="mini-h" style={{ display: 'flex', alignItems: 'center' }}>
              <button
                onClick={() => setLeftTab('rtl')}
                style={{
                  background: leftTab === 'rtl' ? 'var(--accent)' : 'transparent',
                  color:      leftTab === 'rtl' ? 'var(--bg)'     : 'var(--fg-mute)',
                  border: '1px solid var(--line)', borderRadius: 3,
                  padding: '1px 8px', fontSize: 10, cursor: 'pointer',
                  fontFamily: 'var(--mono)', fontWeight: 700,
                  marginRight: 4,
                }}
                title="RTL hierarchy (verilator/pyslang elab)"
              >RTL</button>
              <button
                onClick={() => setLeftTab('tb')}
                style={{
                  background: leftTab === 'tb' ? 'var(--accent)' : 'transparent',
                  color:      leftTab === 'tb' ? 'var(--bg)'     : 'var(--fg-mute)',
                  border: '1px solid var(--line)', borderRadius: 3,
                  padding: '1px 8px', fontSize: 10, cursor: 'pointer',
                  fontFamily: 'var(--mono)', fontWeight: 700,
                }}
                title="cocotb testbench environment"
              >TB{cocotbData && cocotbData.exists ? '' : ' ⊘'}</button>
              <span style={{ color: 'var(--fg-mute)', marginLeft: 8, fontSize: 10 }}>
                {leftTab === 'rtl'
                  ? (
                    <span title={hierarchyBackendTitle}>{hierarchyBackendLabel}</span>
                  )
                  : (cocotbData?.exists ? `cocotb · ${ipName}` : 'cocotb (none)')}
              </span>
              <span style={{ flex: 1 }} />
            </div>
            {leftTab === 'tb' ? (
              <CocotbTreeView
                data={cocotbData}
                ipName={ipName}
                onOpenFile={(p, line) => loadSourceFile(p, line || 0)}
              />
            ) : (
            <div style={{ flex: 1, overflow: 'auto', padding: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
              {hierarchy ? (
                <HierarchyNode node={hierarchy} depth={0}
                  onSelectModule={onSelectModule}
                  activeModule={srcModule} />
              ) : (
                <div style={{ color: 'var(--fg-mute)', padding: 8 }}>
                  No RTL hierarchy yet.<br />
                  {hierarchyError ? (
                    <span style={{ color: 'var(--err)' }}>{hierarchyError}</span>
                  ) : (
                    <span>Pick a workspace IP to elaborate.</span>
                  )}
                </div>
              )}
              {vcdData && vcdData.signals && vcdData.signals.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4 }}>
                    signals ({vcdData.signals.length})
                  </div>
                  {vcdData.signals.slice(0, 30).map(s => (
                    <div
                      key={s.id}
                      onClick={() => onSelectWaveSignal(s.name, s.scope)}
                      style={{
                        padding: '2px 4px', cursor: 'pointer',
                        color: selectedSig === s.name ? 'var(--accent)' : 'var(--fg)',
                        background: selectedSig === s.name ? 'var(--bg-2)' : 'transparent',
                      }}
                    >
                      <span style={{ color: 'var(--fg-mute)' }}>·</span> {s.name}
                      {s.isBus && <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}> {s.range}</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
            )}
          </div>
        )}
        {eff.showHier && eff.lw > 0 && (
          <Splitter orient="v"
            onMouseDown={startDrag('left')}
            onDoubleClick={() => setLeftW(leftW > 0 ? 0 : 220)}
          />
        )}

        {/* CENTER — source (top) + wave (bottom), vertically split */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
          {/* SOURCE band */}
          {eff.showSource && (
            <div style={{
              flex: eff.showWave ? `${Math.round(eff.th * 100)} ${Math.round(eff.th * 100)} 0` : '1 1 0',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
              background: 'var(--panel)',
            }}>
              <div className="mini-h" style={{ display: 'flex', alignItems: 'center' }}>
                <b>source</b>
                <span style={{ color: 'var(--cyan)', marginLeft: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
                  {srcPath || `(click hierarchy module or wave signal)`}
                </span>
                <span style={{ flex: 1 }} />
                {srcLoading && <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>loading…</span>}
                {srcCursor > 0 && (
                  <span style={{ color: 'var(--accent)', fontSize: 10 }}>L{srcCursor}</span>
                )}
                <button
                  className="btn"
                  onClick={() => setShowVcdAnnotations(v => !v)}
                  title="toggle VCD values under the active source line"
                  style={{
                    padding: '1px 8px',
                    fontSize: 10,
                    fontWeight: 700,
                    marginLeft: 8,
                    background: showVcdAnnotations ? 'var(--accent)' : undefined,
                    color: showVcdAnnotations ? '#000' : undefined,
                  }}
                >
                  annot {showVcdAnnotations ? 'on' : 'off'}
                </button>
              </div>
              <SourceViewer
                lines={srcLines}
                cursor={srcCursor}
                path={srcPath}
                vcdAnnotations={sourceVcdAnnotations}
              />
            </div>
          )}
          {/* Source ↔ Wave splitter */}
          {eff.showSource && eff.showWave && (
            <Splitter orient="h"
              onMouseDown={startDrag('topH')}
              onDoubleClick={() => setTopH(0.32)}
            />
          )}

          {/* WAVE band — wrap in .wave-panel for Verdi-style dark canvas
              + sharp signal colors (defined in styles.css). */}
          {eff.showWave && (
            <div className="wave-panel" style={{
              flex: eff.showSource ? `${Math.round((1 - eff.th) * 100)} ${Math.round((1 - eff.th) * 100)} 0` : '1 1 0',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
              borderTop: eff.showSource ? '1px solid var(--line)' : 'none',
              position: 'relative',
            }}>
              {showHelp && (
                <div
                  onClick={() => setShowHelp(false)}
                  style={{
                    position: 'absolute', top: 0, right: 0, bottom: 0, left: 0,
                    background: 'rgba(0,0,0,0.78)', zIndex: 50,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                  <div onClick={e => e.stopPropagation()} style={{
                    background: '#0d1118',
                    border: '1px solid #ffd24d',
                    borderRadius: 6, padding: '14px 20px',
                    fontFamily: 'var(--mono)', fontSize: 12,
                    color: '#c8d2dc', minWidth: 460,
                    boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
                  }}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12,
                      borderBottom: '1px solid #2a3140', paddingBottom: 8,
                    }}>
                      <span style={{ color: '#ffd24d', fontWeight: 700, fontSize: 13, letterSpacing: '0.06em' }}>
                        WAVE SHORTCUTS
                      </span>
                      <span style={{ flex: 1 }} />
                      <span style={{ color: '#6c7888', fontSize: 10 }}>
                        press <b>?</b> or <b>Esc</b> to close
                      </span>
                    </div>
                    {[
                      { keys: ['+', '='], desc: 'zoom in (around cursor A)' },
                      { keys: ['−', '_'], desc: 'zoom out' },
                      { keys: ['f'],      desc: 'fit — show whole VCD' },
                      { keys: ['a'],      desc: 'zoom to cursor A↔B' },
                      { keys: ['←'],      desc: 'pan left  (Shift+← = bigger step)' },
                      { keys: ['→'],      desc: 'pan right (Shift+→ = bigger step)' },
                      { keys: ['Home'],   desc: 'go to t=0' },
                      { keys: ['End'],    desc: 'go to t=tMax' },
                      { keys: ['Ctrl/⌘ + wheel'], desc: 'zoom around cursor A' },
                      { keys: ['?'],      desc: 'toggle this help' },
                    ].map((row, i) => (
                      <div key={i} style={{
                        display: 'grid',
                        gridTemplateColumns: '160px 1fr',
                        padding: '4px 0', gap: 12,
                      }}>
                        <span style={{ display: 'flex', gap: 4 }}>
                          {row.keys.map((k, j) => (
                            <span key={j} style={{
                              background: '#1a2030',
                              border: '1px solid #4a5566',
                              borderBottom: '2px solid #4a5566',
                              borderRadius: 3, padding: '1px 6px',
                              color: '#ffd24d', fontWeight: 700,
                            }}>{k}</span>
                          ))}
                        </span>
                        <span style={{ color: '#c8d2dc' }}>{row.desc}</span>
                      </div>
                    ))}
                    <div style={{
                      marginTop: 12, paddingTop: 8,
                      borderTop: '1px solid #2a3140', color: '#6c7888',
                      fontSize: 10,
                    }}>
                      tip: shortcuts only fire when the wave panel has focus —
                      not while typing in chat or any input.
                    </div>
                  </div>
                </div>
              )}
              <div className="mini-h" style={{ display: 'flex', alignItems: 'center' }}>
                <b>waveform</b>
                <span style={{ color: 'var(--cyan)', marginLeft: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
                  {vcdActive ? vcdActive.split('/').pop() : '(none)'}
                </span>
                <span style={{ flex: 1 }} />
                {/* Editable range — type to jump. Two number inputs for
                    start/end. Plus a tiny tooltip with full range + zoom %. */}
                <RangeInput
                  effRange={effRange}
                  vcdData={vcdData}
                  setViewRange={setViewRange}
                />
                <button className="btn" style={{ padding: '1px 8px', fontSize: 'var(--ui-control-font-size)', marginRight: 2, fontWeight: 700 }}
                        onClick={zoomIn}    title="zoom in  (shortcut: + or =)">+</button>
                <button className="btn" style={{ padding: '1px 8px', fontSize: 'var(--ui-control-font-size)', marginRight: 2, fontWeight: 700 }}
                        onClick={zoomOut}   title="zoom out (shortcut: − or _)">−</button>
                <button className="btn" style={{ padding: '1px 6px', fontSize: 10, marginRight: 2 }}
                        onClick={() => panBy(-0.25)} title="pan left  (shortcut: ←)">◀</button>
                <button className="btn" style={{ padding: '1px 6px', fontSize: 10, marginRight: 2 }}
                        onClick={() => panBy(0.25)}  title="pan right (shortcut: →)">▶</button>
                <button className="btn" style={{ padding: '1px 8px', fontSize: 10, marginRight: 2 }}
                        onClick={zoomToCursors} title="zoom to A↔B (shortcut: a)">A↔B</button>
                <button className="btn" style={{ padding: '1px 8px', fontSize: 10, marginRight: 4 }}
                        onClick={zoomFit}   title="fit whole VCD (shortcut: f)">fit</button>
                <button className="btn"
                        onClick={() => setShowHelp(h => !h)}
                        title="show keyboard shortcuts (shortcut: ?)"
                        style={{
                          padding: '1px 8px', fontSize: 10, fontWeight: 700,
                          background: showHelp ? 'var(--accent)' : undefined,
                          color: showHelp ? '#000' : undefined,
                        }}>?</button>
              </div>
              <div
                style={{ flex: 1, overflow: 'auto', position: 'relative' }}
                onWheel={(e) => {
                  // Ctrl+wheel = zoom around cursor A. Plain wheel = scroll.
                  if (!e.ctrlKey && !e.metaKey) return;
                  e.preventDefault();
                  if (e.deltaY < 0) zoomIn(); else zoomOut();
                }}
              >
                <window.TimeRuler
                  width={waveWidth}
                  tMin={effRange[0]}
                  tMax={effRange[1]}
                  signals={traceList.length}
                  scope={ipName || 'scope'}
                  timescale={vcdData ? vcdData.timescale : 'ns'}
                />

                {/* Cursor strip — dedicated row that holds A/B labels and a
                    Δ readout. Keeps the cursor markers from overlapping the
                    signal rows the way they did before. */}
                <div style={{
                  position: 'sticky', top: 22, zIndex: 5,
                  display: 'grid',
                  gridTemplateColumns: '180px 90px 1fr',
                  height: 18,
                  borderBottom: '1px solid #2a3140',
                  background: '#0d1118',
                  fontFamily: 'var(--mono)', fontSize: 10,
                }}>
                  <span style={{
                    display: 'flex', alignItems: 'center',
                    padding: '0 10px', color: '#6c7888',
                    borderRight: '1px solid #161a22',
                    textTransform: 'uppercase', letterSpacing: '0.06em',
                  }}>cursors</span>
                  <span style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
                    padding: '0 10px', color: '#ffd24d', fontWeight: 700,
                    borderRight: '1px solid #161a22',
                  }}>Δ {waveCursorB - waveCursor}{vcdData ? vcdData.timescale : 'ns'}</span>
                  <div style={{ position: 'relative' }}>
                    {[
                      { time: waveCursor,  kind: 'A', color: '#ffb84d' },
                      { time: waveCursorB, kind: 'B', color: '#4dd0e1' },
                    ].map((c, i) => {
                      // Use the same tToX so the badge sits exactly above
                      // its vertical line. Hide if outside view.
                      const span = effRange[1] - effRange[0] || 1;
                      const x = ((c.time - effRange[0]) / span) * waveWidth;
                      if (x < 0 || x > waveWidth) return null;
                      return (
                        <span key={i} style={{
                          position: 'absolute', left: x, transform: 'translateX(-50%)',
                          top: 1, padding: '0 4px',
                          background: c.color, color: '#000',
                          borderRadius: 2, fontWeight: 700, fontSize: 10,
                          whiteSpace: 'nowrap',
                        }}>
                          {c.kind}={c.time}{vcdData ? vcdData.timescale : 'ns'}
                        </span>
                      );
                    })}
                  </div>
                </div>
                <div style={{ position: 'relative' }}>
                  {traceList.length === 0 && (
                    <div style={{
                      padding: '20px 16px',
                      color: 'var(--fg-mute)',
                      fontStyle: 'italic',
                      fontSize: 12,
                      lineHeight: 1.6,
                    }}>
                      {ipName ? (
                        <>
                          no VCD found for <code>{ipName}</code>.<br />
                          run <code>/sim</code> in chat to generate{' '}
                          <code>{ipName}/sim/{ipName}.vcd</code>, then this
                          panel will populate with real signals.
                        </>
                      ) : (
                        <>pick an IP from <code>IP_ID</code> to scope sim_debug.</>
                      )}
                    </div>
                  )}
                  {traceList.map((t, ti) => {
                    // Verdi-style color hint by name role.
                    const lname = (t.name || '').toLowerCase();
                    const isClock = /\b(clk|clock|sclk|pclk)\b/.test(lname);
                    const isReset = /\b(rst|reset|presetn|areset)\b/.test(lname);
                    const isIrq   = /\b(irq|int|intr)\b/.test(lname);
                    const color = isClock ? '#7CFC4D'      // bright green
                                : isReset ? '#7CFC4D'
                                : isIrq   ? '#ff6b6b'      // pink/red
                                : !t.isBus ? '#4dd0e1'      // cyan for normal scalars
                                : undefined;
                    return (
                      <div key={(t.scope || '') + '/' + t.name + '/' + ti}
                           style={color ? { '--wave-color-override': color } : undefined}>
                        <window.WaveRow
                          name={t.name}
                          scope={t.scope}
                          trace={t.trace}
                          width={waveWidth}
                          isBus={t.isBus}
                          radix={t.radix || 'HEX'}
                          selected={selectedSig === (t.signalName || t.name) || selectedSig === t.name}
                          colorHint={color}
                          onClick={() => onSelectWaveSignal(t.signalName || t.name, t.scope || '')}
                          onEdgeClick={jumpToWaveEdge}
                        />
                      </div>
                    );
                  })}
                  <div style={{ position: 'absolute', top: 0, bottom: 0, left: 280, width: waveWidth, pointerEvents: 'none' }}>
                    <window.WaveCursor time={waveCursor}  kind="a" width={waveWidth} />
                    <window.WaveCursor time={waveCursorB} kind="b" width={waveWidth} />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* CENTER ↔ CHAT splitter */}
        {eff.showChat && eff.rw > 0 && (
          <Splitter orient="v"
            onMouseDown={startDrag('right')}
            onDoubleClick={() => setRightW(rightW > 0 ? 0 : 320)}
          />
        )}

        {/* RIGHT — live chat connected to backend WS (was a mock; now sends
            via window.backend.send and appends streamed tokens / agent /
            reasoning / slash_output events to the feed). */}
        {eff.showChat && (
          <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--panel)', borderLeft: '1px solid var(--line)' }}>
            <div className="mini-h" style={{ display: 'flex', alignItems: 'center' }}>
              <b>chat</b>
              <span style={{ color: 'var(--fg-mute)', marginLeft: 8, fontSize: 10 }}>trace · debug · ask</span>
              <span style={{ flex: 1 }} />
              {chatStreaming && (
                <span style={{ color: 'var(--accent)', fontSize: 10, marginRight: 6 }}>● streaming</span>
              )}
              <button
                className="btn"
                onClick={() => { setChatFeed([]); _streamBuf.current = ''; }}
                style={{ padding: '1px 6px', fontSize: 10 }}
              >clear</button>
            </div>

            {/* Focus card — selected signal / current IP */}
            <div style={{
              padding: '6px 10px',
              background: 'var(--bg-2)', borderBottom: '1px solid var(--line)',
              fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-dim)',
            }}>
              focus: <span style={{ color: 'var(--accent)' }}>{selectedSig || '(click a signal)'}</span>
              {ipName && <> · ip: <span style={{ color: 'var(--cyan)' }}>{ipName}</span></>}
            </div>

            {/* Feed */}
            <div ref={_chatScrollRef} style={{
              flex: 1, overflow: 'auto', padding: '8px 10px',
              fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5,
            }}>
              {chatFeed.length === 0 && (
                <div style={{ color: 'var(--fg-mute)', fontSize: 10, marginBottom: 8 }}>
                  Click a signal in the wave or hierarchy panel to set focus, then
                  pick a quick prompt below or type a free question.
                </div>
              )}
              {chatFeed.map((m, i) => {
                if (m.kind === 'user') {
                  return (
                    <div key={i} style={{ marginBottom: 6, color: 'var(--accent)' }}>
                      <span style={{
                        fontSize: 9, letterSpacing: '0.1em',
                        textTransform: 'uppercase', color: 'var(--fg-mute)',
                        marginRight: 6,
                      }}>YOU</span>
                      <span style={{ fontFamily: 'var(--mono)' }}>{m.text}</span>
                    </div>
                  );
                }
                if (m.kind === 'thought') {
                  return (
                    <div key={i} style={{
                      marginBottom: 6, color: 'var(--magenta)',
                      fontSize: 10, fontStyle: 'italic',
                      borderLeft: '2px solid var(--magenta)',
                      paddingLeft: 8, opacity: 0.8,
                    }}>
                      <span style={{
                        fontSize: 9, letterSpacing: '0.1em',
                        textTransform: 'uppercase', color: 'var(--fg-mute)',
                        marginRight: 6, fontStyle: 'normal',
                      }}>THOUGHT</span>
                      <span style={{ whiteSpace: 'pre-wrap' }}>{m.text}</span>
                    </div>
                  );
                }
                if (m.kind === 'sys') {
                  return (
                    <div key={i} style={{ marginBottom: 6, color: 'var(--err)', fontSize: 10 }}>
                      {m.text}
                    </div>
                  );
                }
                // agent / agent_stream
                return (
                  <div key={i} style={{ marginBottom: 8, color: 'var(--fg)' }}>
                    <span style={{
                      fontSize: 9, letterSpacing: '0.1em',
                      textTransform: 'uppercase', color: 'var(--ok)',
                      marginRight: 6,
                    }}>AGENT{m.kind === 'agent_stream' ? ' …' : ''}</span>
                    <span style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--mono)', fontSize: 10 }}>
                      {m.text}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Quick prompts (signal-aware) */}
            <div style={{
              padding: '6px 10px', borderTop: '1px solid var(--line)',
              background: 'var(--bg-2)', fontSize: 10,
            }}>
              <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em',
                            textTransform: 'uppercase', marginBottom: 4 }}>quick prompts</div>
              {[
                `/trace ${selectedSig || 'gpio_irq'}${ipName ? ' --ip ' + ipName : ''}`,
                `/hier ${ipName || 'gpio_pad'}`,
                selectedSig ? `Why does ${selectedSig} have unexpected values around t=${waveCursor}ns?` : `Explain the FSM in ${ipName || 'this design'}`,
              ].map((p, i) => (
                <div
                  key={i}
                  onClick={() => sendChat(p)}
                  style={{
                    fontFamily: 'var(--mono)', fontSize: 10,
                    color: 'var(--fg)', padding: '3px 6px', marginBottom: 2,
                    background: 'var(--bg)', border: '1px solid var(--line)',
                    borderRadius: 3, cursor: 'pointer',
                  }}
                  title="click to send"
                >{p}</div>
              ))}
            </div>

            {/* Input */}
            <div className="prompt-row" style={{
              padding: 8, borderTop: '1px solid var(--line)',
              background: 'var(--bg)',
            }}>
              <span className="ps">›</span>
              <input
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChat();
                  }
                }}
                placeholder="ask the debug agent · /trace · /hier · ↵ send"
                disabled={chatStreaming}
                style={{ opacity: chatStreaming ? 0.6 : 1 }}
              />
              <span className="kbd-i">/</span>
              <span className="kbd-i">↵</span>
            </div>
          </div>
        )}
      </div>
      )}
    </div>
  );

};
