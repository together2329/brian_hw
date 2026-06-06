// ssot-qa-board-io.tsx — TypeScript migration + split of the import / export /
// validation UI extracted from ssot-qa-board.jsx (Phase 13f / TS-split).
//
// Holds four presentational components lifted verbatim from SsotQaBoard:
//   - <ImportStatusBanner>  = legacy renderImportStatus()        (lines 554-574)
//   - <ImportedFilesList>   = legacy renderImportedFiles()       (lines 575-610)
//   - <ValidationScriptCard>= legacy renderValidationScriptCard()(lines 611-689)
//   - <ImportExportPane>    = legacy `importExportOnly` early return (972-1131)
//
// Each was a closure inside the component reading state/setters; that state is
// now threaded in as explicit props. JSX is byte-identical to the legacy
// markup — this is a mechanical lift, not a redesign.
//
// Cross-file dep: AtlasStatusBadge is owned by the (unmigrated) workspace.jsx,
// read through window at call time via the lambda forward-ref pattern.
//
// Load order (index.html): BEFORE ssot-qa-board.tsx, which resolves these
// through the transitional window bridges at the bottom.
import { type CSSProperties, type ChangeEvent, type DragEvent, type MouseEvent, type RefObject } from 'react';

import type { SsotQaStrings } from './ssot-qa-board-i18n';

// ── Cross-file globals owned by OTHER (unmigrated) files. ──
interface IoWindowGlobals {
  AtlasStatusBadge: (...a: any[]) => any;
  // This file's OWN public globals (set via the bridge below).
  SsotImportStatusBanner: (props: ImportStatusBannerProps) => any;
  SsotImportedFilesList: (props: ImportedFilesListProps) => any;
  SsotValidationScriptCard: (props: ValidationScriptCardProps) => any;
  SsotImportExportPane: (props: ImportExportPaneProps) => any;
  SsotChecklistImportInline: (props: ChecklistImportInlineProps) => any;
  SsotRequirementsGrid: (props: RequirementsGridProps) => any;
  SsotQaActionCards: (props: QaActionCardsProps) => any;
}
const g = window as unknown as IoWindowGlobals;
const AtlasStatusBadge = (...a: any[]): any => g.AtlasStatusBadge(...a);

// ── Shared loose row/result types ────────────────────────────────────
export interface ImportedFileRow {
  name?: string;
  bytes?: number;
  md_path?: string;
  original_path?: string;
  image_count?: number;
  visual_count?: number;
  pending?: boolean;
  error?: boolean;
  ts?: number;
  [k: string]: unknown;
}
export interface ValidationResult {
  ok: boolean;
  mode: string;
  returncode: number | string;
  elapsed_ms: number | string;
  command: string;
  output: string;
}
type SetImportedFiles = (
  updater: ImportedFileRow[] | ((prev: ImportedFileRow[]) => ImportedFileRow[]),
) => void;

// ── <ImportStatusBanner> = legacy renderImportStatus() ───────────────
export interface ImportStatusBannerProps {
  importStatus: string;
  importBusy: boolean;
  setImportStatus: (value: string) => void;
}
export function ImportStatusBanner({ importStatus, importBusy, setImportStatus }: ImportStatusBannerProps) {
  if (!importStatus) return null;
  const failed = importStatus.toLowerCase().includes('fail');
  const importing = importBusy || importStatus.toLowerCase().includes('uploading') || importStatus.toLowerCase().includes('업로드 중');
  const color = failed ? 'var(--err)' : importing ? 'var(--warn)' : 'var(--ok)';
  const icon = failed ? '✕' : importing ? '⟳' : '✓';
  return (
    <div style={{
      marginTop: 10, padding: '7px 9px',
      border: `1px solid ${color}`, borderRadius: 2,
      color, background: `color-mix(in oklch, ${color} 12%, transparent)`,
      fontSize: 11, fontWeight: 600,
      display: 'flex', alignItems: 'center', gap: 6,
    }}>
      <span style={{ fontSize: 13 }}>{icon}</span>
      <span style={{ flex: 1 }}>{importStatus}</span>
      <button type="button" onClick={() => setImportStatus('')}
        style={{ background: 'transparent', border: 'none', color, cursor: 'pointer', fontSize: 12, padding: 0 }}>×</button>
    </div>
  );
}

