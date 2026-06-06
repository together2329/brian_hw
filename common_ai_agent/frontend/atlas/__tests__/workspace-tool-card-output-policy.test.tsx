import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';

import '../ui-utils.tsx';
import { ToolCard } from '../workspace-feed-cards';

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

describe('workspace tool-card output display policy', () => {
  afterEach(() => cleanup());

  it('keeps read_file results collapsed by default', () => {
    const view = render(toolCard('read_file', numberedLines('read-visible-only-after-open', 12)));

    expect(screen.getByText('read_file')).toBeTruthy();
    expect(view.container.textContent).not.toContain('read-visible-only-after-open-01');

    fireEvent.click(screen.getByText('read_file').closest('.tool-card-head') as HTMLElement);

    expect(view.container.textContent).toContain('read-visible-only-after-open-01');
  });

  it('keeps grep_file results collapsed by default', () => {
    render(toolCard('grep_file', [
      '=== Matches in rtl/top.sv ===',
      '  12:     unique_grep_result = 1;',
    ].join('\n')));

    expect(screen.getByText('grep_file')).toBeTruthy();
    expect(screen.queryByText(/unique_grep_result/)).toBeNull();

    fireEvent.click(screen.getByText('grep_file').closest('.tool-card-head') as HTMLElement);

    expect(screen.getByText(/unique_grep_result/)).toBeTruthy();
  });

  it('limits write_file result bodies to 10 lines', () => {
    render(toolCard('write_file', numberedLines('write-preview', 14)));

    expect(screen.getByText('write-preview-10')).toBeTruthy();
    expect(screen.queryByText('write-preview-11')).toBeNull();
    expect(screen.getByText(/4 more lines hidden/)).toBeTruthy();
  });

  it('limits replace result bodies to 30 lines', () => {
    render(toolCard('replace_in_file', numberedLines('replace-preview', 35)));

    expect(screen.getByText('replace-preview-30')).toBeTruthy();
    expect(screen.queryByText('replace-preview-31')).toBeNull();
    expect(screen.getByText(/5 more lines hidden/)).toBeTruthy();
  });
});
