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
});
