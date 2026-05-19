/* coverage.jsx — Atlas UI panel for the verilator coverage workflow.
 *
 * Layout (sits in the center column of workspace.jsx, replacing the chat;
 * the regular left + right ATLAS sidebars stay visible):
 *
 *   ┌──────────────────────────────────────────────┐
 *   │ Stats widget — Lines/Branches %, top files   │
 *   ├────────────────┬─────────────────────────────┤
 *   │ File list      │ Annotated source viewer     │
 *   │ (annotated/*)  │ (color-coded hit/miss)      │
 *   │                │                             │
 *   ├────────────────┴─────────────────────────────┤
 *   │ Gap navigator — top-N unhit lines, click to  │
 *   │ jump to source                                │
 *   └──────────────────────────────────────────────┘
 *
 * Data sources (all via existing /api/file):
 *   <DUT>/cov/coverage.info        — LCOV summary (DA: + BRDA: lines)
 *   <DUT>/cov/annotated/*.cov      — verilator annotated source files
 *
 * State is fetched on mount and on a manual /api/file refresh
 * (no streaming yet — refresh button + auto on workflow switch).
 */

const _COV_DEFAULT_DUT = 'gpio_pad';

const _covRuntimeDut = () => {
  try {
    const norm = window.normalizeAtlasSessionName || ((v) => String(v || '').trim());
    const parts = norm(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
    if (parts.length >= 3) return parts[parts.length - 2];
    const scope = norm(window.SCOPE_PATH || '');
    if (scope && !scope.includes('/')) return scope;
  } catch (_) {}
  return _COV_DEFAULT_DUT;
};

// ── coverage.info parser ──────────────────────────────────────
// Verilator --write-info emits LCOV-style records:
//   TN:<test_name>
//   SF:<source_file>
//   DA:<line>,<count>             ← per-line hit count
//   BRDA:<line>,<block>,<br>,<count>  ← per-branch (count "-" = not exercised)
//   end_of_record
// Multiple SF blocks per file. We aggregate into per-file stats.
const parseCoverageInfo = (txt) => {
  const files = {};   // path → { lines: {hit, total}, branches: {hit, total} }
  let cur = null;
  for (const raw of (txt || '').split('\n')) {
    const line = raw.trim();
    if (line.startsWith('SF:')) {
      const p = line.slice(3);
      if (!files[p]) {
        files[p] = { lines: { hit: 0, total: 0 }, branches: { hit: 0, total: 0 } };
      }
      cur = files[p];
    } else if (line === 'end_of_record') {
      cur = null;
    } else if (cur && line.startsWith('DA:')) {
      const parts = line.slice(3).split(',');
      cur.lines.total += 1;
      if (parts[1] && parts[1] !== '0') cur.lines.hit += 1;
    } else if (cur && line.startsWith('BRDA:')) {
      const parts = line.slice(5).split(',');
      const last = parts[parts.length - 1];
      cur.branches.total += 1;
      if (last && last !== '0' && last !== '-') cur.branches.hit += 1;
    }
  }
  // Compute totals
  let totLH = 0, totLF = 0, totBH = 0, totBF = 0;
  for (const p in files) {
    totLH += files[p].lines.hit;
    totLF += files[p].lines.total;
    totBH += files[p].branches.hit;
    totBF += files[p].branches.total;
  }
  return {
    files,
    totals: {
      lines: { hit: totLH, total: totLF, pct: totLF ? (100 * totLH / totLF) : 0 },
      branches: { hit: totBH, total: totBF, pct: totBF ? (100 * totBH / totBF) : 0 },
    },
  };
};

// ── Annotated source line classifier ──────────────────────────
// Verilator annotated format (each line of source prefixed):
//   "%000000  if (foo)"      → UNHIT (executable but never reached)
//   "%000123  bar = 1;"      → HIT 123 times (% prefix means executable)
//   " 0000234 dout <= ..."   → HIT 234 (no %, raw count)
//   "         end"           → non-executable / non-instrumented
const _hitClass = (line) => {
  // First non-space char determines status
  if (!line) return 'plain';
  const m = line.match(/^(\s*)(%?\d+)/);
  if (!m) return 'plain';
  const num = m[2].replace(/^%/, '');
  // All zeros = unhit. Anything else = hit.
  if (/^0+$/.test(num)) return 'unhit';
  return 'hit';
};

const _hitCount = (line) => {
  const m = line && line.match(/^(\s*)(%?\d+)/);
  if (!m) return 0;
  return parseInt(m[2].replace(/^%/, ''), 10) || 0;
};

// ── Stats widget ──────────────────────────────────────────────
const CovStatsWidget = ({ summary, dut, onRefresh, lastRefresh }) => {
  const t = summary && summary.totals;
  const Bar = ({ pct, color }) => (
    <div style={{
      width: '100%', height: 6, background: 'var(--bg-2)',
      borderRadius: 2, overflow: 'hidden',
    }}>
      <div style={{
        width: `${Math.max(0, Math.min(100, pct))}%`, height: '100%',
        background: color, transition: 'width 0.3s',
      }} />
    </div>
  );
  const fmt = (n) => (n == null ? '—' : `${n.toFixed(2)}%`);
  return (
    <div className="box" style={{ padding: 0 }}>
      <div className="box-h">
        <span>▸ coverage stats</span>
        <span style={{ flex: 1 }} />
        <span className="mute" style={{ fontSize: 10 }}>{dut}</span>
        <span
          onClick={onRefresh}
          title="reload coverage.info"
          style={{ marginLeft: 8, cursor: 'pointer', fontSize: 'var(--ui-control-font-size)', color: 'var(--accent)' }}
        >↻ refresh</span>
      </div>
      <div style={{ padding: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <div style={{ fontSize: 10, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Lines</div>
          <div style={{ fontSize: 22, fontWeight: 600, fontFamily: 'var(--mono)', marginTop: 2 }}>
            {t ? fmt(t.lines.pct) : '—'}
          </div>
          <div style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', marginTop: 2 }}>
            {t ? `${t.lines.hit} / ${t.lines.total}` : 'no data'}
          </div>
          <div style={{ marginTop: 6 }}>
            <Bar pct={t ? t.lines.pct : 0} color="var(--ok, #3fb950)" />
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Branches</div>
          <div style={{ fontSize: 22, fontWeight: 600, fontFamily: 'var(--mono)', marginTop: 2 }}>
            {t ? fmt(t.branches.pct) : '—'}
          </div>
          <div style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', marginTop: 2 }}>
            {t ? `${t.branches.hit} / ${t.branches.total}` : 'no data'}
          </div>
          <div style={{ marginTop: 6 }}>
            <Bar pct={t ? t.branches.pct : 0} color="var(--accent, #39c5cf)" />
          </div>
        </div>
      </div>
      {lastRefresh && (
        <div style={{ padding: '4px 12px 8px', fontSize: 10, color: 'var(--fg-mute)' }}>
          last loaded: {lastRefresh}
        </div>
      )}
    </div>
  );
};

// SSOT model coverage widget — reads cov/coverage.json emitted by
// ssot_coverage_summary.py. Function coverage is sourced from
// function_model; cycle coverage is sourced from cycle_model.
const CovModelWidget = ({ snapshot }) => {
  const fmtPct = (v) => (v == null ? '—' : `${Number(v).toFixed(2)}%`);
  const model = snapshot && snapshot.coverage_model || {};
  const fn = snapshot && (snapshot.function_coverage || model.function) || null;
  const cy = snapshot && (snapshot.cycle_coverage || model.cycle) || null;
  const Cell = ({ label, data, color }) => {
    const pct = data && data.pct != null ? Number(data.pct) : 0;
    const target = data && data.target_pct != null ? Number(data.target_pct) : null;
    const ok = data && data.meets_target;
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontSize: 10, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</span>
          <span style={{ fontSize: 10, color: ok ? 'var(--ok, #3fb950)' : 'var(--fg-mute)' }}>
            {target == null ? '' : `target ${target}%`}
          </span>
        </div>
        <div style={{ fontSize: 22, fontWeight: 600, fontFamily: 'var(--mono)', marginTop: 2 }}>
          {data ? fmtPct(data.pct) : '—'}
        </div>
        <div style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', marginTop: 2 }}>
          {data ? `${data.hit || 0} / ${data.total || 0}` : 'no SSOT model bins'}
        </div>
        <div style={{ marginTop: 6, height: 6, background: 'var(--bg-2)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            width: `${Math.max(0, Math.min(100, pct))}%`,
            height: '100%',
            background: color,
          }} />
        </div>
      </div>
    );
  };
  return (
    <div className="box">
      <div className="box-h">
        <span>▸ SSOT model coverage</span>
        <span style={{ flex: 1 }} />
        <span className="mute" style={{ fontSize: 10 }}>{snapshot ? snapshot.status || 'unknown' : 'no snapshot'}</span>
      </div>
      <div style={{ padding: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <Cell label="Function" data={fn} color="var(--ok, #3fb950)" />
        <Cell label="Cycle" data={cy} color="var(--accent, #39c5cf)" />
      </div>
    </div>
  );
};

// Reusable collapse-arrow span used in box headers. Positioned at the
// far right of the header next to the count. Click → onCollapse().
const _collapseArrow = (onCollapse, dir) => onCollapse ? (
  <span
    onClick={(e) => { e.stopPropagation(); onCollapse(); }}
    title={`collapse ${dir === 'left' ? 'panel ←' : 'panel →'}`}
    style={{
      cursor: 'pointer', marginLeft: 6, padding: '0 6px',
      color: 'var(--fg-mute)', fontSize: 14, userSelect: 'none',
      lineHeight: 1,
    }}
  >{dir === 'left' ? '‹' : '›'}</span>
) : null;

// ── File list (per-file coverage breakdown) ───────────────────
const CovFileList = ({ summary, activeFile, onSelect, onCollapse }) => {
  const files = summary && summary.files;
  if (!files || !Object.keys(files).length) {
    return (
      <div className="box" style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div className="box-h">
          <span>▸ files</span>
          <span style={{ flex: 1 }} />
          {_collapseArrow(onCollapse, 'left')}
        </div>
        <div style={{ padding: 16, color: 'var(--fg-mute)', fontSize: 12 }}>
          No coverage.info found. Run <code>/coverage-build</code>, simulate, then
          <code> /coverage-merge</code> + <code>/coverage-report</code>.
        </div>
      </div>
    );
  }
  const rows = Object.keys(files).sort((a, b) => {
    const pa = files[a].lines.total ? files[a].lines.hit / files[a].lines.total : 1;
    const pb = files[b].lines.total ? files[b].lines.hit / files[b].lines.total : 1;
    return pa - pb;  // worst-coverage first
  });
  return (
    <div className="box" style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div className="box-h">
        <span>▸ files</span>
        <span style={{ flex: 1 }} />
        <span className="mute" style={{ fontSize: 10 }}>{rows.length}</span>
        {_collapseArrow(onCollapse, 'left')}
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {rows.map((p) => {
          const f = files[p];
          const pct = f.lines.total ? (100 * f.lines.hit / f.lines.total) : 0;
          const isActive = activeFile === p;
          const short = p.split('/').slice(-2).join('/');
          return (
            <div
              key={p}
              onClick={() => onSelect(p)}
              style={{
                padding: '6px 12px', cursor: 'pointer',
                background: isActive ? 'var(--select)' : 'transparent',
                borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                fontSize: 12, fontFamily: 'var(--mono)',
              }}
              onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = 'var(--bg-2)'; }}
              onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{short}</span>
                <span style={{
                  fontSize: 'var(--ui-control-font-size)',
                  color: pct >= 80 ? '#3fb950' : pct >= 50 ? '#d4a72c' : '#f85149',
                  marginLeft: 8,
                }}>{pct.toFixed(1)}%</span>
              </div>
              <div style={{ fontSize: 10, color: 'var(--fg-mute)' }}>
                {f.lines.hit}/{f.lines.total} lines ·
                {' '}{f.branches.hit}/{f.branches.total} branches
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── Annotated source viewer (color-coded hit/miss) ────────────
const CovSourceViewer = ({ path, content, jumpToLine }) => {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (jumpToLine != null && ref.current) {
      const el = ref.current.querySelector(`[data-ln="${jumpToLine}"]`);
      if (el && el.scrollIntoView) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [jumpToLine, content]);

  if (!path) {
    return (
      <div className="box" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="mute" style={{ fontSize: 12 }}>← select a file to view annotated source</div>
      </div>
    );
  }
  const lines = (content || '').split('\n');
  return (
    <div className="box" style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div className="box-h">
        <span>▸ annotated</span>
        <span style={{ flex: 1 }} />
        <span className="mute" style={{ fontSize: 10, fontFamily: 'var(--mono)' }}>{path}</span>
      </div>
      <div ref={ref} style={{
        flex: 1, overflow: 'auto',
        fontFamily: 'var(--mono)', fontSize: 12, lineHeight: 1.45,
        padding: '6px 0', background: 'var(--bg)',
      }}>
        {lines.map((line, i) => {
          const cls = _hitClass(line);
          const bg = cls === 'unhit' ? 'rgba(248,81,73,0.10)'
                   : cls === 'hit'   ? 'rgba(63,185,80,0.06)'
                   : 'transparent';
          const fg = cls === 'unhit' ? '#f85149' : 'inherit';
          return (
            <div
              key={i}
              data-ln={i + 1}
              style={{
                display: 'grid', gridTemplateColumns: '50px 1fr',
                background: bg, color: fg,
                paddingLeft: 8,
              }}
            >
              <span style={{ color: 'var(--fg-mute)', textAlign: 'right', paddingRight: 8, userSelect: 'none' }}>
                {i + 1}
              </span>
              <span style={{ whiteSpace: 'pre' }}>{line}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── Gap navigator (top-N unhit lines, click to jump) ──────────
const CovGapNav = ({ annotated, activePath, onJump, onCollapse }) => {
  if (!annotated || !activePath) {
    return (
      <div className="box" style={{ height: '100%' }}>
        <div className="box-h">
          <span>▸ gaps</span>
          <span style={{ flex: 1 }} />
          {_collapseArrow(onCollapse, 'right')}
        </div>
        <div style={{ padding: 16, color: 'var(--fg-mute)', fontSize: 11 }}>
          select a file to see its uncovered lines
        </div>
      </div>
    );
  }
  const unhit = [];
  (annotated || '').split('\n').forEach((line, idx) => {
    if (_hitClass(line) === 'unhit') {
      unhit.push({ ln: idx + 1, code: line.replace(/^[%\s\d]+/, '').trim().slice(0, 80) });
    }
  });
  return (
    <div className="box" style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div className="box-h">
        <span>▸ gaps</span>
        <span style={{ flex: 1 }} />
        <span className="mute" style={{ fontSize: 10 }}>{unhit.length} unhit</span>
        {_collapseArrow(onCollapse, 'right')}
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {unhit.length === 0 ? (
          <div style={{ padding: 16, color: 'var(--fg-mute)', fontSize: 11 }}>
            no unhit lines in this file 🎯
          </div>
        ) : unhit.slice(0, 50).map((u) => (
          <div
            key={u.ln}
            onClick={() => onJump(u.ln)}
            style={{
              padding: '4px 12px', cursor: 'pointer',
              fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)',
              borderBottom: '1px solid var(--line)',
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-2)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
          >
            <span style={{ color: '#f85149', marginRight: 8 }}>:{u.ln}</span>
            <span style={{ color: 'var(--fg-mute)' }}>{u.code || '(empty)'}</span>
          </div>
        ))}
        {unhit.length > 50 && (
          <div style={{ padding: 8, fontSize: 10, color: 'var(--fg-mute)', textAlign: 'center' }}>
            … {unhit.length - 50} more unhit lines (showing top 50)
          </div>
        )}
      </div>
    </div>
  );
};

// ── Toggle coverage widget (per-scope toggle %) ───────────────
// Reads <DUT>/cov/toggle.json (written by /coverage-vcd-toggle).
// Each scope row shows %, toggled/total bits, net count.
const CovToggleWidget = ({ toggle }) => {
  if (!toggle) {
    return (
      <div className="box">
        <div className="box-h"><span>▸ toggle (VCD)</span></div>
        <div style={{ padding: 12, color: 'var(--fg-mute)', fontSize: 11 }}>
          Run <code>/coverage-vcd-toggle</code> to extract toggle coverage from a VCD.
        </div>
      </div>
    );
  }
  const sorted = (toggle.scopes || []).slice().sort((a, b) => a.pct - b.pct);
  const top = sorted.slice(0, 6);
  return (
    <div className="box">
      <div className="box-h">
        <span>▸ toggle (VCD)</span>
        <span style={{ flex: 1 }} />
        <span className="mute" style={{ fontSize: 10 }}>{toggle.nets} nets</span>
      </div>
      <div style={{ padding: '10px 12px', display: 'grid', gridTemplateColumns: '1fr auto', gap: 8 }}>
        <div>
          <div style={{ fontSize: 10, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Bits toggled</div>
          <div style={{ fontSize: 22, fontWeight: 600, fontFamily: 'var(--mono)', marginTop: 2 }}>
            {toggle.pct.toFixed(2)}%
          </div>
          <div style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', marginTop: 2 }}>
            {toggle.toggled_bits} / {toggle.total_bits}
          </div>
        </div>
        <div style={{ width: 6, background: 'var(--bg-2)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            width: '100%',
            height: `${Math.max(0, Math.min(100, toggle.pct))}%`,
            background: 'var(--mag, #d063ff)',
            transform: 'translateY(' + (100 - toggle.pct) + '%)',
          }} />
        </div>
      </div>
      {top.length > 0 && (
        <div style={{ borderTop: '1px solid var(--line)', maxHeight: 130, overflowY: 'auto' }}>
          {top.map((s) => (
            <div key={s.scope} style={{
              display: 'grid', gridTemplateColumns: '50px 1fr',
              padding: '4px 12px', fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)',
            }}>
              <span style={{
                textAlign: 'right', paddingRight: 6,
                color: s.pct >= 80 ? '#3fb950' : s.pct >= 50 ? '#d4a72c' : '#f85149',
              }}>
                {s.pct.toFixed(0)}%
              </span>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {s.scope || '(root)'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Delta tracker (current vs previous run from history.jsonl) ─
// history.jsonl is appended to by coverage_report.sh on each run.
// Each line is one JSON object with timestamp + lines/branches stats.
const CovDeltaWidget = ({ history }) => {
  if (!history || history.length === 0) {
    return (
      <div className="box">
        <div className="box-h"><span>▸ delta</span></div>
        <div style={{ padding: 12, color: 'var(--fg-mute)', fontSize: 11 }}>
          Run <code>/coverage-report</code> at least twice to see iteration deltas.
        </div>
      </div>
    );
  }
  const cur = history[history.length - 1];
  const prev = history.length >= 2 ? history[history.length - 2] : null;
  const deltaLine = prev ? cur.lines.pct - prev.lines.pct : 0;
  const deltaBr = prev ? cur.branches.pct - prev.branches.pct : 0;
  const arrow = (d) => d > 0 ? '▲' : d < 0 ? '▼' : '·';
  const color = (d) => d > 0 ? '#3fb950' : d < 0 ? '#f85149' : 'var(--fg-mute)';
  return (
    <div className="box">
      <div className="box-h">
        <span>▸ delta</span>
        <span style={{ flex: 1 }} />
        <span className="mute" style={{ fontSize: 10 }}>iter {history.length}</span>
      </div>
      <div style={{ padding: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <div style={{ fontSize: 10, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Lines Δ</div>
          <div style={{ fontSize: 18, fontWeight: 600, fontFamily: 'var(--mono)', color: color(deltaLine), marginTop: 2 }}>
            {arrow(deltaLine)} {prev ? (deltaLine >= 0 ? '+' : '') + deltaLine.toFixed(2) + '%' : '—'}
          </div>
          <div style={{ fontSize: 10, color: 'var(--fg-mute)', marginTop: 2 }}>
            now {cur.lines.pct.toFixed(2)}%{prev ? ` (was ${prev.lines.pct.toFixed(2)}%)` : ''}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Branches Δ</div>
          <div style={{ fontSize: 18, fontWeight: 600, fontFamily: 'var(--mono)', color: color(deltaBr), marginTop: 2 }}>
            {arrow(deltaBr)} {prev ? (deltaBr >= 0 ? '+' : '') + deltaBr.toFixed(2) + '%' : '—'}
          </div>
          <div style={{ fontSize: 10, color: 'var(--fg-mute)', marginTop: 2 }}>
            now {cur.branches.pct.toFixed(2)}%{prev ? ` (was ${prev.branches.pct.toFixed(2)}%)` : ''}
          </div>
        </div>
      </div>
      {history.length > 1 && (
        <div style={{
          borderTop: '1px solid var(--line)', padding: '6px 12px',
          fontSize: 10, color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
        }}>
          trend (last {Math.min(10, history.length)}):
          {' '}
          {history.slice(-10).map((h, i) => (
            <span key={i} title={`iter ${history.length - history.slice(-10).length + i + 1}: ${h.lines.pct.toFixed(2)}%`}>
              {h.lines.pct.toFixed(0)}{i < history.slice(-10).length - 1 ? ' → ' : ''}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

// Vertical strip shown in place of a collapsed side panel. Click to expand.
const CovCollapsedStrip = ({ side, label, onExpand }) => (
  <div
    onClick={onExpand}
    title={`expand ${label}`}
    style={{
      height: '100%', cursor: 'pointer',
      background: 'var(--bg-2)',
      border: '1px solid var(--line)',
      borderRadius: 4,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'flex-start',
      padding: '8px 0', gap: 8,
      userSelect: 'none', overflow: 'hidden',
    }}
    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg)'}
    onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-2)'}
  >
    <span style={{ color: 'var(--accent)', fontSize: 14, fontWeight: 700 }}>
      {side === 'left' ? '›' : '‹'}
    </span>
    <span style={{
      color: 'var(--fg-mute)', fontSize: 10,
      letterSpacing: '0.12em', textTransform: 'uppercase',
      writingMode: 'vertical-rl',
    }}>
      {label}
    </span>
  </div>
);

// ── Top-level Coverage panel ──────────────────────────────────
window.Coverage = () => {
  const [dut, setDut] = React.useState(_covRuntimeDut);
  const [summary, setSummary] = React.useState(null);
  const [coverageSnapshot, setCoverageSnapshot] = React.useState(null);
  const [toggle, setToggle] = React.useState(null);
  const [history, setHistory] = React.useState([]);
  const [activeFile, setActiveFile] = React.useState(null);
  const [annotatedContent, setAnnotatedContent] = React.useState('');
  const [jumpLine, setJumpLine] = React.useState(null);
  const [error, setError] = React.useState('');
  const [lastRefresh, setLastRefresh] = React.useState('');
  const [htmlAvailable, setHtmlAvailable] = React.useState(false);
  // Collapse state for the side panels — persisted across reloads.
  const [leftCollapsed, setLeftCollapsed] = React.useState(() => {
    try { return localStorage.getItem('atlasCoverageLeftCollapsed') === '1'; }
    catch (_) { return false; }
  });
  const [rightCollapsed, setRightCollapsed] = React.useState(() => {
    try { return localStorage.getItem('atlasCoverageRightCollapsed') === '1'; }
    catch (_) { return false; }
  });
  const toggleLeft = () => {
    setLeftCollapsed(v => {
      try { localStorage.setItem('atlasCoverageLeftCollapsed', v ? '0' : '1'); } catch (_) {}
      return !v;
    });
  };
  const toggleRight = () => {
    setRightCollapsed(v => {
      try { localStorage.setItem('atlasCoverageRightCollapsed', v ? '0' : '1'); } catch (_) {}
      return !v;
    });
  };

  // Fetch coverage.info via /api/file (also pulls toggle.json and history.jsonl
  // in parallel — all three are written by the coverage_report / vcd_toggle
  // scripts and live under <DUT>/cov/).
  const loadInfo = React.useCallback(async () => {
    setError('');
    const listDir = async (path) => {
      try {
        const r = await fetch('/api/files?path=' + encodeURIComponent(path));
        if (!r.ok) return null;
        return await r.json();
      } catch (_) { return null; }
    };
    // ── Fire all three fetches in parallel ──
    const tryFetch = async (path) => {
      try {
        const r = await fetch('/api/file?path=' + encodeURIComponent(path));
        if (!r.ok) return null;
        return await r.json();
      } catch (_) { return null; }
    };
    const dutDir = await listDir(dut);
    const hasCovDir = dutDir && Array.isArray(dutDir.entries)
      && dutDir.entries.some(e => e && e.type === 'dir' && e.name === 'cov');
    if (!hasCovDir) {
      setSummary(null);
      setCoverageSnapshot(null);
      setToggle(null);
      setHistory([]);
      setHtmlAvailable(false);
      setError(`coverage directory not found — run /coverage-report ${dut} first`);
      return;
    }
    const covDir = await listDir(`${dut}/cov`);
    const covFiles = new Set(
      covDir && Array.isArray(covDir.entries)
        ? covDir.entries.filter(e => e && e.type === 'file').map(e => e.name)
        : []
    );
    const tryFetchCov = async (name) => covFiles.has(name) ? tryFetch(`${dut}/cov/${name}`) : null;
    const [infoResp, toggleResp, histResp, snapshotResp] = await Promise.all([
      tryFetchCov('coverage.info'),
      tryFetchCov('toggle.json'),
      tryFetchCov('history.jsonl'),
      tryFetchCov('coverage.json'),
    ]);

    // Coverage.info → parsed summary (or null if missing)
    if (infoResp) {
      const parsed = parseCoverageInfo(infoResp.content || '');
      setSummary(parsed);
      setLastRefresh(new Date().toLocaleTimeString());
      if (!activeFile && Object.keys(parsed.files).length) {
        const worst = Object.keys(parsed.files).sort((a, b) => {
          const pa = parsed.files[a].lines.total ? parsed.files[a].lines.hit / parsed.files[a].lines.total : 1;
          const pb = parsed.files[b].lines.total ? parsed.files[b].lines.hit / parsed.files[b].lines.total : 1;
          return pa - pb;
        })[0];
        setActiveFile(worst);
      }
    } else {
      setSummary(null);
      setError(`coverage.info not found — run /coverage-report ${dut} first`);
    }

    // toggle.json → optional
    if (toggleResp) {
      try {
        setToggle(JSON.parse(toggleResp.content || 'null'));
      } catch (_) { setToggle(null); }
    } else {
      setToggle(null);
    }

    // history.jsonl → optional, line-delimited JSON
    if (histResp && histResp.content) {
      const rows = histResp.content
        .split('\n')
        .filter(l => l.trim())
        .map(l => { try { return JSON.parse(l); } catch (_) { return null; } })
        .filter(Boolean);
      setHistory(rows);
    } else {
      setHistory([]);
    }

    // coverage.json snapshot → tells us whether HTML is available
    if (snapshotResp) {
      try {
        const snap = JSON.parse(snapshotResp.content || '{}');
        setCoverageSnapshot(snap);
        setHtmlAvailable(!!snap.html_available);
      } catch (_) {
        setCoverageSnapshot(null);
        setHtmlAvailable(false);
      }
    } else {
      setCoverageSnapshot(null);
      setHtmlAvailable(false);
    }
  }, [dut, activeFile]);

  React.useEffect(() => {
    const refreshDut = () => {
      const next = _covRuntimeDut();
      setDut(prev => prev === next ? prev : next);
    };
    refreshDut();
    window.addEventListener('atlas-data-changed', refreshDut);
    window.addEventListener('atlas-session-loaded', refreshDut);
    return () => {
      window.removeEventListener('atlas-data-changed', refreshDut);
      window.removeEventListener('atlas-session-loaded', refreshDut);
    };
  }, []);

  // Fetch annotated <file>.cov when activeFile changes
  React.useEffect(() => {
    if (!activeFile) { setAnnotatedContent(''); return; }
    // Annotated path mirrors source path under <DUT>/cov/annotated/
    // SF: in coverage.info already has the relative path (e.g. gpio_pad/rtl/foo.sv)
    // The annotated/ dir mirrors that — verilator_coverage --annotate writes
    // <annotated>/<basename> for each SF.
    const base = activeFile.split('/').pop();
    const annotatedPath = `${dut}/cov/annotated/${base}`;
    fetch('/api/file?path=' + encodeURIComponent(annotatedPath))
      .then(r => r.ok ? r.json() : Promise.reject(`annotated/${base} not found`))
      .then(j => setAnnotatedContent(j.content || ''))
      .catch(e => {
        setAnnotatedContent('');
        setError(typeof e === 'string' ? e : e.message);
      });
  }, [activeFile, dut]);

  // Initial + when DUT changes
  React.useEffect(() => { loadInfo(); }, [dut]);

  return (
    <div style={{
      display: 'grid',
      gridTemplateRows: 'auto auto 1fr',
      gap: 12, height: '100%', overflow: 'hidden',
    }}>
      {/* Top: stats widget + HTML link */}
      <div style={{ position: 'relative' }}>
        <CovStatsWidget summary={summary} dut={dut} onRefresh={loadInfo} lastRefresh={lastRefresh} />
        {htmlAvailable && (
          <a
            href={`/${dut}/cov/html/index.html`}
            target="_blank"
            rel="noopener noreferrer"
            title="open genhtml report in a new tab"
            style={{
              position: 'absolute', top: 8, right: 12, fontSize: 'var(--ui-control-font-size)',
              color: 'var(--accent)', fontFamily: 'var(--mono)',
              textDecoration: 'none',
            }}
          >↗ HTML report</a>
        )}
      </div>

      {/* Middle row: SSOT function/cycle + toggle widget + delta tracker */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.2fr 1fr 1fr',
        gap: 12,
      }}>
        <CovModelWidget snapshot={coverageSnapshot} />
        <CovToggleWidget toggle={toggle} />
        <CovDeltaWidget history={history} />
      </div>

      {/* Bottom: 3-pane (files | source | gaps).
          Side panels collapse to a 28px strip on demand. */}
      <div style={{
        display: 'grid',
        gridTemplateColumns:
          (leftCollapsed ? '28px' : '240px') +
          ' 1fr ' +
          (rightCollapsed ? '28px' : '240px'),
        gap: 12, minHeight: 0, overflow: 'hidden',
      }}>
        {leftCollapsed
          ? <CovCollapsedStrip side="left" label="files" onExpand={toggleLeft} />
          : <CovFileList
              summary={summary}
              activeFile={activeFile}
              onSelect={(p) => { setActiveFile(p); setJumpLine(null); }}
              onCollapse={toggleLeft}
            />
        }
        <CovSourceViewer
          path={activeFile}
          content={annotatedContent}
          jumpToLine={jumpLine}
        />
        {rightCollapsed
          ? <CovCollapsedStrip side="right" label="gaps" onExpand={toggleRight} />
          : <CovGapNav
              annotated={annotatedContent}
              activePath={activeFile}
              onJump={(ln) => setJumpLine(ln)}
              onCollapse={toggleRight}
            />
        }
      </div>

      {error && (
        <div style={{
          position: 'absolute', bottom: 16, right: 16, zIndex: 50,
          background: 'rgba(248,81,73,0.15)', border: '1px solid #f85149',
          color: '#f85149', padding: '8px 12px', borderRadius: 4,
          fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 400,
        }}>
          ⚠ {error}
          <span
            onClick={() => setError('')}
            style={{ marginLeft: 12, cursor: 'pointer', fontWeight: 700 }}
          >×</span>
        </div>
      )}
    </div>
  );
};
