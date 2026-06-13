// sim-debug-header.tsx — the single unified header bar extracted from
// sim-debug.tsx (strangler-fig split). Behavior-identical: this is the SAME
// MODE / VCD-picker / cursor-readout / expand-mode header row, plus the
// `ModeBtn` / `ExpandBtn` button helpers and the `selectTopTab` dispatcher that
// only the header used. The root SimDebug closure still owns all the state;
// the header receives the slice it reads + the setters it drives as a typed
// props bundle.
//
// Load order: imported by sim-debug.tsx. Owns no window bridge.
import type { ReactNode } from 'react';
import type { VcdData } from './sim-debug-helpers';
import {
  formatFrequencyFromDelta,
  formatTimeDeltaDisplay,
  formatTimeDisplay,
  TIME_DISPLAY_UNITS,
} from './sim-debug-helpers';

interface DebugHeaderProps {
  summaryOnly: boolean;
  topTab: string;
  setTopTab: (id: string) => void;
  setLeftTab: (v: string) => void;
  expand: string;
  setExpand: (v: string) => void;
  vcdActive: string;
  setVcdActive: (v: string) => void;
  vcdFiles: Array<{ path: string }>;
  vcdData: VcdData | null;
  waveCursor: number;
  waveCursorB: number;
  timeDisplayUnit: string;
  setTimeDisplayUnit: (v: string) => void;
  cursorMetric: string;
  setCursorMetric: (v: string) => void;
}

export const DebugHeader = ({
  summaryOnly, topTab, setTopTab, setLeftTab, expand, setExpand,
  vcdActive, setVcdActive, vcdFiles, vcdData, waveCursor, waveCursorB,
  timeDisplayUnit, setTimeDisplayUnit, cursorMetric, setCursorMetric,
}: DebugHeaderProps): ReactNode => {
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

  const ts = vcdData?.timescale || 'ns';
  const delta = waveCursorB - waveCursor;
  const cursorMetricText = cursorMetric === 'freq'
    ? formatFrequencyFromDelta(delta, ts)
    : formatTimeDeltaDisplay(delta, ts, timeDisplayUnit);

  return (
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
          whiteSpace: 'nowrap', flexShrink: 0,
        }}>
          ✓ {vcdData.signals!.length} sig · t={vcdData.timeRange![0]}–{vcdData.timeRange![1]} {vcdData.timescale}
        </span>
      )}
      {!summaryOnly && (
        <>
          <span style={{ color: 'var(--line-2)', margin: '0 4px' }}>│</span>
          <span style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>res</span>
          <select
            value={timeDisplayUnit}
            onChange={e => setTimeDisplayUnit(e.target.value)}
            title={`display time resolution (VCD timescale: ${ts})`}
            style={{
              background: 'var(--bg)', color: 'var(--fg)', border: '1px solid var(--line)',
              padding: '1px 4px', fontSize: 10, fontFamily: 'var(--mono)',
            }}
          >
            {TIME_DISPLAY_UNITS.map(u => <option key={u} value={u}>{u}</option>)}
          </select>
          <span style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>cur A</span>
          <span style={{ color: 'var(--accent)', fontWeight: 600, fontFamily: 'var(--mono)' }}>{formatTimeDisplay(waveCursor, ts, timeDisplayUnit)}</span>
          <span style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>B</span>
          <span style={{ color: 'var(--cyan)', fontWeight: 600, fontFamily: 'var(--mono)' }}>{formatTimeDisplay(waveCursorB, ts, timeDisplayUnit)}</span>
          <select
            value={cursorMetric}
            onChange={e => setCursorMetric(e.target.value)}
            title="show A-B as interval or frequency"
            style={{
              background: 'var(--bg)', color: 'var(--fg)', border: '1px solid var(--line)',
              padding: '1px 4px', fontSize: 10, fontFamily: 'var(--mono)',
            }}
          >
            <option value="delta">Δ</option>
            <option value="freq">freq</option>
          </select>
          <span style={{ color: 'var(--magenta)', fontWeight: 600, fontFamily: 'var(--mono)' }}>{cursorMetricText}</span>
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
  );
};
