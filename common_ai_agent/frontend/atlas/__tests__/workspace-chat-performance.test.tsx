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

import {
  WorkspaceChatPane,
  renderWorkspaceFeedEntries,
  type RenderWorkspaceFeedEntriesProps,
} from '../workspace-root-render';

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

  it('mounts only the latest 20 entries in Recent mode', () => {
    const feed = Array.from({ length: 25 }, (_, i) => ({
      id: `msg-${i}`,
      kind: 'agent',
      text: `entry-${i}`,
    }));
    const feedProps: RenderWorkspaceFeedEntriesProps = {
      feed,
      qaState: {},
      chatFeedSummary: true,
      toggleOpt: vi.fn(),
      setCustom: vi.fn(),
      submitCard: vi.fn(),
      dir: '/tmp/ws',
    };

    render(
      <WorkspaceChatPane
        feedRef={createRef<HTMLDivElement>()}
        streamText=""
        feedEntriesProps={feedProps}
      />,
    );

    expect(renderCounters.feedEntry).toHaveBeenCalledTimes(21);
    expect(screen.getByText(/Showing latest 20 of 25/)).toBeTruthy();
    expect(screen.queryByText('entry-4')).toBeNull();
    expect(screen.getByText('entry-24')).toBeTruthy();
  });

  it('keeps stable entry keys when the Recent window slides', () => {
    const baseFeed = Array.from({ length: 25 }, (_, i) => ({
      id: `msg-${i}`,
      kind: 'agent',
      text: `entry-${i}`,
    }));
    const props = (feed: any[]): RenderWorkspaceFeedEntriesProps => ({
      feed,
      qaState: {},
      chatFeedSummary: true,
      toggleOpt: vi.fn(),
      setCustom: vi.fn(),
      submitCard: vi.fn(),
      dir: '/tmp/ws',
    });

    const beforeKeys = renderWorkspaceFeedEntries(props(baseFeed)).map((node: any) => String(node.key));
    const afterKeys = renderWorkspaceFeedEntries(props([
      ...baseFeed,
      { id: 'msg-25', kind: 'agent', text: 'entry-25' },
    ])).map((node: any) => String(node.key));

    expect(beforeKeys).toContain('feed:msg-10');
    expect(afterKeys).toContain('feed:msg-10');
    expect(afterKeys).not.toContain('feed:msg-5');
  });
});
