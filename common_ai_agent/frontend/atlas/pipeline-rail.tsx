// pipeline-rail.tsx — TypeScript migration slice of pipeline.tsx.
//
// Extracted from pipeline.tsx (was 1208L) so it drops under 1000. Holds the
// left-rail / readiness / chat / phase-group cluster:
//   - HierarchyList                 — IP hierarchy list (left column top).
//   - deriveStageReadiness          — green-readiness derivation from stages.
//   - RunToGreenCard                — readiness card + run-to-green dispatch.
//   - StageStatusRail               — left column status object (IP + stages).
//   - PipelineOrchestratorChatPanel — right-column orchestrator chat.
//   - PhaseGroup                    — phase-grouped StageCard grid.
//
// Same permissive house style as the other pipeline-* siblings: cross-file
// window globals (owned by not-yet-migrated .jsx) are reached through a locally-
// typed `AtlasGlue` view of window so the access type-checks without editing the
// shared types/atlas-window.d.ts. The transitional window.* bridges for these
// symbols still run in pipeline.tsx in the original order.
import {
  memo,
  useState,
  useEffect,
  useRef,
  useCallback,
  type Ref,
  type ReactNode,
  type ChangeEvent,
  type KeyboardEvent,
} from 'react';
import { useStickyChatScroll } from './use-sticky-chat-scroll';
import {
  cleanAtlasTerminalText,
  coalesceAtlasFeedEntries,
  trimAtlasFeedState,
} from './workspace-tool-theme';

// ── Local typed view of the legacy window-glue surface this file touches ──
type AnyComponent = (...a: unknown[]) => ReactNode;
interface StateMeta {
  color: string;
  glyph: string;
  label: string;
}
interface PipelinePolicyPayload {
  run_mode: string;
  exec_mode: string;
  [key: string]: unknown;
}
interface PipelineFlowDef {
  id: string;
  stages?: string[];
  [key: string]: unknown;
}
interface PipelineStageInfo {
  state?: string;
  status?: string;
  top?: string;
  secondary?: string;
  locked_reason?: string;
  latest_evidence?: string;
  live_tail?: string;
  iter?: number | string;
  elapsed_seconds?: number;
  model?: string;
  progress?: number;
  [key: string]: unknown;
}
interface AtlasOrchestratorChatEvent {
  session_id?: string;
  session?: string;
  namespace?: string;
  room?: string;
  workspace_session?: string;
  ip?: string;
  ip_id?: string;
  workspace_id?: string;
  id?: string | number;
  role?: string;
  content?: string;
  payload?: {
    role?: string;
    content?: string;
    display_name?: string;
    [key: string]: unknown;
  };
  created_at?: number;
  [key: string]: unknown;
}
interface AtlasBackendLike {
  subscribe?: (ev: string, cb: (m: AtlasOrchestratorChatEvent) => void) => (() => void) | void;
}
interface PipelineState {
  stages?: Record<string, PipelineStageInfo>;
  orchestrator?: {
    active?: boolean;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}
interface AtlasGlue {
  // cross-file data + helpers (owned by other files)
  PIPELINE_STAGES?: string[];
  PIPELINE_LABEL?: Record<string, string>;
  PIPELINE_FLOW_DEFS?: PipelineFlowDef[];
  pipelineStateMeta: (state: string) => StateMeta;
  pipelineActualStages: (stages: string[]) => string[];
  pipelinePolicyPayload: () => PipelinePolicyPayload;
  StageCard: AnyComponent;
  // session / context globals (owned by other files)
  ATLAS_USER?: { username?: string } & Record<string, unknown>;
  ATLAS_USER_SESSION_ID?: unknown;
  ATLAS_WORKSPACE_SESSION_ID?: unknown;
  ACTIVE_SESSION?: string;
  ATLAS_DB_SESSION_ID?: string;
  backend?: AtlasBackendLike;
}
const w = window as unknown as AtlasGlue;

const normalizeRailSession = (value: unknown): string => (
  String(value || '')
    .trim()
    .replace(/\\/g, '/')
    .split('/')
    .filter(Boolean)
    .join('/')
);

const activeRailWorkspaceSession = (): string => {
  const explicit = normalizeRailSession(w.ATLAS_WORKSPACE_SESSION_ID);
  if (explicit) return explicit;
  const parts = normalizeRailSession(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
  return parts.length >= 4 ? parts[1] || '' : '';
};

const activeOrchestratorRailSession = (ip?: string): string => {
  const activeSession = normalizeRailSession(w.ACTIVE_SESSION || '');
  const parts = activeSession.split('/').filter(Boolean);
  if (parts.length >= 4 && (!ip || parts[2] === ip)) {
    return `${parts[0]}/${parts[1]}/${ip || parts[2]}/orchestrator`;
  }
  const owner = normalizeRailSession(
    (w.ATLAS_USER && w.ATLAS_USER.username)
      || w.ATLAS_USER_SESSION_ID
      || parts[0]
      || '',
  );
  const workspaceSession = activeRailWorkspaceSession();
  return owner && workspaceSession && ip ? `${owner}/${workspaceSession}/${ip}/orchestrator` : '';
};

const eventSessionFromOrchestratorMessage = (message: AtlasOrchestratorChatEvent): string => (
  normalizeRailSession(message?.session_id || message?.session || message?.namespace || message?.room || '')
);

const matchesOrchestratorSession = (
  targetSession: string,
  messageSession: string,
  messageIp?: string,
  ip?: string,
  workspaceSession?: string,
): boolean => {
  const canonicalTarget = normalizeRailSession(targetSession);
  const canonicalMessage = normalizeRailSession(messageSession);
  if (!canonicalTarget && !workspaceSession && !ip) return true;
  if (!canonicalMessage && canonicalTarget) return false;
  if (!canonicalMessage) {
    const msgIp = normalizeRailSession(messageIp || '');
    const hasIpMatch = !!(ip && msgIp && msgIp === normalizeRailSession(ip));
    if (!hasIpMatch) return false;
    return true;
  }
  if (canonicalTarget) {
    const targetParts = canonicalTarget.split('/').filter(Boolean);
    const messageParts = canonicalMessage.split('/').filter(Boolean);
    const minLen = Math.min(targetParts.length, messageParts.length);
    if (minLen >= 2 && messageParts.slice(-minLen).join('/') === targetParts.slice(-minLen).join('/')) {
      return true;
    }
    if (canonicalMessage.startsWith(`${canonicalTarget}/`)) return true;
    return false;
  }
  if (!workspaceSession) return false;
  if (!canonicalMessage) return false;
  const wsParts = normalizeRailSession(workspaceSession).split('/').filter(Boolean);
  const msgParts = canonicalMessage.split('/').filter(Boolean);
  return wsParts.length >= 1 && msgParts.some((part) => wsParts.includes(part));
};

// ── HierarchyList ─────────────────────────────────────────────────────────────
// list with the active IP if the workspace endpoint is missing.
export interface HierarchyListProps {
  activeIp?: string;
  onSelect?: (ip: string) => void;
}
export function HierarchyList({ activeIp, onSelect }: HierarchyListProps) {
  const [ips, setIps] = useState<string[]>([]);
  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const owner = String((w.ATLAS_USER && w.ATLAS_USER.username)
          || w.ATLAS_USER_SESSION_ID
          || (w.ACTIVE_SESSION || '').split('/')[0]
          || '');
        const activeParts = String(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
        const workspaceSession = activeParts.length >= 4 && activeParts[0] === owner
          ? activeParts[1]
          : String(w.ATLAS_WORKSPACE_SESSION_ID || 'default');
        const sessionScope = owner ? `${owner}/${workspaceSession || 'default'}` : '';
        const url = sessionScope ? `/api/ip/list?session_id=${encodeURIComponent(sessionScope)}` : '/api/ip/list';
        const r = await fetch(url);
        const j = await r.json().catch(() => ({}));
        if (dead) return;
        const list = Array.isArray(j.items) ? j.items
                   : Array.isArray(j.ips) ? j.ips
                   : Array.isArray(j.workspaces) ? j.workspaces
                   : [];
        setIps(list.map((x: unknown) => typeof x === 'string' ? x : ((x as Record<string, string>).ip || (x as Record<string, string>).name || (x as Record<string, string>).id || '')).filter(Boolean));
      } catch (_) {
        const ownerScoped = !!(w.ATLAS_USER && w.ATLAS_USER.username);
        if (!dead && !ownerScoped && activeIp) setIps([activeIp]);
      }
    })();
    return () => { dead = true; };
  }, [activeIp]);

  return (
    <div className="pipe-hierarchy">
      <div className="pipe-hierarchy-title">IP HIERARCHY</div>
      <ul className="pipe-hierarchy-list">
        {(ips.length ? ips : (activeIp ? [activeIp] : [])).map(ip => (
          <li key={ip}
              className={`pipe-hierarchy-row ${ip === activeIp ? 'sel' : ''}`}
              onClick={() => onSelect && onSelect(ip)}>
            <span className="pipe-hierarchy-glyph">{ip === activeIp ? '◉' : '○'}</span>
            <span className="pipe-hierarchy-name">{ip}</span>
          </li>
        ))}
        {!ips.length && !activeIp && (
          <li className="pipe-hierarchy-row mute">no IPs yet</li>
        )}
      </ul>
      <div className="pipe-hierarchy-legend mute">
        <div>legend</div>
        <div>✓ passed · ▶ running · ! failed</div>
        <div>⏸ blocked · ⊘ stale · ◯ idle</div>
      </div>
    </div>
  );
}

