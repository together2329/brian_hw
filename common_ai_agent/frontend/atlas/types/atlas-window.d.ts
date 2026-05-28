// atlas-window.d.ts — ambient typings for the ATLAS window-global surface.
//
// TRANSITIONAL bridge for the incremental TS migration (strangler-fig). While
// some files are still legacy `.jsx` registering helpers/components on
// `window.<name>`, every migrated `.tsx` reads/writes those globals through
// this declaration instead of `(window as any)`. Types are intentionally
// permissive (`any`) during the transition — the win at THIS stage is
// NAME-level checking (a typo'd global is a compile error) + react-level
// checking inside each module. Precise per-global types arrive at the
// import-cutover, when `window.X` is replaced by `import { X }` and the
// matching entry here is deleted. When this file is empty, the glue era ends.

declare global {
  interface Window {
    ACTIVE_IP: any;
    ACTIVE_SESSION: any;
    ATLAS_JOBS: any;
    ATLAS_PROGRESS: any;
    ATLAS_USER: any;
    ATLAS_USER_SESSION_ID: any;
    AgentStatusPanel: any;
    AskUserPrompt: any;
    AtlasDashboardHelpers: any;
    AtlasGuide: any;
    AtlasPipeline: any;
    AtlasUserDashboard: any;
    AtlasWorkersLogic: any;
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
    PROJECT_ROOT_NAME: any;
    Pill: any;
    PipelineFlowMap: any;
    PreviewPane: any;
    ProgressPanel: any;
    QA_FLOWS: any;
    SCOPE_PATH: any;
    SOC: any;
    SignalTableCard: any;
    SourceDiffCard: any;
    SsotDocPane: any;
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
    X: any;
    _copyToClipboard: any;
    backend: any;
    d: any;
    openPipelineWorkflowWorkspace: any;
    pinAt: any;
    sectionFact: any;
    workspaceFetchWorkerSnapshot: any;
  }
}

export {};
