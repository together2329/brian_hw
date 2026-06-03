// app-shell.tsx — extracted from app.tsx (strangler-fig TS split).
//
// The entire presentational render tree of the App root: top notice banner,
// workflow-switch toast, boot handshake overlay, Create-IP modal, the desktop
// dir-switcher toolbar, the mobile header, and the main screen router. This is
// a pure view layer — every value/handler it needs is passed in as a prop, and
// it performs only window READS (window.ATLAS_USER, window.location), never any
// window assignment, so no bridge crosses this seam.
//
// Splitting the view out keeps app.tsx focused on the (irreducibly large)
// stateful App hook body. AppShell runs in App's render and receives App's
// live state/closures, so behavior is identical.
//
// Typed in the same permissive house style as app-helpers.tsx — window-sourced
// values are `any` on purpose; props are typed loosely (any) to mirror the
// dynamically-shaped App closures they carry.
import { ErrorBoundary, PipelineRunningChip, OrchInlineStatus } from './app-helpers';
import {
  ATLAS_UI_RESOLUTION_PRESETS,
  ATLAS_RUN_MODE_OPTIONS,
  ATLAS_EXEC_MODE_OPTIONS,
  ATLAS_EXEC_MODE_LOCKED,
  ATLAS_FONT_MODE_OPTIONS,
} from './app-helpers';
import { MobileHeader } from './app-mobile';

// Workspace and the screen components are owned by other (unmigrated) .jsx
// files; resolve them through window at render time.
const Workspace = (props: any) => {
  const W = window.Workspace as any;
  return W ? <W {...props} /> : null;
};

export interface AppShellProps {
  dir: string;
  theme: string;
  setTheme: (t: string) => void;
  topNotice: string;
  setTopNotice: (s: string) => void;
  wfSwitching: any;
  bootHidden: boolean;
  setBootHidden: (v: boolean) => void;
  bootSteps: Record<string, string>;
  bootFailed: boolean;
  bootDisplayDone: boolean;
  nameEntry: { kind: string; value: string } | null;
  setNameEntry: (v: { kind: string; value: string } | null) => void;
  nameEntryBusy: boolean;
  nameEntryInputRef: any;
  commitNameEntry: () => void;
  newIpInitialWorkflow: () => string;
  normalizeSession: (value: unknown) => string;
  activeNamespace: string;
  ownerEditable: boolean;
  activeSessionId: string;
  activeWorkspaceSession: string;
  sessionIdOptions: string[];
  selectSessionId: (id: string) => void;
  newSessionId: () => void;
  activeIp: string;
  WORKFLOW_DEFAULT: string;
  selectIp: (ip: string) => void;
  ipOptions: string[];
  authState: string;
  beginNameEntry: (kind: string) => void;
  execMode: string;
  currentWorkflow: () => string;
  fontMode: string;
  setFontMode: (v: string) => void;
  fontScale: string;
  setFontScale: (v: string) => void;
  resolution: string;
  setResolution: (v: string) => void;
  uiLang: string;
  chooseUiLang: (v: string) => void;
  stopAgent: () => void;
  exitAll: () => void;
  screen: string;
  setScreen: (v: string) => void;
  runMode: string;
  saveRunPolicy: (runMode: string, execMode: string) => void;
  WORKFLOW_OPTIONS: string[];
  selectWorkflow: (wf: string) => void;
  activateDashboardSession: (row: any) => void;
}

