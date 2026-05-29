// atlas-window.d.ts — ambient typings for the ATLAS window-global surface.
// TRANSITIONAL strangler-fig bridge: every migrated .tsx reads/writes window
// globals through these declarations during .jsx↔.tsx coexistence. Permissive
// `any` — the win here is NAME-level + react-level checking; precise per-global
// types arrive at the import-cutover, when window.X becomes import { X } and the
// entry is deleted. When this file is empty, the glue era ends.

declare global {
  interface Window {
    ACTIVE_IP: any;
    ACTIVE_SESSION: any;
    ATLAS_AGENT_RUNNING: any;
    ATLAS_BOOT_CONFIG: any;
    ATLAS_DB_SESSION_ID: any;
    ATLAS_DEFAULT_EXEC_MODE: any;
    ATLAS_EXEC_MODE: any;
    ATLAS_JOBS: any;
    ATLAS_PIPELINE_RUNNING: any;
    ATLAS_PROGRESS: any;
    ATLAS_RESOLUTION: any;
    ATLAS_RUN_MODE: any;
    ATLAS_SESSION_LABEL: any;
    ATLAS_SESSION_UID: any;
    ATLAS_UI_LANG: any;
    ATLAS_USER: any;
    ATLAS_USER_SESSION_ID: any;
    AdminPage: any;
    AgentStatusPanel: any;
    ArchitectChat: any;
    AskUserPrompt: any;
    AtlasDashboardHelpers: any;
    AtlasExecPolicy: any;
    AtlasGuide: any;
    AtlasPipeline: any;
    AtlasUserDashboard: any;
    AtlasWorkersLogic: any;
    Babel: any;
    CONTEXT: any;
    CopyBtn: any;
    DOMPurify: any;
    DagMap: any;
    DebugTab: any;
    DeferredMarkdownPreview: any;
    DigestCard: any;
    DispatchRail: any;
    FLOW_STAGES: any;
    FoldablePane: any;
    GitPanel: any;
    GitTab: any;
    IP_OPTIONS: any;
    InlineCard: any;
    InlineWaveClip: any;
    Kbd: any;
    LobbyPage: any;
    LoginScreen: any;
    MiniScoresheet: any;
    ModuleCard: any;
    NavTab: any;
    OrchestratorChatPanel: any;
    PIPELINE_STAGES: any;
    PRISM_LANG_MAP: any;
    PROJECT_ROOT_NAME: any;
    Pill: any;
    PipelineFlowMap: any;
    PreviewPane: any;
    Prism: any;
    ProgressPanel: any;
    QA_FLOWS: any;
    React: any;
    ReactDOM: any;
    SCOPE_PATH: any;
    SLASH_COMMANDS: any;
    SOC: any;
    SOC_LOOKUP: any;
    SignalTableCard: any;
    SimDebug: any;
    SocArchitect: any;
    SourceDiffCard: any;
    SsotDocPane: any;
    SsotQaBoard: any;
    SsotReviewPane: any;
    StageCard: any;
    StateGlyph: any;
    StateLabel: any;
    StatusBar: any;
    TODOS: any;
    TitleBar: any;
    TodoGraph: any;
    TodoPanel: any;
    WAVE_TIME_START: any;
    WORKFLOW_REPORT_TABS: any;
    WorkflowReportPane: any;
    Workspace: any;
    X: any;
    __atlasClearAssetLoadErrors: any;
    _copyToClipboard: any;
    activateAtlasNamespace: any;
    atlasData: any;
    backend: any;
    buildRequirementHelp: any;
    buildRequirementSimpleName: any;
    buildSsotQaStrings: any;
    d: any;
    marked: any;
    mermaid: any;
    normalizeAtlasSessionName: any;
    openPipelineWorkflowWorkspace: any;
    parseVCD: any;
    pinAt: any;
    sectionFact: any;
    simDebug: any;
    workspaceFetchWorkerSnapshot: any;
  }
}

export {};
