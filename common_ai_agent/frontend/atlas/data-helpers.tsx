// data-helpers.tsx — pure helper cluster extracted from data.jsx (strangler-fig).
//
// data.jsx is ONE IIFE of ORDERED side-effects (installs window.* defaults,
// defines async loaders, wires the WS, and finally publishes window.atlasData).
// To keep every file <1000 lines WITHOUT disturbing that side-effect order,
// only the SIDE-EFFECT-FREE helper functions/constants are moved here. They
// reference no closure-mutable state (no caches, no URL_ACTIVE_SESSION const,
// no async refreshers), so the main file can `import` them at module top and
// the IIFE's execution order is byte-for-byte unchanged.
//
// NOTE: this module performs NO window.* writes. Every `window.X = X`
// side-effect (including `window.normalizeAtlasSessionName = normalizeSessionName`)
// still runs inside data.tsx's IIFE, in the original order. data-helpers.tsx is
// pure value-level code only.
//
// Behavior preserved exactly: logic, comments, and signatures match data.jsx.
import { atlasOagMode } from './runtime-flags';

// ── Flow-stage constants & exec-mode selection ───────────────────────
export const DEFAULT_WORKFLOW = 'default';
// General-purpose chat workflow (workflow/default/). The single-worker
// counterpart to the orchestrator entry gives single-worker mode a free
// conversation window instead of only stage workflows.
export const DEFAULT_FLOW_STAGE = {
  id: DEFAULT_WORKFLOW,
  label: DEFAULT_WORKFLOW,
  cmd: '/workflow default',
  color: 'var(--fg)',
  glyph: 'GP',
};
export const DEFAULT_FLOW_STAGES = [
  DEFAULT_FLOW_STAGE,
  { id: 'ssot-gen',     label: 'ssot-gen',     cmd: '/wf ssot-gen',     color: 'var(--mag)',    glyph: 'SS' },
  { id: 'fl-model-gen', label: 'fl-model-gen', cmd: '/wf fl-model-gen', color: 'var(--cyan)',   glyph: 'FL' },
  { id: 'rtl-gen',      label: 'rtl-gen',      cmd: '/wf rtl-gen',      color: 'var(--accent)', glyph: 'RT' },
  { id: 'tb-gen',       label: 'tb-gen',       cmd: '/wf tb-gen',       color: 'var(--ok)',     glyph: 'TB' },
  { id: 'sim_debug',    label: 'sim_debug',    cmd: '/wf sim_debug',    color: 'var(--warn)',   glyph: 'DB' },
  { id: 'lint',         label: 'lint',         cmd: '/wf lint',         color: 'var(--err)',    glyph: 'LT' },
  { id: 'coverage',     label: 'coverage',     cmd: '/wf coverage',     color: 'var(--cyan)',   glyph: 'CV' },
  { id: 'contract-reflection', label: 'contract-reflection', cmd: '/wf contract-reflection', color: 'var(--mag)', glyph: 'CC' },
  { id: 'syn',          label: 'syn',          cmd: '/wf syn',          color: 'var(--accent)', glyph: 'SY' },
  { id: 'sta',          label: 'sta',          cmd: '/wf sta',          color: 'var(--mag)',    glyph: 'ST' },
  { id: 'pnr',          label: 'pnr',          cmd: '/wf pnr',          color: 'var(--ok)',     glyph: 'PR' },
  { id: 'sta-post',     label: 'sta-post',     cmd: '/wf sta-post',     color: 'var(--warn)',   glyph: 'PS' },
];

export const ORCHESTRATOR_FLOW_STAGE = {
  id: 'orchestrator',
  label: 'orchestrator',
  cmd: '/workflow orchestrator',
  color: 'var(--cyan)',
  glyph: 'OR',
};

export function atlasExecMode(): string {
  const w = window as any;
  return String(
    w.ATLAS_EXEC_MODE
    || w.ATLAS_DEFAULT_EXEC_MODE
    || (w.ATLAS_BOOT_CONFIG && w.ATLAS_BOOT_CONFIG.exec_mode)
    || ''
  ).trim().toLowerCase();
}

export function flowStagesForExecMode(stages?: any[]): any[] {
  if (atlasOagMode()) return [DEFAULT_FLOW_STAGE];
  const base = Array.isArray(stages) ? stages : DEFAULT_FLOW_STAGES;
  const deduped = base.filter((s) => s
    && s.id !== ORCHESTRATOR_FLOW_STAGE.id
    && s.id !== DEFAULT_FLOW_STAGE.id);
  if (atlasExecMode() === 'orchestrator') {
    return [ORCHESTRATOR_FLOW_STAGE].concat(deduped);
  }
  // single-worker: lead with the general-purpose 'default' chat workflow.
  return [DEFAULT_FLOW_STAGE].concat(deduped);
}

