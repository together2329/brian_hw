/**
 * Snapshot / behavior test for the "Select an IP" warning banner.
 *
 * The banner renders inside workspace.jsx's renderPromptRow() when:
 *   workflow === 'orchestrator' && (!activeIp || activeIp.toLowerCase() === 'default')
 *
 * Decision logic is imported from lib/banner_logic.js (shared with browser via
 * window.AtlasBannerLogic UMD shim), so drift between tests and source is caught.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { shouldShowSelectIpBanner, BANNER_TITLE, BANNER_DETAIL } from '../lib/banner_logic.js';

function OrchestratorIpBanner({ workflow, activeIp }) {
  const orchestratorIdle = shouldShowSelectIpBanner({ workflow, activeIp });

  if (!orchestratorIdle) return null;

  return (
    <div
      data-testid="ip-banner"
      title="The orchestrator needs a real IP to know what to work on. The placeholder 'default' carries no SSOT/RTL data so it loops back without dispatching."
    >
      <span style={{ fontWeight: 700 }}>{BANNER_TITLE}</span>
      <span>
        {BANNER_DETAIL}
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
