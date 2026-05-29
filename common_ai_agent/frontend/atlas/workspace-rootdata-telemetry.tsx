// workspace-rootdata-telemetry.tsx — extracted cohesive slice of
// workspace-root-data-hook.tsx (strangler-fig migration of workspace.jsx).
//
// Owns two halves of the workspace data hook that are self-contained and do not
// close over any per-render hook state:
//   - WorkspaceDataDeps: the session-half dependency contract threaded into
//     useWorkspaceData from useWorkspaceSession.
//   - mergeHealthTelemetry / mergeContextTelemetry: the pure telemetry-merge
//     reducers carved out of the /healthz poll loop and the
//     atlas-data-changed / atlas-session-loaded CONTEXT sync. Each takes the
//     previous telemetry snapshot plus a payload and returns the merged slice;
//     they only call session-routing helpers, never React state.
//
// This is an INERT mirror — legacy workspace.jsx still serves the live app.
// Window-sourced values are typed `any` on purpose; do not tighten them.

import {
  normalizeUiSession,
  uiSessionRoute,
  ssotIpFromSession,
} from './workspace-session-routing';
import { QA_HISTORY_STORAGE_PREFIX } from './workspace-tool-theme';

const w = window as any;

/**
 * Session-half dependencies threaded in from useWorkspaceSession so the two
 * extracted halves of the Workspace closure share the same state. Typed loosely
 * (any) because the live shapes are dynamic; this mirrors the original closure
 * where every binding was in scope without annotations.
 */
export interface WorkspaceDataDeps {
  activeNamespace: string;
  workflow: any;
  setWorkflow: (wf: any) => void;
  activeSession: any;
  setActiveSession: (sid: any) => void;
  activeSessionRef: { current: any };
  feed: any[];
  setFeed: (updater: any) => void;
  chatViewSessionRef: { current: any };
  hydratedConversationSessionRef: { current: any };
  liveFeedStartedRef: { current: any };
  workerLogCursorsRef: { current: Map<string, any> };
  streamingRef: { current: any };
  streamBufferRef: { current: any };
  inputRef: { current: any };
  feedRef: { current: any };
  intent: any;
  switchIntent: (i: any) => void;
  resolveSession: (...candidates: any[]) => string;
  setChatViewSession: (sid: any) => void;
  sessionForInputRoute: (ip: any, wf: any) => any;
  setOrchestratorInputRoute: (ip?: any) => void;
  setWorkflowDispatchInputRoute: (wf: any, ip?: any) => void;
  activateSession: (scopePath: any, wf?: any) => void;
  NORMAL_FEED: any[];
  PLAN_FEED: any[];
}

/**
 * Merge a /healthz payload into the previous workspaceTelemetry snapshot.
 * Pure: depends only on the arguments and session-routing helpers, so it lives
 * outside the hook closure. `acceptCounters` / `effectiveRoute` are derived by
 * the caller from the same payload.
 */
export function mergeHealthTelemetry(
  prev: any,
  j: any,
  effectiveSession: any,
  acceptCounters: boolean,
  effectiveRoute: any,
): any {
  const nextSession = normalizeUiSession(effectiveSession || '');
  const prevSession = normalizeUiSession(prev.activeSession || '');
  const prevRoute = uiSessionRoute(prevSession);
  const prevIp = prevRoute.ip || String(prev.costIp || '').trim();
  const changed = !!(nextSession && prevSession && nextSession !== prevSession);
  const resetCounters = changed || !!(
    !acceptCounters
    && effectiveRoute.ip
    && prevIp
    && prevIp !== effectiveRoute.ip
  );
  const keep = (value: any) => (resetCounters ? 0 : value);
  const stable = (key: string, value: any) => {
    if (!acceptCounters) return keep(Number(prev[key] || 0));
    const next = Number(value || 0);
    if (resetCounters) return next;
    const old = Number(prev[key] || 0);
    return Number.isFinite(next) ? Math.max(old, next) : old;
  };
  return {
    activeSession: nextSession || prev.activeSession || '',
    tokensIn: j.tokens_in != null ? stable('tokensIn', j.tokens_in) : Number(prev.tokensIn || 0),
    tokensCache: j.tokens_cache != null ? stable('tokensCache', j.tokens_cache) : Number(prev.tokensCache || 0),
    tokensOut: j.tokens_out != null ? stable('tokensOut', j.tokens_out) : Number(prev.tokensOut || 0),
    costUsd: j.cost_usd != null ? stable('costUsd', j.cost_usd) : Number(prev.costUsd || 0),
    costScope: acceptCounters ? (j.cost_scope || prev.costScope || '') : (prev.costScope || (effectiveRoute.ip ? 'user_ip' : '')),
    costUser: acceptCounters ? (j.cost_user || prev.costUser || '') : (effectiveRoute.owner || prev.costUser || ''),
    costIp: acceptCounters ? (j.cost_ip || effectiveRoute.ip || prev.costIp || '') : (effectiveRoute.ip || ''),
    costCalls: acceptCounters && j.cost_calls != null ? Number(j.cost_calls || 0) : keep(Number(prev.costCalls || 0)),
    model: j.model || j.base_model || prev.model || '',
    agentAlive: typeof j.agent_alive === 'boolean' ? j.agent_alive : !!prev.agentAlive,
    agentRunning: typeof j.agent_running === 'boolean' ? j.agent_running : !!prev.agentRunning,
  };
}

