// workspace-feed-askuser.tsx — SSOT-approval + ask_user interactive blocks.
//
// Extracted from workspace-feed-cards.tsx as part of the strangler-fig
// TypeScript migration to keep each module under 1000 lines. This is an
// INERT mirror: the legacy workspace.jsx still serves the live app.
//
// Owns: the inline-markdown escapers (_escHtml / renderInline), the
// SSOT-approval ("To SSOT") card, the AskUserQuestion option block, the
// AskUserCall action/obs round-trip, and the past-Q&A history panel.
//
// Migration notes (house style):
//   - Real ES module. `React.Fragment` -> imported `Fragment` (automatic JSX
//     runtime, so no `import React` for JSX itself).
//   - window-sourced ATLAS globals (backend / QA_FLOWS / ACTIVE_SESSION /
//     ATLAS_UI_LANG / atlasData) are read off window and typed `any`.
import { Fragment } from 'react';

// `normalizeUiSession` lives in workspace-session-routing (not in this slice's
// allowed import set). It is a tiny pure reader over window.atlasData; inline
// the same logic here so SsotApprovalCard stays self-contained.
const normalizeUiSession = (session: any): string => {
  const w = window as any;
  const norm = (w.atlasData && w.atlasData.normalizeSessionName) || w.normalizeAtlasSessionName;
  try { return norm ? norm(session || '') : ''; }
  catch (_) { return ''; }
};

