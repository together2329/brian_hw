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
// the irreducible SocArchitect root component (its three render closures —
// renderSocView / renderClusterView / renderModuleView — read dozens of
// in-scope variables and cannot be hoisted to sibling files without changing
// behavior, so the component is kept whole). The self-contained pieces were
// extracted into siblings:
//   - soc-architect-styles.tsx    (the injectStyles CSS side-effect)
//   - soc-architect-shared.tsx    (session + fetch/lookup helpers, EMPTY_SOC)
//   - soc-architect-pipeline.tsx  (PIPELINE_STAGES/LABEL, fullPipeline,
//                                   PipelineStrip, ModuleProgressPanel)
//   - soc-architect-panels.tsx    (ArchitectMyIps, IpxactImportBtn, JobTracker)
//   - soc-architect-chat.tsx      (ArchitectChat)
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
  _highlightMatch,
  _buildLookup,
  EMPTY_SOC,
} from './soc-architect-shared';
// soc-architect-pipeline.tsx + soc-architect-chat.tsx register their globals on
// window for THIS file to resolve at render time (matching the legacy
// window.* lookups). Imported for that side-effect; the components themselves
// are read through `g` below so resolution stays at render time.
import './soc-architect-pipeline';
import './soc-architect-chat';

const g = window as unknown as Record<string, any>;

