// orchestrator_chat_logic.mjs — ES module twin of orchestrator_chat_logic.js for vitest.

const MAX_THOUGHT_LINES = 80;
const THOUGHT_COMPACTION_MARKER_RE = /^\.\.\. \(\d+ older thought lines hidden for speed\)$/;
const RUNTIME_HOUSEKEEPING_TOOLS = new Set(['read_pipeline_state', 'yield_run']);

export function cleanTerminalControlText(text) {
  return String(text || '')
    // Keep terminal-title payloads because Codex uses them for compact live
    // status such as "[1/6] ▶ in_progress | ...".
    .replace(/\x1b\]0;([^\x07\x1b]*)(?:\x07|\x1b\\)/g, (_m, title) => String(title || ''))
    .replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g, '')
    .replace(/\x1b\[[0-9;?]*[ -/]*[@-~]/g, '')
    .replace(/\x1b[@-Z\\-_]/g, '')
    .split('\n')
    .map((line) => {
      let clean = String(line || '');
      clean = clean.replace(/^\s*(?:[\u2612\uFFFD])?\]0;/, '');
      clean = clean.replace(/[\x07\x1b\\]+$/g, '');
      if (/^\s*(?:\[\d+\s*\/\s*\d+\]|[▶⏸👀✅❌*]|\[\s?\]|\[>\]|\[\.]|\[v\]|\[x\])/.test(clean)) {
        clean = clean.replace(/[\u2612\uFFFD]+$/g, '');
      }
      return clean.trimEnd();
    })
    .join('\n');
}

function isRuntimeHousekeepingTool(tool) {
  return RUNTIME_HOUSEKEEPING_TOOLS.has(String(tool || '').trim().toLowerCase());
}

function isRuntimeHousekeepingLine(line) {
  const text = String(line || '').trim().replace(/^⏳\s*/, '');
  if (!text) return false;
  if (/^streaming[.\u2026]*\s+\d+s\?\s+idle\s+\(limit\s+\d+s\?\)$/i.test(text)) return true;
  const normalized = text.replace(/\u2026/g, '...').replace(/\s+/g, ' ').trim();
  if (/^(?:\*?\s*)?(?:running|runn+ing|writinng|writ(?:e|ing)|loading|waiting|processing)(?:\s+(?:output|cache|state))?(?:\s*[.]{3,})?(?:\s*\(\d+\/\d+\))?\s*$/i.test(normalized)) {
    return true;
  }
  return false;
}

function stripRuntimeHousekeepingLines(text) {
  return cleanTerminalControlText(text)
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !isRuntimeHousekeepingLine(line))
    .join('\n');
}

export function toolEntryFromDisplayLine(content) {
  const text = cleanTerminalControlText(content).trim();
  if (!text) return null;
  const call = text.match(/^[▶⏺*]\s*([A-Za-z_][\w.-]*)\s*(?:\(([\s\S]*)\))?\s*$/)
    || text.match(/^([A-Za-z_][\w.-]*)\s*\(([\s\S]*)\)\s*$/);
  if (call) {
    const tool = String(call[1] || '').trim() || 'tool';
    const args = call[2] === undefined ? '' : `(${String(call[2] || '').trim()})`;
    return { tool, args, text };
  }
  const loose = text.match(/^[▶⏺*]\s*([A-Za-z_][\w.-]*)\s*(.*)$/);
  if (loose) {
    return {
      tool: String(loose[1] || '').trim() || 'tool',
      args: String(loose[2] || '').trim(),
      text,
    };
  }
  return null;
}