// HTML-escape before any interpolation. Without this, the fallback
// renderer was happy to drop user-controlled text (e.g. file contents
// the agent quoted) straight into HTML — `</code><img src=x onerror=…>`
// inside a backtick span would have escaped the <code> tag and
// injected a payload. DOMPurify catches it downstream now too, but
// belt-and-suspenders.
export const _escHtml = (s: any) => String(s)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');
export const renderInline = (s: any) => _escHtml(s)
  .replace(/`([^`]+)`/g, '<code class="acc" style="background:var(--bg-2);padding:1px 4px;border-radius:2px;">$1</code>')
  .replace(/\*\*([^*]+)\*\*/g, '<b style="color:var(--fg);">$1</b>');

export const SsotApprovalCard = ({ payload }: any) => {
  const ip = payload?.ip || '';
  const decisions = payload?.decisions || {};
  const missing = Array.isArray(payload?.missing) ? payload.missing : [];
  const approved = !!payload?.approved;
  const send = (text: any) => {
    if (!text || !(window as any).backend?.send) return;
    let session = 'default';
    try {
      session = normalizeUiSession((window as any).ACTIVE_SESSION || '') || 'default';
    } catch (_) {
      session = 'default';
    }
    (window as any).backend.send({
      type: 'prompt',
      text,
      session,
      ui_lang: (window as any).ATLAS_UI_LANG || 'ko',
    });
  };
  const rows = [
    ['purpose', 'Purpose'],
    ['bus_interface', 'Bus'],
    ['register_map', 'Registers'],
    ['clock_reset', 'Clock/reset'],
    ['interrupt', 'Interrupt'],
    ['memory_map', 'Memory map'],
    ['parameters', 'Parameters'],
    ['submodule_structure', 'Submodules'],
    ['test_expectation', 'Tests'],
  ];
  const statusText = missing.length
    ? `Missing ${missing.length} decision${missing.length === 1 ? '' : 's'} · To SSOT carries review flags`
    : approved ? 'YAML write enabled' : 'Ready · press To SSOT';
  return (
    <div className="react-block obs" style={{
      borderLeftColor: approved ? 'var(--ok)' : 'var(--warn)',
      background: approved
        ? 'color-mix(in oklch, var(--ok) 8%, var(--bg-2))'
        : 'color-mix(in oklch, var(--warn) 8%, var(--bg-2))',
      padding: '10px 12px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
        <div>
          <span className="rb-tag" style={{ color: approved ? 'var(--ok)' : 'var(--warn)' }}>ssot to-yaml</span>
          <b style={{ marginLeft: 8 }}>{ip}</b>
        </div>
        <span style={{
          fontSize: 10,
          color: approved ? 'var(--ok)' : 'var(--warn)',
          border: `1px solid ${approved ? 'var(--ok)' : 'var(--warn)'}`,
          padding: '2px 6px',
          borderRadius: 2,
          whiteSpace: 'nowrap',
        }}>{statusText}</span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--fg-mute)', marginBottom: 10 }}>
        Review the plan, then press To SSOT. That action approves the current evidence and generates the SSOT YAML from this Web UI session.
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(92px, 0.28fr) minmax(0, 1fr)',
        gap: '4px 10px',
        marginBottom: 10,
        fontSize: 'var(--ui-control-font-size)',
      }}>
        {rows.map(([key, label]) => (
          <Fragment key={key}>
            <span style={{ color: missing.includes(key) ? 'var(--warn)' : 'var(--fg-mute)' }}>{label}</span>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {decisions[key] || <span className="warn">missing</span>}
            </span>
          </Fragment>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <button
          className="mini-btn"
          disabled={!ip}
          onClick={() => send(payload?.generate_cmd || `/to-ssot ${ip}`)}
          title="Approve current evidence and generate SSOT YAML"
        >
          To SSOT
        </button>
        <button
          className="mini-btn"
          onClick={() => send(`/new-ip ${ip} ${payload?.kind || ''}`.trim())}
          title="Reopen the Q&A cards for this IP"
        >
          revise Q&A
        </button>
        <code className="acc">{payload?.generate_cmd || `/to-ssot ${ip}`}</code>
      </div>
    </div>
  );
};

export const AskUserQuestionBlock = ({
  index = 0,
  block = {},
  blockState = { opts: [], custom: '' },
  kind = 'single',
  isBatched = false,
  isActive = true,
  answered = false,
  selectedIndex = 0,
  showQuestion = true,
  onEnsureActive = () => {},
  onSelectIndex = () => {},
  onToggleOption = () => {},
  onCustom = () => {},
  onSelectAll,
  onClearAll,
}: any) => {
  const blockOpts = blockState.opts || [];
  const customIdx = blockOpts.length;
  const blockMultiline = !!(block.multiline || String(block.placeholder || '').includes('\n'));
  const blockPlaceholder = block.placeholder || '';
  const blockSubtitle = block.subtitle || '';
  const blockQuestion = block.question || '';
  const ensureActive = () => onEnsureActive(index);
  return (
    <div
      key={index}
      onClick={() => { if (isBatched && !isActive) ensureActive(); }}
      style={{
        marginBottom: isBatched ? 12 : 0,
        padding: isBatched ? '10px 12px' : 0,
        border: isBatched
          ? `1px solid ${isActive ? 'var(--accent)' : 'var(--line)'}`
          : 'none',
        background: isBatched && isActive
          ? 'color-mix(in oklch, var(--accent) 5%, transparent)'
          : 'transparent',
        borderRadius: 2,
        cursor: isBatched && !isActive ? 'pointer' : 'default',
      }}
    >
      {showQuestion ? (
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 10, color: 'var(--fg)' }}>
          {isBatched && (
            <span
              className={answered ? 'ok' : 'mute'}
              style={{ marginRight: 8, fontSize: 12, fontWeight: 700, fontFamily: 'var(--mono)' }}
            >
              {answered ? '☒' : '☐'} Q{index + 1}.
            </span>
          )}
          {blockQuestion}
          {blockSubtitle && (
            <div className="mute" style={{ fontSize: 'var(--ui-control-font-size)', fontWeight: 400, marginTop: 2 }}>
              {blockSubtitle}
            </div>
          )}
        </div>
      ) : null}

      {kind === 'multi' && blockOpts.length > 1 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 11 }}>
          <span
            onClick={(ev) => {
              ev.stopPropagation();
              ensureActive();
              if (onSelectAll) onSelectAll(blockOpts);
            }}
            style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--accent)', color: 'var(--accent)', borderRadius: 2 }}
            title="Select every option">
            ☑ Select all
          </span>
          <span
            onClick={(ev) => {
              ev.stopPropagation();
              ensureActive();
              if (onClearAll) onClearAll(blockOpts);
            }}
            style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--line)', color: 'var(--fg-mute)', borderRadius: 2 }}
            title="Deselect every option">
            ☐ Clear
          </span>
          <span className="mute" style={{ alignSelf: 'center', fontSize: 10 }}>
            · click rows to toggle individually
          </span>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {blockOpts.map((o: any, oi: number) => {
          const isSel = o.selected;
          const focused = isActive && selectedIndex === oi;
          return (
            <div
              key={o.id}
              onClick={(ev) => { ev.stopPropagation(); ensureActive(); onSelectIndex(oi); onToggleOption(o.id); }}
              style={{
                display: 'grid',
                gridTemplateColumns: '24px 28px 1fr',
                alignItems: 'baseline',
                gap: 6,
                padding: '4px 8px',
                background: focused ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                borderLeft: `2px solid ${focused ? 'var(--accent)' : 'transparent'}`,
                cursor: 'pointer',
                fontFamily: 'var(--mono)',
                fontSize: 13,
                lineHeight: 1.4,
              }}
            >
              <span className="mute" style={{ textAlign: 'right' }}>{oi + 1}.</span>
              <span style={{ color: isSel ? 'var(--accent)' : 'var(--fg-mute)', fontWeight: 700 }}>
                {kind === 'multi' ? (isSel ? '[✓]' : '[ ]') : (isSel ? '(•)' : '( )')}
              </span>
              <div>
                <span style={{ color: focused ? 'var(--fg)' : (isSel ? 'var(--fg)' : 'var(--fg-dim, var(--fg))') }}>
                  {o.label}
                  {o.locked && <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>(required)</span>}
                </span>
                <div className="mute" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)', marginTop: 1 }}>
                  {o.detail}
                </div>
              </div>
            </div>
          );
        })}

        <div
          onClick={(ev) => { ev.stopPropagation(); ensureActive(); onSelectIndex(customIdx); }}
          style={{
            display: 'grid',
            gridTemplateColumns: '24px 28px 1fr',
            alignItems: 'baseline',
            gap: 6,
            padding: '4px 8px',
            background: isActive && selectedIndex === customIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            borderLeft: `2px solid ${isActive && selectedIndex === customIdx ? 'var(--accent)' : 'transparent'}`,
            cursor: 'text',
            fontFamily: 'var(--mono)',
            fontSize: 13,
          }}
        >
          <span className="mute" style={{ textAlign: 'right' }}>{blockOpts.length + 1}.</span>
          <span style={{ color: blockState.custom ? 'var(--warn)' : 'var(--fg-mute)', fontWeight: 700 }}>
            {blockState.custom ? '[✓]' : '[ ]'}
          </span>
          <div style={{ display: 'flex', alignItems: 'stretch', gap: 6 }}>
            {blockMultiline ? (
              <textarea
                className="askcustom"
                value={blockState.custom || ''}
                onChange={(e) => { ensureActive(); onCustom(e.target.value); }}
                onFocus={() => { ensureActive(); onSelectIndex(customIdx); }}
                placeholder={blockPlaceholder || 'custom answer / free-form note…'}
                spellCheck={false}
                style={{
                  background: 'transparent', border: '1px solid var(--line)', outline: 'none',
                  fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 12, flex: 1,
                  padding: '6px 8px', minHeight: 120, lineHeight: 1.45, resize: 'vertical',
                  whiteSpace: 'pre-wrap',
                }}
              />
            ) : (
              <input
                className="askcustom"
                value={blockState.custom || ''}
                onChange={(e) => { ensureActive(); onCustom(e.target.value); }}
                onFocus={() => { ensureActive(); onSelectIndex(customIdx); }}
                placeholder={blockPlaceholder || 'custom answer / free-form note…'}
                style={{
                  background: 'transparent', border: 'none', outline: 'none',
                  fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 13, flex: 1, padding: 0,
                }}
              />
            )}
            {isActive && selectedIndex === customIdx && <span className="cursor-thin" />}
          </div>
        </div>
      </div>
    </div>
  );
};

// then (when submitted) appends an `obs:` line with the user's reply.
export const AskUserCall = ({ flowId, state, dir }: any) => {
  const flow = (window as any).QA_FLOWS[flowId];
  if (!flow || !state) return null;
  const submitted = state.submitted;
  const isBatched = !!state.batched;
  let sel: any[] = [];
  let replySummary = '';
  let argSummary;
  if (isBatched) {
    const tabCount = (flow.questions || []).length;
    const allSel = (state.states || []).map((ts: any, i: number) => {
      const ss = (ts.opts || []).filter((o: any) => o.selected).map((o: any) => o.label).join(', ');
      const c = (ts.custom || '').trim();
      return `Q${i + 1}: ${ss}${c ? (ss ? ' · ' : '') + 'note=' + c : ''}`;
    });
    replySummary = allSel.join(' | ');
    argSummary = `flow="${flowId}", batched=${tabCount} questions`;
  } else {
    sel = state.opts.filter((o: any) => o.selected);
    replySummary = sel.map((o: any) => o.label).join(', ') + (state.custom ? `, +"${state.custom}"` : '');
    argSummary = `flow="${flowId}", question="${flow.question.length > 48 ? flow.question.slice(0, 48) + '…' : flow.question}", kind=${flow.kind}, options=${flow.options.length}`;
  }

  return (
    <>
      <div className="react-block action">
        <span className="rb-tag">action</span>
        <span>
          <b style={{ color: 'var(--tool-accent)' }}>ask_user</b>
          <span className="mute">(</span>
          <span style={{ color: 'var(--fg-mute)' }}>{argSummary}</span>
          <span className="mute">)</span>
          {!submitted && (
            <span className="warn" style={{
              marginLeft: 10, fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase',
              padding: '1px 6px', border: '1px solid var(--warn)', borderRadius: 2,
              background: 'color-mix(in oklch, var(--warn) 12%, transparent)',
            }}>
              ⌨ input pending · reply below
            </span>
          )}
        </span>
      </div>
      {submitted && (
        <div className="react-block obs">
          <span className="rb-tag">obs</span>
          <span><span className="ok">✓</span> user replied · <span style={{ color: 'var(--fg)' }}>{replySummary || '(no selection)'}</span></span>
        </div>
      )}
    </>
  );
};

// ── ask_user — past Q&A round-trips, newest first ────────────────
// Persisted to localStorage in workspace.jsx so the trail survives a
// page reload. Renders below the active SSOT board on the Q&A tab.
export const QaHistoryPanel = ({ history, onClear }: any) => {
  if (!history || history.length === 0) return null;
  const fmtTs = (ts: any) => {
    try {
      const d = new Date(ts);
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      const mo = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      return `${mo}-${dd} ${hh}:${mm}`;
    } catch (_) { return ''; }
  };
  return (
    <div style={{ marginTop: 18 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8,
        paddingBottom: 6, borderBottom: '1px dashed var(--line)',
        fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em', textTransform: 'uppercase',
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
      }}>
        <span className="acc" style={{ fontWeight: 700 }}>▸ Q&amp;A history</span>
        <span className="mute">·</span>
        <span>{history.length} answered</span>
        <span style={{ flex: 1 }} />
        <span
          onClick={onClear}
          style={{ cursor: 'pointer', color: 'var(--fg-mute)', fontSize: 10 }}
          title="Clear local Q&A history (does not affect the agent's session)"
        >clear</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {history.map((entry: any, i: number) => (
          <details
            key={entry.flowId + ':' + entry.ts + ':' + i}
            open={i === 0}
            style={{
              border: '1px solid var(--line)',
              borderLeft: '2px solid var(--ok)',
              borderRadius: 2, padding: '6px 10px',
              background: 'color-mix(in oklch, var(--ok) 4%, transparent)',
            }}
          >
            <summary style={{
              cursor: 'pointer', fontSize: 12, fontFamily: 'var(--mono)',
              listStyle: 'none', display: 'flex', gap: 8, alignItems: 'center',
            }}>
              <span style={{ color: 'var(--ok)', fontWeight: 700 }}>☑</span>
              <span style={{ color: 'var(--fg)' }}>
                {entry.items.length} question{entry.items.length === 1 ? '' : 's'}
                {entry.ip ? ` · ${entry.ip}` : ''}
                {entry.workflow ? ` · ${entry.workflow}` : ''}
              </span>
              <span style={{ flex: 1 }} />
              <span className="mute" style={{ fontSize: 10 }}>{fmtTs(entry.ts)}</span>
            </summary>
            <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {entry.items.map((q: any, qi: number) => {
                const sels = (q.selected || []).map((s: any) => s.label).join(', ');
                const ans = sels
                  ? sels + (q.custom ? ` · note: "${q.custom}"` : '')
                  : (q.custom ? `note: "${q.custom}"` : '(no answer)');
                return (
                  <div key={qi} style={{
                    fontSize: 12, fontFamily: 'var(--mono)',
                    paddingLeft: 6, borderLeft: '1px solid var(--line-2)',
                  }}>
                    <div style={{ color: 'var(--fg-dim)' }}>
                      Q{qi + 1}. {q.question}
                    </div>
                    <div style={{ color: 'var(--fg)', marginTop: 1 }}>
                      <span className="mute">→ </span>{ans}
                    </div>
                  </div>
                );
              })}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
};
