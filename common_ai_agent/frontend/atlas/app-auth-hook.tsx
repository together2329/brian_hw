// app-auth-hook.tsx — extracted from app.tsx (strangler-fig TS split).
//
// The auth gate: (1) the atlas:auth_required listener that re-checks the HTTP
// cookie before kicking the user to LoginScreen, (2) the /api/users/me mount
// probe that establishes window.ATLAS_USER + the active namespace, and (3) the
// run_policy hydration once authed. These three effects are cohesive (all
// authentication/bootstrap) and only touch App's setters + a couple of pure
// callbacks, so they lift into a custom hook that runs in App's render context
// (behavior identical). The window.ATLAS_USER / ATLAS_USER_SESSION_ID /
// ACTIVE_SESSION bridges move here with the auth logic that owns them.
//
// Typed in the same permissive house style as app-helpers.tsx; the deps bag is
// typed loosely (the App closures it carries are dynamically shaped).
import { useEffect } from 'react';
import type { MutableRefObject, Dispatch, SetStateAction } from 'react';
import {
  atlasShouldHoldDashboardActivation,
  mergeAtlasPolicyResponse,
  normalizeAtlasRunMode,
  normalizeAtlasExecMode,
} from './app-helpers';

export interface AtlasAuthGateDeps {
  WORKFLOW_DEFAULT: string;
  authState: string;
  execMode: string;
  authRequiredProbeRef: MutableRefObject<number>;
  normalizeSession: (value: unknown) => string;
  splitSessionNamespace: (session: unknown) => any;
  setBootSteps: Dispatch<SetStateAction<Record<string, string>>>;
  setAuthState: (v: string) => void;
  setActiveSessionId: (v: string) => void;
  setActiveNamespace: (v: string) => void;
  setActiveIp: (v: string) => void;
  setRunMode: (v: string) => void;
  setExecMode: (v: string) => void;
}

