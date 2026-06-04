import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import PerforceSyncTab from '../perforce-sync';

type RequestBody = Record<string, unknown>;
type PendingRow = { readonly path: string; readonly action: string; readonly change: string };
type PendingChange = { readonly id: string; readonly label: string; readonly description?: string };

const jsonResponse = (payload: unknown) =>
  new Response(JSON.stringify(payload), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });

const requestUrl = (input: RequestInfo | URL): string => {
  if (typeof input === 'string') return input;
  if (input instanceof URL) return input.toString();
  return input.url;
};

const readBody = (init?: RequestInit): RequestBody => {
  const bodyText = typeof init?.body === 'string' ? init.body : '{}';
  return JSON.parse(bodyText) as RequestBody;
};

describe('PerforceSyncTab history and submit refresh', () => {
  const logUrls: string[] = [];
  const showUrls: string[] = [];
  const submitBodies: RequestBody[] = [];
  let pendingRows: PendingRow[] = [];
  let pendingChanges: PendingChange[] = [];

  beforeEach(() => {
    logUrls.length = 0;
    showUrls.length = 0;
    submitBodies.length = 0;
    pendingRows = [{ path: '//GOOD_SOC/GOOD_IP/rtl/opened.sv', action: 'edit', change: '12' }];
    pendingChanges = [
      { id: 'default', label: 'default' },
      { id: '12', label: '12 pending checkout', description: 'pending checkout' },
    ];
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = requestUrl(input);
      if (url.startsWith('/api/ip/list')) {
        return jsonResponse({ items: [{ name: 'ulw_p4' }] });
      }
      if (url.startsWith('/api/scm/pane')) {
        const parsed = new URL(url, 'http://atlas.test');
        return jsonResponse({
          ok: true,
          stream: '//GOOD_SOC/GOOD_IP',
          scmRoot: '/tmp/p4_workspace',
          streams: ['//GOOD_SOC/GOOD_IP'],
          localDir: parsed.searchParams.get('local_dir') || '',
          depotDir: parsed.searchParams.get('depot_dir') || '//GOOD_SOC/GOOD_IP/',
          local: [{ path: 'rtl', state: '', kind: 'folder' }],
          depot: [{ path: '//GOOD_SOC/GOOD_IP/rtl/main.sv', rev: '9', kind: 'file' }],
          pending: pendingRows,
          pendingChanges,
        });
      }
      if (url.startsWith('/api/scm/log')) {
        logUrls.push(url);
        return jsonResponse({
          ok: true,
          commits: [
            { sha: '77', short: '77', subject: 'Fix RTL gate', author: 'brian', date: '1780000000' },
          ],
        });
      }
      if (url.startsWith('/api/scm/show')) {
        showUrls.push(url);
        return jsonResponse({
          ok: true,
          diff: 'Change 77 by brian\n--- //GOOD_SOC/GOOD_IP/rtl/main.sv\n+++ //GOOD_SOC/GOOD_IP/rtl/main.sv\n+module fixed;\n',
        });
      }
      if (url === '/api/scm/submit') {
        submitBodies.push(readBody(init));
        pendingRows = [];
        pendingChanges = [{ id: 'default', label: 'default' }];
        return jsonResponse({ ok: true, stdout: 'Change 12 submitted.' });
      }
      return jsonResponse({ ok: true });
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('loads Perforce changelist history and shows the selected changelist diff', async () => {
    const view = within(render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />).container);

    fireEvent.click(await view.findByText('Fix RTL gate'));

    expect(await view.findByText(/\+module fixed;/)).toBeVisible();
    expect(logUrls.some(url => url.includes('/api/scm/log'))).toBe(true);
    expect(logUrls.some(url => url.includes('stream=%2F%2FGOOD_SOC%2FGOOD_IP'))).toBe(true);
    expect(logUrls.some(url => url.includes('scm_root=%2Ftmp%2Fp4_workspace'))).toBe(true);
    expect(showUrls.some(url => url.includes('revision=77'))).toBe(true);
  });

  it('removes a submitted pending changelist from the visible pending list', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    fireEvent.change(await screen.findByLabelText('Pending changelist'), { target: { value: '12' } });
    expect(await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/opened.sv')).toBeVisible();

    fireEvent.change(screen.getByPlaceholderText('changelist description…'), {
      target: { value: 'submit selected pending' },
    });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => expect(submitBodies).toHaveLength(1));
    await waitFor(() => {
      expect(screen.queryByText('//GOOD_SOC/GOOD_IP/rtl/opened.sv')).not.toBeInTheDocument();
    });
  });
});
