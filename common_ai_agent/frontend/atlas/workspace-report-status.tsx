/* workspace-report-status.tsx — strangler-fig migration slice of workspace.jsx.
 *
 * Owns:
 *   - WORKFLOW_REPORT_TABS: workflow-report tab map (bridged to window for
 *     consumption by workflow-report.jsx).
 *   - ATLAS status metadata / normalization + AtlasStatusBadge component.
 *   - Workspace telemetry formatters/extractors.
 *   - Todo-tool text tally/cleaning + misc text helpers.
 *
 * INERT mirror: legacy workspace.jsx still serves the live app. Public exports
 * are consumed by sibling workspace-*.tsx modules and the root composer.
 */
import { type CSSProperties } from 'react';

import { cleanAtlasTerminalText } from './workspace-tool-theme';

export const WORKFLOW_REPORT_TABS: Record<string, any> = {
  orchestrator: {
    label: 'orchestrator',
    title: 'Orchestrator',
    folders: [],
    paths: () => [],
  },
  lint: {
    label: 'lint report',
    title: 'Lint Report',
    folders: ['lint'],
    paths: (ip: string) => [
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
    paths: (ip: string) => [
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
  sim: {
    label: 'sim report',
    title: 'Simulation Report',
    folders: ['sim', 'tb/cocotb', 'tb/cocotb/sim_build'],
    paths: (ip: string) => [
      `${ip}/sim/sim_summary.json`,
      `${ip}/sim/sim_report.md`,
      `${ip}/sim/sim_report.txt`,
      `${ip}/sim/results.xml`,
      `${ip}/sim/scoreboard_events.jsonl`,
      `${ip}/sim/${ip}.vcd`,
      `${ip}/sim/${ip}.fst`,
      `${ip}/tb/cocotb/results.xml`,
      `${ip}/tb/cocotb/sim_build/results.xml`,
      `${ip}/tb/cocotb/sim_build/${ip}.vcd`,
      `${ip}/tb/cocotb/sim_build/${ip}.fst`,
    ],
  },
  sim_debug: {
    label: 'sim_debug report',
    title: 'Simulation Debug Report',
    folders: ['sim', 'sim_debug', 'debug', 'logs'],
    paths: (ip: string) => [
      `${ip}/sim/sim_debug_report.md`,
      `${ip}/sim/fl_rtl_compare.json`,
      `${ip}/sim/mismatch_classification.json`,
      `${ip}/sim/scoreboard_events.jsonl`,
      `${ip}/sim/sim_summary.json`,
      `${ip}/sim/${ip}.vcd`,
      `${ip}/sim/${ip}.fst`,
      `${ip}/sim_debug/sim_debug_report.md`,
    ],
  },
  syn: {
    label: 'syn_report',
    title: 'Synthesis Report',
    folders: ['syn', 'reports/synth'],
    paths: (ip: string) => [
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
    paths: (ip: string) => [
      `${ip}/sta/out/sta.report.md`,
      `${ip}/sta/out/wns.json`,
      `${ip}/sta/out/timing.rpt`,
      `${ip}/sta/out/setup.rpt`,
      `${ip}/sta/out/hold.rpt`,
      `${ip}/sta/out/sta.log`,
      `${ip}/reports/sta/timing.json`,
    ],
  },
  'sta-post': {
    label: 'sta_post_report',
    title: 'Post-Route STA Report',
    folders: ['sta-post', 'sta_post', 'sta', 'reports/sta-post', 'reports/sta_post', 'signoff'],
    paths: (ip: string) => [
      `${ip}/sta-post/out/sta.report.md`,
      `${ip}/sta-post/out/sta_post.report.md`,
      `${ip}/sta-post/out/wns.json`,
      `${ip}/sta-post/out/timing.rpt`,
      `${ip}/sta-post/out/setup.rpt`,
      `${ip}/sta-post/out/hold.rpt`,
      `${ip}/sta-post/out/skew.rpt`,
      `${ip}/sta-post/out/sta.log`,
      `${ip}/sta/sta_post_report.md`,
      `${ip}/sta/out/sta_post.report.md`,
      `${ip}/sta/out/sta-post.report.md`,
      `${ip}/reports/sta-post/timing.json`,
      `${ip}/reports/sta_post/timing.json`,
    ],
  },
  pnr: {
    label: 'pnr_report',
    title: 'PNR Report',
    folders: ['pnr', 'reports/pnr'],
    paths: (ip: string) => [
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
    paths: (ip: string) => [
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
WORKFLOW_REPORT_TABS['sim-debug'] = WORKFLOW_REPORT_TABS.sim_debug;
WORKFLOW_REPORT_TABS.sta_post = WORKFLOW_REPORT_TABS['sta-post'];
(window as any).WORKFLOW_REPORT_TABS = WORKFLOW_REPORT_TABS;  // Phase 13b: consumed by workflow-report.jsx

// Detect success/error in a tool result body. Used by ObsCard to
// stamp a leading ✓/✗ badge + override border color on errors.
export const _obsStatus = (txt: string): 'err' | 'ok' | 'neutral' => {
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

export const ATLAS_STATUS_META: Record<string, { glyph: string; color: string; label: string }> = {
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

export const normalizeAtlasStatus = (status: any): string => {
  const s = String(status || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
  if (s === 'in_progress' || s === 'inprogress') return 'in_progress';
  if (s === 'needs_review' || s === 'needsreview') return 'needs_review';
  if (s === 'fail' || s === 'failed' || s === 'err') return 'error';
  if (s === 'ok' || s === 'pass' || s === 'passed') return 'approved';
  return s || 'pending';
};

export const atlasStatusMeta = (status: any): { glyph: string; color: string; label: string } => {
  const key = normalizeAtlasStatus(status);
  return ATLAS_STATUS_META[key] || { glyph: '·', color: 'var(--fg-mute)', label: String(status || 'unknown') };
};

export const formatWorkspaceTelemetryNumber = (value: any): string => {
  const n = Number(value || 0);
  if (!Number.isFinite(n) || n <= 0) return '0';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n >= 10_000_000 ? 1 : 2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n >= 100_000 ? 0 : 1)}K`;
  return String(Math.round(n));
};

export const formatWorkspaceUsd = (value: any): string => {
  const n = Number(value || 0);
  if (!Number.isFinite(n) || n <= 0) return '$0.0000';
  if (n >= 10) return `$${n.toFixed(2)}`;
  if (n >= 1) return `$${n.toFixed(3)}`;
  return `$${n.toFixed(4)}`;
};

export const workspaceMessageText = (content: any): string => {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content.map((c: any) => {
      if (typeof c === 'string') return c;
      if (!c || typeof c !== 'object') return '';
      return c.text || c.content || c.value || '';
    }).join('');
  }
  return '';
};

export const workspaceToolArgValueText = (value: any): string => {
  try {
    const text = JSON.stringify(value);
    return text === undefined ? String(value) : text;
  } catch (_) {
    return String(value);
  }
};

export const workspaceToolArgsText = (args: any): string => {
  if (typeof args === 'string') {
    const raw = args.trim();
    if (raw.startsWith('{') && raw.endsWith('}')) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          return workspaceToolArgsText(parsed);
        }
      } catch (_) {}
    }
    return args;
  }
  if (args && typeof args === 'object' && !Array.isArray(args)) {
    return Object.entries(args)
      .map(([k, v]) => `${k}=${workspaceToolArgValueText(v)}`)
      .join(', ');
  }
  return args == null ? '' : String(args);
};

export const workspaceTelemetryFromMessages = (messages: any): { count: number; last: string; status: string; result: string } => {
  const out = { count: 0, last: '', status: '', result: '' };
  for (const m of (Array.isArray(messages) ? messages : [])) {
    const role = m && m.role;
    if (role === 'assistant') {
      if (Array.isArray(m.tool_calls)) {
        for (const tc of m.tool_calls) {
          const name = (tc && tc.function && tc.function.name) || (tc && tc.name) || '';
          out.count += 1;
          out.last = name || out.last || 'tool';
          out.status = 'running';
        }
      }
      const text = workspaceMessageText(m.content);
      const matches = text.matchAll(/^▶\s*(\S+)/gm);
      for (const match of matches) {
        out.count += 1;
        out.last = match[1] || out.last || 'tool';
        out.status = 'running';
      }
    } else if (role === 'tool') {
      const text = workspaceMessageText(m.content);
      const firstLine = text.split('\n').find((line: string) => line.trim()) || '';
      const failed = /\b(error|traceback|exception|failed|fatal|exit code [1-9])\b/i.test(text);
      out.last = m.name || out.last || 'tool';
      out.status = failed ? 'error' : 'ok';
      out.result = firstLine;
    }
  }
  return out;
};

export const AtlasStatusBadge = ({ status, label, count, compact = false, soft = false, title }: any) => {
  const meta = atlasStatusMeta(status);
  const text = label || meta.label;
  return (
    <span
      className={`atlas-status-badge${compact ? ' compact' : ''}${soft ? ' soft' : ''}`}
      style={{ '--status-color': meta.color } as CSSProperties}
      title={title || text}
    >
      <span className="atlas-status-dot">{meta.glyph}</span>
      <span>{count != null ? `${count} ${text}` : text}</span>
    </span>
  );
};

export const _limitAtlasLines = (text: any, maxLines = 5): string => {
  const lines = String(text || '').split(/\r?\n/).map((l: string) => l.trimEnd());
  const clean = lines.filter((l: string) => l.trim());
  if (clean.length <= maxLines) return clean.join('\n');
  return clean.slice(0, maxLines).join('\n') + `\n... (+${clean.length - maxLines} more)`;
};

export const TODO_TOOL_RE = /^todo_(write|update|add|remove|status|note)$/i;
export const TODO_STEP_TOOL_RE = /^(?:todo|step)_(write|update|add|remove|status|note)$/i;
export const TODO_STATUS_MARKS: Record<string, string> = {
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

export const _todoStatusTally = (txt: any): Record<string, number> => {
  const tally: Record<string, number> = {};
  const statusRe = /^\s*(⏸|▶|👀|✅|❌|\[\s?\]|\[>\]|\[\.]|\[v\]|\[x\])\s/gm;
  let mm: RegExpExecArray | null;
  while ((mm = statusRe.exec(String(txt || ''))) !== null) {
    const k = TODO_STATUS_MARKS[mm[1]];
    if (k) tally[k] = (tally[k] || 0) + 1;
  }
  return tally;
};

export const _todoTallyLine = (tally: Record<string, number>): string =>
  ['in-progress', 'pending', 'completed', 'approved', 'rejected']
    .filter(k => tally[k])
    .map(k => `${tally[k]} ${k}`)
    .join(' · ');

export const _cleanTodoToolText = (text: any, tool: any): string => {
  let txt = cleanAtlasTerminalText(text).trim();
  if (!TODO_STEP_TOOL_RE.test(String(tool || ''))) return txt;

  const tally = _todoStatusTally(txt);
  const tallyStr = _todoTallyLine(tally);
  txt = txt.replace(/\n\s*── TODO ──[\s\S]*$/m, '').trim();
  txt = txt.replace(/\n\s*--- TODO ---[\s\S]*$/m, '').trim();

  let m = txt.match(/^[✅\[]?v?\]?\s*Task\s+(\d+)\s+approved\.\s*\[([\s\S]*?)\]\s*([\s\S]*)$/i);
  if (m) {
    const next = (m[3] || '').split(/\r?\n/).map((l: string) => l.trim()).filter((l: string) => /^→?\s*Next:/i.test(l))[0] || '';
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

export type TodoStepUpdateInfo = {
  readonly operation: string;
  readonly index: string;
  readonly fromStatus: string;
  readonly toStatus: string;
  readonly title: string;
  readonly reasonLabel: string;
  readonly reason: string;
  readonly next: string;
  readonly note: string;
  readonly tally: string;
  readonly rawSummary: string;
};

const _todoStepOperation = (tool: unknown): string => {
  const match = String(tool || '').trim().match(TODO_STEP_TOOL_RE);
  return match ? String(match[1] || '').toLowerCase() : '';
};

const _unescapeTodoArg = (value: string): string =>
  value.replace(/\\"/g, '"').replace(/\\'/g, "'").replace(/\\n/g, '\n').trim();

const _todoToolArg = (text: string, name: string): string => {
  const safe = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`(?:^|[\\s,(])${safe}\\s*=\\s*(?:"((?:[^"\\\\]|\\\\.)*)"|'((?:[^'\\\\]|\\\\.)*)'|([^,\\n)]+))`, 'i');
  const match = text.match(re);
  if (!match) return '';
  return _unescapeTodoArg(String(match[1] || match[2] || match[3] || ''));
};

const _firstTodoMatch = (text: string, patterns: readonly RegExp[]): string => {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) return String(match[1]).trim();
  }
  return '';
};

export const _formatTodoStepStatus = (status: unknown): string => atlasStatusMeta(status).label;

const _todoStepReasonLabel = (status: string, operation: string): string => {
  const normalized = normalizeAtlasStatus(status);
  if (normalized === 'approved') return 'Approved';
  if (normalized === 'rejected') return 'Rejected';
  if (normalized === 'completed') return 'Review';
  if (normalized === 'in_progress') return 'Started';
  if (normalized === 'pending') return 'Pending';
  if (normalized === 'blocked') return 'Blocked';
  if (normalized === 'error') return 'Error';
  if (operation === 'add') return 'Added';
  if (operation === 'remove') return 'Removed';
  if (operation === 'note') return 'Note';
  return 'Detail';
};

const _todoStepTransition = (text: string): { readonly index: string; readonly fromStatus: string; readonly toStatus: string } => {
  const match = text.match(/#\s*(\d+)\s+([A-Za-z][A-Za-z0-9_-]*)\s*(?:->|→)\s*([A-Za-z][A-Za-z0-9_-]*)/i);
  if (!match) return { index: '', fromStatus: '', toStatus: '' };
  return {
    index: String(match[1] || '').trim(),
    fromStatus: normalizeAtlasStatus(match[2]),
    toStatus: normalizeAtlasStatus(match[3]),
  };
};

export const _parseTodoStepUpdate = (text: unknown, tool: unknown, actionText: unknown = ''): TodoStepUpdateInfo | null => {
  const toolText = String(tool || '').trim();
  if (!TODO_STEP_TOOL_RE.test(toolText)) return null;

  const operation = _todoStepOperation(toolText);
  const rawObs = cleanAtlasTerminalText(text).trim();
  const rawAction = cleanAtlasTerminalText(actionText).trim();
  const cleaned = _cleanTodoToolText(rawObs, toolText);
  const combined = [rawAction, rawObs, cleaned].filter(Boolean).join('\n');
  const transition = _todoStepTransition(combined);
  const actionStatus = normalizeAtlasStatus(_todoToolArg(rawAction, 'status'));
  const index = _todoToolArg(rawAction, 'index')
    || _todoToolArg(rawAction, 'id')
    || transition.index
    || _firstTodoMatch(combined, [
      /\bTask\s+(\d+)\b/i,
      /\bto\s+Task\s+(\d+)\b/i,
      /\bindex\s*=\s*(\d+)\b/i,
    ]);
  const tally = _todoTallyLine(_todoStatusTally(rawObs || cleaned));
  const nextLine = combined.split(/\r?\n/)
    .map((line: string) => line.trim())
    .find((line: string) => /^→?\s*Next:/i.test(line)) || '';
  const next = nextLine.replace(/^→?\s*Next:\s*/i, '').trim();

  let toStatus = transition.toStatus || actionStatus;
  let fromStatus = transition.fromStatus;
  let title = '';
  let reason = _todoToolArg(rawAction, 'reason');
  let note = '';
  let rawSummary = _limitAtlasLines(cleaned.replace(/\n\s*── TODO ──[\s\S]*$/m, '').trim(), 7);

  let match = rawObs.match(/Task\s+(\d+)\s+approved\.\s*\[([\s\S]*?)\]/i);
  if (match) {
    toStatus = 'approved';
    reason = String(match[2] || reason).trim();
  }

  match = rawObs.match(/Task\s+(\d+)\s+rejected:?\s*([\s\S]*)$/i);
  if (match) {
    toStatus = 'rejected';
    reason = String(match[2] || reason).trim();
  }

  match = rawObs.match(/Task\s+(\d+)\s+marked\s+completed\.\s*([\s\S]*)$/i);
  if (match) {
    toStatus = 'completed';
    reason = String(match[2] || reason).trim();
  }

  match = rawObs.match(/Task\s+(\d+)\s+in\s+progress:\s*([^\n]*)/i);
  if (match) {
    toStatus = 'in_progress';
    title = String(match[2] || '').trim();
  }

  match = rawObs.match(/Task\s+(\d+)\s+set\s+to\s+pending:\s*([^\n]*)/i);
  if (match) {
    toStatus = 'pending';
    title = String(match[2] || '').trim();
  }

  match = rawObs.match(/Task\s+(\d+)\s+\[command:\s*([^\]]+)\]\s+(passed|failed)\./i);
  if (match) {
    toStatus = String(match[3]).toLowerCase() === 'passed' ? 'completed' : 'rejected';
    reason = `command: ${String(match[2] || '').trim()}`;
  }

  match = rawObs.match(/Note\s+\[(\d+)\]\s+added\s+to\s+Task\s+\d+:\s*([\s\S]*)$/i);
  if (match) {
    toStatus = 'review';
    note = `[${String(match[1] || '').trim()}] ${_limitAtlasLines(match[2], 5)}`;
  }

  match = rawObs.match(/^Removed:\s*"([\s\S]*?)"/i);
  if (match) {
    toStatus = 'completed';
    title = String(match[1] || '').trim();
  }

  if (/^\s*(?:Error:|Status Conflict:|\[Plan Mode\]|❌\s+Cannot\b)/im.test(rawObs)) {
    toStatus = /\[Plan Mode\]|blocked/i.test(rawObs) ? 'blocked' : 'error';
    reason = rawObs;
  }

  if (/\[blocked:\s*(?:plan|exec)\]/i.test(rawAction)) {
    toStatus = 'blocked';
  }

  if (!toStatus) {
    if (operation === 'add' || operation === 'write' || operation === 'status') toStatus = 'pending';
    else if (operation === 'remove') toStatus = 'completed';
    else if (operation === 'note') toStatus = 'review';
    else toStatus = 'pending';
  }
  const normalizedStatus = normalizeAtlasStatus(toStatus);
  const reasonLabel = _todoStepReasonLabel(normalizedStatus, operation);
  if (!title) title = _todoToolArg(rawAction, 'content');
  if (reason) rawSummary = '';

  return {
    operation,
    index,
    fromStatus,
    toStatus: normalizedStatus,
    title: _limitAtlasLines(title, 3),
    reasonLabel,
    reason: _limitAtlasLines(reason, 6),
    next: _limitAtlasLines(next, 3),
    note,
    tally,
    rawSummary,
  };
};

// Relative timestamp helper for hover-revealed "5m ago" labels.
export const _relTime = (ts: any): string => {
  if (!ts) return '';
  const d = Math.max(0, (Date.now() - ts) / 1000);
  if (d < 5) return 'just now';
  if (d < 60) return `${Math.floor(d)}s ago`;
  if (d < 3600) return `${Math.floor(d / 60)}m ago`;
  if (d < 86400) return `${Math.floor(d / 3600)}h ago`;
  return `${Math.floor(d / 86400)}d ago`;
};

export const _unwrapAtlasOutputFence = (text: any): string => {
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
