/* workspace-lint-coverage.tsx — strangler-fig migration slice of workspace.jsx.
 *
 * Owns:
 *   - YAML fold/highlight helpers: _buildFoldTree fold-range tree,
 *     _FOLD_KIND_COLOR palette, and the _splitYamlComment / _highlightYamlValue
 *     / _highlightYamlLine / _highlightYamlBlock syntax highlighters.
 *   - Lint report cards: LintToolResultCard + LintReportSummary (reads
 *     /api/lint/report).
 *   - Coverage report cards: coverageMetricText, CoverageMetricCell,
 *     CoverageToolCard, CoverageReportSummary (reads /reports/cov).
 *
 * INERT mirror: legacy workspace.jsx still serves the live app. Public exports
 * are consumed by sibling workspace-*.tsx modules and the root composer.
 */
import { useState, useEffect, useCallback } from 'react';

import { AtlasStatusBadge } from './workspace-report-status';
import { _escHtml } from './workspace-feed-cards';
import { ToolOutputPre } from './workspace-markdown-chips';
import { LintToolResultCard } from './lint-diagnostics';

export { LintToolResultCard } from './lint-diagnostics';
export { CoverageReportSummary, CoverageToolCard, CoverageMetricCell, coverageMetricText } from './coverage-report-summary';

export const _buildFoldTree = (ranges: any): any => {
  const sorted = (ranges || []).slice().sort((a: any, b: any) => {
    if (a.line_start !== b.line_start) return a.line_start - b.line_start;
    return b.line_end - a.line_end; // outer first
  });
  const root: any = { children: [], line_start: 0, line_end: 1e9 };
  const stack: any[] = [root];
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
export const _FOLD_KIND_COLOR: Record<string, string> = {
  module: '#88c', always_ff: '#cc8', always_comb: '#8cc',
  function: '#c8c', task: '#fa8', case: '#aca',
  initial: '#888', 'generate-loop': '#cca', 'generate-if': '#cca',
  instance: '#fa8',  // module instances stand out same as task — orange-pink
  section: '#88c', 'sub-section': '#cc8', item: '#8cc', scalar: '#a98',
  object: '#88c', array: '#8cc',
};

export const _splitYamlComment = (value: string): [string, string] => {
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

export const _highlightYamlValue = (value: string): string => {
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

export const _highlightYamlLine = (line: string): string => {
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

export const _highlightYamlBlock = (text: any): string =>
  String(text || '').split(/\r?\n/).map(_highlightYamlLine).join('\n');

// FoldablePane renders the file body as one <div class="line-row"> per
// source line, wrapping ranges from /api/fold-symbols in <details>.
// Supports:
//   • click ▾/▸ on a fold summary → toggle
//   • click 💬 button on a summary → dispatch atlas-fold-comment
//   • drag-select on line-number gutter → floating "Comment selection"

export const LintReportSummary = ({ ip, onSelectPath, onOpenDiagnostic }: any) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [tick, setTick] = useState(0);
  const [running, setRunning] = useState(false);

  const load = useCallback((refresh = false) => {
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

  useEffect(() => { load(false); }, [load, tick]);

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
      minWidth: 0,
      overflow: 'hidden',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <div style={{ minWidth: 0 }}>
          <div className="trunc" title="pyslang + verilator lint" style={{ fontWeight: 900, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 12 }}>
            pyslang + verilator lint
          </div>
          <div className="trunc" title={`${data?.resolved_ip || ip}${data?.timestamp ? ` · ${data.timestamp}` : ''}`} style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, marginTop: 2 }}>
            {data?.resolved_ip || ip} {data?.timestamp ? `· ${data.timestamp}` : ''}
          </div>
        </div>
        <span style={{ flex: 1, minWidth: 0 }} />
        {hasReport && <AtlasStatusBadge status={passed ? 'approved' : 'error'} label={passed ? 'clean' : 'issues'} compact />}
        <button
          className="btn"
          onClick={() => setTick(v => v + 1)}
          disabled={loading}
          style={{ padding: '2px 8px', fontSize: 10, flex: '0 0 auto' }}
        >refresh</button>
        <button
          className="btn"
          onClick={() => load(true)}
          disabled={running || loading}
          style={{ padding: '2px 8px', fontSize: 10, flex: '0 0 auto' }}
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8, minWidth: 0 }}>
            {[
              ['tool', data.tool || 'pyslang+verilator'],
              ['errors', data.errors ?? 0],
              ['warnings', data.warnings ?? 0],
              ['suppressions', data.suppression_violations ?? 0],
              ['style', data.style_violations ?? 0],
            ].map(([label, value]: any) => (
              <div key={label} style={{ border: '1px solid var(--line)', background: 'var(--panel)', borderRadius: 3, padding: '6px 8px', minWidth: 0 }}>
                <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
                <div className="trunc" title={String(value)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 13 }}>{value}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(360px, 100%), 1fr))', gap: 10, minWidth: 0 }}>
            {tools.map((result: any, idx: number) => (
              <LintToolResultCard
                key={`${result.tool || 'tool'}-${idx}`}
                result={result}
                onOpenDiagnostic={onOpenDiagnostic}
              />
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', minWidth: 0, overflow: 'hidden' }}>
            <button className="btn" onClick={() => data.report_path && onSelectPath?.(data.report_path)} style={{ padding: '2px 8px', fontSize: 10, flex: '0 0 auto' }}>
              open json
            </button>
            <button className="btn" onClick={() => data.log_path && onSelectPath?.(data.log_path)} disabled={!data.log_exists} style={{ padding: '2px 8px', fontSize: 10, flex: '0 0 auto' }}>
              open log
            </button>
            <span className="trunc" title={data.command || ''} style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, flex: '1 1 auto', minWidth: 0 }}>
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
