// debug-inline-cards.tsx — TypeScript migration of debug-inline-cards.jsx.
// inline evidence cards rendered INSIDE the chat thread of sim_debug
// workflow. Extracted from debug-var3.jsx so the v4 Tri-surface layout can
// keep its persistent wave panel AND inline clips inside the conversation.
//
// Each card consumes a tool_result payload from the agent (vcd.trace,
// src.read, signal.compare, …) and renders the matching widget. The
// card click handler bumps the cross-panel state hooks (waveCursor /
// selectedSig) so the persistent right-side wave panel scrolls/cursors
// to match.
//
// Cross-file deps (WaveRow / TimeRuler / WaveCursor / XPropOverlay /
// WavePin / SourceCode / MOCK_TRACES) are still owned by the unmigrated
// debug-shared.jsx, so they are kept as window.* lookups. They are not
// (yet) in types/atlas-window.d.ts, so a local typed view of the window
// surface is used to keep the references type-checked without editing the
// shared ambient declaration.
import type { ReactNode } from 'react';

// ── Local typed view of the cross-file window globals this file reads. ──
// Owned by debug-shared.jsx (not yet migrated); mirror their runtime
// shapes loosely enough to preserve behavior. Remove once debug-shared
// migrates and these become real imports.
interface TraceSample {
  t: number;
  v: unknown;
}

interface WaveRowProps {
  key?: string | number;
  name?: string;
  trace: TraceSample[];
  width: number;
  isBus?: boolean;
  radix?: string;
  selected: boolean;
  onClick: () => void;
}

interface TimeRulerProps {
  width: number;
}

interface WaveCursorProps {
  time: number;
  label: string;
  kind: string;
  width: number;
}

interface XPropOverlayProps {
  from: number;
  to?: number;
  width: number;
}

interface WavePinProps {
  key?: string | number;
  time: number;
  kind: string;
  top: number;
  width: number;
  title?: string;
}

interface SourceCodeProps {
  highlight: number[];
  cursor?: number;
  fromLine: number;
  toLine: number;
}

interface DebugSharedWindow {
  MOCK_TRACES?: Record<string, TraceSample[]>;
  TimeRuler?: (props: TimeRulerProps) => ReactNode;
  WaveRow?: (props: WaveRowProps) => ReactNode;
  WaveCursor?: (props: WaveCursorProps) => ReactNode;
  XPropOverlay?: (props: XPropOverlayProps) => ReactNode;
  WavePin?: (props: WavePinProps) => ReactNode;
  SourceCode?: (props: SourceCodeProps) => ReactNode;
}

// Typed accessor for the cross-file globals. Cast preserves the exact
// runtime `window.X` lookups while giving TS the shapes above.
const sharedWin = window as unknown as DebugSharedWindow;

// ── InlineWaveClip ──
// Mini wave clip — 3-4 signals, cursor, optional X-prop overlay.
// Reuses the same WaveRow / TimeRuler / WaveCursor primitives the
// persistent right panel uses, so the visual style stays consistent
// between inline-card and full-panel renderings.
export interface InlineWaveClipSignal {
  key: string;
  label?: string;
  isBus?: boolean;
  radix?: string;
}

export interface InlineWavePin {
  t: number;
  kind: string;
  top?: number;
  title?: string;
}

export interface InlineWaveClipProps {
  signals?: InlineWaveClipSignal[]; // [{ key, label, isBus, radix }]
  cursor?: number;                  // ns (optional)
  width?: number;
  xPropFrom?: number;
  xPropTo?: number;
  pins?: InlineWavePin[];           // [{ t, kind, top, title }]
  onClick?: () => void;             // bubbles to parent for cross-panel sync
}

