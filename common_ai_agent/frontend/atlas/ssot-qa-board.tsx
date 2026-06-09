// ssot-qa-board.tsx — TypeScript migration of ssot-qa-board.jsx (Phase 13f /
// TS-split). Renders the Q&A workbench panel (questions tab).
//
// Originally a single 1717-line mega-root. To get every file < 1000 lines
// without changing behavior, the least-coupled seams were lifted into siblings:
//   - ssot-qa-board-i18n.tsx   → the pure uiLang→strings dictionaries.
//   - ssot-qa-board-qacard.tsx → the QA-card render subtree + pure pending
//                                 helpers (also used by the global submit bar).
//   - ssot-qa-board-io.tsx     → the import / export / validation UI.
// This file keeps the root <SsotQaBoard> component, all hook state, derivation,
// and the import/upload/export/validate handlers (closure-coupled to state).
//
// Cross-file deps owned by the (unmigrated) workspace.jsx are read through
// window at call time via the lambda forward-ref pattern, exactly as the legacy
// IIFE header did. This file's OWN public global window.SsotQaBoard is bridged
// at the bottom so the (still-live) legacy .jsx consumers keep resolving it.
//
// Within this file's own family, the i18n / qacard / io pieces are consumed
// through window bridges (resolved at call time) to avoid any module-eval
// ordering assumptions — same defensive stance the legacy lambdas took.
import {
  useState,
  useEffect,
  useRef,
  useCallback,
  type CSSProperties,
  type DragEvent,
} from 'react';

// Side-effect imports — these siblings register their window bridges
// (buildSsotQaStrings, SsotQaCard / ssotPendingDraft / ssotBuildPendingInputText,
// SsotImportStatusBanner / SsotImportedFilesList / SsotImportExportPane, …) on
// `window` at module-eval time. The legacy .jsx kept every helper in one IIFE
// scope; the .tsx split moved them into siblings, so this file MUST pull them in
// as runtime imports (the `import type` lines below are erased and run nothing).
// main.tsx only side-effect-imports "./ssot-qa-board", relying on it to
// transitively load its own split family — exactly as the entry header promises.
import './ssot-qa-board-i18n';
import './ssot-qa-board-qacard';
import './ssot-qa-board-io';

import type { SsotQaStrings, RequirementText, UiLang } from './ssot-qa-board-i18n';
import type { QaItem, QaDraft, AnswerDrafts } from './ssot-qa-board-qacard';
import type { ImportedFileRow, ValidationResult } from './ssot-qa-board-io';

// ── Window surface: workspace.jsx forward-refs + this family's bridges. ──
interface SsotQaWindowGlobals {
  // workspace.jsx helpers (resolved at call time).
  AskUserQuestionBlock: (...a: any[]) => any;
  AtlasStatusBadge: (...a: any[]) => any;
  atlasStatusMeta: (...a: any[]) => { color: string; [k: string]: unknown };
  normalizeUiSession: (...a: any[]) => string;
  ssotIpFromSession: (...a: any[]) => string;
  // i18n family (ssot-qa-board-i18n.tsx).
  buildSsotQaStrings: (uiLang: UiLang) => SsotQaStrings;
  buildRequirementHelp: (uiLang: UiLang) => RequirementText;
  buildRequirementSimpleName: (uiLang: UiLang) => RequirementText;
  // qacard family (ssot-qa-board-qacard.tsx).
  SsotQaCard: (props: any) => any;
  ssotPendingDraft: (item: QaItem | null | undefined, answerDrafts: AnswerDrafts) => QaDraft;
  ssotHasPendingAnswer: (draft: QaDraft | null | undefined) => boolean;
  ssotBuildPendingInputText: (item: QaItem, draft: QaDraft, ip: string) => string;
  // io family (ssot-qa-board-io.tsx).
  SsotValidationScriptCard: (props: any) => any;
  SsotImportExportPane: (props: any) => any;
  SsotChecklistImportInline: (props: any) => any;
  SsotRequirementsGrid: (props: any) => any;
  SsotQaActionCards: (props: any) => any;
  // This file's own bridge.
  SsotQaBoard: (props: SsotQaBoardProps) => any;
}
const g = window as unknown as SsotQaWindowGlobals;

// Forward-ref to workspace.jsx helpers (resolved at call time):
const AtlasStatusBadge = (...a: any[]): any => g.AtlasStatusBadge(...a);
const normalizeUiSession = (...a: any[]): string => g.normalizeUiSession(...a);
const ssotIpFromSession = (...a: any[]): string => g.ssotIpFromSession(...a);
// Family bridges (resolved at call time, so load order is irrelevant):
const buildSsotQaStrings = (uiLang: UiLang): SsotQaStrings => g.buildSsotQaStrings(uiLang);
const buildRequirementHelp = (uiLang: UiLang): RequirementText => g.buildRequirementHelp(uiLang);
const buildRequirementSimpleName = (uiLang: UiLang): RequirementText => g.buildRequirementSimpleName(uiLang);
const QaCard = (props: any): any => g.SsotQaCard(props);
const pendingDraft = (item: QaItem | null | undefined, answerDrafts: AnswerDrafts): QaDraft =>
  g.ssotPendingDraft(item, answerDrafts);
