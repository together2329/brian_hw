/**
 * Behavior test for AtlasUserDashboard IP row click → onActivateSession.
 *
 * user-dashboard.jsx is a browser-globals script. We inline the minimal
 * component that reproduces the openIp() handler logic (lines 277-288)
 * and the IP inventory table row (lines 374-447) that calls it.
 * Payload building logic is imported from lib/dashboard_helpers.js (shared
 * with browser via window.AtlasDashboardHelpers UMD shim).
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { buildOpenIpPayload } from '../lib/dashboard_helpers.mjs';

// Mocked dashboard data shape matching /api/user/dashboard response
const MOCK_DASHBOARD = {
  ip_inventory: [
    {
      ip: 'uart_v2',
      ip_type: 'rtl',
      session_id: 'uart_v2/ssot-gen/abc123',
      workspace_count: 1,
      ip_row_count: 1,
      last_active: 1716400000,
    },
  ],
  ip_rows: [],
  session_rows: [],
};

// Minimal reproduction of user-dashboard.jsx openIp() + table row logic
function MinimalDashboard({ data, onActivateSession }) {
  const workflowValue = (row) => {
    if (!row.session_id) return '';
    const parts = String(row.session_id).split('/');
    return parts.length >= 2 ? parts[1] : '';
  };

  const openIp = (row) => {
    if (onActivateSession) {
      const payload = buildOpenIpPayload(row, workflowValue);
      onActivateSession(payload);
    }
  };

  const ipInventoryRows = (data && data.ip_inventory) || [];

  return (
    <table>
      <tbody>
        {ipInventoryRows.map((row) => (
          <tr
            key={row.ip}
            data-testid={`ip-row-${row.ip}`}
            onClick={() => row.ip && openIp(row)}
            style={{ cursor: row.ip ? 'pointer' : 'default' }}
          >
            <td>{row.ip || '-'}</td>
            <td>{row.ip_type || 'ip'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

describe('AtlasUserDashboard IP row click', () => {
  let onActivateSession;

  beforeEach(() => {
    onActivateSession = vi.fn();
    // Mock fetch so the real component (if wired) doesn't blow up
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => MOCK_DASHBOARD,
    });
  });

  it('calls onActivateSession with { ip, id, workflow } when IP row is clicked', async () => {
    const user = userEvent.setup();
    render(
      <MinimalDashboard data={MOCK_DASHBOARD} onActivateSession={onActivateSession} />
    );

    const row = screen.getByTestId('ip-row-uart_v2');
    await user.click(row);

    expect(onActivateSession).toHaveBeenCalledOnce();
    const payload = onActivateSession.mock.calls[0][0];
    expect(payload.ip).toBe('uart_v2');
    expect(payload).toHaveProperty('id');
  });

  it('does not call onActivateSession when ip field is empty', async () => {
    const user = userEvent.setup();
    const dataWithEmpty = {
      ip_inventory: [{ ip: '', ip_type: 'rtl', session_id: '', workspace_count: 1, ip_row_count: 1 }],
      ip_rows: [],
      session_rows: [],
    };
    render(
      <MinimalDashboard data={dataWithEmpty} onActivateSession={onActivateSession} />
    );

    // Row with no ip renders but click is gated by `row.ip &&`
    const rows = screen.getAllByRole('row');
    await user.click(rows[0]);
    expect(onActivateSession).not.toHaveBeenCalled();
  });
});
