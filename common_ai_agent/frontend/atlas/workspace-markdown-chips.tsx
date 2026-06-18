/* workspace-markdown-chips.tsx — Atlas chat Markdown → sanitized-HTML
 * pipeline plus the code-fence renderers it feeds.
 *
 * Slice migrated from workspace.jsx (legacy L717–L1063). This is an INERT
 * mirror: the legacy workspace.jsx still serves the live app. The gate is
 * tsc-clean + vitest-green + public exports intact.
 *
 * Responsibilities:
 *   • _markdownHtml: window.marked → window.DOMPurify sanitize bridge, with a
 *     renderInline fallback when marked is unavailable.
 *   • Accidental-indent dedent + image-src normalization helpers.
 *   • _postProcessMarkdownNode: link-target rewrite, Prism class sanitization +
 *     highlight, inline chip classification, blockquote-kind tagging.
 *   • Inline chip activation dispatches atlas-chip-open / atlas-chip-ip
 *     CustomEvents so the chat feed can pivot preview/IP.
 *   • ToolOutputPre / DiffOutputPre: Prism-highlighted tool-output fences.
 *   • _copyToClipboard / CopyBtn: typed imports from ui-utils (used by the Pre
 *     components and re-exported for sibling slices).
 */
import { useState, useEffect, useRef, type ReactNode } from 'react';
import { CopyBtn as UiCopyBtn, copyToClipboard as uiCopyToClipboard } from './ui-utils';

// ── Cross-module window globals owned by sibling slices ────────────────
// renderInline / _escHtml are owned by workspace-feed-cards.tsx and
// _unwrapAtlasOutputFence by workspace-report-status.tsx. Those siblings
// import FROM this file, so importing them back would create a cycle — we
// read them off window (legacy publishes _escHtml; the others are read with
// graceful fallbacks). marked / DOMPurify / Prism / PRISM_LANG_MAP /
// _copyToClipboard / CopyBtn are provided by ui-utils; legacy window bridge
// remains there for not-yet-migrated callers.
interface MarkdownChipWindowGlobals {
  renderInline?: (s: string) => string;
  _unwrapAtlasOutputFence?: (text: unknown) => string;
  _escHtml?: (s: unknown) => string;
  atlasResolveOpenablePath?: (path: unknown) => string;
}
const _mdWin = window as unknown as Window & MarkdownChipWindowGlobals;

const _renderInline = (s: string): string => {
  if (typeof _mdWin.renderInline === 'function') return _mdWin.renderInline(s);
  return _escapeHtml(s);
};

const _unwrapAtlasOutputFenceSafe = (text: unknown): string => {
  if (typeof _mdWin._unwrapAtlasOutputFence === 'function') {
    return _mdWin._unwrapAtlasOutputFence(text);
  }
  return String(text || '');
};

const _escapeHtml = (s: unknown): string => {
  if (typeof _mdWin._escHtml === 'function') return _mdWin._escHtml(s);
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
};

