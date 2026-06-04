// __tests__/admin-session-flow.test.tsx
//
// THE WIRING GATE for the Session Flow admin tab (Task 5): admin.tsx state +
// lazy load + tab registration, plus the new admin-session-flow.tsx component.
//
// Modeled after user-dashboard-render-smoke.test.tsx (real-component mount in
// jsdom with window globals / fetch stubbed), this mounts the REAL AdminPage and
// asserts the two load-bearing contracts of the wiring task:
//
//   1. LAZY-LOAD: the initial admin boot (auth status + loadAdminData's
//      Promise.all of users/sessions/ips/usage/feedback/runtime) does NOT fetch
//      /api/admin/session-flow. Activating the "Session Flow" tab fetches it
//      EXACTLY ONCE. (No initial Promise.all entry; no tight poll.)
//   2. KEEPS EXISTING FLOW TAB: the existing "Flow" tab still renders todo-flow
//      data (from usage.todo_flow), and the new "Session Flow" tab is a SEPARATE,
//      distinct tab — both buttons present, distinct labels, distinct panels.
//
// If a future refactor folds session-flow into loadAdminData, polls it, or
// repurposes the Flow tab, one of these assertions fails.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
// Full-app mount + a click cycle in jsdom can exceed the 5s default under load.
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 });

import { useState } from 'react';
import { render, cleanup, screen, act, fireEvent } from '@testing-library/react';

import { AdminSessionFlowTab } from '../admin-session-flow.tsx';

// A distinctive todo-flow content string so we can assert the EXISTING Flow tab
// still renders todo-flow data (and is not the new Session Flow tab).
const TODO_FLOW_CONTENT = 'TODO-FLOW-MARKER-ROW';

// A session-flow payload with one critical + one warning + one ok session so
// the tab renders rows, the funnel, the count band (needs_attention length 2),
// plus IP flow and attribution gaps for the detail panel + lens assertions.
function sessionFlowPayload() {
  return {
    generated_at: Date.now() / 1000,
    runtime_mode: false,
    range: '7d',
    lens: 'team_lead',
    summary: {
      critical: 1, warning: 1, ok: 1, session_count: 3, ip_count: 1,
      total_cost_usd: 3.4567, total_llm_attempts: 9, total_artifacts: 2,
      total_inputs: 7, attribution_gap_count: 1, unmatched_cost_usd: 2.5,
    },
    needs_attention: [
      { session_id: 's-crit', risk_level: 'critical', risk_reason: 'workflow_blocked' },
      { session_id: 's-warn', risk_level: 'warning', risk_reason: 'no_artifact_after_llm' },
    ],
    funnel: [
      { stage: 'created', count: 3 },
      { stage: 'input', count: 3 },
      { stage: 'worker', count: 2 },
      { stage: 'llm', count: 2 },
      { stage: 'artifact', count: 1 },
      { stage: 'verified', count: 1 },
      { stage: 'completed', count: 1 },
    ],
    sessions: [
      {
        session_id: 's-crit', session_uid: 'uid-crit-RAW', namespace: 'demo', title: 'Critical Session',
        username: 'alice', user_id: 'u-alice', ip_id: 'ip-1', ip: 'uart_v2', workflow: 'ssot-gen',
        flow_state: 'blocked', risk_level: 'critical', risk_reason: 'workflow_blocked',
        input_count: 3, input_chars: 120, input_tokens_est: 30,
        llm_attempts: 5, llm_success: 4, llm_errors: 1,
        tokens_input: 1000, tokens_output: 800, tokens_reasoning: 50,
        cost_usd: 1.2345, worker_runs: 2, active_workers: 0, failed_workers: 1,
        workflow_runs: 1, workflow_errors: 0, artifact_count: 0,
        attribution_confidence: 'exact', missing_reason: '', next_action: 'resolve block',
        stale_age_s: 90000,
      },
      {
        session_id: 's-warn', session_uid: 'uid-warn-RAW', namespace: 'demo', title: 'Warning Session',
        username: 'bob', user_id: 'u-bob', ip_id: 'ip-1', ip: 'uart_v2', workflow: 'rtl-gen',
        flow_state: 'running', risk_level: 'warning', risk_reason: 'no_artifact_after_llm',
        input_count: 2, input_chars: 80, input_tokens_est: 20,
        llm_attempts: 4, llm_success: 4, llm_errors: 0,
        tokens_input: 600, tokens_output: 400, tokens_reasoning: 0,
        cost_usd: 0.72, worker_runs: 1, active_workers: 1, failed_workers: 0,
        workflow_runs: 1, workflow_errors: 0, artifact_count: 0,
        attribution_confidence: 'inferred', missing_reason: 'temporal_inferred', next_action: 'inspect failed/empty run',
        stale_age_s: 1200,
      },
      {
        session_id: 's-ok', session_uid: 'uid-ok-RAW', namespace: 'demo', title: 'OK Session',
        username: 'carol', user_id: 'u-carol', ip_id: 'ip-1', ip: 'uart_v2', workflow: 'ssot-gen',
        flow_state: 'completed', risk_level: 'ok', risk_reason: 'completed',
        input_count: 2, input_chars: 60, input_tokens_est: 15,
        llm_attempts: 0, llm_success: 0, llm_errors: 0,
        tokens_input: 0, tokens_output: 0, tokens_reasoning: 0,
        cost_usd: 0, worker_runs: 1, active_workers: 0, failed_workers: 0,
        workflow_runs: 1, workflow_errors: 0, artifact_count: 2,
        attribution_confidence: 'exact', missing_reason: '', next_action: '',
        stale_age_s: 300,
      },
    ],
    ip_flow: [
      {
        ip_id: 'ip-1', ip: 'uart_v2', workspace_id: 'ws-1', created_by_user_id: 'u-alice',
        source_session_id: 's-crit', source_type: 'workflow', source_confidence: 'exact',
        ip_created_at: Date.now() / 1000 - 86400, risk_level: 'critical',
        sessions: 3, active_sessions: 1, workflows: 2, worker_runs: 4,
        artifact_count: 2, llm_attempts: 9, cost_usd: 1.9545, problem_count: 2,
      },
    ],
    attribution_gaps: [
      {
        session_id: 's-orphan', kind: 'unmatched_llm_spend', llm_attempts: 3,
        cost_usd: 2.5, tokens: 5000, confidence: 'missing', missing_reason: 'no_source_session',
      },
    ],
    pagination: { limit: 100, offset: 0, max_limit: 500, total_sessions: 3, returned: 3 },
  };
}

