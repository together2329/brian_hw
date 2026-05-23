// Capture the real ATLAS /new-ip UI flow:
// dashboard -> orchestrator chat -> typed slash command -> SSOT plan result
// -> automatic workspace pivot for the newly scaffolded IP.
import { mkdir } from 'node:fs/promises';
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

const { browser, page } = await launch({ viewport: { width: 1800, height: 1100 }, dsf: 2 });
const ip = process.env.IP || uniqueIp('shotip');
const kind = process.env.KIND || 'AXI4-Lite packet status block';
const command = `/new-ip ${ip} ${kind}`;

const clickChat = () => page.evaluate(() => {
  const e = [...document.querySelectorAll('button,span,div,[role="tab"]')]
    .find(x => (x.textContent || '').trim().toUpperCase() === 'CHAT' && x.offsetParent);
  if (e) e.click();
});

const typeCommandButDoNotSubmit = async (text) => {
  const ta = await page.waitForSelector('textarea', { timeout: 8000 });
  await ta.click();
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await ta.type(text);
};

const pressEnter = async () => {
  await page.keyboard.press('Enter');
};

const waitForBody = async (re, { tries = 30, interval = 700, label = 'body' } = {}) => {
  for (let i = 0; i < tries; i++) {
    const hit = await page.evaluate((source) => new RegExp(source, 'i').test(document.body.innerText), re.source);
    if (hit) return true;
    log(`poll ${label} ${i}: not yet`);
    await page.waitForTimeout(interval);
  }
  return false;
};

const snapshotState = () => page.evaluate(() => {
  const url = new URL(window.location.href);
  return {
    href: window.location.href,
    urlIp: url.searchParams.get('ip') || '',
    workflow: url.searchParams.get('workflow') || '',
    activeIp: window.ACTIVE_IP || '',
    activeSession: window.ACTIVE_SESSION || '',
    body: document.body.innerText.slice(0, 2000),
  };
});

try {
  await mkdir(OUT, { recursive: true });

  const li = await login(page);
  assert(li.status === 200, `login ok (${li.status})`);
  const me = await jget(page, '/api/users/me');
  assert(me.status === 200, `authed (me ${me.status})`);

  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1800);
  await shoot(page, `new-ip-00-dashboard-${ip}.png`);

  await gotoWorkspace(page, { ip: 'default', workflow: 'orchestrator' });
  await clickChat();
  await page.waitForTimeout(1200);
  await shoot(page, `new-ip-01-orchestrator-chat-before-${ip}.png`);

  await typeCommandButDoNotSubmit(command);
  await page.waitForTimeout(400);
  await shoot(page, `new-ip-02-command-typed-${ip}.png`);

  await pressEnter();
  await page.waitForTimeout(700);
  await shoot(page, `new-ip-03-command-submitted-${ip}.png`);

  const planVisible = await waitForBody(/SSOT TO-YAML|SSOT plan ready|missing decisions|Validation|Approval|approval/i, {
    tries: 40,
    interval: 750,
    label: 'ssot-plan',
  });
  assert(planVisible, 'SSOT plan/result became visible after /new-ip');
  await shoot(page, `new-ip-04-ssot-plan-visible-${ip}.png`);

  const pivoted = await waitForBody(new RegExp(ip), {
    tries: 20,
    interval: 700,
    label: 'ip-pivot',
  });
  const state = await snapshotState();
  log('state:', JSON.stringify({
    ip,
    command,
    urlIp: state.urlIp,
    workflow: state.workflow,
    activeIp: state.activeIp,
    activeSession: state.activeSession,
  }));
  assert(pivoted && (state.href.includes(`ip=${ip}`) || state.activeIp === ip || state.activeSession.includes(ip)), `UI pivoted to new IP ${ip}`);
  await shoot(page, `new-ip-05-pivoted-workspace-${ip}.png`);
} catch (e) {
  assert(false, 'unexpected error: ' + (e && e.stack || e));
} finally {
  await browser.close();
}

log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
log(`IP: ${ip}`);
log(`screenshots: ${OUT}/new-ip-*-${ip}.png`);
process.exit(exitCode());
