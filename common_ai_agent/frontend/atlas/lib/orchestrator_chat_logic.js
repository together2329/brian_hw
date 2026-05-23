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
    var content = String(payload.content || '').trim();
    if (!content) return null;
    var created = Number((message && message.created_at) || 0);
    var createdAt = created > 0 ? created * 1000 : 0;
    var payloadTool = String(payload.tool || payload.name || payload.display_name || '').trim();

    if (role === 'assistant') {
      return { kind: 'agent', text: content, createdAt: createdAt };
    }
    if (role === 'thought' || role === 'reasoning') {
      return { kind: 'thought', text: content, createdAt: createdAt };
    }
    if (role === 'tool') {
      var parsed = toolEntryFromDisplayLine(content);
      if (!parsed) return null;
      return {
        kind: 'action',
        text: parsed.text || content,
        tool: parsed.tool,
        args: parsed.args,
        createdAt: createdAt,
      };
    }
    if (role === 'tool_result' || role === 'observation' || role === 'obs') {
      return {
        kind: 'obs',
        text: content,
        tool: payloadTool,
        createdAt: createdAt,
      };
    }
    return null;
  }

  function feedEntryFromWorkerLogEntry(entry, job) {
    job = job || {};
    var content = String((entry && (entry.content != null ? entry.content : entry.text)) || '').trim();
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

    // The worker prompt/context is huge and already visible in job detail.
    // The live chat should show the worker's actual ReAct/action/result flow.
    if (type === 'context') return null;
    if (type === 'task' && /^\[ATLAS ARCHITECT WORKFLOW CONTEXT\]/.test(content)) return null;

    if (type === 'action' || (role === 'assistant' && /^Action:/.test(content))) {
      var parsed = toolEntryFromDisplayLine(content);
      return {
        kind: 'action',
        text: content,
        tool: parsed ? parsed.tool : tool,
        args: parsed ? parsed.args : '',
        createdAt: createdAt,
        live: true,
        worker: worker,
      };
    }
    if (type === 'observation' || role === 'tool') {
      return { kind: 'obs', text: content, tool: tool, createdAt: createdAt, live: true, worker: worker };
    }
    if (type === 'response' || role === 'assistant') {
      return { kind: 'agent', text: content, createdAt: createdAt, live: true, worker: worker };
    }
    if (type === 'done') {
      return { kind: 'agent', text: content, createdAt: createdAt, live: true, worker: worker };
    }
    return null;
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
    var payload = (a && a.payload && typeof a.payload === 'object') ? a.payload : null;
    if (!payload) {
      // write_handoff carries the task in a nested payload={...} blob even on
      // the flattened "key=val" string path — pull it out so task/reason show.
      var pm = String(argsText || '').match(/payload\s*=\s*(\{[\s\S]*?\})/);
      if (pm) { try { var pj = JSON.parse(pm[1]); if (pj && typeof pj === 'object') payload = pj; } catch (_) {} }
    }
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