// ── <ImportedFilesList> = legacy renderImportedFiles() ───────────────
export interface ImportedFilesListProps {
  t: SsotQaStrings;
  importedFiles: ImportedFileRow[];
  setImportedFiles: SetImportedFiles;
}
export function ImportedFilesList({ t, importedFiles, setImportedFiles }: ImportedFilesListProps) {
  return (
    <div style={{ marginTop: 12, padding: '8px 10px', border: '1px solid var(--line)', borderRadius: 2, background: 'var(--bg-2)', fontSize: 11, fontFamily: 'var(--mono)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
        <span>📥 {t.importedList} · {importedFiles.length}</span>
        {importedFiles.length ? (
          <button type="button" onClick={() => setImportedFiles([])}
            style={{ background: 'transparent', border: '1px solid var(--line)', color: 'var(--fg-mute)', cursor: 'pointer', fontSize: 10, padding: '1px 5px', borderRadius: 2 }}>clear</button>
        ) : null}
      </div>
      {importedFiles.length ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {importedFiles.map((f, i) => (
            <div key={`${f.md_path || f.original_path || f.name}-${f.ts || i}`} style={{ display: 'grid', gridTemplateColumns: '14px minmax(0, 1fr) auto', alignItems: 'center', gap: 6, padding: '4px 5px', color: 'var(--fg)', background: 'var(--bg-1)', borderRadius: 2 }}>
              <span style={{ color: f.error ? 'var(--err)' : f.pending ? 'var(--warn)' : 'var(--ok)', fontWeight: 700 }}>
                {f.error ? '✕' : f.pending ? '⟳' : '✓'}
              </span>
              <div style={{ minWidth: 0 }}>
                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={f.name}>{f.name}</div>
                {f.pending || f.error || f.md_path || f.original_path ? (
                  <div className="mute" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 10 }} title={f.md_path || f.original_path || ''}>
                    {f.pending ? 'uploading...' : f.error ? 'upload failed' : (f.md_path || f.original_path)}
                  </div>
                ) : null}
              </div>
              <span className="mute" style={{ fontSize: 10 }}>
                {f.bytes ? (f.bytes < 1024 ? `${f.bytes}B` : `${(f.bytes/1024).toFixed(1)}K`) : ''}
                {f.image_count ? ` · ${f.image_count} img` : ''}
                {f.visual_count ? ` · ${f.visual_count} visual` : ''}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ color: 'var(--fg-mute)', fontSize: 12 }}>{t.noImportedFiles}</div>
      )}
    </div>
  );
}

