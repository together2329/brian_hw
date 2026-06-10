// Reproduce + capture the real (un-minified message) workspace crash.
// Logs in, loads the workspace, captures page errors + console.error with the
// full Error message (the screenshots only show the minified componentStack).
//
// Env: BASE (default http://127.0.0.1:3000), USER/PASS (default admin/1151),
//      IP (default mctp_assembler_v2), WF (default orchestrator).
import { chromium } from 'playwright';

const BASE = process.env.BASE || 'http://127.0.0.1:3000';
const USER = process.env.USER_NAME || 'admin';
const PASS = process.env.PASS || '1151';
const IP = process.env.IP || 'mctp_assembler_v2';

const log = (m) => console.log(m);
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1680, height: 1000 } });
const errors = [];
try {
  const r = await ctx.request.post(BASE + '/api/auth/login', { data: { username: USER, password: PASS } });
  log(`auth ${USER} -> ${r.status()}`);

  const page = await ctx.newPage();
  page.on('pageerror', (e) => { errors.push('PAGEERROR: ' + (e && e.stack || e && e.message || String(e))); });
  page.on('console', (m) => {
    if (m.type() === 'error') {
      const t = m.text();
      if (/crash|Cannot read|undefined is not|is not a function|TypeError|RangeError|Maximum update/.test(t)) {
        errors.push('CONSOLE.ERROR: ' + t.slice(0, 800));
      }
    }
  });

  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  // login form fallback
  if (await page.$('input[type=password]')) {
    try {
      await page.fill('input[type=text], input[name=username]', USER, { timeout: 5000 });
      await page.fill('input[type=password]', PASS, { timeout: 5000 });
      await page.click('button:has-text("Login"), button:has-text("로그인"), button[type=submit]');
    } catch (_) {}
  }
  await page.waitForTimeout(4000);

  // Try to select the IP + orchestrator workflow via the URL/global hooks.
  await page.evaluate((ip) => {
    try { window.ACTIVE_IP = ip; } catch (_) {}
    try { localStorage.setItem('atlas.activeIp', ip); } catch (_) {}
  }, IP);
  await page.waitForTimeout(1500);

  // Click CHAT tab if present, then type hi
  try {
    const chatTab = await page.$('text=CHAT');
    if (chatTab) { await chatTab.click(); await page.waitForTimeout(1000); }
    const ta = await page.$('textarea');
    if (ta) { await ta.fill('hi'); await page.keyboard.press('Enter'); }
  } catch (_) {}
  await page.waitForTimeout(6000);

  // Is the error-boundary "Reset" screen showing?
  const crashed = await page.$('text=Reset').then(Boolean).catch(() => false);
  const bodyText = (await page.evaluate(() => document.body.innerText || '')).slice(0, 200);
  log(`crashed boundary visible: ${crashed}`);
  log(`body head: ${JSON.stringify(bodyText)}`);
} catch (e) {
  errors.push('SCRIPT: ' + (e && e.message || String(e)));
} finally {
  log('\n=== CAPTURED ERRORS (' + errors.length + ') ===');
  for (const e of errors.slice(0, 10)) log(e + '\n');
  await browser.close();
}
