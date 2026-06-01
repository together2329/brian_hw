import React from 'react';
import { fireEvent, render } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SourceViewer } from '../sim-debug-panels';

describe('sim debug source viewer', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    Reflect.deleteProperty(document, 'caretRangeFromPoint');
  });

  it('highlights the selected signal leaf inside source text', () => {
    const { container } = render(
      <SourceViewer
        lines={[
          'assign w_ready_o = valid_i & w_ready_o;',
          'assign other_ready = 1\'b0;',
        ]}
        selectedSig="tb.dut.u_packet_engine.w_ready_o"
      />,
    );

    const hits = Array.from(container.querySelectorAll('.src-sig-hit'));
    expect(hits.map(el => el.textContent)).toEqual(['w_ready_o', 'w_ready_o']);
    expect(container.textContent).toContain('other_ready');
  });

  it('highlights only the selected source bit slice when a range is selected', () => {
    const { container } = render(
      <SourceViewer
        lines={['irq_status_o[5:0] <= irq_status_o[31:6];']}
        selectedSig="irq_status_o[5:0]"
      />,
    );

    const hits = Array.from(container.querySelectorAll('.src-sig-hit'));
    expect(hits.map(el => el.textContent)).toEqual(['irq_status_o[5:0]']);
  });

  it('does not highlight selected signal names inside comments or numeric literal bases', () => {
    const { container: commentContainer } = render(
      <SourceViewer
        lines={[
          '// Request/control payload',
          'input logic payload;',
        ]}
        selectedSig="payload"
      />,
    );

    expect(Array.from(commentContainer.querySelectorAll('.src-sig-hit')).map(el => el.textContent))
      .toEqual(['payload']);

    const { container: literalContainer } = render(
      <SourceViewer
        lines={['localparam [3:0] IDLE = 4\'d0;']}
        selectedSig="d0"
      />,
    );

    expect(literalContainer.querySelectorAll('.src-sig-hit')).toHaveLength(0);
  });

  it('clears native text selection after capturing source context-menu signals', async () => {
    const removeAllRanges = vi.fn();
    vi.spyOn(window, 'getSelection').mockReturnValue({
      toString: () => 'clk rst irq',
      removeAllRanges,
    } as unknown as Selection);
    const onSignalContextMenu = vi.fn();
    const onSelectSignals = vi.fn();
    const { container } = render(
      <SourceViewer
        lines={['input logic clk, rst, irq;']}
        onSelectSignals={onSelectSignals}
        onSignalContextMenu={onSignalContextMenu}
      />,
    );

    fireEvent.contextMenu(container.querySelector('.src-viewer')!, { clientX: 10, clientY: 10 });
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(onSignalContextMenu).toHaveBeenCalledWith('', 10, 10, ['clk', 'rst', 'irq']);
    expect(removeAllRanges).toHaveBeenCalledTimes(1);
  });

  it('ignores comments and Verilog numeric literals in native source selection menus', async () => {
    const removeAllRanges = vi.fn();
    vi.spyOn(window, 'getSelection').mockReturnValue({
      toString: () => [
        '// Request/control payload',
        'input logic req_valid;',
        'localparam [3:0] IDLE = 4\'d0;',
      ].join('\n'),
      removeAllRanges,
    } as unknown as Selection);
    const onSignalContextMenu = vi.fn();
    const { container } = render(
      <SourceViewer
        lines={['input logic req_valid;']}
        onSignalContextMenu={onSignalContextMenu}
      />,
    );

    fireEvent.contextMenu(container.querySelector('.src-viewer')!, { clientX: 10, clientY: 10 });
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(onSignalContextMenu).toHaveBeenCalledWith('', 10, 10, ['req_valid', 'IDLE']);
    expect(removeAllRanges).toHaveBeenCalledTimes(1);
  });

  it('blocks plain drag text selection in source code', () => {
    const removeAllRanges = vi.fn();
    vi.spyOn(window, 'getSelection').mockReturnValue({
      toString: () => '',
      removeAllRanges,
    } as unknown as Selection);
    const { container } = render(<SourceViewer lines={['input logic presetn;']} />);
    const viewer = container.querySelector('.src-viewer')!;

    expect(fireEvent.mouseDown(viewer, { button: 0 })).toBe(false);
    expect(removeAllRanges).toHaveBeenCalledTimes(1);
  });

  it('collects dragged source identifiers for bulk signal context menu', async () => {
    vi.spyOn(window, 'getSelection').mockReturnValue({
      toString: () => '',
      removeAllRanges: vi.fn(),
    } as unknown as Selection);
    const onSignalContextMenu = vi.fn();
    const onSelectSignals = vi.fn();
    const { container } = render(
      <SourceViewer
        lines={['input logic clk, rst, irq;']}
        onSelectSignals={onSelectSignals}
        onSignalContextMenu={onSignalContextMenu}
      />,
    );
    const code = container.querySelector('[data-src-code]')!;
    const textNode = code.firstChild as Text;
    const text = textNode.textContent || '';
    Object.defineProperty(document, 'caretRangeFromPoint', {
      configurable: true,
      value: vi.fn((x: number) => {
        const range = document.createRange();
        range.setStart(textNode, x < 50 ? 0 : text.length);
        return range;
      }),
    });

    const viewer = container.querySelector('.src-viewer')!;
    fireEvent.mouseDown(viewer, { button: 0, clientX: 1, clientY: 10 });
    fireEvent.mouseMove(window, { clientX: 100, clientY: 10 });
    fireEvent.mouseUp(window, { clientX: 100, clientY: 10 });
    await new Promise(resolve => setTimeout(resolve, 0));
    fireEvent.contextMenu(viewer, { clientX: 100, clientY: 10 });

    expect(onSelectSignals).toHaveBeenCalledWith(['clk', 'rst', 'irq']);
    expect(onSignalContextMenu).toHaveBeenCalledWith('', 100, 10, ['clk', 'rst', 'irq']);
  });

  it('excludes comments and numeric literal bases from dragged source signals', async () => {
    vi.spyOn(window, 'getSelection').mockReturnValue({
      toString: () => '',
      removeAllRanges: vi.fn(),
    } as unknown as Selection);
    const onSelectSignals = vi.fn();
    const { container } = render(
      <SourceViewer
        lines={[
          '// Request/control payload',
          'input logic req_valid;',
          'localparam [3:0] IDLE = 4\'d0, ACCEPT = 4\'d1;',
        ]}
        onSelectSignals={onSelectSignals}
      />,
    );
    const code = container.querySelectorAll('[data-src-code]');
    const startNode = code[0].firstChild as Text;
    const endNode = code[2].firstChild as Text;
    const endText = endNode.textContent || '';
    Object.defineProperty(document, 'caretRangeFromPoint', {
      configurable: true,
      value: vi.fn((_x: number, y: number) => {
        const range = document.createRange();
        range.setStart(y < 20 ? startNode : endNode, y < 20 ? 0 : endText.length);
        return range;
      }),
    });

    const viewer = container.querySelector('.src-viewer')!;
    fireEvent.mouseDown(viewer, { button: 0, clientX: 1, clientY: 10 });
    fireEvent.mouseMove(window, { clientX: 100, clientY: 60 });
    fireEvent.mouseUp(window, { clientX: 100, clientY: 60 });
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(onSelectSignals).toHaveBeenCalledWith(['req_valid', 'IDLE', 'ACCEPT']);
  });

  it('picks the exact source bit slice under the cursor', () => {
    vi.spyOn(window, 'getSelection').mockReturnValue({
      toString: () => '',
      removeAllRanges: vi.fn(),
    } as unknown as Selection);
    const onPickSignal = vi.fn();
    const { container } = render(
      <SourceViewer
        lines={['irq_status_o[5:0] <= irq_status_o[31:6];']}
        onPickSignal={onPickSignal}
      />,
    );
    const code = container.querySelector('[data-src-code]')!;
    const textNode = code.firstChild as Text;
    const text = textNode.textContent || '';
    const range = document.createRange();
    range.setStart(textNode, text.indexOf('[5:0]') + 2);
    Object.defineProperty(document, 'caretRangeFromPoint', {
      configurable: true,
      value: vi.fn(() => range),
    });

    fireEvent.click(container.querySelector('.src-viewer')!, { clientX: 10, clientY: 10 });

    expect(onPickSignal).toHaveBeenCalledWith('irq_status_o[5:0]');
  });
});