// ── <ValidationScriptCard> = legacy renderValidationScriptCard() ─────
export interface ValidationScriptCardProps {
  t: SsotQaStrings;
  validationMode: string;
  validationBusy: boolean;
  validationResult: ValidationResult | null;
  setValidationMode: (value: string) => void;
  runValidation: () => void;
}
export function ValidationScriptCard({
  t,
  validationMode,
  validationBusy,
  validationResult,
  setValidationMode,
  runValidation,
}: ValidationScriptCardProps) {
  const color = !validationResult ? 'var(--fg-mute)' : (validationResult.ok ? 'var(--ok)' : 'var(--err)');
  return (
    <div style={{
      border: '1px solid var(--line)',
      background: 'color-mix(in oklch, var(--bg-2) 58%, transparent)',
      padding: 10,
    }}>
      <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 800 }}>{t.validationScriptTitle}</div>
      <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45 }}>
        {t.validationScriptDetail}
      </div>
      <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <label style={{ color: 'var(--fg-mute)', fontSize: 11 }}>
          {t.validationMode}
        </label>
        <select
          value={validationMode}
          disabled={validationBusy}
          onChange={ev => setValidationMode(ev.target.value)}
          style={{
            background: 'var(--bg)', color: 'var(--fg)',
            border: '1px solid var(--line)', borderRadius: 2,
            fontFamily: 'var(--mono)', fontSize: 11, padding: '3px 6px',
          }}
        >
          <option value="starter">starter</option>
          <option value="engineering">engineering</option>
          <option value="signoff">signoff</option>
        </select>
        <button className="mini-btn" type="button" disabled={validationBusy} onClick={runValidation}>
          {validationBusy ? 'running...' : t.runValidation}
        </button>
        {validationResult ? (
          <AtlasStatusBadge
            status={validationResult.ok ? 'approved' : 'failed'}
            label={validationResult.ok ? t.validationPass : t.validationFail}
            compact
            soft
          />
        ) : null}
      </div>
      {validationResult ? (
        <div style={{
          marginTop: 10,
          border: `1px solid ${color}`,
          background: `color-mix(in oklch, ${color} 10%, transparent)`,
          padding: 8,
          color,
          fontSize: 11,
        }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: validationResult.output ? 6 : 0 }}>
            <span>{validationResult.ok ? t.validationPass : t.validationFail}</span>
            <span className="mute">mode={validationResult.mode}</span>
            <span className="mute">rc={validationResult.returncode}</span>
            {validationResult.elapsed_ms !== '' ? <span className="mute">{validationResult.elapsed_ms}ms</span> : null}
          </div>
          {validationResult.command ? (
            <div className="mute" style={{ marginBottom: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={validationResult.command}>
              {validationResult.command}
            </div>
          ) : null}
          {validationResult.output ? (
            <pre style={{
              margin: 0,
              whiteSpace: 'pre-wrap',
              color: 'var(--fg)',
              fontFamily: 'var(--mono)',
              fontSize: 11,
              lineHeight: 1.45,
              maxHeight: 180,
              overflow: 'auto',
            }}>{validationResult.output}</pre>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

// ── <ImportExportPane> = legacy `importExportOnly` early return ──────
// (lines 972-1131). Renders the full-page Import / Export workbench used when
// the board is mounted in import-only / export-only / both mode.
export interface ImportExportPaneProps {
  t: SsotQaStrings;
  ip: string;
  importExportOnly: boolean;
  importOnly: boolean;
  exportOnly: boolean;
  importInputRef: RefObject<HTMLInputElement>;
  importConverter: string;
  importDragActive: boolean;
  importBusy: boolean;
  importStatus: string;
  importedFiles: ImportedFileRow[];
  onRefresh?: () => void;
  onBack?: () => void;
  changeImportConverter: (next: string) => void;
  setImportDragActive: (active: boolean) => void;
  handleImportDrop: (ev: DragEvent<HTMLDivElement>) => void;
  uploadImportFiles: (fileList: FileList | File[] | null) => void;
  exportSsot: (format: string) => void;
  setImportStatus: (value: string) => void;
  setImportedFiles: SetImportedFiles;
}
export function ImportExportPane(props: ImportExportPaneProps) {
  const {
    t, ip, importExportOnly, importOnly, exportOnly,
    importInputRef, importConverter, importDragActive, importBusy,
    importStatus, importedFiles,
    onRefresh, onBack, changeImportConverter, setImportDragActive,
    handleImportDrop, uploadImportFiles, exportSsot,
    setImportStatus, setImportedFiles,
  } = props;
  const showImportCard = !!(importExportOnly || importOnly);
  const showExportCard = !!(importExportOnly || exportOnly);
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      fontFamily: 'var(--mono)',
      height: '100%',
      minHeight: 0,
      overflowY: 'auto',
    }}>
      <div style={{
        border: '1px solid var(--line)',
        background: 'var(--bg-1)',
        padding: 14,
      }}>
        <input
          ref={importInputRef}
          type="file"
          multiple
          accept=".pdf,.pptx,.docx,.html,.htm,.md,.txt,.rst,.yaml,.yml,.json,.sv,.svh,.v,.vh,.py,.csv,.tsv,.xml,.f,.sdc,.tcl,.rpt,.log,.h,.c,.cpp,.png,.jpg,.jpeg,.gif,.webp,.bmp,.svg,.tif,.tiff"
          style={{ display: 'none' }}
          onChange={(ev: ChangeEvent<HTMLInputElement>) => {
            const files = Array.from(ev.target.files || []);
            ev.target.value = '';
            uploadImportFiles(files);
          }}
        />
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 360px', minWidth: 260 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <div style={{ color: 'var(--fg)', fontSize: 16, fontWeight: 800 }}>
                {importOnly ? t.uploadImportTitle : (exportOnly ? t.exportTitle : t.importExportTitle)}
              </div>
              <code className="acc">{ip}</code>
            </div>
            <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45, maxWidth: 820 }}>
              {importOnly ? t.uploadImportDetail : (exportOnly ? t.exportDetail : t.importExportSubtitle)}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <button className="mini-btn" type="button" onClick={onRefresh}>{t.refresh}</button>
            <button className="mini-btn" type="button" onClick={onBack}>{t.chat}</button>
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: 12,
        alignItems: 'stretch',
      }}>
        {showImportCard && (
        <div style={{
          border: '1px solid var(--line)',
          background: 'color-mix(in oklch, var(--bg-2) 58%, transparent)',
          padding: 14,
        }}>
          <div style={{ color: 'var(--fg)', fontSize: 14, fontWeight: 800 }}>{t.uploadImportTitle}</div>
          <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45 }}>
            {t.uploadImportDetail}
          </div>
          <div style={{
            marginTop: 10,
            display: 'flex', alignItems: 'center', gap: 8,
            fontSize: 11, color: 'var(--fg-mute)',
          }}>
            <span>Converter</span>
            <select
              value={importConverter}
              onChange={(ev) => changeImportConverter(ev.target.value)}
              style={{
                background: 'var(--bg-1)', color: 'var(--fg)',
                border: '1px solid var(--line)', borderRadius: 2,
                padding: '2px 6px', fontFamily: 'var(--mono)', fontSize: 11,
              }}
            >
              <option value="markitdown">markitdown (default)</option>
            </select>
            <span style={{ opacity: 0.65 }}>
              Python markitdown CLI (python3.12 on Windows).
            </span>
          </div>
          <div
            onDragEnter={(ev) => { ev.preventDefault(); ev.stopPropagation(); setImportDragActive(true); }}
            onDragOver={(ev) => { ev.preventDefault(); ev.stopPropagation(); setImportDragActive(true); }}
            onDragLeave={(ev) => { ev.preventDefault(); ev.stopPropagation(); setImportDragActive(false); }}
            onDrop={handleImportDrop}
            onClick={() => importInputRef.current?.click()}
            style={{
              marginTop: 12,
              minHeight: 138,
              border: `1px dashed ${importDragActive ? 'var(--accent)' : 'var(--line-2)'}`,
              background: importDragActive
                ? 'color-mix(in oklch, var(--accent) 14%, transparent)'
                : 'color-mix(in oklch, var(--bg-1) 62%, transparent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              cursor: 'pointer',
              padding: 18,
            } as CSSProperties}
          >
            <div>
              <div style={{ color: importDragActive ? 'var(--accent)' : 'var(--fg)', fontSize: 15, fontWeight: 800 }}>
                {importDragActive ? t.dropHere : t.uploadImportTitle}
              </div>
              <div style={{ marginTop: 6, color: 'var(--fg-mute)', fontSize: 12 }}>
                {t.dropHere} · {t.chooseFiles}
              </div>
              <button
                className="mini-btn"
                type="button"
                disabled={importBusy}
                onClick={(ev: MouseEvent<HTMLButtonElement>) => {
                  ev.stopPropagation();
                  importInputRef.current?.click();
                }}
                style={{ marginTop: 12 }}
              >
                {importBusy ? t.importing : t.chooseFiles}
              </button>
            </div>
          </div>
          <ImportStatusBanner importStatus={importStatus} importBusy={importBusy} setImportStatus={setImportStatus} />
          <ImportedFilesList t={t} importedFiles={importedFiles} setImportedFiles={setImportedFiles} />
        </div>
        )}

        {showExportCard && (
        <div style={{
          border: '1px solid var(--line)',
          background: 'color-mix(in oklch, var(--bg-2) 58%, transparent)',
          padding: 14,
        }}>
          <div style={{ color: 'var(--fg)', fontSize: 14, fontWeight: 800 }}>{t.exportTitle}</div>
          <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45 }}>
            {t.exportDetail}
          </div>
          <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8 }}>
            <button className="mini-btn" type="button" onClick={() => exportSsot('md')}>{t.exportMd}</button>
            <button className="mini-btn" type="button" onClick={() => exportSsot('docx')}>{t.exportDocx}</button>
            <button className="mini-btn" type="button" onClick={() => exportSsot('html')}>{t.exportHtml}</button>
          </div>
        </div>
        )}
      </div>
    </div>
  );
}

