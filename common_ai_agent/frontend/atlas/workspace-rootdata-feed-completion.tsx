// workspace-rootdata-feed-completion.tsx — extracted cohesive slice of
// workspace-root-data-hook.tsx (strangler-fig migration of workspace.jsx).
//
// Owns the pure transform helpers behind the workspace data hook's
// conversation-feed hydration and the chat-input completion menus. None of
// these close over per-render React state; each is a pure function of its
// arguments plus imported helpers (and read-only window.* lookups), so they
// live outside the useWorkspaceData closure:
//   - conversationFeedFromMessages: map a conversation.json message list into
//     the chat feed entry array (user / agent / action / obs).
//   - parseAtQuery: parse the trailing `@…` token of the chat input into the
//     @-file completion descriptor (or null).
//   - filterSlashCommands: score + sort the slash-command list for the `/`
//     completion menu.
//
// This is an INERT mirror — legacy workspace.jsx still serves the live app.
// Window-sourced values are typed `any` on purpose; do not tighten them.

import { _normalizeToolName, atlasIsIterationMarkerText } from './workspace-tool-theme';
import { workspaceToolArgsText } from './workspace-report-status';
import { stripScopeDirective } from './workspace-session-routing';

const w = window as any;

const firstRuntimeText = (...values: any[]): string => {
  for (const value of values) {
    const text = String(value ?? '').trim();
    if (text && text !== '—') return text;
  }
  return '';
};

export function runtimeMetaFromConversationMessage(message: any): any {
  const runtime = (message && message.runtime) || {};
  const tokens = (message && message._tokens) || {};
  const context = (w && w.CONTEXT) || {};
  const model = firstRuntimeText(
    message?.model,
    message?.active_model,
    message?.activeModel,
    message?.runtime_model,
    runtime.model,
    runtime.active_model,
    tokens.model,
    context.model,
    context.activeModel,
    context.baseModel,
  );
  const reasoningEffort = firstRuntimeText(
    message?.reasoning_effort,
    message?.reasoningEffort,
    message?.effort,
    runtime.reasoning_effort,
    runtime.reasoningEffort,
    runtime.effort,
    tokens.reasoning_effort,
    tokens.reasoningEffort,
    context.reasoning_effort,
    context.reasoningEffort,
    context.effort,
  );
  return {
    ...(model ? { model } : {}),
    ...(reasoningEffort ? { reasoningEffort } : {}),
  };
}

/**
 * Map a conversation.json message list into chat feed entries. Pure: depends
 * only on `msgs`, the resolved `session` label (for the turn_end marker), the
 * imported normalizers, and the read-only w.AtlasOrchestratorChatLogic helper.
 */
export function conversationFeedFromMessages(msgs: any[], session: string): any[] {
  const newFeed: any[] = [];
  for (const m of msgs) {
    const role = m.role;
    const rawContent = m.content !== undefined ? m.content : m.text;
    const content = typeof rawContent === 'string' ? rawContent
      : Array.isArray(rawContent) ? rawContent.map((c: any) => c.text || '').join('')
      : '';
    if (role === 'user' && content) {
      newFeed.push({ kind: 'user', text: stripScopeDirective(content) });
    } else if (role === 'assistant') {
      if (content && content.trim()) {
        newFeed.push({ kind: 'agent', text: content, ...runtimeMetaFromConversationMessage(m) });
      }
      if (Array.isArray(m.tool_calls)) {
        for (const tc of m.tool_calls) {
          const fn = _normalizeToolName((tc.function && tc.function.name) || tc.name) || 'tool';
          const args = (tc.function && tc.function.arguments) || tc.arguments || '';
          const argsText = workspaceToolArgsText(args);
          newFeed.push({ kind: 'action', text: `▶ ${fn} ${argsText}`, tool: fn, args: argsText, argsRaw: args });
        }
      }
    } else if (role === 'tool' && content) {
      if (atlasIsIterationMarkerText(content)) {
        newFeed.push({ kind: 'iter_marker', text: content });
        continue;
      }
      const parsedCall = /^[▶⏺]/.test(content)
        ? (w.AtlasOrchestratorChatLogic?.toolEntryFromDisplayLine?.(content) || null)
        : null;
      if (parsedCall) {
        newFeed.push({
          kind: 'action',
          text: parsedCall.text || content,
          tool: parsedCall.tool,
          args: parsedCall.args,
        });
      } else {
        newFeed.push({
          kind: 'obs',
          text: content.slice(0, 8000),
          tool: m.name || '',
          truncated: content.length > 8000,
        });
      }
    }
  }
  if (newFeed.length) {
    newFeed.push({
      kind: 'turn_end',
      text: `↓ live (${session ? `.session/${session}` : 'session history'} above) ↓`,
    });
  }
  return newFeed;
}

/**
 * Parse the trailing `@…` token of the chat input into the @-file completion
 * descriptor, or null when the input does not end with an @-token. Pure aside
 * from the read-only w.CONTEXT.activeIp lookup.
 */
