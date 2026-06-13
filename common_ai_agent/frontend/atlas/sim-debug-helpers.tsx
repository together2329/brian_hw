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
import { activeIpFromSession } from './data-helpers';

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
  simDebugParseVerilogParamValueMap?: typeof parseVerilogParamValueMap;
  simDebugReorderWaveKeys?: typeof reorderWaveKeys;
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
  notInVcd?: boolean;
  // Other fully-qualified names that share this signal's VCD id (same net
  // dumped under multiple hierarchical paths). Lets a pin using any of those
  // names resolve to this row. Populated by the VCD parser.
  aliases?: string[];
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

const TIME_UNIT_SECONDS: Record<string, number> = {
  fs: 1e-15,
  ps: 1e-12,
  ns: 1e-9,
  us: 1e-6,
  ms: 1e-3,
  s: 1,
};

export const TIME_DISPLAY_UNITS = ['auto', 'fs', 'ps', 'ns', 'us', 'ms', 's'];

export const timeUnitFromTimescale = (timescale: unknown): string => {
  const m = String(timescale || '').trim().toLowerCase().match(/(fs|ps|ns|us|ms|s)$/);
  return m ? m[1] : 'ns';
};

export const resolveTimeDisplayUnit = (timescale: unknown, unit: unknown): string => {
  const u = String(unit || 'auto').trim().toLowerCase();
  if (u && u !== 'auto' && TIME_UNIT_SECONDS[u]) return u;
  return timeUnitFromTimescale(timescale);
};

export const parseTimescaleSeconds = (timescale: unknown): number => {
  const raw = String(timescale || '').trim().toLowerCase().replace(/\s+/g, '');
  const m = raw.match(/^([0-9]*\.?[0-9]+)?(fs|ps|ns|us|ms|s)$/);
  if (!m) return 1e-9;
  const amount = m[1] ? Number(m[1]) : 1;
  const unitSeconds = TIME_UNIT_SECONDS[m[2]] || 1e-9;
  return (Number.isFinite(amount) && amount > 0 ? amount : 1) * unitSeconds;
};

export const rawTimeToDisplay = (rawTime: unknown, timescale: unknown, unit: unknown): number => {
  const n = Number(rawTime);
  if (!Number.isFinite(n)) return 0;
  const displayUnit = resolveTimeDisplayUnit(timescale, unit);
  return n * parseTimescaleSeconds(timescale) / (TIME_UNIT_SECONDS[displayUnit] || 1e-9);
};

export const displayTimeToRaw = (displayTime: unknown, timescale: unknown, unit: unknown): number => {
  const n = Number(displayTime);
  if (!Number.isFinite(n)) return 0;
  const displayUnit = resolveTimeDisplayUnit(timescale, unit);
  const tsSeconds = parseTimescaleSeconds(timescale);
  if (!tsSeconds) return n;
  return n * (TIME_UNIT_SECONDS[displayUnit] || 1e-9) / tsSeconds;
};

const compactTimeNumber = (n: number): string => {
  if (!Number.isFinite(n)) return '0';
  const abs = Math.abs(n);
  const digits = abs >= 1000 || Number.isInteger(n) ? 0 : (abs >= 100 ? 1 : abs >= 10 ? 2 : 3);
  const text = n.toFixed(digits);
  return text.includes('.') ? text.replace(/\.?0+$/, '') : text;
};

export const formatTimeDisplay = (rawTime: unknown, timescale: unknown, unit: unknown): string => {
  const displayUnit = resolveTimeDisplayUnit(timescale, unit);
  return `${compactTimeNumber(rawTimeToDisplay(rawTime, timescale, displayUnit))}${displayUnit}`;
};

export const formatTimeDeltaDisplay = (rawDelta: unknown, timescale: unknown, unit: unknown): string => {
  return formatTimeDisplay(Math.abs(Number(rawDelta) || 0), timescale, unit);
};