// Route fetch by URL. Counts session-flow calls so we can assert lazy-load.
let sessionFlowCalls = 0;

function installFetch() {
  sessionFlowCalls = 0;
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

  globalThis.fetch = vi.fn(async (input: any) => {
    const url = String(typeof input === 'string' ? input : (input?.url || ''));
    if (url.includes('/api/admin/auth/status')) {
      // No login required → admin loads immediately (mirrors local-admin bypass).
      return json({ login_required: false, authenticated: true, admin_user_exists: true, mode: 'local', user: { id: 1, username: 'admin' } });
    }
    if (url.includes('/api/admin/session-flow')) {
      sessionFlowCalls += 1;
      return json(sessionFlowPayload());
    }
    if (url.includes('/api/admin/usage')) {
      return json({
        users: [],
        todo_flow: [{ event_id: 'e1', todo_id: 't1', content: TODO_FLOW_CONTENT, event_type: 'approved', created_at: Date.now() / 1000 }],
      });
    }
    if (url.includes('/api/admin/feedback')) return json({ feedback: [] });
    if (url.includes('/api/admin/runtime')) return json({});
    // users / sessions / ips and anything else → empty-OK lists.
    return json({ users: [], sessions: [], ips: [] });
  }) as unknown as typeof fetch;
}

async function mountAdmin() {
  const { AdminPage } = await import('../admin.tsx');
  const result = render(<AdminPage />);
  // Flush the auth-status fetch + loadAdminData Promise.all + state commits.
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  return result;
}

