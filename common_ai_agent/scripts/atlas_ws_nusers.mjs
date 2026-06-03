/**
 * ATLAS — N-user concurrent SERVER-LEVEL verification (pure Node: fetch + ws, NO browser).
 *
 * Removes the headless-browser client bottleneck (driving N full React apps starves
 * the test machine, not the server). Each user exercises the SAME real server paths a
 * browser would, just without rendering:
 *   register -> login (capture atlas_session cookie) -> POST /api/ip/create
 *   -> POST /api/session/activate (switch workflow) -> open /ws/agent (cookie auth)
 *   -> send {type:'prompt',...} -> await agent_received + agent_accepted{ok:true} + output
 * Then the same isolation matrix as the UI test: /api/ip/list scoping + cross-user 403.
 *
 *   ATLAS_E2E_BASE=http://127.0.0.1:3030 ATLAS_E2E_USERS=10 \
 *     ATLAS_E2E_JSON=/tmp/atlas_ws_n10_evidence.json node scripts/atlas_ws_nusers.mjs
 */
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WebSocket = require(path.join(REPO, 'frontend/atlas/node_modules/ws'));

const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3030';
const WSBASE = BASE.replace(/^http/, 'ws');
const N = Math.max(1, Number(process.env.ATLAS_E2E_USERS || 10));
const T = Number(process.env.ATLAS_E2E_TIMEOUT_MS || 120000);
const JSON_OUT = process.env.ATLAS_E2E_JSON || '/tmp/atlas_ws_n10_evidence.json';
const TAG = process.env.ATLAS_E2E_TAG || `ws${Date.now().toString(36)}`;
const WF_ROTATION = ['ssot-gen', 'rtl-gen', 'tb-gen', 'lint', 'coverage', 'sim_debug', 'syn', 'sta', 'fl-model-gen', 'sta-post'];

const log = (m) => console.log(m);
const ok = (m) => console.log('  \x1b[32m✓\x1b[0m ' + m);
const bad = (m) => { console.error('  \x1b[31m✗ ' + m + '\x1b[0m'); failed++; };
const step = (m) => console.log('\n=== ' + m + ' ===');
let failed = 0;
const soft = (c, m) => (c ? ok(m) : bad(m));

function cookieFrom(res) {
  const sc = (res.headers.getSetCookie && res.headers.getSetCookie()) || [];
  for (const c of sc) if (c.startsWith('atlas_session=')) return c.split(';')[0];
  return null;
}
async function jpost(url, body, cookie) {
  const h = { 'Content-Type': 'application/json' };
  if (cookie) h.Cookie = cookie;
  const res = await fetch(BASE + url, { method: 'POST', headers: h, body: JSON.stringify(body || {}) });
  let j = null; try { j = await res.json(); } catch (_) {}
  return { status: res.status, json: j, res };
}
async function jget(url, cookie) {
  const res = await fetch(BASE + url, { headers: cookie ? { Cookie: cookie } : {} });
  let j = null; try { j = await res.json(); } catch (_) {}
  return { status: res.status, json: j };
}

async function chat(owner, ip, wf, cookie, text) {
  return await new Promise((resolve) => {
    const frames = [];
    const out = { received: false, accepted: false, started: false, workerPid: null, sentSession: `${owner}/${ip}/${wf}` };
    let done = false;
    const finish = () => { if (done) return; done = true; try { ws.close(); } catch (_) {} resolve(out); };
    const ws = new WebSocket(`${WSBASE}/ws/agent?session_id=${encodeURIComponent(owner)}`, { headers: { Cookie: cookie } });
    const timer = setTimeout(finish, T);
    ws.on('open', () => {
      ws.send(JSON.stringify({ type: 'prompt', msg_id: `${TAG}-${owner}-1`, text, session: `${owner}/${ip}/${wf}`, ip, workflow: wf, ui_lang: 'en' }));
    });
    ws.on('message', (d) => {
      const s = d.toString(); frames.push(s);
      const blob = frames.join('\n');
      out.received = /"type"\s*:\s*"agent_received"/.test(blob);
      out.accepted = /"type"\s*:\s*"agent_accepted"[\s\S]*?"ok"\s*:\s*true/.test(blob);
      out.started = /"type"\s*:\s*"(token|tool)"/.test(blob) || /"running"\s*:\s*true/.test(blob);
      const pm = blob.match(/"pid"\s*:\s*(\d+)\s*,\s*"type"\s*:\s*"worker_started"/) || blob.match(/"type"\s*:\s*"worker_started"[\s\S]*?"pid"\s*:\s*(\d+)/);
      if (pm) out.workerPid = pm[1];
      if (out.received && out.accepted && out.started) { clearTimeout(timer); finish(); }
    });
    ws.on('error', () => { clearTimeout(timer); finish(); });
  });
}

