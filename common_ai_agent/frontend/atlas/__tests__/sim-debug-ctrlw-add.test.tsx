import React from 'react';
import { cleanup, fireEvent, render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '../debug-shared';
import { SimDebug } from '../sim-debug';

type AnyWindow = typeof window & Record<string, any>;

const jsonResponse = (body: unknown) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });

const makeVcdData = () => {
  const filler = Array.from({ length: 24 }, (_, i) => ({
    id: `f${i}`,
    name: `filler_${i}`,
    signalName: `filler_${i}`,
    scope: 'demo_tb.u_fill',
    range: '',
    isBus: false,
  }));
  const scoped = [
    { id: 'clk_dut', name: 'clk', signalName: 'clk', scope: 'demo_tb.u_dut', range: '', isBus: false },
    { id: 'clk_other', name: 'clk', signalName: 'clk', scope: 'demo_tb.u_other', range: '', isBus: false },
    { id: 'rst_dut', name: 'rst', signalName: 'rst', scope: 'demo_tb.u_dut', range: '', isBus: false },
    { id: 'rst_other', name: 'rst', signalName: 'rst', scope: 'demo_tb.u_other', range: '', isBus: false },
    { id: 'irq_dut', name: 'irq', signalName: 'irq', scope: 'demo_tb.u_dut', range: '', isBus: false },
    { id: 'irq_other', name: 'irq', signalName: 'irq', scope: 'demo_tb.u_other', range: '', isBus: false },
    { id: 'awaddr', name: 's_axi_awaddr', signalName: 's_axi_awaddr', scope: 'demo_tb.u_dut', range: '[31:0]', isBus: true },
  ];
  const signals = [...filler, ...scoped];
  const samples = Object.fromEntries(signals.map((sig, i) => [sig.id, [[0, String(i % 2)], [100, String((i + 1) % 2)]]]));
  return { timescale: '1ns', timeRange: [0, 100], signals, samples };
};

const hierarchyPayload = {
  backend: 'pyslang',
  resolved_top: 'demo_top',
  tree: { name: 'demo_tb.u_dut', module: 'demo_top', children: [] },
  module_files: { demo_top: { file: 'demo_ip/rtl/demo_top.sv', line: 1 } },
};

const moduleSignalsPayload = {
  instance_path: 'demo_tb.u_dut',
  signals: [
    { name: 'clk', direction: 'in', type: 'logic', width: 1, file_line: 'demo_ip/rtl/demo_top.sv:2' },
    { name: 'rst', direction: 'in', type: 'logic', width: 1, file_line: 'demo_ip/rtl/demo_top.sv:3' },
    { name: 'irq', direction: 'out', type: 'logic', width: 1, file_line: 'demo_ip/rtl/demo_top.sv:4' },
    { name: 's_axi_awaddr', direction: 'in', type: 'logic', width: 32, file_line: 'demo_ip/rtl/demo_top.sv:5' },
    { name: 'internal_debug_bus', direction: 'internal', type: 'logic', width: 16, file_line: 'demo_ip/rtl/demo_top.sv:6' },
  ],
};

const installStubs = () => {
  const w = window as AnyWindow;
  w.ACTIVE_IP = 'demo_ip';
  w.ACTIVE_SESSION = 'workspace/demo_ip/sim_debug';
  w.CONTEXT = { active_ip: 'demo_ip' };
  w.backend = { subscribe: vi.fn(() => () => {}) };
  w.parseVCD = vi.fn(() => makeVcdData());

  globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.startsWith('/api/vcd/list')) {
      return jsonResponse({ files: [{ path: 'demo_ip/sim/demo_ip.vcd' }] });
    }
    if (url.startsWith('/api/vcd/raw')) {
      return jsonResponse({ content: '$date test $end' });
    }
    if (url.startsWith('/api/hierarchy')) {
      return jsonResponse(hierarchyPayload);
    }
    if (url.startsWith('/api/source')) {
      return jsonResponse({
        lines: [
          'module demo_top;',
          '  input logic clk, rst, irq;',
          '  input logic [31:0] s_axi_awaddr;',
          '  logic [15:0] internal_debug_bus;',
          'endmodule',
        ],
      });
    }
    if (url.startsWith('/api/module/signals')) {
      return jsonResponse(moduleSignalsPayload);
    }
    if (url.startsWith('/api/vcd/rc/list')) {
      return jsonResponse({ files: [] });
    }
    if (url.startsWith('/api/sim_debug/intent')) {
      return jsonResponse({});
    }
    return jsonResponse({});
  }) as unknown as typeof fetch;
};

const waveNames = (container: HTMLElement) =>
  Array.from(container.querySelectorAll('.wave-panel .wave-name'))
    .map(el => el.textContent || '');

const findHierarchyModule = (container: HTMLElement) =>
  Array.from(container.querySelectorAll<HTMLElement>('[title="open module source"]'))
    .find(el => el.textContent === 'demo_top');

