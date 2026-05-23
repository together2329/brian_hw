// banner_logic.js — Default-IP banner decision logic (browser plain script).
// For ES module imports (vitest), see banner_logic.mjs.

(function () {
  function shouldShowSelectIpBanner(args) {
    args = args || {};
    var workflow = args.workflow;
    var activeIp = args.activeIp;
    return workflow === 'orchestrator' &&
      (!activeIp || String(activeIp).toLowerCase() === 'default');
  }

  var BANNER_TITLE = '⚠ Select an IP';
  var BANNER_DETAIL = 'orchestrator needs a real IP — pick one from the IP_ID dropdown or click + IP at the top to create one. Messages with default are rejected.';

  var api = {
    shouldShowSelectIpBanner: shouldShowSelectIpBanner,
    BANNER_TITLE: BANNER_TITLE,
    BANNER_DETAIL: BANNER_DETAIL,
  };

  if (typeof window !== 'undefined') {
    window.AtlasBannerLogic = api;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})();
