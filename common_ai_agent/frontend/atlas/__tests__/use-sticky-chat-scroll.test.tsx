import { fireEvent, render, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useStickyChatScroll } from '../use-sticky-chat-scroll';

interface StickyPaneProps {
  readonly rows: readonly string[];
}

const StickyPane = ({ rows }: StickyPaneProps) => {
  const { scrollRef, onScroll, scrollToBottom } = useStickyChatScroll<HTMLDivElement>([rows.length]);
  return (
    <>
      <div ref={scrollRef} onScroll={onScroll} data-testid="pane">
        {rows.map((row) => <p key={row}>{row}</p>)}
      </div>
      <button type="button" onClick={scrollToBottom}>jump</button>
    </>
  );
};

const setScrollGeometry = (
  pane: HTMLElement,
  geometry: {
    readonly scrollTop: () => number;
    readonly setScrollTop: (value: number) => void;
    readonly scrollHeight: () => number;
    readonly clientHeight: () => number;
  },
) => {
  Object.defineProperty(pane, 'scrollTop', {
    configurable: true,
    get: geometry.scrollTop,
    set: geometry.setScrollTop,
  });
  Object.defineProperty(pane, 'scrollHeight', { configurable: true, get: geometry.scrollHeight });
  Object.defineProperty(pane, 'clientHeight', { configurable: true, get: geometry.clientHeight });
};

describe('useStickyChatScroll', () => {
  it('does not force-scroll when the user is reading older messages', async () => {
    let scrollTop = 100;
    const { getByTestId, rerender } = render(<StickyPane rows={['a']} />);
    const pane = getByTestId('pane');
    setScrollGeometry(pane, {
      scrollTop: () => scrollTop,
      setScrollTop: (value) => { scrollTop = value; },
      scrollHeight: () => 1000,
      clientHeight: () => 400,
    });

    fireEvent.scroll(pane);
    rerender(<StickyPane rows={['a', 'b']} />);

    await waitFor(() => expect(scrollTop).toBe(100));
  });

  it('keeps following when the user is already near the bottom', async () => {
    let scrollTop = 590;
    const { getByTestId, rerender } = render(<StickyPane rows={['a']} />);
    const pane = getByTestId('pane');
    setScrollGeometry(pane, {
      scrollTop: () => scrollTop,
      setScrollTop: (value) => { scrollTop = value; },
      scrollHeight: () => 1000,
      clientHeight: () => 400,
    });

    fireEvent.scroll(pane);
    rerender(<StickyPane rows={['a', 'b']} />);

    await waitFor(() => expect(scrollTop).toBe(1000));
  });

  it('allows an explicit jump back to the bottom', async () => {
    let scrollTop = 100;
    const { getByRole, getByTestId } = render(<StickyPane rows={['a']} />);
    const pane = getByTestId('pane');
    setScrollGeometry(pane, {
      scrollTop: () => scrollTop,
      setScrollTop: (value) => { scrollTop = value; },
      scrollHeight: () => 1000,
      clientHeight: () => 400,
    });

    fireEvent.scroll(pane);
    fireEvent.click(getByRole('button', { name: 'jump' }));

    await waitFor(() => expect(scrollTop).toBe(1000));
  });
});
