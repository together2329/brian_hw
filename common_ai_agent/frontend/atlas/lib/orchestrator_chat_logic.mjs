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
  const content = String(payload.content || '').trim();
  if (!content) return null;
  const created = Number((message && message.created_at) || 0);
  const createdAt = created > 0 ? created * 1000 : 0;
  const payloadTool = String(payload.tool || payload.name || payload.display_name || '').trim();

  if (role === 'assistant') {
    return { kind: 'agent', text: content, createdAt };
  }
  if (role === 'thought' || role === 'reasoning') {
    return { kind: 'thought', text: content, createdAt };
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
    };
  }
  if (role === 'tool_result' || role === 'observation' || role === 'obs') {
    return {
      kind: 'obs',
      text: content,
      tool: payloadTool,
      createdAt,
    };
  }
  return null;
}
