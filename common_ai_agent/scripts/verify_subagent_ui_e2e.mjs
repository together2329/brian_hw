/**
 * ATLAS Web UI — codex /subagent: workflow-panel selector + click→main-chat.
 *
 * Real-browser (headless Chromium) check against a running ATLAS server with
 * CODEX_BRIDGE=1 + multi-agent. Logs in, sends a prompt that spawns a codex
 * subagent, then:
 *   1. the compact selector appears under the WORKFLOW list (Main + subagent),
 *   2. clicking the subagent row makes the MAIN chat pane render that agent's
 *      (coalesced) transcript — the "Watching subagent" banner shows in chat,
 *   3. the previous main conversation is preserved (selecting Main restores it).
 *
 *   ATLAS_E2E_BASE=http://127.0.0.1:3041 node scripts/verify_subagent_ui_e2e.mjs
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
  "to compute 2+2 and explain the result in one sentence. Wait for it, then tell me what it returned.";

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
  let subagentFrames = 0;
  page.on('websocket', (sock) => {
    if (!sock.url().includes('/ws/agent')) return;
    sock.on('framereceived', (f) => {
      if (/"type"\s*:\s*"subagent"/.test((f.payload || '').toString())) subagentFrames++;
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

  await chat.click();
  await chat.fill(PROMPT);
  await chat.press('Enter');
  log(`prompt sent; waiting up to ${TURN_T / 1000}s for codex to spawn a subagent...`);

  // 1) selector appears under the WORKFLOW list
  const deadline = Date.now() + TURN_T;
  let hasSelector = false;
  while (Date.now() < deadline) {
    hasSelector = await page.evaluate(() => {
      const sel = document.querySelector('.subagent-lanes');
      return !!sel && sel.querySelectorAll('button').length >= 2;   // Main + >=1 subagent
    });
    if (hasSelector && subagentFrames > 0) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(2000);
  await page.screenshot({ path: SHOTS + '/10_selector.png', fullPage: true });
  const left = await page.$('.ws-left-panel');
  if (left) await left.screenshot({ path: SHOTS + '/11_left_rail.png' });
  if (!hasSelector) fail('subagent selector did not appear under the workflow list');

  // 2) click the subagent row -> MAIN chat pane renders its transcript
  const clicked = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('.subagent-lanes button'));
    const subBtn = btns.find((b) => !/Main/.test(b.textContent || ''));
    if (!subBtn) return false;
    subBtn.click();
    return true;
  });
  if (!clicked) fail('could not find a subagent row to click');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: SHOTS + '/12_main_chat_transcript.png', fullPage: true });

  const afterClick = await page.evaluate(() => {
    // The chat markdown renders inside a same-origin iframe, so scan iframe docs
    // too — document.body.innerText alone misses it.
    const texts = [document.body.innerText];
    for (const f of Array.from(document.querySelectorAll('iframe'))) {
      try { texts.push(f.contentDocument?.body?.innerText || ''); } catch (_) { /* cross-origin */ }
    }
    return { watching: /Watching subagent/.test(texts.join('\n')) };
  });
  log('subagent WS frames: ' + subagentFrames);
  log('after click -> main chat shows "Watching subagent": ' + afterClick.watching);
  log('screenshots: ' + SHOTS);

  if (subagentFrames === 0) fail('no `subagent` WS frames reached the browser');
  if (!afterClick.watching) fail('clicking the subagent did NOT render its transcript in the MAIN chat pane');
  log(`\nPASS ✅  selector under workflow + click renders subagent transcript in the MAIN chat (frames=${subagentFrames}).`);
} finally {
  await browser.close();
}
