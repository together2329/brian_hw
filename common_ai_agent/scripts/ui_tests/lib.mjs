// Shared helpers for the ATLAS headless-Chrome e2e suite.
// Principle + gotchas: see README.md. No test logic lives here.
import { chromium } from 'playwright';

export const BASE = process.env.BASE || 'http://127.0.0.1:3001';
export const USER = process.env.U || 'admin';
export const PASS = process.env.P || '1151';
export const OUT = '/Users/brian/Desktop/Project/brian_hw/common_ai_agent/.omc/ui-shots';
export const WORKER_MODEL = process.env.WORKER_MODEL || 'deepseek-v4-pro';
// IPs we must never finalize/kill — shared canonical workers / real user data.
export const PROTECTED_IPS = new Set(['default', 'confirmation', 'mctp_axi']);

const NAME = process.env.TEST_NAME || 'test';
export const log = (...a) => console.log(`[${NAME}]`, ...a);

// ── assertions (collect, never throw — so shoot/cleanup still run) ──────────
const _results = [];
export const assert = (cond, msg) => {
  const ok = !!cond;
  _results.push({ ok, msg });
  log(ok ? `✓ ${msg}` : `✗ FAIL ${msg}`);
  return ok;
};
export const assertEq = (actual, expected, msg) =>
  assert(String(actual) === String(expected), `${msg} (got ${JSON.stringify(actual)}, want ${JSON.stringify(expected)})`);
export const results = () => _results.slice();
export const failures = () => _results.filter(r => !r.ok);
export const skip = (msg) => { log(`~ SKIP ${msg}`); };

// ── browser ─────────────────────────────────────────────────────────────────
export async function launch({ viewport = { width: 1600, height: 1000 }, dsf = 2 } = {}) {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: dsf });
  const page = await ctx.newPage();
  page.on('console', m => { if (m.type() === 'error') log('console.error:', m.text().slice(0, 160)); });
  return { browser, ctx, page };
}

export const jget = (page, path) => page.evaluate(async (p) => {
  try { const r = await fetch(p, { credentials: 'include' }); const b = await r.json().catch(() => null); return { status: r.status, body: b }; }
  catch (e) { return { status: 0, body: null, error: String(e) }; }
}, path);

export const jpost = (page, path, body) => page.evaluate(async ({ p, b }) => {
  try { const r = await fetch(p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify(b || {}) }); const j = await r.json().catch(() => null); return { status: r.status, body: j }; }
  catch (e) { return { status: 0, body: null, error: String(e) }; }
}, { p: path, b: body });

export async function login(page, { base = BASE, user = USER, pass = PASS } = {}) {
  await page.goto(base, { waitUntil: 'domcontentloaded' });
  const r = await jpost(page, '/api/auth/login', { username: user, password: pass });
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  return r;
}

export const logout = (page) => jpost(page, '/api/auth/logout', {});

// URL params set the session but land on Dashboard — click the Workspace tab.
export async function gotoWorkspace(page, { base = BASE, user = USER, ip, workflow = 'orchestrator' }) {
  await page.goto(`${base}/?session_id=${user}&ip=${ip}&workflow=${workflow}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,a,span,.dir-btn,[role="tab"]')]
      .find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent || '').trim()) && x.offsetParent !== null);
    if (e) e.click();
  });
  await page.waitForTimeout(2500);
}

export async function pollUntil(fn, { tries = 30, interval = 3000, label = 'condition' } = {}) {
  for (let i = 0; i < tries; i++) {
    const v = await fn(i);
    if (v) { return v; }
    log(`poll ${label} ${i}: not yet`);
    await new Promise(r => setTimeout(r, interval));
  }
  return null;
}

export const findChip = (page) => page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find(x => /worker session for full live detail/i.test(x.getAttribute('title') || ''));
  return b ? b.textContent.trim() : null;
});

export const uniqueIp = (prefix = 'e2e') => `${prefix}_${Date.now().toString(36)}${Math.floor(Math.random() * 1e3)}`;

export async function shoot(page, name, clip) {
  try { await page.screenshot(clip ? { path: `${OUT}/${name}`, clip } : { path: `${OUT}/${name}` }); log('shot', name); }
  catch (e) { log('shot failed', name, e.message); }
}

// In-band stop (no stop API): wakes the run and tells it to finalize.
export async function finalizeRun(page, ip) {
  if (!ip || PROTECTED_IPS.has(String(ip))) { log('cleanup: skip protected/empty ip', ip); return; }
  await jpost(page, '/api/pipeline/orchestrator/chat', {
    message: 'Stop now. Do not dispatch anything else. Finalize this run as blocked immediately.', ip,
  });
  log('finalize sent for', ip);
}

export async function cleanup(page, ips = []) {
  for (const ip of ips) { await finalizeRun(page, ip); await page.waitForTimeout(800); }
}

// Standard exit for a test file: write nothing if all pass; non-zero on any fail.
export function exitCode() { return failures().length ? 1 : 0; }
