// sim-debug-panels.tsx — TypeScript migration of the standalone presentational
// components extracted from sim-debug.jsx (strangler-fig split). These are the
// self-contained sub-components that lived between the helper cluster and the
// root SimDebug component (lines 230–843), plus the two props-only inner
// components (`Step4`, `Splitter`) that the legacy code defined INSIDE
// SimDebug but which close over nothing but their own props — moving them out
// is behavior-identical and shrinks the root file.
//
// Components: CocotbTreeView, SimResultBadge, SimSummaryPanel, TBHierarchyView,
//             RangeInput, SourceViewer, HierarchyNode, Step4, Splitter.
//
// Load order: included by index.html BEFORE sim-debug.tsx and AFTER
// sim-debug-helpers.tsx. The root component reads these back through
// `window.SimDebug*` bridges registered at the bottom (kept as window refs to
// avoid module-ordering issues — identical to the legacy cross-script-global
// behavior, where everything shared one in-browser-babel scope).
//
// Transitional: bridges to `window.*` at the bottom for not-yet-migrated .jsx.
import { useState, useRef, useEffect, useMemo, Fragment } from 'react';
import type { ReactNode, CSSProperties, MouseEvent as ReactMouseEvent } from 'react';
import {
  annotationAxesForMode,
  VERILOG_KEYWORDS,
  sourceLineIdentifiers,
  stripSignalRange,
  rawTimeToDisplay,
  displayTimeToRaw,
  resolveTimeDisplayUnit,
  formatTimeDisplay,
} from './sim-debug-helpers';

const caretTextAtPoint = (clientX: number, clientY: number): { node: Node; offset: number } | null => {
  const doc = document as Document & {
    caretRangeFromPoint?: (x: number, y: number) => Range | null;
    caretPositionFromPoint?: (x: number, y: number) => { offsetNode: Node; offset: number } | null;
  };
  if (doc.caretRangeFromPoint) {
    const r = doc.caretRangeFromPoint(clientX, clientY);
    if (r && r.startContainer.nodeType === 3) return { node: r.startContainer, offset: r.startOffset };
  } else if (doc.caretPositionFromPoint) {
    const p = doc.caretPositionFromPoint(clientX, clientY);
    if (p && p.offsetNode.nodeType === 3) return { node: p.offsetNode, offset: p.offset };
  }
  return null;
};

interface SourcePoint {
  line: number;
  offset: number;
  text: string;
}
interface SourceCodeSpan {
  start: number;
  end: number;
}

const SOURCE_IDENT_RE = /\b([A-Za-z_][A-Za-z0-9_$]*)\b(\s*\[[^\]\n]+\])?/g;

const verilogCodeSpansForLines = (lines: string[]): SourceCodeSpan[][] => {
  let inBlockComment = false;
  return lines.map(raw => {
    const text = String(raw || '');
    const spans: SourceCodeSpan[] = [];
    let i = 0;
    while (i < text.length) {
      if (inBlockComment) {
        const end = text.indexOf('*/', i);
        if (end < 0) return spans;
        inBlockComment = false;
        i = end + 2;
        continue;
      }
      const lineComment = text.indexOf('//', i);
      const blockComment = text.indexOf('/*', i);
      if (lineComment < 0 && blockComment < 0) {
        if (i < text.length) spans.push({ start: i, end: text.length });
        return spans;
      }
      if (lineComment >= 0 && (blockComment < 0 || lineComment < blockComment)) {
        if (i < lineComment) spans.push({ start: i, end: lineComment });
        return spans;
      }
      if (i < blockComment) spans.push({ start: i, end: blockComment });
      const end = text.indexOf('*/', blockComment + 2);
      if (end < 0) {
        inBlockComment = true;
        return spans;
      }
      i = end + 2;
    }
    return spans;
  });
};

const isInsideCodeSpan = (start: number, end: number, spans?: SourceCodeSpan[]): boolean =>
  !spans || spans.some(span => start >= span.start && end <= span.end);

const isVerilogNumericLiteralIdentifier = (text: string, start: number): boolean => {
  const before = text.slice(Math.max(0, start - 4), start);
  return /'\s*[sS]?$/.test(before);
};

const sourcePointAtPoint = (clientX: number, clientY: number): SourcePoint | null => {
  const caret = caretTextAtPoint(clientX, clientY);
  if (!caret) return null;
  const parent = caret.node.parentElement;
  const codeRoot = parent?.closest('[data-src-code]') as HTMLElement | null;
  const lineRoot = codeRoot?.closest('[data-ln]') as HTMLElement | null;
  if (!codeRoot || !lineRoot) return null;
  const line = Number(lineRoot.getAttribute('data-ln') || 0);
  if (!Number.isFinite(line) || line <= 0) return null;
  const walker = document.createTreeWalker(codeRoot, NodeFilter.SHOW_TEXT);
  let text = '';
  let globalOffset = -1;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const s = n.textContent || '';
    if (n === caret.node) globalOffset = text.length + Math.max(0, Math.min(caret.offset, s.length));
    text += s;
  }
  return globalOffset >= 0 ? { line, offset: globalOffset, text } : null;
};

const signalAtSourceOffset = (text: string, offset: number, codeSpans?: SourceCodeSpan[]): string => {
  const re = new RegExp(SOURCE_IDENT_RE.source, 'g');
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    const base = m[1];
    const full = `${base}${m[2] ? m[2].replace(/\s+/g, '') : ''}`;
    const start = m.index;
    const end = m.index + m[0].length;
    if (!isInsideCodeSpan(start, end, codeSpans)) continue;
    if (isVerilogNumericLiteralIdentifier(text, start)) continue;
    if (offset < start || offset > end) continue;
    return VERILOG_KEYWORDS.has(base.toLowerCase()) ? '' : full;
  }
  return '';
};

// Resolve the signal under a mouse event inside highlighted source. Unlike a
// plain identifier picker, this preserves a trailing Verilog bit/range select
// (`irq_status_o[5:0]`) and also works when the click lands inside the range.
const signalAtPoint = (clientX: number, clientY: number, lines?: string[]): string => {
  const point = sourcePointAtPoint(clientX, clientY);
  if (!point) return '';
  const src = Array.isArray(lines) ? lines : [point.text];
  const spansByLine = verilogCodeSpansForLines(src);
  const spans = Array.isArray(lines) ? spansByLine[point.line - 1] : spansByLine[0];
  return signalAtSourceOffset(point.text, point.offset, spans);
};

