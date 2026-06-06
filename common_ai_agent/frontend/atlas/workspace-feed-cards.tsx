// workspace-feed-cards.tsx — the chat-feed card component family.
//
// Extracted from workspace.jsx (the live source of truth) as part of the
// strangler-fig TypeScript migration. This module is an INERT mirror: the
// legacy workspace.jsx still serves the live app.
//
// Owns: collapsible thought, observation card, handoff/standard/generic tool
// cards (memoized), typewriter, terminal-transcript renderer, live-agent
// preview, the FeedEntry dispatcher (memoized with a custom comparator),
// SSOT-approval card, AskUserQuestion/AskUserCall interactive blocks, and the
// QA-history panel.
//
// Migration notes (house style):
//   - Real ES module. Ambient `React.useState` / `React.useEffect` become the
//     imported `useState` / `useEffect`; `React.memo` -> `memo`;
//     `React.Fragment` -> `Fragment` (automatic JSX runtime, so no `import
//     React` for JSX itself).
//   - Cross-module helpers come from the sibling modules; window-sourced ATLAS
//     globals (QA_FLOWS / backend / AskUserPrompt / Prism / etc.) are read off
//     window. Window-shaped values are typed `any` on purpose.
import { useState, useEffect, memo, Fragment, type ReactNode } from 'react';

import {
  _toolTheme,
  _normalizeToolName,
  _toolDisplay,
  _isWorkflowResultTool,
  atlasIsThinkingPlaceholderText,
  visibleAtlasThoughtLines,
  cleanAtlasTerminalText,
} from './workspace-tool-theme';
import {
  _obsStatus,
  _relTime,
  _unwrapAtlasOutputFence,
  _cleanTodoToolText,
  _formatTodoStepStatus,
  _parseTodoStepUpdate,
  atlasStatusMeta,
  AtlasStatusBadge,
} from './workspace-report-status';
import {
  _markdownHtml,
  _postProcessMarkdownNode,
  _DIFF_RESULT_TOOL_RE,
  _CHIP_PATH_RE,
  _normalizeDisplayedToolPaths,
  ToolOutputPre,
  GrepOutputPre,
  DiffOutputPre,
  CopyBtn,
} from './workspace-markdown-chips';

// Terminal-transcript + ask_user/SSOT families were extracted into siblings to
// keep this module under 1000 lines. The FeedEntry dispatcher below still calls
// these directly, so import the local bindings here (the public re-exports of
// the full families live further down the file).
import {
  _atlasTerminalTranscriptKind,
  AtlasTerminalTranscript,
} from './workspace-feed-terminal';
import {
  SsotApprovalCard,
  AskUserCall,
} from './workspace-feed-askuser';

// ── Feed entry: dispatcher ─────────────────────────────────────────
export const CollapsibleThought = ({ text, summaryMode = true }: any) => {
  // Default state: show only the LAST ~3 lines, dimmed. Reasoning is
  // valuable as a tail (what the agent just decided), but the early
  // chain-of-thought lines are usually scaffolding the user doesn't
  // need to read. Visual clamp also catches long wrapped lines.
  const TAIL_LINES = 3;
  const visibleLines = visibleAtlasThoughtLines(text);
  const placeholderOnly = atlasIsThinkingPlaceholderText(text);
  const displayText = visibleLines.join('\n');
  const [open, setOpen] = useState(!summaryMode);
  if (!displayText.trim()) return null;
  const lines = visibleLines;
  const tail = lines.slice(-TAIL_LINES);
  const hidden = Math.max(0, lines.length - TAIL_LINES);
  const collapsed = placeholderOnly || (summaryMode && !open);
  return (
    <div
      className="react-block thought"
      style={{ cursor: placeholderOnly ? 'default' : 'pointer', opacity: 0.62 /* dim */ }}
      onClick={placeholderOnly ? undefined : () => setOpen(o => !o)}
      title={placeholderOnly ? 'waiting for model output' : (collapsed ? 'click to expand full reasoning' : 'click to collapse')}
    >
      <span className="rb-tag">
        thought{!placeholderOnly && lines.length > 1 && ` (${lines.length})`}
        {!placeholderOnly && collapsed && hidden > 0 && (
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
      } as any}>
        {collapsed ? tail.join('\n') : displayText}
      </span>
    </div>
  );
};

const _READ_RESULT_TOOL_RE = /^(read_file|read_lines|grep_file|find_files|list_dir)$/i;
const _WRITE_RESULT_TOOL_RE = /^(write_file|write_to_file)$/i;
const _REPLACE_RESULT_TOOL_RE = /^(replace_in_file|replace_lines|replace_file_content|edit|patch|update_file|apply_patch)$/i;

