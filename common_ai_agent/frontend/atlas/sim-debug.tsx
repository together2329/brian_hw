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
  buildWaveTraceList,
  buildVcdLineAnnotations,
  inferRtlTopFromVcd,
  activeIpFromAtlasRuntime,
  vcdPathBelongsToIp,
} from './sim-debug-helpers';
import type { VcdData, PinnedSignal } from './sim-debug-helpers';
import { SimSummaryPanel, Splitter } from './sim-debug-panels';
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

export const SimDebug = ({ view = 'debug', initialTab = '' }: SimDebugProps = {}) => {
  const summaryOnly = view === 'summary';
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
            onSelectModule={onSelectModule}
            srcModule={srcModule}
            hierarchyError={hierarchyError}
            vcdData={vcdData}
            selectedSig={selectedSig}
            selectedSigScope={selectedSigScope}
            wavePinnedSignals={wavePinnedSignals}
            onSelectWaveSignal={onSelectWaveSignal}
            showSignalHierarchy={showSignalHierarchy}
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
              sourceVcdAnnotations={sourceVcdAnnotations}
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
              showSignalHierarchy={showSignalHierarchy}
              selectedSig={selectedSig}
              selectedSigScope={selectedSigScope}
              onSelectWaveSignal={onSelectWaveSignal}
              jumpToWaveEdge={jumpToWaveEdge}
            />
          )}
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
