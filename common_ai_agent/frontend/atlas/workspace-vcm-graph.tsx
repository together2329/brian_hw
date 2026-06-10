// VCM tab — interactive graph of the verification-contract spine:
// Requirement → Obligation → Contract → Evidence → Validation.
// Data comes from <ip>/req/vcm_graph.json (emit_vcm_graph.py); this component
// renders columns per kind, free-text search, status/kind filter chips, hover
// neighbourhood highlight and a click detail panel. No graph library — same
// in-house SVG approach as workspace-todo-graph.tsx.
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

type VcmNode = {
  readonly id: string;
  readonly kind: string;
  readonly label: string;
  readonly status: string;
  readonly data: Record<string, unknown>;
};

type VcmEdge = {
  readonly source: string;
  readonly target: string;
  readonly kind: string;
};

type VcmGraphDoc = {
  readonly ip: string;
  readonly locked?: boolean;
  readonly generated_at?: string;
  readonly nodes: readonly VcmNode[];
  readonly edges: readonly VcmEdge[];
};

const COLUMNS: readonly { readonly key: string; readonly title: string; readonly kinds: readonly string[] }[] = [
  { key: 'req', title: 'REQUIREMENT', kinds: ['requirement'] },
  { key: 'obl', title: 'OBLIGATION', kinds: ['obligation'] },
  { key: 'con', title: 'CONTRACT', kinds: ['contract_ref', 'structural_contract', 'behavioral_contract'] },
  { key: 'evi', title: 'EVIDENCE', kinds: ['evidence'] },
  { key: 'val', title: 'VALIDATION', kinds: ['validation', 'ghost'] },
];

const STATUS_COLOR: Record<string, string> = {
  locked: 'var(--accent)',
  closed: 'var(--ok, #4caf78)',
  pass: 'var(--ok, #4caf78)',
  present: 'var(--ok, #4caf78)',
  open: 'var(--warn, #d9a13b)',
  planned: 'var(--warn, #d9a13b)',
  draft: 'var(--warn, #d9a13b)',
  fail: 'var(--err, #e05a5a)',
  missing: 'var(--err, #e05a5a)',
};

const statusColor = (status: string): string => STATUS_COLOR[status] ?? 'var(--fg-mute)';

const STATUS_FILTERS = ['locked', 'closed', 'open', 'planned', 'present', 'pass', 'fail', 'missing'] as const;

