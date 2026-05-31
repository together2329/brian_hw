// workflow-report.tsx — TypeScript migration of workflow-report.jsx
// (Phase 13b refactor: WorkflowReportPane extracted).
// Reads window.WORKFLOW_REPORT_TABS (workspace.jsx exposes it after its def).
//
// What changed vs workflow-report.jsx:
//   - Proper ES module: `import { useState, useEffect, ... } from 'react'`
//     instead of the ambient global `React` + in-browser-babel compile.
//   - Real typed export (`WorkflowReportPane`) — consumers will `import` it
//     once they migrate.
//
// Transitional: cross-file deps still owned by unmigrated .jsx (workspace.jsx,
// preview-pane.jsx) are accessed through `window.*` and are NOT yet in the
// ambient types/atlas-window.d.ts surface, so they are reached via a minimal
// local typed view of `window`. Behavior is identical to the .jsx: these were
// bare top-level identifiers resolved through the shared in-browser-babel
// script scope; in an ES module they must be read off `window`. (PreviewPane
// is also bridged to window.PreviewPane by preview-pane.jsx; the others —
// OrchestratorWorkflowPane / LintReportSummary / CoverageReportSummary /
// readAtlasAsyncResource — will be exposed on window at the Vite cutover when
// their owner migrates.) The own public global `window.WorkflowReportPane` is
// still bridged at the bottom for not-yet-migrated .jsx consumers.
import {
  useState,
  useEffect,
  useMemo,
  useCallback,
  type ReactNode,
} from 'react';
import { PreviewPane } from './preview-pane';
import { CoverageReportSummary, LintReportSummary } from './workspace-lint-coverage';
import { lintDiagnosticLine, lintDiagnosticPath, type LintDiagnostic } from './lint-diagnostics';

// ── Minimal local typings for cross-file window globals (owners unmigrated) ──
// These shapes mirror the runtime contract in workspace.jsx / preview-pane.jsx
// exactly; nothing here changes behavior. Removed once the owners migrate and
// the globals graduate into types/atlas-window.d.ts.
interface WorkflowReportTabMeta {
  label: string;
  title: string;
  folders?: string[];
  paths?: (ip: string) => Array<string | false | null | undefined>;
}

interface FileTreeNode {
  type?: string;
  name?: string;
  [key: string]: unknown;
}

interface AtlasDataApi {
  refreshFileTree?: (scope: string, opts?: { recursive?: boolean; quiet?: boolean }) => unknown;
}

interface WorkflowReportCrossDeps {
  WORKFLOW_REPORT_TABS?: Record<string, WorkflowReportTabMeta>;
  ACTIVE_SESSION?: string;
  SCOPE_PATH?: string;
  FILE_TREE?: FileTreeNode[];
  atlasData?: AtlasDataApi;
  readAtlasAsyncResource: (kind: string, rawPath: string, force?: boolean) => Promise<unknown>;
  OrchestratorWorkflowPane: (props: { activeIp?: string }) => ReactNode;
}

const w = window as unknown as Window & WorkflowReportCrossDeps;

// Cross-file components owned by unmigrated .jsx — referenced via window.* so
// behavior is identical to the bare-identifier resolution in the .jsx world.
const OrchestratorWorkflowPane = w.OrchestratorWorkflowPane;
const readAtlasAsyncResource = (kind: string, rawPath: string, force?: boolean): Promise<unknown> => {
  if (typeof w.readAtlasAsyncResource !== 'function') return Promise.resolve(null);
  return w.readAtlasAsyncResource(kind, rawPath, force);
};

export interface WorkflowReportPaneProps {
  workflow: string;
  activeIp?: string;
}

