// Gap 7: mobile breakpoint (@media max-width:900px / .mob-header). Real layout.
import { launch, login, shoot, assert, failures, exitCode, log } from './lib.mjs';

// phone-sized context
const { browser, page } = await launch({ viewport: { width: 390, height: 844 }, dsf: 3 });
try {
  await login(page);
  await page.waitForTimeout(1500);

  const m = await page.evaluate(() => {
    const mob = document.querySelector('.mob-header');
    const visible = mob ? getComputedStyle(mob).display !== 'none' && mob.offsetParent !== null : false;
    return {
      hasMob: !!mob,
      mobVisible: visible,
      innerW: window.innerWidth,
      scrollW: document.documentElement.scrollWidth,
    };
  });
  assert(m.hasMob, '.mob-header exists in DOM at 390px');
  assert(m.mobVisible, '.mob-header is visible at 390px');
  assert(m.scrollW <= m.innerW + 1, `no horizontal scroll (scrollW ${m.scrollW} <= innerW ${m.innerW})`);
  await shoot(page, 'mobile-390.png');

  // control: at desktop width the mobile header should be hidden
  const ctx2 = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
  const p2 = await ctx2.newPage();
  await login(p2);
  await p2.waitForTimeout(1200);
  const d = await p2.evaluate(() => {
    const mob = document.querySelector('.mob-header');
    return { hidden: !mob || getComputedStyle(mob).display === 'none' || mob.offsetParent === null };
  });
  assert(d.hidden, '.mob-header hidden at 1600px (desktop)');
  await ctx2.close();
} catch (e) {
  assert(false, 'unexpected error: ' + e.message);
} finally {
  await browser.close();
}
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
