// preview-pane.tsx — TypeScript migration of preview-pane.jsx (strangler-fig).
// Phase 13d refactor: PreviewPane, FoldablePane, and DeferredMarkdownPreview
// moved out of workspace.jsx (was ~671 lines deep inside the 19k-line monolith).
//
// Load order: this file is included by index.html BEFORE workspace.jsx, so
// at module-eval time none of the workspace-scope helpers exist yet. We
// therefore use **lambda forward-refs** — each `const X = (...a) => window.X(...a)`
// captures the *name*, not the value; the actual `window.X` lookup happens
// at call time, after workspace.jsx has run and registered the deps via
// `window.X = X;` assignments. The three components register themselves on
// window at the bottom; workspace.jsx aliases them back via
// `const PreviewPane = window.PreviewPane;` for the existing render sites.
//
// Transitional: still bridges to `window.*` at the bottom so not-yet-migrated
// .jsx files keep resolving `window.PreviewPane` / `window.FoldablePane` /
// `window.DeferredMarkdownPreview`.
import { Fragment, useState, useEffect, useRef, useCallback, useMemo } from 'react';
import type { ReactNode, MouseEvent } from 'react';
import { LintDiagnosticLineAnnotation, lintDiagnosticLine } from './lint-diagnostics';
import type { LintDiagnostic } from './lint-diagnostics';
import { appendActiveSessionParam } from './workspace-session-routing';

// ── Cross-file globals owned by OTHER (unmigrated) files. These are NOT
// declared in types/atlas-window.d.ts yet, so we read them through a locally
// typed view of `window`. Keep them as window.* refs (do NOT import) — their
// owners may be unmigrated. Behavior is identical to the legacy lambdas.

// Fold-range: server returns a flat list of {kind, label, line_start, line_end}.
interface FoldRange {
  kind: string;
  label?: string;
  line_start: number;
  line_end: number;
}
// Nested fold tree node (built by _buildFoldTree). The root node has no real
// kind/label and a sentinel [0, 1e9] range.
interface FoldNode {
  kind?: string;
  label?: string;
  line_start: number;
  line_end: number;
  children: FoldNode[];
}
// Async resource returned by useAtlasAsyncResource('file', path).
interface AtlasFileResource {
  body?: string;
  size?: number;
  truncated?: boolean;
  err?: string;
  loading?: boolean;
  mtime?: number;
}
// File-tree meta returned by atlasFileTreeMetaForPath.
interface AtlasFileMeta {
  size?: number;
  mtime?: number;
}
// Minimal Prism surface used here.
interface PrismLanguages {
  [lang: string]: unknown;
}
interface PrismLike {
  languages?: PrismLanguages;
  highlight: (text: string, grammar: unknown, language: string) => string;
  plugins?: {
    autoloader?: {
      loadLanguages?: (lang: string, cb: () => void) => void;
    };
  };
}

interface AtlasWindowGlobals {
  // Forward-ref helper deps (resolved at call time, after workspace.jsx runs).
  _buildFoldTree: (ranges: FoldRange[]) => FoldNode;
  _copyToClipboard: (value: unknown) => boolean;
  _escHtml: (...a: unknown[]) => string;
  _highlightYamlLine: (...a: unknown[]) => string;
  _markdownHtml: (...a: unknown[]) => string;
  _normalizeMarkdownImageSrc: (...a: unknown[]) => string;
  _postProcessMarkdownNode: (...a: unknown[]) => void;
  atlasFileTreeMetaForPath: (...a: unknown[]) => AtlasFileMeta;
  atlasFormatBytes: (...a: unknown[]) => string;
  atlasImageMimeForExt: (...a: unknown[]) => string;
  scheduleAtlasPreviewWork: (work: () => void) => (() => void) | void;
  useAtlasAsyncResource: (
    kind: string,
    path: string,
  ) => [AtlasFileResource, (force?: boolean) => void];
  // Cross-file components / data used directly (no lambda in legacy header —
  // they resolved as cross-script globals under in-browser babel).
  AtlasStatusBadge: (...a: any[]) => any;
  DocxFallbackPane: (...a: any[]) => any;
  _FOLD_KIND_COLOR: Record<string, string>;
  PRISM_LANG_MAP?: Record<string, string>;
  Prism?: PrismLike;
  // This file's OWN public globals (set via the transitional bridge below).
  DeferredMarkdownPreview: (props: DeferredMarkdownPreviewProps) => ReactNode;
  FoldablePane: (props: FoldablePaneProps) => ReactNode;
  PreviewPane: (props: PreviewPaneProps) => ReactNode;
}

const g = window as unknown as AtlasWindowGlobals;

// Forward-ref to workspace.jsx helpers (resolved at call time):
const _buildFoldTree = (ranges: FoldRange[]): FoldNode => g._buildFoldTree(ranges);
const _copyToClipboard = (value: unknown): boolean => g._copyToClipboard(value);
const _escHtml = (...a: unknown[]): string => g._escHtml(...a);
const _highlightYamlLine = (...a: unknown[]): string => g._highlightYamlLine(...a);
const _markdownHtml = (...a: unknown[]): string => g._markdownHtml(...a);
const _normalizeMarkdownImageSrc = (...a: unknown[]): string => g._normalizeMarkdownImageSrc(...a);
const _postProcessMarkdownNode = (...a: unknown[]): void => g._postProcessMarkdownNode(...a);
const atlasFileTreeMetaForPath = (...a: unknown[]): AtlasFileMeta => g.atlasFileTreeMetaForPath(...a);
const atlasFormatBytes = (...a: unknown[]): string => g.atlasFormatBytes(...a);
const atlasImageMimeForExt = (...a: unknown[]): string => g.atlasImageMimeForExt(...a);
const scheduleAtlasPreviewWork = (work: () => void): (() => void) | void => g.scheduleAtlasPreviewWork(work);
const useAtlasAsyncResource = (
  kind: string,
  path: string,
): [AtlasFileResource, (force?: boolean) => void] => g.useAtlasAsyncResource(kind, path);
// AtlasStatusBadge + DocxFallbackPane were resolved as bare cross-script
// globals in the legacy IIFE; route them through window forward-refs so they
// still resolve at render time after workspace.jsx registers them.
const AtlasStatusBadge = (...a: any[]): any => g.AtlasStatusBadge(...a);
const DocxFallbackPane = (...a: any[]): any => g.DocxFallbackPane(...a);

