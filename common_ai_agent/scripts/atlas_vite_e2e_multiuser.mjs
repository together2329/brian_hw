/**
 * ATLAS — MULTI-USER end-to-end verification (Playwright, two isolated browsers).
 *
 * Proves the running ATLAS web app supports multiple REAL users with isolation
 * and concurrency — not just one admin:
 *
 *   register 2 fresh users (real DB rows via POST /api/auth/register)
 *   -> each logs in in its OWN browser context (separate cookie jar)
 *   -> CONCURRENTLY each: create IP -> switch workflow -> chat -> agent responds
 *   -> assert every namespace/prompt is owner-scoped (userA/.. vs userB/..)
 *   ISOLATION (authenticated API on each context):
 *   -> /api/users/me returns the right username per context
 *   -> /api/ip/list is owner-scoped: A sees A's IP and NOT B's IP (and vice-versa)
 *   -> A activating B's session  -> 403 "session owner mismatch"
 *   -> A reading  B's history    -> 403 "session owner mismatch"
 *
 * Run against an already-running multi_user server:
 *   ATLAS_E2E_BASE=http://127.0.0.1:3030 node scripts/atlas_vite_e2e_multiuser.mjs
 *
 * Env: ATLAS_E2E_BASE (http://127.0.0.1:3030), ATLAS_E2E_SHOTS, ATLAS_E2E_TIMEOUT_MS (90000)
 * Exit 0 = PASS, non-zero = FAIL.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3030';
const SHOTS = process.env.ATLAS_E2E_SHOTS || '/tmp/atlas_e2e_multiuser_shots';
const T = Number(process.env.ATLAS_E2E_TIMEOUT_MS || 90000);
const TS = Date.now().toString(36);

fs.mkdirSync(SHOTS, { recursive: true });
const log = (m) => console.log(m);
const ok = (m) => console.log('  \x1b[32m✓\x1b[0m ' + m);
const step = (m) => console.log('\n=== ' + m + ' ===');
let failed = 0;
const soft = (cond, m) => { if (cond) ok(m); else { console.error('  \x1b[31m✗ ' + m + '\x1b[0m'); failed++; } };
const fatal = (m) => { console.error('\x1b[31mFATAL:\x1b[0m ' + m); process.exitCode = 1; throw new Error(m); };

// One user = one browser context = one cookie jar = one identity.
function makeUser(idx) {
  const name = `mu${idx}x${TS}`;
  return { name, pass: `${name}_pw12345`, ip: `ip_${name}`, workflow: idx === 1 ? 'ssot-gen' : 'rtl-gen' };
}

async function driveUser(browser, u) {
  const r = {};
  const ctx = await browser.newContext({ baseURL: BASE, viewport: { width: 1680, height: 1000 }, ignoreHTTPSErrors: true });
  // register (idempotent: 409 if a prior run made it) then login -> cookie in THIS context
  const reg = await ctx.request.post(BASE + '/api/auth/register', { data: { username: u.name, password: u.pass, display_name: u.name } });
  const login = await ctx.request.post(BASE + '/api/auth/login', { data: { username: u.name, password: u.pass } });
  if (!login.ok()) fatal(`${u.name}: login -> ${login.status()} (register was ${reg.status()})`);
  const me = await (await ctx.request.get(BASE + '/api/users/me')).json().catch(() => ({}));
  r.me = (me && (me.username || (me.user && me.user.username))) || null;

  const page = await ctx.newPage();
  const ws = [];
  page.on('websocket', (sock) => {
    if (!sock.url().includes('/ws/agent')) return;
    sock.on('framesent', (f) => ws.push('SENT ' + String(f.payload || '').slice(0, 300)));
    sock.on('framereceived', (f) => ws.push('RECV ' + String(f.payload || '').slice(0, 300)));
  });

  // render + workspace
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: T });
  await page.waitForTimeout(2500);
  let chat = null;
  for (let i = 0; i < 25 && !chat; i++) { chat = await page.$('textarea[placeholder*="message" i], textarea'); if (!chat) await page.waitForTimeout(1000); }
  if (!chat) fatal(`${u.name}: workspace/chat did not render`);

  // create IP via real "+ IP" modal
  const plus = page.locator('button', { hasText: /^\+\s*IP$/ }).first();
  await plus.click({ timeout: 8000 });
  await page.locator('[role="dialog"][aria-label="Create IP"]').waitFor({ state: 'visible', timeout: 8000 });
  await page.fill('[aria-label="New IP name"]', u.ip, { timeout: 8000 });
  await page.locator('[role="dialog"][aria-label="Create IP"] button:has-text("Create")').click();
  for (let i = 0; i < 30; i++) {
    const ai = await page.evaluate(() => window.ACTIVE_IP || null);
    if (ai === u.ip) break;
    await page.waitForTimeout(1000);
  }
  r.activeIpAfterCreate = await page.evaluate(() => window.ACTIVE_IP || null);
  r.sessionAfterCreate = await page.evaluate(() => window.ACTIVE_SESSION || null);

  // switch workflow via the left rail
  const stages = await page.evaluate(() => (window.FLOW_STAGES || []).map((s) => s.id));
  const target = stages.includes(u.workflow) ? u.workflow : (stages.find((s) => s !== 'default') || 'ssot-gen');
  u.workflow = target;
  const wfBtn = page.locator('.left-workflow-list button').filter({ hasText: new RegExp('^\\s*' + target + '\\s*$', 'i') }).first();
  let clicked = false;
  try { await wfBtn.scrollIntoViewIfNeeded({ timeout: 4000 }); await wfBtn.click({ timeout: 6000 }); clicked = true; } catch (_) {}
  if (!clicked) {
    // fallback: the rail dispatches this same event to switchWorkflow()
    await page.evaluate((wf) => window.dispatchEvent(new CustomEvent('atlas-workflow-view-request', { detail: { workflow: wf } })), target);
  }
  r.switchedViaUI = clicked;
  for (let i = 0; i < 30; i++) {
    const s = await page.evaluate(() => window.ACTIVE_SESSION || null);
    if ((s || '').endsWith('/' + target)) break;
    await page.waitForTimeout(800);
  }
  r.sessionAfterSwitch = await page.evaluate(() => window.ACTIVE_SESSION || null);

  // communicate
  chat = await page.$('textarea[placeholder*="message" i], textarea');
  await chat.click();
  await chat.fill(`hi from ${u.name} on ${u.ip}/${target}`);
  await chat.press('Enter');
  const deadline = Date.now() + T;
  let received = false, accepted = false, started = false;
  while (Date.now() < deadline) {
    const blob = ws.join('\n');
    received = /"type"\s*:\s*"agent_received"/.test(blob);
    accepted = /"type"\s*:\s*"agent_accepted"[\s\S]*?"ok"\s*:\s*true/.test(blob);
    started = /"type"\s*:\s*"(token|tool)"/.test(blob) || /"running"\s*:\s*true/.test(blob);
    if (received && accepted && started) break;
    await page.waitForTimeout(500);
  }
  r.chat = { received, accepted, started };
  // confirm the SENT prompt was owner-scoped to THIS user
  r.sentSession = (ws.find((f) => f.startsWith('SENT') && f.includes('"type":"prompt"')) || '').match(/"session":"([^"]+)"/)?.[1] || null;
  await page.screenshot({ path: `${SHOTS}/${u.name}.png` });
  r.ctx = ctx; r.user = u;
  return r;
}

const browser = await chromium.launch({ headless: true });
try {
  const A = makeUser(1), B = makeUser(2);

  step('1/3  two real users — CONCURRENT create-IP + workflow-switch + chat');
  const [ra, rb] = await Promise.all([driveUser(browser, A), driveUser(browser, B)]);

  soft(ra.me === A.name, `userA /api/users/me = ${ra.me} (expected ${A.name})`);
  soft(rb.me === B.name, `userB /api/users/me = ${rb.me} (expected ${B.name})`);
  soft(ra.activeIpAfterCreate === A.ip, `userA created IP "${A.ip}" (active=${ra.activeIpAfterCreate})`);
  soft(rb.activeIpAfterCreate === B.ip, `userB created IP "${B.ip}" (active=${rb.activeIpAfterCreate})`);
  soft((ra.sessionAfterSwitch || '').startsWith(A.name + '/'), `userA session owner-scoped: ${ra.sessionAfterSwitch}`);
  soft((rb.sessionAfterSwitch || '').startsWith(B.name + '/'), `userB session owner-scoped: ${rb.sessionAfterSwitch}`);
  soft(ra.sentSession === `${A.name}/${A.ip}/${A.workflow}`, `userA prompt routed to ${ra.sentSession}`);
  soft(rb.sentSession === `${B.name}/${B.ip}/${B.workflow}`, `userB prompt routed to ${rb.sentSession}`);
  soft(ra.chat.received && ra.chat.accepted && ra.chat.started, `userA agent responded (recv=${ra.chat.received} acc=${ra.chat.accepted} out=${ra.chat.started})`);
  soft(rb.chat.received && rb.chat.accepted && rb.chat.started, `userB agent responded (recv=${rb.chat.received} acc=${rb.chat.accepted} out=${rb.chat.started})`);
  soft(ra.sentSession !== rb.sentSession, `the two users ran in DISTINCT namespaces (no collision)`);

  step('2/3  IP-list scoping — each user sees ONLY their own IPs');
  const aList = await (await ra.ctx.request.get(BASE + '/api/ip/list')).json().catch(() => ({}));
  const bList = await (await rb.ctx.request.get(BASE + '/api/ip/list')).json().catch(() => ({}));
  const aNames = (aList.items || []).map((x) => x.name || x.ip || x);
  const bNames = (bList.items || []).map((x) => x.name || x.ip || x);
  log(`  userA /api/ip/list -> [${aNames.join(', ')}]`);
  log(`  userB /api/ip/list -> [${bNames.join(', ')}]`);
  soft(aNames.includes(A.ip) && !aNames.includes(B.ip), `userA list has ${A.ip}, EXCLUDES ${B.ip}`);
  soft(bNames.includes(B.ip) && !bNames.includes(A.ip), `userB list has ${B.ip}, EXCLUDES ${A.ip}`);

  step('3/3  cross-user access is REJECTED (403)');
  const xActivate = await ra.ctx.request.post(BASE + '/api/session/activate', { data: { owner: B.name, ip: B.ip, workflow: B.workflow } });
  soft(xActivate.status() === 403, `userA activating userB's session -> ${xActivate.status()} (expect 403)`);
  const xHist = await ra.ctx.request.get(BASE + `/api/session/history?session=${encodeURIComponent(`${B.name}/${B.ip}/${B.workflow}`)}`);
  soft(xHist.status() === 403, `userA reading userB's history -> ${xHist.status()} (expect 403)`);
  // sanity: A reading A's own history is allowed
  const ownHist = await ra.ctx.request.get(BASE + `/api/session/history?session=${encodeURIComponent(`${A.name}/${A.ip}/${A.workflow}`)}`);
  soft(ownHist.status() < 400, `userA reading OWN history -> ${ownHist.status()} (expect <400)`);

  step('RESULT');
  if (failed === 0) log(`\n\x1b[32mATLAS multi-user E2E: ✅ VERIFIED\x1b[0m  (users ${A.name} + ${B.name}, concurrent, isolated; shots in ${SHOTS})`);
  else { log(`\n\x1b[31mATLAS multi-user E2E: ❌ ${failed} check(s) FAILED\x1b[0m`); process.exitCode = 1; }
} finally {
  await browser.close();
}
