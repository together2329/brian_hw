const { test, expect } = require('@playwright/test');

test.describe('Atlas UI Smoke Tests', () => {
  test('homepage loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/ATLAS/);
  });

  test('lobby page renders', async ({ page }) => {
    await page.goto('/lobby');
    await expect(page.locator('text=Your Sessions')).toBeVisible();
  });

  test('lobby auto-creates guest and shows sessions', async ({ page }) => {
    await page.goto('/lobby');
    await expect(page.locator('text=Your Sessions')).toBeVisible();
    await expect(page.locator('text=Loading sessions…')).toBeHidden({ timeout: 10000 });
    const hasEmptyState = await page.locator('text=No active sessions match your search.').isVisible().catch(() => false);
    const hasSessionCards = await page.locator('.lobby-card').count() > 0;
    expect(hasEmptyState || hasSessionCards).toBe(true);
  });

  test.fail('/admin returns 403 for guest users', async ({ page }) => {
    const response = await page.goto('/admin');
    expect(response.status()).toBe(403);
  });
});
