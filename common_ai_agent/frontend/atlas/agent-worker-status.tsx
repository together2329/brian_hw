import type { CSSProperties } from 'react';

export interface WorkerJob {
  readonly job_id?: string;
  readonly run_id?: string;
  readonly worker_workflow?: string;
  readonly workflow?: string;
  readonly ip?: string;
  readonly status?: string;
  readonly queue_reason?: string;
  readonly attempt?: number;
  readonly max_attempts?: number;
  readonly worker_log_entries?: number;
  readonly worker_pid?: number | string;
  readonly session?: string;
  readonly worker?: string;
  readonly worker_log_path?: string;
  readonly result_summary?: string;
  readonly error?: string;
}

export interface WorkerSnapshot {
  readonly url?: string;
  readonly workflow?: string;
  readonly transport?: string;
  readonly status?: string;
  readonly running_count?: number;
  readonly pending_count?: number;
  readonly queued_count?: number;
  readonly blocked_count?: number;
  readonly bound_workflow?: string;
  readonly active_jobs?: readonly WorkerJob[];
}

export interface AtlasWorkersLogicApi {
  readonly portFromUrl: (url?: string) => string;
  readonly workerTone: (worker: WorkerSnapshot) => string;
}

export interface AgentWorkerStatusProps {
  readonly workers: readonly WorkerSnapshot[];
  readonly workersError?: string;
  readonly activeIp?: string;
  readonly agentAlive: boolean;
  readonly agentRunning: boolean;
  readonly execMode: string;
  // Interactive session worker ('agent') status from /api/session/worker/status
  // (Task 7). When undefined the agent row falls back to the legacy
  // agentAlive/agentRunning booleans so pre-Task-7 callers keep rendering.
  readonly interactiveWorker?: InteractiveWorkerStatus | null;
  readonly interactiveWorkerError?: string;
  readonly logic?: AtlasWorkersLogicApi;
  readonly onOpenWorkflow?: (opts: { readonly ip?: string; readonly workflow?: string }) => void;
}

export interface WorkerLiveSummary {
  readonly modeLabel: string;
  readonly stateLabel: string;
  readonly detailLabel: string;
  readonly tone: 'active' | 'ok' | 'warn' | 'err' | 'mute';
}

// ── Interactive session worker (the 'agent') — a DISTINCT concept from the
// orchestrator/job 'workflow workers' (WorkerSnapshot above). Fed by
// GET /api/session/worker/status (Task 7), NOT inferred from
// /api/orchestrator/workers. Wave-3 H10: every state below has a real backend
// producer or is dropped. ──
export type InteractiveWorkerState =
  | 'ready'        // warm_session.status==='ready' (alive, not running)
  | 'starting'     // warm_session.status==='started'
  | 'capacity_wait' // Task 6 warmup refused by max_active cap
  | 'switching'    // worker_switching event (Task 3 owner-slot switch)
  | 'stopping'     // set at terminate_session() start, in list_active_metadata
  | 'evicted'      // worker_evicted (Task 7 idle reaper)
  | 'failed';      // warm_session.status==='error'

export interface InteractiveWorkerStatus {
  readonly policy: string;
  readonly single_active_owner: boolean;
  readonly max_active: number;
  readonly active_count: number;
  // Distinguish the authenticated login from the (possibly model-scoped) slot.
  readonly owner?: string;
  readonly owner_slot?: string;
  readonly authenticated_owner?: string;
  readonly owner_active_session?: string;
  readonly state: InteractiveWorkerState;
  readonly alive: boolean;
  readonly running: boolean;
  readonly pid?: number;
  readonly idle_age_sec?: number;
  readonly error?: string;
}

export interface InteractiveWorkerLine {
  readonly stateLabel: string;
  readonly detailLabel: string;
  readonly tone: WorkerLiveSummary['tone'];
}

