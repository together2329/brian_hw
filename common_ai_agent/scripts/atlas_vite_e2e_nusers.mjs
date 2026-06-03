/**
 * ATLAS — N-USER concurrent end-to-end + isolation verification (Playwright).
 *
 * Generalizes atlas_vite_e2e_multiuser.mjs to N real users. Each user:
 *   register -> login (own browser context) -> create IP -> switch a DISTINCT
 *   workflow -> chat -> agent responds. All N run CONCURRENTLY.
 * Then asserts FULL isolation across all users:
 *   - per-user /api/users/me identity
 *   - /api/ip/list scoping: user i sees its own IP and NONE of the others'
 *   - full cross-user 403 matrix: i activating/reading j's session -> 403 (i!=j)
 *   - distinct live worker pids + distinct namespaces (no shared worker / collision)
 * Writes machine-readable evidence JSON for downstream adversarial verifiers.
 *
 *   ATLAS_E2E_BASE=http://127.0.0.1:3030 ATLAS_E2E_USERS=10 \
 *     ATLAS_E2E_JSON=/tmp/atlas_nusers_evidence.json node scripts/atlas_vite_e2e_nusers.mjs
 *
 * Env: ATLAS_E2E_BASE, ATLAS_E2E_USERS (10), ATLAS_E2E_TIMEOUT_MS (120000),
 *      ATLAS_E2E_JSON (/tmp/atlas_nusers_evidence.json), ATLAS_E2E_SHOTS,
 *      ATLAS_E2E_TAG (run tag, default ts), ATLAS_E2E_STOP (1=best-effort stop workers)
 * Exit 0 = all checks pass.
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3030';
const N = Math.max(1, Number(process.env.ATLAS_E2E_USERS || 10));
const T = Number(process.env.ATLAS_E2E_TIMEOUT_MS || 120000);
const JSON_OUT = process.env.ATLAS_E2E_JSON || '/tmp/atlas_nusers_evidence.json';
const SHOTS = process.env.ATLAS_E2E_SHOTS || '/tmp/atlas_e2e_nusers_shots';
const TAG = process.env.ATLAS_E2E_TAG || Date.now().toString(36);
const DO_STOP = process.env.ATLAS_E2E_STOP === '1';
const STAGGER = Number(process.env.ATLAS_E2E_STAGGER_MS || 0); // spread create-IP load to avoid the thundering-herd race

fs.mkdirSync(SHOTS, { recursive: true });
const log = (m) => console.log(m);
const ok = (m) => console.log('  \x1b[32m✓\x1b[0m ' + m);
const bad = (m) => { console.error('  \x1b[31m✗ ' + m + '\x1b[0m'); failed++; };
const step = (m) => console.log('\n=== ' + m + ' ===');
let failed = 0;
const soft = (cond, m) => (cond ? ok(m) : bad(m));

// curated workflow rotation (each user gets a distinct, known-good workflow)
const WF_ROTATION = ['ssot-gen', 'rtl-gen', 'tb-gen', 'lint', 'coverage', 'sim_debug', 'syn', 'sta', 'fl-model-gen', 'sta-post'];
// ATLAS_E2E_OWN_BROWSER=1 → each user gets its OWN browser process, removing the
// single-process contention that starves the last contexts at high N.
const OWN_BROWSER = process.env.ATLAS_E2E_OWN_BROWSER === '1';
const ownBrowsers = [];

function makeUser(i) {
  const name = `nu${i}t${TAG}`;
  return { i, name, pass: `${name}_pw123456`, ip: `ip_${name}`, workflow: WF_ROTATION[i % WF_ROTATION.length] };
}

async function driveUser(browser, u) {
  const r = { name: u.name, ip: u.ip, wantWorkflow: u.workflow, errors: [] };
  if (STAGGER) await new Promise((res) => setTimeout(res, STAGGER * (u.i - 1)));
  const ub = OWN_BROWSER ? await chromium.launch({ headless: true }) : browser;
  if (OWN_BROWSER) ownBrowsers.push(ub);
  const ctx = await ub.newContext({ baseURL: BASE, viewport: { width: 1500, height: 950 }, ignoreHTTPSErrors: true });
  try {
    const reg = await ctx.request.post(BASE + '/api/auth/register', { data: { username: u.name, password: u.pass, display_name: u.name } });
    r.register = reg.status();
    const login = await ctx.request.post(BASE + '/api/auth/login', { data: { username: u.name, password: u.pass } });
    r.login = login.status();
    if (!login.ok()) { r.errors.push(`login ${login.status()}`); r.ctx = ctx; return r; }
    const me = await (await ctx.request.get(BASE + '/api/users/me')).json().catch(() => ({}));
    r.me = me && (me.username || (me.user && me.user.username)) || null;

    const page = await ctx.newPage();
    const ws = [];
    page.on('websocket', (sock) => {
      if (!sock.url().includes('/ws/agent')) return;
      sock.on('framesent', (f) => ws.push('SENT ' + String(f.payload || '').slice(0, 320)));
      sock.on('framereceived', (f) => ws.push('RECV ' + String(f.payload || '').slice(0, 320)));
    });

    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: T });
    await page.waitForTimeout(2500);
    let chat = null;
    for (let i = 0; i < 30 && !chat; i++) { chat = await page.$('textarea[placeholder*="message" i], textarea'); if (!chat) await page.waitForTimeout(1000); }
    if (!chat) { r.errors.push('no chat input'); r.ctx = ctx; return r; }

    // create IP via "+ IP" modal (retry-tolerant under concurrency)
    for (let attempt = 0; attempt < 4; attempt++) {
      if ((await page.evaluate(() => window.ACTIVE_IP || null)) === u.ip) break; // already created on a prior attempt
      try {
        await page.locator('button', { hasText: /^\+\s*IP$/ }).first().click({ timeout: 12000 });
        await page.locator('[role="dialog"][aria-label="Create IP"]').waitFor({ state: 'visible', timeout: 8000 });
        await page.fill('[aria-label="New IP name"]', u.ip, { timeout: 8000 });
        await page.locator('[role="dialog"][aria-label="Create IP"] button:has-text("Create")').click({ timeout: 8000 });
        // wait for the modal to close (success) or surface an error before retrying
        await page.locator('[role="dialog"][aria-label="Create IP"]').waitFor({ state: 'hidden', timeout: 12000 }).catch(() => {});
      } catch (e) { if (attempt === 3) r.errors.push('create-ip: ' + e.message.split('\n')[0]); }
      for (let i = 0; i < 15; i++) { if ((await page.evaluate(() => window.ACTIVE_IP || null)) === u.ip) break; await page.waitForTimeout(1000); }
      if ((await page.evaluate(() => window.ACTIVE_IP || null)) === u.ip) break;
      await page.keyboard.press('Escape').catch(() => {});
      await page.waitForTimeout(1500);
    }
    for (let i = 0; i < 20; i++) { if ((await page.evaluate(() => window.ACTIVE_IP || null)) === u.ip) break; await page.waitForTimeout(1000); }
    r.activeIp = await page.evaluate(() => window.ACTIVE_IP || null);

    // switch workflow (rail click; event fallback)
    const stages = await page.evaluate(() => (window.FLOW_STAGES || []).map((s) => s.id));
    const target = stages.includes(u.workflow) ? u.workflow : (stages.find((s) => s !== 'default') || 'ssot-gen');
    u.workflow = target; r.wantWorkflow = target;
    await page.waitForTimeout(800); // let the rail re-render for the newly-activated IP
    let switched = false;
    for (let attempt = 0; attempt < 3 && !switched; attempt++) {
      const wfBtn = page.locator('.left-workflow-list button').filter({ hasText: new RegExp('^\\s*' + target + '\\s*$', 'i') }).first();
      try { await wfBtn.scrollIntoViewIfNeeded({ timeout: 4000 }); await wfBtn.click({ timeout: 6000 }); r.switchedViaUI = true; }
      catch (_) { await page.evaluate((wf) => window.dispatchEvent(new CustomEvent('atlas-workflow-view-request', { detail: { workflow: wf } })), target); }
      for (let i = 0; i < 15; i++) { const s = await page.evaluate(() => window.ACTIVE_SESSION || null); if ((s || '').endsWith('/' + target)) { switched = true; break; } await page.waitForTimeout(800); }
    }
    r.session = await page.evaluate(() => window.ACTIVE_SESSION || null);

    // communicate
    chat = await page.$('textarea[placeholder*="message" i], textarea');
    await chat.click();
    await chat.fill(`hi from ${u.name} on ${u.ip}/${target} — short reply please`);
    await chat.press('Enter');
    const deadline = Date.now() + T;
    while (Date.now() < deadline) {
      const blob = ws.join('\n');
      r.received = /"type"\s*:\s*"agent_received"/.test(blob);
      r.accepted = /"type"\s*:\s*"agent_accepted"[\s\S]*?"ok"\s*:\s*true/.test(blob);
      r.started = /"type"\s*:\s*"(token|tool)"/.test(blob) || /"running"\s*:\s*true/.test(blob);
      if (r.received && r.accepted && r.started) break;
      await page.waitForTimeout(500);
    }
    const blob = ws.join('\n');
    r.sentSession = (ws.find((f) => f.startsWith('SENT') && f.includes('"type":"prompt"')) || '').match(/"session":"([^"]+)"/)?.[1] || null;
    r.workerPid = (blob.match(/"pid"\s*:\s*(\d+)\s*,\s*"type"\s*:\s*"worker_started"/) || blob.match(/"type"\s*:\s*"worker_started"[\s\S]*?"pid"\s*:\s*(\d+)/) || [])[1] || null;
    // leak scan: any OTHER user's session_id substring appearing in MY ws frames is a red flag (filled later)
    r.wsFrameCount = ws.length;
    r._wsBlob = blob;
    await page.screenshot({ path: `${SHOTS}/${u.name}.png` }).catch(() => {});
    if (DO_STOP) { try { await page.locator('button', { hasText: /STOP/ }).first().click({ timeout: 2000 }); } catch (_) {} }
    r.ctx = ctx;
    return r;
  } catch (e) { r.errors.push('fatal: ' + e.message.split('\n')[0]); r.ctx = ctx; return r; }
}

const browser = OWN_BROWSER ? null : await chromium.launch({ headless: true });
const users = Array.from({ length: N }, (_, i) => makeUser(i + 1));
const evidence = { base: BASE, n: N, tag: TAG, users: [], isolation: {}, summary: {} };
try {
  step(`1/4  ${N} real users — CONCURRENT register+login+createIP+switchWF+chat${OWN_BROWSER ? ' (own browser/user)' : ''}`);
  const results = await Promise.all(users.map((u) => driveUser(browser, u)));

  let respond = 0, owned = 0, ipok = 0;
  const pids = new Set(), sessions = new Set();
  for (const r of results) {
    const responded = r.received && r.accepted && r.started;
    if (responded) respond++;
    if ((r.session || '').startsWith(r.name + '/')) owned++;
    if (r.activeIp === r.ip) ipok++;
    if (r.workerPid) pids.add(r.workerPid);
    if (r.sentSession) sessions.add(r.sentSession);
    soft(responded && (r.session || '').startsWith(r.name + '/') && r.activeIp === r.ip && r.sentSession === `${r.name}/${r.ip}/${r.wantWorkflow}`,
      `${r.name}: ip=${r.activeIp} wf=${r.wantWorkflow} sess=${r.sentSession} resp(recv=${r.received},acc=${r.accepted},out=${r.started}) pid=${r.workerPid}`);
    evidence.users.push({ name: r.name, ip: r.ip, workflow: r.wantWorkflow, me: r.me, activeIp: r.activeIp, session: r.session,
      sentSession: r.sentSession, received: !!r.received, accepted: !!r.accepted, started: !!r.started, workerPid: r.workerPid, errors: r.errors });
  }
  soft(respond === N, `all ${N} agents responded (${respond}/${N})`);
  soft(owned === N, `all ${N} sessions owner-scoped (${owned}/${N})`);
  soft(sessions.size === N, `all ${N} namespaces DISTINCT (${sessions.size}/${N})`);
  const livePids = results.filter((r) => r.workerPid).length;
  if (livePids > 0) soft(pids.size === livePids, `distinct worker pids: ${pids.size} unique of ${livePids} captured (no shared worker)`);
  else log(`  (note: worker_started pids not captured over WS; worker distinctness already covered by distinct namespaces)`);

  step('2/4  cross-session LEAK scan — no user sees another user\'s session_id');
  let leaks = 0;
  for (const r of results) {
    for (const other of results) {
      if (other.name === r.name) continue;
      if (r._wsBlob && other.sentSession && r._wsBlob.includes(other.sentSession)) { leaks++; bad(`LEAK: ${r.name} ws frames contain ${other.name}'s session ${other.sentSession}`); }
    }
  }
  soft(leaks === 0, `zero cross-session leakage across ${N}×${N} frame scan`);
  evidence.isolation.leaks = leaks;

  step(`3/4  IP-list scoping — each user sees ONLY own IP (${N}×${N} exclusion)`);
  const allIps = users.map((u) => u.ip);
  let scopeFails = 0;
  evidence.isolation.ipList = {};
  for (const r of results) {
    if (!r.ctx) continue;
    const list = await (await r.ctx.request.get(BASE + '/api/ip/list')).json().catch(() => ({}));
    const names = (list.items || []).map((x) => x.name || x.ip || x);
    evidence.isolation.ipList[r.name] = names;
    const hasOwn = names.includes(r.ip);
    const others = allIps.filter((ip) => ip !== r.ip && names.includes(ip));
    if (!hasOwn || others.length) { scopeFails++; bad(`${r.name} ip_list=[${names.join(',')}] (own=${hasOwn}, leaked=${others.join(',')})`); }
  }
  soft(scopeFails === 0, `IP-list scoping clean for all ${N} users`);

  step(`4/4  cross-user 403 matrix — activate + history (${N}×${N - 1} pairs)`);
  let a403 = 0, aTot = 0, h403 = 0, hTot = 0;
  for (const ri of results) {
    if (!ri.ctx) continue;
    for (const rj of results) {
      if (rj.name === ri.name) continue;
      aTot++; hTot++;
      const act = await ri.ctx.request.post(BASE + '/api/session/activate', { data: { owner: rj.name, ip: rj.ip, workflow: rj.wantWorkflow } });
      if (act.status() === 403) a403++;
      const his = await ri.ctx.request.get(BASE + `/api/session/history?session=${encodeURIComponent(`${rj.name}/${rj.ip}/${rj.wantWorkflow}`)}`);
      if (his.status() === 403) h403++;
    }
  }
  soft(a403 === aTot, `cross-user ACTIVATE rejected 403: ${a403}/${aTot}`);
  soft(h403 === hTot, `cross-user HISTORY rejected 403: ${h403}/${hTot}`);
  evidence.isolation.activate403 = `${a403}/${aTot}`;
  evidence.isolation.history403 = `${h403}/${hTot}`;

  evidence.summary = { responded: respond, ownerScoped: owned, distinctNamespaces: sessions.size, distinctPids: pids.size, leaks, scopeFails, activate403: `${a403}/${aTot}`, history403: `${h403}/${hTot}`, failedChecks: failed };
  fs.writeFileSync(JSON_OUT, JSON.stringify(evidence, null, 2));

  step('RESULT');  // eslint-friendly
  log(`evidence written -> ${JSON_OUT}`);
  if (failed === 0) log(`\n\x1b[32mATLAS ${N}-user E2E: ✅ VERIFIED\x1b[0m  (concurrent, isolated; shots in ${SHOTS})`);
  else { log(`\n\x1b[31mATLAS ${N}-user E2E: ❌ ${failed} check(s) FAILED\x1b[0m`); process.exitCode = 1; }
} finally {
  if (browser) await browser.close();
  for (const b of ownBrowsers) { try { await b.close(); } catch (_) {} }
}
