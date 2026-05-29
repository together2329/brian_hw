// app-screen-hook.tsx — extracted from app.tsx (strangler-fig TS split).
//
// Top-level screen routing + the screen-driven side effects: the screen state
// (with its URL/localStorage seed), the persist effect, the atlas:open_evidence
// and atlas:open_workflow_workspace listeners that switch to Workspace and open
// a chip, the opt-in screen->workflow auto-switch, the document.documentElement
// data-* attribute sync, the page-load /api/control/stop guard, and
// activateDashboardSession. Cohesive (all "what surface is shown + what happens
// when it changes"), so it lifts into a custom hook running in App's render
// context (behavior identical).
//
// Returns screen / setScreen / activateDashboardSession for App to pass to
// AppShell (and for createIp() to flip the surface to Workspace).
//
// Typed in the same permissive house style as app-helpers.tsx; the deps bag is
// typed loosely (the App closures it carries are dynamically shaped).
import { useState, useEffect, useRef, useCallback } from 'react';
import type { Dispatch, SetStateAction } from 'react';

export interface AtlasScreenDeps {
  dir: string;
  theme: string;
  fontMode: string;
  fontScale: string;
  uiLang: string;
  execMode: string;
  WORKFLOW_DEFAULT: string;
  activeIp: string;
  activeNamespace: string;
  activeSessionId: string;
  activateNamespace: (sessionId: unknown, ipId: unknown, workflow: unknown, syncWorkflow?: boolean, opts?: any) => any;
  confirmStopForWorkflowSwitch: (workflow: unknown) => boolean;
  currentWorkflow: () => string;
  loggedInOwner: () => string;
  normalizeSession: (value: unknown) => string;
  splitSessionNamespace: (session: unknown) => any;
}