export const WorkflowReportPane = ({ workflow, activeIp }: WorkflowReportPaneProps): ReactNode => {
  const WORKFLOW_REPORT_TABS = w.WORKFLOW_REPORT_TABS || {};
  const meta = WORKFLOW_REPORT_TABS[workflow] || null;
  const inferredIp = useMemo(() => {
    const direct = String(activeIp || '').trim();
    if (direct && direct !== 'default') return direct;
    const ns = String(w.ACTIVE_SESSION || '').replace(/^\/+|\/+$/g, '');
    const parts = ns.split('/').filter(Boolean);
    if (parts.length >= 3 && parts[parts.length - 1] === workflow) {
      const candidate = parts[parts.length - 2] || '';
      if (candidate && candidate !== 'default') return candidate;
    }
    const scope = String(w.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
    const leaf = scope.split('/').filter(Boolean).pop() || '';
    if (leaf && leaf !== 'default' && leaf !== workflow) return leaf;
    return '';
  }, [activeIp, workflow]);
  const ip = String(inferredIp || '').trim();
  const [dataTick, setDataTick] = useState(0);
  const [selected, setSelected] = useState('');
  const [focusLine, setFocusLine] = useState(0);
  const [selectedLintDiagnostic, setSelectedLintDiagnostic] = useState<LintDiagnostic | null>(null);

  useEffect(() => {
    const handler = (ev: Event) => {
      const detail = ev && (ev as CustomEvent).detail;
      if (detail === 'FILE_TREE' || detail === 'SCOPE_PATH') setDataTick(v => v + 1);
    };
    window.addEventListener('atlas-data-changed', handler);
    return () => window.removeEventListener('atlas-data-changed', handler);
  }, []);

  useEffect(() => {
    if (!w.atlasData?.refreshFileTree) return;
    if (!ip) return;
    try {
      w.atlasData.refreshFileTree(ip, { recursive: true });
    } catch (_) {}
  }, [workflow, ip]);

  const paths = useMemo(() => {
    if (!meta || !ip) return [];
    const candidatePaths = (meta.paths ? meta.paths(ip) : []).filter(Boolean) as string[];
    const scope = String(w.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
    const folderPrefixes = (meta.folders || []).map((f: string) => `${ip}/${f.replace(/^\/+|\/+$/g, '')}/`);
    const related = (w.FILE_TREE || [])
      .filter(n => n && n.type === 'file')
      .map(n => {
        const relName = String(n.name || '').replace(/^\/+|\/+$/g, '');
        return (scope ? `${scope}/` : '') + relName;
      })
      .filter(p => folderPrefixes.some((prefix: string) => p.startsWith(prefix)))
      .sort((a, b) => a.localeCompare(b));
    return Array.from(new Set([...candidatePaths, ...related]));
  }, [meta, ip, dataTick]);

  const pathsKey = paths.join('\n');
  useEffect(() => {
    if (!paths.length) {
      setSelected('');
      setFocusLine(0);
      setSelectedLintDiagnostic(null);
      return;
    }
    setSelected(current => (current && paths.includes(current)) ? current : paths[0]);
  }, [pathsKey]);

  const selectPath = useCallback((path: string) => {
    setSelected(path);
    setFocusLine(0);
    setSelectedLintDiagnostic(null);
  }, []);

  const openLintDiagnostic = useCallback((diag: LintDiagnostic | null | undefined) => {
    const diagPath = lintDiagnosticPath(diag);
    const line = lintDiagnosticLine(diag);
    if (!diagPath) return;
    setSelected(diagPath);
    setFocusLine(line || 0);
    setSelectedLintDiagnostic(diag || null);
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
              try { w.atlasData?.refreshFileTree?.(ip || w.SCOPE_PATH || '', { recursive: true }); } catch (_) {}
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
                onClick={() => selectPath(p)}
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
          <LintReportSummary ip={ip} onSelectPath={selectPath} onOpenDiagnostic={openLintDiagnostic} />
        )}
        {workflow === 'coverage' && (
          <CoverageReportSummary ip={ip} onSelectPath={selectPath} onOpenDiagnostic={openLintDiagnostic} />
        )}
        <PreviewPane path={selected} onClose={() => {}} focusLine={focusLine} lintDiagnostic={selectedLintDiagnostic} />
      </div>
    </div>
  );
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// (workspace.jsx does `const WorkflowReportPane = window.WorkflowReportPane;`).
// Cast through unknown because window.WorkflowReportPane is not yet declared in
// types/atlas-window.d.ts; remove once consumers import { WorkflowReportPane }.
(window as unknown as { WorkflowReportPane: typeof WorkflowReportPane }).WorkflowReportPane = WorkflowReportPane;
