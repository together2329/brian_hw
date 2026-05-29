/* workspace-ssot-fsm.tsx — strangler-fig migration slice of workspace.jsx.
 *
 * Owns the Digest/FSM visualization layer:
 *   - YamlSectionCard (collapsible per-section YAML card).
 *   - Digest primitives: DigestKV, DigestList, DigestEmpty, compactDigestItems.
 *   - Gates: GatesPanel (+GateRow / GATE_STATUS_GLYPH), fetched from
 *     /api/ssot-gates/<ip>.
 *   - FSM diagram stack: graph builders (fsmGraphFromMachine / uniqueFsmStates),
 *     mermaid bridge (ensureAtlasMermaid via window.mermaid +
 *     window.__ATLAS_MERMAID_INITIALIZED), FsmLayeredSvgDiagram, MermaidFsmGraph,
 *     FsmTransitionTable and the FsmTransitionDiagram composite.
 *
 * INERT mirror: legacy workspace.jsx still serves the live app. Public exports
 * are consumed by sibling workspace-*.tsx modules and the root composer.
 *
 * Window-sourced dependencies:
 *   - window.DigestCard      (GatesPanel card chrome; declared in atlas-window.d.ts)
 *   - window.mermaid         (ensureAtlasMermaid)
 *   - window.DOMPurify       (MermaidFsmGraph svg sanitize)
 *   - window.__ATLAS_MERMAID_INITIALIZED (mermaid init guard)
 *   - (window as any)._highlightYamlBlock — owned by workspace-lint-coverage.tsx,
 *     consumed here via window because it is outside this module's import
 *     allowlist (lint-coverage bridges it to window during the .jsx↔.tsx era).
 */
import { useState, useEffect, useCallback, Fragment, type ReactNode } from 'react';

const DigestCard: any = window.DigestCard;

// ---------------------------------------------------------------------------
// YAML section card
// ---------------------------------------------------------------------------

export const YamlSectionCard = ({ section, statusByKey }: any) => {
  const text = String(section?.text || '');
  const title = String(section?.title || section?.label || section?.key || section?.id || 'section');
  const status = (statusByKey && (statusByKey[section?.key] || statusByKey[section?.id])) || '';
  const lines = text.split('\n');
  // Skip the leading section header (`# === SECTION N ===`) and find the
  // actual top-level key (first non-comment, non-blank line) to compute
  // the summary string.
  let summary = '';
  let topKey = '';
  for (const ln of lines) {
    const trimmed = ln.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const m = trimmed.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (m) {
      topKey = m[1];
      const rhs = m[2];
      if (rhs && rhs !== '|' && rhs !== '>' && rhs !== 'null' && rhs !== '~') {
        summary = rhs.length > 80 ? rhs.slice(0, 80) + '…' : rhs;
      }
    }
    break;
  }
  // Item count: lines starting with '  -' under topKey, OR child key count.
  let countSuffix = '';
  if (!summary) {
    let items = 0, keys = 0;
    for (let i = 0; i < lines.length; i++) {
      const ln = lines[i];
      if (/^\s*-\s/.test(ln) && /^\s{2,}-/.test(ln)) items += 1;
      else if (/^\s{2,}[A-Za-z_][\w-]*:/.test(ln) && !/^\s{4,}/.test(ln)) keys += 1;
    }
    if (items) countSuffix = `${items} item${items === 1 ? '' : 's'}`;
    else if (keys) countSuffix = `${keys} key${keys === 1 ? '' : 's'}`;
    else countSuffix = `${lines.length} line${lines.length === 1 ? '' : 's'}`;
  }
  // Default open for short sections, closed for long ones (>40 lines).
  const [open, setOpen] = useState(lines.length <= 40);
  const statusColor = status === 'approved'
    ? 'var(--ok)'
    : (status === 'flag' || status === 'warn' ? 'var(--warn)' : 'var(--accent)');
  return (
    <div
      style={{
        border: '1px solid var(--line)',
        borderLeft: `3px solid ${statusColor}`,
        borderRadius: 4,
        background: 'color-mix(in oklch, var(--bg-1) 86%, transparent)',
        overflow: 'hidden',
      }}
    >
      <div
        role="button"
        tabIndex={0}
        onClick={() => setOpen(o => !o)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); }
        }}
        title={open ? 'click to collapse' : 'click to expand'}
        style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '7px 12px',
          cursor: 'pointer', userSelect: 'none',
          fontFamily: 'var(--mono)', fontSize: 12,
          background: open ? 'color-mix(in oklch, var(--bg-3) 60%, transparent)' : 'transparent',
        }}
      >
        <span style={{ color: 'var(--cyan)', fontWeight: 700 }}>{title}</span>
        {topKey && topKey !== title && (
          <span className="mute" style={{ fontSize: 10 }}>{topKey}</span>
        )}
        <span style={{ flex: 1 }} />
        {summary ? (
          <span className="mute trunc" style={{
            fontSize: 'var(--ui-control-font-size)', color: 'var(--fg)', opacity: 0.78, maxWidth: '50%',
          }}>
            {summary}
          </span>
        ) : (
          <span className="mute" style={{ fontSize: 10 }}>{countSuffix}</span>
        )}
        <span style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)' }}>
          {open ? '▾' : '▸'}
        </span>
      </div>
      {open ? (
        <pre
          className="tool-output-pre tool-output-yaml language-yaml"
          style={{
            margin: 0, border: 'none', borderTop: '1px solid var(--line)',
            borderRadius: 0,
            maxHeight: 480, overflow: 'auto',
            background: 'var(--code-bg)',
            padding: '10px 12px',
            whiteSpace: 'pre',
          }}
        >
          <code
            className="language-yaml"
            dangerouslySetInnerHTML={{ __html: (window as any)._highlightYamlBlock(text) }}
          />
        </pre>
      ) : null}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Digest primitives
