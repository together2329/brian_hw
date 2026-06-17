// git-tab.tsx — TypeScript migration of git-tab.jsx (strangler-fig).
//
// ATLAS Git tab — per-IP commit history (structured list + split diff +
// explicit revert). Registers window.GitTab consumed by workspace.jsx when
// mainTab === 'git' or the built-in Git companion tab.
//
// TS migration: converted from ambient global React + IIFE window-glue to a
// typed ES module. Still bridges `window.GitTab` at the bottom for not-yet-
// migrated .jsx consumers (workspace.jsx mounts it). Cross-file globals
// (window.ATLAS_USER, window.ATLAS_USER_SESSION_ID, window.ACTIVE_IP) are read
// through a narrow cast since their owners are still .jsx and they are not yet
// declared in types/atlas-window.d.ts.
import {
  useState,
  useEffect,
  useRef,
  useCallback,
  type CSSProperties,
  type ChangeEvent,
  type MouseEvent,
  type ReactNode,
} from 'react';
import { _normalizeDisplayedToolPaths } from './workspace-markdown-chips';

// ── Cross-file window globals owned by unmigrated .jsx, reached via a narrow
// typed view of `window` (not yet in types/atlas-window.d.ts). ──
const w = window as unknown as {
  ATLAS_USER?: { username?: string } | null;
  ATLAS_USER_SESSION_ID?: string;
  ACTIVE_SESSION?: string;
  ACTIVE_IP?: string;
};

// ── Data shapes returned by the ATLAS git API. ──
interface GitCommit {
  hash: string;
  short?: string;
  subject?: string;
  author?: string;
  time?: number;
}

interface GitStatus {
  error?: string;
  branch?: string;
  head?: string;
  cwd?: string;
  files?: unknown[];
  ahead?: number;
  behind?: number;
}

interface IpListItem {
  ip?: string;
  name?: string;
}

const displayPathText = (value: unknown): string => _normalizeDisplayedToolPaths(value);

function _fmtRel(unixSec?: number): string {
  if (!unixSec) return '';
  const delta = Math.max(0, (Date.now() / 1000) - unixSec);
  if (delta < 60) return `${Math.floor(delta)}s ago`;
  if (delta < 3600) return `${Math.floor(delta / 60)}m ago`;
  if (delta < 86400) return `${Math.floor(delta / 3600)}h ago`;
  if (delta < 604800) return `${Math.floor(delta / 86400)}d ago`;
  const d = new Date(unixSec * 1000);
  return d.toLocaleDateString();
}

export interface GitTabProps {
  initialIp?: string;
  provider?: string;
}

