// Script-backed SSOT -> PnR capture.
//
// This avoids waiting for long-running LLM worker handoff loops. It still uses
// ATLAS UI for the visible control surface, but executes the stage functions
// through the repo's deterministic scripts/headless runner and screenshots the
// UI after every stage.
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import {
  BASE,
  OUT,
  assert,
  exitCode,
  failures,
  gotoWorkspace,
  jget,
  launch,
  log,
  login,
  results,
  shoot,
  uniqueIp,
} from './lib.mjs';

const SOURCE_ROOT = process.env.SOURCE_ROOT || '/Users/brian/Desktop/Project/brian_hw/common_ai_agent';
const PROJECT_ROOT = process.env.PROJECT_ROOT || '/Users/brian/Desktop/Project/ROOT_IP';
const WORKFLOW_ROOT = process.env.WORKFLOW_ROOT || path.join(SOURCE_ROOT, 'workflow');
const ip = process.env.IP || uniqueIp('scriptip');
const kind = process.env.KIND || 'AXI4-Lite packet status block';
const runMode = process.env.RUN_MODE || 'starter';
const commandTimeoutMs = Number(process.env.CMD_TIMEOUT_MS || 180000);
const userRequirement = process.env.REQ || [
  'Create a compact AXI4-Lite slave IP for packet status/control.',
  'Expose readable counters, sticky error flags, clear-on-write control bits, interrupt status,',
  'and deterministic reset behavior suitable for RTL, lint, TB, simulation, coverage, synthesis, STA, and PnR evidence.',
].join(' ');
const newIpCommand = `/new-ip ${ip} ${kind}`;

const { browser, page } = await launch({ viewport: { width: 1900, height: 1150 }, dsf: 2 });
const stageResults = [];

const env = {
  ...process.env,
  ATLAS_PROJECT_ROOT: PROJECT_ROOT,
  ATLAS_WORKFLOW_ROOT: WORKFLOW_ROOT,
  ATLAS_RUN_MODE: runMode,
  PYTHONPATH: SOURCE_ROOT,
};

const clickExact = async (label) => page.evaluate((wanted) => {
  const target = String(wanted || '').trim().toUpperCase();
  const e = [...document.querySelectorAll('button,a,span,div,[role="tab"]')]
    .find(x => (x.textContent || '').trim().toUpperCase() === target && x.offsetParent);
  if (e) {
    e.click();
    return true;
  }
  return false;
}, label);

const openValidation = async () => {
  await clickExact('VALIDATION');
  await page.waitForTimeout(700);
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

const refreshValidation = async () => {
  try {
    await page.goto(`${BASE}/?session_id=admin&ip=${ip}&workflow=orchestrator`, {
      waitUntil: 'domcontentloaded',
      timeout: 15000,
    });
  } catch (e) {
    log('refresh goto soft-timeout:', e.message);
  }
  await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,a,span,.dir-btn,[role="tab"]')]
      .find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent || '').trim()) && x.offsetParent);
    if (e) e.click();
  });
  await page.waitForTimeout(1200);
  await openValidation();
};

const capture = async (index, name) => {
  await shoot(page, `ssot-pnr-script-${String(index).padStart(2, '0')}-${name}-${ip}.png`);
};

const run = (label, cmd, args, { cwd = SOURCE_ROOT, timeoutMs = commandTimeoutMs, allowFail = false } = {}) => new Promise((resolve) => {
  log(`run ${label}: ${cmd} ${args.join(' ')}`);
  const child = spawn(cmd, args, { cwd, env, stdio: ['ignore', 'pipe', 'pipe'] });
  let stdout = '';
  let stderr = '';
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    child.kill('SIGTERM');
  }, timeoutMs);
  child.stdout.on('data', d => { stdout += d.toString(); });
  child.stderr.on('data', d => { stderr += d.toString(); });
  child.on('close', (code, signal) => {
    clearTimeout(timer);
    const result = {
      label,
      cmd: [cmd, ...args].join(' '),
      cwd,
      code,
      signal,
      timedOut,
      ok: !timedOut && code === 0,
      stdout: stdout.slice(-8000),
      stderr: stderr.slice(-8000),
    };
    stageResults.push(result);
    log(`done ${label}: code=${code} signal=${signal || ''} timeout=${timedOut}`);
    if (!result.ok && !allowFail) {
      log(`${label} stderr:`, result.stderr.slice(-1000));
    }
    resolve(result);
  });
});

