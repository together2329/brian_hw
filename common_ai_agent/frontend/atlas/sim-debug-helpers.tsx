// sim-debug-helpers.tsx — TypeScript migration of the pure-helper cluster
// extracted from sim-debug.jsx (strangler-fig split). Behavior-preserving:
// these are the same standalone functions that lived at the top of
// sim-debug.jsx (lines 8–228), including the exact `window.simDebug*`
// bridges in the SAME order.
//
// Load order: this file is included by index.html BEFORE sim-debug.tsx /
// sim-debug-panels.tsx. It owns no React component — only data helpers and
// the window bridges that the panels + root component read back through
// `window.simDebug*` (kept as window refs to avoid module-ordering issues,
// identical to the legacy cross-script-global behavior).
//
// Transitional: still bridges to `window.*` at the bottom so the
// not-yet-migrated sim-debug.jsx keeps resolving these globals.

// ── Cross-file globals owned by OTHER (unmigrated) files. Read through a
// locally typed view of `window` so a typo is caught, without editing the
// shared ambient d.ts. Behavior identical to the legacy implicit globals.
interface AtlasData {
  normalizeSessionName?: (s: string) => string;
}
interface SimDebugHelpersWindow {
  atlasData?: AtlasData;
  normalizeAtlasSessionName?: (s: string) => string;
  ACTIVE_SESSION?: string;
  ACTIVE_IP?: string;
  CONTEXT?: {
    activeSession?: string;
    active_session?: string;
    active_ip?: string;
    activeIp?: string;
  };
  // This file's OWN public globals (set via the transitional bridge below).
  simDebugActiveIpFromAtlasRuntime?: typeof activeIpFromAtlasRuntime;
  simDebugVcdPathBelongsToIp?: typeof vcdPathBelongsToIp;
  simDebugVcdValueAtTrace?: typeof vcdValueAtTrace;
  simDebugBuildWaveTraceList?: typeof buildWaveTraceList;
  simDebugBuildVcdLineAnnotations?: typeof buildVcdLineAnnotations;
  simDebugAnnotationAxesForMode?: typeof annotationAxesForMode;
}
const g = (typeof window !== 'undefined' ? window : ({} as Window)) as unknown as SimDebugHelpersWindow;

// Loosely-typed shapes for VCD data passed between helpers. The real parser
// (window.parseVCD) is owned by another file; we only need structural access.
export interface VcdSignal {
  id?: string;
  name?: string;
  signalName?: string;
  scope?: string;
  range?: string;
  isBus?: boolean;
  trace?: Array<[number, unknown] | unknown[]>;
  radix?: string;
}
export interface VcdData {
  signals?: VcdSignal[];
  samples?: Record<string, Array<[number, unknown] | unknown[]>>;
  timeRange?: [number, number];
  timescale?: string;
}
export interface PinnedSignal {
  name?: string;
  scope?: string;
}
export interface VcdAnnotationRow {
  name: string;
  a: string;
  b: string;
}
export interface VcdAnnotationAxis {
  id: string;
  label: string;
  key: string;
  color: string;
}

export const normalizeProjectSourcePath = (rawPath: unknown): string => {
  const raw = String(rawPath || '').replace(/\\/g, '/').replace(/:\d+$/, '');
  const marker = '/common_ai_agent/';
  const idx = raw.indexOf(marker);
  if (idx >= 0) return raw.slice(idx + marker.length);
  return raw.replace(/^\/+/, '');
};

export const normalizeAtlasEventSession = (session: unknown): string => {
  const norm = (g.atlasData && g.atlasData.normalizeSessionName) || g.normalizeAtlasSessionName;
  try { return norm ? norm(String(session || '')) : ''; }
  catch (_) { return ''; }
};

export const atlasEventMatchesActiveSession = (
  m: { session_id?: string; session?: string; namespace?: string } | null | undefined,
  opts: { requireSession?: boolean } = {},
): boolean => {
  const eventSession = normalizeAtlasEventSession((m && (m.session_id || m.session || m.namespace)) || '');
  const activeSession = normalizeAtlasEventSession(
    g.ACTIVE_SESSION
    || (g.CONTEXT && (g.CONTEXT.activeSession || g.CONTEXT.active_session))
    || ''
  );
  if (!activeSession) return !opts.requireSession;
  if (!eventSession) return !opts.requireSession;
  return eventSession === activeSession;
};

export const isDumpScopeName = (name: unknown): boolean => {
  const n = String(name || '');
  return n === 'iverilog_dump' || n === 'atlas_iverilog_vcd_dump' || /_vcd_dump$/.test(n);
};

export const inferRtlTopFromVcd = (parsed: VcdData | null | undefined, fallback = ''): string => {
  const signals = Array.isArray(parsed?.signals) ? parsed!.signals! : [];
  for (const sig of signals) {
    const first = String(sig?.scope || '').split('.').find(Boolean) || '';
    if (first && !isDumpScopeName(first)) return first;
  }
  return fallback || '';
};

