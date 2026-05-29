// workspace-panel-shared.tsx — shared types + cross-file window glue for the
// workspace-panels.tsx cluster (AskUserPrompt / OrchestratorChatPanel /
// GitPanel).
//
// Extracted from workspace-panels.tsx to keep that file and every sibling
// under 1000 lines. This module owns:
//   - the loose data shapes flowing through the three panels (kept loose
//     where the .jsx was loose),
//   - the narrow `w` cast over `window` for cross-file globals owned by
//     unmigrated .jsx (window.QA_FLOWS, window.backend, the workspace.jsx
//     helpers, window.Kbd),
//   - the forward-ref lambdas that resolve those helpers at call time.
//
// Typed in the same permissive house style as shared.tsx — window-sourced
// values are typed as `any`/`unknown` on purpose; do NOT tighten them.
import { type ReactNode } from 'react';

// ── Loose data shapes flowing through these panels (kept loose where the .jsx
// was loose). ──
export interface AskOption {
  id: string;
  selected?: boolean;
  locked?: boolean;
}

export interface AskTabState {
  opts?: AskOption[];
  custom?: string;
}

export interface AskFlowQuestion {
  kind?: string;
  multiline?: boolean;
}

export interface AskFlow {
  kind?: string;
  multiline?: boolean;
  questions?: AskFlowQuestion[];
  stage?: ReactNode;
  step?: ReactNode;
  total?: ReactNode;
}

export interface AskFlowState {
  batched?: boolean;
  active?: number;
  states?: AskTabState[];
  opts?: AskOption[];
  custom?: string;
}

export interface ChatRoom {
  name: string;
  scope?: string;
}

export interface ChatMessage {
  id: string | number;
  ip_id?: unknown;
  user_id?: unknown;
  display_name?: unknown;
  content?: unknown;
  created_at?: number;
}

export interface GitFile {
  path: string;
  status?: string;
  staged?: boolean;
  unstaged?: boolean;
  added?: number | null;
  removed?: number | null;
}

export interface GitCommit {
  sha: string;
  short?: string;
  subject?: string;
  author?: string;
  date?: string;
  added?: number | null;
  removed?: number | null;
  files?: number;
}

export interface GitOpResult {
  kind?: string;
  ok?: boolean;
  stdout?: string;
  stderr?: string;
  error?: string;
}

export interface StatusGlyphCell {
  ch: string;
  color: string;
}

export interface StatusGlyph {
  staged: StatusGlyphCell;
  work: StatusGlyphCell;
}

// WS-bus payload for the 'chat_message' signal — the broadcast carries a
// `room` field (used for the active-room filter) on top of the message fields.
export interface ChatMessagePayload extends ChatMessage {
  room?: string | null;
}

export interface AtlasBackend {
  subscribe?: (ev: string, cb: (m: ChatMessagePayload) => void) => (() => void) | void;
}

// ── Cross-file window globals owned by unmigrated .jsx, reached via a narrow
// typed view of `window` (not yet in types/atlas-window.d.ts). ──
export const w = window as unknown as {
  QA_FLOWS: Record<string, AskFlow | undefined>;
  backend?: AtlasBackend;
  AskUserQuestionBlock: (...a: any[]) => any;
  AtlasStatusBadge: (...a: unknown[]) => unknown;
  TodoGraph: (...a: unknown[]) => unknown;
  _limitAtlasLines: (...a: unknown[]) => unknown;
  _statusGlyph: (...a: unknown[]) => StatusGlyph;
  atlasStatusMeta: (...a: unknown[]) => unknown;
  atlasUiExecMode: (...a: unknown[]) => unknown;
  healthMatchesCurrentUser: (...a: unknown[]) => unknown;
  normalizeUiSession: (...a: unknown[]) => unknown;
  uiEffectiveHealthSession: (...a: unknown[]) => unknown;
  uiHealthCountersMatchBrowserRoute: (...a: unknown[]) => unknown;
  uiSessionRoute: (...a: unknown[]) => unknown;
  workspaceFetchWorkerSnapshot: (...a: unknown[]) => unknown;
  Kbd: (props: { children?: ReactNode }) => ReactNode;
};

// Forward-ref to workspace.jsx helpers (resolved at call time):
export const AskUserQuestionBlock = (...a: any[]) => w.AskUserQuestionBlock(...a);
export const AtlasStatusBadge = (...a: unknown[]) => w.AtlasStatusBadge(...a);
export const TodoGraph = (...a: unknown[]) => w.TodoGraph(...a);
export const _limitAtlasLines = (...a: unknown[]) => w._limitAtlasLines(...a);
export const _statusGlyph = (...a: unknown[]) => w._statusGlyph(...a);
export const atlasStatusMeta = (...a: unknown[]) => w.atlasStatusMeta(...a);
export const atlasUiExecMode = (...a: unknown[]) => w.atlasUiExecMode(...a);
export const healthMatchesCurrentUser = (...a: unknown[]) => w.healthMatchesCurrentUser(...a);
export const normalizeUiSession = (...a: unknown[]) => w.normalizeUiSession(...a);
export const uiEffectiveHealthSession = (...a: unknown[]) => w.uiEffectiveHealthSession(...a);
export const uiHealthCountersMatchBrowserRoute = (...a: unknown[]) => w.uiHealthCountersMatchBrowserRoute(...a);
export const uiSessionRoute = (...a: unknown[]) => w.uiSessionRoute(...a);
export const workspaceFetchWorkerSnapshot = (...a: unknown[]) => w.workspaceFetchWorkerSnapshot(...a);

// Kbd is owned by shared.(jsx|tsx); reached as a cross-file global like the
// helpers above (resolved at call time so an unmigrated owner still works).
export const Kbd = (props: { children?: ReactNode }) => w.Kbd(props);
