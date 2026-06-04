import type {
  InteractiveWorkerState,
  InteractiveWorkerStatus,
} from './agent-worker-status';

type JsonRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is JsonRecord => (
  typeof value === 'object' && value !== null && !Array.isArray(value)
);

const stringField = (record: JsonRecord, key: string): string => {
  const value = record[key];
  return value == null ? '' : String(value);
};

const numberField = (record: JsonRecord, key: string): number => {
  const value = Number(record[key]);
  return Number.isFinite(value) ? value : 0;
};

const optionalNumberField = (record: JsonRecord, key: string): number | undefined => {
  if (record[key] == null) return undefined;
  const value = Number(record[key]);
  return Number.isFinite(value) ? value : undefined;
};

const optionalStringField = (record: JsonRecord, key: string): string | undefined => {
  if (record[key] == null) return undefined;
  return String(record[key]);
};

const normalizedWorkerState = (rawState: string): InteractiveWorkerState | null => {
  switch (rawState) {
    case 'ready':
    case 'starting':
    case 'capacity_wait':
    case 'switching':
    case 'stopping':
    case 'evicted':
    case 'failed':
      return rawState;
    default:
      return null;
  }
};

const workerStateFromPayload = (
  payload: JsonRecord,
  worker: JsonRecord | null,
): InteractiveWorkerState => {
  const rawState = worker ? stringField(worker, 'state').toLowerCase() : '';
  if (rawState === 'running') return 'ready';
  const knownState = normalizedWorkerState(rawState);
  if (knownState) return knownState;
  if (worker && worker.running === true) return 'ready';
  if (worker && worker.alive === true) return 'ready';
  if (Object.prototype.hasOwnProperty.call(payload, 'worker')) return 'evicted';
  return numberField(payload, 'active_count') > 0 ? 'ready' : 'evicted';
};

export const interactiveWorkerStatusFromPayload = (
  payload: unknown,
): InteractiveWorkerStatus | null => {
  if (!isRecord(payload)) return null;
  const hasStatusPayload = (
    Object.prototype.hasOwnProperty.call(payload, 'active_count') ||
    Object.prototype.hasOwnProperty.call(payload, 'worker') ||
    Object.prototype.hasOwnProperty.call(payload, 'policy')
  );
  if (!hasStatusPayload) return null;

  const rawWorker = payload.worker;
  const worker = isRecord(rawWorker) ? rawWorker : null;
  const rawState = worker ? stringField(worker, 'state').toLowerCase() : '';
  const running = rawState === 'running' || worker?.running === true;

  return {
    policy: stringField(payload, 'policy'),
    single_active_owner: payload.single_active_owner === true,
    max_active: numberField(payload, 'max_active'),
    active_count: numberField(payload, 'active_count'),
    owner: optionalStringField(payload, 'owner'),
    owner_slot: optionalStringField(payload, 'owner_slot'),
    authenticated_owner: optionalStringField(payload, 'authenticated_owner'),
    owner_active_session: optionalStringField(payload, 'owner_active_session'),
    state: workerStateFromPayload(payload, worker),
    alive: worker?.alive === true,
    running,
    pid: optionalNumberField(worker || {}, 'pid'),
    idle_age_sec: optionalNumberField(worker || {}, 'idle_age_sec'),
    error: optionalStringField(worker || {}, 'error'),
  };
};
