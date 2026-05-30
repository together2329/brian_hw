// sim-debug-panels.tsx — TypeScript migration of the standalone presentational
// components extracted from sim-debug.jsx (strangler-fig split). These are the
// self-contained sub-components that lived between the helper cluster and the
// root SimDebug component (lines 230–843), plus the two props-only inner
// components (`Step4`, `Splitter`) that the legacy code defined INSIDE
// SimDebug but which close over nothing but their own props — moving them out
// is behavior-identical and shrinks the root file.
//
// Components: CocotbTreeView, SimResultBadge, SimSummaryPanel, TBHierarchyView,
//             RangeInput, SourceViewer, HierarchyNode, Step4, Splitter.
//
// Load order: included by index.html BEFORE sim-debug.tsx and AFTER
// sim-debug-helpers.tsx. The root component reads these back through
// `window.SimDebug*` bridges registered at the bottom (kept as window refs to
// avoid module-ordering issues — identical to the legacy cross-script-global
// behavior, where everything shared one in-browser-babel scope).
//
// Transitional: bridges to `window.*` at the bottom for not-yet-migrated .jsx.
import { useState, useRef, useEffect, useMemo, Fragment } from 'react';
import type { ReactNode, CSSProperties, MouseEvent as ReactMouseEvent } from 'react';
import { annotationAxesForMode } from './sim-debug-helpers';

// ── Cross-file globals owned by OTHER files / this family. Typed via a local
// view of `window`; behavior identical to the legacy implicit globals.
interface PrismLike {
  languages?: Record<string, unknown>;
  highlight?: (code: string, grammar: unknown, lang: string) => string;
  plugins?: { autoloader?: { loadLanguages?: (lang: string, cb: () => void) => void } };
}
interface SimDebugPanelsWindow {
  PRISM_LANG_MAP?: Record<string, string>;
  Prism?: PrismLike;
  SimDebugCocotbTreeView?: typeof CocotbTreeView;
  SimDebugSimResultBadge?: typeof SimResultBadge;
  SimDebugSimSummaryPanel?: typeof SimSummaryPanel;
  SimDebugTBHierarchyView?: typeof TBHierarchyView;
  SimDebugRangeInput?: typeof RangeInput;
  SimDebugSourceViewer?: typeof SourceViewer;
  SimDebugHierarchyNode?: typeof HierarchyNode;
  SimDebugStep4?: typeof Step4;
  SimDebugSplitter?: typeof Splitter;
}
const g = (typeof window !== 'undefined' ? window : ({} as Window)) as unknown as SimDebugPanelsWindow;

type OpenFileFn = (path: string, line?: number) => void;

