// workspace-chat-markdown-frame.tsx — isolated iframe renderer for completed
// assistant Markdown bodies in the main chat feed.
import { useState, useEffect, useRef, useMemo, useCallback, type ReactNode } from 'react';

import {
  _markdownHtml,
  _postProcessMarkdownNode,
} from './workspace-markdown-chips';

const CHAT_MARKDOWN_FRAME_CSS = `
  :root {
    color-scheme: dark;
    --doc-bg: #070b10;
    --doc-panel-2: #0b1118;
    --doc-panel-3: #0d141c;
    --doc-line: #263240;
    --doc-fg: #d7e2ee;
    --doc-muted: #94a3b8;
    --doc-accent: #80d8ff;
    --doc-code-font: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    --doc-body-font: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  html[data-theme="light"] {
    color-scheme: light;
    --doc-bg: #ffffff;
    --doc-panel-2: #f3f6fb;
    --doc-panel-3: #eef3f8;
    --doc-line: #d6dee8;
    --doc-fg: #17202b;
    --doc-muted: #64748b;
    --doc-accent: #0b6ea8;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; min-height: 100%; background: var(--doc-bg); }
  body {
    color: var(--doc-fg);
    font-family: var(--doc-body-font);
    font-size: 14px;
    line-height: 1.68;
    overflow: hidden;
  }
  .md-chat-frame-body {
    width: 100%;
    max-width: 88ch;
    margin: 0;
    padding: 2px 0 4px;
    background: var(--doc-bg);
  }
  .md-chat-frame-body > :first-child { margin-top: 0; }
  .md-chat-frame-body > :last-child { margin-bottom: 0; }
  .md-chat-frame-body p,
  .md-chat-frame-body ul,
  .md-chat-frame-body ol,
  .md-chat-frame-body blockquote { margin: 0 0 .95rem; }
  .md-chat-frame-body h1,
  .md-chat-frame-body h2,
  .md-chat-frame-body h3,
  .md-chat-frame-body h4 {
    color: var(--doc-fg);
    line-height: 1.25;
    letter-spacing: 0;
  }
  .md-chat-frame-body h1 {
    margin: 0 0 .95rem;
    padding-bottom: .55rem;
    border-bottom: 1px solid var(--doc-line);
    font-size: 1.55rem;
    font-weight: 800;
  }
  .md-chat-frame-body h2 {
    margin: 1.55rem 0 .75rem;
    padding-bottom: .3rem;
    border-bottom: 1px solid var(--doc-line);
    font-size: 1.22rem;
    font-weight: 760;
  }
  .md-chat-frame-body h3 {
    margin: 1.25rem 0 .55rem;
    font-size: 1.02rem;
    font-weight: 740;
    color: var(--doc-accent);
  }
  .md-chat-frame-body h4 { margin: 1rem 0 .4rem; font-size: .95rem; font-weight: 720; }
  .md-chat-frame-body ul,
  .md-chat-frame-body ol { padding-left: 1.45rem; }
  .md-chat-frame-body li { margin: .2rem 0; padding-left: .1rem; }
  .md-chat-frame-body a { color: var(--doc-accent); text-decoration: none; }
  .md-chat-frame-body a:hover { text-decoration: underline; }
  .md-chat-frame-body code {
    padding: .1rem .32rem;
    border: 1px solid var(--doc-line);
    border-radius: 4px;
    background: var(--doc-panel-2);
    color: var(--doc-fg);
    font-family: var(--doc-code-font);
    font-size: .9em;
  }
  .md-chat-frame-body pre {
    margin: .95rem 0 1.05rem;
    padding: .9rem 1rem;
    overflow: auto;
    border: 1px solid var(--doc-line);
    border-radius: 6px;
    background: #05080c;
    white-space: pre;
  }
  html[data-theme="light"] .md-chat-frame-body pre { background: #f6f8fb; }
  .md-chat-frame-body pre code {
    padding: 0;
    border: 0;
    background: transparent;
    color: inherit;
    font-size: .9rem;
    line-height: 1.58;
  }
  .md-chat-frame-body table {
    width: 100%;
    margin: .95rem 0 1.1rem;
    border-collapse: collapse;
    border: 1px solid var(--doc-line);
    border-radius: 6px;
    overflow: hidden;
    background: var(--doc-bg);
  }
  .md-chat-frame-body th,
  .md-chat-frame-body td {
    padding: .5rem .62rem;
    border: 1px solid var(--doc-line);
    vertical-align: top;
  }
  .md-chat-frame-body th {
    background: var(--doc-panel-3);
    color: var(--doc-fg);
    font-weight: 750;
  }
  .md-chat-frame-body blockquote {
    padding: .75rem .95rem;
    border-left: 3px solid var(--doc-accent);
    border-radius: 0 6px 6px 0;
    background: var(--doc-panel-3);
    color: var(--doc-muted);
  }
  .md-chat-frame-body hr {
    margin: 1.5rem 0;
    border: 0;
    border-top: 1px solid var(--doc-line);
  }
  .md-chat-frame-body img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: .95rem auto;
    border: 1px solid var(--doc-line);
    border-radius: 6px;
    background: #05080c;
  }
  html[data-theme="light"] .md-chat-frame-body img { background: #ffffff; }
  .md-chat-frame-body input[type="checkbox"] { transform: translateY(1px); margin-right: .4rem; }
  .atlas-mermaid-block {
    margin: .95rem 0 1.1rem;
    padding: .95rem;
    border: 1px solid var(--doc-line);
    border-radius: 6px;
    background: var(--doc-panel-2);
    overflow: auto;
  }
  .stream-caret {
    display: inline-block;
    width: 2px;
    height: 1em;
    margin-left: 2px;
    background: var(--doc-accent);
    vertical-align: text-bottom;
    animation: blink 0.7s step-end infinite;
  }
  @keyframes blink {
    50% { opacity: 0; }
  }
`;