export const formatFrequencyFromDelta = (rawDelta: unknown, timescale: unknown): string => {
  const dt = Math.abs(Number(rawDelta) || 0) * parseTimescaleSeconds(timescale);
  if (!dt) return '∞ Hz';
  const hz = 1 / dt;
  const units: Array<[string, number]> = [['THz', 1e12], ['GHz', 1e9], ['MHz', 1e6], ['kHz', 1e3], ['Hz', 1]];
  const picked = units.find(([, scale]) => hz >= scale) || units[units.length - 1];
  return `${compactTimeNumber(hz / picked[1])} ${picked[0]}`;
};
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
  const sessionIp = activeIpFromSession(g.ACTIVE_SESSION || '');
  return sessionIp && sessionIp !== 'default' ? sessionIp : '';
};

export const vcdPathBelongsToIp = (path: unknown, ip: unknown): boolean => {
  const p = String(path || '').replace(/\\/g, '/').replace(/^\/+/, '');
  const owner = String(ip || '').replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
  return !!owner && (p === owner || p.startsWith(owner + '/'));
};

export const signalRangeOf = (name: unknown): string => {
  const m = String(name || '').trim().match(/(\[[^\]\n]+\])\s*$/);
  return m ? m[1].replace(/\s+/g, '') : '';
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

export const numericValueKey = (value: unknown): string => {
  const raw = String(value || '').trim().replace(/_/g, '');
  if (!raw || /[xXzZ?]/.test(raw)) return '';
  const sized = raw.match(/^(?:\d+)?'([bBoOdDhH])([0-9a-fA-F]+)$/);
  try {
    if (sized) {
      const base = sized[1].toLowerCase();
      const digits = sized[2];
      if (base === 'b') return BigInt('0b' + digits).toString(10);
      if (base === 'o') return BigInt('0o' + digits).toString(10);
      if (base === 'h') return BigInt('0x' + digits).toString(10);
      return BigInt(digits).toString(10);
    }
    if (/^0x[0-9a-fA-F]+$/.test(raw)) return BigInt(raw).toString(10);
    if (/^\d+$/.test(raw)) return BigInt(raw).toString(10);
  } catch (_) {}
  return '';
};

export const vcdTraceValueKey = (value: unknown, isBus: unknown): string => {
  const raw = String(value || '').trim().replace(/_/g, '');
  if (!raw || /[xXzZ?]/.test(raw)) return '';
  try {
    if (isBus && /^[01]+$/.test(raw)) return BigInt('0b' + raw).toString(10);
    return numericValueKey(raw);
  } catch (_) {
    return '';
  }
};

export const parseVerilogParamValueMap = (lines: unknown): Record<string, string> => {
  const text = Array.isArray(lines) ? lines.join('\n') : String(lines || '');
  const cleaned = text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  const out: Record<string, string> = {};
  const declRe = /\b(?:localparam|parameter)\b[\s\S]*?;/g;
  let decl: RegExpExecArray | null;
  while ((decl = declRe.exec(cleaned))) {
    const body = decl[0]
      .replace(/\b(?:localparam|parameter)\b/g, '')
      .replace(/\b(?:logic|reg|wire|integer|int|bit|signed|unsigned)\b/g, '')
      .replace(/\[[^\]\n]+\]/g, ' ');
    const assignRe = /\b([A-Za-z_][A-Za-z0-9_$]*)\b\s*=\s*([^,;]+)/g;
    let m: RegExpExecArray | null;
    while ((m = assignRe.exec(body))) {
      const name = m[1];
      if (VERILOG_KEYWORDS.has(name.toLowerCase())) continue;
      const key = numericValueKey(m[2]);
      if (key && !out[key]) out[key] = name;
    }
  }
  return out;
};

export const VERILOG_KEYWORDS = new Set([
  'always', 'always_comb', 'always_ff', 'assign', 'begin', 'case', 'default', 'else',
  'end', 'endcase', 'endmodule', 'for', 'generate', 'if', 'initial', 'input',
  'integer', 'int', 'localparam', 'logic', 'module', 'negedge', 'or', 'output',
  'parameter', 'posedge', 'reg', 'signed', 'unsigned', 'wire',
]);

const stripVerilogCommentsForIdentifiers = (text: string): string =>
  text.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/\/\/.*$/gm, ' ');

const isNumericLiteralIdentifier = (text: string, start: number): boolean => {
  const before = text.slice(Math.max(0, start - 4), start);
  return /'\s*[sS]?$/.test(before);
};