const sourceSignalsBetween = (lines: string[] | undefined, a: SourcePoint, b: SourcePoint): string[] => {
  const src = Array.isArray(lines) ? lines : [];
  const spansByLine = verilogCodeSpansForLines(src);
  const before = a.line < b.line || (a.line === b.line && a.offset <= b.offset) ? a : b;
  const after = before === a ? b : a;
  const seen = new Set<string>();
  const out: string[] = [];
  for (let lineNo = before.line; lineNo <= after.line; lineNo++) {
    const text = src[lineNo - 1] || '';
    const codeSpans = spansByLine[lineNo - 1] || [];
    const lo = lineNo === before.line ? Math.max(0, before.offset) : 0;
    const hi = lineNo === after.line ? Math.max(lo, Math.min(after.offset, text.length)) : text.length;
    const re = new RegExp(SOURCE_IDENT_RE.source, 'g');
    let m: RegExpExecArray | null;
    while ((m = re.exec(text))) {
      const base = m[1];
      const start = m.index;
      const end = m.index + m[0].length;
      if (end < lo || start > hi) continue;
      if (!isInsideCodeSpan(start, end, codeSpans)) continue;
      if (isVerilogNumericLiteralIdentifier(text, start)) continue;
      if (VERILOG_KEYWORDS.has(base.toLowerCase())) continue;
      const name = `${base}${m[2] ? m[2].replace(/\s+/g, '') : ''}`;
      const key = name.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(name);
    }
  }
  return out;
};

const clearBrowserTextSelection = () => {
  try { window.getSelection && window.getSelection()?.removeAllRanges(); } catch (_) {}
};

const sourceSelectionText = (root: HTMLElement | null): string => {
  const sel = window.getSelection ? window.getSelection() : null;
  const txt = String(sel || '');
  if (!txt.trim()) return '';
  if (!root || typeof sel?.rangeCount !== 'number' || typeof sel?.getRangeAt !== 'function') return txt;
  for (let i = 0; i < sel.rangeCount; i++) {
    const node = sel.getRangeAt(i).commonAncestorContainer;
    const el = node.nodeType === 1 ? node : node.parentNode;
    if (el && root.contains(el)) return txt;
  }
  return '';
};

const selectedSourceLeaf = (selectedSig?: string): string => {
  const leaf = stripSignalRange(selectedSig || '').split('.').pop() || '';
  if (!/^[A-Za-z_][A-Za-z0-9_$]*$/.test(leaf)) return '';
  return VERILOG_KEYWORDS.has(leaf.toLowerCase()) ? '' : leaf;
};

const selectedSourceRange = (selectedSig?: string): string => {
  const m = String(selectedSig || '').match(/(\[[^\]\n]+\])\s*$/);
  return m ? m[1].replace(/\s+/g, '') : '';
};

