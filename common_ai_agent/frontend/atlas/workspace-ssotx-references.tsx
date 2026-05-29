/* workspace-ssotx-references.tsx — strangler-fig sibling of workspace-ssot-extract.tsx.
 *
 * Owns the cross-reference token + linkify layer (the only JSX-bearing group):
 *   - buildReferenceTokens  (registers/features/fsm/irqs → identifier map)
 *   - _refKindColor / _viewIdForRefKind (kind → color / digest-view id)
 *   - linkifyReferences     (prose → hoverable cross-reference chips, JSX)
 *
 * Self-contained: depends only on react. INERT mirror: legacy workspace.jsx
 * still serves the live app. These symbols are re-exported from
 * workspace-ssot-extract.tsx so the public contract is unchanged.
 */
import { type ReactNode } from 'react';

// Build a flat map of "known" identifiers → {kind, description, ref} so
// any prose can be turned into hoverable cross-reference chips. The kinds
// we care about: register (CR), register field (CR.EN), feature (Baud
// generator), interrupt (TX_EMPTY), FSM state (IDLE). Lowercase keys for
// case-insensitive matching but original casing preserved in the chip.
export const buildReferenceTokens = ({ registers, features, fsmMachines, irqs }: any): Map<string, any> => {
  const map = new Map<string, any>();
  const add = (token: any, entry: any) => {
    const key = String(token || '').trim();
    if (!key || key.length < 2) return;
    const lower = key.toLowerCase();
    if (map.has(lower)) return;
    map.set(lower, { ...entry, label: key });
  };
  for (const reg of registers || []) {
    add(reg.name, {
      kind: 'register',
      description: [
        reg.offset && `offset ${reg.offset}`,
        reg.access && `access ${reg.access}`,
        reg.reset && `reset ${reg.reset}`,
        reg.description,
      ].filter(Boolean).join(' · '),
    });
    for (const f of (reg.fields || [])) {
      add(`${reg.name}.${f.name}`, {
        kind: 'field',
        description: [
          f.bits && `bits ${f.bits}`,
          f.access && `access ${f.access}`,
          f.reset && `reset ${f.reset}`,
          f.description,
        ].filter(Boolean).join(' · '),
      });
    }
  }
  for (const feat of features || []) {
    add(feat.name, {
      kind: 'feature',
      description: feat.description || feat.datapath || feat.trigger || '',
    });
  }
  for (const m of fsmMachines || []) {
    for (const s of (m.states || [])) {
      add(s, {
        kind: 'state',
        description: `FSM ${m.name} state${String(m.resetState || '').trim() === String(s).trim() ? ' (reset)' : ''}`,
      });
    }
  }
  for (const irq of irqs || []) {
    add(irq.name, {
      kind: 'interrupt',
      description: [irq.polarity && `polarity ${irq.polarity}`, irq.mask && `mask ${irq.mask}`, irq.description].filter(Boolean).join(' · '),
    });
  }
  return map;
};

export const _refKindColor = (kind: string): string => ({
  register: 'var(--cyan)',
  field: 'var(--accent)',
  feature: 'var(--magenta)',
  state: 'var(--magenta)',
  interrupt: 'var(--warn)',
} as Record<string, string>)[kind] || 'var(--accent)';

export const _viewIdForRefKind = (kind: string): string => ({
  register: 'registers',
  field: 'registers',
  feature: 'features',
  state: 'fsm',
  interrupt: 'overview',
  interface: 'interfaces',
  scenario: 'scenarios',
} as Record<string, string>)[kind] || 'overview';

export const linkifyReferences = (text: any, tokenMap: Map<string, any> | null | undefined, onJump: any): ReactNode => {
  const raw = String(text || '');
  if (!raw || !tokenMap || !tokenMap.size) return raw;
  const tokens = Array.from(tokenMap.keys()).sort((a, b) => b.length - a.length);
  const escaped = tokens.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  if (!escaped) return raw;
  const re = new RegExp(`(?<![A-Za-z0-9_.])(${escaped})(?![A-Za-z0-9_])`, 'gi');
  const out: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = re.exec(raw)) !== null) {
    if (m.index > last) out.push(raw.slice(last, m.index));
    const entry = tokenMap.get(m[0].toLowerCase());
    if (entry) {
      const color = _refKindColor(entry.kind);
      const jumpId = _viewIdForRefKind(entry.kind);
      const clickable = typeof onJump === 'function';
      out.push(
        <span key={`ref-${key++}`}
          title={entry.description ? `${entry.kind}: ${entry.label} — ${entry.description}` : `${entry.kind}: ${entry.label}`}
          onClick={clickable ? () => onJump(jumpId) : undefined}
          style={{
            fontFamily: 'var(--mono)',
            fontSize: '0.9em',
            padding: '1px 5px',
            borderRadius: 3,
            background: `color-mix(in oklch, ${color} 12%, transparent)`,
            color,
            border: `1px solid color-mix(in oklch, ${color} 32%, transparent)`,
            cursor: clickable ? 'pointer' : 'help',
          }}>{m[0]}</span>
      );
    } else {
      out.push(m[0]);
    }
    last = m.index + m[0].length;
  }
  if (last < raw.length) out.push(raw.slice(last));
  return out;
};