interface NextStep {
  stage?: string | null;
  label?: string;
  owner?: string;
  reason?: string;
  status?: string;
}
interface StageReadiness {
  percent: number;
  headline: string;
  message: string;
  next_stage: string | null;
  next_steps: NextStep[];
  state: string;
}
export function deriveStageReadiness(stagesState?: Record<string, PipelineStageInfo> | null): StageReadiness | null {
  const sids = w.PIPELINE_STAGES || [];
  if (!stagesState || !sids.length) return null;
  const labels = w.PIPELINE_LABEL || {};
  let passed = 0, failed = 0, running = 0, blocked = 0, idle = 0;
  let firstNonGreen: string | null = null;
  for (const sid of sids) {
    const info = stagesState[sid] || {};
    const st = String(info.state || 'idle').toLowerCase();
    if (st === 'passed' || st === 'pass' || st === 'green') passed++;
    else if (st === 'running' || st === 'run') { running++; if (!firstNonGreen) firstNonGreen = sid; }
    else if (st === 'failed' || st === 'fail' || st === 'error' || st === 'red') { failed++; if (!firstNonGreen) firstNonGreen = sid; }
    else if (st === 'blocked' || st === 'block') { blocked++; if (!firstNonGreen) firstNonGreen = sid; }
    else { idle++; if (!firstNonGreen) firstNonGreen = sid; }
  }
  const total = sids.length;
  const percent = total ? Math.round((passed / total) * 100) : 0;
  const nextLabel = firstNonGreen ? (labels[firstNonGreen] || firstNonGreen) : null;
  let headline, message, nextSteps;
  if (passed === total) {
    headline = 'Pipeline complete';
    message = `All ${total} stages passed. Review evidence and approve sign-off.`;
    nextSteps = [{ stage: 'audit', label: 'Review goal-audit + approve sign-off', owner: 'human',
                   reason: 'Final human approval is the only gate left.', status: 'pending' }];
  } else if (failed) {
    headline = `${failed} stage${failed > 1 ? 's' : ''} failed`;
    message = `Fix ${nextLabel} (or other failed stage), then re-run downstream.`;
    nextSteps = [{ stage: firstNonGreen, label: `Resolve failure in ${nextLabel}`, owner: 'atlas',
                   reason: 'Failure blocks every downstream stage.', status: 'failed' }];
  } else if (blocked) {
    headline = `${blocked} stage${blocked > 1 ? 's' : ''} blocked`;
    message = `Unblock ${nextLabel} (review decision or missing evidence).`;
    nextSteps = [{ stage: firstNonGreen, label: `Unblock ${nextLabel}`, owner: 'human',
                   reason: 'Blocked stages need a review decision or missing evidence.', status: 'blocked' }];
  } else if (running) {
    headline = `${running} stage${running > 1 ? 's' : ''} running`;
    message = `Waiting for ${nextLabel} to finish.`;
    nextSteps = [{ stage: firstNonGreen, label: `Watch ${nextLabel}`, owner: 'atlas',
                   reason: 'Stage in progress.', status: 'running' }];
  } else if (passed > 0) {
    headline = `${passed} / ${total} stages green`;
    message = `Next: run ${nextLabel}.`;
    nextSteps = [{ stage: firstNonGreen, label: `Run ${nextLabel}`, owner: 'atlas',
                   reason: 'Next stage in the canonical pipeline.', status: 'pending' }];
  } else {
    return null;
  }
  return { percent, headline, message, next_stage: firstNonGreen, next_steps: nextSteps,
           state: passed === total ? 'complete' : (failed ? 'failed' : (blocked ? 'blocked' : (running ? 'running' : 'in_progress'))) };
}