export function feedEntryFromChatMessage(message) {
  const payload = (message && message.payload) || {};
  const role = String(payload.role || '').toLowerCase();
  const rawContent = payload.content == null ? '' : String(payload.content);
  const content = cleanTerminalControlText(rawContent).trim();
  if (role === 'assistant_delta') {
    if (!rawContent) return null;
    const created = Number((message && message.created_at) || 0);
    return {
      kind: 'agent_delta',
      text: rawContent,
      streamId: String(payload.stream_id || payload.streamId || ''),
      createdAt: created > 0 ? created * 1000 : 0,
    };
  }
  if (!content) return null;
  const created = Number((message && message.created_at) || 0);
  const createdAt = created > 0 ? created * 1000 : 0;
  const payloadTool = String(payload.tool || payload.name || payload.display_name || '').trim();

  if (role === 'user') {
    return { kind: 'user', text: content, createdAt };
  }
  if (role === 'assistant') {
    return { kind: 'agent', text: content, createdAt };
  }
  if (role === 'thought' || role === 'reasoning') {
    const cleanText = stripRuntimeHousekeepingLines(content);
    if (!cleanText) return null;
    return { kind: 'thought', text: cleanText, createdAt };
  }
  if (role === 'tool') {
    const parsed = toolEntryFromDisplayLine(content);
    if (!parsed) return null;
    if (isRuntimeHousekeepingTool(parsed.tool)) return null;
    return {
      kind: 'action',
      text: parsed.text || content,
      tool: parsed.tool,
      args: parsed.args,
      createdAt,
    };
  }
  if (role === 'tool_result' || role === 'observation' || role === 'obs') {
    if (isRuntimeHousekeepingTool(payloadTool)) return null;
    return {
      kind: 'obs',
      text: content,
      tool: payloadTool,
      createdAt,
    };
  }
  return null;
}

export function feedEntryFromWorkerLogEntry(entry, job = {}) {
  const content = cleanTerminalControlText(String((entry && (entry.content ?? entry.text)) || '')).trim();
  if (!content) return null;
  const type = String((entry && entry.type) || '').toLowerCase();
  const role = String((entry && entry.role) || '').toLowerCase();
  const workflow = String((job && (job.workflow || job.stage_id)) || '').trim();
  const tool = String((entry && entry.tool) || workflow || role || 'worker').trim();
  const timestamp = Number((entry && entry.timestamp) || (job && job.started_at) || 0);
  const createdAt = timestamp > 0 ? timestamp * 1000 : 0;
  const worker = {
    job_id: String((job && job.job_id) || ''),
    run_id: String((job && job.run_id) || ''),
    workflow,
    stage_id: String((job && job.stage_id) || ''),
    status: String((job && job.status) || ''),
    worker: String((job && job.worker) || ''),
  };

  // The worker prompt/context is huge and already visible in job detail.
  // The live chat should show the worker's actual ReAct/action/result flow.
  if (type === 'context') return null;
  if (type === 'task' && /^\[ATLAS ARCHITECT WORKFLOW CONTEXT\]/.test(content)) return null;

  if (type === 'action' || (role === 'assistant' && /^Action:/.test(content))) {
    const parsed = toolEntryFromDisplayLine(content);
    if (parsed && isRuntimeHousekeepingTool(parsed.tool)) return null;
    return {
      kind: 'action',
      text: content,
      tool: parsed ? parsed.tool : tool,
      args: parsed ? parsed.args : '',
      createdAt,
      live: true,
      worker,
    };
  }
  if (type === 'observation' || role === 'tool') {
    if (isRuntimeHousekeepingTool(tool)) return null;
    return { kind: 'obs', text: content, tool, createdAt, live: true, worker };
  }
  if (type === 'response' || role === 'assistant') {
    return { kind: 'agent', text: content, createdAt, live: true, worker };
  }
  if (type === 'log' || type === 'stdout' || type === 'stderr' || role === 'stdout' || role === 'stderr') {
    const parsed = toolEntryFromDisplayLine(content);
    if (parsed) {
      if (isRuntimeHousekeepingTool(parsed.tool)) return null;
      return {
        kind: 'action',
        text: parsed.text || content,
        tool: parsed.tool,
        args: parsed.args,
        createdAt,
        live: true,
        worker,
      };
    }
    if (/^[⎿└├│]/.test(content)) {
      if (isRuntimeHousekeepingTool(tool)) return null;
      return { kind: 'obs', text: content, tool, createdAt, live: true, worker };
    }
    const text = stripRuntimeHousekeepingLines(content.replace(/^┃\s?/, '').trim());
    if (!text) return null;
    return { kind: 'thought', text, createdAt, live: true, worker };
  }
  if (type === 'done') {
    return { kind: 'agent', text: content, createdAt, live: true, worker };
  }
  return null;
}

const WORKER_TODO_STATUS_MARKS = {
  '⏸': 'pending',
  '▶': 'in_progress',
  '👀': 'completed',
  '✅': 'approved',
  '❌': 'rejected',
  '-': 'pending',
  '>': 'in_progress',
  '[ ]': 'pending',
  '[>]': 'in_progress',
  '[.]': 'completed',
  '[v]': 'approved',
  '[x]': 'rejected',
};

