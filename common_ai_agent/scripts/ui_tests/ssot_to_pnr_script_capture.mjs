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
const CHAT_RECORDER = path.join(SOURCE_ROOT, 'scripts/ui_tests/record_orch_chat.py');
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
let dbUserId = 'admin';
let displayName = 'admin';

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

const chatEntryCount = async () => page.evaluate(() =>
  document.querySelectorAll('.feed-entry, .react-block, .tool-card').length);

const refreshChat = async () => {
  try {
    await page.goto(`${BASE}/?session_id=admin&ip=${ip}&workflow=orchestrator`, {
      waitUntil: 'domcontentloaded',
      timeout: 15000,
    });
  } catch (e) {
    log('chat goto soft-timeout:', e.message);
  }
  await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,a,span,.dir-btn,[role="tab"]')]
      .find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent || '').trim()) && x.offsetParent);
    if (e) e.click();
  });
  await page.waitForTimeout(900);
  await openChat();
  let count = 0;
  for (let i = 0; i < 8; i++) {
    count = await chatEntryCount();
    if (count > 0) break;
    await page.waitForTimeout(500);
  }
  return count;
};

const workflowForStage = (stage) => ({
  ssot: 'ssot-gen',
  'fl-model': 'fl-model-gen',
  'cl-model': 'fl-model-gen',
  equivalence: 'fl-model-gen',
  rtl: 'rtl-gen',
  lint: 'lint',
  tb: 'tb-gen',
  sim: 'sim',
  coverage: 'coverage',
  'sim-debug': 'sim_debug',
  syn: 'syn',
  sta: 'sta',
  pnr: 'pnr',
}[stage] || stage);

const writeWorkflowConversation = async (stage, command, result = null) => {
  const workflow = workflowForStage(stage);
  const sdir = path.join(PROJECT_ROOT, '.session', 'admin', ip, workflow);
  await mkdir(sdir, { recursive: true });
  const messages = [
    {
      role: 'user',
      content: `Run ${stage} for ${ip}.`,
    },
    {
      role: 'assistant',
      content: `I am executing the ${stage} stage for ${ip} and will report command evidence.`,
    },
    {
      role: 'assistant',
      tool_calls: [{
        function: {
          name: 'run_stage',
          arguments: `stage="${stage}", ip="${ip}"`,
        },
      }],
    },
    {
      role: 'tool',
      name: 'run_stage',
      content: result
        ? `└─ ${result.ok ? 'PASS' : 'FAIL'} code=${result.code} timeout=${result.timedOut}\n${resultDetails(result)}`
        : `└─ command pending\n${command}`,
    },
  ];
  if (result) {
    messages.push({
      role: 'assistant',
      content: `${stage} ${result.ok ? 'passed' : 'failed'} for ${ip}.`,
    });
  }
  await writeFile(path.join(sdir, 'conversation.json'), JSON.stringify(messages, null, 2) + '\n', 'utf8');
  await writeFile(path.join(sdir, 'full_conversation.json'), JSON.stringify(messages, null, 2) + '\n', 'utf8');
  return { workflow, count: messages.length };
};

const refreshWorkflowChat = async (workflow) => {
  try {
    await page.goto(`${BASE}/?session_id=admin&ip=${ip}&workflow=${workflow}`, {
      waitUntil: 'domcontentloaded',
      timeout: 15000,
    });
  } catch (e) {
    log('workflow chat goto soft-timeout:', e.message);
  }
  await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,a,span,.dir-btn,[role="tab"]')]
      .find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent || '').trim()) && x.offsetParent);
    if (e) e.click();
  });
  await page.waitForTimeout(900);
  await openChat();
  let count = 0;
  for (let i = 0; i < 10; i++) {
    count = await chatEntryCount();
    if (count > 0) break;
    await page.waitForTimeout(500);
  }
  return count;
};

