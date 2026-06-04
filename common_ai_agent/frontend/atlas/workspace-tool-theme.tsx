// workspace-tool-theme.tsx — TypeScript migration of the pure constants and
// non-React helpers extracted from workspace.jsx (strangler-fig split).
//
// Owns: tool-name theming/aliasing, the workflow-result tool set, orchestrator
// feed coalescing/trimming (delegating to window.AtlasOrchestratorChatLogic
// when present), the worker-snapshot fetch, SCM-tab resolution, and the
// history-limit constants. All symbols are pure (no React/component state).
//
// Cross-file: reads window.atlasData / AtlasOrchestratorChatLogic /
// ATLAS_BOOT_CONFIG / AtlasSCMTab* / SCMTab / GitTab. Types are intentionally
// loose (any) for the dynamic feed/worker/window shapes, matching the original
// untyped behavior exactly.

// ── Tool-call visual theme ────────────────────────────────────────
// Tool calls use one accent color so the chat feed stays calm. Glyphs
// still provide a small shape cue without turning the feed into a legend.
export const TOOL_ACCENT = 'var(--tool-accent)';
export const TOOL_THEME: Record<string, { glyph: string; color: string }> = {
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
  dispatch_workflow: { glyph: '▶', color: TOOL_ACCENT },
  read_pipeline_state: { glyph: '⌕', color: TOOL_ACCENT },
  read_evidence:     { glyph: '▤', color: TOOL_ACCENT },
  read_artifact:     { glyph: '▤', color: TOOL_ACCENT },
  yield_run:         { glyph: '⏸', color: TOOL_ACCENT },
  wait_job:          { glyph: '⏳', color: TOOL_ACCENT },
  mark_downstream_stale: { glyph: '↻', color: TOOL_ACCENT },
  write_handoff:     { glyph: '⇢', color: TOOL_ACCENT },
  classify_failure:  { glyph: '◇', color: TOOL_ACCENT },
  import_document:   { glyph: '▤', color: TOOL_ACCENT },
  read_doc:          { glyph: '▤', color: TOOL_ACCENT },
  git_diff:          { glyph: '◇', color: TOOL_ACCENT },
  git_status:        { glyph: '◇', color: TOOL_ACCENT },
  __default:         { glyph: '▶', color: TOOL_ACCENT },
};
export const _toolTheme = (name: string) => TOOL_THEME[name] || TOOL_THEME.__default;

// Agent meta-cognition tools (todo_*) drive the LLM's session-local working
// memory — completely separate from the workflow's stage TODO tracker
// (RTL-XXXX in rtl_todo_tracker.json, surfaced in the right-side panel).
// Render them as `step_*` in chat so users do NOT conflate agent step
// counters (#2, #3) with the workflow tracker's stable IDs (RTL-0060).
// The underlying tool name is unchanged; only the chat label is swapped.
export const _TOOL_CHAT_ALIAS: Record<string, string> = {
  todo_update: 'step_update',
  todo_note:   'step_note',
  todo_write:  'step_write',
  todo_add:    'step_add',
  todo_remove: 'step_remove',
  todo_status: 'step_status',
};
export const _normalizeToolName = (name: any) => {
  const text = String(name || '').trim();
  return text && text !== '?' ? text : '';
};
export const _toolDisplay = (name: any) => {
  const tool = _normalizeToolName(name);
  return _TOOL_CHAT_ALIAS[tool] || tool || 'tool';
};

export const atlasIsIterationMarkerText = (text: any): boolean => {
  return /^──\s*Iter\s+\d+\s*\/\s*\d+(?:\s+\[[^\]]+\])?\s*$/.test(String(text || '').trim());
};

