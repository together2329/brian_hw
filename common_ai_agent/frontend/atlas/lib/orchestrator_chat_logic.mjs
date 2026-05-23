// orchestrator_chat_logic.mjs — ES module twin of orchestrator_chat_logic.js for vitest.

export function toolEntryFromDisplayLine(content) {
  const text = String(content || '').trim();
  if (!text) return null;
  const call = text.match(/^[▶⏺]\s*([A-Za-z_][\w.-]*)\s*(?:\(([\s\S]*)\))?\s*$/)
    || text.match(/^([A-Za-z_][\w.-]*)\s*\(([\s\S]*)\)\s*$/);
  if (call) {
    const tool = String(call[1] || '').trim() || 'tool';
    const args = call[2] === undefined ? '' : `(${String(call[2] || '').trim()})`;
    return { tool, args, text };
  }
  const loose = text.match(/^[▶⏺]\s*([A-Za-z_][\w.-]*)\s*(.*)$/);
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
  const displayContent = String(payload.content ?? payload.text ?? payload.raw_content ?? payload.rawContent ?? '');
  const rawContent = String(payload.raw_content ?? payload.rawContent ?? displayContent);
  const content = displayContent.trim();
  if (!content) return null;
  const created = Number((message && message.created_at) || 0);
  const createdAt = created > 0 ? created * 1000 : 0;
  const payloadTool = String(payload.tool || payload.name || payload.display_name || '').trim();
  const rawMeta = {
    rawText: rawContent,
    rawRole: role,
    source: String(payload.source || (message && message.source) || 'orchestrator_chat'),
  };

  if (role === 'assistant') {
    return { kind: 'agent', text: content, createdAt, ...rawMeta };
  }
  if (role === 'thought' || role === 'reasoning') {
    return { kind: 'thought', text: content, createdAt, ...rawMeta };
  }
  if (role === 'tool') {
    const parsed = toolEntryFromDisplayLine(content);
    if (!parsed) return null;
    return {
      kind: 'action',
      text: parsed.text || content,
      tool: parsed.tool,
      args: parsed.args,
      createdAt,
      ...rawMeta,
    };
  }
  if (role === 'tool_result' || role === 'observation' || role === 'obs') {
    return {
      kind: 'obs',
      text: content,
      tool: payloadTool,
      createdAt,
      ...rawMeta,
    };
  }
  return null;
}

export function feedEntryFromWorkerLogEntry(entry, job = {}) {
  const displayContent = String((entry && (entry.content ?? entry.text ?? entry.raw_content ?? entry.rawContent)) || '');
  const rawContent = String((entry && (entry.raw_content ?? entry.rawContent)) || displayContent);
  const content = displayContent.trim();
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
  const rawMeta = {
    rawText: rawContent,
    rawRole: String((entry && (entry.raw_role || entry.rawRole || entry.role || entry.type)) || ''),
    source: String((entry && entry.source) || 'worker_log'),
  };

  // The worker prompt/context is huge and already visible in job detail.
  // The live chat should show the worker's actual ReAct/action/result flow.
  if (type === 'context') return null;
  if (type === 'task' && /^\[ATLAS ARCHITECT WORKFLOW CONTEXT\]/.test(content)) return null;

  if (type === 'action' || (role === 'assistant' && /^Action:/.test(content))) {
    const parsed = toolEntryFromDisplayLine(content);
    return {
      kind: 'action',
      text: content,
      tool: parsed ? parsed.tool : tool,
      args: parsed ? parsed.args : '',
      createdAt,
      live: true,
      worker,
      ...rawMeta,
    };
  }
  if (type === 'observation' || role === 'tool') {
    return { kind: 'obs', text: content, tool, createdAt, live: true, worker, ...rawMeta };
  }
  if (type === 'response' || role === 'assistant') {
    return { kind: 'agent', text: content, createdAt, live: true, worker, ...rawMeta };
  }
  if (type === 'done') {
    return { kind: 'agent', text: content, createdAt, live: true, worker, ...rawMeta };
  }
  return null;
}

export function workerStatusEntryFromJob(job = {}) {
  const jobId = String(job.job_id || job.id || '').trim();
  const workflow = String(job.workflow || job.stage_id || 'worker').trim();
  const status = String(job.status || 'active').trim();
  if (!jobId && !workflow && !status) return null;
  const worker = String(job.worker || job.worker_url || '').trim();
  const model = String(job.model || '').trim();
  const runId = String(job.run_id || '').trim();
  const timestamp = Number(job.updated_at || job.finished_at || job.started_at || 0);
  const createdAt = timestamp > 0 ? timestamp * 1000 : Date.now();
  const short = (value) => {
    const text = String(value || '').trim();
    return text.length > 10 ? text.slice(0, 10) : text;
  };
  const host = worker.replace(/^https?:\/\//, '');
  const bits = [
    `worker ${workflow} ${status}`,
    jobId ? `job ${short(jobId)}` : '',
    runId ? `run ${short(runId)}` : '',
    model ? `model ${model}` : '',
    host ? host : '',
  ].filter(Boolean);
  return {
    kind: 'worker_status',
    text: bits.join(' · '),
    createdAt,
    live: true,
    worker: {
      job_id: jobId,
      run_id: runId,
      workflow,
      stage_id: String(job.stage_id || ''),
      status,
      worker,
    },
  };
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

function _hObjectArgValue(argsText, name) {
  const src = String(argsText || '');
  const key = src.search(new RegExp('(?:^|[,\\s])' + name + '\\s*=\\s*\\{'));
  if (key < 0) return null;
  const start = src.indexOf('{', key);
  if (start < 0) return null;
  let depth = 0;
  let quote = '';
  let esc = false;
  for (let i = start; i < src.length; i++) {
    const ch = src[i];
    if (quote) {
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === quote) quote = '';
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      continue;
    }
    if (ch === '{') depth++;
    else if (ch === '}') {
      depth--;
      if (depth === 0) return _hParseJsonObject(src.slice(start, i + 1));
    }
  }
  return null;
}

function _hFirstMetaValue(...values) {
  for (const value of values) {
    if (Array.isArray(value)) {
      const compact = value.map(v => String(v == null ? '' : v).trim()).filter(Boolean);
      if (compact.length) return compact.join(', ');
    } else {
      const text = String(value == null ? '' : value).trim();
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
  const payload = (a && a.payload && typeof a.payload === 'object')
    ? a.payload
    : _hObjectArgValue(argsText, 'payload');
  const stages = (a && Array.isArray(a.stages))
    ? a.stages.map(s => String(s || '').trim()).filter(Boolean) : [];
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
      .map(j => ({ workflow: String(j.workflow || '').trim(), status: String(j.status || '').trim() }))
      .filter(j => j.workflow);
    if (perStage.length > 1) result.jobs = perStage;
    if (!result.status && !result.worker && !result.job && !result.error && !result.jobs) result = null;
  }
  return { sent, result };
}