// Pure mapping so the 'agent' row is unit-testable in isolation from the
// orchestrator summary. capacity_wait is a WARN (waiting for a slot), never an
// ERR that reads like a backend disconnect (plan Task 8 acceptance).
export const summarizeInteractiveWorker = (
  status: InteractiveWorkerStatus | null,
  statusError = '',
): InteractiveWorkerLine => {
  if (statusError) {
    return { stateLabel: 'status error', detailLabel: statusError, tone: 'err' };
  }
  if (!status) {
    return { stateLabel: 'unavailable', detailLabel: 'agent status unavailable', tone: 'mute' };
  }
  switch (status.state) {
    case 'ready':
      return status.running
        ? { stateLabel: 'running', detailLabel: 'session worker running', tone: 'active' }
        : { stateLabel: 'ready', detailLabel: 'session worker hot', tone: 'ok' };
    case 'starting':
      return { stateLabel: 'starting', detailLabel: 'session worker starting', tone: 'warn' };
    case 'capacity_wait':
      return { stateLabel: 'capacity wait', detailLabel: `waiting for a free worker slot (${status.active_count}/${status.max_active})`, tone: 'warn' };
    case 'switching':
      return { stateLabel: 'switching', detailLabel: 'switching workflow', tone: 'warn' };
    case 'stopping':
      return { stateLabel: 'stopping', detailLabel: 'session worker stopping', tone: 'mute' };
    case 'evicted':
      return { stateLabel: 'idle', detailLabel: 'idle worker evicted; next chat restarts it', tone: 'mute' };
    case 'failed':
      return { stateLabel: 'failed', detailLabel: status.error || 'session worker failed', tone: 'err' };
    default:
      return { stateLabel: 'unavailable', detailLabel: 'agent status unavailable', tone: 'mute' };
  }
};

const numericValue = (value: unknown): number => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

const isWorkerAlive = (worker: WorkerSnapshot): boolean => (
  String(worker.status || '') === 'ok'
  || numericValue(worker.running_count) > 0
  || numericValue(worker.pending_count) > 0
  || numericValue(worker.queued_count) > 0
);

export const summarizeWorkerLive = ({
  workers,
  workersError = '',
  agentAlive,
  agentRunning,
  execMode,
}: Pick<AgentWorkerStatusProps, 'workers' | 'workersError' | 'agentAlive' | 'agentRunning' | 'execMode'>): WorkerLiveSummary => {
  const total = workers.length;
  const running = workers.reduce((sum, worker) => sum + numericValue(worker.running_count), 0);
  const pending = workers.reduce((sum, worker) => sum + numericValue(worker.pending_count), 0);
  const queued = workers.reduce((sum, worker) => sum + numericValue(worker.queued_count), 0);
  const blocked = workers.reduce((sum, worker) => sum + numericValue(worker.blocked_count), 0);
  const alive = workers.filter(isWorkerAlive).length;
  const isSingleWorker = execMode === 'single-worker';

  if (workersError) {
    return {
      modeLabel: isSingleWorker ? 'single' : 'orch',
      stateLabel: 'status error',
      detailLabel: workersError,
      tone: 'err',
    };
  }

  if (isSingleWorker) {
    return {
      modeLabel: 'single',
      stateLabel: agentRunning ? 'running' : agentAlive ? 'alive' : 'not confirmed',
      detailLabel: agentRunning ? 'session worker running' : agentAlive ? 'session worker hot' : 'no session worker ack',
      tone: agentRunning ? 'active' : agentAlive ? 'ok' : 'warn',
    };
  }

  if (total === 0) {
    return {
      modeLabel: 'on demand',
      stateLabel: '0/0 alive',
      detailLabel: 'no active workflow workers',
      tone: 'mute',
    };
  }

  const workParts = [
    running ? `${running} running` : '',
    pending ? `${pending} starting` : '',
    queued ? `${queued} queued` : '',
    blocked ? `${blocked} blocked` : '',
  ].filter(Boolean);
  const transportParts = Array.from(new Set(
    workers.map((worker) => String(worker.transport || '').trim()).filter(Boolean),
  ));

  return {
    modeLabel: transportParts.length === 1 ? transportParts[0] : 'orch',
    stateLabel: `${alive}/${total} alive`,
    detailLabel: workParts.length ? workParts.join(' · ') : 'idle',
    tone: running ? 'active' : alive === total ? 'ok' : alive > 0 ? 'warn' : 'err',
  };
};

const portFromUrl = (url?: string): string => {
  const match = String(url || '').match(/:(\d+)(?:\/|$)/);
  return match ? match[1] : '';
};

