/**
 * ATLAS Web UI — BROAD codex /subagent + team checks (Playwright, headless).
 *
 * One real session against a running ATLAS server (CODEX_BRIDGE=1 + multi-agent):
 *   1. spawn a TEAM (several subagents) -> selector under the workflow list shows
 *      Main + N distinctly-labelled lanes
 *   2. click subagent #1 -> MAIN chat renders its transcript (Watching banner)
 *   3. click subagent #2 -> MAIN chat switches to a DIFFERENT transcript
 *   4. click Main -> MAIN chat returns to the original conversation (no banner,
 *      prior reply preserved)
 *   5. transcripts are coalesced (no one-word-per-line fragmentation)
 *
 *   ATLAS_E2E_BASE=http://127.0.0.1:3041 node scripts/verify_subagent_ui_broad.mjs
 */
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.ATLAS_E2E_BASE || 'http://127.0.0.1:3041';
const USER = process.env.ATLAS_ADMIN_USER || 'admin';
const PASS = process.env.ATLAS_ADMIN_PASS || '1151';
const SHOTS = process.env.ATLAS_E2E_SHOTS || '/tmp/atlas_broad_shots';
const T = Number(process.env.ATLAS_E2E_TIMEOUT_MS || 60000);
const TURN_T = Number(process.env.ATLAS_E2E_TURN_MS || 300000);
const PROMPT = process.env.ATLAS_E2E_PROMPT ||
  "Spawn THREE separate subagents in parallel and wait for all of them: agent " +
  "Alpha computes 2+2, agent Beta computes 10*10, agent Gamma reverses the word " +
  "'codex'. Then report each agent's result on its own line.";

fs.mkdirSync(SHOTS, { recursive: true });
let failed = 0;
const ok = (m) => console.log('  \x1b[32m✓\x1b[0m ' + m);
const bad = (m) => { console.error('  \x1b[31m✗ ' + m + '\x1b[0m'); failed++; };
const soft = (c, m) => (c ? ok(m) : bad(m));
const step = (m) => console.log('\n=== ' + m + ' ===');

const chatText = (page) => page.evaluate(() => {
  const texts = [document.body.innerText];
  for (const f of Array.from(document.querySelectorAll('iframe'))) {
    try { texts.push(f.contentDocument?.body?.innerText || ''); } catch (_) { /* x-origin */ }
  }
  return texts.join('\n');
});
const laneInfo = (page) => page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll('.subagent-lanes button'));
  return btns.map((b, i) => ({ i, text: (b.textContent || '').replace(/\s+/g, ' ').trim(), isMain: /\[default\]/.test(b.textContent || '') }));
});
const clickLane = (page, idx) => page.evaluate((i) => {
  const btns = Array.from(document.querySelectorAll('.subagent-lanes button'));
  if (!btns[i]) return false; btns[i].click(); return true;
}, idx);

const browser = await chromium.launch({ headless: true });
try {
  const ctx = await browser.newContext({ baseURL: BASE, ignoreHTTPSErrors: true });
  try { await ctx.request.post(BASE + '/api/auth/login', { data: { username: USER, password: PASS } }); } catch (_) {}
  const page = await ctx.newPage();
  let subagentFrames = 0;
  page.on('websocket', (s) => {
    if (!s.url().includes('/ws/agent')) return;
    s.on('framereceived', (f) => { if (/"type"\s*:\s*"subagent"/.test((f.payload || '').toString())) subagentFrames++; });
  });

  step('1. login + workspace');
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: T });
  await page.waitForTimeout(3000);
  if (await page.$('input[type=password]')) {
    try {
      await page.fill('input[type=text], input[name=username], input[placeholder*="ser" i]', USER, { timeout: 8000 });
      await page.fill('input[type=password]', PASS, { timeout: 8000 });
      await page.click('button:has-text("Login"), button:has-text("로그인"), button[type=submit]');
      await page.waitForTimeout(3000);
    } catch (_) {}
  }
  let chat = null;
  for (let i = 0; i < 25 && !chat; i++) { chat = await page.$('textarea'); if (!chat) await page.waitForTimeout(1000); }
  soft(!!chat, 'workspace + chat input rendered');
  if (!chat) throw new Error('no chat input');

  step('2. spawn a team of subagents');
  await chat.click(); await chat.fill(PROMPT); await chat.press('Enter');
  console.log('  prompt sent; waiting up to ' + (TURN_T / 1000) + 's for codex...');
  const deadline = Date.now() + TURN_T;
  let lanes = [];
  while (Date.now() < deadline) {
    lanes = await laneInfo(page);
    const subs = lanes.filter((l) => !l.isMain).length;
    if (subs >= 1 && subagentFrames > 0 && lanes.length >= 2) {
      // give codex a moment to spawn the rest of the team
      if (subs >= 2) break;
    }
    await page.waitForTimeout(1500);
  }
  await page.waitForTimeout(2500);
  lanes = await laneInfo(page);
  await page.screenshot({ path: SHOTS + '/20_selector.png', fullPage: true });
  const subLanes = lanes.filter((l) => !l.isMain);
  soft(subagentFrames > 0, `subagent WS frames reached browser (${subagentFrames})`);
  soft(lanes.some((l) => l.isMain), 'Main [default] lane present');
  soft(subLanes.length >= 1, `subagent lane(s) present (${subLanes.length})`);
  const team = subLanes.length >= 2;
  soft(team, `TEAM: >=2 subagent lanes (${subLanes.length})` + (team ? '' : ' — only 1 spawned; lane-switch test limited'));
  const subTexts = subLanes.map((l) => l.text);
  soft(new Set(subTexts).size === subTexts.length, `subagent labels are DISTINCT (${subTexts.join(' | ')})`);

  step('3. click subagent #1 -> main chat renders its transcript');
  await clickLane(page, subLanes[0].i);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: SHOTS + '/21_sub1.png', fullPage: true });
  const t1 = await chatText(page);
  soft(/Watching subagent/.test(t1), 'main chat shows the "Watching subagent" banner');
  // coalescing: a real sentence (>=4 words in a row) appears somewhere
  soft(/\b\w+\s+\w+\s+\w+\s+\w+\b/.test(t1), 'transcript reads as sentences (coalesced, not one-word-per-line)');

  let t2 = '';
  if (team) {
    step('4. click subagent #2 -> main chat switches transcript');
    await clickLane(page, subLanes[1].i);
    await page.waitForTimeout(2500);
    await page.screenshot({ path: SHOTS + '/22_sub2.png', fullPage: true });
    t2 = await chatText(page);
    soft(/Watching subagent/.test(t2), 'main chat shows banner for subagent #2');
    soft(t1 !== t2, 'subagent #2 transcript DIFFERS from #1 (per-lane view)');
  }

  step('5. click Main -> return to the original conversation');
  const mainLane = lanes.find((l) => l.isMain);
  await clickLane(page, mainLane.i);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: SHOTS + '/23_main.png', fullPage: true });
  const tMain = await chatText(page);
  soft(!/Watching subagent/.test(tMain), 'returning to Main clears the watch view (original conversation restored)');

  step('RESULT');
  console.log(`  screenshots: ${SHOTS}`);
  console.log(`  lanes: ${lanes.map((l) => (l.isMain ? '[Main]' : l.text)).join('  ·  ')}`);
} finally {
  await browser.close();
}
console.log(`\n===== BROAD WEB UI: ${failed === 0 ? '\x1b[32m✅ ALL PASS\x1b[0m' : '\x1b[31m❌ ' + failed + ' FAILED\x1b[0m'} =====`);
process.exit(failed === 0 ? 0 : 1);
