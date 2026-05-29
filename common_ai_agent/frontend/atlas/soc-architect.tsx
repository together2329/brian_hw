// soc-architect.tsx — Combined V6 + V7 Architect screen (root component).
// TypeScript migration of soc-architect.jsx (strangler-fig split).
//
// Shared 3-column layout (hierarchy tree · center · chat). Center is
// a [Diagram | Status] tab toggle:
//   diagram → V7 drill-in canvas (SoC ▸ cluster ▸ module + bus routing)
//   status  → V6 orch grid + ssot.yaml editor on the selected module
//
// Mock data only — pulls from window.SOC / window.SOC_LOOKUP that
// soc-data.jsx loads. No live backend wiring yet.
//
// SPLIT NOTE: soc-architect.jsx was one 4210-line mega-root. This file keeps
// the SocArchitect root component — its state, effects, derived data and the
// outer render shell. The big render closures + JSX sub-trees read a fixed,
// enumerable set of in-scope values, so each was lifted into a sibling
// UNCHANGED and is now called with an in-scope `ctx` bag at render time
// (behavior-preserving — TS still type-checks every call site). The
// self-contained pieces were extracted into siblings:
//   - soc-architect-styles.tsx    (the injectStyles CSS side-effect)
//   - soc-architect-shared.tsx    (session + fetch/lookup helpers, EMPTY_SOC)
//   - soc-architect-pipeline.tsx  (PIPELINE_STAGES/LABEL, fullPipeline,
//                                   PipelineStrip, ModuleProgressPanel)
//   - soc-architect-panels.tsx    (ArchitectMyIps, IpxactImportBtn, JobTracker)
//   - soc-architect-chat.tsx      (ArchitectChat)
//   - soc-architect-diagrams.tsx  (renderSocView / renderClusterView /
//                                   renderModuleView — the V7 diagram closures)
//   - soc-architect-canvas.tsx    (renderDiagramCanvas — pan/zoom/mini-map)
//   - soc-architect-tree.tsx      (renderHierarchyPanel + renderWorkspaceNode)
//   - soc-architect-views.tsx     (renderStatusGrid / renderDispatchMenu /
//                                   renderSparkPopover)
//
// The styles module is imported FIRST, for its DOM side-effect, preserving the
// original eval-time ordering (injectStyles ran at the top of the .jsx).
//
// Strict-typing note: this is a large mechanical translation of untyped JS, so
// closure-local accumulators + callback params are left as inferred/implicit
// where TS would otherwise demand annotations. These are type-only concerns and
// do NOT affect runtime behavior; precise typing lands at the import-cutover.
import './soc-architect-styles';
import { useState, useEffect, useMemo, useRef, useCallback, Fragment } from 'react';
import { ArchitectMyIps } from './soc-architect-panels';
import {
  normalizeArchitectSession,
  architectEventMatchesActiveSession,
  _fetchLiveSoc,
  _matchesQuery,
  _buildLookup,
  EMPTY_SOC,
} from './soc-architect-shared';
// The big diagram render closures + JSX sub-trees live in siblings (each
// UNCHANGED, fed an in-scope `ctx` bag at call time) so this file stays
// under 1000 lines. See the SPLIT NOTE in each sibling.
import {
  renderSocView as renderSocViewExt,
  renderClusterView as renderClusterViewExt,
  renderModuleView as renderModuleViewExt,
} from './soc-architect-diagrams';
import {
  renderStatusGrid,
  renderDispatchMenu,
  renderSparkPopover,
} from './soc-architect-views';
import { renderDiagramCanvas } from './soc-architect-canvas';
import { renderHierarchyPanel } from './soc-architect-tree';
// soc-architect-pipeline.tsx + soc-architect-chat.tsx register their globals on
// window for THIS file to resolve at render time (matching the legacy
// window.* lookups). Imported for that side-effect; the components themselves
// are read through `g` below so resolution stays at render time.
import './soc-architect-pipeline';
import './soc-architect-chat';

const g = window as unknown as Record<string, any>;

// Cross-file components resolved at render time through window — exactly as the
// legacy `window.X` JSX did. JobTracker / ArchitectChat / IpxactImportBtn are
// owned by this file's own .tsx siblings. Keeping them as window forward-refs
// avoids any import-ordering hazard and preserves behavior. (PipelineStrip /
// ModuleProgressPanel / StatusTrio are only referenced inside the extracted
// render siblings now, so each owns its own forward-ref.)
const JobTracker = (props: any): any => g.JobTracker(props);
const ArchitectChat = (props: any): any => g.ArchitectChat(props);
const IpxactImportBtn = (props: any): any => g.IpxactImportBtn(props);