// Direct workflow/slash results also arrive as `slash_output`, which is the
// user-facing Markdown surface. Keep their mirrored `tool_result` event for
// data refresh subscribers, but do not render it again as a plain obs block.
export const WORKFLOW_RESULT_TOOLS = new Set([
  'slash',
  'workflow',
  'import',
  'new-ip',
  'grill-me',
  'approve',
  'to-ssot',
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
export const _isWorkflowResultTool = (tool: any) => WORKFLOW_RESULT_TOOLS.has(String(tool || '').toLowerCase());

export const refreshChatSession = (session: any, opts?: any) => {
  const api = (window as any).atlasData || {};
  if (typeof api.refreshActiveConversation === 'function') {
    return api.refreshActiveConversation(session, opts);
  }
  if (typeof api.refreshSessionState === 'function') {
    return api.refreshSessionState(session, true, opts || {});
  }
  return null;
};

export const atlasIsThinkingPlaceholderText = (text: any): boolean => {
  const fn = (window as any).AtlasOrchestratorChatLogic?.isThinkingPlaceholderText;
  if (typeof fn === 'function') return fn(text);
  const lines = String(text || '').split('\n').map((l: string) => l.trim()).filter(Boolean);
  if (!lines.length) return false;
  return lines.every((line: string) => (
    line
      .replace(/^[^A-Za-z0-9]+/, '')
      .replace(/^(?:thought|reasoning)\b\s*[:\])\-–—]*/i, '')
      .replace(/^[^A-Za-z0-9]+/, '')
      .trim()
      .replace(/[.…\s]+$/g, '')
      .toLowerCase() === 'thinking'
  ));
};

export const visibleAtlasThoughtLines = (text: any): string[] => {
  const fn = (window as any).AtlasOrchestratorChatLogic?.visibleThoughtLines;
  if (typeof fn === 'function') return fn(text);
  const lines = String(text || '').split('\n').map((l: string) => l.trim()).filter(Boolean);
  if (!lines.length) return [];
  const real = lines.filter((line: string) => !atlasIsThinkingPlaceholderText(line) && !/^\.\.\. \(\d+ older thought lines hidden for speed\)$/.test(line));
  return real;
};

export const compactAtlasThoughtText = (text: any, maxLines = 80): string => {
  const fn = (window as any).AtlasOrchestratorChatLogic?.compactThoughtText;
  if (typeof fn === 'function') return fn(text, maxLines);
  const lines = visibleAtlasThoughtLines(text);
  if (lines.length <= maxLines) return lines.join('\n');
  return [
    `... (${lines.length - maxLines} older thought lines hidden for speed)`,
    ...lines.slice(-maxLines),
  ].join('\n');
};

