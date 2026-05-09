const { test, expect } = require('@playwright/test');

test.describe('Workspace', () => {
  test('opening workspace with session_id connects WS', async ({ page }) => {
    await page.goto('/?session_id=test-a&workflow=ssot-gen');
    await page.waitForFunction(
      () => window.backend && window.backend.getConnectionState() === 'open',
      { timeout: 10000 }
    );
    const state = await page.evaluate(() => window.backend.getConnectionState());
    expect(state).toBe('open');
  });

  test('send prompt and receive connection events', async ({ page }) => {
    await page.goto('/?session_id=test-a&workflow=ssot-gen');
    await page.waitForFunction(
      () => window.backend && window.backend.getConnectionState() === 'open',
      { timeout: 10000 }
    );
    const hello = await page.evaluate(() => new Promise((resolve) => {
      const unsub = window.backend.subscribe('hello', (m) => { unsub(); resolve(m); });
      setTimeout(() => resolve(null), 3000);
    }));
    expect(hello).not.toBeNull();

    const testMsg = 'hello from e2e ' + Date.now();
    await page.fill('.prompt-row input', testMsg);
    await page.press('.prompt-row input', 'Enter');
    await expect(page.locator('.prompt-row input')).toHaveValue('');
    await expect(page.locator('text=' + testMsg).first()).toBeVisible();
  });

  test('session switcher dropdown is visible', async ({ page }) => {
    await page.goto('/?session_id=test-a&workflow=ssot-gen');
    await page.waitForFunction(
      () => window.backend && window.backend.getConnectionState() === 'open',
      { timeout: 10000 }
    );
    await page.waitForSelector('.tab-chip', { timeout: 10000 });
    await page.locator('.tab-chip').first().click();
    await expect(page.locator('button[title="Switch session"]')).toBeVisible();
  });
});