export const _INDENTED_MD_RE = /^(#{1,6}\s|\|.*\|\s*$|[-*+]\s+|\d+\.\s+)/;
export const _CODELIKE_MD_RE = /^(def |class |if |elif |else:|for |while |try:|except |with |return\b|import |from |module\b|endmodule\b|assign\b|always\b|wire\b|reg\b|logic\b|localparam\b|parameter\b|#include\b|[{};])/;

export const _dedentAccidentalMarkdownBlocks = (text: unknown): string => {
  const raw = String(text || '');
  if (!/(^|\n)(?:    |\t)/.test(raw)) return raw;

  const lines = raw.split('\n');
  const out: string[] = [];
  let inFence = false;
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (line.trim().startsWith('```')) {
      inFence = !inFence;
      out.push(line);
      i += 1;
      continue;
    }
    if (inFence || !(line.startsWith('    ') || line.startsWith('\t'))) {
      out.push(line);
      i += 1;
      continue;
    }

    const block: string[] = [];
    let j = i;
    while (j < lines.length) {
      const cur = lines[j];
      if (cur.trim().startsWith('```')) break;
      if (cur.trim() && !(cur.startsWith('    ') || cur.startsWith('\t'))) break;
      block.push(cur);
      j += 1;
    }

    const nonblank = block.filter((ln) => ln.trim());
    const stripped = nonblank.map((ln) => ln.replace(/^[ \t]+/, ''));
    const hasMarkdown = stripped.some((ln) => _INDENTED_MD_RE.test(ln));
    const hasCode = stripped.some((ln) => _CODELIKE_MD_RE.test(ln));
    if (hasMarkdown && !hasCode) {
      const indents = nonblank
        .filter((ln) => ln.startsWith(' '))
        .map((ln) => ln.length - ln.replace(/^ +/, '').length);
      const remove = indents.length ? Math.min(...indents) : 1;
      block.forEach((ln) => {
        if (ln.startsWith(' '.repeat(remove))) out.push(ln.slice(remove));
        else if (ln.startsWith('\t')) out.push(ln.slice(1));
        else out.push(ln);
      });
    } else {
      out.push(...block);
    }
    i = j;
  }
  return out.join('\n');
};

export const _markdownHtml = (text: unknown): string => {
  const body = _dedentAccidentalMarkdownBlocks(_unwrapAtlasOutputFenceSafe(text));
  const rawHtml = (typeof window.marked !== 'undefined' && window.marked.parse)
    ? window.marked.parse(body || '', { breaks: true, gfm: true })
    : _renderInline(body || '');
  return (typeof window.DOMPurify !== 'undefined' && window.DOMPurify.sanitize)
    ? window.DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ['target', 'rel'],
      ADD_DATA_URI_TAGS: ['img'],
    })
    : rawHtml;
};

export const _normalizeMarkdownImageSrc = (src: unknown): string => {
  const value = String(src || '').trim();
  if (!value) return '';
  return value
    .replace(/^data:(image\/[a-z0-9.+-]+)\s*:\s*base64\s*,/i, 'data:$1;base64,')
    .replace(/^data:(image\/[a-z0-9.+-]+)\s*;\s*base64\s*,/i, 'data:$1;base64,');
};

export const _sanitizePrismLanguageClasses = (node: any): void => {
  if (!node) return;
  node.querySelectorAll('pre > code').forEach((c: any) => {
    const classes = Array.from(c.classList || []) as string[];
    const langClasses = classes.filter((cls) => /^language-/i.test(cls));
    if (!langClasses.length) {
      c.classList.add('language-none');
      return;
    }
    langClasses.forEach((cls) => {
      const lang = cls.replace(/^language-/i, '').trim();
      if (!/^[a-z0-9_-]{1,40}$/i.test(lang) || /^data[:;]/i.test(lang)) {
        c.classList.remove(cls);
      }
    });
    if (!(Array.from(c.classList || []) as string[]).some((cls) => /^language-/i.test(cls))) {
      c.classList.add('language-none');
    }
  });
};

