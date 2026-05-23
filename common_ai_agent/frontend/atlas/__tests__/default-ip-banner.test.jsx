/**
 * Snapshot / behavior test for the "Select an IP" warning banner.
 *
 * The banner renders inside workspace.jsx's renderPromptRow() when:
 *   workflow === 'orchestrator' && (!activeIp || activeIp.toLowerCase() === 'default')
 *
 * Because workspace.jsx is a 16k-line browser-globals script (no ES exports),
 * we inline the minimal component that reproduces the exact conditional logic
 * from lines 3782-3804 of workspace.jsx. The production code is not modified.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

// Minimal reproduction of workspace.jsx renderPromptRow() banner logic (lines 3782-3804)
function OrchestratorIpBanner({ workflow, activeIp }) {
  const orchestratorIdle =
    workflow === 'orchestrator' &&
    (!activeIp || String(activeIp).toLowerCase() === 'default');

  if (!orchestratorIdle) return null;

  return (
    <div
      data-testid="ip-banner"
      title="The orchestrator needs a real IP to know what to work on. The placeholder 'default' carries no SSOT/RTL data so it loops back without dispatching."
    >
      <span style={{ fontWeight: 700 }}>⚠ Select an IP</span>
      <span>
        orchestrator needs a real IP — pick one from the IP_ID dropdown or click{' '}
        <b>+ IP</b> at the top to create one. Messages with <code>default</code> are
        rejected.
      </span>
    </div>
  );
}

describe('OrchestratorIpBanner', () => {
  it('shows "Select an IP" when workflow=orchestrator and activeIp=default', () => {
    render(<OrchestratorIpBanner workflow="orchestrator" activeIp="default" />);
    expect(screen.getByText('⚠ Select an IP')).toBeInTheDocument();
  });

  it('shows banner when activeIp is empty string', () => {
    render(<OrchestratorIpBanner workflow="orchestrator" activeIp="" />);
    expect(screen.getByTestId('ip-banner')).toBeInTheDocument();
  });

  it('hides banner when workflow is not orchestrator', () => {
    render(<OrchestratorIpBanner workflow="rtl-gen" activeIp="default" />);
    expect(screen.queryByTestId('ip-banner')).not.toBeInTheDocument();
  });

  it('hides banner when activeIp is a real IP', () => {
    render(<OrchestratorIpBanner workflow="orchestrator" activeIp="uart_v2" />);
    expect(screen.queryByTestId('ip-banner')).not.toBeInTheDocument();
  });
});
