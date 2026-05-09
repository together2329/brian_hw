const { test, expect } = require('@playwright/test');

test.describe('Lobby', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/lobby');
    await expect(page.locator('text=Your Sessions')).toBeVisible();
    await expect(page.locator('text=Loading sessions…')).toBeHidden({ timeout: 10000 });
  });

  test('navigating to lobby shows Your Sessions heading', async ({ page }) => {
    await expect(page.locator('h2:has-text("Your Sessions")')).toBeVisible();
  });

  test('clicking New Session opens modal, creating redirects to workspace', async ({ page }) => {
    await page.click('[aria-label="New Session"]');
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    const testTitle = 'E2E Test Session ' + Date.now();
    await page.fill('[role="dialog"] input[placeholder*="e.g."]', testTitle);
    await page.click('[role="dialog"] button:has-text("Create")');
    await expect(page.locator('[role="dialog"]')).toBeHidden({ timeout: 10000 });
    await page.locator('.lobby-card').filter({ hasText: testTitle }).click();
    await expect(page).toHaveURL(/\?session_id=/);
  });

  test('created session appears in session list', async ({ page }) => {
    const testTitle = 'E2E List Session ' + Date.now();
    await page.click('[aria-label="New Session"]');
    await page.fill('[role="dialog"] input[placeholder*="e.g."]', testTitle);
    await page.click('[role="dialog"] button:has-text("Create")');
    await expect(page.locator('[role="dialog"]')).toBeHidden({ timeout: 10000 });
    await page.goto('/lobby');
    await expect(page.locator('text=Loading sessions…')).toBeHidden({ timeout: 10000 });
    await expect(page.locator('.lobby-card').filter({ hasText: testTitle })).toBeVisible();
  });
});
