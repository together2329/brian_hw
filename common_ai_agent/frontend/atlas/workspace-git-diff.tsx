// workspace-git-diff.tsx — TypeScript migration of the Workspace
// git/diff + file-viewer + footer surfaces (strangler-fig split).
//
// Owns the presentational + lightly-stateful surfaces that sit around the
// chat column: git status glyphs, the static DiffPanel mock, the Office
// docx fallback pane, the per-commit GitDiffPane viewer, the FileViewer
// modal, the OrchestratorWorkflowPane worker dashboard, the
// WorkflowReportPane window bridge, the ConvModeSelector left-column footer
// (with its local Pill), and the terminal-style HotkeyFooter.
//
// Cross-file:
//   - _copyToClipboard            ← ./workspace-markdown-chips
//   - Kbd / DIFF_LINES / atlasData / WorkflowReportPane /
//     workspaceFetchWorkerSnapshot / CONTEXT / SCOPE_PATH / ACTIVE_SESSION
//                                  ← window.* (other ATLAS modules)
//
// The allowed sibling imports (workspace-async-resource / workspace-feed-cards)
// are not needed by this slice's real code — FileViewer fetches via
// window.atlasData.fetchFile rather than useAtlasAsyncResource — so they are
// intentionally not imported (no dead imports).
//
// This .tsx is an INERT mirror — the live app is still served by workspace.jsx.
import { useState, useEffect, useCallback, type ReactNode } from 'react';
import { _copyToClipboard } from './workspace-markdown-chips';
import { appendActiveSessionParam } from './workspace-session-routing';

// `Kbd` is published on window by shared.tsx for not-yet-migrated consumers;
// read it through window here with a permissive cast (it is declared in
// atlas-window.d.ts but we stay decoupled).
const Kbd: any = (window as any).Kbd
  || (({ children }: { children?: ReactNode }) => <span className="kbd">{children}</span>);

// ── Git status glyph table + helper ─────────────────────────────────
export const GIT_STATUS_GLYPH: Record<string, { ch: string; color: string }> = {
  M: { ch: 'M', color: '#d29922' },   // yellow
  A: { ch: 'A', color: '#3fb950' },   // green
  D: { ch: 'D', color: '#f85149' },   // red
  R: { ch: 'R', color: '#a371f7' },   // purple
  '?': { ch: '?', color: 'var(--fg-mute)' },
  ' ': { ch: ' ', color: 'var(--fg-mute)' },
};

export const _statusGlyph = (xy: string) => {
  const a = GIT_STATUS_GLYPH[xy[0]] || GIT_STATUS_GLYPH[' '];
  const b = GIT_STATUS_GLYPH[xy[1]] || GIT_STATUS_GLYPH[' '];
  return { staged: a, work: b };
};

