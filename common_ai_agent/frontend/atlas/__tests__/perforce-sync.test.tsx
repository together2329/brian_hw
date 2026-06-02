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
  const addBodies: Array<Record<string, unknown>> = [];
  const syncBodies: Array<Record<string, unknown>> = [];
  const submitBodies: Array<Record<string, unknown>> = [];
  const paneUrls: string[] = [];

  beforeEach(() => {
    editBodies.length = 0;
    addBodies.length = 0;
    syncBodies.length = 0;
    submitBodies.length = 0;
    paneUrls.length = 0;
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = requestUrl(input);
      if (url.startsWith('/api/ip/list')) {
        return jsonResponse({ items: [{ name: 'ulw_p4' }] });
      }
      if (url.startsWith('/api/scm/pane')) {
        paneUrls.push(url);
        const selectedStream = new URL(url, 'http://atlas.test').searchParams.get('stream') || '//GOOD_SOC/GOOD_IP';
        return jsonResponse({
          ok: true,
          stream: selectedStream,
          scmRoot: '/tmp/p4_workspace',
          streams: ['//GOOD_SOC/GOOD_IP', '//GOOD_SOC/GOOD_IP_DEV'],
          local: [
            { path: 'rtl/existing.sv', state: 'same' },
            { path: 'rtl/new_file.sv', state: 'new' },
          ],
          depot: [{
            path: selectedStream.endsWith('_DEV') ? '//GOOD_SOC/GOOD_IP_DEV/rtl/dev.sv' : '//GOOD_SOC/GOOD_IP/rtl/main.sv',
            rev: '1',
          }],
          pending: [{ path: '//GOOD_SOC/GOOD_IP/rtl/opened.sv', action: 'edit', change: '12' }],
          pendingChanges: [
            { id: 'default', label: 'default' },
            { id: '12', label: '12 existing pending' },
          ],
        });
      }
      if (url === '/api/scm/add') {
        const bodyText = typeof init?.body === 'string' ? init.body : '{}';
        addBodies.push(JSON.parse(bodyText) as Record<string, unknown>);
        return jsonResponse({ ok: true });
      }
      if (url === '/api/scm/edit') {
        const bodyText = typeof init?.body === 'string' ? init.body : '{}';
        editBodies.push(JSON.parse(bodyText) as Record<string, unknown>);
        return jsonResponse({ ok: true });
      }
      if (url === '/api/scm/sync') {
        const bodyText = typeof init?.body === 'string' ? init.body : '{}';
        syncBodies.push(JSON.parse(bodyText) as Record<string, unknown>);
        return jsonResponse({ ok: true });
      }
      if (url === '/api/scm/submit') {
        const bodyText = typeof init?.body === 'string' ? init.body : '{}';
        submitBodies.push(JSON.parse(bodyText) as Record<string, unknown>);
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
    fireEvent.click(screen.getByText('//GOOD_SOC/GOOD_IP/rtl/main.sv'));
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));

    await waitFor(() => {
      expect(editBodies).toHaveLength(1);
      expect(editBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        scmRoot: '/tmp/p4_workspace',
        paths: ['rtl/existing.sv'],
        targetPaths: ['//GOOD_SOC/GOOD_IP/rtl/main.sv'],
      });
    });
  });

  it('reloads pane and posts actions with the selected stream', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/main.sv');
    fireEvent.change(screen.getByLabelText('Perforce stream'), {
      target: { value: '//GOOD_SOC/GOOD_IP_DEV' },
    });

    await screen.findByText('//GOOD_SOC/GOOD_IP_DEV/rtl/dev.sv');
    fireEvent.click(screen.getByText('rtl/existing.sv'));
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));

    await waitFor(() => {
      expect(paneUrls.some(url => url.includes('stream=%2F%2FGOOD_SOC%2FGOOD_IP_DEV'))).toBe(true);
      expect(editBodies.at(-1)).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        stream: '//GOOD_SOC/GOOD_IP_DEV',
        scmRoot: '/tmp/p4_workspace',
        paths: ['rtl/existing.sv'],
      });
    });
  });

  it('posts depot paths to sync when no depot row is selected', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/main.sv');
    fireEvent.click(screen.getByRole('button', { name: /sync/i }));

    await waitFor(() => {
      expect(syncBodies).toHaveLength(1);
      expect(syncBodies[0]).toMatchObject({
        provider: 'perforce',
        ip: 'ulw_p4',
        stream: '//GOOD_SOC/GOOD_IP',
        scmRoot: '/tmp/p4_workspace',
        paths: ['//GOOD_SOC/GOOD_IP/rtl/main.sv'],
      });
    });
  });

  it('posts selected Perforce folder target and pending changelist to add', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    await screen.findByText('rtl/new_file.sv');
    await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/');
    fireEvent.change(screen.getByLabelText('Pending changelist'), {
      target: { value: '12' },
    });
    fireEvent.click(screen.getByText('rtl/new_file.sv'));
    fireEvent.click(screen.getByText('//GOOD_SOC/GOOD_IP/rtl/'));
    fireEvent.click(screen.getByRole('button', { name: /add/i }));

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

  it('checks out selected Perforce file into the selected pending changelist', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/main.sv');
    fireEvent.change(screen.getByLabelText('Pending changelist'), {
      target: { value: '12' },
    });
    fireEvent.click(screen.getByText('//GOOD_SOC/GOOD_IP/rtl/main.sv'));
    fireEvent.click(screen.getByRole('button', { name: /checkout/i }));

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

  it('submits the selected pending changelist', async () => {
    render(<PerforceSyncTab initialIp="ulw_p4" provider="perforce" />);

    const pendingSelect = await screen.findByLabelText('Pending changelist');
    fireEvent.change(pendingSelect, {
      target: { value: '12' },
    });
    await screen.findByText('//GOOD_SOC/GOOD_IP/rtl/opened.sv');
    fireEvent.change(screen.getByPlaceholderText('changelist description…'), {
      target: { value: 'submit selected pending' },
    });
    const submitButtons = screen.getAllByRole('button', { name: /submit/i });
    fireEvent.click(submitButtons[submitButtons.length - 1]);

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
