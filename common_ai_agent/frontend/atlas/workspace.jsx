// workspace.jsx — Chat-centric: ReAct + inline Q&A cards + SSOT/Todo sidebar + file viewer

// ── Tool-call visual theme ────────────────────────────────────────
// Tool calls use one accent color so the chat feed stays calm. Glyphs
// still provide a small shape cue without turning the feed into a legend.
const TOOL_ACCENT = 'var(--tool-accent)';
const TOOL_THEME = {
  write_file:        { glyph: '✎', color: TOOL_ACCENT },
  replace_in_file:   { glyph: '✎', color: TOOL_ACCENT },
  replace_lines:     { glyph: '✎', color: TOOL_ACCENT },
  read_file:         { glyph: '▤', color: TOOL_ACCENT },
  read_lines:        { glyph: '▤', color: TOOL_ACCENT },
  grep_file:         { glyph: '⌕', color: TOOL_ACCENT },
  find_files:        { glyph: '⌕', color: TOOL_ACCENT },
  list_dir:          { glyph: '⌕', color: TOOL_ACCENT },
  run_command:       { glyph: '▶', color: TOOL_ACCENT },
  todo_update:       { glyph: '☑', color: TOOL_ACCENT },
  todo_write:        { glyph: '☑', color: TOOL_ACCENT },
  todo_add:          { glyph: '☑', color: TOOL_ACCENT },
  todo_remove:       { glyph: '☑', color: TOOL_ACCENT },
  todo_status:       { glyph: '☑', color: TOOL_ACCENT },
  todo_note:         { glyph: '☑', color: TOOL_ACCENT },
  scaffold_ip:       { glyph: '◆', color: TOOL_ACCENT },
  ask_user:          { glyph: '⏸', color: TOOL_ACCENT },
  read_doc:          { glyph: '▤', color: TOOL_ACCENT },
  git_diff:          { glyph: '◇', color: TOOL_ACCENT },
  git_status:        { glyph: '◇', color: TOOL_ACCENT },
  __default:         { glyph: '▶', color: TOOL_ACCENT },
};
const _toolTheme = (name) => TOOL_THEME[name] || TOOL_THEME.__default;

// Agent meta-cognition tools (todo_*) drive the LLM's session-local working
// memory — completely separate from the workflow's stage TODO tracker
// (RTL-XXXX in rtl_todo_tracker.json, surfaced in the right-side panel).
// Render them as `step_*` in chat so users do NOT conflate agent step
// counters (#2, #3) with the workflow tracker's stable IDs (RTL-0060).
// The underlying tool name is unchanged; only the chat label is swapped.
const _TOOL_CHAT_ALIAS = {
  todo_update: 'step_update',
  todo_note:   'step_note',
  todo_write:  'step_write',
  todo_add:    'step_add',
  todo_remove: 'step_remove',
  todo_status: 'step_status',
};
const _toolDisplay = (name) => _TOOL_CHAT_ALIAS[name] || name || '?';

// Direct workflow/slash results also arrive as `slash_output`, which is the
// user-facing Markdown surface. Keep their mirrored `tool_result` event for
// data refresh subscribers, but do not render it again as a plain obs block.
const WORKFLOW_RESULT_TOOLS = new Set([
  'slash',
  'workflow',
  'import',
  'new-ip',
  'grill-me',
  'approve',
  'to-ssot',
  'resolve-rtl-blockers',
  'sim-debug',
  'repair-ssot',
  'repair-rtl',
  'repair-equiv',
  'validate-yaml',
  'ssot-fl-model',
  'ssot-equiv-goals',
  'ssot-rtl',
  'ssot-tb-cocotb',
  'ssot-tb',
  'ssot-tb-uvm',
  'ssot-tb-verilog',
  'ssot-tb-sv',
  'tb',
  'sim',
  'lint',
  'syn',
  'sta',
  'coverage',
  'goal-audit',
  'signoff',
]);
const _isWorkflowResultTool = (tool) => WORKFLOW_RESULT_TOOLS.has(String(tool || '').toLowerCase());
const INPUT_HISTORY_LIMIT = 200;
const QA_HISTORY_LIMIT = 50;
const QA_HISTORY_LEGACY_STORAGE_KEY = 'atlasQaHistory';
const QA_HISTORY_STORAGE_PREFIX = 'atlasQaHistory:';
const WORKFLOW_REPORT_TABS = {
  lint: {
    label: 'lint report',
    title: 'Lint Report',
    folders: ['lint'],
    paths: (ip) => [
      `${ip}/lint/dut_lint.json`,
      `${ip}/lint/rtl_lint.json`,
      `${ip}/lint/lint_report.txt`,
      `${ip}/lint/verilator.log`,
      `${ip}/lint/lint.log`,
      `gpio/${ip}/lint/dut_lint.json`,
      `gpio/${ip}/lint/dut_lint.log`,
    ],
  },
  coverage: {
    label: 'coverage report',
    title: 'Coverage Report',
    folders: ['cov', 'sim'],
    paths: (ip) => [
      `${ip}/cov/coverage.json`,
      `${ip}/cov/coverage_ssot.json`,
      `${ip}/cov/coverage.info`,
      `${ip}/cov/toggle.json`,
      `${ip}/cov/merged.vcd`,
      `${ip}/sim/coverage_report.md`,
      `${ip}/sim/${ip}.vcd`,
      `gpio/${ip}/cov/coverage.json`,
      `gpio/${ip}/cov/coverage_ssot.json`,
      `gpio/${ip}/cov/coverage.info`,
      `gpio/${ip}/cov/toggle.json`,
      `gpio/${ip}/sim/coverage_report.md`,
      `gpio/${ip}/sim/${ip}.vcd`,
    ],
  },
  syn: {
    label: 'syn_report',
    title: 'Synthesis Report',
    folders: ['syn', 'reports/synth'],
    paths: (ip) => [
      `${ip}/syn/out/syn.report.md`,
      `${ip}/syn/out/area.json`,
      `${ip}/syn/out/synth.v`,
      `${ip}/syn/out/yosys.log`,
      `${ip}/syn/syn.report.md`,
      `${ip}/reports/synth/qor.json`,
    ],
  },
  sta: {
    label: 'sta_report',
    title: 'STA Report',
    folders: ['sta', 'reports/sta'],
    paths: (ip) => [
      `${ip}/sta/out/sta.report.md`,
      `${ip}/sta/out/wns.json`,
      `${ip}/sta/out/timing.rpt`,
      `${ip}/sta/out/setup.rpt`,
      `${ip}/sta/out/hold.rpt`,
      `${ip}/sta/out/sta.log`,
      `${ip}/reports/sta/timing.json`,
    ],
  },
  pnr: {
    label: 'pnr_report',
    title: 'PNR Report',
    folders: ['pnr', 'reports/pnr'],
    paths: (ip) => [
      `${ip}/pnr/out/pnr.report.md`,
      `${ip}/pnr/out/route.json`,
      `${ip}/pnr/out/drc.json`,
      `${ip}/pnr/out/density.json`,
      `${ip}/pnr/out/pnr.log`,
      `${ip}/pnr/out/routed.def`,
      `${ip}/reports/pnr/route.json`,
    ],
  },
  'tb-gen': {
    label: 'TB Structure',
    title: 'TB Structure',
    folders: ['tb', 'tc', 'verify', 'sim'],
    paths: (ip) => [
      `${ip}/tb/cocotb/tb_structure.json`,
      `${ip}/tb/cocotb/test_${ip}.py`,
      `${ip}/tb/cocotb/sequences.py`,
      `${ip}/tb/cocotb/agents.py`,
      `${ip}/tb/cocotb/scoreboard.py`,
      `${ip}/tb/tb_${ip}.sv`,
      `${ip}/tc/tc_list.json`,
      `${ip}/tc/test_list.json`,
      `${ip}/verify/equivalence_goals.json`,
      `${ip}/sim/scoreboard_events.jsonl`,
      `${ip}/yaml/${ip}.ssot.yaml`,
    ],
  },
};

// Detect success/error in a tool result body. Used by ObsCard to
// stamp a leading ✓/✗ badge + override border color on errors.
const _obsStatus = (txt) => {
  const t = (txt || '').toLowerCase();
  if (/^\s*(error[:!]|\[error\]|✗|❌|\[plan mode\] .* blocked|exit code [1-9]|traceback|^exception:|fatal:)/m.test(t)) return 'err';
  if (/✓|^\s*ok\b|successfully|approved|wrote to|completed|matched|^✅|file does not exist/m.test(t)) {
    // "file does not exist" comes from read_file on a missing path —
    // ambiguous; lean neutral rather than green.
    if (/file does not exist|not found/m.test(t)) return 'neutral';
    return 'ok';
  }
  return 'neutral';
};

const ATLAS_STATUS_META = {
  loading:      { glyph: '◌', color: 'var(--accent)', label: 'loading' },
  refreshing:  { glyph: '↻', color: 'var(--accent)', label: 'refreshing' },
  running:     { glyph: '●', color: 'var(--accent)', label: 'running' },
  active:      { glyph: '●', color: 'var(--accent)', label: 'running' },
  in_progress: { glyph: '●', color: 'var(--accent)', label: 'in-progress' },
  pending:     { glyph: '○', color: 'var(--warn)', label: 'pending' },
  completed:   { glyph: '✓', color: 'var(--ok)', label: 'completed' },
  done:        { glyph: '✓', color: 'var(--ok)', label: 'done' },
  approved:    { glyph: '✓', color: 'var(--ok)', label: 'approved' },
  rejected:    { glyph: '✕', color: 'var(--err)', label: 'rejected' },
  blocked:     { glyph: '!', color: 'var(--err)', label: 'blocked' },
  error:       { glyph: '!', color: 'var(--err)', label: 'error' },
  review:      { glyph: '·', color: 'var(--fg-mute)', label: 'review' },
  needs_review: { glyph: '!', color: 'var(--warn)', label: 'needs review' },
  draft:       { glyph: '·', color: 'var(--fg-mute)', label: 'draft' },
  total:       { glyph: 'Σ', color: 'var(--fg-mute)', label: 'total' },
};

const normalizeAtlasStatus = (status) => {
  const s = String(status || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
  if (s === 'in_progress' || s === 'inprogress') return 'in_progress';
  if (s === 'needs_review' || s === 'needsreview') return 'needs_review';
  if (s === 'fail' || s === 'failed' || s === 'err') return 'error';
  if (s === 'ok' || s === 'pass' || s === 'passed') return 'approved';
  return s || 'pending';
};

const atlasStatusMeta = (status) => {
  const key = normalizeAtlasStatus(status);
  return ATLAS_STATUS_META[key] || { glyph: '·', color: 'var(--fg-mute)', label: String(status || 'unknown') };
};

const AtlasStatusBadge = ({ status, label, count, compact = false, soft = false, title }) => {
  const meta = atlasStatusMeta(status);
  const text = label || meta.label;
  return (
    <span
      className={`atlas-status-badge${compact ? ' compact' : ''}${soft ? ' soft' : ''}`}
      style={{ '--status-color': meta.color }}
      title={title || text}
    >
      <span className="atlas-status-dot">{meta.glyph}</span>
      <span>{count != null ? `${count} ${text}` : text}</span>
    </span>
  );
};

const _limitAtlasLines = (text, maxLines = 5) => {
  const lines = String(text || '').split(/\r?\n/).map(l => l.trimEnd());
  const clean = lines.filter(l => l.trim());
  if (clean.length <= maxLines) return clean.join('\n');
  return clean.slice(0, maxLines).join('\n') + `\n... (+${clean.length - maxLines} more)`;
};

const TODO_TOOL_RE = /^todo_(write|update|add|remove|status|note)$/i;
const TODO_STATUS_MARKS = {
  '⏸': 'pending',
  '▶': 'in-progress',
  '👀': 'completed',
  '✅': 'approved',
  '❌': 'rejected',
  '[ ]': 'pending',
  '[>]': 'in-progress',
  '[.]': 'completed',
  '[v]': 'approved',
  '[x]': 'rejected',
};

const _todoStatusTally = (txt) => {
  const tally = {};
  const statusRe = /^\s*(⏸|▶|👀|✅|❌|\[\s?\]|\[>\]|\[\.]|\[v\]|\[x\])\s/gm;
  let mm;
  while ((mm = statusRe.exec(String(txt || ''))) !== null) {
    const k = TODO_STATUS_MARKS[mm[1]];
    if (k) tally[k] = (tally[k] || 0) + 1;
  }
  return tally;
};

const _todoTallyLine = (tally) =>
  ['in-progress', 'pending', 'completed', 'approved', 'rejected']
    .filter(k => tally[k])
    .map(k => `${tally[k]} ${k}`)
    .join(' · ');

const _cleanTodoToolText = (text, tool) => {
  let txt = String(text || '').trim();
  if (!TODO_TOOL_RE.test(String(tool || ''))) return txt;

  const tally = _todoStatusTally(txt);
  const tallyStr = _todoTallyLine(tally);
  txt = txt.replace(/\n\s*── TODO ──[\s\S]*$/m, '').trim();
  txt = txt.replace(/\n\s*--- TODO ---[\s\S]*$/m, '').trim();

  let m = txt.match(/^[✅\[]?v?\]?\s*Task\s+(\d+)\s+approved\.\s*\[([\s\S]*?)\]\s*([\s\S]*)$/i);
  if (m) {
    const next = (m[3] || '').split(/\r?\n/).map(l => l.trim()).filter(l => /^→?\s*Next:/i.test(l))[0] || '';
    return [
      `Task ${m[1]} approved`,
      `Approved: ${_limitAtlasLines(m[2], 5)}`,
      next.replace(/^→\s*/, ''),
      tallyStr ? `Todo: ${tallyStr}` : '',
    ].filter(Boolean).join('\n');
  }

  m = txt.match(/^[❌\[]?x?\]?\s*Task\s+(\d+)\s+rejected:?\s*([\s\S]*)$/i);
  if (m) {
    return [
      `Task ${m[1]} rejected`,
      `Rejected: ${_limitAtlasLines(m[2], 5)}`,
      tallyStr ? `Todo: ${tallyStr}` : '',
    ].filter(Boolean).join('\n');
  }

  m = txt.match(/^Task\s+(\d+)\s+marked\s+completed\./i);
  if (m) {
    return [
      `Task ${m[1]} completed`,
      'Review: verify ground-truth artifacts, then approve or reject with evidence.',
      tallyStr ? `Todo: ${tallyStr}` : '',
    ].filter(Boolean).join('\n');
  }

  m = txt.match(/^(?:📝\s*)?Note\s+\[(\d+)\]\s+added\s+to\s+Task\s+(\d+):\s*([\s\S]*)$/i);
  if (m) {
    return [
      `Task ${m[2]} note added`,
      `Notes : [${m[1]}] ${_limitAtlasLines(m[3], 5)}`,
      tallyStr ? `Todo: ${tallyStr}` : '',
    ].filter(Boolean).join('\n');
  }

  return txt + (tallyStr && !txt.includes(tallyStr) ? `\nTodo: ${tallyStr}` : '');
};

// Relative timestamp helper for hover-revealed "5m ago" labels.
const _relTime = (ts) => {
  if (!ts) return '';
  const d = Math.max(0, (Date.now() - ts) / 1000);
  if (d < 5) return 'just now';
  if (d < 60) return `${Math.floor(d)}s ago`;
  if (d < 3600) return `${Math.floor(d / 60)}m ago`;
  if (d < 86400) return `${Math.floor(d / 3600)}h ago`;
  return `${Math.floor(d / 86400)}d ago`;
};

const _unwrapAtlasOutputFence = (text) => {
  const raw = String(text || '');
  const trimmed = raw.trim();
  const m = trimmed.match(/^```(?:text|markdown|md)?\s*\n([\s\S]*?)\n```$/i);
  if (!m) return raw;
  const body = m[1].trim();
  if (/^\[(SSOT|MAS|SIM|ATLAS|APPROVED|Plan Mode|to-ssot|ssot-|repair-|resolve-|workflow|import|new-ip|grill|lint|syn|sta|coverage)\b/i.test(body)) {
    return body;
  }
  return raw;
};

const _markdownHtml = (text) => {
  const body = _unwrapAtlasOutputFence(text);
  const rawHtml = (typeof window.marked !== 'undefined' && window.marked.parse)
    ? window.marked.parse(body || '', { breaks: true, gfm: true })
    : renderInline(body || '');
  return (typeof window.DOMPurify !== 'undefined' && window.DOMPurify.sanitize)
    ? window.DOMPurify.sanitize(rawHtml, { ADD_ATTR: ['target', 'rel'] })
    : rawHtml;
};

// Inline-code chip classification + interactivity. Inline `<code>`
// elements ( markdown backticks ) are classified into a few token types
// so CSS can style them differently, and path-like / IP-like chips
// become clickable so the user can pivot the preview pane or active IP
// straight from the chat feed.
const _CHIP_PATH_RE = /^[A-Za-z0-9_./-]+\.(?:sv|v|svh|vh|vlt|sdc|tcl|md|yaml|yml|json|jsonl|txt|log|py|sh|c|cc|cpp|h|hpp|f)$/i;
const _CHIP_DIR_RE  = /^[A-Za-z0-9_-]+\/(?:[A-Za-z0-9_./-]*)$/;
const _CHIP_CMD_RE  = /^\/[a-z][a-z0-9-]+(?:\s.*)?$/i;
const _CHIP_IP_RE   = /^[a-z][a-z0-9_]{1,40}$/i;

const _chipKindFor = (text) => {
  const t = String(text || '').trim();
  if (!t) return '';
  if (_CHIP_CMD_RE.test(t)) return 'cmd';
  if (_CHIP_PATH_RE.test(t)) return 'path';
  if (_CHIP_DIR_RE.test(t) && t.includes('/')) return 'path';
  if (_CHIP_IP_RE.test(t)) return 'ident';
  return '';
};

const _activateChipPath = (path) => {
  try {
    window.dispatchEvent(new CustomEvent('atlas-chip-open', {
      detail: { path: String(path || '') },
    }));
  } catch (_) {}
};

const _activateChipIp = (name) => {
  try {
    window.dispatchEvent(new CustomEvent('atlas-chip-ip', {
      detail: { ip: String(name || '') },
    }));
  } catch (_) {}
};

const _processInlineChips = (node) => {
  // Skip code chips inside <pre> blocks (those are full code blocks, not chips).
  node.querySelectorAll('code').forEach(el => {
    if (el.closest('pre')) return;
    if (el.dataset && el.dataset.chip) return;     // already processed
    const txt = el.textContent || '';
    const kind = _chipKindFor(txt);
    if (!kind) return;
    el.dataset.chip = kind;
    el.classList.add('chip', `chip-${kind}`);
    if (kind === 'path') {
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('title', `open ${txt}`);
      el.style.cursor = 'pointer';
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        _activateChipPath(txt);
      });
      el.addEventListener('keydown', (e) => {
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
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        _activateChipIp(txt);
      });
      el.addEventListener('keydown', (e) => {
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
const _BLOCKQUOTE_KINDS = {
  rule: 'rule', must: 'rule', critical: 'rule', '!': 'rule',
  warn: 'warn', warning: 'warn', danger: 'warn', error: 'warn',
  hint: 'hint', tip: 'hint', note: 'hint', info: 'hint',
  scope: 'scope', context: 'scope',
};

const _processBlockquoteKinds = (node) => {
  node.querySelectorAll('blockquote').forEach(bq => {
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

const _postProcessMarkdownNode = (node) => {
  if (!node) return;
  node.querySelectorAll('a[href]').forEach(a => {
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener noreferrer');
  });
  if (window.Prism) {
    node.querySelectorAll('pre > code').forEach(c => {
      const has = (c.className || '').match(/\blanguage-/);
      if (!has) c.classList.add('language-none');
    });
    try { window.Prism.highlightAllUnder(node); } catch (_) {}
  }
  _processInlineChips(node);
  _processBlockquoteKinds(node);
};

const _toolOutputLanguage = (tool, text) => {
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

const ToolOutputPre = ({ text, tool, truncated }) => {
  const codeRef = React.useRef(null);
  const body = String(text || '') + (truncated ? '\n…[truncated]' : '');
  const tooLarge = body.length > 60000;
  const lang = tooLarge ? 'none' : _toolOutputLanguage(tool, body);
  const className = lang && lang !== 'none' ? `language-${lang}` : 'language-none';

  React.useEffect(() => {
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

const _highlightInlineCode = (code, lang) => {
  const Prism = window.Prism;
  if (!Prism || !lang || lang === 'none' || !Prism.languages || !Prism.languages[lang]) {
    return _escHtml(code);
  }
  try {
    return Prism.highlight(code, Prism.languages[lang], lang);
  } catch (_) {
    return _escHtml(code);
  }
};

const DiffOutputPre = ({ text, tool, truncated }) => {
  const body = String(text || '') + (truncated ? '\n…[truncated]' : '');
  // Unified row format from format_diff_snippet:
  //   context  : "{num}  {content}"        (num + 2 spaces + content)
  //   removed  : "{num} -{content}"        (num + space + '-' + content)
  //   added    : "{num} +{content}"        (num + space + '+' + content)
  // We match all three with the same regex so context rows render
  // through the same span structure (prefix + marker placeholder +
  // code) — otherwise context rows render as raw text and the +/- rows
  // shift left of them, making indentation look broken.
  const ROW_RE = /^(\s*\d+)\s([ \-+])(.*)$/;
  const codeOnly = body.split('\n').map(line => {
    const m = line.match(ROW_RE);
    return m ? m[3] : line;
  }).join('\n');
  const lang = _toolOutputLanguage(tool, codeOnly);
  const [, forceRerender] = React.useState(0);

  React.useEffect(() => {
    const Prism = window.Prism;
    if (!Prism || !lang || lang === 'none' || (Prism.languages && Prism.languages[lang])) return;
    if (Prism.plugins && Prism.plugins.autoloader && Prism.plugins.autoloader.loadLanguages) {
      try {
        Prism.plugins.autoloader.loadLanguages(lang, () => forceRerender(n => n + 1));
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
const CopyBtn = ({ text, label = 'copy' }) => {
  const [copied, setCopied] = React.useState(false);
  const onClick = (e) => {
    e.stopPropagation();
    try { navigator.clipboard.writeText(text || ''); setCopied(true); setTimeout(() => setCopied(false), 1200); }
    catch (_) {}
  };
  return (
    <button onClick={onClick} className="copy-btn" type="button"
      style={{
        position: 'absolute', top: 6, right: 6,
        opacity: 0, transition: 'opacity .15s',
        background: 'var(--bg-2)', border: '1px solid var(--line)',
        color: copied ? 'var(--ok)' : 'var(--fg-mute)',
        fontSize: 10, padding: '1px 6px', borderRadius: 2,
        cursor: 'pointer', fontFamily: 'var(--mono)',
      }}>
      {copied ? '✓ copied' : label}
    </button>
  );
};

// ── Column-resize helpers ─────────────────────────────────────────
// useResizable: state + localStorage persistence + clamp.
// `0` is the special "collapsed" value; any positive width is clamped
// to [minW, maxW]. A separate "lastNonZero" remembers the user's last
// open width so collapse → expand restores cleanly.
const useResizable = (initial, storageKey, minW, maxW, restoreCollapsed = true) => {
  const [w, setW] = React.useState(() => {
    try {
      const raw = parseInt(localStorage.getItem(storageKey), 10);
      if (Number.isFinite(raw) && raw === 0 && restoreCollapsed) {
        return 0;
      }
      if (Number.isFinite(raw) && raw >= minW) {
        return Math.min(maxW, raw);
      }
    } catch (_) {}
    return initial;
  });
  const lastOpenRef = React.useRef(w > 0 ? w : initial);
  React.useEffect(() => {
    if (w > 0) lastOpenRef.current = w;
    try { localStorage.setItem(storageKey, String(w)); } catch (_) {}
  }, [w, storageKey]);
  const set = React.useCallback((next) => {
    if (next === 0) { setW(0); return; }
    setW(Math.max(minW, Math.min(maxW, next)));
  }, [minW, maxW]);
  const toggle = React.useCallback(() => {
    setW(prev => prev === 0 ? lastOpenRef.current : 0);
  }, []);
  return [w, set, toggle];
};

// Splitter: 4px-wide drag handle. drag → resize via onResize(width).
// Double-click → onToggle(). Side='left' resizes the LEFT column
// (drag right widens), side='right' resizes the RIGHT column (drag
// left widens — direction inverted).
const Splitter = ({ width, side, onResize, onToggle, title }) => {
  const drag = React.useRef(null);
  const onMouseDown = (e) => {
    e.preventDefault();
    drag.current = { x: e.clientX, w0: width };
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
    const onMove = (ev) => {
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
      onMouseEnter={(e) => { e.currentTarget.style.background = 'color-mix(in oklch, var(--accent) 30%, transparent)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    />
  );
};

const normalizeUiSession = (session) => {
  const norm = (window.atlasData && window.atlasData.normalizeSessionName) || window.normalizeAtlasSessionName;
  try { return norm ? norm(session || '') : ''; }
  catch (_) { return ''; }
};

const ssotIpFromSession = (session) => {
  const parts = normalizeUiSession(session).split('/').filter(Boolean);
  const idx = parts.lastIndexOf('ssot-gen');
  return idx > 0 ? parts[idx - 1] : '';
};

const isSsotYamlPath = (path) => /\.ssot\.ya?ml$/i.test(String(path || ''));

const ATLAS_ASYNC_RESOURCE_CACHES = {
  file: new Map(),
  ssot: new Map(),
};
const ATLAS_ASYNC_RESOURCE_TIMEOUT_MS = {
  file: 300000,
  ssot: 300000,
};

const scheduleAtlasPreviewWork = (fn, timeout = 900) => {
  let cancelled = false;
  const run = () => {
    if (!cancelled) fn();
  };
  if (typeof window !== 'undefined' && window.requestIdleCallback) {
    const id = window.requestIdleCallback(run, { timeout });
    return () => {
      cancelled = true;
      try { window.cancelIdleCallback && window.cancelIdleCallback(id); } catch (_) {}
    };
  }
  const id = setTimeout(run, 0);
  return () => {
    cancelled = true;
    clearTimeout(id);
  };
};

const emptyAtlasResource = (path = '') => ({
  path,
  body: '',
  size: 0,
  truncated: false,
  err: null,
  loading: false,
  loadedAt: 0,
});

const atlasResourceCache = (kind) =>
  ATLAS_ASYNC_RESOURCE_CACHES[kind] || ATLAS_ASYNC_RESOURCE_CACHES.file;

const isAtlasResourceTimeout = (data) =>
  /\bpreview timed out\b/i.test(String(data && data.err || ''));

const atlasResourceUrl = (kind, path) => {
  const encoded = encodeURIComponent(path);
  return kind === 'ssot'
    ? `/api/ssot?file=${encoded}`
    : `/api/file?path=${encoded}`;
};

const readAtlasAsyncResource = (kind, rawPath, force = false) => {
  const path = String(rawPath || '').trim();
  if (!path) return Promise.resolve(emptyAtlasResource(''));
  const cache = atlasResourceCache(kind);
  const current = cache.get(path);
  if (!force && current?.data && !isAtlasResourceTimeout(current.data)) return Promise.resolve(current.data);
  if (!force && current?.promise) return current.promise;
  if (force && current?.controller) {
    try { current.controller.abort(); } catch (_) {}
  }

  const token = Symbol(`${kind}:${path}`);
  const controller = new AbortController();
  const timeoutMs = ATLAS_ASYNC_RESOURCE_TIMEOUT_MS[kind] || ATLAS_ASYNC_RESOURCE_TIMEOUT_MS.file;
  let didTimeout = false;
  const timeout = setTimeout(() => {
    didTimeout = true;
    controller.abort();
  }, timeoutMs);
  const previous = current?.data || emptyAtlasResource(path);
  const promise = fetch(atlasResourceUrl(kind, path), {
    signal: controller.signal,
    cache: 'no-store',
  }).then(async r => {
    let d = {};
    try { d = await r.json(); }
    catch (_) { d = { error: r.statusText || `HTTP ${r.status}` }; }
    if (!r.ok && !d.error) d.error = r.statusText || `HTTP ${r.status}`;
    const err = d.error || null;
    const body = err && !d.content
      ? (kind === 'ssot' ? `# could not read ${path}\n# ${err}` : `// ${path}\n// (could not read: ${err})`)
      : (d.content || '');
    return {
      path,
      body,
      size: d.size || 0,
      truncated: !!d.truncated,
      err,
      loading: false,
      loadedAt: Date.now(),
    };
  }).catch(e => {
    const msg = e && e.name === 'AbortError'
      ? (didTimeout ? `${kind} preview timed out after ${Math.round(timeoutMs / 1000)}s` : `${kind} preview request cancelled`)
      : String(e);
    return {
      path,
      body: kind === 'ssot' ? `# fetch failed: ${msg}` : `// ${path}\n// fetch failed: ${msg}`,
      size: 0,
      truncated: false,
      err: msg,
      loading: false,
      loadedAt: Date.now(),
    };
  }).then(data => {
    clearTimeout(timeout);
    if (cache.get(path)?.token === token) {
      cache.set(path, { data });
      window.dispatchEvent(new CustomEvent('atlas-resource-loaded', { detail: { kind, path } }));
    }
    return data;
  });

  cache.set(path, { token, promise, data: previous, controller });
  window.dispatchEvent(new CustomEvent('atlas-resource-loading', { detail: { kind, path } }));
  return promise;
};

const cachedAtlasResource = (kind, path) => {
  const key = String(path || '').trim();
  if (!key) return emptyAtlasResource('');
  return atlasResourceCache(kind).get(key)?.data || emptyAtlasResource(key);
};

const useAtlasAsyncResource = (kind, path, options = {}) => {
  const key = String(path || '').trim();
  const versionKey = String(options.versionKey || '');
  const forceOnVersionChange = !!options.forceOnVersionChange;
  const requestSeq = React.useRef(0);
  const lastAutoLoad = React.useRef({ key, versionKey });
  const [state, setState] = React.useState(() => cachedAtlasResource(kind, key));

  const reload = React.useCallback((force = false) => {
    const currentKey = String(path || '').trim();
    const seq = requestSeq.current + 1;
    requestSeq.current = seq;
    if (!currentKey) {
      const empty = emptyAtlasResource('');
      setState(empty);
      return Promise.resolve(empty);
    }
    const cached = cachedAtlasResource(kind, currentKey);
    setState({ ...cached, path: currentKey, loading: true, err: force ? null : cached.err });
    return readAtlasAsyncResource(kind, currentKey, force).then(data => {
      if (requestSeq.current === seq) setState(data);
      return data;
    });
  }, [kind, path]);

  React.useEffect(() => {
    const previous = lastAutoLoad.current;
    const force = forceOnVersionChange && previous.key === key && previous.versionKey !== versionKey;
    lastAutoLoad.current = { key, versionKey };
    reload(force);
    return () => { requestSeq.current += 1; };
  }, [forceOnVersionChange, key, reload, versionKey]);

  React.useEffect(() => {
    if (!key) return undefined;
    const syncFromCache = (event) => {
      const detail = event?.detail || {};
      if (detail.kind !== kind || detail.path !== key) return;
      setState(cachedAtlasResource(kind, key));
    };
    const markLoading = (event) => {
      const detail = event?.detail || {};
      if (detail.kind !== kind || detail.path !== key) return;
      setState(prev => {
        const cached = cachedAtlasResource(kind, key);
        return {
          ...prev,
          ...cached,
          body: cached.body || prev.body || '',
          size: cached.size || prev.size || 0,
          path: key,
          loading: true,
          err: cached.err || prev.err || null,
        };
      });
    };
    window.addEventListener('atlas-resource-loaded', syncFromCache);
    window.addEventListener('atlas-resource-loading', markLoading);
    return () => {
      window.removeEventListener('atlas-resource-loaded', syncFromCache);
      window.removeEventListener('atlas-resource-loading', markLoading);
    };
  }, [kind, key]);

  const visibleState = state.path === key ? state : cachedAtlasResource(kind, key);
  return [visibleState, reload];
};

const workflowFromSession = (session) => {
  const parts = normalizeUiSession(session).split('/').filter(Boolean);
  const last = parts[parts.length - 1] || '';
  return (window.FLOW_STAGES || []).some(s => s.id === last) ? last : '';
};

const SessionSwitcher = ({ currentSession, streaming, onSwitch }) => {
  const [open, setOpen] = React.useState(false);
  const [options, setOptions] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [confirmId, setConfirmId] = React.useState(null);
  const wrapRef = React.useRef(null);

  const fetchOptions = React.useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/sessions');
      const d = await r.json();
      setOptions(Array.isArray(d.sessions) ? d.sessions : []);
    } catch (_) {
      setOptions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!open) return;
    fetchOptions();
    const onDocClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [open, fetchOptions]);

  const currentLabel = (currentSession || '').split('/')[0] || 'default';

  const handleSelect = (id) => {
    setOpen(false);
    if (id === currentLabel) return;
    if (streaming) {
      setConfirmId(id);
      return;
    }
    onSwitch(id);
  };

  return (
    <>
      <div ref={wrapRef} style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          title="Switch session"
          style={{
            background: 'transparent',
            border: '1px solid var(--line)',
            color: 'var(--fg-mute)',
            fontSize: 11,
            fontFamily: 'var(--mono)',
            padding: '2px 8px',
            borderRadius: 2,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <span style={{ color: 'var(--accent)' }}>◈</span>
          <span className="trunc" style={{ maxWidth: 140 }}>{currentLabel}</span>
          <span style={{ fontSize: 9 }}>{open ? '▲' : '▼'}</span>
        </button>
        {open && (
          <div style={{
            position: 'absolute', top: 'calc(100% + 4px)', left: 0, zIndex: 50,
            minWidth: 220, maxWidth: 300, maxHeight: 260, overflow: 'auto',
            background: 'var(--panel)', border: '1px solid var(--line)',
            borderRadius: 2, boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
          }}>
            <div style={{ padding: '6px 10px', borderBottom: '1px solid var(--line)', fontSize: 10, color: 'var(--fg-dim)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Switch session
            </div>
            {loading && (
              <div style={{ padding: '8px 10px', fontSize: 11, color: 'var(--fg-mute)' }}>Loading…</div>
            )}
            {!loading && options.length === 0 && (
              <div style={{ padding: '8px 10px', fontSize: 11, color: 'var(--fg-mute)' }}>No sessions</div>
            )}
            {options.map(s => (
              <div
                key={s.id}
                onClick={() => handleSelect(s.id)}
                style={{
                  padding: '6px 10px', fontSize: 11, cursor: 'pointer',
                  color: s.id === currentLabel ? 'var(--accent)' : 'var(--fg)',
                  background: s.id === currentLabel ? 'color-mix(in oklch, var(--accent) 10%, transparent)' : 'transparent',
                  borderBottom: '1px solid var(--line-2)',
                }}
                onMouseEnter={(e) => { if (s.id !== currentLabel) e.currentTarget.style.background = 'var(--bg-2)'; }}
                onMouseLeave={(e) => { if (s.id !== currentLabel) e.currentTarget.style.background = 'transparent'; }}
              >
                <div style={{ fontWeight: 500 }}>{s.title || s.id}</div>
                <div style={{ fontSize: 10, color: 'var(--fg-mute)', marginTop: 2 }}>{s.project_id || s.id}</div>
              </div>
            ))}
          </div>
        )}
      </div>
      {confirmId && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 100,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
        onClick={(e) => { if (e.target === e.currentTarget) setConfirmId(null); }}
        >
          <div style={{
            background: 'var(--panel)', border: '1px solid var(--line)',
            borderRadius: 4, padding: '20px 24px', maxWidth: 360, width: 'min(90vw, 360px)',
          }}>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: 'var(--fg)' }}>
              Agent is running
            </div>
            <div style={{ fontSize: 12, color: 'var(--fg-mute)', marginBottom: 16, lineHeight: 1.5 }}>
              Switching sessions will interrupt the current agent. Switch anyway?
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn" type="button" onClick={() => setConfirmId(null)} style={{ fontSize: 11 }}>
                Cancel
              </button>
              <button
                className="btn" type="button"
                onClick={() => { const id = confirmId; setConfirmId(null); onSwitch(id); }}
                style={{ fontSize: 11, background: 'var(--warn)', color: 'var(--bg)', borderColor: 'var(--warn)' }}
              >
                Switch
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const Workspace = ({ dir, onScreen, uiLang = 'ko' }) => {
  // Two-axis mode model:
  //   intent: 'normal' | 'plan'   (top-level — shift+tab to swap)
  //   workflow: null | 'ssot' | 'rtl_gen' | 'lint' | 'tb_gen'
  const [intent, setIntent] = React.useState('normal');
  const [workflow, setWorkflow] = React.useState(null);

  // Column widths (drag-resizable, persisted in localStorage).
  // 0 = collapsed; any positive width is clamped to [min, max].
  const [leftW,  setLeftW,  toggleLeft]  = useResizable(230, 'atlasLeftW',  160, 480, false);
  const [rightW, setRightW, toggleRight] = useResizable(360, 'atlasRightW', 260, 600);
  const [splitRightW, setSplitRightW] = useResizable(520, 'atlasSplitRightW', 300, 900, false);

  // File-tree sort mode — 'name' (alphabetical, dirs first; default) or
  // 'recent' (most recently modified first, regardless of dir/file).
  // Persisted across reloads.
  const [fileSort, setFileSort] = React.useState(() => {
    try { return localStorage.getItem('atlasFileSort') === 'recent' ? 'recent' : 'name'; }
    catch (_) { return 'name'; }
  });
  React.useEffect(() => {
    try { localStorage.setItem('atlasFileSort', fileSort); } catch (_) {}
  }, [fileSort]);

  // File-tree expand mode — 'shallow' (top level only at root) or
  // 'deep' (recursive descent up to backend max_depth). Toggling
  // 'expand all' / 'collapse all' triggers a refresh with the chosen
  // recursive flag. Persisted across reloads.
  const [fileExpand, setFileExpand] = React.useState(() => {
    try { return localStorage.getItem('atlasFileExpand') === 'deep' ? 'deep' : 'shallow'; }
    catch (_) { return 'shallow'; }
  });
  React.useEffect(() => {
    try { localStorage.setItem('atlasFileExpand', fileExpand); } catch (_) {}
    if (window.atlasData && window.atlasData.refreshFileTree) {
      window.atlasData.refreshFileTree(window.SCOPE_PATH || '', { recursive: true });
    }
  }, [fileExpand]);
  const [collapsedFileDirs, setCollapsedFileDirs] = React.useState(() => new Set());

  const NORMAL_FEED = [
    { kind: 'agent', text: 'Connected. Type a message and press Enter to talk to the agent.' },
  ];
  const PLAN_FEED = [
    { kind: 'agent', text: '**Plan mode** · read-only. The agent will analyze and propose without executing mutating tools. Use `apply` (or switch back to Normal) to run the plan.' },
  ];

  const resolveSession = React.useCallback((...candidates) => {
    for (const candidate of candidates) {
      try {
        const sid = normalizeUiSession(candidate || '');
        if (sid) return sid;
      } catch (_) {}
    }
    return 'default';
  }, []);

  const [feed, setFeed] = React.useState(NORMAL_FEED);
  const [activeSession, setActiveSession] = React.useState(() => {
    try {
      const sid = normalizeUiSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession')) || 'default';
      window.ACTIVE_SESSION = sid;
      try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
      return sid;
    } catch (_) {
      window.ACTIVE_SESSION = 'default';
      return 'default';
    }
  });
  const activeSessionRef = React.useRef(activeSession);
  const hydratedConversationSessionRef = React.useRef(activeSession);
  React.useEffect(() => { activeSessionRef.current = activeSession; }, [activeSession]);

  const refreshFeed = (newIntent /*, newWorkflow */) => {
    // Do not reset the conversation on mode/workflow switches. The
    // authoritative history lives in .session/<workflow>/conversation.json
    // and is hydrated asynchronously; wiping the browser feed here makes
    // reloads and /wf transitions look like the session was lost.
    setFeed(f => (f && f.length ? f : (newIntent === 'plan' ? PLAN_FEED : NORMAL_FEED)));
  };

  const activateSession = React.useCallback((scopePath, wf) => {
    const rawSid = (window.atlasData && window.atlasData.sessionFor)
      ? window.atlasData.sessionFor(scopePath || window.SCOPE_PATH || '', wf || '')
      : 'default';
    const sid = resolveSession(rawSid);
    window.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (window.atlasData && window.atlasData.refreshSessionState) {
      window.atlasData.refreshSessionState(sid);
    }
    return sid;
  }, []);

  const sendPrompt = React.useCallback((text, sessionOverride) => {
    if (window.backend) {
      const session = resolveSession(
        sessionOverride,
        window.ACTIVE_SESSION,
        activeSessionRef.current,
        activeSession,
      );
      // crypto.randomUUID is secure-context only (localhost / https).
      // Accessing it from http://<lan-ip>/ throws — fall back to
      // getRandomValues, which IS available in non-secure contexts.
      let msg_id;
      try {
        msg_id = window.crypto.randomUUID();
      } catch (_) {
        const b = new Uint8Array(16);
        window.crypto.getRandomValues(b);
        b[6] = (b[6] & 0x0f) | 0x40;
        b[8] = (b[8] & 0x3f) | 0x80;
        const h = Array.from(b, x => x.toString(16).padStart(2, '0'));
        msg_id = `${h.slice(0,4).join('')}-${h.slice(4,6).join('')}-${h.slice(6,8).join('')}-${h.slice(8,10).join('')}-${h.slice(10,16).join('')}`;
      }
      window.backend.send({
        type: 'prompt',
        msg_id,
        text,
        session,
        ui_lang: window.ATLAS_UI_LANG || uiLang,
      });
    }
  }, [activeSession, resolveSession, uiLang]);

  const switchToDefaultSession = React.useCallback(() => {
    const sid = (window.atlasData && window.atlasData.sessionFor)
      ? (window.atlasData.sessionFor('', '') || 'default')
      : 'default';
    window.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (window.atlasData && window.atlasData.refreshSessionState) {
      window.atlasData.refreshSessionState(sid);
    }
    return sid;
  }, []);

  const handleSwitchSession = React.useCallback(async (sessionId) => {
    const current = normalizeUiSession(activeSession || window.ACTIVE_SESSION || '');
    const suffix = current.split('/').slice(1).join('/');
    const newNamespace = suffix ? `${sessionId}/${suffix}` : sessionId;

    try {
      await fetch('/api/sessions/' + encodeURIComponent(sessionId) + '/activate', { method: 'POST' });
    } catch (_) {}

    window.history.replaceState(null, '', '/?session_id=' + encodeURIComponent(sessionId));

    if (window.backend) {
      if (window.backend.disconnect) window.backend.disconnect();
      if (window.backend.connect) window.backend.connect(newNamespace);
    }

    window.ACTIVE_SESSION = newNamespace;
    setActiveSession(newNamespace);
    try { localStorage.setItem('atlasActiveSession', newNamespace); } catch (_) {}

    setStreaming(false);
    streamBufferRef.current = '';
    setStreamText('');

    if (window.atlasData && window.atlasData.refreshSessionState) {
      window.atlasData.refreshSessionState(newNamespace);
    }

    window.dispatchEvent(new CustomEvent('atlas-session-switched', { detail: { sessionId, namespace: newNamespace } }));
  }, [activeSession]);

  const switchIntent = (i) => {
    setIntent(i);
    refreshFeed(i, workflow);
    // Tell the BACKEND about the mode swap — local React state alone
    // doesn't change the agent's behaviour. /plan flips agent_mode to
    // 'plan' (no mutating tools); /mode normal flips it back.
    if (window.backend) {
      const cmd = i === 'plan' ? '/plan' : '/mode normal';
      sendPrompt(cmd);
    }
  };
  const switchWorkflow = async (w) => {
    // Click a workflow chip → activate the backend workspace through the
    // canonical session API. The API path performs the workspace setup
    // synchronously; stale queued `/wf` prompts are avoided because they
    // can land late during fast workflow sweeps.
    const next = workflow === w ? null : w;
    const runningNow = streamingRef.current || window.ATLAS_AGENT_RUNNING === true;
    if (runningNow) {
      const label = next || 'default';
      if (!window.confirm(`Agent is running. Stop it and switch workflow to "${label}"?`)) return;
      try { if (window.backend) window.backend.send({ type: 'stop' }); } catch (_) {}
      try {
        fetch('/api/control/stop', {
          method: 'POST', cache: 'no-store', keepalive: true,
        }).catch(() => {});
      } catch (_) {}
    }
    setStreaming(false);
    try {
      window.ATLAS_AGENT_RUNNING = false;
      window.dispatchEvent(new CustomEvent('atlas-agent-running', { detail: { running: false } }));
    } catch (_) {}
    setWorkflow(next);
    window.CONTEXT = Object.assign({}, window.CONTEXT || {}, { workspace: next || '' });
    refreshFeed(intent, next);
    const sid = activateSession(window.SCOPE_PATH || '', next || '');
    const parts = (activeSession || window.ACTIVE_SESSION || '').split('/');
    const owner = parts[0] || 'default';
    const ip = window.SCOPE_PATH || parts[1] || 'default';
    let activated = false;
    try {
      const res = await fetch('/api/session/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: owner,
          ip: ip,
          workflow: next || 'default',
        }),
      });
      activated = !!(res && res.ok);
    } catch (_) {}
    if (window.backend) {
      if (window.backend.disconnect) window.backend.disconnect();
      if (window.backend.connect) window.backend.connect(sid);
      if (!activated) sendPrompt(next ? `/wf ${next}` : '/workflow default', sid);
    }
  };
  const [input, setInput] = React.useState('');

  // Listen for fold/drag-select comment events from PreviewPane so a
  // click on a fold's 💬 button (or "Comment selection" after a line
  // drag) prefills the chat input with `@<path> L<lo>-L<hi> (label)`
  // and focuses it. The dispatch site is the FoldablePane below; this
  // is the central wire-up so any preview surface can broadcast.
  React.useEffect(() => {
    const handler = (ev) => {
      try {
        const d = ev.detail || {};
        const path  = String(d.path || '');
        const lo    = Number(d.lineStart || d.lo || 0);
        const hi    = Number(d.lineEnd   || d.hi || 0);
        const label = String(d.label || '').trim();
        const text  = String(d.text || '');
        const lang  = String(d.lang || '');
        if (!path || !lo || !hi) return;
        const labelStr = label ? ` (${label})` : '';
        // Embed the actual source slice as a fenced code block so the
        // LLM doesn't need to read_file again. Lang fence (```sv,
        // ```yaml, ```json) gives the model a syntax hint.
        let block = '';
        if (text) {
          const fence = lang || '';
          block = `\n\n\`\`\`${fence}\n${text}\n\`\`\`\n\n`;
        }
        const next = `@${path} L${lo}-${hi}${labelStr}${block || '\n\n'}`;
        setInput(next);
        // After React paints the new value into the textarea, trigger
        // the same auto-grow that onChange does so the multi-line
        // prefill is fully visible (rows={1} otherwise clips it).
        // Two RAFs because React schedules its render via the first
        // and the layout settles in the second.
        requestAnimationFrame(() => requestAnimationFrame(() => {
          const el = inputRef.current;
          if (!el) return;
          el.focus();
          try { el.selectionStart = el.selectionEnd = el.value.length; } catch (_) {}
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 192) + 'px';
        }));
      } catch (_) {}
    };
    window.addEventListener('atlas-fold-comment', handler);
    return () => window.removeEventListener('atlas-fold-comment', handler);
  }, []);

  const [inputHistory, setInputHistory] = React.useState(() => {
    try {
      const raw = localStorage.getItem('atlasInputHistory');
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed)
        ? parsed.filter(x => typeof x === 'string' && x.trim()).slice(-INPUT_HISTORY_LIMIT)
        : [];
    } catch (_) {
      return [];
    }
  });
  const inputHistoryIndexRef = React.useRef(null);
  const inputHistoryDraftRef = React.useRef('');
  const [showSlash, setShowSlash] = React.useState(false);
  const [slashSel, setSlashSel] = React.useState(0);
  const [streaming, setStreaming] = React.useState(false);
  const streamingRef = React.useRef(false);
  const streamBufferRef = React.useRef('');
  React.useEffect(() => { streamingRef.current = streaming; }, [streaming]);
  React.useEffect(() => {
    try {
      window.ATLAS_AGENT_RUNNING = !!streaming;
      window.dispatchEvent(new CustomEvent('atlas-agent-running', {
        detail: { running: !!streaming },
      }));
    } catch (_) {}
  }, [streaming]);
  const [backendState, setBackendState] = React.useState(() => {
    if (!window.backend) return 'missing';
    return window.backend.getConnectionState ? window.backend.getConnectionState() : 'connecting';
  });
  const [peerCount, setPeerCount] = React.useState(1);
  const [streamText, setStreamText] = React.useState('');
  const [openFile, setOpenFile] = React.useState(null);
  const [rightTab, setRightTab] = React.useState('todo'); // todo | progress | git
  // Main column tab: 'chat' shows the conversation feed; 'preview' shows
  // the contents of the file at previewPath with syntax highlighting;
  // 'split' keeps chat and preview visible side-by-side.
  // 'ssot' shows a reviewer-friendly section-by-section SSOT view.
  // 'sim_summary' / 'debug' / 'coverage' / 'workflow_report' are workflow-specific first tabs.
  // 'qa' is the dedicated question-answer pane. 'checklist' is the SSOT
  // readiness/checklist pane for ssot-gen, kept separate from Q&A.
  // Double-clicking a file in the left tree sets previewPath + flips tab.
  const [mainTab, setMainTab] = React.useState('split');    // chat | ssot | qa | checklist | split | preview | sim_summary | debug | coverage | workflow_report
  const [previewPath, setPreviewPath] = React.useState(() => {
    try {
      const saved = localStorage.getItem('atlasPreviewPath');
      return saved ? String(saved) : null;
    } catch (_) {
      return null;
    }
  });
  // Git diff display: when the GitPanel emits atlas-git-show with a
  // commit sha, the center pane swaps in GitDiffPane to render the
  // unified diff instead of the file preview. Setting it back to null
  // (Esc / "back to preview") restores the regular preview flow.
  const [gitShow, setGitShow] = React.useState(null); // {sha, ip, subject} | null
  React.useEffect(() => {
    const onShow = (ev) => {
      const d = ev && ev.detail || {};
      if (!d.sha) return;
      setGitShow({ sha: d.sha, ip: d.ip || '', subject: d.subject || '' });
      setMainTab(t => (t === 'chat' || t === 'qa' || t === 'checklist') ? 'split' : t);
    };
    window.addEventListener('atlas-git-show', onShow);
    return () => window.removeEventListener('atlas-git-show', onShow);
  }, []);
  // Center layout: 'classic' (chat with inline ask_user) or 'tabbed'
  // (Chat / Preview / Q&A tab strip with auto-switch). Comes from the
  // server hello payload (driven by ATLAS_CENTER_LAYOUT in .config).
  const [centerLayout, setCenterLayout] = React.useState('classic');
  const [chatFeedSummary, setChatFeedSummary] = React.useState(
    () => window.ATLAS_CHAT_FEED_SUMMARY !== false
  );
  // qaState is keyed by flow_id. Dynamic flows are added on-the-fly
  // when the agent emits an ask_user event over the WS.
  const [qaState, setQaState] = React.useState({});
  const qaStateRef = React.useRef(qaState);
  React.useEffect(() => { qaStateRef.current = qaState; }, [qaState]);
  // qaHistory: every submitted ask_user round-trip, newest first.
  // Each entry is {flowId, ts, session, ip, workflow, source, items: [{
  //   question, kind, selected: [{id,label}], custom
  // }, ...]}. It is persisted per session+IP; the legacy global
  // localStorage key mixed old GPIO answers into unrelated IPs.
  const [qaHistory, setQaHistory] = React.useState([]);
  const [ssotApproval, setSsotApproval] = React.useState(null);
  const [ssotQa, setSsotQa] = React.useState(null);
  const [ssotQaSessions, setSsotQaSessions] = React.useState([]);

  const replaceInputHistory = React.useCallback((items) => {
    const cleaned = (Array.isArray(items) ? items : [])
      .filter(x => typeof x === 'string' && x.trim())
      .slice(-INPUT_HISTORY_LIMIT);
    setInputHistory(cleaned);
    try { localStorage.setItem('atlasInputHistory', JSON.stringify(cleaned)); } catch (_) {}
  }, []);

  React.useEffect(() => {
    let alive = true;
    fetch('/api/input-history?limit=' + INPUT_HISTORY_LIMIT, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!alive || !d || !Array.isArray(d.history)) return;
        replaceInputHistory(d.history);
      })
      .catch(() => {});
    return () => { alive = false; };
  }, [replaceInputHistory]);

  const recordInputHistory = React.useCallback((raw) => {
    const text = String(raw || '').trim();
    if (!text) return;
    inputHistoryIndexRef.current = null;
    inputHistoryDraftRef.current = '';
    setInputHistory(prev => {
      const next = [...prev, text].slice(-INPUT_HISTORY_LIMIT);
      try { localStorage.setItem('atlasInputHistory', JSON.stringify(next)); } catch (_) {}
      return next;
    });
    fetch('/api/input-history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }).catch(() => {});
  }, []);

  const currentSession = React.useMemo(
    () => resolveSession(activeSession, window.ACTIVE_SESSION),
    [activeSession, resolveSession],
  );

  const activeIp = (() => {
    const parts = normalizeUiSession(currentSession || window.ACTIVE_SESSION).split('/').filter(Boolean);
    if (parts.length >= 3 && parts[1] && parts[1] !== 'default') return parts[1];
    const explicit = String(window.ACTIVE_IP || '').trim();
    if (explicit && explicit !== 'default') return explicit;
    const scoped = String(window.SCOPE_PATH || '').split('/').filter(Boolean).pop() || '';
    return /^[A-Za-z][A-Za-z0-9_]*$/.test(scoped) && scoped !== 'default' ? scoped : '';
  })();

  const activeSsotIp = React.useCallback(() => {
    if (activeIp) return activeIp;
    const fromSession = ssotIpFromSession(currentSession || window.ACTIVE_SESSION);
    if (fromSession) return fromSession;
    const scoped = String(window.SCOPE_PATH || '').split('/').filter(Boolean).pop() || '';
    return /^[A-Za-z][A-Za-z0-9_]*$/.test(scoped) ? scoped : '';
  }, [activeIp, currentSession]);

  const qaHistoryScope = React.useMemo(() => {
    const session = normalizeUiSession(currentSession || window.ACTIVE_SESSION || '');
    const ip = ssotIpFromSession(session) || activeSsotIp() || 'default';
    const safeSession = session || 'default';
    const safeIp = ip || 'default';
    return {
      session,
      ip,
      key: `${QA_HISTORY_STORAGE_PREFIX}${safeSession}:${safeIp}`,
    };
  }, [activeSsotIp, currentSession]);

  const qaHistoryMatchesScope = React.useCallback((entry) => {
    const entrySession = normalizeUiSession(entry?.session || '');
    const entryIp = String(entry?.ip || '').trim();
    const scopeSession = qaHistoryScope.session;
    const scopeIp = qaHistoryScope.ip;
    const hasEntryScope = !!entrySession || !!entryIp;
    if (entrySession && scopeSession && entrySession !== scopeSession) return false;
    if (entryIp && scopeIp && entryIp !== scopeIp) return false;
    if (!hasEntryScope && (scopeSession || (scopeIp && scopeIp !== 'default'))) return false;
    return true;
  }, [qaHistoryScope.ip, qaHistoryScope.session]);

  React.useEffect(() => {
    try {
      const raw = localStorage.getItem(qaHistoryScope.key);
      const parsed = raw ? JSON.parse(raw) : null;
      if (Array.isArray(parsed)) {
        setQaHistory(parsed.filter(qaHistoryMatchesScope).slice(0, QA_HISTORY_LIMIT));
        return;
      }
      const legacyRaw = localStorage.getItem(QA_HISTORY_LEGACY_STORAGE_KEY);
      const legacyParsed = legacyRaw ? JSON.parse(legacyRaw) : [];
      const migrated = Array.isArray(legacyParsed)
        ? legacyParsed.filter(qaHistoryMatchesScope).slice(0, QA_HISTORY_LIMIT)
        : [];
      if (migrated.length) {
        localStorage.setItem(qaHistoryScope.key, JSON.stringify(migrated));
      }
      setQaHistory(migrated);
    } catch (_) {
      setQaHistory([]);
    }
  }, [qaHistoryMatchesScope, qaHistoryScope.key]);

  React.useEffect(() => {
    try {
      const scoped = qaHistory.filter(qaHistoryMatchesScope).slice(0, QA_HISTORY_LIMIT);
      if (scoped.length) {
        localStorage.setItem(qaHistoryScope.key, JSON.stringify(scoped));
      } else {
        localStorage.removeItem(qaHistoryScope.key);
      }
    } catch (_) {}
  }, [qaHistory, qaHistoryMatchesScope, qaHistoryScope.key]);

  const visibleQaHistory = React.useMemo(
    () => qaHistory.filter(qaHistoryMatchesScope).slice(0, QA_HISTORY_LIMIT),
    [qaHistory, qaHistoryMatchesScope],
  );

  const clearQaHistory = React.useCallback(() => {
    setQaHistory([]);
    try { localStorage.removeItem(qaHistoryScope.key); } catch (_) {}
  }, [qaHistoryScope.key]);

  // Single-source-of-truth pivot: whenever the canonical (session_id, ip,
  // workflow) triple resolves to a real IP, point the preview pane at
  // that IP's SSOT yaml. Without this, /new-ip <new> leaves the preview
  // pinned to the previous IP's file and the right pane disagrees with
  // the chat about what we are actually editing. Skips overwriting paths
  // the user explicitly chose in the file tree (anything outside the
  // <ip>/yaml folder is preserved).
  React.useEffect(() => {
    const ip = activeSsotIp();
    if (!ip) return;
    const canonical = `${ip}/yaml/${ip}.ssot.yaml`;
    if (previewPath === canonical) return;
    const cur = String(previewPath || '');
    const looksLikeStaleSsot = !cur || /\/ssot\.yaml$/i.test(cur) || /^[A-Za-z0-9_]+\/yaml\/[^/]+\.ssot\.yaml$/.test(cur);
    if (looksLikeStaleSsot) {
      setPreviewPath(canonical);
    }
  }, [activeSsotIp, previewPath]);

  // Inline-code chip click handlers — wired up from
  // _processInlineChips() in workspace.jsx-level. Path chips dispatch
  // 'atlas-chip-open', IP-name chips dispatch 'atlas-chip-ip'. Both
  // events bubble up to here so the user can pivot the preview / IP
  // dropdown straight from any markdown chip in the chat feed.
  React.useEffect(() => {
    const onPath = (ev) => {
      const path = String(ev?.detail?.path || '').trim();
      if (!path) return;
      setPreviewPath(path);
      try { localStorage.setItem('atlasPreviewPath', path); } catch (_) {}
      // Snap to split-or-full view so the file is actually visible.
      setMainTab(t => (t === 'split' || t === 'preview') ? t : 'split');
    };
    const onIp = (ev) => {
      const ip = String(ev?.detail?.ip || '').trim();
      if (!ip) return;
      // Only switch when the IP token actually maps to a workspace dir.
      const known = (window.IP_OPTIONS || []).map(s => String(s).toLowerCase());
      if (known.length && !known.includes(ip.toLowerCase())) return;
      if (window.atlasData && typeof window.atlasData.setScopePath === 'function') {
        window.atlasData.setScopePath(ip);
      }
      setPreviewPath(`${ip}/yaml/${ip}.ssot.yaml`);
    };
    window.addEventListener('atlas-chip-open', onPath);
    window.addEventListener('atlas-chip-ip', onIp);
    return () => {
      window.removeEventListener('atlas-chip-open', onPath);
      window.removeEventListener('atlas-chip-ip', onIp);
    };
  }, []);

  const refreshSsotQa = React.useCallback(async (sessionOverride) => {
    const session = normalizeUiSession(sessionOverride || currentSession || window.ACTIVE_SESSION || '');
    const ip = ssotIpFromSession(session) || activeSsotIp();
    if (!ip) {
      setSsotQa({ ip: '', toc: [], sections: [], summary: { total: 0, approved: 0, pending: 0 } });
      return null;
    }
    try {
      const qs = new URLSearchParams({ ip });
      if (session) qs.set('session', session);
      // cache: 'no-store' is required — without it the browser will
      // serve a stale qa.json view after /api/ssot/qa/answer flips an
      // entry pending→approved, so the user clicks "refresh" and sees
      // no change. Mirrors refreshSsotQaSessions which already opts
      // out of HTTP cache for the same reason.
      const r = await fetch('/api/ssot/qa?' + qs.toString(), { cache: 'no-store' });
      if (!r.ok) return null;
      const d = await r.json();
      setSsotQa(d);
      return d;
    } catch (_) {
      return null;
    }
  }, [activeSsotIp, currentSession]);

  const refreshSsotQaSessions = React.useCallback(async () => {
    try {
      const r = await fetch('/api/ssot/qa/sessions', { cache: 'no-store' });
      if (!r.ok) return null;
      const d = await r.json();
      const rows = Array.isArray(d.sessions) ? d.sessions : [];
      setSsotQaSessions(rows);
      return rows;
    } catch (_) {
      return null;
    }
  }, []);

  React.useEffect(() => {
    if (workflow !== 'ssot-gen') return;
    const ip = activeSsotIp();
    if (!ip) return;
    const loadedIp = String(ssotQa?.ip || '').trim();
    const session = normalizeUiSession(currentSession || window.ACTIVE_SESSION || '');
    const loadedSession = normalizeUiSession(ssotQa?.session || '');
    const sameSession = !session || !loadedSession || session === loadedSession;
    if (loadedIp === ip && sameSession) return;
    refreshSsotQa(session);
    refreshSsotQaSessions();
  }, [
    activeSsotIp,
    currentSession,
    refreshSsotQa,
    refreshSsotQaSessions,
    ssotQa?.ip,
    ssotQa?.session,
    workflow,
  ]);

  const activateSsotQaSession = React.useCallback((row) => {
    const sid = normalizeUiSession(row?.session || '');
    if (!sid) return;
    window.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (row?.ip && window.atlasData?.setScopePath) {
      window.atlasData.setScopePath(row.ip);
    }
    if (window.atlasData?.refreshSessionState) {
      window.atlasData.refreshSessionState(sid);
    }
    setWorkflow('ssot-gen');
    refreshSsotQa(sid);
  }, [refreshSsotQa]);

  const flowMatchesCurrentSession = React.useCallback((flowId, eventSession) => {
    const flow = window.QA_FLOWS && window.QA_FLOWS[flowId];
    const flowSession = normalizeUiSession(eventSession || (flow && flow.session) || '');
    const active = normalizeUiSession(currentSession || window.ACTIVE_SESSION || '');
    if (!flowSession || !active || flowSession === active) return true;
    const flowParts = flowSession.split('/').filter(Boolean);
    const activeParts = active.split('/').filter(Boolean);
    const minLen = Math.min(flowParts.length, activeParts.length);
    if (minLen < 2) return false;
    return flowParts.slice(-minLen).join('/') === activeParts.slice(-minLen).join('/');
  }, [currentSession]);

  const activateAskUserSession = React.useCallback((session, ip, eventWorkflow) => {
    const sid = normalizeUiSession(session || '');
    if (!sid) return;
    if (flowMatchesCurrentSession('', sid)) return;
    window.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (ip && window.atlasData?.setScopePath) {
      window.atlasData.setScopePath(ip);
    }
    if (eventWorkflow) {
      setWorkflow(eventWorkflow);
    }
    if (window.atlasData?.refreshSessionState) {
      window.atlasData.refreshSessionState(sid, false);
    }
  }, [flowMatchesCurrentSession]);

  // Force a re-render when the live data layer (data.jsx) refreshes
  // FILE_TREE / TODOS / SSOT_FILES so dependent panels show fresh data.
  const [, bumpRender] = React.useReducer(x => x + 1, 0);
  React.useEffect(() => {
    const h = () => bumpRender();
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  React.useEffect(() => {
    refreshSsotQa();
    refreshSsotQaSessions();
    const h = (ev) => {
      if (!ev.detail || ['SESSION_STATE', 'SCOPE_PATH', 'SSOT_QA', 'SSOT_FILES'].includes(ev.detail)) {
        refreshSsotQa();
        refreshSsotQaSessions();
      }
    };
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, [refreshSsotQa, refreshSsotQaSessions]);

  React.useEffect(() => {
    const onData = (ev) => {
      if (ev.detail === 'CONTEXT') {
        setChatFeedSummary(window.ATLAS_CHAT_FEED_SUMMARY !== false);
      }
      if (ev.detail === 'CONTEXT' || ev.detail === 'FLOW_STAGES') {
        const backendWorkflow = (window.CONTEXT && window.CONTEXT.workspace) || '';
        const activeWorkflow = workflowFromSession(window.ACTIVE_SESSION || '');
        const nextWorkflow = activeWorkflow || backendWorkflow;
        const known = (window.FLOW_STAGES || []).some(s => s.id === nextWorkflow);
        if (!nextWorkflow || nextWorkflow === 'default') {
          setWorkflow(null);
        } else if (known) {
          setWorkflow(nextWorkflow);
        }
      }
      if (ev.detail === 'SCOPE_PATH') {
        const activeWorkflow = workflowFromSession(window.ACTIVE_SESSION || '');
        activateSession(window.SCOPE_PATH || '', activeWorkflow || workflow || (window.CONTEXT && window.CONTEXT.workspace) || '');
      }
    };
    onData({ detail: 'CONTEXT' });
    window.addEventListener('atlas-data-changed', onData);
    return () => window.removeEventListener('atlas-data-changed', onData);
  }, [activateSession, workflow]);

  React.useEffect(() => {
    const onSessionSwitched = (ev) => {
      const detail = ev?.detail || {};
      const sid = normalizeUiSession(detail.namespace || detail.session || '');
      if (!sid) return;
      window.ACTIVE_SESSION = sid;
      activeSessionRef.current = sid;
      setActiveSession(sid);
      try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
      const nextWorkflow = workflowFromSession(sid);
      setWorkflow(nextWorkflow && nextWorkflow !== 'default' ? nextWorkflow : null);
      if (window.atlasData && window.atlasData.refreshSessionState) {
        window.atlasData.refreshSessionState(sid, false);
      }
    };
    window.addEventListener('atlas-session-switched', onSessionSwitched);
    return () => window.removeEventListener('atlas-session-switched', onSessionSwitched);
  }, []);

  // Hydrate the chat feed from the active .session/<scope>/<workflow>
  // conversation.json. data.jsx fires 'atlas-conversation-loaded' after
  // active session changes so screen switches do not erase chat history.
  React.useEffect(() => {
    const placeholderTexts = new Set([
      NORMAL_FEED[0]?.text || '',
      PLAN_FEED[0]?.text || '',
    ]);
    const hasLiveFeedEntries = (items) => Array.isArray(items) && items.some(e => {
      if (!e || typeof e !== 'object') return false;
      if (e.kind === 'turn_end') return false;
      if (e.kind === 'agent') {
        const text = String(e.text || '');
        return !!text.trim() && !placeholderTexts.has(text);
      }
      return ['user', 'qcard', 'action', 'obs', 'ssot_approval'].includes(e.kind);
    });
    const hasPendingAskUser = () => {
      const state = qaStateRef.current || {};
      return Object.values(state).some(st => st && !st.submitted);
    };
    const onConvLoaded = (ev) => {
      const msgs = (ev.detail && ev.detail.messages) || [];
      const session = normalizeUiSession(ev.detail && ev.detail.session || '');
      if (session) setActiveSession(session);
      if (streamingRef.current || (streamBufferRef.current || '').trim()) {
        return;
      }
      const newFeed = [];
      for (const m of msgs) {
        const role = m.role;
        const content = typeof m.content === 'string' ? m.content
          : Array.isArray(m.content) ? m.content.map(c => c.text || '').join('')
          : '';
        if (role === 'user' && content) {
          newFeed.push({ kind: 'user', text: content });
        } else if (role === 'assistant') {
          // assistant message may have content + tool_calls
          if (content && content.trim()) {
            newFeed.push({ kind: 'agent', text: content });
          }
          if (Array.isArray(m.tool_calls)) {
            for (const tc of m.tool_calls) {
              const fn = (tc.function && tc.function.name) || tc.name || '?';
              const args = (tc.function && tc.function.arguments) || tc.arguments || '';
              const argsShort = typeof args === 'string'
                ? args.slice(0, 120)
                : JSON.stringify(args).slice(0, 120);
              // Stamp `tool` so the render-time pre-pass can pair this
              // hydrated action with the next 'tool'-role obs into a
              // single ToolCard (matching the live shape).
              newFeed.push({ kind: 'action', text: `▶ ${fn} ${argsShort}`, tool: fn, args: argsShort });
            }
          }
        } else if (role === 'tool' && content) {
          newFeed.push({
            kind: 'obs',
            text: content.slice(0, 8000),
            tool: m.name || '',
            truncated: content.length > 8000,
          });
        }
      }
      // Drop a turn-end divider so the user can tell where the
      // hydrated history ends and live tokens begin.
      if (newFeed.length) {
        newFeed.push({
          kind: 'turn_end',
          text: `↓ live (${session ? `.session/${session}` : 'session history'} above) ↓`,
        });
      }
      setFeed(prev => {
        const prevSession = normalizeUiSession(hydratedConversationSessionRef.current || '');
        const namespaceChanged = !!(session && prevSession && session !== prevSession);
        const sameActiveSession = !session || session === normalizeUiSession(window.ACTIVE_SESSION || activeSessionRef.current || '');
        // ask_user can trigger a session-state refresh before the agent
        // flushes conversation.json. That empty same-session snapshot
        // should not erase the live chat or the pending Q&A card.
        // Real namespace switches still replace the feed below.
        const lateEmptySnapshot = (
          sameActiveSession
          && !namespaceChanged
          && newFeed.length === 0
          && (hasLiveFeedEntries(prev) || hasPendingAskUser())
        );
        if (lateEmptySnapshot) {
          return prev;
        }
        if (session) hydratedConversationSessionRef.current = session;
        return newFeed;
      });
    };
    window.addEventListener('atlas-conversation-loaded', onConvLoaded);
    if (window.ATLAS_LAST_CONVERSATION) {
      onConvLoaded({ detail: window.ATLAS_LAST_CONVERSATION });
    }
    return () => window.removeEventListener('atlas-conversation-loaded', onConvLoaded);
  }, []);

  const inputRef = React.useRef(null);
  const feedRef = React.useRef(null);

  // Derived: the latest unsubmitted qcard. Live ask_user normally appends
  // a qcard to the chat feed, but session-history hydration can replace
  // the feed after a reconnect. Keep Q&A visible from qaState as the
  // authoritative pending-flow state.
  const pendingQcard = React.useMemo(() => {
    for (let i = feed.length - 1; i >= 0; i--) {
      const e = feed[i];
      if (e.kind === 'qcard' && !qaState[e.flowId]?.submitted && flowMatchesCurrentSession(e.flowId)) return e;
    }
    const flowIds = Object.keys(qaState || {});
    for (let i = flowIds.length - 1; i >= 0; i--) {
      const flowId = flowIds[i];
      if (!qaState[flowId]?.submitted && window.QA_FLOWS && window.QA_FLOWS[flowId] && flowMatchesCurrentSession(flowId)) {
        return { kind: 'qcard', flowId, dynamic: true };
      }
    }
    return null;
  }, [feed, qaState, flowMatchesCurrentSession]);

  // Tabbed center layout — auto-switch to Q&A tab when ask_user fires,
  // and back to chat after the user submits.  Classic layout ignores
  // mainTab='qa' entirely (still routes ask_user inline below the feed).
  const _qcardActiveFlow = pendingQcard?.flowId || null;
  const _qcardSubmitted = !!(pendingQcard && qaState[pendingQcard.flowId]?.submitted);
  React.useEffect(() => {
    if (centerLayout !== 'tabbed') return;
    if (_qcardActiveFlow && !_qcardSubmitted && mainTab !== 'qa') {
      setMainTab('qa');
    } else if (!_qcardActiveFlow && mainTab === 'qa' && workflow !== 'ssot-gen') {
      setMainTab('chat');
    }
  }, [centerLayout, _qcardActiveFlow, _qcardSubmitted, workflow]);

  // Keyboard navigation cursor for the ask_user inline form.
  // Index space: 0..opts.length-1 = option rows, opts.length = custom-text row,
  // opts.length+1 = Submit, opts.length+2 = "Chat about this".
  const [askSel, setAskSel] = React.useState(0);
  const pendingQcardActiveTab = pendingQcard
    ? (qaState[pendingQcard.flowId]?.active || 0)
    : 0;
  const showQaTab = centerLayout === 'tabbed' || workflow === 'ssot-gen' || !!pendingQcard;
  const showSsotChecklistTab = workflow === 'ssot-gen';
  const showSsotTab = workflow === 'ssot-gen' || (window.SSOT_FILES || []).length > 0 || isSsotYamlPath(previewPath);
  const showSimSummaryTab = workflow === 'sim_debug';
  const showDebugTab = workflow === 'sim_debug';
  const showCoverageTab = workflow === 'coverage';
  const workflowReportMeta = WORKFLOW_REPORT_TABS[workflow] || null;
  const showWorkflowReportTab = !!workflowReportMeta;
  const ssotQaBoardData = React.useMemo(() => {
    if (ssotQa?.ip) return ssotQa;
    const ip = activeSsotIp();
    if (!ip) return ssotQa;
    return {
      ip,
      workflow: 'ssot-gen',
      session: currentSession || window.ACTIVE_SESSION || '',
      toc: [],
      sections: [],
      summary: { total: 0, approved: 0, pending: 0 },
      requirements: { total: 0, filled: 0, missing: 0, items: [], missing_keys: [] },
    };
  }, [activeSsotIp, currentSession, ssotQa]);
  const lastWorkflowTabRef = React.useRef(null);
  React.useEffect(() => {
    if (lastWorkflowTabRef.current === workflow) return;
    lastWorkflowTabRef.current = workflow;
    if (workflow === 'sim_debug') {
      setMainTab('sim_summary');
      return;
    }
    if (workflow === 'coverage') {
      setMainTab(WORKFLOW_REPORT_TABS[workflow] ? 'workflow_report' : 'coverage');
      return;
    }
    if (workflow === 'ssot-gen') {
      setMainTab('qa');
      return;
    }
    if (WORKFLOW_REPORT_TABS[workflow]) {
      setMainTab('workflow_report');
      return;
    }
    setMainTab(t => (t === 'sim_summary' || t === 'debug' || t === 'coverage' || t === 'workflow_report' || t === 'checklist') ? 'split' : t);
  }, [workflow]);
  React.useEffect(() => { setAskSel(0); }, [pendingQcard?.flowId, pendingQcardActiveTab]);

  // Auto-focus the ask_user prompt area when one opens
  React.useEffect(() => {
    if (pendingQcard) {
      setTimeout(() => {
        const el = document.querySelector('.ask-prompt');
        el?.focus();
      }, 30);
    }
  }, [pendingQcard?.flowId]);

  // ── @ file completion (Python-style, one path segment at a time) ──
  // Find a trailing "@<query>" token (anywhere in the input). The
  // query is everything after the LAST `@` to the end of the line.
  // We split the query into (parentDir, filter): everything up to the
  // last '/' is the directory the user is browsing; everything after
  // is the prefix to match against entries in that directory.
  //
  //   "@"               → parent='',         filter=''       → list project root
  //   "@workflow/"      → parent='workflow', filter=''       → list workflow/
  //   "@workflow/ssot"  → parent='workflow', filter='ssot'   → workflow/ filtered by 'ssot'
  //   "@a/b/c"          → parent='a/b',      filter='c'      → a/b/ filtered by 'c'
  const atQuery = React.useMemo(() => {
    const m = input.match(/(^|\s)@([^\s]*)$/);
    if (!m) return null;
    const raw = m[2];
    const slash = raw.lastIndexOf('/');
    const parentRel = slash >= 0 ? raw.slice(0, slash) : '';
    const filter    = slash >= 0 ? raw.slice(slash + 1) : raw;
    // @-completion is always project-root-relative — independent of
    // SCOPE_PATH, which only narrows the file-tree panel. The token
    // that ends up in the chat must be a full project-root-relative
    // path so the agent can resolve it without knowing about scope.
    return {
      token: '@' + raw,
      pos: m.index + m[1].length,
      raw,
      parentRel,
      parentAbs: parentRel,  // project-root-relative
      filter: filter.toLowerCase(),
    };
  }, [input]);

  // Cache directory listings keyed by absolute path so chaining
  // ("@a/" → "@a/b/" → "@a/b/c/") doesn't refetch each segment.
  const [atDirCache, setAtDirCache] = React.useState({});
  const [atDirEntries, setAtDirEntries] = React.useState([]);

  React.useEffect(() => {
    if (!atQuery) { setAtDirEntries([]); return; }
    const key = atQuery.parentAbs;
    if (atDirCache[key]) { setAtDirEntries(atDirCache[key]); return; }
    let cancelled = false;
    fetch('/api/files?path=' + encodeURIComponent(key))
      .then(r => r.json())
      .then(d => {
        if (cancelled) return;
        const entries = (d && d.entries) || [];
        setAtDirCache(c => ({ ...c, [key]: entries }));
        setAtDirEntries(entries);
      })
      .catch(() => { if (!cancelled) setAtDirEntries([]); });
    return () => { cancelled = true; };
  }, [atQuery && atQuery.parentAbs]);

  const fileMatches = React.useMemo(() => {
    if (!atQuery) return [];
    const f = atQuery.filter;
    const list = !f
      ? atDirEntries
      : atDirEntries.filter(e => e.name.toLowerCase().startsWith(f));
    return list.slice(0, 30);
  }, [atQuery && atQuery.filter, atDirEntries]);

  const filtered = React.useMemo(() => {
    if (!input.startsWith('/')) return [];
    const q = input.slice(1).toLowerCase();
    return window.SLASH_COMMANDS.filter(c =>
      c.cmd.slice(1).toLowerCase().startsWith(q) || c.alias.startsWith(q)
    );
  }, [input]);

  const [showAt, setShowAt] = React.useState(false);
  const [atSel, setAtSel] = React.useState(0);

  React.useEffect(() => {
    if (input.startsWith('/')) { setShowSlash(true); setSlashSel(0); setShowAt(false); }
    else setShowSlash(false);
    // Keep the @ popup open as long as the user is in an @-token —
    // even when matches are momentarily empty (chaining into a new
    // dir takes one fetch round-trip). Closing on empty would flicker.
    if (atQuery) { setShowAt(true); setAtSel(0); }
    else setShowAt(false);
  }, [input, atQuery && atQuery.parentAbs, atQuery && atQuery.filter]);

  const acceptAtCompletion = (entry) => {
    if (!atQuery) return;
    const before = input.slice(0, atQuery.pos);
    const after  = input.slice(atQuery.pos + atQuery.token.length);
    // Replace only the filter portion of the @-token, keeping the
    // parent path the user already typed. So "@workflow/s" + selecting
    // "ssot-gen/" becomes "@workflow/ssot-gen/" (popup stays open and
    // shows ssot-gen's contents next), while selecting a file appends
    // a trailing space and closes the popup.
    const parent = atQuery.parentRel ? atQuery.parentRel + '/' : '';
    if (entry.type === 'dir') {
      // Chain into the directory — popup re-opens with its contents
      // because the new query ends in '/'.
      setInput(before + '@' + parent + entry.name + '/' + after);
      // Keep showAt true; the effect that listens to atQuery will
      // refetch the new directory's entries automatically.
    } else {
      setInput(before + '@' + parent + entry.name + ' ' + after);
      setShowAt(false);
    }
  };

  React.useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [feed, streamText, mainTab]);

  // shift+tab swaps Normal ↔ Plan. Fire even when the chat input is
  // focused — the input is auto-focused, so the old "tagName !== INPUT"
  // guard meant the shortcut never triggered. e.preventDefault stops
  // the browser's native focus-walk regardless.
  React.useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Tab' && e.shiftKey) {
        e.preventDefault();
        switchIntent(intent === 'normal' ? 'plan' : 'normal');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [intent, workflow]);

  // The textarea auto-grows in onChange while the user types but stays
  // tall after submitMsg/setInput('') because that path is state-only
  // and doesn't fire onChange. Watch the value directly and snap the
  // inline height back to the CSS min when it becomes empty.
  React.useEffect(() => {
    if (input === '' && inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
  }, [input]);

  // ── chat actions ───────────────────────────────────────────────
  const submitMsg = (cmd) => {
    const raw = (cmd ?? input).trim();
    if (!raw) return;
    recordInputHistory(raw);
    setInput('');
    setShowSlash(false);

    if (pendingQcard && !raw.startsWith('/') && answerPendingFromInput(raw)) {
      return;
    }

    // ── Client-side slash commands ──────────────────────────────
    // Some commands operate on browser state (SCOPE_PATH lives in
    // localStorage / window) and don't need an agent round-trip.
    // Handle them here BEFORE sending anything to the backend.
    const sessionMatch = raw.match(/^\/(session|sess)(\s+(.*))?$/);
    if (sessionMatch) {
      const arg = (sessionMatch[3] || '').trim();
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      const _clearStreaming = () => {
        setStreaming(false);
        streamBufferRef.current = '';
        setStreamText('');
      };
      if (!arg) {
        setFeed(f => [...f, {
          kind: 'agent',
          text: `Current session: \`${activeSession || window.ACTIVE_SESSION || 'default'}\`\nUse \`/session default\` to return to the default session.`,
        }]);
        _clearStreaming();
        return;
      }
      if (arg.toLowerCase() === 'default') {
        const sid = switchToDefaultSession();
        setFeed(f => [...f, { kind: 'agent', text: `Session set to \`${sid}\`.` }]);
        _clearStreaming();
        return;
      }
      const sid = resolveSession(arg, activeSession, window.ACTIVE_SESSION);
      window.ACTIVE_SESSION = sid;
      setActiveSession(sid);
      try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
      if (window.atlasData && window.atlasData.refreshSessionState) {
        window.atlasData.refreshSessionState(sid);
      }
      setFeed(f => [...f, { kind: 'agent', text: `Session set to \`${sid}\`.` }]);
      _clearStreaming();
      return;
    }

    const m = raw.match(/^\/(scope|cd)(\s+(.*))?$/);
    if (m) {
      const arg = (m[3] || '').trim();
      const cur = window.SCOPE_PATH || '';
      // Same defensive cleanup as the /plan branch — these commands
      // are purely client-side and shouldn't inherit a stale
      // streaming state from a prior unclean turn.
      const _clearStreaming = () => {
        setStreaming(false);
        streamBufferRef.current = '';
        setStreamText('');
      };
      if (!arg) {
        setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
        setFeed(f => [...f, {
          kind: 'agent',
          text: cur
            ? `Current scope: \`${cur}\`\nUse \`/scope <path>\` to change, \`/scope /\` to reset.`
            : 'No scope set — agent works on the whole project.\nUse `/scope <path>` to confine it.',
        }]);
        _clearStreaming();
        return;
      }
      const next = (arg === '/' || arg === '~' || arg === '-') ? '' : arg.replace(/^\/+|\/+$/g, '');
      window.atlasData.setScopePath(next);
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      setFeed(f => [...f, {
        kind: 'agent',
        text: next
          ? `✓ Scope set to \`${next}\`. Future prompts will tell the agent to stay inside this directory.`
          : '✓ Scope cleared. Agent operates on the whole project again.',
      }]);
      _clearStreaming();
      return;
    }

    // /plan, /normal, /mode plan, /mode normal — flip UI intent locally
    // AND forward to backend so agent_mode flips. Mirrors the /scope
    // pattern. Without this, /plan only updated the backend and the
    // sidebar pill stayed on "normal" until shift+tab (also broken).
    //
    // Backend slash registry: '/plan' and '/mode <x>' are registered.
    // '/normal' (without /mode prefix) is NOT registered → would land
    // as "Unknown command" and leave agent_mode in plan_q while the
    // UI happily flipped to normal. Normalize the WIRE form to the
    // canonical command the backend actually handles.
    const modeMatch = raw.match(/^\/(plan|mode\s+plan|mode\s+normal|normal)$/i);
    if (modeMatch) {
      const target = /^\/(plan|mode\s+plan)$/i.test(raw) ? 'plan' : 'normal';
      const wire = target === 'plan' ? '/plan' : '/mode normal';
      setIntent(target);
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      sendPrompt(wire);
      // Slash commands don't run the agent — clear any stale streaming
      // state inherited from a prior turn that didn't close out cleanly
      // (agent crash, dropped WS, etc.). Without this, the banner
      // leaves the running status stuck after the user types /plan.
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    const wfMatch = raw.match(/^\/(wf|workflow)(\s+(\S+))?$/i);
    if (wfMatch) {
      const targetWf = (wfMatch[3] || '').trim();
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      if (targetWf) {
        switchWorkflow(targetWf);
      } else {
        setFeed(f => [...f, {
          kind: 'agent',
          text: `Current workflow: \`${workflow || 'default'}\``,
        }]);
      }
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    const pipelineMatch = raw.match(/^\/(pipeline|pipe|full-pipeline)(\s+(\S+))?$/i);
    if (pipelineMatch) {
      const ipName = (pipelineMatch[3] || window.ACTIVE_IP || activeIp || '').trim();
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      const _clearStreaming = () => {
        setStreaming(false);
        streamBufferRef.current = '';
        setStreamText('');
      };
      if (!ipName || ipName === 'default') {
        setFeed(f => [...f, {
          kind: 'agent',
          text: 'Usage: `/pipeline <ip>` — dispatches SSOT → FL/CL → RTL → lint → TB → sim → coverage → syn → sta → pnr → sta-post.',
        }]);
        _clearStreaming();
        return;
      }
      fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ipName }),
      })
        .then(async r => {
          const j = await r.json().catch(() => ({}));
          if (!r.ok || j.error || j.detail) throw new Error(j.error || j.detail || `HTTP ${r.status}`);
          return j;
        })
        .then(j => {
          const stages = Array.isArray(j.stages)
            ? j.stages.map(s => s && s.id).filter(Boolean).join(' → ')
            : '';
          setFeed(f => [...f, {
            kind: 'agent',
            text: `Dispatched pipeline \`${j.pipeline_id || 'unknown'}\` for \`${ipName}\`${stages ? `.\nStages: ${stages}` : '.'}`,
          }]);
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'JOBS' }));
        })
        .catch(err => setFeed(f => [...f, {
          kind: 'agent',
          text: 'Pipeline dispatch failed: ' + (err && err.message || err),
        }]));
      _clearStreaming();
      return;
    }

    // /commit <msg> — labeled checkpoint in the active IP's per-IP git.
    const commitMatch = raw.match(/^\/commit(\s+([\s\S]+))?$/i);
    if (commitMatch) {
      const msg = (commitMatch[2] || '').trim() || 'manual checkpoint';
      const ipName = (window.ACTIVE_IP || activeIp || '').trim();
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      if (!ipName || ipName === 'default') {
        setFeed(f => [...f, {
          kind: 'agent',
          text: '⚠ no active IP — pick one from the IP_ID dropdown first.',
        }]);
      } else {
        fetch(`/api/ip/${encodeURIComponent(ipName)}/git/commit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg }),
        })
          .then(r => r.json())
          .then(j => {
            const ok = j && j.ok;
            const hash = (j && j.hash) || '?';
            const detail = (j && (j.stderr || j.error || '')).slice(0, 200);
            setFeed(f => [...f, {
              kind: 'agent',
              text: ok ? `✅ committed \`${hash}\` — ${msg}` : `⚠ commit failed: ${detail || 'unknown error'}`,
            }]);
          })
          .catch(err => setFeed(f => [...f, {
            kind: 'agent',
            text: '⚠ commit request failed: ' + (err && err.message || err),
          }]));
      }
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    // /feedback <text> — drop a message into the feedback table so an
    // admin can review it in the admin dashboard. Anyone logged in can
    // submit; the backend tags the row with their user_id.
    const feedbackMatch = raw.match(/^\/feedback(\s+([\s\S]+))?$/i);
    if (feedbackMatch) {
      const text = (feedbackMatch[2] || '').trim();
      setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      if (!text) {
        setFeed(f => [...f, {
          kind: 'agent',
          text: 'Usage: `/feedback <your message>` — sends a message to the admin team.',
        }]);
      } else {
        fetch('/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: text }),
        })
          .then(r => r.json())
          .then(j => setFeed(f => [...f, {
            kind: 'agent',
            text: j && j.ok
              ? `✅ feedback received (id: \`${(j.id || '').slice(0, 8)}\`). Thanks!`
              : `⚠ feedback failed: ${(j && (j.error || j.detail)) || 'unknown error'}`,
          }]))
          .catch(err => setFeed(f => [...f, {
            kind: 'agent',
            text: '⚠ feedback request failed: ' + (err && err.message || err),
          }]));
      }
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    setFeed(f => [...f, { kind: 'user', text: raw }]);
    setStreaming(true);
    setStreamText('');
    // Prepend a scope-restriction directive so the agent is forced to
    // operate inside the user's selected directory. Slash commands
    // bypass the prefix because they hit the local dispatcher first.
    // Confirmation tokens (y / yc / yes / n / cancel / ok …) ALSO
    // bypass — chat_loop's plan-confirmation handler does an exact
    // `inp.lower().strip() in ("y", "yes", ...)` match, and the
    // "[scope] You MUST..." prefix breaks that comparison so plan
    // mode never exits even after the user types `y`. Keep these
    // short tokens unprefixed.
    const isConfirmation = /^(y|yc|yes|n|no|confirm|cancel|ok|proceed|ㅇㅇ|ㄴㄴ|확인|진행|취소|네|예|아니오)$/i.test(raw);
    const scope = (window.SCOPE_PATH || '').trim();
    let outbound = raw;
    if (scope && !raw.startsWith('/') && !isConfirmation) {
      outbound = (
        `[scope] You MUST confine every file read, write, edit, grep, ` +
        `find, and run_command to paths inside "${scope}". Do not touch ` +
        `files outside this directory unless I explicitly say so. The workspace ` +
        `root is still the project root: if a requested path already starts ` +
        `with "${scope}/", use it exactly once and never rewrite it as ` +
        `"${scope}/${scope}/...". For SSOT, the canonical path is ` +
        `"${scope}/yaml/${scope}.ssot.yaml", not ` +
        `"${scope}/${scope}/yaml/${scope}.ssot.yaml".\n\n` +
        raw
      );
    }
    sendPrompt(outbound);
  };

  // Subscribe to backend events and translate them into feed entries.
  React.useEffect(() => {
    if (!window.backend) {
      setBackendState('missing');
      setStreaming(false);
      return;
    }
    if (window.backend.getConnectionState) {
      setBackendState(window.backend.getConnectionState());
    }
    const subs = [];
    // Hello payload — server tells us which center-column layout the
    // user has configured (.config: ATLAS_CENTER_LAYOUT=classic|tabbed).
    subs.push(window.backend.subscribe('hello', (m) => {
      if (m && (m.center_layout === 'tabbed' || m.center_layout === 'classic')) {
        setCenterLayout(m.center_layout);
      }
      if (m && typeof m.chat_feed_summary === 'boolean') {
        window.ATLAS_CHAT_FEED_SUMMARY = m.chat_feed_summary;
        setChatFeedSummary(m.chat_feed_summary);
      }
      if (m && typeof m.running === 'boolean') {
        setStreaming(!!m.running);
      }
    }));
    subs.push(window.backend.subscribe('connection', (m) => {
      const state = (m && m.state) || '';
      setBackendState(state || 'unknown');
      if (state === 'closed' || state === 'error') {
        streamBufferRef.current = '';
        setStreamText('');
        setStreaming(false);
      }
    }));
    subs.push(window.backend.subscribe('peer_joined', (m) => {
      setPeerCount(m.peers || 1);
    }));
    subs.push(window.backend.subscribe('peer_left', (m) => {
      setPeerCount(m.peers || 1);
    }));
    // Coalesce token chunks into a small fixed cadence. The live preview
    // renders this state, so requestAnimationFrame can become too chatty
    // during dense token bursts; 50 ms stays visibly live without forcing
    // a React commit for every WebSocket frame.
    let _streamTimer = 0;
    const STREAM_FLUSH_MS = 50;
    const _flushStream = () => {
      _streamTimer = 0;
      setStreamText(streamBufferRef.current);
    };
    subs.push(window.backend.subscribe('token', (m) => {
      const t = m.text || '';
      if (!t || t === '\x00') return;
      streamBufferRef.current += t;
      if (!_streamTimer) _streamTimer = setTimeout(_flushStream, STREAM_FLUSH_MS);
    }));
    // Reasoning chunks come one-per-sentence; the previous handler
    // setFeed'd on every chunk, so 10 sentences = 10 React re-renders
    // of the entire feed. Stage chunks in a ref and flush at most
    // once per animation frame, mirroring the token stream batcher.
    const _reasonBuf = { lines: [] };
    let _reasonRaf = 0;
    const _flushReason = () => {
      _reasonRaf = 0;
      const newLines = _reasonBuf.lines;
      _reasonBuf.lines = [];
      if (!newLines.length) return;
      const chunk = newLines.join('\n');
      setFeed(l => {
        const last = l[l.length - 1];
        if (last && last.kind === 'thought') {
          return [...l.slice(0, -1),
                  { kind: 'thought', text: last.text + '\n' + chunk, createdAt: last.createdAt || Date.now() }];
        }
        return [...l, { kind: 'thought', text: chunk, createdAt: Date.now() }];
      });
    };
    subs.push(window.backend.subscribe('reasoning', (m) => {
      const t = (m.text || '').trim();
      if (!t) return;
      _reasonBuf.lines.push(t);
      if (!_reasonRaf) _reasonRaf = requestAnimationFrame(_flushReason);
    }));
    // todo_line: react_loop emits a full TodoTracker.format_simple() dump
    // on every iteration and after every tool call (see react_loop.py),
    // which previously flooded the chat feed with redundant "OBS TODO"
    // status blocks. The right-sidebar <TodoPanel/> already renders the
    // authoritative live state via /api/todos (data.jsx subscribes to
    // todo_line for refresh), so swallow the event here and keep the
    // chat for messages/tool_result only.
    // Tool call header: agent is about to invoke a tool.
    subs.push(window.backend.subscribe('tool', (m) => {
      const t = (m.text || '').trim();
      if (!t) return;
      // Detect the per-iteration banner (── Iter N / M  [model]) and
      // route to a thinner iter_marker kind so the feed doesn't break
      // tool action+obs cards with a full-width separator.
      const iterMatch = t.match(/^──\s*Iter\s+(\d+)\s*\/\s*(\d+)\s*\[([^\]]+)\]/);
      if (iterMatch) {
        setFeed(l => [...l, {
          kind: 'iter_marker',
          n: parseInt(iterMatch[1], 10),
          max: parseInt(iterMatch[2], 10),
          model: iterMatch[3].trim(),
          createdAt: Date.now(),
        }]);
        return;
      }
      // Finalize any pending streaming text first so the tool-call entry
      // sits AFTER the pre-tool reasoning/agent text in the feed.
      const buf = streamBufferRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf, createdAt: Date.now() }]);
      streamBufferRef.current = '';
      setStreamText('');
      // Parse "▶ tool_name  args…" → capture tool name so ToolCard can
      // pair this with its tool_result obs and pick a theme color.
      const am = t.match(/^▶\s*(\S+)\s*(.*)$/);
      const toolName = am ? am[1] : '';
      const argsText = am ? (am[2] || '').trim() : '';
      setFeed(l => [...l, {
        kind: 'action',
        text: t,
        tool: toolName,
        args: argsText,
        createdAt: Date.now(),
      }]);
    }));
    // Tool observation: the result the agent just received from the tool.
    subs.push(window.backend.subscribe('tool_result', (m) => {
      const t = (m.text || '').trim();
      if (!t) return;
      if (_isWorkflowResultTool(m.tool || '')) return;
      setFeed(l => [...l, {
        kind: 'obs',
        text: t,
        tool: m.tool || '',
        truncated: !!m.truncated,
        createdAt: Date.now(),
      }]);
    }));
    // Park the in-progress streaming buffer into the feed without
    // touching the streaming flag — flush fires AFTER EACH iteration,
    // not just at turn end, so the spinner must keep going until
    // agent_state(running:false) explicitly says we're done.
    const parkBuffer = () => {
      const buf = streamBufferRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf, createdAt: Date.now() }]);
      streamBufferRef.current = '';
      setStreamText('');
    };
    const turnEnd = () => {
      parkBuffer();
      setStreaming(false);
      // Drop a visible divider in the feed so the user can scroll back
      // and see exactly where each turn ended. Skip if the previous
      // entry is already a turn_end (defensive — flush + done can both
      // call this in close succession).
      setFeed(l => {
        const last = l[l.length - 1];
        if (last && last.kind === 'turn_end') return l;
        return [...l, { kind: 'turn_end', text: '✓ end of loop', createdAt: Date.now() }];
      });
    };
    // Mode flip from backend (chat_loop auto-promotes plan_q→normal when
    // the user types "y" to confirm). Sync the UI pill so it doesn't
    // stay stuck on PLAN while the agent is already executing writes.
    subs.push(window.backend.subscribe('mode_change', (m) => {
      const target = (m.mode || '').toLowerCase();
      if (target === 'normal' || target === 'plan') {
        setIntent(target);
      }
    }));

    // Safety-net feed entry for slash command output. Backend mirrors the
    // fenced output via both the token+flush pipeline and this event; we
    // dedupe by checking streamBufferRef (normal case: token fired first)
    // AND the feed's last agent entry (edge case: flush already parked the
    // buffer and cleared it before this event arrived).
    subs.push(window.backend.subscribe('slash_output', (m) => {
      const t = m.text || '';
      if (!t) return;
      const shown = _unwrapAtlasOutputFence(t);
      // Fast path — token landed in the buffer before us (new emit order).
      const buf = streamBufferRef.current;
      if (buf && (buf.indexOf(t) >= 0 || buf.indexOf(shown) >= 0)) return;
      // Slow path — flush may have already parked the buffer. Check if the
      // last agent entry in the feed is a duplicate.
      let dup = false;
      setFeed(l => {
        const last = l[l.length - 1];
        if (last && last.kind === 'agent' && (last.text === t || last.text === shown)) {
          dup = true;
          return l;
        }
        return [...l, { kind: 'agent', text: shown, createdAt: Date.now(), fromSlash: true }];
      });
      if (dup) return;
      streamBufferRef.current = '';
      setStreamText('');
    }));
    subs.push(window.backend.subscribe('flush', parkBuffer));
    subs.push(window.backend.subscribe('done', turnEnd));
    subs.push(window.backend.subscribe('agent_state', (m) => {
      if (m.running === false) turnEnd();
      else if (m.running === true) setStreaming(true);
    }));
    subs.push(window.backend.subscribe('error', (m) => {
      setFeed(l => [...l, { kind: 'agent', text: `[error] ${m.message || ''}`, createdAt: Date.now() }]);
      streamBufferRef.current = '';
      setStreamText('');
      setStreaming(false);
    }));
    // ask_user → register a dynamic flow and append a qcard to the feed.
    // Two payload shapes:
    //   • Single  : {question, kind, options, subtitle}
    //   • Batched : {questions: [{question, kind, options, subtitle}, ...]}
    // Batched mirrors the textual UI's ask_user breadcrumb-tab flow:
    // the user sees N tabs (☐/☒ marker per tab + a final ✔ Submit tab),
    // fills each, then submits all answers in one round-trip.
    subs.push(window.backend.subscribe('ask_user', (m) => {
      const flowId = m.flow_id;
      if (!flowId) return;
      activateAskUserSession(m.session, m.ip, m.workflow);
      streamBufferRef.current = '';
      setStreamText('');
      setStreaming(false);
      const isBatched = Array.isArray(m.questions) && m.questions.length > 0;
      // Multi-question (batched) ask_user is awkward to answer in the
      // classic-layout inline-bottom slot — N stacked questions with
      // option lists overflow the input area. Promote to the tabbed
      // Q&A pane so the user gets the full center column for the
      // batch. Single-question flows stay inline (fits fine there).
      if (isBatched) {
        setCenterLayout('tabbed');
        setMainTab('qa');
      }
      if (isBatched) {
        const qs = m.questions.map(q => ({
          question: q.question || '',
          kind: q.kind === 'multi' ? 'multi'
              : q.kind === 'input' ? 'input' : 'single',
          subtitle: q.subtitle || '',
          placeholder: q.placeholder || '',
          multiline: !!q.multiline || String(q.placeholder || '').includes('\n'),
          options: (q.options || []).map(o => ({
            id: o.id, label: o.label, detail: o.detail || '', selected: false,
          })),
        }));
        window.QA_FLOWS[flowId] = {
          stage: 'Agent', stageDetail: 'ask_user',
          title: qs[0].question || 'Questions',
          step: 1, total: qs.length,
          breadcrumbs: [], activeBreadcrumb: 0,
          // legacy single fields point to first question (so any
          // existing single-question render fallback still works)
          question: qs[0].question, subtitle: qs[0].subtitle,
          kind: qs[0].kind, options: qs[0].options,
          // batched extras
          batched: true,
          questions: qs,
          history: [], upcoming: [],
          session: normalizeUiSession(m.session || ''),
          ip: m.ip || '',
          workflow: m.workflow || '',
          source: m.source || '',
          dynamic: true,
        };
        setQaState(s => ({
          ...s,
          [flowId]: {
            batched: true,
            active: 0,
            states: qs.map(q => ({
              opts: q.options.map(o => ({ ...o })),
              custom: '',
            })),
            submitted: false,
          },
        }));
      } else {
        // Single-question path — unchanged
        const opts = (m.options || []).map(o => ({
          id: o.id, label: o.label, detail: o.detail || '', selected: false,
        }));
        window.QA_FLOWS[flowId] = {
          stage: 'Agent', stageDetail: 'ask_user',
          title: m.question || 'Question',
          step: 1, total: 1,
          breadcrumbs: [], activeBreadcrumb: 0,
          question: m.question || '',
          subtitle: m.subtitle || '',
          placeholder: m.placeholder || '',
          multiline: !!m.multiline || String(m.placeholder || '').includes('\n'),
          kind: m.kind === 'multi' ? 'multi' : m.kind === 'input' ? 'input' : 'single',
          options: opts,
          history: [], upcoming: [],
          session: normalizeUiSession(m.session || ''),
          ip: m.ip || '',
          workflow: m.workflow || '',
          source: m.source || '',
          dynamic: true,
        };
        setQaState(s => ({
          ...s,
          [flowId]: { opts: opts.map(o => ({ ...o })), custom: '', submitted: false }
        }));
      }
      setFeed(f => (
        f.some(e => e && e.kind === 'qcard' && e.flowId === flowId)
          ? f
          : [...f, { kind: 'qcard', flowId, dynamic: true, session: normalizeUiSession(m.session || '') }]
      ));
      if (m.workflow === 'ssot-gen' || m.source === 'ssot-qna') {
        setTimeout(refreshSsotQa, 150);
      }
    }));
    subs.push(window.backend.subscribe('ssot_approval_ready', (m) => {
      if (!m || !m.ip) return;
      const payload = { ...m, createdAt: Date.now() };
      setSsotApproval(payload);
      setFeed(f => {
        const deduped = f.filter(e => !(e.kind === 'ssot_approval' && e.ip === m.ip));
        return [...deduped, {
          kind: 'ssot_approval',
          ip: m.ip,
          payload,
          createdAt: Date.now(),
        }];
      });
      setStreaming(false);
    }));
    const closeAskUser = (m) => {
      const flowId = m && m.flow_id;
      if (!flowId) return;
      setQaState(s => {
        const cur = s[flowId];
        if (!cur || cur.submitted) return s;
        return { ...s, [flowId]: { ...cur, submitted: true } };
      });
      setTimeout(refreshSsotQa, 250);
    };
    subs.push(window.backend.subscribe('ask_user_answered', closeAskUser));
    subs.push(window.backend.subscribe('ask_user_closed', closeAskUser));
    subs.push(window.backend.subscribe('ssot_qa_updated', (m) => refreshSsotQa(m && m.session)));
    return () => {
      if (_streamTimer) clearTimeout(_streamTimer);
      if (_reasonRaf) cancelAnimationFrame(_reasonRaf);
      subs.forEach(u => u && u());
    };
  }, [activateAskUserSession, refreshSsotQa]);

  const navigateInputHistory = (delta) => {
    if (!inputHistory.length) return false;
    let idx = inputHistoryIndexRef.current;
    if (idx === null || idx === undefined) {
      if (delta > 0) return false;
      inputHistoryDraftRef.current = input;
      idx = inputHistory.length - 1;
    } else {
      idx += delta;
    }
    if (idx < 0) idx = 0;
    if (idx >= inputHistory.length) {
      inputHistoryIndexRef.current = null;
      setInput(inputHistoryDraftRef.current || '');
      return true;
    }
    inputHistoryIndexRef.current = idx;
    setInput(inputHistory[idx] || '');
    setShowSlash(false);
    setShowAt(false);
    return true;
  };

  const onKey = (e) => {
    if (showSlash) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setSlashSel(s => Math.min(s + 1, filtered.length - 1)); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setSlashSel(s => Math.max(s - 1, 0)); return; }
      if (e.key === 'Tab' || e.key === 'Enter') {
        if (filtered[slashSel]) {
          e.preventDefault();
          if (e.key === 'Enter') submitMsg(filtered[slashSel].cmd);
          else setInput(filtered[slashSel].cmd + ' ');
          return;
        }
      }
      if (e.key === 'Escape') { e.preventDefault(); setShowSlash(false); return; }
    }
    if (showAt) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setAtSel(s => Math.min(s + 1, fileMatches.length - 1)); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setAtSel(s => Math.max(s - 1, 0)); return; }
      if (e.key === 'Tab' || e.key === 'Enter') {
        if (fileMatches[atSel]) {
          e.preventDefault();
          acceptAtCompletion(fileMatches[atSel]);
          return;
        }
      }
      if (e.key === 'Escape') { e.preventDefault(); setShowAt(false); return; }
    }
    if (e.key === 'ArrowUp') {
      if (navigateInputHistory(-1)) {
        e.preventDefault();
        requestAnimationFrame(() => {
          const el = inputRef.current;
          if (el) el.setSelectionRange(el.value.length, el.value.length);
        });
      }
      return;
    }
    if (e.key === 'ArrowDown') {
      if (navigateInputHistory(1)) {
        e.preventDefault();
        requestAnimationFrame(() => {
          const el = inputRef.current;
          if (el) el.setSelectionRange(el.value.length, el.value.length);
        });
      }
      return;
    }
    // Plain Enter submits. Shift+Enter and Alt/Option+Enter both
    // insert a literal newline so multi-line prompts (paste, code
    // snippet, structured questions) compose naturally. macOS
    // Safari/Chromium textarea does NOT insert \n on Alt+Enter by
    // default — we splice it in manually so Option+Enter behaves the
    // same as Shift+Enter regardless of OS.
    if (e.key === 'Enter') {
      if (e.altKey) {
        e.preventDefault();
        const el = e.target;
        const lo = el.selectionStart;
        const hi = el.selectionEnd;
        const next = el.value.slice(0, lo) + '\n' + el.value.slice(hi);
        setInput(next);
        requestAnimationFrame(() => {
          el.selectionStart = el.selectionEnd = lo + 1;
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 192) + 'px';
        });
        return;
      }
      if (!e.shiftKey) {
        e.preventDefault();
        submitMsg();
      }
      // Shift+Enter: textarea native handles newline insertion;
      // onChange will fire the auto-grow.
    }
  };

  // ── question card handlers ─────────────────────────────────────
  // Both single-question and batched (tabbed) flows share these
  // helpers; in batched mode they operate on the active tab's slice
  // (states[active]) instead of the top-level opts/custom.
  const toggleOpt = (flowId, optId) => {
    const flow = window.QA_FLOWS[flowId];
    setQaState(s => {
      const cur = s[flowId];
      if (cur.submitted) return s;
      if (cur.batched) {
        const idx = cur.active || 0;
        const q = flow.questions[idx];
        const tabState = cur.states[idx];
        let opts;
        if (q.kind === 'multi') {
          opts = tabState.opts.map(o =>
            o.id === optId ? (o.locked ? o : { ...o, selected: !o.selected }) : o
          );
        } else {
          opts = tabState.opts.map(o => ({ ...o, selected: o.id === optId }));
        }
        const states = cur.states.map((st, i) =>
          i === idx ? { ...st, opts } : st
        );
        return { ...s, [flowId]: { ...cur, states } };
      }
      let opts;
      if (flow.kind === 'multi') {
        opts = cur.opts.map(o => o.id === optId ? (o.locked ? o : { ...o, selected: !o.selected }) : o);
      } else {
        opts = cur.opts.map(o => ({ ...o, selected: o.id === optId }));
      }
      return { ...s, [flowId]: { ...cur, opts } };
    });
  };

  const setCustom = (flowId, val) => {
    setQaState(s => {
      const cur = s[flowId];
      if (!cur) return s;
      if (cur.batched) {
        const idx = cur.active || 0;
        const states = cur.states.map((st, i) =>
          i === idx ? { ...st, custom: val } : st
        );
        return { ...s, [flowId]: { ...cur, states } };
      }
      return { ...s, [flowId]: { ...cur, custom: val } };
    });
  };

  function matchAnswerToken(raw, opts) {
    const text = String(raw || '').trim();
    if (!text) return null;
    if (/^\d+$/.test(text)) {
      const idx = parseInt(text, 10) - 1;
      return opts[idx] || null;
    }
    const low = text.toLowerCase();
    return opts.find(o =>
      String(o.id || '').toLowerCase() === low ||
      String(o.label || '').toLowerCase() === low
    ) || null;
  }

  function parseTextAnswer(raw, question, opts) {
    const text = String(raw || '').trim();
    const kind = question?.kind === 'multi' ? 'multi'
      : question?.kind === 'input' ? 'input'
      : 'single';
    if (!text || kind === 'input' || !opts.length) {
      return { selected: [], custom: text };
    }
    if (kind === 'multi') {
      const tokens = text.split(/[,\s]+/).map(x => x.trim()).filter(Boolean);
      const selected = [];
      const unmatched = [];
      for (const token of tokens) {
        const match = matchAnswerToken(token, opts);
        if (match) selected.push(match.id);
        else unmatched.push(token);
      }
      if (selected.length) {
        return { selected: Array.from(new Set(selected)), custom: unmatched.join(' ') };
      }
      return { selected: [], custom: text };
    }
    const match = matchAnswerToken(text, opts);
    return match ? { selected: [match.id], custom: '' } : { selected: [], custom: text };
  }

  function applyParsedAnswer(tabState, question, parsed) {
    const selected = new Set(parsed.selected || []);
    const kind = question?.kind === 'multi' ? 'multi'
      : question?.kind === 'input' ? 'input'
      : 'single';
    const opts = (tabState.opts || []).map(o => ({
      ...o,
      selected: kind === 'multi'
        ? (!!o.locked || selected.has(o.id))
        : selected.has(o.id),
    }));
    return { ...tabState, opts, custom: parsed.custom || '' };
  }

  function tabHasAnswer(tabState) {
    return !!(
      (tabState?.opts || []).some(o => o.selected) ||
      String(tabState?.custom || '').trim()
    );
  }

  function historySnapshotFor(flowId, flow, st) {
    if (!flow || !st) return null;
    const session = normalizeUiSession(flow.session || currentSession || window.ACTIVE_SESSION || '');
    const ip = String(flow.ip || ssotIpFromSession(session) || activeSsotIp() || '').trim();
    const items = flow.batched
      ? (flow.questions || []).map((q, i) => {
          const tab = (st.states || [])[i] || { opts: [], custom: '' };
          return {
            question: q.question || '',
            kind: q.kind || 'single',
            selected: tab.opts.filter(o => o.selected)
              .map(o => ({ id: o.id, label: o.label })),
            custom: tab.custom || '',
          };
        })
      : [{
          question: flow.question || '',
          kind: flow.kind || 'single',
          selected: (st.opts || []).filter(o => o.selected)
            .map(o => ({ id: o.id, label: o.label })),
          custom: st.custom || '',
        }];
    return {
      flowId,
      ts: Date.now(),
      session,
      ip,
      workflow: flow.workflow || '',
      source: flow.source || '',
      items,
    };
  }

  function answerPendingFromInput(raw) {
    const flowId = pendingQcard?.flowId;
    const flow = flowId && window.QA_FLOWS && window.QA_FLOWS[flowId];
    const st = flowId && qaState[flowId];
    const text = String(raw || '').trim();
    if (!flowId || !flow || !st || st.submitted || !text) return false;

    let nextState = st;
    let shouldSubmit = false;
    let snapshot = null;

    if (st.batched) {
      const questions = flow.questions || [];
      const states = (st.states || questions.map(q => ({
        opts: (q.options || []).map(o => ({ ...o })),
        custom: '',
      }))).map(tab => ({
        ...tab,
        opts: (tab.opts || []).map(o => ({ ...o })),
      }));
      const lines = text.split(/\n+/).map(x => x.trim()).filter(Boolean);
      let lineIdx = 0;
      const active = Math.max(0, Math.min(st.active || 0, Math.max(0, questions.length - 1)));
      const openTargets = questions.map((_, i) => i).filter(i => !tabHasAnswer(states[i]));
      const targets = lines.length > 1
        ? Array.from(new Set((openTargets.length ? openTargets : [active])))
        : [active];
      for (const idx of targets) {
        if (idx < 0 || idx >= questions.length || lineIdx >= lines.length) continue;
        const q = questions[idx];
        const parsed = parseTextAnswer(lines[lineIdx], q, states[idx]?.opts || []);
        states[idx] = applyParsedAnswer(states[idx] || { opts: [], custom: '' }, q, parsed);
        lineIdx += 1;
      }
      const allAnswered = states.length > 0 && states.every(tabHasAnswer);
      const firstOpen = states.findIndex(tab => !tabHasAnswer(tab));
      nextState = {
        ...st,
        states,
        active: allAnswered ? questions.length : Math.max(0, firstOpen),
        submitted: allAnswered,
      };
      shouldSubmit = allAnswered;
      if (shouldSubmit && window.backend) {
        const answers = states.map(tab => ({
          selected: tab.opts.filter(o => o.selected).map(o => o.id),
          custom: tab.custom || '',
        }));
        window.backend.send({ type: 'answer', flow_id: flowId, answers });
        snapshot = historySnapshotFor(flowId, flow, nextState);
      }
    } else {
      const parsed = parseTextAnswer(text, flow, st.opts || []);
      nextState = {
        ...applyParsedAnswer(st, flow, parsed),
        submitted: true,
      };
      shouldSubmit = true;
      if (window.backend) {
        window.backend.send({
          type: 'answer',
          flow_id: flowId,
          selected: nextState.opts.filter(o => o.selected).map(o => o.id),
          custom: nextState.custom || '',
        });
        snapshot = historySnapshotFor(flowId, flow, nextState);
      }
    }

    setFeed(f => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
    setQaState(s => ({ ...s, [flowId]: nextState }));
    if (snapshot) {
      setQaHistory(h => {
        if (h.length && h[0].flowId === snapshot.flowId) return h;
        return [snapshot, ...h].slice(0, QA_HISTORY_LIMIT);
      });
    }
    setMainTab(shouldSubmit ? 'chat' : 'qa');
    setAskSel(0);
    if (shouldSubmit) setStreaming(true);
    return true;
  }

  // Switch active tab in a batched ask_user flow. `idx` may equal
  // questions.length to land on the synthetic 'Submit' tab (review).
  const setActiveTab = (flowId, idx) => {
    setQaState(s => {
      const cur = s[flowId];
      if (!cur || !cur.batched) return s;
      const flow = window.QA_FLOWS[flowId];
      const max = (flow.questions || []).length; // .length = Submit tab
      const next = Math.max(0, Math.min(max, idx));
      return { ...s, [flowId]: { ...cur, active: next } };
    });
  };

  const advanceBatchedQuestion = (flowId) => {
    setQaState(s => {
      const cur = s[flowId];
      if (!cur || !cur.batched) return s;
      const flow = window.QA_FLOWS[flowId];
      const tabCount = (flow.questions || []).length;
      const active = cur.active || 0;
      const next = Math.max(0, Math.min(tabCount, active + 1));
      return { ...s, [flowId]: { ...cur, active: next } };
    });
  };

  // submitCard ships an ask_user answer back to the agent over the WS.
  // Batched flows package every per-tab answer into a single
  // {answers: [...]} payload so the backend resolves all of them in
  // one round-trip — matches the textual UI's batched ask_user.
  const submitCard = (flowId) => {
    // Functional updater so we always read the latest qaState — this
    // matters when a toggle was just queued (e.g. single-kind Enter
    // = toggle+submit) and we'd otherwise see pre-toggle state.
    let snapshot = null;
    setQaState(s => {
      const st = s[flowId];
      if (!st || st.submitted) return s;
      if (window.backend) {
        if (st.batched) {
          const answers = (st.states || []).map(tab => ({
            selected: tab.opts.filter(o => o.selected).map(o => o.id),
            custom: tab.custom || '',
          }));
          window.backend.send({ type: 'answer', flow_id: flowId, answers });
        } else {
          const selectedIds = st.opts.filter(o => o.selected).map(o => o.id);
          window.backend.send({
            type: 'answer',
            flow_id: flowId,
            selected: selectedIds,
            custom: st.custom || '',
          });
        }
      }
      // Build a serializable history snapshot of THIS submit so we
      // can prepend it to qaHistory after the state update flushes.
      try {
        const flow = window.QA_FLOWS && window.QA_FLOWS[flowId];
        if (flow) {
          const items = flow.batched
            ? (flow.questions || []).map((q, i) => {
                const tab = (st.states || [])[i] || { opts: [], custom: '' };
                return {
                  question: q.question || '',
                  kind: q.kind || 'single',
                  selected: tab.opts.filter(o => o.selected)
                    .map(o => ({ id: o.id, label: o.label })),
                  custom: tab.custom || '',
                };
              })
            : [{
                question: flow.question || '',
                kind: flow.kind || 'single',
                selected: (st.opts || []).filter(o => o.selected)
                  .map(o => ({ id: o.id, label: o.label })),
                custom: st.custom || '',
              }];
          snapshot = {
            flowId,
            ts: Date.now(),
            session: normalizeUiSession(flow.session || currentSession || window.ACTIVE_SESSION || ''),
            ip: String(flow.ip || ssotIpFromSession(flow.session || currentSession || window.ACTIVE_SESSION || '') || activeSsotIp() || '').trim(),
            workflow: flow.workflow || '',
            source: flow.source || '',
            items,
          };
        }
      } catch (_) {}
      return { ...s, [flowId]: { ...st, submitted: true } };
    });
    if (snapshot) {
      setQaHistory(h => {
        if (h.length && h[0].flowId === snapshot.flowId) return h; // dedupe re-submits
        return [snapshot, ...h].slice(0, QA_HISTORY_LIMIT);
      });
    }
    setStreaming(true);  // agent resumes after receiving answer
  };

  // ── layout ─────────────────────────────────────────────────────
  // sim_debug owns its own hierarchy / source / wave / chat panels —
  // hide the outer ATLAS sidebars (mode/workflow/files on the left,
  // ATLAS + SSOT/Todo/Diff on the right) so the inner 3-zone
  // debug surface gets the full viewport. Width state is preserved so
  // switching back to another workflow restores the original layout.
  const effLeftW  = leftW;
  const effRightW = rightW;
  const renderFeedEntries = () => {
    // Pairing pre-pass: when an action entry is immediately followed by
    // an obs entry, fuse them into one ToolCard. Adjacency is enough —
    // strict tool-name match is too brittle (legacy/normalized entries
    // sometimes leave .tool empty on one side, causing a standalone
    // "OBS" row to leak into the feed).
    const out = [];
    for (let i = 0; i < feed.length; i++) {
      const cur = feed[i];
      const nxt = feed[i + 1];
      if (cur && cur.kind === 'action' && nxt && nxt.kind === 'obs') {
        out.push(<ToolCard key={i} action={cur} obs={nxt} summaryMode={chatFeedSummary} />);
        i++;
        continue;
      }
      if (cur && cur.kind === 'action' && cur.tool) {
        out.push(<ToolCard key={i} action={cur} obs={null} summaryMode={chatFeedSummary} />);
        continue;
      }
      // Orphan obs (action got swallowed, or hydration ordering anomaly):
      // wrap it in a ToolCard so it gets the same single-row collapsed
      // look as paired tools, instead of a separate "OBS" header line.
      if (cur && cur.kind === 'obs') {
        out.push(<ToolCard key={i} action={null} obs={cur} summaryMode={chatFeedSummary} />);
        continue;
      }
      out.push(
        <FeedEntry
          key={i}
          entry={cur}
          qaState={qaState}
          onToggle={toggleOpt}
          onCustom={setCustom}
          onSubmit={submitCard}
          dir={dir}
          summaryMode={chatFeedSummary}
        />
      );
    }
    return out;
  };
  const renderChatPane = (style = {}) => (
    <div ref={feedRef} style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '14px 18px', ...style }}>
      {renderFeedEntries()}
      <LiveAgentPreview text={streamText} />
    </div>
  );
  const renderPromptRow = () => (
    <div className="prompt-row">
      <span className="ps" style={{ color: 'var(--fg-mute)' }}>❯</span>
      <textarea ref={inputRef} value={input}
        rows={1}
        onChange={e => {
          inputHistoryIndexRef.current = null;
          inputHistoryDraftRef.current = '';
          setInput(e.target.value);
          // Auto-grow up to 8 rows (~12em). Shrinks back when the user
          // deletes content. min-height keeps the row aligned with the
          // ❯ prompt sigil even when empty.
          const el = e.target;
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 192) + 'px';
        }}
        onKeyDown={onKey}
        placeholder={pendingQcard
          ? 'Answer pending Q&A here · "/" for commands'
          : 'Type a message · "/" for commands · "@" for files · ⌥↵ newline'}
        autoFocus
      />
      <span className="mute" style={{ fontSize: 11 }}>
        {pendingQcard ? (
          <>
            <Kbd>↵</Kbd> answer · <Kbd>/</Kbd> cmd · <Kbd>↑</Kbd><Kbd>↓</Kbd> history
          </>
        ) : (
          <>
            <Kbd>/</Kbd> cmd · <Kbd>@</Kbd> file · <Kbd>↑</Kbd><Kbd>↓</Kbd> history · <Kbd>↵</Kbd> send · <Kbd>⌥↵</Kbd> newline
          </>
        )}
      </span>
    </div>
  );

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `${leftW}px 4px 1fr 4px ${rightW}px`,
      gap: 12,
      padding: 16,
      height: '100%', overflow: 'hidden',
    }}>
      {/* LEFT — Mode/Workflow + Files (collapsed when leftW===0 OR sim_debug) */}
      {effLeftW > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        <div className="box">
          <div className="box-h">
            <span>▸ mode</span>
            <span style={{ flex: 1 }} />
            <span
              onClick={toggleLeft}
              title="collapse left panel (double-click splitter to restore)"
              className="mute"
              style={{ cursor: 'pointer', fontSize: 12, padding: '0 6px',
                       userSelect: 'none' }}
            >‹</span>
            <span className="mute" style={{ fontSize: 10, textTransform: 'none', letterSpacing: 0 }}>shift+tab</span>
          </div>
          {/* Intent toggle: Normal | Plan */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--line)' }}>
            <div
              onClick={() => switchIntent('normal')}
              style={{
                padding: '8px 10px', textAlign: 'center', cursor: 'pointer', fontSize: 11,
                letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600,
                color: intent === 'normal' ? 'var(--bg)' : 'var(--fg-mute)',
                background: intent === 'normal' ? 'var(--cyan)' : 'transparent',
                borderRight: '1px solid var(--line)',
              }}
            >● Normal</div>
            <div
              onClick={() => switchIntent('plan')}
              style={{
                padding: '8px 10px', textAlign: 'center', cursor: 'pointer', fontSize: 11,
                letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600,
                color: intent === 'plan' ? 'var(--bg)' : 'var(--fg-mute)',
                background: intent === 'plan' ? 'var(--warn)' : 'transparent',
              }}
            >◐ Plan</div>
          </div>
          <div style={{ padding: '6px 12px 4px', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--fg-mute)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>workflow</span>
            <span className="mute" style={{ fontSize: 9, textTransform: 'none', letterSpacing: 0 }}>· optional · click to toggle</span>
          </div>
          <div style={{ paddingBottom: 4 }}>
            {window.FLOW_STAGES.map((s, i) => {
              const active = workflow === s.id;
              return (
                <button key={s.id}
                  type="button"
                  onClick={() => switchWorkflow(s.id)}
                  style={{
                    display: 'grid', gridTemplateColumns: '14px 38px 1fr 14px',
                    gap: 8, padding: '6px 12px', alignItems: 'center', fontSize: 12, cursor: 'pointer',
                    background: active ? 'var(--select)' : 'transparent',
                    borderLeft: active ? `2px solid ${s.color}` : '2px solid transparent',
                    borderTop: 0, borderRight: 0, borderBottom: 0,
                    width: '100%', color: 'var(--fg)', textAlign: 'left', fontFamily: 'inherit',
                  }}
                  onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--bg-2)'; }}
                  onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
                >
                  <span className="mute">{i + 1}</span>
                  <span style={{ color: s.color, fontWeight: 700, letterSpacing: '0.06em', fontSize: 10 }}>{s.glyph}</span>
                  <span style={{ fontWeight: active ? 500 : 400 }}>{s.label}</span>
                  <span className="mute" style={{ fontSize: 10 }}>{active ? '◉' : '○'}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div className="box-h">
            <span>▸ ip</span>
            <span style={{ flex: 1 }} />
            <span className="acc" style={{ textTransform: 'none', fontSize: 11, letterSpacing: 0 }}>
              {(window.SCOPE_PATH || '').split('/').pop() || 'project root'}
            </span>
          </div>
          <div style={{
            padding: '6px 10px', borderBottom: '1px solid var(--line)',
            display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
            background: 'var(--bg-2)',
          }}>
            <span className="mute" style={{ fontSize: 12 }}>dir</span>
            <span className="mute">›</span>
            <span className="acc" style={{ flex: 1, fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 500 }}>
              {(window.SCOPE_PATH || '').split('/')[0] || 'select IP'}
            </span>
            {/* Sort toggle: name (A-Z, dirs first) ↔ recent (mtime DESC).
                Click cycles between the two; the active one is accent-color. */}
            <span
              title={'sort: ' + (fileSort === 'recent'
                ? 'recent (most recently modified first) — click for A→Z'
                : 'A→Z (dirs first) — click for recent')}
              onClick={() => {
                setFileSort(s => s === 'recent' ? 'name' : 'recent');
                window.atlasData.refreshFileTree(window.SCOPE_PATH || '', { recursive: true });
              }}
              style={{
                cursor: 'pointer',
                fontSize: 11,
                padding: '1px 6px',
                borderRadius: 2,
                userSelect: 'none',
                color: fileSort === 'recent' ? 'var(--accent)' : 'var(--fg-mute)',
                border: '1px solid ' + (fileSort === 'recent' ? 'var(--accent)' : 'var(--line)'),
                fontFamily: 'var(--mono)',
              }}
            >{fileSort === 'recent' ? '⏱ recent' : 'A→Z'}</span>
            {/* Expand-all / collapse-all toggle. 'shallow' = top level
                only at root (default — avoids dumping the whole project
                tree); 'deep' = recursive (backend max_depth=4). Persisted
                across reloads via localStorage. */}
            <span
              title={fileExpand === 'deep'
                ? 'expanded — click to collapse all folders'
                : 'top level only — click to expand all folders'}
              onClick={() => {
                setFileExpand(v => v === 'deep' ? 'shallow' : 'deep');
                setCollapsedFileDirs(new Set());
              }}
              style={{
                cursor: 'pointer',
                fontSize: 10,
                padding: '1px 6px',
                borderRadius: 2,
                userSelect: 'none',
                color: fileExpand === 'deep' ? 'var(--accent)' : 'var(--fg-mute)',
                border: '1px solid ' + (fileExpand === 'deep' ? 'var(--accent)' : 'var(--line)'),
                fontFamily: 'var(--mono)',
              }}
            >{fileExpand === 'deep' ? '▾ all' : '▸ all'}</span>
            <span
              title="refresh — pull the latest file list now"
              style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 13,
                       padding: '0 6px', fontWeight: 600, userSelect: 'none' }}
              onClick={() => window.atlasData.refreshFileTree(window.SCOPE_PATH || '', { recursive: true })}
            >↻</span>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
            {window.FILE_TREE.length === 0 && (
              <div className="mute" style={{ padding: '8px 10px', fontSize: 11 }}>
                (empty — select an IP or refresh)
              </div>
            )}
            {/* Sort: 'recent' = mtime DESC (most recent first, ignoring
                dir/file distinction so just-touched files always float
                to the top). 'name' keeps the API's default A→Z, dirs
                first ordering. /api/files already returns mtime per
                entry — sort happens client-side, no backend change. */}
            {(fileSort === 'recent'
              ? [...window.FILE_TREE].sort((a, b) => (b.mtime || 0) - (a.mtime || 0))
              : window.FILE_TREE
            ).filter(n => {
              const relName = String(n.name || '').replace(/^\/+|\/+$/g, '');
              if (!relName) return false;
              if (fileExpand !== 'deep' && (n.depth || 0) > 0) return false;
              const root = String(window.SCOPE_PATH || '').split('/').filter(Boolean)[0] || '';
              const parts = relName.split('/').filter(Boolean);
              for (let idx = 1; idx < parts.length; idx += 1) {
                const ancestor = [root, ...parts.slice(0, idx)].filter(Boolean).join('/');
                if (collapsedFileDirs.has(ancestor)) return false;
              }
              return true;
            }).map((n, i) => {
              const baseScope = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
              const relName = String(n.name || '').replace(/^\/+|\/+$/g, '');
              const fullPath = (baseScope ? `${baseScope}/` : '') + relName;
              const displayName = relName.split('/').filter(Boolean).pop() || relName;
              const dirCollapsed = n.type === 'dir' && (fileExpand !== 'deep' || collapsedFileDirs.has(fullPath));
              const isSelected = n.type === 'file' && previewPath === fullPath;
              return (
                <div key={i}
                  className={(isSelected ? 'frow active' : (n.active ? 'frow active' : 'frow'))}
                  style={{ paddingLeft: 8 + (n.depth || 0) * 14, cursor: 'pointer' }}
                  onClick={() => {
                    if (n.type === 'file') {
                      readAtlasAsyncResource('file', fullPath).catch(() => {});
                      setPreviewPath(fullPath);
                      try { localStorage.setItem('atlasPreviewPath', fullPath); } catch (_) {}
                      setMainTab('split');
                    } else {
                      const wasDeep = fileExpand === 'deep';
                      if (!wasDeep) setFileExpand('deep');
                      setCollapsedFileDirs(prev => {
                        const next = new Set(prev);
                        if (!wasDeep || next.has(fullPath)) next.delete(fullPath);
                        else next.add(fullPath);
                        return next;
                      });
                    }
                  }}
                  onMouseEnter={() => {
                    if (n.type === 'file') readAtlasAsyncResource('file', fullPath).catch(() => {});
                  }}
                  title={fullPath + (n.type === 'file' ? ' (click to preview)' : ' (click to fold/unfold)')}
                >
                  <span className="fr-icon">{n.type === 'dir' ? (dirCollapsed ? '▸' : '▾') : '◆'}</span>
                  <span className="trunc">{n.type === 'dir' ? <span className="dim">{displayName}/</span> : displayName}</span>
                  <span className="mute" style={{ fontSize: 10 }}>{n.size}</span>
                </div>
              );
            })}
          </div>
          {/* file tree footer */}
          <div style={{ borderTop: '1px solid var(--line)', padding: '6px 10px', fontSize: 10, color: 'var(--fg-mute)', display: 'flex', gap: 10 }}>
            <span>{window.FILE_TREE.length} entries</span>
            <span className="mute">·</span>
            <span className="mute" title="Auto-refreshes on tool_result + every 5s">
              {window.FILE_TREE_LAST_REFRESH
                ? new Date(window.FILE_TREE_LAST_REFRESH).toLocaleTimeString()
                : 'loading…'}
            </span>
            <span style={{ flex: 1 }} />
            <span className="mute"
              title={window.CONTEXT?.projectRoot || ''}>
              {window.SCOPE_PATH
                ? window.SCOPE_PATH
                : (window.CONTEXT && window.CONTEXT.projectRoot
                    ? window.CONTEXT.projectRoot.split('/').pop()
                    : 'project root')}
            </span>
          </div>
        </div>
        {/* Conversation hydration mode selector — sits below the file
            tree, left of the chat input. Picks which on-disk source
            populates the chat feed on (re)load:
              • conversation — recent rolling window from conversation.json
              • full         — every message from full_conversation.json
              • recent 50    — last 50 messages of full_conversation.json
            Default 'conversation'. Saved in localStorage. */}
        <ConvModeSelector />
      </div>
      ) : (
        <div /> /* collapsed — empty grid cell so the 5-track grid stays aligned */
      )}

      {/* LEFT ↔ CENTER splitter — keep visible at 0px so collapsed panels can reopen. */}
      <Splitter width={leftW} side="left" onResize={setLeftW} onToggle={toggleLeft} />

      {/* CENTER — workflow-specific tabs can claim the first screen
          (sim_debug → debug, coverage → coverage); the shared chat /
          preview / Q&A tabs stay available where appropriate. */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        {intent === 'plan' && (
          <div style={{
            padding: '6px 14px', border: '1px solid var(--warn)',
            background: 'color-mix(in oklch, var(--warn) 12%, transparent)',
            color: 'var(--warn)', fontSize: 11, letterSpacing: '0.06em',
            display: 'flex', alignItems: 'center', gap: 10, borderRadius: 2,
          }}>
            <span style={{ fontWeight: 700, textTransform: 'uppercase' }}>◐ Plan mode</span>
            <span style={{ flex: 1 }}>Read-only · agent will analyze and propose, but will not write or run any tools.</span>
            <button className="btn" onClick={() => switchIntent('normal')}
              style={{ borderColor: 'var(--warn)', color: 'var(--warn)', fontSize: 10 }}>
              Apply &amp; switch to Normal <Kbd>⌘ ↵</Kbd>
            </button>
          </div>
        )}
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div className="box-h">
            {/* Tab strip — order: chat · ssot · Q&A · split view · full view.
                "full view" is the file-only pane (was "preview").
                "split view" puts chat and the preview side by side. */}
            {showSimSummaryTab && (
              <span
                className="tab-chip"
                onClick={() => setMainTab('sim_summary')}
                title="SIM summary: scenarios, pass/fail, scoreboard"
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2,
                  color: mainTab === 'sim_summary' ? 'var(--accent)' : 'var(--fg-mute)',
                  background: mainTab === 'sim_summary' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'sim_summary' ? 'var(--accent)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >sim summary</span>
            )}
            {showDebugTab && (
              <span
                className="tab-chip"
                onClick={() => setMainTab('debug')}
                title="Debug view: hierarchy, source, waveform"
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2,
                  color: mainTab === 'debug' ? 'var(--accent)' : 'var(--fg-mute)',
                  background: mainTab === 'debug' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'debug' ? 'var(--accent)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >debug</span>
            )}
            {showCoverageTab && (
              <span
                className="tab-chip"
                onClick={() => setMainTab('coverage')}
                title="Coverage view: SSOT goals, metrics, files, and gaps"
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2,
                  color: mainTab === 'coverage' ? 'var(--accent)' : 'var(--fg-mute)',
                  background: mainTab === 'coverage' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'coverage' ? 'var(--accent)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >coverage</span>
            )}
            {showWorkflowReportTab && (
              <span
                className="tab-chip"
                onClick={() => setMainTab('workflow_report')}
                title={workflowReportMeta.title}
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2,
                  color: mainTab === 'workflow_report' ? 'var(--accent)' : 'var(--fg-mute)',
                  background: mainTab === 'workflow_report' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'workflow_report' ? 'var(--accent)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >{workflowReportMeta.label}</span>
            )}
            {showQaTab && workflow === 'ssot-gen' && (
              <span
                className="tab-chip"
                onClick={() => setMainTab('qa')}
                title={pendingQcard ? 'Answer the agent\'s questions' : 'SSOT Q&A session'}
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2,
                  position: 'relative',
                  color: mainTab === 'qa' ? 'var(--warn)' : (pendingQcard ? 'var(--warn)' : 'var(--fg-mute)'),
                  background: mainTab === 'qa' ? 'color-mix(in oklch, var(--warn) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'qa' ? 'var(--warn)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >
                Q&amp;A Session
                {pendingQcard && mainTab !== 'qa' && (
                  <span style={{
                    position: 'absolute', top: 1, right: 1,
                    width: 6, height: 6, borderRadius: '50%',
                    background: 'var(--warn)',
                    animation: 'pulse 1.5s infinite',
                  }} />
                )}
              </span>
            )}
            {showSsotChecklistTab && (
              <span
                className="tab-chip"
                onClick={() => setMainTab('checklist')}
                title="SSOT checklist: import docs, see missing items, and check RTL readiness"
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                  color: mainTab === 'checklist' ? 'var(--cyan)' : 'var(--fg-mute)',
                  background: mainTab === 'checklist' ? 'color-mix(in oklch, var(--cyan) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'checklist' ? 'var(--cyan)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >Check List</span>
            )}
            <span
              className="tab-chip"
              onClick={() => setMainTab('chat')}
              style={{
                cursor: 'pointer', padding: '2px 8px', borderRadius: 2,
                marginLeft: (showDebugTab || showCoverageTab || showWorkflowReportTab) ? 4 : 0,
                color: mainTab === 'chat' ? 'var(--accent)' : 'var(--fg-mute)',
                background: mainTab === 'chat' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                border: '1px solid ' + (mainTab === 'chat' ? 'var(--accent)' : 'transparent'),
                fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
              }}
            >chat</span>
            {showSsotTab && (
              <span
                className="tab-chip"
                onClick={() => setMainTab('ssot')}
                title="Review SSOT by section"
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                  color: mainTab === 'ssot' ? 'var(--magenta)' : 'var(--fg-mute)',
                  background: mainTab === 'ssot' ? 'color-mix(in oklch, var(--magenta) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'ssot' ? 'var(--magenta)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >ssot</span>
            )}
            {showQaTab && workflow !== 'ssot-gen' && (
              <span
                className="tab-chip"
                onClick={() => setMainTab('qa')}
                title={pendingQcard ? 'Answer the agent\'s questions' : 'No pending questions'}
                style={{
                  cursor: 'pointer',
                  padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                  position: 'relative',
                  color: mainTab === 'qa' ? 'var(--warn)' : (pendingQcard ? 'var(--warn)' : 'var(--fg-mute)'),
                  background: mainTab === 'qa' ? 'color-mix(in oklch, var(--warn) 14%, transparent)' : 'transparent',
                  border: '1px solid ' + (mainTab === 'qa' ? 'var(--warn)' : 'transparent'),
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
                }}
              >
                Q&amp;A
                {pendingQcard && mainTab !== 'qa' && (
                  <span style={{
                    position: 'absolute', top: 1, right: 1,
                    width: 6, height: 6, borderRadius: '50%',
                    background: 'var(--warn)',
                    animation: 'pulse 1.5s infinite',
                  }} />
                )}
              </span>
            )}
            <span
              className="tab-chip"
              onClick={() => setMainTab('split')}
              title="Show chat and preview side by side"
              style={{
                cursor: 'pointer',
                padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                color: mainTab === 'split' ? 'var(--accent)' : 'var(--fg-mute)',
                background: mainTab === 'split' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                border: '1px solid ' + (mainTab === 'split' ? 'var(--accent)' : 'transparent'),
                fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
              }}
            >split view</span>
            <span
              className="tab-chip"
              onClick={() => setMainTab('preview')}
              title={previewPath ? 'Full view: ' + previewPath : 'Open the preview pane in full view'}
              style={{
                cursor: 'pointer',
                padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                color: mainTab === 'preview' ? 'var(--accent)' : 'var(--fg-mute)',
                background: mainTab === 'preview' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                border: '1px solid ' + (mainTab === 'preview' ? 'var(--accent)' : 'transparent'),
                fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
              }}
            >full view</span>
            <span
              className="tab-chip"
              onClick={() => setMainTab('git')}
              title="Git: per-IP commit history graph + revert"
              style={{
                cursor: 'pointer',
                padding: '2px 8px', borderRadius: 2, marginLeft: 4,
                color: mainTab === 'git' ? 'var(--accent)' : 'var(--fg-mute)',
                background: mainTab === 'git' ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                border: '1px solid ' + (mainTab === 'git' ? 'var(--accent)' : 'transparent'),
                fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11,
              }}
            >git</span>
            <span className="mute" style={{ margin: '0 6px' }}>·</span>
            {mainTab === 'chat' ? (
              // Everything in the previous chain (intent badge, workflow
              // chip, SessionSwitcher, peer count) duplicated UI already
              // present in the top dir-select bar (SESSION_ID, IP_ID,
              // WORKFLOW dropdowns) and the left-rail mode toggle.
              null
            ) : mainTab === 'split' ? (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}
                    title={previewPath || ''}>
                chat + {isSsotYamlPath(previewPath) ? 'ssot' : 'preview'} · {previewPath || '(no file selected)'}
              </span>
            ) : mainTab === 'ssot' ? (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}>
                SSOT section review
              </span>
            ) : mainTab === 'checklist' ? (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}>
                SSOT checklist · import · missing items · RTL readiness
              </span>
            ) : mainTab === 'sim_summary' ? (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}>
                sim_debug summary · scenarios · scoreboard
              </span>
            ) : mainTab === 'debug' ? (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}>
                sim_debug hierarchy · source · wave
              </span>
            ) : mainTab === 'coverage' ? (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}>
                coverage workflow · SSOT goals · gaps
              </span>
            ) : mainTab === 'workflow_report' ? (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}>
                {workflowReportMeta ? workflowReportMeta.title : 'workflow report'} · {activeIp || 'no IP'}
              </span>
            ) : (
              <span className="mute trunc" style={{ fontSize: 11, fontFamily: 'var(--mono)', maxWidth: 380 }}
                    title={previewPath || ''}>
                {previewPath || '(no file selected)'}
              </span>
            )}
            <span style={{ flex: 1 }} />
            {/* top-right streaming/ready indicator removed — the
                "Running / End of loop / Waiting on you" pill above the
                input row already conveys this state, and louder, so two
                redundant indicators just add noise to the tab header. */}
            {(mainTab === 'preview' || mainTab === 'split' || mainTab === 'ssot' || mainTab === 'checklist') && (
              <span style={{ fontSize: 10 }}>
                <span className="mute" style={{ marginRight: 8 }}>{mainTab === 'split' ? 'chat only' : 'back to chat'}</span>
                <span onClick={() => setMainTab('chat')} className="acc"
                      style={{ cursor: 'pointer', padding: '2px 6px',
                               border: '1px solid var(--accent)', borderRadius: 2 }}>↵</span>
              </span>
            )}
          </div>
          {mainTab === 'coverage' ? (
            window.Coverage ? (
              <ErrorBoundary label="Coverage">
                <window.Coverage />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                Coverage · loading…
              </div>
            )
          ) : mainTab === 'workflow_report' ? (
            <WorkflowReportPane workflow={workflow} activeIp={activeIp} />
          ) : mainTab === 'checklist' ? (
            <SsotQaBoard
              data={ssotQaBoardData}
              sessions={ssotQaSessions}
              activeSession={currentSession}
              uiLang={uiLang}
              onSelectSession={activateSsotQaSession}
              onBack={() => setMainTab('chat')}
              onRefresh={() => { refreshSsotQa(); refreshSsotQaSessions(); }}
              onRunCommand={submitMsg}
              showChecklist={true}
              checklistOnly={true}
            />
          ) : mainTab === 'chat' ? (
            renderChatPane()
          ) : (mainTab === 'split' || mainTab === 'preview') ? (() => {
            // Unified split/full-view layout — chat | splitter | preview.
            // splitRightW is the persisted preview-pane width. The chat
            // pane takes the remaining space, so dragging the handle gives
            // the user direct left/right control instead of a fixed 50/50.
            const fullView = mainTab === 'preview';
            const splitColumns = fullView
              ? '0px 4px minmax(0, 1fr)'
              : `minmax(260px, 1fr) 4px minmax(300px, ${splitRightW}px)`;
            return (
              <div style={{
                flex: 1, minHeight: 0, display: 'grid',
                gridTemplateColumns: splitColumns,
                transition: fullView ? 'grid-template-columns 0.35s cubic-bezier(0.2, 0.8, 0.2, 1)' : 'none',
                overflow: 'hidden',
              }}>
                <div style={{
                  minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column',
                  overflow: 'hidden',
                  visibility: fullView ? 'hidden' : 'visible',
                }}>
                  <div style={{
                    padding: '4px 10px', borderBottom: '1px solid var(--line)',
                    color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10,
                    letterSpacing: '0.06em', textTransform: 'uppercase',
                  }}>
                    chat stream
                  </div>
                  {renderChatPane({ padding: '10px 12px' })}
                </div>
                <div style={{
                  visibility: fullView ? 'hidden' : 'visible',
                  pointerEvents: fullView ? 'none' : 'auto',
                }}>
                  <Splitter
                    width={splitRightW}
                    side="right"
                    onResize={setSplitRightW}
                    title="drag to resize chat / preview split"
                  />
                </div>
                <div style={{ minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                  {gitShow ? (
                    <GitDiffPane
                      sha={gitShow.sha}
                      ip={gitShow.ip}
                      subject={gitShow.subject}
                      onClose={() => setGitShow(null)}
                    />
                  ) : isSsotYamlPath(previewPath) ? (
                    <SsotReviewPane uiLang={uiLang} initialPath={previewPath} onBack={() => setMainTab('chat')} />
                  ) : (
                    <PreviewPane path={previewPath} onClose={() => setMainTab('chat')} />
                  )}
                </div>
              </div>
            );
          })() : mainTab === 'ssot' ? (
            <SsotReviewPane
              uiLang={uiLang}
              initialPath={isSsotYamlPath(previewPath) ? previewPath : ''}
              onBack={() => setMainTab('chat')}
            />
          ) : mainTab === 'sim_summary' ? (
            window.SimDebug ? (
              <ErrorBoundary label="SimSummary">
                <window.SimDebug key="sim-summary-view" view="summary" />
              </ErrorBoundary>
            ) : window.DebugTab ? (
              <ErrorBoundary label="Debug">
                <window.DebugTab
                  ip={(() => {
                    const segs = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
                    return segs.length >= 2 ? segs[1] : '';
                  })()}
                  onOpenSource={(p) => { setPreviewPath(p); }}
                />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                SIM Summary · loading…
              </div>
            )
          ) : mainTab === 'debug' ? (
            // Prefer the full SimDebug pane (wave viewer + RTL hierarchy
            // + source folds + cocotb tree, all wired to /api/vcd/list +
            // /api/vcd/raw + window.parseVCD) when it's loaded. Fall back
            // to the slim scenario+artifact DebugTab when SimDebug isn't
            // available (e.g. dev build without sim-debug.jsx). Last
            // resort: a "loading…" placeholder.
            window.SimDebug ? (
              <ErrorBoundary label="SimDebug">
                <window.SimDebug key="sim-debug-view" view="debug" initialTab="wave" />
              </ErrorBoundary>
            ) : window.DebugTab ? (
              <ErrorBoundary label="Debug">
                <window.DebugTab
                  ip={(() => {
                    const segs = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
                    return segs.length >= 2 ? segs[1] : '';
                  })()}
                  onOpenSource={(p) => { setPreviewPath(p); }}
                />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                Debug · loading…
              </div>
            )
          ) : mainTab === 'git' ? (
            window.GitTab ? (
              <ErrorBoundary label="Git">
                <window.GitTab initialIp={activeIp} />
              </ErrorBoundary>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
                Git · loading…
              </div>
            )
            ) : (
            /* mainTab === 'qa' — SSOT-GEN QA board or active ask_user */
            <div style={{
              flex: 1,
              minHeight: 0,
              overflow: pendingQcard ? 'auto' : 'hidden',
              padding: pendingQcard ? '14px 18px' : 0,
              display: 'flex',
              flexDirection: 'column',
            }}>
              {pendingQcard ? (
                <AskUserPrompt
                  flowId={pendingQcard.flowId}
                  state={qaState[pendingQcard.flowId]}
                  sel={askSel}
                  intent={intent}
                  fullHeight={true}
                  onSel={setAskSel}
                  onToggle={toggleOpt}
                  onCustom={setCustom}
                  onSubmit={submitCard}
                  onChat={() => { setMainTab('chat'); setAskSel(0); inputRef.current?.focus(); }}
                  onSetTab={setActiveTab}
                  onAdvance={advanceBatchedQuestion}
                />
              ) : (
                <SsotQaBoard
                  data={ssotQaBoardData}
                  sessions={ssotQaSessions}
                  activeSession={currentSession}
                  uiLang={uiLang}
                  onSelectSession={activateSsotQaSession}
                  onBack={() => setMainTab('chat')}
                  onRefresh={() => { refreshSsotQa(); refreshSsotQaSessions(); }}
                  onRunCommand={submitMsg}
                  onUsePending={(_, text, opts = {}) => {
                    setInput(text || '');
                    if (opts?.focusChat !== false) {
                      setMainTab('chat');
                      setTimeout(() => inputRef.current?.focus(), 0);
                    }
                  }}
                  onSubmitPending={(bundle, text) => {
                    const payload = String(text || '').trim();
                    if (!payload) return;
                    const items = Array.isArray(bundle) ? bundle : [];
                    setInput('');
                    // 1) Mirror submitted text into chat feed for traceability.
                    setFeed(f => [...f, { kind: 'user', text: payload, createdAt: Date.now() }]);
                    let session = 'default';
                    try {
                      session = normalizeUiSession(window.ACTIVE_SESSION || '') || 'default';
                    } catch (_) {}
                    // 2) Persist answered items into qa.json via the backend.
                    try {
                      const ip = ssotQa?.ip || activeIp || '';
                      if (ip && items.length) {
                        const qaItems = items.map(({ item, draft }) => {
                          const selected = (draft?.opts || []).filter(o => o.selected).map(o => o.label);
                          const customNote = String(draft?.custom || '').trim();
                          return {
                            // flow_id is required for the backend to UPDATE the
                            // existing pending entry in qa.json instead of
                            // creating a new approved entry that leaves the
                            // pending one stranded.
                            flow_id: item?.flow_id || '',
                            decision_key: item?.decision_key || item?.source || item?.id || '',
                            decision_label: item?.decision_label || '',
                            section_id: item?.section_id || item?.section || '',
                            section_title: item?.section_title || '',
                            question: item?.question || '',
                            subtitle: item?.subtitle || '',
                            selected,
                            answer: customNote || selected.join('; '),
                          };
                        }).filter(x => x.decision_key);
                        if (qaItems.length) {
                          fetch('/api/ssot/qa/answer', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              ip,
                              session,
                              items: qaItems,
                              submitted_text: payload,
                            }),
                          })
                            .then(r => r.ok ? r.json() : null)
                            .then(_resp => {
                              try { refreshSsotQa?.(); } catch (_) {}
                            })
                            .catch(() => {});
                        }
                      }
                    } catch (_) {}
                    // 3) Send the prompt to the backend for LLM processing.
                    try {
                      window.backend?.send?.({
                        type: 'prompt',
                        text: payload,
                        session,
                        ui_lang: window.ATLAS_UI_LANG || 'ko',
                      });
                    } catch (_) {}
                    setMainTab('chat');
                  }}
                />
              )}
            </div>
          )}
        </div>

        {/* prompt — breathing room below so the input row isn't flush
            with the bottom edge of the viewport */}
        <div style={{ position: 'relative', paddingBottom: 24 }}>
          {showAt && atQuery && (
            <div className="slash-menu fade-in" style={{ maxHeight: 280, overflowY: 'auto' }}>
              <div style={{ padding: '6px 12px', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: 'var(--cyan)' }}>
                  {atQuery.parentAbs ? atQuery.parentAbs + '/' : '(project root)'}
                </span>
                <span style={{ flex: 1 }} />
                <span>{fileMatches.length} match{fileMatches.length === 1 ? '' : 'es'}</span>
                <span className="mute">·</span>
                <span><Kbd>↑↓</Kbd> nav · <Kbd>↵</Kbd> select · <Kbd>Esc</Kbd> close</span>
              </div>
              {fileMatches.length === 0 ? (
                <div style={{ padding: '10px 12px', fontSize: 11, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                  {atDirEntries.length === 0 ? 'loading…' : `no entries match "${atQuery.filter}"`}
                </div>
              ) : fileMatches.map((f, i) => (
                <div key={i} className={`slash-item ${i === atSel ? 'sel' : ''}`}
                  onClick={() => acceptAtCompletion(f)}
                  onMouseEnter={() => setAtSel(i)}
                  style={{
                    display: 'grid', gridTemplateColumns: '20px 1fr auto',
                    gap: 8, padding: '5px 12px',
                    background: i === atSel ? 'color-mix(in oklch, var(--accent) 18%, transparent)' : 'transparent',
                    borderLeft: i === atSel ? '2px solid var(--accent)' : '2px solid transparent',
                    cursor: 'pointer',
                  }}>
                  <span style={{ color: f.type === 'dir' ? 'var(--cyan)' : 'var(--accent)' }}>
                    {f.type === 'dir' ? '▸' : '◆'}
                  </span>
                  <span style={{ fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 12 }}>
                    {f.name}{f.type === 'dir' ? '/' : ''}
                  </span>
                  <span className="mute" style={{ fontSize: 10 }}>
                    {f.type === 'dir' ? 'dir' : (f.size != null ? (f.size < 1024 ? f.size + 'B' : (f.size/1024).toFixed(1) + 'K') : '')}
                  </span>
                </div>
              ))}
            </div>
          )}
          {showSlash && filtered.length > 0 && (
            <div className="slash-menu fade-in">
              <div style={{ padding: '6px 12px', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)' }}>
                {filtered.length} command{filtered.length === 1 ? '' : 's'} · <Kbd>↑↓</Kbd> nav · <Kbd>Tab</Kbd> complete · <Kbd>↵</Kbd> run
              </div>
              {filtered.map((c, i) => (
                <div key={c.cmd} className={`slash-item ${i === slashSel ? 'sel' : ''}`}
                  onClick={() => { submitMsg(c.cmd); }}
                  onMouseEnter={() => setSlashSel(i)}>
                  <span className="si-cmd">{c.cmd}</span>
                  <span className="si-alias">{c.alias}</span>
                  <span className="si-desc">{c.desc}</span>
                </div>
              ))}
            </div>
          )}
          {/* Status strip directly above the input — at-a-glance state
              the user doesn't have to look up at the chat header for. */}
          {(() => {
            const backendDown = !window.backend || backendState === 'missing' ||
              backendState === 'closed' || backendState === 'error';
            const s = backendDown
              ? { icon: '!', text: backendState === 'missing' ? 'Backend adapter missing' : 'Backend disconnected', color: 'var(--err)', bg: 'color-mix(in oklch, var(--err) 12%, transparent)' }
              : backendState === 'connecting'
                ? { icon: '·', text: 'Backend connecting', color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 10%, transparent)' }
                : pendingQcard
              ? { icon: '⏸', text: 'Waiting on you · answer the ask_user above', color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)' }
              : streaming
                ? { icon: '◉', text: 'Agent running', color: 'var(--accent)', bg: 'color-mix(in oklch, var(--accent) 16%, transparent)', spin: true }
                : ssotApproval && ssotApproval.approved
                  ? { icon: '◆', text: `SSOT approved · run ${ssotApproval.generate_cmd || `/to-ssot ${ssotApproval.ip}`}`, color: 'var(--ok)', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)' }
                  : ssotApproval
                    ? { icon: '◆', text: `SSOT plan ready · approve ${ssotApproval.ip} before YAML write`, color: 'var(--warn)', bg: 'color-mix(in oklch, var(--warn) 14%, transparent)' }
                : { icon: '✓', text: 'End of loop · agent ready', color: 'var(--ok)', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)' };
            return (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '4px 12px', marginBottom: 4,
                fontSize: 11, fontFamily: 'var(--mono)',
                color: s.color, background: s.bg,
                border: `1px solid ${s.color}`, borderRadius: 2,
                letterSpacing: '0.04em',
              }}>
                <span style={{ fontWeight: 700 }}>
                  {s.icon}{s.spin ? <span className="ascii-spin" style={{ marginLeft: 2 }} /> : null}
                </span>
                <span>{s.text}</span>
              </div>
            );
          })()}
          {/* Bottom prompt area — three rendering modes:
              1. classic + pending qcard      → inline AskUserPrompt unless Q&A tab owns it
              2. tabbed   + on Q&A tab        → hidden (AskUserPrompt lives in tab body)
              3. tabbed   + chat/preview tab  → hint to switch to Q&A tab (not input)
              4. anything + no pending qcard  → normal input row */}
          {pendingQcard && centerLayout === 'classic' && mainTab !== 'qa' ? (
            <AskUserPrompt
              flowId={pendingQcard.flowId}
              state={qaState[pendingQcard.flowId]}
              sel={askSel}
              intent={intent}
              onSel={setAskSel}
              onToggle={toggleOpt}
              onCustom={setCustom}
              onSubmit={submitCard}
              onChat={() => { setAskSel(0); inputRef.current?.focus(); }}
              onSetTab={setActiveTab}
              onAdvance={advanceBatchedQuestion}
            />
          ) : pendingQcard && centerLayout === 'classic' && mainTab === 'qa' ? (
            renderPromptRow()
          ) : pendingQcard && centerLayout === 'tabbed' && mainTab !== 'qa' ? (
            <>
              <div
                onClick={() => setMainTab('qa')}
                className="ask-feed-placeholder"
                style={{
                  padding: '8px 12px',
                  marginBottom: 6,
                  border: '1px dashed var(--warn)',
                  borderRadius: 2,
                  background: 'color-mix(in oklch, var(--warn) 10%, transparent)',
                  color: 'var(--warn)',
                  fontSize: 12,
                  cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
                title="Click to open the Q&A tab"
              >
                <span>⏸</span>
                <span>Agent is waiting on you · type an answer below, or open the <b>Q&amp;A</b> tab for the full card</span>
                <span style={{ flex: 1 }} />
                <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>→ Q&amp;A</span>
              </div>
              {renderPromptRow()}
            </>
          ) : pendingQcard && centerLayout === 'tabbed' && mainTab === 'qa' ? (
            renderPromptRow() /* AskUserPrompt is rendered inside the tab body above */
          ) : (
            renderPromptRow()
          )}
        </div>

        {/* hotkey footer removed — chips were rendered in --fg-mute on
            --bg-2 so most users couldn't read them, and the App-level
            <StatusBar/> below already exposes the model + the same
            shift+tab/⌘+/ hints. */}
      </div>

      {/* CENTER ↔ RIGHT splitter — keep visible at 0px so collapsed panels can reopen. */}
      <Splitter width={rightW} side="right" onResize={setRightW} onToggle={toggleRight} />

      {/* RIGHT — ATLAS status + SSOT/Todo/Diff (hidden when sim_debug or collapsed) */}
      {effRightW > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden', minWidth: 0 }}>
        <AgentStatusPanel intent={intent} workflow={workflow}
                          onCollapse={toggleRight} />
        <div className="box" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="box-h" style={{ padding: 0 }}>
            <RightTab id="todo" cur={rightTab} onTab={setRightTab}>Todo</RightTab>
            <RightTab id="progress" cur={rightTab} onTab={setRightTab}>Progress</RightTab>
            <RightTab id="chat" cur={rightTab} onTab={setRightTab}>Chat</RightTab>
            <RightTab id="git"  cur={rightTab} onTab={setRightTab}>Git</RightTab>
          </div>
          {rightTab === 'progress' && <ProgressPanel />}
          {rightTab === 'todo' && <TodoPanel />}
          {rightTab === 'chat' && <OrchestratorChatPanel activeIp={activeIp} />}
          {rightTab === 'git'  && <GitPanel activeIp={activeIp} />}
        </div>
      </div>
      ) : (
        <div /> /* collapsed — empty grid cell to keep the 5-track grid aligned */
      )}

      {openFile && <FileViewer name={openFile} onClose={() => setOpenFile(null)} />}
    </div>
  );
};

const RightTab = ({ id, cur, onTab, children }) => (
  <span onClick={() => onTab(id)} style={{
    cursor: 'pointer', padding: '10px 14px', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
    color: cur === id ? 'var(--fg)' : 'var(--fg-mute)',
    borderBottom: cur === id ? `2px solid var(--accent)` : '2px solid transparent',
    background: cur === id ? 'var(--bg-2)' : 'transparent',
    flex: 1, textAlign: 'center',
  }}>{children}</span>
);

// ── Feed entry: dispatcher ─────────────────────────────────────────
const CollapsibleThought = ({ text, summaryMode = true }) => {
  // Default state: show only the LAST ~3 lines, dimmed. Reasoning is
  // valuable as a tail (what the agent just decided), but the early
  // chain-of-thought lines are usually scaffolding the user doesn't
  // need to read. Visual clamp also catches long wrapped lines.
  const TAIL_LINES = 3;
  const [open, setOpen] = React.useState(!summaryMode);
  const lines = text.split('\n').filter(l => l.trim());
  const tail = lines.slice(-TAIL_LINES);
  const hidden = Math.max(0, lines.length - TAIL_LINES);
  const collapsed = summaryMode && !open;
  return (
    <div
      className="react-block thought"
      style={{ cursor: 'pointer', opacity: 0.62 /* dim */ }}
      onClick={() => setOpen(o => !o)}
      title={collapsed ? 'click to expand full reasoning' : 'click to collapse'}
    >
      <span className="rb-tag">
        thought{lines.length > 1 && ` (${lines.length})`}
        {collapsed && hidden > 0 && (
          <span className="mute" style={{ marginLeft: 6, fontSize: 10, fontWeight: 400 }}>
            · +{hidden} earlier · click to expand
          </span>
        )}
      </span>
      <span style={{
        whiteSpace: 'pre-wrap',
        display: collapsed ? '-webkit-box' : 'block',
        WebkitBoxOrient: collapsed ? 'vertical' : undefined,
        WebkitLineClamp: collapsed ? TAIL_LINES : undefined,
        overflow: collapsed ? 'hidden' : 'visible',
      }}>
        {collapsed ? tail.join('\n') : text}
      </span>
    </div>
  );
};

// Tool-call observation card — collapsible by default, click to expand.
// Replaces the previous always-expanded <pre> block that drowned the
// chat in tool output. Header shows tool name + first line summary +
// expand chevron; body (full text + diff coloring) stays hidden until
// the user clicks. Inline (single-line) results are shown in full as
// they're already brief.
//
// Optional `embedded` prop: when true, render WITHOUT the outer
// react-block wrapper (used by ToolCard which provides its own
// outer container).
const ObsCard = ({ entry, embedded, summaryMode = true }) => {
  // Replace/edit tools default to OPEN even in summary mode so the user
  // can see the actual diff without an extra click. Other tools stay
  // collapsed in summary mode.
  const isReplaceTool = entry?.tool && /^(replace_in_file|replace_lines|write_file|edit|patch|update_file)/i.test(entry.tool);
  const [open, setOpen] = React.useState(!summaryMode || isReplaceTool);
  React.useEffect(() => {
    setOpen(!summaryMode || isReplaceTool);
  }, [summaryMode, isReplaceTool]);
  let txt = summaryMode ? _cleanTodoToolText(entry.text || '', entry.tool) : (entry.text || '');
  // Strip ANSI escape sequences leaked from terminal-style backends
  // (e.g. `\x1b[1m`, `\x1b[38;5;71m`, `\x1b[0m`) so they don't show as
  // raw `[1m`, `[96m`, etc. in the chat feed.
  txt = txt.replace(/\x1b\[[\d;]*m/g, '');

  const lines = txt.split('\n');
  const isMulti = lines.length > 1;
  const firstLine = lines[0] || '(empty)';
  const lineCount = lines.length;

  // Diff coloring — opt in by tool name or "Added N, removed M" header.
  const looksLikeDiff = /(^|\n)\s*⎿?\s*Added \d+ lines?,? removed \d+ lines?/.test(txt)
                     || (entry.tool && /^(replace_in_file|write_file|edit|patch)/i.test(entry.tool));

  const renderMarkdownBody = () => (
    <div
      className="md-agent md-tool-result"
      dangerouslySetInnerHTML={{ __html: _markdownHtml(txt) }}
      ref={_postProcessMarkdownNode}
    />
  );
  const useMarkdownResult = summaryMode && _isWorkflowResultTool(entry.tool);

  // Status detection — leading ✓/✗ badge so errors stand out
  const status = _obsStatus(txt);
  const statusBadge = status === 'err' ? <span style={{ color: '#f85149' }}>✗</span>
                    : status === 'ok'  ? <span style={{ color: '#3fb950' }}>✓</span>
                    : null;

  // Wrapper element: `embedded=true` → no outer react-block (used inside ToolCard).
  const Wrapper = embedded ? React.Fragment : 'div';
  const wrapperProps = embedded ? {} : { className: 'react-block obs has-hover-affordance', style: { position: 'relative' } };

  // Single-line results: show inline (no toggle, already compact).
  if (!isMulti) {
    return (
      <Wrapper {...wrapperProps}>
        {!embedded && <CopyBtn text={txt} />}
        <span className="rb-tag">{embedded ? '' : 'obs'}{entry.tool && !embedded ? ` · ${entry.tool}` : ''}</span>
        {statusBadge && <span style={{ marginRight: 6 }}>{statusBadge}</span>}
        <span>{txt}{entry.truncated ? ' …[truncated]' : ''}</span>
      </Wrapper>
    );
  }

  // Multi-line: collapsible header + hidden body. When embedded inside
  // a ToolCard, the parent already shows the line count + arrow on its
  // own clickable head, so rendering another header here would force
  // the user to click twice ("first row to peek, second to expand").
  // Skip the inner header in embedded mode and just render the body.
  return (
    <Wrapper {...wrapperProps}>
      {!embedded && <CopyBtn text={txt} />}
      {!embedded ? (
        <div
          onClick={() => setOpen(o => !o)}
          title={open ? 'click to collapse' : 'click to expand full result'}
          style={{
            display: 'flex', alignItems: 'baseline', gap: 8,
            cursor: 'pointer', userSelect: 'none',
          }}
        >
          <span className="rb-tag">obs{entry.tool ? ` · ${entry.tool}` : ''}</span>
          {statusBadge && <span style={{ fontSize: 12 }}>{statusBadge}</span>}
          <span style={{ flex: 1 }} />
          <span className="mute" style={{ fontSize: 'var(--ui-small-font-size)' }}>
            {lineCount} line{lineCount === 1 ? '' : 's'}
            {entry.truncated ? ' · truncated' : ''}
          </span>
          <span className="mute" style={{ fontSize: 'var(--ui-control-font-size)' }}>{open ? '▾' : '▸'}</span>
        </div>
      ) : null}
      {(embedded || open) && (
        looksLikeDiff || !useMarkdownResult ? (
          looksLikeDiff ? (
            <DiffOutputPre text={txt} tool={entry.tool} truncated={entry.truncated} />
          ) : (
            <ToolOutputPre text={txt} tool={entry.tool} truncated={entry.truncated} />
          )
        ) : (
          <>
            {renderMarkdownBody()}
            {entry.truncated ? <div className="mute" style={{ fontSize: 10 }}>…[truncated]</div> : null}
          </>
        )
      )}
    </Wrapper>
  );
};

// ToolCard: pairs an action entry with its obs entry into a single
// connected card with tool-themed left border + glyph + status badge.
// Either half can be missing (action-only when blocked, obs-only is
// uncommon but handled).
const _ToolCardRaw = ({ action, obs, summaryMode = true }) => {
  const tool = (action && action.tool) || (obs && obs.tool) || '';
  const theme = _toolTheme(tool);
  // If the obs indicates an error, override the border to red so the
  // eye finds it. Otherwise use the tool theme color.
  const obsTextRaw = obs ? (summaryMode ? _cleanTodoToolText(obs.text || '', obs.tool) : (obs.text || '')) : '';
  const obsText = obsTextRaw.replace(/\x1b\[[\d;]*m/g, '');
  const status = obs ? _obsStatus(obsText) : 'neutral';
  const borderColor = status === 'err' ? '#f85149' : theme.color;
  let argsText = action && action.text ? action.text.replace(/^▶\s*/, '').replace(new RegExp('^' + tool + '\\s*'), '') : '';
  // Replace/write/edit tools dump the new file content into args, which
  // produces a noisy single-line preview next to the tool name (just
  // the first 80 chars of a 500-line `===========\n//comment...` blob).
  // The diff body shows the actual change, so the header only needs
  // the file path. Heuristics: pull `path="..."` / `path: '...'`
  // / first .sv|.v|.svh|.yaml|.json|.md path-like token, fall back to
  // empty string when nothing recognizable shows up.
  if (tool && /^(replace_in_file|replace_lines|write_file|edit|patch|update_file)/i.test(tool)) {
    const pathMatch = argsText.match(/path\s*[:=]\s*["']([^"']+)["']/i)
      || argsText.match(/^\s*["']([^"']+\.(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl))["']/i)
      || argsText.match(/^\s*([^\s"',{}\[\]]+\.(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl))/i);
    argsText = pathMatch ? pathMatch[1] : '';
  }
  const ts = (action && action.createdAt) || (obs && obs.createdAt) || 0;
  // Replace/edit tools default to OPEN so the diff is visible without an
  // extra click. Other tools default to closed in summary mode.
  const isReplaceTool = tool && /^(replace_in_file|replace_lines|write_file|edit|patch|update_file)/i.test(tool);
  const showFullArgsByDefault = !!tool && /^(run_command|todo_update)$/i.test(tool);
  const obsLines = obs ? obsText.split('\n') : [];
  const obsIsMulti = obsLines.length > 1;
  // Command and todo updates are useful as the primary payload, so show
  // their arguments by default while keeping the result body collapsible.
  // Threshold: > 100 chars or contains a newline.
  const argsIsLong = !!argsText && (argsText.length > 100 || /\n/.test(argsText));
  const [obsOpen, setObsOpen] = React.useState(!summaryMode || isReplaceTool);
  React.useEffect(() => {
    setObsOpen(!summaryMode || isReplaceTool);
  }, [summaryMode, isReplaceTool]);
  const showArgsExpanded = obsOpen || showFullArgsByDefault;
  const headClickable = (!!obs && obsIsMulti) || argsIsLong;
  const toggleObs = () => { if (headClickable) setObsOpen(v => !v); };
  return (
    <div className="tool-card has-hover-affordance"
         style={{ borderLeftColor: borderColor }}>
      <span className="tool-card-ts">{_relTime(ts)}</span>
      <div
        className="tool-card-head"
        role={headClickable ? 'button' : undefined}
        tabIndex={headClickable ? 0 : undefined}
        onClick={headClickable ? toggleObs : undefined}
        onKeyDown={headClickable ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleObs(); }
        } : undefined}
        style={headClickable ? {
          cursor: 'pointer',
          userSelect: 'none',
          alignItems: showArgsExpanded ? 'flex-start' : 'center',
        } : undefined}
        title={headClickable ? (obsOpen ? 'click to collapse' : 'click to expand') : undefined}
      >
        <span className="tool-card-glyph" style={{ color: 'var(--fg)' }}>{theme.glyph}</span>
        <span className="tool-card-tool">{_toolDisplay(tool)}</span>
        {argsText && (
          <span
            className={`tool-card-args${showArgsExpanded ? '' : ' trunc'}`}
            style={{
              color: 'var(--fg)',
              ...(showArgsExpanded ? {
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                overflow: 'visible',
                textOverflow: 'clip',
              } : {}),
            }}
          >{argsText}</span>
        )}
        {status === 'err' && <span className="tool-card-status" style={{ color: '#f85149' }}>✗</span>}
        {status === 'ok'  && <span className="tool-card-status" style={{ color: '#3fb950' }}>✓</span>}
        {(obsIsMulti || argsIsLong) ? (
          <>
            {obsIsMulti && (
              <span className="mute" style={{ fontSize: 'var(--ui-small-font-size)', color: 'var(--fg)' }}>
                {obsLines.length} lines{obs?.truncated ? ' · truncated' : ''}
              </span>
            )}
            <span className="mute" style={{ color: 'var(--fg)' }}>{obsOpen ? '▾' : '▸'}</span>
          </>
        ) : null}
      </div>
      {obs && obsOpen && <div className="tool-card-sep" />}
      {obs && obsOpen && (
        <ObsCard
          entry={{ ...obs, text: obsText }}
          embedded={true}
          summaryMode={summaryMode}
          forceOpen
          hideHeader
        />
      )}
    </div>
  );
};
// Memoized so a single new feed entry doesn't re-render every prior
// ToolCard. action/obs are immutable per turn so reference equality is
// the right comparator.
const ToolCard = React.memo(_ToolCardRaw);

const LiveAgentPreview = React.memo(({ text }) => {
  const body = String(text || '');
  if (!body.trim()) return null;
  return (
    <div className="feed-entry feed-entry-agent feed-entry-live has-hover-affordance" style={{ padding: '8px 0 12px', marginBottom: 4, position: 'relative' }}>
      <span className="feed-entry-label ok" style={{ fontWeight: 600, marginRight: 8,
        fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Agent</span>
      <span className="ts-pill">streaming</span>
      <div
        className="md-agent"
        style={{
          marginTop: 4,
          whiteSpace: 'pre-wrap',
          overflowWrap: 'anywhere',
        }}
      >
        {body}
      </div>
    </div>
  );
});

const _FeedEntryRaw = ({ entry, qaState, onToggle, onCustom, onSubmit, dir, summaryMode = true }) => {
  if (entry.kind === 'user') {
    const userText = String(entry.text || '');
    // Render through markdown so QA submission prompts (which are
    // multi-line markdown with `#`/`##` headers, bullet lists, and code
    // chips) keep their structure instead of collapsing onto one line.
    // Plain single-line user inputs still render fine via marked.
    const userHtml = _markdownHtml(userText);
    return (
      <div className="feed-entry feed-entry-user" style={{ padding: '10px 14px', marginBottom: 12, borderLeft: '2px solid var(--accent)', background: 'var(--bg-2)', borderRadius: 2 }}>
        <span className="feed-entry-label acc" style={{ fontWeight: 600, marginRight: 8, fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase' }}>You</span>
        <div
          className="md-user md-agent"
          style={{ fontFamily: 'var(--mono)', fontSize: 'var(--ui-font-size)', display: 'inline-block', verticalAlign: 'top' }}
          dangerouslySetInnerHTML={{ __html: userHtml }}
          ref={_postProcessMarkdownNode}
        />
      </div>
    );
  }
  if (entry.kind === 'agent') {
    const html = _markdownHtml(entry.text || '');
    return (
      <div className="feed-entry feed-entry-agent has-hover-affordance" style={{ padding: '8px 0 12px', marginBottom: 4, position: 'relative' }}>
        <span className="feed-entry-label ok" style={{ fontWeight: 600, marginRight: 8,
          fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Agent</span>
        {entry.createdAt ? (
          <span className="ts-pill">{_relTime(entry.createdAt)}</span>
        ) : null}
        <CopyBtn text={entry.text || ''} />
        <div className="md-agent" style={{ marginTop: 4 }} dangerouslySetInnerHTML={{ __html: html }}
          ref={_postProcessMarkdownNode}
        />
      </div>
    );
  }
  if (entry.kind === 'thought') {
    return <CollapsibleThought text={entry.text || ''} summaryMode={summaryMode} />;
  }
  if (entry.kind === 'iter_marker') {
    // Hidden from display per user feedback — iteration counter +
    // model badge above every tool was visual noise. Marker entries
    // are still preserved in the feed (so logs / replay still see
    // them) but render nothing.
    return null;
  }
  if (entry.kind === 'action') {
    const planned = entry.planned;
    // Live mode emits {kind:'action', text:'▶ tool args…'}; the old mock
    // shape was {kind:'action', tool, args, planned?}. Prefer .text when
    // present so we don't crash on missing args.
    if (entry.text) {
      return (
        <div className="react-block action">
          <span className="rb-tag">action</span>
          <span className="mute" style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</span>
        </div>
      );
    }
    return (
      <div className="react-block action" style={planned ? { opacity: 0.6, borderLeftColor: 'var(--warn)' } : {}}>
        <span className="rb-tag" style={planned ? { color: 'var(--warn)' } : {}}>{planned ? 'plan·action' : 'action'}</span>
        <span>{planned && <span className="warn" style={{ marginRight: 6, fontStyle: 'italic' }}>[would]</span>}<b style={{ color: 'var(--tool-accent)' }}>{entry.tool}</b>(<span className="mute">{Object.entries(entry.args || {}).filter(([k]) => k !== 'planned').map(([k, v]) => (
          <span key={k}>{k}=<span style={{ color: 'var(--fg)' }}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span> </span>
        ))}</span>)</span>
      </div>
    );
  }
  if (entry.kind === 'obs') {
    return <ObsCard entry={entry} summaryMode={summaryMode} />;
  }
  // legacy inline (unused — kept so the surrounding block compiles
  // until I fully extract; never reached because of return above)
  if (false) {
    let txt = entry.text || '';
    // Plan A: condense todo_* tool results — strip the redundant
    // ── TODO ── list block from the chat OBS. The right-sidebar
    // TodoPanel already shows the full live state via /api/todos;
    // re-printing the 7-line list per iteration drowns the chat in
    // duplicates. Keep the agent's actual response (e.g. "✅ Task 2
    // approved" / "Task 3 marked completed. Now perform a CRITICAL
    // ADVERSARIAL review...") because that's the actionable content.
    if (entry.tool && /^todo_(write|update|add|remove|status|note)$/i.test(entry.tool)) {
      const m = txt.match(/^([\s\S]*?)\n\s*── TODO ──[\s\S]*$/);
      if (m) {
        const head = m[1].trim();
        // Count statuses to put a one-line tally where the list was.
        const tally = {};
        const todoBlock = txt.slice(m[1].length);
        const statusRe = /^\s*(⏸|▶|👀|✅|❌)\s/gm;
        let mm;
        while ((mm = statusRe.exec(todoBlock)) !== null) {
          const k = ({'⏸':'pending','▶':'in-progress','👀':'completed','✅':'approved','❌':'rejected'})[mm[1]];
          if (k) tally[k] = (tally[k] || 0) + 1;
        }
        const tallyStr = ['in-progress','pending','completed','approved','rejected']
          .filter(k => tally[k]).map(k => `${tally[k]} ${k}`).join(' · ');
        txt = head + (tallyStr ? `\n— ${tallyStr} (full list in sidebar →)` : '');
      }
    }
    const isMulti = txt.includes('\n');
    // Diff colorizing — replace_in_file / write_file emit a body where
    // each line is "<lineno> [+|-| ] <content>". Mark + lines green and
    // - lines red. Detect by tool name OR by presence of the "Added N
    // lines, removed M lines" header (which is the canonical signature
    // of a diff-style result).
    const looksLikeDiff = /(^|\n)\s*⎿?\s*Added \d+ lines?,? removed \d+ lines?/.test(txt)
                       || (entry.tool && /^(replace_in_file|write_file|edit|patch)/i.test(entry.tool));
    return (
      <div className="react-block obs">
        <span className="rb-tag">obs{entry.tool ? ` · ${entry.tool}` : ''}</span>
        {isMulti ? (
          <pre style={{
            margin: '4px 0 0', maxHeight: 280, overflow: 'auto',
            background: 'var(--bg-3)', padding: '6px 10px',
            borderRadius: 4, fontSize: 11, lineHeight: 1.45,
            whiteSpace: 'pre', wordBreak: 'normal',
          }}>
            {looksLikeDiff
              ? txt.split('\n').map((line, i) => {
                  // Match "  82 + content" / "  82 - content" / "  82 -//comment".
                  // Require exactly ONE space between line number and
                  // marker — context lines like "  79      - { ... }"
                  // (YAML list inside a diff) have extra spaces, and we
                  // shouldn't colorize those as deletions. Marker can
                  // abut content with no space (e.g. "-//").
                  const m = line.match(/^(\s*\d+ )([+\-])(.*)$/);
                  if (!m) {
                    return <div key={i} style={{ color: 'var(--fg-mute)' }}>{line || ' '}</div>;
                  }
                  const [, prefix, marker, rest] = m;
                  const add = marker === '+';
                  return (
                    <div key={i} style={{
                      background: add
                        ? 'color-mix(in oklch, #3fb950 18%, transparent)'
                        : 'color-mix(in oklch, #f85149 18%, transparent)',
                      color: add ? '#7ee787' : '#ffa198',
                      borderLeft: `2px solid ${add ? '#3fb950' : '#f85149'}`,
                      paddingLeft: 6,
                    }}>
                      <span style={{ color: 'var(--fg-mute)' }}>{prefix}</span>
                      <b>{marker}</b>
                      <span>{rest}</span>
                    </div>
                  );
                })
              : txt}
            {entry.truncated ? '\n…[truncated]' : ''}
          </pre>
        ) : (
          <span>{txt}{entry.truncated ? ' …[truncated]' : ''}</span>
        )}
      </div>
    );
  }
  if (entry.kind === 'qcard') {
    return <AskUserCall flowId={entry.flowId} state={qaState[entry.flowId]} dir={dir} />;
  }
  if (entry.kind === 'ssot_approval') {
    return <SsotApprovalCard payload={entry.payload || entry} />;
  }
  if (entry.kind === 'turn_end') {
    // Visible boundary so users can scroll back and see exactly where
    // each turn ended. Distinct from "waiting on ask_user" — that state
    // shows the AskUserPrompt and never reaches this branch.
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        margin: '14px 0 18px', userSelect: 'none',
      }}>
        <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
        <span className="ok" style={{
          fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase',
          fontFamily: 'var(--mono)', fontWeight: 600,
        }}>{entry.text || '✓ end of loop'}</span>
        <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
      </div>
    );
  }
  return null;
};
// Memoize FeedEntry so adding one new entry doesn't re-render every
// existing one. Custom comparator keeps re-render only on entry data
// change or qaState slice change for the entry's flow id.
const FeedEntry = React.memo(_FeedEntryRaw, (prev, next) => {
  if (prev.entry !== next.entry) return false;
  if (prev.summaryMode !== next.summaryMode) return false;
  if (prev.dir !== next.dir) return false;
  // qaState only matters for ask_user entries
  const flowId = (prev.entry && (prev.entry.flowId || (prev.entry.kind === 'ask_user' && prev.entry.flow_id))) || null;
  if (flowId) {
    const a = (prev.qaState || {})[flowId];
    const b = (next.qaState || {})[flowId];
    if (a !== b) return false;
  }
  return true;
});

// HTML-escape before any interpolation. Without this, the fallback
// renderer was happy to drop user-controlled text (e.g. file contents
// the agent quoted) straight into HTML — `</code><img src=x onerror=…>`
// inside a backtick span would have escaped the <code> tag and
// injected a payload. DOMPurify catches it downstream now too, but
// belt-and-suspenders.
const _escHtml = (s) => String(s)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');
const renderInline = (s) => _escHtml(s)
  .replace(/`([^`]+)`/g, '<code class="acc" style="background:var(--bg-2);padding:1px 4px;border-radius:2px;">$1</code>')
  .replace(/\*\*([^*]+)\*\*/g, '<b style="color:var(--fg);">$1</b>');

const SsotApprovalCard = ({ payload }) => {
  const ip = payload?.ip || '';
  const decisions = payload?.decisions || {};
  const missing = Array.isArray(payload?.missing) ? payload.missing : [];
  const approved = !!payload?.approved;
  const send = (text) => {
    if (!text || !window.backend?.send) return;
    let session = 'default';
    try {
      session = normalizeUiSession(window.ACTIVE_SESSION || '') || 'default';
    } catch (_) {
      session = 'default';
    }
    window.backend.send({
      type: 'prompt',
      text,
      session,
      ui_lang: window.ATLAS_UI_LANG || 'ko',
    });
  };
  const rows = [
    ['purpose', 'Purpose'],
    ['bus_interface', 'Bus'],
    ['register_map', 'Registers'],
    ['clock_reset', 'Clock/reset'],
    ['interrupt', 'Interrupt'],
    ['memory_map', 'Memory map'],
    ['parameters', 'Parameters'],
    ['submodule_structure', 'Submodules'],
    ['test_expectation', 'Tests'],
  ];
  const statusText = missing.length
    ? `Missing ${missing.length} decision${missing.length === 1 ? '' : 's'}`
    : approved ? 'Approved · YAML write enabled' : 'Answered · waiting for approval';
  return (
    <div className="react-block obs" style={{
      borderLeftColor: approved ? 'var(--ok)' : 'var(--warn)',
      background: approved
        ? 'color-mix(in oklch, var(--ok) 8%, var(--bg-2))'
        : 'color-mix(in oklch, var(--warn) 8%, var(--bg-2))',
      padding: '10px 12px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
        <div>
          <span className="rb-tag" style={{ color: approved ? 'var(--ok)' : 'var(--warn)' }}>ssot approval</span>
          <b style={{ marginLeft: 8 }}>{ip}</b>
        </div>
        <span style={{
          fontSize: 10,
          color: approved ? 'var(--ok)' : 'var(--warn)',
          border: `1px solid ${approved ? 'var(--ok)' : 'var(--warn)'}`,
          padding: '2px 6px',
          borderRadius: 2,
          whiteSpace: 'nowrap',
        }}>{statusText}</span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--fg-mute)', marginBottom: 10 }}>
        Q&A is complete. Review the plan, approve it, then generate the SSOT YAML from the same Web UI session.
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(92px, 0.28fr) minmax(0, 1fr)',
        gap: '4px 10px',
        marginBottom: 10,
        fontSize: 11,
      }}>
        {rows.map(([key, label]) => (
          <React.Fragment key={key}>
            <span style={{ color: missing.includes(key) ? 'var(--warn)' : 'var(--fg-mute)' }}>{label}</span>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {decisions[key] || <span className="warn">missing</span>}
            </span>
          </React.Fragment>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <button
          className="mini-btn"
          disabled={approved || missing.length > 0}
          onClick={() => send(payload?.approve_cmd || `approve ${ip}`)}
          title={missing.length ? 'Answer missing Q&A fields first' : 'Approve this SSOT plan'}
        >
          approve
        </button>
        <button
          className="mini-btn"
          disabled={!approved}
          onClick={() => send(payload?.generate_cmd || `/to-ssot ${ip}`)}
          title={approved ? 'Generate SSOT YAML' : 'Approve before writing YAML'}
        >
          generate SSOT
        </button>
        <button
          className="mini-btn"
          onClick={() => send(`/new-ip ${ip} ${payload?.kind || ''}`.trim())}
          title="Reopen the Q&A cards for this IP"
        >
          revise Q&A
        </button>
        <code className="acc">{approved ? (payload?.generate_cmd || `/to-ssot ${ip}`) : (payload?.approve_cmd || `approve ${ip}`)}</code>
      </div>
    </div>
  );
};

const AskUserQuestionBlock = ({
  index = 0,
  block = {},
  blockState = { opts: [], custom: '' },
  kind = 'single',
  isBatched = false,
  isActive = true,
  answered = false,
  selectedIndex = 0,
  showQuestion = true,
  onEnsureActive = () => {},
  onSelectIndex = () => {},
  onToggleOption = () => {},
  onCustom = () => {},
  onSelectAll,
  onClearAll,
}) => {
  const blockOpts = blockState.opts || [];
  const customIdx = blockOpts.length;
  const blockMultiline = !!(block.multiline || String(block.placeholder || '').includes('\n'));
  const blockPlaceholder = block.placeholder || '';
  const blockSubtitle = block.subtitle || '';
  const blockQuestion = block.question || '';
  const ensureActive = () => onEnsureActive(index);
  return (
    <div
      key={index}
      onClick={() => { if (isBatched && !isActive) ensureActive(); }}
      style={{
        marginBottom: isBatched ? 12 : 0,
        padding: isBatched ? '10px 12px' : 0,
        border: isBatched
          ? `1px solid ${isActive ? 'var(--accent)' : 'var(--line)'}`
          : 'none',
        background: isBatched && isActive
          ? 'color-mix(in oklch, var(--accent) 5%, transparent)'
          : 'transparent',
        borderRadius: 2,
        cursor: isBatched && !isActive ? 'pointer' : 'default',
      }}
    >
      {showQuestion ? (
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 10, color: 'var(--fg)' }}>
          {isBatched && (
            <span
              className={answered ? 'ok' : 'mute'}
              style={{ marginRight: 8, fontSize: 12, fontWeight: 700, fontFamily: 'var(--mono)' }}
            >
              {answered ? '☒' : '☐'} Q{index + 1}.
            </span>
          )}
          {blockQuestion}
          {blockSubtitle && (
            <div className="mute" style={{ fontSize: 11, fontWeight: 400, marginTop: 2 }}>
              {blockSubtitle}
            </div>
          )}
        </div>
      ) : null}

      {kind === 'multi' && blockOpts.length > 1 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 11 }}>
          <span
            onClick={(ev) => {
              ev.stopPropagation();
              ensureActive();
              if (onSelectAll) onSelectAll(blockOpts);
            }}
            style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--accent)', color: 'var(--accent)', borderRadius: 2 }}
            title="Select every option">
            ☑ Select all
          </span>
          <span
            onClick={(ev) => {
              ev.stopPropagation();
              ensureActive();
              if (onClearAll) onClearAll(blockOpts);
            }}
            style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--line)', color: 'var(--fg-mute)', borderRadius: 2 }}
            title="Deselect every option">
            ☐ Clear
          </span>
          <span className="mute" style={{ alignSelf: 'center', fontSize: 10 }}>
            · click rows to toggle individually
          </span>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {blockOpts.map((o, oi) => {
          const isSel = o.selected;
          const focused = isActive && selectedIndex === oi;
          return (
            <div
              key={o.id}
              onClick={(ev) => { ev.stopPropagation(); ensureActive(); onSelectIndex(oi); onToggleOption(o.id); }}
              style={{
                display: 'grid',
                gridTemplateColumns: '24px 28px 1fr',
                alignItems: 'baseline',
                gap: 6,
                padding: '4px 8px',
                background: focused ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                borderLeft: `2px solid ${focused ? 'var(--accent)' : 'transparent'}`,
                cursor: 'pointer',
                fontFamily: 'var(--mono)',
                fontSize: 13,
                lineHeight: 1.4,
              }}
            >
              <span className="mute" style={{ textAlign: 'right' }}>{oi + 1}.</span>
              <span style={{ color: isSel ? 'var(--accent)' : 'var(--fg-mute)', fontWeight: 700 }}>
                {kind === 'multi' ? (isSel ? '[✓]' : '[ ]') : (isSel ? '(•)' : '( )')}
              </span>
              <div>
                <span style={{ color: focused ? 'var(--fg)' : (isSel ? 'var(--fg)' : 'var(--fg-dim, var(--fg))') }}>
                  {o.label}
                  {o.locked && <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>(required)</span>}
                </span>
                <div className="mute" style={{ fontSize: 11, fontFamily: 'var(--mono)', marginTop: 1 }}>
                  {o.detail}
                </div>
              </div>
            </div>
          );
        })}

        <div
          onClick={(ev) => { ev.stopPropagation(); ensureActive(); onSelectIndex(customIdx); }}
          style={{
            display: 'grid',
            gridTemplateColumns: '24px 28px 1fr',
            alignItems: 'baseline',
            gap: 6,
            padding: '4px 8px',
            background: isActive && selectedIndex === customIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            borderLeft: `2px solid ${isActive && selectedIndex === customIdx ? 'var(--accent)' : 'transparent'}`,
            cursor: 'text',
            fontFamily: 'var(--mono)',
            fontSize: 13,
          }}
        >
          <span className="mute" style={{ textAlign: 'right' }}>{blockOpts.length + 1}.</span>
          <span style={{ color: blockState.custom ? 'var(--warn)' : 'var(--fg-mute)', fontWeight: 700 }}>
            {blockState.custom ? '[✓]' : '[ ]'}
          </span>
          <div style={{ display: 'flex', alignItems: 'stretch', gap: 6 }}>
            {blockMultiline ? (
              <textarea
                className="askcustom"
                value={blockState.custom || ''}
                onChange={(e) => { ensureActive(); onCustom(e.target.value); }}
                onFocus={() => { ensureActive(); onSelectIndex(customIdx); }}
                placeholder={blockPlaceholder || 'custom answer / free-form note…'}
                spellCheck={false}
                style={{
                  background: 'transparent', border: '1px solid var(--line)', outline: 'none',
                  fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 12, flex: 1,
                  padding: '6px 8px', minHeight: 120, lineHeight: 1.45, resize: 'vertical',
                  whiteSpace: 'pre-wrap',
                }}
              />
            ) : (
              <input
                className="askcustom"
                value={blockState.custom || ''}
                onChange={(e) => { ensureActive(); onCustom(e.target.value); }}
                onFocus={() => { ensureActive(); onSelectIndex(customIdx); }}
                placeholder={blockPlaceholder || 'custom answer / free-form note…'}
                style={{
                  background: 'transparent', border: 'none', outline: 'none',
                  fontFamily: 'var(--mono)', color: 'var(--fg)', fontSize: 13, flex: 1, padding: 0,
                }}
              />
            )}
            {isActive && selectedIndex === customIdx && <span className="cursor-thin" />}
          </div>
        </div>
      </div>
    </div>
  );
};

const SsotQaBoard = ({
  data,
  sessions,
  activeSession,
  uiLang = 'ko',
  onSelectSession,
  onBack,
  onRefresh,
  onRunCommand,
  onSubmitPending,
  showChecklist = false,
  checklistOnly = false,
}) => {
  const sections = Array.isArray(data?.sections) ? data.sections : [];
  const sessionRows = Array.isArray(sessions) ? sessions : [];
  const summary = data?.summary || { total: 0, approved: 0, pending: 0 };
  const requirements = data?.requirements || {};
  const requirementItems = Array.isArray(requirements.items) ? requirements.items : [];
  const missingRequirementKeys = Array.isArray(requirements.missing_keys)
    ? requirements.missing_keys
    : requirementItems.filter(item => item?.status === 'missing').map(item => item.key);
  const requirementTotal = Number(requirements.total || requirementItems.length || 0);
  const requirementMissing = Number(requirements.missing ?? missingRequirementKeys.length ?? 0);
  const requirementFilled = Number(requirements.filled ?? Math.max(0, requirementTotal - requirementMissing));
  const requirementPct = requirementTotal > 0
    ? Math.max(0, Math.min(100, Math.round((requirementFilled / requirementTotal) * 100)))
    : 0;
  const hasIp = !!data?.ip;
  const activeSessionNorm = normalizeUiSession(activeSession || data?.session || '');
  const activeOwner = activeSessionNorm.split('/').filter(Boolean)[0] || '';
  const activeIp = data?.ip || ssotIpFromSession(activeSessionNorm) || '';
  const currentSessionRows = sessionRows.filter(row => {
    const rowSession = normalizeUiSession(row?.session || '');
    const rowParts = rowSession.split('/').filter(Boolean);
    const rowOwner = rowParts[0] || '';
    const rowIp = row?.ip || ssotIpFromSession(rowSession) || '';
    const sameOwner = !activeOwner || !rowOwner || rowOwner === activeOwner;
    const sameIp = !activeIp || rowIp === activeIp;
    return sameOwner && sameIp;
  });
  const t = uiLang === 'en'
    ? {
        noSession: 'No SSOT QA session selected.',
        selectSession: 'Select an IP/session that uses',
        back: 'back to chat',
        title: 'Q&A Session',
        subtitle: 'Answer questions here. The answers fill the SSOT promise sheet for RTL.',
        checklistTitle: 'Check List',
        checklistSubtitle: 'Fill the SSOT promise sheet before making RTL code.',
        legend: 'SSOT = design promise sheet. RTL = hardware code.',
        rtlReadiness: 'RTL readiness',
        nextAction: 'What to do now',
        needTitle: '9 boxes to fill',
        missingTitle: 'Empty boxes now',
        missingEmpty: 'No empty boxes.',
        readyToGenerate: 'Ready to make RTL.',
        needsSsotApproval: 'All boxes are filled. Press To SSOT and approve the promise sheet.',
        blockedByMissing: 'RTL should wait because some boxes are empty.',
        feedTitle: 'Use these 4 steps',
        actionChatTitle: '1. New wishes = Chat',
        actionChatDetail: 'Write what you want in normal words.',
        actionImportTitle: '2. Old docs = Import',
        actionImportDetail: 'Choose files you already have. They go into the Import folder and /import reads them.',
        actionInterviewTitle: '3. Unknowns = Deep Interview',
        actionInterviewDetail: 'Ask only the questions needed to fill empty boxes.',
        actionToSsotTitle: '4. Promise sheet = To SSOT',
        actionToSsotDetail: 'Turn the answers and files into the SSOT document.',
        chooseFile: 'choose file',
        openChat: 'open chat',
        filled: 'filled',
        missing: 'missing',
        refresh: 'refresh',
        chat: 'chat',
        total: 'total',
        approved: 'approved',
        pending: 'pending',
        requirements: 'requirements',
        requirementsRemaining: 'remaining',
        ssot: 'ssot',
        draft: 'draft',
        sessions: 'Current session',
        toc: 'Table of contents',
        none: 'No QA records yet.',
        noSaved: 'No QA records for this session/IP yet.',
        noCards: 'No section QA cards yet. Start',
        noAnswer: 'No answer captured yet.',
        useInput: 'use input',
        answer: 'answer',
        close: 'close',
        sendToInput: 'open input',
        selectOne: 'select one option',
        selectMany: 'select one or more options',
        typedAnswer: 'typed answer',
        customNote: 'custom note',
        noOptions: 'No options provided. Type an answer below.',
        autoInputHint: 'select or type here; chat input stays unchanged until send',
        inputUpdated: 'draft ready',
        send: 'send',
        sendNeedAnswer: 'select an option or type an answer first',
        importFiles: 'Import',
        importing: 'Importing...',
        deepInterview: 'Deep Interview',
        toSsot: 'To SSOT',
        importReady: 'uploaded',
      }
    : {
        noSession: '선택된 SSOT QA 세션이 없습니다.',
        selectSession: 'IP/session을 선택하세요:',
        back: '채팅으로',
        title: 'Q&A Session',
        subtitle: '여기는 질문에 답하는 곳입니다. 답변이 SSOT 약속장의 빈칸을 채웁니다.',
        checklistTitle: 'Check List',
        checklistSubtitle: 'SSOT는 RTL 코드를 만들기 전에 채우는 약속장입니다. 빈칸을 채우면 RTL을 만들 준비가 됩니다.',
        legend: 'SSOT = 설계 약속장. RTL = 실제 회로 코드.',
        rtlReadiness: 'RTL 생성 준비도',
        nextAction: '지금 할 일',
        needTitle: '채워야 하는 9칸',
        missingTitle: '지금 비어 있는 칸',
        missingEmpty: '비어 있는 칸이 없습니다.',
        readyToGenerate: 'RTL을 만들 준비가 됐습니다.',
        needsSsotApproval: '9칸은 다 찼습니다. To SSOT를 눌러 약속장을 만들고 승인하세요.',
        blockedByMissing: '아직 빈칸이 있어서 RTL 만들기는 이릅니다.',
        feedTitle: '이 4단계만 보면 됩니다',
        actionChatTitle: '1. 새로 원하는 것 = Chat',
        actionChatDetail: '말하듯이 적으면 됩니다.',
        actionImportTitle: '2. 이미 가진 문서 = Import',
        actionImportDetail: '파일을 고르면 Import 폴더에 넣고 /import가 읽습니다.',
        actionInterviewTitle: '3. 모르는 것 = Deep Interview',
        actionInterviewDetail: '빈칸을 채우는 질문만 받습니다.',
        actionToSsotTitle: '4. 약속장 만들기 = To SSOT',
        actionToSsotDetail: '파일과 답변을 모아 SSOT 문서를 만듭니다.',
        chooseFile: '파일 선택',
        openChat: '채팅 열기',
        filled: '채움',
        missing: '부족',
        refresh: '새로고침',
        chat: '채팅',
        total: '전체',
        approved: '승인',
        pending: '대기',
        requirements: '요구사항',
        requirementsRemaining: '남음',
        ssot: 'SSOT',
        draft: '작성중',
        sessions: '현재 세션',
        toc: '목차',
        none: '아직 QA 기록이 없습니다.',
        noSaved: '현재 session/IP의 QA 기록이 없습니다.',
        noCards: '아직 section QA 카드가 없습니다. 시작:',
        noAnswer: '아직 답변이 저장되지 않았습니다.',
        useInput: '입력으로',
        answer: '답변',
        close: '닫기',
        sendToInput: '입력창 열기',
        selectOne: '옵션 하나를 선택하세요',
        selectMany: '옵션을 하나 이상 선택하세요',
        typedAnswer: '직접 입력',
        customNote: '추가 설명',
        noOptions: '옵션이 없습니다. 아래에 답변을 입력하세요.',
        autoInputHint: '여기서 선택/입력해도 전송 전까지 채팅 입력창은 바뀌지 않습니다',
        inputUpdated: '답변 초안 준비됨',
        send: '전송',
        sendNeedAnswer: '옵션을 선택하거나 답변을 입력한 후 전송하세요',
        importFiles: 'Import',
        importing: 'Importing...',
        deepInterview: 'Deep Interview',
        toSsot: 'To SSOT',
        importReady: '업로드됨',
      };
  const requirementHelp = uiLang === 'en'
    ? {
        purpose: 'What this IP does in one sentence.',
        bus_interface: 'How software or another block talks to it.',
        register_map: 'Control/status registers, offsets, and access rules.',
        clock_reset: 'Clock names, reset names, polarity, and timing assumptions.',
        interrupt: 'Whether it raises interrupts, and when. Say none if not used.',
        memory_map: 'Address or memory requirements. Say none if not used.',
        parameters: 'Configurable parameters and default values.',
        submodule_structure: 'Internal blocks and who owns each responsibility.',
        test_expectation: 'Minimum simulation/test behavior that proves it works.',
      }
    : {
        purpose: '이 IP가 한 문장으로 무슨 일을 하는지.',
        bus_interface: '소프트웨어나 다른 블록이 어떻게 말을 거는지.',
        register_map: '레지스터 주소, 읽기/쓰기 규칙, 상태값.',
        clock_reset: '클럭/리셋 이름, 극성, 타이밍 조건.',
        interrupt: '인터럽트를 쓰는지, 언제 올리는지. 없으면 없다고 적기.',
        memory_map: '메모리나 주소 요구사항. 없으면 없다고 적기.',
        parameters: '바꿀 수 있는 파라미터와 기본값.',
        submodule_structure: '내부 블록 구성과 각 블록의 책임.',
        test_expectation: '시뮬레이션에서 최소한 무엇을 확인해야 하는지.',
      };
  const requirementSimpleName = uiLang === 'en'
    ? {
        purpose: 'What are we making?',
        bus_interface: 'How does it connect?',
        register_map: 'What knobs and status bits exist?',
        clock_reset: 'What clock and reset does it use?',
        interrupt: 'Does it ring an interrupt bell?',
        memory_map: 'Does it need an address or memory?',
        parameters: 'What can be configured?',
        submodule_structure: 'What small blocks are inside?',
        test_expectation: 'How do we know it works?',
      }
    : {
        purpose: '무엇을 만들까?',
        bus_interface: '어떻게 연결할까?',
        register_map: '조작 버튼과 상태표는?',
        clock_reset: '클럭과 리셋은?',
        interrupt: '인터럽트 알림은?',
        memory_map: '주소나 메모리는?',
        parameters: '바꿀 수 있는 값은?',
        submodule_structure: '안에는 어떤 작은 블록?',
        test_expectation: '어떻게 성공을 확인할까?',
      };
  const requirementByKey = new Map(requirementItems.map(item => [item?.key, item || {}]));
  const requirementLabel = (key) => requirementSimpleName[key] || requirementByKey.get(key)?.label || key;
  const requirementRows = (requirementItems.length ? requirementItems : missingRequirementKeys.map(key => ({ key, status: 'missing' })))
    .filter(item => item?.key)
    .map(item => ({
      key: item.key,
      label: requirementLabel(item.key),
      help: requirementHelp[item.key] || item.label || item.key,
      status: item.status || (missingRequirementKeys.includes(item.key) ? 'missing' : 'filled'),
    }));
  const missingRows = missingRequirementKeys.map(key => ({
    key,
    label: requirementLabel(key),
    help: requirementHelp[key] || requirementLabel(key),
  }));
  const readyForRtl = requirementTotal > 0 && requirementMissing === 0 && !!data?.approved;
  const filledButNeedsSsot = requirementTotal > 0 && requirementMissing === 0 && !data?.approved;
  const rtlReadinessText = readyForRtl
    ? t.readyToGenerate
    : (filledButNeedsSsot ? t.needsSsotApproval : t.blockedByMissing);
  const nextActionText = requirementMissing > 0
    ? (uiLang === 'en'
      ? `${requirementMissing} decision${requirementMissing === 1 ? '' : 's'} are missing. Import existing docs first, then run Deep Interview for the gaps.`
      : `${requirementMissing}개 결정이 부족합니다. 기존 문서가 있으면 먼저 Import하고, 남은 빈칸은 Deep Interview로 채우세요.`)
    : (data?.approved
      ? (uiLang === 'en' ? 'SSOT is approved. RTL generation can use it.' : 'SSOT가 승인되었습니다. RTL 생성에 사용할 수 있습니다.')
      : (uiLang === 'en' ? 'Run To SSOT to document and approve the filled decisions.' : 'To SSOT로 채워진 결정을 문서화하고 승인하세요.'));
  const uploadDoneText = (count) => (
    uiLang === 'en'
      ? `${count} file${count === 1 ? '' : 's'} saved under ${data.ip}/req/imports/; /import started.`
      : `${count}개 파일을 ${data.ip}/req/imports/에 저장하고 /import를 실행했습니다.`
  );
  const importInputRef = React.useRef(null);
  const [importBusy, setImportBusy] = React.useState(false);
  const [importStatus, setImportStatus] = React.useState('');
  const runSsotCommand = (cmd) => {
    const text = String(cmd || '').trim();
    if (!text || !onRunCommand) return;
    onRunCommand(text);
  };
  const readFileAsBase64 = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const raw = String(reader.result || '');
      resolve(raw.includes(',') ? raw.split(',').pop() : raw);
    };
    reader.onerror = () => reject(reader.error || new Error('file read failed'));
    reader.readAsDataURL(file);
  });
  const uploadImportFiles = async (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length || !data?.ip) return;
    setImportBusy(true);
    setImportStatus('');
    try {
      const payloadFiles = await Promise.all(files.map(async file => ({
        name: file.name,
        content_b64: await readFileAsBase64(file),
      })));
      const res = await fetch('/api/ssot/import/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip: data.ip,
          session: activeSessionNorm || '',
          files: payloadFiles,
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok || !payload?.ok) {
        throw new Error(payload?.error || `upload failed (${res.status})`);
      }
      setImportStatus(uploadDoneText((payload.paths || []).length));
      if (payload.command) runSsotCommand(payload.command);
      setTimeout(() => { try { onRefresh && onRefresh(); } catch (_) {} }, 600);
    } catch (err) {
      setImportStatus(String(err?.message || err || 'upload failed'));
    } finally {
      setImportBusy(false);
    }
  };
  // All QA cards (pending AND approved) default to expanded. Track the
  // *closed* set so newly-streamed items inherit the open-by-default rule.
  const [closedCardKeys, setClosedCardKeys] = React.useState(() => new Set());
  const [answerDrafts, setAnswerDrafts] = React.useState({});
  // Active section tab — null means "first section with pending items, else first section".
  const [activeSectionId, setActiveSectionId] = React.useState(null);
  // Per-status group collapse: both groups default open. Tracking the
  // closed set keeps the default-open rule stable across re-renders.
  const [closedStatusGroups, setClosedStatusGroups] = React.useState(() => new Set());
  const pendingItemKey = (item) => [
    item?.flow_id || '',
    item?.section || item?.section_id || '',
    item?.decision_key || item?.source || item?.question || '',
  ].join(':');
  const optionRows = (item) => (
    Array.isArray(item?.options) ? item.options : []
  ).map((option, idx) => {
    const raw = option && typeof option === 'object' ? option : { id: option, label: option };
    const id = String(raw.id ?? raw.value ?? raw.label ?? idx);
    const label = String(raw.label ?? raw.title ?? raw.value ?? raw.id ?? `Option ${idx + 1}`);
    const detail = raw.detail || raw.description || '';
    return { ...raw, id, label, detail };
  });
  const pendingKind = (item) => {
    const kind = String(item?.question_kind || item?.kind || '').toLowerCase();
    if (kind === 'multi' || kind === 'multiple' || kind === 'checkbox') return 'multi';
    if (kind === 'input' || kind === 'text' || kind === 'freeform') return 'input';
    return optionRows(item).length ? 'single' : 'input';
  };
  const pendingDraft = (item) => {
    const key = pendingItemKey(item);
    const stored = answerDrafts[key];
    const rows = optionRows(item);
    if (stored) {
      const selected = new Set((stored.opts || []).filter(o => o.selected).map(o => String(o.id)));
      return {
        opts: rows.map(option => ({ ...option, selected: selected.has(option.id) })),
        custom: stored.custom || '',
      };
    }
    // No in-memory edit yet → seed from the saved answer so approved/answered
    // cards open with their previous selection pre-checked. The seed is
    // matched by option id, label, or value (whichever is in the answer
    // payload). If we cannot match an option, fall back to dropping the
    // entire saved blob into the custom note.
    const ans = item?.answer_data || item?.answer || '';
    const seedSelected = new Set();
    let seedCustom = '';
    if (ans && typeof ans === 'object') {
      const sel = Array.isArray(ans.selected) ? ans.selected : [];
      sel.forEach(s => {
        const tok = String(s || '').trim();
        if (!tok) return;
        const match = rows.find(o => String(o.id) === tok || String(o.label) === tok);
        if (match) seedSelected.add(String(match.id));
      });
      seedCustom = String(ans.answer || ans.note || ans.custom || '').trim();
    } else if (typeof ans === 'string' && ans.trim()) {
      const txt = ans.trim();
      const match = rows.find(o => String(o.label) === txt || String(o.id) === txt);
      if (match) seedSelected.add(String(match.id));
      else seedCustom = txt;
    }
    return {
      opts: rows.map(option => ({ ...option, selected: seedSelected.has(option.id) })),
      custom: seedCustom,
    };
  };
  const hasPendingAnswer = (draft) => (
    (draft?.opts || []).some(o => o.selected)
  ) || String(draft?.custom || '').trim().length > 0;
  const buildPendingInputText = (item, draft = pendingDraft(item)) => {
    const selectedRows = (draft?.opts || []).filter(option => option.selected);
    const selectedLines = selectedRows.map(option => (
      option.detail ? `  - ${option.label} (${option.id}): ${option.detail}` : `  - ${option.label} (${option.id})`
    ));
    const custom = String(draft?.custom || '').trim();
    const ip = data?.ip || activeIp || 'current IP';
    const lines = [];
    const headerKey = item.decision_key ? ` · ${item.decision_key}` : '';
    lines.push(`### Answer pending QA — ${ip}${headerKey}`);
    if (item.decision_label && item.decision_label !== item.question) {
      lines.push(`Decision: ${item.decision_label}`);
    }
    lines.push(`Question: ${item.question || item.decision_label || 'Untitled question'}`);
    if (item.subtitle) lines.push(`Context : ${item.subtitle}`);
    if (selectedLines.length) {
      lines.push('Selected:');
      lines.push(...selectedLines);
    }
    if (custom) lines.push(`Note    : ${custom}`);
    if (!selectedLines.length && !custom) {
      lines.push('Answer  : <choose option or type note>');
    }
    lines.push('Apply this answer to SSOT-GEN QA and continue the current workflow.');
    return lines.join('\n');
  };
  const updatePendingDraft = (item, draft) => {
    const key = pendingItemKey(item);
    setAnswerDrafts(prev => ({ ...prev, [key]: draft }));
  };
  const togglePendingOption = (item, optionId) => {
    const draft = pendingDraft(item);
    const kind = pendingKind(item);
    const opts = (draft.opts || []).map(option => {
      if (kind === 'multi') {
        return option.id === optionId ? { ...option, selected: !option.selected } : option;
      }
      return { ...option, selected: option.id === optionId };
    });
    updatePendingDraft(item, { ...draft, opts });
  };
  const renderPendingAnswerBox = (item) => {
    const draft = pendingDraft(item);
    const kind = pendingKind(item);
    const hasAnswer = hasPendingAnswer(draft);
    return (
      <div
        onClick={(ev) => ev.stopPropagation()}
        onKeyDown={(ev) => ev.stopPropagation()}
        style={{
          marginTop: 8,
          paddingTop: 8,
          borderTop: '1px solid var(--line)',
      }}>
        <div style={{ color: 'var(--fg-mute)', fontSize: 10, marginBottom: 6 }}>
          {kind === 'multi' ? t.selectMany : (kind === 'single' ? t.selectOne : t.typedAnswer)}
        </div>
        {!draft.opts.length ? (
          <div style={{ color: 'var(--fg-mute)', fontSize: 11, marginBottom: 6 }}>{t.noOptions}</div>
        ) : null}
        <AskUserQuestionBlock
          index={0}
          block={{
            question: item.question || item.decision_label || '',
            subtitle: item.subtitle || '',
            placeholder: kind === 'input' ? t.typedAnswer : t.customNote,
            multiline: kind === 'input',
          }}
          blockState={draft}
          kind={kind}
          isBatched={false}
          isActive={true}
          selectedIndex={-1}
          showQuestion={false}
          onToggleOption={(optionId) => togglePendingOption(item, optionId)}
          onCustom={(value) => updatePendingDraft(item, { ...pendingDraft(item), custom: value })}
          onSelectAll={() => updatePendingDraft(item, {
            ...draft,
            opts: (draft.opts || []).map(option => ({ ...option, selected: true })),
          })}
          onClearAll={() => updatePendingDraft(item, {
            ...draft,
            opts: (draft.opts || []).map(option => ({ ...option, selected: false })),
          })}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
          <span style={{ color: hasAnswer ? 'var(--cyan)' : 'var(--fg-mute)', fontSize: 10 }}>
            {hasAnswer ? t.inputUpdated : t.autoInputHint}
          </span>
          <span style={{ flex: 1 }} />
          {onSubmitPending ? (
            <button
              type="button"
              className="mini-btn"
              disabled={!hasAnswer}
              title={hasAnswer ? '' : t.sendNeedAnswer}
              onClick={(ev) => {
                ev.stopPropagation();
                if (!hasAnswer) return;
                onSubmitPending(
                  [{ item, draft }],
                  buildPendingInputText(item, draft),
                );
              }}
              style={{
                background: hasAnswer ? 'var(--cyan)' : undefined,
                color: hasAnswer ? 'var(--bg-0)' : undefined,
                fontWeight: hasAnswer ? 600 : undefined,
                opacity: hasAnswer ? 1 : 0.45,
                cursor: hasAnswer ? 'pointer' : 'not-allowed',
              }}
            >
              {t.send}
            </button>
          ) : null}
        </div>
      </div>
    );
  };
  const renderQa = (item, status) => {
    const key = pendingItemKey(item);
    const isPending = status === 'pending';
    const isApproved = status === 'approved';
    // All QA cards (pending and approved) default OPEN. Approved cards
    // can be re-opened to amend the saved answer (re-select / re-submit).
    const isOpen = (isPending || isApproved) && !closedCardKeys.has(key);
    const statusColor = atlasStatusMeta(status).color;
    const cardToggleable = isPending || isApproved;
    const togglePendingCard = () => {
      if (!cardToggleable) return;
      setClosedCardKeys(prev => {
        const next = new Set(prev);
        if (next.has(key)) next.delete(key);
        else next.add(key);
        return next;
      });
    };
    const handleCardKey = (ev) => {
      if (!cardToggleable) return;
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        togglePendingCard();
      }
    };
    return (
      <div
        key={key}
        role={cardToggleable ? 'button' : undefined}
        tabIndex={cardToggleable ? 0 : undefined}
        onClick={cardToggleable ? togglePendingCard : undefined}
        onKeyDown={cardToggleable ? handleCardKey : undefined}
        title={cardToggleable ? (isOpen ? 'Click to collapse' : 'Click to expand') : undefined}
        style={{
          padding: '8px 10px',
          border: '1px solid var(--line)',
          borderLeft: `3px solid ${statusColor}`,
          background: status === 'approved'
            ? 'color-mix(in oklch, var(--ok) 7%, transparent)'
            : 'color-mix(in oklch, var(--warn) 8%, transparent)',
          marginBottom: 8,
          fontFamily: 'var(--mono)',
          cursor: cardToggleable ? 'pointer' : 'default',
        }}
      >
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
          <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
            {item.decision_key || item.source || 'qa'}
          </span>
          <span style={{ flex: 1 }} />
          {cardToggleable ? (
            <span
              aria-hidden="true"
              style={{
                color: 'var(--fg-mute)',
                fontSize: 10,
                fontFamily: 'var(--mono)',
                userSelect: 'none',
              }}
            >
              {isOpen ? '▾' : '▸'}
            </span>
          ) : null}
        </div>
        <div style={{ color: 'var(--fg)', fontSize: 12, lineHeight: 1.45 }}>
          {item.question || item.decision_label || 'Untitled question'}
        </div>
        {item.subtitle ? (
          <div style={{ color: 'var(--fg-mute)', fontSize: 11, marginTop: 3 }}>
            {item.subtitle}
          </div>
        ) : null}
        {isOpen ? renderPendingAnswerBox(item) : null}
        <div style={{ color: item.answer ? 'var(--fg)' : 'var(--fg-mute)', fontSize: 12, marginTop: 7, lineHeight: 1.45 }}>
          {item.answer || t.noAnswer}
        </div>
      </div>
    );
  };

  if (!hasIp) {
    return (
      <div style={{ padding: 20, color: 'var(--fg-mute)', fontSize: 12, fontFamily: 'var(--mono)' }}>
        <div style={{ marginBottom: 8, color: 'var(--fg)' }}>{t.noSession}</div>
        <div>{t.selectSession} <code style={{ color: 'var(--cyan)' }}>ssot-gen</code>.</div>
        <div style={{ marginTop: 12 }}>
          <button className="mini-btn" type="button" onClick={onBack}>{t.back}</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      fontFamily: 'var(--mono)',
      height: '100%',
      minHeight: 0,
    }}>
      {showChecklist ? (
      <div style={{
        border: '1px solid var(--line)',
        background: 'var(--bg-1)',
        padding: 14,
      }}>
        <input
          ref={importInputRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          onChange={(ev) => {
            const files = ev.target.files;
            ev.target.value = '';
            uploadImportFiles(files);
          }}
        />
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 360px', minWidth: 260 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <div style={{ color: 'var(--fg)', fontSize: 16, fontWeight: 800 }}>{t.checklistTitle}</div>
              <code className="acc">{data.ip}</code>
              <AtlasStatusBadge status={readyForRtl ? 'approved' : (requirementMissing ? 'pending' : 'draft')} label={readyForRtl ? t.approved : (requirementMissing ? t.missing : t.draft)} compact soft />
            </div>
            <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45, maxWidth: 820 }}>
              {t.checklistSubtitle}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <button className="mini-btn" type="button" onClick={onRefresh}>{t.refresh}</button>
            <button className="mini-btn" type="button" onClick={onBack}>{t.chat}</button>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 12,
          marginTop: 14,
          alignItems: 'stretch',
        }}>
          <div style={{
            border: '1px solid var(--line)',
            background: 'color-mix(in oklch, var(--bg-2) 72%, transparent)',
            padding: 10,
          }}>
            <div style={{ color: 'var(--fg-mute)', fontSize: 11, marginBottom: 6 }}>{t.rtlReadiness}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <div style={{ color: readyForRtl ? 'var(--ok)' : (requirementMissing ? 'var(--warn)' : 'var(--cyan)'), fontSize: 34, fontWeight: 800, lineHeight: 1 }}>
                {requirementPct}%
              </div>
              <div style={{ color: 'var(--fg-mute)', fontSize: 12 }}>
                {requirementFilled}/{requirementTotal || 0} {t.filled}
              </div>
            </div>
            <div style={{
              height: 8,
              marginTop: 8,
              border: '1px solid var(--line)',
              background: 'var(--bg-0)',
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${requirementPct}%`,
                height: '100%',
                background: readyForRtl ? 'var(--ok)' : (requirementMissing ? 'var(--warn)' : 'var(--cyan)'),
              }} />
            </div>
            <div style={{ marginTop: 8, color: 'var(--fg)', fontSize: 12, lineHeight: 1.45 }}>
              {rtlReadinessText}
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 9 }}>
              <AtlasStatusBadge status="total" label={t.total} count={summary.total || 0} compact soft />
              <AtlasStatusBadge status="approved" label={t.approved} count={summary.approved || 0} compact soft />
              <AtlasStatusBadge status="pending" label={t.pending} count={summary.pending || 0} compact soft />
            </div>
          </div>

          <div style={{
            border: '1px solid var(--line)',
            background: 'color-mix(in oklch, var(--bg-2) 52%, transparent)',
            padding: 10,
          }}>
            <div style={{ color: 'var(--fg-mute)', fontSize: 11, marginBottom: 6 }}>{t.nextAction}</div>
            <div style={{ color: 'var(--fg)', fontSize: 13, lineHeight: 1.5 }}>{nextActionText}</div>
            <div style={{ marginTop: 12, color: 'var(--fg-mute)', fontSize: 11 }}>{t.feedTitle}</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 8, marginTop: 7 }}>
              <div style={{ borderTop: '2px solid var(--cyan)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionChatTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 11, lineHeight: 1.4, marginTop: 3 }}>{t.actionChatDetail}</div>
                <button className="mini-btn" type="button" onClick={onBack} style={{ marginTop: 7 }}>{t.openChat}</button>
              </div>
              <div style={{ borderTop: '2px solid var(--accent)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionImportTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 11, lineHeight: 1.4, marginTop: 3 }}>{t.actionImportDetail}</div>
                <button
                  className="mini-btn"
                  type="button"
                  disabled={importBusy}
                  onClick={() => importInputRef.current?.click()}
                  title="Upload requirement docs, notes, RTL, YAML, logs, or filelists into SSOT import evidence"
                  style={{ marginTop: 7 }}
                >
                  {importBusy ? t.importing : t.chooseFile}
                </button>
              </div>
              <div style={{ borderTop: '2px solid var(--warn)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionInterviewTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 11, lineHeight: 1.4, marginTop: 3 }}>{t.actionInterviewDetail}</div>
                <button
                  className="mini-btn"
                  type="button"
                  onClick={() => runSsotCommand(`/grill-me ${data.ip}`)}
                  title="Run /grill-me for unresolved SSOT decisions"
                  style={{ marginTop: 7 }}
                >
                  {t.deepInterview}
                </button>
              </div>
              <div style={{ borderTop: '2px solid var(--ok)', paddingTop: 7 }}>
                <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700 }}>{t.actionToSsotTitle}</div>
                <div style={{ color: 'var(--fg-mute)', fontSize: 11, lineHeight: 1.4, marginTop: 3 }}>{t.actionToSsotDetail}</div>
                <button
                  className="mini-btn"
                  type="button"
                  onClick={() => runSsotCommand(`/to-ssot ${data.ip}`)}
                  title="Run /to-ssot for this IP"
                  style={{ marginTop: 7, borderColor: 'var(--ok)', color: 'var(--ok)' }}
                >
                  {t.toSsot}
                </button>
              </div>
            </div>
          </div>
        </div>

        {requirementTotal > 0 ? (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 12,
            marginTop: 14,
            borderTop: '1px solid var(--line)',
            paddingTop: 12,
          }}>
            <div>
              <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 800, marginBottom: 8 }}>{t.needTitle}</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 7 }}>
                {requirementRows.map(row => {
                  const isMissing = row.status === 'missing';
                  return (
                    <div
                      key={row.key}
                      style={{
                        border: '1px solid var(--line)',
                        borderLeft: `3px solid ${isMissing ? 'var(--warn)' : 'var(--ok)'}`,
                        padding: '7px 8px',
                        background: isMissing
                          ? 'color-mix(in oklch, var(--warn) 6%, transparent)'
                          : 'color-mix(in oklch, var(--ok) 5%, transparent)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <AtlasStatusBadge status={isMissing ? 'pending' : 'approved'} label={isMissing ? t.missing : t.filled} compact soft />
                        <span style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {row.label}
                        </span>
                      </div>
                      <div style={{ marginTop: 5, color: 'var(--fg-mute)', fontSize: 11, lineHeight: 1.4 }}>
                        {row.help}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div>
              <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 800, marginBottom: 8 }}>{t.missingTitle}</div>
              {missingRows.length ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                  {missingRows.map(row => (
                    <div
                      key={row.key}
                      style={{
                        border: '1px solid color-mix(in oklch, var(--warn) 45%, var(--line))',
                        background: 'color-mix(in oklch, var(--warn) 8%, transparent)',
                        padding: '7px 8px',
                      }}
                    >
                      <div style={{ color: 'var(--warn)', fontSize: 12, fontWeight: 800 }}>{row.label}</div>
                      <div style={{ marginTop: 4, color: 'var(--fg-mute)', fontSize: 11, lineHeight: 1.4 }}>{row.help}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: 'var(--ok)', fontSize: 12, lineHeight: 1.45 }}>{t.missingEmpty}</div>
              )}
            </div>
          </div>
        ) : null}
        {importStatus ? (
          <div style={{ marginTop: 10, color: importStatus.includes('failed') ? 'var(--warn)' : 'var(--fg-mute)', fontSize: 11 }}>
            {importStatus}
          </div>
        ) : null}
      </div>

      ) : (
        <div style={{
          border: '1px solid var(--line)',
          background: 'var(--bg-1)',
          padding: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <div style={{ color: 'var(--fg)', fontSize: 15, fontWeight: 800 }}>{t.title}</div>
            <code className="acc">{data.ip}</code>
            <span style={{ flex: 1 }} />
            <AtlasStatusBadge status="approved" label={t.approved} count={summary.approved || 0} compact soft />
            <AtlasStatusBadge status="pending" label={t.pending} count={summary.pending || 0} compact soft />
            <button className="mini-btn" type="button" onClick={onRefresh}>{t.refresh}</button>
            <button className="mini-btn" type="button" onClick={onBack}>{t.chat}</button>
          </div>
          <div style={{ marginTop: 7, color: 'var(--fg-mute)', fontSize: 12, lineHeight: 1.45 }}>
            {t.subtitle}
          </div>
        </div>
      )}

      {!checklistOnly ? (
        <>
      <div style={{
        border: '1px solid var(--line)',
        padding: 10,
        background: 'color-mix(in oklch, var(--bg-1) 75%, transparent)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <div style={{ fontSize: 11, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            {t.sessions}
          </div>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>{currentSessionRows.length} ssot-gen</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 8 }}>
          {currentSessionRows.length ? currentSessionRows.slice(0, 12).map(row => {
            const active = normalizeUiSession(row.session) === normalizeUiSession(activeSession || data.session || '');
            const rowSummary = row.summary || {};
            return (
              <button
                key={row.session}
                type="button"
                onClick={() => onSelectSession && onSelectSession(row)}
                style={{
                  textAlign: 'left',
                  border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
                  background: active ? 'color-mix(in oklch, var(--accent) 12%, transparent)' : 'transparent',
                  color: 'var(--fg)',
                  padding: '8px 9px',
                  cursor: 'pointer',
                  fontFamily: 'var(--mono)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AtlasStatusBadge status={row.approved ? 'approved' : (row.status || 'draft')} compact />
                  <span style={{ flex: 1 }} />
                  <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>{row.workflow || 'ssot-gen'}</span>
                </div>
                <div style={{ marginTop: 5, fontSize: 12, color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {row.ip || '(no ip)'}
                </div>
                <div style={{ marginTop: 3, fontSize: 10, color: 'var(--fg-mute)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {row.session}
                </div>
                <div style={{ marginTop: 6, fontSize: 10 }}>
                  <AtlasStatusBadge status="approved" label={t.approved} count={rowSummary.approved || 0} compact soft />
                  <span style={{ color: 'var(--fg-mute)' }}> / </span>
                  <AtlasStatusBadge status="pending" label={t.pending} count={rowSummary.pending || 0} compact soft />
                </div>
              </button>
            );
          }) : (
            <div style={{ color: 'var(--fg-mute)', fontSize: 12 }}>{t.noSaved}</div>
          )}
        </div>
      </div>

      {sections.length ? (() => {
        const sectionsList = sections;
        // Resolve which section to show. If user clicked one, honor that.
        // Otherwise default to the first section that still has pending QAs,
        // falling back to the first section.
        const firstWithPending = sectionsList.find(s => (s.pending || []).length > 0);
        const fallbackId = (firstWithPending || sectionsList[0])?.id;
        const activeId = activeSectionId && sectionsList.some(s => s.id === activeSectionId)
          ? activeSectionId
          : fallbackId;
        const active = sectionsList.find(s => s.id === activeId) || sectionsList[0];
        // Collect all pending items across all sections for the global submit bar.
        const allPending = sectionsList.flatMap(s => (s.pending || []));
        const answerableAllPending = allPending.filter(item => hasPendingAnswer(pendingDraft(item)));
        const submitAll = () => {
          if (!onSubmitPending) return;
          if (!answerableAllPending.length) return;
          const bundle = answerableAllPending.map(item => ({ item, draft: pendingDraft(item) }));
          // Build a single combined prompt that lists every answered pending QA.
          const ip = data?.ip || activeIp || 'current IP';
          const header = `# Submit ${bundle.length} pending QA answer${bundle.length === 1 ? '' : 's'} for ${ip}`;
          const segments = bundle.map(({ item, draft }, i) => {
            const body = buildPendingInputText(item, draft).replace(/^### .*\n?/, '');
            return `## [${i + 1}/${bundle.length}] ${item.decision_key || 'qa'}\n${body}`;
          });
          const combined = [header, '', ...segments].join('\n\n');
          onSubmitPending(bundle, combined);
        };
        return (
          <div style={{
            border: '1px solid var(--line)',
            background: 'var(--bg-1)',
            display: 'flex',
            flex: 1,
            minHeight: 0,
          }}>
            {/* Left column — section tabs (vertical) */}
            <div style={{
              width: 260,
              flex: '0 0 260px',
              borderRight: '1px solid var(--line)',
              padding: 10,
              minHeight: 0,
              overflowY: 'auto',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  {t.toc}
                </div>
                <span style={{ flex: 1 }} />
                {onSubmitPending && allPending.length > 0 ? (
                  <button
                    type="button"
                    className="mini-btn"
                    disabled={!answerableAllPending.length}
                    title={answerableAllPending.length
                      ? `${t.send} all ${answerableAllPending.length} pending`
                      : t.sendNeedAnswer}
                    onClick={submitAll}
                    style={{
                      background: answerableAllPending.length ? 'var(--cyan)' : undefined,
                      color: answerableAllPending.length ? 'var(--bg-0)' : undefined,
                      fontWeight: answerableAllPending.length ? 600 : undefined,
                      opacity: answerableAllPending.length ? 1 : 0.45,
                      cursor: answerableAllPending.length ? 'pointer' : 'not-allowed',
                      fontSize: 10,
                    }}
                  >
                    {t.send} {answerableAllPending.length || ''}
                  </button>
                ) : null}
              </div>
              {sectionsList.map(section => {
                const pendingCount = (section.pending || []).length;
                const approvedCount = (section.approved || []).length;
                const isActive = section.id === activeId;
                return (
                  <button
                    key={section.id}
                    type="button"
                    onClick={() => setActiveSectionId(section.id)}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      border: '1px solid var(--line)',
                      borderLeft: `3px solid ${isActive
                        ? 'var(--cyan)'
                        : (pendingCount > 0 ? 'var(--warn)' : 'var(--ok)')}`,
                      background: isActive
                        ? 'color-mix(in oklch, var(--cyan) 8%, transparent)'
                        : 'transparent',
                      color: 'var(--fg)',
                      padding: '6px 8px',
                      cursor: 'pointer',
                      fontFamily: 'var(--mono)',
                      marginBottom: 4,
                    }}
                  >
                    <div style={{ fontSize: 11, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {section.title}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--fg-mute)', marginTop: 3 }}>
                      {approvedCount} {t.approved} / {pendingCount} {t.pending}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Right column — active section's QA cards */}
            <div style={{
              flex: 1,
              padding: 12,
              overflowY: 'auto',
              minWidth: 0,
              minHeight: 0,
            }}>
              {active ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 10 }}>
                    <div style={{ color: 'var(--fg)', fontSize: 13, fontWeight: 700 }}>{active.title}</div>
                    <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                      {(active.approved || []).length} {t.approved} / {(active.pending || []).length} {t.pending}
                    </span>
                  </div>
                  {['pending', 'approved'].map(grp => {
                    const list = (grp === 'pending' ? active.pending : active.approved) || [];
                    if (!list.length) return null;
                    const collapsed = closedStatusGroups.has(grp);
                    const toggle = () => setClosedStatusGroups(prev => {
                      const next = new Set(prev);
                      if (next.has(grp)) next.delete(grp);
                      else next.add(grp);
                      return next;
                    });
                    return (
                      <div key={grp} style={{ marginBottom: grp === 'pending' ? 10 : 0 }}>
                        <div
                          role="button"
                          tabIndex={0}
                          onClick={toggle}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              toggle();
                            }
                          }}
                          style={{
                            marginBottom: 6,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            cursor: 'pointer',
                            userSelect: 'none',
                          }}
                          title={collapsed ? 'click to expand' : 'click to collapse'}
                        >
                          <span style={{ color: 'var(--fg-mute)', fontSize: 11 }}>
                            {collapsed ? '▶' : '▼'}
                          </span>
                          <AtlasStatusBadge
                            status={grp}
                            label={grp === 'pending' ? t.pending : t.approved}
                            count={list.length}
                            compact
                            soft
                          />
                        </div>
                        {!collapsed && list.map(item => renderQa(item, grp))}
                      </div>
                    );
                  })}
                </>
              ) : null}
            </div>
          </div>
        );
      })() : (
        <div style={{ padding: 20, color: 'var(--fg-mute)', fontSize: 12 }}>
          {t.noCards} <code style={{ color: 'var(--cyan)' }}>/new-ip</code> / <code style={{ color: 'var(--cyan)' }}>/grill-me</code>.
        </div>
      )}
        </>
      ) : null}
    </div>
  );
};

// ── ask_user — compact in-feed tool-call line ─────────────────────
// Renders as `action: ask_user(...)` matching the other tool calls,
// then (when submitted) appends an `obs:` line with the user's reply.
const AskUserCall = ({ flowId, state, dir }) => {
  const flow = window.QA_FLOWS[flowId];
  if (!flow || !state) return null;
  const submitted = state.submitted;
  const isBatched = !!state.batched;
  let sel = [];
  let replySummary = '';
  let argSummary;
  if (isBatched) {
    const tabCount = (flow.questions || []).length;
    const allSel = (state.states || []).map((ts, i) => {
      const ss = (ts.opts || []).filter(o => o.selected).map(o => o.label).join(', ');
      const c = (ts.custom || '').trim();
      return `Q${i + 1}: ${ss}${c ? (ss ? ' · ' : '') + 'note=' + c : ''}`;
    });
    replySummary = allSel.join(' | ');
    argSummary = `flow="${flowId}", batched=${tabCount} questions`;
  } else {
    sel = state.opts.filter(o => o.selected);
    replySummary = sel.map(o => o.label).join(', ') + (state.custom ? `, +"${state.custom}"` : '');
    argSummary = `flow="${flowId}", question="${flow.question.length > 48 ? flow.question.slice(0, 48) + '…' : flow.question}", kind=${flow.kind}, options=${flow.options.length}`;
  }

  return (
    <>
      <div className="react-block action">
        <span className="rb-tag">action</span>
        <span>
          <b style={{ color: 'var(--tool-accent)' }}>ask_user</b>
          <span className="mute">(</span>
          <span style={{ color: 'var(--fg-mute)' }}>{argSummary}</span>
          <span className="mute">)</span>
          {!submitted && (
            <span className="warn" style={{
              marginLeft: 10, fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase',
              padding: '1px 6px', border: '1px solid var(--warn)', borderRadius: 2,
              background: 'color-mix(in oklch, var(--warn) 12%, transparent)',
            }}>
              ⌨ input pending · reply below
            </span>
          )}
        </span>
      </div>
      {submitted && (
        <div className="react-block obs">
          <span className="rb-tag">obs</span>
          <span><span className="ok">✓</span> user replied · <span style={{ color: 'var(--fg)' }}>{replySummary || '(no selection)'}</span></span>
        </div>
      )}
    </>
  );
};

// ── ask_user — past Q&A round-trips, newest first ────────────────
// Persisted to localStorage in workspace.jsx so the trail survives a
// page reload. Renders below the active SSOT board on the Q&A tab.
const QaHistoryPanel = ({ history, onClear }) => {
  if (!history || history.length === 0) return null;
  const fmtTs = (ts) => {
    try {
      const d = new Date(ts);
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      const mo = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      return `${mo}-${dd} ${hh}:${mm}`;
    } catch (_) { return ''; }
  };
  return (
    <div style={{ marginTop: 18 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8,
        paddingBottom: 6, borderBottom: '1px dashed var(--line)',
        fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
      }}>
        <span className="acc" style={{ fontWeight: 700 }}>▸ Q&amp;A history</span>
        <span className="mute">·</span>
        <span>{history.length} answered</span>
        <span style={{ flex: 1 }} />
        <span
          onClick={onClear}
          style={{ cursor: 'pointer', color: 'var(--fg-mute)', fontSize: 10 }}
          title="Clear local Q&A history (does not affect the agent's session)"
        >clear</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {history.map((entry, i) => (
          <details
            key={entry.flowId + ':' + entry.ts + ':' + i}
            open={i === 0}
            style={{
              border: '1px solid var(--line)',
              borderLeft: '2px solid var(--ok)',
              borderRadius: 2, padding: '6px 10px',
              background: 'color-mix(in oklch, var(--ok) 4%, transparent)',
            }}
          >
            <summary style={{
              cursor: 'pointer', fontSize: 12, fontFamily: 'var(--mono)',
              listStyle: 'none', display: 'flex', gap: 8, alignItems: 'center',
            }}>
              <span style={{ color: 'var(--ok)', fontWeight: 700 }}>☑</span>
              <span style={{ color: 'var(--fg)' }}>
                {entry.items.length} question{entry.items.length === 1 ? '' : 's'}
                {entry.ip ? ` · ${entry.ip}` : ''}
                {entry.workflow ? ` · ${entry.workflow}` : ''}
              </span>
              <span style={{ flex: 1 }} />
              <span className="mute" style={{ fontSize: 10 }}>{fmtTs(entry.ts)}</span>
            </summary>
            <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {entry.items.map((q, qi) => {
                const sels = (q.selected || []).map(s => s.label).join(', ');
                const ans = sels
                  ? sels + (q.custom ? ` · note: "${q.custom}"` : '')
                  : (q.custom ? `note: "${q.custom}"` : '(no answer)');
                return (
                  <div key={qi} style={{
                    fontSize: 12, fontFamily: 'var(--mono)',
                    paddingLeft: 6, borderLeft: '1px solid var(--line-2)',
                  }}>
                    <div style={{ color: 'var(--fg-dim)' }}>
                      Q{qi + 1}. {q.question}
                    </div>
                    <div style={{ color: 'var(--fg)', marginTop: 1 }}>
                      <span className="mute">→ </span>{ans}
                    </div>
                  </div>
                );
              })}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
};

// ── ask_user — inline bottom prompt (replaces the regular input row) ──
// Mirrors the screenshot: numbered options, inline `[ ]`/`[✓]`, single
// custom-text line, Submit + "Chat about this" affordances, hint footer.
//
// Batched mode (mirror of textual UI's breadcrumb tabs): when the flow
// carries `flow.batched === true` and `flow.questions: [...]`, a tab
// strip renders above the question — one tab per question with a
// ☐/☒ "answered" marker, plus a final ✔ Submit tab. Active tab
// content is shown using the same option/custom widgets; state lives
// in `state.states[active]` instead of the flat `state.opts/state.custom`.
const AskUserPrompt = ({ flowId, state, sel, intent, fullHeight = false, onToggle, onCustom, onSubmit, onChat, onSel, onSetTab, onAdvance }) => {
  const flow = window.QA_FLOWS[flowId];
  if (!flow || !state) return null;

  // Batched flow virtualization — derive the "view" for the active tab
  // and reuse all the existing single-question rendering below.
  const isBatched = !!state.batched;
  const tabCount = isBatched ? (flow.questions || []).length : 0;
  const active = isBatched ? (state.active || 0) : 0;
  const isSubmitTab = isBatched && active === tabCount;
  // Active tab view (used by the option/custom widgets below)
  const tabState = isBatched
    ? (state.states && state.states[active]) || { opts: [], custom: '' }
    : state;
  const tabFlowKind = isBatched && !isSubmitTab ? flow.questions[active].kind : flow.kind;
  const tabFlowMultiline = !!(isBatched && !isSubmitTab ? flow.questions[active].multiline : flow.multiline);
  const tabAnswered = (i) => {
    const ts = state.states && state.states[i];
    if (!ts) return false;
    return (ts.opts || []).some(o => o.selected) || (ts.custom || '').trim().length > 0;
  };
  const allAnswered = isBatched
    ? (state.states || []).every((_, i) => tabAnswered(i))
    : true;

  const goNextBatchedStep = () => {
    if (!isBatched) return false;
    if (isSubmitTab) {
      if (allAnswered) onSubmit(flowId);
      return true;
    }
    if (active < tabCount - 1) {
      onAdvance ? onAdvance(flowId) : onSetTab && onSetTab(flowId, active + 1);
      return true;
    }
    if (allAnswered) {
      onSubmit(flowId);
    } else {
      onSetTab && onSetTab(flowId, tabCount);
    }
    return true;
  };

  const opts = tabState.opts || [];
  const customIdx = opts.length;       // row index for custom-text line
  const submitIdx = opts.length + 1;   // Submit menu line
  const chatIdx   = opts.length + 2;   // "Chat about this" menu line
  const lastIdx   = chatIdx;

  const onKey = (e) => {
    // Batched flow: ⌘/⌃ + ←/→ moves the keyboard cursor between
    // question blocks (each Q renders its own block; the active block
    // is highlighted and owns the option/custom cursor).
    if (isBatched) {
      if (e.key === 'ArrowLeft' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.max(0, active - 1)); return;
      }
      if (e.key === 'ArrowRight' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.min(tabCount - 1, active + 1)); return;
      }
    }
    if (e.key === 'ArrowDown' || (e.key === 'j' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.min(sel + 1, lastIdx)); return;
    }
    if (e.key === 'ArrowUp' || (e.key === 'k' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.max(sel - 1, 0)); return;
    }
    if (e.key === ' ' && sel < opts.length) {
      // When focus is in the custom-answer input/textarea, space must
      // pass through to the field. Without this guard the parent
      // div's keydown intercepts and toggles the selected option
      // instead, swallowing every space the user types.
      const ae = document.activeElement;
      const aeTag = ae && ae.tagName;
      if (aeTag === 'INPUT' || aeTag === 'TEXTAREA' || (ae && ae.isContentEditable)) return;
      e.preventDefault(); onToggle(flowId, opts[sel].id); return;
    }
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      const activeEl = document.activeElement;
      const isCustomInput = activeEl && activeEl.classList && activeEl.classList.contains('askcustom');
      if (isCustomInput && tabFlowMultiline && !e.metaKey && !e.ctrlKey) return;
      e.preventDefault();
      // Custom-input Enter: in batched, advance to next question (or
      // submit-all on the last); in single, submit immediately when the
      // text isn't empty so a one-shot QA can be answered with Enter.
      if (isCustomInput) {
        if (isBatched) { goNextBatchedStep(); return; }
        if ((tabState.custom || '').trim() || opts.some(o => o.selected)) {
          onSubmit(flowId);
        }
        return;
      }
      if (sel < opts.length) {
        onToggle(flowId, opts[sel].id);
        // Batched + single-kind: advance to next question (or submit
        // when on the last one and everything else is answered).
        if (isBatched && tabFlowKind !== 'multi') { goNextBatchedStep(); return; }
        // Non-batched + single-kind (one-question flow): Enter
        // immediately submits — the user just picked their answer.
        if (!isBatched && tabFlowKind === 'single') { onSubmit(flowId); return; }
        return;
      }
      if (sel === customIdx) {
        if (isBatched && (tabState.custom || '').trim()) { goNextBatchedStep(); return; }
        const el = e.currentTarget.querySelector('input.askcustom, textarea.askcustom'); el?.focus(); return;
      }
      if (sel === submitIdx) {
        if (isBatched) { if (allAnswered) onSubmit(flowId); return; }
        onSubmit(flowId);
        return;
      }
      if (sel === chatIdx)   { onChat(flowId); return; }
    }
    if (e.key === 'Escape') { e.preventDefault(); onSel(0); }
  };

  const renderQuestionBlock = (i, block, bs, kind) => (
    <AskUserQuestionBlock
      key={i}
      index={i}
      block={block}
      blockState={bs}
      kind={kind}
      isBatched={isBatched}
      isActive={!isBatched || i === active}
      answered={tabAnswered(i)}
      selectedIndex={sel}
      onEnsureActive={(idx) => {
        if (isBatched && idx !== active && onSetTab) onSetTab(flowId, idx);
      }}
      onSelectIndex={onSel}
      onToggleOption={(optionId) => onToggle(flowId, optionId)}
      onCustom={(value) => onCustom(flowId, value)}
      onSelectAll={(blockOpts) => {
        blockOpts.forEach(o => { if (!o.selected && !o.locked) onToggle(flowId, o.id); });
      }}
      onClearAll={(blockOpts) => {
        blockOpts.forEach(o => { if (o.selected && !o.locked) onToggle(flowId, o.id); });
      }}
    />
  );

  return (
    <div
      className="ask-prompt fade-in"
      tabIndex={0}
      onKeyDown={onKey}
      style={{
        border: `1px solid var(--accent)`,
        borderLeftWidth: 3,
        background: 'var(--bg-2)',
        padding: '10px 14px 8px',
        outline: 'none',
        boxShadow: '0 -2px 0 0 color-mix(in oklch, var(--accent) 25%, transparent)',
        height: fullHeight ? '100%' : undefined,
        minHeight: fullHeight ? 0 : undefined,
        overflow: fullHeight ? 'auto' : undefined,
      }}
    >
      {/* header — mimics the screenshot: "▸ ask_user · ✓ Submit" */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8,
        fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
      }}>
        <span className="acc" style={{ fontWeight: 700 }}>▸ ask_user</span>
        <span className="mute">·</span>
        <span className="ok" style={{ fontWeight: 600, opacity: sel === submitIdx ? 1 : 0.6 }}>✓ Submit</span>
        <span className="mute">·</span>
        <span className="mute">{flow.stage} · step {flow.step}/{flow.total}</span>
        <span style={{ flex: 1 }} />
        {intent === 'plan' && (
          <span className="warn" style={{ fontSize: 10, fontWeight: 700 }}>◐ plan mode · still asks</span>
        )}
        <span className="mute" style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10 }}>
          {tabFlowKind === 'multi' ? 'multi-select' : tabFlowKind === 'input' ? 'text' : 'single-select'}
        </span>
        {isBatched && (
          <span
            className={allAnswered ? 'ok' : 'mute'}
            style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10, marginLeft: 6, fontWeight: 600 }}
          >
            · {(state.states || []).filter((_, i) => tabAnswered(i)).length}/{tabCount} answered
          </span>
        )}
      </div>

      {/* questions — single block when not batched, stacked blocks when batched */}
      {isBatched
        ? (flow.questions || []).map((q, i) => {
            const ts = (state.states || [])[i] || { opts: [], custom: '' };
            const k = q.kind === 'multi' ? 'multi' : q.kind === 'input' ? 'input' : 'single';
            return renderQuestionBlock(i, q, ts, k);
          })
        : renderQuestionBlock(0, flow, state, tabFlowKind)}

      {/* submit row — for batched, gates on allAnswered and submits all */}
      <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 0 }}>
        <div
          onClick={() => {
            if (isBatched) { if (allAnswered) onSubmit(flowId); }
            else onSubmit(flowId);
          }}
          style={{
            padding: '4px 8px',
            background: sel === submitIdx ? 'color-mix(in oklch, var(--ok) 18%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === submitIdx ? 'var(--ok)' : 'transparent'}`,
            cursor: (isBatched && !allAnswered) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
            color: sel === submitIdx ? 'var(--ok)' : 'var(--fg)',
            fontWeight: sel === submitIdx ? 600 : 400,
            opacity: (isBatched && !allAnswered) ? 0.6 : 1,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>
          {isBatched ? `Submit all (${(state.states || []).filter((_, i) => tabAnswered(i)).length}/${tabCount})` : 'Submit'}
          {!isBatched && (
            <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>
              ({(opts.filter(o => o.selected) || []).length}{tabState.custom ? '+1' : ''} reply)
            </span>
          )}
        </div>
        <div
          onClick={() => { onSel(chatIdx); onChat(flowId); }}
          style={{
            padding: '4px 8px',
            background: sel === chatIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === chatIdx ? 'var(--accent)' : 'transparent'}`,
            cursor: 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>Chat about this
          <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>(send a free-form message instead)</span>
        </div>
      </div>

      {/* hint footer — terminal-style */}
      <div className="mute" style={{
        marginTop: 8, paddingTop: 6, borderTop: '1px dashed var(--line)',
        fontSize: 11, display: 'flex', gap: 14, flexWrap: 'wrap',
      }}>
        <span><Kbd>↵</Kbd> {isBatched ? 'select & next' : 'select & submit'}</span>
        <span><Kbd>↑↓</Kbd>/<Kbd>j k</Kbd> navigate</span>
        <span><Kbd>Space</Kbd> toggle</span>
        <span><Kbd>Tab</Kbd> next field</span>
        {isBatched && <span><Kbd>⌘/⌃ ←→</Kbd> switch question</span>}
        <span><Kbd>Esc</Kbd> top</span>
      </div>
    </div>
  );
};

const SSOT_SECTION_LABELS = {
  schema_version: 'Schema Version',
  metadata: 'Metadata',
  top_module: 'Top Module',
  sub_modules: 'Submodules',
  parameters: 'Parameters',
  io_list: 'I/O List',
  features: 'Features',
  dataflow: 'Dataflow',
  function_model: 'Function Model',
  cycle_model: 'Cycle Model',
  clock_reset_domains: 'Clock / Reset Domains',
  cdc_requirements: 'CDC Requirements',
  rdc_requirements: 'RDC Requirements',
  registers: 'Registers',
  memory: 'Memory',
  interrupts: 'Interrupts',
  fsm: 'FSM',
  timing: 'Timing',
  power: 'Power',
  security: 'Security',
  errors: 'Errors',
  debug: 'Debug',
  integration: 'Integration',
  dft: 'DFT',
  synthesis: 'Synthesis',
  coding_rules: 'Coding Rules',
  reuse_modules: 'Reuse Modules',
  custom: 'Custom Requirements',
  dir_structure: 'Directory Structure',
  filelist: 'File List',
  dv_plan: 'DV Plan',
  quality_gates: 'Quality Gates',
  traceability: 'Traceability',
  workflow_todos: 'Workflow Todos',
  generation_flow: 'Generation Flow',
  decomposition: 'Decomposition',
};

const SSOT_REVIEW_FOCUS = {
  metadata: ['IP name, owner, source, and version are reviewable.', 'Assumptions and scope boundaries are explicit.'],
  top_module: ['Module name, responsibility, clocks, and resets match the intended IP.', 'No implementation detail hides behind placeholder text.'],
  sub_modules: ['Hierarchy is complete enough for RTL partitioning.', 'Module ownership and interfaces are not ambiguous.'],
  parameters: ['Defaults, ranges, legal values, and units are specified.', 'Parameter interactions are called out where they affect behavior.'],
  io_list: ['Every port has direction, width, clock/reset domain, and semantic description.', 'Handshake and sideband conventions are visible.'],
  features: ['Required and optional features are separated.', 'Feature dependencies and disabled states are stated.'],
  dataflow: ['Ingress, transformation, storage, and egress path are understandable.', 'Backpressure, buffering, and ordering rules are explicit.'],
  function_model: ['Functional behavior is stated as reviewable rules.', 'Corner cases and invalid inputs have expected outcomes.'],
  cycle_model: ['Latency, throughput, ordering, and cycle-level promises are concrete.', 'Reset and stall behavior are included.'],
  clock_reset_domains: ['Clock/reset ownership, polarity, and synchronization boundaries are clear.', 'Reset release assumptions are reviewable.'],
  cdc_requirements: ['All clock crossings name source/destination domains.', 'Synchronizer type and data-valid guarantees are explicit.'],
  rdc_requirements: ['Reset crossings and release ordering are stated.', 'Required synchronizers or constraints are named.'],
  registers: ['Address map, access policy, reset values, and side effects are complete.', 'Reserved bits and write-one semantics are visible.'],
  memory: ['Depth, width, ports, arbitration, and initialization are specified.', 'ECC/parity and read-under-write behavior are stated if relevant.'],
  interrupts: ['Sources, masks, clears, aggregation, and pulse/level behavior are reviewable.', 'Software-visible status is aligned with registers.'],
  fsm: ['States, transitions, guards, and error paths are complete.', 'Reset state and illegal-state recovery are specified.'],
  timing: ['Latency budgets, max frequencies, and timing exceptions are justified.', 'Handshake timing assumptions are not implicit.'],
  power: ['Clock gating, retention, isolation, and low-power assumptions are visible.', 'Power-state behavior is consistent with reset/CDC sections.'],
  security: ['Threat assumptions, privilege boundaries, and lock/debug behavior are visible.', 'Unsupported security scope is explicit.'],
  errors: ['Detection, reporting, recovery, and fatal/non-fatal split are clear.', 'Error injection or observability hooks are named when needed.'],
  debug: ['Counters, traces, debug registers, and visibility points are reviewable.', 'Debug behavior does not conflict with security/power constraints.'],
  integration: ['SoC integration assumptions, dependencies, and external contracts are stated.', 'Tie-offs, strap values, and constraints are visible.'],
  dft: ['Scan, MBIST/LBIST, test modes, and clock/reset handling are covered.', 'DFT exceptions are justified.'],
  synthesis: ['Target library, constraints, generated blocks, and synthesis assumptions are visible.', 'Non-synthesizable modeling is excluded from RTL scope.'],
  coding_rules: ['Style and lint contracts are specific enough for generated RTL.', 'Naming, reset, and clocking rules match project conventions.'],
  reuse_modules: ['Reused IP versions, configuration, and integration contracts are explicit.', 'Ownership and verification reuse assumptions are stated.'],
  dir_structure: ['Generated file layout is predictable.', 'Human-owned and generated files are separated.'],
  filelist: ['Required source, include, constraint, and sim files are enumerated.', 'Generation outputs line up with downstream tools.'],
  dv_plan: ['Test intent, coverage targets, sequences, and scoreboards trace to requirements.', 'Corner cases and negative tests are visible.'],
  quality_gates: ['Lint, sim, formal, CDC/RDC, and signoff gates have pass criteria.', 'Known waivers or limits are tracked.'],
  traceability: ['Requirements, SSOT sections, RTL, tests, and gates are connected.', 'Untraced or stale entries are easy to spot.'],
  workflow_todos: ['Human decisions and agent follow-ups are separated.', 'Pending items are actionable and scoped.'],
  generation_flow: ['Generated artifact order and handoff points are clear.', 'Review gates stop unsafe downstream generation.'],
  decomposition: ['Blocks, ownership, dependencies, and generation order are clear.', 'Interfaces between generated units are reviewable.'],
};

const SSOT_DIGEST_VIEWS = [
  { id: 'overview', label: 'Brief', keys: ['top_module', 'features', 'sub_modules', 'io_list', 'registers', 'dataflow'] },
  { id: 'architecture', label: 'Architecture', keys: ['sub_modules', 'decomposition'] },
  { id: 'interfaces', label: 'Interfaces', keys: ['io_list', 'decomposition'] },
  { id: 'feature_map', label: 'Feature Map', keys: ['features', 'sub_modules', 'decomposition', 'function_model', 'cycle_model', 'registers', 'dataflow'] },
  { id: 'function_model', label: 'Function Model', keys: ['function_model'] },
  { id: 'fsm', label: 'FSM', keys: ['fsm'] },
  { id: 'cycle_model', label: 'Cycle Model', keys: ['cycle_model', 'timing'] },
  { id: 'registers', label: 'Register Map', keys: ['registers'] },
  { id: 'dataflow', label: 'Dataflow', keys: ['dataflow'] },
  { id: 'clocking', label: 'CDC / Reset', keys: ['clock_reset_domains', 'cdc_requirements', 'rdc_requirements'] },
  { id: 'review_gaps', label: 'Review Gaps', keys: ['workflow_todos', 'quality_gates', 'traceability', 'top_module', 'features', 'sub_modules', 'io_list', 'registers', 'dataflow', 'function_model', 'cycle_model'] },
  { id: 'gates', label: 'Gates', keys: [] },
  { id: 'raw_yaml', label: 'Raw YAML', keys: [] },
];

const ssotPathOf = (entry) => typeof entry === 'string' ? entry : (entry && entry.path) || '';

const ssotTitleFor = (key) => {
  const raw = String(key || '').trim();
  if (!raw) return 'Untitled Section';
  if (SSOT_SECTION_LABELS[raw]) return SSOT_SECTION_LABELS[raw];
  return raw.split(/[_\-.]+/).filter(Boolean)
    .map(s => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ');
};

const trimSsotValue = (value, max = 130) => {
  const text = String(value ?? '').replace(/^['"]|['"]$/g, '').replace(/\s+/g, ' ').trim();
  if (!text) return '';
  return text.length > max ? text.slice(0, max - 1) + '...' : text;
};

const mdCell = (value) => {
  const text = trimSsotValue(value, 220).replace(/\|/g, '\\|');
  return text || '-';
};

const splitSsotSections = (content) => {
  const lines = String(content || '').split(/\r?\n/);
  const sections = [];
  let current = null;
  const push = () => {
    if (!current) return;
    const text = current.lines.join('\n').trimEnd();
    if (text.trim()) {
      const section = { ...current, text, lineCount: current.lines.length };
      section.summary = summarizeSsotSection(section);
      sections.push(section);
    }
  };

  lines.forEach((line, idx) => {
    const m = line.match(/^([A-Za-z_][A-Za-z0-9_.-]*):(?:\s*(.*))?$/);
    if (m) {
      push();
      current = { key: m[1], value: (m[2] || '').trim(), startLine: idx + 1, lines: [line] };
    } else if (current) {
      current.lines.push(line);
    }
  });
  push();
  return sections;
};

const summarizeSsotSection = (section) => {
  const lines = String(section.text || '').split(/\r?\n/);
  const facts = [];
  const groups = [];
  const listPreview = [];
  const gaps = [];
  let listItems = 0;

  lines.forEach((line, idx) => {
    const list = line.match(/^\s*-\s+(.+)/);
    if (list) {
      listItems += 1;
      if (listPreview.length < 8) listPreview.push(trimSsotValue(list[1], 180));
    }

    const group = line.match(/^\s{2}([A-Za-z0-9_.-]+):\s*(?:#.*)?$/);
    if (group && !groups.includes(group[1]) && groups.length < 12) groups.push(group[1]);

    const fact = line.match(/^\s{2,}([A-Za-z0-9_.-]+):\s*(.+?)\s*$/);
    if (fact && facts.length < 12) {
      const value = trimSsotValue(fact[2]);
      if (value && !['|', '>', '{}', '[]'].includes(value)) facts.push({ key: fact[1], value });
    }

    if (/\b(TBD|TODO|FIXME|unknown|placeholder|pending|null|assumption|unspecified)\b/i.test(line)) {
      const cleaned = trimSsotValue(line, 220);
      if (cleaned && gaps.length < 10) gaps.push({ line: section.startLine + idx, text: cleaned });
    }
  });

  if (section.value && facts.length < 12) facts.unshift({ key: section.key, value: section.value });
  return { facts, groups, listItems, listPreview, gaps, lineCount: lines.length };
};

const rxEscape = (text) => String(text || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const indentOf = (line) => (String(line || '').match(/^\s*/) || [''])[0].length;

const stripYamlScalar = (value) => {
  let text = String(value ?? '').trim();
  text = text.replace(/^['"]|['"]$/g, '');
  return text.replace(/\s+/g, ' ').trim();
};

const fieldFromText = (text, key, max = 260) => {
  const lines = String(text || '').split(/\r?\n/);
  const rx = new RegExp(`^\\s*(?:-\\s*)?${rxEscape(key)}:\\s*(.*)$`);
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(rx);
    if (!m) continue;
    const base = indentOf(lines[i]);
    const parts = [];
    if (m[1] && !['|', '>'].includes(m[1].trim())) parts.push(m[1].trim());
    for (let j = i + 1; j < lines.length; j++) {
      const line = lines[j];
      const trimmed = line.trim();
      if (!trimmed) continue;
      const ind = indentOf(line);
      if (ind <= base) break;
      if (ind === base + 2 && /^[A-Za-z0-9_.-]+:\s*/.test(trimmed)) break;
      if (/^-\s+[A-Za-z0-9_.-]+:\s*/.test(trimmed)) break;
      parts.push(trimmed.replace(/^-\s+/, ''));
    }
    return trimSsotValue(stripYamlScalar(parts.join(' ')), max);
  }
  return '';
};

const sectionByKey = (sections, key) => (sections || []).find(s => s.key === key) || null;
const sectionsForKeys = (sections, keys) => (keys || []).map(k => sectionByKey(sections, k)).filter(Boolean);

const sectionFact = (section, key, fallback = '') => {
  if (!section) return fallback;
  const fromText = fieldFromText(section.text, key);
  if (fromText) return fromText;
  const fact = ((section.summary && section.summary.facts) || []).find(f => f.key === key);
  return fact ? fact.value : fallback;
};

const listBlocksFromText = (text, parentKey = '') => {
  const lines = String(text || '').split(/\r?\n/);
  let start = 0;
  let parentIndent = -1;
  if (parentKey) {
    const parentRx = new RegExp(`^\\s*${rxEscape(parentKey)}:\\s*(?:#.*)?$`);
    const idx = lines.findIndex(line => parentRx.test(line));
    if (idx < 0) return [];
    start = idx + 1;
    parentIndent = indentOf(lines[idx]);
  }

  let listIndent = -1;
  for (let i = start; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (!trimmed) continue;
    const ind = indentOf(lines[i]);
    if (parentKey && ind < parentIndent) break;
    if (parentKey && ind === parentIndent && !trimmed.startsWith('- ') && /^[A-Za-z0-9_.-]+:\s*/.test(trimmed)) break;
    if (trimmed.startsWith('- ')) {
      listIndent = ind;
      start = i;
      break;
    }
  }
  if (listIndent < 0) return [];

  const blocks = [];
  let cur = null;
  for (let i = start; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    const ind = indentOf(line);
    if (parentKey && trimmed && ind < parentIndent) break;
    if (parentKey && trimmed && ind === parentIndent && !trimmed.startsWith('- ') && /^[A-Za-z0-9_.-]+:\s*/.test(trimmed)) break;
    if (trimmed.startsWith('- ') && ind === listIndent) {
      if (cur) blocks.push(cur);
      cur = { startLineOffset: i, lines: [line] };
    } else if (cur) {
      cur.lines.push(line);
    }
  }
  if (cur) blocks.push(cur);
  return blocks.map(b => ({ text: b.lines.join('\n'), startLineOffset: b.startLineOffset }));
};

const listBlocksFromSection = (section, parentKey = '') =>
  section ? listBlocksFromText(section.text, parentKey).map(b => ({
    ...b,
    startLine: section.startLine + b.startLineOffset,
  })) : [];

const inlineYamlObjectFromLine = (line) => {
  const raw = String(line || '').match(/\{(.+)\}/);
  if (!raw) return {};
  return raw[1].split(/,(?=(?:[^'"]*['"][^'"]*['"])*[^'"]*$)/).reduce((acc, part) => {
    const m = part.match(/^\s*([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$/);
    if (m) acc[m[1]] = stripYamlScalar(m[2]);
    return acc;
  }, {});
};

const blockField = (block, key, max = 240) => {
  const direct = fieldFromText(block && block.text, key, max);
  if (direct) return direct;
  const firstLine = String((block && block.text) || '').split(/\r?\n/)[0] || '';
  return trimSsotValue(inlineYamlObjectFromLine(firstLine)[key], max);
};

const blockListValues = (block, parentKey, max = 8) =>
  listBlocksFromText(block && block.text, parentKey)
    .map(b => stripYamlScalar(b.text.split(/\r?\n/)[0].replace(/^\s*-\s*/, '')))
    .filter(Boolean)
    .slice(0, max);

const mapGroupsFromSection = (section, parentKey = '') => {
  if (!section) return [];
  const lines = String(section.text || '').split(/\r?\n/);
  let start = 0;
  let parentIndent = indentOf(lines[0] || '');
  if (parentKey) {
    const rx = new RegExp(`^\\s*${rxEscape(parentKey)}:\\s*(?:#.*)?$`);
    const idx = lines.findIndex(line => rx.test(line));
    if (idx < 0) return [];
    start = idx + 1;
    parentIndent = indentOf(lines[idx]);
  }
  const groups = [];
  let cur = null;
  const wantedIndent = parentKey ? parentIndent + 2 : 2;
  for (let i = start; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) continue;
    const ind = indentOf(line);
    if (parentKey && ind <= parentIndent) break;
    const m = line.match(/^\s*([A-Za-z0-9_.-]+):\s*(.*)$/);
    if (m && ind === wantedIndent && !trimmed.startsWith('- ')) {
      if (cur) groups.push(cur);
      cur = { key: m[1], startLine: section.startLine + i, lines: [line] };
    } else if (cur) {
      cur.lines.push(line);
    }
  }
  if (cur) groups.push(cur);
  return groups.map(g => ({ ...g, text: g.lines.join('\n') }));
};

const extractInterfaces = (section) => listBlocksFromSection(section, 'interfaces').map(block => ({
  name: blockField(block, 'name') || 'interface',
  type: blockField(block, 'type') || 'custom',
  role: blockField(block, 'role'),
  description: blockField(block, 'description', 360),
  ports: listBlocksFromText(block.text, 'ports').map(port => ({
    name: blockField(port, 'name') || stripYamlScalar(port.text.replace(/^\s*-\s*/, '').split(':')[0]),
    direction: blockField(port, 'direction'),
    width: blockField(port, 'width'),
    description: blockField(port, 'description', 220),
  })),
}));

const extractSignalPorts = (section) => listBlocksFromSection(section, 'signals').map(block => ({
  name: blockField(block, 'name') || 'signal',
  direction: blockField(block, 'direction') || blockField(block, 'dir'),
  width: blockField(block, 'width') || '1',
  description: blockField(block, 'description', 220),
}));

const extractReviewInterfaces = (sections, ioSection) => {
  const canonical = extractInterfaces(ioSection);
  const generic = (sections || [])
    .filter(section => section !== ioSection && /(interface|businterfaces|interrupts?)$/i.test(section.key || ''))
    .flatMap(section => {
      const busItems = listBlocksFromSection(section);
      if (busItems.length && /^businterfaces$/i.test(section.key || '')) {
        return busItems.map(block => ({
          name: blockField(block, 'name') || ssotTitleFor(section.key),
          type: blockField(block, 'proto') || blockField(block, 'type') || 'bus',
          role: blockField(block, 'role'),
          description: blockField(block, 'description', 260),
          ports: [],
        }));
      }
      return [{
        name: ssotTitleFor(section.key),
        type: sectionFact(section, 'type') || sectionFact(section, 'proto') || 'interface',
        role: sectionFact(section, 'role'),
        description: sectionFact(section, 'description', ''),
        ports: extractSignalPorts(section),
      }];
    });
  const seen = new Set();
  return [...canonical, ...generic].filter(iface => {
    const key = `${iface.name}:${iface.type}:${iface.role}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return iface.name || iface.description || (iface.ports || []).length;
  });
};

const extractFeatures = (section) => listBlocksFromSection(section).map(block => ({
  name: blockField(block, 'name') || 'Feature',
  trigger: blockField(block, 'trigger', 360),
  datapath: blockField(block, 'datapath', 520),
  control: blockField(block, 'control', 300),
  output: blockField(block, 'output', 360),
}));

// Recursively parse a sub-module block, descending into any nested
// `sub_modules: …` lists declared on the block. Without recursion, the
// BlockDiagram could only ever render one level — adding nested support
// lets a top module wrap its mid-level modules, which themselves wrap
// leaf modules. Only depth-aware code paths use the `children` field;
// existing flat-list consumers ignore it.
const _parseSubmoduleBlock = (block) => ({
  name: blockField(block, 'name') || 'module',
  file: blockField(block, 'file'),
  description: blockField(block, 'description', 360),
  implements: blockListValues(block, 'implements', 6),
  sourceSections: blockListValues(block, 'source_sections', 6),
  interfaces: listBlocksFromText(block.text, 'interfaces').map(iface => ({
    name: blockField(iface, 'name') || 'interface',
    type: blockField(iface, 'type') || 'local',
    inputs: blockListValues(iface, 'inputs', 8),
    outputs: blockListValues(iface, 'outputs', 8),
  })),
  children: listBlocksFromText(block.text, 'sub_modules').map(_parseSubmoduleBlock),
});

const extractSubmodules = (section) => listBlocksFromSection(section).map(_parseSubmoduleBlock);

const extractModuleContracts = (section) => listBlocksFromSection(section, 'module_contracts').map(block => ({
  module: blockField(block, 'module') || blockField(block, 'name') || 'module',
  owns: blockListValues(block, 'owns', 10),
  inputs: blockListValues(block, 'inputs', 12),
  outputs: blockListValues(block, 'outputs', 12),
  implementation: blockField(block, 'implementation_direction', 520)
    || blockField(block, 'implementation', 520)
    || blockField(block, 'approach', 520),
  interfaces: listBlocksFromText(block.text, 'interfaces').map(iface => ({
    name: blockField(iface, 'name') || 'interface',
    type: blockField(iface, 'type') || 'local',
    role: blockField(iface, 'role'),
    inputs: blockListValues(iface, 'inputs', 8),
    outputs: blockListValues(iface, 'outputs', 8),
    description: blockField(iface, 'description', 260),
  })),
}));

const extractRegisters = (section) => {
  const blocks = [
    ...listBlocksFromSection(section, 'register_list'),
    ...listBlocksFromSection(section, 'map'),
  ];
  const source = blocks.length ? blocks : listBlocksFromSection(section);
  return source.map(block => ({
    name: blockField(block, 'name') || 'REG',
    offset: blockField(block, 'offset'),
    width: blockField(block, 'width'),
    access: blockField(block, 'access'),
    reset: blockField(block, 'reset'),
    description: blockField(block, 'description', 300),
    fields: listBlocksFromText(block.text, 'fields').map(field => ({
      name: blockField(field, 'name') || 'field',
      access: blockField(field, 'access'),
      reset: blockField(field, 'reset'),
      description: blockField(field, 'description', 240),
    })),
  }));
};

const _stateNameFromBlock = (block) => {
  const first = String((block && block.text) || '').split(/\r?\n/)[0] || '';
  return blockField(block, 'name')
    || blockField(block, 'state')
    || stripYamlScalar(first.replace(/^\s*-\s*/, ''));
};

const _parseFsmTransition = (block) => {
  const first = String((block && block.text) || '').split(/\r?\n/)[0] || '';
  const scalar = stripYamlScalar(first.replace(/^\s*-\s*/, ''));
  let from = blockField(block, 'from');
  let to = blockField(block, 'to');
  let condition = blockField(block, 'condition', 280)
    || blockField(block, 'guard', 280)
    || blockField(block, 'when', 280)
    || blockField(block, 'on', 280);
  const action = blockField(block, 'action', 240) || blockField(block, 'output', 240);
  if ((!from || !to) && scalar) {
    const m = scalar.match(/^(.+?)\s*(?:->|=>|to)\s*(.+?)(?:\s+(?:when|if|on)\s+(.+))?$/i);
    if (m) {
      from = from || stripYamlScalar(m[1]);
      to = to || stripYamlScalar(m[2]);
      condition = condition || stripYamlScalar(m[3] || '');
    }
  }
  return { from, to, condition, action, raw: scalar };
};

const _fsmFromText = (name, text, sourceKey = '') => {
  const stateBlocks = listBlocksFromText(text, 'states');
  const transitionBlocks = listBlocksFromText(text, 'transitions');
  const states = stateBlocks.map(_stateNameFromBlock).filter(Boolean);
  const transitions = transitionBlocks.map(_parseFsmTransition).filter(t => (
    t.from || t.to || t.condition || t.raw
  ));
  return {
    name,
    sourceKey,
    states,
    transitions,
    resetState: fieldFromText(text, 'reset_state')
      || fieldFromText(text, 'initial_state')
      || fieldFromText(text, 'reset')
      || states[0]
      || '',
    illegalRecovery: fieldFromText(text, 'illegal_state_recovery', 360)
      || fieldFromText(text, 'default_recovery', 360)
      || fieldFromText(text, 'safe_state', 240),
    outputs: blockListValues({ text }, 'outputs', 8),
    actions: blockListValues({ text }, 'actions', 8),
    note: fieldFromText(text, 'note', 360) || fieldFromText(text, 'description', 360),
  };
};

const extractFsms = (section) => {
  if (!section) return [];
  const groups = mapGroupsFromSection(section)
    .filter(group => !/^(states|transitions|outputs|actions)$/i.test(group.key || ''));
  if (groups.length) {
    return groups
      .map(group => _fsmFromText(ssotTitleFor(group.key), group.text, section.key))
      .filter(machine => machine.states.length || machine.transitions.length || machine.note);
  }
  const direct = _fsmFromText(ssotTitleFor(section.key), section.text, section.key);
  if (direct.states.length || direct.transitions.length) return [direct];
  return [];
};

const sourceSectionsForDigestView = (view, sections) => {
  const source = sectionsForKeys(sections, view && view.keys);
  const addMatching = (rx) => {
    (sections || []).forEach(section => {
      if (rx.test(section.key || '') && !source.includes(section)) source.push(section);
    });
  };
  switch (view && view.id) {
    case 'interfaces':
      addMatching(/interface|businterfaces|interrupts?/i);
      break;
    case 'registers':
      addMatching(/register|memory_?map/i);
      break;
    case 'clocking':
      addMatching(/clock|reset|cdc|rdc/i);
      break;
    case 'function_model':
      addMatching(/function|fsm|state|logic|arbitration|ack|interrupt/i);
      break;
    case 'fsm':
      addMatching(/fsm|state|transition/i);
      break;
    case 'cycle_model':
      addMatching(/cycle|timing|latency|handshake|pipeline|scl/i);
      break;
    case 'dataflow':
      addMatching(/dataflow|flow|fifo|buffer|bit_control|start_stop|open_drain|access/i);
      break;
    case 'architecture':
      addMatching(/sub_?modules|decomposition|module|build/i);
      break;
    case 'feature_map':
      addMatching(/feature|fifo|fsm|arbitration|ack|interrupt|start_stop|open_drain|scl|bit_control|access/i);
      break;
    case 'review_gaps':
    case 'raw_yaml':
      return sections || [];
    default:
      break;
  }
  return source;
};

const digestViewsForSections = (sections) => {
  if (!(sections || []).length) return [];
  return SSOT_DIGEST_VIEWS.filter(view => (
    view.id === 'overview'
    || view.id === 'review_gaps'
    || view.id === 'raw_yaml'
    || sourceSectionsForDigestView(view, sections).length > 0
  ));
};

const ssotProgressStatusMap = () => {
  const data = window.ATLAS_PROGRESS || {};
  const selected = data.selected || (Array.isArray(data.modules) ? data.modules[0] : null) || {};
  const ssot = (((selected.progress || {}).ssot) || {});
  const rows = Array.isArray(ssot.sections) ? ssot.sections : [];
  return rows.reduce((acc, row) => {
    const key = row.key || row.id || row.section || row.name;
    if (key) acc[key] = row.status || row.state || row.approval || '';
    return acc;
  }, {});
};

const ssotSectionStatus = (section, statusByKey) => {
  const fromProgress = statusByKey[section.key];
  if (fromProgress) return String(fromProgress).toLowerCase();
  const body = section.text || '';
  if (/(approved|approval|status|state)\s*:\s*['"]?(approved|done|pass|ok|true)/i.test(body)) return 'approved';
  if (section.summary.gaps.length) return 'needs review';
  if (/(pending|blocked|draft|partial|todo|tbd)/i.test(body)) return 'pending';
  return 'review';
};

const ssotStatusColor = (status) => {
  const s = String(status || '').toLowerCase();
  if (['approved', 'done', 'pass', 'ok'].includes(s)) return 'var(--ok)';
  if (['fail', 'failed', 'error', 'rejected', 'blocked'].includes(s)) return 'var(--err)';
  if (['pending', 'needs review', 'draft', 'partial', 'todo'].includes(s)) return 'var(--warn)';
  return 'var(--fg-mute)';
};

const ssotReviewMarkdown = (section, status) => {
  const title = ssotTitleFor(section.key);
  const summary = section.summary || summarizeSsotSection(section);
  const focus = SSOT_REVIEW_FOCUS[section.key] || [
    'Review that this section is specific enough for downstream generation.',
    'Check for missing constraints, ambiguous wording, and stale assumptions.',
  ];
  const rows = [
    ['Status', status || 'review'],
    ['Source line', section.startLine],
    ['YAML lines', summary.lineCount],
    ['List items', summary.listItems],
    ['Nested groups', summary.groups.length ? summary.groups.join(', ') : '-'],
  ];

  const facts = summary.facts.length
    ? summary.facts.map(f => `| \`${mdCell(f.key)}\` | ${mdCell(f.value)} |`).join('\n')
    : '| - | No compact key facts detected. Review raw section below. |';
  const listItems = summary.listPreview.length
    ? summary.listPreview.map(x => `- ${x}`).join('\n')
    : '- No top-level list preview detected.';
  const gaps = summary.gaps.length
    ? summary.gaps.map(g => `- Line ${g.line}: ${g.text}`).join('\n')
    : '- No obvious TBD, null, pending, or placeholder text detected.';

  return [
    `### ${title}`,
    '',
    `\`${section.key}\``,
    '',
    '| Review item | Value |',
    '| --- | --- |',
    rows.map(([k, v]) => `| ${mdCell(k)} | ${mdCell(v)} |`).join('\n'),
    '',
    '#### Reviewer Focus',
    focus.map(x => `- ${x}`).join('\n'),
    '',
    '#### Key Facts',
    '| Field | Value |',
    '| --- | --- |',
    facts,
    '',
    '#### List Preview',
    listItems,
    '',
    '#### Review Flags',
    gaps,
  ].join('\n');
};

// Card-style fold for one Raw YAML section. Header shows the section
// title, a one-line summary derived from the YAML body (item count or
// key count), and a chevron. Body uses the existing tool-output-pre
// Prism YAML highlighter so colors match the rest of the chat feed.
const YamlSectionCard = ({ section, statusByKey }) => {
  const text = String(section?.text || '');
  const title = String(section?.title || section?.label || section?.key || section?.id || 'section');
  const status = (statusByKey && (statusByKey[section?.key] || statusByKey[section?.id])) || '';
  const lines = text.split('\n');
  // Skip the leading section header (`# === SECTION N ===`) and find the
  // actual top-level key (first non-comment, non-blank line) to compute
  // the summary string.
  let summary = '';
  let topKey = '';
  for (const ln of lines) {
    const trimmed = ln.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const m = trimmed.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (m) {
      topKey = m[1];
      const rhs = m[2];
      if (rhs && rhs !== '|' && rhs !== '>' && rhs !== 'null' && rhs !== '~') {
        summary = rhs.length > 80 ? rhs.slice(0, 80) + '…' : rhs;
      }
    }
    break;
  }
  // Item count: lines starting with '  -' under topKey, OR child key count.
  let countSuffix = '';
  if (!summary) {
    let items = 0, keys = 0;
    for (let i = 0; i < lines.length; i++) {
      const ln = lines[i];
      if (/^\s*-\s/.test(ln) && /^\s{2,}-/.test(ln)) items += 1;
      else if (/^\s{2,}[A-Za-z_][\w-]*:/.test(ln) && !/^\s{4,}/.test(ln)) keys += 1;
    }
    if (items) countSuffix = `${items} item${items === 1 ? '' : 's'}`;
    else if (keys) countSuffix = `${keys} key${keys === 1 ? '' : 's'}`;
    else countSuffix = `${lines.length} line${lines.length === 1 ? '' : 's'}`;
  }
  // Default open for short sections, closed for long ones (>40 lines).
  const [open, setOpen] = React.useState(lines.length <= 40);
  const statusColor = status === 'approved'
    ? 'var(--ok)'
    : (status === 'flag' || status === 'warn' ? 'var(--warn)' : 'var(--accent)');
  return (
    <div
      style={{
        border: '1px solid var(--line)',
        borderLeft: `3px solid ${statusColor}`,
        borderRadius: 4,
        background: 'color-mix(in oklch, var(--bg-1) 86%, transparent)',
        overflow: 'hidden',
      }}
    >
      <div
        role="button"
        tabIndex={0}
        onClick={() => setOpen(o => !o)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setOpen(o => !o); }
        }}
        title={open ? 'click to collapse' : 'click to expand'}
        style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '7px 12px',
          cursor: 'pointer', userSelect: 'none',
          fontFamily: 'var(--mono)', fontSize: 12,
          background: open ? 'color-mix(in oklch, var(--bg-3) 60%, transparent)' : 'transparent',
        }}
      >
        <span style={{ color: 'var(--cyan)', fontWeight: 700 }}>{title}</span>
        {topKey && topKey !== title && (
          <span className="mute" style={{ fontSize: 10 }}>{topKey}</span>
        )}
        <span style={{ flex: 1 }} />
        {summary ? (
          <span className="mute trunc" style={{
            fontSize: 11, color: 'var(--fg)', opacity: 0.78, maxWidth: '50%',
          }}>
            {summary}
          </span>
        ) : (
          <span className="mute" style={{ fontSize: 10 }}>{countSuffix}</span>
        )}
        <span style={{ color: 'var(--fg-mute)', fontSize: 11, fontFamily: 'var(--mono)' }}>
          {open ? '▾' : '▸'}
        </span>
      </div>
      {open ? (
        <pre
          className="tool-output-pre tool-output-yaml language-yaml"
          style={{
            margin: 0, border: 'none', borderTop: '1px solid var(--line)',
            borderRadius: 0,
            maxHeight: 480, overflow: 'auto',
            background: 'var(--code-bg)',
            padding: '10px 12px',
            whiteSpace: 'pre',
          }}
        >
          <code
            className="language-yaml"
            dangerouslySetInnerHTML={{ __html: _highlightYamlBlock(text) }}
          />
        </pre>
      ) : null}
    </div>
  );
};

const DigestCard = ({ title, meta, children }) => (
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

const DigestKV = ({ rows }) => (
  <div style={{ display: 'grid', gridTemplateColumns: '112px minmax(0, 1fr)', gap: '5px 10px', fontSize: 12 }}>
    {(rows || []).filter(r => r && r[1] !== '' && r[1] != null).map(([k, v]) => (
      <React.Fragment key={k}>
        <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>{k}</span>
        <span style={{ minWidth: 0, wordBreak: 'break-word' }}>{String(v)}</span>
      </React.Fragment>
    ))}
  </div>
);

const DigestList = ({ items, limit = 8 }) => {
  const rows = (items || []).filter(Boolean).slice(0, limit);
  if (!rows.length) return <DigestEmpty />;
  return (
    <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.45 }}>
      {rows.map((item, idx) => <li key={`${item}-${idx}`}>{item}</li>)}
    </ul>
  );
};

const GATE_STATUS_GLYPH = {
  pass: { glyph: '✓', color: 'var(--ok, #4caf50)' },
  fail: { glyph: '✗', color: 'var(--err, #e53935)' },
  blocked: { glyph: '⚠', color: 'var(--warn, #f9a825)' },
  unverified: { glyph: '○', color: 'var(--mute, #999)' },
  skip: { glyph: '–', color: 'var(--fg-mute, #888)' },
};

const GateRow = ({ item, isStage = false }) => {
  const sk = String(item.status || 'skip').toLowerCase();
  const g = GATE_STATUS_GLYPH[sk] || GATE_STATUS_GLYPH.skip;
  const label = isStage ? item.stage : item.label;
  const tools = isStage ? (item.scripts || []) : (item.helper ? [item.helper] : []);
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '24px minmax(140px, 1.2fr) minmax(0, 2fr) 1fr',
      gap: 10, alignItems: 'baseline',
      padding: '4px 0', borderBottom: '1px dashed var(--line)',
      fontSize: 12, fontFamily: 'var(--mono)',
    }}>
      <span style={{ color: g.color, fontWeight: 800, textAlign: 'center' }}>{g.glyph}</span>
      <span style={{ color: 'var(--fg)' }}>{label}</span>
      <span style={{ color: 'var(--fg-mute)' }}>{item.summary || ''}</span>
      <span className="mute" style={{ fontSize: 10, wordBreak: 'break-all' }}>
        {(item.evidence || []).slice(0, 2).join(' · ')}
        {tools.length ? <>{(item.evidence||[]).length ? <br/> : null}<span style={{opacity: 0.6}}>{tools[0]}</span></> : null}
      </span>
    </div>
  );
};

const GatesPanel = ({ ip }) => {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const fetchGates = React.useCallback(() => {
    if (!ip) return;
    setLoading(true);
    fetch(`/api/ssot-gates/${encodeURIComponent(ip)}`)
      .then(r => r.json())
      .then(j => { setData(j); setError(j.error || ''); })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [ip]);
  React.useEffect(() => { fetchGates(); }, [fetchGates]);
  if (!ip) return <DigestEmpty text="No IP selected" />;
  if (error) return <div style={{ padding: 12, color: 'var(--err)' }}>{error}</div>;
  if (!data && loading) return <div style={{ padding: 12, color: 'var(--fg-mute)' }}>loading gates…</div>;
  if (!data) return <DigestEmpty text="No gates data" />;
  const q = data.ssot_quality || { items: [], passed: 0, total: 0 };
  const s = data.stages || { items: [], passed: 0, total: 0 };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
        <span style={{ color: 'var(--accent)', fontWeight: 800, fontSize: 12 }}>
          Gates · {ip}
        </span>
        <span className="mute" style={{ fontSize: 10, fontFamily: 'var(--mono)' }}>
          SSOT {q.passed}/{q.total} ✓ · Stages {s.passed}/{s.total} ✓
        </span>
        <span className="mute" style={{ fontSize: 10, marginLeft: 'auto', fontFamily: 'var(--mono)' }}>
          {data.generated_at}
        </span>
        <button onClick={fetchGates} disabled={loading} style={{
          background: 'transparent', border: '1px solid var(--line)',
          color: 'var(--fg)', padding: '2px 10px', cursor: 'pointer',
          fontFamily: 'var(--mono)', fontSize: 11,
        }}>{loading ? '…' : 'refresh'}</button>
      </div>
      <DigestCard title={`SSOT Quality (${q.items.length} dims)`} meta={`${q.passed}/${q.total} pass`}>
        <div style={{ display: 'grid', gridTemplateColumns: '24px minmax(140px, 1.2fr) minmax(0, 2fr) 1fr',
          gap: 10, padding: '4px 0', borderBottom: '1px solid var(--line)',
          fontSize: 10, color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>
          <span></span><span>dimension</span><span>summary</span><span>evidence · checker</span>
        </div>
        {q.items.map(item => <GateRow key={item.id} item={item} />)}
      </DigestCard>
      <DigestCard title={`Per-stage Checkers (${s.items.length} stages)`} meta={`${s.passed}/${s.total} pass`}>
        <div style={{ display: 'grid', gridTemplateColumns: '24px minmax(140px, 1.2fr) minmax(0, 2fr) 1fr',
          gap: 10, padding: '4px 0', borderBottom: '1px solid var(--line)',
          fontSize: 10, color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>
          <span></span><span>stage</span><span>summary</span><span>evidence · scripts</span>
        </div>
        {s.items.map(item => <GateRow key={item.stage} item={item} isStage={true} />)}
      </DigestCard>
    </div>
  );
};

const compactDigestItems = (items, limit = 6) => {
  const rows = (items || []).filter(Boolean);
  if (!rows.length) return '';
  const shown = rows.slice(0, limit).join(', ');
  const extra = rows.length > limit ? ` +${rows.length - limit} more` : '';
  return shown + extra;
};

const DigestEmpty = ({ text = 'No structured data in this section yet.' }) => (
  <div className="mute" style={{ fontSize: 12, fontFamily: 'var(--mono)' }}>{text}</div>
);

const fsmDiagramId = (name, index = 0) => (
  `fsm-transition-${index}-${String(name || 'machine').toLowerCase().replace(/[^a-z0-9_-]+/g, '-')}`
);

const truncateSvgText = (value, limit = 24) => {
  const text = String(value || '').trim();
  return text.length > limit ? `${text.slice(0, Math.max(1, limit - 1))}...` : text;
};

const fsmStateKey = (value) => String(value || '').trim();

const fsmSafeId = (value, index = 0) => {
  const base = String(value || 'state')
    .trim()
    .replace(/[^a-zA-Z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 40) || 'state';
  return `S${index}_${/^[A-Za-z_]/.test(base) ? base : `_${base}`}`;
};

const fsmTransitionLabel = (tr, limit = 120) => {
  const condition = String((tr && tr.condition) || '').trim();
  const action = String((tr && tr.action) || '').trim();
  const raw = String((tr && tr.raw) || '').trim();
  const label = [condition, action].filter(Boolean).join(' / ') || raw;
  return limit ? truncateSvgText(label, limit) : label;
};

const escapeMermaidLabel = (value) => (
  String(value || '')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/[\r\n]+/g, ' ')
    .trim()
);

const uniqueFsmStates = (machine) => {
  const out = [];
  const add = (value) => {
    const state = String(value || '').trim();
    if (!state || state === '-') return;
    if (!out.includes(state)) out.push(state);
  };
  (machine.states || []).forEach(add);
  (machine.transitions || []).forEach((tr) => {
    add(tr.from);
    add(tr.to);
  });
  return out;
};

const fsmGraphFromMachine = (machine) => {
  const stateMap = new Map();
  const states = [];
  const addState = (value) => {
    const key = fsmStateKey(value);
    if (!key || key === '-') return null;
    if (stateMap.has(key)) return stateMap.get(key);
    const node = {
      id: fsmSafeId(key, states.length),
      label: key,
      reset: false,
    };
    stateMap.set(key, node);
    states.push(node);
    return node;
  };

  (machine.states || []).forEach(addState);
  (machine.transitions || []).forEach((tr) => {
    addState(tr.from);
    addState(tr.to);
  });
  const reset = addState(machine.resetState);
  if (reset) reset.reset = true;

  const transitions = (machine.transitions || []).map((tr, idx) => {
    const from = addState(tr.from);
    const to = addState(tr.to);
    const label = fsmTransitionLabel(tr, 96);
    const fullLabel = fsmTransitionLabel(tr, 0);
    return {
      id: `T${idx + 1}`,
      index: idx + 1,
      from,
      to,
      fromLabel: fsmStateKey(tr.from),
      toLabel: fsmStateKey(tr.to),
      condition: String((tr && tr.condition) || '').trim(),
      action: String((tr && tr.action) || '').trim(),
      raw: String((tr && tr.raw) || '').trim(),
      label,
      fullLabel,
      drawable: !!(from && to),
    };
  });

  return {
    name: machine.name || 'FSM',
    sourceKey: machine.sourceKey || '',
    reset,
    states,
    transitions,
    drawableTransitions: transitions.filter(t => t.drawable),
  };
};

const fsmGraphToMermaid = (graph) => {
  const lines = ['stateDiagram-v2', '  direction LR'];
  (graph.states || []).forEach((state) => {
    lines.push(`  state "${escapeMermaidLabel(state.label)}" as ${state.id}`);
  });
  if (graph.reset) lines.push(`  [*] --> ${graph.reset.id}`);
  (graph.drawableTransitions || []).forEach((tr) => {
    const label = tr.label ? `: ${escapeMermaidLabel(tr.label)}` : '';
    lines.push(`  ${tr.from.id} --> ${tr.to.id}${label}`);
  });
  if (!(graph.drawableTransitions || []).length && graph.states.length) {
    lines.push(`  [*] --> ${graph.states[0].id}`);
  }
  return lines.join('\n');
};

const ensureAtlasMermaid = () => {
  const mermaid = window.mermaid;
  if (!mermaid || !mermaid.render) return null;
  if (!window.__ATLAS_MERMAID_INITIALIZED) {
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
    window.__ATLAS_MERMAID_INITIALIZED = true;
  }
  return mermaid;
};

const FsmModeButton = ({ active, children, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    style={{
      border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
      borderRadius: 3,
      background: active ? 'color-mix(in oklch, var(--accent) 16%, var(--bg-2))' : 'var(--bg-2)',
      color: active ? 'var(--accent)' : 'var(--fg)',
      fontFamily: 'var(--mono)',
      fontSize: 10,
      padding: '4px 8px',
      cursor: 'pointer',
    }}
  >
    {children}
  </button>
);

const FsmLayeredSvgDiagram = ({ graph, diagramId }) => {
  const states = graph.states || [];
  const transitions = graph.drawableTransitions || [];
  if (!states.length || !transitions.length) {
    return <DigestEmpty text="No drawable FSM transitions yet. Add transition entries with from/to fields." />;
  }

  const adjacency = new Map();
  transitions.forEach((tr) => {
    const list = adjacency.get(tr.from.id) || [];
    list.push(tr.to.id);
    adjacency.set(tr.from.id, list);
  });

  const levelById = new Map();
  const start = (graph.reset || states[0]).id;
  const queue = [start];
  levelById.set(start, 0);
  while (queue.length) {
    const id = queue.shift();
    const level = levelById.get(id) || 0;
    (adjacency.get(id) || []).forEach((next) => {
      if (!levelById.has(next)) {
        levelById.set(next, level + 1);
        queue.push(next);
      }
    });
  }
  let maxLevel = Math.max(0, ...Array.from(levelById.values()));
  states.forEach((state) => {
    if (!levelById.has(state.id)) {
      maxLevel += 1;
      levelById.set(state.id, maxLevel);
    }
  });

  const levels = [];
  states.forEach((state) => {
    const level = levelById.get(state.id) || 0;
    if (!levels[level]) levels[level] = [];
    levels[level].push(state);
  });

  const nodeW = 152;
  const nodeH = 42;
  const pad = 42;
  const colGap = 92;
  const rowGap = 38;
  const maxRows = Math.max(1, ...levels.map(group => (group || []).length));
  const width = Math.max(460, pad * 2 + levels.length * nodeW + Math.max(0, levels.length - 1) * colGap);
  const height = Math.max(180, pad * 2 + maxRows * nodeH + Math.max(0, maxRows - 1) * rowGap);
  const pos = {};
  levels.forEach((group, level) => {
    const groupH = group.length * nodeH + Math.max(0, group.length - 1) * rowGap;
    const y0 = (height - groupH) / 2;
    group.forEach((state, row) => {
      pos[state.id] = {
        x: pad + level * (nodeW + colGap) + nodeW / 2,
        y: y0 + row * (nodeH + rowGap) + nodeH / 2,
      };
    });
  });

  const pairCounts = {};
  const markerId = `${diagramId}-fallback-arrow`;

  return (
    <div style={{ overflowX: 'auto' }}>
      <svg
        role="img"
        aria-label={`${graph.name} fallback FSM graph`}
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', minWidth: Math.min(width, 920), height: 'auto', display: 'block' }}
      >
        <defs>
          <marker id={markerId} markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L9,4 L0,8 Z" fill="var(--cyan)" />
          </marker>
        </defs>
        {graph.reset && pos[graph.reset.id] ? (
          <g>
            <line
              x1={Math.max(8, pos[graph.reset.id].x - nodeW / 2 - 34)}
              y1={pos[graph.reset.id].y}
              x2={pos[graph.reset.id].x - nodeW / 2 - 5}
              y2={pos[graph.reset.id].y}
              stroke="var(--accent)"
              strokeWidth="1.8"
              markerEnd={`url(#${markerId})`}
            />
            <text
              x={Math.max(10, pos[graph.reset.id].x - nodeW / 2 - 34)}
              y={pos[graph.reset.id].y - 8}
              fill="var(--accent)"
              fontFamily="var(--mono)"
              fontSize="10"
            >
              reset
            </text>
          </g>
        ) : null}
        {transitions.map((tr) => {
          const from = pos[tr.from.id];
          const to = pos[tr.to.id];
          if (!from || !to) return null;
          const pairKey = `${tr.from.id}->${tr.to.id}`;
          const pairIdx = pairCounts[pairKey] || 0;
          pairCounts[pairKey] = pairIdx + 1;
          const lane = (pairIdx % 4) * 10;
          const startX = from.x + nodeW / 2;
          const startY = from.y + Math.min(nodeH / 2 - 8, lane);
          const endX = to.x - nodeW / 2;
          const endY = to.y + Math.min(nodeH / 2 - 8, lane);
          let path = '';
          let labelX = (startX + endX) / 2;
          let labelY = (startY + endY) / 2;
          if (tr.from.id === tr.to.id) {
            const x = from.x + nodeW / 2 - 4;
            const y = from.y - nodeH / 2 + 4;
            path = `M ${x} ${y} C ${x + 46} ${y - 34}, ${x + 46} ${y + 34}, ${x} ${y + nodeH - 8}`;
            labelX = x + 34;
            labelY = y - 6;
          } else if ((levelById.get(tr.to.id) || 0) >= (levelById.get(tr.from.id) || 0)) {
            const bend = Math.max(60, Math.abs(endX - startX) * 0.45);
            path = `M ${startX} ${startY} C ${startX + bend} ${startY}, ${endX - bend} ${endY}, ${endX} ${endY}`;
          } else {
            const laneY = Math.min(height - 18, Math.max(startY, endY) + 34 + lane);
            path = `M ${from.x} ${from.y + nodeH / 2} L ${from.x} ${laneY} L ${to.x} ${laneY} L ${to.x} ${to.y + nodeH / 2}`;
            labelX = (from.x + to.x) / 2;
            labelY = laneY - 6;
          }
          return (
            <g key={`${graph.name}:fallback-edge:${tr.id}`}>
              <path
                d={path}
                fill="none"
                stroke="var(--cyan)"
                strokeWidth="1.35"
                markerEnd={`url(#${markerId})`}
              />
              <g>
                <rect
                  x={labelX - 10}
                  y={labelY - 13}
                  width="20"
                  height="16"
                  rx="3"
                  fill="var(--bg-2)"
                  stroke="var(--line-2)"
                />
                <text
                  x={labelX}
                  y={labelY - 1}
                  textAnchor="middle"
                  fill="var(--fg)"
                  fontFamily="var(--mono)"
                  fontSize="9"
                >
                  <title>{tr.fullLabel || tr.label || tr.id}</title>
                  {tr.index}
                </text>
              </g>
            </g>
          );
        })}
        {states.map((state) => {
          const p = pos[state.id];
          const isReset = !!state.reset;
          return (
            <g key={`${graph.name}:fallback-state:${state.id}`}>
              <rect
                x={p.x - nodeW / 2}
                y={p.y - nodeH / 2}
                width={nodeW}
                height={nodeH}
                rx="5"
                fill={isReset ? 'color-mix(in oklch, var(--accent) 16%, var(--bg-2))' : 'var(--bg-2)'}
                stroke={isReset ? 'var(--accent)' : 'var(--line-2)'}
                strokeWidth={isReset ? '1.7' : '1.2'}
              />
              <text
                x={p.x}
                y={p.y + 4}
                textAnchor="middle"
                fill={isReset ? 'var(--accent)' : 'var(--fg)'}
                fontFamily="var(--mono)"
                fontSize="11"
                fontWeight={isReset ? '700' : '500'}
              >
                <title>{state.label}</title>
                {truncateSvgText(state.label, 18)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

const MermaidFsmGraph = ({ graph, code, diagramId }) => {
  const [renderState, setRenderState] = React.useState({ status: 'loading', svg: '', error: '' });

  React.useEffect(() => {
    let cancelled = false;
    const mermaid = ensureAtlasMermaid();
    if (!mermaid) {
      setRenderState({ status: 'fallback', svg: '', error: 'Mermaid library is unavailable.' });
      return () => { cancelled = true; };
    }

    const renderId = `${diagramId}-${Date.now()}-${Math.random().toString(36).slice(2)}`.replace(/[^a-zA-Z0-9_-]/g, '-');
    setRenderState({ status: 'loading', svg: '', error: '' });
    Promise.resolve(mermaid.render(renderId, code))
      .then((result) => {
        if (cancelled) return;
        const rawSvg = (result && result.svg) || '';
        const svg = (window.DOMPurify && window.DOMPurify.sanitize)
          ? window.DOMPurify.sanitize(rawSvg, { USE_PROFILES: { svg: true, svgFilters: true } })
          : rawSvg;
        setRenderState({ status: 'ready', svg, error: '' });
      })
      .catch((err) => {
        if (cancelled) return;
        setRenderState({
          status: 'fallback',
          svg: '',
          error: err && err.message ? err.message : 'Mermaid render failed.',
        });
      });

    return () => { cancelled = true; };
  }, [code, diagramId]);

  if (renderState.status === 'ready' && renderState.svg) {
    return (
      <div
        className="atlas-mermaid-fsm"
        style={{ overflowX: 'auto', padding: 10 }}
        dangerouslySetInnerHTML={{ __html: renderState.svg }}
      />
    );
  }

  return (
    <div>
      {renderState.status === 'fallback' ? (
        <div
          className="mute"
          style={{
            margin: '8px 10px 0',
            padding: '6px 8px',
            border: '1px solid var(--line)',
            borderRadius: 3,
            color: 'var(--warn)',
            fontFamily: 'var(--mono)',
            fontSize: 10,
          }}
        >
          Mermaid fallback: {renderState.error}
        </div>
      ) : null}
      <FsmLayeredSvgDiagram graph={graph} diagramId={diagramId} />
    </div>
  );
};

const FsmTransitionTable = ({ graph }) => {
  const rows = graph.transitions || [];
  if (!rows.length) return <DigestEmpty text="No transitions listed for this FSM." />;
  return (
    <div style={{ display: 'grid', gap: 4 }}>
      <div
        className="mute"
        style={{
          display: 'grid',
          gridTemplateColumns: '36px minmax(90px, 0.65fr) 20px minmax(90px, 0.65fr) minmax(0, 1.5fr)',
          gap: 8,
          fontFamily: 'var(--mono)',
          fontSize: 10,
        }}
      >
        <span>#</span><span>from</span><span></span><span>to</span><span>condition/action</span>
      </div>
      {rows.map((tr, idx) => (
        <div
          key={`${graph.name}:tr:${idx}:${tr.raw}`}
          style={{
            display: 'grid',
            gridTemplateColumns: '36px minmax(90px, 0.65fr) 20px minmax(90px, 0.65fr) minmax(0, 1.5fr)',
            gap: 8,
            alignItems: 'baseline',
            fontFamily: 'var(--mono)',
            fontSize: 11,
            borderTop: idx ? '1px solid var(--line)' : 'none',
            paddingTop: idx ? 5 : 0,
          }}
        >
          <span className="mute">{tr.index}</span>
          <span style={{ color: tr.from ? 'var(--fg)' : 'var(--warn)' }}>{tr.fromLabel || '-'}</span>
          <span className="mute">-&gt;</span>
          <span style={{ color: tr.to ? 'var(--cyan)' : 'var(--warn)' }}>{tr.toLabel || '-'}</span>
          <span className="mute" style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
            {tr.fullLabel || '-'}
          </span>
        </div>
      ))}
    </div>
  );
};

const FsmTransitionDiagram = ({ machine, index = 0 }) => {
  const graph = fsmGraphFromMachine(machine);
  const [mode, setMode] = React.useState('graph');
  const mermaidCode = fsmGraphToMermaid(graph);
  const diagramId = fsmDiagramId(machine.name, index);

  if (!graph.states.length || !graph.transitions.length) {
    return <DigestEmpty text="No drawable FSM transitions yet. Add transition entries with from/to fields." />;
  }

  return (
    <div style={{ marginTop: 10, border: '1px solid var(--line)', borderRadius: 4, background: 'var(--bg)', overflow: 'hidden' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 8,
          padding: '7px 9px',
          borderBottom: '1px solid var(--line)',
          background: 'var(--bg-2)',
        }}
      >
        <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
          {graph.states.length} states / {graph.drawableTransitions.length} drawable transitions
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <FsmModeButton active={mode === 'graph'} onClick={() => setMode('graph')}>Graph</FsmModeButton>
          <FsmModeButton active={mode === 'mermaid'} onClick={() => setMode('mermaid')}>Mermaid</FsmModeButton>
          <FsmModeButton active={mode === 'table'} onClick={() => setMode('table')}>Table</FsmModeButton>
        </div>
      </div>
      {mode === 'graph' ? (
        <MermaidFsmGraph graph={graph} code={mermaidCode} diagramId={diagramId} />
      ) : null}
      {mode === 'mermaid' ? (
        <pre
          className="tool-output-pre language-mermaid"
          style={{
            margin: 0,
            border: 'none',
            borderRadius: 0,
            maxHeight: 360,
            overflow: 'auto',
            background: 'var(--code-bg)',
            padding: '10px 12px',
            whiteSpace: 'pre',
          }}
        >
          <code>{mermaidCode}</code>
        </pre>
      ) : null}
      {mode === 'table' ? (
        <div style={{ padding: 10 }}>
          <FsmTransitionTable graph={graph} />
        </div>
      ) : null}
    </div>
  );
};

// Feature-specific card with a stronger visual hierarchy than the
// generic DigestCard/DigestKV combo. Each row (datapath / control /
// output) gets its own glyph + accent color so a reviewer can scan a
// long feature list quickly. The trigger condition becomes a tinted
// chip under the name rather than a small gray meta.
const _FeatureRow = ({ glyph, label, value, color }) => {
  if (value === '' || value == null) return null;
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '18px 78px minmax(0, 1fr)',
      gap: '4px 10px', alignItems: 'baseline',
      fontSize: 12, lineHeight: 1.45,
    }}>
      <span aria-hidden="true" style={{
        color, fontFamily: 'var(--mono)', fontWeight: 700, textAlign: 'center',
      }}>{glyph}</span>
      <span style={{
        color, fontFamily: 'var(--mono)', fontSize: 10,
        textTransform: 'uppercase', letterSpacing: '0.08em',
      }}>{label}</span>
      <span style={{ minWidth: 0, wordBreak: 'break-word' }}>{String(value)}</span>
    </div>
  );
};

const FeatureCard = ({ index, feature }) => {
  const [hover, setHover] = React.useState(false);
  const hasAny = feature && (feature.datapath || feature.control || feature.output);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        border: '1px solid ' + (hover ? 'var(--accent)' : 'var(--line)'),
        borderRadius: 6,
        background: 'var(--bg-2)',
        padding: '12px 14px',
        minWidth: 0,
        display: 'flex', flexDirection: 'column', gap: 8,
        transition: 'border-color 120ms ease, transform 120ms ease',
        transform: hover ? 'translateY(-1px)' : 'translateY(0)',
      }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <span style={{
          fontFamily: 'var(--mono)', fontSize: 11,
          color: 'var(--fg-mute)', minWidth: 28,
        }}>F{index}.</span>
        <span style={{
          color: 'var(--accent)', fontWeight: 800, fontSize: 14,
          letterSpacing: '0.01em',
        }}>{feature.name || '(unnamed feature)'}</span>
        {feature.trigger ? (
          <span style={{
            fontSize: 10, fontFamily: 'var(--mono)',
            padding: '2px 8px', borderRadius: 999,
            background: 'color-mix(in oklch, var(--magenta) 14%, transparent)',
            color: 'var(--magenta)',
            border: '1px solid color-mix(in oklch, var(--magenta) 35%, transparent)',
          }}>trigger · {feature.trigger}</span>
        ) : null}
      </div>
      {hasAny ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingTop: 2 }}>
          <_FeatureRow glyph="➜" label="datapath" value={feature.datapath}
                       color="var(--accent)" />
          <_FeatureRow glyph="⊳" label="control"  value={feature.control}
                       color="var(--magenta)" />
          <_FeatureRow glyph="⊙" label="output"   value={feature.output}
                       color="var(--green, #22c55e)" />
        </div>
      ) : (
        <div className="mute" style={{ fontSize: 11, fontFamily: 'var(--mono)' }}>
          — no datapath / control / output captured yet —
        </div>
      )}
    </div>
  );
};

const ModuleTree = ({ topName, modules }) => (
  <div className="code" style={{
    margin: 0, padding: '10px 12px', fontSize: 12, lineHeight: 1.55,
    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
  }}>
    <div><span style={{ color: 'var(--magenta)', fontWeight: 800 }}>{topName || 'top'}</span></div>
    {(modules || []).map((m, idx) => {
      const last = idx === modules.length - 1;
      const branch = last ? '└─ ' : '├─ ';
      const pad = last ? '   ' : '│  ';
      const meta = m.file ? `  ${m.file}` : '';
      const desc = m.description ? `${pad}   ${trimSsotValue(m.description, 140)}` : '';
      return (
        <div key={m.name || idx}>
          <div>{branch}<span style={{ color: 'var(--cyan)', fontWeight: 700 }}>{m.name || 'module'}</span><span className="mute">{meta}</span></div>
          {desc ? <div className="mute">{desc}</div> : null}
        </div>
      );
    })}
  </div>
);

// Categorize an interface name + type into one of: clock | reset | bus
// | irq | data. Drives which side of the BlockDiagram frame the chip
// is rendered on, and which color it uses.
const _ifaceKind = (name, type) => {
  const t = `${name || ''} ${type || ''}`.toLowerCase();
  if (/(^|[^a-z])(clk|clock|cks)([^a-z]|$)/.test(t)) return 'clock';
  if (/(^|[^a-z])(rst|reset|aresetn)([^a-z]|$)/.test(t)) return 'reset';
  if (/(apb|axi|ahb|wishbone|tilelink|amba|bus|register|reg_if|reg-if)/.test(t)) return 'bus';
  if (/(irq|interrupt|nmi)/.test(t)) return 'irq';
  return 'data';
};

// Pin connector colors. Clock/reset use a green family (the "ground
// reference" convention from most SoC schematic tools); bus/data/irq
// share a deep navy so the user can tell signal-domain pins from
// timing-domain pins at a glance. Matches the soc-architect ModuleCard
// palette so the two views feel consistent.
// Format a port width hint into SystemVerilog range notation.
// • "" / "1" / 1 → ""        (single-bit, no range)
// • numeric "8"  → "[7:0]"     (concrete range)
// • symbolic "NUM_PINS" → "[NUM_PINS-1:0]" (parametric range)
// • already-shaped "NUM_PINS-1:0" or "[7:0]" → preserved
const _formatWidth = (w) => {
  if (w === undefined || w === null || w === '') return '';
  const s = String(w).trim();
  if (!s || s === '1') return '';
  if (s.startsWith('[') && s.endsWith(']')) return s;
  if (/[:]/.test(s)) return `[${s}]`;
  if (/^\d+$/.test(s)) {
    const n = parseInt(s, 10);
    if (n <= 1) return '';
    return `[${n - 1}:0]`;
  }
  return `[${s}-1:0]`;
};

const _ifaceColor = (kind) => ({
  clock: '#3a8f4f',
  reset: '#3a8f4f',
  bus:   '#1f3552',
  irq:   '#1f3552',
  data:  '#1f3552',
}[kind] || 'var(--fg-mute)');

// Pure HTML/CSS block diagram for the Architecture section.
// Hierarchical layout: the top module is rendered as the OUTER frame,
// and each submodule sits visually contained inside it as a child box.
// Major interfaces (clock, reset, bus, irq, data pads) are rendered as
// chips around the outer frame edges so the user sees the IP's
// "shape" (what plugs in where) at a glance. Each interface chip
// expands to show its full port list when clicked.
// Recursive submodule cell. When the module has `children`, it renders
// as a mini-frame containing nested cells (capped by `depthLimit` —
// any nesting deeper than the limit collapses into a "+N hidden" hint
// so the user can dial up the level via the BlockDiagram header).
const SubmoduleCell = ({ module: m, contractByModule, depth, depthLimit }) => {
  // Submodule pin/interface display — surfaces the per-module local
  // interfaces (apb_slave, gpio_pad, …) as small chips inside the cell
  // so the user can see what each submodule plugs into without leaving
  // the diagram. Contract data (richer: includes role/description)
  // wins over the raw sub_modules[].interfaces list.
  const localIfaces = (contractByModule[m.name]?.interfaces && contractByModule[m.name].interfaces.length
    ? contractByModule[m.name].interfaces
    : (Array.isArray(m.interfaces) ? m.interfaces : []));
  const wiringOnly = !!m.wiring_only;
  const blockColor = wiringOnly ? 'var(--magenta)' : 'var(--cyan)';
  // Per-cell expand state — clicking a chip toggles its drawer
  // independent of the top-level pin-row state.
  const [openLocal, setOpenLocal] = React.useState(() => new Set());
  const toggleLocal = (id) => setOpenLocal(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });
  const childList = Array.isArray(m.children) ? m.children : [];
  const showChildren = childList.length > 0 && depth < depthLimit;
  const hiddenChildren = childList.length > 0 && depth >= depthLimit ? childList.length : 0;
  const orderedChildren = [...childList].sort((a, b) => Number(!!a.wiring_only) - Number(!!b.wiring_only));
  return (
    <div
      style={{
        border: `${wiringOnly ? '1.5px dashed' : '1.5px solid'} ${blockColor}`,
        background: 'var(--bg-1)',
        borderRadius: 5,
        padding: '7px 10px 8px',
        minWidth: 0,
      }}
    >
      <div
        title={m.name}
        style={{
          color: blockColor, fontWeight: 700, fontSize: 12,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}
      >
        {m.name}
      </div>
      {m.file ? (
        <div
          className="mute"
          title={m.file}
          style={{
            fontSize: 9, marginTop: 2,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}
        >
          {m.file}
        </div>
      ) : null}
      {localIfaces.length ? (
        <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 3 }}>
          {localIfaces.map((iface, ifIdx) => {
            const kind = _ifaceKind(iface.name, iface.type);
            const color = _ifaceColor(kind);
            const id = `${m.name}:${iface.name || ifIdx}`;
            const isOpen = openLocal.has(id);
            const allPorts = Array.isArray(iface.ports) && iface.ports.length
              ? iface.ports
              : [
                  ...(Array.isArray(iface.inputs) ? iface.inputs : []).map(n =>
                    typeof n === 'string' ? { name: n, dir: 'input' } : ({ ...n, dir: n.dir || 'input' })
                  ),
                  ...(Array.isArray(iface.outputs) ? iface.outputs : []).map(n =>
                    typeof n === 'string' ? { name: n, dir: 'output' } : ({ ...n, dir: n.dir || 'output' })
                  ),
                ];
            return (
              <div key={id}>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => { e.stopPropagation(); toggleLocal(id); }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      e.stopPropagation();
                      toggleLocal(id);
                    }
                  }}
                  title={iface.description || iface.role || iface.type || iface.name}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 5,
                    padding: '1px 6px',
                    border: `1px solid ${color}`,
                    background: `color-mix(in oklch, ${color} 6%, transparent)`,
                    borderRadius: 10,
                    fontSize: 9,
                    cursor: 'pointer', userSelect: 'none',
                    fontFamily: 'var(--mono)',
                  }}
                >
                  <span style={{
                    width: 6, height: 6, borderRadius: '50%', background: color,
                  }} />
                  <span style={{ color: 'var(--fg)', fontWeight: 600 }}>{iface.name || iface.type}</span>
                  {allPorts.length ? (
                    <span style={{ color: 'var(--fg-mute)' }}>{allPorts.length}</span>
                  ) : null}
                  <span style={{ color: 'var(--fg-mute)' }}>{isOpen ? '▾' : '▸'}</span>
                </span>
                {isOpen && allPorts.length ? (
                  <div style={{
                    marginTop: 3,
                    border: `1px solid ${color}`,
                    borderRadius: 3,
                    background: 'var(--bg-1)',
                    padding: '4px 6px',
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1fr) auto auto',
                    gap: '1px 8px',
                    fontSize: 9,
                  }}>
                    {allPorts.slice(0, 12).map((p, i) => (
                      <React.Fragment key={p.name || i}>
                        <span style={{ color: 'var(--fg)', fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
                        <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{p.dir || p.direction || ''}</span>
                        <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{_formatWidth(p.width)}</span>
                      </React.Fragment>
                    ))}
                    {allPorts.length > 12 ? (
                      <span style={{ gridColumn: '1 / -1', color: 'var(--fg-mute)', fontSize: 8 }}>
                        +{allPorts.length - 12} more
                      </span>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}
      {wiringOnly ? (
        <div
          style={{
            marginTop: 4,
            fontSize: 9, color: 'var(--fg-mute)',
            textTransform: 'uppercase', letterSpacing: '0.06em',
          }}
        >
          wiring only
        </div>
      ) : null}
      {showChildren ? (
        <div style={{
          marginTop: 6,
          padding: '6px',
          border: `1px dashed color-mix(in oklch, ${blockColor} 40%, var(--line))`,
          borderRadius: 4,
          background: `color-mix(in oklch, ${blockColor} 3%, transparent)`,
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: 6,
        }}>
          {orderedChildren.map(child => (
            <SubmoduleCell
              key={child.name}
              module={child}
              contractByModule={contractByModule}
              depth={depth + 1}
              depthLimit={depthLimit}
            />
          ))}
        </div>
      ) : null}
      {hiddenChildren ? (
        <div className="mute" style={{
          marginTop: 4, fontSize: 9, color: 'var(--fg-mute)',
          fontStyle: 'italic',
        }}>
          ↳ +{hiddenChildren} nested submodule{hiddenChildren === 1 ? '' : 's'} (raise depth to view)
        </div>
      ) : null}
    </div>
  );
};

// Walk a module tree to find the deepest level present so the depth
// selector can offer just-enough options (no "5" button when the data
// only goes 2 deep).
const _maxNestingDepth = (modules) => {
  if (!Array.isArray(modules) || !modules.length) return 1;
  let best = 1;
  for (const m of modules) {
    const childDepth = m && Array.isArray(m.children) && m.children.length
      ? 1 + _maxNestingDepth(m.children)
      : 1;
    if (childDepth > best) best = childDepth;
  }
  return best;
};

const BlockDiagram = ({ topName, modules, contractByModule = {}, interfaces = [], clockSection, parameters = [] }) => {
  const list = Array.isArray(modules) ? modules : [];
  if (!list.length) return null;
  // Multi-open: clicking a pin row toggles ITS drawer without closing
  // the others. The user wants to compare port lists side-by-side, so
  // restricting to one open drawer at a time would force back-and-forth
  // re-expansion. Persisted only for the lifetime of the component.
  const [openIfaces, setOpenIfaces] = React.useState(() => new Set());
  const toggleIface = (id) => setOpenIfaces(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });
  const [showAllSignals, setShowAllSignals] = React.useState(false);
  const [showParams, setShowParams] = React.useState(true);
  const maxDepth = _maxNestingDepth(list);
  // Default to 1 level so the diagram stays clean even when the SSOT
  // declares a deep hierarchy. User can raise to 2 / 3 / all from the
  // header. When SSOT has no nesting at all, the selector is hidden.
  const [depthLimit, setDepthLimit] = React.useState(1);
  const paramRows = Array.isArray(parameters) ? parameters.filter(p => p && p.name) : [];
  // Wiring-only wrappers (e.g. <ip>_wrapper) get pushed to the right so
  // the implementation submodules read first; rendering order doesn't
  // imply hardware ordering, just visual grouping.
  const ordered = [...list].sort((a, b) => Number(!!a.wiring_only) - Number(!!b.wiring_only));
  const accent = 'var(--accent)';
  // Bucket interfaces by kind so the chips can sit on the appropriate
  // edge of the frame (clock/reset → left, bus → right, irq → right,
  // data pads → bottom).
  const buckets = { clock: [], reset: [], bus: [], irq: [], data: [] };
  (interfaces || []).forEach(iface => {
    const kind = _ifaceKind(iface.name, iface.type);
    (buckets[kind] || buckets.data).push({ ...iface, kind });
  });
  // Synthesize default clock/reset chips from the clock_reset_domains
  // section if no explicit interface entries exist for them.
  if (!buckets.clock.length && clockSection) {
    const freq = sectionFact && sectionFact(clockSection, 'frequency_hz');
    buckets.clock.push({ name: 'clk', type: 'clock', kind: 'clock', description: freq ? `${freq} Hz` : '', ports: [] });
  }
  if (!buckets.reset.length && clockSection) {
    buckets.reset.push({ name: 'rst_n', type: 'reset', kind: 'reset', description: 'async reset', ports: [] });
  }

  // External pin row — used by the new left-column layout. Renders
  // `<name · type role>  ─── ●`, with the colored line + dot
  // visually "plugging into" the right-hand top-module frame.
  // Clicking the row toggles a port detail drawer underneath.
  const renderPinRow = (iface, idx) => {
    const color = _ifaceColor(iface.kind);
    const id = `${iface.kind}:${iface.name || idx}`;
    const isOpen = openIfaces.has(id);
    const ports = Array.isArray(iface.ports) ? iface.ports
                : Array.isArray(iface.inputs) || Array.isArray(iface.outputs)
                  ? [...(iface.inputs || []).map(n => ({ name: n, dir: 'in' })),
                     ...(iface.outputs || []).map(n => ({ name: n, dir: 'out' }))]
                  : [];
    const visible = showAllSignals ? ports : ports.slice(0, 8);
    // "APB4 S" / "CLK S" / "custom S" — short type tag + role abbrev.
    const typeStr = (iface.type || '').trim() || iface.kind || 'custom';
    const role = (iface.role || '').toLowerCase().startsWith('mast') ? 'M' : 'S';
    return (
      <div key={id} style={{ display: 'flex', flexDirection: 'column' }}>
        <div
          role="button"
          tabIndex={0}
          onClick={() => toggleIface(id)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleIface(id);
            }
          }}
          title={iface.description || iface.role || iface.type || iface.name}
          style={{
            display: 'flex', alignItems: 'center', gap: 0,
            cursor: 'pointer', userSelect: 'none',
            padding: '2px 0',
          }}
        >
          <span style={{
            flex: 1, textAlign: 'right',
            paddingRight: 6,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            fontSize: 11,
          }}>
            <span style={{ color: 'var(--fg)', fontWeight: 600 }}>{iface.name || iface.type}</span>
            <span style={{ color: 'var(--fg-mute)' }}> · {typeStr} {role}</span>
          </span>
          <span style={{ width: 22, height: 1.5, background: color, flexShrink: 0 }} />
          <span style={{
            width: 9, height: 9, borderRadius: '50%',
            background: color,
            flexShrink: 0,
            border: `1px solid ${color}`,
          }} />
          {ports.length ? (
            <span style={{
              marginLeft: 4, fontSize: 9,
              color: 'var(--fg-mute)',
            }}>
              {isOpen ? '▾' : '▸'}
            </span>
          ) : null}
        </div>
        {isOpen && ports.length ? (
          <div style={{
            margin: '4px 0 4px 8px',
            border: `1px solid ${color}`,
            borderRadius: 3,
            background: 'var(--bg-1)',
            padding: '5px 8px',
            display: 'grid',
            gridTemplateColumns: 'auto auto auto',
            gap: '2px 12px',
            fontSize: 10,
            alignItems: 'baseline',
            whiteSpace: 'nowrap',
          }}>
            {visible.map((p, i) => (
              <React.Fragment key={p.name || i}>
                <span style={{ color: 'var(--fg)', fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
                <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{p.dir || p.direction || ''}</span>
                <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{_formatWidth(p.width)}</span>
              </React.Fragment>
            ))}
            {!showAllSignals && ports.length > 8 ? (
              <span style={{ gridColumn: '1 / -1', color: 'var(--fg-mute)', fontSize: 9 }}>
                +{ports.length - 8} more · click "show all" above
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  };

  // Legacy chip renderer — retained for any caller that still wants
  // the in-frame chip style. Kept inert until/unless wired back in.
  // eslint-disable-next-line no-unused-vars
  const renderIfaceChip = (iface, idx) => {
    const color = _ifaceColor(iface.kind);
    const id = `${iface.kind}:${iface.name || idx}`;
    const isOpen = openIfaces.has(id);
    const ports = Array.isArray(iface.ports) ? iface.ports : [];
    const visible = showAllSignals ? ports : ports.slice(0, 8);
    return (
      <div
        key={id}
        style={{
          display: 'flex', flexDirection: 'column', alignItems: 'stretch', minWidth: 0,
        }}
      >
        <div
          role="button"
          tabIndex={0}
          onClick={() => toggleIface(id)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleIface(id);
            }
          }}
          title={iface.description || iface.role || iface.type || iface.name}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '3px 8px',
            border: `1px solid ${color}`,
            background: `color-mix(in oklch, ${color} 8%, var(--bg-1))`,
            borderRadius: 4,
            color, fontSize: 10, fontWeight: 700,
            cursor: 'pointer', userSelect: 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <span style={{
            fontSize: 8, padding: '0 4px', borderRadius: 2,
            border: `1px solid ${color}`, opacity: 0.8,
            textTransform: 'uppercase',
          }}>{iface.kind}</span>
          <span style={{
            overflow: 'hidden', textOverflow: 'ellipsis',
            whiteSpace: 'nowrap', minWidth: 0,
            color: 'var(--fg)',
            fontWeight: 700,
          }}>{iface.name || iface.type}</span>
          {ports.length ? (
            <span style={{ color: 'var(--fg-mute)', fontWeight: 400, fontSize: 9 }}>
              {ports.length}
            </span>
          ) : null}
          <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}>{isOpen ? '▾' : '▸'}</span>
        </div>
        {isOpen && ports.length ? (
          <div style={{
            marginTop: 4,
            border: `1px solid ${color}`,
            borderRadius: 3,
            background: 'var(--bg-1)',
            padding: '5px 8px',
            display: 'grid',
            gridTemplateColumns: 'auto 1fr auto',
            gap: '2px 8px',
            fontSize: 10,
          }}>
            {visible.map((p, i) => (
              <React.Fragment key={p.name || i}>
                <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{p.dir || p.direction || ''}</span>
                <span style={{ color: 'var(--fg)', fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
                <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>{p.width ? `[${p.width}]` : ''}</span>
              </React.Fragment>
            ))}
            {!showAllSignals && ports.length > 8 ? (
              <span style={{ gridColumn: '1 / -1', color: 'var(--fg-mute)', fontSize: 9 }}>
                +{ports.length - 8} more · click "show all" above
              </span>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div style={{
      padding: '14px 12px 18px',
      fontFamily: 'var(--mono)',
      fontSize: 11,
    }}>
      {/* Detail toggle + depth selector. The depth chip group only
          appears when the SSOT declares any nesting (maxDepth > 1) —
          otherwise the buttons would be no-ops and just clutter the
          header. */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        {maxDepth > 1 ? (
          <>
            <span className="mute" style={{ fontSize: 10 }}>depth</span>
            {[1, 2, 3].filter(d => d <= maxDepth).map(d => (
              <button
                key={d}
                type="button"
                className="mini-btn"
                onClick={() => setDepthLimit(d)}
                title={`show ${d} level${d === 1 ? '' : 's'} of submodules`}
                style={depthLimit === d ? {
                  borderColor: 'var(--accent)',
                  color: 'var(--accent)',
                } : undefined}
              >
                {d}
              </button>
            ))}
            {maxDepth > 3 ? (
              <button
                type="button"
                className="mini-btn"
                onClick={() => setDepthLimit(maxDepth)}
                title="show every nested submodule level"
                style={depthLimit >= maxDepth ? {
                  borderColor: 'var(--accent)',
                  color: 'var(--accent)',
                } : undefined}
              >
                all
              </button>
            ) : null}
          </>
        ) : null}
        <span style={{ flex: 1 }} />
        {paramRows.length ? (
          <button
            type="button"
            className="mini-btn"
            onClick={() => setShowParams(v => !v)}
            title={`toggle parameter chips (${paramRows.length})`}
            style={showParams ? {
              borderColor: 'var(--accent)',
              color: 'var(--accent)',
            } : undefined}
          >
            {showParams ? '▾ params' : '▸ params'}
          </button>
        ) : null}
        <button
          type="button"
          className="mini-btn"
          onClick={() => setShowAllSignals(v => !v)}
          title="toggle full port list on every interface"
        >
          {showAllSignals ? '▾ collapse all' : '▸ show all'}
        </button>
      </div>

      {/* Two-column layout: external pin labels (left) connect to the
          framed top module (right) via a short colored line + dot,
          mirroring the soc-architect block-card visual. Pin order:
          bus → data → irq grouped at top, clock → reset grouped at
          bottom (clock/reset are the conventional "ground reference"
          on most block diagrams).
          Left column is `auto`-sized so an expanded port drawer can
          push the column wider than the resting pin labels — without
          this, long widths like `[APB_ADDR_WIDTH-1:0]` got clipped
          inside the 220px cap. */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'auto 1fr',
        gap: 0,
        alignItems: 'stretch',
      }}>
        {/* LEFT — pin column. Each row: label · type role  ─── ● */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '36px 0 18px',
          gap: 4,
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {[...buckets.bus, ...buckets.data, ...buckets.irq].map((iface, i) =>
              renderPinRow(iface, `top${i}`)
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 8 }}>
            {[...buckets.clock, ...buckets.reset].map((iface, i) =>
              renderPinRow(iface, `bot${i}`)
            )}
          </div>
        </div>

        {/* RIGHT — framed top module. Title + category badges on the
            top edge, parameters + submodules inside. */}
        <div style={{
          position: 'relative',
          border: `2px solid ${accent}`,
          borderRadius: 8,
          background: 'color-mix(in oklch, var(--accent) 5%, var(--bg-2))',
          padding: '28px 16px 16px',
          marginLeft: -1,
        }}>
          {/* Top header strip — diamond + module name on the left,
              category badge on the right. Sits FULLY inside the frame
              so the outer border doesn't draw a strikethrough across
              the badge text. */}
          <div style={{
            position: 'absolute',
            top: 8,
            left: 14,
            right: 14,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 8,
            pointerEvents: 'none',
          }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              fontWeight: 700,
              color: 'var(--accent)',
              letterSpacing: '0.04em',
            }}>
              <span style={{ fontSize: 13, lineHeight: 1, color: accent }}>◇</span>
              <span>{topName || 'top'}</span>
            </div>
            <span style={{
              padding: '1px 8px',
              background: 'transparent',
              border: `1px solid color-mix(in oklch, ${accent} 50%, var(--line))`,
              borderRadius: 3,
              fontSize: 9,
              fontWeight: 700,
              color: 'var(--fg-mute)',
              letterSpacing: '0.08em',
              lineHeight: 1.4,
              whiteSpace: 'nowrap',
            }}>
              {(() => {
                const allChips = [...(buckets.bus || []), ...(buckets.irq || []), ...(buckets.data || [])];
                const text = allChips.map(c => `${c.name || ''} ${c.type || ''}`).join(' ').toLowerCase();
                if (/(apb|axi|ahb|wishbone|amba)/.test(text)) return 'PERIPH';
                if (/(cpu|core|fetch|decode|exec)/.test(text)) return 'CORE';
                if (/(dma|dmac)/.test(text)) return 'DMA';
                if (/(mem|cache|sram|dram)/.test(text)) return 'MEM';
                return 'TOP';
              })()}
            </span>
          </div>

          {/* Parameter chips (KEY=value) inside the frame, above
              submodules. Hidden when paramRows empty or user toggled
              off via the header `params` button. */}
          {showParams && paramRows.length ? (
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 6,
              marginBottom: 14,
            }}>
              {paramRows.map(p => (
                <span
                  key={p.name}
                  title={p.description || `${p.name}=${p.value}`}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'baseline',
                    gap: 0,
                    padding: '3px 10px',
                    background: 'var(--bg-1)',
                    border: '1px solid var(--line)',
                    borderRadius: 14,
                    fontSize: 10,
                    color: 'var(--fg-mute)',
                    fontFamily: 'var(--mono)',
                  }}
                >
                  <span>{p.name}</span>
                  {p.value ? (
                    <>
                      <span style={{ color: 'var(--fg-mute)' }}>=</span>
                      <span style={{ color: 'var(--fg)', fontWeight: 700 }}>{p.value}</span>
                    </>
                  ) : null}
                </span>
              ))}
            </div>
          ) : null}

          {/* Inner grid of submodule blocks. */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
            gap: 10,
          }}>
            {ordered.map(m => (
              <SubmoduleCell
                key={m.name}
                module={m}
                contractByModule={contractByModule}
                depth={1}
                depthLimit={depthLimit}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const DigestSourceSections = ({ view, sections, statusByKey, t }) => {
  const source = sourceSectionsForDigestView(view, sections);
  if (!source.length) return null;
  return (
    <details style={{
      marginTop: 12, border: '1px solid var(--line)', borderRadius: 4,
      background: 'var(--bg-2)',
    }}>
      <summary style={{
        cursor: 'pointer', padding: '8px 12px',
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11,
      }}>{t.sourceSections}</summary>
      <div style={{ borderTop: '1px solid var(--line)', padding: '10px 12px', display: 'grid', gap: 10 }}>
        {source.map(section => {
          const status = ssotSectionStatus(section, statusByKey);
          return (
            <div key={section.key} style={{ borderLeft: `2px solid ${ssotStatusColor(status)}`, paddingLeft: 10 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', marginBottom: 4 }}>
                <span style={{ color: 'var(--fg)', fontWeight: 700 }}>{ssotTitleFor(section.key)}</span>
                <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>{section.key} · line {section.startLine}</span>
              </div>
              <div className="md-agent"
                dangerouslySetInnerHTML={{ __html: _markdownHtml(ssotReviewMarkdown(section, status)) }} />
            </div>
          );
        })}
      </div>
    </details>
  );
};

const SsotDigestContent = ({ view, sections, statusByKey, uiLang = 'ko', content = '', selected = '' }) => {
  const t = uiLang === 'en'
    ? { sourceSections: 'Source section review', ports: 'ports', fields: 'fields' }
    : { sourceSections: '원본 섹션 리뷰', ports: 'ports', fields: 'fields' };
  const top = sectionByKey(sections, 'top_module');
  const io = sectionByKey(sections, 'io_list');
  const featuresSection = sectionByKey(sections, 'features');
  const submodsSection = sectionByKey(sections, 'sub_modules');
  const decompSection = sectionByKey(sections, 'decomposition');
  const functionSection = sectionByKey(sections, 'function_model');
  const cycleSection = sectionByKey(sections, 'cycle_model');
  const timingSection = sectionByKey(sections, 'timing');
  const registersSection = sectionByKey(sections, 'registers')
    || sectionByKey(sections, 'memoryMap')
    || sectionByKey(sections, 'memory_map')
    || (sections || []).find(s => /register|memory_?map/i.test(s.key || ''));
  const dataflowSection = sectionByKey(sections, 'dataflow');
  const clockSection = sectionByKey(sections, 'clock_reset_domains')
    || sectionByKey(sections, 'clock_reset')
    || sectionByKey(sections, 'clocks');
  const cdcSection = sectionByKey(sections, 'cdc_requirements');
  const rdcSection = sectionByKey(sections, 'rdc_requirements');
  const memorySection = sectionByKey(sections, 'memory');
  const interruptsSection = sectionByKey(sections, 'interrupts');
  const fsmSection = sectionByKey(sections, 'fsm');
  const errorsSection = sectionByKey(sections, 'errors') || sectionByKey(sections, 'error_handling');
  const parametersSection = sectionByKey(sections, 'parameters')
    || sectionByKey(sections, 'top_module_parameters')
    || sectionByKey(sections, 'module_parameters')
    || sectionByKey(sections, 'parameter_list')
    || sectionByKey(sections, 'default_parameters')
    || (sections || []).find(s => /parameter/i.test(s.key || ''));
  // Extract `parameters` blocks → [{name, default, description}]. SSOT
  // shapes seen in the wild:
  //   • parameters: ─ list of {name, default, description, …}
  //   • top_module: ─ {parameters: [...]}
  //   • parameters: as a flat key=value mapping at section root
  //   • module_parameters / parameter_list / default_parameters
  //   • freeform "NUM_PINS = 32" lines inside a parameters paragraph
  // We try them in order and stop at the first hit so an IP that uses
  // any of these shapes ends up with parameter chips on the diagram.
  const parameters = (() => {
    const collect = (blocks) => blocks.map(b => ({
      name: blockField(b, 'name') || blockField(b, 'key') || blockField(b, 'param') || '',
      value: blockField(b, 'default') || blockField(b, 'value') || blockField(b, 'default_value') || blockField(b, 'val') || '',
      description: blockField(b, 'description', 200),
    })).filter(p => p.name);
    // 1) blocks under the standalone `parameters` section
    let rows = collect(listBlocksFromSection(parametersSection));
    // 2) blocks nested under top_module.parameters
    if (!rows.length) rows = collect(listBlocksFromSection(top, 'parameters'));
    // 3) blocks under `top_module.params` (alternative key)
    if (!rows.length) rows = collect(listBlocksFromSection(top, 'params'));
    // 4) flat KEY: VALUE pairs inside the parameters section text — last
    //    ditch effort for IPs that flatten the parameter list instead of
    //    wrapping each entry in its own `- name: …` block. Only catches
    //    SystemVerilog-style identifiers (UPPER_SNAKE_CASE) so we don't
    //    misread random doc paragraphs as parameters.
    if (!rows.length && parametersSection && parametersSection.text) {
      const seen = new Set();
      const flat = [];
      const re = /^[\s-]*([A-Z_][A-Z0-9_]{2,})\s*[:=]\s*([^\n#]+?)\s*$/gm;
      let m;
      while ((m = re.exec(parametersSection.text)) !== null) {
        const name = m[1];
        if (seen.has(name)) continue;
        seen.add(name);
        flat.push({ name, value: m[2].trim().replace(/^["']|["']$/g, ''), description: '' });
      }
      rows = flat;
    }
    return rows;
  })();

  const interfaces = extractReviewInterfaces(sections, io);
  const parsedFeatures = extractFeatures(featuresSection);
  const featureSections = (sections || []).filter(section => (
    section !== featuresSection
    && /feature|fifo|fsm|generation|arbitration|ack|interrupt|open_drain|access|bit_control|start_stop/i.test(section.key || '')
  ));
  const features = parsedFeatures.length ? parsedFeatures : featureSections.slice(0, 12).map(section => ({
    name: ssotTitleFor(section.key),
    trigger: sectionFact(section, 'trigger') || sectionFact(section, 'condition') || sectionFact(section, 'source'),
    datapath: sectionFact(section, 'datapath') || sectionFact(section, 'description') || sectionFact(section, 'implementation') || sectionFact(section, 'logic'),
    control: sectionFact(section, 'control') || sectionFact(section, 'response') || sectionFact(section, 'timing'),
    output: sectionFact(section, 'output') || sectionFact(section, 'result') || sectionFact(section, 'description'),
    sourceKey: section.key,
  }));
  const rawSubmods = extractSubmodules(submodsSection);
  const moduleContracts = extractModuleContracts(decompSection);
  const submods = rawSubmods.length ? rawSubmods : moduleContracts.map(contract => ({
    name: contract.module,
    file: '',
    description: contract.implementation,
    implements: contract.owns,
    sourceSections: [],
    interfaces: contract.interfaces,
  }));
  const contractByModule = moduleContracts.reduce((acc, contract) => {
    if (contract.module) acc[contract.module] = contract;
    return acc;
  }, {});
  const registers = extractRegisters(registersSection);
  const clockDomains = listBlocksFromSection(clockSection, 'domains').map(block => ({
    name: blockField(block, 'name'),
    frequency: blockField(block, 'frequency_mhz'),
    description: blockField(block, 'description', 260),
  }));
  const resets = listBlocksFromSection(io, 'resets').map(block => ({
    name: blockField(block, 'name'),
    polarity: blockField(block, 'polarity'),
    type: blockField(block, 'sync_async') || blockField(block, 'type'),
    description: blockField(block, 'description', 220),
  }));
  const cdcCrossings = listBlocksFromSection(cdcSection, 'crossings').map(block => ({
    name: blockField(block, 'name'),
    from: blockField(block, 'source_domain'),
    to: blockField(block, 'dest_domain'),
    synchronizer: blockField(block, 'synchronizer'),
    description: blockField(block, 'description', 260),
  }));
  const fsmMachines = extractFsms(fsmSection);
  const dataflowGroups = mapGroupsFromSection(dataflowSection).filter(g => g.key !== 'locked_decisions');
  const transactions = listBlocksFromSection(functionSection, 'transactions');
  const stateVars = listBlocksFromSection(functionSection, 'state_variables');
  const latencyGroups = mapGroupsFromSection(cycleSection, 'latency');
  const handshakeRules = listBlocksFromSection(cycleSection, 'handshake_rules');
  const pipeline = listBlocksFromSection(cycleSection, 'pipeline');
  const topName = sectionFact(top, 'name') || sectionFact(top, 'module') || (top && top.value) || 'SSOT';

  const header = (
    <div style={{ marginBottom: 12 }}>
      <div style={{ color: 'var(--magenta)', fontWeight: 900, fontSize: 18, letterSpacing: 0 }}>
        {topName}
      </div>
      <div style={{ color: 'var(--fg)', lineHeight: 1.45, marginTop: 4, maxWidth: 920 }}>
        {sectionFact(top, 'description', 'No top_module.description available yet.')}
      </div>
    </div>
  );

  const featureTokens = (feature) => String([
    feature && feature.name,
    feature && feature.sourceKey,
    feature && feature.trigger,
    feature && feature.datapath,
  ].filter(Boolean).join(' '))
    .toLowerCase()
    .split(/[^a-z0-9_]+/)
    .filter(token => token.length > 2 && !['the', 'and', 'with', 'for'].includes(token))
    .slice(0, 8);

  const matchesFeature = (text, tokens) => {
    const hay = String(text || '').toLowerCase();
    return (tokens || []).some(token => hay.includes(token));
  };

  const namesForFeature = (rows, tokens, nameOf, textOf, limit = 5) => (rows || [])
    .filter(row => matchesFeature(textOf(row), tokens))
    .map(nameOf)
    .filter(Boolean)
    .slice(0, limit);

  const semanticSectionNames = (rx, limit = 6) => (sections || [])
    .filter(section => rx.test(section.key || ''))
    .map(section => ssotTitleFor(section.key))
    .slice(0, limit);

  const statusForPresence = (present) => present ? 'approved' : 'pending';
  const coverageRows = [
    { label: 'Top module', status: statusForPresence(!!top), detail: topName },
    { label: 'Feature map', status: statusForPresence(features.length > 0), detail: `${features.length} features` },
    { label: 'Architecture', status: statusForPresence(submods.length > 0 || moduleContracts.length > 0), detail: `${submods.length || moduleContracts.length} modules` },
    { label: 'Interfaces', status: statusForPresence(interfaces.length > 0), detail: `${interfaces.length} interfaces` },
    { label: 'Function model', status: statusForPresence(!!functionSection || semanticSectionNames(/function|fsm|logic|state/i, 1).length > 0), detail: functionSection ? 'function_model' : compactDigestItems(semanticSectionNames(/function|fsm|logic|state/i, 3), 3) },
    { label: 'FSM', status: statusForPresence(fsmMachines.length > 0), detail: fsmMachines.length ? `${fsmMachines.length} machines` : compactDigestItems(semanticSectionNames(/fsm|state|transition/i, 3), 3) },
    { label: 'Cycle model', status: statusForPresence(!!cycleSection || !!timingSection || semanticSectionNames(/cycle|timing|latency|scl/i, 1).length > 0), detail: cycleSection ? 'cycle_model' : compactDigestItems(semanticSectionNames(/cycle|timing|latency|scl/i, 3), 3) },
    { label: 'Register map', status: statusForPresence(registers.length > 0), detail: `${registers.length} registers` },
    { label: 'Dataflow', status: statusForPresence(dataflowGroups.length > 0 || semanticSectionNames(/dataflow|flow|fifo|buffer|open_drain|access/i, 1).length > 0), detail: dataflowGroups.length ? `${dataflowGroups.length} flows` : compactDigestItems(semanticSectionNames(/dataflow|flow|fifo|buffer|open_drain|access/i, 3), 3) },
  ];

  const renderOverview = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          <DigestCard title="Top Module" meta={top ? `line ${top.startLine}` : ''}>
            <DigestKV rows={[
              ['name', topName],
              ['type', sectionFact(top, 'type')],
              ['clock', sectionFact(top, 'clock_freq_mhz') ? `${sectionFact(top, 'clock_freq_mhz')} MHz` : sectionFact(clockSection, 'frequency_hz')],
              ['purpose', trimSsotValue(sectionFact(top, 'description', 'No top_module.description available yet.'), 300)],
            ]} />
          </DigestCard>
          <DigestCard title="Review Coverage" meta={`${sections.length} sections`}>
            <div style={{ display: 'grid', gap: 5 }}>
              {coverageRows.map(row => (
                <div key={row.label} style={{ display: 'grid', gridTemplateColumns: '118px minmax(0, 1fr)', gap: 8, alignItems: 'center' }}>
                  <AtlasStatusBadge status={row.status} label={row.label} compact soft />
                  <span className="trunc" style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>{row.detail || '-'}</span>
                </div>
              ))}
            </div>
          </DigestCard>
        </div>
        <DigestCard title="Architecture" meta={`${submods.length} submodules`}>
          {submods.length ? <ModuleTree topName={topName} modules={submods.slice(0, 10)} /> : (
            <DigestList items={moduleContracts.map(contract => `${contract.module}: ${compactDigestItems(contract.owns, 4)}`)} />
          )}
        </DigestCard>
        <div style={{ display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          <DigestCard title="Features" meta={`${features.length} items`}>
            <DigestList items={features.map(f => `${f.name}${f.datapath ? ` - ${trimSsotValue(f.datapath, 90)}` : ''}`)} limit={6} />
          </DigestCard>
          <DigestCard title="Interfaces" meta={`${interfaces.length} interfaces`}>
            <DigestList items={interfaces.map(iface => `${iface.name}${iface.type ? ` (${iface.type})` : ''}${iface.ports.length ? ` · ${iface.ports.length} ports` : ''}`)} limit={6} />
          </DigestCard>
          <DigestCard title="Registers / Dataflow" meta={`${registers.length} regs`}>
            <DigestKV rows={[
              ['registers', compactDigestItems(registers.map(reg => `${reg.name}${reg.offset ? ` @ ${reg.offset}` : ''}`), 5)],
              ['dataflow', compactDigestItems(dataflowGroups.map(g => ssotTitleFor(g.key)), 5) || compactDigestItems(semanticSectionNames(/dataflow|flow|fifo|buffer|open_drain|access/i, 5), 5)],
              ['function', sectionFact(functionSection, 'purpose') || compactDigestItems(semanticSectionNames(/function|fsm|logic|state/i, 4), 4)],
              ['fsm', compactDigestItems(fsmMachines.map(machine => `${machine.name} (${machine.states.length} states)`), 4)],
              ['cycle', sectionFact(cycleSection, 'purpose') || compactDigestItems(semanticSectionNames(/cycle|timing|latency|scl/i, 4), 4)],
            ]} />
          </DigestCard>
        </div>
      </div>
    </>
  );

  const renderFeatures = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 14 }}>
        {features.length ? features.map((f, i) => (
          <FeatureCard key={`${f.name}-${i}`} index={i + 1} feature={f} />
        )) : <DigestEmpty />}
      </div>
    </>
  );

  const renderFeatureMap = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        {features.length ? features.map(feature => {
          const tokens = featureTokens(feature);
          const ownedModules = namesForFeature(
            submods,
            tokens,
            row => row.name,
            row => [row.name, row.description, ...(row.implements || []), ...(row.sourceSections || [])].join(' '),
          );
          const contractModules = namesForFeature(
            moduleContracts,
            tokens,
            row => row.module,
            row => [row.module, row.implementation, ...(row.owns || []), ...(row.inputs || []), ...(row.outputs || [])].join(' '),
          );
          const relatedRegisters = namesForFeature(
            registers,
            tokens,
            row => `${row.name}${row.offset ? ` @ ${row.offset}` : ''}`,
            row => [row.name, row.description, ...(row.fields || []).map(field => `${field.name} ${field.description}`)].join(' '),
          );
          const relatedFlows = namesForFeature(
            dataflowGroups,
            tokens,
            row => ssotTitleFor(row.key),
            row => `${row.key} ${row.text}`,
          );
          const relatedFunction = namesForFeature(
            transactions,
            tokens,
            row => blockField(row, 'id') || blockField(row, 'name'),
            row => row.text,
          );
          const relatedCycle = namesForFeature(
            [...latencyGroups, ...handshakeRules, ...pipeline],
            tokens,
            row => row.key || blockField(row, 'signal') || blockField(row, 'stage') || blockField(row, 'name'),
            row => row.text,
          );
          const modules = compactDigestItems([...new Set([...ownedModules, ...contractModules])], 5);
          return (
            <DigestCard key={feature.name} title={feature.name} meta={feature.sourceKey || feature.trigger}>
              <DigestKV rows={[
                ['what', feature.datapath || feature.output || feature.trigger],
                ['implemented by', modules || compactDigestItems(featureSections.filter(section => matchesFeature(section.text, tokens)).map(section => ssotTitleFor(section.key)), 5)],
                ['submodule direction', compactDigestItems(moduleContracts.filter(contract => matchesFeature(contract.implementation, tokens)).map(contract => `${contract.module}: ${trimSsotValue(contract.implementation, 90)}`), 2)],
                ['control path', feature.control || compactDigestItems(relatedRegisters, 4)],
                ['function model', compactDigestItems(relatedFunction, 4) || sectionFact(functionSection, 'purpose')],
                ['cycle model', compactDigestItems(relatedCycle, 4) || sectionFact(cycleSection, 'purpose')],
                ['registers', compactDigestItems(relatedRegisters, 5)],
                ['dataflow', compactDigestItems(relatedFlows, 5)],
                ['observable output', feature.output],
              ]} />
            </DigestCard>
          );
        }) : (
          <DigestCard title="Feature Map">
            <DigestEmpty text="No feature-level entries were found. Review Gaps shows which anchors are missing." />
          </DigestCard>
        )}
      </div>
    </>
  );

  const renderArchitecture = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard title="Block Diagram" meta={`${topName} → ${submods.length} submodules · ${interfaces.length} interfaces`}>
          {submods.length ? (
            <BlockDiagram
              topName={topName}
              modules={submods}
              contractByModule={contractByModule}
              interfaces={interfaces}
              clockSection={clockSection}
              parameters={parameters}
            />
          ) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Module Tree" meta={`${topName} + ${submods.length} submodules`}>
          {submods.length ? (
            <ModuleTree topName={topName} modules={submods} />
          ) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Module Split" meta={`${submods.length} submodules`}>
          {submods.length ? (
            <div style={{ display: 'grid', gap: 9 }}>
              {submods.map(m => {
                const contract = contractByModule[m.name] || {};
                const localInputs = (contract.inputs || []).length ? contract.inputs : [];
                const localOutputs = (contract.outputs || []).length ? contract.outputs : [];
                const owns = (contract.owns || []).length ? contract.owns : m.implements;
                return (
                  <div key={m.name} style={{ borderBottom: '1px solid var(--line)', paddingBottom: 7 }}>
                    <div><b>{m.name}</b> <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>{m.file}</span></div>
                    <div className="mute" style={{ marginTop: 2 }}>{m.description}</div>
                    {owns.length ? <div style={{ marginTop: 3, color: 'var(--cyan)', fontFamily: 'var(--mono)', fontSize: 10 }}>direction: {owns.join(', ')}</div> : null}
                    {localInputs.length || localOutputs.length ? (
                      <DigestKV rows={[
                        ['inputs', localInputs.join('; ')],
                        ['outputs', localOutputs.join('; ')],
                      ]} />
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : <DigestEmpty />}
        </DigestCard>
        {moduleContracts.length ? (
          <DigestCard title="Implementation Direction" meta={`${moduleContracts.length} module contracts`}>
            <div style={{ display: 'grid', gap: 10 }}>
              {moduleContracts.map(contract => (
                <div key={contract.module} style={{ borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
                  <div style={{ fontWeight: 800 }}>{contract.module}</div>
                  {contract.implementation ? <div className="mute" style={{ marginTop: 2 }}>{contract.implementation}</div> : null}
                  <DigestKV rows={[
                    ['owns', contract.owns.join('; ')],
                    ['inputs', contract.inputs.join('; ')],
                    ['outputs', contract.outputs.join('; ')],
                  ]} />
                </div>
              ))}
            </div>
          </DigestCard>
        ) : null}
        {decompSection ? <DigestSourceSections view={{ keys: ['decomposition'] }} sections={sections} statusByKey={statusByKey} t={t} /> : null}
      </div>
    </>
  );

  const renderFunctionModel = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard title="Purpose">
          <div>{sectionFact(functionSection, 'purpose', 'No function model purpose available yet.')}</div>
        </DigestCard>
        <DigestCard title="Transactions" meta={`${transactions.length} transactions`}>
          {transactions.length ? transactions.map(tx => (
            <div key={blockField(tx, 'id') || blockField(tx, 'name')} style={{ marginBottom: 10, borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
              <div><b>{blockField(tx, 'id')}</b> {blockField(tx, 'name')}</div>
              <DigestKV rows={[
                ['preconditions', blockListValues(tx, 'preconditions', 4).join('; ')],
                ['inputs', blockListValues(tx, 'inputs', 4).join('; ')],
                ['outputs', blockListValues(tx, 'outputs', 4).join('; ')],
                ['side effects', blockListValues(tx, 'side_effects', 4).join('; ')],
              ]} />
            </div>
          )) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="State Variables" meta={`${stateVars.length} variables`}>
          {stateVars.length ? (
            <div style={{ display: 'grid', gap: 5 }}>
              {stateVars.map(v => <DigestKV key={blockField(v, 'name')} rows={[[blockField(v, 'name'), `${blockField(v, 'source')} · reset ${blockField(v, 'reset')} · ${blockField(v, 'description')}`]]} />)}
            </div>
          ) : <DigestEmpty />}
        </DigestCard>
      </div>
    </>
  );

  const renderFsm = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard
          title="FSM Summary"
          meta={`${fsmMachines.length} machines · ${fsmMachines.reduce((sum, m) => sum + uniqueFsmStates(m).length, 0)} states · ${fsmMachines.reduce((sum, m) => sum + m.transitions.length, 0)} transitions`}
        >
          {fsmMachines.length ? (
            <DigestKV rows={[
              ['machines', compactDigestItems(fsmMachines.map(machine => machine.name), 8)],
              ['reset states', compactDigestItems(fsmMachines.map(machine => machine.resetState ? `${machine.name}: ${machine.resetState}` : '').filter(Boolean), 6)],
              ['source', fsmSection ? `fsm section line ${fsmSection.startLine}` : 'No fsm section found'],
            ]} />
          ) : (
            <DigestEmpty text="No structured FSM section found. Add fsm.<machine>.states and fsm.<machine>.transitions to SSOT." />
          )}
        </DigestCard>
        {fsmMachines.map((machine, machineIdx) => {
          const graph = fsmGraphFromMachine(machine);
          return (
            <DigestCard
              key={machine.name}
              title={machine.name}
              meta={`${graph.states.length} states · ${graph.transitions.length} transitions`}
            >
              <DigestKV rows={[
                ['reset', machine.resetState],
                ['illegal recovery', machine.illegalRecovery],
                ['outputs', machine.outputs.join('; ')],
                ['actions', machine.actions.join('; ')],
                ['note', machine.note],
              ]} />
              {graph.states.length ? (
                <div style={{ marginTop: 10 }}>
                  <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, marginBottom: 5 }}>states</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {graph.states.map(state => (
                      <span
                        key={`${machine.name}:${state.id}`}
                        style={{
                          border: '1px solid var(--line-2)',
                          borderRadius: 3,
                          padding: '3px 7px',
                          fontFamily: 'var(--mono)',
                          fontSize: 11,
                          color: state.reset ? 'var(--accent)' : 'var(--fg)',
                          background: state.reset
                            ? 'color-mix(in oklch, var(--accent) 14%, transparent)'
                            : 'var(--bg-3)',
                        }}
                      >
                        {state.label}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
              <FsmTransitionDiagram machine={machine} index={machineIdx} />
            </DigestCard>
          );
        })}
      </div>
    </>
  );

  const renderCycleModel = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard title="Cycle Contract">
          <DigestKV rows={[
            ['purpose', sectionFact(cycleSection, 'purpose')],
            ['clock', sectionFact(cycleSection, 'clock')],
            ['reset assertion', sectionFact(cycleSection, 'assertion')],
            ['reset deassertion', sectionFact(cycleSection, 'deassertion')],
          ]} />
        </DigestCard>
        <DigestCard title="Latency" meta={`${latencyGroups.length} paths`}>
          {latencyGroups.length ? latencyGroups.map(g => (
            <DigestKV key={g.key} rows={[[g.key, `${fieldFromText(g.text, 'min_cycles') || '?'}-${fieldFromText(g.text, 'max_cycles') || '?'} cycles · ${fieldFromText(g.text, 'description')}`]]} />
          )) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Handshake / Pipeline" meta={`${handshakeRules.length} rules · ${pipeline.length} stages`}>
          {handshakeRules.slice(0, 8).map(r => <div key={blockField(r, 'signal')} style={{ marginBottom: 4 }}><b>{blockField(r, 'signal')}</b> <span className="mute">{blockField(r, 'rule', 320)}</span></div>)}
          {pipeline.length ? <hr style={{ border: 0, borderTop: '1px solid var(--line)', margin: '8px 0' }} /> : null}
          {pipeline.map(p => <div key={blockField(p, 'stage')} style={{ marginBottom: 4 }}><b>{blockField(p, 'stage')}</b> <span className="mute">{blockField(p, 'cycle')} · {blockField(p, 'action', 320)}</span></div>)}
        </DigestCard>
      </div>
    </>
  );

  const renderInterfaces = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <div style={{ color: 'var(--accent)', fontWeight: 800, fontSize: 12 }}>Top Module External Interfaces <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>{interfaces.length} interfaces</span></div>
        {interfaces.length ? interfaces.map(iface => (
          <DigestCard key={iface.name} title={iface.name} meta={`${iface.type}${iface.role ? ` · ${iface.role}` : ''} · ${iface.ports.length} ${t.ports}`}>
            <div className="mute" style={{ marginBottom: 8 }}>{iface.description}</div>
            <div style={{ display: 'grid', gap: 4 }}>
              {iface.ports.map(port => (
                <div key={port.name} style={{ display: 'grid', gridTemplateColumns: 'minmax(110px, 0.7fr) 56px minmax(70px, max-content) minmax(0, 1.4fr)', gap: 10, fontFamily: 'var(--mono)', fontSize: 11, alignItems: 'baseline' }}>
                  <span style={{ color: 'var(--fg)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{port.name}</span>
                  <span className="mute">{port.direction}</span>
                  <span className="mute" style={{ whiteSpace: 'nowrap' }}>{_formatWidth(port.width) || '[0]'}</span>
                  <span className="mute" style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{port.description}</span>
                </div>
              ))}
            </div>
          </DigestCard>
        )) : <DigestEmpty />}
        {moduleContracts.length ? (
          <DigestCard title="Submodule Local Interfaces" meta={`${moduleContracts.length} modules`}>
            <div style={{ display: 'grid', gap: 10 }}>
              {moduleContracts.map(contract => (
                <div key={contract.module} style={{ borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
                  <div style={{ fontWeight: 800 }}>{contract.module}</div>
                  <DigestKV rows={[
                    ['inputs', contract.inputs.join('; ')],
                    ['outputs', contract.outputs.join('; ')],
                  ]} />
                  {contract.interfaces.length ? (
                    <div style={{ marginTop: 7, display: 'grid', gap: 6 }}>
                      {contract.interfaces.map(iface => (
                        <div key={iface.name}>
                          <b>{iface.name}</b> <span className="mute">{iface.type}{iface.role ? ` · ${iface.role}` : ''}</span>
                          <DigestKV rows={[
                            ['inputs', iface.inputs.join('; ')],
                            ['outputs', iface.outputs.join('; ')],
                            ['description', iface.description],
                          ]} />
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </DigestCard>
        ) : null}
      </div>
    </>
  );

  const renderRegisters = () => (
    <>
      {header}
      <DigestCard title="Register Map" meta={`${registers.length} registers`}>
        {registers.length ? registers.map(reg => (
          <div key={reg.name} style={{ marginBottom: 11, borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
            <div><b>{reg.name}</b> <span className="mute" style={{ fontFamily: 'var(--mono)' }}>@ {reg.offset} · {reg.access} · reset {reg.reset}</span></div>
            <div className="mute" style={{ marginTop: 2 }}>{reg.description}</div>
            {reg.fields.length ? <div style={{ marginTop: 5, color: 'var(--cyan)', fontFamily: 'var(--mono)', fontSize: 10 }}>{reg.fields.slice(0, 10).map(f => `${f.name}(${f.access})`).join(', ')}</div> : null}
          </div>
        )) : <DigestEmpty />}
      </DigestCard>
    </>
  );

  const renderDataflow = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        {dataflowGroups.length ? dataflowGroups.map(g => (
          <DigestCard key={g.key} title={ssotTitleFor(g.key)}>
            <DigestKV rows={[
              ['source', fieldFromText(g.text, 'source')],
              ['sequence', blockListValues(g, 'sequence', 8).join(' -> ')],
              ['buffer', fieldFromText(g.text, 'buffer')],
              ['backpressure', fieldFromText(g.text, 'backpressure', 360)],
              ['description', fieldFromText(g.text, 'description', 360)],
            ]} />
          </DigestCard>
        )) : <DigestEmpty />}
      </div>
    </>
  );

  const renderClocking = () => (
    <>
      {header}
      <div style={{ display: 'grid', gap: 10 }}>
        <DigestCard title="Clock Domains" meta={`${clockDomains.length} domains`}>
          {clockDomains.length ? clockDomains.map(d => <DigestKV key={d.name} rows={[[d.name, `${d.frequency || '?'} MHz · ${d.description}`]]} />) : <DigestEmpty />}
        </DigestCard>
        <DigestCard title="Reset">
          {resets.length ? resets.map(r => <DigestKV key={r.name} rows={[[r.name, `${r.polarity} · ${r.type} · ${r.description}`]]} />) : <DigestKV rows={[['scheme', sectionFact(clockSection, 'type') || sectionFact(clockSection, 'reset_scheme')]]} />}
        </DigestCard>
        <DigestCard title="CDC / RDC" meta={`${cdcCrossings.length} CDC crossings`}>
          {cdcCrossings.length ? cdcCrossings.map(c => <DigestKV key={c.name} rows={[[c.name, `${c.from} -> ${c.to} · ${c.synchronizer} · ${c.description}`]]} />) : <DigestEmpty text={sectionFact(rdcSection, 'note') || 'No CDC crossings listed.'} />}
        </DigestCard>
      </div>
    </>
  );

  const renderReviewGaps = () => {
    const explicitGaps = (sections || []).flatMap(section => (
      ((section.summary && section.summary.gaps) || []).map(gap => ({
        key: section.key,
        line: gap.line,
        text: gap.text,
      }))
    ));
    const missing = coverageRows.filter(row => row.status !== 'approved');
    return (
      <>
        {header}
        <div style={{ display: 'grid', gap: 10 }}>
          <DigestCard title="Review Coverage" meta={`${coverageRows.length} anchors`}>
            <div style={{ display: 'grid', gap: 6 }}>
              {coverageRows.map(row => (
                <div key={row.label} style={{
                  display: 'grid', gridTemplateColumns: '150px minmax(0, 1fr)',
                  gap: 8, alignItems: 'center', borderBottom: '1px solid var(--line)', paddingBottom: 5,
                }}>
                  <AtlasStatusBadge status={row.status} label={row.label} compact soft />
                  <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11, minWidth: 0, wordBreak: 'break-word' }}>
                    {row.detail || '-'}
                  </span>
                </div>
              ))}
            </div>
          </DigestCard>
          <DigestCard title="Missing Anchors" meta={`${missing.length} missing`}>
            {missing.length ? (
              <DigestList items={missing.map(row => `${row.label}: ${row.detail || 'not found'}`)} />
            ) : <DigestEmpty text="All core review anchors have structured SSOT coverage." />}
          </DigestCard>
          <DigestCard title="Open Flags" meta={`${explicitGaps.length} flags`}>
            {explicitGaps.length ? (
              <div style={{ display: 'grid', gap: 7 }}>
                {explicitGaps.slice(0, 18).map(gap => (
                  <div key={`${gap.key}:${gap.line}:${gap.text}`} style={{ borderLeft: '2px solid var(--warn)', paddingLeft: 8 }}>
                    <div style={{ color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>{ssotTitleFor(gap.key)} · line {gap.line}</div>
                    <div style={{ marginTop: 2 }}>{gap.text}</div>
                  </div>
                ))}
              </div>
            ) : <DigestEmpty text="No TBD, TODO, placeholder, pending, null, or unspecified markers detected." />}
          </DigestCard>
        </div>
      </>
    );
  };

  const renderRawYaml = () => {
    // Embed FoldablePane directly without the DigestCard wrapper —
    // DigestCard pins height for chip-sized content and clipped the
    // scrollable fold body. Now matches /tmp/ssot_fold_engine.html
    // exactly: a single full-bleed fold pane with the toolbar at top,
    // the chat input is the global ATLAS textarea reached via the
    // atlas-fold-comment custom event.
    const lineCount = (content || '').split('\n').length;
    if (!selected || !content) {
      return (
        <>
          {header}
          <div style={{ padding: 16, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12 }}>
            {selected ? 'loading…' : 'no SSOT file selected'}
          </div>
        </>
      );
    }
    return (
      <>
        {header}
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <FoldablePane path={selected} body={content} lang="yaml" lineCount={lineCount} />
        </div>
      </>
    );
  };

  const renderGates = () => {
    const ipFromPath = (() => {
      const p = String(selected || '').trim();
      if (!p) return '';
      const seg = p.split('/').filter(Boolean);
      return seg[0] || '';
    })();
    return (
      <>
        {header}
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '10px 12px' }}>
          <GatesPanel ip={ipFromPath} />
        </div>
      </>
    );
  };

  const renderGeneric = (title, sourceSections) => (
    <>
      {header}
      {sourceSections.length ? <DigestSourceSections view={{ keys: sourceSections.map(s => s.key) }} sections={sections} statusByKey={statusByKey} t={t} /> : <DigestEmpty />}
    </>
  );

  const sourceSections = sourceSectionsForDigestView(view, sections);
  let body;
  if (view.id === 'overview') body = renderOverview();
  else if (view.id === 'features') body = renderFeatures();
  else if (view.id === 'architecture') body = renderArchitecture();
  else if (view.id === 'feature_map') body = renderFeatureMap();
  else if (view.id === 'function_model') body = renderFunctionModel();
  else if (view.id === 'fsm') body = renderFsm();
  else if (view.id === 'cycle_model') body = renderCycleModel();
  else if (view.id === 'interfaces') body = renderInterfaces();
  else if (view.id === 'registers') body = renderRegisters();
  else if (view.id === 'dataflow') body = renderDataflow();
  else if (view.id === 'clocking') body = renderClocking();
  else if (view.id === 'review_gaps') body = renderReviewGaps();
  else if (view.id === 'gates') body = renderGates();
  else if (view.id === 'raw_yaml') body = renderRawYaml();
  else body = renderGeneric(view.label, sourceSections);

  return (
    <>
      {body}
      {!['architecture', 'overview', 'review_gaps', 'raw_yaml', 'gates'].includes(view.id) ? (
        <DigestSourceSections view={view} sections={sections} statusByKey={statusByKey} t={t} />
      ) : null}
    </>
  );
};

const chooseSsotFile = (files, preferredPath = '') => {
  const paths = (Array.isArray(files) ? files : []).map(ssotPathOf).filter(Boolean);
  if (preferredPath && (paths.includes(preferredPath) || isSsotYamlPath(preferredPath))) return preferredPath;
  const scope = String(window.SCOPE_PATH || '').split('/').filter(Boolean).pop() || '';
  const sessionIp = ssotIpFromSession(window.ACTIVE_SESSION || '');
  const explicitIp = String(window.ACTIVE_IP || '').trim();
  // When IP context is the literal `default` placeholder (or empty),
  // do NOT auto-pick the first SSOT in the workspace — that misleads
  // the user into thinking the current session owns that IP. Show the
  // empty/default-workspace state instead and let them pick an IP.
  const ipFromContext = sessionIp || (explicitIp && explicitIp !== 'default' ? explicitIp : '') || scope;
  const isDefault = !ipFromContext || ipFromContext === 'default';
  if (isDefault) return '';
  return paths.find(p => p === `${ipFromContext}.ssot.yaml` || p.includes(`${ipFromContext}/`) || p.includes(`/${ipFromContext}.`))
    || '';
};

const SsotReviewPane = ({ uiLang = 'ko', initialPath = '', onBack }) => {
  const files = Array.isArray(window.SSOT_FILES) ? window.SSOT_FILES : [];
  const [selected, setSelected] = React.useState('');
  const [activeKey, setActiveKey] = React.useState('');
  const lastInitialPath = React.useRef('');

  const t = uiLang === 'en'
    ? {
        title: 'SSOT Design Preview',
        subtitle: 'Human-readable IP digest from SSOT sections.',
        file: 'file',
        empty: 'No *.ssot.yaml files in this project yet.',
        sections: 'views',
        flags: 'flags',
        approved: 'approved',
        raw: 'Raw YAML section',
        reload: 'refresh',
      }
    : {
        title: 'SSOT 설계 프리뷰',
        subtitle: 'SSOT 섹션을 사람이 읽는 IP digest로 보여줍니다.',
        file: '파일',
        empty: '아직 프로젝트에 *.ssot.yaml 파일이 없습니다.',
        sections: '뷰',
        flags: '리뷰 플래그',
        approved: '승인',
        raw: '원본 YAML 섹션',
        reload: '새로고침',
      };

  const ssotFilePaths = files.map(ssotPathOf).filter(Boolean);
  const filePaths = initialPath && isSsotYamlPath(initialPath) && !ssotFilePaths.includes(initialPath)
    ? [initialPath, ...ssotFilePaths]
    : ssotFilePaths;
  const filePathKey = filePaths.join('|');
  const [ssotResource, reloadSsot] = useAtlasAsyncResource('ssot', selected, {
    versionKey: filePathKey,
    forceOnVersionChange: true,
  });
  const content = selected ? (ssotResource.body || '') : '';
  const loading = !!selected && !!ssotResource.loading;
  const ssotHasContent = !!content.trim();
  const showLoading = loading && !content.trim();

  // Auto-reload the SSOT view when the backend writes to the
  // currently-selected yaml. Matches by path suffix so both relative
  // (selected = "spi/yaml/spi.ssot.yaml") and absolute (event path =
  // /full/path/.../spi.ssot.yaml) hits resolve.
  React.useEffect(() => {
    if (!selected) return undefined;
    const handler = (ev) => {
      const changed = (ev && ev.detail && ev.detail.path) || '';
      if (!changed) return;
      if (changed === selected
          || changed.endsWith('/' + selected)
          || selected.endsWith('/' + changed)) {
        reloadSsot(true);
      }
    };
    window.addEventListener('atlas-file-changed', handler);
    return () => window.removeEventListener('atlas-file-changed', handler);
  }, [selected, reloadSsot]);

  React.useEffect(() => {
    if (initialPath && initialPath !== lastInitialPath.current && filePaths.includes(initialPath)) {
      lastInitialPath.current = initialPath;
      setSelected(initialPath);
    }
  }, [initialPath, filePathKey]);

  React.useEffect(() => {
    if (!filePaths.length) {
      if (selected) setSelected('');
      return;
    }
    if (!selected || !filePaths.includes(selected)) {
      setSelected(chooseSsotFile(files, initialPath));
    }
  }, [filePathKey, selected, initialPath]);

  const sections = React.useMemo(() => splitSsotSections(content), [content]);
  const statusByKey = React.useMemo(() => ssotProgressStatusMap(), [content, filePathKey]);
  const digestViews = React.useMemo(() => digestViewsForSections(sections), [sections]);
  const digestViewKey = digestViews.map(v => v.id).join('|');

  React.useEffect(() => {
    if (!digestViews.length) {
      setActiveKey('');
      return;
    }
    if (!activeKey || !digestViews.some(v => v.id === activeKey)) setActiveKey(digestViews[0].id);
  }, [digestViewKey, activeKey]);

  const activeView = digestViews.find(v => v.id === activeKey) || digestViews[0] || null;
  const approvedCount = sections.filter(s => ssotSectionStatus(s, statusByKey) === 'approved').length;
  const flagCount = sections.reduce((sum, s) => sum + ((s.summary && s.summary.gaps.length) || 0), 0);

  if (!filePaths.length) {
    return (
      <div style={{ flex: 1, minHeight: 0, padding: '16px 18px', overflow: 'auto' }}>
        <div className="code" style={{ padding: 16, color: 'var(--fg-mute)' }}>
          # {t.empty}<br />
          # /grill-me → /to-ssot writes the review source.
        </div>
      </div>
    );
  }

  return (
    <div style={{
      flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
      overflow: 'hidden', background: 'var(--bg)',
    }}>
      <div style={{
        padding: '10px 14px', borderBottom: '1px solid var(--line)',
        display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) auto',
        gap: 12, alignItems: 'center', background: 'var(--bg-2)',
      }}>
        <div style={{ minWidth: 0 }}>
          <div style={{
            color: 'var(--magenta)', fontWeight: 800, fontSize: 12,
            letterSpacing: '0.08em', textTransform: 'uppercase',
          }}>{t.title}</div>
          <div className="mute trunc" style={{ marginTop: 3, fontSize: 11, fontFamily: 'var(--mono)' }}>
            {selected || t.file} · {loading ? (ssotHasContent ? 'refreshing' : 'loading') : `${sections.length} ${t.sections}`} · {approvedCount} {t.approved} · {flagCount} {t.flags}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', minWidth: 0 }}>
          {loading ? <AtlasStatusBadge status={ssotHasContent ? 'refreshing' : 'loading'} compact /> : null}
          <select
            value={selected}
            onChange={e => setSelected(e.target.value)}
            style={{
              maxWidth: 340, minWidth: 180, background: 'var(--bg)', color: 'var(--fg)',
              border: '1px solid var(--line)', borderRadius: 2,
              fontFamily: 'var(--mono)', fontSize: 11, padding: '4px 6px',
            }}
          >
            {filePaths.map(path => <option key={path} value={path}>{path}</option>)}
          </select>
          <button
            type="button"
            className="btn"
            onClick={() => reloadSsot(true)}
            style={{ fontSize: 10 }}
          >{t.reload}</button>
          <button type="button" className="btn" onClick={onBack} style={{ fontSize: 10 }}>chat</button>
        </div>
      </div>

      <div style={{
        flex: 1, minHeight: 0, display: 'grid',
        gridTemplateColumns: 'minmax(190px, 240px) minmax(0, 1fr)',
        overflow: 'hidden',
      }}>
        <div style={{
          minHeight: 0, overflow: 'auto', borderRight: '1px solid var(--line)',
          background: 'color-mix(in oklch, var(--bg-2) 72%, transparent)',
          padding: '10px 8px',
        }}>
          {digestViews.map((view, idx) => {
            const sourceSections = sourceSectionsForDigestView(view, sections);
            const gaps = sourceSections.reduce((sum, section) => sum + ((section.summary && section.summary.gaps.length) || 0), 0);
            const approved = sourceSections.length > 0 && sourceSections.every(section => ssotSectionStatus(section, statusByKey) === 'approved');
            const status = gaps ? 'needs review' : approved ? 'approved' : 'review';
            const activeRow = activeView && activeView.id === view.id;
            const color = ssotStatusColor(status);
            const sourceLabel = sourceSections.length
              ? compactDigestItems(sourceSections.map(section => section.key), 4)
              : (view.keys.join(' + ') || 'all sections');
            return (
              <button
                key={view.id + ':' + idx}
                type="button"
                onClick={() => setActiveKey(view.id)}
                title={`${sourceLabel} · ${status}`}
                style={{
                  width: '100%', textAlign: 'left', display: 'grid',
                  gridTemplateColumns: '22px minmax(0, 1fr) auto',
                  gap: 8, alignItems: 'center',
                  background: activeRow
                    ? (view.id === 'raw_yaml' ? 'var(--bg-3)' : 'color-mix(in oklch, var(--magenta) 14%, transparent)')
                    : 'transparent',
                  color: activeRow ? 'var(--fg)' : 'var(--fg-mute)',
                  border: '1px solid ' + (activeRow ? (view.id === 'raw_yaml' ? 'var(--line-2)' : 'var(--magenta)') : 'transparent'),
                  borderRadius: 3, padding: '6px 7px', marginBottom: 4,
                  cursor: 'pointer', fontFamily: 'var(--mono)',
                }}
              >
                <span style={{ color, fontSize: 12, textAlign: 'center' }}>
                  {status === 'approved' ? 'OK' : gaps ? '!' : '·'}
                </span>
                <span style={{ minWidth: 0 }}>
                  <span className="trunc" style={{ display: 'block', fontSize: 12, fontWeight: activeRow ? 800 : 600 }}>
                    {view.label}
                  </span>
                  <span className="trunc" style={{ display: 'block', fontSize: 10, color: 'var(--fg-mute)' }}>
                    {sourceLabel}
                  </span>
                </span>
                <span style={{
                  color, fontSize: 10, border: `1px solid ${color}`,
                  borderRadius: 2, padding: '0 4px', whiteSpace: 'nowrap',
                }}>
                  {gaps || sourceSections.length}
                </span>
              </button>
            );
          })}
        </div>

        <div style={{ minHeight: 0, overflow: 'auto', padding: '14px 18px' }}>
          {ssotResource.err ? (
            <div style={{
              marginBottom: 10, padding: '6px 10px',
              border: '1px solid var(--err)',
              background: 'color-mix(in oklch, var(--err) 12%, transparent)',
              color: 'var(--err)', fontFamily: 'var(--mono)', fontSize: 10,
            }}>
              ssot load error: {ssotResource.err}
            </div>
          ) : null}
          {showLoading ? (
            <div className="code" style={{ padding: 16, color: 'var(--fg-mute)' }}># loading SSOT...</div>
          ) : activeView ? (
            <SsotDigestContent
              view={activeView}
              sections={sections}
              statusByKey={statusByKey}
              uiLang={uiLang}
              content={content}
              selected={selected}
            />
          ) : (
            <div className="code" style={{ padding: 16, color: 'var(--fg-mute)' }}># no sections parsed</div>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Right panels ──────────────────────────────────────────────────
// Live SSOT panel — lists every *.ssot.yaml under the project (or the
// current scope path, if /api/ssot ever filters by it) and shows the
// content of whichever one the user clicks on. Auto-refreshes when the
// agent writes a new SSOT (data.jsx subscribes to tool_result).
const SsotPanel = () => {
  const files = window.SSOT_FILES || [];
  const [selected, setSelected] = React.useState(null);
  const [content, setContent] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  // Default to the first file once the list is populated.
  React.useEffect(() => {
    if (!selected && files.length > 0) setSelected(files[0].path);
  }, [files.length, selected]);

  // Fetch content whenever the selected file changes (or the file list
  // refreshes — the user may want to see updated content for an SSOT
  // the agent just wrote).
  React.useEffect(() => {
    if (!selected) { setContent(''); return; }
    let cancelled = false;
    setLoading(true);
    window.atlasData.fetchSsot(selected).then(d => {
      if (cancelled) return;
      setContent(d?.content || `# (could not read ${selected})`);
      setLoading(false);
    }).catch(() => { if (!cancelled) { setContent(''); setLoading(false); } });
    return () => { cancelled = true; };
  }, [selected, files.length]);

  if (files.length === 0) {
    return (
      <div className="code" style={{ flex: 1, overflow: 'auto',
        padding: '14px 16px', fontSize: 12, color: 'var(--fg-mute)' }}>
        # No *.ssot.yaml files in the project yet.<br />
        # Use <span className="acc">/grill-me</span> to gather the spec
        and <span className="acc">/to-ssot &lt;ip&gt;</span> to write the YAML.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* file picker */}
      <div style={{
        borderBottom: '1px solid var(--line)', padding: '4px 6px',
        display: 'flex', flexWrap: 'wrap', gap: 4,
        background: 'var(--bg-2)',
      }}>
        {files.map(f => (
          <span key={f.path}
            onClick={() => setSelected(f.path)}
            title={f.path}
            style={{
              cursor: 'pointer',
              padding: '2px 8px', fontSize: 10,
              fontFamily: 'var(--mono)',
              border: `1px solid ${selected === f.path ? 'var(--accent)' : 'var(--line)'}`,
              color: selected === f.path ? 'var(--accent)' : 'var(--fg-mute)',
              background: selected === f.path ? 'var(--bg-3, var(--bg-2))' : 'transparent',
              borderRadius: 2,
            }}>
            {f.path.split('/').pop()}
          </span>
        ))}
      </div>
      {/* content viewer */}
      <pre className="code" style={{
        flex: 1, overflow: 'auto', margin: 0,
        padding: '12px 14px', fontSize: 12, lineHeight: 1.55,
        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {loading ? '# loading…' : content}
      </pre>
    </div>
  );
};

const ProgressPanel = () => {
  const [, bump] = React.useReducer(x => x + 1, 0);
  const [moduleId, setModuleId] = React.useState('');

  React.useEffect(() => {
    const h = (ev) => {
      if (!ev.detail || ['PROGRESS', 'SCOPE_PATH', 'SSOT_FILES', 'TODOS'].includes(ev.detail)) bump();
    };
    window.addEventListener('atlas-data-changed', h);
    if (window.atlasData && window.atlasData.refreshProgress) window.atlasData.refreshProgress();
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  const data = window.ATLAS_PROGRESS || {};
  const modules = Array.isArray(data.modules) ? data.modules : [];
  // Active IP comes from the top-bar selector (single source of truth).
  // We derive it from ACTIVE_SESSION and pivot the panel onto that
  // module — no internal IP picker, since the user explicitly asked
  // for "IP는 맨 위에서 선택, 다른 곳에선 표시만".
  const _activeIp = (() => {
    const ns = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
    if (ns.length >= 2) return ns[1];
    return '';
  })();
  const selected = modules.find(m => (m.id || m.name) === _activeIp)
    || modules.find(m => m.id === moduleId)
    || data.selected
    || modules[0]
    || null;

  React.useEffect(() => {
    if (selected && selected.id && selected.id !== moduleId) setModuleId(selected.id);
  }, [selected && selected.id]);

  const progress = (selected && selected.progress) || {};
  const status = (selected && selected.status) || {};
  const details = (selected && selected.status_detail) || {};
  const signoff = (selected && selected.signoff) || {};
  const blockers = Array.isArray(signoff.blockers) ? signoff.blockers : [];
  const ownership = signoff.ownership || {};
  const artifact = (selected && selected.artifact_status) || {};
  const artifactDetails = (selected && selected.artifact_detail) || {};
  const req = progress.req || {};
  const ssot = progress.ssot || {};
  const flModel = progress.fl_model || {};
  const flDecomp = progress.fl_decomp || {};
  const fcovPlan = progress.fcov_plan || {};
  const equiv = progress.equivalence_goals || {};
  const goalAudit = progress.goal_audit || {};
  const rtl = progress.rtl || {};
  const compile = progress.compile || {};
  const lint = progress.lint || {};
  const sim = progress.sim || {};
  const dv = sim.dv_plan || {};
  const results = sim.results || {};
  const coverage = sim.coverage || {};

  const pct = (obj) => Math.max(0, Math.min(100, Number(obj && obj.pct) || 0));
  const stateColor = (s) => {
    const v = String(s || '').toLowerCase();
    if (['ok', 'pass', 'approved', 'done'].includes(v)) return 'var(--ok)';
    if (['fail', 'err', 'error', 'rejected'].includes(v)) return 'var(--err)';
    if (['partial', 'planned', 'active', 'blocked', 'stale'].includes(v)) return 'var(--warn)';
    return 'var(--fg-mute)';
  };
  const pill = (label, value) => (
    <span style={{
      border: `1px solid ${stateColor(value)}`,
      color: stateColor(value),
      borderRadius: 2,
      padding: '1px 6px',
      fontSize: 10,
      fontFamily: 'var(--mono)',
      whiteSpace: 'nowrap',
    }}>{label}: {value || 'pending'}</span>
  );
  const Bar = ({ label, done, total, value, color = 'var(--ok)' }) => {
    const p = value != null ? Math.max(0, Math.min(100, Number(value) || 0))
      : (total ? Math.round(100 * (done || 0) / total) : 0);
    return (
      <div style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--fg-mute)', marginBottom: 3 }}>
          <span>{label}</span>
          <span>{done != null && total != null ? `${done}/${total}` : `${p}%`}</span>
        </div>
        <div style={{ height: 5, background: 'var(--bg-3)', border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${p}%`, background: color }} />
        </div>
      </div>
    );
  };
  const Section = ({ title, right, children }) => (
    <div style={{ borderBottom: '1px solid var(--line)', padding: '10px 12px' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8,
        fontSize: 10, fontFamily: 'var(--mono)', letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}>
        <span style={{ color: 'var(--fg)', fontWeight: 700 }}>{title}</span>
        <span style={{ flex: 1 }} />
        {right && <span className="mute" style={{ letterSpacing: 0, textTransform: 'none' }}>{right}</span>}
      </div>
      {children}
    </div>
  );
  const repairRtl = () => {
    const ip = selected && (selected.id || selected.name || selected.ip_dir || '');
    if (!ip || !window.backend) return;
    window.backend.send({ type: 'prompt', text: `/repair-rtl ${ip}` });
  };

  if (!selected) {
    return (
      <div className="code" style={{ flex: 1, padding: '14px 16px', overflow: 'auto', color: 'var(--fg-mute)', fontSize: 12 }}>
        # No SSOT-backed IP progress found.<br />
        # Create or select a leaf SSOT YAML, then run the ATLAS SSOT → RTL → TB → sim_debug flow.
      </div>
    );
  }

  const sections = Array.isArray(ssot.sections) ? ssot.sections : [];
  const rtlModules = Array.isArray(rtl.modules) ? rtl.modules : [];
  const scenarios = Array.isArray(dv.scenario_rows) ? dv.scenario_rows : [];
  const criteria = coverage.criteria && typeof coverage.criteria === 'object' ? coverage.criteria : {};
  const limitations = coverage.limitations && typeof coverage.limitations === 'object' ? coverage.limitations : {};
  const staticCov = coverage.static && typeof coverage.static === 'object' ? coverage.static : {};
  const ownershipRows = [
    'req', 'ssot', 'fl_model', 'fl_decomp', 'fcov_plan', 'equivalence_goals',
    'goal_audit', 'rtl', 'lint', 'tb', 'sim_debug', 'coverage', 'signoff',
  ].map(k => ownership[k]).filter(Boolean);

  return (
    <div style={{ flex: 1, overflow: 'auto', fontSize: 11 }}>
      <div style={{ padding: '9px 12px', borderBottom: '1px solid var(--line)', background: 'var(--bg-2)' }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 8 }}>
          {/* Display-only IP label — IP selection happens at the top-bar
              dir-switcher (single source of truth). Showing a duplicate
              picker here lets the panel drift out of sync from the
              actual active IP. Click hint suggests where to switch. */}
          <span
            title={`Active IP — switch from the top-bar IP picker.\n${selected.ssot_path || ''}`}
            style={{
              flex: 1, minWidth: 0,
              padding: '4px 8px',
              background: 'var(--bg-3)',
              color: 'var(--fg)',
              border: '1px solid var(--line)',
              borderRadius: 2,
              fontFamily: 'var(--mono)', fontSize: 11,
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              cursor: 'default', userSelect: 'none',
            }}
          >
            {selected.label || selected.name || selected.id || '(no IP)'}
          </span>
          <span className="mute" title={selected.ssot_path || ''}>{selected.kind || 'ip'}</span>
        </div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {pill('signoff', status.signoff)}
          {pill('req', status.req)}
          {pill('ssot', status.ssot)}
          {pill('fl', status.fl_model)}
          {pill('decomp', status.fl_decomp)}
          {pill('fcov plan', status.fcov_plan)}
          {pill('equiv', status.equivalence_goals)}
          {pill('audit', status.goal_audit)}
          {pill('rtl', status.rtl)}
          {pill('lint', status.lint)}
          {pill('tb', status.tb)}
          {pill('simdbg', status.sim_debug || status.sim)}
          {pill('cov', status.coverage)}
        </div>
        <div className="mute" style={{ marginTop: 6, fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.4 }}>
          strict gate: REQ + SSOT + executable FL model + decomposition + FCOV plan + RTL + lint + FL-vs-RTL sim + coverage + goal audit
        </div>
        {blockers.length > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>
            blocked by: {blockers.slice(0, 4).join(' · ')}
          </div>
        )}
        <div style={{ marginTop: 8, display: 'flex', gap: 6, alignItems: 'center' }}>
          <button
            onClick={repairRtl}
            disabled={!selected || !selected.id}
            title="Queue rtl-gen repair from current compile/lint/SSOT evidence"
            style={{
              background: 'var(--bg-3)',
              color: 'var(--accent)',
              border: '1px solid var(--accent)',
              borderRadius: 2,
              padding: '3px 7px',
              fontFamily: 'var(--mono)',
              fontSize: 10,
              cursor: 'pointer',
            }}
          >
            repair rtl-gen
          </button>
          <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            uses SSOT + rtl_compile.json + dut_lint.json
          </span>
        </div>
      </div>

      <Section title="Artifact Evidence" right="not signoff">
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
          {pill('req', artifact.req)}
          {pill('ssot', artifact.ssot)}
          {pill('fl', artifact.fl_model)}
          {pill('decomp', artifact.fl_decomp)}
          {pill('fcov plan', artifact.fcov_plan)}
          {pill('equiv', artifact.equivalence_goals)}
          {pill('audit', artifact.goal_audit)}
          {pill('rtl', artifact.rtl)}
          {pill('tb', artifact.tb)}
          {pill('simdbg', artifact.sim_debug)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '62px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">req</span><span className="trunc" title={artifactDetails.req || ''}>{artifactDetails.req || 'no requirement evidence'}</span>
          <span className="mute">ssot</span><span className="trunc" title={artifactDetails.ssot || ''}>{artifactDetails.ssot || 'no artifact evidence'}</span>
          <span className="mute">fl</span><span className="trunc" title={artifactDetails.fl_model || ''}>{artifactDetails.fl_model || 'no executable FL model'}</span>
          <span className="mute">decomp</span><span className="trunc" title={artifactDetails.fl_decomp || ''}>{artifactDetails.fl_decomp || 'no FL decomposition'}</span>
          <span className="mute">fcov</span><span className="trunc" title={artifactDetails.fcov_plan || ''}>{artifactDetails.fcov_plan || 'no FCOV plan'}</span>
          <span className="mute">equiv</span><span className="trunc" title={artifactDetails.equivalence_goals || ''}>{artifactDetails.equivalence_goals || 'no equivalence goals'}</span>
          <span className="mute">audit</span><span className="trunc" title={artifactDetails.goal_audit || ''}>{artifactDetails.goal_audit || 'no goal audit'}</span>
          <span className="mute">rtl</span><span className="trunc" title={artifactDetails.rtl || ''}>{artifactDetails.rtl || 'no artifact evidence'}</span>
          <span className="mute">tb</span><span className="trunc" title={artifactDetails.tb || ''}>{artifactDetails.tb || 'no artifact evidence'}</span>
          <span className="mute">simdbg</span><span className="trunc" title={artifactDetails.sim_debug || ''}>{artifactDetails.sim_debug || 'no artifact evidence'}</span>
        </div>
      </Section>

      <Section title="Loop Owner & Next Action" right="LLM loop / human gate">
        {ownershipRows.length ? (
          <div style={{ display: 'grid', gridTemplateColumns: '58px 68px 1fr', rowGap: 5, columnGap: 8, fontFamily: 'var(--mono)', fontSize: 10 }}>
            {ownershipRows.map(row => (
              <React.Fragment key={row.stage}>
                <span className="mute">{String(row.stage || '').replace('_', ' ')}</span>
                <span style={{ color: row.owner === 'human gate' ? 'var(--warn)' : stateColor(row.status) }}>
                  {row.owner || 'LLM loop'}
                </span>
                <span
                  className="trunc"
                  title={[
                    `status: ${row.status || 'pending'}`,
                    `validator: ${row.validator || ''}`,
                    `evidence: ${row.evidence || ''}`,
                    `blocker: ${row.blocker || ''}`,
                    `next: ${row.next_action || ''}`,
                  ].join('\n')}
                >
                  {row.next_action || 'inspect stage evidence'}
                </span>
              </React.Fragment>
            ))}
          </div>
        ) : (
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            ownership data missing from ATLAS progress response
          </div>
        )}
      </Section>

      <Section title="SSOT Sections" right={selected.ssot_path}>
        <Bar label="approved sections" done={ssot.approved || 0} total={ssot.total || 0} value={pct(ssot)} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {sections.map(s => (
            <div key={s.key} title={s.key} style={{
              display: 'flex', alignItems: 'center', gap: 5, minWidth: 0,
              color: s.status === 'approved' ? 'var(--fg)' : 'var(--fg-mute)',
              fontFamily: 'var(--mono)', fontSize: 10,
            }}>
              <span style={{ color: stateColor(s.status), width: 10 }}>{s.status === 'approved' ? '✓' : '○'}</span>
              <span className="trunc">{s.label || s.key}</span>
            </div>
          ))}
        </div>
        {ssot.metrics && (
          <div className="mute" style={{ marginTop: 8, lineHeight: 1.5, fontFamily: 'var(--mono)' }}>
            submods {ssot.metrics.submodules || 0} · ports {ssot.metrics.ports || 0} · regs {ssot.metrics.registers || 0} · scenarios {ssot.metrics.dv_scenarios || 0}
          </div>
        )}
      </Section>

      <Section title="FL Model & Coverage Plan" right={flModel.source || details.fl_model}>
        <div style={{ display: 'grid', gridTemplateColumns: '86px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">req</span><span style={{ color: stateColor(req.status) }}>{req.status || 'pending'} · {(req.files || []).length || 0} file(s)</span>
          <span className="mute">model</span><span style={{ color: stateColor(flModel.status) }}>{flModel.status || 'pending'} · {flModel.bytes || 0}B</span>
          <span className="mute">self-check</span><span style={{ color: flModel.self_check && flModel.self_check.passed ? 'var(--ok)' : 'var(--fg-mute)' }}>{flModel.self_check && flModel.self_check.passed ? 'pass' : 'missing'}</span>
          <span className="mute">decomp</span><span style={{ color: stateColor(flDecomp.status) }}>{flDecomp.status || 'pending'} · {flDecomp.units || 0} unit(s)</span>
          <span className="mute">fcov plan</span><span style={{ color: stateColor(fcovPlan.status) }}>{fcovPlan.status || 'pending'} · {fcovPlan.bins || 0} bin(s)</span>
          <span className="mute">equiv</span><span style={{ color: stateColor(equiv.status) }}>{equiv.status || 'pending'} · {equiv.passed || 0}/{equiv.total || 0} pass · {equiv.blocked || 0} blocked · {equiv.untested || 0} untested</span>
        </div>
        {Array.isArray(flDecomp.kinds) && flDecomp.kinds.length > 0 && (
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            model slices: {flDecomp.kinds.join(', ')}
          </div>
        )}
        {fcovPlan.summary && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            bins: scenario {fcovPlan.summary.scenario_bins || 0} · transaction {fcovPlan.summary.transaction_bins || 0} · protocol {fcovPlan.summary.protocol_bins || 0} · state {fcovPlan.summary.state_transition_bins || 0} · error {fcovPlan.summary.error_bins || 0}
          </div>
        )}
        <div style={{ marginTop: 8 }}>
          <Bar
            label="equivalence goals"
            done={equiv.passed || 0}
            total={equiv.total || 0}
            color={stateColor(equiv.status)}
          />
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.45 }}>
            checked {equiv.checked || 0} · failed {equiv.failed || 0} · classifications {equiv.classifications || 0}
            {equiv.compare_evidence ? ` · ${equiv.compare_evidence}` : (equiv.evidence ? ` · ${equiv.evidence}` : '')}
          </div>
          {equiv.classification_counts && Object.keys(equiv.classification_counts).length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              class: {Object.entries(equiv.classification_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
            </div>
          )}
          {equiv.owner_counts && Object.keys(equiv.owner_counts).length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              owner: {Object.entries(equiv.owner_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
            </div>
          )}
          {Array.isArray(equiv.missing_evidence) && equiv.missing_evidence.length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              missing: {equiv.missing_evidence.slice(0, 3).join(', ')}
            </div>
          )}
          {Array.isArray(equiv.stale_evidence) && equiv.stale_evidence.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              stale: {equiv.stale_evidence.slice(0, 3).join(', ')}
            </div>
          )}
          {Array.isArray(equiv.failed_goal_ids) && equiv.failed_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              failed: {equiv.failed_goal_ids.join(', ')}
            </div>
          )}
          {Array.isArray(equiv.blocked_goal_ids) && equiv.blocked_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              blocked: {equiv.blocked_goal_ids.join(', ')}
            </div>
          )}
          {Array.isArray(equiv.untested_goal_ids) && equiv.untested_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              untested: {equiv.untested_goal_ids.join(', ')}
            </div>
          )}
          <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '86px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', fontSize: 10 }}>
            <span className="mute">goal audit</span>
            <span style={{ color: stateColor(goalAudit.status) }}>
              {goalAudit.status || 'pending'} · {goalAudit.passed_checks || 0}/{goalAudit.total_checks || 0} checks · {goalAudit.failed_checks || 0} failed
            </span>
            <span className="mute">evidence</span>
            <span className="trunc" title={goalAudit.source || ''}>{goalAudit.source || 'run /goal-audit <ip>'}</span>
          </div>
          {Array.isArray(goalAudit.blockers) && goalAudit.blockers.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              audit blockers: {goalAudit.blockers.slice(0, 8).join(', ')}
            </div>
          )}
          {Array.isArray(goalAudit.stale_evidence) && goalAudit.stale_evidence.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              audit stale: {goalAudit.stale_evidence.slice(0, 3).join(', ')}
            </div>
          )}
        </div>
      </Section>

      <Section title="RTL Modules" right={rtl.filelist || details.rtl}>
        <Bar label="approved RTL files" done={rtl.approved || 0} total={rtl.total || 0} value={pct(rtl)} color="var(--accent)" />
        {rtlModules.length ? rtlModules.map(m => (
          <div key={m.file || m.name} style={{
            display: 'grid', gridTemplateColumns: '14px 1fr auto', gap: 6,
            alignItems: 'baseline', padding: '3px 0', fontFamily: 'var(--mono)', fontSize: 10,
          }}>
            <span style={{ color: stateColor(m.status) }}>{m.status === 'approved' ? '✓' : m.status === 'partial' ? '◐' : '○'}</span>
            <span className="trunc" title={m.resolved_file && m.resolved_file !== m.file ? `${m.file} -> ${m.resolved_file}` : m.file}>
              {m.name || m.file}
              {m.manifest_mismatch ? <span style={{ color: 'var(--warn)' }}> · manifest</span> : null}
            </span>
            <span className="mute">{m.listed ? 'listed' : 'unlisted'} · {m.bytes || 0}B</span>
          </div>
        )) : <div className="mute">No expected RTL modules found in SSOT/filelist yet.</div>}
        {(rtl.manifest_mismatches || 0) > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
            SSOT/RTL manifest mismatch: {rtl.manifest_mismatches}
          </div>
        )}
      </Section>

      <Section title="Compile Gate" right={compile.source || ''}>
        <div style={{ display: 'grid', gridTemplateColumns: '82px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">status</span><span style={{ color: stateColor(compile.status) }}>{compile.status || 'unknown'}</span>
          <span className="mute">errors</span><span style={{ color: (compile.errors || 0) ? 'var(--err)' : 'var(--ok)' }}>{compile.errors ?? 0}</span>
          <span className="mute">diagnostics</span><span style={{ color: (compile.diagnostics || 0) ? 'var(--warn)' : 'var(--ok)' }}>{compile.diagnostics ?? 0}</span>
          <span className="mute">style</span><span style={{ color: (compile.style_violations || 0) ? 'var(--warn)' : 'var(--ok)' }}>{compile.style_violations ?? 0}</span>
        </div>
        {Array.isArray(compile.style_violation_details) && compile.style_violation_details.slice(0, 4).map((v, idx) => (
          <div key={idx} className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>
            <span style={{ color: 'var(--warn)' }}>{v.file}:{v.line}</span> {v.rule}
          </div>
        ))}
      </Section>

      <Section title="Lint Gate" right={lint.source || ''}>
        <div style={{ display: 'grid', gridTemplateColumns: '70px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">status</span><span style={{ color: stateColor(lint.status) }}>{lint.status || 'unknown'}</span>
          <span className="mute">errors</span><span style={{ color: (lint.errors || 0) ? 'var(--err)' : 'var(--ok)' }}>{lint.errors ?? 0}</span>
          <span className="mute">warnings</span><span style={{ color: (lint.warnings || 0) > (lint.warning_budget || 0) ? 'var(--warn)' : 'var(--ok)' }}>{lint.warnings ?? 0} / budget {lint.warning_budget || 0}</span>
        </div>
      </Section>

      <Section title="Simulation & DV Plan" right={(results.sources || []).join(', ')}>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">scenarios</span><span>{dv.scenarios || 0}</span>
          <span className="mute">scoreboard</span><span>{dv.scoreboard_checks ?? 'derive from SSOT'}</span>
          <span className="mute">tests</span><span>{results.pass || 0} pass / {results.fail || 0} fail / {results.total || 0} total</span>
          <span className="mute">checks</span><span>{results.check_pass ?? 0} pass / {results.check_fail ?? 0} fail / {results.check_total ?? 0} total</span>
        </div>
        {scenarios.slice(0, 12).map(sc => (
          <div key={sc.id || sc.name} style={{
            display: 'grid', gridTemplateColumns: '42px 1fr 70px', gap: 6,
            fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0',
          }}>
            <span className="mute">{sc.id || '-'}</span>
            <span className="trunc" title={sc.expected || sc.name}>{sc.name || sc.expected || 'scenario'}</span>
            <span style={{ color: stateColor(sc.status), textAlign: 'right' }}>{sc.status || 'pending'}</span>
          </div>
        ))}
      </Section>

      <Section title="Coverage Criteria" right={coverage.status || 'unknown'}>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">functional</span><span style={{ color: coverage.functional_pct == null ? 'var(--fg-mute)' : 'var(--ok)' }}>{coverage.functional_pct == null ? 'unknown' : coverage.functional_pct + '%'}</span>
          <span className="mute">goals</span><span>{Object.keys(criteria).length}</span>
          <span className="mute">limits</span><span style={{ color: Object.keys(limitations).length ? 'var(--warn)' : 'var(--fg-mute)' }}>{Object.keys(limitations).length || 0}</span>
        </div>
        {Object.entries(criteria).slice(0, 6).map(([k, v]) => (
          <div key={k} className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0' }}>
            <span style={{ color: 'var(--fg)' }}>{k}</span>: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
          </div>
        ))}
        {Object.entries(staticCov).slice(0, 4).map(([k, v]) => (
          <div key={k} className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0' }}>
            static {k}: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
          </div>
        ))}
        {Object.keys(limitations).length > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
            coverage capability gap: {Object.keys(limitations).join(', ')}
          </div>
        )}
      </Section>
    </div>
  );
};

const TodoPanel = () => {
  const [view, setView] = React.useState('compact'); // compact | detail | graph
  const [openId, setOpenId] = React.useState(null);
  // Per-group collapse state in compact view: {approved: true, ...}
  // means that group is collapsed. Defaults set via collapsedDefault
  // inside the render so they're not duplicated.
  const [collapsedTodoGroups, setCollapsedTodoGroups] = React.useState({});
  const todos = window.TODOS;
  // "Done" counter spans every terminal state (done/approved/completed)
  // — without this, the counter showed 0/7 for tasks the agent had
  // explicitly approved because raw 'approved' status now flows
  // through unchanged from data.jsx.
  const done = todos.filter(t => ['done', 'approved', 'completed'].includes(t.state)).length;

  // Map every status to a glyph + color so the right panel reads at a
  // glance. data.jsx normalizes TodoTracker statuses
  // (pending/in_progress/completed/approved/rejected) into the simpler
  // pending/active/done used by this UI; the renderer below also keeps
  // explicit cases for the raw statuses so live updates render right.
  const stateCfg = (s) => {
    const meta = atlasStatusMeta(s);
    switch (s) {
      // Auto-finished by the agent (no explicit human nod)
      case 'done':        return { glyph: meta.glyph, color: meta.color, label: meta.label };
      case 'completed':   return { glyph: meta.glyph, color: meta.color, label: meta.label };
      // Explicitly approved by a human — distinct glyph + accent
      // colour so the pending/approved distinction reads at a glance
      case 'approved':    return { glyph: meta.glyph, color: meta.color, label: meta.label };
      case 'active':      return { glyph: meta.glyph, color: meta.color, label: 'in-progress' };
      case 'in_progress': return { glyph: meta.glyph, color: meta.color, label: meta.label };
      case 'rejected':    return { glyph: meta.glyph, color: meta.color, label: meta.label };
      // Hollow square + warm warn-yellow so it never reads as "done"
      case 'pending':     return { glyph: meta.glyph, color: meta.color, label: meta.label };
      default:            return { glyph: '☐', color: 'var(--fg-mute)', label: s || '?' };
    }
  };

  const todoLines = (value, { splitCommas = false } = {}) => {
    if (Array.isArray(value)) {
      return value.flatMap(v => todoLines(v, { splitCommas }));
    }
    if (value && typeof value === 'object') {
      return Object.entries(value).flatMap(([k, v]) => {
        const vv = String(v ?? '').trim();
        return vv ? [`${k}: ${vv}`] : [String(k)];
      }).filter(Boolean);
    }
    const raw = String(value ?? '').trim();
    if (!raw) return [];
    const prepared = raw.replace(/\s+(Each\s+TODO\s+gets:)/gi, '\n$1');
    return prepared
      .split(/\r?\n+/)
      .map(line => line.trim())
      .filter(Boolean)
      .flatMap((line) => {
        const clean = line.replace(/^[-*•]\s*/, '').trim();
        if (!clean) return [];
        if (!splitCommas) return [clean];
        const m = clean.match(/^([^:]{2,48}):\s*(.+)$/);
        if (m) return [clean];
        const items = clean.split(/\s*,\s*/).map(s => s.trim()).filter(Boolean);
        if (items.length >= 4 && clean.length > 120) return items;
        return [clean];
      });
  };

  const todoDetailBlocks = (detail) => {
    const blocks = [];
    todoLines(detail, { splitCommas: false }).forEach((line) => {
      const parts = line.length > 180
        ? line.split(/(?<=\.)\s+|;\s+/).map(s => s.trim()).filter(Boolean)
        : [line];
      parts.forEach((part) => {
        const listMatch = part.match(/^([^:]{2,48}):\s*(.+)$/);
        if (listMatch && listMatch[2].includes(',')) {
          const items = listMatch[2].split(/\s*,\s*/).map(s => s.trim()).filter(Boolean);
          if (items.length >= 3) {
            blocks.push({ type: 'list', label: listMatch[1], items });
            return;
          }
        }
        blocks.push({ type: 'text', text: part });
      });
    });
    return blocks;
  };

  const TodoField = ({ label, children }) => (
    <div style={{ display: 'grid', gap: 3 }}>
      <div style={{
        color: 'var(--cyan)',
        fontSize: 10,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        fontWeight: 700,
      }}>{label}</div>
      <div style={{ color: 'var(--fg-dim)', lineHeight: 1.62 }}>{children}</div>
    </div>
  );

  const TodoBulletList = ({ items }) => (
    <div style={{ display: 'grid', gap: 2 }}>
      {items.map((item, idx) => (
        <div key={`${item}-${idx}`} style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
          <span className="mute" style={{ lineHeight: 1.6 }}>•</span>
          <span style={{ flex: 1 }}>{item}</span>
        </div>
      ))}
    </div>
  );

  const TodoStructuredBody = ({ todo }) => {
    const detail = todoDetailBlocks(todo.detail);
    const criteria = todoLines(todo.criteria, { splitCommas: true });
    const sourceRefs = todoLines(todo.sourceRefs, { splitCommas: true });
    const owner = [String(todo.ownerModule || '').trim(), String(todo.ownerFile || '').trim()].filter(Boolean);
    const required = typeof todo.required === 'boolean'
      ? (todo.required ? 'yes' : 'no')
      : (todo.required == null ? '' : String(todo.required).trim());
    return (
      <div style={{ display: 'grid', gap: 8, overflowWrap: 'anywhere' }}>
        {detail.length > 0 && (
          <TodoField label="Detail">
            <div style={{ display: 'grid', gap: 4 }}>
              {detail.map((blk, idx) => (
                blk.type === 'list' ? (
                  <div key={`dlist-${idx}`} style={{ display: 'grid', gap: 3 }}>
                    <span style={{ color: 'var(--fg)' }}>{blk.label}</span>
                    <TodoBulletList items={blk.items} />
                  </div>
                ) : (
                  <div key={`dtext-${idx}`}>{blk.text}</div>
                )
              ))}
            </div>
          </TodoField>
        )}
        {criteria.length > 0 && (
          <TodoField label="Criteria">
            <TodoBulletList items={criteria} />
          </TodoField>
        )}
        {sourceRefs.length > 0 && (
          <TodoField label="Source Refs">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {sourceRefs.map((ref, idx) => (
                <span key={`src-${idx}`} style={{
                  border: '1px solid var(--line)',
                  borderRadius: 2,
                  padding: '1px 6px',
                  color: 'var(--fg)',
                }}>{ref}</span>
              ))}
            </div>
          </TodoField>
        )}
        {owner.length > 0 && (
          <TodoField label="Owner">{owner.join(' · ')}</TodoField>
        )}
        {required && (
          <TodoField label="Required">{required}</TodoField>
        )}
      </div>
    );
  };

  const TodoReason = ({ todo }) => {
    const approved = todo.state === 'approved' || todo.state === 'done';
    const rejected = todo.state === 'rejected';
    const reason = approved ? todo.approvedReason : rejected ? todo.rejectionReason : '';
    if (!reason) return null;
    const label = approved ? 'Approved' : 'Rejected';
    const color = approved ? 'var(--ok)' : 'var(--err)';
    return (
      <div style={{
        marginTop: 5,
        fontFamily: 'var(--mono)',
        fontSize: 'var(--ui-font-size)',
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>
        <span style={{ color, fontWeight: 700 }}>{label}</span>
        <span className="mute"> : </span>
        <span style={{ color: 'var(--fg-dim)' }}>{_limitAtlasLines(reason, 5)}</span>
      </div>
    );
  };

  const TodoNotes = ({ todo }) => {
    const notes = Array.isArray(todo.notes) ? todo.notes.filter(n => String(n || '').trim()) : [];
    if (!notes.length) return null;
    const lastIndex = notes.length;
    const last = String(notes[notes.length - 1] || '');
    return (
      <div style={{
        marginTop: 5,
        fontFamily: 'var(--mono)',
        fontSize: 'var(--ui-font-size)',
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>
        <span style={{ color: 'var(--cyan)', fontWeight: 700 }}>Notes</span>
        <span className="mute"> : </span>
        <span style={{ color: 'var(--fg-dim)' }}>[{lastIndex}] {_limitAtlasLines(last, 5)}</span>
        {notes.length > 1 && (
          <span className="mute" style={{ marginLeft: 6 }}>+{notes.length - 1} earlier</span>
        )}
      </div>
    );
  };

  // Counts per state for the header summary
  const counts = todos.reduce((acc, t) => {
    const cfg = stateCfg(t.state);
    acc[cfg.label] = (acc[cfg.label] || 0) + 1;
    return acc;
  }, {});

  // ── header tab strip
  const Tab = ({ id, label }) => (
    <span onClick={() => setView(id)} style={{
      cursor: 'pointer', padding: '4px 10px', fontSize: 10, letterSpacing: '0.06em',
      textTransform: 'uppercase', fontFamily: 'var(--mono)',
      color: view === id ? 'var(--fg)' : 'var(--fg-mute)',
      background: view === id ? 'var(--bg-2)' : 'transparent',
      border: `1px solid ${view === id ? 'var(--accent)' : 'var(--line)'}`,
      borderRadius: 2,
    }}>{label}</span>
  );

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{
        padding: '8px 12px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, flexWrap: 'wrap',
      }}>
        <span className="mute" style={{ fontFamily: 'var(--mono)' }}>{done}/{todos.length}</span>
        {/* color-coded count chips per state */}
        {['in-progress','pending','done','approved','completed','rejected'].filter(k => counts[k]).map(k => {
          const c = stateCfg(k === 'done' ? 'done' : k.replace('-', '_'));
          return (
            <AtlasStatusBadge key={k} status={k} label={c.label} count={counts[k]} compact soft />
          );
        })}
        <span style={{ flex: 1 }} />
        <span title="Clear all todos"
          onClick={() => { if (confirm('Clear all todos?')) window.atlasData.clearTodos(); }}
          style={{
            cursor: 'pointer', fontSize: 10, padding: '2px 8px',
            border: '1px solid var(--line)', color: 'var(--fg-mute)',
            borderRadius: 2,
          }}>✕ clear</span>
        <span className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>view</span>
        <Tab id="compact" label="list" />
        <Tab id="detail" label="detail" />
        <Tab id="graph" label="graph" />
      </div>

      {/* Progress bar — at-a-glance "X / Y approved" with green fill */}
      {todos.length > 0 && (
        <div style={{ padding: '6px 12px 4px', borderBottom: '1px solid var(--line)',
                       background: 'var(--bg-2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
                         fontSize: 10, fontFamily: 'var(--mono)',
                         color: 'var(--fg-mute)', marginBottom: 3 }}>
            <span>progress</span>
            <span><b style={{ color: 'var(--ok)' }}>{done}</b> / {todos.length} approved</span>
          </div>
          <div style={{ height: 4, background: 'var(--bg-3)',
                         border: '1px solid var(--line)', borderRadius: 2,
                         overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${todos.length ? Math.round(100 * done / todos.length) : 0}%`,
              background: '#3fb950',
              transition: 'width 240ms ease-out',
            }} />
          </div>
        </div>
      )}

      <div style={{ flex: 1, overflow: 'auto' }}>
        {view === 'compact' && (() => {
          // Group by status order: in_progress → pending → completed →
          // rejected → approved (approved collapsed by default since it's
          // usually the long tail of "done" todos that the user no longer
          // needs to scan).
          const groupOf = (t) => {
            const s = t.state;
            if (s === 'active' || s === 'in_progress') return 'in_progress';
            if (s === 'completed') return 'completed';
            if (s === 'approved' || s === 'done') return 'approved';
            if (s === 'rejected') return 'rejected';
            return 'pending';
          };
          const groups = { in_progress: [], pending: [], completed: [], rejected: [], approved: [] };
          todos.forEach(t => groups[groupOf(t)].push(t));
          const order = ['in_progress', 'pending', 'completed', 'rejected', 'approved'];
          const labels = {
            in_progress: 'IN PROGRESS', pending: 'PENDING',
            completed: 'COMPLETED',     rejected: 'REJECTED', approved: 'APPROVED',
          };
          // approved + rejected default-collapsed; in-progress/pending/completed default-open
          const collapsedDefault = { approved: true, rejected: true };
          const isCollapsed = (g) => collapsedTodoGroups[g] !== undefined
            ? collapsedTodoGroups[g] : (collapsedDefault[g] || false);
          const toggleGroup = (g) => setCollapsedTodoGroups(prev =>
            ({ ...prev, [g]: !isCollapsed(g) }));
          return (
            <div style={{ padding: '4px 0' }}>
              {order.map(g => {
                const items = groups[g];
                if (!items.length) return null;
                const collapsed = isCollapsed(g);
                const cfg = stateCfg(g === 'in_progress' ? 'in_progress' : g);
                return (
                  <div key={g}>
                    {/* Group divider — uppercase label, click to toggle */}
                    <div
                      onClick={() => toggleGroup(g)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '4px 12px 2px', cursor: 'pointer',
                        fontFamily: 'var(--mono)', fontSize: 10,
                        letterSpacing: '0.1em', textTransform: 'uppercase',
                        color: cfg.color, userSelect: 'none',
                      }}
                    >
                      <span>{collapsed ? '▸' : '▾'}</span>
                      <AtlasStatusBadge status={g} label={labels[g]} count={items.length} compact />
                      <span style={{ flex: 1, height: 1, background: 'var(--line)',
                                      opacity: 0.5, marginLeft: 6 }} />
                    </div>
                    {!collapsed && items.map(t => {
                      const open = openId === t.id;
                      return (
                        <div key={t.id}>
                          <div
                            onClick={() => setOpenId(open ? null : t.id)}
                            style={{
                              display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 16px',
                              alignItems: 'baseline', gap: 8, padding: '6px 12px',
                              cursor: 'pointer', fontFamily: 'var(--mono)', fontSize: 13,
                              background: t.state === 'active' || t.state === 'in_progress'
                                ? 'color-mix(in oklch, var(--accent) 8%, transparent)'
                                : 'transparent',
                              borderLeft: (t.state === 'active' || t.state === 'in_progress')
                                ? '2px solid var(--accent)' : '2px solid transparent',
                            }}
                          >
                            <span style={{ color: t.state === 'pending' ? 'var(--fg-dim)' : 'var(--fg)' }}>{t.title}</span>
                            <span className="mute" style={{ fontSize: 10 }}>{open ? '▾' : '▸'}</span>
                          </div>
                          {open && (
                            <div className="fade-in" style={{
                              padding: '10px 14px 12px 64px',
                              fontSize: 13,
                              lineHeight: 1.68,
                              color: 'var(--fg-dim)',
                              borderLeft: '2px solid var(--line-2)',
                              borderTop: '1px solid var(--line)',
                              marginLeft: 12,
                              marginRight: 12,
                              background: 'color-mix(in oklch, var(--bg-2) 92%, var(--fg) 8%)',
                            }}>
                              <TodoStructuredBody todo={t} />
                              <TodoNotes todo={t} />
                              <TodoReason todo={t} />
                              {t.deps && t.deps.length > 0 && (
                                <div style={{ marginTop: 6, fontSize: 11, lineHeight: 1.5 }}>
                                  <span className="mute">deps:</span>{' '}
                                  {t.deps.map(d => <span key={d} className="acc">§{d} </span>)}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          );
        })()}

        {view === 'detail' && (
          <div>
            {todos.map(t => {
              const cfg = stateCfg(t.state);
              return (
                <div key={t.id} style={{
                  padding: '10px 14px', borderBottom: '1px solid var(--line)',
                  background: t.state === 'active' ? 'var(--bg-2)' : 'transparent',
                  borderLeft: t.state === 'active' ? '2px solid var(--accent)' : '2px solid transparent',
                }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <AtlasStatusBadge status={t.state} label={cfg.label} compact soft />
                    <span className="mute" style={{ fontSize: 11 }}>{t.section}</span>
                    <span style={{ fontWeight: t.state === 'active' ? 600 : 500, flex: 1, fontSize: 13, color: 'var(--fg)' }}>{t.title}</span>
                  </div>
                  <div style={{
                    color: 'var(--fg-dim)',
                    fontSize: 13,
                    marginTop: 6,
                    marginLeft: 22,
                    lineHeight: 1.62,
                  }}>
                    <TodoStructuredBody todo={t} />
                  </div>
                  <div style={{ marginLeft: 22 }}>
                    <TodoNotes todo={t} />
                    <TodoReason todo={t} />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {view === 'graph' && <TodoGraph todos={todos} openId={openId} setOpenId={setOpenId} />}
      </div>
    </div>
  );
};

// ── Graph view: SVG DAG laid out by topological level ─────────────
const TodoGraph = ({ todos, openId, setOpenId }) => {
  // assign each node a level = max(level of deps) + 1
  const levelOf = {};
  todos.forEach(t => {
    levelOf[t.id] = (t.deps || []).reduce((m, d) => Math.max(m, (levelOf[d] ?? 0) + 1), 0);
  });
  const levels = {};
  todos.forEach(t => { (levels[levelOf[t.id]] = levels[levelOf[t.id]] || []).push(t); });
  const levelKeys = Object.keys(levels).map(Number).sort((a, b) => a - b);

  const W = 320, NODE_W = 80, NODE_H = 32, gapY = 10, gapX = 22, padX = 10, padY = 10;
  const colW = NODE_W + gapX;
  const totalW = padX * 2 + colW * levelKeys.length - gapX;
  const maxRow = Math.max(...levelKeys.map(k => levels[k].length));
  const totalH = padY * 2 + maxRow * (NODE_H + gapY) - gapY;

  const pos = {};
  levelKeys.forEach((lvl, ci) => {
    const col = levels[lvl];
    const colH = col.length * (NODE_H + gapY) - gapY;
    const yStart = padY + (totalH - padY * 2 - colH) / 2;
    col.forEach((t, ri) => {
      pos[t.id] = {
        x: padX + ci * colW,
        y: yStart + ri * (NODE_H + gapY),
      };
    });
  });

  const stateCfg = (s) => {
    const meta = atlasStatusMeta(s);
    const activeish = ['active', 'in_progress', 'running'].includes(normalizeAtlasStatus(s));
    const doneish = ['done', 'completed', 'approved'].includes(normalizeAtlasStatus(s));
    const errish = ['rejected', 'error', 'blocked'].includes(normalizeAtlasStatus(s));
    return {
      fill: activeish || doneish || errish ? `color-mix(in oklch, ${meta.color} 14%, transparent)` : 'transparent',
      stroke: activeish || doneish || errish ? meta.color : 'var(--line)',
      glyph: meta.glyph,
      color: meta.color,
    };
  };

  return (
    <div style={{ padding: 12 }}>
      <div className="mute" style={{ fontSize: 10, marginBottom: 8, fontFamily: 'var(--mono)' }}>
        ── DAG · {levelKeys.length} levels · click a node · ↔ scroll
      </div>
      <div style={{ overflowX: 'auto', overflowY: 'hidden', border: '1px solid var(--line)', borderRadius: 2, background: 'var(--bg-2)' }}>
      <svg width={totalW} height={totalH} style={{ display: 'block' }}>
        {/* edges */}
        <defs>
          <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--fg-mute)" />
          </marker>
        </defs>
        {todos.flatMap(t => (t.deps || []).map(d => {
          const a = pos[d], b = pos[t.id];
          if (!a || !b) return null;
          const x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2;
          const x2 = b.x,           y2 = b.y + NODE_H / 2;
          const mx = (x1 + x2) / 2;
          return (
            <path key={`${d}->${t.id}`}
              d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
              fill="none" stroke="var(--line)" strokeWidth="1"
              markerEnd="url(#arr)"
            />
          );
        }))}
        {/* nodes */}
        {todos.map(t => {
          const p = pos[t.id], cfg = stateCfg(t.state);
          const sel = openId === t.id;
          return (
            <g key={t.id}
              onClick={() => setOpenId(sel ? null : t.id)}
              style={{ cursor: 'pointer' }}
            >
              <rect x={p.x} y={p.y} width={NODE_W} height={NODE_H} rx="2"
                fill={cfg.fill} stroke={sel ? 'var(--fg)' : cfg.stroke}
                strokeWidth={sel ? 2 : 1}
              />
              <text x={p.x + 6} y={p.y + 12} fontSize="8" fill="var(--fg-mute)"
                fontFamily="var(--mono)" letterSpacing="0.04em">{t.section}</text>
              <text x={p.x + NODE_W - 6} y={p.y + 12} fontSize="9" textAnchor="end"
                fill={cfg.color} fontFamily="var(--mono)" fontWeight="700">{cfg.glyph}</text>
              <text x={p.x + 6} y={p.y + 24} fontSize="9" fill="var(--fg)"
                fontFamily="var(--mono)">
                {t.title.length > 11 ? t.title.slice(0, 10) + '…' : t.title}
              </text>
            </g>
          );
        })}
      </svg>
      </div>
      {openId && (
        <div className="fade-in" style={{
          marginTop: 12, padding: '8px 10px', borderLeft: '2px solid var(--accent)',
          background: 'var(--bg-2)', fontFamily: 'var(--mono)', fontSize: 11, lineHeight: 1.5,
        }}>
          {(() => {
            const t = todos.find(x => x.id === openId);
            if (!t) return null;
            const cfg = stateCfg(t.state);
            return (
              <>
                <div>
                  <span style={{ color: cfg.color, fontWeight: 700 }}>{cfg.glyph}</span>{' '}
                  <span className="mute">{t.section}</span>{' '}
                  <span style={{ color: 'var(--fg)' }}>{t.title}</span>
                </div>
                <div className="mute" style={{ marginTop: 4 }}>{t.detail}</div>
                <div style={{ marginTop: 4, fontSize: 10 }}>
                  <span className="mute">deps:</span>{' '}
                  {(t.deps && t.deps.length) ? t.deps.map(d => <span key={d} className="acc">§{d} </span>) : <span className="mute">(none)</span>}
                </div>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

// ── Git panel — branch / changes / diff / commit / push ──────────
// Hits /api/git/{status,diff,commit,push}. Read-only by default;
// commit + push require the user to fill the message and click the
// big buttons. Status mark mapping (XY from `git status --porcelain`):
//   M = modified   A = added   D = deleted   R = renamed
//   ? = untracked  !  = ignored (we don't show those)
const GIT_STATUS_GLYPH = {
  M: { ch: 'M', color: '#d29922' },   // yellow
  A: { ch: 'A', color: '#3fb950' },   // green
  D: { ch: 'D', color: '#f85149' },   // red
  R: { ch: 'R', color: '#a371f7' },   // purple
  '?': { ch: '?', color: 'var(--fg-mute)' },
  ' ': { ch: ' ', color: 'var(--fg-mute)' },
};
const _statusGlyph = (xy) => {
  const a = GIT_STATUS_GLYPH[xy[0]] || GIT_STATUS_GLYPH[' '];
  const b = GIT_STATUS_GLYPH[xy[1]] || GIT_STATUS_GLYPH[' '];
  return { staged: a, work: b };
};

// ============================================================
// OrchestratorChatPanel
//
// Per-IP rooms + the special "_global" room. Renders three stacked
// regions in the right sidebar:
//   1. Room switcher (only rooms the user can enter)
//   2. Collapsible "context card" — workflow / todos / gates / recent
//      events for the active room (the same JSON the running agent
//      receives on its next iteration via core/orchestrator_inject)
//   3. Message thread + composer
//
// Backend: src/atlas_api_chat.py. Live updates ride the existing
// WebSocket via window.backend.subscribe('chat_message', ...).
// ============================================================
const OrchestratorChatPanel = ({ activeIp: activeIpProp = '' } = {}) => {
  const [rooms, setRooms]       = React.useState([]);
  const [room, setRoom]         = React.useState('_global');
  const [messages, setMessages] = React.useState([]);
  const [context, setContext]   = React.useState(null);
  const [contextOpen, setContextOpen] = React.useState(true);
  const [draft, setDraft]       = React.useState('');
  const [busy, setBusy]         = React.useState(false);
  const [error, setError]       = React.useState('');
  const threadRef               = React.useRef(null);

  const fetchRooms = React.useCallback(async () => {
    try {
      const r = await fetch('/api/chat/rooms', { credentials: 'include' });
      if (!r.ok) { setError(`rooms: ${r.status}`); return; }
      const data = await r.json();
      setRooms(data.rooms || []);
    } catch (e) { setError(String(e)); }
  }, []);

  const fetchMessages = React.useCallback(async (rm) => {
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(rm)}/messages?limit=100`,
                            { credentials: 'include' });
      if (!r.ok) { setError(`messages: ${r.status}`); setMessages([]); return; }
      const data = await r.json();
      // API returns newest-first; reverse for chronological render.
      setMessages((data.messages || []).slice().reverse());
      setError('');
    } catch (e) { setError(String(e)); }
  }, []);

  const fetchContext = React.useCallback(async (rm) => {
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(rm)}/context`,
                            { credentials: 'include' });
      if (!r.ok) { setContext(null); return; }
      setContext(await r.json());
    } catch (_) { setContext(null); }
  }, []);

  // Initial + room-change loads.
  React.useEffect(() => { fetchRooms(); }, [fetchRooms]);
  React.useEffect(() => {
    fetchMessages(room);
    fetchContext(room);
  }, [room, fetchMessages, fetchContext]);

  // Default room: prefer the workspace's active IP, fall back to _global.
  React.useEffect(() => {
    if (!rooms.length) return;
    const names = new Set(rooms.map((r) => r.name));
    if (activeIpProp && names.has(activeIpProp)) { setRoom(activeIpProp); return; }
    if (names.has(room)) return;
    setRoom(names.has('_global') ? '_global' : rooms[0].name);
  }, [rooms, activeIpProp, room]);

  // Live updates over the existing WS bus.
  React.useEffect(() => {
    if (!window.backend || typeof window.backend.subscribe !== 'function') {
      return undefined;
    }
    const off = window.backend.subscribe('chat_message', (m) => {
      if (!m || m.room == null) return;
      if (m.room !== room) {
        // Could bump unread badge here; left to a follow-up.
        return;
      }
      setMessages((prev) => {
        // Dedup by id — broadcast_all fans out to every session, so the
        // sender's own client may see its own POST echo.
        if (prev.some((x) => x.id === m.id)) return prev;
        return prev.concat([{
          id: m.id,
          ip_id: m.ip_id,
          user_id: m.user_id,
          display_name: m.display_name,
          content: m.content,
          created_at: m.created_at,
        }]);
      });
    });
    return off;
  }, [room]);

  // Auto-scroll thread on new message.
  React.useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const submit = async () => {
    const text = draft.trim();
    if (!text || busy) return;
    setBusy(true);
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(room)}/send`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
      });
      if (!r.ok) {
        const body = await r.json().catch(() => ({}));
        setError(body.error || `POST ${r.status}`);
      } else {
        setDraft('');
        setError('');
      }
    } catch (e) { setError(String(e)); }
    finally { setBusy(false); }
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0,
                  padding: '8px 10px', gap: 8 }}>
      {/* Room switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 11, color: 'var(--fg-mute)' }}>Room:</span>
        <select
          value={room}
          onChange={(e) => setRoom(e.target.value)}
          style={{ flex: 1, fontSize: 12, padding: '2px 4px',
                   background: 'var(--bg-soft)', color: 'var(--fg)',
                   border: '1px solid var(--border)' }}>
          {rooms.length === 0 && <option value="">(no accessible rooms)</option>}
          {rooms.map((r) => (
            <option key={r.name} value={r.name}>
              {r.scope === 'global' ? 'all IPs (_global)' : r.name}
            </option>
          ))}
        </select>
        <button onClick={() => { fetchRooms(); fetchContext(room); fetchMessages(room); }}
                title="refresh"
                style={{ fontSize: 11, padding: '2px 6px' }}>⟳</button>
      </div>

      {/* Context card */}
      {context && (
        <div className="orchestrator-card"
             style={{ border: '1px solid var(--border)', borderRadius: 4,
                      padding: 6, fontSize: 11, background: 'var(--bg-soft)' }}>
          <div onClick={() => setContextOpen((v) => !v)}
               style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}>
            <strong>Orchestrator · {room}</strong>
            <span style={{ color: 'var(--fg-mute)' }}>{contextOpen ? '▾' : '▸'}</span>
          </div>
          {contextOpen && (
            <div style={{ marginTop: 6, lineHeight: 1.4 }}>
              {room === '_global' ? (
                <div>
                  <div style={{ color: 'var(--fg-mute)' }}>IPs in workspace:</div>
                  {(context.ips || []).map((ip) => (
                    <div key={ip.id || ip.name} style={{ marginLeft: 6 }}>
                      <code>{ip.name}</code>
                      {' · '}
                      <span>{ip.latest_workflow || '—'}/{ip.run_status || '—'}</span>
                      {' · open='}{ip.open_blockers}
                      {' · done='}{ip.completed}
                    </div>
                  ))}
                </div>
              ) : (
                <div>
                  <div>
                    <code>{(context.ip || {}).name}</code>
                    {' · '}
                    <span style={{ color: 'var(--fg-mute)' }}>
                      {(context.workflow || {}).latest_run
                        ? `${context.workflow.latest_run.workflow}/${context.workflow.latest_run.status}`
                        : 'no run yet'}
                    </span>
                  </div>
                  {(context.todos && context.todos.counts) && (
                    <div style={{ marginTop: 4 }}>
                      <span style={{ color: 'var(--fg-mute)' }}>todos:</span>{' '}
                      {Object.entries(context.todos.counts).map(([k, v]) => (
                        <span key={k} style={{ marginRight: 6 }}>{k}={v}</span>
                      ))}
                    </div>
                  )}
                  {(context.todos && context.todos.top_blockers || []).slice(0, 3).map((b) => (
                    <div key={b.id} style={{ marginLeft: 6, color: 'var(--warn)' }}>
                      blocker[{b.status}]: {b.title}
                    </div>
                  ))}
                  {(context.recent_events || []).slice(0, 4).map((e, i) => (
                    <div key={i} style={{ marginLeft: 6, color: 'var(--fg-mute)' }}>
                      {e.kind === 'llm'
                        ? `llm · ${e.model} · $${(e.cost_usd || 0).toFixed(3)}`
                        : `· ${e.event_type || e.kind}`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Message thread */}
      <div ref={threadRef}
           style={{ flex: 1, minHeight: 100, overflowY: 'auto',
                    border: '1px solid var(--border)', borderRadius: 4,
                    padding: 6, fontSize: 12, background: 'var(--bg-soft)' }}>
        {messages.length === 0 ? (
          <div style={{ color: 'var(--fg-mute)', fontStyle: 'italic' }}>
            No messages in this room yet. Posts are sent to the running agent on its next iteration.
          </div>
        ) : (
          messages.map((m) => {
            // Agent messages are identified by the 🤖 prefix in display_name
            // set by core/chat_responder.py. Same author would never start a
            // human message with that emoji (auth flow rejects display names
            // containing 🤖 — see record_chat_message). Visual cue: left-rail
            // accent + slightly different background so the thread reads as
            // a real conversation.
            const isAgent = typeof m.display_name === 'string'
              && m.display_name.startsWith('🤖');
            return (
              <div
                key={m.id}
                className={isAgent ? 'chat-bubble chat-bubble-agent' : 'chat-bubble'}
                style={{
                  marginBottom: 6,
                  padding: '4px 6px',
                  borderRadius: 4,
                  background: isAgent ? 'var(--bg-elevated, var(--bg))' : 'var(--bg)',
                  borderLeft: isAgent ? '3px solid var(--accent, #4a9eff)' : 'none',
                }}>
                <div style={{ display: 'flex', justifyContent: 'space-between',
                              fontSize: 10,
                              color: isAgent ? 'var(--accent, #4a9eff)' : 'var(--fg-mute)' }}>
                  <strong>{m.display_name || m.user_id || 'user'}</strong>
                  <span>{m.created_at ? new Date(m.created_at * 1000).toLocaleTimeString() : ''}</span>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {m.content}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Composer */}
      <div style={{ display: 'flex', gap: 4 }}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKey}
          rows={2}
          placeholder={
            rooms.length === 0
              ? 'No rooms available'
              : `Type feedback for ${room}…  (Enter to send, Shift+Enter newline)`
          }
          disabled={rooms.length === 0 || busy}
          style={{ flex: 1, fontSize: 12, padding: '4px 6px', resize: 'vertical',
                   background: 'var(--bg-soft)', color: 'var(--fg)',
                   border: '1px solid var(--border)' }}/>
        <button onClick={submit} disabled={busy || !draft.trim() || rooms.length === 0}
                style={{ fontSize: 12, padding: '4px 10px' }}>
          {busy ? '…' : 'Send'}
        </button>
      </div>

      {error && (
        <div style={{ fontSize: 10, color: 'var(--err)' }}>{error}</div>
      )}
    </div>
  );
};

const GitPanel = ({ activeIp: activeIpProp = '' } = {}) => {
  const [branch, setBranch] = React.useState('');
  const [ahead, setAhead]   = React.useState(0);
  const [behind, setBehind] = React.useState(0);
  const [files, setFiles]   = React.useState([]);
  const [commits, setCommits] = React.useState([]);
  const [error, setError]   = React.useState('');
  const [selected, setSelected] = React.useState(null);
  const [diff, setDiff]     = React.useState('');
  const [diffLoading, setDiffLoading] = React.useState(false);
  const [message, setMessage] = React.useState('');
  const [busy, setBusy]     = React.useState('');   // '' | 'commit' | 'push'
  const [lastResult, setLastResult] = React.useState(null);

  const [activeIp, setActiveIp] = React.useState(activeIpProp || '');

  React.useEffect(() => {
    setActiveIp(activeIpProp || '');
    setSelected(null);
    setDiff('');
  }, [activeIpProp]);

  const refresh = React.useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (activeIp) params.set('ip', activeIp);
      const qs = params.toString();
      const r = await fetch('/api/git/status' + (qs ? `?${qs}` : ''));
      const d = await r.json();
      setBranch(d.branch || ''); setAhead(d.ahead || 0); setBehind(d.behind || 0);
      setFiles(d.files || []); setError(d.error || '');
    } catch (e) { setError(String(e)); }
    try {
      const params = new URLSearchParams({ limit: '80' });
      if (activeIp) params.set('ip', activeIp);
      const r = await fetch('/api/git/log?' + params.toString());
      const d = await r.json();
      setCommits(Array.isArray(d.commits) ? d.commits : []);
    } catch (_) {}
  }, [activeIp]);

  React.useEffect(() => { refresh(); const id = setInterval(refresh, 5000); return () => clearInterval(id); }, [refresh]);

  // When user clicks a file, fetch its diff (cached as `selected`)
  React.useEffect(() => {
    if (!selected) { setDiff(''); return; }
    let cancelled = false;
    setDiffLoading(true);
    const params = new URLSearchParams({ path: selected });
    if (activeIp) params.set('ip', activeIp);
    fetch('/api/git/diff?' + params.toString())
      .then(r => r.json())
      .then(d => { if (!cancelled) { setDiff(d.diff || d.error || ''); setDiffLoading(false); } })
      .catch(e => { if (!cancelled) { setDiff(String(e)); setDiffLoading(false); } });
    return () => { cancelled = true; };
  }, [selected, files.length, activeIp]);

  const doCommit = async () => {
    if (!message.trim()) { alert('Commit message required.'); return; }
    setBusy('commit');
    try {
      const r = await fetch('/api/git/commit', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, add_all: true, ip: activeIp }),
      });
      const d = await r.json();
      setLastResult({ kind: 'commit', ...d });
      if (d.ok) setMessage('');
      refresh();
    } finally { setBusy(''); }
  };

  const doPush = async () => {
    if (!confirm('Push branch "' + (branch || '?') + '" to origin?')) return;
    setBusy('push');
    try {
      const r = await fetch('/api/git/push', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: activeIp }),
      });
      const d = await r.json();
      setLastResult({ kind: 'push', ...d });
      refresh();
    } finally { setBusy(''); }
  };

  const stagedCount   = files.filter(f => f.staged).length;
  const unstagedCount = files.filter(f => f.unstaged).length;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, fontSize: 12 }}>
      {/* Branch / ahead-behind / refresh */}
      <div style={{
        padding: '6px 10px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--mono)',
      }}>
        <span className="mute" style={{ fontSize: 10 }}>branch</span>
        <span className="acc" style={{ fontWeight: 600 }}>{branch || '(none)'}</span>
        {ahead  > 0 && <span className="ok"  style={{ fontSize: 10 }}>↑{ahead}</span>}
        {behind > 0 && <span className="warn" style={{ fontSize: 10 }}>↓{behind}</span>}
        <span style={{ flex: 1 }} />
        <span onClick={refresh} title="refresh git status"
              style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 13, padding: '0 6px' }}>↻</span>
      </div>

      {/* Commit history — clickable; emits atlas-git-show so the
          center pane can render the unified diff for the chosen
          commit (matches "branch / changes / commit msg + click =
          show diff in center" UX request). */}
      {commits.length ? (
        <div style={{
          borderBottom: '1px solid var(--line)',
          maxHeight: 220,
          overflow: 'auto',
          background: 'var(--bg-2)',
        }}>
          <div className="mute" style={{
            padding: '4px 10px', fontSize: 10,
            textTransform: 'uppercase', letterSpacing: '0.08em',
            borderBottom: '1px solid var(--line)',
          }}>history · {commits.length}</div>
          {commits.map(c => (
            <div
              key={c.sha}
              onClick={() => {
                window.dispatchEvent(new CustomEvent('atlas-git-show', {
                  detail: { sha: c.sha, ip: activeIp, subject: c.subject },
                }));
              }}
              title={`${c.short} · ${c.author} · ${c.date}\n${c.subject}\n+${c.added || 0} −${c.removed || 0} across ${c.files || 0} file(s)`}
              style={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr auto',
                gap: 6,
                padding: '3px 10px',
                cursor: 'pointer',
                fontFamily: 'var(--mono)',
                fontSize: 11,
                borderLeft: '2px solid transparent',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-3)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{c.short}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{c.subject}</span>
              <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>
                {c.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{c.added}</span>}
                {c.removed != null && <span className="err">−{c.removed}</span>}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {/* File list */}
      <div style={{ borderBottom: '1px solid var(--line)', maxHeight: 200, overflow: 'auto' }}>
        {error && <div className="warn" style={{ padding: '8px 10px', fontSize: 11 }}>{error}</div>}
        {!error && files.length === 0 && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            (working tree clean)
          </div>
        )}
        {files.map((f, i) => {
          const sg = _statusGlyph(f.status || '  ');
          const isSel = selected === f.path;
          return (
            <div key={i}
              onClick={() => setSelected(f.path)}
              title={f.path + ' · ' + (f.status || '')}
              style={{
                display: 'grid', gridTemplateColumns: '20px 1fr auto', gap: 6,
                padding: '3px 10px', cursor: 'pointer', fontFamily: 'var(--mono)',
                background: isSel ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                borderLeft: isSel ? '2px solid var(--accent)' : '2px solid transparent',
              }}>
              <span style={{ color: sg.staged.color, fontWeight: 700 }}>{sg.staged.ch}{sg.work.ch}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{f.path}</span>
              <span style={{ fontSize: 10 }}>
                {f.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{f.added}</span>}
                {f.removed != null && <span className="err">−{f.removed}</span>}
              </span>
            </div>
          );
        })}
      </div>

      {/* Diff viewer for selected file */}
      <div style={{ flex: 1, overflow: 'auto', borderBottom: '1px solid var(--line)' }}>
        {!selected && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            Click a file above to view its diff.
          </div>
        )}
        {selected && (
          <pre className="code" style={{
            margin: 0, padding: '8px 10px', fontSize: 11, lineHeight: 1.5,
            whiteSpace: 'pre', fontFamily: 'var(--mono)',
          }}>
            {diffLoading ? 'loading…' :
              (diff || '').split('\n').map((line, i) => {
                let color = 'var(--fg)';
                let bg = 'transparent';
                if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff ') || line.startsWith('@@') || line.startsWith('index ')) {
                  color = 'var(--accent)';
                } else if (line.startsWith('+')) {
                  color = '#7ee787'; bg = 'color-mix(in oklch, #3fb950 12%, transparent)';
                } else if (line.startsWith('-')) {
                  color = '#ffa198'; bg = 'color-mix(in oklch, #f85149 12%, transparent)';
                }
                return <div key={i} style={{ color, background: bg }}>{line || ' '}</div>;
              })
            }
          </pre>
        )}
      </div>

      {/* Commit composer */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          {files.length} change{files.length === 1 ? '' : 's'}
          {stagedCount   > 0 && <span className="ok"   style={{ marginLeft: 6 }}>{stagedCount} staged</span>}
          {unstagedCount > 0 && <span className="warn" style={{ marginLeft: 6 }}>{unstagedCount} unstaged</span>}
        </div>
        <textarea
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder="Commit message — first line = summary, blank line + body for details"
          rows={3}
          style={{
            background: 'var(--bg-3)', border: '1px solid var(--line)',
            borderRadius: 2, padding: '6px 8px', fontSize: 12,
            fontFamily: 'var(--mono)', color: 'var(--fg)', resize: 'vertical',
            outline: 'none', minHeight: 50,
          }}
        />
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className="btn primary"
            disabled={busy !== '' || !message.trim() || files.length === 0}
            onClick={doCommit}
            style={{ flex: 1 }}>
            {busy === 'commit' ? 'committing…' : 'commit ↵'}
          </button>
          <button
            className="btn"
            disabled={busy !== '' || !branch}
            onClick={doPush}>
            {busy === 'push' ? 'pushing…' : ('push ↑' + (ahead ? ahead : ''))}
          </button>
        </div>
        {lastResult && (
          <div style={{
            fontSize: 10, padding: '4px 6px', borderRadius: 2,
            background: lastResult.ok ? 'color-mix(in oklch, var(--ok) 12%, transparent)'
                                       : 'color-mix(in oklch, var(--warn) 12%, transparent)',
            color: lastResult.ok ? 'var(--ok)' : 'var(--warn)',
            fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            maxHeight: 80, overflow: 'auto',
          }}>
            <b>{lastResult.kind}{lastResult.ok ? ' ✓' : ' ✗'}</b>
            {lastResult.stdout && '\n' + lastResult.stdout.trim()}
            {lastResult.stderr && '\n' + lastResult.stderr.trim()}
            {lastResult.error && '\n' + lastResult.error}
          </div>
        )}
      </div>
    </div>
  );
};

const DiffPanel = () => (
  <div className="code" style={{ flex: 1, overflow: 'auto', padding: '12px 14px', fontSize: 12 }}>
    <div className="mute" style={{ marginBottom: 8, fontSize: 11 }}>
      <span className="acc">replace_in_file</span> spi_master/rtl/spi_master.sv
      <span style={{ marginLeft: 12 }} className="ok">+5</span>
      <span style={{ marginLeft: 6 }} className="err">−2</span>
    </div>
    <div style={{ border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
      {window.DIFF_LINES.map((l, i) => (
        <div key={i} style={{
          display: 'grid', gridTemplateColumns: '36px 14px 1fr', gap: 0, padding: '2px 0',
          background: l.kind === 'add' ? 'rgba(89, 192, 138, 0.10)' :
                       l.kind === 'del' ? 'rgba(232, 112, 112, 0.10)' : 'transparent',
          color: l.kind === 'add' ? 'var(--ok)' : l.kind === 'del' ? 'var(--err)' : 'var(--fg)',
          borderLeft: `2px solid ${l.kind === 'add' ? 'var(--ok)' : l.kind === 'del' ? 'var(--err)' : 'transparent'}`,
        }}>
          <span className="mute" style={{ paddingLeft: 8, fontSize: 10 }}>{l.n}</span>
          <span style={{ fontWeight: 700 }}>{l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' '}</span>
          <span style={{ whiteSpace: 'pre' }}>{l.t}</span>
        </div>
      ))}
    </div>
    <div style={{ marginTop: 12, display: 'flex', gap: 6 }}>
      <button className="btn primary">Accept <Kbd>A</Kbd></button>
      <button className="btn">Reject</button>
    </div>
  </div>
);

// ── PreviewPane: in-tab file viewer with Prism syntax highlighting ──
// Inline replacement for the FileViewer modal when the user wants the
// preview alongside (well, replacing) the chat feed via the main tab
// strip. Same /api/file backend; Prism.js handles language detection
// per the PRISM_LANG_MAP set up in index.html.
const DeferredMarkdownPreview = ({ body }) => {
  const nodeRef = React.useRef(null);
  const [html, setHtml] = React.useState('');
  const text = String(body || '');

  React.useEffect(() => {
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

  React.useEffect(() => {
    if (html && nodeRef.current) _postProcessMarkdownNode(nodeRef.current);
  }, [html]);

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
    <div
      ref={nodeRef}
      className="md-agent md-preview"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

// Fold-range tree builder. Server returns a flat list of
// {kind, label, line_start, line_end}; nest them so an outer range
// can wrap inner children when rendered as <details>.
const _buildFoldTree = (ranges) => {
  const sorted = (ranges || []).slice().sort((a, b) => {
    if (a.line_start !== b.line_start) return a.line_start - b.line_start;
    return b.line_end - a.line_end; // outer first
  });
  const root = { children: [], line_start: 0, line_end: 1e9 };
  const stack = [root];
  for (const r of sorted) {
    const node = { ...r, children: [] };
    while (stack.length &&
           !(stack[stack.length - 1].line_start <= node.line_start &&
             stack[stack.length - 1].line_end   >= node.line_end)) {
      stack.pop();
    }
    if (!stack.length) stack.push(root);
    stack[stack.length - 1].children.push(node);
    stack.push(node);
  }
  return root;
};

// Pinned to the standalone /tmp/ssot_fold_engine.html demo palette so
// the in-product FoldablePane summary colors don't drift between
// theme dir/A/B + light/dark combinations. ATLAS variables map to
// chat-panel contrast and produced visibly different fold kind
// colors than the demo the user signed off on.
const _FOLD_KIND_COLOR = {
  module: '#88c', always_ff: '#cc8', always_comb: '#8cc',
  function: '#c8c', task: '#fa8', case: '#aca',
  initial: '#888', 'generate-loop': '#cca', 'generate-if': '#cca',
  instance: '#fa8',  // module instances stand out same as task — orange-pink
  section: '#88c', 'sub-section': '#cc8', item: '#8cc', scalar: '#a98',
  object: '#88c', array: '#8cc',
};

const _splitYamlComment = (value) => {
  let quote = '';
  for (let i = 0; i < value.length; i++) {
    const ch = value[i];
    if (quote) {
      if (ch === quote && value[i - 1] !== '\\') quote = '';
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      continue;
    }
    if (ch === '#' && (i === 0 || /\s/.test(value[i - 1]))) {
      return [value.slice(0, i), value.slice(i)];
    }
  }
  return [value, ''];
};

const _highlightYamlValue = (value) => {
  if (!value) return '';
  const [body, comment] = _splitYamlComment(value);
  const leading = body.match(/^\s*/)?.[0] || '';
  const trailing = body.match(/\s*$/)?.[0] || '';
  const core = body.slice(leading.length, body.length - trailing.length);
  let cls = 'plain';
  if (/^(['"]).*\1$/.test(core)) cls = 'string';
  else if (/^(true|false|yes|no|on|off)$/i.test(core)) cls = 'boolean';
  else if (/^(null|~)$/i.test(core)) cls = 'null';
  else if (/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(core)) cls = 'number';
  else if (/^[|>]$/.test(core)) cls = 'operator';
  const coreHtml = core
    ? `<span class="token ${cls}">${_escHtml(core)}</span>`
    : '';
  const commentHtml = comment
    ? `<span class="token comment">${_escHtml(comment)}</span>`
    : '';
  return `${_escHtml(leading)}${coreHtml}${_escHtml(trailing)}${commentHtml}`;
};

const _highlightYamlLine = (line) => {
  if (!line || !line.trim()) return _escHtml(line || ' ');
  const commentOnly = line.match(/^(\s*)(#.*)$/);
  if (commentOnly) {
    return `${_escHtml(commentOnly[1])}<span class="token comment">${_escHtml(commentOnly[2])}</span>`;
  }
  const keyLine = line.match(/^(\s*)(-\s+)?([^:#\n][^:\n]*?)(\s*:\s*)(.*)$/);
  if (keyLine) {
    const [, indent, dash = '', key, sep, rest] = keyLine;
    return [
      _escHtml(indent),
      dash ? `<span class="token punctuation">${_escHtml(dash)}</span>` : '',
      `<span class="token key">${_escHtml(key.trimEnd())}</span>`,
      `<span class="token punctuation">${_escHtml(sep)}</span>`,
      _highlightYamlValue(rest),
    ].join('');
  }
  const listLine = line.match(/^(\s*-\s+)(.*)$/);
  if (listLine) {
    return `<span class="token punctuation">${_escHtml(listLine[1])}</span>${_highlightYamlValue(listLine[2])}`;
  }
  return _highlightYamlValue(line);
};

const _highlightYamlBlock = (text) =>
  String(text || '').split(/\r?\n/).map(_highlightYamlLine).join('\n');

// FoldablePane renders the file body as one <div class="line-row"> per
// source line, wrapping ranges from /api/fold-symbols in <details>.
// Supports:
//   • click ▾/▸ on a fold summary → toggle
//   • click 💬 button on a summary → dispatch atlas-fold-comment
//   • drag-select on line-number gutter → floating "Comment selection"
const FoldablePane = ({ path, body, lang, lineCount, focusLine = 0 }) => {
  const [ranges, setRanges] = React.useState([]);
  const [skipped, setSkipped] = React.useState(null);
  const [floating, setFloating] = React.useState(null);  // {top, left, lo, hi}
  const [sel, setSel] = React.useState(null);            // {lo, hi}
  const dragRef = React.useRef({ start: null, end: null, on: false });
  const paneRef = React.useRef(null);

  // Fetch fold ranges per (path, body-length) — body-length acts as a
  // cheap content-changed signal so reloaded files refetch.
  React.useEffect(() => {
    if (!path) { setRanges([]); setSkipped(null); return; }
    let cancelled = false;
    fetch(`/api/fold-symbols?path=${encodeURIComponent(path)}`)
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
  const onLineMouseDown = (ln, ev) => {
    ev.preventDefault();
    dragRef.current = { start: ln, end: ln, on: true };
    setSel({ lo: ln, hi: ln });
    setFloating(null);
  };
  const onLineMouseEnter = (ln) => {
    if (!dragRef.current.on) return;
    dragRef.current.end = ln;
    const a = dragRef.current.start, b = ln;
    setSel({ lo: Math.min(a, b), hi: Math.max(a, b) });
  };
  React.useEffect(() => {
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
      const lineEl = pane.querySelector(`.line-row[data-ln="${hi}"]`)
                  || pane.querySelector(`[data-ln="${hi}"]`);
      if (!lineEl) return;
      // Anchor BELOW the last-selected line, pinned to the pane's
      // RIGHT edge. Button is a child of .foldable-pane (NOT
      // .foldable-body) so its `right: 16` lands on the visible
      // right edge even when the body has horizontal-scroll wider
      // than the pane. We accumulate offsetTop up the chain until
      // we hit .foldable-pane itself.
      let top = lineEl.offsetTop + lineEl.offsetHeight;
      let p = lineEl.offsetParent;
      while (p && p !== pane) {
        top += p.offsetTop;
        p = p.offsetParent;
      }
      setFloating({ top, lo, hi });
    };
    window.addEventListener('mouseup', onUp);
    return () => window.removeEventListener('mouseup', onUp);
  }, []);

  React.useEffect(() => {
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

  const dispatchComment = (lo, hi, label) => {
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
  const highlightLine = React.useCallback((line) => {
    if (!line || !line.trim()) return line || ' ';
    if (lang === 'yaml' || lang === 'yml') return _highlightYamlLine(line);
    const Prism = window.Prism;
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
  const srcLines = React.useMemo(
    () => body.split('\n').map(line => line.replace(/^%[0-9A-Fa-f]{4,}\s?/, '')),
    [body],
  );
  const tree = React.useMemo(() => _buildFoldTree(ranges), [ranges]);

  // Render the source as nested <details> + line-rows. Fold controls are
  // deliberately separate rows above the source range: the original YAML/RTL
  // line always remains in the body, so the preview stays faithful to the file.
  const renderLineRow = (ln) => {
    const text = srcLines[ln - 1] != null ? srcLines[ln - 1] : '';
    const html = highlightLine(text);
    const inSel = sel && ln >= sel.lo && ln <= sel.hi;
    return (
      <div key={`L${ln}`} className={'line-row' + (inSel ? ' sel' : '')} data-ln={ln}>
        <span className="lineno"
              data-ln={ln}
              onMouseDown={(ev) => onLineMouseDown(ln, ev)}
              onMouseEnter={() => onLineMouseEnter(ln)}>
          {ln}
        </span>
        <span className="line"
              dangerouslySetInnerHTML={{ __html: html === text ? _escHtml(text) || ' ' : html }} />
      </div>
    );
  };

  const renderFoldSummary = (c, color, depth) => {
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
        <button className="fold-comment-btn"
                onClick={(ev) => { ev.preventDefault(); ev.stopPropagation();
                                   dispatchComment(c.line_start, c.line_end, c.label); }}>
          💬 comment
        </button>
      </summary>
    );
  };

  const renderTree = (node, cursor, depth) => {
    const out = [];
    const children = node.children.slice().sort((a, b) => a.line_start - b.line_start);
    for (const c of children) {
      while (cursor < c.line_start) { out.push(renderLineRow(cursor)); cursor += 1; }
      const color = _FOLD_KIND_COLOR[c.kind] || 'var(--fg-mute)';
      const opened = true;
      const inner = [];
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
  const trail = [];
  let cur = renderedTree.cursor;
  while (cur <= lineCount) { trail.push(renderLineRow(cur)); cur += 1; }

  return (
    <div className={`foldable-pane ${lang === 'yaml' || lang === 'yml' ? 'yaml-pane' : ''}`} ref={paneRef}>
      {skipped && (
        <div style={{ padding: '6px 14px', color: 'var(--warn)', fontSize: 11, fontFamily: 'var(--mono)' }}>
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
      {floating && (
        <button className="fold-floating-comment"
                style={{ position: 'absolute', left: 4, top: floating.top + 4 }}
                onClick={() => dispatchComment(floating.lo, floating.hi, '')}>
          💬 Comment L{floating.lo}-L{floating.hi}
        </button>
      )}
    </div>
  );
};

const LintToolResultCard = ({ result, onOpenDiagnostic }) => {
  const passed = result?.passed === true;
  const diagnostics = Array.isArray(result?.diagnostics) ? result.diagnostics : [];
  return (
    <div style={{
      border: '1px solid ' + (passed ? 'color-mix(in oklch, var(--ok) 35%, var(--line))' : 'color-mix(in oklch, var(--err) 35%, var(--line))'),
      background: 'var(--panel)',
      borderRadius: 4,
      padding: 10,
      minWidth: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontFamily: 'var(--mono)', fontWeight: 900, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {result?.tool || 'tool'}
        </span>
        <AtlasStatusBadge status={passed ? 'approved' : 'error'} label={passed ? 'pass' : 'fail'} compact />
        <span style={{ flex: 1 }} />
        <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>
          rc {result?.returncode ?? '?'}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8, marginBottom: 8 }}>
        {[
          ['errors', result?.errors ?? 0],
          ['warnings', result?.warnings ?? 0],
          ['diagnostics', diagnostics.length],
        ].map(([label, value]) => (
          <div key={label} style={{ border: '1px solid var(--line)', background: 'var(--bg)', borderRadius: 3, padding: '6px 7px' }}>
            <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
            <div style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 14 }}>{value}</div>
          </div>
        ))}
      </div>
      <div className="trunc" title={result?.command || ''} style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>
        {result?.command || '(no command)'}
      </div>
      {diagnostics.length > 0 && (
        <div style={{ marginTop: 8, display: 'grid', gap: 5 }}>
          {diagnostics.slice(0, 5).map((d, idx) => (
            <button key={idx} type="button" onClick={() => onOpenDiagnostic?.(d)} style={{
              textAlign: 'left',
              border: 0,
              background: 'transparent',
              borderLeft: '2px solid ' + (String(d.severity || '').toLowerCase() === 'error' ? 'var(--err)' : 'var(--warn)'),
              padding: '0 0 0 7px',
              color: 'var(--fg)',
              fontFamily: 'var(--mono)',
              fontSize: 10,
              lineHeight: 1.35,
              cursor: d.path || d.file ? 'pointer' : 'default',
            }}>
              <span style={{ color: 'var(--fg-mute)' }}>
                {d.severity || 'diag'} {d.file || ''}{d.line ? `:${d.line}` : ''}{d.column ? `:${d.column}` : ''}
                {d.rule ? ` ${d.rule}` : ''}
              </span>
              <div>{String(d.message || '').slice(0, 260)}</div>
              {d.source && <div style={{ color: 'var(--fg-mute)' }}>{String(d.source).slice(0, 220)}</div>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const LintReportSummary = ({ ip, onSelectPath, onOpenDiagnostic }) => {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState('');
  const [tick, setTick] = React.useState(0);
  const [running, setRunning] = React.useState(false);

  const load = React.useCallback((refresh = false) => {
    if (!ip) return Promise.resolve();
    setLoading(true);
    setErr('');
    if (refresh) setRunning(true);
    const url = `/api/lint/report?ip=${encodeURIComponent(ip)}${refresh ? '&refresh=1' : ''}`;
    return fetch(url, { cache: 'no-store' })
      .then(async r => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.error || `HTTP ${r.status}`);
        setData(d);
        if (d.report_path && !refresh) onSelectPath?.(d.report_path);
      })
      .catch(e => setErr(String(e.message || e)))
      .finally(() => {
        setLoading(false);
        setRunning(false);
      });
  }, [ip, onSelectPath]);

  React.useEffect(() => { load(false); }, [load, tick]);

  const tools = Array.isArray(data?.tool_results) ? data.tool_results : [];
  const passed = data?.passed === true;
  const hasReport = data?.exists === true;
  const runOutput = data?.run?.output || '';

  return (
    <div style={{
      borderBottom: '1px solid var(--line)',
      background: 'var(--bg-2)',
      padding: 12,
      display: 'grid',
      gap: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div>
          <div style={{ fontWeight: 900, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 12 }}>
            pyslang + verilator lint
          </div>
          <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, marginTop: 2 }}>
            {data?.resolved_ip || ip} {data?.timestamp ? `· ${data.timestamp}` : ''}
          </div>
        </div>
        <span style={{ flex: 1 }} />
        {hasReport && <AtlasStatusBadge status={passed ? 'approved' : 'error'} label={passed ? 'clean' : 'issues'} compact />}
        <button
          className="btn"
          onClick={() => setTick(v => v + 1)}
          disabled={loading}
          style={{ padding: '2px 8px', fontSize: 10 }}
        >refresh</button>
        <button
          className="btn"
          onClick={() => load(true)}
          disabled={running || loading}
          style={{ padding: '2px 8px', fontSize: 10 }}
        >run report</button>
      </div>

      {err && (
        <div style={{ color: 'var(--err)', fontFamily: 'var(--mono)', fontSize: 11 }}>{err}</div>
      )}
      {!err && !hasReport && !loading && (
        <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
          No dut_lint.json found yet.
        </div>
      )}
      {loading && (
        <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
          {running ? 'Running canonical DUT lint...' : 'Loading lint report...'}
        </div>
      )}

      {hasReport && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0, 1fr))', gap: 8 }}>
            {[
              ['tool', data.tool || 'pyslang+verilator'],
              ['errors', data.errors ?? 0],
              ['warnings', data.warnings ?? 0],
              ['suppressions', data.suppression_violations ?? 0],
              ['style', data.style_violations ?? 0],
            ].map(([label, value]) => (
              <div key={label} style={{ border: '1px solid var(--line)', background: 'var(--panel)', borderRadius: 3, padding: '6px 8px', minWidth: 0 }}>
                <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
                <div className="trunc" title={String(value)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 13 }}>{value}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
            {tools.map((result, idx) => (
              <LintToolResultCard
                key={`${result.tool || 'tool'}-${idx}`}
                result={result}
                onOpenDiagnostic={onOpenDiagnostic}
              />
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button className="btn" onClick={() => data.report_path && onSelectPath?.(data.report_path)} style={{ padding: '2px 8px', fontSize: 10 }}>
              open json
            </button>
            <button className="btn" onClick={() => data.log_path && onSelectPath?.(data.log_path)} disabled={!data.log_exists} style={{ padding: '2px 8px', fontSize: 10 }}>
              open log
            </button>
            <span className="trunc" title={data.command || ''} style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              {data.command || '(no command)'}
            </span>
          </div>
          {runOutput && (
            <ToolOutputPre text={runOutput} tool="bash" />
          )}
        </>
      )}
    </div>
  );
};

const coverageMetricText = (metric) => {
  if (!metric) return 'n/a';
  if (metric.value != null) return String(metric.value);
  const total = metric.total;
  const hit = metric.hit;
  if (total != null && Number(total) > 0) {
    const pct = metric.pct == null ? '' : ` · ${Number(metric.pct).toFixed(1)}%`;
    return `${hit ?? 0}/${total}${pct}`;
  }
  if (metric.pct != null) return `${Number(metric.pct).toFixed(1)}%`;
  return String(hit ?? 'n/a');
};

const CoverageMetricCell = ({ metric }) => {
  const pct = Number(metric?.pct);
  const hasPct = Number.isFinite(pct);
  const clamped = Math.max(0, Math.min(100, hasPct ? pct : 0));
  const color = hasPct && pct >= Number(metric?.target_pct ?? 90) ? 'var(--ok)' : hasPct ? 'var(--warn)' : 'var(--fg-mute)';
  return (
    <div style={{ border: '1px solid var(--line)', background: 'var(--bg)', borderRadius: 3, padding: '6px 7px', minWidth: 0 }}>
      <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{metric?.label || 'metric'}</div>
      <div className="trunc" title={coverageMetricText(metric)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 13 }}>
        {coverageMetricText(metric)}
      </div>
      {hasPct && (
        <div style={{ height: 4, background: 'var(--line)', marginTop: 5, borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ width: `${clamped}%`, height: '100%', background: color }} />
        </div>
      )}
    </div>
  );
};

const CoverageToolCard = ({ tool, onSelectPath, onOpenDiagnostic }) => {
  const available = tool?.available === true;
  const status = available ? (tool?.status || 'available') : 'missing';
  const metrics = Array.isArray(tool?.metrics) ? tool.metrics : [];
  const diagnostics = Array.isArray(tool?.diagnostics) ? tool.diagnostics : [];
  const missingBins = Array.isArray(tool?.missing_bins) ? tool.missing_bins : [];
  const scopes = Array.isArray(tool?.scopes) ? tool.scopes : [];
  return (
    <div style={{
      border: '1px solid ' + (available ? 'var(--line)' : 'color-mix(in oklch, var(--warn) 35%, var(--line))'),
      background: 'var(--panel)',
      borderRadius: 4,
      padding: 10,
      minWidth: 0,
      display: 'grid',
      gap: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="trunc" title={tool?.label || ''} style={{ fontFamily: 'var(--mono)', fontWeight: 900, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {tool?.label || 'coverage'}
        </span>
        <AtlasStatusBadge status={status === 'pass' ? 'approved' : status === 'missing' ? 'pending' : status} label={status} compact />
      </div>
      {metrics.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(108px, 1fr))', gap: 7 }}>
          {metrics.map((metric, idx) => <CoverageMetricCell key={`${tool?.id || 'tool'}-${idx}`} metric={metric} />)}
        </div>
      )}
      {tool?.note && (
        <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>
          {tool.note}
        </div>
      )}
      {(tool?.path || tool?.vcd) && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', minWidth: 0 }}>
          {tool.path && (
            <button className="btn" onClick={() => onSelectPath?.(tool.path)} style={{ padding: '2px 8px', fontSize: 10 }}>
              open source
            </button>
          )}
          <span className="trunc" title={tool.path || tool.vcd || ''} style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>
            {tool.path || tool.vcd}
          </span>
        </div>
      )}
      {diagnostics.length > 0 && (
        <div style={{ display: 'grid', gap: 5 }}>
          {diagnostics.slice(0, 4).map((d, idx) => (
            <button key={idx} type="button" onClick={() => onOpenDiagnostic?.(d)} style={{
              textAlign: 'left',
              border: 0,
              background: 'transparent',
              borderLeft: '2px solid ' + (String(d.severity || '').toLowerCase() === 'error' ? 'var(--err)' : 'var(--warn)'),
              padding: '0 0 0 7px',
              color: 'var(--fg)',
              fontFamily: 'var(--mono)',
              fontSize: 10,
              lineHeight: 1.35,
              cursor: d.path || d.file ? 'pointer' : 'default',
            }}>
              <span style={{ color: 'var(--fg-mute)' }}>
                {d.severity || 'diag'} {d.file || ''}{d.line ? `:${d.line}` : ''}
              </span>
              <div>{String(d.message || '').slice(0, 260)}</div>
            </button>
          ))}
        </div>
      )}
      {missingBins.length > 0 && (
        <div style={{ borderTop: '1px solid var(--line)', paddingTop: 7, display: 'grid', gap: 4 }}>
          <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>missing bins</div>
          {missingBins.slice(0, 5).map((bin, idx) => (
            <div key={idx} className="trunc" title={bin?.description || bin?.id || ''} style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
              {bin?.id || String(bin)}
            </div>
          ))}
        </div>
      )}
      {scopes.length > 0 && (
        <div style={{ borderTop: '1px solid var(--line)', paddingTop: 7, display: 'grid', gap: 4 }}>
          <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>lowest-toggle scopes</div>
          {scopes.slice(0, 5).map((scope, idx) => (
            <div key={idx} style={{ display: 'grid', gridTemplateColumns: '62px minmax(0, 1fr)', gap: 6, fontFamily: 'var(--mono)', fontSize: 10 }}>
              <span style={{ color: 'var(--warn)' }}>{Number(scope?.pct || 0).toFixed(1)}%</span>
              <span className="trunc" title={scope?.scope || ''}>{scope?.scope || '(scope)'}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const CoverageReportSummary = ({ ip, onSelectPath, onOpenDiagnostic }) => {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState('');
  const [running, setRunning] = React.useState('');
  const [tick, setTick] = React.useState(0);

  const load = React.useCallback((mode = '') => {
    if (!ip) return Promise.resolve();
    setLoading(true);
    setErr('');
    setRunning(mode);
    const params = new URLSearchParams({ ip });
    if (mode === 'summary' || mode === 'all') params.set('refresh', '1');
    if (mode === 'vcd' || mode === 'all') params.set('vcd', '1');
    const url = `/reports/cov?${params.toString()}`;
    return fetch(url, { cache: 'no-store' })
      .then(async r => {
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.error || `HTTP ${r.status}`);
        setData(d);
        const preferred = d.report_exists ? d.report_path
          : d.ssot_exists ? d.ssot_path
          : d.lcov_exists ? d.lcov_path
          : d.toggle_exists ? d.toggle_path
          : d.markdown_exists ? d.markdown_path
          : '';
        if (preferred) onSelectPath?.(preferred);
      })
      .catch(e => setErr(String(e.message || e)))
      .finally(() => {
        setLoading(false);
        setRunning('');
      });
  }, [ip, onSelectPath]);

  React.useEffect(() => { load(''); }, [load, tick]);

  const tools = Array.isArray(data?.tools) ? data.tools : [];
  const artifacts = Array.isArray(data?.artifacts) ? data.artifacts : [];
  const vcdPaths = Array.isArray(data?.vcd_paths) ? data.vcd_paths : [];
  const missingTools = tools.filter(t => !t.available).length;
  const runEntries = Object.entries(data?.run || {}).filter(([, value]) => value && value.output);

  return (
    <div style={{
      borderBottom: '1px solid var(--line)',
      background: 'var(--bg-2)',
      padding: 12,
      display: 'grid',
      gap: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div>
          <div style={{ fontWeight: 900, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 12 }}>
            coverage report
          </div>
          <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, marginTop: 2 }}>
            {data?.resolved_ip || ip} · Verilator + pyslang + VCD + FL/CL
          </div>
        </div>
        <span style={{ flex: 1 }} />
        {data?.status && data.status !== 'unknown' && <AtlasStatusBadge status={data.status} label={data.status} compact />}
        <button className="btn" onClick={() => setTick(v => v + 1)} disabled={loading} style={{ padding: '2px 8px', fontSize: 10 }}>
          refresh
        </button>
        <button className="btn" onClick={() => load('summary')} disabled={!!running || loading} style={{ padding: '2px 8px', fontSize: 10 }}>
          run summary
        </button>
        <button className="btn" onClick={() => load('vcd')} disabled={!!running || loading} style={{ padding: '2px 8px', fontSize: 10 }}>
          run vcd
        </button>
      </div>

      {err && <div style={{ color: 'var(--err)', fontFamily: 'var(--mono)', fontSize: 11 }}>{err}</div>}
      {loading && (
        <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
          {running === 'summary' ? 'Running SSOT coverage summary...' : running === 'vcd' ? 'Running VCD toggle coverage...' : 'Loading coverage report...'}
        </div>
      )}
      {!err && data && !data.exists && !loading && (
        <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
          No coverage artifacts found yet. Static RTL scan still needs a DUT filelist or rtl/ sources.
        </div>
      )}

      {data && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 8 }}>
            {[
              ['tools', tools.length],
              ['missing', missingTools],
              ['artifacts', artifacts.length],
              ['vcd files', vcdPaths.length],
            ].map(([label, value]) => (
              <div key={label} style={{ border: '1px solid var(--line)', background: 'var(--panel)', borderRadius: 3, padding: '6px 8px', minWidth: 0 }}>
                <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
                <div className="trunc" title={String(value)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 13 }}>{value}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(270px, 1fr))', gap: 10 }}>
            {tools.map(tool => (
              <CoverageToolCard key={tool.id || tool.label} tool={tool} onSelectPath={onSelectPath} onOpenDiagnostic={onOpenDiagnostic} />
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <button className="btn" onClick={() => data.report_path && onSelectPath?.(data.report_path)} disabled={!data.report_exists} style={{ padding: '2px 8px', fontSize: 10 }}>
              open json
            </button>
            <button className="btn" onClick={() => data.lcov_path && onSelectPath?.(data.lcov_path)} disabled={!data.lcov_exists} style={{ padding: '2px 8px', fontSize: 10 }}>
              open lcov
            </button>
            <button className="btn" onClick={() => data.toggle_path && onSelectPath?.(data.toggle_path)} disabled={!data.toggle_exists} style={{ padding: '2px 8px', fontSize: 10 }}>
              open toggle
            </button>
            <button className="btn" onClick={() => data.markdown_path && onSelectPath?.(data.markdown_path)} disabled={!data.markdown_exists} style={{ padding: '2px 8px', fontSize: 10 }}>
              open md
            </button>
          </div>
          {Array.isArray(data.errors) && data.errors.length > 0 && (
            <div style={{ color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              {data.errors.join(' · ')}
            </div>
          )}
          {runEntries.map(([name, info]) => (
            <ToolOutputPre key={name} text={`${name}: rc ${info.returncode}\n${info.output || ''}`} tool="bash" />
          ))}
        </>
      )}
    </div>
  );
};

const WorkflowReportPane = ({ workflow, activeIp }) => {
  const meta = WORKFLOW_REPORT_TABS[workflow] || null;
  const inferredIp = React.useMemo(() => {
    const direct = String(activeIp || '').trim();
    if (direct && direct !== 'default') return direct;
    const ns = String(window.ACTIVE_SESSION || '').replace(/^\/+|\/+$/g, '');
    const parts = ns.split('/').filter(Boolean);
    if (parts.length >= 3 && parts[parts.length - 1] === workflow) {
      const candidate = parts[parts.length - 2] || '';
      if (candidate && candidate !== 'default') return candidate;
    }
    const scope = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
    const leaf = scope.split('/').filter(Boolean).pop() || '';
    if (leaf && leaf !== 'default' && leaf !== workflow) return leaf;
    return direct;
  }, [activeIp, workflow]);
  const ip = String(inferredIp || '').trim();
  const [dataTick, setDataTick] = React.useState(0);
  const [selected, setSelected] = React.useState('');
  const [focusLine, setFocusLine] = React.useState(0);

  React.useEffect(() => {
    const handler = (ev) => {
      const detail = ev && ev.detail;
      if (detail === 'FILE_TREE' || detail === 'SCOPE_PATH') setDataTick(v => v + 1);
    };
    window.addEventListener('atlas-data-changed', handler);
    return () => window.removeEventListener('atlas-data-changed', handler);
  }, []);

  React.useEffect(() => {
    if (!window.atlasData?.refreshFileTree) return;
    try {
      window.atlasData.refreshFileTree(ip || window.SCOPE_PATH || '', { recursive: true });
    } catch (_) {}
  }, [workflow, ip]);

  const paths = React.useMemo(() => {
    if (!meta || !ip) return [];
    const candidatePaths = (meta.paths ? meta.paths(ip) : []).filter(Boolean);
    const scope = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
    const folderPrefixes = (meta.folders || []).map(f => `${ip}/${f.replace(/^\/+|\/+$/g, '')}/`);
    const related = (window.FILE_TREE || [])
      .filter(n => n && n.type === 'file')
      .map(n => {
        const relName = String(n.name || '').replace(/^\/+|\/+$/g, '');
        return (scope ? `${scope}/` : '') + relName;
      })
      .filter(p => folderPrefixes.some(prefix => p.startsWith(prefix)))
      .sort((a, b) => a.localeCompare(b));
    return Array.from(new Set([...candidatePaths, ...related]));
  }, [meta, ip, dataTick]);

  const pathsKey = paths.join('\n');
  React.useEffect(() => {
    if (!paths.length) {
      setSelected('');
      return;
    }
    setSelected(current => (current && paths.includes(current)) ? current : paths[0]);
  }, [pathsKey]);

  const openLintDiagnostic = React.useCallback((diag) => {
    const diagPath = String(diag?.path || diag?.file || '').replace(/^\/+/, '');
    const line = Number(diag?.line || 0);
    if (!diagPath) return;
    setSelected(diagPath);
    setFocusLine(line || 0);
    readAtlasAsyncResource('file', diagPath, true).catch(() => {});
  }, []);

  if (!meta) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--fg-mute)' }}>
        No report surface for this workflow.
      </div>
    );
  }

  if (!ip) {
    return (
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12,
      }}>
        Select IP_ID to load {meta.title}.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'grid', gridTemplateColumns: '300px minmax(0, 1fr)', overflow: 'hidden' }}>
      <div style={{
        minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column',
        borderRight: '1px solid var(--line)', background: 'var(--panel)',
      }}>
        <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--line)' }}>
          <div style={{ fontWeight: 800, fontSize: 12, letterSpacing: '0.06em', textTransform: 'uppercase' }}>{meta.title}</div>
          <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, marginTop: 3 }}>{ip} · {paths.length} artifact(s)</div>
        </div>
        <div style={{ padding: 8, borderBottom: '1px solid var(--line)', display: 'flex', gap: 6 }}>
          <button
            className="btn"
            onClick={() => {
              try { window.atlasData?.refreshFileTree?.(ip || window.SCOPE_PATH || '', { recursive: true }); } catch (_) {}
              if (selected) readAtlasAsyncResource('file', selected, true).catch(() => {});
            }}
            style={{ padding: '2px 8px', fontSize: 10 }}
          >refresh</button>
          <span style={{ flex: 1 }} />
          <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, alignSelf: 'center' }}>{workflow}</span>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '6px 0' }}>
          {paths.map((p, i) => {
            const active = selected === p;
            const name = p.split('/').slice(1).join('/') || p;
            return (
              <div
                key={p}
                onClick={() => setSelected(p)}
                onMouseEnter={() => readAtlasAsyncResource('file', p).catch(() => {})}
                title={p}
                style={{
                  display: 'grid', gridTemplateColumns: '22px minmax(0, 1fr)',
                  gap: 6, padding: '5px 10px', cursor: 'pointer',
                  background: active ? 'var(--select)' : 'transparent',
                  color: active ? 'var(--accent)' : 'var(--fg)',
                  borderLeft: '2px solid ' + (active ? 'var(--accent)' : 'transparent'),
                  fontFamily: 'var(--mono)', fontSize: 11,
                }}
              >
                <span style={{ color: 'var(--fg-mute)' }}>{i + 1}</span>
                <span className="trunc">{name}</span>
              </div>
            );
          })}
          {!paths.length && (
            <div style={{ padding: 12, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
              No known report artifacts under {ip}.
            </div>
          )}
        </div>
      </div>
      <div style={{ minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        {workflow === 'lint' && (
          <LintReportSummary ip={ip} onSelectPath={setSelected} onOpenDiagnostic={openLintDiagnostic} />
        )}
        {workflow === 'coverage' && (
          <CoverageReportSummary ip={ip} onSelectPath={setSelected} onOpenDiagnostic={openLintDiagnostic} />
        )}
        <PreviewPane path={selected} onClose={() => {}} focusLine={focusLine} />
      </div>
    </div>
  );
};

const PreviewPane = ({ path, onClose, focusLine = 0 }) => {
  const ext = (path ? (path.split('.').pop() || '') : '').toLowerCase();
  const lang = (window.PRISM_LANG_MAP && window.PRISM_LANG_MAP[ext]) || 'none';
  const isMarkdown = ['md', 'markdown', 'mdown', 'mkdn'].includes(ext);
  const hasGlobPath = !!path && /[*?[\]{}]/.test(path);
  const [resource, reloadPreview] = useAtlasAsyncResource('file', hasGlobPath ? '' : path);

  // Auto-reload when the backend emits file_changed for THIS path.
  React.useEffect(() => {
    if (!path || hasGlobPath) return undefined;
    const handler = (ev) => {
      const changed = (ev && ev.detail && ev.detail.path) || '';
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
  const [highlightedHtml, setHighlightedHtml] = React.useState('');

  React.useEffect(() => {
    setHighlightedHtml('');
    if (!body || !canHighlight || !window.Prism) return undefined;
    let cancelled = false;
    const runHighlight = () => {
      const Prism = window.Prism;
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

  const lineCount = body.split('\n').length;
  const sizeKb = size > 0 ? (size / 1024).toFixed(1) + ' KB' : '';
  const copyPath = () => { try { navigator.clipboard.writeText(path); } catch (_) {} };
  const copyAll  = () => { try { navigator.clipboard.writeText(body);  } catch (_) {} };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* meta strip */}
      <div style={{
        padding: '4px 14px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 10, fontSize: 10,
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
      }}>
        <span>lang <span style={{ color: 'var(--accent)' }}>{isMarkdown ? 'rendered markdown' : (lang === 'none' ? 'plain' : lang)}</span></span>
        <span className="mute">·</span>
        <span>{lineCount} lines</span>
        {sizeKb && <><span className="mute">·</span><span>{sizeKb}</span></>}
        {truncated && <><span className="mute">·</span><span className="warn">truncated at {Math.round((body.length || 0) / 1024)}KB</span></>}
        {highlightTooLarge && <><span className="mute">·</span><span className="warn">syntax highlight skipped for speed</span></>}
        {canHighlight && !highlightedHtml && !loading && body && <><span className="mute">·</span><span className="warn">syntax pending</span></>}
        {hasGlobPath && <><span className="mute">·</span><span className="warn">glob path</span></>}
        {loading && <AtlasStatusBadge status={hasBody ? 'refreshing' : 'loading'} compact soft />}
        <span style={{ flex: 1 }} />
        <span onClick={() => reloadPreview(true)} style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>refresh</span>
        <span onClick={copyAll}  style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>copy</span>
        <span onClick={copyPath} style={{ cursor: 'pointer', padding: '1px 6px', border: '1px solid var(--line)', borderRadius: 2 }}>copy path</span>
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
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto', background: isMarkdown ? 'var(--bg)' : 'var(--bg-3)' }}>
        {blockingLoading ? (
          <div style={{ padding: 16, color: 'var(--fg-mute)', fontFamily: 'var(--code-font, var(--mono))', fontSize: 12 }}>
            loading {path}…
          </div>
        ) : isMarkdown ? (
          <DeferredMarkdownPreview body={body} />
        ) : hasBody ? (
          /* Foldable view: per-line gutter + nested <details> wraps
             from /api/fold-symbols. Verilog/SV and YAML get an AST
             fold; every other extension still gets the per-line
             gutter so drag-select-comment works universally. The
             server's fold extractor returns [] for unknown types,
             so the fold UI stays out of the way. */
          <FoldablePane path={path} body={body} lang={lang} lineCount={lineCount} focusLine={focusLine} />
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
// identical to the in-flight `replace_in_file` previews.
const GitDiffPane = ({ sha, ip, subject, onClose }) => {
  const [body, setBody] = React.useState('');
  const [err, setErr] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  React.useEffect(() => {
    if (!sha) { setBody(''); return undefined; }
    let cancelled = false;
    setLoading(true); setErr('');
    const ipQ = ip ? `&ip=${encodeURIComponent(ip)}` : '';
    fetch(`/api/git/show?sha=${encodeURIComponent(sha)}${ipQ}`)
      .then(r => r.json())
      .then(d => {
        if (cancelled) return;
        if (d.error) setErr(d.error);
        setBody(String(d.diff || ''));
        setLoading(false);
      })
      .catch(e => {
        if (cancelled) return;
        setErr(String(e));
        setLoading(false);
      });
    return () => { cancelled = true; };
  }, [sha, ip]);
  // Split body into header (commit/author/date/subject) and patch
  // (everything from the first `diff --git` onwards) so the header
  // can be styled differently.
  const splitIdx = body.indexOf('\ndiff --git');
  const header = splitIdx >= 0 ? body.slice(0, splitIdx) : body;
  const patch = splitIdx >= 0 ? body.slice(splitIdx + 1) : '';
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <div style={{
        padding: '6px 14px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 10, fontSize: 11,
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
        background: 'var(--bg-2)',
      }}>
        <span className="acc" style={{ fontWeight: 600 }}>{(sha || '').slice(0, 8)}</span>
        {ip && <><span className="mute">·</span><span>{ip}</span></>}
        {subject && <><span className="mute">·</span><span style={{
          color: 'var(--fg)',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          flex: 1, minWidth: 0,
        }}>{subject}</span></>}
        {loading && <span className="mute">loading…</span>}
        <span style={{ flex: 1 }} />
        <span onClick={onClose} title="close diff (back to preview)"
          style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--line)', borderRadius: 2 }}>
          × close
        </span>
      </div>
      {err && (
        <div style={{
          padding: '6px 14px', color: 'var(--err)', fontFamily: 'var(--mono)',
          fontSize: 11, borderBottom: '1px solid var(--err)',
        }}>{err}</div>
      )}
      <div style={{ flex: 1, overflow: 'auto', background: 'var(--bg-3)' }}>
        {header && (
          <pre style={{
            margin: 0, padding: '10px 14px',
            fontFamily: 'var(--code-font, var(--mono))', fontSize: 11, lineHeight: 1.55,
            color: 'var(--fg-mute)',
            whiteSpace: 'pre-wrap',
            borderBottom: patch ? '1px solid var(--line)' : 'none',
            background: 'var(--bg-2)',
          }}>{header}</pre>
        )}
        {patch ? (
          <pre className="tool-output-pre tool-output-diff language-none" style={{
            margin: 0, padding: '8px 0',
            fontFamily: 'var(--code-font, var(--mono))', fontSize: 11, lineHeight: 1.55,
            background: 'transparent',
          }}>
            {patch.split('\n').map((line, i) => {
              let cls = 'diff-line';
              if (line.startsWith('+') && !line.startsWith('+++')) cls += ' add';
              else if (line.startsWith('-') && !line.startsWith('---')) cls += ' del';
              return <div className={cls} key={i}>{line || ' '}</div>;
            })}
          </pre>
        ) : null}
      </div>
    </div>
  );
};

// ── File viewer modal — fetches real content from /api/file ────────
const FileViewer = ({ name, onClose }) => {
  const [body, setBody] = React.useState('# loading…');
  const [size, setSize] = React.useState(0);
  const [truncated, setTruncated] = React.useState(false);
  const [err, setErr] = React.useState(null);
  const ext = (name.split('.').pop() || '').toLowerCase();

  React.useEffect(() => {
    const onEsc = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onEsc);
    return () => window.removeEventListener('keydown', onEsc);
  }, [onClose]);

  React.useEffect(() => {
    let cancelled = false;
    setBody('# loading…'); setErr(null);
    window.atlasData.fetchFile(name).then(d => {
      if (cancelled) return;
      if (d.error) {
        setErr(d.error);
        setBody(`// ${name}\n// (could not read: ${d.error})`);
        return;
      }
      setBody(d.content || '');
      setSize(d.size || 0);
      setTruncated(!!d.truncated);
    }).catch(e => {
      if (!cancelled) {
        setErr(String(e));
        setBody(`// ${name}\n// (fetch failed: ${e})`);
      }
    });
    return () => { cancelled = true; };
  }, [name]);

  const lineCount = body.split('\n').length;
  const sizeKb = size > 0 ? (size / 1024).toFixed(1) + ' KB' : '';

  const copyPath = () => {
    try { navigator.clipboard.writeText(name); } catch (_) {}
  };

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 40,
    }}>
      <div onClick={(e) => e.stopPropagation()} className="box" style={{
        width: 'min(900px, 100%)', height: 'min(680px, 100%)',
        display: 'flex', flexDirection: 'column', background: 'var(--bg)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.45)',
      }}>
        <div className="box-h" style={{ padding: '8px 14px' }}>
          <span style={{ color: 'var(--fg-mute)', marginRight: 6 }}>◆</span>
          <span style={{ color: 'var(--fg)' }}>{name}</span>
          <span className="mute" style={{ marginLeft: 10, textTransform: 'none', letterSpacing: 0, fontSize: 11 }}>
            · {ext || 'file'} · read-only{sizeKb ? ` · ${sizeKb}` : ''}{truncated ? ' · truncated' : ''}
          </span>
          <span style={{ flex: 1 }} />
          <button className="btn" onClick={onClose} style={{ fontSize: 11 }}>Close <Kbd>Esc</Kbd></button>
        </div>
        <pre className="code" style={{
          flex: 1, overflow: 'auto', padding: 16, margin: 0, fontSize: 12, lineHeight: 1.55,
          whiteSpace: 'pre', color: err ? 'var(--warn)' : 'var(--fg)',
        }}>{body}</pre>
        <div style={{ borderTop: '1px solid var(--line)', padding: '8px 14px', display: 'flex', gap: 8, fontSize: 11 }}>
          <span className="mute">{lineCount} lines{truncated ? ' (truncated)' : ''}</span>
          <span style={{ flex: 1 }} />
          <button className="btn" onClick={copyPath}>Copy path</button>
        </div>
      </div>
    </div>
  );
};

// ── conversation hydration mode (left column footer) ───────────────
// Picks which on-disk source the chat feed is rebuilt from on a
// session refresh / page reload. The mode is persisted in
// localStorage and read by data.jsx's refreshSessionState which
// passes it through as a `mode` query param to /api/session/state.
//   • conversation  — recent rolling window (conversation.json). Default.
//   • full          — every message ever (full_conversation.json).
//   • recent        — last 50 messages of full_conversation.json.
const ConvModeSelector = () => {
  const initial = (() => {
    try { return localStorage.getItem('atlasConversationMode') || 'conversation'; }
    catch (_) { return 'conversation'; }
  })();
  const [mode, setMode] = React.useState(initial);
  const apply = (next) => {
    setMode(next);
    try { localStorage.setItem('atlasConversationMode', next); } catch (_) {}
    if (window.atlasData && window.atlasData.refreshSessionState) {
      window.atlasData.refreshSessionState(window.ACTIVE_SESSION || '', true, { mode: next });
    }
  };
  const Pill = ({ id, label, title }) => (
    <span
      onClick={() => apply(id)}
      title={title}
      style={{
        cursor: 'pointer',
        padding: '2px 6px',
        fontSize: 10,
        fontFamily: 'var(--mono)',
        letterSpacing: '0.02em',
        textTransform: 'uppercase',
        color: mode === id ? 'var(--bg)' : 'var(--fg-mute)',
        background: mode === id ? 'var(--accent)' : 'transparent',
        border: '1px solid ' + (mode === id ? 'var(--accent)' : 'var(--line)'),
        borderRadius: 2,
        whiteSpace: 'nowrap',
        flex: '0 0 auto',
      }}
    >{label}</span>
  );
  return (
    <div style={{
      // Sit a little above the bottom edge of the left column so the
      // pills don't visually merge with the splitter line.
      marginBottom: 24,
      border: '1px solid var(--line)',
      borderRadius: 2,
      padding: '6px 8px',
      fontSize: 10, color: 'var(--fg-mute)',
      display: 'flex', alignItems: 'center', gap: 4,
      // No flexWrap — keep all three pills on one row even in a narrow
      // left column. Drop the "history" label text so the pills get
      // every available pixel without wrapping `full` to a new line.
      flexWrap: 'nowrap',
      overflow: 'hidden',
    }}
    title="Conversation hydration source on session reload">
      <Pill id="conversation" label="recent" title="conversation.json — recent rolling window (default)" />
      <Pill id="full"         label="full"   title="every message from full_conversation.json" />
    </div>
  );
};

// ── ATLAS status panel ─────────────────────────────────────────────
const AgentStatusPanel = ({ intent, workflow, onCollapse }) => {
  // Live context — populated by /healthz + WS 'context' events.
  const _ctx = window.CONTEXT || {};
  const [liveStageStatus, setLiveStageStatus] = React.useState(null);
  const effortOptions = ['none', 'low', 'medium', 'high', 'xhigh'];
  const normalizeEffortValue = (value) => (
    effortOptions.includes(String(value || '').toLowerCase())
      ? String(value || '').toLowerCase()
      : 'medium'
  );
  const modelOptions = Array.isArray(_ctx.modelOptions) ? _ctx.modelOptions : [];
  const modelKey =
    _ctx.selectedModelKey
    || ((modelOptions.find(m => m.model === _ctx.model) || modelOptions[0] || {}).key || '');
  const [effortValue, setEffortValue] = React.useState(normalizeEffortValue(_ctx.reasoningEffort));
  const [savingEffort, setSavingEffort] = React.useState(false);
  const [savingModel, setSavingModel] = React.useState(false);
  const [settingsError, setSettingsError] = React.useState('');
  React.useEffect(() => {
    setEffortValue(normalizeEffortValue(_ctx.reasoningEffort));
  }, [_ctx.reasoningEffort]);
  React.useEffect(() => {
    let alive = true;
    const refresh = () => {
      fetch('/api/soc')
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          if (!alive || !d) return;
          const mods = (d.clusters || []).flatMap(c => Array.isArray(c.modules) ? c.modules : []);
          const scoped = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
          const preferred = mods.find(m => scoped && (m.id === scoped || m.ip_dir === scoped)) || mods[0];
          setLiveStageStatus((preferred && preferred.status) || null);
        })
        .catch(() => {});
    };
    refresh();
    const timer = setInterval(refresh, 5000);
    window.addEventListener('atlas-data-changed', refresh);
    return () => {
      alive = false;
      clearInterval(timer);
      window.removeEventListener('atlas-data-changed', refresh);
    };
  }, []);
  const updateEffort = async (value) => {
    setEffortValue(value);
    setSavingEffort(true);
    setSettingsError('');
    try {
      const resp = await fetch('/api/settings/reasoning-effort', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ effort: value }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || data.ok === false) throw new Error(data.error || `HTTP ${resp.status}`);
      window.CONTEXT = Object.assign({}, window.CONTEXT || {}, {
        reasoningEffort: data.reasoning_effort || value,
      });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    } catch (err) {
      setSettingsError(String(err).replace(/^Error:\s*/, ''));
      setEffortValue((window.CONTEXT && window.CONTEXT.reasoningEffort) || _ctx.reasoningEffort || 'medium');
    } finally {
      setSavingEffort(false);
    }
  };
  const updateModel = async (key) => {
    if (!key) return;
    setSavingModel(true);
    setSettingsError('');
    try {
      const resp = await fetch('/api/settings/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok || data.ok === false) throw new Error(data.error || `HTTP ${resp.status}`);
      window.CONTEXT = Object.assign({}, window.CONTEXT || {}, {
        model: data.model || _ctx.model,
        modelOptions: Array.isArray(data.model_options) ? data.model_options : modelOptions,
        selectedModelKey: data.selected_model_key || key,
      });
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    } catch (err) {
      setSettingsError(String(err).replace(/^Error:\s*/, ''));
    } finally {
      setSavingModel(false);
    }
  };
  const ctxUsed = (_ctx.tokens || 0) / 1000;             // → K tokens
  const ctxMax  = Math.max(1, (_ctx.maxTokens || 1000000) / 1000);  // → K
  const pct = Math.min(100, Math.round((ctxUsed / ctxMax) * 100));
  const selectStyle = {
    width: '100%',
    minWidth: 0,
    maxWidth: '100%',
    height: 22,
    fontSize: 10,
  };
  return (
    <div className="box" style={{ flexShrink: 0 }}>
      <div className="box-h" style={{ padding: '6px 12px' }}>
        <span style={{ color: 'var(--accent)', fontWeight: 700 }}>ATLAS</span>
        <span style={{ flex: 1 }} />
        <span style={{
          fontSize: 9, padding: '1px 6px', borderRadius: 2,
          background: intent === 'plan' ? 'color-mix(in oklch, var(--warn) 25%, transparent)' : 'color-mix(in oklch, var(--cyan) 25%, transparent)',
          color: intent === 'plan' ? 'var(--warn)' : 'var(--cyan)',
          fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase',
        }}>{intent === 'plan' ? '◐ plan' : '● normal'}</span>
        {onCollapse && (
          <span
            onClick={onCollapse}
            title="collapse right panel (double-click splitter to restore)"
            className="mute"
            style={{ cursor: 'pointer', fontSize: 12, padding: '0 6px',
                     marginLeft: 6, userSelect: 'none' }}
          >›</span>
        )}
      </div>
      <div style={{ padding: '10px 14px', fontSize: 11, fontFamily: 'var(--mono)' }}>
        {/* Mode line */}
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 8 }}>
          <span className="mute">Mode</span>
          <span style={{ color: 'var(--fg)' }}>
            {intent === 'plan' ? 'Plan' : 'Normal'}
            <span className="mute"> · {workflow ? window.FLOW_STAGES.find(s => s.id === workflow)?.label : 'free chat'}</span>
          </span>
        </div>
        {/* Model */}
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4 }}>
          <span className="mute">Model</span>
          {modelOptions.length ? (
            <select
              className="dir-select"
              style={selectStyle}
              value={modelKey}
              disabled={savingModel}
              title={_ctx.model || ''}
              onChange={(ev) => updateModel(ev.currentTarget.value)}>
              {modelOptions.filter(opt => opt.model && !opt.model.toLowerCase().startsWith('default')).map(opt => (
                <option key={opt.key} value={opt.key}>
                  {opt.model}
                </option>
              ))}
            </select>
          ) : (
            <span style={{ color: 'var(--fg)' }} title={_ctx.baseUrl}>{_ctx.model || '—'}</span>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4 }}>
          <span className="mute">Effort</span>
          <select
            className="dir-select"
            style={selectStyle}
            value={effortValue}
            disabled={savingEffort}
            title={`reasoning_effort = ${effortValue}`}
            onChange={(ev) => updateEffort(ev.currentTarget.value)}>
            {effortOptions.map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        {settingsError && (
          <div style={{ marginLeft: 72, marginBottom: 6, color: 'var(--err)', fontSize: 10 }}>
            {settingsError}
          </div>
        )}
        {(_ctx.provider || _ctx.baseUrl) && (
          <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4, fontSize: 10 }}>
            <span className="mute">via</span>
            <span className="mute trunc" title={_ctx.baseUrl}>
              {_ctx.provider || ''}{_ctx.baseUrl ? ' · ' + _ctx.baseUrl.replace(/^https?:\/\//, '') : ''}
            </span>
          </div>
        )}
        {/* Context with bar */}
        <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr', gap: 8, marginBottom: 4, marginTop: 6 }}>
          <span className="mute">Context</span>
          <span>
            <span style={{ color: 'var(--fg)' }}>
              {ctxUsed >= 1000 ? (ctxUsed/1000).toFixed(2) + 'M' : ctxUsed.toFixed(1) + 'K'}
            </span>
            <span className="mute"> / {ctxMax >= 1000 ? (ctxMax/1000) + 'M' : ctxMax + 'K'} · </span>
            <span className={pct > 70 ? 'warn' : 'ok'}>{pct}%</span>
          </span>
        </div>
        <div style={{ marginLeft: 72, marginBottom: 10, height: 4, background: 'var(--bg-2)', borderRadius: 1, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${pct}%`,
            background: pct > 70 ? 'var(--warn)' : 'var(--accent)',
          }} />
        </div>
        {/* Cost ledger — live from /healthz + 'cost' WS events */}
        {(() => {
          const fmt = (n) => {
            if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
            if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
            return n.toFixed(0);
          };
          const usd = (n) => '$' + (n || 0).toFixed(4);
          const pi = _ctx.pricing ? _ctx.pricing.input  : 0;
          const pc = _ctx.pricing ? _ctx.pricing.cache  : 0;
          const po = _ctx.pricing ? _ctx.pricing.output : 0;
          const tiRaw = _ctx.tokensIn || 0;
          const tc = _ctx.tokensCache || 0;
          const to = _ctx.tokensOut   || 0;
          // tokensIn is raw prompt tokens from provider usage and includes
          // the cached subset. The ledger's Input row should show/bill only
          // uncached input; Cached is displayed and charged separately.
          const ti = Math.max(0, tiRaw - tc);
          const cIn   = ti * pi / 1e6;
          const cCach = tc * pc / 1e6;
          const cOut  = to * po / 1e6;
          const cTot  = cIn + cCach + cOut;
          return (
            <>
              <div className="mute" style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
                Cost {_ctx.pricing && (
                  <span className="mute" style={{ fontSize: 9, fontWeight: 400, letterSpacing: 0, textTransform: 'none', marginLeft: 4 }}>
                    @ ${pi}/${pc}/${po} per 1M
                  </span>
                )}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '64px 1fr 70px', gap: 4, fontSize: 11, lineHeight: 1.55 }}>
                <span className="mute">Input</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{fmt(ti)}</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{usd(cIn)}</span>

                <span className="mute">Cached</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{fmt(tc)}</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{usd(cCach)}</span>

                <span className="mute">Output</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{fmt(to)}</span>
                <span style={{ color: 'var(--fg)', textAlign: 'right' }}>{usd(cOut)}</span>

                <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--fg)', fontWeight: 600 }}>Total</span>
                <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--fg)', textAlign: 'right' }}>{fmt(ti + tc + to)}</span>
                <span style={{ borderTop: '1px solid var(--line)', paddingTop: 3, color: 'var(--ok)', textAlign: 'right', fontWeight: 600 }}>{usd(cTot)}</span>
              </div>
            </>
          );
        })()}

        {/* ── pipeline · ATLAS (this session) ─────────────────────── */}
        <div className="mute" style={{
          fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase',
          marginTop: 14, marginBottom: 6,
          display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap',
        }}>
          <span style={{ color: 'var(--accent)', fontWeight: 700 }}>▸ atlas</span>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>· session</span>
          <span style={{ flex: 1 }} />
          <span className="ok" style={{ fontSize: 9 }}>● live</span>
        </div>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4,
          fontSize: 10, marginBottom: 12,
        }}>
          {(() => {
            const st = liveStageStatus || {};
            const normalize = (v) => v === 'ok' || v === 'pass' ? 'done'
              : v === 'partial' || v === 'approved' || v === 'planned' || v === 'blocked' ? 'active'
              : v === 'err' || v === 'error' || v === 'fail' || v === 'rejected' ? 'err'
              : 'pending';
            const simDebugReady = st.sim_debug === 'ok' || (st.sim === 'ok' && (st.tb === 'ok' || st.tb === 'partial'));
            return [
              { id: 'ssot', label: 'SSOT', state: normalize(st.ssot) },
              { id: 'rtl',  label: 'RTL',  state: normalize(st.rtl) },
              { id: 'tb',   label: 'TB',   state: normalize(st.tb) },
              { id: 'dbg',  label: 'SIMDBG',  state: simDebugReady ? 'done' : normalize(st.sim_debug) },
            ];
          })().map(s => {
            const cfg = s.state === 'done'    ? { color: 'var(--ok)',     glyph: '✓', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)',     border: 'var(--ok)' }
                      : s.state === 'active'  ? { color: 'var(--accent)', glyph: '●', bg: 'color-mix(in oklch, var(--accent) 14%, transparent)', border: 'var(--accent)' }
                      : s.state === 'err'     ? { color: 'var(--err)',    glyph: '✗', bg: 'color-mix(in oklch, var(--err) 14%, transparent)',    border: 'var(--err)' }
                      :                         { color: 'var(--fg-mute)',glyph: '○', bg: 'transparent',                                          border: 'var(--line)' };
            return (
              <div key={s.id} style={{
                border: `1px solid ${cfg.border}`, borderRadius: 2,
                padding: '4px 6px', textAlign: 'center', background: cfg.bg,
                fontFamily: 'var(--mono)',
              }}>
                <div style={{ color: cfg.color, fontWeight: 700, fontSize: 10 }}>
                  {cfg.glyph} {s.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ── Hotkey footer (terminal-style) ─────────────────────────────────
const HotkeyFooter = ({ intent, streaming }) => (
  <div style={{
    display: 'flex', gap: 14, padding: '6px 12px', fontSize: 10,
    color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
    background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 2,
    alignItems: 'center', flexWrap: 'wrap',
  }}>
    <span style={{ color: 'var(--accent)', fontWeight: 600 }}>↑</span>
    <span>{(window.CONTEXT && window.CONTEXT.model) || '—'}</span>
    <span style={{ width: 1, height: 12, background: 'var(--line)' }} />
    <span><Kbd>shift+tab</Kbd> {intent === 'plan' ? 'normal' : 'plan'}</span>
    <span><Kbd>⌫⌫</Kbd> {streaming ? 'interrupt' : 'clear'}</span>
    <span><Kbd>ctrl+c</Kbd> quit</span>
    <span><Kbd>ctrl+j</Kbd> newline</span>
    <span><Kbd>shift+drag</Kbd> copy</span>
    <span><Kbd>shift+insert</Kbd> paste</span>
    <span style={{ flex: 1 }} />
    <span className={streaming ? 'acc' : 'ok'}>{streaming ? 'streaming…' : 'ready'}</span>
  </div>
);

window.Workspace = Workspace;