const hasPendingAnswer = (draft: QaDraft | null | undefined): boolean => g.ssotHasPendingAnswer(draft);
const buildPendingInputText = (item: QaItem, draft: QaDraft, ip: string): string =>
  g.ssotBuildPendingInputText(item, draft, ip);
const ValidationScriptCard = (props: any): any => g.SsotValidationScriptCard(props);
const ImportExportPane = (props: any): any => g.SsotImportExportPane(props);
const ChecklistImportInline = (props: any): any => g.SsotChecklistImportInline(props);
const RequirementsGrid = (props: any): any => g.SsotRequirementsGrid(props);
const QaActionCards = (props: any): any => g.SsotQaActionCards(props);

// ── Loose backend-shaped data / props types (permissive during glue era) ──
export interface SsotSectionData {
  id?: string;
  title?: string;
  pending?: QaItem[];
  approved?: QaItem[];
  [k: string]: unknown;
}
export interface SsotBoardData {
  ip?: string;
  session?: string;
  approved?: boolean;
  sections?: SsotSectionData[];
  summary?: { total?: number; approved?: number; pending?: number };
  requirements?: {
    items?: any[];
    missing_keys?: string[];
    total?: number;
    missing?: number;
    filled?: number;
  };
  imports?: any[];
  [k: string]: unknown;
}
export interface SsotSessionRow {
  session?: string;
  ip?: string;
  approved?: boolean;
  status?: string;
  workflow?: string;
  summary?: { approved?: number; pending?: number };
  [k: string]: unknown;
}
export interface SsotQaBoardProps {
  data?: SsotBoardData;
  sessions?: SsotSessionRow[];
  activeSession?: string;
  uiLang?: UiLang;
  onSelectSession?: (row: SsotSessionRow) => void;
  onBack?: () => void;
  onRefresh?: () => void;
  onRunCommand?: (cmd: string) => void;
  onSubmitPending?: (bundle: Array<{ item: QaItem; draft: QaDraft }>, text: string) => void;
  showChecklist?: boolean;
  checklistOnly?: boolean;
  importExportOnly?: boolean;
  importOnly?: boolean;
  exportOnly?: boolean;
}

