// VCM tab — interactive React Flow graph of the verification-contract spine:
// Requirement → Obligation → Contract → Evidence → Validation.
// Data comes from <ip>/req/vcm_graph.json (emit_vcm_graph.py); this component
// builds React Flow nodes/edges (dagre LR layout), with free-text search,
// status/kind filter chips, neighbour focus on select, and a detail panel.
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
  GraphCanvas,
  layoutDagre,
  flowArrow,
  type FlowNode,
  type FlowEdge,
  type FlowCardData,
} from './workspace-graph-flow';

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

export type VcmGraphDoc = {
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

const vcmSubtitle = (n: VcmNode): string => {
  const label = n.label && n.label !== n.id ? n.label : '';
  return label ? `${n.status} · ${label}` : n.status;
};

// Pure builder (exported for tests): vcm_graph.json doc → laid-out React Flow
// base nodes (dagre LR, no dim/selected applied yet) + edges.
export function buildVcmElements(doc: VcmGraphDoc): { nodes: FlowNode[]; edges: FlowEdge[] } {
  const baseNodes: FlowNode[] = doc.nodes.map((n) => ({
    id: n.id,
    type: 'card',
    position: { x: 0, y: 0 },
    data: {
      title: n.id,
      subtitle: vcmSubtitle(n),
      color: statusColor(n.status),
      dashed: n.kind === 'ghost',
    } satisfies FlowCardData as unknown as Record<string, unknown>,
  }));
  const edges: FlowEdge[] = doc.edges.map((e, i) => ({
    id: `e${i}-${e.source}-${e.target}`,
    source: e.source,
    target: e.target,
    label: e.kind,
    markerEnd: flowArrow,
    style: { stroke: 'var(--fg-mute, #888)' },
    labelStyle: { fill: 'var(--fg-mute, #888)', fontSize: 8, fontFamily: 'var(--mono, monospace)' },
    labelBgStyle: { fill: 'var(--bg-2, #181818)' },
  }));
  return { nodes: layoutDagre(baseNodes, edges, { direction: 'LR' }), edges };
}

export const VcmGraphTab = ({ activeIp }: { readonly activeIp: string }): ReactNode => {
  const [doc, setDoc] = useState<VcmGraphDoc | null>(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [kindFilter, setKindFilter] = useState<string>('');
  const [openId, setOpenId] = useState<string | null>(null);

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

  const built = useMemo(() => (doc ? buildVcmElements(doc) : { nodes: [], edges: [] }), [doc]);

  const q = query.trim().toLowerCase();
  const matches = useCallback((n: VcmNode): boolean => {
    if (statusFilter && n.status !== statusFilter) return false;
    if (kindFilter && !COLUMNS.find(c => c.key === kindFilter)?.kinds.includes(n.kind)) return false;
    if (!q) return true;
    const hay = (n.id + ' ' + n.label + ' ' + JSON.stringify(n.data)).toLowerCase();
    return hay.includes(q);
  }, [q, statusFilter, kindFilter]);

  const focusSet = useMemo(() => {
    if (!openId) return null;
    const s = new Set<string>([openId]);
    for (const nb of neighbours.get(openId) ?? []) s.add(nb);
    return s;
  }, [openId, neighbours]);

  // Apply per-filter dim + selection onto the laid-out base nodes.
  const displayNodes = useMemo<FlowNode[]>(() => built.nodes.map((rn) => {
    const src = nodeById.get(rn.id);
    const hit = src ? matches(src) : true;
    const inFocus = !focusSet || focusSet.has(rn.id);
    const data = rn.data as unknown as FlowCardData;
    return {
      ...rn,
      selected: openId === rn.id,
      data: { ...data, dim: !hit || !inFocus } as unknown as Record<string, unknown>,
    };
  }), [built.nodes, nodeById, matches, focusSet, openId]);

  const displayEdges = useMemo<FlowEdge[]>(() => built.edges.map((e) => {
    const inFocus = !focusSet || (focusSet.has(String(e.source)) && focusSet.has(String(e.target)));
    return { ...e, style: { ...(e.style || {}), opacity: inFocus ? 1 : 0.18 }, animated: Boolean(focusSet && inFocus) };
  }), [built.edges, focusSet]);

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
        <div style={{ flex: 1, minHeight: 0, background: 'var(--bg-2)' }}>
          <GraphCanvas nodes={displayNodes} edges={displayEdges} onSelect={setOpenId} minimap />
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
