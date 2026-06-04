// ssot-doc.tsx — TypeScript migration of ssot-doc.jsx (Phase 13a refactor:
// SsotDocPane extracted from workspace.jsx).
//
// What changed vs ssot-doc.jsx:
//   - Proper ES module: `import { useState, ... } from 'react'` instead of the
//     ambient global `React` + `<script type="text/babel">` compile. Call sites
//     rewritten from `React.useState(` to `useState(`, etc.
//   - Real typed export (`SsotDocPane`) — consumers will `import` it once they
//     migrate.
//
// The component reads three workspace.jsx-scope helpers
// (SSOT_SECTION_LABELS, ssotIpFromSession, ssotTitleFor) — plus ACTIVE_IP /
// ACTIVE_SESSION — via window globals that workspace.jsx exposes after their
// definitions. ssot-doc.tsx loads BEFORE workspace.jsx in index.html so
// workspace.jsx's `const SsotDocPane = window.SsotDocPane;` alias finds the
// export. The helper lookups happen inside the body at RENDER time, by which
// point workspace.jsx has set window.<helper>.
//
// Cross-file deps (SSOT_SECTION_LABELS / ssotIpFromSession / ssotTitleFor /
// ACTIVE_IP / ACTIVE_SESSION) are still owned by the unmigrated workspace.jsx,
// so they are kept as window.* lookups. They are not (yet) in
// types/atlas-window.d.ts, so a local typed view of the window surface is used
// to keep the references type-checked without editing the shared ambient
// declaration.
//
// Transitional: still bridges to `window.SsotDocPane` at the bottom so
// not-yet-migrated .jsx files (e.g. workspace.jsx) keep resolving the global
// component.
import {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
  type ReactNode,
  type DragEvent,
} from 'react';
import { fetchSsotDocSource, sourceForSsotDocTarget } from './ssot-doc-feedback-api';
import {
  buildSsotDocTargetFromElement,
  clearSsotDocSelection,
  dispatchSsotDocComment,
  findSsotDocSelectableElement,
  markSsotDocSelection,
} from './ssot-doc-feedback-dom';
import type { SsotDocSelectedTarget, SsotDocSourceResponse } from './ssot-doc-feedback-types';

// ── Local typed view of the cross-file window globals this file reads. ──
// Owned by workspace.jsx (not yet migrated); mirror their runtime shapes
// loosely enough to preserve behavior. Remove once workspace.jsx migrates and
// these become real imports.
interface SsotDocWindow {
  SSOT_SECTION_LABELS?: Record<string, string>;
  ssotIpFromSession?: (session: unknown) => string;
  ssotTitleFor?: (key: string) => string;
  ACTIVE_IP?: string;
  ACTIVE_SESSION?: unknown;
}

// Typed accessor for the cross-file globals. Cast preserves the exact
// runtime `window.X` lookups while giving TS the shapes above.
const ssotWin = window as unknown as SsotDocWindow;

const activeSsotSessionId = (): string => {
  const raw = String(ssotWin.ACTIVE_SESSION || '').trim();
  return raw === 'default' ? '' : raw;
};

export interface SsotDocPaneProps {
  uiLang?: string;
  ip?: string;
  onBack?: () => void;
}

