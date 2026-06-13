import React from 'react';
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { WaveRow } from '../debug-shared';
import {
  buildWaveDisplayRows,
  buildWaveTraceList,
  formatFrequencyFromDelta,
  formatTimeDeltaDisplay,
  parseVerilogParamValueMap,
  parseWaveCommand,
  removedSignalsAfterReAdd,
  reorderWaveKeys,
  resolveTimeDisplayUnit,
  sourceLineIdentifiers,
  waveSignalKey,
  type VcdSignal,
} from '../sim-debug-helpers';

const scalar = (name: string, scope = 'tb.dut', id = name): VcdSignal => ({
  id,
  name,
  scope,
  range: '',
  isBus: false,
});

const bus = (name: string, range: string, scope = 'tb.dut', id = name): VcdSignal => ({
  id,
  name,
  scope,
  range,
  isBus: true,
});

const traceRow = (name: string, scope = 'tb.dut'): VcdSignal => ({
  name,
  signalName: name,
  scope,
  range: '',
  trace: [[0, '0'], [10, '1']],
  isBus: false,
});

describe('sim debug signal requirements', () => {
  beforeEach(() => {
    window.WAVE_TIME_START = 0;
    window.WAVE_TIME_END = 100;
  });

  it('SDR-007 SDR-014 keeps exact bus slices independent from the full VCD bus', () => {
    const rows = buildWaveTraceList(
      {
        signals: [bus('irq_status_o', '[31:0]', 'tb.dut.u_irq', 'irq')],
        samples: {
          irq: [[0, '1011'], [10, '001011'], [20, '100000']],
        },
      },
      [
        { name: 'irq_status_o[5:0]', scope: 'tb.dut.u_irq' },
        { name: 'irq_status_o[31:6]', scope: 'tb.dut.u_irq' },
        { name: 'irq_status_o[31:0]', scope: 'tb.dut.u_irq' },
      ],
      0,
    );

    expect(rows.map(row => row.name)).toEqual([
      'irq_status_o[5:0]',
      'irq_status_o[31:6]',
      'irq_status_o[31:0]',
    ]);
    expect(rows[0].trace).toEqual([[0, '001011'], [20, '100000']]);
    expect(rows[1].trace).toEqual([[0, '00000000000000000000000000']]);
    expect(rows[2].trace).toEqual([[0, '1011'], [10, '001011'], [20, '100000']]);
  });

  it('SDR-020 keeps missing VCD bus placeholders visibly ranged and bus-typed', () => {
    const rows = buildWaveTraceList(
      {
        signals: [scalar('clk', 'tb.dut', 'clk')],
        samples: { clk: [[0, '0']] },
      },
      [{ name: 'internal_debug_bus[15:0]', scope: 'tb.dut' }],
      0,
    );

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      name: 'internal_debug_bus[15:0]',
      signalName: 'internal_debug_bus',
      scope: 'tb.dut',
      range: '[15:0]',
      isBus: true,
      radix: 'HEX',
      notInVcd: true,
    });
  });

  it('SDR-007 SDR-014 keeps single-bit selects scalar instead of widening to the full bus', () => {
    const rows = buildWaveTraceList(
      {
        signals: [bus('irq_status_o', '[3:0]', 'tb.dut.u_irq', 'irq')],
        samples: { irq: [[0, '1010'], [10, '1011']] },
      },
      [{ name: 'irq_status_o[0]', scope: 'tb.dut.u_irq' }],
      0,
    );

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      name: 'irq_status_o[0]',
      signalName: 'irq_status_o',
      range: '[0]',
      isBus: false,
    });
    expect(rows[0].trace).toEqual([[0, '0'], [10, '1']]);
  });

  it('SDR-020 SDR-021 SDR-022 SDR-023 resolves only proven VCD signals and marks missing or ambiguous rows', () => {
    const rows = buildWaveTraceList(
      {
        signals: [
          scalar('clk', 'tb.dut.u_a', 'a_clk'),
          scalar('clk', 'tb.dut.u_b', 'b_clk'),
          scalar('rst', 'tb.dut.u_b', 'b_rst'),
          scalar('parse_done', 'mctp_axi.u_pkt_parser', 'done'),
          scalar('ready', 'tb.dut.u_a', 'a_ready'),
          scalar('ready', 'tb.dut.u_b', 'b_ready'),
        ],
        samples: {
          a_clk: [[0, '0']],
          b_clk: [[0, '1']],
          b_rst: [[0, '0']],
          done: [[0, '0'], [10, '1']],
          a_ready: [[0, '1']],
          b_ready: [[0, '0']],
        },
      },
      [
        { name: 'clk', scope: 'dut.u_b' },
        { name: 'rst', scope: 'dut.u_b' },
        { name: 'parse_done', scope: 'pkt_parser' },
        { name: 'internal_debug', scope: 'tb.dut.u_b' },
        { name: 'ready' },
      ],
      0,
    );

    expect(rows.map(row => `${row.scope}.${row.signalName}:${row.notInVcd ? 'missing' : 'vcd'}`)).toEqual([
      'tb.dut.u_b.clk:vcd',
      'tb.dut.u_b.rst:vcd',
      'mctp_axi.u_pkt_parser.parse_done:vcd',
      'tb.dut.u_b.internal_debug:missing',
      '.ready:missing',
    ]);
  });

  it('SDR-008 SDR-009 source multi-select tokenization ignores comments and numeric literal fragments', () => {
    const ids = sourceLineIdentifiers(`
      // payload req_valid req_data should not be selected from comments
      assign irq_status_o[5:0] = req_data[5:0] | 4'd0 | 8'hff;
    `);

    expect(ids).toEqual(['irq_status_o[5:0]', 'req_data[5:0]']);
    expect(ids).not.toContain('payload');
    expect(ids).not.toContain('d0');
    expect(ids).not.toContain('hff');
  });

  it('SDR-008 SDR-009 treats declaration widths as type syntax, not source-selected signals', () => {
    const ids = sourceLineIdentifiers(`
      input logic [31:0] s_axi_awaddr,
      output logic [(AXI_DATA_W/8)-1:0] s_axi_wstrb;
    `);

    expect(ids).toEqual(['s_axi_awaddr', 's_axi_wstrb']);
  });

  it('SDR-015 SDR-016 maps parameter/localparam FSM values and renders PARAM display', () => {
    const valueMap = parseVerilogParamValueMap([
      '// localparam [1:0] COMMENT_ONLY = 2 d0;',
      "localparam [3:0] IDLE = 4'd0, ACCEPT = 4'd1, ERROR = 4'hf;",
      "parameter integer COMPLETE = 4'd8;",
    ]);

    expect(valueMap).toEqual({ 0: 'IDLE', 1: 'ACCEPT', 8: 'COMPLETE', 15: 'ERROR' });

    const view = render(
      <WaveRow
        name="fsm_state[3:0]"
        trace={[[0, '0000'], [20, '1111']]}
        width={160}
        isBus
        radix="PARAM"
        valueMap={valueMap}
      />,
    );

    expect(view.container.querySelector('.wave-val')).toHaveTextContent('ERROR');
    expect(Array.from(view.container.querySelectorAll('.bus-flag-text')).map(el => el.textContent)).toContain('IDLE');
  });

  it('renders scalar and bus transitions on the same snapped pixel grid', () => {
    window.WAVE_TIME_START = 0;
    window.WAVE_TIME_END = 20;
    const scalarView = render(
      <WaveRow
        name="PCLK"
        trace={[[0, '0'], [10, '1']]}
        width={100}
      />,
    );
    const busView = render(
      <WaveRow
        name="PADDR"
        trace={[[0, '0000'], [10, '0100']]}
        width={100}
        isBus
      />,
    );

    const scalarPath = scalarView.container.querySelector('path')?.getAttribute('d') || '';
    const busPoints = Array.from(busView.container.querySelectorAll('polygon'))
      .map(el => el.getAttribute('points') || '')
      .join(' ');
    expect(scalarPath).toContain('50.5');
    expect(busPoints).toContain('50.5');
  });

  it('SDR-013 keeps grouped waveform rows contiguous and reorders group blocks together', () => {
    const rows = [traceRow('a'), traceRow('b'), traceRow('c')];
    const displayRows = buildWaveDisplayRows(
      rows,
      { a: 'grp', c: 'grp' },
      { grp: { folded: false, color: '#ffb84d' } },
    );

    expect(displayRows.map(item => item.type === 'group' ? `group:${item.count}` : item.sig.name)).toEqual([
      'group:2',
      'a',
      'c',
      'b',
    ]);
    expect(buildWaveDisplayRows(rows, { a: 'grp', c: 'grp' }, { grp: { folded: true } })
      .map(item => item.type === 'group' ? `group:${item.count}` : item.sig.name)).toEqual(['group:2', 'b']);

    const ordered = rows.map(waveSignalKey);
    expect(reorderWaveKeys(ordered, [ordered[0], ordered[2]], [ordered[1]], 'after')).toEqual([
      ordered[1],
      ordered[0],
      ordered[2],
    ]);
  });

  it('SDR-018 SDR-019 formats time resolution, cursor delta, frequency, and command-driven input', () => {
    expect(resolveTimeDisplayUnit('1ps', 'auto')).toBe('ps');
    expect(formatTimeDeltaDisplay(1500, 'ps', 'ns')).toBe('1.5ns');
    expect(formatTimeDeltaDisplay(100, 'ns', 'ns')).toBe('100ns');
    expect(formatFrequencyFromDelta(10, 'ns')).toBe('100 MHz');
    expect(parseWaveCommand('a=5000 b=15000')).toEqual({ cursorA: 5000, cursorB: 15000 });
    expect(parseWaveCommand('zoom 1000 8000')).toEqual({ view: [1000, 8000] });
    expect(parseWaveCommand('a..b')).toEqual({ zoomCursors: true });
  });

  it('SDR-020 resolves an ambiguous bus leaf to a real row, not a "not in VCD" placeholder', () => {
    // paddr is dumped under several scopes (a bus fanning tb → dut → sub-block).
    // Adding the bare leaf "paddr" must show a REAL row (top-level scope), not a
    // misleading "⚠ not in VCD" placeholder. Regression for the bus-add bug.
    const rows = buildWaveTraceList(
      {
        signals: [
          bus('paddr', '[7:0]', 'tb.dut', 'paddr_top'),
          bus('paddr', '[7:0]', 'tb.dut.u_reg', 'paddr_sub'),
          scalar('irq', 'tb.dut', 'irq'),
        ],
        samples: {
          paddr_top: [[0, '00000001']],
          paddr_sub: [[0, '00000001']],
          irq: [[0, '1']],
        },
      },
      [{ name: 'paddr', scope: '' }, { name: 'irq', scope: '' }],
      0,  // no default rows — only the pinned signals
    );
    const paddrRow = rows.find(r => (r.name || '').toLowerCase().startsWith('paddr'));
    expect(paddrRow).toBeTruthy();
    expect(paddrRow!.notInVcd).toBeFalsy();        // NOT flagged "not in VCD"
    expect(paddrRow!.scope).toBe('tb.dut');        // top-level scope preferred
    const irqRow = rows.find(r => (r.name || '').toLowerCase() === 'irq');
    expect(irqRow && irqRow.notInVcd).toBeFalsy();
  });

  it('SDR-021 re-adding a removed signal un-hides it even under a different hierarchy', () => {
    // Regression: a signal removed via keep/clear is stored as its VCD row
    // (leaf psel @ apb_timer_pwm_irq_v1). A chat/source re-add arrives fully
    // qualified under the TB hierarchy (tb_apb_timer_pwm_irq_v1.psel). The strict
    // string compare missed that, so "add" did nothing. It must come back.
    const allRows: VcdSignal[] = [
      scalar('psel', 'apb_timer_pwm_irq_v1', 'psel'),
      scalar('irq', 'apb_timer_pwm_irq_v1', 'irq'),
    ];
    const removed = [{ name: 'psel', scope: 'apb_timer_pwm_irq_v1' }];

    // re-add under a DIFFERENT hierarchy -> the psel removal is dropped
    expect(
      removedSignalsAfterReAdd(allRows, removed, [{ name: 'tb_apb_timer_pwm_irq_v1.psel', scope: '' }]),
    ).toEqual([]);

    // re-adding an unrelated signal leaves psel removed
    expect(
      removedSignalsAfterReAdd(allRows, removed, [{ name: 'irq', scope: '' }]),
    ).toEqual(removed);

    // not-in-VCD placeholder is un-removed by the string fallback (no row to resolve)
    const removedPh = [{ name: 'pclk', scope: 'tb' }];
    expect(
      removedSignalsAfterReAdd(allRows, removedPh, [{ name: 'pclk', scope: 'tb' }]),
    ).toEqual([]);
  });
});
