// orchestrator_chat_logic.js — browser plain-script helper.
// For ES module imports (vitest), see orchestrator_chat_logic.mjs.

(function () {
  function feedEntryFromChatMessage(message) {
    var payload = (message && message.payload) || {};
    var role = String(payload.role || '').toLowerCase();
    var content = String(payload.content || '').trim();
    if (!content) return null;
    var created = Number((message && message.created_at) || 0);
    var createdAt = created > 0 ? created * 1000 : 0;

    if (role === 'assistant') {
      return { kind: 'agent', text: content, createdAt: createdAt };
    }
    if (role === 'tool') {
      return {
        kind: 'action',
        text: content.indexOf('▶') === 0 ? content : '▶ ' + content,
        createdAt: createdAt,
      };
    }
    return null;
  }

  var api = {
    feedEntryFromChatMessage: feedEntryFromChatMessage,
  };

  if (typeof window !== 'undefined') {
    window.AtlasOrchestratorChatLogic = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