/**
 * Merge a window.CONTEXT usage snapshot into the previous workspaceTelemetry.
 * Pure: depends only on the arguments and normalizeUiSession.
 */
export function mergeContextTelemetry(prev: any, ctx: any): any {
  const nextSession = normalizeUiSession(ctx.activeSession || '');
  const prevSession = normalizeUiSession(prev.activeSession || '');
  const changed = !!(nextSession && prevSession && nextSession !== prevSession);
  const stable = (key: string, value: any) => {
    const next = Number(value || 0);
    if (changed) return next;
    const old = Number(prev[key] || 0);
    return Number.isFinite(next) ? Math.max(old, next) : old;
  };
  return {
    activeSession: nextSession || prev.activeSession || '',
    tokensIn: ctx.tokensIn != null ? stable('tokensIn', ctx.tokensIn) : Number(prev.tokensIn || 0),
    tokensCache: ctx.tokensCache != null ? stable('tokensCache', ctx.tokensCache) : Number(prev.tokensCache || 0),
    tokensOut: ctx.tokensOut != null ? stable('tokensOut', ctx.tokensOut) : Number(prev.tokensOut || 0),
    costUsd: ctx.costUsd != null ? stable('costUsd', ctx.costUsd) : Number(prev.costUsd || 0),
    costScope: ctx.costScope || prev.costScope || '',
    costUser: ctx.costUser || prev.costUser || '',
    costIp: ctx.costIp || prev.costIp || '',
    costCalls: ctx.costCalls != null ? Number(ctx.costCalls || 0) : Number(prev.costCalls || 0),
    model: ctx.model || prev.model || '',
  };
}

/**
 * Resolve the active SSOT IP: prefer the route-derived `activeIp`, then the IP
 * embedded in the current session, then a sanitized trailing segment of
 * w.SCOPE_PATH. Returns '' when none qualifies.
 */
export function resolveActiveSsotIp(activeIp: any, currentSession: any): string {
  if (activeIp) return activeIp;
  const fromSession = ssotIpFromSession(currentSession || w.ACTIVE_SESSION);
  if (fromSession) return fromSession;
  const scoped = String(w.SCOPE_PATH || '').split('/').filter(Boolean).pop() || '';
  return /^[A-Za-z][A-Za-z0-9_]*$/.test(scoped) ? scoped : '';
}

/**
 * Normalize a raw input-history list: drop non-string / blank entries and cap
 * to the most-recent `limit`. Pure.
 */
export function cleanInputHistory(items: any, limit: number): string[] {
  return (Array.isArray(items) ? items : [])
    .filter((x: any) => typeof x === 'string' && x.trim())
    .slice(-limit);
}

/**
 * Read the persisted input-history list from localStorage, returning a cleaned
 * array (empty on any parse / access error).
 */
export function loadStoredInputHistory(limit: number): string[] {
  try {
    const raw = localStorage.getItem('atlasInputHistory');
    const parsed = raw ? JSON.parse(raw) : [];
    return cleanInputHistory(parsed, limit);
  } catch (_) {
    return [];
  }
}

/**
 * Read the persisted preview path from localStorage, or null on miss / error.
 */
export function loadStoredPreviewPath(): string | null {
  try {
    const saved = localStorage.getItem('atlasPreviewPath');
    return saved ? String(saved) : null;
  } catch (_) {
    return null;
  }
}

/**
 * Build the per-session+IP Q&A-history scope descriptor (session, ip, and the
 * localStorage key). Pure: `session` is the normalized current session and
 * `fallbackIp` is the caller's resolved active SSOT IP.
 */
export function buildQaHistoryScope(session: string, fallbackIp: string): {
  session: string;
  ip: string;
  key: string;
} {
  const ip = ssotIpFromSession(session) || fallbackIp || 'default';
  const safeSession = session || 'default';
  const safeIp = ip || 'default';
  return {
    session,
    ip,
    key: `${QA_HISTORY_STORAGE_PREFIX}${safeSession}:${safeIp}`,
  };
}

/**
 * Decide whether a stored Q&A-history entry belongs to the active scope. Pure:
 * `scopeSession` / `scopeIp` come from buildQaHistoryScope.
 */
export function qaHistoryEntryMatchesScope(
  entry: any,
  scopeSession: string,
  scopeIp: string,
): boolean {
  const entrySession = normalizeUiSession(entry?.session || '');
  const entryIp = String(entry?.ip || '').trim();
  const hasEntryScope = !!entrySession || !!entryIp;
  if (entrySession && scopeSession && entrySession !== scopeSession) return false;
  if (entryIp && scopeIp && entryIp !== scopeIp) return false;
  if (!hasEntryScope && (scopeSession || (scopeIp && scopeIp !== 'default'))) return false;
  return true;
}