export const sourceLineIdentifiers = (line: unknown): string[] => {
  const ids: string[] = [];
  const seen = new Set<string>();
  const text = stripVerilogCommentsForIdentifiers(String(line || ''));
  const re = /\b([A-Za-z_][A-Za-z0-9_$]*)\b(\s*\[[^\]\n]+\])?/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    const base = m[1];
    if (isNumericLiteralIdentifier(text, m.index)) continue;
    const id = `${base}${m[2] ? m[2].replace(/\s+/g, '') : ''}`;
    const key = id.toLowerCase();
    if (VERILOG_KEYWORDS.has(base.toLowerCase()) || seen.has(key)) continue;
    seen.add(key);
    ids.push(id);
  }
  return ids;
};

export const signalAliasKeys = (sig: VcdSignal | null | undefined): string[] => {
  // The VCD parser stores the leaf in `name` and the dotted hierarchy in
  // `scope` (e.g. name="mctp_som", scope="NEWIP_MCTP.u_packet_engine"). A pin
  // from the agent or a fully-qualified add carries the WHOLE path
  // ("NEWIP_MCTP.u_packet_engine.mctp_som"), so we must also expose the
  // scope-qualified form as an alias — otherwise such pins never match and the
  // row is wrongly flagged "not in VCD". The scope-qualified form is unique per
  // signal, so this adds no ambiguity (unlike a bare leaf fallback, which would
  // collide top `sram_req` with `u_packet_engine.sram_req`).
  const scope = String(sig?.scope || '').trim();
  const aliases = Array.isArray(sig?.aliases) ? sig!.aliases! : [];
  // Alias entries are ALREADY fully-qualified (e.g.
  // "NEWIP_MCTP.u_packet_engine.sram_req_o") — they go in as-is (plus their
  // leaf); the scope-qualified form below only applies to the leaf names.
  return [sig?.signalName, sig?.name, stripSignalRange(sig?.name), ...aliases]
    .map(a => String(a || '').trim())
    .filter(Boolean)
    .flatMap(a => {
      const forms = [a, a.split('.').pop() as string];
      if (scope) forms.push(`${scope}.${a}`);
      return forms;
    })
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
  const wantedRange = signalRangeOf(name).toLowerCase();
  const rowRange = (signalRangeOf(sig?.name) || signalRangeOf(sig?.range)).toLowerCase();
  if (wantedRange && wantedRange !== rowRange) return false;
  const sigScope = String(sig?.scope || '').trim();
  const wantedScope = String(scope || '').trim();
  if (wantedScope && sigScope !== wantedScope) return false;
  return signalAliasKeys(sig).includes(wanted);
};

const uniqueWaveRows = (rows: VcdSignal[]): VcdSignal[] => {
  const seen = new Set<string>();
  const out: VcdSignal[] = [];
  for (const row of rows) {
    const key = waveSignalKey(row);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(row);
  }
  return out;
};

