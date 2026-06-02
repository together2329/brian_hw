import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import PerforceSyncTab from '../perforce-sync';

type Body = Record<string, unknown>;
type PendingFixture = { readonly path: string; readonly change: string };

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

const bodyStrings = (value: unknown): string[] => {
  if (!Array.isArray(value)) return [];
  return value.map(item => String(item));
};

describe('PerforceSyncTab pane navigation', () => {
  const editBodies: Body[] = [];
  const submitBodies: Body[] = [];
  const diffUrls: string[] = [];
  const checkedOut: PendingFixture[] = [];
  let delayRootLocalPane = false;
  let releaseRootLocalPane: (() => void) | null = null;

  const panePayload = (localDir: string, depotDir: string) => ({
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
      { path: 'docs', state: '', kind: 'folder' },
    ],
    depot: depotDir === '//GOOD_SOC/GOOD_IP/rtl/' ? [
      { path: '//GOOD_SOC/GOOD_IP/rtl/main.sv', rev: '1', kind: 'file' },
      { path: '//GOOD_SOC/GOOD_IP/rtl/other.sv', rev: '1', kind: 'file' },
    ] : [
      { path: '//GOOD_SOC/GOOD_IP/rtl/', rev: '', kind: 'folder' },
      { path: '//GOOD_SOC/GOOD_IP/docs/', rev: '', kind: 'folder' },
    ],
    pending: [
      { path: '//GOOD_SOC/GOOD_IP/rtl/opened.sv', action: 'edit', change: '12' },
      ...checkedOut.map(row => ({ path: row.path, action: 'edit', change: row.change })),
    ],
    pendingChanges: [
      { id: 'default', label: 'default' },
      { id: '12', label: '12 existing pending' },
    ],
  });

  beforeEach(() => {
    editBodies.length = 0;
    submitBodies.length = 0;
    diffUrls.length = 0;
    checkedOut.length = 0;
    delayRootLocalPane = false;
    releaseRootLocalPane = null;
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = requestUrl(input);
      if (url.startsWith('/api/ip/list')) {
        return jsonResponse({ items: [{ name: 'ulw_p4' }] });
      }
      if (url.startsWith('/api/scm/pane')) {
        const parsed = new URL(url, 'http://atlas.test');
        const localDir = parsed.searchParams.get('local_dir') || '';
        const depotDir = parsed.searchParams.get('depot_dir') || '//GOOD_SOC/GOOD_IP/';
        if (delayRootLocalPane && localDir === '') {
          return new Promise<Response>(resolve => {
            releaseRootLocalPane = () => resolve(jsonResponse(panePayload(localDir, depotDir)));
          });
        }
        return jsonResponse(panePayload(localDir, depotDir));
      }
      if (url === '/api/scm/edit') {
        const body = readBody(init);
        editBodies.push(body);
        const change = String(body.changelist || 'default');
        const targetPaths = bodyStrings(body.targetPaths)
          .filter(path => path.startsWith('//') && !path.endsWith('/'));
        const pendingPaths = targetPaths.length ? targetPaths : bodyStrings(body.paths);
        for (const path of pendingPaths) {
          checkedOut.push({ path, change });
        }
        return jsonResponse({ ok: true });
      }
      if (url === '/api/scm/submit') {
        submitBodies.push(readBody(init));
        return jsonResponse({ ok: true });
      }
      if (url.startsWith('/api/scm/diff')) {
        diffUrls.push(url);
        return jsonResponse({
          ok: true,
          diff: '--- //GOOD_SOC/GOOD_IP/rtl/main.sv\n+++ //GOOD_SOC/GOOD_IP/rtl/main.sv\n+module changed;\n',
        });
      }
      return jsonResponse({ ok: true });
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('does not show child files as parent files while going up waits for reload', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const [localRtl] = await screen.findAllByText('rtl/');
    fireEvent.click(localRtl);
    await screen.findByText('new_file.sv');

    delayRootLocalPane = true;
    fireEvent.click(screen.getByText('← ..'));

    expect(screen.queryByText('new_file.sv')).not.toBeInTheDocument();
    releaseRootLocalPane?.();
    await waitFor(() => expect(screen.getAllByText('rtl/')).toHaveLength(2));
  });

  it('moves backward and forward through combined local and depot locations', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const [localRtl] = await screen.findAllByText('rtl/');
    fireEvent.click(localRtl);
    await screen.findByText('new_file.sv');
    fireEvent.click(screen.getByText('rtl/'));
    await screen.findByText('main.sv');

    fireEvent.click(screen.getByRole('button', { name: /back/i }));

    await waitFor(() => expect(screen.queryByText('main.sv')).not.toBeInTheDocument());
    expect(screen.getByText('new_file.sv')).toBeVisible();
    expect(screen.getByText('rtl/')).toBeVisible();

    fireEvent.click(screen.getByRole('button', { name: /forward/i }));

    expect(await screen.findByText('main.sv')).toBeVisible();
    expect(screen.getByText('new_file.sv')).toBeVisible();
  });

  it('shows a checked-out Perforce file in the pending edit list after reload', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const folders = await screen.findAllByText('rtl/');
    fireEvent.click(folders[1]);
    await screen.findByText('main.sv');
    fireEvent.change(screen.getByLabelText('Pending changelist'), { target: { value: '12' } });

    fireEvent.click(screen.getByText('main.sv'));
    fireEvent.click(screen.getByRole('button', { name: /checkout/i }));

    await waitFor(() => expect(editBodies).toHaveLength(1));
    expect(await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/main.sv')).toBeVisible();
  });

  it('checks out a selected local modification into a selected Perforce target file', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const [localRtl] = await screen.findAllByText('rtl/');
    fireEvent.click(localRtl);
    await screen.findByText('new_file.sv');
    fireEvent.click(screen.getByText('rtl/'));
    await screen.findByText('main.sv');

    fireEvent.click(screen.getByText('new_file.sv'));
    fireEvent.click(screen.getByText('main.sv'));
    fireEvent.click(screen.getByRole('button', { name: /checkout/i }));

    await waitFor(() => {
      expect(editBodies).toHaveLength(1);
      expect(editBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        paths: ['rtl/new_file.sv'],
        targetPaths: ['//GOOD_SOC/GOOD_IP/rtl/main.sv'],
      });
      expect(editBodies[0]).not.toHaveProperty('sourceRoot');
    });
    expect(await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/main.sv')).toBeVisible();
  });

  it('loads a pending file diff so submit changes are visible before submit', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    fireEvent.change(await screen.findByLabelText('Pending changelist'), { target: { value: '12' } });
    fireEvent.click(await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/opened.sv'));

    expect(await screen.findByText(/\+module changed;/)).toBeVisible();
    expect(diffUrls.some(url => url.includes('path=%2F%2FGOOD_SOC%2FGOOD_IP%2Frtl%2Fopened.sv'))).toBe(true);
  });

  it('can diff and submit the target file after local checkout', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);
    const [localRtl] = await screen.findAllByText('rtl/');
    fireEvent.click(localRtl);
    await screen.findByText('new_file.sv');
    fireEvent.click(screen.getByText('rtl/'));
    await screen.findByText('main.sv');

    fireEvent.click(screen.getByText('new_file.sv'));
    fireEvent.click(screen.getByText('main.sv'));
    fireEvent.click(screen.getByRole('button', { name: /checkout/i }));
    const pendingTarget = await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/main.sv');
    fireEvent.click(pendingTarget);

    expect(await screen.findByText(/\+module changed;/)).toBeVisible();
    fireEvent.change(screen.getByPlaceholderText('changelist description…'), {
      target: { value: 'submit checkout diff' },
    });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(submitBodies).toHaveLength(1);
      expect(submitBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        message: 'submit checkout diff',
        changelist: 'default',
      });
    });
  });
});
