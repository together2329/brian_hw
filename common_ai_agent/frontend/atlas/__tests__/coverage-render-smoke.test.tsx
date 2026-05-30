import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/react';

describe('Coverage render smoke', () => {
  beforeEach(() => {
    const w = window as unknown as Record<string, unknown>;
    w.ACTIVE_SESSION = 'default/NEWIP_MCTP/coverage';
    w.SCOPE_PATH = 'NEWIP_MCTP';
    w.normalizeAtlasSessionName = (v: unknown) => String(v || '').trim();
    global.fetch = vi.fn(async () =>
      new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
    ) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('mounts the real Coverage panel without undefined component crashes', async () => {
    const { Coverage } = await import('../coverage.tsx');

    expect(typeof Coverage).toBe('function');
    expect(() => render(<Coverage />)).not.toThrow();
  });
});
