import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import PerforceSyncTab from '../perforce-sync';

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

describe('PerforceSyncTab edit action', () => {
  const editBodies: Array<Record<string, unknown>> = [];

  beforeEach(() => {
    editBodies.length = 0;
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = requestUrl(input);
      if (url.startsWith('/api/ip/list')) {
        return jsonResponse({ items: [{ name: 'ulw_p4' }] });
      }
      if (url.startsWith('/api/scm/pane')) {
        return jsonResponse({
          ok: true,
          local: [
            { path: 'rtl/existing.sv', state: 'same' },
            { path: 'rtl/new_file.sv', state: 'new' },
          ],
          depot: [],
          pending: [],
        });
      }
      if (url === '/api/scm/edit') {
        const bodyText = typeof init?.body === 'string' ? init.body : '{}';
        editBodies.push(JSON.parse(bodyText) as Record<string, unknown>);
        return jsonResponse({ ok: true });
      }
      return jsonResponse({ ok: true });
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('posts selected local path to /api/scm/edit', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    await screen.findByText('rtl/existing.sv');

    expect(screen.getByRole('button', { name: /add/i })).toBeVisible();
    expect(screen.getByRole('button', { name: /edit/i })).toBeVisible();
    expect(screen.getByRole('button', { name: /sync/i })).toBeVisible();

    fireEvent.click(screen.getByText('rtl/existing.sv'));
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));

    await waitFor(() => {
      expect(editBodies).toHaveLength(1);
      expect(editBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        paths: ['rtl/existing.sv'],
      });
    });
  });
});
