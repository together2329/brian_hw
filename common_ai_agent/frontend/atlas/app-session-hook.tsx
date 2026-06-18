// app-session-hook.tsx — extracted from app.tsx (strangler-fig TS split).
//
// The session-roster + namespace-sync cluster: refreshTopTargets (rebuilds the
// user/ip dropdown rosters from /api/session/list + /api/ip/list), the
// /healthz-tick syncCurrent listener that snaps the UI triple to the backend's
// reported (sid, ip, wf), the URL/localStorage -> backend handshake that fires
// once after auth, and the atlas-session-switched listener. These are a tight
// cohesive group (syncCurrent and onSwitch both call refreshTopTargets), so
// they lift into a custom hook that runs in App's render context (behavior
// identical). The window.IP_OPTIONS / ACTIVE_SESSION / ACTIVE_IP bridges move
// here with the logic that owns them.
//
// Returns refreshTopTargets so App's createIp() can still trigger a roster
// refresh after scaffolding a new IP.
//
// Typed in the same permissive house style as app-helpers.tsx; the deps bag is
// typed loosely (the App closures it carries are dynamically shaped).
import { useCallback, useMemo, useEffect, useRef } from 'react';
import type { MutableRefObject, Dispatch, SetStateAction } from 'react';
import { atlasShouldHoldDashboardActivation } from './app-helpers';

export interface AtlasSessionSyncDeps {
  WORKFLOW_DEFAULT: string;
  TOP_WORKFLOWS: Set<string>;
  authState: string;
  activeIp: string;
  activeNamespace: string;
  activeSessionId: string;
  initialUrlNamespaceRef: MutableRefObject<string>;
  userPickAtRef: MutableRefObject<number>;
  loggedInOwner: () => string;
  normalizeSession: (value: unknown) => string;
  splitSessionNamespace: (session: unknown) => any;
  namespaceFor: (sessionId: unknown, ipId: unknown, workflow: unknown) => string;
  currentWorkflow: () => string;
  workflowForExecMode: (workflow: unknown) => string;
  applySessionMeta: (payload: any, fallbackNamespace?: unknown) => any;
  syncNamespaceUrl: (namespace: unknown, owner: unknown, ip: unknown, workflow: unknown) => void;
  activateNamespace: (sessionId: unknown, ipId: unknown, workflow: unknown, syncWorkflow?: boolean, opts?: any) => any;
  setSessionIdOptions: Dispatch<SetStateAction<string[]>>;
  setIpOptions: Dispatch<SetStateAction<string[]>>;
  setActiveSessionId: (v: string) => void;
  setActiveNamespace: (v: string) => void;
  setActiveIp: (v: string) => void;
}

const sameStringList = (left: readonly string[] = [], right: readonly string[] = []): boolean => (
  left.length === right.length && left.every((value, index) => value === right[index])
);

const commitStringList = (prev: string[], next: string[]): string[] => (
  sameStringList(prev || [], next) ? prev : next
);

const commitIpList = (prev: string[], next: string[]): string[] => {
  window.IP_OPTIONS = next;
  return commitStringList(prev, next);
};

