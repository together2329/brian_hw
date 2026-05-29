// main.tsx — Vite ES-module entry for the ATLAS frontend.
//
// This replaces the legacy <script type="text/babel" data-presets="react">
// chain from index.html (in-browser Babel transpilation of the .jsx files).
// The side-effect imports below are ordered to MIRROR that legacy index.html
// script order exactly — each module registers its globals / components as a
// side effect, and later modules depend on earlier ones being present.
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

import "./login";
import "./axi-dma-mock";
import "./data";
import "./shared";
import "./ui-utils";
import "./ssot-doc";
import "./workflow-report";
import "./preview-pane";
import "./block-diagram";
import "./ssot-digest";
import "./ssot-digest-content";
import "./ssot-review";
import "./ssot-qa-board";
import "./agent-status-panel";
import "./workspace-panels";
import "./progress-todo-panels";
import "./debug-shared";
import "./debug-inline-cards";
import "./sim-debug";
import "./debug-tab";
import "./git-tab";
import "./perforce-sync";
import "./coverage";
import "./user-dashboard";
import "./workspace";
import "./soc-data";
import "./soc-shared";
import "./soc-architect";
import "./pipeline";
import "./pipe-width";
import "./pipeline-helpers";
import "./pipeline-trace";
import "./pipeline-flow-stage";
import "./guide";
import "./app";
