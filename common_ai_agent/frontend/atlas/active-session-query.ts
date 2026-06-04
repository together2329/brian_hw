interface ActiveSessionWindow {
  readonly atlasData?: {
    readonly normalizeSessionName?: (session: unknown) => string;
  };
  readonly normalizeAtlasSessionName?: (session: unknown) => string;
  readonly ACTIVE_SESSION?: unknown;
  readonly ATLAS_USER?: {
    readonly username?: string;
  };
  readonly ATLAS_USER_SESSION_ID?: string;
  readonly ATLAS_WORKSPACE_SESSION_ID?: string;
  readonly ATLAS_EXEC_MODE?: string;
  readonly ATLAS_DEFAULT_EXEC_MODE?: string;
  readonly ATLAS_BOOT_CONFIG?: {
    readonly exec_mode?: string;
  };
}

const sessionWin = window as ActiveSessionWindow;

const cleanSegment = (value: unknown): string => String(value || '').trim().replace(/^\/+|\/+$/g, '');

const normalizeSession = (value: unknown): string => {
  const raw = cleanSegment(value);
  if (!raw) return '';
  const normalizer = sessionWin.atlasData?.normalizeSessionName || sessionWin.normalizeAtlasSessionName;
  if (!normalizer) return raw;
  try {
    return cleanSegment(normalizer(raw)) || raw;
  } catch (_err) {
    return raw;
  }
};

const currentUsername = (): string =>
  cleanSegment(sessionWin.ATLAS_USER?.username || sessionWin.ATLAS_USER_SESSION_ID || 'validator') || 'validator';

const currentWorkspaceSession = (url: URLSearchParams): string => {
  const storedWorkspace = (() => {
    try {
      return localStorage.getItem('atlasWorkspaceSessionId') || '';
    } catch (_err) {
      return '';
    }
  })();
  return normalizeSession(
    url.get('workspace_session')
      || url.get('workspace')
      || sessionWin.ATLAS_WORKSPACE_SESSION_ID
      || storedWorkspace
      || 'default',
  ) || 'default';
};

const defaultWorkflow = (): string => {
  const mode = String(
    sessionWin.ATLAS_EXEC_MODE
      || sessionWin.ATLAS_DEFAULT_EXEC_MODE
      || sessionWin.ATLAS_BOOT_CONFIG?.exec_mode
      || '',
  ).trim().toLowerCase();
  return mode === 'orchestrator' ? 'orchestrator' : 'default';
};

export const activeSessionForRequest = (): string => {
  try {
    const url = new URLSearchParams(window.location.search);
    const explicitSession = normalizeSession(url.get('session') || url.get('sid') || url.get('namespace') || '');
    const parts = explicitSession.split('/').filter(Boolean);
    if (parts.length >= 4) return explicitSession;

    const username = currentUsername();
    const workspaceSession = currentWorkspaceSession(url);
    if (parts.length === 3) return normalizeSession(`${parts[0]}/${workspaceSession}/${parts[1]}/${parts[2]}`);
    if (parts.length === 2) return normalizeSession(`${username}/${workspaceSession}/${parts[0]}/${parts[1]}`);

    const routeIp = cleanSegment(url.get('ip') || url.get('ip_id') || '');
    if (routeIp && routeIp !== 'default') {
      const workflow = cleanSegment(url.get('workflow') || url.get('wf') || '') || defaultWorkflow();
      return normalizeSession(`${username}/${workspaceSession}/${routeIp}/${workflow}`);
    }

    const activeSession = normalizeSession(sessionWin.ACTIVE_SESSION || '');
    if (activeSession) return activeSession;
    try {
      return normalizeSession(localStorage.getItem('atlasActiveSession') || '');
    } catch (_err) {
      return '';
    }
  } catch (_err) {
    return '';
  }
};

export const appendActiveSessionParam = (params: URLSearchParams): URLSearchParams => {
  const sessionId = activeSessionForRequest();
  if (sessionId) params.set('session_id', sessionId);
  return params;
};
