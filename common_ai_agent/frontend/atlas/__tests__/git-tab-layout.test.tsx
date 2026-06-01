import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { GitTab } from '../git-tab';

const graphPayload = {
  graph: '* raw graph should not render',
  commits: [
    {
      hash: 'abc123456789',
      short: 'abc1234',
      subject: 'replace rtl/example.sv (+2/-1 lines)',
      author: 'Atlas Agent',
      time: 1_780_000_000,
    },
  ],
};

const statusPayload = {
  branch: 'main',
  head: 'abc1234',
  cwd: '/tmp/example',
  files: [],
  ahead: 0,
  behind: 0,
};

const showPayload = {
  diff: [
    'commit abc123456789',
    'diff --git a/rtl/example.sv b/rtl/example.sv',
    '+assign done = 1;',
    '-assign done = 0;',
  ].join('\n'),
};

describe('GitTab layout', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/api/ip/list')) {
        return Promise.resolve(new Response(JSON.stringify({ items: [{ ip: 'brian_dma' }] })));
      }
      if (url.includes('/git/graph')) {
        return Promise.resolve(new Response(JSON.stringify(graphPayload)));
      }
      if (url.includes('/api/git/status')) {
        return Promise.resolve(new Response(JSON.stringify(statusPayload)));
      }
      if (url.includes('/api/git/show')) {
        return Promise.resolve(new Response(JSON.stringify(showPayload)));
      }
      return Promise.resolve(new Response(JSON.stringify({ error: 'unexpected request' }), { status: 404 }));
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows only commit history and the split diff pane', async () => {
    render(<GitTab initialIp="brian_dma" />);

    await screen.findByText('replace rtl/example.sv (+2/-1 lines)');

    expect(screen.queryByText('* raw graph should not render')).not.toBeInTheDocument();
    expect(screen.getByText(/Select a commit from history/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText('replace rtl/example.sv (+2/-1 lines)'));

    await waitFor(() => expect(screen.getByText('+assign done = 1;')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Full diff/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^History$/i })).not.toBeInTheDocument();
  });
});
