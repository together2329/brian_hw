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
import type { ReactNode, CSSProperties, WheelEvent as ReactWheelEvent, MouseEvent as ReactMouseEvent } from 'react';
import {
  normalizeProjectSourcePath,
  stripSignalRange,
  waveSignalMatches,
  buildWaveTraceList,
  buildVcdLineAnnotations,
  inferRtlTopFromVcd,
  activeIpFromAtlasRuntime,
  vcdPathBelongsToIp,
  atlasEventMatchesActiveSession,
} from './sim-debug-helpers';
import type { VcdData, VcdSignal, PinnedSignal } from './sim-debug-helpers';
import {
  CocotbTreeView,
  SimSummaryPanel,
  RangeInput,
  SourceViewer,
  HierarchyNode,
  Splitter,
} from './sim-debug-panels';

// ── Cross-file globals owned by OTHER (unmigrated) files. Typed via a local
// view of `window`; behavior identical to the legacy implicit globals. These
// are workspace/data/wave primitives the root renders or reads at runtime.
interface BackendBridge {
  subscribe?: (event: string, cb: (m: any) => void) => (() => void) | void;
  send?: (msg: { type: string; text: string }) => void;
}
interface SimDebugRootWindow {
  ACTIVE_SESSION?: string;
  backend?: BackendBridge;
  parseVCD?: (content: string) => VcdData;
  WAVE_TIME_START?: number;
  WAVE_TIME_END?: number;
  AtlasTitle: (...a: any[]) => any;
  TimeRuler: (...a: any[]) => any;
  WaveRow: (...a: any[]) => any;
  WaveCursor: (...a: any[]) => any;
  // This file's OWN public global (set via the transitional bridge below).
  SimDebug?: (props?: SimDebugProps) => ReactNode;
}
const g = (typeof window !== 'undefined' ? window : ({} as Window)) as unknown as SimDebugRootWindow;

// Runtime aliases for the window-owned components so JSX reads cleanly while
// still resolving at call time (no module-ordering dependency on the owners).
const AtlasTitle = (props: any) => g.AtlasTitle(props);
const TimeRuler = (props: any) => g.TimeRuler(props);
const WaveRow = (props: any) => g.WaveRow(props);
const WaveCursor = (props: any) => g.WaveCursor(props);

interface SimDebugProps {
  view?: string;
  initialTab?: string;
}

type ViewRange = [number, number] | null;
type ChatEntry = { kind: string; text: string; ts: number };
interface SrcRange { from: number; to: number; hl: number[]; cur: number }

