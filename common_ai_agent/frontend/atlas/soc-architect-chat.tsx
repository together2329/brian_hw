// soc-architect-chat.tsx — ArchitectChat panel for the soc-architect.tsx family
// (TypeScript migration of soc-architect.jsx, strangler-fig split).
//
// Minimal live chat panel that shares the same WebSocket bridge
// (`window.backend`) as Workspace. Pulled out of soc-architect.jsx so the main
// SocArchitect file stays under control. It reads the shared session helpers
// through window forward-refs (registered by soc-architect-shared.tsx) so there
// is no import-ordering hazard.
//
// Transitional: still bridges to `window.ArchitectChat` at the bottom so the
// (still-live) legacy soc-architect.jsx + app.jsx keep resolving it.
import { useState, useEffect, useRef, useCallback } from 'react';

const g = window as unknown as Record<string, any>;

// Shared helpers owned by soc-architect-shared.tsx; resolved at call time.
const normalizeArchitectSession = (session: unknown): string => g.normalizeArchitectSession(session);
const architectEventMatchesActiveSession = (m: any, opts?: { requireSession?: boolean }): boolean =>
  g.architectEventMatchesActiveSession(m, opts);

interface FeedEntry {
  kind: string;
  text: string;
  tool?: string;
}
interface ArchitectChatProps {
  view?: string;
  selModule?: any;
  selCluster?: any;
  onDiagramPlan?: (text: string) => Promise<any>;
}

