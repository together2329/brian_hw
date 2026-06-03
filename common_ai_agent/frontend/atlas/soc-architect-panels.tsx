// soc-architect-panels.tsx — side panels for the soc-architect.tsx family
// (TypeScript migration of soc-architect.jsx, strangler-fig split).
//
// Holds three self-contained sub-components pulled out of soc-architect.jsx:
//   - ArchitectMyIps    — landing card grid of the user's IPs (internal; used
//                          by SocArchitect's landing early-return).
//   - IpxactImportBtn   — IP-XACT XML uploader (window global).
//   - JobTracker        — collapsible list of dispatched HTTP-worker jobs
//                          (window global).
//
// ArchitectMyIps is exported for the main file to import. IpxactImportBtn and
// JobTracker also bridge to `window.*` at the bottom (same registrations as the
// original) so the live legacy soc-architect.jsx keeps resolving them.
import { useState, useEffect, useRef } from 'react';

const g = window as unknown as Record<string, any>;

// Shared helper owned by soc-architect-shared.tsx; resolved at call time.
const normalizeArchitectSession = (session: unknown): string => g.normalizeArchitectSession(session);

// ── ArchitectMyIps — landing card grid of the logged-in user's IPs ──
// The Architect no longer opens on a mock SoC. It opens on the user's own
// IPs (workspace-session-scoped via `/api/ip/list`). Clicking a card opens that
// IP's real SoC diagram. `ips` (name strings from app.jsx ipOptions) seeds an
// instant paint; the fetch then enriches each card with SSOT/workflow/mtime
// status.
interface ArchitectMyIpsProps {
  ips?: any[];
  activeIp?: string;
  onOpen: (name: string) => void;
}
export function ArchitectMyIps({ ips, activeIp, onOpen }: ArchitectMyIpsProps) {
  const [rows, setRows] = useState<any[] | null>(null);
  useEffect(() => {
    let cancelled = false;
    const activeSession = normalizeArchitectSession(g.ACTIVE_SESSION || '');
    const activeParts = activeSession.split('/').filter(Boolean);
    const owner = normalizeArchitectSession(
      (g.ATLAS_USER && g.ATLAS_USER.username)
      || g.ATLAS_USER_SESSION_ID
      || activeParts[0]
      || ''
    );
    const workspaceSession = normalizeArchitectSession(
      activeParts.length >= 4 && activeParts[0] === owner
        ? activeParts[1]
        : (g.ATLAS_WORKSPACE_SESSION_ID || 'default')
    ) || 'default';
    const sessionScope = activeSession || (owner ? `${owner}/${workspaceSession}` : '');
    const url = '/api/ip/list' + (sessionScope ? `?session_id=${encodeURIComponent(sessionScope)}` : '');
    fetch(url, { cache: 'no-store' })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (!cancelled && d && Array.isArray(d.items)) setRows(d.items); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const seed = (Array.isArray(ips) ? ips : [])
    .map(n => (typeof n === 'string' ? { name: n } : n))
    .filter(x => x && x.name && x.name !== 'default');
  const list = (rows && rows.length) ? rows.filter(r => r && r.name && r.name !== 'default') : seed;

  const fmtAgo = (mt: any): string => {
    const t = Number(mt) || 0;
    if (!t) return '';
    const secs = Math.max(0, Date.now() / 1000 - t);
    if (secs < 90) return 'just now';
    if (secs < 3600) return `${Math.round(secs / 60)}m ago`;
    if (secs < 86400) return `${Math.round(secs / 3600)}h ago`;
    return `${Math.round(secs / 86400)}d ago`;
  };

  if (!list.length) {
    return (
      <div className="arch-screen" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--fg-mute)' }}>
          <div style={{ fontSize: 34, marginBottom: 10, opacity: 0.6 }}>◇</div>
          <div style={{ fontSize: 15, color: 'var(--fg)', marginBottom: 4 }}>아직 IP가 없습니다</div>
          <div style={{ fontSize: 12.5 }}>상단 <b>+</b> 또는 <code>/new-ip &lt;name&gt;</code> 로 첫 IP를 만드세요.</div>
        </div>
      </div>
    );
  }

  const chip = { fontSize: 9, color: 'var(--fg-mute)', border: '1px solid var(--line)', padding: '1px 6px', borderRadius: 999 };
  const badge = (ok: boolean) => ({
    fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 999,
    color: ok ? 'var(--bg)' : 'var(--fg-mute)',
    background: ok ? 'var(--accent)' : 'transparent',
    border: ok ? '1px solid var(--accent)' : '1px solid var(--line)',
  });

  return (
    <div className="arch-screen" style={{ overflowY: 'auto', padding: '24px 28px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontSize: 16 }}>My IPs</h2>
        <span style={{ color: 'var(--fg-mute)', fontSize: 12 }}>
          {list.length} IP{list.length > 1 ? 's' : ''} · 카드를 클릭하면 SoC 다이어그램이 열립니다
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 14 }}>
        {list.map((ip: any) => {
          const isActive = ip.name === activeIp;
          return (
            <button key={ip.name} type="button" onClick={() => onOpen(ip.name)}
              style={{
                textAlign: 'left', cursor: 'pointer', font: 'inherit', color: 'var(--fg)',
                background: 'color-mix(in oklch, var(--fg) 4%, transparent)',
                border: `1px solid ${isActive ? 'var(--accent)' : 'var(--line)'}`,
                borderRadius: 10, padding: '14px 16px',
              }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 14 }}>{ip.name}</span>
                {isActive && (
                  <span style={{ fontSize: 9, color: 'var(--bg)', background: 'var(--accent)', padding: '1px 6px', borderRadius: 999 }}>active</span>
                )}
              </div>
              <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <span style={badge(!!ip.has_ssot)}>{ip.has_ssot ? 'SSOT ✓' : 'SSOT —'}</span>
                {(Array.isArray(ip.workflows) ? ip.workflows : []).slice(0, 4).map((w: string) => (
                  <span key={w} style={chip}>{w}</span>
                ))}
              </div>
              {ip.mtime ? (
                <div style={{ marginTop: 8, fontSize: 11, color: 'var(--fg-mute)' }}>updated {fmtAgo(ip.mtime)}</div>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── IpxactImportBtn — IP-XACT XML uploader ────────────────────
// Opens a hidden file input, uploads the XML to /api/ipxact/import,
// then triggers a refresh on the parent so the new IP appears in
// the architect tree + diagram + grid immediately.
interface IpxactImportBtnProps {
  onImported?: () => void;
}
export function IpxactImportBtn({ onImported }: IpxactImportBtnProps) {
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const onClick = () => { if (fileRef.current && !busy) fileRef.current.click(); };
  const onPick = async (e: any) => {
    const f = e.target.files && e.target.files[0];
    e.target.value = ""; // allow re-picking the same file
    if (!f) return;
    setBusy(true); setMsg("uploading…");
    try {
      // architect-aware: ensure the supervisor workflow is active
      // before importing so the agent can react (suggest scaffold,
      // run addrmap_check, etc.). app.jsx auto-switches when entering
      // the Architect screen, but if the user is here mid-session
      // and the workflow drifted (e.g. via /workflow rtl-gen) we
      // nudge it back. No-op when already on architect.
      if (window.backend && typeof window.backend.send === 'function') {
        window.backend.send({ type: 'prompt', text: '/workflow architect' });
      }
      const fd = new FormData();
      fd.append("xml", f, f.name);
      const r = await fetch("/api/ipxact/import", { method: "POST", body: fd });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
      setMsg(`✓ imported ${d.name} → ${d.path}`);
      // Tell the architect agent so it can suggest next steps
      // (add to soc.ssot.yaml, addr conflict check, scaffold).
      if (window.backend && typeof window.backend.send === 'function') {
        window.backend.send({
          type: 'prompt',
          text: `IP-XACT just imported: ${d.name} → ${d.path}. ` +
                `Add it to soc.ssot.yaml under an appropriate cluster, ` +
                `then run addrmap_check.`,
        });
      }
      if (typeof onImported === "function") onImported();
    } catch (err: any) {
      setMsg(`✗ ${err.message || err}`);
    } finally {
      setBusy(false);
      setTimeout(() => setMsg(""), 4000);
    }
  };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, marginRight: 12 }}>
      <input ref={fileRef} type="file" accept=".xml" style={{ display: "none" }} onChange={onPick} />
      <button className="rb-btn" onClick={onClick} disabled={busy}
              title="Convert an IP-XACT (IEEE 1685) XML file into our SSOT YAML"
              style={busy ? { opacity: 0.5 } : undefined}>
        <span className="icn">{busy ? "◌" : "⇪"}</span>import IP-XACT
      </button>
      {msg && (
        <span style={{ fontSize: 10, fontFamily: "var(--mono)",
                       color: msg.startsWith("✓") ? "var(--ok)" : msg.startsWith("✗") ? "var(--err)" : "var(--fg-mute)",
                       maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {msg}
        </span>
      )}
    </span>
  );
}

// ── JobTracker — collapsible list of dispatched HTTP-worker jobs ──
// Lives above ArchitectChat in the right column. Rows show:
//   <icon> <ip> <workflow> <runtime/iter> <cancel-x>
// Click a row → drill the architect view to that IP's cluster.
// Click cancel × → POST /api/job/<id>/cancel.
interface JobTrackerProps {
  jobs?: any[];
  onSelectIp?: (ip: string) => void;
  onLoadSession?: (session: string) => void;
  onLoadJobLog?: (jobId: string, live: boolean) => void;
}
export function JobTracker({ jobs, onSelectIp, onLoadSession, onLoadJobLog }: JobTrackerProps) {
  const [open, setOpen] = useState(true);
  const live = (jobs || []).filter(j => j.status === 'running');
  const recent = (jobs || []).filter(j => j.status !== 'running');

  if ((jobs || []).length === 0) {
    // Compact "no active jobs" header so the user sees the slot exists.
    return (
      <div className="job-tracker" style={{ maxHeight: 32 }}>
        <div className="job-tracker-head" style={{ cursor: 'default', opacity: 0.6 }}>
          <span>jobs</span>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 9, fontStyle: 'italic' }}>no active dispatch — click ⚡ on a block</span>
        </div>
      </div>
    );
  }

  const fmtElapsed = (j: any): string => {
    const t = j.duration_ms ? Math.round(j.duration_ms / 1000)
            : Math.round((Date.now() / 1000) - (j.started_at || 0));
    if (t < 60) return `${t}s`;
    return `${Math.floor(t / 60)}m${(t % 60).toString().padStart(2, '0')}s`;
  };

  const cancel = async (e: any, jobId: string) => {
    e.stopPropagation();
    try {
      await fetch(`/api/job/${jobId}/cancel`, { method: 'POST' });
    } catch (_) {}
  };

  const clearDone = async () => {
    try { await fetch('/api/jobs/clear', { method: 'POST' }); } catch (_) {}
  };

  return (
    <div className="job-tracker" style={!open ? { maxHeight: 28 } : undefined}>
      <div className="job-tracker-head" onClick={() => setOpen(o => !o)}>
        <span>{open ? '▾' : '▸'} jobs</span>
        {live.length > 0 && <span className="badge">{live.length}</span>}
        <span style={{ flex: 1 }} />
        {recent.length > 0 && (
          <span style={{ fontSize: 9, color: 'var(--fg-mute)' }}>
            {recent.length} done
            <span onClick={(e) => { e.stopPropagation(); clearDone(); }}
                  style={{ marginLeft: 8, cursor: 'pointer', color: 'var(--fg-mute)' }}
                  title="clear completed jobs">×</span>
          </span>
        )}
      </div>
      {open && (
        <div className="job-tracker-list">
          {[...live, ...recent].map(j => {
            const sym = j.status === 'running' ? '◌'
                      : j.status === 'completed' ? '✓'
                      : j.status === 'error' ? '✗'
                      : j.status === 'cancelled' ? '○'
                      : j.status === 'queued' ? '…'
                      : j.status === 'blocked' ? '⊘' : '·';
            const subtitle = j.status === 'running'
              ? `iter ${j.iterations || 0}`
              : j.status === 'error' ? (j.error || '').slice(0, 40)
              : j.status === 'completed' ? `+${(j.files_modified || []).length} files`
              : j.status === 'queued' ? `after ${j.depends_on || 'previous'}`
              : j.status === 'blocked' ? (j.error || 'blocked').slice(0, 40)
              : j.status;
            return (
              <div key={j.job_id || j.run_id}
                   className={`job-row ${j.status || ''}`}
                   title={`${j.workflow} on ${j.ip || '-'} · ${j.prompt || ''}\nworker: ${j.worker || '-'}\nrun_id: ${j.run_id || '-'}`}
                   onClick={() => j.ip && typeof onSelectIp === 'function' && onSelectIp(j.ip)}>
                <span className="icn">{sym}</span>
                <span className="ip">{j.ip || '(no ip)'}{' '}
                  <span style={{ color: 'var(--fg-mute)', fontSize: 9.5, fontWeight: 400 }}>· {subtitle}</span>
                </span>
                <span className="wf">{j.workflow}</span>
                <span className="meta">{fmtElapsed(j)}</span>
                {j.session && (
                  <span className="x"
                        onClick={(e) => {
                          e.stopPropagation();
                          const session = normalizeArchitectSession(j.session);
                          if (session) onLoadSession && onLoadSession(session);
                        }}
                        title={`reload session history: .session/${normalizeArchitectSession(j.session) || '-'}`}>↻</span>
                )}
                <span className="x"
                      onClick={(e) => {
                        e.stopPropagation();
                        onLoadJobLog && onLoadJobLog(j.job_id, j.status === 'running');
                      }}
                      title="show worker log in chat">▤</span>
                {j.status === 'running' ? (
                  <span className="x" onClick={(e) => cancel(e, j.job_id)}
                        title="cancel job">✕</span>
                ) : <span />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Transitional bridge: same window.* registrations as soc-architect.jsx so
// the live legacy file + app.jsx keep resolving them. ──
g.IpxactImportBtn = IpxactImportBtn;
g.JobTracker = JobTracker;
