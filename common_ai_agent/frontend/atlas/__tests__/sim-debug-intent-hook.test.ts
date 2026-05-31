import { describe, expect, it } from 'vitest';
import { shouldApplySimDebugIntent, type SimDebugIntentSeqMap } from '../sim-debug-intent-hook';

describe('sim debug intent polling decisions', () => {
  it('does not consume another IP intent before switching to that IP', () => {
    const seen: SimDebugIntentSeqMap = {};
    const intent = { seq: 10, ip: 'ip_b', action: 'show', signals: ['clk'] };

    expect(shouldApplySimDebugIntent('ip_a', intent, seen)).toEqual({
      apply: false,
      key: 'ip_b',
      seq: 10,
    });
    expect(seen).toEqual({});

    const hit = shouldApplySimDebugIntent('ip_b', intent, seen);
    expect(hit).toEqual({ apply: true, key: 'ip_b', seq: 10 });
    seen[hit.key] = hit.seq;

    expect(shouldApplySimDebugIntent('ip_b', intent, seen).apply).toBe(false);
  });

  it('applies blank-IP intents once globally', () => {
    const seen: SimDebugIntentSeqMap = {};
    const intent = { seq: 20, action: 'fit' };

    const first = shouldApplySimDebugIntent('ip_a', intent, seen);
    expect(first).toEqual({ apply: true, key: '*', seq: 20 });
    seen[first.key] = first.seq;

    expect(shouldApplySimDebugIntent('ip_a', intent, seen).apply).toBe(false);
    expect(shouldApplySimDebugIntent('ip_b', intent, seen).apply).toBe(false);
  });
});