export const SimDebug = ({ view = 'debug', initialTab = '' }: SimDebugProps = {}) => {
  const summaryOnly = view === 'summary';
  const initialTopTab = summaryOnly ? 'summary' : (initialTab || 'wave');
  // Cross-panel state — the agent's "current focus"
  const [activeTool, setActiveTool] = useState('vcd.trace'); // last tool the user clicked
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
  // No mock srcRange — the live SourceViewer drives everything from
  // srcLines / srcCursor. Kept as a stub for any leftover references.
  const [srcRange, setSrcRange] = useState<SrcRange>({ from: 0, to: 0, hl: [], cur: 0 });
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
  const [hierarchy, setHierarchy] = useState<any>(null);
  const [hierarchyError, setHierarchyError] = useState('');
  const [hierarchyMeta, setHierarchyMeta] = useState<any>(null);
  // Top-level tab — full-width view selector. Replaces the old
  // chip-toggle on the right rail; the user picks which DEBUG MODE
  // to focus on and that mode takes the entire center space.
  //   wave      = source (collapsible) + waveform (the rest)
  //   hierarchy = full-width instance tree
  //   trace     = source + driver/sink list (full width)
  //   summary   = TC pass/fail table from SSOT scenarios + scoreboard
  const [topTab, setTopTab] = useState(initialTopTab); // summary | wave | hierarchy | trace | tb
  const [rightTab, setRightTab] = useState('wave'); // legacy, mirrors topTab
  useEffect(() => { setRightTab(topTab); }, [topTab]);
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
  }, []);

  useEffect(() => {
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
        const files = (d.files || []).filter((f: { path: string }) => vcdPathBelongsToIp(f.path, activeIp));
        setVcdFiles(files);
        setVcdActive(prev => files.some((f: { path: string }) => f.path === prev) ? prev : (files[0]?.path || ''));
        if (!files.length) setVcdData(null);
      } catch (e) { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [ipName]);

  // Load + parse the active VCD whenever it changes.
  useEffect(() => {
    if (!vcdActive) return;
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch('/api/vcd/raw?path=' + encodeURIComponent(vcdActive));
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
  }, [vcdActive]);

  // Fetch cocotb env info whenever IP changes (used by left-panel TB tab).
  useEffect(() => {
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
  useEffect(() => {
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

  useEffect(() => {
    setRtlTop('');
  }, [ipName]);

  // Fetch hierarchy when IP is known. The UI is scoped by IP directory, but
  // elaboration must use the real RTL top from tb_manifest/SSOT/VCD scope.
  useEffect(() => {
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

  // Build the traceList — real VCD signals only. The default view stays
  // compact (first 24), while Ctrl+W can pin a selected signal beyond
  // that window into the waveform.
  const traceList = useMemo(() => {
    return buildWaveTraceList(vcdData, wavePinnedSignals, 24);
  }, [vcdData, wavePinnedSignals]);

  // Tool-call activations: clicking one in chat re-focuses the side panels.
  const onToolFocus = (toolId: string, opts: { cursor?: number; range?: SrcRange; sig?: string; scope?: string }) => {
    setActiveTool(toolId);
    if (opts.cursor != null) setWaveCursor(opts.cursor);
    if (opts.range) setSrcRange(opts.range);
    if (opts.sig) {
      setSelectedSig(opts.sig);
      setSelectedSigScope(opts.scope || '');
    }
  };

  // ── Resizable splitter state ─────────────────────────────────────
  // The user can drag boundaries between hierarchy / source / wave / chat.
  // Double-click each splitter handle to collapse/restore its panel.
  // Expand-mode buttons (only-source / only-wave) hide the other panes
  // entirely.
  const [leftW, setLeftW] = useState(220);   // hierarchy column width
  const [rightW, setRightW] = useState(320); // chat rail width
  const [topH, setTopH] = useState(0.32);    // source band height as fraction of body
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

  const jumpToWaveEdge = useCallback((edgeTime: number) => {
    const t = Math.round(Number(edgeTime));
    if (!Number.isFinite(t)) return;
    setWaveCursorB(t);

    const [s, e] = effRange;
    if (t >= s && t <= e) return;

    const span = Math.max(1, e - s);
    const [vs, ve] = vcdData ? (vcdData.timeRange as [number, number]) : [s, e];
    let ns = t - span / 2;
    let ne = t + span / 2;
    if (ns < vs) { ne += vs - ns; ns = vs; }
    if (ne > ve) { ns -= ne - ve; ne = ve; }
    ns = Math.max(vs, ns);
    ne = Math.min(ve, ne);
    if (ns <= vs && ne >= ve) setViewRange(null);
    else setViewRange([ns, ne]);
  }, [effRange, vcdData]);

  const addSelectedSignalToWave = useCallback(() => {
    const name = String(selectedSig || '').trim();
    if (!name) return;
    const scope = String(selectedSigScope || '').trim();
    setWavePinnedSignals(prev => {
      const already = (prev || []).some(pin =>
        stripSignalRange(pin.name).toLowerCase() === stripSignalRange(name).toLowerCase()
        && String(pin.scope || '').trim() === scope
      );
      return already ? prev : [...(prev || []), { name, scope }];
    });
    setTopTab('wave');
  }, [selectedSig, selectedSigScope]);

  // ── Keyboard shortcuts (Verdi-ish) ───────────────────────────────
  // Active only while sim_debug has focus AND user isn't typing in
  // an input/textarea/contenteditable.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
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
  }, [vcdData, effRange, zoomIn, zoomOut, zoomFit, zoomToCursors, panBy, addSelectedSignalToWave]);

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

  // Hierarchy click → load the SV file that ACTUALLY defines the
  // module. Uses ONLY the elaborator's `module_files` map. No filename
  // convention fallback — that picks empty stubs (e.g. `gpio_pad.sv`)
  // when the real implementation lives in `gpio_pad_wrapper.sv`. If
  // elab fails, surface the error rather than guessing.
  const onSelectModule = useCallback((moduleName?: string, instancePath?: string) => {
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
  const onSelectWaveSignal = useCallback(async (signalName: string, signalScope = '') => {
    setSelectedSig(signalName);
    setSelectedSigScope(signalScope || '');
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
      onSelectModule(hierarchy.module, hierarchy.name);
    }
  }, [hierarchy, srcPath, srcLoading, onSelectModule]);

  // ── Live chat (backend WS) state ─────────────────────────────────
  // Hooks the right-rail "chat · trace · debug · ask" panel into the
  // existing ATLAS WS bridge. Send goes to /ws/agent as a 'prompt';
  // streamed tokens append to the in-flight assistant entry; flush /
  // agent_state(false) park the buffer as a finished feed entry.
  const [chatFeed, setChatFeed] = useState<ChatEntry[]>([]);   // [{kind:'user'|'agent'|'thought'|'sys', text, ts}]
  const [chatInput, setChatInput] = useState('');
  const [chatStreaming, setChatStreaming] = useState(false);
  const _streamBuf = useRef('');
  const _chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!g.backend) return;
    const subs: Array<(() => void) | void> = [];
    subs.push(g.backend.subscribe!('token', (m: any) => {
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
    subs.push(g.backend.subscribe!('reasoning', (m: any) => {
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
    subs.push(g.backend.subscribe!('flush', (m: any) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      park();
    }));
    subs.push(g.backend.subscribe!('done', (m: any) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      park(); setChatStreaming(false);
    }));
    subs.push(g.backend.subscribe!('agent_state', (m: any) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      if (m.running === false) { park(); setChatStreaming(false); }
      else if (m.running === true) setChatStreaming(true);
    }));
    subs.push(g.backend.subscribe!('slash_output', (m: any) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      const t = m.text || ''; if (!t) return;
      // de-dupe vs streaming buffer
      if (_streamBuf.current && _streamBuf.current.indexOf(t) >= 0) return;
      setChatFeed(f => [...f, { kind: 'agent', text: t, ts: Date.now() }]);
      _streamBuf.current = '';
    }));
    subs.push(g.backend.subscribe!('error', (m: any) => {
      if (!atlasEventMatchesActiveSession(m, { requireSession: true })) return;
      setChatFeed(f => [...f, { kind: 'sys', text: `[error] ${m.message || ''}`, ts: Date.now() }]);
      setChatStreaming(false);
    }));
    return () => subs.forEach(u => u && u());
  }, []);

  useEffect(() => {
    // auto-scroll chat to bottom on new entries
    const el = _chatScrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [chatFeed.length]);

  // Local intent dispatcher — recognizes `/trace <sig>`, `/hier <mod>`,
  // `/wave <path>` etc. and runs them entirely client-side (drives wave
  // panel + source viewer) without paying for an LLM round trip. Only
  // unrecognized input falls through to the backend agent.
  const sendChat = async (text?: string) => {
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
        const lines: string[] = [];
        if (drv) lines.push(`driver: ${drv.kind}  @ ${drv.file_line}`);
        else     lines.push(`driver: not found (signal '${sig}' may be a port or constant)`);
        if (sinks.length) {
          lines.push(`sinks (${sinks.length}):`);
          sinks.slice(0, 8).forEach((s: any) => lines.push(`  · ${s.context} ${s.access || ''} @ ${s.file_line}`));
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
        const flatten = (n: any, depth: number): string[] => {
          if (!n) return [];
          const out = ['  '.repeat(depth) + (n.name || mod) + ' :: ' + (n.module || '')];
          (n.children || []).forEach((c: any) => out.push(...flatten(c, depth + 1)));
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
    if (!g.backend) return;
    setChatStreaming(true);
    _streamBuf.current = '';
    g.backend.send!({ type: 'prompt', text: raw });
  };

  const _drag = useRef<any>(null);
  const startDrag = (kind: string) => (e: ReactMouseEvent) => {
    e.preventDefault();
    _drag.current = { kind, startX: e.clientX, startY: e.clientY,
                      leftW, rightW, topH,
                      bodyH: (e.currentTarget as HTMLElement).parentElement?.parentElement?.clientHeight || 600 };
    const onMove = (ev: MouseEvent) => {
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

  const ExpandBtn = ({ id, glyph, title }: { id: string; glyph: string; title: string }) => (
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

  const selectTopTab = (id: string) => {
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

  const ModeBtn = ({ id, label, title }: { id: string; label: string; title?: string }) => (
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

  const bodyGridColumns = expand === 'hierarchy'
    ? '1fr 0 0 0 0'
    : `${eff.showHier ? eff.lw + 'px' : '0'} ${eff.showHier && eff.lw > 0 ? '4px' : '0'} 1fr ${eff.showChat && eff.rw > 0 ? '4px' : '0'} ${eff.showChat ? eff.rw + 'px' : '0'}`;

  return (
    <div className="atlas-frame" style={{
      display: 'flex', flexDirection: 'column',
      flex: 1, width: '100%', height: '100%',
      minWidth: 0, minHeight: 0,
    }}>
      <AtlasTitle
        // Resolve the active workspace IP — prefer the SimDebug-local
        // ipName (set when a VCD is found), otherwise the live
        // window.ACTIVE_SESSION's middle segment (default/<ip>/<wf>).
        // The hardcoded "spi_master/" fallback inside AtlasTitle is
        // gone now; passing an empty string still falls back to that
        // legacy default for first-paint.
        workspace={
          ipName ||
          (String(g.ACTIVE_SESSION || '').split('/').filter(Boolean)[1]) ||
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
            ✓ {vcdData.signals!.length} sig · t={vcdData.timeRange![0]}–{vcdData.timeRange![1]} {vcdData.timescale}
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
                  {vcdData.signals.slice(0, 30).map((s: VcdSignal) => {
                    const isSelected = selectedSig === s.name && (!selectedSigScope || selectedSigScope === s.scope);
                    const isPinned = wavePinnedSignals.some(pin => waveSignalMatches(s, pin.name, pin.scope));
                    return (
                      <div
                        key={s.id}
                        onClick={() => onSelectWaveSignal(s.name!, s.scope)}
                        style={{
                          padding: '2px 4px', cursor: 'pointer',
                          color: isSelected ? 'var(--accent)' : 'var(--fg)',
                          background: isSelected ? 'var(--bg-2)' : 'transparent',
                          display: 'flex', gap: 4, alignItems: 'center',
                        }}
                        title="click to focus, Ctrl+W to add to waveform"
                      >
                        <span style={{ color: isPinned ? 'var(--cyan)' : 'var(--fg-mute)' }}>{isPinned ? '◆' : '·'}</span>
                        <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {showSignalHierarchy && s.scope ? `${s.scope}.` : ''}{s.name}
                          {s.isBus && <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}> {s.range}</span>}
                        </span>
                      </div>
                    );
                  })}
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
                vcdAnnotations={sourceVcdAnnotations}
                vcdAnnotationAxis={vcdAnnotationAxis}
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
                      { keys: ['Ctrl + W'], desc: 'add focused signal to waveform' },
                      { keys: ['h'],      desc: 'toggle signal hierarchy in labels' },
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
                onWheel={(e: ReactWheelEvent) => {
                  // Ctrl+wheel = zoom around cursor A. Plain wheel = scroll.
                  if (!e.ctrlKey && !e.metaKey) return;
                  e.preventDefault();
                  if (e.deltaY < 0) zoomIn(); else zoomOut();
                }}
              >
                <TimeRuler
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
                    const displayName = showSignalHierarchy && t.scope ? `${t.scope}.${t.name}` : t.name;
                    return (
                      <div key={(t.scope || '') + '/' + t.name + '/' + ti}
                           style={color ? ({ '--wave-color-override': color } as CSSProperties) : undefined}>
                        <WaveRow
                          name={displayName}
                          scope={t.scope}
                          trace={t.trace}
                          width={waveWidth}
                          isBus={t.isBus}
                          radix={t.radix || 'HEX'}
                          selected={waveSignalMatches(t, selectedSig, selectedSigScope)}
                          colorHint={color}
                          onClick={() => onSelectWaveSignal(t.signalName || t.name!, t.scope || '')}
                          onEdgeClick={jumpToWaveEdge}
                        />
                      </div>
                    );
                  })}
                  <div style={{ position: 'absolute', top: 0, bottom: 0, left: 280, width: waveWidth, pointerEvents: 'none' }}>
                    <WaveCursor time={waveCursor}  kind="a" width={waveWidth} />
                    <WaveCursor time={waveCursorB} kind="b" width={waveWidth} />
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

// ── Transitional bridge: register on window so the legacy mount points keep
// resolving `window.SimDebug`. Preserved verbatim from sim-debug.jsx line 845
// (`window.SimDebug = (...) => {...}`), now as an assignment of the exported
// component.
if (typeof window !== 'undefined') {
  g.SimDebug = SimDebug;
}