export const VcmGraphTab = ({ activeIp }: { readonly activeIp: string }): ReactNode => {
  const [doc, setDoc] = useState<VcmGraphDoc | null>(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [kindFilter, setKindFilter] = useState<string>('');
  const [openId, setOpenId] = useState<string | null>(null);
  const [hoverId, setHoverId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!activeIp) { setDoc(null); setError('no active IP'); return; }
    setError('');
    try {
      const r = await fetch('/api/file?path=' + encodeURIComponent(activeIp + '/req/vcm_graph.json'), { cache: 'no-store' });
      if (!r.ok) {
        setDoc(null);
        setError('no vcm_graph.json — run: python3 "$ATLAS_WORKFLOW_ROOT/req-gen/scripts/emit_vcm_graph.py" ' + activeIp);
        return;
      }
      const parsed = await r.json() as VcmGraphDoc;
      if (!Array.isArray(parsed?.nodes)) { setDoc(null); setError('vcm_graph.json: unexpected shape'); return; }
      setDoc(parsed);
    } catch (e) {
      setDoc(null);
      setError(String(e));
    }
  }, [activeIp]);

  useEffect(() => { void load(); }, [load]);

  const nodes = useMemo<readonly VcmNode[]>(() => doc?.nodes ?? [], [doc]);
  const edges = useMemo<readonly VcmEdge[]>(() => doc?.edges ?? [], [doc]);
  const nodeById = useMemo(() => new Map(nodes.map((n: VcmNode) => [n.id, n])), [nodes]);
  const neighbours = useMemo(() => {
    const m = new Map<string, Set<string>>();
    for (const e of edges) {
      if (!m.has(e.source)) m.set(e.source, new Set());
      if (!m.has(e.target)) m.set(e.target, new Set());
      m.get(e.source)!.add(e.target);
      m.get(e.target)!.add(e.source);
    }
    return m;
  }, [edges]);

  const q = query.trim().toLowerCase();
  const matches = useCallback((n: VcmNode): boolean => {
    if (statusFilter && n.status !== statusFilter) return false;
    if (kindFilter && !COLUMNS.find(c => c.key === kindFilter)?.kinds.includes(n.kind)) return false;
    if (!q) return true;
    const hay = (n.id + ' ' + n.label + ' ' + JSON.stringify(n.data)).toLowerCase();
    return hay.includes(q);
  }, [q, statusFilter, kindFilter]);

  // ── layout: columns by kind, vertical stacking ──
  const NODE_W = 168;
  const NODE_H = 34;
  const GAP_Y = 10;
  const GAP_X = 70;
  const PAD = 16;
  const pos = useMemo(() => {
    const p: Record<string, { x: number; y: number }> = {};
    COLUMNS.forEach((col, ci) => {
      const colNodes = nodes.filter((n: VcmNode) => col.kinds.includes(n.kind));
      colNodes.forEach((n: VcmNode, ri: number) => {
        p[n.id] = { x: PAD + ci * (NODE_W + GAP_X), y: PAD + 22 + ri * (NODE_H + GAP_Y) };
      });
    });
    return p;
  }, [nodes]);
  const totalW = PAD * 2 + COLUMNS.length * NODE_W + (COLUMNS.length - 1) * GAP_X;
  const maxRows = Math.max(1, ...COLUMNS.map(c => nodes.filter((n: VcmNode) => c.kinds.includes(n.kind)).length));
  const totalH = PAD * 2 + 22 + maxRows * (NODE_H + GAP_Y);

  const focusSet = useMemo(() => {
    const id = hoverId ?? openId;
    if (!id) return null;
    const s = new Set<string>([id]);
    for (const nb of neighbours.get(id) ?? []) s.add(nb);
    return s;
  }, [hoverId, openId, neighbours]);

  const openNode = openId ? nodeById.get(openId) ?? null : null;

  if (error) {
    return (
      <div style={{ padding: 16, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12 }}>
        VCM graph · {error}
        <div style={{ marginTop: 8 }}>
          <button onClick={() => void load()} style={{ fontSize: 11 }}>retry</button>
        </div>
      </div>
    );
  }
  if (!doc) return <div style={{ padding: 16, color: 'var(--fg-mute)' }}>VCM graph · loading…</div>;

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', padding: '6px 10px', borderBottom: '1px solid var(--line)', flexWrap: 'wrap' }}>
        <span className="mute" style={{ fontSize: 10, fontFamily: 'var(--mono)' }}>
          ── VCM SPINE · {doc.ip}{doc.locked ? ' · locked' : ''} · {nodes.length} nodes
        </span>
        <input
          value={query}
          onChange={(e: { readonly target: { readonly value: string } }) => setQuery(e.target.value)}
          placeholder="search id / label / data…"
          style={{ fontSize: 11, padding: '2px 6px', background: 'var(--bg-2)', border: '1px solid var(--line)', color: 'var(--fg)', minWidth: 180 }}
        />
        {STATUS_FILTERS.map(s => (
          <span
            key={s}
            onClick={() => setStatusFilter(statusFilter === s ? '' : s)}
            style={{
              cursor: 'pointer', fontSize: 10, padding: '1px 7px', borderRadius: 2,
              fontFamily: 'var(--mono)', textTransform: 'uppercase',
              color: statusFilter === s ? statusColor(s) : 'var(--fg-mute)',
              border: '1px solid ' + (statusFilter === s ? statusColor(s) : 'var(--line)'),
            }}
          >{s}</span>
        ))}
        {COLUMNS.map(c => (
          <span
            key={c.key}
            onClick={() => setKindFilter(kindFilter === c.key ? '' : c.key)}
            style={{
              cursor: 'pointer', fontSize: 10, padding: '1px 7px', borderRadius: 2,
              fontFamily: 'var(--mono)',
              color: kindFilter === c.key ? 'var(--accent)' : 'var(--fg-mute)',
              border: '1px solid ' + (kindFilter === c.key ? 'var(--accent)' : 'var(--line)'),
            }}
          >{c.title}</span>
        ))}
        <span style={{ flex: 1 }} />
        <button onClick={() => void load()} style={{ fontSize: 10 }}>↻</button>
      </div>
      <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
        <div style={{ flex: 1, overflow: 'auto', background: 'var(--bg-2)' }}>
          <svg width={totalW} height={totalH} style={{ display: 'block' }}>
            <defs>
              <marker id="vcm-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                <path d="M0,0 L10,5 L0,10 z" fill="var(--fg-mute)" />
              </marker>
            </defs>
            {COLUMNS.map((col, ci) => (
              <text key={col.key} x={PAD + ci * (NODE_W + GAP_X)} y={PAD + 6} fill="var(--fg-mute)"
                    fontSize={10} fontFamily="var(--mono)" letterSpacing="0.08em">{col.title}</text>
            ))}
            {edges.map((e, i) => {
              const a = pos[e.source];
              const b = pos[e.target];
              if (!a || !b) return null;
              const inFocus = !focusSet || (focusSet.has(e.source) && focusSet.has(e.target));
              const x1 = a.x + NODE_W;
              const y1 = a.y + NODE_H / 2;
              const x2 = b.x;
              const y2 = b.y + NODE_H / 2;
              const mx = (x1 + x2) / 2;
              return (
                <path
                  key={i}
                  d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
                  fill="none"
                  stroke={inFocus ? 'var(--fg-mute)' : 'color-mix(in oklch, var(--fg-mute) 22%, transparent)'}
                  strokeWidth={focusSet && inFocus ? 1.6 : 1}
                  markerEnd="url(#vcm-arr)"
                />
              );
            })}
            {nodes.map(n => {
              const p = pos[n.id];
              if (!p) return null;
              const hit = matches(n);
              const inFocus = !focusSet || focusSet.has(n.id);
              const dim = !hit || !inFocus;
              const color = statusColor(n.status);
              return (
                <g
                  key={n.id}
                  transform={`translate(${p.x}, ${p.y})`}
                  style={{ cursor: 'pointer', opacity: dim ? 0.28 : 1 }}
                  onClick={() => setOpenId(openId === n.id ? null : n.id)}
                  onMouseEnter={() => setHoverId(n.id)}
                  onMouseLeave={() => setHoverId(null)}
                >
                  <rect
                    width={NODE_W} height={NODE_H} rx={3}
                    fill={`color-mix(in oklch, ${color} ${openId === n.id ? 22 : 12}%, transparent)`}
                    stroke={openId === n.id ? color : (n.kind === 'ghost' ? 'var(--err, #e05a5a)' : 'var(--line)')}
                    strokeDasharray={n.kind === 'ghost' ? '4 3' : undefined}
                  />
                  <text x={8} y={14} fontSize={10} fontFamily="var(--mono)" fill="var(--fg)">
                    {n.id.length > 24 ? n.id.slice(0, 23) + '…' : n.id}
                  </text>
                  <text x={8} y={27} fontSize={9} fontFamily="var(--mono)" fill={color}>
                    {n.status}{n.label && n.label !== n.id ? ' · ' + (n.label.length > 18 ? n.label.slice(0, 17) + '…' : n.label) : ''}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
        {openNode && (
          <div style={{ width: 300, borderLeft: '1px solid var(--line)', overflow: 'auto', padding: 12, fontSize: 11, fontFamily: 'var(--mono)' }}>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{openNode.id}</div>
            <div style={{ color: statusColor(openNode.status), marginBottom: 8 }}>
              {openNode.kind} · {openNode.status}
            </div>
            {openNode.label !== openNode.id && <div style={{ marginBottom: 8 }}>{openNode.label}</div>}
            {Object.entries(openNode.data).map(([k, v]) => (
              v !== '' && v != null ? (
                <div key={k} style={{ marginBottom: 6 }}>
                  <span className="mute">{k}:</span>{' '}
                  <span style={{ wordBreak: 'break-all' }}>{typeof v === 'string' ? v : JSON.stringify(v)}</span>
                </div>
              ) : null
            ))}
            <div className="mute" style={{ marginTop: 10, fontSize: 10 }}>
              linked: {[...(neighbours.get(openNode.id) ?? [])].slice(0, 12).join(', ') || '(none)'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VcmGraphTab;