interface RunToGreenSummary {
  percent?: number;
  state?: string;
  headline?: string;
  message?: string;
  next_stage?: string | null;
  next_steps?: NextStep[];
  primary_action?: { kind?: string; label?: string; stage?: string };
  [key: string]: unknown;
}
export interface RunToGreenCardProps {
  summary?: RunToGreenSummary | null;
  stages?: Record<string, PipelineStageInfo> | null;
  ip?: string;
  onSelectStage?: (stageId: string) => void;
}
export function RunToGreenCard({ summary, stages, ip, onSelectStage }: RunToGreenCardProps) {
  const [busy, setBusy] = useState(false);
  const derived = deriveStageReadiness(stages);
  const backend = summary || {};
  const backendPercent = Math.max(0, Math.min(100, Number(backend.percent || 0)));
  const derivedPercent = derived ? derived.percent : 0;
  const useDerived = derived && (derivedPercent > backendPercent || backendPercent === 0);
  const data = useDerived
    ? { ...backend, percent: derivedPercent, headline: derived.headline, message: derived.message,
        next_stage: derived.next_stage, next_steps: derived.next_steps, state: derived.state }
    : backend;
  const state = data.state || 'not_started';
  const percent = Math.max(0, Math.min(100, Number(data.percent || 0)));
  const rawSteps = Array.isArray(data.next_steps) ? data.next_steps : [];
  const nextSteps = rawSteps.length ? rawSteps : [{
    stage: 'ssot',
    label: 'Create or import SSOT',
    owner: 'user',
    reason: 'SSOT is the source of truth for every downstream step.',
    status: 'pending',
  }];
  const stageFor = (stage?: string | null): string => {
    if (stage === 'req') return 'ssot';
    if (stage === 'equivalence_goals') return 'equivalence';
    if (stage === 'goal_audit') return 'goal-audit';
    if (stage === 'sim_debug') return 'sim-debug';
    if (stage === 'fl_model') return 'fl-model';
    if (stage === 'fl_decomp' || stage === 'fcov_plan') return 'fl-model';
    return stage || 'ssot';
  };
  const focusStage = (stage?: string | null) => {
    const sid = stageFor(stage || data.next_stage);
    if (typeof onSelectStage === 'function') onSelectStage(sid);
    try {
      window.dispatchEvent(new CustomEvent('atlas:pipeline-focus-stage', {
        detail: { stage: sid },
      }));
    } catch (_) {}
  };
  const runToGreen = async () => {
    if (!ip || busy) return;
    const flow = (w.PIPELINE_FLOW_DEFS || []).find(f => f.id === 'full') || { stages: [] };
    const stages = w.pipelineActualStages(flow.stages || []);
    if (!stages.length) return;
    setBusy(true);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, stages, schedule: 'auto', prompt: '', ...w.pipelinePolicyPayload() }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        console.error('[pipeline] run-to-green failed', j.error || r.status);
      } else {
        try {
          window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', {
            detail: { stage: 'full', ip, jobs: j.jobs || [] },
          }));
          window.dispatchEvent(new CustomEvent('atlas:pipeline-poll'));
        } catch (_) {}
      }
    } catch (e) {
      console.error('[pipeline] run-to-green error', e);
    } finally {
      setBusy(false);
    }
  };
  const primary = data.primary_action || {};
  const primaryKind = primary.kind || 'run_pipeline';
  const primaryLabel = busy ? 'Starting...' : (primary.label || 'Run to Green');
  return (
    <div className="pipe-green-card" data-state={state}>
      <div className="pipe-green-top">
        <span className="pipe-green-kicker">GREEN READINESS</span>
        <span className="pipe-green-percent">{percent}%</span>
      </div>
      <div className="pipe-green-headline">{data.headline || 'Start the IP pipeline'}</div>
      <div className="pipe-green-message">
        {data.message || 'Run the flow and ATLAS will show the next simple action here.'}
      </div>
      <div className="pipe-green-bar" aria-label={`green readiness ${percent}%`}>
        <div className="pipe-green-bar-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="pipe-green-actions">
        <button className="rb-btn primary pipe-green-primary"
                disabled={!ip || busy}
                onClick={() => primaryKind === 'run_pipeline'
                  ? runToGreen()
                  : focusStage(primary.stage || data.next_stage)}>
          {primaryLabel}
        </button>
        {data.next_stage && (
          <button className="rb-btn pipe-green-secondary"
                  onClick={() => focusStage(data.next_stage)}>
            Open Next
          </button>
        )}
      </div>
      <div className="pipe-green-next">
        {nextSteps.length ? nextSteps.map((step, idx) => (
          <button key={`${step.stage || idx}-${idx}`}
                  className="pipe-green-step"
                  onClick={() => focusStage(step.stage)}>
            <span className="pipe-green-step-index">{idx + 1}</span>
            <span className="pipe-green-step-main">
              <span className="pipe-green-step-label">{step.label || step.stage}</span>
              <span className="pipe-green-step-reason">{step.reason || step.status || ''}</span>
            </span>
            <span className="pipe-green-owner">{step.owner || 'atlas'}</span>
          </button>
        )) : (
          <div className="pipe-green-empty">No open step found.</div>
        )}
      </div>
    </div>
  );
}