// ---------------------------------------------------------------------------

export const DigestKV = ({ rows }: any) => (
  <div style={{ display: 'grid', gridTemplateColumns: '112px minmax(0, 1fr)', gap: '5px 10px', fontSize: 12 }}>
    {(rows || []).filter((r: any) => r && r[1] !== '' && r[1] != null).map(([k, v]: any) => (
      <Fragment key={k}>
        <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>{k}</span>
        <span style={{ minWidth: 0, wordBreak: 'break-word' }}>{String(v)}</span>
      </Fragment>
    ))}
  </div>
);

export const DigestList = ({ items, limit = 8 }: any) => {
  const rows = (items || []).filter(Boolean).slice(0, limit);
  if (!rows.length) return <DigestEmpty />;
  return (
    <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.45 }}>
      {rows.map((item: any, idx: number) => <li key={`${item}-${idx}`}>{item}</li>)}
    </ul>
  );
};

export const GATE_STATUS_GLYPH: Record<string, { glyph: string; color: string }> = {
  pass: { glyph: '✓', color: 'var(--ok, #4caf50)' },
  fail: { glyph: '✗', color: 'var(--err, #e53935)' },
  blocked: { glyph: '⚠', color: 'var(--warn, #f9a825)' },
  unverified: { glyph: '○', color: 'var(--mute, #999)' },
  skip: { glyph: '–', color: 'var(--fg-mute, #888)' },
};

export const GateRow = ({ item, isStage = false }: any) => {
  const sk = String(item.status || 'skip').toLowerCase();
  const g = GATE_STATUS_GLYPH[sk] || GATE_STATUS_GLYPH.skip;
  const label = isStage ? item.stage : item.label;
  const tools = isStage ? (item.scripts || []) : (item.helper ? [item.helper] : []);
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '24px minmax(140px, 1.2fr) minmax(0, 2fr) 1fr',
      gap: 10, alignItems: 'baseline',
      padding: '4px 0', borderBottom: '1px dashed var(--line)',
      fontSize: 12, fontFamily: 'var(--mono)',
    }}>
      <span style={{ color: g.color, fontWeight: 800, textAlign: 'center' }}>{g.glyph}</span>
      <span style={{ color: 'var(--fg)' }}>{label}</span>
      <span style={{ color: 'var(--fg-mute)' }}>{item.summary || ''}</span>
      <span className="mute" style={{ fontSize: 10, wordBreak: 'break-all' }}>
        {(item.evidence || []).slice(0, 2).join(' · ')}
        {tools.length ? <>{(item.evidence || []).length ? <br /> : null}<span style={{ opacity: 0.6 }}>{tools[0]}</span></> : null}
      </span>
    </div>
  );
};

