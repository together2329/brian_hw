// workspace-tool-detail-frame.tsx — isolated iframe renderer for expanded
// tool-call result bodies.
import { useState, useEffect, useRef, useMemo, useCallback, type ReactNode } from 'react';

import {
  _markdownHtml,
  _normalizeDisplayedToolPaths,
  _postProcessMarkdownNode,
  _grepOutputRows,
  _highlightInlineCode,
  _toolOutputLanguage,
} from './workspace-markdown-chips';

export type ToolDetailFrameMode = 'text' | 'diff' | 'grep' | 'markdown';

export interface ToolDetailFrameProps {
  text: unknown;
  mode?: ToolDetailFrameMode;
  tool?: unknown;
  truncated?: boolean;
  maxLines?: number;
  title?: string;
  hintText?: string;
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
    --tool-body-font-size: 12px;
    --tool-markdown-font-size: 13px;
    --tool-code-font-size: 11.5px;
    --tool-markdown-line-height: 1.62;
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
  html, body { margin: 0; height: auto; min-height: 0; background: var(--tool-bg); }
  body {
    color: var(--tool-fg);
    font-family: var(--tool-body-font);
    font-size: var(--tool-body-font-size);
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
    font-size: var(--tool-code-font-size);
    line-height: 1.52;
    white-space: pre;
  }
  .tool-detail-pre.tool-detail-grep { white-space: pre-wrap; word-break: break-word; }
  .tool-detail-code code,
  .tool-detail-diff code,
  .tool-detail-grep code {
    padding: 0;
    border: 0;
    background: transparent;
    color: inherit;
    font: inherit;
  }
  .tool-detail-grep {
    display: block;
  }
  .grep-line {
    display: block;
    min-height: 1.52em;
    white-space: pre-wrap;
  }
  .grep-match {
    background: color-mix(in oklch, var(--tool-accent) 12%, transparent);
  }
  .grep-prefix {
    display: inline-block;
    min-width: 3.25rem;
    padding-right: .42rem;
    color: var(--tool-muted);
    text-align: right;
    user-select: none;
  }
  .grep-file {
    color: var(--tool-meta);
  }
  .grep-sep {
    padding-right: .5rem;
    color: var(--tool-muted);
    user-select: none;
  }
  .diff-line {
    display: block;
    min-height: 1.52em;
    padding-left: .42rem;
    border-left: 2px solid transparent;
    white-space: pre;
  }
  .diff-line.add {
    color: var(--tool-add);
    border-left-color: var(--tool-add);
    background: color-mix(in oklch, var(--tool-add) 16%, transparent);
  }
  .diff-line.del {
    color: var(--tool-del);
    border-left-color: var(--tool-del);
    background: color-mix(in oklch, var(--tool-del) 16%, transparent);
  }
  .diff-line.meta { color: var(--tool-meta); }
  .diff-line.ctx { color: var(--tool-fg); }
  .diff-prefix {
    color: var(--tool-muted);
    user-select: none;
  }
  .tool-detail-muted {
    margin-top: .45rem;
    color: var(--tool-muted);
    font-family: var(--tool-code-font);
    font-size: var(--tool-code-font-size);
  }
  .tool-detail-markdown {
    max-width: 100%;
    color: var(--tool-fg);
    background: var(--tool-bg);
    font-size: var(--tool-markdown-font-size);
    line-height: var(--tool-markdown-line-height);
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
    font-size: var(--tool-code-font-size);
  }
  .tool-detail-markdown table {
    width: 100%;
    margin: .85rem 0 .95rem;
    border-collapse: collapse;
    border: 1px solid var(--tool-line);
    background: var(--tool-bg);
  }
  .tool-detail-markdown .md-table-scroll {
    max-width: 100%;
    margin: .85rem 0 .95rem;
    overflow-x: auto;
    overflow-y: hidden;
    border: 1px solid var(--tool-line);
    border-radius: 6px;
    background: var(--tool-bg);
  }
  .tool-detail-markdown .md-table-scroll > table {
    width: max-content;
    min-width: 100%;
    margin: 0;
    border: 0;
    background: transparent;
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
  .token.comment,
  .token.prolog,
  .token.doctype,
  .token.cdata { color: #7d8590; }
  .token.punctuation { color: #c9d1d9; }
  .token.property,
  .token.tag,
  .token.boolean,
  .token.number,
  .token.constant,
  .token.symbol,
  .token.deleted { color: #ff8a8a; }
  .token.selector,
  .token.attr-name,
  .token.string,
  .token.char,
  .token.builtin,
  .token.inserted { color: #9be28f; }
  .token.operator,
  .token.entity,
  .token.url,
  .language-css .token.string,
  .style .token.string { color: #80d8ff; }
  .token.atrule,
  .token.attr-value,
  .token.keyword { color: #d2a8ff; }
  .token.function,
  .token.class-name { color: #ffd166; }
  .token.regex,
  .token.important,
  .token.variable { color: #ffa657; }
`;

const toolDetailTheme = (): string => {
  if (typeof document === 'undefined') return 'dark';
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
};

type FrameTypography = {
  bodyFontSize: string;
  markdownFontSize: string;
  codeFontSize: string;
  markdownLineHeight: string;
};

const cssPxValue = (value: string, fallback: string): string => {
  const trimmed = value.trim();
  return /^\d+(?:\.\d+)?px$/.test(trimmed) ? trimmed : fallback;
};

const cssLineHeightValue = (value: string, fallback: string): string => {
  const trimmed = value.trim();
  return /^(?:\d+(?:\.\d+)?|\d+(?:\.\d+)?px)$/.test(trimmed) ? trimmed : fallback;
};

const toolDetailTypography = (): FrameTypography => {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return {
      bodyFontSize: '12px',
      markdownFontSize: '13px',
      codeFontSize: '11.5px',
      markdownLineHeight: '1.62',
    };
  }
  const rootStyle = window.getComputedStyle(document.documentElement);
  return {
    bodyFontSize: cssPxValue(rootStyle.getPropertyValue('--ui-control-font-size'), '12px'),
    markdownFontSize: cssPxValue(rootStyle.getPropertyValue('--ui-agent-font-size'), '13px'),
    codeFontSize: cssPxValue(rootStyle.getPropertyValue('--ui-code-font-size'), '11.5px'),
    markdownLineHeight: cssLineHeightValue(rootStyle.getPropertyValue('--ui-agent-line-height'), '1.62'),
  };
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

const safeLanguageClass = (lang: string): string => (
  /^[a-z0-9_-]{1,40}$/i.test(lang) ? lang : 'none'
);

export const highlightedToolCodeHtml = (code: unknown, lang: string): string => {
  const safeLang = safeLanguageClass(lang);
  if (!safeLang || safeLang === 'none') return escapeHtml(code);
  return _highlightInlineCode(String(code ?? ''), safeLang);
};

export const toolDetailLanguage = (tool: unknown, text: unknown, hintText = ''): string => {
  if (/^run_command$/i.test(String(tool || ''))) return 'none';
  const body = String(text ?? '');
  const hint = String(hintText || '');
  const lang = _toolOutputLanguage(tool, `${hint}\n${body}`);
  return safeLanguageClass(lang);
};

export const diffClassForLine = (line: string): string => {
  if (/^(diff --git|index |@@|\+\+\+ |--- )/.test(line)) return 'meta';
  if (/^\s*(?:\d+|[|>]*\s*\d+)\s+\+/.test(line)) return 'add';
  if (/^\s*(?:\d+|[|>]*\s*\d+)\s+-/.test(line)) return 'del';
  if (line.startsWith('+')) return 'add';
  if (line.startsWith('-')) return 'del';
  return 'ctx';
};

export const renderedToolBodyHtml = (
  text: string,
  mode: ToolDetailFrameMode,
  truncated?: boolean,
  maxLines?: number,
  tool?: unknown,
  hintText = '',
  languageOverride = '',
): string => {
  const { text: visibleText, hidden } = clampToolText(stripAnsi(_normalizeDisplayedToolPaths(text)), maxLines);
  const lang = safeLanguageClass(languageOverride || toolDetailLanguage(tool, visibleText, hintText));
  const codeClass = lang && lang !== 'none' ? `language-${lang}` : 'language-none';
  const footer = [
    hidden > 0 ? `${hidden} more line${hidden === 1 ? '' : 's'} hidden; expand for full output` : '',
    truncated ? '...[truncated]' : '',
  ].filter(Boolean).map(line => `<div class="tool-detail-muted">${escapeHtml(line)}</div>`).join('');

  if (mode === 'markdown') {
    return `<section class="md-agent tool-detail-markdown">${_markdownHtml(visibleText)}</section>${footer}`;
  }
  if (mode === 'diff') {
    const codeOnly = visibleText.split('\n').map((line) => (
      line.replace(/^\s*(?:\d+|[|>]*\s*\d+)\s+[ +-]/, '')
        .replace(/^[+-]/, '')
    )).join('\n');
    const diffLang = safeLanguageClass(languageOverride || toolDetailLanguage(tool, codeOnly, hintText || visibleText));
    const diffCodeClass = diffLang && diffLang !== 'none' ? `language-${diffLang}` : 'language-none';
    const rows = visibleText.split('\n')
      .map((line) => {
        const kind = diffClassForLine(line);
        if (kind === 'meta') {
          return `<span class="diff-line ${kind}">${escapeHtml(line) || ' '}</span>`;
        }
        const match = line.match(/^(\s*(?:\d+|[|>]*\s*\d+)\s+)([ +-])(.*)$/);
        const bare = !match ? line.match(/^([+-])(.*)$/) : null;
        const prefix = match ? `${match[1]}${match[2]}` : (bare ? bare[1] : '');
        const code = match ? match[3] : (bare ? bare[2] : line);
        return `<span class="diff-line ${kind}"><span class="diff-prefix">${escapeHtml(prefix)}</span><code class="${diffCodeClass}">${highlightedToolCodeHtml(code, diffLang) || ' '}</code></span>`;
      })
      .join('');
    return `<pre class="tool-detail-pre tool-detail-diff ${diffCodeClass}">${rows}</pre>${footer}`;
  }
  if (mode === 'grep') {
    const rows = _grepOutputRows(visibleText)
      .map((row) => {
        if (!row.lineNumber) {
          return `<span class="grep-line grep-${row.kind}">${escapeHtml(row.text) || ' '}</span>`;
        }
        const rowLang = safeLanguageClass(toolDetailLanguage(tool, row.code, row.file || hintText || visibleText));
        const rowCodeClass = rowLang && rowLang !== 'none' ? `language-${rowLang}` : 'language-none';
        const file = row.file ? `<span class="grep-file">${escapeHtml(row.file)}</span><span class="grep-sep">:</span>` : '';
        return `<span class="grep-line grep-${row.kind}">${file}<span class="grep-prefix">${escapeHtml(row.lineNumber)}</span><span class="grep-sep">|</span><code class="${rowCodeClass}">${highlightedToolCodeHtml(row.code, rowLang) || ' '}</code></span>`;
      })
      .join('');
    return `<pre class="tool-detail-pre tool-detail-grep">${rows}</pre>${footer}`;
  }
  return `<pre class="tool-detail-pre tool-detail-code ${codeClass}"><code class="${codeClass}">${highlightedToolCodeHtml(visibleText, lang)}</code></pre>${footer}`;
};

export const ToolDetailFrame = ({
  text,
  mode = 'text',
  tool,
  truncated = false,
  maxLines,
  title,
  hintText = '',
}: ToolDetailFrameProps): ReactNode => {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const pendingMeasureFrameRef = useRef<number | null>(null);
  const [height, setHeight] = useState(42);
  const [theme, setTheme] = useState(toolDetailTheme);
  const [typography, setTypography] = useState(toolDetailTypography);
  const [grammarTick, setGrammarTick] = useState(0);
  const normalizedMode = mode === 'markdown' || mode === 'diff' || mode === 'grep' ? mode : 'text';
  const language = useMemo(
    () => toolDetailLanguage(tool, text, hintText),
    [tool, text, hintText],
  );
  const bodyHtml = useMemo(
    () => renderedToolBodyHtml(String(text ?? ''), normalizedMode, truncated, maxLines, tool, hintText, language),
    [text, normalizedMode, truncated, maxLines, tool, hintText, language, grammarTick],
  );

  useEffect(() => {
    const Prism = window.Prism;
    if (!Prism || !language || language === 'none' || (Prism.languages && Prism.languages[language])) return undefined;
    if (Prism.plugins && Prism.plugins.autoloader && Prism.plugins.autoloader.loadLanguages) {
      try {
        Prism.plugins.autoloader.loadLanguages(language, () => setGrammarTick((tick: number) => tick + 1));
      } catch (_) {}
    }
    return undefined;
  }, [language, text, hintText]);

  useEffect(() => {
    if (typeof document === 'undefined') return undefined;
    const sync = () => {
      setTheme(toolDetailTheme());
      setTypography(toolDetailTypography());
    };
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme', 'data-font-scale', 'data-platform', 'style'],
    });
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
      const rectHeight = root.getBoundingClientRect().height || 0;
      const viewportHeight = frameRef.current?.contentWindow?.innerHeight || 0;
      const stableMetric = (value: number): number => {
        if (!value) return 0;
        if (viewportHeight > 0 && value > rectHeight + 1 && Math.abs(value - viewportHeight) <= 1) {
          return 0;
        }
        return value;
      };
      const next = Math.ceil(Math.max(
        stableMetric(root.scrollHeight || 0),
        stableMetric(root.offsetHeight || 0),
        rectHeight,
        42,
      ));
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
    const typographyCss = `
  :root {
    --tool-body-font-size: ${typography.bodyFontSize};
    --tool-markdown-font-size: ${typography.markdownFontSize};
    --tool-code-font-size: ${typography.codeFontSize};
    --tool-markdown-line-height: ${typography.markdownLineHeight};
  }
`;
    return `<!doctype html>
<html data-theme="${frameTheme}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <base target="_blank" />
  <style>${TOOL_DETAIL_FRAME_CSS}</style>
  <style>${typographyCss}</style>
</head>
<body>
  <main class="tool-detail-frame-body" data-mode="${normalizedMode}">${bodyHtml}</main>
</body>
</html>`;
  }, [bodyHtml, normalizedMode, theme, typography]);

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
