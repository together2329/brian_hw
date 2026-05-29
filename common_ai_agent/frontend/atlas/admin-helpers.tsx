// admin-helpers.tsx — TypeScript migration of the pure helper functions
// extracted from admin.jsx (strangler-fig split, sub-1000 line refactor).
//
// In admin.jsx these were `const fmt = ...` etc. declared inside AdminPage.
// Every helper here is pure (no component state) EXCEPT the filter predicates
// `inRange`/`rowMatches`/`valueMatches`, which closed over the `filters` state.
// Those are reconstructed verbatim via `makeFilterHelpers(filters)` so the
// caller passes its live `filters` object and gets back identical predicates.
//
// Cross-file: this file owns no window globals; it exports typed helpers used
// by the admin-*.tsx family. Types are intentionally loose (any/unknown) for
// the dynamic DB-row shapes, matching the original untyped behavior exactly.

// Generic admin row — server JSON with arbitrary keys.
export type AdminRow = Record<string, any>;

export const formatDate = (ts: unknown): string => {
  if (!ts) return '—';
  try {
    return new Date((ts as number) * 1000).toLocaleString();
  } catch (_) {
    return String(ts);
  }
};

export const fmt = (n: unknown): string => (n == null ? '—' : Number(n).toLocaleString());
export const usd = (n: unknown): string => (n == null ? '—' : `$${Number(n).toFixed(4)}`);
export const durationMs = (n: unknown): string => {
  const value = Number(n || 0);
  if (!value) return '—';
  if (value < 1000) return `${value.toFixed(0)} ms`;
  return `${(value / 1000).toFixed(1)} s`;
};
export const shortId = (value: unknown): string => String(value || '').slice(0, 8) || '—';
export const sessionDisplay = (rowOrId: any): string => {
  const row = rowOrId && typeof rowOrId === 'object' ? rowOrId : { session_id: rowOrId };
  const sessionId = String(row.session_id || row.id || '').trim();
  if (sessionId.includes('/')) return sessionId;
  const label = String(row.session || '').trim();
  return label || shortId(sessionId);
};
export const keyPart = (value: unknown): string => {
  if (value === null || value === undefined || value === '') return 'empty';
  try {
    const text = typeof value === 'object' ? JSON.stringify(value) : String(value);
    return text.replace(/\s+/g, ' ').slice(0, 120) || 'empty';
  } catch (_) {
    return 'value';
  }
};
export const rowKey = (scope: string, index: number, ...parts: unknown[]): string => (
  [scope, ...parts.map(keyPart), index].join(':')
);
export const firstVersion = (row: AdminRow, type: string): any => {
  const items = (row.artifact_versions && row.artifact_versions[type]) || [];
  return items.length ? items[0] : null;
};
export const versionText = (row: AdminRow, type: string): string => {
  const item = firstVersion(row, type);
  return item ? item.version || shortId(item.artifact_version_id) : '—';
};
export const versionTagText = (row: AdminRow, type: string): string => {
  const item = firstVersion(row, type);
  return item ? item.git_tag || item.sha256_tree || shortId(item.artifact_version_id) : '—';
};
export const payloadText = (value: unknown): string => {
  if (value == null || value === '') return '—';
  try {
    const text = typeof value === 'string' ? value : JSON.stringify(value);
    return text.length > 180 ? text.slice(0, 177) + '…' : text;
  } catch (_) {
    return String(value);
  }
};
export const sum = (rows: AdminRow[], key: string): number =>
  rows.reduce((acc, row) => acc + Number(row[key] || 0), 0);

export const rowTimestamp = (row: AdminRow): number => {
  const direct = row.active_session_updated_at || row.last_message_at || row.last_event_at || row.last_tool_at
    || row.last_intervention_at || row.started_at || row.ended_at
    || row.created_at || row.updated_at || row.first_intervention_at;
  if (direct) return Number(direct) || 0;
  if (row.day) {
    const parsed = Date.parse(`${row.day}T23:59:59`);
    return Number.isNaN(parsed) ? 0 : parsed / 1000;
  }
  return 0;
};

export const valueMatches = (selected: string, value: unknown): boolean =>
  !selected || String(value || '') === selected;

export const uniqueOptions = (rows: AdminRow[], key: string): string[] => Array.from(new Set(
  rows.map((row) => String(row[key] || '').trim()).filter(Boolean)
)).sort((a, b) => a.localeCompare(b));

export const workloadScore = (row: AdminRow): number =>
  Number(row.cost || 0) || Number(row.calls || 0) || Number(row.sessionCount || 0);

export const aggregateWorkload = (rows: AdminRow[], key: string, fallback: string): AdminRow[] => {
  const grouped = new Map<string, any>();
  rows.forEach((row) => {
    const name = String(row[key] || '').trim() || fallback;
    if (!grouped.has(name)) {
      grouped.set(name, {
        name,
        calls: 0,
        tokens: 0,
        cost: 0,
        sessionIds: new Set(),
        users: new Set(),
        lastAt: 0,
      });
    }
    const item = grouped.get(name);
    item.calls += Number(row.calls || 0);
    item.tokens += Number(row.tokens || 0);
    item.cost += Number(row.cost || 0);
    if (row.session_id) item.sessionIds.add(row.session_id);
    if (row.username || row.owner_username) item.users.add(row.username || row.owner_username);
    item.lastAt = Math.max(item.lastAt, rowTimestamp(row));
  });
  return Array.from(grouped.values())
    .map((row) => ({
      ...row,
      sessionCount: row.sessionIds.size,
      userCount: row.users.size,
      userList: Array.from(row.users).sort(),
    }))
    .sort((a, b) => workloadScore(b) - workloadScore(a) || b.lastAt - a.lastAt || a.name.localeCompare(b.name));
};

// Filter state shape (mirror of admin.jsx `filters`).
export interface AdminFilters {
  range: string;
  ip: string;
  workspace: string;
  workflow: string;
  user: string;
}

export interface FilterHelpers {
  inRange: (row: AdminRow) => boolean;
  rowMatches: (row: AdminRow) => boolean;
}

// Reconstruct the `filters`-closing predicates from admin.jsx verbatim.
export const makeFilterHelpers = (filters: AdminFilters): FilterHelpers => {
  const inRange = (row: AdminRow): boolean => {
    if (!filters.range || filters.range === 'all') return true;
    const days = ({ '24h': 1, '7d': 7, '30d': 30 } as Record<string, number>)[filters.range] || 7;
    const ts = rowTimestamp(row);
    if (!ts) return true;
    return ts >= ((Date.now() / 1000) - days * 86400);
  };
  const rowMatches = (row: AdminRow): boolean => (
    inRange(row)
    && valueMatches(filters.ip, row.ip)
    && valueMatches(filters.workspace, row.workspace)
    && valueMatches(filters.workflow, row.workflow)
    && valueMatches(filters.user, row.username || row.owner_username)
  );
  return { inRange, rowMatches };
};
