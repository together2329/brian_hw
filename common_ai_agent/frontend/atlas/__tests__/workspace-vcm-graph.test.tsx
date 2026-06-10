// Tests for the VCM React Flow tab (workspace-vcm-graph.tsx).
// The graph logic lives in the pure builder buildVcmElements (json → laid-out
// React Flow nodes/edges) — tested directly. A smoke mount proves the tab
// renders its header + the missing-json guidance without throwing (React Flow
// canvas itself is exercised via the build, not asserted pixel-by-pixel).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';

import { VcmGraphTab, buildVcmElements, type VcmGraphDoc } from '../workspace-vcm-graph';

const GRAPH: VcmGraphDoc = {
  ip: 'demo_ip',
  locked: true,
  nodes: [
    { id: 'REQ_A', kind: 'requirement', label: 'Req A', status: 'locked', data: { statement: 'counts pulses' } },
    { id: 'OBL_A', kind: 'obligation', label: 'OBL_A', status: 'open', data: { owned_by: 'sim' } },
    { id: 'BEH_A', kind: 'behavioral_contract', label: 'Beh A', status: 'closed', data: {} },
    { id: 'EV_A', kind: 'evidence', label: 'EV_A', status: 'present', data: { stage: 'sim' } },
    { id: 'VAL_SIM_SCOREBOARD', kind: 'validation', label: 'sim scoreboard 3/3', status: 'pass', data: {} },
    { id: 'GHOST_X', kind: 'ghost', label: 'dangling', status: 'missing', data: {} },
  ],
  edges: [
    { source: 'REQ_A', target: 'OBL_A', kind: 'requires' },
    { source: 'OBL_A', target: 'BEH_A', kind: 'contracted_by' },
    { source: 'BEH_A', target: 'EV_A', kind: 'evidenced_by' },
    { source: 'EV_A', target: 'VAL_SIM_SCOREBOARD', kind: 'validated_by' },
  ],
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('buildVcmElements', () => {
  it('builds one laid-out node per spine entry with status colours', () => {
    const { nodes } = buildVcmElements(GRAPH);
    expect(nodes).toHaveLength(6);
    // dagre assigned real positions (not all at origin)
    expect(nodes.some(n => n.position.x !== 0 || n.position.y !== 0)).toBe(true);
    const byId = new Map(nodes.map(n => [n.id, n.data as Record<string, unknown>]));
    expect(byId.get('REQ_A')?.title).toBe('REQ_A');
    expect(String(byId.get('REQ_A')?.color)).toContain('--accent');   // locked
    expect(String(byId.get('VAL_SIM_SCOREBOARD')?.color)).toContain('--ok'); // pass
    expect(String(byId.get('GHOST_X')?.color)).toContain('--err');    // missing
    expect(byId.get('GHOST_X')?.dashed).toBe(true);                   // ghost node dashed
  });

  it('maps each spine edge with its relation label and arrow head', () => {
    const { edges } = buildVcmElements(GRAPH);
    expect(edges).toHaveLength(4);
    expect(edges.map(e => e.label)).toEqual(['requires', 'contracted_by', 'evidenced_by', 'validated_by']);
    expect(edges[0]).toMatchObject({ source: 'REQ_A', target: 'OBL_A' });
    expect(edges[0].markerEnd).toBeTruthy();
  });
});

describe('VcmGraphTab', () => {
  const mockFetchOk = () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => GRAPH })) as unknown as typeof fetch);
  };

  it('renders the spine header summary from vcm_graph.json', async () => {
    mockFetchOk();
    render(<VcmGraphTab activeIp="demo_ip" />);
    expect(await screen.findByText(/VCM SPINE · demo_ip · locked · 6 nodes/)).toBeTruthy();
  });

  it('shows the guidance message when the graph json is missing', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false })) as unknown as typeof fetch);
    render(<VcmGraphTab activeIp="demo_ip" />);
    expect(await screen.findByText(/emit_vcm_graph\.py/)).toBeTruthy();
  });
});
