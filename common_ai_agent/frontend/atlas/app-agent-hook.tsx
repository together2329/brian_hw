// app-agent-hook.tsx — extracted from app.tsx (strangler-fig TS split).
//
// Owns the agent-running indicator and the workspace-switch in-flight toast.
// These two pieces of state are tightly coupled (a workspace_changed event
// also clears agentRunning) and both subscribe only to window.backend +
// window.* — they have NO dependency on the rest of App's namespace/auth
// state, so they extract cleanly as a self-contained custom hook.
//
// The hook runs in App's render context (a real React hook), so behavior is
// identical to the inline version. The window.ATLAS_AGENT_RUNNING bridge
// moves here with the symbol that owns it (setAgentRunningState).
//
// Typed in the same permissive house style as app-helpers.tsx —
// window-sourced values are `any` on purpose.
import { useState, useCallback, useEffect, useRef } from 'react';
import type { MutableRefObject, Dispatch, SetStateAction } from 'react';

export interface AtlasAgentRunning {
  agentRunning: boolean;
  agentRunningRef: MutableRefObject<boolean>;
  setAgentRunningState: (running: unknown) => void;
  wfSwitching: any;
  setWfSwitching: Dispatch<SetStateAction<any>>;
}

export function useAtlasAgentRunning(): AtlasAgentRunning {
  const [agentRunning, _setAgentRunning] = useState(false);
  const agentRunningRef = useRef(false);
  const setAgentRunningState = useCallback((running: unknown) => {
    const next = !!running;
    agentRunningRef.current = next;
    try { window.ATLAS_AGENT_RUNNING = next; } catch (_) {}
    _setAgentRunning(next);
  }, []);
  useEffect(() => {
    const subs: Array<(() => void) | undefined> = [];
    const onGlobalRunning = (ev: any) => {
      setAgentRunningState(!!(ev && ev.detail && ev.detail.running));
    };
    try {
      if (typeof window.ATLAS_AGENT_RUNNING === 'boolean') {
        setAgentRunningState(window.ATLAS_AGENT_RUNNING);
      }
      window.addEventListener('atlas-agent-running', onGlobalRunning);
      if (window.backend?.subscribe) {
        subs.push(window.backend.subscribe('hello', (m: any) => {
          if (m && typeof m.running === 'boolean') setAgentRunningState(m.running);
        }));
        subs.push(window.backend.subscribe('agent_state', (m: any) => {
          if (m && typeof m.running === 'boolean') setAgentRunningState(m.running);
        }));
      }
    } catch (_) {}
    return () => {
      try { window.removeEventListener('atlas-agent-running', onGlobalRunning); } catch (_) {}
      subs.forEach(u => { try { u && u(); } catch (_) {} });
    };
  }, [setAgentRunningState]);

  // Workspace switch in-flight indicator. Backend emits
  // `workspace_changing` right before _setup_workspace runs and
  // `workspace_changed` after success. The banner shows a spinner so
  // the user can see the dropdown click hit something, even though
  // setup_workspace usually finishes in < 100 ms.
  const [wfSwitching, setWfSwitching] = useState<any>(null);
  useEffect(() => {
    if (!window.backend?.subscribe) return undefined;
    const subs: Array<(() => void) | undefined> = [];
    try {
      subs.push(window.backend.subscribe('workspace_changing', (m: any) => {
        setWfSwitching({ from: m?.prev || '', to: m?.workspace || '', ip: m?.ip || '' });
      }));
      subs.push(window.backend.subscribe('workspace_changed', (m: any) => {
        const loaded = m?.workspace || '';
        setWfSwitching((cur: any) => (!loaded || (cur && cur.to === loaded)) ? null : cur);
        setAgentRunningState(false);
      }));
    } catch (_) {}
    return () => { subs.forEach(u => { try { u && u(); } catch (_) {} }); };
  }, [setAgentRunningState]);
  useEffect(() => {
    if (!wfSwitching) return undefined;
    const t = setTimeout(() => setWfSwitching(null), 2500);
    return () => clearTimeout(t);
  }, [wfSwitching]);

  return { agentRunning, agentRunningRef, setAgentRunningState, wfSwitching, setWfSwitching };
}
