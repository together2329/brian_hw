import React from 'react';
import { afterEach, beforeAll, describe, expect, it } from 'vitest';

describe('sim debug VCD scoping and annotations', () => {
  beforeAll(async () => {
    globalThis.React = React;
    await import('../sim-debug.jsx?sim-debug-vcd-scope-annotation-test');
  });

  afterEach(() => {
    delete window.ACTIVE_IP;
    delete window.ACTIVE_SESSION;
    delete window.CONTEXT;
  });

  it('keeps VCD picker entries scoped to the active IP', () => {
    expect(window.simDebugVcdPathBelongsToIp('new_axi/sim/tb_minimal.vcd', 'new_axi')).toBe(true);
    expect(window.simDebugVcdPathBelongsToIp('new_axi/sim/cocotb_build/new_axi.vcd', 'new_axi')).toBe(true);
    expect(window.simDebugVcdPathBelongsToIp('mctp_axi/sim/mctp_axi.vcd', 'new_axi')).toBe(false);
  });

  it('resolves the active IP from the live Atlas runtime first', () => {
    window.ACTIVE_SESSION = 'happy2/old_axi/sim_debug';
    window.ACTIVE_IP = 'new_axi';
    expect(window.simDebugActiveIpFromAtlasRuntime()).toBe('new_axi');

    delete window.ACTIVE_IP;
    expect(window.simDebugActiveIpFromAtlasRuntime()).toBe('old_axi');
  });

  it('builds source-line VCD value annotations for A and B cursors', () => {
    const traceList = [
      { name: 'mosi', signalName: 'mosi', trace: [[0, '0'], [10, '1'], [20, '0']], isBus: false },
      { name: 'shift_reg[7:0]', signalName: 'shift_reg', trace: [[0, '00000000'], [10, '10100101']], isBus: true },
    ];

    const items = window.simDebugBuildVcdLineAnnotations({
      line: 'assign mosi = shift_reg[7];',
      traceList,
      selectedSig: 'mosi',
      cursorA: 5,
      cursorB: 15,
    });

    expect(items).toEqual([
      { name: 'mosi', a: '0', b: '1' },
      { name: 'shift_reg[7:0]', a: '0x0', b: '0xA5' },
    ]);
  });

  it('selects which VCD annotation cursor axes are shown in the source viewer', () => {
    expect(window.simDebugAnnotationAxesForMode('a').map(axis => axis.label)).toEqual(['A']);
    expect(window.simDebugAnnotationAxesForMode('b').map(axis => axis.label)).toEqual(['B']);
    expect(window.simDebugAnnotationAxesForMode('both').map(axis => axis.label)).toEqual(['A', 'B']);
    expect(window.simDebugAnnotationAxesForMode('unknown').map(axis => axis.label)).toEqual(['A', 'B']);
  });

  it('adds pinned signals beyond the default waveform slice', () => {
    const signals = Array.from({ length: 30 }, (_, i) => ({
      id: `s${i}`,
      name: `sig_${i}`,
      scope: 'tb.dut',
      range: '',
      isBus: false,
    }));
    const samples = Object.fromEntries(signals.map(s => [s.id, [[0, '0']]]));
    const rows = window.simDebugBuildWaveTraceList(
      { signals, samples },
      [{ name: 'sig_29', scope: 'tb.dut' }],
      24,
    );

    expect(rows).toHaveLength(25);
    expect(rows.map(r => r.signalName)).toContain('sig_29');
    expect(rows.filter(r => r.signalName === 'sig_2')).toHaveLength(1);
  });
});