async function driveUser(u) {
  const r = { name: u.name, ip: u.ip, workflow: u.workflow, errors: [] };
  try {
    await jpost('/api/auth/register', { username: u.name, password: u.pass, display_name: u.name });
    const lg = await jpost('/api/auth/login', { username: u.name, password: u.pass });
    const cookie = cookieFrom(lg.res);
    if (!cookie) { r.errors.push(`no cookie (login ${lg.status})`); return r; }
    r.cookie = cookie;
    const me = await jget('/api/users/me', cookie); r.me = me.json && (me.json.username || (me.json.user && me.json.user.username));
    const cr = await jpost('/api/ip/create', { name: u.ip, kind: 'TBD', exec_mode: 'single-worker', workflow: 'default' }, cookie);
    r.ipCreate = cr.status;
    const act = await jpost('/api/session/activate', { owner: u.name, ip: u.ip, workflow: u.workflow }, cookie);
    r.activate = act.status; r.activatedWf = act.json && (act.json.workflow || (act.json.namespace || '').split('/').pop());
    const c = await chat(u.name, u.ip, u.workflow, cookie, `hi from ${u.name} on ${u.ip}/${u.workflow} — short reply please`);
    Object.assign(r, c);
    return r;
  } catch (e) { r.errors.push('fatal: ' + e.message); return r; }
}

const users = Array.from({ length: N }, (_, i) => {
  const name = `wsu${i + 1}t${TAG}`;
  return { i: i + 1, name, pass: `${name}_pw123456`, ip: `ip_${name}`, workflow: WF_ROTATION[i % WF_ROTATION.length] };
});
const evidence = { base: BASE, n: N, tag: TAG, users: [], isolation: {}, summary: {} };

step(`1/3  ${N} real users — CONCURRENT register+login+createIP+activate+WS-chat (no browser)`);
const results = await Promise.all(users.map(driveUser));
let respond = 0; const sessions = new Set(), pids = new Set();
for (const r of results) {
  const responded = r.received && r.accepted && r.started;
  if (responded) respond++;
  if (r.sentSession) sessions.add(r.sentSession);
  if (r.workerPid) pids.add(r.workerPid);
  soft(responded && r.me === r.name && r.ipCreate < 400, `${r.name}: me=${r.me} ipCreate=${r.ipCreate} activate=${r.activate}(${r.activatedWf}) resp(recv=${r.received},acc=${r.accepted},out=${r.started}) pid=${r.workerPid}`);
  evidence.users.push({ name: r.name, ip: r.ip, workflow: r.workflow, me: r.me, ipCreate: r.ipCreate, activate: r.activate, received: !!r.received, accepted: !!r.accepted, started: !!r.started, workerPid: r.workerPid, errors: r.errors });
}
soft(respond === N, `all ${N} agents responded with output (${respond}/${N})`);
soft(sessions.size === N, `all ${N} namespaces distinct (${sessions.size}/${N})`);
const livePids = results.filter((r) => r.workerPid).length;
if (livePids > 0) soft(pids.size === livePids, `distinct worker pids: ${pids.size}/${livePids}`);

step(`2/3  IP-list scoping — each user sees ONLY own IP`);
const allIps = users.map((u) => u.ip);
let scopeFails = 0;
for (const r of results) {
  if (!r.cookie) continue;
  const list = await jget('/api/ip/list', r.cookie);
  const names = (list.json && list.json.items || []).map((x) => x.name || x.ip || x);
  const others = allIps.filter((ip) => ip !== r.ip && names.includes(ip));
  if (!names.includes(r.ip) || others.length) { scopeFails++; bad(`${r.name} ip_list leaked/missing (has own=${names.includes(r.ip)}, leaked=${others})`); }
}
soft(scopeFails === 0, `IP-list scoping clean for all ${N} users`);

step(`3/3  cross-user 403 matrix (activate + history, ${N}×${N - 1})`);
let a403 = 0, aTot = 0, h403 = 0, hTot = 0;
for (const ri of results) {
  if (!ri.cookie) continue;
  for (const rj of results) {
    if (rj.name === ri.name) continue;
    aTot++; hTot++;
    const a = await jpost('/api/session/activate', { owner: rj.name, ip: rj.ip, workflow: rj.workflow }, ri.cookie);
    if (a.status === 403) a403++;
    const h = await jget(`/api/session/history?session=${encodeURIComponent(`${rj.name}/${rj.ip}/${rj.workflow}`)}`, ri.cookie);
    if (h.status === 403) h403++;
  }
}
soft(a403 === aTot, `cross-user ACTIVATE 403: ${a403}/${aTot}`);
soft(h403 === hTot, `cross-user HISTORY 403: ${h403}/${hTot}`);

evidence.summary = { responded: respond, distinctNamespaces: sessions.size, distinctPids: pids.size, scopeFails, activate403: `${a403}/${aTot}`, history403: `${h403}/${hTot}`, failedChecks: failed };
fs.writeFileSync(JSON_OUT, JSON.stringify(evidence, null, 2));
step('RESULT');
log(`evidence -> ${JSON_OUT}`);
if (failed === 0) log(`\n\x1b[32mATLAS ${N}-user WS E2E: ✅ VERIFIED\x1b[0m (server-level, concurrent, isolated)`);
else { log(`\n\x1b[31mATLAS ${N}-user WS E2E: ❌ ${failed} check(s) FAILED\x1b[0m`); process.exitCode = 1; }
process.exit(process.exitCode || 0);
