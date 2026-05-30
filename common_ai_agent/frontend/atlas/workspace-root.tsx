/* workspace-root.tsx — THE COMPOSER + root component of the ATLAS workspace.
 *
 * Final slice of the strangler-fig migration of workspace.jsx. This module
 * owns the two top-level symbols that assemble everything else:
 *
 *   - Workspace : the giant grid root component (legacy L1886 signature +
 *     L5979–L7199 JSX return). It calls the two state hooks
 *     (useWorkspaceSession + useWorkspaceData), pulls in the render-helper
 *     sub-components, and renders the 5-track layout (left rail · splitter ·
 *     center tabs · splitter · right rail). It registers `window.Workspace`
 *     so app-shell.tsx (which reads `window.Workspace`) can mount it.
 *   - RightTab : the small right-rail tab-label span (legacy L7202).
 *
 * Architecture: the heavy body logic (state, effects, callbacks, derived
 * values, and the bound render helpers `renderChatPane`/`renderPromptRow`)
 * lives in the two hooks. The composer merges their return objects and
 * destructures the locals the JSX needs. Hook returns are permissively typed
 * `any` on purpose — these are window-bridged, dynamically-shaped objects.
 *
 * Panel children are read from `window` exactly as the legacy file does
 * (L13257–L13286): SsotReviewPane / SsotQaBoard / SsotDocPane / PreviewPane /
 * AskUserPrompt / AgentStatusPanel / ProgressPanel / TodoPanel /
 * OrchestratorChatPanel / GitPanel. Layout helpers + the SCM/file panes that
 * were migrated into sibling .tsx modules are imported from those siblings.
 *
 * INERT mirror — the live app is still served by workspace.jsx. The gate is:
 * tsc-clean + vitest-green + window.Workspace registered + public exports
 * intact. Do NOT treat this as the live source of truth.
 */
import { type ReactNode, useMemo, useRef, useState } from 'react';

import { ErrorBoundary } from './app-helpers';
import { Splitter } from './workspace-resize-splitters';
import { WorkflowReadyOverlay } from './workspace-workflow-ready';
import { isSsotYamlPath, normalizeUiSession } from './workspace-session-routing';
import {
  GitDiffPane,
  FileViewer,
  WorkflowReportPane,
} from './workspace-git-diff';
import { TodoEditorPane } from './workspace-todo';
import { useWorkspaceSession, type UseWorkspaceSessionDeps } from './workspace-root-session-hook';
import { useWorkspaceData, type WorkspaceDataDeps } from './workspace-root-data-hook';
import {
  renderWorkspaceLeftRail,
  renderWorkspaceCenterTabStrip,
} from './workspace-rootui-rail-tabs';

// `Kbd` is published on window by shared.tsx for not-yet-migrated consumers;
// read it through window here with a permissive cast + inline fallback so the
// mirror stays decoupled from the global type decls.
const Kbd: any = (window as any).Kbd
  || (({ children }: { children?: ReactNode }) => <span className="kbd">{children}</span>);

// Panel children are read from window, identical to the legacy workspace.jsx
// tail (L13257–L13286). These ATLAS panels live in sibling files / earlier
// bundles that publish themselves onto window before Workspace mounts.
const SsotReviewPane: any = (window as any).SsotReviewPane;
const SsotQaBoard: any = (window as any).SsotQaBoard;
const SsotDocPane: any = (window as any).SsotDocPane;
const PreviewPane: any = (window as any).PreviewPane;
const AskUserPrompt: any = (window as any).AskUserPrompt;
const ProgressPanel: any = (window as any).ProgressPanel;
const TodoPanel: any = (window as any).TodoPanel;
const OrchestratorChatPanel: any = (window as any).OrchestratorChatPanel;
const GitPanel: any = (window as any).GitPanel;
const AgentStatusPanel: any = (window as any).AgentStatusPanel;

// `window` carries the runtime ATLAS bridges (FLOW_STAGES, TODOS, CONTEXT,
// FILE_TREE_*, ACTIVE_SESSION, backend, etc.). Aliased to `any` so the dozens
// of window reads inside the JSX stay permissive without touching the shared
// type decls.
const w: any = window;