export function parseAtQuery(input: string): any {
  const m = input.match(/(^|\s)@([^\s]*)$/);
  if (!m) return null;
  const raw = m[2];
  const slash = raw.lastIndexOf('/');
  const parentRel = slash >= 0 ? raw.slice(0, slash) : '';
  const filter = slash >= 0 ? raw.slice(slash + 1) : raw;
  const activeIpToken = ((w.CONTEXT && w.CONTEXT.activeIp) || '').trim();
  const ipPrefix = activeIpToken && activeIpToken !== 'default' ? activeIpToken : '';
  const absoluteEscape = raw.startsWith('/');
  const alreadyIpScoped = ipPrefix && (parentRel === ipPrefix || parentRel.startsWith(ipPrefix + '/'));
  const ipScoped = !!(ipPrefix && !absoluteEscape && !alreadyIpScoped);
  const trimmedParent = absoluteEscape ? parentRel.replace(/^\/+/, '') : parentRel;
  const parentAbs = ipScoped
    ? (trimmedParent ? `${ipPrefix}/${trimmedParent}` : ipPrefix)
    : trimmedParent;
  return {
    token: '@' + raw,
    pos: (m.index as number) + m[1].length,
    raw,
    parentRel: trimmedParent,
    parentAbs,
    absoluteEscape,
    ipScoped,
    ipPrefix,
    filter: filter.toLowerCase(),
  };
}

/**
 * Score + sort the slash-command list for the `/` completion menu. Pure aside
 * from the read-only w.SLASH_COMMANDS fallback when `slashCommands` is empty.
 */
export function filterSlashCommands(input: string, slashCommands: any[]): any[] {
  if (!/^\/[^\s]*$/.test(input)) return [];
  const q = input.slice(1).toLowerCase();
  const commands = slashCommands.length
    ? slashCommands
    : (Array.isArray(w.SLASH_COMMANDS) ? w.SLASH_COMMANDS : []);
  const scored: any[] = [];
  for (const c of commands) {
    const cmd = String(c.cmd || '').replace(/^\//, '').toLowerCase();
    const aliases = [
      c.alias,
      ...(Array.isArray(c.aliases) ? c.aliases : []),
    ]
      .flatMap((v: any) => String(v || '').split(/[,\s]+/))
      .map((v: string) => v.trim().toLowerCase())
      .filter(Boolean);
    const text = `${c.hint || ''} ${c.desc || ''} ${c.usage || ''}`.toLowerCase();
    let score = -1;
    if (!q) score = 0;
    else if (cmd === q) score = 100;
    else if (cmd.startsWith(q)) score = 80;
    else if (aliases.some((a: string) => a === q)) score = 70;
    else if (aliases.some((a: string) => a.startsWith(q))) score = 60;
    else if (q.length >= 2 && text.includes(q)) score = 20;
    if (score >= 0) scored.push({ c, score, cmd });
  }
  scored.sort((a, b) => (b.score - a.score) || a.cmd.localeCompare(b.cmd));
  return scored.slice(0, 40).map((s) => s.c);
}

/**
 * Build the predicate that decides whether a feed array already holds real
 * (non-placeholder) live entries. Pure: the placeholder set is derived from the
 * NORMAL_FEED / PLAN_FEED seed arrays passed in.
 */
export function makeHasLiveFeedEntries(
  normalFeed: any[],
  planFeed: any[],
): (items: any) => boolean {
  const placeholderTexts = new Set([
    normalFeed[0]?.text || '',
    planFeed[0]?.text || '',
  ]);
  return (items: any) => Array.isArray(items) && items.some((e: any) => {
    if (!e || typeof e !== 'object') return false;
    if (e.kind === 'turn_end') return false;
    if (e.kind === 'agent') {
      const text = String(e.text || '');
      return !!text.trim() && !placeholderTexts.has(text);
    }
    if (e.kind === 'thought') return !!e.live;
    return ['user', 'qcard', 'action', 'obs', 'ssot_approval'].includes(e.kind);
  });
}

/**
 * Find the latest unsubmitted qcard for the current session. Pure: scans the
 * feed first, then dynamic flow ids in w.QA_FLOWS, gating each on the supplied
 * flowMatchesCurrentSession predicate. Returns the matching feed entry, a
 * synthetic dynamic qcard descriptor, or null.
 */
export function derivePendingQcard(
  feed: any[],
  qaState: Record<string, any>,
  flowMatchesCurrentSession: (flowId: any) => boolean,
): any {
  for (let i = feed.length - 1; i >= 0; i--) {
    const e = feed[i];
    if (e.kind === 'qcard' && !qaState[e.flowId]?.submitted && flowMatchesCurrentSession(e.flowId)) return e;
  }
  const flowIds = Object.keys(qaState || {});
  for (let i = flowIds.length - 1; i >= 0; i--) {
    const flowId = flowIds[i];
    if (!qaState[flowId]?.submitted && w.QA_FLOWS && w.QA_FLOWS[flowId] && flowMatchesCurrentSession(flowId)) {
      return { kind: 'qcard', flowId, dynamic: true };
    }
  }
  return null;
}

/**
 * Resolve the SSOT-QA board payload, falling back to an empty board scaffold
 * for the resolved IP when no live ssotQa snapshot exists yet. Pure: returns
 * `ssotQa` as-is when it already carries an ip or no ip can be resolved.
 */
export function buildSsotQaBoardData(ssotQa: any, ip: string, sessionLabel: string): any {
  if (ssotQa?.ip) return ssotQa;
  if (!ip) return ssotQa;
  return {
    ip,
    workflow: 'ssot-gen',
    session: sessionLabel,
    toc: [],
    sections: [],
    summary: { total: 0, approved: 0, pending: 0 },
    requirements: { total: 0, filled: 0, missing: 0, items: [], missing_keys: [] },
  };
}
