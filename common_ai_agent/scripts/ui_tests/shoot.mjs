import { chromium } from 'playwright';

const BASE = process.env.BASE || 'http://127.0.0.1:3001';
const USER = process.env.U || 'admin';
const PASS = process.env.P || '1151';
const OUT = '/Users/brian/Desktop/Project/brian_hw/common_ai_agent/.omc/ui-shots';

const log = (...a) => console.log('[shoot]', ...a);

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
page.on('console', m => { if (m.type() === 'error') log('console.error:', m.text().slice(0, 200)); });

try {
  // 1) load base, then authenticate via the cookie-session login endpoint
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  const loginRes = await page.evaluate(async ({ u, p }) => {
    const r = await fetch('/api/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p }), credentials: 'include',
    });
    let body = null; try { body = await r.json(); } catch (_) {}
    return { status: r.status, body };
  }, { u: USER, p: PASS });
  log('login status:', loginRes.status, JSON.stringify(loginRes.body || {}).slice(0, 200));

  // 2) reload the app now that the session cookie is set
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3500); // in-browser Babel compile + React mount

  await page.screenshot({ path: `${OUT}/00-baseline.png`, fullPage: false });
  log('saved 00-baseline.png');

  // 3) try to surface the toolbar 'size' control value (proves 13px default + px labels)
  const sizeInfo = await page.evaluate(() => {
    const out = { found: false };
    const selects = Array.from(document.querySelectorAll('select'));
    for (const s of selects) {
      const opts = Array.from(s.options).map(o => o.textContent.trim());
      if (opts.some(t => /\d+px/.test(t))) {
        out.found = true;
        out.options = opts;
        out.selected = s.options[s.selectedIndex]?.textContent?.trim();
        const r = s.getBoundingClientRect();
        out.rect = { x: r.x, y: r.y, w: r.width, h: r.height };
        break;
      }
    }
    return out;
  });
  log('size control:', JSON.stringify(sizeInfo));

  // crop the top toolbar region for a clean shot of the font/size controls
  await page.screenshot({ path: `${OUT}/01-toolbar.png`, clip: { x: 0, y: 0, width: 1600, height: 90 } });
  log('saved 01-toolbar.png');

  // also dump body computed font-size to verify 13px base
  const fontInfo = await page.evaluate(() => {
    const cs = getComputedStyle(document.body);
    const v = getComputedStyle(document.documentElement);
    return {
      bodyFont: cs.fontFamily.slice(0, 60),
      uiFontSize: v.getPropertyValue('--ui-font-size').trim(),
      dataFontScale: document.documentElement.getAttribute('data-font-scale'),
      dataFont: document.documentElement.getAttribute('data-font'),
    };
  });
  log('font:', JSON.stringify(fontInfo));
} catch (e) {
  log('ERROR', e.message);
} finally {
  await browser.close();
}
