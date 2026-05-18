// debug-inline-cards.jsx — inline evidence cards rendered INSIDE the
// chat thread of sim_debug workflow. Extracted from debug-var3.jsx so
// the v4 Tri-surface layout can keep its persistent wave panel AND
// inline clips inside the conversation.
//
// Each card consumes a tool_result payload from the agent (vcd.trace,
// src.read, signal.compare, …) and renders the matching widget. The
// card click handler bumps the cross-panel state hooks (waveCursor /
// selectedSig) so the persistent right-side wave panel scrolls/cursors
// to match.

(function () {
  'use strict';

  // Mini wave clip — 3-4 signals, cursor, optional X-prop overlay.
  // Reuses the same WaveRow / TimeRuler / WaveCursor primitives the
  // persistent right panel uses, so the visual style stays consistent
  // between inline-card and full-panel renderings.
  window.InlineWaveClip = ({
    signals,           // [{ key, label, isBus, radix }]
    cursor,            // ns (optional)
    width = 700,
    xPropFrom,
    xPropTo,
    pins,              // [{ t, kind, top, title }]
    onClick,           // bubbles to parent for cross-panel sync
  }) => {
    const rows = (signals || []).map(s => ({
      ...s,
      trace: (window.MOCK_TRACES || {})[s.key] || [],
    }));
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
        {window.TimeRuler && <window.TimeRuler width={width} />}
        <div style={{ position: 'relative' }}>
          {rows.map(s => (
            window.WaveRow ? (
              <window.WaveRow
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
            {cursor != null && window.WaveCursor && (
              <window.WaveCursor time={cursor} label={`t=${cursor}ns`} kind="a" width={width} />
            )}
            {xPropFrom != null && window.XPropOverlay && (
              <window.XPropOverlay from={xPropFrom} to={xPropTo} width={width} />
            )}
            {pins && window.WavePin && pins.map((p, i) => (
              <window.WavePin
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

  // Source diff card — a few SV lines with one highlighted as the bug
  // candidate. Used when the agent reports "root cause at file:line".
  window.SourceDiffCard = ({ file, fromLine, toLine, highlight, cursor, onClick }) => (
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
      {window.SourceCode ? (
        <window.SourceCode
          highlight={highlight || []}
          cursor={cursor}
          fromLine={fromLine}
          toLine={toLine}
        />
      ) : null}
    </div>
  );

  // Compact signal table — name | last value | edges in [t1..t2].
  // Cheap alternative to a full waveform when the agent just wants to
  // show "here are the 5 signals I looked at and their final state".
  window.SignalTableCard = ({ rows, onClick }) => (
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
          <span>{r.last}</span>
          <span style={{ textAlign: 'right' }}>{r.edges ?? 0}</span>
          <span style={{ paddingLeft: 12, color: 'var(--fg-mute)' }}>{r.note || ''}</span>
        </div>
      ))}
    </div>
  );

  // Router — picks the right card based on tool_result.tool. Components
  // that receive raw tool_result payloads can just render <InlineCard
  // result={r} onCardClick={...} /> and forget the dispatching.
  window.InlineCard = ({ result, onCardClick }) => {
    if (!result || !result.tool) return null;
    const tool = result.tool;
    const data = result.data || {};
    if (tool === 'vcd.trace' || tool === 'wave.clip') {
      return (
        <window.InlineWaveClip
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
        <window.SourceDiffCard
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
        <window.SignalTableCard
          rows={data.rows || []}
          onClick={onCardClick && (() => onCardClick({ kind: 'signal_table' }))}
        />
      );
    }
    return null;
  };
})();
