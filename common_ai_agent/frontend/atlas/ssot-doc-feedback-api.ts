import type {
  SsotDocChatPrefillContext,
  SsotDocFeedbackResponse,
  SsotDocFeedbackSubmitRequest,
  SsotDocSelectedTarget,
  SsotDocSourceRequest,
  SsotDocSourceResponse,
} from './ssot-doc-feedback-types';

export class SsotDocFeedbackError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SsotDocFeedbackError';
  }
}

function activeSessionId(): string {
  const win = window as any;
  const norm = win.atlasData?.normalizeSessionName || win.normalizeAtlasSessionName;
  try {
    return norm ? norm(win.ACTIVE_SESSION || '') : String(win.ACTIVE_SESSION || '').trim();
  } catch (_) {
    return '';
  }
}

function appendSessionId(params: URLSearchParams): URLSearchParams {
  const sessionId = activeSessionId();
  if (sessionId) params.set('session_id', sessionId);
  return params;
}

export function requireSsotDocSelection(target: SsotDocSelectedTarget | null): SsotDocSelectedTarget {
  if (!target?.path) {
    throw new SsotDocFeedbackError('Select a DOC component first');
  }
  return target;
}

export async function fetchSsotDocSource(request: SsotDocSourceRequest): Promise<SsotDocSourceResponse> {
  const target = requireSsotDocSelection(request.target);
  const qs = appendSessionId(new URLSearchParams({ ip: request.ip, path: target.path }));
  return parseJsonResponse<SsotDocSourceResponse>(
    await fetch(`/api/ssot/doc-source?${qs.toString()}`, { credentials: 'include' }),
  );
}

export async function submitSsotDocFeedback(
  request: SsotDocFeedbackSubmitRequest,
): Promise<SsotDocFeedbackResponse> {
  const target = requireSsotDocSelection(request.target);
  return parseJsonResponse<SsotDocFeedbackResponse>(
    await fetch('/api/ssot/doc-feedback', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ip: request.ip,
        mode: 'feedback',
        section: target.section,
        path: target.path,
        field: request.field || '',
        value: request.value || '',
        comment: request.comment,
        session_id: activeSessionId(),
      }),
    }),
  );
}

export function sourceForSsotDocTarget(
  source: SsotDocSourceResponse | null,
  target: SsotDocSelectedTarget | null,
): SsotDocSourceResponse | null {
  if (!source || !target) return null;
  return source.path === target.path ? source : null;
}

export function buildSsotDocChatPrefillText(context: SsotDocChatPrefillContext): string {
  const selected = context.selectedText?.trim();
  const yaml = String(context.source?.yaml || '').trim();
  const lines = [
    `/to-ssot ${context.ip}`,
    '',
    'DOC feedback selected from SSOT HTML.',
    `Component: ${context.target.label} (${context.target.kind})`,
    `SSOT path: ${context.target.path}`,
  ];
  if (context.source?.ssot_path) lines.push(`Source file: @${context.source.ssot_path}`);
  if (selected) lines.push('', 'Selected DOC text:', selected);
  if (yaml) lines.push('', 'Current SSOT value:', '```yaml', yaml, '```');
  if (context.comment.trim()) lines.push('', 'Requested change:', context.comment.trim());
  return lines.join('\n').trim() + '\n';
}

async function parseJsonResponse<T extends { ok?: boolean; error?: string }>(response: Response): Promise<T> {
  let payload: T;
  try {
    payload = await response.json() as T;
  } catch (err) {
    throw new SsotDocFeedbackError(`invalid JSON response from ${response.url || 'SSOT DOC API'}`);
  }
  if (!response.ok || payload?.ok === false) {
    throw new SsotDocFeedbackError(payload?.error || `SSOT DOC request failed (${response.status})`);
  }
  return payload;
}
