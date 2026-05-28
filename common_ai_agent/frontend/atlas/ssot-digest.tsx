// ssot-digest.tsx — TypeScript migration of ssot-digest.jsx.
//
// Phase 13c refactor: SSOT digest + review cluster, originally extracted from
// workspace.jsx. Four components were moved as a unit (DigestCard,
// BlockDiagram, SsotDigestContent, SsotReviewPane); the latter three have
// since been extracted to their own files (block-diagram.jsx Phase 18,
// ssot-review.jsx Phase 21, ssot-digest-content.jsx Phase 22). What remains
// here is the leaf primitive DigestCard.
//
// What changed vs ssot-digest.jsx:
//   - Proper ES module: `import { type ReactNode } from 'react'` instead of
//     the ambient global `React` + `<script type="text/babel">` compile.
//   - The IIFE wrapper is unwrapped (ES modules have their own scope, so the
//     forward-ref consts no longer need an IIFE to avoid colliding with
//     workspace.jsx's same-named definitions).
//   - Real typed export (`DigestCard`) — consumers will `import` it once they
//     migrate.
//
// Transitional: still bridges to `window.DigestCard` at the bottom so
// not-yet-migrated .jsx files (e.g. ssot-digest-content.jsx) keep resolving
// the global component.
//
// Load order (index.html): AFTER preview-pane.jsx, BEFORE workspace.jsx.
import { type ReactNode } from 'react';

export interface DigestCardProps {
  title?: ReactNode;
  meta?: string;
  children?: ReactNode;
}

export const DigestCard = ({ title, meta, children }: DigestCardProps) => (
  <div style={{
    border: '1px solid var(--line)', borderRadius: 4,
    background: 'var(--bg-2)', padding: '10px 12px', minWidth: 0,
  }}>
    <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', marginBottom: 7 }}>
      <span style={{ color: 'var(--accent)', fontWeight: 800, fontSize: 12 }}>{title}</span>
      {meta ? <span className="mute trunc" style={{ fontSize: 10, fontFamily: 'var(--mono)' }}>{meta}</span> : null}
    </div>
    {children}
  </div>
);

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// Phase 13c window export — workspace.jsx / ssot-digest-content.jsx alias this
// back. `DigestCard` is not yet declared on the ambient Window in
// types/atlas-window.d.ts, so cast to attach the global without changing
// runtime behavior (the .d.ts entry is added when consumers migrate).
//
// BlockDiagram extracted to block-diagram.jsx in Phase 18 (registered there).
// SsotDigestContent extracted to ssot-digest-content.jsx in Phase 22.
// SsotReviewPane extracted to ssot-review.jsx in Phase 21.
(window as unknown as { DigestCard: typeof DigestCard }).DigestCard = DigestCard;
