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
 *   • _copyToClipboard / CopyBtn: window-reads re-declared here (used by the Pre
 *     components and re-published in the legacy file).
 */
import { useState, useEffect, useRef, type ReactNode } from 'react';

// ── Cross-module window globals owned by sibling slices ────────────────
// renderInline / _escHtml are owned by workspace-feed-cards.tsx and
// _unwrapAtlasOutputFence by workspace-report-status.tsx. Those siblings
// import FROM this file, so importing them back would create a cycle — we
// read them off window (legacy publishes _escHtml; the others are read with
// graceful fallbacks). marked / DOMPurify / Prism / PRISM_LANG_MAP /
// _copyToClipboard / CopyBtn are declared in types/atlas-window.d.ts.
interface MarkdownChipWindowGlobals {
  renderInline?: (s: string) => string;
  _unwrapAtlasOutputFence?: (text: unknown) => string;
  _escHtml?: (s: unknown) => string;
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
export const _CHIP_PATH_RE = /^[A-Za-z0-9_./-]+\.(?:sv|v|svh|vh|vlt|sdc|tcl|md|yaml|yml|json|jsonl|txt|log|py|sh|c|cc|cpp|h|hpp|f)$/i;
export const _CHIP_DIR_RE = /^[A-Za-z0-9_-]+\/(?:[A-Za-z0-9_./-]*)$/;
export const _CHIP_CMD_RE = /^\/[a-z][a-z0-9-]+(?:\s.*)?$/i;
export const _CHIP_IP_RE = /^[a-z][a-z0-9_]{1,40}$/i;
const _BACKSLASH_PATH_TOKEN_RE = /(^|[^\w./:-])((?:[A-Za-z]:\\+[A-Za-z0-9_.$~@-]+(?:\\+[A-Za-z0-9_.$~@-]+)*|[A-Za-z0-9_.$~@-]+(?:\\+[A-Za-z0-9_.$~@-]+)+(?:\\+)?))/g;

export const _normalizeDisplayedToolPaths = (text: unknown): string => (
  String(text || '').replace(
    _BACKSLASH_PATH_TOKEN_RE,
    (_match, lead: string, path: string) => `${lead}${String(path).replace(/\\+/g, '/')}`,
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

export const _activateChipPath = (path: unknown): void => {
  try {
    window.dispatchEvent(new CustomEvent('atlas-chip-open', {
      detail: { path: _normalizeDisplayedToolPaths(path) },
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
    el.dataset.chip = kind;
    el.classList.add('chip', `chip-${kind}`);
    if (kind === 'path') {
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('title', `open ${txt}`);
      el.style.cursor = 'pointer';
      el.addEventListener('click', (e: any) => {
        e.stopPropagation();
        _activateChipPath(txt);
      });
      el.addEventListener('keydown', (e: any) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          _activateChipPath(txt);
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

export const _postProcessMarkdownNode = (node: any): void => {
  if (!node) return;
  node.querySelectorAll('a[href]').forEach((a: any) => {
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener noreferrer');
  });
  _sanitizePrismLanguageClasses(node);
  if (window.Prism) {
    try { window.Prism.highlightAllUnder(node); } catch (_) {}
  }
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

export const ToolOutputPre = ({ text, tool, truncated }: any): ReactNode => {
  const codeRef = useRef<any>(null);
  const body = _normalizeDisplayedToolPaths(text) + (truncated ? '\n…[truncated]' : '');
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

export const DiffOutputPre = ({ text, tool, truncated, hintText = '' }: any): ReactNode => {
  const body = _normalizeDisplayedToolPaths(text) + (truncated ? '\n…[truncated]' : '');
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
// Phase 13e: CopyBtn + _copyToClipboard moved to frontend/atlas/ui-utils.jsx
// (loaded before workspace.jsx in index.html). Alias the globals back to the
// original names so the rest of this file references them unchanged.
export const _copyToClipboard = window._copyToClipboard;
export const CopyBtn = window.CopyBtn;