export function useAtlasSessionSync(deps: AtlasSessionSyncDeps): {
  refreshTopTargets: () => Promise<void>;
} {
  const {
    WORKFLOW_DEFAULT, TOP_WORKFLOWS, authState, activeIp, activeNamespace, activeSessionId,
    initialUrlNamespaceRef, userPickAtRef,
    loggedInOwner, normalizeSession, splitSessionNamespace, namespaceFor,
    currentWorkflow, workflowForExecMode, applySessionMeta, syncNamespaceUrl, activateNamespace,
    setSessionIdOptions, setIpOptions, setActiveSessionId, setActiveNamespace, setActiveIp,
  } = deps;

  const RESERVED_IP_NAMES = useMemo(
    () => new Set(['soc', 'user', ...TOP_WORKFLOWS]),
    [TOP_WORKFLOWS]
  );
  const refreshEpochRef = useRef(0);
  const rosterScopeFor = useCallback((namespace: unknown): string => {
    const parsed = splitSessionNamespace(normalizeSession(namespace || ''));
    const owner = normalizeSession(parsed.sessionId || '');
    const workspaceSession = normalizeSession(parsed.workspaceSession || '') || 'default';
    return owner ? `${owner}/${workspaceSession}` : '';
  }, [normalizeSession, splitSessionNamespace]);
  const resetIpRoster = useCallback(() => {
    const fallback = [WORKFLOW_DEFAULT];
    setIpOptions(prev => commitIpList(prev, fallback));
  }, [WORKFLOW_DEFAULT, setIpOptions]);
  const invalidateRosterRefreshes = useCallback(() => {
    refreshEpochRef.current += 1;
  }, []);

  const refreshTopTargets = useCallback(async () => {
    const refreshEpoch = refreshEpochRef.current + 1;
    refreshEpochRef.current = refreshEpoch;
    const isCurrentRefresh = () => refreshEpoch === refreshEpochRef.current;
    const currentUserSession = loggedInOwner()
      || normalizeSession(window.ATLAS_USER_SESSION_ID || activeSessionId);
    const ownerScopedRoster = authState === 'authed' && !!currentUserSession;
    const browserLocalRosterAllowed = !ownerScopedRoster && authState !== 'checking';
    const nextSessionIds = new Set(['default']);
    const holdActivation = atlasShouldHoldDashboardActivation();
    const nextIps = new Set([WORKFLOW_DEFAULT]);
    const acceptIp = (id: string) => id && (id === WORKFLOW_DEFAULT || !RESERVED_IP_NAMES.has(id));
    const rememberedNamespace = normalizeSession(
      window.ACTIVE_SESSION ||
      activeNamespace ||
      (() => { try { return localStorage.getItem('atlasActiveSession') || ''; } catch (_) { return ''; } })()
    );
    const rememberedParts = splitSessionNamespace(rememberedNamespace);
    const rememberedBelongsToCurrentUser = !!(
      rememberedParts.sessionId &&
      (!currentUserSession || rememberedParts.sessionId === currentUserSession)
    );
    const workspaceSessionForRoster = normalizeSession(
      (rememberedBelongsToCurrentUser ? rememberedParts.workspaceSession : '')
      || (browserLocalRosterAllowed ? (window as any).ATLAS_WORKSPACE_SESSION_ID : '')
      || 'default'
    ) || 'default';
    const refreshRosterScope = currentUserSession ? `${currentUserSession}/${workspaceSessionForRoster}` : '';
    const isCurrentRosterScope = () => {
      if (!refreshRosterScope) return true;
      const liveNamespaceForScope = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '');
      const liveScope = rosterScopeFor(liveNamespaceForScope);
      if (ownerScopedRoster && currentUserSession) {
        const authOwnerNow = loggedInOwner() || normalizeSession(window.ATLAS_USER_SESSION_ID || '');
        if (authOwnerNow && authOwnerNow !== currentUserSession) return false;
        const liveParts = splitSessionNamespace(liveNamespaceForScope);
        const liveOwner = normalizeSession(liveParts.sessionId || '');
        if (liveOwner && liveOwner !== currentUserSession) return true;
      }
      return !liveScope || liveScope === refreshRosterScope;
    };
    const isCurrentScopedRefresh = () => isCurrentRefresh() && isCurrentRosterScope();
    if ((browserLocalRosterAllowed || rememberedBelongsToCurrentUser) && rememberedParts.workspaceSession) {
      nextSessionIds.add(rememberedParts.workspaceSession);
    }
    const rememberedIp = rememberedParts.ipId === 'soc' ? WORKFLOW_DEFAULT : rememberedParts.ipId;
    if (browserLocalRosterAllowed && acceptIp(rememberedIp)) nextIps.add(rememberedIp);
    if (browserLocalRosterAllowed && acceptIp(activeIp)) nextIps.add(activeIp);
    try {
      const r = await fetch('/api/session/list', { cache: 'no-store' });
      if (!isCurrentScopedRefresh()) return;
      if (r.ok) {
        const d = await r.json();
        if (!isCurrentScopedRefresh()) return;
        for (const row of (Array.isArray(d.sessions) ? d.sessions : [])) {
          const raw = (row && row.session) || '';
          const segments = String(raw).split('/').filter(Boolean);
          const parsed = splitSessionNamespace(raw);
          if (parsed.sessionId && (!currentUserSession || parsed.sessionId === currentUserSession)) {
            nextSessionIds.add(parsed.workspaceSession || 'default');
          }
          // Only surface an IP if the on-disk namespace explicitly
          // names an owner (i.e. 3-segment <owner>/<ip>/<wf>). Legacy
          // 2-segment <ip>/<wf> trees parse to {sessionId:'default'},
          // and pre-owner backends used to drop bare-IP dirs that
          // still linger on disk; we don't want them in *this* user's
          // dropdown. Also require the parsed owner to match the
          // current user_session — backend is per-user (operator runs
          // one process per user), so cross-owner pollution is noise.
          if (segments.length < 3) continue;
          // /api/session/list still feeds SESSION_ID. We deliberately
          // stopped collecting IPs from it because the dropdown should
          // reflect what's literally on disk under PROJECT_ROOT, not
          // every IP that ever showed up in a session namespace.
        }
      }
    } catch (_) {}
    // Backend IP roster is authoritative for IP_ID. In multi-user mode this
    // is DB/session scoped by the authenticated owner; do not mix in stale
    // browser-local IPs from another login.
    let ipListOk = false;
    const backendIps = new Set([WORKFLOW_DEFAULT]);
    try {
      const ipScope = normalizeSession(
        currentUserSession ? `${currentUserSession}/${workspaceSessionForRoster}` : ''
      );
      const ipUrl = '/api/ip/list' + (ipScope ? `?session_id=${encodeURIComponent(ipScope)}` : '');
      const r2 = await fetch(ipUrl, { cache: 'no-store' });
      if (!isCurrentScopedRefresh()) return;
      if (r2.ok) {
        ipListOk = true;
        const d2 = await r2.json();
        if (!isCurrentScopedRefresh()) return;
        for (const it of (Array.isArray(d2.items) ? d2.items : [])) {
          const name = normalizeSession(it && it.name);
          if (acceptIp(name)) {
            nextIps.add(name);
            backendIps.add(name);
          }
        }
      }
    } catch (_) {}
    const ipAllowedForCurrentUser = (id: string) => {
      const ip = normalizeSession(id === 'soc' ? WORKFLOW_DEFAULT : id);
      if (!ip || ip === WORKFLOW_DEFAULT) return true;
      if (!acceptIp(ip)) return false;
      if (!ownerScopedRoster) return true;
      return ipListOk && backendIps.has(ip);
    };
    if (!isCurrentScopedRefresh()) return;

    let liveNamespace = holdActivation
      ? ''
      : (normalizeSession(window.ACTIVE_SESSION || activeNamespace) || namespaceFor(currentUserSession, activeIp, currentWorkflow()));
    if (liveNamespace && currentUserSession) {
      const liveParts = splitSessionNamespace(liveNamespace);
      if (liveParts.sessionId && liveParts.sessionId !== currentUserSession) {
        liveNamespace = namespaceFor(
          currentUserSession,
          WORKFLOW_DEFAULT,
          liveParts.workflow || currentWorkflow() || WORKFLOW_DEFAULT
        );
        window.ACTIVE_SESSION = liveNamespace;
        try { localStorage.setItem('atlasActiveSession', liveNamespace); } catch (_) {}
      }
    }
    let parsedLive = splitSessionNamespace(liveNamespace);
    const initialUrlStillOwnsLiveRoute = !!(
      liveNamespace &&
      normalizeSession(initialUrlNamespaceRef.current || '') === liveNamespace
    );
    const healthzConfirmsLiveRoute = (() => {
      if (!liveNamespace) return false;
      try {
        const ctx = window.CONTEXT || {};
        const ctxSession = normalizeSession(ctx.active_session || ctx.activeSession || '');
        if (!ctxSession || ctxSession !== liveNamespace) return false;
        const ctxIp = normalizeSession(ctx.active_ip || ctx.activeIp || '');
        const ctxWorkflow = normalizeSession(
          ctx.active_workflow || ctx.activeWorkflow || ctx.workspace || ''
        );
        const liveIp = parsedLive.ipId === 'soc' ? WORKFLOW_DEFAULT : (parsedLive.ipId || WORKFLOW_DEFAULT);
        const liveWorkflow = parsedLive.workflow || WORKFLOW_DEFAULT;
        return (!ctxIp || ctxIp === liveIp) && (!ctxWorkflow || ctxWorkflow === liveWorkflow);
      } catch (_) {
        return false;
      }
    })();
    if (
      liveNamespace &&
      !ipAllowedForCurrentUser(parsedLive.ipId) &&
      !initialUrlStillOwnsLiveRoute &&
      !healthzConfirmsLiveRoute
    ) {
      const owner = currentUserSession || parsedLive.sessionId || 'default';
      const wf = parsedLive.workflow || currentWorkflow() || WORKFLOW_DEFAULT;
      liveNamespace = namespaceFor(owner, WORKFLOW_DEFAULT, wf);
      parsedLive = splitSessionNamespace(liveNamespace);
      window.ACTIVE_SESSION = liveNamespace;
      try { localStorage.setItem('atlasActiveSession', liveNamespace); } catch (_) {}
    }
    if (!liveNamespace) {
      const sortedSessionIds = Array.from(nextSessionIds).sort((a, b) => {
        if (a === currentUserSession) return -1;
        if (b === currentUserSession) return 1;
        if (a === 'default') return -1;
        if (b === 'default') return 1;
        return a.localeCompare(b);
      });
      setSessionIdOptions(prev => commitStringList(prev, sortedSessionIds));
      const sortedIps = Array.from(nextIps).sort((a, b) => {
        if (a === WORKFLOW_DEFAULT) return -1;
        if (b === WORKFLOW_DEFAULT) return 1;
        return a.localeCompare(b);
      });
      setIpOptions(prev => {
        const merged = new Set(sortedIps);
        if (!ipListOk && !ownerScopedRoster) (prev || []).forEach(ip => { if (acceptIp(ip)) merged.add(ip); });
        const next = Array.from(merged).sort((a, b) => {
          if (a === WORKFLOW_DEFAULT) return -1;
          if (b === WORKFLOW_DEFAULT) return 1;
          return a.localeCompare(b);
        });
        return commitIpList(prev, next);
      });
      setActiveSessionId(currentUserSession || 'default');
      setActiveNamespace('');
      setActiveIp(
        ipAllowedForCurrentUser(activeIp) && activeIp && activeIp !== WORKFLOW_DEFAULT
          ? activeIp
          : WORKFLOW_DEFAULT
      );
      return;
    }
    if (parsedLive.sessionId && (!currentUserSession || parsedLive.sessionId === currentUserSession)) {
      nextSessionIds.add(parsedLive.workspaceSession || 'default');
    }
    // Don't auto-include parsedLive.ipId: when the user deletes a
    // session on disk (rm -rf .session/<owner>/<ip>/<wf>) the
    // localStorage cached ACTIVE_SESSION still parses to the dead
    // ip, and this line used to keep adding it to the dropdown
    // forever. Now the dropdown reflects only what /api/session/list
    // and /api/soc actually have, plus whatever createIp() seeded
    // locally (which sticks for one render cycle, then naturally
    // drops if it never lands on disk).
    const sortedSessionIds = Array.from(nextSessionIds).sort((a, b) => {
      if (a === currentUserSession) return -1;
      if (b === currentUserSession) return 1;
      if (a === 'default') return -1;
      if (b === 'default') return 1;
      return a.localeCompare(b);
    });
    setSessionIdOptions(prev => commitStringList(prev, sortedSessionIds));
    const sortedIps = Array.from(nextIps).sort((a, b) => {
      if (a === WORKFLOW_DEFAULT) return -1;
      if (b === WORKFLOW_DEFAULT) return 1;
      return a.localeCompare(b);
    });
    // Expose for inline-code-chip click validation in workspace.jsx so
    // only IPs confirmed by the backend roster become clickable. In
    // owner-scoped mode a failed roster probe must not preserve another
    // user's previous browser-local list.
    setIpOptions(prev => {
      const merged = new Set(sortedIps);
      if (!ipListOk && !ownerScopedRoster) (prev || []).forEach(ip => { if (acceptIp(ip)) merged.add(ip); });
      const next = Array.from(merged).sort((a, b) => {
        if (a === WORKFLOW_DEFAULT) return -1;
        if (b === WORKFLOW_DEFAULT) return 1;
        return a.localeCompare(b);
      });
      return commitIpList(prev, next);
    });
    setActiveSessionId(currentUserSession || parsedLive.sessionId || 'default');
    setActiveNamespace(liveNamespace);
    setActiveIp(parsedLive.ipId === 'soc' ? WORKFLOW_DEFAULT : (parsedLive.ipId || WORKFLOW_DEFAULT));
  }, [activeIp, activeNamespace, activeSessionId, authState, currentWorkflow, loggedInOwner, namespaceFor, normalizeSession, rosterScopeFor, splitSessionNamespace]);

  useEffect(() => {
    let timer: any = null;
    const syncCurrent = (ev: any) => {
      if (atlasShouldHoldDashboardActivation()) {
        invalidateRosterRefreshes();
        resetIpRoster();
        const authOwner = normalizeSession(
          (window.ATLAS_USER && window.ATLAS_USER.username) ||
          window.ATLAS_USER_SESSION_ID ||
          activeSessionId ||
          'default'
        ) || 'default';
        window.ACTIVE_SESSION = '';
        try { localStorage.removeItem('atlasActiveSession'); } catch (_) {}
        setActiveSessionId(authOwner);
        setActiveNamespace('');
        setActiveIp(WORKFLOW_DEFAULT);
        return;
      }
      const eventSession = normalizeSession(
        (ev && ev.detail && typeof ev.detail === 'object' && ev.detail.session) || ''
      );
      const liveSession = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '');
      if (
        ev &&
        (ev.type === 'atlas-conversation-loaded' || ev.type === 'atlas-session-loaded') &&
        eventSession &&
        liveSession &&
        eventSession !== liveSession
      ) {
        return;
      }
      const scopeBeforeSync = rosterScopeFor(window.ACTIVE_SESSION || activeNamespace || '');
      const ctx = window.CONTEXT || {};
      const ctxSession = normalizeSession(ctx.active_session || ctx.activeSession || '');
      // refreshHealth periodic poll → backend is the ground truth.
      // Snap UI dropdowns to whatever the backend reports as the active
      // (sid, ip, wf), except when backend is still at the boot
      // "default/default/default" placeholder — let the user's
      // localStorage / URL hint own that brief window.
      const isHealthTick = ev && ev.type === 'atlas-data-changed' && ev.detail === 'CONTEXT';
      let namespace;
      if (isHealthTick && ctxSession && ctxSession !== 'default/default/default') {
        const ctxOwner = (ctxSession.split('/').filter(Boolean)[0] || '');
        const authOwner = normalizeSession(
          (window.ATLAS_USER && window.ATLAS_USER.username) ||
          window.ATLAS_USER_SESSION_ID ||
          activeSessionId ||
          ''
        );
        const initialUrlNamespace = normalizeSession(initialUrlNamespaceRef.current || '');
        const parsedUrl = splitSessionNamespace(initialUrlNamespace);
        const parsedCtx = splitSessionNamespace(ctxSession);
        const browserNamespace = normalizeSession(
          window.ACTIVE_SESSION ||
          activeNamespace ||
          (() => { try { return localStorage.getItem('atlasActiveSession') || ''; } catch (_) { return ''; } })()
        );
        const parsedBrowser = splitSessionNamespace(browserNamespace);
        const urlStillOwnsBoot = !!(
          initialUrlNamespace &&
          ctxSession !== initialUrlNamespace &&
          (!parsedUrl.sessionId || !parsedCtx.sessionId || parsedUrl.sessionId === parsedCtx.sessionId)
        );
        const ctxIsDefaultPlaceholder = !!(
          parsedCtx.sessionId &&
          (!parsedCtx.ipId || parsedCtx.ipId === WORKFLOW_DEFAULT) &&
          (!parsedCtx.workflow || parsedCtx.workflow === WORKFLOW_DEFAULT)
        );
        const browserHasRealIp = !!(
          parsedBrowser.sessionId &&
          parsedBrowser.ipId &&
          parsedBrowser.ipId !== WORKFLOW_DEFAULT &&
          parsedBrowser.ipId !== 'soc'
        );
        const browserSameOwner = !!(
          browserNamespace &&
          parsedBrowser.sessionId &&
          (!parsedCtx.sessionId || parsedCtx.sessionId === parsedBrowser.sessionId || parsedBrowser.sessionId === authOwner)
        );
        // During login and fast screen changes, /healthz can briefly report
        // the process bootstrap namespace (often default/<ip>/<wf>). In
        // DB-backed multi-user mode the authenticated user owns the browser
        // namespace, so do not let that stale backend context rewrite the UI
        // back to default and poison the websocket session.
        // Recent user-initiated picks (IP/workflow/session dropdown) win
        // over backend CONTEXT for a brief window. Without this, a /healthz
        // tick firing between the optimistic UI update and the
        // /api/session/activate POST landing on the backend would yank the
        // dropdowns back to the stale triple the backend still reports.
        const userPickIsFresh = (Date.now() - userPickAtRef.current) < 5000;
        if (urlStillOwnsBoot) {
          namespace = initialUrlNamespace;
        } else if (ctxIsDefaultPlaceholder && browserHasRealIp && browserSameOwner) {
          namespace = browserNamespace;
        } else if (authOwner && ctxOwner && ctxOwner !== authOwner && ctxOwner !== 'local-admin') {
          namespace = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '');
        } else if (userPickIsFresh) {
          namespace = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '') || ctxSession;
        } else {
          namespace = ctxSession;
        }
        if (namespace && namespace !== window.ACTIVE_SESSION) {
          window.ACTIVE_SESSION = namespace;
          try { localStorage.setItem('atlasActiveSession', namespace); } catch (_) {}
        }
      } else {
        const requestedSession = normalizeSession(
          (ev && ev.detail && typeof ev.detail === 'object' && ev.detail.session) ||
          window.ACTIVE_SESSION || activeNamespace
        );
        namespace = requestedSession || ctxSession;
      }
      const parsed = splitSessionNamespace(namespace);
      const owner = loggedInOwner() || parsed.sessionId || activeSessionId || 'default';
      const ipSeg = parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : (parsed.ipId || activeIp || WORKFLOW_DEFAULT);
      const wfSeg = parsed.workflow || WORKFLOW_DEFAULT;
      const ownerScope = parsed.workspaceSession ? `${owner}/${parsed.workspaceSession}` : owner;
      const canonicalNamespace = namespaceFor(ownerScope, ipSeg, wfSeg);
      const scopeAfterSync = rosterScopeFor(canonicalNamespace);
      if (scopeBeforeSync && scopeAfterSync && scopeBeforeSync !== scopeAfterSync) {
        invalidateRosterRefreshes();
        resetIpRoster();
      }
      if (canonicalNamespace && canonicalNamespace !== window.ACTIVE_SESSION) {
        window.ACTIVE_SESSION = canonicalNamespace;
        try { localStorage.setItem('atlasActiveSession', canonicalNamespace); } catch (_) {}
      }
      if (initialUrlNamespaceRef.current && canonicalNamespace === normalizeSession(initialUrlNamespaceRef.current)) {
        initialUrlNamespaceRef.current = '';
      }
      setActiveNamespace(canonicalNamespace);
      setActiveSessionId(owner);
      setActiveIp(ipSeg);
      if (isHealthTick && (ctx.dbSessionId || ctx.sessionUid || ctx.sessionLabel)) {
        applySessionMeta({
          db_session_id: ctx.dbSessionId,
          session_uid: ctx.sessionUid,
          session_label: ctx.sessionLabel,
          namespace: canonicalNamespace,
        }, canonicalNamespace);
      }
      // Push the canonical triple into the URL so the address bar
      // never silently disagrees with what the server reports.
      // Without this, reloading after a triple flip kept the OLD
      // ?ip=…&workflow=… params visible even though dropdowns / file
      // tree had pivoted to the new triple.
      try {
        if (canonicalNamespace) syncNamespaceUrl(canonicalNamespace, owner, ipSeg, wfSeg);
      } catch (_) {}
      clearTimeout(timer);
      timer = setTimeout(refreshTopTargets, 150);
    };
    refreshTopTargets();
    window.addEventListener('atlas-session-loaded', syncCurrent);
    window.addEventListener('atlas-conversation-loaded', syncCurrent);
    window.addEventListener('atlas-data-changed', syncCurrent);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('atlas-session-loaded', syncCurrent);
      window.removeEventListener('atlas-conversation-loaded', syncCurrent);
      window.removeEventListener('atlas-data-changed', syncCurrent);
    };
  }, [activeIp, activeNamespace, activeSessionId, applySessionMeta, currentWorkflow, invalidateRosterRefreshes, loggedInOwner, namespaceFor, normalizeSession, refreshTopTargets, resetIpRoster, rosterScopeFor, splitSessionNamespace]);

  useEffect(() => {
    // Don't fire the URL/localStorage → backend handshake before we
    // know who the logged-in user is. Without this guard a stale
    // localStorage entry like "default/sqa/default" left over from a
    // previous run would post /api/session/activate with owner='default'
    // before the auth gate had a chance to rewrite to <user>/default,
    // producing the surprising "prev='', ip='sqa', owner='default'"
    // backend log on first connection.
    if (!window.ATLAS_USER) return;
    if (atlasShouldHoldDashboardActivation()) return;
    const currentNamespace = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '');
    if (!currentNamespace) return;
    const parsed = splitSessionNamespace(currentNamespace);
    if (!parsed.ipId && !parsed.workflow) return;
    // Also bail if the parsed owner is not this user — the auth
    // gate will rewrite localStorage and we'll re-fire then.
    const owner = parsed.sessionId || '';
    if (owner && owner !== (window.ATLAS_USER.username || '')) return;
    activateNamespace(
      parsed.workspaceSession ? `${owner}/${parsed.workspaceSession}` : (parsed.sessionId || activeSessionId || 'default'),
      parsed.ipId || WORKFLOW_DEFAULT,
      parsed.workflow || WORKFLOW_DEFAULT,
      true
    );
    // Run once on mount AFTER auth: this is the URL/localStorage → backend handshake.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authState]);

  useEffect(() => {
    const onSwitch = (ev: any) => {
      const sessionId = ev?.detail?.sessionId;
      const namespace = ev?.detail?.namespace;
      if (!sessionId) return;
      const currentNamespace = normalizeSession(namespace || window.ACTIVE_SESSION || activeNamespace || '');
      const parsed = currentNamespace
        ? splitSessionNamespace(currentNamespace)
        : { sessionId: '', ipId: '', workflow: '' };
      const owner = loggedInOwner() || normalizeSession(parsed.sessionId || sessionId);
      const parsedBelongsToOwner = !!(
        !parsed.sessionId || !owner || parsed.sessionId === owner
      );
      const nextIp = parsedBelongsToOwner
        ? (parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : (parsed.ipId || activeIp || WORKFLOW_DEFAULT))
        : WORKFLOW_DEFAULT;
      const nextWorkflow = workflowForExecMode(parsed.workflow || currentWorkflow() || WORKFLOW_DEFAULT);
      const nextOwnerScope = parsedBelongsToOwner && parsed.workspaceSession
        ? `${owner}/${parsed.workspaceSession}`
        : owner;
      const nextNamespace = currentNamespace && parsedBelongsToOwner && parsed.workflow === nextWorkflow
        ? currentNamespace
        : namespaceFor(nextOwnerScope, nextIp, nextWorkflow);
      const previousScope = rosterScopeFor(window.ACTIVE_SESSION || activeNamespace || '');
      const nextScope = rosterScopeFor(nextNamespace);
      if (previousScope && nextScope && previousScope !== nextScope) {
        invalidateRosterRefreshes();
        resetIpRoster();
      }
      setActiveSessionId(owner);
      setActiveNamespace(nextNamespace);
      setActiveIp(nextIp);
      window.ACTIVE_SESSION = nextNamespace;
      window.ACTIVE_IP = nextIp;
      try { localStorage.setItem('atlasActiveSession', nextNamespace); } catch (_) {}
      if (ev?.detail?.session_uid || ev?.detail?.db_session_id || ev?.detail?.session_label) {
        applySessionMeta(ev.detail, nextNamespace);
      }
      syncNamespaceUrl(
        nextNamespace,
        owner,
        nextIp,
        nextWorkflow
      );
      refreshTopTargets();
    };
    window.addEventListener('atlas-session-switched', onSwitch);
    return () => window.removeEventListener('atlas-session-switched', onSwitch);
  }, [activeIp, activeNamespace, applySessionMeta, currentWorkflow, invalidateRosterRefreshes, loggedInOwner, namespaceFor, normalizeSession, refreshTopTargets, resetIpRoster, rosterScopeFor, splitSessionNamespace, syncNamespaceUrl, workflowForExecMode]);

  useEffect(() => {
    // Worker-initiated workflow switch (/wf, /to-ssot inside the agent).
    // The worker announces the NEW canonical session key via a structured
    // workspace_changed event; follow it through the SAME activate path a
    // dropdown click uses so the dropdown, URL, healthz context, and the
    // next worker spawn all agree. Without this the switch stays a
    // worker-local overlay: the UI keeps showing the old workflow and a
    // respawned worker boots without the new workspace's system prompt.
    //
    // Guards: only worker-sourced events (the activate path emits the same
    // type for UI-initiated switches — following those would loop), only
    // the logged-in owner's namespace (never follow a cross-owner key),
    // and only when the key actually differs from the live one.
    if (!(window as any).backend?.subscribe) return undefined;
    let unsubscribe: (() => void) | undefined;
    try {
      unsubscribe = (window as any).backend.subscribe('workspace_changed', (m: any) => {
        const source = String((m && m.source) || '');
        if (!source.startsWith('worker/')) return;
        const nextNamespace = normalizeSession((m && m.session) || '');
        if (!nextNamespace) return;
        const current = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '');
        if (nextNamespace === current) return;
        const parsed = splitSessionNamespace(nextNamespace);
        const owner = loggedInOwner();
        if (owner && parsed.sessionId && parsed.sessionId !== owner) return;
        const ownerScope = parsed.workspaceSession
          ? `${parsed.sessionId || owner || 'default'}/${parsed.workspaceSession}`
          : (parsed.sessionId || owner || 'default');
        activateNamespace(
          ownerScope,
          parsed.ipId || WORKFLOW_DEFAULT,
          parsed.workflow || WORKFLOW_DEFAULT,
          true,
          { preserveRunning: true }
        );
      });
    } catch (_) {}
    return () => { try { unsubscribe && unsubscribe(); } catch (_) {} };
  }, [activateNamespace, activeNamespace, loggedInOwner, normalizeSession, splitSessionNamespace, WORKFLOW_DEFAULT]);

  return { refreshTopTargets };
}