// Cocotb (testbench) tree view — categorised file list + parsed
// results.xml summary. Click any file to load it in the source viewer.
interface CocotbFile { path: string; name: string; size: number }
interface CocotbCase {
  name?: string; classname?: string; status?: string;
  file?: string; line?: number; sim_time_ns?: string | number; time_s?: number;
}
interface CocotbResults {
  total?: number; pass?: number; fail?: number; skip?: number;
  cases?: CocotbCase[]; error?: string;
}
interface CocotbData {
  exists?: boolean; error?: string; results?: CocotbResults;
  tb_hierarchy?: TBHierarchy;
  tests?: CocotbFile[]; sequences?: CocotbFile[]; env?: CocotbFile[];
  agent?: CocotbFile[]; other?: CocotbFile[]; build?: CocotbFile[];
  [k: string]: unknown;
}
interface CocotbTreeViewProps {
  data: CocotbData | null | undefined;
  ipName: string;
  onOpenFile?: OpenFileFn;
}
const CocotbTreeView = ({ data, ipName, onOpenFile }: CocotbTreeViewProps) => {
  const [openSection, setOpenSection] = useState<Record<string, boolean>>({
    tests: true, sequences: true, env: true, agent: true, other: false, build: false,
  });
  const toggle = (k: string) => setOpenSection(s => ({ ...s, [k]: !s[k] }));

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
  const Sec = ({ k, label }: { k: string; label: string }) => {
    const items = (data[k] as CocotbFile[]) || [];
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
                    {c.sim_time_ns ? `${parseFloat(String(c.sim_time_ns)).toFixed(0)}ns` : `${((c.time_s || 0)*1000).toFixed(0)}ms`}
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

const SimResultBadge = ({ status }: { status?: string }) => {
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

interface SimTest {
  scenario_id?: string; name?: string; status?: string;
  pass_rows?: number; fail_rows?: number; expected?: string;
  checker?: string; source?: string;
}
interface SimSummaryData {
  tests?: SimTest[]; ssot_path?: string; sb_path?: string;
}
interface SimSummaryRow {
  id: string; name: string; status: string; evidence: string;
  expected: string; checker: string; source: string; file: string; line: number;
}
interface SimSummaryPanelProps {
  ipName: string;
  data: SimSummaryData | null | undefined;
  loading: boolean;
  error: string;
  cocotbData: CocotbData | null | undefined;
  onOpenFile?: OpenFileFn;
  onRefresh: () => void;
}
const SimSummaryPanel = ({ ipName, data, loading, error, cocotbData, onOpenFile, onRefresh }: SimSummaryPanelProps) => {
  const scenarioRows: SimSummaryRow[] = Array.isArray(data?.tests) ? data!.tests!.map((t, i) => ({
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
  const resultCases: SimSummaryRow[] = Array.isArray(cocotbData?.results?.cases)
    ? cocotbData!.results!.cases!.map((c, i) => ({
      id: c.name || `TC${i + 1}`,
      name: c.classname ? `${c.classname}.${c.name}` : (c.name || `TC${i + 1}`),
      status: c.status === 'skip' ? 'pending' : (c.status || 'pending'),
      evidence: c.sim_time_ns ? `${parseFloat(String(c.sim_time_ns || '0')).toFixed(0)} ns` : `${Math.round((c.time_s || 0) * 1000)} ms`,
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
  }, { pass: 0, fail: 0, pending: 0, total: 0 } as Record<string, number>);
  const evidencePaths = [
    data?.ssot_path,
    data?.sb_path,
    ipName ? `${ipName}/sim/results.xml` : '',
    ipName ? `${ipName}/tb/cocotb/results.xml` : '',
  ].filter(Boolean) as string[];

  const Stat = ({ label, value, color }: { label: string; value: ReactNode; color: string }) => (
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
interface TBHierarchyEntry {
  name?: string; file?: string; line?: number;
  bases?: string[]; decorators?: string[];
}
interface TBHierarchy {
  envs?: TBHierarchyEntry[]; scoreboards?: TBHierarchyEntry[];
  agents?: TBHierarchyEntry[]; sequences?: TBHierarchyEntry[];
  tests?: TBHierarchyEntry[];
}
const TBHierarchyView = ({ h, onOpenFile }: { h: TBHierarchy; onOpenFile?: OpenFileFn }) => {
  const Group = ({ title, items, color }: { title: string; items?: TBHierarchyEntry[]; color?: string }) => {
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
interface RangeInputVcd { timescale?: string; timeRange?: [number, number] }
interface RangeInputProps {
  effRange: [number, number];
  vcdData: RangeInputVcd | null | undefined;
  setViewRange: (range: [number, number]) => void;
}
const RangeInput = ({ effRange, vcdData, setViewRange }: RangeInputProps) => {
  const ts = vcdData ? vcdData.timescale : 'ns';
  const full = vcdData ? (vcdData.timeRange as [number, number]) : [0, 0];
  const fullSpan = (full[1] - full[0]) || 1;
  const viewSpan = effRange[1] - effRange[0];
  const zoomPct = (fullSpan / Math.max(1e-9, viewSpan)) * 100;

  const [startTxt, setStartTxt] = useState(String(Math.round(effRange[0])));
  const [endTxt,   setEndTxt]   = useState(String(Math.round(effRange[1])));
  useEffect(() => { setStartTxt(String(Math.round(effRange[0]))); }, [effRange[0]]);
  useEffect(() => { setEndTxt  (String(Math.round(effRange[1]))); }, [effRange[1]]);

  const commit = () => {
    if (!vcdData) return;
    const a = Number(startTxt), b = Number(endTxt);
    if (Number.isNaN(a) || Number.isNaN(b)) return;
    const lo = Math.max(full[0], Math.min(a, b));
    const hi = Math.min(full[1], Math.max(a, b));
    if (hi - lo < 1) return;
    setViewRange([lo, hi]);
  };

  const inputStyle: CSSProperties = {
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
          if (e.key === 'Enter') { (e.target as HTMLInputElement).blur(); }
          if (e.key === 'Escape') { setStartTxt(String(Math.round(effRange[0]))); (e.target as HTMLInputElement).blur(); }
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
          if (e.key === 'Enter') { (e.target as HTMLInputElement).blur(); }
          if (e.key === 'Escape') { setEndTxt(String(Math.round(effRange[1]))); (e.target as HTMLInputElement).blur(); }
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
interface SourceViewerAnnotation { name: string; a: string; b: string }
interface SourceViewerProps {
  lines?: string[];
  cursor?: number;
  path?: string;
  vcdAnnotations?: Record<number, SourceViewerAnnotation[]>;
  vcdAnnotationAxis?: string;
}
const SourceViewer = ({ lines, cursor, path, vcdAnnotations = {}, vcdAnnotationAxis = 'both' }: SourceViewerProps) => {
  const ref = useRef<HTMLDivElement>(null);
  // Bump on every Prism load so we re-render once the grammar arrives.
  const [grammarTick, setGrammarTick] = useState(0);
  const annotationAxes = useMemo(
    () => annotationAxesForMode(vcdAnnotationAxis),
    [vcdAnnotationAxis],
  );

  // Resolve language id from extension via window.PRISM_LANG_MAP.
  const ext = (path || '').match(/\.([a-zA-Z0-9]+)$/)?.[1]?.toLowerCase() || '';
  const langId = (g.PRISM_LANG_MAP || {})[ext] || 'none';

  // Highlighted-per-line HTML. If Prism + the grammar are ready we run
  // it; otherwise we fall back to plain escaped text so the panel
  // never goes blank while the autoloader fetches.
  const lineHTMLs = useMemo(() => {
    if (!lines || lines.length === 0) return [];
    const fullCode = lines.join('\n');
    const Prism = g.Prism;
    if (Prism && Prism.languages && Prism.languages[langId]) {
      try {
        const html = Prism.highlight!(fullCode, Prism.languages[langId], langId);
        return html.split('\n');
      } catch (_) {/* fall through */}
    }
    // No grammar yet — escape and split. Trigger autoloader.
    if (Prism && Prism.plugins && Prism.plugins.autoloader && langId !== 'none') {
      Prism.plugins.autoloader.loadLanguages!(langId, () => setGrammarTick(t => t + 1));
    }
    return lines.map(ln =>
      ln.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    );
  }, [lines, langId, grammarTick]);

  useEffect(() => {
    if ((cursor || 0) > 0 && ref.current) {
      const el = ref.current.querySelector(`[data-ln="${cursor}"]`) as HTMLElement | null;
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
          <Fragment key={i}>
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
                      {annotationAxes.map(axis => (
                        <span
                          key={axis.id}
                          style={{ color: axis.color, marginLeft: 5 }}
                        >
                          {axis.label}={(item as unknown as Record<string, string>)[axis.key]}
                        </span>
                      ))}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </Fragment>
        );
      })}
    </div>
  );
};

// Recursive collapsible tree node for the instance hierarchy panel.
// Click on the chevron toggles children; click on the module name fires
// `onSelectModule` so SimDebug can load the matching SV source. The
// instance path stays foreground (accent), module name is cyan.
interface HierarchyTreeNode {
  name?: string; module?: string; cyclic?: boolean;
  children?: HierarchyTreeNode[];
}
interface HierarchyNodeProps {
  node: HierarchyTreeNode | null | undefined;
  depth: number;
  onSelectModule?: (moduleName?: string, instancePath?: string) => void;
  activeModule?: string;
}
const HierarchyNode = ({ node, depth, onSelectModule, activeModule }: HierarchyNodeProps) => {
  const [open, setOpen] = useState(depth < 2);
  if (!node) return null;
  const hasKids = (node.children || []).length > 0;
  const indent = depth * 14;
  const last = (node.name || '').split('.').pop();
  const isActive = activeModule === node.module;
  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `${indent + 14}px minmax(96px, 1fr) 20px minmax(128px, 1.15fr)`,
          alignItems: 'center',
          columnGap: 6,
          padding: '2px 6px 2px 0',
          color: 'var(--fg)',
          background: isActive ? 'color-mix(in oklch, var(--accent) 18%, transparent)' : 'transparent',
          borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
        }}
      >
        <span
          onClick={() => hasKids && setOpen(o => !o)}
          style={{
            justifySelf: 'end',
            color: 'var(--fg-mute)', fontSize: 9,
            cursor: hasKids ? 'pointer' : 'default',
          }}
        >
          {hasKids ? (open ? '▾' : '▸') : '·'}
        </span>
        <span
          onClick={() => onSelectModule && onSelectModule(node.module, node.name)}
          style={{
            color: 'var(--accent)', cursor: 'pointer',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}
          title="open module source"
        >{last}</span>
        <span style={{ color: 'var(--fg-mute)', justifySelf: 'center' }}>::</span>
        <span
          onClick={() => onSelectModule && onSelectModule(node.module, node.name)}
          style={{
            color: 'var(--cyan)', cursor: 'pointer',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}
          title="open module source"
        >{node.module}</span>
        {node.cyclic && (
          <span style={{ color: 'var(--err)', fontSize: 9, marginLeft: 4 }}>cyclic</span>
        )}
      </div>
      {open && hasKids && node.children!.map((c, i) => (
        <HierarchyNode key={i} node={c} depth={depth + 1}
          onSelectModule={onSelectModule} activeModule={activeModule} />
      ))}
    </div>
  );
};

// Compact step block — like V3's but lighter, since panels carry the evidence.
// (Defined inside SimDebug in the legacy file but closes over no state — props
// only — so it is extracted here unchanged.)
interface Step4Props {
  num?: ReactNode; kind?: string; tag?: ReactNode; when?: ReactNode;
  title?: ReactNode; args?: ReactNode; body?: ReactNode; done?: boolean;
  onClick?: () => void; active?: boolean;
}
const Step4 = ({ num, kind, tag, when, title, args, body, done, onClick, active }: Step4Props) => {
  const dotColor = ({
    thought: 'var(--magenta)',
    tool:    'var(--cyan)',
    action:  'var(--accent)',
    obs:     'var(--ok)',
  } as Record<string, string>)[kind || ''] || 'var(--fg-mute)';
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

// Drag handle between panels. Props-only; extracted unchanged from SimDebug.
interface SplitterProps {
  orient: 'v' | 'h';
  onMouseDown?: (e: ReactMouseEvent) => void;
  onDoubleClick?: () => void;
}
const Splitter = ({ orient, onMouseDown, onDoubleClick }: SplitterProps) => (
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

export {
  CocotbTreeView, SimResultBadge, SimSummaryPanel, TBHierarchyView,
  RangeInput, SourceViewer, HierarchyNode, Step4, Splitter,
};
export type {
  CocotbData, CocotbFile, CocotbCase, CocotbResults,
  SimSummaryData, SimTest, SimSummaryRow,
  TBHierarchy, TBHierarchyEntry, HierarchyTreeNode,
  SourceViewerAnnotation, OpenFileFn,
};

// ── Transitional bridge: register on window so sim-debug.tsx (and any legacy
// consumer) resolves these. Namespaced to avoid colliding with workspace
// globals; the root component reads them back through these names.
if (typeof window !== 'undefined') {
  g.SimDebugCocotbTreeView = CocotbTreeView;
  g.SimDebugSimResultBadge = SimResultBadge;
  g.SimDebugSimSummaryPanel = SimSummaryPanel;
  g.SimDebugTBHierarchyView = TBHierarchyView;
  g.SimDebugRangeInput = RangeInput;
  g.SimDebugSourceViewer = SourceViewer;
  g.SimDebugHierarchyNode = HierarchyNode;
  g.SimDebugStep4 = Step4;
  g.SimDebugSplitter = Splitter;
}
