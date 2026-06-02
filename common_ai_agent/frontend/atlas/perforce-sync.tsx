// perforce-sync.tsx — ATLAS Perforce Sync tab (two-pane: Local IP | Perforce).
//
// Registered as window.AtlasSCMTabOverrides.perforce so that, when
// ATLAS_SCM_PROVIDER=perforce, the workspace SCM tab renders THIS component
// instead of the built-in GitTab (see workspace-tool-theme.tsx atlasResolveScmTab).
// No edits to the tab rail / mainTab switch are needed — the existing SCM tab
// swaps its component based on provider + this override.
//
// Backend contract (src/atlas_api_git.py + core/scm_perforce.py):
//   GET  /api/scm/pane?ip=&provider=perforce  -> {local, depot, pending, head, client, stream}
//   POST /api/scm/add     {ip, paths[], targetPaths[]} -> open selected local files
//   POST /api/scm/submit  {ip, message, add_all:false} -> submit pending changelist
//   POST /api/scm/sync    {ip, paths[], targetPaths[]} -> copy Perforce files into local IP root
//   POST /api/scm/revert  {ip, paths[]}        -> revert selected pending files
import {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
  type CSSProperties,
} from 'react';

const w = window as unknown as {
  ATLAS_USER_SESSION_ID?: string;
  ACTIVE_IP?: string;
  GitTab?: any;
  AtlasSCMTabOverrides?: Record<string, any>;
  AtlasSCMTabLabels?: Record<string, string>;
  PerforceSyncTab?: any;
};

interface LocalRow { path: string; state: string }
interface DepotRow { path: string; rev: string }
interface TreeRow { key: string; name: string; path: string; kind: 'up' | 'folder' | 'file'; state?: string; rev?: string }
interface PendRow { path: string; action: string; change?: string }
interface PendingChange { id: string; label?: string; description?: string }
interface PaneState {
  ok: boolean;
  client?: string;
  stream?: string;
  streams?: string[];
  localRoot?: string;
  scmRoot?: string;
  head?: string;
  local: LocalRow[];
  depot: DepotRow[];
  pending: PendRow[];
  pendingChanges?: PendingChange[];
  error?: string;
}

interface PerforceSyncProps {
  initialIp?: string;
  activeIp?: string;
  provider?: string;
  fallbackTab?: any;
}

// state badge → {label, color}
const STATE_BADGE: Record<string, { label: string; color: string }> = {
  new: { label: '● new', color: 'var(--ok)' },
  modified: { label: '~ mod', color: 'var(--warn)' },
  same: { label: '✓ same', color: 'var(--fg-dim)' },
  missing: { label: '✗ local-del', color: 'var(--err)' },
};
const ACTION_COLOR: Record<string, string> = {
  add: 'var(--ok)',
  edit: 'var(--warn)',
  delete: 'var(--err)',
  'move/add': 'var(--ok)',
  'move/delete': 'var(--err)',
};

const parentLocalDir = (dir: string): string => {
  const clean = dir.replace(/\/+$/, '');
  const slash = clean.lastIndexOf('/');
  return slash > 0 ? clean.slice(0, slash) : '';
};

const parentDepotDir = (dir: string, root: string): string => {
  const clean = dir.replace(/\/+$/, '');
  const slash = clean.lastIndexOf('/');
  if (slash < root.length - 1) return root;
  const parent = `${clean.slice(0, slash + 1)}`;
  return parent.length >= root.length ? parent : root;
};

const localFileRowsInDir = (rows: LocalRow[], dir: string): LocalRow[] => {
  const prefix = dir ? `${dir.replace(/\/+$/, '')}/` : '';
  return rows.filter(row => {
    if (!row.path.startsWith(prefix)) return false;
    return !row.path.slice(prefix.length).includes('/');
  });
};