export const _toolResultPreviewLines = (tool: unknown): number => {
  const t = String(tool || '').toLowerCase();
  if (_WRITE_RESULT_TOOL_RE.test(t)) return 10;
  if (_REPLACE_RESULT_TOOL_RE.test(t)) return 30;
  return 0;
};

export const _toolResultDefaultsClosed = (tool: unknown): boolean => (
  _READ_RESULT_TOOL_RE.test(String(tool || ''))
);

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
export const ObsCard = ({ entry, embedded, summaryMode = true, hintText = '' }: any) => {
  // Replace/edit tools default to OPEN even in summary mode so the user
  // can see the actual diff without an extra click. Other tools stay
  // collapsed in summary mode.
  const isReplaceTool = entry?.tool && _DIFF_RESULT_TOOL_RE.test(entry.tool);
  // Read/search tools stay collapsed by default regardless of live/summary
  // state; every other tool follows summaryMode as before.
  const _readClosed = _toolResultDefaultsClosed(entry?.tool);
  const _obsDefaultOpen = _readClosed ? false : (!summaryMode || isReplaceTool);
  const [open, setOpen] = useState<boolean>(_obsDefaultOpen);
  useEffect(() => {
    setOpen(_obsDefaultOpen);
  }, [_obsDefaultOpen]);
  let txt = summaryMode ? _cleanTodoToolText(entry.text || '', entry.tool) : cleanAtlasTerminalText(entry.text || '');
  // Strip ANSI escape sequences leaked from terminal-style backends
  // (e.g. `\x1b[1m`, `\x1b[38;5;71m`, `\x1b[0m`) so they don't show as
  // raw `[1m`, `[96m`, etc. in the chat feed.
  txt = _normalizeDisplayedToolPaths(cleanAtlasTerminalText(txt).replace(/\x1b\[[\d;]*m/g, ''));

  const lines = txt.split('\n');
  const isMulti = lines.length > 1;
  const lineCount = lines.length;
  const maxPreviewLines = _toolResultPreviewLines(entry?.tool);

  // Diff coloring — opt in by tool name or "Added N, removed M" header.
  const displayFormat = String(entry?.display_format || entry?.syntax || '').toLowerCase();
  const looksLikeDiff = displayFormat === 'diff'
                     || /(^|\n)\s*⎿?\s*Added \d+ lines?,? removed \d+ lines?/.test(txt)
                     || (entry.tool && _DIFF_RESULT_TOOL_RE.test(entry.tool));
  const isGrepTool = String(entry?.tool || '').toLowerCase() === 'grep_file';

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
  const Wrapper: any = embedded ? Fragment : 'div';
  const wrapperProps: any = embedded ? {} : { className: 'react-block obs has-hover-affordance', style: { position: 'relative' } };

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
            <DiffOutputPre
              text={txt}
              tool={entry.tool}
              truncated={entry.truncated}
              hintText={hintText || entry.hintText || entry.path || entry.file || ''}
              maxLines={maxPreviewLines}
            />
          ) : isGrepTool ? (
            <GrepOutputPre text={txt} truncated={entry.truncated} maxLines={maxPreviewLines} />
          ) : (
            <ToolOutputPre text={txt} tool={entry.tool} truncated={entry.truncated} maxLines={maxPreviewLines} />
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

export const _parseJsonObject = (text: any) => {
  const raw = String(text || '').trim().replace(/^└─\s*/, '');
  if (!raw || !raw.startsWith('{')) return null;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null;
  } catch (_) {
    return null;
  }
};

export const _firstMetaValue = (...values: any[]) => {
  for (const value of values) {
    if (Array.isArray(value)) {
      const compact = value.map(v => String(v || '').trim()).filter(Boolean);
      if (compact.length) return compact.join(', ');
    } else {
      const text = String(value || '').trim();
      if (text) return text;
    }
  }
  return '';
};

export const _argMetaValue = (argsText: any, name: string) => {
  const re = new RegExp(`(?:^|[,\\s])${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^,\\s]+))`);
  const match = String(argsText || '').match(re);
  return match ? (match[1] || match[2] || match[3] || '').trim() : '';
};

export const _dispatchWorkflowMeta = (tool: any, obsText: any, argsText: any) => {
  if (String(tool || '') !== 'dispatch_workflow') return null;
  const parsed: any = _parseJsonObject(obsText);
  const jobs = Array.isArray(parsed?.jobs) ? parsed.jobs.filter((j: any) => j && typeof j === 'object') : [];
  const model = _firstMetaValue(
    parsed?.model,
    parsed?.models,
    jobs.map((j: any) => j.model),
    _argMetaValue(argsText, 'model')
  );
  const effort = _firstMetaValue(
    parsed?.reasoning_effort,
    parsed?.reasoning_efforts,
    parsed?.effort,
    jobs.map((j: any) => j.reasoning_effort),
    _argMetaValue(argsText, 'reasoning_effort'),
    _argMetaValue(argsText, 'effort')
  );
  const worker = _firstMetaValue(parsed?.worker, parsed?.workers, jobs.map((j: any) => j.worker));
  const execMode = _firstMetaValue(parsed?.exec_mode, jobs.map((j: any) => j.exec_mode));
  if (!model && !effort && !worker && !execMode) return null;
  return { model, effort, worker, execMode };
};

// Handoff parsing lives in lib/orchestrator_chat_logic (loaded before this
// script and tested via vitest) so there is a single source of truth. These
// thin wrappers delegate to it, with a minimal fallback if the global is
// somehow unavailable (degrades to showing the raw args, never crashes).
export const _handoffFields = (action: any, obs: any) => {
  const lib = (typeof window !== 'undefined') && (window as any).AtlasOrchestratorChatLogic;
  if (lib && typeof lib.handoffFields === 'function') return lib.handoffFields(action, obs);
  const argsText = (action && (action.args || action.text)) || '';
  return { sent: { target: '', ip: '', task: String(argsText), reason: '', schedule: '', fanout: false }, result: null };
};

export const _handoffStatusColor = (status: any) => {
  const lib = (typeof window !== 'undefined') && (window as any).AtlasOrchestratorChatLogic;
  if (lib && typeof lib.handoffStatusColor === 'function') return lib.handoffStatusColor(status);
  return '#8b949e';
};

export const HandoffRow = ({ label, children }: any) => (
  <div className="handoff-row">
    <span className="handoff-label">{label}</span>
    <span className="handoff-val">{children}</span>
  </div>
);

export const TodoStepUpdateCard = ({ action, obs, tool, info }: any) => {
  const theme = _toolTheme(tool);
  const isStatusRead = info?.operation === 'status';
  const displayStatus = isStatusRead ? 'review' : (info?.toStatus || 'pending');
  const meta = atlasStatusMeta(displayStatus);
  const ts = (action && action.createdAt) || (obs && obs.createdAt) || 0;
  const target = !isStatusRead ? (info?.index ? `Task #${info.index}` : 'Task') : '';
  const fromLabel = info?.fromStatus ? _formatTodoStepStatus(info.fromStatus) : '';
  const toLabel = info?.toStatus ? _formatTodoStepStatus(info.toStatus) : '';
  const transition = !isStatusRead && fromLabel && toLabel && fromLabel !== toLabel ? `${fromLabel} → ${toLabel}` : (!isStatusRead ? toLabel : '');
  const hasBody = !!(info?.title || info?.reason || info?.note || info?.next || info?.tally || info?.rawSummary);
  return (
    <div className="tool-card step-update-card has-hover-affordance" style={{ borderLeftColor: meta.color || theme.color }}>
      <span className="tool-card-ts">{_relTime(ts)}</span>
      <div className="tool-card-head step-update-head">
        <span className="tool-card-glyph" style={{ color: 'var(--fg)' }}>{theme.glyph}</span>
        <span className="tool-card-tool">{_toolDisplay(tool)}</span>
        <AtlasStatusBadge status={displayStatus} label={isStatusRead ? 'snapshot' : undefined} compact />
        {target && <span className="step-update-target">{target}</span>}
        {transition && <span className="step-update-transition">{transition}</span>}
      </div>
      {hasBody && (
        <>
          <div className="tool-card-sep" />
          <div className="step-update-body">
            {info.title && <HandoffRow label="task">{info.title}</HandoffRow>}
            {info.reason && <HandoffRow label={String(info.reasonLabel || 'detail').toLowerCase()}>{info.reason}</HandoffRow>}
            {info.note && <HandoffRow label="note">{info.note}</HandoffRow>}
            {info.next && <HandoffRow label="next">{info.next}</HandoffRow>}
            {info.tally && <HandoffRow label="todo">{info.tally}</HandoffRow>}
            {info.rawSummary && <HandoffRow label="output">{info.rawSummary}</HandoffRow>}
          </div>
        </>
      )}
    </div>
  );
};

// HandoffCard: clean labeled rendering for orchestrator handoffs
// (dispatch_workflow / write_handoff). Replaces the raw "key={json}" args
// line with an aligned label/value card covering both the dispatch (sent)
// and the worker's result summary (received).
export const _HandoffCardRaw = ({ action, obs, tool }: any) => {
  const theme = _toolTheme(tool);
  const verb = tool === 'write_handoff' ? 'Handoff' : 'Dispatch';
  const { sent, result } = _handoffFields(action, obs);
  const ts = (action && action.createdAt) || (obs && obs.createdAt) || 0;
  const isErr = result && /(error|fail|blocked|fatal)/i.test(`${result.status || ''} ${result.error || ''}`);
  const borderColor = isErr ? '#f85149' : theme.color;
  return (
    <div className="tool-card handoff-card has-hover-affordance" style={{ borderLeftColor: borderColor }}>
      <span className="tool-card-ts">{_relTime(ts)}</span>
      <div className="handoff-block">
        <div className="handoff-title">
          <span className="handoff-glyph">⇢</span>
          <span className="handoff-verb">{verb}</span>
          {sent.target && <span className="handoff-target">{sent.target}</span>}
          {sent.ip && <><span className="handoff-arrow">→</span><span className="handoff-ip">{sent.ip}</span></>}
          {sent.fanout && sent.schedule && <span className="handoff-sched">({sent.schedule})</span>}
        </div>
        {sent.task && <HandoffRow label="task">{sent.task}</HandoffRow>}
        {sent.reason && <HandoffRow label="reason">{sent.reason}</HandoffRow>}
        {sent.schedule && !sent.fanout && <HandoffRow label="schedule">{sent.schedule}</HandoffRow>}
      </div>
      {result && (
        <div className="handoff-block handoff-result">
          <div className="handoff-title">
            <span className="handoff-glyph handoff-return">⎿</span>
            {result.jobs ? (
              <span className="handoff-stages">
                {result.jobs.map((j: any, k: number) => (
                  <span key={k} className="handoff-stage">
                    {j.workflow}{' '}
                    <span className="handoff-dot" style={{ color: _handoffStatusColor(j.status) }}>●</span>
                    {j.status ? ' ' + j.status : ''}
                  </span>
                ))}
              </span>
            ) : (
              <>
                {result.workflow && <span className="handoff-target">{result.workflow}</span>}
                {result.status && (
                  <span className="handoff-status">
                    <span className="handoff-dot" style={{ color: _handoffStatusColor(result.status) }}>●</span>
                    {result.status}
                  </span>
                )}
              </>
            )}
          </div>
          {!result.jobs && result.worker && <HandoffRow label="worker">{result.worker.replace(/^https?:\/\//, '')}</HandoffRow>}
          {!result.jobs && (result.job || result.model) && (
            <HandoffRow label="job">{[result.job, result.model].filter(Boolean).join(' · ')}</HandoffRow>
          )}
          {result.error && <HandoffRow label="error"><span style={{ color: '#f85149' }}>{result.error}</span></HandoffRow>}
        </div>
      )}
    </div>
  );
};
export const HandoffCard = memo(_HandoffCardRaw);

// ToolCard: pairs an action entry with its obs entry into a single
// connected card with tool-themed left border + glyph + status badge.
// Either half can be missing (action-only when blocked, obs-only is
// uncommon but handled).
// Compact one-line summary of a read_pipeline_state result so the chat
// doesn't dump the raw JSON. Returns '' if it can't parse.
export const _pipelineStateSummary = (obsText: any) => {
  try {
    const raw = String(obsText || '').replace(/^└─\s*/, '').trim();
    const d = JSON.parse(raw);
    if (!d || typeof d !== 'object') return '';
    const passed = Array.isArray(d.passed) ? d.passed : [];
    const running = Array.isArray(d.running) ? d.running : [];
    const failed = (d.failed && typeof d.failed === 'object') ? d.failed : {};
    const shortReason = (v: any) => {
      const s = String(v || '');
      const wns = s.match(/WNS=(-?[\d.]+).*?viol=(\d+)/i);
      if (wns) return `WNS ${wns[1]}/${wns[2]}`;
      const st = s.match(/status=([A-Za-z_]+)/i);
      if (st) return st[1];
      const tag = s.match(/\[([a-z-]+)\]\s*(.+)$/i);
      if (tag) return tag[2].slice(0, 24);
      return '';
    };
    const parts = [];
    if (passed.length) parts.push(`✓ ${passed.join(' ')}`);
    const fk = Object.keys(failed);
    if (fk.length) parts.push(`✗ ${fk.map((k: string) => { const r = shortReason(failed[k]); return r ? `${k}(${r})` : k; }).join(' ')}`);
    if (running.length) parts.push(`▶ ${running.join(' ')}`);
    return parts.join('   ');
  } catch (_) { return ''; }
};

export const _artifactReadSummary = (obsText: any) => {
  const d: any = _parseJsonObject(obsText);
  if (!d) return '';
  const files = Array.isArray(d.files) ? d.files.filter(Boolean) : [];
  const missing = Array.isArray(d.missing) ? d.missing.filter(Boolean) : [];
  const previews = Array.isArray(d.previews) ? d.previews.filter((p: any) => p && typeof p === 'object') : [];
  const preview = previews.find((p: any) => p.exists) || previews[0] || {};
  const head = String(preview.head || '');
  const grab = (re: RegExp) => {
    const m = head.match(re);
    return m ? String(m[1] || '').trim() : '';
  };
  const topName = grab(/(?:^|\n)\s*name:\s*([^\n]+)/);
  const topFile = grab(/(?:^|\n)\s*file:\s*([^\n]+)/);
  const modules = Array.from(head.matchAll(/(?:^|\n)\s*-\s*name:\s*([^\n]+)/g))
    .map((m: any) => String(m[1] || '').trim())
    .filter(Boolean)
    .slice(0, 3);
  const parts = [];
  if (files.length) parts.push(files.slice(0, 2).join(', '));
  if (topName) parts.push(`top ${topName}`);
  if (topFile) parts.push(topFile);
  if (modules.length) parts.push(`modules ${modules.join(', ')}`);
  if (missing.length) parts.push(`missing ${missing.length}`);
  return parts.join(' · ');
};

// Readable one-line summary of an orchestrator tool CALL's args, so the chat
// shows "⏸ until job ab12… / your reply · <reason>" instead of raw
// `wake_on={"job_ids":[...],"user_message":true,...}, reason="..."`.
// Returns '' for tools we don't special-case (keeps the raw args).
export const _orchToolArgsSummary = (tool: any, argsText: any) => {
  const t = String(tool || '').toLowerCase();
  const a = String(argsText || '');
  const grab = (re: RegExp) => { const m = a.match(re); return m ? m[1] : ''; };
  const short = (id: any) => { const s = String(id || '').replace(/["'\s]/g, ''); return s.length > 8 ? s.slice(0, 8) + '…' : s; };
  const unq = (s: any) => String(s || '').replace(/\\"/g, '"').replace(/\\n/g, ' ');
  const reason = unq(grab(/reason="((?:[^"\\]|\\.)*)"/));
  const reasonTail = reason ? ` · ${reason}` : '';
  if (t === 'yield_run') {
    const jobs = grab(/"job_ids"\s*:\s*\[([^\]]*)\]/);
    const jobList = jobs ? jobs.split(',').map(short).filter(Boolean) : [];
    const userMsg = /"user_message"\s*:\s*true/.test(a);
    const secs = grab(/"after_seconds"\s*:\s*(\d+)/);
    const waits = [];
    if (jobList.length) waits.push(`job ${jobList.join(', ')}`);
    if (userMsg) waits.push('your reply');
    if (secs) waits.push(`${secs}s timer`);
    return `⏸ ${waits.length ? 'until ' + waits.join(' / ') : 'parked'}${reasonTail}`;
  }
  if (t === 'wait_job') return `job ${short(grab(/job_id="([^"]+)"/))}`;
  if (t === 'read_artifact') { const st = grab(/\bstage="([^"]+)"/); const ip = grab(/\bip="([^"]+)"/); return st ? `${st} evidence` : ip; }
  if (t === 'classify_failure') { const st = grab(/\bstage="([^"]+)"/); return st ? `classify ${st}` : ''; }
  if (t === 'mark_downstream_stale') { const st = grab(/from_stage="([^"]+)"/); return st ? `stale from ${st}` : ''; }
  if (t === 'web_search') { const q = unq(grab(/query="((?:[^"\\]|\\.)*)"/)); return q ? `“${q}”` : ''; }
  if (t === 'web_fetch') return grab(/url="([^"]+)"/);
  if (t === 'import_document') { const p = grab(/path="([^"]+)"/); return p ? p.split('/').pop() : ''; }
  if (t === 'ask_user') return unq(grab(/question="((?:[^"\\]|\\.)*)"/));
  if (t === 'read_pipeline_state') { const ip = grab(/\bip="([^"]+)"/); return ip ? `ip ${ip}` : ''; }
  return '';
};

export const _StandardToolCardRaw = ({ action, obs, summaryMode = true, tool }: any) => {
  const theme = _toolTheme(tool);
  // If the obs indicates an error, override the border to red so the
  // eye finds it. Otherwise use the tool theme color.
  const obsTextRaw = obs ? (summaryMode ? _cleanTodoToolText(obs.text || '', obs.tool) : cleanAtlasTerminalText(obs.text || '')) : '';
  const obsText = cleanAtlasTerminalText(obsTextRaw).replace(/\x1b\[[\d;]*m/g, '');
  const toolName = String(tool || '').toLowerCase();
  const isStateRead = toolName === 'read_pipeline_state';
  const isArtifactRead = toolName === 'read_artifact' || toolName === 'read_evidence';
  const stateSummary = isStateRead && obs ? _pipelineStateSummary(obsText) : '';
  const artifactSummary = isArtifactRead && obs ? _artifactReadSummary(obsText) : '';
  const resultSummary = stateSummary || artifactSummary;
  const status = obs ? _obsStatus(obsText) : 'neutral';
  const borderColor = status === 'err' ? '#f85149' : theme.color;
  const rawArgsText = action && action.text
    ? action.text
        .replace(/^[▶⏺]\s*/, '')
        .replace(tool ? new RegExp('^' + tool.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*') : /^\?\s*/, '')
    : '';
  const todoStepInfo = _parseTodoStepUpdate(obs ? obs.text || '' : '', tool, rawArgsText || (action && action.text) || '');
  if (todoStepInfo) {
    return <TodoStepUpdateCard action={action} obs={obs} tool={tool} info={todoStepInfo} />;
  }
  let argsText = rawArgsText;
  // Replace/write/edit tools dump the new file content into args, which
  // produces a noisy single-line preview next to the tool name (just
  // the first 80 chars of a 500-line `===========\n//comment...` blob).
  // The diff body shows the actual change, so the header only needs
  // the file path. Heuristics: pull `path="..."` / `path: '...'`
  // / first .sv|.v|.svh|.yaml|.json|.md path-like token, fall back to
  // empty string when nothing recognizable shows up.
  if (tool && _DIFF_RESULT_TOOL_RE.test(tool)) {
    const pathMatch = argsText.match(/path\s*[:=]\s*["']([^"']+)["']/i)
      || argsText.match(/^\s*["']([^"']+\.(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl))["']/i)
      || argsText.match(/^\s*([^\s"',{}\[\]]+\.(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl))/i);
    argsText = pathMatch ? pathMatch[1] : '';
  }
  const dispatchMeta = _dispatchWorkflowMeta(tool, obsText, argsText);
  const isDispatchTool = String(tool || '').toLowerCase() === 'dispatch_workflow';
  // Readable orchestrator tool-call summary (yield_run/wait_job/read_artifact/…)
  // shown instead of the raw `key={json}` args. Falls back to raw args.
  const orchSummary = isDispatchTool ? '' : _orchToolArgsSummary(tool, rawArgsText);
  const displayArgs = orchSummary || argsText;
  const ts = (action && action.createdAt) || (obs && obs.createdAt) || 0;
  // Tool results default to OPEN. The user needs to see the result/cost
  // trail without hunting through collapsed cards; large bodies remain
  // bounded by .tool-output-pre max-height.
  const isReplaceTool = tool && _DIFF_RESULT_TOOL_RE.test(tool);
  const defaultsClosed = _toolResultDefaultsClosed(tool);
  const showFullArgsByDefault = !!tool && /^(run_command|todo_update|dispatch_workflow)$/i.test(tool);
  const obsLines = obs ? obsText.split('\n') : [];
  const obsIsMulti = obsLines.length > 1;
  const obsIsLarge = obsText.length > 1200 || obsLines.length > 12;
  const isCompactRead = isStateRead || isArtifactRead;
  // Command and todo updates are useful as the primary payload, so show
  // their arguments by default while keeping the result body collapsible.
  // Threshold: > 100 chars or contains a newline.
  const argsIsLong = !!argsText && (argsText.length > 100 || /\n/.test(argsText));
  // Read/search tools are useful as audit evidence but too noisy in chat.
  // Keep them collapsed in summary mode; write/replace tools stay open with
  // tool-specific line caps enforced by ObsCard.
  // Read/search tools (read_file, read_lines, grep_file, find_files, list_dir)
  // are audit noise in the chat flow — default them COLLAPSED always, even
  // while the worker is live (entrySummaryMode passes summaryMode=false during
  // a live turn, which previously forced them open). Expand on demand via ▸.
  const defaultObsOpen = defaultsClosed
    ? false
    : (((!!obs && !isCompactRead && !obsIsLarge) || !summaryMode) || isReplaceTool);
  const [obsOpen, setObsOpen] = useState<boolean>(defaultObsOpen);
  useEffect(() => {
    setObsOpen(defaultObsOpen);
  }, [defaultObsOpen]);
  const showArgsExpanded = obsOpen || showFullArgsByDefault;
  const headClickable = (!!obs && obsIsMulti) || argsIsLong || (isCompactRead && !!obs) || obsIsLarge;
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
        onKeyDown={headClickable ? (e: any) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleObs(); }
        } : undefined}
        style={headClickable ? {
          cursor: 'pointer',
          userSelect: 'none',
          alignItems: showArgsExpanded ? 'flex-start' : 'center',
          flexWrap: isDispatchTool ? 'wrap' : undefined,
        } : undefined}
        title={headClickable ? (obsOpen ? 'click to collapse' : 'click to expand') : undefined}
      >
        <span className="tool-card-glyph" style={{ color: 'var(--fg)' }}>{theme.glyph}</span>
        <span className="tool-card-tool">{_toolDisplay(tool)}</span>
        {dispatchMeta && (
          <span className="tool-card-meta">
            {dispatchMeta.model && <span>model {dispatchMeta.model}</span>}
            {dispatchMeta.effort && <span>effort {dispatchMeta.effort}</span>}
            {dispatchMeta.execMode && <span>{dispatchMeta.execMode}</span>}
            {dispatchMeta.worker && <span>{dispatchMeta.worker.replace(/^https?:\/\//, '')}</span>}
          </span>
        )}
        {displayArgs && (
          <span
            className={`tool-card-args${showArgsExpanded ? '' : ' trunc'}`}
            style={{
              color: orchSummary ? 'var(--fg-mute)' : 'var(--fg)',
              ...(isDispatchTool ? { flexBasis: '100%' } : {}),
              ...(showArgsExpanded ? {
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                overflow: 'visible',
                textOverflow: 'clip',
              } : {}),
            } as any}
          >{displayArgs}</span>
        )}
        {resultSummary && !obsOpen && (
          <span className="tool-card-args" style={{ color: 'var(--fg-mute)', flexBasis: '100%', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{resultSummary}</span>
        )}
        {status === 'err' && <span className="tool-card-status" style={{ color: '#f85149' }}>✗</span>}
        {status === 'ok'  && <span className="tool-card-status" style={{ color: '#3fb950' }}>✓</span>}
        {(obsIsMulti || argsIsLong || (isCompactRead && !!obs) || obsIsLarge) ? (
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
          entry={{ ...obs, tool: obs?.tool || tool, text: obsText }}
          embedded={true}
          summaryMode={summaryMode}
          hintText={[tool, rawArgsText, argsText].filter(Boolean).join('\n')}
          forceOpen
          hideHeader
        />
      )}
    </div>
  );
};
export const StandardToolCard = memo(_StandardToolCardRaw);

export const _ToolCardRaw = ({ action, obs, summaryMode = true }: any) => {
  const tool = _normalizeToolName((action && action.tool) || (obs && obs.tool) || '');
  // Orchestrator handoffs get a dedicated labeled card instead of the raw
  // "key={json}" args line — see HandoffCard.
  // dispatch_workflow / write_handoff are ALWAYS orchestrator tool calls — use
  // the labeled HandoffCard even for live entries (raw rendering is for worker
  // ReAct steps, whose tool is the workflow name, never these).
  if (tool === 'dispatch_workflow' || tool === 'write_handoff') {
    return <HandoffCard action={action} obs={obs} tool={tool} />;
  }
  return (
    <StandardToolCard
      action={action}
      obs={obs}
      summaryMode={summaryMode}
      tool={tool}
    />
  );
};
// Memoized so a single new feed entry doesn't re-render every prior
// ToolCard. action/obs are immutable per turn so reference equality is
// the right comparator.
export const ToolCard = memo(_ToolCardRaw);

export const Typewriter = ({ text }: any) => {
  const full = String(text || '');
  const [shown, setShown] = useState('');
  const [done, setDone] = useState(false);
  useEffect(() => {
    if (!full) { setDone(true); return; }
    setShown('');
    setDone(false);
    let i = 0;
    const delay = Math.max(8, Math.min(20, Math.round(1200 / full.length)));
    const iv = setInterval(() => {
      i++;
      setShown(full.slice(0, i));
      if (i >= full.length) { clearInterval(iv); setDone(true); }
    }, delay);
    return () => clearInterval(iv);
  }, [full]);
  return (
    <span style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
      {shown}
      {!done && <span className="stream-caret" style={{ display: 'inline-block', width: 2, height: '1em', background: 'var(--accent)', marginLeft: 1, verticalAlign: 'text-bottom', animation: 'blink 0.7s step-end infinite' }} />}
    </span>
  );
};

// Terminal-transcript renderer family moved to ./workspace-feed-terminal to
// keep this module under 1000 lines. Re-exported so the public contract is
// unchanged (every symbol still imports from workspace-feed-cards).
// `_atlasTerminalTranscriptKind` + `AtlasTerminalTranscript` are imported at
// the top (the FeedEntry dispatcher uses them) and re-exported below.
export {
  _ATLAS_TERMINAL_SECTION_RE,
  _atlasTerminalRole,
  _atlasTerminalLineKind,
  _atlasTerminalTokenClass,
  _renderAtlasTerminalInline,
} from './workspace-feed-terminal';
export { _atlasTerminalTranscriptKind, AtlasTerminalTranscript };

export const LiveAgentPreview = memo(({ text }: any) => {
  const body = String(text || '');
  if (!body.trim()) return null;
  return (
    <div className="feed-entry feed-entry-agent feed-entry-live has-hover-affordance" style={{ padding: '8px 0 12px', marginBottom: 4, position: 'relative' }}>
      <span className="feed-entry-label ok" style={{ fontWeight: 600, marginRight: 8,
        fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Agent</span>
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

export const _FeedEntryRaw = ({ entry, qaState, onToggle, onCustom, onSubmit, dir, summaryMode = true }: any) => {
  if (entry.kind === 'user') {
    const userText = String(entry.text || '');
    // Render through markdown so QA submission prompts (which are
    // multi-line markdown with `#`/`##` headers, bullet lists, and code
    // chips) keep their structure instead of collapsing onto one line.
    // Plain single-line user inputs still render fine via marked.
    const userHtml = _markdownHtml(userText);
    return (
      <div className="feed-entry feed-entry-user" style={{ padding: '10px 14px', marginBottom: 12, borderLeft: '2px solid var(--accent)', background: 'var(--bg-2)', borderRadius: 2 }}>
        <span className="feed-entry-label acc" style={{ fontWeight: 600, marginRight: 8, fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>You</span>
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
    const terminalKind = _atlasTerminalTranscriptKind(entry.text || '');
    const html = _markdownHtml(entry.text || '');
    return (
      <div className="feed-entry feed-entry-agent has-hover-affordance" style={{ padding: '8px 0 12px', marginBottom: 4, position: 'relative' }}>
        <span className="feed-entry-label ok" style={{ fontWeight: 600, marginRight: 8,
          fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Agent</span>
        {entry.createdAt ? (
          <span className="ts-pill">{_relTime(entry.createdAt)}</span>
        ) : null}
        <CopyBtn text={entry.text || ''} />
        {entry._animate
          ? <div className="md-agent" style={{ marginTop: 4 }}><Typewriter text={entry.text || ''} /></div>
          : terminalKind
            ? <AtlasTerminalTranscript text={entry.text || ''} kind={terminalKind} />
          : <div className="md-agent" style={{ marginTop: 4 }} dangerouslySetInnerHTML={{ __html: html }}
              ref={_postProcessMarkdownNode}
            />
        }
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
export const FeedEntry = memo(_FeedEntryRaw, (prev: any, next: any) => {
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

// SSOT-approval + ask_user interactive blocks moved to
// ./workspace-feed-askuser to keep this module under 1000 lines. The inline
// escapers (_escHtml/renderInline) travel with them. Re-exported so the public
// contract is unchanged (every symbol still imports from workspace-feed-cards).
// `SsotApprovalCard` + `AskUserCall` are imported at the top (the FeedEntry
// dispatcher uses them) and re-exported below.
export {
  _escHtml,
  renderInline,
  AskUserQuestionBlock,
  QaHistoryPanel,
} from './workspace-feed-askuser';
export { SsotApprovalCard, AskUserCall };
