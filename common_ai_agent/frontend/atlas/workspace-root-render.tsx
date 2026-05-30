// workspace-root-render.tsx — TypeScript migration of the Workspace
// center-column render helpers (strangler-fig split).
//
// Owns the EXTRACTED render-helper sub-components that were inline closures in
// the Workspace component (renderFeedEntries / renderWorkerProgress /
// renderChatPane / renderPromptRow / renderOrchestratorFlowStrip). These are
// pure presentational pieces of the chat column; they receive Workspace state
// and handlers as props instead of capturing them from the closure, so they
// can live in their own module while the root composer (workspace-root.tsx)
// wires them up.
//
// Cross-file:
//   - ToolCard / FeedEntry / LiveAgentPreview  ← ./workspace-feed-cards
//   - orchestratorFlowFromFeed                 ← ./workspace-tool-theme
//   - Kbd / AtlasBannerLogic / openPipelineWorkflowWorkspace ← window.*
//   - atlasUiOrchestratorMode / workflowForExecMode /
//     defaultWorkflowForExecMode are passed in as props (owned by
//     workspace-session-routing; the root composer supplies them).
//
// This .tsx is an INERT mirror — the live app is still served by workspace.jsx.
import {
  type ReactNode,
  type CSSProperties,
  type KeyboardEvent,
  type ChangeEvent,
} from 'react';
import { orchestratorFlowFromFeed } from './workspace-tool-theme';
import { ToolCard, FeedEntry, LiveAgentPreview } from './workspace-feed-cards';

// `Kbd` is published on window by shared.tsx for not-yet-migrated consumers;
// read it through window here (the type decls live in atlas-window.d.ts but we
// stay decoupled from them with a permissive cast).
const Kbd: any = (window as any).Kbd
  || (({ children }: { children?: ReactNode }) => <span className="kbd">{children}</span>);

// ── renderWorkspaceFeedEntries ──────────────────────────────────────────────
// Builds the windowed list of feed cards for the chat pane. Pairs adjacent
// action+obs entries into a single ToolCard, wraps orphan obs rows, and falls
// back to FeedEntry for everything else. Caps the rendered slice at
// MAX_RENDERED_FEED_ENTRIES for scroll performance, prepending a notice when
// older entries are hidden.
export interface RenderWorkspaceFeedEntriesProps {
  feed: any[];
  qaState: any;
  chatFeedSummary: boolean;
  toggleOpt: (...args: any[]) => void;
  setCustom: (...args: any[]) => void;
  submitCard: (...args: any[]) => void;
  dir?: string;
}