// ── ArchitectChat — minimal live chat panel ────────────────────
// Shares the same WebSocket bridge (`window.backend`) as Workspace,
// so prompts go through the same react-loop and tokens stream back.
// Renders only token / reasoning / tool / tool_result events; the
// full feed (with collapsible cards, qcards, slash menu, scope etc.)
// stays on the Workspace screen.
export function ArchitectChat({ view, selModule, selCluster, onDiagramPlan }: ArchitectChatProps) {
  const normalizedView = String(view || 'architect').toLowerCase();
  const isPipelineChat = normalizedView === 'pipeline' || normalizedView === 'orchestrator';
  const [feed, setFeed] = useState<FeedEntry[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [input, setInput] = useState('');
  const bufRef = useRef('');
  const feedRef = useRef<HTMLDivElement | null>(null);
  const jobLogPollRef = useRef<any>(null);

  const replayMessages = useCallback((messages: any[], session: string, path?: string) => {
    const displaySession = normalizeArchitectSession(session) || 'default';
    const rows: FeedEntry[] = [];
    rows.push({
      kind: 'agent',
      text: `[session] loaded .session/${displaySession}${path ? `\n${path}` : ''}`,
    });
    for (const m of messages || []) {
      const role = m.role || '';
      const content = typeof m.content === 'string'
        ? m.content
        : Array.isArray(m.content)
          ? m.content.map((x: any) => typeof x === 'string' ? x : (x && x.text) || '').join('\n')
          : '';
      const text = String(content || '').trim();
      if (!text) continue;
      if (role === 'user') rows.push({ kind: 'user', text });
      else if (role === 'assistant') rows.push({ kind: 'agent', text: text.slice(0, 2400) });
      else if (role === 'tool') rows.push({ kind: 'obs', text: text.slice(0, 1600), tool: m.name || m.tool_call_id || '' });
    }
    setFeed(rows);
  }, []);

  // Subscribe to the live WS once on mount.
  useEffect(() => {
    if (!window.backend || typeof window.backend.subscribe !== 'function') return;
    const subs: Array<() => void> = [];
    subs.push(window.backend.subscribe('token', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      bufRef.current += (m.text || '');
    }));
    subs.push(window.backend.subscribe('reasoning', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      const t = (m.text || '').trim(); if (!t) return;
      setFeed(l => {
        const last = l[l.length - 1];
        if (last && last.kind === 'thought') {
          return [...l.slice(0, -1), { kind: 'thought', text: last.text + '\n' + t }];
        }
        return [...l, { kind: 'thought', text: t }];
      });
    }));
    subs.push(window.backend.subscribe('tool', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      const t = (m.text || '').trim(); if (!t) return;
      // Park any pending tokens before the tool entry.
      const buf = bufRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf }]);
      bufRef.current = '';
      setFeed(l => [...l, { kind: 'action', text: t }]);
    }));
    subs.push(window.backend.subscribe('tool_result', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      const t = (m.text || '').trim(); if (!t) return;
      setFeed(l => [...l, { kind: 'obs', text: t.slice(0, 1200), tool: m.tool || '' }]);
    }));
    const park = () => {
      const buf = bufRef.current;
      if (buf.trim()) setFeed(l => [...l, { kind: 'agent', text: buf }]);
      bufRef.current = '';
    };
    subs.push(window.backend.subscribe('flush', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      park();
    }));
    subs.push(window.backend.subscribe('done', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      park(); setStreaming(false);
    }));
    subs.push(window.backend.subscribe('agent_state', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      if (m.running === false) { park(); setStreaming(false); }
      else if (m.running === true) setStreaming(true);
    }));
    subs.push(window.backend.subscribe('error', (m: any) => {
      if (!architectEventMatchesActiveSession(m, { requireSession: true })) return;
      setFeed(l => [...l, { kind: 'agent', text: `[error] ${m.message || ''}` }]);
      setStreaming(false);
    }));
    return () => subs.forEach(u => { try { u(); } catch (_) {} });
  }, []);

  useEffect(() => {
    const onLoadSession = async (ev: any) => {
      const session = normalizeArchitectSession(ev.detail && ev.detail.session);
      if (!session) return;
      setStreaming(true);
      try {
        const r = await fetch(`/api/session/history?session=${encodeURIComponent(session)}&limit=160`);
        const d = await r.json().catch(() => ({}));
        if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
        if (!d.exists) {
          setFeed([{ kind: 'agent', text: `[session] .session/${session}/conversation.json not found yet` }]);
        } else {
          replayMessages(d.messages || [], session, d.path);
        }
      } catch (e: any) {
        setFeed(l => [...l, { kind: 'agent', text: `[session error] ${e.message || e}` }]);
      } finally {
        setStreaming(false);
      }
    };
    window.addEventListener('atlas:load-session-history', onLoadSession);
    return () => window.removeEventListener('atlas:load-session-history', onLoadSession);
  }, [replayMessages]);

  const replayWorkerLog = useCallback((data: any) => {
    const job = data.job || {};
    const session = normalizeArchitectSession(job.session || '');
    const rows: FeedEntry[] = [{
      kind: 'agent',
      text: `[worker] ${job.ip || '(soc)'} · ${job.workflow || '-'} · ${job.status || data.status || '-'}\n` +
            `job_id: ${job.job_id || '-'}\nrun_id: ${data.run_id || job.run_id || '-'}\n` +
            `session: .session/${session || '-'}`
    }];
    for (const e of data.entries || []) {
      const typ = e.type || '';
      const text = String(e.content || '').trim();
      if (!text) continue;
      if (typ === 'task') rows.push({ kind: 'user', text });
      else if (typ === 'action' || typ === 'tool_call') rows.push({ kind: 'action', text });
      else if (typ === 'observation' || typ === 'tool_result') rows.push({ kind: 'obs', text: text.slice(0, 2200), tool: typ });
      else if (typ === 'error') rows.push({ kind: 'agent', text: `[error] ${text}` });
      else if (typ === 'done' || typ === 'completion') rows.push({ kind: 'agent', text: `[done] ${text}` });
      else if (typ === 'response') rows.push({ kind: 'agent', text: text.slice(0, 2400) });
      else if (typ === 'iteration' || typ === 'system' || typ === 'context') rows.push({ kind: 'thought', text: `[${typ}] ${text}` });
    }
    setFeed(rows);
  }, []);

  useEffect(() => {
    const clearPoll = () => {
      if (jobLogPollRef.current) {
        clearInterval(jobLogPollRef.current);
        jobLogPollRef.current = null;
      }
    };
    const onLoadJobLog = async (ev: any) => {
      const jobId = ev.detail && ev.detail.jobId;
      const live = !!(ev.detail && ev.detail.live);
      if (!jobId) return;
      clearPoll();
      setStreaming(true);
      const loadOnce = async () => {
        try {
          const r = await fetch(`/api/job/${encodeURIComponent(jobId)}/log`);
          const d = await r.json().catch(() => ({}));
          if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
          replayWorkerLog(d);
          if ((d.job || {}).status && (d.job || {}).status !== 'running') {
            clearPoll();
            setStreaming(false);
          }
        } catch (e: any) {
          clearPoll();
          setFeed(l => [...l, { kind: 'agent', text: `[worker log error] ${e.message || e}` }]);
          setStreaming(false);
        }
      };
      await loadOnce();
      if (live) jobLogPollRef.current = setInterval(loadOnce, 2000);
      else setStreaming(false);
    };
    window.addEventListener('atlas:load-job-log', onLoadJobLog);
    return () => {
      clearPoll();
      window.removeEventListener('atlas:load-job-log', onLoadJobLog);
    };
  }, [replayWorkerLog]);

  // Auto-scroll to bottom on new entries.
  useEffect(() => {
    const el = feedRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [feed.length]);

  const send = () => {
    const text = input.trim();
    if (!text) return;
    setFeed(l => [...l, { kind: 'user', text }]);
    setInput('');
    const wantsDiagramPlan =
      /^\/diagram\b/i.test(text) ||
      /^\/(arch|move|mv|connect|cn|add|add-instance|instantiate|delete|del|remove|rm|layout|auto-?layout)\b/i.test(text) ||
      /(diagram|block|connect|move|layout|align|delete|remove|add|배치|정렬|옮겨|움직|연결|추가|삭제|제거|블록|다이어그램)/i.test(text);
    if (wantsDiagramPlan && typeof onDiagramPlan === 'function') {
      setStreaming(true);
      onDiagramPlan(text.replace(/^\/diagram\s*/i, ''))
        .then(res => {
          const notes = (res.notes || []).map((x: string) => `- ${x}`).join('\n');
          setFeed(l => [...l, {
            kind: 'agent',
            text: `[diagram] ${res.summary || 'applied'}\n${notes}`.trim(),
          }]);
        })
        .catch(err => {
          setFeed(l => [...l, { kind: 'agent', text: `[diagram error] ${err.message || err}` }]);
        })
        .finally(() => setStreaming(false));
      return;
    }
    if (isPipelineChat && g.ATLAS_PIPELINE_CHAT_MODE === 'websocket') {
      setStreaming(true);
      const ipName = ((selModule && (selModule.name || selModule.id)) || activeSessionIp || '').trim();
      const policy = (typeof g.pipelinePolicyPayload === 'function')
        ? g.pipelinePolicyPayload()
        : {};
      const outbound = [
        '[ATLAS PIPELINE ORCHESTRATOR CHAT]',
        `- ip: ${ipName || 'active IP'}`,
        `- run_mode: ${policy.run_mode || 'engineering'}`,
        `- exec_mode: ${policy.exec_mode || 'orchestrator'}`,
        `- atlas_api_origin: ${window.location.origin}`,
        '',
        '[DIRECT EXECUTION RULES]',
        '- This right-side Pipeline chat is the real orchestrator control surface.',
        '- Treat /goal as a pipeline goal, not generic todo/plan mode.',
        '- Use read_pipeline_state(ip) for status/evidence reads; do not curl protected /api endpoints.',
        '- For worker/stage/run-to-green requests, call dispatch_workflow directly.',
        '- Do not call todo_add/todo_update/todo_write unless the user explicitly asks for a plan.',
        '- Do not fake pass status; require fresh artifact evidence before reporting success.',
        '',
        text,
      ].join('\n');
      if (window.backend) {
        window.backend.send({
          type: 'prompt',
          text: outbound,
          session: window.ACTIVE_SESSION || '',
          ui_lang: g.ATLAS_UI_LANG || 'en',
        });
      } else {
        setFeed(l => [...l, { kind: 'agent', text: '[error] backend websocket is not connected' }]);
        setStreaming(false);
      }
      return;
    }
    if (isPipelineChat) {
      setStreaming(true);
      const ipName = ((selModule && (selModule.name || selModule.id)) || activeSessionIp || '').trim();
      const policy = (typeof g.pipelinePolicyPayload === 'function')
        ? g.pipelinePolicyPayload()
        : {};
      fetch('/api/pipeline/orchestrator/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          ip: ipName,
          session: window.ACTIVE_SESSION || '',
          session_id: window.ATLAS_USER_SESSION_ID || window.ACTIVE_SESSION || '',
          ...policy,
        }),
      })
        .then(async r => {
          const d = await r.json().catch(() => ({}));
          if (!r.ok || d.error) throw new Error(d.error || `HTTP ${r.status}`);
          const statusLine = d.reply || [
            `orchestrator ${d.status || 'updated'}`,
            d.run_id ? `run_id: ${d.run_id}` : '',
            d.ip ? `ip: ${d.ip}` : '',
          ].filter(Boolean).join('\n');
          setFeed(l => [...l, { kind: 'agent', text: statusLine }]);
          window.dispatchEvent(new CustomEvent('atlas:pipeline-poll', { detail: d }));
          if (d.action === 'dispatch') {
            window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', { detail: d }));
          }
        })
        .catch(err => {
          setFeed(l => [...l, { kind: 'agent', text: `[orchestrator error] ${err.message || err}` }]);
        })
        .finally(() => setStreaming(false));
      return;
    }
    setStreaming(true);
    if (window.backend) {
      window.backend.send({
        type: 'prompt',
        text,
        session: window.ACTIVE_SESSION || '',
        ui_lang: g.ATLAS_UI_LANG || 'en',
      });
    }
  };
  const onKey = (e: any) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const activeSessionIp = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean).slice(-2, -1)[0] || '';
  const scopeLabel = isPipelineChat ? `${(selModule && selModule.name) || activeSessionIp || 'active IP'} · orchestrator`
                   : view === 'soc' ? 'soc · architect'
                   : selModule ? `${selModule.name} · module`
                   : selCluster ? `${selCluster.id} · cluster`
                   : String(view || '').replace(':', ' · ');

  return (
    <div style={{ background: 'var(--panel)', borderLeft: '1px solid var(--line)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="box-h">
        <b>{isPipelineChat ? 'orchestrator chat' : `chat · ${normalizedView}`}</b>
        <span style={{ flex: 1 }} />
        <span className={`pill ${streaming ? 'run' : 'acc'}`} style={{ fontSize: 9 }}>
          {streaming ? 'react-loop · streaming' : 'react-loop · idle'}
        </span>
      </div>

      <div ref={feedRef} style={{ flex: 1, overflow: 'auto', padding: 14, fontSize: 12.5 }}>
        {feed.length === 0 && (
          <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', fontStyle: 'italic', lineHeight: 1.6 }}>
            {isPipelineChat
              ? 'Orchestrator ready. Ask for status, run to green, retry a stage, or create an IP.'
              : 'architect commands: /move cortexa15_0 left, /connect cortexa15_0/M_ACE cci550/S0_ACE ACE, /add counter, /delete counter, /layout.'}
          </div>
        )}
        {feed.map((entry, i) => {
          if (entry.kind === 'user') {
            return (
              <div key={i} style={{ background: 'var(--bg-2)', border: '1px solid var(--line)', padding: '6px 10px', margin: '4px 0 10px', whiteSpace: 'pre-wrap' }}>
                <span className="acc" style={{ fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', marginRight: 6 }}>you</span>
                {entry.text}
              </div>
            );
          }
          if (entry.kind === 'agent') {
            return (
              <div key={i} style={{ padding: '4px 0 10px', whiteSpace: 'pre-wrap', lineHeight: 1.55 }}>
                <span className="ok" style={{ fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', marginRight: 6 }}>agent</span>
                {entry.text}
              </div>
            );
          }
          if (entry.kind === 'thought') {
            return (
              <div key={i} className="react-block thought" style={{ opacity: 0.75 }}>
                <span className="rb-tag">thought</span>
                <span style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</span>
              </div>
            );
          }
          if (entry.kind === 'action') {
            return (
              <div key={i} className="react-block action">
                <span className="rb-tag">tool</span>
                <span style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</span>
              </div>
            );
          }
          if (entry.kind === 'obs') {
            return (
              <div key={i} className="react-block obs">
                <span className="rb-tag">obs{entry.tool ? ` · ${entry.tool}` : ''}</span>
                <span style={{ whiteSpace: 'pre-wrap' }}>{entry.text}</span>
              </div>
            );
          }
          return null;
        })}
      </div>

      <div style={{ padding: 10, borderTop: '1px solid var(--line)', background: 'var(--panel)' }}>
        <div className="prompt-row">
          <span className="ps">›</span>
          <input value={input}
                 onChange={e => setInput(e.target.value)}
                 onKeyDown={onKey}
                 placeholder={isPipelineChat ? "Ask orchestrator…" : "/move · /connect · /add · /delete · /layout"} />
          <span className="kbd" onClick={send} style={{ cursor: 'pointer' }}>↵</span>
        </div>
        <div style={{ marginTop: 6, display: 'flex', gap: 6, fontSize: 10, color: 'var(--fg-mute)', alignItems: 'center' }}>
          <span>scope</span>
          <span className="pill acc" style={{ fontSize: 9 }}>{scopeLabel}</span>
          <span style={{ flex: 1 }} />
          <span><span className="kbd">↵</span> send</span>
        </div>
      </div>
    </div>
  );
}

// ── Transitional bridge so legacy soc-architect.jsx + app.jsx resolve it. ──
g.ArchitectChat = ArchitectChat;
