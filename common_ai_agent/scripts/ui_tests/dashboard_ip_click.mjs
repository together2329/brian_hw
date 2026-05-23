// Gap 5: dashboard IP row click → navigates to that IP's workspace.
import { launch, login, jpost, shoot, assert, failures, exitCode, log, uniqueIp, BASE } from './lib.mjs';

const { browser, page } = await launch();
const ip = uniqueIp('dash');
try {
  await login(page);
  const created = await jpost(page, '/api/ip/create', { name: ip });
  assert(created.status === 200 && created.body && created.body.ok, `created IP ${ip}`);

  // reload dashboard so the new IP shows in the inventory table
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);

  const found = await page.evaluate((ip) => {
    const row = [...document.querySelectorAll('[title]')].find(e => (e.getAttribute('title') || '') === `Open ${ip} workspace`);
    return !!row;
  }, ip);
  assert(found, `dashboard shows a clickable row titled "Open ${ip} workspace"`);
  await shoot(page, 'dash-before-click.png');

  if (found) {
    await page.evaluate((ip) => {
      const row = [...document.querySelectorAll('[title]')].find(e => (e.getAttribute('title') || '') === `Open ${ip} workspace`);
      // click the row itself, not the inner Open button (which stops propagation)
      row.click();
    }, ip);
    await page.waitForTimeout(3500);
    const nav = await page.evaluate(() => {
      const url = new URL(window.location.href);
      return {
        urlIp: url.searchParams.get('ip'),
        hasPrompt: !!document.querySelector('.prompt-row, textarea'),
        activeIp: window.ACTIVE_IP || '',
      };
    });
    assert(nav.urlIp === ip || nav.activeIp === ip, `after click, active IP is ${ip} (url=${nav.urlIp}, active=${nav.activeIp})`);
    assert(nav.hasPrompt, 'workspace mounted (prompt input present)');
    await shoot(page, 'dash-after-click.png');
  }
} catch (e) {
  assert(false, 'unexpected error: ' + e.message);
} finally {
  await browser.close();
}
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
