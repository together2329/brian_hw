// workspace-resize-splitters.tsx — reusable layout primitives migrated from
// workspace.jsx (the legacy .jsx remains the live source of truth; this is an
// inert TS mirror).
//
// This module owns:
//   - useResizable / useVerticalResizable — localStorage-backed width/height
//     hooks with clamp + mouse-drag friendly setters.
//   - Splitter / HorizontalSplitter — the drag-handle components that resize
//     adjacent columns/rows.
//
// Self-contained: depends only on browser window/DOM event APIs (no cross-file
// ATLAS globals). Typed in the permissive house style — React synthetic events
// use the react `MouseEvent`/`KeyboardEvent`, while native window listeners use
// `globalThis.MouseEvent`.
import {
  useState,
  useRef,
  useEffect,
  useCallback,
  type MouseEvent,
  type KeyboardEvent,
} from 'react';

// ── Column-resize helpers ─────────────────────────────────────────
// useResizable: state + localStorage persistence + clamp.
// `0` is the special "collapsed" value; any positive width is clamped
// to [minW, maxW]. A separate "lastNonZero" remembers the user's last
// open width so collapse → expand restores cleanly.
export const useResizable = (
  initial: number,
  storageKey: string,
  minW: number,
  maxW: number,
  restoreCollapsed = true,
): [number, (next: number) => void, () => void] => {
  const [w, setW] = useState<number>(() => {
    try {
      const raw = parseInt(localStorage.getItem(storageKey) as string, 10);
      if (Number.isFinite(raw) && raw === 0 && restoreCollapsed) {
        return 0;
      }
      if (Number.isFinite(raw) && raw >= minW) {
        return Math.min(maxW, raw);
      }
    } catch (_) {}
    return initial;
  });
  const lastOpenRef = useRef<number>(w > 0 ? w : initial);
  useEffect(() => {
    if (w > 0) lastOpenRef.current = w;
    try { localStorage.setItem(storageKey, String(w)); } catch (_) {}
  }, [w, storageKey]);
  const set = useCallback((next: number) => {
    if (next === 0) { setW(0); return; }
    setW(Math.max(minW, Math.min(maxW, next)));
  }, [minW, maxW]);
  const toggle = useCallback(() => {
    setW(prev => prev === 0 ? lastOpenRef.current : 0);
  }, []);
  return [w, set, toggle];
};

export const useVerticalResizable = (
  initial: number,
  storageKey: string,
  minH: number,
  maxH: number,
): [number, (next: number) => void, () => void] => {
  const clamp = useCallback(
    (value: number) => Math.max(minH, Math.min(maxH, value)),
    [minH, maxH],
  );
  const [h, setH] = useState<number>(() => {
    try {
      const raw = parseInt(localStorage.getItem(storageKey) as string, 10);
      if (Number.isFinite(raw)) return clamp(raw);
    } catch (_) {}
    return initial;
  });
  useEffect(() => {
    try { localStorage.setItem(storageKey, String(h)); } catch (_) {}
  }, [h, storageKey]);
  const set = useCallback((next: number) => {
    if (!Number.isFinite(next)) return;
    setH(clamp(next));
  }, [clamp]);
  const reset = useCallback(() => setH(initial), [initial]);
  return [h, set, reset];
};

// Splitter: 4px-wide drag handle. drag → resize via onResize(width).
// Double-click → onToggle(). Side='left' resizes the LEFT column
// (drag right widens), side='right' resizes the RIGHT column (drag
// left widens — direction inverted).
export const Splitter = ({
  width,
  side,
  onResize,
  onToggle,
  title,
}: {
  width: number;
  side: 'left' | 'right';
  onResize: (next: number) => void;
  onToggle?: () => void;
  title?: string;
}) => {
  const drag = useRef<{ x: number; w0: number } | null>(null);
  const onMouseDown = (e: MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    drag.current = { x: e.clientX, w0: width };
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
    const onMove = (ev: globalThis.MouseEvent) => {
      if (!drag.current) return;
      const dx = ev.clientX - drag.current.x;
      const next = side === 'left' ? drag.current.w0 + dx : drag.current.w0 - dx;
      onResize(next);
    };
    const onUp = () => {
      drag.current = null;
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };
  return (
    <div
      onMouseDown={onMouseDown}
      onDoubleClick={onToggle}
      title={title || ('drag to resize · double-click to ' + (width === 0 ? 'expand' : 'collapse'))}
      style={{
        cursor: 'col-resize',
        background: 'transparent',
        borderLeft: '1px solid var(--line)',
        borderRight: '1px solid var(--line)',
        height: '100%',
        transition: 'background 120ms',
      }}
      onMouseEnter={(e: MouseEvent<HTMLDivElement>) => { e.currentTarget.style.background = 'color-mix(in oklch, var(--accent) 30%, transparent)'; }}
      onMouseLeave={(e: MouseEvent<HTMLDivElement>) => { e.currentTarget.style.background = 'transparent'; }}
    />
  );
};

export const HorizontalSplitter = ({
  height,
  onResize,
  onReset,
  title,
}: {
  height: number;
  onResize: (next: number) => void;
  onReset: () => void;
  title?: string;
}) => {
  const drag = useRef<{ y: number; h0: number } | null>(null);
  const step = 18;
  const onMouseDown = (e: MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    drag.current = { y: e.clientY, h0: height };
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'row-resize';
    const onMove = (ev: globalThis.MouseEvent) => {
      if (!drag.current) return;
      onResize(drag.current.h0 + (ev.clientY - drag.current.y));
    };
    const onUp = () => {
      drag.current = null;
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      onResize(height - step);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      onResize(height + step);
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onReset();
    }
  };
  return (
    <div
      className="left-stack-splitter"
      role="separator"
      aria-orientation="horizontal"
      aria-label="Resize Workflow and IP panels"
      tabIndex={0}
      title={title || 'drag to resize Workflow/IP split · double-click to reset'}
      onMouseDown={onMouseDown}
      onDoubleClick={onReset}
      onKeyDown={onKeyDown}
    >
      <span className="left-stack-splitter-grip" aria-hidden="true" />
    </div>
  );
};
