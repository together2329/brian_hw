import { describe, expect, it } from 'vitest';

import {
  initialWorkflow,
  mergePolicyResponse,
  normalizeExecMode,
  policyFromBootConfig,
  preserveRunning,
} from '../lib/exec_policy.mjs';

describe('Atlas exec policy helper', () => {
  it('normalizes UI shorthands to backend exec modes', () => {
    expect(normalizeExecMode('s')).toBe('single-worker');
    expect(normalizeExecMode('single worker')).toBe('single-worker');
    expect(normalizeExecMode('o')).toBe('orchestrator');
    expect(normalizeExecMode('multi_worker')).toBe('orchestrator');
  });

  it('derives new-IP workflow and preservation from boot policy', () => {
    const single = policyFromBootConfig({ exec_mode: 'single-worker' });
    expect(initialWorkflow(single)).toBe('ssot-gen');
    expect(preserveRunning(single)).toBe(false);

    const orchestrator = policyFromBootConfig({
      exec_policy: {
        exec_mode: 'orchestrator',
        initial_workflow: 'orchestrator',
        preserve_running_on_workflow_switch: true,
      },
    });
    expect(initialWorkflow(orchestrator)).toBe('orchestrator');
    expect(preserveRunning(orchestrator)).toBe(true);
  });

  it('merges run-policy responses into boot config', () => {
    const config = { exec_mode: 'single-worker' };
    mergePolicyResponse(config, {
      exec_mode: 'orchestrator',
      policy: {
        exec_mode: 'orchestrator',
        initial_workflow: 'orchestrator',
      },
    });

    expect(config.exec_mode).toBe('orchestrator');
    expect(config.exec_policy.initial_workflow).toBe('orchestrator');
  });
});
