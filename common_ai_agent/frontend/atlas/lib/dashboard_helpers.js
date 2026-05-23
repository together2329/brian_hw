// dashboard_helpers.js — Dashboard openIp payload builder (browser plain script).
// For ES module imports (vitest), see dashboard_helpers.mjs.

(function () {
  function buildOpenIpPayload(row, workflowValue) {
    var wf = workflowValue(row);
    var payload = { id: row.session_id || '', ip: row.ip };
    if (wf) payload.workflow = wf;
    return payload;
  }

  var api = { buildOpenIpPayload: buildOpenIpPayload };

  if (typeof window !== 'undefined') {
    window.AtlasDashboardHelpers = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
