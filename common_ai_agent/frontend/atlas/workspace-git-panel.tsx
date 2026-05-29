// workspace-git-panel.tsx — GitPanel (per-IP git status + commits).
//
// Extracted from workspace-panels.tsx (Phase 13g cluster split) to keep every
// file under 1000 lines. Shared types + the _statusGlyph forward-ref live in
// workspace-panel-shared.tsx. Still bridges window.GitPanel at the bottom for
// not-yet-migrated .jsx consumers (workspace.jsx aliases it back).
import {
  useState,
  useEffect,
  useCallback,
} from 'react';
import {
  _statusGlyph,
  type GitFile,
  type GitCommit,
  type GitOpResult,
} from './workspace-panel-shared';

export interface GitPanelProps {
  activeIp?: string;
}

export const GitPanel = ({ activeIp: activeIpProp = '' }: GitPanelProps = {}) => {
  const [branch, setBranch] = useState('');
  const [ahead, setAhead]   = useState(0);
  const [behind, setBehind] = useState(0);
  const [files, setFiles]   = useState<GitFile[]>([]);
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [error, setError]   = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [diff, setDiff]     = useState('');
  const [diffLoading, setDiffLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy]     = useState('');   // '' | 'commit' | 'push'
  const [lastResult, setLastResult] = useState<GitOpResult | null>(null);

  const [activeIp, setActiveIp] = useState(activeIpProp || '');

  useEffect(() => {
    setActiveIp(activeIpProp || '');
    setSelected(null);
    setDiff('');
  }, [activeIpProp]);

  const refresh = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (activeIp) params.set('ip', activeIp);
      const qs = params.toString();
      const r = await fetch('/api/git/status' + (qs ? `?${qs}` : ''));
      const d = await r.json();
      setBranch(d.branch || ''); setAhead(d.ahead || 0); setBehind(d.behind || 0);
      setFiles(d.files || []); setError(d.error || '');
    } catch (e) { setError(String(e)); }
    try {
      const params = new URLSearchParams({ limit: '80' });
      if (activeIp) params.set('ip', activeIp);
      const r = await fetch('/api/git/log?' + params.toString());
      const d = await r.json();
      setCommits(Array.isArray(d.commits) ? d.commits : []);
    } catch (_) {}
  }, [activeIp]);

  useEffect(() => { refresh(); const id = setInterval(refresh, 5000); return () => clearInterval(id); }, [refresh]);

  // When user clicks a file, fetch its diff (cached as `selected`)
  useEffect(() => {
    if (!selected) { setDiff(''); return; }
    let cancelled = false;
    setDiffLoading(true);
    const params = new URLSearchParams({ path: selected });
    if (activeIp) params.set('ip', activeIp);
    fetch('/api/git/diff?' + params.toString())
      .then(r => r.json())
      .then(d => { if (!cancelled) { setDiff(d.diff || d.error || ''); setDiffLoading(false); } })
      .catch(e => { if (!cancelled) { setDiff(String(e)); setDiffLoading(false); } });
    return () => { cancelled = true; };
  }, [selected, files.length, activeIp]);

  const doCommit = async () => {
    if (!message.trim()) { alert('Commit message required.'); return; }
    setBusy('commit');
    try {
      const r = await fetch('/api/git/commit', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, add_all: true, ip: activeIp }),
      });
      const d = await r.json();
      setLastResult({ kind: 'commit', ...d });
      if (d.ok) setMessage('');
      refresh();
    } finally { setBusy(''); }
  };

  const doPush = async () => {
    if (!confirm('Push branch "' + (branch || '?') + '" to origin?')) return;
    setBusy('push');
    try {
      const r = await fetch('/api/git/push', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: activeIp }),
      });
      const d = await r.json();
      setLastResult({ kind: 'push', ...d });
      refresh();
    } finally { setBusy(''); }
  };

  const stagedCount   = files.filter(f => f.staged).length;
  const unstagedCount = files.filter(f => f.unstaged).length;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, fontSize: 12 }}>
      {/* Branch / ahead-behind / refresh */}
      <div style={{
        padding: '6px 10px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--mono)',
      }}>
        <span className="mute" style={{ fontSize: 10 }}>branch</span>
        <span className="acc" style={{ fontWeight: 600 }}>{branch || '(none)'}</span>
        {ahead  > 0 && <span className="ok"  style={{ fontSize: 10 }}>↑{ahead}</span>}
        {behind > 0 && <span className="warn" style={{ fontSize: 10 }}>↓{behind}</span>}
        <span style={{ flex: 1 }} />
        <span onClick={refresh} title="refresh git status"
              style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 13, padding: '0 6px' }}>↻</span>
      </div>

      {/* Commit history — clickable; emits atlas-git-show so the
          center pane can render the unified diff for the chosen
          commit (matches "branch / changes / commit msg + click =
          show diff in center" UX request). */}
      {commits.length ? (
        <div style={{
          borderBottom: '1px solid var(--line)',
          maxHeight: 220,
          overflow: 'auto',
          background: 'var(--bg-2)',
        }}>
          <div className="mute" style={{
            padding: '4px 10px', fontSize: 10,
            textTransform: 'uppercase', letterSpacing: '0.08em',
            borderBottom: '1px solid var(--line)',
          }}>history · {commits.length}</div>
          {commits.map(c => (
            <div
              key={c.sha}
              onClick={() => {
                window.dispatchEvent(new CustomEvent('atlas-git-show', {
                  detail: { sha: c.sha, ip: activeIp, subject: c.subject },
                }));
              }}
              title={`${c.short} · ${c.author} · ${c.date}\n${c.subject}\n+${c.added || 0} −${c.removed || 0} across ${c.files || 0} file(s)`}
              style={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr auto',
                gap: 6,
                padding: '3px 10px',
                cursor: 'pointer',
                fontFamily: 'var(--mono)',
                fontSize: 'var(--ui-control-font-size)',
                borderLeft: '2px solid transparent',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-3)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{c.short}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{c.subject}</span>
              <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>
                {c.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{c.added}</span>}
                {c.removed != null && <span className="err">−{c.removed}</span>}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {/* File list */}
      <div style={{ borderBottom: '1px solid var(--line)', maxHeight: 200, overflow: 'auto' }}>
        {error && <div className="warn" style={{ padding: '8px 10px', fontSize: 11 }}>{error}</div>}
        {!error && files.length === 0 && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            (working tree clean)
          </div>
        )}
        {files.map((f, i) => {
          const sg = _statusGlyph(f.status || '  ');
          const isSel = selected === f.path;
          return (
            <div key={i}
              onClick={() => setSelected(f.path)}
              title={f.path + ' · ' + (f.status || '')}
              style={{
                display: 'grid', gridTemplateColumns: '20px 1fr auto', gap: 6,
                padding: '3px 10px', cursor: 'pointer', fontFamily: 'var(--mono)',
                background: isSel ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                borderLeft: isSel ? '2px solid var(--accent)' : '2px solid transparent',
              }}>
              <span style={{ color: sg.staged.color, fontWeight: 700 }}>{sg.staged.ch}{sg.work.ch}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{f.path}</span>
              <span style={{ fontSize: 10 }}>
                {f.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{f.added}</span>}
                {f.removed != null && <span className="err">−{f.removed}</span>}
              </span>
            </div>
          );
        })}
      </div>

      {/* Diff viewer for selected file */}
      <div style={{ flex: 1, overflow: 'auto', borderBottom: '1px solid var(--line)' }}>
        {!selected && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            Click a file above to view its diff.
          </div>
        )}
        {selected && (
          <pre className="code" style={{
            margin: 0, padding: '8px 10px', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5,
            whiteSpace: 'pre', fontFamily: 'var(--mono)',
          }}>
            {diffLoading ? 'loading…' :
              (diff || '').split('\n').map((line, i) => {
                let color = 'var(--fg)';
                let bg = 'transparent';
                if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff ') || line.startsWith('@@') || line.startsWith('index ')) {
                  color = 'var(--accent)';
                } else if (line.startsWith('+')) {
                  color = '#7ee787'; bg = 'color-mix(in oklch, #3fb950 12%, transparent)';
                } else if (line.startsWith('-')) {
                  color = '#ffa198'; bg = 'color-mix(in oklch, #f85149 12%, transparent)';
                }
                return <div key={i} style={{ color, background: bg }}>{line || ' '}</div>;
              })
            }
          </pre>
        )}
      </div>

      {/* Commit composer */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          {files.length} change{files.length === 1 ? '' : 's'}
          {stagedCount   > 0 && <span className="ok"   style={{ marginLeft: 6 }}>{stagedCount} staged</span>}
          {unstagedCount > 0 && <span className="warn" style={{ marginLeft: 6 }}>{unstagedCount} unstaged</span>}
        </div>
        <textarea
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder="Commit message — first line = summary, blank line + body for details"
          rows={3}
          style={{
            background: 'var(--bg-3)', border: '1px solid var(--line)',
            borderRadius: 2, padding: '6px 8px', fontSize: 12,
            fontFamily: 'var(--mono)', color: 'var(--fg)', resize: 'vertical',
            outline: 'none', minHeight: 50,
          }}
        />
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className="btn primary"
            disabled={busy !== '' || !message.trim() || files.length === 0}
            onClick={doCommit}
            style={{ flex: 1 }}>
            {busy === 'commit' ? 'committing…' : 'commit ↵'}
          </button>
          <button
            className="btn"
            disabled={busy !== '' || !branch}
            onClick={doPush}>
            {busy === 'push' ? 'pushing…' : ('push ↑' + (ahead ? ahead : ''))}
          </button>
        </div>
        {lastResult && (
          <div style={{
            fontSize: 10, padding: '4px 6px', borderRadius: 2,
            background: lastResult.ok ? 'color-mix(in oklch, var(--ok) 12%, transparent)'
                                       : 'color-mix(in oklch, var(--warn) 12%, transparent)',
            color: lastResult.ok ? 'var(--ok)' : 'var(--warn)',
            fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            maxHeight: 80, overflow: 'auto',
          }}>
            <b>{lastResult.kind}{lastResult.ok ? ' ✓' : ' ✗'}</b>
            {lastResult.stdout && '\n' + lastResult.stdout.trim()}
            {lastResult.stderr && '\n' + lastResult.stderr.trim()}
            {lastResult.error && '\n' + lastResult.error}
          </div>
        )}
      </div>
    </div>
  );
};

(window as unknown as { GitPanel: typeof GitPanel }).GitPanel = GitPanel;