const toneForWorker = (worker: WorkerSnapshot, logic?: AtlasWorkersLogicApi): string => {
  const status = String(worker.status || '');
  if (status === 'ok' && numericValue(worker.running_count) > 0) return 'active';
  if (status === 'ok' && numericValue(worker.pending_count) > 0) return 'pending';
  if (status === 'ok' && numericValue(worker.queued_count) > 0) return 'queued';
  return logic ? logic.workerTone(worker) : status === 'ok' ? 'done' : status === 'mismatch' ? 'err' : 'pending';
};

const cfgFor = (tone: string): { readonly color: string; readonly glyph: string; readonly bg: string; readonly border: string } => (
  tone === 'active' ? { color: 'var(--accent)', glyph: '●', bg: 'color-mix(in oklch, var(--accent) 14%, transparent)', border: 'var(--accent)' } :
  tone === 'done' ? { color: 'var(--ok)', glyph: '✓', bg: 'color-mix(in oklch, var(--ok) 12%, transparent)', border: 'var(--ok)' } :
  tone === 'err' ? { color: 'var(--err)', glyph: '✗', bg: 'color-mix(in oklch, var(--err) 14%, transparent)', border: 'var(--err)' } :
  tone === 'queued' ? { color: 'var(--fg-mute)', glyph: '◌', bg: 'color-mix(in oklch, var(--fg-mute) 9%, transparent)', border: 'var(--line)' } :
  { color: 'var(--fg-mute)', glyph: '○', bg: 'transparent', border: 'var(--line)' }
);

const liveToneStyle: Record<WorkerLiveSummary['tone'], CSSProperties> = {
  active: { color: 'var(--accent)' },
  ok: { color: 'var(--ok)' },
  warn: { color: 'var(--warn)' },
  err: { color: 'var(--err)' },
  mute: { color: 'var(--fg-mute)' },
};

const jobLine = (job: WorkerJob): string => [
  job.status || 'running',
  job.queue_reason || '',
  job.attempt && job.max_attempts && Number(job.max_attempts) > 1 ? `try ${job.attempt}/${job.max_attempts}` : '',
  job.worker_log_entries ? `${job.worker_log_entries} log` : '',
  job.worker_pid ? `pid ${job.worker_pid}` : '',
].filter(Boolean).join(' · ');

