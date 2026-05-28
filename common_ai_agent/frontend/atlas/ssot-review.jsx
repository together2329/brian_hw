// ssot-review.jsx — Phase 21 refactor: SsotReviewPane extracted from
// ssot-digest.jsx (was 1645L, just over the 1000-line target).
// SsotReviewPane wraps SsotDigestContent + chooses SSOT file + manages
// review state. Same IIFE + lambda forward-ref pattern.
//
// Load order (index.html): after ssot-digest.jsx (which exposes
// SsotDigestContent + status helpers). All deps are forward-ref lambdas
// since they're called at render time.

(() => {

const AtlasStatusBadge = (...a) => window.AtlasStatusBadge(...a);
const SsotDigestContent = (...a) => window.SsotDigestContent(...a);
const chooseSsotFile = (...a) => window.chooseSsotFile(...a);
const digestViewsForSections = (...a) => window.digestViewsForSections(...a);
const isSsotYamlPath = (...a) => window.isSsotYamlPath(...a);
const sourceSectionsForDigestView = (...a) => window.sourceSectionsForDigestView(...a);
const splitSsotSections = (...a) => window.splitSsotSections(...a);
const ssotNeedsAttentionStatus = (...a) => window.ssotNeedsAttentionStatus(...a);
const ssotPathOf = (...a) => window.ssotPathOf(...a);
const ssotProgressStatusMap = (...a) => window.ssotProgressStatusMap(...a);
const ssotSectionStatus = (...a) => window.ssotSectionStatus(...a);
const ssotStatusColor = (...a) => window.ssotStatusColor(...a);
const ssotStatusGlyph = (...a) => window.ssotStatusGlyph(...a);
const ssotStatusKey = (...a) => window.ssotStatusKey(...a);
const useAtlasAsyncResource = (...a) => window.useAtlasAsyncResource(...a);
const compactDigestItems = (...a) => window.compactDigestItems(...a);


const SsotReviewPane = ({ uiLang = 'ko', initialPath = '', onBack }) => {
  const files = Array.isArray(window.SSOT_FILES) ? window.SSOT_FILES : [];
  const [selected, setSelected] = React.useState('');
  const [activeKey, setActiveKey] = React.useState('');
  const [ssotPreviewMode, setSsotPreviewMode] = React.useState('view');
  const lastInitialPath = React.useRef('');
  const importDocRef = React.useRef(null);
  const [importDocBusy, setImportDocBusy] = React.useState(false);
  const [importDocStatus, setImportDocStatus] = React.useState('');
  const [importedFiles, setImportedFiles] = React.useState([]);
  const [exportFormat, setExportFormat] = React.useState('');

  const handleImportDocFiles = async (fileList) => {
    const fileArr = Array.from(fileList || []);
    if (!fileArr.length) return;
    const ip = (String(window.ACTIVE_IP || '').trim()) ||
      (() => {
        const parts = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
        return parts.length >= 2 ? parts[1] : parts[0] || '';
      })();
    setImportDocBusy(true);
    setImportDocStatus('');
    try {
      const payloadFiles = await Promise.all(fileArr.map(file => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const raw = String(reader.result || '');
          resolve({ name: file.name, content_b64: raw.includes(',') ? raw.split(',').pop() : raw });
        };
        reader.onerror = () => reject(reader.error || new Error('read failed'));
        reader.readAsDataURL(file);
      })));
      const res = await fetch('/api/ssot/import/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, session: String(window.ACTIVE_SESSION || ''), files: payloadFiles }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok || !payload?.ok) throw new Error(payload?.error || `upload failed (${res.status})`);
      const count = (payload.paths || []).length;
      if (payload.command && window.backend && typeof window.backend.send === 'function') {
        window.backend.send({
          type: 'prompt',
          msg_id: `ssot-import-${Date.now()}-${Math.random().toString(16).slice(2)}`,
          text: payload.command,
          session: String(window.ACTIVE_SESSION || ''),
          ui_lang: window.ATLAS_UI_LANG || uiLang,
        });
      }
      setImportDocStatus(uiLang === 'en'
        ? `${count} file(s) imported. /import started for ${ip}.`
        : `${count}개 파일 임포트 완료. ${ip} /import를 실행했습니다.`);
      const saved = Array.isArray(payload.saved) ? payload.saved : [];
      if (saved.length) {
        setImportedFiles(prev => {
          const next = saved.map(s => ({
            name: s.name || '',
            bytes: s.bytes || 0,
            md_path: s.md_path || '',
            original_path: s.original_path || '',
            image_count: Array.isArray(s.image_paths) ? s.image_paths.length : 0,
            ts: Date.now(),
          }));
          return [...next, ...prev].slice(0, 20);
        });
      }
    } catch (err) {
      setImportDocStatus(String(err?.message || err || 'upload failed'));
    } finally {
      setImportDocBusy(false);
      if (importDocRef.current) importDocRef.current.value = '';
    }
  };

  const t = uiLang === 'en'
    ? {
        title: 'SSOT Design Preview',
        subtitle: 'Human-readable IP digest from SSOT sections.',
        file: 'file',
        empty: 'No *.ssot.yaml files in this project yet.',
        sections: 'views',
        flags: 'flags',
        approved: 'approved',
        raw: 'Raw YAML section',
        reload: 'refresh',
        importDoc: '📄 Import Doc',
        importing: 'importing…',
      }
    : {
        title: 'SSOT 설계 프리뷰',
        subtitle: 'SSOT 섹션을 사람이 읽는 IP digest로 보여줍니다.',
        file: '파일',
        empty: '아직 프로젝트에 *.ssot.yaml 파일이 없습니다.',
        sections: '뷰',
        flags: '리뷰 플래그',
        approved: '승인',
        raw: '원본 YAML 섹션',
        reload: '새로고침',
        importDoc: '📄 Import Doc',
        importing: '임포트 중…',
      };

  const ssotFilePaths = files.map(ssotPathOf).filter(Boolean);
  const filePaths = initialPath && isSsotYamlPath(initialPath) && !ssotFilePaths.includes(initialPath)
    ? [initialPath, ...ssotFilePaths]
    : ssotFilePaths;
  const filePathKey = filePaths.map(path => {
    const meta = files.find(f => ssotPathOf(f) === path) || {};
    return `${path}@${meta.mtime || 0}:${meta.size || 0}`;
  }).join('|');
  const [ssotResource, reloadSsot] = useAtlasAsyncResource('ssot', selected, {
    versionKey: filePathKey,
    forceOnVersionChange: true,
  });
  const content = selected ? (ssotResource.body || '') : '';
  const loading = !!selected && !!ssotResource.loading;
  const ssotHasContent = !!content.trim();
  const showLoading = loading && !content.trim();

  // Auto-reload the SSOT view when the backend writes to the
  // currently-selected yaml. Matches by path suffix so both relative
  // (selected = "spi/yaml/spi.ssot.yaml") and absolute (event path =
  // /full/path/.../spi.ssot.yaml) hits resolve.
  React.useEffect(() => {
    if (!selected) return undefined;
    const handler = (ev) => {
      const changed = (ev && ev.detail && ev.detail.path) || '';
      if (!changed) return;
      if (changed === selected
          || changed.endsWith('/' + selected)
          || selected.endsWith('/' + changed)) {
        reloadSsot(true);
      }
    };
    window.addEventListener('atlas-file-changed', handler);
    return () => window.removeEventListener('atlas-file-changed', handler);
  }, [selected, reloadSsot]);

  React.useEffect(() => {
    if (initialPath && initialPath !== lastInitialPath.current && filePaths.includes(initialPath)) {
      lastInitialPath.current = initialPath;
      setSelected(initialPath);
    }
  }, [initialPath, filePathKey]);

  React.useEffect(() => {
    if (!filePaths.length) {
      if (selected) setSelected('');
      return;
    }
    if (!selected || !filePaths.includes(selected)) {
      setSelected(chooseSsotFile(files, initialPath));
    }
  }, [filePathKey, selected, initialPath]);

  const sections = React.useMemo(() => splitSsotSections(content), [content]);
  const statusByKey = React.useMemo(() => ssotProgressStatusMap(), [content, filePathKey]);
  const digestViews = React.useMemo(() => digestViewsForSections(sections), [sections]);
  const digestViewKey = digestViews.map(v => v.id).join('|');

  React.useEffect(() => {
    if (!digestViews.length) {
      setActiveKey('');
      return;
    }
    if (!activeKey || !digestViews.some(v => v.id === activeKey)) setActiveKey(digestViews[0].id);
  }, [digestViewKey, activeKey]);

  const activeView = digestViews.find(v => v.id === activeKey) || digestViews[0] || null;
  const approvedCount = sections.filter(s => ssotSectionStatus(s, statusByKey) === 'approved').length;
  const flagCount = sections.reduce((sum, s) => sum + ((s.summary && s.summary.gaps.length) || 0), 0);

  if (!filePaths.length) {
    return (
      <div style={{ flex: 1, minHeight: 0, padding: '16px 18px', overflow: 'auto' }}>
        <input
          ref={importDocRef}
          type="file"
          multiple
          accept=".pdf,.pptx,.docx,.html,.htm,.md,.txt,.rst,.yaml,.yml,.json,.sv,.svh,.v,.vh,.py,.csv,.tsv,.xml,.f,.sdc,.tcl,.rpt,.log,.h,.c,.cpp,.png,.jpg,.jpeg,.gif,.webp,.bmp,.svg,.tif,.tiff"
          style={{ display: 'none' }}
          onChange={e => {
            const files = Array.from(e.target.files || []);
            e.target.value = '';
            handleImportDocFiles(files);
          }}
        />
        <div className="code" style={{ padding: 16, color: 'var(--fg-mute)' }}>
          # {t.empty}<br />
          # /grill-me → /to-ssot writes the review source.
        </div>
        <div style={{ marginTop: 10, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn"
            disabled={importDocBusy}
            onClick={() => importDocRef.current?.click()}
            title="Upload requirement docs, notes, RTL, YAML, or logs into SSOT import evidence"
            style={{ fontSize: 10 }}
          >{importDocBusy ? t.importing : t.importDoc}</button>
          <span className="mute" style={{ fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)' }}>
            Uploaded files are saved under req/imports.
          </span>
        </div>

        {importDocStatus ? (() => {
          const failed = importDocStatus.toLowerCase().includes('fail');
          const importing = importDocStatus.toLowerCase().includes('importing') || importDocStatus.toLowerCase().includes('임포트 중');
          const color = failed ? 'var(--err)' : importing ? 'var(--warn)' : 'var(--ok)';
          const icon = failed ? '✕' : importing ? '⟳' : '✓';
          return (
            <div style={{
              padding: '8px 14px',
              fontSize: 'var(--ui-control-font-size)',
              color, background: `color-mix(in oklch, ${color} 12%, transparent)`,
              border: `1px solid ${color}`, borderRadius: 2,
              marginTop: 10,
              fontWeight: 600, letterSpacing: '0.02em',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span style={{ fontSize: 14 }}>{icon}</span>
              <span style={{ flex: 1 }}>{importDocStatus}</span>
              <button type="button"
                onClick={() => setImportDocStatus('')}
                style={{
                  background: 'transparent', border: 'none', color, cursor: 'pointer',
                  fontSize: 13, fontWeight: 700, padding: '0 4px',
                }}
                title="dismiss"
              >×</button>
            </div>
          );
        })() : null}

        {importedFiles.length > 0 ? (
          <div style={{
            marginTop: 10, padding: '8px 10px',
            border: '1px solid var(--line)', borderRadius: 2,
            background: 'var(--bg-1)',
            fontSize: 'var(--ui-control-font-size)',
            fontFamily: 'var(--mono)',
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              marginBottom: 6, fontWeight: 700, color: 'var(--fg-mute)',
              letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
            }}>
              <span>📥 Imported · {importedFiles.length}</span>
              <button type="button" onClick={() => setImportedFiles([])}
                style={{
                  background: 'transparent', border: '1px solid var(--line)',
                  color: 'var(--fg-mute)', cursor: 'pointer',
                  fontSize: 10, padding: '1px 6px', borderRadius: 2,
                }}>clear</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {importedFiles.map((f, i) => (
                <div key={i} style={{
                  display: 'grid', gridTemplateColumns: '14px minmax(0, 1fr) auto',
                  gap: 8, alignItems: 'center',
                  padding: '4px 6px', background: 'var(--bg-2)',
                  borderRadius: 2, color: 'var(--fg)',
                }}>
                  <span style={{ color: 'var(--ok)', fontWeight: 700 }}>✓</span>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={f.name}>{f.name}</div>
                    {f.md_path || f.original_path ? (
                      <div className="mute" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 10 }} title={f.md_path || f.original_path}>
                        {f.md_path || f.original_path}
                      </div>
                    ) : null}
                  </div>
                  <span className="mute" style={{ fontSize: 10 }}>
                    {f.bytes ? (f.bytes < 1024 ? `${f.bytes}B` : `${(f.bytes/1024).toFixed(1)}K`) : ''}
                    {f.image_count ? ` · ${f.image_count} img` : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div style={{
      flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
      overflow: 'hidden', background: 'var(--bg)',
    }}>
      <div style={{
        padding: '10px 14px', borderBottom: '1px solid var(--line)',
        display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) auto',
        gap: 12, alignItems: 'center', background: 'var(--bg-2)',
      }}>
        <div style={{ minWidth: 0 }}>
          <div style={{
            color: 'var(--magenta)', fontWeight: 800, fontSize: 12,
            letterSpacing: '0.08em', textTransform: 'uppercase',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>{t.title}</div>
          <div className="mute trunc" style={{ marginTop: 3, fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)' }}>
            {selected || t.file} · {loading ? (ssotHasContent ? 'refreshing' : 'loading') : `${sections.length} ${t.sections}`} · {approvedCount} {t.approved} · {flagCount} {t.flags}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', minWidth: 0 }}>
          {loading ? <AtlasStatusBadge status={ssotHasContent ? 'refreshing' : 'loading'} compact /> : null}
          <select
            value={selected}
            onChange={e => setSelected(e.target.value)}
            style={{
              maxWidth: 340, minWidth: 180, background: 'var(--bg)', color: 'var(--fg)',
              border: '1px solid var(--line)', borderRadius: 2,
              fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)', padding: '4px 6px',
            }}
          >
            {filePaths.map(path => <option key={path} value={path}>{path}</option>)}
          </select>
          <button
            type="button"
            className="btn"
            onClick={() => reloadSsot(true)}
            style={{ fontSize: 10 }}
          >{t.reload}</button>
          <div style={{ display: 'inline-flex', border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
            {[
              ['view', 'View Mode'],
              ['feedback', 'Feedback Mode'],
            ].map(([mode, label]) => (
              <button
                key={mode}
                type="button"
                onClick={() => setSsotPreviewMode(mode)}
                style={{
                  border: 0,
                  borderRight: mode === 'view' ? '1px solid var(--line)' : 0,
                  background: ssotPreviewMode === mode ? 'var(--accent)' : 'var(--bg)',
                  color: ssotPreviewMode === mode ? 'var(--bg)' : 'var(--fg-mute)',
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
          <input
            ref={importDocRef}
            type="file"
            multiple
            accept=".pdf,.pptx,.docx,.html,.htm,.md,.txt,.rst,.yaml,.yml,.json,.sv,.svh,.v,.vh,.py,.csv,.tsv,.xml,.f,.sdc,.tcl,.rpt,.log,.h,.c,.cpp,.png,.jpg,.jpeg,.gif,.webp,.bmp,.svg,.tif,.tiff"
            style={{ display: 'none' }}
            onChange={e => {
              const files = Array.from(e.target.files || []);
              e.target.value = '';
              handleImportDocFiles(files);
            }}
          />
          <button
            type="button"
            className="btn"
            disabled={importDocBusy}
            onClick={() => importDocRef.current?.click()}
            title="Upload requirement docs, notes, RTL, YAML, or logs into SSOT import evidence"
            style={{ fontSize: 10 }}
          >{importDocBusy ? t.importing : t.importDoc}</button>
          <select
            value={exportFormat}
            onChange={e => {
              const fmt = e.target.value;
              if (!fmt) return;
              const ip = (String(window.ACTIVE_IP || '').trim()) ||
                (() => {
                  const parts = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
                  return parts.length >= 2 ? parts[1] : parts[0] || '';
                })();
              if (!ip) {
                setExportFormat('');
                return;
              }
              const url = `/api/ssot/export?ip=${encodeURIComponent(ip)}&format=${encodeURIComponent(fmt)}`;
              window.location.href = url;
              setExportFormat('');
            }}
            title="Download the canonical ssot yaml as Markdown, Word, or HTML"
            style={{
              background: 'var(--bg)', color: 'var(--fg)',
              border: '1px solid var(--line)', borderRadius: 2,
              fontFamily: 'var(--mono)', fontSize: 10, padding: '4px 6px',
              minWidth: 100,
            }}
          >
            <option value="">📥 Export</option>
            <option value="md">Markdown (.md)</option>
            <option value="docx">Word (.docx)</option>
            <option value="html">HTML (.html)</option>
          </select>
          <button type="button" className="btn" onClick={onBack} style={{ fontSize: 10 }}>chat</button>
        </div>
      </div>

      {importDocStatus ? (() => {
        const failed = importDocStatus.toLowerCase().includes('fail');
        const importing = importDocStatus.toLowerCase().includes('importing') || importDocStatus.toLowerCase().includes('임포트 중');
        const color = failed ? 'var(--err)' : importing ? 'var(--warn)' : 'var(--ok)';
        const icon = failed ? '✕' : importing ? '⟳' : '✓';
        return (
          <div style={{
            padding: '8px 14px',
            fontSize: 'var(--ui-control-font-size)',
            color, background: `color-mix(in oklch, ${color} 12%, transparent)`,
            border: `1px solid ${color}`, borderRadius: 2,
            margin: '6px 14px',
            fontWeight: 600, letterSpacing: '0.02em',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span style={{ fontSize: 14 }}>{icon}</span>
            <span style={{ flex: 1 }}>{importDocStatus}</span>
            <button type="button"
              onClick={() => setImportDocStatus('')}
              style={{
                background: 'transparent', border: 'none', color, cursor: 'pointer',
                fontSize: 13, fontWeight: 700, padding: '0 4px',
              }}
              title="dismiss"
            >×</button>
          </div>
        );
      })() : null}

      {importedFiles.length > 0 ? (
        <div style={{
          margin: '0 14px 6px 14px', padding: '8px 10px',
          border: '1px solid var(--line)', borderRadius: 2,
          background: 'var(--bg-1)',
          fontSize: 'var(--ui-control-font-size)',
          fontFamily: 'var(--mono)',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            marginBottom: 6, fontWeight: 700, color: 'var(--fg-mute)',
            letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
          }}>
            <span>📥 Imported · {importedFiles.length}</span>
            <button type="button" onClick={() => setImportedFiles([])}
              style={{
                background: 'transparent', border: '1px solid var(--line)',
                color: 'var(--fg-mute)', cursor: 'pointer',
                fontSize: 10, padding: '1px 6px', borderRadius: 2,
              }}>clear</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {importedFiles.map((f, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '4px 6px', background: 'var(--bg-2)',
                borderRadius: 2, color: 'var(--fg)',
              }}>
                <span style={{ color: 'var(--ok)', fontWeight: 700 }}>✓</span>
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={f.name}>{f.name}</span>
                <span className="mute" style={{ fontSize: 10 }}>
                  {f.bytes ? (f.bytes < 1024 ? `${f.bytes}B` : `${(f.bytes/1024).toFixed(1)}K`) : ''}
                  {f.image_count ? ` · ${f.image_count} img` : ''}
                </span>
                {f.md_path ? (
                  <button type="button"
                    onClick={() => setSelected(f.md_path)}
                    style={{
                      background: 'transparent', border: '1px solid var(--accent)',
                      color: 'var(--accent)', cursor: 'pointer',
                      fontSize: 10, padding: '1px 6px', borderRadius: 2,
                    }}
                    title={f.md_path}>open</button>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div style={{
        flex: 1, minHeight: 0, display: 'grid',
        gridTemplateColumns: 'minmax(190px, 240px) minmax(0, 1fr)',
        overflow: 'hidden',
      }}>
        <div style={{
          minHeight: 0, overflow: 'auto', borderRight: '1px solid var(--line)',
          background: 'color-mix(in oklch, var(--bg-2) 72%, transparent)',
          padding: '10px 8px',
        }}>
          {digestViews.map((view, idx) => {
            const sourceSections = sourceSectionsForDigestView(view, sections);
            const gaps = sourceSections.reduce((sum, section) => sum + ((section.summary && section.summary.gaps.length) || 0), 0);
            const statuses = sourceSections.map(section => ssotSectionStatus(section, statusByKey));
            const approved = sourceSections.length > 0 && statuses.every(status => ssotStatusKey(status) === 'approved');
            const needsAttention = gaps > 0 || statuses.some(ssotNeedsAttentionStatus);
            const status = needsAttention ? 'needs_review' : approved ? 'approved' : 'review';
            const activeRow = activeView && activeView.id === view.id;
            const color = ssotStatusColor(status);
            const sourceLabel = sourceSections.length
              ? compactDigestItems(sourceSections.map(section => section.key), 4)
              : (view.keys.join(' + ') || 'all sections');
            return (
              <button
                key={view.id + ':' + idx}
                type="button"
                onClick={() => setActiveKey(view.id)}
                title={`${sourceLabel} · ${status}`}
                style={{
                  width: '100%', textAlign: 'left', display: 'grid',
                  gridTemplateColumns: '22px minmax(0, 1fr) auto',
                  gap: 8, alignItems: 'center',
                  background: activeRow
                    ? (view.id === 'raw_yaml' ? 'var(--bg-3)' : 'color-mix(in oklch, var(--magenta) 14%, transparent)')
                    : 'transparent',
                  color: activeRow ? 'var(--fg)' : 'var(--fg-mute)',
                  border: '1px solid ' + (activeRow ? (view.id === 'raw_yaml' ? 'var(--line-2)' : 'var(--magenta)') : 'transparent'),
                  borderRadius: 3, padding: '6px 7px', marginBottom: 4,
                  cursor: 'pointer', fontFamily: 'var(--mono)',
                }}
              >
                <span style={{ color, fontSize: 12, textAlign: 'center' }}>
                  {ssotStatusGlyph(status)}
                </span>
                <span style={{ minWidth: 0 }}>
                  <span className="trunc" style={{ display: 'block', fontSize: 12, fontWeight: activeRow ? 800 : 600 }}>
                    {view.label}
                  </span>
                  <span className="trunc" style={{ display: 'block', fontSize: 10, color: 'var(--fg-mute)' }}>
                    {sourceLabel}
                  </span>
                </span>
                <span style={{
                  color, fontSize: 10, border: `1px solid ${color}`,
                  borderRadius: 2, padding: '0 4px', whiteSpace: 'nowrap',
                }}>
                  {gaps || sourceSections.length}
                </span>
              </button>
            );
          })}
        </div>

        <div style={{ minHeight: 0, overflow: 'auto', padding: '14px 18px' }}>
          {ssotResource.err ? (
            <div style={{
              marginBottom: 10, padding: '6px 10px',
              border: '1px solid var(--err)',
              background: 'color-mix(in oklch, var(--err) 12%, transparent)',
              color: 'var(--err)', fontFamily: 'var(--mono)', fontSize: 10,
            }}>
              ssot load error: {ssotResource.err}
            </div>
          ) : null}
          {showLoading ? (
            <div className="code" style={{ padding: 16, color: 'var(--fg-mute)' }}># loading SSOT...</div>
          ) : activeView ? (
            <SsotDigestContent
              view={activeView}
              sections={sections}
              statusByKey={statusByKey}
              uiLang={uiLang}
              content={content}
              selected={selected}
              feedbackMode={ssotPreviewMode === 'feedback'}
              onJump={(viewId) => setActiveKey(viewId)}
            />
          ) : (
            <div className="code" style={{ padding: 16, color: 'var(--fg-mute)' }}># no sections parsed</div>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Right panels ──────────────────────────────────────────────────
// Live SSOT panel — lists every *.ssot.yaml under the project (or the
// current scope path, if /api/ssot ever filters by it) and shows the
// content of whichever one the user clicks on. Auto-refreshes when the

window.SsotReviewPane = SsotReviewPane;

})();
