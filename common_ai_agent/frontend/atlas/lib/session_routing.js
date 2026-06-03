// session_routing.js — browser helper for Atlas user/IP/workflow routing.
// For ES module imports (vitest), see session_routing.mjs.

(function () {
  var DEFAULT_IP = 'default';
  var KNOWN_WORKFLOWS = new Set([
    'default',
    'orchestrator',
    'ssot-gen',
    'fl-model-gen',
    'rtl-gen',
    'lint',
    'tb-gen',
    'sim',
    'sim_debug',
    'coverage',
    'contract-reflection',
    'syn',
    'sta',
    'pnr',
    'sta-post',
    'goal-audit',
  ]);

  function parts(value) {
    return String(value || '').split('/').map(function (p) { return p.trim(); }).filter(Boolean);
  }

  function isRealIp(value) {
    var ip = String(value || '').trim();
    if (!ip || ip === DEFAULT_IP || ip === 'soc' || ip === 'user') return false;
    if (KNOWN_WORKFLOWS.has(ip.toLowerCase())) return false;
    return /^[A-Za-z][A-Za-z0-9_.-]*$/.test(ip);
  }

  function sessionIpFromSession(session) {
    var p = parts(session);
    if (p.length >= 3 && isRealIp(p[p.length - 2])) return p[p.length - 2];
    return '';
  }

  function sessionRoute(session) {
    var p = parts(session);
    var ip = p.length >= 3 && isRealIp(p[p.length - 2]) ? p[p.length - 2] : '';
    return {
      owner: p[0] || '',
      ip: ip,
      workflow: p.length >= 3 ? (p[p.length - 1] || '') : '',
    };
  }

  function sameOwner(a, b) {
    return !a || !b || a === b || a === 'local-admin' || b === 'local-admin';
  }

  function sessionsShareOwnerIp(a, b) {
    var left = sessionRoute(a);
    var right = sessionRoute(b);
    return !!left.ip && !!right.ip && left.ip === right.ip && sameOwner(left.owner, right.owner);
  }

  function healthCountersMatchRoute(cfg) {
    var browserSession = (cfg && cfg.browserSession) || '';
    var payloadSession = (cfg && cfg.payloadSession) || '';
    if (!browserSession || !payloadSession || browserSession === payloadSession) return true;
    var browser = sessionRoute(browserSession);
    if (!browser.ip) return true;
    return sessionsShareOwnerIp(browserSession, payloadSession);
  }

  function shouldUseBrowserSession(cfg) {
    var browserSession = (cfg && cfg.browserSession) || '';
    var payloadSession = (cfg && cfg.payloadSession) || '';
    if (!browserSession || !payloadSession || browserSession === payloadSession) return false;
    var browser = sessionRoute(browserSession);
    var payload = sessionRoute(payloadSession);
    return !!browser.ip && (!payload.ip || browser.ip !== payload.ip || !sameOwner(browser.owner, payload.owner));
  }

  function scopeIp(scope) {
    var p = parts(scope);
    var ip = p[p.length - 1] || '';
    return isRealIp(ip) ? ip : '';
  }

  function activeIpForRouting(opts) {
    var cfg = opts || {};
    var sessions = Array.isArray(cfg.sessions) ? cfg.sessions : [];
    for (var i = 0; i < sessions.length; i += 1) {
      var ip = sessionIpFromSession(sessions[i]);
      if (ip) return ip;
    }
    return scopeIp(cfg.activeIp) || scopeIp(cfg.scopePath) || '';
  }

  var api = {
    DEFAULT_IP: DEFAULT_IP,
    isRealIp: isRealIp,
    sessionIpFromSession: sessionIpFromSession,
    sessionRoute: sessionRoute,
    sessionsShareOwnerIp: sessionsShareOwnerIp,
    healthCountersMatchRoute: healthCountersMatchRoute,
    shouldUseBrowserSession: shouldUseBrowserSession,
    scopeIp: scopeIp,
    activeIpForRouting: activeIpForRouting,
  };

  if (typeof window !== 'undefined') {
    window.AtlasSessionRouting = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