export const resolvePinnedWaveSignal = (
  allRows: VcdSignal[],
  pin: PinnedSignal | null | undefined,
): VcdSignal | null => {
  const wanted = stripSignalRange(pin?.name).toLowerCase();
  if (!wanted) return null;
  const wantedScope = String(pin?.scope || '').trim();
  const scopeKey = wantedScope.toLowerCase();

  // Collapse a candidate set to ONE row. An ambiguous match resolves ONLY when
  // there is a UNIQUE shortest (top-level) scope — the canonical instance of a
  // bus (paddr/pwdata/prdata) fanned out to descendant scopes (tb → dut →
  // sub-block) carrying the SAME value. Returning null there made
  // buildWaveTraceList mislabel a DUMPED signal as "⚠ not in VCD". A TIE for the
  // shortest scope means genuinely different sibling nets (e.g. u_a.ready vs
  // u_b.ready) — stay unresolved so the UI never picks the wrong net (SDR-022/023).
  const depth = (r: VcdSignal) => String(r?.scope || '').split('.').filter(Boolean).length;
  const pickBest = (cands: VcdSignal[]): VcdSignal | null => {
    const uniq = uniqueWaveRows(cands);
    if (uniq.length <= 1) return uniq[0] || null;
    const scoped = scopeKey
      ? uniq.filter(r => {
          const rs = String(r?.scope || '').trim().toLowerCase();
          return rs === scopeKey || rs.endsWith(`.${scopeKey}`) || scopeKey.endsWith(`.${rs}`);
        })
      : [];
    const pool = scoped.length ? scoped : uniq;
    if (pool.length === 1) return pool[0];
    const sorted = [...pool].sort((a, b) => depth(a) - depth(b));
    return depth(sorted[0]) < depth(sorted[1]) ? sorted[0] : null;
  };

  const exact = pickBest(allRows.filter(row => waveSignalMatches(row, wanted, wantedScope)));
  if (exact) return exact;
  if (wantedScope) {
    const scoped = pickBest(allRows.filter(row => {
      const rowScope = String(row?.scope || '').trim().toLowerCase();
      const scopeOk = rowScope === scopeKey || rowScope.endsWith(`.${scopeKey}`);
      return scopeOk && signalAliasKeys(row).some(alias =>
        alias === wanted || alias.endsWith(`.${wanted}`));
    }));
    if (scoped) return scoped;
  }

  // Tool calls commonly send RTL-ish paths without the VCD top/testbench prefix
  // (e.g. "u_core.done" for "tb.dut.u_core.done").
  if (wanted.includes('.')) {
    const suffix = pickBest(allRows.filter(row =>
      signalAliasKeys(row).some(alias => alias === wanted || alias.endsWith(`.${wanted}`))));
    if (suffix) return suffix;
  }

  // Last resort: match by bare leaf even when the prefix is a module name rather
  // than VCD hierarchy.
  const leaf = wanted.split('.').pop() || '';
  if (!leaf) return null;
  return pickBest(allRows.filter(row =>
    signalAliasKeys(row).some(alias => (alias.split('.').pop() || '') === leaf)));
};

// Given the signals being (re-)added to the wave, return the removedSignals list
// with any entry that should come back DROPPED. A signal removed via keep/clear
// is stored by its VCD row (leaf + concrete scope, e.g. psel@apb_timer_pwm_irq_v1),
// but a chat/source re-add can arrive fully-qualified under a DIFFERENT hierarchy
// (tb_apb_timer_pwm_irq_v1.psel). A strict string compare missed that, so the row
// stayed hidden ("add does nothing"). Resolve each re-added pin to its actual VCD
// row and drop any removal that would hide THAT row (the same match the wave
// traceList filter uses), with a string fallback for not-in-VCD placeholders.
export const removedSignalsAfterReAdd = (
  allRows: VcdSignal[],
  removed: PinnedSignal[],
  reAddedPins: PinnedSignal[],
): PinnedSignal[] => {
  const scopeMatches = (a: unknown, b: unknown): boolean => {
    const aa = String(a || '').trim().toLowerCase();
    const bb = String(b || '').trim().toLowerCase();
    if (!aa && !bb) return true;
    if (!aa || !bb) return false;
    return aa === bb || aa.endsWith(`.${bb}`) || bb.endsWith(`.${aa}`);
  };
  const reAddedRows = (reAddedPins || [])
    .map(pin => resolvePinnedWaveSignal(allRows, pin))
    .filter((r): r is VcdSignal => !!r);
  return (removed || []).filter(rm => {
    if (reAddedRows.some(row => waveSignalMatches(row, rm.name, rm.scope))) return false;
    return !(reAddedPins || []).some(it =>
      stripSignalRange(it.name).toLowerCase() === stripSignalRange(rm.name).toLowerCase()
      && signalRangeOf(it.name).toLowerCase() === signalRangeOf(rm.name).toLowerCase()
      && scopeMatches(it.scope, rm.scope));
  });
};

// Normalized signal identity used to key per-signal decoration (color, group
// tag). Same lowercasing/range-strip as the alias keys, scope-qualified when a
// scope is present so it's unique across the design. UI writes use this; agent
// writes use whatever name they passed — both resolve via lookupSignalMeta.
export const sigIdent = (sig: VcdSignal | null | undefined): string =>
  stripSignalRange(sig?.scope ? `${sig.scope}.${sig.name}` : (sig?.name || '')).toLowerCase();

