/**
 * atlas_workspace_orchestrator_chat_shot.mjs — Playwright verification that the
 * WORKSPACE screen CHAT tab shows the orchestrator's rich activity when the
 * workspace is in orchestrator mode.
 *
 * Repro of the bug being fixed: in orchestrator mode the WORKSPACE CHAT tab used
 * to show only "No <workflow> worker transcript yet." (the per-workflow worker
 * transcript path), even though GET /api/orchestrator/chat/messages?ip=<ip>
 * returns 100+ rich rows (assistant / thought / tool / tool_result). This script
 * drives a real browser to the WORKSPACE CHAT tab in orchestrator mode for an IP
 * with orchestrator chat data and asserts the orchestrator activity now renders.
 *
 * Steps: force orchestrator mode (localStorage atlasExecMode) → login admin/1151
 * → land on WORKSPACE → select an IP with orchestrator chat data → open the CHAT
 * tab → screenshot → assert orchestrator text (dispatch/classify/read_/ask_user/
 * assistant replies) appears in the chat feed.
 *
 * Run (server already serving dist/ at :3000):
 *   node scripts/atlas_workspace_orchestrator_chat_shot.mjs
 * Env:
 *   ATLAS_E2E_BASE   base URL              (default http://127.0.0.1:3000)
 *   ATLAS_E2E_IP     IP with orch chat     (default cnt8_en_v1)
 *   ATLAS_ADMIN_USER/PASS  creds           (default admin / 1151)
 *   ATLAS_E2E_SHOTS  screenshot dir        (default scripts/_shots)
 *   ATLAS_E2E_TIMEOUT_MS per-wait timeout  (default 60000)
 * Exit 0 = orchestrator activity visible in WORKSPACE CHAT; non-zero = not found.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3000';
const IP = process.env.ATLAS_E2E_IP || 'cnt8_en_v1';
const USER = process.env.ATLAS_ADMIN_USER || 'admin';
const PASS = process.env.ATLAS_ADMIN_PASS || '1151';
const SHOTS = process.env.ATLAS_E2E_SHOTS || path.join(__dirname, '_shots');
const T = Number(process.env.ATLAS_E2E_TIMEOUT_MS || 60000);

fs.mkdirSync(SHOTS, { recursive: true });
const log = (m) => console.log(m);
const fail = (m) => { console.error('FAIL: ' + m); process.exitCode = 1; throw new Error(m); };

const browser = await chromium.launch({ headless: true });
let ctx;
try {
  ctx = await browser.newContext({ baseURL: BASE, ignoreHTTPSErrors: true, viewport: { width: 1600, height: 1000 } });

  // --- auth: API login (robust) ---
  let authed = false;
  try {
    const r = await ctx.request.post(BASE + '/api/auth/login', { data: { username: USER, password: PASS } });
    if (r.ok()) { authed = true; log(`auth: POST /api/auth/login ${USER} -> ${r.status()}`); }
    else log(`auth: /api/auth/login -> ${r.status()}`);
  } catch (e) { log('auth: api login error ' + e.message); }
  if (!authed) log('auth: NONE — will attempt the login form in-page');

  const page = await ctx.newPage();
  // Seed orchestrator mode in localStorage so the initial execMode state boots
  // orchestrator (the server's exec_mode can still override it on first sync —
  // we re-assert via the EXEC dropdown below to make the test deterministic).
  await page.addInitScript(() => {
    try {
      localStorage.setItem('atlasExecMode', 'orchestrator');
      localStorage.setItem('atlasScreen', 'workspace');
    } catch (_) {}
  });

  const consoleErr = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErr.push(m.text()); });
  page.on('pageerror', (e) => { consoleErr.push('PAGEERROR ' + e.message); });

  // --- 1) render ---
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: T });
  await page.waitForTimeout(2500);

  // login form fallback if still gated
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

  // --- 2) workspace render: IP select present ---
  let ipSelect = null;
  for (let i = 0; i < 25 && !ipSelect; i++) {
    ipSelect = await page.$('select[aria-label="IP ID"], select.dir-select.ip');
    if (!ipSelect) await page.waitForTimeout(800);
  }
  if (!ipSelect) fail('IP select not found — workspace did not render after auth');
  await page.screenshot({ path: SHOTS + '/01_workspace.png' });

  // --- 3) select the target IP ---
  const opts = await page.$$eval('select[aria-label="IP ID"] option', (os) => os.map((o) => o.value));
  log('ip options: ' + JSON.stringify(opts));
  if (!opts.includes(IP)) fail(`IP "${IP}" not in the dropdown for ${USER}`);
  await ipSelect.selectOption(IP);
  await page.waitForTimeout(2500);

  // --- 3b) ensure EXEC = Orchestrator via the top-bar dropdown (the server's
  // exec_mode sync can revert the localStorage seed to Single Worker). ---
  const execSelect = await page.$('select.dir-select.exec');
  if (!execSelect) fail('EXEC mode dropdown not found');
  const execVal = await execSelect.evaluate((el) => el.value);
  log('exec mode before: ' + execVal);
  if (execVal !== 'orchestrator') {
    await execSelect.selectOption('orchestrator');
    await page.waitForTimeout(3500);
  }
  const execAfter = await execSelect.evaluate((el) => el.value);
  log('exec mode after: ' + execAfter);
  if (execAfter !== 'orchestrator') fail('could not switch EXEC mode to orchestrator');

  // --- 4) open the CHAT tab ---
  // The CHAT tab is a <span> with text "chat" in the rail-tabs row.
  const chatTab = await page.$('span:text-is("chat")');
  if (chatTab) { await chatTab.click(); await page.waitForTimeout(800); }
  else log('chat tab span not found by text — assuming chat is the default tab');

  // --- 5) let the orchestrator chat poll populate (poll interval ~2s) ---
  // Read ONLY the chat-feed container so the right-panel chrome (which has its
  // own "ORCHESTRATOR" / "fl-model-gen" labels) can't produce a false positive.
  const readChatText = () => page.evaluate(() => {
    const el = document.querySelector('[data-workspace-chat-content="true"]')
      || document.querySelector('.workspace-chat-scroll');
    return el ? (el.innerText || '') : '';
  });
  const orchHints = ['dispatch_workflow', 'read_pipeline_state', 'classify_failure',
    'ask_user', 'read_artifact', 'fl-model', 'pipeline state', 'blocked at'];
  let chatText = '';
  let matched = [];
  const deadline = Date.now() + T;
  while (Date.now() < deadline) {
    chatText = await readChatText();
    matched = orchHints.filter((h) => chatText.toLowerCase().includes(h.toLowerCase()));
    if (matched.length >= 2) break;
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: SHOTS + '/02_workspace_chat_orchestrator.png', fullPage: false });

  // Whether the OLD dead-end placeholder is still in the chat feed.
  const hasPlaceholder = /No\s+\w+\s+worker transcript yet\./i.test(chatText);

  log('');
  log(`screenshot: ${SHOTS}/02_workspace_chat_orchestrator.png`);
  log(`chat-feed orchestrator-activity hints matched: ${JSON.stringify(matched)}`);
  log(`old "No <workflow> worker transcript yet." placeholder in chat feed: ${hasPlaceholder}`);
  log(`chat-feed text preview: ${JSON.stringify(chatText.slice(0, 400))}`);

  if (matched.length < 2) {
    fail(`orchestrator activity NOT visible in WORKSPACE CHAT feed (matched=${JSON.stringify(matched)})`);
  }
  if (hasPlaceholder) {
    fail('the "No <workflow> worker transcript yet." dead-end is still rendered in the chat feed');
  }

  log('');
  log(`PASS ✅  WORKSPACE CHAT tab shows orchestrator activity for ${IP} (hints: ${matched.join(', ')})`);
  if (consoleErr.length) log(`(note: ${consoleErr.length} console errors, expected 401/403 pre-auth probes)`);
} finally {
  await browser.close();
}
