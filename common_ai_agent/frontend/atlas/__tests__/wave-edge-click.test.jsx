import React from 'react';
import { fireEvent, render } from '@testing-library/react';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

describe('waveform edge click', () => {
  beforeAll(async () => {
    globalThis.React = React;
    await import('../debug-shared.tsx?wave-edge-click-test');
  });

  afterEach(() => {
    delete window.WAVE_TIME_START;
    delete window.WAVE_TIME_END;
  });

  it('snaps only to a nearby visible trace transition', () => {
    window.WAVE_TIME_START = 0;
    window.WAVE_TIME_END = 100;

    const trace = [[0, 0], [25, 1], [75, 0]];
    expect(window.nearestWaveEdgeTime(trace, 176, 700)).toBe(25);
    expect(window.nearestWaveEdgeTime(trace, 220, 700)).toBe(null);
  });

  it('emits the clicked transition time from WaveRow track clicks', () => {
    window.WAVE_TIME_START = 0;
    window.WAVE_TIME_END = 100;
    const onClick = vi.fn();
    const onEdgeClick = vi.fn();
    const view = render(React.createElement(window.WaveRow, {
      name: 'irq_out',
      trace: [[0, 0], [50, 1], [80, 0]],
      width: 100,
      isBus: false,
      onClick,
      onEdgeClick,
    }));

    const track = view.container.querySelector('.wave-track');
    track.getBoundingClientRect = () => ({
      left: 10,
      right: 110,
      top: 0,
      bottom: 24,
      width: 100,
      height: 24,
      x: 10,
      y: 0,
      toJSON() { return this; },
    });

    fireEvent.click(track, { clientX: 61 });

    expect(onClick).toHaveBeenCalledTimes(1);
    expect(onEdgeClick).toHaveBeenCalledTimes(1);
    expect(onEdgeClick.mock.calls[0][0]).toBe(50);
  });

  it('applies colorHint to bus waveform segments', () => {
    const view = render(React.createElement(window.WaveRow, {
      name: 'irq_status_o[31:0]',
      trace: [[0, '1011']],
      width: 100,
      isBus: true,
      colorHint: '#b388ff',
    }));

    const segment = view.container.querySelector('polygon');
    const label = view.container.querySelector('.bus-flag-text');
    expect(segment?.getAttribute('stroke')).toBe('#b388ff');
    expect(segment?.getAttribute('fill')).toContain('#b388ff');
    expect(label?.getAttribute('style')).toContain('#b388ff');
  });

  it('shows mapped parameter names for FSM-style bus values', () => {
    const view = render(React.createElement(window.WaveRow, {
      name: 'state[1:0]',
      trace: [[0, '00'], [100, '01']],
      width: 200,
      isBus: true,
      radix: 'FSM',
      valueMap: { 0: 'S_IDLE', 1: 'S_RUN' },
    }));

    expect(view.container.querySelector('.wave-val')?.textContent).toBe('S_RUN');
    expect(Array.from(view.container.querySelectorAll('.bus-flag-text')).map(el => el.textContent)).toContain('S_IDLE');
    expect(Array.from(view.container.querySelectorAll('.bus-flag-text')).map(el => el.textContent)).toContain('S_RUN');
  });
});
