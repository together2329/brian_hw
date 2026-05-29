// soc-architect-shared.tsx — shared helpers for the soc-architect.tsx family
// (TypeScript migration of soc-architect.jsx, strangler-fig split).
//
// These module-scope helpers + small data utilities were defined at the top of
// soc-architect.jsx and used by SocArchitect, ArchitectChat, JobTracker, and
// the pipeline helpers alike. They are pulled into this sibling so the main
// file can stay focused on the SocArchitect root component.
//
// Transitional: bridges to `window.*` at the bottom so the (still-live) legacy
// .jsx never sees these and so the rest of THIS family can resolve them through
// window at call time without import-ordering hazards.

const g = window as unknown as Record<string, any>;

export const normalizeArchitectSession = (session: unknown): string => {
  const norm = (g.atlasData && g.atlasData.normalizeSessionName) || g.normalizeAtlasSessionName;
  try { return norm ? norm(session || '') : ''; }
  catch (_) { return ''; }
};

export const architectEventMatchesActiveSession = (
  m: any,
  opts: { requireSession?: boolean } = {},
): boolean => {
  const eventSession = normalizeArchitectSession((m && (m.session_id || m.session || m.namespace)) || '');
  const activeSession = normalizeArchitectSession(
    window.ACTIVE_SESSION
    || (window.CONTEXT && (window.CONTEXT.activeSession || window.CONTEXT.active_session))
    || ''
  );
  if (!activeSession) return !opts.requireSession;
  if (!eventSession) return !opts.requireSession;
  return eventSession === activeSession;
};

// ── Live SoC fetch ─────────────────────────────────────────────
// Pulls `/api/soc` and folds the response into a SOC-shaped object
// the renderers expect. Falls back to the bundled mock if the
// endpoint is unavailable or returns no clusters.
export function _fetchLiveSoc(ipName?: string): Promise<any> {
  // Scope to a single IP when the landing grid opens one (`?ip=<name>` →
  // backend returns just that IP's modules). Otherwise honor any global
  // SCOPE_PATH the Workspace screen set (`?scope=<path>`).
  let url = '/api/soc';
  if (ipName) {
    url = `/api/soc?ip=${encodeURIComponent(ipName)}`;
  } else {
    const scoped = String(window.SCOPE_PATH || '').replace(/^\/+|\/+$/g, '');
    if (scoped) url = `/api/soc?scope=${encodeURIComponent(scoped)}`;
  }
  return fetch(url).then(r => {
    if (!r.ok) throw new Error('soc fetch failed');
    return r.json();
  }).then(d => {
    if (!d || !Array.isArray(d.clusters) || d.clusters.length === 0) return null;
    // Position any cluster that lacks x/y so the diagram doesn't
    // collapse all blocks onto (0,0). Tile horizontally.
    d.clusters.forEach((c: any, i: number) => {
      if (typeof c.x !== 'number') c.x = 80 + i * 540;
      if (typeof c.y !== 'number') c.y = 90;
      if (typeof c.w !== 'number') c.w = 480;
      if (typeof c.h !== 'number') c.h = 460;
      (c.modules || []).forEach((m: any, j: number) => {
        if (typeof m.x !== 'number') m.x = 24 + (j % 3) * 150;
        if (typeof m.y !== 'number') m.y = 56 + Math.floor(j / 3) * 110;
        if (typeof m.w !== 'number') m.w = 140;
        if (typeof m.h !== 'number') m.h = 90;
        if (!Array.isArray(m.interfaces)) m.interfaces = [];
        if (!Array.isArray(m.params)) m.params = [];
      });
    });
    if (!Array.isArray(d.busses)) d.busses = [];
    if (!Array.isArray(d.addrMap)) d.addrMap = [];
    return d;
  }).catch(() => null);
}

// Tree-search helpers — case-insensitive substring match against the
// module's id and name + the cluster id. Returns true when query is
// empty (so the tree is unfiltered by default).
export function _matchesQuery(m: any, clusterId: string, q: string): boolean {
  if (!q) return true;
  const needle = q.toLowerCase();
  const hay = `${m.id || ''} ${m.name || ''} ${m.label || ''} ${clusterId || ''}`.toLowerCase();
  return hay.includes(needle);
}
// Wrap matched substrings in <mark>; safe-escape the rest so we can
// drop into dangerouslySetInnerHTML without an XSS hole.
export function _highlightMatch(text: unknown, q: string): string {
  const t = String(text || '');
  if (!q) return t.replace(/[<>&]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c] as string));
  const esc = t.replace(/[<>&]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c] as string));
  const re = new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
  return esc.replace(re, '<mark style="background:color-mix(in oklch, var(--accent) 35%, transparent);color:var(--fg);padding:0 1px;">$1</mark>');
}

export function _buildLookup(soc: any): Record<string, { cluster: any; module: any }> {
  const lk: Record<string, { cluster: any; module: any }> = {};
  for (const c of soc.clusters) {
    for (const m of c.modules) lk[`${c.id}/${m.id}`] = { cluster: c, module: m };
  }
  return lk;
}

// Empty, shape-valid SoC used when no IP is selected (landing grid) or while
// a selected IP's `/api/soc` fetch is in flight. Replaces the old aurora_soc
// mock fallback so the demo SoC never renders for a real user.
export const EMPTY_SOC = { name: '', version: '', clusters: [], busses: [], addrMap: [] };

// ── Transitional bridge: register on window so the rest of this family can
// resolve through window at call time (no import-ordering hazard). ──
g.normalizeArchitectSession = normalizeArchitectSession;
g.architectEventMatchesActiveSession = architectEventMatchesActiveSession;
g._socArchFetchLiveSoc = _fetchLiveSoc;
g._socArchMatchesQuery = _matchesQuery;
g._socArchHighlightMatch = _highlightMatch;
g._socArchBuildLookup = _buildLookup;
g._socArchEmptySoc = EMPTY_SOC;
