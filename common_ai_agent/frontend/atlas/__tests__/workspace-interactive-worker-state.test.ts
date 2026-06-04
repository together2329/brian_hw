import { describe, expect, it } from 'vitest';

import { interactiveWorkerStatusFromPayload } from '../workspace-interactive-worker-state';

describe('interactiveWorkerStatusFromPayload', () => {
  it('maps an on-demand idle payload without a live worker to evicted instead of failed', () => {
    const status = interactiveWorkerStatusFromPayload({
      policy: 'strict',
      active_count: 0,
      owner: 'alice',
      owner_active_session: 'alice/demo/default',
      worker: null,
    });

    expect(status?.state).toBe('evicted');
    expect(status?.alive).toBe(false);
    expect(status?.running).toBe(false);
  });

  it('keeps an explicit worker failure as failed', () => {
    const status = interactiveWorkerStatusFromPayload({
      policy: 'strict',
      active_count: 1,
      worker: {
        state: 'failed',
        alive: false,
        running: false,
        error: 'worker crashed',
      },
    });

    expect(status?.state).toBe('failed');
    expect(status?.error).toBe('worker crashed');
  });
});
