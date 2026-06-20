/**
 * ATLAS Web UI — codex /subagent left-rail lanes, real-browser end-to-end.
 *
 * Drives the actual vite/.tsx app in headless Chromium against a running ATLAS
 * server (launched with CODEX_BRIDGE=1 + multi-agent). Logs in, sends a prompt
 * that makes codex spawn a subagent, then waits for the `subagent` WS frames to
 * reach the browser AND the "Subagents" lane panel to render in the left rail,
 * and screenshots it.
 *
 *   ATLAS_E2E_BASE=http://127.0.0.1:3041 node scripts/verify_subagent_ui_e2e.mjs
 *
 * Env: ATLAS_E2E_BASE, ATLAS_ADMIN_USER/PASS (admin/1151), ATLAS_E2E_SHOTS,
 *      ATLAS_E2E_TURN_MS (real codex turn budget, default 300000), ATLAS_E2E_PROMPT.
 * Exit 0 = PASS.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3041';
const USER = process.env.ATLAS_ADMIN_USER || 'admin';
const PASS = process.env.ATLAS_ADMIN_PASS || '1151';
const SHOTS = process.env.ATLAS_E2E_SHOTS || '/tmp/atlas_subagent_shots';
const T = Number(process.env.ATLAS_E2E_TIMEOUT_MS || 60000);
const TURN_T = Number(process.env.ATLAS_E2E_TURN_MS || 300000);
const PROMPT = process.env.ATLAS_E2E_PROMPT ||
  "Spawn a subagent named 'Adder' (use your multi-agent / spawn_agent capability) " +
  "to compute 2+2 and return only the number. Wait for it, then tell me what it returned.";

fs.mkdirSync(SHOTS, { recursive: true });
const log = (m) => console.log(m);
const fail = (m) => { console.error('FAIL: ' + m); process.exitCode = 1; throw new Error(m); };

const browser = await chromium.launch({ headless: true });
try {
  const ctx = await browser.newContext({ baseURL: BASE, ignoreHTTPSErrors: true });
  try {
    const r = await ctx.request.post(BASE + '/api/auth/login', { data: { username: USER, password: PASS } });
    log(`auth: POST /api/auth/login ${USER} -> ${r.status()}`);
  } catch (e) { log('auth: api login error ' + e.message); }

  const page = await ctx.newPage();
  const ws = [];
  let subagentFrames = 0;
  page.on('websocket', (sock) => {
    if (!sock.url().includes('/ws/agent')) return;
    sock.on('framereceived', (f) => {
      const p = (f.payload || '').toString();
      if (/"type"\s*:\s*"subagent"/.test(p)) { subagentFrames++; ws.push('RECV ' + p.slice(0, 220)); }
    });
  });

  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: T });
  await page.waitForTimeout(3000);
  if (await page.$('input[type=password]')) {
    try {
      await page.fill('input[type=text], input[name=username], input[placeholder*="ser" i]', USER, { timeout: 8000 });
      await page.fill('input[type=password]', PASS, { timeout: 8000 });
      await page.click('button:has-text("Login"), button:has-text("로그인"), button[type=submit]');
      await page.waitForTimeout(3000);
    } catch (e) { log('login form: ' + e.message); }
  }

  let chat = null;
  for (let i = 0; i < 25 && !chat; i++) {
    chat = await page.$('textarea[placeholder*="message" i], [placeholder*="Type a message" i], textarea');
    if (!chat) await page.waitForTimeout(1000);
  }
  if (!chat) fail('chat input not found — workspace did not render after auth');
  await page.screenshot({ path: SHOTS + '/01_workspace.png', fullPage: true });

  await chat.click();
  await chat.fill(PROMPT);
  await chat.press('Enter');
  log(`prompt sent; waiting up to ${TURN_T / 1000}s for codex to spawn a subagent...`);

  const deadline = Date.now() + TURN_T;
  let panel = false;
  while (Date.now() < deadline) {
    panel = await page.evaluate(() =>
      !!document.querySelector('.subagent-lanes-box') || /Subagents/.test(document.body.innerText));
    if (panel && subagentFrames > 0) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(2000);

  await page.screenshot({ path: SHOTS + '/02_full.png', fullPage: true });
  const left = await page.$('.ws-left-panel');
  if (left) await left.screenshot({ path: SHOTS + '/03_left_rail.png' });
  const box = await page.$('.subagent-lanes-box');
  if (box) await box.screenshot({ path: SHOTS + '/04_subagent_panel.png' });

  const dom = await page.evaluate(() => {
    const b = document.querySelector('.subagent-lanes-box');
    return {
      hasPanel: !!b,
      hasText: document.body.innerText.includes('Subagents'),
      panelText: b ? b.innerText.replace(/\s+/g, ' ').slice(0, 600) : '',
    };
  });

  log('\n--- result ---');
  log('subagent WS frames reaching browser: ' + subagentFrames);
  log('DOM .subagent-lanes-box present: ' + dom.hasPanel);
  log('panel text: ' + dom.panelText);
  log('sample subagent frames:\n' + (ws.slice(-8).join('\n') || '(none)'));
  log('screenshots: ' + SHOTS);

  if (subagentFrames === 0) fail('no `subagent` WS frames reached the browser (bridge->WS path)');
  if (!dom.hasPanel && !dom.hasText) fail('Subagents lane panel did not render in the left rail');
  log(`\nPASS ✅  codex /subagent surfaced as left-rail lanes in the real Web UI (frames=${subagentFrames}).`);
} finally {
  await browser.close();
}