export const renderWorkspaceFeedEntries = ({
  feed,
  qaState,
  chatFeedSummary,
  toggleOpt,
  setCustom,
  submitCard,
  dir,
}: RenderWorkspaceFeedEntriesProps): ReactNode[] => {
  // Pairing pre-pass: when an action entry is immediately followed by
  // an obs entry, fuse them into one ToolCard. Adjacency is enough —
  // strict tool-name match is too brittle (legacy/normalized entries
  // sometimes leave .tool empty on one side, causing a standalone
  // "OBS" row to leak into the feed).
  const out: ReactNode[] = [];
  const entrySummaryMode = (...entries: any[]): boolean => {
    // Live worker thoughts can contain long retry logs, directory listings,
    // and model scratchpad output. Keep tool results expanded when live, but
    // keep thoughts collapsed so the chat remains a readable flow surface.
    if (entries.some((e) => e && e.kind === 'thought')) return true;
    return entries.some((e) => e && e.live) ? false : chatFeedSummary;
  };
  const MAX_RENDERED_FEED_ENTRIES = 240;
  const renderFeed = feed.length > MAX_RENDERED_FEED_ENTRIES
    ? [
      {
        kind: 'agent',
        text: `Showing latest ${MAX_RENDERED_FEED_ENTRIES} of ${feed.length} chat events. Older entries are hidden in this view for speed.`,
        _feedWindowNotice: true,
      },
      ...feed.slice(-MAX_RENDERED_FEED_ENTRIES),
    ]
    : feed;
  for (let i = 0; i < renderFeed.length; i++) {
    const cur = renderFeed[i];
    const nxt = renderFeed[i + 1];
    if (cur && cur.kind === 'action' && nxt && nxt.kind === 'obs') {
      out.push(<ToolCard key={i} action={cur} obs={nxt} summaryMode={entrySummaryMode(cur, nxt)} />);
      i++;
      continue;
    }
    if (cur && cur.kind === 'action' && cur.tool) {
      out.push(<ToolCard key={i} action={cur} obs={null} summaryMode={entrySummaryMode(cur)} />);
      continue;
    }
    // Orphan obs (action got swallowed, or hydration ordering anomaly):
    // wrap it in a ToolCard so it gets the same single-row collapsed
    // look as paired tools, instead of a separate "OBS" header line.
    if (cur && cur.kind === 'obs') {
      out.push(<ToolCard key={i} action={null} obs={cur} summaryMode={entrySummaryMode(cur)} />);
      continue;
    }
    out.push(
      <FeedEntry
        key={i}
        entry={cur}
        qaState={qaState}
        onToggle={toggleOpt}
        onCustom={setCustom}
        onSubmit={submitCard}
        dir={dir}
        summaryMode={entrySummaryMode(cur)}
      />,
    );
  }
  return out;
};

// ── renderWorkspaceWorkerProgress ───────────────────────────────────────────
// Compact live-status strip for a worker session (hidden in orchestrator mode
// or when no worker progress is being tracked). Shows the workflow name,
// status glyph, elapsed time, and iteration count.
export interface RenderWorkspaceWorkerProgressProps {
  workflow?: string;
  workerProgress: any;
}

export const renderWorkspaceWorkerProgress = ({
  workflow,
  workerProgress,
}: RenderWorkspaceWorkerProgressProps): ReactNode => {
  if (workflow === 'orchestrator' || !workerProgress) return null;
  const wp = workerProgress;
  const status = String(wp.status || '').toLowerCase();
  const done = ['passed', 'done', 'completed'].includes(status);
  const failed = ['failed', 'error', 'cancelled', 'blocked'].includes(status);
  const running = !done && !failed;
  const col = running ? 'var(--accent)' : done ? 'var(--ok, #76c893)' : 'var(--err, #e85d5d)';
  let elapsed = '';
  if (wp.startedAt > 0) {
    const s = Math.max(0, Math.floor(Date.now() / 1000 - wp.startedAt));
    elapsed = s < 60 ? `${s}s` : `${Math.floor(s / 60)}m${String(s % 60).padStart(2, '0')}s`;
  }
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '5px 10px', margin: '0 0 6px', fontFamily: 'var(--mono)', fontSize: 11,
      background: 'var(--panel, #0f1118)', border: '1px solid var(--line)',
      borderRadius: 2,
    }}>
      <span style={{ color: col }}>{running ? '▶' : done ? '✓' : '✗'}</span>
      <b>{wp.workflow}</b>
      <span style={{ color: col }}>{status || 'running'}</span>
      {elapsed ? <span className="mute" style={{ color: 'var(--fg-mute)' }}>· {elapsed}</span> : null}
      {wp.iterations > 0 ? <span className="mute" style={{ color: 'var(--fg-mute)' }}>· iter {wp.iterations}</span> : null}
      <span className="mute" style={{ color: 'var(--fg-dim)', marginLeft: 'auto' }}>
        {running ? 'live worker' : done ? 'worker done' : 'worker stopped'}
      </span>
    </div>
  );
};

// ── WorkspaceChatPane ───────────────────────────────────────────────────────
// Scrollable wrapper around the feed cards plus the live agent preview. The
// feed entries are produced via renderWorkspaceFeedEntries with the supplied
// feed props; the optional `style` override merges into the container.
export interface WorkspaceChatPaneProps {
  feedRef: any;
  streamText: string;
  style?: CSSProperties;
  onScroll?: (...args: any[]) => void;
  feedEntriesProps: RenderWorkspaceFeedEntriesProps;
}