// Look up a per-signal decoration value by ANY of the signal's alias keys, so
// a value stored under the agent's name (a submodule-port path, a leaf, …) OR
// the row's canonical ident both resolve. undefined when none match.
export const lookupSignalMeta = <T,>(
  dict: Record<string, T> | null | undefined,
  sig: VcdSignal | null | undefined,
): T | undefined => {
  if (!dict) return undefined;
  for (const a of signalAliasKeys(sig)) {
    if (Object.prototype.hasOwnProperty.call(dict, a)) return dict[a];
  }
  return undefined;
};

export type WaveGroupState = Record<string, { folded: boolean; color?: string }>;
export type WaveDisplayItem =
  | { type: 'group'; tag: string; count: number; folded: boolean; color?: string }
  | { type: 'sig'; sig: VcdSignal; tag: string };

// Build the ordered render list for the wave band: a group header followed by
// its (contiguous) members, interleaved with ungrouped rows. Members of a tag
// are pulled together at the position of the tag's FIRST member in traceList so
// a group reads as one block; folded groups render the header only.
export const buildWaveDisplayRows = (
  traceList: VcdSignal[],
  signalTags: Record<string, string> | null | undefined,
  groupState: WaveGroupState | null | undefined,
): WaveDisplayItem[] => {
  const tags = signalTags || {};
  const groups = groupState || {};
  const tagOf = (sig: VcdSignal): string => {
    for (const a of signalAliasKeys(sig)) { if (tags[a]) return tags[a]; }
    return '';
  };
  const items: WaveDisplayItem[] = [];
  const placed = new Set<string>();
  for (const sig of traceList) {
    const key = waveSignalKey(sig);
    if (placed.has(key)) continue;
    const tag = tagOf(sig);
    if (tag) {
      const members = traceList.filter(s => tagOf(s) === tag);
      const folded = !!groups[tag]?.folded;
      items.push({ type: 'group', tag, count: members.length, folded, color: groups[tag]?.color });
      for (const m of members) placed.add(waveSignalKey(m));
      if (!folded) for (const m of members) items.push({ type: 'sig', sig: m, tag });
    } else {
      items.push({ type: 'sig', sig, tag: '' });
      placed.add(key);
    }
  }
  return items;
};

export type WaveReorderPlacement = 'before' | 'after';

export const reorderWaveKeys = (
  orderedKeys: string[] | null | undefined,
  movingKeys: string[] | null | undefined,
  targetKeys: string[] | null | undefined,
  placement: WaveReorderPlacement = 'before',
): string[] => {
  const current = (orderedKeys || []).map(k => String(k || '')).filter(Boolean);
  const currentSet = new Set(current);
  const moving = (movingKeys || [])
    .map(k => String(k || ''))
    .filter(k => k && currentSet.has(k));
  const movingSet = new Set(moving);
  const target = (targetKeys || [])
    .map(k => String(k || ''))
    .filter(k => k && currentSet.has(k) && !movingSet.has(k));
  if (!current.length || !moving.length || !target.length) return current;
  const remaining = current.filter(k => !movingSet.has(k));
  const targetKey = placement === 'after'
    ? [...target].reverse().find(k => remaining.includes(k))
    : target.find(k => remaining.includes(k));
  if (!targetKey) return current;
  const targetIdx = remaining.indexOf(targetKey);
  const insertAt = placement === 'after' ? targetIdx + 1 : targetIdx;
  return [
    ...remaining.slice(0, insertAt),
    ...moving,
    ...remaining.slice(insertAt),
  ];
};

export const waveRowFromVcdSignal = (vcdData: VcdData, sig: VcdSignal): VcdSignal => ({
  name: (sig.name as string) + (sig.range || ''),
  signalName: sig.name,
  scope: sig.scope,
  range: sig.range || '',
  trace: (vcdData.samples && sig.id != null ? vcdData.samples[sig.id] : undefined) || [],
  isBus: sig.isBus,
  radix: sig.isBus ? 'HEX' : undefined,
  aliases: sig.aliases,
});

