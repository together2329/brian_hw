import { beforeEach, describe, expect, it } from 'vitest';

import {
  ATLAS_ASYNC_RESOURCE_CACHES,
  atlasResourceUrl,
  readAtlasAsyncResource,
} from '../workspace-async-resource';
import { parseAtQuery } from '../workspace-rootdata-feed-completion';
import { appendActiveSessionParam } from '../workspace-session-routing';

describe('workspace session-aware path URLs', () => {
  beforeEach(() => {
    Object.values(ATLAS_ASYNC_RESOURCE_CACHES).forEach(cache => cache.clear());
    (window as any).ACTIVE_SESSION = 'alice/hi/jjj/rtl-gen';
    (window as any).CONTEXT = { activeIp: 'jjj' };
    (window as any).atlasData = {
      normalizeSessionName: (value: unknown) => String(value || '').trim(),
    };
  });

  it('builds preview URLs with active session context', () => {
    expect(atlasResourceUrl('file', 'rtl/top.sv')).toBe(
      '/api/file?path=rtl%2Ftop.sv&session_id=alice%2Fhi%2Fjjj%2Frtl-gen',
    );
    expect(atlasResourceUrl('ssot', 'yaml/jjj.ssot.yaml')).toBe(
      '/api/ssot?file=yaml%2Fjjj.ssot.yaml&session_id=alice%2Fhi%2Fjjj%2Frtl-gen',
    );
  });

  it('appends the active session to workspace resource query params', () => {
    const params = appendActiveSessionParam(new URLSearchParams({ path: 'rtl/top.sv' }));

    expect(params.get('session_id')).toBe('alice/hi/jjj/rtl-gen');
  });

  it('treats rootless @ paths as active-IP relative for lookup', () => {
    const query = parseAtQuery('open @rtl/');

    expect(query.parentRel).toBe('rtl');
    expect(query.parentAbs).toBe('jjj/rtl');
    expect(query.ipScoped).toBe(true);
  });

  it('keeps explicit workspace-root escapes out of active-IP lookup', () => {
    const query = parseAtQuery('open @/doc/');

    expect(query.parentRel).toBe('doc');
    expect(query.parentAbs).toBe('doc');
    expect(query.absoluteEscape).toBe(true);
    expect(query.ipScoped).toBe(false);
  });

  it('does not reuse file preview cache entries across active sessions', async () => {
    const fetchCalls: string[] = [];
    global.fetch = (async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');
      fetchCalls.push(url.toString());
      return new Response(JSON.stringify({
        content: `content for ${url.searchParams.get('session_id') || 'none'}`,
        size: 1,
        mtime: 1,
        truncated: false,
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }) as typeof fetch;

    (window as any).ACTIVE_SESSION = 'alice/hi/jjj/rtl-gen';
    const first = await readAtlasAsyncResource('file', 'rtl/top.sv');
    (window as any).ACTIVE_SESSION = 'alice/other/jjj/rtl-gen';
    const second = await readAtlasAsyncResource('file', 'rtl/top.sv');

    expect(first.body).toBe('content for alice/hi/jjj/rtl-gen');
    expect(second.body).toBe('content for alice/other/jjj/rtl-gen');
    expect(fetchCalls).toHaveLength(2);
  });
});