export const WorkspaceChatPane = ({
  feedRef,
  streamText,
  style = {},
  onScroll,
  feedEntriesProps,
}: WorkspaceChatPaneProps) => (
  <div
    ref={feedRef}
    className="workspace-chat-scroll"
    onScroll={onScroll}
    style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '14px 18px', ...style }}
  >
    {renderWorkspaceFeedEntries(feedEntriesProps)}
    <LiveAgentPreview text={streamText} />
  </div>
);

// ── WorkspaceOrchestratorFlowStrip ──────────────────────────────────────────
// Inline "Flow" strip rendered above the prompt row in orchestrator mode. Maps
// a precomputed flow-state (user → orchestrator → worker steps) into a row of
// tone-coloured pills; worker steps are click-through to the worker session.
const flowTone = (tone: string): { color: string; glyph: string; border: string } => {
  if (tone === 'active') return { color: 'var(--accent)', glyph: '▶', border: 'var(--accent)' };
  if (tone === 'done') return { color: 'var(--ok)', glyph: '✓', border: 'var(--ok)' };
  return { color: 'var(--fg-mute)', glyph: '◌', border: 'var(--line-2)' };
};

export interface WorkspaceOrchestratorFlowStripProps {
  flowState: any;
  activeIp?: string;
}

export const WorkspaceOrchestratorFlowStrip = ({
  flowState,
  activeIp,
}: WorkspaceOrchestratorFlowStripProps): ReactNode => {
  if (!flowState || !Array.isArray(flowState.steps) || flowState.steps.length < 2) return null;
  return (
    <div
      className="orchestrator-flow-strip"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '7px 12px',
        margin: '0 0 6px',
        border: '1px solid var(--line)',
        background: 'color-mix(in oklch, var(--bg-2) 88%, transparent)',
        fontFamily: 'var(--mono)',
        fontSize: 11,
        minHeight: 34,
        overflow: 'hidden',
      }}
      title="Current orchestrator flow for the latest chat request"
    >
      <span style={{ color: 'var(--fg-mute)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        Flow
      </span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0, overflow: 'hidden' }}>
        {flowState.steps.map((step: any, idx: number) => {
          const tone = flowTone(step.tone);
          const clickable = step.key === 'worker' && step.workflow;
          const body = (
            <>
              <span style={{ color: tone.color }}>{tone.glyph}</span>
              <span style={{ fontWeight: 700, color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {step.label}
              </span>
              {step.detail ? (
                <span className="mute" style={{ color: 'var(--fg-mute)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {step.detail}
                </span>
              ) : null}
            </>
          );
          return (
            <div key={step.key || idx} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              {idx > 0 ? <span style={{ color: 'var(--fg-dim)' }}>→</span> : null}
              {clickable ? (
                <button
                  type="button"
                  onClick={() => {
                    try {
                      (window as any).openPipelineWorkflowWorkspace?.({
                        ip: String(activeIp || '').trim(),
                        workflow: step.workflow,
                      });
                    } catch (_) {}
                  }}
                  title={`Open ${step.workflow} worker detail`}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 5,
                    minWidth: 0,
                    maxWidth: 220,
                    padding: '3px 8px',
                    border: `1px solid ${tone.border}`,
                    borderRadius: 4,
                    background: 'var(--bg-2)',
                    color: 'var(--fg)',
                    cursor: 'pointer',
                    fontFamily: 'var(--mono)',
                    fontSize: 11,
                  }}
                >
                  {body}
                </button>
              ) : (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 5,
                    minWidth: 0,
                    maxWidth: step.key === 'user' ? 260 : 190,
                    padding: '3px 8px',
                    border: `1px solid ${tone.border}`,
                    borderRadius: 4,
                    background: 'var(--bg)',
                  }}
                >
                  {body}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── WorkspacePromptRow ──────────────────────────────────────────────────────
// The bottom composer: select-an-IP banner (orchestrator-idle), orchestrator
// flow strip, live-worker chip strip, worker-progress strip, the route pill,
// the auto-growing textarea, and the hotkey hint footer. Receives all the
// chat-input state and handlers from the Workspace closure as props, plus the
// exec-mode helpers (owned by workspace-session-routing) so this module need
// not import outside its allowed sibling set.
export interface WorkspacePromptRowProps {
  workflow?: string;
  activeIp?: string;
  feed: any[];
  orchWorkers: any[];
  workerProgress: any;
  input: string;
  setInput: (value: string) => void;
  inputRef: any;
  inputRouteState: any;
  inputRouteRef: any;
  inputHistoryIndexRef: any;
  inputHistoryDraftRef: any;
  onKey: (event: KeyboardEvent<HTMLTextAreaElement>) => void;
  pendingQcard: any;
  workflowReady: any;
  // exec-mode helpers (from workspace-session-routing; supplied by root)
  atlasUiOrchestratorMode: () => boolean;
  workflowForExecMode: (wf: any) => string;
  defaultWorkflowForExecMode: () => string;
}

export const WorkspacePromptRow = ({
  workflow,
  activeIp,
  feed,
  orchWorkers,
  workerProgress,
  input,
  setInput,
  inputRef,
  inputRouteState,
  inputRouteRef,
  inputHistoryIndexRef,
  inputHistoryDraftRef,
  onKey,
  pendingQcard,
  workflowReady,
  atlasUiOrchestratorMode,
  workflowForExecMode,
  defaultWorkflowForExecMode,
}: WorkspacePromptRowProps) => {
  const orchestratorIdle = (window as any).AtlasBannerLogic
    ? (window as any).AtlasBannerLogic.shouldShowSelectIpBanner({ workflow, activeIp })
    : (workflow === 'orchestrator' && (!activeIp || String(activeIp).toLowerCase() === 'default'));
  const currentInputRoute = inputRouteState || inputRouteRef.current || {};
  const inputRouteType = currentInputRoute.type === 'workflow-dispatch'
    ? 'workflow-dispatch'
    : currentInputRoute.type === 'workflow-chat' || !atlasUiOrchestratorMode()
      ? 'workflow-chat'
      : 'orchestrator-chat';
  const inputRouteWorkflow = inputRouteType === 'orchestrator-chat'
    ? 'orchestrator'
    : workflowForExecMode(currentInputRoute.workflow || workflow || defaultWorkflowForExecMode());
  const inputRouteLabel = inputRouteType === 'workflow-dispatch'
    ? `dispatch:${inputRouteWorkflow}`
    : `ask:${inputRouteWorkflow}`;
  const inputRouteTitle = inputRouteType === 'workflow-dispatch'
    ? `This input creates a ${inputRouteWorkflow} workflow job; runtime stays on orchestrator.`
    : `This input goes to the ${inputRouteWorkflow} chat loop.`;
  const flowState = workflow === 'orchestrator'
    ? orchestratorFlowFromFeed(feed, orchWorkers, activeIp)
    : null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {orchestratorIdle ? (
        <div style={{
          padding: '6px 12px',
          margin: '0 0 6px',
          border: '1px solid var(--warn)',
          background: 'color-mix(in oklch, var(--warn) 14%, transparent)',
          color: 'var(--warn)',
          fontSize: 11,
          fontFamily: 'var(--mono)',
          borderRadius: 2,
          display: 'flex', alignItems: 'center', gap: 8,
        }}
          title="The orchestrator needs a real IP to know what to work on. The placeholder 'default' carries no SSOT/RTL data so it loops back without dispatching."
        >
          <span style={{ fontWeight: 700 }}>⚠ Select an IP</span>
          <span className="mute" style={{ color: 'var(--fg-mute)' }}>
            orchestrator needs a real IP — pick one from the IP_ID dropdown or click <b>+ IP</b> at the top to create one. Messages with <code>default</code> are rejected.
          </span>
        </div>
      ) : null}
      <WorkspaceOrchestratorFlowStrip flowState={flowState} activeIp={activeIp} />
      {workflow === 'orchestrator' && orchWorkers.length > 0 ? (
        <div style={{
          display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6,
          padding: '5px 12px', margin: '0 0 6px',
          borderTop: '1px solid var(--line)',
          fontFamily: 'var(--mono)', fontSize: 11,
        }}>
          <span className="mute" style={{ color: 'var(--fg-mute)' }}>workers</span>
          {orchWorkers.map((w: any) => {
            const st = Number(w.running_count || 0) > 0 ? 'running'
              : Number(w.pending_count || 0) > 0 ? 'starting' : 'queued';
            const col = st === 'running' ? 'var(--accent)' : 'var(--warn)';
            return (
              <button key={w.workflow} type="button"
                title={`Open the ${w.workflow} worker session for full live detail`}
                onClick={() => {
                  try {
                    (window as any).openPipelineWorkflowWorkspace?.({
                      ip: String(activeIp || '').trim(), workflow: w.workflow,
                    });
                  } catch (_) {}
                }}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 5,
                  padding: '2px 8px', border: '1px solid var(--line-2)',
                  borderRadius: 10, background: 'var(--bg-2)', cursor: 'pointer',
                  color: 'var(--fg)', fontFamily: 'var(--mono)', fontSize: 11,
                }}>
                <span style={{ color: col }}>{st === 'running' ? '▶' : '◌'}</span>
                <span style={{ fontWeight: 700 }}>{w.workflow}</span>
                <span className="mute" style={{ color: 'var(--fg-mute)' }}>{st}</span>
              </button>
            );
          })}
          <span className="mute" style={{ color: 'var(--fg-dim)', marginLeft: 'auto' }}>click → detail</span>
        </div>
      ) : null}
      {renderWorkspaceWorkerProgress({ workflow, workerProgress })}
      <div className="prompt-row">
        <span className="ps" style={{ color: 'var(--fg-mute)' }}>❯</span>
        {atlasUiOrchestratorMode() && !pendingQcard ? (
          <span
            className="prompt-route-pill"
            data-route={inputRouteType}
            title={inputRouteTitle}
          >
            {inputRouteLabel}
          </span>
        ) : null}
        <textarea ref={inputRef} value={input}
          rows={1}
          disabled={!!workflowReady}
          onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
            inputHistoryIndexRef.current = null;
            inputHistoryDraftRef.current = '';
            setInput(e.target.value);
            // Auto-grow up to 8 rows (~12em). Shrinks back when the user
            // deletes content. min-height keeps the row aligned with the
            // ❯ prompt sigil even when empty.
            const el = e.target;
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 192) + 'px';
          }}
          onKeyDown={onKey}
          placeholder={workflowReady
            ? `Preparing ${workflowReady.target || 'workflow'}...`
            : (pendingQcard
                ? 'Answer pending Q&A here · "/" for commands'
                : 'Type a message · "/" for commands · "@" for files · ⌥↵ newline')}
          autoFocus
        />
        <span className="mute" style={{ fontSize: 11 }}>
          {pendingQcard ? (
            <>
              <Kbd>↵</Kbd> answer · <Kbd>/</Kbd> cmd · <Kbd>↑</Kbd><Kbd>↓</Kbd> history
            </>
          ) : (
            <>
              <Kbd>/</Kbd> cmd · <Kbd>@</Kbd> file · <Kbd>↑</Kbd><Kbd>↓</Kbd> history · <Kbd>↵</Kbd> send · <Kbd>⌥↵</Kbd> newline
            </>
          )}
        </span>
      </div>
    </div>
  );
};
