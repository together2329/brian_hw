// sim-debug-wave.tsx — the WAVE band panel extracted from sim-debug.tsx
// (strangler-fig split). Behavior-identical: this is the SAME `eff.showWave &&
// (...)` subtree that rendered the Verdi-style dark waveform canvas — its
// mini-header (range input + zoom/pan/fit buttons + help toggle), the
// ctrl-wheel zoom handler, the TimeRuler, the sticky cursor strip, the trace
// rows, and the overlaid A/B WaveCursors. The root SimDebug closure owns all
// the state; this component receives the exact slice it renders + the handlers
// it fires as a typed props bundle (window-sourced values stay `any`, same
// permissive house style as sim-debug-helpers.tsx).
//
// Load order: imported by sim-debug.tsx. Owns no window bridge.
import { useState, useRef, useLayoutEffect, useEffect } from 'react';
import type {
  Dispatch,
  ReactNode,
  CSSProperties,
  MouseEvent as ReactMouseEvent,
  DragEvent as ReactDragEvent,
  SetStateAction,
  WheelEvent as ReactWheelEvent,
} from 'react';
import { RangeInput } from './sim-debug-panels';
import type { PinnedSignal, VcdData, VcdSignal, WaveCommand, WaveGroupState } from './sim-debug-helpers';
import { waveSignalMatches, waveSignalKey, parseWaveCommand, stripTopScope,
         lookupSignalMeta, buildWaveDisplayRows, sigIdent, stripSignalRange, signalRangeOf,
         TIME_DISPLAY_UNITS, resolveTimeDisplayUnit, rawTimeToDisplay,
         formatTimeDisplay, formatTimeDeltaDisplay, formatFrequencyFromDelta,
         reorderWaveKeys } from './sim-debug-helpers';
import type { WaveReorderPlacement } from './sim-debug-helpers';
import { TimeRuler, WaveRow, WaveCursor } from './sim-debug-root-shared';
import { WaveShortcutsOverlay } from './sim-debug-shortcuts';

interface WaveBandProps {
  eff: any;
  showHelp: boolean;
  setShowHelp: (fn: ((h: boolean) => boolean) | boolean) => void;
  vcdActive: string;
  effRange: [number, number];
  vcdData: VcdData | null;
  setViewRange: (r: any) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  zoomFit: () => void;
  zoomToCursors: () => void;
  panBy: (fraction: number) => void;
  waveWidth: number;
  traceList: VcdSignal[];
  ipName: string;
  waveCursor: number;
  waveCursorB: number;
  setWaveCursor: (t: number) => void;
  setWaveCursorB: (t: number) => void;
  showSignalHierarchy: boolean;
  selectedSig: string;
  selectedSigScope: string;
  waveRowSel: PinnedSignal[];
  setWaveRowSel: Dispatch<SetStateAction<PinnedSignal[]>>;
  onSelectWaveSignal: (signalName: string, signalScope?: string) => void;
  onDeleteSignalsFromWave: (items: PinnedSignal[]) => void;
  onReorderSignal: (orderedKeys: string[]) => void;
  decor: WaveDecor;
  timeDisplayUnit: string;
  setTimeDisplayUnit: (v: string) => void;
  waveRcName: string;
  setWaveRcName: (v: string) => void;
  waveRcFiles: Array<{ name: string; path?: string }>;
  waveRcStatus: string;
  onSaveWaveRc: () => void;
  onRestoreWaveRc: () => void;
}

// Per-signal/-group decoration state + mutators (agent- or right-click-driven).
export interface WaveDecor {
  colors: Record<string, string>;
  radices: Record<string, string>;
  paramValueMap: Record<string, string>;
  tags: Record<string, string>;
  groups: WaveGroupState;
  setSignalColor: (names: string[], color: string | null) => void;
  setSignalRadix: (names: string[], radix: string | null) => void;
  moveSignal: (key: string, dir: number) => void;
  assignGroup: (names: string[], tag: string, color?: string | null) => void;
  ungroup: (names: string[]) => void;
  toggleFold: (tag: string, folded?: boolean) => void;
  renameGroup: (oldTag: string, newTag: string) => void;
  setGroupColor: (tag: string, color: string | null) => void;
}

// Palette offered in the right-click colour menu (signal + group).
const WAVE_COLOR_PALETTE = ['#4dd0e1', '#7CFC4D', '#ffb84d', '#ff6b6b', '#b388ff', '#ffd24d', '#9ccc65', '#ff5252'];

const setWaveDragPreview = (e: ReactDragEvent<HTMLElement>, label: string) => {
  if (typeof document === 'undefined' || typeof e.dataTransfer.setDragImage !== 'function') return;
  const el = document.createElement('div');
  el.textContent = label;
  el.className = 'wave-drag-preview';
  document.body.appendChild(el);
  e.dataTransfer.setDragImage(el, 12, 12);
  window.setTimeout(() => el.remove(), 0);
};

