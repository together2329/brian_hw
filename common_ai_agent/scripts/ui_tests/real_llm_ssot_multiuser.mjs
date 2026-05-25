// Real-LLM SSOT smoke for multi-user ATLAS.
//
// Starts from real HTTP cookies, registers two users, creates one IP per user,
// dispatches only the SSOT stage, and waits for each user's own SSOT gate to
// pass. Intended to run against a separately started atlas_ui server.
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import {
  BASE,
  assert,
  exitCode,
  failures,
  jget,
  jpost,
  launch,
  log,
  uniqueIp,
} from './lib.mjs';

const PROJECT_ROOT = process.env.PROJECT_ROOT || '/Users/brian/Desktop/Project/ROOT_IP';
const EXEC_MODE = process.env.EXEC_MODE || 'orchestrator';
const RUN_MODE = process.env.RUN_MODE || 'starter';
const MODEL = (process.env.MODEL || '').trim();
const POLL_MS = Number(process.env.POLL_MS || 5000);
const TIMEOUT_MS = Number(process.env.SSOT_TIMEOUT_MS || 12 * 60 * 1000);
const stamp = Date.now().toString(36);
const password = 'pw1151';
const users = [
  { username: `realssot_a_${stamp}`, ip: uniqueIp('realssot_a') },
  { username: `realssot_b_${stamp}`, ip: uniqueIp('realssot_b') },
];

const requirementFor = (ip, username) => [
  `Create the SSOT for ${ip}, an AXI4-Lite slave control/status IP for ${username}.`,
  'The IP accepts host register accesses, exposes packet counters, sticky error flags, interrupt status,',
  'clear-on-write control bits, deterministic reset behavior, and verification goals for RTL/TB/SIM.',
  'Keep the block compact and suitable for downstream RTL generation.',
].join(' ');

const terminal = new Set(['completed', 'done', 'passed', 'error', 'failed', 'blocked', 'cancelled']);

const { browser, page: pageA } = await launch({ viewport: { width: 1700, height: 1050 }, dsf: 1 });
const ctxB = await browser.newContext({ viewport: { width: 1700, height: 1050 }, deviceScaleFactor: 1 });
const pageB = await ctxB.newPage();
const pages = [pageA, pageB];

const register = async (page, user) => {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  const reg = await jpost(page, '/api/auth/register', {
    username: user.username,
    password,
    display_name: user.username,
  });
  assert(reg.status === 200, `${user.username} registered (${reg.status})`);
  const me = await jget(page, '/api/users/me');
  assert(me.status === 200, `${user.username} authenticated (${me.status})`);
  user.dbUserId = me.body?.user?.id || '';
};

const createIp = async (page, user) => {
  const created = await jpost(page, '/api/ip/create', {
    name: user.ip,
    exec_mode: EXEC_MODE,
    workflow: 'ssot-gen',
    initial_workflow: 'ssot-gen',
  });
  assert(created.status === 200 && created.body?.ok, `${user.username} created IP ${user.ip} (${created.status})`);
  const activated = await jpost(page, '/api/session/activate', {
    owner: user.username,
    ip: user.ip,
    workflow: 'ssot-gen',
    preserve_running: true,
  });
  assert(activated.status === 200 && activated.body?.ok, `${user.username}/${user.ip}/ssot-gen activated (${activated.status})`);
};

const dispatchSsot = async (page, user) => {
  const body = {
    ip: user.ip,
    stages: ['ssot'],
    schedule: 'serial',
    run_mode: RUN_MODE,
    exec_mode: EXEC_MODE,
    prompt: requirementFor(user.ip, user.username),
    user_seed: requirementFor(user.ip, user.username),
  };
  if (MODEL) body.model = MODEL;
  const dispatched = await jpost(page, '/api/pipeline/dispatch', body);
  const job = dispatched.body?.jobs?.[0] || {};
  user.jobId = job.job_id || '';
  user.pipelineId = dispatched.body?.pipeline_id || dispatched.body?.pipeline_run_id || '';
  user.dispatch = dispatched.body || {};
  assert(dispatched.status === 200 && (dispatched.body?.ok || dispatched.body?.deduped), `${user.username} dispatched real SSOT (${dispatched.status})`);
  assert(user.jobId, `${user.username} has SSOT job id ${user.jobId || '(missing)'}`);
};

