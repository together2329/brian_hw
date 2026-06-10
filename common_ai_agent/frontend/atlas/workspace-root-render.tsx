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
// This .tsx is used by the Vite workspace entry; workspace.jsx remains only as
// the legacy reference while the extracted helpers continue to carry the same
// workspace closure contracts.
import {
  type ReactNode,
  type CSSProperties,
  type KeyboardEvent,
  type ChangeEvent,
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { orchestratorFlowFromFeed } from './workspace-tool-theme';
import { ToolCard, FeedEntry, LiveAgentPreview } from './workspace-feed-cards';
import {
  promptImageFilesFromClipboard,
  readPromptImageFiles,
  type PromptImageAttachment,
} from './workspace-prompt-images';

// `Kbd` is published on window by shared.tsx for not-yet-migrated consumers;
// read it through window here (the type decls live in atlas-window.d.ts but we
// stay decoupled from them with a permissive cast).
const Kbd: any = (window as any).Kbd
  || (({ children }: { children?: ReactNode }) => <span className="kbd">{children}</span>);
// Parent input sync: slash/@ drafts need the root to see the text quickly
// (the completion popups are root-rendered), but plain prose can wait — every
// sync costs a full Workspace-root re-render, which is what makes fast typing
// stutter on large sessions.
const PARENT_INPUT_SYNC_DELAY_MS = 60;
const PARENT_INPUT_SYNC_IDLE_DELAY_MS = 240;
const parentInputSyncDelayFor = (next: string): number => (
  /^\/\S*$/.test(next) || /(^|\s)@\S*$/.test(next)
    ? PARENT_INPUT_SYNC_DELAY_MS
    : PARENT_INPUT_SYNC_IDLE_DELAY_MS
);

// ── ATLAS_INPUT_PERF — live input-latency meter (opt-in) ────────────────────
// Enable with localStorage.ATLAS_PERF = '1' (or load with ?perf=1), then
// reload. The composer stamps keystroke→paint latency, the Workspace root
// increments rootRenders, and WorkspaceInputPerfHud (rendered in the prompt
// row) shows both live so re-render storms are visible while typing.
export const ATLAS_INPUT_PERF = {
  enabled: false,
  keyToPaintMs: 0,
  keyToPaintMaxMs: 0,
  rootRenders: 0,
  parentSyncs: 0,
};
try {
  ATLAS_INPUT_PERF.enabled =
    (typeof localStorage !== 'undefined' && localStorage.getItem('ATLAS_PERF') === '1')
    || (typeof location !== 'undefined' && /[?&]perf=1\b/.test(location.search));
} catch (_) { /* storage blocked — meter stays off */ }

export type WorkspacePromptKeyResult = 'handled' | 'submitted' | void;

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

const sameFeedEntriesProps = (
  prev: RenderWorkspaceFeedEntriesProps,
  next: RenderWorkspaceFeedEntriesProps,
): boolean => (
  prev.feed === next.feed
  && prev.qaState === next.qaState
  && prev.chatFeedSummary === next.chatFeedSummary
  && prev.toggleOpt === next.toggleOpt
  && prev.setCustom === next.setCustom
  && prev.submitCard === next.submitCard
  && prev.dir === next.dir
);

const WorkspaceFeedList = memo(
  ({ feedEntriesProps }: { feedEntriesProps: RenderWorkspaceFeedEntriesProps }) => {
    const entries = useMemo(
      () => renderWorkspaceFeedEntries(feedEntriesProps),
      [
        feedEntriesProps.feed,
        feedEntriesProps.qaState,
        feedEntriesProps.chatFeedSummary,
        feedEntriesProps.toggleOpt,
        feedEntriesProps.setCustom,
        feedEntriesProps.submitCard,
        feedEntriesProps.dir,
      ],
    );
    return <>{entries}</>;
  },
  (prev, next) => sameFeedEntriesProps(prev.feedEntriesProps, next.feedEntriesProps),
);

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
    <div className="workspace-chat-content" data-workspace-chat-content="true" style={{ minHeight: '100%' }}>
      <WorkspaceFeedList feedEntriesProps={feedEntriesProps} />
      <LiveAgentPreview text={streamText} />
    </div>
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
  inputResetToken?: number;
  promptImages?: readonly PromptImageAttachment[];
  onPastedPromptImages?: (images: readonly PromptImageAttachment[]) => void;
  onRemovePromptImage?: (id: string) => void;
  inputRef: any;
  inputRouteState: any;
  inputRouteRef: any;
  inputHistoryIndexRef: any;
  inputHistoryDraftRef: any;
  onKey: (event: KeyboardEvent<HTMLTextAreaElement>) => WorkspacePromptKeyResult;
  pendingQcard: any;
  workflowReady: any;
  // exec-mode helpers (from workspace-session-routing; supplied by root)
  atlasUiOrchestratorMode: () => boolean;
  workflowForExecMode: (wf: any) => string;
  defaultWorkflowForExecMode: () => string;
}

