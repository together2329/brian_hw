import React from 'react';
import { afterEach, beforeAll, describe, expect, it } from 'vitest';

describe('sim debug VCD scoping and annotations', () => {
  beforeAll(async () => {
    globalThis.React = React;
    await import('../sim-debug-helpers.tsx?sim-debug-vcd-scope-annotation-test');
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

  it('keeps a pinned bus slice distinct from the full VCD bus', () => {
    const signals = [
      { id: 'irq', name: 'irq_status_o', scope: 'tb.dut', range: '[31:0]', isBus: true },
    ];
    const rows = window.simDebugBuildWaveTraceList(
      { signals, samples: { irq: [[0, '00000000000000000000000000101011'], [10, '00000000000000000000000000111100']] } },
      [{ name: 'irq_status_o[5:0]', scope: 'tb.dut' }],
      0,
    );

    expect(rows).toHaveLength(1);
    expect(rows[0].name).toBe('irq_status_o[5:0]');
    expect(rows[0].range).toBe('[5:0]');
    expect(rows[0].trace).toEqual([[0, '101011'], [10, '111100']]);
  });

  it('zero-extends short VCD bus values before slicing upper bits', () => {
    const signals = [
      { id: 'irq', name: 'irq_status_o', scope: 'tb.dut', range: '[31:0]', isBus: true },
    ];
    const rows = window.simDebugBuildWaveTraceList(
      { signals, samples: { irq: [[0, '1011'], [10, '1']] } },
      [
        { name: 'irq_status_o[5:0]', scope: 'tb.dut' },
        { name: 'irq_status_o[31:6]', scope: 'tb.dut' },
      ],
      0,
    );

    expect(rows.map(r => r.name)).toEqual(['irq_status_o[5:0]', 'irq_status_o[31:6]']);
    expect(rows[0].trace).toEqual([[0, '001011'], [10, '000001']]);
    expect(rows[1].trace).toEqual([[0, '00000000000000000000000000']]);
  });

  it('extracts localparam and parameter numeric labels for FSM display', () => {
    expect(window.simDebugParseVerilogParamValueMap([
      "localparam logic [1:0] S_IDLE = 2'b00, S_RUN = 2'b01;",
      "parameter integer S_DONE = 2'd2;",
    ])).toEqual({ 0: 'S_IDLE', 1: 'S_RUN', 2: 'S_DONE' });
  });

  it('reorders one waveform signal before or after another', () => {
    expect(window.simDebugReorderWaveKeys(['a', 'b', 'c', 'd'], ['c'], ['a'], 'before'))
      .toEqual(['c', 'a', 'b', 'd']);
    expect(window.simDebugReorderWaveKeys(['a', 'b', 'c', 'd'], ['a'], ['c'], 'after'))
      .toEqual(['b', 'c', 'a', 'd']);
  });

  it('reorders a waveform group as one contiguous block', () => {
    expect(window.simDebugReorderWaveKeys(['a', 'g1', 'g2', 'b', 'c'], ['g1', 'g2'], ['c'], 'after'))
      .toEqual(['a', 'b', 'c', 'g1', 'g2']);
    expect(window.simDebugReorderWaveKeys(['a', 'b', 'g1', 'g2', 'c'], ['c'], ['g1', 'g2'], 'before'))
      .toEqual(['a', 'b', 'c', 'g1', 'g2']);
  });

  it('resolves tool-added waveform pins with a missing VCD top prefix', () => {
    const signals = [
      { id: 'done', name: 'done', scope: 'tb.dut.u_core', range: '', isBus: false },
    ];
    const rows = window.simDebugBuildWaveTraceList(
      { signals, samples: { done: [[0, '1']] } },
      [{ name: 'u_core.done', scope: '' }],
      0,
    );

    expect(rows).toHaveLength(1);
    expect(rows[0].notInVcd).toBeFalsy();
    expect(rows[0].scope).toBe('tb.dut.u_core');
    expect(rows[0].signalName).toBe('done');
  });

  it('resolves scoped pins when the passed scope omits the VCD testbench prefix', () => {
    const signals = [
      { id: 'done', name: 'done', scope: 'tb.dut.u_core', range: '', isBus: false },
    ];
    const rows = window.simDebugBuildWaveTraceList(
      { signals, samples: { done: [[0, '1']] } },
      [{ name: 'done', scope: 'dut.u_core' }],
      0,
    );

    expect(rows).toHaveLength(1);
    expect(rows[0].notInVcd).toBeFalsy();
    expect(rows[0].scope).toBe('tb.dut.u_core');
  });

  it('resolves common source port pins with the current RTL instance scope', () => {
    const signals = [
      { id: 'a_clk', name: 'clk', scope: 'tb.dut.u_a', range: '', isBus: false },
      { id: 'b_clk', name: 'clk', scope: 'tb.dut.u_b', range: '', isBus: false },
      { id: 'b_rst', name: 'rst', scope: 'tb.dut.u_b', range: '', isBus: false },
      { id: 'b_irq', name: 'irq', scope: 'tb.dut.u_b', range: '', isBus: false },
    ];
    const samples = {
      a_clk: [[0, '0']],
      b_clk: [[0, '1']],
      b_rst: [[0, '0']],
      b_irq: [[0, '1']],
    };
    const rows = window.simDebugBuildWaveTraceList(
      { signals, samples },
      [
        { name: 'clk', scope: 'dut.u_b' },
        { name: 'rst', scope: 'dut.u_b' },
        { name: 'irq', scope: 'dut.u_b' },
      ],
      0,
    );

    expect(rows.map(r => `${r.scope}.${r.signalName}`)).toEqual([
      'tb.dut.u_b.clk',
      'tb.dut.u_b.rst',
      'tb.dut.u_b.irq',
    ]);
    expect(rows.every(r => !r.notInVcd)).toBe(true);
  });

  it('resolves module-style pins through a unique VCD leaf fallback', () => {
    const signals = [
      { id: 'ready', name: 'w_ready_o', scope: 'tb.dut.u_packet_engine', range: '', isBus: false },
    ];
    const rows = window.simDebugBuildWaveTraceList(
      { signals, samples: { ready: [[0, '0']] } },
      [{ name: 'NEWIP_MCTP_packet_engine.w_ready_o', scope: '' }],
      0,
    );

    expect(rows).toHaveLength(1);
    expect(rows[0].notInVcd).toBeFalsy();
    expect(rows[0].scope).toBe('tb.dut.u_packet_engine');
    expect(rows[0].signalName).toBe('w_ready_o');
  });

  it('keeps ambiguous leaf-only tool pins unresolved instead of guessing', () => {
    const signals = [
      { id: 'a', name: 'done', scope: 'tb.dut.u_a', range: '', isBus: false },
      { id: 'b', name: 'done', scope: 'tb.dut.u_b', range: '', isBus: false },
    ];
    const rows = window.simDebugBuildWaveTraceList(
      { signals, samples: { a: [[0, '0']], b: [[0, '1']] } },
      [{ name: 'module.done', scope: '' }],
      0,
    );

    expect(rows).toHaveLength(1);
    expect(rows[0].notInVcd).toBe(true);
    expect(rows[0].name).toBe('done');
  });
});
