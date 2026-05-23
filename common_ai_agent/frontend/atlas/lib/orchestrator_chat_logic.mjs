// orchestrator_chat_logic.mjs — ES module twin of orchestrator_chat_logic.js for vitest.

export function feedEntryFromChatMessage(message) {
  const payload = (message && message.payload) || {};
  const role = String(payload.role || '').toLowerCase();
  const content = String(payload.content || '').trim();
  if (!content) return null;
  const created = Number((message && message.created_at) || 0);
  const createdAt = created > 0 ? created * 1000 : 0;

  if (role === 'assistant') {
    return { kind: 'agent', text: content, createdAt };
  }
  if (role === 'tool') {
    return {
      kind: 'action',
      text: content.startsWith('▶') ? content : `▶ ${content}`,
      createdAt,
    };
  }
  return null;
}
