// Multi-user chat isolation across the real HTTP cookie boundary.
//
// Verifies two chat surfaces:
// 1) orchestrator CHAT hydrate: DB chat_message rows are keyed by the
//    authenticated user's workspace/ip row and must not bleed to another user.
// 2) workflow CHAT hydrate: .session/<user>/<ip>/<workflow>/conversation.json
//    is visible only to that owning user, even when an empty DB session exists.
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
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

const SOURCE_ROOT = process.env.SOURCE_ROOT || '/Users/brian/Desktop/Project/brian_hw/common_ai_agent';
const PROJECT_ROOT = process.env.PROJECT_ROOT || '/Users/brian/Desktop/Project/ROOT_IP';
const CHAT_RECORDER = path.join(SOURCE_ROOT, 'scripts/ui_tests/record_orch_chat.py');
const DB_PATH = process.env.ATLAS_TRACE_DB_PATH || process.env.ATLAS_DB_PATH || '';

const stamp = Date.now().toString(36);
const userA = `chat_a_${stamp}`;
const userB = `chat_b_${stamp}`;
const password = 'pw1151';
const ip = uniqueIp('chatiso');
const orchA = `ORCH_ONLY_${userA}_${ip}`;
const orchB = `ORCH_ONLY_${userB}_${ip}`;
const wfA = `WF_ONLY_${userA}_${ip}`;
const wfB = `WF_ONLY_${userB}_${ip}`;

const { browser, page: pageA } = await launch({ viewport: { width: 1650, height: 1000 }, dsf: 1 });
const ctxB = await browser.newContext({ viewport: { width: 1650, height: 1000 }, deviceScaleFactor: 1 });
const pageB = await ctxB.newPage();

const register = async (page, username) => {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  const reg = await jpost(page, '/api/auth/register', {
    username,
    password,
    display_name: username,
  });
  assert(reg.status === 200, `${username} registered (${reg.status})`);
  const me = await jget(page, '/api/users/me');
  assert(me.status === 200, `${username} authenticated (${me.status})`);
  return (me.body && me.body.user) || {};
};

const activate = async (page, user, workflow) => {
  const r = await jpost(page, '/api/session/activate', {
    owner: user.username,
    ip,
    workflow,
    preserve_running: true,
  });
  assert(r.status === 200 && r.body && r.body.ok, `${user.username}/${ip}/${workflow} activated (${r.status})`);
};

const recordOrchChat = (user, content) => new Promise((resolve) => {
  const args = [
    CHAT_RECORDER,
    '--project-root', PROJECT_ROOT,
    '--ip', ip,
    '--user-id', user.id,
    '--display-name', user.username,
    '--role', 'user',
  ];
  if (DB_PATH) args.push('--db-path', DB_PATH);
  const child = spawn('python3', args, {
    cwd: SOURCE_ROOT,
    env: { ...process.env, PYTHONPATH: SOURCE_ROOT },
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  let stderr = '';
  child.stderr.on('data', d => { stderr += d.toString(); });
  child.on('close', (code) => {
    assert(code === 0, `recorded orchestrator chat for ${user.username} (${code})`);
    if (code !== 0) log(stderr.slice(-800));
    resolve(code === 0);
  });
  child.stdin.end(content);
});

const writeWorkflowConversation = async (username, content) => {
  const sdir = path.join(PROJECT_ROOT, '.session', username, ip, 'ssot-gen');
  await mkdir(sdir, { recursive: true });
  const messages = [
    { role: 'user', content },
    {
      role: 'assistant',
      content: `ssot-gen private reply for ${username}`,
    },
    {
      role: 'assistant',
      tool_calls: [{
        function: {
          name: 'private_stage_probe',
          arguments: `user="${username}", ip="${ip}"`,
        },
      }],
    },
    {
      role: 'tool',
      name: 'private_stage_probe',
      content: `└─ PASS private workflow chat for ${username}`,
    },
  ];
  await writeFile(path.join(sdir, 'conversation.json'), JSON.stringify(messages, null, 2) + '\n', 'utf8');
  await writeFile(path.join(sdir, 'full_conversation.json'), JSON.stringify(messages, null, 2) + '\n', 'utf8');
};

const getSessionState = (page, session) => page.evaluate(async (sid) => {
  const r = await fetch(
    `/api/session/state?session=${encodeURIComponent(sid)}&limit=120&mode=conversation`,
    { credentials: 'include', cache: 'no-store' },
  );
  const body = await r.json().catch(() => null);
  return { status: r.status, body };
}, session);

const stateText = (state) => {
  const messages = (state.body && state.body.conversation && state.body.conversation.messages) || [];
  return messages.map(m => String(m.content || m.text || '')).join('\n');
};

const gotoWorkspaceChatText = async (page, username, workflow) => {
  await page.goto(`${BASE}/?session_id=${username}&ip=${ip}&workflow=${workflow}`, {
    waitUntil: 'networkidle',
  });
  await page.evaluate(() => {
    const workspace = [...document.querySelectorAll('button,a,span,.dir-btn,[role="tab"]')]
      .find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent || '').trim()) && x.offsetParent);
    if (workspace) workspace.click();
  });
  await page.waitForTimeout(1600);
  await page.evaluate(() => {
    const chat = [...document.querySelectorAll('button,a,span,div,[role="tab"]')]
      .find(x => (x.textContent || '').trim().toUpperCase() === 'CHAT' && x.offsetParent);
    if (chat) chat.click();
  });
  await page.waitForTimeout(1800);
  return page.evaluate(() => document.body.innerText || '');
};

