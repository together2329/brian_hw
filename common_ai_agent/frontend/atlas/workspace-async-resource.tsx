/* workspace-async-resource.tsx — slice of the ATLAS workspace migration.
 *
 * Async file/resource fetch + cache layer for the ATLAS workspace:
 *   - preview-path persistence (localStorage + window.ATLAS_PREVIEW_PATH)
 *   - default preview path per workflow / stage
 *   - idle-scheduled fetch (window.requestIdleCallback)
 *   - in-memory caches (file / ssot) keyed by active session + path with abort + timeout
 *   - byte / image-MIME formatting helpers
 *   - FILE_TREE metadata lookup
 *   - the useAtlasAsyncResource hook (subscribes to
 *     atlas-resource-loaded / atlas-resource-loading window events)
 *
 * These .tsx files are INERT mirrors — the legacy workspace.jsx still
 * serves the live app. Behavior here is identical to the legacy source.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { activeUiSession, KNOWN_WORKFLOW_PATH_SEGMENTS } from './workspace-session-routing';

export const persistAtlasPreviewPath = (path: unknown): void => {
  const value = String(path || '').trim();
  try {
    if (value) localStorage.setItem('atlasPreviewPath', value);
    else localStorage.removeItem('atlasPreviewPath');
  } catch (_) {}
  try { (window as any).ATLAS_PREVIEW_PATH = value; } catch (_) {}
};

export const defaultPreviewPathForWorkflow = (ip: unknown, workflow: unknown): string => {
  const cleanIp = String(ip || '').trim();
  if (!cleanIp) return '';
  const wf = String(workflow || '').trim();
  const stage = ((window as any).PIPELINE_WORKFLOW_PRIMARY_STAGE && (window as any).PIPELINE_WORKFLOW_PRIMARY_STAGE[wf]) || '';
  if ((window as any).pipelineDefaultWorkspacePath) {
    try {
      const path = (window as any).pipelineDefaultWorkspacePath(cleanIp, wf, stage, []);
      if (path) return path;
    } catch (_) {}
  }
  if (wf === 'ssot-gen') return `${cleanIp}/yaml/${cleanIp}.ssot.yaml`;
  if (wf === 'fl-model-gen') return `${cleanIp}/model/functional_model.py`;
  if (wf === 'rtl-gen') return `${cleanIp}/rtl/rtl_authoring_status.md`;
  if (wf === 'lint') return `${cleanIp}/lint/lint_report.txt`;
  if (wf === 'tb-gen') return `${cleanIp}/tb/cocotb/test_${cleanIp}.py`;
  if (wf === 'sim') return `${cleanIp}/sim/sim_summary.json`;
  if (wf === 'coverage') return `${cleanIp}/sim/coverage_report.md`;
  if (wf === 'sim_debug') return `${cleanIp}/sim/sim_debug_report.md`;
  if (wf === 'syn') return `${cleanIp}/syn/syn_report.md`;
  if (wf === 'sta') return `${cleanIp}/sta/sta_report.md`;
  if (wf === 'pnr') return `${cleanIp}/pnr/pnr_report.md`;
  if (wf === 'sta-post') return `${cleanIp}/sta/sta_post_report.md`;
  if (wf === 'goal-audit') return `${cleanIp}/sim/fl_rtl_goal_audit.json`;
  return '';
};

export const previewPathLooksStaleForWorkspace = (path: unknown, ip: unknown): boolean => {
  const cleanIp = String(ip || '').trim();
  const parts = String(path || '').split('/').filter(Boolean);
  if (!cleanIp || parts.length === 0) return false;
  if (parts[0] !== cleanIp) return false;
  return parts.length >= 3 && KNOWN_WORKFLOW_PATH_SEGMENTS.has(parts[1]);
};

export const ATLAS_ASYNC_RESOURCE_CACHES: Record<string, Map<string, any>> = {
  file: new Map(),
  ssot: new Map(),
};
export const ATLAS_ASYNC_RESOURCE_TIMEOUT_MS: Record<string, number> = {
  file: 300000,
  ssot: 300000,
};

export const scheduleAtlasPreviewWork = (fn: () => void, timeout = 900): (() => void) => {
  let cancelled = false;
  const run = () => {
    if (!cancelled) fn();
  };
  if (typeof window !== 'undefined' && (window as any).requestIdleCallback) {
    const id = (window as any).requestIdleCallback(run, { timeout });
    return () => {
      cancelled = true;
      try { (window as any).cancelIdleCallback && (window as any).cancelIdleCallback(id); } catch (_) {}
    };
  }
  const id = setTimeout(run, 0);
  return () => {
    cancelled = true;
    clearTimeout(id);
  };
};

export const activeAtlasResourceSession = (): string => activeUiSession();

export const atlasResourceCacheKey = (
  _kind: string,
  path: unknown,
  sessionScope: string = activeAtlasResourceSession(),
): string => `${String(sessionScope || '')}\n${String(path || '').trim()}`;

export const emptyAtlasResource = (path = '', sessionScope = activeAtlasResourceSession()): any => ({
  path,
  sessionScope,
  body: '',
  size: 0,
  mtime: 0,
  truncated: false,
  err: null,
  loading: false,
  loadedAt: 0,
});

export const atlasResourceCache = (kind: string): Map<string, any> =>
  ATLAS_ASYNC_RESOURCE_CACHES[kind] || ATLAS_ASYNC_RESOURCE_CACHES.file;

export const isAtlasResourceTimeout = (data: any): boolean =>
  /\bpreview timed out\b/i.test(String((data && data.err) || ''));

export const atlasResourceUrl = (
  kind: string,
  path: string,
  sessionScope: string = activeAtlasResourceSession(),
): string => {
  const params = new URLSearchParams(
    kind === 'ssot' ? { file: path } : { path },
  );
  if (sessionScope) params.set('session_id', sessionScope);
  return kind === 'ssot'
    ? `/api/ssot?${params.toString()}`
    : `/api/file?${params.toString()}`;
};

export const clearAtlasResourcePath = (kind: string, rawPath: unknown): void => {
  const path = String(rawPath || '').trim();
  if (!path) return;
  const cache = atlasResourceCache(kind);
  cache.delete(path);
  for (const key of Array.from(cache.keys())) {
    if (key === path || key.endsWith(`\n${path}`)) cache.delete(key);
  }
};

export const readAtlasAsyncResource = (kind: string, rawPath: unknown, force = false): Promise<any> => {
  const path = String(rawPath || '').trim();
  const sessionScope = activeAtlasResourceSession();
  if (!path) return Promise.resolve(emptyAtlasResource('', sessionScope));
  const cache = atlasResourceCache(kind);
  const cacheKey = atlasResourceCacheKey(kind, path, sessionScope);
  const current = cache.get(cacheKey);
  if (!force && current?.data && !isAtlasResourceTimeout(current.data)) return Promise.resolve(current.data);
  if (!force && current?.promise) return current.promise;
  if (force && current?.controller) {
    try { current.controller.abort(); } catch (_) {}
  }

  const token = Symbol(`${kind}:${cacheKey}`);
  const controller = new AbortController();
  const timeoutMs = ATLAS_ASYNC_RESOURCE_TIMEOUT_MS[kind] || ATLAS_ASYNC_RESOURCE_TIMEOUT_MS.file;
  let didTimeout = false;
  const timeout = setTimeout(() => {
    didTimeout = true;
    controller.abort();
  }, timeoutMs);
  const previous = current?.data || emptyAtlasResource(path, sessionScope);
  const promise = fetch(atlasResourceUrl(kind, path, sessionScope), {
    signal: controller.signal,
    cache: 'no-store',
  }).then(async (r: Response) => {
    let d: any = {};
    try { d = await r.json(); }
    catch (_) { d = { error: r.statusText || `HTTP ${r.status}` }; }
    if (!r.ok && !d.error) d.error = r.statusText || `HTTP ${r.status}`;
    const err = d.error || null;
    const body = err && !d.content
      ? (kind === 'ssot' ? `# could not read ${path}\n# ${err}` : `// ${path}\n// (could not read: ${err})`)
      : (d.content || '');
    return {
      path,
      sessionScope,
      body,
      size: d.size || 0,
      mtime: d.mtime || 0,
      truncated: !!d.truncated,
      err,
      loading: false,
      loadedAt: Date.now(),
    };
  }).catch((e: any) => {
    const msg = e && e.name === 'AbortError'
      ? (didTimeout ? `${kind} preview timed out after ${Math.round(timeoutMs / 1000)}s` : `${kind} preview request cancelled`)
      : String(e);
    return {
      path,
      sessionScope,
      body: kind === 'ssot' ? `# fetch failed: ${msg}` : `// ${path}\n// fetch failed: ${msg}`,
      size: 0,
      mtime: 0,
      truncated: false,
      err: msg,
      loading: false,
      loadedAt: Date.now(),
    };
  }).then((data: any) => {
    clearTimeout(timeout);
    if (cache.get(cacheKey)?.token === token) {
      cache.set(cacheKey, { data });
      window.dispatchEvent(new CustomEvent('atlas-resource-loaded', {
        detail: { kind, path, cacheKey, sessionScope },
      }));
    }
    return data;
  });

  cache.set(cacheKey, { token, promise, data: previous, controller });
  window.dispatchEvent(new CustomEvent('atlas-resource-loading', {
    detail: { kind, path, cacheKey, sessionScope },
  }));
  return promise;
};

export const cachedAtlasResource = (
  kind: string,
  path: unknown,
  sessionScope: string = activeAtlasResourceSession(),
): any => {
  const key = String(path || '').trim();
  if (!key) return emptyAtlasResource('', sessionScope);
  const cacheKey = atlasResourceCacheKey(kind, key, sessionScope);
  return atlasResourceCache(kind).get(cacheKey)?.data || emptyAtlasResource(key, sessionScope);
};

export const atlasFormatBytes = (value: unknown): string => {
  const n = Number(value || 0);
  if (!Number.isFinite(n) || n <= 0) return '';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
};

export const atlasImageMimeForExt = (ext: unknown): string => (({
  jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', gif: 'image/gif',
  webp: 'image/webp', bmp: 'image/bmp', svg: 'image/svg+xml',
  tif: 'image/tiff', tiff: 'image/tiff', ico: 'image/x-icon',
} as Record<string, string>)[String(ext || '').toLowerCase()] || 'image');

export const atlasFileTreeMetaForPath = (rawPath: unknown): any => {
  const clean = String(rawPath || '').replace(/^\/+/, '');
  if (!clean) return {};
  const parts = clean.split('/').filter(Boolean);
  const currentIp = String((window as any).SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
  const rel = currentIp && parts[0] === currentIp ? parts.slice(1).join('/') : clean;
  const candidates = new Set([clean, rel]);
  if (currentIp && rel) candidates.add(`${currentIp}/${rel}`);
  const entries = Array.isArray((window as any).FILE_TREE) ? (window as any).FILE_TREE : [];
  for (const item of entries) {
    const name = String(item?.name || '').replace(/^\/+/, '');
    if (!name) continue;
    if (candidates.has(name) || (currentIp && candidates.has(`${currentIp}/${name}`))) {
      return item || {};
    }
  }
  return {};
};

export const useAtlasAsyncResource = (kind: string, path: unknown, options: any = {}): [any, (force?: boolean) => Promise<any>] => {
  const key = String(path || '').trim();
  const sessionScope = activeAtlasResourceSession();
  const cacheKey = atlasResourceCacheKey(kind, key, sessionScope);
  const versionKey = String(options.versionKey || '');
  const forceOnVersionChange = !!options.forceOnVersionChange;
  const requestSeq = useRef(0);
  const lastAutoLoad = useRef<{ key: string; sessionScope: string; versionKey: string }>({
    key,
    sessionScope,
    versionKey,
  });
  const [state, setState] = useState<any>(() => cachedAtlasResource(kind, key, sessionScope));

  const reload = useCallback((force = false): Promise<any> => {
    const currentKey = String(path || '').trim();
    const currentSessionScope = activeAtlasResourceSession();
    const seq = requestSeq.current + 1;
    requestSeq.current = seq;
    if (!currentKey) {
      const empty = emptyAtlasResource('', currentSessionScope);
      setState(empty);
      return Promise.resolve(empty);
    }
    const cached = cachedAtlasResource(kind, currentKey, currentSessionScope);
    setState({ ...cached, path: currentKey, loading: true, err: force ? null : cached.err });
    return readAtlasAsyncResource(kind, currentKey, force).then((data: any) => {
      if (requestSeq.current === seq) setState(data);
      return data;
    });
  }, [kind, path, sessionScope]);

  useEffect(() => {
    const previous = lastAutoLoad.current;
    const force = forceOnVersionChange
      && previous.key === key
      && previous.sessionScope === sessionScope
      && previous.versionKey !== versionKey;
    lastAutoLoad.current = { key, sessionScope, versionKey };
    reload(force);
    return () => { requestSeq.current += 1; };
  }, [forceOnVersionChange, key, reload, sessionScope, versionKey]);

  useEffect(() => {
    if (!key) return undefined;
    const syncFromCache = (event: any) => {
      const detail = event?.detail || {};
      if (detail.kind !== kind || detail.path !== key || detail.cacheKey !== cacheKey) return;
      setState(cachedAtlasResource(kind, key, sessionScope));
    };
    const markLoading = (event: any) => {
      const detail = event?.detail || {};
      if (detail.kind !== kind || detail.path !== key || detail.cacheKey !== cacheKey) return;
      setState((prev: any) => {
        const cached = cachedAtlasResource(kind, key, sessionScope);
        return {
          ...prev,
          ...cached,
          body: cached.body || prev.body || '',
          size: cached.size || prev.size || 0,
          path: key,
          loading: true,
          err: cached.err || prev.err || null,
        };
      });
    };
    window.addEventListener('atlas-resource-loaded', syncFromCache);
    window.addEventListener('atlas-resource-loading', markLoading);
    return () => {
      window.removeEventListener('atlas-resource-loaded', syncFromCache);
      window.removeEventListener('atlas-resource-loading', markLoading);
    };
  }, [cacheKey, kind, key, sessionScope]);

  const visibleState = state.path === key && state.sessionScope === sessionScope
    ? state
    : cachedAtlasResource(kind, key, sessionScope);
  return [visibleState, reload];
};