export const activeIpFromAtlasRuntime = (): string => {
  if (typeof window === 'undefined') return '';
  const direct = String(g.ACTIVE_IP || '').trim();
  if (direct && direct !== 'default') return direct;
  const ctxIp = String((g.CONTEXT && (g.CONTEXT.active_ip || g.CONTEXT.activeIp)) || '').trim();
  if (ctxIp && ctxIp !== 'default') return ctxIp;
  const parts = String(g.ACTIVE_SESSION || '').split('/').filter(Boolean);
  const sessionIp = parts.length >= 2 ? String(parts[1] || '').trim() : '';
  return sessionIp && sessionIp !== 'default' ? sessionIp : '';
};

export const vcdPathBelongsToIp = (path: unknown, ip: unknown): boolean => {
  const p = String(path || '').replace(/\\/g, '/').replace(/^\/+/, '');
  const owner = String(ip || '').replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
  return !!owner && (p === owner || p.startsWith(owner + '/'));
};

export const stripSignalRange = (name: unknown): string => String(name || '').replace(/\s*\[[^\]]+\]\s*$/g, '').trim();

export const vcdValueAtTrace = (trace: Array<unknown[]> | unknown, time: unknown): unknown => {
  if (!Array.isArray(trace) || trace.length === 0) return '?';
  const target = Number(time);
  if (!Number.isFinite(target)) return '?';
  let value: unknown = '?';
  for (const sample of trace) {
    if (!Array.isArray(sample)) continue;
    const t = Number(sample[0]);
    if (!Number.isFinite(t)) continue;
    if (t > target) break;
    value = sample[1];
  }
  return value == null ? '?' : value;
};

export const formatVcdValue = (value: unknown, isBus: unknown): string => {
  if (value == null) return '?';
  const s = String(value);
  if (!isBus) return s;
  if (/^[01]+$/.test(s)) {
    try {
      return '0x' + BigInt('0b' + s).toString(16).toUpperCase();
    } catch (_) {
      return s;
    }
  }
  return s;
};

export const VERILOG_KEYWORDS = new Set([
  'always', 'always_comb', 'always_ff', 'assign', 'begin', 'case', 'default', 'else',
  'end', 'endcase', 'endmodule', 'for', 'generate', 'if', 'input', 'logic', 'module',
  'negedge', 'or', 'output', 'parameter', 'posedge', 'reg', 'wire',
]);

export const sourceLineIdentifiers = (line: unknown): string[] => {
  const ids: string[] = [];
  const seen = new Set<string>();
  const text = String(line || '');
  const re = /\b[A-Za-z_][A-Za-z0-9_$]*\b/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    const id = m[0];
    const key = id.toLowerCase();
    if (VERILOG_KEYWORDS.has(key) || seen.has(key)) continue;
    seen.add(key);
    ids.push(id);
  }
  return ids;
};

export const signalAliasKeys = (sig: VcdSignal | null | undefined): string[] => {
  const aliases = [
    sig?.signalName,
    sig?.name,
    stripSignalRange(sig?.name),
  ];
  return aliases
    .map(a => String(a || '').trim())
    .filter(Boolean)
    .flatMap(a => [a, a.split('.').pop() as string])
    .map(a => stripSignalRange(a).toLowerCase())
    .filter(Boolean);
};

export const waveSignalKey = (sig: VcdSignal | null | undefined): string => {
  const scope = String(sig?.scope || '').trim();
  const name = stripSignalRange(sig?.signalName || sig?.name || '');
  const range = String(sig?.range || '').trim();
  return `${scope}/${name}${range}`.toLowerCase();
};

export const waveSignalMatches = (sig: VcdSignal | null | undefined, name: unknown, scope = ''): boolean => {
  const wanted = stripSignalRange(name).toLowerCase();
  if (!wanted) return false;
  const sigScope = String(sig?.scope || '').trim();
  const wantedScope = String(scope || '').trim();
  if (wantedScope && sigScope !== wantedScope) return false;
  return signalAliasKeys(sig).includes(wanted);
};

export const waveRowFromVcdSignal = (vcdData: VcdData, sig: VcdSignal): VcdSignal => ({
  name: (sig.name as string) + (sig.range || ''),
  signalName: sig.name,
  scope: sig.scope,
  range: sig.range || '',
  trace: (vcdData.samples && sig.id != null ? vcdData.samples[sig.id] : undefined) || [],
  isBus: sig.isBus,
  radix: sig.isBus ? 'HEX' : undefined,
});

export const buildWaveTraceList = (
  vcdData: VcdData | null | undefined,
  pinnedSignals: PinnedSignal[] = [],
  defaultLimit = 24,
): VcdSignal[] => {
  if (!vcdData || !Array.isArray(vcdData.signals) || !vcdData.signals.length) return [];
  const allRows = vcdData.signals.map(s => waveRowFromVcdSignal(vcdData, s));
  const rows = allRows.slice(0, defaultLimit);
  const present = new Set(rows.map(waveSignalKey));
  for (const pin of pinnedSignals || []) {
    const found = allRows.find(row => waveSignalMatches(row, pin.name, pin.scope));
    if (!found) continue;
    const key = waveSignalKey(found);
    if (present.has(key)) continue;
    rows.push(found);
    present.add(key);
  }
  return rows;
};