// ── DiffPanel: static in-flight `replace_in_file` mock ──────────────
export const DiffPanel = () => (
  <div className="code" style={{ flex: 1, overflow: 'auto', padding: '12px 14px', fontSize: 12 }}>
    <div className="mute" style={{ marginBottom: 8, fontSize: 11 }}>
      <span className="acc">replace_in_file</span> spi_master/rtl/spi_master.sv
      <span style={{ marginLeft: 12 }} className="ok">+5</span>
      <span style={{ marginLeft: 6 }} className="err">−2</span>
    </div>
    <div style={{ border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
      {(window as any).DIFF_LINES.map((l: any, i: number) => (
        <div key={i} style={{
          display: 'grid', gridTemplateColumns: '36px 14px 1fr', gap: 0, padding: '2px 0',
          background: l.kind === 'add' ? 'rgba(89, 192, 138, 0.10)' :
                       l.kind === 'del' ? 'rgba(232, 112, 112, 0.10)' : 'transparent',
          color: l.kind === 'add' ? 'var(--ok)' : l.kind === 'del' ? 'var(--err)' : 'var(--fg)',
          borderLeft: `2px solid ${l.kind === 'add' ? 'var(--ok)' : l.kind === 'del' ? 'var(--err)' : 'transparent'}`,
        }}>
          <span className="mute" style={{ paddingLeft: 8, fontSize: 10 }}>{l.n}</span>
          <span style={{ fontWeight: 700 }}>{l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' '}</span>
          <span style={{ whiteSpace: 'pre' }}>{l.t}</span>
        </div>
      ))}
    </div>
    <div style={{ marginTop: 12, display: 'flex', gap: 6 }}>
      <button className="btn primary">Accept <Kbd>A</Kbd></button>
      <button className="btn">Reject</button>
    </div>
  </div>
);

// ── DocxFallbackPane: in-tab fallback for unsupported Office formats ─
// Office documents are stored byte-exact under req/imports/originals/. The
// SSOT importer auto-generates a .md sibling for previewing text content.
export const DocxFallbackPane = ({ path, ext }: { path?: string; ext?: string }) => {
  const sibling = (path || '').replace(/\.(docx|pptx|xlsx)$/i, '.md');
  const rawParams = appendActiveSessionParam(new URLSearchParams({ path: path || '' }));
  return (
    <div style={{ padding: 24, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 12, lineHeight: 1.6 }}>
      <div style={{ color: 'var(--fg)', fontSize: 14, fontWeight: 700, marginBottom: 8 }}>
        .{(ext || '').toLowerCase()} preview not supported in-browser
      </div>
      <div>Office documents are stored byte-exact under <code>req/imports/originals/</code>. The SSOT importer auto-generates a <code>.md</code> sibling for previewing the text content.</div>
      <div style={{ marginTop: 10 }}>
        <a href={`/api/file/raw?${rawParams.toString()}`} style={{ color: 'var(--accent)' }}>📥 download original</a>
        {sibling !== path ? (
          <> · try the auto-converted markdown: <code>{sibling}</code></>
        ) : null}
      </div>
    </div>
  );
};

// ── OrchestratorWorkflowPane: worker/orchestrator status dashboard ──
// Polls workspaceFetchWorkerSnapshot (published on window by the legacy
// workspace.jsx) every 3s for the active IP and renders the orchestrator
// summary + per-worker state grid.
export const OrchestratorWorkflowPane = ({ activeIp }: { activeIp?: string }) => {
  const [snapshot, setSnapshot] = useState<any>({ orchestrator: {}, workers: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const ip = String(activeIp || window.SCOPE_PATH || '').trim();

  const refresh = useCallback(async (options: any = {}) => {
    const manual = !!(options && options.manual);
    if (manual) setLoading(true);
    try {
      const j = await (window as any).workspaceFetchWorkerSnapshot({ ip, activeOnly: true, force: manual });
      setSnapshot(j || { orchestrator: {}, workers: [] });
      setError('');
    } catch (e: any) {
      setError(e && e.message ? e.message : String(e));
    } finally {
      if (manual) setLoading(false);
    }
  }, [ip]);

  useEffect(() => {
    let dead = false;
    const run = async () => {
      if (dead) return;
      await refresh();
    };
    run();
    const t = setInterval(run, 3000);
    return () => { dead = true; clearInterval(t); };
  }, [refresh]);

  const orch = snapshot.orchestrator || {};
  const workers = Array.isArray(snapshot.workers) ? snapshot.workers : [];
  const running = workers.filter((w: any) => Number(w.running_count || 0) > 0);
  const queued = workers.filter((w: any) => Number(w.queued_count || 0) > 0);
  const pending = workers.filter((w: any) => Number(w.pending_count || 0) > 0);
  const mismatch = workers.filter((w: any) => w.status === 'mismatch');
  const down = workers.filter((w: any) => w.status && w.status !== 'ok' && w.status !== 'mismatch');
  const stateColor = (w: any) => {
    if (w.status === 'mismatch') return 'var(--warn)';
    if (w.status === 'ok' && Number(w.running_count || 0) > 0) return 'var(--accent)';
    if (w.status === 'ok' && Number(w.pending_count || 0) > 0) return 'var(--warn)';
    if (w.status === 'ok' && Number(w.queued_count || 0) > 0) return 'var(--fg-mute)';
    if (w.status === 'ok' && Number(w.blocked_count || 0) > 0) return 'var(--err)';
    if (w.status === 'ok') return 'var(--ok)';
    return 'var(--err)';
  };
  const stateLabel = (w: any) => {
    if (w.status === 'mismatch') return 'mismatch';
    if (w.status !== 'ok') return w.status || 'down';
    if (Number(w.running_count || 0) > 0) return 'running';
    if (Number(w.pending_count || 0) > 0) return 'starting';
    if (Number(w.queued_count || 0) > 0) return 'queued';
    if (Number(w.blocked_count || 0) > 0) return 'blocked';
    return 'idle';
  };

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'grid', gridTemplateColumns: '300px minmax(0, 1fr)', overflow: 'hidden' }}>
      <div style={{
        minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column',
        borderRight: '1px solid var(--line)', background: 'var(--panel)',
      }}>
        <div style={{ padding: '12px', borderBottom: '1px solid var(--line)' }}>
          <div style={{ fontWeight: 800, fontSize: 12, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Orchestrator</div>
          <div style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, marginTop: 4 }}>
            {orch.model || 'gpt-5.5'} · {orch.reasoning_effort || 'low'} · {orch.enabled ? 'on' : 'off'}
          </div>
        </div>
        <div style={{ padding: 10, borderBottom: '1px solid var(--line)', display: 'grid', gap: 8 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '90px minmax(0, 1fr)', gap: 8, fontFamily: 'var(--mono)', fontSize: 11 }}>
            <span className="mute">IP</span>
            <span className="trunc">{ip || 'global'}</span>
            <span className="mute">target</span>
            <span className="trunc" style={{ color: orch.active_target ? 'var(--accent)' : 'var(--fg-mute)' }}>
              {orch.active_target || 'idle'}
            </span>
            <span className="mute">last</span>
            <span className="trunc">{orch.last_kind || '-'}</span>
            <span className="mute">workers</span>
            <span>{running.length} running · {pending.length} starting · {queued.length} queued · {mismatch.length} mismatch · {down.length} down</span>
          </div>
          <button className="btn" type="button" onClick={() => refresh({ manual: true })} disabled={loading} style={{ padding: '3px 8px', fontSize: 10, justifySelf: 'start' }}>
            refresh
          </button>
          {error && (
            <div style={{ color: 'var(--err)', fontFamily: 'var(--mono)', fontSize: 10 }}>{error}</div>
          )}
        </div>
        <div style={{ padding: 10, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.5 }}>
          <div>profile · {orch.profile || '-'}</div>
          <div>mode · {orch.mode || '-'}</div>
          <div>corr · {orch.active_corr || '-'}</div>
        </div>
      </div>
      <div style={{ minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>
        <div style={{
          display: 'grid', gridTemplateColumns: 'minmax(120px, 1.1fr) 90px minmax(140px, 1fr) minmax(90px, 0.8fr) minmax(120px, 1fr)',
          gap: 10, padding: '8px 12px', borderBottom: '1px solid var(--line)',
          color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10, textTransform: 'uppercase',
        }}>
          <span>workflow</span>
          <span>state</span>
          <span>model</span>
          <span>effort</span>
          <span>url</span>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          {workers.map((w: any) => {
            const reasons = Array.isArray(w.mismatch_reasons) ? w.mismatch_reasons.join('\n') : '';
            return (
              <div key={w.workflow}
                   title={reasons || w.error || w.url || ''}
                   style={{
                     display: 'grid',
                     gridTemplateColumns: 'minmax(120px, 1.1fr) 90px minmax(140px, 1fr) minmax(90px, 0.8fr) minmax(120px, 1fr)',
                     gap: 10, padding: '7px 12px', borderBottom: '1px solid var(--line-2)',
                     alignItems: 'center', fontFamily: 'var(--mono)', fontSize: 11,
                     background: orch.active_target === w.workflow ? 'var(--select)' : 'transparent',
                   }}>
                <span className="trunc" style={{ fontWeight: 700 }}>{w.workflow}</span>
                <span style={{ color: stateColor(w) }}>{stateLabel(w)}</span>
                <span className="trunc">{w.expected_model || w.model || w.worker_health_model || '-'}</span>
                <span className="trunc">{w.expected_reasoning_effort || w.reasoning_effort || '-'}</span>
                <span className="trunc" style={{ color: 'var(--fg-mute)' }}>{w.url || '-'}</span>
              </div>
            );
          })}
          {!workers.length && (
            <div style={{ padding: 16, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 11 }}>
              No worker status loaded.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Phase 13b refactor: WorkflowReportPane lives in frontend/atlas/workflow-report.jsx;
// read it off window (published there).
export const WorkflowReportPane: any = (window as any).WorkflowReportPane;

// ── GitDiffPane: per-commit `git show` diff viewer ──────────────────
// Styled identically to the in-flight `replace_in_file` previews.
export const GitDiffPane = ({ sha, ip, subject, onClose }: {
  sha?: string; ip?: string; subject?: string; onClose?: () => void;
}) => {
  const [body, setBody] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!sha) { setBody(''); return undefined; }
    let cancelled = false;
    setLoading(true); setErr('');
    const ipQ = ip ? `&ip=${encodeURIComponent(ip)}` : '';
    fetch(`/api/git/show?sha=${encodeURIComponent(sha)}${ipQ}`)
      .then(r => r.json())
      .then(d => {
        if (cancelled) return;
        if (d.error) setErr(d.error);
        setBody(String(d.diff || ''));
        setLoading(false);
      })
      .catch(e => {
        if (cancelled) return;
        setErr(String(e));
        setLoading(false);
      });
    return () => { cancelled = true; };
  }, [sha, ip]);
  // Split body into header (commit/author/date/subject) and patch
  // (everything from the first `diff --git` onwards) so the header
  // can be styled differently.
  const splitIdx = body.indexOf('\ndiff --git');
  const header = splitIdx >= 0 ? body.slice(0, splitIdx) : body;
  const patch = splitIdx >= 0 ? body.slice(splitIdx + 1) : '';
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <div style={{
        padding: '6px 14px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 10, fontSize: 'var(--ui-control-font-size)',
        color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
        background: 'var(--bg-2)',
      }}>
        <span className="acc" style={{ fontWeight: 600 }}>{(sha || '').slice(0, 8)}</span>
        {ip && <><span className="mute">·</span><span>{ip}</span></>}
        {subject && <><span className="mute">·</span><span style={{
          color: 'var(--fg)',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          flex: 1, minWidth: 0,
        }}>{subject}</span></>}
        {loading && <span className="mute">loading…</span>}
        <span style={{ flex: 1 }} />
        <span onClick={onClose} title="close diff (back to preview)"
          style={{ cursor: 'pointer', padding: '2px 8px', border: '1px solid var(--line)', borderRadius: 2 }}>
          × close
        </span>
      </div>
      {err && (
        <div style={{
          padding: '6px 14px', color: 'var(--err)', fontFamily: 'var(--mono)',
          fontSize: 'var(--ui-control-font-size)', borderBottom: '1px solid var(--err)',
        }}>{err}</div>
      )}
      <div style={{ flex: 1, overflow: 'auto', background: 'var(--bg-3)' }}>
        {header && (
          <pre style={{
            margin: 0, padding: '10px 14px',
            fontFamily: 'var(--code-font, var(--mono))', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.55,
            color: 'var(--fg-mute)',
            whiteSpace: 'pre-wrap',
            borderBottom: patch ? '1px solid var(--line)' : 'none',
            background: 'var(--bg-2)',
          }}>{header}</pre>
        )}
        {patch ? (
          <pre className="tool-output-pre tool-output-diff language-none" style={{
            margin: 0, padding: '8px 0',
            fontFamily: 'var(--code-font, var(--mono))', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.55,
            background: 'transparent',
          }}>
            {patch.split('\n').map((line, i) => {
              let cls = 'diff-line';
              if (line.startsWith('+') && !line.startsWith('+++')) cls += ' add';
              else if (line.startsWith('-') && !line.startsWith('---')) cls += ' del';
              return <div className={cls} key={i}>{line || ' '}</div>;
            })}
          </pre>
        ) : null}
      </div>
    </div>
  );
};

// ── FileViewer: modal — fetches real content from /api/file ─────────
export const FileViewer = ({ name, onClose }: { name: string; onClose: () => void }) => {
  const [body, setBody] = useState('# loading…');
  const [size, setSize] = useState(0);
  const [truncated, setTruncated] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const ext = (name.split('.').pop() || '').toLowerCase();

  useEffect(() => {
    const onEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onEsc);
    return () => window.removeEventListener('keydown', onEsc);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    setBody('# loading…'); setErr(null);
    window.atlasData.fetchFile(name).then((d: any) => {
      if (cancelled) return;
      if (d.error) {
        setErr(d.error);
        setBody(`// ${name}\n// (could not read: ${d.error})`);
        return;
      }
      setBody(d.content || '');
      setSize(d.size || 0);
      setTruncated(!!d.truncated);
    }).catch((e: any) => {
      if (!cancelled) {
        setErr(String(e));
        setBody(`// ${name}\n// (fetch failed: ${e})`);
      }
    });
    return () => { cancelled = true; };
  }, [name]);

  const lineCount = body.split('\n').length;
  const sizeKb = size > 0 ? (size / 1024).toFixed(1) + ' KB' : '';

  const copyPath = () => {
    _copyToClipboard(name);
  };

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 40,
    }}>
      <div onClick={(e) => e.stopPropagation()} className="box" style={{
        width: 'min(900px, 100%)', height: 'min(680px, 100%)',
        display: 'flex', flexDirection: 'column', background: 'var(--bg)',
        boxShadow: '0 20px 60px rgba(0,0,0,0.45)',
      }}>
        <div className="box-h" style={{ padding: '8px 14px' }}>
          <span style={{ color: 'var(--fg-mute)', marginRight: 6 }}>◆</span>
          <span style={{ color: 'var(--fg)' }}>{name}</span>
          <span className="mute" style={{ marginLeft: 10, textTransform: 'none', letterSpacing: 0, fontSize: 11 }}>
            · {ext || 'file'} · read-only{sizeKb ? ` · ${sizeKb}` : ''}{truncated ? ' · truncated' : ''}
          </span>
          <span style={{ flex: 1 }} />
          <button className="btn" onClick={onClose} style={{ fontSize: 11 }}>Close <Kbd>Esc</Kbd></button>
        </div>
        <pre className="code" style={{
          flex: 1, overflow: 'auto', padding: 16, margin: 0, fontSize: 12, lineHeight: 1.55,
          whiteSpace: 'pre', color: err ? 'var(--warn)' : 'var(--fg)',
        }}>{body}</pre>
        <div style={{ borderTop: '1px solid var(--line)', padding: '8px 14px', display: 'flex', gap: 8, fontSize: 11 }}>
          <span className="mute">{lineCount} lines{truncated ? ' (truncated)' : ''}</span>
          <span style={{ flex: 1 }} />
          <button className="btn" onClick={copyPath}>Copy path</button>
        </div>
      </div>
    </div>
  );
};