const markSelectedSourceSignal = (
  html: string,
  selectedLeaf: string,
  selectedRange = '',
  codeSpans?: SourceCodeSpan[],
): string => {
  if (!selectedLeaf) return html;
  const parts = html.split(/(<[^>]+>|&(?:[A-Za-z][A-Za-z0-9]+|#[0-9]+|#x[0-9A-Fa-f]+);)/g);
  const plainAfter = (idx: number): string => {
    let out = '';
    for (let i = idx; i < parts.length && out.length < 80; i++) {
      const p = parts[i] || '';
      if (p.startsWith('<')) continue;
      out += p;
    }
    return out;
  };
  let plainOffset = 0;
  return parts.map((part, idx) => {
    if (!part) return part;
    if (part.startsWith('<')) return part;
    if (part.startsWith('&')) {
      plainOffset += 1;
      return part;
    }
    const partOffset = plainOffset;
    const marked = part.replace(/\b([A-Za-z_][A-Za-z0-9_$]*)(\s*\[[^\]\n]+\])?/g, (match, word, directRange = '', pos) => {
      const start = partOffset + Number(pos);
      const end = start + String(match).length;
      if (!isInsideCodeSpan(start, end, codeSpans)) return match;
      if (isVerilogNumericLiteralIdentifier(part, Number(pos))) return match;
      if (word !== selectedLeaf) return match;
      if (selectedRange) {
        const normDirectRange = String(directRange || '').replace(/\s+/g, '');
        const after = normDirectRange ? String(directRange) : part.slice(Number(pos) + word.length) + plainAfter(idx + 1);
        const r = normDirectRange ? [String(directRange), String(directRange)] : after.match(/^\s*(\[[^\]\n]+\])/);
        if (!r || r[1].replace(/\s+/g, '') !== selectedRange) return match;
        if (normDirectRange) return `<span class="src-sig-hit">${word}${directRange}</span>`;
      }
      return `<span class="src-sig-hit">${word}</span>${directRange || ''}`;
    });
    plainOffset += part.length;
    return marked;
  }).join('');
};

// ── Cross-file globals owned by OTHER files / this family. Typed via a local
// view of `window`; behavior identical to the legacy implicit globals.
interface PrismLike {
  languages?: Record<string, unknown>;
  highlight?: (code: string, grammar: unknown, lang: string) => string;
  plugins?: { autoloader?: { loadLanguages?: (lang: string, cb: () => void) => void } };
}
interface SimDebugPanelsWindow {
  PRISM_LANG_MAP?: Record<string, string>;
  Prism?: PrismLike;
  SimDebugCocotbTreeView?: typeof CocotbTreeView;
  SimDebugSimResultBadge?: typeof SimResultBadge;
  SimDebugSimSummaryPanel?: typeof SimSummaryPanel;
  SimDebugTBHierarchyView?: typeof TBHierarchyView;
  SimDebugRangeInput?: typeof RangeInput;
  SimDebugSourceViewer?: typeof SourceViewer;
  SimDebugHierarchyNode?: typeof HierarchyNode;
  SimDebugStep4?: typeof Step4;
  SimDebugSplitter?: typeof Splitter;
}
const g = (typeof window !== 'undefined' ? window : ({} as Window)) as unknown as SimDebugPanelsWindow;

type OpenFileFn = (path: string, line?: number) => void;

// Cocotb (testbench) tree view — categorised file list + parsed
// results.xml summary. Click any file to load it in the source viewer.
interface CocotbFile { path: string; name: string; size: number }
interface CocotbCase {
  name?: string; classname?: string; status?: string;
  file?: string; line?: number; sim_time_ns?: string | number; time_s?: number;
}
interface CocotbResults {
  total?: number; pass?: number; fail?: number; skip?: number;
  cases?: CocotbCase[]; error?: string;
}
interface CocotbData {
  exists?: boolean; error?: string; results?: CocotbResults;
  tb_hierarchy?: TBHierarchy;
  tests?: CocotbFile[]; sequences?: CocotbFile[]; env?: CocotbFile[];
  agent?: CocotbFile[]; other?: CocotbFile[]; build?: CocotbFile[];
  [k: string]: unknown;
}
interface CocotbTreeViewProps {
  data: CocotbData | null | undefined;
  ipName: string;
  onOpenFile?: OpenFileFn;
}
const CocotbTreeView = ({ data, ipName, onOpenFile }: CocotbTreeViewProps) => {
  const [openSection, setOpenSection] = useState<Record<string, boolean>>({
    tests: true, sequences: true, env: true, agent: true, other: false, build: false,
  });
  const toggle = (k: string) => setOpenSection(s => ({ ...s, [k]: !s[k] }));

  if (!data) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                     color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', fontStyle: 'italic' }}>
        loading cocotb env…
      </div>
    );
  }
  if (data.error || !data.exists) {
    return (
      <div style={{ flex: 1, padding: 12, color: 'var(--fg-mute)', fontSize: 11 }}>
        no cocotb env at <code>{ipName}/cocotb/</code><br/>
        {data.error && <span style={{ color: 'var(--err)' }}>{data.error}</span>}
      </div>
    );
  }
  const r = data.results || {};
  const Sec = ({ k, label }: { k: string; label: string }) => {
    const items = (data[k] as CocotbFile[]) || [];
    if (!items.length) return null;
    return (
      <div style={{ marginBottom: 4 }}>
        <div
          onClick={() => toggle(k)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '3px 4px', cursor: 'pointer',
            color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.06em',
            textTransform: 'uppercase', userSelect: 'none',
          }}
        >
          <span style={{ width: 10 }}>{openSection[k] ? '▾' : '▸'}</span>
          <span>{label}</span>
          <span style={{ color: 'var(--fg-dim)' }}>({items.length})</span>
        </div>
        {openSection[k] && items.map(f => (
          <div
            key={f.path}
            onClick={() => onOpenFile && onOpenFile(f.path, 0)}
            style={{
              padding: '1px 4px 1px 22px', cursor: 'pointer',
              color: 'var(--fg)', fontSize: 'var(--ui-control-font-size)',
            }}
            title={f.path}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <span style={{ color: 'var(--fg-mute)' }}>·</span> {f.name}
            <span style={{ color: 'var(--fg-mute)', fontSize: 9, marginLeft: 4 }}>
              {f.size < 1024 ? f.size + 'B' : (f.size/1024).toFixed(1) + 'K'}
            </span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
      {/* Test result summary */}
      {r && r.total != null && (
        <div style={{
          padding: '6px 8px', marginBottom: 8,
          background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 3,
        }}>
          <div style={{
            color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em',
            textTransform: 'uppercase', marginBottom: 4,
          }}>results.xml</div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--ok)', fontWeight: 700 }}>✓ {r.pass}</span>
            <span style={{ color: 'var(--err)', fontWeight: 700 }}>✗ {r.fail}</span>
            <span style={{ color: 'var(--fg-mute)' }}>⊘ {r.skip}</span>
            <span style={{ color: 'var(--fg-mute)' }}>/ {r.total} total</span>
          </div>
          {r.cases && r.cases.length > 0 && (
            <div style={{ marginTop: 6 }}>
              {r.cases.slice(0, 12).map((c, i) => (
                <div
                  key={i}
                  onClick={() => c.file && onOpenFile && onOpenFile(c.file, c.line || 0)}
                  style={{ padding: '2px 0', cursor: c.file ? 'pointer' : 'default', display: 'flex', gap: 6 }}
                  title={c.file ? `${c.file}:${c.line}` : ''}
                >
                  <span style={{
                    color: c.status === 'pass' ? 'var(--ok)' : c.status === 'fail' ? 'var(--err)' : 'var(--fg-mute)',
                    width: 14,
                  }}>{c.status === 'pass' ? '✓' : c.status === 'fail' ? '✗' : '⊘'}</span>
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</span>
                  <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}>
                    {c.sim_time_ns ? `${parseFloat(String(c.sim_time_ns)).toFixed(0)}ns` : `${((c.time_s || 0)*1000).toFixed(0)}ms`}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      {r && r.error && (
        <div style={{ color: 'var(--err)', fontSize: 10, marginBottom: 8 }}>
          results.xml: {r.error}
        </div>
      )}
      {/* TB hierarchy — env / agent / scoreboard / sequence / test classes
          extracted via Python AST. Same role as RTL hierarchy from
          pyslang, but for the Pythonic testbench side. */}
      {data.tb_hierarchy && (
        <TBHierarchyView h={data.tb_hierarchy} onOpenFile={onOpenFile} />
      )}

      <Sec k="tests"     label="tests" />
      <Sec k="sequences" label="sequences" />
      <Sec k="env"       label="env" />
      <Sec k="agent"     label="agents" />
      <Sec k="other"     label="other" />
      <Sec k="build"     label="sim_build" />
    </div>
  );
};

const SimResultBadge = ({ status }: { status?: string }) => {
  const st = String(status || 'pending').toLowerCase();
  const color = st === 'pass' ? 'var(--ok)' : st === 'fail' ? 'var(--err)' : 'var(--warn)';
  const label = st === 'skip' ? 'pending' : st;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: 64, padding: '2px 8px', borderRadius: 3,
      border: '1px solid color-mix(in oklch, ' + color + ' 34%, var(--line))',
      background: 'color-mix(in oklch, ' + color + ' 12%, transparent)',
      color, fontFamily: 'var(--mono)', fontSize: 10, fontWeight: 800,
      letterSpacing: '0.06em', textTransform: 'uppercase',
    }}>{label}</span>
  );
};

interface SimTest {
  scenario_id?: string; name?: string; status?: string;
  pass_rows?: number; fail_rows?: number; expected?: string;
  checker?: string; source?: string;
}
interface SimSummaryData {
  tests?: SimTest[]; ssot_path?: string; sb_path?: string;
}
interface SimSummaryRow {
  id: string; name: string; status: string; evidence: string;
  expected: string; checker: string; source: string; file: string; line: number;
}
interface SimSummaryPanelProps {
  ipName: string;
  data: SimSummaryData | null | undefined;
  loading: boolean;
  error: string;
  cocotbData: CocotbData | null | undefined;
  onOpenFile?: OpenFileFn;
  onRefresh: () => void;
}
const SimSummaryPanel = ({ ipName, data, loading, error, cocotbData, onOpenFile, onRefresh }: SimSummaryPanelProps) => {
  const scenarioRows: SimSummaryRow[] = Array.isArray(data?.tests) ? data!.tests!.map((t, i) => ({
    id: t.scenario_id || `TC${i + 1}`,
    name: t.name || t.scenario_id || `TC${i + 1}`,
    status: t.status || 'pending',
    evidence: `${t.pass_rows || 0} pass / ${t.fail_rows || 0} fail`,
    expected: t.expected || '',
    checker: t.checker || '',
    source: t.source || 'ssot',
    file: '',
    line: 0,
  })) : [];
  const resultCases: SimSummaryRow[] = Array.isArray(cocotbData?.results?.cases)
    ? cocotbData!.results!.cases!.map((c, i) => ({
      id: c.name || `TC${i + 1}`,
      name: c.classname ? `${c.classname}.${c.name}` : (c.name || `TC${i + 1}`),
      status: c.status === 'skip' ? 'pending' : (c.status || 'pending'),
      evidence: c.sim_time_ns ? `${parseFloat(String(c.sim_time_ns || '0')).toFixed(0)} ns` : `${Math.round((c.time_s || 0) * 1000)} ms`,
      expected: '',
      checker: 'results.xml',
      source: 'results.xml',
      file: c.file || '',
      line: c.line || 0,
    }))
    : [];
  const rows = scenarioRows.length ? scenarioRows : resultCases;
  const counts = rows.reduce((acc, r) => {
    const st = r.status === 'skip' ? 'pending' : (r.status || 'pending');
    acc[st] = (acc[st] || 0) + 1;
    acc.total += 1;
    return acc;
  }, { pass: 0, fail: 0, pending: 0, total: 0 } as Record<string, number>);
  const evidencePaths = [
    data?.ssot_path,
    data?.sb_path,
    ipName ? `${ipName}/sim/results.xml` : '',
    ipName ? `${ipName}/tb/cocotb/results.xml` : '',
  ].filter(Boolean) as string[];

  const Stat = ({ label, value, color }: { label: string; value: ReactNode; color: string }) => (
    <div style={{
      minWidth: 118, padding: '10px 12px',
      border: '1px solid var(--line)', borderRadius: 4,
      background: 'var(--bg-2)',
    }}>
      <div style={{ color: 'var(--fg-mute)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ color, fontSize: 24, fontWeight: 800, fontFamily: 'var(--mono)', marginTop: 4 }}>{value}</div>
    </div>
  );

  return (
    <div style={{
      flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
      background: 'var(--panel)', color: 'var(--fg)',
    }}>
      <div style={{
        padding: '12px 14px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
            Sim Summary
          </div>
          <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginTop: 2, fontFamily: 'var(--mono)' }}>
            {ipName || '(no IP selected)'} · TC pass/fail
          </div>
        </div>
        <span style={{ flex: 1 }} />
        {loading && <span style={{ color: 'var(--accent)', fontSize: 10, fontFamily: 'var(--mono)' }}>loading</span>}
        <button className="btn" onClick={onRefresh} style={{ padding: '2px 8px', fontSize: 10 }}>refresh</button>
      </div>

      <div style={{ padding: 14, display: 'flex', gap: 10, flexWrap: 'wrap', borderBottom: '1px solid var(--line)' }}>
        <Stat label="pass" value={counts.pass || 0} color="var(--ok)" />
        <Stat label="fail" value={counts.fail || 0} color="var(--err)" />
        <Stat label="pending" value={counts.pending || 0} color="var(--warn)" />
        <Stat label="total" value={counts.total || 0} color="var(--fg)" />
      </div>

      {error && (
        <div style={{
          padding: '8px 14px', borderBottom: '1px solid var(--err)',
          background: 'color-mix(in oklch, var(--err) 10%, transparent)',
          color: 'var(--err)', fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)',
        }}>{error}</div>
      )}

      <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--line)', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {evidencePaths.length ? evidencePaths.map(p => (
          <button
            key={p}
            className="btn"
            onClick={() => onOpenFile && onOpenFile(p, 0)}
            title={p}
            style={{ padding: '2px 8px', fontSize: 10, fontFamily: 'var(--mono)' }}
          >{p.split('/').slice(-2).join('/')}</button>
        )) : (
          <span style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', fontFamily: 'var(--mono)' }}>no sim evidence files resolved</span>
        )}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 14 }}>
        {rows.length ? (
          <div style={{ border: '1px solid var(--line)', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{
              display: 'grid', gridTemplateColumns: 'minmax(120px, 0.9fr) minmax(220px, 1.4fr) 88px minmax(120px, 0.8fr) minmax(220px, 1.2fr)',
              gap: 0, padding: '7px 10px', background: 'var(--bg-2)',
              color: 'var(--fg-mute)', fontSize: 10, fontFamily: 'var(--mono)',
              letterSpacing: '0.07em', textTransform: 'uppercase', borderBottom: '1px solid var(--line)',
            }}>
              <span>TC</span><span>Name</span><span>Status</span><span>Evidence</span><span>Checker / Expected</span>
            </div>
            {rows.map((r, i) => (
              <div
                key={`${r.id}-${i}`}
                onClick={() => r.file && onOpenFile && onOpenFile(r.file, r.line || 0)}
                style={{
                  display: 'grid', gridTemplateColumns: 'minmax(120px, 0.9fr) minmax(220px, 1.4fr) 88px minmax(120px, 0.8fr) minmax(220px, 1.2fr)',
                  gap: 0, padding: '8px 10px', borderBottom: i === rows.length - 1 ? 'none' : '1px solid var(--line)',
                  background: i % 2 ? 'var(--bg)' : 'transparent',
                  cursor: r.file ? 'pointer' : 'default', alignItems: 'center',
                  fontSize: 'var(--ui-control-font-size)',
                }}
                title={r.file ? `${r.file}:${r.line || 0}` : ''}
              >
                <span style={{ fontFamily: 'var(--mono)', color: 'var(--cyan)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.id}</span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.name}</span>
                <SimResultBadge status={r.status} />
                <span style={{ fontFamily: 'var(--mono)', color: 'var(--fg-mute)' }}>{r.evidence || r.source}</span>
                <span style={{ color: 'var(--fg-mute)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {r.checker || r.expected || r.source || '-'}
                  {r.expected && r.checker ? ` · ${r.expected}` : ''}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{
            border: '1px solid var(--line)', borderRadius: 4,
            padding: 20, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12,
            background: 'var(--bg-2)',
          }}>
            {ipName
              ? `No TC rows yet for ${ipName}.`
              : 'Select IP_ID to load sim summary.'}
          </div>
        )}
      </div>
    </div>
  );
};

// TB class hierarchy — env → agents → drivers/monitors → sequencer →
// sequences. Plus tests at the top. Each entry clickable for source jump.
interface TBHierarchyEntry {
  name?: string; file?: string; line?: number;
  bases?: string[]; decorators?: string[];
}
interface TBHierarchy {
  envs?: TBHierarchyEntry[]; scoreboards?: TBHierarchyEntry[];
  agents?: TBHierarchyEntry[]; sequences?: TBHierarchyEntry[];
  tests?: TBHierarchyEntry[];
}
const TBHierarchyView = ({ h, onOpenFile }: { h: TBHierarchy; onOpenFile?: OpenFileFn }) => {
  const Group = ({ title, items, color }: { title: string; items?: TBHierarchyEntry[]; color?: string }) => {
    if (!items || !items.length) return null;
    return (
      <div style={{ marginBottom: 6 }}>
        <div style={{
          color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.06em',
          textTransform: 'uppercase', marginBottom: 2,
        }}>{title} ({items.length})</div>
        {items.map((x, i) => (
          <div
            key={i}
            onClick={() => onOpenFile && x.file && onOpenFile(x.file, x.line || 0)}
            style={{
              padding: '1px 4px 1px 12px', cursor: 'pointer',
              fontSize: 'var(--ui-control-font-size)', color: color || 'var(--fg)',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}
            title={`${x.file}:${x.line}` + (x.bases?.length ? ` extends ${x.bases.join(', ')}` : '')}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <span style={{ color: 'var(--fg-mute)' }}>·</span>{' '}
            <span>{x.name}</span>
            {x.bases && x.bases.length > 0 && (
              <span style={{ color: 'var(--fg-mute)', fontSize: 9 }}> ({x.bases.join(',').slice(0, 30)})</span>
            )}
            {x.decorators && x.decorators.length > 0 && (
              <span style={{ color: 'var(--magenta)', fontSize: 9 }}> @{x.decorators.join(',').replace(/cocotb\./g,'').slice(0, 22)}</span>
            )}
          </div>
        ))}
      </div>
    );
  };
  return (
    <div style={{
      marginBottom: 8, padding: '6px 8px',
      background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 3,
    }}>
      <div style={{
        color: 'var(--accent)', fontSize: 10, fontWeight: 700,
        letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6,
        borderBottom: '1px solid var(--line)', paddingBottom: 4,
      }}>TB hierarchy (cocotb / UVM)</div>
      <Group title="environment"  items={h.envs}        color="#7CFC4D" />
      <Group title="scoreboards"  items={h.scoreboards} color="#ffd24d" />
      <Group title="agents / BFM" items={h.agents}      color="#4dd0e1" />
      <Group title="sequences"    items={h.sequences}   color="#ff6bd0" />
      <Group title="@cocotb.test" items={h.tests}       color="#ffb84d" />
    </div>
  );
};

// Editable view-range input pair. User can type the start/end time
// directly to jump there. Blur or Enter commits; Esc reverts. Clamps
// to the VCD's full timeRange.
interface RangeInputVcd { timescale?: string; timeRange?: [number, number] }
interface RangeInputProps {
  effRange: [number, number];
  vcdData: RangeInputVcd | null | undefined;
  setViewRange: (range: [number, number]) => void;
  timeDisplayUnit?: string;
}
const RangeInput = ({ effRange, vcdData, setViewRange, timeDisplayUnit = 'auto' }: RangeInputProps) => {
  const ts = vcdData ? vcdData.timescale : 'ns';
  const unit = resolveTimeDisplayUnit(ts, timeDisplayUnit);
  const full = vcdData ? (vcdData.timeRange as [number, number]) : [0, 0];
  const fullSpan = (full[1] - full[0]) || 1;
  const viewSpan = effRange[1] - effRange[0];
  const zoomPct = (fullSpan / Math.max(1e-9, viewSpan)) * 100;
  const displayStart = rawTimeToDisplay(effRange[0], ts, unit);
  const displayEnd = rawTimeToDisplay(effRange[1], ts, unit);
  const displaySpan = rawTimeToDisplay(viewSpan, ts, unit);

  const inputNumber = (n: number) => Number.isInteger(n) ? String(n) : n.toFixed(3).replace(/\.?0+$/, '');
  const [startTxt, setStartTxt] = useState(inputNumber(displayStart));
  const [endTxt,   setEndTxt]   = useState(inputNumber(displayEnd));
  useEffect(() => { setStartTxt(inputNumber(displayStart)); }, [displayStart, unit]);
  useEffect(() => { setEndTxt  (inputNumber(displayEnd)); }, [displayEnd, unit]);

  const commit = () => {
    if (!vcdData) return;
    const a = displayTimeToRaw(startTxt, ts, unit), b = displayTimeToRaw(endTxt, ts, unit);
    if (Number.isNaN(a) || Number.isNaN(b)) return;
    const lo = Math.max(full[0], Math.min(a, b));
    const hi = Math.min(full[1], Math.max(a, b));
    if (hi - lo < 1) return;
    setViewRange([lo, hi]);
  };

  const inputStyle: CSSProperties = {
    background: '#0d1118',
    color: 'var(--accent)',
    border: '1px solid #2a3140',
    padding: '1px 4px',
    width: 80,
    fontSize: 10,
    fontFamily: 'var(--mono)',
    textAlign: 'right',
  };

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      marginRight: 8, fontFamily: 'var(--mono)', fontSize: 10,
      whiteSpace: 'nowrap',
    }} title={`view ${formatTimeDisplay(effRange[0], ts, unit)}–${formatTimeDisplay(effRange[1], ts, unit)}\nfull ${formatTimeDisplay(full[0], ts, unit)}–${formatTimeDisplay(full[1], ts, unit)}\nraw VCD unit ${ts}\nzoom ${zoomPct.toFixed(0)}%`}>
      <span style={{ color: 'var(--fg-mute)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>view</span>
      <input
        type="number"
        value={startTxt}
        onChange={e => setStartTxt(e.target.value)}
        onBlur={commit}
        onKeyDown={e => {
          if (e.key === 'Enter') { (e.target as HTMLInputElement).blur(); }
          if (e.key === 'Escape') { setStartTxt(inputNumber(displayStart)); (e.target as HTMLInputElement).blur(); }
          e.stopPropagation();
        }}
        style={inputStyle}
      />
      <span style={{ color: 'var(--fg-mute)' }}>–</span>
      <input
        type="number"
        value={endTxt}
        onChange={e => setEndTxt(e.target.value)}
        onBlur={commit}
        onKeyDown={e => {
          if (e.key === 'Enter') { (e.target as HTMLInputElement).blur(); }
          if (e.key === 'Escape') { setEndTxt(inputNumber(displayEnd)); (e.target as HTMLInputElement).blur(); }
          e.stopPropagation();
        }}
        style={inputStyle}
      />
      <span style={{ color: 'var(--fg-dim)' }}>{unit}</span>
      <span style={{ color: 'var(--fg-dim)', marginLeft: 4 }}>
        ({inputNumber(displaySpan)}{unit}) · {zoomPct >= 100 ? `×${(zoomPct/100).toFixed(1)}` : `${zoomPct.toFixed(0)}%`}
      </span>
      <span style={{ color: 'var(--fg-mute)', marginLeft: 4 }}>
        full {formatTimeDisplay(full[0], ts, unit)}–{formatTimeDisplay(full[1], ts, unit)}
      </span>
    </span>
  );
};

// Lightweight syntax-highlighted source viewer. Uses Prism (loaded
// globally from index.html — language autoloader fetches the grammar
// for the file extension on demand). Renders each line in its own
// row so line numbers + cursor highlight + per-line click work.
interface SourceViewerAnnotation { name: string; a: string; b: string }
interface SourceViewerProps {
  lines?: string[];
  cursor?: number;
  path?: string;
  selectedSig?: string;
  vcdAnnotations?: Record<number, SourceViewerAnnotation[]>;
  vcdAnnotationAxis?: string;
  // Clicking an identifier in the source picks it as the active signal; the
  // host wires these to focus / add-to-wave / a right-click signal menu.
  onPickSignal?: (name: string) => void;
  onAddSignal?: (name: string) => void;
  onSelectSignals?: (names: string[]) => void;
  // Drag identifiers from the source and release over the waveform → add them.
  onDropToWave?: (names: string[]) => void;
  // selSignals = identifiers found in the current text selection (drag-select a
  // code region → bulk-add all its signals).
  onSignalContextMenu?: (name: string, x: number, y: number, selSignals?: string[]) => void;
}
const SourceViewer = ({
  lines, cursor, path, selectedSig, vcdAnnotations = {}, vcdAnnotationAxis = 'both',
  onPickSignal, onAddSignal, onSelectSignals, onDropToWave, onSignalContextMenu,
}: SourceViewerProps) => {
  // A click/right-click on an identifier resolves the word under the cursor and
  // routes it to the matching handler. Keywords are ignored. Single-click only
  // fires when there is no active text selection (so drag-to-copy still works).
  const pickFromEvent = (clientX: number, clientY: number): string => {
    const w = signalAtPoint(clientX, clientY, lines);
    return w && !VERILOG_KEYWORDS.has(stripSignalRange(w).toLowerCase()) ? w : '';
  };
  const ref = useRef<HTMLDivElement>(null);
  const textSelectModeRef = useRef(false);
  const sourceDragRef = useRef<{
    start: SourcePoint;
    current: SourcePoint;
    startX: number;
    startY: number;
    moved: boolean;
  } | null>(null);
  const semanticDragJustSelectedRef = useRef(false);
  // Bump on every Prism load so we re-render once the grammar arrives.
  const [grammarTick, setGrammarTick] = useState(0);
  const [textSelectMode, setTextSelectMode] = useState(false);
  const [sourceDragSignals, setSourceDragSignals] = useState<string[]>([]);
  const annotationAxes = useMemo(
    () => annotationAxesForMode(vcdAnnotationAxis),
    [vcdAnnotationAxis],
  );
  const selectedLeaf = useMemo(() => selectedSourceLeaf(selectedSig), [selectedSig]);
  const selectedRange = useMemo(() => selectedSourceRange(selectedSig), [selectedSig]);

  // Resolve language id from extension via window.PRISM_LANG_MAP.
  const ext = (path || '').match(/\.([a-zA-Z0-9]+)$/)?.[1]?.toLowerCase() || '';
  const langId = (g.PRISM_LANG_MAP || {})[ext] || 'none';

  // Highlighted-per-line HTML. If Prism + the grammar are ready we run
  // it; otherwise we fall back to plain escaped text so the panel
  // never goes blank while the autoloader fetches.
  const baseLineHTMLs = useMemo(() => {
    if (!lines || lines.length === 0) return [];
    const fullCode = lines.join('\n');
    const Prism = g.Prism;
    if (Prism && Prism.languages && Prism.languages[langId]) {
      try {
        const html = Prism.highlight!(fullCode, Prism.languages[langId], langId);
        return html.split('\n');
      } catch (_) {/* fall through */}
    }
    // No grammar yet — escape and split. Trigger autoloader.
    if (Prism && Prism.plugins && Prism.plugins.autoloader && langId !== 'none') {
      Prism.plugins.autoloader.loadLanguages!(langId, () => setGrammarTick(t => t + 1));
    }
    return lines.map(ln =>
      ln.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    );
  }, [lines, langId, grammarTick]);
  const lineHTMLs = useMemo(() => {
    const codeSpansByLine = verilogCodeSpansForLines(lines || []);
    let htmls = selectedLeaf
      ? baseLineHTMLs.map((html, idx) => markSelectedSourceSignal(html, selectedLeaf, selectedRange, codeSpansByLine[idx]))
      : baseLineHTMLs;
    for (const sig of sourceDragSignals) {
      const leaf = selectedSourceLeaf(sig);
      const range = selectedSourceRange(sig);
      if (!leaf) continue;
      htmls = htmls.map((html, idx) => markSelectedSourceSignal(html, leaf, range, codeSpansByLine[idx]));
    }
    return htmls;
  }, [baseLineHTMLs, lines, selectedLeaf, selectedRange, sourceDragSignals]);

  useEffect(() => {
    if ((cursor || 0) > 0 && ref.current) {
      const el = ref.current.querySelector(`[data-ln="${cursor}"]`) as HTMLElement | null;
      if (el && el.scrollIntoView) el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }, [cursor, lines]);

  if (!lines || lines.length === 0) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                     color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', fontStyle: 'italic' }}>
        no source loaded — click a hierarchy module or a wave signal
      </div>
    );
  }
  return (
    <div
      ref={ref}
      className="src-viewer"
      onMouseDownCapture={e => {
        if (e.button !== 0) return;
        const allowNativeSelection = e.altKey;
        textSelectModeRef.current = allowNativeSelection;
        setTextSelectMode(allowNativeSelection);
        if (allowNativeSelection) return;
        clearBrowserTextSelection();
        e.preventDefault();
        const start = sourcePointAtPoint(e.clientX, e.clientY);
        if (!start) return;
        setSourceDragSignals([]);
        sourceDragRef.current = { start, current: start, startX: e.clientX, startY: e.clientY, moved: false };
        const onMove = (ev: MouseEvent) => {
          const drag = sourceDragRef.current;
          if (!drag) return;
          const next = sourcePointAtPoint(ev.clientX, ev.clientY);
          if (!next) return;
          drag.current = next;
          if (Math.abs(ev.clientX - drag.startX) > 3 || Math.abs(ev.clientY - drag.startY) > 3) {
            drag.moved = true;
            setSourceDragSignals(sourceSignalsBetween(lines, drag.start, next));
          }
        };
        const onUp = (ev: MouseEvent) => {
          window.removeEventListener('mousemove', onMove);
          window.removeEventListener('mouseup', onUp);
          const drag = sourceDragRef.current;
          sourceDragRef.current = null;
          if (drag?.moved) {
            semanticDragJustSelectedRef.current = true;
            const picked = sourceSignalsBetween(lines, drag.start, drag.current);
            setSourceDragSignals(picked);
            // Released over the waveform → ADD the dragged signals there instead
            // of merely selecting them in the source.
            const overWave = typeof document !== 'undefined'
              && typeof document.elementFromPoint === 'function'
              && !!(document.elementFromPoint(ev.clientX, ev.clientY) as HTMLElement | null)?.closest('.wave-panel');
            if (picked.length && overWave && onDropToWave) {
              onDropToWave(picked);
            } else if (picked.length && onSelectSignals) {
              onSelectSignals(picked);
            }
            setTimeout(() => { semanticDragJustSelectedRef.current = false; }, 0);
          }
        };
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);
      }}
      onMouseUpCapture={() => {
        if (!textSelectModeRef.current) clearBrowserTextSelection();
        setTimeout(() => {
          textSelectModeRef.current = false;
          setTextSelectMode(false);
        }, 0);
      }}
      onDragStart={e => {
        if (!textSelectModeRef.current) e.preventDefault();
      }}
      onClick={e => {
        if (!onPickSignal) return;
        if (semanticDragJustSelectedRef.current) {
          semanticDragJustSelectedRef.current = false;
          return;
        }
        if (window.getSelection && String(window.getSelection() || '').length) return; // don't fight drag-select
        const w = pickFromEvent(e.clientX, e.clientY);
        if (w) {
          setSourceDragSignals([]);
          onPickSignal(w);
        }
      }}
      onDoubleClick={e => {
        if (!onAddSignal) return;
        const w = pickFromEvent(e.clientX, e.clientY);
        if (w) {
          setSourceDragSignals([]);
          onAddSignal(w);
        }
      }}
      onContextMenu={e => {
        if (!onSignalContextMenu) return;
        const w = pickFromEvent(e.clientX, e.clientY);
        // Identifiers inside the current text selection → bulk add.
        const selText = sourceSelectionText(ref.current);
        const selSignals = sourceDragSignals.length
          ? sourceDragSignals
          : selText.trim()
          ? sourceLineIdentifiers(selText).filter(s => !VERILOG_KEYWORDS.has(s.toLowerCase()))
          : [];
        if (!w && selSignals.length === 0) return;  // nothing actionable → native menu
        e.preventDefault();
        e.stopPropagation();  // own the menu; don't let an ancestor handler also fire
        onSignalContextMenu(w, e.clientX, e.clientY, selSignals);
        // We already captured selSignals above. Clear the native browser text
        // selection so the source pane does not stay visually dimmed after the
        // menu opens or focus moves to the waveform.
        setTimeout(clearBrowserTextSelection, 0);
      }}
      style={{
      flex: 1, overflow: 'auto', padding: '6px 0',
      fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.45,
      background: 'var(--panel)',
      userSelect: textSelectMode ? 'text' : 'none',
    }}>
      {lineHTMLs.map((html, i) => {
        const lineNo = i + 1;
        const isCur = cursor === lineNo;
        const ann = vcdAnnotations[lineNo] || [];
        return (
          <Fragment key={i}>
            <div
              data-ln={lineNo}
              style={{
                display: 'grid',
                gridTemplateColumns: '46px 1fr',
                padding: '0 8px',
                background: isCur ? 'color-mix(in oklch, var(--accent) 18%, transparent)' : 'transparent',
                borderLeft: isCur ? '2px solid var(--accent)' : '2px solid transparent',
              }}
            >
              <span style={{
                color: isCur ? 'var(--accent)' : 'var(--fg-mute)',
                textAlign: 'right', paddingRight: 8, userSelect: 'none',
                fontSize: 10,
              }}>{lineNo}</span>
              <span
                data-src-code
                style={{ whiteSpace: 'pre' }}
                dangerouslySetInnerHTML={{ __html: html }}
              />
            </div>
            {ann.length > 0 && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: '46px 1fr',
                padding: '2px 8px 5px',
                borderLeft: '2px solid var(--cyan)',
                background: 'color-mix(in oklch, var(--cyan) 9%, transparent)',
              }}>
                <span style={{
                  color: 'var(--cyan)', textAlign: 'right', paddingRight: 8,
                  fontSize: 9, userSelect: 'none',
                }}>vcd</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {ann.map(item => (
                    <span key={item.name} style={{
                      border: '1px solid color-mix(in oklch, var(--cyan) 40%, var(--line))',
                      borderRadius: 3,
                      padding: '0 5px',
                      color: 'var(--fg)',
                      background: 'var(--bg)',
                      fontSize: 10,
                      whiteSpace: 'nowrap',
                    }}>
                      <b style={{ color: 'var(--cyan)' }}>{item.name}</b>
                      {annotationAxes.map(axis => (
                        <span
                          key={axis.id}
                          style={{ color: axis.color, marginLeft: 5 }}
                        >
                          {axis.label}={(item as unknown as Record<string, string>)[axis.key]}
                        </span>
                      ))}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </Fragment>
        );
      })}
    </div>
  );
};

// Recursive collapsible tree node for the instance hierarchy panel.
// Click on the chevron toggles children; click on the module name fires
// `onSelectModule` so SimDebug can load the matching SV source. The
// instance path stays foreground (accent), module name is cyan.
interface HierarchyTreeNode {
  name?: string; module?: string; cyclic?: boolean;
  children?: HierarchyTreeNode[];
}
interface HierarchyNodeProps {
  node: HierarchyTreeNode | null | undefined;
  depth: number;
  onSelectModule?: (moduleName?: string, instancePath?: string) => void;
  activeModule?: string;
}
const HierarchyNode = ({ node, depth, onSelectModule, activeModule }: HierarchyNodeProps) => {
  const [open, setOpen] = useState(depth < 2);
  if (!node) return null;
  const hasKids = (node.children || []).length > 0;
  const indent = depth * 14;
  const last = (node.name || '').split('.').pop();
  const isActive = activeModule === node.module;
  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `${indent + 14}px minmax(96px, 1fr) 20px minmax(128px, 1.15fr)`,
          alignItems: 'center',
          columnGap: 6,
          padding: '2px 6px 2px 0',
          color: 'var(--fg)',
          background: isActive ? 'color-mix(in oklch, var(--accent) 18%, transparent)' : 'transparent',
          borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
        }}
      >
        <span
          onClick={() => hasKids && setOpen(o => !o)}
          style={{
            justifySelf: 'end',
            color: 'var(--fg-mute)', fontSize: 9,
            cursor: hasKids ? 'pointer' : 'default',
          }}
        >
          {hasKids ? (open ? '▾' : '▸') : '·'}
        </span>
        <span
          onClick={() => onSelectModule && onSelectModule(node.module, node.name)}
          style={{
            color: 'var(--accent)', cursor: 'pointer',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}
          title="open module source"
        >{last}</span>
        <span style={{ color: 'var(--fg-mute)', justifySelf: 'center' }}>::</span>
        <span
          onClick={() => onSelectModule && onSelectModule(node.module, node.name)}
          style={{
            color: 'var(--cyan)', cursor: 'pointer',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}
          title="open module source"
        >{node.module}</span>
        {node.cyclic && (
          <span style={{ color: 'var(--err)', fontSize: 9, marginLeft: 4 }}>cyclic</span>
        )}
      </div>
      {open && hasKids && node.children!.map((c, i) => (
        <HierarchyNode key={i} node={c} depth={depth + 1}
          onSelectModule={onSelectModule} activeModule={activeModule} />
      ))}
    </div>
  );
};

// Compact step block — like V3's but lighter, since panels carry the evidence.
// (Defined inside SimDebug in the legacy file but closes over no state — props
// only — so it is extracted here unchanged.)
interface Step4Props {
  num?: ReactNode; kind?: string; tag?: ReactNode; when?: ReactNode;
  title?: ReactNode; args?: ReactNode; body?: ReactNode; done?: boolean;
  onClick?: () => void; active?: boolean;
}
const Step4 = ({ num, kind, tag, when, title, args, body, done, onClick, active }: Step4Props) => {
  const dotColor = ({
    thought: 'var(--magenta)',
    tool:    'var(--cyan)',
    action:  'var(--accent)',
    obs:     'var(--ok)',
  } as Record<string, string>)[kind || ''] || 'var(--fg-mute)';
  return (
    <div
      onClick={onClick}
      style={{
        display: 'grid',
        gridTemplateColumns: '32px 1fr',
        gap: 12,
        marginBottom: 14,
        cursor: onClick ? 'pointer' : 'default',
        padding: '6px 8px',
        borderRadius: 4,
        background: active ? 'color-mix(in oklch, var(--cyan) 8%, transparent)' : 'transparent',
        border: active ? '1px solid color-mix(in oklch, var(--cyan) 30%, var(--line))' : '1px solid transparent',
        transition: 'background 0.15s, border-color 0.15s',
      }}
    >
      <div style={{ position: 'relative', textAlign: 'center' }}>
        <div style={{
          width: 22, height: 22, borderRadius: '50%',
          background: 'var(--panel)',
          border: '1.5px solid ' + dotColor,
          color: dotColor,
          fontFamily: 'var(--mono)', fontSize: 9, fontWeight: 700,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '2px auto 0',
        }}>{num}</div>
        <div style={{
          position: 'absolute', left: '50%', top: 26, bottom: -14,
          width: 1, background: 'var(--line)', transform: 'translateX(-0.5px)',
        }} />
      </div>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
          <span style={{
            color: dotColor,
            fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase',
            fontWeight: 700, fontFamily: 'var(--mono)',
          }}>{tag}</span>
          {done && <span className="pill ok" style={{ fontSize: 8, padding: '0 4px' }}>done</span>}
          <span style={{ flex: 1 }} />
          <span style={{ color: 'var(--fg-mute)', fontSize: 9, fontFamily: 'var(--mono)' }}>{when}</span>
        </div>
        <div style={{ color: 'var(--fg)', fontSize: 12, fontWeight: 500, marginBottom: 3, lineHeight: 1.35 }}>
          {title}
        </div>
        {args && (
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 4 }}>
            ({args})
          </div>
        )}
        {body}
      </div>
    </div>
  );
};

// Drag handle between panels. Props-only; extracted unchanged from SimDebug.
interface SplitterProps {
  orient: 'v' | 'h';
  onMouseDown?: (e: ReactMouseEvent) => void;
  onDoubleClick?: () => void;
}
const Splitter = ({ orient, onMouseDown, onDoubleClick }: SplitterProps) => (
  <div
    onMouseDown={onMouseDown}
    onDoubleClick={onDoubleClick}
    style={{
      background: 'var(--line)',
      cursor: orient === 'v' ? 'col-resize' : 'row-resize',
      flexShrink: 0,
      ...(orient === 'v' ? { width: 4, height: '100%' } : { height: 4, width: '100%' }),
    }}
  />
);

export {
  CocotbTreeView, SimResultBadge, SimSummaryPanel, TBHierarchyView,
  RangeInput, SourceViewer, HierarchyNode, Step4, Splitter,
};
export type {
  CocotbData, CocotbFile, CocotbCase, CocotbResults,
  SimSummaryData, SimTest, SimSummaryRow,
  TBHierarchy, TBHierarchyEntry, HierarchyTreeNode,
  SourceViewerAnnotation, OpenFileFn,
};

// ── Transitional bridge: register on window so sim-debug.tsx (and any legacy
// consumer) resolves these. Namespaced to avoid colliding with workspace
// globals; the root component reads them back through these names.
if (typeof window !== 'undefined') {
  g.SimDebugCocotbTreeView = CocotbTreeView;
  g.SimDebugSimResultBadge = SimResultBadge;
  g.SimDebugSimSummaryPanel = SimSummaryPanel;
  g.SimDebugTBHierarchyView = TBHierarchyView;
  g.SimDebugRangeInput = RangeInput;
  g.SimDebugSourceViewer = SourceViewer;
  g.SimDebugHierarchyNode = HierarchyNode;
  g.SimDebugStep4 = Step4;
  g.SimDebugSplitter = Splitter;
}
