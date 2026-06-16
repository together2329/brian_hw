import React, { useState, type ComponentProps } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { TimeRuler, WaveCursor, WaveRow } from '../debug-shared';
import { WaveBand } from '../sim-debug-wave';
import type { PinnedSignal, VcdSignal } from '../sim-debug-helpers';

type WaveBandProps = ComponentProps<typeof WaveBand>;

const traceRow = (name: string, scope = 'tb.dut'): VcdSignal => ({
  name,
  signalName: name,
  scope,
  range: '',
  trace: [[0, '0'], [10, '1']],
  isBus: false,
});

const makeDecor = (): WaveBandProps['decor'] => ({
  colors: {},
  radices: {},
  paramValueMap: {},
  tags: {},
  groups: {},
  setSignalColor: vi.fn(),
  setSignalRadix: vi.fn(),
  moveSignal: vi.fn(),
  assignGroup: vi.fn(),
  ungroup: vi.fn(),
  toggleFold: vi.fn(),
  renameGroup: vi.fn(),
  setGroupColor: vi.fn(),
});

interface HarnessProps {
  readonly traceList: VcdSignal[];
  readonly onDelete: (items: PinnedSignal[]) => void;
  readonly waveCursor?: number;
  readonly waveRcFiles?: Array<{ name: string; path?: string }>;
  readonly onSave?: () => void;
  readonly onRestore?: () => void;
}

const Harness = ({
  traceList,
  onDelete,
  waveCursor = 0,
  waveRcFiles = [],
  onSave = vi.fn(),
  onRestore = vi.fn(),
}: HarnessProps) => {
  const [waveRowSel, setWaveRowSel] = useState<PinnedSignal[]>([]);
  const [timeDisplayUnit, setTimeDisplayUnit] = useState('ns');
  const [waveRcName, setWaveRcName] = useState('signal.rc');
  return (
    <WaveBand
      eff={{ showSource: false, th: 0.5 }}
      showHelp={false}
      setShowHelp={vi.fn()}
      vcdActive="REQIP/sim/REQIP.vcd"
      effRange={[0, 100]}
      vcdData={{ timeRange: [0, 100], timescale: 'ns' }}
      setViewRange={vi.fn()}
      zoomIn={vi.fn()}
      zoomOut={vi.fn()}
      zoomFit={vi.fn()}
      zoomToCursors={vi.fn()}
      panBy={vi.fn()}
      waveWidth={320}
      traceList={traceList}
      ipName="REQIP"
      waveCursor={waveCursor}
      waveCursorB={10}
      setWaveCursor={vi.fn()}
      setWaveCursorB={vi.fn()}
      showSignalHierarchy={false}
      selectedSig=""
      selectedSigScope=""
      waveRowSel={waveRowSel}
      setWaveRowSel={setWaveRowSel}
      onSelectWaveSignal={vi.fn()}
      onDeleteSignalsFromWave={onDelete}
      onReorderSignal={vi.fn()}
      decor={makeDecor()}
      timeDisplayUnit={timeDisplayUnit}
      setTimeDisplayUnit={setTimeDisplayUnit}
      waveRcName={waveRcName}
      setWaveRcName={setWaveRcName}
      waveRcFiles={waveRcFiles}
      waveRcStatus=""
      onSaveWaveRc={onSave}
      onRestoreWaveRc={onRestore}
    />
  );
};

