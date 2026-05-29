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
});