export function SsotQaBoard({
  data,
  sessions,
  activeSession,
  uiLang = 'ko',
  onSelectSession,
  onBack,
  onRefresh,
  onRunCommand,
  onSubmitPending,
  showChecklist = false,
  checklistOnly = false,
  importExportOnly = false,
  importOnly = false,
  exportOnly = false,
}: SsotQaBoardProps) {
  const sections: SsotSectionData[] = Array.isArray(data?.sections) ? data!.sections! : [];
  const sessionRows: SsotSessionRow[] = Array.isArray(sessions) ? sessions : [];
  const summary = data?.summary || { total: 0, approved: 0, pending: 0 };
  const requirements = data?.requirements || {};
  const requirementItems: any[] = Array.isArray(requirements.items) ? requirements.items : [];
  const missingRequirementKeys: string[] = Array.isArray(requirements.missing_keys)
    ? requirements.missing_keys
    : requirementItems.filter(item => item?.status === 'missing').map(item => item.key);
  const requirementTotal = Number(requirements.total || requirementItems.length || 0);
  const requirementMissing = Number(requirements.missing ?? missingRequirementKeys.length ?? 0);
  const requirementFilled = Number(requirements.filled ?? Math.max(0, requirementTotal - requirementMissing));
  const noRecordedQa = requirementTotal <= 0;
  const requirementPct = requirementTotal > 0
    ? Math.max(0, Math.min(100, Math.round((requirementFilled / requirementTotal) * 100)))
    : 100;
  const hasIp = !!data?.ip;
  const activeSessionNorm = normalizeUiSession(activeSession || data?.session || '');
  const activeOwner = activeSessionNorm.split('/').filter(Boolean)[0] || '';
  const activeIp = data?.ip || ssotIpFromSession(activeSessionNorm) || '';
  const currentSessionRows = sessionRows.filter(row => {
    const rowSession = normalizeUiSession(row?.session || '');
    const rowParts = rowSession.split('/').filter(Boolean);
    const rowOwner = rowParts[0] || '';
    const rowIp = row?.ip || ssotIpFromSession(rowSession) || '';
    const sameOwner = !activeOwner || !rowOwner || rowOwner === activeOwner;
    const sameIp = !activeIp || rowIp === activeIp;
    return sameOwner && sameIp;
  });
  const t: SsotQaStrings = buildSsotQaStrings(uiLang);
  const requirementHelp: RequirementText = buildRequirementHelp(uiLang);
  const requirementSimpleName: RequirementText = buildRequirementSimpleName(uiLang);
  const requirementByKey = new Map<string, any>(requirementItems.map(item => [item?.key, item || {}]));
  const requirementLabel = (key: string): string => requirementSimpleName[key] || requirementByKey.get(key)?.label || key;
  const requirementRows = (requirementItems.length ? requirementItems : missingRequirementKeys.map(key => ({ key, status: 'missing' })))
    .filter(item => item?.key)
    .map(item => ({
      key: item.key,
      label: requirementLabel(item.key),
      help: requirementHelp[item.key] || item.label || item.key,
      status: item.status || (missingRequirementKeys.includes(item.key) ? 'missing' : 'filled'),
    }));
  const missingRows = missingRequirementKeys.map(key => ({
    key,
    label: requirementLabel(key),
    help: requirementHelp[key] || requirementLabel(key),
  }));
  const readyForRtl = !noRecordedQa && requirementMissing === 0 && !!data?.approved;
  const filledButNeedsSsot = !noRecordedQa && requirementMissing === 0 && !data?.approved;
  const rtlReadinessText = noRecordedQa
    ? t.noQaNeeded
    : (readyForRtl
    ? t.readyToGenerate
    : (filledButNeedsSsot ? t.needsSsotApproval : t.blockedByMissing));
  const nextActionText = noRecordedQa
    ? t.noQaNextAction
    : (requirementMissing > 0
    ? (uiLang === 'en'
      ? `${requirementMissing} Q&A card${requirementMissing === 1 ? '' : 's'} are still open. Flow: Import, Deep Interview, To SSOT.`
      : `${requirementMissing}개 Q&A 카드가 아직 열려 있습니다. 흐름은 Import, Deep Interview, To SSOT입니다.`)
    : (data?.approved
      ? (uiLang === 'en' ? 'SSOT is ready. RTL generation can use it.' : 'SSOT가 준비됐습니다. RTL 생성에 사용할 수 있습니다.')
      : (uiLang === 'en' ? 'Run To SSOT to document the completed Q&A.' : 'To SSOT로 완료된 Q&A를 문서화하세요.')));
  const uploadDoneText = (count: number): string => (
    uiLang === 'en'
      ? `${count} file${count === 1 ? '' : 's'} saved under ${data!.ip}/req/imports/; /import started.`
      : `${count}개 파일을 ${data!.ip}/req/imports/에 저장하고 /import를 실행했습니다.`
  );
  const importInputRef = useRef<HTMLInputElement>(null);
  const [importBusy, setImportBusy] = useState(false);
  const [importStatus, setImportStatus] = useState('');
  // Document → markdown converter pick. Server is authoritative; fetch
  // once on mount and write back on user change.
  const [importConverter, setImportConverter] = useState('markitdown');
  useEffect(() => {
    let cancelled = false;
    fetch('/api/ssot/import/converter')
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (cancelled || !d || !d.converter) return;
        setImportConverter(String(d.converter));
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);
  const changeImportConverter = useCallback((next: string): void => {
    const choice = String(next || '').trim().toLowerCase();
    if (!choice) return;
    setImportConverter(choice);
    fetch('/api/ssot/import/converter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ converter: choice }),
    }).catch(() => {});
  }, []);
  const [importDragActive, setImportDragActive] = useState(false);
  const [validationMode, setValidationMode] = useState('engineering');
  const [validationBusy, setValidationBusy] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const importStorageKey = `atlas:ssot-imported-files:${activeSessionNorm || 'session'}:${data?.ip || 'ip'}`;
  const importStem = useCallback((item: ImportedFileRow): string => {
    const raw = (item && (item.name || item.md_path || item.original_path)) || '';
    const base = String(raw).split('/').pop() || '';
    return base.replace(/^\d+_\d+_/, '').replace(/\.(md|pdf)$/i, '').toLowerCase();
  }, []);
  const collapseImportRows = useCallback((rows: ImportedFileRow[]): ImportedFileRow[] => {
    const merged: ImportedFileRow[] = [];
    const stemIdx = new Map<string, number>();
    for (const item of rows) {
      if (!item) continue;
      const stem = importStem(item);
      const key = stem || item.md_path || item.original_path || item.name;
      if (!key) continue;
      if (stemIdx.has(key)) {
        const target = merged[stemIdx.get(key)!];
        if (!target.md_path && item.md_path) target.md_path = item.md_path;
        if (!target.original_path && item.original_path) target.original_path = item.original_path;
        if (!target.image_count && item.image_count) target.image_count = item.image_count;
        if (!target.visual_count && item.visual_count) target.visual_count = item.visual_count;
        if (item.bytes && (!target.bytes || item.bytes > target.bytes)) target.bytes = item.bytes;
        if (target.pending && !item.pending) {
          target.pending = false;
          target.error = item.error || target.error;
        }
        if (!target.error && item.error) target.error = item.error;
      } else {
        stemIdx.set(key, merged.length);
        merged.push({ ...item });
      }
    }
    return merged;
  }, [importStem]);
  const readStoredImportedFiles = useCallback((): ImportedFileRow[] => {
    try {
      const raw = window.localStorage.getItem(importStorageKey);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed.slice(0, 20) : [];
    } catch (_) {
      return [];
    }
  }, [importStorageKey]);
  const [importedFiles, setImportedFilesState] = useState<ImportedFileRow[]>(() => readStoredImportedFiles());
  const setImportedFiles = useCallback((
    updater: ImportedFileRow[] | ((prev: ImportedFileRow[]) => ImportedFileRow[]),
  ): void => {
    setImportedFilesState(prev => {
      const nextRaw = typeof updater === 'function' ? (updater as (p: ImportedFileRow[]) => ImportedFileRow[])(prev) : updater;
      const next = Array.isArray(nextRaw) ? nextRaw.slice(0, 20) : [];
      try {
        if (next.length) window.localStorage.setItem(importStorageKey, JSON.stringify(next));
        else window.localStorage.removeItem(importStorageKey);
      } catch (_) {}
      return next;
    });
  }, [importStorageKey]);
  useEffect(() => {
    const backendImports: any[] = Array.isArray(data?.imports) ? data!.imports! : [];
    if (!backendImports.length) {
      setImportedFilesState(readStoredImportedFiles());
      return;
    }
    const normalized: ImportedFileRow[] = backendImports.map((item, idx) => ({
      name: item.name || String(item.path || item.md_path || item.original_path || '').split('/').pop(),
      bytes: item.bytes || 0,
      md_path: item.md_path || (String(item.path || '').endsWith('.md') ? item.path : ''),
      original_path: item.original_path || item.path || '',
      image_count: item.image_count || (Array.isArray(item.image_paths) ? item.image_paths.length : 0),
      visual_count: item.visual_count || (Array.isArray(item.visual_paths) ? item.visual_paths.length : 0),
      pending: false,
      error: !!item.convert_error,
      ts: item.updated_at || item.mtime || idx,
    })).filter(item => item.name || item.md_path || item.original_path);
    setImportedFiles(prev => collapseImportRows([...normalized, ...prev]).slice(0, 20));
  }, [data?.imports, readStoredImportedFiles, setImportedFiles, collapseImportRows]);
  const runSsotCommand = (cmd: string): void => {
    const text = String(cmd || '').trim();
    if (!text || !onRunCommand) return;
    onRunCommand(text);
  };
  const readFileAsBase64 = (file: File): Promise<string> => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const raw = String(reader.result || '');
      resolve(raw.includes(',') ? raw.split(',').pop()! : raw);
    };
    reader.onerror = () => reject(reader.error || new Error('file read failed'));
    reader.readAsDataURL(file);
  });
  const uploadImportFiles = async (fileList: FileList | File[] | null): Promise<void> => {
    const files = Array.from(fileList || []);
    if (!files.length || !data?.ip) return;
    const uploadStartedAt = Date.now();
    setImportBusy(true);
    setImportStatus(uiLang === 'en' ? `Uploading ${files.length} file${files.length === 1 ? '' : 's'}...` : `${files.length}개 파일 업로드 중...`);
    setImportedFiles(prev => {
      const queued: ImportedFileRow[] = files.map((file, idx) => ({
        name: file.name,
        bytes: file.size || 0,
        md_path: '',
        original_path: '',
        image_count: 0,
        visual_count: 0,
        pending: true,
        ts: uploadStartedAt + idx,
      }));
      return [...queued, ...prev].slice(0, 20);
    });
    try {
      const payloadFiles = await Promise.all(files.map(async file => ({
        name: file.name,
        content_b64: await readFileAsBase64(file),
      })));
      const res = await fetch('/api/ssot/import/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip: data.ip,
          session: activeSessionNorm || '',
          files: payloadFiles,
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok || !payload?.ok) {
        throw new Error(payload?.error || `upload failed (${res.status})`);
      }
      setImportStatus(uploadDoneText((payload.paths || []).length));
      const saved: any[] = Array.isArray(payload.saved) && payload.saved.length
        ? payload.saved
        : (Array.isArray(payload.paths) ? payload.paths.map((path: string) => ({ name: String(path || '').split('/').pop(), original_path: path })) : []);
      if (saved.length) {
        setImportedFiles(prev => {
          const next = collapseImportRows(saved.map(s => ({
            name: s.name || '',
            bytes: s.bytes || 0,
            md_path: s.md_path || '',
            original_path: s.original_path || '',
            image_count: Array.isArray(s.image_paths) ? s.image_paths.length : 0,
            visual_count: Array.isArray(s.visual_paths) ? s.visual_paths.length : 0,
            pending: false,
            ts: Date.now(),
          })));
          const nextStems = new Set(next.map(f => importStem(f)).filter(Boolean));
          const previous = prev.filter(f => {
            if (f.pending && Number(f.ts || 0) >= uploadStartedAt && Number(f.ts || 0) < uploadStartedAt + files.length + 1) return false;
            return !nextStems.has(importStem(f));
          });
          return collapseImportRows([...next, ...previous]).slice(0, 20);
        });
      }
      if (payload.command) runSsotCommand(payload.command);
      setTimeout(() => { try { onRefresh && onRefresh(); } catch (_) {} }, 600);
    } catch (err: any) {
      setImportStatus(String(err?.message || err || 'upload failed'));
      setImportedFiles(prev => prev.map(f => (
        f.pending && Number(f.ts || 0) >= uploadStartedAt && Number(f.ts || 0) < uploadStartedAt + files.length + 1
          ? { ...f, pending: false, error: true }
          : f
      )));
    } finally {
      setImportBusy(false);
    }
  };
  const exportSsot = (format: string): void => {
    const fmt = String(format || '').trim();
    if (!fmt || !data?.ip) return;
    window.location.href = `/api/ssot/export?ip=${encodeURIComponent(data.ip)}&format=${encodeURIComponent(fmt)}`;
  };
  const runValidation = async (): Promise<void> => {
    if (!data?.ip || validationBusy) return;
    setValidationBusy(true);
    setValidationResult(null);
    try {
      const res = await fetch('/api/ssot/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: data.ip, mode: validationMode, session: activeSessionNorm || '' }),
      });
      const payload = await res.json().catch(() => ({}));
      setValidationResult({
        ok: !!payload.ok,
        mode: payload.mode || validationMode,
        returncode: payload.returncode,
        elapsed_ms: payload.elapsed_ms,
        command: payload.command || '',
        output: [payload.stdout || '', payload.stderr || '', payload.error || ''].filter(Boolean).join('\n').trim(),
      });
    } catch (err: any) {
      setValidationResult({
        ok: false,
        mode: validationMode,
        returncode: '',
        elapsed_ms: '',
        command: '',
        output: String(err?.message || err || 'validation failed'),
      });
    } finally {
      setValidationBusy(false);
    }
  };
  const handleImportDrop = (ev: DragEvent<HTMLDivElement>): void => {
    ev.preventDefault();
    ev.stopPropagation();
    setImportDragActive(false);
    uploadImportFiles(ev.dataTransfer?.files || null);
  };
  // All QA cards (pending AND approved) default to expanded. Track the
  // *closed* set so newly-streamed items inherit the open-by-default rule.
  const [closedCardKeys, setClosedCardKeys] = useState<Set<string>>(() => new Set());
  const [answerDrafts, setAnswerDrafts] = useState<AnswerDrafts>({});
  // Active section tab — null means "first section with pending items, else first section".
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  // Per-status group collapse: both groups default open. Tracking the
  // closed set keeps the default-open rule stable across re-renders.
  const [closedStatusGroups, setClosedStatusGroups] = useState<Set<string>>(() => new Set());
  const draftOf = (item: QaItem): QaDraft => pendingDraft(item, answerDrafts);
  const updatePendingDraft = (item: QaItem, draft: QaDraft): void => {
    const key = [
      item?.flow_id || '',
      item?.section || item?.section_id || '',
      item?.decision_key || item?.source || item?.question || '',
    ].join(':');
    setAnswerDrafts(prev => ({ ...prev, [key]: draft }));
  };
  // <QaCard> replaces the legacy renderQa(item, status) closure; pure render
  // helpers + the card subtree now live in ssot-qa-board-qacard.tsx.
  const renderQa = (item: QaItem, status: string) => (
    <QaCard
      key={[
        item?.flow_id || '',
        item?.section || item?.section_id || '',
        item?.decision_key || item?.source || item?.question || '',
      ].join(':')}
      item={item}
      status={status}
      t={t}
      ip={data?.ip || activeIp || 'current IP'}
      answerDrafts={answerDrafts}
      closedCardKeys={closedCardKeys}
      setClosedCardKeys={setClosedCardKeys}
      updatePendingDraft={updatePendingDraft}
      onSubmitPending={onSubmitPending}
    />
  );

  if (!hasIp) {
    return (
      <div style={{ padding: 20, color: 'var(--fg-mute)', fontSize: 12, fontFamily: 'var(--mono)' }}>
        <div style={{ marginBottom: 8, color: 'var(--fg)' }}>{t.noSession}</div>
        <div>{t.selectSession} <code style={{ color: 'var(--cyan)' }}>ssot-gen</code>.</div>
        <div style={{ marginTop: 12 }}>
          <button className="mini-btn" type="button" onClick={onBack}>{t.back}</button>
        </div>
      </div>
    );
  }

  if (importExportOnly || importOnly || exportOnly) {
    return (
      <ImportExportPane
        t={t}
        ip={data!.ip!}
        importExportOnly={importExportOnly}
        importOnly={importOnly}
        exportOnly={exportOnly}
        importInputRef={importInputRef}
        importConverter={importConverter}
        importDragActive={importDragActive}
        importBusy={importBusy}
        importStatus={importStatus}
        importedFiles={importedFiles}
        onRefresh={onRefresh}
        onBack={onBack}
        changeImportConverter={changeImportConverter}
        setImportDragActive={setImportDragActive}
        handleImportDrop={handleImportDrop}
        uploadImportFiles={uploadImportFiles}
        exportSsot={exportSsot}
        setImportStatus={setImportStatus}
        setImportedFiles={setImportedFiles}
      />
    );
  }

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
      {showChecklist ? (
      <div style={{
        border: '1px solid var(--line)',
        background: 'var(--bg-1)',
        paddingTop: 14,
        paddingRight: 14,
        paddingBottom: 100,
        paddingLeft: 14,
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 360px', minWidth: 260 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <div style={{ color: 'var(--fg)', fontSize: 16, fontWeight: 800 }}>{t.checklistTitle}</div>
              <code className="acc">{data!.ip}</code>
              <AtlasStatusBadge
                status={readyForRtl ? 'approved' : (requirementMissing ? 'pending' : 'draft')}
                label={readyForRtl ? t.approved : (requirementMissing ? t.missing : (noRecordedQa ? t.noQaShort : t.draft))}
                compact
                soft
              />
            </div>
            <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45, maxWidth: 820 }}>
              {t.checklistSubtitle}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <button className="mini-btn" type="button" onClick={onRefresh}>{t.refresh}</button>
            <button className="mini-btn" type="button" onClick={onBack}>{t.chat}</button>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 12,
          marginTop: 14,
          alignItems: 'stretch',
        }}>
          <div style={{
            border: '1px solid var(--line)',
            background: 'color-mix(in oklch, var(--bg-2) 72%, transparent)',
            padding: 10,
          }}>
            <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginBottom: 6 } as CSSProperties}>{t.rtlReadiness}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <div style={{ color: readyForRtl ? 'var(--ok)' : (requirementMissing ? 'var(--warn)' : 'var(--cyan)'), fontSize: 34, fontWeight: 800, lineHeight: 1 }}>
                {requirementPct}%
              </div>
              <div style={{ color: 'var(--fg-mute)', fontSize: 12 }}>
                {noRecordedQa ? t.noQaShort : `${requirementFilled}/${requirementTotal || 0} ${t.filled}`}
              </div>
            </div>
            <div style={{
              height: 8,
              marginTop: 8,
              border: '1px solid var(--line)',
              background: 'var(--bg-0)',
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${requirementPct}%`,
                height: '100%',
                background: readyForRtl ? 'var(--ok)' : (requirementMissing ? 'var(--warn)' : 'var(--cyan)'),
              }} />
            </div>
            <div style={{ marginTop: 8, color: 'var(--fg)', fontSize: 12, lineHeight: 1.45 }}>
              {rtlReadinessText}
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 9 }}>
              <AtlasStatusBadge status="total" label={t.total} count={summary.total || 0} compact soft />
              <AtlasStatusBadge status="approved" label={t.approved} count={summary.approved || 0} compact soft />
              <AtlasStatusBadge status="pending" label={t.pending} count={summary.pending || 0} compact soft />
            </div>
          </div>

          {checklistOnly ? (
            <ValidationScriptCard
              t={t}
              validationMode={validationMode}
              validationBusy={validationBusy}
              validationResult={validationResult}
              setValidationMode={setValidationMode}
              runValidation={runValidation}
            />
          ) : (
          <div style={{
            border: '1px solid var(--line)',
            background: 'color-mix(in oklch, var(--bg-2) 52%, transparent)',
            padding: 10,
          }}>
            <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginBottom: 6 } as CSSProperties}>{t.nextAction}</div>
            <div style={{ color: 'var(--fg)', fontSize: 13, lineHeight: 1.5 }}>{nextActionText}</div>
            <div style={{ marginTop: 12, color: 'var(--fg-mute)', fontSize: 11 }}>{t.feedTitle}</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 8, marginTop: 7 }}>
              <div style={{ borderTop: '2px solid var(--cyan)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionChatTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4, marginTop: 3 } as CSSProperties}>{t.actionChatDetail}</div>
                <button className="mini-btn" type="button" onClick={onBack} style={{ marginTop: 7 }}>{t.openChat}</button>
              </div>
              <div style={{ borderTop: '2px solid var(--accent)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionImportTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4, marginTop: 3 } as CSSProperties}>{t.actionImportDetail}</div>
                <button
                  className="mini-btn"
                  type="button"
                  disabled={importBusy}
                  onClick={() => importInputRef.current?.click()}
                  title="Upload requirement docs, notes, RTL, YAML, logs, or filelists into SSOT import evidence"
                  style={{ marginTop: 7 }}
                >
                  {importBusy ? t.importing : t.chooseFile}
                </button>
                <ChecklistImportInline
                  importStatus={importStatus}
                  importBusy={importBusy}
                  importedFiles={importedFiles}
                  setImportStatus={setImportStatus}
                  setImportedFiles={setImportedFiles}
                />
              </div>
              <div style={{ borderTop: '2px solid var(--warn)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionInterviewTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4, marginTop: 3 } as CSSProperties}>{t.actionInterviewDetail}</div>
                <button
                  className="mini-btn"
                  type="button"
                  onClick={() => runSsotCommand(`/grill-me ${data!.ip}`)}
                  title="Run /grill-me for unresolved SSOT decisions"
                  style={{ marginTop: 7 }}
                >
                  {t.deepInterview}
                </button>
              </div>
              <div style={{ borderTop: '2px solid var(--ok)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionToSsotTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4, marginTop: 3 } as CSSProperties}>{t.actionToSsotDetail}</div>
                <button
                  className="mini-btn"
                  type="button"
                  onClick={() => runSsotCommand(`/to-ssot ${data!.ip}`)}
                  title="Run /to-ssot for this IP"
                  style={{ marginTop: 7 }}
                >
                  {t.toSsot}
                </button>
              </div>
            </div>
          </div>
          )}
        </div>

        {requirementTotal > 0 ? (
          <RequirementsGrid t={t} requirementRows={requirementRows} missingRows={missingRows} />
        ) : null}
        {importStatus ? (
          <div style={{ marginTop: 10, color: importStatus.includes('failed') ? 'var(--warn)' : 'var(--fg-mute)', fontSize: 11 }}>
            {importStatus}
          </div>
        ) : null}
      </div>

      ) : (
        <div style={{
          border: '1px solid var(--line)',
          background: 'var(--bg-1)',
          padding: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <div style={{ color: 'var(--fg)', fontSize: 15, fontWeight: 800 }}>{t.title}</div>
            <code className="acc">{data!.ip}</code>
            <span style={{ flex: 1 }} />
            <AtlasStatusBadge status="approved" label={t.approved} count={summary.approved || 0} compact soft />
            <AtlasStatusBadge status="pending" label={t.pending} count={summary.pending || 0} compact soft />
            <button className="mini-btn" type="button" onClick={onRefresh}>{t.refresh}</button>
            <button className="mini-btn" type="button" onClick={onBack}>{t.chat}</button>
          </div>
          <div style={{ marginTop: 7, color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45 }}>
            {t.subtitle}
          </div>
        </div>
      )}

      {!showChecklist && !checklistOnly ? (
        <QaActionCards t={t} ip={data!.ip!} runSsotCommand={runSsotCommand} />
      ) : null}

      {!checklistOnly ? (
        <>
      <div style={{
        border: '1px solid var(--line)',
        padding: 10,
        background: 'color-mix(in oklch, var(--bg-1) 75%, transparent)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <div style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' } as CSSProperties}>
            {t.sessions}
          </div>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>{currentSessionRows.length} ssot-gen</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 8 }}>
          {currentSessionRows.length ? currentSessionRows.slice(0, 12).map(row => {
            const active = normalizeUiSession(row.session) === normalizeUiSession(activeSession || data!.session || '');
            const rowSummary = row.summary || {};
            return (
              <button
                key={row.session}
                type="button"
                onClick={() => onSelectSession && onSelectSession(row)}
                style={{
                  textAlign: 'left',
                  border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
                  background: active ? 'color-mix(in oklch, var(--accent) 12%, transparent)' : 'transparent',
                  color: 'var(--fg)',
                  padding: '8px 9px',
                  cursor: 'pointer',
                  fontFamily: 'var(--mono)',
                } as CSSProperties}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AtlasStatusBadge status={row.approved ? 'approved' : (row.status || 'draft')} compact />
                  <span style={{ flex: 1 }} />
                  <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>{row.workflow || 'ssot-gen'}</span>
                </div>
                <div style={{ marginTop: 5, fontSize: 12, color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {row.ip || '(no ip)'}
                </div>
                <div style={{ marginTop: 3, fontSize: 10, color: 'var(--fg-mute)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {row.session}
                </div>
                <div style={{ marginTop: 6, fontSize: 10 }}>
                  <AtlasStatusBadge status="approved" label={t.approved} count={rowSummary.approved || 0} compact soft />
                  <span style={{ color: 'var(--fg-mute)' }}> / </span>
                  <AtlasStatusBadge status="pending" label={t.pending} count={rowSummary.pending || 0} compact soft />
                </div>
              </button>
            );
          }) : (
            <div style={{ color: 'var(--fg-mute)', fontSize: 12 }}>{t.noSaved}</div>
          )}
        </div>
      </div>

      {sections.length ? (() => {
        const sectionsList = sections;
        // Resolve which section to show. If user clicked one, honor that.
        // Otherwise default to the first section that still has pending QAs,
        // falling back to the first section.
        const firstWithPending = sectionsList.find(s => (s.pending || []).length > 0);
        const fallbackId = (firstWithPending || sectionsList[0])?.id;
        const activeId = activeSectionId && sectionsList.some(s => s.id === activeSectionId)
          ? activeSectionId
          : fallbackId;
        const active = sectionsList.find(s => s.id === activeId) || sectionsList[0];
        // Collect all pending items across all sections for the global submit bar.
        const allPending = sectionsList.flatMap(s => (s.pending || []));
        const answerableAllPending = allPending.filter(item => hasPendingAnswer(draftOf(item)));
        const submitAll = (): void => {
          if (!onSubmitPending) return;
          if (!answerableAllPending.length) return;
          const bundle = answerableAllPending.map(item => ({ item, draft: draftOf(item) }));
          // Build a single combined prompt that lists every answered pending QA.
          const ip = data?.ip || activeIp || 'current IP';
          const header = `# Submit ${bundle.length} pending QA answer${bundle.length === 1 ? '' : 's'} for ${ip}`;
          const segments = bundle.map(({ item, draft }, i) => {
            const body = buildPendingInputText(item, draft, ip).replace(/^### .*\n?/, '');
            return `## [${i + 1}/${bundle.length}] ${item.decision_key || 'qa'}\n${body}`;
          });
          const combined = [header, '', ...segments].join('\n\n');
          onSubmitPending(bundle, combined);
        };
        return (
          <div style={{
            border: '1px solid var(--line)',
            background: 'var(--bg-1)',
            display: 'flex',
            flex: 1,
            minHeight: 0,
          }}>
            {/* Left column — section tabs (vertical) */}
            <div style={{
              width: 260,
              flex: '0 0 260px',
              borderRight: '1px solid var(--line)',
              padding: 10,
              minHeight: 0,
              overflowY: 'auto',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <div style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' } as CSSProperties}>
                  {t.toc}
                </div>
                <span style={{ flex: 1 }} />
                {onSubmitPending && allPending.length > 0 ? (
                  <button
                    type="button"
                    className="mini-btn"
                    disabled={!answerableAllPending.length}
                    title={answerableAllPending.length
                      ? `${t.send} all ${answerableAllPending.length} pending`
                      : t.sendNeedAnswer}
                    onClick={submitAll}
                    style={{
                      background: answerableAllPending.length ? 'var(--cyan)' : undefined,
                      color: answerableAllPending.length ? 'var(--bg-0)' : undefined,
                      fontWeight: answerableAllPending.length ? 600 : undefined,
                      opacity: answerableAllPending.length ? 1 : 0.45,
                      cursor: answerableAllPending.length ? 'pointer' : 'not-allowed',
                      fontSize: 10,
                    }}
                  >
                    {t.send} {answerableAllPending.length || ''}
                  </button>
                ) : null}
              </div>
              {sectionsList.map(section => {
                const pendingCount = (section.pending || []).length;
                const approvedCount = (section.approved || []).length;
                const isActive = section.id === activeId;
                return (
                  <button
                    key={section.id}
                    type="button"
                    onClick={() => setActiveSectionId(section.id ?? null)}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      border: '1px solid var(--line)',
                      borderLeft: `3px solid ${isActive
                        ? 'var(--cyan)'
                        : (pendingCount > 0 ? 'var(--warn)' : 'var(--ok)')}`,
                      background: isActive
                        ? 'color-mix(in oklch, var(--cyan) 8%, transparent)'
                        : 'transparent',
                      color: 'var(--fg)',
                      padding: '6px 8px',
                      cursor: 'pointer',
                      fontFamily: 'var(--mono)',
                      marginBottom: 4,
                    } as CSSProperties}
                  >
                    <div style={{ fontSize: 'var(--ui-control-font-size)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' } as CSSProperties}>
                      {section.title}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--fg-mute)', marginTop: 3 }}>
                      {approvedCount} {t.approved} / {pendingCount} {t.pending}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Right column — active section's QA cards */}
            <div style={{
              flex: 1,
              padding: 12,
              overflowY: 'auto',
              minWidth: 0,
              minHeight: 0,
            }}>
              {active ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 10 }}>
                    <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 700 }}>{active.title}</div>
                    <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                      {(active.approved || []).length} {t.approved} / {(active.pending || []).length} {t.pending}
                    </span>
                  </div>
                  {['pending', 'approved'].map(grp => {
                    const list = (grp === 'pending' ? active.pending : active.approved) || [];
                    if (!list.length) return null;
                    const collapsed = closedStatusGroups.has(grp);
                    const toggle = () => setClosedStatusGroups(prev => {
                      const next = new Set(prev);
                      if (next.has(grp)) next.delete(grp);
                      else next.add(grp);
                      return next;
                    });
                    return (
                      <div key={grp} style={{ marginBottom: grp === 'pending' ? 10 : 0 }}>
                        <div
                          role="button"
                          tabIndex={0}
                          onClick={toggle}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              toggle();
                            }
                          }}
                          style={{
                            marginBottom: 6,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            cursor: 'pointer',
                            userSelect: 'none',
                          }}
                          title={collapsed ? 'click to expand' : 'click to collapse'}
                        >
                          <span style={{ color: 'var(--fg-mute)', fontSize: 11 }}>
                            {collapsed ? '▶' : '▼'}
                          </span>
                          <AtlasStatusBadge
                            status={grp}
                            label={grp === 'pending' ? t.pending : t.approved}
                            count={list.length}
                            compact
                            soft
                          />
                        </div>
                        {!collapsed && list.map(item => renderQa(item, grp))}
                      </div>
                    );
                  })}
                </>
              ) : null}
            </div>
          </div>
        );
      })() : (
        <div style={{ padding: 20, color: 'var(--fg-mute)', fontSize: 12 }}>
          {t.noCards} <code style={{ color: 'var(--cyan)' }}>/new-ip</code> / <code style={{ color: 'var(--cyan)' }}>/grill-me</code>.
        </div>
      )}
        </>
      ) : null}
    </div>
  );
}

// ── ask_user — compact in-feed tool-call line ─────────────────────
// Renders as `action: ask_user(...)` matching the other tool calls,

// Phase 13f window export — workspace.jsx aliases this back.
(window as unknown as { SsotQaBoard: typeof SsotQaBoard }).SsotQaBoard = SsotQaBoard;