// ── Scope path & user-session id helpers ─────────────────────────────
// Scope path: agent is asked (via prompt prefix) to keep all reads,
// writes, and tool calls confined to this directory. Empty string =
// whole project root. Persists across reloads via localStorage.
export function normalizeScopePath(raw: unknown): string {
  const src = String(raw ?? '').trim().replace(/\\/g, '/');
  if (!src || src === '/') return '';
  const out: string[] = [];
  src.split('/').forEach((part) => {
    const seg = String(part || '').trim();
    if (!seg || seg === '.') return;
    if (seg === '..') {
      out.pop();
      return;
    }
    out.push(seg);
  });
  return out.join('/');
}

export function createUserSessionId(): string {
  const stamp = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 8);
  return `u-${stamp}-${rand}`;
}

// ── Size formatter & file-tree node mapping ──────────────────────────
// FILE_TREE entry shape (matches what workspace.jsx renders):
//   { type: 'dir'|'file', name, size, depth, expanded, dim, active }
export function fmtSize(bytes: number): string {
  if (!bytes) return '';
  if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  if (bytes >= 1024)        return (bytes / 1024).toFixed(1) + ' KB';
  return bytes + ' B';
}

export function asTreeNode(entry: any, depth: number): any {
  return {
    type: entry.type === 'dir' ? 'dir' : 'file',
    name: entry.name,
    size: fmtSize(entry.size),
    // Preserve mtime so the workspace panel can sort by 'recent'
    // (most recently modified first). Backend ships it per entry
    // — see atlas_ui.py:367.
    mtime: entry.mtime || 0,
    depth: depth || 0,
    expanded: false,
    dim: false,
    active: false,
  };
}

// ── Todo normalization ───────────────────────────────────────────────
export function normalizeTodoListField(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map(v => String(v ?? '').trim()).filter(Boolean);
  }
  const s = String(value ?? '').trim();
  if (!s) return [];
  return s.split(/\r?\n+/).map(line => line.trim()).filter(Boolean);
}

export function normalizeTodos(rawTodos: any): any[] {
  return (Array.isArray(rawTodos) ? rawTodos : []).map((t, i) => ({
    id:      t.id ? String(t.id) : `t${i + 1}`,
    state:   t.status || 'pending',
    section: t.priority ? String(t.priority).toUpperCase() : '',
    title:   t.content || '',
    detail:  t.detail || '',
    criteria: normalizeTodoListField(t.criteria || t.acceptance_criteria),
    sourceRefs: normalizeTodoListField(t.source_refs || t.sourceRefs || t.references),
    ownerModule: String(t.owner_module || t.ownerModule || '').trim(),
    ownerFile: String(t.owner_file || t.ownerFile || '').trim(),
    required: t.required,
    approvedReason: t.approved_reason || '',
    rejectionReason: t.rejection_reason || '',
    notes:   Array.isArray(t.notes) ? t.notes : [],
    deps:    Array.isArray(t.deps) ? t.deps : [],
    command: t.command || '',
    onReject: t.on_reject ?? t.onReject ?? 0,
    onSuccess: t.on_success ?? t.onSuccess ?? 0,
    onCondition: Array.isArray(t.on_condition) ? t.on_condition : (Array.isArray(t.onCondition) ? t.onCondition : []),
    commandLogs: Array.isArray(t.command_logs) ? t.command_logs : (Array.isArray(t.commandLogs) ? t.commandLogs : []),
  }));
}

// ── Session-name normalization & namespace introspection ─────────────
export const KNOWN_WORKFLOWS = new Set([
  DEFAULT_WORKFLOW,
  'architect',
  'coverage',
  'contract-reflection',
  'fl-model-gen',
  'goal-audit',
  'lint',
  'mas-gen',
  'orchestrator',
  'rtl-gen',
  'signoff',
  'sim',
  'sim_debug',
  'ssot-gen',
  'sta',
  'sta-post',
  'syn',
  'tb-gen',
  'pnr',
]);

export const KNOWN_SESSION_FILES = new Set([
  'conversation.json',
  'full_conversation.json',
  'todo.json',
  'todo_error.json',
  'cost.json',
  'state.json',
  'qa.json',
  'result.json',
]);

