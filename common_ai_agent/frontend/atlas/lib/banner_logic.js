// banner_logic.js — Default-IP banner decision logic.
// Works as both an ES module (vitest/Node) and a plain <script> (browser UMD).

export function shouldShowSelectIpBanner({ workflow, activeIp }) {
  return workflow === 'orchestrator' &&
    (!activeIp || String(activeIp).toLowerCase() === 'default');
}

export const BANNER_TITLE = '⚠ Select an IP';
export const BANNER_DETAIL = 'orchestrator needs a real IP — pick one from the IP_ID dropdown or click + IP at the top to create one. Messages with default are rejected.';

if (typeof window !== 'undefined') {
  window.AtlasBannerLogic = { shouldShowSelectIpBanner, BANNER_TITLE, BANNER_DETAIL };
}