// ─── Internal: StageStatusRail ─────────────────────────────────────
//
// Left column: status is now the primary left-hand object. IP selection stays
// compact at the top, then every workflow stage is visible without scrolling
// the graph or opening a bottom inspector.
export interface StageStatusRailProps {
  activeIp?: string;
  onSelectIp?: (ip: string) => void;
  state?: PipelineState | null;
  simpleSummary?: RunToGreenSummary | null;
  selectedStage?: string;
  onSelectStage?: (stageId: string) => void;
}
export function StageStatusRail({ activeIp, onSelectIp, state, simpleSummary, selectedStage, onSelectStage }: StageStatusRailProps) {
  const labels = w.PIPELINE_LABEL || {};
  const stages = w.PIPELINE_STAGES || [];
  const stagesState = (state && state.stages) || {};
  const [ips, setIps] = useState<string[]>([]);
  const [detailsOpen, setDetailsOpen] = useState(false);

  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const owner = String((w.ATLAS_USER && w.ATLAS_USER.username)
          || w.ATLAS_USER_SESSION_ID
          || (w.ACTIVE_SESSION || '').split('/')[0]
          || '');
        const activeParts = String(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
        const workspaceSession = activeParts.length >= 4 && activeParts[0] === owner
          ? activeParts[1]
          : String(w.ATLAS_WORKSPACE_SESSION_ID || 'default');
        const sessionScope = owner ? `${owner}/${workspaceSession || 'default'}` : '';
        const url = sessionScope ? `/api/ip/list?session_id=${encodeURIComponent(sessionScope)}` : '/api/ip/list';
        const r = await fetch(url);
        const j = await r.json().catch(() => ({}));
        if (dead) return;
        const list = Array.isArray(j.items) ? j.items
                   : Array.isArray(j.ips) ? j.ips
                   : Array.isArray(j.workspaces) ? j.workspaces
                   : [];
        setIps(list.map((x: unknown) => typeof x === 'string' ? x : ((x as Record<string, string>).ip || (x as Record<string, string>).name || (x as Record<string, string>).id || '')).filter(Boolean));
      } catch (_) {
        const ownerScoped = !!(w.ATLAS_USER && w.ATLAS_USER.username);
        if (!dead && !ownerScoped && activeIp) setIps([activeIp]);
      }
    })();
    return () => { dead = true; };
  }, [activeIp]);

  const summarize = (info?: PipelineStageInfo): string => {
    if (!info) return 'no evidence yet';
    return info.top || info.secondary || info.locked_reason || info.latest_evidence || 'no evidence yet';
  };

  return (
    <div className="pipe-stage-rail">
      <div className="pipe-stage-rail-head">
        <div>
          <div className="pipe-stage-rail-kicker">IP</div>
          <div className="pipe-stage-rail-ip">{activeIp || 'no IP'}</div>
        </div>
        <select className="pipe-stage-rail-select"
                value={activeIp || ''}
                onChange={(e: ChangeEvent<HTMLSelectElement>) => onSelectIp && onSelectIp(e.currentTarget.value)}>
          {(ips.length ? ips : (activeIp ? [activeIp] : [])).map(ip => (
            <option key={ip} value={ip}>{ip}</option>
          ))}
        </select>
      </div>
      <RunToGreenCard
        summary={simpleSummary}
        stages={stagesState}
        ip={activeIp}
        onSelectStage={onSelectStage} />
      <button className="pipe-stage-rail-title pipe-stage-rail-toggle"
              onClick={() => setDetailsOpen(v => !v)}
              aria-expanded={detailsOpen}>
        <span>Stage Detail</span>
        <span className="pipe-stage-rail-toggle-hint">{detailsOpen ? '▾ hide' : '▸ show'}</span>
      </button>
      {detailsOpen && (
        <>
          <div className="pipe-stage-rail-hint">Same info as the flow map. Click a row to focus the stage.</div>
          <div className="pipe-stage-rail-list">
            {stages.map(stageId => {
              const info = stagesState[stageId] || {};
              const stateName = info.state || 'idle';
              const meta = w.pipelineStateMeta(stateName);
              return (
                <button key={stageId}
                        className={`pipe-stage-rail-row ${selectedStage === stageId ? 'sel' : ''}`}
                        data-state={stateName}
                        onClick={() => onSelectStage && onSelectStage(stageId)}>
                  <span className="pipe-stage-rail-glyph" style={{ color: meta.color }}>{meta.glyph}</span>
                  <span className="pipe-stage-rail-main">
                    <span className="pipe-stage-rail-name">{labels[stageId] || stageId}</span>
                    <span className="pipe-stage-rail-sub">{summarize(info)}</span>
                  </span>
                  <span className="pipe-stage-rail-state">{meta.label}</span>
                </button>
              );
            })}
          </div>
          <div className="pipe-stage-rail-legend">
            ✓ passed · ▶ running · ! failed · ⏸ blocked · ⊘ stale
          </div>
        </>
      )}
    </div>
  );
}

