// banner_logic.mjs — ES module twin of banner_logic.js for vitest.
// The browser loads the .js plain-script version via <script src>; vitest
// imports here so `import { shouldShowSelectIpBanner } from '../lib/banner_logic.mjs'`
// works without dragging in any browser globals.

export function shouldShowSelectIpBanner({ workflow, activeIp } = {}) {
  return workflow === 'orchestrator' &&
    (!activeIp || String(activeIp).toLowerCase() === 'default');
}

export const BANNER_TITLE = '⚠ Select an IP';
export const BANNER_DETAIL = 'orchestrator needs a real IP — pick one from the IP_ID dropdown or click + IP at the top to create one. Messages with default are rejected.';
