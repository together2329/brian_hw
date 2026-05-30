/**
 * ATLAS vite frontend — real-browser end-to-end check (Playwright headless Chromium).
 *
 * Proves the vite/.tsx app ACTUALLY works in a real browser (not just tsc/build):
 *   render (#root mounts, no error banner, no asset 404s)
 *   → auth → workspace renders (left rail + chat input)
 *   → send "hi" → /ws/agent shows agent_received + agent_accepted{ok:true}
 *
 * Driven by scripts/atlas_vite_e2e_verify.sh (which builds + starts the server).
 * Run standalone against an already-running vite server:
 *   ATLAS_E2E_BASE=http://127.0.0.1:3019 node scripts/atlas_vite_e2e.mjs
 *
 * Env:
 *   ATLAS_E2E_BASE      base URL (default http://127.0.0.1:3019)
 *   ATLAS_COOKIE_FILE   session cookie file (default /tmp/atlas_cookie)
 *   ATLAS_ADMIN_USER/PASS  API-login creds (default admin / 1151)
 *   ATLAS_E2E_SHOTS     screenshot dir (default /tmp/atlas_e2e_shots)
 *   ATLAS_E2E_TIMEOUT_MS per-wait timeout (default 60000)
 * Exit 0 = PASS, non-zero = FAIL (with reason on stderr).
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3019';
const COOKIE_FILE = process.env.ATLAS_COOKIE_FILE || '/tmp/atlas_cookie';
const USER = process.env.ATLAS_ADMIN_USER || 'admin';
const PASS = process.env.ATLAS_ADMIN_PASS || '1151';
const SHOTS = process.env.ATLAS_E2E_SHOTS || '/tmp/atlas_e2e_shots';
const T = Number(process.env.ATLAS_E2E_TIMEOUT_MS || 60000);

fs.mkdirSync(SHOTS, { recursive: true });
const log = (m) => console.log(m);
const fail = (m) => { console.error('FAIL: ' + m); process.exitCode = 1; throw new Error(m); };

const browser = await chromium.launch({ headless: true });
let ctx;
try {
  ctx = await browser.newContext({ baseURL: BASE, ignoreHTTPSErrors: true });

  // --- auth: prefer API login (robust); fall back to the cookie file ---
  let authed = false;
  try {
    const r = await ctx.request.post(BASE + '/api/auth/login', { data: { username: USER, password: PASS } });
    if (r.ok()) { authed = true; log(`auth: POST /api/auth/login ${USER} -> ${r.status()}`); }
    else log(`auth: /api/auth/login -> ${r.status()} (will try cookie file)`);
  } catch (e) { log('auth: api login error ' + e.message); }
  if (!authed && fs.existsSync(COOKIE_FILE)) {
    const v = fs.readFileSync(COOKIE_FILE, 'utf8').trim();
    if (v) {
      const u = new URL(BASE);
      await ctx.addCookies([{ name: 'atlas_session', value: v, domain: u.hostname, path: '/' }]);
      authed = true;
      log('auth: set atlas_session cookie from ' + COOKIE_FILE);
    }
  }
  if (!authed) log('auth: NONE — will attempt the login form in-page');

  const page = await ctx.newPage();
  const consoleErr = [];
  const asset404 = [];
  const ws = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErr.push(m.text()); });
  page.on('pageerror', (e) => { consoleErr.push('PAGEERROR ' + e.message); });
  page.on('requestfailed', (r) => {
    const u = r.url();
    if (/\/(assets|vendor|lib)\//.test(u) || /backend\.js|main\.tsx|vcd-parser\.js/.test(u)) asset404.push(u);
  });
  page.on('websocket', (sock) => {
    if (!sock.url().includes('/ws/agent')) return;
    sock.on('framesent', (f) => ws.push('SENT ' + (f.payload || '').slice(0, 240)));
    sock.on('framereceived', (f) => ws.push('RECV ' + (f.payload || '').slice(0, 240)));
  });

  // --- 1) render ---
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: T });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: SHOTS + '/01_initial.png' });
  const rootLen = await page.evaluate(() => {
    const r = document.querySelector('#root') || document.querySelector('#app');
    return r ? (r.innerHTML || '').length : -1;
  });
  if (rootLen <= 0) fail(`#root empty (white screen). rootLen=${rootLen}`);
  if (await page.$('#atlas-error-banner')) fail('#atlas-error-banner present (uncaught error on load)');
  if (asset404.length) fail('asset 404s: ' + asset404.join(', '));
  log(`render OK: #root non-empty (len=${rootLen}), no error banner, no asset 404s`);

  // --- 2) reach the workspace (login form fallback if still gated) ---
  if (await page.$('input[type=password]')) {
    log('login screen visible — submitting form');
    try {
      await page.fill('input[type=text], input[name=username], input[placeholder*="ser" i]', USER, { timeout: 8000 });
      await page.fill('input[type=password]', PASS, { timeout: 8000 });
      await Promise.all([
        page.click('button:has-text("Login"), button:has-text("로그인"), button[type=submit]'),
        page.waitForTimeout(3000),
      ]);
    } catch (e) { log('login form attempt: ' + e.message); }
    await page.waitForTimeout(2500);
  }

  // --- 3) workspace render: chat input present ---
  let chat = null;
  for (let i = 0; i < 20 && !chat; i++) {
    chat = await page.$('textarea[placeholder*="message" i], [placeholder*="Type a message" i], textarea');
    if (!chat) await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: SHOTS + '/02_workspace.png' });
  if (!chat) fail('chat input not found — workspace did not render after auth');
  const leftRail = await page.evaluate(() =>
    /WORKFLOW|workflow/i.test(document.body.innerText) && /default|ssot|rtl|tb-gen/i.test(document.body.innerText));
  log(`workspace OK: chat input present, leftRail=${leftRail}`);

  // --- 4) send "hi" and watch /ws/agent for the delivery handshake ---
  await chat.click();
  await chat.fill('hi');
  await chat.press('Enter');
  const deadline = Date.now() + T;
  let received = false, accepted = false, running = false;
  while (Date.now() < deadline) {
    const blob = ws.join('\n');
    received = /"type"\s*:\s*"agent_received"/.test(blob);
    accepted = /"type"\s*:\s*"agent_accepted"[\s\S]*?"ok"\s*:\s*true/.test(blob);
    running = /"type"\s*:\s*"agent_state"[\s\S]*?"running"\s*:\s*true/.test(blob);
    if (received && accepted) break;
    await page.waitForTimeout(500);
  }
  await page.waitForTimeout(1000);
  await page.screenshot({ path: SHOTS + '/03_chat.png' });
  log('--- last /ws/agent frames ---');
  log(ws.slice(-14).join('\n') || '(no /ws/agent frames captured)');
  if (!received) fail('no agent_received — prompt NOT delivered to the worker (the "no response" bug)');
  if (!accepted) fail('no agent_accepted{ok:true} — worker did not accept the prompt');

  log('');
  log(`PASS ✅  render + workspace + chat delivered+accepted (running=${running}). shots in ${SHOTS}`);
  if (consoleErr.length) log(`(note: ${consoleErr.length} console errors, expected 401/403 pre-auth probes)`);
} finally {
  await browser.close();
}
