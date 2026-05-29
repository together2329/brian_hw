/**
 * workspace-ssotp-register-views.tsx
 *
 * Interactive SSOT register + scenario viewers extracted from
 * workspace-ssot-panels.tsx for cohesion and to keep every file under
 * 1000 lines. Owns the register bit-map cluster (_parseBitRange,
 * _accessColor, RegisterBitMap, RegisterBitFieldView) and the interactive
 * players (PipelineTraceDiagram, SsotCommandPalette, SsotScenarioPlayer).
 *
 * These .tsx files are INERT mirrors; the legacy workspace.jsx still serves
 * the live app. Window-sourced values are intentionally typed `any`.
 */
import { useState, useEffect, useMemo, Fragment, type ReactNode } from 'react';

import {
  blockField,
  linkifyReferences,
  _hasMeaningfulRegisterField,
  _hasRegisterDetail,
} from './workspace-ssot-extract';

export const PipelineTraceDiagram = ({ pipeline, transactions, maxTransactions = 4 }: any) => {
  // Build a classic stages × cycles matrix from the SSOT pipeline list.
  // Each transaction enters stage 0 one cycle after the previous one,
  // walking diagonally through subsequent stages, so the user can see
  // the instruction-flow pattern with no SSOT scenario data required.
  const stages = (pipeline || [])
    .map((b: any, i: number) => ({
      name: blockField(b, 'stage') || blockField(b, 'name') || blockField(b, 'id') || `S${i}`,
      cycle: Number(blockField(b, 'cycle') || blockField(b, 'phase') || i),
      action: blockField(b, 'action', 200) || blockField(b, 'description', 200) || '',
    }))
    .filter((s: any) => s.name);
  const txList = (transactions || [])
    .slice(0, maxTransactions)
    .map((b: any, i: number) => blockField(b, 'id') || blockField(b, 'name') || `tx_${i + 1}`)
    .filter(Boolean);
  if (!stages.length) return null;
  if (!txList.length) txList.push('flow');
  const txColors = ['var(--accent)', 'var(--magenta)', 'var(--cyan)', 'var(--warn)'];
  const totalCycles = stages.length + txList.length - 1;
  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 5 }}>
        PIPELINE TRACE — {stages.length} stages × {txList.length} {txList.length === 1 ? 'flow' : 'transactions'}
      </div>
      <div style={{ overflowX: 'auto' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: `minmax(110px, max-content) repeat(${totalCycles}, minmax(60px, 1fr))`,
          gap: 2,
        }}>
          <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, padding: '4px 6px' }}>
            stage \\ cycle
          </div>
          {Array.from({ length: totalCycles }, (_, c) => (
            <div key={`pt-h-${c}`}
              style={{
                color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10,
                textAlign: 'center', padding: '4px 2px', borderBottom: '1px solid var(--line)',
              }}>{c}</div>
          ))}
          {stages.map((stage: any, si: number) => (
            <Fragment key={`pt-row-${stage.name}-${si}`}>
              <div title={stage.action || stage.name}
                style={{
                  fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--fg)',
                  padding: '4px 6px', borderRight: '1px solid var(--line)',
                  fontWeight: 700,
                }}>
                {stage.name}
              </div>
              {Array.from({ length: totalCycles }, (_, c) => {
                // Transaction at column c, row si: tx index = c - si.
                const txIdx = c - si;
                if (txIdx < 0 || txIdx >= txList.length) {
                  return (
                    <div key={`pt-c-${si}-${c}`}
                      style={{ border: '1px solid var(--line)', background: 'transparent', minHeight: 22 }} />
                  );
                }
                const color = txColors[txIdx % txColors.length];
                return (
                  <div key={`pt-c-${si}-${c}`}
                    title={`${stage.name} @ cycle ${c} — ${txList[txIdx]}${stage.action ? `\n${stage.action}` : ''}`}
                    style={{
                      border: `1px solid color-mix(in oklch, ${color} 60%, var(--line))`,
                      background: `color-mix(in oklch, ${color} 22%, transparent)`,
                      color, fontFamily: 'var(--mono)', fontSize: 10, fontWeight: 700,
                      textAlign: 'center', padding: '4px 2px',
                      minHeight: 22, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                    {txList[txIdx]}
                  </div>
                );
              })}
            </Fragment>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
        {txList.map((name: any, i: number) => {
          const color = txColors[i % txColors.length];
          return (
            <span key={`pt-leg-${name}-${i}`}
              style={{
                fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 8px', borderRadius: 999,
                background: `color-mix(in oklch, ${color} 14%, transparent)`,
                color, border: `1px solid color-mix(in oklch, ${color} 35%, transparent)`,
              }}>{name}</span>
          );
        })}
      </div>
    </div>
  );
};

export const SsotCommandPalette = ({ items, onJump }: any) => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [sel, setSel] = useState(0);
  useEffect(() => {
    const handler = (e: any) => {
      const isCmd = (e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K');
      if (isCmd) {
        e.preventDefault();
        setOpen(o => !o);
        setQuery('');
        setSel(0);
      } else if (e.key === 'Escape' && open) {
        e.preventDefault();
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);
  if (!open) return null;
  const q = query.trim().toLowerCase();
  const filtered = (items || [])
    .filter((it: any) => !q || it.label.toLowerCase().includes(q) || (it.kind || '').toLowerCase().includes(q) || (it.detail || '').toLowerCase().includes(q))
    .slice(0, 40);
  const handleSelect = (item: any) => {
    setOpen(false);
    setQuery('');
    if (item && typeof onJump === 'function' && item.viewId) onJump(item.viewId);
  };
  const kindColor = (kind: any) => (({
    register: 'var(--cyan)',
    field: 'var(--accent)',
    feature: 'var(--magenta)',
    state: 'var(--magenta)',
    interrupt: 'var(--warn)',
    scenario: 'var(--accent)',
    interface: 'var(--cyan)',
  } as Record<string, string>)[kind] || 'var(--fg-mute)');
  return (
    <div onClick={() => setOpen(false)}
      style={{
        position: 'fixed', inset: 0,
        background: 'color-mix(in oklch, var(--bg-1) 70%, transparent)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        zIndex: 9999, paddingTop: '12vh', backdropFilter: 'blur(2px)',
      }}>
      <div onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--bg-1)', border: '1px solid var(--accent)', borderRadius: 6,
          width: 640, maxWidth: '92vw', overflow: 'hidden',
          boxShadow: '0 16px 64px rgba(0,0,0,0.45)',
        }}>
        <input autoFocus value={query}
          onChange={e => { setQuery(e.target.value); setSel(0); }}
          onKeyDown={e => {
            if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => Math.min(filtered.length - 1, s + 1)); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => Math.max(0, s - 1)); }
            else if (e.key === 'Enter') { e.preventDefault(); handleSelect(filtered[sel]); }
          }}
          placeholder="Jump to register / field / feature / state / interrupt / scenario..."
          style={{
            width: '100%', padding: '12px 16px', background: 'transparent',
            border: 'none', borderBottom: '1px solid var(--line)',
            color: 'var(--fg)', fontSize: 14, fontFamily: 'var(--mono)',
            outline: 'none', boxSizing: 'border-box',
          }} />
        <div style={{ maxHeight: '54vh', overflowY: 'auto' }}>
          {filtered.length ? filtered.map((item: any, i: number) => (
            <div key={`pal-${item.kind}-${item.label}-${i}`}
              onClick={() => handleSelect(item)}
              onMouseEnter={() => setSel(i)}
              style={{
                padding: '7px 16px', cursor: 'pointer',
                background: i === sel ? 'color-mix(in oklch, var(--accent) 16%, transparent)' : 'transparent',
                display: 'grid', gridTemplateColumns: '64px minmax(0, 1.4fr) minmax(0, 1.2fr) 90px',
                alignItems: 'baseline', gap: 12, fontFamily: 'var(--mono)', fontSize: 12,
                borderBottom: '1px solid var(--line)',
              }}>
              <span style={{
                color: kindColor(item.kind), textTransform: 'uppercase', letterSpacing: '0.06em',
                fontSize: 10, fontWeight: 700,
              }}>{item.kind}</span>
              <span style={{ color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.label}
              </span>
              <span style={{ color: 'var(--fg-mute)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.detail || ''}
              </span>
              <span style={{ color: 'var(--fg-mute)', fontSize: 10, textAlign: 'right' }}>{item.viewId}</span>
            </div>
          )) : (
            <div style={{ padding: '14px 16px', color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12 }}>
              No matches for &ldquo;{query}&rdquo;.
            </div>
          )}
        </div>
        <div style={{
          padding: '6px 16px', fontFamily: 'var(--mono)', fontSize: 10,
          color: 'var(--fg-mute)', borderTop: '1px solid var(--line)',
          display: 'flex', justifyContent: 'space-between',
        }}>
          <span>↑/↓ navigate · ↵ jump · esc close</span>
          <span>{filtered.length}/{(items || []).length} entries</span>
        </div>
      </div>
    </div>
  );
};

export const _parseBitRange = (raw: any): { hi: number; lo: number } | null => {
  // Accepts "[7:0]", "7:0", "[0]", "0", "31:24", "15..0".
  const txt = String(raw || '').trim().replace(/^\[|\]$/g, '');
  if (!txt) return null;
  const m = txt.match(/^(\d+)\s*(?::|\.\.)\s*(\d+)$/);
  if (m) {
    const a = parseInt(m[1], 10);
    const b = parseInt(m[2], 10);
    if (!Number.isFinite(a) || !Number.isFinite(b)) return null;
    return { hi: Math.max(a, b), lo: Math.min(a, b) };
  }
  const single = parseInt(txt, 10);
  if (Number.isFinite(single)) return { hi: single, lo: single };
  return null;
};

export const _accessColor = (access: any): string => {
  const a = String(access || '').toLowerCase();
  if (/^rw|^w\b/.test(a)) return 'var(--accent)';
  if (/^ro\b|^r\b/.test(a)) return 'var(--cyan)';
  if (/wo|w1c|w0c|w1s|wac/.test(a)) return 'var(--magenta)';
  if (/rsvd|reserved/.test(a)) return 'var(--fg-mute)';
  return 'var(--accent)';
};

export const RegisterBitMap = ({ width, fields }: any) => {
  const w = Math.max(1, Math.min(64, parseInt(width || '32', 10) || 32));
  const fieldByBit: any[] = Array(w).fill(null);
  for (const f of fields || []) {
    const r = _parseBitRange(f.bits);
    if (!r) continue;
    for (let i = r.lo; i <= r.hi; i++) {
      if (i >= 0 && i < w && !fieldByBit[i]) fieldByBit[i] = f;
    }
  }
  // Collapse consecutive same-field cells into spans.
  const segments: any[] = [];
  for (let i = 0; i < w; i++) {
    const f = fieldByBit[i];
    if (segments.length && segments[segments.length - 1].field === f) {
      segments[segments.length - 1].span += 1;
      segments[segments.length - 1].hi = i;
    } else {
      segments.push({ field: f, span: 1, lo: i, hi: i });
    }
  }
  // MSB-on-left convention for register-map readers.
  const segsLR = [...segments].reverse();
  const labelsLR = segsLR.map((seg: any, idx: number) => {
    const f = seg.field;
    if (!f) {
      return (
        <div key={`bm-rsv-${idx}-${seg.lo}-${seg.hi}`}
          title={`reserved [${seg.hi}:${seg.lo}]`}
          style={{
            flex: `${seg.span} ${seg.span} 0`, minWidth: 0,
            background: 'repeating-linear-gradient(45deg, var(--bg-1) 0 4px, var(--bg-2) 4px 8px)',
            border: '1px solid var(--line)',
            color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 9,
            textAlign: 'center', padding: '6px 2px', overflow: 'hidden',
            textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>—</div>
      );
    }
    const color = _accessColor(f.access);
    const range = seg.hi === seg.lo ? `[${seg.hi}]` : `[${seg.hi}:${seg.lo}]`;
    const tooltip = [
      f.name && `field: ${f.name}`,
      f.access && `access: ${f.access}`,
      f.reset !== undefined && f.reset !== null && f.reset !== '' && `reset: ${f.reset}`,
      range,
      f.description && `\n${f.description}`,
    ].filter(Boolean).join(' · ');
    return (
      <div key={`bm-${f.name || idx}-${seg.lo}-${seg.hi}`}
        title={tooltip}
        style={{
          flex: `${seg.span} ${seg.span} 0`, minWidth: 0,
          background: `color-mix(in oklch, ${color} 18%, transparent)`,
          border: `1px solid color-mix(in oklch, ${color} 60%, var(--line))`,
          color: 'var(--fg)', fontFamily: 'var(--mono)', fontSize: 10,
          textAlign: 'center', padding: '6px 4px', overflow: 'hidden',
          textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
        <div style={{ fontWeight: 800, color }}>{f.name || '?'}</div>
        <div style={{ color: 'var(--fg-mute)', fontSize: 8 }}>{range}</div>
      </div>
    );
  });
  // Bit-number scale (MSB on left).
  const scaleTicks: ReactNode[] = [];
  const tickStep = w >= 32 ? 4 : (w >= 16 ? 2 : 1);
  for (let bit = w - 1; bit >= 0; bit -= tickStep) {
    scaleTicks.push(
      <div key={`tk-${bit}`}
        style={{ flex: '1 1 0', minWidth: 0, textAlign: 'center',
          fontFamily: 'var(--mono)', fontSize: 8, color: 'var(--fg-mute)' }}>
        {bit}
      </div>
    );
  }
  return (
    <div style={{ marginTop: 6, marginBottom: 6 }}>
      <div style={{ display: 'flex', gap: 2 }}>{labelsLR}</div>
      <div style={{ display: 'flex', gap: 2, marginTop: 2 }}>{scaleTicks}</div>
    </div>
  );
};

export const RegisterBitFieldView = ({ width, fields, tokenMap, onJump }: any) => {
  const rows = (fields || []).filter(_hasMeaningfulRegisterField);
  if (!rows.length) return null;
  const hasParsedBits = rows.some((f: any) => _parseBitRange(f.bits));
  return (
    <div data-testid="register-bit-field-view" style={{ marginTop: 8, display: 'grid', gap: 7 }}>
      {hasParsedBits ? <RegisterBitMap width={width || 32} fields={rows} /> : null}
      <div style={{ display: 'grid', gap: 4 }}>
        {rows.map((f: any, fi: number) => {
          const color = _accessColor(f.access);
          return (
            <div key={`bf-${f.name || ''}-${f.bits || ''}-${fi}`} style={{
              display: 'grid',
              gridTemplateColumns: '82px minmax(0, 1fr) auto',
              gap: 8,
              alignItems: 'center',
              padding: '5px 6px',
              border: '1px solid var(--line)',
              borderRadius: 4,
              background: fi % 2 ? 'var(--bg-1)' : 'transparent',
              minWidth: 0,
            }}>
              <div style={{
                fontFamily: 'var(--mono)',
                fontSize: 10,
                color: 'var(--cyan)',
                fontWeight: 900,
                border: '1px solid var(--line-2)',
                borderRadius: 3,
                background: 'var(--bg-2)',
                padding: '3px 5px',
                textAlign: 'center',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}>
                {f.bits || '-'}
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{
                  fontFamily: 'var(--mono)',
                  fontSize: 11,
                  fontWeight: 900,
                  color: 'var(--fg)',
                  overflowWrap: 'anywhere',
                }}>
                  {f.name || 'field'}
                </div>
                {_hasRegisterDetail(f.description) ? (
                  <div className="mute" style={{
                    marginTop: 2,
                    fontSize: 11,
                    lineHeight: 1.35,
                    overflowWrap: 'anywhere',
                  }}>
                    {linkifyReferences(f.description, tokenMap, onJump)}
                  </div>
                ) : null}
              </div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', justifyContent: 'flex-end', minWidth: 0, maxWidth: 180 }}>
                {_hasRegisterDetail(f.access) ? (
                  <span style={{
                    fontFamily: 'var(--mono)',
                    fontSize: 9,
                    color,
                    border: `1px solid color-mix(in oklch, ${color} 60%, var(--line))`,
                    background: `color-mix(in oklch, ${color} 12%, transparent)`,
                    borderRadius: 3,
                    padding: '2px 5px',
                    whiteSpace: 'nowrap',
                    maxWidth: 110,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}>{f.access}</span>
                ) : null}
                {_hasRegisterDetail(f.reset) ? (
                  <span className="mute" style={{
                    fontFamily: 'var(--mono)',
                    fontSize: 9,
                    border: '1px solid var(--line)',
                    borderRadius: 3,
                    padding: '2px 5px',
                    whiteSpace: 'nowrap',
                    maxWidth: 110,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}>{f.reset}</span>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const SsotScenarioPlayer = ({ scenarios, fsmMachines = [], tokenMap, onJump, onSelectFsmState }: any) => {
  const [active, setActive] = useState(0);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const scenario = scenarios[active] || { steps: [] };
  const total = scenario.steps.length;
  // Map fl_state → first step index that hits it (so a state-pill click can
  // jump the scenario back to where that state first appears).
  const stateFirstStep = useMemo(() => {
    const map = new Map();
    scenario.steps.forEach((s: any, i: number) => {
      const key = String(s.fl_state || '').trim();
      if (key && !map.has(key)) map.set(key, i);
    });
    return map;
  }, [scenario]);
  useEffect(() => { setStep(0); setPlaying(false); }, [active]);
  useEffect(() => {
    if (!playing) return;
    if (step >= total - 1) { setPlaying(false); return; }
    const id = setTimeout(() => setStep(s => Math.min(s + 1, total - 1)), 850);
    return () => clearTimeout(id);
  }, [playing, step, total]);
  const cur = scenario.steps[step] || {};
  const sigEntries = Object.entries(cur.signals || {});
  // Pre-collect a stable list of all signals across the scenario for the timeline grid.
  const allSignals = useMemo(() => {
    const seen = new Set();
    const order: any[] = [];
    for (const s of scenario.steps) {
      for (const k of Object.keys(s.signals || {})) {
        if (!seen.has(k)) { seen.add(k); order.push(k); }
      }
    }
    return order;
  }, [scenario]);
  useEffect(() => {
    if (typeof onSelectFsmState === 'function' && cur.fl_state) onSelectFsmState(cur.fl_state);
  }, [cur.fl_state, onSelectFsmState]);
  const btnStyle = (active: any): any => ({
    border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
    background: active ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'var(--bg-2)',
    color: active ? 'var(--accent)' : 'var(--fg)',
    padding: '4px 10px', borderRadius: 4, fontFamily: 'var(--mono)',
    fontSize: 'var(--ui-control-font-size)', cursor: 'pointer',
  });
  return (
    <div style={{ display: 'grid', gap: 14 }}>
      {/* Scenario selector */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {scenarios.map((s: any, i: number) => (
          <span key={`scn-${s.name || i}-${i}`}
            onClick={() => setActive(i)}
            title={s.summary}
            style={{
              ...btnStyle(i === active),
              fontWeight: i === active ? 800 : 500,
            }}>
            {s.name || `scenario ${i + 1}`}{s.synthesized ? ' ◌' : ''}
          </span>
        ))}
      </div>
      {scenario.summary ? (
        <div className="mute" style={{ lineHeight: 1.55 }}>{scenario.summary}</div>
      ) : null}

      {/* Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <span onClick={() => { setStep(0); setPlaying(false); }} style={btnStyle(false)} title="Reset">↺ Reset</span>
        <span onClick={() => setStep(s => Math.max(0, s - 1))} style={btnStyle(false)} title="Back">⏮ Back</span>
        <span onClick={() => setPlaying(p => !p)} style={btnStyle(playing)} title={playing ? 'Pause' : 'Play'}>
          {playing ? '⏸ Pause' : '▶ Play'}
        </span>
        <span onClick={() => setStep(s => Math.min(total - 1, s + 1))} style={btnStyle(false)} title="Step">⏭ Step</span>
        <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>
          cycle {step + 1} / {total}
        </span>
        <input type="range" min={0} max={Math.max(0, total - 1)} value={step}
          onChange={e => { setStep(Number(e.target.value)); setPlaying(false); }}
          style={{ flex: 1, minWidth: 160 }} />
      </div>

      {/* Current step */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'minmax(0, 1.4fr) minmax(160px, 0.9fr)',
        gap: 12, alignItems: 'stretch',
      }}>
        <div style={{ border: '1px solid var(--accent)', borderRadius: 4, padding: '10px 12px', background: 'var(--bg-2)' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
            <span style={{ fontFamily: 'var(--mono)', color: 'var(--cyan)', fontWeight: 800 }}>
              cycle {cur.cycle != null ? cur.cycle : step}
            </span>
            {cur.fl_state ? (
              <span style={{
                fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 8px', borderRadius: 999,
                background: 'color-mix(in oklch, var(--magenta) 14%, transparent)',
                color: 'var(--magenta)', border: '1px solid color-mix(in oklch, var(--magenta) 32%, transparent)',
              }}>FL · {cur.fl_state}</span>
            ) : null}
            {cur.cl_state ? (
              <span style={{
                fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 8px', borderRadius: 999,
                background: 'color-mix(in oklch, var(--accent) 14%, transparent)',
                color: 'var(--accent)', border: '1px solid color-mix(in oklch, var(--accent) 32%, transparent)',
              }}>CL · {cur.cl_state}</span>
            ) : null}
          </div>
          <div style={{ color: 'var(--fg)', lineHeight: 1.55 }}>
            {tokenMap ? linkifyReferences(cur.action || '—', tokenMap, onJump) : (cur.action || '—')}
          </div>
          {cur.notes ? (
            <div className="mute" style={{ marginTop: 5, fontSize: 11 }}>
              {tokenMap ? linkifyReferences(cur.notes, tokenMap, onJump) : cur.notes}
            </div>
          ) : null}
        </div>
        {sigEntries.length ? (
          <div style={{ border: '1px solid var(--line)', borderRadius: 4, padding: '10px 12px', background: 'var(--bg-1)' }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 4 }}>SIGNALS @ cycle {cur.cycle != null ? cur.cycle : step}</div>
            {sigEntries.map(([k, v]: any, i: number) => (
              <div key={`sig-${k}-${i}`} style={{ display: 'flex', gap: 8, fontFamily: 'var(--mono)', fontSize: 11, lineHeight: 1.6 }}>
                <span style={{ color: 'var(--cyan)' }}>{k}</span>
                <span style={{ color: 'var(--fg-mute)' }}>=</span>
                <span style={{ color: 'var(--fg)' }}>{String(v)}</span>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      {/* FSM state map — pills per machine, active state highlighted */}
      {fsmMachines.length ? (
        <div style={{ display: 'grid', gap: 10 }}>
          {fsmMachines.map((m: any, mi: number) => {
            const activeName = String(cur.fl_state || '').trim();
            const activeMatch = (m.states || []).find((s: any) => String(s).trim() === activeName);
            return (
              <div key={`fsm-pane-${m.name || mi}`}
                style={{ border: '1px solid var(--line)', borderRadius: 4, padding: '8px 10px' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)' }}>FSM</span>
                  <span style={{ color: 'var(--accent)', fontWeight: 800 }}>{m.name || `fsm_${mi}`}</span>
                  <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
                    {(m.states || []).length} states · {(m.transitions || []).length} transitions
                  </span>
                  {activeName && !activeMatch ? (
                    <span style={{
                      fontFamily: 'var(--mono)', fontSize: 10, padding: '1px 7px', borderRadius: 999,
                      background: 'color-mix(in oklch, var(--warn) 14%, transparent)',
                      color: 'var(--warn)',
                      border: '1px solid color-mix(in oklch, var(--warn) 32%, transparent)',
                    }}>fl_state "{activeName}" not in this machine</span>
                  ) : null}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {(m.states || []).map((s: any, si: number) => {
                    const label = String(s).trim();
                    const isActive = label === activeName;
                    const isReset = String(m.resetState || '').trim() === label;
                    const jumpIdx = stateFirstStep.get(label);
                    return (
                      <span key={`st-${m.name || mi}-${label || si}-${si}`}
                        title={isReset ? `${label} (reset state)` : label}
                        onClick={() => {
                          if (jumpIdx != null) {
                            setStep(jumpIdx); setPlaying(false);
                          }
                        }}
                        style={{
                          fontFamily: 'var(--mono)', fontSize: 11, padding: '4px 10px',
                          borderRadius: 999,
                          background: isActive
                            ? 'color-mix(in oklch, var(--magenta) 28%, transparent)'
                            : (jumpIdx != null ? 'var(--bg-2)' : 'var(--bg-1)'),
                          color: isActive ? 'var(--magenta)' : (jumpIdx != null ? 'var(--fg)' : 'var(--fg-mute)'),
                          border: `1px solid ${isActive ? 'var(--magenta)' : (isReset ? 'var(--accent)' : 'var(--line)')}`,
                          fontWeight: isActive ? 800 : 500,
                          cursor: jumpIdx != null ? 'pointer' : 'default',
                          letterSpacing: '0.02em',
                        }}>
                        {label}{isReset ? ' ◉' : ''}{isActive ? ' ●' : ''}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

      {/* Timeline */}
      {allSignals.length ? (
        <div style={{ border: '1px solid var(--line)', borderRadius: 4, padding: '10px 12px', overflowX: 'auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 6 }}>
            SIGNAL TIMELINE (click a column to jump)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: `120px repeat(${total}, minmax(48px, 1fr))`, gap: 2 }}>
            <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>cycle</div>
            {scenario.steps.map((s: any, i: number) => (
              <div key={`hd-${i}`}
                onClick={() => { setStep(i); setPlaying(false); }}
                style={{
                  color: i === step ? 'var(--accent)' : 'var(--fg-mute)',
                  fontFamily: 'var(--mono)', fontSize: 10, textAlign: 'center', cursor: 'pointer',
                  fontWeight: i === step ? 800 : 400,
                }}>
                {s.cycle != null ? s.cycle : i}
              </div>
            ))}
            {allSignals.map((sig: any) => (
              <Fragment key={`row-${sig}`}>
                <div style={{ color: 'var(--cyan)', fontFamily: 'var(--mono)', fontSize: 11 }}>{sig}</div>
                {scenario.steps.map((s: any, i: number) => {
                  const val = s.signals && s.signals[sig];
                  return (
                    <div key={`cell-${sig}-${i}`}
                      onClick={() => { setStep(i); setPlaying(false); }}
                      style={{
                        background: i === step
                          ? 'color-mix(in oklch, var(--accent) 22%, transparent)'
                          : (val != null ? 'var(--bg-2)' : 'transparent'),
                        border: '1px solid var(--line)',
                        color: 'var(--fg)', textAlign: 'center',
                        fontFamily: 'var(--mono)', fontSize: 10,
                        padding: '2px 4px', cursor: 'pointer',
                      }}>
                      {val != null ? String(val) : ''}
                    </div>
                  );
                })}
              </Fragment>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
};
