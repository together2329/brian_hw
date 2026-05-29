// app-boot-hook.tsx — extracted from app.tsx (strangler-fig TS split).
//
// Owns the first-connect handshake indicator (the centered boot overlay's
// state machine): WS connect -> hello -> /healthz -> /api/session/list ->
// LLM provider probe. Self-contained — depends only on the authState arg,
// its own state, and window.backend / fetch — so it lifts out as a real
// React custom hook that runs in App's render context (behavior identical).
//
// Returns the raw state + setters (App's auth effect still flips bootSteps.ws
// on auth_required) plus the derived bootDone / bootUsable / bootDisplayDone /
// bootFailed booleans the overlay reads.
//
// Typed in the same permissive house style as app-helpers.tsx.
import { useState, useEffect, useRef } from 'react';
import type { MutableRefObject, Dispatch, SetStateAction } from 'react';

export interface AtlasBoot {
  bootSteps: Record<string, string>;
  setBootSteps: Dispatch<SetStateAction<Record<string, string>>>;
  bootHidden: boolean;
  setBootHidden: Dispatch<SetStateAction<boolean>>;
  bootEverReadyRef: MutableRefObject<boolean>;
  bootDone: boolean;
  bootUsable: boolean;
  bootDisplayDone: boolean;
  bootFailed: boolean;
}

export function useAtlasBoot(authState: string): AtlasBoot {
  const [bootSteps, setBootSteps] = useState<Record<string, string>>({
    ws: 'pending', hello: 'pending', health: 'pending', sessions: 'pending',
    llm: 'pending',
  });
  const [bootHidden, setBootHidden] = useState(false);
  const bootEverReadyRef = useRef(false);

  useEffect(() => {
    const mark = (k: string, v: string) => setBootSteps(s => (s[k] === v ? s : { ...s, [k]: v }));
    const runProbes = () => {
      // Reset HTTP-side legs to pending so the user sees the rerun.
      setBootSteps(s => ({
        ...s,
        health: 'pending', sessions: 'pending', llm: 'pending',
      }));
      if (!bootEverReadyRef.current) setBootHidden(false);
      fetch('/healthz?cost=0', { cache: 'no-store' })
        .then(r => mark('health', r.ok ? 'done' : 'fail'))
        .catch(() => mark('health', 'fail'));
      fetch('/api/session/list', { cache: 'no-store' })
        .then(r => mark('sessions', r.ok ? 'done' : 'fail'))
        .catch(() => mark('sessions', 'fail'));
      // LLM provider probe — cheap GET /v1/models. Backend now treats
      // 200/400/404 as "reachable" so this lights ✓ on every common
      // provider (deepseek, openai, codex OAuth, azure deployment
      // without /models exposed).
      fetch('/api/llm/ping', { cache: 'no-store' })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(j => mark('llm', j && j.ok ? 'done' : 'fail'))
        .catch(() => mark('llm', 'fail'));
    };

    // Initial WS state — backend.js may have already connected by the
    // time this effect runs.
    if (window.backend?.getConnectionState) {
      const s = window.backend.getConnectionState();
      mark('ws', s === 'open' ? 'done' : (s === 'closed' || s === 'error' ? 'fail' : 'pending'));
    }
    const subs: Array<(() => void) | undefined> = [];
    try {
      subs.push(window.backend.subscribe('connection', (m: any) => {
        const next = m?.state === 'open' ? 'done' : 'fail';
        mark('ws', next);
        // On a reconnect (e.g. after backend restart), re-fire the
        // HTTP probes — otherwise the panel stays pinned at whatever
        // it captured the first time the page mounted. The boot card
        // is what the user looks at to confirm "yes the new backend
        // is up", so it MUST refresh after a WS reopen.
        if (next === 'done') runProbes();
      }));
      subs.push(window.backend.subscribe('hello', () => mark('hello', 'done')));
    } catch (_) {}
    runProbes();
    return () => { subs.forEach(u => { try { u && u(); } catch (_) {} }); };
  }, []);
  useEffect(() => {
    if (authState !== 'authed') return undefined;
    const needsProbe = (
      bootSteps.health !== 'done'
      || bootSteps.sessions !== 'done'
      || bootSteps.llm !== 'done'
    );
    if (!needsProbe) return undefined;
    let cancelled = false;
    const mark = (key: string, value: string) => {
      if (cancelled) return;
      setBootSteps(s => (s[key] === value ? s : { ...s, [key]: value }));
    };
    const t = setTimeout(() => {
      fetch('/api/session/list', { cache: 'no-store' })
        .then(r => mark('sessions', r.ok ? 'done' : 'fail'))
        .catch(() => mark('sessions', 'fail'));
      fetch('/healthz?cost=0', { cache: 'no-store' })
        .then(r => mark('health', r.ok ? 'done' : 'fail'))
        .catch(() => mark('health', 'fail'));
      fetch('/api/llm/ping', { cache: 'no-store' })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(j => mark('llm', j && j.ok ? 'done' : 'fail'))
        .catch(() => mark('llm', 'fail'));
    }, 350);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [authState, bootSteps.health, bootSteps.sessions, bootSteps.llm]);
  const bootDone = Object.values(bootSteps).every(v => v === 'done');
  const bootUsable = (
    authState === 'authed'
    && bootSteps.ws === 'done'
    && bootSteps.hello === 'done'
    && bootSteps.llm === 'done'
    && bootSteps.health !== 'fail'
    && bootSteps.sessions !== 'fail'
  );
  const bootDisplayDone = bootDone || bootUsable;
  const bootFailed = !bootDisplayDone && Object.values(bootSteps).some(v => v === 'fail');
  useEffect(() => {
    if (bootDisplayDone) {
      bootEverReadyRef.current = true;
      setTimeout(() => {
        if (bootEverReadyRef.current) setBootHidden(true);
      }, 1200);
    }
  }, [bootDisplayDone]);

  return {
    bootSteps, setBootSteps, bootHidden, setBootHidden, bootEverReadyRef,
    bootDone, bootUsable, bootDisplayDone, bootFailed,
  };
}
