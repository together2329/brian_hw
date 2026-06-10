import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('PerforceSyncTab pending changelist delete', () => {
  const deleteBodies: RequestBody[] = [];
  let pendingRows: PendingRow[] = [];
  let pendingChanges: PendingChange[] = [];

  beforeEach(() => {
    deleteBodies.length = 0;
    // changelist 12 is an empty junk changelist: no opened files at all
    pendingRows = [];
    pendingChanges = [
      { id: 'default', label: 'default' },
      { id: '12', label: '12 stranded by failed submit', description: 'stranded by failed submit' },
    ];
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = requestUrl(input);
      if (url.startsWith('/api/ip/list')) {
        return jsonResponse({ items: [{ name: 'ulw_p4' }] });
      }
      if (url.startsWith('/api/scm/pane')) {
        return jsonResponse({
          ok: true,
          stream: '//GOOD_SOC/GOOD_IP',
          scmRoot: '/tmp/p4_workspace',
          streams: ['//GOOD_SOC/GOOD_IP'],
          localDir: '',
          depotDir: '//GOOD_SOC/GOOD_IP/',
          local: [],
          depot: [],
          pending: pendingRows,
          pendingChanges,
        });
      }
      if (url.startsWith('/api/scm/log')) {
        return jsonResponse({ ok: true, commits: [] });
      }
      if (url === '/api/scm/change/delete') {
        deleteBodies.push(readBody(init));
        pendingChanges = [{ id: 'default', label: 'default' }];
        return jsonResponse({ ok: true, stdout: 'Change 12 deleted.' });
      }
      return jsonResponse({ ok: true });
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('deletes the selected numbered changelist even when it has no opened files', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    expect(await screen.findByText('PENDING')).toBeVisible();
    // no Delete CL button while the default changelist is selected
    expect(screen.queryByRole('button', { name: /delete cl/i })).not.toBeInTheDocument();

    fireEvent.change(await screen.findByLabelText('Pending changelist'), { target: { value: '12' } });
    // empty CL: Revert stays disabled, Delete CL is the cleanup affordance
    expect(screen.getByRole('button', { name: /^revert$/i })).toBeDisabled();
    const deleteButton = await screen.findByRole('button', { name: /delete cl/i });
    fireEvent.click(deleteButton);

    await waitFor(() => expect(deleteBodies).toHaveLength(1));
    expect(deleteBodies[0].changelist).toBe('12');
    expect(deleteBodies[0].provider).toBe('perforce');

    // after deletion the dropdown returns to default and the button disappears
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /delete cl/i })).not.toBeInTheDocument();
    });
    expect((screen.getByLabelText('Pending changelist') as HTMLSelectElement).value).toBe('default');
  });
});
