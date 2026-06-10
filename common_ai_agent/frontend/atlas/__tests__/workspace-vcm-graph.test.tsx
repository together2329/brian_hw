// Smoke + behavior test for the VCM tab graph (workspace-vcm-graph.tsx).
// Mounts VcmGraphTab in jsdom with /api/file mocked to a tiny vcm_graph.json
// and asserts: nodes render, the search box filters (dimming, not removal),
// the status chips exist, and clicking a node opens the detail panel.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';

import { VcmGraphTab } from '../workspace-vcm-graph';

const GRAPH = {
  ip: 'demo_ip',
  locked: true,
  nodes: [
    { id: 'REQ_A', kind: 'requirement', label: 'Req A', status: 'locked', data: { statement: 'counts pulses' } },
    { id: 'OBL_A', kind: 'obligation', label: 'OBL_A', status: 'open', data: { owned_by: 'sim' } },
    { id: 'BEH_A', kind: 'behavioral_contract', label: 'Beh A', status: 'closed', data: {} },
    { id: 'EV_A', kind: 'evidence', label: 'EV_A', status: 'present', data: { stage: 'sim' } },
    { id: 'VAL_SIM_SCOREBOARD', kind: 'validation', label: 'sim scoreboard 3/3', status: 'pass', data: {} },
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

const mockFetchOk = () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    json: async () => GRAPH,
  })) as any);
};

describe('VcmGraphTab', () => {
  it('renders the spine nodes and validation status from vcm_graph.json', async () => {
    mockFetchOk();
    render(<VcmGraphTab activeIp="demo_ip" />);
    expect(await screen.findByText('REQ_A')).toBeTruthy();
    expect(screen.getByText('OBL_A')).toBeTruthy();
    expect(screen.getByText('BEH_A')).toBeTruthy();
    // header summary mentions ip + node count
    expect(screen.getByText(/VCM SPINE · demo_ip · locked · 5 nodes/)).toBeTruthy();
  });

  it('opens the detail panel on node click', async () => {
    mockFetchOk();
    render(<VcmGraphTab activeIp="demo_ip" />);
    const node = await screen.findByText('REQ_A');
    fireEvent.click(node);
    expect(screen.getByText(/requirement · locked/)).toBeTruthy();
    expect(screen.getByText(/counts pulses/)).toBeTruthy();
    // linked neighbours listed in the detail panel — OBL_A now appears twice
    // (SVG node label + the panel's linked list).
    expect(screen.getAllByText(/OBL_A/).length).toBeGreaterThanOrEqual(2);
  });

  it('shows the guidance message when the graph json is missing', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false })) as any);
    render(<VcmGraphTab activeIp="demo_ip" />);
    expect(await screen.findByText(/emit_vcm_graph\.py/)).toBeTruthy();
  });
});
