/* workspace-rootui-rail-tabs.tsx — left-rail + center tab-strip render helpers
 * extracted from workspace-root.tsx so the composer stays under 1000 lines.
 *
 * These two functions are pure render helpers (the same pattern as the
 * hook-bound renderChatPane/renderPromptRow): they take the merged `ws` bag
 * — { ...session, ...data } — that workspace-root assembles, plus read the
 * runtime ATLAS bridges off `window`. They emit JSX 1:1 with the legacy
 * inline blocks; no behavior change. INERT mirror — the live app is still
 * served by workspace.jsx.
 *
 * renderWorkspaceLeftRail   : file-context-menu + mobile drawer chrome +
 *                             the LEFT panel (mode/workflow list + IP file
 *                             tree + conversation-mode selector), or the
 *                             collapsed empty grid cell.
 * renderWorkspaceCenterTabStrip : the center `box-h` tab strip (sim/debug/
 *                             coverage/report/import-export/chat/qa/ssot/doc/
 *                             split/preview/git/todo chips + context label).
 */
import { type ReactNode } from 'react';

import { Splitter, HorizontalSplitter } from './workspace-resize-splitters';
import { appendActiveSessionParam, isSsotYamlPath } from './workspace-session-routing';
import { ConvModeSelector } from './workspace-git-diff';

// `Kbd` is published on window by shared.tsx for not-yet-migrated consumers;
// read it through window with a permissive cast + inline fallback so the
// mirror stays decoupled from the global type decls.
const Kbd: any = (window as any).Kbd
  || (({ children }: { children?: ReactNode }) => <span className="kbd">{children}</span>);

