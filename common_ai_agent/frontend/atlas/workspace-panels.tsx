// workspace-panels.tsx — TypeScript migration of workspace-panels.jsx
// (Phase 13g refactor: 6 sidebar/panel components extracted from
// workspace.jsx as one cohesive cluster). Two of the original six panels
// (ProgressPanel/TodoPanel → progress-todo-panels.jsx in Phase 23) and one
// (AgentStatusPanel → agent-status-panel.jsx in Phase 19) have since been
// re-extracted, so this cluster now owns three:
//
//   1. AskUserPrompt          — chat-input ask_user prompt block
//   2. OrchestratorChatPanel  — orchestrator-mode side chat
//   3. GitPanel               — per-IP git status + commits
//
// SUB-1000 SPLIT: this file grew to 1007 lines, so each panel now lives in its
// own sibling and the shared types + cross-file `w` cast / forward-refs live in
// workspace-panel-shared.tsx. This module is now a thin barrel that re-exports
// the public contract so every symbol stays importable from
// "./workspace-panels" exactly as before:
//
//   - workspace-panel-shared.tsx  — loose data shapes + window glue (`w`, the
//       workspace.jsx helper forward-refs, Kbd)
//   - workspace-ask-prompt.tsx    — AskUserPrompt          (+ window.AskUserPrompt)
//   - workspace-orchestrator-chat.tsx — OrchestratorChatPanel (+ window.OrchestratorChatPanel)
//   - workspace-git-panel.tsx     — GitPanel               (+ window.GitPanel)
//
// Each sibling registers its own window.* bridge as a module side-effect, so
// re-exporting from them here keeps the identical set of window globals
// (window.AskUserPrompt / window.OrchestratorChatPanel / window.GitPanel)
// assigned for the not-yet-migrated .jsx consumers (workspace.jsx aliases
// these back).
//
// Load order (index.html): AFTER ssot-qa-board.jsx, BEFORE workspace.jsx.
//
// Phase 13g window exports — workspace.jsx aliases these back.
// ProgressPanel/TodoPanel extracted to progress-todo-panels.jsx in Phase 23.
// AgentStatusPanel extracted to agent-status-panel.jsx in Phase 19.
export { AskUserPrompt, type AskUserPromptProps } from './workspace-ask-prompt';
export { OrchestratorChatPanel, type OrchestratorChatPanelProps } from './workspace-orchestrator-chat';
export { GitPanel, type GitPanelProps } from './workspace-git-panel';
