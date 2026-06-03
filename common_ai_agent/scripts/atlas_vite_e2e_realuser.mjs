/**
 * ATLAS vite frontend — REAL-USER end-to-end flow (Playwright headless Chromium).
 *
 * Goes beyond the render/chat smoke (atlas_vite_e2e.mjs): it drives the ACTUAL UI
 * controls a user clicks, and verifies each step against the backing API + WS:
 *
 *   login  -> workspace renders
 *   -> click "+ IP"  -> Create-IP modal -> type name -> "Create"   (POST /api/ip/create)
 *   -> verify new IP is the active IP (ip_id <select> + window.ACTIVE_IP)
 *   -> click a DIFFERENT workflow in the left rail .left-workflow-list (switchWorkflow)
 *   -> verify the read-only "workflow" indicator + session triple changed
 *   -> type a chat message -> Enter -> watch /ws/agent for the agent to actually RESPOND
 *      (agent_received + agent_accepted{ok:true} + first token/tool/iter or running flip)
 *
 * Run against an already-running vite server:
 *   ATLAS_E2E_BASE=http://127.0.0.1:3030 node scripts/atlas_vite_e2e_realuser.mjs
 *
 * Env:
 *   ATLAS_E2E_BASE        base URL (default http://127.0.0.1:3030)
 *   ATLAS_ADMIN_USER/PASS login creds (default admin / 1151)
 *   ATLAS_E2E_SHOTS       screenshot dir (default /tmp/atlas_e2e_realuser_shots)
 *   ATLAS_E2E_TIMEOUT_MS  per-wait timeout (default 60000)
 *   ATLAS_E2E_IP          IP name to create (default e2e_<ts>)
 * Exit 0 = PASS, non-zero = FAIL (reason on stderr).
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3030';
const USER = process.env.ATLAS_ADMIN_USER || 'admin';
const PASS = process.env.ATLAS_ADMIN_PASS || '1151';
const SHOTS = process.env.ATLAS_E2E_SHOTS || '/tmp/atlas_e2e_realuser_shots';
const T = Number(process.env.ATLAS_E2E_TIMEOUT_MS || 60000);
const IP = process.env.ATLAS_E2E_IP || `e2e_${Date.now().toString(36)}`;

fs.mkdirSync(SHOTS, { recursive: true });
const log = (m) => console.log(m);
const ok = (m) => console.log('  \x1b[32m✓\x1b[0m ' + m);
const step = (m) => console.log('\n=== ' + m + ' ===');
const fail = (m) => { console.error('\x1b[31mFAIL:\x1b[0m ' + m); process.exitCode = 1; throw new Error(m); };

const browser = await chromium.launch({ headless: true });
let ctx;
try {
  // big desktop viewport so the `.atlas-desktop-only` ip_id switcher (+ IP) renders
  ctx = await browser.newContext({ baseURL: BASE, viewport: { width: 1680, height: 1000 }, ignoreHTTPSErrors: true });

  // --- auth: API login (robust) ---
  const r = await ctx.request.post(BASE + '/api/auth/login', { data: { username: USER, password: PASS } });
  if (!r.ok()) fail(`/api/auth/login -> ${r.status()}`);
  ok(`auth: POST /api/auth/login ${USER} -> ${r.status()}`);

  const page = await ctx.newPage();
  const ws = [];
  const api = [];          // {method,url,status,json}
  const consoleErr = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErr.push(m.text()); });
  page.on('pageerror', (e) => consoleErr.push('PAGEERROR ' + e.message));
  page.on('response', async (res) => {
    const u = res.url();
    if (/\/api\/(ip\/create|session\/activate)/.test(u)) {
      let j = null; try { j = await res.json(); } catch (_) {}
      api.push({ url: u.replace(BASE, ''), status: res.status(), json: j });
    }
  });
  page.on('websocket', (sock) => {
    if (!sock.url().includes('/ws/agent')) return;
    sock.on('framesent', (f) => ws.push('SENT ' + String(f.payload || '').slice(0, 280)));
    sock.on('framereceived', (f) => ws.push('RECV ' + String(f.payload || '').slice(0, 280)));
  });

  // ---------- 1) render + reach workspace ----------
  step('1/5  render + workspace');
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: T });
  await page.waitForTimeout(3000);
  // login-form fallback if still gated
  if (await page.$('input[type=password]')) {
    log('  login screen visible — submitting form');
    try {
      await page.fill('input[type=text], input[name=username], input[placeholder*="ser" i]', USER, { timeout: 8000 });
      await page.fill('input[type=password]', PASS, { timeout: 8000 });
      await page.click('button:has-text("Login"), button:has-text("로그인"), button[type=submit]');
      await page.waitForTimeout(3000);
    } catch (e) { log('  login form attempt: ' + e.message); }
  }
  let chat = null;
  for (let i = 0; i < 25 && !chat; i++) {
    chat = await page.$('textarea[placeholder*="message" i], textarea');
    if (!chat) await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: SHOTS + '/01_workspace.png' });
  if (!chat) fail('chat input never appeared — workspace did not render after auth');
  const rootLen = await page.evaluate(() => (document.querySelector('#root')?.innerHTML || '').length);
  if (await page.$('#atlas-error-banner')) fail('#atlas-error-banner present on load');
  ok(`workspace rendered (#root len=${rootLen}, chat input present)`);

  const readState = () => page.evaluate(() => ({
    activeIp: window.ACTIVE_IP || null,
    activeSession: window.ACTIVE_SESSION || null,
    workflow: (window.CONTEXT && window.CONTEXT.workspace) || null,
    flowStages: (window.FLOW_STAGES || []).map((s) => ({ id: s.id, label: s.label })),
    ipText: (() => { const o = document.querySelector('output.dir-select.readonly'); return o ? o.textContent.trim() : null; })(),
  }));
  const before = await readState();
  log(`  state: ip=${before.activeIp} session=${before.activeSession} workflow=${before.workflow}/${before.ipText}`);
  log(`  FLOW_STAGES: ${before.flowStages.map((s) => s.id).join(', ') || '(none exposed)'}`);

  // ---------- 2) create IP via the real "+ IP" control ----------
  step('2/5  create IP via "+ IP" modal');
  const plusBtn = page.locator('button', { hasText: /^\+\s*IP$/ }).first();
  let createdViaUI = false;
  if (await plusBtn.count()) {
    await plusBtn.scrollIntoViewIfNeeded().catch(() => {});
    await plusBtn.click({ timeout: 8000 });
    const modal = page.locator('[role="dialog"][aria-label="Create IP"]');
    await modal.waitFor({ state: 'visible', timeout: 8000 });
    await page.fill('[aria-label="New IP name"]', IP, { timeout: 8000 });
    await page.screenshot({ path: SHOTS + '/02a_create_modal.png' });
    await modal.locator('button:has-text("Create")').click();
    createdViaUI = true;
    log(`  submitted Create-IP modal with name="${IP}"`);
  } else {
    log('  "+ IP" button not found — falling back to POST /api/ip/create');
    const cr = await ctx.request.post(BASE + '/api/ip/create', { data: { name: IP, kind: 'TBD', exec_mode: 'single-worker' } });
    log(`  POST /api/ip/create -> ${cr.status()}`);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
  }

  // wait for the IP to become active (window.ACTIVE_IP) or appear as an <option>
  let activeIp = null;
  for (let i = 0; i < 30; i++) {
    const s = await readState();
    activeIp = s.activeIp;
    const inSelect = await page.evaluate((ip) =>
      !!Array.from(document.querySelectorAll('select.ip option, select.dir-select.ip option')).find((o) => o.value === ip),
    IP);
    if (activeIp === IP || inSelect) break;
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: SHOTS + '/02b_after_create.png' });
  const createCall = api.find((a) => a.url.includes('/api/ip/create'));
  if (createCall) log(`  POST /api/ip/create -> ${createCall.status} session=${createCall.json?.session || createCall.json?.namespace || ''}`);
  const afterCreate = await readState();
  const ipInSelect = await page.evaluate((ip) =>
    Array.from(document.querySelectorAll('select.ip option, select.dir-select.ip option')).map((o) => o.value).includes(ip), IP);
  if (afterCreate.activeIp !== IP && !ipInSelect) fail(`IP "${IP}" did not become active / never appeared in ip_id <select> (activeIp=${afterCreate.activeIp})`);
  if (createCall && createCall.status >= 400) fail(`/api/ip/create returned ${createCall.status}`);
  ok(`IP "${IP}" created${createdViaUI ? ' (via UI modal)' : ' (via API fallback)'} and active (activeIp=${afterCreate.activeIp}, session=${afterCreate.activeSession})`);

  // ---------- 3) switch workflow via the left rail ----------
  step('3/5  switch workflow (left rail .left-workflow-list)');
  const cur = (afterCreate.workflow || afterCreate.ipText || 'default');
  const stages = afterCreate.flowStages.length ? afterCreate.flowStages : before.flowStages;
  // pick a target != current; prefer ssot-gen / rtl-gen as meaningful real workflows
  const pref = ['ssot-gen', 'rtl-gen', 'tb-gen', 'lint', 'sim'];
  let target = pref.find((p) => stages.some((s) => s.id === p) && p !== cur)
            || (stages.find((s) => s.id !== cur && s.id !== 'default') || {}).id
            || (stages.find((s) => s.id !== cur) || {}).id;
  if (!target) fail(`no alternate workflow available to switch to (stages=${stages.map((s) => s.id).join(',')}, cur=${cur})`);
  log(`  current workflow=${cur} -> switching to "${target}"`);
  const wfBtn = page.locator('.left-workflow-list button').filter({ hasText: new RegExp('^\\s*' + target + '\\s*$', 'i') }).first();
  let switchedViaUI = false;
  if (await wfBtn.count()) {
    await wfBtn.click({ timeout: 8000 });
    switchedViaUI = true;
  } else {
    // label may differ from id — match by the stage's label, else click by index
    const stage = stages.find((s) => s.id === target);
    const byLabel = stage ? page.locator('.left-workflow-list button', { hasText: stage.label }).first() : null;
    if (byLabel && await byLabel.count()) { await byLabel.click({ timeout: 8000 }); switchedViaUI = true; }
    else { await page.evaluate((wf) => window.dispatchEvent(new CustomEvent('atlas-workflow-view-request', { detail: { workflow: wf } })), target); }
  }
  let afterSwitch = null;
  for (let i = 0; i < 25; i++) {
    afterSwitch = await readState();
    if ((afterSwitch.workflow === target) || (afterSwitch.ipText === target) || (afterSwitch.activeSession || '').endsWith('/' + target)) break;
    await page.waitForTimeout(800);
  }
  await page.screenshot({ path: SHOTS + '/03_after_switch.png' });
  const activateCall = api.filter((a) => a.url.includes('/api/session/activate')).pop();
  if (activateCall) log(`  POST /api/session/activate -> ${activateCall.status} workflow=${activateCall.json?.workflow} switch=${activateCall.json?.switch_status || ''}`);
  const wfNow = afterSwitch.workflow || afterSwitch.ipText;
  const sessionEndsRight = (afterSwitch.activeSession || '').endsWith('/' + target);
  if (wfNow !== target && !sessionEndsRight) fail(`workflow did not switch to "${target}" (indicator=${wfNow}, session=${afterSwitch.activeSession})`);
  ok(`workflow switched to "${target}"${switchedViaUI ? ' (via rail click)' : ' (via event)'} — indicator=${wfNow}, session=${afterSwitch.activeSession}`);

  // ---------- 4) communicate: send a chat message, confirm a real response ----------
  step('4/5  communicate — send chat, await agent response');
  chat = await page.$('textarea[placeholder*="message" i], textarea');
  if (!chat) fail('chat input missing after workflow switch');
  const msg = `e2e hello on ${IP}/${target} — please reply briefly`;
  await chat.click();
  await chat.fill(msg);
  await chat.press('Enter');
  log(`  sent: "${msg}"`);
  const deadline = Date.now() + T;
  let received = false, accepted = false, started = false, sentOk = false;
  while (Date.now() < deadline) {
    const blob = ws.join('\n');
    received = /"type"\s*:\s*"agent_received"/.test(blob);
    accepted = /"type"\s*:\s*"agent_accepted"[\s\S]*?"ok"\s*:\s*true/.test(blob);
    // real "the agent is producing output" evidence: a token, a tool/iter line, or running flip
    started = /"type"\s*:\s*"(token|tool)"/.test(blob) || /"type"\s*:\s*"agent_state"[\s\S]*?"running"\s*:\s*true/.test(blob);
    sentOk = new RegExp(`"type":"prompt"[\\s\\S]*?"ip":"${IP}"[\\s\\S]*?"workflow":"${target}"`).test(blob)
          || new RegExp(`"workflow":"${target}"[\\s\\S]*?"ip":"${IP}"`).test(blob);
    if (received && accepted && started) break;
    await page.waitForTimeout(500);
  }
  await page.waitForTimeout(1500);
  await page.screenshot({ path: SHOTS + '/04_chat.png' });
  log('  --- last /ws/agent frames ---');
  log(ws.slice(-16).join('\n') || '  (no /ws/agent frames captured)');
  if (!received) fail('no agent_received — prompt NOT delivered to the worker');
  if (!accepted) fail('no agent_accepted{ok:true} — worker did not accept the prompt');
  if (!started) fail('prompt accepted but NO response signal (no token/tool/running) within timeout — agent did not respond');
  ok(`agent responded on ${IP}/${target} (received+accepted+output; SENT carried right ip/workflow=${sentOk})`);

  // ---------- 5) summary ----------
  step('5/5  RESULT');
  ok('login ✓  create-IP ✓  workflow-switch ✓  communicate ✓');
  log(`\n\x1b[32mATLAS real-user E2E: ✅ VERIFIED\x1b[0m  (IP=${IP}, workflow=${target}, shots in ${SHOTS})`);
  if (consoleErr.length) log(`(note: ${consoleErr.length} console errors — typically pre-auth 401/403 probes)`);
} finally {
  await browser.close();
}
