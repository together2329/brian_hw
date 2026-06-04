import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  buildSsotDocChatPrefillText,
  fetchSsotDocSource,
  requireSsotDocSelection,
  sourceForSsotDocTarget,
  submitSsotDocFeedback,
} from '../ssot-doc-feedback-api';
import type { SsotDocSelectedTarget } from '../ssot-doc-feedback-types';

const target: SsotDocSelectedTarget = {
  section: 'registers',
  path: 'registers.register_list.0.fields.0.description',
  label: 'CTRL.enable.description',
  kind: 'register_field',
};

describe('SSOT DOC feedback API helpers', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (window as any).ACTIVE_SESSION = '';
    (window as any).atlasData = {
      normalizeSessionName: (value: unknown) => String(value || '').trim(),
    };
  });

  it('resolves source lookup and submits feedback with credentials', async () => {
    (window as any).ACTIVE_SESSION = 'alice/hi/demo_ip/ssot-gen';
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ok: true,
        ip: 'demo_ip',
        section: 'registers',
        path: target.path,
        ssot_path: 'demo_ip/yaml/demo_ip.ssot.yaml',
        label: target.label,
        kind: target.kind,
        value: 'Enable transfer',
        yaml: 'Enable transfer\n',
        feedback: [],
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ok: true,
        ip: 'demo_ip',
        section: 'registers',
        path: target.path,
        feedback_id: 'fb_1',
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    vi.stubGlobal('fetch', fetchMock);

    const source = await fetchSsotDocSource({ ip: 'demo_ip', target });
    const feedback = await submitSsotDocFeedback({
      ip: 'demo_ip',
      target,
      comment: 'Clarify enable timing',
      value: 'Enable transfer when START is high.',
    });

    expect(source.value).toBe('Enable transfer');
    expect(feedback.feedback_id).toBe('fb_1');
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/ssot/doc-source?ip=demo_ip&path=registers.register_list.0.fields.0.description&session_id=alice%2Fhi%2Fdemo_ip%2Fssot-gen',
      { credentials: 'include' },
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/ssot/doc-feedback',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body))).toMatchObject({
      ip: 'demo_ip',
      mode: 'feedback',
      section: 'registers',
      path: target.path,
      comment: 'Clarify enable timing',
      value: 'Enable transfer when START is high.',
      session_id: 'alice/hi/demo_ip/ssot-gen',
    });
  });

  it('surfaces backend errors', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response(JSON.stringify({ ok: false, error: 'path must use dot notation' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }),
    ));

    await expect(fetchSsotDocSource({ ip: 'demo_ip', target })).rejects.toThrow('path must use dot notation');
  });

  it('rejects invalid JSON responses', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      new Response('not-json', {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ));

    await expect(fetchSsotDocSource({ ip: 'demo_ip', target })).rejects.toThrow('invalid JSON');
  });

  it('requires a selected DOC target before lookup or comment', () => {
    expect(() => requireSsotDocSelection(null)).toThrow('Select a DOC component first');
  });

  it('builds a structured chat prefill from selected DOC source context', () => {
    const text = buildSsotDocChatPrefillText({
      ip: 'demo_ip',
      target,
      comment: 'This field is confusing.',
      selectedText: 'Enable transfer',
      source: {
        ok: true,
        ip: 'demo_ip',
        ssot_path: 'demo_ip/yaml/demo_ip.ssot.yaml',
        section: 'registers',
        path: target.path,
        label: target.label,
        kind: target.kind,
        value: 'Enable transfer',
        yaml: 'description: Enable transfer\n',
        feedback: [],
      },
    });

    expect(text).toContain('/to-ssot demo_ip');
    expect(text).toContain('SSOT path: registers.register_list.0.fields.0.description');
    expect(text).toContain('This field is confusing.');
    expect(text).toContain('description: Enable transfer');
  });

  it('drops stale source details when the selected DOC target changes', () => {
    const staleSource = {
      ok: true,
      ip: 'demo_ip',
      ssot_path: 'demo_ip/yaml/demo_ip.ssot.yaml',
      section: 'top_module',
      path: 'top_module',
      label: 'Top Module',
      kind: 'section',
      value: { name: 'demo_ip' },
      yaml: 'name: demo_ip\n',
      feedback: [],
    };

    expect(sourceForSsotDocTarget(staleSource, target)).toBeNull();
    expect(sourceForSsotDocTarget(staleSource, {
      section: 'top_module',
      path: 'top_module',
      label: 'Top Module',
      kind: 'section',
    })).toBe(staleSource);
  });
});
