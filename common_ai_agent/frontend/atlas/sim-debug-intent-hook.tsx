// sim-debug-intent-hook.tsx — the agent→panel intent channel extracted from the
// SimDebug root as a self-contained hook. The `sim_debug` agent tool pushes an
// intent (navigate / show signals / cursor / trace / fit) to
// /api/sim_debug/intent; this hook polls it (while the panel is active) and
// applies it via the capabilities the root passes in. Latest-ref pattern so the
// poll always calls the freshest handlers without resetting the interval.
import { useEffect, useRef } from 'react';
import type { VcdData, PinnedSignal } from './sim-debug-helpers';
import type { ViewRange } from './sim-debug-root-shared';

export interface SimDebugIntentDeps {
  ipName: string;
  active: boolean;
  vcdData: VcdData | null;
  pinSignalsToWave: (items: PinnedSignal[]) => void;
  setViewRange: (r: ViewRange) => void;
  setTopTab: (t: string) => void;
  setExpand: (e: string) => void;
  setWaveCursor: (t: number) => void;
  setWaveCursorB: (t: number) => void;
  runSignalTrace: (name: string, scope?: string) => void;
  zoomFit: () => void;
  reorderByNames: (names: string[]) => void;
  setSignalColorByNames: (names: string[], color: string | null) => void;
  assignGroupByNames: (names: string[], tag: string, color?: string | null) => void;
  ungroupByNames: (names: string[]) => void;
  toggleGroupFold: (tag: string, folded?: boolean) => void;
}

export interface SimDebugIntentDecision {
  apply: boolean;
  key: string;
  seq: number;
}

export type SimDebugIntentSeqMap = Record<string, number>;

export const shouldApplySimDebugIntent = (
  ipName: string,
  intent: any,
  seenSeqByKey: SimDebugIntentSeqMap,
): SimDebugIntentDecision => {
  const seq = Number(intent?.seq);
  if (!ipName || !Number.isFinite(seq)) return { apply: false, key: '', seq: 0 };
  const targetIp = String(intent?.ip || '').trim();
  if (targetIp && targetIp !== ipName) {
    // Do not consume another IP's intent. If the user switches to that IP
    // later, the same latest intent should still catch up and apply there.
    return { apply: false, key: targetIp, seq };
  }
  const key = targetIp || '*';
  return { apply: seq > (seenSeqByKey[key] || 0), key, seq };
};

const applyIntent = (d: SimDebugIntentDeps, intent: any): void => {
  const action = String(intent?.action || '');
  const defaultScope = String(intent?.scope || '').trim();
  const clampT = (n: number) => {
    const v = Math.round(Number(n));
    if (!d.vcdData) return v;
    const [lo, hi] = d.vcdData.timeRange as [number, number];
    return Math.max(lo, Math.min(hi, v));
  };
  // Any intent carrying signals adds them first (also switches to the wave tab)
  // so goto/cursor/find/value land with the signal visible.
  const rawSignals = Array.isArray(intent.signals) ? intent.signals
    : (intent.signal ? [intent.signal] : []);
  const sigs: PinnedSignal[] = rawSignals
    .map((s: unknown) => {
      if (s && typeof s === 'object') {
        const obj = s as { name?: unknown; signal?: unknown; scope?: unknown };
        return {
          name: String(obj.name || obj.signal || '').trim(),
          scope: String(obj.scope || defaultScope || '').trim(),
        };
      }
      return { name: String(s || '').trim(), scope: defaultScope };
    })
    .filter((s: PinnedSignal) => !!s.name);
  const sigNames: string[] = sigs.map((s) => {
    const name = String(s.name || '').trim();
    const scope = String(s.scope || '').trim();
    return scope && !name.toLowerCase().startsWith(scope.toLowerCase() + '.') ? `${scope}.${name}` : name;
  });
  // Pin the signals first for actions that act ON shown signals, so the
  // group/color/order lands with them visible. trace/ungroup/fold don't add.
  if (sigs.length && action !== 'trace' && action !== 'ungroup') d.pinSignalsToWave(sigs);

  if (action === 'goto') {
    if (intent.t_start != null && intent.t_end != null) {
      const a = clampT(Math.min(intent.t_start, intent.t_end));
      const b = clampT(Math.max(intent.t_start, intent.t_end));
      if (b - a >= 1) { d.setViewRange([a, b]); d.setTopTab('wave'); d.setExpand('split'); }
    }
    if (intent.cursor_a != null) d.setWaveCursor(clampT(intent.cursor_a));
    if (intent.cursor_b != null) d.setWaveCursorB(clampT(intent.cursor_b));
  } else if (action === 'cursor') {
    if (intent.cursor_a != null) d.setWaveCursor(clampT(intent.cursor_a));
    if (intent.cursor_b != null) d.setWaveCursorB(clampT(intent.cursor_b));
    d.setTopTab('wave');
  } else if (action === 'trace') {
    if (sigs.length) { d.setTopTab('wave'); d.runSignalTrace(String(sigs[0].name), String(sigs[0].scope || '')); }
  } else if (action === 'fit') {
    d.zoomFit();
  } else if (action === 'reorder') {
    d.reorderByNames(sigNames);
  } else if (action === 'group') {
    if (intent.group) d.assignGroupByNames(sigNames, String(intent.group), intent.color ? String(intent.color) : null);
  } else if (action === 'ungroup') {
    if (sigNames.length) d.ungroupByNames(sigNames);
  } else if (action === 'color') {
    if (intent.color) d.setSignalColorByNames(sigNames, String(intent.color));
  } else if (action === 'fold' || action === 'unfold') {
    if (intent.group) d.toggleGroupFold(String(intent.group), action === 'fold');
  }
};

export const useSimDebugIntent = (deps: SimDebugIntentDeps): void => {
  const intentSeqRef = useRef<SimDebugIntentSeqMap>({});
  const depsRef = useRef(deps);
  depsRef.current = deps;
  const { ipName, active } = deps;
  useEffect(() => {
    if (!ipName || !active) return undefined;  // only poll while the panel is visible
    let cancelled = false;
    const tick = async () => {
      try {
        const r = await fetch('/api/sim_debug/intent?ip=' + encodeURIComponent(ipName), { cache: 'no-store' });
        const d = await r.json();
        if (cancelled || !d || typeof d.seq !== 'number') return;
        const decision = shouldApplySimDebugIntent(ipName, d, intentSeqRef.current);
        if (decision.apply) {
          intentSeqRef.current[decision.key] = decision.seq;
          applyIntent(depsRef.current, d);
        }
      } catch (_) { /* ignore poll errors */ }
    };
    tick();  // immediate catch-up when the tab opens
    const id = setInterval(tick, 1500);
    return () => { cancelled = true; clearInterval(id); };
  }, [ipName, active]);
};