const parseSignalRange = (range: unknown): { left: number; right: number; width: number } | null => {
  const body = signalRangeOf(range).slice(1, -1).trim();
  if (!body) return null;
  const parts = body.split(':').map(p => Number(p.trim()));
  if (parts.some(n => !Number.isInteger(n))) return null;
  const left = parts[0];
  const right = parts.length > 1 ? parts[1] : parts[0];
  return { left, right, width: Math.abs(left - right) + 1 };
};

const sliceBusValue = (value: unknown, fullRange: { left: number; right: number; width: number }, reqRange: { left: number; right: number; width: number }): unknown => {
  const s = String(value);
  if (/^[xXzZ]$/.test(s)) return s.repeat(reqRange.width);
  if (!/^[01xXzZ]+$/.test(s)) return value;
  const pad = /^[xXzZ]+$/.test(s) ? s[0] : '0';
  const bits = s.length >= fullRange.width
    ? s.slice(-fullRange.width)
    : s.padStart(fullRange.width, pad);
  const fullStep = fullRange.left <= fullRange.right ? 1 : -1;
  const reqStep = reqRange.left <= reqRange.right ? 1 : -1;
  const out: string[] = [];
  for (let bit = reqRange.left; ; bit += reqStep) {
    const pos = (bit - fullRange.left) / fullStep;
    out.push(pos >= 0 && pos < bits.length ? bits[pos] : 'x');
    if (bit === reqRange.right) break;
  }
  return out.join('');
};

const compactTraceValueChanges = (trace: Array<[unknown, unknown] | unknown[]>): Array<[unknown, unknown] | unknown[]> => {
  const out: Array<[unknown, unknown] | unknown[]> = [];
  for (const sample of trace || []) {
    if (!Array.isArray(sample)) continue;
    const prev = out[out.length - 1];
    if (prev && String(prev[1]) === String(sample[1])) continue;
    out.push(sample);
  }
  return out;
};

const applyPinnedRange = (row: VcdSignal, pin: PinnedSignal | null | undefined): VcdSignal => {
  const reqText = signalRangeOf(pin?.name);
  if (!reqText) return row;
  const rowRangeText = signalRangeOf(row.range) || signalRangeOf(row.name);
  if (!rowRangeText || rowRangeText === reqText) return row;
  const fullRange = parseSignalRange(rowRangeText);
  const reqRange = parseSignalRange(reqText);
  if (!fullRange || !reqRange) return row;
  const trace = Array.isArray(row.trace)
    ? row.trace.map(sample => Array.isArray(sample)
        ? [sample[0], sliceBusValue(sample[1], fullRange, reqRange)] as [unknown, unknown]
        : sample)
    : [];
  const compactTrace = compactTraceValueChanges(trace);
  const base = stripSignalRange(row.signalName || row.name || pin?.name || '');
  return {
    ...row,
    name: `${base}${reqText}`,
    signalName: base,
    range: reqText,
    trace: compactTrace,
    isBus: reqRange.width > 1,
    radix: reqRange.width > 1 ? 'HEX' : undefined,
  };
};

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
    const found = resolvePinnedWaveSignal(allRows, pin);
    if (found) {
      const row = applyPinnedRange(found, pin);
      const key = waveSignalKey(row);
      if (present.has(key)) continue;
      rows.push(row);
      present.add(key);
    } else {
      // Pinned but absent from this VCD (e.g. an internal signal that wasn't
      // dumped). Still show a row so "Add to waveform" gives visible feedback
      // instead of silently doing nothing — flagged so the UI can mark it.
      // Split the dotted path into scope + leaf so this placeholder honors the
      // SAME top-strip + `h` hierarchy toggle as real rows (otherwise it sticks
      // out showing the raw fully-qualified name and ignoring `h`).
      const range = signalRangeOf(pin.name);
      const full = stripSignalRange(pin.name);
      if (!full) continue;
      const dot = full.lastIndexOf('.');
      const leaf = dot >= 0 ? full.slice(dot + 1) : full;
      const scope = String(pin.scope || (dot >= 0 ? full.slice(0, dot) : '')).trim();
      const key = `${scope}/${leaf}${range}`.toLowerCase();
      if (present.has(key)) continue;
      const rangeWidth = parseSignalRange(range)?.width || 1;
      rows.push({
        name: `${leaf}${range}`,
        signalName: leaf,
        scope,
        range,
        trace: [],
        isBus: rangeWidth > 1,
        radix: rangeWidth > 1 ? 'HEX' : undefined,
        notInVcd: true,
      } as VcdSignal);
      present.add(key);
    }
  }
  return rows;
};

