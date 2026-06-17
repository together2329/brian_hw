// workspace-tool-detail-frame.tsx — isolated iframe renderer for expanded
// tool-call result bodies.
import { useState, useEffect, useRef, useMemo, useCallback, type ReactNode } from 'react';

import {
  _markdownHtml,
  _postProcessMarkdownNode,
} from './workspace-markdown-chips';

export type ToolDetailFrameMode = 'text' | 'diff' | 'grep' | 'markdown';

export interface ToolDetailFrameProps {
  text: unknown;
  mode?: ToolDetailFrameMode;
  tool?: unknown;
  truncated?: boolean;
  maxLines?: number;
  title?: string;
}

const TOOL_DETAIL_FRAME_CSS = `
  :root {
    color-scheme: dark;
    --tool-bg: #070b10;
    --tool-panel: #05080c;
    --tool-panel-2: #0b1118;
    --tool-line: #263240;
    --tool-fg: #d7e2ee;
    --tool-muted: #94a3b8;
    --tool-accent: #80d8ff;
    --tool-add: #7ee787;
    --tool-del: #ff8a8a;
    --tool-meta: #9fb8ff;
    --tool-code-font: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    --tool-body-font: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  html[data-theme="light"] {
    color-scheme: light;
    --tool-bg: #ffffff;
    --tool-panel: #f6f8fb;
    --tool-panel-2: #eef3f8;
    --tool-line: #d6dee8;
    --tool-fg: #17202b;
    --tool-muted: #64748b;
    --tool-accent: #0b6ea8;
    --tool-add: #176f2c;
    --tool-del: #b42318;
    --tool-meta: #2451a6;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; min-height: 100%; background: var(--tool-bg); }
  body {
    color: var(--tool-fg);
    font-family: var(--tool-body-font);
    font-size: 12px;
    line-height: 1.55;
    overflow: hidden;
  }
  .tool-detail-frame-body {
    width: 100%;
    margin: 0;
    padding: 0;
    background: var(--tool-bg);
  }
  .tool-detail-pre {
    width: 100%;
    margin: 0;
    padding: .72rem .82rem;
    overflow: auto;
    border: 1px solid var(--tool-line);
    border-radius: 6px;
    background: var(--tool-panel);
    color: var(--tool-fg);
    font-family: var(--tool-code-font);
    font-size: 11.5px;
    line-height: 1.52;
    white-space: pre;
  }
  .tool-detail-pre.tool-detail-grep { white-space: pre-wrap; word-break: break-word; }
  .diff-line { display: block; min-height: 1.52em; }
  .diff-line.add { color: var(--tool-add); }
  .diff-line.del { color: var(--tool-del); }
  .diff-line.meta { color: var(--tool-meta); }
  .diff-line.ctx { color: var(--tool-fg); }
  .tool-detail-muted {
    margin-top: .45rem;
    color: var(--tool-muted);
    font-family: var(--tool-code-font);
    font-size: 11px;
  }
  .tool-detail-markdown {
    max-width: 88ch;
    color: var(--tool-fg);
    background: var(--tool-bg);
    font-size: 13px;
    line-height: 1.62;
  }
  .tool-detail-markdown > :first-child { margin-top: 0; }
  .tool-detail-markdown > :last-child { margin-bottom: 0; }
  .tool-detail-markdown p,
  .tool-detail-markdown ul,
  .tool-detail-markdown ol,
  .tool-detail-markdown blockquote { margin: 0 0 .85rem; }
  .tool-detail-markdown h1,
  .tool-detail-markdown h2,
  .tool-detail-markdown h3,
  .tool-detail-markdown h4 {
    margin: 1.1rem 0 .55rem;
    color: var(--tool-fg);
    line-height: 1.25;
    letter-spacing: 0;
  }
  .tool-detail-markdown h1 { margin-top: 0; padding-bottom: .45rem; border-bottom: 1px solid var(--tool-line); font-size: 1.35rem; }
  .tool-detail-markdown h2 { padding-bottom: .25rem; border-bottom: 1px solid var(--tool-line); font-size: 1.12rem; }
  .tool-detail-markdown h3 { color: var(--tool-accent); font-size: 1rem; }
  .tool-detail-markdown ul,
  .tool-detail-markdown ol { padding-left: 1.35rem; }
  .tool-detail-markdown li { margin: .18rem 0; }
  .tool-detail-markdown a { color: var(--tool-accent); text-decoration: none; }
  .tool-detail-markdown a:hover { text-decoration: underline; }
  .tool-detail-markdown code {
    padding: .08rem .28rem;
    border: 1px solid var(--tool-line);
    border-radius: 4px;
    background: var(--tool-panel-2);
    color: var(--tool-fg);
    font-family: var(--tool-code-font);
    font-size: .9em;
  }
  .tool-detail-markdown pre {
    margin: .8rem 0 .95rem;
    padding: .75rem .82rem;
    overflow: auto;
    border: 1px solid var(--tool-line);
    border-radius: 6px;
    background: var(--tool-panel);
    white-space: pre;
  }
  .tool-detail-markdown pre code {
    padding: 0;
    border: 0;
    background: transparent;
    color: inherit;
    font-size: 11.5px;
  }
  .tool-detail-markdown table {
    width: 100%;
    margin: .85rem 0 .95rem;
    border-collapse: collapse;
    border: 1px solid var(--tool-line);
    background: var(--tool-bg);
  }
  .tool-detail-markdown th,
  .tool-detail-markdown td {
    padding: .45rem .55rem;
    border: 1px solid var(--tool-line);
    vertical-align: top;
  }
  .tool-detail-markdown th { background: var(--tool-panel-2); font-weight: 750; }
  .tool-detail-markdown blockquote {
    padding: .65rem .82rem;
    border-left: 3px solid var(--tool-accent);
    border-radius: 0 6px 6px 0;
    background: var(--tool-panel-2);
    color: var(--tool-muted);
  }
`;

