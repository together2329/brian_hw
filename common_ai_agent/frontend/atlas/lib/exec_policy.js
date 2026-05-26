// exec_policy.js — ATLAS exec-mode policy helper (browser plain script).
// For ES module imports (vitest), see exec_policy.mjs.

(function () {
  var EXEC_MODE_SINGLE = 'single-worker';
  var EXEC_MODE_ORCHESTRATOR = 'orchestrator';
  var EXEC_MODES = [EXEC_MODE_SINGLE, EXEC_MODE_ORCHESTRATOR];

  function normalizeExecMode(value, fallback) {
    var v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
    if (v === 's' || v === 'sw' || v === 'main' || v === 'single' || v === 'worker' || v === 'serial' || v === 'single worker') {
      return EXEC_MODE_SINGLE;
    }
    if (v === 'o' || v === 'orch' || v === 'multi-worker' || v === 'multi worker' || v === 'orchestrator-mode') {
      return EXEC_MODE_ORCHESTRATOR;
    }
    if (EXEC_MODES.indexOf(v) >= 0) return v;
    return fallback || EXEC_MODE_SINGLE;
  }

  function policyFromBootConfig(config) {
    var cfg = config || {};
    var policy = cfg.exec_policy || cfg.policy || {};
    var mode = normalizeExecMode(policy.exec_mode || cfg.exec_mode, EXEC_MODE_SINGLE);
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

  function mergePolicyResponse(targetConfig, response) {
    var cfg = targetConfig || {};
    var data = response || {};
    if (data.exec_mode) cfg.exec_mode = normalizeExecMode(data.exec_mode, cfg.exec_mode);
    if (data.policy) cfg.exec_policy = data.policy;
    else {
      cfg.exec_policy = {
        exec_mode: cfg.exec_mode || data.exec_mode,
        initial_workflow: data.initial_workflow,
        worker_strategy: data.worker_strategy,
        single_worker_url: data.single_worker_url,
        preserve_running_on_workflow_switch: data.preserve_running_on_workflow_switch,
        allow_orchestrator_namespace: data.allow_orchestrator_namespace,
      };
    }
    return cfg;
  }

  function initialWorkflow(configOrPolicy, execMode) {
    var policy = configOrPolicy && configOrPolicy.initial_workflow
      ? configOrPolicy
      : policyFromBootConfig(configOrPolicy || { exec_mode: execMode });
    return policy.initial_workflow || (normalizeExecMode(execMode || policy.exec_mode) === EXEC_MODE_ORCHESTRATOR ? 'orchestrator' : 'default');
  }

  function preserveRunning(configOrPolicy, execMode) {
    var policy = configOrPolicy && Object.prototype.hasOwnProperty.call(configOrPolicy, 'preserve_running_on_workflow_switch')
      ? configOrPolicy
      : policyFromBootConfig(configOrPolicy || { exec_mode: execMode });
    return !!policy.preserve_running_on_workflow_switch;
  }

  var api = {
    EXEC_MODE_SINGLE: EXEC_MODE_SINGLE,
    EXEC_MODE_ORCHESTRATOR: EXEC_MODE_ORCHESTRATOR,
    normalizeExecMode: normalizeExecMode,
    policyFromBootConfig: policyFromBootConfig,
    mergePolicyResponse: mergePolicyResponse,
    initialWorkflow: initialWorkflow,
    preserveRunning: preserveRunning,
  };

  if (typeof window !== 'undefined') {
    window.AtlasExecPolicy = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
