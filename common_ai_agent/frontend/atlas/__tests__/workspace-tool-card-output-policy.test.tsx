import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';

import '../ui-utils.tsx';
import { FeedEntry, ToolCard } from '../workspace-feed-cards';

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
