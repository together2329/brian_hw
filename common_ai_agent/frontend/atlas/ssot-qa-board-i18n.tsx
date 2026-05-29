// ssot-qa-board-i18n.tsx — TypeScript migration + split of the i18n string
// dictionaries extracted from ssot-qa-board.jsx (Phase 13f / TS-split).
//
// These three builders were inline `const t = uiLang === 'en' ? {...} : {...}`
// objects inside SsotQaBoard (lines 66-286 of the legacy .jsx). They are PURE
// functions of `uiLang` with no closure dependency on component state, so they
// are the least-coupled seam to lift out of the 1717-line mega-root.
//
// Load order (index.html): BEFORE ssot-qa-board.tsx. The main component reads
// these through the transitional window bridges (window.buildSsotQaStrings,
// window.buildRequirementHelp, window.buildRequirementSimpleName) to avoid any
// module-ordering assumptions, exactly as the legacy lambda forward-ref pattern
// did for workspace.jsx helpers.
//
// Transitional: bridges to window.* at the bottom so the (still-live) legacy
// ssot-qa-board.jsx is unaffected and any not-yet-migrated consumer resolves.

export type UiLang = 'ko' | 'en' | string;

// Shape of the big string table. Kept as a string-record so adding/renaming a
// key never breaks the type while values stay strongly `string`.
export type SsotQaStrings = Record<string, string>;
export type RequirementText = Record<string, string>;

// ── t — the main UI string table (legacy lines 66-240) ──────────────
export function buildSsotQaStrings(uiLang: UiLang): SsotQaStrings {
  return uiLang === 'en'
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
        reAnswer: 're-answer',
        reAnswerHint: 'already resolved — this re-submits a new answer',
        sent: 'sent — awaiting agent',
        notConnectedRetry: 'not connected — will retry',
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
        reAnswer: '다시 답변',
        reAnswerHint: '이미 처리된 항목 — 새 답변으로 다시 제출합니다',
        sent: '전송됨 — 에이전트 대기 중',
        notConnectedRetry: '연결 안 됨 — 재시도 예정',
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
}

// ── requirementHelp — long-form help per requirement key (lines 241-263) ──
export function buildRequirementHelp(uiLang: UiLang): RequirementText {
  return uiLang === 'en'
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
}

// ── requirementSimpleName — plain-language label per key (lines 264-286) ──
export function buildRequirementSimpleName(uiLang: UiLang): RequirementText {
  return uiLang === 'en'
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
}

// ── Transitional bridge: register on window for the still-live legacy .jsx
// and for the main ssot-qa-board.tsx to resolve at call time. ──
interface SsotQaI18nGlobals {
  buildSsotQaStrings: typeof buildSsotQaStrings;
  buildRequirementHelp: typeof buildRequirementHelp;
  buildRequirementSimpleName: typeof buildRequirementSimpleName;
}
const g = window as unknown as SsotQaI18nGlobals;
g.buildSsotQaStrings = buildSsotQaStrings;
g.buildRequirementHelp = buildRequirementHelp;
g.buildRequirementSimpleName = buildRequirementSimpleName;
