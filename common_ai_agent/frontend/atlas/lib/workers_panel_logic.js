// workers_panel_logic.js — Workers grid summary + tone helpers (browser plain script).
// For ES module imports (vitest), see workers_panel_logic.mjs.

(function () {
  function summarizeWorkers(list) {
    var total = list.length;
    var upCount = list.filter(function (w) { return String(w.status || '') === 'ok'; }).length;
    return { total: total, upCount: upCount };
  }

  function workerTone(w) {
    var s = String(w.status || '');
    if (s === 'ok' && Number(w.running_count || 0) > 0) return 'active';
    if (s === 'ok') return 'done';
    if (s === 'mismatch') return 'err';
    return 'pending';
  }

  function portFromUrl(url) {
    var m = String(url || '').match(/:(\d+)(?:\/|$)/);
    return m ? m[1] : '';
  }

  var api = {
    summarizeWorkers: summarizeWorkers,
    workerTone: workerTone,
    portFromUrl: portFromUrl,
  };

  if (typeof window !== 'undefined') {
    window.AtlasWorkersLogic = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
