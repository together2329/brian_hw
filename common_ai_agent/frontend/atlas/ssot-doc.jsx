// ssot-doc.jsx — Phase 13a refactor: SsotDocPane extracted from workspace.jsx.
//
// The component reads three workspace.jsx-scope helpers
// (SSOT_SECTION_LABELS, ssotIpFromSession, ssotTitleFor) via window globals
// that workspace.jsx exposes after their definitions. ssot-doc.jsx loads
// BEFORE workspace.jsx in index.html so workspace.jsx's
// `const SsotDocPane = window.SsotDocPane;` alias finds the export. The
// helper lookups happen inside the body at RENDER time, by which point
// workspace.jsx has set window.<helper>.

window.SsotDocPane = ({ uiLang = 'ko', ip = '', onBack }) => {
  // Late-bound helper lookups (workspace.jsx assigns these globals).
  const SSOT_SECTION_LABELS = window.SSOT_SECTION_LABELS || {};
  const ssotIpFromSession = window.ssotIpFromSession || ((s) => '');
  const ssotTitleFor = window.ssotTitleFor || ((k) => k);
  const [reloadKey, setReloadKey] = React.useState(0);
  const [docMode, setDocMode] = React.useState('view');
  const [feedbackSection, setFeedbackSection] = React.useState('custom');
  const [feedbackPath, setFeedbackPath] = React.useState('');
  const [feedbackField, setFeedbackField] = React.useState('');
  const [feedbackValue, setFeedbackValue] = React.useState('');
  const [feedbackComment, setFeedbackComment] = React.useState('');
  const [feedbackBusy, setFeedbackBusy] = React.useState(false);
  const [feedbackStatus, setFeedbackStatus] = React.useState('');
  const [docFrameReady, setDocFrameReady] = React.useState(0);
  const docFrameRef = React.useRef(null);
  const commentTextareaRef = React.useRef(null);
  const effectiveIp = String(ip || window.ACTIVE_IP || ssotIpFromSession(window.ACTIVE_SESSION) || '').trim();
  const qs = effectiveIp ? new URLSearchParams({
    ip: effectiveIp,
    format: 'html',
    inline: '1',
    v: String(reloadKey),
  }).toString() : '';
  const inlineUrl = qs ? `/api/ssot/export?${qs}` : '';
  const downloadUrl = effectiveIp
    ? `/api/ssot/export?ip=${encodeURIComponent(effectiveIp)}&format=html`
    : '';
  const title = uiLang === 'en' ? 'SSOT Document' : 'SSOT Document';
  const subtitle = uiLang === 'en'
    ? 'Rendered from the same HTML export artifact.'
    : 'HTML export 산출물을 탭 안에서 그대로 렌더링합니다.';
  const docSections = React.useMemo(() => {
    const preferred = ['top_module', 'io_list', 'registers', 'features', 'function_model', 'cycle_model', 'custom'];
    const seen = new Set();
    return preferred.concat(Object.keys(SSOT_SECTION_LABELS)).filter(key => {
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, []);
  const canSubmitFeedback = !!(
    feedbackComment.trim() || feedbackValue.trim() || feedbackPath.trim() || feedbackField.trim()
  );
  const sectionKeyFromDocLabel = React.useCallback((label) => {
    const norm = (value) => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
    const needle = norm(label);
    if (!needle) return 'custom';
    const matched = docSections.find(key => {
      const title = SSOT_SECTION_LABELS[key] || ssotTitleFor(key);
      return norm(title) === needle || norm(key) === needle;
    });
    return matched || 'custom';
  }, [docSections]);
  const resolveDocDropSection = React.useCallback((node) => {
    const doc = docFrameRef.current?.contentDocument;
    if (!doc || !node) return { section: 'custom', label: 'Custom' };
    let el = node.nodeType === 1 ? node : node.parentElement;
    let heading = null;
    const findPreviousH2 = (start) => {
      let cur = start;
      while (cur && cur !== doc.body) {
        let prev = cur;
        while (prev) {
          if (String(prev.tagName || '').toUpperCase() === 'H2') return prev;
          prev = prev.previousElementSibling;
        }
        cur = cur.parentElement;
      }
      return null;
    };
    heading = findPreviousH2(el);
    if (!heading && el?.closest) heading = el.closest('h2');
    const label = String(heading?.textContent || '').trim();
    const section = sectionKeyFromDocLabel(label);
    return { section, label: label || (SSOT_SECTION_LABELS[section] || ssotTitleFor(section)) };
  }, [sectionKeyFromDocLabel]);
  const applyDocDropSection = React.useCallback((target) => {
    const section = target?.section || 'custom';
    const label = target?.label || SSOT_SECTION_LABELS[section] || ssotTitleFor(section);
    setFeedbackSection(section);
    setFeedbackPath(prev => prev.trim() ? prev : `${section}.review_note`);
    setFeedbackStatus(uiLang === 'en'
      ? `drop target: ${label}`
      : `drop target: ${label}`);
    requestAnimationFrame(() => commentTextareaRef.current?.focus());
  }, [uiLang]);
  const handleDocCommentDragStart = (ev) => {
    if (docMode !== 'feedback') return;
    ev.dataTransfer.effectAllowed = 'copy';
    ev.dataTransfer.setData('text/plain', 'atlas-doc-comment');
    setFeedbackStatus(uiLang === 'en'
      ? 'drop comment on a document section'
      : 'comment를 DOC 섹션 위에 drop 하세요');
  };
  React.useEffect(() => {
    if (docMode !== 'feedback') return undefined;
    const frame = docFrameRef.current;
    if (!frame) return undefined;
    let frameDoc = null;
    try {
      frameDoc = frame.contentDocument;
    } catch (_) {
      frameDoc = null;
    }
    if (!frameDoc || !frameDoc.body) return undefined;
    const style = frameDoc.createElement('style');
    style.textContent = [
      'body.atlas-feedback-drop-mode h2 { cursor: copy; }',
      'body.atlas-feedback-drop-mode h2:hover { outline: 2px dashed #315fdc; outline-offset: 4px; }',
    ].join('\n');
    frameDoc.head.appendChild(style);
    frameDoc.body.classList.add('atlas-feedback-drop-mode');
    const onDragOver = (ev) => {
      ev.preventDefault();
      if (ev.dataTransfer) ev.dataTransfer.dropEffect = 'copy';
    };
    const onDrop = (ev) => {
      ev.preventDefault();
      applyDocDropSection(resolveDocDropSection(ev.target));
    };
    frameDoc.addEventListener('dragover', onDragOver);
    frameDoc.addEventListener('drop', onDrop);
    return () => {
      frameDoc.removeEventListener('dragover', onDragOver);
      frameDoc.removeEventListener('drop', onDrop);
      frameDoc.body?.classList.remove('atlas-feedback-drop-mode');
      try { style.remove(); } catch (_) {}
    };
  }, [docMode, docFrameReady, reloadKey, applyDocDropSection, resolveDocDropSection]);
  const handleDocFeedbackSubmit = async (ev) => {
    ev.preventDefault();
    if (!effectiveIp || !canSubmitFeedback || feedbackBusy) return;
    setFeedbackBusy(true);
    setFeedbackStatus('');
    try {
      const res = await fetch('/api/ssot/doc-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip: effectiveIp,
          mode: 'feedback',
          section: feedbackSection,
          path: feedbackPath,
          field: feedbackField,
          value: feedbackValue,
          comment: feedbackComment,
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok || !payload?.ok) throw new Error(payload?.error || `feedback failed (${res.status})`);
      setFeedbackStatus(uiLang === 'en'
        ? `applied ${payload.path || payload.section || 'feedback'}`
        : `${payload.path || payload.section || 'feedback'} 반영 완료`);
      setFeedbackComment('');
      setFeedbackValue('');
      setReloadKey(k => k + 1);
      window.dispatchEvent(new CustomEvent('atlas-ssot-doc-feedback', { detail: payload }));
    } catch (err) {
      setFeedbackStatus(String(err?.message || err || 'feedback failed'));
    } finally {
      setFeedbackBusy(false);
    }
  };

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
            onSubmit={handleDocFeedbackSubmit}
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
            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(120px, 0.7fr) minmax(160px, 1fr) auto', gap: 8, alignItems: 'center' }}>
              <select
                value={feedbackSection}
                onChange={e => setFeedbackSection(e.target.value)}
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
                onChange={e => {
                  setFeedbackPath(e.target.value);
                  setFeedbackField('');
                }}
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
                draggable={docMode === 'feedback'}
                onDragStart={handleDocCommentDragStart}
                style={{ fontSize: 10, cursor: docMode === 'feedback' ? 'grab' : 'default' }}
              >
                comment
              </button>
            </div>
            <textarea
              ref={commentTextareaRef}
              value={feedbackComment}
              onChange={e => setFeedbackComment(e.target.value)}
              placeholder="comment"
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
            <input
              value={feedbackValue}
              onChange={e => setFeedbackValue(e.target.value)}
              placeholder="value to write into the selected yaml path"
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
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
              <span className="mute" style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {feedbackStatus || ' '}
              </span>
              <button type="submit" className="btn primary" disabled={!canSubmitFeedback || feedbackBusy} style={{ fontSize: 10 }}>
                {feedbackBusy ? 'applying' : 'apply feedback'}
              </button>
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
