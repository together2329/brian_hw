// workflow-report.jsx — Phase 13b refactor: WorkflowReportPane extracted.
// Reads window.WORKFLOW_REPORT_TABS (workspace.jsx exposes it after its def).

window.WorkflowReportPane = ({ workflow, activeIp }) => {
  const WORKFLOW_REPORT_TABS = window.WORKFLOW_REPORT_TABS || {};
  const meta = WORKFLOW_REPORT_TABS[workflow] || null;
  const inferredIp = React.useMemo(() => {
    const direct = String(activeIp || '').trim();
    if (direct && direct !== 'default') return direct;
    const ns = String(window.ACTIVE_SESSION || '').replace(/^\/+|\/+$/g, '');
    const parts = ns.split('/').filter(Boolean);
    if (parts.length >= 3 && parts[parts.length - 1] === workflow) {
      const candidate = parts[parts.length - 2] || '';
      if (candidate && candidate !== 'default') return candidate;
    }
    const scope = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
    const leaf = scope.split('/').filter(Boolean).pop() || '';
    if (leaf && leaf !== 'default' && leaf !== workflow) return leaf;
    return '';
  }, [activeIp, workflow]);
  const ip = String(inferredIp || '').trim();
  const [dataTick, setDataTick] = React.useState(0);
  const [selected, setSelected] = React.useState('');
  const [focusLine, setFocusLine] = React.useState(0);

  React.useEffect(() => {
    const handler = (ev) => {
      const detail = ev && ev.detail;
      if (detail === 'FILE_TREE' || detail === 'SCOPE_PATH') setDataTick(v => v + 1);
    };
    window.addEventListener('atlas-data-changed', handler);
    return () => window.removeEventListener('atlas-data-changed', handler);
  }, []);

  React.useEffect(() => {
    if (!window.atlasData?.refreshFileTree) return;
    if (!ip) return;
    try {
      window.atlasData.refreshFileTree(ip, { recursive: true });
    } catch (_) {}
  }, [workflow, ip]);

  const paths = React.useMemo(() => {
    if (!meta || !ip) return [];
    const candidatePaths = (meta.paths ? meta.paths(ip) : []).filter(Boolean);
    const scope = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
    const folderPrefixes = (meta.folders || []).map(f => `${ip}/${f.replace(/^\/+|\/+$/g, '')}/`);
    const related = (window.FILE_TREE || [])
      .filter(n => n && n.type === 'file')
      .map(n => {
        const relName = String(n.name || '').replace(/^\/+|\/+$/g, '');
        return (scope ? `${scope}/` : '') + relName;
      })
      .filter(p => folderPrefixes.some(prefix => p.startsWith(prefix)))
      .sort((a, b) => a.localeCompare(b));
    return Array.from(new Set([...candidatePaths, ...related]));
  }, [meta, ip, dataTick]);

  const pathsKey = paths.join('\n');
  React.useEffect(() => {
    if (!paths.length) {
      setSelected('');
      return;
    }
    setSelected(current => (current && paths.includes(current)) ? current : paths[0]);
  }, [pathsKey]);

  const openLintDiagnostic = React.useCallback((diag) => {
    const diagPath = String(diag?.path || diag?.file || '').replace(/^\/+/, '');
    const line = Number(diag?.line || 0);
    if (!diagPath) return;
    setSelected(diagPath);
    setFocusLine(line || 0);
    readAtlasAsyncResource('file', diagPath, true).catch(() => {});
  }, []);

  if (workflow === 'orchestrator') {
    return <OrchestratorWorkflowPane activeIp={activeIp} />;
  }

  if (!meta) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
        No report surface for this workflow.
      </div>
    );
  }

  if (!ip) {
    return (
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12,
      }}>
        Select IP_ID to load {meta.title}.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'grid', gridTemplateColumns: '300px minmax(0, 1fr)', overflow: 'hidden' }}>
      <div style={{
        minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column',
        borderRight: '1px solid var(--line)', background: 'var(--panel)',
      }}>
        <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--line)' }}>
          <div style={{ fontWeight: 800, fontSize: 12, letterSpacing: '0.06em', textTransform: 'uppercase' }}>{meta.title}</div>
          <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, marginTop: 3 }}>{ip} · {paths.length} artifact(s)</div>
        </div>
        <div style={{ padding: 8, borderBottom: '1px solid var(--line)', display: 'flex', gap: 6 }}>
          <button
            className="btn"
            onClick={() => {
              try { window.atlasData?.refreshFileTree?.(ip || window.SCOPE_PATH || '', { recursive: true }); } catch (_) {}
              if (selected) readAtlasAsyncResource('file', selected, true).catch(() => {});
            }}
            style={{ padding: '2px 8px', fontSize: 10 }}
          >refresh</button>
          <span style={{ flex: 1 }} />
          <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, alignSelf: 'center' }}>{workflow}</span>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '6px 0' }}>
          {paths.map((p, i) => {
            const active = selected === p;
            const name = p.split('/').slice(1).join('/') || p;
            return (
              <div
                key={p}
                onClick={() => setSelected(p)}
                onMouseEnter={() => readAtlasAsyncResource('file', p).catch(() => {})}
                title={p}
                style={{
                  display: 'grid', gridTemplateColumns: '22px minmax(0, 1fr)',
                  gap: 6, padding: '5px 10px', cursor: 'pointer',
                  background: active ? 'var(--select)' : 'transparent',
                  color: active ? 'var(--accent)' : 'var(--fg)',
                  borderLeft: '2px solid ' + (active ? 'var(--accent)' : 'transparent'),
                  fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)',
                }}
              >
                <span style={{ color: 'var(--fg-mute)' }}>{i + 1}</span>
                <span className="trunc">{name}</span>
              </div>
            );
          })}
          {!paths.length && (
            <div style={{ padding: 12, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
              No known report artifacts under {ip}.
            </div>
          )}
        </div>
      </div>
      <div style={{ minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        {workflow === 'lint' && (
          <LintReportSummary ip={ip} onSelectPath={setSelected} onOpenDiagnostic={openLintDiagnostic} />
        )}
        {workflow === 'coverage' && (
          <CoverageReportSummary ip={ip} onSelectPath={setSelected} onOpenDiagnostic={openLintDiagnostic} />
        )}
        <PreviewPane path={selected} onClose={() => {}} focusLine={focusLine} />
      </div>
    </div>
  );
};