// Drop the leading top-module segment from a scope-qualified signal name, so
// the always-present `NEWIP_MCTP.` prefix isn't repeated on every row.
//   stripTopScope('NEWIP_MCTP.u_irq.event_sync', 'NEWIP_MCTP') → 'u_irq.event_sync'
export const stripTopScope = (name: unknown, top: unknown): string => {
  const s = String(name || '');
  const t = String(top || '').trim();
  return t && s.startsWith(t + '.') ? s.slice(t.length + 1) : s;
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

// Build a name matcher for the signal-search box. Tries the query as a
// regex first (case-insensitive); on an invalid pattern it falls back to
// a case-insensitive substring test so a half-typed regex like `cnt[`
// still filters instead of throwing. Empty query matches everything.
//   { test, isRegex, valid } — `valid` is false only when a non-empty
//   query failed to compile as a regex (UI can flag it but still filters).
export const buildSignalSearchMatcher = (
  query: string,
): { test: (name: string) => boolean; isRegex: boolean; valid: boolean } => {
  const q = String(query || '').trim();
  if (!q) return { test: () => true, isRegex: false, valid: true };
  try {
    const re = new RegExp(q, 'i');
    return { test: (name: string) => re.test(String(name || '')), isRegex: true, valid: true };
  } catch (_) {
    const lower = q.toLowerCase();
    return {
      test: (name: string) => String(name || '').toLowerCase().includes(lower),
      isRegex: false,
      valid: false,
    };
  }
};

// ── Waveform chat/command parser ─────────────────────────────────
// Turns a typed command into a waveform action: place cursor A/B, zoom to a
// time range, fit, or zoom to the A↔B span. Tolerant of several phrasings:
//   "a 5000"  "a=5000 b=15000"  "cursor b 12000"
//   "zoom 1000 5000"  "view 1000-5000"  "확대 1000 5000"
//   "fit" / "전체"     "a..b" / "zoom a b" / "ab"
//   bare "1000 5000" → zoom · bare "5000" → cursor A
export interface WaveCommand {
  cursorA?: number;
  cursorB?: number;
  view?: [number, number];
  fit?: boolean;
  zoomCursors?: boolean;
}
export const parseWaveCommand = (input: string): WaveCommand | null => {
  const t = String(input || '').trim().toLowerCase();
  if (!t) return null;
  if (/^(fit|reset|전체|맞춤)$/.test(t)) return { fit: true };
  if (/^(a\s*[-~.·]+\s*b|zoom\s*a\s*b|a\s*b|ab)$/.test(t)) return { zoomCursors: true };
  const cmd: WaveCommand = {};
  const am = t.match(/(?:^|[^a-z])a\s*[:=]?\s*(-?\d+)/);
  const bm = t.match(/(?:^|[^a-z])b\s*[:=]?\s*(-?\d+)/);
  const zm = t.match(/(?:zoom|view|확대|범위|구간)\D*?(-?\d+)\D+?(-?\d+)/);
  if (am) cmd.cursorA = parseInt(am[1], 10);
  if (bm) cmd.cursorB = parseInt(bm[1], 10);
  if (zm) cmd.view = [parseInt(zm[1], 10), parseInt(zm[2], 10)];
  if (cmd.cursorA == null && cmd.cursorB == null && !cmd.view) {
    const nums = (t.match(/-?\d+/g) || []).map(n => parseInt(n, 10));
    if (nums.length >= 2) cmd.view = [nums[0], nums[1]];
    else if (nums.length === 1) cmd.cursorA = nums[0];
    else return null;
  }
  return cmd;
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
  g.simDebugParseVerilogParamValueMap = parseVerilogParamValueMap;
  g.simDebugReorderWaveKeys = reorderWaveKeys;
  g.simDebugAnnotationAxesForMode = annotationAxesForMode;
}