// LEFT rail: context menu + mobile chrome + mode/workflow + IP file tree.
export const renderWorkspaceLeftRail = (ws: any): ReactNode => {
  const w: any = window;
  const {
    fileContextMenu, setFileContextMenu, deleteIpTreeFile,
    isMobile, mobileHintDismissed, setMobileHintDismissed,
    leftDrawerOpen, setLeftDrawerOpen,
    rightDrawerOpen, setRightDrawerOpen,
    effLeftW,
    leftWorkflowH, setLeftWorkflowH, resetLeftWorkflowH,
    toggleLeft,
    intent, switchIntent, switchWorkflow, workflow,
    filePanelIp, filePanelStatus,
    fileSort, setFileSort,
    fileExpand, setFileExpand,
    collapsedFileDirs, setCollapsedFileDirs,
    visibleFileTree,
    previewPath, setPreviewPath,
    setMainTab,
  } = ws;
  return (
    <>
      {fileContextMenu && (
        <div
          className="file-context-menu"
          style={{ left: fileContextMenu.x, top: fileContextMenu.y }}
          onClick={(event) => event.stopPropagation()}
          onContextMenu={(event) => event.preventDefault()}
        >
          <button
            type="button"
            className="file-context-menu-item"
            title={`Download ${fileContextMenu.path}`}
            onClick={() => {
              const item = fileContextMenu;
              setFileContextMenu(null);
              // Fetch the raw bytes and force a save-as (the /api/file/raw
              // endpoint serves inline, so a blob + download attribute is what
              // turns it into a per-file download).
              (async () => {
                try {
                  const params = appendActiveSessionParam(new URLSearchParams({ path: item.path }));
                  const res = await fetch(
                    `/api/file/raw?${params.toString()}`,
                    { cache: 'no-store', credentials: 'include' },
                  );
                  if (!res.ok) throw new Error(`HTTP ${res.status}`);
                  const blob = await res.blob();
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = String(item.name || (item.path || '').split('/').pop() || 'file');
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  setTimeout(() => URL.revokeObjectURL(url), 1000);
                } catch (error: any) {
                  window.alert(`Download failed: ${String((error && error.message) || error)}`);
                }
              })();
            }}
          >
            Download
          </button>
          <button
            type="button"
            className="file-context-menu-danger"
            title={fileContextMenu.path}
            onClick={() => {
              const item = fileContextMenu;
              setFileContextMenu(null);
              deleteIpTreeFile(item.path, item.ip);
            }}
          >
            Delete
          </button>
        </div>
      )}
      {/* Mobile: hint banner, drawer toggles, and backdrop */}
      {isMobile && !mobileHintDismissed && (
        <div className="atlas-mobile-hint" style={{ gridColumn: '1 / -1' }}>
          <span>ATLAS is optimized for desktop. Some panes may not be available.</span>
          <button
            aria-label="Dismiss mobile hint"
            onClick={() => {
              setMobileHintDismissed(true);
              try { localStorage.setItem('atlasMobileHintDismissed', '1'); } catch (_) {}
            }}
          >×</button>
        </div>
      )}
      {isMobile && (
        <>
          <button
            className="ws-drawer-toggle left"
            aria-label="Open left panel"
            onClick={() => { setLeftDrawerOpen((o: boolean) => !o); setRightDrawerOpen(false); }}
          >☰</button>
          <button
            className="ws-drawer-toggle right"
            aria-label="Open right panel"
            onClick={() => { setRightDrawerOpen((o: boolean) => !o); setLeftDrawerOpen(false); }}
          >⚙</button>
          <div
            className={'ws-drawer-backdrop' + (leftDrawerOpen || rightDrawerOpen ? ' visible' : '')}
            onClick={() => { setLeftDrawerOpen(false); setRightDrawerOpen(false); }}
          />
        </>
      )}
      {/* LEFT — Mode/Workflow + Files (collapsed when leftW===0 OR sim_debug) */}
      {effLeftW > 0 ? (
        <div className={'ws-left-panel' + (isMobile ? (leftDrawerOpen ? ' drawer-open' : '') : '')} style={{ display: 'flex', flexDirection: 'column', gap: 8, overflow: 'hidden', minWidth: 0 }}>
        <div className="box left-workflow-box" style={{ flex: `0 0 ${leftWorkflowH}px` }}>
          <div className="box-h">
            <span>▸ mode</span>
            <span style={{ flex: 1 }} />
            <span
              onClick={toggleLeft}
              title="collapse left panel (double-click splitter to restore)"
              className="mute"
              style={{ cursor: 'pointer', fontSize: 12, padding: '0 6px',
                       userSelect: 'none' }}
            >‹</span>
            <span className="mute" style={{ fontSize: 10, textTransform: 'none', letterSpacing: 0 }}>shift+tab</span>
          </div>
          {/* Intent toggle: Normal | Plan */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--line)' }}>
            <div
              onClick={() => switchIntent('normal')}
              style={{
                padding: '8px 10px', textAlign: 'center', cursor: 'pointer', fontSize: 'var(--ui-control-font-size)',
                letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600,
                color: intent === 'normal' ? 'var(--bg)' : 'var(--fg-mute)',
                background: intent === 'normal' ? 'var(--cyan)' : 'transparent',
                borderRight: '1px solid var(--line)',
              }}
            >● Normal</div>
            <div
              onClick={() => switchIntent('plan')}
              style={{
                padding: '8px 10px', textAlign: 'center', cursor: 'pointer', fontSize: 'var(--ui-control-font-size)',
                letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600,
                color: intent === 'plan' ? 'var(--bg)' : 'var(--fg-mute)',
                background: intent === 'plan' ? 'var(--warn)' : 'transparent',
              }}
            >◐ Plan</div>
          </div>
          <div style={{ padding: '6px 12px 4px', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--fg-mute)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>workflow</span>
            <span className="mute" style={{ fontSize: 9, textTransform: 'none', letterSpacing: 0 }}>
              {ws.atlasUiOrchestratorMode?.() ? '· orchestrator first' : '· optional · click to toggle'}
            </span>
          </div>
          <div className="left-workflow-list">
            {(w.FLOW_STAGES || []).map((s: any, i: number) => {
              const active = (workflow || 'default') === s.id;
              return (
                <button key={s.id}
                  type="button"
                  onClick={() => switchWorkflow(s.id)}
                  style={{
                    display: 'grid', gridTemplateColumns: '14px 38px 1fr 14px',
                    gap: 8, padding: '6px 12px', alignItems: 'center', fontSize: 12, cursor: 'pointer',
                    background: active ? 'var(--select)' : 'transparent',
                    borderLeft: active ? `2px solid ${s.color}` : '2px solid transparent',
                    borderTop: 0, borderRight: 0, borderBottom: 0,
                    width: '100%', color: 'var(--fg)', textAlign: 'left', fontFamily: 'inherit',
                  }}
                  onMouseEnter={(e) => { if (!active) (e.currentTarget as HTMLElement).style.background = 'var(--bg-2)'; }}
                  onMouseLeave={(e) => { if (!active) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                >
                  <span className="mute">{i + 1}</span>
                  <span style={{ color: s.color, fontWeight: 700, letterSpacing: '0.06em', fontSize: 10 }}>{s.glyph}</span>
                  <span style={{ fontWeight: active ? 500 : 400 }}>{s.label}</span>
                  <span className="mute" style={{ fontSize: 10 }}>{active ? '◉' : '○'}</span>
                </button>
              );
            })}
          </div>
        </div>

        <HorizontalSplitter
          height={leftWorkflowH}
          onResize={setLeftWorkflowH}
          onReset={resetLeftWorkflowH}
          title="drag to resize Workflow/IP split · double-click to reset"
        />

        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div className="box-h">
            <span>▸ ip</span>
            <span style={{ flex: 1 }} />
            <span className="acc" style={{ textTransform: 'none', fontSize: 'var(--ui-control-font-size)', letterSpacing: 0 }}>
              {filePanelIp || 'select IP'}
            </span>
          </div>
          <div style={{
            padding: '6px 10px', borderBottom: '1px solid var(--line)',
            display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
            background: 'var(--bg-2)',
          }}>
            <span className="mute" style={{ fontSize: 12 }}>dir</span>
            <span className="mute">›</span>
            <span className="acc" style={{ flex: 1, fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 500 }}>
              {filePanelIp || 'select IP'}
            </span>
            {/* Sort toggle: name (A-Z, dirs first) ↔ recent (mtime DESC). */}
            <span
              title={'sort: ' + (fileSort === 'recent'
                ? 'recent (most recently modified first) — click for A→Z'
                : 'A→Z (dirs first) — click for recent')}
              onClick={() => {
                if (!filePanelIp) return;
                setFileSort((s: string) => s === 'recent' ? 'name' : 'recent');
                w.atlasData.refreshFileTree(filePanelIp, { recursive: true });
              }}
              style={{
                cursor: 'pointer',
                fontSize: 'var(--ui-control-font-size)',
                padding: '1px 6px',
                borderRadius: 2,
                userSelect: 'none',
                color: fileSort === 'recent' ? 'var(--accent)' : 'var(--fg-mute)',
                border: '1px solid ' + (fileSort === 'recent' ? 'var(--accent)' : 'var(--line)'),
                fontFamily: 'var(--mono)',
              }}
            >{fileSort === 'recent' ? '⏱ recent' : 'A→Z'}</span>
            {/* Expand-all / collapse-all toggle. */}
            <span
              title={fileExpand === 'deep'
                ? 'expanded — click to collapse all folders'
                : 'top level only — click to expand all folders'}
              onClick={() => {
                if (!filePanelIp) return;
                setFileExpand((v: string) => v === 'deep' ? 'shallow' : 'deep');
                setCollapsedFileDirs(new Set());
              }}
              style={{
                cursor: 'pointer',
                fontSize: 10,
                padding: '1px 6px',
                borderRadius: 2,
                userSelect: 'none',
                color: fileExpand === 'deep' ? 'var(--accent)' : 'var(--fg-mute)',
                border: '1px solid ' + (fileExpand === 'deep' ? 'var(--accent)' : 'var(--line)'),
                fontFamily: 'var(--mono)',
              }}
            >{fileExpand === 'deep' ? '▾ all' : '▸ all'}</span>
            <span
              title="refresh — pull the latest file list now"
              style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 13,
                       padding: '0 6px', fontWeight: 600, userSelect: 'none' }}
              onClick={() => filePanelIp && w.atlasData.refreshFileTree(filePanelIp, { recursive: true })}
            >↻</span>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
            {visibleFileTree.length === 0 && (
              <div
                className={filePanelIp && w.FILE_TREE_ERROR ? '' : 'mute'}
                style={{
                  padding: '8px 10px',
                  fontSize: 11,
                  color: filePanelIp && w.FILE_TREE_ERROR ? 'var(--err)' : undefined,
                  fontFamily: filePanelIp && w.FILE_TREE_ERROR ? 'var(--mono)' : undefined,
                }}
              >
                {filePanelStatus}
              </div>
            )}
            {(fileSort === 'recent'
              ? [...visibleFileTree].sort((a: any, b: any) => (b.mtime || 0) - (a.mtime || 0))
              : visibleFileTree
            ).filter((n: any) => {
              const relName = String(n.name || '').replace(/^\/+|\/+$/g, '');
              if (!relName) return false;
              if (fileExpand !== 'deep' && (n.depth || 0) > 0) return false;
              const root = filePanelIp;
              const parts = relName.split('/').filter(Boolean);
              for (let idx = 1; idx < parts.length; idx += 1) {
                const ancestor = [root, ...parts.slice(0, idx)].filter(Boolean).join('/');
                if (collapsedFileDirs.has(ancestor)) return false;
              }
              return true;
            }).map((n: any, i: number) => {
              const baseScope = filePanelIp;
              const relName = String(n.name || '').replace(/^\/+|\/+$/g, '');
              const fullPath = (baseScope ? `${baseScope}/` : '') + relName;
              const displayName = relName.split('/').filter(Boolean).pop() || relName;
              const dirCollapsed = n.type === 'dir' && (fileExpand !== 'deep' || collapsedFileDirs.has(fullPath));
              const isSelected = n.type === 'file' && previewPath === fullPath;
              return (
                <div key={i}
                  className={(isSelected ? 'frow active' : (n.active ? 'frow active' : 'frow'))}
                  style={{ paddingLeft: 8 + (n.depth || 0) * 14, cursor: 'pointer' }}
                  onClick={() => {
                    if (n.type === 'file') {
                      ws.readAtlasAsyncResource?.('file', fullPath)?.catch?.(() => {});
                      setPreviewPath(fullPath);
                      ws.persistAtlasPreviewPath?.(fullPath);
                      setMainTab('split');
                    } else {
                      const wasDeep = fileExpand === 'deep';
                      if (!wasDeep) setFileExpand('deep');
                      setCollapsedFileDirs((prev: Set<string>) => {
                        const next = new Set(prev);
                        if (!wasDeep || next.has(fullPath)) next.delete(fullPath);
                        else next.add(fullPath);
                        return next;
                      });
                    }
                  }}
                  onMouseEnter={() => {
                    if (n.type === 'file') ws.readAtlasAsyncResource?.('file', fullPath)?.catch?.(() => {});
                  }}
                  onContextMenu={(event) => {
                    if (n.type !== 'file') return;
                    event.preventDefault();
                    event.stopPropagation();
                    const menuWidth = 148;
                    const menuHeight = 40;
                    const x = Math.max(8, Math.min(event.clientX, window.innerWidth - menuWidth - 8));
                    const y = Math.max(8, Math.min(event.clientY, window.innerHeight - menuHeight - 8));
                    setFileContextMenu({ x, y, path: fullPath, name: displayName, ip: filePanelIp });
                  }}
                  title={fullPath + (n.type === 'file' ? ' (click to preview)' : ' (click to fold/unfold)')}
                >
                  <span className="fr-icon">{n.type === 'dir' ? (dirCollapsed ? '▸' : '▾') : '◆'}</span>
                  <span className="trunc">{n.type === 'dir' ? <span className="dim">{displayName}/</span> : displayName}</span>
                  <span className="mute" style={{ fontSize: 10 }}>{n.size}</span>
                </div>
              );
            })}
          </div>
          {/* file tree footer */}
          <div style={{ borderTop: '1px solid var(--line)', padding: '6px 10px', fontSize: 10, color: 'var(--fg-mute)', display: 'flex', gap: 10 }}>
            <span>{visibleFileTree.length} entries</span>
            <span className="mute">·</span>
            <span className="mute" title="Auto-refreshes on tool_result + every 5s">
              {w.FILE_TREE_LOADING
                ? 'loading…'
                : w.FILE_TREE_ERROR
                  ? 'error'
                  : w.FILE_TREE_LAST_REFRESH
                    ? new Date(w.FILE_TREE_LAST_REFRESH).toLocaleTimeString()
                    : 'not loaded'}
            </span>
            <span style={{ flex: 1 }} />
            <span className="mute"
              title={w.CONTEXT?.projectRoot || ''}>
              {filePanelIp || 'select IP'}
            </span>
          </div>
        </div>
        {/* Conversation hydration mode selector */}
        <ConvModeSelector />
      </div>
      ) : (
        <div /> /* collapsed — empty grid cell so the 5-track grid stays aligned */
      )}
    </>
  );
};

// CENTER tab strip: the `box-h` chip row + the active-tab context label.
export const renderWorkspaceCenterTabStrip = (ws: any): ReactNode => {
  const w: any = window;
  const {
    setMainTab, mainTab,
    showSimSummaryTab, showDebugTab, showCoverageTab, showWorkflowReportTab,
    showSsotImportExportTab, showQaTab, showSsotChecklistTab, showSsotTab, showSsotDocTab,
    showReqTab,
    showBuiltinGitTab,
    workflowReportMeta, workflow, pendingQcard,
    previewPath, activeIp, scmTabLabel,
    debugChatOpen, setDebugChatOpen,
  } = ws;
  return (
    <div className="box-h">
      {/* Tab strip — chat · ssot · Q&A · split view · full view. */}
      {showSimSummaryTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('sim_summary')}
          title="SIM summary: scenarios, pass/fail, scoreboard"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2,
            color: mainTab === 'sim_summary' ? 'var(--accent)' : 'var(--fg-mute)',
            background: mainTab === 'sim_summary' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'sim_summary' ? 'var(--accent)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >sim summary</span>
      )}
      {showDebugTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('debug')}
          title="Debug view: hierarchy, source, waveform"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2,
            color: mainTab === 'debug' ? 'var(--accent)' : 'var(--fg-mute)',
            background: mainTab === 'debug' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'debug' ? 'var(--accent)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >debug</span>
      )}
      {showCoverageTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('coverage')}
          title="Coverage view: SSOT goals, metrics, files, and gaps"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2,
            color: mainTab === 'coverage' ? 'var(--accent)' : 'var(--fg-mute)',
            background: mainTab === 'coverage' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'coverage' ? 'var(--accent)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >coverage</span>
      )}
      {showWorkflowReportTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('workflow_report')}
          title={workflowReportMeta.title}
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2,
            color: mainTab === 'workflow_report' ? 'var(--accent)' : 'var(--fg-mute)',
            background: mainTab === 'workflow_report' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'workflow_report' ? 'var(--accent)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >{workflowReportMeta.label}</span>
      )}
      {showSsotImportExportTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('import_export')}
          title="Import docs and export SSOT artifacts"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2,
            color: mainTab === 'import_export' ? 'var(--accent)' : 'var(--fg-mute)',
            background: mainTab === 'import_export' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'import_export' ? 'var(--accent)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >Import / Export</span>
      )}
      <span
        className="tab-chip tab-chip-primary"
        onClick={() => setMainTab('chat')}
        style={{
          order: -100,
          cursor: 'pointer', padding: '2px 8px', borderRadius: 2,
          marginLeft: 0,
          color: mainTab === 'chat' ? 'var(--accent)' : 'var(--fg-mute)',
          background: mainTab === 'chat' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
          border: '1px solid ' + (mainTab === 'chat' ? 'var(--accent)' : 'transparent'),
          fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
        }}
      >chat</span>
      {showQaTab && (workflow === 'ssot-gen' || pendingQcard) && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('qa')}
          title={pendingQcard ? 'Answer the agent\'s questions' : 'SSOT Q&A session'}
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2, marginLeft: 4,
            position: 'relative',
            color: mainTab === 'qa' ? 'var(--warn)' : (pendingQcard ? 'var(--warn)' : 'var(--fg-mute)'),
            background: mainTab === 'qa' ? 'color-mix(in oklch, var(--warn) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'qa' ? 'var(--warn)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >
          Q&amp;A Session
          {pendingQcard && mainTab !== 'qa' && (
            <span style={{
              position: 'absolute', top: 1, right: 1,
              width: 6, height: 6, borderRadius: '50%',
              background: 'var(--warn)',
              animation: 'pulse 1.5s infinite',
            }} />
          )}
        </span>
      )}
      {showSsotChecklistTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('checklist')}
          title="SSOT validation: missing items, SSOT percent, and validator script"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2, marginLeft: 4,
            color: mainTab === 'checklist' ? 'var(--cyan)' : 'var(--fg-mute)',
            background: mainTab === 'checklist' ? 'color-mix(in oklch, var(--cyan) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'checklist' ? 'var(--cyan)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >Validation</span>
      )}
      {showReqTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('req')}
          title="REQ: requirements + obligations + contract + evidence in one reviewable view"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2, marginLeft: 4,
            color: mainTab === 'req' ? 'var(--accent)' : 'var(--fg-mute)',
            background: mainTab === 'req' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'req' ? 'var(--accent)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >req</span>
      )}
      {showSsotTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('ssot')}
          title="Review SSOT by section"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2, marginLeft: 4,
            color: mainTab === 'ssot' ? 'var(--magenta)' : 'var(--fg-mute)',
            background: mainTab === 'ssot' ? 'color-mix(in oklch, var(--magenta) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'ssot' ? 'var(--magenta)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >ssot</span>
      )}
      {showSsotDocTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('doc')}
          title="Render exported SSOT HTML"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2, marginLeft: 4,
            color: mainTab === 'doc' ? 'var(--magenta)' : 'var(--fg-mute)',
            background: mainTab === 'doc' ? 'color-mix(in oklch, var(--magenta) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'doc' ? 'var(--magenta)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >doc</span>
      )}
      {/* No standing Q&A tab outside ssot-gen (see legacy comment). */}
      <span
        className="tab-chip"
        onClick={() => setMainTab('split')}
        title="Show chat and preview side by side"
        style={{
          cursor: 'pointer',
          padding: '2px 8px', borderRadius: 2, marginLeft: 4,
          color: mainTab === 'split' ? 'var(--accent)' : 'var(--fg-mute)',
          background: mainTab === 'split' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
          border: '1px solid ' + (mainTab === 'split' ? 'var(--accent)' : 'transparent'),
          fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
        }}
      >split view</span>
      <span
        className="tab-chip"
        onClick={() => setMainTab('preview')}
        title={previewPath ? 'Full view: ' + previewPath : 'Open the preview pane in full view'}
        style={{
          cursor: 'pointer',
          padding: '2px 8px', borderRadius: 2, marginLeft: 4,
          color: mainTab === 'preview' ? 'var(--accent)' : 'var(--fg-mute)',
          background: mainTab === 'preview' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
          border: '1px solid ' + (mainTab === 'preview' ? 'var(--accent)' : 'transparent'),
          fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
        }}
      >full view</span>
      <span
        className="tab-chip"
        onClick={() => setMainTab('git')}
        title="SCM: per-IP source-control status, history, diff, and submit actions"
        style={{
          cursor: 'pointer',
          padding: '2px 8px', borderRadius: 2, marginLeft: 4,
          color: mainTab === 'git' ? 'var(--accent)' : 'var(--fg-mute)',
          background: mainTab === 'git' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
          border: '1px solid ' + (mainTab === 'git' ? 'var(--accent)' : 'transparent'),
          fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
        }}
      >{scmTabLabel}</span>
      {showBuiltinGitTab && (
        <span
          className="tab-chip"
          onClick={() => setMainTab('git_native')}
          title="Git: built-in per-IP Git status, history, diff, and revert actions"
          style={{
            cursor: 'pointer',
            padding: '2px 8px', borderRadius: 2, marginLeft: 4,
            color: mainTab === 'git_native' ? 'var(--accent)' : 'var(--fg-mute)',
            background: mainTab === 'git_native' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (mainTab === 'git_native' ? 'var(--accent)' : 'transparent'),
            fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
          }}
        >git</span>
      )}
      {(() => {
        const _allTodos = Array.isArray(w.TODOS) ? w.TODOS : [];
        const _approvedTodos = _allTodos.filter((t: any) => t.state === 'approved').length;
        return (
          <span
            className="tab-chip"
            onClick={() => setMainTab('todo')}
            title="TODO: approved / total for this session"
            style={{
              cursor: 'pointer',
              padding: '2px 8px', borderRadius: 2, marginLeft: 4,
              color: mainTab === 'todo' ? 'var(--accent)' : 'var(--fg-mute)',
              background: mainTab === 'todo' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
              border: '1px solid ' + (mainTab === 'todo' ? 'var(--accent)' : 'transparent'),
              fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 'var(--ui-control-font-size)',
            }}
          >
            todo
            {_allTodos.length > 0 && (
              <span style={{
                marginLeft: 5,
                padding: '0 5px',
                borderRadius: 8,
                background: 'color-mix(in oklch, var(--accent) 20%, transparent)',
                color: 'var(--accent)',
                fontSize: 'calc(var(--ui-control-font-size) - 1px)',
              }}>{_approvedTodos}/{_allTodos.length}</span>
            )}
          </span>
        );
      })()}
      <span className="mute" style={{ margin: '0 6px' }}>·</span>
      {mainTab === 'chat' ? (
        null
      ) : mainTab === 'split' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}
              title={previewPath || ''}>
          chat + {isSsotYamlPath(previewPath) ? 'ssot' : 'preview'} · {previewPath || '(no file selected)'}
        </span>
      ) : mainTab === 'req' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          REQ bundle · requirements · obligations · contract · evidence
        </span>
      ) : mainTab === 'ssot' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          SSOT section review
        </span>
      ) : mainTab === 'doc' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          SSOT HTML export preview
        </span>
      ) : mainTab === 'checklist' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          SSOT validation · missing items · SSOT percent · script gate
        </span>
      ) : mainTab === 'import_export' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          Upload/import docs · export SSOT
        </span>
      ) : mainTab === 'sim_summary' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          sim_debug summary · scenarios · scoreboard
        </span>
      ) : mainTab === 'debug' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          sim_debug hierarchy · source · wave
        </span>
      ) : mainTab === 'coverage' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          coverage workflow · SSOT goals · gaps
        </span>
      ) : mainTab === 'workflow_report' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          {workflowReportMeta ? workflowReportMeta.title : 'workflow report'} · {activeIp || 'no IP'}
        </span>
      ) : mainTab === 'git_native' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          built-in Git · {activeIp || 'no IP'}
        </span>
      ) : mainTab === 'todo' ? (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}>
          TODO list · detail · edit
        </span>
      ) : (
        <span className="mute trunc" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', maxWidth: 380 }}
              title={previewPath || ''}>
          {previewPath || '(no file selected)'}
        </span>
      )}
      <span style={{ flex: 1 }} />
      {mainTab === 'debug' && setDebugChatOpen && (
        <span
          className="tab-chip"
          onClick={() => setDebugChatOpen(!debugChatOpen)}
          title="toggle the agent chat beside the waveform (it can drive the view via the sim_debug tool)"
          style={{
            cursor: 'pointer', padding: '2px 8px', borderRadius: 2, marginRight: 6,
            color: debugChatOpen ? 'var(--accent)' : 'var(--fg-mute)',
            background: debugChatOpen ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            border: '1px solid ' + (debugChatOpen ? 'var(--accent)' : 'var(--line)'),
            fontWeight: 700, letterSpacing: '0.06em', fontSize: 'var(--ui-control-font-size)',
          }}
        >💬 chat{debugChatOpen ? ' ✕' : ''}</span>
      )}
      {(mainTab === 'preview' || mainTab === 'split' || mainTab === 'ssot' || mainTab === 'doc' || mainTab === 'req' || mainTab === 'checklist' || mainTab === 'import_export') && (
        <span style={{ fontSize: 10 }}>
          <span className="mute" style={{ marginRight: 8 }}>{mainTab === 'split' ? 'chat only' : 'back to chat'}</span>
          <span onClick={() => setMainTab('chat')} className="acc"
                style={{ cursor: 'pointer', padding: '2px 6px',
                         border: '1px solid var(--accent)', borderRadius: 2 }}>↵</span>
        </span>
      )}
    </div>
  );
};