const findSignalPaletteRow = (container: HTMLElement, name: string) =>
  Array.from(container.querySelectorAll<HTMLElement>('div[title*="click to focus"]'))
    .find(el => !el.closest('.wave-panel') && el.textContent?.includes(name));

const installSourceDragCaret = (container: HTMLElement) => {
  const code = Array.from(container.querySelectorAll<HTMLElement>('[data-src-code]'))
    .find(el => el.textContent?.includes('clk, rst, irq'));
  expect(code).toBeTruthy();
  const textNode = code!.firstChild as Text;
  const text = textNode.textContent || '';
  Object.defineProperty(document, 'caretRangeFromPoint', {
    configurable: true,
    value: vi.fn((x: number) => {
      const range = document.createRange();
      range.setStart(textNode, x < 50 ? 0 : text.length);
      return range;
    }),
  });
};

const installSourceLineDragCaret = (container: HTMLElement, needle: string) => {
  const code = Array.from(container.querySelectorAll<HTMLElement>('[data-src-code]'))
    .find(el => el.textContent?.includes(needle));
  expect(code).toBeTruthy();
  const textNode = code!.firstChild as Text;
  const text = textNode.textContent || '';
  Object.defineProperty(document, 'caretRangeFromPoint', {
    configurable: true,
    value: vi.fn((x: number) => {
      const range = document.createRange();
      range.setStart(textNode, x < 50 ? 0 : text.length);
      return range;
    }),
  });
};

const openModuleSignals = async (container: HTMLElement) => {
  await waitFor(() => expect(waveNames(container).some(name => name.includes('filler_0'))).toBe(true));
  await waitFor(() => expect(findHierarchyModule(container)).toBeTruthy());
  fireEvent.click(findHierarchyModule(container)!);
  await waitFor(() => expect(findSignalPaletteRow(container, 'clk')).toBeTruthy());
  await waitFor(() => {
    const sourceLines = Array.from(container.querySelectorAll<HTMLElement>('[data-src-code]'));
    expect(sourceLines.some(el => el.textContent?.includes('clk, rst, irq'))).toBe(true);
  });
};

const expectResolvedWaveSignal = async (container: HTMLElement, name: string) => {
  await waitFor(() => {
    const matches = waveNames(container).filter(row => row.includes(name));
    expect(matches.some(row => !row.includes('not in VCD'))).toBe(true);
    expect(matches.some(row => row.includes('not in VCD'))).toBe(false);
  });
};