const localTreeRows = (rows: LocalRow[], dir: string): TreeRow[] => {
  const prefix = dir ? `${dir.replace(/\/+$/, '')}/` : '';
  const folders = new Set<string>();
  const out: TreeRow[] = [];
  if (dir) out.push({ key: '..', name: '← ..', path: parentLocalDir(dir), kind: 'up' });
  for (const row of rows) {
    if (!row.path.startsWith(prefix)) continue;
    const rest = row.path.slice(prefix.length);
    const slash = rest.indexOf('/');
    if (slash >= 0) {
      const name = rest.slice(0, slash + 1);
      folders.add(name);
      continue;
    }
    out.push({ key: row.path, name: rest, path: row.path, kind: 'file', state: row.state });
  }
  for (const name of [...folders].sort()) {
    const path = `${prefix}${name}`.replace(/\/+$/, '');
    out.push({ key: `${prefix}${name}`, name, path, kind: 'folder' });
  }
  return out.sort((a, b) => {
    if (a.kind === 'up') return -1;
    if (b.kind === 'up') return 1;
    if (a.kind !== b.kind) return a.kind === 'folder' ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
};

const depotFileRowsInDir = (rows: DepotRow[], dir: string): DepotRow[] => rows.filter(row => {
  if (!row.path.startsWith(dir)) return false;
  return !row.path.slice(dir.length).includes('/');
});

const depotTreeRows = (rows: DepotRow[], dir: string, root: string): TreeRow[] => {
  const folders = new Set<string>();
  const out: TreeRow[] = [];
  if (dir && dir !== root) out.push({ key: '..', name: '← ..', path: parentDepotDir(dir, root), kind: 'up' });
  for (const row of rows) {
    if (!row.path.startsWith(dir)) continue;
    const rest = row.path.slice(dir.length);
    const slash = rest.indexOf('/');
    if (slash >= 0) {
      const name = rest.slice(0, slash + 1);
      folders.add(name);
      continue;
    }
    out.push({ key: row.path, name: rest, path: row.path, kind: 'file', rev: row.rev });
  }
  for (const name of [...folders].sort()) {
    const path = `${dir}${name}`;
    out.push({ key: path, name, path, kind: 'folder' });
  }
  return out.sort((a, b) => {
    if (a.kind === 'up') return -1;
    if (b.kind === 'up') return 1;
    if (a.kind !== b.kind) return a.kind === 'folder' ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
};

const sx: Record<string, CSSProperties> = {
  root: { display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, fontSize: 12, color: 'var(--fg)' },
  bar: { display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderBottom: '1px solid var(--line)', background: 'var(--bg-2)', flexWrap: 'wrap' },
  mid: { flex: 1, display: 'flex', minHeight: 0 },
  pane: { flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, minHeight: 0 },
  paneHead: { padding: '6px 10px', borderBottom: '1px solid var(--line)', color: 'var(--fg-mute)', display: 'flex', justifyContent: 'space-between', gap: 8, background: 'var(--bg-2)' },
  list: { flex: 1, overflow: 'auto', minHeight: 0 },
  rowLi: { display: 'flex', alignItems: 'center', gap: 8, padding: '3px 10px', borderBottom: '1px solid var(--line)', cursor: 'pointer', fontFamily: 'var(--mono, monospace)' },
  crumb: { color: 'var(--fg-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  center: { display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: 10, padding: '0 12px', borderLeft: '1px solid var(--line)', borderRight: '1px solid var(--line)', background: 'var(--bg)' },
  bottom: { borderTop: '1px solid var(--line)', background: 'var(--bg-2)', padding: '8px 12px', maxHeight: '34%', display: 'flex', flexDirection: 'column', minHeight: 0 },
  pendList: { overflow: 'auto', flex: 1, minHeight: 40, border: '1px solid var(--line)', borderRadius: 4, background: 'var(--bg)' },
  btn: { background: 'transparent', color: 'var(--accent)', border: '1px solid var(--accent)', borderRadius: 4, padding: '5px 12px', font: 'inherit', fontSize: 11, cursor: 'pointer', whiteSpace: 'nowrap' },
  btnPrimary: { background: 'var(--accent)', color: 'var(--bg)', border: '1px solid var(--accent)', borderRadius: 4, padding: '5px 12px', font: 'inherit', fontSize: 11, cursor: 'pointer', whiteSpace: 'nowrap' },
  input: { flex: 1, background: 'var(--bg)', color: 'var(--fg)', border: '1px solid var(--line-2)', borderRadius: 4, padding: '5px 8px', font: 'inherit', fontSize: 12, fontFamily: 'var(--mono, monospace)' },
  mute: { color: 'var(--fg-mute)' },
  empty: { padding: '14px 10px', color: 'var(--fg-dim)', textAlign: 'center' as const },
};

function PerforceSyncTab(props: PerforceSyncProps) {
  const provider = String(props.provider || 'perforce').toLowerCase();
  if (provider !== 'perforce' && typeof props.fallbackTab === 'function') {
    const Fallback = props.fallbackTab;
    return <Fallback {...props} />;
  }

  const [ip, setIp] = useState<string>(props.initialIp || props.activeIp || w.ACTIVE_IP || '');
  const [stream, setStream] = useState<string>('');
  const [scmRoot, setScmRoot] = useState<string>('');
  const [ips, setIps] = useState<string[]>([]);
  const [pane, setPane] = useState<PaneState | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [desc, setDesc] = useState('');
  const [selectedChange, setSelectedChange] = useState('default');
  const [localDir, setLocalDir] = useState('');
  const [depotDir, setDepotDir] = useState('');
  const [selLocal, setSelLocal] = useState<Set<string>>(new Set());
  const [selDepot, setSelDepot] = useState<Set<string>>(new Set());
  const [selPend, setSelPend] = useState<Set<string>>(new Set());
  const mounted = useRef(true);
  const reqRef = useRef(0);
  const activeStream = stream || pane?.stream || '';
  const depotRoot = activeStream ? `${activeStream.replace(/\/+$/, '')}/` : '';

  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

  useEffect(() => {
    if (!depotRoot) return;
    setDepotDir(current => current && current.startsWith(depotRoot) ? current : depotRoot);
  }, [depotRoot]);

  // IP dropdown
  useEffect(() => {
    const sid = w.ATLAS_USER_SESSION_ID ? `?session_id=${encodeURIComponent(w.ATLAS_USER_SESSION_ID)}` : '';
    fetch(`/api/ip/list${sid}`, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => {
        if (!mounted.current) return;
        const names = (d && d.items ? d.items : []).map((x: any) => String(x.name || '')).filter(Boolean);
        setIps(names);
        if (!ip && names.length) setIp(names[0]);
      })
      .catch(() => {});
  }, []); // eslint-disable-line

  const loadPane = useCallback((targetIp: string, targetStream = stream, targetScmRoot = scmRoot) => {
    if (!targetIp) { setPane(null); return; }
    const reqId = ++reqRef.current;
    setBusy(true); setErr('');
    const params = new URLSearchParams({ ip: targetIp, provider: 'perforce' });
    if (targetStream) params.set('stream', targetStream);
    if (targetScmRoot) params.set('scm_root', targetScmRoot);
    fetch(`/api/scm/pane?${params.toString()}`, { cache: 'no-store' })
      .then(r => r.json())
      .then((d: PaneState) => {
        if (!mounted.current || reqRef.current !== reqId) return;
        setPane(d);
        if (!targetStream && d.stream) setStream(d.stream);
        if (!targetScmRoot && d.scmRoot) setScmRoot(d.scmRoot);
        const changeIds = (d.pendingChanges || []).map(change => change.id);
        setSelectedChange(current => (changeIds.includes(current) ? current : 'default'));
        const nextStream = targetStream || d.stream || '';
        const nextDepotRoot = nextStream ? `${nextStream.replace(/\/+$/, '')}/` : '';
        if (nextDepotRoot) setDepotDir(current => current && current.startsWith(nextDepotRoot) ? current : nextDepotRoot);
        if (!d.ok && d.error) setErr(d.error);
        setSelLocal(new Set()); setSelDepot(new Set()); setSelPend(new Set());
      })
      .catch(e => { if (mounted.current && reqRef.current === reqId) setErr(String(e)); })
      .finally(() => { if (mounted.current && reqRef.current === reqId) setBusy(false); });
  }, [stream, scmRoot]);

  useEffect(() => { loadPane(ip, stream, scmRoot); }, [ip, stream, scmRoot, loadPane]);

  const post = useCallback((url: string, body: any, okMsg: string) => {
    setBusy(true); setErr(''); setMsg('');
    const activeStream = stream || pane?.stream || '';
    const activeScmRoot = scmRoot || pane?.scmRoot || '';
    const streamBody = activeStream ? { stream: activeStream } : {};
    const rootBody = activeScmRoot ? { scmRoot: activeScmRoot } : {};
    const changeBody = selectedChange ? { changelist: selectedChange } : {};
    fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...body, ip, provider: 'perforce', ...streamBody, ...rootBody, ...changeBody }) })
      .then(r => r.json())
      .then(d => {
        if (!mounted.current) return;
        if (d && d.ok) setMsg(okMsg + (d.stdout ? ` — ${String(d.stdout).split('\n')[0]}` : ''));
        else setErr((d && (d.error || d.stderr)) || 'operation failed');
      })
      .catch(e => { if (mounted.current) setErr(String(e)); })
      .finally(() => { if (mounted.current) { setBusy(false); loadPane(ip, activeStream, activeScmRoot); } });
  }, [ip, stream, scmRoot, pane?.stream, pane?.scmRoot, selectedChange, loadPane]);

  const toggle = (set: Set<string>, key: string, setter: (s: Set<string>) => void) => {
    const next = new Set(set);
    next.has(key) ? next.delete(key) : next.add(key);
    setter(next);
  };

  const local = pane?.local || [];
  const depot = pane?.depot || [];
  const pending = pane?.pending || [];
  const localRows = useMemo(() => localTreeRows(local, localDir), [local, localDir]);
  const depotRows = useMemo(() => depotTreeRows(depot, depotDir || depotRoot, depotRoot), [depot, depotDir, depotRoot]);
  const pendingChanges = pane?.pendingChanges || [{ id: 'default', label: 'default' }];
  const visiblePending = pending.filter(row => (row.change || 'default') === selectedChange);
  const streams = pane?.streams || (pane?.stream ? [pane.stream] : []);

  const onLocalRow = (row: TreeRow) => {
    if (row.kind === 'up' || row.kind === 'folder') {
      setLocalDir(row.path);
      setSelLocal(new Set());
      return;
    }
    toggle(selLocal, row.path, setSelLocal);
  };

  const onDepotRow = (row: TreeRow) => {
    if (row.kind === 'up' || row.kind === 'folder') {
      setDepotDir(row.path);
      setSelDepot(new Set());
      return;
    }
    toggle(selDepot, row.path, setSelDepot);
  };

  const onAdd = () => {
    const localFiles = localFileRowsInDir(local, localDir);
    const paths = selLocal.size ? [...selLocal] : localFiles.filter(r => r.state !== 'same').map(r => r.path);
    if (!paths.length) { setErr('no local changes to add'); return; }
    post('/api/scm/add', { paths, targetPaths: depotDir ? [depotDir] : [] }, `opened ${paths.length} file(s)`);
  };
  const onCheckout = () => {
    const paths = depot.filter(row => selDepot.has(row.path)).map(row => row.path);
    if (!paths.length) { setErr('select Perforce files to checkout'); return; }
    post('/api/scm/edit', { paths, sourceRoot: 'scm' }, `checked out ${paths.length} file(s)`);
  };
  const onSubmit = () => {
    if (!desc.trim()) { setErr('description required'); return; }
    post('/api/scm/submit', { message: desc.trim(), add_all: false }, 'submitted');
    setDesc('');
  };
  const onSync = () => {
    const depotFiles = depotFileRowsInDir(depot, depotDir || depotRoot);
    const selectedFiles = depot.filter(row => selDepot.has(row.path)).map(row => row.path);
    const paths = selectedFiles.length ? selectedFiles : depotFiles.map(r => r.path);
    if (!paths.length) { setErr('no Perforce files to sync'); return; }
    const targetPaths = localDir ? [`${localDir.replace(/\/+$/, '')}/`] : [];
    post('/api/scm/sync', { paths, targetPaths }, `copied ${paths.length} file(s) to local`);
  };
  const onRevert = () => {
    const pendingRows = (pane?.pending || []).filter(row => (row.change || 'default') === selectedChange);
    const paths = selPend.size ? [...selPend] : pendingRows.map(r => r.path);
    if (!paths.length) { setErr('nothing to revert'); return; }
    post('/api/scm/revert', { paths }, `reverted ${paths.length} file(s)`);
  };

  return (
    <div style={sx.root}>
      <div style={sx.bar}>
        <strong style={{ color: 'var(--accent)' }}>Perforce</strong>
        <label style={sx.mute}>IP:</label>
        <select value={ip} onChange={e => { setIp(e.target.value); setStream(''); setLocalDir(''); setDepotDir(''); }} style={{ ...sx.input, flex: 'none', minWidth: 160 }}>
          {!ips.includes(ip) && ip ? <option value={ip}>{ip}</option> : null}
          {ips.map(n => <option key={n} value={n}>{n}</option>)}
        </select>
        <label htmlFor="perforce-scm-root" style={sx.mute}>SCM Root:</label>
        <input
          id="perforce-scm-root"
          aria-label="Perforce SCM root"
          value={scmRoot}
          onChange={e => setScmRoot(e.target.value)}
          style={{ ...sx.input, flex: '0 1 300px', minWidth: 200 }}
        />
        <label htmlFor="perforce-stream-select" style={sx.mute}>Stream:</label>
        <select
          id="perforce-stream-select"
          aria-label="Perforce stream"
          value={activeStream}
          onChange={e => setStream(e.target.value)}
          style={{ ...sx.input, flex: 'none', minWidth: 220 }}
          disabled={!streams.length}
        >
          {activeStream && !streams.includes(activeStream) ? <option value={activeStream}>{activeStream}</option> : null}
          {streams.map(n => <option key={n} value={n}>{n}</option>)}
        </select>
        <span style={sx.mute} className="mono">
          {pane?.head ? `@${pane.head}` : ''}
        </span>
        <span style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          {busy ? <span style={sx.mute}>…</span> : null}
          {err ? <span style={{ color: 'var(--err)' }} title={err}>⚠ {err.slice(0, 80)}</span> : null}
          {msg ? <span style={{ color: 'var(--ok)' }}>{msg.slice(0, 80)}</span> : null}
          <button style={sx.btn} onClick={() => loadPane(ip, activeStream, scmRoot)} disabled={busy || !ip}>↻ Refresh</button>
        </span>
      </div>

      <div style={sx.mid}>
        {/* LEFT — Local IP */}
        <div style={sx.pane}>
          <div style={sx.paneHead}>
            <span>LOCAL IP</span>
            <span style={sx.crumb} className="mono">/{localDir}</span>
            <span className="mono">{local.length} file(s)</span>
          </div>
          <div style={sx.list}>
            {localRows.length === 0 ? <div style={sx.empty}>empty folder</div> :
              localRows.map(r => {
                const state = r.state || 'unknown';
                const b = STATE_BADGE[state] || { label: state, color: 'var(--fg-dim)' };
                const checked = selLocal.has(r.path);
                return (
                  <div key={r.key} style={sx.rowLi} onClick={() => onLocalRow(r)} title={r.path}>
                    {r.kind === 'file' ? <input type="checkbox" checked={checked} readOnly /> : <span style={{ width: 13, flex: 'none' }}>▸</span>}
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.name}</span>
                    {r.kind === 'file' ? <span style={{ color: b.color, flex: 'none' }}>{b.label}</span> : <span style={{ color: 'var(--fg-dim)', flex: 'none' }}>dir</span>}
                  </div>
                );
              })}
          </div>
        </div>

        {/* CENTER — actions */}
        <div style={sx.center}>
          <button style={sx.btn} onClick={onAdd} disabled={busy || !ip} title="Open selected local files (p4 reconcile)">＋ Add</button>
          <button style={sx.btn} onClick={onCheckout} disabled={busy || !ip} title="Open selected Perforce files into the pending changelist">☑ Checkout</button>
          <button style={sx.btn} onClick={onSync} disabled={busy || !ip} title="Copy selected Perforce files into the local IP root">◀ Sync</button>
        </div>

        {/* RIGHT — Perforce depot */}
        <div style={sx.pane}>
          <div style={sx.paneHead}>
            <span>PERFORCE TARGET</span>
            <span style={sx.crumb} className="mono">{depotDir || depotRoot}</span>
            <span className="mono">{depot.length} file(s)</span>
          </div>
          <div style={sx.list}>
            {depotRows.length === 0 ? <div style={sx.empty}>empty folder</div> :
              depotRows.map(r => {
                const checked = selDepot.has(r.path);
                return (
                  <div key={r.key} style={sx.rowLi} onClick={() => onDepotRow(r)} title={r.path}>
                    {r.kind === 'file' ? <input type="checkbox" checked={checked} readOnly /> : <span style={{ width: 13, flex: 'none' }}>▸</span>}
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.name}</span>
                    <span style={{ color: 'var(--fg-dim)', flex: 'none' }}>{r.kind === 'file' ? `#${r.rev}` : 'dir'}</span>
                  </div>
                );
              })}
          </div>
        </div>
      </div>

      {/* BOTTOM — pending changelist */}
      <div style={sx.bottom}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <strong>PENDING</strong>
          <span style={sx.mute}>{visiblePending.length} file(s) opened</span>
          <label htmlFor="perforce-pending-change" style={sx.mute}>CL:</label>
          <select
            id="perforce-pending-change"
            aria-label="Pending changelist"
            value={selectedChange}
            onChange={e => { setSelectedChange(e.target.value); setSelPend(new Set()); }}
            style={{ ...sx.input, flex: 'none', minWidth: 160 }}
          >
            {pendingChanges.map(change => (
              <option key={change.id} value={change.id}>{change.label || change.id}</option>
            ))}
          </select>
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button style={sx.btn} onClick={onRevert} disabled={busy || !visiblePending.length}>Revert</button>
          </span>
        </div>
        <div style={sx.pendList}>
          {visiblePending.length === 0 ? <div style={sx.empty}>nothing opened — select local files and press ＋ Add</div> :
            visiblePending.map(r => {
              const checked = selPend.has(r.path);
              return (
                <div key={r.path} style={sx.rowLi} onClick={() => toggle(selPend, r.path, setSelPend)}>
                  <input type="checkbox" checked={checked} readOnly />
                  <span style={{ color: ACTION_COLOR[r.action] || 'var(--fg-mute)', width: 76, flex: 'none' }}>{r.action}</span>
                  <span style={{ color: 'var(--fg-dim)', width: 64, flex: 'none' }}>{r.change || 'default'}</span>
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.path}</span>
                </div>
              );
            })}
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
          <input style={sx.input} placeholder="changelist description…" value={desc}
                 onChange={e => setDesc(e.target.value)}
                 onKeyDown={e => { if (e.key === 'Enter') onSubmit(); }} />
          <button style={sx.btnPrimary} onClick={onSubmit} disabled={busy || !ip || !visiblePending.length}>✔ Submit</button>
        </div>
      </div>
    </div>
  );
}

// ── Register as the Perforce SCM tab override (consumed by atlasResolveScmTab
// / atlasScmTabLabel in workspace-tool-theme.tsx) ──
w.AtlasSCMTabOverrides = w.AtlasSCMTabOverrides || {};
w.AtlasSCMTabOverrides.perforce = PerforceSyncTab;
w.AtlasSCMTabLabels = w.AtlasSCMTabLabels || {};
w.AtlasSCMTabLabels.perforce = 'Perforce';
w.PerforceSyncTab = PerforceSyncTab;

export default PerforceSyncTab;
