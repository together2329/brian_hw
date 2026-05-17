// ATLAS Git tab — per-IP commit history (graph + structured list +
// diff + explicit revert). Registers window.GitTab consumed by workspace.jsx when
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
    const [gitStatus, setGitStatus] = useState(null);
    const [selectedCommit, setSelectedCommit] = useState(null);
    const [diffBody, setDiffBody] = useState('');
    const [diffBusy, setDiffBusy] = useState(false);
    const [diffErr, setDiffErr] = useState('');
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState(null);
    const [revertTarget, setRevertTarget] = useState(null);
    const [revertBusy, setRevertBusy] = useState(false);
    const mountedRef = useRef(true);
    const diffReqRef = useRef(0);
    useEffect(() => () => { mountedRef.current = false; }, []);

    const clearSelection = useCallback(() => {
      diffReqRef.current += 1;
      setSelectedCommit(null);
      setDiffBody('');
      setDiffErr('');
      setDiffBusy(false);
      setRevertTarget(null);
    }, []);

    useEffect(() => {
      const next = initialIp || '';
      setIp(prev => prev === next ? prev : next);
      setGitStatus(null);
      clearSelection();
    }, [initialIp, clearSelection]);

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
          const nextNames = initialIp && !names.includes(initialIp)
            ? [initialIp, ...names]
            : names;
          setIpList(nextNames);
          setIp(prev => {
            if (prev) return prev;
            const fallback = (window.ACTIVE_IP && nextNames.includes(window.ACTIVE_IP))
              ? window.ACTIVE_IP : nextNames[0];
            return initialIp || fallback || '';
          });
        })
        .catch(() => setErr('cannot list IPs'));
    }, [initialIp]);

    const refresh = useCallback(() => {
      if (!ip) {
        setGraph('');
        setCommits([]);
        setGitStatus(null);
        return;
      }
      setBusy(true); setErr(null);
      const graphUrl = `/api/ip/${encodeURIComponent(ip)}/git/graph?limit=120`;
      const statusUrl = `/api/git/status?ip=${encodeURIComponent(ip)}`;
      const graphReq = fetch(graphUrl, { cache: 'no-store' })
        .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.error || r.status)));
      const statusReq = fetch(statusUrl, { cache: 'no-store' })
        .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.error || r.status)))
        .catch(e => ({ error: String(e) }));
      Promise.all([graphReq, statusReq])
        .then(([d, status]) => {
          if (!mountedRef.current) return;
          const nextCommits = Array.isArray(d.commits) ? d.commits : [];
          setGraph(d.graph || '');
          setCommits(nextCommits);
          setGitStatus(status && !status.error ? status : null);
          if (status && status.error) setErr(status.error);
          setSelectedCommit(prev => {
            if (!prev) return prev;
            return nextCommits.some(c => c.hash === prev.hash) ? prev : null;
          });
        })
        .catch(e => mountedRef.current && setErr(String(e)))
        .finally(() => mountedRef.current && setBusy(false));
    }, [ip]);

    useEffect(() => { refresh(); }, [refresh]);

    const loadCommitDiff = useCallback((commit) => {
      if (!commit || !commit.hash || !ip) return;
      const reqId = ++diffReqRef.current;
      setSelectedCommit(commit);
      setDiffBody('');
      setDiffErr('');
      setDiffBusy(true);
      fetch(`/api/git/show?sha=${encodeURIComponent(commit.hash)}&ip=${encodeURIComponent(ip)}`,
            { cache: 'no-store' })
        .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.error || r.status)))
        .then(d => {
          if (!mountedRef.current || diffReqRef.current !== reqId) return;
          if (d && d.error) setDiffErr(d.error);
          setDiffBody(String(d && d.diff || ''));
        })
        .catch(e => {
          if (mountedRef.current && diffReqRef.current === reqId) setDiffErr(String(e));
        })
        .finally(() => {
          if (mountedRef.current && diffReqRef.current === reqId) setDiffBusy(false);
        });
    }, [ip]);

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
          if (d && d.ok) {
            clearSelection();
            refresh();
          }
          else setErr(d && (d.error || d.stderr) || 'revert failed');
        })
        .catch(e => { setRevertBusy(false); setErr(String(e)); });
    }, [revertTarget, ip, refresh, clearSelection]);

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
    const sxBody = { flex: 1, overflow: 'hidden', display: 'flex', minHeight: 0 };
    const sxGraphPane = {
      flex: '0 0 30%', minWidth: 240, overflow: 'auto', padding: '8px 12px',
      borderRight: '1px solid var(--line)',
      whiteSpace: 'pre',
    };
    const sxListPane = {
      flex: '0 0 32%', minWidth: 280, overflow: 'auto',
      borderRight: '1px solid var(--line)',
    };
    const sxDiffPane = {
      flex: '1 1 38%', minWidth: 320, overflow: 'hidden',
      display: 'flex', flexDirection: 'column', background: 'var(--bg-3)',
    };
    const sxRow = (selected) => ({
      padding: '6px 12px',
      borderBottom: '1px solid var(--line)',
      cursor: 'pointer',
      background: selected ? 'color-mix(in oklch, var(--accent) 12%, transparent)' : 'transparent',
      borderLeft: '3px solid ' + (selected ? 'var(--accent)' : 'transparent'),
    });
    const sxChip = {
      border: '1px solid var(--line)', borderRadius: 4,
      padding: '2px 6px', color: 'var(--fg-mute)', fontSize: 10,
      whiteSpace: 'nowrap',
    };
    const sxMiniButton = {
      background: 'transparent', color: 'var(--accent)',
      border: '1px solid var(--accent)', borderRadius: 4,
      padding: '2px 7px', fontFamily: 'inherit', fontSize: 10,
      cursor: 'pointer',
    };
    const statusFiles = gitStatus && Array.isArray(gitStatus.files) ? gitStatus.files : [];
    const dirtyCount = statusFiles.length;
    const splitIdx = diffBody.indexOf('\ndiff --git');
    const diffHeader = splitIdx >= 0 ? diffBody.slice(0, splitIdx) : diffBody;
    const diffPatch = splitIdx >= 0 ? diffBody.slice(splitIdx + 1) : '';
    const diffLineStyle = (line) => ({
      padding: '0 12px',
      whiteSpace: 'pre',
      background: line.startsWith('+') && !line.startsWith('+++')
        ? 'color-mix(in oklch, var(--ok, #22c55e) 12%, transparent)'
        : line.startsWith('-') && !line.startsWith('---')
          ? 'color-mix(in oklch, var(--red, #ef4444) 12%, transparent)'
          : 'transparent',
      color: line.startsWith('+') && !line.startsWith('+++')
        ? 'var(--ok, #22c55e)'
        : line.startsWith('-') && !line.startsWith('---')
          ? 'var(--red, #ef4444)'
          : 'var(--fg)',
    });

    return (
      <div style={sxFrame}>
        <div style={sxHeader}>
          <span style={{ fontWeight: 600 }}>Git</span>
          <select
            value={ip}
            onChange={e => {
              setIp(e.target.value);
              setGitStatus(null);
              clearSelection();
            }}
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
          {gitStatus && (
            <>
              <span style={sxChip} title={gitStatus.cwd || ''}>
                branch <b style={{ color: 'var(--fg)' }}>{gitStatus.branch || '(none)'}</b>
              </span>
              <span style={sxChip}>
                HEAD <b style={{ color: 'var(--fg)' }}>{gitStatus.head || 'none'}</b>
              </span>
              <span style={{
                ...sxChip,
                color: dirtyCount ? 'var(--warn, #d97706)' : 'var(--fg-mute)',
              }}>
                {dirtyCount ? `${dirtyCount} dirty` : 'clean'}
              </span>
              {(gitStatus.ahead > 0 || gitStatus.behind > 0) && (
                <span style={sxChip}>
                  {gitStatus.ahead > 0 ? `ahead ${gitStatus.ahead}` : ''}
                  {gitStatus.ahead > 0 && gitStatus.behind > 0 ? ' · ' : ''}
                  {gitStatus.behind > 0 ? `behind ${gitStatus.behind}` : ''}
                </span>
              )}
            </>
          )}
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
            <div style={{
              padding: '6px 12px', borderBottom: '1px solid var(--line)',
              color: 'var(--fg-mute)', fontSize: 10,
              textTransform: 'uppercase', letterSpacing: '0.08em',
              position: 'sticky', top: 0, background: 'var(--bg-2)', zIndex: 1,
            }}>
              history · select commit to view diff
            </div>
            {commits.map(c => (
              <div key={c.hash}
                   style={sxRow(selectedCommit && selectedCommit.hash === c.hash)}
                   onClick={() => loadCommitDiff(c)}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                  <code style={{ color: 'var(--accent)' }}>{c.short}</code>
                  <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                    {_fmtRel(c.time)}
                  </span>
                  <span style={{ color: 'var(--fg-mute)', fontSize: 10 }}>
                    {c.author}
                  </span>
                  <span style={{ flex: 1 }} />
                  {selectedCommit && selectedCommit.hash === c.hash && (
                    <button
                      onClick={(ev) => {
                        ev.stopPropagation();
                        setRevertTarget(c);
                      }}
                      style={sxMiniButton}
                      title="hard reset requires confirmation"
                    >Revert…</button>
                  )}
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
          <div style={sxDiffPane}>
            <div style={{
              padding: '6px 12px', borderBottom: '1px solid var(--line)',
              display: 'flex', alignItems: 'center', gap: 8,
              background: 'var(--bg-2)', minHeight: 30,
            }}>
              <span style={{ fontWeight: 600 }}>Diff</span>
              {selectedCommit && (
                <>
                  <code style={{ color: 'var(--accent)' }}>{selectedCommit.short}</code>
                  <span style={{
                    color: 'var(--fg)', overflow: 'hidden',
                    textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>{selectedCommit.subject}</span>
                </>
              )}
              <span style={{ flex: 1 }} />
              {diffBusy && <span style={{ color: 'var(--fg-mute)', fontSize: 11 }}>loading…</span>}
            </div>
            {!selectedCommit ? (
              <div style={{
                padding: 16, color: 'var(--fg-mute)', fontSize: 12,
              }}>
                Select a commit from history to inspect its patch.
              </div>
            ) : diffErr ? (
              <div style={{ padding: 16, color: 'var(--red, #ef4444)', fontSize: 12 }}>
                {diffErr}
              </div>
            ) : (
              <div style={{ flex: 1, overflow: 'auto' }}>
                {diffHeader && (
                  <pre style={{
                    margin: 0, padding: '10px 12px',
                    fontFamily: 'var(--code-font, var(--mono))',
                    fontSize: 11, lineHeight: 1.55,
                    whiteSpace: 'pre-wrap', color: 'var(--fg-mute)',
                    background: 'var(--bg-2)',
                    borderBottom: diffPatch ? '1px solid var(--line)' : 'none',
                  }}>{diffHeader}</pre>
                )}
                {diffPatch ? (
                  <pre className="tool-output-pre tool-output-diff language-none" style={{
                    margin: 0, padding: '8px 0',
                    fontFamily: 'var(--code-font, var(--mono))',
                    fontSize: 11, lineHeight: 1.55,
                    background: 'transparent',
                  }}>
                    {diffPatch.split('\n').map((line, i) => (
                      <div className="diff-line" key={i} style={diffLineStyle(line)}>
                        {line || ' '}
                      </div>
                    ))}
                  </pre>
                ) : (!diffBusy && (
                  <div style={{ padding: 16, color: 'var(--fg-mute)', fontSize: 12 }}>
                    No patch content for this commit.
                  </div>
                ))}
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