const typeAndSubmit = async (text) => {
  const ta = await page.waitForSelector('textarea', { timeout: 10000 });
  await ta.click();
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await ta.type(text);
  await page.keyboard.press('Enter');
};

const bodyHas = (re) => page.evaluate((source) => new RegExp(source, 'i').test(document.body.innerText), re.source);

const setShotOverlay = async ({ title, status = '', command = '', details = '' }) => {
  await page.evaluate((meta) => {
    let box = document.getElementById('atlas-ui-test-shot-overlay');
    if (!box) {
      box = document.createElement('div');
      box.id = 'atlas-ui-test-shot-overlay';
      document.body.appendChild(box);
    }
    Object.assign(box.style, {
      position: 'fixed',
      right: '18px',
      bottom: '74px',
      zIndex: '2147483647',
      width: '720px',
      maxWidth: '44vw',
      maxHeight: '38vh',
      overflow: 'hidden',
      padding: '14px 16px',
      border: '2px solid #e9c46a',
      borderRadius: '6px',
      background: 'rgba(12, 17, 23, 0.96)',
      color: '#d7dee8',
      font: '13px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
      boxShadow: '0 10px 32px rgba(0,0,0,0.45)',
      whiteSpace: 'pre-wrap',
    });
    box.replaceChildren();

    const add = (text, style = {}) => {
      if (!text) return;
      const el = document.createElement('div');
      el.textContent = text;
      Object.assign(el.style, style);
      box.appendChild(el);
    };
    const statusColor = /FAIL|ERROR|code=[1-9]/i.test(meta.status || '')
      ? '#ff8f70'
      : /PASS|code=0/i.test(meta.status || '')
        ? '#84e0a4'
        : '#e9c46a';
    add(meta.title || '', {
      color: '#ffd166',
      fontSize: '15px',
      fontWeight: '700',
      marginBottom: '8px',
    });
    add(meta.status || '', {
      color: statusColor,
      fontWeight: '700',
      marginBottom: '8px',
    });
    add(meta.command ? `cmd: ${meta.command}` : '', {
      color: '#9fb0c3',
      marginBottom: '8px',
    });
    add(meta.details || '', {
      color: '#c4ceda',
      lineHeight: '1.35',
    });
  }, { title, status, command, details });
};

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

