// sim-debug.tsx — TypeScript migration of the root SimDebug component from
// sim-debug.jsx (strangler-fig split). VARIATION 4: Tri-surface Prompt-first
// Debug. Combines V3's prompt-first agent thread (vcd.open → vcd.trace →
// observation → sr.read tool sequence) with persistent V1-style waveform AND
// source panels. Tool calls in the chat drive what's shown in the side
// panels — clicking a tool card scrolls/cursors the relevant panel; the user
// can also drive panels manually.
//
// This file keeps the ROOT component only. The pure helpers were extracted to
// sim-debug-helpers.tsx and the standalone presentational components to
// sim-debug-panels.tsx (both behavior-identical). SimDebug itself is a single
// tightly-coupled closure (≈1.5k lines) — its hooks/handlers/JSX all close
// over the same ~40 useState cells, so it CANNOT be split further without
// lifting that state into props (a structural redesign, forbidden here).
//
// Load order: included by index.html AFTER sim-debug-helpers.tsx and
// sim-debug-panels.tsx. The `window.SimDebug = ...` bridge at the bottom is
// preserved verbatim so the legacy mount points keep resolving the root.
import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import type { MouseEvent as ReactMouseEvent } from 'react';
import {
  normalizeProjectSourcePath,
  stripSignalRange,
  signalRangeOf,
  buildWaveTraceList,
  buildVcdLineAnnotations,
  parseVerilogParamValueMap,
  inferRtlTopFromVcd,
  activeIpFromAtlasRuntime,
  vcdPathBelongsToIp,
  waveSignalMatches,
  waveSignalKey,
  removedSignalsAfterReAdd,
  waveRowFromVcdSignal,
} from './sim-debug-helpers';
import type { ModuleSignal, VcdData, VcdSignal, PinnedSignal, WaveGroupState } from './sim-debug-helpers';
import { SimSummaryPanel, Splitter } from './sim-debug-panels';
import { useModuleSignals } from './sim-debug-module-signals';
import { useSimDebugIntent } from './sim-debug-intent-hook';
import { appendActiveSessionParam } from './workspace-session-routing';
// Cross-file window view + the shared local types — extracted to
// sim-debug-root-shared.tsx so the presentational siblings can reuse the SAME
// window view (behavior identical).
import { g } from './sim-debug-root-shared';
import type { SimDebugProps, ViewRange } from './sim-debug-root-shared';
// Prop-driven panel subtrees lifted out of the root JSX. The root closure still
// owns all state; these receive the slice they render + the handlers they fire.
import { WaveBand } from './sim-debug-wave';
import { HierarchyPanel, SourceBand } from './sim-debug-panels-side';
import { DebugHeader } from './sim-debug-header';

type CleanPinnedSignal = {
  readonly name: string;
  readonly scope: string;
};

const scopeMatchesLoosely = (a: unknown, b: unknown): boolean => {
  const aa = String(a || '').trim().toLowerCase();
  const bb = String(b || '').trim().toLowerCase();
  if (!aa && !bb) return true;
  if (!aa || !bb) return false;
  return aa === bb || aa.endsWith(`.${bb}`) || bb.endsWith(`.${aa}`);
};

const pinWithModuleWidth = (
  item: CleanPinnedSignal,
  moduleSignals: ModuleSignal[],
  moduleScope: string,
): CleanPinnedSignal => {
  const name = String(item.name || '').trim();
  if (!name || signalRangeOf(name)) return item;
  const leaf = stripSignalRange(name).split('.').pop() || '';
  const matches = moduleSignals.filter(sig => stripSignalRange(sig.name).toLowerCase() === leaf.toLowerCase());
  const scoped = matches.filter(() => scopeMatchesLoosely(item.scope || '', moduleScope));
  const sig = scoped.length === 1 ? scoped[0] : (matches.length === 1 ? matches[0] : null);
  const width = Number(sig?.width || 0);
  return width > 1 ? { ...item, name: `${name}[${width - 1}:0]` } : item;
};