export const cleanAtlasTerminalText = (text: any): string => {
  const fn = (window as any).AtlasOrchestratorChatLogic?.cleanTerminalControlText;
  if (typeof fn === 'function') return fn(text);
  return String(text || '').replace(/\x1b\[[\d;]*m/g, '');
};

export const coalesceAtlasFeedEntries = (current: any, entries: any): any[] => {
  const fn = (window as any).AtlasOrchestratorChatLogic?.coalesceFeedEntries;
  if (typeof fn === 'function') return fn(current, entries);
  const list = Array.isArray(entries) ? entries : [entries];
  const out: any[] = Array.isArray(current) ? current.slice() : [];
  for (const raw of list) {
    if (!raw || typeof raw !== 'object') continue;
    if (raw.kind === 'agent_delta') {
      const deltaText = String(raw.text || '');
      if (!deltaText) continue;
      const streamId = String(raw.streamId || raw.stream_id || '');
      const prevAgent = out[out.length - 1];
      if (prevAgent && prevAgent.kind === 'agent' && String(prevAgent.streamId || '') === streamId) {
        out[out.length - 1] = {
          ...prevAgent,
          ...raw,
          kind: 'agent',
          text: String(prevAgent.text || '') + deltaText,
          streamId,
        };
      } else {
        out.push({
          ...raw,
          kind: 'agent',
          text: deltaText,
          streamId,
        });
      }
      continue;
    }
    const entry = raw.kind === 'thought'
      ? { ...raw, text: compactAtlasThoughtText(raw.text) }
      : raw;
    if (entry.kind === 'thought' && !String(entry.text || '').trim()) continue;
    const thought = entry.kind === 'thought';
    const placeholder = thought && atlasIsThinkingPlaceholderText(entry.text);
    const last = out[out.length - 1];
    const lastPlaceholder = last && last.kind === 'thought' && atlasIsThinkingPlaceholderText(last.text);
    if (placeholder) {
      continue;
    }
    if (lastPlaceholder) out.pop();
    const prev = out[out.length - 1];
    if (thought && prev && prev.kind === 'thought') {
      const prevText = String(prev.text || '').trim();
      const nextText = String(entry.text || '').trim();
      if (nextText && prevText !== nextText) out[out.length - 1] = { ...prev, ...entry, text: compactAtlasThoughtText(prevText ? `${prevText}\n${nextText}` : nextText) };
      else if (nextText) out[out.length - 1] = { ...prev, ...entry, text: prev.text };
      continue;
    }
    out.push(entry);
  }
  return out;
};

export const trimAtlasFeedState = (items: any, maxEntries = 600): any[] => {
  const list: any[] = Array.isArray(items) ? items.filter(Boolean) : [];
  if (list.length <= maxEntries) return list;
  const tail = list.slice(-maxEntries);
  // Keep pending interactive cards even if a very noisy worker log would push
  // them out of the retained window.
  const protectedEntries = list
    .slice(0, -maxEntries)
    .filter((e: any) => e && (e.kind === 'qcard' || e.kind === 'ssot_approval'));
  return [...protectedEntries, ...tail];
};

export const orchestratorFlowToolName = (entry: any) => _normalizeToolName(entry && entry.tool || '').toLowerCase();
export const orchestratorFlowArg = (entry: any, name: string): string => {
  const raw = entry && entry.argsRaw;
  if (raw && typeof raw === 'object' && raw[name] != null) return String(raw[name]).trim();
  const text = String((entry && (entry.args || entry.text)) || '');
  const re = new RegExp('(?:^|[,\\s(])' + name + '\\s*=\\s*(?:"([^"]*)"|\'([^\']*)\'|([^,\\s)]+))');
  const match = text.match(re);
  return match ? String(match[1] || match[2] || match[3] || '').trim() : '';
};

export const orchestratorFlowFromFeed = (feed: any[] = [], workers: any[] = [], activeIp = ''): any => {
  const items = Array.isArray(feed) ? feed : [];
  const lastUserIndex = (() => {
    for (let i = items.length - 1; i >= 0; i--) {
      if (items[i] && items[i].kind === 'user') return i;
    }
    return -1;
  })();
  const recent = lastUserIndex >= 0 ? items.slice(lastUserIndex) : [];
  const userText = lastUserIndex >= 0 ? String(items[lastUserIndex]?.text || '').trim() : '';
  const liveWorkers = (Array.isArray(workers) ? workers : []).filter((w: any) => (
    Number(w.running_count || 0) > 0 ||
    Number(w.pending_count || 0) > 0 ||
    Number(w.queued_count || 0) > 0
  ));
  const actions = recent.filter((e: any) => e && e.kind === 'action');
  const hasCheck = actions.some((e: any) => orchestratorFlowToolName(e) === 'read_pipeline_state');
  const hasWait = actions.some((e: any) => orchestratorFlowToolName(e) === 'yield_run' || orchestratorFlowToolName(e) === 'wait_job');
  const dispatchActions = actions.filter((e: any) => (
    orchestratorFlowToolName(e) === 'dispatch_workflow' ||
    /\bdispatch\b/i.test(String(e.text || ''))
  ));
  const dispatched = dispatchActions
    .map((e: any) => orchestratorFlowArg(e, 'workflow') || String(e.tool || '').trim())
    .filter(Boolean);
  const workerNames = liveWorkers
    .map((w: any) => String(w.workflow || '').trim())
    .filter(Boolean);
  const targets = Array.from(new Set([...dispatched, ...workerNames])).filter(Boolean);
  const hasSignal = userText || hasCheck || dispatchActions.length || liveWorkers.length || hasWait;
  if (!hasSignal) return null;
  const workerRunning = liveWorkers.some((w: any) => Number(w.running_count || 0) > 0);
  const workerPending = liveWorkers.some((w: any) => Number(w.pending_count || 0) > 0);
  const workerQueued = liveWorkers.some((w: any) => Number(w.queued_count || 0) > 0);
  const workerStatus = workerRunning ? 'running' : workerPending ? 'starting' : workerQueued ? 'queued' : '';
  const steps: any[] = [];
  if (userText) {
    steps.push({
      key: 'user',
      label: 'You',
      detail: userText.length > 44 ? `${userText.slice(0, 44)}...` : userText,
      tone: 'done',
    });
  }
  steps.push({
    key: 'orchestrator',
    label: 'Orchestrator',
    detail: hasCheck || dispatchActions.length || hasWait ? 'routing' : 'deciding',
    tone: hasCheck || dispatchActions.length || hasWait ? 'done' : 'active',
  });
  if (hasCheck) {
    steps.push({ key: 'check', label: 'Check state', detail: activeIp || 'ip', tone: 'done' });
  }
  if (dispatchActions.length || targets.length) {
    steps.push({
      key: 'dispatch',
      label: 'Dispatch',
      detail: targets.length ? targets.join(', ') : 'worker',
      tone: liveWorkers.length ? 'done' : 'active',
    });
  }
  if (liveWorkers.length) {
    steps.push({
      key: 'worker',
      label: targets.length ? targets.join(', ') : 'worker',
      detail: workerStatus || 'active',
      tone: workerRunning ? 'active' : workerPending || workerQueued ? 'pending' : 'done',
      workflow: targets[0] || workerNames[0] || '',
    });
  }
  if (hasWait || liveWorkers.length) {
    steps.push({
      key: 'wait',
      label: 'Wait result',
      detail: liveWorkers.length ? 'worker running' : 'yielded',
      tone: liveWorkers.length ? 'active' : 'pending',
    });
  }
  return { steps, activeWorkflow: targets[0] || '', activeIp };
};

export const workspaceFetchWorkerSnapshot = async (opts: any = {}): Promise<any> => {
  const api = (window as any).atlasData || {};
  if (typeof api.fetchWorkerSnapshot === 'function') {
    return api.fetchWorkerSnapshot(opts);
  }
  const w = window as any;
  const explicitWorkspace = String(w.ATLAS_WORKSPACE_SESSION_ID || '').trim();
  const activeParts = String(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
  const workspaceSession = explicitWorkspace || (activeParts.length >= 4 ? activeParts[1] || '' : '');
  const params = new URLSearchParams();
  const activeOnly = opts.activeOnly !== false && opts.active_only !== false;
  if (activeOnly) params.set('active_only', '1');
  const ip = String(opts.ip || '').trim();
  if (ip && ip !== 'default') params.set('ip', ip);
  if (workspaceSession) params.set('workspace_session', workspaceSession);
  const query = params.toString();
  const r = await fetch(`/api/orchestrator/workers${query ? `?${query}` : ''}`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`workers ${r.status}`);
  return r.json();
};

export const atlasBootScmProvider = (): string => {
  const boot = (window as any).ATLAS_BOOT_CONFIG || {};
  const provider = String(boot.scm_provider || '').trim().toLowerCase();
  return provider && provider !== 'auto' ? provider : 'git';
};
export const atlasResolveScmTab = (provider: any): any => {
  const key = String(provider || '').trim().toLowerCase();
  const overrides = (window as any).AtlasSCMTabOverrides || (window as any).SCM_TAB_OVERRIDES || {};
  if (key && typeof overrides[key] === 'function') return overrides[key];
  if (key && typeof overrides[key.toUpperCase()] === 'function') return overrides[key.toUpperCase()];
  if (typeof (window as any).AtlasSCMTab === 'function') return (window as any).AtlasSCMTab;
  if (typeof (window as any).SCMTab === 'function') return (window as any).SCMTab;
  return typeof (window as any).GitTab === 'function' ? (window as any).GitTab : null;
};
export const atlasScmTabLabel = (provider: any, component: any): string => {
  const labels = (window as any).AtlasSCMTabLabels || (window as any).SCM_TAB_LABELS || {};
  const key = String(provider || '').trim().toLowerCase();
  if (key && labels[key]) return String(labels[key]);
  if ((window as any).AtlasSCMTabLabel) return String((window as any).AtlasSCMTabLabel);
  if (component && component !== (window as any).GitTab) return key === 'perforce' ? 'perforce' : 'scm';
  return key === 'perforce' ? 'perforce' : 'git';
};

export const INPUT_HISTORY_LIMIT = 200;
export const QA_HISTORY_LIMIT = 50;
export const QA_HISTORY_LEGACY_STORAGE_KEY = 'atlasQaHistory';
export const QA_HISTORY_STORAGE_PREFIX = 'atlasQaHistory:';