// ── ConvModeSelector: conversation hydration mode (left column footer) ──
// Picks which on-disk source the chat feed is rebuilt from on a session
// refresh / page reload. The mode is persisted in localStorage and read by
// data.jsx's refreshSessionState which passes it through as a `mode` query
// param to /api/session/state.
//   • conversation  — last 30 messages from conversation.json. Default.
//   • full          — every message ever (full_conversation.json).
//   • recent        — last 30 messages of full_conversation.json.
export const ConvModeSelector = () => {
  const initial = (() => {
    try { return localStorage.getItem('atlasConversationMode') || 'conversation'; }
    catch (_) { return 'conversation'; }
  })();
  const [mode, setMode] = useState(initial);
  const apply = (next: string) => {
    setMode(next);
    try { localStorage.setItem('atlasConversationMode', next); } catch (_) {}
    if (window.atlasData && window.atlasData.refreshSessionState) {
      window.atlasData.refreshSessionState(window.ACTIVE_SESSION || '', true, { mode: next });
    }
  };
  const Pill = ({ id, label, title }: { id: string; label: string; title?: string }) => (
    <span
      onClick={() => apply(id)}
      title={title}
      style={{
        cursor: 'pointer',
        padding: '2px 6px',
        fontSize: 10,
        fontFamily: 'var(--mono)',
        letterSpacing: '0.02em',
        textTransform: 'uppercase',
        color: mode === id ? 'var(--bg)' : 'var(--fg-mute)',
        background: mode === id ? 'var(--accent)' : 'transparent',
        border: '1px solid ' + (mode === id ? 'var(--accent)' : 'var(--line)'),
        borderRadius: 2,
        whiteSpace: 'nowrap',
        flex: '0 0 auto',
      }}
    >{label}</span>
  );
  return (
    <div style={{
      // Sit a little above the bottom edge of the left column so the
      // pills don't visually merge with the splitter line.
      marginBottom: 24,
      border: '1px solid var(--line)',
      borderRadius: 2,
      padding: '6px 8px',
      fontSize: 10, color: 'var(--fg-mute)',
      display: 'flex', alignItems: 'center', gap: 4,
      // No flexWrap — keep all three pills on one row even in a narrow
      // left column. Drop the "history" label text so the pills get
      // every available pixel without wrapping `full` to a new line.
      flexWrap: 'nowrap',
      overflow: 'hidden',
    }}
    title="Conversation hydration source on session reload">
      <Pill id="conversation" label="recent" title="conversation.json — last 30 chat messages (default)" />
      <Pill id="full"         label="full"   title="every message from full_conversation.json" />
    </div>
  );
};