export function useAtlasAuthGate(deps: AtlasAuthGateDeps): void {
  const {
    WORKFLOW_DEFAULT, authState, execMode, authRequiredProbeRef,
    normalizeSession, splitSessionNamespace,
    setBootSteps, setAuthState, setActiveSessionId, setActiveNamespace,
    setActiveIp, setRunMode, setExecMode,
  } = deps;

  useEffect(() => {
    const onAuthRequired = () => {
      setBootSteps(s => (s.ws === 'fail' ? s : { ...s, ws: 'fail' }));
      const probeId = authRequiredProbeRef.current + 1;
      authRequiredProbeRef.current = probeId;
      // A single WebSocket can close with auth_required because it was opened
      // before /api/users/me rebound the tab to the current cookie user, or
      // because a stale owner/IP namespace was still in localStorage. Re-check
      // the HTTP auth cookie before showing LoginScreen, otherwise a live run
      // can be kicked back to the login page by one stale socket close.
      fetch('/api/users/me', { cache: 'no-store', credentials: 'include' })
        .then(r => {
          if (r.ok) return r.json();
          if (r.status === 401 || r.status === 403) return { authFailed: true };
          throw new Error(`auth probe ${r.status}`);
        })
        .then(j => {
          if (authRequiredProbeRef.current !== probeId) return;
          if (j && j.authFailed) {
            setAuthState('unauth');
            return;
          }
          const user = j && j.user;
          if (!user || !user.username) {
            setAuthState('unauth');
            return;
          }
          const username = normalizeSession(user.username) || user.username;
          window.ATLAS_USER = user;
          window.ATLAS_USER_SESSION_ID = username;
          try { localStorage.setItem('atlasUserSessionId', username); } catch (_) {}

          const currentNs = normalizeSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession') || '');
          const currentParts = currentNs
            ? splitSessionNamespace(currentNs)
            : { sessionId: '', ipId: '', workflow: '' };
          const currentBelongsToUser = currentNs && currentParts.sessionId === username;
          const defaultWorkflow = execMode === 'orchestrator' ? 'orchestrator' : WORKFLOW_DEFAULT;
          const sourceNs = currentBelongsToUser
            ? currentNs
            : `${username}/${WORKFLOW_DEFAULT}/${WORKFLOW_DEFAULT}/${defaultWorkflow}`;
          const sourceParts = splitSessionNamespace(sourceNs);
          const workspaceSession = normalizeSession(sourceParts.workspaceSession || '') || WORKFLOW_DEFAULT;
          const recoveredNs = `${username}/${workspaceSession}/${sourceParts.ipId || WORKFLOW_DEFAULT}/${sourceParts.workflow || defaultWorkflow}`;
          const recoveredParts = splitSessionNamespace(recoveredNs);
          window.ACTIVE_SESSION = recoveredNs;
          (window as any).ATLAS_WORKSPACE_SESSION_ID = workspaceSession;
          try {
            localStorage.setItem('atlasActiveSession', recoveredNs);
            localStorage.setItem('atlasWorkspaceSessionId', workspaceSession);
          } catch (_) {}
          setActiveSessionId(username);
          setActiveNamespace(recoveredNs);
          setActiveIp(recoveredParts.ipId || WORKFLOW_DEFAULT);
          setAuthState('authed');
          setBootSteps(s => (s.ws === 'fail' ? { ...s, ws: 'pending' } : s));

          if (window.backend) {
            try {
              if (typeof window.backend.switchSession === 'function') {
                window.backend.switchSession(recoveredNs);
              } else if (typeof window.backend.connect === 'function') {
                window.backend.connect(recoveredNs);
              }
            } catch (_) {}
          }
          fetch('/api/session/activate', {
            method: 'POST',
            credentials: 'include',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                owner: username,
                workspace_session: recoveredParts.workspaceSession || workspaceSession || WORKFLOW_DEFAULT,
                ip: recoveredParts.ipId || WORKFLOW_DEFAULT,
                workflow: recoveredParts.workflow || WORKFLOW_DEFAULT,
                preserve_running: true,
            }),
          }).catch(() => {});
        })
        .catch(() => {
          if (authRequiredProbeRef.current === probeId) {
            setBootSteps(s => (s.ws === 'fail' ? s : { ...s, ws: 'fail' }));
          }
        });
    };
    try { window.addEventListener('atlas:auth_required', onAuthRequired); } catch (_) {}
    return () => {
      try { window.removeEventListener('atlas:auth_required', onAuthRequired); } catch (_) {}
    };
  }, [execMode, normalizeSession, splitSessionNamespace]);
  useEffect(() => {
    let cancelled = false;
    fetch('/api/users/me', { cache: 'no-store' })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(j => {
        if (cancelled) return;
        const user = j && j.user;
        if (!user || !user.username) { setAuthState('unauth'); return; }
        window.ATLAS_USER = user;
        window.ATLAS_USER_SESSION_ID = user.username;
        try {
          const username = normalizeSession(user.username) || user.username;
          const url = new URL(window.location.href);
          const urlSession = normalizeSession(url.searchParams.get('session') || '');
          // splitSessionNamespace('') yields {sessionId:'default', ipId:'default',
          // workflow:'default'} — treating those as authoritative would
          // overwrite a real ?ip= deep link with 'default'. Only consult the
          // parsed namespace when ?session= was actually present.
          const urlParts = urlSession
            ? splitSessionNamespace(urlSession)
            : { sessionId: '', ipId: '', workflow: '' };
          const workspaceParam = normalizeSession(
            urlParts.workspaceSession
            || url.searchParams.get('workspace_session')
            || url.searchParams.get('workspace')
            || (window as any).ATLAS_WORKSPACE_SESSION_ID
            || localStorage.getItem('atlasWorkspaceSessionId')
            || ''
          );
          const ipParam = normalizeSession(url.searchParams.get('ip') || url.searchParams.get('ip_id') || '');
          const wfParam = normalizeSession(url.searchParams.get('workflow') || url.searchParams.get('wf') || '');
          const requestedIp = ipParam || normalizeSession(urlParts.ipId || '');
          const requestedWf = wfParam || normalizeSession(urlParts.workflow || '');
          const hasUrlContext = !!(urlSession || requestedIp || requestedWf);
          const holdDashboardActivation = atlasShouldHoldDashboardActivation();
          const currentNs = normalizeSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession') || '');
          const currentOwner = (currentNs.split('/').filter(Boolean)[0] || '');
          const ownerMismatch = !!(currentOwner && currentOwner !== username);
          localStorage.setItem('atlasUserSessionId', username);
          if (hasUrlContext || (!holdDashboardActivation && (!currentNs || currentNs === 'default' || ownerMismatch))) {
            const currentParts = currentNs
              ? splitSessionNamespace(currentNs)
              : { sessionId: '', ipId: '', workflow: '' };
            const defaultWorkflow = execMode === 'orchestrator' ? 'orchestrator' : WORKFLOW_DEFAULT;
            const savedWorkflow = (!ownerMismatch && currentParts.workflow && currentParts.workflow !== WORKFLOW_DEFAULT)
              ? currentParts.workflow
              : '';
            const nextWorkspace = workspaceParam || (!ownerMismatch ? currentParts.workspaceSession : '') || WORKFLOW_DEFAULT;
            const nextIp = requestedIp || (!ownerMismatch ? currentParts.ipId : '') || WORKFLOW_DEFAULT;
            const nextWf = requestedWf || savedWorkflow || defaultWorkflow;
            const nextNs = `${username}/${nextWorkspace}/${nextIp}/${nextWf}`;
            window.ACTIVE_SESSION = nextNs;
            (window as any).ATLAS_WORKSPACE_SESSION_ID = nextWorkspace;
            localStorage.setItem('atlasActiveSession', nextNs);
            localStorage.setItem('atlasWorkspaceSessionId', nextWorkspace);
            setActiveSessionId(username);
            setActiveNamespace(nextNs);
            setActiveIp(nextIp);
            url.searchParams.set('session', nextNs);
            url.searchParams.set('session_id', username);
            url.searchParams.set('workspace_session', nextWorkspace);
            url.searchParams.set('ip', nextIp);
            url.searchParams.set('workflow', nextWf);
            url.searchParams.delete('ip_id');
            url.searchParams.delete('wf');
            window.history.replaceState(null, '', url);
          } else if (holdDashboardActivation) {
            setActiveSessionId(username);
            window.ACTIVE_SESSION = '';
            localStorage.removeItem('atlasActiveSession');
            setActiveNamespace('');
            setActiveIp(WORKFLOW_DEFAULT);
            url.searchParams.delete('session');
            url.searchParams.delete('session_id');
            url.searchParams.delete('workspace_session');
            url.searchParams.delete('workspace');
            url.searchParams.delete('ip');
            url.searchParams.delete('ip_id');
            url.searchParams.delete('workflow');
            url.searchParams.delete('wf');
            window.history.replaceState(null, '', url);
          }
          const activeForBackend = normalizeSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession') || '');
          if (activeForBackend) {
            if (window.backend) {
              if (typeof window.backend.switchSession === 'function') {
                window.backend.switchSession(activeForBackend);
              } else if (typeof window.backend.connect === 'function') {
                window.backend.connect(activeForBackend);
              }
            }
            const parsed = splitSessionNamespace(activeForBackend);
            fetch('/api/session/activate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                owner: username || parsed.sessionId,
                workspace_session: parsed.workspaceSession || WORKFLOW_DEFAULT,
                ip: parsed.ipId || 'default',
                workflow: parsed.workflow || 'default',
              }),
            }).then(() => {
              try { return window.atlasData && window.atlasData.refreshHealth && window.atlasData.refreshHealth(); }
              catch (_) { return null; }
            }).catch(() => {});
          }
        } catch (_) {
          try { localStorage.setItem('atlasUserSessionId', user.username); } catch (_) {}
        }
        setAuthState('authed');
      })
      .catch(() => { if (!cancelled) setAuthState('unauth'); });
    return () => { cancelled = true; };
  }, []);
  useEffect(() => {
    if (authState !== 'authed') return undefined;
    let dead = false;
    fetch('/api/pipeline/run_policy', { cache: 'no-store' })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(j => {
        if (dead || !j) return;
        mergeAtlasPolicyResponse(j);
        if (j.run_mode) setRunMode(normalizeAtlasRunMode(j.run_mode));
        if (j.exec_mode) setExecMode(normalizeAtlasExecMode(j.exec_mode));
      })
      .catch(() => {});
    return () => { dead = true; };
  }, [authState]);
}