export const SsotDocPane = ({ uiLang = 'ko', ip = '', onBack }: SsotDocPaneProps): ReactNode => {
  // Late-bound helper lookups (workspace.jsx assigns these globals).
  const SSOT_SECTION_LABELS = ssotWin.SSOT_SECTION_LABELS || {};
  const ssotIpFromSession = ssotWin.ssotIpFromSession || ((_session: unknown) => '');
  const ssotTitleFor = ssotWin.ssotTitleFor || ((k: string) => k);
  const [reloadKey, setReloadKey] = useState(0);
  const [docMode, setDocMode] = useState('view');
  const [feedbackSection, setFeedbackSection] = useState('custom');
  const [feedbackPath, setFeedbackPath] = useState('');
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackBusy, setFeedbackBusy] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState('');
  const [docFrameReady, setDocFrameReady] = useState(0);
  const [selectedTarget, setSelectedTarget] = useState<SsotDocSelectedTarget | null>(null);
  const [sourceOpen, setSourceOpen] = useState(false);
  const [sourceBusy, setSourceBusy] = useState(false);
  const [sourceInfo, setSourceInfo] = useState<SsotDocSourceResponse | null>(null);
  const docFrameRef = useRef<HTMLIFrameElement>(null);
  const effectiveIp = String(ip || ssotWin.ACTIVE_IP || ssotIpFromSession(ssotWin.ACTIVE_SESSION) || '').trim();
  const sessionId = activeSsotSessionId();
  const qs = effectiveIp ? (() => {
    const params = new URLSearchParams({
      ip: effectiveIp,
      format: 'html',
      inline: '1',
      v: String(reloadKey),
    });
    if (sessionId) params.set('session_id', sessionId);
    return params.toString();
  })() : '';
  const inlineUrl = qs ? `/api/ssot/export?${qs}` : '';
  const downloadUrl = effectiveIp ? (() => {
    const params = new URLSearchParams({ ip: effectiveIp, format: 'html' });
    if (sessionId) params.set('session_id', sessionId);
    return `/api/ssot/export?${params.toString()}`;
  })() : '';
  const title = uiLang === 'en' ? 'SSOT Document' : 'SSOT Document';
  const subtitle = uiLang === 'en'
    ? 'Rendered from the same HTML export artifact.'
    : 'HTML export 산출물을 탭 안에서 그대로 렌더링합니다.';
  const docSections = useMemo(() => {
    const preferred = ['top_module', 'io_list', 'registers', 'features', 'function_model', 'cycle_model', 'custom'];
    const seen = new Set<string>();
    return preferred.concat(Object.keys(SSOT_SECTION_LABELS)).filter(key => {
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, []);
  const canSendFeedback = !!selectedTarget && !feedbackBusy;
  const selectedSourceInfo = sourceForSsotDocTarget(sourceInfo, selectedTarget);
  const applyDocSelection = useCallback((target: SsotDocSelectedTarget | null, el?: Element | null) => {
    if (!target) return;
    setSelectedTarget(target);
    setSourceOpen(false);
    setSourceInfo(null);
    setFeedbackSection(target.section || 'custom');
    setFeedbackPath(target.path);
    setFeedbackStatus(uiLang === 'en'
      ? `selected: ${target.label}`
      : `selected: ${target.label}`);
    if (el) markSsotDocSelection(el);
  }, [uiLang]);
  const handleDocCommentDragStart = (ev: DragEvent<HTMLButtonElement>) => {
    if (docMode !== 'feedback' || !selectedTarget) return;
    ev.dataTransfer.effectAllowed = 'copy';
    ev.dataTransfer.setData('text/plain', 'atlas-doc-comment');
    setFeedbackStatus(uiLang === 'en'
      ? 'drop comment on a document component'
      : 'comment를 DOC component 위에 drop 하세요');
  };
  useEffect(() => {
    if (docMode !== 'feedback') return undefined;
    const frame = docFrameRef.current;
    if (!frame) return undefined;
    let frameDoc: Document | null = null;
    try {
      frameDoc = frame.contentDocument;
    } catch (_) {
      frameDoc = null;
    }
    if (!frameDoc || !frameDoc.body) return undefined;
    const style = frameDoc.createElement('style');
    style.textContent = [
      'body.atlas-feedback-drop-mode [data-ssot-path] { cursor: copy; }',
      'body.atlas-feedback-drop-mode [data-ssot-path]:hover { outline: 2px dashed #315fdc; outline-offset: 4px; }',
      'body.atlas-feedback-drop-mode [data-atlas-doc-feedback-selected="1"] { outline: 3px solid #315fdc !important; outline-offset: 5px; background: rgba(49,95,220,.08) !important; }',
    ].join('\n');
    frameDoc.head.appendChild(style);
    frameDoc.body.classList.add('atlas-feedback-drop-mode');
    const selectFromEvent = (ev: Event) => {
      const el = findSsotDocSelectableElement(ev.target);
      const target = buildSsotDocTargetFromElement(el);
      if (target && el) applyDocSelection(target, el);
    };
    const onClick = (ev: Event) => {
      selectFromEvent(ev);
    };
    const onDragOver = (ev: Event) => {
      ev.preventDefault();
      const dt = (ev as globalThis.DragEvent).dataTransfer;
      if (dt) dt.dropEffect = 'copy';
      const el = findSsotDocSelectableElement(ev.target);
      if (el) markSsotDocSelection(el);
    };
    const onDrop = (ev: Event) => {
      ev.preventDefault();
      selectFromEvent(ev);
    };
    const onKeyDown = (ev: Event) => {
      const key = (ev as KeyboardEvent).key;
      if (key !== 'Escape') return;
      clearSsotDocSelection(frameDoc);
      setSelectedTarget(null);
      setSourceInfo(null);
      setSourceOpen(false);
      setFeedbackStatus('');
    };
    frameDoc.addEventListener('click', onClick);
    frameDoc.addEventListener('dragover', onDragOver);
    frameDoc.addEventListener('drop', onDrop);
    frameDoc.addEventListener('keydown', onKeyDown);
    frameDoc.defaultView?.addEventListener('keydown', onKeyDown);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      frameDoc.removeEventListener('click', onClick);
      frameDoc.removeEventListener('dragover', onDragOver);
      frameDoc.removeEventListener('drop', onDrop);
      frameDoc.removeEventListener('keydown', onKeyDown);
      frameDoc.defaultView?.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keydown', onKeyDown);
      frameDoc.body?.classList.remove('atlas-feedback-drop-mode');
      try { style.remove(); } catch (_) {}
    };
  }, [docMode, docFrameReady, reloadKey, applyDocSelection]);
  const selectedDocText = useCallback(() => {
    try {
      return String(docFrameRef.current?.contentWindow?.getSelection?.()?.toString() || '').trim();
    } catch (_) {
      return '';
    }
  }, []);
  const handleShowSsotSource = useCallback(async () => {
    if (!effectiveIp || !selectedTarget || sourceBusy) return;
    setSourceBusy(true);
    setFeedbackStatus('');
    try {
      const payload = await fetchSsotDocSource({ ip: effectiveIp, target: selectedTarget });
      setSourceInfo(payload);
      setSourceOpen(true);
    } catch (err) {
      setFeedbackStatus(String((err as { message?: unknown })?.message || err || 'source lookup failed'));
    } finally {
      setSourceBusy(false);
    }
  }, [effectiveIp, selectedTarget, sourceBusy]);
  const handleCommentToChat = useCallback(async () => {
    if (!effectiveIp || !selectedTarget || feedbackBusy) return;
    setFeedbackBusy(true);
    let source = sourceForSsotDocTarget(sourceInfo, selectedTarget);
    if (!source) {
      try {
        source = await fetchSsotDocSource({ ip: effectiveIp, target: selectedTarget });
        setSourceInfo(source);
      } catch (_) {
        source = null;
      }
    }
    try {
      dispatchSsotDocComment({
        ip: effectiveIp,
        target: selectedTarget,
        comment: feedbackComment,
        selectedText: selectedDocText(),
        source,
      });
      setFeedbackStatus(uiLang === 'en' ? 'sent to chat input' : 'chat input으로 보냈습니다');
      onBack?.();
    } finally {
      setFeedbackBusy(false);
    }
  }, [effectiveIp, feedbackBusy, feedbackComment, onBack, selectedDocText, selectedTarget, sourceInfo, uiLang]);

  if (!effectiveIp) {
    return (
      <div style={{ flex: 1, minHeight: 0, padding: 18, color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>
        No active IP for SSOT document rendering.
      </div>
    );
  }

  return (
    <div style={{
      flex: 1,
      minHeight: 0,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      background: 'var(--bg)',
    }}>
      <div style={{
        padding: '10px 14px',
        borderBottom: '1px solid var(--line)',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: 'var(--bg-2)',
        fontFamily: 'var(--mono)',
      }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{
            color: 'var(--magenta)',
            fontWeight: 800,
            fontSize: 12,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}>{title}</div>
          <div className="mute trunc" style={{ marginTop: 3, fontSize: 'var(--ui-control-font-size)' }}>
            {effectiveIp} · {subtitle}
          </div>
        </div>
        <button type="button" className="btn" onClick={() => setReloadKey(k => k + 1)} style={{ fontSize: 10 }}>
          refresh
        </button>
        <div style={{ display: 'inline-flex', border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
          {[
            ['view', 'View Mode'],
            ['feedback', 'Feedback Mode'],
          ].map(([mode, label]) => (
            <button
              key={mode}
              type="button"
              onClick={() => setDocMode(mode)}
              style={{
                border: 0,
                borderRight: mode === 'view' ? '1px solid var(--line)' : 0,
                background: docMode === mode ? 'var(--accent)' : 'var(--bg)',
                color: docMode === mode ? 'var(--bg)' : 'var(--fg-mute)',
                fontFamily: 'var(--mono)',
                fontSize: 10,
                fontWeight: 800,
                padding: '4px 8px',
                cursor: 'pointer',
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <button type="button" className="btn" onClick={() => { window.location.href = downloadUrl; }} style={{ fontSize: 10 }}>
          download
        </button>
        <button type="button" className="btn" onClick={onBack} style={{ fontSize: 10 }}>
          chat
        </button>
      </div>
      <div style={{
        flex: 1,
        minHeight: 0,
        padding: 12,
        background: 'var(--bg)',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}>
        {docMode === 'feedback' ? (
          <form
            onSubmit={event => {
              event.preventDefault();
              void handleCommentToChat();
            }}
            style={{
              border: '1px solid var(--line)',
              background: 'var(--bg-2)',
              padding: 10,
              display: 'grid',
              gap: 8,
              fontFamily: 'var(--mono)',
              fontSize: 'var(--ui-control-font-size)',
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(120px, 0.7fr) minmax(160px, 1fr) auto auto', gap: 8, alignItems: 'center' }}>
              <select
                value={feedbackSection}
                onChange={e => setFeedbackSection(e.target.value)}
                disabled={!!selectedTarget}
                style={{
                  background: 'var(--bg)',
                  color: 'var(--fg)',
                  border: '1px solid var(--line)',
                  borderRadius: 2,
                  fontFamily: 'var(--mono)',
                  fontSize: 'var(--ui-control-font-size)',
                  padding: '5px 7px',
                }}
              >
                {docSections.map(section => (
                  <option key={section} value={section}>{SSOT_SECTION_LABELS[section] || ssotTitleFor(section)}</option>
                ))}
              </select>
              <input
                value={feedbackPath}
                onChange={e => setFeedbackPath(e.target.value)}
                readOnly={!!selectedTarget}
                placeholder="yaml path or custom field"
                style={{
                  background: 'var(--bg)',
                  color: 'var(--fg)',
                  border: '1px solid var(--line)',
                  borderRadius: 2,
                  fontFamily: 'var(--mono)',
                  fontSize: 'var(--ui-control-font-size)',
                  padding: '5px 7px',
                }}
              />
              <button
                type="button"
                className="btn"
                disabled={!selectedTarget || sourceBusy}
                onClick={handleShowSsotSource}
                style={{ fontSize: 10 }}
              >
                {sourceBusy ? 'Loading' : 'Show SSOT'}
              </button>
              <button
                type="submit"
                className="btn"
                disabled={!canSendFeedback}
                draggable={docMode === 'feedback'}
                onDragStart={handleDocCommentDragStart}
                style={{ fontSize: 10, cursor: docMode === 'feedback' && selectedTarget ? 'grab' : 'default' }}
              >
                {feedbackBusy ? 'Sending' : 'Send to chat'}
              </button>
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1fr) auto',
              gap: 8,
              alignItems: 'center',
              border: '1px solid var(--line)',
              background: 'var(--bg)',
              padding: '6px 8px',
            }}>
              <span className="mute" style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {selectedTarget
                  ? `${selectedTarget.kind} · ${selectedTarget.label} · ${selectedTarget.path}`
                  : 'Select a DOC component by clicking it, then send feedback to chat.'}
              </span>
              {selectedTarget ? (
                <button
                  type="button"
                  className="btn"
                  onClick={() => {
                    const frameDoc = docFrameRef.current?.contentDocument;
                    if (frameDoc) clearSsotDocSelection(frameDoc);
                    setSelectedTarget(null);
                    setSourceInfo(null);
                    setSourceOpen(false);
                    setFeedbackPath('');
                    setFeedbackStatus('');
                  }}
                  style={{ fontSize: 10 }}
                >
                  clear
                </button>
              ) : null}
            </div>
            {sourceOpen && selectedSourceInfo ? (
              <div style={{
                border: '1px solid var(--line)',
                background: 'var(--bg)',
                padding: 8,
                display: 'grid',
                gap: 6,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                  <strong style={{ color: 'var(--fg)' }}>{selectedSourceInfo.label}</strong>
                  <span className="mute">{selectedSourceInfo.kind}</span>
                </div>
                <div className="mute" style={{ overflowWrap: 'anywhere' }}>
                  @{selectedSourceInfo.ssot_path} · {selectedSourceInfo.path}
                </div>
                <pre style={{
                  margin: 0,
                  maxHeight: 140,
                  overflow: 'auto',
                  background: 'var(--bg-2)',
                  border: '1px solid var(--line)',
                  padding: 8,
                  color: 'var(--fg)',
                  whiteSpace: 'pre-wrap',
                }}>{selectedSourceInfo.yaml || '(empty)'}</pre>
                {selectedSourceInfo.feedback.length ? (
                  <div className="mute">{selectedSourceInfo.feedback.length} existing DOC feedback item(s)</div>
                ) : null}
              </div>
            ) : null}
            <textarea
              value={feedbackComment}
              onChange={e => setFeedbackComment(e.target.value)}
              placeholder="chat feedback note (optional)"
              rows={2}
              style={{
                background: 'var(--bg)',
                color: 'var(--fg)',
                border: '1px solid var(--line)',
                borderRadius: 2,
                fontFamily: 'var(--mono)',
                fontSize: 'var(--ui-control-font-size)',
                padding: '7px 8px',
                resize: 'vertical',
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
              <span className="mute" style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {feedbackStatus || ' '}
              </span>
            </div>
          </form>
        ) : null}
        <iframe
          ref={docFrameRef}
          key={inlineUrl}
          title={`${effectiveIp} SSOT HTML export`}
          data-testid="ssot-doc-frame"
          src={inlineUrl}
          onLoad={() => setDocFrameReady(v => v + 1)}
          style={{
            width: '100%',
            flex: 1,
            minHeight: 0,
            border: '1px solid var(--line)',
            background: '#fff',
          }}
        />
      </div>
    </div>
  );
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// workspace.jsx aliases this back via `const SsotDocPane = window.SsotDocPane;`.
// `SsotDocPane` is not (yet) declared on the ambient Window in
// types/atlas-window.d.ts, so cast to attach the global without changing
// runtime behavior (the .d.ts entry is added when consumers migrate).
(window as unknown as { SsotDocPane: typeof SsotDocPane }).SsotDocPane = SsotDocPane;