describe('Session Flow admin tab wiring (Task 5)', () => {
  beforeEach(() => {
    installFetch();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('lazy-loads: initial admin render does NOT fetch session-flow; activating the tab fetches it once', async () => {
    await mountAdmin();

    // Initial boot must NOT have hit the session-flow endpoint.
    expect(sessionFlowCalls).toBe(0);

    // The tab button exists in the tab row.
    const tabBtn = screen.getByText(/^Session Flow \(/);
    expect(tabBtn).toBeInTheDocument();

    // Activate the tab → exactly one fetch.
    await act(async () => {
      fireEvent.click(tabBtn);
      await Promise.resolve(); await Promise.resolve();
    });
    expect(sessionFlowCalls).toBe(1);

    // The panel rendered the seeded session row + needs-attention band.
    expect(await screen.findByText('Critical Session')).toBeInTheDocument();
    expect(screen.getByText('Needs Attention')).toBeInTheDocument();
  });

  it('keeps existing Flow tab as todo-flow; Session Flow is a separate, distinct tab', async () => {
    await mountAdmin();

    // Both tab buttons are present and distinct.
    const flowBtn = screen.getByText(/^Flow \(/);
    const sessionFlowBtn = screen.getByText(/^Session Flow \(/);
    expect(flowBtn).toBeInTheDocument();
    expect(sessionFlowBtn).toBeInTheDocument();
    expect(flowBtn).not.toBe(sessionFlowBtn);

    // Activating the existing Flow tab renders todo-flow data (NOT session flow),
    // and must not fetch the session-flow endpoint.
    await act(async () => {
      fireEvent.click(flowBtn);
      await Promise.resolve(); await Promise.resolve();
    });
    expect(screen.getByText(TODO_FLOW_CONTENT)).toBeInTheDocument();
    expect(sessionFlowCalls).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Task 6: the AdminSessionFlowTab dashboard (component-level, no admin shell).
// Mounts the REAL component with a controlled lens so we can assert that lens
// switching is CLIENT-SIDE (no refetch — the component never calls fetch) and
// changes which fields/sections render. We control `lens` via a tiny harness
// that owns the lens state, exactly like admin.tsx does.
// ---------------------------------------------------------------------------

function ComponentHarness({ data }: { data: any }) {
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

describe('Session Flow dashboard component (Task 6)', () => {
  beforeEach(() => {
    // The component must NOT fetch on its own; track any stray calls.
    sessionFlowCalls = 0;
    globalThis.fetch = vi.fn(async () => {
      sessionFlowCalls += 1;
      return new Response('{}', { status: 200 });
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('renders session flow payload: Needs Attention band, funnel, and triage table with critical/warning/ok rows', () => {
    render(<ComponentHarness data={sessionFlowPayload()} />);

    // Needs Attention band (team_lead default lens shows critical/warning tiles).
    expect(screen.getByText('Critical Sessions')).toBeInTheDocument();
    expect(screen.getByText('Warning Sessions')).toBeInTheDocument();

    // Funnel rendered as INDEPENDENT per-stage tallies (label says so).
    expect(screen.getByText(/independent per-stage tallies/i)).toBeInTheDocument();
    expect(screen.getByText('Created')).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();

    // Triage table has all three risk rows.
    expect(screen.getByText('Critical Session')).toBeInTheDocument();
    expect(screen.getByText('Warning Session')).toBeInTheDocument();
    expect(screen.getByText('OK Session')).toBeInTheDocument();

    // The component never fetched anything itself.
    expect(sessionFlowCalls).toBe(0);
  });

  it('lens switching changes visible fields WITHOUT a refetch (builder shows attribution + raw IDs; executive hides raw IDs and shows cost/risk)', () => {
    render(<ComponentHarness data={sessionFlowPayload()} />);
    expect(sessionFlowCalls).toBe(0);

    // team_lead (default): no Attribution column header, no raw session_uid.
    expect(screen.queryByText('Attribution')).not.toBeInTheDocument();
    expect(screen.queryByText('uid-crit-RAW')).not.toBeInTheDocument();

    // Switch to Builder → attribution column + raw IDs appear, still no fetch.
    fireEvent.click(screen.getByText('Builder'));
    expect(screen.getByText('Attribution')).toBeInTheDocument();
    expect(screen.getByText('uid-crit-RAW')).toBeInTheDocument();
    expect(sessionFlowCalls).toBe(0);

    // Switch to Executive → raw IDs hidden again, cost + risk rollup visible.
    fireEvent.click(screen.getByText('Executive'));
    expect(screen.queryByText('uid-crit-RAW')).not.toBeInTheDocument();
    expect(screen.getByText('Total Cost')).toBeInTheDocument();
    expect(screen.getByText(/Risk \(crit\/warn\/ok\)/i)).toBeInTheDocument();
    expect(sessionFlowCalls).toBe(0);

    // Switch back to Team Lead → fields revert; never any fetch across toggles.
    fireEvent.click(screen.getByText('Team Lead'));
    expect(screen.getByText('Critical Sessions')).toBeInTheDocument();
    expect(screen.queryByText('uid-crit-RAW')).not.toBeInTheDocument();
    expect(sessionFlowCalls).toBe(0);
  });

  it('clicking a session row opens the detail panel with input/LLM/worker/IP/artifact/gap sections', () => {
    render(<ComponentHarness data={sessionFlowPayload()} />);

    // No detail panel until a row is clicked.
    expect(screen.queryByText('Session Detail')).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Critical Session'));

    expect(screen.getByText('Session Detail')).toBeInTheDocument();
    expect(screen.getByText('Session Identity')).toBeInTheDocument();
    expect(screen.getByText('Input Metrics')).toBeInTheDocument();
    expect(screen.getByText('LLM Metrics')).toBeInTheDocument();
    expect(screen.getByText('Worker Timeline')).toBeInTheDocument();
    expect(screen.getByText('IP Provenance')).toBeInTheDocument();
    expect(screen.getByText('Artifacts / Outcomes')).toBeInTheDocument();
    // Per-session attribution/confidence section (distinct from the fleet-level
    // "Attribution Gaps" table title, so this text is unambiguous).
    expect(screen.getByText('Attribution / Confidence')).toBeInTheDocument();

    // Closing the panel hides it again.
    fireEvent.click(screen.getByText('Close'));
    expect(screen.queryByText('Session Detail')).not.toBeInTheDocument();
  });

  it('selection survives lens toggle: detail panel stays open and builder shows raw IDs', () => {
    render(<ComponentHarness data={sessionFlowPayload()} />);

    // Open detail panel by clicking the critical session row.
    fireEvent.click(screen.getByText('Critical Session'));
    expect(screen.getByText('Session Detail')).toBeInTheDocument();
    expect(sessionFlowCalls).toBe(0);

    // Toggle to Builder lens — panel must still be present (selection keyed by id,
    // not dependent on lens or refetch), and the raw session_uid must appear.
    fireEvent.click(screen.getByText('Builder'));
    expect(screen.getByText('Session Detail')).toBeInTheDocument();
    // uid-crit-RAW is shown in both the triage row AND the detail identity block
    // in builder mode — getAllByText confirms at least one is present.
    expect(screen.getAllByText('uid-crit-RAW').length).toBeGreaterThanOrEqual(1);
    expect(sessionFlowCalls).toBe(0);

    // Toggle back to Team Lead — panel still open, raw ID hidden.
    fireEvent.click(screen.getByText('Team Lead'));
    expect(screen.getByText('Session Detail')).toBeInTheDocument();
    expect(screen.queryByText('uid-crit-RAW')).not.toBeInTheDocument();
    expect(sessionFlowCalls).toBe(0);
  });

  it('empty payload renders a clear operational empty state', () => {
    const empty = {
      generated_at: Date.now() / 1000, runtime_mode: false, range: '7d', lens: 'team_lead',
      summary: { critical: 0, warning: 0, ok: 0 }, needs_attention: [],
      funnel: [], sessions: [], ip_flow: [], attribution_gaps: [],
      pagination: { limit: 100, offset: 0, max_limit: 500, total_sessions: 0, returned: 0 },
    };
    render(<ComponentHarness data={empty} />);
    expect(screen.getByText(/Nothing needs action/i)).toBeInTheDocument();
  });

  it('error payload renders an error state (and does not throw, leaving other tabs usable)', () => {
    render(
      <AdminSessionFlowTab
        data={null}
        loading={false}
        error="Admin role required"
        lens="team_lead"
        onLensChange={() => {}}
      />,
    );
    expect(screen.getByText('Admin role required')).toBeInTheDocument();
    // The lens toggle still renders in the error state (lens is fetch-independent).
    expect(screen.getByText('Builder')).toBeInTheDocument();
  });
});
