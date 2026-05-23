// Capture an end-to-end ATLAS IP flow from SSOT through PnR.
// The script drives the real UI + pipeline API, then screenshots each stage
// when it starts running and when it reaches a terminal state.
import { mkdir } from 'node:fs/promises';
import {
  BASE,
  OUT,
  assert,
  exitCode,
  failures,
  gotoWorkspace,
  jget,
  jpost,
  launch,
  log,
  login,
  results,
  shoot,
  uniqueIp,
} from './lib.mjs';

const PROJECT_ROOT = process.env.PROJECT_ROOT || '/Users/brian/Desktop/Project/ROOT_IP';
const ip = process.env.IP || uniqueIp('flowip');
const kind = process.env.KIND || 'AXI4-Lite packet status block';
const userRequirement = process.env.REQ || [
  'Create a compact AXI4-Lite slave IP for packet status/control.',
  'Expose readable counters, sticky error flags, clear-on-write control bits,',
  'interrupt status, and deterministic reset behavior suitable for RTL/TB/SIM/SYN/PNR evidence.',
].join(' ');
const stages = (process.env.STAGES || [
  'ssot',
  'fl-model',
  'cl-model',
  'equivalence',
  'rtl',
  'lint',
  'tb',
  'sim',
  'coverage',
  'sim-debug',
  'syn',
  'sta',
  'pnr',
].join(',')).split(',').map(s => s.trim()).filter(Boolean);
const stageTimeoutMs = Number(process.env.STAGE_TIMEOUT_MS || 10 * 60 * 1000);
const pollMs = Number(process.env.POLL_MS || 5000);
const model = (process.env.MODEL || '').trim();
const runMode = process.env.RUN_MODE || 'starter';
const execMode = process.env.EXEC_MODE || 'orchestrator';
const command = `/new-ip ${ip} ${kind}`;

const { browser, page } = await launch({ viewport: { width: 1900, height: 1150 }, dsf: 2 });

const terminalStates = new Set(['passed', 'failed', 'blocked', 'error', 'cancelled']);

const clickExact = async (label) => page.evaluate((wanted) => {
  const target = String(wanted || '').trim().toUpperCase();
  const items = [...document.querySelectorAll('button,a,span,div,[role="tab"]')];
  const e = items.find(x => (x.textContent || '').trim().toUpperCase() === target && x.offsetParent);
  if (e) {
    e.click();
    return true;
  }
  return false;
}, label);

const clickContains = async (label) => page.evaluate((wanted) => {
  const target = String(wanted || '').trim().toUpperCase();
  const items = [...document.querySelectorAll('button,a,span,div,[role="tab"]')];
  const e = items.find(x => (x.textContent || '').toUpperCase().includes(target) && x.offsetParent);
  if (e) {
    e.click();
    return true;
  }
  return false;
}, label);

const openValidation = async () => {
  await clickExact('VALIDATION');
  await page.waitForTimeout(600);
};

const openChat = async () => {
  await clickExact('CHAT');
  await page.waitForTimeout(500);
};

const typeAndSubmit = async (text) => {
  const ta = await page.waitForSelector('textarea', { timeout: 10000 });
  await ta.click();
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await ta.type(text);
  await page.keyboard.press('Enter');
};

const bodyHas = (re) => page.evaluate((source) => new RegExp(source, 'i').test(document.body.innerText), re.source);

const waitForBody = async (re, { tries = 40, interval = 750, label = 'body' } = {}) => {
  for (let i = 0; i < tries; i++) {
    if (await bodyHas(re)) return true;
    log(`poll ${label} ${i}: not yet`);
    await page.waitForTimeout(interval);
  }
  return false;
};

const stateFor = async () => {
  const r = await jget(page, `/api/pipeline/state?ip=${encodeURIComponent(ip)}`);
  if (r.status !== 200) {
    return { ok: false, status: r.status, error: r.body?.error || r.error || 'state failed' };
  }
  return { ok: true, status: r.status, body: r.body };
};

const jobSnapshot = async () => {
  const r = await jget(page, '/api/jobs');
  const jobs = Array.isArray(r.body?.jobs) ? r.body.jobs.filter(j => j.ip === ip) : [];
  return jobs.map(j => ({
    stage_id: j.stage_id || '',
    workflow: j.workflow || '',
    status: j.status || '',
    job_id: j.job_id || '',
    run_id: j.run_id || '',
    worker: j.worker || '',
    session: j.session || '',
    model: j.model || '',
  }));
};

const capture = async (index, name) => {
  await openValidation();
  await page.waitForTimeout(500);
  await shoot(page, `ssot-pnr-${String(index).padStart(2, '0')}-${name}-${ip}.png`);
};

