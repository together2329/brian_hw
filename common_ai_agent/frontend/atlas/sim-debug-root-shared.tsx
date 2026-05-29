// sim-debug-root-shared.tsx — cross-file window view + shared types extracted
// from sim-debug.tsx (strangler-fig split). Behavior-identical: this is the
// SAME locally-typed `window` view (`g`) and the SAME runtime aliases for the
// window-owned components (AtlasTitle / TimeRuler / WaveRow / WaveCursor) that
// previously lived inline at the top of sim-debug.tsx. Pulling them into a
// shared module lets sim-debug.tsx and its presentational siblings
// (sim-debug-shortcuts.tsx / sim-debug-chat.tsx) read the SAME window view
// without duplicating the interface.
//
// Window-sourced values stay typed as `any` on purpose (same permissive house
// style as sim-debug-helpers.tsx) — do NOT tighten them.
//
// Load order: imported by sim-debug.tsx (and its siblings). Owns no window
// bridge of its own — the `window.SimDebug` bridge stays in sim-debug.tsx,
// which owns the SimDebug symbol.
import type { ReactNode } from 'react';
import type { VcdData } from './sim-debug-helpers';

// ── Cross-file globals owned by OTHER (unmigrated) files. Typed via a local
// view of `window`; behavior identical to the legacy implicit globals. These
// are workspace/data/wave primitives the root renders or reads at runtime.
export interface BackendBridge {
  subscribe?: (event: string, cb: (m: any) => void) => (() => void) | void;
  send?: (msg: { type: string; text: string }) => void;
}
export interface SimDebugProps {
  view?: string;
  initialTab?: string;
}
export interface SimDebugRootWindow {
  ACTIVE_SESSION?: string;
  backend?: BackendBridge;
  parseVCD?: (content: string) => VcdData;
  WAVE_TIME_START?: number;
  WAVE_TIME_END?: number;
  AtlasTitle: (...a: any[]) => any;
  TimeRuler: (...a: any[]) => any;
  WaveRow: (...a: any[]) => any;
  WaveCursor: (...a: any[]) => any;
  // sim-debug.tsx's OWN public global (set via the transitional bridge there).
  SimDebug?: (props?: SimDebugProps) => ReactNode;
}
export const g = (typeof window !== 'undefined' ? window : ({} as Window)) as unknown as SimDebugRootWindow;

// Runtime aliases for the window-owned components so JSX reads cleanly while
// still resolving at call time (no module-ordering dependency on the owners).
export const AtlasTitle = (props: any) => g.AtlasTitle(props);
export const TimeRuler = (props: any) => g.TimeRuler(props);
export const WaveRow = (props: any) => g.WaveRow(props);
export const WaveCursor = (props: any) => g.WaveCursor(props);

// Shared local types used across the root + its presentational siblings.
export type ViewRange = [number, number] | null;
export type ChatEntry = { kind: string; text: string; ts: number };
export interface SrcRange { from: number; to: number; hl: number[]; cur: number }