// ── HotkeyFooter (terminal-style) ───────────────────────────────────
export const HotkeyFooter = ({ intent, streaming }: { intent?: string; streaming?: boolean }) => (
  <div style={{
    display: 'flex', gap: 14, padding: '6px 12px', fontSize: 10,
    color: 'var(--fg-mute)', fontFamily: 'var(--mono)',
    background: 'var(--bg-2)', border: '1px solid var(--line)', borderRadius: 2,
    alignItems: 'center', flexWrap: 'wrap',
  }}>
    <span style={{ color: 'var(--accent)', fontWeight: 600 }}>↑</span>
    <span>{(window.CONTEXT && window.CONTEXT.model) || '—'}</span>
    <span style={{ width: 1, height: 12, background: 'var(--line)' }} />
    <span><Kbd>shift+tab</Kbd> {intent === 'plan' ? 'normal' : 'plan'}</span>
    <span><Kbd>⌫⌫</Kbd> {streaming ? 'interrupt' : 'clear'}</span>
    <span><Kbd>ctrl+c</Kbd> quit</span>
    <span><Kbd>ctrl+j</Kbd> newline</span>
    <span><Kbd>shift+drag</Kbd> copy</span>
    <span><Kbd>shift+insert</Kbd> paste</span>
    <span style={{ flex: 1 }} />
    <span className={streaming ? 'acc' : 'ok'}>{streaming ? 'streaming…' : 'ready'}</span>
  </div>
);