// Inline-code chip classification + interactivity. Inline `<code>`
// elements ( markdown backticks ) are classified into a few token types
// so CSS can style them differently, and path-like / IP-like chips
// become clickable so the user can pivot the preview pane or active IP
// straight from the chat feed.
export const _CHIP_PATH_RE = /^(?:[A-Za-z]:\/)?[A-Za-z0-9_./-]+\.(?:sv|v|svh|vh|vlt|sdc|tcl|md|yaml|yml|json|jsonl|txt|log|py|sh|c|cc|cpp|h|hpp|f)$/i;
export const _CHIP_DIR_RE = /^[A-Za-z0-9_-]+\/(?:[A-Za-z0-9_./-]*)$/;
export const _CHIP_CMD_RE = /^\/[a-z][a-z0-9-]+(?:\s.*)?$/i;
export const _CHIP_IP_RE = /^[a-z][a-z0-9_]{1,40}$/i;
export const _PLAIN_FILE_PATH_RE = /(^|[\s([{"'`])((?:[A-Za-z]:[\/\\\u20A9\u00A5\uFFE5\uFF3C]+|\.{1,2}[\/\\\u20A9\u00A5\uFFE5\uFF3C]+|[\/\\\u20A9\u00A5\uFFE5\uFF3C]+)?[A-Za-z0-9_.$~@-]+(?:[\/\\\u20A9\u00A5\uFFE5\uFF3C]+[A-Za-z0-9_.$~@-]+)+\.(?:sv|v|svh|vh|vlt|sdc|tcl|md|markdown|yaml|yml|json|jsonl|txt|log|py|sh|c|cc|cpp|h|hpp|f|html|htm|css|js|jsx|ts|tsx))(?:[:#]L?(\d+))?(?=$|[\s)\]}",.;!?])/gi;
export const _DISPLAY_PATH_SEPARATOR_RE = /[\\\u20A9\u00A5\uFFE5\uFF3C]+|\/{2,}/g;
export const _DISPLAY_PATH_TOKEN_RE = /(^|[^\w./:-])((?:[A-Za-z]:)?(?:[\/\\\u20A9\u00A5\uFFE5\uFF3C]+)?[A-Za-z0-9_.$~@-]+(?:[\/\\\u20A9\u00A5\uFFE5\uFF3C]+[A-Za-z0-9_.$~@-]+)+(?:[\/\\\u20A9\u00A5\uFFE5\uFF3C]+)?)(?=$|[^\w.$~@-])/g;

export const _normalizeDisplayPathToken = (path: unknown): string => (
  String(path || '')
    .replace(_DISPLAY_PATH_SEPARATOR_RE, '/')
    .replace(/\/{2,}/g, '/')
);

export const _normalizeDisplayedToolPaths = (text: unknown): string => (
  String(text || '').replace(
    _DISPLAY_PATH_TOKEN_RE,
    (_match, lead: string, path: string) => `${lead}${_normalizeDisplayPathToken(path)}`,
  )
);

export const _chipKindFor = (text: unknown): string => {
  const t = _normalizeDisplayedToolPaths(text).trim();
  if (!t) return '';
  if (_CHIP_CMD_RE.test(t)) return 'cmd';
  if (_CHIP_PATH_RE.test(t)) return 'path';
  if (_CHIP_DIR_RE.test(t) && t.includes('/')) return 'path';
  if (_CHIP_IP_RE.test(t)) return 'ident';
  return '';
};

export const _resolveOpenableChipPath = (path: unknown): string => {
  const clean = _normalizeDisplayedToolPaths(path)
    .trim()
    .replace(/^['"`]+|['"`]+$/g, '')
    .replace(/(?:#L|:)\d+$/i, '');
  if (!clean) return '';
  if (typeof _mdWin.atlasResolveOpenablePath === 'function') {
    return String(_mdWin.atlasResolveOpenablePath(clean) || '').trim();
  }
  return clean;
};

export const _activateChipPath = (path: unknown): void => {
  const clean = _resolveOpenableChipPath(path);
  if (!clean) return;
  try {
    window.dispatchEvent(new CustomEvent('atlas-chip-open', {
      detail: { path: clean },
    }));
  } catch (_) {}
};

export const _activateChipIp = (name: unknown): void => {
  try {
    window.dispatchEvent(new CustomEvent('atlas-chip-ip', {
      detail: { ip: String(name || '') },
    }));
  } catch (_) {}
};

export const _processInlineChips = (node: any): void => {
  // Skip code chips inside <pre> blocks (those are full code blocks, not chips).
  node.querySelectorAll('code').forEach((el: any) => {
    if (el.closest('pre')) return;
    if (el.dataset && el.dataset.chip) return;     // already processed
    const rawTxt = el.textContent || '';
    const txt = _normalizeDisplayedToolPaths(rawTxt);
    const kind = _chipKindFor(txt);
    if (!kind) return;
    if (txt !== rawTxt) el.textContent = txt;
    const resolvedPath = kind === 'path' ? _resolveOpenableChipPath(txt) : '';
    if (kind === 'path' && !resolvedPath) return;
    el.dataset.chip = kind;
    el.classList.add('chip', `chip-${kind}`);
    if (kind === 'path') {
      el.dataset.path = resolvedPath;
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('title', `open ${resolvedPath}`);
      el.style.cursor = 'pointer';
      el.addEventListener('click', (e: any) => {
        e.stopPropagation();
        _activateChipPath(resolvedPath);
      });
      el.addEventListener('keydown', (e: any) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          _activateChipPath(resolvedPath);
        }
      });
    } else if (kind === 'ident') {
      // Heuristic IP chip — only activate if the token appears to be a
      // real top-level workspace dir under PROJECT_ROOT. The dispatcher
      // (atlas-chip-ip listener) does the existence check; we just emit.
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('title', `switch IP to ${txt}`);
      el.style.cursor = 'pointer';
      el.addEventListener('click', (e: any) => {
        e.stopPropagation();
        _activateChipIp(txt);
      });
      el.addEventListener('keydown', (e: any) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          _activateChipIp(txt);
        }
      });
    }
  });
};

export const _processPlainFilePathChips = (node: any): void => {
  if (!node || !node.ownerDocument) return;
  const doc = node.ownerDocument;
  const walker = doc.createTreeWalker(node, NodeFilter.SHOW_TEXT);
  const textNodes: any[] = [];
  let cur = walker.nextNode();
  while (cur) {
    const parent = cur.parentElement;
    const text = String(cur.nodeValue || '');
    if (
      /[\/\\\u20A9\u00A5\uFFE5\uFF3C]/.test(text) &&
      /\.[A-Za-z0-9]{1,10}/.test(text) &&
      parent &&
      !parent.closest('code, pre, a, button, input, textarea, select, script, style')
    ) {
      textNodes.push(cur);
    }
    cur = walker.nextNode();
  }

  textNodes.forEach((textNode) => {
    const text = String(textNode.nodeValue || '');
    _PLAIN_FILE_PATH_RE.lastIndex = 0;
    let match: RegExpExecArray | null;
    let last = 0;
    let changed = false;
    const frag = doc.createDocumentFragment();
    while ((match = _PLAIN_FILE_PATH_RE.exec(text)) !== null) {
      const lead = match[1] || '';
      const path = _normalizeDisplayedToolPaths(match[2] || '').trim();
      const line = match[3] || '';
      const resolvedPath = _resolveOpenableChipPath(path);
      const start = match.index;
      const tokenStart = start + lead.length;
      if (start > last) frag.appendChild(doc.createTextNode(text.slice(last, start)));
      if (lead) frag.appendChild(doc.createTextNode(lead));
      if (!resolvedPath) {
        frag.appendChild(doc.createTextNode(text.slice(tokenStart, _PLAIN_FILE_PATH_RE.lastIndex)));
        last = _PLAIN_FILE_PATH_RE.lastIndex;
        continue;
      }
      const code = doc.createElement('code');
      code.textContent = line ? `${path}:${line}` : path;
      code.dataset.chip = 'path';
      code.dataset.path = resolvedPath;
      if (line) code.dataset.line = line;
      code.classList.add('chip', 'chip-path');
      code.setAttribute('role', 'button');
      code.setAttribute('tabindex', '0');
      code.setAttribute('title', `open ${resolvedPath}`);
      code.style.cursor = 'pointer';
      code.addEventListener('click', (e: any) => {
        e.stopPropagation();
        _activateChipPath(resolvedPath);
      });
      code.addEventListener('keydown', (e: any) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          _activateChipPath(resolvedPath);
        }
      });
      frag.appendChild(code);
      last = _PLAIN_FILE_PATH_RE.lastIndex;
      changed = true;
    }
    if (!changed) return;
    if (last < text.length) frag.appendChild(doc.createTextNode(text.slice(last)));
    textNode.parentNode?.replaceChild(frag, textNode);
  });
};

// Tag blockquotes by lead marker (e.g. [scope], [rule], [warn]) so CSS
// can color the left border per kind.
export const _BLOCKQUOTE_KINDS: Record<string, string> = {
  rule: 'rule', must: 'rule', critical: 'rule', '!': 'rule',
  warn: 'warn', warning: 'warn', danger: 'warn', error: 'warn',
  hint: 'hint', tip: 'hint', note: 'hint', info: 'hint',
  scope: 'scope', context: 'scope',
};

export const _processBlockquoteKinds = (node: any): void => {
  node.querySelectorAll('blockquote').forEach((bq: any) => {
    if (bq.dataset && bq.dataset.kind) return;
    const text = (bq.textContent || '').trim();
    const m = text.match(/^\[?\s*([A-Za-z!]+)\s*\]?/);
    if (!m) return;
    const tag = String(m[1] || '').trim().toLowerCase();
    const kind = _BLOCKQUOTE_KINDS[tag] || '';
    if (kind) {
      bq.dataset.kind = kind;
      bq.classList.add(`quote-${kind}`);
    }
  });
};

let _mermaidBlockSeq = 0;

export const _ensureMarkdownMermaid = (): any => {
  const mermaid = window.mermaid;
  if (!mermaid || !mermaid.render) return null;
  if (!(window as any).__ATLAS_MERMAID_INITIALIZED) {
    try {
      if (typeof mermaid.initialize === 'function') {
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'strict',
          htmlLabels: false,
          theme: 'base',
          themeVariables: {
            background: 'transparent',
            primaryColor: '#101827',
            primaryBorderColor: '#38bdf8',
            primaryTextColor: '#f7fbff',
            lineColor: '#38bdf8',
            secondaryColor: '#152235',
            tertiaryColor: '#0b111c',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
          },
        });
      }
      (window as any).__ATLAS_MERMAID_INITIALIZED = true;
    } catch (_) {
      return null;
    }
  }
  return mermaid;
};