export const SimDebug = ({ view = 'debug', initialTab = '', active = true, preload = false }: SimDebugProps = {}) => {
  const summaryOnly = view === 'summary';
  const dataActive = active || preload;
  const initialTopTab = summaryOnly ? 'summary' : (initialTab || 'wave');
  // Cursors default to null until VCD loads — real positions come from
  // 25 % / 75 % of the actual timeRange (no more 110 / 160 mock values).
  const [waveCursor,  setWaveCursor]  = useState(0);
  const [waveCursorB, setWaveCursorB] = useState(0);
  // View range [start, end] — what slice of the VCD is mapped onto the
  // wave panel width. null = "fit" (whole VCD). Zoom buttons + ctrl+wheel
  // mutate this; "fit" resets it to null.
  const [viewRange, setViewRange] = useState<ViewRange>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [showVcdAnnotations, setShowVcdAnnotations] = useState(false);
  const [vcdAnnotationAxis, setVcdAnnotationAxis] = useState('both');
  // Left panel mode — switch between RTL hierarchy and TB (cocotb) tree.
  const [leftTab, setLeftTab] = useState('rtl');  // 'rtl' | 'tb'
  const [cocotbData, setCocotbData] = useState<any>(null);
  const [simSummary, setSimSummary] = useState<any>(null);
  const [simSummaryLoading, setSimSummaryLoading] = useState(false);
  const [simSummaryError, setSimSummaryError] = useState('');
  const [simSummaryReload, setSimSummaryReload] = useState(0);
  const [selectedSig, setSelectedSig] = useState('mosi');
  const [selectedSigScope, setSelectedSigScope] = useState('');
  const [wavePinnedSignals, setWavePinnedSignals] = useState<PinnedSignal[]>([]);
  const [showSignalHierarchy, setShowSignalHierarchy] = useState(false);
  const waveWidth = 700;

  // ── Live VCD / hierarchy / trace state ──────────────────────────
  // When a real VCD is loaded via /api/vcd, we replace the mock trace
  // list with the parsed signals. Fall back to MOCK_TRACES when no
  // VCD has been picked yet so the panel never shows blank.
  const [vcdFiles, setVcdFiles] = useState<Array<{ path: string }>>([]);
  const [vcdActive, setVcdActive] = useState('');
  const [vcdData, setVcdData] = useState<VcdData | null>(null);   // {signals, samples, timeRange}
  const [timeDisplayUnit, setTimeDisplayUnit] = useState('auto');
  const [cursorMetric, setCursorMetric] = useState('delta');
  const [waveRcName, setWaveRcName] = useState('signal.rc');
  const [waveRcFiles, setWaveRcFiles] = useState<Array<{ name: string; path?: string }>>([]);
  const [waveRcStatus, setWaveRcStatus] = useState('');
  const [hierarchy, setHierarchy] = useState<any>(null);
  const [hierarchyError, setHierarchyError] = useState('');
  const [hierarchyMeta, setHierarchyMeta] = useState<any>(null);
  const [hierarchyLoading, setHierarchyLoading] = useState(false);
  const hierarchyRequestRef = useRef('');
  // Top-level tab — full-width view selector. Replaces the old
  // chip-toggle on the right rail; the user picks which DEBUG MODE
  // to focus on and that mode takes the entire center space.
  //   wave      = source (collapsible) + waveform (the rest)
  //   hierarchy = full-width instance tree
  //   trace     = source + driver/sink list (full width)
  //   summary   = TC pass/fail table from SSOT scenarios + scoreboard
  const [topTab, setTopTab] = useState(initialTopTab); // summary | wave | hierarchy | trace | tb
  const [ipName, setIpName] = useState('');
  const [rtlTop, setRtlTop] = useState('');

  // Auto-detect IP. Two parallel signals are checked:
  //   1) window.ACTIVE_IP / ACTIVE_SESSION — fires immediately on
  //      mount and keeps the panel correctly scoped even when no VCD
  //      has been generated yet (e.g. before /sim runs). Subscribes to
  //      backend session_state events so a workspace switch live-flips
  //      the IP without a manual reload.
  //   2) /api/vcd/list?ip=<ip> — scoped to the active IP only.
  useEffect(() => {
    const seedFromActiveSession = () => {
      const activeIp = activeIpFromAtlasRuntime();
      if (activeIp) setIpName(activeIp);
    };
    seedFromActiveSession();
    if (!g.backend?.subscribe) return undefined;
    const subs: Array<(() => void) | void> = [];
    try {
      subs.push(g.backend.subscribe('session_state', seedFromActiveSession));
    } catch (_) {}
    return () => { subs.forEach(u => { try { u && u(); } catch (_) {} }); };
    // Re-run when the panel becomes active: with the persistent mount the
    // component no longer remounts on each Debug visit, so re-seed the active
    // IP whenever it is shown (catches an IP picked while it was hidden).
  }, [dataActive]);

  useEffect(() => {
    let cancelled = false;
    if (!dataActive || summaryOnly) return () => { cancelled = true; };
    const activeIp = String(ipName || activeIpFromAtlasRuntime()).trim();
    if (!activeIp || activeIp === 'default') {
      setVcdFiles([]);
      setVcdActive('');
      setVcdData(null);
      return () => { cancelled = true; };
    }
    (async () => {
      try {
        const params = appendActiveSessionParam(new URLSearchParams({ ip: activeIp }));
        const r = await fetch('/api/vcd/list?' + params.toString(), {
          cache: 'no-store',
          credentials: 'include',
        });
        const d = await r.json();
        if (cancelled) return;
        const files = (d.files || []).filter((f: { path: string }) => vcdPathBelongsToIp(f.path, activeIp));
        setVcdFiles(files);
        setVcdActive(prev => files.some((f: { path: string }) => f.path === prev) ? prev : (files[0]?.path || ''));
        if (!files.length) setVcdData(null);
      } catch (e) { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [dataActive, summaryOnly, ipName]);

  // Load + parse the active VCD whenever it changes.
  useEffect(() => {
    if (!dataActive || summaryOnly || !vcdActive) return;
    let cancelled = false;
    (async () => {
      try {
        const params = appendActiveSessionParam(new URLSearchParams({ path: vcdActive }));
        const r = await fetch('/api/vcd/raw?' + params.toString(), {
          cache: 'no-store',
          credentials: 'include',
        });
        const d = await r.json();
        if (cancelled) return;
        if (d.content && g.parseVCD) {
          const parsed = g.parseVCD(d.content);
          setVcdData(parsed);
          const inferredTop = inferRtlTopFromVcd(parsed, '');
          if (inferredTop) setRtlTop(prev => prev || inferredTop);
          // Reset view to fit the whole VCD on parse.
          setViewRange(null);
          // Position cursors at sensible spots inside the actual VCD
          // span (25 % and 75 %). Avoids the previous hard-coded 110/160
          // ns which was meaningless for VCDs that don't cover that range.
          const [tMin, tMax] = parsed.timeRange as [number, number];
          const span = tMax - tMin;
          if (span > 0) {
            setWaveCursor (Math.round(tMin + span * 0.25));
            setWaveCursorB(Math.round(tMin + span * 0.75));
          }
        }
      } catch (e) { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [dataActive, summaryOnly, vcdActive]);

  // Fetch cocotb env info whenever IP changes (used by left-panel TB tab).
  useEffect(() => {
    const wantsCocotb = dataActive && (leftTab === 'tb' || summaryOnly || topTab === 'summary');
    if (!ipName || !wantsCocotb) {
      if (!ipName) setCocotbData(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const cocotbParams = appendActiveSessionParam(new URLSearchParams({ ip: ipName }));
        const r = await fetch('/api/cocotb?' + cocotbParams.toString());
        const d = await r.json();
        if (!cancelled) setCocotbData(d);
      } catch (_) { if (!cancelled) setCocotbData(null); }
    })();
    return () => { cancelled = true; };
  }, [dataActive, leftTab, summaryOnly, topTab, ipName]);

  // Fetch TC pass/fail rollup for the Sim Summary tab. The backend
  // merges SSOT scenarios with scoreboard_events.jsonl, and also
  // includes scoreboard-only IDs so failed generated tests are not hidden.
  useEffect(() => {
    const wantsSummary = dataActive && (summaryOnly || topTab === 'summary');
    if (!ipName || !wantsSummary) {
      setSimSummary(null);
      setSimSummaryError('');
      setSimSummaryLoading(false);
      return;
    }
    let cancelled = false;
    setSimSummaryLoading(true);
    (async () => {
      try {
        const scParams = appendActiveSessionParam(new URLSearchParams({ ip: ipName }));
        const r = await fetch('/api/debug/scenarios?' + scParams.toString(), { cache: 'no-store' });
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
  }, [dataActive, summaryOnly, topTab, ipName, simSummaryReload]);

  useEffect(() => {
    setRtlTop('');
    setRemovedSignals([]);
    setWaveRowSel([]);
    setWavePinnedSignals([]);
    setSignalOrder([]);
    setHierarchy(null);
    setHierarchyMeta(null);
    setHierarchyError('');
    setHierarchyLoading(false);
    setSimSummary(null);
    setCocotbData(null);
    hierarchyRequestRef.current = '';
  }, [ipName]);

  // Fetch hierarchy when IP is known. The UI is scoped by IP directory, but
  // elaboration must use the real RTL top from tb_manifest/SSOT/VCD scope.
  useEffect(() => {
    if (!dataActive || summaryOnly || !ipName) return;
    let cancelled = false;
    const topForHierarchy = rtlTop || ipName;
    const requestKey = `${ipName}::${topForHierarchy}`;
    if (hierarchyRequestRef.current === requestKey && hierarchyMeta) return;
    hierarchyRequestRef.current = requestKey;
    setHierarchyLoading(true);
    (async () => {
      try {
        const r = await fetch('/api/hierarchy?top=' + encodeURIComponent(topForHierarchy) +
                              '&ip=' + encodeURIComponent(ipName));
        const d = await r.json();
        if (cancelled) return;
        setHierarchyMeta(d);
        const resolvedTop = d?.resolved_top || d?.tree?.module || '';
        if (resolvedTop) hierarchyRequestRef.current = `${ipName}::${resolvedTop}`;
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
      } finally {
        if (!cancelled) setHierarchyLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [dataActive, summaryOnly, ipName, rtlTop, hierarchyMeta]);

  const hierarchyBackendLabel = useMemo(() => {
    const backend = String(hierarchyMeta?.backend || '').trim();
    const primary = String(hierarchyMeta?.primary_backend || '').trim();
    const display = (backend === 'dual' || backend === 'pyslang+verilator')
      ? 'pyslang + verilator'
      : (backend || 'pyslang + verilator');
    const primarySuffix = primary ? ` (${primary})` : '';
    const topSuffix = rtlTop && rtlTop !== ipName ? ` · top ${rtlTop}` : '';
    return ipName ? `${display}${primarySuffix} · ${ipName}${topSuffix}` : `${display}${primarySuffix}`;
  }, [hierarchyMeta, ipName, rtlTop]);

  const hierarchyBackendTitle = useMemo(() => {
    const results = hierarchyMeta?.backend_results || [];
    if (!Array.isArray(results) || !results.length) return 'RTL hierarchy dual elaboration';
    return results.map((r: any) => {
      const state = r.ok ? 'ok' : (r.error ? `error: ${r.error}` : 'no result');
      return `${r.backend}: ${state}`;
    }).join('\n');
  }, [hierarchyMeta]);

  // Signals removed from the waveform (clicked + Delete/Backspace). Filtered
  // out of the trace list; re-adding a signal clears it from here.
  const [removedSignals, setRemovedSignals] = useState<PinnedSignal[]>([]);
  // Selection inside the waveform viewer itself. This is separate from the
  // signal-palette selection so Delete can remove multiple visible wave rows.
  const [waveRowSel, setWaveRowSel] = useState<PinnedSignal[]>([]);
  useEffect(() => { setWaveRowSel([]); }, [vcdActive]);
  // User-defined row order (waveSignalKey list) from drag-reordering in the
  // waveform. Rows not in the list keep their default position after it.
  const [signalOrder, setSignalOrder] = useState<string[]>([]);
  // Per-signal decoration (agent- or right-click-driven): a color override and
  // a group tag, both keyed by NORMALIZED signal name (alias-resolved at render
  // so an agent's full path and a UI row ident both resolve). groupState holds
  // per-tag fold + color. See sim-debug-helpers buildWaveDisplayRows.
  const [signalColors, setSignalColors] = useState<Record<string, string>>({});
  const [signalRadices, setSignalRadices] = useState<Record<string, string>>({});
  const [paramValueMap, setParamValueMap] = useState<Record<string, string>>({});
  const [signalTags, setSignalTags] = useState<Record<string, string>>({});
  const [groupState, setGroupState] = useState<WaveGroupState>({});

  // Build the traceList — real VCD signals only. The default view stays
  // compact (first 24), while Ctrl+W can pin a selected signal beyond
  // that window into the waveform. Explicitly-removed signals are dropped;
  // remaining rows are ordered by any drag-reordering the user applied.
  const traceList = useMemo(() => {
    let rows = buildWaveTraceList(vcdData, wavePinnedSignals, 24);
    if (removedSignals.length) {
      rows = rows.filter(r => !removedSignals.some(rm => waveSignalMatches(r, rm.name, rm.scope)));
    }
    if (signalOrder.length) {
      const rank = new Map(signalOrder.map((k, i) => [k, i]));
      rows = rows
        .map((r, i) => ({ r, i }))
        .sort((a, b) => {
          const ra = rank.has(waveSignalKey(a.r)) ? (rank.get(waveSignalKey(a.r)) as number) : signalOrder.length + a.i;
          const rb = rank.has(waveSignalKey(b.r)) ? (rank.get(waveSignalKey(b.r)) as number) : signalOrder.length + b.i;
          return ra - rb;
        })
        .map(x => x.r);
    }
    return rows;
  }, [vcdData, wavePinnedSignals, removedSignals, signalOrder]);

  // Drag-reorder in the waveform → store the new full key order.
  const onReorderSignal = useCallback((orderedKeys: string[]) => {
    setSignalOrder(orderedKeys);
  }, []);

  const normName = (n: string) => stripSignalRange(n).toLowerCase();
  const sameSignalSpec = useCallback((a: PinnedSignal, b: PinnedSignal) =>
    stripSignalRange(a.name).toLowerCase() === stripSignalRange(b.name).toLowerCase()
    && signalRangeOf(a.name).toLowerCase() === signalRangeOf(b.name).toLowerCase()
    && String(a.scope || '').trim() === String(b.scope || '').trim(), []);

  // Move a signal row up/down by one (right-click menu). Seeds the order from
  // the currently-visible order, swaps with the neighbour, persists it.
  const moveSignalKey = useCallback((key: string, dir: number) => {
    const keys = traceList.map(waveSignalKey);
    const i = keys.indexOf(key);
    const j = i + dir;
    if (i < 0 || j < 0 || j >= keys.length) return;
    const nk = keys.slice();
    [nk[i], nk[j]] = [nk[j], nk[i]];
    setSignalOrder(nk);
  }, [traceList]);

  // Agent: reorder by signal NAME — matched rows lead in the given order, the
  // rest keep their relative order. (Operates on already-shown rows.)
  const reorderByNames = useCallback((names: string[]) => {
    const want = (names || []).map(normName).filter(Boolean);
    if (!want.length) return;
    const keys = traceList.map(waveSignalKey);
    const lead: string[] = [];
    for (const n of want) {
      const row = traceList.find(r => waveSignalMatches(r, n));
      if (row) { const k = waveSignalKey(row); if (!lead.includes(k)) lead.push(k); }
    }
    if (!lead.length) return;
    setSignalOrder([...lead, ...keys.filter(k => !lead.includes(k))]);
  }, [traceList]);

  const setSignalColorByNames = useCallback((names: string[], color: string | null) => {
    setSignalColors(prev => {
      const out = { ...prev };
      for (const n of names || []) {
        const k = normName(n);
        if (!k) continue;
        if (color) out[k] = color; else delete out[k];
      }
      return out;
    });
  }, []);

  const setSignalRadixByNames = useCallback((names: string[], radix: string | null) => {
    setSignalRadices(prev => {
      const out = { ...prev };
      for (const n of names || []) {
        const k = normName(n);
        if (!k) continue;
        if (radix) out[k] = radix; else delete out[k];
      }
      return out;
    });
  }, []);

  const assignGroupByNames = useCallback((names: string[], tag: string, color?: string | null) => {
    const t = String(tag || '').trim();
    if (!t) return;
    setSignalTags(prev => {
      const out = { ...prev };
      for (const n of names || []) { const k = normName(n); if (k) out[k] = t; }
      return out;
    });
    setGroupState(prev => ({ ...prev, [t]: { folded: prev[t]?.folded ?? false, color: color || prev[t]?.color } }));
  }, []);

  const ungroupByNames = useCallback((names: string[]) => {
    setSignalTags(prev => {
      const out = { ...prev };
      for (const n of names || []) delete out[normName(n)];
      return out;
    });
  }, []);

  const toggleGroupFold = useCallback((tag: string, folded?: boolean) => {
    const t = String(tag || '').trim();
    if (!t) return;
    setGroupState(prev => ({
      ...prev,
      [t]: { ...(prev[t] || { folded: false }), folded: folded == null ? !(prev[t]?.folded) : folded },
    }));
  }, []);

  const renameGroup = useCallback((oldTag: string, newTag: string) => {
    const o = String(oldTag || '').trim();
    const n = String(newTag || '').trim();
    if (!o || !n || o === n) return;
    setSignalTags(prev => {
      const out: Record<string, string> = {};
      for (const k in prev) out[k] = prev[k] === o ? n : prev[k];
      return out;
    });
    setGroupState(prev => {
      const out = { ...prev };
      if (out[o]) { out[n] = { ...out[o], ...(out[n] || {}) }; delete out[o]; }
      return out;
    });
  }, []);

  const setGroupColor = useCallback((tag: string, color: string | null) => {
    const t = String(tag || '').trim();
    if (!t) return;
    setGroupState(prev => ({ ...prev, [t]: { ...(prev[t] || { folded: false }), color: color || undefined } }));
  }, []);

  // Decoration bundle handed to the wave band (state + mutators) so the
  // WaveBand props stay manageable.
  const waveDecor = useMemo(() => ({
    colors: signalColors,
    radices: signalRadices,
    paramValueMap,
    tags: signalTags,
    groups: groupState,
    setSignalColor: setSignalColorByNames,
    setSignalRadix: setSignalRadixByNames,
    moveSignal: moveSignalKey,
    assignGroup: assignGroupByNames,
    ungroup: ungroupByNames,
    toggleFold: toggleGroupFold,
    renameGroup,
    setGroupColor,
  }), [signalColors, signalRadices, paramValueMap, signalTags, groupState, setSignalColorByNames, setSignalRadixByNames, moveSignalKey,
       assignGroupByNames, ungroupByNames, toggleGroupFold, renameGroup, setGroupColor]);

  const normalizeWaveRcName = useCallback((name: string) => {
    const leaf = String(name || 'signal.rc').trim().split(/[\\/]/).pop() || 'signal.rc';
    return leaf.endsWith('.rc') ? leaf : `${leaf}.rc`;
  }, []);

  const refreshWaveRcFiles = useCallback(async () => {
    if (!ipName) {
      setWaveRcFiles([]);
      return;
    }
    try {
      const params = appendActiveSessionParam(new URLSearchParams({ ip: ipName }));
      const r = await fetch('/api/vcd/rc/list?' + params.toString(), {
        cache: 'no-store',
        credentials: 'include',
      });
      const d = await r.json();
      setWaveRcFiles(Array.isArray(d?.files) ? d.files : []);
    } catch (_) {
      setWaveRcFiles([]);
    }
  }, [ipName]);

  useEffect(() => {
    if (!dataActive || summaryOnly || !ipName) return;
    refreshWaveRcFiles();
  }, [dataActive, summaryOnly, ipName, refreshWaveRcFiles]);

  const currentWaveRcSnapshot = useCallback(() => ({
    version: 1,
    vcdActive,
    pins: wavePinnedSignals,
    removed: removedSignals,
    order: signalOrder,
    colors: signalColors,
    radices: signalRadices,
    tags: signalTags,
    groups: groupState,
    cursors: { a: waveCursor, b: waveCursorB },
    viewRange,
    timeDisplayUnit,
    showSignalHierarchy,
    selected: { name: selectedSig, scope: selectedSigScope },
  }), [
    vcdActive, wavePinnedSignals, removedSignals, signalOrder, signalColors,
    signalRadices, signalTags, groupState, waveCursor, waveCursorB, viewRange,
    timeDisplayUnit, showSignalHierarchy, selectedSig, selectedSigScope,
  ]);

  const restoreWaveRcSnapshot = useCallback((raw: any) => {
    const payload = raw?.kind === 'sim_debug_wave_rc' && raw?.payload ? raw.payload : (raw?.payload || raw);
    if (!payload || typeof payload !== 'object') {
      setWaveRcStatus('error: invalid rc');
      return;
    }
    const objectOrEmpty = (v: any) => (v && typeof v === 'object' && !Array.isArray(v)) ? v : {};
    setWavePinnedSignals(Array.isArray(payload.pins) ? payload.pins : []);
    setRemovedSignals(Array.isArray(payload.removed) ? payload.removed : []);
    setSignalOrder(Array.isArray(payload.order) ? payload.order : []);
    setSignalColors(objectOrEmpty(payload.colors));
    setSignalRadices(objectOrEmpty(payload.radices));
    setSignalTags(objectOrEmpty(payload.tags));
    setGroupState(objectOrEmpty(payload.groups));
    if (Array.isArray(payload.viewRange) && payload.viewRange.length === 2) {
      const a = Number(payload.viewRange[0]);
      const b = Number(payload.viewRange[1]);
      if (Number.isFinite(a) && Number.isFinite(b) && Math.abs(b - a) >= 1) setViewRange([Math.min(a, b), Math.max(a, b)]);
    } else {
      setViewRange(null);
    }
    const a = Number(payload.cursors?.a);
    const b = Number(payload.cursors?.b);
    if (Number.isFinite(a)) setWaveCursor(a);
    if (Number.isFinite(b)) setWaveCursorB(b);
    if (payload.timeDisplayUnit) setTimeDisplayUnit(String(payload.timeDisplayUnit));
    if (typeof payload.showSignalHierarchy === 'boolean') setShowSignalHierarchy(payload.showSignalHierarchy);
    if (payload.selected?.name) {
      setSelectedSig(String(payload.selected.name));
      setSelectedSigScope(String(payload.selected.scope || ''));
    }
    setWaveRowSel([]);
    setTopTab('wave');
  }, []);

  const saveWaveRc = useCallback(async () => {
    if (!ipName) {
      setWaveRcStatus('error: no ip');
      return;
    }
    const name = normalizeWaveRcName(waveRcName);
    setWaveRcName(name);
    setWaveRcStatus('saving...');
    try {
      const params = appendActiveSessionParam(new URLSearchParams({ ip: ipName, name }));
      const r = await fetch('/api/vcd/rc/save?' + params.toString(), {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload: currentWaveRcSnapshot() }),
      });
      const d = await r.json();
      if (!r.ok || d?.error) throw new Error(d?.error || `HTTP ${r.status}`);
      setWaveRcStatus(`saved ${d.name || name}`);
      refreshWaveRcFiles();
    } catch (e) {
      setWaveRcStatus(`error: ${String(e).replace(/^Error:\s*/, '')}`);
    }
  }, [ipName, waveRcName, normalizeWaveRcName, currentWaveRcSnapshot, refreshWaveRcFiles]);

  const restoreWaveRc = useCallback(async () => {
    if (!ipName) {
      setWaveRcStatus('error: no ip');
      return;
    }
    const name = normalizeWaveRcName(waveRcName);
    setWaveRcName(name);
    setWaveRcStatus('loading...');
    try {
      const params = appendActiveSessionParam(new URLSearchParams({ ip: ipName, name }));
      const r = await fetch('/api/vcd/rc/load?' + params.toString(), {
        cache: 'no-store',
        credentials: 'include',
      });
      const d = await r.json();
      if (!r.ok || d?.error) throw new Error(d?.error || `HTTP ${r.status}`);
      restoreWaveRcSnapshot(d.payload);
      setWaveRcStatus(`restored ${d.name || name}`);
    } catch (e) {
      setWaveRcStatus(`error: ${String(e).replace(/^Error:\s*/, '')}`);
    }
  }, [ipName, waveRcName, normalizeWaveRcName, restoreWaveRcSnapshot]);

  // Remove one or more signals from the waveform. Also unpins them so pinned
  // rows do not immediately reappear. A scope-qualified item removes exactly
  // that row; an unscoped item keeps the legacy "match by leaf" behavior.
  const removeSignalsFromWave = useCallback((items: PinnedSignal[]) => {
    const clean = (items || [])
      .map(it => ({ name: String(it.name || '').trim(), scope: String(it.scope || '').trim() }))
      .filter(it => it.name);
    if (!clean.length) return;
    setRemovedSignals(prev => {
      const out = [...prev];
      for (const it of clean) if (!out.some(rm => sameSignalSpec(rm, it))) out.push(it);
      return out;
    });
    setWavePinnedSignals(prev => prev.filter(p => !clean.some(it => sameSignalSpec(p, it))));
    setWaveRowSel([]);
  }, [sameSignalSpec]);

  const removeSelectedFromWave = useCallback(() => {
    if (waveRowSel.length) {
      removeSignalsFromWave(waveRowSel);
      return;
    }
    const name = String(selectedSig || '').trim();
    if (!name) return;
    removeSignalsFromWave([{ name, scope: String(selectedSigScope || '').trim() }]);
  }, [waveRowSel, selectedSig, selectedSigScope, removeSignalsFromWave]);

  // ── Resizable splitter state ─────────────────────────────────────
  // The user can drag boundaries between hierarchy / source / wave.
  // Double-click each splitter handle to collapse/restore its panel.
  // Expand-mode buttons (only-source / only-wave) hide the other panes
  // entirely.
  const [leftW, setLeftW] = useState(220);   // hierarchy column width
  const [topH, setTopH] = useState(0.5);     // source band height as fraction of body
  const [expand, setExpand] = useState('split'); // split | wave | source | hierarchy

  // ── Zoom helpers ─────────────────────────────────────────────────
  // Effective visible time window. When viewRange is null we fall back
  // to the full VCD timeRange. tToX() in debug-shared.jsx reads from
  // window.WAVE_TIME_START/END so we mirror the effective range there
  // every render.
  const effRange: [number, number] = useMemo(() => {
    if (viewRange) return viewRange;
    if (vcdData) return [vcdData.timeRange![0], vcdData.timeRange![1]];
    return [0, 200];
  }, [viewRange, vcdData]);

  // Sync the window-scoped time range BEFORE children render, so
  // tToX() in debug-shared.jsx reads the up-to-date view on every
  // zoom. Doing this in useEffect would be one paint behind.
  if (typeof window !== 'undefined') {
    g.WAVE_TIME_START = effRange[0];
    g.WAVE_TIME_END   = effRange[1];
  }

  const zoomIn  = useCallback(() => {
    const [s, e] = effRange;
    const span = e - s;
    const center = (waveCursor != null && waveCursor >= s && waveCursor <= e) ? waveCursor : (s + e) / 2;
    const ns = Math.max(s, center - span * 0.25);
    const ne = Math.min(e, center + span * 0.25);
    if (ne - ns < 1) return;
    setViewRange([ns, ne]);
  }, [effRange, waveCursor]);

  const zoomOut = useCallback(() => {
    if (!vcdData) return;
    const [s, e] = effRange;
    const span = e - s;
    const center = (s + e) / 2;
    const [vs, ve] = vcdData.timeRange as [number, number];
    const ns = Math.max(vs, center - span);
    const ne = Math.min(ve, center + span);
    if (ns === vs && ne === ve) { setViewRange(null); return; }
    setViewRange([ns, ne]);
  }, [effRange, vcdData]);

  const zoomFit = useCallback(() => setViewRange(null), []);

  const zoomToCursors = useCallback(() => {
    const a = Math.min(waveCursor, waveCursorB);
    const b = Math.max(waveCursor, waveCursorB);
    if (b - a < 1) return;
    const pad = (b - a) * 0.1;
    setViewRange([a - pad, b + pad]);
  }, [waveCursor, waveCursorB]);

  // Pan left/right by 25 % of the current window. Clamped to the full
  // VCD range. Used by Arrow keys and the (future) drag-to-pan handler.
  const panBy = useCallback((fraction: number) => {
    if (!vcdData) return;
    const [s, e] = effRange;
    const span = e - s;
    const delta = span * fraction;
    const [vs, ve] = vcdData.timeRange as [number, number];
    let ns = s + delta;
    let ne = e + delta;
    if (ns < vs) { ne += vs - ns; ns = vs; }
    if (ne > ve) { ns -= ne - ve; ne = ve; }
    setViewRange([Math.max(vs, ns), Math.min(ve, ne)]);
  }, [effRange, vcdData]);


  // Multi-selection in the signal pane: Ctrl/⌘+click toggles, Shift+click
  // range-selects. The whole set can be added to the wave at once (Ctrl+W,
  // the "add to wave" button, or the right-click "Add N to waveform").
  const [waveSel, setWaveSel] = useState<PinnedSignal[]>([]);
  const moduleWidthLookupRef = useRef<{ signals: ModuleSignal[]; scope: string }>({ signals: [], scope: '' });

  // Pin one or more explicit signals to the waveform. Dedupes on name+scope,
  // then jumps to the Wave tab so the user sees the traces appear.
  const pinSignalsToWave = useCallback((items: PinnedSignal[]) => {
    const widthLookup = moduleWidthLookupRef.current;
    const clean = (items || [])
      .map(it => ({ name: String(it.name || '').trim(), scope: String(it.scope || '').trim() }))
      .map(it => pinWithModuleWidth(it, widthLookup.signals, widthLookup.scope))
      .filter(it => it.name);
    if (!clean.length) return;
    setWavePinnedSignals(prev => {
      const out = [...(prev || [])];
      for (const it of clean) {
        const already = out.some(pin => sameSignalSpec(pin, it));
        if (!already) out.push(it);
      }
      return out;
    });
    // Re-adding a previously-removed signal must bring it back even when the
    // re-add name form differs from how it was removed (keep/clear store the VCD
    // leaf+scope; chat/source re-add a fully-qualified path under a different
    // hierarchy). See removedSignalsAfterReAdd.
    const allRows = (vcdData?.signals || []).map(s => waveRowFromVcdSignal(vcdData!, s));
    setRemovedSignals(prev => removedSignalsAfterReAdd(allRows, prev, clean));
    setTopTab('wave');
  }, [sameSignalSpec, vcdData]);

  const pinSignalToWave = useCallback((rawName: string, rawScope = '') => {
    pinSignalsToWave([{ name: rawName, scope: rawScope }]);
  }, [pinSignalsToWave]);

  // "keep only these" — the agent can't enumerate what's currently displayed
  // (default VCD rows it never added), so removal happens HERE against the live
  // traceList: pin the kept signals, then drop every other displayed row.
  const rowToSpec = useCallback((r: VcdSignal): PinnedSignal => ({
    name: String(r.name || r.signalName || '').trim(),
    scope: String(r.scope || '').trim(),
  }), []);
  const keepOnlySignals = useCallback((keep: PinnedSignal[]) => {
    const keepClean = (keep || [])
      .map(it => ({ name: String(it.name || '').trim(), scope: String(it.scope || '').trim() }))
      .filter(it => it.name);
    if (!keepClean.length) return;
    pinSignalsToWave(keepClean);  // reveal the kept signals if not already shown
    const drop = traceList
      .filter(r => !keepClean.some(k => waveSignalMatches(r, k.name, k.scope)))
      .map(rowToSpec)
      .filter(it => it.name);
    if (drop.length) removeSignalsFromWave(drop);
  }, [traceList, pinSignalsToWave, removeSignalsFromWave, rowToSpec]);
  const clearWaveSignals = useCallback(() => {
    const drop = traceList.map(rowToSpec).filter(it => it.name);
    if (drop.length) removeSignalsFromWave(drop);
  }, [traceList, removeSignalsFromWave, rowToSpec]);

  // Ctrl+W: add the whole multi-selection when there is one, else the single
  // focused signal.
  const addSelectedSignalToWave = useCallback(() => {
    if (waveSel.length) pinSignalsToWave(waveSel);
    else pinSignalToWave(selectedSig, selectedSigScope);
  }, [waveSel, pinSignalsToWave, pinSignalToWave, selectedSig, selectedSigScope]);

  // ── Keyboard shortcuts (Verdi-ish) ───────────────────────────────
  // Active only while sim_debug has focus AND user isn't typing in
  // an input/textarea/contenteditable.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!active) return;  // panel hidden (other tab) — don't grab global keys
      const tag = (e.target && (e.target as HTMLElement).tagName) || '';
      if (tag === 'INPUT' || tag === 'TEXTAREA' || (e.target && (e.target as HTMLElement).isContentEditable)) return;
      const key = String(e.key || '').toLowerCase();
      if (e.ctrlKey && !e.metaKey && !e.altKey && key === 'w') {
        e.preventDefault();
        e.stopPropagation();
        if (vcdData) addSelectedSignalToWave();
        return;
      }
      if (!vcdData) return;
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
        case 'h': case 'H':
          setShowSignalHierarchy(v => !v); break;
        case 'Delete': case 'Backspace':
          // Mac has no forward-delete: the key labelled "delete" sends
          // Backspace, so accept both. Removes selected waveform rows, falling
          // back to the focused signal when there is no waveform multi-select.
          if (waveRowSel.length || selectedSig) removeSelectedFromWave(); else handled = false;
          break;
        case 'ArrowLeft':
          panBy(e.shiftKey ? -0.5 : -0.25); break;
        case 'ArrowRight':
          panBy(e.shiftKey ? 0.5 : 0.25); break;
        case 'Home':
          if (vcdData) setViewRange([vcdData.timeRange![0], vcdData.timeRange![0] + (effRange[1] - effRange[0])]);
          break;
        case 'End':
          if (vcdData) {
            const span = effRange[1] - effRange[0];
            setViewRange([vcdData.timeRange![1] - span, vcdData.timeRange![1]]);
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
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, [active, vcdData, effRange, zoomIn, zoomOut, zoomFit, zoomToCursors, panBy, addSelectedSignalToWave, waveRowSel.length, selectedSig, removeSelectedFromWave]);

  // ── Source viewer state ──────────────────────────────────────────
  // Replaces the hard-coded mock srcRange. When the user clicks a
  // module in the hierarchy, we fetch <ip>/rtl/<module>.sv via
  // /api/source. When they click a signal in the wave panel, we hit
  // /api/trace first to resolve driver file:line, then fetch that file
  // and scroll to that line.
  const [srcLines, setSrcLines] = useState<string[]>([]);   // string[] (full file)
  const [srcPath, setSrcPath]   = useState('');
  const [srcCursor, setSrcCursor] = useState(0);  // 1-based line; 0 = none
  const [srcModule, setSrcModule] = useState(''); // for hierarchy highlight
  const [srcLoading, setSrcLoading] = useState(false);
  useEffect(() => {
    setParamValueMap(parseVerilogParamValueMap(srcLines));
  }, [srcLines]);

  const loadSourceFile = useCallback(async (path: string, cursorLine?: number) => {
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

  // RTL module-signal feature (per-module port + internal net/var list, the
  // in/out/internal filter, rtl/vcd source toggle, and the signal-click
  // handler) lives in its own hook to keep this root closure lean.
  const {
    moduleSignals, moduleSignalsModule, moduleSignalsScope, moduleSignalsLoading,
    moduleSignalsError, signalFilter, setSignalFilter, signalSource, setSignalSource,
    loadModuleSignals, onSelectModuleSignal,
  } = useModuleSignals({ ipName, rtlTop, loadSourceFile, setSelectedSig, setSelectedSigScope });
  moduleWidthLookupRef.current = { signals: moduleSignals, scope: moduleSignalsScope };

  const sourceSignalScope = useMemo(() => {
    if (!srcPath || !moduleSignalsScope || !moduleSignals.length) return '';
    const currentPath = normalizeProjectSourcePath(srcPath);
    const belongsToLoadedModule = moduleSignals.some(sig => {
      const file = String(sig.file || sig.file_line || '').replace(/:\d+$/, '');
      return file && normalizeProjectSourcePath(file) === currentPath;
    });
    return belongsToLoadedModule ? moduleSignalsScope : '';
  }, [srcPath, moduleSignals, moduleSignalsScope]);

  // Hierarchy click → load the SV file that ACTUALLY defines the
  // module. Uses ONLY the elaborator's `module_files` map. No filename
  // convention fallback — that picks empty stubs (e.g. `gpio_pad.sv`)
  // when the real implementation lives in `gpio_pad_wrapper.sv`. If
  // elab fails, surface the error rather than guessing.
  const onSelectModule = useCallback((moduleName?: string, instancePath?: string, opts?: { loadSignals?: boolean }) => {
    if (!moduleName || !ipName) return;
    setSrcModule(moduleName);
    if (opts?.loadSignals !== false) loadModuleSignals(moduleName);
    (async () => {
      try {
        const useHierarchyPayload = async (d: any) => {
          if (d?.error) {
            setSrcLines([`// elab error: ${d.error}`,
                         `// backend: ${d.backend || '?'}`]);
            setSrcPath('');
            return true;
          }
          const mf = d?.module_files?.[moduleName];
          if (!mf || !mf.file) return false;
          const rel = normalizeProjectSourcePath(mf.file);
          await loadSourceFile(rel, mf.line);
          return true;
        };
        if (await useHierarchyPayload(hierarchyMeta)) return;
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
  }, [ipName, rtlTop, hierarchyMeta, loadSourceFile, loadModuleSignals]);

  // Wave signal click → /api/trace returns driver file_line; fetch + scroll.
  // Clicking a wave signal only SELECTS it (highlight). It deliberately does
  // NOT auto-trace/jump the source — following to RTL is explicit (right-click
  // → Go to driver / Trace, or the command bar).
  const onSelectWaveSignal = useCallback((signalName: string, signalScope = '') => {
    setSelectedSig(signalName);
    setSelectedSigScope(signalScope || '');
  }, []);

  const [traceResult, setTraceResult] = useState<any>(null);

  // Explicit "Go to driver": trace the signal and jump the source to its driver.
  const goToDriver = useCallback(async (signalName: string, signalScope = '') => {
    setSelectedSig(signalName);
    setSelectedSigScope(signalScope || '');
    if (!signalName || !ipName) return;
    try {
      const r = await fetch(
        `/api/trace?signal=${encodeURIComponent(signalName)}` +
        `&top=${encodeURIComponent(rtlTop || ipName)}&ip=${encodeURIComponent(ipName)}` +
        (signalScope ? `&scope=${encodeURIComponent(signalScope)}` : ''));
      const d = await r.json();
      const drivers = Array.isArray(d?.drivers) ? d.drivers : (d?.driver ? [d.driver] : []);
      const drv = drivers[0] || null;
      if (drv && drv.file_line) {
        const m = String(drv.file_line).match(/^(.*):(\d+)$/);
        if (m) await loadSourceFile(normalizeProjectSourcePath(m[1]), parseInt(m[2], 10));
      }
    } catch (e) { /* trace failed; keep current source */ }
  }, [ipName, rtlTop, loadSourceFile]);

  // Explicit "Go to first load": trace the signal and jump to its first sink.
  const goToFirstLoad = useCallback(async (signalName: string, signalScope = '') => {
    const name = String(signalName || '').trim();
    setSelectedSig(name);
    setSelectedSigScope(signalScope || '');
    if (!name || !ipName) return;
    setTraceResult({ signal: name, scope: signalScope || '', loading: true, driver: null, drivers: [], sinks: [] });
    try {
      const r = await fetch(
        `/api/trace?signal=${encodeURIComponent(name)}` +
        `&top=${encodeURIComponent(rtlTop || ipName)}&ip=${encodeURIComponent(ipName)}` +
        (signalScope ? `&scope=${encodeURIComponent(signalScope)}` : ''));
      const d = await r.json();
      const sinks = Array.isArray(d?.sinks) ? d.sinks : [];
      const sk = sinks[0] || null;
      if (sk && sk.file_line) {
        const m = String(sk.file_line).match(/^(.*):(\d+)$/);
        if (m) await loadSourceFile(normalizeProjectSourcePath(m[1]), parseInt(m[2], 10));
      }
      const drivers = Array.isArray(d?.drivers) ? d.drivers : (d?.driver ? [d.driver] : []);
      setTraceResult({
        signal: name, scope: signalScope || '', loading: false,
        driver: drivers[0] || null, drivers,
        driver_count: d?.driver_count ?? drivers.length,
        sinks,
        sink_count: d?.sink_count ?? sinks.length,
        error: d?.error || '', backend: d?.backend || '',
      });
    } catch (e) {
      setTraceResult({ signal: name, scope: signalScope || '', loading: false, driver: null, drivers: [], sinks: [], error: String(e) });
    }
  }, [ipName, rtlTop, loadSourceFile]);

  // Right-click "Trace driver/loads" → pyslang /api/trace. Unlike plain
  // signal selection, this keeps the
  // full {drivers, sinks} result so the pane can render a follow-the-fanout
  // popover the user clicks through.
  const runSignalTrace = useCallback(async (signalName: string, signalScope = '') => {
    const name = String(signalName || '').trim();
    if (!name || !ipName) return;
    setSelectedSig(name);
    setSelectedSigScope(signalScope || '');
    setTraceResult({ signal: name, scope: signalScope || '', loading: true, driver: null, drivers: [], sinks: [] });
    try {
      const r = await fetch(
        `/api/trace?signal=${encodeURIComponent(name)}` +
        `&top=${encodeURIComponent(rtlTop || ipName)}&ip=${encodeURIComponent(ipName)}` +
        (signalScope ? `&scope=${encodeURIComponent(signalScope)}` : ''));
      const d = await r.json();
      const drivers = Array.isArray(d?.drivers) ? d.drivers : (d?.driver ? [d.driver] : []);
      setTraceResult({
        signal: name, scope: signalScope || '', loading: false,
        driver: drivers[0] || null, drivers,
        driver_count: d?.driver_count ?? drivers.length,
        sinks: Array.isArray(d?.sinks) ? d.sinks : [],
        sink_count: d?.sink_count ?? (Array.isArray(d?.sinks) ? d.sinks.length : 0),
        error: d?.error || '', backend: d?.backend || '',
      });
      // Auto-follow to the driver so the source view lands somewhere useful.
      const fl = drivers[0]?.file_line;
      const m = fl && String(fl).match(/^(.*):(\d+)$/);
      if (m) await loadSourceFile(normalizeProjectSourcePath(m[1]), parseInt(m[2], 10));
    } catch (e) {
      setTraceResult({ signal: name, scope: signalScope || '', loading: false, driver: null, drivers: [], sinks: [], error: String(e) });
    }
  }, [ipName, rtlTop, loadSourceFile]);

  // ── Source-code signal interaction ───────────────────────────────
  // Click an identifier in the source → focus it (Ctrl+W then adds it);
  // double-click → add straight to the wave; right-click → a small menu
  // (add / trace driver+loads / go to driver). Use the current RTL instance
  // scope when known so common source identifiers resolve to the right VCD row.
  const [srcSigMenu, setSrcSigMenu] = useState<{ name: string; scope: string; x: number; y: number; selSignals?: string[] } | null>(null);
  const onSourcePickSignal = useCallback((name: string) => {
    setSelectedSig(name);
    setSelectedSigScope(sourceSignalScope);
    setWaveSel(name ? [{ name, scope: sourceSignalScope }] : []);
  }, [sourceSignalScope]);
  const onSourceAddSignal = useCallback((name: string) => {
    setSelectedSig(name);
    setSelectedSigScope(sourceSignalScope);
    setWaveSel(name ? [{ name, scope: sourceSignalScope }] : []);
    pinSignalToWave(name, sourceSignalScope);
  }, [pinSignalToWave, sourceSignalScope]);
  const onSourceSelectSignals = useCallback((names: string[]) => {
    const items = (names || [])
      .map(name => ({ name: String(name || '').trim(), scope: sourceSignalScope }))
      .filter(item => item.name);
    setWaveSel(items);
  }, [sourceSignalScope]);
  // Drag identifiers from the source and release over the waveform → add them.
  const onSourceDropToWave = useCallback((names: string[]) => {
    const items = (names || [])
      .map(name => ({ name: String(name || '').trim(), scope: sourceSignalScope }))
      .filter(item => item.name);
    if (items.length) pinSignalsToWave(items);
  }, [pinSignalsToWave, sourceSignalScope]);
  const onSourceSignalContextMenu = useCallback((name: string, x: number, y: number, selSignals?: string[]) => {
    if (name) { setSelectedSig(name); setSelectedSigScope(sourceSignalScope); }
    if (selSignals && selSignals.length) {
      setWaveSel(selSignals.map(s => ({ name: s, scope: sourceSignalScope })).filter(s => s.name));
    } else if (name) {
      setWaveSel([{ name, scope: sourceSignalScope }]);
    }
    setSrcSigMenu({ name, scope: sourceSignalScope, x, y, selSignals: (selSignals || []).filter(Boolean) });
  }, [sourceSignalScope]);
  useEffect(() => {
    if (!srcSigMenu) return undefined;
    const close = () => setSrcSigMenu(null);
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setSrcSigMenu(null); };
    window.addEventListener('click', close);
    window.addEventListener('keydown', onKey);
    return () => { window.removeEventListener('click', close); window.removeEventListener('keydown', onKey); };
  }, [srcSigMenu]);

  const sourceVcdAnnotations = useMemo(() => {
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
  useEffect(() => {
    if (hierarchy && hierarchy.module && !srcPath && !srcLoading) {
      onSelectModule(hierarchy.module, hierarchy.name, { loadSignals: false });
    }
  }, [hierarchy, srcPath, srcLoading, onSelectModule]);

  const _drag = useRef<any>(null);
  const startDrag = (kind: string) => (e: ReactMouseEvent) => {
    e.preventDefault();
    _drag.current = { kind, startX: e.clientX, startY: e.clientY,
                      leftW, topH,
                      bodyH: (e.currentTarget as HTMLElement).parentElement?.parentElement?.clientHeight || 600 };
    const onMove = (ev: MouseEvent) => {
      const d = _drag.current; if (!d) return;
      if (d.kind === 'left') {
        const w = Math.max(0, Math.min(560, d.leftW + (ev.clientX - d.startX)));
        setLeftW(w);
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
    if (expand === 'wave')      return { lw: 0,          th: 0,   showSource: false, showWave: true,  showHier: false };
    if (expand === 'source')    return { lw: 0,          th: 1.0, showSource: true,  showWave: false, showHier: false };
    if (expand === 'hierarchy') return { lw: leftW || 320, th: 0, showSource: false, showWave: false, showHier: true };
    return { lw: leftW, th: topH, showSource: true, showWave: true, showHier: leftW > 0 };
  })();

  const bodyGridColumns = expand === 'hierarchy'
    ? '1fr 0 0'
    : `${eff.showHier ? eff.lw + 'px' : '0'} ${eff.showHier && eff.lw > 0 ? '4px' : '0'} 1fr`;

  // Agent → panel intent channel (the `sim_debug` tool drives the waveform).
  useSimDebugIntent({
    ipName, active, vcdData, pinSignalsToWave, setViewRange, setTopTab, setExpand,
    setWaveCursor, setWaveCursorB, runSignalTrace, zoomFit,
    reorderByNames, setSignalColorByNames, setSignalRadixByNames, removeSignalsFromWave,
    keepOnlySignals, clearWaveSignals,
    assignGroupByNames, ungroupByNames, renameGroup, toggleGroupFold,
    loadSourceFile,
  });

  return (
    <div className="atlas-frame" style={{
      display: 'flex', flexDirection: 'column',
      flex: 1, width: '100%', height: '100%',
      minWidth: 0, minHeight: 0,
    }}>
      {/* Single unified header — VCD picker + cursor controls + expand mode */}
      <DebugHeader
        summaryOnly={summaryOnly}
        topTab={topTab}
        setTopTab={setTopTab}
        setLeftTab={setLeftTab}
        expand={expand}
        setExpand={setExpand}
        vcdActive={vcdActive}
        setVcdActive={setVcdActive}
        vcdFiles={vcdFiles}
        vcdData={vcdData}
        waveCursor={waveCursor}
        waveCursorB={waveCursorB}
        timeDisplayUnit={timeDisplayUnit}
        setTimeDisplayUnit={setTimeDisplayUnit}
        cursorMetric={cursorMetric}
        setCursorMetric={setCursorMetric}
      />

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
          <HierarchyPanel
            leftTab={leftTab}
            setLeftTab={setLeftTab}
            cocotbData={cocotbData}
            hierarchyBackendTitle={hierarchyBackendTitle}
            hierarchyBackendLabel={hierarchyBackendLabel}
            ipName={ipName}
            loadSourceFile={loadSourceFile}
            hierarchy={hierarchy}
            hierarchyLoading={hierarchyLoading}
            onSelectModule={onSelectModule}
            srcModule={srcModule}
            hierarchyError={hierarchyError}
            vcdData={vcdData}
            selectedSig={selectedSig}
            selectedSigScope={selectedSigScope}
            wavePinnedSignals={wavePinnedSignals}
            onSelectWaveSignal={onSelectWaveSignal}
            showSignalHierarchy={showSignalHierarchy}
            moduleSignals={moduleSignals}
            moduleSignalsModule={moduleSignalsModule}
            moduleSignalsScope={moduleSignalsScope}
            moduleSignalsLoading={moduleSignalsLoading}
            moduleSignalsError={moduleSignalsError}
            signalFilter={signalFilter}
            setSignalFilter={setSignalFilter}
            signalSource={signalSource}
            setSignalSource={setSignalSource}
            onSelectModuleSignal={onSelectModuleSignal}
            addSignalToWave={pinSignalToWave}
            addSignalsToWave={pinSignalsToWave}
            waveSel={waveSel}
            setWaveSel={setWaveSel}
            onTraceSignal={goToDriver}
            onTraceLoad={goToFirstLoad}
            runSignalTrace={runSignalTrace}
            traceResult={traceResult}
            setTraceResult={setTraceResult}
          />
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
            <SourceBand
              eff={eff}
              srcPath={srcPath}
              srcLoading={srcLoading}
              srcCursor={srcCursor}
              showVcdAnnotations={showVcdAnnotations}
              setShowVcdAnnotations={setShowVcdAnnotations}
              waveCursor={waveCursor}
              waveCursorB={waveCursorB}
              vcdData={vcdData}
              vcdAnnotationAxis={vcdAnnotationAxis}
              setVcdAnnotationAxis={setVcdAnnotationAxis}
              srcLines={srcLines}
              selectedSig={selectedSig}
              sourceVcdAnnotations={sourceVcdAnnotations}
              onPickSignal={onSourcePickSignal}
              onAddSignal={onSourceAddSignal}
              onSelectSignals={onSourceSelectSignals}
              onDropToWave={onSourceDropToWave}
              onDropSignalFromWave={goToDriver}
              onSignalContextMenu={onSourceSignalContextMenu}
            />
          )}
          {/* Source ↔ Wave splitter */}
          {eff.showSource && eff.showWave && (
            <Splitter orient="h"
              onMouseDown={startDrag('topH')}
              onDoubleClick={() => setTopH(0.5)}
            />
          )}

          {/* WAVE band — wrap in .wave-panel for Verdi-style dark canvas
              + sharp signal colors (defined in styles.css). */}
          {eff.showWave && (
            <WaveBand
              eff={eff}
              showHelp={showHelp}
              setShowHelp={setShowHelp}
              vcdActive={vcdActive}
              effRange={effRange}
              vcdData={vcdData}
              setViewRange={setViewRange}
              zoomIn={zoomIn}
              zoomOut={zoomOut}
              zoomFit={zoomFit}
              zoomToCursors={zoomToCursors}
              panBy={panBy}
              waveWidth={waveWidth}
              traceList={traceList}
              ipName={ipName}
              waveCursor={waveCursor}
              waveCursorB={waveCursorB}
              setWaveCursor={setWaveCursor}
              setWaveCursorB={setWaveCursorB}
              showSignalHierarchy={showSignalHierarchy}
              selectedSig={selectedSig}
              selectedSigScope={selectedSigScope}
              waveRowSel={waveRowSel}
              setWaveRowSel={setWaveRowSel}
              onSelectWaveSignal={onSelectWaveSignal}
              onDeleteSignalsFromWave={removeSignalsFromWave}
              onReorderSignal={onReorderSignal}
              decor={waveDecor}
              timeDisplayUnit={timeDisplayUnit}
              setTimeDisplayUnit={setTimeDisplayUnit}
              waveRcName={waveRcName}
              setWaveRcName={setWaveRcName}
              waveRcFiles={waveRcFiles}
              waveRcStatus={waveRcStatus}
              onSaveWaveRc={saveWaveRc}
              onRestoreWaveRc={restoreWaveRc}
            />
          )}
        </div>

      </div>
      )}
      {/* Source-code right-click signal menu (add / trace / go-to-driver) */}
      {srcSigMenu && (
        <div
          style={{
            position: 'fixed', left: srcSigMenu.x, top: srcSigMenu.y, zIndex: 60,
            background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 4,
            boxShadow: '0 4px 14px rgba(0,0,0,0.4)', padding: 4, minWidth: 184,
            fontFamily: 'var(--mono)',
          }}
          onClick={e => e.stopPropagation()}
        >
          {(() => {
            const sel = srcSigMenu.selSignals || [];
            const scope = srcSigMenu.scope || '';
            const items: Array<{ label: string; color: string; fn: () => void }> = [];
            // Bulk add from a multi-identifier text selection.
            if (sel.length > 1) {
              items.push({
                label: `＋ Add ${sel.length} signals to waveform`, color: 'var(--fg)',
                fn: () => pinSignalsToWave(sel.map(s => ({ name: s, scope }))),
              });
            }
            // Single-word actions (when the right-click landed on an identifier).
            if (srcSigMenu.name) {
              if (sel.length <= 1) {
                items.push({ label: '＋ Add to waveform', color: 'var(--fg)', fn: () => pinSignalToWave(srcSigMenu.name, scope) });
              }
              items.push({ label: '↳ Trace driver / loads', color: 'var(--cyan)', fn: () => runSignalTrace(srcSigMenu.name, scope) });
              items.push({ label: '→ Go to driver', color: 'var(--accent)', fn: () => goToDriver(srcSigMenu.name, scope) });
              items.push({ label: '→ Go to first load', color: 'var(--cyan)', fn: () => goToFirstLoad(srcSigMenu.name, scope) });
            }
            return items.map(it => (
              <button
                key={it.label}
                onClick={() => { it.fn(); setSrcSigMenu(null); }}
                style={{
                  display: 'block', width: '100%', textAlign: 'left',
                  background: 'transparent', color: it.color, border: 'none',
                  padding: '5px 8px', fontSize: 11, cursor: 'pointer', borderRadius: 3,
                  fontFamily: 'var(--mono)', whiteSpace: 'nowrap',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-2)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >{it.label}</button>
            ));
          })()}
          <div style={{ color: 'var(--fg-mute)', fontSize: 9, padding: '2px 8px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 260 }}>
            {(srcSigMenu.selSignals && srcSigMenu.selSignals.length > 1)
              ? srcSigMenu.selSignals.slice(0, 6).join(', ') + (srcSigMenu.selSignals.length > 6 ? ' …' : '')
              : `${srcSigMenu.scope ? `${srcSigMenu.scope}.` : ''}${srcSigMenu.name}`}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Transitional bridge: register on window so the legacy mount points keep
// resolving `window.SimDebug`. Preserved verbatim from sim-debug.jsx line 845
// (`window.SimDebug = (...) => {...}`), now as an assignment of the exported
// component.
if (typeof window !== 'undefined') {
  g.SimDebug = SimDebug;
}