interface WorkspacePromptComposerProps {
  input: string;
  setInput: (value: string) => void;
  inputResetToken: number;
  promptImages?: readonly PromptImageAttachment[];
  onPastedPromptImages?: (images: readonly PromptImageAttachment[]) => void;
  onRemovePromptImage?: (id: string) => void;
  inputRef: any;
  inputRouteType: string;
  inputRouteTitle: string;
  inputRouteLabel: string;
  showRoutePill: boolean;
  inputHistoryIndexRef: any;
  inputHistoryDraftRef: any;
  onKey: (event: KeyboardEvent<HTMLTextAreaElement>) => WorkspacePromptKeyResult;
  pendingQcard: any;
  workflowReady: any;
  workflowReadyBlocking: boolean;
}

// Tiny opt-in HUD (see ATLAS_INPUT_PERF above). Self-ticking on a 500ms
// interval so it stays live inside the memo'd composer without subscribing
// the composer itself to perf-store changes.
const WorkspaceInputPerfHud = memo(function WorkspaceInputPerfHud() {
  const [snap, setSnap] = useState({ keyMs: 0, maxMs: 0, rootPerSec: 0, syncs: 0 });
  const tickRef = useRef<{ renders: number; at: number }>({ renders: 0, at: 0 });
  useEffect(() => {
    if (!ATLAS_INPUT_PERF.enabled) return;
    tickRef.current = { renders: ATLAS_INPUT_PERF.rootRenders, at: performance.now() };
    const id = setInterval(() => {
      const now = performance.now();
      const prev = tickRef.current;
      const rootPerSec = (ATLAS_INPUT_PERF.rootRenders - prev.renders)
        / Math.max(0.001, (now - prev.at) / 1000);
      tickRef.current = { renders: ATLAS_INPUT_PERF.rootRenders, at: now };
      setSnap({
        keyMs: ATLAS_INPUT_PERF.keyToPaintMs,
        maxMs: ATLAS_INPUT_PERF.keyToPaintMaxMs,
        rootPerSec,
        syncs: ATLAS_INPUT_PERF.parentSyncs,
      });
    }, 500);
    return () => clearInterval(id);
  }, []);
  if (!ATLAS_INPUT_PERF.enabled) return null;
  return (
    <span
      className="mute"
      style={{ fontSize: 11, fontFamily: 'var(--mono)', whiteSpace: 'nowrap' }}
      title={'Input perf meter — keystroke→paint latency · Workspace root renders/sec · '
        + 'debounced parent input syncs. Disable: localStorage.removeItem("ATLAS_PERF")'}
    >
      ⌨ {snap.keyMs.toFixed(0)}ms (max {snap.maxMs.toFixed(0)}) · root {snap.rootPerSec.toFixed(1)}/s · sync {snap.syncs}
    </span>
  );
});