const headlessArgs = (stage, reqPath = '') => {
  const args = [
    'src/headless_workflow.py',
    '--root', PROJECT_ROOT,
    '--ip', ip,
    '--run-mode', runMode,
    '--stages', stage,
    '--provider', 'fake',
  ];
  if (reqPath) args.splice(5, 0, '--req', reqPath);
  return args;
};

try {
  await mkdir(OUT, { recursive: true });
  await mkdir(path.join(SOURCE_ROOT, '.omc', 'stage-reqs'), { recursive: true });

  const li = await login(page);
  assert(li.status === 200, `login ok (${li.status})`);
  const me = await jget(page, '/api/users/me');
  assert(me.status === 200, `authed (me ${me.status})`);

  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await capture(0, 'dashboard');

  await gotoWorkspace(page, { ip: 'default', workflow: 'orchestrator' });
  await openChat();
  await capture(1, 'chat-before-new-ip');
  await typeAndSubmit(newIpCommand);
  await page.waitForTimeout(800);
  await capture(2, 'new-ip-submitted');

  const planned = await waitForBody(new RegExp(`${ip}|SSOT TO-YAML|SSOT plan ready|Validation|Approval`, 'i'), {
    tries: 45,
    interval: 800,
    label: 'new-ip-plan',
  });
  assert(planned, 'new IP appeared in UI');

  await refreshValidation();
  await capture(3, 'validation-before-scripts');

  const reqPath = path.join(SOURCE_ROOT, '.omc', 'stage-reqs', `${ip}_requirements.md`);
  await writeFile(reqPath, `# ${ip} requirements\n\n${userRequirement}\n`, 'utf8');

  const stages = [
    ['ssot', 'python3', headlessArgs('ssot-gen', reqPath), { cwd: SOURCE_ROOT }],
    ['fl-model', 'python3', headlessArgs('fl-model-gen'), { cwd: SOURCE_ROOT }],
    ['cl-model', 'python3', headlessArgs('cl-model'), { cwd: SOURCE_ROOT }],
    ['equivalence', 'python3', headlessArgs('equiv-goals'), { cwd: SOURCE_ROOT }],
    ['rtl', 'python3', headlessArgs('rtl-gen'), { cwd: SOURCE_ROOT }],
    ['lint', 'python3', headlessArgs('lint'), { cwd: SOURCE_ROOT, allowFail: true }],
    ['tb', 'python3', headlessArgs('tb-gen'), { cwd: SOURCE_ROOT, allowFail: true }],
    ['sim', 'python3', headlessArgs('sim'), { cwd: SOURCE_ROOT, allowFail: true }],
    ['coverage', 'python3', headlessArgs('coverage'), { cwd: SOURCE_ROOT, allowFail: true }],
    ['sim-debug', 'python3', headlessArgs('sim-debug'), { cwd: SOURCE_ROOT, allowFail: true }],
    ['syn', 'bash', [path.join(WORKFLOW_ROOT, 'syn/scripts/auto_syn.sh'), ip], { cwd: PROJECT_ROOT, allowFail: true, timeoutMs: 300000 }],
    ['sta', 'bash', [path.join(WORKFLOW_ROOT, 'sta/scripts/auto_sta.sh'), ip], { cwd: PROJECT_ROOT, allowFail: true, timeoutMs: 300000 }],
    ['pnr', 'bash', [path.join(WORKFLOW_ROOT, 'pnr/scripts/auto_pnr.sh'), ip], { cwd: PROJECT_ROOT, allowFail: true, timeoutMs: 900000 }],
  ];

  let shot = 4;
  for (const [stage, cmd, args, opts] of stages) {
    await refreshValidation();
    await capture(shot++, `${stage}-before`);
    const result = await run(stage, cmd, args, opts);
    await refreshValidation();
    await capture(shot++, `${stage}-${result.ok ? 'pass' : 'fail'}`);
  }

  const resultPath = path.join(OUT, `ssot-pnr-script-results-${ip}.json`);
  await writeFile(resultPath, JSON.stringify({ ip, requirement: userRequirement, results: stageResults }, null, 2) + '\n', 'utf8');
  log(`results-json: ${resultPath}`);

  const pnr = stageResults.find(r => r.label === 'pnr');
  assert(!!pnr, 'PNR stage was executed');
  assert(stageResults.some(r => r.label === 'ssot' && r.ok), 'SSOT stage passed');
} catch (e) {
  assert(false, 'unexpected error: ' + (e && e.stack || e));
} finally {
  await browser.close();
}

log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
log(`IP: ${ip}`);
log(`root: ${PROJECT_ROOT}/${ip}`);
log(`screenshots: ${OUT}/ssot-pnr-script-*-${ip}.png`);
process.exit(exitCode());