const capture = async (index, name, meta = {}) => {
  await setShotOverlay({
    title: meta.title || `SHOT ${String(index).padStart(2, '0')} ${name}`,
    status: meta.status || `ip=${ip}`,
    command: meta.command || '',
    details: meta.details || '',
  });
  await page.waitForTimeout(120);
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

const recordChat = (role, content, who = '') => new Promise((resolve) => {
  const child = spawn('python3', [
    CHAT_RECORDER,
    '--project-root', PROJECT_ROOT,
    '--ip', ip,
    '--user-id', dbUserId,
    '--display-name', who || (role === 'assistant' ? 'ATLAS' : role === 'user' ? displayName : 'tool'),
    '--role', role,
  ], { cwd: SOURCE_ROOT, env, stdio: ['pipe', 'pipe', 'pipe'] });
  let stderr = '';
  child.stderr.on('data', d => { stderr += d.toString(); });
  child.on('close', (code) => {
    if (code !== 0) log(`recordChat ${role} failed code=${code}:`, stderr.slice(-600));
    resolve(code === 0);
  });
  child.stdin.end(String(content || ''));
});

const tailLines = (text, maxLines = 10, maxChars = 1200) => String(text || '')
  .split(/\r?\n/)
  .filter(Boolean)
  .slice(-maxLines)
  .join('\n')
  .slice(-maxChars);

const resultDetails = (result) => {
  const stderr = tailLines(result.stderr);
  const stdout = tailLines(result.stdout);
  if (stderr && stdout) return `stderr:\n${stderr}\n\nstdout:\n${stdout}`;
  if (stderr) return `stderr:\n${stderr}`;
  if (stdout) return `stdout:\n${stdout}`;
  return 'no stdout/stderr captured';
};

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
  const authUser = (me.body && me.body.user) || {};
  dbUserId = String(authUser.id || authUser.username || 'admin');
  displayName = String(authUser.username || authUser.display_name || 'admin');

  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  await capture(0, 'dashboard', {
    title: '00 dashboard',
    status: `ip will be created: ${ip}`,
  });

  await gotoWorkspace(page, { ip: 'default', workflow: 'orchestrator' });
  await openChat();
  await capture(1, 'chat-before-new-ip', {
    title: '01 before /new-ip',
    status: 'workspace chat ready',
    command: newIpCommand,
  });
  await typeAndSubmit(newIpCommand);
  await page.waitForTimeout(800);
  await capture(2, 'new-ip-submitted', {
    title: '02 /new-ip submitted',
    status: 'waiting for new IP scaffold / SSOT plan UI',
    command: newIpCommand,
  });

  const planned = await waitForBody(new RegExp(`${ip}|SSOT TO-YAML|SSOT plan ready|Validation|Approval`, 'i'), {
    tries: 45,
    interval: 800,
    label: 'new-ip-plan',
  });
  assert(planned, 'new IP appeared in UI');

  await refreshValidation();
  await capture(3, 'validation-before-scripts', {
    title: '03 validation before deterministic scripts',
    status: 'UI workspace loaded for generated IP',
  });

  const reqPath = path.join(SOURCE_ROOT, '.omc', 'stage-reqs', `${ip}_requirements.md`);
  await writeFile(reqPath, `# ${ip} requirements\n\n${userRequirement}\n`, 'utf8');
  await recordChat('user', userRequirement, displayName);
  await recordChat('assistant', `I will run the IP flow for ${ip} from SSOT through PNR and leave stage evidence in this chat.`, 'ATLAS');

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
    const command = [cmd, ...args].join(' ');
    await recordChat('thought', `Preparing ${stage}: check current ${ip} artifacts, then execute the stage command.`, 'reasoning');
    await recordChat('tool', `⏺ run_stage(stage="${stage}", ip="${ip}")\n${command}`, 'tool');
    const beforeChatCount = await refreshChat();
    assert(beforeChatCount > 0, `${stage} chat feed rendered before execution (${beforeChatCount})`);
    await capture(shot++, `${stage}-chat-before`, {
      title: `${stage}: before`,
      status: 'chat feed shows reasoning + tool call before execution',
      command,
    });
    const result = await run(stage, cmd, args, opts);
    await recordChat(
      'tool_result',
      `└─ ${result.ok ? 'PASS' : 'FAIL'} code=${result.code} timeout=${result.timedOut}\n${resultDetails(result)}`,
      'tool',
    );
    await recordChat(
      'assistant',
      `${stage} ${result.ok ? 'passed' : 'failed'} for ${ip}. ${result.ok ? 'Proceeding to the next stage.' : 'Keeping the failure visible as gate evidence, then continuing only where allowed.'}`,
      'ATLAS',
    );
    const afterChatCount = await refreshChat();
    assert(afterChatCount > 0, `${stage} chat feed rendered after execution (${afterChatCount})`);
    await capture(shot++, `${stage}-chat-${result.ok ? 'pass' : 'fail'}`, {
      title: `${stage}: after`,
      status: 'chat feed shows tool result + assistant summary',
      command,
      details: resultDetails(result),
    });
    const wf = await writeWorkflowConversation(stage, command, result);
    const wfChatCount = await refreshWorkflowChat(wf.workflow);
    assert(wfChatCount > 0, `${stage} workflow chat rendered in ${wf.workflow} (${wfChatCount})`);
    await capture(shot++, `${stage}-${wf.workflow}-workflow-chat-${result.ok ? 'pass' : 'fail'}`, {
      title: `${stage}: ${wf.workflow} chat`,
      status: `individual workflow chat rendered (${wfChatCount} entries)`,
      command,
      details: resultDetails(result),
    });
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
