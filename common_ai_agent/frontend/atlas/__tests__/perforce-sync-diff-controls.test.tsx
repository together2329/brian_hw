import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import PerforceSyncTab from '../perforce-sync';

type RequestBody = Record<string, unknown>;

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

describe('PerforceSyncTab diff controls and saved locations', () => {
  const diffUrls: string[] = [];
  const paneUrls: string[] = [];
  const prefsPosts: RequestBody[] = [];
  const editBodies: RequestBody[] = [];
  let savedPrefs: RequestBody = {};
  let localRows: Array<Record<string, unknown>> = [];
  let depotRows: Array<Record<string, unknown>> = [];

  beforeEach(() => {
    diffUrls.length = 0;
    paneUrls.length = 0;
    prefsPosts.length = 0;
    editBodies.length = 0;
    savedPrefs = {};
    localRows = [{ path: 'rtl', state: '', kind: 'folder' }];
    depotRows = [];
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = requestUrl(input);
      if (url.startsWith('/api/ip/list')) {
        return jsonResponse({ items: [{ name: 'ulw_p4' }] });
      }
      if (url.startsWith('/api/scm/uiprefs')) {
        if (init?.method === 'POST') {
          prefsPosts.push(readBody(init));
          return jsonResponse({ ok: true });
        }
        return jsonResponse({ ok: true, prefs: savedPrefs });
      }
      if (url.startsWith('/api/scm/pane')) {
        paneUrls.push(url);
        const parsed = new URL(url, 'http://atlas.test');
        return jsonResponse({
          ok: true,
          stream: '//GOOD_SOC/GOOD_IP',
          scmRoot: '/tmp/p4_workspace',
          streams: ['//GOOD_SOC/GOOD_IP'],
          localDir: parsed.searchParams.get('local_dir') || '',
          depotDir: parsed.searchParams.get('depot_dir') || '//GOOD_SOC/GOOD_IP/',
          local: localRows,
          depot: depotRows,
          pending: [{ path: '//GOOD_SOC/GOOD_IP/rtl/opened.sv', action: 'edit', change: 'default' }],
          pendingChanges: [{ id: 'default', label: 'default' }],
        });
      }
      if (url.startsWith('/api/scm/log')) {
        return jsonResponse({ ok: true, commits: [] });
      }
      if (url === '/api/scm/edit') {
        editBodies.push(readBody(init));
        return jsonResponse({ ok: true });
      }
      if (url.startsWith('/api/scm/diff')) {
        diffUrls.push(url);
        return jsonResponse({
          ok: true,
          diff: '--- //GOOD_SOC/GOOD_IP/rtl/opened.sv\n+++ /ws/rtl/opened.sv\n@@ -1,1 +1,1 @@\n-module v1;\n+module v2;\n',
        });
      }
      return jsonResponse({ ok: true });
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('selects on pending row click and only loads a colored diff via the Diff button', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    const row = await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/opened.sv');
    fireEvent.click(row);
    // selecting must NOT auto-load the diff
    expect(diffUrls).toHaveLength(0);
    expect(screen.getByText('PENDING')).toBeVisible();

    fireEvent.click(screen.getByTitle('Show diff for the selected pending file'));
    const added = await screen.findByText('+module v2;');
    const removed = screen.getByText('-module v1;');
    expect(diffUrls).toHaveLength(1);
    expect(added.style.color).toBe('var(--ok)');
    expect(removed.style.color).toBe('var(--err)');
  });

  it('pairs multi-file checkout by visible list order, not click order', async () => {
    localRows = [
      { path: 'a.sv', state: 'modified', kind: 'file' },
      { path: 'b.sv', state: 'modified', kind: 'file' },
    ];
    depotRows = [
      { path: '//GOOD_SOC/GOOD_IP/ip/a.sv', rev: '1', kind: 'file' },
      { path: '//GOOD_SOC/GOOD_IP/ip/b.sv', rev: '1', kind: 'file' },
    ];
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    // click in REVERSE order on both panes (local rows have bare-path titles)
    fireEvent.click(await screen.findByTitle('b.sv'));
    fireEvent.click(screen.getByTitle('a.sv'));
    const depotB = await screen.findByTitle('//GOOD_SOC/GOOD_IP/ip/b.sv');
    const depotA = screen.getByTitle('//GOOD_SOC/GOOD_IP/ip/a.sv');
    fireEvent.click(depotB);
    fireEvent.click(depotA);
    fireEvent.click(screen.getByRole('button', { name: /checkout/i }));

    await waitFor(() => expect(editBodies).toHaveLength(1));
    // zipped positionally on the backend: a↔a, b↔b regardless of click order
    expect(editBodies[0].paths).toEqual(['a.sv', 'b.sv']);
    expect(editBodies[0].targetPaths).toEqual([
      '//GOOD_SOC/GOOD_IP/ip/a.sv',
      '//GOOD_SOC/GOOD_IP/ip/b.sv',
    ]);
  });

  it('restores saved pane locations and saves navigation to uiprefs', async () => {
    savedPrefs = { localDir: 'rtl', depotDir: '//GOOD_SOC/GOOD_IP/rtl/', stream: '//GOOD_SOC/GOOD_IP' };
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    await waitFor(() => expect(paneUrls.length).toBeGreaterThan(0));
    expect(paneUrls[0]).toContain('local_dir=rtl');
    expect(paneUrls[0]).toContain('depot_dir=%2F%2FGOOD_SOC%2FGOOD_IP%2Frtl%2F');
    // the restored navigation is also persisted back
    await waitFor(() => expect(prefsPosts.length).toBeGreaterThan(0));
    expect(prefsPosts[0]).toMatchObject({ ip: 'ulw_p4', localDir: 'rtl', depotDir: '//GOOD_SOC/GOOD_IP/rtl/' });
  });
});