const atlasApiUrl = (
  endpoint: string,
  params: Record<string, unknown>,
  hash = '',
): string => {
  const qs = appendActiveSessionParam(new URLSearchParams());
  Object.entries(params).forEach(([key, value]) => {
    if (value != null && String(value) !== '') qs.set(key, String(value));
  });
  return `${endpoint}?${qs.toString()}${hash}`;
};

const atlasFileRawUrl = (
  path: string,
  params: Record<string, unknown> = {},
  hash = '',
): string => atlasApiUrl('/api/file/raw', { path, ...params }, hash);

interface DeferredMarkdownPreviewProps {
  body?: string;
  sourcePath?: string;
}

const MARKDOWN_PREVIEW_IFRAME_CSS = `
  :root {
    color-scheme: dark;
    --doc-bg: #070b10;
    --doc-panel: #070b10;
    --doc-panel-2: #0b1118;
    --doc-panel-3: #0d141c;
    --doc-line: #263240;
    --doc-fg: #d7e2ee;
    --doc-muted: #94a3b8;
    --doc-accent: #80d8ff;
    --doc-warn: #ffd166;
    --doc-ok: #7ee2b8;
    --doc-code-font: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    --doc-body-font: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  html[data-theme="light"] {
    color-scheme: light;
    --doc-bg: #f6f8fb;
    --doc-panel: #ffffff;
    --doc-panel-2: #f3f6fb;
    --doc-panel-3: #eef3f8;
    --doc-line: #d6dee8;
    --doc-fg: #17202b;
    --doc-muted: #64748b;
    --doc-accent: #0b6ea8;
    --doc-warn: #8a5a00;
    --doc-ok: #087f5b;
  }
  * { box-sizing: border-box; }
  html, body { min-height: 100%; }
  body {
    margin: 0;
    background: var(--doc-bg);
    color: var(--doc-fg);
    font-family: var(--doc-body-font);
    font-size: 14px;
    line-height: 1.68;
  }
  .md-preview {
    max-width: 980px;
    min-height: 100vh;
    margin: 0 auto;
    padding: 32px 44px 64px;
    background: var(--doc-panel);
  }
  .md-preview > :first-child { margin-top: 0; }
  .md-preview > :last-child { margin-bottom: 0; }
  .md-preview p,
  .md-preview li,
  .md-preview td { color: var(--doc-fg); }
  .md-preview p,
  .md-preview ul,
  .md-preview ol,
  .md-preview blockquote { margin: 0 0 1rem; }
  .md-preview h1,
  .md-preview h2,
  .md-preview h3,
  .md-preview h4 {
    color: var(--doc-fg);
    line-height: 1.25;
    letter-spacing: 0;
  }
  .md-preview h1 {
    margin: 0 0 1rem;
    padding-bottom: .65rem;
    border-bottom: 1px solid var(--doc-line);
    font-size: 2rem;
    font-weight: 800;
  }
  .md-preview h2 {
    margin: 2rem 0 .85rem;
    padding-bottom: .35rem;
    border-bottom: 1px solid var(--doc-line);
    font-size: 1.38rem;
    font-weight: 760;
  }
  .md-preview h3 {
    margin: 1.55rem 0 .65rem;
    font-size: 1.08rem;
    font-weight: 740;
    color: var(--doc-accent);
  }
  .md-preview h4 {
    margin: 1.25rem 0 .45rem;
    font-size: .96rem;
    font-weight: 720;
  }
  .md-preview a { color: var(--doc-accent); text-decoration: none; }
  .md-preview a:hover { text-decoration: underline; }
  .md-preview ul,
  .md-preview ol { padding-left: 1.45rem; }
  .md-preview li { margin: .22rem 0; padding-left: .12rem; }
  .md-preview code {
    padding: .12rem .34rem;
    border: 1px solid var(--doc-line);
    border-radius: 4px;
    background: var(--doc-panel-2);
    color: var(--doc-fg);
    font-family: var(--doc-code-font);
    font-size: .9em;
  }
  .md-preview pre {
    margin: 1rem 0 1.15rem;
    padding: 1rem 1.05rem;
    overflow: auto;
    border: 1px solid var(--doc-line);
    border-radius: 6px;
    background: #05080c;
  }
  html[data-theme="light"] .md-preview pre { background: #f6f8fb; }
  .md-preview pre code {
    padding: 0;
    border: 0;
    background: transparent;
    color: inherit;
    font-size: .9rem;
    line-height: 1.58;
  }
  .md-preview table {
    width: 100%;
    margin: 1rem 0 1.2rem;
    border-collapse: collapse;
    border: 1px solid var(--doc-line);
    border-radius: 6px;
    overflow: hidden;
    background: var(--doc-panel);
  }
  .md-preview th,
  .md-preview td {
    padding: .55rem .68rem;
    border: 1px solid var(--doc-line);
    vertical-align: top;
  }
  .md-preview th {
    background: var(--doc-panel-3);
    color: var(--doc-fg);
    font-weight: 750;
  }
  .md-preview blockquote {
    padding: .8rem 1rem;
    border-left: 3px solid var(--doc-accent);
    border-radius: 0 6px 6px 0;
    background: var(--doc-panel-3);
    color: var(--doc-muted);
  }
  .md-preview hr {
    margin: 1.8rem 0;
    border: 0;
    border-top: 1px solid var(--doc-line);
  }
  .md-preview img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 1rem auto;
    border: 1px solid var(--doc-line);
    border-radius: 6px;
    background: #05080c;
  }
  html[data-theme="light"] .md-preview img { background: #ffffff; }
  .md-preview input[type="checkbox"] { transform: translateY(1px); margin-right: .42rem; }
  .atlas-mermaid-block {
    margin: 1rem 0 1.2rem;
    padding: 1rem;
    border: 1px solid var(--doc-line);
    border-radius: 6px;
    background: var(--doc-panel-2);
    overflow: auto;
  }
  @media (max-width: 720px) {
    .md-preview { padding: 22px 20px 48px; }
    .md-preview h1 { font-size: 1.6rem; }
  }
`;