const toolDetailTheme = (): string => {
  if (typeof document === 'undefined') return 'dark';
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
};

const escapeHtml = (value: unknown): string => String(value ?? '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

const stripAnsi = (value: string): string => value.replace(/\x1b\[[\d;]*m/g, '');

const clampToolText = (value: string, maxLines?: number): { text: string; hidden: number } => {
  if (!maxLines || maxLines <= 0) return { text: value, hidden: 0 };
  const lines = value.split('\n');
  if (lines.length <= maxLines) return { text: value, hidden: 0 };
  return { text: lines.slice(0, maxLines).join('\n'), hidden: lines.length - maxLines };
};

const diffClassForLine = (line: string): string => {
  if (/^(diff --git|index |@@|\+\+\+ |--- )/.test(line)) return 'meta';
  if (line.startsWith('+')) return 'add';
  if (line.startsWith('-')) return 'del';
  return 'ctx';
};

const renderedToolBodyHtml = (
  text: string,
  mode: ToolDetailFrameMode,
  truncated?: boolean,
  maxLines?: number,
): string => {
  const { text: visibleText, hidden } = clampToolText(stripAnsi(text), maxLines);
  const footer = [
    hidden > 0 ? `${hidden} more line${hidden === 1 ? '' : 's'} hidden; expand for full output` : '',
    truncated ? '...[truncated]' : '',
  ].filter(Boolean).map(line => `<div class="tool-detail-muted">${escapeHtml(line)}</div>`).join('');

  if (mode === 'markdown') {
    return `<section class="md-agent tool-detail-markdown">${_markdownHtml(visibleText)}</section>${footer}`;
  }
  if (mode === 'diff') {
    const rows = visibleText.split('\n')
      .map(line => `<span class="diff-line ${diffClassForLine(line)}">${escapeHtml(line) || ' '}</span>`)
      .join('');
    return `<pre class="tool-detail-pre tool-detail-diff">${rows}</pre>${footer}`;
  }
  const preClass = mode === 'grep' ? 'tool-detail-pre tool-detail-grep' : 'tool-detail-pre';
  return `<pre class="${preClass}">${escapeHtml(visibleText)}</pre>${footer}`;
};

export const ToolDetailFrame = ({
  text,
  mode = 'text',
  tool,
  truncated = false,
  maxLines,
  title,
}: ToolDetailFrameProps): ReactNode => {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const pendingMeasureFrameRef = useRef<number | null>(null);
  const [height, setHeight] = useState(42);
  const [theme, setTheme] = useState(toolDetailTheme);
  const normalizedMode = mode === 'markdown' || mode === 'diff' || mode === 'grep' ? mode : 'text';
  const bodyHtml = useMemo(
    () => renderedToolBodyHtml(String(text ?? ''), normalizedMode, truncated, maxLines),
    [text, normalizedMode, truncated, maxLines],
  );

  useEffect(() => {
    if (typeof document === 'undefined') return undefined;
    const sync = () => setTheme(toolDetailTheme());
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  const postProcessFrame = useCallback(() => {
    const doc = frameRef.current?.contentDocument;
    const root = doc?.querySelector('.tool-detail-frame-body') as HTMLElement | null;
    if (!doc || !root) return;
    resizeObserverRef.current?.disconnect();
    if (pendingMeasureFrameRef.current !== null) {
      window.cancelAnimationFrame(pendingMeasureFrameRef.current);
      pendingMeasureFrameRef.current = null;
    }
    if (normalizedMode === 'markdown') {
      _postProcessMarkdownNode(root);
    }
    const measure = () => {
      pendingMeasureFrameRef.current = null;
      const next = Math.ceil(Math.max(
        root.scrollHeight || 0,
        doc.body?.scrollHeight || 0,
        doc.documentElement?.scrollHeight || 0,
        42,
      )) + 2;
      setHeight(prev => (Math.abs(prev - next) <= 1 ? prev : next));
    };
    const scheduleMeasure = () => {
      if (pendingMeasureFrameRef.current !== null) return;
      pendingMeasureFrameRef.current = window.requestAnimationFrame(measure);
    };
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserverRef.current = new ResizeObserver(() => scheduleMeasure());
      resizeObserverRef.current.observe(root);
    }
    scheduleMeasure();
    window.setTimeout(scheduleMeasure, 120);
  }, [bodyHtml, normalizedMode]);

  useEffect(() => () => {
    resizeObserverRef.current?.disconnect();
    if (pendingMeasureFrameRef.current !== null) {
      window.cancelAnimationFrame(pendingMeasureFrameRef.current);
      pendingMeasureFrameRef.current = null;
    }
  }, []);

  const srcDoc = useMemo(() => {
    const frameTheme = theme === 'light' ? 'light' : 'dark';
    return `<!doctype html>
<html data-theme="${frameTheme}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <base target="_blank" />
  <style>${TOOL_DETAIL_FRAME_CSS}</style>
</head>
<body>
  <main class="tool-detail-frame-body" data-mode="${normalizedMode}">${bodyHtml}</main>
</body>
</html>`;
  }, [bodyHtml, normalizedMode, theme]);

  return (
    <iframe
      ref={frameRef}
      className="tool-detail-frame"
      title={title || `Tool result${tool ? `: ${String(tool)}` : ''}`}
      sandbox="allow-same-origin allow-popups"
      referrerPolicy="no-referrer"
      srcDoc={srcDoc}
      onLoad={postProcessFrame}
      style={{
        width: '100%',
        height,
        minHeight: 42,
        border: 0,
        display: 'block',
        marginTop: 2,
        background: theme === 'light' ? '#ffffff' : '#070b10',
        overflow: 'hidden',
      }}
    />
  );
};
