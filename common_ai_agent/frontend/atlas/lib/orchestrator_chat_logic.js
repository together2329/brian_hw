// orchestrator_chat_logic.js — browser plain-script helper.
// For ES module imports (vitest), see orchestrator_chat_logic.mjs.

(function () {
  function toolEntryFromDisplayLine(content) {
    var text = String(content || '').trim();
    if (!text) return null;
    var call = text.match(/^[▶⏺]\s*([A-Za-z_][\w.-]*)\s*(?:\(([\s\S]*)\))?\s*$/)
      || text.match(/^([A-Za-z_][\w.-]*)\s*\(([\s\S]*)\)\s*$/);
    if (call) {
      var callTool = String(call[1] || '').trim() || 'tool';
      var callArgs = call[2] === undefined ? '' : '(' + String(call[2] || '').trim() + ')';
      return { tool: callTool, args: callArgs, text: text };
    }
    var loose = text.match(/^[▶⏺]\s*([A-Za-z_][\w.-]*)\s*(.*)$/);
    if (loose) {
      return {
        tool: String(loose[1] || '').trim() || 'tool',
        args: String(loose[2] || '').trim(),
        text: text,
      };
    }
    return null;
  }

  function feedEntryFromChatMessage(message) {
    var payload = (message && message.payload) || {};
    var role = String(payload.role || '').toLowerCase();
    var displayContent = String(payload.content != null ? payload.content
      : payload.text != null ? payload.text
      : payload.raw_content != null ? payload.raw_content
      : payload.rawContent != null ? payload.rawContent : '');
    var rawContent = String(payload.raw_content != null ? payload.raw_content
      : payload.rawContent != null ? payload.rawContent : displayContent);
    var content = displayContent.trim();
    if (!content) return null;
    var created = Number((message && message.created_at) || 0);
    var createdAt = created > 0 ? created * 1000 : 0;
    var payloadTool = String(payload.tool || payload.name || payload.display_name || '').trim();
    var rawMeta = {
      rawText: rawContent,
      rawRole: role,
      source: String(payload.source || (message && message.source) || 'orchestrator_chat'),
    };

    if (role === 'assistant') {
      return Object.assign({ kind: 'agent', text: content, createdAt: createdAt }, rawMeta);
    }
    if (role === 'thought' || role === 'reasoning') {
      return Object.assign({ kind: 'thought', text: content, createdAt: createdAt }, rawMeta);
    }
    if (role === 'tool') {
      var parsed = toolEntryFromDisplayLine(content);
      if (!parsed) return null;
      return Object.assign({
        kind: 'action',
        text: parsed.text || content,
        tool: parsed.tool,
        args: parsed.args,
        createdAt: createdAt,
      }, rawMeta);
    }
    if (role === 'tool_result' || role === 'observation' || role === 'obs') {
      return Object.assign({
        kind: 'obs',
        text: content,
        tool: payloadTool,
        createdAt: createdAt,
      }, rawMeta);
    }
    return null;
  }

  function feedEntryFromWorkerLogEntry(entry, job) {
    job = job || {};
    var displayContent = String((entry && (
      entry.content != null ? entry.content
        : entry.text != null ? entry.text
        : entry.raw_content != null ? entry.raw_content : entry.rawContent
    )) || '');
    var rawContent = String((entry && (
      entry.raw_content != null ? entry.raw_content : entry.rawContent
    )) || displayContent);
    var content = displayContent.trim();
    if (!content) return null;
    var type = String((entry && entry.type) || '').toLowerCase();
    var role = String((entry && entry.role) || '').toLowerCase();
    var workflow = String((job && (job.workflow || job.stage_id)) || '').trim();
    var tool = String((entry && entry.tool) || workflow || role || 'worker').trim();
    var timestamp = Number((entry && entry.timestamp) || (job && job.started_at) || 0);
    var createdAt = timestamp > 0 ? timestamp * 1000 : 0;
    var worker = {
      job_id: String((job && job.job_id) || ''),
      run_id: String((job && job.run_id) || ''),
      workflow: workflow,
      stage_id: String((job && job.stage_id) || ''),
      status: String((job && job.status) || ''),
      worker: String((job && job.worker) || ''),
    };
    var rawMeta = {
      rawText: rawContent,
      rawRole: String((entry && (entry.raw_role || entry.rawRole || entry.role || entry.type)) || ''),
      source: String((entry && entry.source) || 'worker_log'),
    };

    // The worker prompt/context is huge and already visible in job detail.
    // The live chat should show the worker's actual ReAct/action/result flow.
    if (type === 'context') return null;
    if (type === 'task' && /^\[ATLAS ARCHITECT WORKFLOW CONTEXT\]/.test(content)) return null;

    if (type === 'action' || (role === 'assistant' && /^Action:/.test(content))) {
      var parsed = toolEntryFromDisplayLine(content);
      return Object.assign({
        kind: 'action',
        text: content,
        tool: parsed ? parsed.tool : tool,
        args: parsed ? parsed.args : '',
        createdAt: createdAt,
        live: true,
        worker: worker,
      }, rawMeta);
    }
    if (type === 'observation' || role === 'tool') {
      return Object.assign({ kind: 'obs', text: content, tool: tool, createdAt: createdAt, live: true, worker: worker }, rawMeta);
    }
    if (type === 'response' || role === 'assistant') {
      return Object.assign({ kind: 'agent', text: content, createdAt: createdAt, live: true, worker: worker }, rawMeta);
    }
    if (type === 'done') {
      return Object.assign({ kind: 'agent', text: content, createdAt: createdAt, live: true, worker: worker }, rawMeta);
    }
    return null;
  }

  function workerStatusEntryFromJob(job) {
    job = job || {};
    var jobId = String(job.job_id || job.id || '').trim();
    var workflow = String(job.workflow || job.stage_id || 'worker').trim();
    var status = String(job.status || 'active').trim();
    if (!jobId && !workflow && !status) return null;
    var workerUrl = String(job.worker || job.worker_url || '').trim();
    var model = String(job.model || '').trim();
    var runId = String(job.run_id || '').trim();
    var timestamp = Number(job.updated_at || job.finished_at || job.started_at || 0);
    var createdAt = timestamp > 0 ? timestamp * 1000 : Date.now();
    var short = function (value) {
      var text = String(value || '').trim();
      return text.length > 10 ? text.slice(0, 10) : text;
    };
    var host = workerUrl.replace(/^https?:\/\//, '');
    var bits = [
      'worker ' + workflow + ' ' + status,
      jobId ? 'job ' + short(jobId) : '',
      runId ? 'run ' + short(runId) : '',
      model ? 'model ' + model : '',
      host ? host : '',
    ].filter(Boolean);
    return {
      kind: 'worker_status',
      text: bits.join(' · '),
      createdAt: createdAt,
      live: true,
      worker: {
        job_id: jobId,
        run_id: runId,
        workflow: workflow,
        stage_id: String(job.stage_id || ''),
        status: status,
        worker: workerUrl,
      },
    };
  }

  // --- Orchestrator handoff formatting (dispatch_workflow / write_handoff) ---
  function hParseJsonObject(text) {
    if (text && typeof text === 'object' && !Array.isArray(text)) return text;
    var raw = String(text || '').trim().replace(/^└─\s*/, '');
    if (!raw || raw.charAt(0) !== '{') return null;
    try {
      var parsed = JSON.parse(raw);
      return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null;
    } catch (_) {
      return null;
    }
  }
  function hArgMetaValue(argsText, name) {
    var re = new RegExp('(?:^|[,\\s])' + name + '\\s*=\\s*(?:"([^"]*)"|\'([^\']*)\'|([^,\\s]+))');
    var match = String(argsText || '').match(re);
    return match ? (match[1] || match[2] || match[3] || '').trim() : '';
  }
  function hObjectArgValue(argsText, name) {
    var src = String(argsText || '');
    var key = src.search(new RegExp('(?:^|[,\\s])' + name + '\\s*=\\s*\\{'));
    if (key < 0) return null;
    var start = src.indexOf('{', key);
    if (start < 0) return null;
    var depth = 0;
    var quote = '';
    var esc = false;
    for (var i = start; i < src.length; i++) {
      var ch = src.charAt(i);
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
        if (depth === 0) return hParseJsonObject(src.slice(start, i + 1));
      }
    }
    return null;
  }
  function hFirstMetaValue() {
    for (var i = 0; i < arguments.length; i++) {
      var value = arguments[i];
      if (Array.isArray(value)) {
        var compact = value.map(function (v) { return String(v == null ? '' : v).trim(); })
          .filter(Boolean);
        if (compact.length) return compact.join(', ');
      } else {
        var text = String(value == null ? '' : value).trim();
        if (text) return text;
      }
    }
    return '';
  }
  function handoffStatusColor(status) {
    var s = String(status || '').toLowerCase();
    if (/(error|fail|blocked|fatal)/.test(s)) return '#f85149';
    if (/(complete|passed|done|success|\bok\b)/.test(s)) return '#3fb950';
    if (/(running|active|dispatch|in_progress|started)/.test(s)) return '#58a6ff';
    return '#8b949e';
  }
  function handoffFields(action, obs) {
    var rawArgs = action && (action.argsRaw != null ? action.argsRaw : action.args);
    var a = (rawArgs && typeof rawArgs === 'object') ? rawArgs : hParseJsonObject(rawArgs);
    if (!a && action && typeof action.args === 'string') a = hParseJsonObject(action.args);
    var argsText = (action && typeof action.args === 'string') ? action.args
      : (action && typeof action.text === 'string') ? action.text : '';
    var payload = (a && a.payload && typeof a.payload === 'object')
      ? a.payload
      : hObjectArgValue(argsText, 'payload');
    var stages = (a && Array.isArray(a.stages))
      ? a.stages.map(function (s) { return String(s || '').trim(); }).filter(Boolean) : [];
    var workflow = hFirstMetaValue(a && a.workflow, hArgMetaValue(argsText, 'workflow'));
    var target = stages.length ? stages.join(', ') : workflow;
    var sent = {
      target: target,
      fanout: stages.length > 1,
      ip: hFirstMetaValue(a && a.ip, hArgMetaValue(argsText, 'ip')),
      task: hFirstMetaValue(a && a.prompt, payload && payload.task, hArgMetaValue(argsText, 'prompt')),
      reason: hFirstMetaValue(a && a.reason, payload && payload.reason, hArgMetaValue(argsText, 'reason')),
      schedule: hFirstMetaValue(a && a.schedule, hArgMetaValue(argsText, 'schedule')),
    };
    var r = hParseJsonObject(obs && obs.text);
    var result = null;
    if (r) {
      var jobs = Array.isArray(r.jobs) ? r.jobs.filter(function (j) { return j && typeof j === 'object'; }) : [];
      result = {
        workflow: hFirstMetaValue(r.workflow, jobs.map(function (j) { return j.workflow; })) || target,
        status: hFirstMetaValue(r.status, jobs.map(function (j) { return j.status; })),
        worker: hFirstMetaValue(r.worker, r.workers, jobs.map(function (j) { return j.worker; })),
        job: hFirstMetaValue(r.job_id, r.job, jobs.map(function (j) { return j.job_id; })),
        model: hFirstMetaValue(r.model, r.models, jobs.map(function (j) { return j.model; })),
        error: hFirstMetaValue(r.error, r.result && r.result.error),
      };
      var perStage = jobs
        .map(function (j) { return { workflow: String(j.workflow || '').trim(), status: String(j.status || '').trim() }; })
        .filter(function (j) { return j.workflow; });
      if (perStage.length > 1) result.jobs = perStage;
      if (!result.status && !result.worker && !result.job && !result.error && !result.jobs) result = null;
    }
    return { sent: sent, result: result };
  }

  var api = {
    feedEntryFromChatMessage: feedEntryFromChatMessage,
    feedEntryFromWorkerLogEntry: feedEntryFromWorkerLogEntry,
    workerStatusEntryFromJob: workerStatusEntryFromJob,
    toolEntryFromDisplayLine: toolEntryFromDisplayLine,
    handoffFields: handoffFields,
    handoffStatusColor: handoffStatusColor,
  };

  if (typeof window !== 'undefined') {
    window.AtlasOrchestratorChatLogic = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
