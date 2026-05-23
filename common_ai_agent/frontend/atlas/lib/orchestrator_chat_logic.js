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

  var api = {
    feedEntryFromChatMessage: feedEntryFromChatMessage,
    toolEntryFromDisplayLine: toolEntryFromDisplayLine,
  };

  if (typeof window !== 'undefined') {
    window.AtlasOrchestratorChatLogic = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