const WorkspacePromptComposer = memo(function WorkspacePromptComposer({
  input,
  setInput,
  inputResetToken = 0,
  promptImages = [],
  onPastedPromptImages,
  onRemovePromptImage,
  inputRef,
  inputRouteType,
  inputRouteTitle,
  inputRouteLabel,
  showRoutePill,
  inputHistoryIndexRef,
  inputHistoryDraftRef,
  onKey,
  pendingQcard,
  workflowReady,
  workflowReadyBlocking,
}: WorkspacePromptComposerProps) {
  const [draftInput, setDraftInput] = useState<string>(input);
  const draftInputRef = useRef<string>(input);
  const localDraftDirtyRef = useRef<boolean>(false);
  const lastLocalParentSyncRef = useRef<string | null>(null);
  const resetTokenRef = useRef<number>(inputResetToken);
  const parentSyncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const resizeInput = useCallback((el: HTMLTextAreaElement | null) => {
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 192) + 'px';
  }, []);
  const clearParentInputSync = useCallback(() => {
    if (parentSyncTimerRef.current === null) return;
    clearTimeout(parentSyncTimerRef.current);
    parentSyncTimerRef.current = null;
  }, []);
  const applyDraftInput = useCallback((next: string) => {
    draftInputRef.current = next;
    setDraftInput(next);
  }, []);
  const scheduleParentInputSync = useCallback((next: string) => {
    clearParentInputSync();
    parentSyncTimerRef.current = setTimeout(() => {
      parentSyncTimerRef.current = null;
      lastLocalParentSyncRef.current = next;
      if (ATLAS_INPUT_PERF.enabled) ATLAS_INPUT_PERF.parentSyncs += 1;
      setInput(next);
    }, parentInputSyncDelayFor(next));
  }, [clearParentInputSync, setInput]);
  const updateDraftFromUser = useCallback((next: string, el: HTMLTextAreaElement) => {
    localDraftDirtyRef.current = true;
    if (ATLAS_INPUT_PERF.enabled) {
      const t0 = performance.now();
      // Double rAF ≈ after the next paint commits — what the eye sees.
      requestAnimationFrame(() => requestAnimationFrame(() => {
        const dt = performance.now() - t0;
        ATLAS_INPUT_PERF.keyToPaintMs = dt;
        if (dt > ATLAS_INPUT_PERF.keyToPaintMaxMs) ATLAS_INPUT_PERF.keyToPaintMaxMs = dt;
      }));
    }
    inputHistoryIndexRef.current = null;
    inputHistoryDraftRef.current = '';
    applyDraftInput(next);
    scheduleParentInputSync(next);
    resizeInput(el);
  }, [applyDraftInput, inputHistoryDraftRef, inputHistoryIndexRef, resizeInput, scheduleParentInputSync]);
  const clearDraftAfterSubmittedKey = useCallback((el: HTMLTextAreaElement) => {
    clearParentInputSync();
    localDraftDirtyRef.current = false;
    lastLocalParentSyncRef.current = null;
    applyDraftInput('');
    resizeInput(el);
  }, [applyDraftInput, clearParentInputSync, resizeInput]);
  useEffect(() => clearParentInputSync, [clearParentInputSync]);
  useEffect(() => {
    if (resetTokenRef.current === inputResetToken) return;
    resetTokenRef.current = inputResetToken;
    clearParentInputSync();
    localDraftDirtyRef.current = false;
    lastLocalParentSyncRef.current = null;
    applyDraftInput(input);
  }, [applyDraftInput, clearParentInputSync, input, inputResetToken]);
  useEffect(() => {
    if (input === draftInputRef.current) {
      localDraftDirtyRef.current = false;
      lastLocalParentSyncRef.current = null;
      return;
    }
    if (localDraftDirtyRef.current && input === lastLocalParentSyncRef.current) return;
    clearParentInputSync();
    localDraftDirtyRef.current = false;
    lastLocalParentSyncRef.current = null;
    applyDraftInput(input);
  }, [applyDraftInput, clearParentInputSync, input]);
  useEffect(() => {
    requestAnimationFrame(() => resizeInput(inputRef.current));
  }, [draftInput, inputRef, resizeInput]);
  const handlePasteImages = useCallback((clipboardData: DataTransfer | null) => {
    const files = promptImageFilesFromClipboard(clipboardData);
    if (!files.length || !onPastedPromptImages) return false;
    void readPromptImageFiles(files)
      .then((images) => {
        if (images.length) onPastedPromptImages(images);
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : String(error);
        console.warn('Unable to attach pasted image:', message);
      });
    return true;
  }, [onPastedPromptImages]);

  return (
    <div className="prompt-row">
      <span className="ps" style={{ color: 'var(--fg-mute)' }}>❯</span>
      {showRoutePill ? (
        <span
          className="prompt-route-pill"
          data-route={inputRouteType}
          title={inputRouteTitle}
        >
          {inputRouteLabel}
        </span>
      ) : null}
      {promptImages.length ? (
        <span style={{
          display: 'inline-flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 4,
          maxWidth: 260,
        }}>
          {promptImages.map((image, index) => (
            <button
              key={image.id}
              type="button"
              title={`Remove ${image.name}`}
              onClick={() => onRemovePromptImage?.(image.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                maxWidth: 130,
                minHeight: 24,
                padding: '2px 6px',
                borderRadius: 4,
                border: '1px solid var(--line-2)',
                background: 'var(--bg-2)',
                color: 'var(--fg)',
                fontFamily: 'var(--mono)',
                fontSize: 11,
                cursor: 'pointer',
                overflow: 'hidden',
              }}
            >
              <span style={{ color: 'var(--accent)' }}>▧{index + 1}</span>
              <span style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}>
                {image.name}
              </span>
              <span aria-hidden="true" style={{ color: 'var(--fg-mute)' }}>×</span>
            </button>
          ))}
        </span>
      ) : null}
      <textarea ref={inputRef} value={draftInput}
        rows={1}
        disabled={workflowReadyBlocking}
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
          updateDraftFromUser(e.target.value, e.target);
        }}
        onPaste={(e) => {
          if (!handlePasteImages(e.clipboardData)) return;
          e.preventDefault();
        }}
        onKeyDown={(e: KeyboardEvent<HTMLTextAreaElement>) => {
          if (e.key === 'Enter' && e.altKey) {
            e.preventDefault();
            const el = e.currentTarget;
            const lo = el.selectionStart;
            const hi = el.selectionEnd;
            const next = el.value.slice(0, lo) + '\n' + el.value.slice(hi);
            updateDraftFromUser(next, el);
            requestAnimationFrame(() => {
              el.selectionStart = el.selectionEnd = lo + 1;
              resizeInput(el);
            });
            return;
          }
          const result = onKey(e);
          if (result === 'submitted') {
            clearDraftAfterSubmittedKey(e.currentTarget);
          }
        }}
        placeholder={workflowReadyBlocking
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
      <WorkspaceInputPerfHud />
    </div>
  );
});

