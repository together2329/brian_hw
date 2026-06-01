import type { LintDiagnostic } from './lint-diagnostics';

export interface CoverageMetric {
  readonly label?: string;
  readonly value?: unknown;
  readonly total?: unknown;
  readonly hit?: unknown;
  readonly pct?: unknown;
  readonly target_pct?: unknown;
}

export interface CoverageFileRow {
  readonly path?: string;
  readonly file?: string;
  readonly modules?: unknown;
  readonly always_blocks?: unknown;
  readonly assigns?: unknown;
  readonly lines?: unknown;
}

export interface CoverageMissingItem {
  readonly id?: string;
  readonly description?: string;
  readonly path?: string;
  readonly file?: string;
  readonly line?: unknown;
  readonly message?: string;
  readonly reason?: string;
  readonly source?: string;
}

export interface CoverageScope {
  readonly scope?: string;
  readonly pct?: unknown;
  readonly toggled?: unknown;
  readonly total?: unknown;
  readonly nets?: unknown;
  readonly path?: string;
  readonly file?: string;
  readonly line?: unknown;
  readonly message?: string;
  readonly reason?: string;
}

export interface CoverageTool {
  readonly id?: string;
  readonly label?: string;
  readonly available: boolean;
  readonly status?: string;
  readonly note?: string;
  readonly path?: string;
  readonly vcd?: string;
  readonly metrics: readonly CoverageMetric[];
  readonly diagnostics: readonly LintDiagnostic[];
  readonly missing_bins: readonly CoverageMissingItem[];
  readonly missing: readonly CoverageMissingItem[];
  readonly files: readonly CoverageFileRow[];
  readonly scopes: readonly CoverageScope[];
}

export interface CoverageRunEntry {
  readonly name: string;
  readonly returncode?: unknown;
  readonly output: string;
}

export interface CoverageReportData {
  readonly exists: boolean;
  readonly resolved_ip?: string;
  readonly status?: string;
  readonly report_exists: boolean;
  readonly report_path?: string;
  readonly ssot_exists: boolean;
  readonly ssot_path?: string;
  readonly lcov_exists: boolean;
  readonly lcov_path?: string;
  readonly toggle_exists: boolean;
  readonly toggle_path?: string;
  readonly markdown_exists: boolean;
  readonly markdown_path?: string;
  readonly tools: readonly CoverageTool[];
  readonly artifacts: readonly unknown[];
  readonly vcd_paths: readonly string[];
  readonly errors: readonly string[];
  readonly run_entries: readonly CoverageRunEntry[];
}

export const textValue = (value: unknown): string => String(value ?? '').trim();