const _sanitizeMermaidSvg = (rawSvg: unknown): string => {
  const svg = String(rawSvg || '');
  return (window.DOMPurify && window.DOMPurify.sanitize)
    ? window.DOMPurify.sanitize(svg, { USE_PROFILES: { svg: true, svgFilters: true } })
    : svg;
};

export const _renderMermaidBlocks = (node: any): void => {
  if (!node) return;
  const mermaid = _ensureMarkdownMermaid();
  if (!mermaid) return;
  node.querySelectorAll('pre > code.language-mermaid, pre > code[class*="language-mermaid"]').forEach((codeEl: any) => {
    const pre = codeEl.parentElement;
    if (!pre || pre.dataset.mermaidState) return;
    const source = String(codeEl.textContent || '').trim();
    if (!source) return;
    const renderId = `atlas-mermaid-md-${Date.now().toString(36)}-${++_mermaidBlockSeq}`.replace(/[^a-zA-Z0-9_-]/g, '-');
    pre.dataset.mermaidState = 'rendering';
    pre.classList.add('atlas-mermaid-pending');
    pre.textContent = 'rendering mermaid diagram...';
    Promise.resolve(mermaid.render(renderId, source))
      .then((result: any) => {
        const rawSvg = typeof result === 'string' ? result : (result && result.svg) || '';
        const svg = _sanitizeMermaidSvg(rawSvg);
        const block = document.createElement('div');
        block.className = 'atlas-mermaid-block';
        block.innerHTML = svg;
        if (pre.parentElement) pre.replaceWith(block);
      })
      .catch((err: any) => {
        const message = err && err.message ? err.message : String(err || 'Mermaid render failed.');
        pre.dataset.mermaidState = 'error';
        pre.classList.remove('atlas-mermaid-pending');
        pre.classList.add('atlas-mermaid-error');
        pre.textContent = `Mermaid render failed: ${message}\n\n${source}`;
      });
  });
};

