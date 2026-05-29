// admin-raw-db.tsx — TypeScript migration of the AdminPage "raw-db" tab,
// extracted verbatim from admin.jsx (strangler-fig split, sub-1000 lines).
//
// Presentational: the parent (admin.tsx) owns all the db state + loaders and
// passes them down. Styles + the `rowKey` helper come from the shared modules.
//
// NOTE on `rowKey`: the original raw-db block declared a LOCAL `const rowKey`
// (a `${offset}-${i}` string) inside the table-rows map, which intentionally
// shadows the imported `rowKey` helper in that scope. That shadow is preserved
// here exactly — the helper import is still used for the table-list / overview
// keys, while the local string is used for the expandable detail rows.
//
// `React.Fragment` from admin.jsx becomes an imported `Fragment`.
//
// Cross-file: owns no window globals. Consumes only the typed props below.
import { Fragment } from 'react';
import {
  tableWrapStyle, tableStyle, thStyle, tdStyle, emptyStateStyle, headerButtonStyle,
} from './admin-styles';
import { rowKey, type AdminRow } from './admin-helpers';

export interface AdminDbPage {
  columns: AdminRow[];
  rows: AdminRow[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminRawDbTabProps {
  dbTables: AdminRow[];
  dbSelectedTable: string | null;
  setDbSelectedTable: (name: string | null) => void;
  dbPage: AdminDbPage;
  dbLoading: boolean;
  dbError: string | null;
  dbExpandedRow: string | null;
  setDbExpandedRow: (key: string | null) => void;
  dbOverview: AdminRow[];
  dbOverviewLoading: boolean;
  dbHideEmpty: boolean;
  setDbHideEmpty: (v: boolean) => void;
  loadDbTables: () => void;
  loadDbTable: (name: string, offset: number, limit: number) => void;
  loadDbOverview: () => void;
}

export function AdminRawDbTab({
  dbTables, dbSelectedTable, setDbSelectedTable, dbPage, dbLoading, dbError,
  dbExpandedRow, setDbExpandedRow, dbOverview, dbOverviewLoading, dbHideEmpty,
  setDbHideEmpty, loadDbTables, loadDbTable, loadDbOverview,
}: AdminRawDbTabProps) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 16 }}>
      <div style={{ ...tableWrapStyle, maxHeight: 600, overflowY: 'auto' }}>
        <div style={{
          padding: '8px 12px', background: '#1c252f', borderBottom: '1px solid #2a3540',
          fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#a3aebb',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span>Tables ({dbTables.length})</span>
          <button
            onClick={loadDbTables}
            style={{ ...headerButtonStyle, padding: '2px 6px', fontSize: 10 }}
            title="Refresh"
          >↻</button>
        </div>
        {dbTables.length === 0 ? (
          <div style={{ padding: 16, color: '#8893a3', fontSize: 12 }}>
            {dbError ? `Error: ${dbError}` : 'Loading…'}
          </div>
        ) : (
          dbTables.map((t, index) => {
            const active = dbSelectedTable === t.name;
            return (
              <button
                key={rowKey('db-table', index, t.name)}
                onClick={() => setDbSelectedTable(t.name)}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  width: '100%',
                  padding: '8px 12px',
                  background: active ? '#22303d' : 'transparent',
                  color: active ? '#f0c674' : '#d6dde6',
                  border: 'none',
                  borderLeft: active ? '3px solid #f0c674' : '3px solid transparent',
                  borderBottom: '1px solid #20272f',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  fontSize: 12,
                  textAlign: 'left',
                }}
              >
                <span style={{ fontWeight: active ? 600 : 400 }}>{t.name}</span>
                <span style={{
                  fontSize: 10, color: active ? '#f0c674' : '#7d8590',
                  background: '#11161c', padding: '2px 6px', borderRadius: 3,
                }}>{t.row_count}</span>
              </button>
            );
          })
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {!dbSelectedTable ? (
          <>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 12, flexWrap: 'wrap',
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#f0c674' }}>
                All tables overview
                <span style={{ color: '#7d8590', fontWeight: 400, marginLeft: 8, fontSize: 12 }}>
                  (3 most-recent rows per table · click a table name to drill in)
                </span>
              </div>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <label style={{ fontSize: 11, color: '#a3aebb', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <input
                    type="checkbox"
                    checked={dbHideEmpty}
                    onChange={(e) => setDbHideEmpty(e.target.checked)}
                  />
                  Hide empty
                </label>
                <button onClick={loadDbOverview} disabled={dbOverviewLoading} style={headerButtonStyle}>
                  {dbOverviewLoading ? '…' : '↻ Refresh'}
                </button>
              </div>
            </div>

            {dbError && (
              <div style={{ ...tableWrapStyle, padding: 16, color: '#e06c75' }}>{dbError}</div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {dbOverview.length === 0 ? (
                <div style={{ ...tableWrapStyle, padding: 24, textAlign: 'center', color: '#8893a3' }}>
                  {dbOverviewLoading ? 'Loading all tables…' : 'No data.'}
                </div>
              ) : (
                dbOverview
                  .filter((t) => !dbHideEmpty || (t.total && t.total > 0))
                  .map((t, index) => (
                    <div key={rowKey('db-overview', index, t.name)} style={tableWrapStyle}>
                      <div style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '8px 14px', background: '#1c252f',
                        borderBottom: '1px solid #2a3540',
                      }}>
                        <button
                          onClick={() => setDbSelectedTable(t.name)}
                          style={{
                            background: 'transparent', border: 'none', padding: 0,
                            color: '#f0c674', fontWeight: 600, fontSize: 13,
                            cursor: 'pointer', fontFamily: 'inherit',
                          }}
                        >
                          {t.name}
                        </button>
                        <div style={{ display: 'flex', gap: 10, fontSize: 11, color: '#7d8590' }}>
                          <span><b style={{ color: '#d6dde6' }}>{t.total}</b> rows</span>
                          <span>{t.columns.length} cols</span>
                        </div>
                      </div>
                      {t.total === 0 ? (
                        <div style={{ padding: '8px 14px', fontSize: 11, color: '#5a6470', fontStyle: 'italic' }}>
                          empty
                        </div>
                      ) : t.rows.length === 0 ? (
                        <div style={{ padding: '8px 14px', fontSize: 11, color: '#e06c75' }}>
                          {t.error || 'no preview rows available'}
                        </div>
                      ) : (
                        <div style={{ overflowX: 'auto' }}>
                          <table style={{ ...tableStyle, fontSize: 11, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
                            <thead>
                              <tr>
                                {t.columns.slice(0, 8).map((c: AdminRow) => (
                                  <th key={c.name} style={{ ...thStyle, padding: '6px 10px', fontSize: 10, whiteSpace: 'nowrap' }}>
                                    {c.name}{c.pk ? <span style={{ color: '#f0c674', marginLeft: 3 }}>*</span> : null}
                                  </th>
                                ))}
                                {t.columns.length > 8 && (
                                  <th style={{ ...thStyle, padding: '6px 10px', fontSize: 10, color: '#7d8590' }}>
                                    +{t.columns.length - 8} more
                                  </th>
                                )}
                              </tr>
                            </thead>
                            <tbody>
                              {t.rows.map((row: AdminRow, i: number) => (
                                <tr key={i}>
                                  {t.columns.slice(0, 8).map((c: AdminRow) => {
                                    const v = row[c.name];
                                    let text;
                                    if (v === null || v === undefined) text = '∅';
                                    else if (typeof v === 'object') text = JSON.stringify(v);
                                    else if (typeof v === 'number' && c.name.endsWith('_at') && v > 1e9) {
                                      try { text = new Date(v * 1000).toISOString().replace('T', ' ').slice(0, 19); }
                                      catch (_) { text = String(v); }
                                    } else text = String(v);
                                    const truncated = text.length > 40 ? text.slice(0, 40) + '…' : text;
                                    return (
                                      <td
                                        key={c.name}
                                        style={{
                                          ...tdStyle, padding: '5px 10px', maxWidth: 180,
                                          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                          color: v === null ? '#5a6470' : tdStyle.color,
                                        }}
                                        title={text}
                                      >{truncated}</td>
                                    );
                                  })}
                                  {t.columns.length > 8 && (
                                    <td style={{ ...tdStyle, padding: '5px 10px', color: '#5a6470', fontStyle: 'italic' }}>…</td>
                                  )}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  ))
              )}
            </div>
          </>
        ) : (
          <>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 12, flexWrap: 'wrap',
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#f0c674', display: 'flex', alignItems: 'center', gap: 8 }}>
                <button
                  onClick={() => setDbSelectedTable(null)}
                  style={{ ...headerButtonStyle, fontSize: 11, padding: '3px 8px' }}
                  title="Back to all-tables overview"
                >← Overview</button>
                {dbSelectedTable}
                <span style={{ color: '#7d8590', fontWeight: 400, fontSize: 12 }}>
                  ({dbPage.total} rows · showing {dbPage.offset + 1}-{Math.min(dbPage.offset + dbPage.rows.length, dbPage.total)})
                </span>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  onClick={() => loadDbTable(dbSelectedTable, Math.max(0, dbPage.offset - dbPage.limit), dbPage.limit)}
                  disabled={dbPage.offset === 0 || dbLoading}
                  style={headerButtonStyle}
                >‹ Prev</button>
                <button
                  onClick={() => loadDbTable(dbSelectedTable, dbPage.offset + dbPage.limit, dbPage.limit)}
                  disabled={dbPage.offset + dbPage.rows.length >= dbPage.total || dbLoading}
                  style={headerButtonStyle}
                >Next ›</button>
                <select
                  value={dbPage.limit}
                  onChange={(e) => loadDbTable(dbSelectedTable, 0, Number(e.target.value))}
                  style={{ ...headerButtonStyle, padding: '4px 6px' }}
                >
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={200}>200</option>
                </select>
                <button
                  onClick={() => loadDbTable(dbSelectedTable, dbPage.offset, dbPage.limit)}
                  disabled={dbLoading}
                  style={headerButtonStyle}
                >↻</button>
              </div>
            </div>

            {dbError ? (
              <div style={{ ...tableWrapStyle, padding: 16, color: '#e06c75' }}>{dbError}</div>
            ) : (
              <div style={{ ...tableWrapStyle, maxHeight: 600, overflowY: 'auto' }}>
                <table style={{ ...tableStyle, fontSize: 11.5, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
                  <thead>
                    <tr>
                      {dbPage.columns.map((c: AdminRow) => (
                        <th key={c.name} style={{ ...thStyle, fontSize: 10, whiteSpace: 'nowrap' }}>
                          {c.name}
                          {c.pk ? <span style={{ color: '#f0c674', marginLeft: 4 }}>PK</span> : null}
                          <div style={{ fontSize: 9, color: '#7d8590', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
                            {c.type || 'ANY'}{c.notnull ? ' · NN' : ''}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dbPage.rows.length === 0 ? (
                      <tr>
                        <td colSpan={dbPage.columns.length} style={{ ...tdStyle, ...emptyStateStyle }}>
                          {dbLoading ? 'Loading…' : 'Table is empty.'}
                        </td>
                      </tr>
                    ) : (
                      dbPage.rows.map((row: AdminRow, i: number) => {
                        const rowKey = `${dbPage.offset}-${i}`;
                        const expanded = dbExpandedRow === rowKey;
                        return (
                          <Fragment key={rowKey}>
                            <tr
                              onClick={() => setDbExpandedRow(expanded ? null : rowKey)}
                              style={{ cursor: 'pointer', background: expanded ? '#191c22' : 'transparent' }}
                            >
                              {dbPage.columns.map((c: AdminRow) => {
                                const v = row[c.name];
                                let text;
                                if (v === null || v === undefined) text = '∅';
                                else if (typeof v === 'object') text = JSON.stringify(v);
                                else if (typeof v === 'number' && c.name.endsWith('_at') && v > 1e9) {
                                  try { text = new Date(v * 1000).toISOString().replace('T', ' ').slice(0, 19); }
                                  catch (_) { text = String(v); }
                                } else text = String(v);
                                const truncated = text.length > 60 ? text.slice(0, 60) + '…' : text;
                                return (
                                  <td
                                    key={c.name}
                                    style={{
                                      ...tdStyle, padding: '6px 10px', maxWidth: 240,
                                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                      color: v === null ? '#5a6470' : tdStyle.color,
                                    }}
                                    title={text}
                                  >{truncated}</td>
                                );
                              })}
                            </tr>
                            {expanded && (
                              <tr>
                                <td colSpan={dbPage.columns.length} style={{ ...tdStyle, background: '#0f1419', padding: 12 }}>
                                  <pre style={{
                                    margin: 0, fontSize: 11, color: '#a3aebb', whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word',
                                  }}>{JSON.stringify(row, null, 2)}</pre>
                                </td>
                              </tr>
                            )}
                          </Fragment>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