function workerTodoState(glyph, status) {
  const raw = String(status || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
  if (raw === 'in_progress' || raw === 'inprogress' || raw === 'active' || raw === 'running') return 'in_progress';
  if (raw === 'done' || raw === 'completed') return 'completed';
  if (raw === 'approved' || raw === 'ok' || raw === 'passed') return 'approved';
  if (raw === 'rejected' || raw === 'blocked' || raw === 'failed' || raw === 'error' || raw === 'fail') return 'rejected';
  if (raw === 'stale') return 'blocked';
  if (raw === 'locked') return 'blocked';
  const mark = WORKER_TODO_STATUS_MARKS[String(glyph || '').trim()];
  if (mark) return mark;
  return 'pending';
}

function workerTodoId(workflow, title, ordinal) {
  const slug = String(title || '')
    .toLowerCase()
    .replace(/[^a-z0-9가-힣]+/gi, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 56);
  return `worker-${String(workflow || 'worker').replace(/[^a-z0-9_-]+/gi, '-')}-${slug || ordinal}`;
}

function parseWorkerTodoLine(line, workflow, ordinal) {
  const row = cleanTerminalControlText(line)
    .replace(/^[⎿└├│]\s*/, '')
    .replace(/^[-*•]\s*/, '')
    .trim();
  if (!row || /^total:/i.test(row) || /^\d+\s+tasks?\b/i.test(row)) return null;
  const match = row.match(/^(?:\[(\d+)\s*\/\s*(\d+)\]\s*)?(?:(⏸|▶|👀|✅|❌|-|>|\[\s?\]|\[>\]|\[\.]|\[v\]|\[x\])\s*)?(?:(pending|in[_\s-]?progress|inprogress|active|running|completed|done|approved|rejected|blocked|failed|error|ok|passed|stale|locked)\s*)?(?:\|\s*)?(.+?)\s*$/i);
  if (!match) return null;
  const hasTodoMarker = !!(match[1] || match[2] || match[4] || (match[3] && row.includes('|')));
  if (!hasTodoMarker) return null;
  const title = String(match[5] || '').trim();
  if (!title || /^[-─]+$/.test(title) || /^todo\b/i.test(title)) return null;
  const idx = match[1] || ordinal;
  const state = workerTodoState(match[3], match[4]);
  return {
    id: workerTodoId(workflow, title, idx),
    state,
    section: 'worker-local',
    title,
    detail: 'Worker-local task from the live worker transcript.',
    sourceRefs: [],
    criteria: [],
    deps: [],
  };
}

export function workerLocalTodosFromFeed(feed, workflow = 'worker') {
  const list = Array.isArray(feed) ? feed : [];
  const byTitle = new Map();
  let ordinal = 0;
  for (const entry of list) {
    const text = cleanTerminalControlText(entry && entry.text);
    if (!text) continue;
    for (const line of text.split(/\r?\n/)) {
      ordinal += 1;
      const todo = parseWorkerTodoLine(line, workflow, ordinal);
      if (!todo) continue;
      const key = todo.title.toLowerCase();
      byTitle.set(key, todo);
    }
  }
  return Array.from(byTitle.values());
}

export function isThinkingPlaceholderLine(line) {
  let normalized = String(line || '').trim();
  for (let i = 0; i < 3; i++) {
    normalized = normalized
      .replace(/^[^A-Za-z0-9]+/, '')
      .replace(/^(?:thought|reasoning)\b\s*[:\])\-–—]*/i, '')
      .trim();
  }
  normalized = normalized
    .replace(/^[^A-Za-z0-9]+/, '')
    .replace(/[.\u2026\s]+$/g, '')
    .toLowerCase();
  return normalized === 'thinking';
}

export function isThinkingPlaceholderText(text) {
  const lines = String(text || '').split('\n').map((line) => line.trim()).filter(Boolean);
  return !!lines.length && lines.every(isThinkingPlaceholderLine);
}

export function visibleThoughtLines(text) {
  const lines = String(text || '').split('\n').map((line) => line.trim()).filter(Boolean);
  if (!lines.length) return [];
  const real = lines.filter((line) => !isThinkingPlaceholderLine(line) && !THOUGHT_COMPACTION_MARKER_RE.test(line));
  return real;
}

export function compactThoughtText(text, maxLines = MAX_THOUGHT_LINES) {
  const lines = visibleThoughtLines(text);
  if (lines.length <= maxLines) return lines.join('\n');
  return [
    `... (${lines.length - maxLines} older thought lines hidden for speed)`,
    ...lines.slice(-maxLines),
  ].join('\n');
}