export function useAtlasScreen(deps: AtlasScreenDeps): {
  screen: string;
  setScreen: Dispatch<SetStateAction<string>>;
  activateDashboardSession: (row: any) => void;
} {
  const {
    dir, theme, fontMode, fontScale, uiLang, execMode, WORKFLOW_DEFAULT,
    activeIp, activeNamespace, activeSessionId, activateNamespace,
    confirmStopForWorkflowSwitch, currentWorkflow, loggedInOwner,
    normalizeSession, splitSessionNamespace,
  } = deps;

  // Top-level screen — 'workspace' is the default landing surface because
  // Chat is the primary Atlas interaction. The dashboard remains available
  // as an explicit screen.
  //
  // 'dashboard' (user landing), 'workspace' (live
  // agent + chat + sidebar), or 'pipeline' (stage dispatcher).
  // Old 'architect' value (mock-data SoC view) migrates to 'pipeline'
  // on first load so existing sessions don't get stranded on a screen
  // that no longer exists.
  const [screen, setScreen] = useState(() => {
    try {
      const params = new URLSearchParams(window.location.search || '');
      const urlView = (params.get('view') || '').trim().toLowerCase();
      const hasUrlContext = !!(
        params.get('session') ||
        params.get('session_id') ||
        params.get('ip') ||
        params.get('ip_id') ||
        params.get('workflow') ||
        params.get('wf')
      );
      // Explicit ?view=pipeline / ?view=architect still honored so
      // deep links keep working. Without URL context, land on Workspace
      // Chat instead of restoring dashboard/pipeline from a prior visit.
      if (urlView === 'dashboard' || urlView === 'workspace' || urlView === 'pipeline' || urlView === 'architect' || urlView === 'guide') return urlView;
      const saved = localStorage.atlasScreen;
      if (hasUrlContext && (saved === 'dashboard' || saved === 'workspace' || saved === 'pipeline' || saved === 'architect' || saved === 'guide')) return saved;
      return 'workspace';
    } catch (_) { return 'workspace'; }
  });
  useEffect(() => {
    try { localStorage.atlasScreen = screen; } catch (_) {}
  }, [screen]);
  const workflowWorkspaceOpenRef = useRef(false);

  useEffect(() => {
    const onOpenEvidence = (ev: any) => {
      const path = String(ev?.detail?.path || '').trim();
      if (!path) return;
      try { localStorage.setItem('atlasPreviewPath', path); } catch (_) {}
      setScreen('workspace');
      setTimeout(() => {
        try {
          window.dispatchEvent(new CustomEvent('atlas-chip-open', {
            detail: { path, source: ev?.detail?.source || 'pipeline' },
          }));
        } catch (_) {}
      }, 0);
    };
    window.addEventListener('atlas:open_evidence', onOpenEvidence);
    return () => window.removeEventListener('atlas:open_evidence', onOpenEvidence);
  }, []);

  useEffect(() => {
    const onOpenWorkflowWorkspace = (ev: any) => {
      const detail = ev?.detail || {};
      const workflow = normalizeSession(detail.workflow || '');
      if (!workflow) return;
      const parsed = splitSessionNamespace(window.ACTIVE_SESSION || activeNamespace || '');
      const owner = loggedInOwner() || normalizeSession(
        detail.sessionId ||
        parsed.sessionId ||
        activeSessionId ||
        window.ATLAS_USER_SESSION_ID ||
        (window.ATLAS_USER && window.ATLAS_USER.username) ||
        'default'
      ) || 'default';
      const ip = normalizeSession(
        detail.ip ||
        parsed.ipId ||
        activeIp ||
        window.SCOPE_PATH ||
        WORKFLOW_DEFAULT
      ) || WORKFLOW_DEFAULT;
      const path = String(detail.path || '').trim();
      const activeWorkflow = normalizeSession(parsed.workflow || currentWorkflow() || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
      // In orchestrator + multi-worker mode, pipeline worker cards are
      // workspace switches, not single-worker stop/restart boundaries.
      const preserveRunning = (
        detail.source === 'pipeline'
        && workflow !== activeWorkflow
        && (activeWorkflow === 'orchestrator' || execMode === 'orchestrator')
      );

      workflowWorkspaceOpenRef.current = true;
      if (!preserveRunning && !confirmStopForWorkflowSwitch(workflow)) return;
      activateNamespace(owner, ip, workflow, true, { preserveRunning });
      setScreen('workspace');
      if (path) {
        try { localStorage.setItem('atlasPreviewPath', path); } catch (_) {}
        setTimeout(() => {
          try {
            window.dispatchEvent(new CustomEvent('atlas-chip-open', {
              detail: { path, source: detail.source || 'pipeline' },
            }));
          } catch (_) {}
        }, 0);
      }
    };
    window.addEventListener('atlas:open_workflow_workspace', onOpenWorkflowWorkspace);
    return () => window.removeEventListener('atlas:open_workflow_workspace', onOpenWorkflowWorkspace);
  }, [
    activeIp,
    activeNamespace,
    activeSessionId,
    activateNamespace,
    confirmStopForWorkflowSwitch,
    currentWorkflow,
    execMode,
    loggedInOwner,
    normalizeSession,
    splitSessionNamespace,
  ]);

  // Screen-change → workflow auto-switch is OPT-IN. By default the
  // user's workflow / IP / session are manual. Pipeline and Architect
  // screens previously force-switched the workflow to 'orchestrator' /
  // 'architect' on enter and back to 'default' on exit, which surprised
  // users who wanted the workflow they explicitly picked to stick.
  // Re-enable via:
  //   localStorage.setItem('atlasArchAutoSwitch', 'on')
  const prevScreenRef = useRef(screen);
  useEffect(() => {
    const prev = prevScreenRef.current;
    if (prev === screen) return;
    prevScreenRef.current = screen;
    if (!window.backend || typeof window.backend.send !== 'function') return;
    const optIn = (() => { try { return localStorage.getItem('atlasArchAutoSwitch') === 'on'; }
                           catch (_) { return false; } })();
    if (!optIn) return;
    if (screen === 'architect' || screen === 'pipeline') {
      const targetWorkflow = screen === 'pipeline' ? 'orchestrator' : 'architect';
      activateNamespace(activeSessionId, activeIp || WORKFLOW_DEFAULT, targetWorkflow, true, {
        preserveRunning: execMode === 'orchestrator' && targetWorkflow === 'orchestrator',
      });
    } else if (prev === 'architect' || prev === 'pipeline') {
      if (workflowWorkspaceOpenRef.current) {
        workflowWorkspaceOpenRef.current = false;
        return;
      }
      if (prev === 'pipeline' && execMode === 'orchestrator') return;
      activateNamespace(activeSessionId, activeIp || WORKFLOW_DEFAULT, WORKFLOW_DEFAULT, true, {
        preserveRunning: execMode === 'orchestrator' && prev === 'pipeline',
      });
    }
  }, [activateNamespace, activeIp, activeSessionId, execMode, screen, uiLang]);

  const activateDashboardSession = useCallback((row: any) => {
    const rowNamespace = normalizeSession(String((row && row.id) || ''));
    const parsed = rowNamespace
      ? splitSessionNamespace(rowNamespace)
      : { sessionId: '', ipId: '', workflow: '' };
    const currentNamespace = normalizeSession(
      window.ACTIVE_SESSION ||
      activeNamespace ||
      (() => { try { return localStorage.getItem('atlasActiveSession') || ''; } catch (_) { return ''; } })()
    );
    const current = currentNamespace
      ? splitSessionNamespace(currentNamespace)
      : { sessionId: '', ipId: '', workflow: '' };
    const owner = loggedInOwner() || normalizeSession(
      parsed.sessionId ||
      current.sessionId ||
      activeSessionId ||
      window.ATLAS_USER_SESSION_ID ||
      (window.ATLAS_USER && window.ATLAS_USER.username) ||
      'default'
    ) || 'default';
    const ip = normalizeSession(
      (row && row.ip) ||
      parsed.ipId ||
      current.ipId ||
      activeIp ||
      WORKFLOW_DEFAULT
    ) || WORKFLOW_DEFAULT;
    const workflow = normalizeSession(
      (row && row.workflow) ||
      parsed.workflow ||
      current.workflow ||
      currentWorkflow() ||
      WORKFLOW_DEFAULT
    ) || WORKFLOW_DEFAULT;
    activateNamespace(owner, ip, workflow, true, {
      preserveRunning: execMode === 'orchestrator',
    });
  }, [activeIp, activeNamespace, activeSessionId, activateNamespace, currentWorkflow, execMode, loggedInOwner, normalizeSession, splitSessionNamespace]);

  useEffect(() => {
    document.documentElement.setAttribute('data-dir', dir);
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-font', fontMode);
    document.documentElement.setAttribute('data-font-scale', fontScale);
  }, [dir, theme, fontMode, fontScale]);

  // Page-load stop guard. Whenever the App mounts (fresh reload, new
  // tab) we fire /api/control/stop so any agent run left over from a
  // prior session halts immediately, instead of resuming for 1000
  // iterations under the user's nose. The backend handler is
  // idempotent — sending stop when nothing is running is a no-op.
  // Followed by a /healthz refresh so the workspace state visible in
  // the UI matches whatever the backend ended up settling on.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await fetch('/api/control/stop', {
          method: 'POST',
          cache: 'no-store',
          keepalive: true,
        });
      } catch (_) {}
      if (cancelled) return;
      // Immediately re-read /healthz so the UI's session/ip/workflow
      // chips reflect the post-stop server state.
      try {
        if (window.atlasData && typeof window.atlasData.refreshHealth === 'function') {
          await window.atlasData.refreshHealth();
        }
      } catch (_) {}
    })();
    return () => { cancelled = true; };
  }, []);

  return { screen, setScreen, activateDashboardSession };
}