export const WorkspacePromptRow = ({
  workflow,
  activeIp,
  feed,
  orchWorkers,
  workerProgress,
  input,
  setInput,
  inputResetToken = 0,
  promptImages = [],
  onPastedPromptImages,
  onRemovePromptImage,
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
  const workflowReadyBlocking = !!(workflowReady && workflowReady.phase !== 'ready');
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
            const blocked = Number(w.blocked_count || 0);
            // Blocked jobs are surfaced as a non-green (err) state so a stalled
            // owner is visible in the strip — running still wins so an active
            // worker with one blocked job reads as running.
            const st = Number(w.running_count || 0) > 0 ? 'running'
              : blocked > 0 ? 'blocked'
              : Number(w.pending_count || 0) > 0 ? 'starting' : 'queued';
            const col = st === 'running' ? 'var(--accent)'
              : st === 'blocked' ? 'var(--err)' : 'var(--warn)';
            const glyph = st === 'running' ? '▶' : st === 'blocked' ? '⏸' : '◌';
            return (
              <button key={w.workflow} type="button"
                data-worker-state={st}
                title={`Open the ${w.workflow} worker session for full live detail${blocked ? ` (${blocked} blocked)` : ''}`}
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
                <span style={{ color: col }}>{glyph}</span>
                <span style={{ fontWeight: 700 }}>{w.workflow}</span>
                <span className="mute" style={{ color: st === 'blocked' ? 'var(--err)' : 'var(--fg-mute)' }}>
                  {st}{blocked > 0 ? ` ${blocked}` : ''}
                </span>
              </button>
            );
          })}
          <span className="mute" style={{ color: 'var(--fg-dim)', marginLeft: 'auto' }}>click → detail</span>
        </div>
      ) : null}
      {renderWorkspaceWorkerProgress({ workflow, workerProgress })}
      <WorkspacePromptComposer
        input={input}
        setInput={setInput}
        inputResetToken={inputResetToken}
        promptImages={promptImages}
        onPastedPromptImages={onPastedPromptImages}
        onRemovePromptImage={onRemovePromptImage}
        inputRef={inputRef}
        inputRouteType={inputRouteType}
        inputRouteTitle={inputRouteTitle}
        inputRouteLabel={inputRouteLabel}
        showRoutePill={atlasUiOrchestratorMode() && !pendingQcard}
        inputHistoryIndexRef={inputHistoryIndexRef}
        inputHistoryDraftRef={inputHistoryDraftRef}
        onKey={onKey}
        pendingQcard={pendingQcard}
        workflowReady={workflowReady}
        workflowReadyBlocking={workflowReadyBlocking}
      />
    </div>
  );
};