export const buildVcdLineAnnotations = ({
  line, traceList, selectedSig, cursorA, cursorB, limit = 8,
}: {
  line: unknown;
  traceList: VcdSignal[] | null | undefined;
  selectedSig: unknown;
  cursorA: unknown;
  cursorB: unknown;
  limit?: number;
}): VcdAnnotationRow[] => {
  if (!Array.isArray(traceList) || traceList.length === 0) return [];
  const byAlias = new Map<string, VcdSignal>();
  for (const sig of traceList) {
    for (const alias of signalAliasKeys(sig)) {
      if (!byAlias.has(alias)) byAlias.set(alias, sig);
    }
  }

  const wanted: string[] = [];
  const pushWanted = (name: unknown) => {
    const key = stripSignalRange(name).toLowerCase();
    if (key && !wanted.includes(key)) wanted.push(key);
  };
  pushWanted(selectedSig);
  sourceLineIdentifiers(line).forEach(pushWanted);

  const rows: VcdAnnotationRow[] = [];
  const seen = new Set<string>();
  for (const key of wanted) {
    const sig = byAlias.get(key);
    if (!sig) continue;
    const display = sig.name || sig.signalName || key;
    const dedupe = stripSignalRange(display).toLowerCase();
    if (seen.has(dedupe)) continue;
    seen.add(dedupe);
    rows.push({
      name: display,
      a: formatVcdValue(vcdValueAtTrace(sig.trace, cursorA), sig.isBus),
      b: formatVcdValue(vcdValueAtTrace(sig.trace, cursorB), sig.isBus),
    });
    if (rows.length >= limit) break;
  }
  return rows;
};

// ── RTL module signals (from /api/module/signals via pyslang) ─────
export interface ModuleSignal {
  name: string;
  direction: 'in' | 'out' | 'inout' | 'internal' | string;
  kind?: string;
  type?: string;
  width?: number;
  file?: string;
  line?: number;
  file_line?: string;
}

// Filter a module's signals by direction tab. 'inout' shows under both
// 'in' and 'out' so a bidirectional port is never hidden from either
// directional view. 'all' returns everything.
export const filterModuleSignals = (
  signals: ModuleSignal[] | null | undefined,
  filter: string,
): ModuleSignal[] => {
  const list = Array.isArray(signals) ? signals : [];
  if (!filter || filter === 'all') return list;
  if (filter === 'in') return list.filter(s => s.direction === 'in' || s.direction === 'inout');
  if (filter === 'out') return list.filter(s => s.direction === 'out' || s.direction === 'inout');
  if (filter === 'internal') return list.filter(s => s.direction === 'internal');
  return list;
};

// Per-direction tallies for the filter-chip badges.
export const moduleSignalCounts = (
  signals: ModuleSignal[] | null | undefined,
): { all: number; in: number; out: number; internal: number } => {
  const list = Array.isArray(signals) ? signals : [];
  return {
    all: list.length,
    in: list.filter(s => s.direction === 'in' || s.direction === 'inout').length,
    out: list.filter(s => s.direction === 'out' || s.direction === 'inout').length,
    internal: list.filter(s => s.direction === 'internal').length,
  };
};

// Short width label for a signal row, e.g. '[15:0]' → '16b', scalar → ''.
export const moduleSignalWidthLabel = (sig: ModuleSignal | null | undefined): string => {
  const w = Number(sig?.width || 0);
  return w > 1 ? `${w}b` : '';
};

export const VCD_ANNOTATION_AXES: VcdAnnotationAxis[] = [
  { id: 'a', label: 'A', key: 'a', color: 'var(--accent)' },
  { id: 'b', label: 'B', key: 'b', color: 'var(--cyan)' },
];

export const annotationAxesForMode = (mode: unknown): VcdAnnotationAxis[] => {
  if (mode === 'a') return VCD_ANNOTATION_AXES.slice(0, 1);
  if (mode === 'b') return VCD_ANNOTATION_AXES.slice(1, 2);
  return VCD_ANNOTATION_AXES;
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx and
// for this file's own siblings (sim-debug-panels.tsx / sim-debug.tsx).
// SAME assignments, SAME order as legacy sim-debug.jsx lines 221–228.
if (typeof window !== 'undefined') {
  g.simDebugActiveIpFromAtlasRuntime = activeIpFromAtlasRuntime;
  g.simDebugVcdPathBelongsToIp = vcdPathBelongsToIp;
  g.simDebugVcdValueAtTrace = vcdValueAtTrace;
  g.simDebugBuildWaveTraceList = buildWaveTraceList;
  g.simDebugBuildVcdLineAnnotations = buildVcdLineAnnotations;
  g.simDebugAnnotationAxesForMode = annotationAxesForMode;
}
