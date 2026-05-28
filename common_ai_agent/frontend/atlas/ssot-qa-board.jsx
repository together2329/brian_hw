// ssot-qa-board.jsx — Phase 13f refactor: SsotQaBoard (~1691 lines)
// extracted from workspace.jsx as its own cluster. Renders the Q&A
// workbench panel (questions tab) — among the largest single-component
// extractions in the refactor (1691 lines, second only to the
// SsotDigestContent cluster's 950 lines).
//
// Load order (index.html): AFTER ssot-digest.jsx, BEFORE workspace.jsx.
// Uses the same lambda forward-ref + IIFE wrapper pattern as the
// earlier phases — only 5 workspace-scope helpers needed (the lowest
// dep count of any 13x extraction so far), so the IIFE header is short.

(() => {

// Forward-ref to workspace.jsx helpers (resolved at call time):
const AskUserQuestionBlock = (...a) => window.AskUserQuestionBlock(...a);
const AtlasStatusBadge = (...a) => window.AtlasStatusBadge(...a);
const atlasStatusMeta = (...a) => window.atlasStatusMeta(...a);
const normalizeUiSession = (...a) => window.normalizeUiSession(...a);
const ssotIpFromSession = (...a) => window.ssotIpFromSession(...a);


const SsotQaBoard = ({
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
}) => {
  const sections = Array.isArray(data?.sections) ? data.sections : [];
  const sessionRows = Array.isArray(sessions) ? sessions : [];
  const summary = data?.summary || { total: 0, approved: 0, pending: 0 };
  const requirements = data?.requirements || {};
  const requirementItems = Array.isArray(requirements.items) ? requirements.items : [];
  const missingRequirementKeys = Array.isArray(requirements.missing_keys)
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
  const t = uiLang === 'en'
    ? {
        noSession: 'No SSOT QA session selected.',
        selectSession: 'Select an IP/session that uses',
        back: 'back to chat',
        title: 'Q&A Session',
        subtitle: 'Answer questions here. The answers fill the SSOT promise sheet.',
        checklistTitle: 'Validation',
        checklistSubtitle: 'Track real Q&A blockers and the validator gate before generation.',
        legend: 'SSOT = design promise sheet. RTL = hardware code.',
        rtlReadiness: 'Q&A readiness',
        nextAction: 'What to do now',
        needTitle: 'Q&A cards',
        missingTitle: 'Open Q&A now',
        missingEmpty: 'No open Q&A.',
        noQaShort: 'No Q&A',
        noQaNeeded: 'No real Q&A blockers are recorded. Do not seed default questions.',
        noQaNextAction: 'If evidence is enough, stop or run To SSOT. Ask Q&A only for a real blocker.',
        readyToGenerate: 'Recorded Q&A is approved. Run validation before RTL generation.',
        needsSsotApproval: 'Recorded Q&A is complete. Press To SSOT to write the SSOT, then run validation.',
        blockedByMissing: 'Recorded Q&A is incomplete because some cards are still open.',
        feedTitle: 'Three-step SSOT flow',
        actionChatTitle: 'Optional notes = Chat',
        actionChatDetail: 'Use chat only for extra context.',
        actionImportTitle: '1. Import',
        actionImportDetail: 'Upload existing docs. Upload automatically imports them.',
        actionInterviewTitle: '2. Deep Interview',
        actionInterviewDetail: 'Ask only what import/wiki evidence cannot resolve.',
        actionToSsotTitle: '3. To SSOT',
        actionToSsotDetail: 'Approve current evidence and write the SSOT document.',
        chooseFile: 'choose file',
        openChat: 'open chat',
        filled: 'filled',
        missing: 'missing',
        refresh: 'refresh',
        chat: 'chat',
        total: 'total',
        approved: 'approved',
        pending: 'pending',
        requirements: 'requirements',
        requirementsRemaining: 'remaining',
        ssot: 'ssot',
        draft: 'draft',
        sessions: 'Current session',
        toc: 'Table of contents',
        none: 'No QA records yet.',
        noSaved: 'No QA records for this session/IP yet.',
        noCards: 'No section QA cards yet. Start',
        noAnswer: 'No answer captured yet.',
        useInput: 'use input',
        answer: 'answer',
        close: 'close',
        sendToInput: 'open input',
        selectOne: 'select one option',
        selectMany: 'select one or more options',
        typedAnswer: 'typed answer',
        customNote: 'custom note',
        noOptions: 'No options provided. Type an answer below.',
        autoInputHint: 'select or type here; chat input stays unchanged until send',
        inputUpdated: 'draft ready',
        send: 'send',
        sendNeedAnswer: 'select an option or type an answer first',
        importFiles: 'Import',
        importing: 'Importing...',
        deepInterview: 'Deep Interview',
        toSsot: 'To SSOT',
        importReady: 'uploaded',
        qaActionTitle: 'Next SSOT actions',
        importExportTitle: 'Import / Export',
        importExportSubtitle: 'Upload existing docs into SSOT import evidence, or export the current SSOT.',
        uploadImportTitle: 'Upload (Import)',
        uploadImportDetail: 'Drop files here or choose files. The imported list updates immediately.',
        dropHere: 'Drop files to upload',
        chooseFiles: 'choose files',
        importedList: 'Imported files',
        noImportedFiles: 'No imported files yet.',
        exportTitle: 'Export',
        exportDetail: 'Download the current SSOT artifact.',
        exportMd: 'Markdown',
        exportDocx: 'Word',
        exportHtml: 'HTML',
        validationScriptTitle: 'SSOT validator script',
        validationScriptDetail: 'Runs verify_ssot.py with --root; check_ssot_disk.sh is used when available.',
        validationMode: 'mode',
        runValidation: 'Run validation',
        validationPass: 'PASS',
        validationFail: 'FAIL',
      }
    : {
        noSession: '선택된 SSOT QA 세션이 없습니다.',
        selectSession: 'IP/session을 선택하세요:',
        back: '채팅으로',
        title: 'Q&A Session',
        subtitle: '여기는 질문에 답하는 곳입니다. 답변이 SSOT 약속장의 빈칸을 채웁니다.',
        checklistTitle: 'Validation',
        checklistSubtitle: '실제 Q&A blocker와 validator gate를 같이 봅니다.',
        legend: 'SSOT = 설계 약속장. RTL = 실제 회로 코드.',
        rtlReadiness: 'Q&A 준비 상태',
        nextAction: '지금 할 일',
        needTitle: 'Q&A 카드',
        missingTitle: '현재 열린 Q&A',
        missingEmpty: '열린 Q&A가 없습니다.',
        noQaShort: 'Q&A 없음',
        noQaNeeded: '실제 Q&A blocker가 기록되지 않았습니다. 기본 질문을 만들지 않습니다.',
        noQaNextAction: '근거가 충분하면 Stop 또는 To SSOT로 가세요. Q&A는 진짜 blocker일 때만 만듭니다.',
        readyToGenerate: '기록된 Q&A는 승인됐습니다. RTL 생성 전 validation을 실행하세요.',
        needsSsotApproval: '기록된 Q&A는 완료됐습니다. To SSOT로 SSOT를 만들고 validation을 실행하세요.',
        blockedByMissing: '아직 열린 Q&A 카드가 있어서 답변장이 완성되지 않았습니다.',
        feedTitle: 'SSOT 3단계 흐름',
        actionChatTitle: '선택 메모 = Chat',
        actionChatDetail: '추가 맥락이 있을 때만 씁니다.',
        actionImportTitle: '1. Import',
        actionImportDetail: '기존 문서를 업로드하세요. 업로드하면 자동으로 import됩니다.',
        actionInterviewTitle: '2. Deep Interview',
        actionInterviewDetail: 'import/wiki 근거로도 부족한 것만 질문합니다.',
        actionToSsotTitle: '3. To SSOT',
        actionToSsotDetail: '현재 근거를 승인하고 SSOT 문서를 만듭니다.',
        chooseFile: '파일 선택',
        openChat: '채팅 열기',
        filled: '채움',
        missing: '부족',
        refresh: '새로고침',
        chat: '채팅',
        total: '전체',
        approved: '승인',
        pending: '대기',
        requirements: '요구사항',
        requirementsRemaining: '남음',
        ssot: 'SSOT',
        draft: '작성중',
        sessions: '현재 세션',
        toc: '목차',
        none: '아직 QA 기록이 없습니다.',
        noSaved: '현재 session/IP의 QA 기록이 없습니다.',
        noCards: '아직 section QA 카드가 없습니다. 시작:',
        noAnswer: '아직 답변이 저장되지 않았습니다.',
        useInput: '입력으로',
        answer: '답변',
        close: '닫기',
        sendToInput: '입력창 열기',
        selectOne: '옵션 하나를 선택하세요',
        selectMany: '옵션을 하나 이상 선택하세요',
        typedAnswer: '직접 입력',
        customNote: '추가 설명',
        noOptions: '옵션이 없습니다. 아래에 답변을 입력하세요.',
        autoInputHint: '여기서 선택/입력해도 전송 전까지 채팅 입력창은 바뀌지 않습니다',
        inputUpdated: '답변 초안 준비됨',
        send: '전송',
        sendNeedAnswer: '옵션을 선택하거나 답변을 입력한 후 전송하세요',
        importFiles: 'Import',
        importing: 'Importing...',
        deepInterview: 'Deep Interview',
        toSsot: 'To SSOT',
        importReady: '업로드됨',
        qaActionTitle: '다음 SSOT 액션',
        importExportTitle: 'Import / Export',
        importExportSubtitle: '기존 문서를 SSOT import 근거로 업로드하거나 현재 SSOT를 내보냅니다.',
        uploadImportTitle: 'Upload (Import)',
        uploadImportDetail: '여기에 파일을 드롭하거나 파일을 선택하세요. import된 파일 목록이 즉시 갱신됩니다.',
        dropHere: '파일을 놓으면 업로드됩니다',
        chooseFiles: '파일 선택',
        importedList: 'Import된 파일',
        noImportedFiles: '아직 import된 파일이 없습니다.',
        exportTitle: 'Export',
        exportDetail: '현재 SSOT 산출물을 다운로드합니다.',
        exportMd: 'Markdown',
        exportDocx: 'Word',
        exportHtml: 'HTML',
        validationScriptTitle: 'SSOT validator script',
        validationScriptDetail: 'verify_ssot.py를 --root 기준으로 실행합니다. 가능하면 check_ssot_disk.sh도 같이 사용합니다.',
        validationMode: 'mode',
        runValidation: 'Validation 실행',
        validationPass: 'PASS',
        validationFail: 'FAIL',
      };
  const requirementHelp = uiLang === 'en'
    ? {
        purpose: 'What this IP does in one sentence.',
        bus_interface: 'How software or another block talks to it.',
        register_map: 'Control/status registers, offsets, and access rules.',
        clock_reset: 'Clock names, reset names, polarity, and timing assumptions.',
        interrupt: 'Whether it raises interrupts, and when. Say none if not used.',
        memory_map: 'Address or memory requirements. Say none if not used.',
        parameters: 'Configurable parameters and default values.',
        submodule_structure: 'Internal blocks and who owns each responsibility.',
        test_expectation: 'Minimum simulation/test behavior that proves it works.',
      }
    : {
        purpose: '이 IP가 한 문장으로 무슨 일을 하는지.',
        bus_interface: '소프트웨어나 다른 블록이 어떻게 말을 거는지.',
        register_map: '레지스터 주소, 읽기/쓰기 규칙, 상태값.',
        clock_reset: '클럭/리셋 이름, 극성, 타이밍 조건.',
        interrupt: '인터럽트를 쓰는지, 언제 올리는지. 없으면 없다고 적기.',
        memory_map: '메모리나 주소 요구사항. 없으면 없다고 적기.',
        parameters: '바꿀 수 있는 파라미터와 기본값.',
        submodule_structure: '내부 블록 구성과 각 블록의 책임.',
        test_expectation: '시뮬레이션에서 최소한 무엇을 확인해야 하는지.',
      };
  const requirementSimpleName = uiLang === 'en'
    ? {
        purpose: 'What are we making?',
        bus_interface: 'How does it connect?',
        register_map: 'What knobs and status bits exist?',
        clock_reset: 'What clock and reset does it use?',
        interrupt: 'Does it ring an interrupt bell?',
        memory_map: 'Does it need an address or memory?',
        parameters: 'What can be configured?',
        submodule_structure: 'What small blocks are inside?',
        test_expectation: 'How do we know it works?',
      }
    : {
        purpose: '무엇을 만들까?',
        bus_interface: '어떻게 연결할까?',
        register_map: '조작 버튼과 상태표는?',
        clock_reset: '클럭과 리셋은?',
        interrupt: '인터럽트 알림은?',
        memory_map: '주소나 메모리는?',
        parameters: '바꿀 수 있는 값은?',
        submodule_structure: '안에는 어떤 작은 블록?',
        test_expectation: '어떻게 성공을 확인할까?',
      };
  const requirementByKey = new Map(requirementItems.map(item => [item?.key, item || {}]));
  const requirementLabel = (key) => requirementSimpleName[key] || requirementByKey.get(key)?.label || key;
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
  const uploadDoneText = (count) => (
    uiLang === 'en'
      ? `${count} file${count === 1 ? '' : 's'} saved under ${data.ip}/req/imports/; /import started.`
      : `${count}개 파일을 ${data.ip}/req/imports/에 저장하고 /import를 실행했습니다.`
  );
  const importInputRef = React.useRef(null);
  const [importBusy, setImportBusy] = React.useState(false);
  const [importStatus, setImportStatus] = React.useState('');
  // Document → markdown converter pick. Server is authoritative; fetch
  // once on mount and write back on user change.
  const [importConverter, setImportConverter] = React.useState('markitdown');
  React.useEffect(() => {
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
  const changeImportConverter = React.useCallback((next) => {
    const choice = String(next || '').trim().toLowerCase();
    if (!choice) return;
    setImportConverter(choice);
    fetch('/api/ssot/import/converter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ converter: choice }),
    }).catch(() => {});
  }, []);
  const [importDragActive, setImportDragActive] = React.useState(false);
  const [validationMode, setValidationMode] = React.useState('engineering');
  const [validationBusy, setValidationBusy] = React.useState(false);
  const [validationResult, setValidationResult] = React.useState(null);
  const importStorageKey = `atlas:ssot-imported-files:${activeSessionNorm || 'session'}:${data?.ip || 'ip'}`;
  const importStem = React.useCallback((item) => {
    const raw = (item && (item.name || item.md_path || item.original_path)) || '';
    const base = String(raw).split('/').pop() || '';
    return base.replace(/^\d+_\d+_/, '').replace(/\.(md|pdf)$/i, '').toLowerCase();
  }, []);
  const collapseImportRows = React.useCallback((rows) => {
    const merged = [];
    const stemIdx = new Map();
    for (const item of rows) {
      if (!item) continue;
      const stem = importStem(item);
      const key = stem || item.md_path || item.original_path || item.name;
      if (!key) continue;
      if (stemIdx.has(key)) {
        const target = merged[stemIdx.get(key)];
        if (!target.md_path && item.md_path) target.md_path = item.md_path;
        if (!target.original_path && item.original_path) target.original_path = item.original_path;
        if (!target.image_count && item.image_count) target.image_count = item.image_count;
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
  const readStoredImportedFiles = React.useCallback(() => {
    try {
      const raw = window.localStorage.getItem(importStorageKey);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed.slice(0, 20) : [];
    } catch (_) {
      return [];
    }
  }, [importStorageKey]);
  const [importedFiles, setImportedFilesState] = React.useState(() => readStoredImportedFiles());
  const setImportedFiles = React.useCallback((updater) => {
    setImportedFilesState(prev => {
      const nextRaw = typeof updater === 'function' ? updater(prev) : updater;
      const next = Array.isArray(nextRaw) ? nextRaw.slice(0, 20) : [];
      try {
        if (next.length) window.localStorage.setItem(importStorageKey, JSON.stringify(next));
        else window.localStorage.removeItem(importStorageKey);
      } catch (_) {}
      return next;
    });
  }, [importStorageKey]);
  React.useEffect(() => {
    const backendImports = Array.isArray(data?.imports) ? data.imports : [];
    if (!backendImports.length) {
      setImportedFilesState(readStoredImportedFiles());
      return;
    }
    const normalized = backendImports.map((item, idx) => ({
      name: item.name || String(item.path || item.md_path || item.original_path || '').split('/').pop(),
      bytes: item.bytes || 0,
      md_path: item.md_path || (String(item.path || '').endsWith('.md') ? item.path : ''),
      original_path: item.original_path || item.path || '',
      image_count: item.image_count || (Array.isArray(item.image_paths) ? item.image_paths.length : 0),
      pending: false,
      error: !!item.convert_error,
      ts: item.updated_at || item.mtime || idx,
    })).filter(item => item.name || item.md_path || item.original_path);
    setImportedFiles(prev => collapseImportRows([...normalized, ...prev]).slice(0, 20));
  }, [data?.imports, readStoredImportedFiles, setImportedFiles, collapseImportRows]);
  const runSsotCommand = (cmd) => {
    const text = String(cmd || '').trim();
    if (!text || !onRunCommand) return;
    onRunCommand(text);
  };
  const readFileAsBase64 = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const raw = String(reader.result || '');
      resolve(raw.includes(',') ? raw.split(',').pop() : raw);
    };
    reader.onerror = () => reject(reader.error || new Error('file read failed'));
    reader.readAsDataURL(file);
  });
  const uploadImportFiles = async (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length || !data?.ip) return;
    const uploadStartedAt = Date.now();
    setImportBusy(true);
    setImportStatus(uiLang === 'en' ? `Uploading ${files.length} file${files.length === 1 ? '' : 's'}...` : `${files.length}개 파일 업로드 중...`);
    setImportedFiles(prev => {
      const queued = files.map((file, idx) => ({
        name: file.name,
        bytes: file.size || 0,
        md_path: '',
        original_path: '',
        image_count: 0,
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
      const saved = Array.isArray(payload.saved) && payload.saved.length
        ? payload.saved
        : (Array.isArray(payload.paths) ? payload.paths.map(path => ({ name: String(path || '').split('/').pop(), original_path: path })) : []);
      if (saved.length) {
        setImportedFiles(prev => {
          const next = collapseImportRows(saved.map(s => ({
            name: s.name || '',
            bytes: s.bytes || 0,
            md_path: s.md_path || '',
            original_path: s.original_path || '',
            image_count: Array.isArray(s.image_paths) ? s.image_paths.length : 0,
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
    } catch (err) {
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
  const exportSsot = (format) => {
    const fmt = String(format || '').trim();
    if (!fmt || !data?.ip) return;
    window.location.href = `/api/ssot/export?ip=${encodeURIComponent(data.ip)}&format=${encodeURIComponent(fmt)}`;
  };
  const runValidation = async () => {
    if (!data?.ip || validationBusy) return;
    setValidationBusy(true);
    setValidationResult(null);
    try {
      const res = await fetch('/api/ssot/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: data.ip, mode: validationMode }),
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
    } catch (err) {
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
  const handleImportDrop = (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    setImportDragActive(false);
    uploadImportFiles(ev.dataTransfer?.files);
  };
  const renderImportStatus = () => {
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
  };
  const renderImportedFiles = () => (
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
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ color: 'var(--fg-mute)', fontSize: 12 }}>{t.noImportedFiles}</div>
      )}
    </div>
  );
  const renderValidationScriptCard = () => {
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
  };
  // All QA cards (pending AND approved) default to expanded. Track the
  // *closed* set so newly-streamed items inherit the open-by-default rule.
  const [closedCardKeys, setClosedCardKeys] = React.useState(() => new Set());
  const [answerDrafts, setAnswerDrafts] = React.useState({});
  // Active section tab — null means "first section with pending items, else first section".
  const [activeSectionId, setActiveSectionId] = React.useState(null);
  // Per-status group collapse: both groups default open. Tracking the
  // closed set keeps the default-open rule stable across re-renders.
  const [closedStatusGroups, setClosedStatusGroups] = React.useState(() => new Set());
  const pendingItemKey = (item) => [
    item?.flow_id || '',
    item?.section || item?.section_id || '',
    item?.decision_key || item?.source || item?.question || '',
  ].join(':');
  const optionRows = (item) => (
    Array.isArray(item?.options) ? item.options : []
  ).map((option, idx) => {
    const raw = option && typeof option === 'object' ? option : { id: option, label: option };
    const id = String(raw.id ?? raw.value ?? raw.label ?? idx);
    const label = String(raw.label ?? raw.title ?? raw.value ?? raw.id ?? `Option ${idx + 1}`);
    const detail = raw.detail || raw.description || '';
    return { ...raw, id, label, detail };
  });
  const pendingKind = (item) => {
    const kind = String(item?.question_kind || item?.kind || '').toLowerCase();
    if (kind === 'multi' || kind === 'multiple' || kind === 'checkbox') return 'multi';
    if (kind === 'input' || kind === 'text' || kind === 'freeform') return 'input';
    return optionRows(item).length ? 'single' : 'input';
  };
  const pendingDraft = (item) => {
    const key = pendingItemKey(item);
    const stored = answerDrafts[key];
    const rows = optionRows(item);
    if (stored) {
      const selected = new Set((stored.opts || []).filter(o => o.selected).map(o => String(o.id)));
      return {
        opts: rows.map(option => ({ ...option, selected: selected.has(option.id) })),
        custom: stored.custom || '',
      };
    }
    // No in-memory edit yet → seed from the saved answer so approved/answered
    // cards open with their previous selection pre-checked. The seed is
    // matched by option id, label, or value (whichever is in the answer
    // payload). If we cannot match an option, fall back to dropping the
    // entire saved blob into the custom note.
    const ans = item?.answer_data || item?.answer || '';
    const seedSelected = new Set();
    let seedCustom = '';
    if (ans && typeof ans === 'object') {
      const sel = Array.isArray(ans.selected) ? ans.selected : [];
      sel.forEach(s => {
        const tok = String(s || '').trim();
        if (!tok) return;
        const match = rows.find(o => String(o.id) === tok || String(o.label) === tok);
        if (match) seedSelected.add(String(match.id));
      });
      seedCustom = String(ans.answer || ans.note || ans.custom || '').trim();
    } else if (typeof ans === 'string' && ans.trim()) {
      const txt = ans.trim();
      const match = rows.find(o => String(o.label) === txt || String(o.id) === txt);
      if (match) seedSelected.add(String(match.id));
      else seedCustom = txt;
    }
    return {
      opts: rows.map(option => ({ ...option, selected: seedSelected.has(option.id) })),
      custom: seedCustom,
    };
  };
  const hasPendingAnswer = (draft) => (
    (draft?.opts || []).some(o => o.selected)
  ) || String(draft?.custom || '').trim().length > 0;
  const buildPendingInputText = (item, draft = pendingDraft(item)) => {
    const selectedRows = (draft?.opts || []).filter(option => option.selected);
    const selectedLines = selectedRows.map(option => (
      option.detail ? `  - ${option.label} (${option.id}): ${option.detail}` : `  - ${option.label} (${option.id})`
    ));
    const custom = String(draft?.custom || '').trim();
    const ip = data?.ip || activeIp || 'current IP';
    const lines = [];
    const headerKey = item.decision_key ? ` · ${item.decision_key}` : '';
    lines.push(`### Answer pending QA — ${ip}${headerKey}`);
    if (item.decision_label && item.decision_label !== item.question) {
      lines.push(`Decision: ${item.decision_label}`);
    }
    lines.push(`Question: ${item.question || item.decision_label || 'Untitled question'}`);
    if (item.subtitle) lines.push(`Context : ${item.subtitle}`);
    if (selectedLines.length) {
      lines.push('Selected:');
      lines.push(...selectedLines);
    }
    if (custom) lines.push(`Note    : ${custom}`);
    if (!selectedLines.length && !custom) {
      lines.push('Answer  : <choose option or type note>');
    }
    lines.push('Apply this answer to SSOT-GEN QA and continue the current workflow.');
    return lines.join('\n');
  };
  const updatePendingDraft = (item, draft) => {
    const key = pendingItemKey(item);
    setAnswerDrafts(prev => ({ ...prev, [key]: draft }));
  };
  const togglePendingOption = (item, optionId) => {
    const draft = pendingDraft(item);
    const kind = pendingKind(item);
    const opts = (draft.opts || []).map(option => {
      if (kind === 'multi') {
        return option.id === optionId ? { ...option, selected: !option.selected } : option;
      }
      return { ...option, selected: option.id === optionId };
    });
    updatePendingDraft(item, { ...draft, opts });
  };
  const renderPendingAnswerBox = (item) => {
    const draft = pendingDraft(item);
    const kind = pendingKind(item);
    const hasAnswer = hasPendingAnswer(draft);
    return (
      <div
        onClick={(ev) => ev.stopPropagation()}
        onKeyDown={(ev) => ev.stopPropagation()}
        style={{
          marginTop: 8,
          paddingTop: 8,
          borderTop: '1px solid var(--line)',
      }}>
        <div style={{ color: 'var(--fg-mute)', fontSize: 10, marginBottom: 6 }}>
          {kind === 'multi' ? t.selectMany : (kind === 'single' ? t.selectOne : t.typedAnswer)}
        </div>
        {!draft.opts.length ? (
          <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginBottom: 6 }}>{t.noOptions}</div>
        ) : null}
        <AskUserQuestionBlock
          index={0}
          block={{
            question: item.question || item.decision_label || '',
            subtitle: item.subtitle || '',
            placeholder: kind === 'input' ? t.typedAnswer : t.customNote,
            multiline: kind === 'input',
          }}
          blockState={draft}
          kind={kind}
          isBatched={false}
          isActive={true}
          selectedIndex={-1}
          showQuestion={false}
          onToggleOption={(optionId) => togglePendingOption(item, optionId)}
          onCustom={(value) => updatePendingDraft(item, { ...pendingDraft(item), custom: value })}
          onSelectAll={() => updatePendingDraft(item, {
            ...draft,
            opts: (draft.opts || []).map(option => ({ ...option, selected: true })),
          })}
          onClearAll={() => updatePendingDraft(item, {
            ...draft,
            opts: (draft.opts || []).map(option => ({ ...option, selected: false })),
          })}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
          <span style={{ color: hasAnswer ? 'var(--cyan)' : 'var(--fg-mute)', fontSize: 10 }}>
            {hasAnswer ? t.inputUpdated : t.autoInputHint}
          </span>
          <span style={{ flex: 1 }} />
          {onSubmitPending ? (
            <button
              type="button"
              className="mini-btn"
              disabled={!hasAnswer}
              title={hasAnswer ? '' : t.sendNeedAnswer}
              onClick={(ev) => {
                ev.stopPropagation();
                if (!hasAnswer) return;
                onSubmitPending(
                  [{ item, draft }],
                  buildPendingInputText(item, draft),
                );
              }}
              style={{
                background: hasAnswer ? 'var(--cyan)' : undefined,
                color: hasAnswer ? 'var(--bg-0)' : undefined,
                fontWeight: hasAnswer ? 600 : undefined,
                opacity: hasAnswer ? 1 : 0.45,
                cursor: hasAnswer ? 'pointer' : 'not-allowed',
              }}
            >
              {t.send}
            </button>
          ) : null}
        </div>
      </div>
    );
  };
  const renderQa = (item, status) => {
    const key = pendingItemKey(item);
    const isPending = status === 'pending';
    const isApproved = status === 'approved';
    // All QA cards (pending and approved) default OPEN. Approved cards
    // can be re-opened to amend the saved answer (re-select / re-submit).
    const isOpen = (isPending || isApproved) && !closedCardKeys.has(key);
    const statusColor = atlasStatusMeta(status).color;
    const cardToggleable = isPending || isApproved;
    const togglePendingCard = () => {
      if (!cardToggleable) return;
      setClosedCardKeys(prev => {
        const next = new Set(prev);
        if (next.has(key)) next.delete(key);
        else next.add(key);
        return next;
      });
    };
    const handleCardKey = (ev) => {
      if (!cardToggleable) return;
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        togglePendingCard();
      }
    };
    return (
      <div
        key={key}
        role={cardToggleable ? 'button' : undefined}
        tabIndex={cardToggleable ? 0 : undefined}
        onClick={cardToggleable ? togglePendingCard : undefined}
        onKeyDown={cardToggleable ? handleCardKey : undefined}
        title={cardToggleable ? (isOpen ? 'Click to collapse' : 'Click to expand') : undefined}
        style={{
          padding: '8px 10px',
          border: '1px solid var(--line)',
          borderLeft: `3px solid ${statusColor}`,
          background: status === 'approved'
            ? 'color-mix(in oklch, var(--ok) 7%, transparent)'
            : 'color-mix(in oklch, var(--warn) 8%, transparent)',
          marginBottom: 8,
          fontFamily: 'var(--mono)',
          cursor: cardToggleable ? 'pointer' : 'default',
        }}
      >
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
          <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
            {item.decision_key || item.source || 'qa'}
          </span>
          <span style={{ flex: 1 }} />
          {cardToggleable ? (
            <span
              aria-hidden="true"
              style={{
                color: 'var(--fg-mute)',
                fontSize: 10,
                fontFamily: 'var(--mono)',
                userSelect: 'none',
              }}
            >
              {isOpen ? '▾' : '▸'}
            </span>
          ) : null}
        </div>
        <div style={{ color: 'var(--fg)', fontSize: 12, lineHeight: 1.45 }}>
          {item.question || item.decision_label || 'Untitled question'}
        </div>
        {item.subtitle ? (
          <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginTop: 3 }}>
            {item.subtitle}
          </div>
        ) : null}
        {isOpen ? renderPendingAnswerBox(item) : null}
        <div style={{ color: item.answer ? 'var(--fg)' : 'var(--fg-mute)', fontSize: 12, marginTop: 7, lineHeight: 1.45 }}>
          {item.answer || t.noAnswer}
        </div>
      </div>
    );
  };

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
            onChange={(ev) => {
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
                <code className="acc">{data.ip}</code>
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
                <option value="cursor-agent">cursor-agent only</option>
                <option value="auto">auto (cursor-agent → markitdown)</option>
              </select>
              <span style={{ opacity: 0.65 }}>
                {importConverter === 'cursor-agent'
                  ? 'Routes every doc through cursor-agent.'
                  : importConverter === 'auto'
                    ? 'Tries cursor-agent first, falls back to markitdown.'
                    : 'Python markitdown CLI (python3.12 on Windows).'}
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
              }}
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
                  onClick={(ev) => {
                    ev.stopPropagation();
                    importInputRef.current?.click();
                  }}
                  style={{ marginTop: 12 }}
                >
                  {importBusy ? t.importing : t.chooseFiles}
                </button>
              </div>
            </div>
            {renderImportStatus()}
            {renderImportedFiles()}
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
              <code className="acc">{data.ip}</code>
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
            <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginBottom: 6 }}>{t.rtlReadiness}</div>
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

          {checklistOnly ? renderValidationScriptCard() : (
          <div style={{
            border: '1px solid var(--line)',
            background: 'color-mix(in oklch, var(--bg-2) 52%, transparent)',
            padding: 10,
          }}>
            <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginBottom: 6 }}>{t.nextAction}</div>
            <div style={{ color: 'var(--fg)', fontSize: 13, lineHeight: 1.5 }}>{nextActionText}</div>
            <div style={{ marginTop: 12, color: 'var(--fg-mute)', fontSize: 11 }}>{t.feedTitle}</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 8, marginTop: 7 }}>
              <div style={{ borderTop: '2px solid var(--cyan)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionChatTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4, marginTop: 3 }}>{t.actionChatDetail}</div>
                <button className="mini-btn" type="button" onClick={onBack} style={{ marginTop: 7 }}>{t.openChat}</button>
              </div>
              <div style={{ borderTop: '2px solid var(--accent)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionImportTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4, marginTop: 3 }}>{t.actionImportDetail}</div>
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
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
              <div style={{ borderTop: '2px solid var(--warn)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionInterviewTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4, marginTop: 3 }}>{t.actionInterviewDetail}</div>
                <button
                  className="mini-btn"
                  type="button"
                  onClick={() => runSsotCommand(`/grill-me ${data.ip}`)}
                  title="Run /grill-me for unresolved SSOT decisions"
                  style={{ marginTop: 7 }}
                >
                  {t.deepInterview}
                </button>
              </div>
              <div style={{ borderTop: '2px solid var(--ok)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionToSsotTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4, marginTop: 3 }}>{t.actionToSsotDetail}</div>
                <button
                  className="mini-btn"
                  type="button"
                  onClick={() => runSsotCommand(`/to-ssot ${data.ip}`)}
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
                      <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4 }}>
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
                      <div style={{ marginTop: 4, color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.4 }}>{row.help}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: 'var(--ok)', fontSize: 12, lineHeight: 1.45 }}>{t.missingEmpty}</div>
              )}
            </div>
          </div>
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
            <code className="acc">{data.ip}</code>
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
              onClick={() => runSsotCommand(`/grill-me ${data.ip}`)}
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
              onClick={() => runSsotCommand(`/to-ssot ${data.ip}`)}
              title="Run /to-ssot for this IP"
              style={{ marginTop: 10 }}
            >
              {t.toSsot}
            </button>
          </div>
        </div>
      ) : null}

      {!checklistOnly ? (
        <>
      <div style={{
        border: '1px solid var(--line)',
        padding: 10,
        background: 'color-mix(in oklch, var(--bg-1) 75%, transparent)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <div style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            {t.sessions}
          </div>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>{currentSessionRows.length} ssot-gen</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 8 }}>
          {currentSessionRows.length ? currentSessionRows.slice(0, 12).map(row => {
            const active = normalizeUiSession(row.session) === normalizeUiSession(activeSession || data.session || '');
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
                }}
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
        const answerableAllPending = allPending.filter(item => hasPendingAnswer(pendingDraft(item)));
        const submitAll = () => {
          if (!onSubmitPending) return;
          if (!answerableAllPending.length) return;
          const bundle = answerableAllPending.map(item => ({ item, draft: pendingDraft(item) }));
          // Build a single combined prompt that lists every answered pending QA.
          const ip = data?.ip || activeIp || 'current IP';
          const header = `# Submit ${bundle.length} pending QA answer${bundle.length === 1 ? '' : 's'} for ${ip}`;
          const segments = bundle.map(({ item, draft }, i) => {
            const body = buildPendingInputText(item, draft).replace(/^### .*\n?/, '');
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
                <div style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
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
                    onClick={() => setActiveSectionId(section.id)}
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
                    }}
                  >
                    <div style={{ fontSize: 'var(--ui-control-font-size)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
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
};

// ── ask_user — compact in-feed tool-call line ─────────────────────
// Renders as `action: ask_user(...)` matching the other tool calls,

// Phase 13f window export — workspace.jsx aliases this back.
window.SsotQaBoard = SsotQaBoard;

})();