const markdownPreviewTheme = (): string => {
  if (typeof document === 'undefined') return 'dark';
  const attr = document.documentElement.getAttribute('data-theme') || '';
  return attr === 'light' ? 'light' : 'dark';
};

const DeferredMarkdownPreview = ({ body, sourcePath = '' }: DeferredMarkdownPreviewProps): ReactNode => {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const [html, setHtml] = useState('');
  const [theme, setTheme] = useState(markdownPreviewTheme);
  const text = String(body || '');

  useEffect(() => {
    if (typeof document === 'undefined') return undefined;
    const sync = () => setTheme(markdownPreviewTheme());
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    setHtml('');
    if (!text.trim()) return undefined;
    let cancelled = false;
    const cancel = scheduleAtlasPreviewWork(() => {
      const next = _markdownHtml(text);
      if (!cancelled) setHtml(next);
    });
    return () => {
      cancelled = true;
      if (cancel) cancel();
    };
  }, [text]);

  const postProcessFrame = useCallback(() => {
    const doc = frameRef.current?.contentDocument;
    const root = doc?.querySelector('.md-preview') as HTMLElement | null;
    if (!html || !doc || !root) return;
    _postProcessMarkdownNode(root);
    // Rewrite <img src="relative/path.png"> → /api/file/raw?path=<resolved>
    // so embedded images from SSOT imports actually render in the preview
    // pane (the raw src is a project-relative path the browser cannot
    // fetch directly).
    const baseDir = sourcePath ? sourcePath.replace(/\/[^/]*$/, '') : '';
    root.querySelectorAll('a[href]').forEach(link => {
      if (!link.getAttribute('target')) link.setAttribute('target', '_blank');
      if (!link.getAttribute('rel')) link.setAttribute('rel', 'noopener noreferrer');
    });
    root.querySelectorAll('img[src]').forEach(img => {
      const rawSrc = img.getAttribute('src') || '';
      const src = _normalizeMarkdownImageSrc(rawSrc);
      if (src && src !== rawSrc) img.setAttribute('src', src);
      (img as HTMLImageElement).style.maxWidth = '100%';
      // Imported datasheets embed dozens of figures; without lazy loading the
      // browser fires every /api/file/raw request at once and the preview
      // stalls. Defer offscreen images and decode async so scroll stays smooth.
      if (!img.getAttribute('loading')) img.setAttribute('loading', 'lazy');
      if (!img.getAttribute('decoding')) img.setAttribute('decoding', 'async');
      if (!sourcePath || !src || /^(https?:|data:|blob:|\/api\/)/i.test(src)) return;
      const rel = src.replace(/^\.\//, '');
      const resolved = rel.startsWith('/') ? rel.slice(1)
        : (baseDir ? `${baseDir}/${rel}` : rel);
      img.setAttribute('src', atlasFileRawUrl(resolved));
    });
  }, [html, sourcePath]);

  const srcDoc = useMemo(() => {
    if (!html) return '';
    const frameTheme = theme === 'light' ? 'light' : 'dark';
    return `<!doctype html>
<html data-theme="${frameTheme}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <base target="_blank" />
  <style>${MARKDOWN_PREVIEW_IFRAME_CSS}</style>
</head>
<body>
  <main class="md-agent md-preview">${html}</main>
</body>
</html>`;
  }, [html, theme]);

  if (!text.trim()) return <div className="md-preview-empty">empty markdown file</div>;
  if (!html) {
    return (
      <pre className="tool-output-pre language-none" style={{
        margin: 0,
        border: 0,
        borderRadius: 0,
        maxHeight: 'none',
        overflow: 'visible',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        <code className="language-none">{text}</code>
      </pre>
    );
  }
  return (
    <iframe
      ref={frameRef}
      className="md-preview-frame"
      title={sourcePath ? `Markdown preview: ${sourcePath}` : 'Markdown preview'}
      sandbox="allow-same-origin allow-popups"
      referrerPolicy="no-referrer"
      srcDoc={srcDoc}
      onLoad={postProcessFrame}
      style={{ width: '100%', height: '100%', minHeight: '100%', border: 0, display: 'block', background: theme === 'light' ? '#f6f8fb' : '#070b10' }}
    />
  );
};

// Fold-range tree builder. Server returns a flat list of
// {kind, label, line_start, line_end}; nest them so an outer range

interface FoldSelection {
  lo: number;
  hi: number;
}
interface FloatingComment {
  top: number;
  lo: number;
  hi: number;
}
interface DragState {
  start: number | null;
  end: number | null;
  on: boolean;
}

interface FoldablePaneProps {
  path?: string;
  body: string;
  lang?: string;
  lineCount: number;
  focusLine?: number;
  feedbackMode?: boolean;
  lintDiagnostic?: LintDiagnostic | null;
}

const FoldablePane = ({ path, body, lang, lineCount, focusLine = 0, feedbackMode = false, lintDiagnostic = null }: FoldablePaneProps): ReactNode => {
  const [ranges, setRanges] = useState<FoldRange[]>([]);
  const [skipped, setSkipped] = useState<string | null>(null);
  const [floating, setFloating] = useState<FloatingComment | null>(null);  // {top, left, lo, hi}
  const [sel, setSel] = useState<FoldSelection | null>(null);            // {lo, hi}
  const dragRef = useRef<DragState>({ start: null, end: null, on: false });
  const paneRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (feedbackMode) return;
    dragRef.current = { start: null, end: null, on: false };
    setSel(null);
    setFloating(null);
  }, [feedbackMode]);

  // Fetch fold ranges per (path, body-length) — body-length acts as a
  // cheap content-changed signal so reloaded files refetch.
  useEffect(() => {
    if (!path) { setRanges([]); setSkipped(null); return; }
    let cancelled = false;
    fetch(atlasApiUrl('/api/fold-symbols', { path }), { cache: 'no-store', credentials: 'include' })
      .then(r => r.json())
      .then(d => {
        if (cancelled) return;
        if (d && d.skipped) { setRanges([]); setSkipped(d.reason || 'skipped'); return; }
        setRanges(Array.isArray(d?.ranges) ? d.ranges : []);
        setSkipped(null);
      })
      .catch(() => { if (!cancelled) { setRanges([]); setSkipped(null); } });
    return () => { cancelled = true; };
  }, [path, body.length]);

  // Drag-select handlers wired on the line-number gutter.
  const onLineMouseDown = (ln: number, ev: MouseEvent) => {
    if (!feedbackMode) return;
    ev.preventDefault();
    dragRef.current = { start: ln, end: ln, on: true };
    setSel({ lo: ln, hi: ln });
    setFloating(null);
  };
  const onLineMouseEnter = (ln: number) => {
    if (!feedbackMode || !dragRef.current.on) return;
    dragRef.current.end = ln;
    const a = dragRef.current.start, b = ln;
    setSel({ lo: Math.min(a as number, b), hi: Math.max(a as number, b) });
  };
  useEffect(() => {
    const onUp = () => {
      if (!dragRef.current.on) return;
      dragRef.current.on = false;
      const { start, end } = dragRef.current;
      if (start == null || end == null) return;
      const hi = Math.max(start, end);
      const lo = Math.min(start, end);
      // Anchor next to the LAST selected line. We use offsetTop /
      // offsetLeft because ATLAS wraps the whole UI in a CSS
      // transform-scaled #scaler — getBoundingClientRect returns
      // scaled pixels while scrollTop returns unscaled, so mixing
      // them shifted the button off-screen. offset* are unscaled
      // relative to the nearest positioned ancestor (.foldable-body
      // is position:relative), so they line up correctly.
      const pane = paneRef.current;
      if (!pane) return;
      // Prefer the .line-row (outer) over the .lineno span so we
      // measure the row's full vertical extent.
      const lineEl = (pane.querySelector(`.line-row[data-ln="${hi}"]`)
                  || pane.querySelector(`[data-ln="${hi}"]`)) as HTMLElement | null;
      if (!lineEl) return;
      // Anchor BELOW the last-selected line, pinned to the pane's
      // RIGHT edge. Button is a child of .foldable-pane (NOT
      // .foldable-body) so its `right: 16` lands on the visible
      // right edge even when the body has horizontal-scroll wider
      // than the pane. We accumulate offsetTop up the chain until
      // we hit .foldable-pane itself.
      let top = lineEl.offsetTop + lineEl.offsetHeight;
      let p = lineEl.offsetParent as HTMLElement | null;
      while (p && p !== pane) {
        top += p.offsetTop;
        p = p.offsetParent as HTMLElement | null;
      }
      setFloating({ top, lo, hi });
    };
    window.addEventListener('mouseup', onUp);
    return () => window.removeEventListener('mouseup', onUp);
  }, []);

  useEffect(() => {
    const line = Number(focusLine || 0);
    if (!line || !paneRef.current) return undefined;
    setSel({ lo: line, hi: line });
    const timer = window.setTimeout(() => {
      const pane = paneRef.current;
      const row = pane?.querySelector(`.line-row[data-ln="${line}"]`)
              || pane?.querySelector(`[data-ln="${line}"]`);
      if (row && row.scrollIntoView) {
        row.scrollIntoView({ block: 'center', inline: 'nearest' });
      }
    }, 80);
    return () => window.clearTimeout(timer);
  }, [path, body.length, focusLine]);

  const dispatchComment = (lo: number, hi: number, label: string) => {
    if (!feedbackMode) return;
    // Slice the source lines for the selection so the chat prefill
    // carries the actual file content, not just a path/range header.
    // The listener wraps it in a fenced code block so the agent sees
    // it verbatim instead of having to re-read the file.
    const sliceText = (srcLines || []).slice(lo - 1, hi).join('\n');
    window.dispatchEvent(new CustomEvent('atlas-fold-comment', {
      detail: {
        path,
        lineStart: lo,
        lineEnd: hi,
        label: label || '',
        text: sliceText,
        lang: lang || '',
      },
    }));
    setFloating(null);
  };

  // Highlight a single line of source via Prism (only when language is
  // known and Prism has the grammar).
  const highlightLine = useCallback((line: string): string => {
    if (!line || !line.trim()) return line || ' ';
    if (lang === 'yaml' || lang === 'yml') return _highlightYamlLine(line);
    const Prism = g.Prism;
    if (!Prism || !lang || lang === 'none' ||
        !Prism.languages || !Prism.languages[lang]) {
      return line;
    }
    try { return Prism.highlight(line, Prism.languages[lang], lang); }
    catch (_) { return line; }
  }, [lang]);

  // Strip Verilator coverage annotation markers (`%FFFFFF`, `%000000`,
  // ...) that some toolflows insert at the start of each line. These
  // are only meaningful inside the coverage workflow's dedicated
  // viewer; in the regular PreviewPane they look like noise. Pattern
  // is anchored at the line start so identifier `%foo` mid-line
  // is not affected.
  const srcLines = useMemo(
    () => body.split('\n').map(line => line.replace(/^%[0-9A-Fa-f]{4,}\s?/, '')),
    [body],
  );
  // Languages where `#` introduces a whole-line comment (markdown uses `#`
  // for headings — keep those visible). When matched, whole-line `#` rows
  // are skipped at render time so the preview shows actual data only;
  // line numbers gap rather than renumber so jump-to-line stays accurate.
  const isHashCommentLang = ['yaml', 'yml', 'python', 'py', 'bash', 'sh',
    'shell', 'makefile', 'mk', 'toml', 'ini', 'conf', 'ruby', 'perl', 'tcl', 'r']
    .includes(String(lang).toLowerCase());
  const isCommentLine = (text: string): boolean => isHashCommentLang && /^\s*#/.test(text);
  const tree = useMemo(() => _buildFoldTree(ranges), [ranges]);
  const annotationLine = lintDiagnosticLine(lintDiagnostic);

  // Render the source as nested <details> + line-rows. Fold controls are
  // deliberately separate rows above the source range: the original YAML/RTL
  // line always remains in the body, so the preview stays faithful to the file.
  const renderLineRow = (ln: number): ReactNode => {
    const text = srcLines[ln - 1] != null ? srcLines[ln - 1] : '';
    if (isCommentLine(text)) return null;
    const html = highlightLine(text);
    const inSel = sel && ln >= sel.lo && ln <= sel.hi;
    return (
      <Fragment key={`L${ln}`}>
        <div className={'line-row' + (inSel ? ' sel' : '')} data-ln={ln}>
          <span className="lineno"
                data-ln={ln}
                onMouseDown={(ev) => onLineMouseDown(ln, ev)}
                onMouseEnter={() => onLineMouseEnter(ln)}>
            {ln}
          </span>
          <span className="line"
                dangerouslySetInnerHTML={{ __html: html === text ? _escHtml(text) || ' ' : html }} />
        </div>
        {lintDiagnostic && annotationLine === ln && (
          <div className="line-row lint-diagnostic-row" data-ln={`${ln}-lint`}>
            <span className="lineno" />
            <span className="line" style={{ whiteSpace: 'normal', overflowWrap: 'anywhere' }}>
              <LintDiagnosticLineAnnotation diagnostic={lintDiagnostic} />
            </span>
          </div>
        )}
      </Fragment>
    );
  };

  const renderFoldSummary = (c: FoldNode, color: string, depth: number): ReactNode => {
    const inSel = sel && c.line_start <= sel.hi && c.line_end >= sel.lo;
    return (
      <summary
        className={'fold-summary fold-control-summary' + (inSel ? ' sel' : '')}
        style={{ borderLeftColor: color, color, paddingLeft: `calc(${depth * 1.5}ch + 8px)` }}
      >
        <span className="fold-label" title={c.label}>
          {c.label || c.kind}
        </span>
        <span className="fold-range mute" title={c.label}>
          {c.kind} L{c.line_start}-L{c.line_end}
        </span>
        {feedbackMode ? (
          <button className="fold-comment-btn"
                  onClick={(ev) => { ev.preventDefault(); ev.stopPropagation();
                                     dispatchComment(c.line_start, c.line_end, c.label || ''); }}>
            💬 comment
          </button>
        ) : null}
      </summary>
    );
  };

  const renderTree = (node: FoldNode, cursor: number, depth: number): { elements: ReactNode[]; cursor: number } => {
    const out: ReactNode[] = [];
    const children = node.children.slice().sort((a, b) => a.line_start - b.line_start);
    for (const c of children) {
      while (cursor < c.line_start) { out.push(renderLineRow(cursor)); cursor += 1; }
      const color = (g._FOLD_KIND_COLOR || {})[c.kind as string] || 'var(--fg-mute)';
      const opened = true;
      const inner: ReactNode[] = [];
      // Keep the original start line in the body. The summary above is
      // only a fold affordance, never a replacement for source text.
      inner.push(renderLineRow(c.line_start));
      cursor = c.line_start + 1;
      const sub = renderTree(c, cursor, depth + 1);
      inner.push(...sub.elements);
      cursor = sub.cursor;
      while (cursor <= c.line_end) { inner.push(renderLineRow(cursor)); cursor += 1; }
      out.push(
        <details key={`F${c.line_start}-${c.line_end}`} {...(opened ? { open: true } : {})}
                 data-kind={c.kind}>
          {renderFoldSummary(c, color, depth)}
          {inner}
        </details>
      );
    }
    return { elements: out, cursor };
  };

  const renderedTree = renderTree(tree, 1, 0);
  const trail: ReactNode[] = [];
  let cur = renderedTree.cursor;
  while (cur <= lineCount) { trail.push(renderLineRow(cur)); cur += 1; }

  return (
    <div className={`foldable-pane ${lang === 'yaml' || lang === 'yml' ? 'yaml-pane' : ''}`} ref={paneRef}>
      {skipped && (
        <div style={{ padding: '6px 14px', color: 'var(--warn)', fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)' }}>
          fold disabled — {skipped}
        </div>
      )}
      {ranges.length > 1 && (
        <div className="foldable-toolbar">
          <button onClick={() => paneRef.current?.querySelectorAll('details').forEach(d => d.open = true)}>▾ Expand all</button>
          <button onClick={() => paneRef.current?.querySelectorAll('details').forEach(d => d.open = false)}>▸ Collapse all</button>
          <button onClick={() => {
            paneRef.current?.querySelectorAll('details').forEach(d => { d.open = (d.dataset.kind === 'section' || d.dataset.kind === 'module'); });
          }}>▾ Top sections only</button>
        </div>
      )}
      <div className="foldable-body">
        {renderedTree.elements}
        {trail}
      </div>
      {feedbackMode && floating && (
        <button className="fold-floating-comment"
                style={{ position: 'absolute', left: 4, top: floating.top + 4 }}
                onClick={() => dispatchComment(floating.lo, floating.hi, '')}>
          💬 Comment L{floating.lo}-L{floating.hi}
        </button>
      )}
    </div>
  );
};

interface ImageMeta {
  width: number;
  height: number;
  error: string;
}

interface PreviewPaneProps {
  path?: string;
  onClose?: () => void;
  focusLine?: number;
  lintDiagnostic?: LintDiagnostic | null;
}

const PreviewPane = ({ path, onClose, focusLine = 0, lintDiagnostic = null }: PreviewPaneProps): ReactNode => {
  const ext = (path ? (path.split('.').pop() || '') : '').toLowerCase();
  const lang = (g.PRISM_LANG_MAP && g.PRISM_LANG_MAP[ext]) || 'none';
  const isMarkdown = ['md', 'markdown', 'mdown', 'mkdn'].includes(ext);
  // .mmd / .mermaid are raw Mermaid (no code fence). Render them as diagrams by
  // wrapping the body in a ```mermaid fence and reusing the markdown pipeline
  // (_markdownHtml -> _postProcessMarkdownNode -> _renderMermaidBlocks).
  const isMermaid = ['mmd', 'mermaid'].includes(ext);
  const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'tif', 'tiff', 'ico'].includes(ext);
  const isPdf = ext === 'pdf';
  const isHtml = ['html', 'htm'].includes(ext);
  const isDocxLike = ['docx', 'pptx', 'xlsx'].includes(ext);
  // isHtml is intentionally NOT binary: keep fetching the text body so the
  // "source" toggle works; the rendered branch loads it in an iframe via
  // /api/file/raw (served as text/html) and ignores the fetched body.
  const isBinary = isImage || isPdf || isDocxLike;
  const hasGlobPath = !!path && /[*?[\]{}]/.test(path);
  // For binary files (images, pdf, docx) skip the text /api/file fetch —
  // the body would just be garbled mojibake. The render branch below uses
  // /api/file/raw directly.
  const [resource, reloadPreview] = useAtlasAsyncResource('file', (hasGlobPath || isBinary) ? '' : (path || ''));

  // Auto-reload when the backend emits file_changed for THIS path.
  useEffect(() => {
    if (!path || hasGlobPath) return undefined;
    const handler = (ev: Event) => {
      const detail = (ev as CustomEvent).detail;
      const changed = (detail && detail.path) || '';
      if (!changed) return;
      // Match by suffix so both relative ("rtl/foo.sv") and absolute
      // ("/full/path/to/rtl/foo.sv") emissions hit when the open
      // preview's path is one or the other.
      if (changed === path || changed.endsWith('/' + path) || path.endsWith('/' + changed)) {
        reloadPreview(true);
      }
    };
    window.addEventListener('atlas-file-changed', handler);
    return () => window.removeEventListener('atlas-file-changed', handler);
  }, [path, hasGlobPath, reloadPreview]);
  const body = hasGlobPath
    ? `// ${path}\n// Preview needs one concrete file path, not a glob pattern.\n// Select an exact file from the tree, for example rtl/<module>.sv.`
    : (resource.body || '');
  const size = hasGlobPath ? 0 : (resource.size || 0);
  const truncated = !hasGlobPath && !!resource.truncated;
  const err = hasGlobPath
    ? 'Preview needs one concrete file path; glob patterns are not previewable.'
    : resource.err;
  const loading = !hasGlobPath && !!resource.loading;
  const hasBody = !!String(body || '').trim();
  const blockingLoading = loading && !hasBody;
  const highlightTooLarge = !isMarkdown && body.length > 60000;
  const canHighlight = !isMarkdown && !highlightTooLarge && lang !== 'none';
  const [highlightedHtml, setHighlightedHtml] = useState('');
  const [previewMode, setPreviewMode] = useState('view');
  const [htmlRendered, setHtmlRendered] = useState(true);
  const [binaryReloadKey, setBinaryReloadKey] = useState(0);
  const [imageMeta, setImageMeta] = useState<ImageMeta>({ width: 0, height: 0, error: '' });

  useEffect(() => {
    setImageMeta({ width: 0, height: 0, error: '' });
  }, [path]);

  useEffect(() => {
    setHighlightedHtml('');
    if (!body || !canHighlight || !g.Prism) return undefined;
    let cancelled = false;
    const runHighlight = () => {
      const Prism = g.Prism;
      if (!Prism) return;
      const applyHighlight = () => {
        if (cancelled || !Prism.languages || !Prism.languages[lang]) return;
        try {
          const html = Prism.highlight(body, Prism.languages[lang], lang);
          if (!cancelled) setHighlightedHtml(html);
        } catch (_) {}
      };
      if (Prism.languages && Prism.languages[lang]) {
        applyHighlight();
      } else if (Prism.plugins && Prism.plugins.autoloader && Prism.plugins.autoloader.loadLanguages) {
        try { Prism.plugins.autoloader.loadLanguages(lang, applyHighlight); } catch (_) {}
      }
    };
    const cancel = scheduleAtlasPreviewWork(runHighlight);
    return () => {
      cancelled = true;
      if (cancel) cancel();
    };
  }, [body, lang, canHighlight]);

  if (!path) {
    return (
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexDirection: 'column', gap: 12, color: 'var(--fg-mute)', padding: 40,
      }}>
        <div style={{ fontSize: 32, opacity: 0.4 }}>◆</div>
        <div style={{ fontSize: 13 }}>No file selected.</div>
        <div style={{ fontSize: 11 }}>Click any file in the tree on the left to preview it here.</div>
      </div>
    );
  }

  const binaryFileMeta = isBinary ? atlasFileTreeMetaForPath(path) : {};
  const effectiveSize = isBinary ? Number(binaryFileMeta.size || 0) : size;
  const effectiveMtime = isBinary ? Number(binaryFileMeta.mtime || 0) : Number(resource.mtime || 0);
  const lineCount = isBinary ? 0 : body.split('\n').length;
  const sizeLabel = atlasFormatBytes(effectiveSize);
  const imageDimLabel = imageMeta.width && imageMeta.height
    ? `${imageMeta.width} x ${imageMeta.height}px`
    : '';
  const binaryKindLabel = isImage
    ? atlasImageMimeForExt(ext)
    : (isPdf ? 'application/pdf' : `application/${ext || 'octet-stream'}`);
  const refreshPreview = () => {
    if (isBinary) {
      setImageMeta({ width: 0, height: 0, error: '' });
      setBinaryReloadKey(k => k + 1);
      return;
    }
    reloadPreview(true);
  };
  const copyPath = () => { _copyToClipboard(path); };
  const copyAll  = () => { _copyToClipboard(body); };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* meta strip */}
      <div style={{
        padding: '4px 14px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 10, fontSize: 10,
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
      }}>
        {isBinary ? (
          <>
            <span>file <span style={{ color: 'var(--accent)' }}>{binaryKindLabel}</span></span>
            {imageDimLabel && <><span className="mute">·</span><span>{imageDimLabel}</span></>}
            {sizeLabel && <><span className="mute">·</span><span>{sizeLabel}</span></>}
            {imageMeta.error && <><span className="mute">·</span><span className="warn">{imageMeta.error}</span></>}
          </>
        ) : (
          <>
            <span>lang <span style={{ color: 'var(--accent)' }}>{isMarkdown ? 'rendered markdown' : (isHtml && htmlRendered) ? 'rendered html' : (lang === 'none' ? 'plain' : lang)}</span></span>
            <span className="mute">·</span>
            <span>{lineCount} lines</span>
            {sizeLabel && <><span className="mute">·</span><span>{sizeLabel}</span></>}
            {truncated && <><span className="mute">·</span><span className="warn">truncated at {Math.round((body.length || 0) / 1024)}KB</span></>}
            {highlightTooLarge && <><span className="mute">·</span><span className="warn">syntax highlight skipped for speed</span></>}
            {canHighlight && !highlightedHtml && !loading && body && <><span className="mute">·</span><span className="warn">syntax pending</span></>}
            {hasGlobPath && <><span className="mute">·</span><span className="warn">glob path</span></>}
            {loading && <AtlasStatusBadge status={hasBody ? 'refreshing' : 'loading'} compact soft />}
          </>
        )}
        <span style={{ flex: 1 }} />
        <span onClick={refreshPreview} style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>refresh</span>
        {!isBinary && <span onClick={copyAll} style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>copy</span>}
        <span onClick={copyPath} style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>copy path</span>
        {isHtml ? (
          <div style={{ display: 'inline-flex', border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
            {[['rendered', 'Rendered'], ['source', 'Source']].map(([m, label]) => {
              const active = (m === 'rendered') === htmlRendered;
              return (
                <button
                  key={m}
                  type="button"
                  onClick={() => setHtmlRendered(m === 'rendered')}
                  style={{
                    border: 0,
                    borderRight: m === 'rendered' ? '1px solid var(--line)' : 0,
                    background: active ? 'var(--accent)' : 'transparent',
                    color: active ? 'var(--bg)' : 'var(--fg-mute)',
                    fontFamily: 'var(--mono)',
                    fontSize: 10,
                    fontWeight: 800,
                    padding: '1px 6px',
                    cursor: 'pointer',
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        ) : (
          <div style={{ display: 'inline-flex', border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
            {[
              ['view', 'View Mode'],
              ['feedback', 'Feedback Mode'],
            ].map(([mode, label]) => (
              <button
                key={mode}
                type="button"
                onClick={() => setPreviewMode(mode)}
                style={{
                  border: 0,
                  borderRight: mode === 'view' ? '1px solid var(--line)' : 0,
                  background: previewMode === mode ? 'var(--accent)' : 'transparent',
                  color: previewMode === mode ? 'var(--bg)' : 'var(--fg-mute)',
                  fontFamily: 'var(--mono)',
                  fontSize: 10,
                  fontWeight: 800,
                  padding: '1px 6px',
                  cursor: 'pointer',
                }}
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>
      {err && (
        <div style={{
          padding: '6px 14px',
          borderBottom: '1px solid var(--err)',
          background: 'color-mix(in oklch, var(--err) 12%, transparent)',
          color: 'var(--err)',
          fontFamily: 'var(--mono)',
          fontSize: 10,
        }}>
          <AtlasStatusBadge status="error" label="preview error" compact /> <span style={{ marginLeft: 8 }}>{err}</span>
        </div>
      )}
      {/* code body — theme-aware background so light mode stays light.
          Markdown files (.md) get full marked → DOMPurify → md-agent
          rendering instead of raw text + Prism, so the same headings/
          code-fence/table styling used for the agent's chat replies
          applies to README/guide files in the preview tab. */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto', background: (isMarkdown || isMermaid) ? 'var(--bg)' : 'var(--bg-3)' }}>
        {blockingLoading ? (
          <div style={{ padding: 16, color: 'var(--fg-mute)', fontFamily: 'var(--code-font, var(--mono))', fontSize: 12 }}>
            loading {path}…
          </div>
        ) : isImage ? (
          <div style={{
            padding: 16, display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
            background: 'var(--bg-2)',
          }}>
            {imageMeta.error ? (
              <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12 }}>
                Image preview failed. Use copy path or download the original import.
              </div>
            ) : (
              <img
                src={atlasFileRawUrl(path, { v: String(effectiveMtime || binaryReloadKey || '') })}
                alt={path}
                style={{ maxWidth: '100%', maxHeight: '90vh', background: '#fff', border: '1px solid var(--line)', borderRadius: 2 }}
                onLoad={(e) => {
                  setImageMeta({
                    width: e.currentTarget.naturalWidth || 0,
                    height: e.currentTarget.naturalHeight || 0,
                    error: '',
                  });
                }}
                onError={(e) => {
                  setImageMeta(prev => ({ ...prev, error: 'image load failed' }));
                  e.currentTarget.style.display = 'none';
                }}
              />
            )}
          </div>
        ) : isPdf ? (
          <iframe
            src={atlasFileRawUrl(path, {}, '#view=FitH')}
            title={path}
            style={{ width: '100%', height: '100%', border: 0, background: '#fff' }}
          />
        ) : isDocxLike ? (
          <DocxFallbackPane path={path} ext={ext} />
        ) : (isHtml && htmlRendered) ? (
          <iframe
            src={atlasFileRawUrl(path, { v: String(effectiveMtime || '') })}
            title={path}
            style={{ width: '100%', height: '100%', border: 0, background: '#fff' }}
          />
        ) : isMermaid ? (
          <DeferredMarkdownPreview body={'```mermaid\n' + (body || '') + '\n```'} sourcePath={path} />
        ) : isMarkdown ? (
          <DeferredMarkdownPreview body={body} sourcePath={path} />
        ) : hasBody ? (
          /* Foldable view: per-line gutter + nested <details> wraps
             from /api/fold-symbols. Verilog/SV and YAML get an AST
             fold; every other extension still gets the per-line
             gutter so drag-select-comment works universally. The
             server's fold extractor returns [] for unknown types,
             so the fold UI stays out of the way. */
          <FoldablePane path={path} body={body} lang={lang} lineCount={lineCount} focusLine={focusLine} feedbackMode={previewMode === 'feedback'} lintDiagnostic={lintDiagnostic} />
        ) : (
          /* 2-column layout: line numbers (sticky left gutter) +
             code body. Both columns share the SAME font-size and
             line-height so each gutter row aligns with its code
             row, even when the body is Prism-highlighted (the
             highlighted HTML stays a single block — splitting it
             per-line would break partial syntax spans). */
          <div className="code-pane" style={{
            display: 'flex',
            fontFamily: 'var(--code-font, var(--mono))', fontSize: 12, lineHeight: 1.55,
            tabSize: 4,
            background: 'transparent',
          }}>
            <div
              aria-hidden="true"
              style={{
                userSelect: 'none',
                padding: '12px 8px 12px 12px',
                textAlign: 'right',
                color: 'var(--fg-mute)',
                borderRight: '1px solid var(--line)',
                minWidth: `${String(lineCount).length + 1}ch`,
                whiteSpace: 'pre',
                opacity: 0.7,
                position: 'sticky', left: 0,
                background: 'var(--bg-3)',
              }}
            >
              {Array.from({ length: lineCount }, (_, i) => `${i + 1}\n`).join('')}
            </div>
            <pre style={{
              margin: 0, flex: 1,
              padding: '12px 16px',
              fontFamily: 'inherit', fontSize: 'inherit', lineHeight: 'inherit',
              whiteSpace: 'pre',
              background: 'transparent',
              color: 'var(--fg)',
            }}>
              {highlightedHtml ? (
                <code
                  className={canHighlight ? ('language-' + lang) : ''}
                  dangerouslySetInnerHTML={{ __html: highlightedHtml }}
                />
              ) : (
                <code className={canHighlight ? ('language-' + lang) : ''}>{body}</code>
              )}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

// Renders the unified diff for one commit. Fetched from /api/git/show.
// Reuses DiffOutputPre's row format (red/green backgrounds, indented
// line numbers, marker column) so a per-commit diff feels visually

export { DeferredMarkdownPreview, FoldablePane, PreviewPane };

// Phase 13d window exports — workspace.jsx aliases these back.
g.DeferredMarkdownPreview = DeferredMarkdownPreview;
g.FoldablePane = FoldablePane;
g.PreviewPane = PreviewPane;
