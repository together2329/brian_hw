// session_routing.mjs — ES module twin of session_routing.js for vitest.

export const DEFAULT_IP = 'default';
export const KNOWN_WORKFLOWS = new Set([
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
  return String(value || '').split('/').map(p => p.trim()).filter(Boolean);
}

export function isRealIp(value) {
  const ip = String(value || '').trim();
  if (!ip || ip === DEFAULT_IP || ip === 'soc' || ip === 'user') return false;
  if (KNOWN_WORKFLOWS.has(ip.toLowerCase())) return false;
  return /^[A-Za-z][A-Za-z0-9_.-]*$/.test(ip);
}

export function sessionIpFromSession(session) {
  const p = parts(session);
  if (p.length >= 3 && isRealIp(p[p.length - 2])) return p[p.length - 2];
  return '';
}

export function sessionRoute(session) {
  const p = parts(session);
  const ip = p.length >= 3 && isRealIp(p[p.length - 2]) ? p[p.length - 2] : '';
  return {
    owner: p[0] || '',
    ip,
    workflow: p.length >= 3 ? (p[p.length - 1] || '') : '',
  };
}

function sameOwner(a, b) {
  return !a || !b || a === b || a === 'local-admin' || b === 'local-admin';
}

export function sessionsShareOwnerIp(a, b) {
  const left = sessionRoute(a);
  const right = sessionRoute(b);
  return !!left.ip && !!right.ip && left.ip === right.ip && sameOwner(left.owner, right.owner);
}

export function healthCountersMatchRoute({
  browserSession = '',
  payloadSession = '',
} = {}) {
  if (!browserSession || !payloadSession || browserSession === payloadSession) return true;
  const browser = sessionRoute(browserSession);
  if (!browser.ip) return true;
  return sessionsShareOwnerIp(browserSession, payloadSession);
}

export function shouldUseBrowserSession({
  browserSession = '',
  payloadSession = '',
} = {}) {
  if (!browserSession || !payloadSession || browserSession === payloadSession) return false;
  const browser = sessionRoute(browserSession);
  const payload = sessionRoute(payloadSession);
  return !!browser.ip && (!payload.ip || browser.ip !== payload.ip || !sameOwner(browser.owner, payload.owner));
}

export function scopeIp(scope) {
  const p = parts(scope);
  const ip = p[p.length - 1] || '';
  return isRealIp(ip) ? ip : '';
}

export function activeIpForRouting({
  sessions = [],
  activeIp = '',
  scopePath = '',
} = {}) {
  for (const session of sessions) {
    const ip = sessionIpFromSession(session);
    if (ip) return ip;
  }
  return scopeIp(activeIp) || scopeIp(scopePath) || '';
}
