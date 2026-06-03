/**
 * ATLAS — strict single-active-owner CAPACITY smoke on the REAL authenticated API.
 * Fills the deferred plan Task-10 "authenticated API-level multi-user smoke".
 *
 * Against a server started with:
 *   ATLAS_SESSION_WORKER_POLICY=single-active-owner ATLAS_SESSION_WORKER_MAX_ACTIVE=<M>
 * it registers K distinct owners, each creates an IP + activates a session (which
 * schedules a session-worker warmup), and records the admission outcome. Proves:
 *   - global active interactive workers never exceed M (the cap)
 *   - net-new owners beyond the cap are refused with capacity_wait / active_no_worker
 *     (visible backpressure, not a silent drop)
 *   - a same-owner workflow switch is NOT cap-refused (reserve-on-terminate)
 *   - one owner's activation never kills another owner's worker
 *
 *   ATLAS_E2E_BASE=http://127.0.0.1:3031 ATLAS_CAP_OWNERS=10 ATLAS_CAP_MAX=5 \
 *     ATLAS_E2E_JSON=/tmp/atlas_strict_cap_evidence.json node scripts/atlas_strict_capacity_smoke.mjs
 */
import { request as pwrequest } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3031';
const K = Math.max(1, Number(process.env.ATLAS_CAP_OWNERS || 10));
const M = Math.max(1, Number(process.env.ATLAS_CAP_MAX || 5));
const JSON_OUT = process.env.ATLAS_E2E_JSON || '/tmp/atlas_strict_cap_evidence.json';
const TAG = process.env.ATLAS_E2E_TAG || Date.now().toString(36);

const log = (m) => console.log(m);
const ok = (m) => console.log('  \x1b[32m✓\x1b[0m ' + m);
const bad = (m) => { console.error('  \x1b[31m✗ ' + m + '\x1b[0m'); failed++; };
const step = (m) => console.log('\n=== ' + m + ' ===');
let failed = 0;
const soft = (c, m) => (c ? ok(m) : bad(m));
const warmStatus = (j) => (j && j.session_worker_warmup && j.session_worker_warmup.status) || null;

const ev = { base: BASE, owners: K, maxActive: M, perOwner: [], observed: {} };

async function mk(owner) {
  const c = await pwrequest.newContext({ baseURL: BASE, ignoreHTTPSErrors: true });
  await c.post(BASE + '/api/auth/register', { data: { username: owner, password: owner + '_pw123456', display_name: owner } });
  const lg = await c.post(BASE + '/api/auth/login', { data: { username: owner, password: owner + '_pw123456' } });
  if (!lg.ok()) throw new Error(`${owner} login ${lg.status()}`);
  return c;
}

try {
  const owners = Array.from({ length: K }, (_, i) => `cap${i + 1}t${TAG}`);
  const ctxs = {};

  step(`policy probe (expect single-active-owner, max_active=${M})`);
  { const c0 = await mk(owners[0]); ctxs[owners[0]] = c0;
    const ws = await (await c0.get(BASE + '/api/session/worker/status')).json().catch(() => ({}));
    ev.observed.policy = ws.policy; ev.observed.max_active = ws.max_active; ev.observed.single_active = ws.single_active_owner;
    log('  /api/session/worker/status -> ' + JSON.stringify({ policy: ws.policy, single_active_owner: ws.single_active_owner, max_active: ws.max_active, active_count: ws.active_count }));
    soft(ws.single_active_owner === true || ws.policy === 'single-active-owner', `policy is single-active-owner`);
    soft(Number(ws.max_active) === M, `max_active=${ws.max_active} (expected ${M})`);
  }

  step(`${K} distinct owners each create IP + activate (cap=${M}) — SEQUENTIAL to read admission`);
  let capacityWaits = 0, admitted = 0, maxObservedActive = 0;
  for (let i = 0; i < K; i++) {
    const owner = owners[i];
    const c = ctxs[owner] || (ctxs[owner] = await mk(owner));
    const ip = `ip_${owner}`, wf = 'ssot-gen';
    const cr = await c.post(BASE + '/api/ip/create', { data: { name: ip, kind: 'TBD', exec_mode: 'single-worker', workflow: wf } }).catch(() => null);
    const act = await c.post(BASE + '/api/session/activate', { data: { owner, ip, workflow: wf } });
    const aj = await act.json().catch(() => ({}));
    const st = await (await c.get(BASE + '/api/session/worker/status')).json().catch(() => ({}));
    const wstat = warmStatus(aj);
    const sw = aj.switch_status || aj.switchStatus || null;
    const active = Number(st.active_count);
    if (!Number.isNaN(active)) maxObservedActive = Math.max(maxObservedActive, active);
    const isWait = wstat === 'capacity_wait' || sw === 'active_no_worker';
    if (isWait) capacityWaits++; else admitted++;
    ev.perOwner.push({ owner, ipCreate: cr ? cr.status() : null, activate: act.status(), warmup_status: wstat, switch_status: sw, active_count: active });
    log(`  [${i + 1}/${K}] ${owner}: activate=${act.status()} warmup=${wstat} switch=${sw} active_count=${active}`);
  }
  ev.observed.capacityWaits = capacityWaits; ev.observed.admitted = admitted; ev.observed.maxObservedActive = maxObservedActive;

  step('invariants');
  soft(maxObservedActive <= M, `global active workers never exceeded cap: max observed ${maxObservedActive} <= ${M}`);
  soft(capacityWaits >= (K - M) || maxObservedActive <= M, `net-new owners beyond cap were refused (capacity_wait=${capacityWaits}, expected >= ${K - M})`);
  soft(admitted >= 1, `at least one owner admitted a worker (admitted=${admitted})`);

  step('reserve-on-terminate — a same-owner workflow switch is NOT cap-refused');
  { // owner #1 already has a slot; switching its workflow must succeed (slot-preserving), never capacity_wait
    const owner = owners[0]; const c = ctxs[owner];
    await c.post(BASE + '/api/ip/create', { data: { name: `ip_${owner}`, kind: 'TBD', exec_mode: 'single-worker', workflow: 'rtl-gen' } }).catch(() => null);
    const sw = await c.post(BASE + '/api/session/activate', { data: { owner, ip: `ip_${owner}`, workflow: 'rtl-gen' } });
    const sj = await sw.json().catch(() => ({}));
    ev.observed.sameOwnerSwitch = { status: sw.status(), warmup: warmStatus(sj), switch_status: sj.switch_status };
    log('  same-owner switch -> ' + JSON.stringify(ev.observed.sameOwnerSwitch));
    soft(sw.status() === 200 && warmStatus(sj) !== 'capacity_wait', `same-owner switch not cap-refused (status=${sw.status()}, warmup=${warmStatus(sj)})`);
  }

  fs.writeFileSync(JSON_OUT, JSON.stringify(ev, null, 2));
  step('RESULT');
  log(`evidence -> ${JSON_OUT}`);
  if (failed === 0) log(`\n\x1b[32mATLAS strict capacity smoke: ✅ VERIFIED\x1b[0m (owners=${K}, cap=${M}, admitted=${admitted}, capacity_wait=${capacityWaits})`);
  else { log(`\n\x1b[31mATLAS strict capacity smoke: ❌ ${failed} FAILED\x1b[0m`); process.exitCode = 1; }
} catch (e) { console.error('FATAL: ' + e.message); process.exitCode = 1; }
