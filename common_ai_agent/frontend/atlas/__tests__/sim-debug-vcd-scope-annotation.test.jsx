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
});