export const InlineWaveClip = ({
  signals,           // [{ key, label, isBus, radix }]
  cursor,            // ns (optional)
  width = 700,
  xPropFrom,
  xPropTo,
  pins,              // [{ t, kind, top, title }]
  onClick,           // bubbles to parent for cross-panel sync
}: InlineWaveClipProps): ReactNode => {
  const rows = (signals || []).map(s => ({
    ...s,
    trace: (sharedWin.MOCK_TRACES || {})[s.key] || [],
  }));
  const TimeRuler = sharedWin.TimeRuler;
  const WaveRow = sharedWin.WaveRow;
  const WaveCursor = sharedWin.WaveCursor;
  const XPropOverlay = sharedWin.XPropOverlay;
  const WavePin = sharedWin.WavePin;
  return (
    <div
      onClick={onClick}
      style={{
        background: 'var(--bg)',
        border: '1px solid var(--line)',
        borderRadius: 4,
        overflow: 'hidden',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      {TimeRuler && <TimeRuler width={width} />}
      <div style={{ position: 'relative' }}>
        {rows.map(s => (
          WaveRow ? (
            <WaveRow
              key={s.key}
              name={s.label}
              trace={s.trace}
              width={width}
              isBus={s.isBus}
              radix={s.radix || 'HEX'}
              selected={false}
              onClick={() => {}}
            />
          ) : null
        ))}
        <div style={{
          position: 'absolute', top: 0, bottom: 0, left: 280,
          width, pointerEvents: 'none',
        }}>
          {cursor != null && WaveCursor && (
            <WaveCursor time={cursor} label={`t=${cursor}ns`} kind="a" width={width} />
          )}
          {xPropFrom != null && XPropOverlay && (
            <XPropOverlay from={xPropFrom} to={xPropTo} width={width} />
          )}
          {pins && WavePin && pins.map((p, i) => (
            <WavePin
              key={i}
              time={p.t}
              kind={p.kind}
              top={p.top || 50}
              width={width}
              title={p.title}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

// ── SourceDiffCard ──
// Source diff card — a few SV lines with one highlighted as the bug
// candidate. Used when the agent reports "root cause at file:line".
export interface SourceDiffCardProps {
  file?: string;
  fromLine?: number;
  toLine?: number;
  highlight?: number[];
  cursor?: number;
  onClick?: () => void;
}

export const SourceDiffCard = ({ file, fromLine, toLine, highlight, cursor, onClick }: SourceDiffCardProps): ReactNode => {
  const SourceCode = sharedWin.SourceCode;
  return (
    <div
      onClick={onClick}
      style={{
        background: 'var(--bg)',
        border: '1px solid var(--line)',
        borderRadius: 4,
        overflow: 'hidden',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <div style={{
        padding: '4px 10px', fontSize: 10, color: 'var(--fg-mute)',
        background: 'var(--bg-2)', borderBottom: '1px solid var(--line)',
        fontFamily: 'var(--mono)',
      }}>
        {file} · L{fromLine}-L{toLine}
      </div>
      {SourceCode ? (
        <SourceCode
          highlight={highlight || []}
          cursor={cursor}
          fromLine={fromLine as number}
          toLine={toLine as number}
        />
      ) : null}
    </div>
  );
};

// ── SignalTableCard ──
// Compact signal table — name | last value | edges in [t1..t2].
// Cheap alternative to a full waveform when the agent just wants to
// show "here are the 5 signals I looked at and their final state".
export interface SignalTableRow {
  name?: string;
  last?: unknown;
  edges?: number;
  note?: string;
  warn?: boolean;
}

export interface SignalTableCardProps {
  rows?: SignalTableRow[];
  onClick?: () => void;
}

export const SignalTableCard = ({ rows, onClick }: SignalTableCardProps): ReactNode => (
  <div
    onClick={onClick}
    style={{
      background: 'var(--bg)',
      border: '1px solid var(--line)',
      borderRadius: 4,
      overflow: 'hidden',
      fontFamily: 'var(--mono)',
      fontSize: 11,
    }}
  >
    <div style={{
      display: 'grid', gridTemplateColumns: '180px 90px 60px 1fr',
      padding: '4px 8px', background: 'var(--bg-2)',
      borderBottom: '1px solid var(--line)', color: 'var(--fg-mute)',
      fontSize: 10,
    }}>
      <span>signal</span>
      <span>last value</span>
      <span style={{ textAlign: 'right' }}>edges</span>
      <span style={{ paddingLeft: 12 }}>note</span>
    </div>
    {(rows || []).map((r, i) => (
      <div key={i} style={{
        display: 'grid', gridTemplateColumns: '180px 90px 60px 1fr',
        padding: '3px 8px', borderBottom: '1px solid var(--line)',
        color: r.warn ? 'var(--err)' : 'var(--fg)',
      }}>
        <span style={{ color: 'var(--accent)' }}>{r.name}</span>
        <span>{r.last as ReactNode}</span>
        <span style={{ textAlign: 'right' }}>{r.edges ?? 0}</span>
        <span style={{ paddingLeft: 12, color: 'var(--fg-mute)' }}>{r.note || ''}</span>
      </div>
    ))}
  </div>
);

// ── InlineCard ──
// Router — picks the right card based on tool_result.tool. Components
// that receive raw tool_result payloads can just render <InlineCard
// result={r} onCardClick={...} /> and forget the dispatching.
export interface InlineCardToolData {
  signals?: InlineWaveClipSignal[];
  cursor?: number;
  xPropFrom?: number;
  xPropTo?: number;
  pins?: InlineWavePin[];
  focus?: string;
  file?: string;
  fromLine?: number;
  toLine?: number;
  highlight?: number[];
  rows?: SignalTableRow[];
}

export interface InlineCardResult {
  tool?: string;
  data?: InlineCardToolData;
}

export interface InlineCardClickPayload {
  kind: string;
  cursor?: number;
  signal?: string;
  file?: string;
  line?: number;
}

export interface InlineCardProps {
  result?: InlineCardResult;
  onCardClick?: (payload: InlineCardClickPayload) => void;
}

export const InlineCard = ({ result, onCardClick }: InlineCardProps): ReactNode => {
  if (!result || !result.tool) return null;
  const tool = result.tool;
  const data = result.data || {};
  if (tool === 'vcd.trace' || tool === 'wave.clip') {
    return (
      <InlineWaveClip
        signals={data.signals || []}
        cursor={data.cursor}
        xPropFrom={data.xPropFrom}
        xPropTo={data.xPropTo}
        pins={data.pins || []}
        onClick={onCardClick && (() => onCardClick({
          kind: 'wave', cursor: data.cursor, signal: data.focus,
        }))}
      />
    );
  }
  if (tool === 'src.read' || tool === 'source.diff') {
    return (
      <SourceDiffCard
        file={data.file}
        fromLine={data.fromLine || 1}
        toLine={data.toLine || 30}
        highlight={data.highlight || []}
        cursor={data.cursor}
        onClick={onCardClick && (() => onCardClick({
          kind: 'source', file: data.file, line: data.cursor,
        }))}
      />
    );
  }
  if (tool === 'signal.table') {
    return (
      <SignalTableCard
        rows={data.rows || []}
        onClick={onCardClick && (() => onCardClick({ kind: 'signal_table' }))}
      />
    );
  }
  return null;
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// Remove once all consumers import these directly. These globals are owned
// by THIS file, so the bridge keeps unmigrated .jsx consumers resolving
// window.InlineWaveClip / window.SourceDiffCard / window.SignalTableCard /
// window.InlineCard.
const bridgeWin = window as unknown as {
  InlineWaveClip: typeof InlineWaveClip;
  SourceDiffCard: typeof SourceDiffCard;
  SignalTableCard: typeof SignalTableCard;
  InlineCard: typeof InlineCard;
};
bridgeWin.InlineWaveClip = InlineWaveClip;
bridgeWin.SourceDiffCard = SourceDiffCard;
bridgeWin.SignalTableCard = SignalTableCard;
bridgeWin.InlineCard = InlineCard;
