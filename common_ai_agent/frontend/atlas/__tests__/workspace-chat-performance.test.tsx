import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { createRef } from 'react';

const renderCounters = vi.hoisted(() => ({
  feedEntry: vi.fn(),
  livePreview: vi.fn(),
  toolCard: vi.fn(),
}));

vi.mock('../workspace-feed-cards', async () => {
  const React = await import('react');
  return {
    FeedEntry: (props: any) => {
      renderCounters.feedEntry(props);
      return React.createElement('div', { 'data-testid': 'feed-entry' }, String(props.entry?.text || ''));
    },
    LiveAgentPreview: (props: any) => {
      renderCounters.livePreview(props);
      return props.text
        ? React.createElement('div', { 'data-testid': 'live-preview' }, String(props.text))
        : null;
    },
    ToolCard: (props: any) => {
      renderCounters.toolCard(props);
      return React.createElement('div', { 'data-testid': 'tool-card' }, 'tool');
    },
  };
});

import { WorkspaceChatPane, type RenderWorkspaceFeedEntriesProps } from '../workspace-root-render';

describe('WorkspaceChatPane streaming render cost', () => {
  afterEach(() => {
    cleanup();
    renderCounters.feedEntry.mockClear();
    renderCounters.livePreview.mockClear();
    renderCounters.toolCard.mockClear();
  });

  it('does not rebuild feed entries when only the live stream text changes', () => {
    const feed = [
      { kind: 'user', text: 'start' },
      { kind: 'agent', text: 'stable completed answer' },
    ];
    const stableFeedProps: RenderWorkspaceFeedEntriesProps = {
      feed,
      qaState: {},
      chatFeedSummary: false,
      toggleOpt: vi.fn(),
      setCustom: vi.fn(),
      submitCard: vi.fn(),
      dir: '/tmp/ws',
    };
    const feedRef = createRef<HTMLDivElement>();

    const { rerender } = render(
      <WorkspaceChatPane
        feedRef={feedRef}
        streamText=""
        feedEntriesProps={stableFeedProps}
      />,
    );

    expect(renderCounters.feedEntry).toHaveBeenCalledTimes(2);
    renderCounters.feedEntry.mockClear();
    renderCounters.toolCard.mockClear();
    renderCounters.livePreview.mockClear();

    rerender(
      <WorkspaceChatPane
        feedRef={feedRef}
        streamText="token burst visible in live preview"
        feedEntriesProps={{ ...stableFeedProps }}
      />,
    );

    expect(screen.getByTestId('live-preview')).toHaveTextContent('token burst visible in live preview');
    expect(renderCounters.feedEntry).not.toHaveBeenCalled();
    expect(renderCounters.toolCard).not.toHaveBeenCalled();
    expect(renderCounters.livePreview).toHaveBeenCalledTimes(1);
  });
});
