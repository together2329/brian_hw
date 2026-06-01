import type { ReactNode } from 'react';

import type { LintDiagnostic } from './lint-diagnostics';
import { AtlasStatusBadge } from './workspace-report-status';
import {
  type CoverageMetric,
  type CoverageTool,
} from './coverage-report-model';
import {
  CoverageDiagnosticButton,
  MissingBinRow,
  MissingItemRow,
  SectionTitle,
  StaticFileRow,
  ToggleScopeRow,
} from './coverage-report-details';

interface CoverageToolCardProps {
  readonly tool: CoverageTool;
  readonly onSelectPath?: (path: string) => void;
  readonly onOpenDiagnostic?: (diagnostic: LintDiagnostic) => void;
}

interface CoverageMetricCellProps {
  readonly metric?: CoverageMetric;
}

export const coverageMetricText = (metric?: CoverageMetric): string => {
  if (!metric) return 'n/a';
  if (metric.value != null) return String(metric.value);
  const total = metric.total;
  const hit = metric.hit;
  if (total != null && Number(total) > 0) {
    const pct = Number(metric.pct);
    const pctText = Number.isFinite(pct) ? ` / ${pct.toFixed(1)}%` : '';
    const pctSuffix = metric.pct == null ? '' : pctText;
    return `${hit ?? 0}/${total}${pctSuffix}`;
  }
  const pct = Number(metric.pct);
  if (Number.isFinite(pct)) return `${pct.toFixed(1)}%`;
  return String(hit ?? 'n/a');
};

export const CoverageMetricCell = ({ metric }: CoverageMetricCellProps): ReactNode => {
  const pct = Number(metric?.pct);
  const hasPct = Number.isFinite(pct);
  const clamped = Math.max(0, Math.min(100, hasPct ? pct : 0));
  const target = Number(metric?.target_pct ?? 90);
  const color = hasPct && pct >= target ? 'var(--ok)' : hasPct ? 'var(--warn)' : 'var(--fg-mute)';
  return (
    <div style={{ border: '1px solid var(--line)', background: 'var(--bg)', borderRadius: 3, padding: '6px 7px', minWidth: 0 }}>
      <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{metric?.label || 'metric'}</div>
      <div className="trunc" title={coverageMetricText(metric)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 13 }}>
        {coverageMetricText(metric)}
      </div>
      {hasPct && (
        <div style={{ height: 4, background: 'var(--line)', marginTop: 5, borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ width: `${clamped}%`, height: '100%', background: color }} />
        </div>
      )}
    </div>
  );
};

export const CoverageToolCard = ({ tool, onSelectPath, onOpenDiagnostic }: CoverageToolCardProps): ReactNode => {
  const available = tool.available === true;
  const status = available ? (tool.status || 'available') : 'missing';
  const assetPath = tool.path || tool.vcd || '';
  return (
    <div style={{ border: '1px solid ' + (available ? 'var(--line)' : 'color-mix(in oklch, var(--warn) 35%, var(--line))'), background: 'var(--panel)', borderRadius: 4, padding: 10, minWidth: 0, display: 'grid', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <span className="trunc" title={tool.label || ''} style={{ fontFamily: 'var(--mono)', fontWeight: 900, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {tool.label || 'coverage'}
        </span>
        <AtlasStatusBadge status={status === 'pass' ? 'approved' : status === 'missing' ? 'pending' : status} label={status} compact />
      </div>
      {tool.metrics.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(108px, 1fr))', gap: 7 }}>
          {tool.metrics.map((metric, idx) => <CoverageMetricCell key={`${tool.id || 'tool'}-${idx}`} metric={metric} />)}
        </div>
      )}
      {tool.note && <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>{tool.note}</div>}
      {assetPath && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', minWidth: 0 }}>
          <button className="btn" onClick={() => onSelectPath?.(assetPath)} style={{ padding: '2px 8px', fontSize: 10 }}>open artifact</button>
          <span className="trunc" title={assetPath} style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>{assetPath}</span>
        </div>
      )}
      {tool.diagnostics.length > 0 && <div style={{ display: 'grid', gap: 5 }}>{tool.diagnostics.slice(0, 6).map((diagnostic, idx) => <CoverageDiagnosticButton key={idx} diagnostic={diagnostic} onOpenDiagnostic={onOpenDiagnostic} />)}</div>}
      {tool.files.length > 0 && <div style={{ borderTop: '1px solid var(--line)', paddingTop: 7, display: 'grid', gap: 4 }}><SectionTitle>static rtl files</SectionTitle>{tool.files.slice(0, 6).map((row, idx) => <StaticFileRow key={idx} row={row} onSelectPath={onSelectPath} />)}</div>}
      {tool.missing.length > 0 && <div style={{ borderTop: '1px solid var(--line)', paddingTop: 7, display: 'grid', gap: 4 }}><SectionTitle>missing rtl/source</SectionTitle>{tool.missing.slice(0, 6).map((item, idx) => <MissingItemRow key={idx} item={item} />)}</div>}
      {tool.missing_bins.length > 0 && <div style={{ borderTop: '1px solid var(--line)', paddingTop: 7, display: 'grid', gap: 4 }}><SectionTitle>missing bins</SectionTitle>{tool.missing_bins.slice(0, 6).map((bin, idx) => <MissingBinRow key={idx} bin={bin} onOpenDiagnostic={onOpenDiagnostic} />)}</div>}
      {tool.scopes.length > 0 && <div style={{ borderTop: '1px solid var(--line)', paddingTop: 7, display: 'grid', gap: 4 }}><SectionTitle>lowest-toggle scopes</SectionTitle>{tool.scopes.slice(0, 6).map((scope, idx) => <ToggleScopeRow key={idx} scope={scope} onOpenDiagnostic={onOpenDiagnostic} />)}</div>}
    </div>
  );
};