export function normalizeSessionName(value: unknown): string {
  const raw = String(value || '').trim().replace(/^["']|["']$/g, '');
  if (!raw) return '';
  const pathish = raw.includes('\\') || raw.includes(':') || raw.startsWith('/') ||
    raw.startsWith('~') || raw.startsWith('.session');
  let parts = raw.replace(/\\/g, '/').replace(/^\/+|\/+$/g, '')
    .split('/')
    .filter(p => p && p !== '.');
  if (!parts.length) return '';
  const lower = parts.map(p => p.toLowerCase());
  const idx = lower.lastIndexOf('.session');
  const hadSessionMarker = idx >= 0;
  if (idx >= 0) parts = parts.slice(idx + 1);
  else if (/^[A-Za-z]:$/.test(parts[0])) {
    parts = parts.slice(1);
    if (parts.length > 2) parts = parts.slice(-2);
  }
  if (parts.length && KNOWN_SESSION_FILES.has(String(parts[parts.length - 1]).toLowerCase())) {
    parts = parts.slice(0, -1);
  }
  if (!parts.length) return '';
  if (
    parts.length > 2 &&
    KNOWN_WORKFLOWS.has(String(parts[parts.length - 1]).toLowerCase()) &&
    pathish &&
    !hadSessionMarker
  ) {
    parts = parts.slice(-2);
  }
  for (const part of parts) {
    if (part === '..' || part.includes(':') || !/^[A-Za-z0-9_.-]+$/.test(part)) return '';
  }
  return parts.join('/');
}

export function sessionPartsEndWithWorkflow(parts: string[]): boolean {
  const last = String(parts[parts.length - 1] || '').toLowerCase();
  return KNOWN_WORKFLOWS.has(last);
}

export function activeWorkflowFromSession(session?: unknown): string {
  const w = window as any;
  const parts = normalizeSessionName(session || w.ACTIVE_SESSION || '').split('/').filter(Boolean);
  const last = parts[parts.length - 1] || '';
  return KNOWN_WORKFLOWS.has(last) ? last : '';
}

export function activeIpFromSession(session?: unknown): string {
  const w = window as any;
  const parts = normalizeSessionName(session || w.ACTIVE_SESSION || '').split('/').filter(Boolean);
  if (parts.length >= 3) {
    const ip = parts[parts.length - 2] || '';
    return ip === DEFAULT_WORKFLOW ? '' : ip;
  }
  return '';
}

// ── WS bootstrap helpers: debounce + write-tool change detection ─────
// Coalesce a burst of WS events into a single API hit per resource.
// Without this, a single agent turn that fires 5 tool_result frames
// in 200 ms triggers 5 file-tree + 5 ssot + 5 todo fetches and the
// UI feels sluggish.
export function debounce(fn: () => void, wait: number): () => void {
  let t: ReturnType<typeof setTimeout>;
  return function () {
    clearTimeout(t);
    t = setTimeout(fn, wait);
  };
}

export const WRITE_TOOL_RE = /^(?:write_file|write_to_file|replace_in_file|replace_lines|replace_file_content|multi_replace_file_content|edit_file|patch_file|apply_patch|patch|update_file)\b/i;
export const CHANGED_PATH_EXT_RE = /^(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl|css|js|jsx|ts|tsx|html)$/i;

export function changedPathsFromToolResult(tool: unknown, text: unknown): string[] {
  const toolText = String(tool || '');
  const body = String(text || '');
  if (!WRITE_TOOL_RE.test(toolText)) return [];
  const seen = new Set<string>();
  const out: string[] = [];
  const add = (value: unknown) => {
    let path = String(value || '').trim().replace(/^['"`]+|['"`]+$/g, '');
    path = path.replace(/[\s,;:]+$/g, '');
    if (!path || path === '.' || path === '..' || path.includes('\n')) return;
    const ext = path.split('.').pop() || '';
    if (!CHANGED_PATH_EXT_RE.test(ext)) return;
    if (!seen.has(path)) {
      seen.add(path);
      out.push(path);
    }
  };
  const scan = (rx: RegExp, source: string = body) => {
    let m;
    while ((m = rx.exec(source)) !== null) add(m[1]);
  };
  scan(/(?:wrote to|wrote|updated|created|deleted|(?:successfully\s+)?replaced\s+(?:in|to)|replaced\s+\d+\s+occurrence(?:\(s\)|s)?\s+in)\s+['"`]([^'"`]+)['"`]/gi);
  scan(/(?:wrote file|updated file|created file|deleted file|target_file|file_path|path)\s*[:=]\s*['"`]?([^\s,'"`)\]]+)/gi, `${toolText}\n${body}`);
  scan(/^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(.+?)\s*$/gmi);
  scan(/^(?:[MADRCU]|\?\?)\s+(.+?)\s*$/gm);
  scan(/^Update\(([^)]+)\)/gm);
  scan(/(?:in|to)\s+([\w./_-]+\.(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl|css|js|jsx|ts|tsx|html))/gi);
  return out;
}

export function dispatchAtlasFileChanged(path: string, tool?: string): void {
  if (!path) return;
  try {
    window.dispatchEvent(new CustomEvent('atlas-file-changed', {
      detail: { path, tool: tool || '' },
    }));
  } catch (_) {}
}