export const GatesPanel = ({ ip }: any) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fetchGates = useCallback(() => {
    if (!ip) return;
    setLoading(true);
    fetch(`/api/ssot-gates/${encodeURIComponent(ip)}`)
      .then(r => r.json())
      .then(j => { setData(j); setError(j.error || ''); })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [ip]);
  useEffect(() => { fetchGates(); }, [fetchGates]);
  if (!ip) return <DigestEmpty text="No IP selected" />;
  if (error) return <div style={{ padding: 12, color: 'var(--err)' }}>{error}</div>;
  if (!data && loading) return <div style={{ padding: 12, color: 'var(--fg-mute)' }}>loading gates…</div>;
  if (!data) return <DigestEmpty text="No gates data" />;
  const q = data.ssot_quality || { items: [], passed: 0, total: 0 };
  const s = data.stages || { items: [], passed: 0, total: 0 };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
        <span style={{ color: 'var(--accent)', fontWeight: 800, fontSize: 12 }}>
          Gates · {ip}
        </span>
        <span className="mute" style={{ fontSize: 10, fontFamily: 'var(--mono)' }}>
          SSOT {q.passed}/{q.total} ✓ · Stages {s.passed}/{s.total} ✓
        </span>
        <span className="mute" style={{ fontSize: 10, marginLeft: 'auto', fontFamily: 'var(--mono)' }}>
          {data.generated_at}
        </span>
        <button onClick={fetchGates} disabled={loading} style={{
          background: 'transparent', border: '1px solid var(--line)',
          color: 'var(--fg)', padding: '2px 10px', cursor: 'pointer',
          fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)',
        }}>{loading ? '…' : 'refresh'}</button>
      </div>
      <DigestCard title={`SSOT Quality (${q.items.length} dims)`} meta={`${q.passed}/${q.total} pass`}>
        <div style={{ display: 'grid', gridTemplateColumns: '24px minmax(140px, 1.2fr) minmax(0, 2fr) 1fr',
          gap: 10, padding: '4px 0', borderBottom: '1px solid var(--line)',
          fontSize: 10, color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>
          <span></span><span>dimension</span><span>summary</span><span>evidence · checker</span>
        </div>
        {q.items.map((item: any) => <GateRow key={item.id} item={item} />)}
      </DigestCard>
      <DigestCard title={`Per-stage Checkers (${s.items.length} stages)`} meta={`${s.passed}/${s.total} pass`}>
        <div style={{ display: 'grid', gridTemplateColumns: '24px minmax(140px, 1.2fr) minmax(0, 2fr) 1fr',
          gap: 10, padding: '4px 0', borderBottom: '1px solid var(--line)',
          fontSize: 10, color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>
          <span></span><span>stage</span><span>summary</span><span>evidence · scripts</span>
        </div>
        {s.items.map((item: any) => <GateRow key={item.stage} item={item} isStage={true} />)}
      </DigestCard>
    </div>
  );
};

export const compactDigestItems = (items: any, limit = 6): string => {
  const rows = (items || []).filter(Boolean);
  if (!rows.length) return '';
  const shown = rows.slice(0, limit).join(', ');
  const extra = rows.length > limit ? ` +${rows.length - limit} more` : '';
  return shown + extra;
};

export const DigestEmpty = ({ text = 'No structured data in this section yet.' }: any) => (
  <div className="mute" style={{ fontSize: 12, fontFamily: 'var(--mono)' }}>{text}</div>
);

// ---------------------------------------------------------------------------
// FSM graph builders
// ---------------------------------------------------------------------------

export const fsmDiagramId = (name: any, index = 0): string => (
  `fsm-transition-${index}-${String(name || 'machine').toLowerCase().replace(/[^a-z0-9_-]+/g, '-')}`
);

export const truncateSvgText = (value: any, limit = 24): string => {
  const text = String(value || '').trim();
  return text.length > limit ? `${text.slice(0, Math.max(1, limit - 1))}...` : text;
};

export const fsmStateKey = (value: any): string => String(value || '').trim();

export const fsmSafeId = (value: any, index = 0): string => {
  const base = String(value || 'state')
    .trim()
    .replace(/[^a-zA-Z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 40) || 'state';
  return `S${index}_${/^[A-Za-z_]/.test(base) ? base : `_${base}`}`;
};

export const fsmTransitionLabel = (tr: any, limit = 120): string => {
  const condition = String((tr && tr.condition) || '').trim();
  const action = String((tr && tr.action) || '').trim();
  const raw = String((tr && tr.raw) || '').trim();
  const label = [condition, action].filter(Boolean).join(' / ') || raw;
  return limit ? truncateSvgText(label, limit) : label;
};

export const escapeMermaidLabel = (value: any): string => (
  String(value || '')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/[\r\n]+/g, ' ')
    .trim()
);

export const uniqueFsmStates = (machine: any): string[] => {
  const out: string[] = [];
  const add = (value: any) => {
    const state = String(value || '').trim();
    if (!state || state === '-') return;
    if (!out.includes(state)) out.push(state);
  };
  (machine.states || []).forEach(add);
  (machine.transitions || []).forEach((tr: any) => {
    add(tr.from);
    add(tr.to);
  });
  return out;
};

export const fsmGraphFromMachine = (machine: any): any => {
  const stateMap = new Map<string, any>();
  const states: any[] = [];
  const addState = (value: any) => {
    const key = fsmStateKey(value);
    if (!key || key === '-') return null;
    if (stateMap.has(key)) return stateMap.get(key);
    const node = {
      id: fsmSafeId(key, states.length),
      label: key,
      reset: false,
    };
    stateMap.set(key, node);
    states.push(node);
    return node;
  };

  (machine.states || []).forEach(addState);
  (machine.transitions || []).forEach((tr: any) => {
    addState(tr.from);
    addState(tr.to);
  });
  const reset = addState(machine.resetState);
  if (reset) reset.reset = true;

  const transitions = (machine.transitions || []).map((tr: any, idx: number) => {
    const from = addState(tr.from);
    const to = addState(tr.to);
    const label = fsmTransitionLabel(tr, 96);
    const fullLabel = fsmTransitionLabel(tr, 0);
    return {
      id: `T${idx + 1}`,
      index: idx + 1,
      from,
      to,
      fromLabel: fsmStateKey(tr.from),
      toLabel: fsmStateKey(tr.to),
      condition: String((tr && tr.condition) || '').trim(),
      action: String((tr && tr.action) || '').trim(),
      raw: String((tr && tr.raw) || '').trim(),
      label,
      fullLabel,
      drawable: !!(from && to),
    };
  });

  return {
    name: machine.name || 'FSM',
    sourceKey: machine.sourceKey || '',
    reset,
    states,
    transitions,
    drawableTransitions: transitions.filter((t: any) => t.drawable),
  };
};

export const fsmGraphToMermaid = (graph: any): string => {
  const lines = ['stateDiagram-v2', '  direction LR'];
  (graph.states || []).forEach((state: any) => {
    lines.push(`  state "${escapeMermaidLabel(state.label)}" as ${state.id}`);
  });
  if (graph.reset) lines.push(`  [*] --> ${graph.reset.id}`);
  (graph.drawableTransitions || []).forEach((tr: any) => {
    const label = tr.label ? `: ${escapeMermaidLabel(tr.label)}` : '';
    lines.push(`  ${tr.from.id} --> ${tr.to.id}${label}`);
  });
  if (!(graph.drawableTransitions || []).length && graph.states.length) {
    lines.push(`  [*] --> ${graph.states[0].id}`);
  }
  return lines.join('\n');
};

export const ensureAtlasMermaid = (): any => {
  const mermaid = window.mermaid;
  if (!mermaid || !mermaid.render) return null;
  if (!(window as any).__ATLAS_MERMAID_INITIALIZED) {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'strict',
      htmlLabels: false,
      theme: 'base',
      themeVariables: {
        background: 'transparent',
        primaryColor: '#101827',
        primaryBorderColor: '#38bdf8',
        primaryTextColor: '#f7fbff',
        lineColor: '#38bdf8',
        secondaryColor: '#152235',
        tertiaryColor: '#0b111c',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
      },
    });
    (window as any).__ATLAS_MERMAID_INITIALIZED = true;
  }
  return mermaid;
};

