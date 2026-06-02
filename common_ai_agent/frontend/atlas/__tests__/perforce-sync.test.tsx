import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import PerforceSyncTab from '../perforce-sync';

type Body = Record<string, unknown>;

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

const readBody = (init?: RequestInit): Body => {
  const bodyText = typeof init?.body === 'string' ? init.body : '{}';
  return JSON.parse(bodyText) as Body;
};

describe('PerforceSyncTab directory actions', () => {
  const paneUrls: string[] = [];
  const editBodies: Body[] = [];
  const addBodies: Body[] = [];
  const syncBodies: Body[] = [];
  const submitBodies: Body[] = [];

  beforeEach(() => {
    paneUrls.length = 0;
    editBodies.length = 0;
    addBodies.length = 0;
    syncBodies.length = 0;
    submitBodies.length = 0;
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = requestUrl(input);
      if (url.startsWith('/api/ip/list')) {
        return jsonResponse({ items: [{ name: 'ulw_p4' }] });
      }
      if (url.startsWith('/api/scm/pane')) {
        paneUrls.push(url);
        const parsed = new URL(url, 'http://atlas.test');
        const localDir = parsed.searchParams.get('local_dir') || '';
        const depotDir = parsed.searchParams.get('depot_dir') || '//GOOD_SOC/GOOD_IP/';
        return jsonResponse({
          ok: true,
          stream: '//GOOD_SOC/GOOD_IP',
          scmRoot: '/tmp/p4_workspace',
          streams: ['//GOOD_SOC/GOOD_IP'],
          localDir,
          depotDir,
          local: localDir === 'rtl' ? [
            { path: 'rtl/existing.sv', state: 'same', kind: 'file' },
            { path: 'rtl/new_file.sv', state: 'new', kind: 'file' },
          ] : [
            { path: 'rtl', state: '', kind: 'folder' },
          ],
          depot: depotDir === '//GOOD_SOC/GOOD_IP/rtl/' ? [
            { path: '//GOOD_SOC/GOOD_IP/rtl/main.sv', rev: '1', kind: 'file' },
            { path: '//GOOD_SOC/GOOD_IP/rtl/other.sv', rev: '1', kind: 'file' },
          ] : [
            { path: '//GOOD_SOC/GOOD_IP/rtl/', rev: '', kind: 'folder' },
          ],
          pending: [{ path: '//GOOD_SOC/GOOD_IP/rtl/opened.sv', action: 'edit', change: '12' }],
          pendingChanges: [
            { id: 'default', label: 'default' },
            { id: '12', label: '12 existing pending' },
          ],
        });
      }
      if (url === '/api/scm/add') {
        addBodies.push(readBody(init));
        return jsonResponse({ ok: true });
      }
      if (url === '/api/scm/edit') {
        editBodies.push(readBody(init));
        return jsonResponse({ ok: true });
      }
      if (url === '/api/scm/sync') {
        syncBodies.push(readBody(init));
        return jsonResponse({ ok: true });
      }
      if (url === '/api/scm/submit') {
        submitBodies.push(readBody(init));
        return jsonResponse({ ok: true });
      }
      return jsonResponse({ ok: true });
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('shows directory roots when local and Perforce panes first load', async () => {
    // Given: local and depot fixtures contain files under rtl/.
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    // When: the pane data loads.
    const folders = await screen.findAllByText('rtl/');

    // Then: both panes show enterable folders instead of flattened file paths.
    expect(folders).toHaveLength(2);
    expect(screen.queryByText('rtl/existing.sv')).not.toBeInTheDocument();
    expect(screen.queryByText('//GOOD_SOC/GOOD_IP/rtl/main.sv')).not.toBeInTheDocument();
  });

  it('enters local and Perforce directories by clicking folder rows', async () => {
    // Given: both panes are at their root directories.
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const [localRtl] = await screen.findAllByText('rtl/');

    // When: the user enters the local rtl folder, then the Perforce rtl folder.
    fireEvent.click(localRtl);
    await screen.findByText('new_file.sv');
    fireEvent.click(screen.getByText('rtl/'));

    // Then: each pane lists basename files for the selected directory.
    expect(screen.getByText('existing.sv')).toBeVisible();
    expect(screen.getByText('new_file.sv')).toBeVisible();
    expect(await screen.findByText('main.sv')).toBeVisible();
    expect(screen.getByText('other.sv')).toBeVisible();
    expect(paneUrls.some(url => url.includes('local_dir=rtl'))).toBe(true);
    expect(paneUrls.some(url => url.includes('depot_dir=%2F%2FGOOD_SOC%2FGOOD_IP%2Frtl%2F'))).toBe(true);
  });

  it('keeps middle actions to add checkout and sync while pending can submit', async () => {
    // Given: the Perforce tab is loaded.
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    await screen.findAllByText('rtl/');

    // When: the action bars render.
    const add = screen.getByRole('button', { name: /add/i });
    const checkout = screen.getByRole('button', { name: /checkout/i });
    const sync = screen.getByRole('button', { name: /sync/i });

    // Then: no middle Edit or Submit action is present, and bottom Submit remains.
    expect(add).toBeVisible();
    expect(checkout).toBeVisible();
    expect(sync).toBeVisible();
    expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeVisible();
  });

  it('adds a selected local file to the selected Perforce target folder and changelist', async () => {
    // Given: the user entered local rtl and Perforce rtl, then selected CL 12.
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const [localRtl] = await screen.findAllByText('rtl/');
    fireEvent.click(localRtl);
    await screen.findByText('new_file.sv');
    fireEvent.click(screen.getByText('rtl/'));
    await screen.findByText('main.sv');
    fireEvent.change(screen.getByLabelText('Pending changelist'), { target: { value: '12' } });

    // When: the user selects a new local file and presses Add.
    fireEvent.click(screen.getByText('new_file.sv'));
    fireEvent.click(screen.getByRole('button', { name: /add/i }));

    // Then: Add posts the relative local file, target depot folder, and changelist.
    await waitFor(() => {
      expect(addBodies).toHaveLength(1);
      expect(addBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        scmRoot: '/tmp/p4_workspace',
        paths: ['rtl/new_file.sv'],
        targetPaths: ['//GOOD_SOC/GOOD_IP/rtl/'],
        changelist: '12',
      });
    });
  });

  it('checks out a selected Perforce file into the selected pending changelist', async () => {
    // Given: the user entered Perforce rtl and selected CL 12.
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const folders = await screen.findAllByText('rtl/');
    fireEvent.click(folders[1]);
    await screen.findByText('main.sv');
    fireEvent.change(screen.getByLabelText('Pending changelist'), { target: { value: '12' } });

    // When: the user selects a Perforce file and presses Checkout.
    fireEvent.click(screen.getByText('main.sv'));
    fireEvent.click(screen.getByRole('button', { name: /checkout/i }));

    // Then: Checkout posts the full depot path as the SCM source.
    await waitFor(() => {
      expect(editBodies).toHaveLength(1);
      expect(editBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        scmRoot: '/tmp/p4_workspace',
        sourceRoot: 'scm',
        paths: ['//GOOD_SOC/GOOD_IP/rtl/main.sv'],
        changelist: '12',
      });
    });
  });

  it('syncs the current Perforce directory into the current local directory', async () => {
    // Given: the user entered local rtl and Perforce rtl.
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const [localRtl] = await screen.findAllByText('rtl/');
    fireEvent.click(localRtl);
    await screen.findByText('new_file.sv');
    fireEvent.click(screen.getByText('rtl/'));
    await screen.findByText('main.sv');

    // When: the user presses Sync without selecting individual files.
    fireEvent.click(screen.getByRole('button', { name: /sync/i }));

    // Then: Sync posts the current depot files and the current local target folder.
    await waitFor(() => {
      expect(syncBodies).toHaveLength(1);
      expect(syncBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        scmRoot: '/tmp/p4_workspace',
        paths: ['//GOOD_SOC/GOOD_IP/rtl/main.sv', '//GOOD_SOC/GOOD_IP/rtl/other.sv'],
        targetPaths: ['rtl/'],
      });
    });
  });

  it('submits the selected pending changelist from the pending section', async () => {
    // Given: CL 12 has an opened pending file.
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    fireEvent.change(await screen.findByLabelText('Pending changelist'), { target: { value: '12' } });
    await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/opened.sv');

    // When: the user enters a description and submits.
    fireEvent.change(screen.getByPlaceholderText('changelist description…'), {
      target: { value: 'submit selected pending' },
    });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Then: Submit posts the selected changelist and description.
    await waitFor(() => {
      expect(submitBodies).toHaveLength(1);
      expect(submitBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        scmRoot: '/tmp/p4_workspace',
        message: 'submit selected pending',
        add_all: false,
        changelist: '12',
      });
    });
  });
});