export const WaveBand = ({
  eff, showHelp, setShowHelp, vcdActive, effRange, vcdData, setViewRange,
  zoomIn, zoomOut, zoomFit, zoomToCursors, panBy, waveWidth: waveWidthProp, traceList,
  ipName, waveCursor, waveCursorB, setWaveCursor, setWaveCursorB,
  showSignalHierarchy, selectedSig,
  selectedSigScope, waveRowSel, setWaveRowSel, onSelectWaveSignal,
  onDeleteSignalsFromWave, onReorderSignal, decor,
  timeDisplayUnit, setTimeDisplayUnit, waveRcName, setWaveRcName,
  waveRcFiles, waveRcStatus, onSaveWaveRc, onRestoreWaveRc,
}: WaveBandProps): ReactNode => {
  // Drag a signal row or a whole group by its left/name zone to reorder it.
  // The plot zone stays reserved for cursor/zoom gestures.
  const dragItemRef = useRef<{ kind: 'sig' | 'group'; keys: string[]; label: string } | null>(null);
  const [dropHint, setDropHint] = useState<{ id: string; placement: WaveReorderPlacement } | null>(null);
  // Right-click menu (signal colour / move / group) + inline group rename.
  const [ctx, setCtx] = useState<{ x: number; y: number; kind: 'sig' | 'group'; sig?: VcdSignal; tag?: string } | null>(null);
  const [renaming, setRenaming] = useState<string | null>(null);
  useEffect(() => {
    if (!ctx) return undefined;
    const close = () => setCtx(null);
    window.addEventListener('click', close);
    window.addEventListener('scroll', close, true);
    return () => { window.removeEventListener('click', close); window.removeEventListener('scroll', close, true); };
  }, [ctx]);
  // ── Resizable label column (signal name + value @ A) vs the plot ──
  // A draggable vertical bar at the label/plot boundary widens or narrows
  // the name+value zone (CSS var --wave-name-w feeds .wave-row / .time-ruler).
  const [nameW, setNameW] = useState(180);
  // Plot origin = end of the name + value columns (the grid boundary where the
  // trace SVGs, ruler axis, and cursor-strip badges all start). The cursor
  // overlay + drag-zoom MUST share this exact origin or the vertical cursor
  // lines drift right of their badges/traces (the old hard-coded 280 was 10px
  // off → "중앙 안 맞아").
  const plotLeft = nameW + 90;
  // Responsive plot width. The wave-row's 3rd grid column is `1fr`, so it
  // stretches to fill the panel — but the trace SVG + the time↔pixel mapping
  // (tToX / xToTime / cursor + ruler placement) all key off a NUMERIC width.
  // A hard-coded 700 left the right of wide windows blank (full-width gridlines
  // but trace only to 700px). Measure the panel and fill the column so the
  // waveform spans the whole viewer. A CSS-only stretch won't do: the number
  // must equal the real pixels or the cursors/ruler would drift.
  const [containerW, setContainerW] = useState(0);
  const waveWidth = containerW > plotLeft + 40 ? Math.round(containerW - plotLeft) : waveWidthProp;
  const ts = vcdData?.timescale || 'ns';
  const displayUnit = resolveTimeDisplayUnit(ts, timeDisplayUnit);
  const deltaRaw = waveCursorB - waveCursor;
  const scrollRef = useRef<HTMLDivElement>(null);
  const [handleTop, setHandleTop] = useState(28);
  useLayoutEffect(() => {
    if (scrollRef.current) setHandleTop(scrollRef.current.offsetTop);
  });
  const startLabelResize = (e: ReactMouseEvent) => {
    e.preventDefault();
    const startX = e.clientX, startW = nameW;
    const onMove = (ev: MouseEvent) =>
      setNameW(Math.max(90, Math.min(560, startW + (ev.clientX - startX))));
    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  // ── Drag-to-zoom: rubber-band a time region on the plot to zoom into it ──
  const plotRef = useRef<HTMLDivElement>(null);
  const plotAreaRef = useRef<HTMLDivElement>(null);  // the plot/cursor layer
  const dragJustZoomed = useRef(false);
  // Track the panel's content width so waveWidth fills the `1fr` plot column.
  useEffect(() => {
    const el = plotRef.current;
    if (!el || typeof ResizeObserver === 'undefined') return undefined;
    const ro = new ResizeObserver(entries => {
      const w = entries[0] && entries[0].contentRect ? entries[0].contentRect.width : 0;
      if (w) setContainerW(w);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const [sel, setSel] = useState<{ x0: number; x1: number } | null>(null);
  const xToTime = (px: number) => {
    const [s, e2] = effRange;
    const clamped = Math.max(0, Math.min(waveWidth, px));
    return s + (clamped / waveWidth) * (e2 - s);
  };
  const startPlotDrag = (e: ReactMouseEvent) => {
    if (!plotAreaRef.current) return;
    // Measure the mouse against the SAME element the cursors + selection box
    // render in (the 700px plot layer), so coordinates can't drift from the
    // label-column width or any offset arithmetic.
    const originX = plotAreaRef.current.getBoundingClientRect().left;
    // Cursor B = middle-click (mouse) OR Option/⌥ + click / Shift + click
    // (MacBook trackpad has no middle button). Cursor A is plain left-click
    // (see jumpToWaveEdge); plain left-drag zooms.
    const wantsCursorB = e.button === 1 || (e.button === 0 && (e.altKey || e.shiftKey));
    if (wantsCursorB) {
      const xb = e.clientX - originX;
      if (xb < 0 || xb > waveWidth) return;
      e.preventDefault();  // stop middle-click autoscroll
      setWaveCursorB(Math.round(xToTime(xb)));
      // Swallow the trailing click so it doesn't also place cursor A / select.
      dragJustZoomed.current = true;
      setTimeout(() => { dragJustZoomed.current = false; }, 0);
      return;
    }
    if (e.button !== 0) return;
    const x0 = e.clientX - originX;
    if (x0 < 0 || x0 > waveWidth) return;  // started outside the plot → ignore
    let moved = false;
    const onMove = (ev: MouseEvent) => {
      const x1 = Math.max(0, Math.min(waveWidth, ev.clientX - originX));
      if (Math.abs(x1 - x0) > 3) moved = true;
      setSel({ x0, x1 });
    };
    const onUp = (ev: MouseEvent) => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      const x1 = Math.max(0, Math.min(waveWidth, ev.clientX - originX));
      setSel(null);
      if (moved && Math.abs(x1 - x0) > 4) {
        const t0 = xToTime(Math.min(x0, x1));
        const t1 = xToTime(Math.max(x0, x1));
        if (t1 - t0 >= 1) {
          dragJustZoomed.current = true;  // swallow the trailing click on the row
          // Safety net: if no click follows this drag, clear the flag so the
          // NEXT genuine click is not swallowed.
          setTimeout(() => { dragJustZoomed.current = false; }, 0);
          setViewRange([Math.round(t0), Math.round(t1)]);
        }
      } else {
        // Plain left-click (no drag) → cursor A at the EXACT clicked time
        // (no edge snapping, so the cursor lands exactly where you clicked).
        setWaveCursor(Math.round(xToTime(x0)));
      }
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };
  const onPlotClickCapture = (e: ReactMouseEvent) => {
    if (dragJustZoomed.current) {
      e.stopPropagation();
      e.preventDefault();
      dragJustZoomed.current = false;
    }
  };

  // Click the TIME AXIS / cursor strip to set a cursor: left = A, ⌥/Shift or
  // middle = B. Same x→time mapping as the plot (shared plotAreaRef origin).
  const placeCursorFromRuler = (e: ReactMouseEvent) => {
    if (!plotAreaRef.current) return;
    const x = e.clientX - plotAreaRef.current.getBoundingClientRect().left;
    if (x < 0 || x > waveWidth) return;  // clicked the name/value columns, not the axis
    const t = Math.round(xToTime(x));
    if (e.button === 1 || (e.button === 0 && (e.altKey || e.shiftKey))) {
      e.preventDefault();
      setWaveCursorB(t);
    } else if (e.button === 0) {
      setWaveCursor(t);
    }
  };

  // ── Chat/command bar: type to place cursor A/B, zoom a range, or fit ──
  const [cmdText, setCmdText] = useState('');
  const [cmdEcho, setCmdEcho] = useState('');
  const clampT = (n: number) => {
    if (!vcdData) return n;
    const [lo, hi] = vcdData.timeRange as [number, number];
    return Math.max(lo, Math.min(hi, n));
  };
  const applyWaveCommand = (cmd: WaveCommand): string => {
    if (cmd.fit) { zoomFit(); return 'fit · whole VCD'; }
    if (cmd.zoomCursors) { zoomToCursors(); return 'zoom A↔B'; }
    const notes: string[] = [];
    if (cmd.cursorA != null) { const a = clampT(cmd.cursorA); setWaveCursor(a); notes.push(`A=${a}`); }
    if (cmd.cursorB != null) { const b = clampT(cmd.cursorB); setWaveCursorB(b); notes.push(`B=${b}`); }
    if (cmd.view) {
      const a = clampT(Math.min(cmd.view[0], cmd.view[1]));
      const b = clampT(Math.max(cmd.view[0], cmd.view[1]));
      if (b - a >= 1) { setViewRange([a, b]); notes.push(`zoom ${a}–${b}`); }
    }
    return notes.join(' · ') || 'no change';
  };
  const runCmd = () => {
    const cmd = parseWaveCommand(cmdText);
    if (!cmd) { setCmdEcho('? try: a 5000 b 15000 · zoom 1000 8000 · fit'); return; }
    setCmdEcho(applyWaveCommand(cmd));
    setCmdText('');
  };

  // Group headers + their (contiguous) members + ungrouped rows, honoring fold.
  const displayItems = buildWaveDisplayRows(traceList, decor.tags, decor.groups);
  const visibleSignalRows = displayItems.flatMap(item => item.type === 'sig' ? [item.sig] : []);
  const orderedWaveKeys = traceList.map(waveSignalKey);
  const groupTagOf = (sig: VcdSignal): string => lookupSignalMeta(decor.tags, sig) || '';
  const groupKeys = (tag: string): string[] =>
    traceList.filter(sig => groupTagOf(sig) === tag).map(waveSignalKey);
  const dropPlacement = (e: ReactMouseEvent | ReactDragEvent<HTMLElement>): WaveReorderPlacement => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    return e.clientY > rect.top + rect.height / 2 ? 'after' : 'before';
  };
  const dragCanDrop = (targetKeys: string[]) => {
    const drag = dragItemRef.current;
    if (!drag || !targetKeys.length) return false;
    const moving = new Set(drag.keys);
    return targetKeys.some(k => !moving.has(k));
  };
  const onWaveDragOver = (e: ReactDragEvent<HTMLElement>, id: string, targetKeys: string[]) => {
    if (!dragCanDrop(targetKeys)) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDropHint({ id, placement: dropPlacement(e) });
  };
  const onWaveDrop = (e: ReactDragEvent<HTMLElement>, targetKeys: string[]) => {
    const drag = dragItemRef.current;
    if (!drag || !dragCanDrop(targetKeys)) return;
    e.preventDefault();
    e.stopPropagation();
    const next = reorderWaveKeys(orderedWaveKeys, drag.keys, targetKeys, dropPlacement(e));
    dragItemRef.current = null;
    setDropHint(null);
    onReorderSignal(next);
  };
  const dndClass = (id: string) =>
    dropHint?.id === id ? ` ${dropHint.placement === 'after' ? 'wave-dnd-after' : 'wave-dnd-before'}` : '';
  const dndShadow = (id: string) =>
    dropHint?.id === id ? `inset 0 ${dropHint.placement === 'after' ? '-2px' : '2px'} 0 var(--accent)` : '';
  const selKeyOf = (name?: string, scope?: string) =>
    `${String(scope || '').trim()}::${stripSignalRange(name).toLowerCase()}${signalRangeOf(name).toLowerCase()}`;
  const selectedWaveKeys = new Set((waveRowSel || []).map(s => selKeyOf(s.name, s.scope)));
  const rowItem = (sig: VcdSignal): PinnedSignal => ({
    name: String(sig.name || sig.signalName || '').trim(),
    scope: String(sig.scope || '').trim(),
  });
  const dedupeWaveSel = (items: PinnedSignal[]) => {
    const seen = new Set<string>();
    const out: PinnedSignal[] = [];
    for (const it of items || []) {
      const name = String(it.name || '').trim();
      const scope = String(it.scope || '').trim();
      if (!name) continue;
      const key = selKeyOf(name, scope);
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({ name, scope });
    }
    return out;
  };
  const [waveAnchorIdx, setWaveAnchorIdx] = useState(-1);
  const isRowSelected = (sig: VcdSignal) => {
    const it = rowItem(sig);
    return selectedWaveKeys.has(selKeyOf(it.name, it.scope));
  };
  const isSelectionZone = (e: ReactMouseEvent) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    return e.clientX - rect.left <= nameW + 90;
  };
  const selectWaveRow = (e: ReactMouseEvent, sig: VcdSignal) => {
    const item = rowItem(sig);
    const idx = visibleSignalRows.findIndex(row => waveSignalKey(row) === waveSignalKey(sig));
    if (e.shiftKey && idx >= 0 && waveAnchorIdx >= 0) {
      const [a, b] = [Math.min(waveAnchorIdx, idx), Math.max(waveAnchorIdx, idx)];
      setWaveRowSel(prev => dedupeWaveSel([...(prev || []), ...visibleSignalRows.slice(a, b + 1).map(rowItem)]));
    } else if (e.ctrlKey || e.metaKey) {
      const key = selKeyOf(item.name, item.scope);
      setWaveRowSel(prev => {
        const current = prev || [];
        const selected = current.some(s => selKeyOf(s.name, s.scope) === key);
        return selected
          ? current.filter(s => selKeyOf(s.name, s.scope) !== key)
          : dedupeWaveSel([...current, item]);
      });
      if (idx >= 0) setWaveAnchorIdx(idx);
    } else {
      setWaveRowSel([item]);
      if (idx >= 0) setWaveAnchorIdx(idx);
      onSelectWaveSignal(item.name || '', item.scope || '');
    }
  };
  const handleWaveRowMouseDown = (e: ReactMouseEvent, sig: VcdSignal) => {
    const wantsMulti = e.button === 0 && (e.ctrlKey || e.metaKey || (e.shiftKey && isSelectionZone(e)));
    if (!wantsMulti) return;
    e.preventDefault();
    e.stopPropagation();
    selectWaveRow(e, sig);
  };
  const handleWaveRowClick = (e: ReactMouseEvent, sig: VcdSignal) => {
    if (e.ctrlKey || e.metaKey || e.shiftKey) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    selectWaveRow(e, sig);
  };
  const ctxIsGrouped = ctx?.kind === 'sig' && ctx.sig ? !!lookupSignalMeta(decor.tags, ctx.sig) : false;
  const ctxSigSelected = ctx?.kind === 'sig' && ctx.sig ? isRowSelected(ctx.sig) : false;
  const ctxDeleteItems = ctx?.kind === 'sig' && ctx.sig && ctxSigSelected && (waveRowSel || []).length > 1
    ? waveRowSel
    : (ctx?.kind === 'sig' && ctx.sig ? [rowItem(ctx.sig)] : []);
  // Decoration actions (colour / radix / grouping) apply to the SAME target set
  // as delete: the full multi-selection when the right-clicked row is part of
  // it, otherwise just the clicked row. Without this, colour/radix changed only
  // the single right-clicked signal even with many rows selected.
  const ctxTargetNames = ctxDeleteItems.map(sigIdent);
  const ctxTargetCount = ctxTargetNames.length;

  return (
    <div className="wave-panel" style={{
      flex: eff.showSource ? `${Math.round((1 - eff.th) * 100)} ${Math.round((1 - eff.th) * 100)} 0` : '1 1 0',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      borderTop: eff.showSource ? '1px solid var(--line)' : 'none',
      position: 'relative',
      ...({ '--wave-name-w': `${nameW}px` } as CSSProperties),
    }}>
      {/* draggable label/plot divider — resize the name+value column */}
      <div
        onMouseDown={startLabelResize}
        title="drag to resize the signal-name column"
        style={{
          position: 'absolute', top: handleTop, bottom: 0, left: nameW + 90,
          width: 6, marginLeft: -3, cursor: 'col-resize', zIndex: 7,
        }}
      />
      <WaveShortcutsOverlay show={showHelp} onClose={() => setShowHelp(false)} />
      <div className="mini-h" style={{ display: 'flex', alignItems: 'center' }}>
        <b>waveform</b>
        <span style={{ color: 'var(--cyan)', marginLeft: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
          {vcdActive ? vcdActive.split('/').pop() : '(none)'}
        </span>
        <span style={{ color: 'var(--line-2)', margin: '0 2px 0 8px' }}>│</span>
        <span style={{ color: 'var(--fg-mute)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>rc</span>
        <input
          list="sim-debug-wave-rc-files"
          value={waveRcName}
          onChange={e => setWaveRcName(e.target.value)}
          onKeyDown={e => e.stopPropagation()}
          placeholder="signal.rc"
          title="waveform rc file name"
          style={{
            width: 96, background: 'var(--bg)', color: 'var(--fg)', border: '1px solid var(--line)',
            borderRadius: 3, padding: '1px 5px', fontSize: 10, fontFamily: 'var(--mono)',
          }}
        />
        <datalist id="sim-debug-wave-rc-files">
          {waveRcFiles.map(f => <option key={f.name} value={f.name} />)}
        </datalist>
        <button className="btn" style={{ padding: '1px 7px', fontSize: 10, marginRight: 2 }}
                onClick={onSaveWaveRc} title="save current waveform layout to rc">
          save
        </button>
        <button className="btn" style={{ padding: '1px 7px', fontSize: 10, marginRight: 4 }}
                onClick={onRestoreWaveRc} title="restore waveform layout from rc">
          restore
        </button>
        {waveRcStatus && (
          <span title={waveRcStatus} style={{
            color: waveRcStatus.startsWith('error') ? 'var(--err)' : 'var(--fg-mute)',
            fontSize: 9, fontFamily: 'var(--mono)', maxWidth: 120,
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>{waveRcStatus}</span>
        )}
        <span style={{ flex: 1 }} />
        {(waveRowSel || []).length > 0 && (
          <>
            <span style={{ color: 'var(--accent)', fontFamily: 'var(--mono)', fontSize: 10, marginRight: 6 }}>
              {waveRowSel.length} selected
            </span>
            <button className="btn" style={{ padding: '1px 8px', fontSize: 10, marginRight: 4 }}
                    onClick={() => onDeleteSignalsFromWave(waveRowSel)}
                    title="delete selected waveform rows">
              delete
            </button>
          </>
        )}
        {/* Editable range — type to jump. Two number inputs for
            start/end. Plus a tiny tooltip with full range + zoom %. */}
        <RangeInput
          effRange={effRange}
          vcdData={vcdData}
          setViewRange={setViewRange}
          timeDisplayUnit={timeDisplayUnit}
        />
        <span style={{ color: 'var(--fg-mute)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>res</span>
        <select
          value={timeDisplayUnit}
          onChange={e => setTimeDisplayUnit(e.target.value)}
          title={`display time resolution (VCD timescale: ${ts})`}
          style={{
            background: 'var(--bg)', color: 'var(--fg)', border: '1px solid var(--line)',
            padding: '1px 4px', fontSize: 10, fontFamily: 'var(--mono)', marginRight: 4,
          }}
        >
          {TIME_DISPLAY_UNITS.map(u => <option key={u} value={u}>{u}</option>)}
        </select>
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
        ref={scrollRef}
        style={{ flex: 1, overflow: 'auto', position: 'relative' }}
        onWheel={(e: ReactWheelEvent) => {
          // Ctrl/Cmd + wheel (incl. trackpad pinch) → zoom toward the pointer.
          // PROPORTIONAL to the wheel delta with a per-event cap, because a
          // trackpad pinch fires dozens of events — the old fixed 2×-per-event
          // zoom made it wildly oversensitive on a MacBook.
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            if (!vcdData) return;
            const [s, en] = effRange;
            const [vs, ve] = vcdData.timeRange as [number, number];
            let center = (s + en) / 2;  // fall back to window center
            if (plotAreaRef.current) {
              const mx = e.clientX - plotAreaRef.current.getBoundingClientRect().left;
              if (mx >= 0 && mx <= waveWidth) center = xToTime(mx);  // zoom toward cursor
            }
            // deltaY<0 (pinch-out / scroll-up) → factor<1 → zoom in.
            const dz = Math.max(-0.18, Math.min(0.18, e.deltaY * 0.01));
            const factor = Math.exp(dz);
            let ns = center - (center - s) * factor;
            let ne = center + (en - center) * factor;
            ns = Math.max(vs, ns);
            ne = Math.min(ve, ne);
            if (ne - ns < 1) return;  // already fully zoomed in
            if (ns <= vs && ne >= ve) setViewRange(null);
            else setViewRange([Math.round(ns), Math.round(ne)]);
            return;
          }
          // Two-finger horizontal swipe (trackpad) → pan the view left/right
          // (also stops the macOS history back/forward swipe gesture).
          if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
            e.preventDefault();
            panBy(Math.max(-0.5, Math.min(0.5, e.deltaX / waveWidth)));
          }
          // else: plain vertical wheel → default scroll of the signal list.
        }}
      >
        {/* Sticky header = TimeRuler + cursor strip pinned together at the
            scroll-container top. Previously the ruler scrolled away while
            the cursor strip stuck at top:22, leaving a 22px gap that let the
            trace rows bleed through (broken-looking on scroll-down). Wrapping
            both in ONE sticky block keeps a solid header as rows scroll. */}
        <div
          onMouseDown={placeCursorFromRuler}
          title="click the time axis to set cursor A · ⌥/Shift+click (or middle-click) for B"
          style={{ position: 'sticky', top: 0, zIndex: 6, background: '#0d1118', cursor: 'crosshair' }}
        >
        <TimeRuler
          width={waveWidth}
          tMin={rawTimeToDisplay(effRange[0], ts, displayUnit)}
          tMax={rawTimeToDisplay(effRange[1], ts, displayUnit)}
          signals={traceList.length}
          scope={ipName || 'scope'}
          timescale={displayUnit}
        />

        {/* Cursor strip — dedicated row that holds A/B labels and a
            Δ readout. Keeps the cursor markers from overlapping the
            signal rows the way they did before. */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: `${nameW}px 90px 1fr`,
          height: 18,
          borderBottom: '1px solid #2a3140',
          background: '#0d1118',
          fontFamily: 'var(--mono)', fontSize: 10,
        }}>
          <span
            title={'A = left-click on the waveform\nB = ⌥/Shift + click (or middle-click)\ndrag = zoom · ⌘/Ctrl+scroll = zoom · two-finger ←→ = pan'}
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              padding: '0 10px', color: '#6c7888',
              borderRight: '1px solid #161a22',
              textTransform: 'uppercase', letterSpacing: '0.06em',
            }}
          >
            cursors
            <span style={{ color: '#ffb84d' }}>A</span>
            <span style={{ color: '#4c5666' }}>click</span>
            <span style={{ color: '#4dd0e1' }}>B</span>
            <span style={{ color: '#4c5666' }}>⌥click</span>
          </span>
          <span style={{
            display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
            padding: '0 10px', color: '#ffd24d', fontWeight: 700,
            borderRight: '1px solid #161a22',
          }}>Δ {formatTimeDeltaDisplay(deltaRaw, ts, displayUnit)} · {formatFrequencyFromDelta(deltaRaw, ts)}</span>
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
                  {c.kind}={formatTimeDisplay(c.time, ts, displayUnit)}
                </span>
              );
            })}
          </div>
        </div>
        </div>
        <div className="wave-top-click-gutter" aria-hidden="true" />
        <div
          ref={plotRef}
          onMouseDown={startPlotDrag}
          onClickCapture={onPlotClickCapture}
          style={{ position: 'relative', cursor: traceList.length ? 'crosshair' : 'default' }}
        >
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
          {displayItems.map((item, di) => {
            if (item.type === 'group') {
              const gcolor = item.color || '#8aa0b5';
              const keys = groupKeys(item.tag);
              const dropId = `grp/${item.tag}`;
              return (
                <div key={'grp/' + item.tag} className={`wave-group-header${dndClass(dropId)}`}
                     draggable={keys.length > 0}
                     onDragStart={e => {
                       if (!keys.length) { e.preventDefault(); return; }
                       dragItemRef.current = { kind: 'group', keys, label: item.tag };
                       e.dataTransfer.effectAllowed = 'move';
                       e.dataTransfer.setData('text/plain', item.tag);
                       setWaveDragPreview(e, item.tag);
                     }}
                     onDragOver={e => onWaveDragOver(e, dropId, keys)}
                     onDragLeave={() => setDropHint(null)}
                     onDrop={e => onWaveDrop(e, keys)}
                     onDragEnd={() => { dragItemRef.current = null; setDropHint(null); }}
                     style={{ ['--wgh-color' as string]: gcolor } as CSSProperties}
                     onContextMenu={e => { e.preventDefault(); e.stopPropagation(); setCtx({ x: e.clientX, y: e.clientY, kind: 'group', tag: item.tag }); }}>
                  <button className="wgh-caret" title={item.folded ? 'expand group' : 'collapse group'}
                          onMouseDown={e => e.stopPropagation()}
                          onClick={() => decor.toggleFold(item.tag)}>{item.folded ? '▸' : '▾'}</button>
                  <span className="wgh-dot" style={{ background: gcolor }} />
                  {renaming === item.tag ? (
                    <input className="wgh-rename" autoFocus defaultValue={item.tag}
                           onClick={e => e.stopPropagation()}
                           onKeyDown={e => {
                             e.stopPropagation();
                             if (e.key === 'Enter') { decor.renameGroup(item.tag, (e.target as HTMLInputElement).value); setRenaming(null); }
                             else if (e.key === 'Escape') setRenaming(null);
                           }}
                           onBlur={e => { decor.renameGroup(item.tag, e.target.value); setRenaming(null); }} />
                  ) : (
                    <span className="wgh-name" title="double-click to rename" onDoubleClick={() => setRenaming(item.tag)}>{item.tag}</span>
                  )}
                  <span className="wgh-count">{item.count}</span>
                  <span style={{ flex: 1 }} />
                  <button className="wgh-act" title="group colour / rename / collapse"
                          onMouseDown={e => e.stopPropagation()}
                          onClick={e => { e.stopPropagation(); setCtx({ x: e.clientX, y: e.clientY, kind: 'group', tag: item.tag }); }}>⋯</button>
                </div>
              );
            }
            const t = item.sig;
            // Color precedence: explicit per-signal override → group color →
            // uniform cyan scalar default (buses keep BusWave's own styling).
            const sigColor = lookupSignalMeta(decor.colors, t);
            const radixOverride = lookupSignalMeta(decor.radices, t);
            const stateLike = /(?:^|_)(?:state|fsm)(?:_|$)/i.test(String(t.signalName || t.name || ''));
            const hasParamMap = !!Object.keys(decor.paramValueMap || {}).length;
            const valueMap = (radixOverride === 'FSM' || radixOverride === 'PARAM' || (!radixOverride && stateLike && hasParamMap))
              ? decor.paramValueMap
              : undefined;
            const rowRadix = radixOverride || (valueMap ? 'FSM' : (t.radix || 'HEX'));
            const groupColor = item.tag ? decor.groups[item.tag]?.color : undefined;
            const color = sigColor || groupColor || (!t.isBus ? '#4dd0e1' : undefined);
            const baseName = showSignalHierarchy && t.scope
              ? stripTopScope(`${t.scope}.${t.name}`, ipName)   // drop the always-present top-module prefix
              : t.name;
            // Pinned but not present in this VCD dump → flag it so "Add to
            // waveform" gives feedback instead of looking like it did nothing.
            const displayName = t.notInVcd ? `${baseName}  ⚠ not in VCD` : baseName;
            const rowKey = waveSignalKey(t);
            const dropId = `sig/${rowKey}`;
            return (
              <div
                key={(t.scope || '') + '/' + t.name + '/' + di}
                className={`wave-dnd-row${dndClass(dropId)}`}
                draggable
                onDragStart={e => {
                  // Only start a reorder when grabbed in the label zone; a drag
                  // started over the plot is a zoom/cursor gesture → cancel it.
                  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
                  if (e.clientX - rect.left > nameW + 90) { e.preventDefault(); return; }
                  // Drag the WHOLE multi-selection together when this row is part
                  // of it — otherwise reordering moved only the grabbed row even
                  // with several selected.
                  const selectedKeys = traceList.filter(isRowSelected).map(waveSignalKey);
                  const keys = (isRowSelected(t) && selectedKeys.length > 1) ? selectedKeys : [rowKey];
                  const label = keys.length > 1 ? `${keys.length} signals` : (t.name || rowKey);
                  dragItemRef.current = { kind: 'sig', keys, label };
                  e.dataTransfer.effectAllowed = 'all';
                  e.dataTransfer.setData('text/plain', t.name || rowKey);
                  // Dropping this row on the source pane jumps there (see SourceViewer).
                  e.dataTransfer.setData('application/x-sim-signal-jump',
                    JSON.stringify({ name: t.name || rowKey, scope: t.scope || '' }));
                  setWaveDragPreview(e, label);
                }}
                onDragOver={e => onWaveDragOver(e, dropId, [rowKey])}
                onDragLeave={() => setDropHint(null)}
                onDrop={e => onWaveDrop(e, [rowKey])}
                onDragEnd={() => { dragItemRef.current = null; setDropHint(null); }}
                onMouseDown={e => handleWaveRowMouseDown(e, t)}
                onContextMenu={e => { e.preventDefault(); e.stopPropagation(); setCtx({ x: e.clientX, y: e.clientY, kind: 'sig', sig: t }); }}
                style={{
                  boxShadow: [
                    item.tag ? `inset 2px 0 0 ${groupColor || '#3a4660'}` : '',
                    dndShadow(dropId),
                  ].filter(Boolean).join(', ') || undefined,
                  ...(color ? ({ '--wave-color-override': color } as CSSProperties) : {}),
                }}
              >
                <WaveRow
                  name={displayName}
                  scope={t.scope}
                  trace={t.trace}
                  width={waveWidth}
                  isBus={t.isBus}
                  radix={rowRadix}
                  selected={waveSignalMatches(t, selectedSig, selectedSigScope) || isRowSelected(t)}
                  colorHint={color}
                  valueMap={valueMap}
                  onClick={(e: ReactMouseEvent<HTMLDivElement>) => handleWaveRowClick(e, t)}
                />
              </div>
            );
          })}
          <div ref={plotAreaRef} style={{ position: 'absolute', top: 0, bottom: 0, left: plotLeft, width: waveWidth, pointerEvents: 'none' }}>
            <WaveCursor time={waveCursor}  kind="a" width={waveWidth} />
            <WaveCursor time={waveCursorB} kind="b" width={waveWidth} />
            {/* drag-to-zoom rubber-band selection — coords are relative to this
                same plot element (measured via plotAreaRef), so the box tracks
                the cursor exactly with no label-width offset. */}
            {sel && Math.abs(sel.x1 - sel.x0) > 1 && (
              <div style={{
                position: 'absolute', top: 0, bottom: 0,
                left: Math.min(sel.x0, sel.x1),
                width: Math.abs(sel.x1 - sel.x0),
                background: 'color-mix(in oklch, var(--accent) 22%, transparent)',
                border: '1px solid var(--accent)',
                pointerEvents: 'none', zIndex: 4,
              }} />
            )}
          </div>
        </div>
      </div>
      {/* Chat/command bar — type to drive the two cursors + zoom. */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
        padding: '4px 8px', borderTop: '1px solid var(--line)', background: 'var(--bg-2)',
      }}>
        <span title="waveform commands" style={{ color: 'var(--cyan)', fontSize: 12 }}>⌨</span>
        <input
          value={cmdText}
          onChange={e => setCmdText(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') { e.preventDefault(); runCmd(); }
            e.stopPropagation();  // don't trigger the Verdi keyboard shortcuts
          }}
          placeholder="cursor / zoom by command —  a 5000 b 15000 · zoom 1000 8000 · a..b · fit"
          spellCheck={false}
          style={{
            flex: 1, minWidth: 0, background: 'var(--bg)', color: 'var(--fg)',
            border: '1px solid var(--line)', borderRadius: 3, padding: '2px 6px',
            fontSize: 10, fontFamily: 'var(--mono)',
          }}
        />
        {cmdEcho && (
          <span style={{ color: 'var(--fg-mute)', fontSize: 9, fontFamily: 'var(--mono)', whiteSpace: 'nowrap', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {cmdEcho}
          </span>
        )}
      </div>
      {/* Right-click menu — colour (signal/group), move up/down, grouping. */}
      {ctx && (
        <div className="wave-ctx-menu" style={{ position: 'fixed', left: ctx.x, top: ctx.y, zIndex: 50 }}
             onClick={e => e.stopPropagation()} onContextMenu={e => e.preventDefault()}>
          <div className="wcm-swatches">
            {WAVE_COLOR_PALETTE.map(c => (
              <button key={c} className="wcm-swatch" style={{ background: c }} title={c}
                onClick={() => {
                  if (ctx.kind === 'group' && ctx.tag) decor.setGroupColor(ctx.tag, c);
                  else if (ctx.sig) decor.setSignalColor(ctxTargetNames, c);
                  setCtx(null);
                }} />
            ))}
          </div>
          <button className="wcm-item" onClick={() => {
            if (ctx.kind === 'group' && ctx.tag) decor.setGroupColor(ctx.tag, null);
            else if (ctx.sig) decor.setSignalColor(ctxTargetNames, null);
            setCtx(null);
          }}>reset colour{ctx.kind === 'sig' && ctxTargetCount > 1 ? ` · ${ctxTargetCount} selected` : ''}</button>

          {ctx.kind === 'sig' && ctx.sig && (
            <>
              <div className="wcm-sep" />
              <div className="wcm-label">radix{ctxTargetCount > 1 ? ` · ${ctxTargetCount} selected` : ''}</div>
              <div className="wcm-radices">
                {['HEX', 'DEC', 'BIN', 'PARAM'].map(radix => (
                  <button key={radix} className="wcm-radix" onClick={() => {
                    decor.setSignalRadix(ctxTargetNames, radix === 'PARAM' ? 'FSM' : radix);
                    setCtx(null);
                  }}>{radix}</button>
                ))}
              </div>
              <button className="wcm-item" onClick={() => { decor.setSignalRadix(ctxTargetNames, null); setCtx(null); }}>reset radix</button>

              <div className="wcm-sep" />
              <button className="wcm-item" onClick={() => { decor.moveSignal(waveSignalKey(ctx.sig!), -1); setCtx(null); }}>↑ move up</button>
              <button className="wcm-item" onClick={() => { decor.moveSignal(waveSignalKey(ctx.sig!), 1); setCtx(null); }}>↓ move down</button>
              <button className="wcm-item" onClick={() => {
                onDeleteSignalsFromWave(ctxDeleteItems);
                setCtx(null);
              }}>⌫ delete {ctxDeleteItems.length > 1 ? `${ctxDeleteItems.length} selected` : 'from waveform'}</button>
              <div className="wcm-sep" />
              <button className="wcm-item" onClick={() => {
                const name = 'group ' + (Object.keys(decor.groups).length + 1);
                decor.assignGroup(ctxTargetNames, name);
                setCtx(null); setRenaming(name);
              }}>＋ new group{ctxTargetCount > 1 ? ` · ${ctxTargetCount} selected` : ''}</button>
              {Object.keys(decor.groups).map(tag => (
                <button key={tag} className="wcm-item" onClick={() => { decor.assignGroup(ctxTargetNames, tag); setCtx(null); }}>→ add to “{tag}”</button>
              ))}
              {ctxIsGrouped && (
                <button className="wcm-item" onClick={() => { decor.ungroup(ctxTargetNames); setCtx(null); }}>✕ remove from group</button>
              )}
            </>
          )}
          {ctx.kind === 'group' && ctx.tag && (
            <>
              <div className="wcm-sep" />
              <button className="wcm-item" onClick={() => { const tag = ctx.tag!; setCtx(null); setRenaming(tag); }}>✎ rename group</button>
              <button className="wcm-item" onClick={() => { decor.toggleFold(ctx.tag!); setCtx(null); }}>{decor.groups[ctx.tag]?.folded ? '▾ expand' : '▸ collapse'}</button>
            </>
          )}
        </div>
      )}
    </div>
  );
};