// ── Workspace : root composer ──────────────────────────────────────
// Two-axis mode model (intent: normal|plan, workflow: null|ssot|…) plus the
// resizable 5-track grid. All state + effects + callbacks live in the two
// hooks; this component just wires them to the layout.
export const Workspace = ({
  dir,
  onScreen,
  uiLang = 'ko',
  activeNamespace = '',
  activeWorkflow = '',
}: {
  dir?: string;
  onScreen?: (...args: any[]) => void;
  uiLang?: string;
  activeNamespace?: string;
  activeWorkflow?: string;
}) => {
  // The two state hooks share a circular deps contract: useWorkspaceSession
  // consumes data-hook-owned primitives (setStreaming/streamingRef/
  // streamBufferRef/setStreamText/setMainTab) while useWorkspaceData consumes
  // session-hook-owned values (intent/switchIntent/resolveSession/…) plus the
  // base feed/session state. The single-closure original wired these implicitly;
  // in the split mirror the composer threads them. The exact deps shapes are
  // still being finalized by the sibling hooks, so the dep bags are passed
  // through an `any` cast here — the root/repair phase reconciles the precise
  // bootstrap ordering once both hook contracts freeze. (These .tsx are inert
  // mirrors; behavior is not exercised at runtime in this phase.)
  // Shared streaming/DOM primitives that BOTH hooks consume. The legacy
  // single-closure original (workspace.jsx L2734-L2736, L3512-L3513) created
  // these at the component top so the session-half (sendPrompt/switchWorkflow)
  // and the data-half (live worker poll / chat submit) could share one source
  // of truth. The composer mirrors that by creating them here and threading
  // them into both dep bags. `streaming` drives the Agent-running spinner and
  // is re-surfaced through the data hook's return for the JSX destructure.
  const [streaming, setStreaming] = useState<boolean>(false);
  const streamingRef = useRef<boolean>(false);
  const streamBufferRef = useRef<string>('');
  const inputRef = useRef<any>(null);
  const feedRef = useRef<any>(null);
  // streamText + mainTab were previously OWNED by useWorkspaceData, but
  // useWorkspaceSession (which runs FIRST) needs their setters in its deps
  // (handleSwitchSession clears streamText; switchWorkflow flips mainTab). The
  // data hook can't supply them at the session-hook call site — it hasn't run
  // yet (circular ordering). So they are lifted here next to streaming and
  // threaded into BOTH dep bags, exactly the composer-owned pattern the comment
  // at the top of this block describes. This is what lets sessionDeps be typed
  // as UseWorkspaceSessionDeps instead of `any`.
  const [streamText, setStreamText] = useState<string>('');
  const [mainTab, setMainTab] = useState<string>('chat');

  const sessionDeps: UseWorkspaceSessionDeps = {
    uiLang,
    activeNamespace,
    activeWorkflow,
    setStreaming,
    streamingRef,
    streamBufferRef,
    setStreamText,
    setMainTab,
  };
  const session = useWorkspaceSession(sessionDeps);

  // Data hook: SSOT/QA boards, worker progress, telemetry, file tree, tab
  // visibility flags, and the bound render helpers (renderChatPane/
  // renderPromptRow) that close over the live feed + input state.
  //
  // Typed as WorkspaceDataDeps (NOT `any`) so tsc threads the session-half
  // contract end-to-end: the moment a required dep is missing (it was — the old
  // `as any` cast silently dropped `activeNamespace`, leaving deps.activeNamespace
  // undefined at runtime) or mistyped, this object literal ERRORS at the call
  // site. This is the type-gate that would have caught the submitMsg stub.
  //
  // Memoized so its identity is stable across renders that don't change a dep —
  // submitMsg's useCallback and the held-input replay effect read individual
  // fields off the threaded contract, and a fresh object every render would
  // needlessly churn the bootstrap. `session` is spread for the session-half
  // values; the explicit fields are the composer-owned shared primitives.
  const dataDeps = useMemo<WorkspaceDataDeps>(() => ({
    ...session,
    dir,
    activeNamespace,
    streaming,
    setStreaming,
    streamingRef,
    streamBufferRef,
    inputRef,
    feedRef,
    // Composer-owned (lifted above) so the session hook can receive the setters
    // in its deps despite running first. The data hook reads the state/setters
    // off deps and re-surfaces them in its return for the JSX destructure.
    streamText,
    setStreamText,
    mainTab,
    setMainTab,
  }), [session, dir, activeNamespace, streaming, streamText, mainTab]);
  const data = useWorkspaceData(dataDeps);

  // Merge the two hook surfaces so destructuring below reads from one bag.
  // (session first, data second — data wins on the few overlapping derived
  // keys it recomputes from session state.)
  //
  // THE TYPE GATE: `ws` is the INTERSECTION of both hook return types plus the
  // handful of defensive, optional reads the JSX does directly off `ws.*`
  // (effLeftW/effRightW are derived locally with a `typeof === 'number'` guard;
  // normalizeUiSession is reached via optional-chaining). Typing this bag — not
  // `any` — means tsc ERRORS the moment the destructure below names a symbol
  // neither hook returns. An `any` bag silently swallowed 15 such undefined
  // destructures; this turns that runtime break into a compile error.
  type WorkspaceComposerExtras = {
    effLeftW?: number;
    effRightW?: number;
    normalizeUiSession?: (s: string) => string;
  };
  type WorkspaceBag = ReturnType<typeof useWorkspaceSession>
    & ReturnType<typeof useWorkspaceData>
    & WorkspaceComposerExtras;
  const ws: WorkspaceBag = { ...session, ...data };

  const {
    // intent / workflow
    intent,
    workflow,
    workflowReady,
    switchIntent,
    switchWorkflow,
    // column widths + collapse toggles
    leftW, setLeftW, toggleLeft,
    rightW, setRightW, toggleRight,
    splitRightW, setSplitRightW,
    leftWorkflowH, setLeftWorkflowH, resetLeftWorkflowH,
    // mobile drawers
    isMobile,
    leftDrawerOpen, setLeftDrawerOpen,
    rightDrawerOpen, setRightDrawerOpen,
    mobileHintDismissed, setMobileHintDismissed,
    // file tree + context menu
    filePanelIp,
    filePanelStatus,
    fileSort, setFileSort,
    fileExpand, setFileExpand,
    collapsedFileDirs, setCollapsedFileDirs,
    visibleFileTree,
    fileContextMenu, setFileContextMenu,
    deleteIpTreeFile,
    // center tabs
    // (mainTab/setMainTab are composer-owned — declared above via useState and
    // threaded into BOTH hook dep bags; the data hook re-surfaces them in its
    // return, but the composer's own state is the authoritative in-scope binding,
    // so they are NOT re-destructured here. Re-binding would shadow-redeclare.)
    previewPath, setPreviewPath,
    gitShow, setGitShow,
    openFile, setOpenFile,
    centerLayout,
    // tab visibility flags
    showSimSummaryTab,
    showDebugTab,
    showCoverageTab,
    showWorkflowReportTab,
    showSsotImportExportTab,
    showQaTab,
    showSsotChecklistTab,
    showSsotTab,
    showSsotDocTab,
    showBuiltinGitTab,
    // workflow report meta
    workflowReportMeta,
    // session / ip
    activeIp,
    activeSession,
    currentSession,
    activeSsotIp,
    // ssot QA board
    ssotQa,
    ssotQaBoardData,
    ssotQaSessions,
    ssotApproval,
    activateSsotQaSession,
    refreshSsotQa,
    refreshSsotQaSessions,
    // ask_user / qa card
    pendingQcard,
    qaState,
    askSel, setAskSel,
    toggleOpt,
    setCustom,
    submitCard,
    setActiveTab,
    advanceBatchedQuestion,
    // input + slash/@ completion
    // (inputRef is composer-owned — declared above and threaded into BOTH hook
    // dep bags; the data hook re-surfaces it in its return, but the composer's
    // own ref is the authoritative in-scope binding, so it is NOT re-destructured
    // here. Re-binding it would shadow-redeclare the const.)
    input, setInput,
    showSlash, slashSel, setSlashSel, filtered,
    showAt, atQuery, atSel, setAtSel, fileMatches, atDirEntries,
    acceptAtCompletion,
    submitMsg,
    // sendPrompt — the canonical chat-hub prompt sender (generates msg_id, ack
    // Promise, and retry-armed {type:'prompt', msg_id, ...}). Routed into the
    // QA-board onSubmitPending handler so that send opts into ack/retry too.
    sendPrompt,
    // feed + streaming
    // (streaming is composer-owned — declared above via useState and threaded
    // into BOTH hook dep bags; the data hook re-surfaces it in its return for
    // completeness, but the composer's own state is the authoritative in-scope
    // binding, so it is NOT re-destructured here.)
    feed, setFeed,
    backendState,
    commandBusy,
    workerProgress,
    orchWorkers,
    workspaceTelemetry,
    // right rail
    rightTab, setRightTab,
    // bound render helpers (close over feed/input/stream state)
    renderChatPane,
    renderPromptRow,
  } = ws;

  // Effective widths — sim_debug/coverage workflows can claim the full
  // viewport; widths are preserved so switching back restores the layout.
  const effLeftW: number = typeof ws.effLeftW === 'number' ? ws.effLeftW : leftW;
  const effRightW: number = typeof ws.effRightW === 'number' ? ws.effRightW : rightW;

  // SCM provider resolution (deployment-specific tab + the built-in Git
  // companion). The hooks expose the resolved values; fall back defensively.
  const scmProvider: any = ws.scmProvider;
  const ScmTabComponent: any = ws.ScmTabComponent;
  const scmTabLabel: any = ws.scmTabLabel;

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `${leftW}px 4px 1fr 4px ${rightW}px`,
      gap: 12,
      padding: 16,
      height: '100%', overflow: 'hidden',
    }}>
      <WorkflowReadyOverlay state={workflowReady} />
      {/* Hand the helper the COMPOSER-derived effLeftW/effRightW. The raw `ws`
          bag has no effLeftW key (neither hook returns it — it is computed
          locally at the effLeftW const above), so renderWorkspaceLeftRail's
          `effLeftW > 0` gate would read `undefined > 0` === false and collapse
          the entire left panel to the empty grid cell while the grid still
          reserves ${leftW}px — i.e. a present-but-blank left column. Inject the
          resolved widths so the gate sees the real number. */}
      {renderWorkspaceLeftRail({ ...ws, effLeftW, effRightW })}

      {/* LEFT ↔ CENTER splitter — keep visible at 0px so collapsed panels can reopen. */}
      <Splitter width={leftW} side="left" onResize={setLeftW} onToggle={toggleLeft} />

      {/* CENTER — workflow-specific tabs can claim the first screen. */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        {intent === 'plan' && (
          <div style={{
            padding: '6px 14px', border: '1px solid var(--warn)',
            background: 'color-mix(in oklch, var(--warn) 12%, transparent)',
            color: 'var(--warn)', fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em',
            display: 'flex', alignItems: 'center', gap: 10, borderRadius: 2,
          }}>
            <span style={{ fontWeight: 700, textTransform: 'uppercase' }}>◐ Plan mode</span>
            <span style={{ flex: 1 }}>Read-only · agent will analyze and propose, but will not write or run any tools.</span>
            <button className="btn" onClick={() => switchIntent('normal')}
              style={{ borderColor: 'var(--warn)', color: 'var(--warn)', fontSize: 10 }}>
              Apply &amp; switch to Normal <Kbd>⌘ ↵</Kbd>
            </button>
          </div>
        )}
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {renderWorkspaceCenterTabStrip(ws)}
          {mainTab === 'coverage' ? (
            typeof w.Coverage === 'function' ? (
              <ErrorBoundary label="Coverage">
                <w.Coverage />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                Coverage · loading…
              </div>
            )
          ) : mainTab === 'workflow_report' ? (
            <WorkflowReportPane workflow={workflow} activeIp={activeIp} />
          ) : mainTab === 'checklist' ? (
            <SsotQaBoard
              data={ssotQaBoardData}
              sessions={ssotQaSessions}
              activeSession={currentSession}
              uiLang={uiLang}
              onSelectSession={activateSsotQaSession}
              onBack={() => setMainTab('chat')}
              onRefresh={() => { refreshSsotQa(); refreshSsotQaSessions(); }}
              onRunCommand={submitMsg}
              showChecklist={true}
              checklistOnly={true}
            />
          ) : mainTab === 'import_export' ? (
            <SsotQaBoard
              data={ssotQaBoardData}
              sessions={ssotQaSessions}
              activeSession={currentSession}
              uiLang={uiLang}
              onSelectSession={activateSsotQaSession}
              onBack={() => setMainTab('chat')}
              onRefresh={() => { refreshSsotQa(); refreshSsotQaSessions(); }}
              onRunCommand={submitMsg}
              importExportOnly={true}
            />
          ) : mainTab === 'chat' ? (
            renderChatPane()
          ) : (mainTab === 'split' || mainTab === 'preview') ? (() => {
            // Unified split/full-view layout — chat | splitter | preview.
            const fullView = mainTab === 'preview';
            const splitColumns = fullView
              ? '0px 4px minmax(0, 1fr)'
              : `minmax(260px, 1fr) 4px minmax(300px, ${splitRightW}px)`;
            return (
              <div style={{
                flex: 1, minHeight: 0, display: 'grid',
                gridTemplateColumns: splitColumns,
                transition: fullView ? 'grid-template-columns 0.35s cubic-bezier(0.2, 0.8, 0.2, 1)' : 'none',
                overflow: 'hidden',
              }}>
                <div style={{
                  minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column',
                  overflow: 'hidden',
                  visibility: fullView ? 'hidden' : 'visible',
                }}>
                  <div style={{
                    padding: '4px 10px', borderBottom: '1px solid var(--line)',
                    color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10,
                    letterSpacing: '0.06em', textTransform: 'uppercase',
                  }}>
                    chat stream
                  </div>
                  {renderChatPane({ padding: '10px 12px' })}
                </div>
                <div style={{
                  visibility: fullView ? 'hidden' : 'visible',
                  pointerEvents: fullView ? 'none' : 'auto',
                }}>
                  <Splitter
                    width={splitRightW}
                    side="right"
                    onResize={setSplitRightW}
                    title="drag to resize chat / preview split"
                  />
                </div>
                <div style={{ minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                  {gitShow ? (
                    <GitDiffPane
                      sha={gitShow.sha}
                      ip={gitShow.ip}
                      subject={gitShow.subject}
                      onClose={() => setGitShow(null)}
                    />
                  ) : isSsotYamlPath(previewPath) ? (
                    <ErrorBoundary label="SSOTPreview">
                      <SsotReviewPane uiLang={uiLang} initialPath={previewPath} onBack={() => setMainTab('chat')} />
                    </ErrorBoundary>
                  ) : (
                    <ErrorBoundary label="Preview">
                      <PreviewPane path={previewPath} onClose={() => setMainTab('chat')} />
                    </ErrorBoundary>
                  )}
                </div>
              </div>
            );
          })() : mainTab === 'ssot' ? (
            <SsotReviewPane
              uiLang={uiLang}
              initialPath={isSsotYamlPath(previewPath) ? previewPath : ''}
              onBack={() => setMainTab('chat')}
            />
          ) : mainTab === 'doc' ? (
            <SsotDocPane
              uiLang={uiLang}
              ip={activeSsotIp()}
              onBack={() => setMainTab('chat')}
            />
          ) : mainTab === 'sim_summary' ? (
            w.SimDebug ? (
              <ErrorBoundary label="SimSummary">
                <w.SimDebug key="sim-summary-view" view="summary" />
              </ErrorBoundary>
            ) : w.DebugTab ? (
              <ErrorBoundary label="Debug">
                <w.DebugTab
                  ip={(() => {
                    const segs = String(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
                    return segs.length >= 2 ? segs[1] : '';
                  })()}
                  onOpenSource={(p: string) => { setPreviewPath(p); }}
                />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                SIM Summary · loading…
              </div>
            )
          ) : mainTab === 'debug' ? (
            w.SimDebug ? (
              <ErrorBoundary label="SimDebug">
                <w.SimDebug key="sim-debug-view" view="debug" initialTab="wave" />
              </ErrorBoundary>
            ) : w.DebugTab ? (
              <ErrorBoundary label="Debug">
                <w.DebugTab
                  ip={(() => {
                    const segs = String(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
                    return segs.length >= 2 ? segs[1] : '';
                  })()}
                  onOpenSource={(p: string) => { setPreviewPath(p); }}
                />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                Debug · loading…
              </div>
            )
            ) : mainTab === 'git' ? (
              ScmTabComponent ? (
                <ErrorBoundary label={scmTabLabel}>
                  <ScmTabComponent
                  initialIp={activeIp}
                  activeIp={activeIp}
                  provider={scmProvider}
                  fallbackTab={w.GitTab}
                />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                {scmTabLabel} · loading…
              </div>
            )
          ) : mainTab === 'git_native' ? (
            w.GitTab ? (
              <ErrorBoundary label="git">
                <w.GitTab
                  initialIp={activeIp}
                  activeIp={activeIp}
                  provider="git"
                />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                git · loading…
              </div>
            )
          ) : mainTab === 'todo' ? (
            <ErrorBoundary label="TodoEditor">
              <TodoEditorPane />
            </ErrorBoundary>
            ) : (
            /* mainTab === 'qa' — SSOT-GEN QA board or active ask_user */
            <div style={{
              flex: 1,
              minHeight: 0,
              overflow: pendingQcard ? 'auto' : 'hidden',
              padding: pendingQcard ? '14px 18px' : 0,
              display: 'flex',
              flexDirection: 'column',
            }}>
              {pendingQcard ? (
                <AskUserPrompt
                  flowId={pendingQcard.flowId}
                  state={qaState[pendingQcard.flowId]}
                  sel={askSel}
                  intent={intent}
                  fullHeight={true}
                  onSel={setAskSel}
                  onToggle={toggleOpt}
                  onCustom={setCustom}
                  onSubmit={submitCard}
                  onChat={() => { setMainTab('chat'); setAskSel(0); inputRef.current?.focus(); }}
                  onSetTab={setActiveTab}
                  onAdvance={advanceBatchedQuestion}
                />
              ) : (
                <SsotQaBoard
                  data={ssotQaBoardData}
                  sessions={ssotQaSessions}
                  activeSession={currentSession}
                  uiLang={uiLang}
                  onSelectSession={activateSsotQaSession}
                  onBack={() => setMainTab('chat')}
                  onRefresh={() => { refreshSsotQa(); refreshSsotQaSessions(); }}
                  onRunCommand={submitMsg}
                  onUsePending={(_: any, text: string, opts: any = {}) => {
                    setInput(text || '');
                    if (opts?.focusChat !== false) {
                      setMainTab('chat');
                      setTimeout(() => inputRef.current?.focus(), 0);
                    }
                  }}
                  onSubmitPending={(bundle: any, text: string) => {
                    const payload = String(text || '').trim();
                    if (!payload) return;
                    const items = Array.isArray(bundle) ? bundle : [];
                    setInput('');
                    // 1) Mirror submitted text into chat feed for traceability.
                    setFeed((f: any[]) => [...f, { kind: 'user', text: payload, createdAt: Date.now() }]);
                    // Use the LIVE resolved session (currentSession), normalized,
                    // falling back to the browser ACTIVE_SESSION. The bag property
                    // ws.normalizeUiSession was never assigned (optional-chained ->
                    // undefined), so the old code collapsed to 'default' and routed
                    // every non-default session's QA answer to the WRONG session.
                    let sessionName = 'default';
                    try {
                      sessionName = normalizeUiSession(currentSession || w.ACTIVE_SESSION || '') || 'default';
                    } catch (_) {}
                    // 2) Persist answered items into qa.json via the backend.
                    try {
                      const ip = ssotQa?.ip || activeIp || '';
                      if (ip && items.length) {
                        const qaItems = items.map(({ item, draft }: any) => {
                          const selected = (draft?.opts || []).filter((o: any) => o.selected).map((o: any) => o.label);
                          const customNote = String(draft?.custom || '').trim();
                          return {
                            flow_id: item?.flow_id || '',
                            decision_key: item?.decision_key || item?.source || item?.id || '',
                            decision_label: item?.decision_label || '',
                            section_id: item?.section_id || item?.section || '',
                            section_title: item?.section_title || '',
                            question: item?.question || '',
                            subtitle: item?.subtitle || '',
                            selected,
                            answer: customNote || selected.join('; '),
                          };
                        }).filter((x: any) => x.decision_key);
                        if (qaItems.length) {
                          fetch('/api/ssot/qa/answer', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              ip,
                              session: sessionName,
                              items: qaItems,
                              submitted_text: payload,
                            }),
                          })
                            .then((r) => r.ok ? r.json() : null)
                            .then((_resp) => {
                              try { refreshSsotQa?.(); } catch (_) {}
                            })
                            .catch(() => {});
                        }
                      }
                    } catch (_) {}
                    // 3) Send the prompt to the backend for LLM processing.
                    // Route through the SAME sendPrompt the chat hub uses so the
                    // QA-board prompt opts into the canonical msg_id + ack/retry
                    // machinery (backend.js only arms a retry for prompts that
                    // carry a msg_id — a bare send is silently lost if a warming
                    // worker drops it). sendPrompt generates the msg_id, builds
                    // the ack Promise, and emits {type:'prompt', msg_id, ...}.
                    // BUG C: capture sendPrompt's return. If the send misses
                    // (backend unavailable / send threw), surface a feed warning
                    // instead of silently dropping the QA answer — mirroring the
                    // chat hub's submitMsg, which re-holds on !sent.ok. We keep this
                    // minimal (a notice, not a full hold/replay) per the QA path's
                    // simpler contract.
                    let sent: any = null;
                    try {
                      sent = sendPrompt(payload, sessionName);
                    } catch (e: any) {
                      sent = { ok: false, error: String((e && e.message) || e) };
                    }
                    if (!sent || sent.ok === false) {
                      setFeed((f: any[]) => [...f, {
                        kind: 'agent',
                        text: `Answer not delivered (${sent?.error || 'backend not ready'}) — please resend.`,
                        createdAt: Date.now(),
                      }]);
                    }
                    setMainTab('chat');
                  }}
                />
              )}
            </div>
          )}
        </div>

        {/* prompt — breathing room below so the input row isn't flush w/ edge. */}
        <div style={{ position: 'relative', paddingBottom: 24, background: 'var(--bg)', zIndex: 2 }}>
          {showAt && atQuery && (
            <div className="slash-menu fade-in" style={{ maxHeight: 280, overflowY: 'auto' }}>
              <div style={{ padding: '6px 12px', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: 'var(--cyan)' }}>
                  {atQuery.parentAbs ? atQuery.parentAbs + '/' : '(project root)'}
                </span>
                <span style={{ flex: 1 }} />
                <span>{fileMatches.length} match{fileMatches.length === 1 ? '' : 'es'}</span>
                <span className="mute">·</span>
                <span><Kbd>↑↓</Kbd> nav · <Kbd>↵</Kbd> select · <Kbd>Esc</Kbd> close</span>
              </div>
              {fileMatches.length === 0 ? (
                <div style={{ padding: '10px 12px', fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                  {atDirEntries.length === 0 ? 'loading…' : `no entries match "${atQuery.filter}"`}
                </div>
              ) : fileMatches.map((f: any, i: number) => (
                <div key={i} className={`slash-item ${i === atSel ? 'sel' : ''}`}
                  onClick={() => acceptAtCompletion(f)}
                  onMouseEnter={() => setAtSel(i)}
                  style={{
                    display: 'grid', gridTemplateColumns: '20px 1fr auto',
                    gap: 8, padding: '5px 12px',
                    background: i === atSel ? 'color-mix(in oklch, var(--accent) 18%, transparent)' : 'transparent',
                    borderLeft: i === atSel ? '2px solid var(--accent)' : '2px solid transparent',
                    cursor: 'pointer',
                  }}>
                  <span style={{ color: f.type === 'dir' ? 'var(--cyan)' : 'var(--accent)' }}>
                    {f.type === 'dir' ? '▸' : '◆'}
                  </span>
                  <span style={{ fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 12 }}>
                    {f.name}{f.type === 'dir' ? '/' : ''}
                  </span>
                  <span className="mute" style={{ fontSize: 10 }}>
                    {f.type === 'dir' ? 'dir' : (f.size != null ? (f.size < 1024 ? f.size + 'B' : (f.size / 1024).toFixed(1) + 'K') : '')}
                  </span>
                </div>
              ))}
            </div>
          )}
          {showSlash && filtered.length > 0 && (
            <div className="slash-menu fade-in">
              <div style={{ padding: '6px 12px', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)' }}>
                {filtered.length} command{filtered.length === 1 ? '' : 's'} · <Kbd>↑↓</Kbd> nav · <Kbd>Tab</Kbd> complete · <Kbd>↵</Kbd> run
              </div>
              {filtered.map((c: any, i: number) => (
                <div key={c.cmd} className={`slash-item ${i === slashSel ? 'sel' : ''}`}
                  onClick={() => { submitMsg(c.cmd); }}
                  onMouseEnter={() => setSlashSel(i)}>
                  <span className="si-cmd">{c.cmd}</span>
                  <span className="si-alias">{c.alias}</span>
                  <span className="si-desc">{c.desc || c.hint || c.usage || ''}</span>
                </div>
              ))}
            </div>
          )}
          {(() => {
            const backendDown = !w.backend || backendState === 'missing' ||
              backendState === 'closed' || backendState === 'error';
            const terminalWorkerStatuses = new Set(['passed', 'done', 'completed', 'failed', 'error', 'cancelled', 'blocked']);
            const activeOrchWorker = workflow === 'orchestrator'
              ? (Array.isArray(orchWorkers) ? orchWorkers.find((wk: any) =>
                Number(wk.running_count || 0) > 0 ||
                Number(wk.pending_count || 0) > 0 ||
                Number(wk.queued_count || 0) > 0
              ) : null)
              : null;
            const workerProgressStatus = String(workerProgress?.status || '').toLowerCase();
            const activeWorkerProgress = workflow !== 'orchestrator' && workerProgress && !terminalWorkerStatuses.has(workerProgressStatus);
            const terminalWorkerProgress = workflow !== 'orchestrator' && workerProgress && terminalWorkerStatuses.has(workerProgressStatus);
            const workerFinishedOk = ['passed', 'done', 'completed'].includes(workerProgressStatus);
            const liveWorkerWorkflow = String(
              (activeOrchWorker && activeOrchWorker.workflow) ||
              (activeWorkerProgress && workerProgress.workflow) ||
              'worker'
            ).trim();
            const liveWorkerActive = !!(activeOrchWorker || activeWorkerProgress);
            const s: any = backendDown
              ? { icon: '!', text: backendState === 'missing' ? 'Backend adapter missing' : 'Backend disconnected', color: 'var(--err)', bg: 'color-mix(in oklch, var(--err) 12%, transparent)' }
              : backendState === 'connecting'
                ? { icon: '·', text: 'Backend connecting', color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 10%, transparent)' }
                : commandBusy
                  ? { icon: '◉', text: commandBusy.text || 'Command running', color: 'var(--accent)', bg: 'color-mix(in oklch, var(--accent) 16%, transparent)', spin: true }
                : pendingQcard
              ? { icon: '⏸', text: 'Waiting on you · answer the ask_user above', color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)' }
              : liveWorkerActive
                ? { icon: '▶', text: `Worker running · ${liveWorkerWorkflow}`, color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)' }
              : streaming
                ? { icon: '◉', text: 'Agent responding', color: 'var(--accent)', bg: 'color-mix(in oklch, var(--accent) 16%, transparent)', spin: true }
              : terminalWorkerProgress
                ? {
                    icon: workerFinishedOk ? '✓' : '!',
                    text: `${workerFinishedOk ? 'Worker done' : 'Worker stopped'} · ${String(workerProgress.workflow || workflow || 'worker')} ${workerProgressStatus}`,
                    color: workerFinishedOk ? 'var(--ok)' : 'var(--err)',
                    bg: `color-mix(in oklch, ${workerFinishedOk ? 'var(--ok)' : 'var(--err)'} 12%, transparent)`,
                  }
                : ssotApproval && ssotApproval.approved
                  ? { icon: '◆', text: `SSOT ready · run ${ssotApproval.generate_cmd || `/to-ssot ${ssotApproval.ip}`}`, color: 'var(--ok)', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)' }
                  : ssotApproval
                    ? { icon: '◆', text: `SSOT plan ready · press To SSOT to generate`, color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)' }
                : { icon: '✓', text: 'End of loop · agent ready', color: 'var(--ok)', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)' };
            return (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '4px 12px', marginBottom: 4,
                fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)',
                color: s.color, background: s.bg,
                border: `1px solid ${s.color}`, borderRadius: 2,
                letterSpacing: '0.04em',
              }}>
                <span style={{ fontWeight: 700 }}>
                  {s.icon}{s.spin ? <span className="ascii-spin" style={{ marginLeft: 2 }} /> : null}
                </span>
                <span>{s.text}</span>
              </div>
            );
          })()}
          {/* Bottom prompt area — four rendering modes (see legacy comment). */}
          {pendingQcard && centerLayout === 'classic' && mainTab !== 'qa' ? (
            <AskUserPrompt
              flowId={pendingQcard.flowId}
              state={qaState[pendingQcard.flowId]}
              sel={askSel}
              intent={intent}
              onSel={setAskSel}
              onToggle={toggleOpt}
              onCustom={setCustom}
              onSubmit={submitCard}
              onChat={() => { setAskSel(0); inputRef.current?.focus(); }}
              onSetTab={setActiveTab}
              onAdvance={advanceBatchedQuestion}
            />
          ) : pendingQcard && centerLayout === 'classic' && mainTab === 'qa' ? (
            renderPromptRow()
          ) : pendingQcard && centerLayout === 'tabbed' && mainTab !== 'qa' ? (
            <>
              <div
                onClick={() => setMainTab('qa')}
                className="ask-feed-placeholder"
                style={{
                  padding: '8px 12px',
                  marginBottom: 6,
                  border: '1px dashed var(--warn)',
                  borderRadius: 2,
                  background: 'color-mix(in oklch, var(--warn) 10%, transparent)',
                  color: 'var(--warn)',
                  fontSize: 12,
                  cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
                title="Click to open the Q&A tab"
              >
                <span>⏸</span>
                <span>Agent is waiting on you · type an answer below, or open the <b>Q&amp;A</b> tab for the full card</span>
                <span style={{ flex: 1 }} />
                <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>→ Q&amp;A</span>
              </div>
              {renderPromptRow()}
            </>
          ) : pendingQcard && centerLayout === 'tabbed' && mainTab === 'qa' ? (
            renderPromptRow() /* AskUserPrompt is rendered inside the tab body above */
          ) : (
            renderPromptRow()
          )}
        </div>
      </div>

      {/* CENTER ↔ RIGHT splitter — keep visible at 0px so collapsed panels can reopen. */}
      <Splitter width={rightW} side="right" onResize={setRightW} onToggle={toggleRight} />

      {/* RIGHT — ATLAS status + SSOT/Todo/Diff (hidden when sim_debug or collapsed) */}
      {effRightW > 0 ? (
        <div className={'ws-right-panel' + (isMobile ? (rightDrawerOpen ? ' drawer-open' : '') : '')} style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        <AgentStatusPanel intent={intent} workflow={workflow} activeIp={activeIp}
                          agentAlive={!!workspaceTelemetry.agentAlive}
                          agentRunning={!!workspaceTelemetry.agentRunning}
                          onCollapse={toggleRight} />
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="box-h" style={{ padding: 0 }}>
            <RightTab id="todo" cur={rightTab} onTab={setRightTab}>Todo</RightTab>
            <RightTab id="progress" cur={rightTab} onTab={setRightTab}>Progress</RightTab>
            <RightTab id="chat" cur={rightTab} onTab={setRightTab}>Chat</RightTab>
            <RightTab id="git"  cur={rightTab} onTab={setRightTab}>Git</RightTab>
          </div>
          {rightTab === 'progress' && <ProgressPanel />}
          {rightTab === 'todo' && <TodoPanel />}
          {rightTab === 'chat' && <OrchestratorChatPanel activeIp={activeIp} />}
          {rightTab === 'git'  && <GitPanel activeIp={activeIp} />}
        </div>
      </div>
      ) : (
        <div /> /* collapsed — empty grid cell to keep the 5-track grid aligned */
      )}

      {openFile && <FileViewer name={openFile} onClose={() => setOpenFile(null)} />}
    </div>
  );
};

// ── RightTab : right-rail tab label ────────────────────────────────
export const RightTab = ({
  id,
  cur,
  onTab,
  children,
}: {
  id: string;
  cur: string;
  onTab: (id: string) => void;
  children?: ReactNode;
}) => (
  <span onClick={() => onTab(id)} style={{
    cursor: 'pointer', padding: '10px 14px', fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em', textTransform: 'uppercase',
    color: cur === id ? 'var(--fg)' : 'var(--fg-mute)',
    borderBottom: cur === id ? `2px solid var(--accent)` : '2px solid transparent',
    background: cur === id ? 'var(--bg-2)' : 'transparent',
    flex: 1, textAlign: 'center',
  }}>{children}</span>
);

// Register the root component on window — app-shell.tsx reads `window.Workspace`
// to mount it. This is the only file that owns this bridge.
(window as any).Workspace = Workspace;
