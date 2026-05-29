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
import type { ReactNode, CSSProperties, WheelEvent as ReactWheelEvent } from 'react';
import { RangeInput } from './sim-debug-panels';
import type { VcdData, VcdSignal } from './sim-debug-helpers';
import { waveSignalMatches } from './sim-debug-helpers';
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
  showSignalHierarchy: boolean;
  selectedSig: string;
  selectedSigScope: string;
  onSelectWaveSignal: (signalName: string, signalScope?: string) => void;
  jumpToWaveEdge: (edgeTime: number) => void;
}

export const WaveBand = ({
  eff, showHelp, setShowHelp, vcdActive, effRange, vcdData, setViewRange,
  zoomIn, zoomOut, zoomFit, zoomToCursors, panBy, waveWidth, traceList,
  ipName, waveCursor, waveCursorB, showSignalHierarchy, selectedSig,
  selectedSigScope, onSelectWaveSignal, jumpToWaveEdge,
}: WaveBandProps): ReactNode => {
  return (
    <div className="wave-panel" style={{
      flex: eff.showSource ? `${Math.round((1 - eff.th) * 100)} ${Math.round((1 - eff.th) * 100)} 0` : '1 1 0',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      borderTop: eff.showSource ? '1px solid var(--line)' : 'none',
      position: 'relative',
    }}>
      <WaveShortcutsOverlay show={showHelp} onClose={() => setShowHelp(false)} />
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
  );
};