// ── SocArchitect — the combined screen ──────────────────────────
export function SocArchitect(props: any = {}) {
  const ipList = (props.ipOptions && props.ipOptions.length ? props.ipOptions : g.IP_OPTIONS) || [];
  const [tab, setTab] = useState('diagram');
  // Landing: '' = show the "My IPs" card grid; '<name>' = show that IP's SoC
  // diagram (fetched via `/api/soc?ip=`). selectedIpRef keeps the current
  // scope available to event-driven refreshes that pass no argument.
  const [selectedIp, setSelectedIp] = useState('');
  const selectedIpRef = useRef('');
  useEffect(() => { selectedIpRef.current = selectedIp; }, [selectedIp]);
  const [view, setView] = useState('soc');           // 'soc' | 'cluster:<id>' | 'module:<ref>'
  const [socTopMode, setSocTopMode] = useState('if'); // 'if' = I/F only, 'detail' = show aux pins/addr
  const [diagramFocus, setDiagramFocus] = useState(false);
  const [leftPanelW, setLeftPanelW] = useState(() => Number(localStorage.getItem('atlas.arch.leftPanelW')) || 240);
  const [rightPanelW, setRightPanelW] = useState(() => Number(localStorage.getItem('atlas.arch.rightPanelW')) || 480);
  const panelResizeRef = useRef<any>(null);
  const [running, setRunning] = useState<any>(null);
  const [layers, setLayers] = useState({
    modules: true, busses: true, clk: false, rst: false, labels: true,
  });
  // Default to fit-to-canvas-ish (70% works for most viewports);
  // bdCanvasRef + the fit() handler below recompute precisely.
  const [zoom, setZoom] = useState(70);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const bdCanvasRef = useRef<any>(null);
  const panDragRef = useRef<any>(null);
  // Per-block manual position overrides + persistence. The actual
  // localStorage key depends on `soc.name`, but `soc` is declared later
  // in this function — so we initialise the state to {} here and the
  // useEffect below (after soc is in scope) loads the right slot.
  const [layout, setLayout] = useState<Record<string, any>>({});
  const blockDragRef = useRef<any>(null);
  // Mini-map toggle
  const [miniOpen, setMiniOpen] = useState(true);
  // Active worker jobs (HTTP-worker dispatched). Polled from /api/jobs
  // every 2s; used by the JobTracker panel + the per-block "running"
  // ring + the block ⚡ menu.
  const [jobs, setJobs] = useState<any[]>([]);
  const beginPanelResize = useCallback((side: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    panelResizeRef.current = {
      side,
      startX: e.clientX,
      left0: leftPanelW,
      right0: rightPanelW,
      viewportW: window.innerWidth || 1440,
    };
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [leftPanelW, rightPanelW]);
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const drag = panelResizeRef.current;
      if (!drag) return;
      const dx = e.clientX - drag.startX;
      if (drag.side === 'left') {
        const next = Math.max(170, Math.min(420, drag.left0 + dx));
        setLeftPanelW(next);
      } else {
        const next = Math.max(320, Math.min(Math.max(360, drag.viewportW - 420), drag.right0 - dx));
        setRightPanelW(next);
      }
    };
    const onUp = () => {
      if (!panelResizeRef.current) return;
      panelResizeRef.current = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      setLeftPanelW(v => {
        localStorage.setItem('atlas.arch.leftPanelW', String(Math.round(v)));
        return v;
      });
      setRightPanelW(v => {
        localStorage.setItem('atlas.arch.rightPanelW', String(Math.round(v)));
        return v;
      });
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, []);
  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const r = await fetch('/api/jobs');
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const d = await r.json();
        if (!cancelled) setJobs(Array.isArray(d.jobs) ? d.jobs : []);
      } catch (_) { /* keep last good */ }
    };
    tick();
    const id = setInterval(tick, 2000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);
  useEffect(() => {
    window.ATLAS_JOBS = jobs || [];
  }, [jobs]);
  // Map ip → most recent running job (used for diagram ring).
  const runningByIp = useMemo(() => {
    const m: Record<string, any> = {};
    for (const j of jobs) {
      if (j.status === 'running' && j.ip) {
        if (!m[j.ip] || (j.started_at || 0) > (m[j.ip].started_at || 0)) m[j.ip] = j;
      }
    }
    return m;
  }, [jobs]);
  const jobsByIp = useMemo(() => {
    const m: Record<string, any> = {};
    for (const j of jobs) {
      if (!j.ip) continue;
      if (!m[j.ip]) m[j.ip] = [];
      m[j.ip].push(j);
    }
    for (const ip of Object.keys(m)) {
      m[ip].sort((a: any, b: any) => (b.started_at || 0) - (a.started_at || 0));
    }
    return m;
  }, [jobs]);
  // Per-block dispatch menu state — anchored to the ⚡ button.
  // {ipRef, x, y} or null.
  const [dispatchMenu, setDispatchMenu] = useState<any>(null);
  const dispatchJob = useCallback(async (workflow: any, ip: any, stageId = '') => {
    setDispatchMenu(null);
    const stageName = stageId || workflow;
    const session = normalizeArchitectSession(ip ? `${ip}/${stageName}` : stageName);
    try {
      const r = await fetch('/api/job/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow,
          ip,
          stage_id: stageId,
          session,
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
      // Force a job poll soon so the ring + tracker update fast.
      setTimeout(() => fetch('/api/jobs').then(r => r.json())
        .then(dd => setJobs(dd.jobs || [])).catch(() => {}), 200);
    } catch (e: any) {
      alert(`dispatch failed: ${e.message || e}\n\n` +
            `Check the worker for ${workflow} is running:\n` +
            `  python src/main.py --serve --port 8001 --worker-name ${workflow}\n` +
            `Or set WORKER_URL_${workflow.toUpperCase().replace(/-/g, '_')} env var.`);
    }
  }, []);
  const dispatchPipeline = useCallback(async (ip: any) => {
    setDispatchMenu(null);
    if (!ip) {
      alert('Select an IP/module first, then run the full pipeline.');
      return;
    }
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
      setTimeout(() => fetch('/api/jobs').then(r => r.json())
        .then(dd => setJobs(dd.jobs || [])).catch(() => {}), 200);
    } catch (e: any) {
      alert(`pipeline dispatch failed: ${e.message || e}`);
    }
  }, []);
  // Sparkline hover popover state — which row is hovered, for the
  // status grid TREND column. {ref, x, y} or null.
  const [sparkPop, setSparkPop] = useState<any>(null);
  // Port-to-port connect state for the top SoC diagram. First click
  // arms a source port; second click writes connections[] through
  // /api/soc/connect and refreshes live data.
  const [pendingPort, setPendingPort] = useState<any>(null);
  const [catalog, setCatalog] = useState<any[]>([]);
  const [workspaceTree, setWorkspaceTree] = useState<any>(null);
  const fitZoom = useCallback(() => {
    const el = bdCanvasRef.current; if (!el) return;
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    // Stage is 1180×720; pick the smaller axis ratio with a small
    // margin so the diagram doesn't kiss the edges.
    const r = Math.min(w / 1180, h / 720) * 0.94;
    setZoom(Math.max(20, Math.min(200, Math.round(r * 100))));
    setPan({ x: 0, y: 0 });          // recenter on fit
  }, []);
  useEffect(() => {
    fitZoom();
    if (typeof ResizeObserver === 'undefined') return;
    const el = bdCanvasRef.current; if (!el) return;
    const ro = new ResizeObserver(() => fitZoom());
    ro.observe(el);
    return () => { try { ro.disconnect(); } catch (_) {} };
  }, [fitZoom, view]);

  // Live data: try `/api/soc` first, fall back to the bundled mock.
  // `live=null` = still loading, `live=false` = fetch failed/empty
  // (use mock), `live=<soc>` = use live data.
  const [live, setLive] = useState<any>(null);
  // Module refs that the agent just touched (mutated SSOT, regen'd RTL,
  // ran sim). Pulses on the diagram + grid until the user clicks
  // somewhere or the next refresh clears them.
  const [touchedSet, setTouchedSet] = useState(() => new Set());
  // Bumped on tool_result events so SocArchitect knows to re-fetch
  // /api/soc (pre-pass debounces multiple events into one fetch).
  const refreshTimerRef = useRef<any>(null);
  const prevModuleRefsRef = useRef(new Set());
  const prevMtimeRef = useRef(new Map());

  // ── Derived data (computed every render, must come BEFORE any
  // useEffect/useMemo that references them — otherwise the deps
  // array hits a TDZ ReferenceError on the first call, the whole
  // component throws, and the screen unmounts.)
  const soc = (live && live.clusters && live.clusters.length) ? live : EMPTY_SOC;
  const lookup = (live && live.clusters && live.clusters.length) ? _buildLookup(live) : {};
  const isLive = !!(live && live.clusters && live.clusters.length);
  useEffect(() => {
    let cancelled = false;
    fetch('/api/catalog/models')
      .then(r => r.json())
      .then(d => { if (!cancelled) setCatalog(Array.isArray(d.models) ? d.models : []); })
      .catch(() => { if (!cancelled) setCatalog([]); });
    return () => { cancelled = true; };
  }, [isLive]);
  useEffect(() => {
    let cancelled = false;
    fetch('/api/workspace/tree?depth=2')
      .then(r => r.json())
      .then(d => { if (!cancelled) setWorkspaceTree(d.root || null); })
      .catch(() => { if (!cancelled) setWorkspaceTree(null); });
    return () => { cancelled = true; };
  }, [isLive]);

  // Hierarchy tree search query — case-insensitive substring match
  // against module id + name. Empty string means "show everything".
  // (Declared after `soc` so the useMemo deps array doesn't hit TDZ.)
  const [treeQuery, setTreeQuery] = useState('');
  const treeMatches = useMemo(() => {
    if (!treeQuery) return [];
    const out = [];
    for (const c of soc.clusters || [])
      for (const m of c.modules || [])
        if (_matchesQuery(m, c.id, treeQuery)) out.push({ ref: `${c.id}/${m.id}`, m, c });
    return out;
  }, [treeQuery, soc]);

  // Layout-persistence key depends on the SoC name so different SoCs
  // keep independent block-position layouts. Reload the layout slot
  // whenever the SoC name changes (Tier-1 ↔ Tier-2 swap, /wf switch).
  const _layoutKey = `architectLayout:${(soc && soc.name) || 'default'}`;
  useEffect(() => {
    try { setLayout(JSON.parse(localStorage.getItem(_layoutKey) || '{}') || {}); }
    catch (_) { setLayout({}); }
  }, [_layoutKey]);
  const persistLayout = useCallback((next: any) => {
    try { localStorage.setItem(_layoutKey, JSON.stringify(next)); } catch (_) {}
  }, [_layoutKey]);
  const getStageScale = useCallback((e: any, stageW = 1180) => {
    const stage = e?.currentTarget?.closest?.('.bd-stage') ||
                  bdCanvasRef.current?.querySelector?.('.bd-stage');
    const rect = stage?.getBoundingClientRect?.();
    if (rect && rect.width > 0) return rect.width / stageW;
    return zoom / 100;
  }, [zoom]);
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const d = blockDragRef.current;
      if (!d || !d.globalDrag) return;
      const dx = (e.clientX - d.startX) / d.scale;
      const dy = (e.clientY - d.startY) / d.scale;
      if (Math.abs(dx) + Math.abs(dy) < 2) return;
      d.dragged = true;
      const nextPos = {
        x: Math.max(0, Math.min(d.maxX, d.baseX + dx)),
        y: Math.max(0, Math.min(d.maxY, d.baseY + dy)),
      };
      setLayout((prev: any) => {
        const next = { ...prev, [d.layoutKey]: nextPos };
        d.latestLayout = next;
        return next;
      });
    };
    const onUp = () => {
      const d = blockDragRef.current;
      if (!d || !d.globalDrag) return;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      if (d.dragged && d.latestLayout) persistLayout(d.latestLayout);
      setTimeout(() => { blockDragRef.current = null; }, 0);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [persistLayout]);

  // Default selection: first module of first cluster (so we don't
  // hold a stale 'periph_ss/spi' ref on a live project that has
  // entirely different IP names).
  const firstRef = (soc && soc.clusters && soc.clusters[0] && soc.clusters[0].modules[0])
    ? `${soc.clusters[0].id}/${soc.clusters[0].modules[0].id}` : '';
  const [selMod, setSelMod] = useState(firstRef);

  const refreshSoc = useCallback((ipName?: any) => {
    // Event-driven refreshes (tool_result, agent actions) pass no argument →
    // re-fetch the currently selected IP via the ref. An explicit name (from
    // opening a card) scopes the fetch to that IP.
    const target = (ipName === undefined || ipName === null) ? selectedIpRef.current : ipName;
    return _fetchLiveSoc(target).then((d: any) => {
      setLive((prev: any) => {
        const next = d || prev || false;
        // Diff module refs: anything new gets marked touched. Also flag
        // a module whose ssot.yaml mtime moved forward (in-place edits
        // without a new module).
        if (next && next.clusters) {
          const nowRefs = new Set();
          const nowMtime = new Map();
          for (const c of next.clusters) for (const m of c.modules) {
            const ref = `${c.id}/${m.id}`;
            nowRefs.add(ref);
            if (m.ssot_mtime) nowMtime.set(ref, m.ssot_mtime);
          }
          const prevRefs = prevModuleRefsRef.current;
          const prevMtime = prevMtimeRef.current;
          const touched: any[] = [];
          for (const r of nowRefs) {
            if (!prevRefs.has(r)) touched.push(r);
            else if (prevMtime.get(r) && nowMtime.get(r) > prevMtime.get(r) + 0.5) touched.push(r);
          }
          if (touched.length && prevRefs.size > 0) {
            setTouchedSet(s => {
              const ns = new Set(s);
              for (const r of touched) ns.add(r);
              return ns;
            });
            // Auto-clear after 10s — the user's eye has caught the pulse
            // by then, and we don't want it animating forever.
            for (const r of touched) {
              setTimeout(() => {
                setTouchedSet(s => {
                  if (!s.has(r)) return s;
                  const ns = new Set(s); ns.delete(r); return ns;
                });
              }, 10000);
            }
          }
          prevModuleRefsRef.current = nowRefs;
          prevMtimeRef.current = nowMtime;
        }
        return next;
      });
    });
  }, []);

  // Fetch the selected IP's SoC when one is open; clear when back on the grid.
  // (No selection → no unscoped project-wide walk; the grid drives its own data.)
  useEffect(() => {
    if (selectedIp) refreshSoc(selectedIp);
    else setLive(null);
  }, [selectedIp, refreshSoc]);

  // Scope-follow: when the user drills into a cluster or module on
  // the diagram, set the global agent scope to that IP's directory so
  // subsequent prompts in the chat panel are confined. Drilling back
  // to the SoC overview clears the scope.
  useEffect(() => {
    if (!isLive || !g.atlasData || typeof g.atlasData.setScopePath !== 'function') return;
    let scope = '';
    if (view.startsWith('cluster:')) {
      // Single-cluster live mode: cluster scope = whole project (no
      // narrowing). Skip setting scope so user gets full project access.
      scope = '';
    } else if (view.startsWith('module:')) {
      const ref = view.split(':')[1];
      const lkv = lookup[ref];
      if (lkv && lkv.module && lkv.module.ip_dir) scope = lkv.module.ip_dir;
    }
    // Avoid clobbering an unrelated scope set by the Workspace screen.
    // Only override when we're presenting an IP-specific view.
    if (scope && window.SCOPE_PATH !== scope) {
      g.atlasData.setScopePath(scope);
    } else if (!scope && view === 'soc' && window.SCOPE_PATH) {
      // Drilled back to overview → release the scope so subsequent
      // prompts can roam.
      g.atlasData.setScopePath('');
    }
  }, [view, isLive, lookup]);

  // Watch tool_result events on the live WS bridge. Anything that
  // touches a yaml/rtl/sim path under <ip>/ → schedule a debounced
  // /api/soc refresh so the diagram + grid pick up the change.
  useEffect(() => {
    if (!window.backend || typeof window.backend.subscribe !== 'function') return;
    const schedule = () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = setTimeout(() => { refreshSoc(); }, 500);
    };
    const unsubA = window.backend.subscribe('tool_result', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      const t = (m.text || '');
      // Only refresh when the tool result mentions a path that looks
      // like an SSOT mutation. Keeps unrelated tool calls (Read, grep)
      // from spamming the endpoint.
      if (/\.ssot\.yaml|\.sv\b|\bsim\/|\brtl\//.test(t)) schedule();
    });
    const unsubB = window.backend.subscribe('flush', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      schedule();
    });
    return () => {
      try { unsubA(); } catch (_) {}
      try { unsubB(); } catch (_) {}
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, [refreshSoc]);

  useEffect(() => {
    // When live data lands, jump to its first module if our current
    // selection doesn't exist there. Keep the top-level SoC overview
    // visible: it now renders live IP instances and real interconnects
    // instead of a mock-only cluster card layout.
    if (isLive) {
      if (!lookup[selMod]) setSelMod(firstRef);
    }
  }, [isLive, firstRef]); // eslint-disable-line

  // In live mode, `touchedSet` is populated by the tool_result watcher
  // above (modules that appear in /api/soc after they were absent before).
  // In mock mode, fall back to the bundled "agent just added periph_ss/spi"
  // demo selection so the design preview still shows the pulse animation.
  const agentTouched = isLive ? touchedSet : new Set(['periph_ss/spi']);
  const isTouched = (ref: any) => agentTouched.has(ref);
  const toggleLayer = (k: string) => setLayers(l => ({ ...l, [k]: !(l as any)[k] }));

  const allRows = [];
  for (const c of soc.clusters) {
    for (const m of c.modules) allRows.push({ ref: `${c.id}/${m.id}`, cluster: c, module: m });
  }
  const lk = lookup[selMod];
  const selModule = lk?.module;
  const selCluster = lk?.cluster;

  const crumb = (() => {
    const parts: Array<{ id: string; label: any; target: string; last?: boolean }> = [{ id: 'soc', label: soc.name || 'aurora_soc', target: 'soc' }];
    if (view.startsWith('cluster:')) {
      parts.push({ id: view.split(':')[1], label: view.split(':')[1], target: view, last: true });
    } else if (view.startsWith('module:')) {
      const ref = view.split(':')[1];
      const lkv = lookup[ref];
      if (lkv) {
        parts.push({ id: lkv.cluster.id, label: lkv.cluster.id, target: `cluster:${lkv.cluster.id}` });
        parts.push({ id: lkv.module.id, label: lkv.module.name, target: view, last: true });
      }
    } else { parts[0].last = true; }
    return parts;
  })();

  const filteredRows = (() => {
    if (view === 'soc') return allRows;
    if (view.startsWith('cluster:')) {
      const cid = view.split(':')[1];
      return allRows.filter(r => r.cluster.id === cid);
    }
    if (view.startsWith('module:')) {
      const ref = view.split(':')[1];
      return allRows.filter(r => r.ref === ref);
    }
    return allRows;
  })();

  // Run metadata for the status grid. Use only real sim_history from
  // /api/soc; missing data stays blank so the UI does not imply a
  // verification run that never happened.
  const runMeta = (mod: any) => {
    const hist = Array.isArray(mod.sim_history) ? mod.sim_history : [];
    const last = hist[hist.length - 1];
    if (last) {
      return {
        t: last.t || '—',
        cov: last.cov || '—',
        tests: last.tests || '—',
        dur: last.dur || '—',
      };
    }
    return { t: '—', cov: '—', tests: '—', dur: '—' };
  };
  const sparkBars = (mod: any) => {
    const hist = Array.isArray(mod.sim_history) ? mod.sim_history : [];
    if (hist.length) {
      // Map each run's duration (seconds, parsed from "4.2s") onto a 2-11
      // bar height. If duration is missing, derive height from status:
      // ok = tall, partial = mid, err = short, pending = stub.
      const dursS = hist.map((r: any) => {
        const v = parseFloat((r.dur || '').replace(/[^\d.]/g, ''));
        return isFinite(v) && v > 0 ? v : null;
      });
      const valid = dursS.filter((v: any) => v != null);
      const max = valid.length ? Math.max(...valid) : 1;
      return hist.map((r: any, i: any) => {
        if (dursS[i] != null) {
          return Math.round(2 + (dursS[i] / max) * 9);
        }
        return r.status === 'ok' ? 9 : r.status === 'partial' ? 6 : r.status === 'err' ? 3 : 2;
      });
    }
    return [];
  };

  // ── V7 diagram renderers ──────────────────────────────────────
  // The three render closures were lifted into ./soc-architect-diagrams (each
  // still UNCHANGED) so this file stays under 1000 lines. They read a fixed,
  // enumerable set of in-scope values, passed through a `ctx` bag at call time.
  const renderSocView = () => renderSocViewExt({
    soc, socTopMode, layout, layers, selMod, pendingPort,
    setPendingPort, setSelMod, setView, getStageScale, blockDragRef,
    refreshSoc, isTouched,
  });
  const renderClusterView = (cid: any) => renderClusterViewExt(cid, {
    soc, layout, layers, selMod, setSelMod, setView, setLayout,
    getStageScale, blockDragRef, persistLayout, isTouched,
    runningByIp, setDispatchMenu,
  });
  const renderModuleView = (ref: any) => renderModuleViewExt(ref, {
    lookup, layers,
  });

  const applyDiagramPlan = useCallback(async (promptText: any) => {
    const r = await fetch('/api/diagram/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: promptText, layout }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
    const plan = d.plan || {};
    const actions = Array.isArray(plan.actions) ? plan.actions : [];
    const refById: Record<string, any> = {};
    for (const c of soc.clusters || []) {
      for (const m of c.modules || []) refById[m.id] = `${c.id}/${m.id}`;
    }
    let nextLayout = { ...layout };
    let touchedLayout = false;
    const notes = [];
    for (const a of actions) {
      if (!a || typeof a !== 'object') continue;
      if (a.type === 'auto_layout') {
        nextLayout = Object.fromEntries(Object.entries(nextLayout).filter(([k]) => !k.startsWith('top:')));
        touchedLayout = true;
        notes.push('auto layout');
      } else if (a.type === 'move_block') {
        const id = String(a.id || a.ref || '').split('/').pop();
        const ref = refById[id as any];
        const x = Number(a.x), y = Number(a.y);
        if (ref && Number.isFinite(x) && Number.isFinite(y)) {
          nextLayout[`top:${ref}`] = {
            x: Math.max(0, Math.min(1080, x)),
            y: Math.max(0, Math.min(650, y)),
          };
          touchedLayout = true;
          notes.push(`move ${id}`);
        }
      } else if (a.type === 'connect_ports') {
        const rr = await fetch('/api/soc/connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ from: a.from, to: a.to, proto: a.proto || '' }),
        });
        const dd = await rr.json().catch(() => ({}));
        if (!rr.ok || dd.error) throw new Error(dd.error || `connect HTTP ${rr.status}`);
        notes.push(`connect ${a.from} -> ${a.to}`);
      } else if (a.type === 'add_instance') {
        const rr = await fetch('/api/soc/instance/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: a.model || a.name,
            id: a.id,
            cluster: a.cluster,
            x: a.x,
            y: a.y,
            addr: a.addr,
          }),
        });
        const dd = await rr.json().catch(() => ({}));
        if (!rr.ok || dd.error) throw new Error(dd.error || `add instance HTTP ${rr.status}`);
        notes.push(`add ${dd.instance?.id || a.id || a.model}`);
      } else if (a.type === 'delete_instance') {
        const id = String(a.id || a.instance || '').trim();
        if (!id) continue;
        if (!confirm(`Remove instance "${id}" from this SoC?\n\nModel files will stay in the available model catalog.`)) {
          notes.push(`skip delete ${id}`);
          continue;
        }
        const rr = await fetch('/api/soc/instance/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id }),
        });
        const dd = await rr.json().catch(() => ({}));
        if (!rr.ok || dd.error) throw new Error(dd.error || `delete instance HTTP ${rr.status}`);
        nextLayout = Object.fromEntries(Object.entries(nextLayout).filter(([k]) => !k.endsWith(`/${id}`)));
        touchedLayout = true;
        notes.push(`delete ${id}`);
      }
    }
    if (touchedLayout) {
      setLayout(nextLayout);
      persistLayout(nextLayout);
    }
    if (actions.some((a: any) => a && (a.type === 'connect_ports' || a.type === 'add_instance' || a.type === 'delete_instance'))) await refreshSoc();
    return {
      summary: plan.summary || 'diagram plan applied',
      count: actions.length,
      notes,
    };
  }, [layout, persistLayout, refreshSoc, soc]);

  const addCatalogInstance = useCallback(async (model: any) => {
    const roleCluster = model.kind === 'cpu' ? 'cpu_ss'
      : model.kind === 'bus' ? 'noc'
      : model.kind === 'mem' ? 'mem_ss'
      : 'periph_ss';
    const r = await fetch('/api/soc/instance/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model.name || model.id,
        cluster: roleCluster,
        x: model.kind === 'mem' ? 850 : model.kind === 'bus' ? 470 : 170,
        y: 560,
      }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || d.error) {
      alert(`add instance failed: ${d.error || `HTTP ${r.status}`}`);
      return;
    }
    await refreshSoc();
    setView('soc');
    if (d.instance && d.instance.id) {
      setSelMod(`${d.cluster}/${d.instance.id}`);
    }
  }, [refreshSoc]);

  const deleteInstance = useCallback(async (id: any) => {
    if (!id) return;
    if (!confirm(`Remove instance "${id}" from this SoC?\n\nModel files will be kept; only soc.ssot.yaml instance/members/connections are changed.`)) return;
    const r = await fetch('/api/soc/instance/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || d.error) {
      alert(`delete instance failed: ${d.error || `HTTP ${r.status}`}`);
      return;
    }
    const nextLayout = Object.fromEntries(Object.entries(layout).filter(([k]) => !k.endsWith(`/${id}`)));
    setLayout(nextLayout);
    persistLayout(nextLayout);
    await refreshSoc();
    setView('soc');
  }, [layout, persistLayout, refreshSoc]);


  // Landing: no IP selected → show the user's own IPs as a card grid (not the
  // diagram, and never the demo SoC). All hooks above have run, so this
  // early return is safe under the rules of hooks.
  if (!selectedIp) {
    return (
      <ArchitectMyIps
        ips={ipList}
        activeIp={props.activeIp}
        onOpen={(name) => {
          setSelectedIp(name);
          // Propagate to app-level activeIp so the header IP-picker and other
          // screens stay in sync. Optional — only fires when app.jsx wired it.
          if (typeof props.onSelectIp === 'function') props.onSelectIp(name);
        }}
      />
    );
  }

  return (
    <div className="arch-screen">
      {/* Run bar (scope · stage triggers · totals). Each stage button
          dispatches the matching backend workflow immediately. */}
      <div className="run-bar">
        <div className="grp">
          <button className="rb-btn" title="모든 IP 목록으로 돌아가기"
                  onClick={() => { setSelectedIp(''); setLive(null); }}>← All IPs</button>
        </div>
        <div className="grp">
          <button className="rb-btn primary"
                  disabled={!selModule}
                  title={selModule ? `run architect → post-STA pipeline on ${selModule.id}` : 'select a module first'}
                  onClick={() => dispatchPipeline(selModule && selModule.id)}>
            <span className="icn">▶</span> full pipeline
          </button>
          {window.PIPELINE_STAGES.map((s: any) => {
            const wfMap: Record<string, any> = {
              ssot: { wf: 'ssot-gen' },
              'fl-model': { wf: 'fl-model-gen', stage: 'fl-model' },
              'cl-model': { wf: 'fl-model-gen', stage: 'cl-model' },
              equivalence: { wf: 'fl-model-gen', stage: 'equivalence' },
              rtl: { wf: 'rtl-gen' },
              lint: { wf: 'lint' },
              tb: { wf: 'tb-gen' },
              sim: { wf: 'sim' },
              coverage: { wf: 'coverage' },
              'sim-debug': { wf: 'sim_debug' },
              syn: { wf: 'syn' },
              sta: { wf: 'sta' },
              pnr: { wf: 'pnr' },
              'sta-post': { wf: 'sta-post' },
              'goal-audit': { wf: 'sim_debug', stage: 'goal-audit' },
            };
            const cfg = wfMap[s] || {};
            const wf = cfg.wf || '';
            const onPipeClick = () => {
              if (!wf || !selModule) return;
              setRunning(s);
              setTimeout(() => setRunning(null), 1100);
              dispatchJob(wf, selModule.id, cfg.stage || s);
            };
            return (
              <button key={s}
                      className={`rb-btn ${s === 'sim' ? 'primary' : ''}`}
                      disabled={!wf || !selModule}
                      title={wf && selModule ? `dispatch ${wf} on ${selModule.id}` : 'select a module first'}
                      onClick={onPipeClick}
                      style={(!wf ? { opacity: 0.4, cursor: 'not-allowed' } : null) as React.CSSProperties | undefined}>
                <span className="icn">{running === s ? '◌' : '▶'}</span>{s}
              </button>
            );
          })}
        </div>
        <span className="rb-spacer" />
        <IpxactImportBtn onImported={() => refreshSoc()} />
        <span className="rb-meta">
          <span>modules · <b>{filteredRows.length}</b>{view !== 'soc' && <span style={{ color: 'var(--fg-mute)' }}> / {allRows.length}</span>}</span>
          <span>busses · <b>{(soc.busses || []).length}</b></span>
          <span style={{ color: 'var(--err)' }}>sim err · <b style={{ color: 'var(--err)' }}>{filteredRows.filter(r => r.module.status.sim === 'err').length}</b></span>
          <span style={{ color: 'var(--warn)' }}>partial · <b style={{ color: 'var(--warn)' }}>{filteredRows.filter(r => r.module.status.sim === 'partial').length}</b></span>
        </span>
      </div>

      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: diagramFocus ? '0 minmax(0,1fr) 0' : `${leftPanelW}px minmax(360px,1fr) ${rightPanelW}px`,
        overflow: 'hidden',
      }}>
        {/* LEFT — hierarchy tree (panel sub-tree lives in ./soc-architect-tree) */}
        {renderHierarchyPanel({
          diagramFocus, beginPanelResize, treeQuery, setTreeQuery, treeMatches,
          setSelMod, setView, soc, isTouched, view, deleteInstance, catalog,
          addCatalogInstance, dispatchJob, workspaceTree, selMod,
        })}

        {/* CENTER — tab bar + diagram or status */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'stretch', borderBottom: '1px solid var(--line)', background: 'var(--bg-2)' }}>
            <div style={{ display: 'flex' }}>
              {[
                { id: 'diagram', label: 'block diagram', icon: '◫' },
                { id: 'status',  label: 'status grid',  icon: '⊞' },
              ].map(t => (
                <button key={t.id}
                        onClick={() => setTab(t.id)}
                        className={`v8-tab ${tab === t.id ? 'sel' : ''}`}>
                  <span className="ic">{t.icon}</span>{t.label}
                </button>
              ))}
            </div>
            <div style={{ flex: 1, padding: '0 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="bd-crumb">
                {crumb.map((p, i) => (
                  <Fragment key={p.id}>
                    {i > 0 && <span className="sep">▸</span>}
                    <span className={`seg ${p.last ? 'last' : ''}`} onClick={() => !p.last && setView(p.target)}>{p.label}</span>
                  </Fragment>
                ))}
              </div>
              <span style={{ flex: 1 }} />
              {view === 'soc' && tab === 'diagram' && (
                <div className="seg-tabs" title="top diagram density">
                  <button className={socTopMode === 'if' ? 'sel' : ''}
                          onClick={() => setSocTopMode('if')}>I/F</button>
                  <button className={socTopMode === 'detail' ? 'sel' : ''}
                          onClick={() => setSocTopMode('detail')}>detail</button>
                </div>
              )}
              {tab === 'diagram' && (
                <button className="btn"
                        style={{ fontSize: 10.5, padding: '3px 9px' }}
                        title="toggle block-diagram focus view"
                        onClick={() => {
                          setDiagramFocus(v => !v);
                          setTimeout(fitZoom, 40);
                        }}>
                  {diagramFocus ? 'show panels' : 'focus diagram'}
                </button>
              )}
              {view !== 'soc' && (
                <button className="btn" style={{ fontSize: 10.5, padding: '3px 9px' }}
                        title="step up one level (module → cluster → soc)"
                        onClick={() => {
                          // Step up one level instead of jumping straight
                          // to soc, matching the breadcrumb depth.
                          if (view.startsWith('module:')) {
                            const ref = view.split(':')[1];
                            const lkv = lookup[ref];
                            if (lkv && lkv.cluster) setView(`cluster:${lkv.cluster.id}`);
                            else setView('soc');
                          } else {
                            setView('soc');
                          }
                        }}>↑ up</button>
              )}
            </div>
          </div>

          {renderDiagramCanvas({
            view, tab, soc, selMod, setSelMod, setView,
            zoom, setZoom, pan, setPan, panDragRef, bdCanvasRef, fitZoom,
            layers, toggleLayer, layout, setLayout, persistLayout, refreshSoc,
            isLive, miniOpen, setMiniOpen,
            renderSocView, renderClusterView, renderModuleView,
          })}

          {tab === 'status' && renderStatusGrid({
            filteredRows, selMod, setSelMod, setView, isTouched, runMeta, sparkBars,
            jobsByIp, setSparkPop, selModule, selCluster, soc,
          })}
        </div>

        {/* RIGHT — vertical stack: JobTracker (collapsible) + chat. */}
        <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden',
                      borderLeft: '1px solid var(--line)', background: 'var(--panel)',
                      position: 'relative',
                      visibility: diagramFocus ? 'hidden' : 'visible' }}>
          <div className="arch-splitter right"
               title="resize chat"
               onMouseDown={(e) => beginPanelResize('right', e)} />
          <JobTracker jobs={jobs}
                             onLoadSession={(session: any) => {
                               const sid = normalizeArchitectSession(session);
                               if (!sid) return;
                               window.dispatchEvent(new CustomEvent('atlas:load-session-history', {
                                 detail: { session: sid },
                               }));
                             }}
                             onLoadJobLog={(jobId: any, live: any) => {
                               if (!jobId) return;
                               window.dispatchEvent(new CustomEvent('atlas:load-job-log', {
                                 detail: { jobId, live: !!live },
                               }));
                             }}
                             onSelectIp={(ip: any) => {
                               const lk = lookup[Object.keys(lookup).find(k => lookup[k].module.id === ip) as any];
                               if (lk) {
                                 setSelMod(`${lk.cluster.id}/${ip}`);
                                 setView(`cluster:${lk.cluster.id}`);
                               }
                             }} />
          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <ArchitectChat view={view} selModule={selModule} selCluster={selCluster}
                                  onDiagramPlan={applyDiagramPlan} />
          </div>
        </div>
      </div>

      {/* Block ⚡ dispatch menu — popover anchored to the button. */}
      {renderDispatchMenu({ dispatchMenu, setDispatchMenu, dispatchPipeline, dispatchJob })}

      {/* Sparkline hover popover — full sim_history of the hovered IP.
          Position-fixed so it can spill out of the grid container. */}
      {renderSparkPopover({ sparkPop, lookup })}
    </div>
  );
}

// ── Transitional bridge so legacy app.jsx + soc-architect.jsx resolve it. ──
g.SocArchitect = SocArchitect;
