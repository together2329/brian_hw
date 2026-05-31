import type { ReactNode } from 'react';

import { AtlasStatusBadge } from './workspace-report-status';

export interface LintDiagnostic {
  readonly path?: string;
  readonly file?: string;
  readonly line?: number | string;
  readonly column?: number | string;
  readonly severity?: string;
  readonly rule?: string;
  readonly message?: string;
  readonly source?: string;
}

interface LintToolResult {
  readonly tool?: string;
  readonly passed?: boolean;
  readonly returncode?: number | string;
  readonly errors?: number | string;
  readonly warnings?: number | string;
  readonly command?: string;
  readonly diagnostics?: readonly LintDiagnostic[];
}

interface LintDiagnosticGroup {
  readonly key: string;
  readonly label: string;
  readonly severity: string;
  readonly diagnostics: readonly LintDiagnostic[];
}

interface LintToolResultCardProps {
  readonly result?: LintToolResult;
  readonly onOpenDiagnostic?: (diagnostic: LintDiagnostic) => void;
}

interface LintDiagnosticAnnotationProps {
  readonly diagnostic: LintDiagnostic;
}

const severityRank = (severity: string): number => {
  const normalized = severity.trim().toLowerCase();
  if (normalized === 'fatal' || normalized === 'error') return 0;
  if (normalized === 'warning' || normalized === 'warn') return 1;
  return 2;
};

const textValue = (value: unknown): string => String(value ?? '').trim();

export const lintDiagnosticPath = (diagnostic: LintDiagnostic | null | undefined): string =>
  textValue(diagnostic?.path || diagnostic?.file).replace(/^\/+/, '');

export const lintDiagnosticLine = (diagnostic: LintDiagnostic | null | undefined): number => {
  const line = Number(diagnostic?.line || 0);
  return Number.isFinite(line) && line > 0 ? line : 0;
};

const lintDiagnosticColumn = (diagnostic: LintDiagnostic): number => {
  const column = Number(diagnostic.column || 0);
  return Number.isFinite(column) && column > 0 ? column : 0;
};

const lintDiagnosticRule = (diagnostic: LintDiagnostic): string => {
  const explicit = textValue(diagnostic.rule);
  if (explicit) return explicit;
  const haystack = `${textValue(diagnostic.message)} ${textValue(diagnostic.source)}`;
  const verilatorCode = haystack.match(/%(?:Error|Warning|Fatal)-([A-Za-z0-9_]+)/);
  if (verilatorCode?.[1]) return verilatorCode[1];
  const uppercaseCode = haystack.match(/\b([A-Z][A-Z0-9_]{2,})\b/);
  if (uppercaseCode?.[1]) return uppercaseCode[1];
  return textValue(diagnostic.message).slice(0, 48) || 'lint';
};

const lintDiagnosticSeverity = (diagnostic: LintDiagnostic): string =>
  textValue(diagnostic.severity) || 'diagnostic';