const stageState = (state, stage) => {
  const item = state?.body?.stages?.[stage];
  return String(item?.state || '').trim().toLowerCase() || 'unknown';
};

const captureStageRun = async () => {
  const seenRunning = new Set();
  const seenTerminal = new Set();
  let shotIndex = 5;
  let currentStageIndex = 0;

  while (currentStageIndex < stages.length) {
    const stage = stages[currentStageIndex];
    const deadline = Date.now() + stageTimeoutMs;
    while (Date.now() < deadline) {
      const state = await stateFor();
      const jobs = await jobSnapshot();
      const activeJobs = jobs.filter(j => ['pending', 'running', 'queued'].includes(String(j.status || '').toLowerCase()));
      const status = state.ok ? stageState(state, stage) : `state-${state.status}`;
      log(`stage=${stage} state=${status} active=${activeJobs.map(j => `${j.stage_id}:${j.status}`).join(',') || '-'}`);

      if (status === 'running' && !seenRunning.has(stage)) {
        seenRunning.add(stage);
        await capture(shotIndex++, `${stage}-running`);
      }

      if ((terminalStates.has(status) || status === 'locked') && !seenTerminal.has(stage)) {
        seenTerminal.add(stage);
        await capture(shotIndex++, `${stage}-${status}`);
        return { stage, status, jobs, stopped: status !== 'passed' };
      }

      if (status === 'passed') {
        if (!seenTerminal.has(stage)) {
          seenTerminal.add(stage);
          await capture(shotIndex++, `${stage}-passed`);
        }
        currentStageIndex += 1;
        break;
      }

      await page.waitForTimeout(pollMs);
    }

    if (Date.now() >= deadline) {
      await capture(shotIndex++, `${stage}-timeout`);
      return { stage, status: 'timeout', jobs: await jobSnapshot(), stopped: true };
    }
  }

  return { stage: stages[stages.length - 1], status: 'passed', jobs: await jobSnapshot(), stopped: false };
};

try {
  await mkdir(OUT, { recursive: true });

  const li = await login(page);
  assert(li.status === 200, `login ok (${li.status})`);
  const me = await jget(page, '/api/users/me');
  assert(me.status === 200, `authed (me ${me.status})`);

  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await capture(0, 'dashboard');

  await gotoWorkspace(page, { ip: 'default', workflow: 'orchestrator' });
  await openChat();
  await capture(1, 'orchestrator-chat');

  await typeAndSubmit(command);
  await page.waitForTimeout(700);
  await capture(2, 'new-ip-submitted');

  const planned = await waitForBody(new RegExp(`${ip}|SSOT TO-YAML|SSOT plan ready|Validation|Approval`, 'i'), {
    tries: 45,
    interval: 800,
    label: 'new-ip-plan',
  });
  assert(planned, 'new IP plan/result appeared in UI');
  await capture(3, 'new-ip-plan-visible');

  await page.goto(`${BASE}/?session_id=admin&ip=${ip}&workflow=orchestrator`, { waitUntil: 'networkidle' });
  await clickContains('WORKSPACE');
  await page.waitForTimeout(1500);
  await openValidation();
  await capture(4, 'validation-before-dispatch');

  const dispatchBody = {
    ip,
    stages,
    schedule: 'serial',
    run_mode: runMode,
    exec_mode: execMode,
    prompt: userRequirement,
    user_seed: userRequirement,
  };
  if (model) dispatchBody.model = model;
  const dispatch = await jpost(page, '/api/pipeline/dispatch', dispatchBody);
  log('dispatch:', JSON.stringify({
    status: dispatch.status,
    ok: dispatch.body?.ok,
    pipeline_run_id: dispatch.body?.pipeline_run_id,
    schedule: dispatch.body?.schedule,
    stages: dispatch.body?.stages?.map(s => s.id),
    error: dispatch.body?.error,
  }));
  assert(dispatch.status === 200 && (dispatch.body?.ok || dispatch.body?.deduped), `pipeline dispatch accepted (${dispatch.status})`);

  const finalState = await captureStageRun();
  log('final:', JSON.stringify(finalState, null, 2));
  assert(finalState.stage === 'pnr' && finalState.status === 'passed', `flow reached PNR pass (got ${finalState.stage}:${finalState.status})`);
} catch (e) {
  assert(false, 'unexpected error: ' + (e && e.stack || e));
} finally {
  await browser.close();
}

log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
log(`IP: ${ip}`);
log(`root: ${PROJECT_ROOT}/${ip}`);
log(`screenshots: ${OUT}/ssot-pnr-*-${ip}.png`);
process.exit(exitCode());