export const numberValue = (value: unknown): number | null => {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const asRecord = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;

const optionalString = (value: unknown): string | undefined => {
  const text = textValue(value);
  return text || undefined;
};

const normalizeMetric = (value: unknown): CoverageMetric | null => {
  const record = asRecord(value);
  if (!record) return null;
  return {
    label: optionalString(record.label),
    value: record.value,
    total: record.total,
    hit: record.hit,
    pct: record.pct,
    target_pct: record.target_pct,
  };
};

const normalizeDiagnostic = (value: unknown): LintDiagnostic | null => {
  const record = asRecord(value);
  if (!record) return null;
  return {
    path: optionalString(record.path),
    file: optionalString(record.file),
    line: record.line as string | number | undefined,
    column: record.column as string | number | undefined,
    severity: optionalString(record.severity),
    rule: optionalString(record.rule),
    message: optionalString(record.message),
    source: optionalString(record.source),
  };
};

const normalizeMissingItem = (value: unknown): CoverageMissingItem | null => {
  if (typeof value === 'string') return { id: value, description: value };
  const record = asRecord(value);
  if (!record) return null;
  return {
    id: optionalString(record.id),
    description: optionalString(record.description),
    path: optionalString(record.path),
    file: optionalString(record.file),
    line: record.line,
    message: optionalString(record.message),
    reason: optionalString(record.reason),
    source: optionalString(record.source),
  };
};

const normalizeFileRow = (value: unknown): CoverageFileRow | null => {
  const record = asRecord(value);
  if (!record) return null;
  return {
    path: optionalString(record.path),
    file: optionalString(record.file),
    modules: record.modules,
    always_blocks: record.always_blocks,
    assigns: record.assigns,
    lines: record.lines,
  };
};

const normalizeScope = (value: unknown): CoverageScope | null => {
  const record = asRecord(value);
  if (!record) return null;
  return {
    scope: optionalString(record.scope),
    pct: record.pct,
    toggled: record.toggled,
    total: record.total,
    nets: record.nets,
    path: optionalString(record.path),
    file: optionalString(record.file),
    line: record.line,
    message: optionalString(record.message),
    reason: optionalString(record.reason),
  };
};

const normalizedArray = <T,>(value: unknown, normalize: (item: unknown) => T | null): readonly T[] =>
  Array.isArray(value) ? value.map(normalize).filter((item): item is T => item !== null) : [];

const normalizeTool = (value: unknown): CoverageTool | null => {
  const record = asRecord(value);
  if (!record) return null;
  return {
    id: optionalString(record.id),
    label: optionalString(record.label),
    available: record.available === true,
    status: optionalString(record.status),
    note: optionalString(record.note),
    path: optionalString(record.path),
    vcd: optionalString(record.vcd),
    metrics: normalizedArray(record.metrics, normalizeMetric),
    diagnostics: normalizedArray(record.diagnostics, normalizeDiagnostic),
    missing_bins: normalizedArray(record.missing_bins, normalizeMissingItem),
    missing: normalizedArray(record.missing, normalizeMissingItem),
    files: normalizedArray(record.files, normalizeFileRow),
    scopes: normalizedArray(record.scopes, normalizeScope),
  };
};

const normalizeRunEntries = (value: unknown): readonly CoverageRunEntry[] => {
  const record = asRecord(value);
  if (!record) return [];
  return Object.entries(record)
    .map(([name, info]): CoverageRunEntry | null => {
      const item = asRecord(info);
      const output = optionalString(item?.output);
      return output ? { name, returncode: item?.returncode, output } : null;
    })
    .filter((entry): entry is CoverageRunEntry => entry !== null);
};

const stringArray = (value: unknown): readonly string[] =>
  Array.isArray(value)
    ? value.map(optionalString).filter((item): item is string => item !== undefined)
    : [];

export const normalizeCoverageReport = (value: unknown): CoverageReportData => {
  const record = asRecord(value) || {};
  return {
    exists: record.exists === true,
    resolved_ip: optionalString(record.resolved_ip),
    status: optionalString(record.status),
    report_exists: record.report_exists === true,
    report_path: optionalString(record.report_path),
    ssot_exists: record.ssot_exists === true,
    ssot_path: optionalString(record.ssot_path),
    lcov_exists: record.lcov_exists === true,
    lcov_path: optionalString(record.lcov_path),
    toggle_exists: record.toggle_exists === true,
    toggle_path: optionalString(record.toggle_path),
    markdown_exists: record.markdown_exists === true,
    markdown_path: optionalString(record.markdown_path),
    tools: normalizedArray(record.tools, normalizeTool),
    artifacts: Array.isArray(record.artifacts) ? record.artifacts : [],
    vcd_paths: stringArray(record.vcd_paths),
    errors: stringArray(record.errors),
    run_entries: normalizeRunEntries(record.run),
  };
};

export const preferredCoveragePath = (data: CoverageReportData): string => {
  if (data.report_exists && data.report_path) return data.report_path;
  if (data.ssot_exists && data.ssot_path) return data.ssot_path;
  if (data.lcov_exists && data.lcov_path) return data.lcov_path;
  if (data.toggle_exists && data.toggle_path) return data.toggle_path;
  if (data.markdown_exists && data.markdown_path) return data.markdown_path;
  return '';
};