const testIdToken = (value: string): string => {
  const token = value.replace(/[^A-Za-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');
  return token || 'lint';
};

export const groupLintDiagnostics = (diagnostics: readonly LintDiagnostic[]): readonly LintDiagnosticGroup[] => {
  const buckets = new Map<string, LintDiagnostic[]>();
  for (const diagnostic of diagnostics) {
    const key = lintDiagnosticRule(diagnostic);
    const bucket = buckets.get(key) || [];
    bucket.push(diagnostic);
    buckets.set(key, bucket);
  }
  return Array.from(buckets.entries())
    .map(([key, items]) => {
      const severity = items
        .map(lintDiagnosticSeverity)
        .sort((a, b) => severityRank(a) - severityRank(b))[0] || 'diagnostic';
      return { key, label: key, severity, diagnostics: items };
    })
    .sort((a, b) => {
      const severityDelta = severityRank(a.severity) - severityRank(b.severity);
      if (severityDelta) return severityDelta;
      const countDelta = b.diagnostics.length - a.diagnostics.length;
      if (countDelta) return countDelta;
      return a.label.localeCompare(b.label);
    });
};

const locationText = (diagnostic: LintDiagnostic): string => {
  const path = textValue(diagnostic.file || diagnostic.path) || '(no file)';
  const line = lintDiagnosticLine(diagnostic);
  const column = lintDiagnosticColumn(diagnostic);
  return `${path}${line ? `:${line}` : ''}${column ? `:${column}` : ''}`;
};

const severityColor = (severity: string): string => {
  const normalized = severity.trim().toLowerCase();
  if (normalized === 'fatal' || normalized === 'error') return 'var(--err)';
  if (normalized === 'warning' || normalized === 'warn') return 'var(--warn)';
  return 'var(--accent)';
};

const LintDiagnosticButton = ({
  diagnostic,
  onOpenDiagnostic,
}: {
  readonly diagnostic: LintDiagnostic;
  readonly onOpenDiagnostic?: (diagnostic: LintDiagnostic) => void;
}): ReactNode => {
  const severity = lintDiagnosticSeverity(diagnostic);
  const message = textValue(diagnostic.message) || '(no message)';
  const source = textValue(diagnostic.source);
  const path = lintDiagnosticPath(diagnostic);
  const line = lintDiagnosticLine(diagnostic);
  const canOpen = !!path;
  return (
    <button
      type="button"
      data-lint-path={path}
      data-lint-line={line ? String(line) : undefined}
      onClick={() => {
        if (canOpen) onOpenDiagnostic?.(diagnostic);
      }}
      style={{
        textAlign: 'left',
        border: 0,
        background: 'transparent',
        borderLeft: `2px solid ${severityColor(severity)}`,
        padding: '0 0 0 7px',
        color: 'var(--fg)',
        fontFamily: 'var(--mono)',
        fontSize: 10,
        lineHeight: 1.35,
        cursor: canOpen ? 'pointer' : 'default',
        minWidth: 0,
      }}
    >
      <span className="trunc" title={locationText(diagnostic)} style={{ display: 'block', color: 'var(--fg-mute)', minWidth: 0 }}>
        {severity} {locationText(diagnostic)}
      </span>
      <div style={{ overflowWrap: 'anywhere' }}>{message.slice(0, 260)}</div>
      {source && <div style={{ color: 'var(--fg-mute)', overflowWrap: 'anywhere' }}>{source.slice(0, 220)}</div>}
    </button>
  );
};

export const LintDiagnosticLineAnnotation = ({ diagnostic }: LintDiagnosticAnnotationProps): ReactNode => {
  const severity = lintDiagnosticSeverity(diagnostic);
  const rule = lintDiagnosticRule(diagnostic);
  const message = textValue(diagnostic.message) || '(no lint message)';
  const source = textValue(diagnostic.source);
  return (
    <div
      data-testid="lint-diagnostic-annotation"
      style={{
        border: `1px solid color-mix(in oklch, ${severityColor(severity)} 45%, var(--line))`,
        borderLeft: `3px solid ${severityColor(severity)}`,
        background: 'color-mix(in oklch, var(--panel) 82%, var(--bg))',
        borderRadius: 3,
        padding: '7px 9px',
        color: 'var(--fg)',
        fontFamily: 'var(--mono)',
        fontSize: 10,
        lineHeight: 1.45,
        whiteSpace: 'normal',
        overflowWrap: 'anywhere',
      }}
    >
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', minWidth: 0, marginBottom: 4 }}>
        <span style={{ color: severityColor(severity), fontWeight: 900, textTransform: 'uppercase' }}>{severity}</span>
        <span style={{ color: 'var(--fg)', fontWeight: 900 }}>{rule}</span>
        <span className="trunc" title={locationText(diagnostic)} style={{ color: 'var(--fg-mute)', minWidth: 0 }}>
          {locationText(diagnostic)}
        </span>
      </div>
      <div>{message}</div>
      {source && (
        <pre style={{
          margin: '6px 0 0',
          whiteSpace: 'pre-wrap',
          color: 'var(--fg-mute)',
          fontFamily: 'inherit',
          fontSize: 'inherit',
        }}>
          {source}
        </pre>
      )}
    </div>
  );
};

export const LintToolResultCard = ({ result, onOpenDiagnostic }: LintToolResultCardProps): ReactNode => {
  const passed = result?.passed === true;
  const diagnostics = Array.isArray(result?.diagnostics) ? result.diagnostics : [];
  const groups = groupLintDiagnostics(diagnostics);
  return (
    <div style={{
      border: `1px solid ${passed ? 'color-mix(in oklch, var(--ok) 35%, var(--line))' : 'color-mix(in oklch, var(--err) 35%, var(--line))'}`,
      background: 'var(--panel)',
      borderRadius: 4,
      padding: 10,
      minWidth: 0,
      overflow: 'hidden',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, minWidth: 0 }}>
        <span className="trunc" title={result?.tool || 'tool'} style={{ fontFamily: 'var(--mono)', fontWeight: 900, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em', minWidth: 0 }}>
          {result?.tool || 'tool'}
        </span>
        <AtlasStatusBadge status={passed ? 'approved' : 'error'} label={passed ? 'pass' : 'fail'} compact />
        <span style={{ flex: 1, minWidth: 0 }} />
        <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, flex: '0 0 auto' }}>
          rc {result?.returncode ?? '?'}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8, marginBottom: 8, minWidth: 0 }}>
        {[
          ['errors', result?.errors ?? 0],
          ['warnings', result?.warnings ?? 0],
          ['diagnostics', diagnostics.length],
        ].map(([label, value]) => (
          <div key={label} style={{ border: '1px solid var(--line)', background: 'var(--bg)', borderRadius: 3, padding: '6px 7px', minWidth: 0 }}>
            <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
            <div className="trunc" title={String(value)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 14 }}>{value}</div>
          </div>
        ))}
      </div>
      <div className="trunc" title={result?.command || ''} style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, minWidth: 0, maxWidth: '100%' }}>
        {result?.command || '(no command)'}
      </div>
      {groups.length > 0 && (
        <div style={{ marginTop: 8, display: 'grid', gap: 6, minWidth: 0 }}>
          {groups.map((group, idx) => (
            <details
              key={group.key}
              open={idx === 0}
              data-testid={`lint-diagnostic-group-${testIdToken(group.key)}`}
              style={{
                border: '1px solid var(--line)',
                borderRadius: 3,
                background: 'var(--bg)',
                minWidth: 0,
                overflow: 'hidden',
              }}
            >
              <summary style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(0, 1fr) auto',
                gap: 8,
                alignItems: 'center',
                padding: '5px 7px',
                cursor: 'pointer',
                color: 'var(--fg)',
                fontFamily: 'var(--mono)',
                fontSize: 10,
              }}>
                <span className="trunc" title={group.label} style={{ fontWeight: 900, color: severityColor(group.severity) }}>
                  {group.label}
                </span>
                <span style={{
                  color: 'var(--fg)',
                  border: '1px solid var(--line)',
                  borderRadius: 999,
                  padding: '0 6px',
                  fontWeight: 900,
                }}>
                  {group.diagnostics.length}
                </span>
              </summary>
              <div style={{ display: 'grid', gap: 5, padding: '0 7px 7px', minWidth: 0 }}>
                {group.diagnostics.map((diagnostic, diagnosticIdx) => (
                  <LintDiagnosticButton
                    key={`${locationText(diagnostic)}-${diagnosticIdx}`}
                    diagnostic={diagnostic}
                    onOpenDiagnostic={onOpenDiagnostic}
                  />
                ))}
              </div>
            </details>
          ))}
        </div>
      )}
    </div>
  );
};
