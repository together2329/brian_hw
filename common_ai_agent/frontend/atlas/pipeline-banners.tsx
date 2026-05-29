// pipeline-banners.tsx — TypeScript migration slice of pipeline.tsx.
//
// Extracted from pipeline.tsx (was 1208L) so it drops under 1000. Holds the two
// self-contained polling alert banners shown above the flow map:
//   - PendingQABanner          — polls /api/ssot/qa, surfaces pending QA cards
//   - OrchestratorAskUserBanner — polls /api/orchestrator/active_run, surfaces
//                                 the orchestrator `ask_user` pause
//
// Same permissive house style as the other pipeline-* siblings: cross-file
// window globals are reached through a locally-typed `AtlasGlue` view of window
// so the access type-checks without editing the shared types/atlas-window.d.ts.
// These two banners touch no cross-file globals, so the view is minimal; the
// transitional window.* bridges for these symbols still run in pipeline.tsx in
// the original order.
import { useState, useEffect } from 'react';

// ── PendingQABanner ──────────────────────────────────────────────────────────
interface QAItem {
  status?: string;
  state?: string;
  detail?: string;
  question?: string;
  topic?: string;
  [key: string]: unknown;
}
export interface PendingQABannerProps {
  ip?: string;
}
export function PendingQABanner({ ip }: PendingQABannerProps) {
  const [pending, setPending] = useState(0);
  const [items, setItems] = useState<QAItem[]>([]);
  useEffect(() => {
    if (!ip) { setPending(0); setItems([]); return; }
    let dead = false;
    const fetchQA = async () => {
      try {
        const r = await fetch(`/api/ssot/qa?ip=${encodeURIComponent(ip)}`);
        if (!r.ok) return;
        const j = await r.json();
        if (dead) return;
        const list: QAItem[] = Array.isArray(j.items) ? j.items
                   : Array.isArray(j.pending) ? j.pending
                   : Array.isArray(j.cards) ? j.cards
                   : [];
        const openOnly = list.filter(x => {
          const s = String(x.status || x.state || '').toLowerCase();
          return s === '' || s === 'pending' || s === 'open' || s === 'unanswered';
        });
        setPending(Number(j.pending_count || openOnly.length || 0));
        setItems(openOnly.slice(0, 3));
      } catch (_) {}
    };
    fetchQA();
    const t = setInterval(fetchQA, 5000);
    return () => { dead = true; clearInterval(t); };
  }, [ip]);
  if (!pending) return null;
  return (
    <div className="pipe-qa-banner" role="alert">
      <span className="pipe-qa-icon">⚠</span>
      <span className="pipe-qa-text">
        <b>{pending}</b> QA card{pending > 1 ? 's' : ''} pending — orchestrator paused.{' '}
        Answer to resume.
      </span>
      <a className="pipe-qa-link" href={`/ssot/${encodeURIComponent(ip!)}/qa`}
         target="_blank" rel="noreferrer">Answer QA →</a>
      {items.length > 0 && (
        <div className="pipe-qa-items">
          {items.map((it, i) => (
            <span key={i} className="pipe-qa-chip" title={it.detail || it.question || ''}>
              {String(it.topic || it.question || `Q${i+1}`).slice(0, 36)}
            </span>
          ))}
          {pending > items.length && (
            <span className="pipe-qa-more">+{pending - items.length} more</span>
          )}
        </div>
      )}
    </div>
  );
}

// Phase 3: surface the orchestrator's `ask_user` pause as a visible banner.
// The orchestrator loop persists run.status="paused" and the latest step's
// verdict="awaiting_user" with decision_json.args.question. Until the user
// replies via the right-side chat the run stays paused, so we poll the
// active_run endpoint and render the question prominently.
export interface OrchestratorAskUserBannerProps {
  ip?: string;
}
export function OrchestratorAskUserBanner({ ip }: OrchestratorAskUserBannerProps) {
  const [question, setQuestion] = useState('');
  const [runId, setRunId] = useState('');
  useEffect(() => {
    if (!ip) { setQuestion(''); setRunId(''); return; }
    let dead = false;
    const fetchActive = async () => {
      try {
        const r = await fetch(`/api/orchestrator/active_run?ip=${encodeURIComponent(ip)}`);
        if (!r.ok) return;
        const j = await r.json();
        if (dead) return;
        const run = j.run || null;
        const step = j.latest_step || null;
        const paused = run && run.status === 'paused';
        const awaiting = step && step.verdict === 'awaiting_user';
        if (paused && awaiting) {
          const args = (step.decision_json && step.decision_json.args) || {};
          setQuestion(String(args.question || '').trim());
          setRunId(run.id || '');
        } else {
          setQuestion('');
          setRunId('');
        }
      } catch (_) {}
    };
    fetchActive();
    const t = setInterval(fetchActive, 3000);
    return () => { dead = true; clearInterval(t); };
  }, [ip]);
  if (!question) return null;
  return (
    <div className="pipe-qa-banner" role="alert" data-source="orchestrator-ask-user">
      <span className="pipe-qa-icon">⏸</span>
      <span className="pipe-qa-text">
        <b>Human decision waiting</b> — orchestrator paused: {question}{' '}
        Answer in the right-side chat to resume.
      </span>
      <span className="pipe-qa-more" title={`run=${runId}`}>run {runId.slice(0, 8)}</span>
    </div>
  );
}
