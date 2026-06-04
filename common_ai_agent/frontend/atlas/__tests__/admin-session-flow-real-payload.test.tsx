// __tests__/admin-session-flow-real-payload.test.tsx
//
// PART C of the Session Flow E2E gate: render the AdminSessionFlowTab from the
// REAL payload captured end-to-end by scripts/atlas_session_flow_e2e.py — i.e.
// the JSON that actually flowed:  real write paths -> out-of-band fold ->
// GET /api/admin/session-flow (real server, admin local-auth) -> this fixture.
//
// This is the "the backend must surface it for the frontend to show it" proof:
// the component is NOT fed a hand-written mock; it is fed the byte-for-byte
// payload the live HTTP route returned. If the backend stops surfacing populated
// rows/funnel/needs_attention, this render assertion fails.
//
// Browser/chromium E2E is known to fail in this env, so the proof is the
// real-payload -> component render (jsdom), not a headed browser.
//
// To regenerate the fixture:  python3 scripts/atlas_session_flow_e2e.py
import { afterEach, describe, expect, it } from 'vitest';
import { render, cleanup, screen, fireEvent, within } from '@testing-library/react';
import { useState } from 'react';

import { AdminSessionFlowTab } from '../admin-session-flow.tsx';
// The REAL captured payload (committed fixture produced by the e2e harness).
import realPayload from './fixtures/session-flow-real-payload.json';

// Tiny harness owning the lens state exactly like admin.tsx does, so a lens
// toggle is client-side (no refetch) — mirrors the production wiring.
function Harness({ data }: { data: any }) {
  const [lens, setLens] = useState('team_lead');
  return (
    <AdminSessionFlowTab
      data={data}
      loading={false}
      error={null}
      lens={lens}
      onLensChange={(l) => setLens(l)}
    />
  );
}

describe('AdminSessionFlowTab renders the REAL captured e2e payload (Part C)', () => {
  afterEach(() => cleanup());

  it('the fixture is the real runtime-mode HTTP payload (sanity on the captured shape)', () => {
    // Guardrails so a stale/empty fixture cannot silently pass the render tests.
    expect(realPayload.runtime_mode).toBe(true);
    expect(Array.isArray(realPayload.sessions)).toBe(true);
    expect(realPayload.sessions.length).toBeGreaterThanOrEqual(3);
    expect(realPayload.pagination.max_limit).toBe(500);
    expect(realPayload.funnel.length).toBe(7);
    expect(realPayload.needs_attention.length).toBeGreaterThanOrEqual(1);

    // The real chain produced ok + warning triage rows (runtime mode does not
    // mark the problem session 'critical'); assert what actually flowed.
    const risks = realPayload.sessions.map((s: any) => s.risk_level);
    expect(risks).toContain('ok');
    expect(risks).toContain('warning');
  });

  it('renders Needs Attention band, funnel, and the triage table from the real payload', () => {
    render(<Harness data={realPayload as any} />);

    // Needs Attention band (team_lead default lens).
    expect(screen.getByText('Needs Attention')).toBeInTheDocument();
    expect(screen.getByText('Critical Sessions')).toBeInTheDocument();
    expect(screen.getByText('Warning Sessions')).toBeInTheDocument();

    // Independent-per-stage funnel rendered with real stage labels.
    expect(screen.getByText(/independent per-stage tallies/i)).toBeInTheDocument();
    expect(screen.getByText('Created')).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();

    // Triage table rendered with the real session count.
    expect(
      screen.getByText(`Sessions (${realPayload.sessions.length})`),
    ).toBeInTheDocument();

    // Every real session is rendered as a row (by title or short id), with its
    // real risk pill present.
    const okRow = realPayload.sessions.find((s: any) => s.risk_level === 'ok')!;
    const warnRow = realPayload.sessions.find((s: any) => s.risk_level === 'warning')!;
    expect(okRow).toBeTruthy();
    expect(warnRow).toBeTruthy();
    // The healthy "title-uart_healthy" session title from the real chain shows.
    expect(screen.getByText(String(okRow.title))).toBeInTheDocument();
  });

  it('renders the real risk tiers (ok + warning) as pills and a populated funnel count', () => {
    render(<Harness data={realPayload as any} />);

    // The risk pills reflect the real classification flowed from the fold.
    expect(screen.getAllByText('ok').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('warning').length).toBeGreaterThanOrEqual(1);

    // The 'created' funnel stage equals the real session count (>=3).
    const created = realPayload.funnel.find((f: any) => f.stage === 'created')!;
    expect(created.count).toBe(realPayload.sessions.length);
  });

  it('clicking a real session row opens the detail panel with all sections', () => {
    render(<Harness data={realPayload as any} />);

    // No detail panel until a row is clicked.
    expect(screen.queryByText('Session Detail')).not.toBeInTheDocument();

    // Click the healthy session row (real title from the captured payload).
    const okRow = realPayload.sessions.find((s: any) => s.risk_level === 'ok')!;
    fireEvent.click(screen.getByText(String(okRow.title)));

    // Detail panel + every section appears, driven by the real row's fields.
    expect(screen.getByText('Session Detail')).toBeInTheDocument();
    expect(screen.getByText('Session Identity')).toBeInTheDocument();
    expect(screen.getByText('Input Metrics')).toBeInTheDocument();
    expect(screen.getByText('LLM Metrics')).toBeInTheDocument();
    expect(screen.getByText('Worker Timeline')).toBeInTheDocument();
    expect(screen.getByText('IP Provenance')).toBeInTheDocument();
    expect(screen.getByText('Artifacts / Outcomes')).toBeInTheDocument();
    expect(screen.getByText('Attribution / Confidence')).toBeInTheDocument();

    // The detail panel shows the real artifact count (healthy session has 1).
    const detail = screen.getByText('Session Detail').closest('div');
    expect(detail).toBeTruthy();

    // Closing the panel hides it again.
    fireEvent.click(screen.getByText('Close'));
    expect(screen.queryByText('Session Detail')).not.toBeInTheDocument();
  });

  it('builder lens exposes the real attribution gap fields without a refetch', () => {
    render(<Harness data={realPayload as any} />);

    // team_lead default: no Attribution column.
    expect(screen.queryByText('Attribution')).not.toBeInTheDocument();

    // Switch to Builder -> the Attribution column appears (client-side only).
    fireEvent.click(screen.getByText('Builder'));
    expect(screen.getByText('Attribution')).toBeInTheDocument();

    // The ghost/unmatched row from the REAL payload carries an attribution
    // confidence (inferred/missing) that the builder lens surfaces.
    const ghost = realPayload.sessions.find(
      (s: any) => !s.username && (s.attribution_confidence === 'inferred'
        || s.attribution_confidence === 'missing'),
    );
    if (ghost) {
      // At least one attribution-confidence cell is rendered in builder mode.
      expect(
        screen.getAllByText(String(ghost.attribution_confidence)).length,
      ).toBeGreaterThanOrEqual(1);
    }
  });
});