export function coalesceFeedEntries(existing = [], incoming = []) {
  const out = Array.isArray(existing) ? existing.slice() : [];
  const fresh = Array.isArray(incoming) ? incoming : [incoming];
  const sameWorkerContext = (prev, entry) => {
    const prevWorker = prev && prev.worker ? prev.worker : {};
    const nextWorker = entry && entry.worker ? entry.worker : {};
    const workerKeys = ['job_id', 'run_id', 'workflow', 'stage_id'];
    for (const key of workerKeys) {
      const a = String(prevWorker[key] || '');
      const b = String(nextWorker[key] || '');
      if (a && b && a !== b) return false;
    }
    return true;
  };
  const looksLikeThoughtStart = (text) => {
    const first = String(text || '').split('\n').map((line) => line.trim()).find(Boolean) || '';
    return /^(?:THOUGHT|REASONING)(?:\s|\(|:|$)|^[-─]{2,}\s|^Let me\b|^I\s+\b|^\*\s+in\s+\d/i.test(first);
  };
  const shouldMergeStdoutContinuationIntoObs = (prev, entry) => {
    if (!prev || prev.kind !== 'obs' || !entry || entry.kind !== 'thought') return false;
    if (!prev.live || !entry.live) return false;
    if (!sameWorkerContext(prev, entry)) return false;
    if (looksLikeThoughtStart(entry.text)) return false;
    return true;
  };
  const shouldMergeObs = (prev, entry) => {
    if (!prev || prev.kind !== 'obs' || !entry || entry.kind !== 'obs') return false;
    if (!sameWorkerContext(prev, entry)) return false;
    const prevTool = String(prev.tool || '');
    const nextTool = String(entry.tool || '');
    return !prevTool || !nextTool || prevTool === nextTool;
  };

  for (const raw of fresh) {
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
      ? { ...raw, text: compactThoughtText(raw.text) }
      : raw;
    if (entry.kind === 'thought' && !String(entry.text || '').trim()) continue;
    const isThought = entry.kind === 'thought';
    const incomingPlaceholder = isThought && isThinkingPlaceholderText(entry.text);
    const last = out[out.length - 1];
    const lastPlaceholder = last && last.kind === 'thought' && isThinkingPlaceholderText(last.text);

    if (incomingPlaceholder) {
      continue;
    }

    if (lastPlaceholder) {
      out.pop();
    }

    const prev = out[out.length - 1];
    if (shouldMergeStdoutContinuationIntoObs(prev, entry)) {
      const prevText = String(prev.text || '').trim();
      const nextText = String(entry.text || '').trim();
      if (!nextText) continue;
      out[out.length - 1] = {
        ...prev,
        ...entry,
        kind: 'obs',
        text: prevText ? `${prevText}\n${nextText}` : nextText,
        tool: prev.tool || entry.tool,
      };
      continue;
    }
    if (isThought && prev && prev.kind === 'thought') {
      const prevText = String(prev.text || '').trim();
      const nextText = String(entry.text || '').trim();
      if (!nextText) continue;
      if (prevText === nextText) {
        out[out.length - 1] = { ...prev, ...entry, text: prev.text };
      } else {
        const mergedText = compactThoughtText(prevText ? `${prevText}\n${nextText}` : nextText);
        out[out.length - 1] = {
          ...prev,
          ...entry,
          text: mergedText,
        };
      }
      continue;
    }
    if (shouldMergeObs(prev, entry)) {
      const prevText = String(prev.text || '').trim();
      const nextText = String(entry.text || '').trim();
      if (!nextText) continue;
      out[out.length - 1] = {
        ...prev,
        ...entry,
        text: prevText ? `${prevText}\n${nextText}` : nextText,
        tool: prev.tool || entry.tool,
      };
      continue;
    }

    out.push(entry);
  }

  return out;
}

// --- Orchestrator handoff formatting (dispatch_workflow / write_handoff) ---
// Turns a handoff tool call (+ optional result obs) into clean labeled fields
// for the HandoffCard UI, instead of dumping raw JSON args. Tolerant of three
// arg shapes: a structured object (hydrated tool_calls carry argsRaw), a JSON
// string, or the flattened "key=value, key=value" text the live stream carries.

function _hParseJsonObject(text) {
  if (text && typeof text === 'object' && !Array.isArray(text)) return text;
  const raw = String(text || '').trim().replace(/^└─\s*/, '');
  if (!raw || !raw.startsWith('{')) return null;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null;
  } catch (_) {
    return null;
  }
}

