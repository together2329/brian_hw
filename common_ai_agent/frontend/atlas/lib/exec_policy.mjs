// exec_policy.mjs — ES module twin of exec_policy.js for vitest.

export const EXEC_MODE_SINGLE = 'single-worker';
export const EXEC_MODE_ORCHESTRATOR = 'orchestrator';
const EXEC_MODES = [EXEC_MODE_SINGLE, EXEC_MODE_ORCHESTRATOR];

export function normalizeExecMode(value, fallback = EXEC_MODE_SINGLE) {
  const v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
  if (v === 's' || v === 'sw' || v === 'main' || v === 'single' || v === 'worker' || v === 'serial' || v === 'single worker') {
    return EXEC_MODE_SINGLE;
  }
  if (v === 'o' || v === 'orch' || v === 'multi-worker' || v === 'multi worker' || v === 'orchestrator-mode') {
    return EXEC_MODE_ORCHESTRATOR;
  }
  if (EXEC_MODES.includes(v)) return v;
  return fallback || EXEC_MODE_SINGLE;
}

export function policyFromBootConfig(config = {}) {
  const policy = config.exec_policy || config.policy || {};
  const mode = normalizeExecMode(policy.exec_mode || config.exec_mode, EXEC_MODE_SINGLE);
  return {
    exec_mode: mode,
    initial_workflow: policy.initial_workflow || (mode === EXEC_MODE_ORCHESTRATOR ? 'orchestrator' : 'default'),
    worker_strategy: policy.worker_strategy || (mode === EXEC_MODE_ORCHESTRATOR ? 'workflow-workers' : 'single-main-loop'),
    single_worker_url: policy.single_worker_url || 'http://127.0.0.1:5601',
    preserve_running_on_workflow_switch:
      typeof policy.preserve_running_on_workflow_switch === 'boolean'
        ? policy.preserve_running_on_workflow_switch
        : mode === EXEC_MODE_ORCHESTRATOR,
    allow_orchestrator_namespace:
      typeof policy.allow_orchestrator_namespace === 'boolean'
        ? policy.allow_orchestrator_namespace
        : mode === EXEC_MODE_ORCHESTRATOR,
  };
}

export function mergePolicyResponse(targetConfig = {}, response = {}) {
  const cfg = targetConfig;
  if (response.exec_mode) cfg.exec_mode = normalizeExecMode(response.exec_mode, cfg.exec_mode);
  if (response.policy) cfg.exec_policy = response.policy;
  else {
    cfg.exec_policy = {
      exec_mode: cfg.exec_mode || response.exec_mode,
      initial_workflow: response.initial_workflow,
      worker_strategy: response.worker_strategy,
      single_worker_url: response.single_worker_url,
      preserve_running_on_workflow_switch: response.preserve_running_on_workflow_switch,
      allow_orchestrator_namespace: response.allow_orchestrator_namespace,
    };
  }
  return cfg;
}

export function initialWorkflow(configOrPolicy = {}, execMode = '') {
  const policy = configOrPolicy.initial_workflow
    ? configOrPolicy
    : policyFromBootConfig(configOrPolicy || { exec_mode: execMode });
  return policy.initial_workflow || (normalizeExecMode(execMode || policy.exec_mode) === EXEC_MODE_ORCHESTRATOR ? 'orchestrator' : 'default');
}

export function preserveRunning(configOrPolicy = {}, execMode = '') {
  const hasPolicyValue = Object.prototype.hasOwnProperty.call(
    configOrPolicy,
    'preserve_running_on_workflow_switch',
  );
  const policy = hasPolicyValue
    ? configOrPolicy
    : policyFromBootConfig(configOrPolicy || { exec_mode: execMode });
  return !!policy.preserve_running_on_workflow_switch;
}
