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

export const LintToolResultCard = ({ result, onOpenDiagnostic }: any) => {
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
        ].map(([label, value]: any) => (
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
          {diagnostics.slice(0, 5).map((d: any, idx: number) => (
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
            ].map(([label, value]: any) => (
              <div key={label} style={{ border: '1px solid var(--line)', background: 'var(--panel)', borderRadius: 3, padding: '6px 8px', minWidth: 0 }}>
                <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
                <div className="trunc" title={String(value)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 13 }}>{value}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
            {tools.map((result: any, idx: number) => (
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

export const coverageMetricText = (metric: any): string => {
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

export const CoverageMetricCell = ({ metric }: any) => {
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

export const CoverageToolCard = ({ tool, onSelectPath, onOpenDiagnostic }: any) => {
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
          {metrics.map((metric: any, idx: number) => <CoverageMetricCell key={`${tool?.id || 'tool'}-${idx}`} metric={metric} />)}
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
          {diagnostics.slice(0, 4).map((d: any, idx: number) => (
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
          {missingBins.slice(0, 5).map((bin: any, idx: number) => (
            <div key={idx} className="trunc" title={bin?.description || bin?.id || ''} style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
              {bin?.id || String(bin)}
            </div>
          ))}
        </div>
      )}
      {scopes.length > 0 && (
        <div style={{ borderTop: '1px solid var(--line)', paddingTop: 7, display: 'grid', gap: 4 }}>
          <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>lowest-toggle scopes</div>
          {scopes.slice(0, 5).map((scope: any, idx: number) => (
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

export const CoverageReportSummary = ({ ip, onSelectPath, onOpenDiagnostic }: any) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [running, setRunning] = useState('');
  const [tick, setTick] = useState(0);

  const load = useCallback((mode = '') => {
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

  useEffect(() => { load(''); }, [load, tick]);

  const tools = Array.isArray(data?.tools) ? data.tools : [];
  const artifacts = Array.isArray(data?.artifacts) ? data.artifacts : [];
  const vcdPaths = Array.isArray(data?.vcd_paths) ? data.vcd_paths : [];
  const missingTools = tools.filter((t: any) => !t.available).length;
  const runEntries = Object.entries(data?.run || {}).filter(([, value]: any) => value && value.output);

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
            ].map(([label, value]: any) => (
              <div key={label} style={{ border: '1px solid var(--line)', background: 'var(--panel)', borderRadius: 3, padding: '6px 8px', minWidth: 0 }}>
                <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
                <div className="trunc" title={String(value)} style={{ fontFamily: 'var(--mono)', fontWeight: 800, fontSize: 13 }}>{value}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(270px, 1fr))', gap: 10 }}>
            {tools.map((tool: any) => (
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
          {runEntries.map(([name, info]: any) => (
            <ToolOutputPre key={name} text={`${name}: rc ${info.returncode}\n${info.output || ''}`} tool="bash" />
          ))}
        </>
      )}
    </div>
  );
};
