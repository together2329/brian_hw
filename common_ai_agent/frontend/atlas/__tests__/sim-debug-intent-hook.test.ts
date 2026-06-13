import { describe, expect, it, vi } from 'vitest';
import { applyIntent, shouldApplySimDebugIntent, type SimDebugIntentSeqMap } from '../sim-debug-intent-hook';

const makeDeps = () => ({
  ipName: 'ip_a',
  active: true,
  vcdData: null,
  pinSignalsToWave: vi.fn(),
  setViewRange: vi.fn(),
  setTopTab: vi.fn(),
  setExpand: vi.fn(),
  setWaveCursor: vi.fn(),
  setWaveCursorB: vi.fn(),
  runSignalTrace: vi.fn(),
  zoomFit: vi.fn(),
  reorderByNames: vi.fn(),
  setSignalColorByNames: vi.fn(),
  setSignalRadixByNames: vi.fn(),
  removeSignalsFromWave: vi.fn(),
  keepOnlySignals: vi.fn(),
  clearWaveSignals: vi.fn(),
  assignGroupByNames: vi.fn(),
  ungroupByNames: vi.fn(),
  toggleGroupFold: vi.fn(),
});

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

describe('applyIntent dispatch for chat waveform actions', () => {
  it('radix sets the override; missing radix resets it', () => {
    const d = makeDeps();
    applyIntent(d, { action: 'radix', signals: ['prdata'], radix: 'FSM' });
    expect(d.setSignalRadixByNames).toHaveBeenCalledWith(['prdata'], 'FSM');

    const d2 = makeDeps();
    applyIntent(d2, { action: 'radix', signals: ['prdata'] });   // 'off' => dropped field
    expect(d2.setSignalRadixByNames).toHaveBeenCalledWith(['prdata'], null);
  });

  it('remove drops signals and does NOT re-pin them', () => {
    const d = makeDeps();
    applyIntent(d, { action: 'remove', signals: ['psel'], scope: 'tb' });
    expect(d.removeSignalsFromWave).toHaveBeenCalledTimes(1);
    expect(d.removeSignalsFromWave.mock.calls[0][0]).toEqual([{ name: 'psel', scope: 'tb' }]);
    expect(d.pinSignalsToWave).not.toHaveBeenCalled();
  });

  it('keep isolates the listed signals without auto-pinning them generically', () => {
    const d = makeDeps();
    applyIntent(d, { action: 'keep', signals: ['irq'] });
    expect(d.keepOnlySignals).toHaveBeenCalledTimes(1);
    expect(d.keepOnlySignals.mock.calls[0][0]).toEqual([{ name: 'irq', scope: '' }]);
    expect(d.pinSignalsToWave).not.toHaveBeenCalled();  // keepOnlySignals pins internally
  });

  it('clear removes everything', () => {
    const d = makeDeps();
    applyIntent(d, { action: 'clear' });
    expect(d.clearWaveSignals).toHaveBeenCalledTimes(1);
  });

  it('show still auto-pins the requested signals', () => {
    const d = makeDeps();
    applyIntent(d, { action: 'show', signals: ['clk'] });
    expect(d.pinSignalsToWave).toHaveBeenCalledTimes(1);
  });
});
