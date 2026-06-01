// main.tsx — Vite ES-module entry for the ATLAS frontend.
//
// This replaces the legacy <script type="text/babel" data-presets="react">
// chain from index.html (in-browser Babel transpilation of the .jsx files).
// The modules below are loaded to MIRROR that legacy index.html script order
// exactly — each module registers its globals / components as a side effect,
// and later modules depend on earlier ones being present.
//
// IMPORTANT ordering rules:
//   1. "./_react-global" MUST be imported FIRST so that window.React and
//      window.ReactDOM are populated with the single bundled React instance
//      BEFORE any module that self-mounts (app.tsx) runs.
//   2. Each top-level module transitively imports its own split siblings, so
//      only the legacy top-level entries are listed here.
//   3. NO explicit createRoot() call here — app.tsx self-mounts at the end via
//      window.ReactDOM.createRoot(document.getElementById('root')).render(<App/>).

import "./_react-global";

async function bootstrapAtlas(): Promise<void> {
  await import("./login");
  await import("./axi-dma-mock");
  await import("./data");
  await import("./shared");
  await import("./ui-utils");
  await import("./ssot-doc");
  await import("./workflow-report");
  await import("./preview-pane");
  await import("./block-diagram");
  await import("./ssot-digest");
  await import("./ssot-digest-content");
  await import("./ssot-review");
  await import("./ssot-qa-board");
  await import("./agent-status-panel");
  await import("./workspace-panels");
  await import("./progress-todo-panels");
  await import("./debug-shared");
  await import("./debug-inline-cards");
  await import("./sim-debug");
  await import("./debug-tab");
  await import("./git-tab");
  await import("./perforce-sync");
  await import("./coverage");
  await import("./user-dashboard");
  await import("./workspace");
  await import("./soc-data");
  await import("./soc-shared");
  await import("./soc-architect");
  await import("./pipeline");
  await import("./pipe-width");
  await import("./pipeline-helpers");
  await import("./pipeline-trace");
  await import("./pipeline-flow-stage");
  await import("./guide");
  await import("./app");
}

bootstrapAtlas().catch((error) => {
  if (typeof window.__atlasReportError === 'function') {
    window.__atlasReportError('bootstrap failed', error?.stack || error?.message || String(error));
  } else {
    console.error(error);
  }
});
