// sim-debug-shortcuts.tsx — the WAVE SHORTCUTS help overlay extracted from
// sim-debug.tsx (strangler-fig split). Behavior-identical: this is the SAME
// modal markup that was rendered inline inside the wave band when `showHelp`
// was true. It closes over NO root state — it only needs `show` and an
// `onClose` callback, so it lifts out cleanly as a prop-driven presentational
// component.
//
// Load order: imported by sim-debug.tsx. Owns no window bridge.
import type { ReactNode } from 'react';

interface WaveShortcutsOverlayProps {
  show: boolean;
  onClose: () => void;
}

// The keyboard-shortcut rows shown in the overlay. Static data — kept here so
// the table and its source of truth live together.
const SHORTCUT_ROWS: Array<{ keys: string[]; desc: string }> = [
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
];

export const WaveShortcutsOverlay = ({ show, onClose }: WaveShortcutsOverlayProps): ReactNode => {
  if (!show) return null;
  return (
    <div
      onClick={onClose}
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
        {SHORTCUT_ROWS.map((row, i) => (
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
  );
};