export function GitTab({ initialIp, provider = '' }: GitTabProps): ReactNode {
  const [ipList, setIpList] = useState<string[]>([]);
  const [ip, setIp] = useState(initialIp || '');
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null);
  const [selectedCommit, setSelectedCommit] = useState<GitCommit | null>(null);
  const [diffBody, setDiffBody] = useState('');
  const [diffBusy, setDiffBusy] = useState(false);
  const [diffErr, setDiffErr] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [revertTarget, setRevertTarget] = useState<GitCommit | null>(null);
  const [revertBusy, setRevertBusy] = useState(false);
  const mountedRef = useRef(true);
  const diffReqRef = useRef(0);
  useEffect(() => () => { mountedRef.current = false; }, []);
  const forcedProvider = String(provider || '').trim().toLowerCase();
  const withProvider = useCallback((url: string) => {
    if (!forcedProvider || forcedProvider === 'auto' || forcedProvider === 'default') return url;
    const sep = url.includes('?') ? '&' : '?';
    return `${url}${sep}provider=${encodeURIComponent(forcedProvider)}`;
  }, [forcedProvider]);
  const withRouteContext = useCallback((url: string) => {
    const withScmProvider = withProvider(url);
    const sessionId = String(w.ACTIVE_SESSION || '').trim();
    if (!sessionId) return withScmProvider;
    const sep = withScmProvider.includes('?') ? '&' : '?';
    return `${withScmProvider}${sep}session_id=${encodeURIComponent(sessionId)}`;
  }, [withProvider]);

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
    const sid = w.ACTIVE_SESSION
      || (w.ATLAS_USER && w.ATLAS_USER.username)
      || w.ATLAS_USER_SESSION_ID || '';
    const url = '/api/ip/list' + (sid ? `?session_id=${encodeURIComponent(sid)}` : '');
    fetch(url, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(d => {
        if (!mountedRef.current) return;
        const items: IpListItem[] = Array.isArray(d.items) ? d.items : [];
        const names = items.map(it => it.ip || it.name || '').filter(Boolean);
        const ownerScoped = !!(w.ATLAS_USER && w.ATLAS_USER.username);
        const nextNames = !ownerScoped && initialIp && !names.includes(initialIp)
          ? [initialIp, ...names]
          : names;
        setIpList(nextNames);
        setIp(prev => {
          if (prev) return prev;
          const fallback = (w.ACTIVE_IP && nextNames.includes(w.ACTIVE_IP))
            ? w.ACTIVE_IP : nextNames[0];
          return initialIp || fallback || '';
        });
      })
      .catch(() => setErr('cannot list IPs'));
  }, [initialIp]);

  const refresh = useCallback(() => {
    if (!ip) {
      setCommits([]);
      setGitStatus(null);
      return;
    }
    setBusy(true); setErr(null);
    const graphUrl = withRouteContext(`/api/ip/${encodeURIComponent(ip)}/git/graph?limit=120`);
    const statusUrl = withRouteContext(`/api/git/status?ip=${encodeURIComponent(ip)}`);
    const graphReq = fetch(graphUrl, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.error || r.status)));
    const statusReq = fetch(statusUrl, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.error || r.status)))
      .catch(e => ({ error: String(e) }));
    Promise.all([graphReq, statusReq])
      .then(([d, status]) => {
        if (!mountedRef.current) return;
        const nextCommits: GitCommit[] = Array.isArray(d.commits) ? d.commits : [];
        setCommits(nextCommits);
        setGitStatus(status && !status.error ? status : null);
        if (status && status.error) setErr(status.error);
        setSelectedCommit(prev => {
          if (!prev) return prev;
          return nextCommits.some(c => c.hash === prev.hash) ? prev : null;
        });
      })
      .catch(e => {
        if (!mountedRef.current) return;
        setCommits([]);
        setGitStatus(null);
        clearSelection();
        setErr(String(e));
      })
      .finally(() => mountedRef.current && setBusy(false));
  }, [ip, clearSelection, withRouteContext]);

  useEffect(() => { refresh(); }, [refresh]);

  const loadCommitDiff = useCallback((commit: GitCommit) => {
    if (!commit || !commit.hash || !ip) return;
    const reqId = ++diffReqRef.current;
    setSelectedCommit(commit);
    setDiffBody('');
    setDiffErr('');
    setDiffBusy(true);
    fetch(withRouteContext(`/api/git/show?sha=${encodeURIComponent(commit.hash)}&ip=${encodeURIComponent(ip)}`),
          { cache: 'no-store' })
      .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.error || r.status)))
      .then(d => {
        if (!mountedRef.current || diffReqRef.current !== reqId) return;
        if (d && d.error) setDiffErr(d.error);
        setDiffBody(displayPathText(d && d.diff || ''));
      })
      .catch(e => {
        if (mountedRef.current && diffReqRef.current === reqId) setDiffErr(String(e));
      })
      .finally(() => {
        if (mountedRef.current && diffReqRef.current === reqId) setDiffBusy(false);
      });
  }, [ip, withRouteContext]);

  const confirmRevert = useCallback(() => {
    if (!revertTarget || !ip) return;
    setRevertBusy(true);
    fetch(`/api/ip/${encodeURIComponent(ip)}/git/revert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hash: revertTarget.hash,
        provider: forcedProvider || undefined,
        session_id: w.ACTIVE_SESSION || undefined,
      }),
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
  }, [revertTarget, ip, forcedProvider, refresh, clearSelection]);

  const sxFrame: CSSProperties = {
    display: 'flex', flexDirection: 'column', height: '100%',
    background: 'var(--bg)', color: 'var(--fg)',
    fontFamily: 'var(--mono)', fontSize: 12,
  };
  const sxHeader: CSSProperties = {
    padding: '8px 12px',
    borderBottom: '1px solid var(--line)',
    background: 'var(--bg-2)',
    display: 'flex', alignItems: 'center', gap: 10,
  };
  const sxBody: CSSProperties = { flex: 1, overflow: 'hidden', display: 'flex', minHeight: 0 };
  const sxListPane: CSSProperties = {
    flex: '0 0 36%', minWidth: 320, overflow: 'auto',
    borderRight: '1px solid var(--line)',
  };
  const sxDiffPane: CSSProperties = {
    flex: '1 1 64%', minWidth: 360, overflow: 'hidden',
    display: 'flex', flexDirection: 'column', background: 'var(--bg-3)',
  };
  const sxRow = (selected: boolean): CSSProperties => ({
    padding: '6px 12px',
    borderBottom: '1px solid var(--line)',
    cursor: 'pointer',
    background: selected ? 'color-mix(in oklch, var(--accent) 12%, transparent)' : 'transparent',
    borderLeft: '3px solid ' + (selected ? 'var(--accent)' : 'transparent'),
  });
  const sxChip: CSSProperties = {
    border: '1px solid var(--line)', borderRadius: 4,
    padding: '2px 6px', color: 'var(--fg-mute)', fontSize: 10,
    whiteSpace: 'nowrap',
  };
  const sxMiniButton: CSSProperties = {
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
  const diffLineStyle = (line: string): CSSProperties => ({
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
          onChange={(e: ChangeEvent<HTMLSelectElement>) => {
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
            <span style={sxChip} title={displayPathText(gitStatus.cwd || '')}>
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
            {((gitStatus.ahead ?? 0) > 0 || (gitStatus.behind ?? 0) > 0) && (
              <span style={sxChip}>
                {(gitStatus.ahead ?? 0) > 0 ? `ahead ${gitStatus.ahead}` : ''}
                {(gitStatus.ahead ?? 0) > 0 && (gitStatus.behind ?? 0) > 0 ? ' · ' : ''}
                {(gitStatus.behind ?? 0) > 0 ? `behind ${gitStatus.behind}` : ''}
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
                 style={sxRow(!!(selectedCommit && selectedCommit.hash === c.hash))}
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
                    onClick={(ev: MouseEvent<HTMLButtonElement>) => {
                      ev.stopPropagation();
                      setRevertTarget(c);
                    }}
                    style={sxMiniButton}
                    title="hard reset requires confirmation"
                  >Revert…</button>
                )}
              </div>
              <div style={{ marginTop: 2 }}>{displayPathText(c.subject)}</div>
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
                }}>{displayPathText(selectedCommit.subject)}</span>
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
                }}>{displayPathText(diffHeader)}</pre>
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
              <div style={{ marginTop: 6 }}>{displayPathText(revertTarget.subject)}</div>
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

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// workspace.jsx mounts <window.GitTab initialIp=… provider=… />. Not yet in
// types/atlas-window.d.ts, so the assignment goes through a narrow cast.
// Remove once consumers import { GitTab } directly.
(window as unknown as { GitTab: typeof GitTab }).GitTab = GitTab;
