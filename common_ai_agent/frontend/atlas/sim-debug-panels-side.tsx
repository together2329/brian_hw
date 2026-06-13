// sim-debug-panels-side.tsx — the LEFT hierarchy panel and the SOURCE band
// extracted from sim-debug.tsx (strangler-fig split). Behavior-identical:
//   • HierarchyPanel = the SAME `eff.showHier && (...)` subtree — the RTL/TB
//     tab toggle, the backend label, the cocotb tree (TB) vs the RTL
//     HierarchyNode + the VCD signal list (RTL).
//   • SourceBand = the SAME `eff.showSource && (...)` subtree — the source
//     mini-header (path + loading/line badges + annot toggle + A/B/A+B axis
//     buttons) and the SourceViewer.
// The root SimDebug closure owns all the state; each panel receives the slice
// it renders + the handlers it fires as a typed props bundle (window-sourced
// values stay `any`, same permissive house style as sim-debug-helpers.tsx).
//
// Load order: imported by sim-debug.tsx. Owns no window bridge.
import { useRef, useState, useEffect } from 'react';
import type { Dispatch, MouseEvent as ReactMouseEvent, ReactNode, SetStateAction } from 'react';
import { CocotbTreeView, SourceViewer, HierarchyNode } from './sim-debug-panels';
import type { VcdData, VcdSignal, ModuleSignal } from './sim-debug-helpers';
import {
  waveSignalMatches, filterModuleSignals, moduleSignalCounts, moduleSignalWidthLabel,
  buildSignalSearchMatcher, stripSignalRange, signalRangeOf, normalizeProjectSourcePath,
} from './sim-debug-helpers';

interface HierarchyPanelProps {
  leftTab: string;
  setLeftTab: (v: string) => void;
  cocotbData: any;
  hierarchyBackendTitle: string;
  hierarchyBackendLabel: string;
  ipName: string;
  loadSourceFile: (path: string, cursorLine?: number) => void;
  hierarchy: any;
  hierarchyLoading: boolean;
  onSelectModule: (moduleName?: string, instancePath?: string) => void;
  srcModule: string;
  hierarchyError: string;
  vcdData: VcdData | null;
  selectedSig: string;
  selectedSigScope: string;
  wavePinnedSignals: Array<{ name?: string; scope?: string }>;
  onSelectWaveSignal: (signalName: string, signalScope?: string) => void;
  showSignalHierarchy: boolean;
  moduleSignals: ModuleSignal[];
  moduleSignalsModule: string;
  moduleSignalsScope: string;
  moduleSignalsLoading: boolean;
  moduleSignalsError: string;
  signalFilter: string;
  setSignalFilter: (v: string) => void;
  signalSource: string;
  setSignalSource: (v: string) => void;
  onSelectModuleSignal: (sig: ModuleSignal) => void;
  addSignalToWave: (name: string, scope?: string) => void;
  addSignalsToWave: (items: Array<{ name?: string; scope?: string }>) => void;
  waveSel: Array<{ name?: string; scope?: string }>;
  setWaveSel: Dispatch<SetStateAction<Array<{ name?: string; scope?: string }>>>;
  onTraceSignal: (name: string, scope?: string) => void;
  onTraceLoad: (name: string, scope?: string) => void;
  runSignalTrace: (name: string, scope?: string) => void;
  traceResult: any;
  setTraceResult: (v: any) => void;
}

// One stable key per selected signal (scope-qualified, range-stripped).
const selKeyOf = (name?: string, scope?: string) =>
  `${String(scope || '').trim()}::${stripSignalRange(name).toLowerCase()}`;

