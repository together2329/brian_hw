// Screenshot the pipeline / orchestrator React Flow graph to verify rendering.
import { chromium } from 'playwright';
const BASE = process.env.BASE || 'http://127.0.0.1:3000';
const USER = process.env.USER_NAME || 'admin';
const PASS = process.env.PASS || '1151';
const IP = process.env.IP || 'cnt8_en_v1';
const OUT = process.env.OUT || '/tmp/pipeline_flow_shot.png';

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1680, height: 1000 } });
const errs = [];
try {
  await ctx.request.post(BASE + '/api/auth/login', { data: { username: USER, password: PASS } });
  const page = await ctx.newPage();
  page.on('pageerror', e => errs.push('PAGEERROR: ' + (e.stack || e.message)));
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  if (await page.$('input[type=password]')) {
    try {
      await page.fill('input[type=text], input[name=username]', USER, { timeout: 5000 });
      await page.fill('input[type=password]', PASS, { timeout: 5000 });
      await page.click('button:has-text("Login"), button[type=submit]');
    } catch (_) {}
  }
  await page.waitForTimeout(3500);
  // Select the IP in whichever <select> lists it as an option.
  try {
    const selects = await page.$$('select');
    for (const s of selects) {
      const ok = await s.selectOption({ label: IP }).then(() => true).catch(() => false);
      if (ok) { console.log('selected IP via dropdown'); break; }
    }
    await page.waitForTimeout(1500);
  } catch (_) {}
  // Go to the PIPELINE top-nav screen.
  for (const sel of ['button:has-text("PIPELINE")', 'text=PIPELINE', '[data-screen="pipeline"]']) {
    const t = await page.$(sel);
    if (t) { await t.click().catch(() => {}); console.log('clicked', sel); await page.waitForTimeout(3000); break; }
  }
  await page.waitForTimeout(3000);
  // Is React Flow present?
  const rf = await page.$('.react-flow').then(Boolean).catch(() => false);
  const nodeCount = await page.$$eval('.react-flow__node', ns => ns.length).catch(() => 0);
  console.log('react-flow present:', rf, '· nodes:', nodeCount);
  const flowEl = await page.$('.react-flow');
  if (flowEl) { await flowEl.screenshot({ path: OUT }).catch(() => page.screenshot({ path: OUT })); }
  else await page.screenshot({ path: OUT, fullPage: false });
  console.log('shot:', OUT);
} catch (e) {
  errs.push('SCRIPT: ' + (e.message || e));
} finally {
  if (errs.length) { console.log('ERRORS:'); errs.slice(0, 5).forEach(e => console.log(e)); }
  await browser.close();
}