const stateFor = async (page, user) => {
  const state = await jget(page, `/api/pipeline/state?ip=${encodeURIComponent(user.ip)}`);
  const ssot = state.body?.stages?.ssot || {};
  return {
    status: state.status,
    state: String(ssot.state || '').toLowerCase(),
    summary: ssot.summary || ssot.evidence || '',
    raw: state.body,
  };
};

const jobsFor = async (page, user) => {
  const r = await jget(page, '/api/jobs');
  const jobs = Array.isArray(r.body?.jobs) ? r.body.jobs : [];
  return jobs.filter(j => j.ip === user.ip || j.job_id === user.jobId);
};

const waitForSsot = async (page, user) => {
  const deadline = Date.now() + TIMEOUT_MS;
  let last = {};
  while (Date.now() < deadline) {
    const state = await stateFor(page, user);
    const jobs = await jobsFor(page, user);
    const ownJob = jobs.find(j => j.job_id === user.jobId) || jobs[0] || {};
    const jobStatus = String(ownJob.status || '').toLowerCase();
    last = { state, jobStatus, ownJob };
    log(`${EXEC_MODE} ${user.username}/${user.ip}: ssot=${state.state || '?'} job=${jobStatus || '?'} worker=${ownJob.worker || '-'}`);
    if (state.state === 'passed') return last;
    if (terminal.has(jobStatus) && !['completed', 'done', 'passed'].includes(jobStatus)) return last;
    await page.waitForTimeout(POLL_MS);
  }
  return last;
};

const verifyArtifact = (user) => {
  const ssotPath = path.join(PROJECT_ROOT, user.ip, 'yaml', `${user.ip}.ssot.yaml`);
  const ok = existsSync(ssotPath);
  assert(ok, `${user.username} SSOT file exists: ${ssotPath}`);
  if (!ok) return;
  const text = readFileSync(ssotPath, 'utf8');
  assert(text.includes('top_module'), `${user.username} SSOT has top_module`);
  assert(text.includes('function_model'), `${user.username} SSOT has function_model`);
  assert(text.length > 1000, `${user.username} SSOT is non-trivial (${text.length} bytes)`);
};

try {
  await Promise.all(users.map((u, i) => register(pages[i], u)));
  await Promise.all(users.map((u, i) => createIp(pages[i], u)));
  await Promise.all(users.map((u, i) => dispatchSsot(pages[i], u)));

  const results = await Promise.all(users.map((u, i) => waitForSsot(pages[i], u)));
  results.forEach((result, i) => {
    const user = users[i];
    assert(result.state?.status === 200, `${user.username} pipeline state readable (${result.state?.status})`);
    assert(result.state?.state === 'passed', `${user.username} SSOT gate passed (got ${result.state?.state || 'unknown'}, job ${result.jobStatus || 'unknown'})`);
    verifyArtifact(user);
  });

  const crossA = await stateFor(pageA, users[1]);
  const crossB = await stateFor(pageB, users[0]);
  assert(crossA.status === 403, `A cannot read B SSOT state (${crossA.status})`);
  assert(crossB.status === 403, `B cannot read A SSOT state (${crossB.status})`);
} catch (e) {
  assert(false, 'unexpected error: ' + (e && e.stack || e));
} finally {
  await ctxB.close();
  await browser.close();
}

log(`exec_mode: ${EXEC_MODE}`);
log(`users: ${users.map(u => `${u.username}/${u.ip}/job=${u.jobId || '-'}`).join(', ')}`);
log(`root: ${PROJECT_ROOT}`);
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