describe('SimDebug Ctrl+W signal add', () => {
  beforeEach(async () => {
    installStubs();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    const w = window as AnyWindow;
    delete w.ACTIVE_IP;
    delete w.ACTIVE_SESSION;
    delete w.CONTEXT;
    delete w.backend;
    delete w.parseVCD;
    Reflect.deleteProperty(document, 'caretRangeFromPoint');
  });

  it('shows waveform signals in the signal palette by default', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);

    await waitFor(() => expect(findSignalPaletteRow(container, 'filler_0')).toBeTruthy());
    expect(container.textContent).not.toContain('Click a module in the hierarchy above to list its signals.');
  });

  it('adds the focused RTL signal with its instance scope', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);

    await openModuleSignals(container);

    fireEvent.click(findSignalPaletteRow(container, 'clk')!);
    await waitFor(() => expect(container.textContent).toContain('1 selected'));
    fireEvent.keyDown(window, { key: 'w', ctrlKey: true });

    await expectResolvedWaveSignal(container, 'clk');
  });

  it('adds all Ctrl-selected RTL signals with their instance scope', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);

    await openModuleSignals(container);

    for (const name of ['rst', 'irq']) {
      const row = findSignalPaletteRow(container, name)!;
      fireEvent.mouseDown(row, { button: 0, ctrlKey: true });
      fireEvent.click(row, { button: 0, ctrlKey: true });
    }
    await waitFor(() => expect(container.textContent).toContain('2 selected'));
    fireEvent.keyDown(window, { key: 'w', ctrlKey: true });

    await expectResolvedWaveSignal(container, 'rst');
    await expectResolvedWaveSignal(container, 'irq');
  });

  it('adds source-dragged signals with Ctrl+W', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);

    await openModuleSignals(container);
    installSourceDragCaret(container);

    const viewer = container.querySelector('.src-viewer')!;
    fireEvent.mouseDown(viewer, { button: 0, clientX: 1, clientY: 10 });
    fireEvent.mouseMove(window, { clientX: 100, clientY: 10 });
    fireEvent.mouseUp(window, { clientX: 100, clientY: 10 });

    await waitFor(() => expect(container.textContent).toContain('3 selected'));
    fireEvent.keyDown(window, { key: 'w', ctrlKey: true });

    await expectResolvedWaveSignal(container, 'clk');
    await expectResolvedWaveSignal(container, 'rst');
    await expectResolvedWaveSignal(container, 'irq');
  });

  it('adds source-dragged signals when released over the waveform (drag & drop)', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);

    await openModuleSignals(container);
    installSourceDragCaret(container);

    // Drop target detection uses document.elementFromPoint (absent in jsdom) —
    // mock it to report the release landed inside the wave panel.
    const wavePanel = container.querySelector('.wave-panel')!;
    const orig = (document as unknown as { elementFromPoint?: unknown }).elementFromPoint;
    (document as unknown as { elementFromPoint: unknown }).elementFromPoint = vi.fn(() => wavePanel);
    try {
      const viewer = container.querySelector('.src-viewer')!;
      fireEvent.mouseDown(viewer, { button: 0, clientX: 1, clientY: 10 });
      fireEvent.mouseMove(window, { clientX: 100, clientY: 10 });
      // Released over the waveform → signals are ADDED without Ctrl+W.
      fireEvent.mouseUp(window, { clientX: 100, clientY: 400 });

      await expectResolvedWaveSignal(container, 'clk');
      await expectResolvedWaveSignal(container, 'rst');
      await expectResolvedWaveSignal(container, 'irq');
    } finally {
      (document as unknown as { elementFromPoint?: unknown }).elementFromPoint = orig;
    }
  });

  it('grabbing a single source identifier and dropping on the wave adds just it', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);
    await openModuleSignals(container);

    // caret always resolves to "clk" in the ports line (the grabbed token).
    const code = Array.from(container.querySelectorAll<HTMLElement>('[data-src-code]'))
      .find(el => el.textContent?.includes('clk, rst, irq'))!;
    const textNode = code.firstChild as Text;
    const clkOffset = (textNode.textContent || '').indexOf('clk');
    Object.defineProperty(document, 'caretRangeFromPoint', {
      configurable: true,
      value: vi.fn(() => { const r = document.createRange(); r.setStart(textNode, clkOffset); return r; }),
    });

    const wavePanel = container.querySelector('.wave-panel')!;
    const orig = (document as unknown as { elementFromPoint?: unknown }).elementFromPoint;
    (document as unknown as { elementFromPoint: unknown }).elementFromPoint = vi.fn(() => wavePanel);
    try {
      const viewer = container.querySelector('.src-viewer')!;
      // vertical grab-and-drop: press on clk, drag straight down onto the wave
      fireEvent.mouseDown(viewer, { button: 0, clientX: 120, clientY: 10 });
      fireEvent.mouseMove(window, { clientX: 120, clientY: 200 });
      fireEvent.mouseUp(window, { clientX: 120, clientY: 400 });
      await expectResolvedWaveSignal(container, 'clk');
    } finally {
      (document as unknown as { elementFromPoint?: unknown }).elementFromPoint = orig;
    }
  });

  it('dropping a waveform signal on the source jumps to it (reverse drag)', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);
    await openModuleSignals(container);

    const viewer = container.querySelector('.src-viewer')!;
    const dataTransfer = {
      types: ['application/x-sim-signal-jump'],
      getData: (t: string) =>
        t === 'application/x-sim-signal-jump'
          ? JSON.stringify({ name: 'irq', scope: 'demo_tb.u_dut' })
          : '',
      dropEffect: '',
    };
    fireEvent.drop(viewer, { dataTransfer });

    // the source jumps by tracing the dropped signal's driver
    await waitFor(() =>
      expect(
        (globalThis.fetch as unknown as { mock: { calls: unknown[][] } }).mock.calls.some(
          c => String(c[0]).startsWith('/api/trace') && String(c[0]).includes('signal=irq'),
        ),
      ).toBe(true),
    );
  });

  it('adds source-dragged bus declarations with their RTL width range', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);

    await openModuleSignals(container);
    installSourceLineDragCaret(container, 's_axi_awaddr');

    const viewer = container.querySelector('.src-viewer')!;
    fireEvent.mouseDown(viewer, { button: 0, clientX: 1, clientY: 48 });
    fireEvent.mouseMove(window, { clientX: 220, clientY: 48 });
    fireEvent.mouseUp(window, { clientX: 220, clientY: 48 });

    await waitFor(() => expect(container.textContent).toContain('1 selected'));
    fireEvent.keyDown(window, { key: 'w', ctrlKey: true });

    await expectResolvedWaveSignal(container, 's_axi_awaddr[31:0]');
  });

  it('keeps source-dragged missing bus declarations visibly multi-bit', async () => {
    const { container } = render(<SimDebug view="debug" initialTab="wave" active />);

    await openModuleSignals(container);
    installSourceLineDragCaret(container, 'internal_debug_bus');

    const viewer = container.querySelector('.src-viewer')!;
    fireEvent.mouseDown(viewer, { button: 0, clientX: 1, clientY: 66 });
    fireEvent.mouseMove(window, { clientX: 240, clientY: 66 });
    fireEvent.mouseUp(window, { clientX: 240, clientY: 66 });

    await waitFor(() => expect(container.textContent).toContain('1 selected'));
    fireEvent.keyDown(window, { key: 'w', ctrlKey: true });

    await waitFor(() => expect(waveNames(container).some(row =>
      row.includes('internal_debug_bus[15:0]') && row.includes('not in VCD'))).toBe(true));
  });
});