// ── <ChecklistImportInline> — the compact import status + imported-files
// readout shown inside the checklist's "1. Import" action card (legacy lines
// 1246-1295). This is a SEPARATE inline markup from ImportStatusBanner /
// ImportedFilesList (different paddings / colors / icons), lifted verbatim so
// the checklist panel stays byte-identical. ──
export interface ChecklistImportInlineProps {
  importStatus: string;
  importBusy: boolean;
  importedFiles: ImportedFileRow[];
  setImportStatus: (value: string) => void;
  setImportedFiles: SetImportedFiles;
}
export function ChecklistImportInline({
  importStatus,
  importBusy,
  importedFiles,
  setImportStatus,
  setImportedFiles,
}: ChecklistImportInlineProps) {
  return (
    <>
      {importStatus ? (() => {
        const failed = importStatus.toLowerCase().includes('fail');
        const importing = importBusy;
        const color = failed ? 'var(--err)' : importing ? 'var(--warn)' : 'var(--ok)';
        const icon = failed ? '✕' : importing ? '⟳' : '✓';
        return (
          <div style={{
            marginTop: 8, padding: '6px 8px',
            border: `1px solid ${color}`, borderRadius: 2,
            color, background: `color-mix(in oklch, ${color} 12%, transparent)`,
            fontSize: 11, fontWeight: 600,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span style={{ fontSize: 13 }}>{icon}</span>
            <span style={{ flex: 1 }}>{importStatus}</span>
            <button type="button" onClick={() => setImportStatus('')}
              style={{ background: 'transparent', border: 'none', color, cursor: 'pointer', fontSize: 12, padding: 0 }}>×</button>
          </div>
        );
      })() : null}
      {importedFiles.length > 0 ? (
        <div style={{ marginTop: 8, padding: '6px 8px', border: '1px solid var(--line)', borderRadius: 2, background: 'var(--bg-2)', fontSize: 11, fontFamily: 'var(--mono)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
            <span>📥 Imported · {importedFiles.length}</span>
            <button type="button" onClick={() => setImportedFiles([])}
              style={{ background: 'transparent', border: '1px solid var(--line)', color: 'var(--fg-mute)', cursor: 'pointer', fontSize: 10, padding: '1px 5px', borderRadius: 2 }}>clear</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {importedFiles.map((f, i) => (
              <div key={`${f.md_path || f.original_path || f.name}-${f.ts || i}`} style={{ display: 'grid', gridTemplateColumns: '14px minmax(0, 1fr) auto', alignItems: 'center', gap: 6, padding: '3px 4px', color: 'var(--fg)' }}>
                <span style={{ color: f.error ? 'var(--err)' : f.pending ? 'var(--warn)' : 'var(--ok)', fontWeight: 700 }}>
                  {f.error ? '✕' : f.pending ? '⟳' : '✓'}
                </span>
                <div style={{ minWidth: 0 }}>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={f.name}>{f.name}</div>
                  {f.pending || f.error || f.md_path || f.original_path ? (
                    <div className="mute" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 10 }} title={f.md_path || f.original_path || ''}>
                      {f.pending ? 'uploading...' : f.error ? 'upload failed' : (f.md_path || f.original_path)}
                    </div>
                  ) : null}
                </div>
                <span className="mute" style={{ fontSize: 10 }}>
                  {f.bytes ? (f.bytes < 1024 ? `${f.bytes}B` : `${(f.bytes/1024).toFixed(1)}K`) : ''}
                  {f.image_count ? ` · ${f.image_count} img` : ''}
                  {f.visual_count ? ` · ${f.visual_count} visual` : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}

// ── <RequirementsGrid> — the "Q&A cards" + "Open Q&A now" two-column grid
// shown in the checklist when requirementTotal > 0 (legacy lines 1328-1391).
// Pure presentation over the derived requirement/missing rows. ──
export interface RequirementRow {
  key: string;
  label: string;
  help: string;
  status?: string;
}
export interface MissingRow {
  key: string;
  label: string;
  help: string;
}
export interface RequirementsGridProps {
  t: SsotQaStrings;
  requirementRows: RequirementRow[];
  missingRows: MissingRow[];
}
export function RequirementsGrid({ t, requirementRows, missingRows }: RequirementsGridProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
      gap: 12,
      marginTop: 14,
      borderTop: '1px solid var(--line)',
      paddingTop: 12,
    }}>
      <div>
        <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 800, marginBottom: 8 }}>{t.needTitle}</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 7 }}>
          {requirementRows.map(row => {
            const isMissing = row.status === 'missing';
            return (
              <div
                key={row.key}
                style={{
                  border: '1px solid var(--line)',
                  borderLeft: `3px solid ${isMissing ? 'var(--warn)' : 'var(--ok)'}`,
                  padding: '7px 8px',
                  background: isMissing
                    ? 'color-mix(in oklch, var(--warn) 6%, transparent)'
                    : 'color-mix(in oklch, var(--ok) 5%, transparent)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AtlasStatusBadge status={isMissing ? 'pending' : 'approved'} label={isMissing ? t.missing : t.filled} compact soft />
                  <span style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {row.label}
                  </span>
                </div>
                <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4 } as CSSProperties}>
                  {row.help}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div>
        <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 800, marginBottom: 8 }}>{t.missingTitle}</div>
        {missingRows.length ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
            {missingRows.map(row => (
              <div
                key={row.key}
                style={{
                  border: '1px solid color-mix(in oklch, var(--warn) 45%, var(--line))',
                  background: 'color-mix(in oklch, var(--warn) 8%, transparent)',
                  padding: '7px 8px',
                }}
              >
                <div style={{ color: 'var(--warn)', fontSize: 12, fontWeight: 800 }}>{row.label}</div>
                <div style={{ marginTop: 4, color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4 } as CSSProperties}>{row.help}</div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: 'var(--ok)', fontSize: 12, lineHeight: 1.45 }}>{t.missingEmpty}</div>
        )}
      </div>
    </div>
  );
}

// ── <QaActionCards> — the Deep Interview / To SSOT two-card row shown when
// the board is in the plain (non-checklist, non-checklistOnly) mode (legacy
// lines 1420-1463). Depends only on t + the run-command callback. ──
export interface QaActionCardsProps {
  t: SsotQaStrings;
  ip: string;
  runSsotCommand: (cmd: string) => void;
}
export function QaActionCards({ t, ip, runSsotCommand }: QaActionCardsProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: 12,
    }}>
      <div style={{
        border: '1px solid var(--line)',
        borderTop: '2px solid var(--warn)',
        background: 'color-mix(in oklch, var(--bg-2) 58%, transparent)',
        padding: 12,
      }}>
        <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 800 }}>{t.actionInterviewTitle}</div>
        <div style={{ color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45, marginTop: 5 }}>{t.actionInterviewDetail}</div>
        <button
          className="mini-btn"
          type="button"
          onClick={() => runSsotCommand(`/grill-me ${ip}`)}
          title="Run /grill-me for unresolved SSOT decisions"
          style={{ marginTop: 10 }}
        >
          {t.deepInterview}
        </button>
      </div>
      <div style={{
        border: '1px solid var(--line)',
        borderTop: '2px solid var(--ok)',
        background: 'color-mix(in oklch, var(--bg-2) 58%, transparent)',
        padding: 12,
      }}>
        <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 800 }}>{t.actionToSsotTitle}</div>
        <div style={{ color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45, marginTop: 5 }}>{t.actionToSsotDetail}</div>
        <button
          className="mini-btn"
          type="button"
          onClick={() => runSsotCommand(`/to-ssot ${ip}`)}
          title="Run /to-ssot for this IP"
          style={{ marginTop: 10 }}
        >
          {t.toSsot}
        </button>
      </div>
    </div>
  );
}

// ── Transitional bridge: register on window for call-time resolution. ──
g.SsotImportStatusBanner = ImportStatusBanner;
g.SsotImportedFilesList = ImportedFilesList;
g.SsotValidationScriptCard = ValidationScriptCard;
g.SsotImportExportPane = ImportExportPane;
g.SsotChecklistImportInline = ChecklistImportInline;
g.SsotRequirementsGrid = RequirementsGrid;
g.SsotQaActionCards = QaActionCards;