interface ChatMessage {
  id?: string | number;
  role?: string;
  content?: string;
  payload?: {
    role?: string;
    content?: string;
    display_name?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}
type OrchestratorFeedEntry = {
  id: string;
  kind: 'agent' | 'thought' | 'action' | 'obs' | 'agent_delta' | string;
  text: string;
  tool?: string;
  args?: string;
  createdAt?: number;
  streamId?: string;
};

const ORCH_CHAT_POLL_INTERVAL_ACTIVE_MS = 1500;
const ORCH_CHAT_POLL_INTERVAL_IDLE_MS = 4500;
const ORCH_CHAT_POLL_INTERVAL_ERROR_MS = 8000;
const ORCH_CHAT_FEED_MAX_ENTRIES = 300;
const ORCH_TS_TO_MS_CEILING = 1e12;
const ORCH_TOOL_CALL_RE = /^(?:[▶⏺*]\s*)?([A-Za-z_][\w.-]*)(?:\s*\(([\s\S]*)\))?\s*$/;

function isOrchestratorHousekeepingLine(text: string): boolean {
  const normalized = String(text || '')
    .replace(/\u2026/g, '...')
    .replace(/\s+/g, ' ')
    .trim();
  if (!normalized) return false;
  if (/^streaming\s+\d+s?\s+idle\s+\(limit\s+\d+s?\)$/i.test(normalized)) return true;
  return /^(?:\*?\s*)?(?:running|runn+ing|writinng|writing|loading|waiting|processing)(?:\s+(?:output|cache|state))?(?:\s*[.]{3,})?(?:\s*\(\d+\/\d+\))?$/i.test(normalized);
}

function cleanChatMessageLine(text: string): string {
  return cleanAtlasTerminalText(text).replace(/\x00/g, '').trim();
}

function toEpochMs(value: unknown, fallback = 0): number {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return fallback;
  return n < ORCH_TS_TO_MS_CEILING ? n * 1000 : n;
}

function formatEpoch(value?: number): string {
  if (!value) return '';
  const d = new Date(value);
  return Number.isFinite(d.getTime())
    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '';
}

function formatFeedHeader(entry: OrchestratorFeedEntry): string {
  const pieces: string[] = [];
  const role = roleFromFeedEntry(entry);
  if (role) pieces.push(role);
  if (entry.tool) pieces.push(entry.tool);
  if (entry.args) pieces.push(entry.args);
  if (entry.kind === 'obs' && !entry.tool) pieces.push('observation');
  if (entry.kind === 'thought') pieces.push('reasoning');
  const time = formatEpoch(entry.createdAt);
  if (time) pieces.push(time);
  return pieces.join(' · ');
}

function parseToolLine(content: string): { tool: string; args: string } | null {
  const match = String(content).match(ORCH_TOOL_CALL_RE);
  if (!match) return null;
  const tool = String(match[1] || '').trim();
  const args = String(match[2] || '').trim();
  if (!tool) return null;
  return {
    tool,
    args: args ? `(${args})` : '',
  };
}

function mapOrchestratorMessageToFeedEntry(message: ChatMessage): OrchestratorFeedEntry | null {
  const globalLogic = (window as Window & { AtlasOrchestratorChatLogic?: { feedEntryFromChatMessage?: (m: ChatMessage) => {
    kind?: string;
    text?: string;
    tool?: string;
    args?: string;
    createdAt?: number;
    streamId?: string;
  } } }).AtlasOrchestratorChatLogic;
  if (globalLogic && typeof globalLogic.feedEntryFromChatMessage === 'function') {
    const parsed = globalLogic.feedEntryFromChatMessage(message);
    if (!parsed || typeof parsed !== 'object') return null;
    const kind = String(parsed.kind || 'agent');
    const text = String(parsed.text || '').trim();
    if (!text) return null;
    const createdAt = toEpochMs(parsed.createdAt == null ? message.created_at : parsed.createdAt, 0);
    const rawId = message.id != null ? String(message.id) : `${kind}:${createdAt || 0}:${text}`;
    return {
      id: rawId,
      kind,
      text,
      tool: parsed.tool ? String(parsed.tool) : undefined,
      args: parsed.args ? String(parsed.args) : undefined,
      createdAt,
      streamId: parsed.streamId ? String(parsed.streamId) : undefined,
    };
  }

  const payload = message.payload || {};
  const role = String(message.role || payload.role || '').toLowerCase();
  const rawContent = String(
    (payload && (payload.content || payload.display_name))
    || message.content
    || '',
  );
  const content = cleanChatMessageLine(rawContent);
  if (!content) return null;

  const createdAt = toEpochMs(message.created_at, 0);
  const messageId = String(message.id || `${role}:${createdAt}:${content}`);

  if (role === 'user') {
    return { id: messageId, kind: 'user', text: content, createdAt };
  }
  if (role === 'assistant_delta') {
    return {
      id: messageId,
      kind: 'agent_delta',
      text: content,
      createdAt,
      streamId: String(payload.stream_id || ''),
    };
  }
  if (role === 'assistant') {
    return { id: messageId, kind: 'agent', text: content, createdAt };
  }
  if (role === 'thought' || role === 'reasoning') {
    if (isOrchestratorHousekeepingLine(content)) return null;
    return { id: messageId, kind: 'thought', text: content, createdAt };
  }
  if (role === 'tool') {
    const parsed = parseToolLine(content);
    if (!parsed) return null;
    if (isOrchestratorHousekeepingLine(parsed.tool)) return null;
    return {
      id: messageId,
      kind: 'action',
      text: content,
      tool: parsed.tool,
      args: parsed.args,
      createdAt,
    };
  }
  if (role === 'tool_result' || role === 'observation' || role === 'obs') {
    const tool = String((payload.tool || payload.name || payload.display_name || payload.role || '') as string).trim();
    if (tool && isOrchestratorHousekeepingLine(tool)) return null;
    return {
      id: messageId,
      kind: 'obs',
      text: content,
      tool,
      createdAt,
    };
  }
  return { id: messageId, kind: 'agent', text: content, createdAt };
}

function eventSinceFromSeconds(value: number | undefined): number {
  if (!Number.isFinite(Number(value)) || Number(value) <= 0) return 0;
  const n = Number(value);
  return n < ORCH_TS_TO_MS_CEILING ? n / 1000 : n;
}

function eventSinceFromPayload(message: AtlasOrchestratorChatEvent): number {
  const created = toEpochMs(
    message.created_at,
    Number(message.payload && message.payload.created_at),
  );
  return eventSinceFromSeconds(created);
}

function roleFromFeedEntry(entry: OrchestratorFeedEntry): string {
  if (entry.kind === 'user') return 'user';
  if (entry.kind === 'action') return entry.tool || 'action';
  if (entry.kind === 'obs') return entry.tool || 'observation';
  if (entry.kind === 'thought') return 'thought';
  return 'assistant';
}
export interface PipelineOrchestratorChatPanelProps {
  ip?: string;
  pipelineState?: PipelineState | null;
}

interface OrchestratorChatComposerProps {
  hasIp: boolean;
  ip?: string;
  onSubmit: (text: string) => Promise<void>;
  scrollToBottom: () => void;
}

const OrchestratorChatComposer = memo(function OrchestratorChatComposer({
  hasIp,
  ip,
  onSubmit,
  scrollToBottom,
}: OrchestratorChatComposerProps) {
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    const text = draft.trim();
    if (!text || !hasIp || sending) return;
    setSending(true);
    scrollToBottom();
    try {
      await onSubmit(text);
      setDraft('');
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      console.warn(`orchestrator chat send failed: ${detail}`);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="orch-chat-input-row">
      <textarea
        className="orch-chat-input"
        placeholder={hasIp ? `Message orchestrator for ${ip}…` : 'Select an IP first'}
        value={draft}
        disabled={sending}
        rows={1}
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button
        className="orch-chat-send-btn"
        disabled={!draft.trim() || !hasIp || sending}
        onClick={() => { void handleSend(); }}
      >
        {sending ? '…' : '▶'}
      </button>
    </div>
  );
});

function PipelineOrchestratorChatPanelImpl({ ip, pipelineState }: PipelineOrchestratorChatPanelProps) {
  const [messages, setMessages] = useState<OrchestratorFeedEntry[]>([]);
  const [filterCategory, setFilterCategory] = useState<'all' | 'thought' | 'action' | 'obs'>('all');
  const [since, setSince] = useState(0);
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sinceRef = useRef(0);
  const subscriptionRef = useRef<(() => void) | void>();
  const fetchOnceRef = useRef<(() => Promise<void>) | null>(null);
  const {
    scrollRef: bodyRef,
    onScroll: onBodyScroll,
    scrollToBottom: scrollBodyToBottom,
  } = useStickyChatScroll<HTMLDivElement>([messages.length]);

  useEffect(() => {
    setMessages([]);
    setFilterCategory('all');
    setSince(0);
    sinceRef.current = 0;
  }, [ip]);

  const isActive = !!(pipelineState && pipelineState.orchestrator && pipelineState.orchestrator.active);
  const hasIp = !!(ip && ip !== 'default');

  useEffect(() => {
    sinceRef.current = since;
  }, [since]);

  useEffect(() => {
    if (!hasIp) {
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
        pollingRef.current = null;
      }
      if (subscriptionRef.current) {
        const unsub = subscriptionRef.current;
        subscriptionRef.current = undefined;
        if (typeof unsub === 'function') unsub();
      }
      return;
    }
    let dead = false;
    const activeWorkspaceSession = activeRailWorkspaceSession();
    const targetSession = activeOrchestratorRailSession(ip);
    const hasLiveBackend = !!(w.backend && typeof w.backend.subscribe === 'function');
    const activeTargetIp = String(ip || '');

    const clearPoll = () => {
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
        pollingRef.current = null;
      }
    };

    const schedulePoll = (delayMs: number) => {
      clearPoll();
      if (dead) return;
      const delay = Number.isFinite(delayMs) && delayMs > 0 ? Math.max(200, Math.round(delayMs)) : ORCH_CHAT_POLL_INTERVAL_IDLE_MS;
      pollingRef.current = setTimeout(() => { void fetchOnce(); }, delay);
    };

    const appendEntries = (incoming: OrchestratorFeedEntry[]) => {
      if (!incoming.length) return;
      setMessages(prev => {
        const merged = coalesceAtlasFeedEntries(prev, incoming as any[]) as OrchestratorFeedEntry[];
        return trimAtlasFeedState(merged, ORCH_CHAT_FEED_MAX_ENTRIES);
      });
      const latest = incoming.reduce((acc, item) => {
        const raw = Number(item.createdAt || 0);
        if (!raw || !Number.isFinite(raw)) return acc;
        return Math.max(acc, eventSinceFromSeconds(raw));
      }, 0);
      if (latest > 0 && latest > sinceRef.current) {
        sinceRef.current = latest;
        setSince(latest);
      }
    };

    const onBackendEvent = (message: AtlasOrchestratorChatEvent) => {
      if (!message || dead) return;
      const session = eventSessionFromOrchestratorMessage(message);
      if (!matchesOrchestratorSession(targetSession, session, String(message.ip || ''), activeTargetIp, activeWorkspaceSession)) return;
      const messageAsChat = mapOrchestratorMessageToFeedEntry(message as ChatMessage);
      if (!messageAsChat) return;
      if (isOrchestratorHousekeepingLine(messageAsChat.text || '')) return;
      appendEntries([messageAsChat]);
      const incomingSince = eventSinceFromPayload(message);
      if (incomingSince > 0 && incomingSince > sinceRef.current) {
        sinceRef.current = incomingSince;
        setSince(incomingSince);
      }
    };

    const fetchOnce = async () => {
      if (dead) return;
      if (typeof document !== 'undefined' && document.visibilityState !== 'visible') {
        schedulePoll(ORCH_CHAT_POLL_INTERVAL_ERROR_MS);
        return;
      }
      try {
        const params = new URLSearchParams({
          ip: ip!,
          since: String(sinceRef.current),
        });
        const workspaceSession = activeRailWorkspaceSession();
        if (workspaceSession) params.set('workspace_session', workspaceSession);
        const url = `/api/orchestrator/chat/messages?${params.toString()}`;
        const r = await fetch(url);
        if (!r.ok) {
          schedulePoll(ORCH_CHAT_POLL_INTERVAL_ERROR_MS);
          return;
        }
        const j = await r.json();
        if (!dead && j.ok && Array.isArray(j.messages)) {
          setMessages(prev => {
            const incoming = Array.isArray(j.messages) ? (j.messages as ChatMessage[]) : [];
            const seen = new Set(prev.map((item) => item.id));
            const fresh = incoming
              .map(mapOrchestratorMessageToFeedEntry)
              .filter((entry): entry is OrchestratorFeedEntry => !!entry && !seen.has(entry.id));
            if (fresh.length === 0) return prev;
            const merged = coalesceAtlasFeedEntries(prev, fresh as any[]) as OrchestratorFeedEntry[];
            return trimAtlasFeedState(merged, ORCH_CHAT_FEED_MAX_ENTRIES);
          });
          const nextSince = Number((j as { next_since?: unknown }).next_since || sinceRef.current);
          if (Number.isFinite(nextSince) && nextSince > sinceRef.current) {
            sinceRef.current = nextSince;
            setSince(nextSince);
          }
        }
        // Poll unconditionally: the backend has no orchestrator_chat WS
        // emitter, so a connected backend.subscribe channel must not turn
        // polling off — it only lowers latency when events do arrive.
        schedulePoll(isActive ? ORCH_CHAT_POLL_INTERVAL_ACTIVE_MS : ORCH_CHAT_POLL_INTERVAL_IDLE_MS);
        return;
      } catch (_) {
        schedulePoll(ORCH_CHAT_POLL_INTERVAL_ERROR_MS);
      }
    };
    fetchOnceRef.current = fetchOnce;

    const onVisibility = () => {
      if (dead) return;
      if (typeof document !== 'undefined' && document.visibilityState !== 'visible') {
        clearPoll();
        return;
      }
      clearPoll();
      void fetchOnce();
    };

    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', onVisibility);
    }
    if (hasLiveBackend && w.backend && typeof w.backend.subscribe === 'function') {
      const off = w.backend.subscribe('orchestrator_chat', onBackendEvent);
      subscriptionRef.current = off;
    } else {
      subscriptionRef.current = undefined;
    }

