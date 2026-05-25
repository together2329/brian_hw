// Real-LLM SSOT -> RTL smoke for ATLAS.
//
// Registers one or more users, creates one IP per user, dispatches SSOT and RTL
// with real workers, and verifies the RTL gate plus disk artifacts. Intended to
// run against a separately started atlas_ui server.
import { existsSync, readFileSync, readdirSync } from 'node:fs';
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
const POLL_MS = Number(process.env.POLL_MS || 10000);
const TIMEOUT_MS = Number(process.env.RTL_TIMEOUT_MS || 30 * 60 * 1000);
const USER_COUNT = Math.max(1, Math.min(4, Number(process.env.USER_COUNT || 1)));
const stamp = Date.now().toString(36);
const password = 'pw1151';
const users = Array.from({ length: USER_COUNT }, (_, i) => {
  const suffix = String.fromCharCode(97 + i);
  return {
    username: `realrtl_${suffix}_${stamp}`,
    ip: uniqueIp(`realrtl_${suffix}`),
  };
});

const requirementFor = (ip, username) => [
  `Create ${ip}, a compact AXI4-Lite slave RTL IP for ${username}.`,
  'The IP accepts 32-bit AXI4-Lite register reads/writes, exposes packet counters, sticky error flags,',
  'clear-on-write status bits, interrupt enable/status, deterministic synchronous reset behavior,',
  'and a small packet-control datapath suitable for downstream TB/SIM evidence.',
  'Keep the design intentionally small so SSOT-derived RTL can compile and lint cleanly.',
].join(' ');

const terminal = new Set(['completed', 'done', 'passed', 'error', 'failed', 'blocked', 'cancelled']);

const readJson = (file) => JSON.parse(readFileSync(file, 'utf8'));

const { browser, page: firstPage } = await launch({ viewport: { width: 1700, height: 1050 }, dsf: 1 });
const contexts = [];
const pages = [firstPage];
for (let i = 1; i < USER_COUNT; i++) {
  const ctx = await browser.newContext({ viewport: { width: 1700, height: 1050 }, deviceScaleFactor: 1 });
  contexts.push(ctx);
  pages.push(await ctx.newPage());
}

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
    workflow: 'orchestrator',
    initial_workflow: 'orchestrator',
  });
  assert(created.status === 200 && created.body?.ok, `${user.username} created IP ${user.ip} (${created.status})`);
  const activated = await jpost(page, '/api/session/activate', {
    owner: user.username,
    ip: user.ip,
    workflow: 'orchestrator',
    preserve_running: true,
  });
  assert(activated.status === 200 && activated.body?.ok, `${user.username}/${user.ip}/orchestrator activated (${activated.status})`);
};

const dispatchUntilRtl = async (page, user) => {
  const seed = requirementFor(user.ip, user.username);
  const body = {
    ip: user.ip,
    stages: ['ssot', 'rtl'],
    schedule: 'serial',
    run_mode: RUN_MODE,
    exec_mode: EXEC_MODE,
    prompt: seed,
    user_seed: seed,
  };
  if (MODEL) body.model = MODEL;
  const dispatched = await jpost(page, '/api/pipeline/dispatch', body);
  const jobs = Array.isArray(dispatched.body?.jobs) ? dispatched.body.jobs : [];
  user.jobs = jobs;
  user.ssotJobId = jobs.find(j => j.stage_id === 'ssot')?.job_id || jobs[0]?.job_id || '';
  user.rtlJobId = jobs.find(j => j.stage_id === 'rtl')?.job_id || jobs[1]?.job_id || '';
  user.pipelineId = dispatched.body?.pipeline_id || dispatched.body?.pipeline_run_id || '';
  user.dispatch = dispatched.body || {};
  assert(dispatched.status === 200 && (dispatched.body?.ok || dispatched.body?.deduped), `${user.username} dispatched real SSOT->RTL (${dispatched.status})`);
  assert(user.ssotJobId, `${user.username} has SSOT job id ${user.ssotJobId || '(missing)'}`);
  assert(user.rtlJobId, `${user.username} has RTL job id ${user.rtlJobId || '(missing)'}`);
};