try {
  const a = await register(pageA, userA);
  const b = await register(pageB, userB);

  await activate(pageA, a, 'orchestrator');
  await activate(pageB, b, 'orchestrator');
  await recordOrchChat(a, orchA);
  await recordOrchChat(b, orchB);

  const aOrch = await getSessionState(pageA, `${userA}/${ip}/orchestrator`);
  const bOrch = await getSessionState(pageB, `${userB}/${ip}/orchestrator`);
  const aOrchText = stateText(aOrch);
  const bOrchText = stateText(bOrch);
  assert(aOrch.status === 200, `A orchestrator state readable (${aOrch.status})`);
  assert(bOrch.status === 200, `B orchestrator state readable (${bOrch.status})`);
  assert(aOrchText.includes(orchA), 'A sees own orchestrator chat');
  assert(!aOrchText.includes(orchB), 'A does not see B orchestrator chat');
  assert(bOrchText.includes(orchB), 'B sees own orchestrator chat');
  assert(!bOrchText.includes(orchA), 'B does not see A orchestrator chat');

  const crossA = await getSessionState(pageA, `${userB}/${ip}/orchestrator`);
  const crossB = await getSessionState(pageB, `${userA}/${ip}/orchestrator`);
  assert(crossA.status === 403, `A cannot read B orchestrator session (${crossA.status})`);
  assert(crossB.status === 403, `B cannot read A orchestrator session (${crossB.status})`);

  // Activate first to create empty DB runtime sessions. This catches the
  // regression where an empty DB session hides the worker conversation file.
  await activate(pageA, a, 'ssot-gen');
  await activate(pageB, b, 'ssot-gen');
  await writeWorkflowConversation(userA, wfA);
  await writeWorkflowConversation(userB, wfB);

  const aWf = await getSessionState(pageA, `${userA}/${ip}/ssot-gen`);
  const bWf = await getSessionState(pageB, `${userB}/${ip}/ssot-gen`);
  const aWfText = stateText(aWf);
  const bWfText = stateText(bWf);
  assert(aWf.status === 200, `A workflow state readable (${aWf.status})`);
  assert(bWf.status === 200, `B workflow state readable (${bWf.status})`);
  assert(aWfText.includes(wfA), 'A sees own workflow chat');
  assert(!aWfText.includes(wfB), 'A does not see B workflow chat');
  assert(bWfText.includes(wfB), 'B sees own workflow chat');
  assert(!bWfText.includes(wfA), 'B does not see A workflow chat');

  const uiAOrch = await gotoWorkspaceChatText(pageA, userA, 'orchestrator');
  const uiBOrch = await gotoWorkspaceChatText(pageB, userB, 'orchestrator');
  assert(uiAOrch.includes(orchA), 'A UI shows own orchestrator chat');
  assert(!uiAOrch.includes(orchB), 'A UI hides B orchestrator chat');
  assert(uiBOrch.includes(orchB), 'B UI shows own orchestrator chat');
  assert(!uiBOrch.includes(orchA), 'B UI hides A orchestrator chat');

  const uiAWf = await gotoWorkspaceChatText(pageA, userA, 'ssot-gen');
  const uiBWf = await gotoWorkspaceChatText(pageB, userB, 'ssot-gen');
  assert(uiAWf.includes(wfA), 'A UI shows own workflow chat');
  assert(!uiAWf.includes(wfB), 'A UI hides B workflow chat');
  assert(uiBWf.includes(wfB), 'B UI shows own workflow chat');
  assert(!uiBWf.includes(wfA), 'B UI hides A workflow chat');
} catch (e) {
  assert(false, 'unexpected error: ' + (e && e.stack || e));
} finally {
  await ctxB.close();
  await browser.close();
}

log(`users: ${userA}, ${userB}`);
log(`ip: ${ip}`);
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