    fetchOnce();
    return () => {
      dead = true;
      clearPoll();
      fetchOnceRef.current = null;
      const unsub = subscriptionRef.current;
      subscriptionRef.current = undefined;
      if (typeof unsub === 'function') unsub();
      if (typeof document !== 'undefined') {
        document.removeEventListener('visibilitychange', onVisibility);
      }
    };
  }, [ip, isActive, hasIp]);

  const visibleMessages = messages.filter((entry) => {
    if (filterCategory === 'all') return true;
    return entry.kind === filterCategory;
  });
  const filterButtonClass = (value: 'all' | 'thought' | 'action' | 'obs'): string => {
    return `orch-chat-filter-btn${filterCategory === value ? ' active' : ''}`;
  };

  const submitMessage = useCallback(async (text: string) => {
    const workspaceSession = activeRailWorkspaceSession();
    const session = activeOrchestratorRailSession(ip);
    const notifySendFailure = (detail: string) => {
      const entry: OrchestratorFeedEntry = {
        id: `local-send-error:${Date.now()}:${Math.random().toString(36).slice(2)}`,
        kind: 'agent',
        text: `⚠ message not delivered${detail ? ` — ${detail}` : ''}`,
        createdAt: Date.now(),
      };
      setMessages(prev => trimAtlasFeedState(
        coalesceAtlasFeedEntries(prev, [entry] as any[]) as OrchestratorFeedEntry[],
        ORCH_CHAT_FEED_MAX_ENTRIES,
      ));
    };
    try {
      const r = await fetch('/api/pipeline/orchestrator/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          ip,
          ...(session ? { session } : {}),
          ...(workspaceSession ? { workspace_session: workspaceSession } : {}),
        }),
      });
      if (!r.ok) {
        let detail = `HTTP ${r.status}`;
        try {
          const j = await r.json();
          const reason = j && (j.error || j.detail);
          if (reason) detail = `HTTP ${r.status}: ${String(reason)}`;
        } catch (_) { /* non-JSON error body */ }
        notifySendFailure(detail);
        return;
      }
      // The server persists the user message (and ack) before replying —
      // pull them into the feed now instead of waiting for the next poll.
      void fetchOnceRef.current?.();
    } catch (e) {
      notifySendFailure(e instanceof Error ? e.message : String(e));
    }
  }, [ip]);

  const roleClass = (role?: string): string => {
    if (role === 'assistant') return 'md-bubble md-agent';
    if (role === 'user') return 'md-bubble md-user md-agent';
    if (role === 'action' || role === 'obs') return 'md-bubble md-tool';
    if (role === 'thought') return 'md-bubble md-tool';
    return 'md-bubble md-agent';
  };

  return (
    <div className="pipe-orch-chat-shell orch-chat-panel">
      <div className="orch-chat-header">
        <span className="orch-chat-title">ORCHESTRATOR CHAT</span>
        <span className="orch-chat-status" data-active={isActive ? 'yes' : 'no'}>
          {isActive ? 'live' : 'idle'}
        </span>
      </div>
      <div className="orch-chat-filter-bar" aria-label="Orchestrator log category filter">
        <button
          type="button"
          className={filterButtonClass('all')}
          onClick={() => setFilterCategory('all')}
        >
          all
        </button>
        <button
          type="button"
          className={filterButtonClass('thought')}
          onClick={() => setFilterCategory('thought')}
        >
          only thought
        </button>
        <button
          type="button"
          className={filterButtonClass('action')}
          onClick={() => setFilterCategory('action')}
        >
          only action
        </button>
        <button
          type="button"
          className={filterButtonClass('obs')}
          onClick={() => setFilterCategory('obs')}
        >
          only obs
        </button>
      </div>
      <div className="orch-chat-body" ref={bodyRef as Ref<HTMLDivElement>} onScroll={onBodyScroll}>
        {visibleMessages.length === 0 ? (
          <div className="orch-chat-empty mute">
            {hasIp
              ? `No orchestrator activity yet for ${ip}. Send a chat message or run a workflow to see logs here.`
              : 'Pick an IP to see orchestrator chat.'}
          </div>
        ) : visibleMessages.map((m, i) => {
          const role = roleFromFeedEntry(m);
          const header = formatFeedHeader(m);
          return (
            <div
              key={m.id || i}
              className={`orch-chat-row ${roleClass(role)} ${`cat-${m.kind}`}`.trim()}
              data-category={m.kind}
            >
              <span className="orch-chat-role">
                {(role || 'assistant').toUpperCase()} {header ? `(${header})` : ''}
              </span>
              <span className="orch-chat-content">
                {m.text || ''}
              </span>
            </div>
          );
        })}
      </div>
      <OrchestratorChatComposer
        hasIp={hasIp}
        ip={ip}
        onSubmit={submitMessage}
        scrollToBottom={scrollBodyToBottom}
      />
    </div>
  );
}

