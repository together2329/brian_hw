import type { ReactNode } from 'react';

import type { LintDiagnostic } from './lint-diagnostics';
import {
  numberValue,
  textValue,
  type CoverageFileRow,
  type CoverageMissingItem,
  type CoverageScope,
} from './coverage-report-model';

export const SectionTitle = ({ children }: { readonly children: ReactNode }): ReactNode => (
  <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{children}</div>
);

const openablePath = (path?: string, file?: string): string => textValue(path || file).replace(/^\/+/, '');

const diagnosticLocation = (diagnostic: LintDiagnostic): string => {
  const location = textValue(diagnostic.file || diagnostic.path) || '(no file)';
  return `${location}${diagnostic.line ? `:${diagnostic.line}` : ''}`;
};

export const CoverageDiagnosticButton = ({
  diagnostic,
  onOpenDiagnostic,
}: {
  readonly diagnostic: LintDiagnostic;
  readonly onOpenDiagnostic?: (diagnostic: LintDiagnostic) => void;
}): ReactNode => {
  const path = openablePath(diagnostic.path, diagnostic.file);
  const severity = textValue(diagnostic.severity) || 'diag';
  const message = textValue(diagnostic.message) || '(no message)';
  return (
    <button
      type="button"
      onClick={() => {
        if (path) onOpenDiagnostic?.(diagnostic);
      }}
      style={{
        textAlign: 'left',
        border: 0,
        background: 'transparent',
        borderLeft: '2px solid ' + (severity.toLowerCase() === 'error' ? 'var(--err)' : 'var(--warn)'),
        padding: '0 0 0 7px',
        color: 'var(--fg)',
        fontFamily: 'var(--mono)',
        fontSize: 10,
        lineHeight: 1.35,
        cursor: path ? 'pointer' : 'default',
      }}
    >
      <span style={{ color: 'var(--fg-mute)' }}>{severity} {diagnosticLocation(diagnostic)}</span>
      <div>{message.slice(0, 260)}</div>
    </button>
  );
};

const statText = (label: string, value: unknown): string | null => {
  const text = textValue(value);
  return text ? `${label} ${text}` : null;
};

export const StaticFileRow = ({
  row,
  onSelectPath,
}: {
  readonly row: CoverageFileRow;
  readonly onSelectPath?: (path: string) => void;
}): ReactNode => {
  const path = openablePath(row.path, row.file);
  const stats = [
    statText('modules', row.modules),
    statText('always', row.always_blocks),
    statText('assigns', row.assigns),
    statText('lines', row.lines),
  ].filter((item): item is string => item !== null);
  const content = (
    <>
      <span className="trunc" title={path}>{path || '(rtl file)'}</span>
      <span style={{ color: 'var(--fg-mute)' }}>{stats.join(' / ') || 'no static counts'}</span>
    </>
  );
  if (!path) {
    return <div style={{ display: 'grid', gap: 2, fontFamily: 'var(--mono)', fontSize: 10 }}>{content}</div>;
  }
  return (
    <button
      type="button"
      onClick={() => onSelectPath?.(path)}
      style={{ textAlign: 'left', border: 0, background: 'transparent', color: 'var(--fg)', display: 'grid', gap: 2, fontFamily: 'var(--mono)', fontSize: 10, cursor: 'pointer', padding: 0 }}
    >
      {content}
    </button>
  );
};

export const MissingItemRow = ({ item }: { readonly item: CoverageMissingItem }): ReactNode => {
  const label = textValue(item.description || item.id || item.path || item.file) || '(missing item)';
  const detail = textValue(item.reason || item.source || item.message);
  return (
    <div title={detail || label} style={{ display: 'grid', gap: 2, fontFamily: 'var(--mono)', fontSize: 10 }}>
      <span className="trunc">{label}</span>
      {detail && <span className="trunc" style={{ color: 'var(--fg-mute)' }}>{detail}</span>}
    </div>
  );
};