describe('sim debug WaveBand requirements', () => {
  beforeEach(() => {
    Object.assign(window, { TimeRuler, WaveRow, WaveCursor });
    window.WAVE_TIME_START = 0;
    window.WAVE_TIME_END = 100;
  });

  it('SDR-011 SDR-012 keeps the first waveform row outside the sticky header and reachable by bulk delete', () => {
    const onDelete = vi.fn();
    const view = render(
      <Harness
        traceList={[traceRow('first_signal'), traceRow('second_signal')]}
        onDelete={onDelete}
      />,
    );

    const stickyHeader = view.container.querySelector('[title^="click the time axis"]');
    const clickGutter = view.container.querySelector('.wave-top-click-gutter');
    const firstRow = screen.getByTitle('first_signal · tb.dut');
    expect(stickyHeader).not.toContainElement(firstRow);
    expect(clickGutter).not.toBeNull();
    expect(
      stickyHeader ? stickyHeader.compareDocumentPosition(firstRow) & Node.DOCUMENT_POSITION_FOLLOWING : 0,
    ).not.toBe(0);
    expect(
      clickGutter ? clickGutter.compareDocumentPosition(firstRow) & Node.DOCUMENT_POSITION_FOLLOWING : 0,
    ).not.toBe(0);

    fireEvent.click(firstRow);
    expect(screen.getByText('1 selected')).toBeInTheDocument();
    fireEvent.click(screen.getByTitle('delete selected waveform rows'));

    expect(onDelete).toHaveBeenCalledWith([{ name: 'first_signal', scope: 'tb.dut' }]);
  });

  it('SDR-013 keeps waveform drag previews anchored next to the pointer', () => {
    const setDragImage = vi.fn();
    const setData = vi.fn();
    const view = render(
      <Harness
        traceList={[traceRow('first_signal'), traceRow('second_signal')]}
        onDelete={vi.fn()}
      />,
    );
    const firstRow = screen.getByTitle('first_signal · tb.dut').closest('.wave-dnd-row');
    expect(firstRow).not.toBeNull();
    if (firstRow === null) return;

    fireEvent.dragStart(firstRow, {
      clientX: 8,
      dataTransfer: { effectAllowed: '', setData, setDragImage },
    });

    expect(setData).toHaveBeenCalledWith('text/plain', 'first_signal');
    expect(setDragImage).toHaveBeenCalledWith(expect.any(HTMLElement), 12, 12);
  });

  it('SDR-013 does not reorder a row when drag starts in the waveform plot area', () => {
    const setDragImage = vi.fn();
    const setData = vi.fn();
    render(
      <Harness
        traceList={[traceRow('first_signal'), traceRow('second_signal')]}
        onDelete={vi.fn()}
      />,
    );
    const firstRow = screen.getByTitle('first_signal · tb.dut').closest('.wave-dnd-row');
    expect(firstRow).not.toBeNull();
    if (firstRow === null) return;

    const event = new Event('dragstart', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clientX', { value: 999 });
    Object.defineProperty(event, 'dataTransfer', {
      value: { effectAllowed: '', setData, setDragImage },
    });
    firstRow.dispatchEvent(event);

    expect(setData).not.toHaveBeenCalled();
    expect(setDragImage).not.toHaveBeenCalled();
  });

  it('SDR-017 exposes rc save/restore controls and preserves rc filenames as user-facing state', () => {
    const onSave = vi.fn();
    const onRestore = vi.fn();
    render(
      <Harness
        traceList={[traceRow('first_signal')]}
        onDelete={vi.fn()}
        waveRcFiles={[{ name: 'signal.rc' }, { name: 'feature.rc' }]}
        onSave={onSave}
        onRestore={onRestore}
      />,
    );

    expect(screen.getByTitle('waveform rc file name')).toHaveValue('signal.rc');
    expect(document.querySelector('option[value="feature.rc"]')).not.toBeNull();

    fireEvent.click(screen.getByTitle('save current waveform layout to rc'));
    fireEvent.click(screen.getByTitle('restore waveform layout from rc'));

    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onRestore).toHaveBeenCalledTimes(1);
  });

  it('SDR-026 shows waveform row values at cursor A instead of the final sample', () => {
    const view = render(
      <Harness
        traceList={[{
          ...traceRow('cursor_value'),
          trace: [[0, '0'], [10, '1'], [20, '0']],
        }]}
        waveCursor={10}
        onDelete={vi.fn()}
      />,
    );

    expect(view.container.querySelector('.wave-val')?.textContent).toBe('1');
  });
});