export function PipelineOrchestratorChatPanel({ ip, pipelineState }: PipelineOrchestratorChatPanelProps) {
  return <PipelineOrchestratorChatPanelImpl ip={ip} pipelineState={pipelineState} />;
}

// ─── Internal: PhaseGroup ──────────────────────────────────────────
//
// Visual grouping of a phase's stage cards into a 2-column grid.
// SIGN-OFF starts collapsed if every stage in the band is idle, since
// most users don't care about the back-end stages until earlier work
// passes. Click the band header to expand/collapse.
interface PhaseGroupPhase {
  id: string;
  stages: string[];
}
export interface PhaseGroupProps {
  phase: PhaseGroupPhase;
  stagesState: Record<string, PipelineStageInfo>;
  ip?: string;
  onChain?: (stageId: string) => void;
  defaultCollapsed?: boolean;
}
export function PhaseGroup({ phase, stagesState, ip, onChain, defaultCollapsed }: PhaseGroupProps) {
  const [collapsed, setCollapsed] = useState(!!defaultCollapsed);
  const stages = phase.stages.filter(s => (w.PIPELINE_STAGES || []).indexOf(s) >= 0);
  // Read window.StageCard at render time (cross-file, owner unmigrated) so a
  // late registration by the owning .jsx is still picked up.
  const StageCardView = w.StageCard as (props: {
    stageId: string;
    info?: PipelineStageInfo;
    ip?: string;
    onChain?: (stageId: string) => void;
  }) => ReactNode;
  return (
    <div className="pipe-phase-group" data-phase={phase.id}>
      <div className="pipe-phase-header" onClick={() => setCollapsed(c => !c)}>
        <span className="pipe-phase-glyph">{collapsed ? '▸' : '▾'}</span>
        <span className="pipe-phase-name">{phase.id}</span>
        <span className="pipe-phase-count mute">({stages.length})</span>
      </div>
      {!collapsed && (
        <div className="pipe-phase-grid">
          {stages.map(s => (
            <StageCardView
              key={s}
              stageId={s}
              info={stagesState[s]}
              ip={ip}
              onChain={onChain} />
          ))}
        </div>
      )}
    </div>
  );
}