export const AppShell = ({
  dir, theme, setTheme, topNotice, setTopNotice, wfSwitching,
  bootHidden, setBootHidden, bootSteps, bootFailed, bootDisplayDone,
  nameEntry, setNameEntry, nameEntryBusy, nameEntryInputRef, commitNameEntry,
  newIpInitialWorkflow, normalizeSession, activeNamespace, ownerEditable,
  activeSessionId, activeWorkspaceSession, sessionIdOptions, selectSessionId, newSessionId,
  activeIp, WORKFLOW_DEFAULT, selectIp, ipOptions, authState, beginNameEntry,
  execMode, currentWorkflow, fontMode, setFontMode, fontScale, setFontScale,
  resolution, setResolution, uiLang, chooseUiLang, stopAgent, exitAll,
  screen, setScreen, runMode, saveRunPolicy, WORKFLOW_OPTIONS, selectWorkflow,
  activateDashboardSession,
}: AppShellProps) => {
  const isFontMode = (value: string) => ATLAS_FONT_MODE_OPTIONS.some(opt => opt.key === value);
  const selectedFontMode = isFontMode(fontMode) ? fontMode : 'mono';
  const chooseFontMode = (value: string) => {
    const next = isFontMode(value) ? value : 'mono';
    setFontMode(next);
    try { localStorage.setItem('atlasFontModeUserSet', '1'); } catch (_) {}
  };
  const nameEntryIsSession = nameEntry?.kind === 'session';
  const nameEntryIsIp = nameEntry?.kind === 'ip';
  const showNameEntryModal = !!nameEntry && (nameEntryIsIp || nameEntryIsSession);
  const nameEntryModalTitle = nameEntryIsSession ? 'Create Session' : 'Create IP';
  const nameEntryModalSub = nameEntryIsSession
    ? `user ${activeSessionId || 'default'}`
    : `workflow ${newIpInitialWorkflow()}`;
  const nameEntryFieldLabel = nameEntryIsSession ? 'session' : 'ip_id';
  const nameEntryInputLabel = nameEntryIsSession ? 'New workspace session' : 'New IP name';
  const nameEntryPlaceholder = nameEntryIsSession ? 'new_session' : 'new_ip';
  const nameEntryCancelLabel = nameEntryIsSession ? 'Cancel new session' : 'Cancel new IP';

  return (
    <div className="app" data-dir={dir} data-theme={theme}>
      {topNotice && (
        <div role="alert" style={{
          padding: '6px 12px', fontSize: 12, fontFamily: 'var(--mono)',
          background: 'color-mix(in oklch, var(--warn) 14%, transparent)',
          color: 'var(--warn)', borderBottom: '1px solid var(--warn)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span>⚠</span>
          <span style={{ flex: 1 }}>{topNotice}</span>
          <button onClick={() => setTopNotice('')}
                  style={{ background: 'transparent', border: 'none', color: 'var(--warn)',
                           cursor: 'pointer', fontSize: 14, lineHeight: 1 }}>×</button>
        </div>
      )}
      {wfSwitching && (
        <div role="status" aria-live="polite" style={{
          position: 'fixed', right: 12, bottom: 12, zIndex: 1200,
          maxWidth: 'min(520px, calc(100vw - 24px))',
          padding: '6px 10px', fontSize: 11, fontFamily: 'var(--mono)',
          background: 'var(--panel)',
          color: 'var(--accent)',
          border: '1px solid var(--accent)',
          borderRadius: 6,
          boxShadow: '0 10px 28px color-mix(in oklch, var(--fg) 18%, transparent)',
          display: 'flex', alignItems: 'center', gap: 8,
          lineHeight: '16px',
          pointerEvents: 'none',
        }}>
          <span style={{
            display: 'inline-block',
            width: 12, height: 12,
            border: '2px solid currentColor',
            borderRightColor: 'transparent',
            borderRadius: '50%',
            animation: 'atlas-spin 0.9s linear infinite',
          }} />
          <span style={{ flex: 1 }}>
            <strong>Workflow Loading ...</strong>{' '}
            <code>{wfSwitching.from || 'default'}</code> → <code>{wfSwitching.to}</code>
            {wfSwitching.ip ? <> · ip=<code>{wfSwitching.ip}</code></> : null}
            <span style={{ marginLeft: 8, opacity: 0.7 }}>
              {wfSwitching.preserveRunning ? '(previous worker kept running)' : '(agent stopped while loading)'}
            </span>
          </span>
          <style>{`@keyframes atlas-spin{to{transform:rotate(360deg)}}`}</style>
        </div>
      )}
      {!bootHidden && (
        <div role="status" aria-live="polite" style={{
          // Centered overlay so the user notices the handshake the
          // moment the page paints. Theme tokens drive bg/fg so dark
          // mode shows dark-on-dark and light mode shows light-on-
          // light; previous hardcoded `var(--bg-1, #14171c)` had a
          // baked-in dark fallback that clashed in light mode because
          // --bg-1 wasn't defined in styles.css.
          position: 'fixed',
          top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 9999,
          minWidth: 360,
          maxWidth: 480,
          padding: '18px 22px',
          fontSize: 13, fontFamily: 'var(--mono)',
          background: 'var(--bg-2)',
          border: '1px solid ' + (bootFailed ? 'var(--red, #ef4444)' : (bootDisplayDone ? 'var(--green, #22c55e)' : 'var(--accent)')),
          borderRadius: 8,
          boxShadow: '0 8px 32px color-mix(in oklch, var(--fg) 25%, transparent)',
          color: 'var(--fg)',
          display: 'flex', flexDirection: 'column', gap: 12,
          transition: 'opacity 250ms ease',
          opacity: bootDisplayDone ? 0.94 : 1,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {!bootDisplayDone && !bootFailed && (
              <span style={{
                display: 'inline-block',
                width: 18, height: 18,
                border: '2px solid currentColor',
                borderRightColor: 'transparent',
                borderRadius: '50%',
                animation: 'atlas-spin 0.9s linear infinite',
                flexShrink: 0,
              }} />
            )}
            {bootDisplayDone && <span style={{ fontSize: 20, fontWeight: 700 }}>✓</span>}
            {bootFailed && <span style={{ fontSize: 20, fontWeight: 700 }}>⚠</span>}
            <span style={{ fontWeight: 600 }}>
              {bootDisplayDone ? 'Backend connected'
                : bootFailed ? 'Connection problem'
                : 'Connecting to backend…'}
            </span>
            <span style={{ flex: 1 }} />
            <button onClick={() => setBootHidden(true)}
                    style={{ background: 'transparent', border: 'none',
                             color: 'currentColor', cursor: 'pointer',
                             fontSize: 18, lineHeight: 1, padding: 0 }}
                    title="dismiss">×</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {Object.entries(bootSteps).map(([k, v]) => {
              const labels: Record<string, string> = {
                ws: 'WebSocket connection',
                hello: 'Backend handshake (hello)',
                health: '/healthz endpoint',
                sessions: 'Session list hydrated',
                llm: 'LLM provider reachable (/models probe)',
              };
              return (
                <div key={k} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  fontSize: 12,
                  opacity: v === 'done' ? 1 : v === 'fail' ? 1 : 0.7,
                  color: v === 'done' ? 'var(--green, #22c55e)' : v === 'fail' ? 'var(--red, #ef4444)' : 'currentColor',
                }}>
                  <span style={{ width: 14, textAlign: 'center', fontWeight: 700 }}>
                    {v === 'done' ? '✓' : v === 'fail' ? '✗' : '○'}
                  </span>
                  <span>{labels[k] || k}</span>
                </div>
              );
            })}
          </div>
          <style>{`@keyframes atlas-spin{to{transform:rotate(360deg)}}`}</style>
        </div>
      )}
      {showNameEntryModal && (
        <div
          className="dir-name-modal-backdrop"
          onMouseDown={() => { if (!nameEntryBusy) setNameEntry(null); }}
        >
          <form
            className="dir-name-modal"
            data-esc-local="true"
            role="dialog"
            aria-modal="true"
            aria-label={nameEntryModalTitle}
            onMouseDown={e => e.stopPropagation()}
            onSubmit={(e) => { e.preventDefault(); commitNameEntry(); }}
          >
            <div className="dir-name-modal-head">
              <div>
                <div className="dir-name-modal-title">{nameEntryModalTitle}</div>
                <div className="dir-name-modal-sub">{nameEntryModalSub}</div>
              </div>
              <button
                type="button"
                className="dir-name-modal-close"
                aria-label={nameEntryCancelLabel}
                disabled={nameEntryBusy}
                onClick={() => setNameEntry(null)}
              >×</button>
            </div>
            <label className="dir-name-modal-field">
              <span>{nameEntryFieldLabel}</span>
              <input
                ref={nameEntryInputRef}
                className="dir-name-modal-input"
                aria-label={nameEntryInputLabel}
                placeholder={nameEntryPlaceholder}
                value={nameEntry.value}
                disabled={nameEntryBusy}
                onChange={e => setNameEntry({ kind: nameEntry.kind, value: e.currentTarget.value })}
                onKeyDown={e => {
                  if (e.key === 'Escape' && !nameEntryBusy) {
                    e.preventDefault();
                    setNameEntry(null);
                  }
                }}
              />
            </label>
            <div className="dir-name-modal-actions">
              <button
                type="button"
                className="dir-name-modal-btn"
                disabled={nameEntryBusy}
                onClick={() => setNameEntry(null)}
              >Cancel</button>
              <button
                type="submit"
                className="dir-name-modal-btn primary"
                disabled={nameEntryBusy || !String(nameEntry.value || '').trim()}
              >{nameEntryBusy ? 'Creating...' : 'Create'}</button>
            </div>
          </form>
        </div>
      )}
      <div className="dir-switcher atlas-desktop-only">
        <label className="dir-select-wrap" title={`User owner. Active namespace: .session/${normalizeSession(activeNamespace) || 'default'}`}>
          <span>user</span>
          <select
            aria-label="User owner"
            className="dir-select"
            disabled={!ownerEditable}
            value={activeSessionId || 'default'}
            onChange={() => {}}>
            <option value={activeSessionId || 'default'}>{activeSessionId || 'default'}</option>
          </select>
        </label>
        {ownerEditable && (
          <button className="dir-btn"
                  title="Create a local user owner and keep the selected IP/workflow"
                  onClick={newSessionId}>+ User</button>
        )}
        <label className="dir-select-wrap" title="Select workspace session. Namespace is user/session/ip_id/workflow.">
          <span>session</span>
          <select
            aria-label="Workspace session"
            className="dir-select"
            value={activeWorkspaceSession || 'default'}
            onChange={e => selectSessionId(e.currentTarget.value)}>
            {sessionIdOptions.includes(activeWorkspaceSession || 'default') ? null : (
              <option value={activeWorkspaceSession || 'default'}>{activeWorkspaceSession || 'default'}</option>
            )}
            {sessionIdOptions.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        {authState === 'authed' && (
          <button className="dir-btn"
                  title="Create a workspace session under the current user"
                  onClick={newSessionId}>+ Session</button>
        )}
        <label className="dir-select-wrap" title="Select ip_id. Namespace is user/session/ip_id/workflow.">
          <span>ip_id</span>
          <select
            aria-label="IP ID"
            className="dir-select ip"
            value={activeIp || WORKFLOW_DEFAULT}
            onChange={e => selectIp(e.currentTarget.value)}>
            <option value={WORKFLOW_DEFAULT}>{WORKFLOW_DEFAULT}</option>
            {/* `value=` of the <select> must exist as an <option>; otherwise
                React renders the first option (label "default") even though
                state holds a real IP like "PL330", which makes the dropdown
                disagree with the URL/session it is supposed to mirror. */}
            {authState !== 'authed' && activeIp && activeIp !== WORKFLOW_DEFAULT && !ipOptions.includes(activeIp) && (
              <option key={activeIp} value={activeIp}>{activeIp}</option>
            )}
            {ipOptions.filter(ip => ip !== WORKFLOW_DEFAULT).map(ip => (
              <option key={ip} value={ip}>{ip}</option>
            ))}
          </select>
        </label>
        <button className="dir-btn"
                title={`Create a new IP under the current user and switch to ${newIpInitialWorkflow()}`}
                onClick={() => beginNameEntry('ip')}>+ IP</button>
        <label className="dir-select-wrap" title="Workflow indicator. Use the left Workflow rail to switch.">
          <span>workflow</span>
          <output className="dir-select readonly">
            {execMode === 'orchestrator' ? 'orchestrator' : (currentWorkflow() || WORKFLOW_DEFAULT)}
          </output>
        </label>
        <button className="dir-btn"
                title={activeIp
                  ? `Download ${activeIp}/ as .zip`
                  : "Select an IP first to download just that workspace; "
                    + "leave blank for the whole project (slow)"}
                disabled={false}
                onClick={() => {
                  const sub = activeIp
                    ? `?subpath=${encodeURIComponent(activeIp)}`
                    : '';
                  window.location.href = `/api/workspace/download.zip${sub}`;
                }}>📦 .zip</button>
        <span style={{ width: 12 }} />
        <label className="dir-select-wrap font-select" title="Change UI font family">
          <span>font</span>
          <select
            aria-label="Font family"
            title="Change UI font family"
            className="dir-select font"
            value={selectedFontMode}
            onPointerDown={e => e.stopPropagation()}
            onClick={e => e.stopPropagation()}
            onInput={e => chooseFontMode(e.currentTarget.value)}
            onChange={e => chooseFontMode(e.currentTarget.value)}>
            {ATLAS_FONT_MODE_OPTIONS.map(opt => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
        </label>
        <label className="dir-select-wrap" title="Change UI text size">
          <span>size</span>
          <select
            className="dir-select mini"
            value={fontScale}
            onChange={e => setFontScale(e.currentTarget.value)}>
            <option value="compact">13px</option>
            <option value="normal">14px</option>
            <option value="large">15px</option>
            <option value="xl">16px</option>
          </select>
        </label>
        <label className="dir-select-wrap" title="Change virtual canvas resolution">
          <span>res</span>
          <select
            className="dir-select res"
            value={resolution}
            onChange={e => setResolution(e.currentTarget.value)}>
            {ATLAS_UI_RESOLUTION_PRESETS.map(p => (
              <option key={p.key} value={p.key}>{p.label}</option>
            ))}
          </select>
        </label>
        <span style={{ width: 12 }} />
        <button className={`dir-btn ${theme === 'dark' ? 'active' : ''}`}
                onClick={() => setTheme('dark')}>Dark</button>
        <button className={`dir-btn ${theme === 'light' ? 'active' : ''}`}
                onClick={() => setTheme('light')}>Light</button>
        <button className={`dir-btn ${uiLang === 'ko' ? 'active' : ''}`}
                title="Prefer Korean for visible agent output"
                onClick={() => chooseUiLang('ko')}>한국어</button>
        <button className={`dir-btn ${uiLang === 'en' ? 'active' : ''}`}
                title="Prefer English for visible agent output"
                onClick={() => chooseUiLang('en')}>English</button>
        <span style={{ width: 12 }} />
        <button className="dir-btn"
                title="Abort the agent's current iteration  (Esc)"
                onClick={stopAgent}>■ Stop</button>
        <button className="dir-btn"
                title="Terminate this session worker; Atlas UI server stays alive  (Ctrl/⌘+Q)"
                onClick={exitAll}>✕ Exit</button>
        <span style={{ width: 12 }} />
        {window.ATLAS_USER && (
          <button className="dir-btn"
                  title={`Logged in as ${window.ATLAS_USER.username}. Click to log out.`}
                  onClick={async () => {
                    try {
                      await fetch('/api/auth/logout', { method: 'POST' });
                    } catch (_) {}
                    try {
                      localStorage.removeItem('atlasUserSessionId');
                      localStorage.removeItem('atlasActiveSession');
                    } catch (_) {}
                    window.location.reload();
                  }}>↩ {window.ATLAS_USER.username}</button>
        )}
        <span data-row-break style={{flex:'0 0 100%',width:'100%',height:0,margin:0,padding:0,border:0}} />
        <button className={`dir-btn ${screen === 'dashboard' ? 'active' : ''}`}
                title="User dashboard · current focus · recent sessions · usage"
                onClick={() => setScreen('dashboard')}>▦ Dashboard</button>
        <button className={`dir-btn ${screen === 'workspace' ? 'active' : ''}`}
                title="Live agent · chat · sidebar (sim/lint/scope)"
                onClick={() => setScreen('workspace')}>⌂ Workspace</button>
        <button className={`dir-btn ${screen === 'pipeline' ? 'active' : ''}`}
                title="Live pipeline dispatcher · stage situation board"
                onClick={() => setScreen('pipeline')}>◫ Pipeline</button>
        <button className={`dir-btn ${screen === 'architect' ? 'active' : ''}`}
                title="SoC structure · per-module status grid · block diagram (rich progress view)"
                onClick={() => setScreen('architect')}>◇ Architect</button>
        <button className={`dir-btn ${screen === 'guide' ? 'active' : ''}`}
                title="How to use ATLAS · default mode + per-workflow capabilities"
                onClick={() => setScreen('guide')}>📖 Guide</button>
        <label className="dir-select-wrap run-policy">
          <span>run</span>
          <select
            className="dir-select policy"
            value={runMode}
            onChange={e => saveRunPolicy(e.currentTarget.value, execMode)}
            title="Run Mode controls evidence strictness, not IP size">
            {ATLAS_RUN_MODE_OPTIONS.map(opt => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
        </label>
        <label className="dir-select-wrap run-policy">
          <span>exec</span>
          <select
            className="dir-select exec"
            value={ATLAS_EXEC_MODE_LOCKED ? 'single-worker' : execMode}
            disabled={ATLAS_EXEC_MODE_LOCKED}
            onChange={e => { if (!ATLAS_EXEC_MODE_LOCKED) saveRunPolicy(runMode, e.currentTarget.value); }}
            title={ATLAS_EXEC_MODE_LOCKED
              ? 'Exec Mode is locked to Single Worker'
              : 'Exec Mode chooses single-worker execution or orchestrator-managed workers'}>
            {(ATLAS_EXEC_MODE_LOCKED
              ? ATLAS_EXEC_MODE_OPTIONS.filter(opt => opt.key === 'single-worker')
              : ATLAS_EXEC_MODE_OPTIONS
            ).map(opt => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
        </label>
        <span style={{ display: 'contents' }}><PipelineRunningChip onClick={() => setScreen('pipeline')} /></span>
        <OrchInlineStatus activeIp={activeIp} />
      </div>
      {/* ── Mobile header (< 900px only) ───────────────────────────── */}
      <MobileHeader
        activeIp={activeIp}
        ipOptions={ipOptions}
        onSelectIp={selectIp}
        onCreateIp={() => beginNameEntry('ip')}
        workflow={execMode === 'orchestrator' ? 'orchestrator' : currentWorkflow()}
        workflowOptions={WORKFLOW_OPTIONS}
        onSelectWorkflow={selectWorkflow}
        onOpenLeftDrawer={() => {
          window.dispatchEvent(new CustomEvent('atlas:mobile-left-drawer'));
        }}
        onOpenRightDrawer={() => {
          window.dispatchEvent(new CustomEvent('atlas:mobile-right-drawer'));
        }}
        stopAgent={stopAgent}
        exitAll={exitAll}
      />
      <div className="app-main">
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {screen === 'dashboard' && window.AtlasUserDashboard
            ? <ErrorBoundary label="Dashboard">
                <window.AtlasUserDashboard
                  activeNamespace={activeNamespace}
                  activeIp={activeIp}
                  activeWorkflow={currentWorkflow()}
                  execMode={execMode}
                  runMode={runMode}
                  onOpenScreen={setScreen}
                  onActivateSession={activateDashboardSession}
                />
              </ErrorBoundary>
            : screen === 'pipeline' && window.AtlasPipeline
            ? <ErrorBoundary label="Pipeline"><window.AtlasPipeline /></ErrorBoundary>
            : screen === 'architect' && window.SocArchitect
              ? <ErrorBoundary label="Architect"><window.SocArchitect ipOptions={ipOptions} activeIp={activeIp} onSelectIp={selectIp} /></ErrorBoundary>
            : screen === 'guide' && window.AtlasGuide
              ? <ErrorBoundary label="Guide"><window.AtlasGuide /></ErrorBoundary>
              : <ErrorBoundary label="Workspace"><Workspace dir={dir} uiLang={uiLang} activeNamespace={activeNamespace} activeWorkflow={currentWorkflow()} /></ErrorBoundary>}
        </div>
        {/* App-level StatusBar removed — model / tokens / iter / rate /
            SAFE chips were duplicated by the right-side AgentStatusPanel,
            and the row clipped against the bottom of the 1080px canvas
            so most users never saw it anyway. */}
      </div>
    </div>
  );
};