// Cross-file components resolved at render time through window — exactly as the
// legacy `window.X` JSX did. PipelineStrip / ModuleProgressPanel / JobTracker /
// ArchitectChat / IpxactImportBtn are owned by this file's own .tsx siblings;
// StatusTrio is owned by another (still-legacy) file. Keeping them as window
// forward-refs avoids any import-ordering hazard and preserves behavior.
const PipelineStrip = (props: any): any => g.PipelineStrip(props);
const ModuleProgressPanel = (props: any): any => g.ModuleProgressPanel(props);
const StatusTrio = (props: any): any => g.StatusTrio(props);
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
  const renderSocView = () => {
    const W = 1180, H = 720;
    const modules: any[] = [];
    for (const c of soc.clusters || []) {
      for (const m of c.modules || []) modules.push({ cluster: c, module: m, ref: `${c.id}/${m.id}` });
    }
    const findRow = (id: any) => modules.find(r => r.module.id === id);
    const isAux = (it: any) => {
      const p = (it.proto || '').toUpperCase();
      return p === 'CLK' || p === 'RST';
    };
    const sizeOf = (m: any) => {
      const visible = (m.interfaces || []).filter((it: any) => socTopMode === 'detail' || !isAux(it));
      const n = Math.max(2, Math.min(5, visible.length));
      return { w: 236, h: Math.max(112, 50 + n * 20) };
    };
    const positions: Record<string, any> = {};
    const put = (id: any, x: any, y: any) => {
      const row = findRow(id); if (!row) return;
      const s = sizeOf(row.module);
      // Top SoC has its own layout namespace. Cluster-local saved
      // positions can be useful inside a cluster view but make the
      // full-chip diagram collapse when the same x/y are reused here.
      const ov = layout && (layout as any)[`top:${row.ref}`];
      const hasOv = ov && typeof ov.x === 'number' && typeof ov.y === 'number';
      const hasSaved = typeof row.module.savedTopX === 'number' && typeof row.module.savedTopY === 'number';
      positions[id] = {
        x: hasOv ? ov.x : hasSaved ? row.module.savedTopX : x,
        y: hasOv ? ov.y : hasSaved ? row.module.savedTopY : y,
        w: s.w, h: s.h,
      };
    };
    // Prefer the familiar Carbon-style SoC placement when these IPs
    // exist; fall back to kind/role based columns for other projects.
    put('cortexa15_0', 74, 92);
    put('cci550',      468, 210);
    put('ddr_phy',     846, 92);
    put('spi_master',  170, 468);
    put('gic_400',     846, 438);
    put('uart_lite',   846, 592);
    let yCpu = 80, yBus = 220, yMem = 88, yPer = 430, yMisc = 560;
    for (const r of modules) {
      if (positions[r.module.id]) continue;
      const role = (r.cluster.role || '').toUpperCase();
      const kind = r.module.kind || '';
      if (role === 'CPU' || kind === 'cpu') { put(r.module.id, 72, yCpu); yCpu += 164; }
      else if (role === 'BUS' || kind === 'bus') { put(r.module.id, 470, yBus); yBus += 168; }
      else if (role === 'MEM' || kind === 'mem') { put(r.module.id, 850, yMem); yMem += 164; }
      else if (role === 'PERIPH' || kind === 'periph') { put(r.module.id, 164, yPer); yPer += 150; }
      else { put(r.module.id, 850, yMisc); yMisc += 140; }
    }
    const ifaceSide = (iface: any) => {
      const side = (iface.side || '').toLowerCase();
      const role = (iface.role || 'slave').toLowerCase();
      const proto = (iface.proto || '').toUpperCase();
      if (proto === 'CLK' || proto === 'RST') return 'left';
      if (side === 'top' || side === 'bottom' || side === 'left' || side === 'right') return side;
      return role === 'master' ? 'right' : 'left';
    };
    const sideList = (m: any, side: any) => (m.interfaces || [])
      .filter((it: any) => socTopMode === 'detail' || !isAux(it))
      .filter((it: any) => ifaceSide(it) === side)
      .slice(0, 5);
    const pinPoint = (m: any, ifaceName: any, preferSide: any) => {
      const p = positions[m.id]; if (!p) return null;
      const iface = (m.interfaces || []).find((it: any) => it.name === ifaceName) || {};
      const side = preferSide || ifaceSide(iface);
      const list = sideList(m, side);
      const idx = Math.max(0, list.findIndex((it: any) => it.name === ifaceName));
      const t = (idx + 1) / (Math.max(1, list.length) + 1);
      const topPorts = sideList(m, 'top');
      const bottomPorts = sideList(m, 'bottom');
      const headerH = 24;
      const topH = topPorts.length ? 18 : 0;
      const bottomH = bottomPorts.length ? 18 : 0;
      if (side === 'top') return { x: p.x + p.w * t, y: p.y + headerH + 1, side };
      if (side === 'bottom') return { x: p.x + p.w * t, y: p.y + p.h - bottomH - 1, side };

      // The visible left/right port rows are not distributed across the
      // whole block: CSS centers the port column inside the body area.
      // Mirror that geometry so wires terminate at the row, not above or
      // below the label.
      const bodyY = p.y + headerH + topH;
      const bodyH = Math.max(1, p.h - headerH - topH - bottomH);
      const rowH = 13;
      const gap = 3;
      const n = Math.max(1, list.length);
      const stackH = n * rowH + (n - 1) * gap;
      const firstY = bodyY + (bodyH - stackH) / 2 + rowH / 2;
      const y = firstY + Math.max(0, idx) * (rowH + gap);
      if (side === 'right') return { x: p.x + p.w + 3, y, side };
      return { x: p.x - 3, y, side: 'left' };
    };
    const protoColor = (proto: any) => {
      const p = (proto || '').toUpperCase();
      if (p === 'ACE' || p === 'AXI' || p === 'AXI4' || p === 'AXI4L') return 'var(--accent)';
      if (p === 'APB' || p === 'AHB') return 'var(--magenta)';
      if (p === 'IRQ') return 'var(--warn)';
      return 'var(--cyan)';
    };
    const connections = [];
    if (layers.busses) {
      for (const bus of (soc.busses || soc.connections || [])) {
        if (!bus.from || !bus.to) continue;
        const [aId, aIf] = String(bus.from).split('/');
        const [bId, bIf] = String(bus.to).split('/');
        const a = findRow(aId)?.module, b = findRow(bId)?.module;
        if (!a || !b) continue;
        const p1 = pinPoint(a, aIf, 'right');
        const p2 = pinPoint(b, bIf, 'left');
        if (!p1 || !p2) continue;
        connections.push({ id: `${bus.from}->${bus.to}`, from: bus.from, to: bus.to,
                           proto: bus.proto || '', color: protoColor(bus.proto), p1, p2 });
      }
    }
    const familyClass = (proto: any) => {
      const x = (proto || '').toUpperCase();
      if (x === 'AXI' || x === 'AXI4') return 'proto-axi';
      if (x === 'AXI4L') return 'proto-axil';
      if (x === 'ACE') return 'proto-ace';
      if (x === 'APB') return 'proto-apb';
      if (x === 'IRQ') return 'proto-irq';
      if (x === 'CLK') return 'proto-clk';
      if (x === 'RST') return 'proto-rst';
      return '';
    };
    const arrowFor = (iface: any) => {
      const role = (iface.role || 'slave').toLowerCase();
      const proto = (iface.proto || '').toUpperCase();
      if (proto === 'IRQ') return '↯';
      if (proto === 'CLK' || proto === 'RST') return '►';
      return role === 'master' ? '►' : '◄';
    };
    const connectPort = async (row: any, iface: any, e: any) => {
      e.stopPropagation();
      const port = {
        ip: row.module.id,
        iface: iface.name,
        proto: (iface.proto || '').toUpperCase(),
        role: (iface.role || '').toLowerCase(),
      };
      if (!pendingPort) {
        setPendingPort(port);
        return;
      }
      if (pendingPort.ip === port.ip && pendingPort.iface === port.iface) {
        setPendingPort(null);
        return;
      }
      const pendingIsMaster = pendingPort.role === 'master';
      const thisIsMaster = port.role === 'master';
      const src = pendingIsMaster || !thisIsMaster ? pendingPort : port;
      const dst = src === pendingPort ? port : pendingPort;
      try {
        const r = await fetch('/api/soc/connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: `${src.ip}/${src.iface}`,
            to: `${dst.ip}/${dst.iface}`,
            proto: src.proto || dst.proto,
          }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
        setPendingPort(null);
        refreshSoc();
      } catch (err: any) {
        alert(`connect failed: ${err.message || err}`);
      }
    };
    const beginBlockDrag = (ref: any, layoutKey: any, p: any, e: any, maxX: any, maxY: any) => {
      if (e.button !== 0) return;
      if (e.target.closest && e.target.closest('.bd-port')) return;
      e.stopPropagation();
      document.body.style.cursor = 'grabbing';
      document.body.style.userSelect = 'none';
      blockDragRef.current = {
        ref,
        layoutKey,
        scale: getStageScale(e, W),
        dragged: false,
        startX: e.clientX,
        startY: e.clientY,
        baseX: p.x,
        baseY: p.y,
        maxX,
        maxY,
        latestLayout: null,
        globalDrag: true,
      };
    };
    const portClass = (m: any, it: any, side: any) => {
      const active = pendingPort && pendingPort.ip === m.id && pendingPort.iface === it.name;
      return `bd-port ${side}-side ${familyClass(it.proto)} ${active ? 'connecting' : ''}`;
    };
    const protoBadge = (it: any) => {
      const p = (it.proto || '').toUpperCase();
      if (!p || p === 'CLK' || p === 'RST') return null;
      return <span className="proto-badge">{p}</span>;
    };
    return (
      <Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          <defs>
            <marker id="soc-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M0,0 L8,4 L0,8 z" fill="currentColor" />
            </marker>
          </defs>
          {connections.map(co => {
            const midX = (co.p1.x + co.p2.x) / 2;
            const points = `${co.p1.x},${co.p1.y} ${midX},${co.p1.y} ${midX},${co.p2.y} ${co.p2.x},${co.p2.y}`;
            return (
              <g key={co.id} style={{ color: co.color }}>
                <polyline points={points} stroke={co.color} strokeWidth="3.2" fill="none"
                          strokeLinejoin="round" strokeLinecap="square" markerEnd="url(#soc-arrow)" />
                <circle cx={co.p1.x} cy={co.p1.y} r="3.2" fill={co.color} />
                <circle cx={co.p2.x} cy={co.p2.y} r="3.2" fill={co.color} />
                {layers.labels && (
                  <g>
                    <rect x={midX - 20} y={(co.p1.y + co.p2.y)/2 - 8} width="40" height="15"
                          className="soc-wire-label" fill="var(--bg)" stroke={co.color} strokeWidth="0.8" />
                    <text x={midX} y={(co.p1.y + co.p2.y)/2} textAnchor="middle"
                          dominantBaseline="middle" fill={co.color} fontSize="10"
                          fontFamily="var(--mono)">{co.proto}</text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
        {modules.map(({ cluster: c, module: m, ref }) => {
          const p = positions[m.id]; if (!p) return null;
          const sel = selMod === ref;
          const touched = isTouched(ref);
          const left = sideList(m, 'left');
          const right = sideList(m, 'right');
          const top = sideList(m, 'top');
          const bottom = sideList(m, 'bottom');
          return (
            <div key={ref} className={`bd-block with-ports soc-top ${m.kind || ''} ${sel ? 'sel' : ''} ${touched ? 'touched' : ''}`}
                 style={{ left: p.x, top: p.y, width: p.w, height: p.h }}
                 onClick={(e) => {
                   if (blockDragRef.current && blockDragRef.current.ref === ref && blockDragRef.current.dragged) return;
                   e.stopPropagation(); setSelMod(ref);
                 }}
                 onDoubleClick={() => {
                   if (blockDragRef.current && blockDragRef.current.ref === ref && blockDragRef.current.dragged) return;
                   setView(`module:${ref}`);
                 }}
                 onMouseDown={(e) => beginBlockDrag(ref, `top:${ref}`, p, e, W - p.w, H - p.h)}>
              <div className="bd-block-head"
                   title="drag block · click ports to connect · double-click to inspect"
                   style={{ cursor: 'grab' }}
                   onMouseDown={(e) => beginBlockDrag(ref, `top:${ref}`, p, e, W - p.w, H - p.h)}>
                <span className="nm-instance">{m.name || m.id}</span>
                <span className="nm-type">({c.id})</span>
                <span style={{ flex: 1 }} />
                {socTopMode === 'detail' && m.addr && <span style={{ fontSize: 9, color: 'var(--cyan)', fontFamily: 'var(--mono)' }}>{m.addr}</span>}
              </div>
              {top.length > 0 && <div className="bd-ports-edge top">{top.map((it: any, i: any) => (
                <span key={i} className={portClass(m, it, 'top')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}><span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}</span>
              ))}</div>}
              <div className="bd-ports">
                <div className="bd-ports-col left">
                  {left.map((it: any, i: any) => (
                    <span key={i} className={portClass(m, it, 'left')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}>
                      <span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}
                    </span>
                  ))}
                </div>
                <div className="bd-center-icon" aria-hidden="true" />
                <div className="bd-ports-col right">
                  {right.map((it: any, i: any) => (
                    <span key={i} className={portClass(m, it, 'right')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}>
                      {protoBadge(it)}<span className="nm">{it.name}</span><span className="arr">{arrowFor(it)}</span>
                    </span>
                  ))}
                </div>
              </div>
              {bottom.length > 0 && <div className="bd-ports-edge bottom">{bottom.map((it: any, i: any) => (
                <span key={i} className={portClass(m, it, 'bottom')} onClick={(e) => connectPort({ cluster: c, module: m, ref }, it, e)}><span className="arr">{arrowFor(it)}</span><span className="nm">{it.name}</span>{protoBadge(it)}</span>
              ))}</div>}
            </div>
          );
        })}
      </Fragment>
    );
  };

  // Carbon SoC-Designer-style cluster view: each module shows its
  // ports as labeled rows on the left + right edges with a center
  // type icon. Connections route pin-to-pin when the cluster has bus
  // info; otherwise we just show the blocks with their interfaces.
  const renderClusterView = (cid: any) => {
    const c = soc.clusters.find((c: any) => c.id === cid); if (!c) return null;
    const W = 1180, H = 720;

    // Per-module port partition: left side = slave + clk + rst,
    // right side = master, top/bottom honoured when explicitly set
    // (typical for IRQ in/out which Carbon-style diagrams place on
    // the top edge). Cap at 5 ports per side so the block doesn't
    // grow taller than its column gap.
    const partition = (m: any) => {
      const ifs = (m.interfaces || []);
      const left: any[] = []; const right: any[] = []; const top: any[] = []; const bottom: any[] = [];
      for (const it of ifs) {
        const side = (it.side || '').toLowerCase();
        const role = (it.role || 'slave').toLowerCase();
        const proto = (it.proto || '').toUpperCase();
        // CLK/RST always go on the left (input pins).
        if (proto === 'CLK' || proto === 'RST') { left.push(it); continue; }
        // Honour explicit `side` first.
        if (side === 'top')         top.push(it);
        else if (side === 'bottom') bottom.push(it);
        else if (side === 'left')   left.push(it);
        else if (side === 'right')  right.push(it);
        // No explicit side: role-based.
        else if (role === 'master') right.push(it);
        else                        left.push(it);
      }
      return {
        left:   left.slice(0, 5),
        right:  right.slice(0, 5),
        top:    top.slice(0, 4),
        bottom: bottom.slice(0, 4),
      };
    };

    // Block size: header (24) + body padded for max(left,right) rows
    // at ~14px each + safe minimum. Top/bottom ports add fixed margins.
    const sizeOf = (m: any) => {
      const { left, right, top, bottom } = partition(m);
      const rows = Math.max(left.length, right.length, 2);
      const headerH = 24;
      const bodyH   = Math.max(76, rows * 14 + 24);
      const topPad    = top.length    ? 18 : 0;
      const bottomPad = bottom.length ? 18 : 0;
      return { w: 220, h: headerH + bodyH + topPad + bottomPad,
               topPad, bottomPad };
    };

    const cols = Math.min(3, c.modules.length);
    const rowsN = Math.ceil(c.modules.length / cols);
    const sizes = c.modules.map(sizeOf);
    const blockW = 220;
    const maxBlockH = Math.max(140, ...sizes.map((s: any) => s.h));
    const gapX = Math.max(40, (W - cols * blockW) / (cols + 1));
    const gapY = Math.max(40, (H - rowsN * maxBlockH - 60) / (rowsN + 1));
    const positions: Record<string, any> = {};
    c.modules.forEach((m: any, i: any) => {
      const ref = `${c.id}/${m.id}`;
      const col = i % cols, rIdx = Math.floor(i / cols);
      // Position precedence (most-local first):
      //   1. layout[ref] from localStorage (user-dragged, not yet saved)
      //   2. m.savedX/savedY from soc.ssot.yaml (saved layout)
      //   3. auto-grid fallback
      const ov = layout && layout[ref];
      const hasOv = ov && typeof ov.x === 'number';
      const hasSaved = typeof m.savedX === 'number';
      positions[m.id] = {
        x: hasOv  ? ov.x
          : hasSaved ? m.savedX
          : gapX + col * (blockW + gapX),
        y: hasOv  ? ov.y
          : hasSaved ? m.savedY
          : 40 + gapY + rIdx * (maxBlockH + gapY),
        w: blockW,
        h: sizes[i].h,
      };
    });

    // Cluster colour cue — drives the optional rail when no per-bus
    // data is available.
    const railColor = c.id === 'cpu_ss' ? 'var(--accent)'
                    : c.id === 'mem_ss' ? 'var(--cyan)'
                    : c.id === 'periph_ss' ? 'var(--magenta)'
                    : c.id === 'noc' ? 'var(--magenta)'
                    : c.id === 'ips' ? 'var(--accent)'
                    : 'var(--warn)';

    // Pin-to-pin connection lines. For each module, walk left ports
    // and try to find a matching right-side port on another module
    // with the same proto family — heuristic, but enough to draw
    // realistic lines until proper bus info lands.
    const protoFamily = (p: any) => {
      const x = (p || '').toUpperCase();
      if (x === 'AXI' || x === 'AXI4' || x === 'AXI4L' || x === 'ACE' || x === 'AXIS') return 'axi';
      if (x === 'APB' || x === 'AHB') return 'apb';
      if (x === 'IRQ') return 'irq';
      return null;
    };
    const connections: any[] = [];
    if (layers.busses) {
      for (const m of c.modules) {
        const partA = partition(m);
        const headerH = 24;
        // For each master (right) on this module, try to find a
        // matching slave (left) on any other module with same family.
        partA.right.forEach((iface: any, i: any) => {
          const fam = protoFamily(iface.proto);
          if (!fam) return;
          for (const n of c.modules) {
            if (n.id === m.id) continue;
            const partB = partition(n);
            const j = partB.left.findIndex((x: any) => protoFamily(x.proto) === fam);
            if (j === -1) continue;
            const pa = positions[m.id], pb = positions[n.id];
            const rowsA = Math.max(partA.left.length, partA.right.length, 2);
            const rowsB = Math.max(partB.left.length, partB.right.length, 2);
            const stepA = (pa.h - headerH - 12) / Math.max(rowsA, 1);
            const stepB = (pb.h - headerH - 12) / Math.max(rowsB, 1);
            const x1 = pa.x + pa.w + 3, y1 = pa.y + headerH + 6 + stepA * (i + 0.5);
            const x2 = pb.x - 3,        y2 = pb.y + headerH + 6 + stepB * (j + 0.5);
            const color = fam === 'axi' ? 'var(--accent)'
                        : fam === 'apb' ? 'var(--magenta)'
                        : fam === 'irq' ? 'var(--warn)'
                        : 'var(--cyan)';
              connections.push({ id: `${m.id}-${iface.name}-${n.id}`, x1, y1, x2, y2, color,
                                proto: iface.proto || '' });
            break; // 1 master ↔ 1 slave per family per module pair
          }
        });
      }
    }

    // Cross-cluster stubs — when soc.busses (from /api/soc) names a
    // connection whose ONE end is inside this cluster but the other is
    // in a different cluster, emit a small chip on the local block's
    // matching edge: "→ <other_cluster>/<other_inst>/<other_iface>".
    const stubs: any[] = [];
    const ipToCluster: Record<string, any> = {};
    for (const cc of soc.clusters) for (const mm of cc.modules) ipToCluster[mm.id] = cc.id;
    const localIds = new Set(c.modules.map((x: any) => x.id));
    const allBusses = (soc && Array.isArray(soc.busses)) ? soc.busses : [];
    const stubColorClass = (proto: any) => {
      const x = (proto || '').toUpperCase();
      if (x === 'AXI' || x === 'AXI4' || x === 'AXI4L' || x === 'ACE') return 'acc';
      if (x === 'APB' || x === 'AHB') return 'magenta';
      if (x === 'IRQ') return 'warn';
      if (x === 'AXIS') return 'cyan';
      return '';
    };
    for (const cn of allBusses) {
      if (!cn || !cn.from || !cn.to) continue;
      const [aInst, aIface] = String(cn.from).split('/');
      const [bInst, bIface] = String(cn.to).split('/');
      const aLocal = localIds.has(aInst);
      const bLocal = localIds.has(bInst);
      if (aLocal === bLocal) continue; // both local → real wire above; both remote → not our problem
      const localInst  = aLocal ? aInst  : bInst;
      const localIface = aLocal ? aIface : bIface;
      const remoteInst = aLocal ? bInst  : aInst;
      const remoteIface= aLocal ? bIface : aIface;
      const remoteCluster = ipToCluster[remoteInst] || '?';
      const isOutgoing = aLocal; // local end is the master/from
      const part = partition(c.modules.find((x: any) => x.id === localInst) || {});
      const pos = positions[localInst]; if (!pos) continue;
      const headerH = 24;
      // Try to find the matching iface row inside left/right partition
      const idxR = part.right.findIndex((x: any) => x.name === localIface);
      const idxL = part.left.findIndex((x: any) => x.name === localIface);
      const onRight = idxR >= 0 || (idxL < 0 && isOutgoing);
      const rows = Math.max(part.left.length, part.right.length, 2);
      const step = (pos.h - headerH - 12) / Math.max(rows, 1);
      const idx = onRight ? Math.max(idxR, 0) : Math.max(idxL, 0);
      const yPin = pos.y + headerH + 6 + step * (idx + 0.5);
      stubs.push({
        id: `stub-${localInst}-${localIface}-${remoteInst}-${remoteIface}`,
        x: onRight ? pos.x + pos.w + 6 : pos.x - 6,
        y: yPin,
        anchor: onRight ? 'left' : 'right',     // CSS positioning
        label: `${isOutgoing ? '→' : '←'} ${remoteCluster}/${remoteInst}/${remoteIface}`,
        proto: cn.proto || '',
      });
    }

    return (
      <Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {connections.length === 0 && layers.busses && (
            <>
              <line x1={60} y1={H/2} x2={W-60} y2={H/2} stroke={railColor} strokeWidth="3" opacity="0.4" />
              {c.modules.map((m: any) => {
                const p = positions[m.id];
                return <line key={m.id} x1={p.x + p.w/2} y1={p.y + p.h/2} x2={p.x + p.w/2} y2={H/2} stroke={railColor} strokeWidth="1" opacity="0.3" strokeDasharray="3,3" />;
              })}
              {layers.labels && (
                <text x={70} y={H/2 - 6} fill="var(--fg-mute)" fontSize="10" fontFamily="var(--mono)" letterSpacing="0.1em">
                  no bus info — heuristic fallback
                </text>
              )}
            </>
          )}
          {/* Pin-to-pin orthogonal lines: H — V — H, with a small
              proto label hovering at the midpoint. */}
          {connections.map(co => {
            const midX = (co.x1 + co.x2) / 2;
            const midY = (co.y1 + co.y2) / 2;
            return (
              <g key={co.id}>
                <polyline
                  points={`${co.x1},${co.y1} ${midX},${co.y1} ${midX},${co.y2} ${co.x2},${co.y2}`}
                  stroke={co.color} strokeWidth="1.6" fill="none" opacity="0.85" />
                <circle cx={co.x1} cy={co.y1} r="2.5" fill={co.color} />
                <circle cx={co.x2} cy={co.y2} r="2.5" fill={co.color} />
                {layers.labels && co.proto && (
                  <g>
                    <rect x={midX - 14} y={midY - 7} width={28} height={12}
                          fill="var(--bg-2)" stroke={co.color} strokeWidth="0.5" opacity="0.9" />
                    <text x={midX} y={midY + 1} textAnchor="middle"
                          fill={co.color} fontSize="9" fontFamily="var(--mono)"
                          dominantBaseline="middle">{co.proto}</text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>

        {c.modules.map((m: any) => {
          const p = positions[m.id];
          const ref = `${c.id}/${m.id}`;
          const sel = selMod === ref;
          const touched = isTouched(ref);
          const { left, right, top, bottom } = partition(m);
          const familyClass = (proto: any) => {
            const x = (proto || '').toUpperCase();
            if (x === 'AXI' || x === 'AXI4') return 'proto-axi';
            if (x === 'AXI4L') return 'proto-axil';
            if (x === 'ACE') return 'proto-ace';
            if (x === 'AXIS') return 'proto-axis';
            if (x === 'APB') return 'proto-apb';
            if (x === 'AHB') return 'proto-ahb';
            if (x === 'IRQ') return 'proto-irq';
            if (x === 'CLK') return 'proto-clk';
            if (x === 'RST') return 'proto-rst';
            return '';
          };
          const arrowFor = (iface: any) => {
            const role = (iface.role || 'slave').toLowerCase();
            const proto = (iface.proto || '').toUpperCase();
            if (proto === 'CLK' || proto === 'RST') return '►'; // input
            if (proto === 'IRQ') return role === 'master' ? '↯' : '↯';
            return role === 'master' ? '►' : '◄';
          };
          // Carbon-style instance name: "<name>[0]"  with type in parens.
          const instLabel = `${m.name || m.id}[0]`;
          const typeLabel = m.label && m.label !== m.name ? `(${m.label})` :
                            m.kind ? `(${(g.MOD_KIND_LABEL || {})[m.kind] || m.kind})` : '';
          const centerGlyph = (g.MOD_ICON || {})[m.kind] || 'C';
          return (
            <div key={m.id} className={`bd-block with-ports ${m.kind || ''} ${sel ? 'sel' : ''} ${touched ? 'touched' : ''} ${runningByIp[m.id] ? 'job-running' : ''}`}
                 style={{ left: p.x, top: p.y, width: p.w, height: p.h }}
                 onClick={(e) => {
                   // Skip if this was the end of a drag — block-head's
                   // mouseup already handles the drag-stop, but a click
                   // on body still selects.
                   if (blockDragRef.current && blockDragRef.current.dragged) return;
                   e.stopPropagation(); setSelMod(ref);
                 }}
                 onDoubleClick={() => setView(`module:${ref}`)}>
              <div className="bd-block-head"
                   title="drag to move · double-click to drill in"
                   style={{ cursor: 'grab' }}
                   onMouseDown={(e) => {
                     // Start a block drag. We store the screen-space start
                     // and the block's stage-space base so mousemove can
                     // compute a delta divided by the current zoom scale.
                     // (Pan doesn't enter the math because pan is a
                     // sibling translate that affects screen coords by
                     // the same amount on both endpoints.)
                     e.stopPropagation();
                     const scale = getStageScale(e, W);
                     blockDragRef.current = {
                       ref, scale, dragged: false,
                       startX: e.clientX, startY: e.clientY,
                       baseX: p.x, baseY: p.y,
                     };
                     e.currentTarget.style.cursor = 'grabbing';
                   }}
                   onMouseMove={(e) => {
                     const d = blockDragRef.current;
                     if (!d || d.ref !== ref) return;
                     const dx = (e.clientX - d.startX) / d.scale;
                     const dy = (e.clientY - d.startY) / d.scale;
                     if (Math.abs(dx) + Math.abs(dy) < 2) return; // dead zone
                     d.dragged = true;
                     setLayout(prev => ({ ...prev, [ref]: {
                       x: Math.max(0, Math.min(W - 60, d.baseX + dx)),
                       y: Math.max(0, Math.min(H - 30, d.baseY + dy)),
                     }}));
                   }}
                   onMouseUp={(e) => {
                     const d = blockDragRef.current;
                     if (!d || d.ref !== ref) return;
                     e.currentTarget.style.cursor = 'grab';
                     // Persist the new layout (only if user actually
                     // moved — pure click stays a click).
                     if (d.dragged) {
                       setLayout(prev => { persistLayout(prev); return prev; });
                     }
                     // Clear after the click handler sees `dragged`.
                     setTimeout(() => { blockDragRef.current = null; }, 0);
                   }}
                   onMouseLeave={(e) => {
                     // If the mouse leaves the head while dragging, stop
                     // — the canvas-level mouseup would clear it anyway,
                     // but this avoids a stuck grabbing cursor.
                     e.currentTarget.style.cursor = 'grab';
                   }}>
                <span className="nm-instance">{instLabel}</span>
                <span className="nm-type">{typeLabel}</span>
                <span style={{ flex: 1 }} />
                {touched && <span className="add-badge">+</span>}
                {m.status.sim === 'err' && <span style={{ color: 'var(--err)', fontSize: 11 }}>✗</span>}
                {/* Running-job ring marker */}
                {runningByIp[m.id] && (
                  <span className="bd-running-pill"
                        title={`${runningByIp[m.id].workflow} · iter ${runningByIp[m.id].iterations}`}>
                    ◌ {runningByIp[m.id].workflow}
                  </span>
                )}
                {m.addr && <span style={{ fontSize: 9, color: 'var(--cyan)', fontFamily: 'var(--mono)' }}>{m.addr.split(' ')[0] || ''}</span>}
                {/* ⚡ dispatch button — opens menu to run workflows on
                    this IP via an HTTP worker. */}
                <button className="bd-dispatch-btn"
                        title="dispatch a workflow on this IP"
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={(e) => {
                          e.stopPropagation();
                          const r = e.currentTarget.getBoundingClientRect();
                          setDispatchMenu({
                            ip: m.id,
                            x: r.right + 4, y: r.top,
                          });
                        }}>⚡</button>
              </div>
              {top.length > 0 && (
                <div className="bd-ports-edge top">
                  {top.map((iface, k) => (
                    <span key={`T${k}`} className={`bd-port top-side ${familyClass(iface.proto)}`}
                          title={`${iface.name} · ${iface.proto || ''} ${iface.role || ''}`}>
                      <span className="arr">{arrowFor(iface)}</span>
                      <span className="nm">{iface.name}</span>
                    </span>
                  ))}
                </div>
              )}
              <div className="bd-ports">
                <div className="bd-ports-col left">
                  {left.map((iface, k) => (
                    <span key={`L${k}`} className={`bd-port left-side ${familyClass(iface.proto)}`}>
                      <span className="arr">{arrowFor(iface)}</span>
                      <span className="nm">{iface.name}{iface.proto && iface.proto !== 'CLK' && iface.proto !== 'RST' ? ` ${(iface.role || '').slice(0,1).toUpperCase()}` : ''}</span>
                    </span>
                  ))}
                </div>
                <div className="bd-center-icon">{centerGlyph}</div>
                <div className="bd-ports-col right">
                  {right.map((iface, k) => (
                    <span key={`R${k}`} className={`bd-port right-side ${familyClass(iface.proto)}`}>
                      <span className="nm">{iface.name}{iface.proto ? ` ${(iface.role || '').slice(0,1).toUpperCase()}` : ''}</span>
                      <span className="arr">{arrowFor(iface)}</span>
                    </span>
                  ))}
                </div>
              </div>
              {bottom.length > 0 && (
                <div className="bd-ports-edge bottom">
                  {bottom.map((iface, k) => (
                    <span key={`B${k}`} className={`bd-port bottom-side ${familyClass(iface.proto)}`}
                          title={`${iface.name} · ${iface.proto || ''} ${iface.role || ''}`}>
                      <span className="arr">{arrowFor(iface)}</span>
                      <span className="nm">{iface.name}</span>
                    </span>
                  ))}
                </div>
              )}
              {layers.clk && <span className="clk-in-marker">▶ clk-in</span>}
            </div>
          );
        })}
        {stubs.map(st => (
          <div key={st.id} className={`bd-stub ${stubColorClass(st.proto)}`}
               style={{
                 left: st.anchor === 'left' ? st.x : undefined,
                 right: st.anchor === 'right' ? (W - st.x) : undefined,
                 top: st.y - 8,
                 transform: st.anchor === 'right' ? 'translateX(0)' : undefined,
               }}>
            {st.label}{st.proto && <span style={{ opacity: 0.7 }}> · {st.proto}</span>}
          </div>
        ))}
      </Fragment>
    );
  };

  const renderModuleView = (ref: any) => {
    const lkm = lookup[ref]; if (!lkm) return null;
    const m = lkm.module;
    const W = 1180, H = 720;
    const blockW = 480, blockH = 320;
    const bx = (W - blockW) / 2, by = (H - blockH) / 2;
    const ifaces = m.interfaces || [];
    return (
      <Fragment>
        <svg className="bd-svg-layer" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {layers.busses && ifaces.map((iface: any) => {
            const sameSide = ifaces.filter((x: any) => x.side === iface.side);
            const idx = sameSide.indexOf(iface);
            const t = (idx + 1) / (sameSide.length + 1);
            let x1, y1, x2, y2;
            if (iface.side === 'left')         { x1 = bx - 80;        y1 = by + blockH * t; x2 = bx;             y2 = y1; }
            else if (iface.side === 'right')   { x1 = bx + blockW + 80; y1 = by + blockH * t; x2 = bx + blockW; y2 = y1; }
            else if (iface.side === 'top')     { x1 = bx + blockW * t; y1 = by - 80;          x2 = x1;          y2 = by; }
            else                                { x1 = bx + blockW * t; y1 = by + blockH + 80; x2 = x1;          y2 = by + blockH; }
            // Stroke color matches the cluster-view port-arrow palette:
            // AXI/ACE/AXI4L → blue accent, APB/AHB → magenta,
            // AXIS → cyan, IRQ → amber, CLK/RST → green.
            const _p = (iface.proto || '').toUpperCase();
            const color =
              (_p === 'AXI' || _p === 'AXI4' || _p === 'AXI4L' || _p === 'ACE') ? 'var(--accent)'
              : (_p === 'APB' || _p === 'AHB') ? 'var(--magenta)'
              : (_p === 'AXIS') ? 'var(--cyan)'
              : (_p === 'IRQ') ? 'var(--warn)'
              : (_p === 'CLK' || _p === 'RST') ? 'var(--ok)'
              : 'var(--fg-mute)';
            return (
              <g key={iface.name}>
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth="2" />
                <circle cx={x1} cy={y1} r="4" fill={color} />
                {layers.labels && (
                  <text x={iface.side === 'left' ? x1 - 6 : iface.side === 'right' ? x1 + 6 : x1}
                        y={iface.side === 'top' ? y1 - 6 : iface.side === 'bottom' ? y1 + 16 : y1 - 6}
                        fill="var(--fg-dim)" fontSize="10" fontFamily="var(--mono)"
                        textAnchor={iface.side === 'left' ? 'end' : iface.side === 'right' ? 'start' : 'middle'}>
                    {iface.name} · {iface.proto}{iface.role === 'master' ? ' M' : ' S'}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
        <div className="bd-block sel" style={{ left: bx, top: by, width: blockW, height: blockH }}>
          <div className="bd-block-head" style={{ padding: '10px 14px', fontSize: 14 }}>
            <span className="ico" style={{ fontSize: 16 }}>{g.MOD_ICON[m.kind]}</span>
            <span className="nm" style={{ fontSize: 16, color: 'var(--accent)' }}>{m.name}</span>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>{g.MOD_KIND_LABEL[m.kind]}</span>
          </div>
          <div className="bd-block-body" style={{ padding: '12px 14px', justifyContent: 'flex-start', flexDirection: 'column', alignItems: 'stretch', gap: 10 }}>
            <div className="lbl" style={{ fontSize: 12, color: 'var(--fg-dim)' }}>{m.label}</div>
            {m.addr && <div className="addr" style={{ fontSize: 12 }}>addr · {m.addr}</div>}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
              {(m.params || []).map((p: any) => (
                <span key={p.k} style={{ fontSize: 10, fontFamily: 'var(--mono)', padding: '2px 7px', background: 'var(--bg-3)', border: '1px solid var(--line)', color: 'var(--fg-dim)' }}>
                  {p.k}=<b style={{ color: 'var(--fg)' }}>{p.v}</b>
                </span>
              ))}
            </div>
            <div style={{ marginTop: 6, fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>pipeline</div>
            <PipelineStrip status={m.status} modId={m.id} big />
          </div>
        </div>
      </Fragment>
    );
  };

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

  const renderWorkspaceNode = useCallback((node: any, depth = 0) => {
    if (!node) return null;
    const kids = Array.isArray(node.children) ? node.children : [];
    const artifacts = Array.isArray(node.artifacts) ? node.artifacts : [];
    const isIp = !!node.is_ip;
    return (
      <Fragment key={node.path || node.name}>
        <div className="bd-tree-row"
             title={node.path || node.name}
             style={{ paddingLeft: 10 + depth * 14, alignItems: 'flex-start' }}>
          <span className="tw">{kids.length ? '▾' : '·'}</span>
          <span className="ico">{isIp ? '◇' : '▸'}</span>
          <span style={{ flex: 1, minWidth: 0 }}>
            <span style={{ display: 'block', color: isIp ? 'var(--fg)' : 'var(--fg-dim)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {node.name}
            </span>
            {isIp && (
              <span style={{ display: 'block', fontSize: 8.5, color: 'var(--fg-mute)', marginTop: 2 }}>
                {node.ssot_count || 1} ssot · {artifacts.slice(0, 5).join(' · ')}
              </span>
            )}
          </span>
          {isIp && <span className="pill acc" style={{ fontSize: 8 }}>ip</span>}
        </div>
        {kids.slice(0, depth === 0 ? 80 : 24).map((k: any) => renderWorkspaceNode(k, depth + 1))}
      </Fragment>
    );
  }, []);

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
        {/* LEFT — hierarchy tree */}
        <div style={{
          background: 'var(--panel)', borderRight: '1px solid var(--line)',
          overflow: 'auto', display: 'flex', flexDirection: 'column', position: 'relative',
          visibility: diagramFocus ? 'hidden' : 'visible',
          pointerEvents: diagramFocus ? 'none' : 'auto',
        }}>
          <div className="arch-splitter left"
               title="resize hierarchy"
               onMouseDown={(e) => beginPanelResize('left', e)} />
          <div className="box-h"><b>hierarchy</b><span style={{ flex: 1 }} /><span className="bd-sync">synced</span></div>
          {/* Search box: filters tree to clusters/modules whose id or
              name contains the query (case-insensitive). When a query
              is active, only matching modules are shown plus their
              parent clusters; matched substrings are highlighted. */}
          <div style={{ padding: '6px 8px', borderBottom: '1px solid var(--line)' }}>
            <input
              value={treeQuery}
              onChange={(e) => setTreeQuery(e.target.value)}
              placeholder="search IPs · ⌃F"
              style={{
                width: '100%', boxSizing: 'border-box',
                background: 'var(--bg-2)', border: '1px solid var(--line)',
                color: 'var(--fg)', font: '11px var(--mono)',
                padding: '4px 8px', outline: 'none', borderRadius: 2,
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape') { setTreeQuery(''); (e.target as HTMLInputElement).blur(); }
                else if (e.key === 'Enter' && treeMatches.length > 0) {
                  // Jump straight to first match.
                  const first = treeMatches[0];
                  setSelMod(first.ref); setView(`module:${first.ref}`);
                }
              }}
            />
          </div>
          <div className="bd-tree" style={{ padding: '6px 0', flex: '1 1 52%', minHeight: 160, overflow: 'auto' }}>
            <div className={`bd-tree-row ${view === 'soc' ? 'sel' : ''}`} onClick={() => setView('soc')}>
              <span className="tw">▼</span><span className="ico">⊞</span>
              <span style={{ flex: 1 }}>{soc.name || 'aurora_soc'}</span>
              <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{soc.version ? (soc.version.startsWith('v') ? soc.version : `v${soc.version}`) : 'v0.4.2'}</span>
            </div>
            {soc.clusters.map((c: any) => {
              // When a query is active, only emit clusters that have
              // at least one matching module. Empty clusters are hidden.
              const visibleModules = treeQuery
                ? c.modules.filter((m: any) => _matchesQuery(m, c.id, treeQuery))
                : c.modules;
              if (treeQuery && visibleModules.length === 0) return null;
              return (
              <Fragment key={c.id}>
                <div className={`bd-tree-row cluster ${view === `cluster:${c.id}` ? 'sel' : ''}`}
                     onClick={() => setView(`cluster:${c.id}`)} style={{ paddingLeft: 18 }}>
                  <span className="tw">▼</span>
                  <span className="ico">{c.id === 'cpu_ss' ? '◆' : c.id === 'mem_ss' ? '▦' : c.id === 'periph_ss' ? '⊟' : c.id === 'noc' ? '╫' : '∿'}</span>
                  <span style={{ flex: 1 }}>{c.id}</span>
                  <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{visibleModules.length}{treeQuery ? `/${c.modules.length}` : ''}</span>
                </div>
                {visibleModules.map((m: any) => {
                  const ref = `${c.id}/${m.id}`;
                  const touched = isTouched(ref);
                  return (
                    <div key={ref} className={`bd-tree-row ${selMod === ref ? 'sel' : ''} ${touched ? 'touched' : ''}`}
                         onClick={() => { setSelMod(ref); if (view === 'soc') setView(`cluster:${c.id}`); }}
                         onDoubleClick={() => setView(`module:${ref}`)}
                         style={{ paddingLeft: 38 }}>
                      <span className="tw">·</span>
                      <span className="ico">{g.MOD_ICON[m.kind]}</span>
                      <span style={{ flex: 1, fontSize: 11.5, color: m.status.sim === 'err' ? 'var(--err)' : undefined }}
                            dangerouslySetInnerHTML={{ __html: _highlightMatch(m.name, treeQuery) }} />
                      {touched && <span style={{ background: 'var(--accent)', color: 'var(--bg)', fontSize: 8, padding: '1px 4px', fontWeight: 700 }}>+</span>}
                      <PipelineStrip status={m.status} modId={m.id} />
                      <button title="remove this instance from the SoC"
                              onClick={(e) => { e.stopPropagation(); deleteInstance(m.id); }}
                              style={{
                                border: '1px solid var(--line)',
                                background: 'var(--bg-2)',
                                color: 'var(--fg-mute)',
                                width: 18,
                                height: 18,
                                lineHeight: '14px',
                                padding: 0,
                                fontSize: 13,
                                cursor: 'pointer',
                                marginLeft: 4,
                              }}>×</button>
                    </div>
                  );
                })}
              </Fragment>
              );
            })}
            {treeQuery && treeMatches.length === 0 && (
              <div style={{ padding: '12px 14px', fontSize: 'var(--ui-control-font-size)',
                            color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                no IPs match "{treeQuery}"
              </div>
            )}
          </div>
          <div className="box-h" style={{ borderTop: '1px solid var(--line)' }}>
            <b>available models</b>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{catalog.length}</span>
          </div>
          <div className="bd-tree" style={{ padding: '5px 0', flex: '0 1 34%', minHeight: 110, overflow: 'auto' }}>
            {catalog.length === 0 && (
              <div style={{ padding: '10px 12px', fontSize: 10.5, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                no catalog models found
              </div>
            )}
            {catalog.map((model: any) => {
              const ports: any[] = Array.isArray(model.ports) ? model.ports : [];
              const protoList = [...new Set(ports.map((p: any) => p && p.proto).filter(Boolean))].slice(0, 4);
              return (
                <div key={`${model.source}:${model.name}`} className="bd-tree-row"
                     title={`${model.ssot_path || ''}\n${ports.map((p: any) => `${p.name}:${p.proto}/${p.role}`).join(' · ')}`}
                     onDoubleClick={() => addCatalogInstance(model)}
                     style={{ paddingLeft: 12, alignItems: 'flex-start' }}>
                  <span className="ico">{g.MOD_ICON[model.kind] || '◇'}</span>
                  <span style={{ flex: 1 }}>
                    <span style={{ display: 'block', color: 'var(--fg)' }}>{model.name}</span>
                    <span style={{ display: 'block', fontSize: 9, color: 'var(--fg-mute)', marginTop: 2 }}>
                      {model.kind || 'ip'} · {ports.length} ports
                    </span>
                  </span>
                  <span style={{ display: 'flex', gap: 3, flexWrap: 'wrap', justifyContent: 'flex-end', maxWidth: 76 }}>
                    {protoList.map(p => (
                      <span key={p} style={{
                        fontSize: 8, border: '1px solid var(--line)', padding: '0 3px',
                        color: p === 'APB' ? 'var(--magenta)' : p === 'IRQ' ? 'var(--warn)' : 'var(--accent)',
                      }}>{p}</span>
                    ))}
                    {['ssot-gen', 'rtl-gen', 'tb-gen', 'sim'].map(wf => (
                      <button key={wf}
                              title={`${wf} · .session/${normalizeArchitectSession(`${model.id || model.name}/${wf}`) || wf}`}
                              onClick={(e) => { e.stopPropagation(); dispatchJob(wf, model.id || model.name); }}
                              style={{
                                border: '1px solid var(--line)',
                                background: 'var(--bg-2)',
                                color: 'var(--fg-mute)',
                                font: '8px var(--mono)',
                                padding: '0 3px',
                                cursor: 'pointer',
                              }}>{wf.split('-')[0]}</button>
                    ))}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="box-h" style={{ borderTop: '1px solid var(--line)' }}>
            <b>workspace directory</b>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>{workspaceTree?.children?.length || 0}</span>
          </div>
          <div className="bd-tree" style={{ padding: '5px 0', flex: '0 1 28%', minHeight: 100, overflow: 'auto' }}>
            {!workspaceTree && (
              <div style={{ padding: '10px 12px', fontSize: 10.5, color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                workspace tree unavailable
              </div>
            )}
            {workspaceTree && (workspaceTree.children || []).map((n: any) => renderWorkspaceNode(n, 0))}
          </div>
          <div style={{ padding: 8, borderTop: '1px solid var(--line)', fontSize: 10, color: 'var(--fg-mute)', letterSpacing: '0.05em' }}>
            click → drill cluster · dbl-click → drill module
          </div>
        </div>

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

          {tab === 'diagram' && (
            <div className={`bd-canvas ${view === 'soc' ? 'soc-carbon' : ''}`} style={{ flex: 1 }} ref={bdCanvasRef}
                 onWheel={(e) => {
                   // Cmd/Ctrl + wheel → zoom. Plain wheel → bubble up
                   // (for outer scroll if any). preventDefault on the
                   // zoom path so the page itself doesn't scroll.
                   if (!(e.ctrlKey || e.metaKey)) return;
                   e.preventDefault();
                   const delta = e.deltaY > 0 ? -8 : 8;
                   setZoom(z => Math.max(20, Math.min(200, z + delta)));
                 }}
                 onMouseDown={(e) => {
                   // Pan the stage by dragging on empty canvas. Skip
                   // when the click hit a block — those have their own
                   // click/drag semantics. Right-click also pans.
                   const onBlock = (e.target as HTMLElement).closest && (e.target as HTMLElement).closest('.bd-block');
                   if (onBlock && e.button === 0) return;
                   panDragRef.current = {
                     startX: e.clientX, startY: e.clientY,
                     baseX: pan.x, baseY: pan.y,
                   };
                   e.currentTarget.style.cursor = 'grabbing';
                 }}
                 onMouseMove={(e) => {
                   if (!panDragRef.current) return;
                   const d = panDragRef.current;
                   setPan({ x: d.baseX + (e.clientX - d.startX),
                            y: d.baseY + (e.clientY - d.startY) });
                 }}
                 onMouseUp={(e) => {
                   panDragRef.current = null;
                   e.currentTarget.style.cursor = '';
                 }}
                 onMouseLeave={(e) => {
                   panDragRef.current = null;
                   e.currentTarget.style.cursor = '';
                 }}
                 onDoubleClick={(e) => {
                   // Empty-canvas dblclick → reset pan. Block dblclick
                   // already drills into module-view (see bd-block).
                   const onBlock = (e.target as HTMLElement).closest && (e.target as HTMLElement).closest('.bd-block');
                   if (!onBlock) setPan({ x: 0, y: 0 });
                 }}>
              <div className="bd-layers">
                <div className="ttl">layers</div>
                {Object.keys(layers).map(k => (
                  <label key={k}>
                    <input type="checkbox" checked={(layers as any)[k]} onChange={() => toggleLayer(k)} /><span>{k}</span>
                  </label>
                ))}
              </div>
              <div className="bd-zoom">
                <button onClick={() => setZoom(z => Math.max(50, z - 10))}>−</button>
                <span className="pct">{zoom}%</span>
                <button onClick={() => setZoom(z => Math.min(200, z + 10))}>+</button>
                <button onClick={fitZoom} title="fit diagram to canvas">fit</button>
                <button onClick={async () => {
                          // Save current localStorage layout into
                          // soc.ssot.yaml's instances[].x/y. After save
                          // we keep the localStorage cache so reload
                          // fingerprints match; subsequent /api/soc
                          // fetches will pick up savedX/Y too.
                          if (!isLive) {
                            alert('Save needs a live soc.ssot.yaml — currently in mock mode.');
                            return;
                          }
                          try {
                            const r = await fetch('/api/soc/layout', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ layout }),
                            });
                            const d = await r.json().catch(() => ({}));
                            if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
                            // Re-fetch /api/soc so savedX/Y land on the
                            // module dicts (and the layout is now the
                            // canonical source of truth).
                            refreshSoc();
                            // brief visual confirm via the run-bar text
                            // or just a console hint — keep noise low.
                            console.info('[architect] layout saved →', d.path,
                                         '· touched:', d.touched, 'cleared:', d.cleared);
                          } catch (err: any) {
                            alert('Save failed: ' + (err.message || err));
                          }
                        }}
                        title="save dragged block positions into soc.ssot.yaml (instances[].x/y)"
                        style={{ borderLeft: '1px solid var(--line)',
                                 color: Object.keys(layout).length ? 'var(--accent)' : 'inherit',
                                 opacity: Object.keys(layout).length ? 1 : 0.4 }}>
                  save
                </button>
                <button onClick={() => {
                          if (Object.keys(layout).length === 0) return;
                          if (!confirm('Reset all dragged block positions to the auto-grid layout?')) return;
                          setLayout({}); persistLayout({});
                        }}
                        title="discard user-dragged block positions and revert to auto-grid"
                        style={{ borderLeft: '1px solid var(--line)',
                                 opacity: Object.keys(layout).length ? 1 : 0.4 }}>
                  reset
                </button>
              </div>
              <div className="bd-legend">
                <span className="swatch acc">AXI/ACE</span>
                <span className="swatch magenta">APB</span>
                <span className="swatch cyan">AXI4</span>
                <span className="swatch warn">analog/IRQ</span>
              </div>
              {/* Fixed virtual stage 1180×720. Both the SVG (viewBox
                  0 0 1180 720) and the block divs (raw px coordinates)
                  live in this stage so their coordinate frames agree.
                  The stage is centered + scaled to fit the available
                  bd-canvas area, then user zoom is multiplied on top. */}
              <div style={{ position: 'absolute', inset: 0, display: 'flex',
                            alignItems: 'center', justifyContent: 'center',
                            overflow: 'hidden' }}>
                <div className="bd-stage" style={{
                  position: 'relative',
                  width: 1180, height: 720,
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom/100})`,
                  transformOrigin: 'center center',
                  flex: '0 0 auto',
                  willChange: 'transform',
                }}>
                  {view === 'soc' && renderSocView()}
                  {view.startsWith('cluster:') && renderClusterView(view.split(':')[1])}
                  {view.startsWith('module:') && renderModuleView(view.split(':')[1])}
                </div>
              </div>
              {/* Mini-map (cluster view only — soc/module views don't
                  benefit since they're either a fixed 4-cluster layout
                  or a single big block). */}
              {miniOpen && view.startsWith('cluster:') && (() => {
                const cid = view.split(':')[1];
                const cc = soc.clusters.find((x: any) => x.id === cid);
                if (!cc) return null;
                const W = 1180, H = 720;
                const mw = 180, mh = Math.round(mw * H / W);
                // Recompute positions the same way renderClusterView
                // does (auto-grid + layout overrides) so the mini-map
                // matches exactly.
                const cols = Math.min(3, cc.modules.length);
                const blockW = 220;
                const partition = (m: any) => {
                  const ifs = (m.interfaces || []);
                  let lc = 0, rc = 0;
                  for (const it of ifs) {
                    const r = (it.role || 'slave').toLowerCase();
                    const p = (it.proto || '').toUpperCase();
                    if (p === 'CLK' || p === 'RST') lc++;
                    else if (r === 'master') rc++;
                    else lc++;
                  }
                  return Math.max(lc, rc, 2);
                };
                const sizes = cc.modules.map((m: any) => ({ h: 24 + Math.max(76, partition(m) * 14 + 24) }));
                const maxBlockH = Math.max(140, ...sizes.map((s: any) => s.h));
                const rowsN = Math.ceil(cc.modules.length / cols);
                const gapX = Math.max(40, (W - cols * blockW) / (cols + 1));
                const gapY = Math.max(40, (H - rowsN * maxBlockH - 60) / (rowsN + 1));
                const sx = mw / W, sy = mh / H;
                return (
                  <div className="bd-minimap"
                       onMouseDown={(e) => {
                         // Click on minimap → pan stage so the click
                         // location maps to the canvas center.
                         const rect = e.currentTarget.getBoundingClientRect();
                         const xWorld = (e.clientX - rect.left) / sx;
                         const yWorld = (e.clientY - rect.top)  / sy;
                         const scale = zoom / 100;
                         setPan({
                           x: ((W / 2) - xWorld) * scale,
                           y: ((H / 2) - yWorld) * scale,
                         });
                         e.stopPropagation();
                       }}>
                    <div className="bd-minimap-head">
                      <span>map</span>
                      <span style={{ flex: 1 }} />
                      <span style={{ cursor: 'pointer' }}
                            onClick={(e) => { e.stopPropagation(); setMiniOpen(false); }}>×</span>
                    </div>
                    <div className="bd-minimap-body" style={{ width: mw, height: mh }}>
                      {cc.modules.map((m: any, i: any) => {
                        const ref = `${cc.id}/${m.id}`;
                        const ov = layout && layout[ref];
                        const col = i % cols, rIdx = Math.floor(i / cols);
                        const x = (ov && typeof ov.x === 'number') ? ov.x : gapX + col * (blockW + gapX);
                        const y = (ov && typeof ov.y === 'number') ? ov.y : 40 + gapY + rIdx * (maxBlockH + gapY);
                        const h = sizes[i].h;
                        const isSel = selMod === ref;
                        const tint = m.kind === 'cpu' ? 'var(--accent)'
                                   : m.kind === 'bus' ? 'var(--magenta)'
                                   : m.kind === 'mem' ? 'var(--cyan)'
                                   : m.kind === 'analog' ? 'var(--warn)'
                                   : 'var(--ok)';
                        return (
                          <div key={m.id}
                               title={m.name}
                               onClick={(ev) => { ev.stopPropagation(); setSelMod(ref); }}
                               onDoubleClick={(ev) => { ev.stopPropagation(); setView(`module:${ref}`); }}
                               style={{
                                 position: 'absolute',
                                 left: x * sx, top: y * sy,
                                 width: blockW * sx, height: h * sy,
                                 background: isSel ? tint : 'color-mix(in oklch, ' + tint + ' 30%, var(--bg-2))',
                                 border: '1px solid ' + (isSel ? 'var(--fg)' : tint),
                                 cursor: 'pointer',
                                 borderRadius: 1,
                               }} />
                        );
                      })}
                      {/* Viewport rectangle: shows what's currently
                          visible given pan + zoom. The visible region in
                          stage coords is centered at (W/2 - pan/scale,
                          H/2 - pan/scale) with size = canvas / scale. */}
                      {(() => {
                        const el = bdCanvasRef.current;
                        if (!el) return null;
                        const scale = zoom / 100;
                        const vw = (el.clientWidth || W) / scale;
                        const vh = (el.clientHeight || H) / scale;
                        const cx = W / 2 - pan.x / scale;
                        const cy = H / 2 - pan.y / scale;
                        const x = Math.max(0, cx - vw / 2);
                        const y = Math.max(0, cy - vh / 2);
                        const w = Math.min(W - x, vw);
                        const h = Math.min(H - y, vh);
                        return (
                          <div style={{
                            position: 'absolute',
                            left: x * sx, top: y * sy,
                            width: w * sx, height: h * sy,
                            border: '1.5px solid var(--accent)',
                            background: 'color-mix(in oklch, var(--accent) 8%, transparent)',
                            pointerEvents: 'none',
                            borderRadius: 1,
                          }} />
                        );
                      })()}
                    </div>
                  </div>
                );
              })()}
              {!miniOpen && view.startsWith('cluster:') && (
                <button className="bd-minimap-toggle"
                        onClick={(e) => { e.stopPropagation(); setMiniOpen(true); }}
                        title="show mini-map">map</button>
              )}
            </div>
          )}

          {tab === 'status' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ flex: 1, overflow: 'auto' }}>
                <table className="orch-grid">
                  <thead>
                    <tr>
                      <th style={{ width: 28 }}></th>
                      <th style={{ width: 180 }}>MODULE</th>
                      <th style={{ width: 120 }}>CLUSTER</th>
                      <th style={{ width: 80 }}>TYPE</th>
                      <th style={{ width: 140 }}>ADDR</th>
                      <th style={{ width: 200 }}>SSOT · RTL · SIM</th>
                      <th style={{ width: 180 }}>LIVE JOBS</th>
                      <th style={{ width: 96 }}>LAST RUN</th>
                      <th style={{ width: 80 }}>TESTS</th>
                      <th style={{ width: 56 }}>COV</th>
                      <th style={{ width: 56 }}>DUR</th>
                      <th style={{ width: 120 }}>TREND</th>
                      <th>NOTE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRows.map(r => {
                      const sel = selMod === r.ref;
                      const isErr = r.module.status.sim === 'err';
                      const touched = isTouched(r.ref);
                      const meta = runMeta(r.module);
                      const bars = sparkBars(r.module);
                      const rowJobs = (jobsByIp[r.module.id] || []).slice(0, 4);
                      return (
                        <tr key={r.ref}
                            className={`orch-row ${sel ? 'sel' : ''} ${isErr ? 'errrow' : ''} ${touched ? 'touched' : ''}`}
                            onClick={() => setSelMod(r.ref)}
                            onDoubleClick={() => setView(`module:${r.ref}`)}>
                          <td className="g-mark">
                            {touched ? <span className="g-add">+</span> : sel ? <span style={{ color: 'var(--accent)' }}>▸</span> : ''}
                          </td>
                          <td>
                            <span className="g-mod-ico">{g.MOD_ICON[r.module.kind]}</span>
                            <b className="g-mod-nm">{r.module.name}</b>
                          </td>
                          <td className="g-clu">{r.cluster.id}</td>
                          <td><span className="g-kind">{g.MOD_KIND_LABEL[r.module.kind]}</span></td>
                          <td className="g-addr">{r.module.addr || <span style={{ color: 'var(--fg-mute)' }}>—</span>}</td>
                          <td><StatusTrio status={r.module.status}
                                                 detail={r.module.status_detail}
                                                 source={r.module.status_source}
                                                 big /></td>
                          <td>
                            {rowJobs.length === 0 ? (
                              <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>idle</span>
                            ) : (
                              <span style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                                {rowJobs.map((j: any) => (
                                  <button key={j.job_id || j.run_id}
                                          className={`pill ${j.status === 'running' ? 'run' : j.status === 'completed' ? 'ok' : j.status === 'error' ? 'err' : ''}`}
                                          title={`${j.workflow} · ${j.status}\n${normalizeArchitectSession(j.session || '') || ''}\nclick to show worker log in chat`}
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            window.dispatchEvent(new CustomEvent('atlas:load-job-log', {
                                              detail: { jobId: j.job_id, live: j.status === 'running' },
                                            }));
                                          }}
                                          style={{ border: 0, cursor: 'pointer', fontSize: 9 }}>
                                    {j.status === 'running' ? '◌' : j.status === 'completed' ? '✓' : j.status === 'error' ? '✗' : j.status === 'queued' ? '…' : j.status === 'blocked' ? '⊘' : '○'} {j.workflow}
                                  </button>
                                ))}
                              </span>
                            )}
                          </td>
                          <td className="g-tnum">{meta.t}</td>
                          <td className="g-tnum" style={{ color: isErr ? 'var(--err)' : meta.tests === '—' ? 'var(--fg-mute)' : 'var(--fg-dim)' }}>{meta.tests}</td>
                          <td className="g-tnum" style={{ color: meta.cov === '—' ? 'var(--fg-mute)' : isErr ? 'var(--warn)' : 'var(--ok)' }}>{meta.cov}</td>
                          <td className="g-tnum" style={{ color: 'var(--fg-mute)' }}>{meta.dur}</td>
                          <td onMouseEnter={(e) => {
                                 // Anchor popover to the cell so it
                                 // tracks horizontal scroll inside the
                                 // grid container.
                                 const rect = e.currentTarget.getBoundingClientRect();
                                 setSparkPop({ ref: r.ref, x: rect.right + 4, y: rect.top });
                               }}
                               onMouseLeave={() => setSparkPop((prev: any) => prev && prev.ref === r.ref ? null : prev)}>
                            {bars.length === 0 ? (
                              <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>—</span>
                            ) : (
                              <svg width={Math.max(40, bars.length * 11)} height="18" style={{ display: 'block' }}>
                                {bars.map((h: any, i: any) => (
                                  <rect key={i} x={i * 11} y={18 - h} width={8} height={h}
                                        fill={isErr && i === bars.length - 1 ? 'var(--err)'
                                            : i === bars.length - 1 ? (r.module.status.sim === 'ok' ? 'var(--ok)' : r.module.status.sim === 'partial' ? 'var(--warn)' : 'var(--fg-mute)')
                                            : 'var(--line-2)'} />
                                ))}
                              </svg>
                            )}
                          </td>
                          <td className="g-note">
                            {rowJobs.length ? <span className="acc">worker · {rowJobs[0].workflow} · {rowJobs[0].status} · {rowJobs[0].run_id || rowJobs[0].job_id}</span>
                              : isErr ? <span className="err">✗ sim error · see sim log</span>
                              : r.module.status.sim === 'partial' ? <span className="warn">◐ partial sim artifacts</span>
                              : r.module.status.sim === 'pending' ? <span style={{ color: 'var(--fg-mute)' }}>○ no sim run data</span>
                              : touched ? <span className="acc">layout changed locally</span>
                              : <span style={{ color: 'var(--fg-mute)' }}>—</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {selModule && (
                <div style={{ flex: '0 0 320px', borderTop: '1px solid var(--line)', background: 'var(--panel)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                  <div className="box-h">
                    <span style={{ color: 'var(--fg-mute)' }}>{(soc.name || 'aurora_soc') + '/'}</span>
                    <b>{selModule.name}.ssot.yaml</b>
                    <span style={{ flex: 1 }} />
                    <StatusTrio status={selModule.status}
                                       detail={selModule.status_detail}
                                       source={selModule.status_source}
                                       big />
                    <span className="pill ok" style={{ fontSize: 9, marginLeft: 8 }}>synced</span>
                  </div>
                  <div style={{ flex: 1, overflow: 'auto' }}>
                    <ModuleProgressPanel module={selModule} />
                    <pre className="code-pane" style={{ margin: 0, height: '100%', fontSize: 11.5 }}>
{selModule.id === 'spi' && soc.ssotYamlSpi ? soc.ssotYamlSpi : `# ${selModule.name}.ssot.yaml — generated
component:
  vendor:  atlas.io
  library: ${selCluster.id}
  name:    ${selModule.name}
  version: 0.1.0

parameters:
${(selModule.params || []).map((p: any) => `  - { name: ${p.k.toUpperCase().padEnd(8)}, value: ${p.v} }`).join('\n')}

busInterfaces:
${(selModule.interfaces || []).map((i: any) => `  - { name: ${i.name}, proto: ${i.proto}, role: ${i.role}, side: ${i.side} }`).join('\n')}
${selModule.addr ? `
memoryMap:
  - { name: regs, base: ${selModule.addr.split(' ')[0]}, range: 0x1000 }
` : ''}`}</pre>
                  </div>
                </div>
              )}
            </div>
          )}
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
      {dispatchMenu && (
        <>
          <div onClick={() => setDispatchMenu(null)}
               style={{ position: 'fixed', inset: 0, zIndex: 999 }} />
          <div style={{
            position: 'fixed', left: dispatchMenu.x, top: dispatchMenu.y,
            zIndex: 1000, minWidth: 180,
            background: 'var(--panel)', border: '1px solid var(--line-2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
            font: '11px var(--mono)',
          }}>
            <div style={{ padding: '4px 10px', background: 'var(--bg-2)',
                          borderBottom: '1px solid var(--line)',
                          fontSize: 10, color: 'var(--fg-mute)',
                          letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              dispatch on <b style={{ color: 'var(--accent)' }}>{dispatchMenu.ip}</b>
            </div>
            <div className="bd-dispatch-item"
                 onClick={() => dispatchPipeline(dispatchMenu.ip)}>
              <span style={{ width: 14, textAlign: 'center', color: 'var(--accent)' }}>▶</span>
              <span style={{ flex: 1 }}>full — architect → post-STA</span>
            </div>
            <div style={{ height: 1, background: 'var(--line)', margin: '2px 0' }} />
            {[
              { wf: 'architect', icon: '◇', label: 'architect — SoC contract' },
              { wf: 'ssot-gen', icon: '◐', label: 'ssot-gen — refresh SSOT' },
              { wf: 'fl-model-gen', stage: 'fl-model', icon: 'ƒ', label: 'fl-model — functional model' },
              { wf: 'fl-model-gen', stage: 'cl-model', icon: 'λ', label: 'cl-model — cycle model' },
              { wf: 'fl-model-gen', stage: 'equivalence', icon: '≡', label: 'equivalence — FL vs RTL goals' },
              { wf: 'rtl-gen',  stage: 'rtl', icon: '⚙', label: 'rtl-gen — generate RTL' },
              { wf: 'lint',     stage: 'lint', icon: '✓', label: 'lint' },
              { wf: 'tb-gen',   stage: 'tb', icon: '⌬', label: 'tb-gen — testbench' },
              { wf: 'sim',      stage: 'sim', icon: '▶', label: 'sim' },
              { wf: 'coverage', stage: 'coverage', icon: '▤', label: 'coverage — function/cycle' },
              { wf: 'sim_debug', stage: 'sim-debug', icon: '◎', label: 'sim-debug' },
              { wf: 'syn',      stage: 'syn', icon: '⊕', label: 'syn' },
              { wf: 'dft',      stage: 'dft', icon: '⊗', label: 'dft' },
              { wf: 'sta',      stage: 'sta', icon: '⊞', label: 'sta' },
              { wf: 'pnr',      stage: 'pnr', icon: '▣', label: 'pnr' },
              { wf: 'sta-post', stage: 'sta-post', icon: '◆', label: 'post-sta' },
              { wf: 'sim_debug', stage: 'goal-audit', icon: '□', label: 'goal-audit' },
            ].map(o => (
              <div key={`${o.wf}:${o.stage || ''}`}
                   className="bd-dispatch-item"
                   onClick={() => dispatchJob(o.wf, dispatchMenu.ip, o.stage || '')}>
                <span style={{ width: 14, textAlign: 'center', color: 'var(--fg-mute)' }}>{o.icon}</span>
                <span style={{ flex: 1 }}>{o.label}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Sparkline hover popover — full sim_history of the hovered IP.
          Position-fixed so it can spill out of the grid container. */}
      {sparkPop && (() => {
        const lk = lookup[sparkPop.ref]; if (!lk) return null;
        const m = lk.module;
        const hist = Array.isArray(m.sim_history) ? m.sim_history : [];
        return (
          <div style={{
            position: 'fixed', left: sparkPop.x, top: sparkPop.y,
            zIndex: 1000, pointerEvents: 'none',
            background: 'var(--panel)', border: '1px solid var(--line-2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
            font: '11px var(--mono)', minWidth: 280, maxWidth: 380,
          }}>
            <div style={{ padding: '6px 10px', background: 'var(--bg-2)',
                          borderBottom: '1px solid var(--line)',
                          fontSize: 10, color: 'var(--fg-mute)',
                          letterSpacing: '0.08em', textTransform: 'uppercase',
                          display: 'flex', gap: 8 }}>
              <b style={{ color: 'var(--accent)' }}>{m.name}</b>
              <span style={{ flex: 1 }} />
              <span>sim · {hist.length} run{hist.length === 1 ? '' : 's'}</span>
            </div>
            {hist.length === 0 ? (
              <div style={{ padding: '12px 10px', color: 'var(--fg-mute)', fontStyle: 'italic' }}>
                no sim history yet ·{' '}
                <span style={{ color: 'var(--fg-dim)' }}>
                  populated when {'<'}ip{'>'}/sim/history.json exists
                </span>
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10.5 }}>
                <thead>
                  <tr style={{ color: 'var(--fg-mute)' }}>
                    <th style={{ textAlign: 'left', padding: '4px 8px', fontWeight: 500 }}>WHEN</th>
                    <th style={{ textAlign: 'right', padding: '4px 8px', fontWeight: 500 }}>TESTS</th>
                    <th style={{ textAlign: 'right', padding: '4px 8px', fontWeight: 500 }}>COV</th>
                    <th style={{ textAlign: 'right', padding: '4px 8px', fontWeight: 500 }}>DUR</th>
                    <th style={{ textAlign: 'right', padding: '4px 8px', fontWeight: 500 }}>RES</th>
                  </tr>
                </thead>
                <tbody>
                  {hist.slice().reverse().map((r: any, i: any) => {
                    const sc = r.status === 'ok' ? 'var(--ok)'
                             : r.status === 'partial' ? 'var(--warn)'
                             : r.status === 'err' ? 'var(--err)' : 'var(--fg-mute)';
                    const sym = r.status === 'ok' ? '✓'
                              : r.status === 'partial' ? '◐'
                              : r.status === 'err' ? '✗' : '○';
                    return (
                      <tr key={i} style={{ borderTop: i ? '1px solid var(--line)' : 'none' }}>
                        <td style={{ padding: '3px 8px', color: 'var(--fg-dim)' }}>{r.t || '—'}</td>
                        <td style={{ padding: '3px 8px', textAlign: 'right' }}>{r.tests || '—'}</td>
                        <td style={{ padding: '3px 8px', textAlign: 'right' }}>{r.cov || '—'}</td>
                        <td style={{ padding: '3px 8px', textAlign: 'right', color: 'var(--fg-mute)' }}>{r.dur || '—'}</td>
                        <td style={{ padding: '3px 8px', textAlign: 'right', color: sc }}>{sym}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        );
      })()}
    </div>
  );
}

// ── Transitional bridge so legacy app.jsx + soc-architect.jsx resolve it. ──
g.SocArchitect = SocArchitect;