const binDiagnostic = (bin: CoverageMissingItem): LintDiagnostic => ({
  severity: 'warning',
  rule: 'COVERAGE_BIN',
  path: bin.path,
  file: bin.file,
  line: bin.line as string | number | undefined,
  message: textValue(bin.message || bin.description || bin.id) || 'coverage bin not hit',
  source: textValue(bin.reason || bin.source),
});

export const MissingBinRow = ({
  bin,
  onOpenDiagnostic,
}: {
  readonly bin: CoverageMissingItem;
  readonly onOpenDiagnostic?: (diagnostic: LintDiagnostic) => void;
}): ReactNode => {
  const diagnostic = binDiagnostic(bin);
  const path = openablePath(diagnostic.path, diagnostic.file);
  const label = textValue(bin.id) || 'missing bin';
  const description = textValue(bin.description || bin.reason || bin.message);
  const body = (
    <>
      <span className="trunc" title={label}>{label}</span>
      {description && <span className="trunc" title={description} style={{ color: 'var(--fg-mute)' }}>{description}</span>}
    </>
  );
  if (!path) {
    return <div style={{ display: 'grid', gap: 2, fontFamily: 'var(--mono)', fontSize: 10 }}>{body}</div>;
  }
  return (
    <button type="button" onClick={() => onOpenDiagnostic?.(diagnostic)} style={{ textAlign: 'left', border: 0, background: 'transparent', color: 'var(--fg)', display: 'grid', gap: 2, fontFamily: 'var(--mono)', fontSize: 10, cursor: 'pointer', padding: 0 }}>
      {body}
    </button>
  );
};

const toggleBitsText = (scope: CoverageScope): string => {
  const toggled = numberValue(scope.toggled);
  const total = numberValue(scope.total);
  if (toggled !== null && total !== null && total > 0) return `${toggled}/${total} bits`;
  return 'n/a bits';
};

const scopeDiagnostic = (scope: CoverageScope): LintDiagnostic => {
  const scopeName = textValue(scope.scope) || 'scope';
  const message = textValue(scope.message) || `toggle gap: only ${toggleBitsText(scope)} toggled in ${scopeName}`;
  return {
    severity: 'warning',
    rule: 'VCD_TOGGLE',
    path: scope.path,
    file: scope.file,
    line: scope.line as string | number | undefined,
    message,
    source: textValue(scope.reason),
  };
};

export const ToggleScopeRow = ({
  scope,
  onOpenDiagnostic,
}: {
  readonly scope: CoverageScope;
  readonly onOpenDiagnostic?: (diagnostic: LintDiagnostic) => void;
}): ReactNode => {
  const diagnostic = scopeDiagnostic(scope);
  const path = openablePath(diagnostic.path, diagnostic.file);
  const pct = numberValue(scope.pct);
  const reason = textValue(scope.reason) || textValue(scope.message) || 'unmet toggle target';
  const nets = textValue(scope.nets);
  const content = (
    <>
      <span style={{ color: 'var(--warn)' }}>{pct === null ? 'n/a' : `${pct.toFixed(1)}%`}</span>
      <span>{toggleBitsText(scope)}</span>
      <span className="trunc" title={scope.scope || ''}>{scope.scope || '(scope)'}</span>
      <span className="trunc" title={reason} style={{ color: 'var(--fg-mute)', gridColumn: '1 / -1' }}>{reason}</span>
      {nets && <span style={{ color: 'var(--fg-mute)', gridColumn: '1 / -1' }}>nets {nets}</span>}
    </>
  );
  const style = {
    display: 'grid',
    gridTemplateColumns: '58px 68px minmax(0, 1fr)',
    gap: 6,
    fontFamily: 'var(--mono)',
    fontSize: 10,
    textAlign: 'left' as const,
    color: 'var(--fg)',
    padding: 0,
  };
  if (!path) return <div style={style}>{content}</div>;
  return (
    <button type="button" onClick={() => onOpenDiagnostic?.(diagnostic)} style={{ ...style, border: 0, background: 'transparent', cursor: 'pointer' }}>
      {content}
    </button>
  );
};
