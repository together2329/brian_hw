import { afterEach, describe, expect, it } from 'vitest';

import { activeIpFromAtlasRuntime } from '../sim-debug-helpers';

describe('sim debug active IP resolution', () => {
  afterEach(() => {
    const w = window as any;
    delete w.ACTIVE_IP;
    delete w.ACTIVE_SESSION;
    delete w.CONTEXT;
  });

  it('reads the IP segment from user/workspace/ip/workflow sessions', () => {
    const w = window as any;
    w.ACTIVE_SESSION = 'alice/s1/demo_ip/sim';

    expect(activeIpFromAtlasRuntime()).toBe('demo_ip');
  });
});