export const _postProcessMarkdownNode = (node: any): void => {
  if (!node) return;
  node.querySelectorAll('a[href]').forEach((a: any) => {
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener noreferrer');
  });
  _sanitizePrismLanguageClasses(node);
  _renderMermaidBlocks(node);
  if (window.Prism) {
    try { window.Prism.highlightAllUnder(node); } catch (_) {}
  }
  _processPlainFilePathChips(node);
  _processInlineChips(node);
  _processBlockquoteKinds(node);
};

export const _DIFF_RESULT_TOOL_RE = /^(replace_in_file|replace_lines|replace_file_content|write_file|write_to_file|edit|patch|update_file)/i;

export const _toolOutputLanguage = (tool: unknown, text: unknown): string => {
  const raw = String(text || '');
  const t = raw.trim();
  if (!t) return 'none';

  const extMatch = raw.match(/\b[\w./-]+\.([a-z0-9]+)(?::|\s|$)/i);
  const ext = extMatch && extMatch[1] && extMatch[1].toLowerCase();
  if (ext && window.PRISM_LANG_MAP && window.PRISM_LANG_MAP[ext]) {
    return window.PRISM_LANG_MAP[ext];
  }

  if (/^(diff --git|@@\s|\+\+\+ |--- )/m.test(t)) return 'diff';
  if (/^\s*[{[]/.test(t)) {
    try { JSON.parse(t); return 'json'; } catch (_) {}
  }
  if (/^(\s*---\s*$|\s*[\w.-]+:\s|-\s+[\w.-]+:\s)/m.test(t)) return 'yaml';
  if (/\b(module|endmodule|always_ff|always_comb|assign|logic|wire|reg)\b/.test(t)) return 'verilog';
  if (/\b(import|from|def|class|Traceback \(most recent call last\))\b/.test(t)) return 'python';
  if (/\b(const|let|function|return|className=|React\.|=>)\b/.test(t)) return 'jsx';
  if (/^\s*(git|npm|pnpm|yarn|python3?|pytest|rg|sed|cmux|curl|uv|make|cargo)\b/m.test(t)) return 'bash';
  if (/^<([a-z][\w:-]*)(\s|>)/i.test(t)) return 'html';
  if (String(tool || '').toLowerCase().includes('git')) return 'diff';
  return 'none';
};

export const _limitToolOutputLines = (text: unknown, maxLines: unknown): string => {
  const body = _normalizeDisplayedToolPaths(text);
  const limit = Math.max(0, Math.floor(Number(maxLines || 0)));
  if (!limit) return body;
  const lines = body.split('\n');
  if (lines.length <= limit) return body;
  const hidden = lines.length - limit;
  return `${lines.slice(0, limit).join('\n')}\n... ${hidden} more line${hidden === 1 ? '' : 's'} hidden`;
};

export const ToolOutputPre = ({ text, tool, truncated, maxLines }: any): ReactNode => {
  const codeRef = useRef<any>(null);
  const fullBody = _normalizeDisplayedToolPaths(text) + (truncated ? '\n…[truncated]' : '');
  const body = _limitToolOutputLines(fullBody, maxLines);
  const tooLarge = body.length > 60000;
  const lang = tooLarge ? 'none' : _toolOutputLanguage(tool, body);
  const className = lang && lang !== 'none' ? `language-${lang}` : 'language-none';

  useEffect(() => {
    const code = codeRef.current;
    const Prism = window.Prism;
    if (!code || !Prism || !lang || lang === 'none') return;
    const highlight = () => {
      try { Prism.highlightElement(code); } catch (_) {}
    };
    if (Prism.languages && Prism.languages[lang]) {
      highlight();
    } else if (Prism.plugins && Prism.plugins.autoloader && Prism.plugins.autoloader.loadLanguages) {
      try { Prism.plugins.autoloader.loadLanguages(lang, highlight); } catch (_) {}
    }
  }, [body, lang]);

  return (
    <pre className={`tool-output-pre ${className}`}>
      <code ref={codeRef} className={className}>{body}</code>
    </pre>
  );
};

export type GrepOutputRowKind = 'header' | 'separator' | 'raw' | 'match' | 'context';
export type GrepOutputRow = {
  readonly kind: GrepOutputRowKind;
  readonly file: string;
  readonly lineNumber: string;
  readonly code: string;
  readonly text: string;
};

const _GREP_FORMATTED_ROW_RE = /^(?:(>>>)\s*)?(\s*\d+):(\s?)(.*)$/;
const _GREP_SYSTEM_MATCH_ROW_RE = /^(.+?):(\d+):(.*)$/;
const _GREP_SYSTEM_CONTEXT_ROW_RE = /^(.+)-(\d+)-(.*)$/;

export const _grepOutputRows = (text: unknown): readonly GrepOutputRow[] => {
  const body = _normalizeDisplayedToolPaths(text);
  return body.split('\n').map((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed === '--') {
      return { kind: 'separator', file: '', lineNumber: '', code: '', text: line };
    }
    if (
      /^=== .* ===$/.test(trimmed)
      || /^Found \d+ matches? in\b/.test(trimmed)
      || /^No matches found\b/.test(trimmed)
      || /^…\[truncated\]$/.test(trimmed)
    ) {
      return { kind: 'header', file: '', lineNumber: '', code: '', text: line };
    }

    const formatted = line.match(_GREP_FORMATTED_ROW_RE);
    if (formatted) {
      const marker = formatted[1] || '';
      return {
        kind: marker ? 'match' : 'context',
        file: '',
        lineNumber: formatted[2].trim(),
        code: formatted[4] || '',
        text: line,
      };
    }

    const systemMatch = line.match(_GREP_SYSTEM_MATCH_ROW_RE);
    if (systemMatch) {
      return {
        kind: 'match',
        file: systemMatch[1],
        lineNumber: systemMatch[2],
        code: systemMatch[3] || '',
        text: line,
      };
    }

    const systemContext = line.match(_GREP_SYSTEM_CONTEXT_ROW_RE);
    if (systemContext) {
      return {
        kind: 'context',
        file: systemContext[1],
        lineNumber: systemContext[2],
        code: systemContext[3] || '',
        text: line,
      };
    }

    return { kind: 'raw', file: '', lineNumber: '', code: '', text: line };
  });
};

export const GrepOutputPre = ({ text, truncated, maxLines }: any): ReactNode => {
  const fullBody = _normalizeDisplayedToolPaths(text) + (truncated ? '\n…[truncated]' : '');
  const body = _limitToolOutputLines(fullBody, maxLines);
  const rows = _grepOutputRows(body);

  return (
    <pre className="tool-output-pre tool-output-grep language-none">
      {rows.map((row, i) => {
        if (!row.lineNumber) {
          return (
            <div className={`grep-line grep-${row.kind}`} key={i}>
              {row.text || ' '}
            </div>
          );
        }
        return (
          <div className={`grep-line grep-${row.kind}`} key={i}>
            <span className="grep-prefix">{row.lineNumber}</span>
            <span className="grep-sep">|</span>
            <code className="grep-code language-none" data-grep-code="true">{row.code}</code>
          </div>
        );
      })}
    </pre>
  );
};

export const _highlightInlineCode = (code: string, lang: string): string => {
  const Prism = window.Prism;
  if (!Prism || !lang || lang === 'none' || !Prism.languages || !Prism.languages[lang]) {
    return _escapeHtml(code);
  }
  try {
    return Prism.highlight(code, Prism.languages[lang], lang);
  } catch (_) {
    return _escapeHtml(code);
  }
};

export const DiffOutputPre = ({ text, tool, truncated, hintText = '', maxLines }: any): ReactNode => {
  const fullBody = _normalizeDisplayedToolPaths(text) + (truncated ? '\n…[truncated]' : '');
  const body = _limitToolOutputLines(fullBody, maxLines);
  // Unified row format from format_diff_snippet:
  //   context  : "{num}  {content}"        (num + 2 spaces + content)
  //   removed  : "{num} -{content}"        (num + space + '-' + content)
  //   added    : "{num} +{content}"        (num + space + '+' + content)
  // We match all three with the same regex so context rows render
  // through the same span structure (prefix + marker placeholder +
  // code) — otherwise context rows render as raw text and the +/- rows
  // shift left of them, making indentation look broken.
  const ROW_RE = /^(\s*\d+)\s([ \-+])(.*)$/;
  const codeOnly = body.split('\n').map((line) => {
    const m = line.match(ROW_RE);
    return m ? m[3] : line;
  }).join('\n');
  const lang = _toolOutputLanguage(tool, `${hintText || ''}\n${codeOnly}`);
  const [, forceRerender] = useState(0);

  useEffect(() => {
    const Prism = window.Prism;
    if (!Prism || !lang || lang === 'none' || (Prism.languages && Prism.languages[lang])) return;
    if (Prism.plugins && Prism.plugins.autoloader && Prism.plugins.autoloader.loadLanguages) {
      try {
        Prism.plugins.autoloader.loadLanguages(lang, () => forceRerender((n: number) => n + 1));
      } catch (_) {}
    }
  }, [lang, body]);

  return (
    <pre className={`tool-output-pre tool-output-diff ${lang && lang !== 'none' ? `language-${lang}` : 'language-none'}`}>
      {body.split('\n').map((line, i) => {
        const m = line.match(ROW_RE);
        if (!m) return <div className="diff-line" key={i}>{line || ' '}</div>;
        const [, numStr, sep, rest] = m;
        const add = sep === '+';
        const del = sep === '-';
        const cls = add ? 'add' : del ? 'del' : '';
        return (
          <div className={`diff-line ${cls}`} key={i}>
            <span className="diff-prefix">{numStr}</span>
            <span className={`diff-marker ${cls}`}>{add || del ? sep : ' '}</span>
            <code
              className={lang && lang !== 'none' ? `language-${lang}` : 'language-none'}
              dangerouslySetInnerHTML={{ __html: _highlightInlineCode(rest, lang) }}
            />
          </div>
        );
      })}
    </pre>
  );
};

// Hover-revealed copy button (positioned absolute; parent must be
// position:relative and apply CSS `:hover .copy-btn{opacity:1}`).
export const _copyToClipboard = uiCopyToClipboard;
export const CopyBtn = UiCopyBtn;
