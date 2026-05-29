// progress-todo-globals.tsx — shared window-glue + loose data shapes for the
// progress-todo panels (extracted from progress-todo-panels.tsx so the source
// and each sibling stay under 1000 lines).
//
// These are the cross-file window globals owned by OTHER (unmigrated) files
// plus the late-bound component forward-refs and the loose payload shapes that
// BOTH ProgressPanel and TodoPanel read. Behaviour is identical to the original
// bare-global references, which resolved through window at runtime.
import { createElement, type ReactNode } from 'react';

// ── Cross-file window globals owned by OTHER (unmigrated) files ──
// These are NOT yet declared in types/atlas-window.d.ts, so we access them via
// a narrow cast that mirrors their runtime shape (owned by workspace.jsx /
// data.jsx). They MUST stay as window.* lookups — their owners may be
// unmigrated, so importing them is not possible.
export interface AtlasStatusMeta {
  glyph: string;
  color: string;
  label: string;
}
export interface AtlasStatusBadgeProps {
  status?: unknown;
  label?: ReactNode;
  count?: number;
  compact?: boolean;
  soft?: boolean;
  title?: string;
}
export interface AtlasWindowGlobals {
  atlasStatusMeta: (status: unknown) => AtlasStatusMeta;
  AtlasStatusBadge: (props: AtlasStatusBadgeProps) => ReactNode;
  _limitAtlasLines: (text: unknown, maxLines?: number) => string;
  TodoGraph: (props: {
    todos: unknown[];
    openId: unknown;
    setOpenId: (id: unknown) => void;
  }) => ReactNode;
  TODOS?: unknown;
  ATLAS_PROGRESS?: AtlasProgressData;
  ACTIVE_SESSION?: unknown;
  atlasData?: {
    refreshProgress?: () => void;
    clearTodos?: () => void;
  };
  backend?: { send: (msg: { type: string; text: string }) => void };
}
export const w = window as unknown as Window & AtlasWindowGlobals;

export const atlasStatusMeta = (status: unknown): AtlasStatusMeta => w.atlasStatusMeta(status);
export const _limitAtlasLines = (text: unknown, maxLines?: number): string => w._limitAtlasLines(text, maxLines);

// The original .jsx referenced `AtlasStatusBadge` / `TodoGraph` as bare globals
// and used them as JSX components (`<AtlasStatusBadge/>`, `<TodoGraph/>`), so
// React MOUNTED the window-owned component. We preserve that by rendering the
// late-bound global via createElement at render time (not calling it as a plain
// function, and not capturing it at module load before workspace.jsx has run).
export const AtlasStatusBadge = (props: AtlasStatusBadgeProps): ReactNode =>
  createElement(w.AtlasStatusBadge as never, props as never);

// Forward-ref to workspace.jsx helpers. The original .jsx wrapped this as
// `const TodoGraph = (...a) => window.TodoGraph(...a)` and rendered <TodoGraph/>,
// so React mounted THIS lambda and `window.TodoGraph` was invoked as a plain
// function. We keep that exact shape (call, not createElement-mount).
export const TodoGraph = (...a: Parameters<AtlasWindowGlobals['TodoGraph']>): ReactNode => w.TodoGraph(...a);

// ── Loose shapes for the SSOT-backed progress payload (window.ATLAS_PROGRESS).
// The data is produced by the backend / data.jsx; we model only what this panel
// reads and otherwise fall back to `unknown`/index signatures, matching the
// original code's defensive `(x && x.y) || {}` access pattern.
export interface AtlasProgressData {
  modules?: ProgressModule[];
  selected?: ProgressModule;
  [key: string]: unknown;
}
export interface ProgressModule {
  id?: string;
  name?: string;
  label?: string;
  kind?: string;
  ip_dir?: string;
  ssot_path?: string;
  progress?: Record<string, unknown>;
  status?: Record<string, unknown>;
  status_detail?: Record<string, unknown>;
  signoff?: Record<string, unknown>;
  artifact_status?: Record<string, unknown>;
  artifact_detail?: Record<string, unknown>;
  [key: string]: unknown;
}

// ── Loose shape for a single TODO item (window.TODOS entries, produced by
// data.jsx). Only the fields the TODO panel reads are modelled.
export interface TodoItem {
  id?: unknown;
  title?: ReactNode;
  state?: string;
  section?: ReactNode;
  detail?: unknown;
  criteria?: unknown;
  sourceRefs?: unknown;
  ownerModule?: unknown;
  ownerFile?: unknown;
  required?: unknown;
  approvedReason?: unknown;
  rejectionReason?: unknown;
  notes?: unknown;
  deps?: unknown[];
  [key: string]: unknown;
}