export const AgentWorkerStatus = ({
  workers,
  workersError = '',
  activeIp = '',
  agentAlive,
  agentRunning,
  execMode,
  interactiveWorker,
  interactiveWorkerError = '',
  logic,
  onOpenWorkflow,
}: AgentWorkerStatusProps) => {
  const summary = summarizeWorkerLive({ workers, workersError, agentAlive, agentRunning, execMode });
  const isSingleWorker = execMode === 'single-worker';
  // Two concepts. The 'agent' (interactive session worker) is driven by the
  // typed interactiveWorker prop when present; otherwise it derives a minimal
  // status from the legacy booleans so nothing regresses pre-Task-7.
  const agentStatus: InteractiveWorkerStatus | null = interactiveWorker !== undefined
    ? interactiveWorker
    : (agentAlive
        ? { policy: '', single_active_owner: isSingleWorker, max_active: 0, active_count: 0, state: 'ready', alive: true, running: agentRunning }
        : null);
  const agentLine = summarizeInteractiveWorker(agentStatus, interactiveWorkerError);
  const activeJobs = workers.flatMap((worker) => (
    Array.isArray(worker.active_jobs)
      ? worker.active_jobs.map((job) => ({ ...job, worker_workflow: job.worker_workflow || worker.workflow }))
      : []
  ));
  const portShort = (worker: WorkerSnapshot) => (logic ? logic.portFromUrl(worker.url) : portFromUrl(worker.url)) || String(worker.workflow || '').slice(0, 4);

  return (
    <>
      <div data-testid="worker-live-summary" style={{ borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)', padding: '7px 0', marginTop: 10, marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
          <span className="mute" style={{ fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 700 }}>Worker Live</span>
          <span className="mute" style={{ fontSize: 9 }}>· {summary.modeLabel}</span>
          <span style={{ flex: 1 }} />
          <span data-testid="worker-live-state" style={{ ...liveToneStyle[summary.tone], fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>{summary.stateLabel}</span>
        </div>
        <div data-testid="worker-live-detail" className="mute" style={{ marginTop: 3, fontSize: 10, fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {summary.detailLabel}
        </div>
      </div>

      <div data-testid="interactive-agent-row" style={{ marginTop: 12, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
        <span className="mute" style={{ fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 700, color: 'var(--accent)' }}>▸ agent</span>
        <span style={{ flex: 1 }} />
        <span data-testid="agent-state" style={{ ...liveToneStyle[agentLine.tone], fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap' }}>{agentLine.stateLabel}</span>
      </div>
      <div data-testid="agent-detail" className="mute" style={{ marginBottom: 10, fontSize: 10, fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {agentLine.detailLabel}
      </div>

      <div className="mute" style={{ fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 6, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap' }}>
        <span style={{ color: 'var(--accent)', fontWeight: 700 }}>▸ workflow workers</span>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>· orchestrator</span>
      </div>

      {workers.length === 0 ? (
        <div data-testid="workflow-workers-empty" className="mute" style={{ fontSize: 10, padding: '4px 0 10px', textAlign: 'center' }}>
          {workersError || 'no active workflow workers'}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4, fontSize: 10, marginBottom: 12 }}>
          {workers.map((worker, index) => {
            const cfg = cfgFor(toneForWorker(worker, logic));
            const label = String(worker.workflow || '').slice(0, 6) || portShort(worker);
            const running = numericValue(worker.running_count);
            const pending = numericValue(worker.pending_count);
            const queued = numericValue(worker.queued_count);
            const active = running || pending || queued;
            return (
              <div key={worker.url || worker.workflow || `worker-${index}`} style={{ border: `1px solid ${cfg.border}`, borderRadius: 2, padding: '4px 6px', textAlign: 'center', background: cfg.bg, fontFamily: 'var(--mono)' }}
                title={`${worker.workflow || '?'}\n${worker.url || ''}\nstatus: ${worker.status || '-'}${running ? `\nrunning jobs: ${running}` : ''}${pending ? `\nstarting jobs: ${pending}` : ''}${queued ? `\nqueued jobs: ${queued}` : ''}${worker.bound_workflow ? `\nbound: ${worker.bound_workflow}` : ''}`}>
                <div style={{ color: cfg.color, fontWeight: 700, fontSize: 10 }}>{cfg.glyph} {label}</div>
                <div className="mute" style={{ fontSize: 9, marginTop: 1 }}>
                  {portShort(worker)}{active ? ` · ${running ? running : pending ? `s${pending}` : `q${queued}`}` : ''}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeJobs.length > 0 ? (
        <div style={{ borderTop: '1px solid var(--line)', paddingTop: 8, marginBottom: 12, fontSize: 10, fontFamily: 'var(--mono)' }}>
          <div className="mute" style={{ fontSize: 9, letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 5 }}>now</div>
          {activeJobs.slice(0, 4).map((job) => (
            <button key={job.job_id || `${job.worker_workflow}-${job.run_id}`} type="button"
              onClick={() => onOpenWorkflow?.({ ip: String(job.ip || activeIp || '').trim(), workflow: job.workflow || job.worker_workflow })}
              title={[job.session || '', job.worker || '', job.worker_log_path ? `log: ${job.worker_log_path}` : '', job.result_summary || job.error || ''].filter(Boolean).join('\n')}
              style={{ width: '100%', display: 'grid', gridTemplateColumns: '12px minmax(0, 1fr)', gap: 6, alignItems: 'start', textAlign: 'left', padding: '4px 0', border: 0, borderBottom: '1px solid color-mix(in oklch, var(--line) 70%, transparent)', background: 'transparent', color: 'var(--fg)', cursor: 'pointer', fontFamily: 'var(--mono)' }}>
              <span style={{ color: job.status === 'queued' ? 'var(--fg-mute)' : 'var(--accent)' }}>{job.status === 'queued' ? '◌' : '▶'}</span>
              <span style={{ minWidth: 0 }}>
                <span style={{ display: 'block', fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{job.workflow || job.worker_workflow || 'worker'}</span>
                <span className="mute" style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{jobLine(job)}</span>
              </span>
            </button>
          ))}
        </div>
      ) : null}
    </>
  );
};
