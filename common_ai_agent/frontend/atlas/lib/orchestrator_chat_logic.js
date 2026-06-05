// orchestrator_chat_logic.js — browser plain-script helper.
// For ES module imports (vitest), see orchestrator_chat_logic.mjs.

(function () {
  var MAX_THOUGHT_LINES = 80;
  var THOUGHT_COMPACTION_MARKER_RE = /^\.\.\. \(\d+ older thought lines hidden for speed\)$/;
  var RUNTIME_HOUSEKEEPING_TOOLS = {
    read_pipeline_state: true,
    yield_run: true,
  };

  function cleanTerminalControlText(text) {
    return String(text || '')
      // Keep terminal-title payloads because Codex uses them for compact live
      // status such as "[1/6] ▶ in_progress | ...".
      .replace(/\x1b\]0;([^\x07\x1b]*)(?:\x07|\x1b\\)/g, function (_m, title) { return String(title || ''); })
      .replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g, '')
      .replace(/\x1b\[[0-9;?]*[ -/]*[@-~]/g, '')
      .replace(/\x1b[@-Z\\-_]/g, '')
      .split('\n')
      .map(function (line) {
        var clean = String(line || '');
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
    return !!RUNTIME_HOUSEKEEPING_TOOLS[String(tool || '').trim().toLowerCase()];
  }

 function isRuntimeHousekeepingLine(line) {
    var text = String(line || '').trim().replace(/^⏳\s*/, '');
    if (!text) return false;
    var normalized = String(text || '').replace(/\u2026/g, '...').replace(/\s+/g, ' ').trim();
    if (/^streaming[.\u2026]*\s+\d+s\?\s+idle\s+\(limit\s+\d+s\?\)$/i.test(text)) return true;
    if (/^(?:\*?\s*)?(?:running|runn+ing|writinng|writ(?:e|ing)|loading|waiting|processing)(?:\s+(?:output|cache|state))?(?:\s*[.]{3,})?(?:\s*\(\d+\/\d+\))?\s*$/i.test(normalized)) {
      return true;
    }
    return false;
  }

  function stripRuntimeHousekeepingLines(text) {
    return cleanTerminalControlText(text)
      .split('\n')
      .map(function (line) { return line.trim(); })
      .filter(function (line) { return line && !isRuntimeHousekeepingLine(line); })
      .join('\n');
  }

  function toolEntryFromDisplayLine(content) {
    var text = cleanTerminalControlText(content).trim();
    if (!text) return null;
    var call = text.match(/^[▶⏺*]\s*([A-Za-z_][\w.-]*)\s*(?:\(([\s\S]*)\))?\s*$/)
      || text.match(/^([A-Za-z_][\w.-]*)\s*\(([\s\S]*)\)\s*$/);
    if (call) {
      var callTool = String(call[1] || '').trim() || 'tool';
      var callArgs = call[2] === undefined ? '' : '(' + String(call[2] || '').trim() + ')';
      return { tool: callTool, args: callArgs, text: text };
    }
    var loose = text.match(/^[▶⏺*]\s*([A-Za-z_][\w.-]*)\s*(.*)$/);
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
    var rawContent = payload.content == null ? '' : String(payload.content);
    var content = cleanTerminalControlText(rawContent).trim();
    if (role === 'assistant_delta') {
      if (!rawContent) return null;
      return {
        kind: 'agent_delta',
        text: rawContent,
        streamId: String(payload.stream_id || payload.streamId || ''),
        createdAt: Number((message && message.created_at) || 0) > 0
          ? Number((message && message.created_at) || 0) * 1000
          : 0,
      };
    }
    if (!content) return null;
    var created = Number((message && message.created_at) || 0);
    var createdAt = created > 0 ? created * 1000 : 0;
    var payloadTool = String(payload.tool || payload.name || payload.display_name || '').trim();

    if (role === 'user') {
      return { kind: 'user', text: content, createdAt: createdAt };
    }
    if (role === 'assistant') {
      return { kind: 'agent', text: content, createdAt: createdAt };
    }
    if (role === 'thought' || role === 'reasoning') {
      var cleanText = stripRuntimeHousekeepingLines(content);
      if (!cleanText) return null;
      return { kind: 'thought', text: cleanText, createdAt: createdAt };
    }
    if (role === 'tool') {
      var parsed = toolEntryFromDisplayLine(content);
      if (!parsed) return null;
      if (isRuntimeHousekeepingTool(parsed.tool)) return null;
      return {
        kind: 'action',
        text: parsed.text || content,
        tool: parsed.tool,
        args: parsed.args,
        createdAt: createdAt,
      };
    }
    if (role === 'tool_result' || role === 'observation' || role === 'obs') {
      if (isRuntimeHousekeepingTool(payloadTool)) return null;
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
    var content = cleanTerminalControlText(String((entry && (entry.content != null ? entry.content : entry.text)) || '')).trim();
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
      if (parsed && isRuntimeHousekeepingTool(parsed.tool)) return null;
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
      if (isRuntimeHousekeepingTool(tool)) return null;
      return { kind: 'obs', text: content, tool: tool, createdAt: createdAt, live: true, worker: worker };
    }
    if (type === 'response' || role === 'assistant') {
      return { kind: 'agent', text: content, createdAt: createdAt, live: true, worker: worker };
    }
    if (type === 'log' || type === 'stdout' || type === 'stderr' || role === 'stdout' || role === 'stderr') {
      var parsedLog = toolEntryFromDisplayLine(content);
      if (parsedLog) {
        if (isRuntimeHousekeepingTool(parsedLog.tool)) return null;
        return {
          kind: 'action',
          text: parsedLog.text || content,
          tool: parsedLog.tool,
          args: parsedLog.args,
          createdAt: createdAt,
          live: true,
          worker: worker,
        };
      }
      if (/^[⎿└├│]/.test(content)) {
        if (isRuntimeHousekeepingTool(tool)) return null;
        return { kind: 'obs', text: content, tool: tool, createdAt: createdAt, live: true, worker: worker };
      }
      var cleanLogText = stripRuntimeHousekeepingLines(content.replace(/^┃\s?/, '').trim());
      if (!cleanLogText) return null;
      return {
        kind: 'thought',
        text: cleanLogText,
        createdAt: createdAt,
        live: true,
        worker: worker,
      };
    }
    if (type === 'done') {
      return { kind: 'agent', text: content, createdAt: createdAt, live: true, worker: worker };
    }
    return null;
  }

  var WORKER_TODO_STATUS_MARKS = {
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
    var raw = String(status || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
    if (raw === 'in_progress' || raw === 'inprogress' || raw === 'active' || raw === 'running') return 'in_progress';
    if (raw === 'done' || raw === 'completed') return 'completed';
    if (raw === 'approved' || raw === 'ok' || raw === 'passed') return 'approved';
    if (raw === 'rejected' || raw === 'blocked' || raw === 'failed' || raw === 'error' || raw === 'fail') return 'rejected';
    if (raw === 'stale' || raw === 'locked') return 'blocked';
    var mark = WORKER_TODO_STATUS_MARKS[String(glyph || '').trim()];
    if (mark) return mark;
    return 'pending';
  }

  function workerTodoId(workflow, title, ordinal) {
    var slug = String(title || '')
      .toLowerCase()
      .replace(/[^a-z0-9가-힣]+/gi, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 56);
    return 'worker-' + String(workflow || 'worker').replace(/[^a-z0-9_-]+/gi, '-') + '-' + (slug || ordinal);
  }

  function parseWorkerTodoLine(line, workflow, ordinal) {
    var row = cleanTerminalControlText(line)
      .replace(/^[⎿└├│]\s*/, '')
      .replace(/^[-*•]\s*/, '')
      .trim();
    if (!row || /^total:/i.test(row) || /^\d+\s+tasks?\b/i.test(row)) return null;
    var match = row.match(/^(?:\[(\d+)\s*\/\s*(\d+)\]\s*)?(?:(⏸|▶|👀|✅|❌|-|>|\[\s?\]|\[>\]|\[\.]|\[v\]|\[x\])\s*)?(?:(pending|in[_\s-]?progress|inprogress|active|running|completed|done|approved|rejected|blocked|failed|error|ok|passed|stale|locked)\s*)?(?:\|\s*)?(.+?)\s*$/i);
    if (!match) return null;
    var hasTodoMarker = !!(match[1] || match[2] || match[4] || (match[3] && row.indexOf('|') >= 0));
    if (!hasTodoMarker) return null;
    var title = String(match[5] || '').trim();
    if (!title || /^[-─]+$/.test(title) || /^todo\b/i.test(title)) return null;
    var idx = match[1] || ordinal;
    var state = workerTodoState(match[3], match[4]);
    return {
      id: workerTodoId(workflow, title, idx),
      state: state,
      section: 'worker-local',
      title: title,
      detail: 'Worker-local task from the live worker transcript.',
      sourceRefs: [],
      criteria: [],
      deps: [],
    };
  }

  function workerLocalTodosFromFeed(feed, workflow) {
    workflow = workflow || 'worker';
    var list = Array.isArray(feed) ? feed : [];
    var byTitle = new Map();
    var ordinal = 0;
    list.forEach(function (entry) {
      var text = cleanTerminalControlText(entry && entry.text);
      if (!text) return;
      text.split(/\r?\n/).forEach(function (line) {
        ordinal += 1;
        var todo = parseWorkerTodoLine(line, workflow, ordinal);
        if (!todo) return;
        byTitle.set(todo.title.toLowerCase(), todo);
      });
    });
    return Array.from(byTitle.values());
  }

  function isThinkingPlaceholderLine(line) {
    var normalized = String(line || '').trim();
    for (var i = 0; i < 3; i++) {
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

  function isThinkingPlaceholderText(text) {
    var lines = String(text || '').split('\n').map(function (line) { return line.trim(); }).filter(Boolean);
    return !!lines.length && lines.every(isThinkingPlaceholderLine);
  }

  function visibleThoughtLines(text) {
    var lines = String(text || '').split('\n').map(function (line) { return line.trim(); }).filter(Boolean);
    if (!lines.length) return [];
    var real = lines.filter(function (line) { return !isThinkingPlaceholderLine(line) && !THOUGHT_COMPACTION_MARKER_RE.test(line); });
    return real;
  }

  function compactThoughtText(text, maxLines) {
    maxLines = maxLines || MAX_THOUGHT_LINES;
    var lines = visibleThoughtLines(text);
    if (lines.length <= maxLines) return lines.join('\n');
    return ['... (' + (lines.length - maxLines) + ' older thought lines hidden for speed)']
      .concat(lines.slice(-maxLines))
      .join('\n');
  }

  function coalesceFeedEntries(existing, incoming) {
    var out = Array.isArray(existing) ? existing.slice() : [];
    var fresh = Array.isArray(incoming) ? incoming : [incoming];
    var sameWorkerContext = function (prev, entry) {
      var prevWorker = prev && prev.worker ? prev.worker : {};
      var nextWorker = entry && entry.worker ? entry.worker : {};
      var workerKeys = ['job_id', 'run_id', 'workflow', 'stage_id'];
      for (var i = 0; i < workerKeys.length; i++) {
        var key = workerKeys[i];
        var a = String(prevWorker[key] || '');
        var b = String(nextWorker[key] || '');
        if (a && b && a !== b) return false;
      }
      return true;
    };
    var looksLikeThoughtStart = function (text) {
      var first = String(text || '').split('\n').map(function (line) { return line.trim(); }).find(Boolean) || '';
      return /^(?:THOUGHT|REASONING)(?:\s|\(|:|$)|^[-─]{2,}\s|^Let me\b|^I\s+\b|^\*\s+in\s+\d/i.test(first);
    };
    var shouldMergeStdoutContinuationIntoObs = function (prev, entry) {
      if (!prev || prev.kind !== 'obs' || !entry || entry.kind !== 'thought') return false;
      if (!prev.live || !entry.live) return false;
      if (!sameWorkerContext(prev, entry)) return false;
      if (looksLikeThoughtStart(entry.text)) return false;
      return true;
    };
    var shouldMergeObs = function (prev, entry) {
      if (!prev || prev.kind !== 'obs' || !entry || entry.kind !== 'obs') return false;
      if (!sameWorkerContext(prev, entry)) return false;
      var prevTool = String(prev.tool || '');
      var nextTool = String(entry.tool || '');
      return !prevTool || !nextTool || prevTool === nextTool;
    };

    fresh.forEach(function (raw) {
      if (!raw || typeof raw !== 'object') return;
      if (raw.kind === 'agent_delta') {
        var deltaText = String(raw.text || '');
        if (!deltaText) return;
        var streamId = String(raw.streamId || raw.stream_id || '');
        var prevAgent = out[out.length - 1];
        if (prevAgent && prevAgent.kind === 'agent' && String(prevAgent.streamId || '') === streamId) {
          out[out.length - 1] = Object.assign({}, prevAgent, raw, {
            kind: 'agent',
            text: String(prevAgent.text || '') + deltaText,
            streamId: streamId,
          });
        } else {
          out.push(Object.assign({}, raw, {
            kind: 'agent',
            text: deltaText,
            streamId: streamId,
          }));
        }
        return;
      }
      var entry = raw.kind === 'thought'
        ? Object.assign({}, raw, { text: compactThoughtText(raw.text) })
        : raw;
      if (entry.kind === 'thought' && !String(entry.text || '').trim()) return;
      var isThought = entry.kind === 'thought';
      var incomingPlaceholder = isThought && isThinkingPlaceholderText(entry.text);
      var last = out[out.length - 1];
      var lastPlaceholder = last && last.kind === 'thought' && isThinkingPlaceholderText(last.text);

      if (incomingPlaceholder) {
        return;
      }

      if (lastPlaceholder) {
        out.pop();
      }

      var prev = out[out.length - 1];
      if (shouldMergeStdoutContinuationIntoObs(prev, entry)) {
        var prevContinuationText = String(prev.text || '').trim();
        var nextContinuationText = String(entry.text || '').trim();
        if (!nextContinuationText) return;
        out[out.length - 1] = Object.assign({}, prev, entry, {
          kind: 'obs',
          text: prevContinuationText ? prevContinuationText + '\n' + nextContinuationText : nextContinuationText,
          tool: prev.tool || entry.tool,
        });
        return;
      }
      if (isThought && prev && prev.kind === 'thought') {
        var prevText = String(prev.text || '').trim();
        var nextText = String(entry.text || '').trim();
        if (!nextText) return;
        if (prevText === nextText) {
          out[out.length - 1] = Object.assign({}, prev, entry, { text: prev.text });
        } else {
          var mergedText = compactThoughtText(prevText ? prevText + '\n' + nextText : nextText);
          out[out.length - 1] = Object.assign({}, prev, entry, {
            text: mergedText,
          });
        }
        return;
      }
      if (shouldMergeObs(prev, entry)) {
        var prevObsText = String(prev.text || '').trim();
        var nextObsText = String(entry.text || '').trim();
        if (!nextObsText) return;
        out[out.length - 1] = Object.assign({}, prev, entry, {
          text: prevObsText ? prevObsText + '\n' + nextObsText : nextObsText,
          tool: prev.tool || entry.tool,
        });
        return;
      }

      out.push(entry);
    });

    return out;
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
  function hValueText(value) {
    if (value == null) return '';
    if (typeof value === 'string') return value.trim();
    if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') return String(value).trim();
    try {
      return JSON.stringify(value);
    } catch (_) {
      return String(value).trim();
    }
  }
  function hFirstMetaValue() {
    for (var i = 0; i < arguments.length; i++) {
      var value = arguments[i];
      if (Array.isArray(value)) {
        var compact = value.map(hValueText).filter(Boolean);
        if (compact.length) return compact.join(', ');
      } else {
        var text = hValueText(value);
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
      ? a.stages.map(hValueText).filter(Boolean) : [];
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
        .map(function (j) { return { workflow: hValueText(j.workflow), status: hValueText(j.status) }; })
        .filter(function (j) { return j.workflow; });
      if (perStage.length > 1) result.jobs = perStage;
      if (!result.status && !result.worker && !result.job && !result.error && !result.jobs) result = null;
    }
    return { sent: sent, result: result };
  }

  var api = {
    cleanTerminalControlText: cleanTerminalControlText,
    feedEntryFromChatMessage: feedEntryFromChatMessage,
    feedEntryFromWorkerLogEntry: feedEntryFromWorkerLogEntry,
    workerLocalTodosFromFeed: workerLocalTodosFromFeed,
    toolEntryFromDisplayLine: toolEntryFromDisplayLine,
    handoffFields: handoffFields,
    handoffStatusColor: handoffStatusColor,
    isThinkingPlaceholderLine: isThinkingPlaceholderLine,
    isThinkingPlaceholderText: isThinkingPlaceholderText,
    visibleThoughtLines: visibleThoughtLines,
    compactThoughtText: compactThoughtText,
    coalesceFeedEntries: coalesceFeedEntries,
  };

  if (typeof window !== 'undefined') {
    window.AtlasOrchestratorChatLogic = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