// ---------------------------------------------------------------------------
// FSM diagram components
// ---------------------------------------------------------------------------

export const FsmModeButton = ({ active, children, onClick }: { active?: boolean; children?: ReactNode; onClick?: () => void }) => (
  <button
    type="button"
    onClick={onClick}
    style={{
      border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
      borderRadius: 3,
      background: active ? 'color-mix(in oklch, var(--accent) 16%, var(--bg-2))' : 'var(--bg-2)',
      color: active ? 'var(--accent)' : 'var(--fg)',
      fontFamily: 'var(--mono)',
      fontSize: 10,
      padding: '4px 8px',
      cursor: 'pointer',
    }}
  >
    {children}
  </button>
);

export const FsmLayeredSvgDiagram = ({ graph, diagramId }: any) => {
  const states = graph.states || [];
  const transitions = graph.drawableTransitions || [];
  if (!states.length || !transitions.length) {
    return <DigestEmpty text="No drawable FSM transitions yet. Add transition entries with from/to fields." />;
  }

  const adjacency = new Map<string, string[]>();
  transitions.forEach((tr: any) => {
    const list = adjacency.get(tr.from.id) || [];
    list.push(tr.to.id);
    adjacency.set(tr.from.id, list);
  });

  const levelById = new Map<string, number>();
  const start = (graph.reset || states[0]).id;
  const queue = [start];
  levelById.set(start, 0);
  while (queue.length) {
    const id = queue.shift() as string;
    const level = levelById.get(id) || 0;
    (adjacency.get(id) || []).forEach((next) => {
      if (!levelById.has(next)) {
        levelById.set(next, level + 1);
        queue.push(next);
      }
    });
  }
  let maxLevel = Math.max(0, ...Array.from(levelById.values()));
  states.forEach((state: any) => {
    if (!levelById.has(state.id)) {
      maxLevel += 1;
      levelById.set(state.id, maxLevel);
    }
  });

  const levels: any[][] = [];
  states.forEach((state: any) => {
    const level = levelById.get(state.id) || 0;
    if (!levels[level]) levels[level] = [];
    levels[level].push(state);
  });

  const nodeW = 152;
  const nodeH = 42;
  const pad = 42;
  const colGap = 92;
  const rowGap = 38;
  const maxRows = Math.max(1, ...levels.map(group => (group || []).length));
  const width = Math.max(460, pad * 2 + levels.length * nodeW + Math.max(0, levels.length - 1) * colGap);
  const height = Math.max(180, pad * 2 + maxRows * nodeH + Math.max(0, maxRows - 1) * rowGap);
  const pos: Record<string, { x: number; y: number }> = {};
  levels.forEach((group, level) => {
    const groupH = group.length * nodeH + Math.max(0, group.length - 1) * rowGap;
    const y0 = (height - groupH) / 2;
    group.forEach((state: any, row: number) => {
      pos[state.id] = {
        x: pad + level * (nodeW + colGap) + nodeW / 2,
        y: y0 + row * (nodeH + rowGap) + nodeH / 2,
      };
    });
  });

  const pairCounts: Record<string, number> = {};
  const markerId = `${diagramId}-fallback-arrow`;

  return (
    <div style={{ overflowX: 'auto' }}>
      <svg
        role="img"
        aria-label={`${graph.name} fallback FSM graph`}
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', minWidth: Math.min(width, 920), height: 'auto', display: 'block' }}
      >
        <defs>
          <marker id={markerId} markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L9,4 L0,8 Z" fill="var(--cyan)" />
          </marker>
        </defs>
        {graph.reset && pos[graph.reset.id] ? (
          <g>
            <line
              x1={Math.max(8, pos[graph.reset.id].x - nodeW / 2 - 34)}
              y1={pos[graph.reset.id].y}
              x2={pos[graph.reset.id].x - nodeW / 2 - 5}
              y2={pos[graph.reset.id].y}
              stroke="var(--accent)"
              strokeWidth="1.8"
              markerEnd={`url(#${markerId})`}
            />
            <text
              x={Math.max(10, pos[graph.reset.id].x - nodeW / 2 - 34)}
              y={pos[graph.reset.id].y - 8}
              fill="var(--accent)"
              fontFamily="var(--mono)"
              fontSize="10"
            >
              reset
            </text>
          </g>
        ) : null}
        {transitions.map((tr: any) => {
          const from = pos[tr.from.id];
          const to = pos[tr.to.id];
          if (!from || !to) return null;
          const pairKey = `${tr.from.id}->${tr.to.id}`;
          const pairIdx = pairCounts[pairKey] || 0;
          pairCounts[pairKey] = pairIdx + 1;
          const lane = (pairIdx % 4) * 10;
          const startX = from.x + nodeW / 2;
          const startY = from.y + Math.min(nodeH / 2 - 8, lane);
          const endX = to.x - nodeW / 2;
          const endY = to.y + Math.min(nodeH / 2 - 8, lane);
          let path = '';
          let labelX = (startX + endX) / 2;
          let labelY = (startY + endY) / 2;
          if (tr.from.id === tr.to.id) {
            const x = from.x + nodeW / 2 - 4;
            const y = from.y - nodeH / 2 + 4;
            path = `M ${x} ${y} C ${x + 46} ${y - 34}, ${x + 46} ${y + 34}, ${x} ${y + nodeH - 8}`;
            labelX = x + 34;
            labelY = y - 6;
          } else if ((levelById.get(tr.to.id) || 0) >= (levelById.get(tr.from.id) || 0)) {
            const bend = Math.max(60, Math.abs(endX - startX) * 0.45);
            path = `M ${startX} ${startY} C ${startX + bend} ${startY}, ${endX - bend} ${endY}, ${endX} ${endY}`;
          } else {
            const laneY = Math.min(height - 18, Math.max(startY, endY) + 34 + lane);
            path = `M ${from.x} ${from.y + nodeH / 2} L ${from.x} ${laneY} L ${to.x} ${laneY} L ${to.x} ${to.y + nodeH / 2}`;
            labelX = (from.x + to.x) / 2;
            labelY = laneY - 6;
          }
          return (
            <g key={`${graph.name}:fallback-edge:${tr.id}`}>
              <path
                d={path}
                fill="none"
                stroke="var(--cyan)"
                strokeWidth="1.35"
                markerEnd={`url(#${markerId})`}
              />
              <g>
                <rect
                  x={labelX - 10}
                  y={labelY - 13}
                  width="20"
                  height="16"
                  rx="3"
                  fill="var(--bg-2)"
                  stroke="var(--line-2)"
                />
                <text
                  x={labelX}
                  y={labelY - 1}
                  textAnchor="middle"
                  fill="var(--fg)"
                  fontFamily="var(--mono)"
                  fontSize="9"
                >
                  <title>{tr.fullLabel || tr.label || tr.id}</title>
                  {tr.index}
                </text>
              </g>
            </g>
          );
        })}
        {states.map((state: any) => {
          const p = pos[state.id];
          const isReset = !!state.reset;
          return (
            <g key={`${graph.name}:fallback-state:${state.id}`}>
              <rect
                x={p.x - nodeW / 2}
                y={p.y - nodeH / 2}
                width={nodeW}
                height={nodeH}
                rx="5"
                fill={isReset ? 'color-mix(in oklch, var(--accent) 16%, var(--bg-2))' : 'var(--bg-2)'}
                stroke={isReset ? 'var(--accent)' : 'var(--line-2)'}
                strokeWidth={isReset ? '1.7' : '1.2'}
              />
              <text
                x={p.x}
                y={p.y + 4}
                textAnchor="middle"
                fill={isReset ? 'var(--accent)' : 'var(--fg)'}
                fontFamily="var(--mono)"
                fontSize="11"
                fontWeight={isReset ? '700' : '500'}
              >
                <title>{state.label}</title>
                {truncateSvgText(state.label, 18)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export const MermaidFsmGraph = ({ graph, code, diagramId }: any) => {
  const [renderState, setRenderState] = useState<any>({ status: 'loading', svg: '', error: '' });

  useEffect(() => {
    let cancelled = false;
    const mermaid = ensureAtlasMermaid();
    if (!mermaid) {
      setRenderState({ status: 'fallback', svg: '', error: 'Mermaid library is unavailable.' });
      return () => { cancelled = true; };
    }

    const renderId = `${diagramId}-${Date.now()}-${Math.random().toString(36).slice(2)}`.replace(/[^a-zA-Z0-9_-]/g, '-');
    setRenderState({ status: 'loading', svg: '', error: '' });
    Promise.resolve(mermaid.render(renderId, code))
      .then((result: any) => {
        if (cancelled) return;
        const rawSvg = (result && result.svg) || '';
        const svg = (window.DOMPurify && window.DOMPurify.sanitize)
          ? window.DOMPurify.sanitize(rawSvg, { USE_PROFILES: { svg: true, svgFilters: true } })
          : rawSvg;
        setRenderState({ status: 'ready', svg, error: '' });
      })
      .catch((err: any) => {
        if (cancelled) return;
        setRenderState({
          status: 'fallback',
          svg: '',
          error: err && err.message ? err.message : 'Mermaid render failed.',
        });
      });

    return () => { cancelled = true; };
  }, [code, diagramId]);

  if (renderState.status === 'ready' && renderState.svg) {
    return (
      <div
        className="atlas-mermaid-fsm"
        style={{ overflowX: 'auto', padding: 10 }}
        dangerouslySetInnerHTML={{ __html: renderState.svg }}
      />
    );
  }

  return (
    <div>
      {renderState.status === 'fallback' ? (
        <div
          className="mute"
          style={{
            margin: '8px 10px 0',
            padding: '6px 8px',
            border: '1px solid var(--line)',
            borderRadius: 3,
            color: 'var(--warn)',
            fontFamily: 'var(--mono)',
            fontSize: 10,
          }}
        >
          Mermaid fallback: {renderState.error}
        </div>
      ) : null}
      <FsmLayeredSvgDiagram graph={graph} diagramId={diagramId} />
    </div>
  );
};

export const FsmTransitionTable = ({ graph }: any) => {
  const rows = graph.transitions || [];
  if (!rows.length) return <DigestEmpty text="No transitions listed for this FSM." />;
  return (
    <div style={{ display: 'grid', gap: 4 }}>
      <div
        className="mute"
        style={{
          display: 'grid',
          gridTemplateColumns: '36px minmax(90px, 0.65fr) 20px minmax(90px, 0.65fr) minmax(0, 1.5fr)',
          gap: 8,
          fontFamily: 'var(--mono)',
          fontSize: 10,
        }}
      >
        <span>#</span><span>from</span><span></span><span>to</span><span>condition/action</span>
      </div>
      {rows.map((tr: any, idx: number) => (
        <div
          key={`${graph.name}:tr:${idx}:${tr.raw}`}
          style={{
            display: 'grid',
            gridTemplateColumns: '36px minmax(90px, 0.65fr) 20px minmax(90px, 0.65fr) minmax(0, 1.5fr)',
            gap: 8,
            alignItems: 'baseline',
            fontFamily: 'var(--mono)',
            fontSize: 'var(--ui-control-font-size)',
            borderTop: idx ? '1px solid var(--line)' : 'none',
            paddingTop: idx ? 5 : 0,
          }}
        >
          <span className="mute">{tr.index}</span>
          <span style={{ color: tr.from ? 'var(--fg)' : 'var(--warn)' }}>{tr.fromLabel || '-'}</span>
          <span className="mute">-&gt;</span>
          <span style={{ color: tr.to ? 'var(--cyan)' : 'var(--warn)' }}>{tr.toLabel || '-'}</span>
          <span className="mute" style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
            {tr.fullLabel || '-'}
          </span>
        </div>
      ))}
    </div>
  );
};

export const FsmTransitionDiagram = ({ machine, index = 0 }: any) => {
  const graph = fsmGraphFromMachine(machine);
  const [mode, setMode] = useState('graph');
  const mermaidCode = fsmGraphToMermaid(graph);
  const diagramId = fsmDiagramId(machine.name, index);

  if (!graph.states.length || !graph.transitions.length) {
    return <DigestEmpty text="No drawable FSM transitions yet. Add transition entries with from/to fields." />;
  }

  return (
    <div style={{ marginTop: 10, border: '1px solid var(--line)', borderRadius: 4, background: 'var(--bg)', overflow: 'hidden' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 8,
          padding: '7px 9px',
          borderBottom: '1px solid var(--line)',
          background: 'var(--bg-2)',
        }}
      >
        <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
          {graph.states.length} states / {graph.drawableTransitions.length} drawable transitions
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <FsmModeButton active={mode === 'graph'} onClick={() => setMode('graph')}>Graph</FsmModeButton>
          <FsmModeButton active={mode === 'mermaid'} onClick={() => setMode('mermaid')}>Mermaid</FsmModeButton>
          <FsmModeButton active={mode === 'table'} onClick={() => setMode('table')}>Table</FsmModeButton>
        </div>
      </div>
      {mode === 'graph' ? (
        <FsmLayeredSvgDiagram graph={graph} diagramId={diagramId} />
      ) : null}
      {mode === 'mermaid' ? (
        <pre
          className="tool-output-pre language-mermaid"
          style={{
            margin: 0,
            border: 'none',
            borderRadius: 0,
            maxHeight: 360,
            overflow: 'auto',
            background: 'var(--code-bg)',
            padding: '10px 12px',
            whiteSpace: 'pre',
          }}
        >
          <code>{mermaidCode}</code>
        </pre>
      ) : null}
      {mode === 'table' ? (
        <div style={{ padding: 10 }}>
          <FsmTransitionTable graph={graph} />
        </div>
      ) : null}
    </div>
  );
};