const stateFor = async (page, user) => {
  const state = await jget(page, `/api/pipeline/state?ip=${encodeURIComponent(user.ip)}`);
  const stages = state.body?.stages || {};
  return {
    status: state.status,
    ssot: String(stages.ssot?.state || '').toLowerCase(),
    rtl: String(stages.rtl?.state || '').toLowerCase(),
    ssotSummary: stages.ssot?.summary || stages.ssot?.evidence || '',
    rtlSummary: stages.rtl?.summary || stages.rtl?.evidence || stages.rtl?.error_summary || '',
    raw: state.body,
  };
};

const jobsFor = async (page, user) => {
  const r = await jget(page, '/api/jobs');
  const jobs = Array.isArray(r.body?.jobs) ? r.body.jobs : [];
  const ownJobIds = new Set([user.ssotJobId, user.rtlJobId].filter(Boolean));
  return jobs.filter(j => j.ip === user.ip || ownJobIds.has(j.job_id));
};

const waitForRtl = async (page, user) => {
  const deadline = Date.now() + TIMEOUT_MS;
  let last = {};
  while (Date.now() < deadline) {
    const state = await stateFor(page, user);
    const jobs = await jobsFor(page, user);
    const rtlJob = jobs.find(j => j.job_id === user.rtlJobId) || jobs.find(j => j.stage_id === 'rtl') || {};
    const ssotJob = jobs.find(j => j.job_id === user.ssotJobId) || jobs.find(j => j.stage_id === 'ssot') || {};
    const rtlStatus = String(rtlJob.status || '').toLowerCase();
    const ssotStatus = String(ssotJob.status || '').toLowerCase();
    last = { state, ssotStatus, rtlStatus, ssotJob, rtlJob, jobs };
    log(`${EXEC_MODE} ${user.username}/${user.ip}: ssot=${state.ssot || '?'} ssotJob=${ssotStatus || '?'} rtl=${state.rtl || '?'} rtlJob=${rtlStatus || '?'} worker=${rtlJob.worker || ssotJob.worker || '-'}`);
    if (state.rtl === 'passed') return last;
    if (terminal.has(rtlStatus) && !['completed', 'done', 'passed'].includes(rtlStatus) && state.rtl !== 'running') return last;
    await page.waitForTimeout(POLL_MS);
  }
  return last;
};

const verifySsotArtifact = (user) => {
  const ssotPath = path.join(PROJECT_ROOT, user.ip, 'yaml', `${user.ip}.ssot.yaml`);
  const ok = existsSync(ssotPath);
  assert(ok, `${user.username} SSOT file exists: ${ssotPath}`);
  if (!ok) return;
  const text = readFileSync(ssotPath, 'utf8');
  assert(text.includes('top_module'), `${user.username} SSOT has top_module`);
  assert(text.includes('function_model'), `${user.username} SSOT has function_model`);
  assert(text.length > 1000, `${user.username} SSOT is non-trivial (${text.length} bytes)`);
};

