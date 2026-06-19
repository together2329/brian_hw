import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { createRef } from 'react';

import '../ui-utils.tsx';
import { FeedEntry, ToolCard } from '../workspace-feed-cards';
import { WorkspaceChatPane, type RenderWorkspaceFeedEntriesProps } from '../workspace-root-render';

const toolCard = (tool: string, text: string) => (
  <ToolCard
    action={{ kind: 'action', tool, text: `▶ ${tool} path="demo.txt"`, createdAt: Date.now() }}
    obs={{ kind: 'obs', tool, text, createdAt: Date.now() }}
    summaryMode
  />
);

const numberedLines = (prefix: string, count: number) => (
  Array.from({ length: count }, (_, i) => `${prefix}-${String(i + 1).padStart(2, '0')}`).join('\n')
);

const toolFrameSrcDoc = (container: HTMLElement): string => (
  container.querySelector('iframe.tool-detail-frame')?.getAttribute('srcdoc') || ''
);

describe('workspace tool-card output display policy', () => {
  afterEach(() => cleanup());

  it('keeps read_file results collapsed by default', () => {
    const view = render(toolCard('read_file', numberedLines('read-visible-only-after-open', 12)));

    expect(screen.getByText('read_file')).toBeTruthy();
    expect(view.container.textContent).not.toContain('read-visible-only-after-open-01');

    fireEvent.click(screen.getByText('read_file').closest('.tool-card-head') as HTMLElement);

    expect(toolFrameSrcDoc(view.container)).toContain('read-visible-only-after-open-01');
  });

  it('keeps grep_file results collapsed by default', () => {
    render(toolCard('grep_file', [
      '=== Matches in rtl/top.sv ===',
      '  12:     unique_grep_result = 1;',
    ].join('\n')));

    expect(screen.getByText('grep_file')).toBeTruthy();
    expect(screen.queryByText(/unique_grep_result/)).toBeNull();

    fireEvent.click(screen.getByText('grep_file').closest('.tool-card-head') as HTMLElement);

    expect(toolFrameSrcDoc(document.body)).toContain('unique_grep_result');
  });

  it('limits write_file result bodies to 10 lines', () => {
    render(toolCard('write_file', numberedLines('write-preview', 14)));

    const srcdoc = toolFrameSrcDoc(document.body);
    expect(srcdoc).toContain('write-preview-10');
    expect(srcdoc).not.toContain('write-preview-11');
    expect(srcdoc).toContain('4 more lines hidden');
  });

  it('limits replace result bodies to 10 lines', () => {
    render(toolCard('replace_in_file', numberedLines('replace-preview', 35)));

    const srcdoc = toolFrameSrcDoc(document.body);
    expect(srcdoc).toContain('replace-preview-10');
    expect(srcdoc).not.toContain('replace-preview-11');
    expect(srcdoc).toContain('25 more lines hidden');
  });

  it('keeps an expanded replace_in_file card open when the Recent window advances', () => {
    const makeFeed = (tailExtra = 0) => [
      ...Array.from({ length: 17 }, (_, i) => ({
        id: `before-${i}`,
        kind: 'agent',
        text: `before-${i}`,
      })),
      {
        id: 'replace-action',
        kind: 'action',
        tool: 'replace_in_file',
        text: '▶ replace_in_file path="demo.txt"',
        createdAt: 1,
      },
      {
        id: 'replace-obs',
        kind: 'obs',
        tool: 'replace_in_file',
        text: numberedLines('replace-stays-open', 35),
        createdAt: 2,
      },
      ...Array.from({ length: 6 + tailExtra }, (_, i) => ({
        id: `after-${i}`,
        kind: 'agent',
        text: `after-${i}`,
      })),
    ];
    const props = (feed: any[]): RenderWorkspaceFeedEntriesProps => ({
      feed,
      qaState: {},
      chatFeedSummary: true,
      toggleOpt: () => {},
      setCustom: () => {},
      submitCard: () => {},
      dir: '/tmp/ws',
    });

    const { rerender, container } = render(
      <WorkspaceChatPane
        feedRef={createRef<HTMLDivElement>()}
        streamText=""
        feedEntriesProps={props(makeFeed())}
      />,
    );

    expect(toolFrameSrcDoc(container)).toContain('replace-stays-open-10');
    expect(toolFrameSrcDoc(container)).not.toContain('replace-stays-open-11');

    fireEvent.click(screen.getByText('replace_in_file').closest('.tool-card-head') as HTMLElement);
    expect(toolFrameSrcDoc(container)).toContain('replace-stays-open-11');

    rerender(
      <WorkspaceChatPane
        feedRef={createRef<HTMLDivElement>()}
        streamText=""
        feedEntriesProps={props(makeFeed(1))}
      />,
    );

    expect(toolFrameSrcDoc(container)).toContain('replace-stays-open-11');
  });

  it('renders parseable raw action lines as tool cards immediately', () => {
    const view = render(
      <FeedEntry
        entry={{ kind: 'action', text: 'Action: run_command(command="pytest -q")', createdAt: Date.now() }}
        summaryMode
      />,
    );

    expect(view.container.querySelector('.tool-card')).toBeTruthy();
    expect(view.container.querySelector('.react-block.action')).toBeNull();
    expect(screen.getByText('run_command')).toBeTruthy();
    expect(view.container.textContent).not.toContain('Action:');
  });
});
