// ATLAS Git tab — per-IP commit history (graph + structured list +
// revert). Registers window.GitTab consumed by workspace.jsx when
// mainTab === 'git'.

(function () {
  const { useState, useEffect, useRef, useCallback } = React;

  function _fmtRel(unixSec) {
    if (!unixSec) return '';
    const delta = Math.max(0, (Date.now() / 1000) - unixSec);
    if (delta < 60) return `${Math.floor(delta)}s ago`;
    if (delta < 3600) return `${Math.floor(delta / 60)}m ago`;
    if (delta < 86400) return `${Math.floor(delta / 3600)}h ago`;
    if (delta < 604800) return `${Math.floor(delta / 86400)}d ago`;
    const d = new Date(unixSec * 1000);
    return d.toLocaleDateString();
  }

  function GitTab({ initialIp }) {
    const [ipList, setIpList] = useState([]);
    const [ip, setIp] = useState(initialIp || '');
    const [graph, setGraph] = useState('');
    const [commits, setCommits] = useState([]);
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState(null);
    const [revertTarget, setRevertTarget] = useState(null);
    const [revertBusy, setRevertBusy] = useState(false);
    const mountedRef = useRef(true);
    useEffect(() => () => { mountedRef.current = false; }, []);

    // Pull the IP roster from /api/ip/list (session-scoped in multi-user mode).
    useEffect(() => {
      const sid = (window.ATLAS_USER && window.ATLAS_USER.username)
        || window.ATLAS_USER_SESSION_ID || '';
      const url = '/api/ip/list' + (sid ? `?session_id=${encodeURIComponent(sid)}` : '');
      fetch(url, { cache: 'no-store' })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(d => {
          if (!mountedRef.current) return;
          const items = Array.isArray(d.items) ? d.items : [];
          const names = items.map(it => it.ip || it.name || '').filter(Boolean);
          setIpList(names);
          if (!ip && names.length) {
            const fallback = (window.ACTIVE_IP && names.includes(window.ACTIVE_IP))
              ? window.ACTIVE_IP : names[0];
            setIp(fallback);
          }
        })
        .catch(() => setErr('cannot list IPs'));
    }, []);  // run once

    const refresh = useCallback(() => {
      if (!ip) return;
      setBusy(true); setErr(null);
      fetch(`/api/ip/${encodeURIComponent(ip)}/git/graph?limit=120`,
            { cache: 'no-store' })
        .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.error || r.status)))
        .then(d => {
          if (!mountedRef.current) return;
          setGraph(d.graph || '');
          setCommits(Array.isArray(d.commits) ? d.commits : []);
        })
        .catch(e => mountedRef.current && setErr(String(e)))
        .finally(() => mountedRef.current && setBusy(false));
    }, [ip]);

    useEffect(() => { refresh(); }, [refresh]);

    const confirmRevert = useCallback(() => {
      if (!revertTarget || !ip) return;
      setRevertBusy(true);
      fetch(`/api/ip/${encodeURIComponent(ip)}/git/revert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hash: revertTarget.hash }),
      })
        .then(r => r.json())
        .then(d => {
          setRevertBusy(false);
          setRevertTarget(null);
          if (d && d.ok) refresh();
          else setErr(d && (d.error || d.stderr) || 'revert failed');
        })
        .catch(e => { setRevertBusy(false); setErr(String(e)); });
    }, [revertTarget, ip, refresh]);

    const sxFrame = {
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'var(--bg)', color: 'var(--fg)',
      fontFamily: 'var(--mono)', fontSize: 12,
    };
    const sxHeader = {
      padding: '8px 12px',
      borderBottom: '1px solid var(--line)',
      background: 'var(--bg-2)',
      display: 'flex', alignItems: 'center', gap: 10,
    };
    const sxBody = { flex: 1, overflow: 'hidden', display: 'flex' };
    const sxGraphPane = {
      flex: '1 1 60%', overflow: 'auto', padding: '8px 12px',
      borderRight: '1px solid var(--line)',
      whiteSpace: 'pre',
    };
    const sxListPane = {
      flex: '1 1 40%', overflow: 'auto',
    };
    const sxRow = (selected) => ({
      padding: '6px 12px',
      borderBottom: '1px solid var(--line)',
      cursor: 'pointer',
      background: selected ? 'color-mix(in oklch, var(--accent) 12%, transparent)' : 'transparent',
    });

    return (
      <div style={sxFrame}>
        <div style={sxHeader}>
          <span style={{ fontWeight: 600 }}>Git</span>
          <select
            value={ip}
            onChange={e => setIp(e.target.value)}
            style={{
              background: 'var(--bg)', color: 'var(--fg)',
              border: '1px solid var(--line)', borderRadius: 4,
              padding: '4px 8px', fontFamily: 'inherit', fontSize: 12,
            }}>
            {!ip && <option value="">(select IP)</option>}
            {ipList.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
          <button onClick={refresh} disabled={busy || !ip}
                  style={{
                    background: 'transparent', color: 'var(--accent)',
                    border: '1px solid var(--accent)', borderRadius: 4,
                    padding: '4px 10px', fontFamily: 'inherit', fontSize: 11,
                    cursor: busy ? 'wait' : 'pointer',
                  }}>{busy ? '…' : '↻ Refresh'}</button>
          <span style={{ flex: 1 }} />
          {err && (
            <span style={{ color: 'var(--red, #ef4444)', fontSize: 11 }}>
              ⚠ {err}
            </span>
          )}
          <span style={{ color: 'var(--fg-mute)', fontSize: 11 }}>
            {commits.length} commits
          </span>
        </div>
        <div style={sxBody}>
          <div style={sxGraphPane}>
            {graph || (busy ? 'loading…' : '(no commits)')}
          </div>
          <div style={sxListPane}>
            {commits.map(c => (
              <div key={c.hash}
                   style={sxRow(revertTarget && revertTarget.hash === c.hash)}
                   onClick={() => setRevertTarget(c)}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                  <code style={{ color: 'var(--accent)' }}>{c.short}</code>
                  <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                    {_fmtRel(c.time)}
                  </span>
                  <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                    {c.author}
                  </span>
                </div>
                <div style={{ marginTop: 2 }}>{c.subject}</div>
              </div>
            ))}
            {commits.length === 0 && !busy && (
              <div style={{ padding: 16, color: 'var(--fg-mute)' }}>
                no commits yet
              </div>
            )}
          </div>
        </div>

        {revertTarget && (
          <div role="dialog" aria-modal="true" style={{
            position: 'fixed', inset: 0, zIndex: 9997,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'color-mix(in oklch, var(--bg) 60%, transparent)',
          }}>
            <div style={{
              minWidth: 380, maxWidth: 520,
              padding: '18px 22px',
              background: 'var(--bg-2)',
              border: '1px solid var(--red, #ef4444)',
              borderRadius: 8,
              color: 'var(--fg)',
              fontFamily: 'var(--mono)', fontSize: 13,
              display: 'flex', flexDirection: 'column', gap: 12,
            }}>
              <div style={{ fontWeight: 700, fontSize: 14 }}>
                Revert <code>{ip}</code> to commit?
              </div>
              <div>
                <code style={{ color: 'var(--accent)' }}>{revertTarget.short}</code>
                {'  '}
                <span style={{ color: 'var(--fg-mute)' }}>{_fmtRel(revertTarget.time)}</span>
                <div style={{ marginTop: 6 }}>{revertTarget.subject}</div>
              </div>
              <div style={{ fontSize: 11, color: 'var(--red, #ef4444)' }}>
                ⚠ Hard reset — all changes after this commit on the working tree will be lost.
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button onClick={() => setRevertTarget(null)} disabled={revertBusy}
                        style={{
                          background: 'transparent', color: 'var(--fg)',
                          border: '1px solid var(--line)', borderRadius: 4,
                          padding: '6px 12px', cursor: 'pointer',
                          fontFamily: 'inherit', fontSize: 12,
                        }}>Cancel</button>
                <button onClick={confirmRevert} disabled={revertBusy}
                        style={{
                          background: 'var(--red, #ef4444)', color: 'white',
                          border: 'none', borderRadius: 4,
                          padding: '6px 12px',
                          cursor: revertBusy ? 'wait' : 'pointer',
                          fontFamily: 'inherit', fontSize: 12, fontWeight: 600,
                        }}>{revertBusy ? '…' : 'Revert (hard reset)'}</button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  window.GitTab = GitTab;
})();