const verifyRtlArtifacts = (user) => {
  const ipRoot = path.join(PROJECT_ROOT, user.ip);
  const filelistPath = path.join(ipRoot, 'list', `${user.ip}.f`);
  const rtlDir = path.join(ipRoot, 'rtl');
  const compilePath = path.join(ipRoot, 'rtl', 'rtl_compile.json');
  const lintPath = path.join(ipRoot, 'lint', 'dut_lint.json');
  const stagePath = path.join(ipRoot, 'logs', 'stage_engine', 'ssot-rtl.json');
  assert(existsSync(filelistPath), `${user.username} RTL filelist exists: ${filelistPath}`);
  assert(existsSync(rtlDir), `${user.username} RTL directory exists: ${rtlDir}`);
  const rtlFiles = existsSync(rtlDir)
    ? readdirSync(rtlDir).filter(name => /\.(sv|v)$/.test(name)).sort()
    : [];
  assert(rtlFiles.length > 0, `${user.username} RTL sources exist (${rtlFiles.join(', ') || 'none'})`);
  const filelistEntries = existsSync(filelistPath)
    ? readFileSync(filelistPath, 'utf8')
      .split(/\r?\n/)
      .map(line => line.replace(/\/\/.*$/, '').replace(/#.*$/, '').trim())
      .filter(line => /\.(sv|v)$/.test(line))
      .map(line => line.replace(/^\.\//, ''))
    : [];
  for (const rtlFile of rtlFiles) {
    assert(
      filelistEntries.includes(`rtl/${rtlFile}`),
      `${user.username} RTL filelist includes rtl/${rtlFile}`,
    );
  }
  const topPath = path.join(rtlDir, `${user.ip}.sv`);
  assert(existsSync(topPath), `${user.username} top RTL exists: ${topPath}`);
  if (existsSync(topPath)) {
    const topText = readFileSync(topPath, 'utf8');
    assert(new RegExp(`module\\s+${user.ip}\\b`).test(topText), `${user.username} top RTL declares module ${user.ip}`);
    assert(!/\b(TBD|TODO|PLACEHOLDER|stub)\b/i.test(topText), `${user.username} top RTL has no placeholder markers`);
  }
  assert(existsSync(compilePath), `${user.username} RTL compile report exists`);
  assert(existsSync(lintPath), `${user.username} DUT lint report exists`);
  assert(existsSync(stagePath), `${user.username} ssot-rtl stage report exists`);
  if (existsSync(compilePath)) {
    const compile = readJson(compilePath);
    assert(compile.passed === true, `${user.username} RTL compile passed`);
    const reported = new Set((compile.rtl_files || []).map(String));
    for (const entry of filelistEntries) {
      assert(reported.has(entry), `${user.username} compile report covers ${entry}`);
    }
  }
  if (existsSync(lintPath)) {
    const lint = readJson(lintPath);
    assert(lint.passed === true, `${user.username} DUT lint passed`);
  }
  if (existsSync(stagePath)) {
    const stage = readJson(stagePath);
    assert(stage.status === 'pass', `${user.username} ssot-rtl stage report status=pass (got ${stage.status || 'missing'})`);
  }
};

try {
  await Promise.all(users.map((u, i) => register(pages[i], u)));
  await Promise.all(users.map((u, i) => createIp(pages[i], u)));
  await Promise.all(users.map((u, i) => dispatchUntilRtl(pages[i], u)));

  const results = await Promise.all(users.map((u, i) => waitForRtl(pages[i], u)));
  results.forEach((result, i) => {
    const user = users[i];
    assert(result.state?.status === 200, `${user.username} pipeline state readable (${result.state?.status})`);
    assert(result.state?.ssot === 'passed', `${user.username} SSOT gate passed (got ${result.state?.ssot || 'unknown'})`);
    assert(result.state?.rtl === 'passed', `${user.username} RTL gate passed (got ${result.state?.rtl || 'unknown'}, job ${result.rtlStatus || 'unknown'})`);
    verifySsotArtifact(user);
    verifyRtlArtifacts(user);
  });

  if (users.length > 1) {
    const crossA = await stateFor(pages[0], users[1]);
    const crossB = await stateFor(pages[1], users[0]);
    assert(crossA.status === 403, `A cannot read B pipeline state (${crossA.status})`);
    assert(crossB.status === 403, `B cannot read A pipeline state (${crossB.status})`);
  }
} catch (e) {
  assert(false, 'unexpected error: ' + (e && e.stack || e));
} finally {
  for (const ctx of contexts) await ctx.close();
  await browser.close();
}

log(`exec_mode: ${EXEC_MODE}`);
log(`users: ${users.map(u => `${u.username}/${u.ip}/ssot=${u.ssotJobId || '-'}/rtl=${u.rtlJobId || '-'}`).join(', ')}`);
log(`root: ${PROJECT_ROOT}`);
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