function _hArgMetaValue(argsText, name) {
  const re = new RegExp('(?:^|[,\\s])' + name + '\\s*=\\s*(?:"([^"]*)"|\'([^\']*)\'|([^,\\s]+))');
  const match = String(argsText || '').match(re);
  return match ? (match[1] || match[2] || match[3] || '').trim() : '';
}

function _hValueText(value) {
  if (value == null) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') return String(value).trim();
  try {
    return JSON.stringify(value);
  } catch (_) {
    return String(value).trim();
  }
}

function _hFirstMetaValue(...values) {
  for (const value of values) {
    if (Array.isArray(value)) {
      const compact = value.map(_hValueText).filter(Boolean);
      if (compact.length) return compact.join(', ');
    } else {
      const text = _hValueText(value);
      if (text) return text;
    }
  }
  return '';
}

export function handoffStatusColor(status) {
  const s = String(status || '').toLowerCase();
  if (/(error|fail|blocked|fatal)/.test(s)) return '#f85149';
  if (/(complete|passed|done|success|\bok\b)/.test(s)) return '#3fb950';
  if (/(running|active|dispatch|in_progress|started)/.test(s)) return '#58a6ff';
  return '#8b949e';  // queued / pending / unknown
}

export function handoffFields(action, obs) {
  const rawArgs = action && (action.argsRaw != null ? action.argsRaw : action.args);
  let a = (rawArgs && typeof rawArgs === 'object') ? rawArgs : _hParseJsonObject(rawArgs);
  if (!a && action && typeof action.args === 'string') a = _hParseJsonObject(action.args);
  const argsText = (action && typeof action.args === 'string') ? action.args
    : (action && typeof action.text === 'string') ? action.text : '';
  let payload = (a && a.payload && typeof a.payload === 'object') ? a.payload : null;
  if (!payload) {
    // write_handoff carries the task in a nested payload={...} blob even on
    // the flattened "key=val" string path — pull it out so task/reason show.
    const pm = String(argsText || '').match(/payload\s*=\s*(\{[\s\S]*?\})/);
    if (pm) { try { const pj = JSON.parse(pm[1]); if (pj && typeof pj === 'object') payload = pj; } catch (_) {} }
  }
  const stages = (a && Array.isArray(a.stages))
    ? a.stages.map(_hValueText).filter(Boolean) : [];
  const workflow = _hFirstMetaValue(a && a.workflow, _hArgMetaValue(argsText, 'workflow'));
  const target = stages.length ? stages.join(', ') : workflow;
  const sent = {
    target,
    fanout: stages.length > 1,
    ip: _hFirstMetaValue(a && a.ip, _hArgMetaValue(argsText, 'ip')),
    task: _hFirstMetaValue(a && a.prompt, payload && payload.task, _hArgMetaValue(argsText, 'prompt')),
    reason: _hFirstMetaValue(a && a.reason, payload && payload.reason, _hArgMetaValue(argsText, 'reason')),
    schedule: _hFirstMetaValue(a && a.schedule, _hArgMetaValue(argsText, 'schedule')),
  };
  const r = _hParseJsonObject(obs && obs.text);
  let result = null;
  if (r) {
    const jobs = Array.isArray(r.jobs) ? r.jobs.filter(j => j && typeof j === 'object') : [];
    result = {
      workflow: _hFirstMetaValue(r.workflow, jobs.map(j => j.workflow)) || target,
      status: _hFirstMetaValue(r.status, jobs.map(j => j.status)),
      worker: _hFirstMetaValue(r.worker, r.workers, jobs.map(j => j.worker)),
      job: _hFirstMetaValue(r.job_id, r.job, jobs.map(j => j.job_id)),
      model: _hFirstMetaValue(r.model, r.models, jobs.map(j => j.model)),
      error: _hFirstMetaValue(r.error, r.result && r.result.error),
    };
    // Fan-out: keep per-stage workflow/status so the card can show
    // "lint ● running · tb ● running · syn ● queued" instead of one merged dot.
    const perStage = jobs
      .map(j => ({ workflow: _hValueText(j.workflow), status: _hValueText(j.status) }))
      .filter(j => j.workflow);
    if (perStage.length > 1) result.jobs = perStage;
    if (!result.status && !result.worker && !result.job && !result.error && !result.jobs) result = null;
  }
  return { sent, result };
}
