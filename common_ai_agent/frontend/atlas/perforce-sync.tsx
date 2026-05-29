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
//   POST /api/scm/add     {ip, paths[]}        -> open selected local files (p4 reconcile)
//   POST /api/scm/submit  {ip, message, add_all:false} -> submit pending changelist
//   POST /api/scm/sync    {ip, paths[]}        -> force sync (overwrite local)
//   POST /api/scm/revert  {ip, paths[]}        -> revert selected pending files
import {
  useState,
  useEffect,
  useRef,
  useCallback,
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
interface PendRow { path: string; action: string }
interface PaneState {
  ok: boolean;
  client?: string;
  stream?: string;
  head?: string;
  local: LocalRow[];
  depot: DepotRow[];
  pending: PendRow[];
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

const sx: Record<string, CSSProperties> = {
  root: { display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, fontSize: 12, color: 'var(--fg)' },
  bar: { display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderBottom: '1px solid var(--line)', background: 'var(--bg-2)', flexWrap: 'wrap' },
  mid: { flex: 1, display: 'flex', minHeight: 0 },
  pane: { flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, minHeight: 0 },
  paneHead: { padding: '6px 10px', borderBottom: '1px solid var(--line)', color: 'var(--fg-mute)', display: 'flex', justifyContent: 'space-between', gap: 8, background: 'var(--bg-2)' },
  list: { flex: 1, overflow: 'auto', minHeight: 0 },
  rowLi: { display: 'flex', alignItems: 'center', gap: 8, padding: '3px 10px', borderBottom: '1px solid var(--line)', cursor: 'pointer', fontFamily: 'var(--mono, monospace)' },
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
  const [ips, setIps] = useState<string[]>([]);
  const [pane, setPane] = useState<PaneState | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [desc, setDesc] = useState('');
  const [selLocal, setSelLocal] = useState<Set<string>>(new Set());
  const [selDepot, setSelDepot] = useState<Set<string>>(new Set());
  const [selPend, setSelPend] = useState<Set<string>>(new Set());
  const mounted = useRef(true);
  const reqRef = useRef(0);

  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

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

  const loadPane = useCallback((targetIp: string) => {
    if (!targetIp) { setPane(null); return; }
    const reqId = ++reqRef.current;
    setBusy(true); setErr('');
    fetch(`/api/scm/pane?ip=${encodeURIComponent(targetIp)}&provider=perforce`, { cache: 'no-store' })
      .then(r => r.json())
      .then((d: PaneState) => {
        if (!mounted.current || reqRef.current !== reqId) return;
        setPane(d);
        if (!d.ok && d.error) setErr(d.error);
        setSelLocal(new Set()); setSelDepot(new Set()); setSelPend(new Set());
      })
      .catch(e => { if (mounted.current && reqRef.current === reqId) setErr(String(e)); })
      .finally(() => { if (mounted.current && reqRef.current === reqId) setBusy(false); });
  }, []);

  useEffect(() => { loadPane(ip); }, [ip, loadPane]);

  const post = useCallback((url: string, body: any, okMsg: string) => {
    setBusy(true); setErr(''); setMsg('');
    fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...body, ip, provider: 'perforce' }) })
      .then(r => r.json())
      .then(d => {
        if (!mounted.current) return;
        if (d && d.ok) setMsg(okMsg + (d.stdout ? ` — ${String(d.stdout).split('\n')[0]}` : ''));
        else setErr((d && (d.error || d.stderr)) || 'operation failed');
      })
      .catch(e => { if (mounted.current) setErr(String(e)); })
      .finally(() => { if (mounted.current) { setBusy(false); loadPane(ip); } });
  }, [ip, loadPane]);

  const toggle = (set: Set<string>, key: string, setter: (s: Set<string>) => void) => {
    const next = new Set(set);
    next.has(key) ? next.delete(key) : next.add(key);
    setter(next);
  };

  const onAdd = () => {
    const paths = selLocal.size ? [...selLocal] : (pane?.local || []).filter(r => r.state !== 'same').map(r => r.path);
    if (!paths.length) { setErr('no local changes to add'); return; }
    post('/api/scm/add', { paths }, `opened ${paths.length} file(s)`);
  };
  const onSubmit = () => {
    if (!desc.trim()) { setErr('description required'); return; }
    post('/api/scm/submit', { message: desc.trim(), add_all: false }, 'submitted');
    setDesc('');
  };
  const onSync = () => {
    const paths = selDepot.size ? [...selDepot] : [];
    post('/api/scm/sync', { paths }, paths.length ? `synced ${paths.length} file(s)` : 'synced (force)');
  };
  const onRevert = () => {
    const paths = selPend.size ? [...selPend] : (pane?.pending || []).map(r => r.path);
    if (!paths.length) { setErr('nothing to revert'); return; }
    post('/api/scm/revert', { paths }, `reverted ${paths.length} file(s)`);
  };

  const local = pane?.local || [];
  const depot = pane?.depot || [];
  const pending = pane?.pending || [];

  return (
    <div style={sx.root}>
      <div style={sx.bar}>
        <strong style={{ color: 'var(--accent)' }}>Perforce</strong>
        <label style={sx.mute}>IP:</label>
        <select value={ip} onChange={e => setIp(e.target.value)} style={{ ...sx.input, flex: 'none', minWidth: 160 }}>
          {!ips.includes(ip) && ip ? <option value={ip}>{ip}</option> : null}
          {ips.map(n => <option key={n} value={n}>{n}</option>)}
        </select>
        <span style={sx.mute} className="mono">
          {pane?.stream || '//GOOD_SOC/GOOD_IP'} {pane?.head ? `@${pane.head}` : ''}
        </span>
        <span style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          {busy ? <span style={sx.mute}>…</span> : null}
          {err ? <span style={{ color: 'var(--err)' }} title={err}>⚠ {err.slice(0, 80)}</span> : null}
          {msg ? <span style={{ color: 'var(--ok)' }}>{msg.slice(0, 80)}</span> : null}
          <button style={sx.btn} onClick={() => loadPane(ip)} disabled={busy || !ip}>↻ Refresh</button>
        </span>
      </div>

      <div style={sx.mid}>
        {/* LEFT — Local IP */}
        <div style={sx.pane}>
          <div style={sx.paneHead}><span>LOCAL IP</span><span className="mono">{local.length} file(s)</span></div>
          <div style={sx.list}>
            {local.length === 0 ? <div style={sx.empty}>no local files tracked / changed</div> :
              local.map(r => {
                const b = STATE_BADGE[r.state] || { label: r.state, color: 'var(--fg-dim)' };
                const checked = selLocal.has(r.path);
                return (
                  <div key={r.path} style={sx.rowLi} onClick={() => toggle(selLocal, r.path, setSelLocal)}>
                    <input type="checkbox" checked={checked} readOnly />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.path}</span>
                    <span style={{ color: b.color, flex: 'none' }}>{b.label}</span>
                  </div>
                );
              })}
          </div>
        </div>

        {/* CENTER — actions */}
        <div style={sx.center}>
          <button style={sx.btn} onClick={onAdd} disabled={busy || !ip} title="Open selected local files (p4 reconcile)">＋ Add</button>
          <button style={sx.btnPrimary} onClick={onSubmit} disabled={busy || !ip} title="Submit the pending changelist">Submit ▶</button>
          <button style={sx.btn} onClick={onSync} disabled={busy || !ip} title="Force-sync from Perforce (overwrite local)">◀ Sync</button>
        </div>

        {/* RIGHT — Perforce depot */}
        <div style={sx.pane}>
          <div style={sx.paneHead}><span>PERFORCE</span><span className="mono">{depot.length} file(s)</span></div>
          <div style={sx.list}>
            {depot.length === 0 ? <div style={sx.empty}>no files in depot for this IP</div> :
              depot.map(r => {
                const checked = selDepot.has(r.path);
                return (
                  <div key={r.path} style={sx.rowLi} onClick={() => toggle(selDepot, r.path, setSelDepot)}>
                    <input type="checkbox" checked={checked} readOnly />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.path}</span>
                    <span style={{ color: 'var(--fg-dim)', flex: 'none' }}>#{r.rev}</span>
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
          <span style={sx.mute}>{pending.length} file(s) opened</span>
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button style={sx.btn} onClick={onRevert} disabled={busy || !pending.length}>Revert</button>
          </span>
        </div>
        <div style={sx.pendList}>
          {pending.length === 0 ? <div style={sx.empty}>nothing opened — select local files and press ＋ Add</div> :
            pending.map(r => {
              const checked = selPend.has(r.path);
              return (
                <div key={r.path} style={sx.rowLi} onClick={() => toggle(selPend, r.path, setSelPend)}>
                  <input type="checkbox" checked={checked} readOnly />
                  <span style={{ color: ACTION_COLOR[r.action] || 'var(--fg-mute)', width: 76, flex: 'none' }}>{r.action}</span>
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.path}</span>
                </div>
              );
            })}
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
          <input style={sx.input} placeholder="changelist description…" value={desc}
                 onChange={e => setDesc(e.target.value)}
                 onKeyDown={e => { if (e.key === 'Enter') onSubmit(); }} />
          <button style={sx.btnPrimary} onClick={onSubmit} disabled={busy || !ip || !pending.length}>✔ Submit</button>
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