const chatMarkdownTheme = (): string => {
  if (typeof document === 'undefined') return 'dark';
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
};

export const ChatMarkdownFrame = ({ text, streaming = false }: { text: unknown; streaming?: boolean }): ReactNode => {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const [height, setHeight] = useState(44);
  const [theme, setTheme] = useState(chatMarkdownTheme);
  const html = useMemo(() => _markdownHtml(text || ''), [text]);

  useEffect(() => {
    if (typeof document === 'undefined') return undefined;
    const sync = () => setTheme(chatMarkdownTheme());
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  const postProcessFrame = useCallback(() => {
    const doc = frameRef.current?.contentDocument;
    const root = doc?.querySelector('.md-chat-frame-body') as HTMLElement | null;
    if (!doc || !root) return;
    resizeObserverRef.current?.disconnect();
    _postProcessMarkdownNode(root);
    const measure = () => {
      const next = Math.ceil(Math.max(
        root.scrollHeight || 0,
        doc.body?.scrollHeight || 0,
        doc.documentElement?.scrollHeight || 0,
        44,
      ));
      setHeight(next + 2);
    };
    root.querySelectorAll('img').forEach(img => {
      img.addEventListener('load', measure, { once: true });
      img.addEventListener('error', measure, { once: true });
    });
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserverRef.current = new ResizeObserver(measure);
      resizeObserverRef.current.observe(root);
    }
    window.requestAnimationFrame(measure);
    window.setTimeout(measure, 120);
  }, [html]);

  useEffect(() => () => resizeObserverRef.current?.disconnect(), []);

  const srcDoc = useMemo(() => {
    const frameTheme = theme === 'light' ? 'light' : 'dark';
    return `<!doctype html>
<html data-theme="${frameTheme}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <base target="_blank" />
  <style>${CHAT_MARKDOWN_FRAME_CSS}</style>
</head>
<body>
  <main class="md-agent md-chat-frame-body">${html}${streaming ? '<span class="stream-caret" aria-hidden="true"></span>' : ''}</main>
</body>
</html>`;
  }, [html, streaming, theme]);

  return (
    <iframe
      ref={frameRef}
      className="chat-markdown-frame"
      title="Agent Markdown response"
      sandbox="allow-same-origin allow-popups"
      referrerPolicy="no-referrer"
      srcDoc={srcDoc}
      onLoad={postProcessFrame}
      style={{
        width: '100%',
        height,
        minHeight: 44,
        border: 0,
        display: 'block',
        marginTop: 4,
        background: theme === 'light' ? '#ffffff' : '#070b10',
        overflow: 'hidden',
      }}
    />
  );
};