// Trace fanout popover — the pyslang /api/trace result for one signal: its
// driver (where it is assigned/driven) and its loads/sinks (where it is read).
// Each row jumps the source viewer to that file:line so the user can follow
// the signal through the RTL.
interface TraceSink { file_line?: string; context?: string; access?: string }
interface TraceData {
  signal?: string; scope?: string; loading?: boolean; error?: string; backend?: string;
  driver?: { file_line?: string; kind?: string } | null;
  drivers?: Array<{ file_line?: string; kind?: string }>;
  driver_count?: number;
  sinks?: TraceSink[]; sink_count?: number;
}
const TraceFanoutPopover = ({ trace, onClose, onFollow }: {
  trace: TraceData; onClose: () => void; onFollow: (fileLine: string) => void;
}): ReactNode => {
  const drivers = Array.isArray(trace?.drivers)
    ? trace!.drivers!
    : (trace?.driver ? [trace.driver] : []);
  const sinks = Array.isArray(trace?.sinks) ? trace!.sinks! : [];
  const TraceRow = ({ fl, label, sub, color }: { fl?: string; label: string; sub?: string; color?: string }) => (
    <div
      onClick={() => fl && onFollow(fl)}
      style={{
        display: 'flex', gap: 6, alignItems: 'baseline',
        padding: '3px 8px', cursor: fl ? 'pointer' : 'default',
        borderRadius: 3,
      }}
      title={fl || ''}
      onMouseEnter={e => { if (fl) e.currentTarget.style.background = 'var(--bg-2)'; }}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      {sub && <span style={{ color: color || 'var(--fg-mute)', fontSize: 9, minWidth: 30 }}>{sub}</span>}
      <span style={{ flex: 1, color: 'var(--fg)', fontSize: 10, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {label}
      </span>
    </div>
  );
  return (
    <div style={{
      position: 'fixed', left: 12, bottom: 12, zIndex: 60,
      width: 340, maxHeight: '62vh', display: 'flex', flexDirection: 'column',
      background: 'var(--panel)', border: '1px solid var(--cyan)', borderRadius: 6,
      boxShadow: '0 6px 22px rgba(0,0,0,0.5)', fontFamily: 'var(--mono)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', borderBottom: '1px solid var(--line)' }}>
        <span style={{ color: 'var(--cyan)', fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase' }}>trace</span>
        <span style={{ flex: 1, color: 'var(--accent)', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {trace.scope ? `${trace.scope}.` : ''}{trace.signal}
        </span>
        <button onClick={onClose} title="close" style={{ background: 'transparent', border: 'none', color: 'var(--fg-mute)', cursor: 'pointer', fontSize: 14, lineHeight: 1 }}>×</button>
      </div>
      <div style={{ overflow: 'auto', padding: '4px 0' }}>
        {trace.loading ? (
          <div style={{ padding: '6px 8px', color: 'var(--fg-mute)', fontSize: 10, fontStyle: 'italic' }}>tracing via pyslang…</div>
        ) : (
          <>
            <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase', padding: '2px 8px' }}>
              drivers / writes ({trace.driver_count ?? drivers.length})
            </div>
            {drivers.length
              ? drivers.map((drv, i) => (
                  <TraceRow key={`${drv.file_line || ''}-${i}`} fl={drv.file_line}
                    label={(drv.file_line || '').split('/').slice(-1)[0] || '(?)'}
                    sub={drivers.length > 1 ? `drv${i + 1}` : 'drv'} color="var(--accent)" />
                ))
              : <div style={{ padding: '2px 8px', color: 'var(--fg-mute)', fontSize: 10 }}>no driver found</div>}
            <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase', padding: '6px 8px 2px' }}>
              loads / sinks ({trace.sink_count ?? sinks.length})
            </div>
            {sinks.length
              ? sinks.map((sk, i) => (
                  <TraceRow key={i} fl={sk.file_line}
                    label={(sk.file_line || '').split('/').slice(-1)[0] || '(?)'}
                    sub={sk.access || 'RD'} color="var(--cyan)" />
                ))
              : <div style={{ padding: '2px 8px', color: 'var(--fg-mute)', fontSize: 10 }}>no loads found</div>}
            {trace.error && (
              <div style={{ padding: '4px 8px', color: 'var(--err)', fontSize: 9 }}>{trace.error}</div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// Direction badge colors — match the wave panel's role hints.
const DIRECTION_COLOR: Record<string, string> = {
  in: '#4dd0e1', out: '#ffb84d', inout: '#ff6bd0', internal: 'var(--fg-mute)',
};
const DIRECTION_GLYPH: Record<string, string> = {
  in: '→', out: '←', inout: '↔', internal: '·',
};

const signalNameWithRange = (name: unknown, range: unknown): string => {
  const n = String(name || '').trim();
  const r = String(range || '').trim();
  if (!n || !r || signalRangeOf(n)) return n;
  return `${n}${r}`;
};

const moduleSignalDisplayName = (sig: ModuleSignal): string => {
  const name = String(sig?.name || '').trim();
  const width = Number(sig?.width || 0);
  return width > 1 && !signalRangeOf(name) ? `${name}[${width - 1}:0]` : name;
};

export const HierarchyPanel = ({
  leftTab, setLeftTab, cocotbData, hierarchyBackendTitle, hierarchyBackendLabel,
  ipName, loadSourceFile, hierarchy, hierarchyLoading, onSelectModule, srcModule, hierarchyError,
  vcdData, selectedSig, selectedSigScope, wavePinnedSignals, onSelectWaveSignal,
  moduleSignals, moduleSignalsModule, moduleSignalsScope, moduleSignalsLoading,
  moduleSignalsError, signalFilter, setSignalFilter, signalSource, setSignalSource,
  onSelectModuleSignal, addSignalToWave, addSignalsToWave, waveSel, setWaveSel,
  onTraceSignal, onTraceLoad, runSignalTrace, traceResult, setTraceResult,
}: HierarchyPanelProps): ReactNode => {
  // Default 50/50 split between the hierarchy tree (top) and the signal
  // list (bottom) — mirrors the source/waveform split's even default.
  const [hierFrac, setHierFrac] = useState(0.5);
  const [signalSearch, setSignalSearch] = useState('');
  // Anchor row index for Shift+click range selection (within the visible list).
  const [anchorIdx, setAnchorIdx] = useState(-1);
  // Right-click menu: anchored at the cursor, carries the row's {name, scope}
  // and whether it belongs to the current multi-selection (→ bulk add/trace).
  const [ctxMenu, setCtxMenu] = useState<
    { x: number; y: number; name: string; scope: string; bulk: boolean } | null
  >(null);
  useEffect(() => {
    if (!ctxMenu) return undefined;
    const close = () => setCtxMenu(null);
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setCtxMenu(null); };
    window.addEventListener('click', close);
    window.addEventListener('keydown', onKey);
    return () => { window.removeEventListener('click', close); window.removeEventListener('keydown', onKey); };
  }, [ctxMenu]);

  // ── Multi-selection helpers ──────────────────────────────────────
  const selectedKeys = new Set((waveSel || []).map(s => selKeyOf(s.name, s.scope)));
  const isRowSelected = (name?: string, scope?: string) => selectedKeys.has(selKeyOf(name, scope));
  const dedupeSel = (items: Array<{ name?: string; scope?: string }>) => {
    const seen = new Set<string>();
    const out: Array<{ name?: string; scope?: string }> = [];
    for (const it of items) {
      const k = selKeyOf(it.name, it.scope);
      if (seen.has(k)) continue;
      seen.add(k);
      out.push({ name: it.name, scope: it.scope || '' });
    }
    return out;
  };
  const hasSelectionModifier = (e: ReactMouseEvent) => e.shiftKey || e.ctrlKey || e.metaKey;

  // Unified row selection. rows = the visible list as {name,scope}; idx =
  // selected index; focus = single-click side effect (focus + source jump).
  const selectRow = (
    e: ReactMouseEvent, idx: number,
    rows: Array<{ name?: string; scope?: string }>, focus: () => void,
  ) => {
    const item = rows[idx];
    if (!item) return;
    if (hasSelectionModifier(e)) {
      // Prevent text selection and the macOS Ctrl+click context-menu path from
      // stealing multi-select gestures before React sees them.
      e.preventDefault();
      e.stopPropagation();
    }
    if (e.shiftKey && anchorIdx >= 0) {
      const [a, b] = [Math.min(anchorIdx, idx), Math.max(anchorIdx, idx)];
      setWaveSel(prev => dedupeSel([...(prev || []), ...rows.slice(a, b + 1)]));
    } else if (e.ctrlKey || e.metaKey) {
      const k = selKeyOf(item.name, item.scope);
      setWaveSel(prev => {
        const current = prev || [];
        const selected = current.some(s => selKeyOf(s.name, s.scope) === k);
        return selected
          ? current.filter(s => selKeyOf(s.name, s.scope) !== k)
          : dedupeSel([...current, item]);
      });
      setAnchorIdx(idx);
    } else {
      setWaveSel([item]);
      setAnchorIdx(idx);
      focus();
    }
  };
  const onRowMouseDown = (
    e: ReactMouseEvent, idx: number,
    rows: Array<{ name?: string; scope?: string }>, focus: () => void,
  ) => {
    if (e.button === 0 && hasSelectionModifier(e)) selectRow(e, idx, rows, focus);
  };
  const onRowClick = (
    e: ReactMouseEvent, idx: number,
    rows: Array<{ name?: string; scope?: string }>, focus: () => void,
  ) => {
    // Modified primary clicks are handled on mousedown so Ctrl+click works on
    // macOS before the browser synthesizes a context-menu event.
    if (hasSelectionModifier(e)) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    selectRow(e, idx, rows, focus);
  };
  const openCtxMenu = (e: ReactMouseEvent, name: string, scope: string) => {
    e.preventDefault();
    setCtxMenu({ x: e.clientX, y: e.clientY, name, scope, bulk: isRowSelected(name, scope) && (waveSel || []).length > 1 });
  };
  const onRowContextMenu = (e: ReactMouseEvent, name: string, scope: string) => {
    if (hasSelectionModifier(e)) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    openCtxMenu(e, name, scope);
  };
  const dragRef = useRef<{ startY: number; startFrac: number; bodyH: number } | null>(null);
  const startSignalResize = (e: ReactMouseEvent) => {
    e.preventDefault();
    const host = (e.currentTarget as HTMLElement).parentElement;
    dragRef.current = {
      startY: e.clientY,
      startFrac: hierFrac,
      bodyH: host?.clientHeight || 420,
    };
    const onMove = (ev: MouseEvent) => {
      const d = dragRef.current;
      if (!d) return;
      const next = Math.max(0.25, Math.min(0.85, d.startFrac + (ev.clientY - d.startY) / d.bodyH));
      setHierFrac(next);
    };
    const onUp = () => {
      dragRef.current = null;
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  return (
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
          onOpenFile={(p: string, line?: number) => loadSourceFile(p, line || 0)}
        />
      ) : (
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', fontFamily: 'var(--mono)', fontSize: 11 }}>
        <div style={{ flex: `${Math.round(hierFrac * 100)} ${Math.round(hierFrac * 100)} 0`, minHeight: 0, overflow: 'auto', padding: 8 }}>
          {hierarchy ? (
            <HierarchyNode node={hierarchy} depth={0}
              onSelectModule={onSelectModule}
              activeModule={srcModule} />
          ) : (
            <div style={{ color: 'var(--fg-mute)', padding: 8 }}>
              {hierarchyLoading ? 'Loading RTL hierarchy…' : 'No RTL hierarchy yet.'}<br />
              {hierarchyError ? (
                <span style={{ color: 'var(--err)' }}>{hierarchyError}</span>
              ) : (
                <span>{hierarchyLoading ? 'Elaborating RTL in the background.' : 'Pick a workspace IP to elaborate.'}</span>
              )}
            </div>
          )}
        </div>
        <div
          onMouseDown={startSignalResize}
          onDoubleClick={() => setHierFrac(0.5)}
          title="resize hierarchy/signals panes (double-click → 50/50)"
          style={{
            height: 4,
            flexShrink: 0,
            background: 'var(--line)',
            cursor: 'row-resize',
          }}
        />
        <div style={{ flex: `${Math.round((1 - hierFrac) * 100)} ${Math.round((1 - hierFrac) * 100)} 0`, minHeight: 0, display: 'flex', flexDirection: 'column', borderTop: '1px solid var(--line)', position: 'relative' }}>
          {(() => {
            const matcher = buildSignalSearchMatcher(signalSearch);
            const counts = moduleSignalCounts(moduleSignals);
            const rtlRows = filterModuleSignals(moduleSignals, signalFilter)
              .filter(s => matcher.test(s.name) || matcher.test(moduleSignalDisplayName(s)));
            const vcdRows = (vcdData?.signals || []).filter(s => {
              const displayName = signalNameWithRange(s.name || s.signalName, s.range || signalRangeOf(s.name));
              return matcher.test(s.name || '') || matcher.test(displayName);
            });
            const vcdShown = vcdRows.slice(0, 200);
            // Flat {name,scope} arrays parallel to the rendered rows — feed the
            // shared multi-select click handler so Ctrl/Shift+click line up.
            const rtlSignalScope = moduleSignalsScope || '';
            const rtlSelRows = rtlRows.map(s => ({ name: s.name, scope: rtlSignalScope }));
            const vcdSelRows = vcdShown.map(s => ({ name: s.signalName || s.name || '', scope: s.scope || '' }));
            const inVcd = (name: string, scope = '') =>
              (vcdData?.signals || []).some(vs => waveSignalMatches(vs, name, scope));
            const pinnedByName = (name: string) =>
              wavePinnedSignals.some(pin =>
                stripSignalRange(pin.name).toLowerCase() === stripSignalRange(name).toLowerCase());
            const FilterChip = ({ id, label, n }: { id: string; label: string; n: number }) => (
              <button
                onClick={() => setSignalFilter(id)}
                title={`${label} signals`}
                style={{
                  background: signalFilter === id ? 'var(--accent)' : 'transparent',
                  color: signalFilter === id ? 'var(--bg)' : 'var(--fg-mute)',
                  border: '1px solid var(--line)', borderRadius: 3,
                  padding: '0 6px', fontSize: 9, cursor: 'pointer',
                  fontFamily: 'var(--mono)', fontWeight: 700, textTransform: 'uppercase',
                }}
              >{label} {n}</button>
            );
            const SrcBtn = ({ id, label, title }: { id: string; label: string; title: string }) => (
              <button
                onClick={() => setSignalSource(id)}
                title={title}
                style={{
                  background: signalSource === id ? 'var(--cyan)' : 'transparent',
                  color: signalSource === id ? '#001018' : 'var(--fg-mute)',
                  border: '1px solid var(--line)', borderRadius: 3,
                  padding: '0 6px', fontSize: 9, cursor: 'pointer',
                  fontFamily: 'var(--mono)', fontWeight: 700,
                }}
              >{label}</button>
            );
            return (
              <>
                {/* header: title · RTL/VCD source toggle */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 8px 4px', flexWrap: 'wrap' }}>
                  <span style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase' }}>signals</span>
                  <SrcBtn id="rtl" label="RTL" title="module ports + internal nets/vars (pyslang)" />
                  <SrcBtn id="vcd" label="VCD" title="signals present in the loaded waveform" />
                  <span style={{ flex: 1 }} />
                  {signalSource === 'rtl' && moduleSignalsModule && (
                    <span style={{ color: 'var(--cyan)', fontSize: 9, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 120 }} title={moduleSignalsModule}>
                      {moduleSignalsModule}
                    </span>
                  )}
                </div>
                {/* search box (regex-aware) */}
                <div style={{ padding: '0 8px 4px' }}>
                  <input
                    value={signalSearch}
                    onChange={e => setSignalSearch(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Escape') setSignalSearch(''); e.stopPropagation(); }}
                    placeholder="search signals (regex)…"
                    spellCheck={false}
                    style={{
                      width: '100%', boxSizing: 'border-box',
                      background: 'var(--bg)',
                      color: matcher.valid ? 'var(--fg)' : 'var(--err)',
                      border: '1px solid ' + (matcher.valid ? 'var(--line)' : 'var(--err)'),
                      borderRadius: 3, padding: '2px 6px',
                      fontSize: 10, fontFamily: 'var(--mono)',
                    }}
                    title={matcher.valid ? 'JS regex, case-insensitive (Esc clears)' : 'invalid regex — using substring match'}
                  />
                </div>
                {/* direction filter chips (RTL only) */}
                {signalSource === 'rtl' && (
                  <div style={{ display: 'flex', gap: 3, padding: '0 8px 5px', flexWrap: 'wrap' }}>
                    <FilterChip id="all" label="all" n={counts.all} />
                    <FilterChip id="in" label="in" n={counts.in} />
                    <FilterChip id="out" label="out" n={counts.out} />
                    <FilterChip id="internal" label="int" n={counts.internal} />
                  </div>
                )}
                {/* multi-selection action bar */}
                {(waveSel || []).length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '0 8px 6px', flexWrap: 'wrap' }}>
                    <span style={{ color: 'var(--accent)', fontSize: 10, fontFamily: 'var(--mono)' }}>{waveSel.length} selected</span>
                    <button
                      className="btn"
                      onClick={() => addSignalsToWave(waveSel)}
                      title="add all selected signals to the waveform (Ctrl+W)"
                      style={{ padding: '1px 8px', fontSize: 10, fontWeight: 700 }}
                    >＋ add to wave</button>
                    <button
                      className="btn"
                      onClick={() => { setWaveSel([]); setAnchorIdx(-1); }}
                      style={{ padding: '1px 8px', fontSize: 10 }}
                    >clear</button>
                    <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}>Ctrl/⇧+click to multi-select</span>
                  </div>
                )}
                {/* scrollable list */}
                <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '0 8px 8px' }}>
                  {signalSource === 'rtl' ? (
                    moduleSignalsLoading ? (
                      <div style={{ color: 'var(--fg-mute)', fontSize: 10, fontStyle: 'italic' }}>elaborating signals…</div>
                    ) : !moduleSignalsModule ? (
                      <div style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                        Click a module in the hierarchy above to list its signals.
                      </div>
                    ) : rtlRows.length === 0 ? (
                      <div style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                        {moduleSignalsError
                          ? <span style={{ color: 'var(--err)' }}>{moduleSignalsError}</span>
                          : (signalSearch || signalFilter !== 'all'
                              ? 'No signals match the current filter/search.'
                              : `No signals found in ${moduleSignalsModule}.`)}
                      </div>
                    ) : (
                      rtlRows.map((s, i) => {
                        const isFocus = selectedSig === s.name;
                        const inSel = isRowSelected(s.name, rtlSignalScope);
                        const pinned = pinnedByName(s.name);
                        const present = inVcd(s.name, rtlSignalScope);
                        const dirColor = DIRECTION_COLOR[s.direction] || 'var(--fg-mute)';
                        const widthLabel = moduleSignalWidthLabel(s);
                        const displayName = moduleSignalDisplayName(s);
                        return (
                          <div
                            key={`${s.name}-${i}`}
                            onMouseDown={e => onRowMouseDown(e, i, rtlSelRows, () => onSelectModuleSignal(s))}
                            onClick={e => onRowClick(e, i, rtlSelRows, () => onSelectModuleSignal(s))}
                            onDoubleClick={() => addSignalToWave(s.name, rtlSignalScope)}
                            onContextMenu={e => onRowContextMenu(e, s.name, rtlSignalScope)}
                            style={{
                              height: 25, boxSizing: 'border-box', borderBottom: '1px solid #11141b', padding: '0 4px', cursor: 'pointer',
                              color: isFocus ? 'var(--accent)' : 'var(--fg)',
                              background: inSel ? 'color-mix(in oklch, var(--accent) 22%, transparent)'
                                        : isFocus ? 'var(--bg-2)' : 'transparent',
                              display: 'flex', gap: 5, alignItems: 'center',
                            }}
                            title={`${s.direction}${widthLabel ? ' · ' + widthLabel : ''} · ${s.type || ''}\nclick to focus · Ctrl/⇧+click multi-select · right-click → add / trace`}
                          >
                            <span style={{ color: present ? 'var(--cyan)' : 'var(--fg-dim)', width: 8 }}>{pinned ? '◆' : present ? '◇' : '·'}</span>
                            <span style={{ color: dirColor, width: 10, textAlign: 'center', fontSize: 10 }} title={s.direction}>{DIRECTION_GLYPH[s.direction] || '·'}</span>
                            <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {displayName}
                            </span>
                          </div>
                        );
                      })
                    )
                  ) : (
                    vcdShown.length > 0 ? (
                      vcdShown.map((s: VcdSignal, i: number) => {
                        const nm = s.signalName || s.name || '';
                        const displayName = signalNameWithRange(s.name || nm, s.range || signalRangeOf(s.name));
                        const isFocus = selectedSig === s.name && (!selectedSigScope || selectedSigScope === s.scope);
                        const inSel = isRowSelected(nm, s.scope || '');
                        const isPinned = wavePinnedSignals.some(pin => waveSignalMatches(s, pin.name, pin.scope));
                        return (
                          <div
                            key={s.id}
                            onMouseDown={e => onRowMouseDown(e, i, vcdSelRows, () => onSelectWaveSignal(s.name!, s.scope))}
                            onClick={e => onRowClick(e, i, vcdSelRows, () => onSelectWaveSignal(s.name!, s.scope))}
                            onDoubleClick={() => addSignalToWave(nm, s.scope || '')}
                            onContextMenu={e => onRowContextMenu(e, nm, s.scope || '')}
                            style={{
                              height: 25, boxSizing: 'border-box', borderBottom: '1px solid #11141b', padding: '0 4px', cursor: 'pointer',
                              color: isFocus ? 'var(--accent)' : 'var(--fg)',
                              background: inSel ? 'color-mix(in oklch, var(--accent) 22%, transparent)'
                                        : isFocus ? 'var(--bg-2)' : 'transparent',
                              display: 'flex', gap: 4, alignItems: 'center',
                            }}
                            title="click to focus · Ctrl/⇧+click multi-select · right-click → add / trace"
                          >
                            <span style={{ color: isPinned ? 'var(--cyan)' : 'var(--fg-mute)' }}>{isPinned ? '◆' : '·'}</span>
                            <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {displayName}
                            </span>
                          </div>
                        );
                      })
                    ) : (
                      <div style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                        {vcdData?.signals?.length ? 'No signals match the search.' : 'No waveform signals loaded.'}
                      </div>
                    )
                  )}
                </div>
                {/* right-click context menu — add (single/bulk) + pyslang trace */}
                {ctxMenu && (() => {
                  const Item = ({ label, onPick, color }: { label: string; onPick: () => void; color?: string }) => (
                    <button
                      onClick={() => { onPick(); setCtxMenu(null); }}
                      style={{
                        display: 'block', width: '100%', textAlign: 'left',
                        background: 'transparent', color: color || 'var(--fg)', border: 'none',
                        padding: '5px 8px', fontSize: 11, cursor: 'pointer', borderRadius: 3,
                        fontFamily: 'var(--mono)', whiteSpace: 'nowrap',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-2)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >{label}</button>
                  );
                  return (
                  <div
                    style={{
                      position: 'fixed', left: ctxMenu.x, top: ctxMenu.y, zIndex: 50,
                      background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 4,
                      boxShadow: '0 4px 14px rgba(0,0,0,0.4)', padding: 4, minWidth: 168,
                    }}
                    onClick={e => e.stopPropagation()}
                  >
                    {ctxMenu.bulk ? (
                      /* multi-selection → add-to-waveform only (tracing N
                         signals at once is ambiguous; Ctrl+W also adds them) */
                      <Item label={`＋ Add ${waveSel.length} to waveform`} onPick={() => addSignalsToWave(waveSel)} />
                    ) : (
                      <>
                        <Item label="＋ Add to waveform" onPick={() => addSignalToWave(ctxMenu.name, ctxMenu.scope)} />
                        <div style={{ height: 1, background: 'var(--line)', margin: '3px 4px' }} />
                        <Item label="↳ Trace driver / loads" color="var(--cyan)"
                              onPick={() => runSignalTrace(ctxMenu.name, ctxMenu.scope)} />
                        <Item label="→ Go to driver" color="var(--accent)"
                              onPick={() => onTraceSignal(ctxMenu.name, ctxMenu.scope)} />
                        <Item label="→ Go to first load" color="var(--cyan)"
                              onPick={() => onTraceLoad(ctxMenu.name, ctxMenu.scope)} />
                      </>
                    )}
                    <div style={{ color: 'var(--fg-mute)', fontSize: 9, padding: '2px 8px', fontFamily: 'var(--mono)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 240 }}>
                      {ctxMenu.bulk
                        ? `${waveSel.length} signals selected`
                        : `${ctxMenu.scope ? `${ctxMenu.scope}.` : ''}${ctxMenu.name}`}
                    </div>
                  </div>
                  );
                })()}
                {/* trace fanout popover — driver + loads (sinks), click to follow */}
                {traceResult && (
                  <TraceFanoutPopover
                    trace={traceResult}
                    onClose={() => setTraceResult(null)}
                    onFollow={(fileLine: string) => {
                      const m = String(fileLine || '').match(/^(.*):(\d+)$/);
                      if (m) loadSourceFile(normalizeProjectSourcePath(m[1]), parseInt(m[2], 10));
                    }}
                  />
                )}
              </>
            );
          })()}
        </div>
      </div>
      )}
    </div>
  );
};

interface SourceBandProps {
  eff: any;
  srcPath: string;
  srcLoading: boolean;
  srcCursor: number;
  showVcdAnnotations: boolean;
  setShowVcdAnnotations: (fn: (v: boolean) => boolean) => void;
  waveCursor: number;
  waveCursorB: number;
  vcdData: VcdData | null;
  vcdAnnotationAxis: string;
  setVcdAnnotationAxis: (mode: string) => void;
  srcLines: string[];
  selectedSig: string;
  sourceVcdAnnotations: any;
  onPickSignal?: (name: string) => void;
  onAddSignal?: (name: string) => void;
  onSelectSignals?: (names: string[]) => void;
  onDropToWave?: (names: string[]) => void;
  onDropSignalFromWave?: (name: string, scope: string) => void;
  onSignalContextMenu?: (name: string, x: number, y: number, selSignals?: string[]) => void;
}

export const SourceBand = ({
  eff, srcPath, srcLoading, srcCursor, showVcdAnnotations, setShowVcdAnnotations,
  waveCursor, waveCursorB, vcdData, vcdAnnotationAxis, setVcdAnnotationAxis,
  srcLines, selectedSig, sourceVcdAnnotations, onPickSignal, onAddSignal, onSelectSignals, onDropToWave, onDropSignalFromWave, onSignalContextMenu,
}: SourceBandProps): ReactNode => {
  return (
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
        {showVcdAnnotations && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 2, marginLeft: 4 }}>
            {([
              ['both', 'A+B', `show VCD values at A (${waveCursor}${vcdData?.timescale || 'ns'}) and B (${waveCursorB}${vcdData?.timescale || 'ns'})`],
              ['a', 'A', `show VCD values at cursor A (${waveCursor}${vcdData?.timescale || 'ns'})`],
              ['b', 'B', `show VCD values at cursor B (${waveCursorB}${vcdData?.timescale || 'ns'})`],
            ] as Array<[string, string, string]>).map(([mode, label, title]) => (
              <button
                key={mode}
                className="btn"
                onClick={() => setVcdAnnotationAxis(mode)}
                title={title}
                style={{
                  padding: '1px 6px',
                  fontSize: 10,
                  fontWeight: 700,
                  minWidth: 26,
                  background: vcdAnnotationAxis === mode ? 'var(--cyan)' : undefined,
                  color: vcdAnnotationAxis === mode ? '#001018' : undefined,
                }}
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>
      <SourceViewer
        lines={srcLines}
        cursor={srcCursor}
        path={srcPath}
        selectedSig={selectedSig}
        vcdAnnotations={sourceVcdAnnotations}
        vcdAnnotationAxis={vcdAnnotationAxis}
        onPickSignal={onPickSignal}
        onAddSignal={onAddSignal}
        onSelectSignals={onSelectSignals}
        onDropToWave={onDropToWave}
        onDropSignalFromWave={onDropSignalFromWave}
        onSignalContextMenu={onSignalContextMenu}
      />
    </div>
  );
};
